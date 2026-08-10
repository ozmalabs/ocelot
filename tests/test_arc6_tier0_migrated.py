"""test_arc6_tier0_migrated — gates for the ARC-6 TIER-0 op-table widening.

WHAT THIS GATES (`PROGRAM_SYNTHESIS_ARC6_PREREG.md` §2/§3,
`PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` §4.1/§9): eight units,
**zero new `TermNode` variants**, acting on the measured finding that
`ProgEval` already EXECUTES what `SynthEnumerate` could not PROPOSE.

  1  fix:StringAsSequence   `Count`/`IndexAt`/`Last`/`In` accept a string
  2  op:TupleOf             the shipped `Vec` Term as an op
  3  op:ProdList            the shipped `Prod` Term; the `SumList` twin
  4  op:ConcatList          list concat as `Fold`+`Append`
  5  op:ArgMaxLenOver       the arg-twin of the shipped `MaxLenOver`
  6  tmpl:item_in_listvar   `item (not) in <list var>`
  7  tmpl:len_item_vs_var   `len(item) OP <scalar var>`
  8  tmpl:nested_reduction  a quantifier over the bound item in a predicate

Every gate is a LIVE INVOCATION, never a name check, for two reasons this
project has already paid for:

  * **An unknown op name is a SILENT NO-OP** (`ops=["Bogus"]` -> `found:
    false, halt_reason:"saturated"`), so a typo would read as an honest
    null.  Each op is therefore asserted to actually FIRE and to produce
    the named Term shape.
  * **Four Terms have the right names and the wrong values** (`Count(str)
    -> 0`, `Last(str) -> None`, `Cat([list,list])` -> Rust debug reprs,
    `Union(dict,dict) -> frozenset()`).  Reading the source would have
    confirmed each; invocation refuted them.

`test_no_regression_scalar_and_string_specs_are_untouched` and
`test_tuple_constructor_does_not_regress_an_already_solved_spec` are the
HS2 (soundness) gates: the second is task 132's OWN spec shape, which the
first cut of this widening genuinely REGRESSED (adding an ungated
`TupleOf` moved `distinct` 167 -> 14709 and turned a size-6 `solved` into
`halt_reason:"budget"`).  It is pinned so the regression cannot come back.

`test_hs3_no_new_termnode_variants` and `test_hs4_op_table_is_the_unit_list`
are mechanical source audits of the two registered COST bars.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest tests/test_arc6_tier0_migrated.py \
    --confcutdir=<this worktree> -q
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

SUB = srs.Substrate()


def L(v):
    return {"type": "Lit", "value": v}


def V(n):
    return {"type": "Var", "name": n}


def ev(term, env=None):
    return SUB._inner.evaluate(term, env or {})


# ARC6 PRUNING FIX (2026-08-03) — THE SPEC WIRE MUST CARRY THE SPEC'S
# TYPES.  `Substrate.evaluate()` serialises its Term dict through JSON, and
# JSON has ONE array type: a Python `list` and a Python `tuple` inside a
# `Lit` both decode as `Value::Tuple`.  That was harmless while list and
# tuple were one Value; under the ARC6 value layer it silently RETYPES
# every list-valued expected output as a tuple, so a spec that means "the
# answer is a list" arrives asking for a tuple and the correct
# list-producing candidate is refused.  `domains.prog_synthesis._wire_rows`
# is the shipped write side of the engine's own tagged form
# (`__list__`/`__tuple__`/`__set__`/`__fset__`, `persist.rs`) and is what
# every production caller already uses; the gates use it too, so what the
# spec DECLARES is what the search is asked for.  A bare array still means
# `Tuple`, so no seed-resident `Lit` literal changes meaning.
from domains.prog_synthesis import _wire_rows  # noqa: E402


def synth(rows, ops=None, max_size=9, max_candidates=0):
    spec = {"type": "SynthEnumerate",
            "examples": L(_wire_rows(rows)),
            "max_size": max_size, "max_candidates": max_candidates,
            "saturate_k": 0, "field": ""}
    if ops is not None:
        spec["ops"] = L(ops)
    return ev(spec)


def term_types(term_json_str):
    """Every `type` name in a returned Term-JSON — so a gate can assert the
    winning candidate really is the SHAPE the unit claims to add, not some
    other term that happened to fit."""
    out = set()

    def walk(o):
        if isinstance(o, dict):
            if "type" in o:
                out.add(o["type"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(json.loads(term_json_str))
    return out


# ===========================================================================
# 1. fix:StringAsSequence — the four shipped Terms, both directions.
# ===========================================================================

def test_count_of_a_string_is_its_character_count():
    # The measured defect: this returned 0.
    assert ev({"type": "Count", "source": L("abc")}) == 3
    assert ev({"type": "Count", "source": L("")}) == 0
    # CHARACTERS, not bytes.
    assert ev({"type": "Count", "source": L("héllo")}) == 5
    # Untouched directions.
    assert ev({"type": "Count", "source": L([1, 2, 3])}) == 3
    assert ev({"type": "Count", "source": L({"a": 1})}) == 1
    assert ev({"type": "Count", "source": L(5)}) == 0
    assert ev({"type": "Count", "source": L(None)}) == 0


def test_indexat_and_last_read_characters_out_of_a_string():
    # Both returned None before.
    assert ev({"type": "IndexAt", "seq": L("abc"), "index": L(0)}) == "a"
    assert ev({"type": "IndexAt", "seq": L("abc"), "index": L(2)}) == "c"
    # Python-style from-the-end indexing, the SAME rule the sequence path uses.
    assert ev({"type": "IndexAt", "seq": L("abc"), "index": L(-1)}) == "c"
    assert ev({"type": "IndexAt", "seq": L("abc"), "index": L(-3)}) == "a"
    # Out of range stays None, in BOTH directions.
    assert ev({"type": "IndexAt", "seq": L("abc"), "index": L(3)}) is None
    assert ev({"type": "IndexAt", "seq": L("abc"), "index": L(-4)}) is None
    assert ev({"type": "Last", "seq": L("abc")}) == "c"
    assert ev({"type": "Last", "seq": L("")}) is None
    # Untouched directions.
    assert ev({"type": "IndexAt", "seq": L([7, 8]), "index": L(0)}) == 7
    assert ev({"type": "Last", "seq": L([7, 8])}) == 8
    assert ev({"type": "Last", "seq": L(5)}) is None


def test_in_on_two_strings_is_pythons_substring_test():
    # Returned False before, for every string pair.
    assert ev({"type": "In", "member": L("a"), "container": L("cat")}) is True
    assert ev({"type": "In", "member": L("at"), "container": L("cat")}) is True
    assert ev({"type": "In", "member": L("z"), "container": L("cat")}) is False
    assert ev({"type": "In", "member": L("ct"), "container": L("cat")}) is False
    assert ev({"type": "In", "member": L(""), "container": L("cat")}) is True
    # Untouched: a text member in a COLLECTION keeps the element scan, so
    # `"a" in ["ab"]` stays False (it is not a substring test there).
    assert ev({"type": "In", "member": L("a"), "container": L(["a", "b"])}) is True
    assert ev({"type": "In", "member": L("a"), "container": L(["ab"])}) is False
    assert ev({"type": "In", "member": L(1), "container": L([1, 2])}) is True
    # Untouched: a non-text member in a text container stays False.
    assert ev({"type": "In", "member": L(1), "container": L("cat")}) is False


def test_string_as_sequence_reaches_the_search_through_a_shipped_template():
    """`item[-1]` was ALREADY in the S4 map-template pool and silently
    produced `(None, None, None)` on strings.  Same pool, now correct.

    2026-08-03 (arc6 pruning fix): the expected output is a LIST.  This
    unit's answer is `MapList`, i.e. Python's `[x[-1] for x in a]`, and a
    list comprehension is a LIST -- under the ARC6 value layer that is no
    longer the same thing as a tuple.  The pin was written pre-value-layer
    and named a tuple; re-pinned to what the term actually returns, and
    delivered over the type-faithful wire so the declaration survives JSON.
    This is STRICTER than the old pin, not wider -- see the refuting-
    direction gate at the foot of this module."""
    rows = [{"inputs": {"a": ["cat", "dog"]}, "output": ["t", "g"]},
            {"inputs": {"a": ["ab"]}, "output": ["b"]},
            {"inputs": {"a": ["xyz", "pq", "r"]}, "output": ["z", "q", "r"]}]
    out = synth(rows)
    assert out["found"] is True, out["halt_reason"]
    assert {"MapList", "IndexAt"} <= term_types(out["term"])


# ===========================================================================
# 2-5. The four new op names — each must actually FIRE.
# ===========================================================================

def test_op_tupleof_fires_and_builds_a_Vec():
    rows = [{"inputs": {"a": 10, "b": 20}, "output": (20, 10)},
            {"inputs": {"a": 15, "b": 17}, "output": (17, 15)},
            {"inputs": {"a": 1, "b": 2}, "output": (2, 1)},
            {"inputs": {"a": -4, "b": 6}, "output": (6, -4)}]
    out = synth(rows)
    assert out["found"] is True, out["halt_reason"]
    assert "Vec" in term_types(out["term"])
    assert out["size"] == 3


def test_op_prodlist_fires_and_builds_a_Prod():
    rows = [{"inputs": {"a": [1, 2, 3]}, "output": 6},
            {"inputs": {"a": [2, 2, 2, 2]}, "output": 16},
            {"inputs": {"a": [3, 5]}, "output": 15},
            {"inputs": {"a": [7]}, "output": 7}]
    out = synth(rows, ops=["ProdList"])
    assert out["found"] is True, out["halt_reason"]
    assert "Prod" in term_types(out["term"])


def test_op_concatlist_fires_and_builds_a_Fold_Append():
    """2026-08-03 (arc6 pruning fix): expected output re-pinned to a LIST,
    for TYPE CONSISTENCY WITH ITS OWN INPUTS -- `a` and `b` are lists, and
    `Fold`+`Append` over them yields a list.  The old tuple pin only ever
    held because the wire collapsed both to `Value::Tuple`."""
    rows = [{"inputs": {"a": [1, 2], "b": [3]}, "output": [1, 2, 3]},
            {"inputs": {"a": [9], "b": [8, 7]}, "output": [9, 8, 7]},
            {"inputs": {"a": [4, 4], "b": [5, 5]}, "output": [4, 4, 5, 5]},
            {"inputs": {"a": [], "b": [1]}, "output": [1]}]
    out = synth(rows)
    assert out["found"] is True, out["halt_reason"]
    assert {"Fold", "Append"} <= term_types(out["term"])


def test_op_argmaxlenover_fires_and_builds_an_Argmax_over_Count():
    """WITH ITS CONTROL, and the control is the point.

    A first version of this gate used rows where the longest sublist was
    simply the answer, and `MaxList` fitted them too — because
    `value.rs::cmp_value` orders two Tuples BY LENGTH FIRST.  So on
    tuple-valued elements the shipped `MaxList` ALREADY behaves as
    max-by-length, and `op:ArgMaxLenOver` adds nothing there except the
    TIE-BREAK.  That is recorded rather than smoothed over: it materially
    weakens the unit, and a gate that did not carry a live control would
    have hidden it.

    These rows are ties on length, where the two genuinely differ:
    `Argmax` over `Count` returns the FIRST maximal element, `MaxList`
    returns the element-wise greatest.

    (2026-08-03, arc6 pruning fix: the expected output is re-pinned to a
    LIST, for TYPE CONSISTENCY WITH ITS OWN INPUT -- `Argmax` returns an
    ELEMENT of `a`, and `a`'s elements are lists.)"""
    rows = [{"inputs": {"a": [[1, 9], [2, 0]]}, "output": [1, 9]},
            {"inputs": {"a": [[1, 1], [9, 9], [0]]}, "output": [1, 1]},
            {"inputs": {"a": [[2, 2], [4, 4], [7]]}, "output": [2, 2]}]
    # THE CONTROL: MaxList must NOT fit these rows.
    control = synth(rows, ops=["MaxList"])
    assert control["found"] is False
    out = synth(rows, ops=["ArgMaxLenOver"])
    assert out["found"] is True, out["halt_reason"]
    assert {"Argmax", "Count"} <= term_types(out["term"])


# ===========================================================================
# 6-8. The three template units.
# ===========================================================================

def test_tmpl_item_in_listvar_fires():
    """2026-08-03 (arc6 pruning fix): expected output re-pinned to a LIST.
    The answer is `FilterList`, i.e. `[x for x in a if x not in b]`, and a
    list comprehension is a LIST.  See the module note on `_wire_rows`."""
    rows = [{"inputs": {"a": [1, 2, 3, 4], "b": [2, 4]}, "output": [1, 3]},
            {"inputs": {"a": [5, 6], "b": [6]}, "output": [5]},
            {"inputs": {"a": [7, 8, 9], "b": [7, 9]}, "output": [8]},
            {"inputs": {"a": [1, 2], "b": []}, "output": [1, 2]}]
    out = synth(rows)
    assert out["found"] is True, out["halt_reason"]
    assert {"FilterList", "In", "Not"} <= term_types(out["term"])
    # FX1's own number: the search is SOLVED, not merely under budget.
    assert out["halt_reason"] == "solved"
    assert out["distinct"] == 1434, out["distinct"]


def test_tmpl_len_item_vs_var_fires():
    """Needs `fix:StringAsSequence` too -- `Count` on a string used to
    return 0, so this predicate matched NOTHING.  Both units at once.
    (2026-08-03: expected output re-pinned to a LIST.)"""
    rows = [{"inputs": {"a": ["ab", "cde", "fg"], "b": 2}, "output": ["ab", "fg"]},
            {"inputs": {"a": ["x", "yz", "w"], "b": 1}, "output": ["x", "w"]},
            {"inputs": {"a": ["abc", "de"], "b": 3}, "output": ["abc"]},
            {"inputs": {"a": ["pq", "rs"], "b": 5}, "output": []}]
    out = synth(rows)
    assert out["found"] is True, out["halt_reason"]
    assert {"FilterList", "Count"} <= term_types(out["term"])


def test_tmpl_nested_reduction_fires():
    """2026-08-03: expected output re-pinned to a LIST -- and so are its
    ELEMENTS, which are the input's own sublists, themselves lists."""
    rows = [{"inputs": {"a": [[1, 2], [9, 1], [3]], "b": 3}, "output": [[1, 2], [3]]},
            {"inputs": {"a": [[5], [1, 1]], "b": 2}, "output": [[1, 1]]},
            {"inputs": {"a": [[2, 2], [4]], "b": 2}, "output": [[2, 2]]},
            {"inputs": {"a": [[8]], "b": 1}, "output": []}]
    out = synth(rows)
    assert out["found"] is True, out["halt_reason"]
    ts = term_types(out["term"])
    assert "FilterList" in ts
    # A REDUCTION inside the predicate is the whole unit.
    assert ts & {"MaxOver", "MinOver", "Sum"}


# ===========================================================================
# HS2 — soundness.  Nothing that worked may stop working.
# ===========================================================================

def test_no_regression_scalar_and_string_specs_are_untouched():
    """A spec that is neither list-shaped nor list-OUTPUT keeps the
    pre-widening typed default, so its search is byte-identical."""
    scalar = [{"inputs": {"x": 0}, "output": 1},
              {"inputs": {"x": 1}, "output": 2},
              {"inputs": {"x": 2}, "output": 3}]
    out = synth(scalar, max_size=7)
    assert out["found"] is True
    assert out["term_str"] == "(x + 1)"
    assert out["size"] == 3
    string = [{"inputs": {"s": "AB"}, "output": "ab"},
              {"inputs": {"s": "Cd"}, "output": "cd"}]
    out = synth(string, max_size=5)
    assert out["found"] is True
    assert "CaseFold" in term_types(out["term"])


def test_tuple_constructor_does_not_regress_an_already_solved_spec():
    """THE HS2 PIN.  This spec (task 132's shape: a list of characters ->
    the joined string) is solved by `JoinList` at size 6.  The first cut of
    this widening offered `TupleOf` to it and blew the candidate budget
    before reaching size 6 -- a REGRESSION of an already-passing task.

    `TupleOf` is now offered only when the spec's OUTPUT is tuple-shaped,
    and is registered as a TERMINAL candidate (never a building block), so
    it cannot multiply the distinct pool.  Both are pinned here."""
    rows = [{"inputs": {"a": ["e", "x", "e", "r", "c", "i", "s", "e", "s"]},
             "output": "exercises"},
            {"inputs": {"a": ["p", "y", "t", "h", "o", "n"]}, "output": "python"}]
    out = synth(rows)
    assert out["found"] is True, out["halt_reason"]
    assert out["halt_reason"] == "solved"
    assert out["size"] == 6
    assert "Fold" in term_types(out["term"])
    # The pool stays bounded: the regression showed up as distinct blowing
    # from 167 to 14709.  A generous ceiling, well under that.
    assert out["distinct"] < 5000, out["distinct"]


def test_unknown_op_is_still_a_silent_no_op_not_a_crash():
    """Registered hazard: a MISSPELLED op name never fires and looks like an
    honest null.  Pinned so the property stays visible."""
    # TWO rows with DIFFERENT outputs, so no auto-appended constant leaf can
    # fit the spec on its own -- a single-row spec is solved at size 1 by
    # `Lit(<the output>)` and would pass this gate with no ops at all.
    rows = [{"inputs": {"x": 1}, "output": 2},
            {"inputs": {"x": 5}, "output": 6}]
    out = synth(rows, ops=["Bogus"])
    assert out["found"] is False
    assert out["halt_reason"] in ("saturated", "max_size")
    out = synth(rows, ops=["Bogus", "Plus"])
    assert out["found"] is True


# ===========================================================================
# HS3 / HS4 — the two registered COST bars, as mechanical source audits.
# ===========================================================================

def _git_show(path):
    return subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + path],
                          capture_output=True, text=True).stdout


def _termnode_variants(text):
    i = text.index("pub enum TermNode {")
    depth, start = 0, i + len("pub enum TermNode ")
    body = None
    for k in range(start, len(text)):
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
            if depth == 0:
                body = text[start + 1:k]
                break
    assert body is not None
    names, d = [], 0
    for line in body.splitlines():
        s = line.strip()
        if d == 0:
            m = re.match(r"^([A-Z][A-Za-z0-9_]*)\s*(\{|\(|,|$)", s)
            if m:
                names.append(m.group(1))
        d += line.count("{") - line.count("}")
    return names


def test_hs3_no_new_termnode_variants():
    """HS3 (registered): tier 0 costs ZERO new `TermNode` variants.  The
    prereg's own rule -- *in a structural seam audit the PRICE; count
    variants, not names* -- made mechanical."""
    rel = os.path.join("runners", "dsl", "src", "term.rs")
    committed = _git_show(rel)
    if not committed:
        return  # nothing to diff against (shallow/other checkout)
    with open(os.path.join(ROOT, rel)) as f:
        live = f.read()
    added = set(_termnode_variants(live)) - set(_termnode_variants(committed))
    assert added == set(), "tier 0 added TermNode variants: %s" % sorted(added)


# The eight units, EXACTLY as `PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md`
# §9 names them -- written from that list, not from any task.
ARC6_TIER0_UNITS = [
    "fix:StringAsSequence",
    "op:TupleOf",
    "op:ProdList",
    "op:ConcatList",
    "op:ArgMaxLenOver",
    "tmpl:item_in_listvar",
    "tmpl:len_item_vs_var",
    "tmpl:nested_reduction",
]

# The op NAMES the four op-units contribute.  A per-task operator (the
# registered HS4 failure mode -- `remove_odd_index_chars`,
# `binary_reflected_powerset`) would appear here as a name no unit implies.
ARC6_TIER0_OP_NAMES = {"TupleOf", "ProdList", "ConcatList", "ArgMaxLenOver"}


def test_hs4_op_table_is_the_unit_list_and_nothing_else():
    """HS4 (registered): the shipped op table must diff EMPTY against one
    written from the operator list alone.  Mechanical both ways -- no name
    the units do not imply, and no unit without its name."""
    rel = os.path.join("runners", "dsl", "src", "synth_enumerate.rs")
    with open(os.path.join(ROOT, rel)) as f:
        live = f.read()
    committed = _git_show(rel)
    live_ops = set(re.findall(r'\(\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*,\s*OpKind::', live))
    if committed:
        old_ops = set(re.findall(r'\(\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*,\s*OpKind::', committed))
        assert live_ops - old_ops == ARC6_TIER0_OP_NAMES, \
            "op table diff is not the unit list: added %s" % sorted(live_ops - old_ops)
        assert old_ops - live_ops == set(), "tier 0 removed an op name"
    # Every op unit's name is actually IN the table (an absent name is a
    # silent no-op, so this is the other half of the diff).
    assert ARC6_TIER0_OP_NAMES <= live_ops


def test_hs4_units_are_all_present_and_named_in_the_source():
    """Each of the eight units names itself at its implementation site, so
    the shipped table is diffable against the unit list by reading."""
    src = ""
    for rel in (os.path.join("runners", "dsl", "src", "synth_enumerate.rs"),
                os.path.join("runners", "dsl", "src", "term.rs")):
        with open(os.path.join(ROOT, rel)) as f:
            src += f.read()
    missing = [u for u in ARC6_TIER0_UNITS if u not in src]
    assert missing == [], "units not named at their implementation site: %s" % missing


def test_no_python_decision_was_added():
    """ARCHITECTURE (CLAUDE.md): decisions are Rules/Terms; Python is
    mechanical I/O.  Tier 0 is entirely Rust + the op table -- it must add
    NO Python under `domains/`."""
    out = subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "domains", "seeds"],
                         capture_output=True, text=True).stdout.strip()
    assert out == "", "tier 0 must not touch domains/ or seeds/: %s" % out


# ===========================================================================
# ARC6 PRUNING FIX (2026-08-03) — THE REFUTING DIRECTION, WHICH IS WHY THE
# FOUR SPECS ABOVE WERE RE-PINNED RATHER THAN WIDENED.
#
# The four tier-0 template gates went red after the value layer.  The
# registered diagnosis was a SEARCH-SPACE EXPLOSION ("list and tuple no
# longer collide, so observational-equivalence pruning is weaker;
# distinct 1,434 -> 16,148").  Measured, that INVERTS cause and effect:
# `FilterList`/`MapList` now correctly return a `Value::List` (a Python
# list comprehension is a list), the specs declared TUPLE-typed expected
# outputs over a wire that could not carry the distinction anyway, so the
# search was asked for something no candidate can produce, ran to its
# 200,000-candidate budget, and ACCUMULATED 16,148 distinct behaviours
# BECAUSE it never halted.  Give the same search the type it actually
# means and it solves at exactly 1,434 — the arm-A figure, unchanged.
#
# These two gates pin BOTH directions, so the property cannot silently
# revert to a collapse: the same spec is SOLVED when it asks for a list
# and REFUSED when it asks for a tuple.
# ===========================================================================

_MAP_ROWS = [{"inputs": {"lists": [[1, 2], [3, 4]]}, "output": [1, 3]},
             {"inputs": {"lists": [[9], [7, 8, 9]]}, "output": [9, 7]}]


def test_list_typed_spec_is_solved_by_the_list_producing_term():
    out = synth(_MAP_ROWS, ops=["MapList"])
    assert out["found"] is True, out["halt_reason"]
    assert {"MapList", "IndexAt"} <= term_types(out["term"])


def test_tuple_typed_spec_is_NOT_solved_by_the_list_producing_term():
    """THE VALUE LAYER'S OWN PROPERTY.  Byte-identical rows, the expected
    output declared a TUPLE — a list comprehension does not produce one, so
    the honest verdict is `found:false`.  Before the value layer these two
    specs were INDISTINGUISHABLE; if a later change re-merges list and
    tuple in the spec-target relation, this gate goes red."""
    rows = [dict(r, output=tuple(r["output"])) for r in _MAP_ROWS]
    out = synth(rows, ops=["MapList"])
    assert out["found"] is False, out["term_str"]


def test_the_bare_lit_wire_is_no_longer_lossy():
    """REPOINTED by prereg A8 (2026-08-03). This gate was
    `test_the_bare_lit_wire_is_the_thing_that_was_lossy`, and it pinned the
    DEFECT: without the tagged wire a bare `Lit` list arrived as a tuple, so
    a list-declared and a tuple-declared spec were literally the SAME spec —
    the collapse that cost this project one wrong prereg amendment (A6) and
    one wrong pair of diagnoses (A7).

    `py.rs::pyobj_to_json_term` fixes that at the encode boundary, so the
    gate is repointed at the corrected fact rather than deleted. BOTH
    directions are kept, because the value of this gate was always that it
    is paired: the bare wire now carries a list AS a list, and the
    tuple-declared spec is STILL refused (below). If a later change
    re-collapses the two, both halves go red."""
    bare = {"type": "SynthEnumerate", "examples": L(_MAP_ROWS),
            "max_size": 9, "max_candidates": 0, "saturate_k": 0, "field": "",
            "ops": L(["MapList"])}
    out = ev(bare)
    assert out["found"] is True, out          # the BARE wire now solves it,
    assert out["halt_reason"] == "solved"     # with no `_wire_rows` at all,
    assert out["tested"] == 25                # at arm A's own figures.
    assert out["distinct"] == 17
    assert ev({"type": "Lit", "value": [1, 2]}) == [1, 2]          # list  -> LIST
    assert type(ev({"type": "Lit", "value": [1, 2]})) is list
    assert ev({"type": "Lit", "value": (1, 2)}) == (1, 2)          # tuple -> TUPLE
    assert type(ev({"type": "Lit", "value": (1, 2)})) is tuple
    # `_wire_rows` still works and is now REDUNDANT rather than required.
    assert ev(L(_wire_rows([{"inputs": {}, "output": [1, 2]}])[0]["output"])) == [1, 2]
