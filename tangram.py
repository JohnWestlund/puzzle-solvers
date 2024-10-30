import argparse
import string
import sys

# ANSI escape codes for colors
COLORS = [
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

RESET_COLOR = "\033[0m"

def get_max_row_length(board_str):
    rows = board_str.split('.')
    max_length = 0

    for row in rows:
        if row.strip() == '':
            continue
        elements = row.split(',')
        row_length = 0
        for elem in elements:
            if elem.strip() == '0':
                row_length += 1
            else:
                try:
                    row_length += int(elem, 16)
                except ValueError:
                    raise ValueError(f"Invalid element '{elem}' in board string.")
        max_length = max(max_length, row_length)

    return max_length

def parse_board_or_piece(input_str, max_length):
    rows = input_str.split('.')
    bit_array = []

    for i, row in enumerate(rows):
        if row.strip() == '':
            continue
        bit_row = []
        elements = row.split(',')
        for elem in elements:
            if elem.strip() == '0':
                bit_row.append(0)
            else:
                try:
                    num = int(elem)
                except ValueError:
                    raise ValueError(f"Invalid element '{elem}' in input string.")
                if num < 0:
                    bit_row.extend([0] * abs(num))
                else:
                    bit_row.extend([1] * num)
        
        bit_row.extend([0] * (max_length * 2 - len(bit_row) + 1))
        
        bit_array.append(bit_row)

    return bit_array

def convert_to_1d_bitmap(bit_array):
    return [bit for row in bit_array for bit in row]

def count_piece_fits(board_bitmap, piece_bitmap, max_row_length, verbosity):
    board_len = len(board_bitmap)
    piece_len = len(piece_bitmap)
    count = 0

    for shift in range(board_len - piece_len + 1):
        # Shift the padded piece bitmap
        shifted_piece_bitmap = [0] * shift + piece_bitmap + [0] * (board_len - (piece_len + shift))
        
        # Perform bitwise AND operation
        bitwise_and_bitmap = [(board_bitmap[k] & shifted_piece_bitmap[k]) for k in range(board_len)]
        
        if verbosity >= 3:
            print(f"\nBoard Length:Piece Length & Shift: {board_len}:{piece_len} & {shift}")
            print("Padded Piece Bitmap:")
            print_1d_bitmap(shifted_piece_bitmap)
            print("Bitwise AND Bitmap:")
            print_1d_bitmap(bitwise_and_bitmap)
        
        if all((board_bitmap[k] & shifted_piece_bitmap[k]) == shifted_piece_bitmap[k] for k in range(board_len)):
            count += 1

    return count

def shift_board_bitmap(board_bitmap, max_row_length):
    board_len = len(board_bitmap)
    shift_amount = board_len - max_row_length
    shifted_board_bitmap = [0] * shift_amount + board_bitmap[:max_row_length]
    return shifted_board_bitmap

def print_bit_array(bit_array, piece_number=None, use_color=False, verbosity=0):
    # Calculate max_length based on the position of the furthest non-zero element in any row
    reset = RESET_COLOR if use_color else ""
    max_length = max((len(row) - next((i for i, x in enumerate(reversed(row)) if x != 0 and x != ' ' and x != reset + " "), len(row)) for row in bit_array))
    max_row = max(bit_array, key=len)
    if verbosity >= 3:
        print(f"\nLongest row: {max_length}\n{max_row}")
    
    if piece_number is not None:
        letter = string.ascii_letters[piece_number - 1]
        color = COLORS[piece_number % len(COLORS)] if use_color else ""
        reset = RESET_COLOR if use_color else ""
        print("+" + "-" * (max_length * 2) + "+")
        for row in bit_array:
            row_str = ' '.join(color + letter if x == 1 else reset + " " for x in row[:max_length]) + " "
            print("|" + row_str + reset + " " * (max_length * 2 - 1 - len(row_str)) + "|")
        print("+" + "-" * (max_length * 2) + "+")
    else:
        print("+" + "-" * (max_length * 2 + 1) + "+")
        for row in bit_array:
            if use_color:
                color = COLORS[0]
                row_str = ' ' + ' '.join((color + "#" + reset if x == 1 else "_" for x in row[:max_length]))
            else:
                row_str = ' ' + ' '.join(("#" if x == 1 else "_" for x in row[:max_length]))
            print("|" + row_str + " " + reset + " " * (max_length * 2 - 2 - len(row_str)) + "|")
        print("+" + "-" * (max_length * 2 + 1) + "+")

def print_1d_bitmap(bitmap):
    print(' '.join(map(str, bitmap)))

def subtract_bitmaps(board_bitmap, piece_bitmap):
    return [board_bitmap[i] - piece_bitmap[i] for i in range(len(board_bitmap))]

def is_all_zeros(bitmap):
    return all(bit == 0 for bit in bitmap)

def convert_1d_to_2d(bitmap, rows, cols):
    return [bitmap[i * cols:(i + 1) * cols] for i in range(rows)]

def place_piece_on_board(board_2d, piece_bitmap, shift, piece_number, max_row_length, use_color=False):
    letter = string.ascii_letters[piece_number - 1]
    color = COLORS[piece_number % len(COLORS)] if use_color else ""
    reset = RESET_COLOR if use_color else ""
    piece_len = len(piece_bitmap)
    board_len = len(board_2d) * len(board_2d[0])
    shifted_piece_bitmap = [0] * shift + piece_bitmap + [0] * (board_len - piece_len - shift)
    rows = len(board_2d)
    cols = len(board_2d[0])

    for i in range(rows):
        for j in range(cols):
            index = i * cols + j
            if index < len(shifted_piece_bitmap) and shifted_piece_bitmap[index] == 1:
                #board_2d[i][j] = color + letter + reset
                board_2d[i][j] = reset + color + letter

def solve_recursive(board_bitmap, pieces, max_row_length, solution, board_2d, verbosity, use_color=False):
    if is_all_zeros(board_bitmap):
        print("Solution found:")
        print_bit_array(board_2d, use_color=use_color, verbosity=args.v)
        return True

    if not pieces:
        return False

    piece_number, piece_bitmap = pieces[0]
    remaining_pieces = pieces[1:]

    board_len = len(board_bitmap)
    piece_len = len(piece_bitmap)

    for shift in range(board_len - piece_len + 1 + max_row_length):
        shifted_piece_bitmap = [0] * shift + piece_bitmap + [0] * (board_len - piece_len - shift)
        
        if all((board_bitmap[k] & shifted_piece_bitmap[k]) == shifted_piece_bitmap[k] for k in range(board_len)):
            new_board_bitmap = subtract_bitmaps(board_bitmap, shifted_piece_bitmap)
            new_board_2d = [row[:] for row in board_2d]  # Deep copy of the board
            place_piece_on_board(new_board_2d, piece_bitmap, shift, piece_number, max_row_length, use_color)
            new_solution = solution + [(piece_number, shift)]
            if solve_recursive(new_board_bitmap, remaining_pieces, max_length, new_solution, new_board_2d, verbosity, use_color):
                return True

    return False

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # Check if any argument starts with a '-'
        for arg in sys.argv[1:]:
            if arg.startswith('-') and not arg.startswith('--'):
                message += "\nIf an argument starts with a '-', please escape it with a '\\'."
                break
        self.print_usage(sys.stderr)
        self.exit(2, f"Error parsing arguments: {message}\n")

parser = CustomArgumentParser(description='Solve tangram style grid puzzles')
parser.add_argument('-b', '--board', type=str, required=True, help='Board definition string.')
parser.add_argument('-p', '--pieces', type=str, nargs='*', help='Piece definition strings.')
parser.add_argument('-v', action='count', default=0, help='Increase verbosity level. Up to -vvv.')
parser.add_argument('-s', '--solve', action='store_true', help='Check if the puzzle is solvable. Returns 1st solution, not all..')
parser.add_argument('-c', '--color', action='store_true', help='Enable color coding for the pieces.')

try:
    args = parser.parse_args()
except argparse.ArgumentError as e:
    print(f"Error parsing arguments: {e}")
    exit()

# Remove leading backslashes
board = args.board.replace('\\', '')
# Replace semicolons with commas
board = board.replace(';', '.')

try:
    max_length = get_max_row_length(board)
    board_array = parse_board_or_piece(board, max_length)
except ValueError as e:
    print(f"Error parsing board: {e}")
    exit()

board_bitmap = convert_to_1d_bitmap(board_array)

print("Board:")
print_bit_array(board_array, use_color=args.color)

if args.v >= 1:
    print("1D Board Bitmap:")
    print_1d_bitmap(board_bitmap)

piece_fits = []
total_piece_ones = 0
piece_arrays = []

if args.pieces:
    for i, piece in enumerate(args.pieces):
        # Remove leading backslashes
        piece = piece.replace('\\', '')
        # Replace semicolons with commas
        piece = piece.replace(';', '.')
        try:
            piece_array = parse_board_or_piece(piece, max_length)
            piece_arrays.append(piece_array)
        except ValueError as e:
        # Enhance the error message with additional information
            error_message = str(e)
            if any(part.startswith('-') for part in args.board.split(',')):
                error_message += " If an argument starts with a '-', please escape it with a '\\'."
            print(f"Error parsing piece {i+1}: {error_message}")
            continue

        piece_bitmap = convert_to_1d_bitmap(piece_array)
        fits = count_piece_fits(board_bitmap, piece_bitmap, max_length, args.v)
        piece_fits.append((i + 1, piece_bitmap, fits))
        total_piece_ones += sum(piece_bitmap)

# Sort pieces by the number of fits (ascending order)
piece_fits.sort(key=lambda x: x[2])

# Create a mapping from piece number to piece array
piece_array_map = {i + 1: piece_arrays[i] for i in range(len(piece_arrays))}

for piece_info in piece_fits:
    piece_number, piece_bitmap, fits = piece_info
    piece_array = piece_array_map[piece_number]
    print(f"\nPiece {piece_number}:")
    print_bit_array(piece_array, piece_number, use_color=args.color, verbosity=args.v)
    if args.v >= 1:
        print(f"1D Piece {piece_number} Bitmap:")
        print_1d_bitmap(piece_bitmap)
    print(f"Piece {piece_number} fits {fits} times in the board.")

if args.solve:
    total_board_ones = sum(board_bitmap)
    if total_board_ones != total_piece_ones:
        print(f"Error: The number of 1s in the board ({total_board_ones}) and pieces ({total_piece_ones}) are not equal.")
        exit()

    pieces_sorted = [(piece_number, piece_bitmap) for piece_number, piece_bitmap, fits in piece_fits]
    reset = RESET_COLOR + " " if args.color else " "
    board_2d = [[reset for _ in range(len(board_array[0]))] for _ in range(len(board_array))]
    if not solve_recursive(board_bitmap, pieces_sorted, max_length, [], board_2d, args.v, args.color):
        print("No solution found.")
