# Global debug variable
DEBUG = False

class Path:
    def __init__(self, label, start, end, directions=None):
        self.label = label
        self.start = start
        self.end = end
        self.directions = directions if directions is not None else []
        
        # Call the print function if debug mode is enabled
        if DEBUG:
            self.print()

    def get_path_coordinates(self, include_direction=True):
        x, y = self.start
        path_coordinates = []
        for direction in self.directions:
            if include_direction:
                path_coordinates.append((x, y, direction))
            else:
                path_coordinates.append((x, y))
            if direction == '^':
                x -= 1
            elif direction == 'v':
                x += 1
            elif direction == '<':
                y -= 1
            elif direction == '>':
                y += 1
        return path_coordinates   

    def __repr__(self):
        return f"Path(label={self.label}, start={self.start}, end={self.end}, directions={self.directions})"

    def print(self):
        print(f"Path Object: Label={self.label}, Start={self.start}, End={self.end}, Directions={self.directions}")

class Grid:
    def __init__(self, grid_str):
        self.grid, self.pairs_dict, self.labels = self.parse_grid(grid_str)
        self.total_traversable = sum(cell == 1 for row in self.grid for cell in row) + len(self.pairs_dict) * 2
        self.original_values = []  # Stack to store original values of pairs

    def parse_grid(self, grid_str):
        grid_str = grid_str.replace('\\', '')
        grid_str = grid_str.replace(';', '.')
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
                raise ValueError(f"Error: Label '{label}' does not have exactly two coordinates. Found positions: {positions}")

        start_end_pairs_dict = {label: {'start': positions[0], 'end': positions[1], 'label': label} for label, positions in pairs_dict.items()}
        return grid, start_end_pairs_dict, labels

    def is_valid_move(self, x, y, visited):
        rows, cols = len(self.grid), len(self.grid[0])
        return 0 <= x < rows and 0 <= y < cols and self.grid[x][y] >= 1 and (x, y) not in visited

    def activate_path(self, path_obj=None, value=0, solving_pair_count=-1):
        if solving_pair_count < 0:
            solving_pair_count=len(self.pairs_dict)
        if path_obj is None:
            # Restore original values from the stack
            if self.original_values:
                original_value = self.original_values.pop()
                for coords, val in original_value.items():
                    self.grid[coords[0]][coords[1]] = val
        else:
            path_coordinates = path_obj.get_path_coordinates()
            # Save original values to the stack
            original_value = {}
            x, y = path_obj.start
            original_value[(x, y)] = self.grid[x][y]
            self.grid[x][y] = value
            for x, y, direction in path_coordinates:
                if (x, y) not in original_value:
                    original_value[(x, y)] = self.grid[x][y]
                self.grid[x][y] = value
            self.original_values.append(original_value)
        self.total_traversable = sum(cell == 1 for row in self.grid for cell in row) + solving_pair_count * 2

    def activate_pair(self, pair=None, value=1):
        if pair is None:
            # Restore original values from the stack
            if self.original_values:
                original_value = self.original_values.pop()
                for coords, val in original_value.items():
                    self.grid[coords[0]][coords[1]] = val
        else:
            start, end = pair['start'], pair['end']
            # Save original values to the stack
            original_value = {}
            if start not in original_value:
                original_value[start] = self.grid[start[0]][start[1]]
            if end not in original_value:
                original_value[end] = self.grid[end[0]][end[1]]
            self.original_values.append(original_value)
            # Set new values
            self.grid[start[0]][start[1]] = value
            self.grid[end[0]][end[1]] = value

    def is_perimeter(self, x, y, pair, debug=False):
        # Activate the pair at the beginning
        self.activate_pair(pair, 0)
        rows, cols = len(self.grid), len(self.grid[0])
        
        # Check if the cell is on the perimeter of the grid
        if x == 0 or x == rows - 1 or y == 0 or y == cols - 1:
            self.activate_pair(None)  # Deactivate the pair before returning
            return 1 if debug else True

        # Directions for 8 adjacent cells
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        # Check if the cell is adjacent to a non-traversable cell connected to the perimeter
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols and self.grid[nx][ny] == 0:
                # Perform a BFS/DFS to check if this non-traversable cell is connected to the perimeter
                if self.is_connected_to_perimeter(nx, ny):
                    self.activate_pair(None)  # Deactivate the pair before returning
                    return self.is_connected_to_perimeter(nx, ny, debug) if debug else True

        self.activate_pair(None)  # Deactivate the pair before returning
        return 0 if debug else False

    def is_connected_to_perimeter(self, x, y, debug=False):
        rows, cols = len(self.grid), len(self.grid[0])
        visited = set()
        stack = [(x, y)]
        
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            
            # Check if this cell is on the perimeter
            if cx == 0 or cx == rows - 1 or cy == 0 or cy == cols - 1:
                return 3 if debug else True

            # Directions for 4-connected cells (up, down, left, right)
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < rows and 0 <= ny < cols and self.grid[nx][ny] == 0 and (nx, ny) not in visited:
                    stack.append((nx, ny))
        
        return 4 if debug else False

    def print(self, use_color):
        grid_copy = [row[:] for row in self.grid]
        for label, pair in self.pairs_dict.items():
            sx, sy = pair['start']
            ex, ey = pair['end']
            grid_copy[sx][sy] = label
            grid_copy[ex][ey] = label

        for row in grid_copy:
            if use_color:
                print(' '.join(self.colorize(str(cell)) for cell in row))
            else:
                print(' '.join(str(cell) for cell in row))
        print()

    def colorize(self, cell):
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
        color_map = {self.labels[i]: colors[i % len(colors)] for i in range(len(self.labels))}
        if isinstance(cell, tuple):
            direction, label = cell
            if label in color_map:
                return f"{color_map[label]}{direction}{reset}"
            else:
                raise ValueError(f"Error: {label} not in color_map")
        else:
            if cell == '1' or cell == 1:
                return '_'
            elif cell == '0' or cell == 0:
                return '#'
            elif cell == '-1' or cell == -1:
                return '*'
            return f"{color_map.get(cell, '')}{cell}{reset}"

    def print_paths(self, paths, use_color, debug_level=0):
        grid_copy = [row[:] for row in self.grid]
        for path_obj in paths:
            if path_obj.directions is None:
                continue
            label = path_obj.label
            if debug_level >= 1:
                print(f"Debug: Printing path for label {label} from {path_obj.start} to {path_obj.end}")
            sx, sy = path_obj.start
            ex, ey = path_obj.end
            x, y = sx, sy
            for direction in path_obj.directions:
                if direction == '^':
                    x -= 1
                elif direction == 'v':
                    x += 1
                elif direction == '<':
                    y -= 1
                elif direction == '>':
                    y += 1
                if (x, y) != path_obj.start and (x, y) != path_obj.end:  # Check if (x, y) are any of the pairs' start or end coordinates
                    for other_label, other_pair in self.pairs_dict.items():
                        if (x, y) == other_pair['start'] or (x, y) == other_pair['end']:
                            print(f"Conflict: Label {label} attempting to write to coordinate ({x}, {y}) which is start/end of label {other_label}")
                grid_copy[x][y] = (direction, label)
            grid_copy[sx][sy] = label
            grid_copy[ex][ey] = label

        for row in grid_copy:
            if use_color:
                print(' '.join(self.colorize(cell) for cell in row))
            else:
                #print(' '.join('*' if cell == -1 else str(cell) for cell in row))
                print(' '.join('*' if cell == -1 else str(cell) if not isinstance(cell, tuple) else cell[0] for cell in row))
        print()

    def print_perimeter(self, label=None):
        if label is None or label not in self.pairs_dict:
            print(f"Error: Label '{label}' not found in pairs_dict.")
            return
        
        pair = self.pairs_dict[label]
        
        rows, cols = len(self.grid), len(self.grid[0])
        
        for x in range(rows):
            row_output = []
            for y in range(cols):
                row_output.append(str(int(self.is_perimeter(x, y, pair, debug=True))))
            print(' '.join(row_output))
        print()
