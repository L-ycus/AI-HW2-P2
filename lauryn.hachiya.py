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
        return (heuristic(board), None ,visited)

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

def heuristic():
    return 27

def choose_move(game, state, time_limit):
    moves = game.legal_moves(state)
    alpha = float("-inf")
    beta = float("inf")
    if(len(moves) > 0 ):
        move = minimax_alpha_beta(state, True, alpha, beta, True)
    else:
        move = minimax_alpha_beta(state, True, alpha, beta, False)
    return move 