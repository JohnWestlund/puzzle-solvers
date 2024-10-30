from grid import Grid, Path
import argparse
import itertools
import sys

def find_paths(grid_obj, start, end, visited, perimeter_mode=False, label=None):
    perimeter_message=" "
    if perimeter_mode:
        perimeter_message = " perimeter "

    def dfs(current, path, visited):
        nonlocal path_counter

        # Early return if path_counter exceeds max_paths
        if path_counter >= max_paths:
            return

        if current == end:
            # Append the 'E' dummy direction to indicate the end
            path.append('E')
            # Create a Path object with the given label
            paths.append(Path(label=label, start=start, end=end, directions=path[:]))
            path.pop()  # Remove 'E' after adding the path
            path_counter += 1

            # Print progress if enabled
            if print_progress and path_counter % 512 == 0:
                print(f"\rPair {label} ({start} -> {end}){perimeter_message}paths found: {path_counter}", end='', flush=True)
            return

        x, y = current
        visited.add(current)

        # Define possible moves: up, down, left, right
        moves = [(-1, 0, '^'), (1, 0, 'v'), (0, -1, '<'), (0, 1, '>')]

        for dx, dy, direction in moves:
            nx, ny = x + dx, y + dy
            if grid_obj.is_valid_move(nx, ny, visited) and (not perimeter_mode or grid_obj.is_perimeter(nx, ny, grid.pairs_dict.get(label, None))):
                path.append(direction)
                dfs((nx, ny), path, visited)
                path.pop()

        visited.remove(current)

    paths = []
    path_counter = 0
    dfs(start, [], visited)

    # Final progress print to indicate if max_paths was exceeded
    if print_progress:
        if path_counter >= max_paths:
            status = "max_paths exceeded"
        else:
            status = "complete"
        print(f"\rPair {label} ({start} -> {end}){perimeter_message}paths found: {path_counter} ({status})", flush=True)

    return paths

def find_all_combinations(grid_obj, labels):
    def search(current_label_index, current_paths, visited_cells):
        if current_label_index == len(labels):
            # Check if all traversable cells are used
            if len(visited_cells) == grid_obj.total_traversable:
                valid_combinations.append(current_paths[:])
            return

        label = labels[current_label_index]
        pair = grid_obj.pairs_dict[label]
        start, end = pair['start'], pair['end']

        # Find all paths for the current label
        grid_obj.activate_pair(pair, 1)
        paths = find_paths(grid_obj, start, end, visited_cells, label=label)
        grid_obj.activate_pair(None)

        for path in paths:
            # Get path coordinates
            path_coords = path.get_path_coordinates(include_direction=False)

            # Check if path overlaps with already visited cells
            if any((x, y) in visited_cells for x, y in path_coords):
                continue

            # Mark cells as visited
            for x, y in path_coords:
                visited_cells.add((x, y))

            # Add path to current paths
            current_paths.append(path)

            # Recurse to the next label
            search(current_label_index + 1, current_paths, visited_cells)

            # Backtrack: remove path and unmark cells
            current_paths.pop()
            for x, y in set(path_coords):
                visited_cells.remove((x, y))

    valid_combinations = []
    search(0, [], set())
    return valid_combinations

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # Check if any argument starts with a '-'
        for arg in sys.argv[1:]:
            if arg.startswith('-') and not arg.startswith('--'):
                message += "\nIf an argument starts with a '-', please escape it with a '\\'."
                break
        self.print_usage(sys.stderr)
        self.exit(2, f"Error parsing arguments: {message}\n")

# Read in command line options
parser = CustomArgumentParser(description='Grid Path Finder')
parser.add_argument('-c', '--color', action='store_true', help="Enable colored output")
parser.add_argument('-g', '--grid', type=str, required=True, help="Grid definition string")
parser.add_argument('-m', '--max', type=int, default=50000, help="Maximum number of paths to find before stopping early (default: 50000, -1 for infinite)")
parser.add_argument('-v', '--verbose', action='count', default=0, help="Increase verbosity level")
args = parser.parse_args()

# Set globals
global max_paths, print_progress, verbosity, path_counter
print_progress = False
max_paths = args.max
verbosity = args.verbose

grid = Grid(args.grid)

if verbosity >= 1:
    print("Original Grid with Pairs Labeled:")
    grid.print(use_color=True)

if verbosity >= 2 and args.perimeter:
    print("Grid Perimeter Cell View:")
    grid.print_perimeter(args.perimeter)
    print(f"grid.total_traversable: {grid.total_traversable}")

# Store paths from each run
all_perimeter_paths = []
perimeter_path_labels = []
internal_path_labels = []

print("Searching for pairs that can be connected via grid perimeter:")
for label, pair in grid.pairs_dict.items():
    if verbosity >= 3:
        print(f"Label {label} Grid Perimeter Cell View:")
        grid.print_perimeter(label)

    path_counter = 0
    print_progress = True
    grid.activate_pair(pair, 1)
    paths = find_paths(grid, pair['start'], pair['end'], set(), perimeter_mode=True, label=label)
    grid.activate_pair(None)
    print_progress = False
    if paths and len(paths) > 0:
        perimeter_path_labels.append(label)
        all_perimeter_paths.append(paths)
    else:
        internal_path_labels.append(label)

# Sort all_paths by the length of each sublist
all_perimeter_paths.sort(key=len)

# Generate all combinations of perimeter paths
all_perimeter_combinations = list(itertools.product(*all_perimeter_paths))

# Output the lists of labels
if verbosity >= 2:
    print("Labels that can be connected along the perimeter:", perimeter_path_labels)
    print("Number of perimeter paths found per label       :")
    for label in perimeter_path_labels:
        # Find the corresponding paths list for the label
        for paths in all_perimeter_paths:
            if paths and paths[0].label == label:
                print(f"\t{label}: {len(paths)}")
    print("Labels that can only be connected internally    :", internal_path_labels)

# Define labels_to_solve as only the labels that had no perimeter path(s)
labels_to_solve = internal_path_labels

# NOTE: Assumes at least 1 perimeter path was found
# Process each combination of perimeter paths
for i, path_combination in enumerate(all_perimeter_combinations):
    print(f"\nProcessing perimeter path combination {i+1}/{len(all_perimeter_combinations)}:")
    for path in path_combination:
        # Pass list of internal_path_labels to change total number of traversible cells
        grid.activate_path(path, 0, len(internal_path_labels)) # Mark path as non-traversible
    grid.print_paths(path_combination, use_color=args.color, debug_level=verbosity)
    label_path_count = []
    for label in labels_to_solve:
        pair = grid.pairs_dict[label]
        start, end = pair['start'], pair['end']
        current_pair_info = f"Pair {label} ({start} -> {end}):"
        path_counter = 0

        # Activate the pair to make the start and end points traversable
        grid.activate_pair(pair, 1)

        print_progress = True
        print(current_pair_info, end=' ')
        paths = find_paths(grid, start, end, set(), perimeter_mode=False, label=label)
        print_progress = False

        if paths is None:
            label_path_count.append((max_paths, label))
        else:
            label_path_count.append((len(paths), label))

        # Deactivate the pair to restore the original grid state
        grid.activate_pair(None)

    # Sort labels by the number of possible paths
    label_path_count.sort()
    sorted_labels = [label for _, label in label_path_count]

    # Find all paths using the sorted labels
    #all_paths = find_all_paths(grid, sorted_labels, 0, set())
    all_paths = find_all_combinations(grid, sorted_labels)

    if all_paths:
        print("Solution found:")
        for paths in all_paths:
            grid.print_paths(paths + list(path_combination), use_color=args.color, debug_level=verbosity)
    else:
        print("No solution found that uses all traversable locations.")
    for path in path_combination:
        grid.activate_path(None)    # Restore path
