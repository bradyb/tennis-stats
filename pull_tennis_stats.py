import certifi
import csv
import urllib3

from tennis_stats import AusOpenStatsCalculator

http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)

with open('input.csv', newline='') as csvfile:
    fileReader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in fileReader:
        playerName, gender, playerId, stat, round = row[0], row[1], int(row[2]), row[3], int(row[4])
        ts = AusOpenStatsCalculator(round, playerId, gender, http)
        print("Stat:", stat,  "for player:", playerName, "in round:", round, "is:", ts.getStat(stat))
