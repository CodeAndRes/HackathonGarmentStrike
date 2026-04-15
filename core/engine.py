"""
core/engine.py
──────────────
Pure game logic for Garment Strike (dynamic Supply Chain Battleship).

Board   : 6×6 up to 10×10 (configurable via board_size parameter)
Pedidos : configurable via ship_sizes parameter (default: [5, 4, 3, 3, 2])
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

# Las constantes globales ahora son funciones generadoras
def get_board_cols(size: int) -> list[str]:
    return list("ABCDEFGHIJ"[:size])

def get_board_rows(size: int) -> list[int]:
    return list(range(1, size + 1))

# Canonical ship configuration
REQUIRED_SHIP_SIZES: list[int] = sorted([5, 4, 3, 3, 2], reverse=True)

ShotResult = Literal["hit", "miss", "sunk", "already_shot"]

LOGISTICS_MAP = {
    "hit": "Prenda encajada",
    "miss": "Prenda perdida",
    "sunk": "Pedido ENCAJADO",
    "already_shot": "Celda duplicada"
}

# Regex genérica para validar coordenadas dinámicas
_COORD_BASE_RE = re.compile(r"^([A-Ja-j])(\d+)$")

def validate_game_config(board_size: int, ship_sizes: list[int]) -> None:
    """Validate game configuration before starting a match.
    
    Raises ValueError with a descriptive message if the configuration is invalid.
    This is a pre-flight check intended to be called from main.py / CLI before
    constructing Board objects.
    """
    if not 6 <= board_size <= 10:
        raise ValueError(f"board_size debe ser entre 6 y 10, recibido: {board_size}")
    if any(s > board_size for s in ship_sizes):
        raise ValueError(f"Ningún barco puede ser mayor que el tablero ({board_size})")
    if any(s < 2 for s in ship_sizes):
        raise ValueError(f"Tamaño mínimo de barco es 2")
    total_cells = sum(ship_sizes)
    max_cells = (board_size * board_size) // 2
    if total_cells > max_cells:
        raise ValueError(f"Total de celdas ({total_cells}) excede el 50% del tablero ({max_cells})")


# ── Coordinate helpers ────────────────────────────────────────────────────────


def parse_coord(raw: str, size: int = 10) -> tuple[str, int]:
    """Parse 'B5' → ('B', 5) validating against board size."""
    m = _COORD_BASE_RE.match(raw.strip())
    if not m:
        raise ValueError(f"Formato de coordenada inválido: {raw!r}")
    
    col = m.group(1).upper()
    row = int(m.group(2))
    
    valid_cols = get_board_cols(size)
    valid_rows = get_board_rows(size)
    
    if col not in valid_cols or row not in valid_rows:
        raise ValueError(
            f"Coordenada {raw!r} fuera del tablero {size}x{size} "
            f"(A-{valid_cols[-1]}{valid_rows[0]}-{valid_rows[-1]})."
        )
    return col, row


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
            alphabet = "ABCDEFGHIJ"  # full alphabet; only used for index math
            col_idxs = sorted(alphabet.index(c) for c in cols)
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
    """
    Ocean grid holding ships and recording incoming shots.
    Can be 6x6 up to 10x10.
    """

    def __init__(self, size: int = 10, ships: list[Ship] | None = None, ship_sizes: list[int] | None = None) -> None:
        self.size = size
        self.ship_sizes = sorted(ship_sizes if ship_sizes is not None else REQUIRED_SHIP_SIZES, reverse=True)
        self.cols = get_board_cols(size)
        self.rows = get_board_rows(size)
        self.ships = ships or []
        # Maps coord → result of the shot that landed there
        self.shots_received: dict[tuple[str, int], ShotResult] = {}
        
        # Validaciones de la configuración de barcos
        if self.ship_sizes:
            if max(self.ship_sizes) > self.size:
                raise ValueError(f"Max ship size {max(self.ship_sizes)} exceeds board size {self.size}.")
            if min(self.ship_sizes) < 2:
                raise ValueError(f"Minimum ship size must be >= 2.")
            if sum(self.ship_sizes) > (self.size * self.size) / 2:
                raise ValueError(f"Total ship cells {sum(self.ship_sizes)} exceed 50% of the board area {(self.size * self.size)}.")

        if ships:
            self._validate_placement()

    # -- Validation -----------------------------------------------------------

    def _validate_placement(self) -> None:
        seen: set[tuple[str, int]] = set()
        for ship in self.ships:
            for col, row in ship.cells:
                if col not in self.cols or row not in self.rows:
                    raise ValueError(
                        f"Celda {format_coord(col, row)} fuera del tablero (A1-{self.cols[-1]}{self.size})."
                    )
                if (col, row) in seen:
                    raise ValueError(
                        f"Solapamiento detectado en {format_coord(col, row)}."
                    )
                seen.add((col, row))

        actual_sizes = sorted([s.size for s in self.ships], reverse=True)
        if actual_sizes != self.ship_sizes:
            raise ValueError(
                f"Configuración de pedidos incorrecta. "
                f"Esperado {self.ship_sizes}, recibido {actual_sizes}."
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
        Returns grid of single-char strings for current size.
        '~' unknown | 'X' hit/sunk | 'O' miss | '#' ship (only when reveal_ships=True)
        """
        grid: list[list[str]] = [["~"] * self.size for _ in range(self.size)]
        if reveal_ships:
            for ship in self.ships:
                for col, row in ship.cells:
                    try:
                        ci = self.cols.index(col)
                        grid[row - 1][ci] = "#"
                    except ValueError:
                        # This should have been caught by validation, but let's be safe
                        continue
        for (col, row), result in self.shots_received.items():
            try:
                ci = self.cols.index(col)
                ri = row - 1
                grid[ri][ci] = "X" if result in ("hit", "sunk") else "O"
            except ValueError:
                continue
        return grid

    def grid_text(self, reveal_ships: bool = False) -> str:
        """Human-readable ASCII grid for LLM prompt injection."""
        header = "    " + "  ".join(self.cols)
        lines = [header, "   +" + "---" * self.size + "-+"]
        for ri, row_data in enumerate(self.visible_state(reveal_ships)):
            row_num = str(ri + 1).rjust(2)
            lines.append(f"{row_num} | " + "  ".join(row_data) + "  |")
        lines.append("   +" + "---" * self.size + "-+")
        return "\n".join(lines)

    def grid_text_compact(self, reveal_ships: bool = False) -> str:
        """Token-efficient grid: plain rows separated by spaces, no ASCII borders."""
        header = " ".join(self.cols)
        rows = [header]
        for ri, row_data in enumerate(self.visible_state(reveal_ships)):
            rows.append(f"{ri + 1:>2} " + " ".join(row_data))
        return "\n".join(rows)
    def grid_text_minimal(self) -> str:
        """Hyper-token-efficient board text: returns only known coordinates."""
        agua = []
        impacto = []
        for (col, row), result in self.shots_received.items():
            c = format_coord(col, row)
            if result in ("hit", "sunk"):
                impacto.append(c)
            else:
                agua.append(c)
        
        txt = ""
        if impacto:
            txt += f"IMPACTOS PREVIOS (X): {', '.join(impacto)}\n"
        if agua:
            txt += f"AGUA/MISS PREVIO (O): {', '.join(agua)}\n"
        
        if not txt:
            return "TABLERO RIVAL: (Aún no has disparado)"
        
        return f"ESTADO ACTUAL DEL TABLERO RIVAL:\n{txt}"


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
        r"(?:P|Pedido_?)(\d+)\s*:\s*((?:[A-Ja-j]\d+\s*)+)", re.IGNORECASE
    )
    _TABLE = re.compile(
        r"\|\s*(?:P|Pedido_?)(\d+)\s*\|\s*\d+\s*\|\s*"
        r"((?:[A-Ja-j]\d+\s*)+)\s*\|",
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, filepath: str | Path, size: int = 10, ship_sizes: list[int] | None = None) -> list[Ship]:
        """Parse warehouse file and return list of Ship objects (fault-tolerant)."""
        ships, _, _ = cls.parse_with_status(filepath, size=size, ship_sizes=ship_sizes)
        return ships

    @classmethod
    def parse_with_status(
        cls, filepath: str | Path, size: int = 10, emit_warning: bool = True, ship_sizes: list[int] | None = None
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
            return cls.generate_random_layout(size=size, ship_sizes=ship_sizes), True, reason

        ships: list[Ship] = []
        try:
            for pat in (cls._SIMPLE, cls._TABLE):
                for m in pat.finditer(text):
                    order_id = f"P{m.group(1)}"
                    raw_coords = m.group(2).split()
                    cells = [parse_coord(c, size=size) for c in raw_coords]
                    ships.append(Ship(order_id=order_id, size=len(cells), cells=cells))
                if ships:
                    break

            if not ships:
                raise ValueError(
                    "No se encontraron pedidos. Usa formato tipo: P1: A1 B1 C1 D1 E1"
                )

            # Validate full board configuration in one place.
            Board(size=size, ships=ships, ship_sizes=ship_sizes)
            return ships, False, "ok"
        except Exception as exc:
            reason = f"Formato inválido en {str(filepath)!r}: {exc}"
            if emit_warning:
                warnings.warn(
                    f"[AlmacenParser] {reason}. Usando layout aleatorio legal.",
                    RuntimeWarning,
                    stacklevel=2,
                )
            return cls.generate_random_layout(size=size, ship_sizes=ship_sizes), True, reason

    @classmethod
    def generate_random_layout(cls, size: int = 10, ship_sizes: list[int] | None = None) -> list[Ship]:
        """Generate a legal random layout with required sizes (if they fit)."""
        cols = get_board_cols(size)
        rows = get_board_rows(size)
        occupied: set[tuple[str, int]] = set()
        ships: list[Ship] = []

        # Adjust ship sizes if board is too small
        target_sizes = sorted(ship_sizes if ship_sizes is not None else REQUIRED_SHIP_SIZES, reverse=True)
        effective_sizes = [s for s in target_sizes if s <= size]
        if not effective_sizes:
             effective_sizes = [2] # absolute fallback

        for idx, s_size in enumerate(effective_sizes, start=1):
            placed = False
            for _ in range(500):
                horizontal = random.choice([True, False])
                if horizontal:
                    row = random.choice(rows)
                    start_ci = random.randint(0, len(cols) - s_size)
                    cells = [(cols[start_ci + off], row) for off in range(s_size)]
                else:
                    col = random.choice(cols)
                    start_row = random.randint(1, len(rows) - s_size + 1)
                    cells = [(col, start_row + off) for off in range(s_size)]

                if any(c in occupied for c in cells):
                    continue

                ship = Ship(order_id=f"P{idx}", size=s_size, cells=cells)
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

    Turn limit and tiebreaker logic are handled by the caller (tournament.py),
    NOT by this class. This class only detects the natural end condition
    (all ships sunk).
    """

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
        Only checks the natural end condition: all of one player's ships sunk.
        Turn limits and tiebreakers are the caller's responsibility.
        """
        for name, own_board in self.boards.items():
            if own_board.all_sunk:
                winner = self.names[1 - self.names.index(name)]
                return True, winner
        return False, None
