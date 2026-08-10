"""Control-flow graph support: BasicBlocks, branches, and a forward interpreter.

Phase 1 adds three things to the agent's LLVM IR layer:

  * `LLVMBasicBlock` nodes — containers for a sequence of instructions.
    Order is held in the `instructions` list attr on the BB; the
    `contains_inst` edges encode set membership.

  * `br` and `br_cond` instructions — the canonical structured branch
    primitives. `br label %t` is a single-target jump (target via
    `uses_op0`). `br_cond i1 %c, label %t, label %f` is the conditional
    form (cond via `uses_op0`, true target via `uses_op1`, false target
    via `uses_op2`).

  * Forward interpreter — given the entry BB and a binding dict for
    function parameters, walks instructions in BB order, dispatches at
    each terminator. The previous backward (producer-walk) interpreter
    can't follow control flow; this one can.

P5 (PROGRAM_SYNTHESIS_PLAN.md §4-P5, LLVM track) adds **phi**:

  * `%v = phi i32 [ <val>, %<label> ], [ <val>, %<label> ]` — the
    loop-carried-value primitive the P2 lift documented as the
    dialect's frontier ("no phi ⇒ no counting loop"). Incoming values
    are held via `uses_op0..uses_op2` edges (2–3 incomings — the
    production set opens exactly op0..op2); the predecessor labels
    ride the `incoming_labels` list attr, index-aligned with the
    operand edges. Phis must lead their block (LLVM's own rule; the
    parser enforces it mechanically).

  * The forward interpreter commits phis ATOMICALLY at block entry
    (parallel semantics: all incoming values are read before any phi
    result is written, selected by the edge actually taken), and
    recomputes each executed instruction's value per execution — with
    loop-carried values, an instruction's operands legitimately change
    across iterations, so the old compute-once cache semantics would
    read stale values. Without phi nothing can change across
    re-executions, so pre-phi programs behave byte-identically.

The `fold_br_cond_const` optimization rule (added in
`seeds/llvm_passes.json`) turns `br_cond` with a statically known
condition into an unconditional `br` — the canonical "constant-cond
collapses dead branch" pattern that subsequent passes (DCE on the
now-unreachable BB) can build on.

Per the architecture rule, parser/emitter/interpreter are mechanical
text↔graph translators. The reasoning lives inside the substrate's
rules and concepts; this module just connects the world to the graph.
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Grammar productions for the CFG layer
# ---------------------------------------------------------------------------

_BB_PRODUCTIONS = [
    # LLVMBasicBlock contains LLVMInstructions
    ("LLVMBasicBlock", "contains_inst", "LLVMInstruction"),
    # Branch instructions point at BasicBlocks via uses_op*
    ("LLVMInstruction", "uses_op0", "LLVMBasicBlock"),
    ("LLVMInstruction", "uses_op1", "LLVMBasicBlock"),
    ("LLVMInstruction", "uses_op2", "LLVMBasicBlock"),
]


def install_cfg_productions(substrate) -> None:
    """Open the grammar to admit the CFG edge types. Call this on a
    substrate before parsing multi-BB programs."""
    for src_t, et, tgt_t in _BB_PRODUCTIONS:
        substrate.add_production({
            "src": {"type": src_t, "var": "src"},
            "edge_type": et,
            "tgt": {"type": tgt_t, "var": "tgt"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "llvm_ir_cfg",
        })


# ---------------------------------------------------------------------------
# Parser — extends llvm_ir_io with CFG awareness
# ---------------------------------------------------------------------------

_RE_LABEL = re.compile(r"^\s*(?P<name>[\w.]+):\s*$")
_RE_BR = re.compile(r"^\s*br\s+label\s+%(?P<target>[\w.]+)\s*$")
_RE_PHI = re.compile(
    r"^\s*(?P<name>%[\w.]+)\s*=\s*phi\s+(?P<ty>i\d+)\s+(?P<rest>.+?)\s*$")
_RE_PHI_INCOMING = re.compile(
    r"\[\s*(?P<val>%[\w.]+|-?\d+)\s*,\s*%(?P<label>[\w.]+)\s*\]")
_RE_BR_COND = re.compile(
    r"""
    ^\s*br\s+
    i1\s+
    (?P<cond>%[\w.]+|-?\d+)
    \s*,\s*
    label\s+%(?P<true_target>[\w.]+)
    \s*,\s*
    label\s+%(?P<false_target>[\w.]+)
    \s*$
    """,
    re.VERBOSE,
)


def parse_llvm_cfg(substrate, text: str,
                   inputs: tuple[str, ...] = ()) -> dict:
    """Parse multi-BB LLVM IR text into a CFG-rich substrate graph.

    Returns a dict with:
      `ssa`: SSA name → NodeID for produced values + inputs
      `bbs`: BB name → LLVMBasicBlock NodeID
      `entry_bb`: NodeID of the first BB encountered (the entry point)
      `function_name`: parsed from `define` line, if present

    Resolves forward branch references after the full text is parsed.
    """
    # Local import to avoid a circular dep at module load.
    from .llvm_ir_io import _RE_BINOP, _RE_ICMP, _RE_RET, _RE_SELECT, \
        _resolve_operand

    ssa: dict[str, int] = {}
    bbs: dict[str, int] = {}
    pending_branches: list[tuple[int, str, str]] = []  # (inst, edge_type, target_name)
    # Phi incoming %values may be forward references (a loop latch value
    # is defined AFTER the header phi that consumes it) — resolved after
    # the full text is parsed, like branch targets.
    pending_phi_ops: list[tuple[int, str, str]] = []   # (inst, edge_type, ssa_name)
    current_bb: int | None = None
    current_bb_has_non_phi = False
    entry_bb: int | None = None
    function_name: str | None = None

    # Pre-create input LLVMValue nodes.
    for name in inputs:
        if not name.startswith("%"):
            raise ValueError(f"input name {name!r} must start with %")
        ssa[name] = substrate.add_node("LLVMValue", {"type": "i32"})

    def _new_bb(name: str, is_entry: bool = False) -> int:
        bb_id = substrate.add_node("LLVMBasicBlock", {
            "name": name,
            "instructions": [],
            "is_entry": is_entry,
        })
        bbs[name] = bb_id
        return bb_id

    def _emit_to_current(inst: int, is_phi: bool = False) -> None:
        """Add `inst` to the current BB's contains_inst edge + ordered list."""
        nonlocal current_bb, current_bb_has_non_phi
        if current_bb is None:
            # No label seen yet → create an implicit entry BB.
            current_bb = _new_bb("__entry__", is_entry=True)
        if is_phi and current_bb_has_non_phi:
            raise ValueError(
                "phi must lead its basic block (a phi after a non-phi "
                "instruction is invalid LLVM IR)")
        if not is_phi:
            current_bb_has_non_phi = True
        substrate.add_edge(current_bb, "contains_inst", inst, {})
        # Append to ordered list — must round-trip through set_attr because
        # the substrate's attrs are by-value.
        bb_attrs = substrate.node(current_bb)["attrs"]
        order = list(bb_attrs.get("instructions", []))
        order.append(inst)
        substrate.set_attr(current_bb, "instructions", order)

    for raw in text.strip().splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        # define line — extract function name (used for codegen later).
        m = re.match(
            r"^\s*define\s+i\d+\s+@(?P<fn>[\w.]+)\s*\(.*\)\s*\{?\s*$", line)
        if m:
            function_name = m.group("fn")
            continue
        if line == "}" or line.endswith("{") and "define" not in line:
            continue

        # Label: `name:` — starts a new BB.
        if m := _RE_LABEL.match(line):
            name = m.group("name")
            # The first explicit-label BB is the function entry. Used
            # by `eliminate_unreachable_bb` to refuse deletion of the
            # entry even when no branches target it.
            is_first = entry_bb is None
            bb_id = _new_bb(name, is_entry=is_first)
            if is_first:
                entry_bb = bb_id
            current_bb = bb_id
            current_bb_has_non_phi = False
            continue

        # Phi — must lead its block; incoming %values may be forward
        # references (loop latch values), resolved after the parse.
        if m := _RE_PHI.match(line):
            name = m.group("name")
            ty = m.group("ty")
            incomings = _RE_PHI_INCOMING.findall(m.group("rest"))
            if len(incomings) < 2:
                raise ValueError(
                    f"phi needs at least 2 incomings: {raw!r}")
            if len(incomings) > 3:
                raise ValueError(
                    f"phi supports at most 3 incomings (uses_op0..2): "
                    f"{raw!r}")
            inst = substrate.add_node("LLVMInstruction", {
                "opcode": "phi",
                "incoming_labels": [lbl for _val, lbl in incomings],
            })
            result = substrate.add_node("LLVMValue", {"type": ty})
            substrate.add_edge(inst, "produces", result, {})
            for k, (val, _lbl) in enumerate(incomings):
                et = f"uses_op{k}"
                if val.startswith("%"):
                    pending_phi_ops.append((inst, et, val))
                else:
                    const = substrate.add_node("LLVMConstant", {
                        "value": int(val), "type": ty})
                    substrate.add_edge(inst, et, const, {})
            ssa[name] = result
            _emit_to_current(inst, is_phi=True)
            continue

        # Branches — must be emitted before any other op, since branches
        # may reference forward-defined BBs that exist as instructions
        # otherwise.
        if m := _RE_BR.match(line):
            inst = substrate.add_node("LLVMInstruction", {"opcode": "br"})
            _emit_to_current(inst)
            pending_branches.append((inst, "uses_op0", m.group("target")))
            continue

        if m := _RE_BR_COND.match(line):
            inst = substrate.add_node("LLVMInstruction",
                                      {"opcode": "br_cond"})
            cond_node = _resolve_operand(substrate, m.group("cond"), "i1", ssa)
            substrate.add_edge(inst, "uses_op0", cond_node, {})
            _emit_to_current(inst)
            pending_branches.append(
                (inst, "uses_op1", m.group("true_target")))
            pending_branches.append(
                (inst, "uses_op2", m.group("false_target")))
            continue

        # select / icmp / binop / ret — delegate to existing regexes,
        # but EMIT into the current BB.
        if m := _RE_SELECT.match(line):
            name = m.group("name")
            ty = m.group("ty1")
            if m.group("ty2") != ty:
                raise ValueError(
                    f"select branch types must match; "
                    f"got {ty!r} vs {m.group('ty2')!r}")
            inst = substrate.add_node("LLVMInstruction", {"opcode": "select"})
            cond_node = _resolve_operand(substrate, m.group("cond"), "i1", ssa)
            a_node = _resolve_operand(substrate, m.group("a"), ty, ssa)
            b_node = _resolve_operand(substrate, m.group("b"), ty, ssa)
            result = substrate.add_node("LLVMValue", {"type": ty})
            substrate.add_edge(inst, "uses_op0", cond_node, {})
            substrate.add_edge(inst, "uses_op1", a_node, {})
            substrate.add_edge(inst, "uses_op2", b_node, {})
            substrate.add_edge(inst, "produces", result, {})
            ssa[name] = result
            _emit_to_current(inst)
            continue

        if m := _RE_ICMP.match(line):
            name = m.group("name")
            pred = m.group("pred")
            ty = m.group("ty")
            lhs = m.group("lhs")
            rhs = m.group("rhs")
            inst = substrate.add_node(
                "LLVMInstruction", {"opcode": f"icmp_{pred}"})
            lhs_node = _resolve_operand(substrate, lhs, ty, ssa)
            rhs_node = _resolve_operand(substrate, rhs, ty, ssa)
            result = substrate.add_node("LLVMValue", {"type": "i1"})
            substrate.add_edge(inst, "uses_op0", lhs_node, {})
            substrate.add_edge(inst, "uses_op1", rhs_node, {})
            substrate.add_edge(inst, "produces", result, {})
            ssa[name] = result
            _emit_to_current(inst)
            continue

        if m := _RE_BINOP.match(line):
            name = m.group("name")
            opcode = m.group("opcode")
            ty = m.group("ty")
            lhs = m.group("lhs")
            rhs = m.group("rhs")
            inst = substrate.add_node("LLVMInstruction", {"opcode": opcode})
            lhs_node = _resolve_operand(substrate, lhs, ty, ssa)
            rhs_node = _resolve_operand(substrate, rhs, ty, ssa)
            result = substrate.add_node("LLVMValue", {"type": ty})
            substrate.add_edge(inst, "uses_op0", lhs_node, {})
            substrate.add_edge(inst, "uses_op1", rhs_node, {})
            substrate.add_edge(inst, "produces", result, {})
            ssa[name] = result
            _emit_to_current(inst)
            continue

        if m := _RE_RET.match(line):
            ty = m.group("ty")
            val = m.group("val")
            ret_inst = substrate.add_node("LLVMInstruction",
                                          {"opcode": "ret"})
            operand = _resolve_operand(substrate, val, ty, ssa)
            substrate.add_edge(ret_inst, "uses_op0", operand, {})
            _emit_to_current(ret_inst)
            continue

        raise ValueError(f"unrecognised LLVM IR line: {raw!r}")

    # Resolve forward branch references now that all BBs exist.
    for inst, edge_type, target_name in pending_branches:
        if target_name not in bbs:
            raise ValueError(
                f"branch from inst {inst} references undefined label "
                f"%{target_name}")
        substrate.add_edge(inst, edge_type, bbs[target_name], {})

    # Resolve phi incoming values now that every SSA name exists.
    for inst, edge_type, ssa_name in pending_phi_ops:
        if ssa_name not in ssa:
            raise ValueError(
                f"phi at inst {inst} references undefined SSA name "
                f"{ssa_name!r}")
        substrate.add_edge(inst, edge_type, ssa[ssa_name], {})

    if entry_bb is None:
        # Implicit entry — no labels were used.
        entry_bb = bbs.get("__entry__")

    return {
        "ssa": ssa,
        "bbs": bbs,
        "entry_bb": entry_bb,
        "function_name": function_name,
    }


# ---------------------------------------------------------------------------
# Forward interpreter for CFG programs
# ---------------------------------------------------------------------------

def interpret_cfg(substrate, entry_bb: int, bindings: dict[int, int],
                  max_steps: int = 10000) -> int:
    """Execute the CFG starting at `entry_bb` under `bindings` (input
    NodeID → concrete value). Returns the value the executed `ret`
    instruction returns.

    Raises `RuntimeError` on infinite loops (more than `max_steps`
    instructions executed) or if execution falls off the end of a BB
    without a terminator.
    """
    from .llvm_ir_interp import interpret  # backward eval helper

    values = dict(bindings)
    current_bb = entry_bb
    prev_bb_name: str | None = None
    steps = 0

    def _operand_value(node: int) -> int:
        # Already computed (input or earlier producer in this run).
        if node in values:
            return values[node]
        # Constants and constant-folded values cached.
        # Defer to the value-walking interpreter for one node.
        return interpret(substrate, node, values)

    while True:
        bb_attrs = substrate.node(current_bb)["attrs"]
        # Filter to live BB-contained instructions: rules may have
        # deleted entries; the BB's `instructions` list isn't updated
        # by the substrate, and NodeID slots may have been reused by
        # other types. The contains_inst edge cascade-cleans on delete,
        # so the live set is what `contains_inst` still points at.
        live_set = set(substrate.neighbours(current_bb, "contains_inst"))
        instructions = [i for i in bb_attrs.get("instructions", [])
                        if i in live_set]

        # ---- phi commit: parallel semantics at block entry ------------
        # All incoming values are READ (against the pre-entry state)
        # before ANY phi result is written, so same-block phis can
        # reference each other's previous-iteration values soundly.
        phi_updates: list[tuple[int, int]] = []
        for inst in instructions:
            attrs = substrate.node(inst)["attrs"]
            if attrs.get("opcode") != "phi":
                continue
            steps += 1
            if steps > max_steps:
                raise RuntimeError(
                    f"interpret_cfg: exceeded {max_steps} steps — "
                    f"infinite loop?")
            labels = attrs.get("incoming_labels") or []
            if prev_bb_name is None or prev_bb_name not in labels:
                raise RuntimeError(
                    f"interpret_cfg: phi at inst {inst} has no incoming "
                    f"for predecessor {prev_bb_name!r} "
                    f"(labels: {labels})")
            idx = labels.index(prev_bb_name)
            operand = substrate.neighbours(inst, f"uses_op{idx}")[0]
            produces = substrate.neighbours(inst, "produces")
            phi_updates.append((produces[0], _operand_value(operand)))
        for dst, val in phi_updates:
            values[dst] = val

        terminated = False
        for inst in instructions:
            opcode = substrate.node(inst)["attrs"].get("opcode")
            if opcode == "phi":
                continue  # committed at block entry
            steps += 1
            if steps > max_steps:
                raise RuntimeError(
                    f"interpret_cfg: exceeded {max_steps} steps — "
                    f"infinite loop?")
            if opcode is None:
                # Slot was reused by a non-instruction node; skip.
                continue

            if opcode == "ret":
                op0 = substrate.neighbours(inst, "uses_op0")[0]
                return _operand_value(op0)

            if opcode == "br":
                prev_bb_name = bb_attrs.get("name")
                current_bb = substrate.neighbours(inst, "uses_op0")[0]
                terminated = True
                break

            if opcode == "br_cond":
                cond_node = substrate.neighbours(inst, "uses_op0")[0]
                cond_val = _operand_value(cond_node)
                prev_bb_name = bb_attrs.get("name")
                if cond_val:
                    current_bb = substrate.neighbours(inst, "uses_op1")[0]
                else:
                    current_bb = substrate.neighbours(inst, "uses_op2")[0]
                terminated = True
                break

            # Regular instruction: compute its result and record in values.
            produces = substrate.neighbours(inst, "produces")
            if not produces:
                raise RuntimeError(
                    f"interpret_cfg: instruction {inst} (op {opcode!r}) "
                    f"has no produces edge but isn't a terminator")
            # The backward interpreter handles each opcode's evaluation.
            # Recompute per execution: with phi, an instruction's
            # operands legitimately change across loop iterations, so
            # the previous run's cached result must not be reused.
            # (Without phi nothing can change — behaviour identical.)
            values.pop(produces[0], None)
            result = interpret(substrate, produces[0], values)
            values[produces[0]] = result

        if not terminated:
            raise RuntimeError(
                f"interpret_cfg: BB {substrate.node(current_bb)['attrs']['name']!r} "
                f"fell off the end without a terminator")


__all__ = [
    "install_cfg_productions",
    "parse_llvm_cfg",
    "interpret_cfg",
]
