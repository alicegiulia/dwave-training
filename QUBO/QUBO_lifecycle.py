# Copyright 2020 D-Wave Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import defaultdict
from dimod import BinaryQuadraticModel as BQM
import networkx as nx
import dwave.embedding
from dwave.system import DWaveSampler, EmbeddingComposite

# Create Q matrix
Q = defaultdict(int)

Q[(1,1)] = -62
Q[(1,2)] = 48
Q[(1,3)] = 48
Q[(2,2)] = -57
Q[(2,3)] = 48
Q[(3,3)] = -59

print("\nQUBO:\n")
for i in range(1,4):
    row = ''
    for j in range(1,4):
        if (i,j) in Q:
            row += str(Q[(i,j)])+'\t'
        else:
            row += str(0) + '\t'
    print(row)

qubo_model = BQM.from_qubo(Q)
ising_model = qubo_model.to_ising()

# Pause for the user to hint <enter> to continue
input()
print("\nConverting QUBO to Ising ...")

print("\nIsing:\n")

for i in range(1,4):
    row = ''
    for j in range(1,4):
        if j<i:
            row += str(0) + '\t'
        elif j==i:
            row += str(ising_model[0][i]) + '\t'
        else:
            row += str(ising_model[1][(j,i)]) + '\t'
    print(row)

input()
print("\nEmbedding logical problem into physical layout ...")

# Construct logical problem graph
prob_graph = nx.Graph()
prob_graph.add_edges_from([(1,2),(2,3),(1,3)])

# Construct an embedding
embedding = {1:[1], 2:[2], 3:[3,4]}

# Map our Ising model onto the embedding
qubits = list(i for x in embedding.values() for i in x)
target = nx.cycle_graph(qubits)
th, tJ = dwave.embedding.embed_ising(ising_model[0], ising_model[1], embedding, target)

print("\nQMI (unscaled):\n")

for i in range(1,5):
    row = ''
    for j in range(1,5):
        if j==i:
            row += str(th[i]) + '\t'
        elif (i,j) in tJ:
            row += str(tJ[(i,j)]) + '\t'
        else:
            row += str(0) + '\t'
    print(row)

# J range is -1, +1
max_j = max(list(map(abs, tJ.values())))

# h range is -2, +2
max_h = max(list(map(abs, th.values()))) / 2

# Find our scale factor
scale_factor = max(max_j, max_h)

input()
print("\nScaling physical problem by", scale_factor, "...")

print("\nQMI (scaled):\n")

# Scale QMI
for i in range(1,5):
    row = ''
    for j in range(1,5):
        if j==i:
            th[i] = th[i]/scale_factor
            row += str(round(th[i], 2)) + '\t'
        elif (i,j) in tJ:
            tJ[(i,j)] = tJ[(i,j)]/scale_factor
            row += str(round(tJ[(i,j)], 2)) + '\t'
        else:
            row += str(0) + '\t'
    print(row)

input()
print("\nSending problem to QPU...")

sampler = EmbeddingComposite(DWaveSampler(solver={'qpu': True})) # Use EmbeddingComposite to work around any missing qubits
sampleset = sampler.sample_ising(th, tJ, num_reads=10, label='Training - QUBO Lifecycle')

print("\nBest QMI solution found:\n")

best_QMI_solution = sampleset.first.sample
print(best_QMI_solution)

input()
print("\nConverting QMI solution to Ising ...")

best_Ising_solution = dict(best_QMI_solution)
del best_Ising_solution[4] # Resolve a potential chain break 

print("\nBest Ising solution found:\n")
print(best_Ising_solution)

input()
print("\nConverting Ising solution to QUBO ...")

best_QUBO_solution = dict(best_Ising_solution)
for key, val in best_QUBO_solution.items():
    if val == -1:
        best_QUBO_solution[key] = 0

print("\nBest QUBO solution found:\n")
print(best_QUBO_solution)
