import os
import pandas as pd
import nflreadpy as nfl
from ingest import get_secret

NFL_DATA_DIR = os.path.join(get_secret("OUTPUT_DIR", "./data"), "nfl")
os.makedirs(NFL_DATA_DIR, exist_ok=True)


def fetch_nfl_schedules(year: int = 2026) -> pd.DataFrame:
    """Loads NFL schedules & scores for a season, caching locally as Parquet."""
    cache_path = os.path.join(NFL_DATA_DIR, f"schedules_{year}.parquet")
    if os.path.exists(cache_path) and year != 2026:
        return pd.read_parquet(cache_path)

    df = nfl.load_schedules(seasons=[int(year)]).to_pandas()
    if not df.empty:
        df.to_parquet(cache_path, index=False)
    return df


def fetch_nfl_team_stats(year: int = 2026) -> pd.DataFrame:
    """Loads weekly NFL team box score stats for a season."""
    cache_path = os.path.join(NFL_DATA_DIR, f"team_stats_{year}.parquet")
    if os.path.exists(cache_path) and year != 2026:
        return pd.read_parquet(cache_path)

    df = nfl.load_team_stats(seasons=[int(year)], summary_level="week").to_pandas()
    if not df.empty:
        df.to_parquet(cache_path, index=False)
    return df


def fetch_nfl_player_stats(year: int = 2026) -> pd.DataFrame:
    """Loads weekly NFL player box score stats (with positions included)."""
    cache_path = os.path.join(NFL_DATA_DIR, f"player_stats_{year}.parquet")
    if os.path.exists(cache_path) and year != 2026:
        return pd.read_parquet(cache_path)

    df = nfl.load_player_stats(seasons=[int(year)], summary_level="week").to_pandas()
    if not df.empty:
        df.to_parquet(cache_path, index=False)
    return df


def fetch_nfl_game_plays(year: int = 2026, game_id: str = None) -> pd.DataFrame:
    """Loads NFL play-by-play for a season (cached locally) and filters to a single game_id."""
    cache_path = os.path.join(NFL_DATA_DIR, f"pbp_{year}.parquet")
    if os.path.exists(cache_path) and year != 2026:
        df = pd.read_parquet(cache_path)
    else:
        df = nfl.load_pbp(seasons=[int(year)]).to_pandas()
        if not df.empty:
            df.to_parquet(cache_path, index=False)

    if game_id and not df.empty and "game_id" in df.columns:
        return df[df["game_id"].astype(str) == str(game_id)].copy()
    return df