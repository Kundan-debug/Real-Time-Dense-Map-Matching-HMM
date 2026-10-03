from pathlib import Path

import osmnx as ox
import pandas as pd

GPS_FILE = Path("data/taxi_gps_features.csv")
OUTPUT_FILE = Path("data/road_network.graphml")

TRIPS = [
    "20080404_043128",
    "20080404_071650"
]

df = pd.read_csv(GPS_FILE)

gps = df[df["trip_id"].isin(TRIPS)].copy()

# Get GPS bounding box
min_lat = gps["latitude"].min()
max_lat = gps["latitude"].max()
min_lon = gps["longitude"].min()
max_lon = gps["longitude"].max()

# Add a small margin around the trajectory
margin = 0.02

north = max_lat + margin
south = min_lat - margin
east = max_lon + margin
west = min_lon - margin

print("GPS bounding box:")
print(f"North: {north}")
print(f"South: {south}")
print(f"East:  {east}")
print(f"West:  {west}")

print("\nDownloading OpenStreetMap road network...")

G = ox.graph_from_bbox(
    (west, south, east, north),
    network_type="drive",
    simplify=True
)

print("\nRoad network downloaded.")
print(f"Nodes: {len(G.nodes)}")
print(f"Edges: {len(G.edges)}")

ox.save_graphml(G, OUTPUT_FILE)

print(f"\nSaved to: {OUTPUT_FILE}")
