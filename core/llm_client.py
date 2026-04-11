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
import time
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
    latency_ms: Optional[float] = None

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
Coordenada válida: letra A-J + número 1-10. Ej: A1, B5, J10.
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
        max_retries: int = 5,
        temperature: float = 0.0,
        quick_mode: bool = True,
        max_tokens: int = 512,
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
        last_n = 1 if self.quick_mode else 3
        history_block = "\n".join(
            f"  [T{e.turno:>3}] {e.agente:<15} → {e.coordenada}  "
            f"resultado={e.resultado.upper()}"
            for e in move_history[-last_n:]
        ) if move_history else "  (ningún movimiento)"

        if self.quick_mode:
            return (
                f"## REGLAS\n{agent_md}\n\n"
                f"ESTADO ACTUAL:\n{opponent_board_text}\n"
                f"ÚLTIMO MSG:\n{history_block}\n\n"
                f"ATENCIÓN: ¡NUNCA repitas una de las CELDAS PROHIBIDAS!\n"
                f"Elige la MEJOR coordenada nueva. Responde SOLO con JSON: {{\"coordenada\":\"A1\", \"razonamiento\":\"...\", \"estrategia_aplicada\":\"...\"}}"
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
        forbidden_coords: set[str] = None,
    ) -> AgentMove:
        """
        Ask the LLM for its next move.
        Retries up to max_retries times with a correction hint on bad output.
        Raises ValueError if all retries exhausted.
        """
        time.sleep(5)  # Rate limiting for Free Tier (max 15 RPM)
        prompt = self.build_prompt(
            agent_md, opponent_board_text, move_history, my_name, opponent_name
        )
        last_error: Exception | None = None
        start_time = time.perf_counter()

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

                if not self.is_local_model:
                    # request_kwargs["response_format"] = {"type": "json_object"}
                    pass

                # --- DEBUG LOG START ---
                with open("llm_debug.log", "a", encoding="utf-8") as debug_f:
                    debug_f.write(f"\n{'='*80}\n")
                    debug_f.write(f"TURNO: {my_name} vs {opponent_name} | Intento: {attempt}\n")
                    debug_f.write(f"{'-'*80}\n## PROMPT ENVIADO:\n")
                    for m in request_kwargs["messages"]:
                        debug_f.write(f"[{m['role'].upper()}]:\n{m['content']}\n")
                    debug_f.write(f"{'-'*80}\n")
                # --- DEBUG LOG END ---

                response = litellm.completion(**request_kwargs)
                raw = (response.choices[0].message.content or "").strip()
                
                # --- DEBUG RESPONSE START ---
                with open("llm_debug.log", "a", encoding="utf-8") as debug_f:
                    debug_f.write(f"## RESPUESTA LLM:\n{raw}\n")
                # --- DEBUG RESPONSE END ---
                
                if not raw:
                    raise ValueError("La API devolvió una respuesta vacía.")
                
                normalized = self._normalize_raw_response(raw)
                try:
                    data = json.loads(normalized)
                except (json.JSONDecodeError, ValueError) as json_err:
                    # Diagnóstico: Si falla, imprimimos los primeros 100 char para ver qué está pasando
                    print(f"DEBUG: JSON corrupto o incompleto. Crudo (truncado): {raw[:100]}...")
                    # Si falla el JSON, intentamos extraerlo manualmente por si acaso
                    extracted = self._extract_json_object(normalized)
                    data = json.loads(extracted)

                data["latency_ms"] = (time.perf_counter() - start_time) * 1000.0
                move = AgentMove(**data)
                
                if forbidden_coords and move.coordenada in forbidden_coords:
                    raise ValueError(
                        f"¡ALERTA! Acabas de proponer {move.coordenada}, pero ESA CELDA YA FUE DISPARADA PREVIAMENTE. "
                        "Revisa la lista de CELDAS PROHIBIDAS y responde de nuevo eligiendo una casilla COMPLETAMENTE NUEVA."
                    )
                return move

            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2)  # Pequeña pausa antes de reintentar por si fue cuota
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
