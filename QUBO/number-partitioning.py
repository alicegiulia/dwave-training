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

## ---------------------------------------------------

#The number partitioning problem begins with a set of numbers, S.  We must split
#the set of numbers into two sets with equal sum.

from dwave.system import DWaveSampler, EmbeddingComposite

# Define your QUBO dictionary
def get_qubo(S):
    """Returns a dictionary representing a QUBO.

    Args:
        S(list of integers): represents the numbers being partitioned
    """

    Q = {}
    C = sum(S)

    for i in range(len(S)):
        for j in range(i, len(S)):
            if i == j:
                Q[(i,j)] = (-4 * C * S[i]) + (4 * S[i]**2) #based on QUBO for number partitioning problem
            else:
                Q[(i,j)] = 8 * S[i] * S[j]
        
    print(Q)

    return Q

# Choose QPU parameters in the following function
def run_on_qpu(Q, sampler):
    """Runs the QUBO problem Q on the sampler provided.

    Args:
        Q(dict): a representation of a QUBO
        sampler(dimod.Sampler): a sampler that uses the QPU
    """

    #chainstrength = 26000 # update
    numruns = 1000 # update

    sample_set = sampler.sample_qubo(Q, num_reads=numruns, label='Training - Number Partitioning') #if chainstrength not as parameter, it's optimized by the function

    #print(sample_set)

    return sample_set


## ------- Main program -------
if __name__ == "__main__":

    ## ------- Set up our list of numbers -------
    S = [25, 7, 13, 31, 42, 17, 21, 10]

    ## ------- Set up our QUBO dictionary -------

    Q = get_qubo(S)

    ## ------- Run our QUBO on the QPU -------

    sampler = EmbeddingComposite(DWaveSampler())

    sample_set = run_on_qpu(Q, sampler)

    ## ------- Return results to user -------
    for sample in sample_set:
        S1 = [S[i] for i in sample if sample[i] == 1]
        S0 = [S[i] for i in sample if sample[i] == 0]
        print("S0 Sum: ", sum(S0), "\tS1 Sum: ", sum(S1), "\t", S0)
