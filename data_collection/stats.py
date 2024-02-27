import asyncio
import aiohttp
import random
import json
import time
import os

def convertTimeToFloat(toi):
    mins = toi.split(':')[0]
    secs = toi.split(':')[1]

    return float(mins) + (float(secs) / 60)

def merge_goalie_season_results(season_data):
    data = []
    seen_seasons = {}
    toAdd = ["gamesPlayed", "gamesStarted", "wins", "losses", "otLosses", "shotsAgainst", "goalsAgainst", "shutouts", "timeOnIce"]
    
    for season in season_data:
        if season["gameTypeId"] != 2:
            continue
        
        if seen_seasons.get(season['season'], 0):
            seen_seasons[season['season']] = seen_seasons[season['season']] + 1
            original_data = data[-1]

            for key in toAdd:
                if key == "timeOnIce":
                    original_data[key] += convertTimeToFloat(season.get(key, "0:0"))
                else:
                    original_data[key] += int(season.get(key, 0))
            
            data[-1] = original_data
        else:
            seen_seasons[season['season']] = 1

            new_season = {}
            new_season['season'] = season['season']
            for key in toAdd:
                if key == "timeOnIce":
                    new_season[key] = convertTimeToFloat(season.get(key, "0:0"))
                else:
                    new_season[key] = int(season.get(key, 0))

            data.append(new_season)
    
    return data

def merge_season_results(season_data, position_type):
    if position_type == "G":
        return merge_goalie_season_results(season_data)
    
    data = []
    seen_seasons = {}
    toAdd = ["gamesPlayed", "goals", "assists", "plusMinus", "powerPlayGoals", "powerPlayPoints", "shorthandedGoals", "shorthandedPoints", "shots", "pim"]
    toAverage = ["faceoffWinningPctg", "avgToi"]
    
    for season in season_data:
        if season["gameTypeId"] != 2:
            continue

        if seen_seasons.get(season['season'], 0):
            seen_seasons[season['season']] = seen_seasons[season['season']] + 1
            original_data = data[-1]

            for key in toAdd:
                original_data[key] += int(season.get(key, 0))
            
            for key in toAverage:
                new_val = float(season.get(key, 0)) if key != "avgToi" else convertTimeToFloat(season[key])
                original_data[key] = (new_val + (original_data[key] * (seen_seasons.get(season['season']) - 1))) / seen_seasons.get(season['season'])
            
            data[-1] = original_data
        else:
            seen_seasons[season['season']] = 1

            new_season = {}
            new_season['season'] = season['season']
            for key in toAdd:
                new_season[key] = int(season.get(key, 0))
            
            for key in toAverage:
                new_season[key] = float(season.get(key, 0)) if key != "avgToi" else convertTimeToFloat(season.get(key, "0:0"))

            data.append(new_season)
    
    return data

async def get_player_stats(player):
    link = f'https://api-web.nhle.com/v1/player/{player.get("playerId")}/landing'
    async with aiohttp.ClientSession() as session:
        await asyncio.sleep(random.random())
        async with session.get(link) as resp:
            data = await resp.json()
            stats_to_store = []

            if data["position"] != "G":
                nhl_stats = merge_season_results([season for season in data['seasonTotals'] if season["leagueAbbrev"] == "NHL"], data["position"])

                for year in nhl_stats:
                    year_dict = {}

                    year_dict['season'] = int(str(year.get('season'))[-4:])
                    year_dict['position'] = player.get('playerPosition')
                    year_dict['gamesPlayed'] = year.get('gamesPlayed')
                    year_dict['PIM'] = year.get('pim')

                    if year.get('gamesPlayed') == 0:
                        continue

                    year_dict['G82'] = (year.get('goals') / year.get('gamesPlayed')) * 82
                    year_dict['A82'] = (year.get('assists') / year.get('gamesPlayed')) * 82
                    year_dict['PM82'] = (year.get('plusMinus') / year.get('gamesPlayed')) * 82
                    year_dict['PPG82'] = (year.get('powerPlayGoals') / year.get('gamesPlayed')) * 82
                    year_dict['PPA82'] = ((year.get('powerPlayPoints') - year.get('powerPlayGoals')) / year.get('gamesPlayed')) * 82
                    year_dict['SHG82'] = (year.get('shorthandedGoals') / year.get('gamesPlayed')) * 82
                    year_dict['SHA82'] = ((year.get('shorthandedPoints') - year.get('shorthandedGoals')) / year.get('gamesPlayed')) * 82

                    if year.get('shots') == 0:
                        year_dict['S%'] = 0
                    else:
                        year_dict['S%'] = year.get('goals') / year.get('shots')
                    
                    stats_to_store.append(year_dict)
            else:
                nhl_stats = merge_season_results([season for season in data['seasonTotals'] if season["leagueAbbrev"] == "NHL"], data["position"])

                for year in nhl_stats:
                    year_dict = {}

                    year_dict['season'] = int(str(year.get('season'))[-4:])
                    year_dict['position'] = player.get('playerPosition')
                    year_dict['gamesPlayed'] = year.get('gamesPlayed')
                    year_dict['GS'] = year.get('gamesStarted')
                    year_dict['W'] = year.get('wins')
                    year_dict['L'] = year.get('losses') + year.get('otLosses')
                    year_dict['SO'] = year.get('shutouts')

                    if year.get('shotsAgainst') == 0 or year.get('timeOnIce') == 0:
                        continue

                    year_dict['SV%'] = year.get('goalsAgainst') / year.get('shotsAgainst')
                    year_dict['GAA'] = year.get('goalsAgainst') / (year.get('timeOnIce') / 60)
                    
                    stats_to_store.append(year_dict)
            
            return {player.get("playerName"): stats_to_store}

async def main():
    files = os.listdir("collected_data/player_names/")

    for initial_file in files:
        initial = initial_file[-1]
        stats = []

        with open(f'collected_data/player_names/{initial_file}', 'r') as f:
            names = json.load(f)
            tasks = [get_player_stats(player) for player in names]
            ac = await asyncio.gather(*tasks)
            for c in ac:
                stats.append(c)
        
        with open(f'collected_data/player_stats/player_stats_{initial}', 'w') as f:
            json.dump(stats, f)
        
start_time = time.time()
asyncio.get_event_loop().run_until_complete(main())
print("--- %s seconds ---" % (time.time() - start_time))
