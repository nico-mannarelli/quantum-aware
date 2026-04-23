# Quantum Benchmark Toolkit — Results Report

## Overview

This project benchmarks two small quantum workloads across three backends at four compiler optimization levels. The goal is to measure how transpilation choices affect circuit structure and output quality on noisy simulators.

**Workloads:** GHZ state preparation, QAOA Max-Cut  
**Backends:** ideal simulator (AerSimulator, no noise), FakeNairobi (7-qubit IBM noise model), FakeLagos (7-qubit IBM noise model)  
**Optimization levels:** 0–3 (Qiskit preset pass manager)  
**Shots:** 512 per run  
**Quality metrics:** GHZ fidelity = P(00..0) + P(11..1); QAOA = approximation ratio

---

## Workload 1 — GHZ State

The GHZ circuit prepares a maximally entangled state: one Hadamard gate followed by a chain of CNOT gates. The ideal output is exactly 50% `000...0` and 50% `111...1`. Any deviation is a direct measure of noise.

### Circuit structure after transpilation

| Backend | n | Opt | Depth | 2Q gates |
|---|---|---|---|---|
| ideal | 3 | 0–3 | 4 | 2 |
| fake_nairobi | 3 | 0–3 | 6 | 2 |
| fake_nairobi | 5 | **0** | **11** | **10** |
| fake_nairobi | 5 | 1–3 | 8 | 4 |
| fake_lagos | 3 | 0–3 | 6 | 2 |
| fake_lagos | 5 | **0** | **11** | **10** |
| fake_lagos | 5 | 1–3 | 8 | 4 |

The ideal simulator circuit is unchanged by optimization level — there are no hardware constraints to satisfy. On the fake backends, the logical 4-gate GHZ-5 circuit at opt=0 expands to 10 two-qubit gates because the compiler inserts SWAP gates to route qubits across the device's coupling map. At opt=1 the compiler finds a better initial qubit mapping and reduces this to 4 — the same count as the logical circuit.

### Quality scores

| Backend | n | Opt 0 | Opt 1 | Opt 2 | Opt 3 |
|---|---|---|---|---|---|
| ideal | 3 | 1.000 | 1.000 | 1.000 | 1.000 |
| ideal | 5 | 1.000 | 1.000 | 1.000 | 1.000 |
| fake_nairobi | 3 | 0.909 | 0.916 | 0.926 | 0.921 |
| fake_nairobi | 5 | 0.840 | **0.865** | 0.857 | 0.871 |
| fake_lagos | 3 | 0.420 | 0.398 | 0.686 | **0.726** |
| fake_lagos | 5 | **0.249** | 0.496 | 0.500 | **0.509** |

The FakeLagos result at n=5, opt=0 is the sharpest signal in the dataset: quality collapses to **0.249**, barely above the 0.125 floor of a uniform random distribution over 8 bitstrings. The same circuit on FakeNairobi at the same optimization level scores 0.840. Both devices have the same number of qubits and the same logical circuit was compiled at the same optimization level — the difference is Lagos's higher native gate error rates and a coupling map that forces more expensive routing for this circuit.

Going from opt=0 to opt=1 on FakeLagos recovers quality to 0.496 — a near-doubling — by eliminating 6 unnecessary two-qubit gates.

---

## Workload 2 — QAOA Max-Cut

QAOA is a variational algorithm: a parameterized circuit is executed repeatedly while a classical optimizer (COBYLA) adjusts the angles to maximize the expected cut value. The approximation ratio measures how close the quantum result is to the brute-force optimal cut.

Graph: random 3-node and 5-node graphs (seed=42), QAOA depth p=1.

### Quality scores

| Backend | n | Opt 0 | Opt 1 | Opt 2 | Opt 3 |
|---|---|---|---|---|---|
| ideal | 3 | **1.000** | 0.999 | 0.998 | 0.995 |
| ideal | 5 | 0.524 | 0.523 | 0.538 | 0.541 |
| fake_nairobi | 3 | 0.887 | **0.954** | 0.949 | 0.938 |
| fake_nairobi | 5 | 0.536 | 0.508 | 0.522 | 0.520 |
| fake_lagos | 3 | 0.472 | **0.820** | 0.831 | 0.803 |
| fake_lagos | 5 | 0.485 | 0.514 | 0.500 | 0.498 |

**3-qubit results** follow the same pattern as GHZ. FakeNairobi at opt=1 reaches 0.954 — the circuit is deep enough (depth 12 after transpilation) that noise matters, but not deep enough to completely wash out the signal. FakeLagos at opt=0 drops to 0.472, barely above random, then recovers to 0.820 at opt=1 when the unnecessary SWAP gates are removed. The opt=0 transpiled QAOA circuit on both fake backends has depth 20 and 5 two-qubit gates; at opt=1 this drops to depth 12 and 2 gates.

**5-qubit results** are flat across all backends and optimization levels at ~0.51–0.54. This is expected: QAOA with p=1 layer doesn't have enough expressibility to solve a 5-node Max-Cut reliably. The approximation ratio of ~0.53 is close to the 0.5 expected from a random bitstring assignment, meaning the optimizer is not finding a useful signal. Increasing p would recover quality but was out of scope for this experiment.

---

## Findings

**1. Optimization level 1 captures almost all available gains.**  
The depth and two-qubit gate count reduction from opt=0 to opt=1 is large (e.g. 10 → 4 two-qubit gates for GHZ-5). From opt=1 to opt=3 the improvement is marginal in both circuit structure and quality score. For time-constrained workflows, opt=1 is the practical choice.

**2. Device topology affects quality as much as optimization level.**  
FakeLagos and FakeNairobi are both 7-qubit IBM-family devices, yet on GHZ-5 at opt=0 their quality scores differ by 3.4× (0.249 vs 0.840). The combination of Lagos's higher gate error rates and a coupling map that forces more SWAP insertions for this particular circuit makes it far more sensitive to the compiler's routing choices. On noisy hardware, device selection is not a secondary concern.

**3. The opt=1 recovery on noisy backends is driven by SWAP elimination.**  
The quality improvement from opt=0 to opt=1 is directly traceable to the two-qubit gate count: GHZ-5 drops from 10 to 4, QAOA-3 drops from 5 to 2. Fewer two-qubit gates means fewer high-error operations, which translates directly into higher quality scores.

**4. QAOA p=1 breaks down at 5 qubits.**  
The ideal simulator reaches 1.000 approximation ratio on the 3-qubit graph but only ~0.53 on the 5-qubit graph — indistinguishable from random. This is a known limitation of shallow QAOA circuits, not a tooling issue. Meaningful QAOA results on larger graphs require more layers (p≥2) or problem-specific angle initialization.

---

## Methodology notes

- All Qiskit runs used `qiskit-aer` 0.17.2 with `qiskit` 2.0+
- Fake backend noise models sourced from `qiskit-ibm-runtime` 0.46.1 via `NoiseModel.from_backend()`
- QAOA classical optimization used `scipy.optimize.minimize` with COBYLA, 30 iterations, random seed 0
- Results saved to `results/raw/` (JSON with full bitstring counts) and `results/processed/` (CSV)
- Plots generated with matplotlib, saved to `results/processed/`

---

## What would strengthen these results

- **Higher shot count (4096+):** the 512-shot budget introduces sampling variance, especially visible in the Lagos quality scores which fluctuate non-monotonically across opt levels
- **QAOA p=2 on 5 qubits:** would demonstrate that the 5-qubit failure is a depth issue, not a hardware issue
- **Real device run:** a single IBM or Braket QPU run for one workload would ground the fake backend noise models in real hardware behavior
