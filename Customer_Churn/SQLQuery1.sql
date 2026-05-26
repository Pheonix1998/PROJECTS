USE [PRACTICEDB];

SELECT TOP 2 * FROM [dbo].[Fact_Customer_Analytics]
SELECT TOP 2 * FROM [dbo].[Dim_Segment]
SELECT TOP 2 * FROM [dbo].[Dim_Demographics]

-- Friction Analysis: Is there a significant difference in the cart_abandonment_rate between customers who churned and those who stayed? (Use: AVG() and GROUP BY churn_flag)
SELECT [churn_flag],
CASE WHEN [churn_flag] = 0 THEN 'Not_Churned'
	 WHEN [churn_flag] = 1 THEN 'Churned'
END AS Segments,
CONCAT(ROUND(AVG([cart_abandonment_rate])*100,2), ' ', '%') AS average_rate_percent
FROM [dbo].[Fact_Customer_Analytics]
GROUP BY [churn_flag]
ORDER BY CONCAT(ROUND(AVG([cart_abandonment_rate])*100,2), ' ', '%') DESC;


-- Do customers with a loyalty_score above 70 actually churn less than those with a score below 30? (Use: CASE WHEN loyalty_score > 70 THEN 'High' ELSE 'Low' END)
SELECT [churn_flag],
CASE WHEN [churn_flag] = 0 THEN 'Not_Churned'
	 WHEN [churn_flag] = 1 THEN 'Churned'
END AS Flags,
COUNT (CASE WHEN [loyalty_score] > 70 THEN [loyalty_score] END) AS Cust_greater_than_70,
COUNT (CASE WHEN [loyalty_score] < 30 THEN [loyalty_score] END) AS Cust_lower_than_30
FROM[dbo].[Fact_Customer_Analytics]
GROUP BY [churn_flag];

-- Discount Dependency: Does a high discount_usage_rate create loyal customers, or does it just attract bargain-hunters who churn anyway?
SELECT
CASE WHEN [discount_usage_rate] >=0.7 THEN '70% High'
	 WHEN [discount_usage_rate] <0.7 AND [discount_usage_rate] >=0.4 THEN '40% Medium'
	 WHEN [discount_usage_rate] <0.4 THEN 'Low'
END AS Discounts,
COUNT([customer_id]) AS Total_Customers,
ROUND(AVG(CAST(churn_flag AS FLOAT)*100.0),2) AS churn_perct,
ROUND(AVG([loyalty_score]),2) AS Loyalty_scores,
ROUND(AVG(total_spent), 2) AS Avg_Total_Spent,
ROUND(AVG(purchase_frequency), 2) AS Avg_Purchase_Freq,
ROUND(AVG([avg_order_value]),2) AS AOV,
ROUND(avg([website_visits]),2) as UI_visits
FROM [dbo].[Fact_Customer_Analytics]
GROUP BY (CASE WHEN [discount_usage_rate] >=0.7 THEN '70% High'
	           WHEN [discount_usage_rate] <0.7 AND [discount_usage_rate] >=0.4 THEN '40% Medium'
	           WHEN [discount_usage_rate] <0.4 THEN 'Low'
          END)
ORDER BY Discounts DESC;

-- Channel Experience: Are customers who prefer "Online" shopping churning at a higher rate than "In-Store" shoppers, indicating a poor website UI? (Use: INNER JOIN on Dim_Segment and GROUP BY preferred_channel)
WITH CTE_CHURNS AS
(
SELECT 
		sg.[preferred_channel],
		COUNT(fca.[customer_id]) AS Total_Customers,
		SUM(CASE WHEN fca.[churn_flag] = 1 THEN fca.churn_flag END) AS churns
		FROM [dbo].[Fact_Customer_Analytics] AS fca
		LEFT JOIN [dbo].[Dim_Segment] AS sg
		ON sg.segment_id = fca.segment_id
GROUP BY sg.preferred_channel
)
SELECT *,
CONCAT((ROUND(CAST(ctc.churns as float)/ctc.Total_Customers,2)) *100.0, ' ', '%') AS Churn_perct
FROM CTE_CHURNS as ctc
ORDER BY ctc.Total_Customers DESC;

-- The Recency Tipping Point: At what specific recency_days bucket (e.g., 0-30, 31-60, 61-90, 90+) does the churn rate jump past 50%? (Use: CASE WHEN to create recency buckets)
SELECT 
	  CASE WHEN [recency_days] >= 0 AND [recency_days] <=30 THEN 'Recency_1'
		   WHEN [recency_days] > 30 AND [recency_days] <=60 THEN 'Recency_2'
		   WHEN [recency_days] > 60 AND [recency_days] <=90 THEN 'Recency_3'
		   WHEN [recency_days] > 90 THEN 'Recency_4'
	  END AS Recencies,
CONCAT(ROUND(AVG(CAST([churn_flag] AS FLOAT))*100.00,2), ' ' ,'%') AS Churnings_prct
FROM [dbo].[Fact_Customer_Analytics] as fca
GROUP BY ( CASE WHEN [recency_days] >= 0 AND [recency_days] <=30 THEN 'Recency_1'
		   WHEN [recency_days] > 30 AND [recency_days] <=60 THEN 'Recency_2'
		   WHEN [recency_days] > 60 AND [recency_days] <=90 THEN 'Recency_3'
		   WHEN [recency_days] >90 THEN 'Recency_4'
	  END )
ORDER BY Churnings_prct DESC;

-- Digital Disengagement: For active (non-churned) customers, how many have an email_open_rate below 10% AND website_visits below 5? (Use: WHERE churn_flag = 0 AND email_open_rate < 0.10 AND website_visits < 5)
WITH CTE_NEW AS
(
SELECT 
	COUNT(CASE WHEN [churn_flag] = 0 THEN [churn_flag] END) AS Non_churned
FROM [dbo].[Fact_Customer_Analytics]
WHERE [email_open_rate] < 0.1 AND [website_visits] < 5
GROUP BY CASE WHEN [churn_flag] = 0 THEN [churn_flag] END
)
SELECT * FROM CTE_NEW
WHERE Non_churned <> 0

-- The VIP Flight Risk: How many of our "VIP" customers are currently showing high cart_abandonment_rate (>50%) but haven't churned yet?
   
   SELECT COUNT(ds.[customer_segment]) AS VIP_Customers
    FROM [dbo].[Fact_Customer_Analytics] AS fca
    LEFT JOIN [dbo].[Dim_Segment] AS ds
    ON ds.segment_id = fca.segment_id
    WHERE ds.[customer_segment] = 'VIP' AND fca.[cart_abandonment_rate] > 0.5 AND [churn_flag] = 0

-- The 90-Day Win-Back List: Which highly valuable customers (total_spent > $2,000) have not purchased in the last 75 to 146 days and need an immediate targeted email campaign?

SELECT 
[customer_id],[total_spent],[email_open_rate]*100.0 AS email_open_rates,[recency_days]
FROM [dbo].[Fact_Customer_Analytics] fca
WHERE [total_spent] > 2000 AND [recency_days] BETWEEN 75 AND 146
ORDER BY [recency_days] DESC

-- Checkout Audit Trigger: Which specific demographics (Age + Region) are experiencing the highest cart abandonment, so the UX team knows exactly who to interview for website improvements? (Use: JOIN on Dim_Demographics and ORDER BY AVG(cart_abandonment_rate) DESC)

SELECT dd.[region],
	CASE WHEN dd.[age_group] = '18-24' THEN 'Gen_Z'
		 WHEN dd.[age_group] = '25-34' THEN 'Young_Adults'
		 WHEN dd.[age_group] = '35-44' THEN 'Mature_Adults'
		 WHEN dd.[age_group] = '45-54' THEN 'Older_Adults'
		 WHEN dd.[age_group] = '55+' THEN 'Senior_Citizens'
	END AS Age_Segments,
CONCAT(ROUND(AVG(fca.[cart_abandonment_rate])*100.00,2), ' ', '%') AS Average_Cart_abandonment_prct
FROM [dbo].[Fact_Customer_Analytics] AS fca
LEFT JOIN [dbo].[Dim_Demographics] AS dd
ON dd.demographic_id = fca.demographic_id
GROUP BY dd.[region],
	CASE WHEN dd.[age_group] = '18-24' THEN 'Gen_Z'
		 WHEN dd.[age_group] = '25-34' THEN 'Young_Adults'
		 WHEN dd.[age_group] = '35-44' THEN 'Mature_Adults'
		 WHEN dd.[age_group] = '45-54' THEN 'Older_Adults'
		 WHEN dd.[age_group] = '55+' THEN 'Senior_Citizens'
	END
ORDER BY CONCAT(ROUND(AVG(fca.[cart_abandonment_rate])*100.00,2), ' ', '%') DESC

-- Mobile App Push Campaign: How many "New" customers who prefer the "Mobile App" have an engagement_score below 40? (These users need a push notification sequence to build habits)
SELECT COUNT(fca.[customer_id]) AS Customers, DS.[customer_segment]
FROM [dbo].[Fact_Customer_Analytics] AS FCA
LEFT JOIN [dbo].[Dim_Segment] AS DS
ON DS.segment_id = fca.segment_id
WHERE DS.[preferred_channel] = 'Mobile APP' AND fca.engagement_score < 40
GROUP BY  DS.[customer_segment]
ORDER BY COUNT(fca.[customer_id]) DESC

-- Total Revenue Lost: What is the total historical revenue (SUM(total_spent)) attributed to customers who have churned?
SELECT [churn_flag],
CONCAT(ROUND(SUM([total_spent])/1000000,2), ' ' ,'Million') AS Revenue
FROM [dbo].[Fact_Customer_Analytics]
WHERE [churn_flag] = 1
GROUP BY [churn_flag]

-- Average Lifetime Value (LTV) Disparity: How much more, on average, does a retained customer spend compared to a churned customer?

WITH CTE_EXPENSES AS
(
SELECT
	ROUND(AVG(CASE WHEN [churn_flag] = 0 THEN [total_spent] END),2) AS Retained_Spent,
	ROUND(AVG(CASE WHEN [churn_flag] = 1 THEN [total_spent] END),2) AS Churned_Spent
FROM [dbo].[Fact_Customer_Analytics]
)
SELECT *,
(Retained_Spent - Churned_Spent) AS More_Amount
FROM CTE_EXPENSES

-- Demographic Bleed: Which Region is losing the most overall revenue to churn, and which Age Group within that region is driving it?
SELECT 
	dd.[region], FCA.[churn_flag],
		CASE WHEN dd.[age_group] = '18-24' THEN 'Gen_Z'
		 WHEN dd.[age_group] = '25-34' THEN 'Young_Adults'
		 WHEN dd.[age_group] = '35-44' THEN 'Mature_Adults'
		 WHEN dd.[age_group] = '45-54' THEN 'Older_Adults'
		 WHEN dd.[age_group] = '55+' THEN 'Senior_Citizens'
	END AS Age_Segments,
	CONCAT(ROUND(SUM(FCA.[total_spent]/1000000),2), ' ' , 'Millions') AS Revenue_bleeds
	FROM [dbo].[Fact_Customer_Analytics] AS FCA
	LEFT JOIN [dbo].[Dim_Demographics] AS dd
	ON FCA.demographic_id = dd.demographic_id
	GROUP BY dd.[region], FCA.[churn_flag],
		CASE WHEN dd.[age_group] = '18-24' THEN 'Gen_Z'
		 WHEN dd.[age_group] = '25-34' THEN 'Young_Adults'
		 WHEN dd.[age_group] = '35-44' THEN 'Mature_Adults'
		 WHEN dd.[age_group] = '45-54' THEN 'Older_Adults'
		 WHEN dd.[age_group] = '55+' THEN 'Senior_Citizens'
	END
	HAVING FCA.churn_flag = 1
	ORDER BY CONCAT(ROUND(SUM(FCA.[total_spent]/1000000),2), ' ' , 'Millions') DESC

-- Segment Health Check: What is the exact churn rate percentage for each customer_segment (New, Returning, Loyal, VIP)? (Is the loyalty program actually working?)

	SELECT ds.[customer_segment],
	COUNT([customer_id]) AS Total_Customers,
	CONCAT((ROUND(SUM(CASE WHEN [churn_flag] = 1 THEN 1 END)/ CAST(COUNT(FCA.[customer_id]) AS FLOAT),2)) * 100, ' ', '%') AS Churn_Rate_Percentages
	FROM [dbo].[Fact_Customer_Analytics] AS FCA
	LEFT JOIN [dbo].[Dim_Segment] AS ds
	ON FCA.segment_id = ds.segment_id
	GROUP BY ds.customer_segment
	ORDER BY CONCAT((ROUND(SUM(CASE WHEN [churn_flag] = 1 THEN 1 END)/ CAST(COUNT(FCA.[customer_id]) AS FLOAT),2)) * 100, ' ', '%') DESC