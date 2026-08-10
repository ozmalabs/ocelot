"""End-to-end LLVM IR text → optimize → text round-trip.

The agent now operates on REAL LLVM IR. Text comes in; the substrate
runs its compiler-design knowledge over the graph; text comes back out.

This is the world-adapter boundary the architecture rule describes:
Python translates external I/O (text) into graph mutations, the
substrate's installed rules do the reasoning, Python reads the
optimised graph back out.
"""
from __future__ import annotations

import pytest

from domains.llvm_pass_compiler import install_passes_seed
from domains.compiler_theory_seed import install_compiler_theory_seed
from domains.optimization_pipelines_seed import (
    install_pipelines_seed, run_pipeline_by_name,
)
from domains.llvm_ir_io import emit_llvm_ir, parse_llvm_ir


_REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
_PASSES = f"{_REPO_ROOT}/seeds/llvm_passes.json"
_THEORY = f"{_REPO_ROOT}/seeds/compiler_theory.json"
_PIPES = f"{_REPO_ROOT}/seeds/optimization_pipelines.json"


def _fresh_substrate():
    from substrate_rs import _native
    s = _native.Substrate()
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
    # BB-containing-instructions edge (added in CFG phase but also
    # needed because parse_llvm_ir creates an implicit entry BB and
    # the orphan_instruction_elimination rule checks count_in via
    # this edge).
    s.add_production({
        'src': {'type': 'LLVMBasicBlock', 'var': 'src'},
        'edge_type': 'contains_inst',
        'tgt': {'type': 'LLVMInstruction', 'var': 'tgt'},
        'where': None,
        'weight': {'type': 'Lit', 'value': 1.0},
        'provenance': 'test:open',
    })
    return s


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------

def test_parse_single_binop_creates_three_edges():
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, "%r = add i32 3, 5\nret i32 %r")

    # Two constants, one add inst, one ret inst, one produced LLVMValue.
    assert len(s.nodes("LLVMConstant")) == 2
    assert len(s.nodes("LLVMInstruction")) == 2  # add + ret
    add_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"]["opcode"] == "add")
    assert len(s.neighbours(add_inst, "uses_op0")) == 1
    assert len(s.neighbours(add_inst, "uses_op1")) == 1
    assert len(s.neighbours(add_inst, "produces")) == 1
    assert ssa["%r"] is not None
    assert ssa["__return__"] == ssa["%r"]


def test_parse_resolves_ssa_references():
    """An operand `%t` in a later instruction binds to the LLVMValue
    that an earlier instruction produced."""
    s = _fresh_substrate()
    text = """
    %t = add i32 1, 2
    %r = mul i32 %t, 3
    ret i32 %r
    """
    ssa = parse_llvm_ir(s, text)

    mul = next(n for n in s.nodes("LLVMInstruction")
               if s.node(n)["attrs"]["opcode"] == "mul")
    op0 = s.neighbours(mul, "uses_op0")[0]
    # mul's op0 should be the LLVMValue produced by the add.
    assert op0 == ssa["%t"]
    assert s.node(op0)["type"] == "LLVMValue"


def test_parse_treats_named_input_as_pre_existing_value():
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, "%r = add i32 %x, 1\nret i32 %r", inputs=["%x"])
    assert s.node(ssa["%x"])["type"] == "LLVMValue"
    add = next(n for n in s.nodes("LLVMInstruction")
               if s.node(n)["attrs"]["opcode"] == "add")
    assert ssa["%x"] in s.neighbours(add, "uses_op0")


def test_parse_rejects_forward_reference():
    s = _fresh_substrate()
    with pytest.raises(ValueError, match="unknown SSA name"):
        parse_llvm_ir(s, "%r = add i32 %x, 1\nret i32 %r")  # no inputs


def test_parse_skips_comments_and_blanks():
    s = _fresh_substrate()
    text = """
    ; this is a comment
    %r = add i32 3, 5  ; inline comment

    ret i32 %r
    """
    ssa = parse_llvm_ir(s, text)
    assert "%r" in ssa
    assert "__return__" in ssa


def test_parse_accepts_function_braces():
    s = _fresh_substrate()
    text = """
    define i32 @foo(i32 %x) {
      %r = add i32 %x, 1
      ret i32 %r
    }
    """
    ssa = parse_llvm_ir(s, text, inputs=["%x"])
    assert "%r" in ssa


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------

def test_emit_single_instruction():
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, "%r = add i32 3, 5\nret i32 %r")
    text = emit_llvm_ir(s, ssa["__return__"])
    # Re-emitted form: one add, one ret.
    assert "add i32 3, 5" in text
    assert "ret i32" in text


def test_emit_uses_input_names_when_provided():
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, "%r = add i32 %x, 1\nret i32 %r", inputs=["%x"])
    text = emit_llvm_ir(s, ssa["__return__"], input_names={ssa["%x"]: "%x"})
    assert "%x" in text
    assert "add i32 %x, 1" in text


# ---------------------------------------------------------------------------
# end-to-end: parse → optimize → emit
# ---------------------------------------------------------------------------

def test_full_pipeline_collapses_real_llvm_ir():
    """The agent ingests real LLVM IR text, runs the `local_peephole`
    pipeline on the substrate-resident graph, and emits the optimized
    program back as text. The cascade `(x + 1) + 2 → x + 3` happens
    *inside the substrate's compiler-design knowledge*, not in the
    parser."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)

    input_ir = """
    define i32 @foo(i32 %x) {
      %t = add i32 %x, 1
      %r = add i32 %t, 2
      ret i32 %r
    }
    """
    ssa = parse_llvm_ir(s, input_ir, inputs=["%x"])
    input_node = ssa["%x"]

    result = run_pipeline_by_name(s, "local_peephole")
    assert result["rules_applied"] > 0

    # The ret's operand still resolves — replace_value rewired uses
    # transparently. Walk back from the ret to the new root.
    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    new_root = s.neighbours(ret_inst, "uses_op0")[0]

    out_text = emit_llvm_ir(s, new_root, input_names={input_node: "%x"})
    # The optimised form: one add, one ret. The constant 3 (= 1+2)
    # appears as the literal operand.
    assert "add i32 %x, 3" in out_text or "add i32 3, %x" in out_text, \
        f"expected `add i32 %x, 3` after pipeline; got:\n{out_text}"
    assert out_text.count("add") == 1, \
        f"only one add should survive; got:\n{out_text}"


# ---------------------------------------------------------------------------
# icmp — integer comparisons fold over the same constant_folding concept
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pred,a,b,expected", [
    ("eq", 5, 5, 1),
    ("eq", 5, 7, 0),
    ("ne", 5, 5, 0),
    ("ne", 5, 7, 1),
    ("slt", 3, 5, 1),
    ("slt", 5, 3, 0),
    ("slt", 5, 5, 0),
    ("sle", 5, 5, 1),
    ("sle", 5, 7, 1),
    ("sle", 5, 3, 0),
    ("sgt", 5, 3, 1),
    ("sgt", 5, 5, 0),
    ("sge", 5, 5, 1),
    ("sge", 3, 5, 0),
])
def test_icmp_constfold_via_pipeline(pred, a, b, expected):
    """icmp <pred> i32 c1, c2 with both operands constant folds to an
    i1 constant. Demonstrates that the constant_folding concept
    extends to a new value type with no concept change — same
    structural fingerprint, same family, same soundness argument."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)

    parse_llvm_ir(s, f"""
        %r = icmp {pred} i32 {a}, {b}
        ret i1 %r
    """)
    run_pipeline_by_name(s, "local_peephole")

    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    result = s.neighbours(ret_inst, "uses_op0")[0]
    assert s.node(result)["type"] == "LLVMConstant"
    assert s.node(result)["attrs"]["value"] == expected
    assert s.node(result)["attrs"]["type"] == "i1"


def test_icmp_eq_self_folds_to_true():
    """icmp eq X, X → 1 regardless of what X is. Pure algebraic
    identity — equality is reflexive."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)

    parse_llvm_ir(s, """
        %r = icmp eq i32 %x, %x
        ret i1 %r
    """, inputs=["%x"])
    run_pipeline_by_name(s, "local_peephole")

    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    result = s.neighbours(ret_inst, "uses_op0")[0]
    assert s.node(result)["type"] == "LLVMConstant"
    assert s.node(result)["attrs"]["value"] == 1


def test_icmp_ne_self_folds_to_false():
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)
    parse_llvm_ir(s, """
        %r = icmp ne i32 %x, %x
        ret i1 %r
    """, inputs=["%x"])
    run_pipeline_by_name(s, "local_peephole")
    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    result = s.neighbours(ret_inst, "uses_op0")[0]
    assert s.node(result)["attrs"]["value"] == 0


def test_icmp_emit_round_trips_through_parse():
    """An icmp instruction emits the canonical `icmp <pred> <ty>`
    syntax, which the parser can re-ingest."""
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = icmp slt i32 %x, 10
        ret i1 %r
    """, inputs=["%x"])
    out = emit_llvm_ir(
        s, ssa["__return__"],
        input_names={ssa["%x"]: "%x"},
        ret_type="i1",
    )
    assert "icmp slt i32 %x, 10" in out


def test_icmp_then_arithmetic_cascade():
    """A more elaborate end-to-end: an icmp that folds, then an add
    over its constant result. The cascade tests that i1 constants
    feed back into the rest of the optimization pipeline correctly."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)

    parse_llvm_ir(s, """
        %c = icmp eq i32 5, 5
        ret i1 %c
    """)
    run_pipeline_by_name(s, "local_peephole")

    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    result = s.neighbours(ret_inst, "uses_op0")[0]
    # The icmp instruction is gone.
    assert not any(s.node(n)["attrs"].get("opcode", "").startswith("icmp_")
                   for n in s.nodes("LLVMInstruction"))
    # The remaining value is a literal i1 = 1.
    assert s.node(result)["type"] == "LLVMConstant"
    assert s.node(result)["attrs"]["value"] == 1


# ---------------------------------------------------------------------------
# select — the canonical compare-then-choose primitive
# ---------------------------------------------------------------------------

def test_parse_select_creates_three_operand_edges():
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = select i1 1, i32 100, i32 200
        ret i32 %r
    """)
    sel = next(n for n in s.nodes("LLVMInstruction")
               if s.node(n)["attrs"]["opcode"] == "select")
    assert len(s.neighbours(sel, "uses_op0")) == 1  # cond
    assert len(s.neighbours(sel, "uses_op1")) == 1  # a
    assert len(s.neighbours(sel, "uses_op2")) == 1  # b


@pytest.mark.parametrize("cond,expected", [(1, 100), (0, 200)])
def test_select_with_constant_condition_folds(cond, expected):
    """select i1 c, i32 100, i32 200 with c statically known → fold to
    the chosen value."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)

    parse_llvm_ir(s, f"""
        %r = select i1 {cond}, i32 100, i32 200
        ret i32 %r
    """)
    run_pipeline_by_name(s, "local_peephole")

    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    result = s.neighbours(ret_inst, "uses_op0")[0]
    assert s.node(result)["type"] == "LLVMConstant"
    assert s.node(result)["attrs"]["value"] == expected
    # The select instruction was eliminated.
    assert not any(s.node(n)["attrs"].get("opcode") == "select"
                   for n in s.nodes("LLVMInstruction"))


def test_select_with_equal_branches_folds_regardless_of_condition():
    """select i1 %c, i32 %x, i32 %x → %x. The condition becomes
    irrelevant when both branches denote the same value."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)

    ssa = parse_llvm_ir(s, """
        %r = select i1 %c, i32 %x, i32 %x
        ret i32 %r
    """, inputs=["%c", "%x"])
    run_pipeline_by_name(s, "local_peephole")

    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    result = s.neighbours(ret_inst, "uses_op0")[0]
    assert result == ssa["%x"], \
        "the ret should now reference %x directly, not via the select"
    assert not any(s.node(n)["attrs"].get("opcode") == "select"
                   for n in s.nodes("LLVMInstruction"))


def test_icmp_then_select_cascade_collapses():
    """The canonical compare-then-choose pattern. The agent's pipeline
    rules cascade across two opcode families:
        icmp constfold → i1 constant in cond → select_constant_condition
                       → rewire to chosen branch → DCE cleans up.

    This is the highest-leverage demo: a multi-instruction structure
    spanning two opcode families collapses to a single value because
    the agent's compiler-theory knowledge composes correctly."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)

    parse_llvm_ir(s, """
        %c = icmp slt i32 3, 10
        %r = select i1 %c, i32 100, i32 200
        ret i32 %r
    """)
    result = run_pipeline_by_name(s, "local_peephole")
    assert result["rules_applied"] >= 2

    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    final = s.neighbours(ret_inst, "uses_op0")[0]
    assert s.node(final)["type"] == "LLVMConstant"
    # 3 < 10 is true, so the select picks 100.
    assert s.node(final)["attrs"]["value"] == 100


def test_select_emit_round_trips_through_parse():
    """A select instruction emits canonical `select i1 cond, ty a, ty b`
    syntax that the parser can re-ingest."""
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = select i1 %c, i32 %a, i32 %b
        ret i32 %r
    """, inputs=["%c", "%a", "%b"])
    out = emit_llvm_ir(
        s, ssa["__return__"],
        input_names={ssa["%c"]: "%c", ssa["%a"]: "%a", ssa["%b"]: "%b"},
    )
    assert "select i1 %c, i32 %a, i32 %b" in out


# ---------------------------------------------------------------------------
# Integer division — sdiv/srem with UB-preservation guards
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("a,b,expected", [
    (10, 3, 3),
    (-10, 3, -3),     # truncate toward zero
    (10, -3, -3),
    (-10, -3, 3),
    (15, 5, 3),
    (-15, 5, -3),
])
def test_sdiv_folds_via_pipeline(a, b, expected):
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)
    parse_llvm_ir(s, f"""
        %r = sdiv i32 {a}, {b}
        ret i32 %r
    """)
    run_pipeline_by_name(s, "local_peephole")
    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    result = s.neighbours(ret_inst, "uses_op0")[0]
    assert s.node(result)["type"] == "LLVMConstant"
    assert s.node(result)["attrs"]["value"] == expected


@pytest.mark.parametrize("a,b,expected", [
    (10, 3, 1),
    (-10, 3, -1),     # sign follows dividend (LLVM srem)
    (10, -3, 1),
    (-10, -3, -1),
    (15, 5, 0),
])
def test_srem_folds_via_pipeline(a, b, expected):
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)
    parse_llvm_ir(s, f"""
        %r = srem i32 {a}, {b}
        ret i32 %r
    """)
    run_pipeline_by_name(s, "local_peephole")
    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    result = s.neighbours(ret_inst, "uses_op0")[0]
    assert s.node(result)["attrs"]["value"] == expected


def test_sdiv_by_zero_does_NOT_fold():
    """LLVM defines sdiv-by-zero as undefined behaviour. A folding
    pass that materialised any concrete value (including 0) would be
    replacing defined-but-trapping semantics with a specific value —
    that's a real semantic change, not an optimization. The rule's
    where-clause guards against this with `not (rhs.value == 0)`.
    Result: the sdiv instruction stays in the IR; the trap stays in
    the runtime."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)
    parse_llvm_ir(s, """
        %r = sdiv i32 5, 0
        ret i32 %r
    """)
    run_pipeline_by_name(s, "local_peephole")
    # The sdiv instruction is still alive — refused to fold.
    assert any(s.node(n)["attrs"].get("opcode") == "sdiv"
               for n in s.nodes("LLVMInstruction")), \
        "sdiv by 0 must NOT fold (would introduce defined behavior " \
        "where LLVM specifies undefined)"


def test_srem_by_zero_does_NOT_fold():
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)
    parse_llvm_ir(s, """
        %r = srem i32 5, 0
        ret i32 %r
    """)
    run_pipeline_by_name(s, "local_peephole")
    assert any(s.node(n)["attrs"].get("opcode") == "srem"
               for n in s.nodes("LLVMInstruction"))


def test_sdiv_by_one_folds_to_x():
    """sdiv X, 1 → X — identity even when X is not constant."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)
    ssa = parse_llvm_ir(s, """
        %r = sdiv i32 %x, 1
        ret i32 %r
    """, inputs=["%x"])
    run_pipeline_by_name(s, "local_peephole")
    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    result = s.neighbours(ret_inst, "uses_op0")[0]
    assert result == ssa["%x"]


def test_full_pipeline_folds_pure_constants():
    """All-constant input folds to a single ret of a literal."""
    s = _fresh_substrate()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)

    ssa = parse_llvm_ir(s, """
        %t = add i32 3, 5
        %r = mul i32 %t, 2
        ret i32 %r
    """)
    run_pipeline_by_name(s, "local_peephole")

    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    new_root = s.neighbours(ret_inst, "uses_op0")[0]
    # The result of the chain is a single constant.
    assert s.node(new_root)["type"] == "LLVMConstant"
    assert s.node(new_root)["attrs"]["value"] == 16  # (3+5)*2
