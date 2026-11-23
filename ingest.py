import os
import json
import cfbd
from dotenv import load_dotenv

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

def get_teams_api():
    return cfbd.TeamsApi(cfbd.ApiClient(get_api_configuration()))

def fetch_and_cache_games(year: int = 2026, classification: str = 'fbs', season_type: str = 'both'):
    games_api = get_games_api()
    output_dir = get_secret("OUTPUT_DIR", "./data")
    games_data = games_api.get_games(year=int(year), season_type=season_type, classification=classification)
    raw_json_list = [game.to_dict() for game in games_data]
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"records_{year}.json")
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(raw_json_list, f, default=str, indent=4)
    return output_filename

def fetch_team_roster(year: int = 2026, team: str = None):
    """
    Fetches team roster for a given team and season to map athlete IDs/names to positions.
    Only caches non-empty responses.
    """
    if not team:
        return []
    try:
        teams_api = get_teams_api()
        output_dir = get_secret("OUTPUT_DIR", "./data")
        os.makedirs(output_dir, exist_ok=True)

        clean_team = team.lower().replace(' ', '_').replace('&', 'and')
        output_filename = os.path.join(output_dir, f"roster_{clean_team}_{year}.json")

        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if cached:
                    return cached

        roster_data = teams_api.get_roster(year=int(year), team=team)
        raw_roster_list = [player.to_dict() for player in roster_data]

        if raw_roster_list:
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(raw_roster_list, f, default=str, indent=4)

        return raw_roster_list

    except Exception as error:
        print(f"❌ ROSTER INGESTION REJECTED ({team} {year}): {error}")
        return []

def fetch_game_team_stats(year: int = 2026, team: str = None):
    try:
        games_api = get_games_api()
        output_dir = get_secret("OUTPUT_DIR", "./data")
        os.makedirs(output_dir, exist_ok=True)

        clean_team = team.lower().replace(' ', '_') if team else "all"
        output_filename = os.path.join(output_dir, f"box_stats_{clean_team}_{year}.json")

        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                return json.load(f)

        box_stats = games_api.get_game_team_stats(year=int(year), team=team) if team else games_api.get_game_team_stats(year=int(year))
        raw_box_list = [game.to_dict() for game in box_stats]

        if raw_box_list:
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(raw_box_list, f, default=str, indent=4)

        return raw_box_list
    except Exception as error:
        print(f"❌ STATS INGESTION REJECTED: {error}")
        return []

def fetch_game_player_stats(year: int = 2026, team: str = None):
    try:
        games_api = get_games_api()
        output_dir = get_secret("OUTPUT_DIR", "./data")
        os.makedirs(output_dir, exist_ok=True)

        clean_team = team.lower().replace(' ', '_') if team else "all"
        output_filename = os.path.join(output_dir, f"player_stats_{clean_team}_{year}.json")

        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                return json.load(f)

        player_stats = games_api.get_game_player_stats(year=int(year), team=team) if team else games_api.get_game_player_stats(year=int(year))
        raw_player_list = [game.to_dict() for game in player_stats]

        if raw_player_list:
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(raw_player_list, f, default=str, indent=4)

        return raw_player_list
    except Exception as error:
        print(f"❌ PLAYER STATS INGESTION REJECTED: {error}")
        return []

def fetch_game_plays(year: int = 2026, week: int = 1, team: str = None):
    try:
        plays_api = get_plays_api()
        output_dir = get_secret("OUTPUT_DIR", "./data")
        os.makedirs(output_dir, exist_ok=True)

        clean_team = team.lower().replace(' ', '_') if team else "all"
        output_filename = os.path.join(output_dir, f"plays_{clean_team}_wk{week}_{year}.json")

        if os.path.exists(output_filename):
            with open(output_filename, "r", encoding="utf-8") as f:
                return json.load(f)

        plays_data = plays_api.get_plays(year=int(year), week=int(week), team=team)
        raw_plays_list = [play.to_dict() for play in plays_data]

        if raw_plays_list:
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(raw_plays_list, f, default=str, indent=4)

        return raw_plays_list
    except Exception as error:
        print(f"❌ PLAYS INGESTION REJECTED: {error}")
        return []

if __name__ == "__main__":
    for yr in range(2010, 2027):
        fetch_and_cache_games(year=yr)