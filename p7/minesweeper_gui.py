# Minesweeper_gui.py
# Isabella Herrera Pilonieta
# April 8, 2026
# CS 262 AI and Machine Learning
# Homework 7. The idea od this code is to recreate the game Minesweeper and add a live knowledge panel to the game.
# The code is based on the course example using AI to solve the game, and to show the knowledge panel live as the game is played.

"""

Minesweeper + live knowledge panel (tkinter).

Run from this folder: python minesweeper_gui.py

"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from game import MinesweeperGame, human_cell_name, human_cell_name_from_label
from knowledge_engine import knowledge_snapshot

# --- Theme: white, black, forest green ---
WHITE = "#ffffff"
BLACK = "#000000"
FOREST = "#1B5E20"
FOREST_MID = "#2E7D32"
FOREST_LIGHT = "#C8E6C9"
FOREST_HEADER = "#1B5E20"
TEXT_MUTED = "#212121"

BG_WINDOW = WHITE
BG_PANEL = WHITE
BG_INSTRUCTIONS = WHITE
ACCENT = FOREST
ACCENT_LIGHT = FOREST_MID
BOARD_MAT = FOREST_LIGHT
BOARD_RIM = FOREST_MID
HEADER_BG = FOREST_HEADER
HEADER_FG = WHITE
TILE_HIDDEN = FOREST_LIGHT
TILE_HIDDEN_BORDER = FOREST_MID
TILE_REVEALED = WHITE
TILE_NUMBER_BG = "#E8F5E9"
MINE_WRONG = "#FFCDD2"
MINE_ICON = BLACK
MINE_REVEAL = "#C62828"
FLAG_FG = FOREST
FLAG_BG = "#FFF9C4"

NUM_COLORS = {
    1: "#0D47A1",
    2: FOREST_MID,
    3: "#B71C1C",
    4: "#311B92",
    5: "#880E4F",
    6: "#00695C",
    7: BLACK,
    8: "#424242",
}

PRESETS = {
    "Beginner": (9, 9, 10),
    "Intermediate": (16, 16, 40),
    "Expert": (16, 30, 99),
}

HEADER_FONT = ("Segoe UI", 9, "bold")
INSTR_FONT = ("Segoe UI", 9)
TITLE_FONT = ("Segoe UI", 16, "bold")
SUBTITLE_FONT = ("Segoe UI", 10)


class MinesweeperApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Minesweeper · Knowledge Lab")
        self.root.configure(bg=BG_WINDOW)
        self.rows, self.cols, self.num_mines = PRESETS["Beginner"]
        self.game = MinesweeperGame(self.rows, self.cols, self.num_mines)
        self.buttons: list[list[tk.Button]] = []
        self.flag_mode = tk.BooleanVar(value=False)
        self.mines_left_var = tk.StringVar(value="")
        self.instructions_text: scrolledtext.ScrolledText | None = None

        self._apply_styles()
        self._build_menu()
        self._build_layout()
        self._new_game()

    def _apply_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG_WINDOW)
        style.configure("Card.TFrame", background=BG_PANEL)
        style.configure(
            "Accent.TButton",
            background=FOREST,
            foreground=WHITE,
            borderwidth=0,
            focuscolor=FOREST_LIGHT,
            font=("Segoe UI", 9, "bold"),
            padding=(12, 6),
        )
        style.map(
            "Accent.TButton",
            background=[("active", FOREST_MID), ("pressed", "#0D3D12")],
        )
        style.configure(
            "Ghost.TButton",
            background=WHITE,
            foreground=BLACK,
            borderwidth=1,
            font=("Segoe UI", 9),
            padding=(8, 4),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", FOREST_LIGHT)],
        )
        style.configure(
            "TCheckbutton",
            background=BG_WINDOW,
            foreground=BLACK,
            font=("Segoe UI", 9),
        )
        style.configure(
            "TLabelframe",
            background=BG_PANEL,
            foreground=BLACK,
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "TLabelframe.Label",
            background=BG_PANEL,
            foreground=FOREST,
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "Mine.TLabel",
            background=BG_WINDOW,
            foreground=TEXT_MUTED,
            font=("Segoe UI", 9),
        )

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New game (current size)", command=self._new_game)
        game_menu.add_separator()
        for name in PRESETS:
            game_menu.add_command(
                label=f"New — {name}",
                command=lambda n=name: self._new_game_preset(n),
            )

    def _refresh_instructions_panel(self) -> None:
        """One scrollable text: controls + board info + all static help."""
        if self.instructions_text is None:
            return
        txt = self.instructions_text
        txt.configure(state=tk.NORMAL)
        txt.delete("1.0", tk.END)

        txt.insert(tk.END, "CONTROLS AND CURRENT BOARD\n", "dyn_title")
        txt.insert(
            tk.END,
            "• Left-click: reveal (or place/remove a flag if “Flag mode” is on).\n"
            "• Right-click: toggle flag on a hidden cell.\n"
            "• Numbers on a revealed cell = how many mines are in the 8 neighbors "
            "(the display does not subtract your flags from that number).\n\n",
            "body",
        )
        txt.insert(
            tk.END,
            f"Current preset: {self.rows}×{self.cols} board, {self.num_mines} mines. "
            "Labels on the grid: Row 1 / Col 1 = top-left (1-based). "
            f"Internal id example: 3_0 = {human_cell_name(3, 0)} (0-based row_column).\n\n",
            "body",
        )
        txt.insert(tk.END, "—" * 42 + "\n\n", "sep")

        txt.insert(tk.END, "HOW TO READ COORDINATES\n", "title")
        txt.insert(
            tk.END,
            "• Grid labels on the board: Row 1, Col 1 is the top-left cell (1-based).\n"
            "• Internal cell ids use the form R_C with 0-based indices: "
            "R counts rows from the top starting at 0; C counts columns from the left starting at 0.\n"
            f"  Example: 3_0 is the same square as {human_cell_name(3, 0)} on the labeled grid.\n\n",
            "body",
        )

        txt.insert(tk.END, "WHAT THE NUMBERS IN THE KNOWLEDGE MODEL MEAN\n", "title")
        txt.insert(
            tk.END,
            "• Each sentence comes from a revealed numbered clue on the board.\n"
            "• The listed cells are still hidden neighbors of that clue (not revealed, not flagged).\n"
            "• The number after '=' is how many mines remain among only those listed cells.\n"
            "  It equals: (digit on that clue) minus (flags on neighbors of that clue).\n\n",
            "body",
        )

        txt.insert(tk.END, "COMPACT (R,C) FORMAT IN THE KNOWLEDGE PANEL\n", "title")
        txt.insert(
            tk.END,
            "• In “Knowledge from the board”, keys look like '2_0'=1: the part before '=' is one or "
            "more cell ids joined by commas when a clue touches several unknowns.\n"
            "• In each cell id R_C: the number before '_' is the row index R; the number after '_' is "
            "the column index C (both 0-based, top-left is 0_0).\n\n",
            "body",
        )

        txt.insert(tk.END, "NOTES\n", "title")
        txt.insert(
            tk.END,
            "• Flags are treated as known mines when building sentences.\n"
            "• Deduced safe cells and deduced mines follow the same inference rules as the class example.\n",
            "body",
        )

        txt.configure(state=tk.DISABLED)

    def _build_static_instructions(self, parent: ttk.Frame) -> None:
        outer = ttk.LabelFrame(
            parent,
            text="How to play & read the knowledge panel — scroll for all sections",
            padding=8,
        )
        outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))

        txt = scrolledtext.ScrolledText(
            outer,
            height=16,
            wrap=tk.WORD,
            font=INSTR_FONT,
            relief=tk.FLAT,
            padx=12,
            pady=10,
            bg=BG_INSTRUCTIONS,
            fg=BLACK,
            highlightthickness=1,
            highlightbackground=FOREST_LIGHT,
            highlightcolor=FOREST_MID,
        )
        txt.tag_configure(
            "dyn_title",
            font=("Segoe UI", 9, "bold"),
            foreground=FOREST,
        )
        txt.tag_configure(
            "title",
            font=("Segoe UI", 9, "bold"),
            underline=True,
            foreground=FOREST,
            spacing1=6,
            spacing3=4,
        )
        txt.tag_configure("body", lmargin1=12, lmargin2=12, foreground=BLACK)
        txt.tag_configure("sep", foreground=FOREST_MID)

        self.instructions_text = txt
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Wheel scroll when the pointer is over the instructions (works while read-only)
        def _wheel(e: tk.Event) -> str:
            txt.yview_scroll(int(-1 * (e.delta / 120)), "units")
            return "break"

        txt.bind("<MouseWheel>", _wheel)
        outer.bind("<MouseWheel>", _wheel)

    def _build_layout(self) -> None:
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        left = ttk.Frame(main, style="TFrame")

        banner = tk.Frame(left, bg=FOREST, padx=16, pady=12)
        banner.pack(fill=tk.X, padx=8, pady=(4, 0))
        tk.Label(
            banner,
            text="Minesweeper",
            font=TITLE_FONT,
            fg=WHITE,
            bg=FOREST,
        ).pack(anchor=tk.W)
        tk.Label(
            banner,
            text="Play the grid · watch the knowledge base update live",
            font=SUBTITLE_FONT,
            fg=FOREST_LIGHT,
            bg=FOREST,
        ).pack(anchor=tk.W, pady=(2, 0))

        toolbar = ttk.Frame(left, style="TFrame")
        toolbar.pack(fill=tk.X, padx=8, pady=(12, 8))

        ttk.Button(toolbar, text="↻  Restart", style="Accent.TButton", command=self._new_game).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Checkbutton(
            toolbar,
            text="Flag mode",
            variable=self.flag_mode,
        ).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(toolbar, textvariable=self.mines_left_var, style="Mine.TLabel").pack(
            side=tk.LEFT, padx=(0, 12)
        )

        diff = ttk.LabelFrame(toolbar, text="Difficulty", padding=(6, 4))
        diff.pack(side=tk.LEFT, padx=(8, 0))
        for name in PRESETS:
            ttk.Button(
                diff,
                text=name,
                style="Ghost.TButton",
                width=10,
                command=lambda n=name: self._new_game_preset(n),
            ).pack(side=tk.LEFT, padx=2)

        board_wrap = tk.Frame(left, bg=BOARD_RIM, padx=3, pady=3)
        board_wrap.pack(padx=8, pady=8)
        inner = tk.Frame(board_wrap, bg=BOARD_MAT, padx=6, pady=6)
        inner.pack()
        self.board_frame = tk.Frame(inner, bg=BOARD_MAT)
        self.board_frame.pack()

        self._build_static_instructions(left)

        main.add(left, weight=1)

        right = ttk.Frame(main, padding=8, style="Card.TFrame")
        kb_header = tk.Frame(right, bg=BG_PANEL)
        kb_header.pack(fill=tk.X, pady=(0, 6))
        tk.Label(
            kb_header,
            text="Knowledge base",
            font=("Segoe UI", 12, "bold"),
            fg=FOREST,
            bg=BG_PANEL,
        ).pack(anchor=tk.W)
        tk.Label(
            kb_header,
            text="Live logical state from your moves",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_PANEL,
        ).pack(anchor=tk.W)

        self.knowledge_text = scrolledtext.ScrolledText(
            right,
            width=58,
            height=36,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg=WHITE,
            fg=BLACK,
            insertbackground=FOREST,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=FOREST_LIGHT,
            highlightcolor=FOREST_MID,
            padx=8,
            pady=8,
        )
        self.knowledge_text.tag_configure(
            "k_sec",
            font=("Consolas", 9, "bold"),
            foreground=FOREST,
        )
        self.knowledge_text.tag_configure(
            "k_lbl",
            font=("Consolas", 9, "bold"),
            foreground=FOREST_MID,
        )
        self.knowledge_text.tag_configure("k_plain", font=("Consolas", 9), foreground=BLACK)
        self.knowledge_text.pack(fill=tk.BOTH, expand=True)
        main.add(right, weight=1)

    def _new_game_preset(self, name: str) -> None:
        self.rows, self.cols, self.num_mines = PRESETS[name]
        self._new_game()

    def _update_mines_counter(self) -> None:
        remaining = self.num_mines - len(self.game.flagged)
        self.mines_left_var.set(f"Mines left: {remaining}")

    def _new_game(self) -> None:
        self._refresh_instructions_panel()
        for w in self.board_frame.winfo_children():
            w.destroy()
        self.buttons = []
        self.game = MinesweeperGame(self.rows, self.cols, self.num_mines)

        corner = tk.Label(self.board_frame, text="", width=2, bg=BOARD_MAT)
        corner.grid(row=0, column=0)
        for c in range(self.cols):
            tk.Label(
                self.board_frame,
                text=str(c + 1),
                font=HEADER_FONT,
                fg=HEADER_FG,
                bg=HEADER_BG,
                padx=4,
                pady=2,
            ).grid(row=0, column=c + 1, padx=1, pady=1)
        for r in range(self.rows):
            tk.Label(
                self.board_frame,
                text=str(r + 1),
                font=HEADER_FONT,
                fg=HEADER_FG,
                bg=HEADER_BG,
                padx=4,
                pady=2,
            ).grid(row=r + 1, column=0, padx=1, pady=1)

            row_widgets: list[tk.Button] = []
            for c in range(self.cols):
                btn = tk.Button(
                    self.board_frame,
                    width=3,
                    height=1,
                    relief=tk.RAISED,
                    font=("Segoe UI", 10, "bold"),
                    borderwidth=2,
                    cursor="hand2",
                    activebackground=TILE_HIDDEN,
                )
                btn.grid(row=r + 1, column=c + 1, padx=1, pady=1)

                def make_handlers(rr: int, cc: int):
                    def on_left(_e=None):
                        if self.flag_mode.get():
                            self._on_flag(rr, cc)
                        else:
                            self._on_reveal(rr, cc)

                    def on_right(_e=None):
                        self._on_flag(rr, cc)

                    return on_left, on_right

                lh, rh = make_handlers(r, c)
                btn.bind("<Button-1>", lh)
                btn.bind("<Button-3>", rh)
                row_widgets.append(btn)
            self.buttons.append(row_widgets)

        self._update_mines_counter()
        self._refresh_board()
        self._refresh_knowledge()

    def _on_reveal(self, r: int, c: int) -> None:
        if self.game.game_over:
            return
        res = self.game.reveal(r, c)
        if res == "mine":
            messagebox.showinfo("Minesweeper", "Hit a mine — game over.")
        elif res == "win":
            messagebox.showinfo("Minesweeper", "You cleared the board.")
        self._refresh_board()
        self._refresh_knowledge()

    def _on_flag(self, r: int, c: int) -> None:
        if self.game.game_over:
            return
        self.game.toggle_flag(r, c)
        self._refresh_board()
        self._refresh_knowledge()

    def _refresh_board(self) -> None:
        self._update_mines_counter()
        for r in range(self.rows):
            for c in range(self.cols):
                btn = self.buttons[r][c]
                btn.config(state=tk.NORMAL)
                if (r, c) in self.game.flagged and (r, c) not in self.game.revealed:
                    btn.config(
                        text="⚑",
                        fg=FLAG_FG,
                        bg=FLAG_BG,
                        activebackground=FLAG_BG,
                        relief=tk.RAISED,
                        highlightbackground=TILE_HIDDEN_BORDER,
                    )
                elif (r, c) not in self.game.revealed:
                    btn.config(
                        text="",
                        fg=BLACK,
                        bg=TILE_HIDDEN,
                        activebackground=TILE_HIDDEN,
                        relief=tk.RAISED,
                        highlightbackground=TILE_HIDDEN_BORDER,
                    )
                elif (r, c) in self.game.mines:
                    btn.config(
                        text="✹",
                        fg=MINE_ICON,
                        bg=MINE_WRONG,
                        relief=tk.SUNKEN,
                        highlightbackground=MINE_WRONG,
                    )
                else:
                    n = self.game.display_number(r, c)
                    if n == 0:
                        btn.config(
                            text="",
                            fg=BLACK,
                            bg=TILE_REVEALED,
                            relief=tk.SUNKEN,
                            highlightbackground=TILE_REVEALED,
                        )
                    else:
                        btn.config(
                            text=str(n),
                            fg=NUM_COLORS.get(n, BLACK),
                            bg=TILE_NUMBER_BG,
                            relief=tk.SUNKEN,
                            highlightbackground=TILE_NUMBER_BG,
                        )
        if self.game.game_over and not self.game.won:
            for rr in range(self.rows):
                for cc in range(self.cols):
                    if (rr, cc) in self.game.mines and (rr, cc) not in self.game.revealed:
                        b = self.buttons[rr][cc]
                        b.config(
                            text="✹",
                            fg=WHITE,
                            bg=MINE_REVEAL,
                            activebackground=MINE_REVEAL,
                            highlightbackground=MINE_REVEAL,
                        )

    @staticmethod
    def _fmt_km_compact_lines(km: dict[str, int]) -> str:
        if not km:
            return "  (empty — reveal cells with numbers next to unknowns to add sentences)\n"
        lines: list[str] = []
        for k in sorted(km.keys(), key=lambda s: (len(s), s)):
            lines.append(f"  '{k}'={km[k]}")
        return "\n".join(lines) + "\n"

    def _fmt_cell_list_human(self, labels: list[str]) -> str:
        if not labels:
            return "(none)"
        sort_l = sorted(labels, key=lambda s: tuple(map(int, s.split("_", 1))))
        return ", ".join(human_cell_name_from_label(x) for x in sort_l)

    def _refresh_knowledge(self) -> None:
        km0, km1, deduced_mines, deduced_clear = knowledge_snapshot(self.game)
        kt = self.knowledge_text
        kt.delete("1.0", tk.END)

        kt.insert(tk.END, "1) Knowledge from the board (initial km). (R,C)\n\n", "k_sec")
        kt.insert(tk.END, self._fmt_km_compact_lines(km0), "k_plain")

        kt.insert(tk.END, "\n2) After iterative inference\n\n", "k_sec")

        kt.insert(tk.END, "   ", "k_plain")
        kt.insert(tk.END, "Deduced safe to open:", "k_lbl")
        kt.insert(
            tk.END,
            " " + self._fmt_cell_list_human(deduced_clear) + "\n",
            "k_plain",
        )

        kt.insert(tk.END, "   ", "k_plain")
        kt.insert(tk.END, "Deduced mines:", "k_lbl")
        kt.insert(
            tk.END,
            " " + self._fmt_cell_list_human(deduced_mines) + "\n\n",
            "k_plain",
        )

        kt.insert(tk.END, "   Simplified km:\n\n", "k_plain")
        kt.insert(tk.END, self._fmt_km_compact_lines(km1), "k_plain")

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    MinesweeperApp().run()
