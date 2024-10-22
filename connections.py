import argparse

# Global counter for the number of paths found
path_counter = 0
current_pair_info = ""
print_progress = False

def is_valid_move(grid, x, y, visited):
    rows, cols = len(grid), len(grid[0])
    return 0 <= x < rows and 0 <= y < cols and grid[x][y] == 1 and (x, y) not in visited

def find_paths(grid, start, end, visited, max_paths):
    global path_counter, current_pair_info, print_progress
    if start == end:
        path_counter += 1
        if print_progress and path_counter % 1000 == 0:
            print(f"\r{current_pair_info} Paths found: {path_counter}", end='', flush=True)
        if max_paths != -1 and path_counter >= max_paths:
            return None  # Indicate that the max cap has been reached
        return [[(end[0], end[1], 'E')]]  # Include a dummy direction for the end point

    x, y = start
    visited.add(start)
    paths = []
    for dx, dy, direction in [(-1, 0, '^'), (1, 0, 'v'), (0, -1, '<'), (0, 1, '>')]:
        nx, ny = x + dx, y + dy
        if is_valid_move(grid, nx, ny, visited):
            result = find_paths(grid, (nx, ny), end, visited, max_paths)
            if result is None:
                visited.remove(start)
                return None  # Propagate the max cap reached signal
            for path in result:
                paths.append([(x, y, direction)] + path)
            if max_paths != -1 and path_counter >= max_paths:
                visited.remove(start)
                return paths
    visited.remove(start)
    return paths

def find_all_paths(grid, pairs, index, visited, total_traversable):
    if index == len(pairs):
        return [[]] if len(visited) == total_traversable else []
    
    start, end = pairs[index]
    all_paths = []
    # Temporarily make the start and end points traversable
    grid[start[0]][start[1]] = 1
    grid[end[0]][end[1]] = 1
    for path in find_paths(grid, start, end, visited, -1):  # Pass -1 as max_paths
        if path is None:
            grid[start[0]][start[1]] = 0
            grid[end[0]][end[1]] = 0
            return all_paths  # Early exit if max cap is reached
        new_visited = visited | set((x, y) for x, y, _ in path)
        for subsequent_paths in find_all_paths(grid, pairs, index + 1, new_visited, total_traversable):
            all_paths.append([path] + subsequent_paths)
        if len(new_visited) == total_traversable:
            grid[start[0]][start[1]] = 0
            grid[end[0]][end[1]] = 0
            return all_paths  # Early exit if all traversable locations are used
    grid[start[0]][start[1]] = 0
    grid[end[0]][end[1]] = 0
    return all_paths

def print_grid(grid, pairs, use_color, labels):
    grid_copy = [row[:] for row in grid]
    for i, (start, end) in enumerate(pairs):
        label = labels[i]
        sx, sy = start
        ex, ey = end
        grid_copy[sx][sy] = label
        grid_copy[ex][ey] = label
    for row in grid_copy:
        if use_color:
            print(' '.join(colorize(str(cell), None, labels) for cell in row))
        else:
            print(' '.join(str(cell) for cell in row))
    print()

def print_paths_on_grid(grid, paths, pairs, use_color, labels):
    grid_copy = [row[:] for row in grid]
    for i, path in enumerate(paths):
        label = labels[i]
        start, end = pairs[i]
        sx, sy = start
        ex, ey = end
        for (x, y, direction) in path:
            if (x, y) != start and (x, y) != end:
                grid_copy[x][y] = (direction, label)
        grid_copy[sx][sy] = label
        grid_copy[ex][ey] = label
    for row in grid_copy:
        if use_color:
            print(' '.join(colorize(cell, pairs, labels) for cell in row))
        else:
            print(' '.join(str(cell) for cell in row))
    print()

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
    return f"{color_map.get(cell, '')}{cell}{reset}"

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
                grid_row.append(0)
                pairs.append((cell, (i, len(grid_row) - 1)))
        grid.append(grid_row)
    max_length = max(len(row) for row in grid)
    for row in grid:
        row.extend([0] * (max_length - len(row)))
    pairs_dict = {}
    for label, position in pairs:
        if label in pairs_dict:
            pairs_dict[label].append(position)
        else:
            pairs_dict[label] = [position]
    start_end_pairs = [(positions[0], positions[1]) for positions in pairs_dict.values()]
    return grid, start_end_pairs, labels

def main():
    parser = argparse.ArgumentParser(description="Grid Path Finder")
    parser.add_argument('-c', '--color', action='store_true', help="Enable colored output")
    parser.add_argument('-g', '--grid', type=str, required=True, help="Grid definition string")
    parser.add_argument('-s', '--solve', action='store_true', help="Solve the grid and find paths")
    parser.add_argument('-m', '--max', type=int, default=-1, help="Maximum number of paths to find before stopping early")
    args = parser.parse_args()

    global max_paths, print_progress
    max_paths = args.max

    grid, pairs, labels = parse_grid(args.grid)
    total_traversable = sum(cell == 1 for row in grid for cell in row) + len(pairs) * 2

    print("Original Grid with Pairs Labeled:")
    print_grid(grid, pairs, args.color, labels)

    if args.solve:
        pair_paths_count = []
        for i, (start, end) in enumerate(pairs):
            global path_counter, current_pair_info
            path_counter = 0
            current_pair_info = f"Pair {labels[i]} ({start} -> {end}):"
            grid[start[0]][start[1]] = 1
            grid[end[0]][end[1]] = 1
            print_progress = True
            print(current_pair_info, end=' ')
            paths = find_paths(grid, start, end, set(), max_paths)
            print_progress = False
            if paths is None:
                print(f"\r{current_pair_info} {max_paths} possible paths (max cap reached)")
                pair_paths_count.append((max_paths, (start, end)))
            else:
                print(f"\r{current_pair_info} {len(paths)} possible paths")
                pair_paths_count.append((len(paths), (start, end)))
            del paths  # Explicitly delete the paths object to free memory
            grid[start[0]][start[1]] = 0
            grid[end[0]][end[1]] = 0

        pair_paths_count.sort()
        sorted_pairs = [pair for _, pair in pair_paths_count]

        all_paths = find_all_paths(grid, sorted_pairs, 0, set(), total_traversable)
        if all_paths:
            print("Solution found:")
            for paths in all_paths:
                print_paths_on_grid(grid, paths, sorted_pairs, args.color, labels)
                break  # Only print the first complete solution
        else:
            print("No solution found that uses all traversable locations.")

if __name__ == "__main__":
    main()
