import os
import json
import cfbd
from dotenv import load_dotenv

# Load environment variables from local .env if present
load_dotenv()

def get_secret(key: str, default=None):
    """Checks OS environment variables first, then falls back to Streamlit Cloud secrets."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

OUTPUT_DIR = get_secret("OUTPUT_DIR", "./data")

def get_api_configuration():
    api_key = get_secret("CFBD_API_KEY")
    if not api_key:
        raise ValueError("CFBD_API_KEY is missing. Add it to your local .env file or Streamlit Cloud Secrets.")
    return cfbd.Configuration(access_token=api_key)

def get_games_api():
    return cfbd.GamesApi(cfbd.ApiClient(get_api_configuration()))

def get_plays_api():
    return cfbd.PlaysApi(cfbd.ApiClient(get_api_configuration()))

def fetch_and_cache_games(year: int = 2026, classification: str = 'fbs', season_type: str = 'both'):
    """
    Fetches raw game records (regular + postseason) for any season (2020-2026) and caches locally.
    """
    print("\n=====================================")
    print(f"RUNNING LIVE GAME DATA INGESTION ({year})...")
    print("=====================================")

    try:
        games_api = get_games_api()
        output_dir = get_secret("OUTPUT_DIR", "./data")
        
        print(f"Connecting to secure data server gateway for {year} season...")
        games_data = games_api.get_games(year=int(year), season_type=season_type, classification=classification)
        
        raw_json_list = [game.to_dict() for game in games_data]
        
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"records_{year}.json")
        
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(raw_json_list, f, default=str, indent=4)
            
        print(f"SUCCESS! Saved {len(raw_json_list)} FBS game records into '{output_filename}'.")
        return output_filename

    except Exception as error:
        print(f"❌ PIPELINE CONNECTION REJECTED ({year}): {error}")
        raise error

    finally:
        print("=====================================\n")

def fetch_game_team_stats(year: int = 2026, team: str = None):
    """
    Fetches detailed box score team statistics for a given team and season.
    Caches locally per team/year.
    """
    try:
        games_api = get_games_api()
        output_dir = get_secret("OUTPUT_DIR", "./data")
        os.makedirs(output_dir, exist_ok=True)

        clean_team = team.lower().replace(' ', '_') if team else "all"
        output_filename = os.path.join(output_dir, f"box_stats_{clean_team}_{year}.json")

        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                return json.load(f)

        print(f"Fetching detailed game team stats for {team if team else 'FBS'} ({year})...")
        
        if team:
            box_stats = games_api.get_game_team_stats(year=int(year), team=team)
        else:
            box_stats = games_api.get_game_team_stats(year=int(year))

        raw_box_list = [game.to_dict() for game in box_stats]

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(raw_box_list, f, default=str, indent=4)

        return raw_box_list

    except Exception as error:
        print(f"❌ STATS INGESTION REJECTED: {error}")
        return []

def fetch_game_player_stats(year: int = 2026, team: str = None):
    """
    Fetches individual player box score statistics for a given team and season.
    Caches locally per team/year to minimize API calls.
    """
    try:
        games_api = get_games_api()
        output_dir = get_secret("OUTPUT_DIR", "./data")
        os.makedirs(output_dir, exist_ok=True)

        clean_team = team.lower().replace(' ', '_') if team else "all"
        output_filename = os.path.join(output_dir, f"player_stats_{clean_team}_{year}.json")

        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                return json.load(f)

        print(f"Fetching individual player game stats for {team if team else 'FBS'} ({year})...")
        
        if team:
            player_stats = games_api.get_game_player_stats(year=int(year), team=team)
        else:
            player_stats = games_api.get_game_player_stats(year=int(year))

        raw_player_list = [game.to_dict() for game in player_stats]

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(raw_player_list, f, default=str, indent=4)

        return raw_player_list

    except Exception as error:
        print(f"❌ PLAYER STATS INGESTION REJECTED: {error}")
        return []

def fetch_game_plays(year: int = 2026, week: int = 1, team: str = None):
    """
    Fetches play-by-play telemetry for a specific team, week, and season.
    Caches locally per team/week/year.
    """
    try:
        plays_api = get_plays_api()
        output_dir = get_secret("OUTPUT_DIR", "./data")
        os.makedirs(output_dir, exist_ok=True)

        clean_team = team.lower().replace(' ', '_') if team else "all"
        output_filename = os.path.join(output_dir, f"plays_{clean_team}_wk{week}_{year}.json")

        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                return json.load(f)

        print(f"Fetching play-by-play telemetry for {team} - Week {week} ({year})...")
        plays_data = plays_api.get_plays(year=int(year), week=int(week), team=team)
        raw_plays_list = [play.to_dict() for play in plays_data]

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(raw_plays_list, f, default=str, indent=4)

        return raw_plays_list

    except Exception as error:
        print(f"❌ PLAYS INGESTION REJECTED: {error}")
        return []

if __name__ == "__main__":
    for yr in range(2020, 2027):
        fetch_and_cache_games(year=yr)