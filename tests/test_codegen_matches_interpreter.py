"""End-to-end codegen verification.

For each test program:
  1. Parse LLVM IR text
  2. Interpret it on random inputs → expected values
  3. Run `local_peephole` to optimize
  4. Emit x86-64 ASM from the optimized IR
  5. Assemble + load the ASM as a callable
  6. Call it with the same random inputs → actual values
  7. Assert expected == actual

This proves the agent's full toolchain (parse → optimize → codegen
→ assemble → execute) preserves program semantics. Up to this point
verification has compared *interpreter* before and after optimization;
this confirms the lowering to machine code is correct too. The
"correctness by construction" claim in `llvm_ir_to_asm.py` becomes a
tested invariant.

Tests skip cleanly if `gcc` isn't present (some CI environments).
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
from domains.llvm_ir_io import parse_llvm_ir
from domains.llvm_ir_interp import interpret
from domains.llvm_ir_to_asm import emit_x86_64_asm


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


def _i32_wrap(v: int) -> int:
    """Wrap a Python int into i32 two's complement for ctypes comparison."""
    v = v & 0xFFFFFFFF
    return v - (1 << 32) if v >= (1 << 31) else v


def _verify_codegen(ir_text: str, fn_name: str,
                    inputs: tuple[str, ...],
                    num_samples: int = 20,
                    seed: int = 0,
                    value_range: tuple[int, int] = (-50, 50)) -> None:
    """Differential test: interpreter result == compiled+executed result
    on `num_samples` random inputs."""
    rng = random.Random(seed)

    # Build the interpreted reference.
    s_interp = _fresh_substrate()
    ssa_interp = parse_llvm_ir(s_interp, ir_text, inputs=list(inputs))

    # Build the codegen path: optimize, then emit ASM, then assemble.
    s_cg = _fresh_substrate()
    ssa_cg = parse_llvm_ir(s_cg, ir_text, inputs=list(inputs))
    run_pipeline_by_name(s_cg, "local_peephole")
    asm = emit_x86_64_asm(
        s_cg, _ret_root(s_cg), fn_name,
        input_nodes=[ssa_cg[n] for n in inputs],
    )
    compiled_fn = assemble_and_load(asm, fn_name, n_args=len(inputs))

    for sample in range(num_samples):
        vals = [rng.randint(*value_range) for _ in inputs]
        bindings = {ssa_interp[name]: v for name, v in zip(inputs, vals)}
        try:
            expected = interpret(s_interp, _ret_root(s_interp), bindings)
        except ZeroDivisionError:
            # Source program has UB on this input — codegen output's
            # behavior here is also undefined, skip.
            continue
        expected_wrapped = _i32_wrap(expected)
        actual = compiled_fn(*vals)
        assert expected_wrapped == actual, (
            f"codegen mismatch on sample {sample}: "
            f"inputs={dict(zip(inputs, vals))}, "
            f"interpreter={expected_wrapped}, compiled={actual}, "
            f"asm:\n{asm}"
        )


# ---------------------------------------------------------------------------
# tests — the end-to-end soundness invariant
# ---------------------------------------------------------------------------

def test_constant_only_program_compiles_and_executes():
    """The simplest non-trivial test: a function that returns a constant
    (after constfold collapses the chain)."""
    s = _fresh_substrate()
    parse_llvm_ir(s, "ret i32 275")
    asm = emit_x86_64_asm(s, _ret_root(s), "const275")
    fn = assemble_and_load(asm, "const275", n_args=0)
    assert fn() == 275


def test_add_constant_to_input():
    _verify_codegen(
        "%r = add i32 %x, 3\nret i32 %r",
        "add3", inputs=("%x",),
    )


def test_mul_by_constant():
    _verify_codegen(
        "%r = mul i32 %x, 7\nret i32 %r",
        "mul7", inputs=("%x",),
    )


def test_strength_reduced_mul_by_power_of_2():
    """The optimizer turns mul-by-4 into shl-by-2; the asm should use
    shll. The end-to-end value must still equal x * 4."""
    _verify_codegen(
        "%r = mul i32 %x, 4\nret i32 %r",
        "mul4", inputs=("%x",),
    )


def test_chained_adds_collapse_then_compile():
    """`(x + 1) + 2 → x + 3` after reassoc + constfold. The asm should
    do one addl $3 — verified by running it."""
    _verify_codegen("""
        %a = add i32 %x, 1
        %b = add i32 %a, 2
        ret i32 %b
    """, "chain_add", inputs=("%x",))


def test_arithmetic_identity_chain():
    """add 0, mul 1, and -1, or 0 — all noops, optimizer should remove
    them. The asm should reduce to passing %x through to %eax."""
    _verify_codegen("""
        %a = add i32 %x, 0
        %b = mul i32 %a, 1
        %c = and i32 %b, -1
        %r = or i32 %c, 0
        ret i32 %r
    """, "identity_chain", inputs=("%x",))


def test_subtraction():
    _verify_codegen(
        "%r = sub i32 %x, %y\nret i32 %r",
        "subxy", inputs=("%x", "%y"),
    )


def test_bitwise_ops():
    _verify_codegen("""
        %a = and i32 %x, 255
        %b = or i32 %a, 4096
        %r = xor i32 %b, 16
        ret i32 %r
    """, "bitop", inputs=("%x",))


def test_signed_division():
    """sdiv lowers to cdq + idiv. Verify on random non-zero divisors."""
    _verify_codegen(
        "%r = sdiv i32 %x, %y\nret i32 %r",
        "sdivxy", inputs=("%x", "%y"),
        # Avoid divisor=0 in the random range — UB is excluded from
        # the verifier anyway, but skipping noise.
        value_range=(1, 50),
    )


def test_signed_remainder():
    _verify_codegen(
        "%r = srem i32 %x, %y\nret i32 %r",
        "sremxy", inputs=("%x", "%y"),
        value_range=(1, 50),
    )


def test_icmp_produces_correct_boolean():
    """Comparisons emit cmp + setcc + movzbl. Verify on signed ranges."""
    _verify_codegen(
        "%r = icmp slt i32 %x, %y\nret i32 %r",
        "lt_xy", inputs=("%x", "%y"),
    )


def test_select_with_runtime_condition():
    """select lowers to test + cmov. The compiled function should pick
    %a when cond is non-zero, %b otherwise."""
    _verify_codegen("""
        %r = select i1 %c, i32 %a, i32 %b
        ret i32 %r
    """, "tern", inputs=("%c", "%a", "%b"),
        # cond is i1 — restrict to 0/1.
        value_range=(0, 1))


def test_branchless_abs():
    """The headline cross-family demo: icmp + select pattern for abs(x).
    Optimized + codegen'd → executed → matches the interpreter."""
    _verify_codegen("""
        %neg = sub i32 0, %x
        %is_neg = icmp slt i32 %x, 0
        %r = select i1 %is_neg, i32 %neg, i32 %x
        ret i32 %r
    """, "absx", inputs=("%x",))


def test_branchless_abs_then_scale():
    """abs(x) * 4 — the canonical compiler-textbook example. Through
    the full agent pipeline: optimize (mul → shl), emit x86-64,
    assemble, execute, verify on random inputs."""
    _verify_codegen("""
        %neg = sub i32 0, %x
        %is_neg = icmp slt i32 %x, 0
        %abs = select i1 %is_neg, i32 %neg, i32 %x
        %r = mul i32 %abs, 4
        ret i32 %r
    """, "abs_scale", inputs=("%x",))


def test_max_of_two():
    """The textbook `max(a, b)` — also branchless via select."""
    _verify_codegen("""
        %c = icmp sgt i32 %a, %b
        %r = select i1 %c, i32 %a, i32 %b
        ret i32 %r
    """, "max_ab", inputs=("%a", "%b"))


def test_clamp_to_range():
    """Clamp x into [0, 100] using two icmp+select. A real
    multi-instruction pattern."""
    _verify_codegen("""
        %lo = icmp slt i32 %x, 0
        %x_ge_0 = select i1 %lo, i32 0, i32 %x
        %hi = icmp sgt i32 %x_ge_0, 100
        %r = select i1 %hi, i32 100, i32 %x_ge_0
        ret i32 %r
    """, "clamp", inputs=("%x",),
        value_range=(-200, 200))
