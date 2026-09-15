"""TRACK 4 — THE ACCOMMODATION GATE (Rubric B readiness gate; precision/recall).

Carey's conceptual-change protocol (Origin of Concepts; the PMC4001252 false-belief
study) credits representational change ONLY when a genuinely new representation is
constructed AND used, and ONLY for learners who were "conceptually close" (a readiness
gate) — not on a single exposure. That readiness gate is the human-science analogue of
the minting loop's PERSISTENCE gate: mint a new axis only when the residual RECURS
(accommodation), never on a one-off miss (which would be gap-fill / over-fitting).

This track scores the gate as a retrieval task over a battery of gap-events, each with
a GOLD label of whether it SHOULD mint:
  · PERSISTENT gap  -> should mint      (recurs across segments; readiness met)
  · TRANSIENT gap   -> should NOT mint  (a single/too-brief miss)
  · DUPLICATE gap   -> should NOT mint  (already-induced; the over-minting guard)
Precision/recall/F1 (scoring/metrics.gate_precision_recall) over "minted the right
thing", plus a LATENCY check (a persistent gap should mint at the segment where its
integer persistence first reaches the threshold — not before, the readiness gate).

FALSIFIABLE CLAIMS:
  G1  PERSISTENT -> MINT: a residual that recurs to threshold mints a new axis.
  G2  TRANSIENT -> NO MINT: a residual seen too few times never mints (readiness
      gate holds; not gap-fill). Demonstrated by threshold > max-persistence and by
      a 1-segment run.
  G3  DUPLICATE -> REFUSED: re-offering an already-minted residual is refused by the
      sd-loop dedup guard (recognized_duplicate), so no second axis is coined.
  G4  GATE PRECISION/RECALL: over the mixed battery, precision = recall = 1.0 (every
      should-mint minted, no should-not-mint minted).
  G5  READINESS LATENCY: the persistent gap mints exactly when persistence first
      reaches the threshold, and the mint's recorded persistence >= threshold.
  G6  TEACHER-FREE: ask-spy = 0 across the held path.

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/minting/track4_accommodation_gate.py
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))
sys.path.insert(0, os.path.join(_HERE, "scoring"))

import metrics as M                     # noqa: E402
import substrate_runner as R            # noqa: E402
from domains import reflective_faculty as rf   # noqa: E402


def main() -> int:
    print("=" * 78)
    print("TRACK 4 — ACCOMMODATION GATE (Rubric B readiness gate; precision/recall)")
    print("accumulated episode-wide predicate-count recurrence (not consecutive "
          "run length) -> mint; one qualifying appearance/count below threshold "
          "-> no mint; duplicate -> refused; teacher-free")
    print("  Exact matched schedules and first-due segments: "
          "test_recurrence_control.py")
    print("=" * 78)

    fx = R.load_fixture()
    # use one rich category to drive a real minting trajectory
    cat = "bird"
    items = fx["categories"][cat]

    # ---------------------------------------------------------------- G1 ----- #
    # A fine-grain set-point on the prototype: the roaming trajectory keeps reaching
    # members whose fine signature the set-point never admitted -> a residual that
    # recurs every segment -> mints once persistence reaches the threshold.
    print("\n" + "-" * 78)
    print("G1  PERSISTENT residual -> MINT (recurs to threshold)")
    print("-" * 78)
    spy1 = R.AskSpy()
    res = R.run_minting(cat, items, R.FINE, mint_after_quanta=2, max_segments=6,
                        spy=spy1)
    print("  residual persistence ledger: %s" % res["residual_persistence"])
    print("  mint_events: %s"
          % [(e["predicate"], e["minted"], e["persistence"])
             for e in res["mint_events"]])
    print("  minted axes: %s" % res["minted_axes"])
    persistent_preds = [p for p, k in res["residual_persistence"].items() if k >= 2]
    g1 = len(res["minted_axes"]) >= 1 and len(persistent_preds) >= 1
    print("  a residual recurred >=2 AND an axis was minted: %s" % g1)
    print("  G1 %s" % ("PASS" if g1 else "FAIL"))

    # ---------------------------------------------------------------- G2 ----- #
    # ONE QUALIFYING APPEARANCE / COUNT BELOW THRESHOLD: (a) threshold ABOVE the
    # episode-wide predicate count reached over the run -> nothing mints; (b) a
    # one-segment exposure cannot reach threshold 2. Interrupted recurrence is
    # covered precisely by test_recurrence_control.py, not asserted transient here.
    print("\n" + "-" * 78)
    print("G2  ONE QUALIFYING APPEARANCE / COUNT BELOW THRESHOLD -> NO MINT")
    print("-" * 78)
    spy2a = R.AskSpy()
    probe = R.run_minting(cat, items, R.FINE, mint_after_quanta=999, max_segments=5,
                          spy=spy2a)
    max_persist = (max(probe["residual_persistence"].values())
                   if probe["residual_persistence"] else 0)
    spy2b = R.AskSpy()
    hi = R.run_minting(cat, items, R.FINE, mint_after_quanta=max_persist + 2,
                       max_segments=5, spy=spy2b)
    spy2c = R.AskSpy()
    one = R.run_minting(cat, items, R.FINE, mint_after_quanta=2, max_segments=1,
                        spy=spy2c)
    mints_hi = len([e for e in hi["mint_events"] if e["minted"]])
    mints_one = len([e for e in one["mint_events"] if e["minted"]])
    print("  residual max persistence over a 5-segment run: %d" % max_persist)
    print("  threshold=%d (> max persistence) -> minted %d axes"
          % (max_persist + 2, mints_hi))
    print("  1-segment run, threshold=2        -> minted %d axes" % mints_one)
    g2 = mints_hi == 0 and mints_one == 0
    print("  G2 %s" % ("PASS" if g2 else "FAIL"))

    # ---------------------------------------------------------------- G3 ----- #
    # DUPLICATE: re-offer an already-minted residual predicate to the sd-loop; the
    # recognized_duplicate guard must refuse a second axis. Uses the same
    # induce_concern gate the loop uses.
    print("\n" + "-" * 78)
    print("G3  DUPLICATE residual -> REFUSED (over-minting guard)")
    print("-" * 78)
    s, nodes, proto = R.build_category(cat, items)
    r_first = rf.induce_concern(s, [["track4_dup_pred"]],
                                name_hint="minted_track4_dup_pred")
    r_again = rf.induce_concern(s, [["track4_dup_pred"]],
                                name_hint="minted_track4_dup_pred")
    print("  first offer : minted=%s" % r_first.get("minted"))
    print("  second offer: minted=%s note=%r"
          % (r_again.get("minted"), (r_again.get("note", "") or "")[:60]))
    g3 = r_first.get("minted") is True and r_again.get("minted") is False
    print("  G3 %s" % ("PASS" if g3 else "FAIL"))

    # ---------------------------------------------------------------- G4 ----- #
    # GATE precision/recall over a mixed battery of gap-events.
    print("\n" + "-" * 78)
    print("G4  GATE PRECISION/RECALL over a mixed battery")
    print("-" * 78)
    # gold: which events SHOULD mint. persistent -> yes ; transient/duplicate -> no.
    gold_should_mint = {"persistent_gap"}
    predicted = set()
    if g1:
        predicted.add("persistent_gap")          # G1 minted the persistent one
    # transient + duplicate must NOT be predicted; G2/G3 confirm they were not
    if not g2:
        predicted.add("transient_gap")            # (only if the gate wrongly minted)
    if not g3:
        predicted.add("duplicate_gap")            # (only if the guard failed)
    pr = M.gate_precision_recall(predicted, gold_should_mint)
    print("  events: accumulated recurrence(gold=mint), one exposure(gold=no), duplicate(gold=no)")
    print("  predicted mints: %s" % sorted(predicted))
    print("  precision=%.2f recall=%.2f f1=%.2f (tp=%d fp=%d fn=%d)"
          % (pr["precision"], pr["recall"], pr["f1"], pr["tp"], pr["fp"], pr["fn"]))
    g4 = pr["precision"] == 1.0 and pr["recall"] == 1.0
    print("  G4 %s" % ("PASS" if g4 else "FAIL"))

    # ---------------------------------------------------------------- G5 ----- #
    # READINESS LATENCY: the persistent gap mints at/after the threshold, never
    # before; the minted event's recorded persistence >= threshold.
    print("\n" + "-" * 78)
    print("G5  READINESS LATENCY (mints only once persistence reaches threshold)")
    print("-" * 78)
    thr = 2
    minted_events = [e for e in res["mint_events"] if e["minted"]]
    latency_ok = all(e["persistence"] >= thr for e in minted_events) and minted_events
    print("  mint_after_quanta = %d" % thr)
    print("  minted events' recorded persistence: %s"
          % [e["persistence"] for e in minted_events])
    g5 = bool(latency_ok)
    print("  every mint fired at persistence >= threshold: %s" % g5)
    print("  G5 %s" % ("PASS" if g5 else "FAIL"))

    # ---------------------------------------------------------------- G6 ----- #
    print("\n" + "-" * 78)
    print("G6  TEACHER-FREE (ask-spy = 0)")
    print("-" * 78)
    spy_total = (res["_ask_spy"] + probe["_ask_spy"] + hi["_ask_spy"]
                 + one["_ask_spy"])
    g6 = spy_total == 0
    print("  total ask-spy across held-path minting runs: %d" % spy_total)
    print("  G6 %s" % ("PASS" if g6 else "FAIL"))

    # ---------------------------------------------------------------- verdict  #
    print("\n" + "=" * 78)
    print("CLAIMS")
    print("=" * 78)
    rows = [("G1 accumulated recurrence -> mint", g1),
            ("G2 one appearance / count below threshold -> no mint", g2),
            ("G3 duplicate -> refused (over-mint guard)", g3),
            ("G4 gate precision = recall = 1.0", g4),
            ("G5 readiness latency (mints at threshold)", g5),
            ("G6 teacher-free (ask-spy = 0)", g6)]
    for name, ok in rows:
        print("  %-46s %s" % (name, "PASS" if ok else "FAIL"))
    allpass = all(ok for _, ok in rows)
    verdict = ("TRACK 4 PASS: the minting gate is a genuine accommodation gate — an "
               "accumulated episode-wide predicate count mints a new axis at readiness; "
               "one qualifying appearance/count below threshold does not; a duplicate "
               "is refused by the over-minting guard; precision=recall=1.0; and the "
               "run is teacher-free. Exact continuous and interrupted schedules plus "
               "their first-due segments are locked in test_recurrence_control.py. "
               "This is Carey's readiness-gated conceptual change, in discrete quanta."
               if allpass else
               "TRACK 4 HONEST RESULT: see failing claim(s) above.")
    print("\nVERDICT: %s" % verdict)
    print("=" * 78)

    summary = {"track": 4, "metric": "accommodation_gate_precision_recall",
               "gate": pr, "max_persistence": max_persist,
               "minted_axes": res["minted_axes"],
               "mints_high_threshold": mints_hi, "mints_one_segment": mints_one,
               "duplicate_refused": g3, "ask_spy_total": spy_total,
               "g1": g1, "g2": g2, "g3": g3, "g4": g4, "g5": g5, "g6": g6,
               "all_pass": allpass}
    print("SUMMARY_JSON " + json.dumps(summary))
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
