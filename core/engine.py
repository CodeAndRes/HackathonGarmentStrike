"""
core/engine.py
──────────────
Pure game logic for Garment Strike (10×10 Supply Chain Battleship).

Board   : A1–J10  (columns A-J, rows 1-10)
Pedidos : sizes 5, 4, 3, 3, 2  (must all be placed)
Rules   : HIT or SUNK → same agent shoots again (handled by caller).

Developer Agent  – core board logic.
Reviewer Agent   – enforces the repeat-turn rule via ShotResult literals.
"""
from __future__ import annotations

import random
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# ── Constants ─────────────────────────────────────────────────────────────────

BOARD_COLS: list[str] = list("ABCDEFGHIJ")
BOARD_ROWS: list[int] = list(range(1, 11))

# Canonical ship configuration – sorted descending for comparison
REQUIRED_SHIP_SIZES: list[int] = sorted([5, 4, 3, 3, 2], reverse=True)

ShotResult = Literal["hit", "miss", "sunk", "already_shot"]

_COORD_RE = re.compile(r"^([A-Ja-j])(10|[1-9])$")


# ── Coordinate helpers ────────────────────────────────────────────────────────


def parse_coord(raw: str) -> tuple[str, int]:
    """Parse 'B5' → ('B', 5).  Raises ValueError on invalid format."""
    m = _COORD_RE.match(raw.strip())
    if not m:
        raise ValueError(
            f"Coordenada inválida: {raw!r}. "
            "Formato esperado: letra A-J + número 1-10  (ej: B5, J10)."
        )
    return m.group(1).upper(), int(m.group(2))


def format_coord(col: str, row: int) -> str:
    return f"{col.upper()}{row}"


# ── Ship (Pedido / Caja) ──────────────────────────────────────────────────────


@dataclass
class Ship:
    """One order/box placed on the board."""

    order_id: str
    size: int
    cells: list[tuple[str, int]]   # normalised: (UPPERCASE col, int row)
    hits: set[tuple[str, int]] = field(default_factory=set)

    def __post_init__(self) -> None:
        # Normalise column letters to uppercase
        self.cells = [(c.upper(), r) for c, r in self.cells]
        if len(self.cells) != self.size:
            raise ValueError(
                f"Pedido {self.order_id!r}: declara tamaño {self.size} "
                f"pero tiene {len(self.cells)} celdas."
            )
        self._validate_contiguous()

    def _validate_contiguous(self) -> None:
        cols = [c for c, _ in self.cells]
        rows = [r for _, r in self.cells]
        unique_cols = set(cols)
        unique_rows = set(rows)

        if len(unique_cols) == 1:
            # Vertical
            sorted_rows = sorted(rows)
            expected = list(range(sorted_rows[0], sorted_rows[0] + self.size))
            if sorted_rows != expected:
                raise ValueError(
                    f"Pedido {self.order_id!r}: celdas verticales no contiguas – {self.cells}"
                )
        elif len(unique_rows) == 1:
            # Horizontal
            col_idxs = sorted(BOARD_COLS.index(c) for c in cols)
            expected = list(range(col_idxs[0], col_idxs[0] + self.size))
            if col_idxs != expected:
                raise ValueError(
                    f"Pedido {self.order_id!r}: celdas horizontales no contiguas – {self.cells}"
                )
        else:
            raise ValueError(
                f"Pedido {self.order_id!r}: las celdas no están en línea recta – {self.cells}"
            )

    def receive_hit(self, coord: tuple[str, int]) -> None:
        self.hits.add(coord)

    @property
    def is_sunk(self) -> bool:
        return len(self.hits) >= self.size


# ── Board ─────────────────────────────────────────────────────────────────────


class Board:
    """One player's 10 × 10 ocean grid."""

    def __init__(self, ships: list[Ship]) -> None:
        self.ships = ships
        # Maps coord → result of the shot that landed there
        self.shots_received: dict[tuple[str, int], ShotResult] = {}
        self._validate_placement()

    # -- Validation -----------------------------------------------------------

    def _validate_placement(self) -> None:
        seen: set[tuple[str, int]] = set()
        for ship in self.ships:
            for col, row in ship.cells:
                if col not in BOARD_COLS or row not in BOARD_ROWS:
                    raise ValueError(
                        f"Celda {format_coord(col, row)} fuera del tablero (A1–J10)."
                    )
                if (col, row) in seen:
                    raise ValueError(
                        f"Solapamiento detectado en {format_coord(col, row)}."
                    )
                seen.add((col, row))

        actual_sizes = sorted([s.size for s in self.ships], reverse=True)
        if actual_sizes != REQUIRED_SHIP_SIZES:
            raise ValueError(
                f"Configuración de pedidos incorrecta. "
                f"Esperado {REQUIRED_SHIP_SIZES}, recibido {actual_sizes}."
            )

    # -- Shooting -------------------------------------------------------------

    def shoot(self, col: str, row: int) -> ShotResult:
        """
        Apply one shot from the opponent.
        Returns ShotResult – caller is responsible for turn management:
          · 'hit' or 'sunk'  → same agent shoots again (Golden Rule).
          · 'miss'           → switch to other agent.
          · 'already_shot'   → treat as wasted turn / error.
        """
        coord = (col.upper(), row)
        if coord in self.shots_received:
            return "already_shot"
        for ship in self.ships:
            if coord in ship.cells:
                ship.receive_hit(coord)
                result: ShotResult = "sunk" if ship.is_sunk else "hit"
                self.shots_received[coord] = result
                return result
        self.shots_received[coord] = "miss"
        return "miss"

    # -- Queries --------------------------------------------------------------

    @property
    def all_sunk(self) -> bool:
        return all(ship.is_sunk for ship in self.ships)

    def visible_state(self, reveal_ships: bool = False) -> list[list[str]]:
        """
        Returns 10×10 grid of single-char strings.
        '~' unknown | 'X' hit/sunk | 'O' miss | '#' ship (only when reveal_ships=True)
        """
        grid: list[list[str]] = [["~"] * 10 for _ in range(10)]
        if reveal_ships:
            for ship in self.ships:
                for col, row in ship.cells:
                    grid[row - 1][BOARD_COLS.index(col)] = "#"
        for (col, row), result in self.shots_received.items():
            ci = BOARD_COLS.index(col)
            ri = row - 1
            grid[ri][ci] = "X" if result in ("hit", "sunk") else "O"
        return grid

    def grid_text(self, reveal_ships: bool = False) -> str:
        """Human-readable ASCII grid for LLM prompt injection."""
        header = "    " + "  ".join(BOARD_COLS)
        lines = [header, "   +" + "---" * 10 + "-+"]
        for ri, row_data in enumerate(self.visible_state(reveal_ships)):
            row_num = str(ri + 1).rjust(2)
            lines.append(f"{row_num} | " + "  ".join(row_data) + "  |")
        lines.append("   +" + "---" * 10 + "-+")
        return "\n".join(lines)


# ── Move record ───────────────────────────────────────────────────────────────


@dataclass
class MoveRecord:
    turn: int
    agent_name: str
    coordinate: str
    result: ShotResult
    razonamiento: str = ""
    estrategia_aplicada: str = ""


# ── Almacen Parser ────────────────────────────────────────────────────────────


class AlmacenParser:
    """
    Reads almacen_equipo_X.md and returns validated Ship objects.

    Supported line formats (case-insensitive):

        Simple key: coords
            P1: A1 B1 C1 D1 E1
            Pedido1: A3 B3 C3 D3

        Markdown table row
            | P1 | 5 | A1 B1 C1 D1 E1 |
    """

    _SIMPLE = re.compile(
        r"^(?:P|Pedido_?)(\d+)\s*:\s*"
        r"((?:[A-Ja-j](?:10|[1-9])\s*)+)",
        re.IGNORECASE | re.MULTILINE,
    )
    _TABLE = re.compile(
        r"\|\s*(?:P|Pedido_?)(\d+)\s*\|\s*\d+\s*\|\s*"
        r"((?:[A-Ja-j](?:10|[1-9])\s*)+)\s*\|",
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, filepath: str | Path) -> list[Ship]:
        """Parse warehouse file and return list of Ship objects (fault-tolerant)."""
        ships, _, _ = cls.parse_with_status(filepath)
        return ships

    @classmethod
    def parse_with_status(
        cls, filepath: str | Path, emit_warning: bool = True
    ) -> tuple[list[Ship], bool, str]:
        """
        Parse warehouse file with status metadata.
        Returns: (ships, used_fallback, reason)
        """
        try:
            text = Path(filepath).read_text(encoding="utf-8")
        except Exception as exc:
            reason = f"No se pudo leer archivo {str(filepath)!r}: {exc}"
            if emit_warning:
                warnings.warn(
                    f"[AlmacenParser] {reason}. Usando layout aleatorio legal.",
                    RuntimeWarning,
                    stacklevel=2,
                )
            return cls.generate_random_layout(), True, reason

        ships: list[Ship] = []
        try:
            for pat in (cls._SIMPLE, cls._TABLE):
                for m in pat.finditer(text):
                    order_id = f"P{m.group(1)}"
                    raw_coords = m.group(2).split()
                    cells = [parse_coord(c) for c in raw_coords]
                    ships.append(Ship(order_id=order_id, size=len(cells), cells=cells))
                if ships:
                    break

            if not ships:
                raise ValueError(
                    "No se encontraron pedidos. Usa formato tipo: P1: A1 B1 C1 D1 E1"
                )

            # Validate full board configuration in one place.
            Board(ships)
            return ships, False, "ok"
        except Exception as exc:
            reason = f"Formato inválido en {str(filepath)!r}: {exc}"
            if emit_warning:
                warnings.warn(
                    f"[AlmacenParser] {reason}. Usando layout aleatorio legal.",
                    RuntimeWarning,
                    stacklevel=2,
                )
            return cls.generate_random_layout(), True, reason

    @classmethod
    def generate_random_layout(cls) -> list[Ship]:
        """Generate a legal random layout with required sizes: 5,4,3,3,2."""
        occupied: set[tuple[str, int]] = set()
        ships: list[Ship] = []

        for idx, size in enumerate(REQUIRED_SHIP_SIZES, start=1):
            placed = False
            for _ in range(500):
                horizontal = random.choice([True, False])
                if horizontal:
                    row = random.choice(BOARD_ROWS)
                    start_ci = random.randint(0, len(BOARD_COLS) - size)
                    cells = [(BOARD_COLS[start_ci + off], row) for off in range(size)]
                else:
                    col = random.choice(BOARD_COLS)
                    start_row = random.randint(1, len(BOARD_ROWS) - size + 1)
                    cells = [(col, start_row + off) for off in range(size)]

                if any(c in occupied for c in cells):
                    continue

                ship = Ship(order_id=f"P{idx}", size=size, cells=cells)
                ships.append(ship)
                occupied.update(cells)
                placed = True
                break

            if not placed:
                # Extremely unlikely with a 10x10 board, but keep deterministic safety.
                raise RuntimeError("No se pudo generar layout aleatorio legal.")

        return ships


# ── Game ──────────────────────────────────────────────────────────────────────


class Game:
    """
    Orchestrates one match between two agents.

    Reviewer Agent note:
        The Golden Rule (HIT/SUNK → repeat turn) is NOT enforced here.
        This class is a pure state machine. The caller (tournament.py / main.py)
        must check apply_move() result and call switch_turn() only on 'miss'
        or 'already_shot'.  This keeps turn logic transparent and testable.
    """

    MAX_TURNS = 120  # short hackathon-safe cap to avoid stalled matches

    def __init__(
        self,
        agent_a_name: str,
        board_a: Board,
        agent_b_name: str,
        board_b: Board,
    ) -> None:
        self.names: list[str] = [agent_a_name, agent_b_name]

        # agent → own board (for display)
        self.boards: dict[str, Board] = {
            agent_a_name: board_a,
            agent_b_name: board_b,
        }
        # agent → opponent's board (target for shooting)
        self.agents: dict[str, Board] = {
            agent_a_name: board_b,
            agent_b_name: board_a,
        }

        self._current_idx: int = 0
        self.turn_count: int = 0
        self.move_log: list[MoveRecord] = []
        self.shots_fired: dict[str, int] = {agent_a_name: 0, agent_b_name: 0}

    @property
    def current_agent(self) -> str:
        return self.names[self._current_idx]

    @property
    def opponent(self) -> str:
        return self.names[1 - self._current_idx]

    def apply_move(
        self,
        col: str,
        row: int,
        razonamiento: str = "",
        estrategia: str = "",
    ) -> ShotResult:
        """
        Fire one shot from the current agent onto the opponent's board.
        Records the move and returns ShotResult.
        Caller decides turn switching based on result.
        """
        target_board = self.agents[self.current_agent]
        result = target_board.shoot(col, row)

        self.shots_fired[self.current_agent] += 1
        self.turn_count += 1

        self.move_log.append(
            MoveRecord(
                turn=self.turn_count,
                agent_name=self.current_agent,
                coordinate=format_coord(col, row),
                result=result,
                razonamiento=razonamiento,
                estrategia_aplicada=estrategia,
            )
        )
        return result

    def switch_turn(self) -> None:
        """Switch the active agent to the other player."""
        self._current_idx = 1 - self._current_idx

    def is_over(self) -> tuple[bool, str | None]:
        """
        Returns (finished, winner_name).
        At MAX_TURNS, winner is decided by total impacts (hit+sunk).
        """
        for name, own_board in self.boards.items():
            if own_board.all_sunk:
                winner = self.names[1 - self.names.index(name)]
                return True, winner
        if self.turn_count >= self.MAX_TURNS:
            metrics: dict[str, tuple[int, int, int]] = {}
            for name in self.names:
                target_board = self.agents[name]
                impacts = sum(
                    1 for r in target_board.shots_received.values() if r in ("hit", "sunk")
                )
                sunk_ships = sum(1 for s in target_board.ships if s.is_sunk)
                # tuple sorted descending: impacts, sunk ships, shots fired
                metrics[name] = (impacts, sunk_ships, self.shots_fired[name])

            # Deterministic winner selection even on perfect tie:
            # impacts > sunk ships > total shots fired > registration order.
            winner = sorted(
                self.names,
                key=lambda n: (metrics[n][0], metrics[n][1], metrics[n][2]),
                reverse=True,
            )[0]
            return True, winner
        return False, None
