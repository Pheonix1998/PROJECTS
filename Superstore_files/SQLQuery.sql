USE [PRACTICEDB];

SELECT * FROM sys.indexes;
sp_helpindex'[dbo].[Final_Cleaned_Superstore]';

ALTER TABLE [dbo].[Final_Cleaned_Superstore]
ALTER COLUMN Returned VARCHAR(30)

SELECT TOP 5 *
FROM [dbo].[Final_Cleaned_Superstore]

-- Write a query to retrieve a list of all unique Cities and States located in the 'West' region.
SELECT DISTINCT [City], [State],[Regional Manager]
FROM [dbo].[Final_Cleaned_Superstore]
WHERE [Region] = 'West'

-- High-Value Orders: Find all orders where the Sales amount is greater than $5,000, ordered from highest to lowest sales.
SELECT [Order ID], FORMAT([Order Date], 'dd/MM/yyyy') AS Order_Date
FROM [dbo].[Final_Cleaned_Superstore]
WHERE [Sales] > 5000
ORDER BY [Sales] DESC

-- Specific Managers: List all orders handled by 'Chuck Magee' or 'Sadie Pawthorne' that were shipped via 'First Class'.
SELECT [Order ID],[Regional Manager],[Ship Mode]
FROM [dbo].[Final_Cleaned_Superstore]
WHERE [Regional Manager] = 'Chuck Magee' OR [Regional Manager] = 'Sadie Pawthorne' AND [Ship Mode] = 'First Class'

-- Returned Items: Retrieve the Order ID, Customer Name, and Category for every order that was marked as 'Yes' in the Returned column.
SELECT [Order ID],[Customer Name],[Category],[Returned]
FROM [dbo].[Final_Cleaned_Superstore]
WHERE [Returned] = 'Yes'

-- Manager Performance: Calculate the total Sales and total Profit for each Regional Manager.
SELECT [Regional Manager],
ROUND(SUM([Sales]),2) AS Total_Sales,
ROUND(SUM([Profit]),2) AS Total_Profit,
CONCAT(ROUND(SUM([Profit]) * 100.0 / SUM([Sales]),2), ' ', '%') AS Profit_Margin
FROM [dbo].[Final_Cleaned_Superstore]
GROUP BY [Regional Manager]

-- Profitability Check: Which Sub-Category has the highest average profit?
WITH CTE_AVG_PRFT AS
(
	SELECT [Sub-Category],
	ROUND(AVG([Profit]),2) AS Average_Profit
	FROM [dbo].[Final_Cleaned_Superstore]
	GROUP BY [Sub-Category]
)
SELECT *,
DENSE_RANK() OVER (ORDER BY Average_Profit DESC) AS Ranks
FROM CTE_AVG_PRFT

-- Regional Health: Find the total number of orders placed in each Region. Only show regions that have more than 500 orders.
SELECT [Region],
COUNT(DISTINCT([Order ID])) AS Number_of_Orders
FROM [dbo].[Final_Cleaned_Superstore]
GROUP BY [Region]
HAVING COUNT([Order ID]) > 500
ORDER BY COUNT(DISTINCT([Order ID])) DESC

-- Profit Margin Analysis: Write a query to calculate the Profit Margin (Profit divided by Sales) for each Category.
SELECT [Category],
CONCAT(ROUND(SUM([Profit]) * 100 / SUM([Sales]),2), ' ', '%') AS Profit_Margin
FROM [dbo].[Final_Cleaned_Superstore]
GROUP BY [Category]
ORDER BY ROUND(SUM([Profit]) * 100 / SUM([Sales]),2) DESC

-- Return Impact: Use a CASE statement to create a column called Status. If Returned is 'Yes', label it 'Refunded'; otherwise, label it 'Earned'. Summarize the total Sales for these two groups.
WITH CTE_SUMMARY AS
(
	SELECT [Returned],[Sales],
	CASE
		WHEN [Returned] = 'Yes' THEN 'Refunded'
		WHEN [Returned] = 'No' THEN 'Earned'
		END AS Groupings
	FROM [dbo].[Final_Cleaned_Superstore]
)
SELECT Groupings,
ROUND(SUM([Sales]),2) AS Total_Sales
FROM CTE_SUMMARY
GROUP BY Groupings
ORDER BY ROUND(SUM([Sales]),2) DESC

-- Loss Leaders: Identify all Sub-Categories where the total Profit is negative (less than 0), but the total Sales are greater than $10,000.
SELECT [Sub-Category],
ROUND(SUM([Profit]),2) AS Total_Profit,
ROUND(SUM([Sales]),2) AS Total_Sales
FROM [dbo].[Final_Cleaned_Superstore]
GROUP BY [Sub-Category]
HAVING SUM([Sales]) > 10000 AND SUM([Profit]) < 0

-- Geospatial Focus: Find the top 10 Cities in terms of total profit within the state of California.
SELECT TOP 10 [City],
ROUND(SUM ([Profit]),2) AS Total_Profit
FROM [dbo].[Final_Cleaned_Superstore]
GROUP BY [City]
HAVING EXISTS ( SELECT 1 FROM [dbo].[Final_Cleaned_Superstore] WHERE [State] = 'California')
ORDER BY SUM ([Profit]) DESC

-- Monthly Trends: Using Order Date, calculate the total Sales for each month in the year 2021.
SELECT
DATENAME(MONTH,[Order Date]) AS Months,
ROUND(SUM([Sales]),2) AS Total_Sales
FROM [dbo].[Final_Cleaned_Superstore]
GROUP BY DATENAME(MONTH,[Order Date])
HAVING EXISTS (SELECT 1 FROM [dbo].[Final_Cleaned_Superstore] WHERE YEAR([Order Date]) = 2021)
ORDER BY ROUND(SUM([Sales]),2) DESC

-- Customer Loyalty (CTE): Create a CTE that identifies customers who have placed more than 10 orders. Join this CTE back to the main table to find their total lifetime Profit.
WITH CTE_Loyal_Customers AS
(
    SELECT 
    [Customer ID],
    COUNT([Order ID]) AS Order_Count
    FROM [dbo].[Final_Cleaned_Superstore]
    GROUP BY [Customer ID]
    HAVING COUNT([Order ID]) > 10
)
SELECT 
	  CLC.Order_Count,
	  FCS.[Customer ID],
	  ROUND(SUM(FCS.[Profit]),2) AS Total_Profit
	  FROM [dbo].[Final_Cleaned_Superstore] AS FCS
	  LEFT JOIN CTE_Loyal_Customers AS CLC
	  ON FCS.[Customer ID] = CLC.[Customer ID]
	  GROUP BY CLC.Order_Count, FCS.[Customer ID]
	  HAVING CLC.Order_Count IS NOT NULL AND   ROUND(SUM(FCS.[Profit]),2) >= 0
	  ORDER BY  SUM(FCS.[Profit]) DESC

-- Ranking Sub-Categories: Use the RANK() or DENSE_RANK() function to rank Sub-Categories by their total sales within each Category.
WITH CTE_SUB_CAT AS
(
	SELECT [Sub-Category],[Category],
	ROUND(SUM([Sales]),2) AS Total_Sales
	FROM [dbo].[Final_Cleaned_Superstore]
	GROUP BY [Sub-Category],[Category]
)
SELECT *,
DENSE_RANK () OVER (PARTITION BY [Category] ORDER BY Total_Sales DESC) AS Rankings
FROM CTE_SUB_CAT

-- Return Rate by Manager: Calculate the Return Rate for each Regional Manager (Total Returned Orders / Total Orders).
SELECT 
    [Regional Manager],
    COUNT(*) AS Total_Orders,
    SUM(CASE 
		WHEN [Returned] = 'Yes' THEN 1 
		ELSE 0 
		END) AS Total_Returns,
    CONCAT(CAST(SUM(CASE WHEN [Returned] = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(10, 2)), ' ' , '%') AS Return_Rate_Prct
FROM [dbo].[Final_Cleaned_Superstore]
GROUP BY [Regional Manager]
ORDER BY Return_Rate_Prct DESC;