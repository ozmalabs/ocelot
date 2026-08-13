"""test_arc6_valuelayer_migrated — gates for the ARC-6 VALUE-LAYER
list/tuple distinction (`PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md`, prereg
amendment **A3**, bars HV1-HV4).

WHAT THIS GATES.  `list` and `tuple` used to be the SAME `Value::Tuple`,
so `{"a":[1,2,3]}` read back `(1,2,3)` and `Eq((1,2),[1,2])` was True.
That collapse was measured (`PROGRAM_SYNTHESIS_ARC6_VERDICT.md` §4) to
produce **12 false accepts out of 15** the moment any non-scalar row
verdict was switched on.  The fix is a distinct `Value::List` variant
plus type-faithful `ProgEval`.

EVERY GATE IS A LIVE INVOCATION, IN BOTH DIRECTIONS.  The standing rule
in this tree is that *a bug in the refuting direction is
indistinguishable from an honest null* — a comparator that returned False
for everything would satisfy a one-sided "the tuple case is rejected"
test.  So each equality gate asserts the True case as well, and the row
verdict is driven to BOTH `pass` and `fail` on the same shape.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 COLUMNS=250 \
    pytest tests/test_arc6_valuelayer_migrated.py --confcutdir=<this worktree> -q
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import pytest  # noqa: E402
import substrate_rs as srs  # noqa: E402
from domains import prog_synthesis as psy  # noqa: E402
from domains.prog_ir_emit import (  # noqa: E402
    NATIVE_ORACLES, NATIVE_RECV_ORACLES, emit_prog_ir,
)


def _lit(v):
    return {"type": "Lit", "value": v}


def _oracles():
    items = []
    for n in sorted(set(NATIVE_ORACLES) | set(NATIVE_RECV_ORACLES)):
        items += [_lit(n), _lit("builtin")]
    return {"type": "MkDict", "items": items}


def _run_source(src, env):
    """Compile real Python source to the hub Program IR and run it in
    `ProgEval`, returning the Python object the substrate hands back."""
    emitted = emit_prog_ir(src)
    assert emitted.get("ok"), emitted.get("blockers")
    s = srs.Substrate()
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": emitted["ir"],
         "env": {"type": "Var", "name": "e"}, "oracles": _oracles(),
         "fuel": psy._FUEL, "field": ""},
        {"e": dict(env)})
    assert out.get("trap") is None, out.get("trap")
    return out.get("result")


def _ref(src, env):
    ns = {}
    exec(compile(src, "<gate>", "exec"), ns)  # noqa: S102
    return ns["f"](*[env[k] for k in sorted(env)])


# ---------------------------------------------------------------------------
# 1) the value layer itself — the attr boundary, in both directions
# ---------------------------------------------------------------------------
def test_a_list_attr_reads_back_as_a_list_and_a_tuple_as_a_tuple():
    s = srs.Substrate()
    n = s.add_node("X", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    at = s.node(n)["attrs"]
    assert isinstance(at["lst"], list) and at["lst"] == [1, 2, 3]
    assert isinstance(at["tup"], tuple) and at["tup"] == (1, 2, 3)


def test_eq_distinguishes_list_from_tuple_in_BOTH_directions():
    """The refuting direction alone proves nothing: a comparator stuck at
    False would pass it.  Equal-kind pairs must still agree."""
    s = srs.Substrate()
    n = s.add_node("X", {
        "a": [1, 2, 3], "a2": [1, 2, 3], "b": (1, 2, 3),
        "c": [1, 2], "nest": [1, [2, 3]], "nest2": [1, (2, 3)]})

    def attr(k):
        return {"type": "Attr",
                "node": _lit({"__nid__": n.value if hasattr(n, "value") else n}),
                "key": k}

    def eq(k1, k2):
        return bool(s._inner.evaluate(
            {"type": "Eq", "a": attr(k1), "b": attr(k2)}, {}))

    assert eq("a", "a2") is True        # list  == equal list
    assert eq("b", "b") is True         # tuple == itself
    assert eq("a", "b") is False        # THE FIX: list != tuple
    assert eq("a", "c") is False        # different elements still differ
    assert eq("nest", "nest") is True   # nested list, same
    assert eq("nest", "nest2") is False # ... and the collapse is not nested-only


def test_a_set_of_lists_does_not_collapse_and_sorting_lists_still_orders():
    """`cmp_value` drives BOTH `make_set` dedup and `sorted`.  Without a
    (List, List) arm two distinct lists compare Equal via the tag
    fallback: the set silently collapses to one element and `sorted`
    becomes a no-op.  Both are asserted here because both are silent."""
    assert _run_source("def f(a):\n    return sorted(a)\n",
                       {"a": [[3], [1], [2]]}) == [[1], [2], [3]]
    s = srs.Substrate()
    n = s.add_node("X", {"xs": [[1], [2], [1]]})
    item = [{"type": "IndexAt",
             "seq": {"type": "Attr",
                     "node": _lit({"__nid__": n.value if hasattr(n, "value") else n}),
                     "key": "xs"},
             "index": _lit(i)} for i in (0, 1, 2)]
    setof = {"type": "SetT", "items": item}
    # Counted INSIDE the substrate: three list elements, two distinct.  If
    # `cmp_value` lacked its (List, List) arm this would read 1.
    assert s._inner.evaluate({"type": "Count", "source": setof}, {}) == 2


def test_a_set_of_lists_cannot_be_handed_back_to_python_and_says_so_LOUDLY():
    """A NEW, DELIBERATE failure mode, recorded rather than hidden.

    The substrate holds a `Set` of `List`s perfectly well (above).  But
    `value_to_py` builds a real Python `set`, and a Python list is
    UNHASHABLE — so reading such a set out now raises, where before it
    silently produced a set of TUPLES.  That silence WAS the collapse.
    CPython raises on `{[1, 2]}` too, so this is the faithful behaviour;
    it is pinned here because it is a behaviour change a caller can hit."""
    s = srs.Substrate()
    n = s.add_node("X", {"xs": [[1], [2]]})
    setof = {"type": "SetT", "items": [
        {"type": "IndexAt",
         "seq": {"type": "Attr",
                 "node": _lit({"__nid__": n.value if hasattr(n, "value") else n}),
                 "key": "xs"},
         "index": _lit(i)} for i in (0, 1)]}
    with pytest.raises(TypeError):
        s._inner.evaluate(setof, {})
    # ... and the TUPLE case, which is what every pre-existing caller has,
    # is untouched.
    n2 = s.add_node("Y", {"xs": [(1,), (2,)]})
    setof2 = {"type": "SetT", "items": [
        {"type": "IndexAt",
         "seq": {"type": "Attr",
                 "node": _lit({"__nid__": n2.value if hasattr(n2, "value") else n2}),
                 "key": "xs"},
         "index": _lit(i)} for i in (0, 1)]}
    assert s._inner.evaluate(setof2, {}) == {(1,), (2,)}


def test_a_list_attr_survives_a_graph_checkpoint_round_trip():
    """`persist.rs` gained a `__list__` tag symmetric with `__tuple__`.
    Without it the distinction would be destroyed by every save/load —
    which is exactly how `Set`/`FrozenSet` justify being two tags."""
    s = srs.Substrate()
    n = s.add_node("X", {"lst": [1, [2, 3]], "tup": (1, (2, 3))})
    blob = s.graph_to_dict()
    s2 = srs.Substrate()
    s2.graph_from_dict(blob)
    at = s2.node(n)["attrs"]
    assert isinstance(at["lst"], list) and at["lst"] == [1, [2, 3]]
    assert isinstance(at["tup"], tuple) and at["tup"] == (1, (2, 3))


# ---------------------------------------------------------------------------
# 2) ProgEval type-faithfulness — the half without which nothing moves
# ---------------------------------------------------------------------------
TYPE_CASES = [
    ("listcomp",        "def f(a):\n    return [x for x in a]\n", {"a": [10, 20, 30]}),
    ("tuple_literal",   "def f(a):\n    return (a[0], a[1])\n", {"a": [10, 20, 30]}),
    ("list_literal",    "def f(a):\n    return [a[0], a[1]]\n", {"a": [10, 20, 30]}),
    ("sorted",          "def f(a):\n    return sorted(a)\n", {"a": [3, 1, 2]}),
    ("list_call",       "def f(a):\n    return list(a)\n", {"a": [1, 2]}),
    ("tuple_call",      "def f(a):\n    return tuple(a)\n", {"a": [1, 2]}),
    ("slice_of_list",   "def f(a):\n    return a[1:]\n", {"a": [1, 2, 3]}),
    ("slice_of_tuple",  "def f(a):\n    return a[1:]\n", {"a": (1, 2, 3)}),
    ("split",           "def f(a):\n    return a.split(' ')\n", {"a": "x y z"}),
    ("isinstance_list", "def f(a):\n    return isinstance(a, list)\n", {"a": [1]}),
    ("isinstance_tuple_on_a_list", "def f(a):\n    return isinstance(a, tuple)\n", {"a": [1]}),
    ("isinstance_tuple", "def f(a):\n    return isinstance(a, tuple)\n", {"a": (1,)}),
    ("isinstance_list_on_a_tuple", "def f(a):\n    return isinstance(a, list)\n", {"a": (1,)}),
    ("str_of_a_tuple",  "def f(a):\n    return str((1, 2))\n", {"a": [0]}),
    ("str_of_a_list",   "def f(a):\n    return str([1, 2])\n", {"a": [0]}),
    ("list_of_zip",     "def f(a):\n    return list(zip(a, a))\n", {"a": [1, 2]}),
    ("reversing_slice", "def f(a):\n    return a[::-1]\n", {"a": [1, 2, 3]}),
    ("identity_list",   "def f(a):\n    return a\n", {"a": [1, 2]}),
    ("identity_tuple",  "def f(a):\n    return a\n", {"a": (1, 2)}),
    ("aug_concat",      "def f(a):\n    b = []\n    for x in a:\n        b += [x]\n    return b\n", {"a": [1, 2]}),
    ("tuple_around_a_list", "def f(a):\n    return (len(a), a)\n", {"a": [1, 2]}),
    ("item_assignment", "def f(a):\n    a[0] = 9\n    return a\n", {"a": [1, 2]}),
]


@pytest.mark.parametrize("name,src,env", TYPE_CASES, ids=[c[0] for c in TYPE_CASES])
def test_prog_eval_agrees_with_cpython_on_the_container_TYPE(name, src, env):
    got = _run_source(src, env)
    ref = _ref(src, env)
    assert type(got) is type(ref), f"{name}: {type(got).__name__} vs {type(ref).__name__}"
    assert got == ref


def test_the_dsl_list_comprehension_terms_produce_lists():
    """`MapList`/`FilterList` exist, by their own doc comments, to be
    "the faithful target for a Python LIST comprehension".  They are what
    `SynthEnumerate` emits for `op:MapList` / `op:FilterList`, so if they
    return tuples the row verdict rejects every correct list answer the
    enumerator can propose.  In CPython `[f(x) for x in t]` is a LIST even
    when `t` is a tuple — asserted here with a TUPLE source."""
    s = srs.Substrate()
    n = s.add_node("X", {"xs": (1, 2, 3, 4)})
    src = {"type": "Attr",
           "node": _lit({"__nid__": n.value if hasattr(n, "value") else n}),
           "key": "xs"}
    mapped = s._inner.evaluate(
        {"type": "MapList", "source": src, "var_name": "it",
         "value": {"type": "Plus", "items": [{"type": "Var", "name": "it"}, _lit(1)]}}, {})
    assert isinstance(mapped, list) and mapped == [2, 3, 4, 5]
    filtered = s._inner.evaluate(
        {"type": "FilterList", "source": src, "var_name": "it",
         "predicate": {"type": "Gt", "a": {"type": "Var", "name": "it"}, "b": _lit(2)}}, {})
    assert isinstance(filtered, list) and filtered == [3, 4]
    # `Vec`/`op:TupleOf` is a TUPLE and must stay one.
    vec = s._inner.evaluate({"type": "Vec", "items": [_lit(1), _lit(2)]}, {})
    assert isinstance(vec, tuple) and vec == (1, 2)


def test_a_read_modify_write_helper_PRESERVES_the_container_kind():
    """THE BUG THIS RUNG ACTUALLY SHIPPED, AND THEN FOUND.

    `shape_decode::set_coord` — the single funnel every geometry generator
    goes through (translate / rotate / reflect / scale / modular) —
    destructured `Tuple | List` and always emitted a `Tuple`. So a
    generator applied to LIST-shaped observed relations produced TUPLE
    relations, `frames_equal` never matched, `BlinkBridge` reported
    `freeze` instead of the inferred generator, and **9 vision gates went
    red** (`test_blink_bridge_migrated`, `test_illusion_render_migrated`)
    while the whole 257-task MBPP battery stayed clean.

    The lesson, pinned: adding a variant is safe at every site that only
    READS a sequence; the dangerous sites are the ones that COPY it. This
    exercises the end-to-end effect (a translate generator inferred over
    list-shaped cells) rather than the helper, because the helper is
    private and the effect is what broke."""
    from substrate.boot_core import boot_core
    from substrate.seed_loader import manifest_for
    import domains.reflective_faculty as rf
    import domains.seed_registry  # noqa: F401 — registers the manifests

    DOT = [["cell", 0, 0, "red"]]
    DT = ["label", "coord:r", "coord:c", "colour"]

    def moving(dv, n):
        out, cur = [DOT], DOT
        for _ in range(n - 1):
            cur = [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cur]
            out.append(cur)
        return out

    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("blink_bridge"), ag)
    s.set_attr(ag, "blink_bridge_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(DOT),
                                  "kind": "faculty", "faculty": "base_L",
                                  "dim_types": DT})
    t = moving((0, 2), 6)
    o = s.add_node("Observation", {"frames": [t[0], t[1], [], [], [], t[5]],
                                   "dim_types": DT, "status": "blink_seq",
                                   "key": ["blink"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    # The generator must be INFERRED, not fallen back to `freeze` — the
    # symptom of the retyping bug was exactly `freeze` here.
    assert at.get("bridge_kind") == "translate", at.get("bridge_kind")
    bridged = at.get("bridged")
    assert bridged, "the bridge must confabulate the gap"
    assert sorted(tuple(x) for x in bridged[0]) == \
        sorted(tuple(x) for x in t[2]), (bridged[0], t[2])


# ---------------------------------------------------------------------------
# 3) the row verdict — driven to BOTH verdicts on the SAME shape
# ---------------------------------------------------------------------------
def _boot():
    import mbpp_arc3_battery as arc3b
    return arc3b.boot_full_r3()


def _drive_row_verdict(ir, rows):
    """Ingest a spec, write `ir` as the candidate, evaluate, run rules,
    and read the row's own verdict back.  The DECISION is the seed rule
    `ps_row_pass` / `ps_row_fail` (`Eq(got, expected)`), untouched by this
    rung; only the mechanical record of `got` changed."""
    s, ag = _boot()
    m = psy.ingest_spec(s, ag, "write a function f", rows)
    s._inner.run_rules(400000)
    g = s.in_neighbours(m, "about_message")[0]
    s.set_attr(g, "ps_ir", json.dumps(ir))
    s.set_attr(g, "ps_ir_built", s.node(g)["attrs"].get("ps_attempts"))
    assert psy.eval_and_record(s, ag, g) is True
    s._inner.run_rules(400000)
    row = s.neighbours(m, "has_example")[0]
    return s.node(row)["attrs"]


_RET_LIST = {"type": "ProgSeq", "stmts": [
    {"type": "ProgDefFnParam", "name": "a", "default": None},
    {"type": "ProgDefFnParam", "name": "b", "default": None},
    {"type": "ProgReturn", "value": {
        "type": "ProgContainerLit", "kind": "list",
        "items": [{"type": "Var", "name": "a"}, {"type": "Var", "name": "b"}]}}]}

_RET_TUPLE = json.loads(json.dumps(_RET_LIST).replace('"kind": "list"', '"kind": "tuple"'))


def test_the_row_verdict_ACCEPTS_a_list_answer_to_a_list_question():
    at = _drive_row_verdict(_RET_LIST,
                            [{"inputs": {"a": 1, "b": 2}, "expected": [1, 2]}])
    assert at["got"] == [1, 2] and isinstance(at["got"], list)
    assert at["ps_verdict"] == "pass"


def test_the_row_verdict_REJECTS_a_tuple_answer_to_a_list_question():
    """HV1, live.  This is the 12-false-accepts case: same elements,
    wrong container.  Under the old value layer this row read `pass`."""
    at = _drive_row_verdict(_RET_TUPLE,
                            [{"inputs": {"a": 1, "b": 2}, "expected": [1, 2]}])
    assert at["got"] == (1, 2) and isinstance(at["got"], tuple)
    assert at["ps_verdict"] == "fail"


def test_the_row_verdict_ACCEPTS_a_tuple_answer_to_a_tuple_question():
    """The other direction of the same gate — a verdict that rejected
    everything non-scalar would pass the test above and fail this one."""
    at = _drive_row_verdict(_RET_TUPLE,
                            [{"inputs": {"a": 1, "b": 2}, "expected": (1, 2)}])
    assert at["ps_verdict"] == "pass"


def test_a_non_scalar_got_is_recorded_at_all():
    """The block was never the RULE — it was `eval_and_record`'s
    scalar-only cast, which stored `None` for every sequence result, so
    `Eq(got, expected)` could not agree however correct the program was.
    Pinned so the cast cannot come back."""
    at = _drive_row_verdict(_RET_LIST,
                            [{"inputs": {"a": 1, "b": 2}, "expected": [1, 2]}])
    assert at["got"] is not None


def test_hv4_the_foldup_lane_records_a_non_scalar_too():
    """HV4.  The descent fold-up lane (`fu_got`, read by
    `ps_foldup_accept`/`ps_foldup_reject`) carried the IDENTICAL
    scalar-only cast and has NO `fu_cmp_ok` to fall back on.  A source
    audit, because the lane needs a full descent to reach dynamically and
    the claim being gated is precisely that the cast is gone from BOTH
    places."""
    import inspect
    src = inspect.getsource(psy)
    assert 'sub.set_attr(r, "fu_got", got)' in src
    assert 'isinstance(got, _SCALARS)' not in src.split("def _row_cmp_ok")[0], (
        "a scalar-only cast survives on one of the two verdict lanes")


# ---------------------------------------------------------------------------
# 4) what this rung did NOT fix — pinned so it cannot be quietly inherited
# ---------------------------------------------------------------------------
def test_out_of_scope_defects_are_still_present_and_named():
    """`Eq(0.0, False)` (A3) is REGISTERED as a defect this rung must not
    absorb. If it is fixed later, this test fails and the write-up's "what
    remains unfixed" section has to be updated with it — which is the
    point.

    `sorted`-on-strings (prereg §4 here) is UPDATED
    (CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md): `sorted()`'s "extern"
    (`prog_eval.rs`) was named a REPORTED-ORDER site and switched to the
    interner-aware `cmp_value_lex` comparator — real byte-lexicographic
    order regardless of process-history intern order. `cmp_value`'s own
    `(Str, Str)` arm is UNCHANGED (still Sym-id order — canonicalisation
    call sites, e.g. `Dict`/`Set` construction, keep using it unmodified),
    so this is a narrower, scoped fix, not the rejected project-wide
    interner-threading refactor. See PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md
    §9.3 for the update note."""
    s = srs.Substrate()
    # `Eq(0.0, False)`: False in the substrate, True in Python. Named, not bundled.
    assert bool(s._inner.evaluate({"type": "Eq", "a": _lit(0.0), "b": _lit(False)}, {})) is False
    assert (0.0 == False) is True  # noqa: E712 — the divergence IS the assertion
    # `sorted()` is now real lexicographic order, independent of which
    # substrate interned "pear"/"apple"/"fig" in which order.
    src = "def f(a):\n    return sorted(a)\n"

    def sorted_on(words, prime):
        sub = srs.Substrate()
        for w in prime:
            sub.add_node("Prime", {"v": w})
        emitted = emit_prog_ir(src)
        return sub._inner.evaluate(
            {"type": "ProgEval", "prog": emitted["ir"],
             "env": {"type": "Var", "name": "e"}, "oracles": _oracles(),
             "fuel": psy._FUEL, "field": ""}, {"e": {"a": list(words)}}).get("result")

    words = ["pear", "apple", "fig"]
    fwd = sorted_on(words, ["apple", "fig", "pear"])
    rev = sorted_on(words, ["pear", "fig", "apple"])
    assert fwd == rev == sorted(words), (
        "sorted-on-strings should now be lexicographic regardless of intern "
        "order; got fwd=%r rev=%r" % (fwd, rev))
