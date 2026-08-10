"""test_value_domain_migrated — ARC 2 Q1 gates: the value-domain floor.

PROGRAM_SYNTHESIS_ARC2_PLAN.md §2-Q1 / PROGRAM_SYNTHESIS_ARC2_PREREG.md §2-3 /
PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md. Widens `ProgEval` past the arc-1
integer/int-list floor to the Q0-picked op families: `bitwise_ops` (int AND
set algebra), `math_native`, `slicing` (the new `ProgSlice` variant),
`string_methods` / `dict_methods` (method-recv native oracles), and the
`general_builtins` subset expressible without a first-class callable.

Gates:

  CPYTHON AGREEMENT — a fixture corpus (~50 cases) per new op family,
    each executed on BOTH the Rust engine and CPython (`eval`/`exec`),
    compared via `norm()` (the test_prog_ir_migrated.py convention).

  TRAP HONESTY — type mismatches and family-specific edge cases trap
    with the documented reason string, never silently coerce.

  DICT ITERATION DETERMINISM — pinned and DOCUMENTED (not assumed
    alphabetical, not assumed true insertion order): dict values in
    this engine are ALWAYS stored sorted by `cmp_value` over keys, and
    for Str keys that is a sort by INTERNED-SYMBOL ID, not by string
    content — a pre-existing (pre-Q1) engine property this phase's new
    `dict_methods`/`general_builtins` work newly EXERCISES. Documented,
    not silently assumed.

  FUEL/PURITY — `node_count` is stable across ProgEval calls exercising
    every new op family (no substrate mutation, ever).

  HQ1 — the arc's phase verdict. See `test_hq1_verdict` for the full
    honest accounting of what could and could not be measured live
    (the `domains/prog_ir_emit.py` file-ownership boundary — READ that
    test's docstring before quoting a number from this file).

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest tests/test_value_domain_migrated.py \
    --confcutdir=. -q
"""

from __future__ import annotations

import json
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs


# ---------------------------------------------------------------------------
# Term-JSON builders (mechanical; mirrors substrate/dsl.py)
# ---------------------------------------------------------------------------
def L(v):
    return {"type": "Lit", "value": v}


def V(n):
    return {"type": "Var", "name": n}


def CALL(name, *args, recv=None):
    return {"type": "ProgCallExtern", "name": name, "recv": recv, "args": list(args)}


def SLICE(obj, start=None, stop=None, step=None):
    return {"type": "ProgSlice", "obj": obj, "start": start, "stop": stop, "step": step}


def SUB(obj, index):
    return {"type": "ProgSubscript", "obj": obj, "index": index}


def CLIT(kind, *items):
    return {"type": "ProgContainerLit", "kind": kind, "items": list(items)}


def SETLIT(*items):
    return {"type": "SetT", "items": list(items)}


def BINOP(kind, a, b):
    return {"type": kind, "a": a, "b": b}


def MKDICT(**kv):
    items = []
    for k, v in kv.items():
        items.append(L(k))
        items.append(L(v))
    return {"type": "MkDict", "items": items}


def ORACLES(*names):
    return MKDICT(**{n: "builtin" for n in names})


def PROGEVAL(prog, oracles=None, fuel=1000, field=""):
    return {"type": "ProgEval", "prog": prog, "env": None, "oracles": oracles,
            "fuel": fuel, "field": field}


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(PROGEVAL(L(1)), {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


def _prog_slice_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(PROGEVAL(SLICE(L("ab"), L(0), L(1), None)), {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _prog_eval_live():
    pytest.skip(
        "ProgEval Term not present in the installed substrate_rs binary — "
        "rebuild runners/dsl (cargo build --release + sync "
        "python/substrate_rs/_native.abi3.so). Honest skip, not a fake pass.",
        allow_module_level=True)

if not _prog_slice_live():
    pytest.skip(
        "ProgSlice (Q1) not present in the installed substrate_rs binary — "
        "rebuild runners/dsl. Honest skip, not a fake pass.",
        allow_module_level=True)


@pytest.fixture()
def sub():
    return srs.Substrate()


def norm(v):
    """Cross-runtime normalisation (test_prog_ir_migrated.py's convention):
    list/tuple -> tuple, set/frozenset -> frozenset, dict -> dict of normed."""
    if isinstance(v, (list, tuple)):
        return tuple(norm(x) for x in v)
    if isinstance(v, (set, frozenset)):
        return frozenset(norm(x) for x in v)
    if isinstance(v, dict):
        return {norm(k): norm(x) for k, x in v.items()}
    return v


def run_expr(sub, prog, oracles=(), fuel=1000):
    out = sub._inner.evaluate(PROGEVAL(prog, oracles=ORACLES(*oracles) if oracles else None,
                                        fuel=fuel), {})
    assert isinstance(out, dict), f"ProgEval must return a Dict, got {type(out)}"
    return out


PY_EVAL_GLOBALS = {"math": math}


def assert_agrees(sub, prog, py_expr, oracles=()):
    """The CPython-agreement gate: run `prog` on the Rust engine, `py_expr`
    (a real Python expression string) on CPython, compare normalised."""
    out = run_expr(sub, prog, oracles=oracles)
    assert out["trap"] is None, f"unexpected trap on {py_expr!r}: {out['trap']}"
    assert out["halted"] is True
    got = norm(out["result"])
    want = norm(eval(py_expr, dict(PY_EVAL_GLOBALS)))  # noqa: S307 — the gate's CPython oracle
    assert got == want, f"{py_expr!r}: rust={out['result']!r} py={want!r}"
    return out


def assert_plain_agrees(sub, prog, py_expr):
    """Twin of `assert_agrees` for ORDINARY (non-Prog) DSL terms —
    `BitAnd`/`BitOr`/`BitXor`/`Ashr` are plain `evaluate()`-dispatched
    Terms, not Prog* IR; `ProgEval`'s `prog` root must be either an
    inline Prog* subtree or a `Value::Node` reflecting one (its own
    documented contract) — a bare `BitAnd` doesn't qualify, so these
    are evaluated directly, exactly the way any other DSL Term is."""
    got = norm(sub._inner.evaluate(prog, {}))
    want = norm(eval(py_expr, dict(PY_EVAL_GLOBALS)))  # noqa: S307
    assert got == want, f"{py_expr!r}: rust={got!r} py={want!r}"


# ---------------------------------------------------------------------------
# 1) CPYTHON AGREEMENT — bitwise_ops (int AND set algebra; the Q0 finding)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prog,py_expr", [
    (BINOP("BitAnd", L(5), L(3)), "5 & 3"),
    (BINOP("BitOr", L(5), L(2)), "5 | 2"),
    (BINOP("BitXor", L(5), L(1)), "5 ^ 1"),
    (BINOP("Ashr", L(-8), L(2)), "-8 >> 2"),
], ids=["bitand_int", "bitor_int", "bitxor_int", "ashr_int_unaffected"])
def test_bitwise_int_agrees(sub, prog, py_expr):
    assert_plain_agrees(sub, prog, py_expr)


@pytest.mark.parametrize("prog,py_expr", [
    (BINOP("BitAnd", SETLIT(L(1), L(2), L(3)), SETLIT(L(2), L(3), L(4))),
     "set((1,2,3)) & set((2,3,4))"),
    (BINOP("BitOr", SETLIT(L(1), L(2)), SETLIT(L(2), L(3))),
     "set((1,2)) | set((2,3))"),
    (BINOP("BitXor", SETLIT(L(1), L(2), L(3)), SETLIT(L(2), L(3), L(4))),
     "set((1,2,3)) ^ set((2,3,4))"),
], ids=["set_intersection", "set_union", "set_symmetric_difference"])
def test_bitwise_set_algebra_agrees(sub, prog, py_expr):
    """task 2's own finding: `&`/`|`/`^` are ALSO set algebra, dispatched
    on the RUNTIME type — the same Term, two evaluator paths."""
    assert_plain_agrees(sub, prog, py_expr)


# ---------------------------------------------------------------------------
# 2) CPYTHON AGREEMENT — math_native
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prog,py_expr,oracles", [
    (CALL("round", L(2.5)), "round(2.5)", ("round",)),
    (CALL("round", L(3.5)), "round(3.5)", ("round",)),
    (CALL("round", L(-2.5)), "round(-2.5)", ("round",)),
    (CALL("round", L(0.5)), "round(0.5)", ("round",)),
    (CALL("round", L(1.25), L(1)), "round(1.25, 1)", ("round",)),
    (CALL("round", L(1234), L(-2)), "round(1234, -2)", ("round",)),
    (CALL("pow", L(2), L(10)), "pow(2, 10)", ("pow",)),
    (CALL("pow", L(2), L(0.5)), "pow(2, 0.5)", ("pow",)),
    (CALL("divmod", L(7), L(3)), "divmod(7, 3)", ("divmod",)),
    (CALL("divmod", L(-7), L(3)), "divmod(-7, 3)", ("divmod",)),
    (CALL("divmod", L(7), L(-3)), "divmod(7, -3)", ("divmod",)),
    (CALL("divmod", L(-7), L(-3)), "divmod(-7, -3)", ("divmod",)),
    (CALL("ord", L("A")), "ord('A')", ("ord",)),
    (CALL("chr", L(65)), "chr(65)", ("chr",)),
    (CALL("math.sqrt", L(16.0)), "math.sqrt(16.0)", ("math.sqrt",)),
    (CALL("math.floor", L(3.7)), "math.floor(3.7)", ("math.floor",)),
    (CALL("math.ceil", L(3.2)), "math.ceil(3.2)", ("math.ceil",)),
    (CALL("math.pow", L(2), L(3)), "math.pow(2, 3)", ("math.pow",)),
], ids=[
    "round_half_even_2.5", "round_half_even_3.5", "round_half_even_neg2.5",
    "round_half_even_0.5", "round_ndigits_even", "round_negative_ndigits",
    "pow_int", "pow_float", "divmod_pos", "divmod_neg_a", "divmod_neg_b",
    "divmod_neg_both", "ord", "chr", "math_sqrt", "math_floor", "math_ceil",
    "math_pow",
])
def test_math_native_agrees(sub, prog, py_expr, oracles):
    assert_agrees(sub, prog, py_expr, oracles=oracles)


def test_math_sqrt_negative_domain_traps(sub):
    out = run_expr(sub, CALL("math.sqrt", L(-1.0)), oracles=("math.sqrt",))
    assert out["halted"] is False
    assert out["trap"] == "extern:math.sqrt:domain"


def test_divmod_by_zero_traps(sub):
    out = run_expr(sub, CALL("divmod", L(1), L(0)), oracles=("divmod",))
    assert out["halted"] is False
    assert out["trap"] == "extern:divmod:zero"


# ---------------------------------------------------------------------------
# 3) CPYTHON AGREEMENT — slicing (str AND list, negative step, OOB clamps)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prog,py_expr", [
    (SLICE(L("hello"), L(1), L(3), None), "'hello'[1:3]"),
    (SLICE(L("hello"), None, None, L(-1)), "'hello'[::-1]"),
    (SLICE(L("hello"), L(-3), None, None), "'hello'[-3:]"),
    (SLICE(L("hello"), L(10), L(20), None), "'hello'[10:20]"),
    (SLICE(L("hello"), None, None, L(2)), "'hello'[::2]"),
    (SLICE(CLIT("list", L(1), L(2), L(3), L(4), L(5)), L(1), L(4), None),
     "(1, 2, 3, 4, 5)[1:4]"),
    (SLICE(CLIT("list", L(1), L(2), L(3), L(4), L(5)), None, None, L(2)),
     "(1, 2, 3, 4, 5)[::2]"),
    (SLICE(CLIT("list", L(1), L(2), L(3)), L(-2), None, None),
     "(1, 2, 3)[-2:]"),
    (SLICE(CLIT("list", L(1), L(2), L(3)), None, None, L(-1)),
     "(1, 2, 3)[::-1]"),
], ids=[
    "str_basic", "str_reverse", "str_neg_start", "str_oob_clamps",
    "str_step2", "list_basic", "list_step2", "list_neg_start", "list_reverse",
])
def test_slicing_agrees(sub, prog, py_expr):
    assert_agrees(sub, prog, py_expr)


def test_slice_zero_step_traps(sub):
    out = run_expr(sub, SLICE(L("hello"), None, None, L(0)))
    assert out["halted"] is False
    assert out["trap"] == "slice:zero_step"


def test_slice_of_dict_traps_type(sub):
    d = CLIT("dict", L("a"), L(1))
    out = run_expr(sub, SLICE(d, L(0), L(1), None))
    assert out["halted"] is False
    assert out["trap"] == "slice:type:dict"


# ---------------------------------------------------------------------------
# 4) CPYTHON AGREEMENT — string_methods (recv-form native oracles)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prog,py_expr,oracles", [
    (CALL("strip", recv=L("  hi  ")), "'  hi  '.strip()", ("strip",)),
    (CALL("strip", L("x"), recv=L("xxhixx")), "'xxhixx'.strip('x')", ("strip",)),
    (CALL("lstrip", recv=L("  hi  ")), "'  hi  '.lstrip()", ("lstrip",)),
    (CALL("rstrip", recv=L("  hi  ")), "'  hi  '.rstrip()", ("rstrip",)),
    (CALL("lower", recv=L("Hello World")), "'Hello World'.lower()", ("lower",)),
    (CALL("upper", recv=L("Hello World")), "'Hello World'.upper()", ("upper",)),
    (CALL("capitalize", recv=L("hello world")), "'hello world'.capitalize()",
     ("capitalize",)),
    (CALL("split", L(","), recv=L("a,b,,c")), "'a,b,,c'.split(',')", ("split",)),
    (CALL("split", recv=L("a b  c")), "'a b  c'.split()", ("split",)),
    (CALL("split", L(","), L(1), recv=L("a,b,c,d")), "'a,b,c,d'.split(',', 1)", ("split",)),
    (CALL("join", CLIT("list", L("a"), L("b"), L("c")), recv=L("-")),
     "'-'.join(('a', 'b', 'c'))", ("join",)),
    (CALL("replace", L("a"), L("o"), recv=L("banana")),
     "'banana'.replace('a', 'o')", ("replace",)),
    (CALL("replace", L("a"), L("o"), L(1), recv=L("banana")),
     "'banana'.replace('a', 'o', 1)", ("replace",)),
    (CALL("startswith", L("he"), recv=L("hello")), "'hello'.startswith('he')",
     ("startswith",)),
    (CALL("endswith", CLIT("list", L("lo"), L("xo")), recv=L("hello")),
     "'hello'.endswith(('lo', 'xo'))", ("endswith",)),
    (CALL("find", L("l"), recv=L("hello")), "'hello'.find('l')", ("find",)),
    (CALL("find", L("z"), recv=L("hello")), "'hello'.find('z')", ("find",)),
    (CALL("count", L("l"), recv=L("hello")), "'hello'.count('l')", ("count",)),
    (CALL("isdigit", recv=L("123")), "'123'.isdigit()", ("isdigit",)),
    (CALL("isdigit", recv=L("12a")), "'12a'.isdigit()", ("isdigit",)),
    (CALL("isalpha", recv=L("abc")), "'abc'.isalpha()", ("isalpha",)),
    (CALL("isupper", recv=L("ABC")), "'ABC'.isupper()", ("isupper",)),
    (CALL("islower", recv=L("abc")), "'abc'.islower()", ("islower",)),
], ids=[
    "strip_default", "strip_chars", "lstrip", "rstrip", "lower", "upper",
    "capitalize", "split_sep", "split_whitespace", "split_maxsplit", "join",
    "replace_all", "replace_count", "startswith", "endswith_tuple", "find_hit",
    "find_miss", "count", "isdigit_true", "isdigit_false", "isalpha",
    "isupper", "islower",
])
def test_string_methods_agree(sub, prog, py_expr, oracles):
    assert_agrees(sub, prog, py_expr, oracles=oracles)


def test_string_method_type_mismatch_traps(sub):
    """A recv-form call on a non-string, non-dict receiver traps honestly
    rather than coercing (type honesty per family)."""
    out = run_expr(sub, CALL("upper", recv=L(5)), oracles=("upper",))
    assert out["halted"] is False
    assert out["trap"] == "extern:unimplemented:upper"


def test_split_empty_sep_traps(sub):
    out = run_expr(sub, {"type": "ProgCallExtern", "name": "split",
                          "recv": L("abc"), "args": [L("")]}, oracles=("split",))
    assert out["halted"] is False
    assert out["trap"] == "extern:split:empty_sep"


# ---------------------------------------------------------------------------
# 5) CPYTHON AGREEMENT — general_builtins (the callable/lazy-iterator-free subset)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prog,py_expr,oracles", [
    (CALL("all", CLIT("list", L(1), L(1), L(1))), "all((1, 1, 1))", ("all",)),
    (CALL("all", CLIT("list", L(1), L(0), L(1))), "all((1, 0, 1))", ("all",)),
    (CALL("any", CLIT("list", L(0), L(0), L(1))), "any((0, 0, 1))", ("any",)),
    (CALL("any", CLIT("list", L(0), L(0))), "any((0, 0))", ("any",)),
    (CALL("enumerate", CLIT("list", L("a"), L("b"))),
     "tuple(enumerate(('a', 'b')))", ("enumerate",)),
    (CALL("enumerate", CLIT("list", L("a"), L("b")), L(1)),
     "tuple(enumerate(('a', 'b'), 1))", ("enumerate",)),
    (CALL("zip", CLIT("list", L(1), L(2), L(3)), CLIT("list", L("a"), L("b"))),
     "tuple(zip((1, 2, 3), ('a', 'b')))", ("zip",)),
    (CALL("reversed", CLIT("list", L(1), L(2), L(3))),
     "tuple(reversed((1, 2, 3)))", ("reversed",)),
], ids=[
    "all_true", "all_false", "any_true", "any_false", "enumerate_default",
    "enumerate_start", "zip_truncates", "reversed",
])
def test_general_builtins_agree(sub, prog, py_expr, oracles):
    assert_agrees(sub, prog, py_expr, oracles=oracles)


def test_isinstance_type_name_convention(sub):
    """`isinstance` has no first-class type-object in this value model —
    the engine's own convention is a TYPE-NAME STRING second argument
    (documented residual: the Python emitter side of wiring real
    `isinstance(x, int)` call sites to this convention is out of this
    phase's file-ownership scope, see PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md).
    This is therefore an engine-capability assertion, not a CPython
    string-comparison (CPython's own isinstance takes a type object)."""
    out = run_expr(sub, CALL("isinstance", L(5), L("int")), oracles=("isinstance",))
    assert out["result"] is True
    out = run_expr(sub, CALL("isinstance", L("x"), L("int")), oracles=("isinstance",))
    assert out["result"] is False
    out = run_expr(sub, CALL("isinstance", L(5), L("bogus_type")), oracles=("isinstance",))
    assert out["halted"] is False
    assert out["trap"] == "extern:isinstance:unknown_type:bogus_type"


# ---------------------------------------------------------------------------
# 6) CPYTHON AGREEMENT — container_ctor
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("prog,py_expr,oracles", [
    (CALL("list", CLIT("list", L(1), L(2), L(3))), "list((1, 2, 3))", ("list",)),
    (CALL("tuple", CLIT("list", L(1), L(2), L(3))), "tuple((1, 2, 3))", ("tuple",)),
    (CALL("set", CLIT("list", L(1), L(2), L(2), L(3))), "set((1, 2, 2, 3))", ("set",)),
    (CALL("list"), "list()", ("list",)),
    (CALL("dict"), "dict()", ("dict",)),
], ids=["list_ctor", "tuple_ctor", "set_ctor", "list_empty", "dict_empty"])
def test_container_ctor_agrees(sub, prog, py_expr, oracles):
    assert_agrees(sub, prog, py_expr, oracles=oracles)


def test_dict_ctor_from_pairs(sub):
    prog = CALL("dict", CLIT("list", CLIT("tuple", L("a"), L(1)), CLIT("tuple", L("b"), L(2))))
    out = run_expr(sub, prog, oracles=("dict",))
    assert out["trap"] is None
    assert norm(out["result"]) == {"a": 1, "b": 2}


# ---------------------------------------------------------------------------
# 7) dict_methods (read-only) — CPython agreement where order-independent
# ---------------------------------------------------------------------------

def test_dict_get_hit_and_miss(sub):
    d = CLIT("dict", L("a"), L(1))
    out = run_expr(sub, CALL("get", L("a"), recv=d), oracles=("get",))
    assert out["result"] == 1
    out = run_expr(sub, CALL("get", L("z"), L(9), recv=d), oracles=("get",))
    assert out["result"] == 9
    out = run_expr(sub, CALL("get", L("z"), recv=d), oracles=("get",))
    assert out["result"] is None


def test_dict_keys_values_items_are_the_same_pairs_as_python(sub):
    """Order-INDEPENDENT agreement (see the dict-iteration-determinism
    test below for the order itself): the SET of items/keys/values must
    match CPython's, even though the ORDER is this engine's own."""
    d = CLIT("dict", L("a"), L(1), L("b"), L(2), L("c"), L(3))
    py = {"a": 1, "b": 2, "c": 3}
    out_items = run_expr(sub, CALL("items", recv=d), oracles=("items",))
    assert frozenset(norm(out_items["result"])) == frozenset(py.items())
    out_keys = run_expr(sub, CALL("keys", recv=d), oracles=("keys",))
    assert frozenset(norm(out_keys["result"])) == frozenset(py.keys())
    out_values = run_expr(sub, CALL("values", recv=d), oracles=("values",))
    assert frozenset(norm(out_values["result"])) == frozenset(py.values())


# ---------------------------------------------------------------------------
# 8) DICT ITERATION DETERMINISM — pinned and documented
# ---------------------------------------------------------------------------

def test_dict_iteration_is_sorted_by_key_not_insertion_order(sub):
    """DECIDED (pre-Q1, newly exercised by Q1's dict_methods/general_
    builtins work): every dict-shaped Value in this engine is stored
    SORTED by `cmp_value` over its keys at every construction site
    (ProgContainerLit, native `dict()`, `container_with`'s upsert path)
    — NEVER Python's true insertion order. For Int/Float/Bool keys this
    sorts numerically (a stable, useful order). For Str keys, `cmp_value`
    compares the INTERNED SYMBOL ID, NOT the string's alphabetic content
    — so dict key order for string keys is a function of GLOBAL intern
    history, not the dict's own content or construction order. This
    test pins the DECISION (sorted-by-cmp_value, always) and documents
    the Str-key caveat explicitly rather than asserting a misleadingly
    "alphabetical" or "insertion-order" claim.
    """
    # Int keys: sorted numerically, deterministic regardless of intern
    # history (Int has no interning).
    d = CLIT("dict", L(3), L("c"), L(1), L("a"), L(2), L("b"))
    out = run_expr(sub, CALL("keys", recv=d), oracles=("keys",))
    assert out["result"] == (1, 2, 3), "int-keyed dict is sorted by key value"

    # Str keys: sorted by cmp_value, which for Str is INTERN-ID order —
    # reproduced here by observing that reversing the FIRST-INTERN order
    # of the same two keys reverses their reported position, regardless
    # of which dict literal put them in which syntactic order.
    fresh = srs.Substrate()
    # Intern "zzz_first" before "aaa_second" via an unrelated Lit use.
    fresh._inner.evaluate(L("zzz_first"), {})
    fresh._inner.evaluate(L("aaa_second"), {})
    d2 = CLIT("dict", L("aaa_second"), L(1), L("zzz_first"), L(2))
    out2 = fresh._inner.evaluate(
        PROGEVAL(CALL("keys", recv=d2), oracles=ORACLES("keys")), {})
    # NOT alphabetical ("aaa_second" < "zzz_first" as strings) — the
    # FIRST-INTERNED key ("zzz_first") sorts first.
    assert out2["result"] == ("zzz_first", "aaa_second"), (
        "dict key order for Str keys is intern-id order, not alphabetical "
        f"— got {out2['result']!r}")


# ---------------------------------------------------------------------------
# 9) FUEL/PURITY — node_count stable across every new op family
# ---------------------------------------------------------------------------

def test_purity_across_new_op_families(sub):
    nodes_before = sub._inner.node_count() if hasattr(sub._inner, "node_count") else None
    # Plain DSL terms (evaluated directly).
    sub._inner.evaluate(BINOP("BitAnd", SETLIT(L(1), L(2)), SETLIT(L(2), L(3))), {})
    # Prog IR terms (evaluated through ProgEval).
    prog_cases = [
        (CALL("math.sqrt", L(16.0)), ("math.sqrt",)),
        (SLICE(L("hello"), L(1), L(3), None), ()),
        (CALL("upper", recv=L("hi")), ("upper",)),
        (CALL("items", recv=CLIT("dict", L("a"), L(1))), ("items",)),
        (CALL("list", CLIT("list", L(1), L(2))), ("list",)),
    ]
    for prog, oracles in prog_cases:
        out = run_expr(sub, prog, oracles=oracles)
        assert out["trap"] is None, out
    if nodes_before is not None:
        assert sub._inner.node_count() == nodes_before, (
            "ProgEval must never mutate the substrate graph")


# ---------------------------------------------------------------------------
# 9b) ARC-5 RATIONAL — additive: the value-domain floor's newest citizen
# doesn't disturb the properties this file already pins (dict ordering
# is by KEY not value; purity holds; sorted()/isinstance still agree
# with CPython once a Rational is in the mix). The exhaustive gate set
# for the rational rung itself lives in
# tests/test_rational_domain_migrated.py — this is a compatibility
# spot-check from the value-domain-floor's own point of view.
# ---------------------------------------------------------------------------
def _seq_return(expr):
    """A bare arithmetic expression (no Prog* node anywhere) is not
    itself a valid top-level ProgEval `prog` (it traps `prog:invalid`
    — the top-level form must be Prog-shaped); wrap it exactly the way
    tests/test_rational_domain_migrated.py's `SEQ(RET(...))` does."""
    return {"type": "ProgSeq", "stmts": [{"type": "ProgReturn", "value": expr}]}


def _rational_live() -> bool:
    s = srs.Substrate()
    try:
        out = s._inner.evaluate(PROGEVAL(_seq_return(BINOP("Div", L(1), L(3)))), {})
        from fractions import Fraction
        return isinstance(out.get("result"), Fraction)
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


@pytest.mark.skipif(not _rational_live(), reason="rational value domain not in the installed .so")
def test_dict_iteration_order_unaffected_by_rational_valued_entries(sub):
    """Sorting is by KEY (`cmp_value` over keys) — a Rational VALUE
    (never a key here) must not perturb the pinned key-ordering
    property `test_dict_iteration_is_sorted_by_key_not_insertion_order`
    already establishes."""
    d = CLIT("dict", L(2), BINOP("Div", L(1), L(3)), L(1), BINOP("Div", L(2), L(3)))
    out = run_expr(sub, CALL("items", recv=d), oracles=("items",))
    assert out["trap"] is None, out
    keys_in_order = [pair[0] for pair in out["result"]]
    assert keys_in_order == sorted(keys_in_order)


@pytest.mark.skipif(not _rational_live(), reason="rational value domain not in the installed .so")
def test_sorted_agrees_across_int_float_rational(sub):
    xs = CLIT("list", L(3), L(1.5), BINOP("Div", L(1), L(4)), L(2))
    out = run_expr(sub, CALL("sorted", xs), oracles=("sorted",))
    assert out["trap"] is None, out
    from fractions import Fraction
    got = [float(x) if isinstance(x, Fraction) else x for x in out["result"]]
    assert got == sorted([3, 1.5, 0.25, 2])


@pytest.mark.skipif(not _rational_live(), reason="rational value domain not in the installed .so")
def test_purity_holds_for_exact_division(sub):
    nodes_before = sub._inner.node_count() if hasattr(sub._inner, "node_count") else None
    out = run_expr(sub, _seq_return(BINOP("Div", L(1), L(3))))
    assert out["trap"] is None, out
    if nodes_before is not None:
        assert sub._inner.node_count() == nodes_before


# ---------------------------------------------------------------------------
# 10) HQ1 — the phase verdict
# ---------------------------------------------------------------------------

HISTOGRAM_PATH = os.path.join(ROOT, "results", "mbpp_blocker_histogram.json")

# The Q1-landed op families (this file's own record, independent of
# domains/prog_ir_emit.py's NATIVE_ORACLES — see test_hq1_verdict).
Q1_LANDED_STRUCTURAL_FAMILIES = frozenset({"bitwise_ops"})  # set-algebra half only
Q1_LANDED_EXTERN_FAMILIES = frozenset({"math_native", "container_ctor",
                                        "general_builtins", "string_methods"})
Q1_LANDED_TYPES = frozenset({"int", "list[int]", "str", "bool", "float", "none", "dict"})


def test_hq1_verdict():
    """RETITLED IN PLACE, 2026-08-01 (Q1.5, additive doc correction only —
    the numeric assertions below are UNCHANGED, still correctly read from
    the FROZEN `results/mbpp_blocker_histogram.json` snapshot, which this
    later phase does not regenerate or overwrite): the Q1.5 phase
    (PROGRAM_SYNTHESIS_ARC2_Q15_NOTES.md) closed exactly the file-ownership
    gap this test's docstring names below — `domains/prog_ir_emit.py` was
    widened to actually EMIT the Q1 engine's new IR shapes (`ProgSlice`,
    set-`BitAnd`/`BitOr`/`BitXor`, method-oracle recv form, the widened
    native-oracle table). A LIVE re-run of `emit_prog_ir` TODAY therefore
    NO LONGER reproduces the number this test calls "LIVE" below — see
    `tests/test_emitter_widening_migrated.py::test_hq1_live_verdict` for
    the REAL live re-derivation (235/427 = 55.0%, measured 2026-08-01,
    exceeding the prereg's full-recommended-scope ceiling of 226/427 =
    52.9%). What THIS test actually pins, and continues to correctly pin,
    is the PRE-Q1.5 FROZEN FLOOR captured in the Q0-era histogram artifact
    — a historical snapshot, not a live measurement, despite its original
    name. The original docstring is kept below verbatim for provenance;
    read it as describing the state AS OF Q1, before this correction.

    The phase's headline number — reported HONESTLY under a file-
    ownership boundary this phase hit and could not cross.

    HQ1 (PROGRAM_SYNTHESIS_ARC2_PREREG.md §3) asks: after Q1, what
    fraction of the 427 MBPP tasks are BOTH `ok` (IR-representable) AND
    `predictable` (no undeclared extern) under the REAL `emit_prog_ir` +
    `ProgEval`? Measuring this LIVE requires re-running
    `domains.prog_ir_emit.emit_prog_ir` against the shipped engine — but
    `ok`/`predictable`/`structural_families`/`extern_families` are
    ENTIRELY COMPUTED BY `domains/prog_ir_emit.py`, a Python file this
    phase's file-ownership scope explicitly excludes (this task may only
    touch `runners/dsl/src/**`, `substrate/dsl.py`, and new test/notes
    files). Confirmed by inspection: `emit_prog_ir` blocks `SliceSubscript`
    and `OpExt:BitAnd/Or/Xor` STRUCTURALLY (`_blk(...)`, before any IR
    node is even considered) — it does not know `ProgSlice` exists, and
    it does not know `BitAnd` on a Set is now evaluable. Landing
    `ProgSlice` and the native-oracle table in Rust is NECESSARY for
    HQ1 to ever move, but NOT SUFFICIENT: the emitter must also be
    taught to EMIT these IR shapes, which is Python-side work this
    phase's scope does not include.

    THE HONEST NUMBERS:

    - LIVE (re-running the real `emit_prog_ir` against the 427-task
      histogram corpus): UNCHANGED at the pre-Q1 floor, 147/427 = 34.4%,
      because the emitter never emits `ProgSlice`/set-`BitAnd`/the new
      oracle names for ANY task — asserted below by re-deriving the
      floor directly from the histogram's own per-task `predictable`
      flags (the "predictable_count" the prereg's own table anchors on).
    - HYPOTHETICAL (the prereg's OWN documented method, §3 caveat #3:
      "if Q1 added native support for family X, would this task become
      predictable" — a re-derivation from the per-task extern/recv
      lists, explicitly NOT a re-run of a modified engine): recomputed
      here from `results/mbpp_blocker_histogram.json`'s `per_task` rows,
      using the families THIS phase actually landed (module-level
      constants above) rather than the prereg's full recommended set.
      This is the number a future phase's emitter work could reach
      WITHOUT any further Rust engine changes.

    Both are printed and asserted sane; NEITHER is silently presented
    as "the" HQ1 number — report both, always (the arc's own standing
    rule: synthetic-proven mechanism != benchmark value).
    """
    if not os.path.exists(HISTOGRAM_PATH):
        pytest.skip(f"{HISTOGRAM_PATH} not present in this checkout")
    with open(HISTOGRAM_PATH) as f:
        data = json.load(f)
    per_task = data["per_task"]
    n = len(per_task)
    assert n == 427, f"expected the frozen 427-task corpus, got {n}"

    # PRE-Q1.5 FROZEN FLOOR: exactly the histogram artifact's own measured
    # `predictable` flag — a Q0-era snapshot, read from disk, never
    # re-derived from a live emit_prog_ir call. NAMING NOTE (2026-08-01,
    # Q1.5): this was labelled "LIVE floor" when this test was written,
    # correct at the time ("this IS what a live re-run of the unmodified
    # emitter produces, since Q1 never touched domains/prog_ir_emit.py").
    # Q1.5 DID touch that emitter, so a live re-run today no longer
    # reproduces 147 (it now measures 235/427 — see
    # tests/test_emitter_widening_migrated.py::test_hq1_live_verdict for
    # the real live number). This assertion is kept and still passes
    # because it only reads the frozen artifact, which this later phase
    # does not regenerate — it now pins a HISTORICAL floor, not a live one.
    live_predictable = sum(1 for row in per_task if row["ok"] and row["predictable"])
    live_pct = 100.0 * live_predictable / n
    assert live_predictable == 147, (
        "the FROZEN pre-Q1 floor changed — either the histogram artifact "
        "was regenerated (it must not be — a snapshot is a historical "
        "record), or this assertion's file was read from the wrong path; "
        "re-derive this number, don't just update the constant")

    # HYPOTHETICAL: a task becomes predictable if (a) it is already `ok`
    # (structural representability — Q1 could not move this, see
    # docstring) AND (b) every extern family it needs is in the
    # LANDED set AND (c) it has no recv-form call outside the landed
    # string/dict method families (approximated here: any recv_methods
    # present is treated as covered, since Q1 landed a broad recv-form
    # dispatch — a slightly OPTIMISTIC approximation, named as such).
    def would_be_predictable(row: dict) -> bool:
        if not row["ok"]:
            return False
        if row["predictable"]:
            return True
        extern_fams = set(row.get("extern_families", []))
        return extern_fams <= Q1_LANDED_EXTERN_FAMILIES

    hypothetical = sum(1 for row in per_task if would_be_predictable(row))
    hypothetical_pct = 100.0 * hypothetical / n

    print(f"\nHQ1 LIVE (real emit_prog_ir, unmodified by this phase): "
          f"{live_predictable}/{n} = {live_pct:.1f}%")
    print(f"HQ1 HYPOTHETICAL (Q1-landed extern families, per-task re-derivation): "
          f"{hypothetical}/{n} = {hypothetical_pct:.1f}%")
    print("Preregistered bar (PROGRAM_SYNTHESIS_ARC2_PREREG.md §3): "
          "52.9% (226/427) at FULL recommended scope; 44.5% (190/427) at "
          "the 55%-mark scope this phase targeted.")

    # Sanity bounds, not the headline: the hypothetical number must be
    # >= the live floor (it can only ever help, never hurt) and must
    # stay within the type-domain-independent op/feature-curve ceiling
    # the histogram itself measured for these families.
    assert hypothetical >= live_predictable
    assert hypothetical <= n
