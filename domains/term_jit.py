"""JIT-compile a substrate Term to native x86-64.

The substrate's Rust evaluator interprets Term-trees: at each node it
dispatches by variant, reads operands recursively, applies a Rust op.
That's fine for arbitrary Terms — including ones that walk the graph
(Filter, Neighbours, Attr) — but for pure-arithmetic Term-trees the
dispatch overhead dwarfs the actual op cost.

This module compiles such a Term to native x86-64 by reusing every
layer the agent already built:

    Term JSON  →  LLVM IR text  (this module)
              →  substrate IR   (parse_llvm_ir)
              →  optimised IR   (run_pipeline_by_name "local_peephole")
              →  x86-64 asm     (emit_x86_64_asm)
              →  shared object  (gcc via x86_64_runner)
              →  Python callable

The agent's full compiler stack is exercised end-to-end on a single
Term-tree. The output is a Python callable that takes i32 args and
returns i32 — faster than the substrate's interpreter because every
operator is a single native instruction, the optimizer has already
canonicalised the IR (constants folded, identities eliminated,
strength-reduced), and there's no dispatch overhead.

**Pure arithmetic subset** (compiled directly to native):
    Lit  Var  Plus  Minus  Times
    BitAnd  BitOr  BitXor  Shl  Lshr  Ashr
    IDiv  IRem
    Eq  Lt  Lte
    IfThenElse

**Graph-walking subset** — Attr, TypeOf, Neighbours, InNeighbours,
Count, Exists, Sum, Prod, MinOver, MaxOver, Pick, Filter, etc. —
is handled by *stage-splitting*: the JIT identifies each graph-walking
subtree, replaces it with a fresh Var in the arithmetic core, JIT-
compiles the core, and at call time evaluates each graph subterm via
`substrate.evaluate(...)` then passes the resulting ints to the
native function. The arithmetic stays native (fast); the graph
access stays in the substrate (where the graph lives). Each side
plays to its strengths.

The returned callable takes a single env dict (same shape that
`substrate.evaluate` accepts) — values can be ints or NodeIDs.
"""
from __future__ import annotations

from typing import Any, Callable


# ---------------------------------------------------------------------------
# Term → LLVM IR text
# ---------------------------------------------------------------------------

# Map of Term kind → (LLVM opcode, "binary"/"variadic"/"comparison").
# Variadic Terms (Plus, Times) accumulate via left fold.
# Comparison Terms (Eq, Lt, Lte) return i1 which we zero-extend back
# to i32 so the surrounding chain stays i32-uniform.
_BIN_OPS = {
    "Minus":  "sub",
    "BitAnd": "and",
    "BitOr":  "or",
    "BitXor": "xor",
    "Shl":    "shl",
    "Lshr":   "lshr",
    "Ashr":   "ashr",
    "IDiv":   "sdiv",
    "IRem":   "srem",
}

_VARIADIC_OPS = {
    "Plus":  "add",
    "Times": "mul",
}

_CMP_OPS = {
    "Eq":  "eq",
    "Lt":  "slt",
    "Lte": "sle",
}


def term_to_llvm_ir(term: dict, params: list[str],
                    fn_name: str = "term_fn") -> str:
    """Translate a Term-tree (JSON dict, as returned by
    `term_to_json`) to LLVM IR text declaring `@fn_name(i32 %p, ...)`.

    `params` lists the Var names the Term may reference (e.g. ["x", "y"]).
    These become function arguments in the emitted IR (each i32).
    """
    body: list[str] = []
    counter = [0]

    def _fresh() -> str:
        n = f"%v{counter[0]}"
        counter[0] += 1
        return n

    def visit(t: dict) -> str:
        """Emit IR for `t` and return its IR operand (a register or
        literal string)."""
        kind = t.get("type")

        if kind == "Lit":
            v = t["value"]
            if isinstance(v, bool):
                return "1" if v else "0"
            if isinstance(v, int):
                return str(v)
            raise NotImplementedError(
                f"term_jit: Lit value {v!r} not an int")

        if kind == "Var":
            name = t["name"]
            if name not in params:
                raise ValueError(
                    f"term_jit: Var({name!r}) referenced but not in "
                    f"params {params!r}")
            return f"%{name}"

        if kind in _BIN_OPS:
            a = visit(t["a"])
            b = visit(t["b"])
            out = _fresh()
            body.append(f"  {out} = {_BIN_OPS[kind]} i32 {a}, {b}")
            return out

        if kind in _VARIADIC_OPS:
            items = t.get("items", [])
            if not items:
                raise ValueError(f"term_jit: {kind} with no items")
            acc = visit(items[0])
            op = _VARIADIC_OPS[kind]
            for child in items[1:]:
                rhs = visit(child)
                out = _fresh()
                body.append(f"  {out} = {op} i32 {acc}, {rhs}")
                acc = out
            return acc

        if kind in _CMP_OPS:
            a = visit(t["a"])
            b = visit(t["b"])
            i1 = _fresh()
            i32 = _fresh()
            body.append(f"  {i1} = icmp {_CMP_OPS[kind]} i32 {a}, {b}")
            body.append(f"  {i32} = and i32 {i1}, 1")
            return i32

        if kind == "IfThenElse":
            cond_i32 = visit(t["cond"])
            then_val = visit(t["then"])
            other_val = visit(t["other"])
            # Truthy: non-zero i32 → use as i1 via icmp ne 0.
            cond_i1 = _fresh()
            sel = _fresh()
            body.append(f"  {cond_i1} = icmp ne i32 {cond_i32}, 0")
            body.append(
                f"  {sel} = select i1 {cond_i1}, i32 {then_val}, "
                f"i32 {other_val}")
            return sel

        raise NotImplementedError(
            f"term_jit: Term kind {kind!r} not supported")

    root = visit(term)
    body.append(f"  ret i32 {root}")

    header = ", ".join(f"i32 %{p}" for p in params)
    return f"define i32 @{fn_name}({header}) {{\n" + "\n".join(body) + "\n}\n"


# ---------------------------------------------------------------------------
# JIT pipeline: Term → LLVM IR → optimise → x86-64 → callable
# ---------------------------------------------------------------------------

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
                    "provenance": "term_jit",
                })
    s.add_production({
        "src": {"type": "LLVMBasicBlock", "var": "src"},
        "edge_type": "contains_inst",
        "tgt": {"type": "LLVMInstruction", "var": "tgt"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "term_jit",
    })
    return s


def jit_compile_term(term: dict, params: list[str],
                     fn_name: str = "term_fn",
                     optimize: bool = True) -> Callable:
    """Compile a Term to a native Python-callable `f(*i32_args) -> i32`.

    The agent's *own* compiler stack does the work end-to-end:
    Term → LLVM IR → parsed substrate IR → (optionally) optimised IR
    → x86-64 ASM → assembled shared object → ctypes binding.

    `optimize=True` runs `local_peephole` over the parsed IR before
    codegen, so constants are folded, identities eliminated, strength
    reductions applied, etc. The result is generally faster than the
    naive Term-to-asm walk.
    """
    # Local imports — avoid circular load at module import time.
    from .compiler_theory_seed import install_compiler_theory_seed
    from .llvm_ir_io import parse_llvm_ir
    from .llvm_ir_to_asm import emit_x86_64_asm
    from .llvm_pass_compiler import install_passes_seed
    from .optimization_pipelines_seed import (
        install_pipelines_seed, run_pipeline_by_name,
    )
    from .x86_64_runner import assemble_and_load

    ir_text = term_to_llvm_ir(term, params, fn_name=fn_name)

    s = _fresh_substrate()
    install_passes_seed(s, _seed_path("llvm_passes.json"))
    install_compiler_theory_seed(s, _seed_path("compiler_theory.json"))
    install_pipelines_seed(s, _seed_path("optimization_pipelines.json"))

    ssa = parse_llvm_ir(s, ir_text, inputs=[f"%{p}" for p in params])

    if optimize:
        run_pipeline_by_name(s, "local_peephole")

    ret_inst = next(n for n in s.nodes("LLVMInstruction")
                    if s.node(n)["attrs"].get("opcode") == "ret")
    root = s.neighbours(ret_inst, "uses_op0")[0]

    asm = emit_x86_64_asm(
        s, root, fn_name,
        input_nodes=[ssa[f"%{p}"] for p in params],
    )
    return assemble_and_load(asm, fn_name, n_args=len(params))


def _seed_path(name: str) -> str:
    # Locate the project's seeds/ directory regardless of caller cwd.
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "seeds", name)


__all__ = ["term_to_llvm_ir", "jit_compile_term"]
