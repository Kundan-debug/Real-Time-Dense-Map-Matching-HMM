from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/Geolife Trajectories 1.3/Data/010")
LABEL_FILE = DATA_DIR / "labels.txt"

# Read taxi-labelled time intervals
labels = pd.read_csv(
    LABEL_FILE,
    sep="\t",
    skip_blank_lines=True
)

labels.columns = ["start_time", "end_time", "mode"]

labels["start_time"] = pd.to_datetime(labels["start_time"])
labels["end_time"] = pd.to_datetime(labels["end_time"])

taxi_labels = labels[labels["mode"].str.strip().str.lower() == "taxi"].copy()

print(f"Taxi intervals found: {len(taxi_labels)}")

results = []

trajectory_files = sorted(
    (DATA_DIR / "Trajectory").glob("*.plt")
)

for file_path in trajectory_files:

    try:
        df = pd.read_csv(
            file_path,
            skiprows=6,
            header=None,
            names=[
                "latitude",
                "longitude",
                "altitude",
                "days",
                "date",
                "time"
            ]
        )

        if df.empty:
            continue

        timestamps = pd.to_datetime(
            df["date"].astype(str) + " " + df["time"].astype(str)
        )

        trajectory_start = timestamps.min()
        trajectory_end = timestamps.max()

        # Check whether this trajectory overlaps any taxi interval
        for _, taxi in taxi_labels.iterrows():

            overlap = (
                trajectory_start <= taxi["end_time"]
                and trajectory_end >= taxi["start_time"]
            )

            if overlap:
                results.append({
                    "file": str(file_path),
                    "points": len(df),
                    "trajectory_start": trajectory_start,
                    "trajectory_end": trajectory_end,
                    "taxi_start": taxi["start_time"],
                    "taxi_end": taxi["end_time"]
                })

    except Exception as e:
        print(f"Could not process {file_path}: {e}")

results_df = pd.DataFrame(results)

if results_df.empty:
    print("\nNo matching taxi trajectories found.")
else:
    results_df = results_df.drop_duplicates(
        subset=["file", "taxi_start", "taxi_end"]
    )

    results_df = results_df.sort_values(
        by="points",
        ascending=False
    )

    print("\nTaxi-labelled trajectory files:")
    print(results_df.to_string(index=False))

    results_df.to_csv(
        "results/taxi_trajectories.csv",
        index=False
    )

    print("\nSaved to:")
    print("results/taxi_trajectories.csv")