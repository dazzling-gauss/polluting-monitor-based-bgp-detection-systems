# Polluting Monitor-based BGP Anomaly Detection Systems

This repository contains the code to run experiments on state-of-the-art bgp anomaly detection methods based on public monitors. We provide the code to run 3 pollution-based attacks. Two of them are based on the work of [DFOH](https://dfoh.uclouvain.be/), one is based on the work of [BEAM](https://www.usenix.org/system/files/sec24summer-prepub-670-chen-yihao.pdf).

## Getting Started

### Prerequisites

- **Python Version**: The experiments are designed to run on Python 3.10.
- **Dependencies**: All necessary Python packages are listed in `requirements.txt`. Install them using pip:

```bash
pip install -r requirements.txt
```

Alternatively, for those using pipenv, set up a virtual environment and install dependencies with:

```bash
pipenv shell
pipenv install
```

- **Additional Setup**: Running the DFOH or BEAM attack experiments requires further dependencies. Detailed installation instructions are available in the `README.md` files within their respective directories.


## Running Experiments

To discover all available commands and their usage, execute:
```bash
python main.py --help
```

### Examples

- DFOH blaming attack:
```bash
python main.py dfoh blame 205218
python main.py dfoh plot blame
```
- DFOH pollution attack
```bash
python main.py dfoh run-single-attacker 205218 --max_runs=5
```
- BEAM pollution attack
```bash
python main.py beam pollution
```