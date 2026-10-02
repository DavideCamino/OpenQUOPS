### 1. Package name and supported environment

 - The document uses OpenQOPS and OpenQUOPS. Which name should be used, and what should the Python import name be?
 - What minimum Python version should be supported?
 - Should solver dependencies be optional—for example, allowing users to install the core library without Qiskit or D-Wave?

 ### 2. Input validation and variable names

 - Are variable names required, or should the library generate names such as x0, x1, … when omitted?
 - For names without a dot, should the entire name be preserved?
 - Should ancillary variables be detected by $ before or after removing the prefix? For example, should aux$.x be considered ancillary?
 - Are names count and energy forbidden because they conflict with the result columns?
 - Must matrices be dense NumPy arrays, or should sparse matrices also be supported?
 - Should any nonzero entry below the diagonal cause an error, or should tiny floating-point values be tolerated?
 - For .npz input, is a missing offset interpreted as zero? Should a file containing both qubo and quso be rejected?

 I would also validate that coefficients are finite real numbers and that the number of variable names matches the matrix dimension.

 ### 3. QUBO/QUSO conversion

 - Do you need only QUBO → QUSO, or conversion in both directions?
 - Which variable mapping should be used: x = (1-s)/2 or x = (s+1)/2? Both work, but they produce different spin labels.
 - Should conversion return a new problem or modify the existing one?

 Your Hamiltonian definition explicitly treats the QUSO diagonal as linear terms, not sᵢ². I would preserve that convention throughout.

 ### 4. Result semantics

 - If a solver internally converts a problem, should returned assignments always use the original input domain—binary for QUBO and spins for QUSO?
 - Should results include every sampled assignment, or only assignments having the best energy? For brute force specifically, should it return every configuration, all
   optimal configurations, or just one optimum?
 - When ancillary variables are removed, should their columns be omitted entirely? Would you also like an option to retain the full assignments?
 - For brute force, should count=1 apply before grouping, so a grouped row may have a count greater than one?
 - Should rows be sorted by increasing energy?
 - What should happen if all variables are ancillary? One row with the total count and minimum energy would follow your grouping rule.

 A consequence of the specified grouping rule: a row’s energy is the minimum across its hidden ancillary assignments, not necessarily the energy of every sample counted in
 that row. Is that intended?

 ### 5. Solver behavior and options

 - Should every solver accept both QUBO and QUSO, converting internally when necessary?
 - For simulated annealing, which settings should be exposed initially—for example, number of reads, sweeps, temperature schedule, and random seed?
 - Should brute force have a configurable size limit to prevent accidental exponential runs?
 - Do you have preferred solver names? Otherwise, I would use implementation-specific names rather than generic names such as QAOA or SimulatedAnnealing.

 ### 6. QAOA specification

 This is the largest area where implementation choices are still open:

 - Should both variants use standard QAOA with an initial |+⟩ state, an X mixer, and configurable depth p?
 - Should optimization minimize expected energy, or another objective such as CVaR?
 - On Aer, should objective evaluations use exact statevector expectations, finite-shot estimates, or support both?
 - How should initial parameters be generated, and should users be able to supply them?
 - What defaults do you want for depth, shots, optimization budget, and restart count?
 - Should independent restarts run sequentially or optionally in parallel?
 - Should the final dataframe come from a fresh sampling run using the best parameters, rather than pooling samples collected during optimization?
 - How should the basic QAOA solver differ from the advanced one? Could it be a convenience wrapper around the same implementation with fixed choices and no restarts?

 ### 7. Real quantum backends

 - Does “real quantum backend” specifically mean IBM Quantum through Qiskit Runtime, or should other providers be supported?
 - Should users pass an already configured backend/service object, leaving credentials outside the library?
 - Are hardware features such as error mitigation needed initially?
 - Should hardware execution be blocking only, or do you need job submission and later result retrieval?

 ### 8. Extensibility, metadata, and deliverables

 - Should users add solvers simply by implementing an interface and passing an instance, or do you also want registration and lookup by name?
 - Should execution time include preprocessing, compilation, optimization, and hardware queue time, or should these be reported separately?
 - Beyond solver name and time, do you need standardized metadata such as configuration, seed, best parameters, optimization history, and backend/job identifiers?
 - Should the initial deliverable include tests, examples, packaging, and user documentation?
 - Is this a new API, or is there existing code/API compatibility to preserve?

 You do not need to decide every default yourself—where you have no preference, you can say “choose sensible defaults.” The most important decisions are the conversion
 convention, result semantics, QAOA behavior, and intended hardware provider.