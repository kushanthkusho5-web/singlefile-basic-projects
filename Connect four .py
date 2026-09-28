#!/usr/bin/env python3
"""
CONNECT FOUR - Challenge the Machine
====================================
Drop discs into a 7x6 grid and connect four in a row - across, up/down or
diagonally - before your opponent does.

Run it with:   python3 connect_four.py      (on Windows: python connect_four.py)
Only the Python standard library is used, so there is nothing to install.

Features
--------
* Play vs the computer (Easy / Medium / Hard) or with a friend on one keyboard.
* The computer uses MINIMAX with ALPHA-BETA PRUNING - a classic game-AI idea.
* Choose to go first (X) or second (O).
* Hint (h) and Undo (u) commands, discs that fall with a little animation,
  a highlighted winning line, and a session scoreboard.
"""

import os
import random
import sys
import time

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
AUTHOR = "Your Name"        # <-- put your name here; it shows on the credits screen

ROWS, COLS = 6, 7
EMPTY = " "
PIECE_COLORS = {"X": "1;91", "O": "1;93"}     # red and yellow
COLUMN_ORDER = [3, 2, 4, 1, 5, 0, 6]          # look at the centre first (smarter + faster)

# name: (search depth, chance of a random blunder)
LEVELS = {"1": ("Easy", 2, 0.30), "2": ("Medium", 4, 0.05), "3": ("Hard", 7, 0.0)}

USE_COLOR = False


# ---------------------------------------------------------------------------
# SMALL HELPERS
# ---------------------------------------------------------------------------
def detect_color():
    """Use colours only when the terminal can show them."""
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    if not sys.stdout.isatty():
        return False
    if os.name == "nt":
        os.system("")       # switches on colour support in Windows 10+ terminals
    return True


def paint(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def clear_screen():
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")
    else:
        print("\n" + "-" * 44)


def ask(prompt):
    return input(prompt).strip().lower()


def ask_yes_no(prompt):
    while True:
        answer = ask(prompt + " (y/n) ")
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print(" Please type y or n.")


def banner(text):
    print(paint("=" * 44, "1;96"))
    print(paint(text.center(44), "1;96"))
    print(paint("=" * 44, "1;96"))


# ---------------------------------------------------------------------------
# BOARD LOGIC  (the board is one flat list of 42 cells: index = row * 7 + column)
# ---------------------------------------------------------------------------
def make_windows():
    """Every possible line of four cells (there are 69), as lists of indices."""
    lines = []
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                end_r, end_c = r + 3 * dr, c + 3 * dc
                if 0 <= end_r < ROWS and 0 <= end_c < COLS:
                    lines.append(tuple((r + i * dr) * COLS + (c + i * dc) for i in range(4)))
    return lines


WINDOWS = make_windows()


def new_board():
    return [EMPTY] * (ROWS * COLS)


def open_columns(board):
    """Columns that still have room, centre first."""
    return [c for c in COLUMN_ORDER if board[c] == EMPTY]


def landing_row(board, col):
    """The row a disc dropped into `col` would land on (None if the column is full)."""
    for r in range(ROWS - 1, -1, -1):
        if board[r * COLS + col] == EMPTY:
            return r
    return None


def find_winner(board):
    """Returns (piece, winning_cells) or (None, ())."""
    for line in WINDOWS:
        piece = board[line[0]]
        if piece != EMPTY and piece == board[line[1]] == board[line[2]] == board[line[3]]:
            return piece, line
    return None, ()


def other(piece):
    return "O" if piece == "X" else "X"


# ---------------------------------------------------------------------------
# THE COMPUTER PLAYER
# ---------------------------------------------------------------------------
def evaluate(board, me):
    """Give the board a score: positive is good for `me`, negative is bad."""
    opp = other(me)
    score = 0
    centre = [board[r * COLS + 3] for r in range(ROWS)]
    score += 3 * centre.count(me)                   # centre discs are powerful
    for line in WINDOWS:
        cells = [board[i] for i in line]
        mine, theirs = cells.count(me), cells.count(opp)
        if mine and theirs:
            continue                                # a mixed line can't be completed
        if mine == 3:
            score += 5
        elif mine == 2:
            score += 2
        elif theirs == 3:
            score -= 6                              # danger: block this!
        elif theirs == 2:
            score -= 1
    return score


def minimax(board, depth, alpha, beta, my_turn, me):
    """Look `depth` moves ahead and return the best score `me` can force.

    Alpha-beta pruning skips branches that cannot change the result.
    """
    winner, _ = find_winner(board)
    if winner == me:
        return 1000000 + depth              # winning sooner is better
    if winner:
        return -1000000 - depth
    columns = open_columns(board)
    if not columns:
        return 0                            # draw
    if depth == 0:
        return evaluate(board, me)

    piece = me if my_turn else other(me)
    best = -10**9 if my_turn else 10**9
    for col in columns:
        idx = landing_row(board, col) * COLS + col
        board[idx] = piece
        value = minimax(board, depth - 1, alpha, beta, not my_turn, me)
        board[idx] = EMPTY
        if my_turn:
            best = max(best, value)
            alpha = max(alpha, best)
        else:
            best = min(best, value)
            beta = min(beta, best)
        if alpha >= beta:
            break
    return best


def best_move(board, me, depth):
    """Pick the column with the best minimax score (ties are broken randomly)."""
    scored = []
    for col in open_columns(board):
        idx = landing_row(board, col) * COLS + col
        board[idx] = me
        value = minimax(board, depth - 1, -10**9, 10**9, False, me)
        board[idx] = EMPTY
        scored.append((value, col))
    top = max(value for value, _ in scored)
    return random.choice([col for value, col in scored if value == top])


def computer_move(board, me, level):
    _, depth, blunder_chance = LEVELS[level]
    if random.random() < blunder_chance:
        return random.choice(open_columns(board))       # a "human" mistake
    return best_move(board, me, depth)


# ---------------------------------------------------------------------------
# DRAWING
# ---------------------------------------------------------------------------
def render(board, win_cells=()):
    lines = ["  " + "   ".join(str(c + 1) for c in range(COLS))]
    border = "+" + "---+" * COLS
    lines.append(border)
    for r in range(ROWS):
        row = "|"
        for c in range(COLS):
            idx = r * COLS + c
            piece = board[idx]
            shown = paint(piece, PIECE_COLORS[piece]) if piece != EMPTY else " "
            row += f"[{shown}]|" if idx in win_cells else f" {shown} |"
        lines.append(row)
        lines.append(border)
    return "\n".join(lines)


def draw(board, header, lines=(), win_cells=()):
    clear_screen()
    banner("CONNECT FOUR")
    print(f" {header}\n")
    print(render(board, win_cells))
    print()
    for line in lines:
        print(" " + line)


def drop_animation(board, col, row, piece, header):
    """Let the disc fall through the column (only in a real terminal)."""
    if not sys.stdout.isatty():
        return
    for r in range(row):
        frame = board[:]
        frame[r * COLS + col] = piece
        draw(frame, header)
        time.sleep(0.05)


def show_help():
    clear_screen()
    banner("HOW TO PLAY")
    print("""
 GOAL   Connect four of your discs in a row - horizontally, vertically
        or diagonally - before your opponent does.

 PLAY   Type a column number (1-7) to drop your disc.
        The disc falls to the lowest free spot.

 KEYS   1-7    drop a disc
        h      hint: the computer suggests a column
        u      undo your last move
        color  turn colours on/off if the screen looks strange
        q      quit the game

 TIPS   The centre column is the strongest. Watch for diagonals, and
        try to make two threats at once so the computer can't block both!
""")
    ask(" Press Enter to continue...")


def show_credits():
    clear_screen()
    banner("CREDITS")
    print(f"""
 Game design & code  : {AUTHOR}
 Built with          : Python 3 (standard library only)
 AI idea             : Minimax search with alpha-beta pruning
 Original repository : singlefile-basic-projects

 Thanks for playing!
""")
    ask(" Press Enter to go back...")


# ---------------------------------------------------------------------------
# PLAYING ONE MATCH
# ---------------------------------------------------------------------------
def play_match(stats, vs_computer, level="2", human="X"):
    """Play one game. `human` is the piece you control against the computer."""
    global USE_COLOR
    board = new_board()
    history = []                    # indices of every disc placed, oldest first
    turn = "X"                      # X always moves first
    notes = []

    def name_of(piece):
        if vs_computer:
            return "You" if piece == human else "Computer"
        return "Player 1" if piece == "X" else "Player 2"

    title = (f"Vs Computer ({LEVELS[level][0]})" if vs_computer else "Two players")

    while True:
        header = f"{title} | X: {name_of('X')}  O: {name_of('O')}"
        controls = "Type 1-7 to drop | h hint | u undo | color | q quit"
        who = paint(turn, PIECE_COLORS[turn])
        draw(board, header, notes + ["", f"{name_of(turn)} ({who}) to move.  {controls}"])
        notes = []

        if vs_computer and turn != human:
            col = computer_move(board, turn, level)
            notes.append(f"Computer dropped a disc in column {col + 1}.")
        else:
            command = ask(" Your move > ")
            if command in ("q", "quit"):
                if ask_yes_no(" Quit this game?"):
                    return
                continue
            if command in ("h", "hint"):
                col = best_move(board, turn, 5)
                notes.append(f"Hint: column {col + 1} looks strong.")
                continue
            if command in ("u", "undo"):
                steps = 2 if vs_computer else 1
                if len(history) < steps:
                    notes.append("Nothing to undo yet.")
                else:
                    for _ in range(steps):
                        board[history.pop()] = EMPTY
                    if not vs_computer:
                        turn = other(turn)
                    notes.append("Move undone.")
                continue
            if command == "color":
                USE_COLOR = not USE_COLOR
                notes.append("Colours are now " + ("ON." if USE_COLOR else "OFF."))
                continue
            if not command.isdigit() or not 1 <= int(command) <= COLS:
                notes.append(f"Please type a column number from 1 to {COLS}.")
                continue
            col = int(command) - 1
            if landing_row(board, col) is None:
                notes.append(f"Column {col + 1} is full - pick another one.")
                continue

        row = landing_row(board, col)
        drop_animation(board, col, row, turn, header)
        board[row * COLS + col] = turn
        history.append(row * COLS + col)

        winner, cells = find_winner(board)
        if winner:
            result = f"{name_of(winner)} ({winner}) connected four!"
            stats[name_of(winner)] = stats.get(name_of(winner), 0) + 1
        elif not open_columns(board):
            winner, cells = None, ()
            result = "The board is full - it's a draw!"
            stats["Draws"] += 1
        else:
            turn = other(turn)
            continue

        draw(board, header, [paint(result, "1;92"), f"Moves played: {len(history)}"], cells)
        ask("\n Press Enter to return to the menu...")
        return


# ---------------------------------------------------------------------------
# MENU
# ---------------------------------------------------------------------------
def choose(prompt, options):
    """Show numbered options; returns the chosen key or None for 'back'."""
    while True:
        print(f"\n {prompt}")
        for key, label in options.items():
            print(f"   {key}) {label}")
        print("   b) Back")
        choice = ask(" > ")
        if choice in options:
            return choice
        if choice in ("b", "back"):
            return None
        print(" Please pick one of the listed options.")


def scoreboard(stats):
    return (f"You {stats.get('You', 0)}  |  Computer {stats.get('Computer', 0)}  |  "
            f"P1 {stats.get('Player 1', 0)}  |  P2 {stats.get('Player 2', 0)}  |  "
            f"Draws {stats['Draws']}")


def main():
    global USE_COLOR
    USE_COLOR = detect_color()
    stats = {"Draws": 0}
    try:
        while True:
            clear_screen()
            banner("CONNECT FOUR")
            print(f"\n Scoreboard: {scoreboard(stats)}\n")
            print("   1) Play vs the computer")
            print("   2) Two players")
            print("   3) How to play")
            print("   4) Credits")
            print("   5) Quit")
            pick = ask("\n > ")

            if pick == "1":
                level = choose("Choose a level:", {k: v[0] for k, v in LEVELS.items()})
                if level is None:
                    continue
                side = choose("Which side?", {"1": "X - you move first", "2": "O - computer moves first"})
                if side is None:
                    continue
                play_match(stats, True, level, "X" if side == "1" else "O")
            elif pick == "2":
                play_match(stats, False)
            elif pick == "3":
                show_help()
            elif pick == "4":
                show_credits()
            elif pick in ("5", "q", "quit", "exit"):
                break
    except (KeyboardInterrupt, EOFError):
        pass
    print("\n Thanks for playing Connect Four. Goodbye!")


if __name__ == "__main__":
    main()3
