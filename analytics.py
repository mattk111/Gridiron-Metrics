import json
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./data")
DEFAULT_FILEPATH = os.path.join(OUTPUT_DIR, "records_2025.json")

def load_raw_data(filepath: str = DEFAULT_FILEPATH) -> pd.DataFrame:
    """Loads raw game records JSON into a pandas DataFrame."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing live data file at: {filepath}. Run ingest.py first!")
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return pd.DataFrame(data)

def get_teams_by_conference(df: pd.DataFrame, conference: str) -> list:
    """Extracts a sorted list of unique team names belonging to a specific conference."""
    cols = df.columns.tolist()
    home_conf_key = next((c for c in cols if 'conference' in c.lower() and 'home' in c.lower()), None)
    away_conf_key = next((c for c in cols if 'conference' in c.lower() and 'away' in c.lower()), None)
    home_team_key = next((c for c in cols if 'home_team' in c.lower() or 'hometeam' in c.lower()), 'home_team')
    away_team_key = next((c for c in cols if 'away_team' in c.lower() or 'awayteam' in c.lower()), 'away_team')

    teams = set()
    if home_conf_key and away_conf_key:
        target = conference.lower()
        home_matches = df[df[home_conf_key].astype(str).str.lower() == target][home_team_key].dropna()
        away_matches = df[df[away_conf_key].astype(str).str.lower() == target][away_team_key].dropna()
        teams.update(home_matches)
        teams.update(away_matches)
    return sorted(list(teams))

def get_team_schedule(df: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Filters season records to isolate a selected team's full schedule."""
    cols = df.columns.tolist()
    home_team_key = next((c for c in cols if 'home_team' in c.lower() or 'hometeam' in c.lower()), 'home_team')
    away_team_key = next((c for c in cols if 'away_team' in c.lower() or 'awayteam' in c.lower()), 'away_team')

    schedule_df = df[(df[home_team_key] == team_name) | (df[away_team_key] == team_name)].copy()
    
    if 'week' in schedule_df.columns:
        schedule_df = schedule_df.sort_values(by='week')
        
    return schedule_df

def parse_game_box_stats(game_id: int, team_name: str, year: int = 2025) -> dict:
    """
    Queries cached team statistics and parses side-by-side metrics for a targeted game.
    Flexibly maps camelCase or snake_case keys from CFBD responses.
    """
    from ingest import fetch_game_team_stats
    box_records = fetch_game_team_stats(year=year, team=team_name)
    
    selected_game = None
    for record in box_records:
        rec_id = record.get('id') or record.get('game_id')
        if str(rec_id) == str(game_id):
            selected_game = record
            break
            
    if not selected_game:
        return {}

    parsed_stats = {}
    for team_entry in selected_game.get('teams', []):
        t_name = team_entry.get('school') or team_entry.get('team')
        stat_dict = {}
        for stat in team_entry.get('stats', []):
            category = stat.get('category')
            value = stat.get('stat')
            stat_dict[category] = value
            
            clean_cat = str(category).lower().replace(' ', '').replace('_', '')
            stat_dict[clean_cat] = value

        parsed_stats[t_name] = stat_dict

    return parsed_stats

def get_game_plays_df(game_id: int, week: int, team_name: str, year: int = 2025) -> pd.DataFrame:
    """
    Fetches play-by-play records for a specific team/week and isolates the exact game_id.
    """
    from ingest import fetch_game_plays
    plays_records = fetch_game_plays(year=year, week=week, team=team_name)
    if not plays_records:
        return pd.DataFrame()
        
    df_plays = pd.DataFrame(plays_records)
    cols = df_plays.columns.tolist()
    game_id_key = next((c for c in cols if c.lower() in ['game_id', 'gameid']), None)
    
    if game_id_key and game_id:
        filtered = df_plays[df_plays[game_id_key].astype(str) == str(game_id)].copy()
        if not filtered.empty:
            return filtered
            
    return df_plays

def calculate_coaching_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates game-level coaching metrics and logs analysis breakdown."""
    processed_df = df.copy()
    cols = processed_df.columns.tolist()
    
    home_team_key = next((c for c in cols if 'home_team' in c.lower() or 'hometeam' in c.lower()), 'home_team')
    away_team_key = next((c for c in cols if 'away_team' in c.lower() or 'awayteam' in c.lower()), 'away_team')
    home_pts_key = next((c for c in cols if 'home_points' in c.lower() or 'homepoints' in c.lower()), 'home_points')
    away_pts_key = next((c for c in cols if 'away_points' in c.lower() or 'awaypoints' in c.lower()), 'away_points')

    processed_df['home_pts'] = pd.to_numeric(processed_df[home_pts_key], errors='coerce').fillna(0).astype(int)
    processed_df['away_pts'] = pd.to_numeric(processed_df[away_pts_key], errors='coerce').fillna(0).astype(int)

    processed_df['total_points'] = processed_df['home_pts'] + processed_df['away_pts']
    processed_df['is_explosive_game'] = processed_df['total_points'] >= 60
    processed_df['margin'] = (processed_df['home_pts'] - processed_df['away_pts']).abs()
    
    return processed_df

if __name__ == "__main__":
    try:
        live_df = load_raw_data()
        calculate_coaching_metrics(live_df)
    except Exception as e:
        print(f"Pipeline Execution Error: {e}")