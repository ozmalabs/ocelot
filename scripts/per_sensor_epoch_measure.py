#!/usr/bin/env python3
"""PER-SENSOR EPOCH + THE EXPENSIVE MATCH — the measurement harness (188000).

Prereg: `PER_SENSOR_EPOCH_PREREG.md`, committed ALONE before any number here.

Two mechanisms, both DEFAULT OFF, measured separately and together:

  * `binding_projection` (engine flag) — a DROPPABLE, BYTE-IDENTICAL MIRROR.
    Deduplicate a rule's binding set on the variables its where-clause and
    effects actually reference. Byte-identity IS claimed.
  * `per_sensor_epoch` (eye context flag) — a SEMANTIC change. Each sensor's
    clock carries its own KEY and advances on its own change. Whole-graph
    byte-identity is NOT claimed and is NOT the gate; OBSERVABLE identity is,
    with the digest delta shown to be epoch-only.

Mechanical I/O + measurement only. Every decision lives in the Rust engine or
in graph data.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

SEED = 188000
OUTDIR = os.path.join(ROOT, "results", "per_sensor_epoch")
MAX_ROUNDS = 200_000

#: 186000's six-area relabelling (scheduling metadata only; no seed file edited).
AREA_SPLIT = (("retinal_mint_onset_2d", "v1_onset"),
              ("retinal_mint_carve_2d", "mt_carve"),
              ("retinal_mint_motion_2d", "mt_motion"),
              ("retinal_mint_salience_2d", "lip_salience"))

#: The four ARMS. (binding_projection, per_sensor_epoch)
ARMS = (("committed", False, False),
        ("projection", True, False),
        ("per_sensor", False, True),
        ("both", True, True))

EPOCH_KEYS = ("input_epoch", "rod_epoch", "column_epoch", "retina_epoch",
              "percept_epoch")


# ------------------------------------------------------------------ dumps -----
def canon(obj):
    if isinstance(obj, float):
        return "f" + repr(obj)
    if isinstance(obj, bool):
        return "b" + repr(obj)
    if isinstance(obj, int):
        return "i" + repr(obj)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(canon(x) for x in obj) + "]"
    if isinstance(obj, dict):
        return "{" + ",".join(
            repr(k) + ":" + canon(obj[k]) for k in sorted(obj, key=repr)) + "}"
    return repr(obj)


NONDETERMINISTIC_ATTRS = {("AreaLoad", "service_wall_micros"),
                          ("TaskResult", "wall_micros")}


def _strip_wallclock(d):
    for node in d.get("nodes", []):
        for _t, key in NONDETERMINISTIC_ATTRS:
            if node.get("type") == _t:
                node["attrs"].pop(key, None)
    return d


def dump(inner):
    return canon(_strip_wallclock(inner.graph_to_dict()))


def digest(text):
    import hashlib
    return hashlib.blake2b(text.encode(), digest_size=8).hexdigest()


def _set_projection(inner, on):
    fn = getattr(inner, "set_binding_projection", None)
    if fn is None:
        if on:
            raise RuntimeError("this engine has no set_binding_projection")
        return False
    fn(on)
    return True


# ------------------------------------------------------------------- eyes ------
def _fixture_lumas():
    from scripts import eye_accel_measure as EA
    lumas, _labels, _names = EA._load_fixture()
    return list(lumas)


def build_eye(n_el=15, n_az=20, *, projection=False, per_sensor=False,
              wrong_epoch=False, accel=False, split=True, telemetry=False):
    """The 186000 six-area retina, verbatim, plus this rung's two flags."""
    from domains.photon_eye import GraphEye
    from scripts import doom_carve_scale_measure as M
    ctx = {"retina_2d": True, "synchronous": True,
           "worker_capacity": 1, "onset_threshold_db": M.ONSET_DB,
           "onset_refractory_epochs": 0.0, "visual_carve": True,
           "carve_min_coherence": M.CARVE_MIN_COH,
           "carve_min_events": M.CARVE_MIN_EVENTS,
           "visual_motion": True, "visual_salience": True,
           "retina_accel": accel}
    if per_sensor:
        ctx["per_sensor_epoch"] = True
    if wrong_epoch:
        ctx["per_sensor_epoch_wrong"] = True
    eye = GraphEye(n_az=n_az, n_el=n_el, adapt_rate=M.ADAPT_RATE,
                   context=ctx).build()
    inner = eye.substrate._inner
    if split:
        for rule, area in AREA_SPLIT:
            inner.set_rule_area(rule, area)
    _set_projection(inner, projection)
    if telemetry:
        inner.set_dirty_telemetry(True)
    return eye, inner


# ------------------------------------------------- §1 THE MAP + the probe ------
def epoch_map(n_el=120, n_az=160, hold=6):
    """WHICH rules read WHICH epoch key, per arm, and 187000's isolation probe.

    The probe: settle the eye to zero dirty rules, then make exactly ONE write —
    the retina ROOT's clock, what `submit_photons_2d` does first, unconditionally.
    187000 measured 0 -> 8 dirty rules across 6 areas from that single write.
    """
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    f0 = DI._grid(lumas[0], n_el, n_az)
    out = {}
    for tag, per_sensor in (("committed", False), ("per_sensor", True)):
        eye, inner = build_eye(n_el, n_az, per_sensor=per_sensor, accel=True,
                               telemetry=True)
        inner.set_precise_dirty(True)
        counts = dpw.photon_counts(f0, None)
        for _ in range(hold):
            eye.submit_photons_2d(dpw.packets_from_counts(counts, None))
        inner.run_rules_settle(0, MAX_ROUNDS, False, False)
        readers = {k: sorted(inner.rules_reading_attr(k)) for k in EPOCH_KEYS}
        inner.reset_dirty_marks()
        before = inner.dirty_rule_count()
        eye.substrate.set_attr(eye._retina, eye._retina_epoch_key,
                               eye._epoch + 999)
        probe = {"root_key": eye._retina_epoch_key,
                 "dirty_rules_before": before,
                 "dirty_rules_after": inner.dirty_rule_count(),
                 "dirty_areas_after": inner.dirty_area_names(),
                 "woken": sorted(inner.dirty_rule_names())}
        out[tag] = {"readers": readers, "one_root_epoch_write": probe,
                    "projectable_rules": inner.projectable_rules()}
        print(f"[§1 {tag}] one root write: {before} -> "
              f"{probe['dirty_rules_after']} dirty rules, "
              f"{len(probe['dirty_areas_after'])} areas "
              f"{probe['dirty_areas_after']}")
        for k in EPOCH_KEYS:
            if readers[k]:
                print(f"    {k}: {len(readers[k])} readers "
                      f"{[r[1] for r in readers[k]]}")
        eye.stop()
    return out


# --------------------------------------------------- §2 the WORKLOAD set -------
def _wl_vision_carve(projection, per_sensor=False, wrong_projection=False,
                     n_el=15, n_az=20, hold=8, motion=6):
    """The REAL 2-D retina on the GRAPH path — the `run_rules` oracle."""
    from domains import doom_photon_world as dpw
    from scripts import eye_accel_measure as EA
    lumas = _fixture_lumas()
    eye, inner = build_eye(n_el, n_az, projection=projection,
                           per_sensor=per_sensor, split=False)
    if wrong_projection:
        inner.set_projection_overaggressive(True)
    f0 = EA._area_mean(lumas[0], n_el, n_az)
    for _ in range(hold):
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
        inner.run_cognitive_tasks(1)
        inner.run_rules()
        eye.prune_settled_tasks()
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for luma in lumas[1:1 + motion]:
        g = EA._area_mean(luma, n_el, n_az)
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(g, None), None))
        inner.run_cognitive_tasks(1)
        inner.run_rules()
        eye.prune_settled_tasks()
    eye.settle_carve_2d(since_epoch=since)
    eye.settle_motion_2d(since_epoch=since)
    eye.settle_salience_2d(since_epoch=since)
    inner.run_cognitive_tasks(1)
    inner.run_rules()
    out = dump(inner)
    eye.stop()
    return out


def _sched_agent(extra_seeds=()):
    from substrate.world_adapter import WorldAdapter
    agent = WorldAdapter(seeds=())
    for name in ("cognitive_areas", "cognitive_scheduler") + tuple(extra_seeds):
        path = os.path.join(ROOT, "seeds", name + ".json")
        agent.inner.load_seed_manifest(json.load(open(path)), agent.agent)
    return agent


def _sched_scenario(agent, n_areas=1, n_tasks=2):
    for a in range(n_areas):
        area = agent.s.add_node("CognitiveArea", {
            "name": f"test{a}", "status": "active", "input_epoch": 2,
            "logical_tick": 0, "desired_workers": 1, "effort": 0.0,
            "last_residual_epoch": -1})
        dst = agent.s.add_node("CognitiveArea", {
            "name": f"dst{a}", "status": "active", "input_epoch": 1,
            "logical_tick": 0, "desired_workers": 1, "effort": 0.0,
            "last_residual_epoch": -1})
        agent.inner.add_edge_unchecked(area, "projects_to", dst)
        res = agent.s.add_node("Residual", {"epoch": 5 + a})
        agent.inner.add_edge_unchecked(area, "has_residual", res)
        load = agent.s.add_node("AreaLoad", {
            "queued": 3, "failed": 0, "fold_conflicts": 0,
            "capacity_workers": 2})
        agent.inner.add_edge_unchecked(area, "has_area_load", load)
        for i in range(n_tasks):
            t = agent.s.add_node("CognitiveTask", {
                "status": "pending", "kind": "abs_diff_energy",
                "payload": [float(i), float(i + 1)], "input_epoch": 2,
                "salience": 0.9 - 0.1 * i, "logical_time": i,
                "area": f"test{a}", "order": 2, "effort": 1})
            agent.inner.add_edge_unchecked(area, "has_task", t)


def _wl_scheduler(projection, per_sensor=False, wrong_projection=False,
                  extra=()):
    agent = _sched_agent(extra)
    _set_projection(agent.inner, projection)
    if wrong_projection:
        agent.inner.set_projection_overaggressive(True)
    _sched_scenario(agent, n_areas=3, n_tasks=3)
    for _ in range(4):
        agent.inner.run_cognitive_tasks(1)
        agent.inner.run_rules()
    return dump(agent.inner)


def _wl_quiet_areas(projection, per_sensor=False, wrong_projection=False):
    return _wl_scheduler(projection, per_sensor, wrong_projection,
                         extra=("information_commitment", "spatial_belief_core"))


def _wl_conversation(projection, per_sensor=False, wrong_projection=False):
    from substrate.world_adapter import WorldAdapter
    agent = WorldAdapter()
    _set_projection(agent.inner, projection)
    if wrong_projection:
        agent.inner.set_projection_overaggressive(True)
    for text in ("hello there", "the moon is cold",
                 "i think it is bright", "tell me more"):
        agent.add_inbound(text)
        agent.inner.run_rules()
    return dump(agent.inner)


def _wl_doom_accel(projection, per_sensor=False, wrong_projection=False,
                   n_el=120, n_az=160, hold=8, motion=6):
    """The SHIPPED Doom configuration: 160x120, `retina_accel` ON."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    eye, inner = build_eye(n_el, n_az, projection=projection,
                           per_sensor=per_sensor, accel=True, split=False)
    if wrong_projection:
        inner.set_projection_overaggressive(True)
    f0 = DI._grid(lumas[0], n_el, n_az)
    for _ in range(hold):
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for luma in lumas[1:1 + motion]:
        g = DI._grid(luma, n_el, n_az)
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(g, None), None))
    eye.settle_carve_2d(since_epoch=since)
    inner.run_cognitive_tasks(1)
    inner.run_rules()
    out = dump(inner)
    eye.stop()
    return out


WORKLOADS = {
    "vision_carve": _wl_vision_carve,
    "scheduler": _wl_scheduler,
    "quiet_areas": _wl_quiet_areas,
    "conversation": _wl_conversation,
    "doom_accel_160x120": _wl_doom_accel,
}
#: The workloads the eye's per-sensor epoch can touch at all.
VISION_WORKLOADS = ("vision_carve", "doom_accel_160x120")


def default_dumps():
    """C1 — the DEFAULT (both flags OFF) dumps. Compared against the BASE
    engine's own run of this same protocol, run from the canonical tree."""
    out = {}
    for name, fn in WORKLOADS.items():
        out[name] = digest(fn(False))
        print(f"[C1 default {name}] {out[name]}")
    return out


def projection_identity():
    """C2a — `binding_projection` ON vs OFF, whole-graph, float-exact."""
    out = {}
    for name, fn in WORKLOADS.items():
        off, on = fn(False), fn(True)
        out[name] = {"off": digest(off), "on": digest(on),
                     "identical": off == on}
        print(f"[C2a {name}] {'IDENTICAL' if off == on else '*** DIVERGES ***'}")
    return out


def wrong_projection():
    """F1b — the over-aggressive projection MUST break byte-identity."""
    out = {}
    for name, fn in WORKLOADS.items():
        good, bad = fn(True), fn(True, wrong_projection=True)
        out[name] = {"good": digest(good), "overaggressive": digest(bad),
                     "diverges": good != bad}
        print(f"[F1b {name}] "
              f"{'DIVERGES (falsifier holds)' if good != bad else 'identical'}")
    return out


# ------------------------------------- §3 OBSERVABLE identity (per-sensor) -----
def _rod_state(eye, keys=("adaptation", "activation", "prev_activation",
                          "caught_quanta")):
    n = eye.n_az * eye.n_el
    rods = [eye._receptors[(f, "rod")] for f in range(n)]
    return {k: [repr(x) for x in eye.substrate.get_attr_many(rods, k)]
            for k in keys}


def landed_carve(projection=False, per_sensor=False, wrong_epoch=False):
    """C2b / C3a — the LANDED Doom carve at 160x120 (4 / 0.1215 / 0.9784 / 0),
    through `dirty_index_measure`'s committed Poisson protocol."""
    from scripts import dirty_index_measure as DI
    from scripts import eye_accel_measure as EA
    lumas_full, labels_full, names = EA._load_fixture()
    lumas = list(lumas_full)
    lg160 = [EA._downsample_labels(labels_full[i], 120, 160)
             for i in range(1, labels_full.shape[0])]
    nm160 = [names[i] for i in range(1, labels_full.shape[0])]
    orig_build, orig_rod = DI.build_eye, DI.rod_state

    def patched(n_el, n_az, **k):
        from domains.photon_eye import GraphEye
        from scripts import doom_carve_scale_measure as M
        ctx = {"retina_2d": True, "synchronous": True, "worker_capacity": 1,
               "onset_threshold_db": M.ONSET_DB, "onset_refractory_epochs": 0.0,
               "visual_carve": True, "carve_min_coherence": M.CARVE_MIN_COH,
               "carve_min_events": M.CARVE_MIN_EVENTS,
               "retina_accel": k.get("accel", True),
               "retina_accel_perturb": k.get("perturb", False),
               "retina_dirty": k.get("dirty", False),
               "retina_dirty_stamp_epoch": k.get("stamp", True),
               "retina_dirty_naive": k.get("naive", False),
               "retina_dirty_shed": k.get("shed", False)}
        if per_sensor:
            ctx["per_sensor_epoch"] = True
        if wrong_epoch:
            ctx["per_sensor_epoch_wrong"] = True
        eye = GraphEye(n_az=n_az, n_el=n_el, adapt_rate=M.ADAPT_RATE,
                       context=ctx).build()
        _set_projection(eye.substrate._inner, projection)
        return eye

    DI.build_eye = patched
    #: the epoch attr is EXPECTED to move under per-sensor; the four STATE
    #: attrs are the observable and are compared at full precision.
    DI.rod_state = lambda eye: _rod_state(eye)
    try:
        r = DI.poisson_carve_run(lumas, lg160, nm160, 120, 160, arm="accel")
    finally:
        DI.build_eye, DI.rod_state = orig_build, orig_rod
    return {"n_polygons": len(r["polygons"]),
            "union_iou": r.get("union_iou"),
            "carve_precision": r.get("carve_precision"),
            "false_polygons": r.get("false_polygons"),
            "onset_digest": digest(canon(r["onset_stream"])),
            "n_onsets": len(r["onset_stream"]),
            "rod_state_digest": digest(canon(r["rod"]))}


def graph_path_onsets(per_sensor=False, wrong_epoch=False, n_el=15, n_az=20,
                      hold=8, motion=6):
    """The GRAPH path's onset stream — the ONLY place a rod's epoch is READ by
    a rule (`retinal_mint_onset_2d`). This is where the wrong-epoch falsifier
    has to bite; on the accel path the epoch is bookkeeping the mirror never
    reads, so a check there would be vacuous and is reported as such."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    from scripts import eye_accel_measure as EA
    lumas = _fixture_lumas()
    eye, inner = build_eye(n_el, n_az, per_sensor=per_sensor,
                           wrong_epoch=wrong_epoch, split=False)
    f0 = EA._area_mean(lumas[0], n_el, n_az)
    for _ in range(hold):
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
        inner.run_cognitive_tasks(1)
        inner.run_rules()
        eye.prune_settled_tasks()
    for luma in lumas[1:1 + motion]:
        g = EA._area_mean(luma, n_el, n_az)
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(g, None), None))
        inner.run_cognitive_tasks(1)
        inner.run_rules()
        eye.prune_settled_tasks()
    stream = DI.onset_stream(eye)
    rods = _rod_state(eye)
    eye.stop()
    return {"n_onsets": len(stream), "onset_digest": digest(canon(stream)),
            "rod_state_digest": digest(canon(rods))}


def _attr_delta(raw_a, raw_b):
    """C3b — the ATTRIBUTE-LEVEL diff of two whole-graph dumps. Returns the set
    of `(node_type, attr_key)` whose value differs, plus keys present in one
    arm and absent in the other. If anything but an epoch key appears here, the
    per-sensor arm has moved something it must not have."""
    def index(raw):
        out = {}
        for n in raw["nodes"]:
            out[n["id"]] = (n.get("type"), n.get("attrs", {}))
        return out
    ia, ib = index(raw_a), index(raw_b)
    moved, only_a, only_b = set(), set(), set()
    for nid, (ty, aa) in ia.items():
        if nid not in ib:
            continue
        _tb, bb = ib[nid]
        for k in set(aa) | set(bb):
            if k not in bb:
                only_a.add((ty, k))
            elif k not in aa:
                only_b.add((ty, k))
            elif canon(aa[k]) != canon(bb[k]):
                moved.add((ty, k))
    return {"changed_value": sorted(moved),
            "only_in_committed": sorted(only_a),
            "only_in_per_sensor": sorted(only_b),
            "node_ids_only_committed": sorted(set(ia) - set(ib))[:20],
            "node_ids_only_per_sensor": sorted(set(ib) - set(ia))[:20],
            "n_nodes": (len(ia), len(ib))}


def digest_delta(n_el=120, n_az=160, hold=8, motion=6):
    """C3b on the SHIPPED Doom path: whole-graph, attribute-level."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    raws = {}
    for tag, per_sensor in (("committed", False), ("per_sensor", True)):
        eye, inner = build_eye(n_el, n_az, per_sensor=per_sensor, accel=True,
                               split=False)
        f0 = DI._grid(lumas[0], n_el, n_az)
        for _ in range(hold):
            eye.submit_photons_2d(
                dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
        for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
            eye.substrate.remove_node(nid)
        since = eye._epoch + 1
        for luma in lumas[1:1 + motion]:
            g = DI._grid(luma, n_el, n_az)
            eye.submit_photons_2d(
                dpw.packets_from_counts(dpw.photon_counts(g, None), None))
        eye.settle_carve_2d(since_epoch=since)
        inner.run_cognitive_tasks(1)
        inner.run_rules()
        raws[tag] = _strip_wallclock(inner.graph_to_dict())
        eye.stop()
    d = _attr_delta(raws["committed"], raws["per_sensor"])
    print("[C3b digest delta]", json.dumps(d, indent=1, default=str))
    return d


# ---------------------------------------- §4 dirty areas + cost vs change ------
def scene_fraction_sweep(fracs=(0.0, 0.01, 0.05, 0.25, 1.0), n_el=15, n_az=20,
                         hold=10, probe=6, reps=5, accel=False, arms=ARMS):
    """H1/H2 — dirty AREAS and per-tick cost vs the fraction of the SCENE that
    changed. 187000's adapt-then-perturb protocol verbatim: hold a static frame
    until the sheet SETTLES, then change exactly `frac` of the cells."""
    from domains import doom_photon_world as dpw
    from scripts import eye_accel_measure as EA
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    grid = DI._grid if accel else EA._area_mean
    base = grid(lumas[0], n_el, n_az)
    alt = grid(lumas[3], n_el, n_az)
    n = n_el * n_az
    rng = np.random.default_rng(SEED)
    order = rng.permutation(n)
    out = {"n_el": n_el, "n_az": n_az, "reps": reps, "accel": accel,
           "sweep": []}
    for frac in fracs:
        k = int(round(frac * n))
        cells = [int(x) for x in order[:k]]
        scene = base.copy()
        for c in cells:
            scene[c // n_az, c % n_az] = alt[c // n_az, c % n_az]
        for arm, projection, per_sensor in arms:
            secs, areas, dirty_rules, attempts = [], None, None, None
            for _ in range(reps):
                eye, inner = build_eye(n_el, n_az, projection=projection,
                                       per_sensor=per_sensor, accel=accel)
                inner.set_precise_dirty(True)
                for _ in range(hold):
                    eye.submit_photons_2d(dpw.packets_from_counts(
                        dpw.photon_counts(base, None), None))
                    inner.run_cognitive_tasks(1)
                    inner.run_rules_settle(0, MAX_ROUNDS, False, False)
                    eye.prune_settled_tasks()
                tk = []
                for _ in range(probe):
                    eye.submit_photons_2d(dpw.packets_from_counts(
                        dpw.photon_counts(scene, None), None))
                    inner.run_cognitive_tasks(1)
                    a = inner.dirty_area_names()
                    d = inner.dirty_rule_count()
                    t0 = time.perf_counter()
                    r = inner.run_rules_settle(0, MAX_ROUNDS, False, False)
                    tk.append(time.perf_counter() - t0)
                    eye.prune_settled_tasks()
                secs.append(statistics.median(tk))
                areas, dirty_rules = a, d
                attempts = sum(row["attempted"] for rd in r["rounds"]
                               for row in rd["rows"])
                eye.stop()
            out["sweep"].append({
                "change_fraction": frac, "changed_cells": k, "arm": arm,
                "median_tick_seconds": statistics.median(secs),
                "spread_seconds": (min(secs), max(secs)),
                "dirty_areas": areas, "n_dirty_areas": len(areas),
                "dirty_rules": dirty_rules, "rule_attempts": attempts})
            print(f"[{'accel' if accel else 'graph'} frac={frac:<5} "
                  f"{arm:<11}] areas={len(areas)} rules={dirty_rules} "
                  f"attempts={attempts} "
                  f"t={statistics.median(secs)*1e3:.3f} ms  {areas}")
    return out


def cost_attribution(n_el=15, n_az=20, hold=12, probe=8, arms=ARMS):
    """H3 / P2 — WHERE the per-tick time goes, per rule, per arm."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    f0 = DI._grid(lumas[0], n_el, n_az)
    out = {}
    for arm, projection, per_sensor in arms:
        eye, inner = build_eye(n_el, n_az, projection=projection,
                               per_sensor=per_sensor)
        for _ in range(hold):
            eye.submit_photons_2d(
                dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
            inner.run_cognitive_tasks(1)
            inner.run_rules_settle(0, MAX_ROUNDS, False, False)
            eye.prune_settled_tasks()
        inner.reset_rule_costs()
        t0 = time.perf_counter()
        for _ in range(probe):
            eye.submit_photons_2d(
                dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
            inner.run_cognitive_tasks(1)
            inner.run_rules_settle(0, MAX_ROUNDS, False, False)
            eye.prune_settled_tasks()
        wall = time.perf_counter() - t0
        rows = [r for r in inner.rule_costs() if r[1] > 0]
        rows.sort(key=lambda r: -r[1])
        total = sum(r[1] for r in rows)
        out[arm] = {
            "probe_ticks": probe, "wall_ms_per_tick": wall / probe * 1e3,
            "rule_ms_per_tick": total / probe / 1e3,
            "top_rules": [{"rule": r[0], "micros": r[1], "processed": r[2],
                           "progressed": r[3],
                           "frac_of_rule_time": r[1] / max(1, total)}
                          for r in rows[:8]]}
        print(f"[cost {arm:<11}] {out[arm]['wall_ms_per_tick']:.3f} ms/tick "
              f"wall, {out[arm]['rule_ms_per_tick']:.3f} ms/tick in rules")
        for r in out[arm]["top_rules"][:3]:
            print(f"    {r['frac_of_rule_time']*100:5.1f}%  {r['rule']} "
                  f"(processed {r['processed']}, progressed {r['progressed']})")
        eye.stop()
    return out


def accel_cost_attribution(n_el=120, n_az=160, hold=8, probe=4,
                           arms=(("committed", False, False),
                                 ("per_sensor", False, True))):
    """WHY cutting the accel path's dirty areas 6 -> 2 buys no time: which rules
    the settlement actually spends it in, per arm. A woken rule with an EMPTY
    match set is nearly free; the time is somewhere else, and this says where."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    f0 = DI._grid(lumas[0], n_el, n_az)
    out = {}
    for arm, projection, per_sensor in arms:
        eye, inner = build_eye(n_el, n_az, projection=projection,
                               per_sensor=per_sensor, accel=True)
        inner.set_precise_dirty(True)
        for _ in range(hold):
            eye.submit_photons_2d(
                dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
            inner.run_rules_settle(0, MAX_ROUNDS, False, False)
        inner.reset_rule_costs()
        settle = 0.0
        for _ in range(probe):
            eye.submit_photons_2d(
                dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
            t0 = time.perf_counter()
            inner.run_rules_settle(0, MAX_ROUNDS, False, False)
            settle += time.perf_counter() - t0
        rows = [r for r in inner.rule_costs() if r[1] > 0]
        rows.sort(key=lambda r: -r[1])
        total = sum(r[1] for r in rows)
        out[arm] = {
            "settle_ms_per_tick": settle / probe * 1e3,
            "rule_ms_per_tick": total / probe / 1e3,
            "dirty_areas": inner.dirty_area_names(),
            "top_rules": [{"rule": r[0], "micros": r[1], "processed": r[2],
                           "progressed": r[3],
                           "frac_of_rule_time": r[1] / max(1, total)}
                          for r in rows[:6]]}
        print(f"[accel-cost {arm:<11}] settle {out[arm]['settle_ms_per_tick']:.3f}"
              f" ms/tick, rules {out[arm]['rule_ms_per_tick']:.3f} ms/tick")
        for r in out[arm]["top_rules"][:4]:
            print(f"    {r['frac_of_rule_time']*100:5.1f}%  {r['rule']} "
                  f"(processed {r['processed']}, progressed {r['progressed']})")
        eye.stop()
    return out


def per_sensor_lag(n_el=120, n_az=160, holds=(8, 40, 80, 120)):
    """Does the rod's clock ACTUALLY become the rod's own time? On a
    bit-repeatable input the receptor EMA reaches an exact float64 fixed point
    (185000: t* ~ 71 at rate 0.4). Past it a settled rod's epoch STOPS
    advancing — that is per-sensor time, measured, not asserted. Under the
    default POISSON sensor no cell is ever bitwise settled, so the per-sensor
    clock degenerates to the global one; that is reported too, not hidden."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    f0 = DI._grid(lumas[0], n_el, n_az)
    n = n_el * n_az
    out = []
    for h in holds:
        for tag, rng_seed in (("noiseless", None), ("poisson", SEED)):
            eye, inner = build_eye(n_el, n_az, per_sensor=True, accel=True)
            rng = None if rng_seed is None else np.random.default_rng(rng_seed)
            for _ in range(h):
                if rng is None:
                    eye.submit_photons_2d(
                        dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
                else:
                    eye.submit_photons_2d(dpw.photon_packets(f0, rng))
            rods = [eye._receptors[(f, "rod")] for f in range(n)]
            ep = eye.substrate.get_attr_many(rods, "rod_epoch")
            lag = sum(1 for e in ep if e is None or int(e) < eye._epoch)
            out.append({"hold": h, "sensor": tag, "epoch": eye._epoch,
                        "rods_whose_clock_lags": lag,
                        "frac_lagging": lag / n})
            print(f"[lag hold={h:<4} {tag:<9}] {lag}/{n} rod clocks lag "
                  f"({lag / n * 100:.1f}%)")
            eye.stop()
    return out


# ------------------------------------------------ §5 NO-FREE-LUNCH ------------
def no_free_lunch(n_el=15, n_az=20, hold=10, probe=8, reps=5):
    """F2 — when the WHOLE scene changes every tick there is no quiet sensor, so
    the per-sensor epoch must cost the same or slightly MORE."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    frames = [DI._grid(l, n_el, n_az) for l in lumas[:6]]
    out = {}
    for arm, projection, per_sensor in (("committed", False, False),
                                        ("per_sensor", False, True)):
        ts = []
        for _ in range(reps):
            eye, inner = build_eye(n_el, n_az, projection=projection,
                                   per_sensor=per_sensor, accel=True)
            for i in range(hold):
                eye.submit_photons_2d(dpw.packets_from_counts(
                    dpw.photon_counts(frames[i % len(frames)], None), None))
            t0 = time.perf_counter()
            for i in range(probe):
                eye.submit_photons_2d(dpw.packets_from_counts(
                    dpw.photon_counts(frames[i % len(frames)], None), None))
            ts.append((time.perf_counter() - t0) / probe)
            eye.stop()
        out[arm] = {"median_seconds": statistics.median(ts),
                    "spread": (min(ts), max(ts))}
    out["ratio_per_sensor_over_committed"] = (
        out["per_sensor"]["median_seconds"] / out["committed"]["median_seconds"])
    print(f"[F2 no-free-lunch] committed "
          f"{out['committed']['median_seconds']*1e3:.3f} ms  per_sensor "
          f"{out['per_sensor']['median_seconds']*1e3:.3f} ms  ratio "
          f"{out['ratio_per_sensor_over_committed']:.3f}")
    return out


# ------------------------------------------------------------------ main -------
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    os.makedirs(OUTDIR, exist_ok=True)
    from domains.engine_provenance import engine_preamble, provenance_line
    print(provenance_line(ROOT))
    engine_preamble(ROOT)
    want = set(argv) or {"map", "default", "identity", "wrong", "landed",
                         "delta", "falsifier", "sweep", "cost", "accelcost",
                         "lag", "nfl"}
    rep = {"seed_block": [SEED, SEED + 999]}
    if "map" in want:
        rep["epoch_map"] = epoch_map()
    if "default" in want:
        rep["C1_default_dumps"] = default_dumps()
    if "identity" in want:
        rep["C2a_projection_identity"] = projection_identity()
    if "wrong" in want:
        rep["F1b_wrong_projection"] = wrong_projection()
    if "landed" in want:
        rep["C2b_C3a_landed_carve"] = {
            "committed": landed_carve(),
            "projection": landed_carve(projection=True),
            "per_sensor": landed_carve(per_sensor=True),
            "both": landed_carve(projection=True, per_sensor=True)}
        print("[C2b/C3a]", json.dumps(rep["C2b_C3a_landed_carve"], indent=1))
    if "delta" in want:
        rep["C3b_digest_delta"] = digest_delta()
    if "falsifier" in want:
        rep["F1a_wrong_epoch"] = {
            "committed": graph_path_onsets(),
            "per_sensor": graph_path_onsets(per_sensor=True),
            "wrong_epoch": graph_path_onsets(per_sensor=True, wrong_epoch=True)}
        print("[F1a]", json.dumps(rep["F1a_wrong_epoch"], indent=1))
    if "sweep" in want:
        rep["H2_graph_sweep"] = scene_fraction_sweep(accel=False)
        rep["H1_accel_sweep"] = scene_fraction_sweep(
            accel=True, n_el=120, n_az=160, hold=8, probe=4, reps=3)
    if "cost" in want:
        rep["H3_cost_attribution"] = cost_attribution()
    if "accelcost" in want:
        rep["accel_cost_attribution"] = accel_cost_attribution()
    if "lag" in want:
        rep["per_sensor_lag"] = per_sensor_lag()
    if "nfl" in want:
        rep["F2_no_free_lunch"] = no_free_lunch()
    path = os.path.join(OUTDIR, "per_sensor_epoch.json")
    prev = json.load(open(path)) if os.path.exists(path) else {}
    prev.update(rep)
    with open(path, "w") as fh:
        json.dump(prev, fh, indent=1, default=str)
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
