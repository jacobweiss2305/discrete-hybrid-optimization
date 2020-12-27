# -*- coding: utf-8 -*-
"""
Simple CP problem that schedules jobs on a machine, ensuring available resources aren't overused 

Requirements: 
 - CPLEX (or other Pyomo-compatible solver)
"""

# Import 
from docplex.cp.model import CpoModel
from docplex.cp.solution import CpoRefineConflictResult
from sys import stdout

# Input data
numJobs = 10 # Number of jobs
totalTime = 15 # Total time blocks
availResources = 2 # Total amount of resource available for this machine.  Assume each job uses one resource
jobLength = [1,2,3,4,5,1,1,2,2,2] # The length (in time blocks) of each job

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

# Add specific constraints
model.add(TIME[3] < TIME[2]) # Job 4 must start before job 3
model.add(model.min(TIME[j] for j in range(numJobs)) == 0) # The first job must start at time 0
model.add(RESOURCE[4] != RESOURCE[5]) # Jobs 5 and 6 must use different resources

# Add objective function to end as early as possible 
# This line is optional; without it, this is the original constraint satisfaction problem.
# May require more than 10 seconds of runtime.
model.add(model.minimize(model.max(TIME[j] + jobLength[j] for j in range(numJobs))))

# Solve model
print("Solving model....")
msol = model.solve(TimeLimit=100)

if msol: # If the model ran successfully, it returns True 
    print("Solution:")
    for j in range(numJobs):
        print("Job " + str(j) + " starts at time " + str(msol[TIME[j]]) + " and uses resource " + str(msol[RESOURCE[j]]))
    print("Last job time ends at " + str(max(msol[TIME[j]] + jobLength[j] for j in range(numJobs))) )
else: # Problem is infeasible; print the infeasibility 
   theConflictsResult = model.refine_conflict()
   print(theConflictsResult)


""" RESULTS
Without objective function:
    Job 0 starts at time 8 and uses resource 0
    Job 1 starts at time 13 and uses resource 1
    Job 2 starts at time 9 and uses resource 0
    Job 3 starts at time 2 and uses resource 0
    Job 4 starts at time 0 and uses resource 1
    Job 5 starts at time 14 and uses resource 0
    Job 6 starts at time 6 and uses resource 1
    Job 7 starts at time 10 and uses resource 1
    Job 8 starts at time 8 and uses resource 1
    Job 9 starts at time 6 and uses resource 0
    Last job time ends at 15

With objective function:
    Job 0 starts at time 6 and uses resource 1
    Job 1 starts at time 5 and uses resource 0
    Job 2 starts at time 2 and uses resource 0
    Job 3 starts at time 0 and uses resource 1
    Job 4 starts at time 7 and uses resource 1
    Job 5 starts at time 9 and uses resource 0
    Job 6 starts at time 10 and uses resource 0
    Job 7 starts at time 7 and uses resource 0
    Job 8 starts at time 4 and uses resource 1
    Job 9 starts at time 0 and uses resource 0
    Last job time ends at 12
"""