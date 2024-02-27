# Merge Contract JSON Data by Names to Yearly data in player_stats -> Loop contract by contract, if there are three years of data prior to the contract for that name, include the contract and use exponentially weighted moving average values for the stats. Then create JSON with all keys for stats and contract value based on that.
import json



def find_duplicates():
    duplicates = set()
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        seen_players = {}
        with open(f'collected_data/player_names/player_names_{letter}.json') as f:
            players = json.load(f)
            for player in players:
                player_name = player.get("playerName")
                if seen_players.get(player_name, None):
                    duplicates.add(player_name)
                else:
                    seen_players[player_name] = True
    
    return duplicates

def match_contracts(duplicates):
    gp = {year: 82 for year in range(2000, 2025)}
    gp[2005] = 0
    gp[2013] = 41
    gp[2021] = 56

    stats = {}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        letter_stats = {}
        with open(f'collected_data/player_stats/player_stats_{letter}.json') as f:
            players = json.load(f)
            for player in players:
                key = list(player.keys())[0]
                values = player[key]

                player_career_stats = {}
                if key not in duplicates:
                    for season in values:
                        if (season.get('position') != 'G' and season.get("gamesPlayed") >= (1 / 3) * gp[season.get("season")]) or (season.get('position') == 'G' and season.get("gamesPlayed") >= (1 / 5) * gp[season.get("season")]):
                            if season.get("season") == 2005:
                                continue

                            if season.get("SV%", None):
                                season['SV%'] = 1 - season['SV%']

                            toAdjust = ["gamesPlayed", "PIM", "GS", "W", "L", "SO"]

                            for adjustable in toAdjust:
                                if season.get(adjustable, None):
                                    season[adjustable] = (season[adjustable] / gp[season.get("season")]) * 82

                            player_career_stats[season.get("season")] = season
                    
                    letter_stats[key] = player_career_stats
        
        stats[letter] = letter_stats
    
    ages = {}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        letter_ages = {}
        with open(f'collected_data/player_ages/player_ages_{letter}.json') as f:
            players = json.load(f)
            for player in players:
                key = list(player.keys())[0]
                values = player[key]
                if key not in duplicates:
                    letter_ages[key] = values
        
        ages[letter] = letter_ages
    
    cleaned_contract_data = []
    data_missing = []
    for i in range(1, 17):
        with open(f'collected_data/player_contracts/player_contracts_{i}.json', 'r') as f:
            contracts = json.load(f)
            for contract in contracts:
                if contract.get("Name") in duplicates:
                    data_missing.append(contract)
                    continue

                initial = contract.get("Name").split(' ')[-1][0]
                if not stats.get(initial, None) or not stats[initial].get(contract.get("Name")) or not ages.get(initial, None) or not ages[initial].get(contract.get("Name")):
                    data_missing.append(contract)
                    continue

                career_stats = stats[initial][contract.get("Name")]
                age_stats = ages[initial][contract.get("Name")]

                prevYear = contract.get("PrevYear")
                if career_stats.get(prevYear, None) and career_stats.get(prevYear - 1, None) and career_stats.get(prevYear - 2, None):
                    if career_stats.get(prevYear)["position"] in ['C', 'L', 'R', 'D']:
                        statKeys = ["gamesPlayed", "PIM", "G82", "A82", "PM82", "PPG82", "PPA82", "SHG82", "SHA82", "S%"]
                    else:
                        statKeys = ["gamesPlayed", "GS", "W", "L", "SO", "SV%", "GAA"]

                    initial_stats = {}

                    for stat in statKeys:
                        initial_stats[stat] = ((5 / 9) * career_stats.get(prevYear, None)[stat]) + ((3 / 9) * career_stats.get(prevYear - 1, None)[stat]) + ((1 / 9) * career_stats.get(prevYear - 2, None)[stat])
                    
                    initial_stats["position"] = career_stats.get(prevYear)["position"]
                    initial_stats["Length"] = contract.get("Length")
                    initial_stats["Name"] = contract.get("Name")
                    initial_stats["CapPct"] = contract.get("CapPct")
                    initial_stats["EndIsUFA"] = contract.get("EndIsUFA")
                    initial_stats["StartIsUFA"] = contract.get("StartIsUFA")
                    initial_stats["Age"] = prevYear - age_stats

                    cleaned_contract_data.append(initial_stats)
                else:
                    data_missing.append(contract)
    return cleaned_contract_data, data_missing


dups = find_duplicates()
cleaned_contracts, missing_data = match_contracts(dups)
positions = {'Centers': ['C'], 'Wings': ['L', 'R'], 'Defencemen': ['D'], 'Goalies': ['G']}

for pos, types in positions.items():
    pos_contract_data = list(filter(lambda x: x['position'] in types, cleaned_contracts))
    with open(f'collected_data/player_cleaned_data/cleaned_contract_data_{pos}.json', 'w') as f:
        json.dump(pos_contract_data, f)

with open(f'collected_data/player_cleaned_data/missing_contracts.json', 'w') as f:
    json.dump(missing_data, f)