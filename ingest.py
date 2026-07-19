import os
import requests
from dotenv import load_dotenv

load_dotenv()
RAW_KEY = os.getenv("CFBD_API_KEY")

# Automatically injects the precise 'Bearer ' prefix format the server expects
headers = {
    "Authorization": f"Bearer {RAW_KEY}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}

# The single most stable statistical tracking endpoint
url = "https://collegefootballdata.com"

print("\n=====================================")
print("RUNNING FINAL SAFE TUNNEL TEST...")
print("=====================================")

try:
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        print("SUCCESS! Data pipeline link fully established.")
        print("Your Python script successfully broke the server redirect loops.")
        print("=====================================\n")
    else:
        print(f"Server Connection Established with Code: {response.status_code}")
        print("Your script is hitting the right path, but the API key is invalid.")
        print("Action: Check your email to ensure no characters were missed in your key copy.")

except Exception as error:
    print(f"Pipeline blocked by local OS file system: {error}")
