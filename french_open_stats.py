import csv
import re
from bs4 import BeautifulSoup

def split_objects(s):
    objects = []
    reader = csv.reader([s], delimiter=',', quotechar='"', escapechar='\\')
    for row in reader:
        objects.append(row)
    return objects

# TODO: Is it possible to calculate playerId from playerName?
class FrenchOpenUrlConstructor:
    """
    Class for constructing the URL used to access FrenchOpen stats.
    """
    def __init__(self, playerId, gender, round):
        self.playerId = playerId
        self.gender = gender
        self.round = round

    def getMatchId(self):
        # round = 7 -> 001
        # round = 6 -> 002 (if playerId <= 64), 003 (playerId > 64)
        # ...
        # round = 1 -> 064 (if playerId = 1, 2), 065 (if playerId = 3, 4), ..., 127 (if playerId = 127, 128)
        return 2**(7 - self.round) + int((self.playerId - 1) / 2**self.round)

    def getUrl(self):
        urlBase = "https://www.rolandgarros.com/en-us/matches/2022"

        if self.gender == "M":
            urlBase = urlBase + "/SM"
        elif self.gender == "F":
            urlBase = urlBase + "/SD"

        matchId = self.getMatchId()
        paddedMatchId = str(matchId).rjust(3, '0')
        return urlBase + paddedMatchId

# TODO: Add verification.
# * URL actually contains results for that player.
# * Team is correct and not magically guessed.
class FrenchOpenStatsCalculator:
    """
    Class for calculating fantasy tennis stats for the Australian Open.
    """
    def __init__(self, round, playerId, gender, http):
        self.team = self.getTeam(round, playerId)
        self.displayUrl = FrenchOpenUrlConstructor(playerId=playerId,gender=gender,round=round).getUrl()
        self.soup = self.getMatchStats(playerId, gender, round, http)
        self.team = self.getTeam(round, playerId)
    
    def getDisplayUrl(self):
        return self.displayUrl
    
    def getMatchStats(self, playerId, gender, round, http):
        matchUrl = FrenchOpenUrlConstructor(playerId=playerId,gender=gender,round=round).getUrl()
        resp = http.request("GET", matchUrl)
        if (resp.status != 200):
            print("Error fetching URL:", matchUrl)

        html = resp.data.decode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all('script')

        # Get the script containing the match stats.
        statsScript = None
        for script in scripts:
            if (len(script.contents) > 0 and "window.__NUXT__" in script.contents[0]):
                statsScript = script.contents[0]
        
        self.variableMap = self.getJsVariableMap(statsScript)
        self.matchStats = self.getMatchStatisticsSection(statsScript)
        
    def getMatchStatisticsSection(self, statsScript):
        searchTerm = "matchStatistics:{"
        startIdx = statsScript.find(searchTerm)

        i = startIdx + len(searchTerm) - 1
        bracesCount = 0
        while (i < len(statsScript)):
            if statsScript[i] == "{":
                bracesCount = bracesCount + 1
            if statsScript[i] == "}":
                bracesCount = bracesCount - 1
            i = i + 1
            if bracesCount == 0:
                break

        return statsScript[startIdx:i]

    def getJsVariableMap(self, statsScript):
        searchTerm = "window.__NUXT__=(function"

        # Get a list of the function arguments.
        startIdx = statsScript.find(searchTerm)
        i = startIdx + len(searchTerm)
        while (i < len(statsScript) and statsScript[i] != ")"):
            i = i + 1
        varNames = statsScript[startIdx + len(searchTerm) + 1:i]
        varNameList = varNames.split(",")

        # Get a list of the argument values.
        startIdx = statsScript.find("}(")
        endIdx = statsScript.find("));")
        varValues = statsScript[startIdx + 2:endIdx]
        varValueList = split_objects(varValues)[0]

        assert(len(varNameList) == len(varValueList))

        # Construct map from variable name to value.
        returnMap = {}
        for i in range(len(varNameList)):
            returnMap[varNameList[i]] = varValueList[i]
        return returnMap

    def getTeam(self, round, playerId):
        while (round > 1):
            modulus = playerId % 2
            playerId = playerId // 2 + modulus
            round = round - 1
        return ('teamAValue' if (playerId % 2) == 1 else 'teamBValue')

    def getNumericalStatByName(self, name):
        searchTerm = name + ":{"
    
        statIdx = self.matchStats.find(searchTerm)
        statSection = self.matchStats[statIdx:]

        valueIdx = statSection.find(self.team)
        valueSection = statSection[valueIdx:]
        i = 0
        while (i < len(valueSection)):
            char = valueSection[i]
            if char in "},":
                break
            i = i + 1
        stat = valueSection[len(self.team)+1:i]
        try:
            int(stat.strip('"'))
            return int(stat.strip('"'))
        except:
            return int(self.variableMap[stat])


        return stat.strip('"')

    def getFractionalStatByName(self, name, getOpponentStat=False):
        team = self.team
        if getOpponentStat:
            if team == "teamAValue":
                team = "teamBValue"
            elif team == "teamBValue":
                team = "teamAValue"
        
        searchTerm = name + ":{"
    
        statIdx = self.matchStats.find(searchTerm)
        statSection = self.matchStats[statIdx:]

        valueIdx = statSection.find(team)
        valueSection = statSection[valueIdx:]
        i = 0
        while (i < len(valueSection)):
            char = valueSection[i]
            if char in "},":
                break
            i = i + 1
        stat = valueSection[len(team)+1:i]

        # Define the regular expression pattern to match the integers
        pattern = r'\d+'

        # Find all occurrences of the pattern in the string
        matches = re.findall(pattern, stat.strip('"'))
        integers = [int(match) for match in matches]

        if (len(integers) == 4):
            return integers[0], integers[2]
        else:
            stat = self.variableMap[stat]
            matches = re.findall(pattern, stat.strip('"'))
            integers = [int(match) for match in matches]

            if (len(integers) == 4):
                return integers[0], integers[2]

    def getAces(self):
        return self.getNumericalStatByName("aces")
    
    def getDoubleFaults(self):
        return self.getNumericalStatByName("doubleFaults")

    def getServe(self):
        numAces = self.getAces()
        assert(numAces is not None)
        numDoubleFaults = self.getDoubleFaults()
        assert(numDoubleFaults is not None)
        return 3 * (int(numAces) - int(numDoubleFaults))

    def getWinners(self):
        return self.getNumericalStatByName("winners")

    def getUnforcedErrors(self):
        return self.getNumericalStatByName("unforcedErrors")

    def getPower(self):
        numWinners = int(self.getWinners())
        numUnforcedErrors = int(self.getUnforcedErrors())
        return 2 * numWinners - numUnforcedErrors

    def getReturns(self):
        returnWon, returnPlayed = self.getFractionalStatByName("returnPoints")
        return round(100 * float(returnWon) / float(returnPlayed))

    def getDefense(self):
        pointsWon, pointsPlayed = self.getFractionalStatByName("winRateOnSecondServe")
        return round(100 * float(pointsWon) / float(pointsPlayed))

    def getMind(self):
        bpWon, _ = self.getFractionalStatByName("breakPoint")
        numTimesBroken, bpFaced = self.getFractionalStatByName("breakPoint", getOpponentStat=True)

        bpSaved = bpFaced - numTimesBroken
        
        return 5 * bpWon + 5 * bpSaved - 3 * numTimesBroken
    
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