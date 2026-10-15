from ...problem import ProblemType, QuadraticProblem
from ...result import SolverResult
from ..base import Solver

from collections.abc import Callable, Sequence
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

import time
import pandas as pd

class Qiskit_Aer_QAOA(Solver):
    """Optimize and sample QAOA circuits using Qiskit Aer and SciPy COBYLA."""

    def __init__(self):
        """Initialize the QAOA solver."""
        super().__init__()


    def build_paulis_list(self, problem: QuadraticProblem) -> list[tuple[str, list[int], float]]:
        """Return Z/ZZ terms for problem, a spin model; omit its constant offset."""
        pauli_list = []
        for i in range(len(problem.matrix)):
            pauli_list.append(("Z", [i], problem.matrix[i][i]))
            for j in range(i+1, len(problem.matrix)):
                pauli_list.append(("ZZ", [i, j], problem.matrix[i][j]))    
        return pauli_list

    def build_cost_hamiltonian(self, problem: QuadraticProblem) -> SparsePauliOp:
        """Return the cost operator for problem, a spin model, without its offset."""
        paulis = self.build_paulis_list(problem)
        cost_hamiltonian = SparsePauliOp.from_sparse_list(paulis, len(problem.matrix))
        return cost_hamiltonian

    def build_circuit(self, cost_hamiltonian: SparsePauliOp, reps: int = 2) -> QAOAAnsatz:
        """Build a QAOA ansatz.

        Args:
            cost_hamiltonian: Operator encoding the objective.
            reps: Number of QAOA layers.
        """
        circuit = QAOAAnsatz(cost_operator=cost_hamiltonian, reps=reps)
        return circuit

    def transpile(self, backend: Any, circuit: QAOAAnsatz, seed: int | None = None) -> Any:
        """Compile a circuit with optimization level 3.

        Args:
            backend: Target execution backend.
            circuit: QAOA ansatz to compile.
            seed: Optional transpiler random seed.
        """
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
        """Estimate the objective for a parameterized circuit.

        Args:
            params: Circuit parameter values.
            ansatz: Transpiled circuit with its qubit layout.
            hamiltonian: Cost operator on virtual qubits.
            estimator: Primitive used to estimate expectation values.
        """
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
        """Run one COBYLA optimization in an estimator session.

        Args:
            backend: Execution backend.
            init_params: Starting circuit parameter values.
            candidate_circuit: Transpiled QAOA circuit.
            cost_hamiltonian: Objective operator.
            cost_func_estimator: Callback evaluating parameters, circuit, operator, and estimator.
            shots: Shots per expectation estimate.
            seed: Optional simulator random seed.
        """
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
        """Draw uniformly distributed starting parameters.

        Args:
            num_params: Number of values to generate.
            rng: Random number generator.
            lower_bound: Minimum parameter value, inclusive.
            upper_bound: Maximum parameter value, exclusive.
        """
        return rng.uniform(lower_bound, upper_bound, num_params)

    def repeated_optimization(
        self,
        backend: Any,
        candidate_circuit: Any,
        cost_hamiltonian: SparsePauliOp,
        cost_func_estimator: Callable,
        shots: int,
        num_restarts: int = 10,
        seed: int | None = None,
    ) -> OptimizeResult:

        """Optimize random starts and return the lowest-cost result.

        Args:
            backend: Execution backend.
            candidate_circuit: Transpiled QAOA circuit.
            cost_hamiltonian: Objective operator.
            cost_func_estimator: Callback evaluating parameters, circuit, operator, and estimator.
            shots: Shots per expectation estimate.
            num_restarts: Number of independent optimization runs.
            seed: Optional seed for initial parameters and simulator seeds.
        """
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
        """Sample a bound circuit and return integer outcome counts.

        Args:
            backend: Execution backend.
            optimized_circuit: Parameter-bound circuit with measurements.
            shots: Number of measurement shots.
            seed: Optional simulator random seed.
        """
        sampler = Sampler(mode=backend)
        sampler.options.default_shots = shots
        sampler.options.simulator.seed_simulator = seed


        pub = (optimized_circuit,)
        job = sampler.run([pub], shots=shots)
        counts_int = job.result()[0].data.meas.get_int_counts()

        return counts_int

    def to_spin(self, integer: int, num_bits: int) -> list[int]:
        """Decode an outcome into spins, least-significant qubit first.

        Args:
            integer: Measured outcome encoded as an integer.
            num_bits: Number of qubits in the outcome.
        """
        result = np.binary_repr(integer, width=num_bits)
        bitstring = [int(digit) for digit in result]
        bitstring.reverse()
        spins = [1 - 2*b for b in bitstring]
        return spins

    def to_bin(self, integer: int, num_bits: int) -> list[int]:
            """Decode an outcome into bits, least-significant qubit first.

            Args:
                integer: Measured outcome encoded as an integer.
                num_bits: Number of qubits in the outcome.
            """
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
        """Convert measured outcomes into assignment rows with counts.

        Args:
            problem: Model defining variable names and binary or spin values.
            counts_int: Integer outcomes mapped to occurrence counts.
        """
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
        """Package QAOA samples as a solver result.

        Args:
            problem: Model defining variable names and representation.
            solution: Integer outcomes mapped to occurrence counts.
            time: Solver runtime in seconds.
        """
        dataframe = self.to_dataframe(problem, solution)
        result = SolverResult(dataframe=dataframe, execution_time=time, solver='qaoa')
        return result

    def solve(self, problem: QuadraticProblem, level: int = 2, seed: int | None = None, sample_shots: int = 4096, estimator_shot: int = 2048, num_restart: int = 10) -> SolverResult:
        """Optimize a QAOA circuit and sample candidate assignments.

        Args:
            problem: Binary or spin model to solve.
            level: Number of QAOA layers.
            seed: Optional random seed for compilation, optimization, and sampling.
            sample_shots: Number of final measurement shots.
            estimator_shot: Shots per optimization expectation estimate.
            num_restart: Number of random-start optimization runs.
        """
        quso_problem = problem.to_quso()
        start = time.time()

        backend = qiskit_aer.AerSimulator(seed_simulator=seed)

        hamiltonian = self.build_cost_hamiltonian(quso_problem)
        circuit = self.build_circuit(hamiltonian, reps=level)
        transpiled_circuit = self.transpile(backend, circuit, seed=seed)
        best_params = self.repeated_optimization(backend, transpiled_circuit, hamiltonian, self.cost_func_estimator, estimator_shot, seed=seed, num_restarts=num_restart)
        optimized_circuit = transpiled_circuit.assign_parameters(best_params.x)
        optimized_circuit.measure_all()
        counts = self.sample(backend, optimized_circuit, seed=seed, shots=sample_shots)

        stop = time.time()

        result = self.write_solution(problem, counts, stop-start)
        return result