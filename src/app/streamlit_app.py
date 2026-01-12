
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.metrics import engine

st.set_page_config(page_title="Project Controls Intelligence", layout="wide")

DB_PATH = "data/processed/pc_intel.db"

# Cloud Deployment Fix: Generate data if DB is missing
if not os.path.exists(DB_PATH):
    st.warning("Database not found. Initializing specific synthetic data for demo...")
    try:
        # Import data generation and ETL modules locally to avoid circular imports if any
        # Adjust paths if necessary, but sys.path is already set
        import sys
        
        # Ensure directories exist
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        
        # Run Data Generation
        from src.data_gen import generate_data
        with st.spinner("Generating synthetic project data..."):
            generate_data.generate_all()
            
        # Run ETL to build DB
        from src.etl import load_all
        with st.spinner("Building analytics database..."):
            load_all.init_db()
            load_all.process_all()
            
        st.success("Initialization complete! Loading dashboard...")
        st.rerun()
        
    except Exception as e:
        st.error(f"Failed to initialize data: {e}")
        st.stop()

# Load CSS
def load_css():
    with open("src/app/assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Load Weekly Metrics
    df_metrics_w = engine.get_project_metrics(conn)
    df_schedule_w = pd.read_sql("SELECT * FROM vw_schedule_weekly", conn)
    
    # Load Monthly Metrics
    df_metrics_m_raw = pd.read_sql("SELECT * FROM vw_ev_monthly", conn)
    df_metrics_m = engine.calculate_kpis(df_metrics_m_raw) # Recalculate KPIs on monthly snapshots
    
    df_schedule_m = pd.read_sql("SELECT * FROM vw_schedule_monthly", conn)
    
    # Load WBS Performance (Monthly) for Treemaps
    df_wbs_m = pd.read_sql("SELECT * FROM vw_wbs_performance_monthly", conn)
    
    # Load Activities for Gantt
    df_activities = pd.read_sql("SELECT * FROM activities", conn)
    
    # Load Changes
    df_changes = pd.read_sql("SELECT * FROM changes", conn)
    
    # Load Projects
    df_projects = pd.read_sql("SELECT * FROM projects", conn)
    
    conn.close()
    
    # Pre-calculate flags
    df_flags = engine.generate_flags(df_metrics_w, df_schedule_w, df_changes)
    
    return {
        "weekly": {"metrics": df_metrics_w, "schedule": df_schedule_w},
        "monthly": {"metrics": df_metrics_m, "schedule": df_schedule_m}
    }, df_changes, df_projects, df_flags, df_activities, df_wbs_m

try:
    data_dict, df_changes, df_projects, df_flags, df_activities, df_wbs_m = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}. Did you run 'make build_db'?")
    st.stop()

# Sidebar
st.sidebar.title("PC Intelligence")
page = st.sidebar.radio("Navigate", ["Overview", "Trends", "Schedule Health", "Changes", "Data Explorer"])

# View Granularity
view_grain = st.sidebar.radio("View Granularity", ["Monthly", "Weekly"], index=0) # Default to Monthly as requested

# Select Data based on Granularity
df_metrics = data_dict[view_grain.lower()]["metrics"]
df_schedule = data_dict[view_grain.lower()]["schedule"]

# Project Selector (Global or per page? let's do global for context if filtering)
# Actually, Overview should show all or a summary.
# Let's add a project filter in sidebar used by Trends/Schedule/Changes.
project_options = df_projects['project_id'].unique()
selected_project = st.sidebar.selectbox("Select Project", project_options)

st.title("Project Controls Intelligence")

# --- Overview ---
if page == "Overview":
    st.header("Portfolio Overview")
    
    # Latest Status for all projects
    latest_dates = df_metrics.groupby('project_id')['week_ending'].max()
    
    cols = st.columns(len(project_options))
    
    for i, pid in enumerate(project_options):
        # Get latest data
        last_date = latest_dates[pid]
        row = df_metrics[(df_metrics['project_id'] == pid) & (df_metrics['week_ending'] == last_date)].iloc[0]
        
        with cols[i]:
            st.subheader(f"{pid}")
            st.caption(df_projects[df_projects['project_id'] == pid]['name'].iloc[0])
            
            col1, col2 = st.columns(2)
            col1.metric("CPI", f"{row['cpi']:.2f}", delta=f"{row['cpi']-1:.2f}")
            col2.metric("SPI", f"{row['spi']:.2f}", delta=f"{row['spi']-1:.2f}")
            
            st.metric("EAC", f"${row['eac']:,.0f}")
            st.metric("VAC", f"${row['vac']:,.0f}", delta_color="normal")
            
            # Show active flags
            p_flags = df_flags[(df_flags['project_id'] == pid) & (df_flags['week_ending'] == last_date)]
            if not p_flags.empty:
                st.warning(f"{len(p_flags)} Active Flags")
                for _, f in p_flags.iterrows():
                    st.write(f"- {f['flag_type']}")
            else:
                st.success("No Active Flags")

# --- Trends ---
elif page == "Trends":
    st.header(f"Trends Analysis: {selected_project}")
    
    proj_metrics = df_metrics[df_metrics['project_id'] == selected_project]
    
    # CPI/SPI Chart
    fig_kpi = px.line(proj_metrics, x='week_ending', y=['cpi', 'spi'], title="CPI & SPI Trends")
    fig_kpi.add_hline(y=1.0, line_dash="dash", line_color="gray")
    fig_kpi.add_hline(y=0.9, line_dash="dot", line_color="red")
    st.plotly_chart(fig_kpi, use_container_width=True)
    
    # EV/PV/AC Chart
    fig_ev = px.line(proj_metrics, x='week_ending', y=['ev', 'pv', 'ac'], title="EVM Metrics (Cumulative)")
    st.plotly_chart(fig_ev, use_container_width=True)
    
    # --- Cost Performance Analysis (Treemap) ---
    st.subheader("Cost Performance by WBS (Variance Analysis)")
    
    # Get latest monthly data for this project
    proj_wbs = df_wbs_m[df_wbs_m['project_id'] == selected_project]
    
    # We need the LAST available month
    if not proj_wbs.empty:
        last_period = proj_wbs['week_ending'].max()
        current_wbs_data = proj_wbs[proj_wbs['week_ending'] == last_period].copy()
        
        # Color by CPI (Efficient vs Inefficient)
        # Avoid div by zero
        current_wbs_data['cpi'] = current_wbs_data.apply(lambda x: x['ev'] / x['ac'] if x['ac'] > 0 else 1.0, axis=1)
        
        fig_tree = px.treemap(
            current_wbs_data, 
            path=['project_id', 'wbs_id'], 
            values='bac', # Size by Budget
            color='cpi',
            color_continuous_scale='RdYlGn',
            range_color=[0.8, 1.2],
            # midpoint=1.0, # Removed invalid argument
            title=f"WBS Budget Distribution & Performance (CPI) - {last_period}"
        )
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.info("No WBS data available.")
        
    
    # Flags Table
    st.subheader("Health Flags History")
    proj_flags = df_flags[df_flags['project_id'] == selected_project]
    st.dataframe(proj_flags)

# --- Schedule Health ---
elif page == "Schedule Health":
    st.header(f"Schedule Health: {selected_project}")
    
    proj_sched = df_schedule[df_schedule['project_id'] == selected_project]
    
    c1, c2 = st.columns(2)
    with c1:
        fig_float = px.line(proj_sched, x='week_ending', y='avg_float', title="Average Total Float (Days)")
        st.plotly_chart(fig_float, use_container_width=True)
        
    with c2:
        fig_crit = px.line(proj_sched, x='week_ending', y='critical_count', title="Critical Activities Count")
        st.plotly_chart(fig_crit, use_container_width=True)
        
    # Percent Complete
    fig_pct = px.line(proj_sched, x='week_ending', y=['planned_pct_total', 'actual_pct_total'], title="Schedule Progress %")
    st.plotly_chart(fig_pct, use_container_width=True)
    
    # --- Gantt Chart ---
    st.subheader("Project Schedule (Gantt)")
    
    proj_acts = df_activities[df_activities['project_id'] == selected_project].copy()
    
    if not proj_acts.empty:
        # Sort by start date
        proj_acts = proj_acts.sort_values(by='start')
        
        # Create Gantt
        fig_gantt = px.timeline(
            proj_acts, 
            x_start="start", 
            x_end="finish", 
            y="name", 
            color="is_critical",
            color_discrete_map={True: "red", False: "blue"},
            hover_data=["activity_id", "total_float", "original_duration"],
            title="Activity Schedule"
        )
        # Ensure y-axis is sorted properly (top to bottom)
        fig_gantt.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_gantt, use_container_width=True)
    else:
        st.info("No activities found for this project.")

# --- Changes ---
elif page == "Changes":
    st.header(f"Change Management: {selected_project}")
    
    proj_changes = df_changes[df_changes['project_id'] == selected_project]
    
    if proj_changes.empty:
        st.info("No changes recorded for this project.")
    else:
        # Metrics
        total_delta_bac = proj_changes['delta_bac'].sum()
        total_delta_days = proj_changes['delta_finish_days'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Cumulative Budget Impact", f"${total_delta_bac:,.2f}")
        c2.metric("Cumulative Schedule Impact", f"{total_delta_days} Days")
        
        st.subheader("Change Log")
        st.dataframe(proj_changes)

# --- Data Explorer ---
elif page == "Data Explorer":
    st.header("Data Explorer")
    
    table_options = {
        "Projects": df_projects,
        "Metrics (Weekly)": data_dict["weekly"]["metrics"],
        "Metrics (Monthly)": data_dict["monthly"]["metrics"],
        "Schedule (Weekly)": data_dict["weekly"]["schedule"],
        "Schedule (Monthly)": data_dict["monthly"]["schedule"],
        "Changes": df_changes,
        "Flags": df_flags
    }
    
    selected_table = st.selectbox("Select Dataset", list(table_options.keys()))
    
    st.subheader(f"{selected_table}")
    
    # Filter by selected project context? 
    # Usually explorer implies raw access, but let's offer a filter toggle
    df_show = table_options[selected_table]
    
    # Some tables might not have project_id (though all ours do so far)
    if 'project_id' in df_show.columns:
        filter_proj = st.checkbox(f"Filter by Selected Project ({selected_project})", value=True)
        if filter_proj:
            df_show = df_show[df_show['project_id'] == selected_project]
            
    st.dataframe(df_show, use_container_width=True)
