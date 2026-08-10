"""TownView backend — serves the SPA and streams the Bigville town.

Endpoints
    GET /                      the SPA (static files)
    GET /api/runs              list recorded play.json documents under results/
    GET /api/replay/<name>     return one recorded play document (raw; SPA normalises)
    GET /api/live              SSE stream: construct a BigvilleLivingTownWorld, step it,
                               emit one `frame` per tick (unified schema; see DATA_CONTRACT.md)

Run (from the gamma-substrate root):
    python -m web.townview.server.app                 # http://127.0.0.1:8756
    python -m web.townview.server.app --port 9000 --host 0.0.0.0

This module is a WORLD ADAPTER / host layer only: it reads graph state and translates
it to JSON. No agent decisions live here — the town's cognition runs in the Rust
substrate behind `integ_step()`.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

# --- make the gamma-substrate root importable (worlds/, scripts/, ...) ---------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

WEB = os.path.join(ROOT, "web", "townview")
RESULTS = os.path.join(ROOT, "results")

from fastapi import FastAPI, HTTPException, Query, Request        # noqa: E402
from fastapi.responses import JSONResponse                        # noqa: E402
from fastapi.staticfiles import StaticFiles                       # noqa: E402
from sse_starlette.sse import EventSourceResponse                 # noqa: E402

app = FastAPI(title="TownView")


# ------------------------------------------------------------------ recorded runs ----
def _find_runs():
    """Every play.json (or *_play.json) under results/, newest first."""
    runs = []
    if not os.path.isdir(RESULTS):
        return runs
    for dirpath, _dirs, files in os.walk(RESULTS):
        for fn in files:
            if fn == "play.json" or fn.endswith("_play.json") or fn.endswith(".play.json"):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, RESULTS)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                # a friendly name: the containing dir (or file stem)
                name = rel.replace(os.sep, "/")
                label = os.path.basename(dirpath) if fn == "play.json" else fn[:-5]
                runs.append({"name": name, "label": label,
                             "size": st.st_size, "mtime": st.st_mtime})
    runs.sort(key=lambda r: r["mtime"], reverse=True)
    return runs


@app.get("/api/runs")
def api_runs():
    return {"runs": _find_runs()}


@app.get("/api/replay/{name:path}")
def api_replay(name: str):
    # constrain to results/ — no path traversal
    full = os.path.abspath(os.path.join(RESULTS, name))
    if not full.startswith(RESULTS + os.sep) or not os.path.isfile(full):
        raise HTTPException(status_code=404, detail="run not found")
    try:
        with open(full) as f:
            return JSONResponse(json.load(f))
    except Exception as e:                                        # noqa: BLE001
        raise HTTPException(status_code=500, detail="bad play doc: %s" % e)


# ------------------------------------------------------------------ live SSE ----------
def _sse(type_, payload):
    return {"data": json.dumps({"type": type_, **payload})}


def _resident_cards(world, derive):
    """Rich resident cards for the `meta` message — a pure graph read via play_doc's
    own resident assembly, plus predicts/rels derived from the town's Bonds."""
    residents_cfg, bonds = derive
    predicts = {r["name"]: r.get("predicts", []) for r in residents_cfg}
    # per-resident directed bonds -> warm/hostile with magnitudes
    rels = {nm: [] for nm in world.people}
    for (a, b), v in bonds.items():
        if a in rels:
            aff = float(v.get("affection", 0.0)) - float(v.get("resentment", 0.0))
            rels[a].append({
                "who": b,
                "feeling": "warm" if aff > 0 else ("hostile" if aff < 0 else "neutral"),
                "affection": float(v.get("affection", 0.0)),
                "resentment": float(v.get("resentment", 0.0)),
            })
    doc = world.play_doc()
    by_id = {r.get("id", r.get("name")): r for r in doc["residents"]}
    cards = []
    for nm in world.people:
        base = dict(by_id.get(nm, {"id": nm, "name": nm}))
        base["id"] = nm
        base["predicts"] = predicts.get(nm, [])
        base["rels"] = rels.get(nm, [])
        cards.append(base)
    return cards, doc


async def _live_gen(request: Request, cast: int, seed: int, max_ticks: int):
    from worlds.bigville_living_town_world import BigvilleLivingTownWorld as W
    world = None
    try:
        world = await asyncio.to_thread(W, cast=cast, seed=seed)
        derive = await asyncio.to_thread(world._derive_social)
        cards, doc0 = await asyncio.to_thread(_resident_cards, world, derive)
        yield _sse("meta", {
            "grid": [doc0["map"]["w"], doc0["map"]["h"]],
            "square": doc0.get("residents") and _townhall(doc0) or [doc0["map"]["w"] // 2, doc0["map"]["h"] // 2],
            "map": doc0["map"],
            "residents": cards,
            "institutions": doc0.get("institutions", {}),
            "shops": doc0.get("shops", {}),
            "cast": cast, "seed": seed, "max_ticks": max_ticks,
            "title": "live",
        })

        last_boards = None
        for t in range(max_ticks):
            if await request.is_disconnected():
                yield _sse("end", {"reason": "client-gone", "ticks": t})
                return
            before = len(world.events)
            await asyncio.to_thread(world.integ_step)
            frame = await asyncio.to_thread(_read_frame, world, before)
            yield _sse("frame", frame)

            # boards change slowly — only push when they do
            boards = await asyncio.to_thread(_read_boards, world)
            sig = json.dumps(boards, sort_keys=True)
            if sig != last_boards:
                last_boards = sig
                yield _sse("paper", boards)
            await asyncio.sleep(0.01)      # yield to the loop; keeps SSE flushing
        yield _sse("end", {"reason": "max-ticks", "ticks": max_ticks})
    except Exception as e:                                        # noqa: BLE001
        import traceback
        traceback.print_exc()
        yield _sse("end", {"reason": "error: %s" % e, "ticks": -1})
    finally:
        if world is not None:
            try:
                await asyncio.to_thread(world.close)
            except Exception:                                    # noqa: BLE001
                pass


def _townhall(doc):
    for b in doc.get("map", {}).get("buildings", []):
        if b.get("id") == "townhall" or b.get("type") == "townhall":
            return [b["x"], b["y"]]
    return [doc["map"]["w"] // 2, doc["map"]["h"] // 2]


def _read_frame(world, before):
    pos = {nm: [int(p[0]), int(p[1])] for nm in world.people
           if (p := world.pos.get(nm)) and not world.is_dead(nm)}
    events = []
    for e in world.events[before:]:
        actors = e.get("actors") or []
        actor = actors[0] if actors else None
        at = None
        if actor and world.pos.get(actor):
            p = world.pos[actor]
            at = [int(p[0]), int(p[1])]
        events.append({
            "actor": actor, "act": e.get("act", e.get("kind", "")),
            "target": e.get("target"), "text": e.get("text", ""),
            "kind": e.get("kind", ""), "at": at,
        })
    return {"t": int(world.world_epoch), "day": int(world.world_epoch // 36),
            "pos": pos, "events": events}


def _read_boards(world):
    from worlds.bigville_integ3_state import export_townstate3
    snap = export_townstate3(world)
    return {
        "paper": snap.get("paper", []),
        "council_board": snap.get("council_board", []),
        "collective_action": snap.get("collective_action"),
        "institutions": snap.get("institutions", {}),
    }


@app.get("/api/live")
async def api_live(request: Request,
                   cast: int = Query(8, ge=3, le=16),
                   seed: int = Query(276000),
                   ticks: int = Query(160, ge=1, le=2000)):
    return EventSourceResponse(_live_gen(request, cast, seed, ticks))


@app.get("/api/health")
def api_health():
    return {"ok": True, "root": ROOT, "runs": len(_find_runs())}


# ------------------------------------------------------------------ static SPA --------
# mount LAST so /api/* wins; html=True serves index.html at "/"
app.mount("/", StaticFiles(directory=WEB, html=True), name="spa")


def main():
    import uvicorn
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8756)
    args = ap.parse_args()
    print("TownView -> http://%s:%d  (root=%s)" % (args.host, args.port, ROOT))
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
