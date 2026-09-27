import random


def play_round():
    secret_number = random.randint(1, 100)
    guesses_left = 7

    print("\nI'm thinking of a number from 1 to 100.")
    print(f"You have {guesses_left} guesses. Type 'q' to quit this round.")

    while guesses_left > 0:
        answer = input(f"\nGuess ({guesses_left} left): ").strip().lower()

        if answer == "q":
            print(f"The number was {secret_number}.")
            return

        try:
            guess = int(answer)
        except ValueError:
            print("Enter a whole number from 1 to 100, or 'q' to quit.")
            continue

        if not 1 <= guess <= 100:
            print("Your guess must be between 1 and 100.")
            continue

        guesses_left -= 1

        if guess == secret_number:
            print(f"You got it! The number was {secret_number}.")
            return
        if guess < secret_number:
            print("Too low!")
        else:
            print("Too high!")

    print(f"Out of guesses! The number was {secret_number}.")


def main():
    print("=== GUESS THE NUMBER ===")

    while True:
        play_round()
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()