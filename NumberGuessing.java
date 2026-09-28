import java.util.Random;
import java.util.Scanner;

public class NumberGuessing {
    private static final Scanner scanner = new Scanner(System.in);
    private static final Random random = new Random();

    public static void main(String[] args) {
        int wins = 0;
        int totalPoints = 0;
        boolean playAgain = true;

        System.out.println("=== Number Guessing Game ===");
        System.out.println("Guess the secret number before your attempts run out.");

        while (playAgain) {
            int maximum = chooseDifficulty();
            int attempts = chooseAttempts(maximum);
            int secretNumber = random.nextInt(maximum) + 1;
            boolean won = false;

            System.out.printf("I picked a number from 1 to %d. You have %d attempts.%n", maximum, attempts);

            for (int attempt = 1; attempt <= attempts; attempt++) {
                int guess = readNumber("Attempt " + attempt + ": ", 1, maximum);

                if (guess == secretNumber) {
                    int points = attempts - attempt + 1;
                    wins++;
                    totalPoints += points;
                    System.out.printf("Correct! You earned %d point%s.%n", points, points == 1 ? "" : "s");
                    won = true;
                    break;
                }

                if (guess < secretNumber) {
                    System.out.println("Too low.");
                } else {
                    System.out.println("Too high.");
                }
            }

            if (!won) {
                System.out.println("Out of attempts. The number was " + secretNumber + ".");
            }

            System.out.printf("Score - Wins: %d | Points: %d%n", wins, totalPoints);
            playAgain = readYesOrNo("Play again? (y/n): ");
        }

        System.out.println("Thanks for playing!");
    }

    private static int chooseDifficulty() {
        while (true) {
            System.out.print("Choose difficulty: 1) Easy  2) Medium  3) Hard: ");
            String choice = scanner.nextLine().trim();
            if (choice.equals("1")) return 50;
            if (choice.equals("2")) return 100;
            if (choice.equals("3")) return 200;
            System.out.println("Please choose 1, 2, or 3.");
        }
    }

    private static int chooseAttempts(int maximum) {
        if (maximum == 50) return 8;
        if (maximum == 100) return 7;
        return 6;
    }

    private static int readNumber(String prompt, int minimum, int maximum) {
        while (true) {
            System.out.print(prompt);
            try {
                int number = Integer.parseInt(scanner.nextLine().trim());
                if (number >= minimum && number <= maximum) return number;
            } catch (NumberFormatException exception) {
            }
            System.out.printf("Enter a whole number from %d to %d.%n", minimum, maximum);
        }
    }

    private static boolean readYesOrNo(String prompt) {
        while (true) {
            System.out.print(prompt);
            String answer = scanner.nextLine().trim().toLowerCase();
            if (answer.equals("y") || answer.equals("yes")) return true;
            if (answer.equals("n") || answer.equals("no")) return false;
            System.out.println("Please answer y or n.");
        }
    }
}
