import requests
import pandas as pd
import urllib
from sqlalchemy import create_engine

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# ⚠️ PASTE YOUR ACTUAL RAPIDAPI KEY BELOW
RAPID_API_KEY = "efbafd8532msh4e1a7cd94f4d8e6p1f1f6fjsn33dd94c10d97" 
MATCH_ID = "40381" 

# SQL Server Configuration
SQL_SERVER_NAME = r'TATHAGATA\SQLEXPRESS'
DATABASE_NAME = 'PRACTICEDB'
# ==========================================

def fetch_match_scorecard(match_id, api_key):
    """Fetches the scorecard JSON for a specific match ID."""
    url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/hscard"
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network Error: {e}")
        return None

# ==========================================
# 🚀 MAIN EXECUTION (ETL PIPELINE)
# ==========================================
if __name__ == "__main__":
    
    print(f"Fetching scorecard data for Match ID: {MATCH_ID}...")
    scorecard_data = fetch_match_scorecard(MATCH_ID, RAPID_API_KEY)

    if scorecard_data and 'scorecard' in scorecard_data and len(scorecard_data['scorecard']) > 0:
        print("✅ Successfully fetched data from API!\n")
        
        # ---------------------------------------------------------
        # 1. BASE INNINGS DATA
        # ---------------------------------------------------------
        df_innings = pd.json_normalize(scorecard_data['scorecard'])
        
        # ---------------------------------------------------------
        # 2. TRANSFORM BATTING STATISTICS
        # ---------------------------------------------------------
        print("🏏 Extracting Batting Statistics...")
        df_batting_raw = df_innings[['inningsid', 'batteamname', 'batsman']].copy()
        df_batting_exploded = df_batting_raw.explode('batsman').reset_index(drop=True).dropna(subset=['batsman'])
        
        df_batting_stats = pd.json_normalize(df_batting_exploded['batsman'])
        df_batting_final = pd.concat([
            df_batting_exploded[['inningsid', 'batteamname']].reset_index(drop=True), 
            df_batting_stats.reset_index(drop=True)
        ], axis=1)

        desired_batting_cols = ['inningsid', 'batteamname', 'name', 'runs', 'balls', 'fours', 'sixes', 'strikeRate']
        safe_batting_cols = [col for col in desired_batting_cols if col in df_batting_final.columns]
        
        # ---------------------------------------------------------
        # 3. TRANSFORM BOWLING STATISTICS
        # ---------------------------------------------------------
        print("🎯 Extracting Bowling Statistics...")
        df_bowling_raw = df_innings[['inningsid', 'bowler']].copy()
        df_bowling_exploded = df_bowling_raw.explode('bowler').reset_index(drop=True).dropna(subset=['bowler'])
        
        df_bowling_stats = pd.json_normalize(df_bowling_exploded['bowler'])
        df_bowling_final = pd.concat([
            df_bowling_exploded[['inningsid']].reset_index(drop=True), 
            df_bowling_stats.reset_index(drop=True)
        ], axis=1)

        desired_bowling_cols = ['inningsid', 'name', 'overs', 'maidens', 'runs', 'wickets', 'economy']
        safe_bowling_cols = [col for col in desired_bowling_cols if col in df_bowling_final.columns]
        
        # ---------------------------------------------------------
        # 4. LOAD INTO SQL SERVER
        # ---------------------------------------------------------
        print("\n==========================================")
        print(f"🗄️ LOADING DATA DIRECTLY TO SQL SERVER ({DATABASE_NAME})")
        print("==========================================")
        
        params = urllib.parse.quote_plus(
            f'Driver={{ODBC Driver 17 for SQL Server}};'
            f'Server={SQL_SERVER_NAME};'
            f'Database={DATABASE_NAME};'
            f'Trusted_Connection=yes;'
        )

        try:
            engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
            
            # Dump Pandas DataFrame straight to SQL Server Tables
            df_batting_final[safe_batting_cols].to_sql('match_batting_stats', con=engine, if_exists='append', index=False)
            print("✅ Batting data successfully loaded into 'match_batting_stats' table.")

            df_bowling_final[safe_bowling_cols].to_sql('match_bowling_stats', con=engine, if_exists='append', index=False)
            print("✅ Bowling data successfully loaded into 'match_bowling_stats' table.")

        except Exception as db_error:
            print(f"❌ Database Error: {db_error}")
        finally:
            if 'engine' in locals():
                engine.dispose()
                print("🔌 Database connection closed.")
    else:
        print("⚠️ Failed to fetch valid scorecard data.")