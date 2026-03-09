import random

def get_int(prompt: str, min_val: int = None, max_val: int = None) -> int:
    """Prompt until the user enters a valid integer (optionally within bounds)."""
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if min_val is not None and value < min_val:
                print(f"Please enter a number >= {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"Please enter a number <= {max_val}.")
                continue
            return value
        except ValueError:
            print("Please enter a valid integer.")

def make_maze(rows: int, cols: int, percent_x: int) -> list[str]:
    """Return a list of strings representing a maze."""
    p = percent_x / 100.0
    maze_lines = []
    for _ in range(rows):
        line_chars = []
        for _ in range(cols):
            line_chars.append('X' if random.random() < p else '.')
        maze_lines.append(''.join(line_chars))
    return maze_lines

def main() -> None:
    print("=== Maze File Generator ===")
    rows = get_int("Number of rows: ", min_val=1)
    cols = get_int("Number of columns: ", min_val=1)
    percent_x = get_int("Percentage of X's (0-100): ", min_val=0, max_val=100)
    filename = input("Output file name (e.g., maze1.txt): ").strip()

    if not filename:
        print("Error: file name cannot be blank.")
        return

    maze = make_maze(rows, cols, percent_x)

    try:
        with open(filename, "w", encoding="utf-8") as f:
            for line in maze:
                f.write(line + "\n")
        print(f"Saved maze to '{filename}' ({rows}x{cols}, {percent_x}% X).")
    except OSError as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    main()