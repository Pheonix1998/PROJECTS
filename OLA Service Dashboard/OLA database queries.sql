Use [MyDatabase]
Select * 
From [dbo].[OLA Cleaned]


SELECT COUNT(*) AS total_rows_imported
FROM [dbo].[OLA Cleaned]

/* =========================================================
1. Retrieve all successful bookings
   Interpretation:
   This query filters completed transactions to analyze
   fulfilled demand and operational throughput.
========================================================= */
SELECT *
FROM [dbo].[OLA Cleaned]
WHERE Booking_Status = 'Success';

/* =========================================================
2. Find the average ride distance for each vehicle type
   Interpretation:
   Enables vehicle-wise utilization analysis and helps
   optimize fleet allocation strategy.
========================================================= */
SELECT     Vehicle_Type,
    AVG(Ride_Distance) AS avg_ride_distance
FROM [dbo].[OLA Cleaned]
GROUP BY Vehicle_Type;


/* =========================================================
3. Get the total number of cancelled rides by customers
   Interpretation:
   Quantifies customer-driven churn and demand volatility.
========================================================= */
SELECT 
    SUM(
        CASE 
            WHEN ISNUMERIC(Canceled_Rides_by_Customer) = 1 
            THEN CAST(Canceled_Rides_by_Customer AS INT) 
            ELSE 0 
        END
    ) AS total_customer_cancellations
FROM [dbo].[OLA Cleaned];


/* =========================================================
4. List the top 5 customers who booked the highest number of rides
   Interpretation:
   Identifies high-value and repeat customers for loyalty
   and retention initiatives.
========================================================= */
SELECT TOP 5
    Customer_ID,
    COUNT(Booking_ID) AS total_rides
FROM [dbo].[OLA Cleaned]
GROUP BY Customer_ID
ORDER BY total_rides ASC;

/* =========================================================
5. Get the number of rides cancelled by drivers due to
   personal and car-related issues
   Interpretation:
   Highlights driver-side operational risks and
   reliability bottlenecks.
========================================================= */
SELECT 
    COUNT(*) AS driver_cancellations_personal_car
FROM [dbo].[OLA Cleaned]
WHERE Incomplete_Rides_Reason IN ('Personal Issue', 'Car Issue');

/* =========================================================
6. Find the maximum and minimum driver ratings for
   Prime Sedan bookings
   Interpretation:
   Measures service quality dispersion for a premium
   vehicle segment by identifying best- and worst-case
   driver performance.
========================================================= */
SELECT 
    MAX(Driver_Ratings) AS max_driver_rating,
    MIN(Driver_Ratings) AS min_driver_rating
FROM [dbo].[OLA Cleaned]
WHERE Vehicle_Type = 'Prime Sedan';

/* =========================================================
7. Retrieve all rides where payment was made using UPI
   Interpretation:
   Supports digital payment adoption analysis and
   transaction channel optimization.
========================================================= */
SELECT *
FROM [dbo].[OLA Cleaned]
WHERE Payment_Method = 'UPI';

/* =========================================================
8. Find the average customer rating per vehicle type
   Interpretation:
   Benchmarks customer satisfaction across fleet categories.
========================================================= */
SELECT 
    Vehicle_Type,
    AVG(Customer_Rating) AS avg_customer_rating
FROM [dbo].[OLA Cleaned]
GROUP BY Vehicle_Type;


/* =========================================================
9. Calculate the total booking value of rides completed successfully
   Interpretation:
   Represents realized revenue and is a core financial KPI.
========================================================= */
SELECT 
    SUM(Booking_Value) AS total_successful_booking_value
FROM [dbo].[OLA Cleaned]
WHERE Booking_Status = 'Success';

/* =========================================================
10. List all incomplete rides along with the proper reason
    Interpretation:
    Enables root-cause analysis for service failures and
    operational improvement planning.
========================================================= */
SELECT 
    Booking_ID,
    Incomplete_Rides_Reason
FROM [dbo].[OLA Cleaned]
WHERE Booking_Status = 'Incomplete';


SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE '%OLA%';

SELECT DB_NAME() AS current_database;