#!/usr/bin/env python3
"""A23 — AR23c: THE REPRICING-LOOP TEST, DONE PROPERLY THIS TIME.

`PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A23, registered BEFORE this
script was written.  A22 SS6 named the next charter: build candidate (a)
(the impotence-specific ask) NOT as a naive reuse of `ag_ask`'s own
`REGION`-fallback re-entry gate, because `REGION(g)` falls back to `g.agid`
whenever `sig_seam` is unset — true of every `supply_blocker`/
`source_claim`/`decomposition_tier` goal this tree has ever minted — so a
naive impotence-ask keyed the same way would inherit the SAME per-goal
re-entry gate and risk a repricing loop with no fixed point (A14 design
investigation finding 3, quoted in AMENDMENT A23).

`tools/build_arc_executor_seed.py` v1.8.0 (this rung) already ships the
FIX: `ax_ask_impotent`, keyed to the `AgendaVerdict` node's own identity
(an `InNeighbours(av, asked_about_verdict)` edge-existence guard) rather
than to `REGION(nearest_unroutable_goal())`.  This script is the MEASURED
A/B comparison the design investigation predicted, not assumed: on the
EXACT SAME live scene — A22's own already-validated construction (decompose
via a REAL horizon reply, both `re_measure` goals via the SAME validated
`headroom_n -> 0` synthetic exit, A13 SS7.1/A22 SS3), driving A14 group-2's
own testimony-chain mechanism (repeated unconditioned `attach_reply` against
`ag_ask`'s OWN already-open questions, which is what drives
`nearest_unroutable_agid` to drift across kinds within ONE measurement
epoch, exactly as A22 SS3 already measured: `decomposition_tier` ->
`supply_blocker` -> `source_claim` -> `source_claim` -> `source_claim`) —
this script installs BOTH `ax_ask_impotent` (the shipped, native rule,
already active via the `arc_executor` seed) AND a THROWAWAY naive
comparator (constructed only in this script via `load_seed_manifest`,
NEVER written to any seed file — mirrors how A14/A22 never shipped a "bad"
alternative into a seed either) that reuses `ag_ask`'s own `REGION`+
`asked_epoch` re-entry-gate SHAPE, applied to the impotence verdict instead
of a value tie.  Both mechanisms watch the SAME chain; their ask counts are
read off directly, live, twin-run for determinism (the IM5/A14/A22
precedent).

Predictions, stated before running (per this arc's own house rule of
registering a prediction before looking, PROGRAM_SYNTHESIS_ARC6_PREREG.md
amendment A23, AR23c):
  * NAIVE fires MULTIPLE times across the chain (once per newly-drifted
    REGION) — no fixed point inside the one-epoch chain.
  * NATIVE fires EXACTLY ONCE for the whole chain — the `av` node backing
    every step is the SAME node throughout (A14's own headline finding:
    testimony reweights the pool WITHOUT changing its membership), so the
    mint-once-by-node-identity guard is satisfied after the first ask and
    stays satisfied for the rest of the chain.

Run:
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \\
    PYTHONPATH=runners/dsl/python:. timeout 300 \\
    python3 scripts/arc6_question_driver_impotence_ask_measure.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts"), os.path.join(ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains import arc_goal_ingest as agi  # noqa: E402

import arc6_impotence_resweep_measure as rw  # noqa: E402
from build_arc_goals_seed import (  # noqa: E402
    A, AND, EQ, EXISTS, HUB, L, MEASURE_EPOCH, NOT, NOT_, REGION, T, V,
)
from build_arc_executor_seed import _nearest_unroutable_goal  # noqa: E402

OUT = os.path.join(ROOT, "results", "arc6_question_driver_impotence_ask.json")

NAIVE_RULE_NAME = "ax_ask_impotent_NAIVE_measurement_only"


def log(*a):
    print(*a, file=sys.stderr)
    sys.stderr.flush()


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# =========================================================================== #
#  THE NAIVE COMPARATOR — constructed here ONLY, never written to a seed
#  file.  Reuses ag_ask's OWN re-entry-gate SHAPE (Not(Exists(ArcQuestion,
#  region==REGION(g), asked_epoch==MEASURE_EPOCH()))), applied to the
#  impotence verdict's nearest_unroutable_goal instead of a value-tie pair.
#  This is candidate (a) AS A22 SS6 WARNED AGAINST BUILDING IT — kept here
#  ONLY as the A/B measurement's control arm.
# =========================================================================== #
def naive_rule_dict():
    goal = _nearest_unroutable_goal()
    return {
        "name": NAIVE_RULE_NAME,
        "comment": (
            "A23 MEASUREMENT-ONLY CONTROL ARM — never shipped to a seed. "
            "The naive reuse AMENDMENT A23's design investigation predicts "
            "does NOT reach a fixed point: keyed exactly like ag_ask's own "
            "re-entry gate (region==REGION(nearest_unroutable_goal), "
            "asked_epoch==MEASURE_EPOCH()), so it re-fires every time "
            "testimony drifts nearest_unroutable_agid to a goal not yet "
            "asked about BY THAT REGION. Mints a THIRD, distinct node type "
            "(neither ArcQuestion nor ArcImpotenceQuestion) so this control "
            "arm cannot itself confound the measurement two different ways: "
            "(1) it cannot satisfy ag_ask's OWN re-entry guard (which reads "
            "region equality over `NodesOfType(ArcQuestion)` specifically — "
            "a coincidental region match, since nearest_unroutable_goal IS "
            "one of the pool members ag_ask itself ranks, would otherwise "
            "silently suppress a genuine ag_ask tie-question this scene's "
            "own chain depends on); (2) it cannot be swept up by the "
            "existing ag_reply_mints_testimony_* rules (the SAME leak the "
            "native rule's own type choice was fixed to avoid, live, during "
            "this rung's own measurement — see ax_ask_impotent's comment)."),
        "batch": True,
        "match": HUB + [["agenda", "has_agenda_verdict", "av"]],
        "where": AND(
            EQ(A(V("av"), "kind"), L("impotent")),
            NOT(EQ(A(V("av"), "stale"), L(1.0))),
            NOT(EXISTS(NOT_("ArcImpotenceQuestionNaiveControl"), "q0",
                       AND(EQ(A(V("q0"), "region"), REGION(goal)),
                           EQ(A(V("q0"), "asked_epoch"), MEASURE_EPOCH())))),
        ),
        "effects": [
            ["add_node", "qn", "ArcImpotenceQuestionNaiveControl", {
                "kind": "impotence_naive",
                "region": T(REGION(goal)),
                "agid_a": T(A(goal, "agid")),
                "asked_epoch": T(MEASURE_EPOCH()),
                "answered": 0.0,
                "status": "open",
            }],
        ],
    }


def _leave_pool_all(s, agids):
    """The SAME A13 SS7.1 pool-exit technique, applied to BOTH `re_measure`
    goals in one pass (A22 SS3's own cheap-extension precedent)."""
    for agid in agids:
        found = False
        for n in s.nodes("ArcGoal"):
            if s.node(n)["attrs"].get("agid") == agid:
                s.set_attr(n, "headroom_n", 0.0)
                found = True
        if not found:
            raise AssertionError("no such goal: " + agid)


def _answer_ordinary_open(s):
    """A14 group-2's own mechanism (`_answer_open`), verbatim in substance:
    `ax_ask_impotent`/the naive control arm mint DISTINCT node types
    (ArcImpotenceQuestion / ArcImpotenceQuestionNaiveControl, not
    ArcQuestion), so `s.nodes("ArcQuestion")` here naturally never includes
    them — no special-case filter needed, by construction, not by a Python
    decision over which questions count."""
    sent = 0
    for n in s.nodes("ArcQuestion"):
        a = s.node(n)["attrs"]
        if a.get("answered") == 1.0 or a.get("status") != "open":
            continue
        agi.attach_reply(s, n, "I do not know either; use your judgement.")
        sent += 1
    return sent


def _impotence_question_counts(s):
    native = [dict(s.node(n)["attrs"], _id=str(n))
              for n in s.nodes("ArcImpotenceQuestion")]
    naive = [dict(s.node(n)["attrs"], _id=str(n))
             for n in s.nodes("ArcImpotenceQuestionNaiveControl")]
    return {
        "native_count": len(native),
        "native_regions": [q.get("region") for q in native],
        "naive_count": len(naive),
        "naive_regions": [q.get("region") for q in naive],
    }


def run_scene(n_replies=6):
    s, ag = rw.boot()
    manifest = {"id": "a23_naive_measurement_only_" + str(id(s)),
                "version": "0.0.0", "depends_on": [],
                "rules": [naive_rule_dict()]}
    s._inner.load_seed_manifest(manifest, ag)
    s._inner.run_rules()

    decompose_rec = rw.drive_decompose(s, 5.0)
    s._inner.run_rules()
    #  The structural re_measure ArcGoal does not exist until its own
    #  residual actually goes stale (a real mint-on-condition rule, A22 SS8.3
    #  -- the SAME ordering fix A22's own script needed).  Force staleness
    #  the SAME narrow poke A13 SS7.1/A15 SS4.2 validated FIRST; row-verdict
    #  is organically stale already at boot (A22's own finding, unchanged).
    rw.axe._put_fact(s, "arc6_structural_ceiling_present", "0")
    s._inner.run_rules()
    _leave_pool_all(s, [rw.AGID_ROW, rw.AGID_STRUCT])
    s._inner.run_rules()

    steps = [dict(rw._snapshot(s, "reply_0"),
                  replies_sent_this_step=0,
                  pool_agids_sig=sorted(rw.axe.pool(s)),
                  impotence_counts=_impotence_question_counts(s))]
    for i in range(1, n_replies + 1):
        sent = _answer_ordinary_open(s)
        s._inner.run_rules()
        snap = rw._snapshot(s, "reply_%d" % i)
        snap["replies_sent_this_step"] = sent
        snap["pool_agids_sig"] = sorted(rw.axe.pool(s))
        snap["impotence_counts"] = _impotence_question_counts(s)
        steps.append(snap)
        if sent == 0:
            break

    kinds_seen = [st["live_winner"]["sel_kind"] for st in steps]
    final_counts = steps[-1]["impotence_counts"]
    return {
        "decompose_rec": decompose_rec,
        "steps": steps,
        "pool_signature_constant": len({tuple(st["pool_agids_sig"])
                                        for st in steps}) == 1,
        "live_winner_kind_sequence": kinds_seen,
        "n_distinct_kinds_in_chain": len(set(kinds_seen)),
        "FINAL_native_ask_count": final_counts["native_count"],
        "FINAL_native_regions": final_counts["native_regions"],
        "FINAL_naive_ask_count": final_counts["naive_count"],
        "FINAL_naive_regions": final_counts["naive_regions"],
        "NATIVE_REACHED_FIXED_POINT": final_counts["native_count"] <= 1,
        "NAIVE_REACHED_FIXED_POINT": final_counts["naive_count"] <= 1,
    }


def main():
    t0 = time.time()
    log("== run 1 ==")
    run1 = run_scene()
    log("run1: native=%d naive=%d kinds=%r" % (
        run1["FINAL_native_ask_count"], run1["FINAL_naive_ask_count"],
        run1["live_winner_kind_sequence"]))
    log("== run 2 (twin-run determinism check) ==")
    run2 = run_scene()
    log("run2: native=%d naive=%d kinds=%r" % (
        run2["FINAL_native_ask_count"], run2["FINAL_naive_ask_count"],
        run2["live_winner_kind_sequence"]))

    twin_run_identical = (
        run1["live_winner_kind_sequence"] == run2["live_winner_kind_sequence"]
        and run1["FINAL_native_ask_count"] == run2["FINAL_native_ask_count"]
        and run1["FINAL_naive_ask_count"] == run2["FINAL_naive_ask_count"])

    out = {
        "_README": (
            "A23 -- AR23c, the repricing-loop test.  Two independent live "
            "runs of the SAME scene (A22's own decompose + synthetic-exit "
            "construction, A14 group-2's own testimony-chain mechanism), "
            "comparing the SHIPPED native ax_ask_impotent (mint-once by the "
            "AgendaVerdict node's own identity) against a throwaway naive "
            "comparator (mint-once by REGION(nearest_unroutable_goal), the "
            "SAME shape ag_ask itself uses) that is constructed ONLY in "
            "this script and never written to a seed.  Bars: "
            "PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A23, AR23c."),
        "engine_sha256": _sha256_file(os.path.join(
            ROOT, "runners", "dsl", "python", "substrate_rs",
            "_native.abi3.so")),
        "seed_sha256_arc_executor": _sha256_file(
            os.path.join(ROOT, "seeds", "arc_executor.json")),
        "run1": run1,
        "run2": run2,
        "twin_run_byte_identical": twin_run_identical,
        "VERDICT": {
            "native_reached_fixed_point": run1["NATIVE_REACHED_FIXED_POINT"]
                and run2["NATIVE_REACHED_FIXED_POINT"],
            "naive_reached_fixed_point": run1["NAIVE_REACHED_FIXED_POINT"]
                and run2["NAIVE_REACHED_FIXED_POINT"],
            "n_distinct_kinds_in_chain": run1["n_distinct_kinds_in_chain"],
            "prediction_confirmed": (
                run1["NATIVE_REACHED_FIXED_POINT"]
                and not run1["NAIVE_REACHED_FIXED_POINT"]),
        },
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, default=str)
    log("wrote", OUT)
    print(json.dumps(out["VERDICT"], indent=2, default=str))
    print("total elapsed:", out["elapsed_seconds"], "s")


if __name__ == "__main__":
    main()
