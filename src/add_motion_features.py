from pathlib import Path

import numpy as np
import pandas as pd

INPUT_FILE = Path("data/taxi_gps.csv")
OUTPUT_FILE = Path("data/taxi_gps_features.csv")

EARTH_RADIUS_M = 6_371_000

def haversine_distance(lat1, lon1, lat2, lon2):
    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    dlat = lat2 - lat1
    dlon = np.radians(lon2) - np.radians(lon1)

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )

    return 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(a))

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    dlon = np.radians(lon2 - lon1)

    x = np.sin(dlon) * np.cos(lat2)

    y = (
        np.cos(lat1) * np.sin(lat2)
        - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    )

    bearing = np.degrees(np.arctan2(x, y))

    return (bearing + 360) % 360

df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(df["timestamp"])

df = df.sort_values(
    ["trip_id", "timestamp"]
).copy()

# Remove duplicate timestamps within each trip
df = df.drop_duplicates(
    subset=["trip_id", "timestamp"]
).copy()

# Previous GPS point in the same trip
df["prev_latitude"] = df.groupby("trip_id")["latitude"].shift(1)
df["prev_longitude"] = df.groupby("trip_id")["longitude"].shift(1)
df["prev_timestamp"] = df.groupby("trip_id")["timestamp"].shift(1)

# Time difference
df["time_diff_s"] = (
    df["timestamp"] - df["prev_timestamp"]
).dt.total_seconds()

# Distance between consecutive GPS points
df["distance_m"] = haversine_distance(
    df["prev_latitude"],
    df["prev_longitude"],
    df["latitude"],
    df["longitude"]
)

# Speed in m/s
df["speed_mps"] = (
    df["distance_m"] / df["time_diff_s"]
)

# Heading / bearing in degrees
df["heading_deg"] = calculate_bearing(
    df["prev_latitude"],
    df["prev_longitude"],
    df["latitude"],
    df["longitude"]
)

# First point of each trip has no previous point
first_points = df["prev_timestamp"].isna()

df.loc[first_points, "distance_m"] = 0
df.loc[first_points, "time_diff_s"] = 0
df.loc[first_points, "speed_mps"] = 0
df.loc[first_points, "heading_deg"] = np.nan

# Do not treat long GPS gaps as normal motion intervals.
# A gap greater than 10 seconds is marked invalid for speed/heading.
long_gap = df["time_diff_s"] > 10

df.loc[long_gap, "distance_m"] = np.nan
df.loc[long_gap, "speed_mps"] = np.nan
df.loc[long_gap, "heading_deg"] = np.nan

# Remove helper columns
df = df.drop(
    columns=[
        "prev_latitude",
        "prev_longitude",
        "prev_timestamp"
    ]
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Motion features created successfully.")
print(f"Total GPS points: {len(df)}")
print(f"Output: {OUTPUT_FILE}")

print("\nSpeed statistics (m/s):")
print(df["speed_mps"].describe())

print("\nSpeed statistics (km/h):")
print((df["speed_mps"] * 3.6).describe())

print("\nTime-gap statistics (seconds):")
print(df["time_diff_s"].describe())

print("\nHeading statistics (degrees):")
print(df["heading_deg"].describe())

print("\nLong gaps (>10 seconds):")
print(long_gap.sum())
