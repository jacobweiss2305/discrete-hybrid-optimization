# -*- coding: utf-8 -*-
"""
Transportation problem from Applied Mathematical Programming, by Bradley et al.
Chapter 8, problem 3, p. 260

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
    return sum(model.costs[i,j] * model.FLOW[i,j] for (i,j) in model.arcs)

def supply_rule(model,k):
    # Constraint on available supply 
    return sum(model.FLOW[i,j] for (i,j) in model.arcs if i ==k) <= model.supply[k]

def demand_rule(model,k):
    # Constraint on required demand  
    return sum(model.FLOW[i,j] for (i,j) in model.arcs if j ==k) >= model.demand[k]

def SolveUsingPyomo():
    ''' Create and solve a concrete Pyomo model '''

    # Initialize data structures with hard-coded data from example
    numTerminals = 5 # Number of terminals (supply nodes)
    numFacilities = 5 # Number of facilities (demand nodes)
    numNodes = numTerminals + numFacilities
    supply = {1:45, 2:90, 3:95, 4:75, 5:105}
    demand = {6:120, 7:80, 8:50, 9:75, 10:85}
    costs = {(1,6):6, (1,7):6, (1,8):9, (1,9):4, (1,10):10,    
            (2,6):3, (2,7):2, (2,8):7, (2,9):5, (2,10):10,
            (3,6):8, (3,7):7, (3,8):5, (3,9):6, (3,10):10,
            (4,6):11, (4,7):12, (4,8):9, (4,9):5, (4,10):10,
            (5,6):4, (5,7):3, (5,8):4, (5,9):5, (5,10):10
            }
    arcs = [(1,6), (1,7), (1,8), (1,9), (1,10),    
            (2,6), (2,7), (2,8), (2,9), (2,10),
            (3,6), (3,7), (3,8), (3,9), (3,10),
            (4,6), (4,7), (4,8), (4,9), (4,10),
            (5,6), (5,7), (5,8), (5,9), (5,10)
            ]

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and sets...")
    model.i = Set(initialize=[i for i in range(1, numNodes+1)], ordered=True) # Index on each node
    model.supplyNodes = Set(within=model.i, initialize = [*range(1,numTerminals+1)]) # Index on each supply node
    model.demandNodes = Set(within=model.i, initialize = [*range(numTerminals+1,numNodes+1)]) # Index on each demand node
    model.arcs = Set(within=model.i * model.i, initialize = arcs) # Create the set of arcs

    # Define variables
    print("Creating variables...")
    model.FLOW = Var(model.arcs, domain=NonNegativeReals, initialize = 0) # Flow variable
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.supply = Param(model.supplyNodes, initialize = supply)
    model.demand = Param((model.demandNodes), initialize = demand)
    model.costs = Param(model.arcs, initialize = costs)

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = minimize)

    print("Creating constraints on supply and demand...")
    model.supplyConstraint = Constraint(model.supplyNodes, rule=supply_rule) 
    model.demandConstraint = Constraint(model.demandNodes, rule=demand_rule) 

    print("Done.")

    print("Running solver...")
    opt = SolverFactory("cplex") #, solver_io="direct") #("_cplex_direct") #, solver_io="python") # Options: cplex, gurobi, glpk  SolverFactory(“gurobi”, solver_io=‘python’)
    # model.dual = Suffix(direction=Suffix.IMPORT) # Import dual values from model
    # model.rc = Suffix(direction=Suffix.IMPORT) # Import reduced costs from model 
    model.write('testLPfile.lp', io_options={'symbolic_solver_labels':True} ) # Use this if you want to write the .lp file 
    results = opt.solve(model, tee=True) # This runs the solver
    print("Done.")
    
    # Write full optimizer results
    # results.write()
    
    # Print results (this is hard-coded to be specific to this problem)
    amountSentReceived = [0] * numNodes
    print("The objective value is: " + str(model.objective.expr()))
    for i,j in model.arcs:
        if(model.FLOW[i,j].value > 0): # If there is flow on this arc
            print("There are " + str(model.FLOW[i,j].value) + " units of flow from " + str(i) + " to " +str(j))
            amountSentReceived[i-1] += model.FLOW[i,j].value
            amountSentReceived[j-1] += model.FLOW[i,j].value
    for i in model.supplyNodes: print("Node " +str(i) + " sent " + str(amountSentReceived[i-1]) + " units of flow.")
    for i in model.demandNodes: print("Node " +str(i) + " received " + str(amountSentReceived[i-1]) + " units of flow.")

SolveUsingPyomo() # Run above code 