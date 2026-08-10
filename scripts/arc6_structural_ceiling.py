"""arc6_structural_ceiling — the STRUCTURAL ceiling for arc 6's residual.

MEASUREMENT ONLY.  Nothing is built.  No file under `seeds/`, `runners/`,
`domains/` or any adapter is modified.  No `git add`/`commit`/`stash`.
This script writes exactly one artefact,
`results/arc6_structural_ceiling.json`, plus its own stdout.

WHAT THIS MEASURES, AND WHY IT IS A NEW SEAM
--------------------------------------------
`PROGRAM_SYNTHESIS_ARC6_A_CEILING.md` established that of the 53
live-unreached MBPP tasks, **no import fixes 42 of them (79%)**.  The
blockers there are not mathematical; they are structural primitives.  Two
independent inversions pointed the same way: `sympy.ntheory` strictly
unlocks ZERO because its hits compute the maths exactly and then die on a
structural primitive, and the family that tops the strict list wins only
by supplying `multiset`/`ordered`/`subsets` -- a frequency counter, a sort
and a combination generator, i.e. structural primitives dressed as a
mathematics import.

So the arc's premise (the pipeline is blocked on mathematics it already
owns) is at least partly wrong for this corpus.  **The residual is blocked
on structure.**  This script characterises those 42 precisely enough to
decide whether a structural seam is worth building.

THE INSTRUMENT
--------------
Every claim is made by LIVE INVOCATION, in both directions:

  * a primitive is present  <=> a Term-JSON built from it evaluates to the
    right value on a concrete input (never "the name is in the source");
  * a primitive is absent   <=> the engine refuses it by name, or accepts
    it and returns the WRONG value (the dangerous case -- three of this
    script's findings are of exactly that kind);
  * a task's requirement set is verified by a HAND-CONSTRUCTED Term
    witness evaluated on that task's own REVEALED rows.  A witness that
    reproduces every revealed row proves the current primitive inventory
    SUFFICES and the blocker is the enumerator's op table / template pool
    / budget -- not a missing primitive.

Held-out rows never enter any detection or selection path: every witness
is scored on `split_rows(rows, "primary")["revealed"]` only, and the
held-out row is not read at all (mechanically audited, see
`_held_out_isolation_audit`).

ENGINE PROVENANCE IS PART OF THE MEASUREMENT'S IDENTITY
-------------------------------------------------------
`site-packages/substrate_rs.pth` is an ABSOLUTE path into the CANONICAL
tree and `_native.abi3.so` is gitignored, so a bare script in a worktree
silently imports a DIFFERENT binary than the one it believes it is
measuring.  That is live here, not hypothetical: at the time of writing
this tree's engine is 5c1b472fe674 and the canonical tree's is
7dd9af13a038 -- two different binaries.  `engine_preamble()` is therefore
called BEFORE any import of `substrate_rs`, and the engine sha256 is
recorded in the artefact next to the numbers.

CONTAMINATION DISCIPLINE
------------------------
MBPP test-split `code` is read for MEASUREMENT classification only.  No
prompt text and no reference code enters any codebook, cue vocabulary or
taught shape.  Every claim below is a paired id list, never a count alone.

Run:
    OZMA_NO_LLM=1 python scripts/arc6_structural_ceiling.py
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import inspect
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# MUST precede `import substrate_rs` -- see the module docstring.
from domains.engine_provenance import (  # noqa: E402
    engine_preamble, provenance_stamp, provenance_line,
)

engine_preamble(strict=False)

import substrate_rs as srs  # noqa: E402

from domains.mbpp_spec import parse_asserts, split_rows  # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
A_CEILING = os.path.join(ROOT, "results", "arc6_a_ceiling.json")
BACKWARD_PROBE = os.path.join(ROOT, "results", "arc4_backward_probe.json")
OUT = os.path.join(ROOT, "results", "arc6_structural_ceiling.json")

# `PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md` sec 3's three "moved" tables --
# the same derivation the A-ceiling used, reproduced here so the
# population is DERIVED and cross-checked rather than inherited on trust.
S4_MOVED = {
    "pass": [69, 90, 132, 145, 278, 410, 443, 472],
    "accepted_holdout_fail": [19, 65, 66, 70, 95, 116, 166, 253, 270, 294,
                              400, 438, 446],
    "moved_to_different_gap": [272, 413, 418, 460],
}

# ---------------------------------------------------------------------------
# Term-JSON helpers.  Field names were read from `runners/dsl/src/jsonio.rs`
# and every one is exercised live below -- a wrong field name raises
# `MissingField`, so the probes cannot silently degrade into no-ops.
# ---------------------------------------------------------------------------

def L(v):
    return {"type": "Lit", "value": v}


def V(n):
    return {"type": "Var", "name": n}


def FL(src, var, pred):
    return {"type": "FilterList", "source": src, "var_name": var, "predicate": pred}


def ML(src, var, val):
    return {"type": "MapList", "source": src, "var_name": var, "value": val}


_SUB = srs.Substrate()


def ev(term, env=None):
    """Evaluate a Term-JSON.  Returns (status, value_or_error_string)."""
    try:
        return "ok", _SUB._inner.evaluate(term, env or {})
    except Exception as exc:  # noqa: BLE001 -- the error text IS the evidence
        return "refused", "%s: %s" % (type(exc).__name__, exc)


def norm(x):
    """Fold list/tuple to a comparable shape.  The engine realises BOTH a
    Python list and a Python tuple as `Value::Tuple` (measured -- see the
    `lit_list`/`lit_tuple` probes), so a comparison that distinguished them
    would refute correct terms for a reason the value model does not have."""
    if isinstance(x, (list, tuple)):
        return tuple(norm(i) for i in x)
    return x


# ---------------------------------------------------------------------------
# 1.  PRIMITIVE PROBES -- live, both directions.
#
# Each probe is (id, claim, term, expected, kind).  `kind` is one of:
#   present  -- the claim is that the primitive EXISTS and is correct
#   absent   -- the claim is that the engine refuses it by name
#   wrong    -- the claim is that the engine ACCEPTS it and is WRONG
#               (the dangerous kind: reading the name would confirm it)
# The verdict is computed from the live result, never asserted.
# ---------------------------------------------------------------------------

_ORACLES = {k: True for k in (
    "len abs min max range sum str int float bool sorted round pow divmod ord "
    "chr list tuple set frozenset dict all any isinstance enumerate zip "
    "reversed upper lower capitalize strip lstrip rstrip split join replace "
    "startswith endswith find count isdigit isalpha items keys values get"
).split()}


def CE(name, args, recv=None):
    t = {"type": "ProgCallExtern", "name": name, "args": args}
    if recv is not None:
        t["recv"] = recv
    return t


def PROG(expr, oracles=None):
    return {"type": "ProgEval",
            "prog": {"type": "ProgReturn", "value": expr},
            "env": L({}),
            "oracles": L(oracles if oracles is not None else _ORACLES)}


def _prog_result(value):
    """ProgEval returns a record; the probe compares its `result` field."""
    if isinstance(value, dict) and "result" in value:
        return value["result"] if value.get("trap") is None else "TRAP:" + str(value["trap"])
    return value


PROBES = [
    # ---- the Value / JSON boundary -------------------------------------
    ("lit_tuple", "a Python tuple crosses the Lit boundary",
     L((1, 2, 3)), (1, 2, 3), "present"),
    ("lit_list", "a Python list crosses the Lit boundary AS A TUPLE "
     "(list and tuple are the SAME value in this domain)",
     L([1, 2, 3]), (1, 2, 3), "present"),
    ("lit_dict", "a Python dict crosses the Lit boundary",
     L({"a": 1, "b": 2}), {"a": 1, "b": 2}, "present"),
    ("lit_list_of_tuples", "nested tuples cross the Lit boundary",
     L([(1, 2), (3, 4)]), ((1, 2), (3, 4)), "present"),
    ("lit_set", "a Python set CANNOT cross the Lit boundary "
     "(S4 sec 4.3's task-115 breakage, reproduced)",
     L({1, 2, 3}), None, "absent"),
    ("lit_frozenset", "a Python frozenset CANNOT cross the Lit boundary",
     L(frozenset({1, 2})), None, "absent"),
    ("lit_float", "a float crosses the Lit boundary",
     L(-16.22), -16.22, "present"),

    # ---- sequence construction -----------------------------------------
    ("term_Vec", "Vec constructs a tuple (n-ary sequence construction)",
     {"type": "Vec", "items": [L(2), L(1)]}, (2, 1), "present"),
    ("term_Vec_nested", "Vec nests",
     {"type": "Vec", "items": [L("a"), {"type": "Vec", "items": [L(1), L(2)]}]},
     ("a", (1, 2)), "present"),
    ("term_Append", "Append extends a sequence by one item",
     {"type": "Append", "seq": L([1, 2]), "item": L(3)}, (1, 2, 3), "present"),
    ("term_Fold_Append", "Fold+Append IS list concatenation "
     "(no dedicated Term needed -- the JoinList precedent)",
     {"type": "Fold", "source": L([3, 4]), "var_name": "i", "acc_name": "acc",
      "init": L([1, 2]), "body": {"type": "Append", "seq": V("acc"), "item": V("i")}},
     (1, 2, 3, 4), "present"),
    ("term_Cat_on_lists", "Cat is STRING concatenation and produces Rust "
     "debug reprs on lists -- the name says list-concat, the value refutes it",
     {"type": "Cat", "items": [L([1, 2]), L([3])]}, (1, 2, 3), "wrong"),

    # ---- reduction ------------------------------------------------------
    ("term_Prod", "Prod folds a product over a source",
     {"type": "Prod", "source": L([2, 3, 4]), "var_name": "i", "value": V("i")},
     24, "present"),
    ("term_Argmax_bylen", "Argmax returns the ELEMENT maximising a value "
     "expression (the arg-twin of MaxLenOver)",
     {"type": "Argmax", "source": L([[1], [1, 2, 3], [1, 2]]), "var_name": "x",
      "value": {"type": "Count", "source": V("x")}}, (1, 2, 3), "present"),

    # ---- membership -----------------------------------------------------
    ("term_In_list", "In tests membership in a list",
     {"type": "In", "member": L(2), "container": L([1, 2, 3])}, True, "present"),
    ("term_In_list_neg", "In is correct in the negative direction too",
     {"type": "In", "member": L(9), "container": L([1, 2, 3])}, False, "present"),
    ("term_FilterList_notIn", "a cross-list NOT-IN predicate is expressible "
     "as a Term today (only the enumerator's TEMPLATE POOL lacks it)",
     FL(L([1, 2, 3]), "x", {"type": "Not", "arg": {
         "type": "In", "member": V("x"), "container": L([2])}}), (1, 3), "present"),

    # ---- STRING AS A SEQUENCE -- four refutations, all in the same place
    ("term_Count_str", "Count (the enumerator's `Len` op) returns 0 for a "
     "STRING -- a string has no length in this value domain",
     {"type": "Count", "source": L("abc")}, 3, "wrong"),
    ("term_IndexAt_str", "IndexAt returns None on a STRING",
     {"type": "IndexAt", "seq": L("abc"), "index": L(1)}, "b", "wrong"),
    ("term_Last_str", "Last returns None on a STRING",
     {"type": "Last", "seq": L("abc")}, "c", "wrong"),
    ("term_In_str", "In returns False for a character in a STRING",
     {"type": "In", "member": L("a"), "container": L("cat")}, True, "wrong"),
    ("term_IndexAt_list", "IndexAt is correct on a LIST (so the defect is "
     "the STRING case specifically, not the Term)",
     {"type": "IndexAt", "seq": L([10, 20, 30]), "index": L(1)}, 20, "present"),
    ("term_IndexAt_neg", "IndexAt supports a negative index on a LIST",
     {"type": "IndexAt", "seq": L([10, 20, 30]), "index": L(-1)}, 30, "present"),

    # ---- string ops -----------------------------------------------------
    ("term_StringSlice", "StringSlice slices a string by [start,end)",
     {"type": "StringSlice", "s": L("hello"), "start": L(1), "end": L(3)},
     "el", "present"),
    ("term_StringSlice_neg", "StringSlice does NOT support a negative end",
     {"type": "StringSlice", "s": L("hello"), "start": L(0), "end": L(-1)},
     "hell", "wrong"),
    ("term_StringIndexOf", "StringIndexOf gives the FIRST index, never a count",
     {"type": "StringIndexOf", "haystack": L("hello"), "needle": L("l")},
     2, "present"),
    ("term_Tokenize", "Tokenize returns (offset,len) SPANS, not substrings -- "
     "so it is not a `split`",
     {"type": "Tokenize", "text": L("a b c")}, ("a", "b", "c"), "wrong"),
    ("term_Join_str", "Join joins STRINGS with a separator",
     {"type": "Join", "separator": L("-"), "items": L(["a", "b"])},
     "a-b", "present"),
    ("term_Join_ints", "Join emits Rust debug reprs for non-string elements "
     "-- there is no value->string coercion in the Term layer",
     {"type": "Join", "separator": L("-"), "items": L([1, 2])}, "1-2", "wrong"),
    ("term_CaseFold", "CaseFold lowercases (there is no upper/capitalize twin)",
     {"type": "CaseFold", "text": L("ABC")}, "abc", "present"),

    # ---- dict -----------------------------------------------------------
    ("term_MkDict", "MkDict builds a dict from ALTERNATING key,value items",
     {"type": "MkDict", "items": [L("a"), L(1), L("b"), L(2)]},
     {"a": 1, "b": 2}, "present"),
    ("term_DictGet", "DictGet reads one key",
     {"type": "DictGet", "dict": L({"a": 1}), "key": L("a")}, 1, "present"),
    ("term_Sum_over_dict", "a reduction over a Dict yields NOTHING -- there is "
     "no items/keys/values iteration",
     {"type": "Sum", "source": L({"a": 1, "b": 2}), "var_name": "k",
      "value": V("k")}, 3, "wrong"),
    ("term_Union_on_dicts", "Union on two dicts returns an EMPTY FROZENSET -- "
     "there is no dict merge",
     {"type": "Union", "a": L({"a": 1}), "b": L({"b": 2})},
     {"a": 1, "b": 2}, "wrong"),

    # ---- named-absent Terms (refused by the engine, by name) ------------
    ("absent_Sort", "no Sort Term", {"type": "Sort", "source": L([3, 1, 2])}, None, "absent"),
    ("absent_Sorted", "no Sorted Term", {"type": "Sorted", "source": L([3, 1, 2])}, None, "absent"),
    ("absent_SortBy", "no SortBy Term",
     {"type": "SortBy", "source": L([3, 1, 2]), "var_name": "x", "value": V("x")}, None, "absent"),
    ("absent_Reverse", "no Reverse Term", {"type": "Reverse", "seq": L([1, 2, 3])}, None, "absent"),
    ("absent_Reversed", "no Reversed Term", {"type": "Reversed", "seq": L([1, 2, 3])}, None, "absent"),
    ("absent_Replace", "no Replace Term",
     {"type": "Replace", "text": L("abc"), "old": L("a"), "new": L("z")}, None, "absent"),
    ("absent_Split", "no Split Term",
     {"type": "Split", "text": L("a b"), "sep": L(" ")}, None, "absent"),
    ("absent_Slice", "no general sequence Slice Term",
     {"type": "Slice", "seq": L([1, 2, 3]), "start": L(0), "end": L(2)}, None, "absent"),
    ("absent_ListSlice", "no ListSlice Term",
     {"type": "ListSlice", "seq": L([1, 2, 3]), "start": L(0), "end": L(2)}, None, "absent"),
    ("absent_Round", "no Round Term", {"type": "Round", "value": L(2.6)}, None, "absent"),
    ("absent_Enumerate", "no Enumerate Term (no (index,element) binder)",
     {"type": "Enumerate", "source": L([1, 2])}, None, "absent"),
    ("absent_ToStr", "no value->string coercion Term",
     {"type": "ToStr", "value": L(3)}, None, "absent"),
    ("absent_Chars", "no string->characters Term",
     {"type": "Chars", "text": L("abc")}, None, "absent"),
    ("absent_Items", "no dict-items Term", {"type": "Items", "dict": L({"a": 1})}, None, "absent"),
    ("absent_Keys", "no dict-keys Term", {"type": "Keys", "dict": L({"a": 1})}, None, "absent"),
    ("absent_Values", "no dict-values Term", {"type": "Values", "dict": L({"a": 1})}, None, "absent"),

    # ---- the ProgEval layer: is class (c) actually empty? ---------------
    ("prog_sorted_ints", "ProgEval HAS sorted, and it is correct on ints",
     PROG(CE("sorted", [L([15, 79, 25, 38, 69])])), (15, 25, 38, 69, 79), "present"),
    ("prog_sorted_strs", "ProgEval's sorted is WRONG on STRINGS -- it orders by "
     "INTERNER SYMBOL ID, i.e. by the order strings were first seen in the "
     "PROCESS (see the `str_order_is_process_dependent` experiment)",
     PROG(CE("sorted", [L(["pear", "apple", "fig"])])),
     ("apple", "fig", "pear"), "wrong"),
    ("prog_sorted_tuples", "ProgEval's sorted is correct on tuples of ints",
     PROG(CE("sorted", [L([(3, 4), (1, 2), (2, 9)])])),
     ((1, 2), (2, 9), (3, 4)), "present"),
    ("prog_len_str", "ProgEval HAS len on a string (unlike the Term layer)",
     PROG(CE("len", [L("hello")])), 5, "present"),
    ("prog_split", "ProgEval HAS str.split", PROG(CE("split", [L("_")], recv=L("a_b_c"))),
     ("a", "b", "c"), "present"),
    ("prog_replace", "ProgEval HAS str.replace",
     PROG(CE("replace", [L("a"), L("z")], recv=L("abca"))), "zbcz", "present"),
    ("prog_join", "ProgEval HAS str.join", PROG(CE("join", [L(["a", "b"])], recv=L("-"))),
     "a-b", "present"),
    ("prog_capitalize", "ProgEval HAS str.capitalize",
     PROG(CE("capitalize", [], recv=L("abc"))), "Abc", "present"),
    ("prog_count_substr", "ProgEval HAS str.count",
     PROG(CE("count", [L("std")], recv=L("letstdlenstdporstd"))), 3, "present"),
    ("prog_enumerate", "ProgEval HAS enumerate",
     PROG(CE("list", [CE("enumerate", [L(["a", "b"])])])), ((0, "a"), (1, "b")), "present"),
    ("prog_reversed", "ProgEval HAS reversed",
     PROG(CE("list", [CE("reversed", [L([1, 2, 3])])])), (3, 2, 1), "present"),
    ("prog_round", "ProgEval HAS round", PROG(CE("round", [L(2.6)])), 3, "present"),
    ("prog_str", "ProgEval HAS str()", PROG(CE("str", [L(3)])), "3", "present"),
    ("prog_int", "ProgEval HAS int()", PROG(CE("int", [L("42")])), 42, "present"),
    ("prog_slice_step", "ProgEval HAS strided slicing",
     PROG({"type": "ProgSlice", "obj": L([1, 2, 3, 4, 5, 6]), "start": L(0),
           "step": L(2)}), (1, 3, 5), "present"),
    ("prog_slice_str_reverse", "ProgEval HAS negative-step slicing (string reverse)",
     PROG({"type": "ProgSlice", "obj": L("abc"), "step": L(-1)}), "cba", "present"),
    ("prog_subscript_str", "ProgEval HAS string subscripting",
     PROG({"type": "ProgSubscript", "obj": L("abc"), "index": L(1)}), "b", "present"),
    ("prog_set_out", "a SET can come OUT of ProgEval even though it cannot go IN "
     "through Lit -- the boundary is asymmetric",
     PROG(CE("set", [L([1, 2, 2])])), {1, 2}, "present"),
    ("prog_dict_out", "a dict can come out of ProgEval",
     PROG({"type": "ProgContainerLit", "kind": "dict", "items": [L("a"), L(1)]}),
     {"a": 1}, "present"),
    ("prog_comprehension_notin", "ProgEval HAS a list comprehension with a "
     "`not in` guard -- the whole of task 161's reference, at the Prog layer",
     PROG({"type": "ProgComprehensionList", "var": "x", "source": L([1, 2, 3]),
           "expr": V("x"), "cond": {"type": "Not", "arg": {
               "type": "In", "member": V("x"), "container": L([2])}}}),
     (1, 3), "present"),
    ("prog_sorted_dict_items", "ProgEval HAS dict.items() and can sort it",
     PROG(CE("sorted", [CE("items", [], recv=L({"a": 2, "b": 1}))])),
     (("a", 2), ("b", 1)), "present"),
    ("prog_format_absent", "ProgEval does NOT have str.format",
     PROG(CE("format", [L(1)], recv=L("temp{0}")), dict(_ORACLES, format=True)),
     "temp1", "wrong"),
    ("prog_counter_absent", "ProgEval does NOT have collections.Counter",
     PROG(CE("Counter", [L([1, 1, 2])]), dict(_ORACLES, Counter=True)),
     {1: 2, 2: 1}, "wrong"),
    ("prog_combinations_absent", "ProgEval does NOT have itertools.combinations",
     PROG(CE("combinations", [L([1, 2]), L(1)]), dict(_ORACLES, combinations=True)),
     ((1,), (2,)), "wrong"),
]


def run_probes():
    out = []
    for pid, claim, term, expected, kind in PROBES:
        status, value = ev(term)
        got = _prog_result(value) if status == "ok" else value
        if kind == "absent":
            verdict = "CONFIRMED_ABSENT" if status == "refused" else "UNEXPECTEDLY_PRESENT"
        else:
            matches = (status == "ok" and norm(got) == norm(expected))
            if kind == "present":
                verdict = "CONFIRMED_PRESENT" if matches else "REFUTED"
            else:  # kind == "wrong"
                verdict = "CONFIRMED_WRONG" if not matches else "UNEXPECTEDLY_CORRECT"
        out.append({"probe": pid, "claim": claim, "kind": kind,
                    "status": status, "got": repr(got)[:220],
                    "expected_if_correct": repr(expected)[:160],
                    "verdict": verdict})
    return out


def str_order_experiment():
    """PROOF that string ordering is process-history dependent, not merely
    non-lexicographic.  Two FRESH substrates; the second has its interner
    primed with two extra strings first.  If the sorted output differs, the
    order is a function of interning history -- which makes every
    string-keyed `Set`/`Dict` canonical order, and every `sorted` over
    strings, dependent on what the process happened to see earlier."""
    prog = PROG(CE("sorted", [L(["pear", "apple", "fig"])]))
    a = srs.Substrate()
    r_a = _prog_result(a._inner.evaluate(prog, {}))
    b = srs.Substrate()
    b._inner.evaluate(L("zzz"), {})
    b._inner.evaluate(L("apple"), {})
    r_b = _prog_result(b._inner.evaluate(prog, {}))
    return {"fresh_substrate": list(r_a),
            "after_priming_interner_with_zzz_then_apple": list(r_b),
            "python_sorted": sorted(["pear", "apple", "fig"]),
            "process_history_dependent": list(r_a) != list(r_b),
            "root_cause": "runners/dsl/src/value.rs::cmp_value -- "
                          "(Value::Str(x), Value::Str(y)) => x.0.cmp(&y.0), "
                          "i.e. interner Sym id, not the resolved text",
            "blast_radius": [
                "sorted / min / max / Argmax / MaxOver over strings",
                "Value::Set / FrozenSet canonical storage order (value.rs "
                "documents these as 'sorted ... deterministic regardless of "
                "construction order' -- true only within one process history)",
                "Value::Dict key order (documented as 'sorted by key')",
                "Gt/Lt/Gte/Lte between two strings",
            ]}


def unknown_op_experiment():
    """Is the enumerator's op table the SOLE gate, and are additions purely
    additive?  An unknown op name must be a silent no-op (not a trap), and a
    known one must convert -- exactly the arc-4 S4 precondition."""
    rows = [{"inputs": {"a": i, "b": j}, "output": i + j}
            for i, j in [(1, 2), (3, 4), (5, 6)]]
    res = {}
    for ops in (["Bogus"], ["Plus"], ["Bogus", "Plus"]):
        term = {"type": "SynthEnumerate", "examples": L(rows), "ops": L(ops),
                "consts": None, "exclude": None, "max_size": 5,
                "max_candidates": 5000, "saturate_k": 0, "field": ""}
        r = _SUB._inner.evaluate(term, {})
        res["+".join(ops)] = {"found": r["found"], "term_str": r["term_str"],
                              "halt_reason": r["halt_reason"]}
    res["_reading"] = ("an unknown op name neither traps nor changes the "
                       "result; the op table is the sole gate and every "
                       "addition is purely additive (the arc-4 S4 shape)")
    return res


# ---------------------------------------------------------------------------
# 2.  THE OPERATOR INVENTORY -- the units a ceiling is counted in.
#
# Each unit carries `blind`: would a person add this to a program
# synthesiser WITHOUT having seen the test split?  This is the structural
# twin of the A-ceiling's `registered_blind` test, and it is the ONLY thing
# separating an honest ceiling from a cherry-picked one.
# ---------------------------------------------------------------------------

UNITS = {
    # ---- tier 0: ZERO new TermNode (the exact arc-4 S4 shape) ----------
    "op:TupleOf": {
        "what": "expose the EXISTING `Vec` Term as a SynthEnumerate op "
                "(n-ary tuple construction)",
        "cost_class": "a_enum_op", "new_termnode": 0, "blind": "YES",
        "evidence": ["term_Vec", "term_Vec_nested"],
    },
    "op:ProdList": {
        "what": "expose the EXISTING `Prod` Term as a ListUnary op "
                "(the `SumList` twin)",
        "cost_class": "a_enum_op", "new_termnode": 0, "blind": "YES",
        "evidence": ["term_Prod"],
    },
    "op:ConcatList": {
        "what": "a list-concatenation op built as Fold+Append over existing "
                "Terms (exactly how `JoinList` was built in arc-4 S4)",
        "cost_class": "a_enum_op", "new_termnode": 0, "blind": "YES",
        "evidence": ["term_Fold_Append", "term_Append", "term_Cat_on_lists"],
    },
    "op:ArgMaxLenOver": {
        "what": "expose the EXISTING `Argmax` Term with a `Count(item)` value "
                "(the arg-twin of the already-shipped `MaxLenOver`)",
        "cost_class": "a_enum_op", "new_termnode": 0, "blind": "WEAK -- "
                "general as 'argmax by a projection', but the specific "
                "by-length variant is one step from bespoke",
        "evidence": ["term_Argmax_bylen"],
    },
    "tmpl:item_in_listvar": {
        "what": "filter-template extension: `item (not) in <list spec var>`, "
                "over the EXISTING `In` Term",
        "cost_class": "a_template", "new_termnode": 0, "blind": "YES",
        "evidence": ["term_In_list", "term_In_list_neg", "term_FilterList_notIn"],
    },
    "tmpl:len_item_vs_var": {
        "what": "filter-template extension: compare `len(item)` to a scalar "
                "VARIABLE, not only to a constant",
        "cost_class": "a_template", "new_termnode": 0, "blind": "YES",
        "evidence": [],
    },
    "tmpl:nested_reduction": {
        "what": "allow a REDUCTION over the bound item inside a filter "
                "predicate (an all/any quantifier over a sublist)",
        "cost_class": "a_template", "new_termnode": 0, "blind": "YES -- but "
                "it widens the template grammar from bounded to recursive, "
                "which S4 sec 4.4 named as an architectural seam",
        "evidence": [],
    },
    "fix:StringAsSequence": {
        "what": "make the EXISTING Count/IndexAt/Last/In accept a string "
                "(a string currently has no length, no index and no members)",
        "cost_class": "a_enum_op", "new_termnode": 0, "blind": "YES",
        "evidence": ["term_Count_str", "term_IndexAt_str", "term_Last_str",
                     "term_In_str", "term_IndexAt_list"],
        "risk": "SEMANTIC CHANGE to shipped Terms, not an addition: "
                "`Count(str)` returns 0 today and any caller relying on that "
                "changes behaviour.  This is the one tier-0 unit that is not "
                "purely additive.",
    },

    # ---- tier 1: new TermNode, stdlib-universal ------------------------
    "term:Slice": {
        "what": "a general sequence slice (start/stop/step, negatives)",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["absent_Slice", "absent_ListSlice", "term_StringSlice",
                     "term_StringSlice_neg", "prog_slice_step"],
    },
    "term:Replace": {
        "what": "string replace",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["absent_Replace", "prog_replace"],
    },
    "term:Split": {
        "what": "split a string on a delimiter into SUBSTRINGS "
                "(`Tokenize` returns spans, not substrings)",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["absent_Split", "term_Tokenize", "prog_split"],
    },
    "term:Capitalize": {
        "what": "upper/capitalize (only `CaseFold`/lower exists)",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["term_CaseFold", "prog_capitalize"],
    },
    "term:Str": {
        "what": "value -> string coercion",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["absent_ToStr", "term_Join_ints", "prog_str"],
    },
    "term:ParseInt": {
        "what": "string -> int coercion",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["prog_int"],
    },
    "term:Round": {
        "what": "round a number",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["absent_Round", "prog_round"],
    },
    "term:Reverse": {
        "what": "reverse a sequence or string",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["absent_Reverse", "absent_Reversed", "prog_slice_str_reverse"],
    },
    "term:IndexedMap": {
        "what": "bind (index, element) together in a map/filter body -- the "
                "enumerate() binder S4 sec 4.5 named as a genuine new-Term "
                "decision",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["absent_Enumerate", "prog_enumerate"],
    },
    "term:StrCount": {
        "what": "count occurrences of a substring "
                "(`StringIndexOf` gives the FIRST index only)",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["term_StringIndexOf", "prog_count_substr"],
    },

    # ---- tier 2: ordering, and the boundary ---------------------------
    "term:Sort": {
        "what": "a sorting Term (plain and by a projection)",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["absent_Sort", "absent_Sorted", "absent_SortBy",
                     "prog_sorted_ints"],
    },
    "fix:StrOrder": {
        "what": "make `cmp_value` order two strings by TEXT, not by interner "
                "symbol id -- a MANDATORY prerequisite of any sort, because "
                "shipping a knowingly wrong string order is not an option",
        "cost_class": "c_engine_semantics", "new_termnode": 0, "blind": "YES",
        "evidence": ["prog_sorted_strs"],
        "risk": "CROSS-CUTTING.  Changes the canonical storage order of every "
                "Value::Set/FrozenSet and every Value::Dict with string keys, "
                "engine-wide -- i.e. it can move any frozen fixture whose "
                "artefact contains a string-keyed set or dict.",
    },
    "boundary:SetLit": {
        "what": "let a Python set/frozenset cross the `{\"type\":\"Lit\"}` "
                "boundary (S4 sec 4.3's flagged task-115 breakage)",
        "cost_class": "b_boundary", "new_termnode": 0, "blind": "YES",
        "evidence": ["lit_set", "lit_frozenset", "prog_set_out"],
    },

    # ---- tier 3: dict ---------------------------------------------------
    "term:DictItems": {
        "what": "iterate a Dict as (key,value) pairs, and let the "
                "enumerator's list-typed index accept a Dict "
                "(`is_listlike` excludes Dict by construction)",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["absent_Items", "absent_Keys", "absent_Values",
                     "term_Sum_over_dict", "prog_sorted_dict_items"],
    },
    "term:DictMerge": {
        "what": "merge two dicts",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["term_Union_on_dicts", "term_MkDict"],
    },
    "term:GroupCount": {
        "what": "a frequency map (Counter) over a sequence",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "YES",
        "evidence": ["prog_counter_absent", "term_MkDict"],
    },

    # ---- tier 4: genuinely expensive -----------------------------------
    "term:Recurse": {
        "what": "an unbounded iteration / recursion / unfold binder "
                "(`Fold` only folds an EXISTING source; there is no `range`, "
                "no self-reference and no fixpoint)",
        "cost_class": "a_new_capability", "new_termnode": 1, "blind": "YES -- "
                "but this is a capability decision, not an operator: it "
                "changes what the search space IS",
        "evidence": ["term_Fold_Append"],
    },
    "term:Combinations": {
        "what": "combinatorial generators (combinations, "
                "combinations_with_replacement, powerset)",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "WEAK -- "
                "this is the structural twin of the A-ceiling's F4 finding: "
                "`sympy.utilities.iterables.subsets` supplies exactly this, "
                "and refuted 0/3 on task 462 because the ORDER was wrong",
        "evidence": ["prog_combinations_absent"],
    },
    "term:Format": {
        "what": "str.format",
        "cost_class": "a_new_termnode", "new_termnode": 1, "blind": "WEAK -- "
                "one MBPP task uses it; nothing else in the corpus does",
        "evidence": ["prog_format_absent"],
    },
    "search:max_size": {
        "what": "raise `max_size` above 9 (or widen the template grammar) so "
                "a composition that uses ONLY existing ops can be reached",
        "cost_class": "d_search", "new_termnode": 0, "blind": "YES",
        "evidence": [],
    },
}


# ---------------------------------------------------------------------------
# 3.  THE TAXONOMY -- per task, the FULL set of units it requires.
#
# A task is unlocked by a bundle iff EVERY unit it requires is in that
# bundle.  Multi-membership is deliberate and is the honest shape: the 42
# do not partition, they overlap, and a partition would overstate every
# single-unit yield.
# ---------------------------------------------------------------------------

REQUIREMENTS = {
    11:  (["fix:StringAsSequence", "term:Slice", "term:IndexedMap"],
          "delete the FIRST and the LAST occurrence of a char: needs a char "
          "index, a slice, and index-aware iteration"),
    18:  (["fix:StringAsSequence"],
          "keep chars of s1 not present in s2: iterate a string's chars and "
          "test membership in another string; JoinList already rebuilds it"),
    75:  (["tmpl:nested_reduction"],
          "keep sublists whose EVERY element is divisible by K: a quantifier "
          "over the bound item, inside a filter predicate"),
    87:  (["term:DictMerge"], "merge three dicts, first-wins"),
    88:  (["term:GroupCount"], "frequency map of a list, as a dict"),
    98:  (["op:ProdList"], "product of a list divided by its length"),
    99:  (["term:Recurse", "term:Str"],
          "decimal -> binary string: repeated divmod, then digits to text"),
    102: (["term:Split", "term:Capitalize"], "snake_case -> CamelCase"),
    106: (["op:ConcatList"], "tuple ++ list"),
    118: (["term:Split"], "split a string on the space character"),
    141: (["term:Sort", "fix:StrOrder"], "sort a list"),
    161: (["tmpl:item_in_listvar"], "drop elements of list1 present in list2"),
    170: (["term:Slice"], "sum of a[m:n+1]"),
    172: (["term:StrCount"], "count occurrences of the substring 'std'"),
    226: (["term:IndexedMap", "fix:StringAsSequence"],
          "keep characters at EVEN index"),
    230: (["term:Replace"], "replace blanks with a character"),
    232: (["term:Sort", "fix:StrOrder", "term:Slice", "boundary:SetLit"],
          "n largest items; the assert compares SETS so the row cannot even "
          "be expressed today"),
    255: (["term:Combinations", "op:TupleOf"],
          "combinations WITH REPLACEMENT, as a list of tuples"),
    257: (["op:TupleOf"], "return (b, a)"),
    260: (["term:Recurse"], "Newman-Shanks-Williams linear recurrence to n"),
    262: (["op:TupleOf", "term:Slice"], "split a list at L, return both halves"),
    264: (["search:max_size"],
          "piecewise dog-age: EVERY op already exists; the composition is "
          "size 14 against max_size=9"),
    265: (["term:Slice", "term:Recurse"],
          "strided split: needs a stride slice AND a range over 0..step"),
    283: (["term:Recurse", "term:GroupCount"],
          "digit frequency of an integer, compared against the digit"),
    290: (["op:TupleOf", "op:ArgMaxLenOver"],
          "(max length, the longest sublist) as a pair"),
    301: (["term:DictItems", "term:Recurse"], "depth of a nested dict"),
    310: (["fix:StringAsSequence", "op:TupleOf"], "string -> tuple of characters"),
    390: (["term:Format"], "apply a format string to every element"),
    411: (["term:Split", "term:Capitalize"], "snake_case -> CamelCase (twin of 102)"),
    419: (["term:Round"], "round every element, sum, multiply by length"),
    421: (["term:Str"],
          "join a tuple with a delimiter; `Join` exists and only the "
          "value->string coercion is missing"),
    424: (["fix:StringAsSequence"], "last character of each string in a tuple"),
    437: (["term:IndexedMap", "fix:StringAsSequence"],
          "keep characters at ODD 1-based index"),
    439: (["term:Str", "term:ParseInt"],
          "concatenate the decimal digits of a list of ints into one int"),
    448: (["term:Recurse"], "sum of Perrin numbers to n"),
    450: (["fix:StringAsSequence", "tmpl:len_item_vs_var"],
          "keep strings whose length equals n"),
    456: (["term:Reverse"], "reverse every string in a list"),
    462: (["term:Recurse", "op:ConcatList", "op:TupleOf"],
          "powerset in binary-reflected order"),
    473: (["term:Sort", "fix:StrOrder", "op:TupleOf", "boundary:SetLit"],
          "order-insensitive tuple intersection; the assert compares SETS"),
    474: (["term:Replace"], "replace a character"),
    475: (["term:DictItems", "term:Sort", "fix:StrOrder", "op:TupleOf"],
          "sort a dict by value, as a list of pairs"),
    479: (["term:Str", "fix:StringAsSequence"], "leading digit of a number"),
}


# ---------------------------------------------------------------------------
# 4.  WITNESSES -- hand-built Term trees, evaluated on REVEALED rows only.
#
# A WITNESS proves the current primitive inventory SUFFICES for that task.
# A REFUTATION proves the opposite for the term that LOOKS like the answer,
# and is the more valuable of the two: three of these refute a claim that
# reading the Term's name would have confirmed.
# ---------------------------------------------------------------------------

WITNESSES = {
    75: (FL(V("a"), "s", {"type": "Eq", "a": {
            "type": "MaxOver", "source": V("s"), "var_name": "e",
            "value": {"type": "Mod", "a": V("e"), "b": V("b")}}, "b": L(0)}),
         "expected WITNESS -- every Term exists; the blocker is that the "
         "filter TEMPLATE POOL cannot nest a reduction"),
    98: ({"type": "Div",
          "a": {"type": "Prod", "source": V("a"), "var_name": "i", "value": V("i")},
          "b": {"type": "Count", "source": V("a")}},
         "expected WITNESS -- `Prod` exists, only the op name is missing"),
    106: ({"type": "Fold", "source": V("a"), "var_name": "i", "acc_name": "acc",
           "init": V("b"), "body": {"type": "Append", "seq": V("acc"), "item": V("i")}},
          "expected WITNESS -- list concat via the JoinList (Fold) precedent"),
    161: (FL(V("a"), "x", {"type": "Not", "arg": {
             "type": "In", "member": V("x"), "container": V("b")}}),
          "expected WITNESS -- `In` exists; the template pool lacks it"),
    257: ({"type": "Vec", "items": [V("b"), V("a")]},
          "expected WITNESS -- `Vec` exists; the op table lacks it"),
    264: ({"type": "IfThenElse", "cond": {"type": "Lte", "a": V("a"), "b": L(2)},
           "then": {"type": "Times", "items": [V("a"), L(10.5)]},
           "other": {"type": "Plus", "items": [L(21), {"type": "Times", "items": [
               {"type": "Minus", "a": V("a"), "b": L(2)}, L(4)]}]}},
          "expected WITNESS -- EVERY op is already in DEFAULT_OPS; this task "
          "is a pure search-budget case and is MISCLASSIFIED as structural"),
    290: ({"type": "Vec", "items": [
            {"type": "MaxOver", "source": V("a"), "var_name": "x",
             "value": {"type": "Count", "source": V("x")}},
            {"type": "Argmax", "source": V("a"), "var_name": "x",
             "value": {"type": "Count", "source": V("x")}}]},
          "expected WITNESS -- Vec + Argmax, both existing Terms"),
    # --- the refuting direction: terms whose NAME says they are the answer
    421: ({"type": "Join", "separator": L("-"), "items": V("a")},
          "expected REFUTATION -- `Join` is exactly the concept, and emits "
          "`Int(4)` for a non-string element"),
    424: (ML(V("a"), "x", {"type": "Last", "seq": V("x")}),
          "expected REFUTATION -- `item[-1]` IS in S4's map-template pool, "
          "yet `Last` returns None on a string"),
    450: (FL(V("a"), "e", {"type": "Eq", "a": {"type": "Count", "source": V("e")},
                           "b": V("b")}),
          "expected REFUTATION -- the A-ceiling called this a template-pool "
          "gap; `Count` on a string returns 0, so it is a missing primitive"),
    456: (ML(V("a"), "x", {"type": "StringSlice", "s": V("x"), "start": L(0),
                           "end": L(-1)}),
          "expected REFUTATION -- StringSlice has no negative index"),
    141: ({"type": "Argmax", "source": V("a"), "var_name": "x", "value": V("x")},
          "expected REFUTATION -- Argmax is an extremum, not an ordering"),
    87: ({"type": "Union", "a": V("a"), "b": V("b")},
         "expected REFUTATION -- Union on dicts returns an empty frozenset"),
    88: ({"type": "MkDict", "items": [V("a")]},
         "expected REFUTATION -- MkDict takes ALTERNATING k,v items"),
    118: ({"type": "Tokenize", "text": V("a")},
          "expected REFUTATION -- Tokenize returns spans, not substrings"),
    310: ({"type": "Tokenize", "text": V("a")},
          "expected REFUTATION -- same"),
    172: ({"type": "StringIndexOf", "haystack": V("a"), "needle": L("std")},
          "expected REFUTATION -- first index, not a count; note it matches "
          "row 1 by COINCIDENCE, which is why all rows are required"),
    479: ({"type": "IndexAt", "seq": V("a"), "index": L(0)},
          "expected REFUTATION -- IndexAt on an Int is None"),
}


def term_nodes(t):
    """Node count of a Term-JSON tree.  This is the enumerator's OWN size
    metric ('size = 1 (the node) + sum of child sizes',
    `synth_enumerate.rs`), applied to a hand-built tree so a witness can be
    compared against `max_size = 9`.  It is ARITHMETIC, not a live search:
    see the residual in the companion document."""
    if not isinstance(t, dict):
        return 0
    n = 1
    for k, v in t.items():
        if k == "type":
            continue
        if isinstance(v, dict):
            n += term_nodes(v)
        elif isinstance(v, list):
            n += sum(term_nodes(x) for x in v)
    return n


def run_witnesses(tasks):
    out = {}
    for tid in sorted(WITNESSES):
        term, note = WITNESSES[tid]
        parsed = parse_asserts(tasks[tid])
        split = split_rows(parsed["rows"], "primary")
        revealed = split["revealed"]  # HELD-OUT IS NEVER READ
        rows_out = []
        for row in revealed:
            status, got = ev(term, dict(row["inputs"]))
            expected = row["expected"]
            match = (status == "ok" and norm(got) == norm(expected))
            if (not match and status == "ok" and isinstance(expected, float)
                    and isinstance(got, (int, float))):
                tol = row.get("tol", 1e-3)
                match = abs(got - expected) <= tol * max(1.0, abs(expected))
            rows_out.append({"inputs": {k: repr(v)[:80] for k, v in row["inputs"].items()},
                             "got": repr(got)[:150],
                             "expected": repr(expected)[:150],
                             "match": bool(match)})
        n_ok = sum(1 for r in rows_out if r["match"])
        verdict = ("WITNESS" if n_ok == len(rows_out) and rows_out
                   else ("PARTIAL" if n_ok else "REFUTED"))
        out[str(tid)] = {"verdict": verdict, "rows_matched": n_ok,
                         "rows_total": len(rows_out),
                         "term_size_nodes": term_nodes(term),
                         "within_max_size_9": term_nodes(term) <= 9,
                         "note": note, "rows": rows_out}
    return out


def run_row_boundary(tasks, ids):
    """Can each task's own REVEALED rows even be handed to SynthEnumerate?
    A row set that cannot cross the `Lit` boundary is blocked BEFORE any
    search happens -- cost class (b), not (a) or (d)."""
    out = {}
    for tid in ids:
        parsed = parse_asserts(tasks[tid])
        split = split_rows(parsed["rows"], "primary")
        revealed = split["revealed"]
        synth_rows = [{"inputs": r["inputs"], "output": r["expected"]}
                      for r in revealed]
        status, val = ev({"type": "Lit", "value": synth_rows})
        out[str(tid)] = {
            "expressible": status == "ok",
            "error": None if status == "ok" else val,
            "expected_type": type(revealed[0]["expected"]).__name__,
            "input_types": [type(v).__name__ for v in revealed[0]["inputs"].values()],
            "unordered_assert": any(r.get("unordered") for r in parsed["rows"]),
        }
    return out


# ---------------------------------------------------------------------------
# 5.  BUNDLES -- the ceiling arithmetic.
# ---------------------------------------------------------------------------

BUNDLES = [
    ("B0_zero_new_termnode",
     "the EXACT arc-4 S4 shape: op-table + template-pool additions over "
     "Terms that ALREADY EXIST, plus making the existing sequence Terms "
     "string-aware.  Zero new TermNode variants.",
     ["op:TupleOf", "op:ProdList", "op:ConcatList", "op:ArgMaxLenOver",
      "tmpl:item_in_listvar", "tmpl:len_item_vs_var", "tmpl:nested_reduction",
      "fix:StringAsSequence"]),
    ("B1_plus_stdlib_terms",
     "B0 plus the string/sequence operators that exist in every programming "
     "language's standard library and that ProgEval ALREADY HAS at its own "
     "layer -- so each is a Term-layer port of a shipped behaviour, not a "
     "new idea.",
     ["op:TupleOf", "op:ProdList", "op:ConcatList", "op:ArgMaxLenOver",
      "tmpl:item_in_listvar", "tmpl:len_item_vs_var", "tmpl:nested_reduction",
      "fix:StringAsSequence",
      "term:Slice", "term:Replace", "term:Split", "term:Capitalize",
      "term:Str", "term:ParseInt", "term:Round", "term:Reverse",
      "term:IndexedMap", "term:StrCount"]),
    ("B2_plus_order_boundary_dict",
     "B1 plus ordering (which drags in the cross-cutting string-order fix), "
     "the set/Lit boundary, and the three dict operators.",
     ["op:TupleOf", "op:ProdList", "op:ConcatList", "op:ArgMaxLenOver",
      "tmpl:item_in_listvar", "tmpl:len_item_vs_var", "tmpl:nested_reduction",
      "fix:StringAsSequence",
      "term:Slice", "term:Replace", "term:Split", "term:Capitalize",
      "term:Str", "term:ParseInt", "term:Round", "term:Reverse",
      "term:IndexedMap", "term:StrCount",
      "term:Sort", "fix:StrOrder", "boundary:SetLit",
      "term:DictItems", "term:DictMerge", "term:GroupCount"]),
    ("B3_everything",
     "B2 plus recursion/unfold, combinatorial generators, str.format and a "
     "raised search budget -- i.e. every unit named anywhere in this "
     "measurement.  This is the INVENTORY ceiling, not a recommendation.",
     sorted(UNITS)),
]


def unlock(bundle_units):
    have = set(bundle_units)
    return sorted(tid for tid, (req, _why) in REQUIREMENTS.items()
                  if set(req) <= have)


def per_unit_yield():
    """Tasks unlocked by adding EXACTLY ONE unit to the empty bundle, and
    tasks for which the unit is NECESSARY.  The two numbers differ a lot,
    and quoting the second as the first is how a structural ceiling
    inflates."""
    out = {}
    for unit in sorted(UNITS):
        alone = sorted(tid for tid, (req, _w) in REQUIREMENTS.items() if req == [unit])
        necessary = sorted(tid for tid, (req, _w) in REQUIREMENTS.items() if unit in req)
        out[unit] = {"unlocked_alone_ids": alone, "n_alone": len(alone),
                     "necessary_for_ids": necessary, "n_necessary": len(necessary),
                     "cost_class": UNITS[unit]["cost_class"],
                     "new_termnode": UNITS[unit]["new_termnode"],
                     "blind": UNITS[unit]["blind"]}
    return out


# ---------------------------------------------------------------------------
# 6.  Held-out isolation audit -- proof, not assertion.
# ---------------------------------------------------------------------------

def generator_order_experiment(tasks):
    """THE CHERRY-PICK SEAM, measured rather than argued.

    A generator operator (`combinations`, `powerset`) is blind-nameable, but
    a generator has an ORDER, and a task that asserts a LIST asserts that
    order.  So: does the ORDER a general generator would naturally produce
    match what the task requires?  If not, the operator that unlocks the
    task is not the general one -- it is an order-specific variant chosen
    because this task needs it, which is exactly the A-ceiling's
    cherry-picking failure in structural clothing.

    Measured on REVEALED rows only, in pure Python (no sympy, no import
    claim): the question is about ORDER, not about which library provides
    the generator.
    """
    import itertools

    def powerset_size_lex(xs):
        return [list(c) for k in range(len(xs) + 1)
                for c in itertools.combinations(xs, k)]

    out = {}
    for tid, gen in ((255, "combinations_with_replacement"), (462, "powerset")):
        parsed = parse_asserts(tasks[tid])
        revealed = split_rows(parsed["rows"], "primary")["revealed"]
        rows = []
        for row in revealed:
            args = list(row["inputs"].values())
            if gen == "combinations_with_replacement":
                natural = [tuple(c) for c in
                           itertools.combinations_with_replacement(args[0], args[1])]
            else:
                natural = powerset_size_lex(args[0])
            expected = row["expected"]
            rows.append({
                "natural_order_matches": norm(natural) == norm(expected),
                "as_multiset_matches":
                    sorted(map(repr, natural)) == sorted(map(repr, expected)),
                "natural_head": repr(natural[:4]),
                "expected_head": repr(list(expected)[:4]),
            })
        out[str(tid)] = {
            "generator": gen,
            "rows": rows,
            "order_matches_on_every_revealed_row": all(r["natural_order_matches"] for r in rows),
            "same_elements_different_order": all(
                r["as_multiset_matches"] and not r["natural_order_matches"] for r in rows),
        }
    out["_reading"] = (
        "where `same_elements_different_order` is true, a BLIND generator "
        "operator computes the right SET and fails the task on ORDER alone.  "
        "The operator that would convert it is order-specific and therefore "
        "cherry-picked.  This reproduces, in the structural seam, the exact "
        "failure the A-ceiling measured for "
        "`sympy.utilities.iterables.subsets` on task 462 (0/3).")
    return out


def _held_out_isolation_audit():
    """No function that decides or verifies anything may mention held-out
    rows.  `split_rows(...)["revealed"]` is the ONLY row source used; the
    literal `held_out` appears nowhere in the analysing functions' source.
    (The `run_witnesses`/`run_row_boundary` sources are checked live.)"""
    bad = []
    audited = (run_witnesses, run_row_boundary, run_probes, unlock,
               per_unit_yield, term_nodes, generator_order_experiment)
    for fn in audited:
        src = inspect.getsource(fn)
        if "held_out" in src.replace("# HELD-OUT IS NEVER READ", ""):
            bad.append(fn.__name__)
    return {"functions_audited": [f.__name__ for f in audited],
        "functions_mentioning_held_out": bad,
        "clean": not bad}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(FIXTURE) as fh:
        tasks = {r["task_id"]: r for r in json.load(fh)}

    # --- population, derived and cross-checked --------------------------
    with open(BACKWARD_PROBE) as fh:
        bucket = json.load(fh)["ha4_search_reach_sizing"]["ok_already_no_named_lever"]
    moved = sorted({i for v in S4_MOVED.values() for i in v})
    s4_residual = sorted(set(bucket) - set(moved))

    with open(A_CEILING) as fh:
        a_ceiling = json.load(fh)
    struct_ids = sorted(
        a_ceiling["blocker_split"]["ids_over_live_unreached"]["missing_structural_primitive"])
    live_unreached = sorted(a_ceiling["staleness_correction"]["live_unreached_ids"])

    population = {
        "s4_85_bucket_n": len(bucket),
        "s4_residual_60_n": len(s4_residual),
        "live_unreached_53_ids": live_unreached,
        "live_unreached_n": len(live_unreached),
        "structural_42_ids": struct_ids,
        "structural_42_n": len(struct_ids),
        "source": "results/arc6_a_ceiling.json :: blocker_split."
                  "ids_over_live_unreached.missing_structural_primitive",
        "a_ceiling_sha256": sha256_of(A_CEILING),
        "cross_check_residual_matches_derivation":
            set(struct_ids) <= set(s4_residual),
        "cross_check_all_in_live_unreached": set(struct_ids) <= set(live_unreached),
        "cross_check_requirements_cover_population":
            sorted(REQUIREMENTS) == struct_ids,
    }

    probes = run_probes()
    witnesses = run_witnesses(tasks)
    boundary = run_row_boundary(tasks, struct_ids)

    bundles = []
    for name, why, units in BUNDLES:
        ids = unlock(units)
        bundles.append({
            "bundle": name, "rationale": why, "units": units,
            "n_units": len(units),
            "new_termnodes": sum(UNITS[u]["new_termnode"] for u in units),
            "unlocked_ids": ids, "n_unlocked": len(ids),
            "not_unlocked_ids": sorted(set(struct_ids) - set(ids)),
        })

    # --- the two ceilings ------------------------------------------------
    b0, b1, b2, b3 = (b["n_unlocked"] for b in bundles)
    ceilings = {
        "_definition": {
            "honest": "a task is counted only when EVERY unit it requires is "
                      "a GENERAL operator -- one nameable before the "
                      "population was read, whose yield is a CONSEQUENCE of "
                      "the unit rather than the REASON for it (the "
                      "A-ceiling's own rule, transposed from imports to "
                      "operators).",
            "cherry_picked": "one bespoke operator per task, named after that "
                             "task's own shape (`remove_odd_index_chars`, "
                             "`newman_recurrence`, `binary_reflected_"
                             "powerset`) -- an oracle table that encodes the "
                             "test-split answers.",
        },
        "honest_B0_zero_new_termnode": {"n": b0, "ids": bundles[0]["unlocked_ids"]},
        "honest_B1_plus_stdlib_terms": {"n": b1, "ids": bundles[1]["unlocked_ids"]},
        "honest_B2_plus_order_boundary_dict": {"n": b2, "ids": bundles[2]["unlocked_ids"]},
        "inventory_ceiling_B3_everything": {"n": b3, "ids": bundles[3]["unlocked_ids"]},
        "cherry_picked_per_task": {"n": len(struct_ids), "ids": struct_ids},
        "gap_B0_to_B3": b3 - b0,
        "inflation_B0_to_B3": round(b3 / b0, 2) if b0 else None,
        "why_the_A_CEILING_TRAP_DOES_NOT_REPRODUCE_IN_THE_SAME_FORM":
            "the A-ceiling's 5 -> 27 inflation came from GRANULARITY: a "
            "per-task kernel (`perrin_sum`) bought reach a general module "
            "(`sympy.ntheory`) did not, so the big number encoded the answer "
            "key.  Here the general operator set reaches the SAME 42 the "
            "bespoke one would -- `sort`, `slice`, `split`, `replace`, "
            "`str`, `round`, `reverse`, `enumerate`, `dict.items` are the "
            "standard library of every language and cannot be cherry-picked "
            "the way `perrin_sum` can.  THE INFLATION MECHANISM IS DIFFERENT, "
            "NOT ABSENT: here it is COST HIDING.  B0=%d costs zero new Term "
            "variants; B3=%d costs 17 new Term variants, a cross-cutting "
            "engine-semantics correction and a new capability.  The "
            "discipline that keeps 10 from becoming 42 is therefore PRICING "
            "THE TERMS, not auditing the naming." % (b0, b3),
        "the_one_place_the_A_CEILING_TRAP_DOES_REPRODUCE": {
            "where": "generator ORDER -- see "
                     "`generator_order_is_the_cherry_pick_seam`.",
            "measured": "task 255 SPLITS FROM task 462.  A blind "
                        "`combinations_with_replacement` reproduces 255's "
                        "revealed rows EXACTLY (order included), so 255 is "
                        "an honest unlock.  A blind size-lexicographic "
                        "powerset reproduces NEITHER 462's outer order NOR "
                        "the element order inside each subset -- the operator "
                        "that converts 462 is order-specific and was chosen "
                        "BECAUSE 462 needs it.  That is a cherry-pick.",
            "order_specific_ids": [462],
            "honest_inventory_ceiling_excluding_order_specific": b3 - 1,
        },
    }

    # --- strict reach: inventory suffices AND the composition is in reach
    strict = {}
    for tid, rec in witnesses.items():
        if rec["verdict"] == "WITNESS":
            strict[tid] = {"within_max_size_9": rec["within_max_size_9"],
                           "size": rec["term_size_nodes"]}
    strict_ids = sorted(int(t) for t, r in strict.items() if r["within_max_size_9"])
    over_budget_ids = sorted(int(t) for t, r in strict.items() if not r["within_max_size_9"])

    # --- the S4 discount: reach is not conversion ------------------------
    s4_discount = {
        "s4_moved_off_enumerate_failed": len(moved),
        "s4_fully_correct_pass": len(S4_MOVED["pass"]),
        "pass_rate_among_moved": round(len(S4_MOVED["pass"]) / len(moved), 3),
        "reading": "arc-4 S4 widened the enumerator by 11 ops and moved 25/85 "
                   "off `gapped:enumerate_failed`, of which only 8 were fully "
                   "correct.  A structural widening's PASS yield is therefore "
                   "empirically about a third of its REACH yield, ON THIS "
                   "PIPELINE.  Any headline quoting reach as conversion is "
                   "inflated by ~3x, and this prior is from the same corpus, "
                   "the same enumerator and the same protocol.",
    }

    # --- dimension vs operator -------------------------------------------
    dimension = {
        "missing_dimension_ids": [],
        "n": 0,
        "test_applied": "CLAUDE.md's own decision procedure: *is this value IN "
                        "a frame, or BETWEEN frames?*  A missing DIMENSION is "
                        "a coordinate the frame does not have at all (pi, an "
                        "irrational, a complex argument -- all cross-frame, "
                        "all unreachable at ANY search size).  Arc 5 proved "
                        "the claim converts by supplying pi exactly and "
                        "closing 82/85/139/233/276/312.",
        "finding": "ZERO of the 42 are blocked by a missing dimension.  Every "
                   "structural blocker produces a value ALREADY INSIDE the "
                   "value domain (Value::Tuple, Value::Str, Value::Dict) and "
                   "every coordinate involved -- a character index, a list "
                   "position, a digit place -- is an IN-FRAME INTEGER.  These "
                   "are operator gaps, not dimension gaps.",
        "the_two_borderline_cases": {
            "(index, element) binding": {
                "argument_for_dimension": "for a list with repeated elements, "
                    "NO composition of the current ops can distinguish two "
                    "occurrences -- every element-wise term is a function of "
                    "the element alone.  That is literally "
                    "unreachable-at-any-search-size, the property arc 5's "
                    "dimension claim rests on.",
                "argument_against": "a position is the tuple's own integer "
                    "ordinal and `IndexAt(seq, k)` already reads it.  The "
                    "coordinate is present in the frame; only the BINDER that "
                    "carries it into a map/filter body is missing.",
                "verdict": "OPERATOR.  In-frame integer => operator, by "
                           "CLAUDE.md's test.  Recorded because it is the one "
                           "case where the weaker claim looks like the "
                           "stronger one.",
            },
            "string as a sequence": {
                "argument_for_dimension": "a string is ATOMIC in the current "
                    "value domain -- measured: Count=0, IndexAt=None, "
                    "Last=None, In=False -- so a character is unreachable at "
                    "any search size.",
                "argument_against": "the character index is again an in-frame "
                    "integer, and the Terms exist and simply refuse "
                    "Value::Str.  This is a type-coverage gap in shipped "
                    "Terms, not an absent coordinate.",
                "verdict": "OPERATOR.",
            },
        },
        "consequence": "the structural seam is a WEAKER claim than arc 5's "
                       "pi result (no unreachable-at-any-size argument is "
                       "available) and a CHEAPER one (nothing here requires a "
                       "new value domain).  Those two facts are the same fact.",
    }

    record = {
        "_README": __doc__.strip(),
        "measured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "engine_provenance": provenance_stamp(strict=False),
        "engine_note": "site-packages/substrate_rs.pth is an ABSOLUTE path "
                       "into the canonical tree and _native.abi3.so is "
                       "gitignored, so a bare script in a worktree silently "
                       "imports a DIFFERENT binary.  Live here: this tree's "
                       "engine and the canonical tree's engine have different "
                       "sha256.  engine_preamble() is called before any "
                       "substrate_rs import and the sha256 is recorded above.",
        "population": population,
        "held_out_isolation": _held_out_isolation_audit(),
        "primitive_probes": probes,
        "probe_summary": {
            v: [p["probe"] for p in probes if p["verdict"] == v]
            for v in sorted({p["verdict"] for p in probes})
        },
        "str_order_is_process_dependent": str_order_experiment(),
        "unknown_op_is_a_silent_noop": unknown_op_experiment(),
        "generator_order_is_the_cherry_pick_seam": generator_order_experiment(tasks),
        "row_boundary_per_task": boundary,
        "row_boundary_blocked_ids": sorted(
            int(t) for t, r in boundary.items() if not r["expressible"]),
        "witnesses": witnesses,
        "witness_ids": sorted(int(t) for t, r in witnesses.items()
                              if r["verdict"] == "WITNESS"),
        "refuted_ids": sorted(int(t) for t, r in witnesses.items()
                              if r["verdict"] == "REFUTED"),
        "partial_ids": sorted(int(t) for t, r in witnesses.items()
                              if r["verdict"] == "PARTIAL"),
        "operator_units": UNITS,
        "per_task_requirements": {
            str(tid): {"requires": req, "why": why,
                       "cost_classes": sorted({UNITS[u]["cost_class"] for u in req})}
            for tid, (req, why) in sorted(REQUIREMENTS.items())
        },
        "per_unit_yield": per_unit_yield(),
        "bundles": bundles,
        "ceilings": ceilings,
        "strict_reach": {
            "_definition": "a WITNESS proves the primitive inventory suffices; "
                           "`within_max_size_9` additionally checks the "
                           "composition against the enumerator's own default "
                           "budget.  This half is SIZE ARITHMETIC under the "
                           "module's documented rule, not a live search -- "
                           "only a build settles it.",
            "witness_and_in_budget_ids": strict_ids,
            "witness_but_over_budget_ids": over_budget_ids,
            "per_task": strict,
        },
        "s4_reach_vs_conversion_prior": s4_discount,
        "inventory_ceiling_is_not_reach": {
            "claim": "every bundle number above is an INVENTORY ceiling: it "
                     "counts tasks whose required PRIMITIVES would all exist. "
                     "It is NOT a claim that the enumerator would FIND the "
                     "composition.",
            "two_separate_discounts": [
                "(1) size.  Only `strict_reach.witness_and_in_budget_ids` is "
                "checked against `max_size=9`, and even that is size "
                "arithmetic rather than a live search.",
                "(2) search-space growth.  Several units make the search "
                "HARDER as they make it richer.  `term:Recurse` is the "
                "extreme case: a self-referential binder in an enumerative "
                "search is a combinatorial explosion, so the 6 ids it "
                "unlocks at the inventory level (99, 260, 265, 283, 301, "
                "448, 462) are the LEAST likely of the 42 to convert.  "
                "`tmpl:nested_reduction` has the same shape at smaller "
                "scale: S4 sec 4.4 named the bounded-vs-recursive template "
                "grammar as an architectural seam, not a parameter.",
            ],
            "consequence": "the honest expected CONVERSION for a bundle is "
                           "its inventory count discounted twice -- once by "
                           "size/reach, once by the S4 pass-rate prior "
                           "(8/25 = 32%% of moved tasks were fully correct).",
        },
        "dimension_vs_operator": dimension,
        "cost_class_legend": {
            "a_enum_op": "(a) a missing SynthEnumerate OPERATOR over a Term "
                         "that already exists -- zero new TermNode, the exact "
                         "arc-4 S4 shape",
            "a_template": "(a) a missing entry in the bounded filter/map "
                          "TEMPLATE POOL -- zero new TermNode",
            "a_new_termnode": "(a) a genuinely new DSL Term variant "
                              "(term.rs + jsonio.rs + the enumerator's local "
                              "term_json/term_str serialisers)",
            "a_new_capability": "(a) a capability decision that changes what "
                                "the search space IS, not an operator in it",
            "b_boundary": "(b) a Value/JSON boundary that cannot represent "
                          "the result at all",
            "c_engine_semantics": "(c) shipped engine semantics that are "
                                  "WRONG and must be corrected, with "
                                  "cross-cutting blast radius",
            "d_search": "(d) every operator exists; the composition is out of "
                        "the search's reach",
        },
    }

    payload = json.dumps({k: v for k, v in record.items()
                          if k not in ("measured_at", "engine_provenance")},
                         sort_keys=True, default=str)
    record["id_hash"] = hashlib.sha256(payload.encode()).hexdigest()[:16]

    with open(OUT, "w") as fh:
        json.dump(record, fh, indent=1, sort_keys=False, default=str)

    # ---- stdout summary -------------------------------------------------
    print(provenance_line())
    print("population: 42 structural ids, cross-checks:",
          {k: v for k, v in population.items() if k.startswith("cross_check")})
    print("\nprobe verdicts:")
    for v, ids in record["probe_summary"].items():
        print("  %-22s %d  %s" % (v, len(ids), " ".join(ids)))
    print("\nwitnesses (inventory suffices):", record["witness_ids"])
    print("refuted   (name looked right):  ", record["refuted_ids"])
    print("partial:                        ", record["partial_ids"])
    print("row-boundary blocked:           ", record["row_boundary_blocked_ids"])
    print("\nbundles:")
    for b in bundles:
        print("  %-32s units=%-2d newTerm=%-2d unlocked=%-2d %s"
              % (b["bundle"], b["n_units"], b["new_termnodes"],
                 b["n_unlocked"], b["unlocked_ids"]))
    print("\nceilings: honest B0=%d  B1=%d  B2=%d | inventory B3=%d | "
          "cherry-picked=%d" % (b0, b1, b2, b3, len(struct_ids)))
    print("\ngenerator order (the cherry-pick seam):")
    for tid in ("255", "462"):
        g = record["generator_order_is_the_cherry_pick_seam"][tid]
        print("  task %s (%s): order_matches=%s  same_elements_wrong_order=%s"
              % (tid, g["generator"], g["order_matches_on_every_revealed_row"],
                 g["same_elements_different_order"]))
    print("\ndimension ids:", dimension["missing_dimension_ids"])
    print("str-order process-dependent:",
          record["str_order_is_process_dependent"]["process_history_dependent"])
    print("\nid_hash =", record["id_hash"])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
