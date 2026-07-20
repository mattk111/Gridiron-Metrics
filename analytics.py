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
    
    print(f"Raw Success Rate:             {raw_success_rate:.1f}%")
    print(f"Talent-Adjusted Success Index: {avg_weighted_success:.1f}")
    print(f"Total Explosive Plays Created: {explosive_count}")
    
    # --- DETAILED PLAY INSPECTION LOG ---
    print("\n--- Detailed Play Inspection Log ---")
    for index, r in processed_df.iterrows():
        print(f"Play {index + 1}: {r['play_type']} | Dn: {r['down']} | Dist: {r['distance']} | Yds Gained: {r['yards_gained']} | Success: {r['is_success']} | Explosive: {r['is_explosive']}")
        
    return processed_df

if __name__ == "__main__":
    # Smoke test to verify local environment and imports run without errors
    try:
        print("Initializing GridironMetrics-CFB Analytics Engine...")
        
        # Mock data array updated to include mock opponent talent scores (0-100 scale)
        mock_data = [
            {"play_type": "Run", "down": 1, "distance": 10, "yards_gained": 6, "opponent_talent": 85.0},   
            {"play_type": "Pass", "down": 2, "distance": 8, "yards_gained": 3, "opponent_talent": 85.0},   
            {"play_type": "Pass", "down": 3, "distance": 4, "yards_gained": 16, "opponent_talent": 40.0},  
            {"play_type": "Run", "down": 4, "distance": 2, "yards_gained": 1, "opponent_talent": 40.0}     
        ]
        
        test_df = pd.DataFrame(mock_data)
        results = calculate_coaching_metrics(test_df)
        
    except Exception as e:
        # Error catch block to instantly output terminal debugging info if it crashes
        print(f"Pipeline Execution Error: {e}")
