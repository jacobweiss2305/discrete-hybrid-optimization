# -*- coding: utf-8 -*-
"""
Job shipping and scheduling problem for IP+CP assignment.
Combines a network flow IP with a constraint satisfaction problem.
Network flow problem aims to minimize costs of sending specific jobs to sites.
At each site, must check feasibility of processing those jobs.
Uses lazy constraint callback.  

Requirements: 
 - CPLEX (or other Pyomo-compatible solver)
"""
# Import 
from pyomo.environ import *
from pyomo.opt import *
from pyomo.core import * 

import cplex
from cplex.callbacks import LazyConstraintCallback

import pandas as pd # For importing data from csv files
import os
import sys

from scheduling_subproblem import *

os.chdir(sys.path[0]) # This changes the working directory to directory of this .py file 

# Need to create these as globals, so we can access them within callback code
global numNodes
global totalTime
numNodes = 0
totalTime = 0
numMachines = {}
jobLengths = {}
arcs = []

def importData(supplyDataFileName, worksiteFileName, jobDataFileName, costDataFileName, capacityDataFileName, numNodes):
    # Import data using pandas and return a list containing the data in separate objects 
    print("Reading input data...")
    transshipmentNodes = [*range(1,numNodes+1)] 

    # Supply data (number of jobs at each node)
    theDataFrame = pd.read_csv(supplyDataFileName, header=None) # Use pandas to read the csv 
    numJobs = 1
    supply = {} # For each node, a list of the jobs that come from that site 
    supplyNodes = []
    supplyJobArcs = [] # Arcs between each supply node and its associated jobs
    for i in range(numNodes): # Iterate through each row
        if theDataFrame.values[i] > 0: 
            transshipmentNodes.remove(i+1) # Mark as not a transshipment node
            supplyNodes.append(i+1)
            supply[i+1] = [*range(numJobs, numJobs + int(theDataFrame.values[i]))] # Otherwise, this will return an numpy array
            for k in range(numJobs, numJobs + int(theDataFrame.values[i])):
                supplyJobArcs.append((i+1, k))
            numJobs += int(theDataFrame.values[i])
    numJobs -= 1 # To adjust at end 

    # Worksite data (0 for non-worksites; number of machines for each worksite)
    theDataFrame = pd.read_csv(worksiteFileName, header=None) # Use pandas to read the csv 
    global numMachines
    numMachines = {} # Number of machines at each worksite
    worksiteNodes = []
    for i in range(numNodes): # Iterate through each row
        if theDataFrame.values[i] > 0: 
            transshipmentNodes.remove(i+1) # Mark as not a transshipment node
            worksiteNodes.append(i+1)
            numMachines[i+1] = float(theDataFrame.values[i])

    # Job data, indicating length of job
    theDataFrame = pd.read_csv(jobDataFileName, header=None) # Use pandas to read the csv 
    global jobLengths
    jobLengths = {} 
    for i in range(numJobs): # Iterate through each row
        if theDataFrame.values[i] > 0: 
            jobLengths[i+1] = float(theDataFrame.values[i])

    numTransshipmentNodes = len(transshipmentNodes)
    if numNodes != len(supplyNodes) + len(worksiteNodes) + numTransshipmentNodes:
        print("ERROR: The number of nodes does not sum as expected.")

    # Cost and arc capacity data
    theDataFrameCost = pd.read_csv(costDataFileName, header=None) # Use pandas to read the csv 
    theDataFrameCapacity = pd.read_csv(capacityDataFileName, header=None) 
    costs = {} 
    capacities = {}     
    global arcs
    for i in range(numNodes): # Iterate through each row and column.  
        for j in range(numNodes): 
            if i != j and theDataFrameCost.values[i,j] >= 0 and theDataFrameCapacity.values[i,j] > 0:
                costs[i+1,j+1] = float(theDataFrameCost.values[i,j])
                capacities[i+1,j+1] = float(theDataFrameCapacity.values[i,j])
                if i+1 in supply: # If this is a supply node
                    for k in supply[i+1]: arcs.append((i+1,j+1,k)) # Add index for jobs associated with this supply node
                else: # Not a supply node; add arcs for all jobs 
                    for k in range(1, numJobs+1): arcs.append((i+1,j+1,k)) # Add index for jobs 

    print("Input data read successfully.")
    return [supplyNodes, supplyJobArcs, worksiteNodes, transshipmentNodes, numJobs, supply, numMachines, jobLengths, costs, capacities, arcs]

def objective_rule(model):
    # Create objective function
    return sum(model.costs[i,j] * model.FLOW[i,j,k] for (i,j,k) in model.arcs)

def arcCapacity_rule(model,i,j):
    # Constraint on arc capacity 
    if (i,j) not in model.capacities: # If this isn't an arc, skip it
        return Constraint.Skip
    else:
        return sum(model.FLOW[m,n,k] for (m,n,k) in model.arcs if m== i if n==j) <= model.capacities[i,j]

def eachJobOut_rule(model,i,k):
    # Jobs must come out of each customer (supply) site
    return sum(model.FLOW[m,j,t] for (m,j,t) in model.arcs if m == i if t == k) == 1

def eachJobIn_rule(model,k):
    # Each job must go to a worksite
    return sum(model.FLOW[i,j,t] for (i,j,t) in model.arcs if j in model.worksiteNodes if t == k) == 1

def bof_rule(model,i,k):
    # Balance-of-flow constraints on transshipment nodes
    return sum(model.FLOW[m,j,t] for (m,j,t) in model.arcs if m==i if t==k) - sum(model.FLOW[j,m,t] for (j,m,t) in model.arcs if m==i if t==k) == 0

class cplexLazyConstraintCallback(LazyConstraintCallback):
    # CPLEX lazy constraint callback (this is only enabled when solving using .lp file interface).
    # For each worksite, need to read in current solution, create and solve CSP, and add cuts if current assignment is not feasible.
    def __call__(self):
        print("This is the lazy constraint callback code")
        
        # Reference global values (otherwise, can't access these data inside this callback code)
        global numNodes
        global arcs
        global totalTime
        global numMachines # Dict of number of machines at each worksite
        global jobLengths

        # Create data structure to hold jobs assigned
        jobAssigned = {}
        tempVariableDict = {} # For adding cuts, if needed
        for worksite in numMachines: # Total number of worksites
            jobAssigned[worksite] = [] 
            tempVariableDict[worksite] = [] 

        # Record assigned jobs, by looping over all flow arcs, where j = a worksite.  
        for i,j,k in arcs:
            if j in numMachines: # If this is a worksite
                if self.get_values('FLOW(' + str(i) + '_' + str(j) + '_' + str(k) + ')') == 1: # If this arc is bringing in a job 
                    jobAssigned[j].append(k)
                    tempVariableDict[j].append(('FLOW(' + str(i) + '_' + str(j) + '_' + str(k) + ')'))

        # Loop through each worksite and check feasibilty.
        # If infeasible, add a constraint preventing all of these jobs from being assigned to this node
        for worksite in numMachines:
            numJobs = len(jobAssigned[worksite]) # Number of jobs
            if numJobs > 0:
                availResources = int(numMachines[worksite]) # Number of available machines at this worksite
                theseJobLengths = []
                for job in jobAssigned[worksite]:
                    theseJobLengths.append(jobLengths[job])

                isFeasible = solveSchedulingSubproblem(numJobs, totalTime, availResources, theseJobLengths)
                if not isFeasible: # Scheduling problem was infeasible; add cut
                    print("Infeasible assignment at worksite " + str(worksite) + "; adding cut...")
                    variableList = tempVariableDict[worksite] # Create list of string names of the active variables
                    coefficientList = [1] * len(variableList) # Create list of the coefficients 
                    self.add([variableList,coefficientList], "L", len(variableList)-1) # Add a cut that says at least one of these jobs can't get done
                    print("The variableList is " + str(variableList))
                else:
                    print("Feasible assignment of jobs to machines at worksite " + str(worksite))
            
def solveUsingPyomoCPLEX_LP(supplyDataFileName, worksiteFileName, costDataFileName, capacityDataFileName, jobDataFileName, numNodes, totalTime):
    ''' Create and solve a concrete Pyomo model and CPLEX interface (to allow lazy constraint callbacks) '''

    # Read in data
    supplyNodes, supplyJobArcs, worksiteNodes, transshipmentNodes, numJobs, supply, numMachines, jobLengths, costs, capacities, arcs = \
        importData(supplyDataFileName, worksiteFileName, jobDataFileName, costDataFileName, capacityDataFileName, numNodes) 

    # Create a concrete Pyomo model
    print("Building Pyomo model...")
    model = ConcreteModel() 
    
    # Define indices and sets 
    print("Creating indices and sets...")
    model.i = Set(initialize=[i for i in range(1, numNodes+1)], ordered=True) # Index on each node
    model.k = Set(initialize=[k for k in range(1, numJobs+1)], ordered=True) # Index on each job
    model.supplyNodes = Set(within=model.i, initialize = supplyNodes) # Index on each supply node (customer site)
    model.worksiteNodes = Set(within=model.i, initialize = worksiteNodes) # Index on each worksite node
    model.transshipmentNodes = Set(within=model.i, initialize = transshipmentNodes) # Index on each transshipment node
    model.arcs = Set(within=model.i * model.i * model.k, initialize = arcs) # Create the set of arcs
    model.supplyJobArcs = Set(within=model.i * model.k, initialize=supplyJobArcs) # Arcs between each supply node and its jobs

    # # Define variables
    print("Creating variables...")
    model.FLOW = Var(model.arcs, domain=Binary, initialize = 0) # Flow variable, indicating arc i,j for job k
    
    # Create parameters (i.e., data)
    print("Creating parameters...")
    model.supply = Param(model.supplyNodes, initialize = supply) # For each customer node, a list of the jobs that come from that site 
    model.machines = Param(model.worksiteNodes, initialize = numMachines) # Number of machines at each worksite
    model.costs = Param(model.i * model.i, initialize = costs) # Assumes costs for each job are the same
    model.capacities = Param(model.i * model.i, initialize = capacities) # Total capacity on arc, across all jobs    

     # Create objective function
    print("Creating objective function...")
    model.objective = Objective(rule=objective_rule, sense = minimize)

    print("Creating constraints on arc capacities...")
    model.arcCapacityConstraint = Constraint(model.i, model.i, rule=arcCapacity_rule) 

    print("Creating constraints ensuring each job gets done...")
    model.jobOutConstraint = Constraint(model.supplyJobArcs, rule=eachJobOut_rule)
    model.jobInConstraint = Constraint(model.k, rule=eachJobIn_rule)

    print("Creating balance-of-flow constraints...")
    model.bofConstraint = Constraint(model.transshipmentNodes, model.k, rule=bof_rule) 

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
    print("The objective value is: " + str(results.get_objective_value()))
    amountSent = [0] * numNodes
    amountReceived = [0] * numNodes
    for i,j,k in model.arcs:
        theFlow = results.get_values("FLOW(" + str(i) + "_" + str(j) + "_" + str(k)+ ")") 
        if(theFlow) > 0: # If there is flow on this arc
            print("Job " + str(k) + " went from node " + str(i) + " to node " +str(j))
            amountSent[i-1] += theFlow
            amountReceived[j-1] += theFlow
    for i in model.supplyNodes: print("Node " +str(i) + " sent " + str(amountSent[i-1] - amountReceived[i-1]) + " jobs.")
    for i in model.worksiteNodes: print("Node " +str(i) + " received " + str(amountReceived[i-1] - amountSent[i-1]) + " jobs.")

#### Specify data files and run above code
## Small Dataset
supplyDataFileName = "data/supplyDataSmall.csv" # Total number of jobs that come out of each customer site
worksiteFileName = "data/worksiteDataSmall.csv" # Number of machines, at each worksite
costDataFileName = "data/costDataSmall.csv" # Per-unit shipping costs on each arc, for each job 
capacityDataFileName = "data/capacityDataSmall.csv" # Total arc capacities (over all jobs)
jobDataFileName = "data/jobDataSmall.csv" 
numNodes = 12
totalTime = 6 # For small dataset, 4 seems to be lower bound 

## Medium Dataset
# supplyDataFileName = "data/supplyDataMedium.csv" # Total number of jobs that come out of each customer site
# worksiteFileName = "data/worksiteDataMedium.csv" # Number of machines, at each worksite
# costDataFileName = "data/costDataMedium.csv" # Per-unit shipping costs on each arc, for each job 
# capacityDataFileName = "data/capacityDataMedium.csv" # Total arc capacities (over all jobs)
# jobDataFileName = "data/jobDataMedium.csv" 
# numNodes = 100
# totalTime = 9 #9 seems to be infeasible (5000 sec, 27 user cuts). 10 worked 17 user cuts, 3887 secs; 12 worked, 17 user cuts, 2058 seconds

solveUsingPyomoCPLEX_LP(supplyDataFileName, worksiteFileName, costDataFileName, capacityDataFileName, jobDataFileName, numNodes, totalTime) # Run above code 