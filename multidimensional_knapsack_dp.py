# -*- coding: utf-8 -*-
"""
Code to solve the 0-1 multidimensional knapsack problem using a dynamic programming approach.
Three dimensions: money, linear (one dimensional space), and time.
Data provided in slides

"""
# Import 
import numpy as np

numItems = 20
sackSizeMoney = 17
sackSizeWeight = 20
sackSizeTime = 30

itemMoney = [0,2,3,4,5,4,3,2,1,5,4,4,6,9,4,3,6,4,6,2,4] # 0th item is placeholder, to allow one-based indexing
itemWeight =[0,1,3,3,5,6,4,2,4,6,3,5,6,4,3,2,4,3,4,3,4]
itemTime =  [0,2,4,4,5,7,3,4,6,7,3,6,3,5,6,4,6,7,4,6,4]
itemValue = [0,4,3,6,7,4,3,8,4,3,5,3,5,3,5,3,6,3,4,2,1]

valueTable = np.zeros((numItems+1,sackSizeMoney+1,sackSizeWeight+1,sackSizeTime+1), dtype=np.int32) # Create array of zeros


# 0-1 dynamic programming knapsack algorithm
for i in range(1,numItems+1): # For each item
    for w in range(0,sackSizeMoney+1): # For each amount of space remaining 
        for x in range(0,sackSizeWeight+1): 
            for y in range(0,sackSizeTime+1): # For each amount of space remaining 
                if itemMoney[i] <= w and itemWeight[i] <= x and itemTime[i] <= y: # Item can fit
                    if itemValue[i] + valueTable[i-1, w-itemMoney[i],  x-itemWeight[i],  y-itemTime[i]] > valueTable[i-1,w,x,y]: # if this item should be included
                        valueTable[i,w,x,y] = itemValue[i] + valueTable[i-1, w-itemMoney[i],  x-itemWeight[i],  y-itemTime[i]] # Save as new value
                    else: # Item shouldn't be included
                        valueTable[i,w,x,y] = valueTable[i-1, w,x,y] # Carry forward previous solution without this item
                else: # Item can't fit
                    valueTable[i,w,x,y] = valueTable[i-1, w,x,y] # Carry forward previous solution without this item

# Obtain solution from table
i = numItems
w = sackSizeMoney
x = sackSizeWeight
y = sackSizeTime
sackContents = [] # Items that are selected
totalValue = 0
totalMoney = 0
totalWeight = 0
totalTime = 0 
while i > 0 and w > 0 and x > 0 and y > 0:
    if valueTable[i,w,x,y] != valueTable[i-1,w,x,y]:
        sackContents.append(i)
        totalValue += itemValue[i]
        totalMoney += itemMoney[i]
        totalWeight += itemWeight[i]
        totalTime += itemTime[i]
        i -= 1
        w = w - itemWeight[i]
        x = x - itemTime[i]
        y = y - itemMoney[i]
    else:
        i -= 1
sackContents.sort() # Sort smallest to largest

# Print results
# print("The completed table is:")
# print(valueTable)

print("The selected items are: ")
print(sackContents)
print("Total value: " + str(totalValue))
print("Total money: " + str(totalMoney)) 
print("Total weight: " + str(totalWeight)) 
print("Total time: " + str(totalTime)) 
print("")


'''
SOLUTIONS
PART 1
1.  The state variables now are the amount of remaining money, weight, and time.
2.  The runtime is now O(nWMT), where n is the number of items, and W, M, and T are respectively the maxes of the weight, money, and time values.  

PART 2
There is more than one way to approach this problem.  An extension of the above multidimensional knapsack would be something like the following:

State variables: A set of variables that describes the size and orientation of a contiguous block of available (open) space.  
    The state variables need to account for all of the unusual (non-rectangular) shapes that could occur.

Action: The selection, position, and orientation of an item.

Stages: As in our earlier problems, a stage would represent an action from a given state (one for each box).

This problem suffers from state space explosion: Unlike the traditional knapsack, we must consider the location and orientation of each of the shapes.
This generates a lot more sub-problems to be solved, and reduces the gains to be had from dynamic programming.
Further, the vast majority of combinations we will explore in a complete dynamic programming approach would be of little or no practical use,
as we would never encounter them or select them as part of an optimal solution.  One would want to explore other methods of representing and 
approximating the problem to overcome this (and much research has gone into this problem). 

'''