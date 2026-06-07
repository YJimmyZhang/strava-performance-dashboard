import os
import time
import json
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

def fetch_streams_and_splits():
    client = get_client()

    # Load activity IDs from cleaned CSV
    df = pd.read_csv("data/processed/activities_clean.csv")
    activity_ids = df["id"].tolist()
    total = len(activity_ids)

    gps_data = []
    splits_data = []

    for i, activity_id in enumerate(activity_ids):
        print(f"Fetching {i+1}/{total} — activity {activity_id}")

        try:
            # --- GPS streams ---
            streams = client.get_activity_streams(
                activity_id,
                types=["latlng", "altitude", "velocity_smooth", "heartrate"],
                resolution="medium"  # medium = ~300 points per activity
            )

            if "latlng" in streams:
                latlng = streams["latlng"].data
                altitude = streams["altitude"].data if "altitude" in streams else [None] * len(latlng)
                velocity = streams["velocity_smooth"].data if "velocity_smooth" in streams else [None] * len(latlng)
                hr = streams["heartrate"].data if "heartrate" in streams else [None] * len(latlng)

                for j, (lat, lng) in enumerate(latlng):
                    gps_data.append({
                        "activity_id": activity_id,
                        "lat": lat,
                        "lng": lng,
                        "altitude": altitude[j] if j < len(altitude) else None,
                        "velocity": velocity[j] if j < len(velocity) else None,
                        "hr": hr[j] if j < len(hr) else None,
                    })

            # --- Splits ---
            activity = client.get_activity(activity_id)
            if activity.splits_metric:
                for split in activity.splits_metric:
                    splits_data.append({
                        "activity_id": activity_id,
                        "split": split.split,
                        "distance_m": float(split.distance),
                        "elapsed_time_sec": int(split.elapsed_time),
                        "moving_time_sec": int(split.moving_time),
                        "elevation_difference": float(split.elevation_difference),
                        "avg_hr": split.average_heartrate,
                        "avg_speed": float(split.average_speed),
                        "pace_min_per_km": (int(split.moving_time) / 60) / (float(split.distance) / 1000) if float(split.distance) > 0 else None
                    })

        except Exception as e:
            print(f"  ⚠️ Error on activity {activity_id}: {e}")
            continue

        # Strava rate limit — 100 requests per 15 min
        # Each activity = 2 requests (streams + detail)
        # So 50 activities per 15 min = 1 every 18 seconds
        time.sleep(18)

        # Save checkpoint every 50 activities
        if (i + 1) % 50 == 0:
            pd.DataFrame(gps_data).to_csv("data/raw/gps_streams.csv", index=False)
            pd.DataFrame(splits_data).to_csv("data/raw/splits.csv", index=False)
            print(f"  ✅ Checkpoint saved at {i+1} activities")

    # Final save
    pd.DataFrame(gps_data).to_csv("data/raw/gps_streams.csv", index=False)
    pd.DataFrame(splits_data).to_csv("data/raw/splits.csv", index=False)
    print(f"Done! GPS points: {len(gps_data)}, Split rows: {len(splits_data)}")

if __name__ == "__main__":
    fetch_streams_and_splits()