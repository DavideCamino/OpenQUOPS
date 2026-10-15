from ...problem import ProblemType, QuadraticProblem
from ...result import SolverResult
from ..base import Solver

from collections.abc import Callable, Mapping, Sequence
from typing import Any

import numpy as np
from scipy.optimize import OptimizeResult, minimize

from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

import qiskit_aer

from qiskit_ibm_runtime import Session
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.executor_sampler import Sampler

import qubovert
import time
import pandas as pd

class Qiskit_Aer_QAOA(Solver):
    """Find all global optima using qubovert's exhaustive solver."""

    def __init__(self):
        super().__init__()


    def build_paulis_list(self, problem: QuadraticProblem) -> list[tuple[str, list[int], float]]:
        pauli_list = []
        for i in range(len(problem.matrix)):
            pauli_list.append(("Z", [i], problem.matrix[i][i]))
            for j in range(i+1, len(problem.matrix)):
                pauli_list.append(("ZZ", [i, j], problem.matrix[i][j]))    
        return pauli_list

    def build_cost_hamiltonian(self, problem: QuadraticProblem) -> SparsePauliOp:
        paulis = self.build_paulis_list(problem)
        cost_hamiltonian = SparsePauliOp.from_sparse_list(paulis, len(problem.matrix))
        return cost_hamiltonian

    def build_circuit(self, cost_hamiltonian: SparsePauliOp, reps: int = 2) -> QAOAAnsatz:
        circuit = QAOAAnsatz(cost_operator=cost_hamiltonian, reps=reps)
        return circuit

    def transpile(self, backend: Any, circuit: QAOAAnsatz, seed: int | None = None) -> Any:
        pm = generate_preset_pass_manager(optimization_level=3, backend=backend, seed_transpiler=seed)
        candidate_circuit = pm.run(circuit)
        return candidate_circuit

    def cost_func_estimator(
        self,
        params: Sequence[float] | np.ndarray,
        ansatz: Any,
        hamiltonian: SparsePauliOp,
        estimator: Estimator,
    ) -> float:
        # transform the observable defined on virtual qubits to
        # an observable defined on all physical qubits
        isa_hamiltonian = hamiltonian.apply_layout(ansatz.layout)

        pub = (ansatz, isa_hamiltonian, params)
        job = estimator.run([pub])

        results = job.result()[0]
        cost = results.data.evs
        
        return cost

    def optimization(
        self,
        backend: Any,
        init_params: Sequence[float] | np.ndarray,
        candidate_circuit: Any,
        cost_hamiltonian: SparsePauliOp,
        cost_func_estimator: Callable[[Sequence[float] | np.ndarray, Any, SparsePauliOp, Estimator], float],
        shots: int,
        seed: int | None = None,
    ) -> OptimizeResult:
        with Session(backend=backend) as session:
            estimator = Estimator(mode=session)
            estimator.options.default_shots = shots
            estimator.options.simulator.seed_simulator = seed

            result = minimize(
                cost_func_estimator,
                init_params,
                args=(candidate_circuit, cost_hamiltonian, estimator),
                method="COBYLA",
                tol=1e-5
            )
            return result

    def generate_initial_params(
        self,
        num_params: int,
        rng: np.random.Generator,
        lower_bound: float = 0.0,
        upper_bound: float = 2 * np.pi,
    ) -> np.ndarray:
        return rng.uniform(lower_bound, upper_bound, num_params)

    def repeated_optimization(
        self,
        backend: Any,
        candidate_circuit: Any,
        cost_hamiltonian: SparsePauliOp,
        cost_func_estimator: Callable[[Sequence[float] | np.ndarray, Any, SparsePauliOp, Estimator], float],
        shots: int,
        num_restarts: int = 10,
        seed: int | None = None,
    ) -> OptimizeResult:

        rng = np.random.default_rng(seed)
        best_result: OptimizeResult | None = None

        for _ in range(num_restarts):
            init_params = self.generate_initial_params(candidate_circuit.num_parameters, rng)
            optimization_seed = None if seed is None else int(rng.integers(0, np.iinfo(np.int32).max))

            result = self.optimization(
                backend,
                init_params,
                candidate_circuit,
                cost_hamiltonian,
                cost_func_estimator,
                shots=shots,
                seed=optimization_seed,
            )

            if best_result is None or result.fun < best_result.fun:
                best_result = result

        return best_result

    def sample(
        self,
        backend: Any,
        optimized_circuit: Any,
        shots: int,
        seed: int | None = None,
    ) -> dict[int, int]:
        sampler = Sampler(mode=backend)
        sampler.options.default_shots = shots
        sampler.options.simulator.seed_simulator = seed


        pub = (optimized_circuit,)
        job = sampler.run([pub], shots=shots)
        counts_int = job.result()[0].data.meas.get_int_counts()

        return counts_int

    def to_spin(self, integer: int, num_bits: int) -> list[int]:
        result = np.binary_repr(integer, width=num_bits)
        bitstring = [int(digit) for digit in result]
        bitstring.reverse()
        spins = [1 - 2*b for b in bitstring]
        return spins

    def to_bin(self, integer: int, num_bits: int) -> list[int]:
            result = np.binary_repr(integer, width=num_bits)
            bitstring = [int(digit) for digit in result]
            bitstring.reverse()
            bins = [b for b in bitstring]
            return bins

    def to_dataframe(
        self,
        problem: QuadraticProblem,
        counts_int: dict,
    ) -> pd.DataFrame:
        data = []
        for key, value in counts_int.items():
            if problem.problem_type == ProblemType.QUBO:
                assignement = self.to_bin(key, len(problem.matrix))
            else:
                assignement = self.to_spin(key, len(problem.matrix))
            data.append(assignement + [value])

        cols = problem.symbols + ['num_occurrences']
        dataframe = pd.DataFrame(data, columns=cols)
        return dataframe

    def write_solution(self, problem: QuadraticProblem, solution: dict, time: float) -> SolverResult:
        dataframe = self.to_dataframe(problem, solution)
        result = SolverResult(dataframe=dataframe, execution_time=time, solver='qaoa')
        return result

    def solve(self, problem: QuadraticProblem, seed: int | None = None, sample_shots: int = 4096, estimator_shot: int = 2048, num_restart: int = 10) -> SolverResult:
        quso_problem = problem.to_quso()
        start = time.time()

        backend = qiskit_aer.AerSimulator(seed_simulator=seed)

        hamiltonian = self.build_cost_hamiltonian(quso_problem)
        circuit = self.build_circuit(hamiltonian)
        transpiled_circuit = self.transpile(backend, circuit, seed=seed)
        best_params = self.repeated_optimization(backend, transpiled_circuit, hamiltonian, self.cost_func_estimator, estimator_shot, seed=seed, num_restarts=num_restart)
        optimized_circuit = transpiled_circuit.assign_parameters(best_params.x)
        optimized_circuit.measure_all()
        counts = self.sample(backend, optimized_circuit, seed=seed, shots=sample_shots)

        stop = time.time()

        result = self.write_solution(problem, counts, stop-start)
        return result