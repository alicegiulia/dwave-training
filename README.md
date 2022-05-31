# Dwave-training
Collection of optimization/QUBO problems solved with D-wave hybrid quantum annealer on D-wave Leap IDE. 
Official repo at https://github.com/dwave-examples and https://github.com/dwave-training

# Workflow for hybrid solver optimization (gradient based constrained optimization w/ Ocean)
1. Formulate QUBO/BQM/DQM/CQM (Quadratic Unconstrained Binary Optimization/Binary Quadratic Model/Discrete Quadratic Model/Constrained Quadratic Model):
  - Choose a real-world problem (problem domain)
  - Translate the problem into optimization with an objective (goal: what you want to minimize) and constraints (rules: you have to follow)
  - Convert them to maths statements with binary variables
  - Convert constraints into "suitable QUBO constraints": choose the math expression for an adequate penalty function (cost function) associated with the constraint. It may be tricky, so find more here https://docs.dwavesys.com/docs/latest/handbook_reformulating.html#elementary-boolean-operations
  - Write the QUBO as: QUBO/ISING = min (objective + lagrange_param * (constraints))  //NB: in QUBO x^2 = x
  - Solve the algebra and find the resulting matrix from the values of linear and quadratic terms of the QUBO's variables
  - Write the code as matrix (QUBO)/Ocean APIs of linear and quadratic biases (DQM/CQM)

3. Establish Sampler/Solver

5. Run (sample) on sampler

7. Interpret results - Energy analysis

# Tunable hyperparameters
- Number of reads- accounts for the probabilistic nature of the solver (10, 100, 1000...)
- Lagrange- enforce that constraints are met (default: ~75% estimate value of objective):
  ¤ Hard constraints (they must be met) - bigger lagrange
  ¤ Soft constraints (they should be met) - smaller lagrange
- Chain strength - enforce that a string of qubits behave as one variable (can be visualised with dwave.inspector.show()) as every logical problem is embedded to (map onto) the topology of the QPU:
  ¤ Linear terms >> Nodes >> QUBITS 
  ¤ Quadratic terms >> Edges >> COUPLERS.
  A small chain strength can cause broken chains : the chain of qubits behaving as one logical variables (so having all same values 0s or 1s) assume mix values, breaking the constraint.
  A large chain strenght can dominate the QUBO: bad solutions as it's difficult to find a minimum.
  
// in Discrete Quadratic Modelws (dqm):
- max number of variables (default: 3000)
- max number of cases per variable (default: 10000)
- max quadratic bias (default: 3B)
- set time limit (default: [3 s, 24 h])


# Requirements
- dwave-ocean-sdk>=3.3.0 
- python_version>='3.5'
