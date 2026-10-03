from pathlib import Path

import numpy as np
import pandas as pd

EMISSION_FILE = Path("data/emissions.csv")
TRANSITION_FILE = Path("data/transitions.csv")
OUTPUT_FILE = Path("data/viterbi_result.csv")

# Small value to avoid log(0)
EPS = 1e-12

# Load data
emissions = pd.read_csv(EMISSION_FILE)
transitions = pd.read_csv(TRANSITION_FILE)

emissions["timestamp"] = pd.to_datetime(
    emissions["timestamp"]
)

# Unique GPS observations
gps_indices = sorted(
    emissions["gps_index"].unique()
)

# Create a unique state identifier
def state_id(row):
    return (
        int(row["edge_u"]),
        int(row["edge_v"]),
        int(row["edge_key"])
    )

emissions["state"] = emissions.apply(
    state_id,
    axis=1
)

# Group emission states by GPS observation
emission_groups = {
    gps_index: group
    for gps_index, group
    in emissions.groupby("gps_index")
}

# Transition lookup:
# (previous_state, current_state) -> score
transition_lookup = {}

for _, row in transitions.iterrows():

    previous_state = (
        int(row["prev_edge_u"]),
        int(row["prev_edge_v"]),
        int(row["prev_edge_key"])
    )

    current_state = (
        int(row["edge_u"]),
        int(row["edge_v"]),
        int(row["edge_key"])
    )

    transition_lookup[
        (row["prev_gps_index"], row["gps_index"],
         previous_state, current_state)
    ] = row["transition_score"]

# Viterbi dynamic programming tables
viterbi = {}
backpointer = {}

# Initialization

first_gps = gps_indices[0]

viterbi[first_gps] = {}

for _, row in emission_groups[first_gps].iterrows():

    state = row["state"]

    emission = max(
        float(row["emission_score"]),
        EPS
    )

    viterbi[first_gps][state] = np.log(
        emission
    )

    backpointer[
        (first_gps, state)
    ] = None

# Recursion

for position in range(1, len(gps_indices)):

    prev_gps = gps_indices[position - 1]
    current_gps = gps_indices[position]

    viterbi[current_gps] = {}

    current_candidates = emission_groups[
        current_gps
    ]

    previous_candidates = emission_groups[
        prev_gps
    ]

    for _, current_row in current_candidates.iterrows():

        current_state = current_row["state"]

        emission = max(
            float(current_row["emission_score"]),
            EPS
        )

        best_score = -np.inf
        best_previous_state = None

        for _, previous_row in previous_candidates.iterrows():

            previous_state = previous_row["state"]

            previous_score = viterbi[
                prev_gps
            ].get(
                previous_state,
                -np.inf
            )

            if previous_score == -np.inf:
                continue

            transition_score = transition_lookup.get(
                (
                    prev_gps,
                    current_gps,
                    previous_state,
                    current_state
                ),
                EPS
            )

            transition_score = max(
                float(transition_score),
                EPS
            )

            score = (
                previous_score
                + np.log(transition_score)
                + np.log(emission)
            )

            if score > best_score:

                best_score = score
                best_previous_state = previous_state

        viterbi[current_gps][
            current_state
        ] = best_score

        backpointer[
            (current_gps, current_state)
        ] = best_previous_state

# Backtracking

last_gps = gps_indices[-1]

last_state = max(
    viterbi[last_gps],
    key=viterbi[last_gps].get
)

best_path = []

current_state = last_state

for gps_index in reversed(gps_indices):

    best_path.append(
        (gps_index, current_state)
    )

    current_state = backpointer[
        (gps_index, current_state)
    ]

    if current_state is None:
        break


best_path.reverse()

# Create result

results = []

for gps_index, state in best_path:

    gps_rows = emission_groups[
        gps_index
    ]

    match = gps_rows[
        gps_rows["state"] == state
    ].iloc[0]

    results.append({
        "gps_index": gps_index,
        "timestamp": match["timestamp"],
        "latitude": match["latitude"],
        "longitude": match["longitude"],
        "edge_u": state[0],
        "edge_v": state[1],
        "edge_key": state[2],
        "distance_m": match["distance_m"],
        "emission_score": match["emission_score"]
    })

result = pd.DataFrame(results)

result.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Viterbi map matching complete.")
print(f"GPS observations: {len(gps_indices)}")
print(f"Matched observations: {len(result)}")
print(f"Output: {OUTPUT_FILE}")

print("\nFirst 10 matched states:")
print(
    result.head(10).to_string(index=False)
)
