import streamlit as st
import pandas as pd
import urllib
from sqlalchemy import create_engine, text
import plotly.express as px
import numpy as np  

# ==========================================
# ⚙️ PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Executive Cricket Analytics", layout="wide", page_icon="🏏")
st.title("🏏 Match Performance Executive Dashboard")
st.markdown("Live database connection extracting actionable insights from SQL Server.")

# ==========================================
# 🔌 DATABASE CONNECTION
# ==========================================
@st.cache_resource
def init_connection():
    SQL_SERVER_NAME = r'TATHAGATA\SQLEXPRESS'
    DATABASE_NAME = 'PRACTICEDB'
    params = urllib.parse.quote_plus(
        f'Driver={{ODBC Driver 17 for SQL Server}};'
        f'Server={SQL_SERVER_NAME};'
        f'Database={DATABASE_NAME};'
        f'Trusted_Connection=yes;'
    )
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

engine = init_connection()

# ==========================================
# 📥 DATA EXTRACTION (SQL QUERIES)
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    try:
        df_bat = pd.read_sql("SELECT * FROM match_batting_stats", con=engine)
        df_bowl = pd.read_sql("SELECT * FROM match_bowling_stats", con=engine)
        
        # Safely convert Batting columns to numeric (only if they exist)
        bat_num_cols = ['runs', 'balls', 'fours', 'sixes']
        existing_bat_cols = [col for col in bat_num_cols if col in df_bat.columns]
        df_bat[existing_bat_cols] = df_bat[existing_bat_cols].apply(pd.to_numeric, errors='coerce')
        
        # Calculate strikeRate dynamically if it wasn't loaded into SQL Server
        if 'strikeRate' not in df_bat.columns:
            if 'runs' in df_bat.columns and 'balls' in df_bat.columns:
                df_bat['strikeRate'] = (df_bat['runs'] / df_bat['balls'] * 100).fillna(0)
            else:
                df_bat['strikeRate'] = 0.0
        else:
            df_bat['strikeRate'] = pd.to_numeric(df_bat['strikeRate'], errors='coerce')
            
        # Safely convert Bowling columns to numeric
        bowl_num_cols = ['overs', 'maidens', 'runs', 'wickets', 'economy']
        existing_bowl_cols = [col for col in bowl_num_cols if col in df_bowl.columns]
        df_bowl[existing_bowl_cols] = df_bowl[existing_bowl_cols].apply(pd.to_numeric, errors='coerce')
        
        return df_bat, df_bowl
    except Exception as e:
        st.error(f"⚠️ Database Connection Failed. Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Helper function to execute CRUD changes safely and refresh data
def execute_crud_query(query_str, params=None):
    try:
        with engine.begin() as conn:
            if params:
                conn.execute(text(query_str), params)
            else:
                conn.execute(text(query_str))
        # Clear the cache so the dashboard immediately reads the fresh data
        load_data.clear() 
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

df_batting, df_bowling = load_data()

# ==========================================
# 🎛️ SIDEBAR FILTERS
# ==========================================
if not df_batting.empty and not df_bowling.empty:
    st.sidebar.header("Filter Parameters")
    
    if 'batteamname' in df_batting.columns:
        teams = ["All Teams"] + df_batting['batteamname'].dropna().unique().tolist()
        selected_team = st.sidebar.selectbox("Select Batting Team", teams)
        
        if selected_team != "All Teams":
            df_batting = df_batting[df_batting['batteamname'] == selected_team]
    else:
        st.sidebar.warning("Team names not found in dataset.")
        
    st.sidebar.markdown("---")
    st.sidebar.info("Dashboard driven by local SQL Server instance: `PRACTICEDB`")

    # ==========================================
    # 📊 DASHBOARD TABS
    # ==========================================
    # Added Tab 5 for CRUD operations
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview KPIs", "Batting Analytics", "Bowling Analytics", "SQL Analytics", "🛠️ Data Management (CRUD)"
    ])

    # --- TAB 1: OVERVIEW KPIs ---
    with tab1:
        st.subheader("Match Executive Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        runs_sum = int(df_batting['runs'].sum()) if 'runs' in df_batting.columns else 0
        wkts_sum = int(df_bowling['wickets'].sum()) if 'wickets' in df_bowling.columns else 0
        
        fours = df_batting['fours'].sum() if 'fours' in df_batting.columns else 0
        sixes = df_batting['sixes'].sum() if 'sixes' in df_batting.columns else 0
        
        col1.metric("Total Runs Scored", runs_sum)
        col2.metric("Total Boundaries (4s/6s)", int(fours + sixes))
        col3.metric("Total Wickets Fallen", wkts_sum)
        
        total_balls = df_batting['balls'].sum() if 'balls' in df_batting.columns else 0
        overall_sr = (runs_sum / total_balls) * 100 if total_balls > 0 else 0
        col4.metric("Avg Match Strike Rate", f"{overall_sr:.2f}")
        
        st.markdown("### Raw Data Feeds (Read Operation)")
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(df_batting, use_container_width=True)
        with c2:
            st.dataframe(df_bowling, use_container_width=True)

    # --- TAB 2: BATTING ANALYTICS ---
    with tab2:
        st.subheader("Batting Performance & Momentum")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if 'runs' in df_batting.columns and 'strikeRate' in df_batting.columns and 'balls' in df_batting.columns:
                fig_scatter = px.scatter(
                    df_batting, x="strikeRate", y="runs", size="balls", color="name",
                    hover_name="name", title="Impact Matrix: Runs vs Strike Rate",
                    labels={"strikeRate": "Strike Rate", "runs": "Runs Scored", "balls": "Balls Faced"}
                )
                fig_scatter.add_vrect(x0=130, x1=max(df_batting['strikeRate'].max(), 150), 
                                      fillcolor="green", opacity=0.1, layer="below", line_width=0)
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.warning("Insufficient data for Impact Matrix.")
            
        with col_b2:
            if 'fours' in df_batting.columns and 'sixes' in df_batting.columns:
                df_boundaries = df_batting[['name', 'fours', 'sixes']].melt(id_vars='name', var_name='Boundary Type', value_name='Count')
                df_boundaries = df_boundaries[df_boundaries['Count'] > 0]
                fig_bar = px.bar(
                    df_boundaries, x="name", y="Count", color="Boundary Type",
                    title="Boundary Distribution per Player",
                    barmode="group", color_discrete_map={"fours": "#1f77b4", "sixes": "#ff7f0e"}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("Boundary data missing.")

    # --- TAB 3: BOWLING ANALYTICS ---
    with tab3:
        st.subheader("Bowling Economy & Impact")
        
        col_bw1, col_bw2 = st.columns(2)
        with col_bw1:
            if 'economy' in df_bowling.columns:
                df_bowling_sorted = df_bowling.sort_values(by='economy', ascending=True)
                fig_eco = px.bar(
                    df_bowling_sorted, x="name", y="economy", text="economy",
                    title="Most Economical Bowlers",
                    labels={"name": "Bowler", "economy": "Economy Rate"},
                    color="economy", color_continuous_scale="Viridis_r"
                )
                fig_eco.update_traces(textposition='outside')
                st.plotly_chart(fig_eco, use_container_width=True)
            else:
                st.warning("Economy data missing.")
            
        with col_bw2:
            if 'runs' in df_bowling.columns and 'wickets' in df_bowling.columns and 'overs' in df_bowling.columns:
                fig_wkts = px.scatter(
                    df_bowling, x="runs", y="wickets", size="overs", color="name",
                    title="Cost of Wickets: Runs Conceded vs Wickets Taken",
                    labels={"runs": "Runs Conceded", "wickets": "Wickets Taken"}
                )
                st.plotly_chart(fig_wkts, use_container_width=True)
            else:
                st.warning("Insufficient data for Wicket Analysis.")

    # --- TAB 4: SQL ANALYTICS ---
    with tab4:
        st.subheader("Insights Derived from SQL Queries")
        
        st.markdown("##### Top Run Scorers (Q3 & Q4)")
        if 'runs' in df_batting.columns:
            top_scorers = df_batting[df_batting['runs'] > 20].sort_values(by='runs', ascending=False)
            if not top_scorers.empty:
                fig_q3 = px.bar(top_scorers, x='name', y='runs', text='runs', color='runs',
                                title="Players scoring > 20 Runs", labels={'name': 'Player', 'runs': 'Runs'})
                st.plotly_chart(fig_q3, use_container_width=True)
            else:
                st.info("No players scored more than 20 runs for this selection.")

        st.markdown("##### All-Rounders Impact (Q9)")
        if 'name' in df_batting.columns and 'name' in df_bowling.columns:
            df_allround = pd.merge(df_batting, df_bowling, on='name', how='inner', suffixes=('_bat', '_bowl'))
            if not df_allround.empty:
                all_rounders = df_allround[(df_allround['runs_bat'] >= 10) & (df_allround['wickets'] >= 1)]
                if not all_rounders.empty:
                    fig_q9 = px.scatter(all_rounders, x='runs_bat', y='wickets', size='runs_bat', color='name',
                                        title="Players with 10+ Runs AND 1+ Wickets",
                                        labels={'runs_bat': 'Runs Scored', 'wickets': 'Wickets Taken'})
                    st.plotly_chart(fig_q9, use_container_width=True)
                else:
                    st.info("No players meet the All-Rounder criteria for this selection.")
            else:
                st.info("No overlapping players found in batting and bowling data for this team.")

        st.markdown("##### Bowling Excellence (Q10 & Q18)")
        col_sql1, col_sql2 = st.columns(2)
        with col_sql1:
            if 'wickets' in df_bowling.columns and 'runs' in df_bowling.columns:
                top_bowlers = df_bowling.sort_values(by=['wickets', 'runs'], ascending=[False, True]).head(5)
                fig_q10 = px.bar(top_bowlers, x='name', y='wickets', color='runs', text='runs',
                                 title="Best Figures (Wickets desc, Runs asc)", 
                                 labels={'name': 'Bowler', 'wickets': 'Wickets Taken', 'runs': 'Runs Conceded'})
                st.plotly_chart(fig_q10, use_container_width=True)
        with col_sql2:
            if 'economy' in df_bowling.columns and 'overs' in df_bowling.columns:
                eco_bowlers = df_bowling[df_bowling['overs'] >= 2].sort_values(by='economy', ascending=True)
                fig_q18 = px.line(eco_bowlers, x='name', y='economy', markers=True, 
                                  title="Most Economical Bowlers (Min 2 Overs)",
                                  labels={'name': 'Bowler', 'economy': 'Economy Rate'})
                st.plotly_chart(fig_q18, use_container_width=True)

        st.markdown("##### Player Form & Calculated Rankings (Q21 & Q23)")
        col_sql3, col_sql4 = st.columns(2)
        with col_sql3:
            if set(['runs', 'fours', 'sixes']).issubset(df_batting.columns):
                df_batting_rank = df_batting.copy()
                df_batting_rank['batting_points'] = (df_batting_rank['runs'] * 0.1) + (df_batting_rank['fours'] * 0.5) + (df_batting_rank['sixes'] * 1.0)
                
                fig_q21 = px.bar(df_batting_rank.sort_values(by='batting_points', ascending=False), 
                                 x='batting_points', y='name', orientation='h', color='batting_points',
                                 title="Custom Batting Points Formula", labels={'name': 'Player', 'batting_points': 'Points'})
                fig_q21.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_q21, use_container_width=True)
        with col_sql4:
            if 'runs' in df_batting.columns:
                conditions = [
                    (df_batting['runs'] >= 50),
                    (df_batting['runs'] >= 20) & (df_batting['runs'] < 50),
                    (df_batting['runs'] < 20)
                ]
                choices = ['Excellent Form', 'Good Form', 'Poor Form']
                df_batting_form = df_batting.copy()
                df_batting_form['Form_Status'] = np.select(conditions, choices, default='Unknown')
                
                form_counts = df_batting_form['Form_Status'].value_counts().reset_index()
                form_counts.columns = ['Form Status', 'Count']
                
                fig_q23 = px.pie(form_counts, names='Form Status', values='Count', hole=0.4,
                                 title="Player Form Distribution", 
                                 color='Form Status',
                                 color_discrete_map={'Excellent Form':'green', 'Good Form':'orange', 'Poor Form':'red'})
                st.plotly_chart(fig_q23, use_container_width=True)

    # --- TAB 5: DATA MANAGEMENT (CRUD) ---
    with tab5:
        st.subheader("🛠️ Database Administrator Tools")
        st.markdown("Modifying records here will execute real-time queries against your `PRACTICEDB` SQL Server and refresh the dashboard instantly.")

        crud_action = st.radio("Select Operation:", ["➕ Create (Insert)", "✏️ Update", "❌ Delete"], horizontal=True)

        if crud_action == "➕ Create (Insert)":
            st.markdown("#### Add New Batting Record")
            with st.form("create_form"):
                c1, c2 = st.columns(2)
                new_name = c1.text_input("Player Name")
                new_team = c2.text_input("Team Name")
                new_runs = c1.number_input("Runs", min_value=0, step=1)
                new_balls = c2.number_input("Balls Faced", min_value=0, step=1)
                new_fours = c1.number_input("Fours", min_value=0, step=1)
                new_sixes = c2.number_input("Sixes", min_value=0, step=1)

                if st.form_submit_button("Insert Record into Database"):
                    if new_name and new_team:
                        insert_query = "INSERT INTO match_batting_stats (name, batteamname, runs, balls, fours, sixes) VALUES (:name, :team, :runs, :balls, :fours, :sixes)"
                        params = {"name": new_name, "team": new_team, "runs": new_runs, "balls": new_balls, "fours": new_fours, "sixes": new_sixes}
                        
                        if execute_crud_query(insert_query, params):
                            st.success(f"✅ Successfully inserted {new_name} into SQL Server.")
                            st.rerun()
                    else:
                        st.error("Player Name and Team Name are required fields.")

        elif crud_action == "✏️ Update":
            st.markdown("#### Update Existing Record")
            if 'name' in df_batting.columns:
                player_to_update = st.selectbox("Select Player to Update", df_batting['name'].sort_values().unique())
                
                if player_to_update:
                    # Fetch current stats to populate the form defaults
                    current_stats = df_batting[df_batting['name'] == player_to_update].iloc[0]
                    
                    with st.form("update_form"):
                        st.info(f"Editing stats for **{player_to_update}**")
                        c1, c2 = st.columns(2)
                        upd_runs = c1.number_input("Runs", value=int(current_stats.get('runs', 0)), min_value=0, step=1)
                        upd_balls = c2.number_input("Balls Faced", value=int(current_stats.get('balls', 0)), min_value=0, step=1)
                        upd_fours = c1.number_input("Fours", value=int(current_stats.get('fours', 0)), min_value=0, step=1)
                        upd_sixes = c2.number_input("Sixes", value=int(current_stats.get('sixes', 0)), min_value=0, step=1)
                        
                        if st.form_submit_button("Commit Update"):
                            update_query = """
                            UPDATE match_batting_stats 
                            SET runs = :runs, balls = :balls, fours = :fours, sixes = :sixes 
                            WHERE name = :name
                            """
                            params = {"runs": upd_runs, "balls": upd_balls, "fours": upd_fours, "sixes": upd_sixes, "name": player_to_update}
                            
                            if execute_crud_query(update_query, params):
                                st.success(f"✅ Successfully updated records for {player_to_update}.")
                                st.rerun()

        elif crud_action == "❌ Delete":
            st.markdown("#### Delete Record")
            if 'name' in df_batting.columns:
                player_to_delete = st.selectbox("Select Player to Remove", df_batting['name'].sort_values().unique())
                
                if player_to_delete:
                    st.warning(f"⚠️ Are you sure you want to permanently delete **{player_to_delete}** from the database? This cannot be undone.")
                    if st.button("Delete Record", type="primary"):
                        delete_query = "DELETE FROM match_batting_stats WHERE name = :name"
                        if execute_crud_query(delete_query, {"name": player_to_delete}):
                            st.success(f"🗑️ Record for {player_to_delete} has been deleted.")
                            st.rerun()

else:
    st.info("Waiting for data. Please ensure your ETL script ran successfully and populated `PRACTICEDB`.")