from ..base import Solver
from ...problem import ProblemType, QuadraticProblem
from ...result import SolverResult

from dwave.samplers import SimulatedAnnealingSampler
import dimod 
from dimod import SampleSet
from dimod import Sampler
import time

class AnnealOcean(Solver):
    """Find all global optima using qubovert's exhaustive solver."""

    def __init__(self):
        super().__init__()

    def write_solution(self, sampleset: SampleSet, time: float) -> SolverResult:
        sampleset = sampleset.aggregate()
        dataframe = sampleset.to_pandas_dataframe()
        dataframe = dataframe.drop('energy', axis=1)
        result = SolverResult(dataframe=dataframe, execution_time=time, solver='simulated annealing')
        return result

    def solve(self, problem: QuadraticProblem, num_samples: int = 1024, sampler: Sampler = SimulatedAnnealingSampler()) -> SolverResult:
        start = time.time()

        if problem.problem_type == ProblemType.QUBO:
            bqm = dimod.BQM.from_qubo(problem.to_qubovert_qubo().Q, problem.to_qubovert_qubo().offset)
        else:
            bqm = dimod.BQM.from_ising(problem.to_qubovert_quso().h, problem.to_qubovert_quso().J, problem.to_qubovert_quso().offset)

        sampleset = sampler.sample(bqm=bqm, num_reads=num_samples)

        stop = time.time()

        result = self.write_solution(sampleset, stop-start)
        return result