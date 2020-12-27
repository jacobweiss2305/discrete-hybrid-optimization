# -*- coding: utf-8 -*-
"""
Created on Tue Mar 20 20:16:21 2018

@author: jweiss
"""

#------------------------------------------------------------------------------
#Using PuLP
import pandas as pd
from pulp import *

#Optimizer
prob = LpProblem('Treasury Island', LpMaximize)

#Decision Variables
x = LpVariable("x", lowBound = None, upBound = 0)
y = LpVariable("y",lowBound = None, upBound = 0)

#Objective Function
prob += 700*x + 700*y
prob += (-2-(4*x - 4*y)) <= 0
prob += (-1-(x - 2*y)) <= 0
prob += (-4-(2*x - y)) <= 0
prob += (-15-(3*x - 5*y)) <= 0


#Solution
prob.solve()
for v in prob.variables():
    print(v.name, "=", v.varValue)



if prob.solve() == 1:
    print("Feasible Optimal Solution") 
elif prob.solve() == -1:
    print("Error: Infeasible Solution")
elif prob.solve() is not 1 or -1:
    print("Error: Unbounded or Not Optimal")
    
print("---------The solution to this Treasury Island problem is----------")
print("Total Tickers:")
for var in prob.variables():
    print(str(var).replace('Ticker_','')+" "+str(var.varValue))
        
