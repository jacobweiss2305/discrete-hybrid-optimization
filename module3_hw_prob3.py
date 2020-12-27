# -*- coding: utf-8 -*-
"""
Code to solve problems from Applied Mathematical Programming, by Bradley et al. 
Chapter 9, Problem 3

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
    return sum(model.customers[i] * model.SELECT[i] for i in model.i)

def moneyAvail_rule(model):
    # Constraint on amount of money
    return sum(model.cost[i] * model.SELECT[i] for i in model.i) <= model.money_avail

def designerAvail_rule(model):
    # Constraint on amount of designer hours
    return sum(model.designer[i] * model.SELECT[i] for i in model.i) <= model.designer_avail

def salesAvail_rule(model):
    # Constraint on amount of salesperson hours
    return sum(model.sales[i] * model.SELECT[i] for i in model.i) <= model.sales_avail

def constraint4_rule(model):
    # Constraint 4 from formulation
    return model.SELECT[4] + model.SELECT[5] >= model.SELECT[6]

def constraint5_rule(model):
    # Constraint 5 from formulation
    return model.SELECT[2] + model.SELECT[5] <= 1

def SolveUsingPyomo():
    ''' Create and solve a concrete Pyomo model '''

    # Initialize data structures with hard-coded data 
    numOptions = 6 # Number of advertising option
    customers = {1:1000000, 2:200000, 3:300000, 4:400000, 5:450000, 6:450000} # Dict of customers reached per option i
    costs = {1:500000, 2:150000, 3:300000, 4:250000, 5:250000, 6:100000} # Dict of costs per option i    
    designer = {1:700, 2:250, 3:200, 4:200, 5:300, 6:400} # Dict of designer hours needed per option i    
    sales = {1:200, 2:100, 3:100, 4:100, 5:100, 6:1000} # Dict of salesperson hours needed per option i
    money_avail = 1800000 # Total money available
    designer_avail = 1500 # Number of designer hours available
    sales_avail = 1200 # Nmber of salesperson hours available 

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and set...")
    model.i = Set(initialize=[i for i in range(1, numOptions+1)], ordered=True) # Index on each advertising option 
  
    # Define variables
    print("Creating variables...")
    model.SELECT = Var(model.i, domain=Boolean, initialize = 0) # Indicates if advertising option is selected
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.customers = Param(model.i, initialize = customers)
    model.cost = Param(model.i, initialize = costs)
    model.designer = Param(model.i, initialize = designer)
    model.sales = Param(model.i, initialize = sales)
    model.money_avail = Param(initialize = money_avail)
    model.designer_avail = Param(initialize = designer_avail)
    model.sales_avail = Param(initialize = sales_avail) 

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = maximize)

    print("Creating constraints...")
    model.moneyAvailConstraint = Constraint(rule=moneyAvail_rule) 
    model.designAvailConstraint = Constraint(rule=designerAvail_rule)   
    model.salesAvailConstraint = Constraint(rule=salesAvail_rule)
    model.constraint4Constraint = Constraint(rule=constraint4_rule)
    model.constraint5Constraint = Constraint(rule=constraint5_rule)

    print("Done.")

    print("Running solver...")
    opt = SolverFactory("cplex") #, solver_io="direct") #("_cplex_direct") #, solver_io="python") # Options: cplex, gurobi, glpk  SolverFactory(“gurobi”, solver_io=‘python’)
    # model.dual = Suffix(direction=Suffix.IMPORT) # Import dual values from model
    # model.rc = Suffix(direction=Suffix.IMPORT) # Import reduced costs from model 
    # model.write('testLPfile.lp', io_options={'symbolic_solver_labels':True} )# Use this if you want to write the .lp file 
    results = opt.solve(model, tee=True) # This runs the solver
    print("Done.")
    
    # Write full optimizer results
    # results.write()
    
    # Print results (this is hard-coded to be specific to this problem)
    print("The objective value is: " + str(model.objective.expr()))
    for option in model.i:
        if(model.SELECT[option].value > 0): # If this optiono was selected 
            print("Option " + str(option) + " was selected (customers reached = " + str(model.customers[option]) + ")")

SolveUsingPyomo() # Run above code 