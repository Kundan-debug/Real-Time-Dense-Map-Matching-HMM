from pathlib import Path
import sys

import osmnx as ox
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point

GPS_FILE = Path("data/taxi_gps_features.csv")
GRAPH_FILE = Path("data/road_network.graphml")
OUTPUT_FILE = Path("data/candidates.csv")

TRIP_ID = sys.argv[1] if len(sys.argv) > 1 else "20080404_071650"
RADIUS_M = 50


# Load GPS data
df = pd.read_csv(GPS_FILE)

df = df[
    df["trip_id"] == TRIP_ID
].copy()

df["timestamp"] = pd.to_datetime(df["timestamp"])

print(f"GPS points: {len(df)}")


# Load road network
G = ox.load_graphml(GRAPH_FILE)

print(f"Road nodes: {len(G.nodes)}")
print(f"Road edges: {len(G.edges)}")


# Project road network
G_projected = ox.project_graph(G)

nodes, edges = ox.graph_to_gdfs(
    G_projected,
    nodes=True,
    edges=True
)

print(f"Projected CRS: {edges.crs}")


# Coordinate transformation
transformer = Transformer.from_crs(
    "EPSG:4326",
    edges.crs,
    always_xy=True
)


# Generate candidates
candidate_rows = []

for gps_idx, row in df.iterrows():

    x, y = transformer.transform(
        row["longitude"],
        row["latitude"]
    )

    gps_point = Point(x, y)

    nearby_edges = edges[
        edges.geometry.distance(gps_point) <= RADIUS_M
    ]

    for (u, v, key), edge in nearby_edges.iterrows():

        distance = edge.geometry.distance(gps_point)

        candidate_rows.append({
            "trip_id": row["trip_id"],
            "gps_index": gps_idx,
            "timestamp": row["timestamp"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],

            # Motion features
            "speed_mps": row["speed_mps"],
            "heading_deg": row["heading_deg"],
            "time_diff_s": row["time_diff_s"],

            # Road candidate
            "edge_u": u,
            "edge_v": v,
            "edge_key": key,
            "distance_m": distance
        })


candidates = pd.DataFrame(candidate_rows)

candidates = candidates.sort_values(
    ["gps_index", "distance_m"]
)

candidates.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\nCandidate generation complete.")
print(f"Total candidate rows: {len(candidates)}")

if len(candidates) > 0:

    counts = (
        candidates
        .groupby("gps_index")
        .size()
    )

    print(f"GPS points with candidates: {counts.size}")
    print(f"Average candidates per GPS point: {counts.mean():.2f}")
    print(f"Maximum candidates for one GPS point: {counts.max()}")

    print("\nFirst 10 candidates:")
    print(
        candidates.head(10).to_string(index=False)
    )

else:
    print("WARNING: No candidates were found.")
