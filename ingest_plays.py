import os
import json
import cfbd
import time
from dotenv import load_dotenv

load_dotenv()
RAW_KEY = os.getenv("CFBD_API_KEY")

print("\n=====================================")
print("RUNNING LIVE PLAY-BY-PLAY INGESTION...")
print("=====================================")

try:
    configuration = cfbd.Configuration(
        access_token = RAW_KEY
    )
    
    api_client = cfbd.ApiClient(configuration)
    api_instance = cfbd.PlaysApi(api_client)
    
    master_play_list = []
    target_year = 2025  # Upgraded to fully completed 2025 season
    target_team = 'LSU'
    
    print(f"Initializing master scraping loop for {target_team} ({target_year})...")
    
    # Cycle through all 14 standard regular season weeks automatically
    for week_num in range(1, 15):
        print(f"   ↳ Fetching Week {week_num} tracking logs...")
        try:
            # Using the corrected library method name to bypass interface blocks
            raw_plays = api_instance.get_plays(year=target_year, week=week_num, team=target_team)
            
            if raw_plays:
                week_dicts = [play.to_dict() for play in raw_plays]
                master_play_list.extend(week_dicts)
                print(f"      ✅ Found {len(week_dicts)} plays executed.")
            else:
                print("      ⏸️ Bye Week / No play metrics logged.")
                
            # Protect your token key from rate-limit restrictions
            time.sleep(0.2)
            
        except Exception as week_error:
            print(f"      ⚠️ Week {week_num} data unavailable: {week_error}")

    # Save specifically under the 2025 LSU filename label
    output_filename = f"plays_lsu_{target_year}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(master_play_list, f, default=str, indent=4)
        
    print("\n=====================================")
    print("SUCCESS! Full season play-by-play database built.")
    print(f"Saved {len(master_play_list)} total historical play rows into '{output_filename}'.")
    print("=====================================\n")

except Exception as error:
    print(f"❌ MASTER PIPELINE REJECTED: {error}")
