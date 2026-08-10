"""arc6_a_ceiling — Seam A's A-CEILING as an IMPORT LIST, measured.

MEASUREMENT ONLY. Nothing in `seeds/`, `runners/`, `domains/`, or any
adapter is read-for-edit or touched. This script builds nothing; it
INVOKES candidate kernels live and checks them against each task's OWN
example rows.

What this measures
------------------
`PROGRAM_SYNTHESIS_ARC6_PLAN.md` sec 3 M0 asks for the A-ceiling as "an
import list ranked by tasks-unlocked per unit of import work", NOT a
go/no-go.  `RESEARCH_IMPORT_SOURCES.md` established SymPy as THE import
vehicle (installed, BSD-3-Clause, 107/125 invoked ntheory/combinatorics
results exact, ZERO inexact) and established the architectural filter:
`prog_eval.rs`'s own doc comment forbids shelling out, so an oracle must
be an in-process call.  SymPy is in-process.

Population: the 60 ids `PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md` sec 3 left as
`gapped:enumerate_failed` out of its 85-task bucket, derived here from
`results/arc4_backward_probe.json` (the bucket) minus S4's own three
moved-id lists -- never retyped as a literal.

THE CONTAMINATION TRAP THIS SCRIPT IS BUILT TO AVOID
----------------------------------------------------
If each unreached task is mapped to the kernel that solves THAT task, and
the oracle table is that hand-picked per-task set, then the oracle table
ENCODES THE TEST-SPLIT ANSWERS and every later "conversion" is a
coincidental fit by construction.  Four coincidental fits have already
been caught in this project.  So:

  * the import unit is a MODULE/FAMILY (`sympy.ntheory`, ...), never a
    callable chosen because it happens to answer one task;
  * every family carries an explicit `registered_blind` justification --
    would a person register this WITHOUT having seen the test split?
  * both ceilings are reported: HONEST (module registration) and
    CHERRY-PICKED (one bespoke kernel per task).  The gap is a finding.

MBPP test-split `code` is read for MEASUREMENT classification only (the
standing rule).  No prompt text and no reference code enters any
codebook, cue vocabulary, or taught shape -- this script writes exactly
two artefacts, `results/arc6_a_ceiling.json` and its own stdout.

Run:
    OZMA_NO_LLM=1 python scripts/arc6_a_ceiling.py
"""

from __future__ import annotations

import ast
import datetime as _dt
import hashlib
import inspect
import json
import math
import os
import sys
import traceback
import warnings

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
BACKWARD_PROBE = os.path.join(ROOT, "results", "arc4_backward_probe.json")
CEILING_AB = os.path.join(ROOT, "results", "arc6_ceiling_ab.json")
OUT = os.path.join(ROOT, "results", "arc6_a_ceiling.json")

# --------------------------------------------------------------------------
# 0.  Population -- derived, never retyped
# --------------------------------------------------------------------------

# PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md sec 3, the three "moved" tables.
S4_MOVED = {
    "pass": [69, 90, 132, 145, 278, 410, 443, 472],
    "accepted_holdout_fail": [19, 65, 66, 70, 95, 116, 166, 253, 270, 294,
                              400, 438, 446],
    "moved_to_different_gap": [272, 413, 418, 460],
}


def derive_population():
    with open(BACKWARD_PROBE) as fh:
        bucket = json.load(fh)["ha4_search_reach_sizing"]["ok_already_no_named_lever"]
    moved = sorted({i for v in S4_MOVED.values() for i in v})
    residual = sorted(set(bucket) - set(moved))
    return sorted(bucket), moved, residual


def live_pass_ids():
    """The most recent LIVE full-test-split pass list.

    `PROGRAM_SYNTHESIS_ARC6_M0_AB.md` sec 0 re-derived this live on
    2026-08-01 through the UNMODIFIED `mbpp_endgame_battery` driver
    (twin-run identical, cross-run hash reproduced).  It is read from that
    phase's committed JSON rather than re-run here: a sibling agent is
    concurrently editing `seeds/`, so a battery re-run today would measure
    a half-edited seed state, which is a WORSE number than a dated one.
    Reported with its condition attached, per the standing rule.
    """
    try:
        with open(CEILING_AB) as fh:
            d = json.load(fh)
    except FileNotFoundError:
        return None, "results/arc6_ceiling_ab.json absent"
    for path in (("current_state", "pass_ids"), ("live_state", "pass_ids"),
                 ("pass_ids",)):
        node = d
        for k in path:
            if not isinstance(node, dict) or k not in node:
                node = None
                break
            node = node[k]
        if isinstance(node, list):
            return sorted(node), "/".join(path)
    found = _deep_find_list(d, "pass_ids")
    return (sorted(found), "deep-scan pass_ids") if found else (None, "not found")


def engine_provenance_record():
    """WHICH Rust binary is in play -- recorded even though this
    measurement does not use one.

    THE HAZARD (confirmed live in this worktree, 2026-08-02): an isolated
    git worktree silently imports the CANONICAL tree's engine, because
    `site-packages/substrate_rs.pth` is an absolute path into the
    canonical tree and `_native.abi3.so` is gitignored. The two binaries
    on this machine are NOT interchangeable:

        canonical 7dd9af13... -- LACKS arc4-S4's list-op widening
        worktree  5c1b472f... -- HAS it (the arc-5 engine, the intended one)

    Verified by symbol content, not by path: `strings` finds SumList /
    MaxLenOver / MinLenOver / JoinList / LastElem in 5c1b472f and NOT in
    7dd9af13.

    This script loads NO engine at all (pure Python + SymPy), so its own
    numbers cannot move. The stamp is recorded anyway so the artifact is
    reproducible against a specific binary rather than against "whatever
    was on sys.path", and so the ONE engine-dependent INPUT (the pass_ids
    this measurement cross-checks staleness against) can be audited.
    """
    rec = {"this_script_loads_an_engine": False, "modules_loaded": []}
    rec["modules_loaded"] = sorted(
        m for m in sys.modules if m == "substrate_rs"
        or m.startswith("substrate_rs."))
    rec["this_script_loads_an_engine"] = bool(rec["modules_loaded"])
    try:
        from domains import engine_provenance as ep
        rec["stamp"] = ep.provenance_stamp(strict=False)
        rec["provenance_line"] = ep.provenance_line()
        rec["distinct_native_artifacts"] = ep.distinct_native_artifacts()
        rec["resolvable_natives"] = ep.resolvable_natives()
    except Exception as exc:
        rec["stamp_error"] = repr(exc)
    # sha256 both known artifacts directly, independent of import machinery
    rec["artifacts"] = {}
    for label, path in (
        ("this_tree", os.path.join(ROOT, "runners", "dsl", "python",
                                   "substrate_rs", "_native.abi3.so")),
    ):
        try:
            with open(path, "rb") as fh:
                rec["artifacts"][label] = {
                    "path": path,
                    "sha256": hashlib.sha256(fh.read()).hexdigest()}
        except OSError as exc:
            rec["artifacts"][label] = {"path": path, "error": repr(exc)}
    return rec


def _deep_find_list(obj, key):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key and isinstance(v, list):
                return v
            r = _deep_find_list(v, key)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _deep_find_list(v, key)
            if r:
                return r
    return None


# --------------------------------------------------------------------------
# 1.  Assert parsing -- each task's OWN example rows, from the fixture
# --------------------------------------------------------------------------

def _def_names(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]


def parse_rows(task):
    """(args, expected, rel_tol|None, wrapper) per assert.

    Never executes the reference code.  `wrapper` records an `assert
    set(f(...)) == set(...)` style comparison so the probe's own result is
    compared under the SAME wrapper -- a defect found live: without it,
    task 232's list result was compared against a set and spuriously
    refuted (see `breakage` in the JSON).
    """
    names = set(_def_names(task["code"]))
    rows = []
    for stmt in task["test_list"]:
        try:
            node = ast.parse(stmt).body[0]
        except SyntaxError:
            continue
        if not isinstance(node, ast.Assert):
            continue
        test = node.test
        rel_tol = None
        expected_node = None
        call = None
        lhs = None
        if (isinstance(test, ast.Call) and isinstance(test.func, ast.Attribute)
                and test.func.attr == "isclose"):
            lhs = test.args[0]
            call = _find_call(lhs, names)
            expected_node = test.args[1]
            for kw in test.keywords:
                if kw.arg == "rel_tol":
                    rel_tol = _lit(kw.value)
            if rel_tol is None:
                rel_tol = 1e-9
        elif isinstance(test, ast.Compare) and isinstance(test.ops[0], ast.Eq):
            lhs = test.left
            call = _find_call(lhs, names)
            expected_node = test.comparators[0]
        if call is None or expected_node is None:
            continue
        wrapper = None
        if (isinstance(lhs, ast.Call) and isinstance(lhs.func, ast.Name)
                and lhs.func.id in ("set", "frozenset", "sorted", "list",
                                    "tuple", "dict")):
            wrapper = lhs.func.id
        try:
            args = [_lit(a) for a in call.args]
            expected = _lit(expected_node)
        except Exception:
            continue
        rows.append({"args": args, "expected": expected, "rel_tol": rel_tol,
                     "wrapper": wrapper, "assert": stmt})
    return rows


def _find_call(node, names):
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id in names:
            return n
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            return n
    return None


def _lit(node):
    # literal_eval, but tolerating set(...) / frozenset(...) wrappers.
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id in ("set", "frozenset", "tuple", "list", "dict"):
        inner = _lit(node.args[0]) if node.args else []
        return {"set": set, "frozenset": frozenset, "tuple": tuple,
                "list": list, "dict": dict}[node.func.id](inner)
    return ast.literal_eval(node)


_WRAP = {"set": set, "frozenset": frozenset, "sorted": sorted,
         "list": list, "tuple": tuple, "dict": dict}


def matches(got, expected, rel_tol, wrapper=None):
    """Compare a probe result against the task's own expected value.

    Returns (bool, rendering_required).  `rendering_required` is True when
    the raw kernel result is an EXACT SymPy object (Rational/Integer) that
    only equals the assert's float AFTER a cross-frame rendering step.
    This distinction is load-bearing here, not cosmetic: CLAUDE.md's
    frame/continuum invariant says the exact value is the in-frame datum
    and the float is the rendering, so an oracle returning Rational(9,2)
    is CORRECT and the verdict layer -- not the oracle -- owns the
    float comparison. Found live: task 422 was refuted on row 1 purely
    because Rational(9,2) != 4.5 under Python ==.
    """
    rendering = False
    try:
        if wrapper and wrapper in _WRAP and not isinstance(got, _WRAP[wrapper]):
            got = _WRAP[wrapper](got)
        if rel_tol is not None:
            return (math.isclose(float(got), float(expected),
                                 rel_tol=rel_tol), rendering)
        if got == expected:
            return True, rendering
        if isinstance(expected, (int, float)) and not isinstance(got, (int, float, bool)):
            rendering = True
            return float(got) == float(expected), rendering
        if isinstance(expected, float) and isinstance(got, (int, float)):
            return float(got) == float(expected), rendering
        return False, rendering
    except Exception:
        return False, rendering


# --------------------------------------------------------------------------
# 2.  The IMPORT UNITS -- module/family granularity, task-independent
# --------------------------------------------------------------------------
#
# Each entry is a unit a person would plausibly register HAVING NEVER SEEN
# the test split.  `registered_blind` states the justification explicitly;
# a unit whose honest answer is "no" does not go on the list.

FAMILIES = [
    {
        "id": "F1_sympy_ntheory",
        "module": "sympy.ntheory",
        "unit": "register sympy.ntheory's public callables that return exact "
                "values on integer arguments",
        "registered_blind": True,
        "blind_justification":
            "Canonical number-theory module of the one already-installed, "
            "BSD-licensed, measured-zero-inexact library. domains/reason.py "
            "ALREADY hand-wraps a strict subset (gcd/lcm/isprime/factorize/"
            "divisor_count/divisor_sum/totient); registering the module is "
            "the obvious generalisation of a decision already taken.",
    },
    {
        "id": "F2_sympy_comb_numbers",
        "module": "sympy.functions.combinatorial.numbers",
        "unit": "register the named integer sequences (fibonacci, lucas, "
                "catalan, bell, bernoulli, euler, harmonic, partition, "
                "tribonacci, motzkin, genocchi, stirling, nC/nP/nT, ...)",
        "registered_blind": True,
        "blind_justification":
            "One module, one concept ('the named combinatorial sequences'). "
            "MBPP's own published task distribution is not needed to want "
            "Fibonacci/Catalan/Bell available to a synthesiser.",
    },
    {
        "id": "F3_sympy_comb_factorials",
        "module": "sympy.functions.combinatorial.factorials",
        "unit": "register factorial, factorial2, binomial, subfactorial, "
                "ff, rf",
        "registered_blind": True,
        "blind_justification":
            "6 callables, one concept. math.comb is ALREADY imported and "
            "called inside domains/reason.py (for an unrelated Steenrod "
            "purpose) -- the binomial half of this family is a zero-cost "
            "registration of something the tower already links against.",
    },
    {
        "id": "F4_sympy_iterables",
        "module": "sympy.utilities.iterables",
        "unit": "register sympy.utilities.iterables' generators/utilities "
                "(subsets, multiset, multiset_permutations, partitions, "
                "ordered, dict_merge, flatten, ...)",
        "registered_blind": "WEAK",
        "blind_justification":
            "HONESTLY WEAKER THAN F1-F3. This module is a general Python "
            "utility grab-bag, not a mathematical concept: registering it "
            "wholesale pulls in sort (`ordered`), dict merge (`dict_merge`) "
            "and frequency counting (`multiset`) -- capabilities a person "
            "would more naturally take from the stdlib. It is listed "
            "because it IS one module and IS in the vehicle, and flagged "
            "because its yield below is largely NON-mathematical, which is "
            "precisely the shape a cherry-pick would take if unpoliced.",
    },
    {
        "id": "F5_sympy_elementary_crossframe",
        "module": "sympy.functions.elementary.{miscellaneous,trigonometric,"
                  "complexes} + sympy.pi",
        "unit": "register the CROSS-FRAME maps and constants: sqrt, cbrt, "
                "root, sin/cos/tan/asin/acos/atan/atan2, Abs/arg/re/im, pi, E",
        "registered_blind": True,
        "blind_justification":
            "This is the family that supplies MISSING DIMENSIONS (pi, the "
            "irrationals, the complex argument), which CLAUDE.md's own "
            "frame/continuum invariant says live in Hom(frame,frame) and "
            "which arc 5 independently identified as absent. SymPy holds "
            "them EXACTLY and symbolically (tan(pi/4) is exactly 1), so the "
            "invariant is respected: the continuous parameter is carried "
            "intensionally, only the rendering is stepped.",
    },
    {
        "id": "F6_sympy_concrete",
        "module": "sympy.concrete.summations / sympy.solvers.recurr",
        "unit": "register summation() and rsolve() (symbolic sum / linear "
                "recurrence solver)",
        "registered_blind": False,
        "blind_justification":
            "REJECTED from the honest list. These take SYMBOLIC arguments "
            "(a Symbol, an expression, a recurrence relation), not values; "
            "an ORACLE in ProgEval's CallExtern table receives evaluated "
            "Values. Wiring them would require the synthesiser to build a "
            "symbolic expression first -- that is Seam B's job (prose -> "
            "formula), not Seam A's. Listed so the exclusion is visible.",
    },
]


def walk_family(mod_name):
    """Inventory a module's public callables + live exactness spot-check."""
    try:
        mod = __import__(mod_name, fromlist=["*"])
    except Exception as exc:  # pragma: no cover - recorded, not raised
        return {"module": mod_name, "import_error": repr(exc)}
    pub = []
    for name, obj in inspect.getmembers(mod):
        if name.startswith("_") or not callable(obj):
            continue
        if not getattr(obj, "__module__", "").startswith("sympy"):
            continue
        pub.append(name)
    return {"module": mod_name, "public_callables": len(pub),
            "names": sorted(pub)}


# --------------------------------------------------------------------------
# 3.  THE PROBES -- live invocation against each task's own example rows
# --------------------------------------------------------------------------
#
# A probe names a callable that comes FROM A REGISTERED FAMILY.  The
# surrounding expression is the composition the synthesiser would still
# have to find; `composition_beyond_kernel` says what that is, so the
# claim "the kernel unlocks this" is never larger than what was verified.

def build_probes():
    from sympy import (Abs, arg, binomial, harmonic, pi, sqrt, tan)
    from sympy.ntheory import count_digits, digits
    from sympy.utilities.iterables import dict_merge, multiset, ordered, subsets

    P = []

    def probe(task, family, callables, fn, composition, tier, residual,
              note=""):
        # `residual` = what STILL blocks the task after the kernel supplies
        # the mathematics. "none" is the only value for which the kernel
        # genuinely UNLOCKS the task; everything else means the kernel is
        # necessary but not sufficient, and saying "unlocked" would be the
        # overclaim.
        assert residual in ("none", "small_template_gap", "budget",
                            "structural_primitive"), residual
        P.append({"task_id": task, "family": family, "callables": callables,
                  "fn": fn, "composition_beyond_kernel": composition,
                  "tier": tier, "residual_blocker_after_kernel": residual,
                  "note": note})

    # ---- F3: combinatorial factorials -------------------------------------
    probe(80, "F3_sympy_comb_factorials", ["binomial"],
          lambda n: binomial(n + 2, 3),
          "argument shift n->n+2 (one Plus node)", "kernel_complete", "none",
          "tetrahedral number IS C(n+2,3); reference computes "
          "n(n+1)(n+2)/6 at size 11, above the enumerator's max_size=9")
    probe(422, "F3_sympy_comb_factorials", ["binomial"],
          lambda n: binomial(n + 1, 2) ** 2 / n,
          "square, divide by n (3 nodes)", "kernel_core", "none",
          "sum of first n cubes = C(n+1,2)^2 -- Nicomachus; collapses an "
          "unbounded fold to one closed-form kernel call")

    # ---- F2: combinatorial numbers ----------------------------------------
    probe(248, "F2_sympy_comb_numbers", ["harmonic"],
          lambda n: float(harmonic(n)),
          "none -- the kernel IS the function", "kernel_complete", "none",
          "harmonic(7) is the EXACT Rational 363/140; the assert's float is "
          "the rendering")

    # ---- F1: ntheory ------------------------------------------------------
    probe(479, "F1_sympy_ntheory", ["digits"],
          lambda n: digits(n)[1],
          "IndexAt(_,1) -- an op the enumerator already has", "kernel_core", "small_template_gap")
    probe(99, "F1_sympy_ntheory", ["digits"],
          lambda n: "".join(str(d) for d in digits(n, 2)[1:]),
          "drop-first slice + map-to-str + join; JoinList/MapList exist, "
          "the drop-first slice does not", "kernel_core", "structural_primitive")
    probe(283, "F1_sympy_ntheory", ["count_digits"],
          lambda n: all(v <= k for k, v in count_digits(n).items()),
          "all-over-dict-items -- NO dict iteration primitive exists",
          "kernel_core", "structural_primitive")

    # ---- F5: cross-frame maps + constants ---------------------------------
    probe(293, "F5_sympy_elementary_crossframe", ["sqrt"],
          lambda w, h: float(sqrt(w * w + h * h)),
          "two Times + one Plus (size ~8, inside max_size=9)", "kernel_core", "none",
          "MISSING DIMENSION: no irrational is constructible in-frame at "
          "any search size")
    probe(246, "F5_sympy_elementary_crossframe", ["sqrt"],
          lambda n: float(sqrt(n)),
          "none -- the kernel IS the function", "kernel_complete", "none",
          "MISSING DIMENSION; the prompt names an ALGORITHM (Babylonian) "
          "but the asserts test only the value")
    probe(163, "F5_sympy_elementary_crossframe", ["tan", "pi"],
          lambda s, l: float(s * l ** 2 / (4 * tan(pi / s))),
          "Pow + 3 arithmetic nodes; total ~11, ABOVE max_size=9",
          "kernel_core", "budget",
          "MISSING DIMENSION (pi AND tan); tan(pi/4) is exactly 1 in SymPy")
    probe(252, "F5_sympy_elementary_crossframe", ["Abs", "arg"],
          lambda z: (float(Abs(z)), float(arg(z))),
          "TUPLE CONSTRUCTION -- no such op in the enumerator (see task 257)",
          "kernel_core", "structural_primitive", "MISSING DIMENSION (complex argument)")

    # ---- F4: iterables (the weak family) ----------------------------------
    probe(255, "F4_sympy_iterables", ["subsets"],
          lambda l, n: list(subsets(l, n, repetition=True)),
          "none -- the kernel IS the function, order included",
          "kernel_complete", "none", "MATHEMATICAL yield of F4")
    probe(462, "F4_sympy_iterables", ["subsets"],
          lambda l: [list(s) for s in subsets(l)],
          "list-of-list rewrap", "kernel_core", "structural_primitive",
          "EXPECTED TO FAIL: subsets() emits size-lexicographic order, the "
          "task asserts binary-reflected order. Judged by NAME this is a "
          "match; judged by INVOCATION it is not.")
    probe(141, "F4_sympy_iterables", ["ordered"],
          lambda l: list(ordered(l)),
          "none", "kernel_complete", "none",
          "NON-mathematical yield of F4 -- this is 'sorting via a computer "
          "algebra import', the honest cost of module granularity")
    probe(88, "F4_sympy_iterables", ["multiset"],
          lambda l: multiset(l),
          "none", "kernel_complete", "none", "NON-mathematical yield of F4")
    probe(87, "F4_sympy_iterables", ["dict_merge"],
          lambda a, b, c: dict_merge(a, b, c),
          "none", "kernel_complete", "none",
          "NON-mathematical yield of F4; precedence direction UNVERIFIED "
          "by name -- the probe decides it")
    probe(232, "F4_sympy_iterables", ["ordered"],
          lambda l, n: list(ordered(l))[-n:],
          "negative-slice-by-variable -- not an enumerator op",
          "kernel_core", "structural_primitive", "NON-mathematical yield of F4")
    probe(475, "NONE_no_family_callable", [],
          lambda d: sorted(d.items(), key=lambda kv: -kv[1]),
          "sort BY A KEY over dict items", "no_family_callable", "structural_primitive",
          "NEGATIVE, and the sharpest one here: `sympy.utilities.iterables."
          "ordered` LOOKS like the kernel for 'sort a dictionary by value' "
          "and is not -- it sorts by SymPy's own default_sort_key, not by a "
          "caller-supplied key. This probe therefore uses plain sorted() and "
          "is EXCLUDED from every ceiling: it demonstrates the task is "
          "solvable, not that an importable kernel solves it.")

    # ---- controls: tasks whose blocker is NOT a kernel ---------------------
    probe(59, "NONE_arithmetic_only", [],
          lambda n: 3 * n * n - 2 * n,
          "pure arithmetic already in the op set", "no_kernel_needed", "budget",
          "CONTROL: octagonal number needs NO import; arc 5's exact-first "
          "rung already converted it")
    probe(435, "NONE_arithmetic_only", [],
          lambda n: n % 10,
          "Mod, already in the op set", "no_kernel_needed", "budget",
          "CONTROL: no kernel would help; blocker is elsewhere")
    probe(162, "NONE_arithmetic_only", [],
          lambda n: ((n + 1) // 2) * (n - (n + 1) // 2 + 1),
          "floor-div + 4 arithmetic nodes", "no_kernel_needed", "budget",
          "CONTROL: closed form exists but is composed of primitives the "
          "op set already has -- a BUDGET problem, not an import problem")

    return P


# The named sequences with NO callable anywhere in the registered families.
# Verified live by namespace search (see `search_namespace`).
ABSENT_CONCEPTS = {
    260: ["newman", "shanks", "williams", "nsw", "pell"],
    448: ["perrin"],
    59: ["octagonal", "polygonal"],
    80: ["tetrahedral"],
}


def search_namespace(terms):
    """Live: does ANY registered-family module expose a callable whose name
    contains one of these terms?"""
    hits = []
    for fam in FAMILIES:
        for mod_name in _mod_names(fam):
            try:
                mod = __import__(mod_name, fromlist=["*"])
            except Exception:
                continue
            for name, obj in inspect.getmembers(mod):
                if name.startswith("_") or not callable(obj):
                    continue
                low = name.lower()
                for t in terms:
                    if t in low:
                        hits.append(f"{mod_name}.{name}")
    return sorted(set(hits))


def _mod_names(fam):
    m = fam["module"]
    if "{" in m:
        base, rest = m.split("{", 1)
        opts, _, tail = rest.partition("}")
        out = [base + o.strip() for o in opts.split(",")]
        for extra in tail.split("+")[1:]:
            out.append(extra.strip())
        return [o for o in out if o and not o.startswith("sympy.pi")]
    return [p.strip() for p in m.replace("+", "/").split("/") if p.strip()]


# --------------------------------------------------------------------------
# 4.  Per-task blocker classification (ANALYSIS, labelled as such)
# --------------------------------------------------------------------------
#
# missing_dimension : the task needs a value not constructible in-frame at
#                     ANY search size (pi, an irrational, a complex arg).
#                     A kernel supplying it is a STRONGER claim -- it adds
#                     a dimension rather than shortening a search.
# budget            : every primitive exists; the composition is deeper
#                     than max_size=9 (or wider than the template pool).
# missing_structural_primitive : the blocker is a NON-mathematical op the
#                     enumerator lacks (sort, dict/tuple construction,
#                     string split/replace/reverse, (index,element) pairs,
#                     nested iteration). NO KERNEL CAN FIX THESE.

BLOCKER = {
    11:  ("missing_structural_primitive", "index-aware char removal (first+last occurrence)"),
    18:  ("missing_structural_primitive", "per-char set membership + string rebuild"),
    59:  ("budget", "3n^2-2n; all primitives present"),
    75:  ("missing_structural_primitive", "nested iteration: all() over each sublist"),
    80:  ("budget", "n(n+1)(n+2)/6 costs size 11 > max_size 9"),
    82:  ("missing_dimension", "pi"),
    85:  ("missing_dimension", "pi"),
    87:  ("missing_structural_primitive", "dict construction/merge"),
    88:  ("missing_structural_primitive", "dict construction (frequency map)"),
    98:  ("missing_structural_primitive", "PRODUCT fold -- no Product term in the op set"),
    99:  ("missing_structural_primitive", "base conversion + string build"),
    102: ("missing_structural_primitive", "split + capitalise + join"),
    106: ("missing_structural_primitive", "tuple/list concatenation"),
    118: ("missing_structural_primitive", "string split on delimiter"),
    137: ("budget", "count-zeros / (len - count-zeros); Filter+Count+Div present"),
    139: ("missing_dimension", "pi (literal 3.1415 in the reference)"),
    141: ("missing_structural_primitive", "SORT"),
    161: ("missing_structural_primitive", "cross-list filter (membership in a second list)"),
    162: ("budget", "closed form needs floor-div + 4 nodes"),
    163: ("missing_dimension", "pi AND tan"),
    170: ("missing_structural_primitive", "index-range slice"),
    172: ("missing_structural_primitive", "substring count"),
    226: ("missing_structural_primitive", "(index,element) pairs -- no enumerate binder"),
    230: ("missing_structural_primitive", "string replace"),
    232: ("missing_structural_primitive", "SORT + top-n slice"),
    233: ("missing_dimension", "pi (literal 3.1415)"),
    246: ("missing_dimension", "sqrt / irrational"),
    248: ("budget", "unbounded 1/i fold; closed form is a kernel"),
    252: ("missing_dimension", "complex modulus+argument"),
    255: ("missing_structural_primitive", "combination GENERATOR"),
    257: ("missing_structural_primitive", "TUPLE construction"),
    260: ("missing_structural_primitive", "linear recurrence to depth n -- no recursion binder"),
    262: ("missing_structural_primitive", "slice + tuple construction"),
    264: ("missing_structural_primitive", "whole-input conditional branch"),
    265: ("missing_structural_primitive", "strided slicing, list of lists"),
    276: ("missing_dimension", "pi (literal 3.1415)"),
    283: ("missing_structural_primitive", "digit extraction + per-digit counting"),
    290: ("missing_structural_primitive", "TUPLE construction (len, argmax-list)"),
    293: ("missing_dimension", "sqrt / irrational"),
    301: ("missing_structural_primitive", "recursive dict traversal"),
    310: ("missing_structural_primitive", "string -> tuple of chars"),
    312: ("missing_dimension", "pi"),
    390: ("missing_structural_primitive", "format-string application"),
    411: ("missing_structural_primitive", "split + capitalise + join"),
    419: ("missing_structural_primitive", "round-each + fold + multiply-by-len"),
    421: ("missing_structural_primitive", "join with delimiter over mixed types"),
    422: ("budget", "sum of cubes fold; closed form is a kernel"),
    424: ("missing_structural_primitive", "per-element last-index extraction"),
    435: ("budget", "n % 10 -- Mod present; blocker is elsewhere in the pipeline"),
    437: ("missing_structural_primitive", "(index,element) pairs"),
    439: ("missing_structural_primitive", "map-to-str + join + int()"),
    442: ("budget", "count-positive / len, rounded"),
    448: ("missing_structural_primitive", "Perrin recurrence to depth n"),
    450: ("missing_structural_primitive", "filter by len == n (template pool gap)"),
    456: ("missing_structural_primitive", "per-element string REVERSE -- no Reverse op"),
    462: ("missing_structural_primitive", "powerset GENERATOR in a specific order"),
    473: ("missing_structural_primitive", "set-of-sorted-tuples intersection"),
    474: ("missing_structural_primitive", "string replace"),
    475: ("missing_structural_primitive", "SORT a dict by value"),
    479: ("missing_structural_primitive", "leading-digit extraction"),
}

# Is the task's CORE a mathematical object at all?  A kernel import can
# only ever help where this is True.  (Analysis, from prompt + reference.)
MATH_SHAPED = {
    59, 80, 82, 85, 98, 99, 137, 139, 162, 163, 232, 233, 246, 248, 252,
    255, 260, 276, 283, 293, 312, 422, 435, 442, 448, 462, 479,
}


# --------------------------------------------------------------------------
# 5.  Run
# --------------------------------------------------------------------------

def main():
    started = _dt.datetime.now(_dt.timezone.utc).isoformat()
    with open(FIXTURE) as fh:
        tasks = {t["task_id"]: t for t in json.load(fh)}

    bucket, moved, residual = derive_population()
    passes, pass_src = live_pass_ids()

    stale = sorted(set(residual) & set(passes)) if passes else []
    live_unreached = sorted(set(residual) - set(stale))
    engine = engine_provenance_record()

    out = {
        "_README": (
            "A-ceiling for arc 6 Seam A. MEASUREMENT ONLY -- nothing built, "
            "no seed/runner/adapter touched. Every kernel claim below was "
            "VERIFIED BY LIVE INVOCATION on the task's own example rows; a "
            "kernel is never accepted on the strength of its name. Both "
            "ceilings are reported: module-granularity (honest) and "
            "per-task cherry-picked (inflated). Paired id lists throughout."
        ),
        "measured_at": started,
        "engine_provenance": engine,
        "engine_dependence_audit": {
            "_why": "an isolated worktree silently imports the CANONICAL "
                    "tree's engine (site-packages/substrate_rs.pth is an "
                    "absolute path into it; _native.abi3.so is gitignored). "
                    "The two binaries differ: canonical 7dd9af13 LACKS "
                    "arc4-S4's list-op widening, worktree 5c1b472f HAS it. "
                    "So every claim has to say which binary it rests on.",
            "engine_independent": {
                "what": ["all 20 SymPy probes and their row-level "
                         "verdicts", "the family inventories",
                         "the namespace absence checks",
                         "every ceiling number (strict 5/8, verified 14, "
                         "cherry-picked 27/60)"],
                "why": "this process loads no substrate_rs module at all "
                       "(see engine_provenance.modules_loaded == []); the "
                       "probes are pure Python + SymPy.",
            },
            "engine_dependent_INPUT": {
                "what": "the staleness cross-check -- the 7 S4-residual ids "
                        "that now PASS -- is read from "
                        "results/arc6_ceiling_ab.json::current_state."
                        "pass_ids, which WAS produced by running an engine.",
                "which_binary_produced_it": "5c1b472f (the intended one)",
                "evidence_1_path": "scripts/arc6_ceiling_ab.py derives ROOT "
                        "from its own __file__ and inserts ROOT/runners/dsl/"
                        "python at sys.path[0]; that artifact's recorded "
                        "environment.cwd is THIS worktree, so the insertion "
                        "resolved to this tree's 5c1b472f, not the .pth's "
                        "canonical 7dd9af13. Reproduced live.",
                "evidence_2_content": "STRONGER, and independent of any "
                        "path reasoning: that pass list contains all eight "
                        "of S4's list-op conversions (69, 90, 132, 145, "
                        "278, 410, 443, 472). Tasks 90 and 132 require "
                        "MaxLenOver and JoinList, symbols that `strings` "
                        "finds in 5c1b472f and NOT in 7dd9af13. A run on "
                        "the canonical binary could not have produced them.",
            },
            "analysis_relative_to": {
                "what": "the BLOCKER classification and "
                        "residual_blocker_after_kernel fields assert what "
                        "the enumerator can and cannot compose.",
                "binary": "5c1b472f -- i.e. WITH S4's Len/SumList/MaxList/"
                          "MinLenOver/First/LastElem/JoinList/FilterList/"
                          "MapList ops. Against the canonical 7dd9af13 "
                          "these judgements would be WRONG IN THE "
                          "CONSERVATIVE DIRECTION: fewer ops means more "
                          "tasks blocked, so the strict ceiling could only "
                          "fall, never rise.",
            },
        },
        "import_vehicle": {
            "library": "sympy",
            "version": None,
            "why": "RESEARCH_IMPORT_SOURCES.md sec 1.1/5: already installed, "
                   "BSD-3-Clause, 107/125 invoked ntheory/combinatorics "
                   "results exact and ZERO inexact; in-process, so it "
                   "satisfies prog_eval.rs's 'NO shelling out, ever'.",
        },
        "population": {
            "s4_85_bucket": bucket,
            "s4_moved_off_enumerate_failed": moved,
            "s4_residual_60": residual,
            "n_residual": len(residual),
            "derivation": "results/arc4_backward_probe.json :: "
                          "ha4_search_reach_sizing.ok_already_no_named_lever "
                          "MINUS PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md sec 3's "
                          "three moved-id tables. Never retyped as a literal.",
        },
        "staleness_correction": {
            "pass_ids_source": f"PROGRAM_SYNTHESIS_ARC6_M0_AB.md via {pass_src}",
            "condition": "measured 2026-08-01 on the full 257-task test "
                         "split through the unmodified mbpp_endgame_battery "
                         "driver; NOT re-run here because a sibling agent is "
                         "concurrently editing seeds/",
            "s4_residual_ids_that_now_PASS": stale,
            "n_stale": len(stale),
            "live_unreached_ids": live_unreached,
            "n_live_unreached": len(live_unreached),
        },
        "families": [],
        "probes": [],
        "namespace_absence_checks": {},
        "blocker_split": {},
        "ceilings": {},
        "ranked_import_list": [],
        "breakage": [],
        "harness_defects_found_live": [
            {
                "defect": "an EXACT SymPy result does not compare equal to "
                          "the assert's float under Python ==",
                "found_on": "task 422 row 1: binomial(3,2)**2/2 -> "
                            "Rational(9,2), asserted against 4.5",
                "why_it_matters": "this is the frame/continuum boundary "
                                  "showing up as an integration cost. The "
                                  "oracle is RIGHT to return the exact "
                                  "Rational; the float belongs to the "
                                  "rendering/verdict layer. Any real Seam A "
                                  "build needs an explicit exact->rendered "
                                  "step at the ProgEval boundary, and that "
                                  "step is real import work nobody had "
                                  "costed.",
                "fix": "matches() now records `rendering_required` per row "
                       "instead of silently failing.",
            },
            {
                "defect": "asserts of the form `assert set(f(...)) == "
                          "set(...)` lost their wrapper, so a list result "
                          "was compared against a set and spuriously "
                          "refuted",
                "found_on": "task 232 (all 3 rows)",
                "why_it_matters": "a measurement bug in the REFUTING "
                                  "direction is the dangerous kind here: it "
                                  "would have under-reported the ceiling "
                                  "and been indistinguishable from an "
                                  "honest null.",
                "fix": "parse_rows() records the LHS wrapper; matches() "
                       "applies it to the probe result too.",
            },
        ],
    }

    try:
        import sympy
        out["import_vehicle"]["version"] = sympy.__version__
    except Exception as exc:
        out["breakage"].append({"where": "import sympy", "error": repr(exc)})
        json.dump(out, open(OUT, "w"), indent=1, default=str)
        return 1

    # --- family inventory -------------------------------------------------
    for fam in FAMILIES:
        rec = {k: v for k, v in fam.items()}
        rec["modules_walked"] = []
        total = 0
        for mod_name in _mod_names(fam):
            w = walk_family(mod_name)
            if "public_callables" in w:
                total += w["public_callables"]
            rec["modules_walked"].append(w)
        rec["public_callables_total"] = total
        out["families"].append(rec)

    # --- absence checks ---------------------------------------------------
    for tid, terms in ABSENT_CONCEPTS.items():
        hits = search_namespace(terms)
        out["namespace_absence_checks"][str(tid)] = {
            "searched_for": terms,
            "hits_in_registered_families": hits,
            "absent": not hits,
        }

    # --- probes -----------------------------------------------------------
    probes = build_probes()
    for p in probes:
        tid = p["task_id"]
        task = tasks[tid]
        rows = parse_rows(task)
        results = []
        ok = 0
        rendered_any = False
        for r in rows:
            rec = {"args": r["args"], "expected": r["expected"],
                   "rel_tol": r["rel_tol"], "wrapper": r["wrapper"]}
            try:
                got = p["fn"](*r["args"])
                rec["got"] = got
                m, rendering = matches(got, r["expected"], r["rel_tol"],
                                       r["wrapper"])
                rec["match"] = m
                rec["rendering_required"] = rendering
                rendered_any = rendered_any or rendering
            except Exception as exc:
                rec["got"] = None
                rec["error"] = f"{type(exc).__name__}: {exc}"
                rec["match"] = False
                out["breakage"].append({
                    "where": f"probe task {tid} ({p['family']})",
                    "error": rec["error"],
                    "trace_tail": traceback.format_exc().strip().splitlines()[-1],
                })
            ok += bool(rec["match"])
            results.append(rec)
        verdict = ("verified_all_rows" if rows and ok == len(rows)
                   else "verified_partial" if ok
                   else "refuted_on_own_rows")
        out["probes"].append({
            "task_id": tid,
            "prompt": task["prompt"],
            "family": p["family"],
            "callables": p["callables"],
            "tier": p["tier"],
            "residual_blocker_after_kernel": p["residual_blocker_after_kernel"],
            "composition_beyond_kernel": p["composition_beyond_kernel"],
            "note": p["note"],
            "rows_total": len(rows),
            "rows_matched": ok,
            "verdict": verdict,
            "exact_result_needed_crossframe_rendering": rendered_any,
            "rows": results,
        })

    # --- blocker split ----------------------------------------------------
    by_blocker = {}
    for tid in residual:
        kind, why = BLOCKER[tid]
        by_blocker.setdefault(kind, []).append(tid)
    out["blocker_split"] = {
        "_legend": {
            "missing_dimension": "needs a value not constructible in-frame "
                                 "at ANY search size (pi, an irrational, a "
                                 "complex argument). A kernel supplying one "
                                 "ADDS A DIMENSION -- a strictly stronger "
                                 "claim than shortening a search.",
            "budget": "every primitive exists; the composition is deeper "
                      "than max_size=9 or outside the bounded template "
                      "pool. A kernel here only SHORTENS A SEARCH.",
            "missing_structural_primitive": "the blocker is a NON-"
                      "mathematical op the enumerator lacks (sort, dict/"
                      "tuple construction, string split/replace/reverse, "
                      "(index,element) binding, nested iteration). NO "
                      "MATHEMATICAL kernel fixes these. A NON-mathematical "
                      "utility import can -- and exactly three of them "
                      "(88, 141, 255) fall out of registering "
                      "sympy.utilities.iterables, whose callables `multiset`"
                      "/`ordered`/`subsets` ARE a frequency-counter, a sort "
                      "and a combination generator. That overlap is not a "
                      "classification error, it IS the finding: F4's yield "
                      "sits entirely in the class a maths import should not "
                      "reach, which is why its blind-registration case is "
                      "marked WEAK and why the 5-id strong-families ceiling "
                      "is the one to scope from.",
        },
        "counts_over_s4_residual_60": {k: len(v) for k, v
                                       in sorted(by_blocker.items())},
        "ids_over_s4_residual_60": {k: sorted(v) for k, v
                                    in sorted(by_blocker.items())},
        "counts_over_live_unreached": {
            k: len([i for i in v if i in set(live_unreached)])
            for k, v in sorted(by_blocker.items())},
        "ids_over_live_unreached": {
            k: sorted(i for i in v if i in set(live_unreached))
            for k, v in sorted(by_blocker.items())},
        "per_task_reason": {str(t): {"class": BLOCKER[t][0],
                                     "why": BLOCKER[t][1]} for t in residual},
        "math_shaped_ids": sorted(MATH_SHAPED & set(residual)),
        "not_math_shaped_ids": sorted(set(residual) - MATH_SHAPED),
    }

    # --- ceilings ---------------------------------------------------------
    verified = {p["task_id"] for p in out["probes"]
                if p["verdict"] == "verified_all_rows"
                and p["family"].startswith("F")}
    refuted = {p["task_id"] for p in out["probes"]
               if p["verdict"] != "verified_all_rows"
               and p["family"].startswith("F")}
    strong_fams = {"F1_sympy_ntheory", "F2_sympy_comb_numbers",
                   "F3_sympy_comb_factorials", "F5_sympy_elementary_crossframe"}
    verified_strong = {p["task_id"] for p in out["probes"]
                       if p["verdict"] == "verified_all_rows"
                       and p["family"] in strong_fams}
    verified_weak = verified - verified_strong

    kernel_complete = {p["task_id"] for p in out["probes"]
                       if p["verdict"] == "verified_all_rows"
                       and p["tier"] == "kernel_complete"
                       and p["family"].startswith("F")}
    kernel_core = verified - kernel_complete

    # STRICTEST: the kernel is verified AND nothing else blocks the task.
    unlocked = {p["task_id"] for p in out["probes"]
                if p["verdict"] == "verified_all_rows"
                and p["family"].startswith("F")
                and p["residual_blocker_after_kernel"] == "none"}
    unlocked_strong = unlocked & verified_strong
    still_blocked = {}
    for p in out["probes"]:
        if (p["verdict"] == "verified_all_rows" and p["family"].startswith("F")
                and p["residual_blocker_after_kernel"] != "none"):
            still_blocked.setdefault(
                p["residual_blocker_after_kernel"], []).append(p["task_id"])

    cherry_concept = sorted(MATH_SHAPED & set(residual))
    out["ceilings"] = {
        "_definition": {
            "honest": "tasks whose MATHEMATICAL CORE is computed exactly by "
                      "a callable ALREADY PRESENT in a module registered as "
                      "a whole, verified by live invocation on that task's "
                      "own example rows.",
            "cherry_picked_concept": "tasks unlockable by minting ONE "
                      "BESPOKE KERNEL PER TASK, named after that task's own "
                      "concept (octagonal(), perrin_sum(), newman_prime(), "
                      "area_polygon(), ...). This is the number a per-task "
                      "mapping would report, and it is FAKE: the oracle "
                      "table would encode the test-split answers.",
            "cherry_picked_reductio": "the true limit of the same move: an "
                      "oracle named mbpp_task_<id> for every task = 60/60. "
                      "Stated so the direction of the inflation is visible.",
        },
        "honest_all_families": {
            "ids": sorted(verified), "n": len(verified),
            "denominator_s4_residual": len(residual),
            "denominator_live_unreached": len(live_unreached),
        },
        "honest_strong_families_only": {
            "note": "F1/F2/F3/F5 -- the families whose blind-registration "
                    "justification is unqualified. F4 (sympy.utilities."
                    "iterables) is excluded here because its registration "
                    "justification is WEAK and its yield is largely non-"
                    "mathematical.",
            "ids": sorted(verified_strong), "n": len(verified_strong),
        },
        "honest_weak_family_only_ids": sorted(verified_weak),
        "STRICT_kernel_verified_AND_nothing_else_blocks": {
            "_definition": "the headline the arc should be scoped from: a "
                           "family callable reproduces the task's own rows "
                           "AND the remaining composition is already inside "
                           "the enumerator's reach. Every other id below is "
                           "a task where the kernel is NECESSARY BUT NOT "
                           "SUFFICIENT -- calling those 'unlocked' would be "
                           "the overclaim this measurement exists to avoid.",
            "ids": sorted(unlocked), "n": len(unlocked),
            "strong_families_only_ids": sorted(unlocked_strong),
            "strong_families_only_n": len(unlocked_strong),
        },
        "kernel_verified_but_still_blocked_by": {
            k: sorted(v) for k, v in sorted(still_blocked.items())},
        "kernel_is_the_whole_function_ids": sorted(kernel_complete),
        "kernel_is_the_core_composition_still_needed_ids": sorted(kernel_core),
        "refuted_by_live_invocation_ids": sorted(refuted),
        "cherry_picked_concept": {"ids": cherry_concept,
                                  "n": len(cherry_concept)},
        "cherry_picked_reductio": {"ids": residual, "n": len(residual)},
        "gap_honest_vs_cherry_concept": len(cherry_concept) - len(verified),
    }

    # --- ranked import list ----------------------------------------------
    fam_yield, fam_yield_strict = {}, {}
    for p in out["probes"]:
        if p["verdict"] == "verified_all_rows" and p["family"].startswith("F"):
            fam_yield.setdefault(p["family"], []).append(p["task_id"])
            if p["residual_blocker_after_kernel"] == "none":
                fam_yield_strict.setdefault(p["family"], []).append(p["task_id"])
    COST = {
        "F1_sympy_ntheory": ("LOWEST", "already installed; oracle-table "
                             "registration only; reason.py already wraps a "
                             "subset by hand"),
        "F2_sympy_comb_numbers": ("LOWEST", "same registration, one module"),
        "F3_sympy_comb_factorials": ("LOWEST", "6 callables; math.comb "
                                     "already imported in reason.py"),
        "F4_sympy_iterables": ("LOW", "one module, but generator-valued "
                               "returns need a Value bridge, and the "
                               "blind-registration case is WEAK"),
        "F5_sympy_elementary_crossframe": ("MEDIUM", "adds a DIMENSION: "
                               "symbolic irrationals/pi must round-trip "
                               "through the exact Value domain and be "
                               "rendered only at the verdict boundary -- "
                               "the one family that touches the frame/"
                               "continuum invariant"),
    }
    ranked = []
    for fam_id, ids in fam_yield.items():
        cost, why = COST.get(fam_id, ("?", ""))
        fam = next(f for f in FAMILIES if f["id"] == fam_id)
        strict = sorted(fam_yield_strict.get(fam_id, []))
        ranked.append({
            "family": fam_id,
            "unit": fam["unit"],
            "registered_blind": fam["registered_blind"],
            "tasks_kernel_verified_ids": sorted(ids),
            "n_kernel_verified": len(ids),
            "tasks_STRICTLY_unlocked_ids": strict,
            "n_strict": len(strict),
            "import_cost": cost,
            "cost_note": why,
        })
    order = {"LOWEST": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "?": 9}
    ranked.sort(key=lambda r: (-r["n_strict"], order.get(r["import_cost"], 9),
                               -r["n_kernel_verified"]))
    out["ranked_import_list"] = ranked

    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1, default=str)

    # --- stdout summary ---------------------------------------------------
    eng = out["engine_provenance"]
    print(f"engine: loads_engine={eng['this_script_loads_an_engine']} "
          f"modules={eng['modules_loaded']}")
    print(f"  this tree's artifact sha256="
          f"{eng['artifacts'].get('this_tree', {}).get('sha256', '?')[:16]}")
    print(f"sympy {out['import_vehicle']['version']}")
    print(f"S4 residual: {len(residual)} ids")
    print(f"  of which now PASS (stale): {stale}")
    print(f"  live unreached: {len(live_unreached)}")
    print()
    for p in out["probes"]:
        print(f"  task {p['task_id']:>3}  {p['family']:<32} "
              f"{'/'.join(p['callables']) or '-':<18} "
              f"{p['rows_matched']}/{p['rows_total']}  {p['verdict']:<20} "
              f"residual={p['residual_blocker_after_kernel']}")
    print()
    print("blocker split (s4 residual 60):",
          out["blocker_split"]["counts_over_s4_residual_60"])
    print("blocker split (live unreached):",
          out["blocker_split"]["counts_over_live_unreached"])
    print("HONEST kernel-verified (all families):",
          out["ceilings"]["honest_all_families"]["n"],
          out["ceilings"]["honest_all_families"]["ids"])
    print("HONEST kernel-verified (strong families only):",
          out["ceilings"]["honest_strong_families_only"]["n"],
          out["ceilings"]["honest_strong_families_only"]["ids"])
    st = out["ceilings"]["STRICT_kernel_verified_AND_nothing_else_blocks"]
    print("STRICT unlocked (nothing else blocks):", st["n"], st["ids"])
    print("STRICT unlocked, strong families only:",
          st["strong_families_only_n"], st["strong_families_only_ids"])
    print("kernel verified but STILL blocked by:",
          out["ceilings"]["kernel_verified_but_still_blocked_by"])
    print("CHERRY-PICKED (concept kernels):",
          out["ceilings"]["cherry_picked_concept"]["n"])
    print("CHERRY-PICKED (reductio):",
          out["ceilings"]["cherry_picked_reductio"]["n"])
    print()
    for r in out["ranked_import_list"]:
        print(f"  strict {r['n_strict']:>2} / verified {r['n_kernel_verified']:>2}"
              f"  {r['import_cost']:<7} {r['family']}  "
              f"strict={r['tasks_STRICTLY_unlocked_ids']} "
              f"verified={r['tasks_kernel_verified_ids']}")
    if out["breakage"]:
        print("\nBREAKAGE:")
        for b in out["breakage"]:
            print("  ", b["where"], "->", b["error"])
    h = hashlib.sha256(json.dumps(
        {"honest": sorted(verified), "residual": residual},
        sort_keys=True).encode()).hexdigest()[:16]
    print(f"\nid_hash={h}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
