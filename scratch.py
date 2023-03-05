import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--window-size=1920,1200")
options.add_argument('--headless=new')

driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
driver.get("https://www.rolandgarros.com/en-us/matches/2022/SM001")
soup = BeautifulSoup(driver.page_source, 'html.parser')
match_stats = soup.find("div", id="RGMatchStats")
soup = BeautifulSoup(str(match_stats), 'html.parser')


scores_strings = soup.find_all(string=re.compile('First serve'))
aces_string = scores_strings[0].parent.parent.parent.parent
aces_bold_self = aces_string.find("div", {"class": "labelBold p1highlight player1 non-speed"})
aces_non_bold_self = aces_string.find("div", {"class": "label player1 non-speed"})
if (aces_bold_self is not None):
    print("DF Bold:", aces_bold_self.text)
if (aces_non_bold_self is not None):
    print("DF Non Bold:", aces_non_bold_self.text)

aces_bold_other = aces_string.find("div", {"class": "labelBold p2highlight player2 non-speed"})
aces_non_bold_other = aces_string.find("div", {"class": "label player2 non-speed"})
if (aces_bold_other is not None):
    print("DFOther Bold:", aces_bold_other.text)
if (aces_non_bold_other is not None):
    print("DFOther Non Bold:", aces_non_bold_other.text)
# print(scores_strings[0].parent.parent.parent.parent.find("div", {"class": "p1highlight player1 non-speed"}).text)
# print(match_stats)
# print(driver.page_source)
driver.quit()

# send a request to the URL
# url = 'https://www.rolandgarros.com/en-us/matches/2022/SM001'
# response = requests.get(url)

# # parse HTML content using BeautifulSoup
# soup = BeautifulSoup(response.content, 'html.parser')

# print(soup.prettify())

# # find the "Match Stats" section
# match_stats = soup.find('section', {'class': 'match-stats'})

# # find the "Aces" row and extract the value
# aces_row = match_stats.find('tr', {'class': 'aces'})
# nadal_aces = aces_row.find_all('td')[1].text.strip()

# # print the number of aces hit by Rafael Nadal
# print(f"Rafael Nadal hit {nadal_aces} aces in the match.")

# url = "http://www.gallimard-jeunesse.fr/searchjeunesse/advanced/(order)/author?catalog[0]=1&SearchAction=1"
# browser = webdriver.Firefox()
# browser.get(url)
# sleep(10)
# all_body_id_html =  browser.find_element_by_id('body') # you can also get all html





