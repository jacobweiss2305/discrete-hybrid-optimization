# -*- coding: utf-8 -*-
"""
Code to solve problems from Applied Mathematical Programming, by Bradley et al. 
Chapter 9, Problem 1
Data provided in slides

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
    return sum(model.cost[s] * model.SELECT[s] for s in model.s)

def totalSites_rule(model):
    # Constraint on minimum number of sites to be selected
    return sum(model.SELECT[s] for s in model.s) >= 5

def siteConstraint1_rule(model):
    return model.SELECT[8] <= 2 - model.SELECT[1] - model.SELECT[7]

def siteConstraint2_rule(model):
    return model.SELECT[5] <= 1 - model.SELECT[3]

def siteConstraint3_rule(model):
    return model.SELECT[5] <= 1 - model.SELECT[4]

def siteConstraint4_rule(model):
    return model.SELECT[5] + model.SELECT[6] + model.SELECT[7] + model.SELECT[8]  <= 2

def SolveUsingPyomo():
    ''' Create and solve a concrete Pyomo model '''

    # Initialize data structures with hard-coded data 
    numSites = 10 # Number of sites
    costs = {1:5, 2:3, 3:4, 4:2, 5:7, 6:3, 7:3, 8:5, 9:4, 10:6} # Dict of costs per site

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and set...")
    model.s = Set(initialize=[s for s in range(1, numSites+1)], ordered=True) # Index on each site
  
    # Define variables
    print("Creating variables...")
    model.SELECT = Var(model.s, domain=Boolean, initialize = 0) # Indicates if site s is selected
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.cost = Param(model.s, initialize = costs)

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = minimize)

    print("Creating constraints...")
    model.totalSitesConstraint = Constraint(rule=totalSites_rule) 
    model.siteConstraint1 = Constraint(rule=siteConstraint1_rule) 
    model.siteConstraint2 = Constraint(rule=siteConstraint2_rule) 
    model.siteConstraint3 = Constraint(rule=siteConstraint3_rule) 
    model.siteConstraint4 = Constraint(rule=siteConstraint4_rule)     
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
    for site in model.s:
        if(model.SELECT[site].value > 0): # If this site was selected 
            print("Site " + str(site) + " was selected (cost is " + str(model.cost[site]) + ")")

SolveUsingPyomo() # Run above code 