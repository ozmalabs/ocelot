"""Live (G, Γ) visualiser — FastAPI + WebSocket.

Demo flow: a single AppState owns the (G, Γ) substrate. A background tick task
steps the substrate at ``tick_seconds``. Every step (and every Γ-swap) broadcasts
a JSON snapshot to all connected clients. Rule swaps are timed server-side from
``/preset/{name}`` receipt to the first post-swap step that renders.

Run: ``python -m viz.server`` from the experiment directory.
"""
from __future__ import annotations

import asyncio
import json
import random
import sys
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).parent.parent))

from domains import conway  # noqa: E402
from substrate import GammaLearner, grammar_from_json, grammar_to_json  # noqa: E402

FRONTEND_DIR = Path(__file__).parent / "frontend"


class AppState:
    def __init__(self, rows: int = 48, cols: int = 48) -> None:
        self.rows = rows
        self.cols = cols
        self.rule_name = "Conway"
        self.tick_seconds = 0.08
        self.run_task: asyncio.Task | None = None
        self.clients: set[WebSocket] = set()
        self.last_swap_t: float = time.monotonic()
        self.last_swap_render_ms: float | None = None
        self.last_step_ms: float = 0.0
        self.generation = 0
        self.substrate = None
        self.learner: GammaLearner = GammaLearner()
        self.learning_active: bool = False
        self.reset(seed=42)

    def reset(self, seed: int) -> None:
        rng = random.Random(seed)
        board = [[1 if rng.random() < 0.35 else 0 for _ in range(self.cols)]
                 for _ in range(self.rows)]
        self.substrate = conway.make_substrate(conway.RULE_PRESETS[self.rule_name])
        conway.encode_board(self.substrate, board)
        self.generation = 0
        self.last_swap_t = time.monotonic()
        self.last_swap_render_ms = None

    def step(self) -> None:
        t0 = time.monotonic()
        before = (conway.decode_board(self.substrate, self.rows, self.cols)
                  if self.learning_active else None)
        conway.step(self.substrate)
        self.last_step_ms = (time.monotonic() - t0) * 1000
        self.generation += 1
        if self.last_swap_render_ms is None:
            self.last_swap_render_ms = (time.monotonic() - self.last_swap_t) * 1000
        if before is not None:
            after = conway.decode_board(self.substrate, self.rows, self.cols)
            self.learner.observe_transition(before, after)

    def swap_rule(self, name: str) -> None:
        if name not in conway.RULE_PRESETS:
            raise HTTPException(404, f"unknown preset: {name}")
        grammar = conway.RULE_PRESETS[name]()
        conway.swap_grammar(self.substrate, grammar)
        self.rule_name = name
        self.last_swap_t = time.monotonic()
        self.last_swap_render_ms = None

    def swap_grammar_json(self, grammar_json: dict, label: str = "custom") -> None:
        grammar = grammar_from_json(grammar_json)
        conway.swap_grammar(self.substrate, grammar)
        self.rule_name = label
        self.last_swap_t = time.monotonic()
        self.last_swap_render_ms = None

    def apply_learned(self) -> None:
        if not self.learner.grammar.productions:
            raise HTTPException(409, "learner has no productions yet — start learning first")
        conway.swap_grammar(self.substrate, self.learner.grammar)
        self.rule_name = "Learned"
        self.last_swap_t = time.monotonic()
        self.last_swap_render_ms = None

    def reset_learner(self) -> None:
        self.learner = GammaLearner()
        self.learning_active = False

    def snapshot(self) -> dict:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "generation": self.generation,
            "rule": self.rule_name,
            "board": conway.decode_board(self.substrate, self.rows, self.cols),
            "productions": [{
                "provenance": p.provenance,
                "src": p.src.type,
                "edge": p.edge_type,
                "tgt": p.tgt.type,
            } for p in self.substrate.checker.grammar.productions],
            "running": self.run_task is not None and not self.run_task.done(),
            "tick_seconds": self.tick_seconds,
            "last_swap_render_ms": self.last_swap_render_ms,
            "last_step_ms": round(self.last_step_ms, 2),
            "presets": list(conway.RULE_PRESETS.keys()),
            "grammar_json": grammar_to_json(self.substrate.checker.grammar),
            "learner": {
                "active": self.learning_active,
                "observations": self.learner.observation_count,
                "edits": len(self.learner.edit_log),
                "cases_covered": sum(1 for k in self.learner.observations),
                "cases_total": 2 * 9,  # 2 src types × 9 alive-n values
                "productions": len(self.learner.grammar.productions),
                "recent_edits": [
                    {"op": e.op, "src": e.src_type, "tgt": e.tgt_type,
                     "n_set": list(e.n_set), "reason": e.reason}
                    for e in self.learner.edit_log[-6:]
                ],
                "grammar_json": (grammar_to_json(self.learner.grammar)
                                 if self.learner.grammar.productions else None),
            },
        }


state = AppState()
app = FastAPI()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


async def broadcast() -> None:
    if not state.clients:
        return
    msg = json.dumps(state.snapshot())
    dead: list[WebSocket] = []
    for ws in list(state.clients):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.clients.discard(ws)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    state.clients.add(ws)
    await ws.send_text(json.dumps(state.snapshot()))
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        state.clients.discard(ws)


@app.get("/state")
async def get_state() -> dict:
    return state.snapshot()


@app.post("/step")
async def post_step() -> dict:
    state.step()
    await broadcast()
    return state.snapshot()


@app.post("/reset")
async def post_reset(payload: dict | None = None) -> dict:
    seed = (payload or {}).get("seed", random.randint(0, 10**6))
    state.reset(int(seed))
    await broadcast()
    return state.snapshot()


@app.post("/preset/{name}")
async def post_preset(name: str) -> dict:
    state.swap_rule(name)
    await broadcast()
    return state.snapshot()


@app.post("/learn/start")
async def post_learn_start() -> dict:
    state.learning_active = True
    await broadcast()
    return state.snapshot()


@app.post("/learn/stop")
async def post_learn_stop() -> dict:
    state.learning_active = False
    await broadcast()
    return state.snapshot()


@app.post("/learn/reset")
async def post_learn_reset() -> dict:
    state.reset_learner()
    await broadcast()
    return state.snapshot()


@app.post("/learn/apply")
async def post_learn_apply() -> dict:
    state.apply_learned()
    await broadcast()
    return state.snapshot()


@app.post("/grammar")
async def post_grammar(payload: dict) -> dict:
    """Replace Γ with a user-supplied JSON grammar. The label appears as the
    active rule name. Returns 422 with a useful message on parse failure."""
    label = payload.get("label", "custom")
    grammar_json = payload.get("grammar") or payload
    try:
        state.swap_grammar_json(grammar_json, label=label)
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(422, f"invalid grammar: {exc}")
    await broadcast()
    return state.snapshot()


async def _run_loop() -> None:
    try:
        while True:
            state.step()
            await broadcast()
            await asyncio.sleep(state.tick_seconds)
    except asyncio.CancelledError:
        pass


@app.post("/run")
async def post_run(payload: dict | None = None) -> dict:
    if payload and "tick_seconds" in payload:
        state.tick_seconds = max(0.01, float(payload["tick_seconds"]))
    if state.run_task is None or state.run_task.done():
        state.run_task = asyncio.create_task(_run_loop())
    return state.snapshot()


@app.post("/stop")
async def post_stop() -> dict:
    if state.run_task is not None and not state.run_task.done():
        state.run_task.cancel()
    return state.snapshot()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
