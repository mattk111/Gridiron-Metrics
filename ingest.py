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


def _to_dict_list(items) -> list:
    out = []
    for item in items or []:
        if hasattr(item, "to_dict"):
            out.append(item.to_dict())
        elif isinstance(item, dict):
            out.append(item)
    return out


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
            all_games.extend(_to_dict_list(games))
        except Exception:
            try:
                enum_val = cfbd.SeasonType.REGULAR if s_type == "regular" else cfbd.SeasonType.POSTSEASON
                games = games_api.get_games(year=int(year), season_type=enum_val)
                all_games.extend(_to_dict_list(games))
            except Exception as e:
                print(f"Warning fetching {year} {s_type} games: {e}")

    if all_games:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(all_games, f, default=str, indent=2)

    return all_games


def fetch_game_team_stats(year: int = 2026, team: str = None, week: int = None, game_id: int = None, **kwargs) -> list:
    """Fetches team box score stats matching analytics.py keyword arguments (year, team, week, game_id)."""
    games_api = get_games_api()
    results = []
    for s_type in ["regular", "postseason"]:
        api_kwargs = {"year": int(year)}
        if team:
            api_kwargs["team"] = team
        if week is not None:
            api_kwargs["week"] = int(week)
        if game_id is not None:
            api_kwargs["id"] = int(game_id)

        try:
            stats = games_api.get_game_team_stats(season_type=s_type, **api_kwargs)
            results.extend(_to_dict_list(stats))
        except Exception:
            try:
                enum_val = cfbd.SeasonType.REGULAR if s_type == "regular" else cfbd.SeasonType.POSTSEASON
                stats = games_api.get_game_team_stats(season_type=enum_val, **api_kwargs)
                results.extend(_to_dict_list(stats))
            except Exception as e:
                print(f"Error fetching team stats ({year} {s_type}): {e}")
    return results


def fetch_game_player_stats(year: int = 2026, team: str = None, week: int = None, game_id: int = None, **kwargs) -> list:
    """Fetches player box score stats matching analytics.py keyword arguments (year, team, week, game_id)."""
    games_api = get_games_api()
    results = []
    for s_type in ["regular", "postseason"]:
        api_kwargs = {"year": int(year)}
        if team:
            api_kwargs["team"] = team
        if week is not None:
            api_kwargs["week"] = int(week)
        if game_id is not None:
            api_kwargs["id"] = int(game_id)

        try:
            stats = games_api.get_game_player_stats(season_type=s_type, **api_kwargs)
            results.extend(_to_dict_list(stats))
        except Exception:
            try:
                enum_val = cfbd.SeasonType.REGULAR if s_type == "regular" else cfbd.SeasonType.POSTSEASON
                stats = games_api.get_game_player_stats(season_type=enum_val, **api_kwargs)
                results.extend(_to_dict_list(stats))
            except Exception as e:
                print(f"Error fetching player stats ({year} {s_type}): {e}")
    return results


def fetch_game_plays(year: int = 2026, week: int = None, team: str = None, game_id: int = None, **kwargs) -> list:
    """Fetches play-by-play data matching analytics.py keyword arguments (year, week, team, game_id)."""
    plays_api = get_plays_api()
    results = []
    for s_type in ["regular", "postseason"]:
        api_kwargs = {"year": int(year)}
        if week is not None:
            api_kwargs["week"] = int(week)
        if team:
            api_kwargs["team"] = team

        try:
            plays = plays_api.get_plays(season_type=s_type, **api_kwargs)
            results.extend(_to_dict_list(plays))
        except Exception:
            try:
                enum_val = cfbd.SeasonType.REGULAR if s_type == "regular" else cfbd.SeasonType.POSTSEASON
                plays = plays_api.get_plays(season_type=enum_val, **api_kwargs)
                results.extend(_to_dict_list(plays))
            except Exception as e:
                print(f"Error fetching plays ({year} {s_type}): {e}")

    if game_id is not None and results:
        filtered = [p for p in results if str(p.get("game_id") or p.get("gameId") or p.get("id")) == str(game_id)]
        if filtered:
            return filtered
    return results


def fetch_team_roster(team: str, year: int = 2026, **kwargs) -> list:
    """Fetches official season roster for position lookups (QB, RB, WR, TE)."""
    teams_api = get_teams_api()
    try:
        roster = teams_api.get_roster(team=team, year=int(year))
        return _to_dict_list(roster)
    except Exception as e:
        print(f"Error fetching roster for {team} ({year}): {e}")
        return []


if __name__ == "__main__":
    for yr in range(2010, 2027):
        fetch_and_cache_games(year=yr)