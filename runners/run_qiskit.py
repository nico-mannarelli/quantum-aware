from __future__ import annotations
import time
import numpy as np
from qiskit_aer import AerSimulator

from backends.qiskit_backends import (
    get_ideal_simulator,
    get_fake_backend,
    get_noisy_simulator,
    transpile_circuit,
    circuit_metrics,
)
from analysis.metrics import ghz_fidelity, counts_from_qiskit
from circuits.qaoa import approximation_ratio


def run_qiskit_ghz(circuit, n_qubits: int, backend_name: str, opt_level: int, shots: int = 1024) -> dict:
    if backend_name == "ideal_simulator":
        simulator = get_ideal_simulator()
        t0 = time.perf_counter()
        transpiled = transpile_circuit(circuit, simulator, opt_level)
        transpile_time = time.perf_counter() - t0
        t0 = time.perf_counter()
        job = simulator.run(transpiled, shots=shots)
        result = job.result()
        runtime = time.perf_counter() - t0
    else:
        fake_be = get_fake_backend(backend_name)
        noisy_sim = get_noisy_simulator(fake_be)
        t0 = time.perf_counter()
        transpiled = transpile_circuit(circuit, fake_be, opt_level)
        transpile_time = time.perf_counter() - t0
        t0 = time.perf_counter()
        job = noisy_sim.run(transpiled, shots=shots)
        result = job.result()
        runtime = time.perf_counter() - t0

    counts = counts_from_qiskit(result)
    metrics = circuit_metrics(transpiled)
    quality = ghz_fidelity(counts, n_qubits)

    return {
        "workload": "ghz",
        "n_qubits": n_qubits,
        "backend": backend_name,
        "opt_level": opt_level,
        "shots": shots,
        "transpile_time_s": transpile_time,
        "runtime_s": runtime,
        "depth": metrics["depth"],
        "gate_count": metrics["gate_count"],
        "two_qubit_gate_count": metrics["two_qubit_gate_count"],
        "quality_score": quality,
        "counts": counts,
    }


def run_qiskit_qaoa(circuit, graph, backend_name: str, opt_level: int, shots: int = 1024) -> dict:
    from scipy.optimize import minimize
    from circuits.qaoa import bind_qaoa

    n_qubits = graph.number_of_nodes()

    if backend_name == "ideal_simulator":
        simulator = get_ideal_simulator()
        execute_backend = simulator
        transpile_backend = simulator
    else:
        fake_be = get_fake_backend(backend_name)
        execute_backend = get_noisy_simulator(fake_be)
        transpile_backend = fake_be

    def objective(params):
        p = len(params) // 2
        bound = bind_qaoa(circuit, params[:p].tolist(), params[p:].tolist())
        tr = transpile_circuit(bound, transpile_backend, opt_level)
        job = execute_backend.run(tr, shots=shots)
        res = job.result()
        c = counts_from_qiskit(res)
        return -approximation_ratio(c, graph)

    x0 = np.random.default_rng(0).uniform(0, np.pi, 2)
    t0 = time.perf_counter()
    opt_result = minimize(objective, x0, method="COBYLA", options={"maxiter": 30, "rhobeg": 0.5})
    total_time = time.perf_counter() - t0

    best_params = opt_result.x
    p = len(best_params) // 2
    bound = bind_qaoa(circuit, best_params[:p].tolist(), best_params[p:].tolist())

    t0 = time.perf_counter()
    transpiled = transpile_circuit(bound, transpile_backend, opt_level)
    transpile_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    job = execute_backend.run(transpiled, shots=shots)
    result = job.result()
    runtime = time.perf_counter() - t0

    counts = counts_from_qiskit(result)
    metrics = circuit_metrics(transpiled)
    quality = approximation_ratio(counts, graph)

    return {
        "workload": "qaoa_maxcut",
        "n_qubits": n_qubits,
        "backend": backend_name,
        "opt_level": opt_level,
        "shots": shots,
        "transpile_time_s": transpile_time,
        "runtime_s": runtime + total_time,
        "depth": metrics["depth"],
        "gate_count": metrics["gate_count"],
        "two_qubit_gate_count": metrics["two_qubit_gate_count"],
        "quality_score": quality,
        "counts": counts,
    }
