import re
import sys
from pathlib import Path

def rewrite():
    test_file = Path(r"c:\Projects\BT-Supply-Impulse\tests\test_engine.py")
    content = test_file.read_text(encoding="utf-8")
    
    # 1. Remove REQUIRED_SHIP_SIZES from imports
    content = re.sub(
        r"REQUIRED_SHIP_SIZES,\s*",
        "",
        content
    )
    
    # 2. Re-implement _make_ships and _make_valid_board
    make_ships_old = '''def _make_ships() -> list[Ship]:
    """Return a valid set of 5 ships that don't overlap."""
    return [
        Ship("P1", 5, [("A", r) for r in range(1, 6)]),   # vertical col A rows 1-5
        Ship("P2", 4, [("C", r) for r in range(1, 5)]),   # vertical col C rows 1-4
        Ship("P3", 3, [("E", r) for r in range(1, 4)]),   # vertical col E rows 1-3
        Ship("P4", 3, [("G", r) for r in range(1, 4)]),   # vertical col G rows 1-3
        Ship("P5", 2, [("I", r) for r in range(1, 3)]),   # vertical col I rows 1-2
    ]


def _make_valid_board() -> Board:
    return Board(ships=_make_ships())'''

    make_ships_new = '''def _make_ships(ship_sizes: list[int] | None = None, board_size: int = 10) -> list[Ship]:
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
    return Board(size=board_size, ships=ships, ship_sizes=ship_sizes)'''
    content = content.replace(make_ships_old, make_ships_new)

    # 3. Parametrize TestBoard
    test_board_old = '''class TestBoard:
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
        assert "#" in text'''

    test_board_new = '''@pytest.mark.parametrize("board_size, ship_sizes", [
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
        assert "#" in text'''
    content = content.replace(test_board_old, test_board_new)

    # 4. Replace REQUIRED_SHIP_SIZES with [5, 4, 3, 3, 2] in tests
    content = content.replace("REQUIRED_SHIP_SIZES", "[5, 4, 3, 3, 2]")

    # 5. Add F2.2 tests to TestAlmacenParser
    extra_tests = '''
    def test_parse_with_status_custom_sizes(self, tmp_path):
        f = tmp_path / "almacen_custom.md"
        f.write_text("P1: A1 A2 A3\\nP2: B1 B2\\nP3: C1 C2\\n", encoding="utf-8")
        ships, used_fallback, reason = AlmacenParser.parse_with_status(f, size=6, ship_sizes=[3, 2, 2])
        assert not used_fallback
        assert sorted([s.size for s in ships], reverse=True) == [3, 2, 2]

    def test_parse_file_with_larger_ship_uses_fallback(self, tmp_path):
        f = tmp_path / "almacen_large.md"
        f.write_text("P1: A1 B1 C1 D1 E1\\n", encoding="utf-8")
        ships, used_fallback, reason = AlmacenParser.parse_with_status(f, size=6, ship_sizes=[3, 2, 2])
        assert used_fallback is True

    def test_parse_empty_ship_sizes_controlled_error(self, tmp_path):
        f = tmp_path / "almacen_empty.md"
        f.write_text("P1: A1\\n", encoding="utf-8")
        # El validador interno puede o no lanzar un ValueError. Lo importante es asegurar
        # que falla por tamaños incorrectos o termina en fallback en general.
        ships, used_fallback, reason = AlmacenParser.parse_with_status(f, size=6, ship_sizes=[])
        assert used_fallback is True

    def test_parse_ship_larger_than_board_uses_fallback(self, tmp_path):
        f = tmp_path / "almacen_too_long.md"
        # Coordinadas fuera del tablero (A7 en tablero 6x6 da error de out of bounds primero,
        # provocando fallback)
        f.write_text("P1: A1 A2 A3 A4 A5 A6 A7\\n", encoding="utf-8")
        ships, used_fallback, reason = AlmacenParser.parse_with_status(f, size=6, ship_sizes=[7, 2, 2])
        assert used_fallback is True
'''
    import inspect
    # Find end of TestAlmacenParser
    parts = content.split("# Game – Golden Rule enforcement")
    parts[0] = parts[0].rstrip() + extra_tests + "\n\n\n# ═══════════════════════════════════════════════════════════════════════════════\n# Game – Golden Rule enforcement"
    content = parts[0] + parts[1]

    test_file.write_text(content, encoding="utf-8")
    print("Done")

if __name__ == "__main__":
    rewrite()
