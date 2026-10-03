from pathlib import Path
import pandas as pd

# Path to the GeoLife trajectory folders
DATA_DIR = Path("data/Geolife Trajectories 1.3/Data")

records = []

# Find every .plt trajectory file
trajectory_files = list(DATA_DIR.glob("*/Trajectory/*.plt"))

print(f"Total trajectory files found: {len(trajectory_files)}")

for file_path in trajectory_files:
    try:
        # Skip the 6-line header
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

        records.append({
            "file": str(file_path),
            "points": len(df),
            "start_date": df["date"].iloc[0] if len(df) > 0 else None,
            "end_date": df["date"].iloc[-1] if len(df) > 0 else None
        })

    except Exception as e:
        print(f"Could not read {file_path}: {e}")

# Convert results to a DataFrame
summary = pd.DataFrame(records)

# Sort by number of GPS observations
summary = summary.sort_values(
    by="points",
    ascending=False
)

# Display the 20 longest trajectories
print("\nTop 20 trajectories by number of GPS points:")
print(summary.head(20).to_string(index=False))

# Save the complete inspection results
summary.to_csv(
    "results/trajectory_summary.csv",
    index=False
)

print("\nSaved summary to:")
print("results/trajectory_summary.csv")