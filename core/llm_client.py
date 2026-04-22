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

from pydantic import BaseModel, field_validator, ValidationInfo

from core import prompts

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
    def validate_coordinate(cls, v: str, info: ValidationInfo) -> str:
        clean = v.strip().upper()
        if not _COORD_RE.match(clean):
            raise ValueError(
                f"Coordenada {v!r} inválida. "
                "Debe ser letra A-J seguida de número 1-10  (ej: B5, J10)."
            )
        
        # Validación dinámica si se provee el contexto
        if info.context is not None and "board_size" in info.context:
            size = info.context["board_size"]
            from core.engine import parse_coord
            # parse_coord levanta ValueError si está fuera de límites
            parse_coord(clean, size=size)

        return clean


# ── Move history entry ────────────────────────────────────────────────────────


class MoveHistoryEntry(BaseModel):
    turno: int
    agente: str
    coordenada: str
    resultado: str
    razonamiento: Optional[str] = None


# ── System prompt (fixed, injected once per session) ─────────────────────────

# _SYSTEM_PROMPT is now generated dynamically per-request.


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
        max_retries: int = 3,
        temperature: float = 0.2,
        quick_mode: bool = True,
        api_sleep: float = 6.0,
        max_tokens: int = 150,
        board_size: int = 10,
    ) -> None:
        if not LITELLM_AVAILABLE:
            raise ImportError(
                "litellm is required.  Install it with:  pip install litellm"
            )
        self.model = model
        self.max_retries = max_retries
        self.temperature = temperature
        self.quick_mode = quick_mode
        self.api_sleep = api_sleep
        self.max_tokens = max_tokens
        self.board_size = board_size
        self.is_local_model = self.model.lower().startswith("ollama/")

        # Allow explicit override; otherwise rely on env vars loaded by caller
        if api_key:
            os.environ["LITELLM_API_KEY"] = api_key

    # ── JSON extraction (always applied, not just for local models) ──────

    @staticmethod
    def _strip_json_fences(raw: str) -> str:
        """Remove markdown fences (```json ... ```) that models love to add."""
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

    @staticmethod
    def _extract_coord_fallback(raw: str) -> Optional[str]:
        """
        Last-resort: regex-extract a coordinate like 'E5' or 'J10' from 
        any text, even truncated JSON. This is why local models 'worked' -
        the response always at least contained a coordinate.
        """
        m = re.search(r'"coordenada"\s*:\s*"([A-Ja-j](?:10|[1-9]))"', raw)
        if m:
            return m.group(1).upper()
        # Even more desperate: any standalone coordinate pattern
        m = re.search(r'\b([A-Ja-j](?:10|[1-9]))\b', raw)
        if m:
            return m.group(1).upper()
        return None

    def _parse_response(self, raw: str) -> dict:
        """
        Multi-stage parser that handles all known Gemini quirks:
        1. Strip markdown fences
        2. Extract JSON object
        3. Parse JSON
        4. Fallback: regex-extract coordinate from truncated response
        """
        # Stage 1: Clean fences (Gemini wraps in ```json``` even when told not to)
        cleaned = self._strip_json_fences(raw)
        
        # Stage 2: Extract JSON object substring
        extracted = self._extract_json_object(cleaned)
        
        # Stage 3: Try parsing
        try:
            data = json.loads(extracted)
            # Normalize key aliases (coord -> coordenada)
            if "coord" in data and "coordenada" not in data:
                data["coordenada"] = data["coord"]
            if "razonamiento" not in data:
                data["razonamiento"] = data.get("razon", "Analisis del tablero")
            if "estrategia_aplicada" not in data:
                data["estrategia_aplicada"] = "General"
            return data
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Stage 4: Truncated JSON fallback - extract coordinate with regex
        coord = self._extract_coord_fallback(raw)
        if coord:
            return {
                "coordenada": coord,
                "razonamiento": "Respuesta parcial del LLM (auto-recuperada)",
                "estrategia_aplicada": "Auto-recovery",
            }
        
        # Nothing worked
        raise ValueError(f"No se pudo extraer coordenada de la respuesta: {raw[:80]}...")

    # ── Prompt construction ──────────────────────────────────────────────────

    def build_messages(
        self,
        agent_md: str,
        opponent_board_text: str,
        move_history: list[MoveHistoryEntry],
        my_name: str,
        opponent_name: str,
        forbidden_coords: set[str],
    ) -> list[dict]:
        # Filter history to only include this agent's LAST 5 shots
        my_history = [m for m in move_history if m.agente == my_name][-5:]

        from core.engine import LOGISTICS_MAP
        history_text = "\n".join(
            f"{m.coordenada}: {LOGISTICS_MAP.get(m.resultado, m.resultado).upper()}"
            for m in my_history
        )
        if not history_text:
            history_text = "(None)"


        # Check for fallback recovery (if last move was system-forced)
        warning_text = ""
        if my_history and my_history[-1].razonamiento:
            if "SISTEMA: Fallback" in my_history[-1].razonamiento:
                warning_text = (
                    "CRITICAL: Your previous response was invalid or repeated a cell. \n"
                    "The system had to force a random shot. \n"
                    "RE-FOCUS: Check THE BOARD (X and O) carefully. Do NOT shoot there.\n\n"
                )

        # Calculate boundary text for prompt
        max_letter = "ABCDEFGHIJ"[self.board_size - 1]
        range_text = f"A-{max_letter}, 1-{self.board_size}"

        system_content = prompts.SYSTEM_PROMPT.format(
            my_name=my_name,
            opponent_name=opponent_name,
            agent_md=agent_md,
            size=self.board_size,
            range_text=range_text
        )

        user_content = prompts.USER_PROMPT_TEMPLATE.format(
            warning_text=warning_text,
            opponent_board_text=opponent_board_text,
            history_text=history_text,
            range_text=range_text,
        )

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

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
        Retries up to max_retries times. Each retry is a FRESH call
        (no accumulated corrections that poison the context).
        Raises ValueError if all retries exhausted.
        """
        if not self.is_local_model and self.api_sleep > 0:
            time.sleep(self.api_sleep)
        
        messages = self.build_messages(
            agent_md, opponent_board_text, move_history, my_name, opponent_name, forbidden_coords
        )
        last_error: Exception | None = None
        start_time = time.perf_counter()

        for attempt in range(1, self.max_retries + 1):
            try:
                request_kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "timeout": 60,
                }
                # We avoid passing max_tokens/num_predict by default for Gemini/Ollama
                # because they often interpret it as a character limit or truncate early.
                if not (self.is_local_model or "gemini" in self.model.lower()):
                    request_kwargs["max_tokens"] = self.max_tokens

                # We avoid passing max_tokens/num_predict by default because 
                # some providers (Gemini, Ollama) misinterpret it as a character limit 
                # in early turns, causing premature truncation.

                # --- DEBUG LOG ---
                with open("logs/llm_debug.log", "a", encoding="utf-8") as debug_f:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    debug_f.write(f"\n{'='*80}\n")
                    debug_f.write(f"[{timestamp}] TURNO: {my_name} | Modelo: {self.model} | Intento: {attempt}\n")
                    for msg in messages:
                        debug_f.write(f"[{msg['role'].upper()}] ({len(msg['content'])} chars):\n{msg['content'][:300]}...\n")
                    debug_f.write(f"{'-'*80}\n")

                response = litellm.completion(**request_kwargs)
                raw = (response.choices[0].message.content or "").strip()

                # --- DEBUG RESPONSE ---
                with open("logs/llm_debug.log", "a", encoding="utf-8") as debug_f:
                    debug_f.write(f"RESP ({len(raw)} chars): {raw}\n")

                if not raw:
                    raise ValueError("La API devolvio una respuesta vacia.")

                # Parse with multi-stage fallback (handles fences + truncation)
                data = self._parse_response(raw)
                data["latency_ms"] = (time.perf_counter() - start_time) * 1000.0
                move = AgentMove.model_validate(data, context={"board_size": self.board_size})

                if forbidden_coords and move.coordenada in forbidden_coords:
                    raise ValueError(
                        f"Coordenada {move.coordenada} ya fue disparada."
                    )
                return move

            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2)  # Small pause before retry

            except Exception as exc:
                # Handle transient API errors (Service Unavailable, Rate Limit)
                if LITELLM_AVAILABLE and attempt < self.max_retries:
                    if "ServiceUnavailableError" in str(type(exc)) or "RateLimitError" in str(type(exc)):
                        last_error = exc
                        time.sleep(5)  # Wait longer for server recovery
                        continue

                # Re-raise unexpected errors (network, auth, quota) immediately
                raise RuntimeError(
                    f"LLM call failed (model={self.model!r}): {exc}"
                ) from exc

        raise ValueError(
            f"No se obtuvo coordenada valida del LLM tras {self.max_retries} intentos. "
            f"Ultimo error: {last_error}"
        )
