import ast
import sys
import fanorona


def load_tree(path):
    with open(path) as f:
        return ast.literal_eval(f.read().strip())


def is_leaf(node):
    return isinstance(node, tuple)


def name_of(node):
    return node[0]


def children_of(node):
    return list(node[1:])


def minimax(node, maximizing=True):
    """Plain minimax, no pruning. See the module docstring for the
    exact (value, visited) contract."""
    visited = [name_of(node)]

    if is_leaf(node): #if it's a tuple -> terminal
        return (node[1], visited)


    #if it's MAX
    if(maximizing):
        max_val = float('-inf')
        for child in children_of(node):
            temp_val, child_visited = minimax(child, False)
            max_val = max(temp_val, max_val)
            visited.extend(child_visited)
        return (max_val, visited)
    else:
        min_val = float('inf')
        for child in children_of(node):
            
            temp_val, child_visited = minimax(child, True)
            min_val = min(temp_val, min_val)
            visited.extend(child_visited)
        return (min_val, visited)
    #raise NotImplementedError("TODO: implement minimax")


def minimax_alpha_beta(game, state, depth, maximizing=True, alpha=float("-inf"), beta=float("inf"), continue_turn = False):
    """Minimax with alpha-beta pruning. Same (value, visited) contract
    as minimax() above -- but visited must NOT include anything pruned."""
    board, player, chain = state
    visited = [board]
    #if Terminal-Test
    if depth == 0 or state.is_terminal(game, state):
        #return Utility
        return (heuristic(board, player), None ,visited)

    best_move = None
    #if it's MAX
    if(maximizing):
        #v = -inf
        max_val = float('-inf')
        #for each a in Actions
        for child in state.legal_moves(game, state):
            next_state = game.apply_move(game, state, child)

            #if the next move has the same player as the current one (MAX), keep as maximizing
            if state.current_player(game, next_state) == state.current_player(game, state):
                temp_val, best, child_visited = minimax_alpha_beta(game, next_state, depth-1, True, alpha, beta, continue_turn)
            else:
                temp_val, best, child_visited = minimax_alpha_beta(game, next_state, depth-1, False, alpha, beta, continue_turn)

            #updating values
            if(temp_val > max_val):
                max_val = temp_val
                best_move = best
            visited.extend(child_visited)

            #pruning
            if max_val >= beta:
                return (max_val, best_move, visited)
            alpha = max(alpha, max_val)
        return (max_val, best_move, visited)
    else:
        min_val = float('inf')
        for child in state.legal_moves(game, state):
            next_state = game.apply_move(game, state, child)

             #if the next move has the same player as the current one (MIN), keep maximizing as false
            if state.current_player(game, next_state) == state.current_player(game, state):
                temp_val, best, child_visited = minimax_alpha_beta(game, next_state, depth-1, False, alpha, beta, continue_turn)
            else:
                temp_val, best, child_visited = minimax_alpha_beta(game, next_state, depth-1, True, alpha, beta, continue_turn)
            
            #min_val = min(temp_val, min_val)
            if(temp_val < min_val):
                min_val = temp_val
                best_move = best
            visited.extend(child_visited)
            
            if min_val <= alpha:
                return (min_val, best_move, visited)
            beta = min(beta, min_val)
        return (min_val, best_move, visited)
    #raise NotImplementedError("TODO: implement minimax_alpha_beta")

#counts how many pieces you have on strong intersections - opponent on strong intersections
def heuristic(board, player):
    #print("DEBUGGING board", board)
    board_eval = 0
    for r in range(4):
        if(r % 2 == 0): # r = 0, 2, 4
            for c in range(4): #c = 2, 4, 6, 8
                if(board[r][(c+1)*2] == player):
                    board_eval += 1
                else:
                    board_eval -= 1
                
        else: # r = 1, 3
            for c in range(4): #c = 1, 3, 5, 7
                if(board[r][(c)*2+1] == player):
                    board_eval+= 1
                else:
                    board_eval -= 1

    return board_eval

def choose_move(game, state, time_limit):
    #moves = game.legal_moves(state)
    heuristic(state[1])
    alpha = float("-inf")
    beta = float("inf")
    best_val, best_move, visited = minimax_alpha_beta(game, state, 10, True, alpha, beta, True)
  
    return best_move 
