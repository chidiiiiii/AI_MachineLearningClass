"""
p4_maze_viewer.py
Spring 2026
Prof. Lehman (viewer generated with ChatGPT prompts)

Tkinter viewer that opens history.csv produced by p4_maze_search.py
and animates the search:

- Walls (X), open cells (.), start (A), end (B)
- DISCOVER events mark frontier
- EXPAND events mark tried/expanded and remove from frontier
- UPDATE events (A*) treated like DISCOVER (optional highlight)
- PATH records can be overlaid at the end (or anytime via toggle)

Controls:
- Open CSV
- Play / Pause
- Step
- Reset
- Speed slider (ms per step)
- Toggle: show path overlay
"""

import csv
import tkinter as tk
from tkinter import filedialog, messagebox


class MazeHistoryViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Maze History Viewer (BFS / DFS / A*)")
        self.geometry("1000x750")

        # --- Data ---
        self.algorithm = ""
        self.rows = 0
        self.cols = 0
        self.start = (0, 0)
        self.end = (0, 0)

        self.base_grid = []          # chars from CELL snapshot
        self.events = []             # list of dicts sorted by step
        self.path_cells = []         # list of (r,c) in order

        # Replay state
        self.current_index = 0
        self.playing = False
        self.after_id = None
        self.ms_per_step = 60

        self.frontier = set()
        self.tried = set()

        # --- UI ---
        self._build_ui()

    # ---------------------------
    # UI setup
    # ---------------------------
    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        self.btn_open = tk.Button(top, text="Open history.csv", command=self.open_file)
        self.btn_open.pack(side=tk.LEFT)

        self.btn_play = tk.Button(top, text="Play", width=8, command=self.toggle_play, state=tk.DISABLED)
        self.btn_play.pack(side=tk.LEFT, padx=(10, 0))

        self.btn_step = tk.Button(top, text="Step", width=8, command=self.step_once, state=tk.DISABLED)
        self.btn_step.pack(side=tk.LEFT, padx=6)

        self.btn_reset = tk.Button(top, text="Reset", width=8, command=self.reset_replay, state=tk.DISABLED)
        self.btn_reset.pack(side=tk.LEFT, padx=6)

        tk.Label(top, text="Speed (ms/step):").pack(side=tk.LEFT, padx=(20, 4))
        self.speed = tk.Scale(top, from_=10, to=400, orient=tk.HORIZONTAL, length=220, command=self.on_speed_change)
        self.speed.set(self.ms_per_step)
        self.speed.pack(side=tk.LEFT)

        self.show_path_var = tk.BooleanVar(value=False)
        self.chk_path = tk.Checkbutton(top, text="Show path overlay", variable=self.show_path_var,
                                       command=self.redraw_all, state=tk.DISABLED)
        self.chk_path.pack(side=tk.LEFT, padx=(20, 0))

        self.status = tk.Label(self, text="Open a history.csv file to begin.", anchor="w")
        self.status.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 6))

        # Canvas with scrollbars
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.hbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.vbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")

        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        # Drawing params
        self.cell_size = 30
        self.pad = 10

        # item ids for fast updates
        self.rect_ids = {}  # (r,c) -> rect_id
        self.text_ids = {}  # (r,c) -> text_id

    # ---------------------------
    # File loading
    # ---------------------------
    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open history CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            self.load_history_csv(path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n\n{e}")
            return

        self.btn_play.config(state=tk.NORMAL)
        self.btn_step.config(state=tk.NORMAL)
        self.btn_reset.config(state=tk.NORMAL)
        self.chk_path.config(state=tk.NORMAL)
        self.btn_play.config(text="Play")

        self.reset_replay()
        self.status.config(text=f"Loaded: {path} | Algorithm: {self.algorithm} | Events: {len(self.events)}")

    def load_history_csv(self, filename):
        self.algorithm = ""
        self.rows = 0
        self.cols = 0
        self.start = (0, 0)
        self.end = (0, 0)

        self.base_grid = []
        self.events = []
        self.path_cells = []

        meta_seen = False
        cell_records = []
        event_records = []
        path_records = []

        with open(filename, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rtype = (row.get("record_type") or "").strip().upper()
                if rtype == "META":
                    meta_seen = True
                    self.algorithm = (row.get("algorithm") or "").strip()
                    self.rows = int(row.get("maze_rows") or 0)
                    self.cols = int(row.get("maze_cols") or 0)
                    self.start = (int(row.get("start_row") or 0), int(row.get("start_col") or 0))
                    self.end = (int(row.get("end_row") or 0), int(row.get("end_col") or 0))
                elif rtype == "CELL":
                    cell_records.append(row)
                elif rtype == "EVENT":
                    event_records.append(row)
                elif rtype == "PATH":
                    path_records.append(row)

        if not meta_seen or self.rows <= 0 or self.cols <= 0:
            raise ValueError("META record missing or invalid maze size.")

        # Build base grid from CELL records
        self.base_grid = [["." for _ in range(self.cols)] for _ in range(self.rows)]
        for rec in cell_records:
            rr = int(rec["row"])
            cc = int(rec["col"])
            val = (rec.get("cell_value") or ".")
            self.base_grid[rr][cc] = val

        # Parse events
        parsed_events = []
        for rec in event_records:
            step_s = rec.get("step") or ""
            if step_s.strip() == "":
                continue
            step = int(step_s)

            ev = (rec.get("event") or "").strip().upper()
            rr = int(rec.get("row") or 0)
            cc = int(rec.get("col") or 0)

            parsed_events.append({
                "step": step,
                "event": ev,
                "row": rr,
                "col": cc,
            })

        parsed_events.sort(key=lambda d: d["step"])
        self.events = parsed_events

        # Parse path (in order)
        parsed_path = []
        for rec in path_records:
            rr = int(rec.get("row") or 0)
            cc = int(rec.get("col") or 0)
            step_s = rec.get("step") or ""
            step = int(step_s) if step_s.strip() != "" else 0
            parsed_path.append((step, rr, cc))

        parsed_path.sort(key=lambda t: t[0])
        self.path_cells = [(rr, cc) for (_, rr, cc) in parsed_path]

        # Build / redraw canvas
        self.build_canvas_grid()

    # ---------------------------
    # Drawing
    # ---------------------------
    def build_canvas_grid(self):
        self.canvas.delete("all")
        self.rect_ids.clear()
        self.text_ids.clear()

        # Choose a reasonable cell size for large mazes
        max_w = 900
        max_h = 600
        if self.cols > 0 and self.rows > 0:
            size_w = max(8, min(40, (max_w - 2 * self.pad) // self.cols))
            size_h = max(8, min(40, (max_h - 2 * self.pad) // self.rows))
            self.cell_size = min(size_w, size_h)

        cs = self.cell_size
        pad = self.pad

        width = pad * 2 + self.cols * cs
        height = pad * 2 + self.rows * cs
        self.canvas.configure(scrollregion=(0, 0, width, height))

        for r in range(self.rows):
            for c in range(self.cols):
                x1 = pad + c * cs
                y1 = pad + r * cs
                x2 = x1 + cs
                y2 = y1 + cs

                val = self.base_grid[r][c]
                fill, text = self.style_for_cell(r, c, base_val=val)

                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="gray80")
                t = self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, font=("Consolas", max(8, cs // 2)))

                self.rect_ids[(r, c)] = rect
                self.text_ids[(r, c)] = t

    def style_for_cell(self, r, c, base_val=None):
        """Return (fill_color, text_char) for a cell given current replay state."""
        if base_val is None:
            base_val = self.base_grid[r][c]

        # Base appearance
        if base_val == "X":
            fill = "black"
            text = ""
        elif base_val == "A":
            fill = "white"
            text = "A"
        elif base_val == "B":
            fill = "white"
            text = "B"
        else:
            fill = "white"
            text = ""

        # Overlay: tried/frontier/path
        # Keep walls always walls, and keep A/B text visible.
        if base_val != "X":
            is_start = (r, c) == self.start
            is_end = (r, c) == self.end

            if (r, c) in self.tried and not is_start and not is_end:
                fill = "light gray"
                text = "T"

            if (r, c) in self.frontier and not is_start and not is_end:
                fill = "khaki"
                text = "F"

            if self.show_path_var.get() and (r, c) in set(self.path_cells) and not is_start and not is_end:
                fill = "pale green"
                text = "P"

            # Ensure A/B stay visible
            if is_start:
                text = "A"
                fill = "white"
            if is_end:
                text = "B"
                fill = "white"

        return fill, text

    def redraw_cell(self, r, c):
        rect = self.rect_ids.get((r, c))
        text_id = self.text_ids.get((r, c))
        if rect is None or text_id is None:
            return

        fill, text = self.style_for_cell(r, c)
        self.canvas.itemconfigure(rect, fill=fill)
        self.canvas.itemconfigure(text_id, text=text)

    def redraw_all(self):
        # Update everything (used when toggling path overlay)
        for r in range(self.rows):
            for c in range(self.cols):
                self.redraw_cell(r, c)

    # ---------------------------
    # Replay controls
    # ---------------------------
    def on_speed_change(self, value):
        try:
            self.ms_per_step = int(float(value))
        except ValueError:
            self.ms_per_step = 60

    def toggle_play(self):
        if not self.events:
            return

        self.playing = not self.playing
        self.btn_play.config(text="Pause" if self.playing else "Play")

        if self.playing:
            self.schedule_next()
        else:
            self.cancel_scheduled()

    def cancel_scheduled(self):
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def schedule_next(self):
        self.cancel_scheduled()
        self.after_id = self.after(self.ms_per_step, self.play_tick)

    def play_tick(self):
        if not self.playing:
            return

        if self.current_index >= len(self.events):
            self.playing = False
            self.btn_play.config(text="Play")
            self.after_id = None
            return

        self.step_once()
        self.schedule_next()

    def reset_replay(self):
        self.cancel_scheduled()
        self.playing = False
        self.btn_play.config(text="Play")

        self.current_index = 0
        self.frontier.clear()
        self.tried.clear()

        self.redraw_all()
        self.update_step_status()

    def update_step_status(self):
        if not self.events:
            self.status.config(text="No events loaded.")
            return
        if self.current_index >= len(self.events):
            self.status.config(text=f"{self.algorithm} | Done | steps: {len(self.events)}")
        else:
            ev = self.events[self.current_index]
            self.status.config(text=f"{self.algorithm} | step {self.current_index+1}/{len(self.events)} "
                                   f"| next: {ev['event']} at ({ev['row']},{ev['col']})")

    def step_once(self):
        if self.current_index >= len(self.events):
            self.update_step_status()
            return

        ev = self.events[self.current_index]
        r, c = ev["row"], ev["col"]
        kind = ev["event"]

        # Apply event to overlay sets
        if kind == "DISCOVER":
            # Add to frontier if it's not already expanded
            if (r, c) not in self.tried:
                self.frontier.add((r, c))
                self.redraw_cell(r, c)

        elif kind == "EXPAND":
            # Remove from frontier and mark tried
            if (r, c) in self.frontier:
                self.frontier.remove((r, c))
            self.tried.add((r, c))
            self.redraw_cell(r, c)

        elif kind == "UPDATE":
            # Treat like a "re-discover" (keeps it visible as frontier if not expanded)
            if (r, c) not in self.tried:
                self.frontier.add((r, c))
                self.redraw_cell(r, c)

        else:
            # Unknown event type: ignore safely
            pass

        self.current_index += 1
        self.update_step_status()


if __name__ == "__main__":
    app = MazeHistoryViewer()
    app.mainloop()