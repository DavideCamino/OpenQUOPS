1. name
    1. OpenQUOPS is the library name, oquops is the Python import name
    2. 3.10
    3. no they are mandatory

2. input
    1. library generate names such as x0, x1, … when omitted
    2. yes
    3. before, aux$.x is ancillary
    4. yes
    5. matrices are dense NumPy arrays
    6. any nonzero entry below the diagonal cause an error
    7. a missing offset is interpreted as zero, and a file containing both qubo and quso has to be rejected

3. conversion
    1. I need conversion in both directions
    2. you have to use the qubovert function that already implement the conversion, do not implement the algorithm
    3. the conversion has to return a new problem

4. result
    1. the returned assignments always use the original input domain
    2. results include every sampled assignment, for brute force it return all
   optimal configurations and use the qubovert function, do not implement the algorithm
   3. I want an option to retain the full assignments
   4. yes
   5. rows be sorted by decreasing count
   6. if all variables are ancillary raise an error

5. solver
    1. yes
    2. all of the ones you proposed
    3. no I will take care of that
    4. use implementation-specific names

6. QAOA
    1. both variants use a configurable depth p, the modular one accept state and mixer as parameter in the constructor having |+⟩ state, and X mixer, as default
    2. optimization minimize expected energy
    3. It use the Estimator class
    4. initial parameters are random generated, the user can provide a seed.
    5. depth=2, shots=2048, optimization budget: max_iter=200 optimization_shot=1024, and restart=3
    6. sequentially
    7. fresh sampling run using the best parameters
    8. no i want 2 different classes, the firt is very simple and easy to explore, the second is the complete version

7. Real quantum backends: for now ignore this requirement. i will implement this later.

8. Extensibility, metadata, and deliverables
    1. simply by implementing an interface and passing an instance
    2. time include all steps
    3. optimization history
    4. yes
    5. new api