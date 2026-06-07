import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import os

# --- Page config ---
st.set_page_config(
    page_title="Running Performance Dashboard",
    page_icon="🏃",
    layout="wide"
)

# --- Load data ---
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/activities_final.csv", parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_localize(None)
    df = df.sort_values("date").reset_index(drop=True)
    return df

@st.cache_data
def load_gps():
    return pd.read_csv("data/raw/gps_streams.csv").dropna(subset=["lat", "lng"])

@st.cache_data
def load_whoop():
    recovery = pd.read_csv("data/raw/whoop_recovery.csv", parse_dates=["date"])
    sleep = pd.read_csv("data/raw/whoop_sleep.csv", parse_dates=["date"])
    return recovery, sleep

df = load_data()
gps = load_gps()
recovery, sleep = load_whoop()

# --- Sidebar ---
st.sidebar.title("🏃 Running Dashboard")
st.sidebar.markdown("Personal athlete monitoring system")
st.sidebar.markdown("---")

page = st.sidebar.selectbox("Navigate", [
    "Overview",
    "Training Load",
    "HR Efficiency",
    "Heatmap",
    "Readiness",
    "Models"
])

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Total runs:** {len(df)}")
st.sidebar.markdown(f"**Date range:** {df['date'].min().date()} → {df['date'].max().date()}")
st.sidebar.markdown(f"**Total km:** {df['distance_km'].sum():.0f} km")

# --- Overview Page ---
if page == "Overview":
    st.title("🏃 Running Performance Dashboard")
    st.markdown("Personal athlete monitoring system — Strava + Whoop 5.0")
    
   

    # Add to Overview page after the metrics
    st.subheader("🏆 Personal Bests")
    col1, col2, col3, col4 = st.columns(4)

    def pace_to_time(pace_min_per_km, distance_km):
        total_minutes = pace_min_per_km * distance_km
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        seconds = int((total_minutes * 60) % 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    best_5k = df[df["distance_km"].between(4.9, 5.1)]["pace_min_per_km"].min()
    best_10k = df[df["distance_km"].between(9.9, 10.1)]["pace_min_per_km"].min()
    best_hm = df[df["distance_km"].between(20, 22)]["pace_min_per_km"].min()
    best_marathon = df[df["distance_km"].between(41, 43)]["pace_min_per_km"].min()

    col1.metric("5K", pace_to_time(best_5k, 5.0))
    col2.metric("10K", pace_to_time(best_10k, 10.0))
    col3.metric("Half Marathon", pace_to_time(best_hm, 21.0975))
    col4.metric("Marathon", pace_to_time(best_marathon, 42.195))

     # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Runs", len(df))
    col2.metric("Total Distance", f"{df['distance_km'].sum():.0f} km")
    col3.metric("Avg Pace", f"{df['pace_min_per_km'].mean():.2f} min/km")
    col4.metric("Avg HR", f"{df['avg_hr'].mean():.0f} bpm")


    # Weekly mileage
    df["week"] = df["date"].dt.to_period("W").dt.start_time
    weekly = df.groupby("week")["distance_km"].sum().reset_index()
    fig = px.bar(weekly, x="week", y="distance_km",
                 title="Weekly Mileage",
                 labels={"distance_km": "km", "week": "Week"})
    st.plotly_chart(fig, use_container_width=True)

    # Pace over time
    df_clean = df[df["pace_min_per_km"] <= 8]
    fig2 = px.scatter(df_clean, x="date", y="pace_min_per_km",
                      trendline="lowess",
                      title="Pace Over Time",
                      labels={"pace_min_per_km": "Pace (min/km)", "date": "Date"})
    fig2.update_yaxes(autorange="reversed")
    st.plotly_chart(fig2, use_container_width=True)

# --- Training Load Page ---
elif page == "Training Load":
    st.title("📈 Training Load")

    df_daily = df.set_index("date")[["distance_km"]].resample("D").sum().fillna(0)
    df_daily["rolling_7d"] = df_daily["distance_km"].rolling(7).sum()
    df_daily["rolling_28d"] = df_daily["distance_km"].rolling(28).sum()
    df_daily["acwr"] = np.where(
        df_daily["rolling_28d"] > 5,
        df_daily["rolling_7d"] / df_daily["rolling_28d"],
        np.nan
    )
    df_daily["acwr_smooth"] = df_daily["acwr"].rolling(7).mean()
    df_plot = df_daily[df_daily.index >= "2023-06-01"]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_daily.index, y=df_daily["distance_km"], 
                         name="Daily km", opacity=0.4))
    fig.add_trace(go.Scatter(x=df_daily.index, y=df_daily["rolling_7d"],
                             name="7-day load", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df_daily.index, y=df_daily["rolling_28d"],
                             name="28-day load", line=dict(color="orange")))
    fig.update_layout(title="Training Load Over Time")
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.line(df_plot, x=df_plot.index, y="acwr_smooth",
                   title="Acute:Chronic Workload Ratio",
                   labels={"acwr_smooth": "ACWR"})
    fig2.add_hline(y=1.5, line_dash="dash", line_color="red",
                   annotation_text="Injury risk")
    fig2.add_hline(y=0.8, line_dash="dash", line_color="orange",
                   annotation_text="Undertraining")
    st.plotly_chart(fig2, use_container_width=True)

# --- HR Efficiency Page ---
elif page == "HR Efficiency":
    st.title("❤️ HR Efficiency")
    st.markdown("Speed per heartbeat — a proxy for cardiovascular fitness")

    df_easy = df[(df["avg_hr"].notna()) & (df["avg_hr"] < 155)].copy()
    df_easy["speed_m_per_min"] = (df_easy["distance_km"] * 1000) / (df_easy["duration_sec"] / 60)
    df_easy["hr_efficiency"] = df_easy["speed_m_per_min"] / df_easy["avg_hr"]
    df_easy = df_easy[df_easy["hr_efficiency"] < 1.5].copy()

    df_easy["week"] = df_easy["date"].dt.to_period("W").dt.start_time
    weekly = df_easy.groupby("week")["hr_efficiency"].mean().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_easy["date"], y=df_easy["hr_efficiency"],
                             mode="markers", opacity=0.3, name="Individual runs"))
    fig.add_trace(go.Scatter(x=weekly["week"], y=weekly["hr_efficiency"],
                             name="Weekly avg", line=dict(color="blue", width=2)))
    fig.update_layout(title="HR Efficiency Over Time (easy runs)")
    st.plotly_chart(fig, use_container_width=True)

    # Forecast
    # Forecast — test vs actual version
    st.subheader("16-Week Backtest")
    weekly = weekly[weekly["hr_efficiency"] < 1.5].reset_index(drop=True)

    train = weekly["hr_efficiency"][:-16]
    test = weekly["hr_efficiency"][-16:]
    test_weeks = weekly["week"][-16:]

    model_hw = ExponentialSmoothing(
        train,
        trend="add",
        seasonal=None,
        initialization_method="estimated"
    ).fit()

    forecast = model_hw.forecast(16)
    mae = np.mean(np.abs(forecast.values - test.values))

    st.metric("MAE", f"{mae:.4f} m/min/bpm")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=weekly["week"].astype(str),
        y=weekly["hr_efficiency"],
        name="Actual"))
    fig2.add_trace(go.Scatter(
        x=test_weeks.astype(str),
        y=forecast.values,
        name="Forecast",
        line=dict(color="red", dash="dash")))
    fig2.update_layout(title="HR Efficiency ")
    st.plotly_chart(fig2, use_container_width=True)

# --- Heatmap Page ---
elif page == "Heatmap":
    st.title("🗺️ Where I Run")
    
    centre_lat = gps["lat"].median()
    centre_lng = gps["lng"].median()

    m = folium.Map(location=[centre_lat, centre_lng],
                   zoom_start=13, tiles="CartoDB dark_matter")
    HeatMap(gps[["lat", "lng"]].values.tolist(),
            radius=8, blur=10, min_opacity=0.3).add_to(m)
    folium_static(m, width=1200, height=600)

# --- Readiness Page ---
elif page == "Readiness":
    st.title("⚡ Readiness & Recovery")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(recovery, x="date", y="recovery_score",
                      title="Daily Recovery Score (Whoop)",
                      labels={"recovery_score": "Recovery %"})
        fig.add_hline(y=67, line_dash="dash", line_color="green")
        fig.add_hline(y=33, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.line(recovery, x="date", y="hrv_rmssd",
                       title="HRV Over Time",
                       labels={"hrv_rmssd": "HRV rMSSD (ms)"})
        st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.line(sleep, x="date", y="sleep_performance_pct",
                   title="Sleep Performance %")
    st.plotly_chart(fig3, use_container_width=True)

# --- Models Page ---
elif page == "Models":
    st.title("🤖 Models")

    st.subheader("Model 1 — XGBoost Pace Predictor")
    st.markdown("""
    - **R² = 0.47** on easy runs
    - **MAE = 21 sec/km**
    - Heart rate is the dominant predictor, followed by chronic training load and elevation
    """)

    st.subheader("Model 3 — HR Efficiency Forecasting")
    st.markdown("""
    - **Holt-Winters exponential smoothing** with additive trend
    - **MAE = 0.089 m/min/bpm**
    - Captures long-term fitness trend but underestimates post-race recovery dips
    """)

    st.subheader("Model 5 — Readiness Score")
    st.markdown("""
    - **XGBoost vs Whoop black-box comparison**
    - Training load outweighs all biometric signals combined
    - Whoop's recovery score ranks last in feature importance
    """)