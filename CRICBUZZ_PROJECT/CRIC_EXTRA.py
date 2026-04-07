import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ==========================================
# ⚙️ PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Executive Cricket Analytics", layout="wide", page_icon="🏏")
st.title("🏏 Match Performance Executive Dashboard")
st.markdown("Live analytics dashboard using CSV data source (Cloud Deployable).")

# ==========================================
# 📥 DATA LOADING (CSV)
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    df_bat = pd.read_csv("match_batting_stats.csv")
    df_bowl = pd.read_csv("match_bowling_stats.csv")

    # Convert to numeric safely
    bat_num_cols = ['runs', 'balls', 'fours', 'sixes']
    for col in bat_num_cols:
        if col in df_bat.columns:
            df_bat[col] = pd.to_numeric(df_bat[col], errors='coerce')

    # Strike Rate
    if 'strikeRate' not in df_bat.columns:
        df_bat['strikeRate'] = (df_bat['runs'] / df_bat['balls'] * 100).fillna(0)

    bowl_num_cols = ['overs', 'maidens', 'runs', 'wickets', 'economy']
    for col in bowl_num_cols:
        if col in df_bowl.columns:
            df_bowl[col] = pd.to_numeric(df_bowl[col], errors='coerce')

    return df_bat, df_bowl


def save_data(df_bat, df_bowl):
    df_bat.to_csv("match_batting_stats.csv", index=False)
    df_bowl.to_csv("match_bowling_stats.csv", index=False)


df_batting, df_bowling = load_data()

# ==========================================
# 🎛️ SIDEBAR FILTERS
# ==========================================
st.sidebar.header("Filter Parameters")

teams = ["All Teams"] + df_batting['batteamname'].dropna().unique().tolist()
selected_team = st.sidebar.selectbox("Select Batting Team", teams)

if selected_team != "All Teams":
    df_batting = df_batting[df_batting['batteamname'] == selected_team]
    if 'batteamname' in df_bowling.columns:
        df_bowling = df_bowling[df_bowling['batteamname'] == selected_team]

st.sidebar.markdown("---")
st.sidebar.info("Data Source: CSV Files")

# ==========================================
# 📊 DASHBOARD TABS
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview KPIs", "Batting Analytics", "Bowling Analytics", "SQL Analytics", "🛠️ Data Management (CRUD)"
])

# --- TAB 1: OVERVIEW KPIs ---
with tab1:
    st.subheader("Match Executive Summary")
    col1, col2, col3, col4 = st.columns(4)

    runs_sum = int(df_batting['runs'].sum())
    wkts_sum = int(df_bowling['wickets'].sum())
    fours = df_batting['fours'].sum()
    sixes = df_batting['sixes'].sum()

    col1.metric("Total Runs Scored", runs_sum)
    col2.metric("Total Boundaries (4s/6s)", int(fours + sixes))
    col3.metric("Total Wickets Fallen", wkts_sum)

    total_balls = df_batting['balls'].sum()
    overall_sr = (runs_sum / total_balls) * 100 if total_balls > 0 else 0
    col4.metric("Avg Match Strike Rate", f"{overall_sr:.2f}")

    st.markdown("### Raw Data")
    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(df_batting, use_container_width=True)
    with c2:
        st.dataframe(df_bowling, use_container_width=True)

# --- TAB 2: BATTING ANALYTICS ---
with tab2:
    st.subheader("Batting Performance & Momentum")

    fig_scatter = px.scatter(
        df_batting, x="strikeRate", y="runs", size="balls", color="name",
        hover_name="name", title="Impact Matrix: Runs vs Strike Rate"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    df_boundaries = df_batting[['name', 'fours', 'sixes']].melt(
        id_vars='name', var_name='Boundary Type', value_name='Count'
    )
    df_boundaries = df_boundaries[df_boundaries['Count'] > 0]

    fig_bar = px.bar(
        df_boundaries, x="name", y="Count", color="Boundary Type",
        title="Boundary Distribution per Player", barmode="group"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 3: BOWLING ANALYTICS ---
with tab3:
    st.subheader("Bowling Economy & Impact")

    df_bowling_sorted = df_bowling.sort_values(by='economy', ascending=True)
    fig_eco = px.bar(
        df_bowling_sorted, x="name", y="economy", text="economy",
        title="Most Economical Bowlers"
    )
    st.plotly_chart(fig_eco, use_container_width=True)

    fig_wkts = px.scatter(
        df_bowling, x="runs", y="wickets", size="overs", color="name",
        title="Cost of Wickets"
    )
    st.plotly_chart(fig_wkts, use_container_width=True)

# --- TAB 4: ANALYTICS ---
with tab4:
    st.subheader("Advanced Insights")

    top_scorers = df_batting.sort_values(by='runs', ascending=False)
    fig_q3 = px.bar(top_scorers, x='name', y='runs', title="Top Run Scorers")
    st.plotly_chart(fig_q3, use_container_width=True)

    df_allround = pd.merge(df_batting, df_bowling, on='name', how='inner')
    fig_q9 = px.scatter(df_allround, x='runs_x', y='wickets', size='runs_x', color='name',
                        title="All-Rounder Impact")
    st.plotly_chart(fig_q9, use_container_width=True)

# --- TAB 5: CRUD ---
with tab5:
    st.subheader("Data Management (CSV)")

    crud_action = st.radio("Select Operation:", ["Add", "Update", "Delete"], horizontal=True)

    # ADD
    if crud_action == "Add":
        name = st.text_input("Player Name")
        team = st.text_input("Team Name")
        runs = st.number_input("Runs", 0)
        balls = st.number_input("Balls", 0)
        fours = st.number_input("Fours", 0)
        sixes = st.number_input("Sixes", 0)

        if st.button("Add Record"):
            new_row = pd.DataFrame([[name, team, runs, balls, fours, sixes]],
                                   columns=df_batting.columns)
            df_batting = pd.concat([df_batting, new_row], ignore_index=True)
            save_data(df_batting, df_bowling)
            st.success("Record Added")

    # UPDATE
    elif crud_action == "Update":
        player = st.selectbox("Select Player", df_batting['name'].unique())
        new_runs = st.number_input("New Runs", 0)

        if st.button("Update Record"):
            df_batting.loc[df_batting['name'] == player, 'runs'] = new_runs
            save_data(df_batting, df_bowling)
            st.success("Record Updated")

    # DELETE
    elif crud_action == "Delete":
        player = st.selectbox("Select Player to Delete", df_batting['name'].unique())

        if st.button("Delete Record"):
            df_batting = df_batting[df_batting['name'] != player]
            save_data(df_batting, df_bowling)
            st.success("Record Deleted")