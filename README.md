# Strava Performance Dashboard 🏃

Personal athlete monitoring system fusing Strava running data 
(800+ activities) with Whoop 5.0 biometrics to model and predict 
running performance.

## Goals
- Track HR efficiency trend over time as a proxy for cardiovascular fitness
- Predict race times (5K, 10K) from training and biometric features
- Build a personalised readiness score and compare it against Whoop's black-box score
- Visualise training load, recovery, and performance on an interactive dashboard

## Data Sources
- **Strava** — 800+ running activities via API (pace, HR, GPS, elevation)
- **Whoop 5.0** — daily biometrics via CSV export (HRV, resting HR, sleep stages, recovery score, strain)
- **Open-Meteo** — free historical weather API (temperature, humidity per run)

## Models
- **XGBoost** — pace and race time predictor from training + biometric features
- **LSTM** — HR efficiency trend smoothing and fitness trajectory forecasting

## Stack
- Data: Pandas, stravalib, Open-Meteo API
- Modelling: scikit-learn, XGBoost, PyTorch
- Dashboard: Streamlit, Plotly, Folium

## Project Structure
strava-performance-dashboard/
├── data/
│   ├── raw/          ← Strava export, Whoop CSVs (gitignored)
│   └── processed/    ← cleaned, merged dataframes (gitignored)
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_modelling.ipynb
├── src/
│   ├── strava_fetch.py
│   ├── whoop_process.py
│   └── features.py
├── dashboard/
│   └── app.py
├── requirements.txt
└── README.md


## Status
🚧 Active development — started June 2026