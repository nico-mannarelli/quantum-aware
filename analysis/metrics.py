from __future__ import annotations
import numpy as np


def ghz_fidelity(counts: dict[str, int], n_qubits: int) -> float:
    total = sum(counts.values())
    zeros = "0" * n_qubits
    ones = "1" * n_qubits
    p_zeros = counts.get(zeros, 0) / total
    p_ones = counts.get(ones, 0) / total
    return p_zeros + p_ones


def total_variation_distance(counts_a: dict[str, int], counts_b: dict[str, int]) -> float:
    all_keys = set(counts_a) | set(counts_b)
    total_a = sum(counts_a.values())
    total_b = sum(counts_b.values())
    tvd = 0.0
    for k in all_keys:
        pa = counts_a.get(k, 0) / total_a
        pb = counts_b.get(k, 0) / total_b
        tvd += abs(pa - pb)
    return tvd / 2.0


def normalize_counts(counts: dict[str, int]) -> dict[str, float]:
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}


def counts_from_qiskit(result, circuit_name: str | None = None) -> dict[str, int]:
    if circuit_name:
        return dict(result.get_counts(circuit_name))
    return dict(result.get_counts())
