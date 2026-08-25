import os
import json
import cfbd
from dotenv import load_dotenv

load_dotenv()
RAW_KEY = os.getenv("CFBD_API_KEY")

print("\n=====================================")
print("RUNNING LIVE PASSING DATA INGESTION...")
print("=====================================")

YEAR = 2025

try:
    configuration = cfbd.Configuration(
        access_token = RAW_KEY
    )

    api_client = cfbd.ApiClient(configuration)
    players_api = cfbd.PlayersApi(api_client)
    stats_api = cfbd.StatsApi(api_client)

    print("Connecting to secure data server gateway...")
    # Player-level completions/attempts/yards for the completion-ratio side
    # of the Passing Efficiency Index.
    passing_player_stats = players_api.get_player_season_stats(
        year=YEAR, season_type='regular', category='passing'
    )
    # Team-level advanced stats for the dropback-success side of the index.
    advanced_team_stats = stats_api.get_advanced_team_season_stats(year=YEAR)

    payload = {
        "player_passing_stats": [row.to_dict() for row in passing_player_stats],
        "advanced_team_stats": [row.to_dict() for row in advanced_team_stats],
    }

    output_filename = "passing_raw_2025.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, default=str, indent=4)

    print("SUCCESS! Real passing data pipeline established.")
    print(
        f"Saved {len(payload['player_passing_stats'])} passing stat rows and "
        f"{len(payload['advanced_team_stats'])} team advanced-stat rows into '{output_filename}'."
    )

except Exception as error:
    print(f"❌ PIPELINE CONNECTION REJECTED: {error}")

print("=====================================\n")