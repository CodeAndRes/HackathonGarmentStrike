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
    AlmacenParser,
    Board,
    Game,
    Ship,
    format_coord,
    parse_coord,
    validate_game_config,
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


def _make_ships(ship_sizes: list[int] | None = None, board_size: int = 10) -> list[Ship]:
    """Return a valid set of ships that don't overlap."""
    if ship_sizes is None:
        ship_sizes = [5, 4, 3, 3, 2]
    ships = []
    cols = "ABCDEFGHIJ"
    for i, size in enumerate(ship_sizes):
        col = cols[i]
        ships.append(Ship(f"P{i+1}", size, [(col, r) for r in range(1, size + 1)]))
    return ships


def _make_valid_board(ship_sizes: list[int] | None = None, board_size: int = 10) -> Board:
    if ship_sizes is None:
        ship_sizes = [5, 4, 3, 3, 2]
    ships = _make_ships(ship_sizes, board_size)
    return Board(size=board_size, ships=ships, ship_sizes=ship_sizes)


# ═══════════════════════════════════════════════════════════════════════════════
# Board
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("board_size, ship_sizes", [
    (10, [5, 4, 3, 3, 2]),
    (6, [3, 3, 2]),
    (8, [4, 3, 2, 2]),
    (6, [2, 2]),
])
class TestBoard:
    def test_valid_board_created(self, board_size, ship_sizes):
        board = _make_valid_board(ship_sizes, board_size)
        assert len(board.ships) == len(ship_sizes)

    def test_overlap_raises(self, board_size, ship_sizes):
        ships = _make_ships(ship_sizes, board_size)
        if len(ships) < 2:
            pytest.skip("Necesita al menos 2 barcos para testear solapamiento")
        first_col = ships[0].cells[0][0]
        ships[1] = Ship("P2", ships[1].size, [(first_col, r) for r in range(1, ships[1].size + 1)])
        with pytest.raises(ValueError, match="olapamiento"):
            Board(size=board_size, ships=ships, ship_sizes=ship_sizes)

    def test_wrong_ship_sizes_raises(self, board_size, ship_sizes):
        ships = _make_ships(ship_sizes, board_size)
        ships = ships[:-1]
        with pytest.raises(ValueError):
            Board(size=board_size, ships=ships, ship_sizes=ship_sizes)

    def test_wrong_required_sizes_raises(self, board_size, ship_sizes):
        ships = _make_ships(ship_sizes, board_size)
        invalid_cells = ships[0].cells[:1]
        if not invalid_cells:
            invalid_cells = [("A", 1)]
        ships[0] = Ship("P1", 1, invalid_cells) # invalid size 1
        with pytest.raises(ValueError):
            Board(size=board_size, ships=ships, ship_sizes=ship_sizes)

    def _get_miss_coord(self, board: Board):
        cells = {c for s in board.ships for c in s.cells}
        for r in board.rows:
            for c in board.cols:
                if (c, r) not in cells:
                    return c, r
        return board.cols[-1], board.rows[-1]

    def test_shoot_miss(self, board_size, ship_sizes):
        board = _make_valid_board(ship_sizes, board_size)
        mc, mr = self._get_miss_coord(board)
        assert board.shoot(mc, mr) == "miss"

    def test_shoot_hit(self, board_size, ship_sizes):
        board = _make_valid_board(ship_sizes, board_size)
        c, r = board.ships[0].cells[0]
        assert board.shoot(c, r) == "hit"

    def test_shoot_sunk_size2(self, board_size, ship_sizes):
        board = _make_valid_board(ship_sizes, board_size)
        ship = min(board.ships, key=lambda s: s.size)
        for c, r in ship.cells[:-1]:
            board.shoot(c, r)
        c, r = ship.cells[-1]
        result = board.shoot(c, r)
        assert result == "sunk"

    def test_shoot_already_shot(self, board_size, ship_sizes):
        board = _make_valid_board(ship_sizes, board_size)
        mc, mr = self._get_miss_coord(board)
        board.shoot(mc, mr)
        assert board.shoot(mc, mr) == "already_shot"

    def test_all_sunk_false_initially(self, board_size, ship_sizes):
        board = _make_valid_board(ship_sizes, board_size)
        assert not board.all_sunk

    def test_all_sunk_after_all_cells_hit(self, board_size, ship_sizes):
        board = _make_valid_board(ship_sizes, board_size)
        for ship in board.ships:
            for col, row in ship.cells:
                board.shoot(col, row)
        assert board.all_sunk

    def test_grid_text_returns_string(self, board_size, ship_sizes):
        board = _make_valid_board(ship_sizes, board_size)
        text = board.grid_text(reveal_ships=False)
        assert isinstance(text, str)
        assert "~" in text     # hidden cells

    def test_grid_text_reveal_shows_ships(self, board_size, ship_sizes):
        board = _make_valid_board(ship_sizes, board_size)
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
        assert sorted([s.size for s in ships], reverse=True) == [5, 4, 3, 3, 2]

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
        assert sorted([s.size for s in ships], reverse=True) == [5, 4, 3, 3, 2]

    def test_empty_file_falls_back_to_random_layout(self, tmp_path):
        f = tmp_path / "almacen_empty.md"
        f.write_text("# No pedidos aquí", encoding="utf-8")
        ships = AlmacenParser.parse(f)
        assert len(ships) == 5
        assert sorted([s.size for s in ships], reverse=True) == [5, 4, 3, 3, 2]

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
    def test_parse_with_status_custom_sizes(self, tmp_path):
        f = tmp_path / "almacen_custom.md"
        f.write_text("P1: A1 A2 A3\nP2: B1 B2\nP3: C1 C2\n", encoding="utf-8")
        ships, used_fallback, reason = AlmacenParser.parse_with_status(f, size=6, ship_sizes=[3, 2, 2])
        assert not used_fallback
        assert sorted([s.size for s in ships], reverse=True) == [3, 2, 2]

    def test_parse_file_with_larger_ship_uses_fallback(self, tmp_path):
        f = tmp_path / "almacen_large.md"
        f.write_text("P1: A1 B1 C1 D1 E1\n", encoding="utf-8")
        ships, used_fallback, reason = AlmacenParser.parse_with_status(f, size=6, ship_sizes=[3, 2, 2])
        assert used_fallback is True

    def test_parse_empty_ship_sizes_controlled_error(self, tmp_path):
        f = tmp_path / "almacen_empty.md"
        f.write_text("P1: A1\n", encoding="utf-8")
        # El validador interno puede o no lanzar un ValueError. Lo importante es asegurar
        # que falla por tamaños incorrectos o termina en fallback en general.
        ships, used_fallback, reason = AlmacenParser.parse_with_status(f, size=6, ship_sizes=[])
        assert used_fallback is True

    def test_parse_ship_larger_than_board_uses_fallback(self, tmp_path):
        f = tmp_path / "almacen_too_long.md"
        # Coordinadas fuera del tablero (A7 en tablero 6x6 da error de out of bounds primero,
        # provocando fallback)
        f.write_text("P1: A1 A2 A3 A4 A5 A6 A7\n", encoding="utf-8")
        ships, used_fallback, reason = AlmacenParser.parse_with_status(f, size=6, ship_sizes=[7, 2, 2])
        assert used_fallback is True



# ═══════════════════════════════════════════════════════════════════════════════
# Game – Golden Rule enforcement
# ═══════════════════════════════════════════════════════════════════════════════


def _make_game() -> Game:
    board_a = _make_valid_board()
    board_b = _make_valid_board()
    return Game("Agent_A", board_a, "Agent_B", board_b)


class TestGame:
    def _get_miss_coord(self, board: Board):
        cells = {c for s in board.ships for c in s.cells}
        for r in board.rows:
            for c in board.cols:
                if (c, r) not in cells:
                    return c, r
        return board.cols[-1], board.rows[-1]

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
        c, r = self._get_miss_coord(game.agents["Agent_A"])
        result = game.apply_move(c, r)
        assert result == "miss"
        assert len(game.move_log) == 1
        assert game.move_log[0].result == "miss"

    def test_hit_recorded_in_log(self):
        game = _make_game()
        c, r = game.agents["Agent_A"].ships[0].cells[0]
        result = game.apply_move(c, r)
        assert result == "hit"
        assert game.move_log[0].result == "hit"

    def test_golden_rule_hit_does_not_require_switch(self):
        """Helper: after a HIT the caller should NOT switch. Test state stays on Agent_A."""
        game = _make_game()
        c, r = game.agents["Agent_A"].ships[0].cells[0]
        result = game.apply_move(c, r)
        assert result == "hit"
        # Simulate correct caller behaviour: don't switch on hit
        assert game.current_agent == "Agent_A"

    def test_golden_rule_miss_requires_switch(self):
        """After MISS the caller switches. Verify Agent_A → Agent_B."""
        game = _make_game()
        c, r = self._get_miss_coord(game.agents["Agent_A"])
        result = game.apply_move(c, r)
        assert result == "miss"
        game.switch_turn()
        assert game.current_agent == "Agent_B"

    def test_sunk_result(self):
        game = _make_game()
        ship = min(game.agents["Agent_A"].ships, key=lambda s: s.size)
        for c, r in ship.cells[:-1]:
            game.apply_move(c, r)
        c, r = ship.cells[-1]
        result = game.apply_move(c, r)
        assert result == "sunk"

    def test_already_shot_result(self):
        game = _make_game()
        c, r = self._get_miss_coord(game.agents["Agent_A"])
        game.apply_move(c, r)
        result = game.apply_move(c, r)
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
        c, r = game.agents["Agent_A"].ships[0].cells[0]
        game.apply_move(c, r)
        c2, r2 = game.agents["Agent_A"].ships[0].cells[1]
        game.apply_move(c2, r2)
        assert game.shots_fired["Agent_A"] == 2
        assert game.shots_fired["Agent_B"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# F1.2 – ship_sizes propagation
# ═══════════════════════════════════════════════════════════════════════════════


class TestShipSizesPropagation:
    """Verify ship_sizes flows correctly through Board, AlmacenParser, and generate_random_layout."""

    def test_board_stores_custom_ship_sizes(self):
        custom = [3, 2, 2]
        board = Board(size=6, ships=[], ship_sizes=custom)
        assert board.ship_sizes == sorted(custom, reverse=True)

    def test_board_defaults_to_required_when_none(self):
        board = Board(size=10, ships=[])
        assert board.ship_sizes == [5, 4, 3, 3, 2]

    def test_board_validates_custom_sizes_on_placement(self):
        """Board with custom ship_sizes should reject ships that don't match."""
        ships = [
            Ship("P1", 3, [("A", 1), ("B", 1), ("C", 1)]),
            Ship("P2", 2, [("E", 1), ("F", 1)]),
        ]
        # Expect [3, 2] but only one size-2 ship → config mismatch
        with pytest.raises(ValueError, match="incorrecta"):
            Board(size=6, ships=[ships[0]], ship_sizes=[3, 2])

    def test_board_6x6_with_custom_ships(self):
        """A 6x6 board with [3, 2, 2] should work perfectly."""
        ships = [
            Ship("P1", 3, [("A", 1), ("B", 1), ("C", 1)]),
            Ship("P2", 2, [("E", 1), ("F", 1)]),
            Ship("P3", 2, [("A", 3), ("B", 3)]),
        ]
        board = Board(size=6, ships=ships, ship_sizes=[3, 2, 2])
        assert len(board.ships) == 3
        assert board.ship_sizes == [3, 2, 2]

    def test_board_8x8_with_custom_ships(self):
        """An 8x8 board with [4, 3, 2] should work."""
        ships = [
            Ship("P1", 4, [("A", r) for r in range(1, 5)]),
            Ship("P2", 3, [("C", r) for r in range(1, 4)]),
            Ship("P3", 2, [("E", 1), ("E", 2)]),
        ]
        board = Board(size=8, ships=ships, ship_sizes=[4, 3, 2])
        assert len(board.ships) == 3

    def test_generate_random_layout_custom_sizes(self):
        """generate_random_layout with custom sizes should produce matching ships."""
        custom = [3, 2, 2]
        ships = AlmacenParser.generate_random_layout(size=6, ship_sizes=custom)
        actual = sorted([s.size for s in ships], reverse=True)
        assert actual == sorted(custom, reverse=True)

    def test_generate_random_layout_defaults_to_required(self):
        """Without ship_sizes, generate_random_layout should use [5, 4, 3, 3, 2]."""
        ships = AlmacenParser.generate_random_layout(size=10)
        actual = sorted([s.size for s in ships], reverse=True)
        assert actual == [5, 4, 3, 3, 2]

    def test_parser_fallback_uses_custom_sizes(self, tmp_path):
        """When an almacen file is invalid, fallback should use the provided custom sizes."""
        f = tmp_path / "almacen_bad.md"
        f.write_text("garbage content, not valid", encoding="utf-8")
        custom = [3, 2, 2]
        ships, used_fallback, _ = AlmacenParser.parse_with_status(f, size=6, ship_sizes=custom)
        assert used_fallback is True
        actual = sorted([s.size for s in ships], reverse=True)
        assert actual == sorted(custom, reverse=True)

    def test_board_rejects_ship_larger_than_board(self):
        """A ship of size 7 should be rejected on a 6x6 board."""
        with pytest.raises(ValueError, match="exceeds board size"):
            Board(size=6, ships=[], ship_sizes=[7, 2])

    def test_board_rejects_ship_size_1(self):
        """Ships of size 1 are not allowed."""
        with pytest.raises(ValueError, match="Minimum ship size"):
            Board(size=6, ships=[], ship_sizes=[3, 1])

    def test_board_rejects_too_many_ship_cells(self):
        """Total ship cells exceeding 50% of board area should be rejected."""
        # 6x6 = 36 cells, 50% = 18. [5,5,5,5] = 20 cells → too many
        with pytest.raises(ValueError, match="exceed 50%"):
            Board(size=6, ships=[], ship_sizes=[5, 5, 5, 5])


# ═══════════════════════════════════════════════════════════════════════════════
# F1.4 – validate_game_config
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidateGameConfig:
    """Tests for the centralized pre-flight config validator."""

    def test_valid_config_passes(self):
        """A valid configuration should not raise."""
        validate_game_config(board_size=6, ship_sizes=[3, 2, 2])

    def test_valid_default_config_passes(self):
        """The default configuration (10x10, [5,4,3,3,2]) should pass."""
        validate_game_config(board_size=10, ship_sizes=[5, 4, 3, 3, 2])

    def test_board_size_too_small(self):
        with pytest.raises(ValueError, match="entre 6 y 10"):
            validate_game_config(board_size=5, ship_sizes=[3, 2])

    def test_board_size_too_large(self):
        with pytest.raises(ValueError, match="entre 6 y 10"):
            validate_game_config(board_size=11, ship_sizes=[3, 2])

    def test_ship_larger_than_board(self):
        with pytest.raises(ValueError, match="mayor que el tablero"):
            validate_game_config(board_size=6, ship_sizes=[7, 2])

    def test_ship_size_1_rejected(self):
        with pytest.raises(ValueError, match="mínimo"):
            validate_game_config(board_size=10, ship_sizes=[5, 1])

    def test_total_cells_exceed_half_board(self):
        """50% of a 6x6 board = 18 cells. [5,5,5,5]=20 → should fail."""
        with pytest.raises(ValueError, match="excede el 50%"):
            validate_game_config(board_size=6, ship_sizes=[5, 5, 5, 5])

