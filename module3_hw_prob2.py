# -*- coding: utf-8 -*-
"""
Code to solve problems from Applied Mathematical Programming, by Bradley et al. 
Chapter 9, Problem 2
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
    return sum(model.basicCosts[i] * model.Y[i] for i in model.i) + sum(model.courseCosts[i,c] * model.X[i,c] for (i,c) in model.arcs)

def yDefinition_rule(model,i,c):
    # Enforce the definition of Y
    return model.X[i,c] <= model.Y[i]

def requiredFields_rule(model,f):
    # Ensure at least one course in this field is selected 
    return sum(model.X[i,c] for (i,c) in model.arcs if c in model.sF[f]) >= 1

def requiredCourses_rule(model):
    # Ensure at least ten courses are selected
    return sum(model.X[i,c] for (i,c) in model.arcs) >= 10

def SolveUsingPyomo():
    ''' Create and solve a concrete Pyomo model '''

    # Initialize data structures with hard-coded data 
    numColleges = 5 # Number of colleges 
    numCourses = 40 # Number of courses (total)
    numFields = 6 # Number of fields 
    basicCosts = {1:10, 2:12, 3:13, 4:15, 5:16 } # Dict of tuition (basic) costs of attending college i
    # List of arcs among college i and course c
    arcs = [
        (1,1),	(1,2),	(1,3),	(1,4),	(1,5),	(1,6),	(1,7),	(1,8),
        (2,9),	(2,10),	(2,11),	(2,12),	(2,13),	(2,14),	(2,15),	(2,16),
        (3,17),	(3,18),	(3,19),	(3,20),	(3,21),	(3,22),	(3,23),	(3,24),
        (4,25),	(4,26),	(4,27),	(4,28),	(4,29),	(4,30),	(4,31),	(4,32),
        (5,33),	(5,34),	(5,35),	(5,36),	(5,37),	(5,38),	(5,39),	(5,40) ] 
    # Dict of course charges of college i, course c
    courseCosts = {
        (1,1):7,	(1,2):2,	(1,3):9,	(1,4):1,	(1,5):5,	(1,6):10,	(1,7):9,	(1,8):6,
        (2,9):9,	(2,10):1,	(2,11):4,	(2,12):1,	(2,13):9,	(2,14):1,	(2,15):4,	(2,16):8,
        (3,17):6,	(3,18):3,	(3,19):7,	(3,20):8,	(3,21):4,	(3,22):3,	(3,23):2,	(3,24):3,
        (4,25):1,	(4,26):7,	(4,27):6,	(4,28):4,	(4,29):1,	(4,30):10,	(4,31):7,	(4,32):3,
        (5,33):3,	(5,34):1,	(5,35):7,	(5,36):3,	(5,37):3,	(5,38):5,	(5,39):10,	(5,40):2  } 
    # Dict of list of courses in each field 
    coursesInField = {1:[1,7,9,15,17,25,33],
                    2:[2,10,18,23,26,31,34],
                    3:[3,8,11,19,27,35,39],	
                    4:[4,12,16,20,24,28,36],
                    5:[5,13,21,29,32,37],
                    6:[6,14,22,30,38,40] } 

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and set...")
    model.i = Set(initialize=[i for i in range(1, numColleges+1)], ordered=True) # Index on each college
    model.c = Set(initialize=[c for c in range(1, numCourses+1)], ordered=True) # Index on each course
    model.arcs = Set(within=model.i * model.c, initialize = arcs) # Create the set of arcs   
    model.f = Set(initialize=[f for f in range(1, numFields+1)], ordered=True) # Index on each field     
    model.sF = Set(model.f) # Subset of courses in field f
    for f in model.f: # Store those courses in field f
        for c in coursesInField[f]:
            model.sF[f].add(c) # Store in f entry in sF 

    # Define variables
    print("Creating variables...")
    model.X = Var(model.arcs, domain=Boolean, initialize = 0) # Indicates if course c from college i is selected 
    model.Y = Var(model.i, domain=Boolean, initialize = 0) # Indicates if college i is attended 

    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.basicCosts = Param(model.i, initialize = basicCosts)
    model.courseCosts = Param(model.arcs, initialize = courseCosts)

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = minimize)

    print("Creating constraints...")
    model.yDefinitionConstraint = Constraint(model.arcs, rule=yDefinition_rule) 
    model.requiredFieldsConstraint = Constraint(model.f, rule=requiredFields_rule)
    model.requiredCoursesConstraint = Constraint(rule=requiredCourses_rule)   
   
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
    for i,c in model.arcs:
        if(model.X[i,c].value > 0): # If this college and course was selected 
            # Get the field for this course
            # Note this is *not* an efficient way of retrieving this information 
            theField = 0
            for f in model.f: 
                if c in model.sF[f]: 
                    theField = f
                    break
            print("Course " + str(c) + " in field " + str(theField) + " at college " + str(i) + " was selected.")

SolveUsingPyomo() # Run above code 