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

_SYSTEM_PROMPT = """Eres un estratega en 'Garment Strike'. Tablero 10x10 (A-J, 1-10).
Responde SOLO con un JSON en UNA SOLA LINEA, ejemplo:
{"coordenada":"E5","razonamiento":"Centro del tablero","estrategia_aplicada":"Damero"}
IMPORTANTE: JSON en UNA sola linea, sin saltos de linea, sin explicaciones extra."""


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
        max_tokens: int = 256,
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

    def build_prompt(
        self,
        agent_md: str,
        opponent_board_text: str,
        move_history: list[MoveHistoryEntry],
        my_name: str,
        opponent_name: str,
    ) -> str:
        # Keep it short - this is the KEY insight from debugging
        return (
            f"ESTRATEGIA: {agent_md}\n"
            f"TABLERO: {opponent_board_text}\n"
            f"Responde con JSON en UNA linea."
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
        Retries up to max_retries times. Each retry is a FRESH call
        (no accumulated corrections that poison the context).
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
                # CRITICAL: Fresh messages each attempt - never accumulate corrections
                messages = [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]

                request_kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                }

                # Pass num_predict for Ollama compatibility
                if self.is_local_model:
                    request_kwargs["num_predict"] = self.max_tokens

                # --- DEBUG LOG ---
                with open("llm_debug.log", "a", encoding="utf-8") as debug_f:
                    debug_f.write(f"\n{'='*80}\n")
                    debug_f.write(f"TURNO: {my_name} | Intento: {attempt}\n")
                    debug_f.write(f"PROMPT ({len(prompt)} chars): {prompt[:200]}...\n")
                    debug_f.write(f"{'-'*80}\n")

                response = litellm.completion(**request_kwargs)
                raw = (response.choices[0].message.content or "").strip()

                # --- DEBUG RESPONSE ---
                with open("llm_debug.log", "a", encoding="utf-8") as debug_f:
                    debug_f.write(f"RESP ({len(raw)} chars): {raw}\n")

                if not raw:
                    raise ValueError("La API devolvio una respuesta vacia.")

                # Parse with multi-stage fallback (handles fences + truncation)
                data = self._parse_response(raw)
                data["latency_ms"] = (time.perf_counter() - start_time) * 1000.0
                move = AgentMove(**data)
                
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
                # Re-raise unexpected errors (network, auth, quota) immediately
                raise RuntimeError(
                    f"LLM call failed (model={self.model!r}): {exc}"
                ) from exc

        raise ValueError(
            f"No se obtuvo coordenada valida del LLM tras {self.max_retries} intentos. "
            f"Ultimo error: {last_error}"
        )
