# OpenQUOPS

A Python library for quadratic optimization in QUBO (binary) and QUSO (spin)
form, with exhaustive search, Ocean annealing, and Qiskit Aer QAOA solvers.

## Installation

Python 3.10 or newer is required. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

The base installation includes problem conversion, result containers, and the
brute-force solver. Install optional solvers as needed:

```bash
python -m pip install '.[annealing]'  # Ocean simulated annealing
python -m pip install '.[qaoa]'       # Qiskit Aer QAOA
python -m pip install '.[all]'        # All solvers
```

For development, use an editable installation:

```bash
python -m pip install -e '.[all,dev]'
```

Optional dependencies may impose a higher minimum Python version. The QAOA
extra constrains Aer and IBM Runtime to their current minor versions because
the solver uses version-sensitive Runtime APIs.

## Example

```python
import numpy as np

from oquops import ProblemType, QuadraticProblem
from oquops.solvers.exact.bruteforce_qubovert import BruteForceSolver

problem = QuadraticProblem(
    matrix=np.array([[-1.0, 2.0], [0.0, -1.0]]),
    symbols=("x0", "x1"),
    problem_type=ProblemType.QUBO,
)
result = BruteForceSolver().solve(problem)
print(result.dataframe)
print(f"Runtime: {result.execution_time:.6f} seconds")
```

Optional solver imports (after installing their extras):

```python
from oquops.solvers.annealing.annealing_ocean import AnnealOcean
from oquops.solvers.variational.qaoa_qiskit_aer import Qiskit_Aer_QAOA
```

## Build distributions

```bash
python -m pip install '.[dev]'
python -m build
```

The wheel and source archive are written to `dist/`.

## Author

   Developed by [Davide Camino](https://github.com/DavideCamino).

## License

GNU GPL version 3; see [LICENSE](LICENSE).
