# -*- coding: utf-8 -*-
"""
Metal-working shop example from Applied Mathematical Programming, by Bradley et al. 
This is the dual formulation.  

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
    return sum(model.objCoefficients[u] * model.DUAL_VAR[u] for u in model.u)

def constraint_rule(model,i): 
    # Constraints in dual problem
    return sum(model.usedTranspose[i,u] * model.DUAL_VAR[u] for u in model.u) >= model.constraintRHS[i]

def SolveUsingPyomo():
    ''' Create and solve a concrete Pyomo model '''

    # Initialize data structures with hard-coded data from example
    numDualVariables = 2 # Number of dual variables
    numDualConstraints = 3 # Number of dual constraints
    objCoefficients = {1:24, 2:60} # Dict of coefficients in dual objective function
    usedTranspose = {(1,1):0.5, (1,2):1, (2,1):2, (2,2):2, (3,1):1, (3,2):4} # Transpose of primal problem's A matrix 
    constraintRHS = {1:6, 2:14, 3:13} # Dict of constraint right-hand-side coefficients

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and set...")
    model.u = Set(initialize=[u for u in range(1, numDualVariables+1)], ordered=True) # Index on each dual variable
    model.i = Set(initialize=[i for i in range(1, numDualConstraints+1)], ordered=True) # Index on each dual constraint 
    
    # Define variables
    print("Creating variables...")
    model.DUAL_VAR = Var(model.u, domain=NonNegativeReals, initialize = 0) # Dual variable 
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.objCoefficients = Param(model.u, initialize = objCoefficients)
    model.usedTranspose = Param((model.i * model.u), initialize = usedTranspose)
    model.constraintRHS = Param(model.i, initialize = constraintRHS)

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = minimize)

    print("Creating constraints in dual problem...")
    model.dualConstraint = Constraint(model.i, rule=constraint_rule) # This constraint will be created for each i
    
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
    print("The objective value is: " + str(model.objective.expr()))
    for item in model.u:
        if(model.DUAL_VAR[item].value > 0): # If this variable is non-zero
            print("Dual variable " + str(item) + " has value: " + str(model.DUAL_VAR[item].value) )
    print("Shadow price for flatbed trailers = ", model.dual[model.dualConstraint[1]])
    print("Shadow price for economy trailers = ", model.dual[model.dualConstraint[2]])
    print("Shadow price for luxury trailers = ", model.dual[model.dualConstraint[3]])    
    print("Reduced cost for metal-working dual variable = ", model.rc[model.DUAL_VAR[1]])
    print("Reduced cost for woodworking dual variable = ", model.rc[model.DUAL_VAR[2]])

SolveUsingPyomo() # Run above code 