"""Minesweeper board state: mines, reveals, flags, first-click-safe placement."""
import random


def cell_label(row: int, col: int) -> str:
    """Single-cell id without commas (km keys join cells with commas)."""
    return f"{row}_{col}"


def parse_label(s: str) -> tuple[int, int]:
    a, b = s.split("_", 1)
    return int(a), int(b)


def human_cell_name(row: int, col: int) -> str:
    """Human-readable coordinates: Row 1 = top, Col 1 = left (1-based)."""
    return f"Row {row + 1}, Col {col + 1}"


def human_cell_name_from_label(label: str) -> str:
    """Turn internal id like 3_0 into 'Row 4, Col 1' (indices are 0-based in code)."""
    r, c = parse_label(label)
    return human_cell_name(r, c)


class MinesweeperGame:
    def __init__(self, rows: int = 9, cols: int = 9, num_mines: int = 10):
        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines
        self.mines: set[tuple[int, int]] = set()
        self.revealed: set[tuple[int, int]] = set()
        self.flagged: set[tuple[int, int]] = set()
        self.mines_placed = False
        self.game_over = False
        self.won = False

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def neighbors(self, r: int, c: int):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if self.in_bounds(nr, nc):
                    yield nr, nc

    def _neighbor_mine_count(self, r: int, c: int) -> int:
        return sum(1 for nr, nc in self.neighbors(r, c) if (nr, nc) in self.mines)

    def place_mines(self, safe_r: int, safe_c: int) -> None:
        safe = {(safe_r, safe_c)}
        for nr, nc in self.neighbors(safe_r, safe_c):
            safe.add((nr, nc))
        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in safe
        ]
        n = min(self.num_mines, len(candidates))
        self.mines = set(random.sample(candidates, n)) if n else set()
        self.mines_placed = True

    def _flood_reveal(self, r: int, c: int) -> None:
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            for nr, nc in self.neighbors(cr, cc):
                if (nr, nc) in self.mines or (nr, nc) in self.flagged:
                    continue
                if (nr, nc) in self.revealed:
                    continue
                self.revealed.add((nr, nc))
                if self._neighbor_mine_count(nr, nc) == 0:
                    stack.append((nr, nc))

    def reveal(self, r: int, c: int) -> str:
        """
        Returns status: 'ok' | 'mine' | 'win' | 'flagged' | 'already' | 'over'
        """
        if self.game_over:
            return "over"
        if (r, c) in self.flagged:
            return "flagged"
        if (r, c) in self.revealed:
            return "already"
        if not self.mines_placed:
            self.place_mines(r, c)
        if (r, c) in self.mines:
            self.revealed.add((r, c))
            self.game_over = True
            self.won = False
            return "mine"
        self.revealed.add((r, c))
        if self._neighbor_mine_count(r, c) == 0:
            self._flood_reveal(r, c)
        if self._check_win():
            self.game_over = True
            self.won = True
            return "win"
        return "ok"

    def _check_win(self) -> bool:
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) not in self.mines and (r, c) not in self.revealed:
                    return False
        return True

    def toggle_flag(self, r: int, c: int) -> None:
        if self.game_over:
            return
        if (r, c) in self.revealed:
            return
        if (r, c) in self.flagged:
            self.flagged.discard((r, c))
        else:
            self.flagged.add((r, c))

    def display_number(self, r: int, c: int) -> int | None:
        """Adjacent mine count for a revealed non-mine cell."""
        if (r, c) not in self.revealed or (r, c) in self.mines:
            return None
        return self._neighbor_mine_count(r, c)
