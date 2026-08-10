#!/usr/bin/env python3
"""A13/WH4(c) — THE IMPOTENCE TERM.  Measurement runner.

Builds the IM1/IM2/IM4/IM5 scenes live (no fixtures beyond the shipped seed
boot), reads `AgendaVerdict{kind:'impotent'}` back off the graph, and writes
one JSON artifact carrying every trace this rung's results doc quotes.  Pure
measurement: no Python decision, mechanical boot -> mutate -> run_rules ->
read-off, the same shape `domains/arc_executor.py`'s own read-off helpers
already are.

Run:
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \\
    PYTHONPATH=runners/dsl/python:. python3 scripts/arc6_impotence_term_measure.py
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
OUT = os.path.join(ROOT, "results", "arc6_impotence_term.json")


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


def _boot(with_magnitude: bool, ladder: bool = True):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    sids = ["program_synthesis", "goal_residuals", "arc_goals"]
    if with_magnitude:
        sids.append("arc_magnitude")
    sids.append("arc_executor")
    for sid in sids:
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    assert _coherence_probe(s), "VALUE LAYER ABSENT on this engine"
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    if with_magnitude:
        from domains import arc_magnitude_ingest as ami
        ami.resolve_attrition_keys(s)
        if ladder:
            ami.install_tier_ladder(s, ami.probe_tier_ladder())
    return s, ag


def _leave_pool(s, agid):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            s.set_attr(n, "headroom_n", 0.0)
            return
    raise AssertionError("no such goal: " + agid)


def _agenda_attrs(s):
    return s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]


def im1_positive():
    s, _ = _boot(with_magnitude=False)
    s._inner.run_rules()
    before = axe.agenda_verdicts(s, "impotent")
    _leave_pool(s, AGID)
    s._inner.run_rules()
    after = axe.agenda_verdicts(s, "impotent")
    return {"before_verdicts": before, "after_verdicts": after,
            "pool_after": axe.pool(s)}


def im1_negative():
    s, _ = _boot(with_magnitude=False)
    s._inner.run_rules()
    return {"pool": axe.pool(s), "verdicts": axe.agenda_verdicts(s, "impotent")}


def im1_empty_pool():
    s, _ = _boot(with_magnitude=False)
    s._inner.run_rules()
    for n in s.nodes("ArcGoal"):
        s.set_attr(n, "status", "retired")
    s._inner.run_rules()
    return {"pool": axe.pool(s), "verdicts": axe.agenda_verdicts(s, "impotent")}


def im2_discriminator():
    s, _ = _boot(with_magnitude=False)
    s._inner.run_rules()
    at = _agenda_attrs(s)
    return {"winner": at["arc_sel_agid"], "AGID_in_pool": AGID in axe.pool(s),
            "verdicts": axe.agenda_verdicts(s, "impotent")}


def im4_compose():
    s, _ = _boot(with_magnitude=True, ladder=True)
    s._inner.run_rules()
    at_before = _agenda_attrs(s)
    before_verdicts = axe.agenda_verdicts(s, "impotent")
    _leave_pool(s, AGID)
    s._inner.run_rules()
    at_after = _agenda_attrs(s)
    after_verdicts = axe.agenda_verdicts(s, "impotent")
    return {"mg_sel_agid_before": at_before["mg_sel_agid"],
            "before_verdicts": before_verdicts,
            "arc_sel_agid_after": at_after["arc_sel_agid"],
            "mg_sel_agid_after": at_after["mg_sel_agid"],
            "after_verdicts": after_verdicts}


def im5_mint_once_and_lapse():
    s, _ = _boot(with_magnitude=False)
    s._inner.run_rules()
    _leave_pool(s, AGID)
    s._inner.run_rules()
    first = axe.agenda_verdicts(s, "impotent")
    s._inner.run_rules()
    s._inner.run_rules()
    unchanged = axe.agenda_verdicts(s, "impotent")

    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == "arc6.claim.tier0_hs1_0_of_10":
            s.set_attr(n, "headroom_n", 0.0)
    s._inner.run_rules()
    different_pool = axe.agenda_verdicts(s, "impotent")

    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    after_epoch_bump = axe.agenda_verdicts(s, "impotent")

    return {"first": first, "unchanged_pool_repeat": unchanged,
            "different_pool": different_pool,
            "after_epoch_bump": after_epoch_bump}


def twin_run_determinism():
    def scene():
        s, _ = _boot(with_magnitude=False)
        s._inner.run_rules()
        _leave_pool(s, AGID)
        s._inner.run_rules()
        avs = axe.agenda_verdicts(s, "impotent")
        return [{k: v for k, v in a.items() if k != "_id"} for a in avs]
    r1, r2 = scene(), scene()
    return {"byte_identical": r1 == r2, "scene": r1}


def main():
    out = {
        "_README": (
            "A13/WH4(c) -- THE IMPOTENCE TERM.  Every scene below is a LIVE "
            "boot + mutation + run_rules() + read-off; nothing is a fixture "
            "replay.  IM1-IM5 per PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment "
            "A13."),
        "engine_sha256": _engine_sha(),
        "seed_version": "1.2.0",
        "seed_sha256": _sha256(os.path.join(ROOT, "seeds", "arc_executor.json")),
        "IM1_positive_and_negative": {
            "positive_leave_pool": im1_positive(),
            "negative_healthy_pool": im1_negative(),
            "empty_pool_is_not_impotent": im1_empty_pool(),
        },
        "IM2_discriminator": im2_discriminator(),
        "IM4_composes_with_order_N": im4_compose(),
        "IM5_mint_once_and_lapse": im5_mint_once_and_lapse(),
        "twin_run_determinism": twin_run_determinism(),
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, default=str)
    print("wrote", OUT)
    print("engine", out["engine_sha256"][:12])
    print("seed  ", out["seed_sha256"][:12])


if __name__ == "__main__":
    main()
