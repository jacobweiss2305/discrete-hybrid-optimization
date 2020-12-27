# -*- coding: utf-8 -*-
"""
Metal-working shop example from Applied Mathematical Programming, by Bradley et al. 
This is the primal formulation.  

Requirements: 
 - CPLEX (or other Pyomo-compatible solver)
"""
# Import 
from pyomo.environ import *
from pyomo.opt import *
from pyomo.core import * 
import cplex

def objective_rule(model):
    # Create objective function
    return sum(model.profit[i] * model.SELECT[i] for i in model.i)

def budget_rule(model,j):
    # Constraint on available budget 
    return sum(model.used[j,i] * model.SELECT[i] for i in model.i) <= model.budget[j]

def SolveUsingPyomo():
    ''' Create and solve a concrete Pyomo model '''

    # Initialize data structures with hard-coded data from example
    numTrailers = 3 # Number of types of trailers
    numResources = 2 # Number of types of resources
    profit = {1:6, 2:14, 3:13} # Dict of trailer profit values (the c vector: coefficients in objective function)
    used = {(1,1):0.5, (1,2):2, (1,3):1, (2,1):1, (2,2):2, (2,3):4} # Amount of resource j used by trailer i (the A matrix)
    budget = {1:24, 2:60} # Dict of resource budget values (the b vector: right-hand-side coefficients)

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and set...")
    model.i = Set(initialize=[i for i in range(1, numTrailers+1)], ordered=True) # Index on each type of trailer
    model.j = Set(initialize=[j for j in range(1, numResources+1)], ordered=True) # Index on each type of resource
    
    # Define variables
    print("Creating variables...")
    model.SELECT = Var(model.i, domain=NonNegativeReals, initialize = 0) # Indicates if number (actually, amount) of trailer i selected
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.profit = Param(model.i, initialize = profit)
    model.used = Param((model.j * model.i), initialize = used)
    model.budget = Param(model.j, initialize = budget)

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = maximize)

    print("Creating constraints on available resource budgets...")
    model.budgetConstraint = Constraint(model.j, rule=budget_rule) # This constraint will be created for each resource in set model.j
    
    print("Done.")

    print("Running solver...")
    opt = SolverFactory("cplex") #, solver_io="direct") #("_cplex_direct") #, solver_io="python") # Options: cplex, gurobi, glpk  SolverFactory(“gurobi”, solver_io=‘python’)
    model.dual = Suffix(direction=Suffix.IMPORT) # Import dual values from model
    model.rc = Suffix(direction=Suffix.IMPORT) # Import reduced costs from model 
    # model.write('testLPfile.lp') #io_options={‘symbolic_solver_labels’:True} # Use this if you want to write the .lp file 
    results = opt.solve(model, tee=True) # This runs the solver
    print("Done.")
    
    # Write full optimizer results
    # results.write()
    
    # Print results (this is hard-coded to be specific to this problem)
    totalMetalWorkingDays = 0 
    totalWoodWorkingDays = 0 
    print("The objective value is: " + str(model.objective.expr()))
    for item in model.i:
        if(model.SELECT[item].value > 0): # If this trailer was selected 
            print("Trailer type " + str(item) + " was selected " + str(model.SELECT[item].value) + " times.")
            totalMetalWorkingDays = totalMetalWorkingDays + used[(1,item)] * model.SELECT[item].value
            totalWoodWorkingDays = totalWoodWorkingDays + used[(2,item)] * model.SELECT[item].value
    print("The total used totalMetalWorkingDays days is: " + str(totalMetalWorkingDays))
    print("The total used woodworking days is: " + str(totalWoodWorkingDays))
    print("Dual for metalworking days = ", model.dual[model.budgetConstraint[1]])
    print("Dual for woodworking days = ", model.dual[model.budgetConstraint[2]])
    print("Reduced cost for flat-bed trailers = ", model.rc[model.SELECT[1]])
    print("Reduced cost for economy trailers = ", model.rc[model.SELECT[2]])
    print("Reduced cost for luxury trailers = ", model.rc[model.SELECT[3]])

SolveUsingPyomo() # Run above code 