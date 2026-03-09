# alphaBeta.py
# prof. lehman
# code generated and slightly modified from chat GPT 4 prompt
# spring 2024, updated number range 2026
#
# creates a tree with x16 child nodes
#
#  

import random

# set random seed ie. will get same set of random numbers
# comment out or change seed to change numbers
random.seed(32)


class Node:
    def __init__(self, depth, is_maximizing_player, value=None):
        self.depth = depth
        self.is_maximizing_player = is_maximizing_player
        self.value = value
        self.children = []
        self.pruned = False

    def add_child(self, child):
        self.children.append(child)

def create_tree(node, current_depth, max_depth=4):
    if current_depth < max_depth:
        node.add_child(create_tree(Node(current_depth + 1, not node.is_maximizing_player), current_depth + 1, max_depth))
        node.add_child(create_tree(Node(current_depth + 1, not node.is_maximizing_player), current_depth + 1, max_depth))
    else:
        
        node.value = random.randint(1, 50)  # Assigning random values at leaf nodes
    return node

def minimax(node, depth, alpha, beta, is_maximizing_player):
    if depth == 0 or node.value is not None:
        return node.value

    if is_maximizing_player:
        max_eval = float('-inf')
        for child in node.children:
            eval = minimax(child, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                for c in node.children[node.children.index(child)+1:]:
                    c.pruned = True
                break
        print("max_eval", max_eval)
        return max_eval
    else:
        min_eval = float('inf')
        for child in node.children:
            eval = minimax(child, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                for c in node.children[node.children.index(child)+1:]:
                    c.pruned = True
                break
        print("     min_eval", min_eval)        
        return min_eval

def print_tree(node, indent="", last=True):
    print(indent, "+- " if last else "|- ", node.value if node.value is not None else "M" if node.is_maximizing_player else "m", " (Pruned)" if node.pruned else "", sep="")
    indent += "   " if last else "|  "
    
    # change to print tree in reverse
    #for i, child in enumerate(node.children):
    for i, child in reversed(list(enumerate(node.children))):    
        last = i == len(node.children) - 1
        print_tree(child, indent, last)

# Create and display the tree
root = create_tree(Node(0, True), 0)
minimax_value = minimax(root, 4, float('-inf'), float('inf'), True)
print("Minimax Value: ", minimax_value)
print("\nTree with Pruned Branches:")
print_tree(root)




