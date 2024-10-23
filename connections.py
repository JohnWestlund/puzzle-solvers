import argparse

# Global counter for the number of paths found
path_counter = 0
current_pair_info = ""
print_progress = False
verbosity = 0
hardcoded_paths = {}
solution_found = False  # Global variable to indicate if a solution has been found
fast_mode = False  # Global variable to enable fast mode

def is_valid_move(grid, x, y, visited):
    rows, cols = len(grid), len(grid[0])
    return 0 <= x < rows and 0 <= y < cols and grid[x][y] == 1 and (x, y) not in visited

def is_perimeter(grid, x, y, start, end):
    rows, cols = len(grid), len(grid[0])

    # Check if the cell is on the perimeter of the grid
    if (x, y) == start or (x, y) == end:
        return True
    if x == 0 or x == rows - 1 or y == 0 or y == cols - 1:
        return True

    # Check if the cell is adjacent to a non-traversable cell connected to the perimeter
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 0:
            if nx == 0 or nx == rows - 1 or ny == 0 or ny == cols - 1:
                return True
            # Check if the non-traversable cell is connected to the perimeter
            for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nnx, nny = nx + ddx, ny + ddy
                if 0 <= nnx < rows and 0 <= nny < cols and grid[nnx][nny] == 0:
                    if nnx == 0 or nnx == rows - 1 or nny == 0 or nny == cols - 1:
                        return True

    return False

def find_paths(grid, start, end, visited, max_paths, perimeter_mode=False):
    global path_counter, current_pair_info, print_progress, hardcoded_paths, solution_found, fast_mode
    if fast_mode and solution_found:
        return None  # Exit early if a solution has been found in fast mode

    if start == end:
        path_counter += 1
        if print_progress and path_counter % 512 == 0:
            print(f"\r{current_pair_info} Paths found: {path_counter}", end='', flush=True)
        if max_paths != -1 and path_counter >= max_paths:
            return None  # Indicate that the max cap has been reached
        return [[(end[0], end[1], 'E')]]  # Include a dummy direction for the end point

    if current_pair_info in hardcoded_paths:
        return hardcoded_paths[current_pair_info]

    x, y = start
    visited.add(start)
    paths = []
    for dx, dy, direction in [(-1, 0, '^'), (1, 0, 'v'), (0, -1, '<'), (0, 1, '>')]:
        nx, ny = x + dx, y + dy
        if is_valid_move(grid, nx, ny, visited) and (not perimeter_mode or is_perimeter(grid, nx, ny, start, end)):
            result = find_paths(grid, (nx, ny), end, visited, max_paths, perimeter_mode)
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
    global solution_found, fast_mode
    if fast_mode and solution_found:
        return []  # Exit early if a solution has been found in fast mode

    if verbosity >= 2:
        print(f"Debug: find_all_paths called with index={index}, visited={visited}, total_traversable={total_traversable}")

    if index == len(pairs):
        if verbosity >= 2:
            print(f"Debug: Reached end of pairs with visited={len(visited)}")
        if len(visited) == total_traversable:
            solution_found = True  # Mark that a solution has been found
            return [[]]
        else:
            return []

    pair = pairs[index]
    start, end, label = pair['start'], pair['end'], pair['label']
    all_paths = []

    # Temporarily make the start and end points traversable
    grid[start[0]][start[1]] = 1
    grid[end[0]][end[1]] = 1

    if verbosity >= 2:
        print(f"Debug: Trying to find paths from {start} to {end}")

    for path in find_paths(grid, start, end, visited, -1):
        if path is None:
            grid[start[0]][start[1]] = 0
            grid[end[0]][end[1]] = 0
            if verbosity >= 2:
                print(f"Debug: Early exit due to max cap reached for pair {start} -> {end}")
            return all_paths  # Early exit if max cap is reached

        new_visited = visited | set((x, y) for x, y, _ in path)

        if verbosity >= 3:
            print(f"Debug: Found path from {start} to {end}, new_visited={new_visited}")

        for subsequent_paths in find_all_paths(grid, pairs, index + 1, new_visited, total_traversable):
            all_paths.append([path] + subsequent_paths)

        # Early exit if all traversable locations are used
        if len(new_visited) == total_traversable:
            grid[start[0]][start[1]] = 0
            grid[end[0]][end[1]] = 0
            if verbosity >= 1:
                print(f"Debug: Early exit with all traversable locations used for pair {start} -> {end}")
            return all_paths

    grid[start[0]][start[1]] = 0
    grid[end[0]][end[1]] = 0

    if verbosity >= 2:
        print(f"Debug: Returning all_paths with length={len(all_paths)} for pair {start} -> {end}")

    return all_paths

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

def print_paths_on_grid(grid, paths, pairs, use_color, labels, debug_level=0):
    grid_copy = [row[:] for row in grid]
    for i, path in enumerate(paths):
        pair = pairs[i]
        label = pair['label']
        if debug_level >= 1:
            print(f"Debug: Printing path for label {label} from {pair['start']} to {pair['end']}")
        sx, sy = pair['start']
        ex, ey = pair['end']
        for (x, y, direction) in path:
            if (x, y) != pair['start'] and (x, y) != pair['end']:  # Check if (x, y) are any of the pairs' start or end coordinates
                for other_pair in pairs:
                    if (x, y) == other_pair['start'] or (x, y) == other_pair['end']:
                        print(f"Conflict: Label {label} attempting to write to coordinate ({x}, {y}) which is start/end of label {other_pair['label']}")
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

def parse_hardcoded_path(path_str, start):
    directions = path_str.split(',')
    path = []
    x, y = start
    for direction in directions:
        if direction == '^':
            x -= 1
        elif direction == 'v':
            x += 1
        elif direction == '<':
            y -= 1
        elif direction == '>':
            y += 1
        path.append((x, y, direction))
    return path

def apply_hardcoded_paths(grid, pairs, labels):
    global hardcoded_paths
    all_paths = []
    for label, path in hardcoded_paths.items():
        pair = next(pair for pair in pairs if pair['label'] == label)
        start, end = pair['start'], pair['end']
        x, y = start
        for (dx, dy, direction) in path:
            if direction == '^':
                x -= 1
            elif direction == 'v':
                x += 1
            elif direction == '<':
                y -= 1
            elif direction == '>':
                y += 1
            if 0 <= x < len(grid) and 0 <= y < len(grid[0]):
                grid[x][y] = 1
            else:
                raise IndexError(f"Path for label {label} goes out of grid bounds at ({x}, {y})")
        all_paths.append(path)
    return all_paths

def main():
    parser = argparse.ArgumentParser(description="Grid Path Finder")
    parser.add_argument('-c', '--color', action='store_true', help="Enable colored output")
    parser.add_argument('-g', '--grid', type=str, required=True, help="Grid definition string")
    parser.add_argument('-s', '--solve', action='store_true', help="Solve the grid and find paths")
    parser.add_argument('-m', '--max', type=int, default=500000, help="Maximum number of paths to find before stopping early (default: 500000, -1 for infinite)")
    parser.add_argument('-p', '--perimeter', type=str, help="Solve for perimeter path for the specified pair label")
    parser.add_argument('-P', '--path', type=str, nargs=2, action='append', metavar=('LABEL', 'DIRECTIONS'), help="Specify a hardcoded path for a pair (can be used multiple times)")
    parser.add_argument('-v', '--verbose', action='count', default=0, help="Increase verbosity level")
    parser.add_argument('-f', '--fast', action='store_true', help="Enable fast mode to stop after finding the first solution")
    args = parser.parse_args()

    global max_paths, print_progress, verbosity, hardcoded_paths, fast_mode 
    max_paths = args.max
    verbosity = args.verbose
    fast_mode = args.fast

    grid, pairs, labels = parse_grid(args.grid)
    total_traversable = sum(cell == 1 for row in grid for cell in row) + len(pairs) * 2

    if verbosity >= 1:
        print("Original Grid with Pairs Labeled:")
        print_grid(grid, pairs, args.color, labels)

    if args.path:
        for label, directions in args.path:
            pair = next(pair for pair in pairs if pair['label'] == label)
            start, end = pair['start'], pair['end']
            hardcoded_path = parse_hardcoded_path(directions, start)
            hardcoded_paths[label] = hardcoded_path

    if args.perimeter:
        pair = next(pair for pair in pairs if pair['label'] == args.perimeter)
        start, end = pair['start'], pair['end']
        global path_counter, current_pair_info
        path_counter = 0
        current_pair_info = f"Pair {pair['label']} ({start} -> {end}):"
        grid[start[0]][start[1]] = 1
        grid[end[0]][end[1]] = 1
        print_progress = True
        print(current_pair_info, end=' ')
        paths = find_paths(grid, start, end, set(), max_paths, perimeter_mode=True)
        print_progress = False
        if paths is None:
            print(f"\r{current_pair_info} {max_paths} possible paths (max cap reached)")
        else:
            print(f"\r{current_pair_info} {len(paths)} possible paths")
        if verbosity >= 1:
            print_paths_on_grid(grid, paths, [pair], args.color, [pair['label']], debug_level=verbosity)
        # Print the path definition in the format that the --path option will accept
        if paths:
            path_directions = ','.join(direction for _, _, direction in paths[0] if direction != 'E')
            print(f"Path definition for --path option: -P {pair['label']} \"{path_directions}\"")
        grid[start[0]][start[1]] = 0
        grid[end[0]][end[1]] = 0
        return

    if args.solve:
        # Apply hardcoded paths to the grid and include them in the all_paths
        hardcoded_paths_list = apply_hardcoded_paths(grid, pairs, labels)
        # Mark cells in hardcoded paths as non-traversable
        if hardcoded_paths_list:
            for path in hardcoded_paths_list:
                for x, y, _ in path:
                    grid[x][y] = 0
        # Print the grid with hardcoded paths before solving
        print("Grid with Hardcoded Paths Applied:")
        print_grid(grid, pairs, args.color, labels)
        # Remove pairs that have hardcoded paths
        pairs_to_solve = [pair for pair in pairs if pair['label'] not in hardcoded_paths]
        pairs_already_solved = [pair for pair in pairs if pair['label'] in hardcoded_paths]
        # Adjust total_traversable to account for hardcoded paths
        total_traversable -= sum(len(path) + 1 for path in hardcoded_paths_list) # Add 1 for the dummy direction
        if verbosity >= 1:
            print(f"Debug: Adjusted total_traversable={total_traversable} after applying hardcoded paths")
        pair_paths_count = []
        for pair in pairs_to_solve:
            start, end = pair['start'], pair['end']
            path_counter = 0
            current_pair_info = f"Pair {pair['label']} ({start} -> {end}):"
            grid[start[0]][start[1]] = 1
            grid[end[0]][end[1]] = 1
            print_progress = True
            print(current_pair_info, end=' ')
            paths = find_paths(grid, start, end, set(), max_paths)
            print_progress = False
            if paths is None:
                print(f"\r{current_pair_info} {max_paths} possible paths (max cap reached)")
                pair_paths_count.append((max_paths, pair))
            else:
                print(f"\r{current_pair_info} {len(paths)} possible paths")
                pair_paths_count.append((len(paths), pair))
            del paths # Explicitly delete the paths object to free memory
            grid[start[0]][start[1]] = 0
            grid[end[0]][end[1]] = 0
        pair_paths_count.sort()
        sorted_pairs = [pair for _, pair in pair_paths_count]
        all_paths = find_all_paths(grid, sorted_pairs, 0, set(), total_traversable)
        # Mark cells in hardcoded paths as traversable
        for path in hardcoded_paths_list:
            for x, y, _ in path:
                grid[x][y] = 1
        if hardcoded_paths_list:
            all_paths = [hardcoded_paths_list + solution for solution in all_paths]
        if all_paths:
            print("Solution found:")
            for paths in all_paths:
                print_paths_on_grid(grid, paths, pairs_already_solved + sorted_pairs, args.color, labels, debug_level=verbosity)
        else:
            print("No solution found that uses all traversable locations.")

if __name__ == "__main__":
    main()
