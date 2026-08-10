"""Cost model for the agent's LLVM IR subset.

Assigns a *latency* (approximate cycle count) to each opcode based on
modern x86-64 microarchitecture (Skylake-class). The model is coarse
on purpose — what matters is the RELATIVE ordering across opcodes:
  * 1 cycle:    add/sub/and/or/xor/shl/lshr/ashr/ret
  * 2 cycles:   icmp variants (cmp+setcc+movzbl pipeline)
  * 3 cycles:   mul (imul has 3-cycle latency on most modern x86)
  * 5 cycles:   select (test + cmov + mov)
  * 22 cycles:  sdiv (idiv is notoriously slow)
  * 22 cycles:  srem (same idiv microcode)

`compute_program_cost(s, root)` walks the IR from a result back through
producers and sums each instruction's latency.

This module gives the `cost_equivalence` category in
`compiler_theory.json` a concrete numerical backing: a strength
reduction rule (mul → shl) doesn't just CLAIM to lower cost — the
model proves it (3 → 1). And `verify_optimization_reduces_or_equals_cost`
turns the abstract guarantee into a tested invariant.
"""
from __future__ import annotations


# Opcode → approximate latency in cycles (Skylake-class x86-64).
# These match the agent's codegen sequences in `llvm_ir_to_asm.py`:
# - icmp lowers to cmp+setcc+movzbl ≈ 2 cycles
# - select lowers to test+cmov+mov ≈ 5 cycles
# - sdiv/srem use cdq + idiv ≈ 22 cycles
_OPCODE_COST: dict[str, int] = {
    "add": 1, "sub": 1, "mul": 3,
    "and": 1, "or": 1, "xor": 1,
    "shl": 1, "lshr": 1, "ashr": 1,
    "sdiv": 22, "srem": 22,
    "icmp_eq": 2, "icmp_ne": 2, "icmp_slt": 2, "icmp_sle": 2,
    "icmp_sgt": 2, "icmp_sge": 2,
    "select": 5,
    "ret": 1,
}


def opcode_cost(opcode: str) -> int:
    """Latency (in approximate cycles) for `opcode`. Unknown opcodes
    return 1 — conservative default."""
    return _OPCODE_COST.get(opcode, 1)


def _topo_walk(substrate, root: int) -> list[int]:
    """DFS post-order over the producer graph rooted at `root`."""
    order: list[int] = []
    visited: set[int] = set()

    def visit(value: int) -> None:
        if value in visited:
            return
        visited.add(value)
        producers = substrate.in_neighbours(value, "produces")
        if not producers:
            return
        inst = producers[0]
        for et in ("uses_op0", "uses_op1", "uses_op2"):
            for op in substrate.neighbours(inst, et):
                visit(op)
        order.append(inst)

    visit(root)
    return order


def compute_program_cost(substrate, root: int) -> int:
    """Sum of latency across the instruction DAG that produces `root`.

    Counts each instruction once (DFS visited-set). Constants and
    function inputs cost 0 — they don't execute.
    """
    instrs = _topo_walk(substrate, root)
    cost = 0
    for inst in instrs:
        opcode = substrate.node(inst)["attrs"].get("opcode", "")
        cost += opcode_cost(opcode)
    # Add the cost of the ret terminator (not in the topo walk because
    # it doesn't produce a value — but it does cost a cycle).
    cost += opcode_cost("ret")
    return cost


def cost_breakdown(substrate, root: int) -> dict[str, int]:
    """Per-opcode cost contribution for explanation purposes."""
    instrs = _topo_walk(substrate, root)
    breakdown: dict[str, int] = {}
    for inst in instrs:
        opcode = substrate.node(inst)["attrs"].get("opcode", "")
        breakdown[opcode] = breakdown.get(opcode, 0) + opcode_cost(opcode)
    breakdown["ret"] = breakdown.get("ret", 0) + opcode_cost("ret")
    return breakdown


__all__ = ["opcode_cost", "compute_program_cost", "cost_breakdown"]
