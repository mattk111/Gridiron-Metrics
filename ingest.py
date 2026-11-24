import os
import json
import inspect
import cfbd
from dotenv import load_dotenv

load_dotenv()


def get_secret(key: str, default: str = "") -> str:
    """Reads secrets from Streamlit Cloud st.secrets first, then falls back to .env / os.environ."""
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return os.getenv(key, default).strip()


def get_api_configuration():
    """Creates a CFBD Configuration compatible with both cfbd v4 and v5+ SDKs."""
    api_key = get_secret("CFBD_API_KEY")
    if not api_key:
        raise ValueError("CFBD_API_KEY not found in Streamlit Secrets or .env file.")

    sig = inspect.signature(cfbd.Configuration.__init__)
    if "access_token" in sig.parameters:
        return cfbd.Configuration(access_token=api_key)

    config = cfbd.Configuration()
    config.api_key["Authorization"] = api_key
    config.api_key_prefix["Authorization"] = "Bearer"
    return config


def get_games_api():
    return cfbd.GamesApi(cfbd.ApiClient(get_api_configuration()))


def get_plays_api():
    return cfbd.PlaysApi(cfbd.ApiClient(get_api_configuration()))


def get_teams_api():
    return cfbd.TeamsApi(cfbd.ApiClient(get_api_configuration()))


def fetch_and_cache_games(year: int = 2026):
    """Fetches regular + postseason FBS games for a season and caches them as JSON."""
    output_dir = get_secret("OUTPUT_DIR", "./data")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"records_{year}.json")

    games_api = get_games_api()
    all_games = []

    for s_type in ["regular", "postseason"]:
        try:
            games = games_api.get_games(year=int(year), season_type=s_type)
            for g in games:
                if hasattr(g, "to_dict"):
                    all_games.append(g.to_dict())
                elif isinstance(g, dict):
                    all_games.append(g)
        except Exception as e:
            print(f"Warning fetching {year} {s_type} games: {e}")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(all_games, f, default=str, indent=2)

    return all_games


if __name__ == "__main__":
    for yr in range(2010, 2027):
        fetch_and_cache_games(year=yr)