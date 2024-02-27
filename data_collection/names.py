import requests
import json

ALL_PLAYERS_URL = "https://search.d3.nhle.com/api/v1/search/player?culture=en-us&limit=3000&q=%2A&active=true"

def get_all_player_names():
    r = requests.get(ALL_PLAYERS_URL).json()

    all_players = {}
    for player in r:
        lastSeason = player.get('lastSeasonId', None)
        playerId = player.get('playerId', None)
        playerName = player.get('name', None)
        playerPosition = player.get('positionCode', None)
        playerKey = playerName.split(' ')[-1][0]

        if None not in [lastSeason, playerId, playerName, playerPosition]:
            if not all_players.get(playerKey, None):
                all_players[playerKey] = []
            
            all_players[playerKey].append({'playerName': playerName, 'playerId': playerId, 'playerPosition': playerPosition})
    
    return all_players

all_names = get_all_player_names()
for key in all_names:
    with open(f'collected_data/player_names/player_names_{key}', 'w') as f:
        json.dump(sorted(all_names[key], key = lambda x: x['playerName'].split(' ')[-1]), f) 
