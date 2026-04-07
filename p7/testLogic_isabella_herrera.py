#        file: testLogic.py
#        date: March 9, 2026
#        name: Isabella Herrera

# description: The idea of this code is to recreate the game Clue. 
# The main idea of the game is to find who is the killer, the weapon and the room
# The code used the knowledge of each "round" to determine which cards the player has and which cards other players have.



from logic import *

# People
peacock = Symbol("Peacock")
orchid = Symbol("Orchid")
green = Symbol("Green")
plum = Symbol("Plum")

# Weapons
lead_pipe = Symbol("Lead Pipe")
wrench = Symbol("Wrench")
dagger = Symbol("Dagger")
revolver = Symbol("Revolver")

# Places
hall = Symbol("Hall")
studio = Symbol("Studio")
kitchen = Symbol("Kitchen")
ballroom = Symbol("Ballroom")

# These are the cards I got at the beginning of the game
knowledge = And(
    Not(green),
    Not(wrench),
    Not(kitchen)
)

# TURN 1
# I asked: Peacock, dagger, Hall
# Player 2 showed: Hall

knowledge = knowledge.add((Not(hall)))

# TURN 2
# Player 2 asked: Orchid, Wrench, Kitchen
# Player 3 showed: ??

knowledge = knowledge.add(Or(Not(orchid), Not(wrench), Not(kitchen)))

# TURN 3
# Player 3 asked: Plum, lead pipe, Kitchen
# I showed: Kitchen

knowledge = knowledge.add(Not(kitchen), Or(Not(plum), Not(lead_pipe)))

# TURN 4
# I asked: Plum, Revolver, Studio
# No one showed anything

knowledge = knowledge.add((plum))
knowledge = knowledge.add((revolver))
knowledge = knowledge.add((studio)) 

# Check the logic for all of the symbols to see if we can determine who the killer is, the weapon and the room
symbols = [
    peacock, orchid, green, plum,
    lead_pipe, wrench, dagger, revolver,
    hall, studio, kitchen, ballroom
]

print()
print( knowledge.formula() )
print()

# Itinerates through all the symbols and checks if the knowledge entails that symbol. If it does, it prints it out as a possible solution.
for symbol in symbols:
    if model_check(knowledge, symbol):
        print(symbol)


