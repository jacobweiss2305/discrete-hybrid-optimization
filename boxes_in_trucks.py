# -*- coding: utf-8 -*-
"""
Example of integrating integer optimization with constraint programming.
Packing boxes into trucks: IP is to minimize costs of assignment of boxes to trucks,
and CP is to ensure boxes fit (in 3D space) into trucks.
Assumes boxes can be oriented in one of two dimensions (up/down, left/right), but not turned on side.

Uses lazy constraint callbacks.  

Requirements: 
 - CPLEX (or other Pyomo-compatible solver)
"""
# Import 
from pyomo.environ import *
from pyomo.opt import *
from pyomo.core import * 
import cplex
from cplex.callbacks import LazyConstraintCallback

from packing_subproblem import * # For running packing CSP using constraint programming 

# Global variables, to be able to access this data in the lazy constraint callback
numBoxes = 0 # Total number of boxes 
numContainers = 0 # Number of containers (trucks)
boxSize = {} # Dict of box sizes, by (box, dim, orientation)
containerSize = {} # Dict of container (truck) sizes, in each of three dimensions [d1, d2, d3]
numLazyConstraints = 0 # Number of lazy constraints added 

def generateRandomData(numBoxes, numContainers):
    # Generate random data and return data structures
    from random import randrange, seed 
    seed(1) # Set random seed

    # Fixed values for random ranges
    costLB = 1
    costUB = 10
    boxSizeLB = 1
    boxSizeUB = 5
    contSizeLB = 3
    contSizeUB = 10

    print("Generating random input data...")
    boxSize = {} # Dict of box sizes, by (box, dim, orientation)
    costs = {} # Dist of costs of assigning a box to a container (b,c):cost
    containerSize = {} # Dict of container (truck) sizes, in each of three dimensions truck:[d1, d2, d3]
    for b in range(1, numBoxes+1):
        # Generate box size 
        theLength = randrange(boxSizeLB, boxSizeUB)
        theWidth = randrange(boxSizeLB, boxSizeUB)
        theHeight = randrange(boxSizeLB, boxSizeUB)
        boxSize[b,1,1] = theLength
        boxSize[b,2,2] = theLength
        boxSize[b,2,1] = theWidth
        boxSize[b,1,2] = theWidth
        boxSize[b,3,1] = theHeight
        boxSize[b,3,2] = theHeight

        # Generate box costs 
        for c in range(1, numContainers+1):
            costs[(b,c)] = randrange(costLB, costUB)

    # Generate box costs 
    for c in range(1, numContainers+1):
        containerSize[c] = [randrange(contSizeLB, contSizeUB), randrange(contSizeLB, contSizeUB),randrange(contSizeLB, contSizeUB)]

    return costs, boxSize, containerSize 

def objective_rule(model):
    # Create objective function
    return sum(model.cost[b,t] * model.ASSIGN[b,t] for b in model.b for t in model.t)

def assignment_rule(model,b):
    # Each box must be assigned to exactly one truck
    return sum(model.ASSIGN[b,t] for t in model.t) == 1

class cplexLazyConstraintCallback(LazyConstraintCallback):
    # CPLEX lazy constraint callback (this is only enabled when solving using .lp file interface).
    # For each worksite, need to read in current solution, create and solve CSP, and add cuts if current assignment is not feasible.
    def __call__(self):
        print("This is the lazy constraint callback code")

        # Reference global values (otherwise, can't access these data inside this callback code)
        global numBoxes
        global numContainers
        global boxSize
        global containerSize
        global numLazyConstraints

        # Read in values of current assignments
        for t in range(1,numContainers+1):
            theBoxes = []
            variableList = [] # # Create list of string names of the active variables, if needed in lazy constraint
            theContainerSize = containerSize[t] # Get list of dimensions for this container
            for b in range(1, numBoxes+1):
                if self.get_values('ASSIGN(' + str(b) + '_' + str(t) + ')') > 0: # If this box assigned to this container
                    theBoxes.append(b)
                    variableList.append('ASSIGN(' + str(b) + '_' + str(t) + ')')

            # Run constraint programming problem to determine if these boxes fit in this container
            isFeasible = solvePackingSubproblem(theBoxes, boxSize, theContainerSize)

            if not isFeasible: # Scheduling problem was infeasible; add cut
                print("Infeasible assignment in container " + str(t) + "; adding cut...")
                coefficientList = [1] * len(variableList) # Create list of the coefficients 
                self.add([variableList,coefficientList], "L", len(variableList)-1) # Add a cut that says at least one of these boxes can't be assigned to this box
                numLazyConstraints += 1
                print("The variableList is " + str(variableList))
            else:
                print("Feasible assignment of boxes to container " + str(t))

def SolveUsingPyomoCPLEX_LP(theNumBoxes, theNumContainers, costs, theBoxSize, theContainerSize):
    ''' Create and solve a concrete Pyomo model and CPLEX interface (to allow lazy constraint callbacks) 
    theNumBoxes: Number of boxes (int)
    theNumContainers: Number of containers (trucks) (int)
    costs: Dict of costs of assigning a box to a container (b,t):cost
    theBoxSize: Dict of box sizes, by (box, dim, orientation)
    theContainerSize: Dict of container (truck) sizes, in each of three dimensions [d1, d2, d3]
    '''

    # Initialize data structures (globally, for use in callback)
    global numBoxes 
    numBoxes = theNumBoxes
    global numContainers 
    numContainers = theNumContainers
    global boxSize
    boxSize = theBoxSize
    global containerSize
    containerSize = theContainerSize
    global numLazyConstraints

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and sets...")
    model.b = Set(initialize=[b for b in range(1, numBoxes+1)], ordered=True) # Index on each box
    model.t = Set(initialize=[t for t in range(1, numContainers+1)], ordered=True) # Index on each container/truck

    # Define variables
    print("Creating variables...")
    model.ASSIGN = Var(model.b * model.t, domain=Binary, initialize = 0) # Indicates the assignment of a box to a truck
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.cost = Param(model.b * model.t, initialize = costs)
    # Also box and truck size, by dim / orientation

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = minimize)

    print("Creating assignment constraints ...")
    model.assignmentConstraint = Constraint(model.b, rule=assignment_rule) 

    print("Adding (optional) constraints disallowing individual boxes in containers...")
    # Check if a box can't possibly fit in a container.  
    # This will reduce number of lazy constraints, but might not reduce overall runtime.
    model.noFitConstraints = ConstraintList() # For adding an array of constraints 
    numNoFitConstraints = 0
    for t in model.t:
        for b in model.b:
            # If it definitely doesn't fit
            if (boxSize[b,1,1] > containerSize[t][0] and boxSize[b,1,2] > containerSize[t][0]) or \
               (boxSize[b,2,1] > containerSize[t][1] and boxSize[b,2,2] > containerSize[t][1]) or \
               (boxSize[b,3,1] > containerSize[t][2]):
                numNoFitConstraints += 1
                model.noFitConstraints.add(model.ASSIGN[b,t] == 0)
    if numNoFitConstraints > 0: print("Added " + str(numNoFitConstraints) + " constraints to prevent selection of items that don't fit.")
    print("Done.")

    print("Pyomo model created.  Saving as LP file and setting up CPLEX interface...")
    model.write('pyomoModel.lp', io_options={'symbolic_solver_labels':True}) # Write Pyomo model as an LP file
    modelCPLEX = cplex.Cplex('pyomoModel.lp')
    theCPLEXLazyCallback = modelCPLEX.register_callback(cplexLazyConstraintCallback) # Register the lazy constraint callback
    # Note using control callbacks (like lazy constraints) means you can only use opportunistic parallel processing, and disables some reductions.

    print("Running solver...")
    modelCPLEX.solve()

    print("Done.  Loading solution from CPLEX back into Pyomo object and saving results...")
    results = modelCPLEX.solution
    
    # Print results (this is hard-coded to be specific to this problem)
    print("The total number of lazy constraints is: " + str(numLazyConstraints))
    print("The objective value is: " + str(results.get_objective_value()))
    for b in model.b:
        for t in model.t:
            if(results.get_values("ASSIGN(" + str(b) + "_" + str(t) + ")")) > 0:
                print("Box " + str(b) + " is assigned to container " + str(t) + ", at a cost of " + str(model.cost[b,t]))


# Small dataset, for testing
numBoxes = 5 # Number of boxes
numContainers = 3 # Number of containers (trucks)
costs = {(1,1):1, (1,2):2, (1,3):3, # Costs of assigning a box to a container
            (2,1):1, (2,2):2, (2,3):3,
            (3,1):1, (3,2):2, (3,3):3,
            (4,1):1, (4,2):2, (4,3):3,
            (5,1):1, (5,2):2, (5,3):3 } 
# Dict of box sizes, by (box, dim, orientation)
boxSize = { (1,1,1):1, (1,1,2):1, (1,2,1):1, (1,2,2):1, (1,3,1):1, (1,3,2):1, 
            (2,1,1):2, (2,1,2):2, (2,2,1):2, (2,2,2):2, (2,3,1):2, (2,3,2):2,
            (3,1,1):1, (3,1,2):4, (3,2,1):4, (3,2,2):1, (3,3,1):1, (3,3,2):1,
            (4,1,1):2, (4,1,2):5, (4,2,1):5, (4,2,2):2, (4,3,1):2, (4,3,2):2,
            (5,1,1):1, (5,1,2):3, (5,2,1):3, (5,2,2):1, (5,3,1):3, (5,3,2):3 } 

# Dict of container (truck) sizes, in each of three dimensions [d1, d2, d3]
containerSize = {1:[3,6,5], 2:[4,4,4], 3:[5,8,5]} 

# Use this to generate random data.  Otherwise, just comment this to use above test data. 
numBoxes = 20
numContainers = 8 # 8 works, 7 works but takes about 60 sec  
costs, boxSize, containerSize = generateRandomData(numBoxes, numContainers)

SolveUsingPyomoCPLEX_LP(numBoxes, numContainers, costs, boxSize, containerSize) # Run above code 