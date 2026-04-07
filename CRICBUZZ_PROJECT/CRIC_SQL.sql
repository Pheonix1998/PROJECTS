USE [PRACTICEDB];

SELECT * FROM [dbo].[match_batting_stats];
SELECT * FROM [dbo].[match_bowling_stats];

--Q1: Find all players who represent Ireland. Display their full name, playing role, batting style, and bowling style.
SELECT bts.[inningsid],
       bts.[batteamname] AS Country,
       bts.[name] AS Batsman,
       bts.[runs]
FROM [dbo].[match_batting_stats] AS bts
WHERE [batteamname] = 'Ireland'
ORDER BY [runs] DESC;


-- Q2: Show all match details (Innings 1)
SELECT [inningsid],
       [batteamname] AS Country,
SUM([runs]) AS Details
FROM [dbo].[match_batting_stats]
GROUP BY [inningsid], [batteamname];

-- Q3: Top 10 highest run scorers in the dataset.

    SELECT TOP 10
           [batteamname] AS Country,
           [name] AS Batsman,
           SUM([runs]) AS Total_Runs
    FROM [dbo].[match_batting_stats]
    GROUP BY [batteamname] ,[name]
    ORDER BY Total_Runs DESC;

-- Q4: Find players who scored more than 20 runs.
    SELECT 
           [batteamname] AS Country,
           [name] AS Batsman,
           [runs]AS Runs
    FROM [dbo].[match_batting_stats]
    WHERE [runs] > 20;

-- Q5: Calculate total runs scored by each team.
    SELECT 
           [batteamname] AS Country,
           SUM([runs]) AS Total_Runs
    FROM [dbo].[match_batting_stats]
    GROUP BY [batteamname];

-- Q6: Count how many players batted for each team.
    SELECT 
           [batteamname] AS Country,
           COUNT(DISTINCT([name])) AS Total_Players
    FROM [dbo].[match_batting_stats]
    GROUP BY [batteamname];

-- Q7: Find the highest individual score in the match.
SELECT DISTINCT TOP 1
      ([name]) AS Names,
      MAX([runs]) OVER (PARTITION BY [name]) AS Max_Runs
FROM [dbo].[match_batting_stats]
ORDER BY Max_Runs DESC;

-- Q8: List all bowlers who bowled a maiden over.
SELECT DISTINCT([name])
FROM [dbo].[match_bowling_stats]
WHERE [maidens] <> 0;

-- Q9: Players who scored 10+ runs AND took 1+ wicket (All-rounders).
SELECT DISTINCT
       bts.[name] AS Batsmen,
       bts.[batteamname] AS Country,
       bts.[runs] AS Runs,
       bls.[name] AS Bowlers,
       bls.[wickets] AS Wickets
FROM [dbo].[match_batting_stats] AS bts
INNER JOIN [dbo].[match_bowling_stats] AS bls
ON bts.[inningsid] = bls.[inningsid]
WHERE bts.runs >= 10 AND bls.[wickets] >1
ORDER BY Runs DESC;

-- Q10: Best bowling figures (Most wickets, then lowest runs).
SELECT TOP 5 name, wickets, runs, economy 
FROM match_bowling_stats 
ORDER BY wickets DESC, runs ASC;

-- Q11. Identify high-scoring batting pairs (Consecutive players).
WITH BattingOrder AS (
    SELECT name, runs, inningsid, ROW_NUMBER() OVER(ORDER BY (SELECT NULL)) as pos
    FROM match_batting_stats
)
SELECT a.name as Player1, b.name as Player2, (a.runs + b.runs) as combined_runs 
FROM BattingOrder a 
JOIN BattingOrder b ON a.pos = b.pos - 1 AND a.inningsid = b.inningsid 
WHERE (a.runs + b.runs) >= 50;

-- Q12. Bowling economy analysis.
SELECT 
    [name] AS Bowlers,
    CAST(AVG(CAST([economy] AS FLOAT)) AS INT) AS AVG_ECONOMY,
    SUM(CAST([wickets] AS INT)) AS TOTAL_WICKETS
FROM [dbo].[match_bowling_stats]
GROUP BY [name];

-- Q13: Most economical bowlers (at least 2 overs).

SELECT DISTINCT
     [name],
     CAST([overs] AS float) AS Overs,
     [economy]
FROM [dbo].[match_bowling_stats]
WHERE CAST([overs] AS float) >= 2
ORDER BY [economy] ASC;

-- Q14: Player Performance Ranking (Custom Formula).

SELECT name, 
       (runs * 0.1) + (fours * 0.5) + (sixes * 1.0) as batting_points 
FROM match_batting_stats 
ORDER BY batting_points DESC;

-- Q15: Categorizing Player Form
WITH CTE_CAT AS
(
    SELECT 
           [name] AS Batsmen,
           [batteamname] AS Country,
           [runs] AS Runs,
    NTILE(3) OVER (ORDER BY [runs] DESC) AS Segments
    FROM [dbo].[match_batting_stats]
)
SELECT * ,
CASE 
    WHEN Segments = 1 THEN 'GOOD'
    WHEN Segments = 2 THEN 'INTERMEDIATE'
    WHEN Segments = 3 THEN 'LOW'
END AS Performance
FROM CTE_CAT;