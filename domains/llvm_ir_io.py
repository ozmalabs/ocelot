"""LLVM IR text ↔ substrate graph.

A tiny world-adapter that maps a useful subset of LLVM IR text syntax
to/from substrate nodes:

  parse_llvm_ir(s, text)   — text → graph; returns the SSA name map
  emit_llvm_ir(s, root)    — graph → text; walks back from a result

Subset supported (Phase 1):

  * Single basic block — no branches, no phi nodes
  * Integer arithmetic: add, sub, mul, and, or, xor, shl, lshr, ashr
  * Type annotations limited to `iN` (we treat `i32` as the default)
  * Constants are integer literals
  * SSA names: `%name` (alphanumeric/underscore)
  * `ret <ty> <value>` to mark the function's result
  * Comments (`;`) and blank lines are ignored
  * Optional `define <ty> @name(<args>) {` / `}` braces are accepted
    and ignored — the parser just looks for instruction-shaped lines

Per the architecture rule, this is mechanical translation. No reasoning,
no decisions over graph state — just text ↔ graph node/edge mutations.
The compiler's *thinking* happens in the substrate via the rule engine
once the IR is loaded.
"""
from __future__ import annotations

import re
from typing import Iterable


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------

_RE_BINOP = re.compile(
    r"""
    ^\s*
    (?P<name>%[\w.]+)         # %r
    \s*=\s*
    (?P<opcode>\w+)           # add
    \s+
    (?P<ty>i\d+)              # i32
    \s+
    (?P<lhs>%[\w.]+|-?\d+)    # %a or 3 or -5
    \s*,\s*
    (?P<rhs>%[\w.]+|-?\d+)    # %b or 5
    \s*$
    """,
    re.VERBOSE,
)

_RE_ICMP = re.compile(
    r"""
    ^\s*
    (?P<name>%[\w.]+)               # %r
    \s*=\s*
    icmp\s+
    (?P<pred>eq|ne|slt|sle|sgt|sge|ult|ule|ugt|uge)
    \s+
    (?P<ty>i\d+)                    # i32 (operand type)
    \s+
    (?P<lhs>%[\w.]+|-?\d+)
    \s*,\s*
    (?P<rhs>%[\w.]+|-?\d+)
    \s*$
    """,
    re.VERBOSE,
)

_RE_SELECT = re.compile(
    r"""
    ^\s*
    (?P<name>%[\w.]+)               # %r
    \s*=\s*
    select\s+
    i1\s+                           # condition type is always i1
    (?P<cond>%[\w.]+|-?\d+)         # %c or 0/1
    \s*,\s*
    (?P<ty1>i\d+)                   # value type — e.g. i32
    \s+
    (?P<a>%[\w.]+|-?\d+)
    \s*,\s*
    (?P<ty2>i\d+)                   # second value type (must match)
    \s+
    (?P<b>%[\w.]+|-?\d+)
    \s*$
    """,
    re.VERBOSE,
)

_RE_RET = re.compile(
    r"""
    ^\s*ret\s+
    (?P<ty>i\d+)
    \s+
    (?P<val>%[\w.]+|-?\d+)
    \s*$
    """,
    re.VERBOSE,
)


def _resolve_operand(substrate, val: str, ty: str,
                     ssa_map: dict[str, int]) -> int:
    """Operand text → NodeID. Either an existing SSA name (must be in
    the map) or a literal constant (creates an LLVMConstant)."""
    if val.startswith("%"):
        if val not in ssa_map:
            raise ValueError(f"unknown SSA name {val!r} — forward reference?")
        return ssa_map[val]
    # Integer literal.
    return substrate.add_node("LLVMConstant", {
        "value": int(val),
        "type": ty,
    })


def parse_llvm_ir(substrate, text: str,
                  inputs: Iterable[str] = ()) -> dict[str, int]:
    """Parse LLVM IR text into substrate nodes.

    `inputs` lists SSA names that are function parameters / inputs —
    they pre-exist as LLVMValue nodes without producers. (If an
    instruction references one and it wasn't declared, the parser
    raises.) Most callers use `inputs=("%x",)` etc.

    Returns the SSA name → NodeID map, including:
      * Each input name → its pre-created LLVMValue
      * Each produced name → its LLVMValue
      * `__return__` → the LLVMValue or LLVMConstant the `ret` referenced
    """
    ssa: dict[str, int] = {}

    def _contain(inst: int) -> None:
        # No-op in the single-BB parser. CFG-shape callers use
        # parse_llvm_cfg instead, which DOES wire contains_inst edges.
        return

    # Pre-create input LLVMValues.
    for name in inputs:
        if not name.startswith("%"):
            raise ValueError(f"input name {name!r} must start with %")
        ssa[name] = substrate.add_node("LLVMValue", {"type": "i32"})

    for raw in text.strip().splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        # Skip braces, function headers, etc.
        if line.endswith("{") or line == "}" or line.startswith("define "):
            continue

        # select first — its 3-operand structure doesn't overlap with
        # the others but precedes them for clarity.
        if m := _RE_SELECT.match(line):
            name = m.group("name")
            ty = m.group("ty1")
            if m.group("ty2") != ty:
                raise ValueError(
                    f"select branch types must match; got {ty!r} vs {m.group('ty2')!r}"
                )
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
            _contain(inst)
            continue

        # icmp first — its syntax overlaps with binop's word-shape so the
        # binop regex would mis-parse `icmp eq i32` if we let it try.
        if m := _RE_ICMP.match(line):
            name = m.group("name")
            pred = m.group("pred")
            ty = m.group("ty")
            lhs = m.group("lhs")
            rhs = m.group("rhs")

            inst = substrate.add_node("LLVMInstruction", {"opcode": f"icmp_{pred}"})
            lhs_node = _resolve_operand(substrate, lhs, ty, ssa)
            rhs_node = _resolve_operand(substrate, rhs, ty, ssa)
            # The result is always i1 regardless of operand type.
            result = substrate.add_node("LLVMValue", {"type": "i1"})
            substrate.add_edge(inst, "uses_op0", lhs_node, {})
            substrate.add_edge(inst, "uses_op1", rhs_node, {})
            substrate.add_edge(inst, "produces", result, {})
            ssa[name] = result
            _contain(inst)
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
            _contain(inst)
            continue

        if m := _RE_RET.match(line):
            ty = m.group("ty")
            val = m.group("val")
            ret_inst = substrate.add_node("LLVMInstruction", {"opcode": "ret"})
            operand = _resolve_operand(substrate, val, ty, ssa)
            substrate.add_edge(ret_inst, "uses_op0", operand, {})
            ssa["__return__"] = operand
            _contain(ret_inst)
            continue

        raise ValueError(f"unrecognised LLVM IR line: {raw!r}")

    return ssa


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------

def _topo_walk(substrate, root: int) -> list[int]:
    """DFS post-order: every dependency comes before the instruction
    that uses it. Returns a list of LLVMInstruction NodeIDs in emit
    order, excluding the ret instruction (caller appends that)."""
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
        # Visit operand producers first — including op2 for 3-operand
        # instructions like select.
        for et in ("uses_op0", "uses_op1", "uses_op2"):
            for op in substrate.neighbours(inst, et):
                visit(op)
        order.append(inst)

    visit(root)
    return order


def emit_llvm_ir(substrate, root: int,
                 input_names: dict[int, str] | None = None,
                 ret_type: str = "i32") -> str:
    """Emit LLVM IR text for the computation rooted at `root`
    (typically the SSA value returned by the function).

    `input_names` maps NodeID → SSA name for pre-existing input
    LLVMValue nodes (function parameters). Other LLVMValues get fresh
    `%vN` names assigned in emit order.

    The output is a sequence of instructions ending with a `ret`.
    Constants are emitted inline by value.
    """
    input_names = dict(input_names or {})
    instr_order = _topo_walk(substrate, root)

    # Name every LLVMValue we encounter.
    value_name: dict[int, str] = dict(input_names)
    next_id = 0

    def name_of(node: int) -> str:
        attrs = substrate.node(node)
        if attrs["type"] == "LLVMConstant":
            v = attrs["attrs"].get("value")
            return str(v)
        if node in value_name:
            return value_name[node]
        nonlocal next_id
        nm = f"%v{next_id}"
        next_id += 1
        value_name[node] = nm
        return nm

    lines: list[str] = []
    for inst in instr_order:
        opcode = substrate.node(inst)["attrs"]["opcode"]
        op0 = substrate.neighbours(inst, "uses_op0")[0]
        op1 = substrate.neighbours(inst, "uses_op1")[0]
        result = substrate.neighbours(inst, "produces")[0]
        result_attrs = substrate.node(result)["attrs"]
        result_name = name_of(result)
        lhs_name = name_of(op0)
        rhs_name = name_of(op1)
        # icmp_<pred> renders as `icmp <pred>` over the OPERAND type
        # (which is the type of op0, not the i1 result).
        if opcode.startswith("icmp_"):
            pred = opcode[len("icmp_"):]
            operand_ty = substrate.node(op0)["attrs"].get("type", "i32")
            lines.append(f"  {result_name} = icmp {pred} {operand_ty} "
                         f"{lhs_name}, {rhs_name}")
        elif opcode == "select":
            # 3-operand: `select i1 %cond, <ty> %a, <ty> %b`.
            op2 = substrate.neighbours(inst, "uses_op2")[0]
            op2_name = name_of(op2)
            value_ty = substrate.node(op1)["attrs"].get("type", "i32")
            lines.append(f"  {result_name} = select i1 {lhs_name}, "
                         f"{value_ty} {rhs_name}, {value_ty} {op2_name}")
        else:
            ty = result_attrs.get("type", "i32")
            lines.append(f"  {result_name} = {opcode} {ty} {lhs_name}, {rhs_name}")

    # Trailing ret.
    lines.append(f"  ret {ret_type} {name_of(root)}")
    return "\n".join(lines)


__all__ = ["parse_llvm_ir", "emit_llvm_ir"]
