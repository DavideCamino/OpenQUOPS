"""Common solver interface."""

from abc import ABC, abstractmethod

from ..problem import QuadraticProblem
from ..result import SolverResult


class Solver(ABC):
    """Define the common interface for quadratic problem solvers."""

    @abstractmethod
    def solve(self, problem: QuadraticProblem) -> SolverResult:
        """Return solutions for problem, the quadratic model to solve or sample."""