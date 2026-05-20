"""
Integration test — hits the real Riot API, mocks only DB and AWS.
Run with:
    RIOT_API_KEY="RGAPI-..." python test_integration.py
"""
import os
import json
import unittest.mock as mock

api_key = os.environ.get("RIOT_API_KEY") 
if not api_key:
    raise SystemExit("Set RIOT_API_KEY env var before running this test")

os.environ["AWS_REGION_NAME"] = "us-west-2"
os.environ["SECRET_ARN"] = "mock"

with mock.patch("boto3.client") as mock_boto, \
     mock.patch("psycopg2.connect") as mock_db, \
     mock.patch("time.sleep"):

    mock_client = mock.MagicMock()
    mock_boto.return_value = mock_client
    mock_client.get_secret_value.return_value = {
        "SecretString": json.dumps({
            "riot_api_key": api_key,
            "db_password":  "unused",
            "db_endpoint":  "localhost:5432",
            "db_name":      "unused",
        })
    }

    mock_conn = mock.MagicMock()
    mock_db.return_value = mock_conn

    from handler import main
    result = main({}, {})
    print("Result:", result)

    # Print every SQL call so you can see what would be written to the DB
    print("\n--- DB calls ---")
    for call in mock_conn.cursor.return_value.execute.call_args_list:
        sql  = call[0][0].strip().split("\n")[0]   # first line of query
        args = call[0][1] if len(call[0]) > 1 else ""
        print(f"  {sql[:60]}  {args}")
