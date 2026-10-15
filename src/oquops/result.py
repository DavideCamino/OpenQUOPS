from .problem import ProblemType

import pandas as pd
import numpy as np
from typing import Any

class SolverResult:
    """Store sampled assignments, execution time, solver name, and metadata."""

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
        """Initialize a solver result.

        Args:
            dataframe: Assignments with variable columns and num_occurrences.
            execution_time: Solver runtime in seconds.
            solver: Solver name.
            metadata: Optional solver-specific details; defaults to an empty dict.
        """
        self.dataframe = dataframe
        self.execution_time = execution_time
        self.solver = solver
        if metadata is not None:
            self.metadata = metadata
        else:
            self.metadata = {}
        



