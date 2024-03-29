import certifi
import csv
import urllib3

from australian_open_stats import AusOpenStatsCalculator
from french_open_stats import FrenchOpenStatsCalculator

http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)

# Usage:
# round is the round of the tournament (1-7)
# playerId is the position in the draw (for example, the 2022 Men's draw goes Djokovic=1, Nishioka=2, Molcan=3, Coria=4, ...)
# gender is M or F

with open('input.csv', newline='') as csvfile:
    fileReader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in fileReader:
        playerName, gender, playerId, stat, round = row[0], row[1], int(row[2]), row[3], int(row[4])
        ts = FrenchOpenStatsCalculator(round, playerId, gender, http)
        print("Stat:", stat,  "for player:", playerName, "in round:", round, "is:", ts.getStat(stat))
        print("Match stats URL is:", ts.getDisplayUrl(), "\n")
