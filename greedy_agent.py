"""
A built-in test opponent: prefers a move that captures the most pieces,
otherwise moves randomly. No search, no lookahead -- not a worked
example of how to structure a minimax search.
"""
import random


def choose_move(game, state, time_limit):
    moves = game.legal_moves(state)
    captured_counts = [getattr(m, "captured", ()) for m in moves]
    best = max((len(c) for c in captured_counts), default=0)
    if best == 0:
        return random.choice(moves)
    best_moves = [m for m, c in zip(moves, captured_counts) if len(c) == best]
    return random.choice(best_moves)
