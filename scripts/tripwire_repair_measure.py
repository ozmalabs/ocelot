#!/usr/bin/env python3
"""TRIPWIRE REPAIR — L1b's structural audits become AST-based (confirmatory run).

Pre-registration: `VISION_TRIPWIRE_REPAIR_PREREG.md`, committed BEFORE this run at
`7c920c42` (§3). NO seeds consumed — every arm is deterministic static analysis of
committed seed JSON plus synthetic Term trees built here, so there is no sampling and
no noise floor to draw. 53000-53999 remain CLEAN.

Arms (see the prereg for predictions and failing inputs):
  BLIND  — the CURRENT string test passes on a seed that DOES contain a bound
  SEES   — the AST detector finds the `Lt`-inside-`Not(Exists)` bound
  EVADE  — 7 semantically-equivalent bound compositions; AST must catch ALL, the old
           string test must miss at least one                        (the RISKED arm)
  FP     — genuine non-bounds are NOT flagged                       (the CONJUNCTION)
  TABLE  — L1b's audit table re-run; any changed verdict reported

Run from the gamma-substrate dir:
    python scripts/tripwire_repair_measure.py
"""
from __future__ import annotations

import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

from tools.term_ast_audit import (  # noqa: E402
    audit_seed, audit_seed_file, comparisons_in, legacy_string_test,
)

SEEDS = os.path.join(_ROOT, "seeds")


# ================================================================================
# THE SYNTHETIC BATTERIES — Term trees built here, never loaded into the agent
# ================================================================================
#
# Every EVASION entry is SEMANTICALLY THE SAME PREDICATE: "the observation's distance
# lies within the packing radius". Only the COMPOSITION varies. A detector that is
# reading structure rather than text must return the same verdict for all seven.

def _dist():
    """A computed distance magnitude — `Sqrt(Plus(...))`."""
    return {"type": "Sqrt", "arg": {"type": "Plus", "items": [
        {"type": "Attr", "node": {"type": "Var", "name": "obs"}, "name": "d_rg"},
        {"type": "Attr", "node": {"type": "Var", "name": "obs"}, "name": "d_by"}]}}


def _radius():
    """A computed threshold — HALF the minimum separation (`Times` with an `items`
    LIST; the `a`/`b` form would be an EMPTY PRODUCT = 1, process rule 4)."""
    return {"type": "Times", "items": [
        {"type": "Lit", "value": 0.5},
        {"type": "MinOver", "source": {"type": "NodesOfType",
                                       "node_type": "ColourCategory"},
         "term": {"type": "Attr", "node": {"type": "Var", "name": "c"},
                  "name": "sep"}}]}


def evasion_battery():
    """Seven equivalent spellings of ONE bound. E1 is the ONLY one the old test sees."""
    d, r = _dist, _radius
    return [
        ("E1_plain_Lte",
         "the spelling the old test was written for — the POSITIVE CONTROL that "
         "proves the old test is not simply broken",
         {"type": "Lte", "a": d(), "b": r()}),
        ("E2_strict_Lt",
         "re-spelled `Lt` — the LANDED colour composition",
         {"type": "Lt", "a": d(), "b": r()}),
        ("E3_Lt_inside_Not_Exists",
         "the ACTUAL k=1 shape: negated and nested inside `Not(Exists(Filter(...)))`",
         {"type": "Not", "arg": {"type": "Exists", "source": {
             "type": "Filter",
             "source": {"type": "NodesOfType", "node_type": "ColourCategory"},
             "pred": {"type": "Lt", "a": d(), "b": r()}}}}),
        ("E4_reversed_Gte",
         "operands SWAPPED and the comparator mirrored — identical semantics",
         {"type": "Gte", "a": r(), "b": d()}),
        ("E5_reversed_Gt",
         "swapped AND strict",
         {"type": "Gt", "a": r(), "b": d()}),
        ("E6_double_negation",
         "buried under two `Not`s inside an `And` — even polarity, still a bound",
         {"type": "And", "items": [
             {"type": "Not", "arg": {"type": "Not", "arg": {
                 "type": "Lt", "a": {"type": "Abs", "arg": d()}, "b": r()}}},
             {"type": "Eq", "a": {"type": "Lit", "value": 1},
              "b": {"type": "Lit", "value": 1}}]}),
        ("E7_in_a_where_clause",
         "moved out of `effects` into a `where` clause — a POSITION the old "
         "rule-scoped scan can miss when the bound is relocated to a sibling rule",
         {"name": "syn_rule", "match": [], "where": [
             {"type": "Gte", "a": r(), "b": d()}], "effects": []}),
    ]


def nonbound_battery():
    """Genuine NON-bounds. A detector that flags these is useless (the conjunction)."""
    return [
        ("N1_flag_read",
         "a config gate: `Gt(Attr(identity), Lit(0.0))`",
         {"type": "Gt", "a": {"type": "Attr", "node": {"type": "Var", "name": "ag"},
                              "name": "identity"},
          "b": {"type": "Lit", "value": 0.0}}),
        ("N2_cardinality",
         "exact-equality admission: `Lt(Count(residual), Lit(1))` — L1b's own "
         "similarity row calls this NOT a verdict bound",
         {"type": "Lt", "a": {"type": "Count", "source": {
             "type": "Neighbours", "node": {"type": "Var", "name": "h"},
             "edge": "residual"}},
          "b": {"type": "Lit", "value": 1}}),
        ("N3_epoch",
         "a scheduling comparison: `Lt(Attr(epoch), Attr(codebook_epoch))`",
         {"type": "Lt", "a": {"type": "Attr", "node": {"type": "Var", "name": "h"},
                              "name": "epoch"},
          "b": {"type": "Attr", "node": {"type": "Var", "name": "ag"},
                "name": "codebook_epoch"}}),
    ]


# ================================================================================
# THE ARMS
# ================================================================================

def arm_BLIND():
    """The PREMISE (ENTAILED, declared not banked): the current tripwire PASSES on a
    seed that DOES contain a bound. Passing means failing to trip."""
    path = os.path.join(SEEDS, "vision_colour_identity.json")
    seed = json.load(open(path))
    rule = [r for r in seed["rules"] if r["name"] == "ci_assign"][0]
    return {
        "seed_version": seed.get("version"),
        "old_test_says_no_Lte": legacy_string_test(rule, "Lte"),
        "old_test_says_no_Gte": legacy_string_test(rule, "Gte"),
        "actual_comparators": {op: sum(1 for c in comparisons_in(rule) if c.op == op)
                               for op in ("Lt", "Lte", "Gt", "Gte")},
        "pass": legacy_string_test(rule, "Lte"),
        "note": "PASSES ⇒ the tripwire does not trip ⇒ blindness reproduced",
    }


def arm_SEES():
    """The repaired detector finds the `Lt`-inside-`Not(Exists)` bound."""
    a = audit_seed_file(os.path.join(SEEDS, "vision_colour_identity.json"), "ci_assign")
    negated = [d for d in a["T1_detail"] if d["not_depth"] > 0]
    return {"audit": a, "n_bounds": a["T1_bound_like"],
            "n_negated_bounds": len(negated),
            "pass": a["T1_bound_like"] >= 1}


def arm_EVADE():
    """THE RISKED ARM. Seven equivalent bounds: AST must catch 7/7; the old string
    test must miss at least one."""
    rows = []
    for name, why, tree in evasion_battery():
        found = comparisons_in(tree)
        rows.append({
            "case": name, "why": why,
            "ast_bound_like": sum(1 for c in found if c.bound_like),
            "ast_detects": any(c.bound_like for c in found),
            # the old test only ever looked for `Lte`
            "old_string_test_detects": not legacy_string_test(tree, "Lte"),
            "max_not_depth": max([c.not_depth for c in found], default=0),
        })
    ast_hits = sum(1 for r in rows if r["ast_detects"])
    old_hits = sum(1 for r in rows if r["old_string_test_detects"])
    return {"rows": rows, "n": len(rows), "ast_detected": ast_hits,
            "old_detected": old_hits, "old_missed": len(rows) - old_hits,
            "pass": ast_hits == len(rows) and old_hits < len(rows)}


def arm_FP():
    """THE CONJUNCTION. Genuine non-bounds must NOT be flagged T1 — while T0 flags
    them, which is exactly why both tiers are reported."""
    rows = []
    for name, why, tree in nonbound_battery():
        found = comparisons_in(tree)
        rows.append({"case": name, "why": why,
                     "T0_any": len(found),
                     "T1_bound_like": sum(1 for c in found if c.bound_like)})
    real = audit_seed_file(os.path.join(SEEDS, "shape_decode_loop.json"))
    return {
        "synthetic": rows,
        "synthetic_false_positives": sum(r["T1_bound_like"] for r in rows),
        "real_seed": "shape_decode_loop.json",
        "real_T0_any_comparator": real["T0_any_comparator"],
        "real_T1_bound_like": real["T1_bound_like"],
        "real_non_bound_reasons": sorted({d["reason"]
                                          for d in real["T0_non_bound_detail"]}),
        "pass": (sum(r["T1_bound_like"] for r in rows) == 0
                 and real["T1_bound_like"] == 0
                 and real["T0_any_comparator"] > 0),
        "note": ("T0 > 0 on the real seed is required: it makes this arm "
                 "non-vacuous — there ARE comparators there to misclassify"),
    }


def arm_TABLE():
    """L1b's audit table re-run with the AST detector. Report any changed verdict."""
    targets = [
        ("colour identity (ci_assign)", "vision_colour_identity.json", "ci_assign",
         "NONE - zero Lte nodes"),
        ("similarity / untangling (shape_decode_loop)", "shape_decode_loop.json", None,
         "NONE - zero Lte/Gte in the whole seed"),
        ("deformation (df_recognize)", "vision_deformation.json", "df_recognize",
         "3x Lte (eps)"),
        ("T2 category (cat_recognize)", "vision_category.json", None,
         "box containment + exact signature Eq"),
        ("L1b's own gate (vision_uniqueness)", "vision_uniqueness.json", None,
         "Lte 1.0 (inherited lattice step)"),
    ]
    rows = []
    for label, fname, rule, l1b_said in targets:
        path = os.path.join(SEEDS, fname)
        if not os.path.exists(path):
            rows.append({"rung": label, "seed": fname, "status": "SEED ABSENT"})
            continue
        a = audit_seed_file(path, rule)
        tree = json.load(open(path))
        if rule:
            tree = [r for r in tree["rules"] if r["name"] == rule][0]
        rows.append({
            "rung": label, "seed": fname, "scope": rule or "<whole seed>",
            "L1b_recorded": l1b_said,
            "old_test_says_no_bound_Lte": legacy_string_test(tree, "Lte"),
            "T0_any_comparator": a["T0_any_comparator"],
            "T0_by_op": a["T0_by_op"],
            "T1_bound_like": a["T1_bound_like"],
            "AST_has_bound": a["has_bound"],
            "negated_bounds": sum(1 for d in a["T1_detail"] if d["not_depth"] > 0),
            # a verdict CHANGES when the old instrument said "no bound" and the AST
            # detector finds one
            "VERDICT_CHANGES": bool(legacy_string_test(tree, "Lte")) and a["has_bound"],
        })
    return {"rows": rows,
            "n_changed": sum(1 for r in rows if r.get("VERDICT_CHANGES")),
            "changed": [r["rung"] for r in rows if r.get("VERDICT_CHANGES")]}


def main():
    t0 = time.time()
    res = {
        "rung": "TRIPWIRE REPAIR — L1b's structural audits become AST-based",
        "prereg": "VISION_TRIPWIRE_REPAIR_PREREG.md @ 7c920c42",
        "base_main_HEAD": "b7c3eaeb",
        "provenance": provenance_line(),
        "seeds_consumed": "NONE (deterministic static analysis; 53000-53999 CLEAN)",
        "BLIND": arm_BLIND(),
        "SEES": arm_SEES(),
        "EVADE": arm_EVADE(),
        "FP": arm_FP(),
        "TABLE": arm_TABLE(),
    }
    res["elapsed_s"] = round(time.time() - t0, 3)
    out = os.path.join(_ROOT, "results", "tripwire_repair.json")
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    for arm in ("BLIND", "SEES", "EVADE", "FP"):
        print(f"{arm:7s} pass={res[arm]['pass']}")
    print(f"TABLE   verdicts changed: {res['TABLE']['n_changed']} "
          f"{res['TABLE']['changed']}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
