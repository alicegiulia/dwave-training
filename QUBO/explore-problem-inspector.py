# Copyright 2021 D-Wave Systems, Inc.
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

# ------ Import necessary packages ----
from collections import defaultdict

from dwave.system import DWaveSampler, FixedEmbeddingComposite
from minorminer import find_embedding
import networkx as nx

import matplotlib
try:
    import matplotlib.pyplot as plt
except ImportError:
    matplotlib.use("agg")
    import matplotlib.pyplot as plt

import dwave.inspector #import for visual problem inspector!

# ------- Set up our graph -------

# Create empty graph
G = nx.Graph()

# Add edges to the graph (also adds nodes)
G.add_edges_from([(1,2),(1,3),(2,4),(3,4),(3,5),(4,5)])

# ------- Set up our QUBO dictionary -------

# Initialize our Q matrix
Q = defaultdict(int)

# Update Q matrix for every edge in the graph
for i, j in G.edges:
    Q[(i,i)]+= -1
    Q[(j,j)]+= -1
    Q[(i,j)]+= 2

# ------- Run our QUBO on the QPU -------
# Set up QPU parameters
chain_strength = 0.1
num_reads = 10

# Run the QUBO on a solver with the specified topology
QPU = DWaveSampler(solver={'topology__type__eq': 'chimera'}) #here update with the topology of interest! chimera, pegasus..
embedding = find_embedding(Q, QPU.edgelist)

print("\nEmbedding found:\n", embedding)

sampler = FixedEmbeddingComposite(QPU, embedding)
response = sampler.sample_qubo(Q,
                               chain_strength=chain_strength,
                               num_reads=num_reads,
                               label='Training - Embedding')

dwave.inspector.show(response)    #here a window open with interactive problem inspector - aka visual mapping of QUBO onto topology

print("\nSampleset:")
print(response)

# ------- Print results to user -------
print("\nSolutions:")
print('-' * 60)
print('{:>15s}{:>15s}{:^15s}{:^15s}'.format('Set 0','Set 1','Energy','Cut Size'))
print('-' * 60)
for sample, E in response.data(fields=['sample','energy']):
    S0 = [k for k,v in sample.items() if v == 0]
    S1 = [k for k,v in sample.items() if v == 1]
    print('{:>15s}{:>15s}{:^15s}{:^15s}'.format(str(S0),str(S1),str(E),str(int(-1*E))))
