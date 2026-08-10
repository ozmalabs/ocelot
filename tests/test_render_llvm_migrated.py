"""test_render_llvm_migrated — P5 LLVM-track gates
(PROGRAM_SYNTHESIS_PLAN.md §4-P5: "LLVM IR: extend emission to the IR
statement set (branches, loops via CFG blocks); x86-64 = IR → existing
cfg_to_asm chain. No direct statement templates for asm.").

Gates:

  THE ROUND-TRIP LAW — hub IR → emit_prog_to_llvm → parse_llvm_cfg →
    lift_llvm_cfg → hub IR again. The LIFT IMAGE is the canonical form:
    L = lift(parse(emit(P))) is a ONE-ROUND FIXPOINT
    (lift(parse(emit(L))) == L, byte-identical Term-JSON), and for
    while / both-arms-return / join-with-else / straight-line shapes
    emit(L) == emit(P) byte-identical .ll text. The canonicalization
    deltas P → L are enumerated in PROGRAM_SYNTHESIS_P5_LLVM.md §4
    (SSA temp naming, phi init/latch copies, cond inlining, empty-arm
    materialisation, guard/continuation absorption).

  THE TRIPLE-AGREEMENT LAW — on every compile fixture and pinned
    integer input: ProgEval(P) == interpret_cfg(parse(emit(P))) ==
    the x86-64 .so built by emit_x86_64_cfg + assemble_and_load.
    The x86-64 read-off IS the chain — no direct statement templates.

  THE FRONTIER CLOSED — phi landed in the dialect (P2 §3's documented
    recipe, now applied): a counting loop PARSES, INTERPRETS to values,
    COMPILES, and LIFTS to a ProgWhile with loop-carried variables.
    (The P2 no-phi loop fixture keeps its agreement-of-refusal gates in
    test_prog_read_llvm_migrated — unchanged, still green.)

  HONEST REFUSALS — out-of-scope hub IR (containers, strings, try,
    calls, nested control) → {ok: False, blockers: [...]}; phi outside
    the two structured patterns → lift blocker; malformed phi text →
    parse ValueError.

  THE P4 ARTIFACT — the accepted max_of_two Program (the real P4
    pipeline, re-run) and a lattice-ordered synthesized loop program
    (sum-to-n, taught as a SHUFFLED statement spine — the corpus
    bigrams order it) emit to LLVM, compile to x86-64, run, and agree
    with ProgEval on held-out inputs.

Run: pytest tests/test_render_llvm_migrated.py --confcutdir=. -q
(the worktree-engine seam — P1 notes §6).
"""
from __future__ import annotations

import json
import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs

from domains.llvm_ir_cfg import (
    install_cfg_productions, interpret_cfg, parse_llvm_cfg,
)
from domains.llvm_ir_cfg_to_asm import emit_x86_64_cfg
from domains.llvm_ir_io import parse_llvm_ir
from domains.prog_ir_llvm import lift_llvm_cfg
from domains.prog_ir_to_llvm import emit_prog_to_llvm

_HAS_GCC = shutil.which("gcc") is not None


def _prog_eval_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ProgEval",
                           "prog": {"type": "ProgSeq", "stmts": []},
                           "env": None, "oracles": None,
                           "fuel": 10, "field": ""}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _prog_eval_live():
    pytest.skip(
        "ProgEval Term not present in the installed substrate_rs binary — "
        "stale engine (P1 notes §6). Honest skip, not a fake pass.",
        allow_module_level=True)


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
def fresh():
    s = srs.Substrate()
    for src_t in ("LLVMInstruction", "LLVMConstant", "LLVMValue"):
        for tgt_t in ("LLVMInstruction", "LLVMConstant", "LLVMValue"):
            for et in ("uses_op0", "uses_op1", "uses_op2", "produces"):
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    install_cfg_productions(s)
    return s


_ORACLES = {"type": "MkDict", "items": [
    {"type": "Lit", "value": "range"}, {"type": "Lit", "value": "builtin"},
]}


def prog_eval(prog, env, fuel=200000):
    s = srs.Substrate()
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": prog,
         "env": {"type": "Var", "name": "e"},
         "oracles": _ORACLES, "fuel": fuel, "field": ""},
        {"e": env})
    assert isinstance(out, dict)
    return out


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def SEQ(*s): return {"type": "ProgSeq", "stmts": list(s)}
def A(n, v): return {"type": "ProgAssignVar", "name": n, "value": v}
def P(n): return {"type": "ProgDefFnParam", "name": n, "default": None}
def RET(v): return {"type": "ProgReturn", "value": v}
def PLUS(*xs): return {"type": "Plus", "items": list(xs)}
def TIMES(*xs): return {"type": "Times", "items": list(xs)}


def WHILE(cond, *body):
    return {"type": "ProgWhile", "cond": cond, "body": SEQ(*body),
            "orelse": None}


def IF(cond, then, orelse=None):
    return {"type": "ProgIfStmt", "cond": cond, "then": then,
            "orelse": orelse}


# ---------------------------------------------------------------------------
# fixtures (hub IR, integer/control-flow scope)
# ---------------------------------------------------------------------------
SUM = SEQ(  # counting loop — inexpressible in the dialect before phi
    P("n"), A("acc", L(0)), A("i", L(0)),
    WHILE({"type": "Lte", "a": V("i"), "b": V("n")},
          A("acc", PLUS(V("acc"), V("i"))),
          A("i", PLUS(V("i"), L(1)))),
    RET(V("acc")))

MAX_RET = SEQ(  # both-arms-return diamond
    P("a"), P("b"),
    IF({"type": "Gt", "a": V("a"), "b": V("b")},
       SEQ(RET(V("a"))), SEQ(RET(V("b")))))

MAX_EXPR = SEQ(  # the P4 template shape: Return of IfThenElse → select
    P("a"), P("b"),
    RET({"type": "IfThenElse",
         "cond": {"type": "Gt", "a": V("a"), "b": V("b")},
         "then": V("a"), "other": V("b")}))

IFJOIN = SEQ(  # join with phis, both arms assign
    P("x"), A("r", L(0)),
    IF({"type": "Gt", "a": V("x"), "b": L(10)},
       SEQ(A("r", TIMES(V("x"), L(2)))),
       SEQ(A("r", PLUS(V("x"), L(100))))),
    RET(V("r")))

IFJOIN_NOELSE = SEQ(  # empty-arm join phi (entry-edge incoming)
    P("x"), A("r", V("x")),
    IF({"type": "Gt", "a": V("x"), "b": L(0)},
       SEQ(A("r", {"type": "Minus", "a": L(0), "b": V("x")}))),
    RET(V("r")))

FOREACH = SEQ(  # range-ForEach → desugared counting loop
    P("n"), A("acc", L(0)),
    {"type": "ProgForEach", "var": "i",
     "iter": {"type": "ProgCallExtern", "name": "range", "recv": None,
              "args": [V("n")]},
     "body": {"type": "ProgAugAssign", "name": "acc", "op": "add",
              "value": V("i")},
     "orelse": None},
    RET(V("acc")))

STRAIGHT = SEQ(  # straight-line arithmetic with a redefinition
    P("x"), P("y"),
    A("t", PLUS(V("x"), V("y"))),
    A("t", TIMES(V("t"), V("t"))),
    RET({"type": "Minus", "a": V("t"), "b": V("y")}))


def _py_sum(n): return sum(range(0, n + 1)) if n >= 0 else 0


CASES = {
    "SUM": (SUM, ["n"], [({"n": 0}, 0), ({"n": 5}, 15), ({"n": 10}, 55),
                         ({"n": -3}, 0)]),
    "MAX_RET": (MAX_RET, ["a", "b"],
                [({"a": 3, "b": 9}, 9), ({"a": 9, "b": 3}, 9),
                 ({"a": 4, "b": 4}, 4), ({"a": -7, "b": -2}, -2)]),
    "MAX_EXPR": (MAX_EXPR, ["a", "b"],
                 [({"a": 2, "b": 8}, 8), ({"a": 8, "b": 2}, 8)]),
    "IFJOIN": (IFJOIN, ["x"], [({"x": 11}, 22), ({"x": 10}, 110),
                               ({"x": -4}, 96)]),
    "IFJOIN_NOELSE": (IFJOIN_NOELSE, ["x"],
                      [({"x": 5}, -5), ({"x": 0}, 0), ({"x": -6}, -6)]),
    "FOREACH": (FOREACH, ["n"], [({"n": 0}, 0), ({"n": 5}, 10),
                                 ({"n": 1}, 0)]),
    "STRAIGHT": (STRAIGHT, ["x", "y"],
                 [({"x": 3, "y": 4}, 45), ({"x": -2, "y": 2}, -2)]),
}

# emit(L) == emit(P) holds where the lift loses nothing the emitter
# re-materialises differently; the empty-arm join materialises an
# orelse (documented delta §4), so its text fixpoint lands one round
# later (emit(L) == emit(L2)).
_TEXT_IDENTICAL = {"SUM", "MAX_RET", "MAX_EXPR", "IFJOIN", "FOREACH",
                   "STRAIGHT"}


def emit_parse_lift(prog, name, params):
    e = emit_prog_to_llvm(prog, fn_name=name)
    assert e["ok"], f"{name}: emit refused: {e['blockers']}"
    s = fresh()
    out = parse_llvm_cfg(s, e["text"],
                         inputs=tuple("%" + p for p in e["params"]))
    lift = lift_llvm_cfg(s, out)
    assert lift["ok"], f"{name}: lift blocked: {lift['blockers']}"
    return e, s, out, lift


# ---------------------------------------------------------------------------
# 1) determinism
# ---------------------------------------------------------------------------
def test_emit_is_deterministic():
    for name, (prog, _params, _cases) in CASES.items():
        a = emit_prog_to_llvm(prog, fn_name=name.lower())
        b = emit_prog_to_llvm(prog, fn_name=name.lower())
        assert a == b, name


# ---------------------------------------------------------------------------
# 2) THE ROUND-TRIP LAW
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(CASES))
def test_round_trip_law(name):
    prog, params, cases = CASES[name]
    e, _s, _out, lift = emit_parse_lift(prog, name.lower(), params)
    lifted = lift["prog"]

    # (a) semantic identity: ProgEval(P) == ProgEval(L) on pinned inputs
    #     (and both equal the pinned expected value).
    for env, expected in cases:
        r0 = prog_eval(prog, env)
        r1 = prog_eval(lifted, env)
        assert r0["trap"] is None and r1["trap"] is None, (name, env)
        assert r0["result"] == r1["result"] == expected, \
            f"{name} {env}: P={r0['result']} L={r1['result']} " \
            f"expected={expected}"

    # (b) the lift image is a ONE-ROUND FIXPOINT: re-emitting and
    #     re-lifting L reproduces L byte-identically.
    e2 = emit_prog_to_llvm(lifted, fn_name=name.lower(),
                           params=e["params"])
    assert e2["ok"], f"{name}: re-emit refused: {e2['blockers']}"
    s2 = fresh()
    out2 = parse_llvm_cfg(s2, e2["text"],
                          inputs=tuple("%" + p for p in e["params"]))
    lift2 = lift_llvm_cfg(s2, out2)
    assert lift2["ok"], lift2["blockers"]
    assert json.dumps(lift2["prog"], sort_keys=True) == \
        json.dumps(lifted, sort_keys=True), f"{name}: lift not a fixpoint"

    # (c) text canonicality: emit(L) == emit(P) byte-identical where the
    #     shape permits (all but the empty-arm join, documented §4) —
    #     and ALWAYS emit(L) == emit(lift(emit(L))) (text fixpoint).
    if name in _TEXT_IDENTICAL:
        assert e2["text"] == e["text"], \
            f"{name}: emit(L) != emit(P)\n{e['text']}\n----\n{e2['text']}"
    e3 = emit_prog_to_llvm(lift2["prog"], fn_name=name.lower(),
                           params=e["params"])
    assert e3["ok"] and e3["text"] == e2["text"], \
        f"{name}: emitted text not a fixpoint"


def test_lifted_loop_has_progwhile_and_carried_inits():
    _e, _s, _out, lift = emit_parse_lift(SUM, "sumto", ["n"])
    txt = json.dumps(lift["prog"])
    assert '"ProgWhile"' in txt
    # the phi resolution: init assigns before the loop, latch copies in
    # the body (the P2 §3 recipe applied)
    stmts = lift["prog"]["stmts"]
    kinds = [st["type"] for st in stmts]
    assert kinds.count("ProgAssignVar") >= 2  # acc/i inits
    assert kinds[-1] == "ProgReturn"


# ---------------------------------------------------------------------------
# 3) THE TRIPLE-AGREEMENT LAW (compiled — few, small)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _HAS_GCC, reason="gcc not available")
@pytest.mark.parametrize("name", ["SUM", "MAX_RET", "IFJOIN",
                                  "IFJOIN_NOELSE"])
def test_triple_agreement(name):
    from domains.x86_64_runner import assemble_and_load
    prog, params, cases = CASES[name]
    fn_name = f"ta_{name.lower()}"
    e = emit_prog_to_llvm(prog, fn_name=fn_name)
    assert e["ok"], e["blockers"]
    s = fresh()
    out = parse_llvm_cfg(s, e["text"],
                         inputs=tuple("%" + p for p in e["params"]))
    asm = emit_x86_64_cfg(s, out["entry_bb"], fn_name,
                          input_nodes=[out["ssa"]["%" + p]
                                       for p in e["params"]])
    compiled = assemble_and_load(asm, fn_name, n_args=len(e["params"]))
    for env, expected in cases:
        r_prog = prog_eval(prog, env)
        assert r_prog["trap"] is None
        r_interp = interpret_cfg(
            s, out["entry_bb"],
            {out["ssa"]["%" + p]: env[p] for p in e["params"]})
        r_native = compiled(*[env[p] for p in e["params"]])
        assert r_prog["result"] == r_interp == r_native == expected, \
            f"{name} {env}: ProgEval={r_prog['result']} " \
            f"interp={r_interp} native={r_native} expected={expected}"


# ---------------------------------------------------------------------------
# 4) the frontier closed: counting loops in the dialect
# ---------------------------------------------------------------------------
def test_counting_loop_interprets_to_values_with_phi():
    # The P2-measured impossibility ("no phi ⇒ every loop runs 0
    # iterations or forever") is CLOSED: this loop text counts.
    text = """
    define i32 @tri(i32 %n) {
    entry:
      br label %h
    h:
      %acc = phi i32 [ 0, %entry ], [ %acc_2, %body ]
      %i = phi i32 [ 0, %entry ], [ %i_2, %body ]
      %t0 = icmp sle i32 %i, %n
      br i1 %t0, label %body, label %exit
    body:
      %acc_2 = add i32 %acc, %i
      %i_2 = add i32 %i, 1
      br label %h
    exit:
      ret i32 %acc
    }
    """
    s = fresh()
    out = parse_llvm_cfg(s, text, inputs=("%n",))
    for n in (0, 1, 7, 12):
        got = interpret_cfg(s, out["entry_bb"], {out["ssa"]["%n"]: n})
        assert got == _py_sum(n), (n, got)
    # and it lifts to a ProgWhile that ProgEval agrees with
    lift = lift_llvm_cfg(s, out)
    assert lift["ok"], lift["blockers"]
    assert '"ProgWhile"' in json.dumps(lift["prog"])
    for n in (0, 7):
        r = prog_eval(lift["prog"], {"n": n})
        assert r["trap"] is None and r["result"] == _py_sum(n)


def test_phi_parse_honesty():
    # phi after a non-phi instruction → invalid
    s = fresh()
    with pytest.raises(ValueError, match="phi must lead"):
        parse_llvm_cfg(s, """
        h:
          %a = add i32 %x, 1
          %p = phi i32 [ 0, %h ], [ 1, %h ]
          ret i32 %p
        """, inputs=("%x",))
    # single incoming → invalid
    s = fresh()
    with pytest.raises(ValueError, match="at least 2"):
        parse_llvm_cfg(s, "h:\n  %p = phi i32 [ 0, %e ]\n  ret i32 %p\n",
                       inputs=())
    # undefined incoming SSA name → invalid
    s = fresh()
    with pytest.raises(ValueError, match="undefined SSA name"):
        parse_llvm_cfg(
            s, "h:\n  %p = phi i32 [ %ghost, %a ], [ 0, %b ]\n"
               "  ret i32 %p\n", inputs=())
    # the single-block parser stays a no-phi dialect (honest residual)
    s = fresh()
    with pytest.raises(ValueError, match="unrecognised"):
        parse_llvm_ir(s, "%p = phi i32 [ 0, %a ], [ 1, %b ]\nret i32 %p\n",
                      inputs=())


def test_phi_outside_supported_pattern_is_refused():
    # A phi in a plain br/ret chain (no loop, no diamond) has no
    # consumer pattern → honest blocker, never a silent mis-lift.
    text = """
    entry:
      br label %m
    m:
      %p = phi i32 [ 0, %entry ], [ 1, %entry ]
      ret i32 %p
    """
    s = fresh()
    out = parse_llvm_cfg(s, text, inputs=())
    lift = lift_llvm_cfg(s, out)
    assert lift["ok"] is False
    assert "phi_outside_supported_pattern" in lift["blockers"]


# ---------------------------------------------------------------------------
# 5) honest emit refusals (scope: integers + structured control flow)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("prog,blocker", [
    (SEQ(P("n"), RET({"type": "ProgCallExtern", "name": "abs",
                      "recv": None, "args": [V("n")]})),
     "unsupported_expr:ProgCallExtern"),
    (SEQ(P("n"), A("x", {"type": "ProgCallExtern", "name": "abs",
                         "recv": None, "args": [V("n")]}), RET(V("x"))),
     "call_extern_unsupported:abs"),
    (SEQ(P("n"), A("x", {"type": "ProgContainerLit", "kind": "list",
                         "items": [L(1)]}), RET(L(0))),
     "unsupported_expr:ProgContainerLit"),
    (SEQ(P("n"), RET(L("hello"))), "non_integer_literal:'hello'"),
    (SEQ(P("n"), {"type": "ProgTryOr", "body": SEQ(RET(L(1))),
                  "exc_var": "e", "handler": SEQ(RET(L(0)))}, RET(L(0))),
     "unsupported_stmt:ProgTryOr"),
    (SEQ(P("n"), WHILE({"type": "Lt", "a": V("n"), "b": L(3)},
                       IF({"type": "Gt", "a": V("n"), "b": L(1)},
                          SEQ(A("n", L(5))))),
         RET(V("n"))), "nested_control_unsupported:loop_body"),
    (SEQ(P("n"), WHILE({"type": "Lt", "a": V("n"), "b": L(3)},
                       RET(V("n"))), RET(V("n"))),
     "return_in_loop_unsupported"),
    (SEQ(P("n"),
         {"type": "ProgForEach", "var": "i", "iter": V("n"),
          "body": A("x", L(1)), "orelse": None},
         RET(L(0))), "foreach_iter_unsupported"),
    (SEQ(P("n"), A("x", L(1))), "missing_return"),
    (SEQ(P("n"), {"type": "ProgAugAssign", "name": "n", "op": "div",
                  "value": L(2)}, RET(V("n"))),
     "augassign_op_unsupported:div"),
    (SEQ(P("n"), RET(V("ghost"))), "unbound_var:ghost"),
])
def test_out_of_scope_hub_ir_is_an_honest_refusal(prog, blocker):
    out = emit_prog_to_llvm(prog, fn_name="r")
    assert out["ok"] is False
    assert out["text"] is None
    assert blocker in out["blockers"], (blocker, out["blockers"])
    # refusals are deterministic too
    assert emit_prog_to_llvm(prog, fn_name="r") == out


def test_foreach_loop_var_is_dropped_after_the_loop():
    # Post-loop, the desugared counter holds `stop`, not the last item
    # (CPython/ProgEval) — the emitter refuses the read instead of
    # silently diverging.
    prog = SEQ(P("n"), A("acc", L(0)),
               {"type": "ProgForEach", "var": "i",
                "iter": {"type": "ProgCallExtern", "name": "range",
                         "recv": None, "args": [V("n")]},
                "body": {"type": "ProgAugAssign", "name": "acc",
                         "op": "add", "value": V("i")},
                "orelse": None},
               RET(V("i")))
    out = emit_prog_to_llvm(prog, fn_name="r")
    assert out["ok"] is False
    assert "unbound_var:i" in out["blockers"]


# ---------------------------------------------------------------------------
# 6) THE P4 ARTIFACT — accepted Programs through the chain
# ---------------------------------------------------------------------------
def _spine_parts():
    # sum 0..n as a COUNT-DOWN loop over the parameter: three parts with
    # DISTINCT statement heads (the P4 lattice connects different labels
    # only — each part used once), shipped SHUFFLED so the order is the
    # corpus bigrams' decision, not the template's.
    return [
        RET(V("acc")),
        {"type": "ProgWhile",
         "cond": {"type": "Gte", "a": V("n"), "b": L(0)},
         "body": SEQ({"type": "ProgAugAssign", "name": "acc",
                      "op": "add", "value": V("n")},
                     {"type": "ProgAugAssign", "name": "n",
                      "op": "sub", "value": L(1)}),
         "orelse": None},
        A("acc", L(0)),
    ]


@pytest.mark.skipif(not _HAS_GCC, reason="gcc not available")
def test_p4_artifact_chain_max_of_two_and_synthesized_loop():
    from domains import prog_synthesis as psy
    from domains.x86_64_runner import assemble_and_load

    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)

    def synthesize(text, examples):
        m = psy.ingest_spec(s, ag, text, examples)
        psy.pump(s, ag)
        goals = s.in_neighbours(m, "about_message")
        assert len(goals) == 1
        return psy.read_goal(s, goals[0])

    def compile_program(r, fn_name, params):
        prog = json.loads(s.node(r["program"])["attrs"]["program"])
        e = emit_prog_to_llvm(prog, fn_name=fn_name)
        assert e["ok"], f"{fn_name}: emit refused: {e['blockers']}"
        assert e["params"] == params
        s2 = fresh()
        out = parse_llvm_cfg(s2, e["text"],
                             inputs=tuple("%" + p for p in params))
        asm = emit_x86_64_cfg(s2, out["entry_bb"], fn_name,
                              input_nodes=[out["ssa"]["%" + p]
                                           for p in params])
        return prog, assemble_and_load(asm, fn_name, n_args=len(params))

    # --- the accepted P4 artifact: max_of_two --------------------------
    r = synthesize(
        "write a function max_of_two that returns the larger of two "
        "numbers",
        [({"a": 2, "b": 9}, 9), ({"a": 7, "b": 3}, 7),
         ({"a": 4, "b": 4}, 4)])
    assert r["status"] == "accepted" and r["construction"] == "max_of_two"
    prog, fn = compile_program(r, "max_of_two", ["a", "b"])
    for env in ({"a": 11, "b": 5}, {"a": -3, "b": 4}, {"a": 6, "b": 6}):
        expected = prog_eval(prog, env)["result"]  # held-out, ProgEval
        assert fn(env["a"], env["b"]) == expected == max(env["a"],
                                                         env["b"])

    # --- a synthesized loop program: sum 0..n --------------------------
    # Taught as a statement-grain spine with SHUFFLED parts; accepted
    # only if the lattice orders them and every example row passes
    # (ProgEval decides — the P4 verify loop, unchanged).
    s.add_node("ShapeSignature", {
        "name": "sum_to_n_spine", "kind": "code_write_construction",
        "signature": json.dumps([["CUMULATIVE"]]),
        "trigger_tokens": ["CUMULATIVE"], "spine": 1.0,
        "ground_template": json.dumps({
            "desc": "returns the cumulative sum from zero to n",
            "mode": "code_write_stmts", "args": ["n"],
            "stmts": _spine_parts()})})
    r2 = synthesize(
        "write a function sum_to_n that is cumulative from zero up to n",
        [({"n": 0}, 0), ({"n": 4}, 10), ({"n": 10}, 55)])
    assert r2["status"] == "accepted", r2
    assert r2["construction"] == "sum_to_n_spine"
    prog2 = json.loads(s.node(r2["program"])["attrs"]["program"])
    # the accepted order is the corpus order, not the shuffled template's
    kinds = [st["type"] for st in prog2["stmts"]]
    assert kinds == ["ProgDefFnParam", "ProgAssignVar", "ProgWhile",
                     "ProgReturn"], kinds
    prog2, fn2 = compile_program(r2, "sum_to_n", ["n"])
    for n in (7, 12, 100):  # held-out
        expected = prog_eval(prog2, {"n": n})["result"]
        assert fn2(n) == expected == _py_sum(n)
