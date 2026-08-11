#!/usr/bin/env python3
"""A21 — POOL-COMPOSITION DRIFT, CLOSED WITHOUT TOUCHING `gr_condition_lapse`.
Measurement runner.

Builds the AR21c scenes live (no fixtures beyond the shipped seed boot),
reads `AgendaVerdict{kind:'impotent'}` back off the graph (`pool_stale`, the
new A21 axis, alongside the unmodified `stale`), and writes one JSON
artifact carrying every trace the results doc quotes.  Pure measurement: no
Python decision, mechanical boot -> mutate -> run_rules -> read-off, the
same shape `domains/arc_executor.py`'s own read-off helpers already are.

Run:
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \\
    PYTHONPATH=runners/dsl/python:. python3 scripts/arc6_condition_lapse_measure.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import arc_executor as axe  # noqa: E402
from domains import arc_goal_ingest as agi  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

AGID = "arc.remeasure.arc6.verdict.row_verdict_seed_only"
SECOND_AGID = "arc6.claim.tier0_hs1_0_of_10"
OUT = os.path.join(ROOT, "results", "arc6_condition_lapse.json")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _engine_sha() -> str:
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs",
                      "_native.abi3.so")
    return _sha256(so)


def _coherence_probe(s) -> bool:
    n = s.add_node("ExecEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    a = s.node(n)["attrs"]
    return a["lst"] != a["tup"]


def _boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals",
                "arc_executor"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    assert _coherence_probe(s), "VALUE LAYER ABSENT on this engine"
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    return s, ag


def _leave_pool(s, agid):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            orig = s.node(n)["attrs"].get("headroom_n")
            s.set_attr(n, "headroom_n", 0.0)
            return orig
    raise AssertionError("no such goal: " + agid)


def _restore_pool(s, agid, headroom_n):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            s.set_attr(n, "headroom_n", headroom_n)
            return
    raise AssertionError("no such goal: " + agid)


def ar21c_fires_on_drift_no_epoch_bump():
    """Direction (i).  A verdict mints for the 7-goal pool (pool_stale:0.0).
    A SECOND goal then leaves the pool -- composition drift -- with NO epoch
    bump anywhere in the scene.  The mechanism must, within the SAME
    run_rules() fixpoint: (a) mint a fresh verdict for the new 6-goal pool
    (IM5's own mint-once-by-signature behaviour, unmodified), and (b) flip
    the FIRST verdict's pool_stale to 1.0 -- the new fact this rung adds --
    while its epoch-keyed `stale` stays 0.0 (no measurement has happened)."""
    s, _ = _boot()
    s._inner.run_rules()
    _leave_pool(s, AGID)
    s._inner.run_rules()
    first = axe.agenda_verdicts(s, "impotent")
    assert len(first) == 1, first
    first_id = first[0]["_id"]
    assert first[0]["pool_stale"] == 0.0
    assert first[0]["stale"] == 0.0

    _leave_pool(s, SECOND_AGID)
    s._inner.run_rules()
    after = axe.agenda_verdicts(s, "impotent")
    by_id = {a["_id"]: a for a in after}
    return {
        "first_verdict_id": first_id,
        "after_all_ids": sorted(by_id),
        "first_verdict_after_drift": by_id[first_id],
        "pool_n_seen": sorted({a["pool_n"] for a in after}),
        "new_verdict_minted_for_6_pool": any(
            a["pool_n"] == 6 and a["pool_stale"] == 0.0 for a in after),
        "first_verdict_pool_stale_flipped": by_id[first_id]["pool_stale"] == 1.0,
        "first_verdict_epoch_stale_UNCHANGED": by_id[first_id]["stale"] == 0.0,
    }


def ar21c_does_not_fire_across_epoch_bump_without_drift():
    """Direction (ii).  Reproduce IM5's own 'bump arc_measure_epoch, pool
    composition UNCHANGED' scene and show pool_stale does NOT flip on
    either the superseded or the fresh verdict -- the mechanism must be
    provably orthogonal to the epoch-shaped one, not a duplicate trigger."""
    s, _ = _boot()
    s._inner.run_rules()
    _leave_pool(s, AGID)
    s._inner.run_rules()
    before = axe.agenda_verdicts(s, "impotent")
    assert len(before) == 1
    assert before[0]["stale"] == 0.0 and before[0]["pool_stale"] == 0.0

    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    after = axe.agenda_verdicts(s, "impotent")
    return {
        "before": before,
        "after_epoch_bump": after,
        "count_after": len(after),
        "all_pool_stale_zero": all(a["pool_stale"] == 0.0 for a in after),
        "epoch_stale_split": sorted({a["stale"] for a in after}),
    }


def ar21c_pool_hold_the_reverse_direction():
    """The gr_condition_lapse/gr_condition_hold precedent is two-sided by
    construction; so is this.  Drift the pool (pool_stale -> 1.0 on the
    first verdict), then restore the composition to EXACTLY what the first
    verdict recorded (re-add the second goal to the pool) and show
    ax_impotent_pool_hold restores pool_stale to 0.0."""
    s, _ = _boot()
    s._inner.run_rules()
    _leave_pool(s, AGID)
    s._inner.run_rules()
    first = axe.agenda_verdicts(s, "impotent")[0]
    first_id = first["_id"]

    second_orig_headroom = _leave_pool(s, SECOND_AGID)
    s._inner.run_rules()
    drifted = [a for a in axe.agenda_verdicts(s, "impotent") if a["_id"] == first_id][0]

    _restore_pool(s, SECOND_AGID, second_orig_headroom)
    s._inner.run_rules()
    restored = [a for a in axe.agenda_verdicts(s, "impotent") if a["_id"] == first_id][0]

    return {
        "first_pool_stale": first["pool_stale"],
        "drifted_pool_stale": drifted["pool_stale"],
        "restored_pool_stale": restored["pool_stale"],
    }


def twin_run_determinism():
    def scene():
        s, _ = _boot()
        s._inner.run_rules()
        _leave_pool(s, AGID)
        s._inner.run_rules()
        _leave_pool(s, SECOND_AGID)
        s._inner.run_rules()
        avs = axe.agenda_verdicts(s, "impotent")
        return sorted(
            [{k: v for k, v in a.items() if k != "_id"} for a in avs],
            key=lambda a: (a["pool_n"], a["pool_stale"]))
    r1, r2 = scene(), scene()
    return {"byte_identical": r1 == r2, "scene": r1}


def main():
    out = {
        "_README": (
            "A21 -- POOL-COMPOSITION DRIFT, CLOSED WITHOUT TOUCHING "
            "gr_condition_lapse.  Every scene below is a LIVE boot + "
            "mutation + run_rules() + read-off; nothing is a fixture "
            "replay.  AR21c per PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment "
            "A21."),
        "engine_sha256": _engine_sha(),
        "seed_version": "1.7.0",
        "seed_sha256": _sha256(os.path.join(ROOT, "seeds", "arc_executor.json")),
        "goal_residuals_seed_sha256":
            _sha256(os.path.join(ROOT, "seeds", "goal_residuals.json")),
        "AR21c_fires_on_drift_no_epoch_bump":
            ar21c_fires_on_drift_no_epoch_bump(),
        "AR21c_does_not_fire_across_epoch_bump_without_drift":
            ar21c_does_not_fire_across_epoch_bump_without_drift(),
        "AR21c_pool_hold_the_reverse_direction":
            ar21c_pool_hold_the_reverse_direction(),
        "twin_run_determinism": twin_run_determinism(),
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, default=str)
    print("wrote", OUT)
    print("engine", out["engine_sha256"][:12])
    print("seed  ", out["seed_sha256"][:12])


if __name__ == "__main__":
    main()
