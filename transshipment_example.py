# -*- coding: utf-8 -*-
"""
Transshipment problem from Applied Mathematical Programming, by Bradley et al.
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

    # Initialize data structures with hard-coded data from example
    numPlants = 2 # Number of plants
    numMarkets = 2 # Number of markets
    numTransshipmentNodes = 3 # Number of transshipment nodes
    numNodes = numPlants + numMarkets + numTransshipmentNodes
    supply = {1:250, 2:450} # Supply at plants
    demand = {6:200, 7:500} # Demand at markets 
    costs = {(1,3):6, (1,5):7, (2,3):6, (2,4):9, (2,5):4, (3,4):8, (3,5):2,
             (4,6):15, (4,7):10, (5,6):14, (5,7):17 }
    arcs = [(1,3), (1,5), (2,3), (2,4), (2,5), (3,4), (3,5),
             (4,6), (4,7), (5,6), (5,7) ]

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and sets...")
    model.i = Set(initialize=[i for i in range(1, numNodes+1)], ordered=True) # Index on each node
    model.supplyNodes = Set(within=model.i, initialize = [1,2]) # Index on each plant node
    model.demandNodes = Set(within=model.i, initialize = [6,7]) # Index on each market node
    model.transshipmentNodes = Set(within=model.i, initialize = [3,4,5]) # Index on each transshipment node
    model.arcs = Set(within=model.i * model.i, initialize = arcs) # Create the set of arcs

    # Define variables
    print("Creating variables...")
    model.FLOW = Var(model.arcs, domain=NonNegativeReals, initialize = 0) # Flow variable
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.supply = Param(model.supplyNodes, initialize = supply)
    model.demand = Param(model.demandNodes, initialize = demand)    
    model.costs = Param(model.arcs, initialize = costs)

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = minimize)

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