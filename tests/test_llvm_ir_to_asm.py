"""End-to-end: LLVM IR → optimize → x86-64 asm.

These tests verify the agent's codegen pass produces correct x86-64
assembly for its integer-IR subset. The assembly isn't run here
(would require external `as` + `ld` + a process); we verify the EMITTED
SHAPE matches what GCC/clang would produce for the same construct.
"""
from __future__ import annotations

import pytest

from domains.llvm_pass_compiler import install_passes_seed
from domains.compiler_theory_seed import install_compiler_theory_seed
from domains.optimization_pipelines_seed import (
    install_pipelines_seed, run_pipeline_by_name,
)
from domains.llvm_ir_io import parse_llvm_ir
from domains.llvm_ir_to_asm import emit_x86_64_asm


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
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)
    return s


def _ret_root(s):
    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    return s.neighbours(ret_inst, "uses_op0")[0]


# ---------------------------------------------------------------------------
# Direct codegen tests — IR → asm, no optimization between
# ---------------------------------------------------------------------------

def test_constant_function_emits_mov_eax():
    """A function that just returns a constant should be a single
    mov + ret."""
    s = _fresh_substrate()
    parse_llvm_ir(s, "ret i32 42")
    asm = emit_x86_64_asm(s, _ret_root(s), "answer")
    assert ".globl answer" in asm
    assert "movl $42, %eax" in asm
    assert "ret" in asm


def test_add_constant_uses_addl():
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = add i32 %x, 3
        ret i32 %r
    """, inputs=["%x"])
    asm = emit_x86_64_asm(s, _ret_root(s), "addthree", input_node=ssa["%x"])
    # x is in %edi (System V first arg). r = x + 3.
    assert "movl %edi" in asm
    assert "addl $3" in asm


def test_mul_constant_uses_imul_three_operand():
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = mul i32 %x, 7
        ret i32 %r
    """, inputs=["%x"])
    asm = emit_x86_64_asm(s, _ret_root(s), "mul_by_7", input_node=ssa["%x"])
    # imul with immediate src uses the 3-operand form on x86-64.
    assert "imull $7" in asm


def test_shift_constant_uses_immediate():
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = shl i32 %x, 2
        ret i32 %r
    """, inputs=["%x"])
    asm = emit_x86_64_asm(s, _ret_root(s), "shl_2", input_node=ssa["%x"])
    assert "shll $2" in asm


def test_sdiv_uses_idiv_with_cdq():
    """idiv requires sign-extension via cdq before dividing."""
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = sdiv i32 %x, %y
        ret i32 %r
    """, inputs=["%x", "%y"])
    asm = emit_x86_64_asm(
        s, _ret_root(s), "div",
        input_nodes=[ssa["%x"], ssa["%y"]],
    )
    assert "cdq" in asm
    assert "idivl" in asm


def test_icmp_uses_cmp_setcc_movzbl():
    """icmp lowers to cmp + setcc + movzbl (zero-extend the byte)."""
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = icmp slt i32 %x, 10
        ret i1 %r
    """, inputs=["%x"])
    asm = emit_x86_64_asm(s, _ret_root(s), "is_lt_10", input_node=ssa["%x"])
    assert "cmpl $10, %edi" in asm
    assert "setl" in asm
    assert "movzbl" in asm


def test_select_with_runtime_cond_uses_cmov():
    """select with a runtime condition lowers to test + cmov."""
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = select i1 %c, i32 %a, i32 %b
        ret i32 %r
    """, inputs=["%c", "%a", "%b"])
    asm = emit_x86_64_asm(
        s, _ret_root(s), "ternary",
        input_nodes=[ssa["%c"], ssa["%a"], ssa["%b"]],
    )
    assert "testl" in asm
    assert "cmov" in asm  # cmovzl or cmovnzl


# ---------------------------------------------------------------------------
# End-to-end: parse → optimize → codegen
# ---------------------------------------------------------------------------

def test_optimized_chain_lowers_to_two_instructions():
    """`(x + 1) + 2 + ...` collapses via reassoc + constfold, then
    codegen should emit a single addl."""
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %a = add i32 %x, 1
        %b = add i32 %a, 2
        ret i32 %b
    """, inputs=["%x"])
    run_pipeline_by_name(s, "local_peephole")
    asm = emit_x86_64_asm(s, _ret_root(s), "fold_chain",
                          input_node=ssa["%x"])
    # After optimization, only one add remains.
    assert asm.count("addl") == 1
    assert "addl $3" in asm  # 1 + 2 folded


def test_optimized_mul_by_power_of_2_lowers_to_shl():
    """Strength reduction (mul by 4 → shl by 2) produces an asm shift,
    not a multiply."""
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %r = mul i32 %x, 4
        ret i32 %r
    """, inputs=["%x"])
    run_pipeline_by_name(s, "local_peephole")
    asm = emit_x86_64_asm(s, _ret_root(s), "mul_4",
                          input_node=ssa["%x"])
    assert "imull" not in asm  # strength reduction did its job
    assert "shll" in asm


def test_pure_constant_program_lowers_to_single_mov():
    """An entire program that folds to a constant should be one mov +
    one ret — the most aggressive optimization a codegen can demand."""
    s = _fresh_substrate()
    parse_llvm_ir(s, """
        %a = add i32 100, 50
        %b = mul i32 %a, 2
        %c = sub i32 %b, 25
        ret i32 %c
    """)
    run_pipeline_by_name(s, "local_peephole")
    asm = emit_x86_64_asm(s, _ret_root(s), "constant_expr")
    # 100+50=150, *2=300, -25=275
    assert "movl $275, %eax" in asm


def test_branchless_abs_lowers_correctly():
    """The branchless `abs(x)` pattern (icmp+select) lowers to cmp/setcc/
    test/cmov. This is the canonical shape compilers love."""
    s = _fresh_substrate()
    ssa = parse_llvm_ir(s, """
        %neg = sub i32 0, %x
        %is_neg = icmp slt i32 %x, 0
        %r = select i1 %is_neg, i32 %neg, i32 %x
        ret i32 %r
    """, inputs=["%x"])
    run_pipeline_by_name(s, "local_peephole")
    asm = emit_x86_64_asm(s, _ret_root(s), "abs_x",
                          input_node=ssa["%x"])
    assert "subl" in asm
    assert "cmpl" in asm
    assert "cmov" in asm
    assert "ret" in asm
