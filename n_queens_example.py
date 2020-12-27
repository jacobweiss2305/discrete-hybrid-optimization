# --------------------------------------------------------------------------
# This is a modified version of the n-queens code provided with IBM Optimization Studio. 
# Original source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
The eight queens puzzle is the problem of placing eight chess queens on an 8x8
chessboard so that no two queens threaten each other. Thus, a solution requires
that no two queens share the same row, column, or diagonal.

The eight queens puzzle is an example of the more general n-queens problem of
placing n queens on an nxn chessboard, where solutions exist for all natural
numbers n with the exception of n=2 and n=3.

See https://en.wikipedia.org/wiki/Eight_queens_puzzle for more information.

Please refer to documentation for appropriate setup of solving configuration.
"""

from docplex.cp.model import CpoModel
from sys import stdout

# Set model parameters
NB_QUEEN = 8 # Number of queens 

# Create a CPO model
model = CpoModel()

# Create column index of each queen
# Arguments: size, domain_min, domain_max, name
# That is, create NB_QUEEN integer variables that take on a value between 0 and NB_QUEEN
# The value indicates the row of that ith column with a queen 
x = model.integer_var_list(NB_QUEEN, 0, NB_QUEEN - 1, "X") 

# One queen per row
model.add(model.all_diff(x))

# Queens cannot be the same number of columns apart as they are rows apart
for i in range(NB_QUEEN):
    for j in range(NB_QUEEN):
        if i != j: 
            model.add(model.abs(i-j) != model.abs(x[i] - x[j]))

# Solve model
print("Solving model....")
msol = model.solve(TimeLimit=10)

# Print solution
if msol: # If the model ran successfully, it returns True 
    stdout.write("Solution:")
    for v in x:
        stdout.write(" {}".format(msol[v])) # Write out the solution (i.e., the row for each column)
    stdout.write("\n")
    # Draw chess board
    for r in range(NB_QUEEN): # Iterate over each row
        for c in range(NB_QUEEN):
            stdout.write(" ")
            stdout.write("Q" if r == msol[x[c]] else ".") # If there is a queen assigned to this r/c, print Q
        stdout.write("\n")
else:
    stdout.write("Solve status: {}\n".format(msol.get_solve_status()))
