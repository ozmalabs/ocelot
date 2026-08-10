#!/usr/bin/env python3
"""Mock API server for the jabberwock web UI.

Stdlib only. Serves the static files in web/ at "/" and implements the
full daemon API contract on port 8788, so the frontend can be built and
verified without the real Rust-backed daemon. This file IS the executable
documentation of the contract:

    POST /api/chat            {"text": "..."} -> {"ok": true, "reply": "..."}
    GET  /api/chat/history    -> {"ok": true, "turns": [{text, reply, heard?, ts}, ...]}
    POST /api/enroll          {"label", "audio_b64", "filename"?} ->
                                {"ok": true, "word": "...", "n_exemplars": N}
    GET  /api/status          -> {"ok": true, "uptime_s", "ticks",
                                   "node_count", "last_checkpoint_ts",
                                   "booted_from"}
    GET  /api/sessions        -> {"ok": true, "sessions": [...]}
    GET  /api/sessions/<id>   -> {"ok": true, "session": {...}, "trace": [...]}
    GET  /api/proposals       -> {"ok": true, "proposals": [...]}
    GET  /api/proposals/<id>  -> {"ok": true, "proposal": {...}, "spec": {...}, "diff": "..."}
    POST /api/proposals/<id>/approve -> {"ok", "installed", "requires_restart",
                                          "reason"?, "diagnostics"?} (fake: flips to
                                          installed after ~2s, emits proposal_update)
    GET  /api/auto_approve    -> {"ok": true, "enabled", "paused_until_restart",
                                   "max_installs_per_hour", "require_additive",
                                   "allowed_semantics_kinds", "installs_this_hour"}
    POST /api/auto_approve    {"enabled"?, "max_installs_per_hour"?, "require_additive"?,
                                   "allowed_semantics_kinds"?} -> same shape as the GET
                                   (fake: just stores the fields, emits auto_approve_update)
    GET  /api/events          -> text/event-stream of
                                  {"type": "chat"|"status"|"session_update"
                                   |"enrolled"|"proposal_update"|"auto_approve_update", ...}

Run:
    python3 web/mock_server.py
Then open http://127.0.0.1:8788/
"""
from __future__ import annotations

import json
import queue
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

WEB_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8788
START_TS = time.time()

# --------------------------------------------------------------------------
# fake agent state
# --------------------------------------------------------------------------

STATE_LOCK = threading.Lock()
STATE = {
    "ticks": 41213,
    "node_count": 88342,
    "last_checkpoint_ts": time.time() - 240,
    "booted_from": "checkpoint",
}

CANNED_REPLIES = [
    "I parse that as a claim about the current frame; let me check the residual against what I predicted.",
    "That maps onto the feedback_control meta-shape I already hold. Want me to walk the rule that fired?",
    "I don't have a grounded concept for that yet. Show me an example and I can construct one from a framed concern.",
    "Order-N collapse says: what you're describing dequantizes to something I've already seen in ls20. Same family.",
    "I see: the thing you're asking about. I aim: to resolve the gap in my own terms, not borrow yours.",
    "That's a rule, not a fact. I'd need to compose it via ground_concern before I can act on it reliably.",
    "Noted. I'll fold that into the residual on my next tick and see if salience shifts.",
    "Low confidence. My collapse over that shape is still mostly prior, not much evidence yet.",
]

ACTIONS = ["up", "down", "left", "right", "act", "wait"]

SEE_VOICES = [
    "The thing moves.",
    "The thing stays.",
    "The thing blocks.",
    "The thing opens.",
    "The thing responds.",
    "Two coloured parts share one boundary.",
    "A wall closes the north edge.",
    "The slider stops only at the corners.",
]
AIM_VOICES = [
    "I explore the unclaimed quadrant.",
    "I approach the flagged cell.",
    "I avoid the region that halted me last time.",
    "I escape the pocket toward the frontier.",
    "I search for the affordance I haven't tried.",
    "I hold position; the residual is still unexplained.",
    "I test whether the wall I learned still holds.",
]

REASONINGS = [
    "Frontier expanded toward the unexplored quadrant; residual salience highest on the northern wall.",
    "Config-space flood closed at this node; minted an interaction hypothesis for the untried affordance.",
    "Predicted collapse matched observation; surprise near zero, continuing along the planned route.",
    "Surprise spike on the last transition; learned a new wall and re-planned the route shape.",
    "Argmax over drives selected the highest-residual axis; salience wired to the unexplained shortfall.",
    "Dequantized the current shape against the held quanta; remainder routed to a finer-grained match.",
]

SESSIONS = [
    {
        "id": 1001,
        "kind": "experiment",
        "game": "ls20",
        "status": "done",
        "hypothesis": (
            "The avatar is the multi-coloured blob (blue+orange body); motion is "
            "quantised to 5-cell slides; the chamber has 4 corner stops reachable "
            "only via the slider affordance, not free movement."
        ),
        "frames": 46,
        "score": 7,
        "run_dir": "/var/runs/sess-2026-07-01-001",
    },
    {
        "id": 1002,
        "kind": "experiment",
        "game": "vc33",
        "status": "running",
        "hypothesis": (
            "Colour-swap regions propagate along a contiguous same-colour flood; "
            "the goal state is a fully homogeneous grid."
        ),
        "frames": 18,
        "score": 2,
        "run_dir": "/var/runs/sess-2026-07-02-002",
    },
    {
        "id": 1003,
        "kind": "experiment",
        "game": "ft09",
        "status": "requested",
        "hypothesis": "",
        "frames": 0,
        "score": 0,
        "run_dir": "",
    },
    {
        "id": 1004,
        "kind": "experiment",
        "game": "jw77",
        "status": "failed",
        "hypothesis": (
            "Assumed the grid wraps toroidally; contradicted at frame 12 by a "
            "hard wall collision on the east edge."
        ),
        "frames": 12,
        "score": 0,
        "run_dir": "/var/runs/sess-2026-06-30-004",
    },
]

RUNNING_SESSION_ID = 1002


def make_trace(n: int) -> list[dict]:
    trace = []
    score = 0
    for i in range(n):
        if random.random() < 0.2:
            score += 1
        trace.append({
            "frame": i,
            "action": random.choice(ACTIONS),
            "score": score,
            "reasoning": random.choice(REASONINGS),
            "self_report": f"I see: {random.choice(SEE_VOICES)} I aim: {random.choice(AIM_VOICES)}",
        })
    return trace


SESSIONS_LOCK = threading.Lock()
TRACES = {s["id"]: make_trace(s["frames"]) for s in SESSIONS}

# --------------------------------------------------------------------------
# fake rung-4 self-extension proposals (mocks domains.self_extend_rust +
# domains.proposal_install's ExtensionProposal / RustExtensionSpec shapes)
# --------------------------------------------------------------------------

_REACHABLE_DIFF = """--- term.rs (enum variant) ---
    ReachableFrom { node: TermIdx, edge_type: Sym, any_type: bool },

--- term.rs (evaluator arm) ---
        TermNode::ReachableFrom { node, edge_type, any_type } => {
            let v = evaluate(arena, *node, env, ctx);
            let Value::Node(start) = v else {
                return Value::make_frozenset(vec![]);
            };
            let et = if *any_type { None } else { Some(*edge_type) };
            let mut visited: rustc_hash::FxHashSet<NodeID> = rustc_hash::FxHashSet::default();
            let mut frontier: Vec<NodeID> = vec![start];
            visited.insert(start);
            while let Some(cur) = frontier.pop() {
                for nb in ctx.graph.neighbours(cur, et) {
                    if visited.insert(nb) { frontier.push(nb); }
                }
            }
            visited.remove(&start);
            Value::make_frozenset(visited.into_iter().map(Value::Node).collect::<Vec<_>>())
        }

--- jsonio.rs (name arm) ---
        TermNode::ReachableFrom { .. } => "ReachableFrom","""

_ANCESTORS_DIFF = """--- term.rs (enum variant) ---
    AncestorsOf { node: TermIdx, edge_type: Sym, any_type: bool },

--- term.rs (evaluator arm) ---
        TermNode::AncestorsOf { node, edge_type, any_type } => {
            let v = evaluate(arena, *node, env, ctx);
            let Value::Node(start) = v else {
                return Value::make_frozenset(vec![]);
            };
            // walks REVERSE edges -- ctx.graph has no in_neighbours() index
            // built for every edge type yet, only the ones InNeighbours
            // already declared; this draft primitive assumed it did.
            let et = if *any_type { None } else { Some(*edge_type) };
            let mut visited: rustc_hash::FxHashSet<NodeID> = rustc_hash::FxHashSet::default();
            let mut frontier: Vec<NodeID> = vec![start];
            visited.insert(start);
            while let Some(cur) = frontier.pop() {
                for nb in ctx.graph.in_neighbours(cur, et) {
                    if visited.insert(nb) { frontier.push(nb); }
                }
            }
            visited.remove(&start);
            Value::make_frozenset(visited.into_iter().map(Value::Node).collect::<Vec<_>>())
        }"""

PROPOSALS = [
    {
        "id": 746,
        "name": "ReachableFrom",
        "of": "ReachableFrom",
        "status": "already_present",
        "installed": True,
        "requires_restart": True,
        "motivating_residual": "worlds/browser.py:514-522 (BrowserWorld.observe, the has_affordance mirror comment)",
        "purpose": ("a native Term for the transitive closure of one edge type -- 'every "
                    "node reachable from X via zero-or-more edge_type hops' -- so a graph "
                    "RULE can express unbounded-depth structure without a host adapter "
                    "mechanically flattening it in Python first"),
        "why_new": ("the DSL's only graph-neighbour primitive, Neighbours, is ONE hop; no "
                    "Term expresses an unbounded, data-dependent walk"),
        "semantics_kind": "graph_reachability",
        "sandbox_ok": True,
        "seconds": 4.2,
        "approved_by": "creator",
        "ts": time.time() - 3600 * 6,
        "diff": _REACHABLE_DIFF,
        "last_error": None,
    },
    {
        "id": 812,
        "name": "AncestorsOf",
        "of": "AncestorsOf",
        "status": "failed",
        "installed": False,
        "requires_restart": True,
        "motivating_residual": "domains/dependency_graph.py:88 (upstream-of query flattened in Python)",
        "purpose": "reverse transitive closure -- every node that reaches X via zero-or-more edge_type hops",
        "why_new": "ReachableFrom only walks forward edges; a dependency-upstream query needs the reverse walk",
        "semantics_kind": "graph_reachability",
        "sandbox_ok": False,
        "seconds": 3.1,
        "approved_by": None,
        "ts": time.time() - 3600 * 2,
        "diff": _ANCESTORS_DIFF,
        "last_error": (
            "error[E0599]: no method named `in_neighbours` found for struct `Graph` in the "
            "current scope\n  --> src/term.rs:2901:32\n   |\n2901 |  for nb in ctx.graph.in_neighbours(cur, et) {\n"
            "   |                                ^^^^^^^^^^^^^ method not found in `Graph`\n\n"
            "error: could not compile `substrate_rs` (lib) due to 1 previous error"
        ),
    },
    {
        "id": 793,
        "name": "WhitenBatchNorm",
        "of": "WhitenBatchNorm",
        "status": "validated",
        "installed": False,
        "requires_restart": True,
        "motivating_residual": "domains/speech_frontend.py:212 (per-vector whitening re-factors the same W every call)",
        "purpose": ("batch within-class whitening: factor the within-class scatter W = L "
                    "L^T once, then return L^-1 x for every row of a data matrix -- the "
                    "Whiten transform amortised so the Cholesky factorisation is shared, "
                    "not recomputed per vector"),
        "why_new": ("Whiten { W, x } re-factors W on every call (O(m*n^3) for m vectors); "
                    "the factorisation is invariant across rows but the single-vector Term "
                    "cannot hoist it out of the loop"),
        "semantics_kind": "matrix_whiten_batch",
        "sandbox_ok": True,
        "seconds": 6.8,
        "approved_by": None,
        "ts": time.time() - 900,
        "diff": (
            "--- term.rs (enum variant) ---\n"
            "    WhitenMany { a: TermIdx, b: TermIdx },\n\n"
            "--- term.rs (evaluator arm) ---\n"
            "        TermNode::WhitenMany { a, b } => {\n"
            "            let wv = evaluate(arena, *a, env, ctx);\n"
            "            let xs = evaluate(arena, *b, env, ctx);\n"
            "            whiten_many(&wv, &xs)\n"
            "        }\n\n"
            "--- term.rs (helper) ---\n"
            "fn whiten_many(w: &Value, xs: &Value) -> Value {\n"
            "    // Cholesky W = L L^T once; forward-solve per row of xs.\n"
            "    /* ... full body emitted into term.rs ... */\n"
            "}"
        ),
        "last_error": None,
    },
]
PROPOSALS_LOCK = threading.Lock()


def _proposal_list_entry(p: dict) -> dict:
    return {k: v for k, v in p.items() if k not in ("diff",)}


def _proposal_detail(p: dict) -> dict:
    return {
        "proposal": {
            "id": p["id"], "of": p["of"], "status": p["status"],
            "installed": p["installed"], "requires_restart": p["requires_restart"],
            "approved_by": p["approved_by"], "approved_ts": p.get("approved_ts"),
            "seconds": p["seconds"], "last_error": p["last_error"],
        },
        "spec": {
            "name": p["name"], "purpose": p["purpose"],
            "motivating_residual": p["motivating_residual"],
            "why_new": p["why_new"], "semantics_kind": p["semantics_kind"],
        },
        "diff": p["diff"],
    }


def _do_approve(pid: int, delay_s: float = 2.0) -> dict:
    """Mocks the real daemon's SYNCHRONOUS approve (domains.proposal_install.
    install_proposal): blocks for `delay_s` (standing in for a real cargo
    check + maturin build), then applies the same guardrail shape the real
    helper documents -- refuses anything not 'validated', flips
    installed=True on success, and always reports requires_restart=True."""
    with PROPOSALS_LOCK:
        p = next((p for p in PROPOSALS if p["id"] == pid), None)
    if p is None:
        return {"ok": False, "error": "not found"}
    if p["installed"]:
        return {"ok": False, "reason": "already installed", "installed": True,
                "requires_restart": True}
    if p["status"] == "already_present":
        with PROPOSALS_LOCK:
            p["installed"] = True
            p["approved_by"] = "web"
            p["approved_ts"] = time.time()
        broadcast({"type": "proposal_update", "id": pid, "status": "installed", "installed": True})
        return {"ok": True, "installed": True, "requires_restart": True,
                "reason": "already in runtime"}
    if p["status"] != "validated":
        return {"ok": False, "reason": f"status is {p['status']!r}, not 'validated'"}
    time.sleep(delay_s)  # stand-in for a real cargo check + maturin develop
    with PROPOSALS_LOCK:
        p["installed"] = True
        p["approved_by"] = "web"
        p["approved_ts"] = time.time()
    broadcast({"type": "proposal_update", "id": pid, "status": "installed", "installed": True})
    return {"ok": True, "installed": True, "requires_restart": True, "reason": "installed"}

# --------------------------------------------------------------------------
# fake auto-approve policy state (mocks domains.auto_approve's
# AutoApprovePolicy node -- OFF by default, same as the real daemon)
# --------------------------------------------------------------------------

AUTO_APPROVE_LOCK = threading.Lock()
AUTO_APPROVE = {
    "enabled": False,
    "max_installs_per_hour": 2,
    "require_additive": True,
    "allowed_semantics_kinds": ["graph_reachability"],
    "paused_until_restart": False,
    "installs_this_hour": 0,
}


def _auto_approve_status() -> dict:
    with AUTO_APPROVE_LOCK:
        return dict(AUTO_APPROVE)


def _auto_approve_apply(payload: dict) -> dict:
    with AUTO_APPROVE_LOCK:
        if "enabled" in payload:
            AUTO_APPROVE["enabled"] = bool(payload["enabled"])
        if "max_installs_per_hour" in payload:
            try:
                AUTO_APPROVE["max_installs_per_hour"] = int(payload["max_installs_per_hour"])
            except (TypeError, ValueError):
                pass
        if "require_additive" in payload:
            AUTO_APPROVE["require_additive"] = bool(payload["require_additive"])
        if "allowed_semantics_kinds" in payload and isinstance(payload["allowed_semantics_kinds"], list):
            AUTO_APPROVE["allowed_semantics_kinds"] = [str(k) for k in payload["allowed_semantics_kinds"]]
        return dict(AUTO_APPROVE)


# --------------------------------------------------------------------------
# fake enrollment state (mocks domains.speech_enrollment.enroll's return)
# --------------------------------------------------------------------------

ENROLL_LOCK = threading.Lock()
ENROLLED_WORDS: dict[str, int] = {}   # word -> exemplar count

CHAT_HISTORY_LOCK = threading.Lock()
CHAT_HISTORY: list[dict] = []

# --------------------------------------------------------------------------
# SSE broadcast
# --------------------------------------------------------------------------

SSE_LOCK = threading.Lock()
SSE_CLIENTS: list[queue.Queue] = []


def broadcast(event: dict) -> None:
    with SSE_LOCK:
        for q in list(SSE_CLIENTS):
            try:
                q.put_nowait(event)
            except queue.Full:
                pass


def current_status_event() -> dict:
    with STATE_LOCK:
        return {
            "type": "status",
            "ok": True,
            "uptime_s": round(time.time() - START_TS, 1),
            "ticks": STATE["ticks"],
            "node_count": STATE["node_count"],
            "last_checkpoint_ts": STATE["last_checkpoint_ts"],
            "booted_from": STATE["booted_from"],
        }


def background_status_loop() -> None:
    while True:
        time.sleep(5)
        with STATE_LOCK:
            STATE["ticks"] += random.randint(80, 240)
            STATE["node_count"] += random.randint(0, 12)
        broadcast(current_status_event())


def flip_running_session_after_delay(delay_s: float = 20.0) -> None:
    time.sleep(delay_s)
    with SESSIONS_LOCK:
        for s in SESSIONS:
            if s["id"] == RUNNING_SESSION_ID and s["status"] == "running":
                s["status"] = "done"
                s["frames"] = 24
                s["score"] = 5
                TRACES[s["id"]] = make_trace(s["frames"])
                broadcast({"type": "session_update", "id": s["id"], "status": s["status"]})
                break


# --------------------------------------------------------------------------
# HTTP handler
# --------------------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    server_version = "JabberwockMock/0.1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # noqa: A003 - stdlib signature
        print(f"[mock] {self.address_string()} " + (fmt % args))

    # -- helpers ------------------------------------------------------

    def _send_json(self, obj: dict, status: int = 200) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _sse_frame(obj: dict) -> bytes:
        return f"data: {json.dumps(obj)}\n\n".encode("utf-8")

    # -- routing --------------------------------------------------------

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            payload = current_status_event()
            payload.pop("type", None)
            payload["auto_approve"] = _auto_approve_status()
            self._send_json(payload)
            return
        if path == "/api/chat/history":
            with CHAT_HISTORY_LOCK:
                self._send_json({"ok": True, "turns": list(CHAT_HISTORY)})
            return
        if path.startswith("/api/chat/turns/") and path.endswith("/trace"):
            tid = path[len("/api/chat/turns/"):-len("/trace")]
            with CHAT_HISTORY_LOCK:
                turn = next((t for t in CHAT_HISTORY if str(t.get("turn_id")) == tid), None)
            if turn is None:
                self._send_json({"ok": False, "error": "not found"}, status=404)
                return
            self._send_json({"ok": True, "trace": {
                "turn_id": int(tid),
                "question": turn["text"],
                "reply": turn["reply"],
                "parse": {"comp_dispatch_path": "mock"},
                "goals": [],
                "mentions": [],
                "concerns": turn.get("concerns") or [],
                "current_topic": None,
            }})
            return
        if path == "/api/sessions":
            with SESSIONS_LOCK:
                self._send_json({"ok": True, "sessions": [dict(s) for s in SESSIONS]})
            return
        if path.startswith("/api/sessions/"):
            sid_str = path[len("/api/sessions/"):]
            try:
                sid = int(sid_str)
            except ValueError:
                sid = sid_str
            with SESSIONS_LOCK:
                session = next((s for s in SESSIONS if s["id"] == sid), None)
                if session is None:
                    self._send_json({"ok": False, "error": "not found"}, status=404)
                    return
                self._send_json({"ok": True, "session": dict(session), "trace": list(TRACES.get(sid, []))})
            return
        if path == "/api/proposals":
            with PROPOSALS_LOCK:
                self._send_json({"ok": True, "proposals": [_proposal_list_entry(p) for p in PROPOSALS]})
            return
        if path.startswith("/api/proposals/"):
            pid_str = path[len("/api/proposals/"):]
            try:
                pid = int(pid_str)
            except ValueError:
                self._send_json({"ok": False, "error": "not found"}, status=404)
                return
            with PROPOSALS_LOCK:
                p = next((p for p in PROPOSALS if p["id"] == pid), None)
                if p is None:
                    self._send_json({"ok": False, "error": "not found"}, status=404)
                    return
                self._send_json({"ok": True, **_proposal_detail(p)})
            return
        if path == "/api/auto_approve":
            self._send_json({"ok": True, **_auto_approve_status()})
            return
        if path == "/api/events":
            self._handle_sse()
            return

        self._serve_static(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                payload = {}
            text = str(payload.get("text", ""))

            # Simulate real "the agent is thinking" latency.
            time.sleep(random.uniform(1.0, 2.0))
            reply = random.choice(CANNED_REPLIES)
            heard = [w for w in ENROLLED_WORDS if w in text.lower().split()]
            if heard:
                reply = f"{reply} — heard: {', '.join(heard)}"

            self._send_json({"ok": True, "reply": reply})
            with CHAT_HISTORY_LOCK:
                CHAT_HISTORY.append({"text": text, "reply": reply, "heard": heard,
                                     "ts": time.time(), "turn_id": len(CHAT_HISTORY) + 1})
            # Broadcast so any other connected client (e.g. a second
            # browser tab, or the CLI) also sees this exchange.
            broadcast({"type": "chat", "text": text, "reply": reply, "heard": heard})
            return

        if parsed.path.startswith("/api/chat/turns/") and parsed.path.endswith("/flag"):
            tid = parsed.path[len("/api/chat/turns/"):-len("/flag")]
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                payload = {}
            note = str(payload.get("note", "")).strip()
            if not note:
                self._send_json({"ok": False, "error": "missing note"}, status=400)
                return
            with CHAT_HISTORY_LOCK:
                turn = next((t for t in CHAT_HISTORY if str(t.get("turn_id")) == tid), None)
                if turn is None:
                    self._send_json({"ok": False, "error": "not found"}, status=404)
                    return
                concern_id = 9000 + int(tid)
                turn.setdefault("concerns", []).append({
                    "id": concern_id, "kind": "reply_fix", "content": note, "status": "noted",
                })
                turn["flagged"] = True
            self._send_json({"ok": True, "turn_id": int(tid), "concern_id": concern_id, "note": note})
            broadcast({"type": "self_concern_update", "id": str(concern_id), "status": "noted"})
            return

        if parsed.path == "/api/enroll":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                payload = {}
            label = str(payload.get("label", "")).strip()
            audio_b64 = payload.get("audio_b64")
            if not label or not audio_b64:
                self._send_json({"ok": False, "error": "missing label or audio_b64"}, status=400)
                return
            # Mock: no real audio decode/DTW — just accept it and count exemplars,
            # exercising the exact request/response/SSE shape the real daemon uses.
            time.sleep(random.uniform(0.3, 0.8))
            with ENROLL_LOCK:
                ENROLLED_WORDS[label] = ENROLLED_WORDS.get(label, 0) + 1
                n_exemplars = ENROLLED_WORDS[label]
            self._send_json({"ok": True, "word": label, "n_exemplars": n_exemplars})
            broadcast({"type": "enrolled", "word": label, "n_exemplars": n_exemplars})
            return

        if parsed.path == "/api/ingest":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                payload = {}
            filename = str(payload.get("filename", "")).strip()
            if not filename or not payload.get("data_b64"):
                self._send_json({"ok": False, "error": "missing filename or data_b64"}, status=400)
                return
            ext = Path(filename).suffix.lower()
            kind = "text" if ext in {".txt", ".md", ".json", ".csv", ".html"} else (
                "image" if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp"} else (
                "pdf" if ext == ".pdf" else (
                "audio" if ext in {".wav", ".mp3", ".webm", ".ogg"} else "binary")))
            preview = {
                "text": "text file ingested (mock)",
                "image": "image rasterised (mock)",
                "pdf": "pdf pages rasterised (mock)",
                "audio": "audio heard (mock)",
                "binary": "binary stored (mock)",
            }[kind]
            out = {"ok": True, "filename": filename, "kind": kind, "preview": preview,
                   "message_id": random.randint(10000, 99999)}
            if kind == "text":
                out["n_mentions"] = 12
            if kind == "pdf":
                out["page_count"] = 3
            self._send_json(out)
            broadcast({"type": "ingested", **out})
            return

        if parsed.path.startswith("/api/proposals/") and parsed.path.endswith("/approve"):
            pid_str = parsed.path[len("/api/proposals/"):-len("/approve")]
            try:
                pid = int(pid_str)
            except ValueError:
                self._send_json({"ok": False, "error": "not found"}, status=404)
                return
            result = _do_approve(pid)
            self._send_json(result)
            return

        if parsed.path == "/api/auto_approve":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                payload = {}
            status = _auto_approve_apply(payload)
            self._send_json({"ok": True, **status})
            broadcast({"type": "auto_approve_update", **status})
            return

        self._send_json({"ok": False, "error": "not found"}, status=404)

    # -- SSE --------------------------------------------------------------

    def _handle_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q: queue.Queue = queue.Queue(maxsize=100)
        with SSE_LOCK:
            SSE_CLIENTS.append(q)
        try:
            # Send an immediate snapshot so the client's header doesn't sit
            # blank for up to 5s waiting on the next tick.
            self.wfile.write(self._sse_frame(current_status_event()))
            self.wfile.flush()
            while True:
                try:
                    event = q.get(timeout=15)
                    self.wfile.write(self._sse_frame(event))
                    self.wfile.flush()
                except queue.Empty:
                    # Comment-only heartbeat; EventSource ignores lines that
                    # start with ':' but it keeps the socket from idling out.
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with SSE_LOCK:
                if q in SSE_CLIENTS:
                    SSE_CLIENTS.remove(q)

    # -- static files -----------------------------------------------------

    def _serve_static(self, path: str) -> None:
        if path == "/":
            path = "/index.html"
        rel = path.lstrip("/")
        fpath = (WEB_DIR / rel).resolve()
        if WEB_DIR not in fpath.parents and fpath != WEB_DIR:
            self.send_response(403)
            self.end_headers()
            return
        if not fpath.is_file():
            body = b"not found"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json",
            ".svg": "image/svg+xml",
        }.get(fpath.suffix, "application/octet-stream")
        data = fpath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    threading.Thread(target=background_status_loop, daemon=True).start()
    threading.Thread(target=flip_running_session_after_delay, daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[mock] serving {WEB_DIR} + API on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
