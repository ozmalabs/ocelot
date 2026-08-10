#!/usr/bin/env python3
"""ATTR-THRESHOLD FALSE NEGATIVE — the confirmatory run.

Specified in `VISION_AST_ATTR_PREREG.md`, committed BEFORE this run at `bfc1eef5`.

Closes (as far as it is closable) the false-negative class the tripwire rung measured in
its OWN detector and deliberately left unpatched under §5: a bound whose THRESHOLD IS A
STORED ATTRIBUTE is atomic-vs-atomic, so T1 reads it as a flag/epoch read and misses it.

STATIC ANALYSIS ONLY. Evaluates no Term, runs no episode, consumes NO seed — 53000-53999
allocated and expected to remain CLEAN. Holds no agent state, makes no agent decision
(CLAUDE.md): audit tooling, same class as the AST scan L1b already applies to Python.
"""
from __future__ import annotations

import glob
import importlib.util
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEEDS = os.path.join(ROOT, "seeds")
sys.path.insert(0, ROOT)

from tools.term_ast_audit import (  # noqa: E402
    audit_seed_file, comparisons_in, is_codebook_crossing, scope_from_match,
    vars_referenced, walk_terms_scoped,
)

# The five rows of L1b's audit table, as the tripwire rung re-ran them.
# `scope=None` means WHOLE SEED — which is how the tripwire rung actually measured the
# category row, despite labelling it `cat_recognize` (reconciled in the results).
TABLE = [
    ("colour identity", "vision_colour_identity.json", "ci_assign"),
    ("similarity",      "shape_decode_loop.json",      None),
    ("deformation",     "vision_deformation.json",     "df_recognize"),
    ("T2 category",     "vision_category.json",        None),
    ("L1b gate",        "vision_uniqueness.json",      None),
]

# What the tripwire rung published (`VISION_TRIPWIRE_REPAIR_RESULTS.md:111-117`).
TRIPWIRE_PUBLISHED = {
    "colour identity": {"T0": 6,  "T1": 1},
    "similarity":      {"T0": 19, "T1": 0},
    "deformation":     {"T0": 3,  "T1": 3},
    "T2 category":     {"T0": 9,  "T1": 0},
    "L1b gate":        {"T0": 10, "T1": 6},
}


def _tripwire_module():
    """Load the tripwire rung's batteries so they are re-run AS PUBLISHED, not copied."""
    spec = importlib.util.spec_from_file_location(
        "tripwire_repair_measure", os.path.join(HERE, "tripwire_repair_measure.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _canon(node):
    """Erase the ONLY thing that differs between a bound and an epoch read: names."""
    if isinstance(node, dict):
        out = {}
        for k, v in sorted(node.items()):
            if k in ("key", "name") and isinstance(v, str) and node.get("type") in ("Attr", "Var"):
                out[k] = "<erased>"
            else:
                out[k] = _canon(v)
        return out
    if isinstance(node, list):
        return [_canon(x) for x in node]
    return node


# ================================================================================
# THE ARMS
# ================================================================================

def arm_HEADLINE():
    """RISKED. T2 finds T2-category's four `Lte(Attr,Attr)` box-containment bounds."""
    rule = audit_seed_file(os.path.join(SEEDS, "vision_category.json"), "cat_recognize")
    whole = audit_seed_file(os.path.join(SEEDS, "vision_category.json"), None)
    promoted = [d for d in rule["T2_detail"] if d["via"] == "T2_codebook_crossing"]
    return {
        "rule_scoped": {k: rule[k] for k in
                        ("T0_any_comparator", "T1_bound_like", "T2_bound_like")},
        "whole_seed": {k: whole[k] for k in
                       ("T0_any_comparator", "T1_bound_like", "T2_bound_like")},
        "promoted_detail": promoted,
        "all_promoted_are_Lte_Attr_Attr": all(
            d["op"] == "Lte" and d["operands"] == ["Attr", "Attr"] for d in promoted),
        "pass": len(promoted) == 4 and rule["T1_bound_like"] == 0,
    }


def arm_CONJUNCTION():
    """RISKED — the arm a detect-everything build MUST fail.

    Similarity must still report ZERO genuine bounds (T0's 19 must NOT return), and the
    tripwire rung's three declared non-bounds must stay non-bounds.
    """
    sim = audit_seed_file(os.path.join(SEEDS, "shape_decode_loop.json"), None)
    tw = _tripwire_module()
    fps = []
    for name, why, tree in tw.nonbound_battery():
        found = comparisons_in(tree)
        fps.append({"case": name, "T1": any(c.bound_like for c in found),
                    "T2": any(c.t2_bound_like for c in found)})
    return {
        "similarity_T0": sim["T0_any_comparator"],
        "similarity_T1": sim["T1_bound_like"],
        "similarity_T2": sim["T2_bound_like"],
        "similarity_undecidable_residual": sim["undecidable_residual"],
        "similarity_residual_detail": sim["undecidable_residual_detail"],
        "nonbound_battery": fps,
        "n_false_positives": sum(1 for f in fps if f["T2"]),
        "pass": sim["T2_bound_like"] == 0 and not any(f["T2"] for f in fps),
    }


def arm_EVADE():
    """RISKED. The tripwire rung's seven equivalent spellings must still be 7/7."""
    tw = _tripwire_module()
    rows = []
    for name, why, tree in tw.evasion_battery():
        found = comparisons_in(tree)
        rows.append({"case": name,
                     "T1": any(c.bound_like for c in found),
                     "T2": any(c.t2_bound_like for c in found)})
    return {"battery": rows,
            "T1_hits": sum(1 for r in rows if r["T1"]),
            "T2_hits": sum(1 for r in rows if r["T2"]),
            "pass": all(r["T2"] for r in rows) and len(rows) == 7}


def arm_TABLE():
    """RISKED. Re-run every audit-table row; exactly ONE verdict must move."""
    rows = []
    for label, seed, scope in TABLE:
        a = audit_seed_file(os.path.join(SEEDS, seed), scope)
        pub = TRIPWIRE_PUBLISHED[label]
        rows.append({
            "row": label, "seed": seed, "scope": scope or "<whole seed>",
            "tripwire_T0": pub["T0"], "tripwire_T1": pub["T1"],
            "T0": a["T0_any_comparator"], "T1": a["T1_bound_like"],
            "T2": a["T2_bound_like"],
            "T0_reproduces": a["T0_any_comparator"] == pub["T0"],
            "T1_reproduces": a["T1_bound_like"] == pub["T1"],
            "verdict_moves": a["T2_bound_like"] != a["T1_bound_like"],
            "undecidable_residual": a["undecidable_residual"],
            "bound_range": a["bound_range"],
        })
    moved = [r for r in rows if r["verdict_moves"]]
    return {"rows": rows, "n_verdicts_moved": len(moved),
            "moved": [r["row"] for r in moved],
            "all_T0_reproduce": all(r["T0_reproduces"] for r in rows),
            "all_T1_reproduce": all(r["T1_reproduces"] for r in rows),
            "pass": len(moved) == 1 and moved[0]["row"] == "T2 category"
                    and all(r["T0_reproduces"] and r["T1_reproduces"] for r in rows)}


def arm_DERIVED_NEGATIVE():
    """ENTAILED — declared, NOT banked. The residual class is NOT structurally decidable.

    PROOF BY AST-ISOMORPHISM, not assertion: a genuine stored-threshold bound and the
    tripwire rung's own DECLARED non-bound are the same AST once names are erased.
    """
    genuine = {"type": "Lt",
               "a": {"type": "Attr", "node": {"type": "Var", "name": "h"}, "key": "dist"},
               "b": {"type": "Attr", "node": {"type": "Var", "name": "ag"}, "key": "bound"}}
    declared_nonbound = {"type": "Lt",
                         "a": {"type": "Attr", "node": {"type": "Var", "name": "h"}, "key": "epoch"},
                         "b": {"type": "Attr", "node": {"type": "Var", "name": "ag"}, "key": "codebook_epoch"}}
    identical = _canon(genuine) == _canon(declared_nonbound)
    return {
        "canonical_asts_identical": identical,
        "genuine_bound_T2": any(c.t2_bound_like for c in comparisons_in(genuine)),
        "declared_nonbound_T2": any(c.t2_bound_like for c in comparisons_in(declared_nonbound)),
        "conclusion": ("NOT structurally decidable — the two differ ONLY in what the "
                       "attribute names MEAN, so any structural predicate assigns them "
                       "the same verdict. The audit table must report a RANGE for this "
                       "class, never a verdict."),
        "pass": identical,
    }


def arm_CORPUS():
    """DESCRIPTIVE. The size of the promoted class and of the undecidable residual."""
    promoted, residual, same_key = [], [], 0
    for path in sorted(glob.glob(os.path.join(SEEDS, "*.json"))):
        try:
            seed = json.load(open(path))
        except Exception:
            continue
        if not isinstance(seed, dict):
            continue
        for r in seed.get("rules", []) or []:
            for node, _p, _d, scope in walk_terms_scoped(r, scope_from_match(r)):
                if node.get("type") not in ("Lt", "Lte", "Gt", "Gte"):
                    continue
                a, b = node.get("a"), node.get("b")
                if not (isinstance(a, dict) and a.get("type") == "Attr"
                        and isinstance(b, dict) and b.get("type") == "Attr"):
                    continue
                rec = {"seed": os.path.basename(path), "rule": r.get("name"),
                       "op": node["type"]}
                if is_codebook_crossing(node, scope):
                    promoted.append(rec)
                else:
                    residual.append(rec)
                    ka = a.get("key") or a.get("name")
                    kb = b.get("key") or b.get("name")
                    if ka == kb:
                        same_key += 1
    from collections import Counter
    return {
        "n_attr_vs_attr_total": len(promoted) + len(residual),
        "n_promoted_by_T2": len(promoted),
        "n_undecidable_residual": len(residual),
        "n_residual_same_key": same_key,
        "promoted_by_seed": dict(Counter(p["seed"] for p in promoted)),
        "promoted_by_rule": dict(Counter(f"{p['seed']}::{p['rule']}" for p in promoted)),
        "note": ("`n_residual_same_key` is counted INSIDE the residual, not excluded "
                 "from it: same-key is a MEASURED heuristic for non-bound on this "
                 "corpus, NOT a proof (a threshold stored under the same attribute name "
                 "on a params node would be a same-key bound). Keeping it inside keeps "
                 "the reported range HONEST rather than flatteringly tight."),
    }


def arm_KNOWN_FALSE_NEGATIVE():
    """DESCRIPTIVE — the declared cost of the tight `NodesOfType` reading of 'codebook'.

    Reported because the prereg promised BOTH costs, not just the flattering one.
    """
    path = os.path.join(SEEDS, "topic_search_verify.json")
    if not os.path.exists(path):
        return {"present": False}
    seed = json.load(open(path))
    hits = []
    for r in seed.get("rules", []) or []:
        for node, _p, _d, scope in walk_terms_scoped(r, scope_from_match(r)):
            if node.get("type") not in ("Lt", "Lte", "Gt", "Gte"):
                continue
            a, b = node.get("a"), node.get("b")
            if not (isinstance(a, dict) and a.get("type") == "Attr"
                    and isinstance(b, dict) and b.get("type") == "Attr"):
                continue
            ka, kb = a.get("key") or a.get("name"), b.get("key") or b.get("name")
            if {ka, kb} == {"overlap_ratio", "min_overlap"}:
                hits.append({"rule": r.get("name"), "keys": [ka, kb],
                             "T2": is_codebook_crossing(node, scope)})
    return {
        "present": True, "hits": hits,
        "missed_by_T2": all(not h["T2"] for h in hits) and bool(hits),
        "why": ("a GENUINE bound (`overlap_ratio` vs `min_overlap`) whose candidate is "
                "quantified over `InNeighbours`, not `NodesOfType`. The tight reading "
                "of 'codebook' costs this false negative; the loose reading (rival R5) "
                "costs 3 tick-guard false positives. Both costs measured, neither hidden."),
    }


def main():
    t0 = time.time()
    out = {
        "rung": "AST ATTR-THRESHOLD (T2 codebook-crossing)",
        "prereg": "VISION_AST_ATTR_PREREG.md @ bfc1eef5",
        "base_main_HEAD": "fc638821",
        "seeds_consumed": 0,
        "seeds_allocated": "53000-53999 (UNCONSUMED — static analysis evaluates no Term)",
        "HEADLINE": arm_HEADLINE(),
        "CONJUNCTION": arm_CONJUNCTION(),
        "EVADE": arm_EVADE(),
        "TABLE": arm_TABLE(),
        "DERIVED_NEGATIVE": arm_DERIVED_NEGATIVE(),
        "CORPUS": arm_CORPUS(),
        "KNOWN_FALSE_NEGATIVE": arm_KNOWN_FALSE_NEGATIVE(),
    }
    out["elapsed_s"] = round(time.time() - t0, 3)
    try:
        out["provenance"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        out["provenance"] = "<unavailable>"
    dest = os.path.join(ROOT, "results", "ast_attr.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    for arm in ("HEADLINE", "CONJUNCTION", "EVADE", "TABLE", "DERIVED_NEGATIVE"):
        print(f"  {arm:18s} pass={out[arm].get('pass')}")
    print(f"  CORPUS   promoted={out['CORPUS']['n_promoted_by_T2']} "
          f"residual={out['CORPUS']['n_undecidable_residual']}")
    print(f"-> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
