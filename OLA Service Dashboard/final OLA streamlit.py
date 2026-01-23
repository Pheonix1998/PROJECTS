# ===============================
# IMPORTS
# ===============================
import streamlit as st
import pandas as pd
import pyodbc
import matplotlib.pyplot as plt

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="OLA Ride Operations Dashboard",
    layout="wide"
)

# ===============================
# DATA LOAD (LOCAL SQL + CLOUD CSV FALLBACK)
# ===============================
@st.cache_data(show_spinner=False)
def load_data():
    try:
        # -------- LOCAL SQL SERVER (WORKS ONLY ON YOUR MACHINE) --------
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=TATHAGATA\\SQLEXPRESS;"
            "DATABASE=MyDatabase;"
            "Trusted_Connection=yes;"
        )

        query = """
            SELECT
                CAST(Date AS DATE) AS Date,
                Booking_Status,
                Vehicle_Type,
                V_TAT,
                C_TAT,
                Booking_Value,
                Payment_Method,
                Ride_Distance,
                Customer_Rating
            FROM dbo.[OLA Cleaned]
        """

        df = pd.read_sql(query, conn)
        conn.close()

    except Exception:
        # -------- STREAMLIT CLOUD FALLBACK --------
        df = pd.read_csv("OLA_Cleaned.csv")

    df["Date"] = pd.to_datetime(df["Date"])
    return df


df_raw = load_data()

# ===============================
# SIDEBAR FILTERS
# ===============================
st.sidebar.header("Business Controls")

vehicle_filter = st.sidebar.multiselect(
    "Vehicle Type",
    sorted(df_raw["Vehicle_Type"].dropna().unique())
)

status_filter = st.sidebar.multiselect(
    "Booking Status",
    sorted(df_raw["Booking_Status"].dropna().unique())
)

df = df_raw.copy()

if vehicle_filter:
    df = df[df["Vehicle_Type"].isin(vehicle_filter)]

if status_filter:
    df = df[df["Booking_Status"].isin(status_filter)]

# ===============================
# EXECUTIVE KPI LAYER
# ===============================
st.title("OLA Ride Operations – Business Impact Dashboard")

k1, k2, k3, k4, k5 = st.columns(5)

total_bookings = len(df)
success_rate = (df["Booking_Status"] == "Success").mean() * 100
avg_revenue = df.loc[df["Booking_Status"] == "Success", "Booking_Value"].mean()
avg_rating = df["Customer_Rating"].mean()
total_revenue = df.loc[df["Booking_Status"] == "Success", "Booking_Value"].sum()

k1.metric("Total Bookings", total_bookings)
k2.metric("Service Fulfillment (%)", round(success_rate, 2))
k3.metric("Avg Revenue per Ride", round(avg_revenue, 2))
k4.metric("Avg Customer Rating", round(avg_rating, 2))
k5.metric("Total Revenue", f"₹ {round(total_revenue, 2):,}")

st.markdown("""
**Executive Interpretation:**  
These KPIs summarize operational scale, reliability, monetization efficiency, and customer experience health.
""")

# ===============================
# BOOKING STATUS DISTRIBUTION
# ===============================
st.subheader("Booking Outcome Distribution")

status_counts = df["Booking_Status"].value_counts()
st.bar_chart(status_counts)

st.markdown("""
**Business Interpretation:**  
Cancellations and failures represent direct demand leakage.  
Improving fulfillment directly improves realized revenue and customer trust.
""")

# ===============================
# SERVICE FULFILLMENT BY VEHICLE TYPE
# ===============================
st.subheader("Service Fulfillment Rate by Vehicle Type")

fulfillment = (
    df.assign(Success=df["Booking_Status"] == "Success")
      .groupby("Vehicle_Type")["Success"]
      .mean()
      .mul(100)
      .sort_values(ascending=False)
)

st.bar_chart(fulfillment)

st.markdown("""
**Business Interpretation:**  
Vehicle categories with lower fulfillment indicate supply gaps or driver reluctance, requiring targeted onboarding or incentives.
""")

# ===============================
# REVENUE BY VEHICLE TYPE
# ===============================
st.subheader("Revenue Contribution by Vehicle Type")

vehicle_revenue = (
    df[df["Booking_Status"] == "Success"]
    .groupby("Vehicle_Type")["Booking_Value"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(vehicle_revenue)

st.markdown("""
**Business Interpretation:**  
High-revenue vehicle types should be prioritized for fleet expansion and premium positioning.
""")

# ===============================
# AVERAGE RIDE DISTANCE BY VEHICLE TYPE
# ===============================
st.subheader("Average Ride Distance by Vehicle Type")

avg_distance = (
    df[df["Booking_Status"] == "Success"]
    .groupby("Vehicle_Type")["Ride_Distance"]
    .mean()
    .sort_values(ascending=False)
)

st.bar_chart(avg_distance)

st.markdown("""
**Business Interpretation:**  
Longer trips increase fare potential but raise operational cost exposure and driver fatigue.
""")

# ===============================
# TURNAROUND TIME PERFORMANCE
# ===============================
st.subheader("Operational Efficiency – Turnaround Time")

tat_summary = df[["V_TAT", "C_TAT"]].mean()
st.bar_chart(tat_summary)

st.markdown("""
**Metric Definitions:**  
- **V_TAT:** Driver arrival latency  
- **C_TAT:** Customer waiting duration  

Lower turnaround times reduce cancellations and improve platform stickiness.
""")

# ===============================
# DEMAND LEAKAGE ANALYSIS
# ===============================
st.subheader("Demand Leakage – Cancellation vs Failure")

leakage = {
    "Cancelled by Customer": df["Booking_Status"].str.contains("Customer", case=False, na=False).sum(),
    "Cancelled by Driver": df["Booking_Status"].str.contains("Driver", case=False, na=False).sum(),
    "Driver Not Found": df["Booking_Status"].str.contains("Not Found", case=False, na=False).sum()
}

st.bar_chart(pd.Series(leakage))

st.markdown("""
**Business Interpretation:**  
Driver-led cancellations indicate supply instability, while customer cancellations reflect waiting-time dissatisfaction.
""")

# ===============================
# PAYMENT METHOD vs VALUE GENERATED (STACKED BAR)
# ===============================
st.subheader("Payment Method vs Value Generated")

payment_value = (
    df.groupby(["Payment_Method", "Booking_Status"])["Booking_Value"]
    .sum()
    .unstack(fill_value=0)
)

status_order = [
    "Canceled by Customer",
    "Canceled by Driver",
    "Driver Not Found",
    "Success"
]

payment_value = payment_value[[c for c in status_order if c in payment_value.columns]]

fig, ax = plt.subplots(figsize=(10, 6))

bottom = None
for status in payment_value.columns:
    ax.bar(
        payment_value.index,
        payment_value[status],
        bottom=bottom,
        label=status
    )
    bottom = payment_value[status] if bottom is None else bottom + payment_value[status]

for i, method in enumerate(payment_value.index):
    cumulative = 0
    for status in payment_value.columns:
        value = payment_value.loc[method, status]
        if value > 0:
            ax.text(i, cumulative + value / 2, f"{int(value):,}", ha="center", va="center", fontsize=9)
            cumulative += value

ax.set_title("Booking Types vs Value Generated", fontsize=14)
ax.set_xlabel("Payment Method")
ax.set_ylabel("Booking Value")
ax.legend(title="Booking Status", bbox_to_anchor=(1.02, 1), loc="upper left")
ax.grid(axis="y", alpha=0.3)

st.pyplot(fig)

st.markdown("""
**Business Interpretation:**  
Cash dominates gross value but also carries the highest cancellation leakage.  
UPI shows cleaner realization and better scalability from an operations standpoint.
""")

# ===============================
# DAILY BOOKING TREND – JULY
# ===============================
st.subheader("Daily Booking Trend – July")

july_df = df[df["Date"].dt.month == 7]
daily_bookings = july_df.groupby(july_df["Date"].dt.day).size()

st.line_chart(daily_bookings)

st.markdown("""
**Business Interpretation:**  
Daily volatility guides surge pricing, fleet allocation, and targeted promotions.
""")

# ===============================
# DAILY REVENUE TREND – JULY
# ===============================
st.subheader("Daily Revenue Trend – July")

daily_revenue = (
    july_df[july_df["Booking_Status"] == "Success"]
    .groupby(july_df["Date"].dt.day)["Booking_Value"]
    .sum()
)

st.line_chart(daily_revenue)

st.markdown("""
**Business Interpretation:**  
Revenue trends may diverge from volume due to pricing, distance, and vehicle mix effects.
""")