from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/Geolife Trajectories 1.3/Data/010")
LABEL_FILE = DATA_DIR / "labels.txt"
OUTPUT_FILE = Path("data/taxi_gps.csv")


# Read transportation labels
labels = pd.read_csv(
    LABEL_FILE,
    sep="\t",
    skip_blank_lines=True
)

labels.columns = ["start_time", "end_time", "mode"]

labels["start_time"] = pd.to_datetime(labels["start_time"])
labels["end_time"] = pd.to_datetime(labels["end_time"])

taxi_labels = labels[
    labels["mode"].str.strip().str.lower() == "taxi"
].copy()

print(f"Taxi intervals found: {len(taxi_labels)}")


# Read trajectory files
trajectory_files = sorted(
    (DATA_DIR / "Trajectory").glob("*.plt")
)

all_taxi_points = []

for file_path in trajectory_files:

    try:
        rows = []

        with open(file_path, "r", encoding="utf-8") as f:

            for line in f:

                parts = line.strip().split(",")

                # Valid GeoLife GPS record has 7 fields:
                # latitude, longitude, altitude, days, date, time
                # Some files may contain extra fields, so require at least 6.
                if len(parts) < 6:
                    continue

                try:
                    latitude = float(parts[0])
                    longitude = float(parts[1])
                    altitude = float(parts[2])
                    days = float(parts[3])
                    date = parts[5]
                    time = parts[6] if len(parts) > 6 else parts[5]

                    # In the standard GeoLife format:
                    # parts[0] = latitude
                    # parts[1] = longitude
                    # parts[2] = altitude
                    # parts[3] = days
                    # parts[5] = date
                    # parts[6] = time

                    timestamp = pd.to_datetime(
                        f"{date} {time}"
                    )

                    rows.append({
                        "latitude": latitude,
                        "longitude": longitude,
                        "altitude": altitude,
                        "timestamp": timestamp
                    })

                except (ValueError, TypeError):
                    continue

        if not rows:
            continue

        df = pd.DataFrame(rows)

        # Check every taxi interval
        for _, taxi in taxi_labels.iterrows():

            mask = (
                (df["timestamp"] >= taxi["start_time"])
                & (df["timestamp"] <= taxi["end_time"])
            )

            taxi_points = df.loc[mask].copy()

            if len(taxi_points) > 0:

                taxi_points["trip_id"] = (
                    taxi["start_time"].strftime("%Y%m%d_%H%M%S")
                )

                taxi_points["mode"] = "taxi"

                all_taxi_points.append(taxi_points)

    except Exception as e:
        print(f"Could not process {file_path}: {e}")


# Combine all taxi points
if not all_taxi_points:

    print("No taxi GPS points found.")

else:

    taxi_data = pd.concat(
        all_taxi_points,
        ignore_index=True
    )

    # Keep useful columns
    taxi_data = taxi_data[
        [
            "trip_id",
            "timestamp",
            "latitude",
            "longitude",
            "altitude",
            "mode"
        ]
    ]

    # Sort
    taxi_data = taxi_data.sort_values(
        ["trip_id", "timestamp"]
    )

    # Remove duplicate timestamps within each trip
    taxi_data = taxi_data.drop_duplicates(
        subset=["trip_id", "timestamp"]
    )

    # Save
    taxi_data.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nTaxi dataset created successfully.")
    print(f"Total taxi GPS points: {len(taxi_data)}")
    print(
        f"Number of taxi trips: "
        f"{taxi_data['trip_id'].nunique()}"
    )

    print("\nFirst 10 GPS points:")
    print(
        taxi_data.head(10).to_string(index=False)
    )

    print("\nPoints per taxi trip:")
    print(
        taxi_data.groupby("trip_id")
        .size()
        .sort_values(ascending=False)
        .head(20)
    )

    print(f"\nSaved to: {OUTPUT_FILE}")
