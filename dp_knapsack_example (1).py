# -*- coding: utf-8 -*-
"""
Code to solve the 0-1 knapsack problem using a dynamic programming approach.
Example from Dynamic Programming lecture.  
Data provided in slides

"""
# Import 
import numpy as np

numItems = 4
sackSize = 5

itemWeight = [0,2,3,4,5] # 0th item is placeholder, to allow one-based indexing
itemValue = [0,3,4,5,6]

valueTable = np.zeros((numItems+1,sackSize+1), dtype=np.int32) # Create array of zeros

# 0-1 dynamic programming knapsack algorithm
for i in range(1,numItems+1): # For each item
    for w in range(0,sackSize+1): # For each amount of space remaining
        if itemWeight[i] <= w: # Item can fit
            if itemValue[i] + valueTable[i-1, w-itemWeight[i]] > valueTable[i-1,w]: # if this item should be included
                valueTable[i,w] = itemValue[i] + valueTable[i-1, w-itemWeight[i]] # Save as value
            else: # Item shouldn't be included
                valueTable[i,w] = valueTable[i-1, w] # Carry forward previous solution without this item
        else: # Item can't fit
            valueTable[i,w] = valueTable[i-1, w] # Carry forward previous solution without this item

# Obtain solution from table
i = numItems
k = sackSize
sackContents = [] # Items that are selected
totalValue = 0
totalWeight = 0
while i > 0 and k > 0:
    if valueTable[i,k] != valueTable[i-1,k]:
        sackContents.append(i)
        totalValue = totalValue + itemValue[i]
        totalWeight = totalWeight + itemWeight[i]
        i -= 1
        k = k - itemWeight[i]
    else:
        i -= 1
sackContents.sort() # Sort smallest to largest

# Print results
print("The completed table is:")
print(valueTable)

print("The selected items are: ")
print(sackContents)
print("Total value: " + str(totalValue))
print("Total weight: " +str(totalWeight)) 