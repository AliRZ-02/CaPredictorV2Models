import asyncio
import aiohttp
import random
import json
import time
import os

async def get_player_stats(player):
    link = f'https://api-web.nhle.com/v1/player/{player.get("playerId")}/landing'
    async with aiohttp.ClientSession() as session:
        await asyncio.sleep(random.random())
        async with session.get(link) as resp:
            data = await resp.json()
            
            return {player.get("playerName"): int(data.get("birthDate")[:4])}

async def main():
    files = os.listdir("collected_data/player_names/")

    for initial_file in files:
        initial = initial_file[-6]
        stats = []

        with open(f'collected_data/player_names/{initial_file}', 'r') as f:
            names = json.load(f)
            tasks = [get_player_stats(player) for player in names]
            ac = await asyncio.gather(*tasks)
            for c in ac:
                stats.append(c)
        
        with open(f'collected_data/player_ages/player_ages_{initial}.json', 'w') as f:
            json.dump(stats, f)
        
start_time = time.time()
asyncio.get_event_loop().run_until_complete(main())
print("--- %s seconds ---" % (time.time() - start_time))
