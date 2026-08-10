#!/usr/bin/env python
"""arc6_tier0_report — assemble `results/arc6_tier0.json` from the three
measured arms plus the LIVE witness sweeps.

Mechanical only: it reads the three battery snapshots
(`results/arc6_tier0_{before,armB_rebuild,after}.json`), re-runs every
witness sweep LIVE against the current engine, and writes one artifact.
No synthesis, engine, seed or spec code is touched.

THE THREE ARMS, because this intervention includes an engine change and a
rebuild alone has already silently moved results once in this project
(34 -> 32, `PROGRAM_SYNTHESIS_ARC5_FINAL.md`):

  A  committed .rs  + engine 5c1b472f  (the arc-5 baseline binary)
  B  committed .rs  + a FRESH rebuild  (isolates the rebuild alone)
  C  tier-0 .rs     + its build        (the result)

Only C - B may be claimed.  B is bit-identical to A here (the build is
reproducible), which is recorded as the measurement it is, not assumed.

Run:
  OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python scripts/arc6_tier0_report.py
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains.engine_provenance import engine_preamble, provenance_stamp  # noqa: E402
engine_preamble()

import substrate_rs as srs  # noqa: E402

SUB = srs.Substrate()
B0_IDS = [18, 75, 98, 106, 161, 257, 290, 310, 424, 450]
STRICT_IDS = [75, 98, 106, 161, 257, 290]
ARC5_FINAL = os.path.join(ROOT, "results", "arc5_final.json")
OUT = os.path.join(ROOT, "results", "arc6_tier0.json")


def ev(term, env=None):
    try:
        return "ok", SUB._inner.evaluate(term, env or {})
    except Exception as exc:  # noqa: BLE001 -- the error text IS the evidence
        return "refused", "%s: %s" % (type(exc).__name__, exc)


def L(v):
    return {"type": "Lit", "value": v}


def V(n):
    return {"type": "Var", "name": n}


def wilson(k, n):
    if n == 0:
        return {"k": k, "n": n, "p": None, "ci95": None}
    z, p = 1.959963984540054, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {"k": k, "n": n, "p": round(p, 6),
            "ci95": [round(max(0.0, c - h), 6), round(min(1.0, c + h), 6)]}


def snap(label):
    with open(os.path.join(ROOT, "results", "arc6_tier0_%s.json" % label)) as f:
        return json.load(f)


# --------------------------------------------------------------------------
# The unit probes -- LIVE, because an unknown op name is a SILENT NO-OP and a
# misspelling would read as an honest null.
# --------------------------------------------------------------------------
def unit_probes():
    out = {}

    # --- fix:StringAsSequence: the four shipped Terms, both directions.
    fixes = [
        ("Count(str)", {"type": "Count", "source": L("abc")}, 3, 0),
        ("Count(list) unchanged", {"type": "Count", "source": L([1, 2, 3])}, 3, 3),
        ("IndexAt(str,1)", {"type": "IndexAt", "seq": L("abc"), "index": L(1)}, "b", None),
        ("IndexAt(str,-1)", {"type": "IndexAt", "seq": L("abc"), "index": L(-1)}, "c", None),
        ("IndexAt(str,9) out of range", {"type": "IndexAt", "seq": L("abc"), "index": L(9)}, None, None),
        ("Last(str)", {"type": "Last", "seq": L("abc")}, "c", None),
        ("Last(list) unchanged", {"type": "Last", "seq": L([7, 8])}, 8, 8),
        ("In(char,str)", {"type": "In", "member": L("a"), "container": L("cat")}, True, False),
        ("In(substr,str)", {"type": "In", "member": L("at"), "container": L("cat")}, True, False),
        ("In(absent,str)", {"type": "In", "member": L("z"), "container": L("cat")}, False, False),
        ("In(elem,list) unchanged", {"type": "In", "member": L(1), "container": L([1, 2])}, True, True),
        ("In(int,str) unchanged", {"type": "In", "member": L(1), "container": L("cat")}, False, False),
    ]
    rows = []
    for name, term, want, was in fixes:
        st, got = ev(term)
        rows.append({"probe": name, "status": st, "got": got,
                     "expected_now": want, "was_before_tier0": was,
                     "fires": st == "ok" and got == want})
    out["fix:StringAsSequence"] = {
        "fires": all(r["fires"] for r in rows), "probes": rows}

    # --- the four ops + three templates, each solved LIVE from a spec.
    def synth(spec_rows, ops=None, max_size=9):
        spec = {"type": "SynthEnumerate", "examples": L(spec_rows),
                "max_size": max_size, "max_candidates": 0,
                "saturate_k": 0, "field": ""}
        if ops is not None:
            spec["ops"] = L(ops)
        st, v = ev(spec)
        return v if st == "ok" else {"found": False, "halt_reason": st}

    def types_of(term_str):
        acc = set()

        def walk(o):
            if isinstance(o, dict):
                if "type" in o:
                    acc.add(o["type"])
                for x in o.values():
                    walk(x)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(json.loads(term_str))
        return sorted(acc)

    cases = [
        ("op:TupleOf", None, ["Vec"],
         [{"inputs": {"a": 10, "b": 20}, "output": (20, 10)},
          {"inputs": {"a": 15, "b": 17}, "output": (17, 15)},
          {"inputs": {"a": 1, "b": 2}, "output": (2, 1)},
          {"inputs": {"a": -4, "b": 6}, "output": (6, -4)}]),
        ("op:ProdList", ["ProdList"], ["Prod"],
         [{"inputs": {"a": [1, 2, 3]}, "output": 6},
          {"inputs": {"a": [2, 2, 2, 2]}, "output": 16},
          {"inputs": {"a": [3, 5]}, "output": 15},
          {"inputs": {"a": [7]}, "output": 7}]),
        ("op:ConcatList", None, ["Fold", "Append"],
         [{"inputs": {"a": [1, 2], "b": [3]}, "output": (1, 2, 3)},
          {"inputs": {"a": [9], "b": [8, 7]}, "output": (9, 8, 7)},
          {"inputs": {"a": [4, 4], "b": [5, 5]}, "output": (4, 4, 5, 5)},
          {"inputs": {"a": [], "b": [1]}, "output": (1,)}]),
        # Tie rows: `MaxList` on tuples is ALREADY max-by-length (cmp_value
        # orders tuples by length first), so only a tie separates the two.
        ("op:ArgMaxLenOver", ["ArgMaxLenOver"], ["Argmax", "Count"],
         [{"inputs": {"a": [[1, 9], [2, 0]]}, "output": (1, 9)},
          {"inputs": {"a": [[1, 1], [9, 9], [0]]}, "output": (1, 1)},
          {"inputs": {"a": [[2, 2], [4, 4], [7]]}, "output": (2, 2)}]),
        ("tmpl:item_in_listvar", None, ["FilterList", "In", "Not"],
         [{"inputs": {"a": [1, 2, 3, 4], "b": [2, 4]}, "output": (1, 3)},
          {"inputs": {"a": [5, 6], "b": [6]}, "output": (5,)},
          {"inputs": {"a": [7, 8, 9], "b": [7, 9]}, "output": (8,)},
          {"inputs": {"a": [1, 2], "b": []}, "output": (1, 2)}]),
        ("tmpl:len_item_vs_var", None, ["FilterList", "Count"],
         [{"inputs": {"a": ["ab", "cde", "fg"], "b": 2}, "output": ("ab", "fg")},
          {"inputs": {"a": ["x", "yz", "w"], "b": 1}, "output": ("x", "w")},
          {"inputs": {"a": ["abc", "de"], "b": 3}, "output": ("abc",)},
          {"inputs": {"a": ["pq", "rs"], "b": 5}, "output": ()}]),
        ("tmpl:nested_reduction", None, ["FilterList", "MaxOver"],
         [{"inputs": {"a": [[1, 2], [9, 1], [3]], "b": 3}, "output": ((1, 2), (3,))},
          {"inputs": {"a": [[5], [1, 1]], "b": 2}, "output": ((1, 1),)},
          {"inputs": {"a": [[2, 2], [4]], "b": 2}, "output": ((2, 2),)},
          {"inputs": {"a": [[8]], "b": 1}, "output": ()}]),
    ]
    for unit, ops, want_types, spec_rows in cases:
        r = synth(spec_rows, ops)
        ts = types_of(r["term"]) if r.get("found") else []
        out[unit] = {
            "fires": bool(r.get("found")) and set(want_types) <= set(ts),
            "ops_declared": ops, "n_rows_swept": len(spec_rows),
            "found": bool(r.get("found")), "size": r.get("size"),
            "halt_reason": r.get("halt_reason"),
            "term_str": r.get("term_str"), "term_types": ts,
            "required_term_types": want_types,
        }
    return out


# --------------------------------------------------------------------------
# The per-candidate LIVE pipeline read: what the enumerator PROPOSED, what
# ProgEval COMPUTED, and where the verdict landed.
# --------------------------------------------------------------------------
def candidate_trace():
    import mbpp_arc3_battery as arc3b
    from domains import prog_synthesis as psy
    from domains import mbpp_spec as ms
    with open(os.path.join(ROOT, "tests", "fixtures", "mbpp",
                           "sanitized-mbpp.json")) as f:
        tasks = json.load(f)
    by = {t["task_id"]: t for t in arc3b.q0_split_tasks(tasks)["test"]}
    out = {}
    for tid in B0_IDS:
        t = by[tid]
        parsed = ms.parse_asserts(t)
        revealed = ms.split_rows(parsed["rows"], "primary")["revealed"]
        s, ag = arc3b.boot_full_r3()
        try:
            r = psy.synthesize_from_request(s, ag, t["prompt"], revealed)
        except Exception as exc:  # noqa: BLE001
            out[str(tid)] = {"pipeline_exception": "%s: %s" % (type(exc).__name__, exc)}
            continue
        rec = {"status": r.get("status"), "gap_reason": r.get("gap_reason"),
               "enumerate_outcome": r.get("enumerate_outcome"),
               "proposed_term_str": None, "rows": []}
        for g in s.nodes("Goal"):
            at = s.node(g)["attrs"]
            if at.get("kind") != "synth_program":
                continue
            note = at.get("ps_enumerate_note")
            if note and rec["proposed_term_str"] is None:
                rec["proposed_term_str"] = str(note)
            for m in s.neighbours(g, "about_message"):
                for row in s.neighbours(m, "has_example"):
                    ra = s.node(row)["attrs"]
                    rec["rows"].append({
                        "expected": repr(ra.get("expected"))[:120],
                        "expected_type": type(ra.get("expected")).__name__,
                        "progeval_result_json": str(ra.get("got_json"))[:120],
                        "eval_ok": ra.get("eval_ok"),
                        "cmp_ok": ra.get("cmp_ok"),
                        "row_verdict": ra.get("ps_verdict"),
                        "got_attr_is_none": ra.get("got") is None,
                    })
            break
        out[str(tid)] = rec
    return out


# --------------------------------------------------------------------------
# The constructed-witness sweep for every AGGREGATE change, including the
# refuting direction.  Seven coincidental fits are on this project's record.
# --------------------------------------------------------------------------
def gained_id_sweeps():
    """Task 120 is the ONLY id the aggregate gained.  It is swept here on
    CONSTRUCTED inputs (never held-out rows) against the task's own stated
    meaning, and it is REFUTED."""
    term = {"type": "Max", "items": [
        L(36),
        {"type": "Prod",
         "source": {"type": "IndexAt", "seq": V("a"), "index": L(0)},
         "var_name": "__item", "value": V("__item")}]}
    sweeps = [[[2, 7], [2, 6], [1, 8], [4, 9]], [[10, 20], [15, 2], [5, 10]],
              [[1, 1], [1, 1]], [[3, 3], [100, 100]],
              [[2, 2], [5, 5], [1, 1]], [[0, 5], [7, 7]]]
    rows = []
    for a in sweeps:
        st, got = ev(term, {"a": a})
        truth = max(x * y for x, y in a)
        rows.append({"input": a, "got": got, "task_meaning_says": truth,
                     "match": st == "ok" and got == truth})
    return {"120": {
        "accepted_term_str": "max(36, prod(__item for __item in a[0]))",
        "verdict": "COINCIDENTAL FIT -- NOT COUNTED AS A CONVERSION",
        "why": ("the term hard-codes 36 (an auto-appended spec-output "
                "constant) and reads only a[0]; it fits every revealed AND "
                "held-out row of this task by accident and is wrong in "
                "general"),
        "n_constructed_inputs": len(sweeps),
        "n_matching": sum(1 for r in rows if r["match"]),
        "rows": rows}}


def main():
    a, b, c = snap("before"), snap("armB_rebuild"), snap("after")
    A, B, C = (set(x["pass_ids"]) for x in (a, b, c))
    with open(ARC5_FINAL) as f:
        frozen = set(json.load(f)["arm"]["outcome_taxonomy"]["pass"]["task_ids"])

    ia = {t: k for k, v in a["outcome_taxonomy"].items() for t in v["task_ids"]}
    ic = {t: k for k, v in c["outcome_taxonomy"].items() for t in v["task_ids"]}

    probes = unit_probes()
    trace = candidate_trace()
    sweeps = gained_id_sweeps()

    genuine = sorted(t for t in (C - A)
                     if sweeps.get(str(t), {}).get("verdict", "").startswith("COINC") is False)
    converted_b0 = sorted(set(genuine) & set(B0_IDS))

    rec = {
        "_README": (
            "ARC 6 TIER 0 -- the SynthEnumerate op-table widening.  PAIRED "
            "ID LISTS, never a bare count.  THE AGGREGATE IS UNDERPOWERED "
            "BY CONSTRUCTION: 35/257 -> 36/257 sits well inside the "
            "baseline Wilson CI [9.96, 18.35]; the result is the id list "
            "plus witnesses, not the score.  The one id the aggregate "
            "gained (120) is a CONSTRUCTED-WITNESS-REFUTED coincidental "
            "fit and is NOT claimed."),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "head": subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                               capture_output=True, text=True).stdout.strip(),
        "engine_provenance_now": provenance_stamp(),
        "arms": {
            "_why_three": (
                "this intervention INCLUDES an engine change, and an engine "
                "rebuild alone has already silently moved MBPP results in "
                "this project (34 -> 32, with no seed or Python change).  "
                "Arm B isolates the rebuild so that C - B, not C - A, is "
                "what tier 0 may claim."),
            "A_baseline_code_baseline_engine": {
                "engine_sha256": a["engine_provenance"]["sha256"],
                "pass_ids": sorted(A), "n": len(A),
                "outcome_hash": a["determinism"]["outcome_hash_run1"],
                "twin_run_identical": a["determinism"]["identical"],
                "reproduces_frozen_arc5_final": sorted(A) == sorted(frozen)},
            "B_baseline_code_rebuilt_engine": {
                "engine_sha256": b["engine_provenance"]["sha256"],
                "pass_ids": sorted(B), "n": len(B),
                "outcome_hash": b["determinism"]["outcome_hash_run1"],
                "twin_run_identical": b["determinism"]["identical"]},
            "C_tier0_code_tier0_engine": {
                "engine_sha256": c["engine_provenance"]["sha256"],
                "pass_ids": sorted(C), "n": len(C),
                "outcome_hash": c["determinism"]["outcome_hash_run1"],
                "twin_run_identical": c["determinism"]["identical"]},
            "B_minus_A": {"gained": sorted(B - A), "lost": sorted(A - B),
                          "engine_bit_identical": (
                              a["engine_provenance"]["sha256"]
                              == b["engine_provenance"]["sha256"]),
                          "reading": ("the rebuild is bit-reproducible and "
                                      "contributes EXACTLY ZERO; C - B == C - A")},
            "C_minus_B": {"gained": sorted(C - B), "lost": sorted(B - C)},
        },
        "candidate_population": {
            "b0_ids": B0_IDS,
            "strict_witness_and_in_budget_ids": STRICT_IDS,
            "outcome_before": {str(t): ia.get(t) for t in B0_IDS},
            "outcome_after": {str(t): ic.get(t) for t in B0_IDS},
            "moved_off_enumerate_failed": sorted(
                t for t in B0_IDS
                if ia.get(t) == "gapped:enumerate_failed"
                and ic.get(t) != "gapped:enumerate_failed"),
            "converted": converted_b0,
        },
        "unit_attribution": probes,
        "candidate_pipeline_trace": trace,
        "gained_id_witness_sweeps": sweeps,
        "aggregate": {
            "before": wilson(len(A), a["n_runnable"]),
            "after": wilson(len(C), c["n_runnable"]),
            "caveat": ("UNDERPOWERED BY CONSTRUCTION -- the after point "
                       "estimate lies inside the before CI.  Report the id "
                       "list and the witnesses; the score is not a detection."),
        },
        "hs_verdicts": {
            "HS1_primary_ge_3_of_10_convert": {
                "bar": ">=3 of the 10 B0 ids convert, paired-id exact, each "
                       "with a constructed witness, zero coincidental fits",
                "converted_b0_ids": converted_b0,
                "verdict": "PASS" if len(converted_b0) >= 3 else "FAIL"},
            "HS2_soundness_no_regression": {
                "bar": "the after pass-list must be a SUPERSET of the 35 in "
                       "results/arc5_final.json",
                "frozen_35": sorted(frozen),
                "after": sorted(C),
                "missing_from_after": sorted(frozen - C),
                "verdict": "PASS" if frozen <= C else "FAIL"},
            "HS3_cost_zero_new_termnode_variants": {
                "bar": "zero new TermNode variants",
                "files_changed": ["runners/dsl/src/term.rs",
                                  "runners/dsl/src/synth_enumerate.rs"],
                "gate": "tests/test_arc6_tier0_migrated.py::test_hs3_no_new_termnode_variants",
                "verdict": "PASS"},
            "HS4_op_table_is_task_independent": {
                "bar": "the shipped op table must diff EMPTY against one "
                       "written from the operator list alone",
                "op_names_added": ["TupleOf", "ProdList", "ConcatList",
                                   "ArgMaxLenOver"],
                "unit_list_source": "PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md sec 9",
                "gate": "tests/test_arc6_tier0_migrated.py::test_hs4_op_table_is_the_unit_list_and_nothing_else",
                "verdict": "PASS"},
        },
        "contamination": {
            "held_out_rows_never_read": True,
            "note": ("every unit probe is a CONSTRUCTED spec written from "
                     "the operator list; the per-candidate trace uses "
                     "split_rows(...)['revealed'] only, through the "
                     "unchanged pipeline; test-split `code` was read for "
                     "MEASUREMENT classification only and entered no "
                     "codebook, cue vocabulary or taught shape"),
        },
    }
    with open(OUT, "w") as f:
        json.dump(rec, f, indent=2, sort_keys=True, default=str)
    print("wrote", OUT)
    for k, v in rec["hs_verdicts"].items():
        print("  %-46s %s" % (k, v["verdict"]))
    print("  C - B gained:", rec["arms"]["C_minus_B"]["gained"],
          " lost:", rec["arms"]["C_minus_B"]["lost"])
    print("  units firing:",
          sorted(k for k, v in probes.items() if v.get("fires")))
    print("  units NOT firing:",
          sorted(k for k, v in probes.items() if not v.get("fires")))


if __name__ == "__main__":
    main()
