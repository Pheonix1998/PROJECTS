USE [PRACTICEDB];
SELECT * FROM [dbo].[FREELANCERS];

--CREATE CLUSTERED COLUMNSTORE  INDEX CCLIX ON [dbo].[FREELANCERS];
-- The Elites
SELECT TOP 10
[freelancer_ID] AS ID,
[primary_skill] AS Skills,
[name] AS Names,
[country],
[years_of_experience],
[hourly_rate (USD)] AS Charges,
[rating] AS Ratings,
[client_satisfaction] *100 AS Satisfaction_percent,
DENSE_RANK() OVER (PARTITION BY [primary_skill] ORDER BY [hourly_rate (USD)] ASC, [rating] DESC, [client_satisfaction] DESC) AS Rankings
FROM [dbo].[FREELANCERS] AS FRL
WHERE [is_active] = 1; /* Active Filter */

-- Percentiles
WITH CTE_PCTLS AS
(
	SELECT DISTINCT [primary_skill],
    PERCENTILE_CONT(0.25) WITHIN GROUP(ORDER BY [hourly_rate (USD)]) OVER (PARTITION BY [primary_skill]) AS Lower_Quartile,
	PERCENTILE_CONT(0.50) WITHIN GROUP(ORDER BY [hourly_rate (USD)]) OVER (PARTITION BY [primary_skill]) AS Median,
	PERCENTILE_CONT(0.75) WITHIN GROUP(ORDER BY [hourly_rate (USD)]) OVER (PARTITION BY [primary_skill]) AS Upper_Quartile
	FROM [dbo].[FREELANCERS]
	WHERE [is_active] = 1
),
CTE_RANGES AS
(
	SELECT *,
	(Upper_Quartile - Lower_Quartile) AS IQR,
	(Upper_Quartile + (1.5 * (Upper_Quartile - Lower_Quartile))) AS Upper_Boundary,
	ABS((Lower_Quartile - (1.5 * (Upper_Quartile - Lower_Quartile)))) AS Lower_Boundary
	FROM CTE_PCTLS
)
SELECT * FROM CTE_RANGES
ORDER BY Median DESC;

-- Quartile Performance
WITH CTE_PCTLS AS
(
	SELECT DISTINCT [country],
	PERCENTILE_CONT(0.00) WITHIN GROUP(ORDER BY [hourly_rate (USD)]) OVER (PARTITION BY [country]) AS Minimum_Quartile,
    PERCENTILE_CONT(0.25) WITHIN GROUP(ORDER BY [hourly_rate (USD)]) OVER (PARTITION BY [country]) AS Lower_Quartile,
	PERCENTILE_CONT(0.50) WITHIN GROUP(ORDER BY [hourly_rate (USD)]) OVER (PARTITION BY [country]) AS Median,
	PERCENTILE_CONT(0.75) WITHIN GROUP(ORDER BY [hourly_rate (USD)]) OVER (PARTITION BY [country]) AS Upper_Quartile,
	PERCENTILE_CONT(1.00) WITHIN GROUP(ORDER BY [hourly_rate (USD)]) OVER (PARTITION BY [country]) AS Maximum_Quartile
	FROM [dbo].[FREELANCERS]
	WHERE [is_active] = 1 /* Active Filter */
),
CTE_RANGES AS
(
	SELECT *,
	(Upper_Quartile - Lower_Quartile) AS IQR,
	(Upper_Quartile + (1.5 * (Upper_Quartile - Lower_Quartile))) AS Upper_Boundary,
	ABS((Lower_Quartile - (1.5 * (Upper_Quartile - Lower_Quartile)))) AS Lower_Boundary
	FROM CTE_PCTLS
),
CTE_SUMMARY AS
(
SELECT *,
(SELECT ROUND(AVG([client_satisfaction]) * 100.00,2) FROM [dbo].[FREELANCERS] AS FRL WHERE FRL.country = CTR.country) AS Client_Satisfaction,
(SELECT COUNT([freelancer_ID]) FROM [dbo].[FREELANCERS] AS FRL WHERE FRL.country = CTR.country) AS Freelancers
FROM CTE_RANGES AS CTR
)
SELECT TOP 5 
	   [country],
	   Lower_Quartile,
	   Median,
	   Upper_Quartile,
	   Client_Satisfaction,
	   Freelancers
FROM CTE_SUMMARY
ORDER BY Freelancers DESC,Median DESC;

--  Pricing Outliers
WITH CTE_PRICES AS
(
	SELECT DISTINCT [primary_skill],[hourly_rate (USD)],
	PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY [hourly_rate (USD)]) OVER(PARTITION BY [primary_skill]) AS PERCTL_90
	FROM [dbo].[FREELANCERS]
    WHERE [is_active] = 1
)
SELECT CTPS.* ,
	   FRLS.[name] AS Names,
(SELECT COUNT(DISTINCT([freelancer_ID])) FROM [dbo].[FREELANCERS] AS FRLS WHERE FRLS.primary_skill = CTPS.primary_skill) AS Freelancer_Numbers
FROM CTE_PRICES AS CTPS
LEFT JOIN [dbo].[FREELANCERS] AS FRLS
ON FRLS.primary_skill = CTPS.primary_skill
WHERE CTPS.[hourly_rate (USD)] > PERCTL_90 /* Outlier condition */
ORDER BY Names ASC;

-- Experience vs. Rate Trajectory
SELECT DISTINCT[primary_skill],[hourly_rate (USD)],[years_of_experience],
ROUND(AVG([hourly_rate (USD)]) OVER (PARTITION BY [primary_skill] ORDER BY [years_of_experience] ASC),2) AS RUN_AVG
FROM [dbo].[FREELANCERS]
ORDER BY [years_of_experience];

-- The Rating Gap
WITH CTE_RATINGS AS
(
SELECT DISTINCT [country], [primary_skill],
ROUND(AVG([rating]),2) AS Averages
FROM [dbo].[FREELANCERS]
GROUP BY [country], [primary_skill]
),
CTE_FINAL AS
(
SELECT CTR.*,
	   FLRS.[rating] AS Ratings,
	   FLRS.name AS Names
FROM CTE_RATINGS AS CTR
LEFT JOIN [dbo].[FREELANCERS] AS FLRS
ON FLRS.primary_skill = CTR.primary_skill AND FLRS.country = CTR.country
)
SELECT *,
ROUND((Averages - Ratings),2) AS Gaps
FROM CTE_FINAL
ORDER BY [country] ASC;

-- The Experience Premium Anomaly
WITH CTE_MIS AS
(
SELECT [primary_skill] AS Skills,
ROUND(AVG([hourly_rate (USD)]),2) AS Average_Charges,
	   CASE WHEN [years_of_experience] > = 0 AND [years_of_experience] < = 3 THEN 'Junior'
		    WHEN [years_of_experience] > = 4 AND [years_of_experience] < = 8 THEN 'Mid'
			WHEN [years_of_experience] > = 9 THEN 'Senior'
	   END AS Categories
FROM [dbo].[FREELANCERS]
GROUP BY [primary_skill],
	      CASE WHEN [years_of_experience] > = 0 AND [years_of_experience] < = 3 THEN 'Junior'
		       WHEN [years_of_experience] > = 4 AND [years_of_experience] < = 8 THEN 'Mid'
	           WHEN [years_of_experience] > = 9 THEN 'Senior'
	      END
)
SELECT Skills
FROM CTE_MIS
GROUP BY Skills
HAVING AVG(CASE WHEN Categories = 'Senior' THEN Average_Charges END) < AVG(CASE WHEN Categories = 'Mid' THEN Average_Charges END);

-- Market Saturation & Diversity
WITH CTE_PART AS
(
	SELECT DISTINCT [primary_skill] AS Skills,
	CAST(SUM(CASE WHEN [gender] = 'FEMALE' THEN 1 END) AS FLOAT) AS FEMALES,
	CAST(COUNT(DISTINCT([freelancer_ID])) AS FLOAT) AS Freelancers,
	ROUND(CAST(SUM(CASE WHEN [gender] = 'FEMALE' THEN 1 END) AS FLOAT) / CAST(COUNT(DISTINCT([freelancer_ID])) AS FLOAT) * 100.00,2) AS AVG_FEMALES
	FROM [dbo].[FREELANCERS] AS FLR
	GROUP BY [primary_skill]
),
CTE_GLOBE_AVG AS
(
	SELECT ROUND(CAST(SUM(CASE WHEN [gender] = 'FEMALE' THEN 1 END) AS FLOAT) / CAST(COUNT(DISTINCT([freelancer_ID])) AS FLOAT) * 100.00,2) AS Females_Global
	FROM [dbo].[FREELANCERS] AS FLRS
)
SELECT CTP.*, CTGA.*
FROM CTE_PART AS CTP
CROSS JOIN CTE_GLOBE_AVG AS CTGA
WHERE CTP.AVG_FEMALES < CTGA.Females_Global;

-- Weighted Quality Score
WITH CTE_Scores AS
(
	SELECT [primary_skill] AS Skills,
		   ROUND(AVG([rating]),2) AS Unweighted_Average,
		   ROUND(AVG([rating] * [years_of_experience]),2) AS Weighted_Average,
		   ROUND(COUNT(DISTINCT([freelancer_ID])),2) AS Freelancers,
		   ROUND(AVG([years_of_experience]),2) AS Years_of_Experience
	FROM [dbo].[FREELANCERS]
	GROUP BY [primary_skill]
)
SELECT *,
ROUND((Weighted_Average - Unweighted_Average),2) AS Average_Gap
FROM CTE_Scores
ORDER BY ROUND((Weighted_Average - Unweighted_Average),2) DESC;

-- The Polarizing Skills
WITH CTE_Polars AS
(
	SELECT DISTINCT [primary_skill],
	STDEV([client_satisfaction]) AS Deviations
	FROM [dbo].[FREELANCERS]
	GROUP BY [primary_skill]
),
CTE_SUMMARY AS
(
SELECT *,
(SELECT AVG([client_satisfaction]) FROM [dbo].[FREELANCERS] AS FRLS WHERE FRLS.[primary_skill] = CTP.[primary_skill]) AS Satisfaction_Scores
FROM CTE_Polars AS CTP
),
CTE_RANKINGS AS
(
SELECT *,
DENSE_RANK() OVER (ORDER BY Satisfaction_Scores DESC) AS Rankings
FROM CTE_SUMMARY
)
SELECT *
FROM CTE_RANKINGS
WHERE Rankings = 1; /* Highest filter */

-- Flight Risk / Dormant Talent
WITH CTE_DORMANCY AS
(
	SELECT DISTINCT [primary_skill] AS Skills,
	COUNT(DISTINCT([freelancer_ID])) AS Freelancers,
	COUNT(CASE WHEN [rating] > = 4.0 AND [is_active] = 0 THEN [primary_skill] END) AS High_Inactive,
	COUNT(CASE WHEN [rating] > = 4.0 AND [is_active] = 1 THEN [primary_skill] END) AS High_Active
	FROM [dbo].[FREELANCERS]
	GROUP BY [primary_skill]
),
CTE_RATIO AS
(
	SELECT *,
    ROUND((CAST(High_Inactive AS float) / CAST(High_Active AS float)),2) AS Ratio
	FROM CTE_DORMANCY
),
CTE_RANKINGS AS
(
SELECT *,
DENSE_RANK() OVER (ORDER BY Ratio DESC) AS Ratio_Ranks
FROM CTE_RATIO
)
SELECT * 
FROM CTE_RANKINGS
WHERE Ratio_Ranks = 1; /* Highest ratio filter */

-- The "Value Pick" Algorithm
    WITH CTE_PICKS AS
    (
    SELECT [freelancer_ID],
           [name],
           [primary_skill],
           [country],
           [hourly_rate (USD)],
           [client_satisfaction],
           [is_active],
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY [client_satisfaction]) OVER () AS TOP_10_Global_Satisfaction,
    ROUND(AVG([hourly_rate (USD)]) OVER (PARTITION BY [primary_skill],[country]),2) AS Hourly_rate_by_skill_country
    FROM [dbo].[FREELANCERS]
    ),
    CTE_RATES AS
    (
    SELECT *,
    PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY Hourly_rate_by_skill_country) OVER() AS PERCENTILE_20_BELOW
    FROM CTE_PICKS
    )
    SELECT *
    FROM CTE_RATES
    WHERE [is_active] = 1 AND [client_satisfaction] > = TOP_10_Global_Satisfaction AND [hourly_rate (USD)] < = PERCENTILE_20_BELOW
    ORDER BY [client_satisfaction] DESC , Hourly_rate_by_skill_country DESC;

-- Language Localization Mismatch
WITH CTE_LANGUAGE AS
(
SELECT [country],[language],
COUNT([language]) AS Speakers
FROM [dbo].[FREELANCERS]
WHERE [is_active] = 1
GROUP BY [country],[language]
),
CTE_RANKINGS AS
(
SELECT * ,
DENSE_RANK() OVER (PARTITION BY [country] ORDER BY Speakers DESC) AS Rankings
FROM CTE_LANGUAGE
),
CTE_MAX AS
(
SELECT * FROM CTE_RANKINGS
WHERE Rankings = 1
)
SELECT F.[freelancer_ID],
	   F.[name],
	   F.[country],
	   F.[language],
	   F.[hourly_rate (USD)],
	   F.is_active,
	   CTM.*
	   FROM CTE_MAX AS CTM
	   LEFT JOIN [dbo].[FREELANCERS] AS F
	   ON F.country  = CTM.country
	   WHERE F.is_active = 1 AND  CTM.Rankings <> 1;

-- Peer-to-Peer Recommendation
-- Step 1: Isolate the target freelancer's profile metrics
WITH TargetFreelancer AS (
    SELECT 
        freelancer_ID, 
        primary_skill, 
        years_of_experience, 
        client_satisfaction
    FROM Freelancers
    WHERE freelancer_ID = 'FL250001'
)

-- Step 2: Extract top alternative candidates using a Self-Join
SELECT TOP 3
    a.freelancer_ID AS Recommended_ID,
    a.name AS Recommended_Name,
    a.primary_skill,
    a.years_of_experience,
    a.client_satisfaction,
    a.[hourly_rate (USD)]
FROM Freelancers a
INNER JOIN TargetFreelancer t 
    -- Match on exact skill category
    ON a.primary_skill = t.primary_skill
    -- Exclude the target freelancer from the results
    AND a.freelancer_ID <> t.freelancer_ID
    -- Define the +/- 2 years of experience window
    AND a.years_of_experience BETWEEN (t.years_of_experience - 2) AND (t.years_of_experience + 2)
    -- Ensure the recommendation represents an upgrade in quality
    AND a.client_satisfaction > t.client_satisfaction
ORDER BY 
    a.client_satisfaction DESC;

-- Exact Median Calculation
WITH CTE_CALCULATIONS AS
(
SELECT DISTINCT ([primary_skill]),
CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY [hourly_rate (USD)]) OVER (PARTITION BY [primary_skill]) AS FLOAT) AS Median,
CAST(ROUND(AVG([hourly_rate (USD)]) OVER (PARTITION BY [primary_skill]),2) AS FLOAT)AS Average
FROM [dbo].[FREELANCERS]
),
CTE_MIS AS
(
SELECT *,
ABS(ROUND((Median - Average),2)) AS Changes
FROM CTE_CALCULATIONS
)
SELECT *,
CASE WHEN Average > Median +2  THEN 'Right Skewed'
	 WHEN  Average < Median -2 THEN 'Left Skewed'
	END AS Skewness
FROM CTE_MIS
ORDER BY Changes DESC;

-- The Generational Shift
WITH AgeBrackets AS (
    -- Step 1: Categorize freelancers into distinct age decades using CASE WHEN
    SELECT 
        freelancer_ID,
        primary_skill,
        CASE 
            WHEN age >= 20 AND age < 30 THEN '20-29'
            WHEN age >= 30 AND age < 40 THEN '30-39'
            WHEN age >= 40 AND age < 50 THEN '40-49'
            WHEN age >= 50 THEN '50+'
        END AS Age_Decade
    FROM 
        [dbo].[FREELANCERS]
    WHERE 
        age IS NOT NULL
),
SkillCounts AS (
    -- Step 2: Aggregate the total count of freelancers per decade and skill
    SELECT 
        Age_Decade,
        primary_skill,
        COUNT(freelancer_ID) AS Total_Freelancers
    FROM 
        AgeBrackets
    GROUP BY 
        Age_Decade, 
        primary_skill
),
RankedSkills AS (
    -- Step 3: Apply a Window Function to rank the skills within each decade
    -- Tie-breaker added: alphabetical order of primary_skill
    SELECT 
        Age_Decade,
        primary_skill,
        Total_Freelancers,
        ROW_NUMBER() OVER(
            PARTITION BY Age_Decade 
            ORDER BY Total_Freelancers DESC, primary_skill ASC
        ) as Skill_Rank
    FROM 
        SkillCounts
)
-- Step 4: Pivot the data into a flattened dashboard-ready format
SELECT 
    Age_Decade,
    
    -- Rank 1 Skill & Count
    MAX(CASE WHEN Skill_Rank = 1 THEN primary_skill END) AS Top_Skill_1,
    MAX(CASE WHEN Skill_Rank = 1 THEN Total_Freelancers END) AS Count_1,
    
    -- Rank 2 Skill & Count
    MAX(CASE WHEN Skill_Rank = 2 THEN primary_skill END) AS Top_Skill_2,
    MAX(CASE WHEN Skill_Rank = 2 THEN Total_Freelancers END) AS Count_2,
    
    -- Rank 3 Skill & Count
    MAX(CASE WHEN Skill_Rank = 3 THEN primary_skill END) AS Top_Skill_3,
    MAX(CASE WHEN Skill_Rank = 3 THEN Total_Freelancers END) AS Count_3

FROM 
    RankedSkills
WHERE 
    Skill_Rank <= 3
GROUP BY 
    Age_Decade
ORDER BY 
    Age_Decade;