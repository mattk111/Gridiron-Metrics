import os
import json
import cfbd
from dotenv import load_dotenv

load_dotenv()
RAW_KEY = os.getenv("CFBD_API_KEY")

print("\n=====================================")
print("RUNNING LIVE DATA API INGESTION...")
print("=====================================")

try:
    # Official V2 System Configuration Layout
    configuration = cfbd.Configuration(
        access_token = RAW_KEY
    )
    
    # Initialize the secure API tunnel client
    api_client = cfbd.ApiClient(configuration)
    api_instance = cfbd.GamesApi(api_client)
    
    print("Connecting to secure data server gateway...")
    # Filters the data stream directly on the server for 2025 FBS-only matchups
    games_data = api_instance.get_games(year=2025, season_type='regular', classification='fbs')
    
    # Convert custom library objects to clean dictionary models before saving
    raw_json_list = [game.to_dict() for game in games_data]
    
    # Save the real structured records straight to your local disk file
    output_filename = "records_2025.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(raw_json_list, f, default=str, indent=4)
        
    print("SUCCESS! Real college football data pipeline established.")
    print(f"Saved {len(raw_json_list)} real FBS game records into '{output_filename}'.")

except Exception as error:
    print(f"❌ PIPELINE CONNECTION REJECTED: {error}")
    print("Action Required: Check your .env file to ensure the API key is active.")
    
print("=====================================\n")
