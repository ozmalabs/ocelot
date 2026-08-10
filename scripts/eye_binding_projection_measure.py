#!/usr/bin/env python3
"""SHIP THE LINEAR EYE — measurement + observable-manifold gate (block 195000).

Prereg: `EYE_BINDING_PROJECTION_PREREG.md`, committed ALONE before any number here.

The fix: the eye opts into the 188000 `binding_projection` engine flag by default
(mechanical adapter config, no agent logic). The flag fires the scheduler rule
`ct_area_effort_tracks_live_salience` once per AREA instead of once per task-on-area
(the rule binds `task` but references it nowhere), collapsing an O(cells^2)
`term_eval:Attr` count to O(cells). The OBSERVABLE MANIFOLD is unchanged.

This module is IMPORT-INERT: it toggles NO shared flag at import time. Every flag
is set inside a function, on a freshly-built eye. Mechanical I/O + measurement only.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

ONSET_DB = 6.0
CARVE_MIN_COH = 0.5
CARVE_MIN_EVENTS = 2.5
SEED = 195000

EYE_NODE_TYPES = (
    "RetinalOnsetEvent", "VisionPolygon", "CognitiveArea", "CognitiveTask",
    "Retina", "RetinalColumn", "Photoreceptor", "Agent", "RetinalMotion",
    "RetinalSalience", "AreaLoad", "TaskResult",
)


# ------------------------------------------------------------------ eyes ------
def _moving_bar_eye(n_el, n_az, *, projection=True, wrong=False):
    """A moving-bar 2-D retina — the WORK-COUNT workload (self-contained)."""
    from domains.photon_eye import GraphEye
    ctx = {"retina_2d": True,
           "onset_threshold_db": ONSET_DB, "onset_refractory_epochs": 0.0,
           "visual_carve": True, "carve_min_coherence": CARVE_MIN_COH,
           "carve_min_events": CARVE_MIN_EVENTS,
           "binding_projection": projection}
    if wrong:
        ctx["binding_projection_wrong"] = True
    eye = GraphEye(n_az=n_az, n_el=n_el, context=ctx).build()
    return eye, eye.substrate._inner


def _bar_frame(n_el, n_az, phase):
    luma = np.full((n_el, n_az), 10.0)
    col = phase % n_az
    luma[:, col] = 200.0
    luma[:, (col + 1) % n_az] = 200.0
    return luma


# -------------------------------------------------- observable projections ----
def onset_signature(eye):
    """Sorted (azimuth=column_index, elevation=row_index) of every onset."""
    s = eye.substrate
    sig = []
    for nid in s.nodes("RetinalOnsetEvent"):
        a = s.node(nid)["attrs"]
        sig.append((a.get("column_index"), a.get("row_index")))
    return sorted(sig)


def _r(x, nd=6):
    return round(x, nd) if isinstance(x, float) else x


def carve_polygons(eye):
    """Sorted canonical-attr tuples of every VisionPolygon (carve output)."""
    s = eye.substrate
    keys = ("row_min", "row_max", "col_min", "col_max", "n_events",
            "coherence", "speed", "direction", "epoch")
    out = []
    for nid in s.nodes("VisionPolygon"):
        a = s.node(nid)["attrs"]
        out.append(tuple(_r(a.get(k)) if isinstance(a.get(k), float)
                         else a.get(k) for k in keys))
    return sorted(out, key=repr)


def area_effort(eye):
    s = eye.substrate
    out = {}
    for nid in s.nodes("CognitiveArea"):
        a = s.node(nid)["attrs"]
        out[a.get("name")] = _r(a.get("effort")) if isinstance(
            a.get("effort"), float) else a.get("effort")
    return dict(sorted(out.items(), key=repr))


def node_counts(eye):
    s = eye.substrate
    return {t: len(list(s.nodes(t))) for t in EYE_NODE_TYPES}


def manifold(eye):
    """The full observable manifold this rung gates on."""
    return {
        "onset_sig": onset_signature(eye),
        "carve_polys": carve_polygons(eye),
        "area_effort": area_effort(eye),
        "node_counts": node_counts(eye),
    }


def manifold_digest(m):
    blob = json.dumps(m, sort_keys=True, default=repr)
    return hashlib.blake2b(blob.encode(), digest_size=12).hexdigest()


# ------------------------------------------------- graph_to_dict analysis -----
def _raw_dump(inner):
    return inner.graph_to_dict()


def _node_multiset(d):
    """Nodes as a sorted multiset of (type, sorted-attr-items) — order-free."""
    out = []
    for n in d.get("nodes", []):
        attrs = tuple(sorted(
            (k, _r(v) if isinstance(v, float) else v)
            for k, v in n.get("attrs", {}).items()
            # drop nondeterministic wall-clock attrs (188000 precedent)
            if not (n.get("type") in ("AreaLoad", "TaskResult")
                    and k in ("service_wall_micros", "wall_micros"))))
        out.append((n.get("type"), n.get("id"), attrs))
    return sorted(out, key=repr)


def _edge_multiset(d):
    """Edges as a sorted multiset of (src, type, tgt) — order-free."""
    out = [(e.get("src"), e.get("type"), e.get("tgt")) for e in d.get("edges", [])]
    return sorted(out, key=repr)


def _canon(obj):
    return json.dumps(obj, sort_keys=True, default=repr)


def _raw_md5(d):
    return hashlib.md5(_canon(d).encode()).hexdigest()


# --------------------------------------------------------- WORK-COUNT ---------
def _fit_exp(cells, vals):
    xs = [math.log(c) for c in cells]
    ys = [math.log(max(v, 1e-9)) for v in vals]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


def _measure_tick(n_el, n_az, projection, warm=6, reps=3):
    import substrate_rs as srs
    eye, inner = _moving_bar_eye(n_el, n_az, projection=projection)
    rng = np.random.default_rng(SEED)
    from domains import doom_photon_world as dpw
    for t in range(warm):
        eye.submit_photons_2d(dpw.photon_packets(_bar_frame(n_el, n_az, t), rng))
        inner.run_cognitive_tasks(1)
        inner.run_rules()
        eye.prune_settled_tasks()
    srs._native.Substrate.scale_audit_set_enabled(True)
    srs._native.Substrate.scale_audit_reset()
    eye.submit_photons_2d(dpw.photon_packets(_bar_frame(n_el, n_az, warm), rng))
    inner.run_cognitive_tasks(1)
    inner.run_rules()
    snap = dict(srs._native.Substrate.scale_audit_snapshot())
    srs._native.Substrate.scale_audit_set_enabled(False)
    eye.prune_settled_tasks()
    onsets = len(list(eye.substrate.nodes("RetinalOnsetEvent")))
    times = []
    for r in range(reps):
        eye.submit_photons_2d(
            dpw.photon_packets(_bar_frame(n_el, n_az, warm + 1 + r), rng))
        inner.run_cognitive_tasks(1)
        t0 = time.perf_counter()
        inner.run_rules()
        times.append(time.perf_counter() - t0)
        eye.prune_settled_tasks()
    times.sort()
    return snap, onsets, times[len(times) // 2]


def work_count(scales=((12, 15), (16, 20), (24, 30), (32, 40))):
    rep = {}
    for projection in (False, True):
        arm = "on" if projection else "off"
        cells, attr, tev, ce, wall, ons = [], [], [], [], [], []
        rows = []
        for (ne, na) in scales:
            snap, onsets, wt = _measure_tick(ne, na, projection)
            n = ne * na
            cells.append(n)
            attr.append(snap.get("term_eval:Attr", 0))
            tev.append(snap.get("term_evals_total", 0))
            ce.append(snap.get("cand_enum", 0))
            wall.append(wt)
            ons.append(onsets)
            rows.append({"cells": n, "term_eval_Attr": snap.get("term_eval:Attr", 0),
                         "term_evals_total": snap.get("term_evals_total", 0),
                         "cand_enum": snap.get("cand_enum", 0),
                         "wall_ms": round(wt * 1e3, 3), "onsets": onsets})
        rep[arm] = {
            "rows": rows,
            "exp_term_eval_Attr": round(_fit_exp(cells, attr), 3),
            "exp_term_evals_total": round(_fit_exp(cells, tev), 3),
            "exp_cand_enum": round(_fit_exp(cells, ce), 3),
            "exp_wall": round(_fit_exp(cells, wall), 3),
            "onsets": ons,
        }
    rep["onsets_identical"] = rep["off"]["onsets"] == rep["on"]["onsets"]
    return rep


# ----------------------------------------------- OBSERVABLE-MANIFOLD GATE -----
def _bar_manifold(n_el, n_az, projection, hold=6, motion=5):
    from domains import doom_photon_world as dpw
    eye, inner = _moving_bar_eye(n_el, n_az, projection=projection)
    rng = np.random.default_rng(SEED)
    for t in range(hold + motion):
        eye.submit_photons_2d(dpw.photon_packets(_bar_frame(n_el, n_az, t), rng))
        inner.run_cognitive_tasks(1)
        inner.run_rules()
        if t < hold + motion - 1:
            eye.prune_settled_tasks()
    m = manifold(eye)
    raw = _raw_dump(inner)
    eye.stop()
    return m, raw


def _doom_eye(n_el, n_az, projection, wrong=False, hold=8, motion=6):
    """The landed 160x120 Doom carve crop (reuses the 188000 harness build)."""
    from scripts import per_sensor_epoch_measure as PSE
    from scripts import dirty_index_measure as DI
    from domains import doom_photon_world as dpw
    eye, inner = PSE.build_eye(n_el, n_az, accel=True, split=False)
    # The 188000 harness sets the flag itself; here drive it via OUR option
    # instead to exercise the shipped path. Rebuild via context:
    eye.stop()
    from domains.photon_eye import GraphEye
    from scripts import doom_carve_scale_measure as M
    ctx = {"retina_2d": True, "synchronous": True, "worker_capacity": 1,
           "onset_threshold_db": M.ONSET_DB, "onset_refractory_epochs": 0.0,
           "visual_carve": True, "carve_min_coherence": M.CARVE_MIN_COH,
           "carve_min_events": M.CARVE_MIN_EVENTS, "visual_motion": True,
           "visual_salience": True, "retina_accel": True,
           "binding_projection": projection}
    if wrong:
        ctx["binding_projection_wrong"] = True
    eye = GraphEye(n_az=n_az, n_el=n_el, adapt_rate=M.ADAPT_RATE,
                   context=ctx).build()
    inner = eye.substrate._inner
    lumas = PSE._fixture_lumas()
    f0 = DI._grid(lumas[0], n_el, n_az)
    for _ in range(hold):
        eye.submit_photons_2d(dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for luma in lumas[1:1 + motion]:
        g = DI._grid(luma, n_el, n_az)
        eye.submit_photons_2d(dpw.packets_from_counts(dpw.photon_counts(g, None), None))
    eye.settle_carve_2d(since_epoch=since)
    inner.run_cognitive_tasks(1)
    inner.run_rules()
    m = manifold(eye)
    raw = _raw_dump(inner)
    eye.stop()
    return m, raw


def manifold_gate(bar_scales=((8, 10), (12, 15), (16, 20))):
    """OFF ≡ ON on the observable manifold across scales + the Doom crop."""
    rows = []
    all_ok = True
    for (ne, na) in bar_scales:
        m_off, _ = _bar_manifold(ne, na, False)
        m_on, _ = _bar_manifold(ne, na, True)
        ok = manifold_digest(m_off) == manifold_digest(m_on)
        all_ok &= ok
        rows.append({"workload": f"moving_bar_{ne}x{na}",
                     "off_digest": manifold_digest(m_off),
                     "on_digest": manifold_digest(m_on),
                     "n_onsets": len(m_off["onset_sig"]),
                     "n_polys": len(m_off["carve_polys"]),
                     "identical": ok})
    # the landed Doom crop
    m_off, _ = _doom_eye(120, 160, False)
    m_on, _ = _doom_eye(120, 160, True)
    ok = manifold_digest(m_off) == manifold_digest(m_on)
    all_ok &= ok
    rows.append({"workload": "doom_carve_160x120",
                 "off_digest": manifold_digest(m_off),
                 "on_digest": manifold_digest(m_on),
                 "n_onsets": len(m_off["onset_sig"]),
                 "n_polys": len(m_off["carve_polys"]),
                 "identical": ok})
    return {"rows": rows, "all_identical": all_ok}


# ---------------------------------------- NON-OBSERVABLE-SCATTER IDENTIFY -----
#: The ONLY graph_to_dict attributes that differ run-to-run — literal elapsed-
#: time MEASUREMENTS. Exactly 188000's declared nondeterministic set. MEASURED
#: (not assumed) to be the entire OFF/ON raw difference on the shipped eye path.
WALLCLOCK_ATTRS = {("AreaLoad", "service_wall_micros"),
                   ("TaskResult", "wall_micros")}


def _strip_wallclock(d):
    import copy
    d = copy.deepcopy(d)
    for n in d.get("nodes", []):
        for t, k in WALLCLOCK_ATTRS:
            if n.get("type") == t:
                n.get("attrs", {}).pop(k, None)
    return d


def _differing_node_attrs(a, b):
    """Which (type, attr) pairs differ between two raw dumps (same node ids)."""
    def by_id(d):
        m = {}
        for n in d.get("nodes", []):
            m[n.get("id")] = (n.get("type"), n.get("attrs", {}))
        return m
    ma, mb = by_id(a), by_id(b)
    diffs = set()
    for nid, (t, at) in ma.items():
        bt = mb.get(nid, (None, {}))[1]
        for k in set(at) | set(bt):
            if at.get(k) != bt.get(k):
                diffs.add((t, k))
    return sorted(diffs)


def scatter_identification():
    """MEASURE what actually differs between the OFF and ON graph_to_dict, and
    prove it is NON-observable. Finding: the raw dumps differ, but the ONLY
    differing attributes are the two wall-clock timing measurements — they
    differ even between two identical OFF runs (run-to-run nondeterminism), and
    once they are stripped the full graph is BYTE-IDENTICAL OFF ≡ ON ≡ run-to-
    run. The node/edge SETS (and even list ORDER) are already identical."""
    _, raw_off1 = _doom_eye(120, 160, False)
    _, raw_off2 = _doom_eye(120, 160, False)
    _, raw_on = _doom_eye(120, 160, True)
    diff_off_off = _differing_node_attrs(raw_off1, raw_off2)   # nondeterminism
    diff_off_on = _differing_node_attrs(raw_off1, raw_on)      # OFF vs ON
    nodes_equal = _node_multiset(raw_off1) == _node_multiset(raw_on)
    edges_equal = _edge_multiset(raw_off1) == _edge_multiset(raw_on)
    edge_order_same = (
        [(e.get("src"), e.get("type"), e.get("tgt")) for e in raw_off1["edges"]]
        == [(e.get("src"), e.get("type"), e.get("tgt")) for e in raw_on["edges"]])
    node_order_same = ([n.get("id") for n in raw_off1["nodes"]]
                       == [n.get("id") for n in raw_on["nodes"]])
    s_off1 = _raw_md5(_strip_wallclock(raw_off1))
    s_off2 = _raw_md5(_strip_wallclock(raw_off2))
    s_on = _raw_md5(_strip_wallclock(raw_on))
    return {
        "raw_md5_off1": _raw_md5(raw_off1),
        "raw_md5_off2": _raw_md5(raw_off2),
        "raw_md5_on": _raw_md5(raw_on),
        "raw_md5_differs_off_vs_on": _raw_md5(raw_off1) != _raw_md5(raw_on),
        "raw_md5_differs_off_vs_off": _raw_md5(raw_off1) != _raw_md5(raw_off2),
        "differing_attrs_off_vs_off": [list(x) for x in diff_off_off],
        "differing_attrs_off_vs_on": [list(x) for x in diff_off_on],
        "scatter_is_wallclock_only":
            set(map(tuple, diff_off_on)) == WALLCLOCK_ATTRS and
            set(map(tuple, diff_off_off)) == WALLCLOCK_ATTRS,
        "node_set_identical": nodes_equal,
        "edge_set_identical": edges_equal,
        "node_list_order_identical": node_order_same,
        "edge_list_order_identical": edge_order_same,
        "wallclock_stripped_md5_off1": s_off1,
        "wallclock_stripped_byte_identical_off_on": s_off1 == s_on,
        "wallclock_stripped_deterministic_off_off": s_off1 == s_off2,
        "n_nodes": len(raw_off1.get("nodes", [])),
        "n_edges": len(raw_off1.get("edges", [])),
    }


# --------------------------------------------- UNSOUND-PROJECTION FALSIFIER ---
def _sched_efforts(projection, wrong):
    """area.effort per CognitiveArea on the 3-area scheduler scenario — the SAME
    rule (`ct_area_effort_tracks_live_salience`) the eye's per-tick cost is, run
    on a genuine MULTI-HUB graph so the projection's soundness is observable."""
    from scripts import per_sensor_epoch_measure as PSE
    ag = PSE._sched_agent(())
    PSE._set_projection(ag.inner, projection)
    if wrong:
        ag.inner.set_projection_overaggressive(True)
    PSE._sched_scenario(ag, n_areas=3, n_tasks=3)
    for _ in range(4):
        ag.inner.run_cognitive_tasks(1)
        ag.inner.run_rules()
    eff = {}
    for nid in ag.s.nodes("CognitiveArea"):
        a = ag.s.node(nid)["attrs"]
        eff[a["name"]] = _r(a.get("effort")) if isinstance(
            a.get("effort"), float) else a.get("effort")
    return dict(sorted(eff.items()))


def falsifier():
    """NON-VACUITY. Projecting away `area` — the var that IS used in the guard
    AND the effect — MUST break an observable when >1 hub matches. The eye is
    structurally ONE task-bearing area (`retina`), so sound and unsound coincide
    there (recorded); the mechanism's non-vacuity is therefore witnessed on the
    3-area scheduler running the SAME rule, where empty-var projection fires
    ONCE and leaves 2 of 3 areas' `effort` STALE — the `area.effort` observable
    diverges, while the SOUND projection is byte-identical to OFF."""
    off = _sched_efforts(False, False)
    sound = _sched_efforts(True, False)
    wrong = _sched_efforts(True, True)
    # the eye itself: one hub → sound and unsound observably coincide
    m_eye_sound, _ = _doom_eye(120, 160, projection=True, wrong=False)
    m_eye_wrong, _ = _doom_eye(120, 160, projection=True, wrong=True)
    return {
        "sched_effort_off": off,
        "sched_effort_sound": sound,
        "sched_effort_wrong": wrong,
        "sound_is_mirror_of_off": off == sound,
        "wrong_breaks_effort_observable": sound != wrong,
        "diverges": sound != wrong,
        "eye_single_hub_sound_eq_wrong":
            manifold_digest(m_eye_sound) == manifold_digest(m_eye_wrong),
    }


# ----------------------------------------------------------------- C1 ---------
def c1_default_is_committed():
    """OFF path (our adapter, binding_projection=False) is the committed oracle:
    its wall-clock-stripped graph_to_dict is BYTE-IDENTICAL to the ON path
    (== committed main), and deterministic. The ONLY raw difference OFF-vs-ON is
    the wall-clock scatter (which is also present OFF-vs-OFF)."""
    _m1, raw_off1 = _doom_eye(120, 160, False)
    _m2, raw_off2 = _doom_eye(120, 160, False)
    _m_on, raw_on = _doom_eye(120, 160, True)
    s_off1 = _raw_md5(_strip_wallclock(raw_off1))
    s_off2 = _raw_md5(_strip_wallclock(raw_off2))
    s_on = _raw_md5(_strip_wallclock(raw_on))
    return {
        "off_stripped_md5": s_off1,
        "off_stripped_deterministic": s_off1 == s_off2,
        "off_equals_on_stripped": s_off1 == s_on,
        "off_vs_on_raw_differs_only_by_wallclock":
            _raw_md5(raw_off1) != _raw_md5(raw_on) and s_off1 == s_on,
        "manifold_off_equals_on":
            manifold_digest(_m1) == manifold_digest(_m_on),
    }


def full_report():
    rep = {"seed": SEED}
    print("[§4 work-count] measuring OFF vs ON exponents ...")
    rep["work_count"] = work_count()
    print("[§3 manifold-gate] OFF ≡ ON across scales + Doom crop ...")
    rep["manifold_gate"] = manifold_gate()
    print("[§6 scatter] identifying the graph_to_dict difference ...")
    rep["scatter"] = scatter_identification()
    print("[§5 falsifier] unsound (empty-var) projection ...")
    rep["falsifier"] = falsifier()
    print("[§7 C1] OFF path == committed main ...")
    rep["c1"] = c1_default_is_committed()
    return rep


if __name__ == "__main__":
    import pprint
    r = full_report()
    outdir = os.path.join(ROOT, "results")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "eye_binding_projection.json"), "w") as f:
        json.dump(r, f, indent=2, default=repr)
    pprint.pprint(r)
