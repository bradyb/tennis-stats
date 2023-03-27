import argparse
import glob

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r", "--round", help="round of the tournament to pull from", type=int
    )
    args = parser.parse_args()
    round = args.round
    teams = glob.glob("teams/*.team")
    # TODO: Read the teams from each of these files and update using the round.
    print("Getting stats for round: " + str(round))
    print("Here are the team files: ")
    print(teams)
