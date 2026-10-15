"""
Runs one Fanorona match between any two agents -- a submitted
`choose_move` function, a built-in agent, or a human (see
match_viewer.py).

Draw rule: official Fanorona rules only describe a draw abstractly
("neither side can force a win"), so this is a *course* rule instead:
if MAX_PLIES_WITHOUT_CAPTURE plies pass with no capture, it's a draw.

Agent contract: a Python file defining

    def choose_move(game, state, time_limit):
        ...
        return move  # one of game.legal_moves(state)

`time_limit` is a float, seconds. If choose_move doesn't return within
that time, raises, or returns something that isn't a currently-legal
move, the offending agent FORFEITS THAT MOVE ONLY: the harness substitutes
a uniformly random legal move, logs exactly what went wrong, and the
match continues. One bad move doesn't end the game -- see run_match's
`violations` in its return value for anything an instructor should look
at before assigning credit for a given match.
"""
import importlib.util
import random
import signal
import sys
import time
import traceback

from fanorona import STOP

# Course rule: We picked MAX_PLIES_WITHOUT_CAPTURE to be 1000 
# based on data we collected over 100 games.
MAX_PLIES_WITHOUT_CAPTURE = 1000

_AGENT_COUNTER = 0


class AgentTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise AgentTimeout("agent exceeded its time limit")


def load_agent(path):
    """Load a student's submitted file as an isolated module (a unique
    name each call, so two submissions can both be loaded in the same
    process without one's module-level globals clobbering the other's)
    and return its choose_move function."""
    global _AGENT_COUNTER
    _AGENT_COUNTER += 1
    module_name = f"_submitted_agent_{_AGENT_COUNTER}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "choose_move"):
        raise ValueError(f"{path} does not define a choose_move function")
    return module.choose_move


def random_agent(game, state, time_limit):
    """A built-in baseline: picks uniformly among legal moves. Ignores
    time_limit entirely -- it's always instant."""
    return random.choice(game.legal_moves(state))


def make_safe_agent(choose_move_fn, label):
    """Wrap a raw choose_move function so it NEVER raises and ALWAYS
    returns a legal move -- any failure (timeout, exception, illegal
    move) is logged and replaced with a random legal move instead.

    Returns (safe_fn, violations); violations entries have "ply" and
    "reason"."""
    violations = []

    def safe_fn(game, state, time_limit, ply):
        legal = game.legal_moves(state)
        old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
        signal.setitimer(signal.ITIMER_REAL, time_limit)
        try:
            move = choose_move_fn(game, state, time_limit)
        except AgentTimeout:
            violations.append({
                "ply": ply, "agent": label, "reason":
                f"exceeded the {time_limit}s time limit",
            })
            move = None
        except Exception:
            violations.append({
                "ply": ply, "agent": label, "reason":
                "raised an exception:\n" + traceback.format_exc(),
            })
            move = None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)

        if move is None or move not in legal:
            if move is not None:
                violations.append({
                    "ply": ply, "agent": label, "reason":
                    f"returned a move that isn't currently legal: {move!r}",
                })
            move = random.choice(legal)
        return move

    return safe_fn, violations


def run_match(game, agent_w, agent_b, time_limit=5.0, label_w="W", label_b="B",
               max_plies=2000, max_plies_without_capture=MAX_PLIES_WITHOUT_CAPTURE):
    """Play one full game. agent_w/agent_b are raw choose_move functions
    (game, state, time_limit) -> move -- wrap a student's file with
    load_agent() first, or pass random_agent, or any other built-in.

    Returns a dict: {"winner": ..., "plies": N, "violations": [...],
    "ended_by": "no_legal_moves" | "no_capture_rule" | "max_plies_reached"}."""
    # label_w/label_b are just cosmetic names for the violation log.
    safe_w, violations_w = make_safe_agent(agent_w, label_w or "W")
    safe_b, violations_b = make_safe_agent(agent_b, label_b or "B")
    agents = {"W": safe_w, "B": safe_b}

    state = game.initial_state()
    ply = 0
    plies_since_capture = 0
    while not game.is_terminal(state):
        if ply >= max_plies:
            return {
                "winner": None, "plies": ply,
                "violations": violations_w + violations_b,
                "ended_by": "max_plies_reached",
            }
        if plies_since_capture >= max_plies_without_capture:
            return {
                "winner": None, "plies": ply,
                "violations": violations_w + violations_b,
                "ended_by": "no_capture_rule",
            }
        player = game.current_player(state)  # "W" or "B"
        move = agents[player](game, state, time_limit, ply)
        state = game.apply_move(state, move)
        ply += 1
        if move is not STOP and move.captured:
            plies_since_capture = 0
        else:
            plies_since_capture += 1

    return {
        "winner": game.winner(state), "plies": ply,
        "violations": violations_w + violations_b,
        "ended_by": "no_legal_moves",
    }
