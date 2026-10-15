"""Common solver interface."""

from abc import ABC, abstractmethod

from ..problem import QuadraticProblem
from ..result import SolverResult


class Solver(ABC):
    @abstractmethod
    def solve(self, problem: QuadraticProblem) -> SolverResult:
        """Solve or sample a quadratic problem."""