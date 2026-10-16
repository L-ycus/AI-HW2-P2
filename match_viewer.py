"""
Watch two Fanorona agents play each other (or a human vs. an agent, or
two humans) in a browser. Run with, e.g.:

    python3 match_viewer.py --w path/to/alice_agent.py --b random
    python3 match_viewer.py --w human --b greedy

--w/--b each take a file path, or one of: "human", "random", "greedy".
("baseline" parses but isn't available to you -- see resolve_agent.)

Built on play_web.py's GameSession -- human turns work exactly as they
do there; MatchSession.step_ai() handles an AI's turn the same way, so
the frontend auto-steps whenever it's an AI's move.
"""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

import greedy_agent
import match_runner
from fanorona import FanoronaGame, STOP, ROWS, COLS
from play_web import GameSession, PLAYER_NAME

PORT = 8001


def resolve_agent(spec):
    """spec is "human", "random", "greedy", "baseline", or a file path.
    Returns (choose_move_or_None, label) -- None means human.

    "baseline" isn't part of the given packet -- instructor-only."""
    if spec == "human":
        return None, "human"
    if spec == "random":
        return match_runner.random_agent, "random"
    if spec == "greedy":
        return greedy_agent.choose_move, "greedy (prefers captures, no search)"
    if spec == "baseline":
        try:
            import baseline_agent
        except ImportError:
            parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
            sys.path.insert(0, parent_dir)
            try:
                import baseline_agent
            except ImportError:
                raise SystemExit(
                    "\"baseline\" isn't available here -- it's an instructor-only "
                    "opponent, not part of the given packet. Use \"random\" or "
                    "\"greedy\" instead, or point --w/--b at a file.")
        return baseline_agent.choose_move, "baseline (depth 2, material only)"
    return match_runner.load_agent(spec), os.path.basename(spec)


class MatchSession(GameSession):

    def __init__(self, agent_w, agent_b, time_limit, label_w, label_b):
        self.time_limit = time_limit
        self.label_w, self.label_b = label_w, label_b
        self.raw_agent_w, self.raw_agent_b = agent_w, agent_b
        super().__init__()

    def restart(self):
        super().restart()
        self.ply = 0
        self.violations = []
        self.plies_since_capture = 0
        self.drawn_by_rule = False
        self.safe_w, viol_w = (
            match_runner.make_safe_agent(self.raw_agent_w, self.label_w)
            if self.raw_agent_w is not None else (None, None))
        self.safe_b, viol_b = (
            match_runner.make_safe_agent(self.raw_agent_b, self.label_b)
            if self.raw_agent_b is not None else (None, None))
        self._violation_lists = [v for v in (viol_w, viol_b) if v is not None]

    def _record_capture_tracking(self, captured):
        """Course no-capture-draw rule -- applies to human or AI moves."""
        if captured:
            self.plies_since_capture = 0
        else:
            self.plies_since_capture += 1
        if self.plies_since_capture >= match_runner.MAX_PLIES_WITHOUT_CAPTURE:
            self.drawn_by_rule = True

    def _play(self, step):
        super()._play(step)
        self._record_capture_tracking(bool(step.captured))

    def is_ai_turn(self):
        if self.game.is_terminal(self.state):
            return False
        player = self.game.current_player(self.state)
        safe_fn = self.safe_w if player == "W" else self.safe_b
        return safe_fn is not None

    def step_ai(self):
        """If it's an AI's turn, get its move and apply it the same way
        a human click would. No-op otherwise."""
        if self.drawn_by_rule or not self.is_ai_turn() or self.pending_choice is not None:
            return False
        player = self.game.current_player(self.state)
        safe_fn = self.safe_w if player == "W" else self.safe_b
        move = safe_fn(self.game, self.state, self.time_limit, self.ply)
        self.violations = sorted(
            (v for lst in self._violation_lists for v in lst),
            key=lambda v: v["ply"])
        if move is STOP:
            super().end_turn()  # bypass this class's own end_turn() guard below
            self._record_capture_tracking(False)
        else:
            self._play(move)  # tracks capture/no-capture internally
        self.ply += 1
        return True

    def click(self, pos):
        if self.drawn_by_rule or self.is_ai_turn():
            return
        super().click(pos)

    def choose(self, index):
        if self.drawn_by_rule or self.is_ai_turn():
            return
        super().choose(index)

    def end_turn(self):
        # step_ai() bypasses this via super().end_turn() directly, so
        # it's safe to just block here whenever it's an AI's turn.
        if self.drawn_by_rule or self.is_ai_turn():
            return
        super().end_turn()
        self._record_capture_tracking(False)

    def to_json(self):
        data = super().to_json()
        data["label_w"] = self.label_w
        data["label_b"] = self.label_b
        data["is_ai_turn"] = self.is_ai_turn()
        data["violations"] = self.violations
        data["drawn_by_rule"] = self.drawn_by_rule
        if self.drawn_by_rule:
            # Real Fanorona state isn't actually terminal -- this is the
            # no-capture rule calling it a draw instead.
            data["terminal"] = True
            data["winner"] = None
        return data


def build_page():
    from play_web import PAGE as BASE_PAGE
    # The draw() override must land BEFORE the page's final
    # fetch(...).then(draw) call, which captures draw by reference at
    # that point -- inserting it too late would leave the first render
    # unpatched.
    extra_html = """
<div id="violations" style="max-width:640px;margin:10px auto;text-align:left;font-size:13px;color:#a33;"></div>
"""
    extra_js = """
function renderViolations(data) {
  const el = document.getElementById("violations");
  if (!data.violations || data.violations.length === 0) { el.textContent = ""; return; }
  el.innerHTML = "<b>Rule violations this game (logged, move was replaced with a random legal one):</b><br>" +
    data.violations.map(v => `ply ${v.ply} (${v.agent}): ${v.reason.split("\\n")[0]}`).join("<br>");
}

function annotateDrawByRule(data) {
  if (!data.drawn_by_rule) return;
  statusEl.textContent += "\\n\\n(Called a draw: no capture in __MAX_PLIES_WITHOUT_CAPTURE__ " +
    "plies -- a course rule, not an official Fanorona rule. See match_runner.py.)";
}

let autoStepTimer = null;

function maybeAutoStep(data) {
  if (autoStepTimer) { clearTimeout(autoStepTimer); autoStepTimer = null; }
  if (data.terminal) return;
  if (data.is_ai_turn) {
    autoStepTimer = setTimeout(() => post("/api/step"), 400);
  }
}

const _origDraw = draw;
draw = function(data) {
  _origDraw(data);
  renderViolations(data);
  annotateDrawByRule(data);
  maybeAutoStep(data);
};
""".replace("__MAX_PLIES_WITHOUT_CAPTURE__", str(match_runner.MAX_PLIES_WITHOUT_CAPTURE))
    anchor = 'statusEl.textContent = lines.join("\\n");\n}'
    page = BASE_PAGE.replace("<div id=\"choices\"></div>",
                              "<div id=\"choices\"></div>\n" + extra_html)
    assert anchor in page, "draw() closing anchor not found -- did play_web.py's draw() change shape?"
    page = page.replace(anchor, anchor + "\n" + extra_js)
    return page


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--w", required=True, help='"human", "random", "greedy", or a path to a submitted agent file')
    parser.add_argument("--b", required=True, help='same choices as --w')
    parser.add_argument("--time-limit", type=float, default=5.0, help="seconds each agent gets per move")
    args = parser.parse_args()

    agent_w, label_w = resolve_agent(args.w)
    agent_b, label_b = resolve_agent(args.b)

    session = MatchSession(agent_w, agent_b, args.time_limit, label_w, label_b)
    page = build_page()

    class Handler(BaseHTTPRequestHandler):

        def _send_json(self, obj):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                body = page.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/state":
                self._send_json(session.to_json())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {}

            if self.path == "/api/click":
                session.click((payload.get("r"), payload.get("c")))
            elif self.path == "/api/choose":
                session.choose(payload.get("index"))
            elif self.path == "/api/end_turn":
                session.end_turn()
            elif self.path == "/api/restart":
                session.restart()
            elif self.path == "/api/step":
                session.step_ai()
            else:
                self.send_response(404)
                self.end_headers()
                return
            self._send_json(session.to_json())

        def log_message(self, format, *args):
            pass

    print(f"W = {label_w}, B = {label_b}, time limit = {args.time_limit}s/move")
    print(f"Match viewer running at http://localhost:{PORT}  (Ctrl+C to stop)")
    HTTPServer(("localhost", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
