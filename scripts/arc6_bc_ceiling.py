#!/usr/bin/env python
"""arc6_bc_ceiling — ARC 6 M0, the B and C ceiling probes (MEASUREMENT ONLY,
builds nothing). Companion to `PROGRAM_SYNTHESIS_ARC6_PLAN.md` §1 seams B/C
and §3 M0, and to `PROGRAM_SYNTHESIS_ARC6_A_CEILING.md` (whose honest-vs-
cherry-picked discipline this script reproduces for both ceilings).

This script owns ONLY `results/arc6_bc_ceiling.json` and this file. It writes
nothing else, reads no file for edit, and touches no seed/engine/adapter
source. It never calls git.

=====================================================================
CEILING B — `extract_function` retargeted to hub IR
=====================================================================
`domains/construction_grammar.py::extract_function` + `comprehend_recursive`
is a closed propose-from-NL -> verify-by-execution loop (proven 8/8 against
real OEIS ground truth). Seam B would retarget its OUTPUT surface from
`compute_grounding`'s formula string to hub IR. Retargeting the output cannot
change what the INPUT grammar can read, so the ceiling is set by two things,
both measured here by live invocation:

  (B-i)  SURFACE reach — does `extract_function(prompt)` return anything on an
         MBPP prompt, and is what it returns CORRECT (verified by executing
         the extracted formula against the task's own example rows — never
         judged by eye)?
  (B-ii) LANGUAGE reach — the grammar is FINITE and small. Its entire language
         is ENUMERATED here (every aggregator x value-map x pre-filter x
         member-form x post-filter surface, plus the flat clauses), each
         surface fed through the REAL `extract_function`, each resulting
         formula GROUNDED (`comprehend_computational_definition`) and
         EVALUATED (`reason.solve`). A task is IN-LANGUAGE iff some sentence
         of that language reproduces EVERY one of the task's example rows.
         This bounds ANY retargeting of the parser, because it is a statement
         about what the grammar can MEAN, not about how prose is spelled.

The mechanical retarget (B-i, retargeted variant) is ONE task-independent
normalisation, nameable before the population is read: strip the MBPP
boilerplate imperative prefix, and rewrite the argument-denoting noun phrases
("a given number", "the number", ...) to the grammar's index variable `n`.
Nothing per-task. The cherry-picked ceilings are reported beside the honest
ones so the granularity inflation is visible rather than available.

=====================================================================
CEILING C — math `ShapeSignature`s as the recognition codebook
=====================================================================
`PROGRAM_SYNTHESIS_ARC5_SHAPE_PROBE.md` measured 0 GENUINE algorithmic
recognitions against `seeds/shape_vocabulary.json` (23 hits, all substring
collisions). Seam C proposes `seeds/math_capability_shapes.json` instead.

Measured here: the codebook's real composition (re-derived, not quoted); the
SCHEMA question (does `RecogniseShape` even consume this file?) answered by
live invocation in BOTH directions — a null-returning harness is worthless
unless a positive control proves the harness fires; three keyword variants
mechanically derived from content ALREADY IN the seed file (no new vocabulary
authored, so the test can never be a per-task key); every hit traced to its
causing keyword, classified genuine/spurious, and subjected to the KEY TEST
(a cue that fires on exactly one task is a lookup key, not a recognition —
the failure mode Seam D's leave-one-out just exposed).

CONTAMINATION. MBPP test-split `code` is never read by this script at all
(`q0_split_tasks` strips it). Prompt text and example rows are read for
MEASUREMENT classification only; no prompt text enters any codebook, cue
vocabulary, or taught shape — the three C variants are derived exclusively
from the seed file, mechanically, and are printed in the artifact so this can
be checked. Example rows are used ONLY to VERIFY a candidate by execution;
nothing is fed back into any search or selection path (there is no search in
this script).

Runtime:
    OZMA_NO_LLM=1 python scripts/arc6_bc_ceiling.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ENGINE PROVENANCE FIRST — before anything can import substrate_rs. A number
# from an unknown binary is not a measurement (PROTOCOL §10; the .pth points
# at the CANONICAL tree, so a worktree silently measures a foreign engine
# unless this call pins its own).
from domains.engine_provenance import (  # noqa: E402
    engine_preamble, provenance_stamp, sha256_of)

engine_preamble()

import substrate_rs as srs  # noqa: E402,F401
import mbpp_arc3_battery as arc3b  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
from substrate.seed_loader import normalize_declarative  # noqa: E402
from domains import construction_grammar as cg  # noqa: E402
from domains import compute_grounding as cgnd  # noqa: E402
from domains import reason  # noqa: E402
from domains import mbpp_spec  # noqa: E402

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
PROSE_PATH = os.path.join(ROOT, "seeds", "math_prose_constructions.json")
MATH_SHAPES_PATH = os.path.join(ROOT, "seeds", "math_capability_shapes.json")
SHAPE_VOCAB_PATH = os.path.join(ROOT, "seeds", "shape_vocabulary.json")
OUT_PATH = os.path.join(ROOT, "results", "arc6_bc_ceiling.json")

# Every input this measurement depends on, hashed into the artifact so the
# numbers are attributable to an exact file state (a sibling agent editing a
# seed mid-run is the named hazard).
INPUT_FILES = [
    "domains/construction_grammar.py",
    "domains/compute_grounding.py",
    "domains/reason.py",
    "domains/mbpp_spec.py",
    "seeds/math_prose_constructions.json",
    "seeds/math_capability_shapes.json",
    "seeds/shape_vocabulary.json",
    "tests/fixtures/mbpp/sanitized-mbpp.json",
    "scripts/mbpp_zero_shot_baseline.py",
]

# n-window over which two grammar formulas are compared for SEMANTIC identity
# (two spellings of the same function collapse to one entry).
SIG_WINDOW = list(range(1, 25))
# A row whose single input exceeds this is not evaluated — the grammar's forms
# are O(n) sums and a 10^6 row would dominate the runtime. Recorded, never
# silently dropped.
MAX_EVAL_N = 20000


# ========================================================================= #
#  shared loaders
# ========================================================================= #
def load_test_tasks() -> List[Dict[str, Any]]:
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    tasks = arc3b.q0_split_tasks(all_tasks)["test"]
    for t in tasks:
        assert "code" not in t, "contamination: code survived the split"
    return tasks


def task_rows(task: Dict[str, Any]) -> Dict[str, Any]:
    """All parseable example rows for a task, via the STANDING spec parser
    (`domains/mbpp_spec.py`), unmodified. Used for VERIFICATION ONLY."""
    parsed = mbpp_spec.parse_asserts(task)
    rows = parsed.get("rows", [])
    return {"rows": rows, "n_rows": len(rows),
            "n_unparseable": parsed.get("n_unparseable", 0)}


# ========================================================================= #
#  CEILING B
# ========================================================================= #
def b_vocabulary() -> Dict[str, Any]:
    """VERIFY the plan's quoted vocabulary against the seed file itself, and
    report the DISTINCT-SEMANTICS collapse beside the raw entry counts (the
    same granularity trap the A-ceiling found: an entry count is not a
    capability count)."""
    with open(PROSE_PATH) as f:
        g = json.load(f)

    raw = {k: len(g.get(k, [])) for k in
           ("clauses", "member_forms", "value_maps", "filters", "aggregators",
            "operators")}
    plan_claim = {"clauses": 10, "member_forms": 5, "aggregators": 4,
                  "filters": 4}
    plan_agrees = {k: (raw[k] == v) for k, v in plan_claim.items()}

    # DISTINCT SEMANTICS — collapse entries that differ only in surface
    # spelling (a leading "the", a synonym) onto the value they compute.
    distinct = {
        "clauses": sorted({c["formula"] for c in g["clauses"]}),
        "member_forms": sorted({(m["value"], m["predicate"])
                                for m in g["member_forms"]}),
        "value_maps": sorted({(v["value"], v["predicate"])
                              for v in g["value_maps"]}),
        "filters": sorted({f["mask"] for f in g["filters"]}),
        "aggregators": sorted({a["formula"] for a in g["aggregators"]}),
    }
    operators_runnable = sorted({bool(o.get("held_runnable"))
                                 for o in g.get("operators", [])})
    return {
        "raw_entry_counts": raw,
        "plan_quoted": plan_claim,
        "plan_quoted_verified": plan_agrees,
        "plan_quoted_verified_all": all(plan_agrees.values()),
        "distinct_semantics_counts": {k: len(v) for k, v in distinct.items()},
        "distinct_semantics": {k: [list(x) if isinstance(x, tuple) else x
                                   for x in v] for k, v in distinct.items()},
        "operators_held_runnable_values": operators_runnable,
        "operators_are_inert": operators_runnable == [False],
        "index_var": g.get("index_var"),
        "acquired_at_import": {k: len(v) for k, v in cg._ACQUIRED.items()},
        "note": ("The 27 `operators` all carry held_runnable=false — they are "
                 "comprehend_theorem's invariant-naming vocabulary sharing "
                 "this file, not part of extract_function's arithmetic "
                 "surface. Confirmed here rather than quoted."),
    }


def b_enumerate_language() -> Dict[str, Any]:
    """ENUMERATE the grammar's ENTIRE language by generating every surface the
    construction grammar can compose, feeding each through the REAL
    `extract_function`, then GROUNDING and EVALUATING every formula it emits.

    Nothing is hand-written: the surfaces are assembled from the seed's own
    `pattern` lists, and every formula in the result came out of the real
    extractor. This is the LANGUAGE, not a reconstruction of it."""
    with open(PROSE_PATH) as f:
        g = json.load(f)

    def surface(pattern: List[str]) -> str:
        return " ".join(p for p in pattern if not p.startswith("{"))

    aggs = [surface(a["pattern"]) for a in g["aggregators"]]
    vmaps = [""] + [surface(v["pattern"]) for v in g["value_maps"]]
    pres = [""] + [surface(f["pattern"]) for f in g["filters"]
                   if f.get("position") == "pre"]
    mforms = [surface(m["pattern"]) for m in g["member_forms"]]
    posts = [""] + [surface(f["pattern"]) for f in g["filters"]
                    if f.get("position") != "pre"]

    surfaces: List[str] = []
    for a in aggs:
        for v in vmaps:
            for p in pres:
                for m in mforms:
                    for q in posts:
                        parts = [a] + ([v] if v else []) + ([p] if p else []) \
                            + [m] + ([q] if q else [])
                        surfaces.append(" ".join(parts))
    # the FLAT clause route — each clause's own surface string.
    clause_surfaces = [c["clause"] for c in g["clauses"]]
    surfaces_all = surfaces + clause_surfaces

    formulas: Dict[str, List[str]] = {}   # formula -> surfaces that produced it
    unparsed_surfaces: List[str] = []
    for s in surfaces_all:
        cands = cg.extract_function(s)
        if not cands:
            unparsed_surfaces.append(s)
            continue
        for c in cands:
            formulas.setdefault(c, []).append(s)

    # GROUND + EVALUATE each formula; dedupe by its value signature.
    entries: List[Dict[str, Any]] = []
    by_sig: Dict[str, str] = {}
    for f in sorted(formulas):
        term = ground_formula(f)
        if term is None:
            entries.append({"formula": f, "grounded": False,
                            "example_surface": sorted(formulas[f])[0]})
            continue
        sig = []
        ok = True
        for n in SIG_WINDOW:
            v = eval_formula(term, n)
            if v is None:
                ok = False
                break
            sig.append(v)
        if not ok:
            entries.append({"formula": f, "grounded": True, "evaluable": False,
                            "example_surface": sorted(formulas[f])[0]})
            continue
        key = json.dumps(sig)
        entries.append({
            "formula": f, "grounded": True, "evaluable": True,
            "signature_n_1_to_24": sig,
            "n_surfaces": len(formulas[f]),
            "example_surface": sorted(formulas[f])[0],
            "semantic_duplicate_of": by_sig.get(key),
        })
        by_sig.setdefault(key, f)

    runnable = [e for e in entries if e.get("evaluable")]
    canonical = [e for e in runnable if e.get("semantic_duplicate_of") is None]
    return {
        "n_generated_surfaces": len(surfaces_all),
        "n_surfaces_that_parse": len(surfaces_all) - len(unparsed_surfaces),
        "unparsed_surfaces": sorted(unparsed_surfaces),
        "n_distinct_formulas": len(formulas),
        "n_runnable_formulas": len(runnable),
        "n_distinct_FUNCTIONS": len(canonical),
        "canonical_functions": [
            {"formula": e["formula"], "example_surface": e["example_surface"],
             "signature_n_1_to_24": e["signature_n_1_to_24"]}
            for e in sorted(canonical, key=lambda x: x["formula"])],
        "all_entries": entries,
        "note": ("n_distinct_FUNCTIONS is the whole semantic reach of the "
                 "grammar's compositional + flat-clause routes. The embedded-"
                 "'=' route (b) is NOT finite and is measured separately."),
    }


_GROUND_CACHE: Dict[str, Any] = {}


def ground_formula(formula: str):
    if formula in _GROUND_CACHE:
        return _GROUND_CACHE[formula]
    try:
        comp = cgnd.comprehend_computational_definition("a(n) = %s" % formula)
    except Exception:
        comp = None
    term = comp["term"] if comp else None
    _GROUND_CACHE[formula] = term
    return term


def eval_formula(term, n: int) -> Optional[int]:
    try:
        v = reason.solve(term, {"n": n})
    except Exception:
        return None
    try:
        return int(v)
    except Exception:
        return None


def _unary_int_rows(rows: List[Dict[str, Any]]) -> Optional[List[Tuple[int, int]]]:
    """A task is a candidate for the grammar's f(n)->int form iff EVERY row has
    exactly one input, that input is a non-bool int, and the expected value is
    a non-bool int. Returns [(n, expected)] or None."""
    out: List[Tuple[int, int]] = []
    if not rows:
        return None
    for r in rows:
        ins = r.get("inputs", {})
        if len(ins) != 1:
            return None
        (v,) = list(ins.values())
        e = r.get("expected")
        if isinstance(v, bool) or isinstance(e, bool):
            return None
        if not isinstance(v, int) or not isinstance(e, int):
            return None
        out.append((v, e))
    return out


def b_in_language(tasks: List[Dict[str, Any]], language: Dict[str, Any]) -> Dict[str, Any]:
    """(B-ii) THE LANGUAGE CEILING. For every task with the grammar's own
    signature shape f(int)->int, test EVERY sentence of the enumerated
    language against ALL of the task's example rows. A task is in-language iff
    some sentence reproduces every row.

    ALL rows are required — the A-ceiling's task-87 lesson (a kernel verified
    on one row and reported as a match would have been a fifth coincidental
    fit, produced by under-sampling rather than by cherry-picking)."""
    funcs = [(e["formula"], ground_formula(e["formula"]))
             for e in language["canonical_functions"]]
    funcs = [(f, t) for f, t in funcs if t is not None]

    shape_ok, shape_bad, skipped_big = [], [], []
    hits: List[Dict[str, Any]] = []
    per_task: Dict[str, Any] = {}
    for t in tasks:
        tid = t["task_id"]
        rows = task_rows(t)["rows"]
        pairs = _unary_int_rows(rows)
        if pairs is None:
            shape_bad.append(tid)
            per_task[str(tid)] = {"signature_shape": "not_unary_int"}
            continue
        if any(abs(n) > MAX_EVAL_N for n, _ in pairs):
            skipped_big.append(tid)
            per_task[str(tid)] = {"signature_shape": "unary_int",
                                  "skipped": "input_exceeds_MAX_EVAL_N"}
            continue
        shape_ok.append(tid)
        matched = None
        for formula, term in funcs:
            ok = True
            for n, expected in pairs:
                got = eval_formula(term, n)
                if got is None or got != expected:
                    ok = False
                    break
            if ok:
                matched = formula
                break
        per_task[str(tid)] = {"signature_shape": "unary_int",
                              "n_rows": len(pairs),
                              "matched_formula": matched}
        if matched:
            hits.append({"task_id": tid, "formula": matched,
                         "n_rows_all_matched": len(pairs),
                         "prompt": t["prompt"]})
    return {
        "n_language_sentences_tested": len(funcs),
        "signature_shape_unary_int_ids": sorted(shape_ok),
        "n_signature_shape_unary_int": len(shape_ok),
        "n_signature_shape_other": len(shape_bad),
        "skipped_input_too_large_ids": sorted(skipped_big),
        "in_language_ids": sorted(h["task_id"] for h in hits),
        "in_language_hits": hits,
        "per_task": per_task,
    }


_BOILERPLATE = re.compile(
    r"^\s*write a (?:python )?(?:function|program)\s+(?:that\s+|to\s+)?", re.I)
# ONE task-independent normalisation, nameable before the population is read:
# the argument-denoting noun phrases MBPP uses where the grammar expects its
# index variable `n`. Longest first so "the given number" wins over "number".
_ARG_PHRASES = [
    "a given natural number", "the given natural number",
    "a given number", "the given number", "given number",
    "a given integer", "the given integer",
    "a number", "the number", "an integer", "the integer",
]

# TWO GUARDS, both derived from the GRAMMAR (not from the population), added
# after the un-guarded version was caught spuriously REFUTING task 96 — see
# `retarget_guards_provenance` in the artifact and §"what broke" in the write-up.
#   G1  "the number OF ..." is the grammar's own `number_of` AGGREGATOR, not an
#       argument. Never rewrite an argument phrase that is followed by "of".
#   G2  "an integer n" already BINDS the index variable. Rewriting it yields
#       "n n". When the phrase is followed by the index variable, DELETE the
#       phrase instead of substituting it.
_AGG_HEADS = ("of",)


def mechanical_retarget(prompt: str) -> str:
    """The BEDROCK RETARGET, mechanically: strip MBPP's imperative boilerplate
    and rewrite argument-denoting noun phrases to the grammar's index variable.
    Task-independent by construction — the phrase list and both guards are
    fixed, grammar-derived and printed in the artifact, so they can be diffed
    against a version written without reading the population."""
    s = _BOILERPLATE.sub("", prompt)
    low = s.lower()
    for ph in _ARG_PHRASES:
        out, i = [], 0
        while True:
            j = low.find(ph, i)
            if j < 0:
                out.append(low[i:])
                break
            tail = low[j + len(ph):]
            nxt = tail.lstrip()
            if nxt.split(" ")[0].strip(".,;:") in _AGG_HEADS:      # G1
                out.append(low[i:j + len(ph)])
            elif nxt.split(" ")[0].strip(".,;:") == "n":            # G2
                out.append(low[i:j])
            else:
                out.append(low[i:j] + "n")
            i = j + len(ph)
        low = "".join(out)
    return re.sub(r"\s+", " ", low).strip()


# ---- witness verification of the language ceiling ------------------------- #
# A row-matching formula is a CANDIDATE, not a hit. Each in-language id is
# checked against a reference relation written from the PROMPT's ordinary
# meaning (external knowledge — never the task's reference code, never a
# held-out row) over a sweep far wider than the rows. Researcher judgment,
# recorded with its reasoning so it can be checked.
def _n_divisors(n):
    return sum(1 for k in range(1, n + 1) if n % k == 0)


def _aliquot(n):
    return sum(k for k in range(1, n) if n % k == 0)


def _sum_even_divisors(n):
    return sum(k for k in range(1, n + 1) if n % k == 0 and k % 2 == 0)


REFERENCE_RELATIONS: Dict[int, Dict[str, Any]] = {
    89: {"fn": lambda n: n - 1,
         "reading": "'the closest smaller number than n' is n-1",
         "source": "the prompt's ordinary meaning",
         "conceptually_matches_prompt": False,
         "conceptual_note": ("the matching sentence is 'the number of integers "
                             "smaller than n' — extensionally identical to n-1 "
                             "on the whole domain n>=1, but a DIFFERENT concept. "
                             "No prose retarget routes this prompt there; it "
                             "counts as language reach, never as parser reach.")},
    96: {"fn": _n_divisors,
         "reading": "d(n), the count of divisors of n",
         "source": "the prompt's ordinary meaning",
         "conceptually_matches_prompt": True},
    224: {"fn": lambda n: bin(n).count("1"),
          "reading": "popcount(n) — the count of 1 bits",
          "source": "the prompt states it explicitly",
          "conceptually_matches_prompt": False},
    295: {"conceptually_matches_prompt": True,
          "fn": _aliquot,
          "reading": ("the prompt says 'all divisors' but the task's own three "
                      "asserts (8->7, 12->16, 7->1) define the PROPER-divisor "
                      "(aliquot) sum; the aliquot reading is the one the task "
                      "actually specifies and is used here"),
          "source": "the prompt + the task's own asserts, stated"},
    453: {"fn": _sum_even_divisors,
          "reading": "the sum of the even divisors of n",
          "source": "the prompt's ordinary meaning",
          "conceptually_matches_prompt": True},
}
WITNESS_SWEEP = list(range(1, 61))


def b_witness_sweep(in_language: Dict[str, Any]) -> Dict[str, Any]:
    """THE FIFTH-COINCIDENTAL-FIT SCREEN. Three rows is a small sample; a
    formula that reproduces them can still be a coincidence. Sweep each
    in-language formula against its task's reference relation and report the
    FIRST divergence."""
    rows = []
    for h in in_language["in_language_hits"]:
        tid = h["task_id"]
        ref = REFERENCE_RELATIONS.get(tid)
        term = ground_formula(h["formula"])
        if ref is None or term is None:
            rows.append({"task_id": tid, "formula": h["formula"],
                         "verdict": "UNVERIFIED_no_reference_relation_declared"})
            continue
        diverge = None
        all_div = []
        for n in WITNESS_SWEEP:
            got = eval_formula(term, n)
            want = ref["fn"](n)
            if got != want:
                if diverge is None:
                    diverge = {"n": n, "formula_gives": got,
                               "reference_gives": want}
                all_div.append(n)
        rows.append({
            "task_id": tid, "formula": h["formula"],
            "reference_reading": ref["reading"], "reference_source": ref["source"],
            "conceptually_matches_prompt": ref.get("conceptually_matches_prompt"),
            "conceptual_note": ref.get("conceptual_note"),
            "sweep": "n=1..60",
            "first_divergence": diverge,
            "n_divergences_in_sweep": len(all_div),
            "divergent_n": all_div[:20],
            "verdict": "coincidental_fit" if diverge else "witness_verified",
        })
    verified = [r["task_id"] for r in rows if r["verdict"] == "witness_verified"]
    coincidental = [r["task_id"] for r in rows if r["verdict"] == "coincidental_fit"]
    concept_ok = sorted(r["task_id"] for r in rows
                        if r["verdict"] == "witness_verified"
                        and r.get("conceptually_matches_prompt"))
    return {"per_task": rows,
            "witness_verified_AND_conceptually_matching_ids": concept_ok,
            "witness_verified_ids": sorted(verified),
            "coincidental_fit_ids": sorted(coincidental),
            "unverified_ids": sorted(r["task_id"] for r in rows
                                     if r["verdict"].startswith("UNVERIFIED"))}


# ---- what each in-language id would actually need -------------------------- #
# The import list for Seam B, in the A-ceiling's style: for every id the
# grammar can MEAN, the minimal missing piece is named AND its surface is
# tested live, so the claim "this one addition unlocks it" is never taken on
# the strength of its description.
CONSTRUCTION_PROBES: List[Dict[str, Any]] = [
    {"task_id": 96, "needed": "nothing beyond the mechanical retarget",
     "probe_surface": "find the number of divisors of n",
     "unit": "retarget only"},
    {"task_id": 295, "needed": "tolerate a leading quantifier ('all') in the "
                               "aggregator's {set} slot",
     "probe_surface": "the sum of divisors of n that are less than n",
     "blocked_surface": "return the sum of all divisors of n",
     "unit": "one slot-normalisation rule (or one seeded qualifier)"},
    {"task_id": 453, "needed": "'factors' as a member-form synonym of 'divisors'",
     "probe_surface": "find the sum of even divisors of n",
     "blocked_surface": "find the sum of even factors of n",
     "unit": "ONE member_form entry in the seed JSON"},
    {"task_id": 89, "needed": "a per-task clause equating 'the closest smaller "
                              "number than n' with 'the number of integers "
                              "smaller than n' — NOT a vocabulary item",
     "probe_surface": "number of integers smaller than n",
     "blocked_surface": "find the closest smaller number than n",
     "unit": "CHERRY-PICK — one clause, one task"},
    {"task_id": 224, "needed": "nothing — its language match is a coincidental "
                               "fit (see the witness sweep)",
     "probe_surface": "count the number of set bits in n",
     "unit": "n/a"},
]


def b_construction_probe() -> Dict[str, Any]:
    rows = []
    for p in CONSTRUCTION_PROBES:
        row = dict(p)
        row["probe_surface_parses"] = bool(cg.extract_function(p["probe_surface"]))
        row["probe_surface_candidates"] = cg.extract_function(p["probe_surface"])
        if "blocked_surface" in p:
            row["blocked_surface_parses"] = bool(
                cg.extract_function(p["blocked_surface"]))
        rows.append(row)
    return {"per_task": rows,
            "note": ("every 'needed' claim is verified in BOTH directions: the "
                     "blocked surface is shown NOT to parse and the repaired "
                     "surface is shown TO parse, by live invocation.")}


def b_surface_reach(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """(B-i) SURFACE reach, measured twice — raw prompt and mechanically
    retargeted prompt — and in BOTH directions: a non-empty parse is recorded,
    and then VERIFIED by executing the extracted formula on the task's own
    rows. A parse that is not verified is a false positive, not a hit."""
    out: Dict[str, Any] = {}
    for variant, xform in (("raw_prompt", lambda p: p),
                           ("mechanically_retargeted", mechanical_retarget)):
        parsed, genuine, rows_detail = [], [], []
        for t in tasks:
            tid = t["task_id"]
            text = xform(t["prompt"])
            try:
                cands = cg.extract_function(text)
            except Exception as exc:                     # loud, never silent
                rows_detail.append({"task_id": tid, "error": repr(exc)[:200]})
                continue
            if not cands:
                continue
            parsed.append(tid)
            rows = task_rows(t)["rows"]
            pairs = _unary_int_rows(rows)
            verdicts = []
            hit = None
            for c in cands:
                term = ground_formula(c)
                if term is None:
                    verdicts.append({"candidate": c, "verified": False,
                                     "why": "did_not_ground"})
                    continue
                if pairs is None:
                    verdicts.append({"candidate": c, "verified": False,
                                     "why": "task_is_not_unary_int"})
                    continue
                if any(abs(n) > MAX_EVAL_N for n, _ in pairs):
                    verdicts.append({"candidate": c, "verified": False,
                                     "why": "input_exceeds_MAX_EVAL_N"})
                    continue
                got = [eval_formula(term, n) for n, _ in pairs]
                want = [e for _, e in pairs]
                ok = got == want
                verdicts.append({"candidate": c, "verified": ok,
                                 "got": got, "expected": want})
                if ok:
                    hit = c
            if hit:
                genuine.append(tid)
            rows_detail.append({"task_id": tid, "input_text": text,
                                "candidates": cands, "verdicts": verdicts,
                                "genuine": hit is not None,
                                "prompt": t["prompt"]})
        out[variant] = {
            "n_parsed": len(parsed), "parsed_ids": sorted(parsed),
            "n_genuine": len(genuine), "genuine_ids": sorted(genuine),
            "detail": rows_detail,
        }
    out["retarget_rule"] = {
        "boilerplate_regex": _BOILERPLATE.pattern,
        "argument_phrases": _ARG_PHRASES,
        "guards": {
            "G1_never_rewrite_before_of":
                "'the number OF x' is the grammar's own number_of AGGREGATOR",
            "G2_delete_when_followed_by_index_var":
                "'an integer n' already binds n; substituting yields 'n n'",
        },
        "task_independent": True,
        "retarget_guards_provenance": (
            "the FIRST version of this function had neither guard and "
            "spuriously refuted task 96 ('find the number of divisors of a "
            "given integer' -> 'find n of divisors of n'), destroying the "
            "aggregator it was supposed to feed. A bug in the refuting "
            "direction is indistinguishable from an honest null; it was found "
            "by reading the retargeted TEXT, not the aggregate."),
    }
    return out


_CUE_WORDS = ["sum of", "number of", "squares of", "divisors", "even", "odd",
              "integers", "numbers", "factorial", "less than"]


def b_cherry_picked(tasks: List[Dict[str, Any]], surface: Dict[str, Any],
                    in_language: Dict[str, Any], witness: Dict[str, Any],
                    probe: Dict[str, Any]) -> Dict[str, Any]:
    """The CHERRY-PICKED readings, reported beside the honest ones so the
    inflation is visible rather than available (the A-ceiling's 5 -> 27 -> 60)."""
    # THE KEY TEST applied to B's import list (imported from Seam D's
    # leave-one-out null): an addition that fires on exactly one task is a
    # lookup key wearing a vocabulary item's name.
    per_addition_reach = {}
    for label, needle in (("member_form_synonym_factors", "factor"),
                          ("leading_quantifier_all", " all ")):
        ids = sorted(t["task_id"] for t in tasks if needle in t["prompt"].lower())
        per_addition_reach[label] = {
            "prompts_containing_the_cue": ids, "cross_task_reach": len(ids),
            "is_key_fires_on_one_task_only": len(ids) == 1}

    cue_hits: Dict[str, List[int]] = {}
    cue_ids = []
    for t in tasks:
        low = t["prompt"].lower()
        fired = [c for c in _CUE_WORDS if c in low]
        if fired:
            cue_ids.append(t["task_id"])
            for c in fired:
                cue_hits.setdefault(c, []).append(t["task_id"])
    seed_add = sorted(set(witness["witness_verified_ids"]) & {
        r["task_id"] for r in probe["per_task"]
        if r["unit"].startswith("ONE") or r["unit"].startswith("one")
        or r["unit"] == "retarget only"})
    return {
        "level_0_honest_parses_today_and_verified":
            {"n": surface["raw_prompt"]["n_genuine"],
             "ids": surface["raw_prompt"]["genuine_ids"]},
        "level_1_honest_after_mechanical_retarget_and_verified":
            {"n": surface["mechanically_retargeted"]["n_genuine"],
             "ids": surface["mechanically_retargeted"]["genuine_ids"]},
        "level_1b_after_two_blind_seed_additions":
            {"n": len(seed_add), "ids": seed_add,
             "additions": ["'factors' as a member-form synonym of 'divisors'",
                           "leading-quantifier tolerance in the {set} slot"],
             "why_this_is_still_honest":
                 "both additions are nameable without reading any task's "
                 "answer and each yields more than the task that motivated it "
                 "only if the population contains more such prose — which is "
                 "measured, not assumed, in per_addition_reach."},
        "level_2_language_ceiling_row_matched":
            {"n": len(in_language["in_language_ids"]),
             "ids": in_language["in_language_ids"],
             "caveat": "row-matched only; see level_2b"},
        "level_2b_language_ceiling_witness_verified":
            {"n": len(witness["witness_verified_ids"]),
             "ids": witness["witness_verified_ids"],
             "refuted_as_coincidental_fit": witness["coincidental_fit_ids"]},
        "level_3_cherry_picked_cue_word_present":
            {"n": len(cue_ids), "ids": sorted(cue_ids),
             "per_cue": {k: sorted(v) for k, v in sorted(cue_hits.items())},
             "why_this_is_not_a_ceiling":
                 "a cue word in the prose says nothing about whether the "
                 "grammar can MEAN the task; level 2 is the same population "
                 "screened by execution."},
        "per_addition_reach": per_addition_reach,
        "level_4_reductio":
            {"n": len(tasks),
             "recipe": "add one clause per task: {clause: <the prompt>, "
                       "formula: <that task's answer>} — the grammar is a "
                       "JSON list, so this is one line each, and it encodes "
                       "the test split."},
    }


def b_embedded_equation_route(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Route (b) of `extract_function` (each '=' RHS segment is a candidate
    arithmetic form) is the one UNBOUNDED route — it does not depend on the
    seed vocabulary at all. Measure how much of MBPP it can even see."""
    with_eq, arith_rhs = [], []
    for t in tasks:
        p = t["prompt"]
        segs = re.split(r"(?<![=<>!])=(?!=)", p)[1:]
        if not segs:
            continue
        with_eq.append(t["task_id"])
        for seg in segs:
            m = re.match(r"\s*([0-9n!\^\*\+\-\/\(\)\s\.]+)", seg)
            if m and re.search(r"n|\d", m.group(1)):
                arith_rhs.append(t["task_id"])
                break
    return {"prompts_containing_an_equals_sign": sorted(with_eq),
            "prompts_whose_rhs_looks_arithmetic": sorted(set(arith_rhs))}


# ========================================================================= #
#  CEILING C
# ========================================================================= #
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "given", "has", "have", "in", "into", "is", "it", "its", "of", "on", "or",
    "over", "same", "that", "the", "then", "this", "to", "under", "up", "was",
    "were", "which", "with", "within", "without", "between", "each", "not",
    "no", "so", "than", "there", "these", "they", "was", "will", "would",
}


def c_codebook() -> Dict[str, Any]:
    """RE-DERIVE the codebook's composition. The plan says '17
    ShapeSignature{kind:"math"}'; an earlier correction said 6 of 17. Neither
    is trusted — both are recomputed from the file."""
    with open(MATH_SHAPES_PATH) as f:
        seed = json.load(f)
    nodes = seed["nodes"]
    sig_nodes = [n for n in nodes if n["type"] == "ShapeSignature"]
    by_kind: Dict[str, List[str]] = {}
    for n in sig_nodes:
        by_kind.setdefault(n["attrs"].get("kind", "<none>"), []).append(
            n["attrs"]["name"])
    math_nodes = [{"name": n["attrs"]["name"],
                   "concept": n["attrs"].get("concept", ""),
                   "signature": n["attrs"]["signature"]}
                  for n in sig_nodes if n["attrs"].get("kind") == "math"]

    # Does ANY node carry the fields RecogniseShape needs?
    schema = {
        "n_nodes_total": len(nodes),
        "n_ShapeSignature": len(sig_nodes),
        "node_types": sorted({n["type"] for n in nodes}),
        "n_with_type_MetaShape": sum(1 for n in nodes if n["type"] == "MetaShape"),
        "n_with_keywords_attr": sum(1 for n in nodes if "keywords" in n["attrs"]),
        "n_edges": len(seed.get("edges", [])),
    }
    return {
        "counts_by_kind": {k: len(v) for k, v in sorted(by_kind.items())},
        "names_by_kind": {k: sorted(v) for k, v in sorted(by_kind.items())},
        "plan_claim_17_math": False,
        "measured_math_count": len(math_nodes),
        "measured_math_names": sorted(n["name"] for n in math_nodes),
        "math_nodes": math_nodes,
        "recognise_shape_schema_requirements": schema,
        "schema_fits_recognise_shape": (schema["n_with_type_MetaShape"] > 0
                                        and schema["n_with_keywords_attr"] > 0),
    }


def _split_words(s: str) -> List[str]:
    return [w for w in re.split(r"[^a-z0-9]+", (s or "").lower()) if w]


def _signature_tokens(sig: str) -> List[str]:
    try:
        tuples = json.loads(sig)
    except Exception:
        return []
    toks = []
    for tup in tuples:
        for tok in tup:
            if isinstance(tok, str) and tok.islower():
                toks.append(tok)
    return toks


def c_keyword_variants(math_nodes: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
    """Three keyword sets per math shape, ALL read MECHANICALLY off content
    already in the seed file. Nothing is authored here — which is what makes
    the KEY TEST meaningful: a per-task key cannot be smuggled in."""
    name_concept, relation_all, relation_content = {}, {}, {}
    for n in math_nodes:
        words = set(_split_words(n["name"])) | set(_split_words(n["concept"]))
        name_concept[n["name"]] = sorted(words - _STOPWORDS)
        toks = set(_signature_tokens(n["signature"]))
        relation_all[n["name"]] = sorted(toks)
        relation_content[n["name"]] = sorted(toks - _STOPWORDS)
    return {"name_concept": name_concept, "relation_all": relation_all,
            "relation_content": relation_content}


def _synthetic_manifest(keyword_sets: Dict[str, List[str]], vid: str) -> dict:
    """A MetaShape+ShapePrinciple manifest, IN MEMORY ONLY (never written to
    seeds/), in the exact node/edge shape `seeds/shape_vocabulary.json` uses,
    so the REAL Rust `recognise_meta_shape` scorer runs against it unmodified."""
    nodes, edges = [], []
    lid = 1
    for shape, kws in sorted(keyword_sets.items()):
        pid, mid = lid, lid + 1
        lid += 2
        nodes.append({"local_id": pid, "type": "ShapePrinciple",
                      "attrs": {"name": "arc6bc_%s_%s" % (vid, shape),
                                "keywords": kws}})
        nodes.append({"local_id": mid, "type": "MetaShape",
                      "attrs": {"name": "math:%s" % shape}})
        edges.append({"src": {"local": mid}, "type": "has_principle",
                      "tgt": {"local": pid}, "attrs": {}})
    return normalize_declarative(
        {"id": "arc6_bc_math_codebook_%s_SYNTHETIC" % vid,
         "version": "0.0.0-measurement-only", "depends_on": [],
         "nodes": nodes, "edges": edges})


def _run_recognise(prompts: Dict[int, str], keyword_sets: Dict[str, List[str]],
                   vid: str) -> Dict[str, Any]:
    manifest = _synthetic_manifest(keyword_sets, vid)
    wa = WorldAdapter()
    summary = wa.inner.load_seed_manifest(manifest, wa.agent)
    rows = []
    for tid in sorted(prompts):
        text = prompts[tid].lower()
        shape = wa.inner.evaluate(
            {"type": "RecogniseShape", "text": {"type": "Lit", "value": text}}, {})
        row = {"task_id": tid, "recognised_shape": shape}
        if shape:
            row["matched_keywords"] = sorted(
                "%s:%s" % (s, kw) for s, kws in keyword_sets.items()
                for kw in kws if kw and kw in text)
        rows.append(row)
    rec = [r for r in rows if r["recognised_shape"]]
    counts: Dict[str, int] = {}
    for r in rec:
        counts[r["recognised_shape"]] = counts.get(r["recognised_shape"], 0) + 1
    return {"variant": vid, "keyword_sets": keyword_sets,
            "seed_load": {k: v for k, v in summary.items()
                          if k in ("nodes", "edges", "rules_skipped")},
            "n_tasks": len(rows), "n_recognised": len(rec),
            "shape_counts": counts, "recognised_rows": rec}


def c_direct_load(prompts: Dict[int, str]) -> Dict[str, Any]:
    """THE LITERAL READING, measured not assumed: load
    `seeds/math_capability_shapes.json` AS IT IS and run `RecogniseShape`.

    A null here proves nothing on its own — a broken harness returns null too.
    So `c_positive_control` runs in the SAME process and MUST fire."""
    with open(MATH_SHAPES_PATH) as f:
        seed = json.load(f)
    wa = WorldAdapter()
    summary = wa.inner.load_seed_manifest(normalize_declarative(seed), wa.agent)
    fired = []
    for tid in sorted(prompts):
        shape = wa.inner.evaluate(
            {"type": "RecogniseShape",
             "text": {"type": "Lit", "value": prompts[tid].lower()}}, {})
        if shape:
            fired.append({"task_id": tid, "recognised_shape": shape})
    return {"seed_load": {k: v for k, v in summary.items()
                          if k in ("nodes", "edges", "rules_skipped")},
            "n_tasks": len(prompts), "n_recognised": len(fired),
            "recognised": fired,
            "reading": ("the seed file loaded verbatim, RecogniseShape run "
                        "against every test prompt")}


def c_positive_control(prompts: Dict[int, str]) -> Dict[str, Any]:
    """THE REFUTING-DIRECTION GUARD. A synthetic MetaShape whose keyword is a
    word that demonstrably occurs in MBPP prompts MUST fire. If it does not,
    every null in ceiling C is a harness bug, not a finding.

    The control's vocabulary is deliberately trivial and is NOT part of any
    measured variant — it exists only to prove the instrument works."""
    kws = {"control_divisor": ["divisor"], "control_string": ["string"]}
    res = _run_recognise(prompts, kws, "positive_control")
    expect_divisor = sorted(t for t, p in prompts.items() if "divisor" in p.lower())
    expect_string = sorted(t for t, p in prompts.items() if "string" in p.lower())
    return {"result": {k: v for k, v in res.items() if k != "recognised_rows"},
            "recognised_ids": sorted(r["task_id"] for r in res["recognised_rows"]),
            "expected_ids_by_substring":
                sorted(set(expect_divisor) | set(expect_string)),
            "control_fires": res["n_recognised"] > 0,
            "control_matches_substring_expectation":
                sorted(r["task_id"] for r in res["recognised_rows"]) ==
                sorted(set(expect_divisor) | set(expect_string))}


# ---- genuine/spurious classification -------------------------------------- #
# The bar (arc5's, reused verbatim): a hit is GENUINE only if the causing word
# is concept-specific AND the task's own structure independently exhibits that
# concept. Each verdict below is a researcher judgment, recorded WITH its
# reasoning so it can be checked rather than merely asserted.
CLASSIFICATION: Dict[Tuple[str, int], Dict[str, str]] = {
    ("name_concept", 283): {
        "verdict": "spurious",
        "reason": ("the causing word is 'self', inside 'the digit itSELF'. The "
                   "task compares each digit's frequency to the digit — no "
                   "self-reference at a smaller scale, which is what "
                   "self_similarity's signature (build NEW from PRIOR / refers "
                   "NEW to SELF / bound SELF by SCALE) actually says.")},
    ("relation_all", 101): {
        "verdict": "spurious",
        "reason": ("the one hit the mechanical glue rule cannot dismiss on its "
                   "own — its causing set is {'base','to'}, and 'base' is not "
                   "glue. Inspected by hand: identical to the relation_content "
                   "hit below, '1-BASEd indexing'.")},
    ("relation_content", 101): {
        "verdict": "spurious",
        "reason": ("'base' matches '1-BASEd indexing'. In the signature 'base "
                   "STOP' is a recursion BASE CASE; here it is an indexing "
                   "convention. Different sense of the same string.")},
    ("relation_content", 222): {
        "verdict": "spurious",
        "reason": ("'type' matches 'same data TYPE'. In the signature 'type "
                   "CONTACT is INVARIANT' is the topological type of a contact "
                   "between parts; here it is a Python runtime type check.")},
    ("relation_content", 237): {
        "verdict": "spurious",
        "reason": ("'map' matches 'MAPping each unique tuple to the number of "
                   "times it occurs'. That is dict construction; the signature's "
                   "'map PART to PART' + 'invariant PART under TRANSFORM' is "
                   "permutation invariance. The nearest thing to a genuine hit "
                   "in the whole sweep, and it still fails the second half of "
                   "the bar.")},
    ("relation_content", 286): {
        "verdict": "spurious",
        "reason": ("'repeat' matches 'formed by REPEATing the given array k "
                   "times'. Literal array repetition is not an invariance "
                   "claim; the task is a maximum-subarray problem.")},
    ("relation_content", 395): {
        "verdict": "spurious",
        "reason": ("'repeat' matches 'first non-REPEATed character' — a "
                   "frequency check, and the word appears NEGATED.")},
    ("relation_content", 470): {
        "verdict": "spurious",
        "reason": ("'pairwise' matches 'PAIRWISE addition of neighboring "
                   "elements'. Arithmetic over adjacent pairs, not topological "
                   "contact between parts with an invariant type.")},
}
# `relation_all` is classified MECHANICALLY rather than one hit at a time: its
# keyword sets are the signature's grammatical glue, and a hit caused only by
# glue cannot be a recognition of anything. Exceptions are enumerated, never
# waved through.
_GLUE = {"to", "from", "by", "is", "into", "under", "between"}


def c_classify_hit(variant: str, task_id: int, shape: str, prompt: str,
                   matched: List[str]) -> Dict[str, Any]:
    """Classify one hit. The causing keyword is the one belonging to the
    WINNING shape; the verdict and its reason are recorded per hit."""
    causing = [m for m in matched if m.split(":", 1)[0] == shape.split(":", 1)[-1]]
    words = {c.split(":", 1)[1] for c in causing}
    row = {"variant": variant, "task_id": task_id, "shape": shape,
           "prompt": prompt, "matched_keywords": matched,
           "causing_keywords_for_winning_shape": causing}
    hand = CLASSIFICATION.get((variant, task_id))
    if hand:
        row.update(hand)
        row["classified_by"] = "hand_inspection"
    elif variant == "relation_all":
        only_glue = bool(words) and words <= _GLUE
        row["verdict"] = "spurious" if only_glue else "spurious_needs_inspection"
        row["reason"] = ("caused only by closed-class glue %s carried in the "
                         "relation signature" % sorted(words)) if only_glue else \
            ("causing words %s include a non-glue token — enumerated as an "
             "exception rather than waved through" % sorted(words))
        row["classified_by"] = "mechanical_glue_rule"
        row["causing_words_are_glue_only"] = only_glue
    else:
        row["verdict"] = "UNCLASSIFIED"
        row["classified_by"] = "none"
    return row


def c_key_test(hits: List[Dict[str, Any]], prompts: Dict[int, str]) -> Dict[str, Any]:
    """THE KEY TEST (imported from Seam D's leave-one-out null): a cue that
    fires on exactly ONE task is a lookup key, not a recognition. For every
    causing keyword, count how many of the 257 prompts contain it, and flag
    any that carries verbatim prompt text."""
    rows = []
    for h in hits:
        for ck in h["causing_keywords_for_winning_shape"]:
            kw = ck.split(":", 1)[1]
            reach = sorted(t for t, p in prompts.items() if kw in p.lower())
            rows.append({"task_id": h["task_id"], "shape": h["shape"],
                         "keyword": kw, "cross_task_reach": len(reach),
                         "is_key_fires_on_one_task_only": len(reach) == 1,
                         "verbatim_prompt_substring_of_len_ge_12": len(kw) >= 12})
    return {"per_causing_keyword": rows,
            "n_keys": sum(1 for r in rows if r["is_key_fires_on_one_task_only"]),
            "note": ("all three variants' keywords are derived MECHANICALLY "
                     "from the seed file, so a per-task key is structurally "
                     "impossible here; the test is run anyway, and it is the "
                     "test the CHERRY-PICKED reading must survive.")}


# The SEMANTIC ceiling for C: which of the 257 tasks would a person say
# genuinely exhibit one of the SIX math concepts? Named by concept, then
# screened by a hand-written cue vocabulary (which is exactly the cherry-pick
# — it is authored AFTER reading the population, and that is stated).
_SEMANTIC_CUES = {
    "symmetry": ["palindrome", "symmetr", "reverse", "invariant", "mirror"],
    "self_similarity": ["recursive", "recursion", "fractal", "self-similar"],
    "fractal": ["fractal"],
    "phi_bounded_recursion": ["fibonacci", "golden ratio", "phi"],
    "curvature": ["curvature", "angle", "turn", "heading", "rotate"],
    "topology": ["topolog", "connected component", "adjacen", "neighbor",
                 "neighbour"],
}
# THE SAME FAILURE MODE, IN MY OWN INSTRUMENT. The cue "turn" above matches
# "reTURNs" in 29 MBPP prompts. It is left in place, and repaired separately,
# because a cherry-picked ceiling that collapses under the exact collision it
# was built to expose is the most useful thing this pass produces.
_SEMANTIC_CUES_REPAIRED = {
    "symmetry": ["palindrome", "symmetr", "reverse", "mirror", "invariant"],
    "self_similarity": ["fractal", "self-similar", "recursion"],
    "fractal": ["fractal"],
    "phi_bounded_recursion": ["fibonacci", "golden ratio"],
    "curvature": ["curvature", "angle", "rotate", "clockwise", "heading"],
    "topology": ["topolog", "connected component", "adjacen", "neighbor",
                 "neighbour"],
}
# Hand audit of the REPAIRED pass: does the task's structure actually
# instantiate that shape's SIGNATURE (not merely its name)? Researcher
# judgment, recorded with its reasoning.
_SEMANTIC_AUDIT = {
    (100, "symmetry"): ("genuine", "a palindrome IS invariance under the "
                        "reversal transform — the signature's 'invariant PART "
                        "under TRANSFORM' holds literally"),
    (56, "symmetry"): ("spurious", "uses the reverse of a number as an operand; "
                       "asserts no invariance"),
    (131, "symmetry"): ("spurious", "APPLIES a reversal to a sub-sequence; a "
                        "transform performed, not an invariance claimed"),
    (456, "symmetry"): ("spurious", "same: reversal applied, not asserted"),
    (124, "curvature"): ("spurious", "arg(z) of a complex number is not an "
                         "accumulated heading over advancing turns"),
    (293, "curvature"): ("spurious", "'right ANGLEd triangle' — the task is "
                         "Pythagoras; no turn is accumulated into a heading"),
    (458, "curvature"): ("spurious", "'rect-ANGLE-' — a substring collision "
                         "inside the word 'rectangle', in MY OWN repaired cue "
                         "set, on the second attempt"),
    (291, "topology"): ("spurious", "adjacency constraint in a counting DP; no "
                        "invariant contact TYPE between parts"),
    (470, "topology"): ("spurious", "arithmetic over adjacent pairs; same"),
}


def c_semantic_ceiling(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The CHERRY-PICKED ceiling for C, stated so the inflation is visible:
    if a person hand-authors an algorithmic keyword list per math shape AFTER
    reading the population, how many tasks does each shape claim? Every hit is
    then asked the actionability question: does the codebook carry ANY payload
    (constraint / relaxation / IR template) behind the label?"""
    per_shape: Dict[str, List[Dict[str, Any]]] = {}
    claimed: set = set()
    for shape, cues in sorted(_SEMANTIC_CUES.items()):
        rows = []
        for t in tasks:
            low = t["prompt"].lower()
            fired = [c for c in cues if c in low]
            if fired:
                rows.append({"task_id": t["task_id"], "cues": fired,
                             "prompt": t["prompt"]})
                claimed.add(t["task_id"])
        per_shape[shape] = rows
    # SECOND PASS — repaired cues, then a hand audit of every hit.
    repaired: List[Dict[str, Any]] = []
    for shape, cues in sorted(_SEMANTIC_CUES_REPAIRED.items()):
        for t in tasks:
            low = t["prompt"].lower()
            fired = [c for c in cues if c in low]
            if not fired:
                continue
            verdict, why = _SEMANTIC_AUDIT.get(
                (t["task_id"], shape), ("UNAUDITED", ""))
            repaired.append({"task_id": t["task_id"], "shape": shape,
                             "cues": fired, "prompt": t["prompt"],
                             "verdict": verdict, "reason": why})
    genuine = sorted({r["task_id"] for r in repaired if r["verdict"] == "genuine"})

    with open(MATH_SHAPES_PATH) as f:
        seed = json.load(f)
    payload_keys = sorted({k for n in seed["nodes"] for k in n["attrs"]})
    return {
        "repaired_cues": _SEMANTIC_CUES_REPAIRED,
        "repaired_pass_hits": repaired,
        "repaired_pass_n_hits": len(repaired),
        "hand_audited_genuine_ids": genuine,
        "hand_audited_genuine_n": len(genuine),
        "naive_cue_bug": ("the first pass's curvature cue 'turn' matches "
                          "'reTURNs' — 29 of its 31 claimed ids. My own "
                          "cherry-picked instrument reproduced the exact "
                          "substring-collision failure it was built to expose."),
        "authored_cues": _SEMANTIC_CUES,
        "authored_after_reading_the_population": True,
        "per_shape_claimed": {k: [r["task_id"] for r in v]
                              for k, v in per_shape.items()},
        "per_shape_detail": per_shape,
        "union_claimed_ids": sorted(claimed),
        "n_union_claimed": len(claimed),
        "codebook_attr_keys": payload_keys,
        "codebook_carries_a_synthesis_payload": bool(
            {"constraint", "relaxation", "template", "ir", "mechanism_steps"}
            & set(payload_keys)),
        "actionability_note": (
            "Even a genuine recognition supplies only a LABEL: the "
            "ShapeSignature nodes carry name/kind/concept/faculty/signature "
            "and nothing else. No constraint, no relaxation family, no IR "
            "template. A label with no payload cannot change what the "
            "enumerator does."),
    }


# ========================================================================= #
#  driver
# ========================================================================= #
def compute_everything() -> Dict[str, Any]:
    tasks = load_test_tasks()
    prompts = {t["task_id"]: t["prompt"] for t in tasks}

    vocab = b_vocabulary()
    language = b_enumerate_language()
    in_language = b_in_language(tasks, language)
    witness = b_witness_sweep(in_language)
    probe = b_construction_probe()
    surface = b_surface_reach(tasks)
    eqroute = b_embedded_equation_route(tasks)
    cherry = b_cherry_picked(tasks, surface, in_language, witness, probe)

    codebook = c_codebook()
    direct = c_direct_load(prompts)
    control = c_positive_control(prompts)
    kwsets = c_keyword_variants(codebook["math_nodes"])
    variants = {}
    all_hits: List[Dict[str, Any]] = []
    for vid in ("name_concept", "relation_all", "relation_content"):
        res = _run_recognise(prompts, kwsets[vid], vid)
        for r in res["recognised_rows"]:
            all_hits.append(c_classify_hit(vid, r["task_id"],
                                           r["recognised_shape"],
                                           prompts[r["task_id"]],
                                           r.get("matched_keywords", [])))
        variants[vid] = res
    informative = [h for h in all_hits if h["variant"] != "relation_all"]
    keytest = c_key_test(informative, prompts)
    semantic = c_semantic_ceiling(tasks)
    verdicts: Dict[str, int] = {}
    for h in all_hits:
        verdicts[h["verdict"]] = verdicts.get(h["verdict"], 0) + 1
    genuine = sorted({h["task_id"] for h in all_hits if h["verdict"] == "genuine"})
    glue_exceptions = [h for h in all_hits
                       if h["verdict"] == "spurious_needs_inspection"]

    return {
        "ceiling_b_extract_function": {
            "vocabulary": vocab,
            "language_enumeration": language,
            "language_ceiling": in_language,
            "witness_sweep": witness,
            "missing_construction_probe": probe,
            "surface_reach": surface,
            "embedded_equation_route": eqroute,
            "ceilings_honest_vs_cherry_picked": cherry,
        },
        "ceiling_c_math_shape_codebook": {
            "codebook": codebook,
            "direct_load_literal_reading": direct,
            "positive_control": control,
            "keyword_variants": variants,
            "all_hits_classified": all_hits,
            "verdict_counts": verdicts,
            "genuine_recognition_ids": genuine,
            "n_genuine_recognitions": len(genuine),
            "glue_rule_exceptions_needing_inspection": glue_exceptions,
            "informative_variant_hits": informative,
            "key_test": keytest,
            "semantic_cherry_picked_ceiling": semantic,
        },
        "n_test_tasks": len(tasks),
    }


def _stable(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


def main() -> None:
    t0 = time.time()
    stamp = provenance_stamp()
    print(stamp["line"])
    first = compute_everything()
    second = compute_everything()
    h1 = hashlib.sha256(_stable(first).encode()).hexdigest()
    h2 = hashlib.sha256(_stable(second).encode()).hexdigest()
    assert h1 == h2, "NON-DETERMINISTIC: twin runs disagree (%s vs %s)" % (h1, h2)

    inputs = {}
    for rel in INPUT_FILES:
        p = os.path.join(ROOT, rel)
        inputs[rel] = sha256_of(p) if os.path.exists(p) else None

    out = dict(first)
    out["determinism"] = {"twin_run_sha256": h1, "twin_runs_identical": True}
    out["engine_provenance"] = stamp
    out["input_file_sha256"] = inputs
    out["measured_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    out["elapsed_seconds"] = round(time.time() - t0, 1)
    out["scope"] = ("MEASUREMENT ONLY — nothing built, no seed/engine/adapter "
                    "source read for edit or modified, no git command run.")
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=str)
    print("wrote %s  (%.1fs, id_hash=%s)" % (OUT_PATH, out["elapsed_seconds"], h1[:16]))

    b = out["ceiling_b_extract_function"]
    c = out["ceiling_c_math_shape_codebook"]
    print("\n--- CEILING B ---")
    print(" vocabulary verified vs plan:", b["vocabulary"]["plan_quoted_verified"])
    print(" distinct semantics:", b["vocabulary"]["distinct_semantics_counts"])
    print(" language: %d surfaces -> %d formulas -> %d distinct FUNCTIONS" % (
        b["language_enumeration"]["n_generated_surfaces"],
        b["language_enumeration"]["n_distinct_formulas"],
        b["language_enumeration"]["n_distinct_FUNCTIONS"]))
    for k, v in b["ceilings_honest_vs_cherry_picked"].items():
        if isinstance(v, dict) and "n" in v:
            print("  %-58s n=%s %s" % (k, v["n"], v.get("ids", "")))
    print(" witness sweep:", b["witness_sweep"]["witness_verified_ids"],
          "coincidental:", b["witness_sweep"]["coincidental_fit_ids"])
    print(" per-addition reach:",
          {k: v["cross_task_reach"] for k, v in
           b["ceilings_honest_vs_cherry_picked"]["per_addition_reach"].items()})
    print("\n--- CEILING C ---")
    print(" codebook by kind:", c["codebook"]["counts_by_kind"])
    print(" direct literal load recognised:", c["direct_load_literal_reading"]["n_recognised"])
    print(" positive control fires:", c["positive_control"]["control_fires"],
          "n=", c["positive_control"]["result"]["n_recognised"])
    for vid, res in c["keyword_variants"].items():
        print("  %-18s recognised %3d/257  shapes=%s" % (
            vid, res["n_recognised"], res["shape_counts"]))
    print(" informative hits:", [(h["variant"], h["task_id"], h["shape"])
                                 for h in c["informative_variant_hits"]])
    print(" semantic cherry-picked union:", c["semantic_cherry_picked_ceiling"]["n_union_claimed"])


if __name__ == "__main__":
    main()
