# Battleship
# Discover the hidden ships before your turns run out.

import random

BOARD_SIZE = 5
SHIP_COUNT = 4
MAX_TURNS = 12


def create_board():
    """Create a blank 5x5 board."""
    return [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def place_ships(rng):
    """Return a set of hidden ship coordinates."""
    ship_positions = set()

    while len(ship_positions) < SHIP_COUNT:
        row = rng.randint(0, BOARD_SIZE - 1)
        col = rng.randint(0, BOARD_SIZE - 1)
        ship_positions.add((row, col))

    return ship_positions


def display_board(guess_board):
    """Display the current known state of the board."""
    print("    1 2 3 4 5")
    for row_index, row in enumerate(guess_board):
        line = [str(row_index + 1).rjust(2)]
        line.extend(row)
        print(" ".join(line))
    print()


def reveal_board(ship_positions):
    """Show the final ship layout for the end-of-game display."""
    board = create_board()
    for row, col in ship_positions:
        board[row][col] = "S"
    display_board(board)


def run_game(seed=None, input_func=input, output_func=print):
    """Run one game of Battleship."""
    rng = random.Random(seed)
    ship_positions = place_ships(rng)
    guess_board = create_board()
    hit_count = 0
    turns_taken = 0

    output_func("\n=== Battleship ===")
    output_func("Sink all hidden ships before you run out of turns.")
    output_func("Enter row and column numbers (for example: 3 4)\n")

    while turns_taken < MAX_TURNS and hit_count < SHIP_COUNT:
        display_board(guess_board)
        raw_guess = input_func("Choose a target (row column): ")

        try:
            row_text, col_text = raw_guess.strip().split()
            row = int(row_text) - 1
            col = int(col_text) - 1
        except ValueError:
            output_func("Please enter two numbers, like '3 4'.")
            continue

        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            output_func("Coordinates must be between 1 and 5.")
            continue

        if guess_board[row][col] in ("X", "O"):
            output_func("You already guessed that spot. Try a new target.")
            continue

        turns_taken += 1

        if (row, col) in ship_positions:
            guess_board[row][col] = "X"
            hit_count += 1
            output_func("Direct hit!")
        else:
            guess_board[row][col] = "O"
            output_func("Miss!")

    display_board(guess_board)

    if hit_count == SHIP_COUNT:
        output_func(f"You won! You sank all {SHIP_COUNT} ships in {turns_taken} turns.")
    else:
        output_func("Game over! You ran out of turns.")
        output_func("The ships were hidden here:")
        reveal_board(ship_positions)

    return hit_count == SHIP_COUNT


def main():
    """Play a full Battleship session."""
    print("=== Battleship Game ===")

    while True:
        print("\nOptions:")
        print("1. Play Battleship")
        print("2. Exit")

        choice = input("\nEnter choice (1/2): ")

        if choice == "1":
            run_game()
            again = input("\nPlay again? (y/n): ").strip().lower()
            if again != "y":
                print("Thanks for playing!")
                break
        elif choice == "2":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
