import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import urllib

# ==============================================================================
# 0. CONFIGURATION
# ==============================================================================
FILE_PATH = r"E:\\Labmentix Internship\\RIDE SERVICE PROJECT\\OLA_DataSet.xlsx - July.csv"

# SQL Server Connection String (Windows Authentication)
# Note: Ensure 'ODBC Driver 17 for SQL Server' is installed on your machine.
SERVER_NAME = r'TATHAGATA\SQLEXPRESS'
DATABASE_NAME = 'PRACTICEDB'

conn_str = (
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server={SERVER_NAME};"
    f"Database={DATABASE_NAME};"
    f"Trusted_Connection=yes;"
)
quoted_conn_str = urllib.parse.quote_plus(conn_str)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={quoted_conn_str}")

# ==============================================================================
# 1. EXTRACT: Load Raw Data
# ==============================================================================
print("Loading raw data...")
df = pd.read_csv(FILE_PATH)

# ==============================================================================
# 2. TRANSFORM: The "Bulletproof" Cleaning Logic
# ==============================================================================
print("Cleaning data...")

# A. Calculate Medians for Continuous Metrics
med_vtat = df['V_TAT'].median()
med_ctat = df['C_TAT'].median()
med_drat = df['Driver_Ratings'].median()
med_crat = df['Customer_Rating'].median()

# B. Calculate Modes for Categorical Metrics
mode_pay = df['Payment_Method'].mode()[0]
mode_ccust = df['Canceled_Rides_by_Customer'].mode()[0]
mode_cdrv = df['Canceled_Rides_by_Driver'].mode()[0]
mode_increas = df['Incomplete_Rides_Reason'].mode()[0]

# C. Impute Continuous Metrics (Only for successful rides to prevent phantom data)
df['V_TAT'] = np.where(df['Booking_Status'] == 'Success', df['V_TAT'].fillna(med_vtat), df['V_TAT'])
df['C_TAT'] = np.where(df['Booking_Status'] == 'Success', df['C_TAT'].fillna(med_ctat), df['C_TAT'])
df['Driver_Ratings'] = np.where(df['Booking_Status'] == 'Success', df['Driver_Ratings'].fillna(med_drat), df['Driver_Ratings'])
df['Customer_Rating'] = np.where(df['Booking_Status'] == 'Success', df['Customer_Rating'].fillna(med_crat), df['Customer_Rating'])

# Default Payment Method
df['Payment_Method'] = df['Payment_Method'].fillna(mode_pay)

# D. Conditional Categorical Imputation (The Fixes)
# Fix 1: Customer Cancellations
df['Canceled_Rides_by_Customer'] = np.where(df['Booking_Status'] == 'Success', 'N/A - Completed Ride',
                                   np.where(df['Booking_Status'] == 'Canceled by Customer', df['Canceled_Rides_by_Customer'].fillna(mode_ccust), 'N/A'))

# Fix 2: Driver Cancellations
df['Canceled_Rides_by_Driver'] = np.where(df['Booking_Status'] == 'Success', 'N/A - Completed Ride',
                                 np.where(df['Booking_Status'] == 'Canceled by Driver', df['Canceled_Rides_by_Driver'].fillna(mode_cdrv), 'N/A'))

# Fix 3: Incomplete Rides
df['Incomplete_Rides'] = np.where(df['Booking_Status'] == 'Success', 'No', df['Incomplete_Rides'].fillna('Unknown'))

df['Incomplete_Rides_Reason'] = np.where(df['Booking_Status'] == 'Success', 'N/A - Completed Ride',
                                np.where(df['Incomplete_Rides'] == 'Yes', df['Incomplete_Rides_Reason'].fillna(mode_increas), 'N/A'))

# Convert formats
df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True)
df['Booking_Value'] = pd.to_numeric(df['Booking_Value'], errors='coerce')
df['Ride_Distance'] = pd.to_numeric(df['Ride_Distance'], errors='coerce')

# ==============================================================================
# 3. ARCHITECTURE: Build the Star Schema
# ==============================================================================
print("Building Star Schema...")

# A. Dim_Date (Enriched for Business Analytics)
dim_date = df[['Date']].drop_duplicates().dropna().copy()
dim_date['Year'] = dim_date['Date'].dt.year
dim_date['Month_Num'] = dim_date['Date'].dt.month
dim_date['Month_Name'] = dim_date['Date'].dt.strftime('%B')
dim_date['Day_Of_Week_Num'] = dim_date['Date'].dt.weekday + 1 # Monday=1, Sunday=7
dim_date['Day_Name'] = dim_date['Date'].dt.strftime('%A')
dim_date['Is_Weekend'] = np.where(dim_date['Day_Of_Week_Num'].isin([6, 7]), 1, 0)

# B. Dim_Customer
dim_customer = df[['Customer_ID']].drop_duplicates().dropna()

# C. Dim_Vehicle (Now includes images for BI visualization)
dim_vehicle = df.groupby('Vehicle_Type', as_index=False).agg({'Vehicle Images': 'max'})
dim_vehicle.rename(columns={'Vehicle Images': 'Vehicle_Image_URL'}, inplace=True)

# D. Dim_Ride_Status (The Junk Dimension)
status_cols = ['Booking_Status', 'Canceled_Rides_by_Customer', 'Canceled_Rides_by_Driver', 'Incomplete_Rides', 'Incomplete_Rides_Reason']
dim_ride_status = df[status_cols].drop_duplicates().reset_index(drop=True)
dim_ride_status.insert(0, 'Status_ID', range(1, 1 + len(dim_ride_status))) # Create Surrogate Key

# E. Fact_Bookings
# Merge the Status_ID back to the main dataframe
fact_bookings = pd.merge(df, dim_ride_status, on=status_cols, how='left')

# Select the final columns for the Fact Table
fact_cols = [
    'Booking_ID', 'Date', 'Customer_ID', 'Vehicle_Type', 
    'Pickup_Location', 'Drop_Location', 'Payment_Method', 
    'Status_ID', 'V_TAT', 'C_TAT', 'Driver_Ratings', 
    'Customer_Rating', 'Booking_Value', 'Ride_Distance'
]
fact_bookings = fact_bookings[fact_cols]

# ==============================================================================
# 4. LOAD: Export to SQL Server (SSMS)
# ==============================================================================
print(f"Connecting to {SERVER_NAME} | Database: {DATABASE_NAME}...")

# Dictionary of DataFrames and their target table names
tables_to_export = {
    'Dim_Customer': dim_customer,
    'Dim_Vehicle': dim_vehicle,
    'Dim_Date': dim_date,
    'Dim_Ride_Status': dim_ride_status,
    'Fact_Bookings': fact_bookings
}

for table_name, dataframe in tables_to_export.items():
    print(f"Exporting {table_name} ({len(dataframe)} rows)...")
    try:
        # if_exists='replace' drops the table if it exists and creates a new one
        dataframe.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
        print(f" -> {table_name} loaded successfully!")
    except Exception as e:
        print(f" -> Error loading {table_name}: {e}")

print("\nETL Pipeline Complete!.")