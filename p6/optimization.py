import random
import math

# optimization.py
# prof. lehman
# spring 2024
#
# code used to demonstrate hill climbing for optimization for CS362
#
# The code simulates a scenario where there are five cities (shown with C)
# and two cell towers.  One of the cell towers (7,14) has a fixed location.
# The second cell tower should be placed at a location that minimizes
# the distance to each city.
#

# display world
def printWorld( temp, tw ):
    
    print("  ", end="")
    for c in range(0, numCols):
        print( f"{c%10:2d}", end="" )
    print()

    for r in range(0, len(temp)):
        print( f"{r:2d} ", end="" )
        
        for c in range(0, len(temp[r])):
                if (r,c) in tw:
                    print( "T", end=" " )
                else:
                    print( temp[r][c], end=" " )
        print()
    print()
    
# return distance between two tuples (a,b) <-> (c,d)
# also called the "Hamming distance"
def getDistance( start, stop ):
    
    # extract values from tuple
    a,b = start
    c,d = stop
    
    rowDistance = abs(a-c)
    colDistance = abs(b-d)
    return rowDistance + colDistance

# return minimum distace for one city to any tower
def getMinimumDistance( myLocation, allLocations ):
    
    # store distances to all locations
    distances = []
    for location in allLocations:
        d = getDistance( myLocation, location )    
        distances.append( d )
    
    return min( distances )
    
# return sum distances for all cities to closest tower
def getSumMinimumDistance( myCities, myTowers ):
    
    total = 0
    
    for city in myCities:
        total += getMinimumDistance( city, myTowers )
        
    return total


# perform hill climbing search for best 2nd tower location
def hill_climb_second_tower(start_location, cities, fixed_tower, numRows, numCols):
    
    current = start_location
    current_towers = [fixed_tower, current]
    current_value = getSumMinimumDistance(cities, current_towers)
    
    while True:
        r, c = current
        
        # 4-neighborhood: up, down, left, right (within bounds)
        neighbors = []
        if r > 0:
            neighbors.append((r - 1, c))
        if r < numRows - 1:
            neighbors.append((r + 1, c))
        if c > 0:
            neighbors.append((r, c - 1))
        if c < numCols - 1:
            neighbors.append((r, c + 1))
        
        best_neighbor = current
        best_value = current_value
        
        # evaluate neighbors
        for nr, nc in neighbors:
            towers = [fixed_tower, (nr, nc)]
            value = getSumMinimumDistance(cities, towers)
            if value < best_value:
                best_value = value
                best_neighbor = (nr, nc)
                print( "better:", nr, nc, value  )
        
        # if no neighbor is better, we are at a local minimum
        if best_neighbor == current:
            break
        
        # move to better neighbor and repeat
        current = best_neighbor
        current_value = best_value
    
    return current, current_value

# ****************************************************
# ************************* main *********************
# ****************************************************

random.seed(12)
    
# create grid as nested list
grid = []
numRows = 10
numCols = 30
for r in range(0, numRows):
    newRow = []
    for c in range(0, numCols):
        newRow.append( "." )
    grid.append( newRow)

# city locations - hard coded - DO NOT CHANGE
cities = [ (2,3), (5,2), (5,8), (5,24), (5,27) ]

# place cities in grid
for city in cities:
    r,c = city # get data from tuple
    grid[r][c] = "C"

# place towers
towers = []

towers = [(7,14)]


# *** modify second point to test one placement of second tower
start_second_tower = (4,25)
towers = [(7,14), start_second_tower]

print( "cities: ", cities )
print( "towers: ", towers )
print()

printWorld( grid, towers )

value = getSumMinimumDistance( cities, towers )
print( f"total distance = {value}" )
print()



# run hill climbing from chosen starting location
fixed_tower = (7,14)
final_loc, final_value = hill_climb_second_tower(start_second_tower, cities, fixed_tower, numRows, numCols)
print(f"hill climbing start location = {start_second_tower}")
print(f"hill climbing final location  = {final_loc}")
print(f"hill climbing total distance  = {final_value}")
print()


# *** following code maps all possible solutions for second tower ***

# determine best placement for 2nd tower by
# calculating placement results for second tower at all positions
print("Cost for all locations for 2nd tower")

# print index for column headings
print("   ", end="")
for c in range(0, numCols):
    print( f"{c%10:3d}", end="" )
print()
    
# calculate and print total distance for placement of 2nd tower
for r in range(0, numRows):
    print( f"{r:3d}", end="" )
    for c in range(0, numCols):
        towers = [(7,14)] # First tower at fixed location 7,14
        location = (r,c)
        towers.append(location) #set towers to one location r,c
        
        value = getSumMinimumDistance( cities, towers )
        print( f"{value:3d}", end="" )
    print()