# bfs_dfs_astar_history.py
# spring 2024 (updated spring 2026)
# prof. lehman
#
# BFS, DFS, A* maze traversal
# Enhancement: writes history.csv for later animation/replay

from collections import deque
import heapq
import csv


steps_explored = 0


# ----------------------------
# I/O helpers
# ----------------------------
def read_maze(filename):
    with open(filename, "r") as file:
        return [list(line.rstrip("\n")) for line in file]


def find_start_end(maze):
    start = end = None
    for i, row in enumerate(maze):
        for j, cell in enumerate(row):
            if cell == "A":
                start = (i, j)
            elif cell == "B":
                end = (i, j)
    return start, end


def reconstruct_path(parent_map, start, end):
    """Returns [] if end unreachable."""
    if end not in parent_map:
        return []
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = parent_map[cur]
    path.reverse()
    if not path or path[0] != start:
        return []
    return path


# ----------------------------
# History logging
# ----------------------------
def write_history_csv(filename, algorithm, maze, start, end, events, path):
    """
    Writes ONE CSV with mixed record types.

    record_type values:
      META  : global settings
      CELL  : maze grid snapshot
      EVENT : discover/expand/update events
      PATH  : final path cells in order (if found)
    """
    rows = len(maze)
    cols = len(maze[0]) if rows > 0 else 0

    fieldnames = [
        "record_type",
        "algorithm",
        "step",
        "event",
        "row",
        "col",
        "parent_row",
        "parent_col",
        "g",
        "f",
        "frontier_size",
        "maze_rows",
        "maze_cols",
        "cell_value",
        "start_row",
        "start_col",
        "end_row",
        "end_col",
    ]

    with open(filename, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        # META
        w.writerow({
            "record_type": "META",
            "algorithm": algorithm,
            "maze_rows": rows,
            "maze_cols": cols,
            "start_row": start[0],
            "start_col": start[1],
            "end_row": end[0],
            "end_col": end[1],
        })

        # CELL snapshot (lets the animation program recreate the maze without reading maze_blank.txt)
        for r in range(rows):
            for c in range(cols):
                w.writerow({
                    "record_type": "CELL",
                    "algorithm": algorithm,
                    "row": r,
                    "col": c,
                    "cell_value": maze[r][c],
                })

        # EVENT timeline
        for e in events:
            w.writerow({
                "record_type": "EVENT",
                "algorithm": algorithm,
                "step": e.get("step"),
                "event": e.get("event"),
                "row": e.get("row"),
                "col": e.get("col"),
                "parent_row": e.get("parent_row"),
                "parent_col": e.get("parent_col"),
                "g": e.get("g"),
                "f": e.get("f"),
                "frontier_size": e.get("frontier_size"),
            })

        # PATH (in order)
        for i, (r, c) in enumerate(path):
            w.writerow({
                "record_type": "PATH",
                "algorithm": algorithm,
                "step": i,
                "row": r,
                "col": c,
            })


# ----------------------------
# Search algorithms (now emit events)
# ----------------------------
def bfs(maze, start, end):
    global steps_explored
    steps_explored = 0

    queue = deque([start])
    parent = {start: None}
    events = []
    step = 0

    # optional: record initial "discover" for start
    events.append({
        "step": step, "event": "DISCOVER",
        "row": start[0], "col": start[1],
        "parent_row": "", "parent_col": "",
        "g": 0, "f": "",
        "frontier_size": len(queue)
    })
    step += 1

    while queue:
        current = queue.popleft()
        steps_explored += 1

        events.append({
            "step": step, "event": "EXPAND",
            "row": current[0], "col": current[1],
            "parent_row": (parent[current][0] if parent[current] else ""),
            "parent_col": (parent[current][1] if parent[current] else ""),
            "g": "", "f": "",
            "frontier_size": len(queue)
        })
        step += 1

        if current == end:
            break

        for di, dj in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            ni, nj = current[0] + di, current[1] + dj
            if (
                0 <= ni < len(maze)
                and 0 <= nj < len(maze[0])
                and maze[ni][nj] != "X"
                and (ni, nj) not in parent
            ):
                parent[(ni, nj)] = current
                queue.append((ni, nj))

                events.append({
                    "step": step, "event": "DISCOVER",
                    "row": ni, "col": nj,
                    "parent_row": current[0], "parent_col": current[1],
                    "g": "", "f": "",
                    "frontier_size": len(queue)
                })
                step += 1

    path = reconstruct_path(parent, start, end)
    tried = { (e["row"], e["col"]) for e in events if e["event"] == "EXPAND" }
    return path, tried, events


def dfs(maze, start, end):
    global steps_explored
    steps_explored = 0

    stack = [start]
    parent = {start: None}
    events = []
    step = 0

    events.append({
        "step": step, "event": "DISCOVER",
        "row": start[0], "col": start[1],
        "parent_row": "", "parent_col": "",
        "g": 0, "f": "",
        "frontier_size": len(stack)
    })
    step += 1

    while stack:
        current = stack.pop()
        steps_explored += 1

        events.append({
            "step": step, "event": "EXPAND",
            "row": current[0], "col": current[1],
            "parent_row": (parent[current][0] if parent[current] else ""),
            "parent_col": (parent[current][1] if parent[current] else ""),
            "g": "", "f": "",
            "frontier_size": len(stack)
        })
        step += 1

        if current == end:
            break

        for di, dj in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            ni, nj = current[0] + di, current[1] + dj
            if (
                0 <= ni < len(maze)
                and 0 <= nj < len(maze[0])
                and maze[ni][nj] != "X"
                and (ni, nj) not in parent
            ):
                parent[(ni, nj)] = current
                stack.append((ni, nj))

                events.append({
                    "step": step, "event": "DISCOVER",
                    "row": ni, "col": nj,
                    "parent_row": current[0], "parent_col": current[1],
                    "g": "", "f": "",
                    "frontier_size": len(stack)
                })
                step += 1

    path = reconstruct_path(parent, start, end)
    tried = { (e["row"], e["col"]) for e in events if e["event"] == "EXPAND" }
    return path, tried, events


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star(maze, start, end):
    global steps_explored
    steps_explored = 0

    open_heap = []
    heapq.heappush(open_heap, (heuristic(start, end), start))

    parent = {start: None}
    g_score = {start: 0}
    closed = set()

    events = []
    step = 0

    events.append({
        "step": step, "event": "DISCOVER",
        "row": start[0], "col": start[1],
        "parent_row": "", "parent_col": "",
        "g": 0, "f": heuristic(start, end),
        "frontier_size": len(open_heap)
    })
    step += 1

    while open_heap:
        f, current = heapq.heappop(open_heap)

        # Skip stale entries
        if current in closed:
            continue

        closed.add(current)
        steps_explored += 1

        events.append({
            "step": step, "event": "EXPAND",
            "row": current[0], "col": current[1],
            "parent_row": (parent[current][0] if parent[current] else ""),
            "parent_col": (parent[current][1] if parent[current] else ""),
            "g": g_score.get(current, ""),
            "f": f,
            "frontier_size": len(open_heap)
        })
        step += 1

        if current == end:
            break

        for di, dj in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            neighbor = (current[0] + di, current[1] + dj)

            if not (0 <= neighbor[0] < len(maze) and 0 <= neighbor[1] < len(maze[0])):
                continue
            if maze[neighbor[0]][neighbor[1]] == "X":
                continue

            tentative_g = g_score[current] + 1

            if neighbor not in g_score:
                # first time seen
                parent[neighbor] = current
                g_score[neighbor] = tentative_g
                new_f = tentative_g + heuristic(neighbor, end)
                heapq.heappush(open_heap, (new_f, neighbor))

                events.append({
                    "step": step, "event": "DISCOVER",
                    "row": neighbor[0], "col": neighbor[1],
                    "parent_row": current[0], "parent_col": current[1],
                    "g": tentative_g,
                    "f": new_f,
                    "frontier_size": len(open_heap)
                })
                step += 1

            elif tentative_g < g_score[neighbor]:
                # found a better route
                parent[neighbor] = current
                g_score[neighbor] = tentative_g
                new_f = tentative_g + heuristic(neighbor, end)
                heapq.heappush(open_heap, (new_f, neighbor))

                events.append({
                    "step": step, "event": "UPDATE",
                    "row": neighbor[0], "col": neighbor[1],
                    "parent_row": current[0], "parent_col": current[1],
                    "g": tentative_g,
                    "f": new_f,
                    "frontier_size": len(open_heap)
                })
                step += 1

    path = reconstruct_path(parent, start, end)
    tried = { (e["row"], e["col"]) for e in events if e["event"] == "EXPAND" }
    return path, tried, events


# ----------------------------
# Display helpers (your original output still works)
# ----------------------------
def display_maze(maze, path):
    grid = [row[:] for row in maze]
    for (r, c) in path:
        if grid[r][c] not in ("A", "B", "X"):
            grid[r][c] = "P"
    for row in grid:
        print("".join(row))


# *** main ***


maze_file = "maze_file.txt"
temp = input("Enter maze file name (maze_file.txt default): ").strip()
if len(temp) > 0:
    maze_file = temp

maze = read_maze(maze_file)
start, end = find_start_end(maze)

if start is None or end is None:
    print("Error: maze must contain both 'A' and 'B'.")
    raise SystemExit

search_method = input("Enter search method (BFS, DFS, or A*): ").strip().upper()

if search_method == "BFS":
    algorithm = "BFS"
    algorithm_name = "BFS"
    path, tried, events = bfs(maze, start, end)
elif search_method == "DFS":
    algorithm = "DFS"
    algorithm_name = "DFS"
    path, tried, events = dfs(maze, start, end)
elif search_method in ("A*", "ASTAR", "A_STAR"):
    algorithm = "A*"
    algorithm_name = "AStar"
    path, tried, events = a_star(maze, start, end)
else:
    print("Invalid search method. Please enter 'BFS', 'DFS', or 'A*': ")
    raise SystemExit

# Write history for animation program
history_file = "history.csv"
temp = input("Enter history file name (\"history\" default): ").strip()
   
if len(temp) > 0:
    history_file = temp + "_" + algorithm_name + ".csv"
else:
    history_file = "history" + "_" + algorithm_name + ".csv"
    
write_history_csv(history_file, algorithm, maze, start, end, events, path)

# Console output (keep your current behavior)
print()
display_maze(maze, path)
print()

if not path:
    print("No path found from A to B.")
    print("Number of steps: 0")
else:
    print(f"Number of steps: {len(path) - 1}")

print(f"Number of steps explored: {steps_explored}")
print("Wrote replay file: ", history_file)