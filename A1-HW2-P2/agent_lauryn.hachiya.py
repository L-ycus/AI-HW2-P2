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


def minimax_alpha_beta(game, state, depth, maximizing, alpha=float("-inf"), beta=float("inf"), root_player=None):
    """Minimax with alpha-beta pruning. Same (value, visited) contract
    as minimax() above -- but visited must NOT include anything pruned."""
    if(root_player is None):
        return None

    board = state[0]
    player = state[1]
    chain = state[2]

    visited = [board]
    #if Terminal-Test
    if depth == 0 or game.is_terminal(state):
        #return Utility
        ret =  heuristic(board, root_player)
        return (ret, None , visited)

    best_move = None
    #if it's MAX

    if(maximizing):
        #v = -inf
        max_val = float('-inf')
        #for each a in Actions
        for child in game.legal_moves(state):
            next_state = game.apply_move(state, child)

            #if the next move has the same player as the current one (MAX), keep as maximizing
            if game.current_player(next_state) == game.current_player(state):
                temp_val, best, child_visited = minimax_alpha_beta(game, next_state, depth-1, True, alpha, beta, root_player)
            else:
                temp_val, best, child_visited = minimax_alpha_beta(game, next_state, depth-1, False, alpha, beta, root_player)

            #updating values
            if(temp_val > max_val):
                max_val = temp_val
                best_move = child
            visited.extend(child_visited)

            #pruning
            if max_val >= beta:
                return (max_val, best_move, visited)
            alpha = max(alpha, max_val)
        return (max_val, best_move, visited)
    else:
        min_val = float('inf')
        for child in game.legal_moves(state):
            next_state = game.apply_move(state, child)

             #if the next move has the same player as the current one (MIN), keep maximizing as false
            if game.current_player(next_state) == game.current_player(state):
                temp_val, best, child_visited = minimax_alpha_beta(game, next_state, depth-1, False, alpha, beta, root_player)
            else:
                temp_val, best, child_visited = minimax_alpha_beta(game, next_state, depth-1, True, alpha, beta, root_player)
            
            #min_val = min(temp_val, min_val)
            if(temp_val < min_val):
                min_val = temp_val
                best_move = child
            visited.extend(child_visited)
            
            if min_val <= alpha:
                return (min_val, best_move, visited)
            beta = min(beta, min_val)
        
        return (min_val, best_move, visited)
    #raise NotImplementedError("TODO: implement minimax_alpha_beta")

#counts how many pieces you have on strong intersections - opponent on strong intersections
#only called for root player
def heuristic(board, player):
    #print("DEBUGGING board", board)
    board_eval = 0
    for r in range(5):
        for c in range(9):
            tile = board[r][c]
            if tile == ".":
                continue
            if (r % 2) == (c % 2):
                board_eval+=1
            if tile == player:
                board_eval+=1
    return board_eval
    


def choose_move(game, state, time_limit):
    #moves = game.legal_moves(state)
    #heuristic(state[1])
    alpha = float("-inf")
    beta = float("inf")
    
    best_val, best_move, visited = minimax_alpha_beta(game, state, 5, True, alpha, beta, state[1])
  
    #state[1] is the player we're rooting on
    #print("DEBUGGING: ", state[1], ": ", best_val, best_move)
    return best_move 
