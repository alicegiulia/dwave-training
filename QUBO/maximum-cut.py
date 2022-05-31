# Copyright 2019 D-Wave Systems, Inc.
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

# ----------

#This problem has a wide
#variety of real-world applications.
#For example, suppose that we have a set of different computers, each with
#different types of connections.  Some computers have bluetooth, some have USB
#ports, HDMI ports, etc.  We want to split our set of computers into two groups
#for two different projects, but it's very important that the two groups can
#connect to each other.  The problem is sometimes the wires and connections don't
#work!  How can we be sure that we have the best chance at remaining connected?
#One way to solve this problem is with the maximum cut problem.  If we think of
#our set of computers as a graph (a node/vertex for each computer), and draw an
#edge between computers that can connect to each other, we have a model of our
#network.  If we look for a maximum cut in our graph, then we are looking for a
#way to split the nodes into two groups so that there are as many edges as
#possible between the groups.  In our computer set, this means that we have two
#groups with as many connections as possible between the two groups.  Now if one
#connection goes down, we have many more to use!  This way we have created a more
#resilient network by providing many redundant connections between groups in case
#one connection fails.

from collections import defaultdict

from dwave.system.samplers import DWaveSampler
from dwave.system.composites import EmbeddingComposite
import networkx as nx

import matplotlib
matplotlib.use("agg")
from matplotlib import pyplot as plt
import dwave.inspector

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
#chainstrength = 0.5
numruns = 10

# Run the QUBO on the solver from your config file
sampler = EmbeddingComposite(DWaveSampler(solver={'topology__type':'chimera'}))
response = sampler.sample_qubo(Q,
                               #chain_strength=chainstrength,
                               num_reads=numruns,
                               label='Example - Maximum Cut')
dwave.inspector.show(response)

# ------- Print results to user -------
print('-' * 60)
print('{:>15s}{:>15s}{:^15s}{:^15s}'.format('Set 0','Set 1','Energy','Cut Size'))
print('-' * 60)
for sample, E in response.data(fields=['sample','energy']):
    S0 = [k for k,v in sample.items() if v == 0]
    S1 = [k for k,v in sample.items() if v == 1]
    print('{:>15s}{:>15s}{:^15s}{:^15s}'.format(str(S0),str(S1),str(E),str(int(-1*E))))

# ------- Display results to user -------
# Grab best result
# Note: "best" result is the result with the lowest energy
# Note2: the look up table (lut) is a dictionary, where the key is the node index
#   and the value is the set label. For example, lut[5] = 1, indicates that
#   node 5 is in set 1 (S1).
lut = response.first.sample

# Interpret best result in terms of nodes and edges
S0 = [node for node in G.nodes if not lut[node]]
S1 = [node for node in G.nodes if lut[node]]
cut_edges = [(u, v) for u, v in G.edges if lut[u]!=lut[v]]
uncut_edges = [(u, v) for u, v in G.edges if lut[u]==lut[v]]

# Display best result
pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, pos, nodelist=S0, node_color='r')
nx.draw_networkx_nodes(G, pos, nodelist=S1, node_color='c')
nx.draw_networkx_edges(G, pos, edgelist=cut_edges, style='dashdot', alpha=0.5, width=3)
nx.draw_networkx_edges(G, pos, edgelist=uncut_edges, style='solid', width=3)
nx.draw_networkx_labels(G, pos)

filename = "maxcut_plot.png"
plt.savefig(filename, bbox_inches='tight')
print("\nYour plot is saved to {}".format(filename))
