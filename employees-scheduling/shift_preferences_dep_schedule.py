from dimod import DiscreteQuadraticModel
from dwave.system import LeapHybridDQMSampler, LeapHybridCQMSampler
from dimod import ConstrainedQuadraticModel, Binary

# Set the solver we're going to use
def set_sampler():
    '''Returns a dimod sampler'''

    sampler = LeapHybridDQMSampler()

    return sampler

# Set employees and preferences
def employee_preferences():
    '''Returns a dictionary of employees with their preferences on shifts'''

    preferences = { "Anna": [1,2,3,1,1,3,1,2,100], #Anna cannot work shift 9
                    "Bill": [3,3,1,2,2,2,3,1,2],
                    "Chris": [3,3,2,2,100,1,3,2,3], #Chris cannot work shift 5
                    "Diane": [1,1,3,3,2,1,3,3,3],
                    "Erica": [3,2,2,3,1,2,2,3,2],
                    "Frank": [3,100,1,3,3,3,2,1,1], #Frank cannot work shift 2
                    "George": [1,100,2,2,3,2,3,2,1],  #George cannot work shift 2
                    "Harriet": [3,1,2,1,2,2,3,3,1],
                    "Martin": [1,3,1,1,2,1,1,2,3],
                    "Lulu": [1,3,2,2,2,2,2,2,2],
                    "Paolo": [1,2,1,2,3,3,1,3,3],
                    "Adele": [1,1,3,2,1,1,3,3,1],
                    "Gab": [100, 100, 100, 100, 100, 100, 100, 100, 100]} #Gab is in vacation for 3 days

    return preferences

def departments_var(departments):
    """Define the variables to be used for the CQM.
    Args:
        departments (list): List of departments under consideration
    
    Returns:
        department (list): 
            List of variables named '{dep}' for each department dep in departments, where dep is replaced by the department code.
    """
    department = [Binary(f'{dep}') for dep in departments]

    return department

def employee_department_preferences():

    '''Returns a dictionary of employees with their preferences on departments.
    Here kitchen [0], lighting [1], restaurant [2]'''
    
    preferences_department = { "Anna": [1,2,3], 
                                "Bill": [3,3,1],
                                "Chris": [3,2,3], 
                                "Diane": [1,1,3],
                                "Erica": [3,2,2],
                                "Frank": [3,1,100], #Frank cannot work in the Restaurant department
                                "George": [1,2,3],  
                                "Harriet": [3,1,2],
                                "Martin": [1,3,1],
                                "Lulu": [3,3,3],
                                "Paolo": [2,1,3],
                                "Adele": [3,1,1],
                                "Gab": [1, 1, 1]}

    return preferences_department

# Create DQM object
def build_dqm(preferences, num_pref):
    '''Builds the DQM for our problem'''

    # preferences = employee_preferences()
    # num_shifts = 9


    # Initialize the DQM object
    dqm = DiscreteQuadraticModel()

    # Build the DQM starting by adding variables
    for name in preferences:
        dqm.add_variable(num_pref, label=name) #(number of cases per variable, label of the variable)

    # Use linear weights to assign employee preferences
    for name in preferences:
        dqm.set_linear(name, preferences[name])


    # Set some quadratic biases to reflect the restrictions
    # for i in range(num_shifts):
        # dqm.set_quadratic_case("Bill", i, "Frank", i, 100)  #Frank cannot work in the Restaurant department
        # dqm.set_quadratic_case("Erica", i, "Bill", i, -100) #Erica and Bill would like to work in the Lighting department.

    people = list(preferences.keys())

    # Set some linear and quadratic biases so that each shift gets exactly two people scheduled.
    # Think of your discrete variables/cases as individual binary variables.  
    #For example, if variable Erik has cases 1, 2, 3, and 4, this is equivalent to four binary variables: Erik/Shift 1, Erik/Shift 2, Erik/Shift 3, and Erik/Shift 4.

    # Set the constraint: x + y >= 1 (penalty function: -x -y + xy) so that each shift gets equal or more than two people scheduled
    for i in range(num_pref):
        for j in range(len(people)):
            dqm.set_linear_case(people[j], i, -1)
            for z in range(j+1, len(people)):
                dqm.set_linear_case(people[z], i,  -1)
                dqm.set_quadratic_case(people[j], i, people[z], i,  1)

   
    return dqm


# Solve the problem
def solve_problem(dqm, sampler):
    '''Runs the provided dqm object on the designated sampler'''

    # Initialize the DQM solver
    sampler = set_sampler()

    # Solve the problem using the DQM solver
    sampleset = sampler.sample_dqm(dqm, label='Training - Employee Scheduling')

    return sampleset

# Process solution
def process_sampleset(sampleset, num_pref):
    '''Processes the best solution found for displaying'''
   
    # Get the first solution
    sample = sampleset.first.sample

    shift_schedule=[ [] for i in range(num_pref)]

    # Interpret according to shifts
    for key, val in sample.items():
        shift_schedule[val].append(key)

    return shift_schedule

# DEPARTMENT PREFERENCES    

def define_cqm(dqm_1, dqm_2):

    cqm = ConstrainedQuadraticModel()
    
    cqm.set_objective(dqm_2)

    return cqm

def sample_cqm(cqm):

    sampler = LeapHybridCQMSampler()
    sampleset_cqm = sampler.sample_cqm(cqm, time_limit=5, label = 'CQM problem')


    return sampleset_cqm

def process_sampleset_cqm(sampleset_cqm, num_pref):
    '''Processes the best solution found for displaying'''

    # Get the first solution
    sample = sampleset_cqm.first.sample

    dep_schedule=[ [] for i in range(num_pref)]

    # Interpret according to shifts
    for key, val in sample.items():
        dep_schedule[val].append(key)

    return dep_schedule


## ------- Main program -------
if __name__ == "__main__":

    # Problem information
    shifts = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    num_shifts = len(shifts)
    preferences_shift = employee_preferences()
    
    departments = ['Kitchen', 'Lighting', 'Restaurant']
    num_dep = len(departments)
    preferences_department = employee_department_preferences()

    #dqm shift preferences
    # dqm_shift = build_dqm(preferences_shift, num_shifts)

    # sampler_shift = set_sampler()

    # sampleset_shift = solve_problem(dqm_shift, sampler_shift)

    # shift_schedule = process_sampleset(sampleset_shift, num_shifts)

    # preferences = {}
    
    # for j in range(num_shifts):
    #     # for name in shift_schedule[j]:
    #         # preferences[name] = preferences_department[name]

    #     dqm_dep = build_dqm(preferences_department, num_dep)

    #     sampler_dep = set_sampler()

    #     sampleset_dep = solve_problem(dqm_dep, sampler_dep)

    #     dep_schedule = process_sampleset(sampleset_dep, num_dep)

    #     print("Shift:", shifts[j],  "\tEmployee(s): ", shift_schedule[j])
        
    #     for i in range(num_dep):
    #         print("Department:", departments[i], "\tEmployee(s): ", dep_schedule[i])
   

    # #dqm department preferences
    dqm_dep = build_dqm(preferences_department, num_dep)

    sampler_dep = set_sampler()

    sampleset_dep = solve_problem(dqm_dep, sampler_dep)

    dep_schedule = process_sampleset(sampleset_dep, num_dep)

    preferences = {}

    for j in range(num_dep):
        # for name in dep_schedule[j]:
        #     preferences[name] = preferences_shift[name]
        
        dqm_shift = build_dqm(preferences_shift, num_shifts)

        sampler_shift = set_sampler()

        sampleset_shift = solve_problem(dqm_shift, sampler_shift)

        shift_schedule = process_sampleset(sampleset_shift, num_shifts)

        print("Department:", departments[j], "\tEmployee(s): ", dep_schedule[j])
        
        for i in range(num_shifts):
            print("Shift:", shifts[i], "\tEmployee(s): ", shift_schedule[i])


    # combine preferences
    # cqm = define_cqm(dqm_shift, dqm_dep)

    # sampleset_cqm = sample_cqm(cqm)

    # dep_schedule = process_sampleset_cqm(sampleset_cqm, num_shifts)

    # for i in range(num_dep):
    #     print("Department:", departments[i], "\tEmployee(s): ", dep_schedule[i])
    #     for j in range(num_shifts):
    #         print("Shift:", shifts[j], "\tEmployee(s): ", shift_schedule[j])
