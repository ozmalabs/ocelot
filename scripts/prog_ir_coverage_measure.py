#!/usr/bin/env python3
"""prog_ir_coverage_measure.py — P2 (python frame) coverage measurement
(PROGRAM_SYNTHESIS_PREREG.md §4; the P2 task card).

Over the SAME corpus scope as the frozen P0 baseline scan
(`results/code_synthesis_baseline.json`: sorted *.py under domains/,
TOP-LEVEL ast.FunctionDef only — `code_curriculum.scan_repo_functions`'s
enumeration, reproduced verbatim, minus the agent reads), attempt
`emit_prog_ir` on every function and record ok / blockers. Also computes:

  * the ProgEval-PREDICTABLE subset of the emittable set (no undeclared
    externs: every extern in the P1 native-oracle set, no recv-form calls)
    — the honest second number;
  * the P0 histogram's PREDICTION for this scope, computed from its own
    per-function `analyse()` (imported, never reimplemented): a function is
    predicted-representable iff its required-variant set ⊆ the P1 variant
    set (at_80 21 + While + Raise);
  * the same two numbers over the HISTOGRAM'S OWN scope (domains/ +
    substrate/, methods + nested + async included, 9,522 functions at P0)
    so the ~80.5% headline is compared like-for-like;
  * the frozen 27-identity baseline list checked as a SUBSET of the new
    emittable list (the §4 registered prediction — any exit is named).

Deterministic: sorted walks, sorted keys, fixed date field. Pure-ast +
emitter; no substrate boot, no agent logic.

Output: results/prog_ir_python_coverage.json — every total DERIVED from an
identity list (the 2026-07-21 baseline rule).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 \
     scripts/prog_ir_coverage_measure.py

ARC 2 Q1.5 ADDITIVE RE-RUN MODE (PROGRAM_SYNTHESIS_ARC2_Q15_NOTES.md):
`main()` above (the P2 measurement — frozen, byte-untouched by this phase)
is never called by the new mode. `main_append_q15()` re-runs the IDENTICAL
`enumerate_baseline_scope()` / `measure()` / `aggregate()` pipeline against
the Q1.5-widened `domains/prog_ir_emit.py` and APPENDS the result as a new
top-level `q15_post_widening` key onto the EXISTING on-disk artifact — the
frozen P2 keys (`scope_baseline_domains_toplevel`, `scope_histogram_full`,
`frozen_27_subset_check`) are read back and rewritten byte-identical;
nothing here overwrites them (the arc-1 "append-only frozen artifact"
discipline, PROGRAM_SYNTHESIS_ARC2_PREREG.md §8 "a baseline is a list").

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 \
     scripts/prog_ir_coverage_measure.py --append-q15
"""
from __future__ import annotations

import ast
import json
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains.prog_ir_emit import P1_VARIANT_SET, emit_prog_ir  # noqa: E402
import prog_ir_statement_histogram as hist                     # noqa: E402

DATE = "2026-07-31"
DATE_Q15 = "2026-08-01"   # arc 2 Q1.5 additive re-run date (module docstring)
BASELINE_PATH = os.path.join(_ROOT, "results", "code_synthesis_baseline.json")
OUT_PATH = os.path.join(_ROOT, "results", "prog_ir_python_coverage.json")


def enumerate_baseline_scope():
    """The frozen-baseline scan's enumeration, verbatim: sorted *.py under
    domains/, top-level ast.FunctionDef only (async excluded, methods and
    nested defs excluded — `scan_repo_functions` walks `tree.body`)."""
    all_paths = []
    base = os.path.join(_ROOT, "domains")
    for dirpath, _dirnames, filenames in os.walk(base):
        for fn in filenames:
            if fn.endswith(".py"):
                all_paths.append(os.path.join(dirpath, fn))
    all_paths.sort()
    n_files = 0
    out = []
    for path in all_paths:
        try:
            src = open(path).read()
        except OSError:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        n_files += 1
        rel = os.path.relpath(path, _ROOT)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                out.append((rel, node))
    return out, n_files


def measure(funcs, meta_maker):
    """One pass: emit + histogram-analyse every function. Returns per-id
    rows keyed for aggregation."""
    rows = []
    for fid, node, meta in funcs:
        r = emit_prog_ir(node)
        _feats, req = hist.analyse(node, meta)
        predicted = all(v in P1_VARIANT_SET for v in req)
        rows.append({
            "id": fid,
            "ok": r["ok"],
            "blockers": r.get("blockers", []),
            "predictable": bool(r.get("predictable")) if r["ok"] else False,
            "externs": r.get("externs", []) if r["ok"] else [],
            "predicted": predicted,
            "req_outside_set": sorted(v for v in req
                                      if v not in P1_VARIANT_SET),
        })
    return rows


def aggregate(rows, total):
    ok_ids = sorted(r["id"] for r in rows if r["ok"])
    predictable_ids = sorted(r["id"] for r in rows if r["ok"] and r["predictable"])
    blocked = sorted(({"id": r["id"], "blockers": r["blockers"]}
                      for r in rows if not r["ok"]), key=lambda x: x["id"])
    blocker_mass = Counter()
    for r in rows:
        for b in r["blockers"]:
            blocker_mass[b] += 1
    predicted_ids = sorted(r["id"] for r in rows if r["predicted"])
    pred_not_emit = sorted(({"id": r["id"], "blockers": r["blockers"]}
                            for r in rows if r["predicted"] and not r["ok"]),
                           key=lambda x: x["id"])
    emit_not_pred = sorted(({"id": r["id"],
                             "req_outside_set": r["req_outside_set"]}
                            for r in rows if r["ok"] and not r["predicted"]),
                           key=lambda x: x["id"])
    pne_mass = Counter()
    for row in pred_not_emit:
        for b in row["blockers"]:
            pne_mass[b] += 1
    pct = lambda n: round(100.0 * n / total, 2) if total else 0.0
    return {
        "n_total": total,
        "emittable": {"n": len(ok_ids), "pct": pct(len(ok_ids)),
                      "ids": ok_ids},
        "predictable": {
            "definition": ("emittable AND every extern name in the P1 "
                           "native-oracle set AND no recv-form call — "
                           "'no undeclared externs'"),
            "n": len(predictable_ids), "pct": pct(len(predictable_ids)),
            "pct_of_emittable": (round(100.0 * len(predictable_ids)
                                       / len(ok_ids), 2) if ok_ids else 0.0),
            "ids": predictable_ids},
        "blocked": {"n": len(blocked), "rows": blocked,
                    "blocker_mass_ranked": [
                        {"blocker": k, "mass": v} for k, v in
                        sorted(blocker_mass.items(),
                               key=lambda kv: (-kv[1], kv[0]))]},
        "histogram_prediction": {
            "definition": ("required-variant set (histogram analyse(), "
                           "imported) ⊆ the P1 variant set"),
            "n_predicted": len(predicted_ids), "pct": pct(len(predicted_ids)),
            "predicted_ids": predicted_ids,
            "agreement": {
                "predicted_and_emitted": len([r for r in rows
                                              if r["predicted"] and r["ok"]]),
                "predicted_not_emitted": {
                    "n": len(pred_not_emit), "rows": pred_not_emit,
                    "blocker_mass_ranked": [
                        {"blocker": k, "mass": v} for k, v in
                        sorted(pne_mass.items(),
                               key=lambda kv: (-kv[1], kv[0]))]},
                "emitted_not_predicted": {"n": len(emit_not_pred),
                                          "rows": emit_not_pred},
            }},
    }


def main():
    # ---- scope A: the frozen-baseline scan scope (domains/ top-level) ----
    pairs, n_files = enumerate_baseline_scope()
    funcs_a = [("%s::%s@%d" % (rel, node.name, node.lineno), node,
                {"is_method": False, "is_async": False,
                 "is_nested": False, "is_toplevel": True})
               for rel, node in pairs]
    rows_a = measure(funcs_a, None)
    agg_a = aggregate(rows_a, len(funcs_a))

    # ---- scope B: the histogram's own scope (domains/+substrate/, all) ----
    hfuncs, h_files, h_syntax = hist.enumerate_functions()
    funcs_b = [(fid, node, meta) for fid, node, meta in hfuncs]
    rows_b = measure(funcs_b, None)
    agg_b = aggregate(rows_b, len(funcs_b))
    # scope B id lists are large and derivable; keep the numbers + the
    # blocker mass, drop the per-id lists (scope A is the deliverable list).
    for key in ("emittable", "predictable"):
        agg_b[key].pop("ids", None)
    agg_b["blocked"].pop("rows", None)
    agg_b["histogram_prediction"].pop("predicted_ids", None)
    agg_b["histogram_prediction"]["agreement"]["predicted_not_emitted"].pop("rows", None)
    agg_b["histogram_prediction"]["agreement"]["emitted_not_predicted"].pop("rows", None)

    # ---- the frozen 27-identity subset check (§4 registered prediction) ----
    with open(BASELINE_PATH) as fh:
        baseline = json.load(fh)
    frozen27 = [(e["file"], e["qualname"])
                for e in baseline["term_emittable"]["entries"]]
    emitted_keys = set()
    for r in rows_a:
        rel, rest = r["id"].split("::", 1)
        name = rest.split("@", 1)[0]
        if r["ok"]:
            emitted_keys.add((rel, name))
    missing27 = sorted("%s::%s" % k for k in frozen27
                       if k not in emitted_keys)

    out = {
        "date": DATE,
        "task": "PROGRAM_SYNTHESIS P2 (python frame) coverage",
        "emitter": "domains/prog_ir_emit.py emit_prog_ir (ast entry)",
        "p1_variant_set": sorted(P1_VARIANT_SET),
        "scope_baseline_domains_toplevel": {
            "enumeration": ("sorted *.py under domains/, top-level "
                            "ast.FunctionDef only — scan_repo_functions' "
                            "walk (the frozen-baseline scope)"),
            "n_files": n_files,
            **agg_a,
        },
        "scope_histogram_full": {
            "enumeration": ("prog_ir_statement_histogram.enumerate_functions"
                            " — domains/ + substrate/, methods + nested + "
                            "async included (the P0 histogram scope)"),
            "n_files": h_files, "n_syntax_error": h_syntax,
            "note": ("per-id lists elided for size; identical derivation to "
                     "scope A — rerun this script to regenerate"),
            **agg_b,
        },
        "frozen_27_subset_check": {
            "registered_prediction": ("PROGRAM_SYNTHESIS_PREREG.md §4: the "
                                      "frozen 27 survive as a subset of the "
                                      "new emittable list; any exit is a "
                                      "named regression"),
            "n_frozen": len(frozen27),
            "all_present": not missing27,
            "missing": missing27,
        },
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s" % OUT_PATH)
    a, b = out["scope_baseline_domains_toplevel"], out["scope_histogram_full"]
    print("scope A (domains/ toplevel, n=%d): emittable %d (%.2f%%), "
          "predictable %d (%.2f%%), histogram-predicted %d (%.2f%%)"
          % (a["n_total"], a["emittable"]["n"], a["emittable"]["pct"],
             a["predictable"]["n"], a["predictable"]["pct"],
             a["histogram_prediction"]["n_predicted"],
             a["histogram_prediction"]["pct"]))
    print("scope B (histogram full, n=%d): emittable %d (%.2f%%), "
          "predictable %d (%.2f%%), histogram-predicted %d (%.2f%%)"
          % (b["n_total"], b["emittable"]["n"], b["emittable"]["pct"],
             b["predictable"]["n"], b["predictable"]["pct"],
             b["histogram_prediction"]["n_predicted"],
             b["histogram_prediction"]["pct"]))
    print("frozen-27 subset: all_present=%s missing=%d"
          % (out["frozen_27_subset_check"]["all_present"], len(missing27)))
    print("top blockers (scope A): %s"
          % ", ".join("%s=%d" % (r["blocker"], r["mass"]) for r in
                      a["blocked"]["blocker_mass_ranked"][:12]))


def main_append_q15():
    """ARC 2 Q1.5 additive re-run (module docstring): re-derive BOTH scope
    measurements from the SAME `enumerate_baseline_scope()`/`measure()`/
    `aggregate()` functions above (unmodified) against the Q1.5-widened
    emitter, and APPEND them under a new `q15_post_widening` key onto the
    EXISTING on-disk artifact. The frozen P2 keys are read back and
    rewritten byte-identical — never overwritten."""
    with open(OUT_PATH) as fh:
        existing = json.load(fh)
    frozen_a = existing["scope_baseline_domains_toplevel"]
    frozen_b = existing["scope_histogram_full"]

    pairs, n_files = enumerate_baseline_scope()
    funcs_a = [("%s::%s@%d" % (rel, node.name, node.lineno), node,
                {"is_method": False, "is_async": False,
                 "is_nested": False, "is_toplevel": True})
               for rel, node in pairs]
    rows_a = measure(funcs_a, None)
    agg_a = aggregate(rows_a, len(funcs_a))

    hfuncs, h_files, h_syntax = hist.enumerate_functions()
    funcs_b = [(fid, node, meta) for fid, node, meta in hfuncs]
    rows_b = measure(funcs_b, None)
    agg_b = aggregate(rows_b, len(funcs_b))
    for key in ("emittable", "predictable"):
        agg_b[key].pop("ids", None)
    agg_b["blocked"].pop("rows", None)
    agg_b["histogram_prediction"].pop("predicted_ids", None)
    agg_b["histogram_prediction"]["agreement"]["predicted_not_emitted"].pop("rows", None)
    agg_b["histogram_prediction"]["agreement"]["emitted_not_predicted"].pop("rows", None)

    existing["q15_post_widening"] = {
        "date": DATE_Q15,
        "task": "PROGRAM_SYNTHESIS ARC2 Q1.5 (python frame) coverage re-run",
        "emitter": "domains/prog_ir_emit.py emit_prog_ir (ast entry, Q1.5-widened)",
        "note": ("SAME enumeration + aggregate() derivation as the frozen "
                 "P2 keys above (scope_baseline_domains_toplevel / "
                 "scope_histogram_full), re-run against the Q1.5-widened "
                 "emitter (ProgSlice, bitwise set-algebra, method-oracle "
                 "recv form, container_ctor/math_native/general_builtins "
                 "predictability, isinstance type-name wiring). This block "
                 "is APPENDED — the P2 keys above are byte-unchanged."),
        "scope_baseline_domains_toplevel": {
            "n_files": n_files,
            "delta_vs_frozen_p2": {
                "emittable_n": agg_a["emittable"]["n"] - frozen_a["emittable"]["n"],
                "predictable_n": agg_a["predictable"]["n"] - frozen_a["predictable"]["n"],
            },
            **agg_a,
        },
        "scope_histogram_full": {
            "n_files": h_files, "n_syntax_error": h_syntax,
            "delta_vs_frozen_p2": {
                "emittable_n": agg_b["emittable"]["n"] - frozen_b["emittable"]["n"],
                "predictable_n": agg_b["predictable"]["n"] - frozen_b["predictable"]["n"],
            },
            **agg_b,
        },
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        json.dump(existing, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("appended q15_post_widening to %s" % OUT_PATH)
    qa, qb = existing["q15_post_widening"]["scope_baseline_domains_toplevel"], \
        existing["q15_post_widening"]["scope_histogram_full"]
    print("Q1.5 scope A (domains/ toplevel, n=%d): emittable %d (%.2f%%, "
          "delta %+d), predictable %d (%.2f%%, delta %+d)"
          % (n_files and len(funcs_a), qa["emittable"]["n"], qa["emittable"]["pct"],
             qa["delta_vs_frozen_p2"]["emittable_n"],
             qa["predictable"]["n"], qa["predictable"]["pct"],
             qa["delta_vs_frozen_p2"]["predictable_n"]))
    print("Q1.5 scope B (histogram full, n=%d): emittable %d (%.2f%%, "
          "delta %+d), predictable %d (%.2f%%, delta %+d)"
          % (len(funcs_b), qb["emittable"]["n"], qb["emittable"]["pct"],
             qb["delta_vs_frozen_p2"]["emittable_n"],
             qb["predictable"]["n"], qb["predictable"]["pct"],
             qb["delta_vs_frozen_p2"]["predictable_n"]))


if __name__ == "__main__":
    if "--append-q15" in sys.argv:
        main_append_q15()
    else:
        main()
