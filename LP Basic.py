# -*- coding: utf-8 -*-
"""
Created on Wed Apr 04 20:50:06 2018

@author: jweiss
"""

import numpy as np
from pulp import *

c= np.array([0,1,0,0,1,1])
b= np.matrix([[1,1,1,0,0,0],[0,0,0,1,1,1],[1,0,0,1,0,0],[0,1,0,0,1,0],[0,0,1,0,0,1]])
D= np.array([1,0,0,0,0,1])
x1= [10,10,0,0,10,10]
x2= [0,10,10,10,10,0]  
ctx1 = np.dot(c,x1)
ctx2 = np.dot(c,x2)
Dx1 = np.dot(D,x1)
Dx2 = np.dot(D,x2)

B = np.matrix([[20,0],[1,1]])
B_inv = np.linalg.inv(B)
cost = np.array([30,20])
dual = np.dot(B_inv,cost)
dual
 
ax = np.dot(1.5,D)
c-ax

#
##Optimizer
#prob = LpProblem('MP', LpMinimize)
#
##Decision Variables
#x1 = LpVariable("x1")
#x2 = LpVariable("x2")
#x3 = LpVariable("x3")
#x4 = LpVariable("x4")
#x5 = LpVariable("x5")
#x6 = LpVariable("x6")
#
##Objective Function
#prob += -1.5*x1 + 1*x2 + 0*x3 + 0*x4 + 1*x5 - .5*x6 
#
#prob += 1*x1 + 1*x2 + 1*x3 + 0*x4 + 0*x5 + 0*x6 == 20
#prob += 0*x1 + 0*x2 + 0*x3 + 1*x4 + 1*x5 + 1*x6 == 20
#prob += 1*x1 + 0*x2 + 0*x3 + 1*x4 + 0*x5 + 0*x6 == 10
#prob += 0*x1 + 1*x2 + 0*x3 + 0*x4 + 1*x5 + 0*x6 == 20
#prob += 0*x1 + 0*x2 + 1*x3 + 0*x4 + 0*x5 + 1*x6 == 10



L1 = LpVariable("L1")
L2 = LpVariable("L2")
L3 = LpVariable("L3")
prob = LpProblem('MP', LpMinimize)
prob += 30*L1 + 0*L2 + 20*L3
prob += 30*L1 + 0*L2 - 10*L3 <= 12
prob += L1 + L2 + L3 == 1
prob += L1 >= 0
prob += L2 >= 0
prob += L3 >= 0


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
print("Total:")
for var in prob.variables():
    print(str(var).replace('Ticker_','')+" "+str(var.varValue))




