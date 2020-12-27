# -*- coding: utf-8 -*-
"""
Scheduling subproblem for job shipping and scheduling problem, for one worksite.  
Checks feasibility, given number of jobs.  
Solves using constraint programming.

Requirements: 
 - CPLEX (or other Pyomo-compatible solver)
"""

# Import 
from docplex.cp.model import CpoModel
from docplex.cp.solution import CpoRefineConflictResult
from sys import stdout

def solveSchedulingSubproblem(numJobs, totalTime, availResources, jobLength):
    ''' Input data
    numJobs: Number of jobs (int)
    totalTime: Total time blocks (int)
    availResources: Total amount of resource available for this machine.  Assume each job uses one resource. (int)
    jobLength: The length (in time blocks) of each job (list, by job number)
    '''

    # Create a CPO model
    model = CpoModel()

    # Create variables
    TIME = model.integer_var_list(numJobs, 0, totalTime - 1, "TIME") # For each job, indicate start time
    RESOURCE = model.integer_var_list(numJobs, 0, availResources - 1, "RESOURCE") # For each job, indicate resource used

    # Add general constraints
    for i in range(numJobs):
        # Jobs must end before the end of the totalTime available
        model.add(TIME[i] + jobLength[i] <= totalTime) 
        # Jobs can't be scheduled on a machine at the same time
        for j in range(numJobs):
            if i != j:
                model.add( (RESOURCE[i] != RESOURCE[j]) | (TIME[i] + jobLength[i] <= TIME[j]) | (TIME[j] + jobLength[j] <= TIME[i]) ) 

    # If there's only one job, then above constraints will never reference RESOURCE variable.
    # In that case, RESOURCE won't show up in the problem, and won't get a value.
    # To prevent this, we add dummy constraints on RESOURCE as follows:
    if numJobs == 1: model.add(RESOURCE[0] >= 0)

    # Solve model
    print("Solving model....")
    msol = model.solve(TimeLimit=10)

    if msol: # If the model ran successfully, it returns True 
        print("Solution:")
        for j in range(numJobs):
            print("Job " + str(j) + " starts at time " + str(msol[TIME[j]]) + " and uses resource " + str(msol[RESOURCE[j]]))
        print("Last job time ends at " + str(max(msol[TIME[j]] + jobLength[j] for j in range(numJobs))) )
        return True
    else: # Problem is infeasible; print the infeasibility 
        # theConflictsResult = model.refine_conflict()
        # print(theConflictsResult)
        return False 
