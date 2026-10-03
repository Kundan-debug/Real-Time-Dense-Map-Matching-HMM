from pathlib import Path

import numpy as np
import osmnx as ox
import pandas as pd
from pyproj import Transformer

CANDIDATE_FILE = Path("data/candidates.csv")
GRAPH_FILE = Path("data/road_network.graphml")
OUTPUT_FILE = Path("data/emissions.csv")

# Parameters
DISTANCE_SIGMA = 20.0
HEADING_SIGMA = 45.0

def angle_difference(a, b):
    """
    Smallest absolute difference between two angles.
    Result is between 0 and 180 degrees.
    """
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)

def bearing_from_points(x1, y1, x2, y2):
    """
    Bearing of a road edge in projected coordinates.
    """
    angle = np.degrees(
        np.arctan2(
            x2 - x1,
            y2 - y1
        )
    )

    return (angle + 360) % 360

# Load candidates
candidates = pd.read_csv(CANDIDATE_FILE)

candidates["timestamp"] = pd.to_datetime(
    candidates["timestamp"]
)

# Load road graph
G = ox.load_graphml(GRAPH_FILE)

# Project graph to metric coordinates
G_projected = ox.project_graph(G)

nodes, edges = ox.graph_to_gdfs(
    G_projected,
    nodes=True,
    edges=True
)

# Convert GPS coordinates to graph CRS
transformer = Transformer.from_crs(
    "EPSG:4326",
    edges.crs,
    always_xy=True
)

road_headings = {}

# Calculate heading for every directed road edge
for (u, v, key), edge in edges.iterrows():

    try:
        x1 = nodes.loc[u].geometry.x
        y1 = nodes.loc[u].geometry.y

        x2 = nodes.loc[v].geometry.x
        y2 = nodes.loc[v].geometry.y

        heading = bearing_from_points(
            x1, y1, x2, y2
        )

        road_headings[(u, v, key)] = heading

    except Exception:
        road_headings[(u, v, key)] = np.nan

# Calculate emission features
results = []

for _, row in candidates.iterrows():

    edge_id = (
        row["edge_u"],
        row["edge_v"],
        row["edge_key"]
    )

    road_heading = road_headings.get(
        edge_id,
        np.nan
    )

    gps_heading = row.get(
        "heading_deg",
        np.nan
    )

    distance = row["distance_m"]

    # Distance component
    distance_score = np.exp(
        -(distance ** 2)
        / (2 * DISTANCE_SIGMA ** 2)
    )

    # Direction component
    if pd.isna(gps_heading) or pd.isna(road_heading):
        heading_difference = np.nan
        heading_score = 1.0
    else:
        heading_difference = angle_difference(
            gps_heading,
            road_heading
        )

        heading_score = np.exp(
            -(heading_difference ** 2)
            / (2 * HEADING_SIGMA ** 2)
        )

    # Combined emission score
    emission_score = (
        distance_score * heading_score
    )

    results.append({
        "trip_id": row["trip_id"],
        "gps_index": row["gps_index"],
        "timestamp": row["timestamp"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "edge_u": row["edge_u"],
        "edge_v": row["edge_v"],
        "edge_key": row["edge_key"],
        "distance_m": distance,
        "road_heading_deg": road_heading,
        "gps_heading_deg": gps_heading,
        "heading_diff_deg": heading_difference,
        "distance_score": distance_score,
        "heading_score": heading_score,
        "emission_score": emission_score
    })

emissions = pd.DataFrame(results)

emissions.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Emission calculation complete.")
print(f"Total candidate states: {len(emissions)}")
print(f"Output: {OUTPUT_FILE}")

print("\nEmission score statistics:")
print(
    emissions["emission_score"].describe()
)

print("\nFirst 10 emission states:")
print(
    emissions.head(10).to_string(index=False)
)
