from pathlib import Path

import numpy as np
import pandas as pd

EMISSION_FILE = Path("data/emissions.csv")
TRANSITION_FILE = Path("data/transitions.csv")

EPS = 1e-12

def create_state(row):
    return (
        int(row["edge_u"]),
        int(row["edge_v"]),
        int(row["edge_key"]),
    )

def run_viterbi(emissions, transitions):
    """Run Viterbi over the supplied observation window."""

    emissions = emissions.copy()
    transitions = transitions.copy()

    emissions["state"] = emissions.apply(
        create_state,
        axis=1
    )

    gps_indices = sorted(emissions["gps_index"].unique())

    groups = {
        gps: group
        for gps, group in emissions.groupby("gps_index")
    }

    if not gps_indices:
        return pd.DataFrame()

    first_gps = gps_indices[0]
    first_group = groups[first_gps]

    dp = {}
    backpointer = {}

    for _, row in first_group.iterrows():
        state = row["state"]
        emission = max(float(row["emission_score"]), EPS)

        dp[state] = np.log(emission)
        backpointer[(first_gps, state)] = None

    for position in range(1, len(gps_indices)):
        gps = gps_indices[position]
        previous_gps = gps_indices[position - 1]

        current_group = groups[gps]

        transition_group = transitions[
            (transitions["prev_gps_index"] == previous_gps)
            & (transitions["gps_index"] == gps)
        ]

        current_dp = {}

        for _, curr_row in current_group.iterrows():
            curr_state = curr_row["state"]
            emission = max(float(curr_row["emission_score"]), EPS)

            candidates = transition_group[
                (transition_group["edge_u"] == curr_state[0])
                & (transition_group["edge_v"] == curr_state[1])
                & (transition_group["edge_key"] == curr_state[2])
            ]

            best_score = -np.inf
            best_prev_state = None

            for _, trans_row in candidates.iterrows():

                prev_state = (
                    int(trans_row["prev_edge_u"]),
                    int(trans_row["prev_edge_v"]),
                    int(trans_row["prev_edge_key"])
                )

                if prev_state not in dp:
                    continue

                transition_score = max(
                    float(trans_row["transition_score"]),
                    EPS
                )

                score = (
                    dp[prev_state]
                    + np.log(transition_score)
                    + np.log(emission)
                )

                if score > best_score:
                    best_score = score
                    best_prev_state = prev_state

            if best_prev_state is not None:
                current_dp[curr_state] = best_score
                backpointer[(gps, curr_state)] = best_prev_state

        if not current_dp:
            for _, row in current_group.iterrows():
                state = row["state"]
                emission = max(
                    float(row["emission_score"]),
                    EPS
                )

                current_dp[state] = np.log(emission)
                backpointer[(gps, state)] = None

        dp = current_dp

    last_gps = gps_indices[-1]
    last_state = max(dp, key=dp.get)

    path = []
    current_state = last_state

    for gps in reversed(gps_indices):

        path.append({
            "gps_index": gps,
            "state": current_state
        })

        current_state = backpointer.get(
            (gps, current_state)
        )

        if current_state is None and gps != first_gps:
            break

    path.reverse()

    return pd.DataFrame(path)

def run_realtime_hmm(emissions, transitions, window_size=30, buffer_size=0):
    """
    Run real-time buffered HMM map matching.

    window_size:
        Number of observations used by each Viterbi window.

    buffer_size:
        Number of future observations used before committing
        the matched state for an observation.

    The final flush ensures that all observations are evaluated.
    """

    gps_indices = sorted(emissions["gps_index"].unique())
    committed = {}

    def process_window(available_position, target_position):
        if target_position < 0 or target_position >= len(gps_indices):
            return

        if target_position in committed:
            return

        start_position = max(0, available_position - window_size + 1)

        window_gps = gps_indices[
            start_position:available_position + 1
        ]

        target_gps = gps_indices[target_position]

        if target_gps not in window_gps:
            return

        window_emissions = emissions[
            emissions["gps_index"].isin(window_gps)
        ].copy()

        window_transitions = transitions[
            transitions["gps_index"].isin(window_gps)
            & transitions["prev_gps_index"].isin(window_gps)
        ].copy()

        if window_emissions.empty:
            return

        result = run_viterbi(
            window_emissions,
            window_transitions
        )

        if result.empty:
            return

        target_result = result[
            result["gps_index"] == target_gps
        ]

        if target_result.empty:
            return

        row = target_result.iloc[0]

        committed[target_position] = {
            "gps_index": row["gps_index"],
            "matched_state": row["state"],
            "buffer_size": buffer_size,
            "window_size": window_size,
            "delay_seconds": buffer_size,
        }

    # Normal real-time processing
    for available_position in range(len(gps_indices)):

        target_position = available_position - buffer_size

        process_window(
            available_position,
            target_position
        )

    # Final flush
    final_position = len(gps_indices) - 1

    for target_position in range(
        max(0, len(gps_indices) - buffer_size),
        len(gps_indices)
    ):
        process_window(
            final_position,
            target_position
        )

    rows = [
        committed[position]
        for position in sorted(committed.keys())
    ]

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)

    # Extract matched edge components
    result[
        ["matched_edge_u", "matched_edge_v", "matched_edge_key"]
    ] = pd.DataFrame(
        result["matched_state"].tolist(),
        index=result.index
    )

    # Get distance for the ACTUAL matched edge
    distance_lookup = emissions[
        [
            "gps_index",
            "edge_u",
            "edge_v",
            "edge_key",
            "distance_m"
        ]
    ].copy()

    result = result.merge(
        distance_lookup,
        left_on=[
            "gps_index",
            "matched_edge_u",
            "matched_edge_v",
            "matched_edge_key"
        ],
        right_on=[
            "gps_index",
            "edge_u",
            "edge_v",
            "edge_key"
        ],
        how="left"
    )

    result.drop(
        columns=["edge_u", "edge_v", "edge_key"],
        inplace=True
    )

    return result
