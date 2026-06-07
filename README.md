# Strava Performance Dashboard 🏃

Personal athlete monitoring system fusing Strava running data 
(500+ activities) with Whoop 5.0 biometrics to model and predict 
running performance.

https://strava-performance-dashboard-tdwmgbmwjgzkhmwb8jmhry.streamlit.app/

## Goals
- Track HR efficiency trend over time as a proxy for cardiovascular fitness
- Predict running pace race times (5K, 10K) from training and biometric features (in development)
- Automatically classify run types from km-by-km split data (in development)
- Visualise training load, recovery, and performance on an interactive dashboard

## Data Sources
- **Strava** — 500+ running activities via API (pace, HR, GPS, elevation)
- **Whoop 5.0** — daily biometrics via CSV export (HRV, resting HR, sleep stages, recovery score, strain)

## Models
- **XGBoost** — pace and race time predictor from training + biometric features
- **LSTM** — HR efficiency trend smoothing and fitness trajectory forecasting
- **Holt-Winters (exponential smoothing)** - HR Efficiency Forecasting
- **Run Type Classifier** 

## Stack
- **Data:** Python, Pandas, stravalib, Whoop API
- **Modelling:** scikit-learn, XGBoost, statsmodels
- **Dashboard:** Streamlit, Plotly, Folium
- **GPS:** gpxpy, Folium HeatMap (330k GPS points across 342 activities)

## Project Structure
```
strava-performance-dashboard/
├── data/
│   ├── raw/          
│   └── processed/    
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
```


## Status
Active development 
