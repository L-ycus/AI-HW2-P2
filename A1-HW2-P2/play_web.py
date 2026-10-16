"""
Two humans play Fanorona with a point-and-click board, in a browser. Run
with: python3 play_web.py, then open http://localhost:8000

Standard library only (http.server) -- nothing to install, and no
dependency on tkinter (which isn't available in every Python install).
The browser is a thin rendering/click layer; the Python server holds the
one authoritative game state and is the only thing that calls into
fanorona.py, so the game rules being exercised are exactly the same,
already-verified FanoronaGame -- nothing about the rules is reimplemented
in JavaScript.

Interaction: click one of your own pieces, then click a highlighted
point to move. If the same piece can keep
capturing, the newly-highlighted points let you continue the chain, and
"End turn" is enabled as soon as stopping is legal (right after any
capturing leg) -- it's labeled "End turn," not "Confirm move," because
there's no way to un-confirm a leg already played; it just ends your
turn where you are. If stopping is the only thing you could possibly
do (no further captures available), the turn ends on its own -- no
button to click for something that was never actually a choice.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from fanorona import FanoronaGame, STOP, ROWS, COLS

PORT = 8000
PLAYER_NAME = {"W": "White", "B": "Black"}


class GameSession:
    """Thin UI-state wrapper around a FanoronaGame. self.state is always
    the real, already-applied game state -- every leg (and every STOP) is
    a genuine call to game.apply_move, not a provisional/undoable draft
    the way it was when a whole capture chain was one atomic Move. The
    only things tracked here beyond self.state are pure UI conveniences:
    which piece is currently selected (before any leg of a fresh turn has
    been played), and a running record of this turn's path/captures so
    far, purely for drawing a trail -- fanorona.py itself is what decides
    whether a chain can continue or must stop (via legal_moves() on the
    current state)."""

    def __init__(self):
        self.game = FanoronaGame()
        self.restart()

    def restart(self):
        self.state = self.game.initial_state()
        self.selected = None
        self.pending_choice = None
        self.turn_path = []
        self.turn_captured = set()

    def chain(self):
        return self.state[2]

    def legal_moves(self):
        return self.game.legal_moves(self.state)

    def active_piece(self):
        """The piece the player is currently moving -- either the one
        they clicked (before taking any leg this turn) or, once mid-chain,
        the piece fanorona.py itself is tracking."""
        chain = self.chain()
        return chain.piece_pos if chain is not None else self.selected

    def selectable_pieces(self):
        return {m.from_pos for m in self.legal_moves() if m is not STOP}

    def destinations(self):
        """to_pos -> list of Steps, for the currently active piece only.
        Normally one Step per destination, but a single piece can have
        both an approach AND a withdrawal capture landing on the SAME
        square with DIFFERENT pieces captured -- then there are two Steps
        for that one destination, and the player has to pick which (see
        pending_choice)."""
        active = self.active_piece()
        if active is None:
            return {}
        options = {}
        for m in self.legal_moves():
            if m is not STOP and m.from_pos == active:
                options.setdefault(m.to_pos, []).append(m)
        return options

    def potential_captures(self):
        """Enemy pieces capturable by the ACTIVE piece's very next move --
        nothing at all before a piece is selected (every capturable piece
        on the board lighting up before you've even picked which piece to
        move is noisy, not useful), and only this one piece's targets
        once selected or mid-chain."""
        active = self.active_piece()
        if active is None:
            return set()
        captured = set()
        for m in self.legal_moves():
            if m is not STOP and m.from_pos == active:
                captured.update(m.captured)
        return captured

    def click(self, pos):
        if self.game.is_terminal(self.state):
            return
        pos = tuple(pos)

        if self.pending_choice is not None:
            # any new click abandons an open approach/withdrawal choice --
            # same "click elsewhere" logic already used to deselect a
            # piece, no separate Cancel button needed. Clicking the exact
            # same destination again just reopens the same choice.
            self.pending_choice = None

        if self.chain() is None and self.selected is None:
            if pos in self.selectable_pieces():
                self.selected = pos
            return

        if self.chain() is None and pos == self.selected:
            self.selected = None
            return

        dest_options = self.destinations()
        if pos in dest_options:
            steps = dest_options[pos]
            if len(steps) == 1:
                self._play(steps[0])
            else:
                self.pending_choice = steps

    def choose(self, index):
        """Resolve an ambiguous destination -- the player picked which of
        pending_choice's captures they meant."""
        if self.pending_choice is None or not (0 <= index < len(self.pending_choice)):
            return
        step = self.pending_choice[index]
        self.pending_choice = None
        self._play(step)

    def _play(self, step):
        """Actually apply one leg -- a real move, immediately, unlike the
        old design where a leg was only provisional until end_turn()."""
        if self.chain() is None:
            self.turn_path = [step.from_pos]
            self.turn_captured = set()
        self.turn_path.append(step.to_pos)
        self.turn_captured.update(step.captured)
        self.state = self.game.apply_move(self.state, step)
        self.selected = None
        if self.chain() is None:
            # a non-capturing (paika) leg ends the turn immediately --
            # there's no chain to show a trail for
            self.turn_path = []
            self.turn_captured = set()
        elif self.legal_moves() == [STOP]:
            # STOP is the only legal option -- not a real choice, so don't
            # make the player click just to confirm something that was
            # never in question. (When there IS a real choice -- STOP vs.
            # at least one continuation -- End Turn stays a genuine,
            # explicit decision; see the module docstring.)
            self.end_turn()

    def end_turn(self):
        """Play the STOP move -- only legal, and only meaningful, while
        mid-chain. Unlike the old design, this is a real Game move now,
        not just a UI action that commits an already-decided sequence."""
        if self.chain() is None:
            return
        self.state = self.game.apply_move(self.state, STOP)
        self.turn_path = []
        self.turn_captured = set()

    def to_json(self):
        board, player, chain = self.state
        terminal = self.game.is_terminal(self.state)
        winner = self.game.winner(self.state) if terminal else None
        active = self.active_piece()
        return {
            "board": [list(row) for row in board],
            "player": player,
            "player_name": PLAYER_NAME[player],
            "current_pos": list(active) if active else None,
            "selectable": [list(p) for p in self.selectable_pieces()] if active is None else [],
            "destinations": [list(p) for p in self.destinations()],
            "potential_captures": [list(p) for p in self.potential_captures()],
            "chain_path": [list(p) for p in self.turn_path],
            "captured_this_turn": [list(p) for p in self.turn_captured],
            "captured_so_far": len(self.turn_captured),
            "pending_choice": (
                [{"to_pos": list(s.to_pos), "captured": [list(p) for p in s.captured]}
                 for s in self.pending_choice]
                if self.pending_choice is not None else None
            ),
            "can_end_turn": chain is not None and self.pending_choice is None,
            "in_chain": chain is not None,
            "num_legal_moves": len(self.legal_moves()),
            "terminal": terminal,
            "winner": PLAYER_NAME[winner] if winner else None,
        }


session = GameSession()

PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Fanorona</title>
<style>
  body { font-family: Helvetica, Arial, sans-serif; text-align: center; background: #f0ece0; }
  h1 { margin-top: 20px; }
  canvas { background: #d9c9a3; border-radius: 6px; margin-top: 10px; cursor: pointer; }
  #status { font-size: 16px; margin: 12px auto; max-width: 500px; white-space: pre-line; }
  button { font-size: 14px; padding: 6px 14px; margin: 4px; }
</style>
</head>
<body>
<h1>Fanorona</h1>
<canvas id="board" width="640" height="360"></canvas>
<div id="status"></div>
<div id="choices"></div>
<div>
  <button id="endturn">End turn</button>
  <button id="restart">Restart game</button>
</div>
<script>
const MARGIN = 40, SPACING = 70, RADIUS = 22, ROWS = %(rows)d, COLS = %(cols)d;
const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
let current = null;

function xy(r, c) { return [MARGIN + c * SPACING, MARGIN + r * SPACING]; }

function nearestPoint(x, y) {
  let best = null, bestDist = 25;
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const [px, py] = xy(r, c);
    const d = Math.hypot(px - x, py - y);
    if (d < bestDist) { best = [r, c]; bestDist = d; }
  }
  return best;
}

function hasPos(list, r, c) {
  return list.some(p => p[0] === r && p[1] === c);
}

function draw(data) {
  current = data;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#5a4b30";
  ctx.font = "12px Helvetica";
  ctx.textAlign = "center";
  for (let c = 0; c < COLS; c++) {
    const [x] = xy(0, c);
    ctx.fillText("col " + c, x, MARGIN - 20);
  }
  ctx.textAlign = "right";
  for (let r = 0; r < ROWS; r++) {
    const [, y] = xy(r, 0);
    ctx.fillText("row " + r, MARGIN - 15, y + 4);
  }
  ctx.textAlign = "center";
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const dirs = [[0,1],[1,-1],[1,0],[1,1]];
    for (const [dr, dc] of dirs) {
      if ((r + c) %% 2 !== 0 && dr !== 0 && dc !== 0) continue;
      const rr = r + dr, cc = c + dc;
      if (rr >= 0 && rr < ROWS && cc >= 0 && cc < COLS) {
        const [x1, y1] = xy(r, c), [x2, y2] = xy(rr, cc);
        ctx.strokeStyle = "#8a7a55"; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      }
    }
  }
  // Trail connecting every square the moving piece has occupied this
  // turn, so a continuing chain visibly reads as one piece's journey.
  if (data.chain_path && data.chain_path.length > 1) {
    ctx.strokeStyle = "#d6a24a";
    ctx.lineWidth = 3;
    ctx.setLineDash([6, 5]);
    ctx.beginPath();
    data.chain_path.forEach((p, i) => {
      const [x, y] = xy(p[0], p[1]);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.setLineDash([]);
  }

  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const [x, y] = xy(r, c);
    const piece = data.board[r][c];
    const isCaptured = hasPos(data.captured_this_turn, r, c);
    const isCurrent = data.current_pos && data.current_pos[0] === r && data.current_pos[1] === c;

    if (hasPos(data.destinations, r, c)) {
      ctx.beginPath(); ctx.arc(x, y, RADIUS + 5, 0, 2*Math.PI);
      ctx.strokeStyle = "#2e8b57"; ctx.lineWidth = 3; ctx.stroke();
    } else if (hasPos(data.selectable, r, c)) {
      ctx.beginPath(); ctx.arc(x, y, RADIUS + 5, 0, 2*Math.PI);
      ctx.strokeStyle = "#4a7fd6"; ctx.lineWidth = 2; ctx.stroke();
    }
    // Potential captures: an enemy piece still at risk from continuing
    // the current selection. Skip it if the piece is already marked
    // captured-this-turn -- it's not "at risk" anymore, it's taken.
    if ((piece === "W" || piece === "B") && !isCaptured && hasPos(data.potential_captures, r, c)) {
      ctx.beginPath(); ctx.arc(x, y, RADIUS + 9, 0, 2*Math.PI);
      ctx.strokeStyle = "#c0392b"; ctx.lineWidth = 3; ctx.setLineDash([4, 3]);
      ctx.stroke(); ctx.setLineDash([]);
    }
    if (piece === "W" || piece === "B") {
      ctx.beginPath(); ctx.arc(x, y, RADIUS, 0, 2*Math.PI);
      if (isCaptured) {
        // Taken this turn -- still drawn (not erased) but recolored to a
        // dull, washed-out version of its own color, so it reads as
        // "marked for removal" rather than a live piece.
        ctx.fillStyle = piece === "W" ? "#cdbfa8" : "#7a7a7a";
      } else {
        ctx.fillStyle = piece === "W" ? "#f5f0e6" : "#2b2b2b";
      }
      if (isCurrent) ctx.globalAlpha = 0.5;  // mid-move, not yet settled
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = isCurrent ? "#d6a24a" : (isCaptured ? "#c0392b" : "#2b2b2b");
      ctx.lineWidth = isCurrent ? 4 : 2;
      ctx.stroke();
    } else {
      ctx.beginPath(); ctx.arc(x, y, 3, 0, 2*Math.PI);
      ctx.fillStyle = "#8a7a55"; ctx.fill();
    }
  }

  document.getElementById("endturn").disabled = !data.can_end_turn;

  const choicesEl = document.getElementById("choices");
  choicesEl.innerHTML = "";
  if (data.pending_choice) {
    data.pending_choice.forEach((opt, i) => {
      const btn = document.createElement("button");
      btn.textContent = "Capture " + JSON.stringify(opt.captured);
      btn.addEventListener("click", () => post("/api/choose", { index: i }));
      choicesEl.appendChild(btn);
    });
  }

  let lines = [];
  if (data.terminal) {
    lines.push(data.winner ? (data.winner + " wins -- no legal moves left for the other side.") : "Draw.");
    lines.push("Click Restart to play again.");
  } else {
    lines.push(data.player_name + " to move.");
    if (data.pending_choice) {
      lines.push("This move can capture two different ways -- pick which one below.");
    } else if (!data.current_pos) {
      lines.push(data.num_legal_moves + " legal move(s) available -- click a highlighted piece.");
    } else if (data.in_chain) {
      // if there were no further captures, the turn already auto-ended
      // server-side -- in_chain only stays true while continuing is a
      // real choice, so destinations is never empty here.
      lines.push("Moving " + JSON.stringify(data.current_pos) + " -- captured " + data.captured_so_far + " so far.");
      lines.push("Green rings: continue the chain. End turn: stop here instead.");
      lines.push("(Captures already made are final -- there's no undo.)");
    } else {
      lines.push("Selected " + JSON.stringify(data.current_pos) + " -- click a highlighted point to move.");
    }
    lines.push("");
    lines.push("Blue: your pieces that can move. Green: legal destination.");
    lines.push("Red dashed ring: an enemy piece still at risk this turn.");
    lines.push("Faded/greyed piece: already captured this turn. Gold dashed trail: your piece's path so far.");
    lines.push("Faint (see-through) piece: your piece's current spot, mid-move.");
  }
  statusEl.textContent = lines.join("\\n");
}

async function post(path, body) {
  const res = await fetch(path, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body || {}) });
  draw(await res.json());
}

canvas.addEventListener("click", (e) => {
  const rect = canvas.getBoundingClientRect();
  const pos = nearestPoint(e.clientX - rect.left, e.clientY - rect.top);
  if (pos) post("/api/click", { r: pos[0], c: pos[1] });
});
document.getElementById("endturn").addEventListener("click", () => post("/api/end_turn"));
document.getElementById("restart").addEventListener("click", () => post("/api/restart"));

fetch("/api/state").then(r => r.json()).then(draw);
</script>
</body>
</html>
""" % {"rows": ROWS, "cols": COLS}


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
            body = PAGE.encode("utf-8")
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
        else:
            self.send_response(404)
            self.end_headers()
            return
        self._send_json(session.to_json())

    def log_message(self, format, *args):
        pass  # keep the console quiet during play


if __name__ == "__main__":
    print(f"Fanorona running at http://localhost:{PORT}  (Ctrl+C to stop)")
    HTTPServer(("localhost", PORT), Handler).serve_forever()
