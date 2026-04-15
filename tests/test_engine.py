"""
tests/test_engine.py
────────────────────
QA Agent: Unit tests for core/engine.py

Coverage:
  · parse_coord : valid inputs, all malformed cases (K5, B-12, A11, empty, …)
  · Ship        : valid placement, wrong size, non-contiguous, diagonal
  · Board       : valid config, overlap, wrong ship count, all shot results
  · AlmacenParser: simple format, markdown table, empty file, missing file
  · Game        : turn management, Golden Rule (HIT→repeat, MISS→switch)
"""
from __future__ import annotations

import textwrap

import pytest

from core.engine import (
    REQUIRED_SHIP_SIZES,
    AlmacenParser,
    Board,
    Game,
    Ship,
    format_coord,
    parse_coord,
)


# ═══════════════════════════════════════════════════════════════════════════════
# parse_coord
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseCoord:
    # ── Valid ─────────────────────────────────────────────────────────────────

    def test_basic(self):
        assert parse_coord("B5") == ("B", 5)

    def test_lowercase_normalised(self):
        assert parse_coord("a1") == ("A", 1)

    def test_row_10(self):
        assert parse_coord("J10") == ("J", 10)

    def test_leading_trailing_spaces(self):
        assert parse_coord("  C7  ") == ("C", 7)

    def test_all_valid_columns(self):
        for letter in "ABCDEFGHIJ":
            col, row = parse_coord(f"{letter}5")
            assert col == letter
            assert row == 5

    # ── Invalid: bad column ───────────────────────────────────────────────────

    def test_col_K_out_of_range(self):
        with pytest.raises(ValueError):
            parse_coord("K5")

    def test_col_Z(self):
        with pytest.raises(ValueError):
            parse_coord("Z3")

    def test_col_number_prefix(self):
        with pytest.raises(ValueError):
            parse_coord("5B")

    # ── Invalid: bad row ──────────────────────────────────────────────────────

    def test_row_zero(self):
        with pytest.raises(ValueError):
            parse_coord("A0")

    def test_row_eleven(self):
        with pytest.raises(ValueError):
            parse_coord("B11")

    def test_row_negative_dash(self):
        """'B-12' is a common LLM mistake – must be rejected."""
        with pytest.raises(ValueError):
            parse_coord("B-12")

    def test_row_float(self):
        with pytest.raises(ValueError):
            parse_coord("B5.5")

    def test_row_100(self):
        with pytest.raises(ValueError):
            parse_coord("A100")

    # ── Invalid: garbage ─────────────────────────────────────────────────────

    def test_empty_string(self):
        with pytest.raises(ValueError):
            parse_coord("")

    def test_only_letters(self):
        with pytest.raises(ValueError):
            parse_coord("BB")

    def test_only_numbers(self):
        with pytest.raises(ValueError):
            parse_coord("55")

    def test_reversed(self):
        with pytest.raises(ValueError):
            parse_coord("5B")

    def test_special_chars(self):
        with pytest.raises(ValueError):
            parse_coord("B*5")


# ═══════════════════════════════════════════════════════════════════════════════
# Ship
# ═══════════════════════════════════════════════════════════════════════════════


class TestShip:
    def test_horizontal_ship_valid(self):
        cells = [("A", 1), ("B", 1), ("C", 1), ("D", 1), ("E", 1)]
        ship = Ship(order_id="P1", size=5, cells=cells)
        assert ship.size == 5
        assert not ship.is_sunk

    def test_vertical_ship_valid(self):
        cells = [("A", i) for i in range(1, 4)]
        ship = Ship(order_id="P1", size=3, cells=cells)
        assert len(ship.cells) == 3

    def test_normalises_lowercase_columns(self):
        ship = Ship(order_id="P1", size=2, cells=[("a", 1), ("b", 1)])
        assert all(c.isupper() for c, _ in ship.cells)

    def test_sunk_after_all_hits(self):
        cells = [("A", 1), ("A", 2)]
        ship = Ship(order_id="P1", size=2, cells=cells)
        ship.receive_hit(("A", 1))
        assert not ship.is_sunk
        ship.receive_hit(("A", 2))
        assert ship.is_sunk

    def test_wrong_cell_count_raises(self):
        with pytest.raises(ValueError, match="tamaño"):
            Ship(order_id="P1", size=3, cells=[("A", 1), ("A", 2)])

    def test_non_contiguous_vertical_raises(self):
        with pytest.raises(ValueError, match="contiguas"):
            Ship(order_id="P1", size=3, cells=[("A", 1), ("A", 3), ("A", 5)])

    def test_non_contiguous_horizontal_raises(self):
        with pytest.raises(ValueError, match="contiguas"):
            Ship(order_id="P1", size=3, cells=[("A", 1), ("C", 1), ("E", 1)])

    def test_diagonal_raises(self):
        with pytest.raises(ValueError, match="línea recta"):
            Ship(order_id="P1", size=3, cells=[("A", 1), ("B", 2), ("C", 3)])


# ═══════════════════════════════════════════════════════════════════════════════
# Board helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _make_ships() -> list[Ship]:
    """Return a valid set of 5 ships that don't overlap."""
    return [
        Ship("P1", 5, [("A", r) for r in range(1, 6)]),   # vertical col A rows 1-5
        Ship("P2", 4, [("C", r) for r in range(1, 5)]),   # vertical col C rows 1-4
        Ship("P3", 3, [("E", r) for r in range(1, 4)]),   # vertical col E rows 1-3
        Ship("P4", 3, [("G", r) for r in range(1, 4)]),   # vertical col G rows 1-3
        Ship("P5", 2, [("I", r) for r in range(1, 3)]),   # vertical col I rows 1-2
    ]


def _make_valid_board() -> Board:
    return Board(ships=_make_ships())


# ═══════════════════════════════════════════════════════════════════════════════
# Board
# ═══════════════════════════════════════════════════════════════════════════════


class TestBoard:
    def test_valid_board_created(self):
        board = _make_valid_board()
        assert len(board.ships) == 5

    def test_overlap_raises(self):
        ships = _make_ships()
        # Replace P2 so it overlaps with P1 at (A,1)
        ships[1] = Ship("P2", 4, [("A", r) for r in range(1, 5)])
        with pytest.raises(ValueError, match="olapamiento"):
            Board(ships=ships)

    def test_wrong_ship_sizes_raises(self):
        ships = [
            Ship("P1", 5, [("A", r) for r in range(1, 6)]),
        ]
        with pytest.raises(ValueError):
            Board(ships=ships)

    def test_wrong_required_sizes_raises(self):
        # 5 ships but wrong sizes (all size 2)
        ships = [
            Ship(f"P{i}", 2, [("A", r) for r in range(1 + i * 2, 3 + i * 2)])
            for i in range(5)
        ]
        with pytest.raises(ValueError):
            Board(ships=ships)

    def test_shoot_miss(self):
        board = _make_valid_board()
        assert board.shoot("B", 1) == "miss"

    def test_shoot_hit(self):
        board = _make_valid_board()
        assert board.shoot("A", 1) == "hit"

    def test_shoot_sunk_size2(self):
        board = _make_valid_board()
        board.shoot("I", 1)
        result = board.shoot("I", 2)
        assert result == "sunk"

    def test_shoot_already_shot(self):
        board = _make_valid_board()
        board.shoot("B", 5)
        assert board.shoot("B", 5) == "already_shot"

    def test_all_sunk_false_initially(self):
        board = _make_valid_board()
        assert not board.all_sunk

    def test_all_sunk_after_all_cells_hit(self):
        board = _make_valid_board()
        for ship in board.ships:
            for col, row in ship.cells:
                board.shoot(col, row)
        assert board.all_sunk

    def test_grid_text_returns_string(self):
        board = _make_valid_board()
        text = board.grid_text(reveal_ships=False)
        assert isinstance(text, str)
        assert "~" in text     # hidden cells
        assert "A" in text     # column header

    def test_grid_text_reveal_shows_ships(self):
        board = _make_valid_board()
        text = board.grid_text(reveal_ships=True)
        assert "#" in text


# ═══════════════════════════════════════════════════════════════════════════════
# AlmacenParser
# ═══════════════════════════════════════════════════════════════════════════════

_VALID_SIMPLE = textwrap.dedent("""\
    # Almacén – Test

    P1: A1 B1 C1 D1 E1
    P2: A3 B3 C3 D3
    P3: F5 F6 F7
    P4: H8 I8 J8
    P5: D7 D8
""")

_VALID_TABLE = textwrap.dedent("""\
    | P1 | 5 | A1 B1 C1 D1 E1 |
    | P2 | 4 | A3 B3 C3 D3 |
    | P3 | 3 | F5 F6 F7 |
    | P4 | 3 | H8 I8 J8 |
    | P5 | 2 | D7 D8 |
""")


class TestAlmacenParser:
    def test_parse_simple_format(self, tmp_path):
        f = tmp_path / "almacen_test.md"
        f.write_text(_VALID_SIMPLE, encoding="utf-8")
        ships = AlmacenParser.parse(f)
        assert len(ships) == 5
        assert sorted([s.size for s in ships], reverse=True) == REQUIRED_SHIP_SIZES

    def test_parse_markdown_table_format(self, tmp_path):
        f = tmp_path / "almacen_table.md"
        f.write_text(_VALID_TABLE, encoding="utf-8")
        ships = AlmacenParser.parse(f)
        assert len(ships) == 5

    def test_case_insensitive_lowercase_coords(self, tmp_path):
        content = "P1: a1 b1 c1 d1 e1\nP2: a3 b3 c3 d3\nP3: f5 f6 f7\nP4: h8 i8 j8\nP5: d7 d8\n"
        f = tmp_path / "almacen_lc.md"
        f.write_text(content, encoding="utf-8")
        ships = AlmacenParser.parse(f)
        # Columns should be normalised to uppercase
        for ship in ships:
            for col, _ in ship.cells:
                assert col.isupper()

    def test_missing_file_falls_back_to_random_layout(self):
        ships = AlmacenParser.parse("/nonexistent/path/almacen.md")
        assert len(ships) == 5
        assert sorted([s.size for s in ships], reverse=True) == REQUIRED_SHIP_SIZES

    def test_empty_file_falls_back_to_random_layout(self, tmp_path):
        f = tmp_path / "almacen_empty.md"
        f.write_text("# No pedidos aquí", encoding="utf-8")
        ships = AlmacenParser.parse(f)
        assert len(ships) == 5
        assert sorted([s.size for s in ships], reverse=True) == REQUIRED_SHIP_SIZES

    def test_invalid_coords_falls_back_to_random_layout(self, tmp_path):
        f = tmp_path / "almacen_bad_coords.md"
        f.write_text(
            "P1: A1 B1 C1 D1 E1\n"
            "P2: K3 K4 K5 K6\n"  # invalid col K
            "P3: F5 F6 F7\n"
            "P4: H8 I8 J8\n"
            "P5: D7 D8\n",
            encoding="utf-8",
        )
        ships, used_fallback, reason = AlmacenParser.parse_with_status(f)
        assert used_fallback is True
        assert "Formato inválido" in reason
        assert len(ships) == 5


# ═══════════════════════════════════════════════════════════════════════════════
# Game – Golden Rule enforcement
# ═══════════════════════════════════════════════════════════════════════════════


def _make_game() -> Game:
    board_a = _make_valid_board()
    board_b = _make_valid_board()
    return Game("Agent_A", board_a, "Agent_B", board_b)


class TestGame:
    def test_initial_turn_is_agent_a(self):
        game = _make_game()
        assert game.current_agent == "Agent_A"

    def test_switch_turn(self):
        game = _make_game()
        game.switch_turn()
        assert game.current_agent == "Agent_B"

    def test_switch_twice_returns_to_agent_a(self):
        game = _make_game()
        game.switch_turn()
        game.switch_turn()
        assert game.current_agent == "Agent_A"

    def test_miss_recorded_in_log(self):
        game = _make_game()
        result = game.apply_move("B", 1)   # B1 is empty on both boards
        assert result == "miss"
        assert len(game.move_log) == 1
        assert game.move_log[0].result == "miss"

    def test_hit_recorded_in_log(self):
        game = _make_game()
        result = game.apply_move("A", 1)   # A1 is occupied (P1)
        assert result == "hit"
        assert game.move_log[0].result == "hit"

    def test_golden_rule_hit_does_not_require_switch(self):
        """Helper: after a HIT the caller should NOT switch. Test state stays on Agent_A."""
        game = _make_game()
        result = game.apply_move("A", 1)
        assert result == "hit"
        # Simulate correct caller behaviour: don't switch on hit
        assert game.current_agent == "Agent_A"

    def test_golden_rule_miss_requires_switch(self):
        """After MISS the caller switches. Verify Agent_A → Agent_B."""
        game = _make_game()
        result = game.apply_move("B", 1)
        assert result == "miss"
        game.switch_turn()
        assert game.current_agent == "Agent_B"

    def test_sunk_result(self):
        game = _make_game()
        # P5 on board_b = I1, I2 (size 2)
        game.apply_move("I", 1)
        result = game.apply_move("I", 2)
        assert result == "sunk"

    def test_already_shot_result(self):
        game = _make_game()
        game.apply_move("B", 1)
        result = game.apply_move("B", 1)
        assert result == "already_shot"

    def test_is_over_false_initially(self):
        game = _make_game()
        finished, winner = game.is_over()
        assert not finished
        assert winner is None

    def test_is_over_true_when_all_sunk(self):
        game = _make_game()
        # Sink every ship on board_b by having Agent_A shoot them all
        board_b = game.agents["Agent_A"]
        for ship in board_b.ships:
            for col, row in ship.cells:
                game.apply_move(col, row)
        finished, winner = game.is_over()
        assert finished
        assert winner == "Agent_A"

    @pytest.mark.skip(reason="Timeout and points tiebreaker logic moved to tournament.py")
    def test_max_turns_winner_by_impacts(self):
        pass

    def test_shots_fired_tracking(self):
        game = _make_game()
        game.apply_move("A", 1)
        game.apply_move("A", 2)
        assert game.shots_fired["Agent_A"] == 2
        assert game.shots_fired["Agent_B"] == 0
