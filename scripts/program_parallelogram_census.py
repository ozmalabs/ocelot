#!/usr/bin/env python
"""program_parallelogram_census — OFFLINE CENSUS ONLY.

First slice of PROPOSAL 2 ("program-parallelogram") from
`docs/research/engine_substrate/DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md`
§3: *"First slice: OFFLINE — run the anti-unifier over the existing
accepted-Program corpus and count parallelograms with support >= 2 ...
zero agent wiring until that census says the population is real."*

This script does exactly that and NOTHING else:

  - reads the already-measured MBPP endgame battery artifact
    (`results/mbpp_endgame.json`, produced by
    `scripts/mbpp_endgame_battery.py`, UNCHANGED) — no new synthesis run,
    no engine change, no seed change;
  - groups accepted Program-IR trees (`row["ir"]`, the `domains.prog_
    synthesis.synthesize_from_request` output already captured by the
    battery) by exact structural skeleton (type tags + key sets + list
    lengths, leaf VALUES free) — the same "group by exact tree skeleton
    first" discipline `scratch_rr/rr4_find_parallelogram.py` used at the
    RULE grain (`docs/research/engine_substrate/RULE_REFERENCE_LAYER_
    SIZING_RESULTS.md` §4.2), applied here at the Program-IR grain;
  - for every skeleton family with >= 2 distinct accepted tasks, calls the
    real, shipped `AntiUnifyWitness`/`Substitute` Terms (`runners/dsl/src/
    term.rs:1036,3758` in this worktree, confirmed unchanged from the
    design doc's citation) via `substrate_rs`'s generic `evaluate()` --
    the SAME Python-callable pattern `scratch_rr/rr1_covers_witness_
    probe.py`/`rr4_transfer_at_scale.py` already established -- to
    recover the shared template, the per-task witnesses, and verify the
    round-trip (`Substitute(template, sigma_i) == member_i`) natively;
  - separately runs a clearly-labeled SYNTHETIC probe over the two
    hand-verified-but-NOT-currently-solved clusters (task 102/411,
    137/442) from `docs/research/program_synthesis/PROGRAM_SYNTHESIS_
    CEILING_REASSESSMENT_7_PREREG.md` §4 -- their term-trees are quoted
    from that document, NOT re-derived, and are never merged into the
    real-corpus counts;
  - writes ONE JSON artifact (`results/program_parallelogram_census.json`)
    and prints a summary. Mints nothing, wires nothing, touches no seed,
    no graph, no live agent path.

Run:
    PYTHONPATH=runners/dsl/python:. python3 scripts/program_parallelogram_census.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402

RESULTS_PATH = os.path.join(HERE, "results", "mbpp_endgame.json")
OUT_PATH = os.path.join(HERE, "results", "program_parallelogram_census.json")

WILD = "·?·"  # the `wild` Term FIELD name (Sym), as in scratch_rr/*.py
_S = srs.Substrate()
_N = _S._inner  # raw native handle -- takes term-JSON dicts directly


# --------------------------------------------------------------------------- #
#  The Rust anti-unification algebra -- the exact Python-callable pattern
#  scratch_rr/rr1_covers_witness_probe.py and scratch_rr/rr4_transfer_at_
#  scale.py already established for the RULE grain, reused verbatim here.
# --------------------------------------------------------------------------- #
def ev(term: Dict[str, Any]) -> Any:
    return _N.evaluate(term, {})


def lit(v: Any) -> Dict[str, Any]:
    return {"type": "Lit", "value": v}


def idx(seq: Dict[str, Any], i: int) -> Dict[str, Any]:
    return {"type": "IndexAt", "seq": seq, "index": lit(i)}


def auw_term(vals: List[Any]) -> Dict[str, Any]:
    return {"type": "AntiUnifyWitness", "values": lit(tuple(vals)), "wild": WILD}


def anti_unify_witness(vals: List[Any]) -> Tuple[Any, Tuple[Dict[Tuple, Any], ...]]:
    """Real `AntiUnifyWitness` call, N-ary (not just pairs -- `values` is a
    collection of 2+ Values, per `term.rs:1027-1036`'s own doc comment).
    Returns `(template, sigmas)`, `sigmas` a tuple of one {path_tuple: value}
    dict per input -- verified live in this worktree that tuple-keyed dicts
    survive the Rust->Python RETURN direction fine (only the reverse,
    Python->Rust term-JSON INPUT, cannot encode a tuple-keyed dict, per
    RULE_REFERENCE_LAYER_SIZING_RESULTS.md §7.2's "native.evaluate cannot
    carry a sigma" finding -- which is about feeding a sigma back IN, not
    about reading one back OUT)."""
    return ev(auw_term(vals))


def _values_equal(a: Any, b: Any) -> bool:
    """Structural equality that treats Python `list` and `tuple` as the SAME
    shape. Required because `anti_unify_witness_values`'s Tuple/List arm
    (`term.rs:3801-3815`) always reconstructs `Value::Tuple(...)` regardless
    of whether the ORIGINAL inputs were `Value::List` or `Value::Tuple`
    (`return Value::Tuple(Arc::new(out));`, unconditional) -- so a
    `Substitute`d program whose IR used JSON arrays (Python `list`, ->
    `Value::List` on the way in) comes back as Python `tuple` at every
    position the algebra touched. This is a genuine, newly-observed quirk
    of the anti-unify ALGEBRA's own reconstruction (it does not preserve
    List-vs-Tuple identity through a round trip), not an information-loss
    bug in the template/witness split itself -- confirmed by hand (the
    JSON-serialized content is byte-identical; only the Python container
    TYPE differs) and NOT the same defect class as RULE_REFERENCE_LAYER_
    SIZING_RESULTS.md's "Encoding C" residual-loss (that one drops content;
    this one only relabels a container type). A strict Python `==` would
    misreport every List-bearing program as "lossy"; this function is the
    honest, documented tolerance for that one quirk -- everything else
    (keys, values, order, counts) is still compared exactly."""
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(_values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_values_equal(a[k], b[k]) for k in a)
    return a == b


def verify_lossless(vals: List[Any]) -> List[bool]:
    """`Substitute(template, sigma_i) == vals[i]` for every i -- template and
    sigma recovered via ONE native `AntiUnifyWitness`+`Substitute` term-tree
    per instance (the `roundtrip()` precedent in `scratch_rr/rr1_covers_
    witness_probe.py:61-75`, since a sigma with tuple-path keys cannot cross
    the wire as fresh Python->Rust input), then compared in Python with
    `_values_equal` (list/tuple-tolerant; see its docstring)."""
    at = auw_term(vals)
    out = []
    for i, v in enumerate(vals):
        expr = {"type": "Substitute", "template": idx(at, 0),
                "sigma": idx(idx(at, 1), i), "wild": WILD}
        reconstructed = ev(expr)
        out.append(_values_equal(reconstructed, v))
    return out


# --------------------------------------------------------------------------- #
#  Structural skeleton grouping -- "group by exact tree skeleton first" is
#  the RULE_REFERENCE_LAYER precedent (rr4_find_parallelogram.py's own
#  `skeleton()`), extended here to force TYPE-TAG equality at every level
#  (a bare structural skeleton would let e.g. `Plus{a,b}` and `Minus{a,b}`
#  collapse into one family with the op name itself as a "hole" -- not
#  meaningful, since a Call{name,...} dispatch needs a CONCRETE op name).
#  `AntiUnifyWitness`'s Dict arm only generalises over SHARED keys and
#  silently DROPS non-shared keys from both template and residual (the
#  "Encoding C" pitfall RULE_REFERENCE_LAYER_SIZING_RESULTS.md §1.1 found
#  and rejected) -- so an exact-skeleton precondition is not a convenience,
#  it is what keeps every reported "hole" a genuine leaf substitution
#  instead of a silently-lossy key omission.
# --------------------------------------------------------------------------- #
def skeleton(n: Any):
    if isinstance(n, dict):
        if "type" in n:
            other_keys = tuple(sorted(k for k in n if k != "type"))
            return ("D", n["type"], other_keys,
                     tuple(skeleton(n[k]) for k in other_keys))
        return ("Dn", tuple(sorted((k, skeleton(v)) for k, v in n.items())))
    if isinstance(n, list):
        return ("L", tuple(skeleton(x) for x in n))
    return ("_",)


def kind_of(v: Any) -> str:
    if isinstance(v, (list, tuple)):
        return "list"
    if isinstance(v, dict):
        return "dict"
    return "scalar"


def is_single_expr_template(ir: Dict[str, Any]) -> bool:
    """The ONLY shape that resembles the derived_ops design's target grain
    (`DERIVED_OPERATOR_TIER_RESULTS.md` §3: a single Term-tree, holes as
    `Var(<param>)` children of one op) -- `ProgSeq{ProgDefFnParam*,
    ProgReturn{value: <one Term>}}`, nothing else in the statement list."""
    if not isinstance(ir, dict) or ir.get("type") != "ProgSeq":
        return False
    stmts = ir.get("stmts") or []
    if not stmts or stmts[-1].get("type") != "ProgReturn":
        return False
    return all(s.get("type") in ("ProgDefFnParam", "ProgReturn") for s in stmts)


# --------------------------------------------------------------------------- #
#  Corpus loading
# --------------------------------------------------------------------------- #
def load_arm_rows(results_path: str, arm: str) -> List[Dict[str, Any]]:
    with open(results_path) as fh:
        d = json.load(fh)
    return d["arms"][arm]["runnable_rows"], d.get("head"), d.get("measured_at")


def corpus_entries(rows: List[Dict[str, Any]], outcomes) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        if r.get("outcome") in outcomes and r.get("ir") is not None:
            out.append({
                "task_id": r["task_id"],
                "outcome": r["outcome"],
                "construction": r.get("construction"),
                "prompt": r.get("prompt"),
                "ir": r["ir"],
            })
    return out


def group_families(entries: List[Dict[str, Any]]):
    fams = defaultdict(list)
    for e in entries:
        fams[skeleton(e["ir"])].append(e)
    return fams


# --------------------------------------------------------------------------- #
#  Family analysis
# --------------------------------------------------------------------------- #
def analyze_family(members: List[Dict[str, Any]]) -> Dict[str, Any]:
    irs = [m["ir"] for m in members]
    try:
        template, sigmas = anti_unify_witness(irs)
    except Exception as e:  # noqa: BLE001 -- report, never crash the census
        return {"error": "%s: %s" % (type(e).__name__, e)}

    all_paths = set()
    for s in sigmas:
        all_paths.update(s.keys())

    hole_kinds = {}
    for p in all_paths:
        kinds = sorted({kind_of(s[p]) for s in sigmas if p in s})
        hole_kinds[".".join(str(x) for x in p)] = kinds

    try:
        lossless = verify_lossless(irs)
    except Exception as e:  # noqa: BLE001
        lossless = ["error: %s: %s" % (type(e).__name__, e)]

    single_expr = [is_single_expr_template(ir) for ir in irs]
    constructions = Counter(m.get("construction") for m in members)

    return {
        "task_ids": [m["task_id"] for m in members],
        "support": len(members),
        "n_holes": len(all_paths),
        "hole_paths": sorted(hole_kinds.keys()),
        "hole_kinds": hole_kinds,
        "all_holes_scalar_or_list": all(
            set(k) <= {"scalar", "list"} for k in hole_kinds.values()
        ) if hole_kinds else True,
        "lossless": lossless,
        "all_lossless": all(x is True for x in lossless),
        "all_single_expr_template": all(single_expr),
        "any_single_expr_template": any(single_expr),
        "constructions": dict(constructions),
    }


def census_over(entries: List[Dict[str, Any]], label: str) -> Dict[str, Any]:
    fams = group_families(entries)
    multi = {k: v for k, v in fams.items() if len(v) >= 2}
    families_out = []
    for members in multi.values():
        a = analyze_family(members)
        a["label"] = label
        families_out.append(a)

    zero_hole = [f for f in families_out if f.get("n_holes") == 0]
    real = [f for f in families_out if f.get("n_holes", 0) > 0 and "error" not in f]
    errored = [f for f in families_out if "error" in f]

    return {
        "label": label,
        "n_entries": len(entries),
        "n_families_total": len(fams),
        "n_families_size1": sum(1 for v in fams.values() if len(v) == 1),
        "n_families_support_ge2": len(multi),
        "n_families_zero_hole_duplicate": len(zero_hole),
        "n_families_errored": len(errored),
        "n_families_real_parallelogram": len(real),
        "families": families_out,
    }


# --------------------------------------------------------------------------- #
#  SYNTHETIC probe -- the two hand-verified, NOT-currently-solved clusters
#  from PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_7_PREREG.md §4. Quoted from
#  that document verbatim (its own §4.1/§4.2 term description), never
#  merged into the real-corpus counts above.
# --------------------------------------------------------------------------- #
def _var(name):
    return {"type": "Var", "name": name}


def cluster_102_411_ir():
    # Fold(MapList(Split(a,"_"), item, Capitalize(item)),
    #      item2, acc, init="", body=StringConcat(acc,item2))
    split_a = {"type": "Split", "text": _var("a"), "sep": lit("_")}
    maplist = {"type": "MapList", "source": split_a, "var_name": "item",
               "value": {"type": "Capitalize", "text": _var("item")}}
    fold = {"type": "Fold", "source": maplist, "var_name": "item2",
            "acc_name": "acc", "init": lit(""),
            "body": {"type": "StringConcat", "parts": [_var("acc"), _var("item2")]}}
    return {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": fold},
    ]}


def cluster_137_ir():
    # Div(Count(FilterList(a,item,Eq(item,0))),
    #     Minus(Count(a), Count(FilterList(a,item,Eq(item,0)))))
    filt = {"type": "FilterList", "source": _var("a"), "var_name": "item",
            "predicate": {"type": "Eq", "a": _var("item"), "b": lit(0)}}
    count_filt = {"type": "Count", "source": filt}
    count_a = {"type": "Count", "source": _var("a")}
    minus = {"type": "Minus", "a": count_a, "b": count_filt}
    div = {"type": "Div", "a": count_filt, "b": minus}
    return {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": div},
    ]}


def cluster_442_ir():
    # Round(Div(Count(FilterList(a,item,Gt(item,0))),Count(a)),2)
    filt = {"type": "FilterList", "source": _var("a"), "var_name": "item",
            "predicate": {"type": "Gt", "a": _var("item"), "b": lit(0)}}
    count_filt = {"type": "Count", "source": filt}
    count_a = {"type": "Count", "source": _var("a")}
    div = {"type": "Div", "a": count_filt, "b": count_a}
    rnd = {"type": "Round", "value": div, "ndigits": lit(2)}
    return {"type": "ProgSeq", "stmts": [
        {"type": "ProgDefFnParam", "name": "a", "default": None},
        {"type": "ProgReturn", "value": rnd},
    ]}


def synthetic_probe() -> Dict[str, Any]:
    out = {}
    # Cluster 1: 102/411 share the EXACT same term-tree (same shape, same
    # ops -- the design doc's own framing: "the same program over different
    # data"). Anti-unifying two copies of literally the same tree finds a
    # zero-hole "family" -- correctly reported as a degenerate duplicate,
    # not a template-with-holes parallelogram; the real content of this
    # cluster is that ONE template solves BOTH tasks verbatim (a stronger,
    # not weaker, form of transfer than a hole-bearing template).
    ir102 = cluster_102_411_ir()
    ir411 = cluster_102_411_ir()  # same hand-verified term for both tasks
    fam1 = analyze_family([{"task_id": 102, "ir": ir102, "construction": "synthetic_hand_verified"},
                            {"task_id": 411, "ir": ir411, "construction": "synthetic_hand_verified"}])
    fam1["note"] = ("102 and 411 use the IDENTICAL hand-verified term "
                     "(per CEILING_REASSESSMENT_7 §4.1, both solved by the "
                     "SAME Fold/MapList/Split/Capitalize composition over "
                     "different data) -- zero holes is the CORRECT, "
                     "expected finding here, not a null result.")
    out["cluster_102_411"] = fam1

    ir137 = cluster_137_ir()
    ir442 = cluster_442_ir()
    skel_match = skeleton(ir137) == skeleton(ir442)
    if skel_match:
        fam2 = analyze_family([{"task_id": 137, "ir": ir137, "construction": "synthetic_hand_verified"},
                                {"task_id": 442, "ir": ir442, "construction": "synthetic_hand_verified"}])
    else:
        # DELIBERATELY do NOT run AntiUnifyWitness across a skeleton
        # mismatch: 137's core expression is `Div(Count(...), Minus(...))`
        # while 442's is `Round(Div(Count(...), Count(a)), 2)` -- their
        # top-level "value" dicts share only the "type" key. Running
        # AntiUnifyWitness anyway hits exactly the "Encoding C" pitfall
        # RULE_REFERENCE_LAYER_SIZING_RESULTS.md §1.1 found and rejected:
        # the Dict arm generalises over SHARED keys only (term.rs:3401-
        # 3404-equivalent logic at :3780-3787) and silently DROPS every
        # non-shared key from both template and residual -- it would
        # report a bogus "1 hole" (the "type" leaf) while quietly losing
        # the entire a/b vs value/ndigits substructure, and the round-trip
        # verification below would (correctly) then also fail. Measured
        # directly during this rung (see PREREG doc) before this guard was
        # added -- kept here as the honest, permanent fix, not silently
        # corrected.
        fam2 = {"support": 2, "n_holes": None, "hole_paths": None,
                "hole_kinds": None, "lossless": None,
                "all_lossless": None, "task_ids": [137, 442]}
    fam2["skeleton_matched"] = skel_match
    fam2["note"] = (
        "137 and 442 do NOT share a skeleton: 137's core expression is "
        "Div(Count(FilterList(...)), Minus(Count(a), Count(FilterList(...)))) "
        "(2-level, no rounding); 442's is Round(Div(Count(FilterList(...)), "
        "Count(a)), 2) (rounding wraps a SIMPLER Div with different "
        "denominator structure). AntiUnifyWitness was NOT run across this "
        "mismatch (see comment above) -- these two hand-verified programs "
        "would NOT trivially anti-unify into one clean template even if "
        "both were solved and entered the corpus; despite the design doc's "
        "own 0.93-prompt-similarity framing for the OTHER cluster, "
        "prompt-level similarity does not predict Program-IR skeleton "
        "similarity for THIS pair."
        if not skel_match else
        "137 and 442 share a skeleton and were anti-unified directly."
    )
    out["cluster_137_442"] = fam2
    return out


# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #
def main():
    if not os.path.exists(RESULTS_PATH):
        print("FATAL: %s not found -- run scripts/mbpp_endgame_battery.py "
              "first (see module docstring)." % RESULTS_PATH, file=sys.stderr)
        return 1

    rows_full, head, measured_at = load_arm_rows(RESULTS_PATH, "full")
    rows_stripped, _, _ = load_arm_rows(RESULTS_PATH, "content_stripped")
    rows_official, _, _ = load_arm_rows(RESULTS_PATH, "official")

    report: Dict[str, Any] = {
        "provenance": {
            "results_path": RESULTS_PATH,
            "results_head": head,
            "results_measured_at": measured_at,
        },
        "arms": {},
        "synthetic_probe": None,
    }

    # PRIMARY population: 'full' arm, pass-only (held-out-verified accepted
    # programs -- the trustworthy population).
    full_pass = corpus_entries(rows_full, {"pass"})
    report["arms"]["full_pass"] = census_over(full_pass, "full_pass")

    # SECONDARY: 'full' arm, status==accepted (pass + accepted_holdout_fail
    # -- the literal "accepted-Program corpus" per the design doc's own
    # technical vocabulary; accepted_holdout_fail programs are KNOWN to
    # include memorization artifacts, reported separately, never merged
    # into the primary count).
    full_accepted = corpus_entries(rows_full, {"pass", "accepted_holdout_fail"})
    report["arms"]["full_accepted"] = census_over(full_accepted, "full_accepted")

    # Cross-checks: content_stripped and official arms, pass-only.
    stripped_pass = corpus_entries(rows_stripped, {"pass"})
    report["arms"]["content_stripped_pass"] = census_over(stripped_pass, "content_stripped_pass")
    official_pass = corpus_entries(rows_official, {"pass"})
    report["arms"]["official_pass"] = census_over(official_pass, "official_pass")

    report["synthetic_probe"] = synthetic_probe()

    with open(OUT_PATH, "w") as fh:
        json.dump(report, fh, indent=1, sort_keys=False)

    # ------------------------------------------------------------------- #
    #  Summary print
    # ------------------------------------------------------------------- #
    print("=" * 78)
    print("PROGRAM PARALLELOGRAM CENSUS -- results/mbpp_endgame.json")
    print("  head=%s measured_at=%s" % (head, measured_at))
    print("=" * 78)
    for key in ("full_pass", "full_accepted", "content_stripped_pass", "official_pass"):
        r = report["arms"][key]
        print("\n[%s] n_entries=%d n_families_total=%d n_singleton=%d "
              "n_support>=2=%d" % (key, r["n_entries"], r["n_families_total"],
                                    r["n_families_size1"], r["n_families_support_ge2"]))
        print("  zero-hole duplicate families: %d   errored: %d   "
              "REAL parallelograms (>0 holes): %d" %
              (r["n_families_zero_hole_duplicate"], r["n_families_errored"],
               r["n_families_real_parallelogram"]))
        for f in r["families"]:
            if f.get("n_holes", 0) > 0 and "error" not in f:
                print("    tasks=%s support=%d holes=%d lossless=%s "
                      "single_expr=%s constructions=%s" %
                      (f["task_ids"], f["support"], f["n_holes"],
                       f["all_lossless"], f["all_single_expr_template"],
                       f["constructions"]))

    print("\n[synthetic_probe]")
    for k, f in report["synthetic_probe"].items():
        print("  %s: holes=%s lossless=%s note=%s" %
              (k, f.get("n_holes"), f.get("all_lossless") if "all_lossless" in f else f.get("lossless"),
               f.get("note", "")))

    print("\nWrote %s" % OUT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
