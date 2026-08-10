#!/usr/bin/env python3
"""PER-AREA ASYNC SETTLEMENT — the measurement harness (block 186000).

Prereg: `SETTLEMENT_PER_AREA_PREREG.md`, committed ALONE before any number here.

The thesis: a cortex tick is a SETTLEMENT EVENT that CARRIES a residual. The
committed global `run_rules` fixpoint is CLOSED-ACCOUNT settlement (residual==0
IS its termination condition) and a synchronous barrier. `run_rules_settle` is
the OPEN-ACCOUNT form: each area settles as much as its BUDGET affords, then
carries the rest.

This script is MECHANICAL I/O + measurement only. Every decision about what
settles when lives in the Rust engine and in the rules' own `area` metadata.

Arms, all driven through ONE substitutable engine call:
  global   -> inner.run_rules()                       (the committed oracle)
  settle-U -> inner.run_rules_settle(0, ...)          (UNBOUNDED budget)
  settle-b -> inner.run_rules_settle(b, ...)          (FINITE budget, carried)
  drop-b   -> inner.run_rules_settle(b, ..., True)    (FINITE budget, DISCARDED)
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

SEED = 186000
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(RESULTS, "per_area_settlement")
MAX_ROUNDS = 200_000


# ------------------------------------------------------------------ dumps -----
def canon(obj):
    """Canonical, float-exact JSON text for a graph dump. `repr()` on every
    float so a byte-identity claim is made at full precision, never at str()."""
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


#: The ONLY attributes excluded from a byte-identity dump, NAMED (never a
#: pattern, never a tolerance). Both are WALL-CLOCK instrumentation the runtime
#: writes into the graph, so they differ between two runs of the SAME binary on
#: the SAME input — measured, not assumed: two consecutive `run_rules` runs of
#: every workload here differ in EXACTLY these two keys and in nothing else
#: (node ids, `next_id` and the whole edge set all reproduce exactly).
NONDETERMINISTIC_ATTRS = {("AreaLoad", "service_wall_micros"),
                          ("TaskResult", "wall_micros")}


def _strip_wallclock(d):
    for node in d.get("nodes", []):
        for _t, key in NONDETERMINISTIC_ATTRS:
            if node.get("type") == _t:
                node["attrs"].pop(key, None)
    return d


def dump(inner):
    """The FULL graph state, float-exact. `graph_to_dict` is the engine's own
    persistence form — every node id/type/attr and every edge — minus the two
    named wall-clock counters above."""
    return canon(_strip_wallclock(inner.graph_to_dict()))


# ------------------------------------------------------------------- arms ------
class Driver:
    """The substitutable engine call. `reports` accumulates the settlement
    ledgers so the residual curve is read off the MECHANISM, not re-derived."""

    def __init__(self, kind, budget=0, drop=False, snapshot=False):
        self.kind = kind
        self.budget = budget
        self.drop = drop
        self.snapshot = snapshot
        self.reports = []
        self.seconds = []

    def __call__(self, inner):
        t0 = time.perf_counter()
        if self.kind == "global":
            out = inner.run_rules()
        else:
            out = inner.run_rules_settle(self.budget, MAX_ROUNDS, self.drop,
                                         self.snapshot)
            self.reports.append(out)
        self.seconds.append(time.perf_counter() - t0)
        return out


# -------------------------------------------------------------- workloads ------
# Each workload is a PROTOCOL: it takes the engine driver and returns the final
# full graph dump. Identical material in every arm; only the driver differs.

def _fixture_lumas():
    from scripts import eye_accel_measure as EA
    lumas, _labels, _names = EA._load_fixture()
    return list(lumas)


def wl_vision_carve(run, n_el=15, n_az=20, hold=8, motion_frames=6):
    """THE VISION PATH — the real retina, on the GRAPH (`retina_accel=False`),
    i.e. the `run_rules` oracle path that carries the carve/motion/salience
    settle ops. Areas present: `scheduler` (10 rules) + `retina`.
    """
    from domains.photon_eye import GraphEye
    from domains import doom_photon_world as dpw
    from scripts import doom_carve_scale_measure as M
    from scripts import eye_accel_measure as EA

    lumas = _fixture_lumas()

    def grid(luma):
        return EA._area_mean(luma, n_el, n_az)

    eye = GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=M.ADAPT_RATE,
        context={"retina_2d": True, "synchronous": True, "worker_capacity": 1,
                 "onset_threshold_db": M.ONSET_DB,
                 "onset_refractory_epochs": 0.0,
                 "visual_carve": True, "carve_min_coherence": M.CARVE_MIN_COH,
                 "carve_min_events": M.CARVE_MIN_EVENTS,
                 "visual_motion": True, "visual_salience": True,
                 "retina_accel": False}).build()
    inner = eye.substrate._inner
    f0 = grid(lumas[0])
    for _ in range(hold):
        eye.submit_photons_2d(dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
        inner.run_cognitive_tasks(1)
        run(inner)
        eye.prune_settled_tasks()
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for luma in lumas[1:1 + motion_frames]:
        g = grid(luma)
        eye.submit_photons_2d(dpw.packets_from_counts(dpw.photon_counts(g, None), None))
        inner.run_cognitive_tasks(1)
        run(inner)
        eye.prune_settled_tasks()
    # THE NAMED BOTTLENECK: the per-AREA settle ops.
    eye.settle_carve_2d(since_epoch=since)
    eye.settle_motion_2d(since_epoch=since)
    eye.settle_salience_2d(since_epoch=since)
    inner.run_cognitive_tasks(1)
    run(inner)
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
    """The real scheduler scenario from `test_seizure_dynamics_migrated`:
    areas with tasks, a residual, a projection, an area load."""
    made = []
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
        made.append(area)
    return made


def wl_scheduler(run):
    """The cognitive-task SCHEDULER on its own — the `scheduler` area."""
    agent = _sched_agent()
    _sched_scenario(agent, n_areas=3, n_tasks=3)
    for _ in range(4):
        agent.inner.run_cognitive_tasks(1)
        run(agent.inner)
    return dump(agent.inner)


def wl_quiet_areas(run):
    """The SAME scheduler scenario, with FOUR MORE real seeds loaded whose
    rules live in OTHER areas (`executive`, `motor`, `learning`, `spatial`) and
    which have NO material to match. Those areas are permanently QUIET — the
    honest test of 'an area with no dirty input does no work'."""
    agent = _sched_agent(("information_commitment", "spatial_belief_core"))
    _sched_scenario(agent, n_areas=3, n_tasks=3)
    for _ in range(4):
        agent.inner.run_cognitive_tasks(1)
        run(agent.inner)
    return dump(agent.inner)


def wl_conversation(run):
    """A NON-VISION domain: the booted conversational agent ingesting text.
    Its rules are almost all in the DEFAULT (`global`) area, so this is the
    one-area degenerate case — included precisely because the reduction must
    hold there too."""
    from substrate.world_adapter import WorldAdapter
    agent = WorldAdapter()
    for text in ("hello there", "the moon is cold",
                 "i think it is bright", "tell me more"):
        agent.add_inbound(text)
        run(agent.inner)
    return dump(agent.inner)


WORKLOADS = {
    "vision_carve": wl_vision_carve,
    "scheduler": wl_scheduler,
    "quiet_areas": wl_quiet_areas,
    "conversation": wl_conversation,
}


# ------------------------------------------- synthetic N-area cost workload ----
def synth_areas(n_areas, dirty_areas, chain=6):
    """N independent areas, each a CHAIN of rules over its OWN node type, so an
    area's work is real and an area's quietness is real. Rules are installed by
    `add_rule` with an explicit `"area"` — the same manifest key every seed
    uses. Only `dirty_areas` of them are given material."""
    from substrate.world_adapter import WorldAdapter
    agent = WorldAdapter(seeds=())
    inner = agent.inner
    for a in range(n_areas):
        for k in range(chain):
            inner.add_rule({
                "name": f"syn_a{a}_r{k}",
                "area": f"syn{a}",
                "order": 1,
                "match": [["src", f"e_a{a}_{k}", "tgt"]],
                "effects": [["add_edge", "src", f"e_a{a}_{k + 1}", "tgt", {}],
                            ["set_attr_if_different", "tgt", f"v{k}", float(k)]],
            })
    for a in range(dirty_areas):
        s = agent.s.add_node(f"SynSrc{a}", {"i": float(a)})
        t = agent.s.add_node(f"SynTgt{a}", {"i": float(a)})
        inner.add_edge_unchecked(s, f"e_a{a}_0", t)
    return agent


# ----------------------------------------------------------------- helpers -----
def residual_curve(report):
    return [r["residual"] for r in report["rounds"]]


def carried_total(driver):
    """Total work an area's budget did not reach and therefore CARRIED, summed
    over every round of every settlement call the driver made."""
    return sum(row["carried"] for rep in driver.reports
               for rd in rep["rounds"] for row in rd["rows"])


def median_of(fn, reps=5):
    return statistics.median(fn() for _ in range(reps))


# -------------------------------------------------------------------- main -----
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    os.makedirs(OUTDIR, exist_ok=True)
    from domains.engine_provenance import provenance_stamp
    prov = provenance_stamp(strict=False)
    rep = {"block": SEED, "engine_source_match": prov.get("source_match"),
           "engine_short": prov.get("short")}

    # --- C1c: the DEFAULT path, dumped for the base-vs-new comparison -------
    if "--default-dump" in argv:
        out = {}
        for name, wl in WORKLOADS.items():
            d = Driver("global")
            t0 = time.perf_counter()
            text = wl(d)
            out[name] = {"dump_len": len(text), "digest": _digest(text),
                         "seconds": time.perf_counter() - t0}
            print(f"[C1c] {name}: {out[name]['digest']} "
                  f"(len {out[name]['dump_len']})", flush=True)
        path = os.path.join(OUTDIR, "default_path_dump.json")
        json.dump({"engine_short": prov.get("short"), "workloads": out},
                  open(path, "w"), indent=2)
        print("wrote", path)
        return 0

    # --- C2: THE REDUCTION -------------------------------------------------
    # Measured for BOTH schedules: the ASYNC form (each area reads its dirty set
    # on its own clock) and the BARRIER form (all areas snapshot at round start).
    print("=== C2 THE REDUCTION: settle(unbounded) vs the global fixpoint ===",
          flush=True)
    reduction = {}
    for name, wl in WORKLOADS.items():
        row = {}
        try:
            g = Driver("global")
            base = wl(g)
            row["base_digest"] = _digest(base)
            row["global_seconds"] = sum(g.seconds)
            for tag, snap in (("async", False), ("barrier", True)):
                u = Driver("settle", 0, False, snap)
                got = wl(u)
                rounds = [r["n_rounds"] for r in u.reports]
                areas = u.reports[-1]["areas"] if u.reports else []
                row[tag] = {
                    "identical": base == got, "digest": _digest(got),
                    "settle_steps": sum(r["steps"] for r in u.reports),
                    "n_areas": len(areas), "areas": areas,
                    "rounds_per_call": rounds,
                    "max_rounds_in_a_call": max(rounds) if rounds else 0,
                    "seconds": sum(u.seconds),
                }
        except Exception as exc:      # a workload that cannot run is reported
            row["error"] = f"{type(exc).__name__}: {exc}"
        reduction[name] = row
        print(f"[C2] {name}: {json.dumps(row)}", flush=True)
    rep["C2_reduction"] = reduction

    # THE SCOPE PROBE the reduction needs: areas whose rules are INTERLEAVED in
    # the rule list, so area-major order is NOT the committed pass order.
    rep["C2d_interleaved_areas"] = _interleaved_probe()
    print(f"[C2d] {json.dumps(rep['C2d_interleaved_areas'])}", flush=True)

    # --- C3: RESIDUAL IS CARRIED ------------------------------------------
    print("=== C3 RESIDUAL CARRIED: finite budget -> same endpoint ===",
          flush=True)
    carried = {}
    for name, wl in WORKLOADS.items():
        r = reduction.get(name, {})
        snap = _winning_schedule(r)
        if snap is None:
            continue
        g = Driver("global")
        base = wl(g)
        rows = {"schedule": "barrier" if snap else "async"}
        for b in (1, 2, 4, 8):
            d = Driver("settle", b, False, snap)
            got = wl(d)
            rows[b] = {
                "identical_endpoint": base == got,
                "rounds_per_call": [x["n_rounds"] for x in d.reports],
                "total_rounds": sum(x["n_rounds"] for x in d.reports),
                "carried_total": carried_total(d),
                "residual_curve_last_call": (
                    residual_curve(d.reports[-1]) if d.reports else []),
                "terminal_residual": (
                    d.reports[-1]["rounds"][-1]["residual"]
                    if d.reports and d.reports[-1]["rounds"] else None),
            }
        u = Driver("settle", 0, False, snap)
        wl(u)
        rows["unbounded"] = {
            "total_rounds": sum(x["n_rounds"] for x in u.reports),
            "carried_total": carried_total(u)}
        carried[name] = rows
        print(f"[C3] {name}: " + json.dumps(
            {k: (v if k in ("unbounded", "schedule") else
                 {kk: v[kk] for kk in ("identical_endpoint", "total_rounds",
                                       "carried_total", "terminal_residual")})
             for k, v in rows.items()}), flush=True)
    rep["C3_carried"] = carried

    # --- C3d: "you never get to 0 unless you stop operating" ---------------
    print("=== C3d residual under CONTINUING input, then STOPPED input ===",
          flush=True)
    rep["C3d_flow"] = _flowing_residual()
    print(f"[C3d] {json.dumps(rep['C3d_flow'])}", flush=True)

    # --- F: THE DROP FALSIFIER ---------------------------------------------
    print("=== F DROP-the-residual must DIVERGE ===", flush=True)
    drop = {}
    for name, wl in WORKLOADS.items():
        snap = _winning_schedule(reduction.get(name, {}))
        if snap is None:
            continue
        g = Driver("global")
        base = wl(g)
        rows = {"schedule": "barrier" if snap else "async"}
        for b in (1, 2, 4, 8):
            c = Driver("settle", b, False, snap)
            carried_dump = wl(c)
            dd = Driver("settle", b, True, snap)
            drop_dump = wl(dd)
            rows[b] = {
                "carried_equals_global": carried_dump == base,
                "drop_equals_global": drop_dump == base,
                "drop_equals_carried": drop_dump == carried_dump,
                "drop_digest": _digest(drop_dump),
                "carried_digest": _digest(carried_dump),
                "drop_steps": sum(r["steps"] for r in dd.reports),
                "carried_steps": sum(r["steps"] for r in c.reports),
                "dump_len_drop": len(drop_dump),
                "dump_len_carried": len(carried_dump),
            }
        drop[name] = rows
        print(f"[F] {name}: {json.dumps(rows)}", flush=True)
    rep["F_drop_falsifier"] = drop

    # --- C4: COST ∝ SURPRISE AT THE AREA GRAIN -----------------------------
    print("=== C4 cost tracks DIRTY AREAS ===", flush=True)
    rep["C4_cost"] = _cost_vs_dirty_areas()
    print(f"[C4] {json.dumps(rep['C4_cost'])}", flush=True)

    print("=== C4d THE VISION PATH's own areas (carve/motion/salience) ===",
          flush=True)
    rep["C4d_vision_areas"] = _vision_area_split()
    print(f"[C4d] {json.dumps(rep['C4d_vision_areas'])}", flush=True)

    path = os.path.join(OUTDIR, "per_area_settlement.json")
    json.dump(rep, open(path, "w"), indent=2)
    print("wrote", path)
    _plot(rep)
    return 0


def _plot(rep):
    """The three curves. Guarded — a missing matplotlib is never fatal."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:                                  # noqa: BLE001
        print("plot skipped:", exc)
        return
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))

    flow = rep["C3d_flow"]
    y = flow["flowing_residual"] + flow["quiet_residual_head"]
    ax[0].plot(range(1, len(y) + 1), y, marker="o", ms=3)
    ax[0].axvline(len(flow["flowing_residual"]) + 0.5, color="crimson", ls="--")
    ax[0].set_title("residual per settlement round\n(input flows | input STOPS)")
    ax[0].set_xlabel("round"); ax[0].set_ylabel("carried residual")

    for name, rows in rep.get("C3_carried", {}).items():
        bs = [b for b in (1, 2, 4, 8) if str(b) in rows or b in rows]
        rounds = [(rows.get(b) or rows.get(str(b)))["total_rounds"] for b in bs]
        ax[1].plot(bs, rounds, marker="o", label=name)
    ax[1].set_xscale("log", base=2)
    ax[1].set_title("rounds to the SAME endpoint\nvs per-area budget")
    ax[1].set_xlabel("budget (progressing steps / area / round)")
    ax[1].set_ylabel("total rounds"); ax[1].legend(fontsize=7)

    sweep = rep["C4_cost"]["sweep"]
    ax[2].plot([r["dirty_areas"] for r in sweep],
               [r["seconds"] * 1e6 for r in sweep], marker="o")
    ax[2].set_title(f"cost vs DIRTY areas "
                    f"(total areas = {rep['C4_cost']['n_areas']})")
    ax[2].set_xlabel("dirty areas"); ax[2].set_ylabel("microseconds / settle")
    fig.tight_layout()
    out = os.path.join(OUTDIR, "per_area_settlement.png")
    fig.savefig(out, dpi=120)
    print("wrote", out)


def _digest(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _winning_schedule(row):
    """Which settlement SCHEDULE reproduced the fixpoint on this workload:
    the ASYNC (no-barrier) form if it did, else the BARRIER form, else None.
    Reported, never assumed."""
    if row.get("async", {}).get("identical"):
        return False
    if row.get("barrier", {}).get("identical"):
        return True
    return None


def _interleaved_probe(chain=4):
    """THE SCOPE PROBE. In every committed seed set an area's rules are
    CONTIGUOUS in the rule list (a seed is loaded as a unit), so area-major
    order is the identity permutation of pass order. Here the areas are
    deliberately INTERLEAVED (a0, b0, a1, b1, ...), so settlement's area-major
    order is a genuine re-ordering of the committed pass. Whether the reduction
    survives that is the honest boundary of the claim."""
    from substrate.world_adapter import WorldAdapter

    def build():
        agent = WorldAdapter(seeds=())
        inner = agent.inner
        for k in range(chain):
            for a in ("x", "y"):                       # INTERLEAVED by design
                inner.add_rule({
                    "name": f"ilv_{a}{k}", "area": f"ilv_{a}", "order": 1,
                    "match": [["s", f"ile_{a}_{k}", "t"]],
                    "effects": [
                        ["add_edge", "s", f"ile_{a}_{k + 1}", "t", {}],
                        ["add_node", "n", f"IlvMint_{a}_{k}", {"k": float(k)}],
                    ],
                })
        for a in ("x", "y"):
            s = agent.s.add_node(f"IlvSrc{a}", {})
            t = agent.s.add_node(f"IlvTgt{a}", {})
            inner.add_edge_unchecked(s, f"ile_{a}_0", t)
        return agent

    a = build(); a.inner.run_rules(); base = dump(a.inner)
    out = {"chain": chain, "base_digest": _digest(base)}
    for tag, snap in (("async", False), ("barrier", True)):
        b = build()
        rep = b.inner.run_rules_settle(0, MAX_ROUNDS, False, snap)
        got = dump(b.inner)
        out[tag] = {"identical": got == base, "digest": _digest(got),
                    "steps": rep["steps"], "n_rounds": rep["n_rounds"],
                    "areas": rep["areas"]}
    return out


def _flowing_residual(n_flow=30, n_quiet=60):
    """THE AXIOM, MEASURED. While the world keeps feeding the graph, the
    account never closes: settle ONE round per world tick under a finite
    budget and watch the residual. When the input stops, it must drain to 0."""
    agent = _sched_agent()
    inner = agent.inner
    areas = _sched_scenario(agent, n_areas=2, n_tasks=2)
    flowing, quiet = [], []
    ep = 3
    for _ in range(n_flow):
        # The world keeps arriving: a fresh task + a fresh residual epoch.
        for a in areas:
            t = agent.s.add_node("CognitiveTask", {
                "status": "pending", "kind": "abs_diff_energy",
                "payload": [1.0, 2.0], "input_epoch": ep, "salience": 0.5,
                "logical_time": ep, "area": "test", "order": 2, "effort": 1})
            inner.add_edge_unchecked(a, "has_task", t)
        ep += 1
        r = inner.run_rules_settle(2, 1, False, False)   # EXACTLY ONE round
        flowing.append(r["rounds"][-1]["residual"] if r["rounds"] else 0)
    for _ in range(n_quiet):                      # the input STOPS
        r = inner.run_rules_settle(2, 1, False, False)
        quiet.append(r["rounds"][-1]["residual"] if r["rounds"] else 0)
    nz = sum(1 for x in flowing if x > 0)
    drain = next((i + 1 for i, x in enumerate(quiet) if x == 0), None)
    return {"flowing_rounds": n_flow, "flowing_residual": flowing,
            "flowing_nonzero_fraction": nz / max(1, n_flow),
            "quiet_residual_head": quiet[:20],
            "rounds_to_zero_after_input_stops": drain,
            "quiet_terminal_residual": quiet[-1] if quiet else None}


def _settled_synth(n_areas):
    """N areas with NO material, SETTLED. A freshly installed rule is dirty by
    construction (the engine must try it once), so measuring straight after
    `add_rule` would time 'try all 32 areas once' and say nothing about
    surprise. Settling first is the honest starting state — the same discipline
    block 185000 used (adapt the sheet to its fixed point, THEN perturb)."""
    agent = synth_areas(n_areas, 0)
    agent.inner.run_rules_settle(0, MAX_ROUNDS, False, False)
    return agent


def _perturb(agent, d):
    """Give material to exactly `d` areas — the SURPRISE. Cross-area waking is
    the engine's committed `mark_edge_type_dirty` / `dirty_by_writeset`, i.e.
    event-causal, never a barrier."""
    for a in range(d):
        s = agent.s.add_node(f"SynSrc{a}", {"i": float(a)})
        t = agent.s.add_node(f"SynTgt{a}", {"i": float(a)})
        agent.inner.add_edge_unchecked(s, f"e_a{a}_0", t)


def _vision_area_split(n_el=15, n_az=20, hold=8):
    """C4d — THE NAMED BOTTLENECK, at the AREA grain.

    The committed vision seeds put EVERY retinal rule in ONE `retina` area, so
    out of the box the per-area lever has nothing to pull on inside vision.
    Here the four retinal mint rules are RELABELLED into four areas via
    `set_rule_area` — scheduling metadata only, and no committed seed file is
    edited. The carve / motion / salience settle ops then become areas that are
    QUIET on an ordinary photon tick and dirty only when their settle task is
    minted. Both arms are reported: as-shipped and split.
    """
    from domains.photon_eye import GraphEye
    from domains import doom_photon_world as dpw
    from scripts import doom_carve_scale_measure as M
    from scripts import eye_accel_measure as EA

    lumas = _fixture_lumas()
    out = {}
    for tag, split in (("as_shipped", False), ("split_areas", True)):
        eye = GraphEye(
            n_az=n_az, n_el=n_el, adapt_rate=M.ADAPT_RATE,
            context={"retina_2d": True, "synchronous": True,
                     "worker_capacity": 1, "onset_threshold_db": M.ONSET_DB,
                     "onset_refractory_epochs": 0.0, "visual_carve": True,
                     "carve_min_coherence": M.CARVE_MIN_COH,
                     "carve_min_events": M.CARVE_MIN_EVENTS,
                     "visual_motion": True, "visual_salience": True,
                     "retina_accel": False}).build()
        inner = eye.substrate._inner
        if split:
            for rule, area in (("retinal_mint_onset_2d", "v1_onset"),
                               ("retinal_mint_carve_2d", "mt_carve"),
                               ("retinal_mint_motion_2d", "mt_motion"),
                               ("retinal_mint_salience_2d", "lip_salience")):
                inner.set_rule_area(rule, area)
        f0 = EA._area_mean(lumas[0], n_el, n_az)
        # Ordinary photon ticks: NO settle task is minted, so the carve /
        # motion / salience areas hold nothing to do.
        quiet_rows, tick_seconds = [], []
        for _ in range(hold):
            eye.submit_photons_2d(
                dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
            inner.run_cognitive_tasks(1)
            t0 = time.perf_counter()
            r = inner.run_rules_settle(0, MAX_ROUNDS, False, False)
            tick_seconds.append(time.perf_counter() - t0)
            quiet_rows.append([
                {"area": row["area"], "dirty": row["dirty"],
                 "attempted": row["attempted"], "steps": row["steps"]}
                for rd in r["rounds"] for row in rd["rows"]])
            eye.prune_settled_tasks()
        since = eye._epoch + 1
        # NOW the settle ops fire: their areas wake.
        eye.settle_carve_2d(since_epoch=since)
        eye.settle_motion_2d(since_epoch=since)
        eye.settle_salience_2d(since_epoch=since)
        inner.run_cognitive_tasks(1)
        t0 = time.perf_counter()
        r = inner.run_rules_settle(0, MAX_ROUNDS, False, False)
        settle_seconds = time.perf_counter() - t0
        out[tag] = {
            "areas": r["areas"],
            "plain_photon_tick_rows": quiet_rows[-1],
            "areas_working_on_a_plain_photon_tick": sorted(
                {r_["area"] for r_ in quiet_rows[-1]}),
            "areas_working_on_the_settle_tick": sorted(
                {row["area"] for rd in r["rounds"] for row in rd["rows"]}),
            "median_photon_tick_seconds": statistics.median(tick_seconds),
            "settle_tick_seconds": settle_seconds,
            "settle_tick_rows": [
                {"area": row["area"], "dirty": row["dirty"],
                 "attempted": row["attempted"], "steps": row["steps"]}
                for rd in r["rounds"] for row in rd["rows"]],
        }
        eye.stop()
    return out


def _cost_vs_dirty_areas(n_areas=32, reps=9):
    """At a FIXED total area count, sweep how many areas hold dirty material —
    measured from a SETTLED state, so the cost is the cost of SURPRISE."""
    out = {"n_areas": n_areas, "sweep": [], "reps": reps}
    for d in (0, 1, 2, 4, 8, 16, 32):
        ts, steps, dirty_seen, attempts, worked = [], None, None, None, None
        for _ in range(reps):
            agent = _settled_synth(n_areas)
            _perturb(agent, d)
            t0 = time.perf_counter()
            r = agent.inner.run_rules_settle(0, MAX_ROUNDS, False, False)
            ts.append(time.perf_counter() - t0)
            steps = r["steps"]
            dirty_seen = max((rd["dirty_areas"] for rd in r["rounds"]),
                             default=0)
            attempts = sum(row["attempted"] for rd in r["rounds"]
                           for row in rd["rows"])
            worked = sorted({row["area"] for rd in r["rounds"]
                             for row in rd["rows"]})
        out["sweep"].append({"dirty_areas": d, "seconds": statistics.median(ts),
                             "steps": steps, "max_dirty_areas_seen": dirty_seen,
                             "rule_attempts": attempts,
                             "areas_that_did_any_work": len(worked)})
    xs = [row["dirty_areas"] for row in out["sweep"]]
    ys = [row["seconds"] for row in out["sweep"]]
    slope, icept = np.polyfit(xs, ys, 1)
    pred = [slope * x + icept for x in xs]
    ybar = sum(ys) / len(ys)
    ss_res = sum((y - p) ** 2 for y, p in zip(ys, pred))
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    out["affine_fit"] = {"slope": slope, "intercept": icept,
                         "r2": 1.0 - ss_res / ss_tot if ss_tot else None}
    one = next(r["seconds"] for r in out["sweep"] if r["dirty_areas"] == 1)
    allv = next(r["seconds"] for r in out["sweep"] if r["dirty_areas"] == n_areas)
    out["cost_ratio_d1_over_dAll"] = one / allv

    # C4c — THE HONEST ALL-DIRTY CASE: no free lunch.
    gt, st = [], []
    for _ in range(reps):
        a = _settled_synth(n_areas); _perturb(a, n_areas)
        t0 = time.perf_counter(); a.inner.run_rules(); gt.append(time.perf_counter() - t0)
        a = _settled_synth(n_areas); _perturb(a, n_areas)
        t0 = time.perf_counter(); a.inner.run_rules_settle(0, MAX_ROUNDS, False, False)
        st.append(time.perf_counter() - t0)
    out["all_dirty"] = {"global_seconds": statistics.median(gt),
                        "settle_seconds": statistics.median(st),
                        "ratio_settle_over_global":
                            statistics.median(st) / statistics.median(gt)}
    return out


if __name__ == "__main__":
    sys.exit(main())
