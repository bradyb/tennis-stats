import certifi
import csv
import urllib3

from tennis_stats import getStat

http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)

with open('input.csv', newline='') as csvfile:
    fileReader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in fileReader:
        playerName = row[0]
        gender = row[1]
        playerId = int(row[2])
        stat = row[3]
        round = int(row[4])
        getStat(playerName, playerId, round, gender, stat, http)
