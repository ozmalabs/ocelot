"""Multi-basic-block x86-64 codegen.

Emits assembly for CFG-shaped LLVM IR — `LLVMBasicBlock` containers
with `br` / `br_cond` terminators — to AT&T-syntax x86-64.

  * BBs are walked in topological order starting from the entry BB.
    Each BB becomes a labeled section.
  * Instructions inside each BB are emitted in their `instructions`
    list order (the source order from the LLVM IR text).
  * Terminators lower to control-flow instructions:
      ret      → `movl <root_reg>, %eax; ret`
      br       → `jmp <target_label>`
      br_cond  → `testl %cond, %cond; jne <true_label>; jmp <false_label>`
  * Cross-BB SSA values stay in the registers they were allocated in;
    the bump allocator never reuses, so a value defined in BB A and
    consumed in BB B keeps its register valid across the branch.
  * Phi nodes (P5): each phi result gets its register in a PRE-PASS
    (predecessors may be emitted before the phi's own block); the phi
    itself emits no code — instead each incoming EDGE materialises the
    value with a `movl` before its jump (classic phi elimination into
    edge copies). `br_cond` edges that carry copies are split into
    local edge stubs (`jne .<fn>_<bb>_t; <false movs>; jmp F;
    .<fn>_<bb>_t: <true movs>; jmp T`) so a copy never executes on the
    wrong path; `movl` preserves EFLAGS, so the stub sits safely
    between `testl` and the jumps. Same-block phi-reads-phi (the
    parallel-copy swap hazard) is refused honestly, not mis-lowered.

The reused `_byte_of` helper and register pool live in
`llvm_ir_to_asm.py`; this module imports them to stay DRY.
"""
from __future__ import annotations

from .llvm_ir_to_asm import _ALL_CALLER_SAVED, _ARG_REGS, _RET_REG, _SETCC, _byte_of


def _topo_bb_order(substrate, entry_bb: int) -> list[int]:
    """Depth-first walk from `entry_bb` following branch successors.
    Each BB appears once, in pre-order. Unreachable BBs are omitted.

    Successors are read from the BB's terminator instruction:
      ret      → none
      br       → uses_op0
      br_cond  → uses_op1 (true), uses_op2 (false)
    """
    order: list[int] = []
    visited: set[int] = set()

    def visit(bb: int) -> None:
        if bb in visited:
            return
        visited.add(bb)
        order.append(bb)
        # Find terminator and recurse into successors.
        bb_attrs = substrate.node(bb)["attrs"]
        live = set(substrate.neighbours(bb, "contains_inst"))
        for inst in bb_attrs.get("instructions", []):
            if inst not in live:
                continue
            opcode = substrate.node(inst)["attrs"].get("opcode")
            if opcode == "ret":
                return
            if opcode == "br":
                tgt = substrate.neighbours(inst, "uses_op0")[0]
                visit(tgt)
                return
            if opcode == "br_cond":
                t_bb = substrate.neighbours(inst, "uses_op1")[0]
                f_bb = substrate.neighbours(inst, "uses_op2")[0]
                visit(t_bb)
                visit(f_bb)
                return
        # No terminator found — leaf BB. Will be diagnosed during emit.

    visit(entry_bb)
    return order


def emit_x86_64_cfg(substrate, entry_bb: int, function_name: str,
                    input_nodes: list[int] | None = None) -> str:
    """Emit x86-64 assembly for a multi-BB function.

    `entry_bb` is the entry LLVMBasicBlock NodeID. `input_nodes` lists
    function inputs bound to System V argument registers (%edi, %esi,
    %edx, %ecx, %r8d, %r9d). The result of any executed `ret` lands in
    %eax before the actual `ret` instruction.

    Returns AT&T-syntax assembly text.
    """
    inputs = list(input_nodes or [])
    if len(inputs) > len(_ARG_REGS):
        raise NotImplementedError(
            f"CFG codegen takes at most {len(_ARG_REGS)} inputs")

    # SSA value → register assignment. Persists across BBs.
    value_loc: dict[int, str] = {}
    for i, node in enumerate(inputs):
        value_loc[node] = _ARG_REGS[i]

    input_regs = set(value_loc.values())
    ssa_pool = [r for r in _ALL_CALLER_SAVED if r not in input_regs]
    next_reg = 0

    def alloc_reg() -> str:
        nonlocal next_reg
        if next_reg >= len(ssa_pool):
            raise NotImplementedError(
                "Multi-BB codegen Phase 1 doesn't spill to stack — "
                "more live values than registers")
        r = ssa_pool[next_reg]
        next_reg += 1
        return r

    def loc_of(node: int) -> str:
        if substrate.node(node)["type"] == "LLVMConstant":
            return f"${substrate.node(node)['attrs']['value']}"
        if node in value_loc:
            return value_loc[node]
        raise ValueError(f"unallocated SSA value: {node}")

    # Build a BB-label suffixed with the function name so multiple
    # functions in one .s file don't collide.
    def bb_label(bb: int) -> str:
        name = substrate.node(bb)["attrs"]["name"]
        return f".{function_name}_{name}"

    bb_order = _topo_bb_order(substrate, entry_bb)

    def _live_insts(bb: int) -> list[int]:
        live = set(substrate.neighbours(bb, "contains_inst"))
        return [i for i in substrate.node(bb)["attrs"].get("instructions", [])
                if i in live]

    def _block_phis(bb: int) -> list[int]:
        return [i for i in _live_insts(bb)
                if substrate.node(i)["attrs"].get("opcode") == "phi"]

    # PRE-PASS: allocate a register for every phi result up front — an
    # edge copy in a predecessor may be emitted before the phi's block.
    phi_block: dict[int, int] = {}  # phi inst → its BB
    for bb in bb_order:
        for phi in _block_phis(bb):
            produces = substrate.neighbours(phi, "produces")
            value_loc[produces[0]] = alloc_reg()
            phi_block[phi] = bb

    def _edge_movs(from_bb: int, to_bb: int) -> list[str]:
        """The copies that realise `to_bb`'s phis along the edge
        from `from_bb` (selected by predecessor label)."""
        movs: list[str] = []
        from_name = substrate.node(from_bb)["attrs"]["name"]
        for phi in _block_phis(to_bb):
            attrs = substrate.node(phi)["attrs"]
            labels = attrs.get("incoming_labels") or []
            if from_name not in labels:
                raise ValueError(
                    f"phi {phi} has no incoming for predecessor "
                    f"{from_name!r} (labels: {labels})")
            idx = labels.index(from_name)
            src_node = substrate.neighbours(phi, f"uses_op{idx}")[0]
            src_producers = substrate.in_neighbours(src_node, "produces")
            if src_producers and \
                    substrate.node(src_producers[0])["attrs"].get(
                        "opcode") == "phi" and \
                    phi_block.get(src_producers[0]) == to_bb:
                raise NotImplementedError(
                    "phi reading a same-block phi (parallel-copy swap) "
                    "— refused rather than mis-lowered")
            dst = value_loc[substrate.neighbours(phi, "produces")[0]]
            src = loc_of(src_node)
            if src != dst:
                movs.append(f"    movl {src}, {dst}")
        return movs

    lines: list[str] = [
        f".globl {function_name}",
        f".type {function_name}, @function",
        f"{function_name}:",
    ]

    for bb_i, bb in enumerate(bb_order):
        # Only emit a label for non-entry BBs (the function name is
        # the entry label).
        if bb_i > 0:
            lines.append(f"{bb_label(bb)}:")

        bb_attrs = substrate.node(bb)["attrs"]
        live = set(substrate.neighbours(bb, "contains_inst"))
        for inst in bb_attrs.get("instructions", []):
            if inst not in live:
                continue
            opcode = substrate.node(inst)["attrs"].get("opcode")
            if opcode is None:
                continue
            if opcode == "phi":
                # No code at the phi itself — every incoming edge
                # materialised the value with a movl (pre-allocated reg).
                continue

            # Terminators.
            if opcode == "ret":
                op0 = substrate.neighbours(inst, "uses_op0")[0]
                src = loc_of(op0)
                if src != _RET_REG:
                    lines.append(f"    movl {src}, {_RET_REG}")
                lines.append("    ret")
                break  # rest of BB is dead

            if opcode == "br":
                tgt = substrate.neighbours(inst, "uses_op0")[0]
                lines.extend(_edge_movs(bb, tgt))
                # Fall-through to the next BB in topo order is free;
                # otherwise emit a jmp.
                next_bb = bb_order[bb_i + 1] if bb_i + 1 < len(bb_order) else None
                if tgt != next_bb:
                    lines.append(f"    jmp {bb_label(tgt)}")
                break

            if opcode == "br_cond":
                cond = substrate.neighbours(inst, "uses_op0")[0]
                t_bb = substrate.neighbours(inst, "uses_op1")[0]
                f_bb = substrate.neighbours(inst, "uses_op2")[0]
                cond_src = loc_of(cond)
                next_bb = (bb_order[bb_i + 1]
                           if bb_i + 1 < len(bb_order) else None)
                if cond_src.startswith("$"):
                    # Constant cond — shouldn't happen post-optimization,
                    # but emit a literal jump (with that edge's copies).
                    cond_val = int(cond_src[1:])
                    chosen = t_bb if cond_val else f_bb
                    lines.extend(_edge_movs(bb, chosen))
                    if chosen != next_bb:
                        lines.append(f"    jmp {bb_label(chosen)}")
                    break
                t_movs = _edge_movs(bb, t_bb)
                f_movs = _edge_movs(bb, f_bb)
                lines.append(f"    testl {cond_src}, {cond_src}")
                if not t_movs and not f_movs:
                    # Standard pattern: test cond; jne to true target;
                    # fall through to false target (or jmp if needed).
                    lines.append(f"    jne {bb_label(t_bb)}")
                    if f_bb != next_bb:
                        lines.append(f"    jmp {bb_label(f_bb)}")
                else:
                    # Split the edges so a copy never executes on the
                    # wrong path. movl preserves EFLAGS, so the stub
                    # sits safely after the testl.
                    bb_name = substrate.node(bb)["attrs"]["name"]
                    t_stub = f".{function_name}_{bb_name}_t"
                    lines.append(f"    jne {t_stub}")
                    lines.extend(f_movs)
                    lines.append(f"    jmp {bb_label(f_bb)}")
                    lines.append(f"{t_stub}:")
                    lines.extend(t_movs)
                    lines.append(f"    jmp {bb_label(t_bb)}")
                break

            # Non-terminator instructions: reuse the single-BB codegen
            # logic by emitting the same sequences here.
            result_reg = alloc_reg()
            produces = substrate.neighbours(inst, "produces")
            if produces:
                value_loc[produces[0]] = result_reg

            op0 = substrate.neighbours(inst, "uses_op0")
            op1 = substrate.neighbours(inst, "uses_op1")
            op2 = substrate.neighbours(inst, "uses_op2")

            if opcode in ("add", "sub", "and", "or", "xor"):
                mnemonic = {"add": "addl", "sub": "subl",
                            "and": "andl", "or": "orl", "xor": "xorl"}[opcode]
                lines.append(f"    movl {loc_of(op0[0])}, {result_reg}")
                lines.append(f"    {mnemonic} {loc_of(op1[0])}, {result_reg}")
            elif opcode == "mul":
                src1 = substrate.node(op1[0])
                if src1["type"] == "LLVMConstant":
                    lines.append(
                        f"    imull {loc_of(op1[0])}, {loc_of(op0[0])}, "
                        f"{result_reg}")
                else:
                    lines.append(f"    movl {loc_of(op0[0])}, {result_reg}")
                    lines.append(f"    imull {loc_of(op1[0])}, {result_reg}")
            elif opcode in ("shl", "lshr", "ashr"):
                mnemonic = {"shl": "shll", "lshr": "shrl",
                            "ashr": "sarl"}[opcode]
                src1 = substrate.node(op1[0])
                lines.append(f"    movl {loc_of(op0[0])}, {result_reg}")
                if src1["type"] == "LLVMConstant":
                    lines.append(
                        f"    {mnemonic} {loc_of(op1[0])}, {result_reg}")
                else:
                    lines.append(f"    movl {loc_of(op1[0])}, %ecx")
                    lines.append(f"    {mnemonic} %cl, {result_reg}")
            elif opcode in ("sdiv", "srem"):
                lines.append(f"    movl {loc_of(op0[0])}, %eax")
                lines.append("    cdq")
                divisor = loc_of(op1[0])
                if divisor.startswith("$"):
                    lines.append(f"    movl {divisor}, %r10d")
                    lines.append("    idivl %r10d")
                else:
                    lines.append(f"    idivl {divisor}")
                src = "%eax" if opcode == "sdiv" else "%edx"
                if result_reg != src:
                    lines.append(f"    movl {src}, {result_reg}")
            elif opcode.startswith("icmp_"):
                pred = opcode[len("icmp_"):]
                setcc = _SETCC[pred]
                lines.append(f"    cmpl {loc_of(op1[0])}, {loc_of(op0[0])}")
                byte_reg = _byte_of(result_reg)
                lines.append(f"    {setcc} {byte_reg}")
                lines.append(f"    movzbl {byte_reg}, {result_reg}")
            elif opcode == "select":
                cond_src = loc_of(op0[0])
                a = loc_of(op1[0])
                b = loc_of(op2[0])
                lines.append(f"    movl {a}, {result_reg}")
                if cond_src.startswith("$"):
                    if int(cond_src[1:]) == 0:
                        lines.append(f"    movl {b}, {result_reg}")
                else:
                    lines.append(f"    testl {cond_src}, {cond_src}")
                    if b.startswith("$"):
                        lines.append(f"    movl {b}, %r10d")
                        lines.append(f"    cmovzl %r10d, {result_reg}")
                    else:
                        lines.append(f"    cmovzl {b}, {result_reg}")
            else:
                raise NotImplementedError(
                    f"CFG codegen: opcode {opcode!r} not implemented")

    return "\n".join(lines)


__all__ = ["emit_x86_64_cfg"]
