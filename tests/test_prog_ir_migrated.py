"""test_prog_ir_migrated — P1 gates for the Program IR + ProgEval + naming
primitives (PROGRAM_SYNTHESIS_PREREG.md §3; PROGRAM_SYNTHESIS_PLAN.md §3.2).

Gates:

  REFLECT ROUND-TRIP — for EVERY new variant: Term-JSON →
    ``add_term_subgraph`` → ``term_subgraph_json`` → identical canonical
    JSON (idempotent under a second round-trip).

  PROGEVAL ≡ CPYTHON — a fixture corpus of small programs, each built as
    IR and ALSO executed by CPython ``exec``; result + final env agree.
    Every variant with semantics is covered (While and Raise included).
    The disagreement list must be EMPTY — each fixture asserts.

  FUEL HONESTY — a while-loop with too-little fuel → ``halted: False``,
    ``steps == fuel``, ``trap == "fuel"``, no exception, NEVER a value.

  STRUCTURAL HONESTY — the main ``evaluate()`` on a bare statement
    variant does NOT execute it (returns the documented inert None).

  NAMING PRIMITIVES — SnakeCase/CaseFold return usable strings
    (Surface(Text) end-to-end, the registered plan-§6.3 fallback); a
    Computed ``set_attr`` effect stores the Surface as a usable string
    attr (rule fired via tick), and a render-template combinator (Cat)
    accepts it.

Documented ProgEval divergences the fixtures respect (prog_eval.rs
module docs): expression arithmetic is DSL-semantics (no
ZeroDivisionError), list/tuple both realise as Tuple, no aliasing
through lvalue writes, set iteration order is the substrate's.
"""
from __future__ import annotations

import json
import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs


# ---------------------------------------------------------------------------
# Term-JSON builders (mechanical; mirrors substrate/dsl.py's Prog* classes)
# ---------------------------------------------------------------------------
def L(v):
    return {"type": "Lit", "value": v}


def V(n):
    return {"type": "Var", "name": n}


def SEQ(*stmts):
    return {"type": "ProgSeq", "stmts": list(stmts)}


def ASSIGN(name, value):
    return {"type": "ProgAssignVar", "name": name, "value": value}


def AUG(name, op, value):
    return {"type": "ProgAugAssign", "name": name, "op": op, "value": value}


def UNPACK(targets, value):
    return {"type": "ProgTupleUnpack", "targets": list(targets), "value": value}


def IF(cond, then, orelse=None):
    return {"type": "ProgIfStmt", "cond": cond, "then": then, "orelse": orelse}


def FOR(var, it, body, orelse=None):
    return {"type": "ProgForEach", "var": var, "iter": it, "body": body, "orelse": orelse}


def WHILE(cond, body, orelse=None):
    return {"type": "ProgWhile", "cond": cond, "body": body, "orelse": orelse}


def LOOPCTL(kind):
    return {"type": "ProgLoopCtl", "kind": kind}


def RET(value=None):
    return {"type": "ProgReturn", "value": value}


def TRY(body, exc_var="", handler=None):
    return {"type": "ProgTryOr", "body": body, "exc_var": exc_var, "handler": handler}


def RAISE(exc=None):
    return {"type": "ProgRaise", "exc": exc}


def IMP(module, alias="", names=()):
    return {"type": "ProgImportStmt", "module": module, "alias": alias, "names": list(names)}


def SSET(obj, index, value):
    return {"type": "ProgSubscriptSet", "obj": obj, "index": index, "value": value}


def ASET(obj, attr, value):
    return {"type": "ProgAttrSet", "obj": obj, "attr": attr, "value": value}


def PARAM(name, default=None):
    return {"type": "ProgDefFnParam", "name": name, "default": default}


def CALL(name, *args, recv=None):
    return {"type": "ProgCallExtern", "name": name, "recv": recv, "args": list(args)}


def AGET(obj, attr):
    return {"type": "ProgAttrGet", "obj": obj, "attr": attr}


def SUB(obj, index):
    return {"type": "ProgSubscript", "obj": obj, "index": index}


def CLIT(kind, *items):
    return {"type": "ProgContainerLit", "kind": kind, "items": list(items)}


def COMPL(var, source, expr, cond=None):
    return {"type": "ProgComprehensionList", "var": var, "source": source,
            "expr": expr, "cond": cond}


def COMPG(var, source, expr, cond=None):
    return {"type": "ProgComprehensionGen", "var": var, "source": source,
            "expr": expr, "cond": cond}


def ISOP(a, b, negated=False):
    return {"type": "ProgIsOp", "a": a, "b": b, "negated": negated}


def FSTR(*parts):
    return {"type": "ProgFString", "parts": list(parts)}


def PLUS(*items):
    return {"type": "Plus", "items": list(items)}


def TIMES(*items):
    return {"type": "Times", "items": list(items)}


def MINUS(a, b):
    return {"type": "Minus", "a": a, "b": b}


def GT(a, b):
    return {"type": "Gt", "a": a, "b": b}


def LT(a, b):
    return {"type": "Lt", "a": a, "b": b}


def EQ(a, b):
    return {"type": "Eq", "a": a, "b": b}


def MKDICT(**kv):
    items = []
    for k, v in kv.items():
        items.append(L(k))
        items.append(L(v))
    return {"type": "MkDict", "items": items}


def PROGEVAL(prog, env=None, oracles=None, fuel=1000, field=""):
    return {"type": "ProgEval", "prog": prog, "env": env, "oracles": oracles,
            "fuel": fuel, "field": field}


def ORACLES(*names):
    return MKDICT(**{n: "builtin" for n in names})


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
@pytest.fixture()
def sub():
    return srs.Substrate()


def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(PROGEVAL(SEQ()), {})
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


def run_prog(sub, prog, env=None, oracles=(), fuel=1000):
    """Evaluate ProgEval over `prog`, threading env via a Var binding
    (mechanical adapter I/O; the interpreter is entirely Rust)."""
    env_child = V("envd") if env else None
    oracles_child = ORACLES(*oracles) if oracles else None
    out = sub._inner.evaluate(
        PROGEVAL(prog, env=env_child, oracles=oracles_child, fuel=fuel),
        {"envd": env} if env else None,
    )
    assert isinstance(out, dict), f"ProgEval must return a Dict, got {type(out)}"
    return out


def norm(v):
    """Cross-runtime normalisation: list/tuple → tuple, dict → dict of
    normed, str stays str (Surface renders to str via value_to_py)."""
    if isinstance(v, (list, tuple)):
        return tuple(norm(x) for x in v)
    if isinstance(v, (set, frozenset)):
        return frozenset(norm(x) for x in v)
    if isinstance(v, dict):
        return {norm(k): norm(x) for k, x in v.items()}
    return v


def run_python_block(src, env):
    g = dict(env)
    exec(textwrap.dedent(src), g)  # noqa: S102 — the gate's CPython oracle
    g.pop("__builtins__", None)
    return g


def assert_env_agrees(sub, prog, py_src, env, keys, oracles=()):
    out = run_prog(sub, prog, env=env or None, oracles=oracles)
    assert out["trap"] is None, f"unexpected trap: {out['trap']}"
    assert out["halted"] is True
    py_env = run_python_block(py_src, env)
    for k in keys:
        assert norm(out["env_out"].get(k)) == norm(py_env[k]), (
            f"env disagreement on {k!r}: rust={out['env_out'].get(k)!r} "
            f"py={py_env[k]!r}")
    return out


def assert_result_agrees(sub, prog, py_src, env, oracles=()):
    """def-style fixture: py_src defines f; expected = f(**env)."""
    out = run_prog(sub, prog, env=env or None, oracles=oracles)
    assert out["trap"] is None, f"unexpected trap: {out['trap']}"
    assert out["halted"] is True
    g = {}
    exec(textwrap.dedent(py_src), g)  # noqa: S102
    expected = g["f"](**env)
    assert norm(out["result"]) == norm(expected), (
        f"result disagreement: rust={out['result']!r} py={expected!r}")
    return out


# ---------------------------------------------------------------------------
# 1) REFLECT ROUND-TRIP — every new variant.
# ---------------------------------------------------------------------------
# One sample per variant, written in the EMISSION dialect (optional
# children explicit null; optional identifier sentinels explicit "").
REFLECT_SAMPLES = {
    "ProgSeq": SEQ(ASSIGN("a", L(1)), RET(V("a"))),
    "ProgAssignVar": ASSIGN("x", PLUS(L(1), L(2))),
    "ProgAugAssign": AUG("x", "add", L(3)),
    "ProgTupleUnpack": UNPACK(["a", "b"], CLIT("tuple", L(1), L(2))),
    "ProgIfStmt": IF(GT(V("x"), L(0)), ASSIGN("y", L(1)), ASSIGN("y", L(0))),
    "ProgForEach": FOR("i", CALL("range", L(3)), AUG("t", "add", V("i")), None),
    "ProgWhile": WHILE(LT(V("i"), L(5)), AUG("i", "add", L(1)), None),
    "ProgLoopCtl": LOOPCTL("break"),
    "ProgReturn": RET(PLUS(V("x"), L(1))),
    "ProgTryOr": TRY(RAISE(L("boom")), "e", ASSIGN("c", L(1))),
    "ProgRaise": RAISE(L("nope")),
    "ProgImportStmt": IMP("math", "", ["sqrt", "floor"]),
    "ProgSubscriptSet": SSET(V("d"), L("k"), L(5)),
    "ProgAttrSet": ASET(V("r"), "count", L(2)),
    "ProgDefFnParam": PARAM("n", L(7)),
    "ProgCallExtern": CALL("len", V("xs")),
    "ProgAttrGet": AGET(V("r"), "count"),
    "ProgSubscript": SUB(V("xs"), L(0)),
    "ProgContainerLit": CLIT("dict", L("k"), L(1), L("j"), L(2)),
    "ProgComprehensionList": COMPL("x", V("xs"), TIMES(V("x"), V("x")), GT(V("x"), L(1))),
    "ProgComprehensionGen": COMPG("x", V("xs"), TIMES(V("x"), L(2)), None),
    "ProgIsOp": ISOP(V("v"), L(None), negated=True),
    "ProgFString": FSTR(L("x="), V("x")),
    "ProgEval": PROGEVAL(SEQ(ASSIGN("a", L(1))), env=None, oracles=None, fuel=5, field=""),
    "SnakeCase": {"type": "SnakeCase", "text": L("Foo Bar")},
    "CaseFold": {"type": "CaseFold", "text": L("MiXeD")},
}


def _canon(d):
    """Canonical form: drop null-valued fields (absent optional child ≡
    explicit null in the wire dialect) recursively."""
    if isinstance(d, dict):
        return {k: _canon(v) for k, v in d.items() if v is not None}
    if isinstance(d, list):
        return [_canon(x) for x in d]
    return d


@pytest.mark.parametrize("variant", sorted(REFLECT_SAMPLES))
def test_reflect_round_trip(sub, variant):
    sample = REFLECT_SAMPLES[variant]
    nid = sub._inner.add_term_subgraph(sample)
    c1 = json.loads(sub._inner.term_subgraph_json(nid))
    assert c1["type"] == variant
    # Identity with the source, canonically (null ≡ absent).
    assert _canon(c1) == _canon(sample), f"{variant} did not round-trip"
    # Idempotence: a second reflect pass is byte-stable.
    nid2 = sub._inner.add_term_subgraph(c1)
    c2 = json.loads(sub._inner.term_subgraph_json(nid2))
    assert c2 == c1, f"{variant} second round-trip drifted"


# ---------------------------------------------------------------------------
# 2) PROGEVAL ≡ CPYTHON — the fixture corpus.
# ---------------------------------------------------------------------------
def test_arith_assign_seq(sub):
    prog = SEQ(
        ASSIGN("a", L(2)),
        ASSIGN("b", PLUS(TIMES(V("a"), L(3)), L(4))),
        ASSIGN("c", MINUS(V("b"), V("a"))),
    )
    assert_env_agrees(sub, prog, "a = 2\nb = a * 3 + 4\nc = b - a\n", {},
                      ["a", "b", "c"])


def test_if_else(sub):
    prog = IF(GT(V("x"), L(3)), ASSIGN("y", L("big")), ASSIGN("y", L("small")))
    assert_env_agrees(sub, prog, "y = 'big' if x > 3 else 'small'\n",
                      {"x": 5}, ["y"])
    assert_env_agrees(sub, prog, "y = 'big' if x > 3 else 'small'\n",
                      {"x": 2}, ["y"])


def test_for_range_accumulator(sub):
    prog = SEQ(
        ASSIGN("total", L(0)),
        FOR("i", CALL("range", V("n")), AUG("total", "add", V("i"))),
    )
    assert_env_agrees(sub, prog,
                      "total = 0\nfor i in range(n):\n    total += i\n",
                      {"n": 6}, ["total", "i"], oracles=("range",))


def test_while_loop(sub):
    prog = SEQ(
        ASSIGN("i", L(0)),
        ASSIGN("s", L(0)),
        WHILE(LT(V("i"), L(5)),
              SEQ(AUG("s", "add", V("i")), AUG("i", "add", L(1)))),
    )
    assert_env_agrees(sub, prog,
                      "i = 0\ns = 0\nwhile i < 5:\n    s += i\n    i += 1\n",
                      {}, ["i", "s"])


def test_tuple_unpack(sub):
    prog = SEQ(UNPACK(["a", "b"], V("p")), ASSIGN("c", PLUS(V("a"), V("b"))))
    assert_env_agrees(sub, prog, "a, b = p\nc = a + b\n",
                      {"p": (3, 4)}, ["a", "b", "c"])


def test_try_raise_caught(sub):
    prog = TRY(RAISE(L("boom")), "e", ASSIGN("caught", L(1)))
    out = assert_env_agrees(
        sub, prog,
        "try:\n    raise ValueError('boom')\nexcept Exception:\n    caught = 1\n",
        {}, ["caught"])
    # The trap reason is bound to the exc var (interpreter's own spelling).
    assert out["env_out"]["e"] == "raise:boom"


def test_comprehension_list(sub):
    prog = ASSIGN("ys", COMPL("x", V("xs"), TIMES(V("x"), V("x")), GT(V("x"), L(1))))
    assert_env_agrees(sub, prog, "ys = [x * x for x in xs if x > 1]\n",
                      {"xs": (1, 2, 3)}, ["ys"])


def test_comprehension_gen_via_sum(sub):
    prog = ASSIGN("s", CALL("sum", COMPG("x", V("xs"), TIMES(V("x"), L(2)))))
    assert_env_agrees(sub, prog, "s = sum(x * 2 for x in xs)\n",
                      {"xs": (1, 2, 3)}, ["s"], oracles=("sum",))


def test_builtin_oracles(sub):
    prog = SEQ(
        ASSIGN("n", CALL("len", V("xs"))),
        ASSIGN("m", CALL("max", V("xs"))),
        ASSIGN("k", CALL("abs", V("d"))),
    )
    assert_env_agrees(sub, prog, "n = len(xs)\nm = max(xs)\nk = abs(d)\n",
                      {"xs": (7, 8, 9), "d": -3}, ["n", "m", "k"],
                      oracles=("len", "max", "abs"))


def test_loop_ctl_break_continue(sub):
    prog = SEQ(
        ASSIGN("total", L(0)),
        FOR("i", CALL("range", L(10)),
            SEQ(
                IF(EQ(V("i"), L(3)), LOOPCTL("break")),
                IF(EQ(V("i"), L(1)), LOOPCTL("continue")),
                AUG("total", "add", V("i")),
            )),
    )
    assert_env_agrees(
        sub, prog,
        "total = 0\n"
        "for i in range(10):\n"
        "    if i == 3:\n        break\n"
        "    if i == 1:\n        continue\n"
        "    total += i\n",
        {}, ["total"], oracles=("range",))


def test_aug_assign_operators(sub):
    prog = SEQ(
        ASSIGN("a", L(7)), AUG("a", "mult", L(2)),
        ASSIGN("b", L(9)), AUG("b", "sub", L(1)),
        ASSIGN("c", L(17)), AUG("c", "floordiv", L(2)),
        ASSIGN("d", L(10)), AUG("d", "mod", L(3)),
        ASSIGN("e", L("ab")), AUG("e", "add", L("cd")),
    )
    assert_env_agrees(
        sub, prog,
        "a = 7\na *= 2\nb = 9\nb -= 1\nc = 17\nc //= 2\n"
        "d = 10\nd %= 3\ne = 'ab'\ne += 'cd'\n",
        {}, ["a", "b", "c", "d", "e"])


def test_subscript_read_write(sub):
    prog = SEQ(
        ASSIGN("d", CLIT("dict", L("k"), L(1))),
        SSET(V("d"), L("k"), L(5)),
        ASSIGN("xs", CLIT("list", L(7), L(8))),
        SSET(V("xs"), L(0), L(9)),
        ASSIGN("y", PLUS(SUB(V("d"), L("k")), SUB(V("xs"), L(0)))),
    )
    assert_env_agrees(
        sub, prog,
        "d = {'k': 1}\nd['k'] = 5\nxs = [7, 8]\nxs[0] = 9\ny = d['k'] + xs[0]\n",
        {}, ["y", "xs", "d"])


def test_nested_subscript_set_path(sub):
    prog = SEQ(
        ASSIGN("g", CLIT("dict", L("a"), CLIT("list", L(1), L(2)))),
        SSET(SUB(V("g"), L("a")), L(1), L(9)),
        ASSIGN("y", SUB(SUB(V("g"), L("a")), L(1))),
    )
    assert_env_agrees(sub, prog,
                      "g = {'a': [1, 2]}\ng['a'][1] = 9\ny = g['a'][1]\n",
                      {}, ["y"])


def test_is_none(sub):
    prog = IF(ISOP(V("v"), L(None)), ASSIGN("y", L(1)), ASSIGN("y", L(0)))
    assert_env_agrees(sub, prog, "y = 1 if v is None else 0\n",
                      {"v": None}, ["y"])
    assert_env_agrees(sub, prog, "y = 1 if v is None else 0\n",
                      {"v": 5}, ["y"])
    # is not None
    prog2 = IF(ISOP(V("v"), L(None), negated=True), ASSIGN("y", L(1)), ASSIGN("y", L(0)))
    assert_env_agrees(sub, prog2, "y = 1 if v is not None else 0\n",
                      {"v": 5}, ["y"])


def test_fstring(sub):
    prog = ASSIGN("s", FSTR(L("x="), V("x"), L(", r="), V("r")))
    assert_env_agrees(sub, prog, "s = f'x={x}, r={r}'\n",
                      {"x": 7, "r": 2.5}, ["s"])


def test_container_literals(sub):
    prog = SEQ(
        ASSIGN("t", CLIT("list", L(1), L(2))),
        ASSIGN("u", CLIT("tuple", CALL("len", V("t")), SUB(V("t"), L(1)))),
    )
    assert_env_agrees(sub, prog, "t = [1, 2]\nu = (len(t), t[1])\n",
                      {}, ["u"], oracles=("len",))


def test_return_def_style(sub):
    prog = SEQ(
        IF(GT(V("x"), L(0)), RET(TIMES(V("x"), L(2)))),
        RET(L(0)),
    )
    src = "def f(x):\n    if x > 0:\n        return x * 2\n    return 0\n"
    assert_result_agrees(sub, prog, src, {"x": 5})
    assert_result_agrees(sub, prog, src, {"x": -2})


def test_def_fn_param_default(sub):
    prog = SEQ(PARAM("n", L(7)), RET(PLUS(V("n"), L(1))))
    src = "def f(n=7):\n    return n + 1\n"
    # Called WITHOUT n → default binds.
    out = run_prog(sub, prog, env=None)
    assert out["trap"] is None and out["result"] == 8
    # Called WITH n → env wins.
    assert_result_agrees(sub, prog, src, {"n": 3})


def test_attr_get_set_records(sub):
    prog = SEQ(
        ASSIGN("r", CLIT("dict")),
        ASET(V("r"), "x", L(5)),
        RET(PLUS(AGET(V("r"), "x"), L(1))),
    )
    src = ("def f():\n"
           "    class R:\n        pass\n"
           "    r = R()\n"
           "    r.x = 5\n"
           "    return r.x + 1\n")
    assert_result_agrees(sub, prog, src, {})


def test_import_stmt_no_op(sub):
    prog = SEQ(IMP("math"), ASSIGN("z", L(1)))
    assert_env_agrees(sub, prog, "import math\nz = 1\n", {}, ["z"])


def test_while_raise_interplay(sub):
    # while + raise + try: loop until i == 3 then raise; caught outside.
    prog = TRY(
        SEQ(
            ASSIGN("i", L(0)),
            WHILE(L(True),
                  SEQ(AUG("i", "add", L(1)),
                      IF(EQ(V("i"), L(3)), RAISE(L("done")))))),
        "e",
        ASSIGN("stopped", V("i")),
    )
    assert_env_agrees(
        sub, prog,
        "try:\n"
        "    i = 0\n"
        "    while True:\n"
        "        i += 1\n"
        "        if i == 3:\n            raise ValueError('done')\n"
        "except Exception:\n"
        "    stopped = i\n",
        {}, ["i", "stopped"])


# ---------------------------------------------------------------------------
# 3) Honest traps
# ---------------------------------------------------------------------------
def test_undeclared_extern_traps(sub):
    prog = ASSIGN("y", CALL("foo", L(1)))
    out = run_prog(sub, prog)  # no oracles declared
    assert out["halted"] is False
    assert out["trap"] == "extern:foo"
    assert out["result"] is None
    assert "y" not in out["env_out"]
    # CPython agrees this is an error (NameError).
    with pytest.raises(NameError):
        run_python_block("y = foo(1)\n", {})


def test_uncaught_raise_traps(sub):
    out = run_prog(sub, RAISE(L("boom")))
    assert out["halted"] is False
    assert out["trap"] == "raise:boom"
    with pytest.raises(ValueError):
        run_python_block("raise ValueError('boom')\n", {})


# ---------------------------------------------------------------------------
# 4) FUEL HONESTY
# ---------------------------------------------------------------------------
def test_fuel_honesty(sub):
    prog = SEQ(ASSIGN("i", L(0)),
               WHILE(L(True), AUG("i", "add", L(1))))
    out = run_prog(sub, prog, fuel=7)
    assert out["halted"] is False, "fuel exhaustion must NEVER report halted"
    assert out["steps"] == 7, f"steps must equal fuel, got {out['steps']}"
    assert out["trap"] == "fuel"
    assert out["result"] is None, "fuel exhaustion must never yield a value"
    # Honest partial env: i advanced but is not the completed value.
    assert isinstance(out["env_out"].get("i"), int)
    assert out["env_out"]["i"] > 0

    # Fuel is NOT catchable by TryOr (a catchable fuel-out forges halted).
    prog2 = TRY(WHILE(L(True), ASSIGN("x", L(1))), "e", ASSIGN("caught", L(1)))
    out2 = run_prog(sub, prog2, fuel=5)
    assert out2["halted"] is False
    assert out2["trap"] == "fuel"
    assert "caught" not in out2["env_out"]


# ---------------------------------------------------------------------------
# 5) STRUCTURAL HONESTY — statement IR is inert under the main evaluator.
# ---------------------------------------------------------------------------
def test_structural_honesty_main_evaluate_is_inert(sub):
    for sample in (
        ASSIGN("x", L(1)),
        SEQ(ASSIGN("x", L(1))),
        WHILE(L(True), ASSIGN("x", L(1))),   # would hang if executed
        RAISE(L("boom")),                     # would raise if executed
        CALL("len", L((1, 2))),
        SUB(L((1, 2)), L(0)),
        FSTR(L("a")),
    ):
        assert sub._inner.evaluate(sample, {}) is None, (
            f"{sample['type']} must be INERT under evaluate()")


# ---------------------------------------------------------------------------
# 6) NAMING PRIMITIVES — Surface(Text) end-to-end (plan §6.3 fallback).
# ---------------------------------------------------------------------------
def test_snake_case_and_case_fold_eval(sub):
    n = sub._inner
    assert n.evaluate({"type": "SnakeCase", "text": L("Total Cost (USD)")}, {}) == "total_cost_usd"
    assert n.evaluate({"type": "SnakeCase", "text": L("camelCaseName")}, {}) == "camel_case_name"
    assert n.evaluate({"type": "SnakeCase", "text": L("HTTPServer2x")}, {}) == "httpserver2x"
    assert n.evaluate({"type": "CaseFold", "text": L("MiXeD UP")}, {}) == "mixed up"
    # Honest gap on non-strings — never coerced.
    assert n.evaluate({"type": "SnakeCase", "text": L(3)}, {}) is None


def test_snake_case_surface_is_usable_in_set_attr_and_templates(sub):
    """The §6.3 fallback made TRUE: a Computed set_attr stores the
    Surface(Text) as a usable string attr (graph-resident Rule, fired
    via tick — the rule_minting_dialect finding-4 precedent), and the
    render-template combinator (Cat) accepts Surface input."""
    s = sub
    anchor = s.add_node("Anchor", {})
    probe = s.add_node("Probe", {})
    s._inner.add_edge_unchecked(anchor, "trig", probe)
    s.add_node("Rule", {
        "id": "name_from_spec_words",
        "match": [["anc", "trig", "tg"]],
        "where": L(True),
        "effect": [["set_attr", "tg", "ident",
                    {"__term__": {"type": "SnakeCase", "text": L("Total Cost")}}]],
    })
    s.tick()
    got = s.node(probe)["attrs"].get("ident")
    assert got == "total_cost", f"set_attr must store a usable string, got {got!r}"

    # Render-template acceptance: Cat concatenates the Surface.
    cat = {"type": "Cat", "items": [
        {"type": "SnakeCase", "text": L("Total Cost")}, L("_v1")]}
    assert s._inner.evaluate(cat, {}) == "total_cost_v1"


# ---------------------------------------------------------------------------
# 7) ProgEval over a REFLECTED subgraph (the graph-data form).
# ---------------------------------------------------------------------------
def test_prog_eval_over_reflected_subgraph(sub):
    prog = SEQ(ASSIGN("x", L(2)), ASSIGN("y", PLUS(V("x"), L(3))))
    nid = sub._inner.add_term_subgraph(prog)
    out = sub._inner.evaluate(
        PROGEVAL({"type": "Var", "name": "p"}), {"p": nid})
    assert out["trap"] is None
    assert out["halted"] is True
    assert out["env_out"]["y"] == 5
