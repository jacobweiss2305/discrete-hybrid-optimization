# -*- coding: utf-8 -*-
"""
Packing subproblem for boxes-in-truck problem, for one truck.  
Checks feasibility, given boxes and truck.  
Assumes each box has only two possible orientations.
Solves using constraint programming.

Requirements: 
 - CPLEX (or other Pyomo-compatible solver)
"""

# Import 
from docplex.cp.model import CpoModel
from docplex.cp.solution import CpoRefineConflictResult
from sys import stdout

def solvePackingSubproblem(theBoxes, boxSize, containerSize):
    ''' Input data
    theBoxes: the boxes to pack into container (list)
    boxSize: size of each box, in each of three dimensions [box, dim, orientation] (dict)
    containerSize: size of this container, in each of three dimensions (list)
    '''

    # Create a CPO model
    model = CpoModel()

    # Create variables
    maxPosition = max(containerSize)
    theKeys = []
    for b in theBoxes: # Each box and dimension
        theKeys.append((b,1))
        theKeys.append((b,2))
        theKeys.append((b,3))
    POSITION = model.integer_var_dict(theKeys, 0, maxPosition, "POSITION") # For each box and in each dimension, the location of origin corner
    theKeys = []
    for b in theBoxes: # Each box and orientation
        theKeys.append((b,1))
        theKeys.append((b,2))
    ORIENTATION = model.binary_var_dict(theKeys, "ORIENTATION") # For each box, indicates which orientation

    # Add constraints
    # Ensure boxes aren't closer than touching (i.e., overlapping each other)
    for i in theBoxes:
        for j in theBoxes:
            if i != j:
                model.add(
                ( POSITION[(i,1)] + boxSize[i,1,1] * ORIENTATION[(i,1)] + boxSize[i,1,2] * ORIENTATION[(i,2)] <= POSITION[(j,1)] ) |  
                ( POSITION[(i,2)] + boxSize[i,2,1] * ORIENTATION[(i,1)] + boxSize[i,2,2] * ORIENTATION[(i,2)] <= POSITION[(j,2)] ) |  
                ( POSITION[(i,3)] + boxSize[i,3,1] * ORIENTATION[(i,1)] + boxSize[i,3,2] * ORIENTATION[(i,2)] <= POSITION[(j,3)] ) )  # Dim 3

	# Ensure boxes are inside container
    for d in range(1,4): # For each dimension
        for i in theBoxes:
            model.add( POSITION[(i,d)] + boxSize[i,d,1] * ORIENTATION[(i,1)] + boxSize[i,d,2] * ORIENTATION[(i,2)] <= containerSize[d-1] )
            # model.add( POSITION[(i,d)] >= 0 ) # Not needed, since this is implied by the variable's lower bound 

  	# Ensure each box has an orientation
    for i in theBoxes:
        model.add(ORIENTATION[i,1] + ORIENTATION[i,2] == 1)

    # Solve model
    print("Solving model....")
    msol = model.solve(TimeLimit=10)

    if msol: # If the model ran successfully, it returns True 
        return True
    else: # Problem is infeasible; print the infeasibility 
        # theConflictsResult = model.refine_conflict()
        # print(theConflictsResult)
        return False 
