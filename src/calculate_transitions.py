from pathlib import Path

import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd

CANDIDATE_FILE = Path("data/candidates.csv")
GRAPH_FILE = Path("data/road_network.graphml")
OUTPUT_FILE = Path("data/transitions.csv")

# Maximum road-network distance we allow between
# consecutive candidate edges.
MAX_NETWORK_DISTANCE = 1000.0

# Controls how strongly distance mismatch is penalized.
DISTANCE_SIGMA = 50.0


def get_edge_start_end(edge):
    return edge[0], edge[1]


# Load candidate states
candidates = pd.read_csv(CANDIDATE_FILE)

candidates["timestamp"] = pd.to_datetime(
    candidates["timestamp"]
)

# Load road graph
G = ox.load_graphml(GRAPH_FILE)

# Make sure edge lengths are numeric
for u, v, key, data in G.edges(keys=True, data=True):
    data["length"] = float(data.get("length", 0))


# Group candidates by GPS observation
candidate_groups = {
    gps_index: group
    for gps_index, group
    in candidates.groupby("gps_index")
}

gps_indices = sorted(candidate_groups.keys())

transition_rows = []

for current_pos in range(1, len(gps_indices)):

    prev_gps = gps_indices[current_pos - 1]
    curr_gps = gps_indices[current_pos]

    prev_candidates = candidate_groups[prev_gps]
    curr_candidates = candidate_groups[curr_gps]

    # GPS distance between observations
    prev_point = prev_candidates.iloc[0]

    curr_point = curr_candidates.iloc[0]

    gps_distance = ox.distance.great_circle(
        prev_point["latitude"],
        prev_point["longitude"],
        curr_point["latitude"],
        curr_point["longitude"]
    )

    for _, prev in prev_candidates.iterrows():

        prev_u = prev["edge_u"]
        prev_v = prev["edge_v"]

        for _, curr in curr_candidates.iterrows():

            curr_u = curr["edge_u"]
            curr_v = curr["edge_v"]

            # If previous edge ends at current edge's start,
            # the transition is directly connected.
            directly_connected = (
                prev_v == curr_u
            )

            # If the edges are the same physical road
            # or reverse directions, also treat them as
            # a local transition.
            same_edge = (
                prev_u == curr_u
                and prev_v == curr_v
            )

            reverse_edge = (
                prev_u == curr_v
                and prev_v == curr_u
            )

            try:

                # Shortest network distance from the end
                # of the previous candidate to the start
                # of the current candidate.
                if same_edge:

                    network_distance = 0.0

                elif prev_v == curr_u:

                    network_distance = 0.0

                else:

                    network_distance = nx.shortest_path_length(
                        G,
                        source=prev_v,
                        target=curr_u,
                        weight="length"
                    )

            except nx.NetworkXNoPath:

                network_distance = np.inf

            # Ignore impossible / excessively long transitions.
            if network_distance > MAX_NETWORK_DISTANCE:
                continue

            if np.isinf(network_distance):
                continue

            # Total estimated road distance between candidates.
            road_distance = (
                network_distance
                + float(curr["distance_m"])
                + float(prev["distance_m"])
            )

            # Distance discrepancy.
            discrepancy = abs(
                road_distance - gps_distance
            )

            distance_score = np.exp(
                -(discrepancy ** 2)
                / (2 * DISTANCE_SIGMA ** 2)
            )

            # Backtracking penalty.
            if reverse_edge:
                backtrack_score = 0.05

            elif directly_connected:
                backtrack_score = 1.0

            elif same_edge:
                backtrack_score = 0.8

            else:
                backtrack_score = 0.5

            transition_score = (
                distance_score
                * backtrack_score
            )

            transition_rows.append({
                "prev_gps_index": prev_gps,
                "gps_index": curr_gps,

                "prev_edge_u": prev_u,
                "prev_edge_v": prev_v,
                "prev_edge_key": prev["edge_key"],

                "edge_u": curr_u,
                "edge_v": curr_v,
                "edge_key": curr["edge_key"],

                "gps_distance_m": gps_distance,
                "network_distance_m": network_distance,
                "road_distance_m": road_distance,
                "distance_discrepancy_m": discrepancy,

                "directly_connected": directly_connected,
                "same_edge": same_edge,
                "reverse_edge": reverse_edge,

                "distance_score": distance_score,
                "backtrack_score": backtrack_score,
                "transition_score": transition_score
            })


transitions = pd.DataFrame(
    transition_rows
)

transitions.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Transition calculation complete.")
print(f"Total transitions: {len(transitions)}")
print(f"Output: {OUTPUT_FILE}")

if len(transitions) > 0:

    print("\nTransition score statistics:")
    print(
        transitions["transition_score"].describe()
    )

    print("\nDirectly connected transitions:")
    print(
        transitions["directly_connected"].sum()
    )

    print("\nBacktracking transitions:")
    print(
        transitions["reverse_edge"].sum()
    )

    print("\nFirst 10 transitions:")
    print(
        transitions.head(10).to_string(index=False)
    )

else:

    print("WARNING: No transitions were generated.")
