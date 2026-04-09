"""
Build the Minesweeper knowledge model (km) from the current board and run
the same iterative inference as the course example (zeros, full sets, subset).
"""
from __future__ import annotations

from game import MinesweeperGame, cell_label


def _sort_key(label: str) -> tuple[int, int]:
    parts = label.split("_", 1)
    if len(parts) != 2:
        return (0, 0)
    return int(parts[0]), int(parts[1])


def _sorted_key(cells: list[str]) -> str:
    cells = [c for c in cells if c]
    cells = sorted(cells, key=_sort_key)
    return ",".join(cells)


def build_knowledge_model(game: MinesweeperGame) -> dict[str, int]:
    """
    Each revealed number cell yields one sentence: among unknown (unrevealed,
    unflagged) neighbors, exactly `remaining` mines remain, where
    remaining = displayed_number - flagged_neighbors.
    """
    km: dict[str, int] = {}
    if not game.mines_placed:
        return km

    for r in range(game.rows):
        for c in range(game.cols):
            if (r, c) not in game.revealed or (r, c) in game.mines:
                continue
            shown = game.display_number(r, c)
            if shown is None:
                continue
            unknowns: list[str] = []
            flagged_adj = 0
            for nr, nc in game.neighbors(r, c):
                if (nr, nc) in game.flagged:
                    flagged_adj += 1
                elif (nr, nc) not in game.revealed:
                    unknowns.append(cell_label(nr, nc))
            remaining = shown - flagged_adj
            if not unknowns:
                continue
            if remaining < 0 or remaining > len(unknowns):
                # Wrong flags vs clue — omit sentence (avoids bogus deductions)
                continue
            key = _sorted_key(unknowns)
            km[key] = remaining
    return km


def infer_knowledge(initial_km: dict[str, int]) -> tuple[dict[str, int], list[str], list[str]]:
    """
    Course-style iteration until no change: derive deduced mines, safe cells,
    and simplified km. Returns (final_km, mines, clear).
    """
    km = {k: v for k, v in initial_km.items()}
    mines: list[str] = []
    clear: list[str] = []

    for _ in range(500):
        changes = False
        new_mines: list[str] = []
        new_clear: list[str] = []
        new_km: dict[str, int] = {}

        for key, value in list(km.items()):
            temp = [x for x in key.split(",") if x]
            if not temp:
                continue

            if value == 0:
                for i in temp:
                    new_clear.append(i)
                changes = True
                continue

            if len(temp) == value:
                for i in temp:
                    new_mines.append(i)
                changes = True
                continue

            for m in mines:
                while m in temp:
                    temp.remove(m)
                    value -= 1
                    changes = True
            for c in clear:
                if c in temp:
                    temp.remove(c)
                    changes = True

            if temp:
                nk = _sorted_key(temp)
                new_km[nk] = value

        for key1, value1 in list(km.items()):
            for key2, value2 in list(km.items()):
                if key1 == key2:
                    continue
                s1 = {x for x in key1.split(",") if x}
                s2 = {x for x in key2.split(",") if x}
                if not s1 or not s1.issubset(s2):
                    continue
                diff = s2 - s1
                if not diff:
                    continue
                nk = _sorted_key(list(diff))
                nv = value2 - value1
                new_km[nk] = nv
                changes = True

        for m in new_mines:
            if m not in mines:
                mines.append(m)
                changes = True
        for c in new_clear:
            if c not in clear:
                clear.append(c)
                changes = True

        km = new_km
        if not changes:
            break

    return km, mines, clear


def knowledge_snapshot(
    game: MinesweeperGame,
) -> tuple[dict[str, int], dict[str, int], list[str], list[str]]:
    """Returns (km_from_board, km_after_inference, deduced_mines, deduced_safe)."""
    km0 = build_knowledge_model(game)
    km1, mines, clear = infer_knowledge(km0)
    return km0, km1, mines, clear
