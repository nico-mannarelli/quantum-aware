from __future__ import annotations
from braket.devices import LocalSimulator
from braket.circuits import Circuit as BraketCircuit
from qiskit import QuantumCircuit


def get_local_simulator() -> LocalSimulator:
    return LocalSimulator()


def qiskit_to_braket(qc: QuantumCircuit) -> BraketCircuit:
    """Convert a Qiskit circuit (no parameters, no measurements) to a Braket circuit."""
    from qiskit.qasm2 import dumps
    import re

    qasm = dumps(qc.remove_final_measurements(inplace=False))
    bc = BraketCircuit()
    n = qc.num_qubits

    gate_map = {
        "h": lambda q: bc.h(q),
        "cx": lambda c, t: bc.cnot(c, t),
        "x": lambda q: bc.x(q),
        "y": lambda q: bc.y(q),
        "z": lambda q: bc.z(q),
        "s": lambda q: bc.s(q),
        "t": lambda q: bc.t(q),
    }

    for line in qasm.splitlines():
        line = line.strip().rstrip(";")
        if not line or line.startswith("//") or line.startswith("OPENQASM") or line.startswith("include") or line.startswith("qreg") or line.startswith("creg"):
            continue
        parts = line.split()
        gate_name = parts[0].lower()
        qubits_str = " ".join(parts[1:])
        qubit_indices = [int(m) for m in re.findall(r"\[(\d+)\]", qubits_str)]

        if gate_name == "rz":
            angle_match = re.search(r"rz\(([^)]+)\)", line)
            if angle_match:
                import ast
                angle = float(ast.literal_eval(angle_match.group(1)))
                bc.rz(qubit_indices[0], angle)
        elif gate_name == "rx":
            angle_match = re.search(r"rx\(([^)]+)\)", line)
            if angle_match:
                import ast
                angle = float(ast.literal_eval(angle_match.group(1)))
                bc.rx(qubit_indices[0], angle)
        elif gate_name in gate_map:
            gate_map[gate_name](*qubit_indices)

    return bc


def run_braket_circuit(circuit: BraketCircuit, device: LocalSimulator, shots: int = 1024) -> dict:
    task = device.run(circuit, shots=shots)
    result = task.result()
    return dict(result.measurement_counts)


def braket_circuit_metrics(circuit: BraketCircuit) -> dict:
    instructions = circuit.instructions
    two_qubit = sum(1 for i in instructions if len(i.target) > 1)
    return {
        "gate_count": len(instructions),
        "two_qubit_gate_count": two_qubit,
        "depth": circuit.depth,
    }
