from typing import List
from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
import datetime
import aiohttp
import asyncio
import random
import json
import time
import re

@dataclass
class ContractInfo:
    name: str
    link: str

BASE_CAPFRIENDLY_BROWSE_URL = 'https://www.capfriendly.com/browse/active?stats-season=2024&pg='
BASE_CAPFRIENDLY_URL = 'https://www.capfriendly.com'

# player_data_page = requests.get(BASE_CAPFRIENDLY_BROWSE_URL + '1', 'lxml').text
# parsed_player_page = BeautifulSoup(player_data_page, 'lxml')
# pagination = parsed_player_page.find("div", attrs={"class": "pagination"}).text
# last_page = re.findall(r"Page \d+ of (\d+)", pagination)[0]

# players = []
# player_table = parsed_player_page.find("table", attrs={"id": "brwt"}).find("tbody").findAll("tr")
# for player in player_table:
#     td = player.find('td')
#     player_name = re.findall(r"\d+\. (.*)", td.text)[0]
#     link = BASE_CAPFRIENDLY_URL + td.find('a')['href']
#     players.append({player_name: link})

# for i in range(2, int(last_page) + 1):
#     r = requests.get(BASE_CAPFRIENDLY_BROWSE_URL + f'{i}', 'lxml').text
#     parsed_r = BeautifulSoup(r, 'lxml')
#     r_table = parsed_r.find("table", attrs={"id": "brwt"}).find("tbody").findAll("tr")

#     for r in r_table:
#         td = r.find('td')
#         player_name = re.findall(r"\d+\. (.*)", td.text)[0]
#         link = BASE_CAPFRIENDLY_URL + td.find('a')['href']
#         players.append({player_name: link})

# with open('players_salaries.json', 'w') as f:
#     json.dump(players, f)

###
# Get contract list
###

def recursive_div(div):
    try:
        dict_total = {}
        if not div.find('div') and div.find('span'):
            key = div.find('span').text
            value = div.text.replace(key, '').replace(':', '').strip()
            dict_total.update({key : value})
        elif not div.find('span'):
            return {}
        else:
            for inner_div in div.findAll('div'):
                dict_total.update(recursive_div(inner_div))
        
        return dict_total
    except:
        return {}

async def request_players(name, url):
    async with aiohttp.ClientSession() as session:
        await asyncio.sleep(random.random())
        async with session.get(url) as resp:
            player_page = await resp.text()
            player_contracts = BeautifulSoup(player_page, 'lxml').findAll("div", {"class": "cf_playerContract__meta rel"})

            divs = []
            for c_div in player_contracts:
                div_dict = recursive_div(c_div)

                try:
                    length = int(re.findall(r"(\d+) ", div_dict.get("Length"))[0])
                except:
                    length = None

                try:
                    prev_year = datetime.datetime.strptime(div_dict.get("Signing Date"), "%b. %d, %Y").year
                except:
                    try:
                        prev_year = datetime.datetime.strptime(div_dict.get("Signing Date"), "%b %d, %Y").year
                    except:
                        prev_year = None
                
                try:
                    cap_pct = float(div_dict.get("Cap %")) / 100
                except:
                    cap_pct = None
                
                try:
                    end_ufa = 1 if div_dict.get("Expiry Status") == "UFA" else 0
                except:
                    end_ufa = None
                
                keep_dict = {
                    "Name": name,
                    "Length": length,
                    "PrevYear": prev_year,
                    "CapPct": cap_pct,
                    "EndIsUFA": end_ufa
                }
                divs.append(keep_dict)
            
            divs.sort(key=lambda x: x['PrevYear'])

            for idx in range(len(divs)):
                if idx == 0:
                    divs[idx]['StartIsUFA'] = 0
                else:
                    divs[idx]['StartIsUFA'] = divs[idx - 1]['EndIsUFA']

            return divs

start_time = time.time()
all_contracts = []
batch_number = 16
batch_size = 100

with open("players_salaries.json", 'r') as f:
    player_page_json = json.load(f)

async def main():
    global all_contracts

    urls = []
    for player in player_page_json[(batch_number - 1) * batch_size: batch_number * batch_size]:
        name = list(player.keys())[0]
        link = list(player.values())[0]
        urls.append((name, link))

    tasks = [request_players(l[0], l[1]) for l in urls]
    ac = await asyncio.gather(*tasks)
    for c in ac:
        all_contracts = all_contracts + c
        

asyncio.get_event_loop().run_until_complete(main())
print("--- %s seconds ---" % (time.time() - start_time))

with open(f'player_contracts_{batch_number}.json', 'w') as f:
    json.dump(all_contracts, f)
