# Real-Time Dense Map Matching with Hidden Markov Models

## Authors

- **Kundan V** — PES1UG24CS243
- **Kaushik** — PES1UG24CS222

## Overview

This project implements a real-time dense GPS map-matching system using a Hidden Markov Model (HMM) and the Viterbi algorithm.

The system maps noisy GPS observations to likely road segments using OpenStreetMap (OSM) road data. It uses GPS-to-road distance and heading information for emission probabilities, while transition probabilities consider road-network connectivity, travel distance, and backtracking.

A buffered real-time inference approach is used to study the trade-off between output delay and map-matching distance.

## Problem Statement

GPS observations collected from mobile devices can contain noise and positional errors. Map matching is the process of associating these noisy GPS observations with the most likely road segments on a road network.

The objective of this project is to develop a real-time HMM-based map-matching system that can process dense GPS trajectories and study how a small output buffer affects map-matching performance.

## Dataset

The project uses the **Microsoft GeoLife GPS Trajectory Dataset**.

The dataset contains GPS trajectories collected from mobile devices. A subset of taxi trajectories is extracted and used for the experiments.

The selected trajectories contain dense GPS observations, making them suitable for studying real-time map matching.

## Approach

The overall workflow is:

1. Extract taxi trajectories from the GeoLife dataset.
2. Calculate GPS motion features such as speed and heading.
3. Download the corresponding OpenStreetMap road network.
4. Generate candidate road segments around each GPS observation.
5. Calculate emission scores using:
   - GPS-to-road distance
   - GPS heading versus road heading
6. Calculate transition scores using:
   - Road-network distance
   - GPS displacement
   - Road connectivity
   - Backtracking penalty
7. Apply the Viterbi algorithm to find the most likely sequence of road segments.
8. Perform buffered real-time inference using different output delays.
9. Compare the resulting map-matching distance and percentage of observations within 10 metres of the selected road.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Kundan-debug/Real-Time-Dense-Map-Matching-HMM.git
cd Real-Time-Dense-Map-Matching-HMM
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Dataset Setup

Download the **Microsoft GeoLife GPS Trajectory Dataset** and extract it into the `data/` directory.

The expected directory structure is:

```text
data/
└── Geolife Trajectories 1.3/
```

The raw dataset is not included in this repository because of its size.

## Running the Project

Run the scripts in the following order.

### 1. Inspect the dataset

```bash
python src/inspect_dataset.py
```

### 2. Extract taxi trajectories

```bash
python src/extract_taxi_data.py
```

### 3. Add motion features

```bash
python src/add_motion_features.py
```

### 4. Download the road network

```bash
python src/download_road_network.py
```

### 5. Generate road candidates

For the primary trajectory:

```bash
python src/generate_candidates.py 20080404_043128
```

### 6. Calculate emission scores

```bash
python src/calculate_emissions.py
```

### 7. Calculate transition scores

```bash
python src/calculate_transitions.py
```

### 8. Run Viterbi map matching

```bash
python src/viterbi.py
```

### 9. Run real-time HMM experiments

```bash
python src/realtime_hmm.py
```

The generated experiment results and plots are stored in the `results/` directory.

## Results

The experiments evaluate the effect of different output buffer sizes on map-matching performance.

The tested buffer sizes are:

```text
0, 5, 10, 15, 20 seconds
```

The main evaluation measures are:

- Mean GPS-to-matched-road distance
- Median GPS-to-matched-road distance
- Percentage of observations within 10 metres of the matched road
- Percentage of observations within 20 metres of the matched road
- Observation coverage

The generated result files include:

The generated result files include:

```text
results/
├── buffer_experiment.csv
├── buffer_experiment_trip2.csv
├── combined_delay_vs_distance.png
├── delay_vs_10m_accuracy.png
├── delay_vs_distance.png
├── final_experiment_summary.csv
├── taxi_trajectories.csv
└── trajectory_summary.csv
```

The experiments showed a small improvement when introducing a short output buffer, while increasing the buffer beyond approximately 5 seconds produced little additional change for the tested trajectories.

## Conclusion

The project demonstrates a real-time GPS map-matching approach based on a Hidden Markov Model and Viterbi decoding.

The results show that buffered inference can provide a small improvement in map-matching distance for the tested trajectories. However, the effect of buffering varies between trajectories, indicating that trajectory characteristics can influence the performance of the same HMM configuration.

## Limitations

The GeoLife dataset used in this project does not provide ground-truth road-segment labels for the selected trajectories. Therefore, the evaluation uses GPS-to-selected-road distance as a map-matching distance metric rather than claiming true road-level accuracy.

The implementation is also a simplified adaptation of the reference HMM approach. The current system uses hand-designed Gaussian scoring functions rather than the learned SVM weights described in the reference paper.

## Requirements

The main Python dependencies are listed in `requirements.txt`:

```text
numpy
pandas
scipy
scikit-learn
matplotlib
seaborn
osmnx
pyproj
shapely
```

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
```
