# Dice Roller Game
# Roll the dice and try to beat the computer or hit the target score.

import random


def roll_dice():
    """Return a random value between 1 and 6."""
    return random.randint(1, 6)


def play_round():
    """Play one round of the dice game."""
    target = 20
    player_total = 0
    computer_total = 0

    print("\n=== Dice Roller Game ===")
    print(f"First to reach {target} points wins the game!")

    while player_total < target and computer_total < target:
        input("Press Enter to roll the dice... ")
        player_roll = roll_dice()
        computer_roll = roll_dice()

        player_total += player_roll
        computer_total += computer_roll

        print(f"You rolled: {player_roll} | Computer rolled: {computer_roll}")
        print(f"Current score: You {player_total} - {computer_total} Computer")

        if player_total >= target:
            print("\n🎉 You win the game!")
            return
        if computer_total >= target:
            print("\n💻 Computer wins the game!")
            return

        again = input("Roll again? (y/n): ").strip().lower()
        if again != "y":
            print("Thanks for playing!")
            return


def main():
    """Main menu loop for the dice game."""
    print("=== Dice Roller Game ===")

    while True:
        print("\nOptions:")
        print("1. Play")
        print("2. Exit")

        choice = input("\nEnter choice (1/2): ")

        if choice == "1":
            play_round()
        elif choice == "2":
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please choose 1 or 2.")


if __name__ == "__main__":
    main()
