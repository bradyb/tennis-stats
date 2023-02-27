Tool for pulling Fantasy Tennis stats. It currently only works for the Australian Open; implementing for other slams is WIP. Usage instructions:

1. Clone this repository.
2. Modify the input.csv file to pull the stats you want. The format is csv. Each row has (playerName, playerGender, playerPositionInDraw, stat, round). playerPositionInDraw can be found by viewing the draw and seeing where the player appears in the Round 1 draw (i.e. top of the draw is position 1, bottom of the draw is position 128).
3. Run "python3 pull_tennis_stats.py" from the terminal; it will print each stat that was requested.

Future work:
*  Make this work for all Grand Slam tournaments.
*  Implement a better UI (either web server or something that'll directly read an Excel spreadsheet and populate stats in it).
