USE [PRACTICEDB];

--Selecting the entire table to understand the data structure and content
SELECT *
FROM [dbo].[Fitbit_Business_Master_Hourly];

-- How many unique users are active on our platform, and what is our total log count?
SELECT
    COUNT(DISTINCT Id) AS Total_Unique_Users,
    COUNT(*) AS Total_Days_Logged
FROM [dbo].[Fitbit_Business_Master_Hourly];

-- What are the average daily steps, distance, and calories burned?
SELECT 
    ROUND(AVG(TotalSteps), 0) AS Avg_Daily_Steps,
    ROUND(AVG(TotalDistance), 2) AS Avg_Daily_Distance_Km,
    ROUND(AVG([HourlyCalories]), 0) AS Avg_Daily_Calories
FROM  [dbo].[Fitbit_Business_Master_Hourly]
WHERE TotalSteps > 0; -- Ignores days the tracker was left on the nightstand

-- How often do users hit the standard 10,000 daily step goal?
SELECT 
    CASE 
        WHEN TotalSteps >= 10000 THEN 'Goal Met (10k+ Steps)'
        ELSE 'Goal Missed (<10k Steps)' 
    END AS Step_Goal_Status,
    COUNT(*) AS Total_Days,
    ROUND(AVG([HourlyCalories]), 0) AS Avg_Calories_Burned
FROM 
    [dbo].[Fitbit_Business_Master_Hourly]
WHERE 
    TotalSteps > 0
GROUP BY 
    CASE 
        WHEN TotalSteps >= 10000 THEN 'Goal Met (10k+ Steps)'
        ELSE 'Goal Missed (<10k Steps)' 
    END;
-- How do users spend their time throughout the day?
SELECT 
    ROUND(AVG(VeryActiveMinutes), 0) AS Avg_Very_Active_Mins,
    ROUND(AVG(FairlyActiveMinutes), 0) AS Avg_Fairly_Active_Mins,
    ROUND(AVG(LightlyActiveMinutes), 0) AS Avg_Lightly_Active_Mins,
    ROUND(AVG(SedentaryMinutes), 0) AS Avg_Sedentary_Mins
FROM 
    [dbo].[Fitbit_Business_Master_Hourly]
WHERE 
    TotalSteps > 0;
-- Are users actually sleeping when they go to bed?
SELECT 
    ROUND(AVG(TotalTimeInBed), 0) AS Avg_Mins_In_Bed,
    ROUND(AVG(TotalMinutesAsleep), 0) AS Avg_Mins_Asleep,
    ROUND((AVG(TotalMinutesAsleep) / AVG(TotalTimeInBed)) * 100, 1) AS Sleep_Efficiency_Pct
FROM 
    [dbo].[Fitbit_Business_Master_Hourly]
WHERE 
    TotalMinutesAsleep IS NOT NULL 
    AND TotalTimeInBed > 0;
-- What are the resting and peak heart rate averages?
SELECT 
    ROUND(AVG(Avg_HR), 1) AS Overall_Daily_Avg_HR,
    ROUND(MIN([Avg_HR]), 1) AS Average_Resting_HR,
    ROUND(MAX([Avg_HR]), 1) AS Average_Peak_HR
FROM 
    [dbo].[Fitbit_Business_Master_Hourly]
WHERE 
    Avg_HR IS NOT NULL;
-- Are users logging weight manually or using smart scales?
SELECT 
    IsManualReport,
    COUNT(*) AS Total_Weight_Logs,
    ROUND(AVG(WeightKg), 1) AS Avg_Weight_Kg,
    ROUND(AVG(BMI), 1) AS Avg_BMI
FROM 
    STRAVA_MASTER_DATA
WHERE 
    WeightKg IS NOT NULL
GROUP BY 
    IsManualReport;
-- Who are the Top 5 most active users by total steps?
SELECT TOP 5
    Id AS User_ID,
    SUM(TotalSteps) AS Total_Steps_Taken,
    SUM([HourlyCalories]) AS Total_Calories_Burned,
    ROUND(AVG(TotalDistance), 2) AS Avg_Daily_Distance
FROM 
    [dbo].[Fitbit_Business_Master_Hourly]
GROUP BY 
    Id
ORDER BY 
    Total_Steps_Taken DESC;
-- Do high-burn days lead to longer sleep?
SELECT 
    CASE 
        WHEN [HourlyCalories] >= 2500 THEN 'High Exertion (2500+ Cal)'
        ELSE 'Normal/Low Exertion (<2500 Cal)' 
    END AS Exertion_Level,
    COUNT(*) AS Days_Recorded,
    ROUND(AVG(TotalMinutesAsleep), 0) AS Avg_Minutes_Asleep
FROM 
    [dbo].[Fitbit_Business_Master_Hourly]
WHERE 
    TotalMinutesAsleep IS NOT NULL
GROUP BY 
    CASE 
        WHEN [HourlyCalories] >= 2500 THEN 'High Exertion (2500+ Cal)'
        ELSE 'Normal/Low Exertion (<2500 Cal)' 
    END;
-- Which users push themselves the hardest?
SELECT TOP 5
    Id AS User_ID,
    ROUND(SUM(VeryActiveDistance), 2) AS Total_Very_Active_Distance_Km,
    ROUND(SUM(ModeratelyActiveDistance), 2) AS Total_Moderate_Distance_Km
FROM 
    [dbo].[Fitbit_Business_Master_Hourly]
GROUP BY 
    Id
ORDER BY 
    Total_Very_Active_Distance_Km DESC;