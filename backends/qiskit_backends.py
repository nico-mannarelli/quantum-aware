from __future__ import annotations
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager


FAKE_BACKEND_MAP = {
    "fake_nairobi": "FakeNairobiV2",
    "fake_lagos": "FakeLagosV2",
    "fake_manila": "FakeManilaV2",
}


def get_ideal_simulator() -> AerSimulator:
    return AerSimulator()


def get_fake_backend(name: str):
    from qiskit_ibm_runtime.fake_provider import FakeNairobiV2, FakeLagosV2, FakeManilaV2
    backends = {
        "fake_nairobi": FakeNairobiV2,
        "fake_lagos": FakeLagosV2,
        "fake_manila": FakeManilaV2,
    }
    if name not in backends:
        raise ValueError(f"Unknown fake backend: {name}. Available: {list(backends)}")
    return backends[name]()


def get_noisy_simulator(fake_backend) -> AerSimulator:
    noise_model = NoiseModel.from_backend(fake_backend)
    return AerSimulator(noise_model=noise_model)


def transpile_circuit(circuit, backend, optimization_level: int = 1):
    pm = generate_preset_pass_manager(
        optimization_level=optimization_level,
        backend=backend,
    )
    return pm.run(circuit)


def circuit_metrics(transpiled_circuit) -> dict:
    ops = transpiled_circuit.count_ops()
    cx_count = ops.get("cx", 0) + ops.get("ecr", 0) + ops.get("cz", 0)
    return {
        "depth": transpiled_circuit.depth(),
        "gate_count": sum(ops.values()),
        "two_qubit_gate_count": cx_count,
        "ops": dict(ops),
    }
