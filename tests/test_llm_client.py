"""
tests/test_llm_client.py
────────────────────────
QA Agent: Unit tests for core/llm_client.py

Coverage:
  · AgentMove Pydantic model:
      - Accepts all valid A-J + 1-10 coordinates
      - Rejects every known LLM failure mode (B-12, K5, A11, reversed, empty, …)
      - Normalises lowercase to uppercase
  · LLMClient.build_prompt:
      - Contains agent.md content
      - Contains board text
      - Lists move history (max 5)
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.llm_client import AgentMove, LLMClient, MoveHistoryEntry


# ═══════════════════════════════════════════════════════════════════════════════
# AgentMove validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentMoveValidCoords:
    """QA: All 100 valid board cells should be accepted."""

    def test_a1(self):
        m = AgentMove(coordenada="A1", razonamiento="r", estrategia_aplicada="e")
        assert m.coordenada == "A1"

    def test_j10(self):
        m = AgentMove(coordenada="J10", razonamiento="r", estrategia_aplicada="e")
        assert m.coordenada == "J10"

    def test_lowercase_normalised_to_uppercase(self):
        m = AgentMove(coordenada="b5", razonamiento="r", estrategia_aplicada="e")
        assert m.coordenada == "B5"

    def test_leading_trailing_spaces_stripped(self):
        m = AgentMove(coordenada="  C7  ", razonamiento="r", estrategia_aplicada="e")
        assert m.coordenada == "C7"

    @pytest.mark.parametrize("coord", ["A1", "A10", "J1", "J10", "E5", "F6", "H8"])
    def test_parametrised_valid(self, coord: str):
        m = AgentMove(coordenada=coord, razonamiento="r", estrategia_aplicada="e")
        assert len(m.coordenada) in (2, 3)


class TestAgentMoveInvalidCoords:
    """QA Agent: every invalid format must raise ValidationError, not crash silently."""

    # ── Column out of range ───────────────────────────────────────────────────

    def test_col_K_llm_mistake(self):
        """Classic LLM error: column K is outside the board."""
        with pytest.raises(ValidationError):
            AgentMove(coordenada="K5", razonamiento="r", estrategia_aplicada="e")

    def test_col_L(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="L3", razonamiento="r", estrategia_aplicada="e")

    def test_col_Z(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="Z1", razonamiento="r", estrategia_aplicada="e")

    # ── Row out of range ──────────────────────────────────────────────────────

    def test_row_zero(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="A0", razonamiento="r", estrategia_aplicada="e")

    def test_row_eleven(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="A11", razonamiento="r", estrategia_aplicada="e")

    def test_row_hundred(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="A100", razonamiento="r", estrategia_aplicada="e")

    # ── Negative / dash formats ───────────────────────────────────────────────

    def test_negative_row_dash(self):
        """'B-12' is a known LLM hallucination."""
        with pytest.raises(ValidationError):
            AgentMove(coordenada="B-12", razonamiento="r", estrategia_aplicada="e")

    def test_negative_row_minus_one(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="C-1", razonamiento="r", estrategia_aplicada="e")

    # ── Reversed / malformed ─────────────────────────────────────────────────

    def test_reversed_number_first(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="5B", razonamiento="r", estrategia_aplicada="e")

    def test_only_letters(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="BB", razonamiento="r", estrategia_aplicada="e")

    def test_only_numbers(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="55", razonamiento="r", estrategia_aplicada="e")

    def test_empty_string(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="", razonamiento="r", estrategia_aplicada="e")

    def test_float_row(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="B5.5", razonamiento="r", estrategia_aplicada="e")

    def test_with_asterisk(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="B*5", razonamiento="r", estrategia_aplicada="e")

    def test_with_space_inside(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="B 5", razonamiento="r", estrategia_aplicada="e")

    # ── Security: injection attempts ─────────────────────────────────────────

    def test_sql_injection_attempt(self):
        """Coordinate field must reject SQL injection gracefully."""
        with pytest.raises(ValidationError):
            AgentMove(
                coordenada="'; DROP TABLE--",
                razonamiento="",
                estrategia_aplicada="",
            )

    def test_script_injection_attempt(self):
        with pytest.raises(ValidationError):
            AgentMove(
                coordenada="<script>",
                razonamiento="r",
                estrategia_aplicada="e",
            )

    # ── Missing required fields ───────────────────────────────────────────────

    def test_missing_razonamiento(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="B5", estrategia_aplicada="test")  # type: ignore[call-arg]

    def test_missing_estrategia(self):
        with pytest.raises(ValidationError):
            AgentMove(coordenada="B5", razonamiento="test")  # type: ignore[call-arg]

    def test_missing_coordenada(self):
        with pytest.raises(ValidationError):
            AgentMove(razonamiento="r", estrategia_aplicada="e")  # type: ignore[call-arg]


# ═══════════════════════════════════════════════════════════════════════════════
# LLMClient.build_prompt (no LLM call needed)
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildPrompt:
    """Unit-test the prompt builder in isolation (no external LLM call)."""

    def _client(self) -> LLMClient:
        # We instantiate without calling LLM – litellm import may or may not exist
        try:
            return LLMClient(model="gemini/gemini-1.5-pro")
        except ImportError:
            pytest.skip("litellm not installed")

    def test_agent_md_injected(self):
        client = self._client()
        prompt = client.build_prompt(
            agent_md="MY STRATEGY HERE",
            opponent_board_text="~ ~ ~",
            move_history=[],
            my_name="Team_A",
            opponent_name="Team_B",
        )
        assert "MY STRATEGY HERE" in prompt

    def test_board_text_injected(self):
        client = self._client()
        prompt = client.build_prompt(
            agent_md="strategy",
            opponent_board_text="BOARD_CONTENT_XYZ",
            move_history=[],
            my_name="Team_A",
            opponent_name="Team_B",
        )
        assert "BOARD_CONTENT_XYZ" in prompt

    def test_team_names_injected(self):
        client = self._client()
        prompt = client.build_prompt(
            agent_md="s",
            opponent_board_text="b",
            move_history=[],
            my_name="ALPHA",
            opponent_name="BETA",
        )
        assert "ALPHA" in prompt
        assert "BETA" in prompt

    def test_history_limited_to_last_5(self):
        client = self._client()
        history = [
            MoveHistoryEntry(turno=i, agente="A", coordenada=f"A{i}", resultado="miss")
            for i in range(1, 11)   # 10 entries
        ]
        prompt = client.build_prompt(
            agent_md="s",
            opponent_board_text="b",
            move_history=history,
            my_name="A",
            opponent_name="B",
        )
        # Last 5 entries (turns 6-10) must be in the prompt
        assert "A10" in prompt
        assert "A6" in prompt
        # Older entries (turns 1-5) must be pruned; verify via turn bracket label
        assert "T  1]" not in prompt
        assert "T  5]" not in prompt
        assert "T  6]" in prompt

    def test_empty_history_shows_placeholder(self):
        client = self._client()
        prompt = client.build_prompt(
            agent_md="s",
            opponent_board_text="b",
            move_history=[],
            my_name="A",
            opponent_name="B",
        )
        assert "ningún movimiento" in prompt


class TestLocalJsonCleanup:
    def _client(self, model: str = "ollama/gemma4") -> LLMClient:
        try:
            return LLMClient(model=model)
        except ImportError:
            pytest.skip("litellm not installed")

    def test_strip_json_fences(self):
        client = self._client()
        raw = """```json
        {"coordenada":"B5","razonamiento":"x","estrategia_aplicada":"y"}
        ```"""
        cleaned = client._normalize_raw_response(raw)
        assert cleaned.startswith("{")
        assert cleaned.endswith("}")

    def test_extract_json_from_extra_text(self):
        client = self._client()
        raw = "Respuesta:\n{" \
              "\"coordenada\":\"C7\",\"razonamiento\":\"r\",\"estrategia_aplicada\":\"e\"" \
              "}\nGracias"
        cleaned = client._normalize_raw_response(raw)
        data = AgentMove.model_validate_json(cleaned)
        assert data.coordenada == "C7"

    def test_cloud_model_keeps_raw(self):
        client = self._client(model="gemini/gemini-1.5-flash")
        raw = '{"coordenada":"A1","razonamiento":"r","estrategia_aplicada":"e"}'
        assert client._normalize_raw_response(raw) == raw
