import os
import json
import pandas as pd
import streamlit as st

# --- PAGE INITIALIZATION LAYOUT ---
st.set_page_config(page_title="GridironMetrics CFB Dashboard", page_icon="🏈", layout="wide")

# --- CONSOLIDATED BACKEND DATA LOADERS ---
def load_game_data():
    if os.path.exists('records_2025.json'):
        with open('records_2025.json', 'r', encoding='utf-8') as f:
            return pd.DataFrame(json.load(f))
    return pd.DataFrame()

def load_mock_play_data():
    return pd.DataFrame([
        {"play_type": "Run", "down": 1, "distance": 10, "yards_gained": 6, "yard_line": 75},   
        {"play_type": "Run", "down": 1, "distance": 10, "yards_gained": 2, "yard_line": 69},   
        {"play_type": "Pass", "down": 1, "distance": 10, "yards_gained": 12, "yard_line": 45}, 
        {"play_type": "Pass", "down": 2, "distance": 8, "yards_gained": 3, "yard_line": 33},   
        {"play_type": "Pass", "down": 3, "distance": 4, "yards_gained": 16, "yard_line": 16}, 
        {"play_type": "Run", "down": 4, "distance": 2, "yards_gained": 1, "yard_line": 2}  
    ])

# --- APP NAVIGATION SIDEBAR ---
st.sidebar.title("🏈 Navigation Matrix")
app_mode = st.sidebar.radio("Select Analytics ViewProfile:", ["Game Analysis Engine", "Play Scouting Engine"])

# =====================================================================
# VIEW PANEL 1: GAME ANALYSIS ENGINE
# =====================================================================
if app_mode == "Game Analysis Engine":
    st.title("📊 2025 Regular Season Game Analysis Engine")
    st.markdown("Evaluates schedule margins, scoring profiles, and conference field metrics.")
    
    df_games = load_game_data()
    
    if df_games.empty:
        st.error("Missing raw file 'records_2025.json'. Run ingest.py inside your terminal panel first!")
    else:
        # --- FIXED: BULLETPROOF DYNAMIC KEY HUNTER ---
        cols = df_games.columns.tolist()
        home_team_key = next((c for c in cols if 'home_team' in c.lower() or 'hometeam' in c.lower()), 'home_team')
        away_team_key = next((c for c in cols if 'away_team' in c.lower() or 'awayteam' in c.lower()), 'away_team')
        home_pts_key = next((c for c in cols if 'home_points' in c.lower() or 'homepoints' in c.lower()), '_home_points')
        away_pts_key = next((c for c in cols if 'away_points' in c.lower() or 'awaypoints' in c.lower()), '_away_points')
        home_conf_key = next((c for c in cols if 'conference' in c.lower() and 'home' in c.lower()), None)

        # Map scores cleanly using the dynamically extracted keys
        df_games['home_pts'] = pd.to_numeric(df_games[home_pts_key], errors='coerce').fillna(0).astype(int)
        df_games['away_pts'] = pd.to_numeric(df_games[away_pts_key], errors='coerce').fillna(0).astype(int)
        df_games['total_points'] = df_games['home_pts'] + df_games['away_pts']
        df_games['margin'] = (df_games['home_pts'] - df_games['away_pts']).abs()

        # --- INTERACTIVE WEB CONTROLS ---
        st.subheader("🛠️ Strategy Filtering Panel")
        col1, col2 = st.columns(2)
        
        with col1:
            if home_conf_key:
                conf_list = sorted(df_games[home_conf_key].dropna().unique().tolist())
                selected_conf = st.selectbox("Select FBS Conference to Isolate:", conf_list)
                filtered_df = df_games[df_games[home_conf_key] == selected_conf]
            else:
                st.warning("Conference fields missing from dataset layout.")
                filtered_df = df_games
                
        with col2:
            display_limit = st.slider("Maximum Match Records to Output:", min_value=5, max_value=50, value=20, step=5)

        # --- RUN ENGINE METRICS INTERNALLY ---
        total_games = len(filtered_df)
        if total_games > 0:
            avg_margin = filtered_df['margin'].mean()
            explosive_games = (filtered_df['total_points'] >= 60).sum()
            tight_games = (filtered_df['margin'] <= 7).sum()

            # --- VISUAL WEB METRIC CARDS ---
            st.subheader("📈 Performance Benchmarks")
            m1, m2, m3 = st.columns(3)
            m1.metric("Dataset Row Count", f"{total_games} Games")
            m2.metric("Average Scoring Margin", f"{avg_margin:.1f} Pts")
            m3.metric("One-Score Game Rate", f"{(tight_games/total_games)*100:.1f}%")

                       # --- RENDER WEB COMPLIANT DATA REPORT ---
            st.subheader(f"📋 Top {display_limit} Match Records Matrix")
            
            report_df = filtered_df.head(display_limit).copy()
            report_df['Explosive'] = report_df['total_points'].apply(lambda x: "Yes" if x >= 60 else "No")
            
            # 1. Create a safe subset dataframe using the exact variable names
            display_df = report_df[[home_team_key, away_team_key, 'home_pts', 'away_pts', 'total_points', 'margin', 'Explosive']].copy()
            
            # 2. FORCE RENAME: Hardcode index values to drop raw text variables completely
            display_df.columns = [
                "Home Team", 
                "Away Team", 
                "Home Points", 
                "Away Points", 
                "Total Points", 
                "Scoring Margin", 
                "Explosive"
            ]
            
            # Render the updated table cleanly to the web dashboard interface
            st.dataframe(display_df, use_container_width=True)

            st.dataframe(report_df[[home_team_key, away_team_key, 'home_pts', 'away_pts', 'total_points', 'margin', 'Explosive']], use_container_width=True)
        else:
            st.warning("Zero game records found for the selected conference criteria.")

# =====================================================================
# VIEW PANEL 2: PLAY SCOUTING ENGINE
# =====================================================================
else:
    st.title("🏈 Down & Distance Play Scouting Engine")
    st.markdown("Isolates situational play telemetry success rates and explosive down tracking profiles.")
    
    df_plays = load_mock_play_data()
    
    def evaluate_play_success(r):
        down, dist, yds = int(r['down']), int(r['distance']), int(r['yards_gained'])
        if down == 1:   return yds >= (0.50 * dist)
        elif down == 2: return yds >= (0.70 * dist)
        return yds >= dist

    df_plays['is_success'] = df_plays.apply(evaluate_play_success, axis=1)
    df_plays['is_explosive'] = (
        ((df_plays['play_type'] == 'Pass') & (df_plays['yards_gained'] >= 15)) |
        ((df_plays['play_type'] == 'Run') & (df_plays['yards_gained'] >= 10))
    )

    # --- PERFORMANCE STATISTICS PANELS ---
    total_p = len(df_plays)
    success_rate = (df_plays['is_success'].sum() / total_p) * 100
    explosive_count = df_plays['is_explosive'].sum()

    p1, p2 = st.columns(2)
    p1.metric("Situational Success Velocity", f"{success_rate:.1f}%")
    p2.metric("Explosive Plays Tracked", f"{explosive_count} Plays")

    st.subheader("📋 Detailed Down-by-Down Inspection Log")
    
    # Enforces your preferred capitalized "Down" formatting preference across columns
    display_plays = df_plays.copy()
    display_plays['Success Status'] = display_plays['is_success'].apply(lambda x: "Yes" if x else "No")
    display_plays['Explosive Play'] = display_plays['is_explosive'].apply(lambda x: "Yes" if x else "No")
    display_plays.columns = ['Play Type', 'Down', 'Distance', 'Yards Gained', 'Yard Line', 'is_success', 'is_explosive', 'Success Status', 'Explosive Play']
    
    st.dataframe(display_plays[['Play Type', 'Down', 'Distance', 'Yards Gained', 'Yard Line', 'Success Status', 'Explosive Play']], use_container_width=True)
