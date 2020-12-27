# -*- coding: utf-8 -*-
"""
Minimum cost network flow problem for network flow assignment
Chapter 8, problem 21, p. 267

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

def arcCapacity_rule(model,i,j):
    # Constraint on arc capacity 
    return model.FLOW[i,j] <= model.capacities[i,j]

def bof_rule(model,k):
    # Balance-of-flow constraints on nodes
    balance = 0 # Assume transshipment node with balance of 0
    if k in model.supplyNodes: # Supply node
        balance = model.supply[k]
    elif k in model.demandNodes: # Demand node 
        balance = -1 * model.demand[k]

    return sum(model.FLOW[i,j] for (i,j) in model.arcs if i ==k) - sum(model.FLOW[i,j] for (i,j) in model.arcs if j ==k) == balance

def SolveUsingPyomo():
    ''' Create and solve a concrete Pyomo model '''

    # Initialize data structures with hard-coded data 
    numSourceNodes = 3 # Number of source nodes
    numDemandNodes = 4 # Number of demand nodes
    numTransshipmentNodes = 5 # Number of transshipment nodes
    numNodes = numSourceNodes + numDemandNodes + numTransshipmentNodes
    supply = {1:100, 2:150, 3:75} # Supply
    demand = {9:50, 10:50, 11:100, 12:125} # Demand 
    costs = {(1,4):.75, (1,5):1.2, (2,5):1, (2,8):1.4, (3,7):.75, (3,8):.55, (4,6):.9, (4,7):.5, (4,10):2, (5,6):1.4, (5,7):2.7,
            (6,9):.9, (6,10):.6, (7,9):3.2, (7,10):2.2, (7,11):2.7, (7,12):2.1, (8,7):1, (8,11):3.8, (8,12):3.4 }
    capacities = {(1,4):75, (1,5):50, (2,5):100, (2,8):100, (3,7):50, (3,8):50, (4,6):25, (4,7):20, (4,10): 100, (5,6):25, (5,7):125,
            (6,9):50, (6,10):20, (7,9):25, (7,10):25, (7,11):75, (7,12):50, (8,7):100, (8,11):50, (8,12):100 }
    arcs = [(1,4), (1,5), (2,5), (2,8), (3,7), (3,8), (4,6), (4,7), (4,10), (5,6), (5,7),
            (6,9), (6,10), (7,9), (7,10), (7,11), (7,12), (8,7), (8,11), (8,12) ]

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and sets...")
    model.i = Set(initialize=[i for i in range(1, numNodes+1)], ordered=True) # Index on each node
    model.supplyNodes = Set(within=model.i, initialize = [1,2,3]) # Index on each plant node
    model.demandNodes = Set(within=model.i, initialize = [9,10,11,12]) # Index on each market node
    model.transshipmentNodes = Set(within=model.i, initialize = [4,5,6,7,8]) # Index on each transshipment node
    model.arcs = Set(within=model.i * model.i, initialize = arcs) # Create the set of arcs

    # Define variables
    print("Creating variables...")
    model.FLOW = Var(model.arcs, domain=NonNegativeReals, initialize = 0) # Flow variable
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.supply = Param(model.supplyNodes, initialize = supply)
    model.demand = Param(model.demandNodes, initialize = demand)
    model.costs = Param(model.arcs, initialize = costs)
    model.capacities = Param(model.arcs, initialize = capacities)    

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = minimize)

    print("Creating constraints on arc capacities...")
    model.arcCapacityConstraint = Constraint(model.arcs, rule=arcCapacity_rule) 

    print("Creating balance-of-flow constraints...")
    model.bofConstraint = Constraint(model.i, rule=bof_rule) 

    print("Done.")

    print("Running solver...")
    opt = SolverFactory("cplex") #, solver_io="direct") #("_cplex_direct") #, solver_io="python") # Options: cplex, gurobi, glpk  SolverFactory(“gurobi”, solver_io=‘python’)
    # model.dual = Suffix(direction=Suffix.IMPORT) # Import dual values from model
    # model.rc = Suffix(direction=Suffix.IMPORT) # Import reduced costs from model 
    # model.write('testLPfile.lp', io_options={'symbolic_solver_labels':True} ) # Use this if you want to write the .lp file 
    results = opt.solve(model, tee=True) # This runs the solver
    print("Done.")
    
    # Write full optimizer results
    # results.write()
    
    # Print results (this is hard-coded to be specific to this problem)
    amountSent = [0] * numNodes
    amountReceived = [0] * numNodes
    print("The objective value is: " + str(model.objective.expr()))
    for i,j in model.arcs:
        theFlow = model.FLOW[i,j].value
        if(theFlow > 0): # If there is flow on this arc
            print("There are " + str(model.FLOW[i,j].value) + " units of flow from " + str(i) + " to " +str(j))
            amountSent[i-1] += theFlow
            amountReceived[j-1] += theFlow
    for i in model.supplyNodes: print("Node " +str(i) + " sent " + str(amountSent[i-1]) + " units of flow.")
    for i in model.demandNodes: print("Node " +str(i) + " received " + str(amountReceived[i-1]) + " units of flow.")

SolveUsingPyomo() # Run above code 