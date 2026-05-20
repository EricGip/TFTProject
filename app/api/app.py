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
    client = boto3.client(
        "secretsmanager",
        region_name=os.environ.get("AWS_REGION", "us-west-2")
    )
    response = client.get_secret_value(
        SecretId=os.environ["SECRET_ARN"]
    )
    return json.loads(response["SecretString"])


def get_db_connection():
    secrets = get_secrets()
    return psycopg2.connect(
        host=secrets["db_endpoint"].split(":")[0],
        dbname=secrets["db_name"],
        user="dbadmin",
        password=secrets["db_password"]
    )


def serialize_row(row):
    d = dict(row)
    for k, v in d.items():
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat()
    return d


@app.route("/health")
def health():
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
                ROUND(wins::numeric / NULLIF(wins + losses, 0) * 100, 1) AS win_rate,
                fetched_at
            FROM tft_leaderboard
            ORDER BY rank ASC
        """)
        players = [serialize_row(p) for p in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"players": players, "count": len(players)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/player/<riot_id>")
def player(riot_id):
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
                ROUND(wins::numeric / NULLIF(wins + losses, 0) * 100, 1) AS win_rate,
                fetched_at
            FROM tft_leaderboard
            WHERE riot_id = %s
        """, (riot_id,))
        p = cur.fetchone()
        cur.close()
        conn.close()
        if not p:
            return jsonify({"error": "Player not found"}), 404
        return jsonify(serialize_row(p)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/player/<riot_id>/matches")
def player_matches(riot_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            WITH pm AS (
                SELECT match_id, puuid, placement, fetched_at
                FROM tft_match_participants
                WHERE riot_id = %s
                ORDER BY fetched_at DESC
                LIMIT 20
            )
            SELECT
                pm.match_id,
                pm.placement,
                pm.fetched_at,
                COALESCE(
                    (SELECT json_agg(
                                json_build_object(
                                    'character_id', u.character_id,
                                    'tier', u.tier,
                                    'rarity', u.rarity,
                                    'item_names', u.item_names
                                ) ORDER BY u.rarity DESC NULLS LAST
                            )
                     FROM tft_match_units u
                     WHERE u.match_id = pm.match_id AND u.puuid = pm.puuid
                    ), '[]'::json
                ) AS units,
                COALESCE(
                    (SELECT json_agg(
                                json_build_object(
                                    'trait_name', t.trait_name,
                                    'num_units', t.num_units,
                                    'tier', t.tier
                                ) ORDER BY t.tier DESC NULLS LAST
                            ) FILTER (WHERE t.tier > 0)
                     FROM tft_match_traits t
                     WHERE t.match_id = pm.match_id AND t.puuid = pm.puuid
                    ), '[]'::json
                ) AS traits
            FROM pm
            ORDER BY pm.fetched_at DESC
        """, (riot_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        matches = []
        for row in rows:
            m = serialize_row(row)
            m['units'] = m['units'] if m['units'] is not None else []
            m['traits'] = m['traits'] if m['traits'] is not None else []
            matches.append(m)

        return jsonify({"matches": matches}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/meta/units")
def meta_units():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                u.character_id,
                COUNT(*) AS games_played,
                ROUND(AVG(u.tier)::numeric, 1) AS avg_tier,
                ROUND(AVG(u.rarity)::numeric, 1) AS avg_rarity,
                array_agg(DISTINCT mp.riot_id)
                    FILTER (WHERE mp.riot_id IS NOT NULL AND mp.riot_id != '') AS players
            FROM tft_match_units u
            JOIN tft_match_participants mp
                ON mp.match_id = u.match_id AND mp.puuid = u.puuid
            GROUP BY u.character_id
            ORDER BY games_played DESC
            LIMIT 30
        """)
        units = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"units": units}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/meta/traits")
def meta_traits():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                t.trait_name,
                COUNT(*) AS games_played,
                ROUND(AVG(t.tier)::numeric, 1) AS avg_tier,
                ROUND(AVG(t.num_units)::numeric, 1) AS avg_num_units,
                array_agg(DISTINCT mp.riot_id)
                    FILTER (WHERE mp.riot_id IS NOT NULL AND mp.riot_id != '') AS players
            FROM tft_match_traits t
            JOIN tft_match_participants mp
                ON mp.match_id = t.match_id AND mp.puuid = t.puuid
            WHERE t.tier > 0
            GROUP BY t.trait_name
            ORDER BY games_played DESC
            LIMIT 30
        """)
        traits = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"traits": traits}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def stats():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                MAX(league_points)                                             AS highest_lp,
                ROUND(AVG(wins::numeric / NULLIF(wins + losses, 0) * 100), 1) AS avg_win_rate,
                MAX(fetched_at)                                                AS last_updated,
                COUNT(*)                                                       AS total_players
            FROM tft_leaderboard
        """)
        result = serialize_row(cur.fetchone())
        cur.close()
        conn.close()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
