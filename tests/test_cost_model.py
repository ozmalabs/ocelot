"""Cost-model verification: the optimizer never INCREASES program cost.

This is the operational form of the `cost_equivalence` soundness
category in `compiler_theory.json`. The category says "a transformation
that replaces an operator with a cheaper one preserving the same
value". We test the inverse: the optimization pipeline never makes
the program more expensive.

For each test program:
  1. Parse, compute cost
  2. Optimize via `local_peephole`
  3. Compute cost again
  4. Assert: post-cost <= pre-cost

The strength-reduction tests in particular show STRICT improvement
(mul=3 cycles → shl=1 cycle saves 2 cycles per fold).
"""
from __future__ import annotations

import pytest

from domains.llvm_pass_compiler import install_passes_seed
from domains.compiler_theory_seed import install_compiler_theory_seed
from domains.optimization_pipelines_seed import (
    install_pipelines_seed, run_pipeline_by_name,
)
from domains.llvm_ir_io import parse_llvm_ir
from domains.llvm_cost_model import (
    cost_breakdown, compute_program_cost, opcode_cost,
)


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
# cost model itself
# ---------------------------------------------------------------------------

def test_opcode_costs_are_ordered_correctly():
    """Sanity check: the model captures the right relative ordering of
    operator costs on modern x86-64."""
    # shl is cheaper than mul (the strength-reduction premise).
    assert opcode_cost("shl") < opcode_cost("mul")
    # sdiv is much more expensive than everything else.
    assert opcode_cost("sdiv") > opcode_cost("mul")
    assert opcode_cost("sdiv") > opcode_cost("select")
    # Simple arithmetic is uniform cost.
    assert opcode_cost("add") == opcode_cost("sub") == opcode_cost("xor")


def test_compute_cost_sums_instruction_latencies():
    s = _fresh_substrate()
    parse_llvm_ir(s, """
        %a = add i32 %x, 1
        %b = mul i32 %a, 4
        ret i32 %b
    """, inputs=["%x"])
    # add (1) + mul (3) + ret (1) = 5
    assert compute_program_cost(s, _ret_root(s)) == 5


def test_breakdown_isolates_per_opcode_contribution():
    s = _fresh_substrate()
    parse_llvm_ir(s, """
        %a = add i32 %x, 1
        %b = mul i32 %a, 4
        ret i32 %b
    """, inputs=["%x"])
    breakdown = cost_breakdown(s, _ret_root(s))
    assert breakdown["add"] == 1
    assert breakdown["mul"] == 3
    assert breakdown["ret"] == 1


# ---------------------------------------------------------------------------
# the headline invariant: optimization never makes the program slower
# ---------------------------------------------------------------------------

def _cost_before_and_after(ir_text: str, inputs: tuple[str, ...]):
    s_pre = _fresh_substrate()
    parse_llvm_ir(s_pre, ir_text, inputs=list(inputs))
    pre = compute_program_cost(s_pre, _ret_root(s_pre))

    s_post = _fresh_substrate()
    parse_llvm_ir(s_post, ir_text, inputs=list(inputs))
    run_pipeline_by_name(s_post, "local_peephole")
    post = compute_program_cost(s_post, _ret_root(s_post))
    return pre, post


def test_strength_reduction_strictly_reduces_cost():
    """mul X, 4 (3 cycles) → shl X, 2 (1 cycle). Strict improvement."""
    pre, post = _cost_before_and_after(
        "%r = mul i32 %x, 4\nret i32 %r", ("%x",),
    )
    assert post < pre, f"strength reduction should strictly cut cost; " \
                       f"got pre={pre}, post={post}"
    # Cost difference is exactly the mul-vs-shl gap (2 cycles).
    assert pre - post == opcode_cost("mul") - opcode_cost("shl")


def test_constant_folding_strictly_reduces_cost():
    """A pure-constant program should collapse entirely — cost equals
    just the ret."""
    pre, post = _cost_before_and_after(
        """
        %a = add i32 100, 50
        %b = mul i32 %a, 2
        ret i32 %b
        """, (),
    )
    assert post < pre
    assert post == opcode_cost("ret")  # only the ret remains


def test_identity_elimination_strictly_reduces_cost():
    """`add X, 0` is eliminated — the program drops one add cost."""
    pre, post = _cost_before_and_after(
        "%r = add i32 %x, 0\nret i32 %r", ("%x",),
    )
    assert post < pre
    assert pre - post == opcode_cost("add")


def test_reassoc_plus_constfold_collapse_chain_strictly_reduces():
    """`(x + 1) + 2 → x + 3` cuts an add from the program."""
    pre, post = _cost_before_and_after(
        """
        %a = add i32 %x, 1
        %b = add i32 %a, 2
        ret i32 %b
        """, ("%x",),
    )
    assert post < pre
    assert pre - post == opcode_cost("add")  # one fewer add


def test_dce_does_not_change_dynamic_cost():
    """Dead code already costs nothing at runtime — our cost model
    measures DYNAMIC cost along the live producer path, so DCE
    leaves pre/post equal. (DCE's real win is code-size + cache
    pressure, not latency along the live path.) The invariant we
    care about is post <= pre; equality is fine here."""
    pre, post = _cost_before_and_after(
        """
        %dead = mul i32 %x, 7
        %r = add i32 %x, 1
        ret i32 %r
        """, ("%x",),
    )
    assert post == pre, (
        f"dead code shouldn't change dynamic cost; got "
        f"pre={pre}, post={post}"
    )
    # But the static instruction count IS smaller.
    s_pre = _fresh_substrate()
    parse_llvm_ir(s_pre, """
        %dead = mul i32 %x, 7
        %r = add i32 %x, 1
        ret i32 %r
    """, inputs=["%x"])
    s_post = _fresh_substrate()
    parse_llvm_ir(s_post, """
        %dead = mul i32 %x, 7
        %r = add i32 %x, 1
        ret i32 %r
    """, inputs=["%x"])
    run_pipeline_by_name(s_post, "local_peephole")
    pre_n = len(s_pre.nodes("LLVMInstruction"))
    post_n = len(s_post.nodes("LLVMInstruction"))
    assert post_n < pre_n, (
        f"DCE should reduce instruction count; got pre={pre_n}, "
        f"post={post_n}"
    )


def test_icmp_select_constant_cascade_strictly_reduces():
    """icmp folds → select with constant cond folds → both gone.
    Saves 2 (icmp) + 5 (select) = 7 cycles."""
    pre, post = _cost_before_and_after(
        """
        %c = icmp slt i32 5, 10
        %r = select i1 %c, i32 100, i32 200
        ret i32 %r
        """, (),
    )
    assert post < pre
    assert pre - post == opcode_cost("icmp_slt") + opcode_cost("select")


# Sanity-check that nothing in the rule set is making programs slower.

_INVARIANT_PROGRAMS = [
    # plain arithmetic
    ("%r = add i32 %x, %y\nret i32 %r", ("%x", "%y")),
    # multi-step
    ("""
        %a = add i32 %x, 1
        %b = add i32 %a, 2
        %c = mul i32 %b, 4
        ret i32 %c
     """, ("%x",)),
    # branchless abs
    ("""
        %neg = sub i32 0, %x
        %is_neg = icmp slt i32 %x, 0
        %r = select i1 %is_neg, i32 %neg, i32 %x
        ret i32 %r
     """, ("%x",)),
    # CSE opportunity
    ("""
        %a = add i32 %x, %y
        %b = add i32 %x, %y
        %r = mul i32 %a, %b
        ret i32 %r
     """, ("%x", "%y")),
    # signed division
    ("%r = sdiv i32 %x, 7\nret i32 %r", ("%x",)),
    # bitwise
    ("""
        %a = and i32 %x, 255
        %b = or i32 %a, 16
        %r = xor i32 %b, 1
        ret i32 %r
     """, ("%x",)),
    # comparison
    ("%r = icmp sgt i32 %x, %y\nret i32 %r", ("%x", "%y")),
]


@pytest.mark.parametrize("ir,inputs", _INVARIANT_PROGRAMS)
def test_optimization_never_increases_cost(ir, inputs):
    """The invariant: post-optimization cost <= pre-optimization cost
    on every input program. If this ever fails, some rule in the seed
    is moving in the wrong direction — likely violating
    `cost_equivalence`."""
    pre, post = _cost_before_and_after(ir, inputs)
    assert post <= pre, (
        f"optimization should never increase cost; got pre={pre}, "
        f"post={post}, ir={ir.strip()!r}"
    )
