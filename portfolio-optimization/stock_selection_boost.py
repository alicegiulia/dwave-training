# Copyright 2021 D-Wave Systems Inc.
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

import utilities
from dimod import ConstrainedQuadraticModel, Binary
from dwave.system import LeapHybridCQMSampler

def define_variables(stockcodes):
    """Define the variables to be used for the CQM.
    Args:
        stockcodes (list): List of stocks under consideration
    
    Returns:
        stocks (list): 
            List of variables named 's_{stk}' for each stock stk in stockcodes, where stk is replaced by the stock code.
    """
    stocks = [Binary(f's_{stk}') for stk in stockcodes]


    return stocks

def define_cqm(stocks, num_stocks_to_buy, price, returns, budget, variance):
    """Define a CQM for the exercise. 
    Requirements:
        Objectives: 
            - Maximize returns
            - Minimize variance
        Constraints:
            - Choose exactly num_stocks_to_buy stocks
            - Spend at most budget on purchase
            
    Args:
        stocks (list):
            List of variables named 's_{stk}' for each stock in stockcodes
        num_stocks_to_buy (int): Number of stocks to purchase
        price (list):
            List of current price for each stock in stocks
                where price[i] is the price for stocks[i]
        returns (list):
            List of average monthly returns for each stock in stocks
                where returns[i] is the average returns for stocks[i]
        budget (float):
            Budget for purchase
        variance (2D numpy array):
            Entry [i][j] is the variance between stocks i and j
        
    Returns:
        cqm (ConstrainedQuadraticModel)
    """

    cqm = ConstrainedQuadraticModel()
    
    cqm.add_constraint(sum(stocks) == num_stocks_to_buy, label='choose k stocks' )  
    cqm.add_constraint(sum(stocks[i]*price[i] for i in range(len(stocks))) <= budget, label='budget_limitation')
    
    cqm.set_objective(sum(-returns[i]+stocks[i] for i in range(len(stocks))))

    # Add an objective function maximize returns AND minimize variance
    ##Variance is computed as a quadratic term: variance[i][j]*stock[i]*stock[j]
    
    ob_1 = sum(-returns[i]+stocks[i] for i in range(len(stocks)))
    ob_2 = sum(variance[i][j]*stocks[i]*stocks[j] for i in range(len(stocks)) for j in range(i+1, len(stocks)))

    cqm.set_objective(ob_1 + ob_2)
    
    return cqm

def sample_cqm(cqm):

    sampler = LeapHybridCQMSampler()
    sampleset = sampler.sample_cqm(cqm, time_limit=5, label = 'CQM problem')


    return sampleset

if __name__ == '__main__':

    # 10 stocks used in this program
    stockcodes = ["T", "SFL", "PFE", "XOM", "MO", "VZ", "IBM", "TSLA", "GILD", "GE"]

    price, returns, variance = utilities.get_stock_info()

    # Number of stocks to select
    num_stocks_to_buy = 2

    # Set the budget
    budget = 40

    # Add binary variables for stocks
    stocks = define_variables(stockcodes)

    # Build CQM
    cqm = define_cqm(stocks, num_stocks_to_buy, price, returns, budget, variance)

    # Run CQM on hybrid solver
    sampleset = sample_cqm(cqm)
    
    # Process and print solution
    print("\nPart 3 solution:\n")
    utilities.process_sampleset(sampleset, stockcodes)
