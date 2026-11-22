import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from analytics import (
    get_teams_by_conference, 
    get_team_schedule, 
    parse_game_box_stats,
    parse_game_player_leaders,
    get_game_plays_df
)

# --- ENVIRONMENT CONFIGURATION ---
load_dotenv()
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./data")
AVAILABLE_SEASONS = [2026, 2025, 2024, 2023, 2022, 2021, 2020]

# --- PAGE INITIALIZATION LAYOUT ---
st.set_page_config(page_title="GridironMetrics CFB Dashboard", page_icon="🏈", layout="wide")

# --- CONSOLIDATED BACKEND DATA LOADERS ---
@st.cache_data(ttl=3600)
def load_game_data(year: int):
    """Loads schedule data for any season (2020-2026), auto-fetching from CFBD if not cached."""
    filepath = os.path.join(OUTPUT_DIR, f"records_{year}.json")
    if not os.path.exists(filepath):
        from ingest import fetch_and_cache_games
        fetch_and_cache_games(year=year)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return pd.DataFrame(json.load(f))
    return pd.DataFrame()

def extract_stat_value(team_stats_dict, possible_keys):
    for key in possible_keys:
        if key in team_stats_dict:
            return team_stats_dict[key]
        clean_key = str(key).lower().replace(' ', '').replace('_', '')
        if clean_key in team_stats_dict:
            return team_stats_dict[clean_key]
    return "N/A"

def parse_comparable_stat(val):
    """Converts raw box score strings (numbers or 'made-att' ratios) into comparable floats."""
    if val is None or str(val).strip().upper() == "N/A":
        return None
    s = str(val).strip()
    if "-" in s and not s.startswith("-"):
        parts = s.split("-")
        if len(parts) == 2:
            try:
                made = float(parts[0])
                att = float(parts[1])
                return (made / att) if att > 0 else 0.0
            except ValueError:
                return None
    try:
        return float(s)
    except ValueError:
        return None

def style_box_score_winner(row, away_col, home_col):
    """Highlights the cell of the team with the better performance in each stat row."""
    styles = [''] * len(row)
    metric_name = str(row.get("Metric", "")).lower()
    
    away_val = parse_comparable_stat(row.get(away_col))
    home_val = parse_comparable_stat(row.get(home_col))
    
    if away_val is None or home_val is None or away_val == home_val:
        return styles

    lower_is_better = "turnover" in metric_name
    away_wins = (away_val < home_val) if lower_is_better else (away_val > home_val)

    win_style = 'background-color: rgba(16, 185, 129, 0.28); color: #ecfdf5; font-weight: 700;'
    col_names = list(row.index)
    
    if away_wins:
        styles[col_names.index(away_col)] = win_style
    else:
        styles[col_names.index(home_col)] = win_style
        
    return styles

def style_leader_winner(row, away_col, home_col, away_yards_list, home_yards_list):
    """Highlights the statistical leader cell with higher yardage in each category."""
    styles = [''] * len(row)
    idx = row.name
    a_yds = away_yards_list[idx]
    h_yds = home_yards_list[idx]

    if a_yds is None or h_yds is None or a_yds == h_yds:
        return styles

    win_style = 'background-color: rgba(16, 185, 129, 0.28); color: #ecfdf5; font-weight: 700;'
    col_names = list(row.index)

    if a_yds > h_yds:
        styles[col_names.index(away_col)] = win_style
    else:
        styles[col_names.index(home_col)] = win_style

    return styles

def format_play_clock(clock_val):
    """Formats CFBD clock dict ({'minutes': 2, 'seconds': 43}) or string into '2:43'."""
    if isinstance(clock_val, dict):
        mins = clock_val.get('minutes')
        secs = clock_val.get('seconds')
        if mins is not None and secs is not None:
            return f"{int(mins)}:{int(secs):02d}"
    if clock_val is None or str(clock_val).strip() in ["", "None", "nan"]:
        return "N/A"
    return str(clock_val)

def clock_to_seconds(clock_val):
    """Converts CFBD clock dict or 'MM:SS' string into total seconds remaining for sorting."""
    if isinstance(clock_val, dict):
        mins = clock_val.get('minutes')
        secs = clock_val.get('seconds')
        if mins is not None and secs is not None:
            return int(mins) * 60 + int(secs)
    s = str(clock_val).strip()
    if ":" in s:
        parts = s.split(":")
        if len(parts) == 2:
            try:
                return int(parts[0]) * 60 + int(parts[1])
            except ValueError:
                pass
    return -1

def format_quarter(period_val):
    """Formats CFBD period into clean quarter number (1-4, or OT)."""
    try:
        p = int(float(period_val))
        return p if p <= 4 else f"OT{p - 4}"
    except (ValueError, TypeError):
        return "N/A"

def format_running_score(row, offense_key, off_score_key, def_score_key, away_team, home_team):
    """Aligns CFBD offense_score/defense_score into consistent 'Away - Home' format."""
    if not off_score_key or not def_score_key:
        return "N/A"
    try:
        off_pts = int(float(row.get(off_score_key)))
        def_pts = int(float(row.get(def_score_key)))
    except (ValueError, TypeError):
        return "N/A"

    offense_team = str(row.get(offense_key, '')).strip() if offense_key else ""
    if offense_team.lower() == away_team.lower():
        away_pts, home_pts = off_pts, def_pts
    elif offense_team.lower() == home_team.lower():
        home_pts, away_pts = off_pts, def_pts
    else:
        return f"{off_pts} - {def_pts}"

    return f"{away_team} {away_pts} - {home_team} {home_pts}"

def render_hierarchy_selector(df_games, selected_year: int, key_prefix="nav"):
    """Reusable 3-column Conference -> Team -> Game hierarchy selector."""
    cols = df_games.columns.tolist()
    home_conf_key = next((c for c in cols if 'conference' in c.lower() and 'home' in c.lower()), None)
    home_team_key = next((c for c in cols if 'home_team' in c.lower() or 'hometeam' in c.lower()), 'home_team')
    away_team_key = next((c for c in cols if 'away_team' in c.lower() or 'awayteam' in c.lower()), 'away_team')
    home_pts_key = next((c for c in cols if 'home_points' in c.lower() or 'homepoints' in c.lower()), 'home_points')
    away_pts_key = next((c for c in cols if 'away_points' in c.lower() or 'awaypoints' in c.lower()), 'away_points')
    season_type_key = next((c for c in cols if 'season_type' in c.lower() or 'seasontype' in c.lower()), None)

    df_games = df_games.copy()
    df_games['raw_home_pts'] = pd.to_numeric(df_games[home_pts_key], errors='coerce')
    df_games['raw_away_pts'] = pd.to_numeric(df_games[away_pts_key], errors='coerce')
    df_games['home_pts'] = df_games['raw_home_pts'].fillna(0).astype(int)
    df_games['away_pts'] = df_games['raw_away_pts'].fillna(0).astype(int)

    st.subheader(f"🛠️ {selected_year} Hierarchy Selection Panel")
    col_conf, col_team, col_game = st.columns(3)

    with col_conf:
        if home_conf_key:
            conf_list = sorted(df_games[home_conf_key].dropna().unique().tolist())
            default_idx = conf_list.index("SEC") if "SEC" in conf_list else 0
            selected_conf = st.selectbox("1️⃣ Select Conference:", conf_list, index=default_idx, key=f"{key_prefix}_{selected_year}_conf")
        else:
            selected_conf = "SEC"

    teams_in_conf = get_teams_by_conference(df_games, selected_conf)
    with col_team:
        if teams_in_conf:
            selected_team = st.selectbox("2️⃣ Select Team:", teams_in_conf, key=f"{key_prefix}_{selected_year}_team")
        else:
            all_teams = sorted(df_games[home_team_key].dropna().unique().tolist())
            selected_team = st.selectbox("2️⃣ Select Team:", all_teams, key=f"{key_prefix}_{selected_year}_team")

    schedule_df = get_team_schedule(df_games, selected_team)

    game_options = {}
    for _, r in schedule_df.iterrows():
        g_id = r.get('id')
        wk = r.get('week', 1)
        ht = r.get(home_team_key, 'Unknown')
        at = r.get(away_team_key, 'Unknown')
        is_completed = pd.notna(r.get('raw_home_pts')) and pd.notna(r.get('raw_away_pts'))
        hp = int(r.get('home_pts', 0))
        ap = int(r.get('away_pts', 0))
        
        s_type = str(r.get(season_type_key, 'regular')).lower() if season_type_key else 'regular'
        wk_prefix = "Postseason" if s_type == "postseason" else f"Week {wk}"

        if is_completed:
            label = f"{wk_prefix}: {at} ({ap}) @ {ht} ({hp})"
        else:
            label = f"{wk_prefix}: {at} @ {ht} (Scheduled)"
        game_options[label] = (g_id, wk, ht, at, hp, ap, is_completed)

    with col_game:
        if game_options:
            selected_game_label = st.selectbox("3️⃣ Select Game from Schedule:", list(game_options.keys()), key=f"{key_prefix}_{selected_year}_game")
            g_id, wk, ht, at, hp, ap, is_completed = game_options[selected_game_label]
            return selected_team, g_id, wk, ht, at, hp, ap, is_completed
        else:
            st.warning("No games found for this team.")
            st.stop()

# --- IMPACT PLAY CLASSIFIER & ROW HIGHLIGHTER ---
def classify_impact_play(row, p_type_key, text_key, scoring_key):
    """Identifies Touchdowns, Field Goals, and Turnovers from CFBD play telemetry."""
    p_type = str(row.get(p_type_key, '')).lower()
    p_text = str(row.get(text_key, '')).lower()
    is_scoring = bool(row.get(scoring_key, False)) if scoring_key else False

    turnover_keywords = ['interception', 'intercepted', 'fumble recovery', 'fumbles, recovered', 'turnover on downs']
    is_turnover = any(k in p_type or k in p_text for k in turnover_keywords)

    is_td = 'touchdown' in p_type or 'touchdown' in p_text or (is_scoring and 'field goal' not in p_type and 'safety' not in p_type)
    is_fg = ('field goal good' in p_type) or (is_scoring and 'field goal' in p_type) or ('field goal' in p_text and 'is good' in p_text)

    if is_turnover and is_td:
        return "🚨🏆 DEF/ST TD"
    elif is_turnover:
        return "🚨 TURNOVER"
    elif is_td:
        return "🏆 TOUCHDOWN"
    elif is_fg:
        return "🎯 FIELD GOAL"
    return "Standard"

def style_impact_rows(row):
    """Applies high-contrast row tinting in dark mode for scoring plays and turnovers."""
    impact = row.get("Impact Play", "Standard")
    if "TOUCHDOWN" in impact or "DEF/ST TD" in impact:
        return ['background-color: rgba(16, 185, 129, 0.24); color: #ecfdf5; font-weight: 600;'] * len(row)
    elif "FIELD GOAL" in impact:
        return ['background-color: rgba(245, 158, 11, 0.22); color: #fffbeb; font-weight: 600;'] * len(row)
    elif "TURNOVER" in impact:
        return ['background-color: rgba(239, 68, 68, 0.24); color: #fef2f2; font-weight: 600;'] * len(row)
    return [''] * len(row)

def build_plays_grid(df_plays, limit_plays=None, offense_filter="All Offenses", down_filter="All Downs", impact_filter="All Plays", away_team="", home_team=""):
    """Processes raw play-by-play DataFrame into chronologically sorted grid with Quarter, Time, and Score columns."""
    play_cols = df_plays.columns.tolist()
    offense_key = next((c for c in play_cols if c.lower() in ['offense', 'offense_team', 'offenseteam']), None)
    p_type_key = next((c for c in play_cols if 'play_type' in c.lower() or 'playtype' in c.lower()), 'play_type')
    down_key = next((c for c in play_cols if c.lower() == 'down'), 'down')
    distance_key = next((c for c in play_cols if c.lower() == 'distance'), 'distance')
    yards_key = next((c for c in play_cols if 'yards_gained' in c.lower() or 'yardsgained' in c.lower()), 'yards_gained')
    text_key = next((c for c in play_cols if 'play_text' in c.lower() or 'playtext' in c.lower()), 'play_text')
    scoring_key = next((c for c in play_cols if c.lower() == 'scoring'), None)
    period_key = next((c for c in play_cols if c.lower() in ['period', 'quarter']), None)
    clock_key = next((c for c in play_cols if c.lower() == 'clock'), None)
    drive_num_key = next((c for c in play_cols if c.lower() in ['drive_number', 'drivenumber']), None)
    play_num_key = next((c for c in play_cols if c.lower() in ['play_number', 'playnumber']), None)
    id_key = next((c for c in play_cols if c.lower() == 'id'), None)
    off_score_key = next((c for c in play_cols if c.lower() in ['offense_score', 'offensescore']), None)
    def_score_key = next((c for c in play_cols if c.lower() in ['defense_score', 'defensescore']), None)

    df_plays = df_plays.copy()

    # --- CHRONOLOGICAL SORTING (Quarter ASC -> Clock Seconds DESC -> Drive/Play Sequence ASC) ---
    df_plays['_sort_period'] = pd.to_numeric(df_plays[period_key], errors='coerce').fillna(99) if period_key else 99
    df_plays['_sort_clock'] = df_plays[clock_key].apply(clock_to_seconds) if clock_key else -1
    df_plays['_sort_drive'] = pd.to_numeric(df_plays[drive_num_key], errors='coerce').fillna(9999) if drive_num_key else 9999
    df_plays['_sort_play'] = pd.to_numeric(df_plays[play_num_key], errors='coerce').fillna(9999) if play_num_key else 9999
    df_plays['_sort_id'] = pd.to_numeric(df_plays[id_key], errors='coerce').fillna(0) if id_key else 0

    df_plays = df_plays.sort_values(
        by=['_sort_period', '_sort_clock', '_sort_drive', '_sort_play', '_sort_id'],
        ascending=[True, False, True, True, True]
    ).reset_index(drop=True)

    df_plays['Quarter'] = df_plays[period_key].apply(format_quarter) if period_key else "N/A"
    df_plays['Time'] = df_plays[clock_key].apply(format_play_clock) if clock_key else "N/A"
    df_plays['Score'] = df_plays.apply(
        lambda r: format_running_score(r, offense_key, off_score_key, def_score_key, away_team, home_team),
        axis=1
    )

    df_plays['clean_down'] = pd.to_numeric(df_plays[down_key], errors='coerce').fillna(0).astype(int)
    df_plays['clean_dist'] = pd.to_numeric(df_plays[distance_key], errors='coerce').fillna(0).astype(int)
    df_plays['clean_yds'] = pd.to_numeric(df_plays[yards_key], errors='coerce').fillna(0).astype(int)

    df_plays['Impact Play'] = df_plays.apply(
        lambda r: classify_impact_play(r, p_type_key, text_key, scoring_key), axis=1
    )

    df_plays['play_category'] = df_plays[p_type_key].apply(
        lambda x: 'Pass' if 'pass' in str(x).lower() or 'incomplete' in str(x).lower() 
        else ('Run' if 'rush' in str(x).lower() or 'run' in str(x).lower() 
        else ('Special Teams' if 'field goal' in str(x).lower() or 'punt' in str(x).lower() or 'kickoff' in str(x).lower() else 'Other'))
    )

    df_plays = df_plays[(df_plays['clean_down'] > 0) | (df_plays['Impact Play'] != "Standard")]

    if offense_key and offense_filter != "All Offenses":
        df_plays = df_plays[df_plays[offense_key] == offense_filter]
        
    if down_filter != "All Downs":
        target_down_int = int(down_filter.split()[0][0])
        df_plays = df_plays[df_plays['clean_down'] == target_down_int]

    if impact_filter == "Impact Plays Only (TDs, FGs, Turnovers)":
        df_plays = df_plays[df_plays['Impact Play'] != "Standard"]
    elif impact_filter == "Scoring Plays Only":
        df_plays = df_plays[df_plays['Impact Play'].str.contains("TOUCHDOWN|FIELD GOAL|DEF/ST TD")]
    elif impact_filter == "Turnovers Only":
        df_plays = df_plays[df_plays['Impact Play'].str.contains("TURNOVER|DEF/ST TD")]

    def evaluate_play_success(r):
        dn, ds, yd = r['clean_down'], r['clean_dist'], r['clean_yds']
        if dn == 1:   return yd >= (0.50 * ds)
        elif dn == 2: return yd >= (0.70 * ds)
        elif dn in [3, 4]: return yd >= ds
        return "TOUCHDOWN" in r['Impact Play'] or "FIELD GOAL" in r['Impact Play']

    df_plays['is_success'] = df_plays.apply(evaluate_play_success, axis=1)
    df_plays['is_explosive'] = (
        ((df_plays['play_category'] == 'Pass') & (df_plays['clean_yds'] >= 15)) |
        ((df_plays['play_category'] == 'Run') & (df_plays['clean_yds'] >= 10))
    )

    metrics = {
        "total": len(df_plays),
        "success_count": int(df_plays['is_success'].sum()) if len(df_plays) > 0 else 0,
        "explosive_count": int(df_plays['is_explosive'].sum()) if len(df_plays) > 0 else 0,
        "td_count": int(df_plays['Impact Play'].str.contains("TOUCHDOWN|DEF/ST TD").sum()) if len(df_plays) > 0 else 0,
        "fg_count": int(df_plays['Impact Play'].str.contains("FIELD GOAL").sum()) if len(df_plays) > 0 else 0,
        "to_count": int(df_plays['Impact Play'].str.contains("TURNOVER|DEF/ST TD").sum()) if len(df_plays) > 0 else 0,
    }

    if len(df_plays) == 0:
        return pd.DataFrame(), metrics

    sliced_plays = df_plays if limit_plays is None else df_plays.head(limit_plays)
    display_plays = sliced_plays.copy().reset_index(drop=True)
    display_plays['Success Status'] = display_plays['is_success'].apply(lambda x: "Yes" if x else "No")
    display_plays['Explosive Play'] = display_plays['is_explosive'].apply(lambda x: "Yes" if x else "No")

    display_cols = ['Quarter', 'Time', 'Score', 'Impact Play', 'play_category', 'clean_down', 'clean_dist', 'clean_yds', 'Success Status', 'Explosive Play', text_key]
    col_names = ["Quarter", "Time", "Score", "Impact Play", "Play Category", "Down", "Distance", "Yards Gained", "Success Status", "Explosive Play", "Play Description"]
    
    if offense_key:
        display_cols.insert(3, offense_key)
        col_names.insert(3, "Offense")

    final_web_grid = display_plays[display_cols].copy()
    final_web_grid.columns = col_names
    return final_web_grid, metrics

# --- APP NAVIGATION SIDEBAR ---
st.sidebar.title("🏈 Navigation Matrix")

selected_season = st.sidebar.selectbox(
    "📅 Select CFB Season:",
    AVAILABLE_SEASONS,
    index=0  # Defaults to current 2026 season
)

st.sidebar.divider()

app_mode = st.sidebar.radio(
    "Select Analytics ViewProfile:", 
    ["Single Game Inspector", "Game Analysis Engine", "Play Scouting Engine"]
)

# =====================================================================
# VIEW PANEL 1: SINGLE GAME INSPECTOR
# =====================================================================
if app_mode == "Single Game Inspector":
    st.title(f"🔍 {selected_season} CFB Single Game Box Score Inspector")
    st.markdown(f"Drill down through **Conference ➔ Team ➔ Schedule** to view full **{selected_season}** match statistics, statistical leaders, and timestamped plays.")

    with st.spinner(f"Loading {selected_season} season schedule..."):
        df_games = load_game_data(selected_season)

    if df_games.empty:
        st.error(f"Could not load game records for the {selected_season} season.")
    else:
        selected_team, selected_game_id, selected_week, home_team, away_team, home_score, away_score, is_completed = render_hierarchy_selector(
            df_games, selected_year=selected_season, key_prefix="box"
        )

        # --- SCOREBOARD DISPLAY BANNER ---
        st.divider()
        sc1, sc2, sc3 = st.columns([2, 1, 2])
        
        with sc1:
            st.metric(label=f"Away: {away_team}", value=f"{away_score} Pts" if is_completed else "Scheduled")
        with sc2:
            st.markdown("<h2 style='text-align: center; margin-top: 10px;'>VS</h2>", unsafe_allow_html=True)
        with sc3:
            st.metric(label=f"Home: {home_team}", value=f"{home_score} Pts" if is_completed else "Scheduled")

        if not is_completed:
            st.info(f"📅 This {selected_season} matchup ({away_team} @ {home_team}) has not been played yet. Box score, player leaders, and play-by-play telemetry will populate once the game is underway or completed.")
        else:
            # --- DETAILED BOX SCORE TELEMETRY ---
            st.subheader("📊 Official Team Box Score Telemetry")
            st.caption("🟩 **Green Highlight** indicates the statistical advantage in that category (lower is better for Turnovers).")
            
            with st.spinner(f"Fetching box score metrics for {selected_team} ({selected_season})..."):
                box_data = parse_game_box_stats(game_id=selected_game_id, team_name=selected_team, year=selected_season)

            if box_data:
                metric_definitions = [
                    ("Total Yards", ["totalYards", "total_yards", "tot_yds"]),
                    ("Passing Yards", ["netPassingYards", "net_passing_yards", "passingYards"]),
                    ("Rushing Yards", ["rushingYards", "rushing_yards", "rushYards"]),
                    ("First Downs", ["firstDowns", "first_downs"]),
                    ("Turnovers", ["turnovers", "total_turnovers"]),
                    ("3rd Down Conversions", ["thirdDownEff", "third_down_eff"]),
                    ("Completions / Attempts", ["completionAttempts", "completion_attempts"])
                ]

                away_dict = box_data.get(away_team, {})
                home_dict = box_data.get(home_team, {})

                table_rows = []
                for label, keys in metric_definitions:
                    away_val = extract_stat_value(away_dict, keys)
                    home_val = extract_stat_value(home_dict, keys)
                    table_rows.append({"Metric": label, away_team: away_val, home_team: home_val})

                comparison_df = pd.DataFrame(table_rows)
                styled_comparison = comparison_df.style.apply(
                    lambda r: style_box_score_winner(r, away_team, home_team), axis=1
                )
                st.dataframe(styled_comparison, width="stretch", hide_index=True)
            else:
                st.info("Detailed box score stats are currently unavailable or not yet published for this game.")

            # --- INDIVIDUAL STATISTICAL LEADERS (PASSING, RUSHING, RECEIVING) ---
            st.divider()
            st.subheader("🌟 Individual Statistical Leaders")
            st.caption("Top yardage performer per team in Passing, Rushing, and Receiving (🟩 highlights the higher yardage total).")
            
            with st.spinner(f"Loading individual player leaders for {away_team} @ {home_team}..."):
                leaders_data = parse_game_player_leaders(game_id=selected_game_id, team_name=selected_team, year=selected_season)

            if leaders_data:
                away_leaders = leaders_data.get(away_team, {})
                home_leaders = leaders_data.get(home_team, {})

                leader_categories = [
                    ("🎯 Passing Yards Leader", "passing"),
                    ("🏃 Rushing Yards Leader", "rushing"),
                    ("🙌 Receiving Yards Leader", "receiving"),
                ]

                leader_rows = []
                away_yards_list = []
                home_yards_list = []

                for label, cat_key in leader_categories:
                    a_entry = away_leaders.get(cat_key)
                    h_entry = home_leaders.get(cat_key)

                    leader_rows.append({
                        "Category": label,
                        away_team: a_entry["summary"] if a_entry else "N/A",
                        home_team: h_entry["summary"] if h_entry else "N/A",
                    })
                    away_yards_list.append(a_entry["yards"] if a_entry else None)
                    home_yards_list.append(h_entry["yards"] if h_entry else None)

                leaders_df = pd.DataFrame(leader_rows)
                styled_leaders = leaders_df.style.apply(
                    lambda r: style_leader_winner(r, away_team, home_team, away_yards_list, home_yards_list),
                    axis=1
                )
                st.dataframe(styled_leaders, width="stretch", hide_index=True)
            else:
                st.info("Individual player box score stats are not available for this game.")

            # --- GAME PLAY-BY-PLAY LOG (CHRONOLOGICAL WITH QUARTER, TIME & RUNNING SCORE) ---
            st.divider()
            st.subheader("⏱️ Game Play-by-Play Log")
            with st.spinner(f"Loading play-by-play log for {away_team} @ {home_team}..."):
                df_game_plays = get_game_plays_df(game_id=selected_game_id, week=selected_week, team_name=selected_team, year=selected_season)

            if not df_game_plays.empty:
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    box_impact_filter = st.selectbox(
                        "Filter Plays:", 
                        ["All Plays", "Impact Plays Only (TDs, FGs, Turnovers)", "Scoring Plays Only", "Turnovers Only"],
                        key="box_play_filter"
                    )
                with f_col2:
                    box_show_all = st.checkbox("Show All Plays (Max)", value=True, key="box_show_all")
                    box_play_limit = st.slider(
                        "Plays to Display:", 
                        min_value=10, 
                        max_value=500, 
                        value=500, 
                        step=10, 
                        disabled=box_show_all,
                        key="box_play_limit"
                    )

                st.caption("🎨 **Row Highlight Legend:** 🟩 **Green** = Touchdown | 🟨 **Gold** = Field Goal | 🟥 **Red** = Turnover")
                plays_grid, box_metrics = build_plays_grid(
                    df_game_plays, 
                    limit_plays=None if box_show_all else box_play_limit, 
                    impact_filter=box_impact_filter,
                    away_team=away_team, 
                    home_team=home_team
                )
                if not plays_grid.empty:
                    st.caption(f"Showing **{len(plays_grid)}** of **{box_metrics['total']}** total plays (Chronological Order).")
                    st.dataframe(plays_grid.style.apply(style_impact_rows, axis=1), width="stretch", hide_index=True)
                else:
                    st.info("No plays match the selected filter.")
            else:
                st.info("Play-by-play telemetry is not available for this matchup.")

# =====================================================================
# VIEW PANEL 2: GAME ANALYSIS ENGINE
# =====================================================================
elif app_mode == "Game Analysis Engine":
    st.title(f"📊 {selected_season} Season Game Analysis Engine")
    st.markdown(f"Evaluates **{selected_season}** schedule margins, scoring profiles, and conference field metrics.")
    
    with st.spinner(f"Loading {selected_season} season records..."):
        df_games = load_game_data(selected_season)
    
    if df_games.empty:
        st.error(f"Could not load game records for the {selected_season} season.")
    else:
        cols = df_games.columns.tolist()
        home_team_key = next((c for c in cols if 'home_team' in c.lower() or 'hometeam' in c.lower()), 'home_team')
        away_team_key = next((c for c in cols if 'away_team' in c.lower() or 'awayteam' in c.lower()), 'away_team')
        home_pts_key = next((c for c in cols if 'home_points' in c.lower() or 'homepoints' in c.lower()), 'home_points')
        away_pts_key = next((c for c in cols if 'away_points' in c.lower() or 'awaypoints' in c.lower()), 'away_points')
        home_conf_key = next((c for c in cols if 'conference' in c.lower() and 'home' in c.lower()), None)

        df_games['raw_home_pts'] = pd.to_numeric(df_games[home_pts_key], errors='coerce')
        df_games['raw_away_pts'] = pd.to_numeric(df_games[away_pts_key], errors='coerce')
        completed_games = df_games.dropna(subset=['raw_home_pts', 'raw_away_pts']).copy()

        completed_games['home_pts'] = completed_games['raw_home_pts'].astype(int)
        completed_games['away_pts'] = completed_games['raw_away_pts'].astype(int)
        completed_games['total_points'] = completed_games['home_pts'] + completed_games['away_pts']
        completed_games['margin'] = (completed_games['home_pts'] - completed_games['away_pts']).abs()

        st.subheader("🛠️ Strategy Filtering Panel")
        col1, col2 = st.columns(2)
        
        with col1:
            if home_conf_key:
                conf_list = sorted(completed_games[home_conf_key].dropna().unique().tolist())
                default_idx = conf_list.index("SEC") if "SEC" in conf_list else 0
                selected_conf = st.selectbox("Select FBS Conference to Isolate:", conf_list, index=default_idx)
                filtered_df = completed_games[completed_games[home_conf_key] == selected_conf]
            else:
                st.warning("Conference fields missing from dataset layout.")
                filtered_df = completed_games
                
        with col2:
            display_limit = st.slider("Maximum Match Records to Output:", min_value=5, max_value=100, value=25, step=5)

        total_games = len(filtered_df)
        if total_games > 0:
            avg_margin = filtered_df['margin'].mean()
            tight_games = (filtered_df['margin'] <= 7).sum()

            st.subheader("📈 Performance Benchmarks")
            m1, m2, m3 = st.columns(3)
            m1.metric("Completed Games", f"{total_games} Games")
            m2.metric("Average Scoring Margin", f"{avg_margin:.1f} Pts")
            m3.metric("One-Score Game Rate", f"{(tight_games/total_games)*100:.1f}%")

            st.subheader(f"📋 Top {display_limit} Match Records Matrix")
            report_df = filtered_df.head(display_limit).copy()
            report_df['Explosive'] = report_df['total_points'].apply(lambda x: "Yes" if x >= 60 else "No")
            
            display_df = report_df[[home_team_key, away_team_key, 'home_pts', 'away_pts', 'total_points', 'margin', 'Explosive']].copy()
            display_df.columns = ["Home Team", "Away Team", "Home Points", "Away Points", "Total Points", "Scoring Margin", "Explosive"]
            st.dataframe(display_df, width="stretch", hide_index=True)
        else:
            st.warning(f"Zero completed game records found for {selected_season} under the selected conference criteria.")

# =====================================================================
# VIEW PANEL 3: PLAY SCOUTING ENGINE (2020-2026 SEASONS)
# =====================================================================
else:
    st.title(f"🏈 {selected_season} Down & Distance Play Scouting Engine")
    st.markdown(f"Drill down through **Conference ➔ Team ➔ Schedule** to evaluate situational play-by-play telemetry across any **{selected_season}** matchup.")
    
    with st.spinner(f"Loading {selected_season} season schedule..."):
        df_games = load_game_data(selected_season)
    
    if df_games.empty:
        st.error(f"Could not load game records for the {selected_season} season.")
    else:
        selected_team, selected_game_id, selected_week, home_team, away_team, home_score, away_score, is_completed = render_hierarchy_selector(
            df_games, selected_year=selected_season, key_prefix="plays"
        )

        st.divider()
        if not is_completed:
            st.info(f"📅 This {selected_season} matchup ({away_team} @ {home_team}) has not been played yet. Play-by-play telemetry will appear once the game begins.")
        else:
            with st.spinner(f"Loading play-by-play telemetry for {away_team} @ {home_team} ({selected_season})..."):
                df_plays = get_game_plays_df(game_id=selected_game_id, week=selected_week, team_name=selected_team, year=selected_season)

            if df_plays.empty:
                st.warning(f"No play-by-play data available for {away_team} @ {home_team} ({selected_season}).")
            else:
                st.subheader("🛠️ Play Analytics Slicing Panel")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    offense_options = ["All Offenses", away_team, home_team]
                    selected_offense = st.selectbox("Offensive Unit:", offense_options)
                with col2:
                    selected_down = st.selectbox("Down Profile:", ["All Downs", "1st Down", "2nd Down", "3rd Down", "4th Down"])
                with col3:
                    impact_filter = st.selectbox("Impact Play Filter:", ["All Plays", "Impact Plays Only (TDs, FGs, Turnovers)", "Scoring Plays Only", "Turnovers Only"])
                with col4:
                    show_all_plays = st.checkbox("Show All Plays (Max)", value=True, key="scouting_show_all")
                    limit_plays = st.slider(
                        "Max Plays:", 
                        min_value=10, 
                        max_value=500, 
                        value=500, 
                        step=10,
                        disabled=show_all_plays
                    )

                final_web_grid, metrics = build_plays_grid(
                    df_plays,
                    limit_plays=None if show_all_plays else limit_plays,
                    offense_filter=selected_offense,
                    down_filter=selected_down,
                    impact_filter=impact_filter,
                    away_team=away_team,
                    home_team=home_team
                )

                total_p_count = metrics["total"]
                if total_p_count > 0:
                    success_count = metrics["success_count"]
                    success_rate = (success_count / total_p_count) * 100

                    st.subheader("📋 Film Room Metrics")
                    p1, p2, p3, p4 = st.columns(4)
                    p1.metric("Situational Success Rate", f"{success_rate:.1f}%", f"{success_count}/{total_p_count} Plays")
                    p2.metric("Explosive Chunk Plays", f"{metrics['explosive_count']} Plays")
                    p3.metric("Scoring Plays (TD / FG)", f"{metrics['td_count']} TDs | {metrics['fg_count']} FGs")
                    p4.metric("Turnovers Forced / Lost", f"{metrics['to_count']} Turnovers")

                    st.caption("🎨 **Row Highlight Legend:** 🟩 **Green** = Touchdown | 🟨 **Gold** = Field Goal | 🟥 **Red** = Turnover")
                    
                    header_label = f"All {total_p_count} Plays" if show_all_plays else f"Top {len(final_web_grid)} of {total_p_count} Plays"
                    st.subheader(f"📋 Down-by-Down Inspection Log ({header_label} — Chronological)")

                    styled_grid = final_web_grid.style.apply(style_impact_rows, axis=1)
                    st.dataframe(styled_grid, width="stretch", hide_index=True)
                else:
                    st.warning("No tracking data available for the chosen filter criteria.")