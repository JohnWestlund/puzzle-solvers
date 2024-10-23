import argparse

def is_perimeter(grid, x, y, pairs, label=None):
    rows, cols = len(grid), len(grid[0])
    
    # Temporarily modify the grid if a label is provided
    if label:
        try:
            start_end_pair = next(pair for pair in pairs if pair['label'] == label)
        except StopIteration:
            print(f"Label '{label}' not found in pairs.")
            return False

        start = start_end_pair['start']
        end = start_end_pair['end']
        original_start_value = grid[start[0]][start[1]]
        original_end_value = grid[end[0]][end[1]]
        grid[start[0]][start[1]] = 0
        grid[end[0]][end[1]] = 0

    # Check if the cell is on the perimeter of the grid
    if x == 0 or x == rows - 1 or y == 0 or y == cols - 1:
        if label:
            # Restore the original values
            grid[start[0]][start[1]] = original_start_value
            grid[end[0]][end[1]] = original_end_value
        return True

    # Check if the cell is adjacent to a non-traversable cell connected to the perimeter
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < rows and 0 <= ny < cols and (grid[nx][ny] == 0):# or grid[nx][ny] == -1):
            if nx == 0 or nx == rows - 1 or ny == 0 or ny == cols - 1:
                if label:
                    # Restore the original values
                    grid[start[0]][start[1]] = original_start_value
                    grid[end[0]][end[1]] = original_end_value
                return True
            # Check if the non-traversable cell is connected to the perimeter
            for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nnx, nny = nx + ddx, ny + ddy
                if 0 <= nnx < rows and 0 <= nny < cols and (grid[nnx][nny] == 0):# or grid[nnx][nny] == -1):
                    if nnx == 0 or nnx == rows - 1 or nny == 0 or nny == cols - 1:
                        if label:
                            # Restore the original values
                            grid[start[0]][start[1]] = original_start_value
                            grid[end[0]][end[1]] = original_end_value
                        return True

    if label:
        # Restore the original values
        grid[start[0]][start[1]] = original_start_value
        grid[end[0]][end[1]] = original_end_value

    return False

def parse_grid(grid_str):
    rows = grid_str.split('.')
    grid = []
    pairs = []
    labels = []
    for i, row in enumerate(rows):
        grid_row = []
        for cell in row.split(','):
            try:
                value = int(cell)
                if value > 0:
                    grid_row.extend([1] * value)
                elif value < 0:
                    grid_row.extend([0] * abs(value))
                else:
                    grid_row.extend([0])
            except ValueError:
                if cell not in labels:
                    labels.append(cell)
                grid_row.append(-1)
                pairs.append({'label': cell, 'start': (i, len(grid_row) - 1)})
        grid.append(grid_row)
    max_length = max(len(row) for row in grid)
    for row in grid:
        row.extend([0] * (max_length - len(row)))
    pairs_dict = {}
    for pair in pairs:
        label = pair['label']
        position = pair['start']
        if label in pairs_dict:
            pairs_dict[label].append(position)
        else:
            pairs_dict[label] = [position]
    # Check that each label has exactly two coordinates
    for label, positions in pairs_dict.items():
        if len(positions) != 2:
            print(f"Error: Label '{label}' does not have exactly two coordinates. Found positions: {positions}")
            exit(1)
    start_end_pairs = [{'start': positions[0], 'end': positions[1], 'label': label} for label, positions in pairs_dict.items()]
    return grid, start_end_pairs, labels

def colorize(cell, pairs, labels):
    colors = [
        "\033[97m",  # White
        "\033[90m",  # Bright Black (Gray)
        "\033[41m",  # Red Background
        "\033[42m",  # Green Background
        "\033[43m",  # Yellow Background
        "\033[44m",  # Blue Background
        "\033[45m",  # Magenta Background
        "\033[46m",  # Cyan Background
        "\033[47m",  # White Background
        "\033[91m",  # Red
        "\033[92m",  # Green
        "\033[93m",  # Yellow
        "\033[94m",  # Blue
        "\033[95m",  # Magenta
        "\033[96m",  # Cyan
    ]
    reset = '\033[0m'
    color_map = {labels[i]: colors[i % len(colors)] for i in range(len(labels))}
    if isinstance(cell, tuple):
        direction, label = cell
        if label in color_map:
            return f"{color_map[label]}{direction}{reset}"
    else:
        if cell == 1 or cell == '1':
            return '_'
        elif cell == 0 or cell == '0':
            return '#'
        elif cell == -1 or cell == '-1':
            return '*'
        elif cell == '@':
            return f"\033[93m@{reset}"  # Yellow for perimeter cells
    return f"{color_map.get(cell, '')}{cell}{reset}"

def print_grid(grid, pairs, use_color, labels):
    grid_copy = [row[:] for row in grid]
    for pair in pairs:
        label = pair['label']
        sx, sy = pair['start']
        ex, ey = pair['end']
        grid_copy[sx][sy] = label
        grid_copy[ex][ey] = label
    for row in grid_copy:
        if use_color:
            print(' '.join(colorize(str(cell), None, labels) for cell in row))
        else:
            print(' '.join(str(cell) for cell in row))
    print()

def main():
    parser = argparse.ArgumentParser(description="Grid Perimeter Finder")
    parser.add_argument('-g', '--grid', type=str, required=True, help="Grid definition string")
    parser.add_argument('-c', '--color', action='store_true', help="Enable colored output")
    parser.add_argument('-p', '--path', type=str, help="Start and end labels separated by a comma (e.g., A,B)")
    args = parser.parse_args()

    grid, pairs, labels = parse_grid(args.grid)

    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == 1:  # Only consider traversable cells
                for pair in pairs:
                    start, end = pair['start'], pair['end']
                    if is_perimeter(grid, i, j, pairs, args.path):
                        grid[i][j] = '@'

    print("Grid with Perimeter cells marked:")
    print_grid(grid, pairs, args.color, labels)

if __name__ == "__main__":
    main()
