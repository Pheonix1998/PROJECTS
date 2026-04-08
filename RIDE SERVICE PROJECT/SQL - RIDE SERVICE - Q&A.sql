USE [PRACTICEDB]

-- 1. Retrieve all successful bookings:
SELECT f.*
FROM Fact_Bookings f
JOIN Dim_Ride_Status s 
    ON f.Status_ID = s.Status_ID
WHERE s.Booking_Status = 'Success';

-- 2. Find the average ride distance for each vehicle type:
SELECT 
    Vehicle_Type, 
    ROUND(AVG(Ride_Distance),2) AS Avg_Ride_Distance
FROM Fact_Bookings
GROUP BY Vehicle_Type;

-- 3. Get the total number of cancelled rides by customers:
SELECT COUNT(f.Booking_ID) AS Total_Customer_Cancellations
FROM Fact_Bookings f
JOIN Dim_Ride_Status s 
    ON f.Status_ID = s.Status_ID
WHERE s.Booking_Status = 'Canceled by Customer';

-- 4. List the top 5 customers who booked the highest number of rides:
SELECT TOP 5
    [Customer_ID], COUNT([Booking_ID]) AS Total_Bookings
FROM [dbo].[Fact_Bookings]
GROUP BY [Customer_ID]
ORDER BY Total_Bookings DESC;

-- 5. Get the number of rides cancelled by drivers due to personal and car-related issues:
SELECT COUNT(f.Booking_ID) AS Total_Driver_Issues
FROM Fact_Bookings f
JOIN Dim_Ride_Status s 
    ON f.Status_ID = s.Status_ID
WHERE s.Canceled_Rides_by_Driver = 'Personal & Car related issue';

--6. Find the maximum and minimum driver ratings for Prime Sedan bookings:
SELECT 
    MAX(Driver_Ratings) AS Max_Rating, 
    MIN(Driver_Ratings) AS Min_Rating
FROM Fact_Bookings
WHERE Vehicle_Type = 'Prime Sedan';

-- 7. Retrieve all rides where payment was made using UPI:
SELECT Vehicle_Type, Payment_Method
FROM Fact_Bookings
WHERE Payment_Method = 'UPI';

-- 8. Find the average customer rating per vehicle type:
SELECT [Vehicle_Type],
ROUND(AVG([Customer_Rating]),2) AS Average_rating
FROM [dbo].[Fact_Bookings]
GROUP BY [Vehicle_Type]
ORDER BY Average_rating DESC;

-- 9.Calculate the total booking value of rides completed successfully
SELECT CONCAT(SUM(fB.[Booking_Value])/100000, ' ', 'K') AS TOTAL_BOOKINGS
FROM [dbo].[Fact_Bookings] AS fB
LEFT JOIN [dbo].[Dim_Ride_Status] AS RS
ON RS.[Status_ID] = fb.[Status_ID]

-- 10. List all incomplete rides along with the reason:
SELECT 
    f.Booking_ID, 
    s.Incomplete_Rides_Reason
FROM Fact_Bookings f
JOIN Dim_Ride_Status s 
    ON f.Status_ID = s.Status_ID
WHERE s.Incomplete_Rides = 'Yes';