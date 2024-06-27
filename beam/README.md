# Run Beam experiments

This folder contains the code to run BEAM experiments. To successfully execute the experiments, additional dependencies are required.

## Requirements (repo + data)

Before running the experiments, ensure the following prerequisites are met:

1. **BEAM Repository**: Have the [BEAM repository](https://github.com/yhchen-tsinghua/routing-anomaly-detection/tree/master)
2. **Data Requirements**: The experiments require specific datasets, including:
   - A trained model.
   - Monitor data.
   - Pollution data.

We provide a demo dataset, as training and collecting bgp routes could take a while.

## Setup Instructions

To clone the BEAM repository and extract the demo data, execute the script provided:

```bash
./beam/script.sh
```

## Usage

To run the pollution on the demo data run:

```bash
python main.py beam pollution
```