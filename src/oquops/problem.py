from __future__ import annotations

import qubovert
from enum import Enum
import numpy as np


class ProblemType(str, Enum):
    """Identify binary (QUBO) or spin (QUSO) problem variables."""

    QUBO = "qubo"
    QUSO = "quso"

class QuadraticProblem:
    """Store and evaluate a quadratic problem and convert its representation."""

    matrix: np.ndarray
    symbols: tuple[str, ...]
    problem_type: ProblemType
    offset: float = 0

    def __init__(
            self,
            matrix: np.ndarray,
            symbols: tuple[str, ...],
            problem_type: ProblemType,
            offset: float = 0
        ) -> None:

        """Initialize a problem.

        Args:
            matrix: Upper-triangular coefficients; diagonal entries are linear terms.
            symbols: Variable names in matrix order.
            problem_type: Binary (QUBO) or spin (QUSO) representation.
            offset: Constant energy term.
        """
        self.matrix = matrix
        self.symbols = symbols
        self.problem_type = problem_type
        self.offset = offset

    def evaluate(self, assignement: np.ndarray) -> float:
        """Return energy for assignement, the variable values in matrix order."""
        energy = self.offset
        for i in range(len(self.matrix)):
            energy += self.matrix[i][i] * assignement[i]
            for j in range(i+1, len(self.matrix)):
                energy +=  self.matrix[i][j] * assignement[i] * assignement[j]
        return energy

    @staticmethod
    def __matrix_names_from_qubovert(q : qubovert.QUSO | qubovert.QUBO) -> tuple[np.ndarray, list[str]]:
        syms = list(np.zeros(len(q.variables)))
        matrix = np.zeros ((len(q.variables), len(q.variables)))
        for (var, id) in q.mapping.items():
            syms[id] = var
        if type(q) == qubovert.QUBO:
            qubo = q.to_qubo()
            for (i,j), value in qubo.Q.items():
                matrix[i][j] = value
        elif type(q) == qubovert.QUSO:
            quso = q.to_quso()
            for i, value in quso.h.items():
                matrix[i][i] = value
            for (i,j), value in quso.J.items():
                matrix[i][j] = value
        return (matrix, syms)

    def to_qubovert_quso(self) -> qubovert.QUSO:
        """Return an equivalent qubovert spin model, including the offset."""
        if self.problem_type == ProblemType.QUSO:
            p_qubovert = qubovert.QUSO()
        else:
            p_qubovert = qubovert.QUBO()
        for i in range(len(self.matrix)):
            p_qubovert[(self.symbols[i],)] += self.matrix[i][i]
            for j in range(i+1, len(self.matrix)):
                p_qubovert[(self.symbols[i], self.symbols[j])] += self.matrix[i][j]
        p_qubovert += self.offset
        if self.problem_type == ProblemType.QUSO:
            return p_qubovert
        else:
            return qubovert.utils.qubo_to_quso(p_qubovert)

    def to_qubovert_qubo(self) -> qubovert.QUBO:
        """Return an equivalent qubovert binary model, including the offset."""
        if self.problem_type == ProblemType.QUBO:
            p_qubovert = qubovert.QUBO()
        else:
            p_qubovert = qubovert.QUSO()
        for i in range(len(self.matrix)):
            p_qubovert[(self.symbols[i],)] += self.matrix[i][i]
            for j in range(i+1, len(self.matrix)):
                p_qubovert[(self.symbols[i], self.symbols[j])] += self.matrix[i][j]
        p_qubovert += self.offset
        if self.problem_type == ProblemType.QUBO:
            return p_qubovert
        else:
            return qubovert.utils.quso_to_qubo(p_qubovert)

    def to_quso(self) -> QuadraticProblem:
        """Return an equivalent spin problem with the same variable names."""
        p_qubovert = self.to_qubovert_quso()
        matrix, symbols = self.__matrix_names_from_qubovert(p_qubovert)
        offset = p_qubovert.offset
        return QuadraticProblem(matrix, symbols, ProblemType.QUSO, offset)

    def to_qubo(self) -> QuadraticProblem:
        """Return an equivalent binary problem with the same variable names."""
        p_qubovert = self.to_qubovert_qubo()
        matrix, symbols = self.__matrix_names_from_qubovert(p_qubovert)
        offset = p_qubovert.offset
        return QuadraticProblem(matrix, symbols, ProblemType.QUBO, offset)

    @classmethod
    def from_qubovert_qubo(cls, qubo : qubovert.QUBO) -> QuadraticProblem:
        matrix, symbols = cls.__matrix_names_from_qubovert(qubo)
        offset = qubo.offset
        return QuadraticProblem(matrix, symbols, ProblemType.QUBO, offset)

    @classmethod
    def from_qubovert_quso(cls, quso : qubovert.QUSO) -> QuadraticProblem:
        matrix, symbols = cls.__matrix_names_from_qubovert(quso)
        offset = quso.offset
        return QuadraticProblem(matrix, symbols, ProblemType.QUSO, offset)


        
