# Quantum Benchmark Toolkit

A software + experimentation toolkit that compiles small quantum workloads for different backends, runs them on simulators, and compares metrics: circuit depth, two-qubit gate count, runtime, and output quality.

## What it does

1. Generates circuits (GHZ state, QAOA Max-Cut).
2. Compiles each circuit for several Qiskit backends at optimization levels 0–3.
3. Runs each on ideal and noisy (fake-device) simulators; optionally Braket local simulator.
4. Saves results to CSV/JSON.
5. Plots depth, gate count, quality, and runtime comparisons.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Full run: all workloads, all backends, all optimization levels
python scripts/run_experiment.py

# Subset run
python scripts/run_experiment.py --workloads ghz --backends ideal_simulator fake_nairobi --shots 512

# Include Braket local simulator
python scripts/run_experiment.py --braket

# Override qubit counts and opt levels
python scripts/run_experiment.py --qubit-counts 3 5 7 --opt-levels 1 3
```

Results land in `results/raw/` (JSON) and `results/processed/` (CSV + plots).

## Metrics collected

| Metric | Description |
|---|---|
| `depth` | Transpiled circuit depth |
| `gate_count` | Total gate count after transpilation |
| `two_qubit_gate_count` | CX/ECR/CZ count - main noise proxy |
| `transpile_time_s` | Time to run the pass manager |
| `runtime_s` | Time to execute on simulator |
| `quality_score` | GHZ: P(00..0) + P(11..1); QAOA: approximation ratio |

## Backends

**Qiskit (primary)**
- `ideal_simulator` - AerSimulator, no noise
- `fake_nairobi` - 7-qubit IBM fake backend with realistic noise model
- `fake_lagos` - 7-qubit IBM fake backend (different topology)

**Amazon Braket (secondary, optional)**
- `braket_local` - LocalSimulator, no noise, exact state vector

## Project structure

```
configs/         experiment configs (YAML)
circuits/        workload definitions (Qiskit)
backends/        backend factory + metrics helpers
runners/         experiment execution (Qiskit + Braket)
analysis/        metric helpers and plotting
results/raw/     raw JSON output
results/processed/ CSV summaries + plots
notebooks/       exploration.ipynb
scripts/         run_experiment.py
```
