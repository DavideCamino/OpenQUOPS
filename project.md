# OpenQOPS

OpenQUOPS (Open Quadratic Unconstained Optimization Problem Solvers) is a library to define and solve QUBO and QUSO problem.

The base idea is that library is a collection of solvers that can be easly expanded. The modulariti is the core of the library.

From now on to refer to a generic problem without specifiing QUBO or QUSO I use QP (Quadratic Problem)

## Input
There are two ways to define a problem:
- defining the matrix that represent the Hamiltonian, the type of the problem (qubo or quso) the name of the variables and an optional energy offset
- loading a .npz file this file have the fields
    - qubo/quso that specify the matrix of the QP (and the name of the field specify also the type of the problem)
    - syms that specify the names of variables
    - offset for the energy offset
    - other fields (if present) are ignored

### Variables names
The problem can have ancillary variables, they can be recognized by a '$' in their name. also variables can have one or more dot in the name. Only the part after the first dot is interesting (sat.a.b -> a.b). When defining or loading a problem ensure that there are no vasribles with the same name after the removal of the first part (if happen raise an appropriate excetion)

### Hamiltonian
The matrix represent the Hamiltonian of the problem. The matrix has to be square and upper triangular (ensure that and raise an exception if not). To evaluate the energy of a specyfic configuration of variables the formula is:

$$energy = \sum_{i=0}^n \sum_{j=i+1}^n A(i,j)\cdot v_i\cdot v_j + \sum_{i=0}^n A(i,i)\cdot v_i + offset$$

Where
- $v_i$  is the variable $i$, if the problem is qubo $i \in \{0, 1\}$, if the problem is quso $i \in \{-1, 1\}$
- $A(i,j)$ is the coefficient stored in the cell $(i,j)$ of the hamiltonian
- $offest$ is the offset if present

## Ouput

### Results
The result of a problem is a tuple (dataframe, metadata):
- metadata contains the name of the solver, the execution time and various info solver dependant.
- dataframe is a pandas dataframe that has a coumn for each variable, after there are other 2 columns count and energy. Each row contains one assignement, the number of time that the assignement is sampled and the energy associated to that assignement. If there are ancillary variables group all line that differ only for the ancillary variables and show only the different assignement of the non ancillary. for the last two column:
    - count is the sum of all counts that have been grouped
    - energy is the min energy among all the assignement

### Manage the problem
I need a function to pass from qubo to quso. This can be implemented using the qubovert util. The problem can be saved into an npz file that has the same structure of the one described for the input 

## Solvers
For now implement 4 example solvers 
- brutefoce that use qubovert (for this method the count in the dataframe can be fixed at 1)
- simulated annealing using dwave ocean framework
- QAOA using qiskit to define the circuit and Aer to simulate the execution.
- An advanced version of QAOA, this use Qiskit but is very modular:
    - implement a restarting mechanism for the parameter otimization: it exec the optimization n indipendent time and use only the best parameters averall
    - i can specify the backend: implement a backend that use Aer, and one that use real quantum backend
    - i can specify the optimization algoritm. for now implement one optimizer that use scipy.optimize and the constructor has as parameter the optimization method, the default is 'COBYLA'

As sad before the library can be expanded, so give to this solver a specific name so i can implement other solver that do, for example, simulate annealing in other ways

## General indication:
the software has to
- use the latest library functions and framework
- the code has to be as modular as possible, with interface and abstract method when needed
- the code as to be clean and easy to read, every constructor has to explain all of his parameters.