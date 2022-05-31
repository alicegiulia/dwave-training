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

## --------------

#Given three boxes with values 17, 21, and 19, the BQM program returns the pair of boxes with the
#smallest sum.

from dwave.system import DWaveSampler, EmbeddingComposite
from dimod import BinaryQuadraticModel

# Define your BQM
def get_bqm(S):
    """Returns a dictionary representing a QUBO.

    Args:
        S(list of integers): the value for each box
    """

    bqm = BinaryQuadraticModel('BINARY')

    # Add BQM construction here
    var = ['box_17', 'box_21', 'box_19']
    
    for i in range(len(S)):
        bqm.set_linear(var[i], S[i])

    bqm.add_linear_equality_constraint([(var[i], i) for i in range(len(S))], 
        lagrange_multiplier= 800, constant = -2) #NB Lagrange multiplier! tune it for better results (it weights the constraints)
    print(bqm)
    return bqm

#Choose QPU parameters in the following function
def run_on_qpu(bqm, sampler):
    """Runs the BQM on the sampler provided.

    Args:
        bqm (BinaryQuadraticModel): a BQM for the problem;
            variable names should be 'box_17', 'box_21', and 'box_19'
        sampler (dimod.Sampler): a sampler that uses the QPU
    """

    numruns = 1000 # update

    sample_set = sampler.sample(bqm, num_reads=numruns, label='Training - Choosing Boxes')

    return sample_set

## ------- Main program -------
if __name__ == "__main__":

    S = [17, 21, 19]

    bqm = get_bqm(S)

    sampler = EmbeddingComposite(DWaveSampler())

    sample_set = run_on_qpu(bqm, sampler)
    
    print("Sample_set:")
    print(sample_set)
