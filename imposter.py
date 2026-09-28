import random

CREW = ["Nova", "Juno", "Orion", "Zara", "Kite", "Luma"]


def normalize_name(name: str) -> str:
    return name.strip().title()


def choose_crew(player_name: str):
    available = [member for member in CREW if member != player_name]
    random.shuffle(available)
    crew = [player_name] + available[:4]
    return crew


def reveal_suspicion(suspicion, crew):
    highest = max(suspicion.values())
    candidates = [member for member in crew if suspicion[member] == highest]
    target = random.choice(candidates)
    return target, highest


def print_rules():
    print("=" * 60)
    print("IMPOSTER GAME".center(60))
    print("=" * 60)
    print("You are part of a small crew on a drifting space station.")
    print("One of the crew is secretly the impostor.")
    print("Complete tasks, scan for suspicious behavior, and catch the liar before the station loses power.")
    print("\nCommands:")
    print("  1) Complete a task")
    print("  2) Scan the room")
    print("  3) Accuse a crewmate")
    print("  4) Quit")
    print("=" * 60)


def main():
    print_rules()
    name = input("Enter your name: ").strip() or "Commander"
    player_name = normalize_name(name)
    crew = choose_crew(player_name)
    impostor = random.choice(crew)

    power = 100
    suspicion = {member: 0 for member in crew}
    rounds = 0
    won = False

    while rounds < 6 and power > 0:
        rounds += 1
        print(f"\n--- Round {rounds} ---")
        print(f"Station power: {power}%")
        print("Crew:", ", ".join(crew))

        if random.random() < 0.7:
            sabotage_target = random.choice([member for member in crew if member != impostor])
            suspicion[sabotage_target] += 1
            power -= 12
            print(f"A system glitch appears near {sabotage_target}. Suspicion rises.")

        choice = input("Choose an action (1-4): ").strip()

        if choice == "1":
            power += 10
            print("You completed a task and restored some power.")
        elif choice == "2":
            target, level = reveal_suspicion(suspicion, crew)
            print(f"Your scan suggests {target} is the most suspicious right now (score: {level}).")
        elif choice == "3":
            accusations = ", ".join(crew)
            target = normalize_name(input(f"Who do you accuse? ({accusations}): "))
            if target not in crew:
                print("That name is not on the station roster.")
                continue
            if target == impostor:
                won = True
                print(f"\nYou caught the impostor: {impostor}!")
                print("The station survives the sabotage and the crew cheers your name.")
                break
            suspicion[target] += 2
            power -= 8
            print(f"{target} was not the impostor. The crew loses trust and the station drops further.")
        elif choice == "4":
            print("You abandoned the station before finding the impostor.")
            break
        else:
            print("Invalid choice. Try again.")
            continue

        if power <= 0:
            print("\nThe station's power is gone. The impostor wins.")
            break

        if rounds >= 6 and not won:
            print("\nThe rounds are over and the impostor escaped detection.")
            print(f"The hidden impostor was: {impostor}")

    if won:
        print("\nVictory! You saved the station.")
    elif power > 0 and rounds >= 6:
        print("\nYou ran out of time before catching the impostor.")

    print("\nThanks for playing!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame interrupted. The station remains in danger.")
