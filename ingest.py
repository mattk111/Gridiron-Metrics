import os
import json
import cfbd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RAW_KEY = os.getenv("CFBD_API_KEY")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./data")

def get_api_configuration():
    if not RAW_KEY:
        raise ValueError("CFBD_API_KEY is missing from environment variables. Check your .env file.")
    return cfbd.Configuration(access_token=RAW_KEY)

def get_games_api():
    return cfbd.GamesApi(cfbd.ApiClient(get_api_configuration()))

def get_plays_api():
    return cfbd.PlaysApi(cfbd.ApiClient(get_api_configuration()))

def fetch_and_cache_games(year: int = 2025, classification: str = 'fbs', season_type: str = 'regular'):
    """
    Fetches raw game records from the CFBD GamesApi and caches them to a local JSON file.
    """
    print("\n=====================================")
    print("RUNNING LIVE GAME DATA INGESTION...")
    print("=====================================")

    try:
        games_api = get_games_api()
        
        print("Connecting to secure data server gateway...")
        games_data = games_api.get_games(year=year, season_type=season_type, classification=classification)
        
        raw_json_list = [game.to_dict() for game in games_data]
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_filename = os.path.join(OUTPUT_DIR, f"records_{year}.json")
        
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(raw_json_list, f, default=str, indent=4)
            
        print("SUCCESS! Real college football game data pipeline established.")
        print(f"Saved {len(raw_json_list)} real FBS game records into '{output_filename}'.")
        return output_filename

    except Exception as error:
        print(f"❌ PIPELINE CONNECTION REJECTED: {error}")
        print("Action Required: Check your .env file to ensure the API key is active.")
        raise error

    finally:
        print("=====================================\n")

def fetch_game_team_stats(year: int = 2025, team: str = None):
    """
    Fetches detailed box score team statistics for a given team/year.
    Caches locally to disk to minimize network calls.
    """
    try:
        games_api = get_games_api()
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        clean_team = team.lower().replace(' ', '_') if team else "all"
        output_filename = os.path.join(OUTPUT_DIR, f"box_stats_{clean_team}_{year}.json")

        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                return json.load(f)

        print(f"Fetching detailed game team stats for {team if team else 'FBS'} ({year})...")
        
        if team:
            box_stats = games_api.get_game_team_stats(year=year, team=team)
        else:
            box_stats = games_api.get_game_team_stats(year=year)

        raw_box_list = [game.to_dict() for game in box_stats]

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(raw_box_list, f, default=str, indent=4)

        return raw_box_list

    except Exception as error:
        print(f"❌ STATS INGESTION REJECTED: {error}")
        return []

def fetch_game_plays(year: int = 2025, week: int = 1, team: str = None):
    """
    Fetches play-by-play telemetry for a specific team and week using PlaysApi.get_plays().
    Caches locally per team/week so repeated inspections load instantly.
    """
    try:
        plays_api = get_plays_api()
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        clean_team = team.lower().replace(' ', '_') if team else "all"
        output_filename = os.path.join(OUTPUT_DIR, f"plays_{clean_team}_wk{week}_{year}.json")

        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                return json.load(f)

        print(f"Fetching play-by-play telemetry for {team} - Week {week} ({year})...")
        plays_data = plays_api.get_plays(year=year, week=int(week), team=team)
        raw_plays_list = [play.to_dict() for play in plays_data]

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(raw_plays_list, f, default=str, indent=4)

        return raw_plays_list

    except Exception as error:
        print(f"❌ PLAYS INGESTION REJECTED: {error}")
        return []

if __name__ == "__main__":
    fetch_and_cache_games(year=2025)