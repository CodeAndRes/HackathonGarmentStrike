"""
core/llm_client.py
──────────────────
Brain Bridge: routes each game turn through an LLM.

Responsibilities:
  · Build a structured prompt injecting agent.md + board state + move history.
  · Call the LLM via LiteLLM (supports Gemini, OpenAI, Anthropic, …).
  · Parse & validate the response with Pydantic (enforces JSON schema).
  · Retry up to max_retries times with a correction hint on bad output.

Developer Agent  – prompt construction and LiteLLM integration.
QA Agent         – Pydantic validator rejects malformed coordinates before
                   they can corrupt game state (e.g. "B-12", "K5", "A11").
"""
from __future__ import annotations

import json
import os
import re
from typing import Optional

from pydantic import BaseModel, field_validator

try:
    import litellm

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

# ── Coordinate validation regex (mirrors engine.py) ──────────────────────────

_COORD_RE = re.compile(r"^[A-J](10|[1-9])$")

# ── Output schema (enforced by Pydantic) ─────────────────────────────────────


class AgentMove(BaseModel):
    """
    The only valid LLM response shape.
    Pydantic raises ValidationError on any malformed coordinate,
    allowing the retry loop to request a correction from the LLM.
    """

    coordenada: str
    razonamiento: str
    estrategia_aplicada: str

    @field_validator("coordenada")
    @classmethod
    def validate_coordinate(cls, v: str) -> str:
        clean = v.strip().upper()
        if not _COORD_RE.match(clean):
            raise ValueError(
                f"Coordenada {v!r} inválida. "
                "Debe ser letra A-J seguida de número 1-10  (ej: B5, J10)."
            )
        return clean


# ── Move history entry ────────────────────────────────────────────────────────


class MoveHistoryEntry(BaseModel):
    turno: int
    agente: str
    coordenada: str
    resultado: str
    razonamiento: Optional[str] = None


# ── System prompt (fixed, injected once per session) ─────────────────────────

_SYSTEM_PROMPT = """\
Eres un agente de Garment Strike (Supply Chain Battleship). Tablero 10×10 (A-J, 1-10).
Responde SOLO con JSON válido:
{"coordenada":"<A-J><1-10>","razonamiento":"<breve>","estrategia_aplicada":"<nombre>"}
Coordenada válida: letra A-J + número 1-10. Ej: A1, B5, J10. NO dispares a celdas ya disparadas.
"""


# ── LLM Client ────────────────────────────────────────────────────────────────


class LLMClient:
    """
    Connects the game engine to any LLM supported by LiteLLM.

    Usage:
        client = LLMClient(model="gemini/gemini-1.5-pro")
        move = client.get_move(agent_md, board_text, history, my_name, opp_name)
    """

    def __init__(
        self,
        model: str = "gemini/gemini-1.5-pro",
        api_key: Optional[str] = None,
        max_retries: int = 1,
        temperature: float = 0.0,
        quick_mode: bool = False,
        max_tokens: int = 80,
    ) -> None:
        if not LITELLM_AVAILABLE:
            raise ImportError(
                "litellm is required.  Install it with:  pip install litellm"
            )
        self.model = model
        self.max_retries = max_retries
        self.temperature = temperature
        self.quick_mode = quick_mode
        self.max_tokens = max_tokens
        self.is_local_model = self.model.lower().startswith("ollama/")

        # Allow explicit override; otherwise rely on env vars loaded by caller
        if api_key:
            os.environ["LITELLM_API_KEY"] = api_key

    @staticmethod
    def _strip_json_fences(raw: str) -> str:
        """
        Remove markdown fences often returned by local models, e.g.:
          ```json
          {...}
          ```
        """
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
        return text.strip()

    @staticmethod
    def _extract_json_object(raw: str) -> str:
        """Extract the first top-level JSON object from free-form text."""
        text = raw.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return text
        return text[start : end + 1]

    def _normalize_raw_response(self, raw: str) -> str:
        """Normalize LLM output before json.loads; stricter for local models."""
        cleaned = raw.strip()
        if self.is_local_model:
            cleaned = self._strip_json_fences(cleaned)
            cleaned = self._extract_json_object(cleaned)
        return cleaned

    # ── Prompt construction ──────────────────────────────────────────────────

    def build_prompt(
        self,
        agent_md: str,
        opponent_board_text: str,
        move_history: list[MoveHistoryEntry],
        my_name: str,
        opponent_name: str,
    ) -> str:
        last_n = 3
        history_block = "\n".join(
            f"  [T{e.turno:>3}] {e.agente:<15} → {e.coordenada}  "
            f"resultado={e.resultado.upper()}"
            + (f"  (razón: {e.razonamiento})" if (e.razonamiento and not self.quick_mode) else "")
            for e in move_history[-last_n:]
        ) or "  (ningún movimiento aún)"

        if self.quick_mode:
            return (
                f"## MANIFIESTO\n{agent_md}\n\n"
                f"Eres {my_name} vs {opponent_name}.\n"
                f"TABLERO RIVAL:\n```\n{opponent_board_text}\n```\n"
                f"ÚLTIMOS {last_n} MOVIMIENTOS:\n{history_block}\n\n"
                f"Elige la MEJOR coordenada. Responde SOLO con JSON."
            )

        return (
            f"## MANIFIESTO ESTRATÉGICO (agent.md de {my_name})\n"
            f"---\n"
            f"{agent_md}\n"
            f"---\n\n"
            f"## ESTADO DEL TURNO\n"
            f"- Eres: **{my_name}**\n"
            f"- Rival: **{opponent_name}**\n\n"
            f"## TABLERO RIVAL ({'?' if not opponent_board_text else 'estado actual'})\n"
            f"```\n"
            f"{opponent_board_text}\n"
            f"```\n"
            f"Leyenda: ~ celda desconocida | X impacto | O agua\n\n"
            f"## ÚLTIMOS {last_n} MOVIMIENTOS\n"
            f"{history_block}\n\n"
            f"## INSTRUCCIÓN\n"
            f"Basándote en tu manifiesto estratégico, elige la MEJOR coordenada para disparar ahora.\n"
            f"Responde ÚNICAMENTE con el JSON especificado en las reglas del sistema."
        )

    # ── LLM call with retry ──────────────────────────────────────────────────

    def get_move(
        self,
        agent_md: str,
        opponent_board_text: str,
        move_history: list[MoveHistoryEntry],
        my_name: str,
        opponent_name: str,
    ) -> AgentMove:
        """
        Ask the LLM for its next move.
        Retries up to max_retries times with a correction hint on bad output.
        Raises ValueError if all retries exhausted.
        """
        prompt = self.build_prompt(
            agent_md, opponent_board_text, move_history, my_name, opponent_name
        )
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                request_kwargs = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                }

                # Pass num_predict for Ollama compatibility
                if self.is_local_model:
                    request_kwargs["num_predict"] = self.max_tokens

                # Gemini/OpenAI support strict response_format; some local providers don't.
                if not self.is_local_model:
                    request_kwargs["response_format"] = {"type": "json_object"}

                response = litellm.completion(**request_kwargs)
                raw = response.choices[0].message.content or ""
                normalized = self._normalize_raw_response(raw)
                data = json.loads(normalized)
                return AgentMove(**data)

            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    prompt += (
                        f"\n\n[CORRECCIÓN REQUERIDA – Intento {attempt} inválido: {exc}. "
                        "Responde SÓLO con JSON válido y coordenada A-J + 1-10.]"
                    )

            except Exception as exc:
                # Re-raise unexpected errors (network, auth, quota) immediately
                raise RuntimeError(
                    f"LLM call failed (model={self.model!r}): {exc}"
                ) from exc

        raise ValueError(
            f"No se obtuvo coordenada válida del LLM tras {self.max_retries} intentos. "
            f"Último error: {last_error}"
        )
