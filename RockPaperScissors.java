import java.util.Random;
import java.util.Scanner;

public class RockPaperScissors {
    private static final Scanner scanner = new Scanner(System.in);
    private static final Random random = new Random();
    private static final String[] CHOICES = {"rock", "paper", "scissors"};

    public static void main(String[] args) {
        int playerWins = 0;
        int computerWins = 0;
        int draws = 0;
        boolean playAgain = true;

        System.out.println("=== Rock-Paper-Scissors ===");

        while (playAgain) {
            String playerChoice = readChoice();
            String computerChoice = CHOICES[random.nextInt(CHOICES.length)];
            System.out.println("Computer chose: " + computerChoice);

            int result = compareChoices(playerChoice, computerChoice);
            if (result > 0) {
                playerWins++;
                System.out.println("You win this round!");
            } else if (result < 0) {
                computerWins++;
                System.out.println("Computer wins this round!");
            } else {
                draws++;
                System.out.println("This round is a draw.");
            }

            System.out.printf("Score - You: %d | Computer: %d | Draws: %d%n", playerWins, computerWins, draws);
            playAgain = readYesOrNo("Play again? (y/n): ");
        }

        System.out.println("Thanks for playing!");
    }

    private static String readChoice() {
        while (true) {
            System.out.print("Choose rock, paper, or scissors: ");
            String choice = scanner.nextLine().trim().toLowerCase();
            if (choice.equals("rock") || choice.equals("paper") || choice.equals("scissors")) {
                return choice;
            }
            System.out.println("Please enter rock, paper, or scissors.");
        }
    }

    private static int compareChoices(String playerChoice, String computerChoice) {
        if (playerChoice.equals(computerChoice)) return 0;
        if ((playerChoice.equals("rock") && computerChoice.equals("scissors"))
                || (playerChoice.equals("paper") && computerChoice.equals("rock"))
                || (playerChoice.equals("scissors") && computerChoice.equals("paper"))) {
            return 1;
        }
        return -1;
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
