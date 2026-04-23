from __future__ import annotations
import numpy as np
import networkx as nx
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector


def build_maxcut_graph(n_nodes: int, seed: int = 42) -> nx.Graph:
    rng = np.random.default_rng(seed)
    G = nx.Graph()
    G.add_nodes_from(range(n_nodes))
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if rng.random() < 0.6:
                G.add_edge(i, j, weight=1.0)
    return G


def build_qaoa(graph: nx.Graph, p: int = 1) -> QuantumCircuit:
    n = graph.number_of_nodes()
    gamma = ParameterVector("γ", p)
    beta = ParameterVector("β", p)

    qc = QuantumCircuit(n, n)
    qc.h(range(n))

    for layer in range(p):
        for u, v in graph.edges():
            qc.cx(u, v)
            qc.rz(2 * gamma[layer], v)
            qc.cx(u, v)
        for i in range(n):
            qc.rx(2 * beta[layer], i)

    qc.measure(range(n), range(n))
    return qc


def bind_qaoa(qc: QuantumCircuit, gamma_vals: list[float], beta_vals: list[float]) -> QuantumCircuit:
    import re
    param_map = {}
    for g in qc.parameters:
        name = g.name
        idx_match = re.search(r"\[(\d+)\]", name)
        idx = int(idx_match.group(1)) if idx_match else 0
        if name.startswith("γ"):
            param_map[g] = gamma_vals[idx]
        elif name.startswith("β"):
            param_map[g] = beta_vals[idx]
    return qc.assign_parameters(param_map)


def maxcut_energy(bitstring: str, graph: nx.Graph) -> float:
    cut = 0
    for u, v in graph.edges():
        if bitstring[u] != bitstring[v]:
            cut += graph[u][v].get("weight", 1.0)
    return cut


def approximation_ratio(counts: dict[str, int], graph: nx.Graph) -> float:
    max_cut = _brute_force_max_cut(graph)
    if max_cut == 0:
        return 0.0
    total_shots = sum(counts.values())
    expected_cut = sum(
        (shots / total_shots) * maxcut_energy(bits, graph)
        for bits, shots in counts.items()
    )
    return expected_cut / max_cut


def _brute_force_max_cut(graph: nx.Graph) -> float:
    n = graph.number_of_nodes()
    best = 0.0
    for mask in range(1 << n):
        bits = format(mask, f"0{n}b")
        best = max(best, maxcut_energy(bits, graph))
    return best
