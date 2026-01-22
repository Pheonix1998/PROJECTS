USE [MyDatabase]
SELECT *
FROM [dbo].[Medibuddy insurance data personal details]

USE [MyDatabase]
SELECT *
FROM [dbo].[Medibuddy Insurance Data Price]

-- Check duplicates in Excel 1
USE [MyDatabase]
SELECT "Policy_no", COUNT(*)
FROM [dbo].[Medibuddy insurance data personal details]
GROUP BY "Policy_no"
HAVING COUNT(*) > 1;

-- Check duplicates in Excel 2
SELECT "Policy_no", COUNT(*)
FROM [dbo].[Medibuddy Insurance Data Price]
GROUP BY "Policy_no"
HAVING COUNT(*) > 1;


--JOINED TABLE
USE [MyDatabase];

SELECT
    r.Policy_no,
    r.children,
    r.smoker,
    r.region,
    p.age,
    p.sex,
    p.bmi,
    p.charges_in_INR
FROM [Medibuddy insurance data personal details] r
LEFT JOIN [Medibuddy Insurance Data Price] p
    ON r.Policy_no = p.Policy_no;
