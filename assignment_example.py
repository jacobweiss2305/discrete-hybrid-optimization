# -*- coding: utf-8 -*-
"""
Assignment problem from Applied Mathematical Programming, by Bradley et al.
Chapter 8, problem 10, p. 263

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
    return sum(model.experience[i,j] * model.SELECT[i,j] for (i,j) in model.arcs)

def person_rule(model,k):
    # Constraint requiring each person to have only one job 
    return sum(model.SELECT[i,j] for (i,j) in model.arcs if i ==k) == 1

def job_rule(model,k):
    # Constraint requiring each job to be assigned exactly once 
    return sum(model.SELECT[i,j] for (i,j) in model.arcs if j ==k) == 1

def SolveUsingPyomo():
    ''' Create and solve a concrete Pyomo model '''

    # Initialize data structures with hard-coded data from example
    numPeople = 5 # Number of personnel
    numJobs = 5 # Number of jobs
    numNodes = numPeople + numJobs
    experience = {(1,6):3, (1,7):5, (1,8):6, (1,9):2, (1,10):2,
                  (2,6):2, (2,7):3, (2,8):5, (2,9):3, (2,10):2,
                  (3,6):3,          (3,8):4, (3,9):2, (3,10):2,
                  (4,6):3,          (4,8):3, (4,9):2, (4,10):2,
                           (5,7):3,          (5,9):1            }
    arcs = [(1,6), (1,7), (1,8), (1,9), (1,10),
            (2,6), (2,7), (2,8), (2,9), (2,10),
            (3,6),          (3,8), (3,9), (3,10),
            (4,6),          (4,8), (4,9), (4,10),
                   (5,7),          (5,9)         ]

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and sets...")
    model.i = Set(initialize=[i for i in range(1, numNodes+1)], ordered=True) # Index on each node
    model.peopleNodes = Set(within=model.i, initialize = [*range(1,numPeople+1)]) # Index on each person node
    model.jobNodes = Set(within=model.i, initialize = [*range(numPeople+1,numNodes+1)]) # Index on each job node
    model.arcs = Set(within=model.i * model.i, initialize = arcs) # Create the set of arcs

    # Define variables
    print("Creating variables...")
    model.SELECT = Var(model.arcs, domain=Binary, initialize = 0) # Flow variable
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.experience = Param(model.arcs, initialize = experience)

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = maximize)

    print("Creating assignment constraints ...")
    model.personConstraint = Constraint(model.peopleNodes, rule=person_rule) 
    model.jobConstraint = Constraint(model.jobNodes, rule=job_rule) 

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
    print("The objective value is: " + str(model.objective.expr()))
    for i,j in model.arcs:
        if(model.SELECT[i,j].value == 1): # If there is flow (an assignment) on this arc
            print("Person " + str(i) + " is assigned to job " + str(j) + ", with " +str(model.experience[i,j]) + " years of experience.")

SolveUsingPyomo() # Run above code 