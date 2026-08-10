"""prog_ir_llvm — lift LLVM-IR substrate graphs into the hub Program IR.

P2, LLVM track (PROGRAM_SYNTHESIS_PLAN.md §4-P2: "lift `parse_llvm_ir`'s
output into hub IR — it is already graph-shaped; this is a
correspondence-rule seed, not new parsing"). The graphs that
`domains/llvm_ir_io.py::parse_llvm_ir` and
`domains/llvm_ir_cfg.py::parse_llvm_cfg` already build become a READ
FRAME of the P1 hub IR (`Prog*` TermNode variants):

  single block      instruction DAG → ``ProgSeq`` of ``ProgAssignVar``
                    (SSA name := DSL arithmetic Term over prior names),
                    ``ret`` → ``ProgReturn``.
  CFG, structured   the two reducible patterns the existing modules
                    produce — if-then-else diamonds → ``ProgIfStmt``,
                    natural single-latch loops → ``ProgWhile``.
  call              → ``ProgCallExtern`` with the callee symbol
                    (graph-level row: neither existing parser mints a
                    call instruction — see the doc's frontier section).
  anything else     honest residual ``{ok: False, blockers: [...]}`` —
                    no goto emulation, no node splitting at P2.

The opcode → Term correspondence is DATA: `seeds/llvm_correspondence.json`
ships ``LLVMOpcodeMap`` rows whose ``template`` attr is Term-JSON with
``{"__operand__": N}`` placeholders. This module is a table-driven
walker: table dispatch per opcode plus the two structural pattern
matches. Per the architecture rule it is mechanical translation (one
graph dialect read into another, the `ast_to_term.py` precedent) —
no agent decisions, no graph-state-dependent branching beyond honest
"can this shape be lifted" pattern admission, whose failure is always
a recorded blocker, never silent repair.

Honesty guards (all mechanical scans, all → blockers):

  * ``unsupported_opcode:<op>`` — opcode has no table row (e.g. the
    unsigned icmp predicates, which `llvm_ir_interp` refuses too; phi,
    which the dialect cannot produce).
  * ``unstructured_cfg`` — the block graph doesn't match the two
    structured patterns (irreducible cycles, nested br_cond arms,
    re-entry into an already-lifted block).
  * ``cross_arm_value_read`` / ``join_reads_branch_value`` /
    ``loop_exit_reads_body_value`` — dominance-violating SSA reads.
    The trusted oracle (`llvm_ir_interp.interpret`) evaluates values
    BACKWARD through producers regardless of the executed path, so it
    computes such values anyway; the lifted program would honestly
    trap ``name:<n>``. Rather than ship a silent divergence, the lift
    refuses these shapes.
"""
from __future__ import annotations

import json
import os

from .llvm_ir_io import _topo_walk

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(_REPO_ROOT, "seeds", "llvm_correspondence.json")

_TERMINATORS = ("ret", "br", "br_cond")


# ---------------------------------------------------------------------------
# correspondence table
# ---------------------------------------------------------------------------

def load_correspondence(substrate=None) -> dict[str, dict]:
    """opcode → row (dict of the LLVMOpcodeMap attrs).

    Reads the rows from ``LLVMOpcodeMap`` nodes when the seed is loaded
    on `substrate` (the agent holds the table), else from the manifest
    file. Mechanical read — the table itself is the seed's data.
    """
    rows: dict[str, dict] = {}
    if substrate is not None:
        for nid in substrate.nodes("LLVMOpcodeMap"):
            attrs = substrate.node(nid)["attrs"]
            if attrs.get("opcode"):
                rows[attrs["opcode"]] = dict(attrs)
    if not rows:
        with open(SEED_PATH, encoding="utf-8") as f:
            manifest = json.load(f)
        for n in manifest.get("nodes", []):
            if n.get("type") == "LLVMOpcodeMap":
                rows[n["attrs"]["opcode"]] = dict(n["attrs"])
    return rows


def _subst(template, operands: list[dict]):
    """Replace ``{"__operand__": N}`` placeholders with operand terms."""
    if isinstance(template, dict):
        if set(template.keys()) == {"__operand__"}:
            return operands[template["__operand__"]]
        return {k: _subst(v, operands) for k, v in template.items()}
    if isinstance(template, list):
        return [_subst(x, operands) for x in template]
    return template


# ---------------------------------------------------------------------------
# naming + operands (mechanical text↔graph bookkeeping)
# ---------------------------------------------------------------------------

def _var_name(ssa_name: str) -> str:
    return ssa_name.lstrip("%").replace(".", "_")


def _name_map(ssa: dict[str, int]) -> dict[int, str]:
    return {nid: _var_name(name)
            for name, nid in ssa.items() if name != "__return__"}


def _operand_term(substrate, node: int, names: dict[int, str]) -> dict:
    info = substrate.node(node)
    if info["type"] == "LLVMConstant":
        return {"type": "Lit", "value": int(info["attrs"]["value"])}
    return {"type": "Var", "name": names.get(node, f"v{node}")}


def _operands(substrate, inst: int) -> list[int]:
    ops: list[int] = []
    for et in ("uses_op0", "uses_op1", "uses_op2"):
        tgts = substrate.neighbours(inst, et)
        if not tgts:
            break
        ops.append(tgts[0])
    return ops


# ---------------------------------------------------------------------------
# per-instruction lift (pure table dispatch)
# ---------------------------------------------------------------------------

def _inst_stmt(substrate, inst: int, table, names, blockers) -> dict | None:
    """One non-terminator LLVMInstruction → one ProgAssignVar (or None
    with a blocker recorded)."""
    attrs = substrate.node(inst)["attrs"]
    opcode = attrs.get("opcode")
    row = table.get(opcode)
    if row is None or row.get("kind") not in ("expr", "call"):
        blockers.append(f"unsupported_opcode:{opcode}")
        return None
    produced = substrate.neighbours(inst, "produces")
    if not produced:
        blockers.append(f"no_result:{opcode}")
        return None
    op_terms = [_operand_term(substrate, o, names)
                for o in _operands(substrate, inst)]
    if row["kind"] == "call":
        callee = attrs.get("callee")
        if not callee:
            blockers.append("call:missing_callee")
            return None
        value = {"type": "ProgCallExtern", "name": str(callee),
                 "recv": None, "args": op_terms}
    else:
        if len(op_terms) != int(row.get("arity", len(op_terms))):
            blockers.append(f"operand_arity:{opcode}")
            return None
        value = _subst(json.loads(row["template"]), op_terms)
    return {"type": "ProgAssignVar",
            "name": names.get(produced[0], f"v{produced[0]}"),
            "value": value}


# ---------------------------------------------------------------------------
# Var read/write scans (the dominance honesty guards)
# ---------------------------------------------------------------------------

def _var_reads(obj, out: set[str]) -> None:
    if isinstance(obj, dict):
        if obj.get("type") == "Var" and isinstance(obj.get("name"), str):
            out.add(obj["name"])
        for v in obj.values():
            _var_reads(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _var_reads(v, out)


def _var_writes(stmts: list[dict]) -> set[str]:
    out: set[str] = set()

    def walk(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "ProgAssignVar":
                out.add(obj["name"])
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(stmts)
    return out


def _reads_of(stmts) -> set[str]:
    out: set[str] = set()
    _var_reads(stmts, out)
    return out


# ---------------------------------------------------------------------------
# single-block lift (parse_llvm_ir output)
# ---------------------------------------------------------------------------

def lift_llvm_block(substrate, ssa: dict[str, int], table=None) -> dict:
    """Lift a single-basic-block LLVM graph (`parse_llvm_ir` output)
    into hub IR.

    Returns ``{"ok": True, "prog": <ProgSeq Term-JSON>, "blockers": []}``
    or ``{"ok": False, "prog": None, "blockers": [...]}``.

    Instruction order is the deterministic dependency (DFS post-)order
    from the returned value — the same order `emit_llvm_ir` uses; dead
    instructions (unreachable from ret) are not lifted, matching the
    oracle, which never computes them either.
    """
    table = table if table is not None else load_correspondence(substrate)
    blockers: list[str] = []
    if "__return__" not in ssa:
        return {"ok": False, "prog": None, "blockers": ["missing_ret"]}
    names = _name_map(ssa)
    ret_node = ssa["__return__"]
    stmts: list[dict] = []
    for inst in _topo_walk(substrate, ret_node):
        st = _inst_stmt(substrate, inst, table, names, blockers)
        if st is not None:
            stmts.append(st)
    stmts.append({"type": "ProgReturn",
                  "value": _operand_term(substrate, ret_node, names)})
    blockers = list(dict.fromkeys(blockers))
    if blockers:
        return {"ok": False, "prog": None, "blockers": blockers}
    return {"ok": True, "prog": {"type": "ProgSeq", "stmts": stmts},
            "blockers": []}


# ---------------------------------------------------------------------------
# CFG lift (parse_llvm_cfg output) — the two structured patterns
# ---------------------------------------------------------------------------

def lift_llvm_cfg(substrate, parse_out: dict, table=None) -> dict:
    """Lift a multi-BB LLVM CFG graph (`parse_llvm_cfg` output) into
    hub IR. Structured control flow only:

      * if-then-else diamonds (both arms return; or arms rejoining at a
        common block, including the empty-arm if-then / guard-clause
        forms) → ``ProgIfStmt``;
      * natural single-latch loops (a header ``br_cond`` with one arm a
        straight-line chain latching back to the header) →
        ``ProgWhile``. When the header's computations feed ONLY the
        branch condition they are INLINED into the while condition
        (re-evaluated each iteration by construction); otherwise they
        are emitted before the loop and re-emitted at the end of the
        body so the condition is honestly re-evaluated.

    **Phi (P5)** — the P2 §3 recipe, now applied: a phi is a
    ``ProgAssignVar`` of the incoming value on each incoming edge.

      * loop-header phi → an INIT assignment before the loop (the
        entry-edge value) + a LATCH assignment at the end of the body
        (the latch-edge value);
      * join-block phi → an assignment at the end of each arm (the
        empty arm materialises as an ``orelse`` holding just the
        copies; an entry edge straight from the header carries the
        pre-branch value).

    Phis anywhere else (arm interiors, loop bodies, ret/br blocks) are
    an honest ``phi_outside_supported_pattern`` blocker — refusal, not
    silent mis-lift. Same-block phi-reads-phi (parallel-copy hazard) is
    ``phi_parallel_copy_unsupported``.

    Any other shape → ``{"ok": False, "blockers": ["unstructured_cfg",
    ...]}``. No goto emulation, no node splitting.
    """
    table = table if table is not None else load_correspondence(substrate)
    names = _name_map(parse_out["ssa"])
    blockers: list[str] = []
    emitted: set[int] = set()
    consumed_phi_blocks: set[int] = set()
    br_row = table.get("br_cond") or {}
    cond_tpl = json.loads(br_row.get("template", '{"__operand__": 0}'))
    cond_neg_tpl = json.loads(
        br_row.get("template_negated", '{"__operand__": 0}'))

    def live_insts(bb: int) -> list[int]:
        live = set(substrate.neighbours(bb, "contains_inst"))
        return [i for i in substrate.node(bb)["attrs"].get("instructions", [])
                if i in live]

    def bb_name(bb: int) -> str:
        return substrate.node(bb)["attrs"].get("name", "")

    def phi_rows(bb: int) -> list[tuple[int, int, list[tuple[str, int]]]]:
        """[(phi inst, result node, [(pred label, operand node), ...])]
        for the block's leading phis (with the parallel-copy guard)."""
        rows = []
        insts = live_insts(bb)
        phi_results = set()
        for inst in insts:
            if substrate.node(inst)["attrs"].get("opcode") == "phi":
                produced = substrate.neighbours(inst, "produces")
                if produced:
                    phi_results.add(produced[0])
        for inst in insts:
            attrs = substrate.node(inst)["attrs"]
            if attrs.get("opcode") != "phi":
                continue
            labels = attrs.get("incoming_labels") or []
            produced = substrate.neighbours(inst, "produces")
            if not produced or len(labels) < 2:
                blockers.append("phi_malformed")
                continue
            ops: list[tuple[str, int]] = []
            for k, lbl in enumerate(labels):
                tgts = substrate.neighbours(inst, f"uses_op{k}")
                if not tgts:
                    blockers.append("phi_malformed")
                    break
                if tgts[0] in phi_results:
                    blockers.append("phi_parallel_copy_unsupported")
                ops.append((str(lbl), tgts[0]))
            else:
                rows.append((inst, produced[0], ops))
        return rows

    def has_phis(blocks) -> bool:
        return any(
            substrate.node(i)["attrs"].get("opcode") == "phi"
            for b in blocks for i in live_insts(b))

    def block_parts(bb: int):
        """(assign stmts, terminator inst | None) for one block. Phis
        are skipped here — they are STRUCTURAL (consumed by the loop /
        join patterns); a phi no pattern consumes is caught by the
        `phi_outside_supported_pattern` checks in `structure`."""
        stmts: list[dict] = []
        term = None
        insts = live_insts(bb)
        for idx, inst in enumerate(insts):
            opcode = substrate.node(inst)["attrs"].get("opcode")
            if opcode == "phi":
                continue
            if opcode in _TERMINATORS:
                term = inst
                if idx != len(insts) - 1:
                    blockers.append("terminator_not_last")
                break
            st = _inst_stmt(substrate, inst, table, names, blockers)
            if st is not None:
                stmts.append(st)
        return stmts, term

    def linear_run(bb: int):
        """Chase straight-line blocks (assigns + unconditional br) from
        `bb`. Returns a dict:
          blocks: ordered blocks consumed,
          stmts:  their lifted assign stmts (ProgReturn appended on ret),
          kind:   "ret" | "brcond" | "emitted" | "cycle" | "noterm",
          hit:    the emitted block reached (kind == "emitted"),
          at:     the block where the run stopped (kind == "brcond").
        """
        blocks: list[int] = []
        stmts: list[dict] = []
        while True:
            if bb in emitted:
                return {"blocks": blocks, "stmts": stmts,
                        "kind": "emitted", "hit": bb}
            if bb in blocks:
                return {"blocks": blocks, "stmts": stmts, "kind": "cycle"}
            blocks.append(bb)
            s, term = block_parts(bb)
            stmts.extend(s)
            if term is None:
                return {"blocks": blocks, "stmts": stmts, "kind": "noterm"}
            opcode = substrate.node(term)["attrs"]["opcode"]
            if opcode == "ret":
                op0 = substrate.neighbours(term, "uses_op0")[0]
                stmts.append({"type": "ProgReturn",
                              "value": _operand_term(substrate, op0, names)})
                return {"blocks": blocks, "stmts": stmts, "kind": "ret"}
            if opcode == "br_cond":
                return {"blocks": blocks, "stmts": stmts,
                        "kind": "brcond", "at": bb}
            bb = substrate.neighbours(term, "uses_op0")[0]

    def arm_before(run: dict, join: int):
        """(blocks, stmts) of `run` strictly before block `join`."""
        blocks = []
        for b in run["blocks"]:
            if b == join:
                break
            blocks.append(b)
        # Re-lift just those blocks' stmts (runs collect flat, so slice
        # by recomputing — deterministic and cheap at this scale).
        stmts: list[dict] = []
        for b in blocks:
            s, _term = block_parts(b)
            stmts.extend(s)
        return blocks, stmts

    def seq(stmts: list[dict]) -> dict:
        return {"type": "ProgSeq", "stmts": stmts}

    def _inline_defs(term_json, defs: dict[str, dict]):
        """Recursively substitute header-computed Vars into a Term."""
        if isinstance(term_json, dict):
            if term_json.get("type") == "Var" and \
                    term_json.get("name") in defs:
                return _inline_defs(defs[term_json["name"]], defs)
            return {k: _inline_defs(v, defs) for k, v in term_json.items()}
        if isinstance(term_json, list):
            return [_inline_defs(x, defs) for x in term_json]
        return term_json

    def _phi_copies(rows, pred_name: str, kind: str):
        """One ProgAssignVar per phi for the `pred_name` edge; a
        missing/ambiguous incoming is a blocker."""
        copies: list[dict] = []
        for _inst, result, ops in rows:
            matching = [op for lbl, op in ops if lbl == pred_name]
            if len(matching) != 1:
                blockers.append(f"phi_incoming_mismatch:{kind}")
                continue
            copies.append({
                "type": "ProgAssignVar",
                "name": names.get(result, f"v{result}"),
                "value": _operand_term(substrate, matching[0], names)})
        return copies

    def structure(bb: int) -> list[dict]:
        stmts: list[dict] = []
        while True:
            if bb in emitted:
                blockers.append("unstructured_cfg")
                return stmts
            emitted.add(bb)
            bb_phis = [] if bb in consumed_phi_blocks else phi_rows(bb)
            bb_stmts, term = block_parts(bb)
            if term is None:
                blockers.append("missing_terminator")
                return stmts
            opcode = substrate.node(term)["attrs"]["opcode"]
            if opcode == "ret":
                if bb_phis:
                    blockers.append("phi_outside_supported_pattern")
                stmts.extend(bb_stmts)
                op0 = substrate.neighbours(term, "uses_op0")[0]
                stmts.append({"type": "ProgReturn",
                              "value": _operand_term(substrate, op0, names)})
                return stmts
            if opcode == "br":
                if bb_phis:
                    blockers.append("phi_outside_supported_pattern")
                stmts.extend(bb_stmts)
                bb = substrate.neighbours(term, "uses_op0")[0]
                continue
            # --- br_cond: the two structured patterns -----------------
            header = bb
            cond_node = substrate.neighbours(term, "uses_op0")[0]
            t_bb = substrate.neighbours(term, "uses_op1")[0]
            f_bb = substrate.neighbours(term, "uses_op2")[0]
            cond = _operand_term(substrate, cond_node, names)
            truthy = _subst(cond_tpl, [cond])
            negated = _subst(cond_neg_tpl, [cond])

            t_run = linear_run(t_bb) if t_bb != header else \
                {"blocks": [], "stmts": [], "kind": "emitted", "hit": header}
            f_run = linear_run(f_bb) if f_bb != header else \
                {"blocks": [], "stmts": [], "kind": "emitted", "hit": header}

            t_latch = t_run["kind"] == "emitted" and t_run.get("hit") == header
            f_latch = f_run["kind"] == "emitted" and f_run.get("hit") == header

            # Pattern: natural single-latch loop.
            if t_latch and f_latch:
                blockers.append("unstructured_cfg")  # no exit arm
                return stmts
            if t_latch or f_latch:
                body_run = t_run if t_latch else f_run
                exit_bb = f_bb if t_latch else t_bb
                if has_phis(body_run["blocks"]):
                    blockers.append("phi_outside_supported_pattern")
                emitted.update(body_run["blocks"])
                # Phi resolution (P2 §3 recipe): entry-edge init before
                # the loop, latch-edge assignment at the end of the body.
                latch_name = bb_name(body_run["blocks"][-1]
                                     if body_run["blocks"] else header)
                phi_names: set[str] = set()
                inits: list[dict] = []
                latch_copies: list[dict] = []
                for _inst, result, ops in bb_phis:
                    latch_ops = [op for lbl, op in ops if lbl == latch_name]
                    entry_ops = [op for lbl, op in ops if lbl != latch_name]
                    if len(latch_ops) != 1 or len(entry_ops) != 1:
                        blockers.append("phi_incoming_mismatch:loop")
                        continue
                    v = names.get(result, f"v{result}")
                    phi_names.add(v)
                    inits.append({
                        "type": "ProgAssignVar", "name": v,
                        "value": _operand_term(substrate, entry_ops[0],
                                               names)})
                    latch_copies.append({
                        "type": "ProgAssignVar", "name": v,
                        "value": _operand_term(substrate, latch_ops[0],
                                               names)})
                rest = structure(exit_bb) if exit_bb != header else None
                if rest is None:
                    blockers.append("unstructured_cfg")
                    return stmts
                # Header computations feed the condition; when nothing
                # OUTSIDE the header reads them, they inline into the
                # while condition (re-evaluated each iteration by
                # construction). Otherwise: pre-loop emission + body-end
                # re-emission (the honest re-evaluation), as before.
                header_defs = {s["name"]: s["value"] for s in bb_stmts
                               if s.get("type") == "ProgAssignVar"}
                elsewhere = (_reads_of(body_run["stmts"])
                             | _reads_of(latch_copies)
                             | _reads_of(inits) | _reads_of(rest))
                inline_ok = not (set(header_defs) & elsewhere)
                if inline_ok:
                    inlined = _inline_defs(cond, header_defs)
                    while_cond = _subst(cond_tpl if t_latch else cond_neg_tpl,
                                        [inlined])
                    body_stmts = body_run["stmts"] + latch_copies
                    pre_stmts = inits
                else:
                    while_cond = truthy if t_latch else negated
                    body_stmts = (body_run["stmts"] + latch_copies
                                  + bb_stmts)
                    pre_stmts = inits + bb_stmts
                body_exclusive = (_var_writes(body_run["stmts"])
                                  - phi_names
                                  - (set(header_defs) if not inline_ok
                                     else set()))
                if body_exclusive & _reads_of(rest):
                    blockers.append("loop_exit_reads_body_value")
                stmts.extend(pre_stmts)
                stmts.append({"type": "ProgWhile", "cond": while_cond,
                              "body": seq(body_stmts), "orelse": None})
                stmts.extend(rest)
                return stmts

            # Below here the header's own phis have no consumer pattern.
            if bb_phis:
                blockers.append("phi_outside_supported_pattern")
            stmts.extend(bb_stmts)

            # Pattern: diamond with a join block (incl. empty-arm forms).
            f_blocks = set(f_run["blocks"])
            join = next((b for b in t_run["blocks"] + [None]
                         if b is not None and b in f_blocks), None)
            if t_bb == f_bb:
                join = t_bb
            if join is not None:
                t_arm_blocks, t_arm_stmts = arm_before(t_run, join)
                f_arm_blocks, f_arm_stmts = arm_before(f_run, join)
                if has_phis(t_arm_blocks) or has_phis(f_arm_blocks):
                    blockers.append("phi_outside_supported_pattern")
                # Join phis (P2 §3 recipe): an assignment at the end of
                # each arm; an empty arm materialises as orelse copies.
                join_phis = ([] if join in consumed_phi_blocks
                             else phi_rows(join))
                if join_phis:
                    t_pred = bb_name(t_arm_blocks[-1] if t_arm_blocks
                                     else header)
                    f_pred = bb_name(f_arm_blocks[-1] if f_arm_blocks
                                     else header)
                    t_arm_stmts = t_arm_stmts + _phi_copies(
                        join_phis, t_pred, "join")
                    f_arm_stmts = f_arm_stmts + _phi_copies(
                        join_phis, f_pred, "join")
                    consumed_phi_blocks.add(join)
                if _var_writes(t_arm_stmts) & _reads_of(f_arm_stmts) or \
                   _var_writes(f_arm_stmts) & _reads_of(t_arm_stmts):
                    blockers.append("cross_arm_value_read")
                emitted.update(t_arm_blocks)
                emitted.update(f_arm_blocks)
                # A name defined on only ONE path may not be read past
                # the join (a both-arms write — the phi copies — is
                # defined on every path and is legal to read).
                one_sided = (_var_writes(t_arm_stmts)
                             ^ _var_writes(f_arm_stmts))
                rest = structure(join)
                if one_sided & _reads_of(rest):
                    blockers.append("join_reads_branch_value")
                stmts.append({"type": "ProgIfStmt", "cond": truthy,
                              "then": seq(t_arm_stmts),
                              "orelse": seq(f_arm_stmts) if f_arm_stmts
                              else None})
                stmts.extend(rest)
                return stmts

            # Pattern: diamond, both arms return (disjoint rets).
            if t_run["kind"] == "ret" and f_run["kind"] == "ret":
                if has_phis(t_run["blocks"]) or has_phis(f_run["blocks"]):
                    blockers.append("phi_outside_supported_pattern")
                if _var_writes(t_run["stmts"]) & _reads_of(f_run["stmts"]) or \
                   _var_writes(f_run["stmts"]) & _reads_of(t_run["stmts"]):
                    blockers.append("cross_arm_value_read")
                emitted.update(t_run["blocks"])
                emitted.update(f_run["blocks"])
                stmts.append({"type": "ProgIfStmt", "cond": truthy,
                              "then": seq(t_run["stmts"]),
                              "orelse": seq(f_run["stmts"])})
                return stmts

            # Guard-clause: exactly one arm returns; the other is the
            # continuation.
            if t_run["kind"] == "ret":
                if has_phis(t_run["blocks"]):
                    blockers.append("phi_outside_supported_pattern")
                emitted.update(t_run["blocks"])
                stmts.append({"type": "ProgIfStmt", "cond": truthy,
                              "then": seq(t_run["stmts"]), "orelse": None})
                bb = f_bb  # continuation lifts in the outer loop
                continue
            if f_run["kind"] == "ret":
                if has_phis(f_run["blocks"]):
                    blockers.append("phi_outside_supported_pattern")
                emitted.update(f_run["blocks"])
                stmts.append({"type": "ProgIfStmt", "cond": negated,
                              "then": seq(f_run["stmts"]), "orelse": None})
                bb = t_bb
                continue

            blockers.append("unstructured_cfg")
            return stmts

    entry = parse_out.get("entry_bb")
    if entry is None:
        return {"ok": False, "prog": None, "blockers": ["missing_entry"]}
    stmts = structure(entry)
    out_blockers = list(dict.fromkeys(blockers))
    if out_blockers:
        return {"ok": False, "prog": None, "blockers": out_blockers}
    return {"ok": True, "prog": {"type": "ProgSeq", "stmts": stmts},
            "blockers": []}


__all__ = [
    "SEED_PATH",
    "load_correspondence",
    "lift_llvm_block",
    "lift_llvm_cfg",
]
