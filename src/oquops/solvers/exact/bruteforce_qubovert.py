from ...problem import ProblemType, QuadraticProblem
from ...result import SolverResult
from ..base import Solver

import qubovert
import time
import pandas as pd

class BruteForceSolver(Solver):
    """Find all global optima using qubovert's exhaustive solver."""

    def __init__(self):
        super().__init__()

    def write_solution(self, solution: list[dict], time: float) -> SolverResult:
        dataframe = pd.DataFrame(solution)
        dataframe['num_occurrences'] = 1
        result = SolverResult(dataframe=dataframe, execution_time=time, solver='qubovert bruteforce')
        return result

    def solve(self, problem: QuadraticProblem) -> SolverResult:
        start = time.time()

        if problem.problem_type == ProblemType.QUBO:
            model = problem.to_qubovert_qubo()
        else:
            model = problem.to_qubovert_quso()

        solutions = model.solve_bruteforce(all_solutions=True)

        stop = time.time()

        result = self.write_solution(solutions, stop-start)
        return result