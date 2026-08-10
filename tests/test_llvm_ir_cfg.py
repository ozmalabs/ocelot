"""Multi-basic-block CFG support: parse, interpret, optimize.

The agent's IR now supports `LLVMBasicBlock` nodes containing ordered
instruction lists, `br`/`br_cond` opcodes, and forward-execution CFG
walking. The optimization rule `fold_br_cond_const` collapses a
conditional branch with a statically-known condition into an
unconditional one — the canonical "constant-fold control flow"
demonstration.
"""
from __future__ import annotations

import pytest

from domains.llvm_pass_compiler import install_passes_seed
from domains.compiler_theory_seed import install_compiler_theory_seed
from domains.optimization_pipelines_seed import (
    install_pipelines_seed, run_pipeline_by_name,
)
from domains.llvm_ir_cfg import (
    install_cfg_productions, interpret_cfg, parse_llvm_cfg,
)


_REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
_PASSES = f"{_REPO_ROOT}/seeds/llvm_passes.json"
_THEORY = f"{_REPO_ROOT}/seeds/compiler_theory.json"
_PIPES = f"{_REPO_ROOT}/seeds/optimization_pipelines.json"


def _fresh_substrate():
    from substrate_rs import _native
    s = _native.Substrate()
    # Open the base LLVM grammar.
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
    # Add CFG-specific productions on top.
    install_cfg_productions(s)
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPES)
    return s


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------

def test_parse_creates_basic_blocks():
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        define i32 @foo(i32 %x) {
        entry:
          %c = icmp slt i32 %x, 0
          br i1 %c, label %neg, label %pos
        neg:
          ret i32 -1
        pos:
          ret i32 1
        }
    """, inputs=("%x",))

    assert out["function_name"] == "foo"
    assert set(out["bbs"].keys()) == {"entry", "neg", "pos"}
    assert out["entry_bb"] == out["bbs"]["entry"]
    # Verify each BB carries its instructions in order.
    entry_attrs = s.node(out["bbs"]["entry"])["attrs"]
    entry_insts = list(entry_attrs["instructions"])
    assert len(entry_insts) == 2  # icmp + br_cond


def test_parse_creates_branch_edges_to_basic_blocks():
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          br i1 1, label %t, label %f
        t:
          ret i32 100
        f:
          ret i32 200
    """)
    br_cond = next(n for n in s.nodes("LLVMInstruction")
                   if s.node(n)["attrs"].get("opcode") == "br_cond")
    # uses_op0 = cond (the constant), uses_op1 = t BB, uses_op2 = f BB
    op1 = s.neighbours(br_cond, "uses_op1")[0]
    op2 = s.neighbours(br_cond, "uses_op2")[0]
    assert s.node(op1)["type"] == "LLVMBasicBlock"
    assert s.node(op2)["type"] == "LLVMBasicBlock"
    assert s.node(op1)["attrs"]["name"] == "t"
    assert s.node(op2)["attrs"]["name"] == "f"


def test_parse_rejects_forward_label_that_never_appears():
    s = _fresh_substrate()
    with pytest.raises(ValueError, match="undefined label"):
        parse_llvm_cfg(s, """
            entry:
              br label %nowhere
        """)


# ---------------------------------------------------------------------------
# forward interpreter
# ---------------------------------------------------------------------------

def test_interpret_cfg_handles_unconditional_branch_chain():
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          br label %middle
        middle:
          %v = add i32 %x, 1
          br label %finish
        finish:
          ret i32 %v
    """, inputs=("%x",))
    val = interpret_cfg(s, out["entry_bb"], {out["ssa"]["%x"]: 41})
    assert val == 42


def test_interpret_cfg_takes_true_branch():
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          %c = icmp slt i32 %x, 0
          br i1 %c, label %neg, label %pos
        neg:
          ret i32 -1
        pos:
          ret i32 1
    """, inputs=("%x",))
    assert interpret_cfg(s, out["entry_bb"], {out["ssa"]["%x"]: -7}) == -1


def test_interpret_cfg_takes_false_branch():
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          %c = icmp slt i32 %x, 0
          br i1 %c, label %neg, label %pos
        neg:
          ret i32 -1
        pos:
          ret i32 1
    """, inputs=("%x",))
    assert interpret_cfg(s, out["entry_bb"], {out["ssa"]["%x"]: 5}) == 1


def test_interpret_cfg_executes_diamond_with_pure_constant_branches():
    """SSA values defined in entry are usable in both branches because
    entry dominates them. Without phi nodes we can't have values flow
    back across the merge — both branches need to ret independently."""
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          %doubled = mul i32 %x, 2
          %c = icmp slt i32 %doubled, 100
          br i1 %c, label %small, label %big
        small:
          %s = add i32 %doubled, 1
          ret i32 %s
        big:
          %b = add i32 %doubled, 100
          ret i32 %b
    """, inputs=("%x",))
    # %x = 10 → doubled=20, small branch, return 21
    assert interpret_cfg(s, out["entry_bb"], {out["ssa"]["%x"]: 10}) == 21
    # %x = 60 → doubled=120, big branch, return 220
    assert interpret_cfg(s, out["entry_bb"], {out["ssa"]["%x"]: 60}) == 220


# ---------------------------------------------------------------------------
# optimization — fold_br_cond_const cascade
# ---------------------------------------------------------------------------

def test_fold_br_cond_with_static_true_collapses_to_unconditional():
    """A `br_cond` whose condition is statically true folds to an
    unconditional `br` to the true target. The false target is no longer
    referenced."""
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          br i1 1, label %t, label %f
        t:
          ret i32 100
        f:
          ret i32 200
    """)
    run_pipeline_by_name(s, "local_peephole")

    # The br_cond instruction should now be a br (opcode flipped).
    branch = next(n for n in s.nodes("LLVMInstruction")
                  if s.node(n)["attrs"].get("opcode") == "br")
    # uses_op0 should now point at the true target (t).
    target = s.neighbours(branch, "uses_op0")[0]
    assert s.node(target)["type"] == "LLVMBasicBlock"
    assert s.node(target)["attrs"]["name"] == "t"
    # uses_op1 and uses_op2 should be empty.
    assert s.neighbours(branch, "uses_op1") == []
    assert s.neighbours(branch, "uses_op2") == []
    # And no br_cond remains.
    assert not any(s.node(n)["attrs"].get("opcode") == "br_cond"
                   for n in s.nodes("LLVMInstruction"))


def test_fold_br_cond_with_static_false_targets_false_branch():
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          br i1 0, label %t, label %f
        t:
          ret i32 100
        f:
          ret i32 200
    """)
    run_pipeline_by_name(s, "local_peephole")
    branch = next(n for n in s.nodes("LLVMInstruction")
                  if s.node(n)["attrs"].get("opcode") == "br")
    target = s.neighbours(branch, "uses_op0")[0]
    assert s.node(target)["attrs"]["name"] == "f"


def test_icmp_then_br_cond_cascade_collapses_via_pipeline():
    """The control-flow analogue of the icmp+select cascade: an icmp
    whose operands are constants folds, then the resulting br_cond
    sees a constant condition and collapses to an unconditional br.

    `icmp slt 5, 10 → true → br_cond true, …, … → br label %then`.
    """
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          %c = icmp slt i32 5, 10
          br i1 %c, label %then, label %else
        then:
          ret i32 100
        else:
          ret i32 200
    """)
    run_pipeline_by_name(s, "local_peephole")

    # The icmp is gone (constfolded).
    assert not any(s.node(n)["attrs"].get("opcode", "").startswith("icmp_")
                   for n in s.nodes("LLVMInstruction"))
    # The branch is now unconditional, targeting `then`.
    branch = next(n for n in s.nodes("LLVMInstruction")
                  if s.node(n)["attrs"].get("opcode") == "br")
    target = s.neighbours(branch, "uses_op0")[0]
    assert s.node(target)["attrs"]["name"] == "then"


# ---------------------------------------------------------------------------
# differential test: optimization preserves CFG semantics
# ---------------------------------------------------------------------------

def test_dead_block_elimination_removes_unreachable_bb():
    """After `fold_br_cond` collapses the static-cond branch, the
    non-chosen target loses its only reference. `eliminate_unreachable_bb`
    cleans it up. Orphan instructions left behind don't affect program
    behavior (the CFG interpreter never visits them); a future
    cleanup pass can sweep them up but isn't part of this phase."""
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          br i1 1, label %taken, label %dead
        taken:
          ret i32 42
        dead:
          %junk = mul i32 1, 2
          ret i32 %junk
    """)
    n_bbs_before = len(s.nodes("LLVMBasicBlock"))
    assert n_bbs_before == 3

    run_pipeline_by_name(s, "local_peephole")

    bbs_after = s.nodes("LLVMBasicBlock")
    bb_names_after = {s.node(b)["attrs"]["name"] for b in bbs_after}
    assert "dead" not in bb_names_after, \
        "dead BB should have been eliminated"
    # entry + taken survive.
    assert "entry" in bb_names_after
    assert "taken" in bb_names_after


def test_dbe_never_deletes_entry_block_even_with_no_incoming_refs():
    """The entry BB never has incoming branches (it's the function's
    entry point) but is_entry=true exempts it from DBE. If we forgot
    to check is_entry, the entire function would vanish."""
    s = _fresh_substrate()
    out = parse_llvm_cfg(s, """
        entry:
          %r = add i32 %x, 1
          ret i32 %r
    """, inputs=("%x",))
    run_pipeline_by_name(s, "local_peephole")
    bbs_after = s.nodes("LLVMBasicBlock")
    assert any(s.node(b)["attrs"]["name"] == "entry" for b in bbs_after), \
        "entry BB must survive even though no branches target it"


def test_optimization_preserves_cfg_semantics_on_random_inputs():
    """Run a multi-BB program before and after `local_peephole`;
    interpreter results must agree on a range of inputs. This extends
    the existing single-BB preservation guarantee to control flow."""
    import random
    rng = random.Random(0)

    ir = """
        entry:
          %x_plus_one = add i32 %x, 1
          %c = icmp slt i32 %x_plus_one, 0
          br i1 %c, label %neg, label %nonneg
        neg:
          %r1 = sub i32 0, %x_plus_one
          ret i32 %r1
        nonneg:
          %r2 = mul i32 %x_plus_one, 2
          ret i32 %r2
    """
    for _ in range(20):
        x = rng.randint(-50, 50)

        s_pre = _fresh_substrate()
        out_pre = parse_llvm_cfg(s_pre, ir, inputs=("%x",))
        v_pre = interpret_cfg(s_pre, out_pre["entry_bb"],
                              {out_pre["ssa"]["%x"]: x})

        s_post = _fresh_substrate()
        out_post = parse_llvm_cfg(s_post, ir, inputs=("%x",))
        run_pipeline_by_name(s_post, "local_peephole")
        v_post = interpret_cfg(s_post, out_post["entry_bb"],
                               {out_post["ssa"]["%x"]: x})

        assert v_pre == v_post, (
            f"CFG-aware optimization regression: x={x}, "
            f"pre={v_pre}, post={v_post}"
        )
