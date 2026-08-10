#!/usr/bin/env python3
"""THE EMPTY-MATCH-SET PROOF — the measurement harness (block 189000).

Prereg: `EMPTY_MATCH_PROOF_PREREG.md`, committed ALONE before any number here.

ONE mechanism, DEFAULT OFF, a DROPPABLE BYTE-IDENTICAL MIRROR:

  * `empty_match_proof` (engine flag) — do not enumerate a rule whose match set
    is PROVABLY empty under the current graph (some match edge's edge type has
    ZERO live edges). Byte-identity IS claimed and IS the gate.
  * `empty_match_proof_unsound` (engine flag) — THE FALSIFIER. Treats a
    SINGLETON edge type as absent. MUST break byte-identity.

Mechanical I/O + measurement only. Every decision lives in the Rust engine or
in graph data.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts import per_sensor_epoch_measure as P  # noqa: E402

SEED = 189000
OUTDIR = os.path.join(ROOT, "results", "empty_match_proof")
MAX_ROUNDS = P.MAX_ROUNDS

#: The three rules 188000 named — woken every tick, O(cells) each, progressed 0.
THE_THREE = ("retinal_mint_onset_2d",
             "photon_column_synthesizes_retinal_percept",
             "photon_apply_receptor_transduction")

#: (name, empty_match_proof, empty_match_proof_unsound)
ARMS = (("off", False, False),
        ("proof", True, False),
        ("unsound", True, True))


def _set_proof(inner, on, unsound=False):
    fn = getattr(inner, "set_empty_match_proof", None)
    if fn is None:
        if on:
            raise RuntimeError("this engine has no set_empty_match_proof")
        return False
    fn(on)
    if unsound:
        inner.set_empty_match_proof_unsound(True)
    return True


def build_eye(n_el=15, n_az=20, *, proof=False, unsound=False, accel=False,
              split=True, precise=False):
    eye, inner = P.build_eye(n_el=n_el, n_az=n_az, accel=accel, split=split)
    _set_proof(inner, proof, unsound)
    if precise:
        inner.set_precise_dirty(True)
    return eye, inner


# ------------------------------------------------------- §1 THE DIAGNOSIS -----
def diagnosis(n_el=120, n_az=160, hold=8):
    """WHICH rules are provably empty, on which path, and WHY — read off the
    live graph via the engine's own `provably_empty_rules`. This is the
    prereg's §1 table, re-derived by the mechanism itself."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = P._fixture_lumas()
    out = {}
    for tag, accel, dims in (("accel_160x120", True, (n_el, n_az)),
                             ("graph_20x15", False, (15, 20))):
        el, az = dims
        f0 = DI._grid(lumas[0], el, az)
        eye, inner = build_eye(el, az, accel=accel, precise=True, split=False)
        for _ in range(hold):
            eye.submit_photons_2d(
                dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
            inner.run_rules_settle(0, MAX_ROUNDS, False, False)
        empties = inner.provably_empty_rules()
        by_name = {r[0]: {"area": r[1], "witness_edge_type": r[2]} for r in empties}
        out[tag] = {
            "provably_empty_rules": [
                {"rule": r[0], "area": r[1], "zero_population_edge_type": r[2]}
                for r in empties],
            "of_the_three": {r: by_name.get(r) for r in THE_THREE},
        }
        print(f"[diagnosis {tag}] {len(empties)} provably-empty active rules")
        for r in THE_THREE:
            w = by_name.get(r)
            print(f"    {r:<45} {'EMPTY via ' + w['witness_edge_type'] if w else 'NOT provably empty'}")
        eye.stop()
    return out


# --------------------------------------------------- §2 the WORKLOAD set ------
def _wl_vision_carve(proof, unsound=False, n_el=15, n_az=20, hold=8, motion=6):
    """The REAL 2-D retina on the GRAPH path — the `run_rules` oracle."""
    from domains import doom_photon_world as dpw
    from scripts import eye_accel_measure as EA
    lumas = P._fixture_lumas()
    eye, inner = build_eye(n_el, n_az, proof=proof, unsound=unsound, split=False)
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
    out = P.dump(inner)
    eye.stop()
    return out


def _wl_scheduler(proof, unsound=False, extra=(), n_areas=3, n_tasks=3):
    agent = P._sched_agent(extra)
    _set_proof(agent.inner, proof, unsound)
    P._sched_scenario(agent, n_areas=n_areas, n_tasks=n_tasks)
    for _ in range(4):
        agent.inner.run_cognitive_tasks(1)
        agent.inner.run_rules()
    return P.dump(agent.inner)


def _wl_quiet_areas(proof, unsound=False):
    return _wl_scheduler(proof, unsound,
                         extra=("information_commitment", "spatial_belief_core"))


def _wl_scheduler_wide(proof, unsound=False):
    """A GENUINELY DISTINCT non-vision workload — 188000's residual 8 recorded
    that `scheduler` and `quiet_areas` produce the same dump digest, so its
    identity claim was really 4-distinct. This one is 5 areas x 6 tasks, so the
    scheduler rules have large, NON-empty match sets."""
    return _wl_scheduler(proof, unsound, n_areas=5, n_tasks=6)


def _wl_conversation(proof, unsound=False):
    from substrate.world_adapter import WorldAdapter
    agent = WorldAdapter()
    _set_proof(agent.inner, proof, unsound)
    for text in ("hello there", "the moon is cold",
                 "i think it is bright", "tell me more"):
        agent.add_inbound(text)
        agent.inner.run_rules()
    return P.dump(agent.inner)


def _wl_doom_accel(proof, unsound=False, n_el=120, n_az=160, hold=8, motion=6):
    """The SHIPPED Doom configuration: 160x120, `retina_accel` ON."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = P._fixture_lumas()
    eye, inner = build_eye(n_el, n_az, proof=proof, unsound=unsound,
                           accel=True, split=False)
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
    out = P.dump(inner)
    eye.stop()
    return out


WORKLOADS = {
    "vision_carve": _wl_vision_carve,
    "scheduler": _wl_scheduler,
    "quiet_areas": _wl_quiet_areas,
    "scheduler_wide": _wl_scheduler_wide,
    "conversation": _wl_conversation,
    "doom_accel_160x120": _wl_doom_accel,
}
NON_VISION = ("scheduler", "quiet_areas", "scheduler_wide", "conversation")


def identity(arms=("off", "proof", "unsound")):
    """C1 / C2a / F1 — the whole-graph float-exact dumps, per arm."""
    out = {}
    for name, fn in WORKLOADS.items():
        row = {}
        for arm in arms:
            _, proof, unsound = next(a for a in ARMS if a[0] == arm)
            row[arm] = P.digest(fn(proof, unsound))
        row["proof_identical_to_off"] = (row.get("proof") == row.get("off"))
        row["unsound_diverges"] = (row.get("unsound") != row.get("off"))
        out[name] = row
        print(f"[identity {name:<20}] off={row.get('off')} proof={row.get('proof')} "
              f"unsound={row.get('unsound')}  "
              f"{'IDENTICAL' if row['proof_identical_to_off'] else '*** DIVERGES ***'}"
              f" | falsifier {'BITES' if row['unsound_diverges'] else '*** VACUOUS ***'}")
    return out


# ------------------------------------------- §3 OBSERVABLE identity -----------
def landed_carve(proof=False, unsound=False):
    """C2b/C2c — the LANDED Doom carve at 160x120 (4 / 0.1215 / 0.9784 / 0),
    through `dirty_index_measure`'s committed Poisson protocol. Structure taken
    verbatim from 188000's `landed_carve` so the two are directly comparable;
    the only change is WHICH flag is set on the eye's engine."""
    from scripts import dirty_index_measure as DI
    from scripts import eye_accel_measure as EA
    lumas_full, labels_full, names = EA._load_fixture()
    lumas = list(lumas_full)
    lg160 = [EA._downsample_labels(labels_full[i], 120, 160)
             for i in range(1, labels_full.shape[0])]
    nm160 = [names[i] for i in range(1, labels_full.shape[0])]
    orig_build, orig_rod = DI.build_eye, DI.rod_state
    seen = {}

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
        eye = GraphEye(n_az=n_az, n_el=n_el, adapt_rate=M.ADAPT_RATE,
                       context=ctx).build()
        _set_proof(eye.substrate._inner, proof, unsound)
        seen["inner"] = eye.substrate._inner
        return eye

    DI.build_eye = patched
    DI.rod_state = lambda eye: P._rod_state(eye)
    try:
        r = DI.poisson_carve_run(lumas, lg160, nm160, 120, 160, arm="accel")
    finally:
        DI.build_eye, DI.rod_state = orig_build, orig_rod
    inner = seen.get("inner")
    out = {"n_polygons": len(r["polygons"]),
           "union_iou": r.get("union_iou"),
           "carve_precision": r.get("carve_precision"),
           "false_polygons": r.get("false_polygons"),
           "onset_digest": P.digest(P.canon(r["onset_stream"])),
           "n_onsets": len(r["onset_stream"]),
           "rod_state_digest": P.digest(P.canon(r["rod"])),
           "empty_match_skips": (inner.empty_match_skips()
                                 if inner is not None
                                 and hasattr(inner, "empty_match_skips") else [])}
    print(f"[carve proof={proof} unsound={unsound}] polys={out['n_polygons']} "
          f"iou={out['union_iou']} prec={out['carve_precision']} "
          f"false={out['false_polygons']} onsets={out['n_onsets']} "
          f"digest={out['onset_digest']} rod={out['rod_state_digest']}")
    return out


def graph_path_onsets(proof=False, unsound=False, n_el=15, n_az=20,
                      hold=8, motion=6):
    """C2d / F1 — the GRAPH-path onset stream. The falsifier's target: on this
    path `retinal_mint_onset_2d` binds the retina's SINGLE `has_onset_params_2d`
    edge, so the unsound (<=1) predicate silently kills every onset."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    from scripts import eye_accel_measure as EA
    lumas = P._fixture_lumas()
    eye, inner = build_eye(n_el, n_az, proof=proof, unsound=unsound, split=False)
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
    out = {"onsets": len(stream), "digest": P.digest(P.canon(stream)),
           "rod_digest": P.digest(P.canon(P._rod_state(eye))),
           "skips": inner.empty_match_skips()}
    eye.stop()
    print(f"[graph-onsets proof={proof} unsound={unsound}] {out['onsets']} onsets, "
          f"digest {out['digest']}, skips {out['skips']}")
    return out


# ----------------------------------------------- §4 COST — the headline -------
def accel_cost(n_el=120, n_az=160, hold=8, probe=4, trials=5):
    """H1/H2 — the shipped accel path's settlement cost and per-rule breakdown,
    proof OFF vs ON. Median of `trials` builds x `probe` ticks."""
    from domains import doom_photon_world as dpw
    from scripts import dirty_index_measure as DI
    lumas = P._fixture_lumas()
    f0 = DI._grid(lumas[0], n_el, n_az)
    out = {}
    for arm, proof, unsound in (("off", False, False), ("proof", True, False)):
        settles, rules_ms, breakdowns, skips = [], [], [], []
        for _ in range(trials):
            eye, inner = build_eye(n_el, n_az, proof=proof, unsound=unsound,
                                   accel=True, precise=True)
            for _ in range(hold):
                eye.submit_photons_2d(
                    dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
                inner.run_rules_settle(0, MAX_ROUNDS, False, False)
            inner.reset_rule_costs()
            if hasattr(inner, "reset_empty_match_skips"):
                inner.reset_empty_match_skips()
            t = 0.0
            for _ in range(probe):
                eye.submit_photons_2d(
                    dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
                t0 = time.perf_counter()
                inner.run_rules_settle(0, MAX_ROUNDS, False, False)
                t += time.perf_counter() - t0
            rows = [r for r in inner.rule_costs() if r[1] > 0]
            rows.sort(key=lambda r: -r[1])
            total = sum(r[1] for r in rows)
            settles.append(t / probe * 1e3)
            rules_ms.append(total / probe / 1e3)
            breakdowns.append([
                {"rule": r[0], "micros": r[1], "processed": r[2],
                 "progressed": r[3], "frac_of_rule_time": r[1] / max(1, total)}
                for r in rows[:6]])
            skips.append(inner.empty_match_skips()
                         if hasattr(inner, "empty_match_skips") else [])
            eye.stop()
        mid = sorted(range(trials), key=lambda i: settles[i])[trials // 2]
        share3 = sum(r["frac_of_rule_time"] for r in breakdowns[mid]
                     if r["rule"] in THE_THREE)
        # The ABSOLUTE cost of the three, which is the figure that carries
        # meaning: the SHARE is a fraction of a denominator that itself falls
        # ~1000x, so it is not a fact about the eye (see RESULTS §3, H2).
        micros3 = sum(r["micros"] for r in breakdowns[mid]
                      if r["rule"] in THE_THREE)
        out[arm] = {
            "settle_ms_per_tick_median": statistics.median(settles),
            "settle_ms_per_tick_all": settles,
            "settle_ms_spread": (min(settles), max(settles)),
            "rule_ms_per_tick_median": statistics.median(rules_ms),
            "top_rules": breakdowns[mid],
            "share_of_rule_time_of_THE_THREE": share3,
            "micros_of_THE_THREE_over_probe": micros3,
            "micros_of_THE_THREE_per_tick": micros3 / probe,
            "empty_match_skips": skips[mid],
        }
        print(f"[accel-cost {arm:<6}] settle {out[arm]['settle_ms_per_tick_median']:.3f}"
              f" ms/tick (spread {min(settles):.3f}-{max(settles):.3f}), rules "
              f"{out[arm]['rule_ms_per_tick_median']:.3f} ms/tick, "
              f"THE THREE = {share3*100:.1f}% of rule time")
        for r in out[arm]["top_rules"][:4]:
            print(f"    {r['frac_of_rule_time']*100:5.1f}%  {r['rule']} "
                  f"(processed {r['processed']}, progressed {r['progressed']})")
    o, n = out["off"]["settle_ms_per_tick_median"], out["proof"]["settle_ms_per_tick_median"]
    out["ratio_proof_over_off"] = n / o
    print(f"[accel-cost] H1 ratio = {out['ratio_proof_over_off']:.3f}")
    return out


def graph_path_cost(n_el=15, n_az=20, hold=10, probe=8, trials=5):
    """H3 + the no-free-lunch companion on the eye's own GRAPH path, where
    `has_task` is POPULATED and only the 2-D-sheet rule proves empty."""
    from domains import doom_photon_world as dpw
    from scripts import eye_accel_measure as EA
    lumas = P._fixture_lumas()
    f0 = EA._area_mean(lumas[0], n_el, n_az)
    out = {}
    for arm, proof in (("off", False), ("proof", True)):
        settles, skips, empties = [], [], []
        for _ in range(trials):
            eye, inner = build_eye(n_el, n_az, proof=proof, precise=True)
            for _ in range(hold):
                eye.submit_photons_2d(
                    dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
                inner.run_cognitive_tasks(1)
                inner.run_rules_settle(0, MAX_ROUNDS, False, False)
            if hasattr(inner, "reset_empty_match_skips"):
                inner.reset_empty_match_skips()
            t = 0.0
            for _ in range(probe):
                eye.submit_photons_2d(
                    dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
                inner.run_cognitive_tasks(1)
                t0 = time.perf_counter()
                inner.run_rules_settle(0, MAX_ROUNDS, False, False)
                t += time.perf_counter() - t0
            settles.append(t / probe * 1e3)
            skips.append(inner.empty_match_skips()
                         if hasattr(inner, "empty_match_skips") else [])
            empties.append([r[0] for r in inner.provably_empty_rules()])
            eye.stop()
        out[arm] = {"settle_ms_per_tick_median": statistics.median(settles),
                    "settle_ms_per_tick_all": settles,
                    "empty_match_skips": skips[-1],
                    "provably_empty_rules": empties[-1]}
        print(f"[graph-cost {arm:<6}] settle {out[arm]['settle_ms_per_tick_median']:.3f} ms/tick"
              f"  skipped={[s[0] for s in skips[-1]]}")
    out["ratio_proof_over_off"] = (out["proof"]["settle_ms_per_tick_median"]
                                   / out["off"]["settle_ms_per_tick_median"])
    print(f"[graph-cost] ratio = {out['ratio_proof_over_off']:.3f}")
    return out


# ------------------------------------------------ §5 NO-FREE-LUNCH -----------
def _nfl_substrate(proof, n_rules=64, n_nodes=200):
    """A substrate in which NOT ONE rule is provably empty: every rule's single
    match edge type is heavily populated. The proof can skip NOTHING here and
    can only pay for its k index lookups. Built explicitly rather than borrowed
    from a seeded agent, because a small seeded agent has many genuinely-empty
    rules — which would turn F2 into a SECOND WIN instead of a control."""
    import substrate_rs as srs
    s = srs.Substrate()
    inner = s._inner
    _set_proof(inner, proof)
    hub = s.add_node("Hub", {"v": 0.0})
    for i in range(n_nodes):
        n = s.add_node("Cell", {"v": float(i), "w": 0.0})
        inner.add_edge_unchecked(hub, "link", n)
    for k in range(n_rules):
        inner.add_rule({
            "name": f"nfl_rule_{k}",
            "match": [["h", "link", "c"]],
            "where": {"type": "Gt",
                      "a": {"type": "Attr", "node": {"type": "Var", "name": "c"},
                            "key": "v"},
                      "b": {"type": "Lit", "value": float(k)}},
            "effects": [["set_attr", "c", "w", float(k)]],
        })
    return s, inner


def no_free_lunch(reps=7, n_rules=64, n_nodes=200, passes=3):
    """F2 — a workload where NO rule's match set is empty. The proof must cost
    the same or slightly more (it pays k index lookups per enumeration and
    skips nothing)."""
    out = {}
    for arm, proof in (("off", False), ("proof", True)):
        ts, empties = [], None
        for _ in range(reps):
            _s, inner = _nfl_substrate(proof, n_rules, n_nodes)
            empties = inner.provably_empty_rules()
            t0 = time.perf_counter()
            for _ in range(passes):
                inner.force_all_dirty()
                inner.run_rules(MAX_ROUNDS)
            ts.append((time.perf_counter() - t0) * 1e3)
        out[arm] = {"ms_median": statistics.median(ts), "ms_all": ts,
                    "provably_empty_rules": empties}
    out["nothing_is_empty"] = (out["proof"]["provably_empty_rules"] == [])
    out["ratio_proof_over_off"] = (out["proof"]["ms_median"] / out["off"]["ms_median"])
    print(f"[no-free-lunch] off {out['off']['ms_median']:.2f} ms, "
          f"proof {out['proof']['ms_median']:.2f} ms, "
          f"ratio {out['ratio_proof_over_off']:.3f}  "
          f"(nothing_is_empty={out['nothing_is_empty']})")
    return out


# ------------------------------------------------------------------ main ------
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    want = set(argv) or {"diagnosis", "identity", "carve", "graph_onsets",
                         "accel_cost", "graph_cost", "nfl"}
    os.makedirs(OUTDIR, exist_ok=True)
    res = {"seed": SEED}
    if "diagnosis" in want:
        res["diagnosis"] = diagnosis()
    if "identity" in want:
        res["identity"] = identity()
    if "carve" in want:
        res["carve"] = {"off": landed_carve(False), "proof": landed_carve(True),
                        "unsound": landed_carve(True, True)}
    if "graph_onsets" in want:
        res["graph_onsets"] = {"off": graph_path_onsets(False),
                               "proof": graph_path_onsets(True),
                               "unsound": graph_path_onsets(True, True)}
    if "accel_cost" in want:
        res["accel_cost"] = accel_cost()
    if "graph_cost" in want:
        res["graph_cost"] = graph_path_cost()
    if "nfl" in want:
        res["no_free_lunch"] = no_free_lunch()
    path = os.path.join(OUTDIR, "empty_match_proof.json")
    old = {}
    if os.path.exists(path):
        old = json.load(open(path))
    old.update(res)
    json.dump(old, open(path, "w"), indent=1, default=str)
    print("wrote", path)
    return res


if __name__ == "__main__":
    main()
