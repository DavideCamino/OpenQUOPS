from .problem import ProblemType

import pandas as pd
import numpy as np
from typing import Any

"""
TO DO:

- input validation

"""

class SolverResult:
    """
        Class that: 
            - store the solution of a quadratic problem. The solution is:
                - dataframe: one column for each variable one column for the num_occurrences
                  one row for each assignement sampled in the last cell the times
                  that the assignement is observed;
                - execution_time
                - solver name
                - metadata: solver specific information, saved as dictionary.
            - save the solution on a file
            - retun one or all assignement as np.ndarray
    """

    problem_type: ProblemType
    dataframe: pd.DataFrame
    execution_time: float
    solver: str
    metadata: dict[str, Any]

    def __init__(
            self,
            dataframe: pd.DataFrame,
            execution_time: float,
            solver: str,
            metadata: dict[str, Any] | None = None
            ) -> None:
        self.dataframe = dataframe
        self.execution_time = execution_time
        self.solver = solver
        if metadata is not None:
            self.metadata = metadata
        else:
            self.metadata = {}
        



