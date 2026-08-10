"""End-to-end CFG codegen verification.

Same shape as `test_codegen_matches_interpreter.py` but for multi-BB
programs: parse → interpret on random inputs → optimize → emit
multi-BB x86-64 → assemble → load → execute → assert results match.

The agent's full toolchain (parser + optimizer + codegen + assembler
+ runner) now closes the loop for control flow programs too.
"""
from __future__ import annotations

import random
import shutil

import pytest

from domains.llvm_pass_compiler import install_passes_seed
from domains.compiler_theory_seed import install_compiler_theory_seed
from domains.optimization_pipelines_seed import (
    install_pipelines_seed, run_pipeline_by_name,
)
from domains.llvm_ir_cfg import (
    install_cfg_productions, interpret_cfg, parse_llvm_cfg,
)
from domains.llvm_ir_cfg_to_asm import emit_x86_64_cfg


_REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
_PASSES = f"{_REPO_ROOT}/seeds/llvm_passes.json"
_THEORY = f"{_REPO_ROOT}/seeds/compiler_theory.json"
_PIPES = f"{_REPO_ROOT}/seeds/optimization_pipelines.json"


if shutil.which("gcc") is None:
    pytest.skip("gcc not available", allow_module_level=True)

from domains.x86_64_runner import assemble_and_load  # noqa: E402


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
    install_cfg_productions(s)
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)
    return s


def _i32_wrap(v: int) -> int:
    v = v & 0xFFFFFFFF
    return v - (1 << 32) if v >= (1 << 31) else v


def _verify_cfg_codegen(ir_text: str, fn_name: str,
                        inputs: tuple[str, ...],
                        num_samples: int = 20,
                        seed: int = 0,
                        value_range: tuple[int, int] = (-50, 50)) -> None:
    rng = random.Random(seed)

    s_interp = _fresh_substrate()
    out_interp = parse_llvm_cfg(s_interp, ir_text, inputs=inputs)

    s_cg = _fresh_substrate()
    out_cg = parse_llvm_cfg(s_cg, ir_text, inputs=inputs)
    run_pipeline_by_name(s_cg, "local_peephole")
    asm = emit_x86_64_cfg(
        s_cg, out_cg["entry_bb"], fn_name,
        input_nodes=[out_cg["ssa"][n] for n in inputs],
    )
    compiled = assemble_and_load(asm, fn_name, n_args=len(inputs))

    for sample in range(num_samples):
        vals = [rng.randint(*value_range) for _ in inputs]
        bindings = {out_interp["ssa"][n]: v for n, v in zip(inputs, vals)}
        expected = interpret_cfg(s_interp, out_interp["entry_bb"], bindings)
        expected_wrapped = _i32_wrap(expected)
        actual = compiled(*vals)
        assert expected_wrapped == actual, (
            f"sample {sample}: inputs={dict(zip(inputs, vals))}, "
            f"interp={expected_wrapped}, compiled={actual}\n"
            f"asm:\n{asm}"
        )


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_unconditional_branch_chain():
    _verify_cfg_codegen("""
        define i32 @inc(i32 %x) {
        entry:
          br label %mid
        mid:
          %v = add i32 %x, 1
          br label %end
        end:
          ret i32 %v
        }
    """, "inc", inputs=("%x",))


def test_conditional_branch_chooses_correctly():
    """`sign(x)` returns -1 for negative x, +1 otherwise."""
    _verify_cfg_codegen("""
        define i32 @sign(i32 %x) {
        entry:
          %c = icmp slt i32 %x, 0
          br i1 %c, label %neg, label %nonneg
        neg:
          ret i32 -1
        nonneg:
          ret i32 1
        }
    """, "sign", inputs=("%x",))


def test_conditional_branch_with_cross_bb_value():
    """A value defined in entry is used in both branches — the codegen
    must keep it in the same register across the branch."""
    _verify_cfg_codegen("""
        define i32 @scale_or_negate(i32 %x) {
        entry:
          %doubled = mul i32 %x, 2
          %c = icmp slt i32 %x, 0
          br i1 %c, label %neg, label %pos
        neg:
          %n = sub i32 0, %doubled
          ret i32 %n
        pos:
          ret i32 %doubled
        }
    """, "scale_or_negate", inputs=("%x",))


def test_diamond_with_distinct_branch_arithmetic():
    """Each branch does its own arithmetic before returning."""
    _verify_cfg_codegen("""
        define i32 @branched_compute(i32 %x) {
        entry:
          %c = icmp sgt i32 %x, 100
          br i1 %c, label %big, label %small
        big:
          %b = sub i32 %x, 100
          ret i32 %b
        small:
          %s = mul i32 %x, 3
          ret i32 %s
        }
    """, "branched_compute", inputs=("%x",))


def test_optimization_collapses_static_branch_and_compiles():
    """The pipeline folds the static-cond branch — codegen produces
    code for only the live path. The verifier executes that code and
    confirms semantics match what the unoptimized program would
    have returned."""
    _verify_cfg_codegen("""
        define i32 @const_branch(i32 %x) {
        entry:
          %c = icmp slt i32 5, 10
          br i1 %c, label %take, label %skip
        take:
          %r = mul i32 %x, 4
          ret i32 %r
        skip:
          ret i32 0
        }
    """, "const_branch", inputs=("%x",))


def test_compare_then_branch_canonical_pattern():
    """The canonical structured-branch pattern: compare x to a
    constant, branch based on result. Each branch does its own
    arithmetic and returns."""
    _verify_cfg_codegen("""
        define i32 @abs_then_double(i32 %x) {
        entry:
          %neg = icmp slt i32 %x, 0
          br i1 %neg, label %was_neg, label %was_pos
        was_neg:
          %a = sub i32 0, %x
          %ar = mul i32 %a, 2
          ret i32 %ar
        was_pos:
          %b = mul i32 %x, 2
          ret i32 %b
        }
    """, "abs_then_double", inputs=("%x",))
