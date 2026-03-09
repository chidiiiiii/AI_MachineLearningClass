"""
tictactoe_minimax_2026.py

prof. lehman
spring 2026

Minimax for Tic Tac Toe with:
- configurable starting board (set at top)
- configurable depth (plies)
- selectable evaluation function:
    1) terminal_only: +1 X win, -1 O win, 0 otherwise (needs full depth to be meaningful)
    2) tanimoto_100_10_1: heuristic line counting using 100/10/1

Enhancement:
- Traces evaluation numbers at each level of the search tree for EVERY root branch.
- Still prints a root-branch summary table and the chosen move.
"""

from __future__ import annotations
from typing import List, Optional, Tuple

# ----------------------------
# Configuration (edit these)
# ----------------------------

CURRENT_PLAYER = "O"  # "X" (MAX) or "O" (MIN)

# *** note(1): pick one of the following evaluation functions ***
#EVAL_MODE = "terminal_only"
EVAL_MODE = "tanimoto_100_10_1"

# *** note(2): set search depth to 4 for terminal_only class example ***
SEARCH_DEPTH = 2 # plies (ie. depth to search)

# *** note(3): set your board here ***
START_BOARD = [
    "O", " ", "X",
    " ", "X", "O",
    " ", " ", "X"
]


SHOW_BOARD_PER_BRANCH = False  # True prints the board after each root move (optional)

# Option A tracing controls
TRACE_ALL_ROOT_BRANCHES = True
TRACE_SHOW_ROOT_BOARD = True   # show the board position after the root move (nice for class)

# ----------------------------
# Game definitions
# ----------------------------

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
    (0, 4, 8), (2, 4, 6)              # diagonals
]

def format_board(b: List[str]) -> str:
    rows = []
    for r in range(0, 9, 3):
        rows.append(" | ".join(b[r:r+3]))
    return "\n---------\n".join(rows)

def winner(board: List[str]) -> Optional[str]:
    for a, b, c in WIN_LINES:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    return None

def board_full(board: List[str]) -> bool:
    return all(cell != " " for cell in board)

def legal_moves(board: List[str]) -> List[int]:
    return [i for i, cell in enumerate(board) if cell == " "]

def next_player(p: str) -> str:
    return "O" if p == "X" else "X"

def idx_to_rc(i: int) -> Tuple[int, int]:
    return (i // 3, i % 3)

# ----------------------------
# Evaluation functions
# ----------------------------

def eval_terminal_only(board: List[str]) -> int:
    w = winner(board)
    if w == "X":
        return 1
    if w == "O":
        return -1
    return 0  # tie OR non-terminal

def line_counts(board: List[str], player: str) -> Tuple[int, int, int]:
    opp = "O" if player == "X" else "X"
    c3 = c2 = c1 = 0
    for a, b, c in WIN_LINES:
        line = [board[a], board[b], board[c]]
        if opp in line:
            continue
        marks = line.count(player)
        empties = line.count(" ")
        if marks == 3:
            c3 += 1
        elif marks == 2 and empties == 1:
            c2 += 1
        elif marks == 1 and empties == 2:
            c1 += 1
    return c3, c2, c1

def eval_tanimoto_100_10_1(board: List[str]) -> int:
    x3, x2, x1 = line_counts(board, "X")
    o3, o2, o1 = line_counts(board, "O")
    return (100*x3 + 10*x2 + x1) - (100*o3 + 10*o2 + o1)

def evaluate(board: List[str]) -> int:
    if EVAL_MODE == "terminal_only":
        return eval_terminal_only(board)
    if EVAL_MODE == "tanimoto_100_10_1":
        return eval_tanimoto_100_10_1(board)
    raise ValueError(f"Unknown EVAL_MODE: {EVAL_MODE}")

# ----------------------------
# Minimax (depth-limited) with tracing
# ----------------------------

def minimax(board: List[str], player: str, depth: int, *, trace: bool=False, ply: int=0) -> int:
    """
    If trace=True, prints:
      - leaf evals (win/full/depth==0)
      - internal node child-values list and chosen best
    Indentation is based on ply (tree depth from the trace root).
    """
    indent = "  " * ply

    w = winner(board)
    if w is not None or board_full(board) or depth == 0:
        val = evaluate(board)
        if trace:
            state = "WIN" if w is not None else ("FULL" if board_full(board) else "DEPTH0")
            print(f"{indent}{player} depth={depth} [{state}] eval= {val}")
        return val

    moves = legal_moves(board)

    if trace:
        role = "MAX" if player == "X" else "MIN"
        print(f"{indent}{player} depth={depth} ({role}) exploring moves {moves}")

    child_vals: List[Tuple[int, int]] = []  # (move, value)

    if player == "X":  # MAX
        best_val = -10**9
        for mv in moves:
            board[mv] = "X"
            val = minimax(board, "O", depth - 1, trace=trace, ply=ply + 1)
            board[mv] = " "
            child_vals.append((mv, val))
            if val > best_val:
                best_val = val

        if trace:
            vals_only = [v for _, v in child_vals]
            best_moves = [mv for mv, v in child_vals if v == best_val]
            print(f"{indent}{player} chooses {best_val} from {vals_only} via moves {best_moves}")

        return best_val

    else:  # MIN (player == "O")
        best_val = 10**9
        for mv in moves:
            board[mv] = "O"
            val = minimax(board, "X", depth - 1, trace=trace, ply=ply + 1)
            board[mv] = " "
            child_vals.append((mv, val))
            if val < best_val:
                best_val = val

        if trace:
            vals_only = [v for _, v in child_vals]
            best_moves = [mv for mv, v in child_vals if v == best_val]
            print(f"{indent}{player} chooses {best_val} from {vals_only} via moves {best_moves}")

        return best_val

# ----------------------------
# Root branch reporting helpers
# ----------------------------

def branch_values(board: List[str], player: str, depth: int) -> List[Tuple[int, int]]:
    """
    Returns a list of (move_index, predicted_value) for each legal root move.
    predicted_value is the minimax value AFTER making that move.
    """
    results: List[Tuple[int, int]] = []
    for mv in legal_moves(board):
        board[mv] = player
        val = minimax(board, next_player(player), depth - 1, trace=False, ply=0)
        board[mv] = " "
        results.append((mv, val))
    return results

def choose_best_from_branches(player: str, branches: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Choose best branch for player: MAX chooses highest value, MIN chooses lowest value.
    Tie-break: smallest move index (deterministic).
    """
    if player == "X":
        best_mv, best_val = max(branches, key=lambda t: (t[1], -t[0]))
    else:
        best_mv, best_val = min(branches, key=lambda t: (t[1], t[0]))
    return best_mv, best_val

# ----------------------------
# Main
# ----------------------------

def main() -> None:
    # Print index guide
    print("  0 | 1 | 2")
    print(" ---+---+---")
    print("  3 | 4 | 5")
    print(" ---+---+---")
    print("  6 | 7 | 8")

    board = START_BOARD[:]

    if EVAL_MODE == "terminal_only":
        empties = board.count(" ")
        if SEARCH_DEPTH < empties:
            print("\nWARNING: EVAL_MODE='terminal_only' but SEARCH_DEPTH is less than")
            print(f"the number of empty squares ({empties}). Non-terminal leaves score 0,")
            print("so results may be misleading unless you search to the end.\n")

    print("\n=== Tic Tac Toe Minimax (trace all root branches) ===\n")
    print("Evaluation:", EVAL_MODE)
    print("Depth (plies):", SEARCH_DEPTH)
    print("Player to move:", CURRENT_PLAYER)
    print("\nStarting board:\n")
    print(format_board(board))

    w = winner(board)
    if w is not None or board_full(board):
        print("\nGame is already over.")
        print("Board value:", evaluate(board))
        return

    # ---- Option A: trace every root branch ----
    traced_branches: List[Tuple[int, int]] = []
    for mv in legal_moves(board):
        board[mv] = CURRENT_PLAYER

        print("\n" + "=" * 60)
        print(f"Root move {mv} by {CURRENT_PLAYER} (row,col={idx_to_rc(mv)})")
        print("=" * 60)

        if TRACE_SHOW_ROOT_BOARD:
            print(format_board(board))
            print()

        val = minimax(
            board,
            next_player(CURRENT_PLAYER),
            SEARCH_DEPTH - 1,
            trace=TRACE_ALL_ROOT_BRANCHES,
            ply=1
        )

        board[mv] = " "
        traced_branches.append((mv, val))

        if SHOW_BOARD_PER_BRANCH:
            board[mv] = CURRENT_PLAYER
            print("\nBoard after this root move:\n")
            print(format_board(board))
            board[mv] = " "

    # Choose best move from traced branches
    best_mv, best_val = choose_best_from_branches(CURRENT_PLAYER, traced_branches)

    # Sort for display: best-first for X; lowest-first for O
    branches_sorted = sorted(
        traced_branches,
        key=lambda t: t[1],
        reverse=(CURRENT_PLAYER == "X")
    )

    print("\n\n=== Root branch summary (predicted minimax value) ===\n")
    header = f"{'Move':>4}  {'(r,c)':>7}  {'Predicted value':>16}  {'Chosen':>7}"
    print(header)
    print("-" * len(header))

    for mv, val in branches_sorted:
        r, c = idx_to_rc(mv)
        chosen = "<<<" if mv == best_mv else ""
        print(f"{mv:>4}  ({r},{c})  {val:>16}  {chosen:>7}")

    print("\nBest move:", best_mv, " (row,col)=", idx_to_rc(best_mv))
    print("Best predicted value:", best_val)

    board[best_mv] = CURRENT_PLAYER
    print("\nBoard after best move:\n")
    print(format_board(board))

if __name__ == "__main__":
    main()