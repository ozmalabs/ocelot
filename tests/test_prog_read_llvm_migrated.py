"""test_prog_read_llvm_migrated — P2 LLVM-track gates
(PROGRAM_SYNTHESIS_PLAN.md §4-P2: LLVM IR becomes a READ frame of the
P1 hub Program IR).

Gates:

  THE AGREEMENT LAW — lift (domains/prog_ir_llvm.py) → ProgEval vs the
    EXISTING trusted oracle (domains/llvm_ir_interp.interpret /
    llvm_ir_cfg.interpret_cfg — already trusted by
    test_codegen_matches_interpreter) on the same inputs: identical
    results on every in-scope fixture. The CPython-agreement analogue.

  STRUCTURED PATTERNS — the if-diamond lifts to ProgIfStmt, the
    single-latch loop to ProgWhile (structural asserts + agreement).

  HONEST RESIDUALS — irreducible CFG → blockers ["unstructured_cfg"];
    dominance-violating join reads → "join_reads_branch_value" (the
    oracle back-computes those values path-independently; the lifted
    program would trap name:<n> — refusing beats silently diverging);
    unsigned icmp → "unsupported_opcode:icmp_ult" (matched to the
    oracle's own refusal); `call` in .ll text → parse-layer ValueError
    (neither existing parser speaks call — the correspondence row is
    gated graph-level instead).

  LOOP SEMANTICS WITHOUT PHI — the dialect has no phi (llvm_ir_io.py
    header), so loops run 0 iterations or forever. Zero-iteration
    inputs gate exact agreement; looping inputs gate agreement-of-
    refusal (interp RuntimeError max_steps ⟷ ProgEval fuel trap,
    halted False, never a value).

  REFLECT ROUND-TRIP on a lifted program; DETERMINISM (two fresh
    parse+lift runs → byte-identical JSON); the correspondence seed
    LOADS CLEAN via load_seed_manifest and the table read back from
    the graph equals the file's.

Documented divergences (fixtures respect them; see
PROGRAM_SYNTHESIS_P2_LLVM.md): sdiv/srem by ZERO (oracle raises
ZeroDivisionError = LLVM UB surfaced; IDiv/IRem return silent 0);
i64 wrap on add/sub/mul overflow (oracle wraps; DSL arithmetic
doesn't); lshr-by-0 of a negative value.

Run: pytest tests/test_prog_read_llvm_migrated.py --confcutdir=. -q
(the worktree-engine seam — P1 notes §6).
"""
from __future__ import annotations

import json
import os
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
from domains.llvm_ir_interp import interpret
from domains.llvm_ir_io import parse_llvm_ir
from domains.prog_ir_llvm import (
    SEED_PATH, lift_llvm_block, lift_llvm_cfg, load_correspondence,
)

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "fixtures", "prog_ir_read_llvm")


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
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
        "stale engine (P1 notes §6: rebuild + sync _native.abi3.so). "
        "Honest skip, not a fake pass.",
        allow_module_level=True)


def fresh():
    """Substrate with the LLVM grammar opened (the test_llvm_ir_cfg
    pattern) — mechanical setup, no passes/pipelines needed here."""
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


def read_fixture(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def prog_eval(prog, env=None, oracles=None, fuel=5000):
    s = srs.Substrate()
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": prog,
         "env": {"type": "Var", "name": "envd"} if env else None,
         "oracles": oracles, "fuel": fuel, "field": ""},
        {"envd": env} if env else None)
    assert isinstance(out, dict)
    return out


def _oracles(*names):
    items = []
    for n in names:
        items += [{"type": "Lit", "value": n}, {"type": "Lit", "value": "builtin"}]
    return {"type": "MkDict", "items": items}


def lift_block_fixture(name: str, inputs: tuple[str, ...]):
    s = fresh()
    ssa = parse_llvm_ir(s, read_fixture(name), inputs=inputs)
    return s, ssa, lift_llvm_block(s, ssa)


def lift_cfg_fixture(name: str, inputs: tuple[str, ...]):
    s = fresh()
    out = parse_llvm_cfg(s, read_fixture(name), inputs=inputs)
    return s, out, lift_llvm_cfg(s, out)


def assert_block_agreement(name, inputs, cases):
    """THE LAW, single-block form: ProgEval(lift) ≡ llvm_ir_interp."""
    s, ssa, lift = lift_block_fixture(name, inputs)
    assert lift["ok"], f"{name}: lift blocked: {lift['blockers']}"
    for case in cases:
        expected = interpret(s, ssa["__return__"],
                             {ssa[k]: v for k, v in case.items()})
        env = {k.lstrip("%"): v for k, v in case.items()}
        out = prog_eval(lift["prog"], env=env)
        assert out["trap"] is None and out["halted"] is True, \
            f"{name} {case}: trap={out['trap']}"
        assert out["result"] == expected, \
            f"{name} {case}: lift={out['result']} oracle={expected}"


def assert_cfg_agreement(name, inputs, cases):
    """THE LAW, CFG form: ProgEval(lift) ≡ interpret_cfg."""
    s, pout, lift = lift_cfg_fixture(name, inputs)
    assert lift["ok"], f"{name}: lift blocked: {lift['blockers']}"
    for case in cases:
        expected = interpret_cfg(s, pout["entry_bb"],
                                 {pout["ssa"][k]: v for k, v in case.items()})
        env = {k.lstrip("%"): v for k, v in case.items()}
        out = prog_eval(lift["prog"], env=env)
        assert out["trap"] is None and out["halted"] is True, \
            f"{name} {case}: trap={out['trap']}"
        assert out["result"] == expected, \
            f"{name} {case}: lift={out['result']} oracle={expected}"
    return lift


def stmt_types(obj, out=None):
    out = out if out is not None else set()
    if isinstance(obj, dict):
        t = obj.get("type")
        if isinstance(t, str):
            out.add(t)
        for v in obj.values():
            stmt_types(v, out)
    elif isinstance(obj, list):
        for v in obj:
            stmt_types(v, out)
    return out


# ---------------------------------------------------------------------------
# 0) the seed loads clean; graph-held table ≡ file table
# ---------------------------------------------------------------------------
def test_seed_loads_clean_and_table_round_trips():
    with open(SEED_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    s = srs.Substrate()
    summary = s.load_seed_manifest(manifest)
    assert summary["nodes"] == len(manifest["nodes"])
    from_graph = load_correspondence(s)
    from_file = load_correspondence(None)
    assert from_graph == from_file
    # Every expr row's template is valid Term-JSON.
    for opcode, row in from_file.items():
        if row["kind"] == "expr":
            tpl = json.loads(row["template"])
            assert isinstance(tpl, dict) and "type" in tpl, opcode


# ---------------------------------------------------------------------------
# 1) single-block lifts + THE AGREEMENT LAW
# ---------------------------------------------------------------------------
def test_straightline_arith_agrees():
    assert_block_agreement(
        "straight_arith.ll", ("%x", "%y"),
        [{"%x": 3, "%y": 4}, {"%x": -7, "%y": 2}, {"%x": 0, "%y": 0},
         {"%x": 100, "%y": -41}])


def test_bitops_agree():
    assert_block_agreement(
        "bitops.ll", ("%x", "%y"),
        [{"%x": 13, "%y": 6}, {"%x": 255, "%y": 129},
         {"%x": 0, "%y": 0}, {"%x": 4096, "%y": 15}])


def test_divrem_agrees_on_nonzero_divisors():
    # Truncate-toward-zero + sign-of-dividend remainder: EXACT agreement.
    # Divisor 0 is the documented divergence (oracle raises LLVM-UB;
    # IDiv/IRem return silent 0) — fixture-avoided by design.
    assert_block_agreement(
        "divrem.ll", ("%x", "%y"),
        [{"%x": -7, "%y": 2}, {"%x": 7, "%y": -2},
         {"%x": 9, "%y": 4}, {"%x": -9, "%y": -4}, {"%x": 0, "%y": 5}])


def test_icmp_select_agrees():
    assert_block_agreement(
        "icmp_select.ll", ("%x",),
        [{"%x": -5}, {"%x": 0}, {"%x": 55}, {"%x": 100}, {"%x": 250}])


def test_icmp_result_is_in_frame_integer():
    # ret of a bare icmp: the lift must yield 0/1 ints (i1 in-frame),
    # exactly the oracle's 0/1 — not Bools.
    s, ssa, lift = lift_block_fixture("icmp_ret.ll", ("%x",))
    assert lift["ok"], lift["blockers"]
    for x in (-3, 0, 3):
        expected = interpret(s, ssa["__return__"], {ssa["%x"]: x})
        out = prog_eval(lift["prog"], env={"x": x})
        assert out["result"] == expected
        assert isinstance(out["result"], int) and not isinstance(out["result"], bool)


# ---------------------------------------------------------------------------
# 2) CFG structured patterns + THE LAW
# ---------------------------------------------------------------------------
def test_diamond_ret_lifts_to_progifstmt_and_agrees():
    lift = assert_cfg_agreement(
        "diamond_ret.ll", ("%x",),
        [{"%x": 10}, {"%x": 60}, {"%x": 49}, {"%x": 50}, {"%x": -5}])
    assert "ProgIfStmt" in stmt_types(lift["prog"])
    assert "ProgWhile" not in stmt_types(lift["prog"])


def test_diamond_join_lifts_and_agrees():
    lift = assert_cfg_agreement(
        "diamond_join.ll", ("%x",),
        [{"%x": 0}, {"%x": 4}, {"%x": 100}, {"%x": -9}])
    assert "ProgIfStmt" in stmt_types(lift["prog"])


def test_single_latch_loop_lifts_to_progwhile_zero_iteration_agreement():
    # No phi in the dialect → the loop is 0-iteration or infinite.
    # Zero-iteration inputs (x >= 10): exact agreement.
    lift = assert_cfg_agreement(
        "loop_single_latch.ll", ("%x",),
        [{"%x": 10}, {"%x": 42}, {"%x": 1000}])
    assert "ProgWhile" in stmt_types(lift["prog"])


def test_nonterminating_loop_both_engines_refuse():
    # Looping inputs (x < 10): agreement-of-refusal. The oracle hits
    # max_steps (RuntimeError); ProgEval exhausts fuel — halted False,
    # trap "fuel", steps == fuel, NEVER a value.
    s, pout, lift = lift_cfg_fixture("loop_single_latch.ll", ("%x",))
    assert lift["ok"], lift["blockers"]
    with pytest.raises(RuntimeError, match="steps"):
        interpret_cfg(s, pout["entry_bb"], {pout["ssa"]["%x"]: 3},
                      max_steps=500)
    out = prog_eval(lift["prog"], env={"x": 3}, fuel=64)
    assert out["halted"] is False
    assert out["trap"] == "fuel"
    assert out["steps"] == 64
    assert out["result"] is None


# ---------------------------------------------------------------------------
# 3) call — correspondence row (graph-level) + parse-layer residual
# ---------------------------------------------------------------------------
def test_call_ll_is_an_honest_parse_residual():
    # Neither existing parser speaks `call` — scope is exactly what the
    # io/cfg modules produce, so the .ll form fails AT PARSE, honestly.
    s = fresh()
    with pytest.raises(ValueError, match="unrecognised"):
        parse_llvm_ir(s, read_fixture("call.ll"), inputs=("%x",))


def test_graph_level_call_lifts_to_progcallextern():
    # The correspondence row lifts a graph-built call instruction
    # (mechanical node/edge construction — the only way a call node can
    # exist in this dialect today).
    s = fresh()
    x = s.add_node("LLVMValue", {"type": "i32"})
    inst = s.add_node("LLVMInstruction", {"opcode": "call", "callee": "abs"})
    r = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(inst, "uses_op0", x, {})
    s.add_edge(inst, "produces", r, {})
    ssa = {"%x": x, "%r": r, "__return__": r}
    lift = lift_llvm_block(s, ssa)
    assert lift["ok"], lift["blockers"]
    types = stmt_types(lift["prog"])
    assert "ProgCallExtern" in types
    calls = [st for st in lift["prog"]["stmts"]
             if st["type"] == "ProgAssignVar"
             and st["value"].get("type") == "ProgCallExtern"]
    assert calls and calls[0]["value"]["name"] == "abs"
    # Declared oracle → evaluates natively; undeclared → extern trap.
    ok = prog_eval(lift["prog"], env={"x": -5}, oracles=_oracles("abs"))
    assert ok["trap"] is None and ok["result"] == 5
    bad = prog_eval(lift["prog"], env={"x": -5})
    assert bad["halted"] is False and bad["trap"] == "extern:abs"
    assert bad["result"] is None


# ---------------------------------------------------------------------------
# 4) honest residuals
# ---------------------------------------------------------------------------
def test_unstructured_cfg_is_an_honest_residual():
    s, pout, lift = lift_cfg_fixture("unstructured.ll", ("%x",))
    assert lift["ok"] is False
    assert lift["prog"] is None
    assert "unstructured_cfg" in lift["blockers"]


def test_join_reading_a_branch_value_is_refused_not_diverged():
    # The oracle back-computes %da regardless of the executed path; the
    # lifted program would trap name:da on the b path. Refuse, honestly.
    s, pout, lift = lift_cfg_fixture("join_reads_branch.ll", ("%x",))
    assert lift["ok"] is False
    assert "join_reads_branch_value" in lift["blockers"]


def test_unsigned_icmp_refused_matching_the_oracle():
    s, ssa, lift = lift_block_fixture("icmp_ult.ll", ("%x", "%y"))
    assert lift["ok"] is False
    assert "unsupported_opcode:icmp_ult" in lift["blockers"]
    # The oracle's frontier is the same line.
    with pytest.raises(ValueError, match="unsupported opcode"):
        interpret(s, ssa["__return__"], {ssa["%x"]: 1, ssa["%y"]: 2})


# ---------------------------------------------------------------------------
# 5) reflect round-trip + determinism
# ---------------------------------------------------------------------------
def _canon(d):
    """Canonical form: drop null-valued fields (absent optional child ≡
    explicit null in the wire dialect) recursively."""
    if isinstance(d, dict):
        return {k: _canon(v) for k, v in d.items() if v is not None}
    if isinstance(d, list):
        return [_canon(x) for x in d]
    return d


def test_lifted_program_reflect_round_trips():
    _s, _pout, lift = lift_cfg_fixture("diamond_ret.ll", ("%x",))
    assert lift["ok"]
    sub = srs.Substrate()
    nid = sub._inner.add_term_subgraph(lift["prog"])
    c1 = json.loads(sub._inner.term_subgraph_json(nid))
    assert c1["type"] == "ProgSeq"
    assert _canon(c1) == _canon(lift["prog"])
    nid2 = sub._inner.add_term_subgraph(c1)
    c2 = json.loads(sub._inner.term_subgraph_json(nid2))
    assert c2 == c1


@pytest.mark.parametrize("name,inputs,mode", [
    ("straight_arith.ll", ("%x", "%y"), "block"),
    ("diamond_ret.ll", ("%x",), "cfg"),
    ("loop_single_latch.ll", ("%x",), "cfg"),
])
def test_lift_is_deterministic(name, inputs, mode):
    def one():
        if mode == "block":
            _s, _ssa, lift = lift_block_fixture(name, inputs)
        else:
            _s, _pout, lift = lift_cfg_fixture(name, inputs)
        assert lift["ok"], lift["blockers"]
        return json.dumps(lift["prog"], sort_keys=True)

    assert one() == one()
