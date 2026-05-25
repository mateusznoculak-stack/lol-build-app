from fastapi import FastAPI
import requests
import os
from collections import Counter

app = FastAPI()

API_KEY = os.getenv("RIOT_API_KEY")
REGION = "europe"
HEADERS = {"X-Riot-Token": API_KEY}

PRO_PLAYERS = [
    "puuid_1",
    "puuid_2"
]

def get_patch():
    return requests.get(
        "https://ddragon.leagueoflegends.com/api/versions.json"
    ).json()[0]

def get_matches(puuid):
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    return requests.get(url, headers=HEADERS).json()

def get_match(match_id):
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    return requests.get(url, headers=HEADERS).json()

@app.get("/build/{champion}")
def build(champion: str):
    patch = get_patch()
    data = []

    for puuid in PRO_PLAYERS:
        matches = get_matches(puuid)

        for m in matches[:10]:
            match = get_match(m)

            if patch not in match["info"]["gameVersion"]:
                continue

            for p in match["info"]["participants"]:
                if p["championName"].lower() == champion.lower():
                    data.append({
                        "role": p["teamPosition"],
                        "items": [
                            p["item0"], p["item1"], p["item2"],
                            p["item3"], p["item4"], p["item5"]
                        ],
                        "win": p["win"],
                        "keystone": p["perks"]["styles"][0]["selections"][0]["perk"]
                    })

    result = {}

    for role in set(d["role"] for d in data):
        role_data = [d for d in data if d["role"] == role]

        items = []
        for d in role_data:
            items.extend(d["items"])

        best_items = [i for i, _ in Counter(items).most_common(6)]
        winrate = sum(d["win"] for d in role_data) / len(role_data) * 100
        keystone = Counter(d["keystone"] for d in role_data).most_common(1)[0][0]

        result[role] = {
            "items": best_items,
            "winrate": round(winrate, 2),
            "keystone": keystone
        }

    return {"champion": champion, "patch": patch, "roles": result}
