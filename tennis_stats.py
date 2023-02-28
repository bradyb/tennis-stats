import json

# TODO: Is it possible to calculate playerId from playerName?
class AusOpenUrlConstructor:
    """
    Class for constructing the URL used to access AusOpen stats.
    """
    def __init__(self, playerId, gender, round):
        self.playerId = playerId
        self.gender = gender
        self.round = round
    
    def getRoundId(self):
        roundId = self.playerId
        curRound = self.round
        while (curRound > 0):
            modulus = roundId % 2
            roundId = roundId // 2 + modulus
            curRound = curRound - 1
        return roundId

    def getUrl(self):
        urlBase = "https://prod-scores-api.ausopen.com/match-centre"

        if self.gender == "M":
            urlBase = urlBase + "/MS"
        elif self.gender == "F":
            urlBase = urlBase + "/WS"

        roundId = self.getRoundId()
        paddedRoundId = str(roundId).rjust(2, '0')
        return urlBase + str(self.round) + paddedRoundId

# TODO: Add verification.
# * URL actually contains results for that player.
# * Team is correct and not magically guessed.
class AusOpenStatsCalculator:
    """
    Class for calculating fantasy tennis stats for the Australian Open.
    """
    def __init__(self, round, playerId, gender, http):
        self.team = self.getTeam(round, playerId)
        self.statsObj = self.getStatsObject(playerId, gender, round, http)
    
    def getStatsObject(self, playerId, gender, round, http):
        matchUrl = AusOpenUrlConstructor(playerId=playerId,gender=gender,round=round).getUrl()

        resp = http.request("GET", matchUrl)
        if (resp.status != 200):
            print("Error fetching URL:", self.url)
        
        jsonResp = json.loads(resp.data.decode('utf-8'))

        if (jsonResp["match_state"] != "Complete"):
            print("This match is not completed!")

        numSets = len(jsonResp['stats']['key_stats'][0]['sets'])
        statsObj = jsonResp['stats']['key_stats'][0]['sets'][numSets - 1]
        assert (statsObj['set'] == "All")
        return statsObj

    def getTeam(self, round, playerId):
        while (round > 1):
            modulus = playerId % 2
            playerId = playerId // 2 + modulus
            round = round - 1
        return ('teamA' if (playerId % 2) == 1 else 'teamB')

    def getAces(self):
        for stat in self.statsObj['stats']:
            if stat['name'] == "Aces":
                return stat[self.team]['primary']
        return None
    
    def getDoubleFaults(self):
        for stat in self.statsObj['stats']:
            if stat['name'] == "Double faults":
                return stat[self.team]['primary']
        return None

    def getServe(self):
        numAces = self.getAces()
        assert(numAces is not None)
        numDoubleFaults = self.getDoubleFaults()
        assert(numDoubleFaults is not None)
        return 3 * (int(numAces) - int(numDoubleFaults))

    def getWinners(self):
        for stat in self.statsObj['stats']:
            if stat['name'] == "Winners":
                return stat[self.team]['primary']
        return -1

    def getUnforcedErrors(self):
        for stat in self.statsObj['stats']:
            if stat['name'] == "Unforced errors":
                return stat[self.team]['primary']
        return -1  

    def getPower(self):
        numWinners = int(self.getWinners())
        numUnforcedErrors = int(self.getUnforcedErrors())
        return 2 * numWinners - numUnforcedErrors

    def getReturns(self):
        for stat in self.statsObj['stats']:
            if stat['name'] == "Receiving points won":
                return stat[self.team]['primary']
        return -1

    def getDefense(self):
        for stat in self.statsObj['stats']:
            if stat['name'] == "Win 2nd serve":
                return stat[self.team]['primary']
        return -1

    def getMind(self):
        for stat in self.statsObj['stats']:
            if stat['name'] == "Break points won":
                otherTeam = 'teamB' if self.team == 'teamA' else 'teamA'
                numBpWon = int(stat[self.team]['secondary'].split("/")[0])
                numBpFaced = int(stat[otherTeam]['secondary'].split("/")[1])
                numBroken = int(stat[otherTeam]['secondary'].split("/")[0])
                numBpSaved = numBpFaced - numBroken
                return 5 * (numBpWon + numBpSaved) - 3 * numBroken
        return -1
    
    def getStat(self, stat):
        if (stat == "Serve"):
            return self.getServe()
        elif (stat == "Power"):
            return self.getPower()
        elif (stat == "Return"):
            return self.getReturns()
        elif (stat == "Defense"):
            return self.getDefense()
        elif (stat == "Mind"):
            return self.getMind()
        else:
            print("Invalid stat was passed!")
            return 0