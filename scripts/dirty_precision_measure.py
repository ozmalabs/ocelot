#!/usr/bin/env python3
"""DIRTY-PROPAGATION PRECISION — the measurement harness (block 187000).

Prereg: `DIRTY_PRECISION_PREREG.md`, committed ALONE before any number here.

Block 186000 returned an HONEST NEGATIVE on the vision path: relabelling the
retina into six areas left all six dirty on every photon tick. It named
`dirty_by_writeset` as the culprit. **This harness does not assume that.** §1 is
a DIAGNOSIS that attributes every dirty-MARK on the real photon path to the code
path that made it, and only then does anything get measured about a build.

Mechanical I/O + measurement only. Every decision about what wakes what lives in
the Rust engine.

Arms:
  over-approx -> the committed blanket (`precise_dirty` OFF)  — the ORACLE
  precise     -> `precise_dirty` ON (key-precise + value-level)
  wrong       -> `dirty_overaggressive` ON (the falsifier; MUST diverge)
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

SEED = 187000
OUTDIR = os.path.join(ROOT, "results", "dirty_precision")
MAX_ROUNDS = 200_000

# The six-area relabelling block 186000 measured (scheduling metadata only —
# no committed seed file is edited).
AREA_SPLIT = (("retinal_mint_onset_2d", "v1_onset"),
              ("retinal_mint_carve_2d", "mt_carve"),
              ("retinal_mint_motion_2d", "mt_motion"),
              ("retinal_mint_salience_2d", "lip_salience"))


# ------------------------------------------------------------------ dumps -----
def canon(obj):
    """Canonical float-EXACT JSON text (`repr` on every float), so byte-identity
    is claimed at full precision and never at `str()`."""
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


#: The ONLY excluded attributes, NAMED (never a pattern, never a tolerance) —
#: wall-clock counters the runtime writes into the graph, so two runs of the
#: SAME binary on the SAME input differ in them. Inherited verbatim from 186000,
#: whose gate proves nothing else drifts.
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


def _set_precise(inner, on):
    """Set the flag, tolerating an engine that does not have it — so the SAME
    protocol can be run on the BASE engine (C1c) to compare DEFAULT-path dumps.
    A base engine can only run the OFF arm; asking it for ON is a hard error."""
    fn = getattr(inner, "set_precise_dirty", None)
    if fn is None:
        if on:
            raise RuntimeError("this engine has no set_precise_dirty — "
                               "the ON arm cannot be run on the base engine")
        return False
    fn(on)
    return True


def _set_telemetry(inner, on):
    fn = getattr(inner, "set_dirty_telemetry", None)
    if fn is None:
        if on:
            raise RuntimeError("this engine has no set_dirty_telemetry")
        return False
    fn(on)
    return True


# ------------------------------------------------------------------- eyes ------
def _fixture_lumas():
    from scripts import eye_accel_measure as EA
    lumas, _labels, _names = EA._load_fixture()
    return list(lumas)


def build_split_eye(n_el=15, n_az=20, *, precise=False, telemetry=False,
                    accel=False, split=True):
    """The 186000 six-area retina, verbatim (`set_rule_area` relabel only)."""
    from domains.photon_eye import GraphEye
    from scripts import doom_carve_scale_measure as M
    eye = GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=M.ADAPT_RATE,
        context={"retina_2d": True, "synchronous": True,
                 "worker_capacity": 1, "onset_threshold_db": M.ONSET_DB,
                 "onset_refractory_epochs": 0.0, "visual_carve": True,
                 "carve_min_coherence": M.CARVE_MIN_COH,
                 "carve_min_events": M.CARVE_MIN_EVENTS,
                 "visual_motion": True, "visual_salience": True,
                 "retina_accel": accel}).build()
    inner = eye.substrate._inner
    if split:
        for rule, area in AREA_SPLIT:
            inner.set_rule_area(rule, area)
    _set_precise(inner, precise)
    _set_telemetry(inner, telemetry)
    return eye, inner


# ------------------------------------------------------- §1 THE DIAGNOSIS ------
def diagnose(n_el=15, n_az=20, hold=8, accel=False, precise=False):
    """WHICH over-approximation dominates, on the REAL photon path.

    Counts, per PLAIN photon tick (the 186000 protocol exactly: submit ->
    run_cognitive_tasks -> settle -> prune):

      * dirty MARKS by path — P1 `dirty_by_writeset` (rule effects),
        P2 `mark_edge_type_dirty`, P3 the EXTERNAL-write blanket;
      * SPURIOUS marks: rules attempted that made NO progress;
      * NO-OP writes: `set_attr` calls whose value equalled the stored value.

    Telemetry only — the over-approximate (committed) path throughout.
    """
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    f0 = DI._grid(lumas[0], n_el, n_az)
    eye, inner = build_split_eye(n_el, n_az, precise=precise, telemetry=True,
                                 accel=accel)
    rows = []
    for t in range(hold):
        # RESET FIRST: the marks this tick's EXTERNAL writes make (the photon
        # submission + the cognitive-task completions) are precisely what the
        # settlement event then has to face.
        inner.reset_dirty_marks()
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
        inner.run_cognitive_tasks(1)
        m_pre = inner.dirty_marks()
        dirty_before = inner.dirty_rule_count()
        areas_before = inner.dirty_area_names()
        names_before = sorted(inner.dirty_rule_names())
        t0 = time.perf_counter()
        r = inner.run_rules_settle(0, MAX_ROUNDS, False, False)
        secs = time.perf_counter() - t0
        m = inner.dirty_marks()
        m = dict(m)
        m["pre_settle"] = m_pre
        attempted = sum(row["attempted"] for rd in r["rounds"] for row in rd["rows"])
        steps = r["steps"]
        rows.append({
            "tick": t, "seconds": secs,
            "dirty_rules_at_tick_start": dirty_before,
            "dirty_areas_at_tick_start": areas_before,
            "dirty_rule_names_at_tick_start": names_before,
            "areas_that_worked": sorted({row["area"] for rd in r["rounds"]
                                         for row in rd["rows"]}),
            "rule_attempts": attempted, "progressing_steps": steps,
            "spurious_attempts": attempted - steps,
            "marks": m,
        })
        eye.prune_settled_tasks()
    eye.stop()
    # The last SETTLED tick is the honest one (the first ticks are the
    # install-time all-dirty transient; 186000's adapt-then-perturb discipline).
    last = rows[-1]
    pre = last["marks"]["pre_settle"]
    tot = pre["writeset"] + pre["edge_type"] + pre["external"]
    return {
        "n_el": n_el, "n_az": n_az, "hold": hold, "accel": accel,
        "precise": precise, "rows": rows,
        "settled_tick": {
            "marks_total_before_settlement": tot,
            "P1_writeset": pre["writeset"],
            "P2_edge_type": pre["edge_type"],
            "P3_external": pre["external"],
            "P1_frac": (pre["writeset"] / tot) if tot else 0.0,
            "P2_frac": (pre["edge_type"] / tot) if tot else 0.0,
            "P3_frac": (pre["external"] / tot) if tot else 0.0,
            "external_write_events": pre["external_events"],
            "attr_writes": pre["attr_writes"],
            "noop_attr_writes": pre["noop_attr_writes"],
            "noop_frac": (pre["noop_attr_writes"] / max(1, pre["attr_writes"])),
            "marks_total_whole_tick": (last["marks"]["writeset"]
                                       + last["marks"]["edge_type"]
                                       + last["marks"]["external"]),
            "rule_attempts": last["rule_attempts"],
            "progressing_steps": last["progressing_steps"],
            "spurious_attempts": last["spurious_attempts"],
            "spurious_frac": (last["spurious_attempts"]
                              / max(1, last["rule_attempts"])),
            "dirty_rules": last["dirty_rules_at_tick_start"],
            "dirty_areas": last["dirty_areas_at_tick_start"],
            "dirty_rule_names": last["dirty_rule_names_at_tick_start"],
        },
    }


def epoch_coupling(n_el=120, n_az=160, hold=80):
    """WHY every area stays awake — the counterfactual that NAMES the coupling.

    Reports (a) every active rule whose read-set contains `Attr("input_epoch")`
    with its area, and (b) the dirty set on a settled plain photon tick with the
    per-cell epoch STAMP ON vs OFF (185000's `retina_dirty_stamp_epoch`).

    (b) is a DIAGNOSTIC counterfactual, NOT a claim: 185000 measured that
    dropping the stamp is exact on everything OBSERVABLE but is not whole-graph
    byte-identical, and this rung claims nothing about it. It is here to answer
    one question — is the shared epoch stamp what couples the areas?
    """
    from domains.photon_eye import GraphEye
    from domains import doom_photon_world as dpw
    from scripts import doom_carve_scale_measure as M
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    f0 = DI._grid(lumas[0], n_el, n_az)
    out = {}
    for tag, stamp in (("stamp_ON_as_shipped", True), ("stamp_OFF_counterfactual", False)):
        eye = GraphEye(
            n_az=n_az, n_el=n_el, adapt_rate=M.ADAPT_RATE,
            context={"retina_2d": True, "synchronous": True,
                     "worker_capacity": 1, "onset_threshold_db": M.ONSET_DB,
                     "onset_refractory_epochs": 0.0, "visual_carve": True,
                     "carve_min_coherence": M.CARVE_MIN_COH,
                     "carve_min_events": M.CARVE_MIN_EVENTS,
                     "visual_motion": True, "visual_salience": True,
                     "retina_accel": True, "retina_dirty": True,
                     "retina_dirty_stamp_epoch": stamp}).build()
        inner = eye.substrate._inner
        for rule, area in AREA_SPLIT:
            inner.set_rule_area(rule, area)
        inner.set_precise_dirty(True)
        inner.set_dirty_telemetry(True)
        counts = dpw.photon_counts(f0, None)
        for _ in range(hold):
            eye.submit_photons_2d(
                dpw.packets_from_counts(counts, None),
                dirty=np.arange(n_el * n_az))
        inner.run_rules_settle(0, MAX_ROUNDS, False, False)
        inner.reset_dirty_marks()
        eye.submit_photons_2d(dpw.packets_from_counts(counts, None),
                              dirty=np.arange(n_el * n_az))
        m = inner.dirty_marks()
        out[tag] = {
            "dirty_areas": inner.dirty_area_names(),
            "n_dirty_areas": len(inner.dirty_area_names()),
            "dirty_rules": sorted(inner.dirty_rule_names()),
            "attr_writes": m["attr_writes"],
            "noop_attr_writes": m["noop_attr_writes"],
            "external_marks": m["external"],
        }
        if tag.startswith("stamp_ON"):
            out["rules_reading_input_epoch"] = sorted(
                inner.rules_reading_attr("input_epoch"))
            # THE ISOLATION PROBE. Settle, then make exactly ONE write: the
            # retina ROOT's `input_epoch` (what `submit_photons_2d` does first,
            # unconditionally, outside every accelerator flag). NO rule reads
            # `input_epoch` ON THAT NODE — they read it on `rod` / `task` /
            # `column` / `area` — so at INSTANCE granularity this write would
            # wake nobody. At KEY granularity it wakes all of them.
            inner.run_rules_settle(0, MAX_ROUNDS, False, False)
            inner.reset_dirty_marks()
            before = inner.dirty_rule_count()
            eye.substrate.set_attr(eye._retina, "input_epoch", eye._epoch + 999)
            out["one_root_epoch_write"] = {
                "dirty_rules_before": before,
                "dirty_rules_after": inner.dirty_rule_count(),
                "dirty_areas_after": inner.dirty_area_names(),
                "woken": sorted(inner.dirty_rule_names()),
                "marks": inner.dirty_marks(),
            }
            print("[epoch-coupling ONE ROOT WRITE] "
                  f"{before} -> {inner.dirty_rule_count()} dirty rules, "
                  f"{len(inner.dirty_area_names())} areas: "
                  f"{inner.dirty_area_names()}")
        print(f"[epoch-coupling {tag}] areas={out[tag]['n_dirty_areas']} "
              f"{out[tag]['dirty_areas']} marks={m['external']} "
              f"noop={m['noop_attr_writes']}/{m['attr_writes']}")
        eye.stop()
    return out


def noop_vs_hold(n_el=120, n_az=160, holds=(1, 5, 10, 20, 40, 80, 120)):
    """How much of the per-cell receptor write becomes a NO-OP as the sheet
    ADAPTS. Block 185000 measured the receptor EMA reaching an EXACT float64
    fixed point (t*~71 at rate 0.4); this is the same fact read through the
    dirty path — once a cell's state stops moving, four of its five per-cell
    writes stop changing anything, and the fifth (`input_epoch`) never does.
    """
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    out = []
    for h in holds:
        eye, inner = build_split_eye(n_el, n_az, precise=True, telemetry=True,
                                     accel=True)
        f0 = DI._grid(lumas[0], n_el, n_az)
        for _ in range(h):
            eye.submit_photons_2d(
                dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
        inner.reset_dirty_marks()
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
        m = inner.dirty_marks()
        out.append({"hold": h, "attr_writes": m["attr_writes"],
                    "noop_attr_writes": m["noop_attr_writes"],
                    "noop_frac": m["noop_attr_writes"] / max(1, m["attr_writes"]),
                    "external_marks": m["external"]})
        print(f"[noop@hold={h:<4}] {out[-1]['noop_frac']*100:.1f}% no-op "
              f"({m['noop_attr_writes']}/{m['attr_writes']}), "
              f"marks={m['external']}")
        eye.stop()
    return out


# --------------------------------------------------- §2 BYTE-IDENTITY ----------
def _wl_vision_carve(precise, wrong=False, n_el=15, n_az=20, hold=8, motion=6):
    """The REAL 2-D retina on the GRAPH path (`retina_accel=False`) — the
    `run_rules` oracle that carries the carve/motion/salience settle ops."""
    from domains import doom_photon_world as dpw
    from scripts import eye_accel_measure as EA
    lumas = _fixture_lumas()
    eye, inner = build_split_eye(n_el, n_az, precise=precise, split=False)
    if wrong:
        inner.set_dirty_overaggressive(True)
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


def _wl_scheduler(precise, wrong=False, extra=()):
    agent = _sched_agent(extra)
    _set_precise(agent.inner, precise)
    if wrong:
        agent.inner.set_dirty_overaggressive(True)
    _sched_scenario(agent, n_areas=3, n_tasks=3)
    for _ in range(4):
        agent.inner.run_cognitive_tasks(1)
        agent.inner.run_rules()
    return dump(agent.inner)


def _wl_quiet_areas(precise, wrong=False):
    return _wl_scheduler(precise, wrong,
                         extra=("information_commitment", "spatial_belief_core"))


def _wl_conversation(precise, wrong=False):
    from substrate.world_adapter import WorldAdapter
    agent = WorldAdapter()
    _set_precise(agent.inner, precise)
    if wrong:
        agent.inner.set_dirty_overaggressive(True)
    for text in ("hello there", "the moon is cold",
                 "i think it is bright", "tell me more"):
        agent.add_inbound(text)
        agent.inner.run_rules()
    return dump(agent.inner)


def _wl_doom_accel(precise, wrong=False, n_el=120, n_az=160, hold=8, motion=6):
    """The SHIPPED Doom configuration: 160x120, `retina_accel` ON. The sheet is
    one FFI pass, but every per-cell receptor write still goes through
    `Substrate::set_attr` — i.e. straight through the dirty path this rung
    touches — and the carve/motion/salience settle ops still run `run_rules`."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    eye, inner = build_split_eye(n_el, n_az, precise=precise, accel=True,
                                 split=False)
    if wrong:
        inner.set_dirty_overaggressive(True)
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


def _decompose(a_raw, b_raw):
    """When two dumps differ, say EXACTLY how: node list, node SET, edge list,
    edge SET, `next_id`. An ORDER difference and a CONTENT difference are not
    the same finding and must never be reported as one."""
    na = [canon(n) for n in a_raw["nodes"]]
    nb = [canon(n) for n in b_raw["nodes"]]
    ea = [canon(e) for e in a_raw["edges"]]
    eb = [canon(e) for e in b_raw["edges"]]
    return {
        "next_id_identical": a_raw["next_id"] == b_raw["next_id"],
        "node_list_ordered_identical": na == nb,
        "node_set_identical": sorted(na) == sorted(nb),
        "edge_list_ordered_identical": ea == eb,
        "edge_set_identical": sorted(ea) == sorted(eb),
        "n_nodes": (len(na), len(nb)), "n_edges": (len(ea), len(eb)),
    }


#: Workloads whose protocol can hand back the RAW dict (for the decomposition)
#: and whose endpoint can be probed for a genuine fixpoint.
def _raw_and_fixpoint(precise):
    """Run `conversation` and return (raw dump, steps the COMMITTED loop still
    makes after every rule is force-dirtied). Zero steps proves the endpoint is
    a genuine fixpoint of the WHOLE rule system — i.e. no wake was missed."""
    from substrate.world_adapter import WorldAdapter
    agent = WorldAdapter()
    _set_precise(agent.inner, precise)
    for text in ("hello there", "the moon is cold",
                 "i think it is bright", "tell me more"):
        agent.add_inbound(text)
        agent.inner.run_rules()
    raw = agent.inner.graph_to_dict()
    agent.inner.set_precise_dirty(False)
    agent.inner.force_all_dirty()
    steps = agent.inner.run_rules()
    after = agent.inner.graph_to_dict()
    return raw, steps, canon(_strip_wallclock(after)) == canon(
        _strip_wallclock(json.loads(json.dumps(raw))))


def byte_identity():
    out = {}
    for name, fn in WORKLOADS.items():
        off = fn(False)
        on = fn(True)
        out[name] = {
            "over_approx": digest(off), "precise": digest(on),
            "identical": off == on,
            "chars": len(off),
        }
        print(f"[C2a {name}] over={out[name]['over_approx']} "
              f"precise={out[name]['precise']} "
              f"{'IDENTICAL' if out[name]['identical'] else '*** DIVERGES ***'}")
    # THE DECOMPOSITION + THE FIXPOINT PROOF, on the one workload that moved.
    raw_off, steps_off, fp_off = _raw_and_fixpoint(False)
    raw_on, steps_on, fp_on = _raw_and_fixpoint(True)
    out["conversation_decomposition"] = _decompose(raw_off, raw_on)
    out["conversation_fixpoint_probe"] = {
        "over_approx_steps_after_force_all_dirty": steps_off,
        "precise_steps_after_force_all_dirty": steps_on,
        "over_approx_graph_unchanged_by_probe": fp_off,
        "precise_graph_unchanged_by_probe": fp_on,
    }
    print("[C2a conversation DECOMPOSITION]",
          json.dumps(out["conversation_decomposition"], indent=1))
    print("[C2a conversation FIXPOINT PROBE]",
          json.dumps(out["conversation_fixpoint_probe"], indent=1))
    return out


def default_path_dump():
    """C1c — the DEFAULT (precise OFF) dumps, for comparison against the BASE
    engine's own run of the same protocol."""
    out = {}
    for name, fn in WORKLOADS.items():
        d = fn(False)
        out[name] = digest(d)
        print(f"[C1c default {name}] {out[name]}")
    return out


def wrong_precision():
    """F1 — the over-aggressive predicate MUST break byte-identity."""
    out = {}
    for name, fn in WORKLOADS.items():
        good = fn(True)
        bad = fn(True, wrong=True)
        out[name] = {"precise": digest(good), "overaggressive": digest(bad),
                     "diverges": good != bad}
        print(f"[F1 {name}] {'DIVERGES (falsifier holds)' if out[name]['diverges'] else 'identical -- NON-VACUITY NOT SHOWN'}")
    return out


# --------------------------------------------- §3 landed 160x120 carve --------
def landed_carve(precise):
    """C2b — the LANDED Doom carve at 160x120 (seed 182000, Poisson sensor),
    through `dirty_index_measure`'s committed protocol. The pinned facts are
    4 polygons / union_iou 0.1215 / carve_precision 0.9784."""
    from scripts import dirty_index_measure as DI
    from scripts import eye_accel_measure as EA
    lumas_full, labels_full, names = EA._load_fixture()
    lumas = list(lumas_full)
    lg160 = [EA._downsample_labels(labels_full[i], 120, 160)
             for i in range(1, labels_full.shape[0])]
    nm160 = [names[i] for i in range(1, labels_full.shape[0])]
    orig = DI.build_eye

    def patched(*a, **k):
        eye = orig(*a, **k)
        _set_precise(eye.substrate._inner, precise)
        return eye

    DI.build_eye = patched
    try:
        r = DI.poisson_carve_run(lumas, lg160, nm160, 120, 160, arm="accel")
    finally:
        DI.build_eye = orig
    return {"n_polygons": len(r["polygons"]),
            "union_iou": r.get("union_iou"),
            "carve_precision": r.get("carve_precision"),
            "false_polygons": r.get("false_polygons"),
            "onset_digest": digest(canon(r["onset_stream"])),
            "rod_digest": digest(canon(r["rod"]))}


# ------------------------------------- §4 dirty count + cost vs change ---------
def scene_fraction_sweep(fracs=(0.0, 0.01, 0.05, 0.25, 1.0), n_el=15, n_az=20,
                         hold=10, probe=6, reps=5):
    """H1/H2/H3 — dirty AREAS and per-tick cost as a function of the fraction of
    the SCENE that changed, on the 186000 six-area retina.

    Protocol (the 185000/186000 adapt-then-perturb discipline): hold a static
    frame until the sheet has SETTLED, then change exactly `frac` of the cells
    and measure the settlement event that follows. Measuring straight after
    build would time 'try every rule once' and say nothing about surprise.
    """
    from domains import doom_photon_world as dpw
    from scripts import eye_accel_measure as EA
    lumas = _fixture_lumas()
    base = EA._area_mean(lumas[0], n_el, n_az)
    alt = EA._area_mean(lumas[3], n_el, n_az)
    n = n_el * n_az
    rng = np.random.default_rng(SEED)
    order = rng.permutation(n)
    out = {"n_el": n_el, "n_az": n_az, "reps": reps, "sweep": []}
    for frac in fracs:
        k = int(round(frac * n))
        cells = set(int(x) for x in order[:k])
        grid = base.copy()
        for c in cells:
            grid[c // n_az, c % n_az] = alt[c // n_az, c % n_az]
        for arm, precise in (("over_approx", False), ("precise", True)):
            secs, areas, dirty_rules, attempts = [], None, None, None
            for _ in range(reps):
                eye, inner = build_split_eye(n_el, n_az, precise=precise)
                for _ in range(hold):
                    eye.submit_photons_2d(dpw.packets_from_counts(
                        dpw.photon_counts(base, None), None))
                    inner.run_cognitive_tasks(1)
                    inner.run_rules_settle(0, MAX_ROUNDS, False, False)
                    eye.prune_settled_tasks()
                # THE PERTURBATION: `frac` of the sheet changes.
                tk = []
                for _ in range(probe):
                    eye.submit_photons_2d(dpw.packets_from_counts(
                        dpw.photon_counts(grid, None), None))
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
                "dirty_rules": dirty_rules, "rule_attempts": attempts,
            })
            print(f"[H frac={frac:<5} {arm:<11}] areas={len(areas)} "
                  f"dirty_rules={dirty_rules} attempts={attempts} "
                  f"t={statistics.median(secs)*1e3:.3f} ms")
    return out


def cost_attribution(n_el=15, n_az=20, hold=12, probe=8):
    """WHERE the 2.87 ms per photon tick actually goes, per rule.

    The rung's negative is only honest if it says what the time IS, not just
    what it is not. `rule_costs` is the engine's own always-on per-rule
    instrumentation: (name, micros, times processed, times progressed)."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = _fixture_lumas()
    f0 = DI._grid(lumas[0], n_el, n_az)
    out = {}
    for arm, precise in (("over_approx", False), ("precise", True)):
        eye, inner = build_split_eye(n_el, n_az, precise=precise)
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
            "probe_ticks": probe,
            "wall_seconds_total": wall,
            "wall_ms_per_tick": wall / probe * 1e3,
            "rule_micros_total": total,
            "rule_ms_per_tick": total / probe / 1e3,
            "top_rules": [{"rule": r[0], "micros": r[1], "processed": r[2],
                           "progressed": r[3],
                           "frac_of_rule_time": r[1] / max(1, total)}
                          for r in rows[:8]],
        }
        print(f"[cost {arm}] {out[arm]['wall_ms_per_tick']:.3f} ms/tick wall, "
              f"{out[arm]['rule_ms_per_tick']:.3f} ms/tick inside rules")
        for r in out[arm]["top_rules"][:4]:
            print(f"    {r['frac_of_rule_time']*100:5.1f}%  {r['rule']} "
                  f"(processed {r['processed']}, progressed {r['progressed']})")
        eye.stop()
    return out


# ------------------------------------------------ §5 NO-FREE-LUNCH ------------
def no_free_lunch(n_rules=64, n_writes=400, reps=7):
    """F2 — when EVERY write genuinely changes something that EVERY rule reads,
    precise must cost the SAME or slightly MORE than the blanket. Built so the
    precise predicate can skip NOTHING: one shared attr key, every rule reads it
    in its where-clause, every write changes the value."""
    from substrate.world_adapter import WorldAdapter

    def build(precise):
        agent = WorldAdapter(seeds=())
        _set_precise(agent.inner, precise)
        src = agent.s.add_node("NflSrc", {"v": 0.0})
        tgt = agent.s.add_node("NflTgt", {"v": 0.0})
        agent.inner.add_edge_unchecked(src, "nfl_edge", tgt)
        for i in range(n_rules):
            agent.inner.add_rule({
                "name": f"nfl_{i}",
                "match": [["s", "nfl_edge", "t"]],
                "where": {"type": "Gt",
                          "a": {"type": "Attr", "node": {"type": "Var", "name": "s"},
                                "key": "v"},
                          "b": {"type": "Lit", "value": 1e18}},
                "effects": [["set_attr_if_different", "t", "v", 1.0]],
            })
        agent.inner.run_rules()
        return agent, src

    out = {}
    for arm, precise in (("over_approx", False), ("precise", True)):
        ts = []
        for _ in range(reps):
            agent, src = build(precise)
            t0 = time.perf_counter()
            for w in range(n_writes):
                agent.s.set_attr(src, "v", float(w + 1))
                agent.inner.run_rules()
            ts.append(time.perf_counter() - t0)
        out[arm] = {"median_seconds": statistics.median(ts),
                    "spread": (min(ts), max(ts))}
    out["ratio_precise_over_approx"] = (out["precise"]["median_seconds"]
                                        / out["over_approx"]["median_seconds"])
    print(f"[F2 no-free-lunch] over={out['over_approx']['median_seconds']*1e3:.2f} ms "
          f"precise={out['precise']['median_seconds']*1e3:.2f} ms "
          f"ratio={out['ratio_precise_over_approx']:.3f}")
    return out


# ------------------------------------------------------------------ main -------
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    os.makedirs(OUTDIR, exist_ok=True)
    from domains.engine_provenance import engine_preamble, provenance_line
    print(provenance_line(ROOT))
    engine_preamble(ROOT)
    want = set(argv) or {"diagnose", "identity", "wrong", "landed", "sweep",
                         "nfl", "default", "noop", "epoch", "cost"}
    rep = {"seed_block": [SEED, SEED + 999]}
    if "diagnose" in want:
        rep["diagnosis"] = diagnose()
        print("[§1 DIAGNOSIS graph 20x15 OVER-APPROX]",
              json.dumps(rep["diagnosis"]["settled_tick"], indent=1))
        rep["diagnosis_precise"] = diagnose(precise=True)
        print("[§1 same tick, PRECISE]",
              json.dumps(rep["diagnosis_precise"]["settled_tick"], indent=1))
        rep["diagnosis_doom_accel"] = diagnose(n_el=120, n_az=160, hold=6,
                                               accel=True)
        print("[§1 DIAGNOSIS doom 160x120 accel OVER-APPROX]",
              json.dumps(rep["diagnosis_doom_accel"]["settled_tick"], indent=1))
        rep["diagnosis_doom_accel_precise"] = diagnose(
            n_el=120, n_az=160, hold=6, accel=True, precise=True)
        print("[§1 doom 160x120 accel, PRECISE]",
              json.dumps(rep["diagnosis_doom_accel_precise"]["settled_tick"],
                         indent=1))
    if "noop" in want:
        rep["noop_vs_hold"] = noop_vs_hold()
    if "epoch" in want:
        rep["epoch_coupling"] = epoch_coupling()
    if "default" in want:
        rep["C1c_default_dumps"] = default_path_dump()
    if "identity" in want:
        rep["C2a_byte_identity"] = byte_identity()
    if "landed" in want:
        rep["C2b_landed_carve"] = {"over_approx": landed_carve(False),
                                   "precise": landed_carve(True)}
        print("[C2b]", json.dumps(rep["C2b_landed_carve"], indent=1))
    if "wrong" in want:
        rep["F1_wrong_precision"] = wrong_precision()
    if "sweep" in want:
        rep["H_scene_fraction"] = scene_fraction_sweep()
    if "nfl" in want:
        rep["F2_no_free_lunch"] = no_free_lunch()
    if "cost" in want:
        rep["cost_attribution"] = cost_attribution()
    path = os.path.join(OUTDIR, "dirty_precision.json")
    prev = {}
    if os.path.exists(path):
        prev = json.load(open(path))
    prev.update(rep)
    with open(path, "w") as fh:
        json.dump(prev, fh, indent=1, default=str)
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
