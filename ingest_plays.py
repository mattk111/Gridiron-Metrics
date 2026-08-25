import os
import json
import time
import cfbd
from dotenv import load_dotenv

load_dotenv()
RAW_KEY = os.getenv("CFBD_API_KEY")

print("\n=====================================")
print("RUNNING LIVE PLAY-BY-PLAY INGESTION...")
print("=====================================")

YEAR = 2025
WEEKS = range(1, 16)  # regular season runs through ~week 15 with champ weekend

try:
    configuration = cfbd.Configuration(
        access_token = RAW_KEY
    )

    api_client = cfbd.ApiClient(configuration)
    teams_api = cfbd.TeamsApi(api_client)
    plays_api = cfbd.PlaysApi(api_client)

    print("Connecting to secure data server gateway...")
    # The plays endpoint has no server-side classification filter, so we grab
    # the FBS roster once and lock to FBS-only client-side, same rule ingest.py
    # already enforces server-side for game records.
    fbs_teams = {t.school for t in teams_api.get_fbs_teams(year=YEAR)}

    all_plays = []
    for week in WEEKS:
        print(f"Pulling snaps for Week {week}...")
        try:
            week_plays = plays_api.get_plays(year=YEAR, week=week, season_type='regular')
        except Exception as week_error:
            print(f"  ⚠️ Skipped week {week}: {week_error}")
            continue

        for play in week_plays:
            record = play.to_dict()
            if record.get('offense') in fbs_teams and record.get('defense') in fbs_teams:
                all_plays.append(record)

        time.sleep(0.2)  # stay polite with rate limits

    output_filename = "plays_2025.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_plays, f, default=str, indent=4)

    print("SUCCESS! Real play-by-play pipeline established.")
    print(f"Saved {len(all_plays)} FBS-ONLY plays into '{output_filename}'.")

except Exception as error:
    print(f"❌ PIPELINE CONNECTION REJECTED: {error}")

print("=====================================\n")