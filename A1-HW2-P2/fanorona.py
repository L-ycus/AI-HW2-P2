"""
Fanorona (the standard 5x9 "Fanorona Tsivy" variant) as a Game.

Board: 5 rows (0-4) x 9 columns (0-8) = 45 intersections. Every point is
connected to its orthogonal neighbors (N/S/E/W). A point is ALSO
connected to its diagonal neighbors (NE/NW/SE/SW), but only if
(row + col) is even -- this is what gives a real Fanorona board its
alternating-diamond look, and it's not optional/cosmetic: diagonal
capture lines only exist where diagonal movement lines exist.

State is (board, player, chain):
  - board: a tuple of 5 tuples of 9 characters each, 'W' / 'B' / '.'.
    Immutable and hashable, same convention as every Problem state in
    Phase 1-3.
  - player: 'W' or 'B' -- whose turn it is.
  - chain: None if the player to move is starting a fresh turn, or a
    ChainContext if they are mid-capture-chain and may choose to
    continue capturing with the SAME piece or stop. This is what makes
    "go again" visible to search: current_player(state) stays the same
    across a chain (see apply_move), so a MinimaxAgent has to check
    whose turn it actually is at each node rather than assuming strict
    alternation by tree depth -- the same idea taught with Mancala's
    extra-turn rule, just with an explicit choice (stop or continue)
    instead of an unconditional extra turn.

Move is either:
  - a single Step(from_pos, to_pos, captured) namedtuple -- one leg, and
  - captured: a tuple of (row, col) positions removed by this leg (empty
    tuple for a non-capturing move).
  - the sentinel STOP -- only legal when chain is not None, meaning
    "end my turn here instead of continuing to capture with this piece."

Rules encoded here (standard Fanorona rules -- see
https://en.wikipedia.org/wiki/Fanorona):
  - Approach capture: moving from A to B captures every enemy piece in
    the straight line starting immediately beyond B, in the direction of
    the move, up to (not including) the first empty point or the edge.
  - Withdrawal capture: moving from A to B captures every enemy piece in
    the straight line starting immediately beyond A, in the direction
    OPPOSITE the move.
  - A single leg can never be both an approach and a withdrawal capture
    at once -- if both are available, the player picks one (that's two
    separate legal Moves here, not one Move with a sub-choice).
  - Capturing is mandatory: if ANY capturing move is available anywhere
    on the board for the player to move, non-capturing (paika) moves are
    not legal this turn. (This only applies to the FIRST leg of a turn --
    once you've captured once, continuing is always optional.)
  - After a capturing leg, the same piece may continue capturing by
    moving again, provided the next leg (a) is itself a capture, (b)
    does not revisit a point already visited this turn, and (c) is not
    in the same direction as the leg just played. The player may also
    choose to stop after any capturing leg -- that choice is the STOP
    move above, always legal whenever chain is not None, even if no
    legal continuation exists either.

Not modeled: the traditional draw-by-repetition rule. A game here always
ends when the player to move has no legal moves (they lose) -- see
is_terminal. Worth knowing before relying on this for a very long
human-vs-human game that repeats positions.
"""
from collections import namedtuple

from game import Game

ROWS = 5
COLS = 9

Step = namedtuple("Step", ["from_pos", "to_pos", "captured"])
ChainContext = namedtuple("ChainContext", ["piece_pos", "visited", "last_direction"])


class _Stop:
    def __repr__(self):
        return "STOP"


STOP = _Stop()  # a dedicated sentinel, never equal to any Step

_ORTHOGONAL = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_DIAGONAL = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def _in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS


def _directions(r, c):
    """Every direction a piece at (r, c) can move in or capture along."""
    if (r + c) % 2 == 0:
        return _ORTHOGONAL + _DIAGONAL
    return list(_ORTHOGONAL)


def _opponent(player):
    return "B" if player == "W" else "W"


def _line_of_enemies(board, r, c, dr, dc, player):
    """Positions of the contiguous run of `player`'s enemies starting at
    (r+dr, c+dc) and continuing in direction (dr, dc), stopping at the
    first empty point or the edge. Empty tuple if (r+dr, c+dc) itself is
    off-board, empty, or a friendly piece (i.e. no capture this way)."""
    enemy = _opponent(player)
    positions = []
    rr, cc = r + dr, c + dc
    while _in_bounds(rr, cc) and board[rr][cc] == enemy:
        positions.append((rr, cc))
        rr += dr
        cc += dc
    return tuple(positions)


def _set(board, pos, value):
    """A new board with board[pos] = value -- board is an immutable
    tuple of tuples, so this rebuilds the one row that changed."""
    r, c = pos
    row = board[r]
    new_row = row[:c] + (value,) + row[c + 1:]
    return board[:r] + (new_row,) + board[r + 1:]


def _apply_step(board, step, player):
    board = _set(board, step.from_pos, ".")
    board = _set(board, step.to_pos, player)
    for pos in step.captured:
        board = _set(board, pos, ".")
    return board


def _first_leg_moves(board, player):
    """Every legal way to START a turn: single Steps only, one leg deep.
    If any capturing leg exists anywhere on the board, only capturing
    legs are legal (mandatory capture); otherwise every non-capturing
    (paika) leg is legal."""
    capturing_moves = []
    paika_moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != player:
                continue
            for dr, dc in _directions(r, c):
                dest_r, dest_c = r + dr, c + dc
                if not _in_bounds(dest_r, dest_c) or board[dest_r][dest_c] != ".":
                    continue
                approach = _line_of_enemies(board, dest_r, dest_c, dr, dc, player)
                withdrawal = _line_of_enemies(board, r, c, -dr, -dc, player)
                if not approach and not withdrawal:
                    paika_moves.append(Step((r, c), (dest_r, dest_c), ()))
                    continue
                for captured in (approach, withdrawal):
                    if captured:
                        capturing_moves.append(Step((r, c), (dest_r, dest_c), captured))
    return capturing_moves if capturing_moves else paika_moves


def _continuation_moves(board, player, chain):
    """Every legal way to continue (or stop) a capture chain already in
    progress. STOP is always included -- stopping is legal after any
    capturing leg, even if no further continuation exists."""
    moves = [STOP]
    r, c = chain.piece_pos
    for dr, dc in _directions(r, c):
        if (dr, dc) == chain.last_direction:
            continue  # can't continue straight in the same direction
        dest_r, dest_c = r + dr, c + dc
        if not _in_bounds(dest_r, dest_c) or board[dest_r][dest_c] != ".":
            continue
        if (dest_r, dest_c) in chain.visited:
            continue  # can't revisit a point already used this turn
        approach = _line_of_enemies(board, dest_r, dest_c, dr, dc, player)
        withdrawal = _line_of_enemies(board, r, c, -dr, -dc, player)
        for captured in (approach, withdrawal):
            if captured:
                moves.append(Step((r, c), (dest_r, dest_c), captured))
    return moves


class FanoronaGame(Game):

    def initial_state(self):
        # Row 0-1: Black, solid. Row 3-4: White, solid. Row 2 (middle):
        # strictly alternating B/W with the true center (col 4) empty --
        # NOT grouped and NOT mirror-symmetric around the center. Pixel-
        # verified against the reference diagram at
        # https://www.mindsports.nl/index.php/the-pit/528-fanorona
        # (fanorona_inpos.gif) rather than guessed, since a plausible-
        # looking but wrong middle row changes which opening captures
        # exist. 22 pieces per side.
        board = (
            ("B",) * COLS,
            ("B",) * COLS,
            ("B", "W", "B", "W", ".", "B", "W", "B", "W"),
            ("W",) * COLS,
            ("W",) * COLS,
        )
        return (board, "W", None)

    def current_player(self, state):
        return state[1]

    def legal_moves(self, state):
        board, player, chain = state
        if chain is not None:
            return _continuation_moves(board, player, chain)
        return _first_leg_moves(board, player)

    def apply_move(self, state, move):
        board, player, chain = state
        if move is STOP:
            return (board, _opponent(player), None)
        new_board = _apply_step(board, move, player)
        if not move.captured:
            # a non-capturing (paika) leg always ends the turn immediately
            return (new_board, _opponent(player), None)
        # a capturing leg -- same player continues, may choose to stop next
        if chain is None:
            visited = {move.from_pos, move.to_pos}
        else:
            visited = chain.visited | {move.to_pos}
        direction = (move.to_pos[0] - move.from_pos[0], move.to_pos[1] - move.from_pos[1])
        new_chain = ChainContext(move.to_pos, visited, direction)
        return (new_board, player, new_chain)

    def is_terminal(self, state):
        return len(self.legal_moves(state)) == 0

    def winner(self, state):
        # The player to move with no legal moves loses.
        return _opponent(self.current_player(state))

    def render(self, state):
        board, player, chain = state
        lines = ["    " + " ".join(str(c) for c in range(COLS))]
        for r in range(ROWS):
            lines.append(f"row {r}: " + " ".join(board[r]))
        if chain is None:
            lines.append(f"to move: {player}")
        else:
            lines.append(f"to move: {player} (mid-chain at {chain.piece_pos}, may continue or stop)")
        return "\n".join(lines)
