import json
import os
import time
import boto3
import psycopg2
import urllib.request

def get_secrets():
    client = boto3.client("secretsmanager", region_name=os.environ["AWS_REGION_NAME"])
    response = client.get_secret_value(SecretId=os.environ["SECRET_ARN"])
    return json.loads(response["SecretString"])

def riot_get(url, api_key):
    req = urllib.request.Request(url, headers={
        "X-Riot-Token": api_key,
        "User-Agent": "Mozilla/5.0",
    })
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def get_challengers(api_key, region="na1"):
    url = f"https://{region}.api.riotgames.com/tft/league/v1/challenger?queue=RANKED_TFT"
    data = riot_get(url, api_key)
    return sorted(data["entries"], key=lambda x: x["leaguePoints"], reverse=True)[:20]

def get_match_ids(api_key, puuid, region="americas", count=5):
    url = f"https://{region}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?count={count}"
    return riot_get(url, api_key)

def get_match_detail(api_key, match_id, region="americas"):
    url = f"https://{region}.api.riotgames.com/tft/match/v1/matches/{match_id}"
    return riot_get(url, api_key)

def find_participant(match, puuid):
    for p in match["info"]["participants"]:
        if p["puuid"] == puuid:
            return p
    return None

def create_tables(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tft_leaderboard (
            rank          INTEGER,
            puuid         TEXT,
            riot_id       TEXT,
            league_points INTEGER,
            wins          INTEGER,
            losses        INTEGER,
            fetched_at    TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tft_match_participants (
            match_id   TEXT,
            puuid      TEXT,
            riot_id    TEXT,
            placement  INTEGER,
            fetched_at TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (match_id, puuid)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tft_match_traits (
            match_id   TEXT,
            puuid      TEXT,
            trait_name TEXT,
            num_units  INTEGER,
            tier       INTEGER,
            fetched_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tft_match_units (
            match_id     TEXT,
            puuid        TEXT,
            character_id TEXT,
            item_names   TEXT[],
            rarity       INTEGER,
            tier         INTEGER,
            fetched_at   TIMESTAMP DEFAULT NOW()
        )
    """)

def main(event, context):
    secrets = get_secrets()
    api_key = secrets["riot_api_key"]
    db_pass = secrets["db_password"]
    db_host = secrets["db_endpoint"].split(":")[0]
    db_name = secrets["db_name"]

    players = get_challengers(api_key)

    conn = psycopg2.connect(host=db_host, dbname=db_name, user="dbadmin", password=db_pass)
    cur = conn.cursor()
    create_tables(cur)

    cur.execute("DELETE FROM tft_leaderboard")
    for i, player in enumerate(players, 1):
        cur.execute("""
            INSERT INTO tft_leaderboard (rank, puuid, league_points, wins, losses)
            VALUES (%s, %s, %s, %s, %s)
        """, (i, player["puuid"], player["leaguePoints"], player["wins"], player["losses"]))

    # Dev key limit: 100 req/2min. Fetch match history for top 20 only.
    # Increase to 50 once you have a production key.
    seen_matches = set()
    for player in players[:20]:
        puuid = player["puuid"]
        time.sleep(1.5)
        match_ids = get_match_ids(api_key, puuid)

        for match_id in match_ids:
            if match_id in seen_matches:
                continue
            seen_matches.add(match_id)

            time.sleep(1.5)
            match = get_match_detail(api_key, match_id)
            participant = find_participant(match, puuid)
            if not participant:
                continue

            riot_id   = participant.get("riotIdGameName", "")
            placement = participant["placement"]

            cur.execute(
                "UPDATE tft_leaderboard SET riot_id = %s WHERE puuid = %s",
                (riot_id, puuid)
            )

            cur.execute("""
                INSERT INTO tft_match_participants (match_id, puuid, riot_id, placement)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (match_id, puuid) DO NOTHING
            """, (match_id, puuid, riot_id, placement))

            for trait in participant.get("traits", []):
                cur.execute("""
                    INSERT INTO tft_match_traits (match_id, puuid, trait_name, num_units, tier)
                    VALUES (%s, %s, %s, %s, %s)
                """, (match_id, puuid, trait["name"], trait.get("num_units", 0), trait.get("tier_current", 0)))

            for unit in participant.get("units", []):
                cur.execute("""
                    INSERT INTO tft_match_units (match_id, puuid, character_id, item_names, rarity, tier)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (match_id, puuid, unit["character_id"], unit.get("itemNames", []), unit.get("rarity", 0), unit.get("tier", 0)))

    conn.commit()
    cur.close()
    conn.close()

    return {"statusCode": 200, "body": f"Processed {len(players)} players, {len(seen_matches)} matches"}
