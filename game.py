"""
The Game interface. This is the two-player-game analogue of Phase 1-3's
Problem interface: it's the ONLY thing generic game-playing code (search
agents, the arena runner) knows about -- it never looks at what a state
"is," only that these methods exist and behave as documented below.

A concrete game (like FanoronaGame) subclasses this and fills in every
method. Nothing here is game-specific, and nothing game-specific belongs
in generic code that talks to a Game.

State: must be hashable and immutable (a tuple, a frozenset, a plain
value, ... -- not a list or dict). This lets search agents use states as
dictionary keys the same way Phase 1-3's Problem states could.

Move: opaque to everything except the Game itself. An agent that calls
legal_moves() gets back a list of Move objects and picks one -- it never
needs to construct a Move by hand or know what's inside it.
"""


class Game:

    def initial_state(self):
        """Return the starting state."""
        raise NotImplementedError

    def current_player(self, state):
        """Return whose turn it is to move in this state (e.g. 'W' or
        'B')."""
        raise NotImplementedError

    def legal_moves(self, state):
        """Return a list of every legal Move for the player to move in
        this state. If this list is empty, the game is over (see
        is_terminal) -- there is no "pass" move in this interface."""
        raise NotImplementedError

    def apply_move(self, state, move):
        """Return the new state that results from the player to move
        playing `move` (one of the Move objects legal_moves(state) just
        returned -- not something built from scratch). Does not modify
        `state` in place."""
        raise NotImplementedError

    def is_terminal(self, state):
        """Return True if the game is over in this state."""
        raise NotImplementedError

    def winner(self, state):
        """Only called when is_terminal(state) is True. Return the
        winning player (same kind of value current_player() returns), or
        None for a draw."""
        raise NotImplementedError

    def render(self, state):
        """Return a human-readable string showing the board. Used by
        HumanAgent and by the arena runner between moves -- purely for
        display, never used by search code."""
        raise NotImplementedError
