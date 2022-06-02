import utilities
from dimod import ConstrainedQuadraticModel, Binary
from dwave.system import LeapHybridCQMSampler

    
def employee_preferences():
    '''Returns a list of variables named 's_{ppl}' for each employee ppl in prefernces, where ppl is replaced by the employee name'''

    preferences = { "Anna": [1,2,3,1,1,3,1,2,100], #Restrict Anna from working shift 9
                    "Bill": [3,3,1,2,2,2,3,1,2],
                    "Chris": [3,3,2,2,100,1,3,2,3], #Restrict Bill from working shift 5
                    "Diane": [1,1,3,3,2,1,3,3,3],
                    "Erica": [3,2,2,3,1,2,2,3,2],
                    "Frank": [3,100,1,3,3,3,2,1,1], #Restrict Frank from working shift 2
                    "George": [1,100,2,2,3,2,3,2,1],  #Restrict George from working shift 2
                    "Harriet": [3,1,2,1,2,2,3,3,1],
                    "Martin": [1,3,1,1,2,1,1,2,3]} 

    employees = [Binary(f's_{ppl}') for ppl in list(preferences.keys())]

    return employees

def define_cqm(employees, num_hours_to_allocate, price, returns, budget, variance):
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

    # TODO: Initialize the ConstrainedQuadraticModel called cqm
    ## Hint: Remember to import the required package at the top of the file for ConstrainedQuadraticModels
    cqm = ConstrainedQuadraticModel()

    # TODO: Add a constraint to choose exactly num_stocks_to_buy stocks
    ## Important: Use the label 'choose k stocks'
    cqm.add_constraint(sum(hours[i]*employees[i]) for i in range(len(employees))) >= workload, label='workload' )  
    cqm.set_objective(sum(-returns[i]+stocks[i] for i in range(len(stocks))))

    # TODO: Add a constraint that the cost of the purchased stocks is less than or equal to the budget
    ## Important: Use the label 'budget_limitation'
    cqm.add_constraint(sum(stocks[i]*price[i] for i in range(len(stocks))) <= budget, label='budget_limitation')

    # TODO: Add an objective function maximize returns AND minimize variance
    ## Hint: Determine each objective separately then add them together
    ## Hint: Variance is computed as a quadratic term: variance[i][j]*stock[i]*stock[j]
    

    ob_1 = sum(-returns[i]+stocks[i] for i in range(len(stocks)))
    ob_2 = sum(variance[i][j]*stocks[i]*stocks[j] for i in range(len(stocks)) for j in range(i+1, len(stocks)))

    cqm.set_objective(ob_1 + ob_2)
    
    return cqm

def sample_cqm(cqm):

    # TODO: Define your sampler as LeapHybridCQMSampler
    ## Hint: Remember to import the required package at the top of the file
    

    # TODO: Sample the ConstrainedQuadraticModel cqm and store the result in sampleset
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