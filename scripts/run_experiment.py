"""Main experiment runner. Usage: python scripts/run_experiment.py [--workloads ghz qaoa] [--backends ideal fake_nairobi] [--shots 1024]"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from circuits.ghz import build_ghz
from circuits.qaoa import build_maxcut_graph, build_qaoa
from runners.run_qiskit import run_qiskit_ghz, run_qiskit_qaoa
from analysis.plots import generate_all_plots


QISKIT_BACKENDS = ["ideal_simulator", "fake_nairobi", "fake_lagos"]
ALL_WORKLOADS = ["ghz", "qaoa"]
OPT_LEVELS = [0, 1, 2, 3]

RAW_DIR = ROOT / "results" / "raw"
PROC_DIR = ROOT / "results" / "processed"


def run_ghz_experiments(backends: list[str], qubit_counts: list[int], shots: int, opt_levels: list[int]) -> list[dict]:
    rows = []
    for n in qubit_counts:
        circuit = build_ghz(n)
        for backend in backends:
            for opt in opt_levels:
                print(f"  GHZ n={n} | {backend} | opt={opt}")
                try:
                    row = run_qiskit_ghz(circuit, n, backend, opt, shots)
                    rows.append(row)
                except Exception as e:
                    print(f"    FAILED: {e}")
    return rows


def run_qaoa_experiments(backends: list[str], qubit_counts: list[int], shots: int, opt_levels: list[int]) -> list[dict]:
    rows = []
    for n in qubit_counts:
        graph = build_maxcut_graph(n, seed=42)
        circuit = build_qaoa(graph, p=1)
        for backend in backends:
            for opt in opt_levels:
                print(f"  QAOA n={n} | {backend} | opt={opt}")
                try:
                    row = run_qiskit_qaoa(circuit, graph, backend, opt, shots)
                    rows.append(row)
                except Exception as e:
                    print(f"    FAILED: {e}")
    return rows


def run_braket_experiments(workloads: list[str], shots: int) -> list[dict]:
    rows = []
    try:
        from runners.run_braket import run_braket_ghz, run_braket_qaoa
    except ImportError as e:
        print(f"  Braket not available: {e}")
        return rows

    if "ghz" in workloads:
        for n in [3, 5]:
            print(f"  Braket GHZ n={n}")
            try:
                circuit = build_ghz(n)
                row = run_braket_ghz(circuit, n, shots)
                rows.append(row)
            except Exception as e:
                print(f"    FAILED: {e}")

    if "qaoa" in workloads:
        for n in [4]:
            print(f"  Braket QAOA n={n}")
            try:
                graph = build_maxcut_graph(n, seed=42)
                circuit = build_qaoa(graph, p=1)
                from runners.run_braket import run_braket_qaoa
                row = run_braket_qaoa(circuit, graph, shots)
                rows.append(row)
            except Exception as e:
                print(f"    FAILED: {e}")

    return rows


def save_results(rows: list[dict], timestamp: str) -> tuple[Path, Path]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    json_path = RAW_DIR / f"results_{timestamp}.json"
    safe_rows = [{k: v for k, v in r.items() if k != "counts"} for r in rows]
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2, default=str)

    df = pd.DataFrame(safe_rows)
    csv_path = PROC_DIR / f"results_{timestamp}.csv"
    df.to_csv(csv_path, index=False)

    return json_path, csv_path


def main():
    parser = argparse.ArgumentParser(description="Quantum benchmarking experiment runner")
    parser.add_argument("--workloads", nargs="+", default=ALL_WORKLOADS, choices=ALL_WORKLOADS)
    parser.add_argument("--backends", nargs="+", default=QISKIT_BACKENDS)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--opt-levels", nargs="+", type=int, default=OPT_LEVELS)
    parser.add_argument("--qubit-counts", nargs="+", type=int, default=[3, 5])
    parser.add_argument("--braket", action="store_true", help="Also run Braket local simulator")
    args = parser.parse_args()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    all_rows: list[dict] = []

    if "ghz" in args.workloads:
        print("\n=== GHZ experiments ===")
        all_rows.extend(run_ghz_experiments(args.backends, args.qubit_counts, args.shots, args.opt_levels))

    if "qaoa" in args.workloads:
        print("\n=== QAOA Max-Cut experiments ===")
        all_rows.extend(run_qaoa_experiments(args.backends, args.qubit_counts, args.shots, args.opt_levels))

    if args.braket:
        print("\n=== Braket experiments ===")
        all_rows.extend(run_braket_experiments(args.workloads, args.shots))

    if not all_rows:
        print("No results collected.")
        return

    json_path, csv_path = save_results(all_rows, timestamp)
    print(f"\nSaved raw JSON: {json_path}")
    print(f"Saved CSV: {csv_path}")

    safe_rows = [{k: v for k, v in r.items() if k != "counts"} for r in all_rows]
    df = pd.DataFrame(safe_rows)
    print(f"\nTotal rows: {len(df)}")
    print(df[["workload", "backend", "opt_level", "n_qubits", "depth", "two_qubit_gate_count", "quality_score"]].to_string(index=False))

    print("\nGenerating plots...")
    plot_paths = generate_all_plots(df)
    for p in plot_paths:
        print(f"  Saved: {p}")


if __name__ == "__main__":
    main()
