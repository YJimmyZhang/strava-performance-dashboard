import os
import requests
import pandas as pd
from dotenv import load_dotenv
import secrets as python_secrets

load_dotenv()

WHOOP_CLIENT_ID = os.getenv("WHOOP_CLIENT_ID")
WHOOP_CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET")
WHOOP_REDIRECT_URI = "http://localhost:8000/whoop/callback/"

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
BASE_URL = "https://api.prod.whoop.com/developer/v2"

SCOPES = "read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement"

def get_auth_url():
    params = {
        "client_id": WHOOP_CLIENT_ID,
        "redirect_uri": WHOOP_REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": python_secrets.token_urlsafe(16),
    }
    req = requests.Request("GET", AUTH_URL, params=params).prepare()
    return req.url

def get_access_token(code):
    response = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": WHOOP_REDIRECT_URI,
        "client_id": WHOOP_CLIENT_ID,
        "client_secret": WHOOP_CLIENT_SECRET,
    })
    return response.json()

def get_headers():
    return {"Authorization": f"Bearer {os.getenv('WHOOP_ACCESS_TOKEN')}"}

def fetch_all_pages(endpoint):
    """Fetch all pages from a paginated Whoop endpoint"""
    results = []
    url = f"{BASE_URL}/{endpoint}?limit=25"
    
    while url:
        response = requests.get(url, headers=get_headers())
        data = response.json()
        results.extend(data.get("records", []))
        next_token = data.get("next_token")
        if next_token:
            url = f"{BASE_URL}/{endpoint}?limit=25&nextToken={next_token}"
        else:
            url = None
    
    return results

def fetch_recovery():
    records = fetch_all_pages("cycle")  # recovery is inside cycle in v2
    rows = []
    for r in records:
        recovery = r.get("recovery", {})
        score = recovery.get("score", {}) if recovery else {}
        rows.append({
            "date": r.get("start")[:10] if r.get("start") else None,
            "recovery_score": score.get("recovery_score"),
            "hrv_rmssd": score.get("hrv_rmssd_milli"),
            "resting_hr": score.get("resting_heart_rate"),
            "skin_temp_celsius": score.get("skin_temp_celsius"),
            "spo2_pct": score.get("spo2_percentage"),
            "strain": r.get("score", {}).get("strain"),
            "avg_hr": r.get("score", {}).get("average_heart_rate"),
        })
    return pd.DataFrame(rows)

def fetch_sleep():
    records = fetch_all_pages("activity/sleep")
    rows = []
    for r in records:
        score = r.get("score", {}) or {}
        stage_summary = score.get("stage_summary", {}) or {}
        rows.append({
            "date": r.get("created_at", "")[:10],
            "sleep_performance_pct": score.get("sleep_performance_percentage"),
            "sleep_duration_min": score.get("total_in_bed_time_milli", 0) / 60000,
            "deep_sleep_min": stage_summary.get("total_slow_wave_sleep_time_milli", 0) / 60000,
            "rem_sleep_min": stage_summary.get("total_rem_sleep_time_milli", 0) / 60000,
            "light_sleep_min": stage_summary.get("total_light_sleep_time_milli", 0) / 60000,
        })
    return pd.DataFrame(rows)

def fetch_cycles():
    records = fetch_all_pages("cycle")
    rows = []
    for r in records:
        score = r.get("score", {}) or {}
        rows.append({
            "date": r.get("start", "")[:10],
            "strain": score.get("strain"),
            "avg_hr": score.get("average_heart_rate"),
            "max_hr": score.get("max_heart_rate"),
            "kilojoules": score.get("kilojoules"),
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    print("Fetching Whoop data...")
    
    recovery = fetch_recovery()
    print(f"Recovery records: {len(recovery)}")
    recovery.to_csv("data/raw/whoop_recovery.csv", index=False)
    
    sleep = fetch_sleep()
    print(f"Sleep records: {len(sleep)}")
    sleep.to_csv("data/raw/whoop_sleep.csv", index=False)
    
    cycles = fetch_cycles()
    print(f"Cycle records: {len(cycles)}")
    cycles.to_csv("data/raw/whoop_cycles.csv", index=False)
    
    print("Done! Whoop data saved.")