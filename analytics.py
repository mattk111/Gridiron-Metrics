import json
import pandas as pd

def load_raw_data(filepath):
    # Open the raw JSON file and load it safely with correct encoding
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert the raw JSON lists into a standard Pandas DataFrame table
    return pd.DataFrame(data)

def calculate_coaching_metrics(df):
    # Copy the DataFrame to avoid modifying the original source data
    processed_df = df.copy()
    
    # --- METRIC 1: EXPLOSIVE PLAYS ---
    # Flag runs >= 10 yards and passes >= 15 yards based on coaching standards
    processed_df['is_explosive'] = (
        ((processed_df['play_type'] == 'Pass') & (processed_df['yards_gained'] >= 15)) |
        ((processed_df['play_type'] == 'Run') & (processed_df['yards_gained'] >= 10))
    )
    
    # --- METRIC 2: SITUATIONAL SUCCESS RATES ---
    # Apply special filters: 1st Down(>= 50%), 2nd Down(>=70&), 3rd/4th Down(100% Conversion)
    def evaluate_play_success(r):
        down = r['down']
        distance = r['distance']
        yards = r['yards_gained']
        
        if down == 1:   return yards >= (0.50 * distance)
        elif down == 2: return yards >= (0.70 * distance)
        elif down == 3: return yards >= distance
        elif down == 4: return yards >= distance
        return False

    # Map the calculation function across every single row in the data table
    processed_df['is_success'] = processed_df.apply(evaluate_play_success, axis=1)
    
    # --- METRIC 3: OPPONENT TALENT WEIGHTING ---
    # Multiply success (1 or 0) by the opponent's normalized talent rating scale
    processed_df['weighted_success'] = processed_df['is_success'].astype(int) * (processed_df['opponent_talent'] / 100.0)
    
    # Print status check to verify row counts match expected inputs
    print("\n--- Pipeline Transformation Matrix ---")
    print(f"Successfully loaded {len(processed_df)} raw play rows into DataFrame.")
    
    # Calculate overall pipeline performance benchmarks for quick logging
    total_plays = len(processed_df)
    raw_success_rate = (processed_df['is_success'].sum() / total_plays) * 100
    avg_weighted_success = processed_df['weighted_success'].mean() * 100
    explosive_count = processed_df['is_explosive'].sum()
    
    # FEATURE 1: EXPLOSIVE PLAY PERCENTAGE TRACKER
    explosive_pct = (explosive_count / total_plays) * 100
    
    print(f"Raw Success Rate:             {raw_success_rate:.1f}%")
    print(f"Talent-Adjusted Success Index: {avg_weighted_success:.1f}")
    print(f"Total Explosive Plays Created: {explosive_count} ({explosive_pct:.1f}% of total plays)")
    
    # FEATURE 2: RED ZONE EFFICIENCY FILTER
    print("\n--- Red Zone Execution Report ---")
    # Red Zone is defined as being on or inside the opponent's 20-yard line
    red_zone_plays = processed_df[processed_df['yard_line'] <= 20]
    total_rz_plays = len(red_zone_plays)
    
    if total_rz_plays > 0:
        rz_success_count = red_zone_plays['is_success'].sum()
        rz_success_rate = (rz_success_count / total_rz_plays) * 100
        print(f"Red Zone Success Rate:        {rz_success_rate:.1f}% ({rz_success_count}/{total_rz_plays} successful plays)")
    else:
        print("No Red Zone situational data available.")
    
    # --- METRIC 4: RUN/PASS TENDENCY COUNTER ---
    print("\n--- Coaching Tendency Breakdown ---")
    
    # Isolate 1st down plays specifically
    first_downs = processed_df[processed_df['down'] == 1]
    total_first_downs = len(first_downs)
    
    if total_first_downs > 0:
        run_count = (first_downs['play_type'] == 'Run').sum()
        pass_count = (first_downs['play_type'] == 'Pass').sum()
        print(f"1st Down Play-Calling: Run: {(run_count / total_first_downs) * 100:.1f}% ({run_count}) | Pass: {(pass_count / total_first_downs) * 100:.1f}% ({pass_count})")
    else:
        print("No 1st down situational data available.")
        
    # Isolate 3rd down plays specifically (The Money Down)
    third_downs = processed_df[processed_df['down'] == 3]
    total_third_downs = len(third_downs)
    
    if total_third_downs > 0:
        t_run_count = (third_downs['play_type'] == 'Run').sum()
        t_pass_count = (third_downs['play_type'] == 'Pass').sum()
        print(f"3rd Down Play-Calling: Run: {(t_run_count / total_third_downs) * 100:.1f}% ({t_run_count}) | Pass: {(t_pass_count / total_third_downs) * 100:.1f}% ({t_pass_count})")
    else:
        print("No 3rd down situational data available.")
    
    # --- DETAILED PLAY INSPECTION LOG ---
        # --- DETAILED PLAY INSPECTION LOG ---
    print("\n--- Detailed Play Inspection Log ---")
    for index, r in processed_df.iterrows():
        # Capitalized 'Down:' as requested
        print(f"Play {index + 1}: {r['play_type']} | Down: {r['down']} | Dist: {r['distance']} | Yds Gained: {r['yards_gained']} | Success: {r['is_success']} | Explosive: {r['is_explosive']} | RZ: {r['yard_line'] <= 20}")
        
    return processed_df

if __name__ == "__main__":
    try:
        print("Initializing GridironMetrics-CFB Analytics Engine...")
        
        # Mock data array updated to include 'yard_line' field (distance to opponent goal)
        mock_data = [
            {"play_type": "Run", "down": 1, "distance": 10, "yards_gained": 6, "opponent_talent": 85.0, "yard_line": 75},   
            {"play_type": "Run", "down": 1, "distance": 10, "yards_gained": 2, "opponent_talent": 85.0, "yard_line": 69},   
            {"play_type": "Pass", "down": 1, "distance": 10, "yards_gained": 12, "opponent_talent": 60.0, "yard_line": 45}, 
            {"play_type": "Pass", "down": 2, "distance": 8, "yards_gained": 3, "opponent_talent": 85.0, "yard_line": 33},   
            {"play_type": "Pass", "down": 3, "distance": 4, "yards_gained": 16, "opponent_talent": 40.0, "yard_line": 16},  # Inside Red Zone (Success)
            {"play_type": "Run", "down": 4, "distance": 2, "yards_gained": 1, "opponent_talent": 40.0, "yard_line": 2}      # Inside Red Zone (Fail)
        ]
        
        test_df = pd.DataFrame(mock_data)
        results = calculate_coaching_metrics(test_df)
        
    except Exception as e:
        print(f"Pipeline Execution Error: {e}")
