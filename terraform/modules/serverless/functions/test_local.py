import os
import io
import json
import unittest.mock as mock

os.environ["AWS_REGION_NAME"] = "us-west-2"
os.environ["SECRET_ARN"] = "mock"

# --- fake API responses ---

FAKE_CHALLENGERS = {
    "tier": "CHALLENGER",
    "queue": "RANKED_TFT",
    "entries": [
        {"puuid": "puuid-1", "leaguePoints": 1844, "wins": 208, "losses": 97,
         "rank": "I", "veteran": True, "inactive": False, "freshBlood": False, "hotStreak": False},
        {"puuid": "puuid-2", "leaguePoints": 1200, "wins": 150, "losses": 80,
         "rank": "I", "veteran": False, "inactive": False, "freshBlood": False, "hotStreak": False},
    ]
}

FAKE_MATCH_IDS = ["NA1_1234567890", "NA1_9876543210"]

FAKE_MATCH_DETAIL = {
    "metadata": {"match_id": "NA1_1234567890", "participants": ["puuid-1", "puuid-2"]},
    "info": {
        "participants": [
            {
                "puuid": "puuid-1",
                "riotIdGameName": "TestPlayer",
                "placement": 1,
                "traits": [
                    {"name": "TFT13_Trait_Rebel", "num_units": 3, "tier_current": 2}
                ],
                "units": [
                    {"character_id": "TFT13_Jinx", "itemNames": ["TFT_Item_Deathblade"], "rarity": 2, "tier": 2}
                ]
            }
        ]
    }
}

def make_urlopen_mock(req, *_):
    url = req.full_url
    if "challenger" in url:
        body = json.dumps(FAKE_CHALLENGERS).encode()
    elif "/ids" in url:
        body = json.dumps(FAKE_MATCH_IDS).encode()
    else:
        body = json.dumps(FAKE_MATCH_DETAIL).encode()
    return io.BytesIO(body)

# --- run handler under mocks ---

with mock.patch("boto3.client") as mock_boto, \
     mock.patch("psycopg2.connect") as mock_db, \
     mock.patch("urllib.request.urlopen", side_effect=make_urlopen_mock), \
     mock.patch("time.sleep"):

    mock_client = mock.MagicMock()
    mock_boto.return_value = mock_client
    mock_client.get_secret_value.return_value = {
        "SecretString": json.dumps({
            "riot_api_key": "RGAPI-fake-key-for-local-testing",
            "db_password":  "testpassword",
            "db_endpoint":  "localhost:5432",
            "db_name":      "tftdashboard",
        })
    }

    mock_conn = mock.MagicMock()
    mock_db.return_value = mock_conn

    from handler import main
    result = main({}, {})
    print("Lambda result:", result)
