import os
import pandas as pd
from dotenv import load_dotenv
from stravalib.client import Client

load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
TOKEN_EXPIRES_AT = int(os.getenv("STRAVA_TOKEN_EXPIRES_AT"))

def get_client():
    client = Client(
        access_token=ACCESS_TOKEN,
        refresh_token=REFRESH_TOKEN,
        token_expires=TOKEN_EXPIRES_AT
    )
    client.refresh_access_token(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        refresh_token=REFRESH_TOKEN
    )
    return client

def fetch_activities():
    client = get_client()
    activities = client.get_activities()

    data = []
    for activity in activities:
        if activity.type.root == "Run":
            data.append({
                "id": activity.id,
                "date": activity.start_date_local,
                "name": activity.name,
                "distance_km": float(activity.distance) / 1000,
                "duration_sec": int(activity.moving_time),
                "elevation_m": float(activity.total_elevation_gain),
                "avg_hr": activity.average_heartrate,
                "max_hr": activity.max_heartrate,
                "avg_speed": float(activity.average_speed),
            })

    print(f"Total activities collected: {len(data)}")  # debug
    
    if not data:
        print("No runs found — check filter")
        return None

    df = pd.DataFrame(data)
    df["pace_min_per_km"] = (df["duration_sec"] / 60) / df["distance_km"]
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df

if __name__ == "__main__":
    print("Fetching activities...")
    df = fetch_activities()
    print(f"Fetched {len(df)} runs")
    print(df.head())
    df.to_csv("data/raw/activities.csv", index=False)
    print("Saved to data/raw/activities.csv")