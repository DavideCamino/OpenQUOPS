# Implementation overview

OpenQUOPS separates the optimization model (`QuadraticProblem`), solver logic,
and output (`SolverResult`). All solvers inherit from the abstract `Solver`
interface in `src/oquops/solvers/base.py`, which requires
`solve(problem) -> SolverResult`. Concrete solvers add their own options.
This keeps the input/output structure shared while delegating computation to
qubovert, Ocean, or Qiskit rather than reimplementing those backends.

## Problem

**File:** `src/oquops/problem.py`  
**Classes:** `ProblemType`, `QuadraticProblem`

- **Structure:** `ProblemType` distinguishes QUBO variables (`0, 1`) from QUSO
  spins (`-1, +1`). `QuadraticProblem` stores a NumPy coefficient `matrix`,
  variable names in `symbols`, a `problem_type`, and a constant `offset`.
- **What it does:** Represents a quadratic objective, evaluates assignments,
  and converts between binary and spin representations.
- **How:** The diagonal stores linear coefficients; entries above the diagonal
  store pair interactions. `evaluate()` computes
  `offset + sum(matrix[i,i] * x[i]) + sum(matrix[i,j] * x[i] * x[j], i < j)`.
  That is, with coefficient matrix $M$, constant offset $c$ and assignement $\mathbf{x}$:

  $$
  E(\mathbf{x}) = c + \sum_{i=0}^{n-1} M_{ii} x_i
  + \sum_{i=0}^{n-1} \sum_{j=i+1}^{n-1} M_{ij} x_i x_j.
  $$

  Entries below the diagonal are ignored, so interactions are counted once.
- **Implementation decision:** Conversion is delegated to qubovert.
  `to_qubovert_qubo()` and `to_qubovert_quso()` build backend models, including
  the constant offset. `to_qubo()` and `to_quso()` reconstruct a new
  `QuadraticProblem` from the converted coefficients, retaining the symbol tuple.
  The binary/spin relation is `s = 1 - 2*x`.

The constructor currently stores inputs without validating dimensions, variable
names, or assignment values; callers must provide consistent data.

## Result

**File:** `src/oquops/result.py`  
**Class:** `SolverResult`

- **Structure:** Stores a pandas `dataframe`, `execution_time` in seconds,
  a `solver` name, and optional `metadata` (an empty dictionary by default).
- **What it does:** Provides a common container for both exact solutions and
  sampled assignments.
- **How:** Solvers prepare one DataFrame row per returned assignment, with
  variable columns and a `num_occurrences` column, then pass it to the
  constructor along with timing and solver information. Results use the original
  problem's representation: spins in $\{-1,+1\}$ for QUSO and binary values in
  $\{0,1\}$ for QUBO, even if a solver converts the model internally.

  The correspondence between a binary value $x_i$ and a spin $s_i$ is:

  $$
  s_i = 1 - 2x_i, \qquad x_i = \frac{1 - s_i}{2}.
  $$

  Thus, binary **0** corresponds to spin **+1**, and binary **1** corresponds
  to spin **−1**. Converting the objective coefficients and offset consistently
  preserves the energy of corresponding assignments.
- **Implementation decision:** A DataFrame supports downstream inspection and
  analysis without exposing backend-specific result objects. The container
  itself does not calculate energies, sort solutions, or validate the data.

`problem_type` is annotated on the class but is not initialized by the
constructor. Current solvers leave `metadata` empty and exclude result-formatting
work from their reported execution time.

## Brute force

**File:** `src/oquops/solvers/exact/bruteforce_qubovert.py`  
**Class:** `BruteForceSolver`

- **Structure:** A stateless `Solver` subclass with `solve()` for computation
  and `write_solution()` for output formatting.
- **What it does:** Finds every globally optimal assignment, rather than
  returning every possible assignment.
- **How:** `solve()` converts the problem to the matching qubovert QUBO or QUSO
  model and calls `solve_bruteforce(all_solutions=True)`. `write_solution()`
  turns the optimal variable/value dictionaries into a DataFrame and assigns
  each row `num_occurrences = 1`.
- **Implementation decision:** Exhaustive search provides an exact reference
  for checking heuristic solvers, but its exponential search space restricts
  practical use to small problems. Conversion and exhaustive solving are timed;
  DataFrame construction is not.

## Annealing

**File:** `src/oquops/solvers/annealing/annealing_ocean.py`  
**Class:** `AnnealOcean`

- **Structure:** A stateless `Solver` subclass with `solve(problem,
  num_samples=1024, sampler=SimulatedAnnealingSampler())` and
  `write_solution()`.
- **What it does:** Samples low-energy assignments through an Ocean-compatible
  sampler; the default implementation uses classical simulated annealing.
- **How:** A QUBO becomes a dimod binary quadratic model through
  `BQM.from_qubo()`, while a QUSO uses `BQM.from_ising()`. Both include the
  problem offset. The sampler receives `num_reads=num_samples`.
  `write_solution()` aggregates identical samples, converts the `SampleSet`
  to a DataFrame, and removes the energy column while retaining occurrence
  counts.
- **Implementation decision:** Accepting a sampler object separates the wrapper
  from a particular sampling implementation. A replacement must support the
  supplied `bqm` and `num_reads` arguments. Sampling is heuristic and does not
  guarantee a global optimum.

## QAOA

**File:** `src/oquops/solvers/variational/qaoa_qiskit_aer.py`  
**Class:** `Qiskit_Aer_QAOA`

- **Structure:** A `Solver` subclass split into helpers for Hamiltonian and
  circuit construction, transpilation, parameter optimization, measurement,
  and result conversion. `solve()` coordinates these stages without storing
  run-specific state on the solver.
- **What it does:** Runs a hybrid quantum/classical optimization on a Qiskit
  Aer simulator, then samples candidate assignments from the optimized circuit.
  It is approximate and does not guarantee a global optimum.

### Execution flow and decisions

1. **Normalize the model:** Convert the input to QUSO so that each linear term
   maps to a Pauli `Z` and each interaction to `ZZ`. `build_paulis_list()` and
   `build_cost_hamiltonian()` construct a `SparsePauliOp`. The constant offset
   is omitted because it does not change the minimizing parameters or the
   measurement probabilities.
2. **Construct and compile:** `build_circuit()` creates a `QAOAAnsatz` with
   `reps=level`. The default is two layers. `transpile()` compiles it for the
   Aer backend with optimization level 3; this compilation setting is separate
   from the number of QAOA layers.
3. **Estimate the objective:** `cost_func_estimator()` applies the transpiled
   circuit's qubit layout to the Hamiltonian and uses an IBM Runtime
   `Estimator` to obtain its expectation value.
4. **Optimize parameters:** `optimization()` opens a backend session and calls
   SciPy's derivative-free COBYLA optimizer with tolerance `1e-5`.
   `generate_initial_params()` draws angles uniformly from `[0, 2*pi)`, and
   `repeated_optimization()` keeps the lowest-cost result across random starts.
   Multiple starts reduce dependence on one initialization, but do not establish
   global optimality.
5. **Measure:** Bind the selected parameters, add measurements, and use a
   Runtime `Sampler` to obtain integer outcome counts.
6. **Format results:** `to_bin()` reverses the bit representation to put qubit
   zero first. `to_spin()` additionally applies `s = 1 - 2*x`.
   `to_dataframe()` chooses binary or spin values according to the original
   input type, and `write_solution()` packages the counts in `SolverResult`.

### Main options

| Parameter | Purpose | Default |
| --- | --- | --- |
| `level` | Number of QAOA layers | `2` |
| `seed` | Seeds compilation, initial parameters, and simulator runs | `None` |
| `sample_shots` | Final measurement count | `4096` |
| `estimator_shot` | Shots per expectation estimate | `2048` |
| `num_restart` | Number of independent optimization runs | `10` |

The timer starts after QUSO conversion and covers backend setup through final
sampling, excluding output formatting. The optimizer's parameters and cost are
not currently retained in result metadata.

**Current limitations:** `num_restart` must be positive because the solver
requires a best optimization result. Also, `to_dataframe()` currently combines
`problem.symbols` with a list using `+`; this fails for the documented tuple
symbol type and needs a tuple/list normalization before QAOA result formatting
can work with that type. Runtime primitives are version-sensitive, which is why
the installation configuration constrains the supported Runtime minor version.
