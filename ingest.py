import os
import json
import inspect
import urllib.request
import urllib.parse
import cfbd
from dotenv import load_dotenv

load_dotenv()

CFBD_BASE_URL = "https://api.collegefootballdata.com"


def get_secret(key: str, default: str = "") -> str:
    """Reads secrets from Streamlit Cloud st.secrets first, then falls back to .env / os.environ."""
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return os.getenv(key, default).strip()


def _cfbd_rest_get(endpoint: str, params: dict) -> list:
    """Direct REST fallback to api.collegefootballdata.com using Bearer token (immune to SDK version changes)."""
    api_key = get_secret("CFBD_API_KEY")
    if not api_key:
        raise ValueError("CFBD_API_KEY not found in Streamlit Secrets or .env file.")

    clean_params = {k: v for k, v in params.items() if v is not None}
    query = urllib.parse.urlencode(clean_params)
    url = f"{CFBD_BASE_URL}{endpoint}?{query}" if query else f"{CFBD_BASE_URL}{endpoint}"

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "GridironMetrics/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data if isinstance(data, list) else []


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


def _normalize_record(d: dict) -> dict:
    """Ensures both snake_case and camelCase keys exist on every CFBD record."""
    aliases = {
        "homeTeam": "home_team",
        "awayTeam": "away_team",
        "homeConference": "home_conference",
        "awayConference": "away_conference",
        "homeClassification": "home_classification",
        "awayClassification": "away_classification",
        "homePoints": "home_points",
        "awayPoints": "away_points",
        "seasonType": "season_type",
        "startDate": "start_date",
        "gameId": "game_id",
        "offenseTeam": "offense_team",
        "playType": "play_type",
        "yardsGained": "yards_gained",
        "playText": "play_text",
        "driveNumber": "drive_number",
        "playNumber": "play_number",
        "offenseScore": "offense_score",
        "defenseScore": "defense_score",
    }
    out = dict(d)
    for camel, snake in aliases.items():
        if camel in out and snake not in out:
            out[snake] = out[camel]
    return out


def _to_dict_list(items) -> list:
    out = []
    for item in items or []:
        if hasattr(item, "to_dict"):
            out.append(_normalize_record(item.to_dict()))
        elif isinstance(item, dict):
            out.append(_normalize_record(item))
    return out


def fetch_and_cache_games(year: int = 2026):
    """Fetches regular + postseason FBS games for a season and caches them as JSON."""
    output_dir = get_secret("OUTPUT_DIR", "./data")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"records_{year}.json")

    all_games = []
    for s_type in ["regular", "postseason"]:
        try:
            raw = _cfbd_rest_get("/games", {"year": int(year), "seasonType": s_type})
            all_games.extend(_to_dict_list(raw))
        except Exception as e:
            print(f"Warning fetching {year} {s_type} games via REST: {e}")
            try:
                games_api = get_games_api()
                games = games_api.get_games(year=int(year), season_type=s_type)
                all_games.extend(_to_dict_list(games))
            except Exception as e2:
                print(f"Warning fetching {year} {s_type} games via SDK: {e2}")

    if all_games:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(all_games, f, default=str, indent=2)

    return all_games


def fetch_game_team_stats(year: int = 2026, team: str = None, week: int = None, game_id: int = None, **kwargs) -> list:
    """Fetches team box score stats."""
    results = []
    for s_type in ["regular", "postseason"]:
        params = {"year": int(year), "seasonType": s_type, "team": team, "week": week, "id": game_id}
        try:
            raw = _cfbd_rest_get("/games/teams", params)
            results.extend(_to_dict_list(raw))
        except Exception as e:
            print(f"Error fetching team stats ({year} {s_type}): {e}")
    return results


def fetch_game_player_stats(year: int = 2026, team: str = None, week: int = None, game_id: int = None, **kwargs) -> list:
    """Fetches individual player box score stats."""
    results = []
    for s_type in ["regular", "postseason"]:
        params = {"year": int(year), "seasonType": s_type, "team": team, "week": week, "id": game_id}
        try:
            raw = _cfbd_rest_get("/games/players", params)
            results.extend(_to_dict_list(raw))
        except Exception as e:
            print(f"Error fetching player stats ({year} {s_type}): {e}")
    return results


def fetch_game_plays(year: int = 2026, week: int = None, team: str = None, game_id: int = None, **kwargs) -> list:
    """Fetches play-by-play data for a CFB game."""
    results = []
    for s_type in ["regular", "postseason"]:
        params = {"year": int(year), "seasonType": s_type, "week": week, "team": team}
        try:
            raw = _cfbd_rest_get("/plays", params)
            results.extend(_to_dict_list(raw))
        except Exception as e:
            print(f"Error fetching plays ({year} {s_type}): {e}")

    if game_id is not None and results:
        filtered = [p for p in results if str(p.get("game_id") or p.get("gameId") or p.get("id")) == str(game_id)]
        if filtered:
            return filtered
    return results


def fetch_team_roster(team: str, year: int = 2026, **kwargs) -> list:
    """Fetches official season roster for position lookups (QB, RB, WR, TE)."""
    try:
        raw = _cfbd_rest_get("/roster", {"team": team, "year": int(year)})
        return _to_dict_list(raw)
    except Exception as e:
        print(f"Error fetching roster for {team} ({year}): {e}")
        return []


if __name__ == "__main__":
    for yr in range(2010, 2027):
        fetch_and_cache_games(year=yr)