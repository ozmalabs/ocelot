#!/usr/bin/env python
"""arc6_verdict_report — PRICE the non-scalar row verdict.

Reads the two measured arms (`results/arc6_verdict_before.json`,
`results/arc6_verdict_after.json`), runs the CONSTRUCTED-WITNESS sweep for
every newly-accepted candidate LIVE against the current engine, measures
the list/tuple type-collapse exposure, checks the HS2-class regression
bar, and writes `results/arc6_verdict_pricing.json`.

THE FOUR MEASUREMENTS (the orchestrator's phase-1 questions):

  1. UPSIDE     newly accepted, and — separately — newly accepted AND
                CORRECT, each correctness claim proven by a sweep of
                CONSTRUCTED inputs that are neither revealed nor held-out
                rows, judged against the task's own reference
                implementation (`code`, read for MEASUREMENT ONLY).
  2. DOWNSIDE   `list` and `tuple` are the same `Value::Tuple`, so a
                comparison that reads `cmp_ok` can equate values the
                reference distinguishes.  For each newly-accepted
                candidate we ask whether the accept SURVIVES a
                type-SENSITIVE comparison, and if not, whether the
                divergence is the container type alone.
  3. REGRESSION the after pass-list must be a superset of the before
                pass-list AND of the frozen 35 (`results/arc5_final.json`).
  4. `got`      every rule/adapter that reads the `got` attribute, and
                whether it is affected.

CONTAMINATION.  Constructed inputs are generated MECHANICALLY from the
row schema by type-driven mutation; every generated input equal to a
revealed OR held-out row is DISCARDED.  `task["code"]` is executed only
as the measurement ORACLE, after every arm has already been measured; it
enters no codebook, cue vocabulary or taught shape.

Run:
  OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python scripts/arc6_verdict_report.py
"""
from __future__ import annotations

import json
import math
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

import mbpp_arc3_battery as arc3b  # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402

RESULTS = os.path.join(ROOT, "results")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
ARC5_FINAL = os.path.join(RESULTS, "arc5_final.json")
OUT = os.path.join(RESULTS, "arc6_verdict_pricing.json")

KNOWN_FIVE = [106, 161, 257, 424, 450]
_Z = 1.959963984540054


def wilson(k, n):
    if n == 0:
        return {"k": 0, "n": 0, "p": None, "ci95": [None, None]}
    p = k / n
    d = 1 + _Z * _Z / n
    c = (p + _Z * _Z / (2 * n)) / d
    hw = _Z * math.sqrt(p * (1 - p) / n + _Z * _Z / (4 * n * n)) / d
    return {"k": k, "n": n, "p": round(p, 6),
            "ci95": [round(max(0.0, c - hw), 6), round(min(1.0, c + hw), 6)]}


def comparator_probe():
    """LIVE, both directions: what does the substrate's `Eq` say, and what
    does Python's `==` (which is what `_row_cmp_ok` uses) say, on the pairs
    a row verdict can actually see?  This is the blast-radius measurement:
    swapping the comparator is NOT semantics-preserving on SCALAR rows."""
    import substrate_rs as srs
    from domains import prog_synthesis as psy
    from fractions import Fraction
    s = srs.Substrate()

    def lit(v):
        return {"type": "Lit", "value": v}

    def sub_eq(a, b):
        return s._inner.evaluate({"type": "Eq", "a": lit(a), "b": lit(b)}, {})

    pairs = [(1, True), (0, False), (1.0, True), (0.0, False), (1, 1.0),
             (2.0, 2), (0.5, False), ((1, 2), [1, 2]), ("a", "a"),
             (Fraction(1, 1), True)]
    rows = []
    for a, b in pairs:
        try:
            se = bool(sub_eq(a, b))
        except TypeError:  # a value the PyO3 boundary cannot carry (Fraction)
            se = "not_representable_at_the_pyo3_boundary"
        rows.append({
            "a": repr(a), "b": repr(b),
            "substrate_Eq": se,
            "python_eq": bool(a == b),
            "row_cmp_ok": psy._row_cmp_ok(a, b, None, False),
        })
    diverge = [r for r in rows if r["substrate_Eq"] != (r["row_cmp_ok"] == 1.0)]
    return {"pairs": rows, "diverging_pairs": diverge,
            "reading": ("every diverging pair is a case the candidate makes "
                        "LOOSER on a PLAIN row -- including SCALAR rows the "
                        "change was not aimed at.  (1,2) vs [1,2] diverges "
                        "the other way, but only in this synthetic probe: on "
                        "a real row `expected` has already been round-tripped "
                        "through the graph and is a tuple, so cmp_ok says 1.0 "
                        "there too.)")}


def string_order_probe(after):
    """PREREG §4's LIVE DEFECT, reached by the newly-admitted class.

    `cmp_value` orders `Str` by INTERNER SYMBOL ID, so ordering strings
    depends on the order they were interned INTO THAT SUBSTRATE.  The row
    verdict evaluates on the GOAL's own long-lived substrate
    (`eval_and_record` -> `sub._inner.evaluate`), which is primed by the
    seed load and by everything the task did before.  A non-scalar row
    verdict newly admits list-output programs that call
    `MaxOver`/`MinOver`/`sorted` over STRING elements -- so it newly makes
    an ACCEPT depend on that defect.  This probe evaluates the same
    accepted IR on a fresh substrate, on a booted one, and on a booted one
    with the interner deliberately primed in reverse."""
    import substrate_rs as srs
    from domains import prog_synthesis as psy
    from domains.prog_ir_emit import NATIVE_ORACLES

    def oracles():
        items = []
        for n in sorted(NATIVE_ORACLES):
            items.append({"type": "Lit", "value": n})
            items.append({"type": "Lit", "value": "builtin"})
        return {"type": "MkDict", "items": items}

    def ev_on(s, ir, env):
        return s._inner.evaluate(
            {"type": "ProgEval", "prog": ir, "env": {"type": "Var", "name": "e"},
             "oracles": oracles(), "fuel": psy._FUEL, "field": ""}, {"e": env})

    cases = [("393", {"a": [["zz"], ["aa", "bb"], ["cc", "dd"]]},
              "max(input_list, key=len) -> ['aa','bb'] (FIRST of length 2)"),
             ("457", {"a": [["q", "r"], ["s", "t"], ["u"]]},
              "min(lst, key=len) -> ['u']")]
    prime = ["zz", "uu", "tt", "ss", "rr", "qq", "cc", "dd", "bb", "aa"]
    out = []
    for tid, env, meaning in cases:
        ir = after["per_task"][tid]["ir"]
        s1 = srs.Substrate()
        s2, _ = arc3b.boot_full_r3()
        s3, _ = arc3b.boot_full_r3()
        for w in prime:
            s3.add_node("Prime", {"v": w})
        r1 = ev_on(s1, ir, env).get("result")
        r2 = ev_on(s2, ir, env).get("result")
        r3 = ev_on(s3, ir, env).get("result")
        out.append({"task_id": int(tid), "input": env,
                    "reference_meaning": meaning,
                    "fresh_substrate": r1, "booted_substrate": r2,
                    "booted_then_interner_primed_in_reverse": r3,
                    "unstable": not (r1 == r2 == r3)})
    return {"probes": out,
            "any_unstable": any(p["unstable"] for p in out),
            "reading": ("an UNSTABLE row means the accepted program's answer "
                        "-- and therefore the verdict -- depends on interner "
                        "history.  PREREG §4 registers this defect as NOT an "
                        "arc-6 deliverable and says a later build must not "
                        "quietly inherit it.  A non-scalar row verdict makes "
                        "the pipeline inherit it.")}


def _jdefault(o):
    """`mbpp_arc3_battery._json_default` plus the two shapes only this
    report ever sees: `Fraction` (arc-5's exact rational domain reaching
    the adapter boundary -- see TIER0 §7.3) and any other repr-able."""
    import fractions
    if isinstance(o, fractions.Fraction):
        return {"__fraction__": [o.numerator, o.denominator]}
    try:
        return arc3b._json_default(o)
    except TypeError:
        return {"__repr__": repr(o)}


def snap(label):
    with open(os.path.join(RESULTS, "arc6_verdict_%s.json" % label)) as f:
        return json.load(f)


# --------------------------------------------------------------------------
#  the reference oracle (MEASUREMENT ONLY) + constructed-input generation
# --------------------------------------------------------------------------
def _ref_fn(task, func_name):
    ns = {}
    exec(compile(task["code"], "<mbpp:%s>" % task["task_id"], "exec"), ns)  # noqa: S102
    fn = ns.get(func_name)
    if fn is None:  # the reference names it differently; take the last def
        cands = [v for v in ns.values() if callable(v) and getattr(v, "__module__", None) is None]
        fn = cands[-1] if cands else None
    return fn


def _hashable(v):
    if isinstance(v, (list, tuple)):
        return ("seq",) + tuple(_hashable(x) for x in v)
    if isinstance(v, (set, frozenset)):
        return ("set",) + tuple(sorted((repr(x) for x in v)))
    if isinstance(v, dict):
        return ("dict",) + tuple(sorted((repr(k), _hashable(x)) for k, x in v.items()))
    return ("v", repr(v))


_WORDS = ["zebra", "kiwi", "aa", "bcd", "python program", "x", "Hello World",
          "abcabc", "  pad  "]


def _variants(v, rng_seed):
    """Type-driven mutations of ONE input value.  Mechanical; no task
    knowledge whatsoever."""
    out = []
    if isinstance(v, bool):
        out = [not v, v]
    elif isinstance(v, int):
        out = [v + 1, v + 2, v * 2 + 1, abs(v) + 7, 1, 2, 3, 5, 12]
    elif isinstance(v, float):
        out = [v + 1.0, v * 2.0, 1.5, 3.25, 10.0]
    elif isinstance(v, str):
        out = [v[::-1], v + v, v.upper(), v.lower()] + _WORDS
    elif isinstance(v, (list, tuple)):
        seq = list(v)
        out = [seq[::-1]]
        if seq:
            out.append(seq[:1])
            out.append(seq + [seq[0]])
            out.append(seq[1:] + seq[:1])
            inner = seq[0]
            if isinstance(inner, (int, float)) and not isinstance(inner, bool):
                out.append([x + 1 if isinstance(x, (int, float)) and not isinstance(x, bool)
                            else x for x in seq])
                out.append(sorted(seq, key=repr))
                out.append([inner] * 3)
            elif isinstance(inner, str):
                out.append([s[::-1] for s in seq])
                out.append(sorted(seq))
                out.append(seq + ["zz"])
            elif isinstance(inner, (list, tuple)):
                out.append([list(x)[::-1] for x in seq])
                out.append([list(seq[0]) + [9]] + [list(x) for x in seq[1:]])
                out.append([list(seq[0])] * 2)
        if isinstance(v, tuple):
            out = [tuple(x) if isinstance(x, list) else x for x in out]
    elif isinstance(v, (set, frozenset)):
        out = [type(v)(list(v)[:1]), type(v)(list(v) + [99])]
    elif isinstance(v, dict):
        out = [dict(list(v.items())[:1])]
    return out


def constructed_inputs(rows, limit=24):
    """New input dicts, generated by mutating each known row one ARGUMENT
    at a time (and, for multi-arg tasks, in pairs).  Every input equal to
    a KNOWN row's input (revealed or held-out) is discarded."""
    known = {_hashable(r["inputs"]) for r in rows}
    seen = set(known)
    out = []
    names = sorted(rows[0]["inputs"]) if rows else []
    for r in rows:
        base = r["inputs"]
        for nm in names:
            for alt in _variants(base[nm], 0):
                cand = dict(base)
                cand[nm] = alt
                h = _hashable(cand)
                if h in seen:
                    continue
                seen.add(h)
                out.append(cand)
                if len(out) >= limit:
                    return out
    # pair mutations, for the multi-arg tasks the single-arg sweep under-covers
    for r in rows:
        base = r["inputs"]
        if len(names) < 2:
            break
        alts = {nm: _variants(base[nm], 0) for nm in names}
        for i in range(min(6, min((len(a) for a in alts.values()), default=0))):
            cand = {nm: alts[nm][i] for nm in names}
            h = _hashable(cand)
            if h in seen:
                continue
            seen.add(h)
            out.append(cand)
            if len(out) >= limit:
                return out
    return out


def _norm(v):
    if isinstance(v, (list, tuple)):
        return ["#seq"] + [_norm(x) for x in v]
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in v.items()}
    return v


def _typed(v):
    """Type-SENSITIVE normal form: list and tuple are DIFFERENT."""
    if isinstance(v, list):
        return ["#list"] + [_typed(x) for x in v]
    if isinstance(v, tuple):
        return ["#tuple"] + [_typed(x) for x in v]
    if isinstance(v, dict):
        return {k: _typed(x) for k, x in v.items()}
    if isinstance(v, (set, frozenset)):
        return ["#set"] + sorted(repr(x) for x in v)
    return v


def _num_close(a, b, tol):
    try:
        return math.isclose(float(a), float(b), rel_tol=float(tol), abs_tol=1e-9)
    except (TypeError, ValueError):
        return False


def sweep(task, ir, rows, tol, unordered):
    """Run the ACCEPTED program and the REFERENCE on constructed inputs."""
    func_name = None
    for stmt in task.get("test_list", []):
        f = ms.classify_assert(stmt)
        if f.get("ok"):
            func_name = f["func_name"]
            break
    fn = _ref_fn(task, func_name)
    inputs = constructed_inputs(rows)
    names = sorted(rows[0]["inputs"]) if rows else []
    recs = []
    for env in inputs:
        try:
            ref = fn(*[env[n] for n in names])
        except Exception as e:  # noqa: BLE001 — an input the reference rejects is not a probe
            recs.append({"inputs": env, "skipped": "reference_raised:%s" % type(e).__name__})
            continue
        try:
            out = arc3b.prog_eval(ir, dict(env))
            halted = out.get("halted") is True and out.get("trap") is None
            got = out.get("result")
        except Exception as e:  # noqa: BLE001
            halted, got = False, "exception:%s" % type(e).__name__
        if not halted:
            recs.append({"inputs": env, "ref": ref, "got": None,
                         "trap": str(out.get("trap"))[:80] if isinstance(out, dict) else None,
                         "norm_ok": False, "typed_ok": False})
            continue
        if unordered:
            try:
                norm_ok = frozenset(got if isinstance(got, (list, tuple, set, frozenset)) else [got]) \
                    == frozenset(ref if isinstance(ref, (list, tuple, set, frozenset)) else [ref])
            except TypeError:
                norm_ok = False
            typed_ok = norm_ok
        elif tol is not None:
            norm_ok = typed_ok = _num_close(got, ref, tol)
        else:
            norm_ok = _norm(got) == _norm(ref)
            typed_ok = _typed(got) == _typed(ref)
        recs.append({"inputs": env, "ref": ref, "got": got,
                     "norm_ok": bool(norm_ok), "typed_ok": bool(typed_ok),
                     "ref_type": type(ref).__name__, "got_type": type(got).__name__})
    # --- the CAUSAL collapse test, on the task's OWN rows -----------------
    # `expected` here is the literal from the corpus's own assert, with its
    # REAL Python type (mbpp_spec.parse_asserts never round-trips it through
    # the graph).  `got` is what the substrate returns -- always a tuple for
    # any sequence, because list and tuple are one `Value::Tuple`.  So:
    #   collapse_required : some row agrees only when the container type is
    #                       ignored  -> the accept EXISTS ONLY under the
    #                       collapse
    #   corpus_assert_ok  : the accepted program satisfies the corpus's own
    #                       `assert f(...) == <literal>` under real Python
    #                       semantics, on every row.
    own = []
    for r in rows:
        try:
            out = arc3b.prog_eval(ir, dict(r["inputs"]))
            halted = out.get("halted") is True and out.get("trap") is None
            g = out.get("result")
        except Exception:  # noqa: BLE001
            halted, g = False, None
        exp = r["expected"]
        if not halted:
            own.append({"inputs": r["inputs"], "expected": exp, "got": None,
                        "norm_ok": False, "typed_ok": False})
            continue
        if r.get("unordered"):
            try:
                ok = frozenset(g if isinstance(g, (list, tuple, set, frozenset)) else [g]) \
                    == frozenset(exp if isinstance(exp, (list, tuple, set, frozenset)) else [exp])
            except TypeError:
                ok = False
            own.append({"inputs": r["inputs"], "expected": exp, "got": g,
                        "norm_ok": bool(ok), "typed_ok": bool(ok)})
            continue
        if r.get("tol") is not None:
            ok = _num_close(g, exp, r["tol"])
            own.append({"inputs": r["inputs"], "expected": exp, "got": g,
                        "norm_ok": bool(ok), "typed_ok": bool(ok)})
            continue
        own.append({"inputs": r["inputs"], "expected": exp, "got": g,
                    "norm_ok": _norm(g) == _norm(exp),
                    "typed_ok": _typed(g) == _typed(exp)})
    collapse_required = any(o["norm_ok"] and not o["typed_ok"] for o in own)
    corpus_assert_ok = all(o["typed_ok"] for o in own)

    live = [r for r in recs if "skipped" not in r]
    n = len(live)
    n_norm = sum(1 for r in live if r["norm_ok"])
    n_typed = sum(1 for r in live if r["typed_ok"])
    ref_types = sorted({r["ref_type"] for r in live if "ref_type" in r})
    got_types = sorted({r["got_type"] for r in live if "got_type" in r})
    verdict = ("CORRECT" if n and n_norm == n else
               "NO_PROBES" if not n else "COINCIDENTAL_FIT")
    collapse = (n_typed < n_norm)
    return {
        "accept_requires_list_tuple_collapse": bool(collapse_required),
        "satisfies_corpus_own_assert_semantics": bool(corpus_assert_ok),
        "own_rows": own,
        "constructed_mismatches": [r for r in recs
                                   if "skipped" not in r and not r["norm_ok"]][:10],
        "n_constructed_probed": n,
        "n_reference_rejected_inputs": len(recs) - n,
        "n_norm_agree": n_norm,
        "n_typed_agree": n_typed,
        "reference_return_types": ref_types,
        "substrate_return_types": got_types,
        "verdict": verdict,
        "type_collapse_dependent": bool(collapse),
        "rows": recs[:14],
    }


# --------------------------------------------------------------------------
def main():
    before, after = snap("before"), snap("after")
    B, A = set(before["pass_ids"]), set(after["pass_ids"])
    Bacc, Aacc = set(before["accepted_ids"]), set(after["accepted_ids"])
    with open(ARC5_FINAL) as f:
        arc5 = set(json.load(f)["pass_ids"])

    with open(FIXTURE) as f:
        all_tasks = json.load(f)
    by_id = {t["task_id"]: t for t in all_tasks}

    new_acc = sorted(Aacc - Bacc)
    lost_acc = sorted(Bacc - Aacc)
    new_pass = sorted(A - B)
    lost_pass = sorted(B - A)

    sweeps = {}
    for tid in new_acc:
        task = by_id[tid]
        parsed = ms.parse_asserts(task)
        rows = parsed["rows"]
        spec = ms.split_rows(rows, "primary")
        ir = after["per_task"][str(tid)]["ir"]
        tol = rows[0].get("tol")
        unordered = bool(rows[0].get("unordered"))
        s = sweep(task, ir, rows, tol, unordered)
        s["became_pass"] = tid in A
        s["holdout_all_ok"] = bool((after["per_task"][str(tid)].get("holdout") or {}).get("all_ok"))
        s["n_revealed"] = len(spec["revealed"])
        s["n_held_out"] = len(spec["held_out"])
        sweeps[str(tid)] = s

    correct = [t for t in new_acc if sweeps[str(t)]["verdict"] == "CORRECT"]
    coincidental = [t for t in new_acc if sweeps[str(t)]["verdict"] == "COINCIDENTAL_FIT"]
    unprobed = [t for t in new_acc if sweeps[str(t)]["verdict"] == "NO_PROBES"]
    # CAUSAL, measured on the task's OWN rows (see `sweep`): the accept
    # exists only because list and tuple are one Value::Tuple.
    collapse_dep = [t for t in new_acc
                    if sweeps[str(t)]["accept_requires_list_tuple_collapse"]]
    # A FALSE ACCEPT under the corpus's own grading semantics: the accepted
    # program does NOT satisfy `assert f(...) == <literal>` in real Python.
    collapse_false = [t for t in new_acc
                      if not sweeps[str(t)]["satisfies_corpus_own_assert_semantics"]]
    # Wrong in general as well -- the coincidental-fit mechanism, which the
    # collapse newly EXPOSES for list-valued answers.
    wrong_in_general = coincidental
    new_pass_correct = [t for t in new_pass if sweeps[str(t)]["verdict"] == "CORRECT"]
    new_pass_coincidental = [t for t in new_pass if sweeps[str(t)]["verdict"] != "CORRECT"]

    converted_known = [t for t in KNOWN_FIVE
                       if t in new_acc and sweeps[str(t)]["verdict"] == "CORRECT"]

    # Was the collapse load-bearing at the ACCEPT layer before this change?
    # Mechanical: the expected-value types of the 36 baseline passes.
    base_types = {}
    for tid in sorted(B):
        rws = ms.parse_asserts(by_id[tid])["rows"]
        base_types[str(tid)] = sorted({type(r["expected"]).__name__ for r in rws})
    base_nonscalar = sorted(int(k) for k, v in base_types.items()
                            if any(t not in ("int", "float", "str", "bool") for t in v))

    # Question 4 -- every rule that reads the `got` attribute family.
    with open(os.path.join(ROOT, "seeds", "program_synthesis.json")) as f:
        seed = json.load(f)
    got_readers = {}
    for r in seed["rules"]:
        s_ = json.dumps(r)
        keys = [k for k in ('"key": "got"', '"key": "fu_got"',
                            '"key": "got_json"', '"key": "cmp_ok"') if k in s_]
        if keys:
            got_readers[r["name"]] = [k.split('"')[3] for k in keys]

    bar = {
        "bar_1_three_of_five_known_convert_with_witnesses": {
            "known_five": KNOWN_FIVE,
            "converted_with_constructed_witness": converted_known,
            "n": len(converted_known), "required": 3,
            "verdict": "PASS" if len(converted_known) >= 3 else "FAIL",
        },
        "bar_2_zero_false_accepts_from_list_tuple_collapse": {
            "newly_accepted_whose_accept_needs_the_collapse": collapse_dep,
            "n_needs_the_collapse": len(collapse_dep),
            "false_accepts_fail_the_corpus_own_assert_semantics": collapse_false,
            "n_false_accepts": len(collapse_false),
            "also_wrong_in_general_coincidental_fits": wrong_in_general,
            "n_wrong_in_general": len(wrong_in_general),
            "verdict": "PASS" if not collapse_false else "FAIL",
        },
        "bar_3_thirty_five_pass_ids_preserved": {
            "arc5_final_35": sorted(arc5),
            "after_is_superset_of_arc5_35": arc5 <= A,
            "after_is_superset_of_before_36": B <= A,
            "lost_pass_ids": lost_pass,
            "lost_accepted_ids": lost_acc,
            "verdict": "PASS" if (arc5 <= A and B <= A and not lost_pass) else "FAIL",
        },
    }
    go = all(v["verdict"] == "PASS" for v in bar.values())

    rec = {
        "_README": (
            "arc6 NON-SCALAR ROW VERDICT -- PRICING.  Paired id lists, never "
            "a bare count.  THE AGGREGATE IS UNDERPOWERED BY CONSTRUCTION: "
            "36/257 [10.3, 18.8] -> 49/257 overlaps the baseline Wilson CI, "
            "so the score is NOT the result; the result is the paired id "
            "list plus the constructed witnesses.  The intervention is a "
            "SEED edit only (ps_row_pass / ps_row_fail read the already-"
            "computed cmp_ok fact) -- zero Rust, zero Python, so the engine "
            "is identical across both arms and the A1.2 three-arm "
            "requirement does not apply (verified: identical sha256)."),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine_provenance": provenance_stamp(),
        "engine_archived_out_of_tree": (
            "~/ozma-engine-archive/_native.abi3.so.<sha256> (prereg A1.1)"),
        "intervention": {
            "what": ("ps_row_pass / ps_row_fail read Attr(r,'cmp_ok') instead "
                     "of Eq(Attr(r,'got'), Attr(r,'expected'))"),
            "files_changed": ["seeds/program_synthesis.json"],
            "rust_changed": False, "python_changed": False,
            "new_termnode_variants": 0,
            "seed_sha256_before": before["seed_sha256"],
            "seed_sha256_after": after["seed_sha256"],
        },
        "arms": {
            "before": {"label": before["label"], "engine": before["engine_provenance"]["short"],
                       "seed_sha256": before["seed_sha256"],
                       "pass_ids": before["pass_ids"], "accepted_ids": before["accepted_ids"],
                       "determinism": before["determinism"]},
            "after": {"label": after["label"], "engine": after["engine_provenance"]["short"],
                      "seed_sha256": after["seed_sha256"],
                      "pass_ids": after["pass_ids"], "accepted_ids": after["accepted_ids"],
                      "determinism": after["determinism"]},
            "same_engine": (before["engine_provenance"]["sha256"]
                            == after["engine_provenance"]["sha256"]),
        },
        "paired_diff": {
            "newly_accepted": new_acc, "lost_accepted": lost_acc,
            "newly_pass": new_pass, "lost_pass": lost_pass,
            "newly_accepted_AND_correct": correct,
            "newly_accepted_but_coincidental_fit": coincidental,
            "newly_accepted_unprobed": unprobed,
            "newly_pass_AND_correct": new_pass_correct,
            "newly_pass_but_coincidental_fit": new_pass_coincidental,
        },
        "aggregate_with_its_caveat": {
            "before": wilson(len(B), 257), "after": wilson(len(A), 257),
            "caveat": ("UNDERPOWERED BY CONSTRUCTION -- report the id list "
                       "and the witnesses, never this number alone."),
        },
        "type_collapse": {
            "mechanism": ("Python list and Python tuple are BOTH Value::Tuple "
                          "in this substrate, verified live: a node attr set "
                          "to [1,2,3] reads back as (1,2,3).  Set and dict are "
                          "NOT collapsed (Value::Set / Value::Dict are "
                          "distinct).  So the ONLY values the collapse can "
                          "equate are two sequences with IDENTICAL elements "
                          "and different container types -- it can never "
                          "equate two different element sequences."),
            "pre_existing": ("the collapse is ALREADY load-bearing on two "
                             "paths this change does not touch: "
                             "mbpp_arc3_battery.agree() normalises list/tuple "
                             "for EVERY held-out row, and _row_cmp_ok already "
                             "backs ps_row_pass_special on tol/unordered "
                             "rows."),
            "newly_accepted_whose_accept_needs_the_collapse": collapse_dep,
            "of_those_failing_the_corpus_own_assert": collapse_false,
            "not_a_choice_of_comparator": (
                "measured live: substrate Eq((1,2),[1,2]) is TRUE (both are "
                "Value::Tuple) while Python (1,2)==[1,2] is FALSE -- but the "
                "row's `expected` attr is READ BACK FROM THE GRAPH, so it is "
                "already a tuple by the time _row_cmp_ok sees it.  The "
                "collapse is therefore a property of the VALUE LAYER, not of "
                "the decision to read cmp_ok: storing the non-scalar `got` "
                "and keeping Eq(got, expected) collapses IDENTICALLY.  Any "
                "non-scalar row verdict in this substrate inherits it."),
            "numeric_coercion_note": (
                "measured live: substrate Eq(1,True), Eq(0,False), Eq(1,1.0) "
                "are ALL TRUE, and Python == agrees, so the comparator swap "
                "adds no numeric/bool looseness.  It does newly EXPOSE it for "
                "non-scalar results -- task 222 is accepted returning "
                "Fraction(len(a), a[-1]) where a BOOL is expected, because "
                "Fraction(1,1) == True."),
        },
        "comparator_semantics_probe": comparator_probe(),
        "string_order_defect_probe": string_order_probe(after),
        "baseline_36_are_all_scalar_output": {
            "expected_types_per_baseline_pass_id": base_types,
            "baseline_pass_ids_with_a_non_scalar_expected": base_nonscalar,
            "reading": ("empty ⇒ the list/tuple collapse was NEVER load-bearing "
                        "at the ACCEPT layer before this change; it becomes "
                        "load-bearing for the first time here."),
        },
        "where_else_got_is_read": {
            "_note": ("read from the seed AS COMMITTED (the candidate was "
                      "reverted after measurement -- NO-GO).  Reproduce the "
                      "measured `after` arm with "
                      "`python scripts/arc6_verdict_patch.py apply`, which "
                      "yields seed sha256 "
                      "ae3dfea8590a6bbf5340ceba70bca8bf5aa78830b5656ca025ec35a7fe115f58."),
            "seed_rules": got_readers,
            "adapter_sites": {
                "domains/prog_synthesis.py:784": (
                    "eval_and_record -- SETS `got`, scalar-only cast.  The "
                    "source of the block.  This candidate does NOT change it: "
                    "`got` keeps its scalar-only meaning and the rules read "
                    "`cmp_ok` instead."),
                "domains/prog_synthesis.py:785": (
                    "`got_json` -- the full result, already recorded, read by "
                    "no rule (diagnostic only)."),
                "domains/prog_synthesis.py:794": (
                    "`cmp_ok` -- the comparison fact this candidate promotes "
                    "to the plain rows.  Computed off the RAW result."),
                "domains/prog_synthesis.py:2001": (
                    "`fu_got` -- the DESCENT FOLD-UP lane's own scalar-only "
                    "cast, read by ps_foldup_accept / ps_foldup_reject with "
                    "the SAME Eq(fu_got, expected) shape.  **A SECOND, "
                    "INDEPENDENT non-scalar blindness that this candidate "
                    "does NOT fix** -- there is no `fu_cmp_ok` fact to read.  "
                    "Any claim that 'the non-scalar verdict is fixed' would "
                    "be false while this stands."),
                "scripts/mbpp_arc3_battery.py:225 agree()": (
                    "the HELD-OUT verdict -- already list/tuple-blind "
                    "(`_norm`), and already the grading path for every "
                    "existing pass.  Unaffected by this candidate, and the "
                    "reason a collapse-dependent accept still reaches "
                    "`pass`."),
                "domains/prog_synthesis.py:2369 (read-back)": (
                    "CounterExample.got is reported out of the goal "
                    "mechanically -- diagnostic, no decision.  Stays None for "
                    "a non-scalar counterexample either way."),
            },
        },
        "constructed_witness_sweeps": sweeps,
        "bars": bar,
        "go_no_go": "GO" if go else "NO-GO",
    }
    with open(OUT, "w") as f:
        json.dump(rec, f, indent=2, sort_keys=True, default=_jdefault)
    print("newly accepted:", new_acc)
    print("newly pass    :", new_pass)
    print("lost pass     :", lost_pass, " lost accepted:", lost_acc)
    print("CORRECT       :", correct)
    print("COINCIDENTAL  :", coincidental)
    print("collapse-dep  :", collapse_dep)
    print("false accepts :", collapse_false)
    print("baseline non-scalar expected ids:", base_nonscalar)
    for k, v in bar.items():
        print(v["verdict"], k)
    print("GO/NO-GO:", rec["go_no_go"])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
