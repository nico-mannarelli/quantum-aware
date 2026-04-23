from __future__ import annotations
import time
import numpy as np
from braket.devices import LocalSimulator

from backends.braket_backends import (
    get_local_simulator,
    qiskit_to_braket,
    run_braket_circuit,
    braket_circuit_metrics,
)
from analysis.metrics import ghz_fidelity
from circuits.qaoa import approximation_ratio, bind_qaoa


def run_braket_ghz(qiskit_circuit, n_qubits: int, shots: int = 1024) -> dict:
    device = get_local_simulator()
    bc = qiskit_to_braket(qiskit_circuit)

    t0 = time.perf_counter()
    counts = run_braket_circuit(bc, device, shots=shots)
    runtime = time.perf_counter() - t0

    metrics = braket_circuit_metrics(bc)
    quality = ghz_fidelity(counts, n_qubits)

    return {
        "workload": "ghz",
        "n_qubits": n_qubits,
        "backend": "braket_local",
        "opt_level": None,
        "shots": shots,
        "transpile_time_s": 0.0,
        "runtime_s": runtime,
        "depth": metrics["depth"],
        "gate_count": metrics["gate_count"],
        "two_qubit_gate_count": metrics["two_qubit_gate_count"],
        "quality_score": quality,
        "counts": counts,
    }


def run_braket_qaoa(qiskit_circuit, graph, shots: int = 1024) -> dict:
    from scipy.optimize import minimize

    device = get_local_simulator()
    n_qubits = graph.number_of_nodes()

    def objective(params):
        p = len(params) // 2
        bound = bind_qaoa(qiskit_circuit, params[:p].tolist(), params[p:].tolist())
        bc = qiskit_to_braket(bound)
        c = run_braket_circuit(bc, device, shots=shots)
        return -approximation_ratio(c, graph)

    x0 = np.random.default_rng(0).uniform(0, np.pi, 2)
    t0 = time.perf_counter()
    opt_result = minimize(objective, x0, method="COBYLA", options={"maxiter": 30, "rhobeg": 0.5})
    total_time = time.perf_counter() - t0

    best_params = opt_result.x
    p = len(best_params) // 2
    bound = bind_qaoa(qiskit_circuit, best_params[:p].tolist(), best_params[p:].tolist())
    bc = qiskit_to_braket(bound)

    metrics = braket_circuit_metrics(bc)

    t0 = time.perf_counter()
    counts = run_braket_circuit(bc, device, shots=shots)
    runtime = time.perf_counter() - t0

    quality = approximation_ratio(counts, graph)

    return {
        "workload": "qaoa_maxcut",
        "n_qubits": n_qubits,
        "backend": "braket_local",
        "opt_level": None,
        "shots": shots,
        "transpile_time_s": 0.0,
        "runtime_s": runtime + total_time,
        "depth": metrics["depth"],
        "gate_count": metrics["gate_count"],
        "two_qubit_gate_count": metrics["two_qubit_gate_count"],
        "quality_score": quality,
        "counts": counts,
    }
