import requests
import pandas as pd

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# ⚠️ PASTE YOUR ACTUAL RAPIDAPI KEY BELOW
RAPID_API_KEY = "efbafd8532msh4e1a7cd94f4d8e6p1f1f6fjsn33dd94c10d97" 

# The specific match ID we want to analyze
MATCH_ID = "40381" 
# ==========================================

def fetch_match_scorecard(match_id, api_key):
    """
    Fetches the scorecard JSON for a specific match ID.
    """
    url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/hscard"
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        return response.json()
        
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 403:
            print("\n❌ HTTP 403 FORBIDDEN: Check your API key and subscription.")
        elif response.status_code == 401:
            print("\n❌ HTTP 401 UNAUTHORIZED: Your API key is invalid or expired.")
        elif response.status_code == 429:
            print("\n❌ HTTP 429 TOO MANY REQUESTS: Quota exceeded.")
        else:
            print(f"\n❌ HTTP Error: {http_err}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network Error: {e}")
        return None

# ==========================================
# 🚀 MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    
    if RAPID_API_KEY == "PASTE_YOUR_ACTUAL_KEY_HERE":
        print("⚠️ STOP: You need to paste your RapidAPI key into the RAPID_API_KEY variable first!")
    else:
        print(f"Fetching scorecard data for Match ID: {MATCH_ID}...")
        scorecard_data = fetch_match_scorecard(MATCH_ID, RAPID_API_KEY)

        if scorecard_data:
            print("✅ Successfully fetched data!\n")
            print(f"Match Status: {scorecard_data.get('status', 'Unknown')}")
            
            if 'scorecard' in scorecard_data and len(scorecard_data['scorecard']) > 0:
                
                # ---------------------------------------------------------
                # 1. BASE INNINGS DATA
                # ---------------------------------------------------------
                df_innings = pd.json_normalize(scorecard_data['scorecard'])
                
                # ---------------------------------------------------------
                # 2. EXTRACT BATTING STATISTICS
                # ---------------------------------------------------------
                print("\n==========================================")
                print("🏏 EXTRACTING BATTING STATISTICS")
                print("==========================================")
                
                df_batting_raw = df_innings[['inningsid', 'batteamname', 'batsman']].copy()
                df_batting_exploded = df_batting_raw.explode('batsman').reset_index(drop=True)
                
                # Drop rows where batsman data might be NaN (e.g., innings hasn't happened yet)
                df_batting_exploded = df_batting_exploded.dropna(subset=['batsman'])
                
                df_batting_stats = pd.json_normalize(df_batting_exploded['batsman'])
                df_batting_final = pd.concat([
                    df_batting_exploded[['inningsid', 'batteamname']].reset_index(drop=True), 
                    df_batting_stats.reset_index(drop=True)
                ], axis=1)

                print(f"Extracted {len(df_batting_final)} total batting records.")
                
                # SAFE COLUMN SELECTION: Only grab columns that actually exist in the payload
                desired_batting_cols = ['inningsid', 'batteamname', 'name', 'runs', 'balls', 'fours', 'sixes', 'strikeRate']
                safe_batting_cols = [col for col in desired_batting_cols if col in df_batting_final.columns]
                
                print("\n📊 Clean Batting Table Preview:")
                print(df_batting_final[safe_batting_cols].head())

                # ---------------------------------------------------------
                # 3. EXTRACT BOWLING STATISTICS
                # ---------------------------------------------------------
                print("\n==========================================")
                print("🎯 EXTRACTING BOWLING STATISTICS")
                print("==========================================")
                
                # Note: We use 'bowlteamname' to know which team is bowling, if available. 
                # Otherwise, we just map it to the innings.
                df_bowling_raw = df_innings[['inningsid', 'bowler']].copy()
                df_bowling_exploded = df_bowling_raw.explode('bowler').reset_index(drop=True)
                df_bowling_exploded = df_bowling_exploded.dropna(subset=['bowler'])
                
                df_bowling_stats = pd.json_normalize(df_bowling_exploded['bowler'])
                df_bowling_final = pd.concat([
                    df_bowling_exploded[['inningsid']].reset_index(drop=True), 
                    df_bowling_stats.reset_index(drop=True)
                ], axis=1)

                print(f"Extracted {len(df_bowling_final)} total bowling records.")
                
                # Safe column selection for bowlers
                desired_bowling_cols = ['inningsid', 'name', 'overs', 'maidens', 'runs', 'wickets', 'economy']
                safe_bowling_cols = [col for col in desired_bowling_cols if col in df_bowling_final.columns]
                
                print("\n📊 Clean Bowling Table Preview:")
                print(df_bowling_final[safe_bowling_cols].head())

            else:
                print("⚠️ No 'scorecard' array found in the response.")