# MinesKnowlegeModel_Lehman.py
# prof. lehman
# spring 2024 (updated class examples spring 2026)
# CS 262 AI and Machine Learning
#
# Knowledge model to determine mine locations
# and locations to open
#
# Code iterates through knowlege model simpifying model
# by identifying mines, and spaces that are clear to open
# progam iterates until no further knowledge can be derived
#
# Project idea based on project description from
#   https://cs50.harvard.edu/ai/2024/projects/1/minesweeper/
#
# Code written by hand (no AI) except for lookup for how to
# convert lists to sets
#
# Knowledge model uses Python dictionary
# storing list of cells and count
# - one entry for each number (unless there are duplicates)
# - cells must be listed in alphabetical order
#

# knowledge model
km = {}


# Sample Board and Knowlege Model
# Sample #1
"""
km["a,b"] = 2
km["a,b,c"] = 2
km["b,c,d,e,f"] = 1
km["e,f,g"] = 1
km["f,g"] = 1

"""
# -------------------------------------------------------

# Example 2

"""

km["a,b,e,d"] = 1
km["b,c,e,f,g"] = 1
km["d,e,h"] = 1
km["d,e,g,h,i"] = 1
km["h,g,i"] = 1
km["f,g,i,j"] = 1

"""
# -------------------------------------------------------

# Example 3

#"""
# Knowledge number 1
km["a,c"] = 1
km["a,c,e"] = 1
km["c,e,i,h,g"] = 2
km["g,h"] = 1

#We know that e is empty so we try it again 

#"""


mines = []
clear = []

print( "--- start ---" )
print( "mines: ", mines )
print( " open: ", clear )
print( "   km: ", km )
print()

changes = True
round = 1

while changes == True:
   
    print(f"--- round: {round} ---")
    
    changes = False
    
    new_mines = []
    new_clear = []
    new_km = {}
          
    # process all items in knowledge model
    for key, value in km.items():
               
        # get key and convert to list
        temp = key.split(",")
        
        # not a mine, can open spot
        if value == 0:    
            for i in temp:
                new_clear.append( i )
            changes = True
        
        # is a mine
        elif len(temp) == value:
            for i in temp:
                new_mines.append( i )
            changes = True
            
        else:
            # not a mine or open spot
            
            # remove mines
            for m in mines:
                if m in temp:
                    temp.remove(m)
                    changes = True
                    value = value - 1
            
            # remove values not mines
            for c in clear:
                if c in temp:
                    temp.remove(c)
                    changes = True
            
            # if update adjust key
            if changes == True:
                new_key = ""
                for i in temp:
                    new_key = new_key+str(i) + ","
                key = new_key[:-1] #remove last ,
             
            # save sentence
            if len(key) > 0:
                new_km[key] = value
               
    # check for subsets in knowledge model
    for key1, value1 in km.items():
        for key2, value2 in km.items():
            if key1 != key2:
                s1 = set(key1.split(","))
                s2 = set(key2.split(","))
                
                if s1.issubset(s2):
                    changes = True
                    new_set = s2 - s1
                    new_list = list(new_set)
                    new_list.sort()
                    new_key = ""
                    for i in new_list:
                        new_key = new_key+str(i) + ","
                    new_key = new_key[:-1]
                    new_value = value2 - value1
                    new_km[ new_key ] = new_value
                    #print( f"{s2} - {s1}  {new_key} => {new_value}" )
                    
    # update mines list
    for m in new_mines:
        if m not in mines:
            mines.append(m)
            
    # update clear list
    for c in new_clear:
        if c not in clear:
            clear.append(c)
    
    # update km
    km = new_km
    
    round = round + 1
    
    #loop
  
    # indented to see how knowledge model changes each round
    # undent this section to limit output to final answer
    print()
    print( "mines: ", mines )
    print( " open: ", clear )
    print( "   km: ", km )
    print()

