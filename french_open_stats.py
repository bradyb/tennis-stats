import json
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
    def __init__(self, round, playerId, gender):
        self.team = self.getTeam(round, playerId)
        self.displayUrl = FrenchOpenUrlConstructor(playerId=playerId,gender=gender,round=round).getUrl()
        self.soup = self.getSoup(playerId, gender, round)
        self.team = self.getTeam(round, playerId)
    
    def getDisplayUrl(self):
        return self.displayUrl
    
    def getSoup(self, playerId, gender, round):
        matchUrl = FrenchOpenUrlConstructor(playerId=playerId,gender=gender,round=round).getUrl()
        options = Options()
        options.add_argument("--window-size=1920,1200")
        options.add_argument('--headless=new')
        driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
        driver.get(matchUrl)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        match_stats = soup.find("div", id="RGMatchStats")
        soup = BeautifulSoup(str(match_stats), 'html.parser')

        return soup

    def getTeam(self, round, playerId):
        while (round > 1):
            modulus = playerId % 2
            playerId = playerId // 2 + modulus
            round = round - 1
        return ('player1' if (playerId % 2) == 1 else 'player2')

    def getSingleTextStatByName(self, name):
        statSections = self.soup.find_all(string=re.compile(name))
        statSection = statSections[0].parent.parent.parent.parent
       
        if self.team == "player1":
            statSelf = statSection.find("div", {"class": re.compile(r'.*p1Stats.*')})
            return statSelf.text

        if self.team == "player2":
            statSelf = statSection.find("div", {"class": re.compile(r'.*p2Stats.*')})
            return statSelf.text

    def getFractionStatByName(self, name):
        fraction_regex = r'\d+/\d+ '
        statSections = self.soup.find_all(string=re.compile(name))
        statSection = statSections[0].parent.parent.parent.parent
       
        if self.team == "player1":
            statSelf = statSection.find("div", {"class": re.compile(r'.*p1Stats.*')})
            statList = statSelf.find_all("div", {"class": re.compile(r'.*player1 non-speed')})
            for stat in statList:
                if (re.fullmatch(fraction_regex, stat.text)):
                    numerator, denominator = int(stat.text.split("/")[0]), int(stat.text.split("/")[1])
                    return int(round(100 * numerator/denominator))

        if self.team == "player2":
            statSelf = statSection.find("div", {"class": re.compile(r'.*p2Stats.*')})
            statList = statSelf.find_all("div", {"class": re.compile(r'.*player2 non-speed')})
            for stat in statList:
                if (re.fullmatch(fraction_regex, stat.text)):
                    numerator, denominator = int(stat.text.split("/")[0]), int(stat.text.split("/")[1])
                    return int(round(100 * numerator/denominator))

    def getAces(self):
        return self.getSingleTextStatByName("Aces")
    
    def getDoubleFaults(self):
        return self.getSingleTextStatByName("Double faults")

    def getServe(self):
        numAces = self.getAces()
        assert(numAces is not None)
        numDoubleFaults = self.getDoubleFaults()
        assert(numDoubleFaults is not None)
        return 3 * (int(numAces) - int(numDoubleFaults))

    def getWinners(self):
        return self.getSingleTextStatByName("Winners")

    def getUnforcedErrors(self):
        return self.getSingleTextStatByName("Unforced errors")

    def getPower(self):
        numWinners = int(self.getWinners())
        numUnforcedErrors = int(self.getUnforcedErrors())
        return 2 * numWinners - numUnforcedErrors

    def getReturns(self):
        return self.getFractionStatByName("Receiving points won")

    def getDefense(self):
        return self.getFractionStatByName("Win on 2nd serve")

    def getMind(self):
        statSections = self.soup.find_all(string=re.compile("Break points won"))
        statSection = statSections[0].parent.parent.parent.parent
        bpWon, bpSaved, numBroken = 0, 0, 0
        fraction_regex = r'\d+/\d+ '
       
        if self.team == "player1":
            # Get own player's break point stats.
            bpSection = statSection.find("div", {"class": re.compile(r'.*p1Stats.*')})
            bpSection = bpSection.find_all("div", {"class": re.compile(r'.*player1 non-speed')})
            for section in bpSection:
                if (re.fullmatch(fraction_regex, section.text)):
                    bpWon = int(section.text.split("/")[0])
                    break
            # Get opponent's break point stats.
            bpSection = statSection.find("div", {"class": re.compile(r'.*p2Stats.*')})
            bpSection = bpSection.find_all("div", {"class": re.compile(r'.*player2 non-speed')})
            for section in bpSection:
                if (re.fullmatch(fraction_regex, section.text)):
                    bpSaved = int(section.text.split("/")[1]) - int(section.text.split("/")[0])
                    numBroken = int(section.text.split("/")[0])
                    break

        if self.team == "player2":
            # Get own player's break point stats.
            bpSection = statSection.find("div", {"class": re.compile(r'.*p2Stats.*')})
            bpSection = bpSection.find_all("div", {"class": re.compile(r'.*player2 non-speed')})
            for section in bpSection:
                if (re.fullmatch(fraction_regex, section.text)):
                    bpWon = int(section.text.split("/")[0])
                    break
            # Get opponent's break point stats.
            bpSection = statSection.find("div", {"class": re.compile(r'.*p1Stats.*')})
            bpSection = bpSection.find_all("div", {"class": re.compile(r'.*player1 non-speed')})
            for section in bpSection:
                 if (re.fullmatch(fraction_regex, section.text)):
                    bpSaved = int(section.text.split("/")[1]) - int(section.text.split("/")[0])
                    numBroken = int(section.text.split("/")[0])
                    break
        
        return 5 * bpSaved + 5 * bpWon - 3 * numBroken
    
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