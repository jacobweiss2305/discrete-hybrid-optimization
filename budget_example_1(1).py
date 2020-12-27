# -*- coding: utf-8 -*-
"""
Simple example problem: budgeting for disaster relief (first problem)

Requirements: 
 - CPLEX (or other Pyomo-compatible solver)
"""
# Import 
from pyomo.environ import *
from pyomo.opt import *
from pyomo.core import * 
import cplex
import numpy as np

def objective_rule(model):
    # Create objective function
    return sum(model.benefit[i] * model.SELECT[i] for i in model.i)

def budget_rule(model):
    # Constraint on available budget 
    return sum(model.cost[i] * model.SELECT[i] for i in model.i) <= model.budget

def fridge_electricity_rule(model,i):
    # Constraint on requiring a refrigerator or generator
    if i == 2 or i == 3:
        return model.SELECT[4] >= model.SELECT[i]
    elif i == 4 or i == 5 or i == 7:
        return model.SELECT[6] >= model.SELECT[i]
    else:
        return Constraint.Skip

def vaccine_rule(model, i):
    # Constraint on vaccines
    if i == 1:
        return 2-model.SELECT[2]-model.SELECT[3] >= model.SELECT[i]
    elif i == 2 or i == 3:
        return 1-model.SELECT[1] >= model.SELECT[i]
    else:
        return Constraint.Skip    

def SolveUsingPyomo():
    ''' Create and solve a concrete Pyomo model '''

    # Initialize data structures with hard-coded data from example
    numItems = 9 # Items
    itemBenefit = {1:5,2:2,3:2,4:3,5:5,6:5,7:1,8:5,9:4} # Dict of item benefit values
    itemCost = {1:50,2:20,3:25,4:1,5:100,6:50,7:1,8:10,9:1} # Dict of item costs (in $K)
    budget = 175 # Total budget, in $K

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and set...")
    model.i = Set(initialize=[i for i in range(1, numItems+1)], ordered=True) # Index on each item
    
    # Define variables
    print("Creating variables...")
    model.SELECT = Var(model.i, domain=Binary, initialize = 0) # Indicates if item i is selected
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.benefit = Param(model.i, initialize = itemBenefit)
    model.cost = Param(model.i, initialize = itemCost)
    model.budget = Param(initialize = budget)

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = maximize)

    print("Creating constraint on available budget...")
    model.budgetConstraint = Constraint(rule=budget_rule)

    print("Creating constraints on requirement to have refrigerator or generator...")
    model.fridgeElecConstraint = Constraint(model.i, rule=fridge_electricity_rule)

    print("Creating constraints on vaccine purchases...")
    model.vaccineConstraint = Constraint(model.i, rule=vaccine_rule)
    
    print("Done.")

    print("Running solver...")
    opt = SolverFactory("cplex") #, solver_io="direct") #("_cplex_direct") #, solver_io="python") # Options: cplex, gurobi, glpk  SolverFactory(“gurobi”, solver_io=‘python’)
    # model.write('testLPfile.lp') #io_options={‘symbolic_solver_labels’:True} # Use this if you want the .lp file 
    results = opt.solve(model, tee=True) # This runs the solver
    print("Done.")
    
    # Write full optimizer results
    # results.write()
    
    # Print results
    totalBudgetUsed = 0 
    print("The objective value is: " + str(model.objective.expr()))
    for item in model.i:
        if(model.SELECT[item] == 1): # If this item was selected 
            print("Item " + str(item) + " was selected.")
            totalBudgetUsed = totalBudgetUsed + model.cost[item]
    print("The total value of items purchased is: $" + str(totalBudgetUsed) + "K")

SolveUsingPyomo() # Run above code 