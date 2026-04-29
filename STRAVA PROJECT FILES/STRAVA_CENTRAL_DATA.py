import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine
import urllib.parse

def build_and_push_master_dataset():
    print("🚀 Starting Complete ETL Pipeline for Strava/Fitbit Datasets...")

    # ==========================================
    # CONFIGURATION & FILE PATHS
    # ==========================================
    base_path = r"E:\Labmentix Internship\STRAVA"
    
    server = r'TATHAGATA\SQLEXPRESS'
    database = 'PRACTICEDB'
    table_name = 'Fitbit_Business_Master_Hourly'
    driver = 'ODBC Driver 17 for SQL Server' 

    # ==========================================
    # 1. LOAD & STANDARDIZE NATIVE HOURLY DATA
    # ==========================================
    print("⏳ Loading native hourly data...")
    
    # Using your exact local file paths
    h_cal = pd.read_csv(os.path.join(base_path, 'hourlyCalories_merged.csv'))
    h_int = pd.read_csv(os.path.join(base_path, 'hourlyIntensities_merged.csv'))
    h_ste = pd.read_csv(os.path.join(base_path, 'hourlySteps_merged.csv'))

    h_cal['Datetime_Hour'] = pd.to_datetime(h_cal['ActivityHour'])
    h_int['Datetime_Hour'] = pd.to_datetime(h_int['ActivityHour'])
    h_ste['Datetime_Hour'] = pd.to_datetime(h_ste['ActivityHour'])

    h_cal = h_cal.rename(columns={'Calories': 'HourlyCalories'}).drop(columns=['ActivityHour'])
    h_int = h_int.rename(columns={'TotalIntensity': 'HourlyTotalIntensity', 'AverageIntensity': 'HourlyAvgIntensity'}).drop(columns=['ActivityHour'])
    h_ste = h_ste.rename(columns={'StepTotal': 'HourlySteps'}).drop(columns=['ActivityHour'])

    # Merge native hourly files together
    hourly_df = pd.merge(h_cal, h_ste, on=['Id', 'Datetime_Hour'], how='outer')
    hourly_df = pd.merge(hourly_df, h_int, on=['Id', 'Datetime_Hour'], how='outer')

    # ==========================================
    # 2. AGGREGATE GRANULAR DATA (Seconds/Minutes -> Hourly)
    # ==========================================
    print("⏳ Aggregating seconds and minutes data into hourly grain...")
    
    # Heart Rate (Seconds)
    hr = pd.read_csv(os.path.join(base_path, 'heartrate_seconds_merged.csv'))
    hr['Datetime_Hour'] = pd.to_datetime(hr['Time']).dt.floor('H')
    hr_hourly = hr.groupby(['Id', 'Datetime_Hour'], as_index=False)['Value'].mean().rename(columns={'Value': 'Avg_HR'})
    hourly_df = pd.merge(hourly_df, hr_hourly, on=['Id', 'Datetime_Hour'], how='outer')

    # METs (Minutes - Narrow format)
    mets = pd.read_csv(os.path.join(base_path, 'minuteMETsNarrow_merged.csv'))
    mets['Datetime_Hour'] = pd.to_datetime(mets['ActivityMinute']).dt.floor('H')
    mets_hourly = mets.groupby(['Id', 'Datetime_Hour'], as_index=False)['METs'].mean().rename(columns={'METs': 'Avg_METs'})
    hourly_df = pd.merge(hourly_df, mets_hourly, on=['Id', 'Datetime_Hour'], how='outer')

    # ==========================================
    # 3. LOAD & DEDUPLICATE NATIVE DAILY DATA 
    # ==========================================
    print("⏳ Loading daily contextual data and preventing duplicates...")
    
    da = pd.read_csv(os.path.join(base_path, 'dailyActivity_merged.csv'))
    da['Date'] = pd.to_datetime(da['ActivityDate']).dt.date
    da = da.rename(columns={'Calories': 'DailyCalories'}).drop(columns=['ActivityDate'])
    da.drop_duplicates(subset=['Id', 'Date'], keep='first', inplace=True) 

    sd = pd.read_csv(os.path.join(base_path, 'sleepDay_merged.csv'))
    sd['Date'] = pd.to_datetime(sd['SleepDay']).dt.date
    sd.drop(columns=['SleepDay'], inplace=True)
    sd.drop_duplicates(subset=['Id', 'Date'], keep='first', inplace=True)

    wl = pd.read_csv(os.path.join(base_path, 'weightLogInfo_merged.csv'))
    wl['Date'] = pd.to_datetime(wl['Date']).dt.date
    wl.drop(columns=['Fat', 'LogId'], errors='ignore', inplace=True)
    wl.drop_duplicates(subset=['Id', 'Date'], keep='first', inplace=True)

    # ==========================================
    # 4. MASTER MERGE (Hourly + Daily)
    # ==========================================
    print("🔗 Merging all timelines into a Master Fact Table...")
    
    hourly_df['Date'] = hourly_df['Datetime_Hour'].dt.date
    master = pd.merge(hourly_df, da, on=['Id', 'Date'], how='left')
    master = pd.merge(master, sd, on=['Id', 'Date'], how='left')
    master = pd.merge(master, wl, on=['Id', 'Date'], how='left')

    # ==========================================
    # 5. SMART DATA IMPUTATION
    # ==========================================
    print("🧹 Applying missing value imputation...")

    # Fill basic activity gaps with 0
    master.fillna({
        'HourlyCalories': 0, 'HourlySteps': 0, 
        'HourlyTotalIntensity': 0, 'HourlyAvgIntensity': 0, 
        'Avg_METs': 10 # 10 is baseline resting MET
    }, inplace=True)

    # Heart Rate Failsafe Imputation
    master['Avg_HR'] = master.groupby(['Id', 'Date'])['Avg_HR'].transform(lambda x: x.fillna(x.mean()))
    master['Avg_HR'] = master.groupby('Id')['Avg_HR'].transform(lambda x: x.fillna(x.mean()))
    master['Avg_HR'] = master['Avg_HR'].fillna(70) # Global Resting Failsafe

    # Daily Metrics Context Fill (Forward/Backward for Weight and Sleep)
    master.sort_values(['Id', 'Datetime_Hour'], inplace=True)
    daily_cols = ['WeightKg', 'WeightPounds', 'BMI', 'TotalSleepRecords', 'TotalMinutesAsleep', 'TotalTimeInBed']
    master[daily_cols] = master.groupby('Id')[daily_cols].ffill().bfill()

    # Fill any remaining random nulls from the left join
    master.fillna(0, inplace=True)

    # ==========================================
    # 6. ENFORCE HOUR GRAIN
    # ==========================================
    print("🛡️ Enforcing strict hourly grain for BI Dashboarding...")
    master.drop_duplicates(subset=['Id', 'Datetime_Hour'], keep='first', inplace=True)
    
    # Drop intermediate 'Date' column; SQL Server handles Datetime_Hour natively
    master.drop(columns=['Date'], inplace=True)
    
    print(f"✅ Data processing complete. Shape: {master.shape[0]} Rows, {master.shape[1]} Columns.")

    # ==========================================
    # 7. EXPORT DIRECTLY TO SQL SERVER
    # ==========================================
    print("💾 Pushing data to SSMS...")
    
    try:
        connection_string = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
        params = urllib.parse.quote_plus(connection_string)
        engine = create_engine(f'mssql+pyodbc:///?odbc_connect={params}')

        master.to_sql(table_name, con=engine, if_exists='replace', index=False)
        
        print("\n🎉 SUCCESS! Master dataset pushed successfully.")
        print(f"Table [{table_name}] is ready in Database [{database}] for Tableau.")
        
    except Exception as e:
        print("\n❌ EXPORT FAILED. Please check your SQL Server connection details.")
        print(f"Error detail: {e}")

# Run the entire pipeline
if __name__ == "__main__":
    build_and_push_master_dataset()