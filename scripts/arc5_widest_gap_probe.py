#!/usr/bin/env python
"""arc5_widest_gap_probe — CEILING MEASUREMENT: can a WIDEST-GAP criterion
select the right relaxation of Gamma, with NO hand-built lexicon?

`PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md` measured that CONJECTURING S3
symmetry for `br_10_top_of_three` and augmenting the revealed rows with
their orbit converts a wrong `Max(a, b)` to a correct `Max(a, Max(b, c))`
with ZERO new oracle calls -- but the symmetry was chosen BY HAND. The
obvious follow-up ("build a lexicon of symmetric-operation words") is
CONTENT, which this project has measured as worthless five times
(`PROGRAM_SYNTHESIS_ARC4_SUMMARY.md`). This measurement tests whether a
SELECTION CRITERION -- enumerate candidate relaxations, pick the one that
removes the most of the held version space, refutation-first -- can stand
in for that lexicon.

THE CRITERION, precisely:

  1. REFUTATION FIRST. A relaxation (conjectured invariant: a permutation
     symmetry, or an idempotence/fixed-point law) is tested against the
     REVEALED ROWS ALONE before it is ever used. If the rows already
     contradict it, it is discarded -- never scored, never applied. This
     is the soundness half, and it matters more than the gap half (a false
     relaxation manufactures wrong labels).
  2. AUGMENT. A relaxation that survives refutation lets us MANUFACTURE
     new (input, output) pairs from data we already hold and trust -- the
     conjecture's own closure over the revealed rows (a permutation's
     orbit; an idempotent law's fixed points) -- exactly the mechanism
     `PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md` validated for S3, generalised
     here to the FULL relaxation family (S_n, every 2-cycle subgroup,
     idempotence) instead of hand-picking S3.
  3. MEASURE THE GAP. `V0` = the number of DISTINCT behaviours (functions,
     not syntax trees) reachable by a small, fixed op inventory
     (`Plus/Minus/Times/Max/Min/Abs/Neg`, size <=5) that are consistent
     with the REVEALED rows alone. `V1` = the number that are ALSO
     consistent with the relaxation's augmented rows. `Gap = V0 - V1` --
     how much of the held version space the relaxation removes. Distinctness
     is measured over a WIDE PROBE grid (the cartesian recombination of
     each argument's OWN observed values across the revealed rows, plus
     the relaxation's own augmented-row inputs) -- an operational
     equivalence relation derived entirely from data already held, never
     full extensional equality (an honest approximation, stated once here
     and not smoothed over below).
  4. SELECT the un-refuted, non-self-contradicting (V1>0) relaxation with
     the LARGEST gap; take the MDL-smallest surviving candidate as "the"
     completion; verify it against held-out data (NEVER used for
     selection) plus, for the headline task, a hand-constructed witness
     independent of both revealed and held-out rows.

MONOTONICITY is included as a REFUTABLE candidate family (checked against
revealed-row pairs differing in exactly one argument) but NOT gap-scored:
no augmentation mechanism was built for it in this timebox (there is no
clean way to manufacture a NEW labelled row from "the function doesn't
decrease" without inventing a magnitude that isn't in the data). It
contributes to the refutation-rate accounting only -- an honest, named
scope limit, not a smoothed-over null.

OUTPUT-RANGE/BOUND constraints were considered and DELIBERATELY EXCLUDED
from the catalogue: a bound derived from revealed rows' own min/max output
cannot be refuted BY those same rows (it is true of them by construction),
which fails this measurement's own refutation-first discipline. Named,
not silently dropped.

READS ONLY: `tests/fixtures/mbpp/sanitized-mbpp.json` (via
`mbpp_arc3_battery.q0_split_tasks`), `results/mbpp_arc3_endgame.json`
(frozen -- the 76 traps' own accepted IR, read only for each task's
PARAMETER NAMES via `arc4_failure_anatomy._param_names`, never for its
program body), `results/arc4_structural_verdicts.json` (the 36
honest-residual id list), `tests/fixtures/prog_synthesis_battery/tasks.json`
(br_10's own fixture rows). NO changes to synthesis/engine/seed/spec code
anywhere -- measurement only. No Rust changes: the version-space
enumeration is a small, bounded Python search over the SAME kind of op
inventory `SynthEnumerate`/`generator.py` already use, driven through the
real native `evaluate()` Term evaluator for every candidate check (never
re-implementing arithmetic in Python).

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/arc5_widest_gap_probe.py
"""
from __future__ import annotations

import hashlib
import inspect
import itertools
import json
import math
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402
import mbpp_arc3_battery as arc3b  # noqa: E402
import arc4_failure_anatomy as afa  # noqa: E402
import arc4_structural_verdicts as asv  # noqa: E402 -- collect_var_refs, reused verbatim
from domains import mbpp_spec as ms  # noqa: E402

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
R3_ENDGAME_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")
STRUCTURAL_PATH = os.path.join(ROOT, "results", "arc4_structural_verdicts.json")
BATTERY_PATH = os.path.join(ROOT, "tests", "fixtures", "prog_synthesis_battery", "tasks.json")
OUT_PATH = os.path.join(ROOT, "results", "arc5_widest_gap.json")

# The exact 12 ids (PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md's reopen lane),
# quoted verbatim from `tests/test_reject_informs_repair_migrated.py` via
# `scripts/arc5_shape_constraint_probe.py`'s own citation -- never
# hand-re-derived a second, possibly-drifting way.
REOPENED_12 = [14, 58, 103, 125, 126, 164, 228, 304, 396, 414, 430, 432]

# ========================================================================= #
#  grammar -- the FIXED, SMALL op inventory this measurement enumerates.
#  Same node-JSON shapes the real Rust Term evaluator (`runners/dsl/src/
#  jsonio.rs`) parses -- Plus/Times/Max/Min (n-ary "items"), Minus (binary
#  "a"/"b"), Abs/Neg (unary "arg"). No Div/comparisons/IfThenElse: keeps
#  the size-5 search small and fast; a documented scope limit, not hidden
#  (tasks whose true program needs them are honestly reported "no matching
#  candidate", never silently faked).
# ========================================================================= #
BASE_CONSTS: Tuple[int, ...] = (0, 1, -1)
BINARY_OPS = ("Plus", "Minus", "Times", "Max", "Min")
COMMUTATIVE_BINARY = {"Plus", "Times", "Max", "Min"}
UNARY_OPS = ("Abs", "Neg")
MAX_SIZE = 5
CONST_CAP = 4  # BASE_CONSTS (3) + at most 1 task-derived extra
TOL = 1e-9


def const_pool_for(revealed_rows: List[Dict[str, Any]], params: List[str]) -> Tuple[int, ...]:
    vals = set(BASE_CONSTS)
    extra = set()
    for row in revealed_rows:
        for p in params:
            v = row["inputs"].get(p)
            if isinstance(v, int) and not isinstance(v, bool) and abs(v) <= 20:
                extra.add(v)
        ev = row.get("expected")
        if isinstance(ev, int) and not isinstance(ev, bool) and abs(ev) <= 20:
            extra.add(ev)
    extra -= vals
    extra_sorted = sorted(extra, key=lambda x: (abs(x), x))[: max(0, CONST_CAP - len(vals))]
    return tuple(sorted(vals | set(extra_sorted)))


# candidate representation: (expr_dict, size)
def _leaf_var(name: str) -> Dict[str, Any]:
    return {"type": "Var", "name": name}


def _leaf_lit(v: int) -> Dict[str, Any]:
    return {"type": "Lit", "value": v}


def _mk_bin(op: str, a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    if op == "Minus":
        return {"type": "Minus", "a": a, "b": b}
    return {"type": op, "items": [a, b]}


def _mk_un(op: str, a: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": op, "arg": a}


_GEN_CACHE: Dict[Tuple[Any, ...], List[Tuple[Dict[str, Any], int]]] = {}


def generate_candidates(params: Tuple[str, ...], consts: Tuple[int, ...],
                        max_size: int) -> List[Tuple[Dict[str, Any], int]]:
    """Bottom-up size-ordered enumeration (generator.py's own algorithm,
    reproduced at Python scale for a small grammar) -- EVERY function here
    takes only (params, consts, max_size); no held-out data, no task
    identity, nothing beyond the grammar parameters."""
    key = (params, consts, max_size)
    if key in _GEN_CACHE:
        return _GEN_CACHE[key]
    by_size: Dict[int, List[Dict[str, Any]]] = {1: []}
    for p in params:
        by_size[1].append(_leaf_var(p))
    for c in consts:
        by_size[1].append(_leaf_lit(c))
    for size in range(2, max_size + 1):
        bucket: List[Dict[str, Any]] = []
        for child in by_size.get(size - 1, []):
            for op in UNARY_OPS:
                bucket.append(_mk_un(op, child))
        for s1 in range(1, size - 1):
            s2 = size - 1 - s1
            if s2 < 1:
                continue
            for op in BINARY_OPS:
                for a in by_size.get(s1, []):
                    for b in by_size.get(s2, []):
                        bucket.append(_mk_bin(op, a, b))
        by_size[size] = bucket
    out = [(t, s) for s in range(1, max_size + 1) for t in by_size[s]]
    _GEN_CACHE[key] = out
    return out


def term_str(expr: Dict[str, Any]) -> str:
    t = expr["type"]
    if t == "Var":
        return expr["name"]
    if t == "Lit":
        return repr(expr["value"])
    if t == "Minus":
        return "Minus(%s, %s)" % (term_str(expr["a"]), term_str(expr["b"]))
    if t in ("Abs", "Neg"):
        return "%s(%s)" % (t, term_str(expr["arg"]))
    return "%s(%s)" % (t, ", ".join(term_str(x) for x in expr["items"]))


def eval_expr(s: "srs.Substrate", expr: Dict[str, Any], inputs: Dict[str, Any]) -> Any:
    """The ONLY evaluation primitive this file uses -- the real native
    Term evaluator, never a reimplementation of arithmetic in Python.
    `inputs` becomes the Var environment directly (dict keys = Var
    names)."""
    try:
        return s._inner.evaluate(expr, dict(inputs))
    except Exception:
        return _EVAL_ERROR


_EVAL_ERROR = object()


def numeric_agree(got: Any, expected: Any) -> bool:
    if got is _EVAL_ERROR:
        return False
    if isinstance(expected, bool) or isinstance(got, bool):
        return isinstance(got, bool) and isinstance(expected, bool) and got == expected
    if isinstance(got, (int, float)) and isinstance(expected, (int, float)):
        return abs(float(got) - float(expected)) <= TOL
    return got == expected


# ========================================================================= #
#  task applicability -- arity in {2,3}, every revealed/held-out
#  input+output an int (not bool). A documented scope gate, not a silent
#  filter: every excluded task is still reported, with its reason.
# ========================================================================= #
def task_applicability(params: List[str], revealed_rows: List[Dict[str, Any]]
                       ) -> Dict[str, Any]:
    if len(params) not in (2, 3):
        return {"applicable": False, "reason": "arity_not_2_or_3", "arity": len(params)}
    for row in revealed_rows:
        for p in params:
            v = row["inputs"].get(p)
            if not isinstance(v, int) or isinstance(v, bool):
                return {"applicable": False, "reason": "non_integer_input", "arity": len(params)}
        ev = row.get("expected")
        if not isinstance(ev, int) or isinstance(ev, bool):
            return {"applicable": False, "reason": "non_integer_output", "arity": len(params)}
    return {"applicable": True, "arity": len(params)}


def wide_probe_points(params: List[str], revealed_rows: List[Dict[str, Any]]
                      ) -> List[Dict[str, Any]]:
    """The recombination of each argument's OWN observed values across the
    revealed rows -- no new magnitude is introduced, only re-assignment of
    values already seen (the same discipline the orbit result used for
    S3's augmentation)."""
    per_arg = []
    for p in params:
        vals = sorted({row["inputs"][p] for row in revealed_rows})
        per_arg.append(vals)
    points = []
    for combo in itertools.product(*per_arg):
        points.append(dict(zip(params, combo)))
    return points


def _dedup_points(points: List[Dict[str, Any]], params: List[str]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for pt in points:
        key = tuple(pt[p] for p in params)
        if key in seen:
            continue
        seen.add(key)
        out.append(pt)
    return out


# ========================================================================= #
#  INTENT EVIDENCE -- a further weight source, per the author's reframe:
#  a trap is a program that satisfies every revealed row while ignoring
#  the ASKER's declared intent ("top_of_three" declares three parameters
#  and means three"). `arity_gap` = declared_arity - used_arity, read
#  straight off the ACCEPTED program's own IR (reusing D3's
#  `collect_var_refs` verbatim, never reimplemented) against the
#  signature the request declared -- no lexicon, no held-out data.
#  `name_arity_hint` is a light LEXICAL extraction (a numeral word in the
#  function name or prompt) -- explicitly NOT an NLU claim, named as such.
# ========================================================================= #
_NUMERAL_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                  "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6}
_QUANTITY_NOUNS = {"numbers", "values", "integers", "elements", "items",
                   "args", "arguments", "digits"}
_WORD_RE = re.compile(r"[a-z0-9']+")


def name_arity_hint(prompt: Optional[str], func_name: Optional[str]) -> Optional[int]:
    """Function-NAME numeral word first (`top_of_three` -> 3), else a
    PROMPT numeral word within 2 tokens of a quantity noun ("...of three
    numbers"). A light lexical read, not an NLU claim."""
    for tok in re.split(r"[^a-z0-9]+", (func_name or "").lower()):
        if tok in _NUMERAL_WORDS:
            return _NUMERAL_WORDS[tok]
    tokens = _WORD_RE.findall((prompt or "").lower())
    for i, tok in enumerate(tokens):
        if tok in _NUMERAL_WORDS:
            window = tokens[i + 1:i + 3]
            if any(w in _QUANTITY_NOUNS for w in window):
                return _NUMERAL_WORDS[tok]
    return None


def intent_evidence(params: List[str], ir: Optional[Dict[str, Any]],
                    prompt: Optional[str], func_name: Optional[str]) -> Dict[str, Any]:
    declared = len(params)
    used = None
    if ir is not None:
        refs = asv.collect_var_refs(ir)
        used = len(set(params) & refs)
    hint = name_arity_hint(prompt, func_name)
    arity_gap = (declared - used) if used is not None else None
    return {
        "declared_arity": declared, "used_arity": used, "arity_gap": arity_gap,
        "arity_gap_flags_trap": bool(arity_gap is not None and arity_gap > 0),
        "name_arity_hint": hint,
        "name_arity_agrees": (hint == declared) if hint is not None else None,
    }


# ========================================================================= #
#  relaxation family -- REFUTATION FIRST, always. Every function below
#  takes only (params, revealed_rows); no held-out data anywhere.
# ========================================================================= #
def _revealed_input_output_map(params: List[str], revealed_rows: List[Dict[str, Any]]
                               ) -> Dict[Tuple[Any, ...], Any]:
    m = {}
    for row in revealed_rows:
        key = tuple(row["inputs"][p] for p in params)
        m[key] = row["expected"]
    return m


def relax_permutation(params: List[str], revealed_rows: List[Dict[str, Any]],
                      subgroup: Optional[Tuple[int, int]]) -> Dict[str, Any]:
    """subgroup=None -> full S_n; subgroup=(i,j) -> the 2-cycle swapping
    positions i,j only, all other positions fixed. REFUTED iff some
    permutation (within the named subgroup) of some revealed row's own
    argument values lands on an input tuple ALREADY assigned a DIFFERENT
    expected output by the revealed rows themselves (covers both the
    simple "two revealed rows are a permutation pair with different
    outputs" case and any less obvious collision)."""
    n = len(params)
    base = _revealed_input_output_map(params, revealed_rows)
    if subgroup is None:
        perms = list(itertools.permutations(range(n)))
        name = "sym_full_S%d" % n
    else:
        i, j = subgroup
        identity = tuple(range(n))
        swapped = list(identity)
        swapped[i], swapped[j] = swapped[j], swapped[i]
        perms = [identity, tuple(swapped)]
        name = "sym_2cycle_%s_%s" % (params[i], params[j])
    refuted = False
    refuted_reason = None
    augmented: List[Dict[str, Any]] = []
    seen_new: Dict[Tuple[Any, ...], Any] = {}
    for row in revealed_rows:
        vals = [row["inputs"][p] for p in params]
        expected = row["expected"]
        for perm in perms:
            # new_vals[pos] = value that ends up at position `pos` after
            # applying `perm` as "position pos receives the value that was
            # at position perm[pos]"
            new_vals = [vals[perm[pos]] for pos in range(n)]
            key = tuple(new_vals)
            if key in base and base[key] != expected:
                refuted = True
                refuted_reason = ("permuted row %r (from revealed row %r) collides with "
                                  "a differently-labelled revealed row" % (key, tuple(vals)))
            if key in seen_new and seen_new[key] != expected:
                refuted = True
                refuted_reason = refuted_reason or (
                    "two permuted images of revealed rows disagree at %r" % (key,))
            seen_new[key] = expected
    if not refuted:
        for key, expected in seen_new.items():
            if key not in base:
                augmented.append({"inputs": dict(zip(params, key)), "expected": expected})
    # n_supporting_revealed_rows: revealed-row PAIRS that are already
    # permutation-images of each other under this subgroup (evidence for
    # the conjecture already present in the data, distinct from
    # refutation, which looks for a MISMATCH of the same kind).
    n_supporting = 0
    for a, b in itertools.combinations(revealed_rows, 2):
        va = tuple(a["inputs"][p] for p in params)
        vb = tuple(b["inputs"][p] for p in params)
        for perm in perms:
            if tuple(va[perm[pos]] for pos in range(n)) == vb:
                n_supporting += 1
                break
    # value_overlap_plausible: do the OBSERVED VALUE SETS of the permuted
    # positions actually overlap? A weak, mechanical arity/type-plausibility
    # signal distinct from refutation -- permuting two positions whose
    # observed ranges never overlap is a syntactically-legal but
    # semantically-suspicious conjecture (e.g. swapping an index with a
    # magnitude).
    positions = list(range(n)) if subgroup is None else list(subgroup)
    value_sets = []
    for pos in positions:
        value_sets.append({row["inputs"][params[pos]] for row in revealed_rows})
    overlap_plausible = all(
        bool(value_sets[a] & value_sets[b])
        for a, b in itertools.combinations(range(len(value_sets)), 2)) if len(value_sets) > 1 else True
    group_order = math.factorial(n) if subgroup is None else 2
    return {"name": name, "family": "permutation", "subgroup": subgroup,
            "applicable": n >= 2, "refuted": refuted, "refuted_reason": refuted_reason,
            "augmented_rows": augmented if not refuted else [],
            "mdl_bits": math.log2(group_order),
            "n_supporting_revealed_rows": n_supporting,
            "plausibility_signal": overlap_plausible}


def relax_idempotent(params: List[str], revealed_rows: List[Dict[str, Any]]
                     ) -> Dict[str, Any]:
    """Fixed-point conjecture: f(x, x, ..., x) = x. Refuted iff a revealed
    row already has every argument equal to the same value but an output
    that differs from it. Requires >=1 already-equal-args revealed row as
    SUPPORT before any augmentation is manufactured -- an unrefuted-but-
    unsupported conjecture manufactures nothing (reported honestly, not
    smoothed into a positive)."""
    supporting = []
    refuted = False
    refuted_reason = None
    for row in revealed_rows:
        vals = [row["inputs"][p] for p in params]
        if len(set(vals)) == 1:
            v = vals[0]
            if row["expected"] != v:
                refuted = True
                refuted_reason = "revealed row %r has all-equal args but expected %r != %r" % (
                    tuple(vals), row["expected"], v)
            else:
                supporting.append(v)
    supported = bool(supporting) and not refuted
    augmented: List[Dict[str, Any]] = []
    if supported:
        pool = set()
        for row in revealed_rows:
            for p in params:
                pool.add(row["inputs"][p])
        base = _revealed_input_output_map(params, revealed_rows)
        for v in sorted(pool):
            key = tuple(v for _ in params)
            if key not in base:
                augmented.append({"inputs": dict(zip(params, key)), "expected": v})
    return {"name": "idempotent_fixed_point", "family": "idempotence", "subgroup": None,
            "applicable": True, "supported": supported, "refuted": refuted,
            "refuted_reason": refuted_reason, "augmented_rows": augmented,
            # A naive, fixed complexity score (one relation, arity-
            # independent) -- idempotence has no group-order analogue the
            # way permutation subgroups do; recorded as a feature for a
            # LATER weighted collapse to calibrate, not tuned here.
            "mdl_bits": 1.0,
            "n_supporting_revealed_rows": len(supporting),
            "plausibility_signal": supported}


def check_monotonicity(params: List[str], revealed_rows: List[Dict[str, Any]]
                       ) -> Dict[str, Any]:
    """REFUTATION-ONLY (no gap: no augmentation mechanism is constructed --
    see module docstring). Per-argument: collect the sign of
    delta(output)/delta(arg) over revealed-row pairs differing in EXACTLY
    that argument; both signs observed -> refuted in BOTH directions for
    that argument."""
    per_arg = {}
    for p in params:
        signs = set()
        pairs_seen = 0
        for a, b in itertools.combinations(revealed_rows, 2):
            ia, ib = a["inputs"], b["inputs"]
            if any(ia[q] != ib[q] for q in params if q != p):
                continue
            if ia[p] == ib[p]:
                continue
            pairs_seen += 1
            d_arg = ib[p] - ia[p]
            d_out = b["expected"] - a["expected"]
            if isinstance(d_out, (int, float)) and not isinstance(d_out, bool):
                if d_arg * d_out > 0:
                    signs.add("nondecreasing")
                elif d_arg * d_out < 0:
                    signs.add("nonincreasing")
                else:
                    signs.add("flat")
        applicable = pairs_seen > 0
        # both directions observed together (excluding "flat", which is
        # compatible with either) => refute BOTH.
        both = ("nondecreasing" in signs) and ("nonincreasing" in signs)
        per_arg[p] = {
            "applicable": applicable, "pairs_seen": pairs_seen,
            "observed_signs": sorted(signs),
            "nondecreasing_refuted": both,
            "nonincreasing_refuted": both,
            "supported_direction": (
                "nondecreasing" if (applicable and not both and "nondecreasing" in signs)
                else "nonincreasing" if (applicable and not both and "nonincreasing" in signs)
                else "constant" if (applicable and signs == {"flat"})
                else None),
        }
    return per_arg


# ========================================================================= #
#  version space -- V0/V1, gap, per relaxation.
# ========================================================================= #
def matched_pool(s: "srs.Substrate", candidates: List[Tuple[Dict[str, Any], int]],
                 params: List[str], revealed_rows: List[Dict[str, Any]]
                 ) -> List[Tuple[Dict[str, Any], int]]:
    out = []
    for expr, size in candidates:
        ok = True
        for row in revealed_rows:
            got = eval_expr(s, expr, row["inputs"])
            if not numeric_agree(got, row["expected"]):
                ok = False
                break
        if ok:
            out.append((expr, size))
    return out


def _signature(s: "srs.Substrate", expr: Dict[str, Any],
              probe_points: List[Dict[str, Any]]) -> Tuple[Any, ...]:
    sig = []
    for pt in probe_points:
        v = eval_expr(s, expr, pt)
        sig.append(round(v, 9) if isinstance(v, float) else v)
    return tuple(sig)


def count_distinct(s: "srs.Substrate", pool: List[Tuple[Dict[str, Any], int]],
                   probe_points: List[Dict[str, Any]]
                   ) -> Tuple[int, Dict[Tuple[Any, ...], List[Tuple[Dict[str, Any], int]]]]:
    groups: Dict[Tuple[Any, ...], List[Tuple[Dict[str, Any], int]]] = {}
    for expr, size in pool:
        sig = _signature(s, expr, probe_points)
        groups.setdefault(sig, []).append((expr, size))
    return len(groups), groups


def gap_for_relaxation(s: "srs.Substrate", pool: List[Tuple[Dict[str, Any], int]],
                       params: List[str], wide_probe: List[Dict[str, Any]],
                       relax: Dict[str, Any]) -> Dict[str, Any]:
    augmented = relax.get("augmented_rows") or []
    probe_r = _dedup_points(wide_probe + [a["inputs"] for a in augmented], params)
    v0, groups0 = count_distinct(s, pool, probe_r)
    survivors = []
    for expr, size in pool:
        ok = True
        for a in augmented:
            got = eval_expr(s, expr, a["inputs"])
            if not numeric_agree(got, a["expected"]):
                ok = False
                break
        if ok:
            survivors.append((expr, size))
    v1, groups1 = count_distinct(s, survivors, probe_r)
    gap = v0 - v1
    log_ratio = (math.log2(v0 / v1) if v1 > 0 else None)
    unsatisfiable = (v0 > 0 and v1 == 0)
    rep = None
    if survivors:
        best = min(survivors, key=lambda t: (t[1], term_str(t[0])))
        rep = {"term": best[0], "term_str": term_str(best[0]), "size": best[1]}
    return {"n_probe_points": len(probe_r), "v0": v0, "v1": v1, "gap": gap,
            "log2_ratio": log_ratio, "n_augmented_rows": len(augmented),
            "unsatisfiable_under_augmentation": unsatisfiable,
            "n_survivors_raw": len(survivors), "representative": rep}


# ========================================================================= #
#  per-task pipeline
# ========================================================================= #
_SEARCH_FN_SOURCE_MUST_NOT_MENTION = "held_out"


def _held_out_isolation_audit() -> Dict[str, Any]:
    fns = [const_pool_for, generate_candidates, task_applicability, wide_probe_points,
          relax_permutation, relax_idempotent, check_monotonicity, matched_pool,
          count_distinct, gap_for_relaxation, name_arity_hint, intent_evidence]
    hits = {fn.__name__: (_SEARCH_FN_SOURCE_MUST_NOT_MENTION in inspect.getsource(fn))
           for fn in fns}
    return {"functions_checked": sorted(hits), "any_hit": any(hits.values()),
            "hits": {k: v for k, v in hits.items() if v}}


def verify_against_held_out(s: "srs.Substrate", expr: Optional[Dict[str, Any]],
                            held_out_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """MEASUREMENT-ONLY (the sanctioned pattern: reads held-out data,
    never feeds it back into anything above this function). The ONLY
    function in this module allowed to see a held-out row."""
    if expr is None:
        return {"all_ok": None, "checks": []}
    checks = []
    all_ok = True
    for hr in held_out_rows:
        got = eval_expr(s, expr, hr["inputs"])
        ok = numeric_agree(got, hr["expected"])
        checks.append({"inputs": hr["inputs"], "got": got if got is not _EVAL_ERROR else None,
                       "expected": hr["expected"], "ok": ok})
        all_ok = all_ok and ok
    return {"all_ok": all_ok, "checks": checks}


def run_task(s: "srs.Substrate", task_key: Any, params: List[str],
            revealed_rows: List[Dict[str, Any]], held_out_rows: List[Dict[str, Any]],
            witness_rows: Optional[List[Dict[str, Any]]] = None,
            accepted_ir: Optional[Dict[str, Any]] = None,
            prompt: Optional[str] = None, func_name: Optional[str] = None
            ) -> Dict[str, Any]:
    app = task_applicability(params, revealed_rows)
    row = {"task_id": task_key, "params": params, "n_revealed": len(revealed_rows),
          "applicability": app,
          "intent_evidence": intent_evidence(params, accepted_ir, prompt, func_name)}
    if not app["applicable"]:
        return row

    consts = const_pool_for(revealed_rows, params)
    candidates = generate_candidates(tuple(params), consts, MAX_SIZE)
    pool = matched_pool(s, candidates, params, revealed_rows)
    wide_probe = wide_probe_points(params, revealed_rows)
    row["const_pool"] = list(consts)
    row["n_candidates_generated"] = len(candidates)
    row["n_matched_revealed_only"] = len(pool)
    row["n_wide_probe_points"] = len(wide_probe)

    relaxations = []
    n = len(params)
    relaxations.append(relax_permutation(params, revealed_rows, None))
    for i, j in itertools.combinations(range(n), 2):
        relaxations.append(relax_permutation(params, revealed_rows, (i, j)))
    relaxations.append(relax_idempotent(params, revealed_rows))
    mono = check_monotonicity(params, revealed_rows)

    scored = []
    for relax in relaxations:
        entry = dict(relax)
        if relax["refuted"] or not relax.get("applicable", True) or \
           (relax["family"] == "idempotence" and not relax.get("supported")):
            entry["gap_computed"] = False
        elif pool:
            g = gap_for_relaxation(s, pool, params, wide_probe, relax)
            entry.update(g)
            entry["gap_computed"] = True
        else:
            entry["gap_computed"] = False
        scored.append(entry)
    # RETROSPECTIVE, MEASUREMENT-ONLY: score EVERY gap-computed candidate's
    # representative against held-out data -- never used to select (the
    # `eligible`/selection block below reads ONLY gap/refutation/
    # unsatisfiability, unchanged). This is what lets us characterise the
    # cases where gap-as-sole-weight is wrong: was a CORRECT relaxation
    # even on the table, just not the widest-gap one? (per the author's
    # reframe -- "gap is one weight, not the decider"; this is the data a
    # later weighted collapse over gap/mdl_bits/n_supporting_revealed_rows/
    # plausibility_signal would need to be fit and evaluated against.)
    for r in scored:
        if r.get("gap_computed") and r.get("representative"):
            r["held_out_check"] = verify_against_held_out(
                s, r["representative"]["term"], held_out_rows)
        else:
            r["held_out_check"] = {"all_ok": None, "checks": []}

    row["relaxations"] = scored
    row["monotonicity"] = mono

    eligible = [r for r in scored if r.get("gap_computed") and r["gap"] > 0
               and not r.get("unsatisfiable_under_augmentation")]
    selected = None
    if eligible:
        eligible.sort(key=lambda r: (-r["gap"], r["v1"], r["name"]))
        selected = eligible[0]
    row["n_relaxations_considered"] = len(scored)
    row["n_refuted"] = sum(1 for r in scored if r.get("refuted"))
    row["n_gap_scored"] = sum(1 for r in scored if r.get("gap_computed"))
    row["selected_relaxation"] = selected["name"] if selected else None
    row["selected_gap"] = selected["gap"] if selected else None

    verify = None
    if selected and selected.get("representative"):
        verify = verify_against_held_out(s, selected["representative"]["term"], held_out_rows)
        if witness_rows:
            wv = verify_against_held_out(s, selected["representative"]["term"], witness_rows)
            verify["witness_all_ok"] = wv["all_ok"]
            verify["witness_checks"] = wv["checks"]
    row["held_out_verify"] = verify
    row["converted"] = bool(selected and verify and verify.get("all_ok") and
                            (verify.get("witness_all_ok") in (None, True)))
    row["false_selection"] = bool(selected and verify and verify.get("all_ok") is False)

    # gap-as-sole-weight accuracy accounting (the reframed verdict question).
    correct_names = [r["name"] for r in scored
                     if r.get("gap_computed") and r.get("held_out_check", {}).get("all_ok")]
    row["correct_relaxation_names"] = correct_names
    row["any_correct_available"] = bool(correct_names)
    row["gap_argmax_correct"] = bool(selected and selected["name"] in correct_names)
    if selected and correct_names and not row["gap_argmax_correct"]:
        by_name = {r["name"]: r for r in scored}
        row["wrong_selection_feature_comparison"] = {
            "selected": {k: selected.get(k) for k in
                        ("name", "gap", "v0", "v1", "mdl_bits",
                         "n_supporting_revealed_rows", "plausibility_signal")},
            "correct_alternatives": [
                {k: by_name[nm].get(k) for k in
                 ("name", "gap", "v0", "v1", "mdl_bits",
                  "n_supporting_revealed_rows", "plausibility_signal")}
                for nm in correct_names],
        }
    return row


# ========================================================================= #
#  population loaders
# ========================================================================= #
def load_test_tasks() -> Dict[int, Dict[str, Any]]:
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = arc3b.q0_split_tasks(all_tasks)
    test_tasks = splits["test"]
    for t in test_tasks:
        assert "code" not in t, "contamination: code field survived split_tasks"
    return {t["task_id"]: t for t in test_tasks}


def load_ahf() -> Dict[int, Dict[str, Any]]:
    with open(R3_ENDGAME_PATH) as f:
        endgame = json.load(f)
    rows = endgame["arms"]["full_r3"]["runnable_rows"]
    return {r["task_id"]: r for r in rows if r["outcome"] == "accepted_holdout_fail"}


def load_residual_36() -> List[int]:
    with open(STRUCTURAL_PATH) as f:
        d = json.load(f)
    return list(d["new_honest_residual_ids"])


def load_d3_fired_by_task() -> Dict[int, bool]:
    """The PROJECT'S OWN D3 (`unread_declared_param`) verdict per task,
    read from the already-frozen, already-cited structural-verdicts
    artifact -- used here ONLY to characterise arity_gap's false
    positives (is this ALSO an independently-confirmed structural defect,
    or a case the sparse revealed rows can't even confirm?), never to
    select or refute anything above."""
    with open(STRUCTURAL_PATH) as f:
        d = json.load(f)
    out = {}
    for k, v in d["per_task"].items():
        d3 = v.get("detectors", {}).get("d3_unread_declared_param", {})
        out[int(k)] = bool(d3.get("fired"))
    return out


def run_all() -> Dict[str, Any]:
    t0 = time.time()
    s = srs.Substrate()

    with open(BATTERY_PATH) as f:
        battery = json.load(f)
    br10 = next(t for t in battery["tasks"] if t["id"] == "br_10_top_of_three")
    br10_revealed = [{"inputs": r["inputs"], "expected": r["expected"]}
                     for r in br10["example_rows"]]
    br10_held_out = [{"inputs": r["inputs"], "expected": r["expected"]}
                     for r in br10["held_out_rows"]]
    # A hand-constructed witness, independent of BOTH revealed and
    # held-out rows above -- domain-known semantics ("top of three" =
    # max(a,b,c)), used ONLY to score the already-selected program, never
    # to select it.
    br10_witness = [{"inputs": {"a": 100, "b": 3, "c": 47}, "expected": 100},
                    {"inputs": {"a": -1, "b": -50, "c": -2}, "expected": -1}]
    # br_10's own accepted trap, exactly as `PROGRAM_SYNTHESIS_ARC5_ORBIT_
    # RESULT.md` / `scripts/arc5_shape_constraint_probe.py` established it
    # live (`Max(a, b)`, ignoring `c`) -- read here ONLY for the intent-
    # evidence arity_gap feature (which params does the ACCEPTED program
    # read), never as a search input.
    BR10_TRAP_IR = {"type": "Max", "items": [{"type": "Var", "name": "a"},
                                             {"type": "Var", "name": "b"}]}
    br10_row = run_task(s, "br_10_top_of_three", ["a", "b", "c"], br10_revealed,
                        br10_held_out, witness_rows=br10_witness,
                        accepted_ir=BR10_TRAP_IR, prompt=br10["request_text"],
                        func_name="top_of_three")

    tasks_by_id = load_test_tasks()
    ahf = load_ahf()
    residual_36 = load_residual_36()

    def mbpp_row(tid: int) -> Dict[str, Any]:
        ir = ahf[tid]["ir"]
        params = afa._param_names(ir)
        parsed = ms.parse_asserts(tasks_by_id[tid])
        split = ms.split_rows(parsed["rows"], "primary")
        revealed = list(split["revealed"])
        held_out = list(split["held_out"])
        sf = ms.signature_facts(tasks_by_id[tid])
        return run_task(s, tid, params, revealed, held_out, accepted_ir=ir,
                        prompt=tasks_by_id[tid]["prompt"], func_name=sf.get("func_name"))

    reopened_rows = [mbpp_row(tid) for tid in REOPENED_12]
    residual_rows = [mbpp_row(tid) for tid in sorted(residual_36)]

    def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        applicable = [r for r in rows if r["applicability"]["applicable"]]
        converted = [r["task_id"] for r in rows if r.get("converted")]
        false_sel = [r["task_id"] for r in rows if r.get("false_selection")]
        selected_rows = [r for r in rows if r.get("selected_relaxation")]
        selected = [r["task_id"] for r in selected_rows]
        n_refuted_total = sum(r.get("n_refuted", 0) for r in rows)
        n_considered_total = sum(r.get("n_relaxations_considered", 0) for r in rows)
        # gap-as-sole-weight accuracy accounting (the reframed verdict
        # question: not "criterion vs lexicon" but "how good a weight is
        # gap alone, and where does it fail"). Denominator = tasks where
        # a selection was actually made (a null/no-selection task says
        # nothing about gap's ACCURACY, only its coverage).
        gap_correct_ids = [r["task_id"] for r in selected_rows if r.get("gap_argmax_correct")]
        gap_wrong_ids = [r["task_id"] for r in selected_rows if not r.get("gap_argmax_correct")]
        oracle_available_ids = [r["task_id"] for r in rows if r.get("any_correct_available")]
        wrong_but_correct_was_available = [
            {"task_id": r["task_id"], "comparison": r.get("wrong_selection_feature_comparison")}
            for r in selected_rows
            if not r.get("gap_argmax_correct") and r.get("any_correct_available")]
        return {
            "n_tasks": len(rows), "n_applicable": len(applicable),
            "applicable_ids": [r["task_id"] for r in applicable],
            "inapplicable_ids_and_reasons": [
                {"task_id": r["task_id"], "reason": r["applicability"]["reason"]}
                for r in rows if not r["applicability"]["applicable"]],
            "selected_ids": selected, "converted_ids": converted,
            "false_selection_ids": false_sel,
            "n_relaxation_instances_considered": n_considered_total,
            "n_relaxation_instances_refuted": n_refuted_total,
            "refutation_rate": (n_refuted_total / n_considered_total
                               if n_considered_total else None),
            "gap_as_sole_weight": {
                "n_selected": len(selected_rows),
                "gap_argmax_correct_ids": gap_correct_ids,
                "gap_argmax_wrong_ids": gap_wrong_ids,
                "gap_selection_accuracy": (len(gap_correct_ids) / len(selected_rows)
                                          if selected_rows else None),
                "oracle_ceiling_ids": oracle_available_ids,
                "oracle_ceiling_rate": (len(oracle_available_ids) / len(applicable)
                                       if applicable else None),
                "wrong_selection_characterization": wrong_but_correct_was_available,
            },
        }

    # ---- intent-evidence (arity_gap) vs gap-score: head-to-head, same
    # population (the tasks where GROUND TRUTH -- "a relaxation from this
    # catalogue IS correct" -- is even DEFINED, i.e. the applicable
    # population across all three groups). Precision/recall for each
    # predictor against the SAME ground truth (`any_correct_available`).
    all_rows = [br10_row] + reopened_rows + residual_rows
    applicable_all = [r for r in all_rows if r["applicability"]["applicable"]]
    d3_fired_by_task = load_d3_fired_by_task()

    def _confusion(pred_key_fn):
        tp, fp, fn, tn = [], [], [], []
        for r in applicable_all:
            gt = bool(r.get("any_correct_available"))
            pred = bool(pred_key_fn(r))
            tid = r["task_id"]
            if pred and gt:
                tp.append(tid)
            elif pred and not gt:
                fp.append(tid)
            elif not pred and gt:
                fn.append(tid)
            else:
                tn.append(tid)
        precision = len(tp) / (len(tp) + len(fp)) if (tp or fp) else None
        recall = len(tp) / (len(tp) + len(fn)) if (tp or fn) else None
        return {"tp_ids": tp, "fp_ids": fp, "fn_ids": fn, "tn_ids": tn,
               "precision": precision, "recall": recall}

    intent_vs_gap = {
        "_caveat": ("n=%d applicable tasks total -- FAR too small to power "
                   "a precision/recall claim; reported honestly as a "
                   "head-to-head on the only population where ground "
                   "truth (any_correct_available) is defined, not as a "
                   "generalising result." % len(applicable_all)),
        "ground_truth": "any_correct_available (a relaxation in this "
                        "catalogue passes held-out for this task)",
        "n_applicable": len(applicable_all),
        "n_ground_truth_positive": sum(1 for r in applicable_all
                                       if r.get("any_correct_available")),
        "arity_gap_predictor": _confusion(
            lambda r: r["intent_evidence"]["arity_gap_flags_trap"]),
        "gap_score_predictor": _confusion(
            lambda r: r.get("selected_relaxation") is not None),
        "per_task": [
            {"task_id": r["task_id"],
             "any_correct_available": r.get("any_correct_available"),
             "arity_gap_flags_trap": r["intent_evidence"]["arity_gap_flags_trap"],
             "gap_score_flags_trap": r.get("selected_relaxation") is not None,
             "n_matched_revealed_only": r.get("n_matched_revealed_only"),
             "d3_unread_declared_param_fired": d3_fired_by_task.get(r["task_id"])
                                              if isinstance(r["task_id"], int) else None,
             "intent_evidence": r["intent_evidence"]}
            for r in applicable_all],
        "confound_note": (
            "RAW precision/recall above treats gap-score's silence as a "
            "negative prediction, but gap-score can ONLY ever predict "
            "positive when n_matched_revealed_only > 0 (this measurement's "
            "tiny Plus/Minus/Times/Max/Min/Abs/Neg, size<=5 grammar finds "
            "ANY candidate at all matching the revealed rows) -- it is "
            "silent on every task where the grammar's own version space "
            "is empty, REGARDLESS of whether that task is a genuine trap. "
            "Cross-checked against this project's OWN, already-frozen D3 "
            "(unread_declared_param) detector (`results/"
            "arc4_structural_verdicts.json`): every arity_gap FALSE "
            "POSITIVE in this run has n_matched_revealed_only==0 (gap-score "
            "never got a chance to fire), and D3 independently CONFIRMS "
            "most of them as genuine structural defects, not arity_gap "
            "noise -- see arity_gap_fp_d3_cross_check below."
        ),
        "arity_gap_fp_d3_cross_check": [
            {"task_id": r["task_id"],
             "d3_fired": d3_fired_by_task.get(r["task_id"]) if isinstance(r["task_id"], int) else None,
             "n_matched_revealed_only": r.get("n_matched_revealed_only")}
            for r in applicable_all
            if r["intent_evidence"]["arity_gap_flags_trap"] and not r.get("any_correct_available")],
    }

    result = {
        "_README": ("Arc 5 widest-gap probe. Read br_10 first (the "
                   "headline), then reopened_12 (generalisation), then "
                   "residual_36 (the honest-residual coverage question), "
                   "then intent_vs_gap_head_to_head (arity_gap as a "
                   "rival/companion weight)."),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provenance": {
            "reads": [FIXTURE_PATH, R3_ENDGAME_PATH, STRUCTURAL_PATH, BATTERY_PATH],
            "writes": [OUT_PATH],
            "modifies_synthesis_engine_seed_or_spec_code": False,
        },
        "grammar": {"binary_ops": list(BINARY_OPS), "unary_ops": list(UNARY_OPS),
                   "max_size": MAX_SIZE, "const_cap": CONST_CAP,
                   "base_consts": list(BASE_CONSTS)},
        "br_10": br10_row,
        "reopened_12": {"rows": reopened_rows, "summary": summarize(reopened_rows)},
        "residual_36": {"rows": residual_rows, "summary": summarize(residual_rows)},
        "intent_vs_gap_head_to_head": intent_vs_gap,
        "held_out_isolation_audit": _held_out_isolation_audit(),
        "environment": {k: os.environ.get(k) for k in
                       ("OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED")},
        "elapsed_seconds": None,
    }
    result["elapsed_seconds"] = round(time.time() - t0, 2)
    return result


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


def main() -> None:
    run1 = run_all()
    run2 = run_all()

    def _strip_clock(r: Dict[str, Any]) -> Dict[str, Any]:
        r = dict(r)
        r["measured_at"] = None
        r["elapsed_seconds"] = None
        return r

    h1 = hashlib.sha256(_canon(_strip_clock(run1)).encode()).hexdigest()
    h2 = hashlib.sha256(_canon(_strip_clock(run2)).encode()).hexdigest()
    run1["determinism"] = {"twin_run_sha256_match": h1 == h2, "sha256": h1}
    assert h1 == h2, "NON-DETERMINISTIC across twin runs -- %s != %s" % (h1, h2)

    with open(OUT_PATH, "w") as f:
        json.dump(run1, f, indent=2, default=str, sort_keys=True)
    print("wrote", OUT_PATH)
    print("br_10 selected:", run1["br_10"]["selected_relaxation"],
         "gap:", run1["br_10"]["selected_gap"], "converted:", run1["br_10"]["converted"])
    print("reopened_12 summary:", json.dumps(run1["reopened_12"]["summary"], indent=2))
    print("residual_36 summary:", json.dumps(run1["residual_36"]["summary"], indent=2))
    h2h = run1["intent_vs_gap_head_to_head"]
    print("intent_vs_gap n_applicable=%d n_gt_pos=%d" %
         (h2h["n_applicable"], h2h["n_ground_truth_positive"]))
    print("  arity_gap predictor:", {k: v for k, v in h2h["arity_gap_predictor"].items()
                                     if k in ("precision", "recall", "tp_ids", "fp_ids", "fn_ids")})
    print("  gap_score predictor:", {k: v for k, v in h2h["gap_score_predictor"].items()
                                     if k in ("precision", "recall", "tp_ids", "fp_ids", "fn_ids")})
    print("elapsed:", run1["elapsed_seconds"], "s")


if __name__ == "__main__":
    main()
