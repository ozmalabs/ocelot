#!/usr/bin/env python
"""arc6_ceiling_ab — ARC 6 M0, ceilings A and B (measurement only, builds
nothing). See PROGRAM_SYNTHESIS_ARC6_PLAN.md sec 1 (Seams A/B) and sec 3 (M0).

STEP 0 — re-derive the CURRENT unreached-task population, live, rather than
trust results/mbpp_endgame.json (explicitly stale per the task brief) or any
prose-quoted number. Reuses the standing measurement driver
(scripts/mbpp_endgame_battery.py's own boot_full/run_arm/holdout_verdict —
imported, never re-implemented) against the current working tree (which
includes arc4 S2/S4/S6 and arc5 exact-first + MOVES, per `git log` on
domains/prog_synthesis.py / seeds/program_synthesis.json / domains/prog_moves.py
/ domains/prog_exact.py at the time this ran).

STEP 1 — CEILING A: enumerate the math tower's kernels (read the modules,
not the audit's prose); enumerate/classify the unreached tasks; match; and,
for classes with no matching kernel, name the missing kernel and estimate
import cost. This produces an IMPORT LIST ranked by tasks-unlocked per unit
of import work, per the plan's explicit framing (an import list, not a
go/no-go).

STEP 2 — CEILING B: reproduce scripts/oeis_extract_verify.py's 8/8 live (the
proof the propose->verify loop still works), then measure how many of the
257 MBPP TEST prompts are (i) parseable by extract_function/comprehend_recursive
TODAY (single-index sequence bedrock), (ii) parseable AFTER a *mechanical*
bedrock retarget from `k in 1..n` to the function's own named parameters
(estimated by analysis, not built), and (iii) needing genuine new vocabulary
(named, ranked by frequency).

Contamination: MBPP test-split `code` is read here ONLY for measurement
classification (the arc-2 histogram allowance, restated in the plan's
"Discipline" section) — never merged into a codebook, cue table, or learning
path. OEIS/HLE data never enters MBPP evaluation (this script never mixes
the OEIS 8/8 reproduction's output into any MBPP scoring).

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
  OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/arc6_ceiling_ab.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import mbpp_endgame_battery as meb          # noqa: E402 — the standing driver, reused not reimplemented
import mbpp_zero_shot_baseline as q0        # noqa: E402 — split_tasks (test = 11..510)
from domains import construction_grammar as cg   # noqa: E402 — extract_function / comprehend_recursive
from domains import compute_grounding as cgnd    # noqa: E402 — comprehend_computational_definition
from domains import reason                        # noqa: E402 — reason.solve
from domains import oeis_local as oe              # noqa: E402 — real OEIS dump

RESULTS_PATH = os.path.join(ROOT, "results", "arc6_ceiling_ab.json")
FIXTURE_PATH = meb.FIXTURE_PATH


# --------------------------------------------------------------------------- #
# STEP 0 — current unreached population, live.
# --------------------------------------------------------------------------- #
def derive_current_state() -> Dict[str, Any]:
    all_tasks = json.load(open(FIXTURE_PATH))
    splits = q0.split_tasks(all_tasks)
    test_tasks = splits["test"]
    assert len(test_tasks) == 257, "expected 257 test tasks, got %d" % len(test_tasks)

    t0 = time.time()
    arm = meb.run_arm("full", test_tasks)
    elapsed = time.time() - t0

    by_outcome: Dict[str, List[int]] = {}
    for r in arm["runnable_rows"]:
        by_outcome.setdefault(r["outcome"], []).append(r["task_id"])
    for r in arm["excluded_rows"]:
        by_outcome.setdefault(r["outcome"], []).append(r["task_id"])
    for k in by_outcome:
        by_outcome[k].sort()

    pass_ids = sorted(by_outcome.get("pass", []))
    unreached_ids = sorted(
        tid for outcome, ids in by_outcome.items() if outcome != "pass"
        for tid in ids
    )
    return {
        "n_test_tasks": len(test_tasks),
        "elapsed_seconds": round(elapsed, 2),
        "determinism": arm["determinism"],
        "aggregates": arm["aggregates"],
        "outcome_taxonomy": {k: {"n": len(v), "task_ids": v} for k, v in sorted(
            by_outcome.items(), key=lambda kv: -len(kv[1]))},
        "pass_ids": pass_ids,
        "n_pass": len(pass_ids),
        "unreached_ids": unreached_ids,
        "n_unreached": len(unreached_ids),
    }


# --------------------------------------------------------------------------- #
# STEP 1a — the tower's kernel inventory (read the code, not the audit prose).
# --------------------------------------------------------------------------- #
def kernel_inventory() -> List[Dict[str, Any]]:
    """Concrete, by-hand inventory. Every entry cites the exact function and
    module; verified against the source in the same session this script was
    written (see PROGRAM_SYNTHESIS_ARC6_M0_AB.md sec 'what was read')."""
    K = []

    def k(name, module, computes, inp, out, exact, notes=""):
        K.append({"name": name, "module": module, "computes": computes,
                  "input_type": inp, "output_type": out, "exact": exact,
                  "notes": notes})

    # --- domains/reason.py : general integer/number-theory tower ----------
    k("factorize", "domains/reason.py", "prime factorisation of an integer",
      "int", "dict[int,int] (prime->exponent)", True)
    k("totient", "domains/reason.py", "Euler's totient phi(n)",
      "int", "int", True)
    k("divisor_sum", "domains/reason.py", "sigma(n), sum of divisors",
      "int", "int", True)
    k("nth_fibonacci", "domains/reason.py", "n-th Fibonacci number",
      "int", "int", True)
    k("partition_count", "domains/reason.py", "p(n), integer partitions of n",
      "int", "int", True)
    k("hook_dim", "domains/reason.py",
      "dimension of the S_n irrep for a partition, via hook-length formula",
      "partition (list[int])", "int", True)
    k("count_where/sum_where/chain_sum/chain_bind", "domains/reason.py",
      "generic BINDER evaluators: free-variable iteration over a collection, "
      "re-solving a body Term per binding (fold/filter/map at the Term-tree "
      "level, evaluated in Python rather than the Rust DSL)",
      "Term-tree + bound collection", "any", True,
      "this is the same SHAPE as Fold/Filter/MapList already in the Rust "
      "synth_enumerate.rs op set — parallel implementation, not shared code")
    k("_matrix_rank_gf2 / _matrix_rank_q", "domains/reason.py",
      "matrix rank over GF(2) or over Q", "list[list[int|Fraction]]", "int", True)
    k("_smith_normal_form_factors", "domains/reason.py",
      "Smith normal form invariant factors of an integer matrix",
      "list[list[int]]", "list[int]", True)
    k("_integral_homology", "domains/reason.py",
      "integral homology groups of a chain complex from boundary matrices",
      "list of boundary matrices", "list[(free_rank, torsion list)]", True)
    k("_cup_product/_cup_i_product/_steenrod_square_cochain", "domains/reason.py",
      "Steenrod algebra cochain-level operations", "cochains", "cochains", True,
      "graduate topology; far outside MBPP's domain")
    k("_bg2_integral_homology_rank / _bg2_integral_torsion_2rank",
      "domains/reason.py", "mod-2 cohomology of BG2 (classifying space of G2)",
      "degree (int)", "int", True, "one hand-curated object family, not general")
    k("_spin_bordism_free_rank / _spin_bordism_torsion_2rank", "domains/reason.py",
      "spin bordism groups of BG2", "degree (int)", "int", True, "ditto")
    k("answer_within / solve_within / solve / reconsider / estimate_complexity",
      "domains/reason.py",
      "the dispatcher: NL question -> comprehended Term-tree -> op-cost "
      "estimate against a budget -> evaluate, with cheaper-alternative "
      "fallback ('reconsider') on overrun", "prose + optional bindings_factory",
      "typed value", True,
      "objects (matrices/groups) are supplied EXTERNALLY per question via a "
      "bindings_factory — this dispatcher does not itself extract objects "
      "from raw prose in the general case (see compute_grounding/construct_"
      "compute_* for the readers that do, narrowly)")

    # --- domains/comprehend_theorem.py + ground_reductions.py -------------
    k("comprehend_theorem_statement (comprehend_theorem.py)",
      "domains/comprehend_theorem.py",
      "parses 'a group with [property] has [invariant]=[value]' into a "
      "checkable ImplicationClause(antecedent: Callable, value), "
      "self-verified against KNOWN_OBJECTS/KNOWN_VALUES before trust",
      "prose theorem statement", "ImplicationClause (predicate + value)", True,
      "scoped to ONE family: group-invariant theorems over free products. "
      "No construction for a property of a PROGRAM's I/O relation "
      "(permutation-invariance, monotonicity, idempotence) — confirmed by "
      "reading seeds/theorem_constructions.json's 6 statement_forms/10 "
      "property_modifiers/4 invariant_atoms, zero of which mention "
      "functions, arguments, or programs")

    # --- domains/compute_grounding.py + construction_grammar.py -----------
    k("comprehend_computational_definition", "domains/compute_grounding.py",
      "composes a prose definition ('the lcm of a and b is a*b/gcd(a,b)') "
      "into a Term-tree over held primitives (gcd/times/div/mod/divisor_sum) "
      "and evaluates via reason.solve; ABSTAINS if an operand is not itself "
      "computational", "prose definition + optional bound n", "typed value", True)
    k("extract_function (route a: flat clause)", "domains/construction_grammar.py",
      "OEIS-style prose 'a(n) = f(n)' -> candidate closed-form RHS via a flat "
      "clause match", "prose", "Term-tree (closed form)", True)
    k("extract_function (route b: embedded '=' segment)",
      "domains/construction_grammar.py",
      "parses an embedded '=' segment inside prose into a candidate RHS",
      "prose", "Term-tree", True)
    k("comprehend_recursive (route c, order-N compositional)",
      "domains/construction_grammar.py",
      "recursive descent over member-form / value-map / filter / aggregator "
      "constructions, e.g. 'sum of squares of divisors of n' = "
      "aggregator(sum) o value-map(square) o member-form(divisors-of-n)",
      "prose", "Term-tree (composed)", True,
      "single free variable n, member-forms indexed 1..n or over n's "
      "divisors/factors — NOT a multi-parameter function signature")

    # --- domains/construct_compute_*.py : 9 bounded-enumeration modules ---
    k("construct_compute_enumerations (S_n irreps, sum-of-squares reps, "
      "Aztec-diamond domino tilings)", "domains/construct_compute_enumerations.py",
      "exact, provably-finite enumeration per family, each family recognised "
      "by a hand-authored regex over the question stem", "prose stem (regex-matched)",
      "int (exact count)", True,
      "the ENUMERATION is general once the family is recognised; the "
      "RECOGNITION is a family-specific regex catalogue, not open-domain NLU")
    k("construct_compute_betti/_chain/_gendef/_graphs/_group_orders/"
      "_homotopy/_physchem/_pi1/_subgroups", "domains/construct_compute_*.py",
      "eight sibling bounded-enumeration families (Betti numbers, chain "
      "complexes, generic-definition counts, graph invariants, group orders, "
      "homotopy groups of small spaces, physical-chemistry basis-function "
      "counts, fundamental groups, subgroup counts)", "prose stem (regex-matched)",
      "typed value", True, "same regex-recognition caveat as above, per family")

    # --- domains/oeis_local.py ---------------------------------------------
    k("oeis_local.present/definition", "domains/oeis_local.py",
      "reads a real downloaded OEIS parquet dump and returns ground-truth "
      "sequence values for verification", "OEIS A-number", "list[int]", True,
      "verification oracle, not a solving kernel")

    # --- reason.py's CAPABILITIES table — the ACTUAL declared-oracle table --
    # (read directly from source, `domains/reason.py` line 884 on): this is
    # the ground truth for what a comprehended Term-tree can already reduce
    # to, and it is structurally the SAME shape Seam A proposes (a declared-
    # oracle table `ProgEval.CallExtern` can register against) — this table
    # is effectively a pre-existing prototype of exactly what Seam A asks
    # for, just living in the wrong interpreter.
    k("reason.CAPABILITIES['prime']", "domains/reason.py",
      "primality test (trial division, _isprime)", "int", "bool", True,
      "already a declared, named capability — a genuine standing kernel, "
      "not paraphrase")
    k("reason.CAPABILITIES['gcd'/'lcm']", "domains/reason.py",
      "math.gcd / math.lcm, wrapped as named capabilities", "(int,int)", "int", True)
    k("reason.CAPABILITIES['largest_prime_factor'/'prime_factors']",
      "domains/reason.py", "derived from _factorize", "int",
      "int / list[int]", True)
    k("reason.CAPABILITIES['divisor_count'/'divisor_sum'/'totient']",
      "domains/reason.py", "d(n)/sigma(n)/phi(n) from the SAME "
      "_factorize-based multiplicative-function machinery", "int", "int", True)
    k("reason.CAPABILITIES['factorial'/'even'/'odd'/'divides'/"
      "'plus'/'minus'/'times'/'div'(exact)/'mod'/comparisons]",
      "domains/reason.py", "the base arithmetic/parity/divisibility oracle "
      "set a comprehended definition composes over", "int(s)", "typed value", True,
      "'div' is EXACT (Fraction, reduces to int when whole) — pre-dates and "
      "agrees with arc5's own rational-domain landing")
    k("reason.CAPABILITIES['range_incl'/'cardinality'/'member'/'is_empty'/"
      "'intersection'/'are_disjoint']", "domains/reason.py",
      "eager collection ops (a concrete list-of-ints representation)",
      "list[int] / (list,list)", "typed value", True,
      "count_where/sum_where (the LAZY binder evaluators, separate from this "
      "eager table) are the ones structurally identical to Fold/Filter/"
      "MapList already in synth_enumerate.rs")
    k("_is_perfect_square", "domains/reason.py",
      "perfect-square test using math.isqrt", "int", "bool", True,
      "demonstrates math.isqrt is ALREADY imported and used in this exact "
      "module — an integer sqrt oracle is a zero-cost addition, not an import")
    k("_is_probably_prime", "domains/reason.py",
      "deterministic Miller-Rabin, n < 3.3e14", "int", "bool", True,
      "a SECOND, faster primality oracle already exists alongside _isprime "
      "(used above the trial-division cost threshold)")
    k("math.comb (stdlib, already imported and called)", "domains/reason.py",
      "binomial coefficient nCr — called internally at "
      "_steenrod_square_poly_coeff (line ~745, `math.comb(j, i) % 2`)",
      "(int,int)", "int", True,
      "math.comb is stdlib and is LITERALLY ALREADY CALLED in this file — "
      "registering it as a general-purpose oracle for nCr-shaped MBPP tasks "
      "costs a declaration, not an implementation")

    return K


# --------------------------------------------------------------------------- #
# STEP 1b/c — classify unreached tasks against the kernel inventory.
# --------------------------------------------------------------------------- #
_MATH_CLASS_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("number_theory_elementary",
     re.compile(r"\b(gcd|lcm|prime|factorial|fibonacci|divisor|factor|"
                r"perfect number|composite|coprime|digit sum|palindrome)\b", re.I)),
    ("combinatorics_counting",
     re.compile(r"\b(combination|permutation|choose|catalan|arrangement|"
                r"ways to|n choose|binomial)\b", re.I)),
    ("sqrt_trig_geometry",
     re.compile(r"\b(sqrt|square root|sin|cos|tan|degree|radius|circle|"
                r"triangle|volume|surface area|perimeter|hypotenuse|angle)\b", re.I)),
    ("matrix_linear_algebra",
     re.compile(r"\bmatrix|matrices|determinant|transpose\b", re.I)),
    ("group_or_abstract_algebra",
     re.compile(r"\bgroup\b|\bhomomorphism\b|\bpermutation group\b", re.I)),
    ("sequence_series",
     re.compile(r"\bseries\b|\bsequence\b|\bsum of first\b|\bnth term\b", re.I)),
]


def classify_task_math_shape(prompt: str, code: str) -> List[str]:
    hay = prompt + "\n" + (code or "")
    hits = [name for name, pat in _MATH_CLASS_PATTERNS if pat.search(hay)]
    return hits


def match_unreached_to_kernels(unreached_ids: List[int],
                                tasks_by_id: Dict[int, Dict[str, Any]],
                                kernels: List[Dict[str, Any]]
                                ) -> Dict[str, Any]:
    """COARSE PASS ONLY — a keyword classifier over the 222 unreached tasks,
    used to size which classes are even present. This is NOT the final
    match (see HAND_AUDIT below, which reads each hit's actual reference
    code and corrects every false positive this regex produces — e.g. the
    literal substring 'group' inside `m.group(0)` in task 440's code, or
    'factor' inside 'selecting one factor from each list' in task 308)."""
    rows = []
    class_counts: Dict[str, List[int]] = {}
    for tid in unreached_ids:
        t = tasks_by_id[tid]
        shapes = classify_task_math_shape(t["prompt"], t.get("code", ""))
        rows.append({"task_id": tid, "prompt": t["prompt"], "math_shapes": shapes})
        if not shapes:
            class_counts.setdefault("no_math_shape_detected", []).append(tid)
        for s in shapes:
            class_counts.setdefault(s, []).append(tid)
    for k in class_counts:
        class_counts[k].sort()
    return {"rows": rows, "class_counts": {k: {"n": len(v), "task_ids": v}
                                            for k, v in sorted(class_counts.items(),
                                                                key=lambda kv: -len(kv[1]))}}


# --------------------------------------------------------------------------- #
# HAND AUDIT — every coarse-pass hit read against its actual reference code
# (task brief: "read every one of the ... tasks' real reference solutions and
# prompts", the same discipline PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md sec 1 used
# for the class A-G taxonomy). This is the real (3) "match" the plan asks
# for; the regex above is only a recall net.
# --------------------------------------------------------------------------- #
HAND_AUDIT: Dict[int, Dict[str, Any]] = {
    # --- GENUINE kernel matches: a reason.py function already computes this,
    #     or the extract_function compositional grammar already expresses it.
    96: {"verdict": "genuine_match",
        "kernel": "reason.CAPABILITIES['divisor_count'] (_divisor_count)",
        "why": "'find the number of divisors of a given integer' IS d(n); "
               "_divisor_count(n) computes it exactly. Not reached today "
               "only because the prompt paraphrase ('of a given integer') "
               "doesn't literally contain the seeded clause phrase ('of n') "
               "extract_function's flat-clause route needs verbatim."},
    256: {"verdict": "adjacent_match",
        "kernel": "reason.CAPABILITIES['prime'] (_isprime) + the count_where "
                  "binder",
        "why": "'count of primes less than n' = count_where(1..n, isprime) — "
               "the PRIMITIVE (_isprime) and the BINDER (count_where) both "
               "already exist; the missing piece is composing them for a "
               "prompt phrased as an imperative task rather than an OEIS-"
               "style sequence definition."},
    244: {"verdict": "adjacent_match",
        "kernel": "math.isqrt, already imported+used by reason._is_perfect_"
                  "square", "why": "'next perfect square greater than N' = "
               "(isqrt(N)+1)**2 — the exact idiom reason.py already uses for "
               "a DIFFERENT question (testing perfect-squareness); isqrt "
               "itself is zero-cost (stdlib)."},
    453: {"verdict": "adjacent_match",
        "kernel": "reason.CAPABILITIES['divisor_sum'] / _factorize",
        "why": "'sum of even factors of n' needs a PARITY-FILTERED divisor "
               "sum; _factorize's prime-power decomposition is the exact "
               "machinery divisor_sum already uses, just not exposed with a "
               "parity filter."},
    420: {"verdict": "genuine_match_seam_b_named_gap",
        "kernel": "construction_grammar's compositional aggregator grammar "
                  "(extract_function route c)",
        "why": "'cube sum of first n even natural numbers' = "
               "sum{k in 1..n : (2k)^3} is EXACTLY the aggregator-o-valuemap-"
               "o-member-form-o-filter shape this grammar composes for "
               "'squares of' today — verified live: seeds/math_prose_"
               "constructions.json's own '_doc_no_cubes' key says CUBES IS "
               "DELIBERATELY NOT SEEDED (only 'squares_of' exists as a "
               "value-map) and names the exact acquisition path "
               "(construction_grammar.acquire_construction) that would close "
               "it — the single most precisely-named import on this list."},
    # --- adjacent: the PATTERN exists (a hand-built special case), not the
    #     general kernel; a standard, well-known algorithm would close it.
    260: {"verdict": "adjacent_pattern",
        "kernel": "reason._nth_fibonacci (a hard-coded 2-term linear "
                  "recurrence, fast-doubling)",
        "why": "Newman-Shanks-Williams a(n)=2a(n-1)+a(n-2) is the SAME "
               "shape as Fibonacci's a(n)=a(n-1)+a(n-2), just different "
               "coefficients — reason.py has the PATTERN but not a GENERIC "
               "linear-recurrence evaluator (only the one Fibonacci-specific "
               "closed form)."},
    300: {"verdict": "adjacent_missing_primitive",
        "kernel": "math.comb (present in reason.py, not exposed as an oracle)",
        "why": "the reference solution accumulates nCr(n,r)^2 — needs a "
               "general binomial-coefficient oracle; math.comb is already "
               "imported and called in this exact file for an unrelated "
               "purpose (Steenrod square coefficients mod 2)."},
    274: {"verdict": "adjacent_missing_primitive",
        "kernel": "math.comb (same as 300)",
        "why": "'sum of even-index binomial coefficients' = 2^(n-1) by a "
               "binomial-theorem identity; a general nCr oracle plus a "
               "held identity (or even brute summation over comb(n,k) for "
               "even k) would reach it."},
    67: {"verdict": "adjacent_different_object",
        "kernel": "reason._partition_count (a DIFFERENT combinatorial "
                  "object — integer partitions, not set partitions)",
        "why": "Bell numbers count partitions of a SET into non-empty "
               "blocks; reason.py's partition_count counts partitions of an "
               "INTEGER. Same combinatorics neighbourhood, different "
               "function; the reference solution's own triangle recurrence "
               "is a standard ~10-line DP, not implemented anywhere in the "
               "tower today."},
    # --- no kernel and no cheap adjacent one: named, not imported.
    163: {"verdict": "no_kernel_named_gap",
        "kernel": None,
        "why": "needs tan(); reason.py has NO trigonometric functions "
               "anywhere (confirmed: no sin/cos/tan in the CAPABILITIES "
               "table or module). Independently already named as arc5's "
               "own residual (PROGRAM_SYNTHESIS_ARC5_SUMMARY.md sec 3.2, "
               "'tan (163)')."},
    293: {"verdict": "no_kernel_named_gap", "kernel": None,
        "why": "needs sqrt of a SUM of two squares (a composite argument); "
               "reason.py's only sqrt is math.isqrt used for an integer "
               "perfect-square TEST, not a general (possibly irrational) "
               "sqrt oracle. Already named as arc5's own residual ('sqrt of "
               "a composite argument (293, 731)')."},
    124: {"verdict": "no_kernel_named_gap", "kernel": None,
        "why": "needs complex-number support / atan2; nothing in reason.py "
               "represents a complex number (the topology modules use "
               "cochains/simplices, an unrelated representation). A "
               "genuinely new, narrow (1-task) kernel."},
    # --- false positives: the coarse regex hit a substring, not the concept.
    440: {"verdict": "false_positive", "kernel": None,
        "why": "the regex matched literal 'group' inside `m.group(0)` in "
               "the reference CODE (a re.Match method call) — nothing to do "
               "with group theory."},
    308: {"verdict": "false_positive", "kernel": None,
        "why": "the regex matched 'factor' inside the PROMPT's own English "
               "('selecting one factor from each list', meaning a list "
               "element) — not number-theoretic factorisation. The task is "
               "a top-N cross-product selection, a list/sort problem."},
    100: {"verdict": "false_positive", "kernel": None,
        "why": "'palindrome' matched the number-theory bucket but the task "
               "is digit-string manipulation with an open-ended search loop "
               "— no reason.py kernel is relevant."},
    74: {"verdict": "false_positive", "kernel": None,
        "why": "'sequence' in the prompt refers to a general list/array "
               "pattern-matching task (bijection check via dicts/sets), not "
               "a mathematical sequence."},
    245: {"verdict": "false_positive", "kernel": None,
        "why": "'bitonic subsequence' is a dynamic-programming array problem "
               "(longest-increasing-then-decreasing sum), not a closed-form "
               "sequence the tower expresses."},
    414: {"verdict": "false_positive", "kernel": None,
        "why": "'sequence' again means 'list' here (checking membership "
               "overlap between two lists) — no mathematical content."},
    255: {"verdict": "false_positive", "kernel": None,
        "why": "the reference solution is one call to "
               "itertools.combinations_with_replacement — a standard-"
               "library call, not a derivation the math tower would supply."},
    12: {"verdict": "false_positive", "kernel": None,
        "why": "'matrix' matched, but the task is 'sort rows by their sum' "
               "— reason.py's matrix kernels (rank/Smith-normal-form) are "
               "irrelevant to this; needs a Sort-by-key list primitive "
               "(a synthesis-engine gap, not a math-tower gap)."},
    129: {"verdict": "false_positive", "kernel": None,
        "why": "'matrix' matched, but 'is this a magic square' needs row/"
               "col/diagonal sum comparisons — again irrelevant to rank/SNF."},
    14: {"verdict": "false_positive", "kernel": None,
        "why": "'volume' matched the geometry bucket, but l*b*h/2 is plain "
               "3-argument scalar arithmetic already inside the existing "
               "enumerator's op set — no tower kernel is needed; whatever "
               "keeps this unreached is a synthesis-engine question, out of "
               "this ceiling's scope."},
    17: {"verdict": "false_positive", "kernel": None,
        "why": "'perimeter' matched, but 4*a is trivial linear arithmetic."},
    171: {"verdict": "false_positive", "kernel": None,
        "why": "'perimeter' matched, but 5*a is trivial linear arithmetic."},
    441: {"verdict": "false_positive", "kernel": None,
        "why": "'surface area' matched, but 6*l*l is trivial arithmetic."},
}


def build_hand_audit_summary(unreached_ids: List[int]) -> Dict[str, Any]:
    by_verdict: Dict[str, List[int]] = {}
    for tid in unreached_ids:
        entry = HAND_AUDIT.get(tid)
        v = entry["verdict"] if entry else "not_audited_no_coarse_hit"
        by_verdict.setdefault(v, []).append(tid)
    for v in by_verdict:
        by_verdict[v].sort()
    return {
        "by_verdict": {v: {"n": len(ids), "task_ids": ids}
                       for v, ids in sorted(by_verdict.items(),
                                            key=lambda kv: -len(kv[1]))},
        "rows": {str(tid): entry for tid, entry in sorted(HAND_AUDIT.items())},
        "method": ("every coarse-pass regex hit (25 tasks) read against its "
                   "real prompt AND reference code by hand; "
                   "'not_audited_no_coarse_hit' = the 197 remaining "
                   "unreached tasks the coarse pass found no math-flavoured "
                   "keyword in at all — these are presumptively "
                   "list/string/control-flow tasks the math tower has no "
                   "claim on, not individually re-read (197 manual reads "
                   "was out of this M0 budget; flagged, not hidden)."),
    }


IMPORT_LIST = [
    {
        "rank": 1,
        "missing_kernel": "Register reason.py's EXISTING CAPABILITIES "
                           "(prime/isqrt/divisor_count/divisor_sum) as "
                           "ProgEval-declared oracles + add ONE parity-"
                           "filtered-sum composition",
        "tasks_unlocked": [96, 244, 256, 453],
        "n_tasks_unlocked": 4,
        "standard_algorithm": True,
        "adjacent_machinery": "ZERO new mathematics — every primitive "
                               "(_isprime, math.isqrt via _is_perfect_square, "
                               "_divisor_count, _factorize) is ALREADY "
                               "WRITTEN, exact, and (for the divisor "
                               "functions) already OEIS-verified by "
                               "scripts/oeis_extract_verify.py. This is pure "
                               "registration: declare the function in "
                               "ProgEval's oracle table so CallExtern can "
                               "reach it.",
        "exact_representable": True,
        "import_cost": "LOWEST of the ranking — literally a declaration, no "
                        "implementation. count_where/sum_where composition "
                        "(needed for 256/453) is the ONE piece of real work, "
                        "and it mirrors a shape (Filter/Fold over a range) "
                        "the Rust synth_enumerate.rs ALREADY implements "
                        "independently — reusing that instead of the Python "
                        "binder is the honestly cheaper of two equally-"
                        "exact routes.",
        "tasks_unlocked_per_unit_cost": "HIGHEST on this list",
    },
    {
        "rank": 2,
        "missing_kernel": "Add ONE value-map construction ('cubes_of') to "
                           "seeds/math_prose_constructions.json — a Seam-B "
                           "import, named by the seed's OWN documentation",
        "tasks_unlocked": [420],
        "n_tasks_unlocked": 1,
        "standard_algorithm": True,
        "adjacent_machinery": "the file's own '_doc_no_cubes' key already "
                               "explains this is deliberately deferred and "
                               "names the exact mechanism "
                               "(construction_grammar.acquire_construction) "
                               "that would close it — this is not a "
                               "discovery, it is reading a comment the "
                               "authors already left.",
        "exact_representable": True,
        "import_cost": "LOWEST — one JSON value-map entry, structurally "
                        "identical to the existing 'squares_of' entry "
                        "(replace v*v with v*v*v).",
        "tasks_unlocked_per_unit_cost": "HIGH on a single-task basis (cost "
                                        "is trivial even though n=1)",
    },
    {
        "rank": 3,
        "missing_kernel": "Register math.comb (nCr) as a ProgEval oracle",
        "tasks_unlocked": [274, 300],
        "n_tasks_unlocked": 2,
        "standard_algorithm": True,
        "adjacent_machinery": "math.comb is STDLIB and is LITERALLY ALREADY "
                               "IMPORTED AND CALLED in domains/reason.py "
                               "(line ~745, _steenrod_square_poly_coeff) for "
                               "an unrelated purpose. Registering it as a "
                               "general oracle costs a one-line declaration.",
        "exact_representable": True,
        "import_cost": "LOWEST — zero implementation, one declaration.",
        "tasks_unlocked_per_unit_cost": "VERY HIGH",
    },
    {
        "rank": 4,
        "missing_kernel": "A generic bounded linear-recurrence evaluator "
                           "(a(n) = c1*a(n-1) + c2*a(n-2) + ..., with base "
                           "cases) generalising reason._nth_fibonacci",
        "tasks_unlocked": [260],
        "n_tasks_unlocked": 1,
        "standard_algorithm": True,
        "adjacent_machinery": "reason._nth_fibonacci is the ONE hard-coded "
                               "instance of exactly this shape (fast-"
                               "doubling for a 2-term recurrence); "
                               "generalising it to arbitrary declared "
                               "coefficients is a standard, well-known "
                               "technique (matrix power, or plain memoised "
                               "recursion for MBPP-scale n).",
        "exact_representable": True,
        "import_cost": "LOW — one new function, no new Term/oracle-table "
                        "shape (fits the same 'declared extern' pattern).",
        "tasks_unlocked_per_unit_cost": "MEDIUM (narrow today, but the "
                                        "SHAPE recurs — any future linear-"
                                        "recurrence-defined MBPP task would "
                                        "be free once this lands)",
    },
    {
        "rank": 5,
        "missing_kernel": "A Bell-number (set-partition count) DP function",
        "tasks_unlocked": [67],
        "n_tasks_unlocked": 1,
        "standard_algorithm": True,
        "adjacent_machinery": "reason._partition_count is the SAME "
                               "combinatorics neighbourhood (integer "
                               "partitions) using the SAME DP-table style; "
                               "Bell numbers are a different (set-"
                               "partition) object needing their own "
                               "~10-line triangle recurrence (the task's "
                               "own reference solution already IS that "
                               "recurrence).",
        "exact_representable": True,
        "import_cost": "LOW — one new function, same style as an existing "
                        "one in the same module.",
        "tasks_unlocked_per_unit_cost": "MEDIUM-LOW (n=1, but a well-known, "
                                        "cheap algorithm)",
    },
    {
        "rank": 6,
        "missing_kernel": "trig functions (tan at minimum) as ProgEval "
                           "oracles / a new ExactFamily",
        "tasks_unlocked": [163],
        "n_tasks_unlocked": 1,
        "standard_algorithm": True,
        "adjacent_machinery": "NONE in reason.py (confirmed: no sin/cos/tan "
                               "anywhere in the module or its CAPABILITIES "
                               "table) — this is a genuine gap on BOTH "
                               "sides (the tower has no trig kernel; "
                               "prog_exact.py's ExactFamily catalogue has no "
                               "trig-composite family either). Already named "
                               "as arc5's own residual.",
        "exact_representable": ("PARTIALLY — tan(pi/s) for a general integer "
                                "s is cross-frame/irrational in general; "
                                "representable to a declared tolerance, not "
                                "exactly, without a symbolic-radical Value "
                                "type (does not exist)."),
        "import_cost": "MEDIUM — math.tan itself is free (stdlib), but "
                        "making the RESULT exact-representable in this "
                        "project's rational-domain sense needs either a "
                        "tolerance-carrying Value or accepting a float leaf "
                        "(a genuine, if narrow, exception to the exact-first "
                        "rung's own discipline).",
        "tasks_unlocked_per_unit_cost": "LOW (n=1, real new machinery "
                                        "needed, not just registration)",
    },
    {
        "rank": 7,
        "missing_kernel": "generic sqrt-of-a-composite-argument as an "
                           "ExactFamily (Pythagorean-triple-shaped: "
                           "sqrt(a^2+b^2))",
        "tasks_unlocked": [293],
        "n_tasks_unlocked": 1,
        "standard_algorithm": True,
        "adjacent_machinery": "reason.py's only sqrt is math.isqrt used for "
                               "an integer PERFECT-SQUARE TEST, not a "
                               "general (possibly irrational) sqrt oracle — "
                               "same 'no kernel on either side' shape as "
                               "trig above. Already named as arc5's own "
                               "residual ('sqrt of a composite argument "
                               "(293, 731)').",
        "exact_representable": "PARTIALLY, same caveat as trig above.",
        "import_cost": "MEDIUM, same shape as trig above.",
        "tasks_unlocked_per_unit_cost": "LOW (n=1)",
    },
    {
        "rank": 8,
        "missing_kernel": "complex-number support (atan2/cmath.phase) as a "
                           "ProgEval oracle",
        "tasks_unlocked": [124],
        "n_tasks_unlocked": 1,
        "standard_algorithm": True,
        "adjacent_machinery": "NONE — no complex-number representation "
                               "exists anywhere in reason.py (the topology "
                               "modules use cochains/simplices, an entirely "
                               "different representation).",
        "exact_representable": False,
        "import_cost": "MEDIUM (a new value representation, even if the "
                        "underlying math.atan2 call is free) for a SINGLE "
                        "task — the worst ratio on this list.",
        "tasks_unlocked_per_unit_cost": "LOWEST",
    },
    {
        "rank": None,
        "missing_kernel": "NOT RANKED — group-theoretic invariants via "
                           "comprehend_theorem (order/ends/cohomological "
                           "dimension)",
        "tasks_unlocked": [],
        "n_tasks_unlocked": 0,
        "standard_algorithm": False,
        "adjacent_machinery": "comprehend_theorem.py's parse-ground-emit-"
                               "self-verify MECHANISM is directly reusable; "
                               "its CONTENT (group-theory statement forms) "
                               "has NO matching unreached-MBPP-task class — "
                               "the one coarse-pass hit (task 440) is a "
                               "confirmed false positive (a `.group(0)` "
                               "regex-method-call substring, not group "
                               "theory).",
        "exact_representable": True,
        "import_cost": "N/A — importing this would be speculative content "
                        "with a MEASURED zero target, which the plan's own "
                        "scoping risk explicitly warns against ('importing "
                        "kernels indefinitely is unbounded work').",
        "tasks_unlocked_per_unit_cost": "N/A — do not import",
    },
    {
        "rank": None,
        "missing_kernel": "NOT RANKED — a new bounded-exact-enumeration "
                           "family per the construct_compute_*.py pattern, "
                           "speculative (no specific unreached task named)",
        "tasks_unlocked": [],
        "n_tasks_unlocked": 0,
        "standard_algorithm": True,
        "adjacent_machinery": "construct_compute_enumerations.py's own "
                               "documented pattern ('a family recogniser, "
                               "the same enumeration on each') is the "
                               "template — but every EXISTING family in "
                               "this 9-module set targets HLE-grade objects "
                               "(Grassmannians, twist-spun branched covers, "
                               "Grigorchuk-group subgroup counts) with NO "
                               "overlap in the 222-task unreached population "
                               "(confirmed: zero coarse-pass or hand-audit "
                               "hits map to any of these 9 modules).",
        "exact_representable": True,
        "import_cost": "LOW per hypothetical family, UNBOUNDED in "
                        "aggregate if pursued without a named target — the "
                        "plan's own named scoping risk. Listed here only to "
                        "record that it was considered and correctly not "
                        "ranked.",
        "tasks_unlocked_per_unit_cost": "N/A — do not import speculatively",
    },
]


# --------------------------------------------------------------------------- #
# STEP 2 — CEILING B.
# --------------------------------------------------------------------------- #
def _verify_one_oeis(seq_id: str, window: int = 12):
    """Byte-for-byte the same mechanism as scripts/oeis_extract_verify.py's
    own verify_one (reproduced inline here so this script has no import-time
    dependency on that one being unmodified — the MECHANISM under test is
    extract_function + comprehend_computational_definition + reason.solve,
    all imported live from the real modules, never re-implemented)."""
    d = oe.definition(seq_id)
    if d is None:
        return seq_id, None, "not in dump", []
    prose, values, offset = d["name"], d["values"], d["offset"]
    cands = cg.extract_function(prose)
    for cand in cands:
        comp = cgnd.comprehend_computational_definition("a(n) = %s" % cand)
        if not comp:
            continue
        term = comp["term"]
        ok, checked = True, 0
        for i, want in enumerate(values[:window]):
            n = offset + i
            try:
                got = reason.solve(term, {"n": n})
            except Exception:
                ok = False
                break
            if int(got) != int(want):
                ok = False
                break
            checked += 1
        if ok and checked >= 4:
            return seq_id, cand, prose, values[:8]
    return seq_id, None, prose, cands


def reproduce_oeis_extract_verify_live() -> Dict[str, Any]:
    """Reproduce scripts/oeis_extract_verify.py live (its own targets, its
    own mechanism) — confirms the propose-from-NL -> verify-by-execution
    loop still works before ceiling B reasons about its reach."""
    if not oe.present():
        return {"ok": False, "reason": "oeis parquet dump not present in this env"}
    targets = ["A000005", "A000010", "A000203", "A000027",
               "A000217", "A005843", "A000290", "A000142"]
    out = []
    for sid in targets:
        sid_, cand, prose, vals = _verify_one_oeis(sid)
        out.append({"a_number": sid, "prose": prose, "extracted_formula": cand,
                   "verified": cand is not None,
                   "sample_or_candidates": vals})
    n_ok = sum(1 for r in out if r["verified"])
    frontier = []
    for sid in ["A000045", "A000040"]:
        d = oe.definition(sid)
        _, cand, _, _ = _verify_one_oeis(sid)
        frontier.append({"a_number": sid, "prose": d["name"] if d else None,
                        "extracted_and_verified": cand is not None,
                        "expected": "None — recursive/no-closed-form, the "
                                    "named honest frontier"})
    return {"ok": True, "n_cases": len(targets), "n_verified_match": n_ok,
            "detail": out, "honest_frontier": frontier}


# --- extract_function's grammar, characterised for the (i)/(ii)/(iii) split -
def _prompt_signature_shape(prompt: str) -> Optional[str]:
    """Heuristic (LABELLED estimate, not a measured parse) for whether a
    prompt names a single running-index sequence ('the sum of the first n
    natural numbers') vs a multi-parameter function over NAMED slots
    ('given three numbers a, b, c, find the maximum'). Used only to size
    (ii) vs (iii); never fed back into extract_function itself."""
    single_index_cues = re.compile(
        r"\bfirst n\b|\bthe first \d+\b|\bnatural numbers\b|\bnth\b|"
        r"\bn-th\b|\bsum of .* numbers from\b|\bseries\b", re.I)
    if single_index_cues.search(prompt):
        return "single_index_sequence"
    return None


_MEMBER_FORM_CUES = re.compile(
    r"\bdivisors? of\b|\bfactors? of\b|\bdigits? of\b|\bmultiples? of\b|"
    r"\belements? of\b|\bnumbers? from \d+ to \d+\b|\bin the range\b", re.I)
_AGGREGATOR_CUES = re.compile(
    r"\bsum of\b|\bproduct of\b|\bcount of\b|\bnumber of\b|\bmaximum of\b|"
    r"\bminimum of\b|\baverage of\b", re.I)
_FILTER_CUES = re.compile(
    r"\beven\b|\bodd\b|\bprime\b|\bdivisible by\b|\bgreater than\b|"
    r"\bless than\b", re.I)
_OPERATOR_CUES = re.compile(
    r"\bsquare\b|\bcube\b|\bsquare root\b|\bfactorial\b|\breverse\b|\+|\-|"
    r"\*|/|\bmodul(o|us)\b", re.I)


def extract_function_grammar_probe(prompt: str, code: str) -> str:
    """Returns 'ok_today' / 'ok_after_retarget' / 'needs_new_vocab', with the
    (labelled) reasoning recorded by the caller. This function performs the
    real (i) check by actually calling extract_function (returns a list of
    candidate RHS strings — non-empty means the RAW MBPP prompt, as-is,
    already parses into a candidate formal form under the single-index-n
    bedrock); (ii)/(iii) are analysis, not execution — see the module
    docstring."""
    try:
        cands = cg.extract_function(prompt)
    except Exception:
        cands = []
    if cands:
        return "ok_today"
    # (ii) estimate: would the bedrock retarget (index -> named params) let
    # this parse? True iff the prompt's aggregator/member-form/filter/
    # operator vocabulary is entirely within the grammar's existing
    # constructions AND the function signature is recoverable from the
    # prompt/code (arity is small, params are named).
    has_agg = bool(_AGGREGATOR_CUES.search(prompt))
    has_member = bool(_MEMBER_FORM_CUES.search(prompt))
    has_filter = bool(_FILTER_CUES.search(prompt))
    has_op = bool(_OPERATOR_CUES.search(prompt))
    # crude arity estimate from the reference solution's def line.
    arity = None
    try:
        tree = ast.parse(code or "", mode="exec")
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                arity = len(node.args.args)
                break
    except Exception:
        pass
    if (has_agg or has_member or has_filter) and arity is not None and arity <= 3:
        return "ok_after_retarget"
    if has_op and arity is not None and arity <= 2 and not (has_agg or has_member):
        # a pure scalar-arithmetic composite over named params (e.g.
        # "double the input and add one") — bedrock retarget alone would
        # suffice since there is no member-form/aggregator/filter needed,
        # just re-pointing the bound variable at a parameter.
        return "ok_after_retarget"
    return "needs_new_vocab"


_MISSING_VOCAB_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("string_manipulation (concat/substring/case/split/replace, no "
      "aggregator-over-collection shape)",
     re.compile(r"\bstring\b|\bsubstring\b|\bcharacter\b|\buppercase\b|"
                r"\blowercase\b|\breplace\b|\bconcatenate\b", re.I)),
    ("dict_or_tuple_construction (build/merge a mapping or record, not a "
      "scalar aggregate)",
     re.compile(r"\bdictionary\b|\bdict\b|\btuple\b|\bkey-value\b|\bmerge\b", re.I)),
    ("sort_or_ranking (order a collection / find kth largest, no closed "
      "aggregator)",
     re.compile(r"\bsort\b|\bsorted\b|\border\b|\bkth\b|\brank\b", re.I)),
    ("conditional_selection (branch on a predicate over the whole input, "
      "not a per-element filter)",
     re.compile(r"\bif\b.*\belse\b|\bcheck if\b|\bwhether\b|\bvalid\b", re.I)),
    ("multi_step_procedure (the reference solution has a loop with mutated "
      "state across iterations — not a pure fold)",
     re.compile(r"\bwhile\b|\bswap\b|\bstep\b|\biteratively\b", re.I)),
    ("regex_or_pattern_match",
     re.compile(r"\bregex\b|\bpattern\b|\bmatch\b", re.I)),
]


def classify_missing_vocab(prompt: str, code: str) -> List[str]:
    hay = prompt + "\n" + (code or "")
    return [name for name, pat in _MISSING_VOCAB_PATTERNS if pat.search(hay)]


def ceiling_b(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    oeis_repro = reproduce_oeis_extract_verify_live()

    ok_today, ok_after_retarget, needs_new_vocab = [], [], []
    vocab_rows = []
    for t in tasks:
        tid = t["task_id"]
        prompt = t["prompt"]
        code = t.get("code", "")
        verdict = extract_function_grammar_probe(prompt, code)
        if verdict == "ok_today":
            ok_today.append(tid)
        elif verdict == "ok_after_retarget":
            ok_after_retarget.append(tid)
        else:
            needs_new_vocab.append(tid)
            missing = classify_missing_vocab(prompt, code)
            vocab_rows.append({"task_id": tid, "prompt": prompt,
                              "missing_constructions": missing or ["unclassified"]})

    missing_freq: Dict[str, int] = {}
    for row in vocab_rows:
        for m in row["missing_constructions"]:
            missing_freq[m] = missing_freq.get(m, 0) + 1
    missing_ranked = sorted(missing_freq.items(), key=lambda kv: -kv[1])

    return {
        "oeis_extract_verify_live_reproduction": oeis_repro,
        "grammar_vocabulary": {
            "clause_constructions": 10, "member_forms": 5, "value_maps": 2,
            "aggregators": 4, "filters": 4,
            "operators_as_named_by_the_plan": 27,
            "CORRECTION (read seeds/math_prose_constructions.json directly)":
                "the plan's own '27 operators' figure is real but does NOT "
                "describe extract_function's ARITHMETIC vocabulary for "
                "MBPP-shaped prompts. Every one of the 27 entries has "
                "'held_runnable': false and is a group-theory/topology "
                "INVARIANT-NAME operator (kernel_of, image_of, rank_of, "
                "euler_characteristic_of, homology_of, betti_number_of, "
                "dimension_of, fundamental_group_of, genus_of) — this is "
                "comprehend_theorem's asked-invariant-TYPING vocabulary "
                "(for HLE-style theorem/invariant prose), a DIFFERENT "
                "construction family that happens to share this JSON file. "
                "extract_function's actual composable arithmetic surface "
                "for a sequence-in-n is only: 10 clauses + 5 member-forms + "
                "2 value-maps (squares_of is the ONLY non-trivial one — "
                "'cubes_of' is explicitly, self-documentedly absent, see "
                "the '_doc_no_cubes' key) + 4 filters + 4 aggregators. This "
                "narrower true vocabulary is what (i)/(ii)/(iii) below are "
                "measured against.",
            "source": "seeds/math_prose_constructions.json, read directly "
                       "(not the plan's own prose, per the task's 'be "
                       "concrete — read the code' instruction)",
        },
        "i_ok_today": {"n": len(ok_today), "task_ids": sorted(ok_today),
                       "method": "MEASURED — extract_function(prompt) called "
                                 "live and returned a non-empty candidate list",
                       "HONEST CAVEAT (hand-checked, not just counted)":
                           "all 3 hits (160, 267, 270) are DEGENERATE partial "
                           "matches, not genuine correct extractions: 160's "
                           "prompt contains a literal 'ax + by = n' and route "
                           "(b)'s embedded-'=' regex grabs the trailing 'n' as "
                           "a bogus one-token 'formula'; 267 ('sum of the "
                           "squares of the first n odd natural numbers') "
                           "partially matches the 'squares_of' value-map but "
                           "the aggregator+member-form composition around it "
                           "fails, leaving the bare fragment 'n*n'; 270 "
                           "similarly yields the fragment '2*n'. NONE of the "
                           "3 would evaluate to the task's correct answer. "
                           "The honest reading of (i) is closer to 0 GENUINE "
                           "matches and 3 LOOSE (non-empty-candidate-list) "
                           "matches — both numbers are reported, neither "
                           "hidden."},
        "ii_ok_after_retarget": {"n": len(ok_after_retarget),
                                 "task_ids": sorted(ok_after_retarget),
                                 "method": "ESTIMATED — labelled analysis: the "
                                           "prompt/reference solution's "
                                           "vocabulary (aggregator/member-"
                                           "form/filter/operator cues) is "
                                           "within the grammar's existing "
                                           "construction set AND the "
                                           "reference solution's arity is <=3 "
                                           "(so a signature-parameter bedrock "
                                           "is plausible); NOT built or run "
                                           "through a retargeted parser"},
        "iii_needs_new_vocab": {"n": len(needs_new_vocab),
                                "task_ids": sorted(needs_new_vocab),
                                "rows": vocab_rows,
                                "missing_construction_ranked": missing_ranked},
        "assumptions": [
            "arity estimated by counting the reference solution's top-level "
            "function parameters via ast — this reads test-split `code`, "
            "permitted for MEASUREMENT classification only (arc-2 histogram "
            "allowance), never fed into a codebook/cue table.",
            "(ii) is a heuristic textual-cue classifier, not a parser; it is "
            "almost certainly an OVER-estimate in some cases (a prompt can "
            "mention 'sum of' without the underlying computation being a "
            "clean fold) and an UNDER-estimate in others (a prompt with no "
            "cue word can still be aggregator-shaped) — reported as a "
            "labelled estimate for exactly this reason.",
            "the (i)/(ii) boundary is conservative: extract_function is "
            "called with the RAW prompt text (its real, current single-"
            "index-sequence-biased grammar), so (i) undercounts nothing — "
            "every genuine current success is captured by direct execution.",
        ],
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    print("=== STEP 0: re-deriving current unreached-task population (live) ===")
    state = derive_current_state()
    print("  n_pass=%d n_unreached=%d (of %d test tasks), elapsed=%.1fs, "
          "determinism.identical=%s" %
          (state["n_pass"], state["n_unreached"], state["n_test_tasks"],
           state["elapsed_seconds"], state["determinism"]["identical"]))

    all_tasks = json.load(open(FIXTURE_PATH))
    tasks_by_id = {t["task_id"]: t for t in all_tasks}  # code present here — measurement-only read

    print("=== STEP 1: CEILING A — kernel inventory + match + import list ===")
    kernels = kernel_inventory()
    match = match_unreached_to_kernels(state["unreached_ids"], tasks_by_id, kernels)
    print("  kernels inventoried: %d" % len(kernels))
    for cname, d in match["class_counts"].items():
        print("  coarse pass: %-32s n=%d" % (cname, d["n"]))
    hand_audit = build_hand_audit_summary(state["unreached_ids"])
    print("  --- hand audit (every coarse hit read against real code) ---")
    for v, d in hand_audit["by_verdict"].items():
        print("  %-32s n=%d %s" % (v, d["n"], d["task_ids"] if d["n"] <= 6 else ""))

    print("=== STEP 2: CEILING B — extract_function reach ===")
    test_tasks_stripped = json.load(open(FIXTURE_PATH))
    test_split = q0.split_tasks(test_tasks_stripped)["test"]
    # re-attach code for THIS measurement's classification only (contamination
    # rule: measurement-only, never merged into a codebook).
    test_with_code = [tasks_by_id[t["task_id"]] for t in test_split]
    b = ceiling_b(test_with_code)
    print("  (i) ok_today=%d  (ii) ok_after_retarget=%d  (iii) needs_new_vocab=%d"
          % (b["i_ok_today"]["n"], b["ii_ok_after_retarget"]["n"],
             b["iii_needs_new_vocab"]["n"]))
    print("  oeis_extract_verify live reproduction: %s (%d/%d match)" %
          (b["oeis_extract_verify_live_reproduction"].get("ok"),
           b["oeis_extract_verify_live_reproduction"].get("n_verified_match", 0),
           b["oeis_extract_verify_live_reproduction"].get("n_cases", 0)))

    artifact = {
        "_README": ("PROGRAM_SYNTHESIS_ARC6_PLAN.md M0, ceilings A and B. "
                    "Measurement only — no engine/seed/adapter source touched. "
                    "State re-derived LIVE via mbpp_endgame_battery.run_arm; "
                    "results/mbpp_endgame.json was NOT used (stale per the "
                    "task brief)."),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "environment": {"python": sys.version, "cwd": ROOT},
        "current_state": state,
        "ceiling_a": {
            "kernel_inventory": kernels,
            "coarse_pass_match": match,
            "hand_audit": hand_audit,
            "import_list_ranked": IMPORT_LIST,
        },
        "ceiling_b": b,
    }
    determinism_hash = hashlib.sha256(
        json.dumps({"pass_ids": state["pass_ids"],
                   "unreached_ids": state["unreached_ids"]},
                  sort_keys=True).encode()).hexdigest()
    artifact["current_state"]["cross_run_id_hash"] = determinism_hash

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(artifact, f, indent=2, default=meb._json_default)
    print("wrote %s" % RESULTS_PATH)


if __name__ == "__main__":
    main()
