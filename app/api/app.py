import os
import json
import boto3
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify
from functools import lru_cache

app = Flask(__name__)

@lru_cache(maxsize=1)
def get_secrets():
    # """
    # Fetches secrets once and caches them for the lifetime
    # of this Lambda execution / EC2 process.
    # lru_cache means this only calls Secrets Manager on the
    # first request — not on every API call.
    # """
    client = boto3.client(
        "secretsmanager",
        region_name=os.environ.get("AWS_REGION", "us-west-2")
    )
    response = client.get_secret_value(
        SecretId=os.environ["SECRET_ARN"]
    )
    return json.loads(response["SecretString"])
    
    # Uncomment this for local testing
    # return {"db_endpoint": "localhost:5432", "db_name": "tftdashboard", "db_password": "test"}


def get_db_connection():
    """
    Creates a new DB connection using secrets from Secrets Manager.
    Called per-request — psycopg2 connections aren't thread safe
    to share across requests.
    """
    secrets = get_secrets()
    return psycopg2.connect(
        host=secrets["db_endpoint"].split(":")[0],
        dbname=secrets["db_name"],
        user="dbadmin",
        password=secrets["db_password"]
    )

@app.route("/health")
def health():
    """
    This is the route the ALB hits every 30 seconds.
    We check the DB connection here too — if RDS is down
    the instance should be marked unhealthy.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
    

@app.route("/api/leaderboard")
def leaderboard():
    """
    Returns the current top 50 TFT challenger players.
    This is the main route the React dashboard calls.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                rank,
                riot_id,
                league_points,
                wins,
                losses,
                ROUND(wins::numeric / NULLIF(wins + losses, 0) * 100, 1) as win_rate,
                fetched_at
            FROM tft_leaderboard
            ORDER BY rank ASC
        """)
        players = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            "players": [dict(p) for p in players],
            "count":   len(players)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


@app.route("/api/player/<riot_id>")
def player(riot_id):
    """
    Returns details for a specific player.
    The React dashboard calls this when a user clicks a row.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                rank,
                summoner_name,
                league_points,
                wins,
                losses,
                ROUND(wins::numeric / NULLIF(wins + losses, 0) * 100, 1) as win_rate,
                fetched_at
            FROM tft_leaderboard
            WHERE summoner_name = %s
        """, (riot_id,))

        player = cur.fetchone()
        cur.close()
        conn.close()

        if not player:
            return jsonify({"error": "Player not found"}), 404

        return jsonify(dict(player)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/api/stats")
def stats():
    """
    Aggregate stats for the dashboard header —
    highest LP, average win rate, last updated time.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                MAX(league_points)                                        as highest_lp,
                ROUND(AVG(wins::numeric / NULLIF(wins + losses, 0) * 100), 1) as avg_win_rate,
                MAX(fetched_at)                                           as last_updated,
                COUNT(*)                                                  as total_players
            FROM tft_leaderboard
        """)
        stats = dict(cur.fetchone())
        cur.close()
        conn.close()
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)