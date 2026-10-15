from .exception import ProblemValidationError

import qubovert
from enum import Enum
import numpy as np


class ProblemType(str, Enum):
    QUBO = "qubo"
    QUSO = "quso"

class QuadraticProblem:
    """
        Class that: 
            - store a quadratic problem
            - allows to define or load a problem
            - save a problem to file
            - convert from QUBO to QUSO and viceversa
    """

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

        self.matrix = matrix
        self.symbols = symbols
        self.problem_type = problem_type
        self.offset = offset

    def evaluate(self, assignement: np.ndarray) -> float:
        energy = self.offset
        for i in range(len(self.matrix)):
            energy += self.matrix[i][i] * assignement[i]
            for j in range(i+1, len(self.matrix)):
                energy +=  self.matrix[i][j] * assignement[i] * assignement[j]
        return energy

    def to_qubovert_quso(self) -> qubovert.QUSO:
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
        p_qubovert = self.to_qubovert_quso().to_quso()
        matrix = np.zeros((len(self.symbols), len(self.symbols)))

        for i, value in p_qubovert.h.items():
            matrix[i][i] = value
        for (i,j), value in p_qubovert.J.items():
            matrix[i][j] = value
        offset = p_qubovert.offset

        return QuadraticProblem(matrix, self.symbols, ProblemType.QUSO, offset)

    def to_qubo(self) -> QuadraticProblem:
            p_qubovert = self.to_qubovert_qubo().to_qubo()
            matrix = np.zeros((len(self.symbols), len(self.symbols)))
    
            for (i,j), value in p_qubovert.Q.items():
                matrix[i][j] = value
            offset = p_qubovert.offset
    
            return QuadraticProblem(matrix, self.symbols, ProblemType.QUBO, offset)
        
