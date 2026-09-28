"""Break the computer's four-digit code before you run out of guesses."""

import random

CODE_LENGTH = 4
DIGITS = "123456"
MAX_GUESSES = 10


def score_guess(secret, guess):
    """Return the counts of correct digits and correct positions."""
    exact = sum(secret_digit == guess_digit for secret_digit, guess_digit in zip(secret, guess))
    misplaced = sum(digit in secret for digit in guess) - exact
    return exact, misplaced


def get_guess(input_func=input, output_func=print):
    """Read a four-digit guess with no repeated digits."""
    while True:
        guess = input_func("Enter four different digits (1-6): ").strip()
        if (
            len(guess) == CODE_LENGTH
            and all(digit in DIGITS for digit in guess)
            and len(set(guess)) == CODE_LENGTH
        ):
            return guess
        output_func("Use four different digits from 1 to 6.")


def run_game(seed=None, input_func=input, output_func=print):
    """Play one round and return whether the code was cracked."""
    rng = random.Random(seed)
    secret = "".join(rng.sample(DIGITS, CODE_LENGTH))

    output_func("\n=== Mastermind ===")
    output_func(f"Crack the {CODE_LENGTH}-digit code. Digits are 1-6, with no repeats.")
    output_func(f"You have {MAX_GUESSES} guesses.")

    for attempt in range(1, MAX_GUESSES + 1):
        guess = get_guess(input_func, output_func)
        if guess == secret:
            output_func(f"Code cracked in {attempt} guess(es)!")
            return True

        exact, misplaced = score_guess(secret, guess)
        output_func(f"Exact position: {exact} | Right digit, wrong position: {misplaced}")
        output_func(f"Guesses remaining: {MAX_GUESSES - attempt}")

    output_func(f"Out of guesses! The code was {secret}.")
    return False


def main():
    """Run the Mastermind menu."""
    print("=== Mastermind ===")

    while True:
        print("\nOptions:")
        print("1. Play")
        print("2. Exit")
        choice = input("\nEnter choice (1/2): ").strip()

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
            print("Invalid choice! Please choose 1 or 2.")


if __name__ == "__main__":
    main()