import json
import os
import re
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./data")
DEFAULT_FILEPATH = os.path.join(OUTPUT_DIR, "records_2025.json")

def load_raw_data(filepath: str = DEFAULT_FILEPATH) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing live data file at: {filepath}. Run ingest.py first!")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return pd.DataFrame(data)

def get_teams_by_conference(df: pd.DataFrame, conference: str) -> list:
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
    cols = df.columns.tolist()
    home_team_key = next((c for c in cols if 'home_team' in c.lower() or 'hometeam' in c.lower()), 'home_team')
    away_team_key = next((c for c in cols if 'away_team' in c.lower() or 'awayteam' in c.lower()), 'away_team')

    schedule_df = df[(df[home_team_key] == team_name) | (df[away_team_key] == team_name)].copy()
    if 'week' in schedule_df.columns:
        schedule_df = schedule_df.sort_values(by='week')
    return schedule_df

def parse_game_box_stats(game_id: int, team_name: str, year: int = 2025) -> dict:
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

def _normalize_player_name(name: str) -> str:
    """Strips suffixes (Jr., Sr., II, III, IV) and punctuation for reliable name matching."""
    s = str(name or "").lower().strip()
    s = re.sub(r"[.,']", "", s)
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _build_roster_position_lookup(year: int, team_name: str) -> tuple[dict, dict]:
    """
    Builds (id_to_pos, normalized_name_to_pos) maps from cached team roster data.
    """
    from ingest import fetch_team_roster
    roster = fetch_team_roster(year=year, team=team_name)
    id_map = {}
    name_map = {}

    for p in roster:
        pos = str(p.get('position') or '').strip().upper()
        if not pos:
            continue

        p_id = p.get('id')
        if p_id is not None:
            id_map[str(p_id).strip()] = pos

        first = str(p.get('first_name') or p.get('firstName') or '').strip()
        last = str(p.get('last_name') or p.get('lastName') or '').strip()
        combined = f"{first} {last}".strip()
        raw_name = str(p.get('name') or p.get('full_name') or combined).strip()

        norm_name = _normalize_player_name(raw_name)
        if norm_name:
            name_map[norm_name] = pos

    return id_map, name_map

def parse_game_player_leaders(game_id: int, team_name: str, year: int = 2025) -> dict:
    """
    Extracts the statistical leader in passing, rushing, and receiving yards
    for each team in a given game, prefixed with their roster position (e.g., 'QB Jayden Daniels').
    """
    from ingest import fetch_game_player_stats
    player_records = fetch_game_player_stats(year=year, team=team_name)

    selected_game = None
    for record in player_records:
        rec_id = record.get('id') or record.get('game_id')
        if str(rec_id) == str(game_id):
            selected_game = record
            break

    if not selected_game:
        return {}

    target_categories = ['passing', 'rushing', 'receiving']
    default_pos_by_cat = {'passing': 'QB', 'rushing': 'RB', 'receiving': 'WR'}
    leaders_by_team = {}

    for team_entry in selected_game.get('teams', []):
        t_name = team_entry.get('school') or team_entry.get('team')
        leaders_by_team[t_name] = {cat: None for cat in target_categories}
        id_map, name_map = _build_roster_position_lookup(year=year, team_name=t_name)

        for cat_entry in team_entry.get('categories', []):
            cat_name = str(cat_entry.get('name', '')).lower()
            if cat_name not in target_categories:
                continue

            player_stats_map = {}
            for type_entry in cat_entry.get('types', []):
                stat_type = str(type_entry.get('name', '')).upper()
                for athlete in type_entry.get('athletes', []):
                    p_name = athlete.get('name', 'Unknown')
                    p_id = athlete.get('id')
                    stat_val = athlete.get('stat', '0')
                    if p_name not in player_stats_map:
                        player_stats_map[p_name] = {"_id": p_id}
                    player_stats_map[p_name][stat_type] = stat_val

            best_player = None
            best_yards = float('-inf')
            best_raw_stats = {}

            for p_name, stats_dict in player_stats_map.items():
                try:
                    yds = float(stats_dict.get('YDS', 0))
                except (ValueError, TypeError):
                    yds = 0.0

                if yds > best_yards:
                    best_yards = yds
                    best_player = p_name
                    best_raw_stats = stats_dict

            if best_player is not None:
                p_id_str = str(best_raw_stats.get("_id")).strip() if best_raw_stats.get("_id") is not None else ""
                norm_player = _normalize_player_name(best_player)

                pos = (
                    id_map.get(p_id_str)
                    or name_map.get(norm_player)
                    or default_pos_by_cat.get(cat_name, "")
                )
                player_display = f"{pos} {best_player}".strip() if pos else best_player

                yds_int = int(best_yards) if best_yards.is_integer() else best_yards
                if cat_name == 'passing':
                    c_att = best_raw_stats.get('C/ATT', '')
                    tds = best_raw_stats.get('TD', '0')
                    ints = best_raw_stats.get('INT', '0')
                    detail = f"{c_att}, {yds_int} YDS, {tds} TD, {ints} INT" if c_att else f"{yds_int} YDS, {tds} TD, {ints} INT"
                elif cat_name == 'rushing':
                    car = best_raw_stats.get('CAR', '0')
                    tds = best_raw_stats.get('TD', '0')
                    detail = f"{car} CAR, {yds_int} YDS, {tds} TD"
                else:  # receiving
                    rec = best_raw_stats.get('REC', '0')
                    tds = best_raw_stats.get('TD', '0')
                    detail = f"{rec} REC, {yds_int} YDS, {tds} TD"

                leaders_by_team[t_name][cat_name] = {
                    "player": player_display,
                    "yards": best_yards,
                    "summary": f"{player_display} ({detail})"
                }

    return leaders_by_team

def get_game_plays_df(game_id: int, week: int, team_name: str, year: int = 2025) -> pd.DataFrame:
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
    processed_df = df.copy()
    cols = processed_df.columns.tolist()
    
    home_pts_key = next((c for c in cols if 'home_points' in c.lower() or 'homepoints' in c.lower()), 'home_points')
    away_pts_key = next((c for c in cols if 'away_points' in c.lower() or 'awaypoints' in c.lower()), 'away_points')

    processed_df['home_pts'] = pd.to_numeric(processed_df[home_pts_key], errors='coerce').fillna(0).astype(int)
    processed_df['away_pts'] = pd.to_numeric(processed_df[away_pts_key], errors='coerce').fillna(0).astype(int)

    processed_df['total_points'] = processed_df['home_pts'] + processed_df['away_pts']
    processed_df['is_explosive_game'] = processed_df['total_points'] >= 60
    processed_df['margin'] = (processed_df['home_pts'] - processed_df['away_pts']).abs()
    
    return processed_df