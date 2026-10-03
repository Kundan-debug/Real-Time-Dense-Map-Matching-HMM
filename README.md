# Real-Time Dense Map Matching with Hidden Markov Models

## Authors

- **Kundan V** — PES1UG24CS243
- **Kaushik** — PES1UG24CS222

## Overview

This project implements a real-time dense GPS map-matching system using a Hidden Markov Model (HMM) and the Viterbi algorithm.

The system takes noisy GPS trajectories and matches each GPS observation to a candidate road segment from an OpenStreetMap road network. A buffered real-time version is also implemented to study the trade-off between output delay and map-matching quality.

## Problem Statement

GPS observations from mobile devices can contain positional noise and may not lie exactly on the road network. The objective is to determine the most likely road segment corresponding to each GPS observation while supporting real-time operation.

The project investigates how introducing a short output buffer affects the GPS-to-matched-road distance.

## Dataset

The project uses the Microsoft GeoLife GPS Trajectory Dataset 1.3.

The experiment uses taxi-mode trajectories from user 010. Two dense 1 Hz trajectories were selected:

- `20080404_043128` — 1,925 GPS observations
- `20080404_071650` — 2,167 GPS observations

The dataset does not provide ground-truth road-segment labels. Therefore, evaluation is based on GPS-to-matched-road distance rather than true road-level accuracy.

## Methodology

The processing pipeline is:

GPS trajectories  
↓  
Motion feature extraction  
↓  
OpenStreetMap road network  
↓  
Candidate road generation  
↓  
Emission scoring  
↓  
Transition scoring  
↓  
Viterbi map matching  
↓  
Real-time buffered HMM  
↓  
Delay vs. distance evaluation

### 1. Motion Features

For consecutive GPS observations, the system calculates:

- Distance travelled
- Speed
- Heading
- Time difference

Large time gaps are handled separately to avoid treating missing intervals as continuous motion.

### 2. Candidate Generation

For every GPS observation, road segments within a 50 metre radius are considered candidate states.

The road network is obtained from OpenStreetMap using OSMnx.

### 3. Emission Model

Each candidate road segment receives an emission score based on:

- Distance between the GPS point and the road segment
- Difference between GPS heading and road-segment heading

Gaussian scoring functions are used for these features.

The combined emission score is:

`distance_score × heading_score`

### 4. Transition Model

Transitions between consecutive candidate road segments are scored using:

- Estimated road-network distance
- GPS displacement
- Distance discrepancy
- Same-edge movement
- Directly connected edges
- Reverse/backtracking transitions

A lower penalty is assigned to transitions that represent backtracking.

### 5. Viterbi Algorithm

The Viterbi algorithm finds the highest-scoring sequence of road-segment states over the GPS observations.

The implementation uses log-space dynamic programming to avoid numerical underflow.

### 6. Real-Time Buffered HMM

A sliding Viterbi window of 30 observations is used.

The real-time implementation introduces output buffers of:

- 0 seconds
- 5 seconds
- 10 seconds
- 15 seconds
- 20 seconds

A buffer delays the commitment of a matched state so that future GPS observations can be incorporated into the decision.

## Experimental Results

### Trajectory 1

Trajectory `20080404_043128` contains 1,925 observations.

| Buffer | Mean Distance (m) | Median Distance (m) | Within 10 m |
|---:|---:|---:|---:|
| 0 s | 3.524 | 2.586 | 97.14% |
| 5 s | 3.507 | 2.588 | 97.30% |
| 10 s | 3.507 | 2.588 | 97.30% |
| 15 s | 3.507 | 2.588 | 97.30% |
| 20 s | 3.507 | 2.588 | 97.30% |

### Trajectory 2

Trajectory `20080404_071650` contains 2,167 observations.

| Buffer | Mean Distance (m) | Median Distance (m) | Within 10 m |
|---:|---:|---:|---:|
| 0 s | 5.450 | 3.816 | 83.80% |
| 5 s | 5.383 | 3.779 | 84.45% |
| 10 s | 5.384 | 3.779 | 84.45% |
| 15 s | 5.384 | 3.779 | 84.45% |
| 20 s | 5.384 | 3.779 | 84.45% |

All tested configurations achieved 100% observation coverage after the final-buffer flush.

### Observations

Across both trajectories, introducing a 5-second buffer produced a small reduction in mean GPS-to-matched-road distance.

Increasing the buffer beyond 5 seconds produced little additional change in the tested trajectories.

The second trajectory produced larger distances than the first, indicating that the same HMM configuration behaves differently across trajectories.

## Results Figures

The generated figures are available in the `results/` directory:

- `delay_vs_distance.png`
- `combined_delay_vs_distance.png`
- `delay_vs_10m_accuracy.png`

## Project Structure

```text
Real-Time-Dense-Map-Matching-HMM/
├── results/
│   ├── buffer_experiment.csv
│   ├── buffer_experiment_trip2.csv
│   ├── combined_delay_vs_distance.png
│   ├── delay_vs_10m_accuracy.png
│   ├── delay_vs_distance.png
│   ├── final_experiment_summary.csv
│   ├── taxi_trajectories.csv
│   └── trajectory_summary.csv
├── src/
│   ├── add_motion_features.py
│   ├── calculate_emissions.py
│   ├── calculate_transitions.py
│   ├── download_road_network.py
│   ├── extract_taxi_data.py
│   ├── find_taxi_trajectories.py
│   ├── generate_candidates.py
│   ├── inspect_dataset.py
│   ├── realtime_hmm.py
│   └── viterbi.py
├── .gitignore
├── README.md
└── requirements.txt
