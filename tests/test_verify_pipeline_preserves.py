"""Verify the optimization pipeline preserves semantics.

For each test program: parse twice (once for the "before" interpretation,
once for the "after" interpretation), interpret both on random inputs,
optimize the second one with `local_peephole`, re-interpret, assert
the values agree. This is **differential testing** — the agent's
abstract validity arguments in `compiler_theory.json` are concrete
demonstrations on this set of programs.

If a future rule change introduces a semantic regression, these tests
catch it on a random input before any LLVM bench would notice.
"""
from __future__ import annotations

import random

import pytest

from domains.llvm_pass_compiler import install_passes_seed
from domains.compiler_theory_seed import install_compiler_theory_seed
from domains.optimization_pipelines_seed import (
    install_pipelines_seed, run_pipeline_by_name,
)
from domains.llvm_ir_io import parse_llvm_ir
from domains.llvm_ir_interp import interpret


_REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
_PASSES = f"{_REPO_ROOT}/seeds/llvm_passes.json"
_THEORY = f"{_REPO_ROOT}/seeds/compiler_theory.json"
_PIPES = f"{_REPO_ROOT}/seeds/optimization_pipelines.json"


def _fresh_substrate_with_passes():
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


def _verify(ir_text: str, inputs: tuple[str, ...] = (),
            num_samples: int = 30, seed: int = 0,
            value_range: tuple[int, int] = (-50, 50)) -> None:
    """Differential test: same `ir_text` interpreted before optimization
    and after `local_peephole` should agree on `num_samples` random
    input bindings.

    `inputs` is the tuple of SSA names treated as function parameters."""
    rng = random.Random(seed)

    for sample in range(num_samples):
        input_values = {name: rng.randint(*value_range) for name in inputs}

        # Before-opt interpretation.
        s_pre = _fresh_substrate_with_passes()
        ssa_pre = parse_llvm_ir(s_pre, ir_text, inputs=list(inputs))
        pre_bindings = {ssa_pre[name]: val
                        for name, val in input_values.items()}
        try:
            v_pre = interpret(s_pre, _ret_root(s_pre), pre_bindings)
        except ZeroDivisionError:
            # Inputs hit a UB case; skip — the optimizer can't promise
            # to preserve behavior of programs that have UB on this
            # input.
            continue

        # After-opt interpretation.
        s_post = _fresh_substrate_with_passes()
        ssa_post = parse_llvm_ir(s_post, ir_text, inputs=list(inputs))
        post_bindings = {ssa_post[name]: val
                         for name, val in input_values.items()}
        run_pipeline_by_name(s_post, "local_peephole")
        v_post = interpret(s_post, _ret_root(s_post), post_bindings)

        assert v_pre == v_post, (
            f"semantic regression on sample {sample}: "
            f"inputs={input_values}, "
            f"before={v_pre}, after={v_post}, "
            f"ir={ir_text!r}"
        )


# ---------------------------------------------------------------------------
# unit tests for the interpreter itself
# ---------------------------------------------------------------------------

def test_interpret_constant_returns_value():
    s = _fresh_substrate_with_passes()
    parse_llvm_ir(s, "ret i32 42")
    assert interpret(s, _ret_root(s), {}) == 42


def test_interpret_add():
    s = _fresh_substrate_with_passes()
    ssa = parse_llvm_ir(s, """
        %r = add i32 %x, 10
        ret i32 %r
    """, inputs=["%x"])
    assert interpret(s, _ret_root(s), {ssa["%x"]: 5}) == 15
    assert interpret(s, _ret_root(s), {ssa["%x"]: -3}) == 7


def test_interpret_signed_division_truncates_toward_zero():
    s = _fresh_substrate_with_passes()
    ssa = parse_llvm_ir(s, """
        %r = sdiv i32 %x, %y
        ret i32 %r
    """, inputs=["%x", "%y"])
    # LLVM sdiv semantics: truncate toward zero.
    assert interpret(s, _ret_root(s), {ssa["%x"]: 10, ssa["%y"]: 3}) == 3
    assert interpret(s, _ret_root(s), {ssa["%x"]: -10, ssa["%y"]: 3}) == -3
    assert interpret(s, _ret_root(s), {ssa["%x"]: 10, ssa["%y"]: -3}) == -3
    assert interpret(s, _ret_root(s), {ssa["%x"]: -10, ssa["%y"]: -3}) == 3


def test_interpret_srem_sign_follows_dividend():
    s = _fresh_substrate_with_passes()
    ssa = parse_llvm_ir(s, """
        %r = srem i32 %x, %y
        ret i32 %r
    """, inputs=["%x", "%y"])
    assert interpret(s, _ret_root(s), {ssa["%x"]: -10, ssa["%y"]: 3}) == -1
    assert interpret(s, _ret_root(s), {ssa["%x"]: 10, ssa["%y"]: -3}) == 1


def test_interpret_div_by_zero_raises():
    s = _fresh_substrate_with_passes()
    ssa = parse_llvm_ir(s, """
        %r = sdiv i32 %x, %y
        ret i32 %r
    """, inputs=["%x", "%y"])
    with pytest.raises(ZeroDivisionError):
        interpret(s, _ret_root(s), {ssa["%x"]: 10, ssa["%y"]: 0})


def test_interpret_icmp():
    s = _fresh_substrate_with_passes()
    ssa = parse_llvm_ir(s, """
        %r = icmp slt i32 %x, %y
        ret i1 %r
    """, inputs=["%x", "%y"])
    assert interpret(s, _ret_root(s), {ssa["%x"]: 3, ssa["%y"]: 10}) == 1
    assert interpret(s, _ret_root(s), {ssa["%x"]: 10, ssa["%y"]: 3}) == 0


def test_interpret_select():
    s = _fresh_substrate_with_passes()
    ssa = parse_llvm_ir(s, """
        %r = select i1 %c, i32 %a, i32 %b
        ret i32 %r
    """, inputs=["%c", "%a", "%b"])
    assert interpret(s, _ret_root(s), {ssa["%c"]: 1, ssa["%a"]: 7, ssa["%b"]: 9}) == 7
    assert interpret(s, _ret_root(s), {ssa["%c"]: 0, ssa["%a"]: 7, ssa["%b"]: 9}) == 9


# ---------------------------------------------------------------------------
# differential tests — the headline capability
# ---------------------------------------------------------------------------

def test_pipeline_preserves_arithmetic_identity_chain():
    """Algebraic identity elimination should not change values."""
    _verify("""
        %a = add i32 %x, 0
        %b = mul i32 %a, 1
        %c = and i32 %b, -1
        %r = or i32 %c, 0
        ret i32 %r
    """, inputs=("%x",))


def test_pipeline_preserves_reassoc_then_constfold():
    """Reassoc + constfold cascade must not change values."""
    _verify("""
        %a = add i32 %x, 1
        %b = add i32 %a, 2
        %c = add i32 %b, 3
        ret i32 %c
    """, inputs=("%x",))


def test_pipeline_preserves_strength_reduction():
    """mul by power-of-2 → shl must preserve values."""
    _verify("""
        %a = mul i32 %x, 4
        %b = mul i32 %a, 8
        ret i32 %b
    """, inputs=("%x",))


def test_pipeline_preserves_cse():
    """CSE must not change values."""
    _verify("""
        %a = add i32 %x, %y
        %b = add i32 %x, %y
        %c = mul i32 %a, %b
        ret i32 %c
    """, inputs=("%x", "%y"))


def test_pipeline_preserves_icmp_select_cascade():
    """The compare-then-choose cascade must preserve all input cases."""
    _verify("""
        %c = icmp slt i32 %x, %y
        %r = select i1 %c, i32 %x, i32 %y
        ret i32 %r
    """, inputs=("%x", "%y"))


def test_pipeline_preserves_select_same_branches():
    """select c, X, X → X must produce X regardless of c."""
    _verify("""
        %r = select i1 %c, i32 %x, i32 %x
        ret i32 %r
    """, inputs=("%c", "%x"), value_range=(0, 1))


def test_pipeline_preserves_division_when_safe():
    """sdiv by non-zero constants folds; verify values match."""
    _verify("""
        %a = sdiv i32 %x, 3
        %b = sdiv i32 %a, 5
        ret i32 %b
    """, inputs=("%x",), value_range=(-100, 100))


def test_pipeline_preserves_complex_program():
    """Many concepts at once: reassoc + constfold + identity + DCE + CSE."""
    _verify("""
        %a = add i32 %x, 1
        %b = add i32 %a, 2
        %c = mul i32 %b, 1
        %d = and i32 %x, -1
        %e = add i32 %c, %d
        ret i32 %e
    """, inputs=("%x",))


def test_pipeline_preserves_pure_constants():
    """Everything-constant programs should fold to a single literal
    whose value matches the unoptimized computation."""
    _verify("""
        %a = add i32 100, 50
        %b = mul i32 %a, 2
        %c = sub i32 %b, 25
        ret i32 %c
    """, inputs=())  # no inputs — constant program
