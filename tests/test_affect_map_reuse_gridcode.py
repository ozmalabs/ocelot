"""Confirmatory test for docs/research/psychology_affect/AFFECT_MAP_REUSE_GRID_CODE_PREREG.md
(block 367000, start commit 79369ffe).

Part A: does the spatial quanta map have a 6-fold directional code? (expected: no, 4-fold).
Part B: does the UNCHANGED quanta machinery carry a valence-arousal map, and what does its
distance signal encode?

This file is a WORLD ADAPTER only, in the convention of tests/test_quanta_navigation_migrated.py:
it authors belief cells, the is_self Region -> responds_via -> ControlResponse chain and a world
Goal, calls the Rust `space_quantize` primitive once, then drives the adapter's two-phase tick and
reads `chosen_action`. Every navigation decision is made by the qf_* rules in
seeds/quanta_navigation.json. The Fourier fits and rank correlations are OFFLINE measurement of the
recorded walks, not agent code.

One test per gate (G-A1..G-B3). X-A4 and X-B3 record values and do not assert. Every measured
value is written to results/affect_map_reuse_gridcode.json for the RESULTS document.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import time

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "quanta_navigation.json")
OUT_PATH = os.path.join(ROOT, "results", "affect_map_reuse_gridcode.json")
START_COMMIT = "79369ffee4ebc7e6c366ae2f93904b384637105a"   # prereg commit (§9)
# §12.3 (VISION_PROTOCOL): G-B1's claim is about THIS RUNG's own commits, so it is pinned to
# the rung's range (prereg commit .. result commit), never to the mutable working tree, which
# later rungs legitimately change (e.g. block 369000 adds seeds/affect_frame.json).
RESULT_COMMIT = "6ed6d3c5a58c558c6b0349e974f653e329730780"
FLOOR, WALL = 4, 3
TOL = 1e-9
MAX_STEPS = 64
B1_BUDGET_S = 3600.0                                          # §3 B1 runtime fallback

# §4 oracle values (pre-registered, Appendix A)
A4_SQ, A8_SQ, A6_HEX = 0.180262476027, 0.050961235773, 0.068916648906

SQUARE_CONTROLS = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
# X-A4: axial hex controls (di, dj) in {(±1,0),(0,±1),(1,-1),(-1,1)}, laid out as dc=di, dr=dj
HEX_CONTROLS = {"Ip": (0, 1), "Im": (0, -1), "Jp": (1, 0), "Jm": (-1, 0),
                "IpJm": (-1, 1), "ImJp": (1, -1)}

ANCHORS = {"happy": (3, 2), "surprised": (1, 4), "afraid": (-2, 4), "angry": (-3, 3),
           "disgusted": (-3, 1), "sad": (-3, -2), "neutral": (0, 0)}   # (valence, arousal)


# ---------------------------------------------------------------------------------------------
# results record (offline measurement output)
# ---------------------------------------------------------------------------------------------

def _record(section, payload):
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    data = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as fh:
            data = json.load(fh)
    data[section] = payload
    with open(OUT_PATH, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)


@pytest.fixture(scope="module", autouse=True)
def _header():
    from domains.engine_provenance import provenance_line
    head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
    if os.path.exists(OUT_PATH):
        os.remove(OUT_PATH)
    _record("header", {"start_commit": START_COMMIT, "head_at_run": head,
                       "engine": provenance_line(), "started_unix": time.time()})
    yield


# ---------------------------------------------------------------------------------------------
# world adapter harness (after tests/test_quanta_navigation_migrated.py)
# ---------------------------------------------------------------------------------------------

def _fresh():
    wa = WorldAdapter(seeds=())
    with open(SEED_PATH) as fh:
        wa.inner.load_seed_manifest(json.load(fh), None)
    return wa


def _build_world(passable, H, W, controls, start, goal):
    """Fresh adapter + belief over the H x W grid (every cell authored: FLOOR iff in
    `passable`, else WALL), decoded once by the Rust primitive, plus controls and a world
    Goal. Returns (wa, game, summary)."""
    wa = _fresh()
    S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "nav_repr": "quanta",
                                        "nav_mode": "seek", "avatar_pose": list(start),
                                        "flood_epoch": 0.0})
    for r in range(H):
        for c in range(W):
            val = float(FLOOR if (r, c) in passable else WALL)
            n = S.add_node("WorldInstance", {"world_type": "Cell", "row": float(r),
                                             "col": float(c), "value": val})
            I.add_edge_unchecked(game, "has_cell", n)
    gid = int(str(game).lstrip("#"))
    summary = dict(I.space_quantize(gid, 2, "1x1", [FLOOR], [0, 0], [H - 1, W - 1], 1))
    sr = S.add_node("Region", {"is_self": 1.0})
    I.add_edge_unchecked(game, "has_region", sr)
    for name, (dr, dc) in controls.items():
        cr = S.add_node("ControlResponse", {"dr": float(dr), "dc": float(dc), "dz": 0.0,
                                            "cname": name})
        I.add_edge_unchecked(sr, "responds_via", cr)
    g = S.add_node("Goal", {"pose": list(goal), "committed": 1.0, "world": 1.0})
    I.add_edge_unchecked(game, "committed_goal", g)
    return wa, game, summary


def _tick2(wa, game, epoch):
    I = wa.inner
    I.set_attr(game, "chosen_action", "")
    I.set_attr(game, "closed", -1.0)
    I.set_attr(game, "flood_epoch", float(epoch))
    I.run_rules()
    I.set_attr(game, "closed", 0.0)
    I.run_rules()
    return wa.s.node(game)["attrs"].get("chosen_action") or ""


def _quanta(wa):
    out = []
    for q in wa.s.nodes("SpaceQuantum"):
        a = wa.s.node(q)["attrs"]
        out.append((q, tuple(a["lo"]), tuple(a["hi"]), a.get("kind"), a.get("qdist")))
    return out


def _quantum_qdist_at(wa, pose):
    for _, lo, hi, kind, qd in _quanta(wa):
        if kind == "passable" and all(lo[d] <= pose[d] <= hi[d] for d in range(2)):
            return qd
    return None


def _walk(passable, H, W, controls, start, goal, record_start_qdist=False):
    """Mechanical world loop: tick, read the action, move iff the TRUE world allows it.
    Returns dict(arrived, steps, path, start_qdist)."""
    wa, game, summary = _build_world(passable, H, W, controls, start, goal)
    I = wa.inner
    pos, path, start_qdist = tuple(start), [tuple(start)], None
    for step in range(MAX_STEPS):
        if pos == tuple(goal):
            return {"arrived": True, "steps": step, "path": path, "start_qdist": start_qdist,
                    "summary": summary}
        I.set_attr(game, "avatar_pose", [int(pos[0]), int(pos[1])])
        act = _tick2(wa, game, epoch=step + 1)
        if step == 0 and record_start_qdist:
            start_qdist = _quantum_qdist_at(wa, pos)
        if not act:
            break
        dr, dc = controls[act]
        tgt = (pos[0] + dr, pos[1] + dc)
        if tgt in passable:
            pos = tgt
        path.append(pos)
    return {"arrived": pos == tuple(goal), "steps": len(path) - 1, "path": path,
            "start_qdist": start_qdist, "summary": summary}


# ---------------------------------------------------------------------------------------------
# offline measurement (Appendix A analysis)
# ---------------------------------------------------------------------------------------------

def _amp(points, k):
    th = np.array([math.atan2(y, x) for x, y, _ in points])
    f = np.array([p[2] for p in points])
    X = np.column_stack([np.ones_like(th), np.cos(k * th), np.sin(k * th)])
    c, *_ = np.linalg.lstsq(X, f, rcond=None)
    return math.hypot(c[1], c[2])


def _amps(points):
    return {k: _amp(points, k) for k in range(3, 9)}


def _hex_points():
    pts = []
    for i in range(-12, 13):
        for j in range(-12, 13):
            x, y = i + 0.5 * j, (math.sqrt(3) / 2) * j
            r = math.hypot(x, y)
            if 6 - TOL <= r <= 8 + TOL:
                pts.append((i, j, x, y, r, (abs(i) + abs(j) + abs(i + j)) // 2))
    return pts


def _rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for t in range(i, j + 1):
            ranks[order[t]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def _spearman(a, b):
    ra, rb = np.array(_rank(a)), np.array(_rank(b))
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def _stair(p, q):
    dv, da = q[0] - p[0], q[1] - p[1]
    Dv, Da = abs(dv), abs(da)
    sv, sa = (dv > 0) - (dv < 0), (da > 0) - (da < 0)
    iv = ia = 0
    cur = list(p)
    out = [tuple(p)]
    while iv < Dv or ia < Da:
        if iv < Dv and (Da == 0 or iv * Da <= ia * Dv):
            iv += 1
            cur[0] += sv
        else:
            ia += 1
            cur[1] += sa
        out.append(tuple(cur))
    return out


def _va_to_rc(va):
    """(valence, arousal) -> (row, col) in the 11x11 grid: row <-> arousal, col <-> valence."""
    return (va[1] + 5, va[0] + 5)


# ---------------------------------------------------------------------------------------------
# Part A — square spatial map
# ---------------------------------------------------------------------------------------------

A_H = A_W = 19
A_CENTRE = (9, 9)
A_FLOOR = {(r, c) for r in range(1, 18) for c in range(1, 18)}
S_SQ = [(dx, dy) for dx in range(-8, 9) for dy in range(-8, 9) if 36 <= dx * dx + dy * dy <= 64]

_part_a = {}


def _run_part_a():
    if _part_a:
        return _part_a
    rows = []
    t0 = time.time()
    for dx, dy in S_SQ:
        goal = (A_CENTRE[0] + dy, A_CENTRE[1] + dx)
        w = _walk(A_FLOOR, A_H, A_W, SQUARE_CONTROLS, A_CENTRE, goal)
        rows.append({"dx": dx, "dy": dy, "arrived": w["arrived"], "steps": w["steps"]})
    _part_a["rows"] = rows
    _part_a["wall_s"] = time.time() - t0
    return _part_a


def test_GA1_spatial_walk_is_manhattan():
    res = _run_part_a()
    rows = res["rows"]
    assert len(rows) == 88
    arrived = sum(r["arrived"] for r in rows)
    match = sum(r["arrived"] and r["steps"] == abs(r["dx"]) + abs(r["dy"]) for r in rows)
    _record("G-A1", {"n": len(rows), "arrived": arrived, "steps_eq_manhattan": match,
                     "wall_s": res["wall_s"],
                     "mismatches": [r for r in rows
                                    if not (r["arrived"] and r["steps"] == abs(r["dx"]) + abs(r["dy"]))]})
    assert arrived == 88
    assert match == 88


def test_GA3_pipeline_positive_control_hex_off_graph():
    pts = _hex_points()
    assert len(pts) == 120
    amps = _amps([(x, y, hd / r) for _, _, x, y, r, hd in pts])
    _record("G-A3", {"n": len(pts), "amps": amps})
    assert abs(amps[6] - A6_HEX) <= TOL
    for k in (3, 4, 5, 7, 8):
        assert amps[k] <= TOL, f"hex control fold {k} = {amps[k]}"


def test_GA2_no_grid_code_on_the_spatial_map():
    # G-A2 is interpretable only if the off-graph pipeline control passes (G-A3).
    pts = _hex_points()
    hamps = _amps([(x, y, hd / r) for _, _, x, y, r, hd in pts])
    pipeline_ok = abs(hamps[6] - A6_HEX) <= TOL and all(hamps[k] <= TOL for k in (3, 4, 5, 7, 8))
    rows = _run_part_a()["rows"]
    pts_sq = [(r["dx"], r["dy"], r["steps"] / math.hypot(r["dx"], r["dy"])) for r in rows]
    amps = _amps(pts_sq)
    _record("G-A2", {"amps": amps, "pipeline_control_ok": pipeline_ok})
    assert pipeline_ok, "G-A3 failed: G-A2 is uninterpretable and is not reported as passed"
    for k in (3, 5, 6, 7):
        assert amps[k] <= TOL, f"fold {k} amplitude {amps[k]}"
    assert abs(amps[4] - A4_SQ) <= TOL
    assert abs(amps[8] - A8_SQ) <= TOL


# ---------------------------------------------------------------------------------------------
# Part B — valence-arousal map on the unchanged machinery
# ---------------------------------------------------------------------------------------------

B_H = B_W = 11
B_LATTICE = [(v, a) for v in range(-4, 5) for a in range(-4, 5)]
B_OPEN = {_va_to_rc(p) for p in B_LATTICE}


def test_GB1_reuse_with_zero_mechanism_change():
    pairs = [(p, q) for p in B_LATTICE for q in B_LATTICE if p != q]
    assert len(pairs) == 6480
    t0 = time.time()
    done, fallback = [], False
    for p, q in pairs:
        if time.time() - t0 > B1_BUDGET_S:
            fallback = True
            break
        w = _walk(B_OPEN, B_H, B_W, SQUARE_CONTROLS, _va_to_rc(p), _va_to_rc(q))
        done.append((p, q, w["arrived"], w["steps"]))
    full_wall_s = time.time() - t0
    if fallback:
        starts = [(v, a) for v in (-4, 0, 4) for a in (-4, 0, 4)]
        pairs = [(p, q) for p in starts for q in B_LATTICE if p != q]
        t1 = time.time()
        done = []
        for p, q in pairs:
            w = _walk(B_OPEN, B_H, B_W, SQUARE_CONTROLS, _va_to_rc(p), _va_to_rc(q))
            done.append((p, q, w["arrived"], w["steps"]))
        fallback_wall_s = time.time() - t1
    else:
        fallback_wall_s = None
    arrived = sum(d[2] for d in done)
    match = sum(d[2] and d[3] == abs(d[0][0] - d[1][0]) + abs(d[0][1] - d[1][1]) for d in done)
    diff = subprocess.run(["git", "-C", ROOT, "diff", "--stat", START_COMMIT, RESULT_COMMIT,
                           "--", "runners/", "seeds/"], capture_output=True, text=True)
    _record("G-B1", {"n_pairs": len(pairs), "arrived": arrived, "steps_eq_manhattan": match,
                     "fallback_used": fallback, "full_run_wall_s": full_wall_s,
                     "fallback_wall_s": fallback_wall_s,
                     "git_diff_stat_runners_seeds": diff.stdout, "git_diff_rc": diff.returncode,
                     "mismatches": [d for d in done
                                    if not (d[2] and d[3] == abs(d[0][0] - d[1][0]) + abs(d[0][1] - d[1][1]))][:50]})
    assert diff.returncode == 0
    assert diff.stdout.strip() == "", f"mechanism changed:\n{diff.stdout}"
    assert arrived == len(pairs)
    assert match == len(pairs)


def test_GB2_open_affect_plane_is_metrically_blind():
    per_goal = []
    decode = None
    for q in B_LATTICE:
        wa, game, summary = _build_world(B_OPEN, B_H, B_W, SQUARE_CONTROLS, _va_to_rc((0, 0)),
                                         _va_to_rc(q))
        if decode is None:
            qs = _quanta(wa)
            decode = {"summary": summary,
                      "quanta": [(lo, hi, kind) for _, lo, hi, kind, _ in qs]}
        _tick2(wa, game, epoch=1)
        qs = _quanta(wa)
        goal_qd = _quantum_qdist_at(wa, _va_to_rc(q))
        per_goal.append({"goal": q, "goal_quantum_qdist": goal_qd, "n_quanta": len(qs)})
    qd_values = sorted({g["goal_quantum_qdist"] for g in per_goal}, key=str)
    _record("G-B2", {"decode": decode, "distinct_goal_qdist": qd_values,
                     "per_goal": per_goal})
    s = decode["summary"]
    assert s["quanta"] == 1 and s["portals"] == 0 and s["frontiers"] == 0
    (lo, hi, kind), = decode["quanta"]
    assert (lo, hi, kind) == ((1, 1), (9, 9), "passable")          # covers all 81 cells
    assert all(g["n_quanta"] == 1 for g in per_goal)
    assert qd_values == [0.0], f"qdist varies with goal: {qd_values}"


def _b3_belief():
    names = list(ANCHORS)
    vis = set()
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            vis.update(_stair(ANCHORS[names[a]], ANCHORS[names[b]]))
    return vis


_part_b3 = {}


def _run_part_b3():
    if _part_b3:
        return _part_b3
    vis = _b3_belief()
    passable = {_va_to_rc(p) for p in vis}
    rows = []
    summary = None
    for x in ANCHORS:
        for y in ANCHORS:
            if x == y:
                continue
            p, q = ANCHORS[x], ANCHORS[y]
            w = _walk(passable, B_H, B_W, SQUARE_CONTROLS, _va_to_rc(p), _va_to_rc(q),
                      record_start_qdist=True)
            summary = summary or w["summary"]
            man = abs(p[0] - q[0]) + abs(p[1] - q[1])
            rows.append({"from": x, "to": y, "arrived": w["arrived"], "steps": w["steps"],
                         "manhattan": man, "euclid": math.hypot(p[0] - q[0], p[1] - q[1]),
                         "start_qdist": w["start_qdist"]})
    _part_b3.update({"n_cells": len(vis), "rows": rows, "summary": summary})
    return _part_b3


def test_GB3_experience_map_consistency():
    res = _run_part_b3()
    rows = res["rows"]
    assert res["n_cells"] == 33
    assert len(rows) == 42
    arrived = sum(r["arrived"] for r in rows)
    below = [r for r in rows if r["arrived"] and r["steps"] < r["manhattan"]]
    _record("G-B3", {"n_cells": res["n_cells"], "n_pairs": len(rows), "arrived": arrived,
                     "below_manhattan": below,
                     "non_arrivals": [r for r in rows if not r["arrived"]]})
    assert arrived == 42
    assert not below


# ---------------------------------------------------------------------------------------------
# Exploratory arms (record, no assertion)
# ---------------------------------------------------------------------------------------------

def test_XB3_what_qdist_encodes_on_the_experience_map():
    res = _run_part_b3()
    rows = res["rows"]
    excess = [r["steps"] - r["manhattan"] for r in rows if r["arrived"]]
    hist = {}
    for e in excess:
        hist[e] = hist.get(e, 0) + 1
    qd = [r["start_qdist"] for r in rows]
    ok = [i for i, v in enumerate(qd) if v is not None]
    _record("X-B3", {
        "summary": res["summary"],
        "excess_steps_histogram": {str(k): v for k, v in sorted(hist.items())},
        "spearman_qdist_vs_euclid": _spearman([qd[i] for i in ok], [rows[i]["euclid"] for i in ok]),
        "spearman_qdist_vs_manhattan": _spearman([qd[i] for i in ok],
                                                 [rows[i]["manhattan"] for i in ok]),
        "n_with_qdist": len(ok),
        "rows": rows,
    })


def test_XA4_hexagonal_controls_on_the_same_machinery():
    H = W = 27
    centre = (13, 13)
    floor = {(r, c) for r in range(1, 26) for c in range(1, 26)}
    pts = _hex_points()
    rows = []
    t0 = time.time()
    for i, j, x, y, r, hd in pts:
        goal = (centre[0] + j, centre[1] + i)
        w = _walk(floor, H, W, HEX_CONTROLS, centre, goal)
        path = w["path"]
        rows.append({"i": i, "j": j, "x": x, "y": y, "r": r, "hexdist": hd,
                     "arrived": w["arrived"], "steps": w["steps"],
                     "revisits": len(path) - len(set(path))})
    arrived = [rw for rw in rows if rw["arrived"]]
    amps = _amps([(rw["x"], rw["y"], rw["steps"] / rw["r"]) for rw in arrived]) if arrived else {}
    _record("X-A4", {"n": len(rows), "arrived": len(arrived),
                     "steps_eq_hexdist": sum(rw["arrived"] and rw["steps"] == rw["hexdist"]
                                             for rw in rows),
                     "with_revisits": sum(rw["revisits"] > 0 for rw in rows),
                     "amps_over_arrived": amps, "wall_s": time.time() - t0, "rows": rows})
