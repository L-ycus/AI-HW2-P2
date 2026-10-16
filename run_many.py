"""
Headless batch runner: play many games between two agents and report a
win/draw/loss tally -- no browser needed.

    python3 run_many.py --w agent_jordan.smith.py --b random --games 10
    python3 run_many.py --w random --b agent_jordan.smith.py --games 10

--w/--b each take a file path, or one of: "random", "greedy". ("human"
isn't valid here -- use match_viewer.py instead.)

--w always plays W, --b always plays B for the whole run -- no color
swap within one invocation. Run it twice with --w/--b swapped to get a
color-balanced sample (White moves first, so this matters).
"""
import argparse
import time

import match_runner
from fanorona import FanoronaGame
from match_viewer import resolve_agent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--w", required=True, help='"random", "greedy", or a path to a submitted agent file')
    parser.add_argument("--b", required=True, help="same choices as --w")
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--time-limit", type=float, default=5.0, help="seconds each agent gets per move")
    parser.add_argument("--max-plies", type=int, default=2000, help="hard per-game ply cap, should basically never fire")
    parser.add_argument("--max-plies-without-capture", type=int, default=match_runner.MAX_PLIES_WITHOUT_CAPTURE,
                         help="course draw rule: declare a draw after this many plies with no capture")
    args = parser.parse_args()

    if args.w == "human" or args.b == "human":
        parser.error('"human" isn\'t valid here -- there\'s no browser to click in. Use match_viewer.py instead.')

    agent_w, label_w = resolve_agent(args.w)
    agent_b, label_b = resolve_agent(args.b)
    game = FanoronaGame()

    results = {"W": 0, "B": 0, None: 0}
    total_violations = []
    ply_counts = []

    print(f"W = {label_w}, B = {label_b}, time limit = {args.time_limit}s/move, {args.games} game(s)")
    t_start = time.time()
    for i in range(args.games):
        result = match_runner.run_match(game, agent_w, agent_b, time_limit=args.time_limit,
                                          label_w=label_w, label_b=label_b, max_plies=args.max_plies,
                                          max_plies_without_capture=args.max_plies_without_capture)
        results[result["winner"]] += 1
        ply_counts.append(result["plies"])
        if result["violations"]:
            total_violations.append((i, result["violations"]))
        if result["winner"] is not None:
            tag = f"{result['winner']} wins"
        elif result["ended_by"] == "no_capture_rule":
            tag = "draw (no capture rule)"
        else:
            tag = "draw (max plies reached -- worth a look)"
        print(f"  game {i + 1}/{args.games}: {tag} ({result['plies']} plies"
              f"{', ' + str(len(result['violations'])) + ' violation(s)' if result['violations'] else ''})")

    elapsed = time.time() - t_start
    print()
    print(f"{args.games} games -- W={label_w} vs B={label_b}:")
    print(f"  W wins: {results['W']}   draws: {results[None]}   B wins: {results['B']}")
    print(f"  average game length: {sum(ply_counts) / len(ply_counts):.0f} plies")
    print(f"  total time: {elapsed:.1f}s ({elapsed / args.games:.2f}s/game)")
    if total_violations:
        print(f"\n  {sum(len(v) for _, v in total_violations)} rule violation(s) across "
              f"{len(total_violations)} game(s) -- worth a look before giving credit for this matchup:")
        for game_idx, viols in total_violations:
            for v in viols:
                print(f"    game {game_idx + 1}, ply {v['ply']} ({v['agent']}): {v['reason'].splitlines()[0]}")


if __name__ == "__main__":
    main()
