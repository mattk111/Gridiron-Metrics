import json
import os
import pandas as pd

def load_raw_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing live data file at: {filepath}. Run ingest.py first!")
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return pd.DataFrame(data)

def calculate_coaching_metrics(df):
    processed_df = df.copy()
    cols = processed_df.columns.tolist()
    
    # DYNAMIC KEY HUNTER: Finds the fields regardless of library casing/underscore variations
    home_team_key = next((c for c in cols if 'home_team' in c.lower() or 'hometeam' in c.lower()), 'home_team')
    away_team_key = next((c for c in cols if 'away_team' in c.lower() or 'awayteam' in c.lower()), 'away_team')
    home_pts_key = next((c for c in cols if 'home_points' in c.lower() or 'homepoints' in c.lower()), 'home_points')
    away_pts_key = next((c for c in cols if 'away_points' in c.lower() or 'awaypoints' in c.lower()), 'away_points')

    # Convert the located keys to clean numeric columns
    processed_df['home_pts'] = pd.to_numeric(processed_df[home_pts_key], errors='coerce').fillna(0).astype(int)
    processed_df['away_pts'] = pd.to_numeric(processed_df[away_pts_key], errors='coerce').fillna(0).astype(int)

    # --- METRIC 1: TOTAL POINTS SCORE TRACKER ---
    processed_df['total_points'] = processed_df['home_pts'] + processed_df['away_pts']
    processed_df['is_explosive_game'] = processed_df['total_points'] >= 60
    
    # --- METRIC 2: REAL MARGIN DIFFERENTIAL ---
    processed_df['margin'] = (processed_df['home_pts'] - processed_df['away_pts']).abs()
    
    print("\n--- Pipeline Transformation Matrix ---")
    print(f"Successfully loaded {len(processed_df)} raw 2025 game rows into DataFrame.")
    
    total_games = len(processed_df)
    if total_games == 0:
        print("No game logs found inside the data file.")
        return processed_df
        
    explosive_count = processed_df['is_explosive_game'].sum()
    explosive_pct = (explosive_count / total_games) * 100
    avg_margin = processed_df['margin'].mean()
    
    print(f"Dataset Average Scoring Margin: {avg_margin:.1f} points")
    print(f"Explosive Games (>=60 points):  {explosive_count} matches ({explosive_pct:.1f}% of season logs)")
    
    # --- RED ZONE / SITUATIONAL EFFICIENCY PROFILE ---
    print("\n--- Red Zone Execution Report ---")
    tight_games = processed_df[processed_df['margin'] <= 7]
    total_tight_games = len(tight_games)
    
    if total_tight_games > 0:
        tight_pct = (total_tight_games / total_games) * 100
        print(f"One-Score Game Rate:           {tight_pct:.1f}% ({total_tight_games}/{total_games} games decided inside 7 points)")
    else:
        print("No situational data available.")
        
    # --- METRIC 4: HOME FIELD WIN RATE COUNTER ---
    print("\n--- Coaching Tendency Breakdown ---")
    processed_df['home_won'] = processed_df['home_pts'] > processed_df['away_pts']
    home_wins = processed_df['home_won'].sum()
    home_win_pct = (home_wins / total_games) * 100
    print(f"Home Field Success Velocity:  Run: {home_win_pct:.1f}% ({home_wins} wins) | Pass: {100 - home_win_pct:.1f}% ({total_games - home_wins} losses)")
    
    # --- DETAILED PLAY INSPECTION LOG ---
    print("\n--- Detailed Play Inspection Log ---")
    sample_view = processed_df.head(len(processed_df)) # Evaluates whatever sub-slice limit the user set
    for index, r in sample_view.iterrows():
        home_team = r.get(home_team_key, 'Unknown')
        away_team = r.get(away_team_key, 'Unknown')
        
        # Enforcing "Yes" / "No" preferred styling formatting
        is_explosive_txt = "Yes" if r['is_explosive_game'] else "No"
        
        print(f"Game {index + 1}: {home_team} vs {away_team} | Score: {r['home_pts']}-{r['away_pts']} | Total: {r['total_points']} | Explosive: {is_explosive_txt}")
        
    return processed_df

if __name__ == "__main__":
    try:
        print("Initializing GridironMetrics-CFB Real-Data Engine...")
        real_data_path = 'records_2025.json' 
        
        live_df = load_raw_data(real_data_path)
        
        print("\n=============================================")
        print("🏈 CUSTOM FBS CONFERENCE FILTER TOOL")
        print("=============================================")
        
        user_conf = input("Enter FBS Conference to isolate (e.g. SEC, Big Ten, ACC, MAC): ").strip()
        
        try:
            user_limit = input("Enter the maximum number of games to display (e.g. 10, 20): ").strip()
            user_limit = int(user_limit)
        except ValueError:
            print("⚠️ Invalid number typed. Defaulting view profile to 20 games.")
            user_limit = 20

        # --- REVISED EXACT COLUMN MAPPING MATCH ---
        cols = live_df.columns.tolist()
        home_conf_key = next((c for c in cols if 'conference' in c.lower() and 'home' in c.lower()), None)
        away_conf_key = next((c for c in cols if 'conference' in c.lower() and 'away' in c.lower()), None)

        if home_conf_key and away_conf_key:
            # Clean string conversions to handle library variations safely
            live_df[home_conf_key] = live_df[home_conf_key].astype(str).str.strip().str.lower()
            live_df[away_conf_key] = live_df[away_conf_key].astype(str).str.strip().str.lower()
            
            target_search = user_conf.lower()
            
            # Filter rows where either conference column matches the typed search value
            filtered_df = live_df[
                (live_df[home_conf_key] == target_search) | 
                (live_df[away_conf_key] == target_search)
            ]
        else:
            print("⚠️ Conference identifiers missing from dataset columns. Processing global logs.")
            filtered_df = live_df

        # --- EXECUTE ENGINE LOGIC ---
        if len(filtered_df) == 0:
            print(f"\n❌ Zero records found matching the conference: '{user_conf}'.")
        else:
            print(f"\n✅ Successfully isolated {len(filtered_df)} matches involving the '{user_conf}'.")
            results = calculate_coaching_metrics(filtered_df.head(user_limit))
        
    except Exception as e:
        print(f"Pipeline Execution Error: {e}")
