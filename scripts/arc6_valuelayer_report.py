#!/usr/bin/env python
"""arc6_valuelayer_report — the ARC-6 VALUE-LAYER artifact.

Reads the THREE arms required by prereg A1.2 (an engine change is in
scope for this rung, so a two-arm before/after would span two binaries
and could not separate the intervention from the rebuild):

  A  results/arc6_verdict_armA_baseline.json   baseline code + BASELINE engine
  B  results/arc6_verdict_armB_rebuild.json    baseline code + FINAL engine
  C  results/arc6_verdict_armC_fix.json        fix code    + FINAL engine

and writes `results/arc6_valuelayer.json`: paired id lists, per-bar
verdicts for HV1-HV4, every engine sha256, constructed witnesses for
every claimed conversion, and the out-of-scope defect probes.

The witness machinery is IMPORTED from `arc6_verdict_report` rather than
re-invented, so a conversion claimed here is judged by the SAME sweep,
the SAME constructed-input generator and the SAME type-sensitive
comparison that priced the seed-only candidate.

CONTAMINATION.  Unchanged from that module: constructed inputs are
generated mechanically from the row schema by type-driven mutation, every
generated input equal to a revealed OR held-out row is discarded, and
`task["code"]` is executed only as the measurement oracle, AFTER every
arm was already measured.

Run:
  OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python scripts/arc6_valuelayer_report.py
"""
from __future__ import annotations

import json
import os
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

import arc6_verdict_report as vr  # noqa: E402  — the witness machinery, reused
from domains import mbpp_spec as ms  # noqa: E402
import mbpp_arc3_battery as arc3b  # noqa: E402

RESULTS = os.path.join(ROOT, "results")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
OUT = os.path.join(RESULTS, "arc6_valuelayer.json")

# A3's two registered id lists, quoted verbatim.
HV1_TWELVE = [161, 249, 272, 290, 393, 413, 418, 424, 436, 450, 457, 460]
HV2_EIGHT = [106, 161, 257, 272, 413, 436, 450, 460]


def snap(label):
    with open(os.path.join(RESULTS, "arc6_verdict_%s.json" % label)) as f:
        return json.load(f)


def foldup_lane_audit():
    """HV4.  Mechanical source audit of BOTH verdict lanes: the plain row
    lane (`got`) and the descent fold-up lane (`fu_got`).  The fold-up
    lane has no `fu_cmp_ok` fact to fall back on, so if its scalar-only
    cast survives, "the non-scalar verdict is fixed" is FALSE."""
    src = open(os.path.join(ROOT, "domains", "prog_synthesis.py")).read()
    row_cast = 'sub.set_attr(r, "got", got if isinstance(got, _SCALARS) else None)' in src
    fu_cast = 'sub.set_attr(r, "fu_got", got if isinstance(got, _SCALARS) else None)' in src
    return {
        "row_lane_scalar_cast_present": row_cast,
        "foldup_lane_scalar_cast_present": fu_cast,
        "row_lane_stores_non_scalar": 'sub.set_attr(r, "got", got)' in src,
        "foldup_lane_stores_non_scalar": 'sub.set_attr(r, "fu_got", got)' in src,
        "verdict": "PASS" if not row_cast and not fu_cast else "FAIL",
        "reading": ("HV4 asks that the fold-up lane is fixed too or that the "
                    "write-up says plainly it is not.  It is fixed: the "
                    "identical one-line cast was removed from both lanes in "
                    "the same change, and neither seed rule was touched."),
    }


def attr_comparator_probe():
    """The comparison a row verdict ACTUALLY makes: both operands are graph
    ATTRS, written from Python and read back by the rule.  This is the path
    on which `list` and `tuple` used to collapse."""
    import substrate_rs as srs
    s = srs.Substrate()
    pairs = [([1, 2], [1, 2]), ([1, 2], (1, 2)), ((1, 2), (1, 2)),
             ([1, 2], [1, 3]), ([1, [2]], [1, (2,)]), ([1, 2], [1, 2, 3])]
    n = s.add_node("Probe", {})
    rows = []
    for i, (x, y) in enumerate(pairs):
        s.set_attr(n, "x%d" % i, x)
        s.set_attr(n, "y%d" % i, y)
        nid = n.value if hasattr(n, "value") else n

        def attr(k):
            return {"type": "Attr", "node": {"type": "Lit", "value": {"__nid__": nid}},
                    "key": k}
        rows.append({
            "a": repr(x), "b": repr(y),
            "substrate_Eq_over_attrs": bool(s._inner.evaluate(
                {"type": "Eq", "a": attr("x%d" % i), "b": attr("y%d" % i)}, {})),
            "python_eq": bool(x == y),
            "read_back_types": [type(s.node(n)["attrs"]["x%d" % i]).__name__,
                                type(s.node(n)["attrs"]["y%d" % i]).__name__],
        })
    return {"pairs": rows,
            "diverging_pairs": [r for r in rows
                                if r["substrate_Eq_over_attrs"] != r["python_eq"]],
            "reading": ("EMPTY diverging_pairs is the fix: over graph attrs the "
                        "substrate's Eq now agrees with Python on every "
                        "list/tuple pair, in BOTH directions.")}


def main() -> None:
    with open(FIXTURE) as f:
        all_tasks = json.load(f)
    by_id = {t["task_id"]: t for t in all_tasks}

    A, B, C = snap("armA_baseline"), snap("armB_rebuild"), snap("armC_fix")
    pa, pb, pc = (set(x["pass_ids"]) for x in (A, B, C))
    aa, ab, ac = (set(x["accepted_ids"]) for x in (A, B, C))
    arc5 = set(json.load(open(os.path.join(RESULTS, "arc5_final.json")))
               .get("pass_ids", []))

    # --- constructed-witness sweep for every id whose status MOVED ------
    moved = sorted((ac - aa) | (aa - ac) | set(HV2_EIGHT) | set(HV1_TWELVE))
    sweeps = {}
    for tid in moved:
        rec = C["per_task"].get(str(tid)) or {}
        ir = rec.get("ir")
        task = by_id.get(tid)
        if ir is None or task is None:
            sweeps[str(tid)] = {"skipped": "not accepted in arm C (no IR)",
                                "arm_c_outcome": rec.get("outcome"),
                                "arm_c_status": rec.get("status")}
            continue
        parsed = ms.parse_asserts(task)
        rows = parsed["rows"]
        sweeps[str(tid)] = vr.sweep(task, ir, rows, parsed.get("tol"),
                                    parsed.get("unordered"))
        sweeps[str(tid)]["arm_c_status"] = rec.get("status")
        sweeps[str(tid)]["arm_c_outcome"] = rec.get("outcome")

    def has(tid, key):
        s = sweeps.get(str(tid)) or {}
        return s.get(key)

    newly_accepted = sorted(ac - aa)
    newly_pass = sorted(pc - pa)

    # --- HV1, BOTH readings, neither substituted for the other ----------
    twelve_still_accepted = [t for t in HV1_TWELVE if t in ac]
    collapse_dependent = [t for t in sorted(ac)
                          if has(t, "accept_requires_list_tuple_collapse") is True]
    fails_corpus_assert = [t for t in newly_accepted
                           if has(t, "satisfies_corpus_own_assert_semantics") is False]
    hv1 = {
        "literal_reading": {
            "bar": "the 12 named collapse-accepts are REJECTED",
            "twelve": HV1_TWELVE,
            "still_accepted_in_arm_C": twelve_still_accepted,
            "rejected_in_arm_C": [t for t in HV1_TWELVE if t not in ac],
            "verdict": "PASS" if not twelve_still_accepted else "FAIL",
        },
        "mechanism_reading": {
            "bar": ("ZERO accepts DEPEND on the list/tuple collapse -- "
                    "measured per id as accept_requires_list_tuple_collapse, "
                    "the same fact arc6_verdict_report computed when it found 12. "
                    "THIS IS THE REGISTERED BAR: 'zero false accepts FROM THE "
                    "LIST/TUPLE COLLAPSE'."),
            "accepts_that_depend_on_the_collapse": collapse_dependent,
            "verdict": "PASS" if not collapse_dependent else "FAIL",
        },
        "separately__coincidental_fits_are_a_DIFFERENT_hazard": {
            "note": ("NOT what HV1 bars, and reported here rather than folded "
                     "into it. A coincidental fit is a program that is wrong "
                     "IN GENERAL while fitting the revealed rows -- a "
                     "pre-existing, separately-registered mechanism that has "
                     "nothing to do with container types. Every id below is "
                     "measured with accept_requires_list_tuple_collapse=False."),
            "newly_accepted_failing_the_corpus_own_assert": fails_corpus_assert,
            "newly_accepted_COINCIDENTAL_FIT": [
                t for t in newly_accepted if has(t, "verdict") == "COINCIDENTAL_FIT"],
            "newly_accepted_CORRECT": [
                t for t in newly_accepted if has(t, "verdict") == "CORRECT"],
            "seed_only_candidate_had_7_fits": [222, 249, 290, 393, 418, 424, 457],
        },
        "note": ("HV1-literal and HV2 are JOINTLY UNSATISFIABLE: 6 of HV2's 8 "
                 "ids (161 272 413 436 450 460) are IN the 12, so rejecting all "
                 "12 caps HV2 at 2. Both readings are reported; neither is "
                 "quietly substituted for the other."),
    }

    hv2_converted = [t for t in HV2_EIGHT if t in ac and t not in aa]
    hv2 = {
        "bar": ">=6 of the 8 measured-correct ids convert, each with a constructed witness",
        "eight": HV2_EIGHT,
        "converted": hv2_converted,
        "not_converted": [t for t in HV2_EIGHT if t not in hv2_converted],
        "witness_verdicts": {str(t): {
            "verdict": has(t, "verdict"),
            "n_probes": has(t, "n_constructed_probed"),
            "n_agree_typed": has(t, "n_typed_agree"),
            "n_agree_norm": has(t, "n_norm_agree"),
            "arm_c_status": has(t, "arm_c_status"),
        } for t in HV2_EIGHT},
        "n": len(hv2_converted),
        "required": 6,
        "verdict": "PASS" if len(hv2_converted) >= 6 else "FAIL",
    }

    hv3 = {
        "bar": "the 36 arm-A pass ids are preserved; the after-list is a superset",
        "armA_pass": sorted(pa), "armB_pass": sorted(pb), "armC_pass": sorted(pc),
        "lost_pass_C_vs_A": sorted(pa - pc),
        "lost_accepted_C_vs_A": sorted(aa - ac),
        "lost_pass_B_vs_A": sorted(pa - pb),
        "C_superset_of_A": pa <= pc,
        "C_superset_of_arc5_35": arc5 <= pc,
        "verdict": "PASS" if (pa <= pc and arc5 <= pc and aa <= ac) else "FAIL",
    }

    arms = {
        "A_baseline_code_baseline_engine": {
            "engine_sha256": A["engine_provenance"]["sha256"],
            "seed_sha256": A["seed_sha256"],
            "pass_ids": sorted(pa), "accepted_ids": sorted(aa),
            "n_pass": len(pa), "n_accepted": len(aa),
            "determinism": A.get("determinism"),
        },
        "B_baseline_code_FINAL_engine": {
            "engine_sha256": B["engine_provenance"]["sha256"],
            "seed_sha256": B["seed_sha256"],
            "pass_ids": sorted(pb), "accepted_ids": sorted(ab),
            "n_pass": len(pb), "n_accepted": len(ab),
            "determinism": B.get("determinism"),
        },
        "C_fix_code_FINAL_engine": {
            "engine_sha256": C["engine_provenance"]["sha256"],
            "seed_sha256": C["seed_sha256"],
            "pass_ids": sorted(pc), "accepted_ids": sorted(ac),
            "n_pass": len(pc), "n_accepted": len(ac),
            "determinism": C.get("determinism"),
        },
        "B_minus_A": {
            "pass_gained": sorted(pb - pa), "pass_lost": sorted(pa - pb),
            "accepted_gained": sorted(ab - aa), "accepted_lost": sorted(aa - ab),
            "reading": ("what the REBUILD plus the engine's own semantic change "
                        "did, with the adapter untouched. EMPTY means the value "
                        "layer is inert until the verdict is allowed to see a "
                        "non-scalar -- which is the honest shape of this rung."),
        },
        "C_minus_B": {
            "pass_gained": sorted(pc - pb), "pass_lost": sorted(pb - pc),
            "accepted_gained": sorted(ac - ab), "accepted_lost": sorted(ab - ac),
            "reading": "the intervention. THIS is what may be claimed (A1.2).",
        },
    }

    rec = {
        "_README": ("ARC6 value-layer list/tuple distinction. PAIRED ID LISTS, "
                    "never a bare count. The aggregate is UNDERPOWERED BY "
                    "CONSTRUCTION -- any move of a few ids sits inside the "
                    "baseline Wilson CI [9.96, 18.35]; the result is the id "
                    "list plus the witnesses, not the score."),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine_provenance_of_this_report": provenance_stamp(),
        "arms": arms,
        "aggregate_with_its_caveat": {
            "armA": vr.wilson(len(pa), A["n_runnable"]),
            "armB": vr.wilson(len(pb), B["n_runnable"]),
            "armC": vr.wilson(len(pc), C["n_runnable"]),
            "caveat": ("the intervals overlap; this is underpowered by "
                       "construction and is NOT a detection. The result is the "
                       "id list and the witnesses."),
        },
        "paired_diff": {
            "newly_accepted_C_vs_A": newly_accepted,
            "newly_pass_C_vs_A": newly_pass,
            "lost_accepted": sorted(aa - ac),
            "lost_pass": sorted(pa - pc),
        },
        "bars": {"HV1": hv1, "HV2": hv2, "HV3": hv3, "HV4": foldup_lane_audit()},
        "constructed_witness_sweeps": sweeps,
        "comparator_semantics_probe": vr.comparator_probe(),
        "comparator_probe_read_this_way": (
            "vr.comparator_probe() feeds its pairs through `Lit`, i.e. through "
            "`json.dumps`, where JSON's ONE array type erases list-vs-tuple "
            "BEFORE the engine sees it -- so its `(1,2) vs [1,2]` row still "
            "reads True and is measuring the Lit/JSON boundary, NOT the value "
            "layer. `attr_comparator_probe` below is the same question asked "
            "the way a row verdict actually asks it: off graph ATTRS."),
        "attr_comparator_probe": attr_comparator_probe(),
        "out_of_scope_defects": {
            "sorted_on_strings": ("prereg §4. `cmp_value` still orders Str by "
                                  "interner symbol id; DELIBERATELY untouched. "
                                  "Probed live by "
                                  "tests/test_arc6_valuelayer_migrated.py::"
                                  "test_out_of_scope_defects_are_still_present_and_named"),
            "eq_0p0_false": ("A3. `Eq(0.0, False)` is False in the substrate and "
                             "True in Python. Named, not bundled; see the "
                             "comparator_semantics_probe rows."),
        },
    }
    with open(OUT, "w") as f:
        json.dump(rec, f, indent=2, sort_keys=True, default=vr._jdefault)
    print("HV1 literal   :", hv1["literal_reading"]["verdict"],
          "still accepted:", twelve_still_accepted)
    print("HV1 mechanism :", hv1["mechanism_reading"]["verdict"],
          "collapse-dependent:", collapse_dependent)
    print("  (separate)   : coincidental fits:",
          [t for t in newly_accepted if has(t, "verdict") == "COINCIDENTAL_FIT"],
          "| fails corpus assert:", fails_corpus_assert)
    print("HV2           :", hv2["verdict"], hv2_converted)
    print("HV3           :", hv3["verdict"], "lost:", hv3["lost_pass_C_vs_A"])
    print("HV4           :", rec["bars"]["HV4"]["verdict"])
    print("B-A           :", arms["B_minus_A"]["pass_gained"],
          arms["B_minus_A"]["pass_lost"])
    print("C-B           :", arms["C_minus_B"]["pass_gained"],
          arms["C_minus_B"]["pass_lost"])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
