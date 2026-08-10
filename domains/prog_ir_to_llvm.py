"""prog_ir_to_llvm — emit hub Program-IR (Prog* Term-JSON) as LLVM IR text.

P5, LLVM track (PROGRAM_SYNTHESIS_PLAN.md §4-P5: "LLVM IR: extend
emission to the IR statement set (branches, loops via CFG blocks);
x86-64 = IR → existing cfg_to_asm chain. No direct statement templates
for asm."). The WRITE half of the P2 read frame: `domains/prog_ir_llvm.py`
lifts the dialect INTO hub IR; this module renders hub IR OUT as .ll
text the existing chain speaks end-to-end —

    hub IR ──emit_prog_to_llvm──▶ .ll text
           ──parse_llvm_cfg────▶ substrate CFG graph
           ──interpret_cfg─────▶ oracle value        (agreement leg 2)
           ──emit_x86_64_cfg───▶ AT&T asm
           ──assemble_and_load─▶ native callable     (agreement leg 3)
           ──lift_llvm_cfg─────▶ hub IR again        (the round-trip law)

Loop mechanism: **phi** (the P5 decision — see PROGRAM_SYNTHESIS_P5_LLVM.md
§1). A `ProgWhile`'s loop-carried variables (assigned in the body,
bound before the loop) become header phis; the emitter is a minimal
SSA constructor over an environment of var → operand bindings, where a
pure copy (`x = y`, `x = 3`) is a REBIND that emits no instruction.

Scope — the frame is integers + structured control flow, exactly the
dialect the io/cfg modules speak. In scope:

  * ProgSeq / ProgAssignVar / ProgAugAssign(add|sub|mult) / ProgReturn
    over integer expressions (Plus/Minus/Times, BitAnd/Or/Xor,
    Shl/Lshr/Ashr, IDiv/IRem, Eq/Lt/Lte/Gt/Gte, IfThenElse → select,
    IfThenElse(cmp,1,0) → bare icmp);
  * ProgIfStmt → br_cond diamond (both-arms-return, guard clause, or
    join with phis for arm-assigned variables);
  * ProgWhile → single-latch loop with header phis;
  * ProgForEach over ProgCallExtern("range", …) → desugared counting
    loop (the loop variable is DROPPED after the loop: the while
    desugar leaves it at `stop`, CPython/ProgEval leave it at the last
    item — refusing post-loop reads beats silently diverging);
  * ProgDefFnParam at the top → i32 function parameters.

Everything else — containers, strings, floats, try/raise, calls,
comprehensions, nested control flow inside loop bodies or if arms —
is an honest ``{ok: False, blockers: [...]}`` refusal, never a partial
or speculative emission. In particular **ProgCallExtern does NOT emit
a `call`**: neither dialect parser speaks call (P2 §5), so emitted
call text would be unparseable by the frame's own reader; the refusal
`call_extern_unsupported:<name>` is the recorded frontier.

Per the architecture rule this is mechanical translation (graph/JSON
dialect → text), the exact mirror of the P2 lift: table-and-pattern
dispatch, no agent decisions; every unsupported shape is a recorded
blocker, never silent repair.
"""
from __future__ import annotations

import re
from typing import Any


class EmitRefusal(Exception):
    """An honest emission refusal; `.blocker` is the recorded reason."""

    def __init__(self, blocker: str) -> None:
        super().__init__(blocker)
        self.blocker = blocker


# ---------------------------------------------------------------------------
# op tables (the correspondence, write direction)
# ---------------------------------------------------------------------------

_BIN_OPS = {
    "Minus": "sub", "BitAnd": "and", "BitOr": "or", "BitXor": "xor",
    "Shl": "shl", "Lshr": "lshr", "Ashr": "ashr",
    "IDiv": "sdiv", "IRem": "srem",
}
_VARIADIC_OPS = {"Plus": "add", "Times": "mul"}
_CMP_PREDS = {"Eq": "eq", "Lt": "slt", "Lte": "sle", "Gt": "sgt", "Gte": "sge"}
# Predicate after commuting operands (literal-first comparisons are
# commuted so the .ll text never puts an immediate where the asm layer
# would need a cmpl destination).
_PRED_SWAP = {"eq": "eq", "slt": "sgt", "sle": "sge", "sgt": "slt",
              "sge": "sle"}
_AUG_OPS = {"add", "sub", "mult"}  # → Plus / Minus / Times
_CONTROL_TYPES = {"ProgIfStmt", "ProgWhile", "ProgForEach", "ProgTryOr",
                  "ProgLoopCtl"}
_NAME_RE = re.compile(r"^[A-Za-z_][\w.]*$")


def _stmts(x: Any) -> list[dict]:
    """Normalise a body field (None | stmt | ProgSeq | list) to a flat
    statement list."""
    if x is None:
        return []
    if isinstance(x, list):
        out: list[dict] = []
        for s in x:
            out.extend(_stmts(s))
        return out
    if isinstance(x, dict) and x.get("type") == "ProgSeq":
        return _stmts(x.get("stmts") or [])
    if isinstance(x, dict):
        return [x]
    raise EmitRefusal("malformed_stmt")


def _walk_types(stmts: list[dict]):
    for st in stmts:
        t = st.get("type")
        yield t
        # statement-list children only — expression subtrees can't
        # contain statements in this IR.
        for key in ("then", "orelse", "body", "stmts"):
            if key in st and st.get(key) is not None:
                yield from _walk_types(_stmts(st[key]))


def _writes(stmts: list[dict]) -> list[str]:
    """Ordered unique variable names assigned by `stmts` (flat)."""
    out: list[str] = []
    for st in stmts:
        if st.get("type") in ("ProgAssignVar", "ProgAugAssign"):
            n = st.get("name")
            if isinstance(n, str) and n not in out:
                out.append(n)
    return out


def _is_cmp(t: dict) -> bool:
    return isinstance(t, dict) and t.get("type") in _CMP_PREDS


def _is_cmp01(t: dict) -> bool:
    """IfThenElse(<cmp>, 1, 0) — the in-frame-integer comparison shape
    the P2 lift writes; emitted as a bare icmp."""
    if not (isinstance(t, dict) and t.get("type") == "IfThenElse"):
        return False
    then, other = t.get("then"), t.get("other")
    return (_is_cmp(t.get("cond"))
            and isinstance(then, dict) and then.get("type") == "Lit"
            and then.get("value") == 1
            and isinstance(other, dict) and other.get("type") == "Lit"
            and other.get("value") == 0)


def _is_lit_zero(t: Any) -> bool:
    return isinstance(t, dict) and t.get("type") == "Lit" \
        and t.get("value") == 0


class _Emitter:
    def __init__(self, fn_name: str, params: list[str]) -> None:
        self.fn_name = fn_name
        self.params = params
        self.blocks: list[list] = []      # [label, [lines]]
        self.cur: list | None = None
        self.env: dict[str, str] = {}
        self.used: set[str] = set()
        self.tcount = 0
        self.lcount = 0

    # -- plumbing ----------------------------------------------------------
    def new_block(self, label: str) -> None:
        self.blocks.append([label, []])
        self.cur = self.blocks[-1]

    def cur_label(self) -> str:
        assert self.cur is not None
        return self.cur[0]

    def line(self, s: str) -> None:
        assert self.cur is not None
        self.cur[1].append(f"  {s}")

    def fresh_label(self) -> str:
        self.lcount += 1
        return f"b{self.lcount}"

    def fresh_temp(self) -> str:
        while True:
            n = f"t{self.tcount}"
            self.tcount += 1
            if n not in self.used:
                self.used.add(n)
                return f"%{n}"

    def ssa_name(self, var: str) -> str:
        """A fresh SSA name for a (re)definition of program var `var`."""
        if var not in self.used:
            self.used.add(var)
            return f"%{var}"
        k = 2
        while f"{var}_{k}" in self.used:
            k += 1
        self.used.add(f"{var}_{k}")
        return f"%{var}_{k}"

    # -- expressions -------------------------------------------------------
    def emit_expr(self, t: Any, hint: str | None = None) -> str:
        """Emit `t`; return its operand string (register or literal).
        `hint` names the top instruction's result (assignment target)."""
        if not isinstance(t, dict):
            raise EmitRefusal("malformed_expr")
        ty = t.get("type")

        if ty == "Lit":
            v = t.get("value")
            if isinstance(v, bool):
                return "1" if v else "0"
            if isinstance(v, int):
                return str(v)
            raise EmitRefusal(f"non_integer_literal:{v!r}")

        if ty == "Var":
            name = t.get("name")
            if name not in self.env:
                raise EmitRefusal(f"unbound_var:{name}")
            return self.env[name]

        if ty in _VARIADIC_OPS:
            items = t.get("items") or []
            if not items:
                raise EmitRefusal(f"empty_variadic:{ty}")
            acc = self.emit_expr(items[0],
                                 hint if len(items) == 1 else None)
            op = _VARIADIC_OPS[ty]
            for i, child in enumerate(items[1:]):
                rhs = self.emit_expr(child)
                out = (hint if hint and i == len(items) - 2
                       else self.fresh_temp())
                self.line(f"{out} = {op} i32 {acc}, {rhs}")
                acc = out
            return acc

        if ty in _BIN_OPS:
            a = self.emit_expr(t.get("a"))
            b = self.emit_expr(t.get("b"))
            out = hint or self.fresh_temp()
            self.line(f"{out} = {_BIN_OPS[ty]} i32 {a}, {b}")
            return out

        if ty in _CMP_PREDS:
            return self.emit_cmp(t, hint)

        if ty == "IfThenElse":
            if _is_cmp01(t):
                return self.emit_cmp(t["cond"], hint)
            inner, flipped = self._unwrap_cond(t.get("cond"))
            if _is_cmp(inner):
                cond = self.emit_cmp(inner)
            elif _is_cmp01(inner):
                cond = self.emit_cmp(inner["cond"])
            else:
                cond = self.emit_expr(inner)
            then_t, other_t = t.get("then"), t.get("other")
            if flipped:
                # Inverted condition → swap the arms instead of
                # materialising an inversion instruction.
                then_t, other_t = other_t, then_t
            a = self.emit_expr(then_t)
            b = self.emit_expr(other_t)
            out = hint or self.fresh_temp()
            self.line(f"{out} = select i1 {cond}, i32 {a}, i32 {b}")
            return out

        raise EmitRefusal(f"unsupported_expr:{ty}")

    def emit_cmp(self, t: dict, hint: str | None = None) -> str:
        pred = _CMP_PREDS[t["type"]]
        a = self.emit_expr(t.get("a"))
        b = self.emit_expr(t.get("b"))
        if not a.startswith("%") and not b.startswith("%"):
            # Both literal: materialise the lhs (cmpl can't take two
            # immediates downstream).
            m = self.fresh_temp()
            self.line(f"{m} = add i32 {a}, 0")
            a = m
        elif not a.startswith("%"):
            # Commute so the immediate is the SECOND operand.
            a, b = b, a
            pred = _PRED_SWAP[pred]
        out = hint or self.fresh_temp()
        self.line(f"{out} = icmp {pred} i32 {a}, {b}")
        return out

    @staticmethod
    def _unwrap_cond(cond: Any) -> tuple[Any, bool]:
        """Strip truthiness wrappers: Not(x) flips; Eq(x, 0) flips.
        Returns (inner, flipped)."""
        flipped = False
        while isinstance(cond, dict):
            ty = cond.get("type")
            if ty == "Not":
                cond = cond.get("arg")
                flipped = not flipped
                continue
            if ty == "Eq" and _is_lit_zero(cond.get("b")) \
                    and not _is_lit_zero(cond.get("a")):
                cond = cond.get("a")
                flipped = not flipped
                continue
            break
        return cond, flipped

    def emit_cond_branch(self, cond: Any, t_label: str,
                         f_label: str) -> None:
        inner, flipped = self._unwrap_cond(cond)
        if flipped:
            t_label, f_label = f_label, t_label
        if _is_cmp(inner):
            v = self.emit_cmp(inner)
        elif _is_cmp01(inner):
            v = self.emit_cmp(inner["cond"])
        else:
            v = self.emit_expr(inner)
        self.line(f"br i1 {v}, label %{t_label}, label %{f_label}")

    # -- statements --------------------------------------------------------
    def _refuse_nested_control(self, stmts: list[dict],
                               where: str) -> None:
        for ty in _walk_types(stmts):
            if ty in _CONTROL_TYPES:
                raise EmitRefusal(f"nested_control_unsupported:{where}")

    @staticmethod
    def _check_returns(stmts: list[dict]) -> bool:
        """True iff the list ends with ProgReturn; a mid-list return is
        unreachable code → refuse."""
        for i, st in enumerate(stmts):
            if st.get("type") == "ProgReturn" and i != len(stmts) - 1:
                raise EmitRefusal("unreachable_code")
        return bool(stmts) and stmts[-1].get("type") == "ProgReturn"

    def emit_stmts(self, stmts: list[dict]) -> bool:
        """Emit; returns True if the statement stream terminated (ret on
        every path)."""
        i = 0
        while i < len(stmts):
            st = stmts[i]
            ty = st.get("type")
            if ty == "ProgSeq":
                merged = _stmts(st) + stmts[i + 1:]
                return self.emit_stmts(merged)
            if ty == "ProgDefFnParam":
                raise EmitRefusal("param_not_at_top")
            if ty == "ProgReturn":
                if i != len(stmts) - 1:
                    raise EmitRefusal("unreachable_code")
                v = self.emit_expr(st.get("value"))
                self.line(f"ret i32 {v}")
                return True
            if ty in ("ProgAssignVar", "ProgAugAssign"):
                self.emit_assign(st)
            elif ty == "ProgIfStmt":
                terminated = self.emit_if(st, rest=stmts[i + 1:])
                if terminated:
                    return True
                # emit_if consumed nothing beyond itself when it
                # returns False; continue with the rest here.
            elif ty == "ProgWhile":
                self.emit_while(st)
            elif ty == "ProgForEach":
                self.emit_foreach(st)
            else:
                raise EmitRefusal(f"unsupported_stmt:{ty}")
            i += 1
        return False

    def emit_assign(self, st: dict) -> None:
        name = st.get("name")
        if not (isinstance(name, str) and _NAME_RE.match(name)):
            raise EmitRefusal(f"invalid_identifier:{name!r}")
        value = st.get("value")
        if st.get("type") == "ProgAugAssign":
            op = st.get("op")
            if op not in _AUG_OPS:
                raise EmitRefusal(f"augassign_op_unsupported:{op}")
            base = {"type": "Var", "name": name}
            value = ({"type": "Plus", "items": [base, value]} if op == "add"
                     else {"type": "Minus", "a": base, "b": value}
                     if op == "sub"
                     else {"type": "Times", "items": [base, value]})
        if isinstance(value, dict) and value.get("type") == "ProgCallExtern":
            raise EmitRefusal(
                f"call_extern_unsupported:{value.get('name')}")
        if isinstance(value, dict) and value.get("type") in ("Var", "Lit"):
            # Pure copy → rebind, no instruction (SSA has no copies).
            self.env[name] = self.emit_expr(value)
            return
        self.env[name] = self.emit_expr(value, hint=self.ssa_name(name))

    def emit_if(self, st: dict, rest: list[dict]) -> bool:
        then_stmts = _stmts(st.get("then"))
        else_stmts = _stmts(st.get("orelse"))
        self._refuse_nested_control(then_stmts, "if_arm")
        self._refuse_nested_control(else_stmts, "if_arm")
        t_ret = self._check_returns(then_stmts)
        e_ret = self._check_returns(else_stmts)

        if t_ret and e_ret:
            tl, el = self.fresh_label(), self.fresh_label()
            self.emit_cond_branch(st.get("cond"), tl, el)
            base = dict(self.env)
            self.new_block(tl)
            self.emit_stmts(then_stmts)
            self.env = dict(base)
            self.new_block(el)
            self.emit_stmts(else_stmts)
            self.env = dict(base)
            if rest:
                raise EmitRefusal("unreachable_code")
            return True

        if t_ret:  # guard clause: else (if any) merges into continuation
            tl, cont = self.fresh_label(), self.fresh_label()
            self.emit_cond_branch(st.get("cond"), tl, cont)
            base = dict(self.env)
            self.new_block(tl)
            self.emit_stmts(then_stmts)
            self.env = dict(base)
            self.new_block(cont)
            if else_stmts:
                self.emit_stmts(else_stmts)
            return False

        if e_ret:  # mirrored guard: then merges into continuation
            cont, el = self.fresh_label(), self.fresh_label()
            self.emit_cond_branch(st.get("cond"), cont, el)
            base = dict(self.env)
            self.new_block(el)
            self.emit_stmts(else_stmts)
            self.env = dict(base)
            self.new_block(cont)
            self.emit_stmts(then_stmts)
            return False

        # Neither arm returns → join (phis for arm-assigned variables).
        base = dict(self.env)
        tl = self.fresh_label()
        el = self.fresh_label() if else_stmts else None
        jl = self.fresh_label()
        from_label = self.cur_label()
        self.emit_cond_branch(st.get("cond"), tl, el or jl)

        self.new_block(tl)
        self.env = dict(base)
        self.emit_stmts(then_stmts)
        env_t = dict(self.env)
        then_end = self.cur_label()
        self.line(f"br label %{jl}")

        if else_stmts:
            self.new_block(el)  # type: ignore[arg-type]
            self.env = dict(base)
            self.emit_stmts(else_stmts)
            env_e = dict(self.env)
            else_end = self.cur_label()
            self.line(f"br label %{jl}")
        else:
            env_e = dict(base)
            else_end = from_label

        self.new_block(jl)
        self.env = dict(base)
        ordered = _writes(then_stmts) + [
            v for v in _writes(else_stmts) if v not in _writes(then_stmts)]
        for v in ordered:
            in_t, in_e = v in env_t, v in env_e
            if in_t and in_e:
                if env_t[v] == env_e[v]:
                    self.env[v] = env_t[v]
                else:
                    nm = self.ssa_name(v)
                    self.line(
                        f"{nm} = phi i32 [ {env_t[v]}, %{then_end} ], "
                        f"[ {env_e[v]}, %{else_end} ]")
                    self.env[v] = nm
            else:
                # One-sided definition: not available past the join
                # (the lift refuses reads of it too).
                self.env.pop(v, None)
        return False

    def emit_while(self, st: dict) -> None:
        if st.get("orelse"):
            raise EmitRefusal("while_orelse_unsupported")
        body = _stmts(st.get("body"))
        self._refuse_nested_control(body, "loop_body")
        for ty in _walk_types(body):
            if ty == "ProgReturn":
                raise EmitRefusal("return_in_loop_unsupported")
        writes = _writes(body)
        carried = [v for v in writes if v in self.env]

        hl, bl, xl = (self.fresh_label(), self.fresh_label(),
                      self.fresh_label())
        pre_label = self.cur_label()
        pre_vals = {v: self.env[v] for v in carried}
        self.line(f"br label %{hl}")

        self.new_block(hl)
        header_block = self.cur
        phi_slots: dict[str, tuple[int, str]] = {}
        for v in carried:
            nm = self.ssa_name(v)
            header_block[1].append(None)  # placeholder, patched below
            phi_slots[v] = (len(header_block[1]) - 1, nm)
            self.env[v] = nm
        env_header = dict(self.env)
        self.emit_cond_branch(st.get("cond"), bl, xl)

        self.new_block(bl)
        self.env = dict(env_header)
        self.emit_stmts(body)
        latch_label = self.cur_label()
        latch_vals = {v: self.env[v] for v in carried}
        self.line(f"br label %{hl}")

        for v in carried:
            idx, nm = phi_slots[v]
            header_block[1][idx] = (
                f"  {nm} = phi i32 [ {pre_vals[v]}, %{pre_label} ], "
                f"[ {latch_vals[v]}, %{latch_label} ]")

        self.new_block(xl)
        self.env = dict(env_header)  # carried → phi names; locals dropped

    def emit_foreach(self, st: dict) -> None:
        if st.get("orelse"):
            raise EmitRefusal("foreach_orelse_unsupported")
        it = st.get("iter")
        if not (isinstance(it, dict)
                and it.get("type") == "ProgCallExtern"
                and it.get("name") == "range"
                and not it.get("recv")
                and len(it.get("args") or []) in (1, 2)):
            raise EmitRefusal("foreach_iter_unsupported")
        var = st.get("var")
        if not (isinstance(var, str) and _NAME_RE.match(var)):
            raise EmitRefusal(f"invalid_identifier:{var!r}")
        args = it["args"]
        start = args[0] if len(args) == 2 else {"type": "Lit", "value": 0}
        stop = args[-1]
        # Evaluate `stop` ONCE before the loop (range semantics), bound
        # under a reserved name the body cannot write.
        stop_key = f"__range_stop_{self.lcount}"
        self.env[stop_key] = self.emit_expr(stop)
        self.emit_assign({"type": "ProgAssignVar", "name": var,
                          "value": start})
        body = _stmts(st.get("body")) + [{
            "type": "ProgAssignVar", "name": var,
            "value": {"type": "Plus",
                      "items": [{"type": "Var", "name": var},
                                {"type": "Lit", "value": 1}]}}]
        self.emit_while({
            "type": "ProgWhile",
            "cond": {"type": "Lt", "a": {"type": "Var", "name": var},
                     "b": {"type": "Var", "name": stop_key}},
            "body": {"type": "ProgSeq", "stmts": body},
            "orelse": None})
        # Post-loop, the desugared var holds `stop`, not the last item
        # (CPython/ProgEval semantics) — drop it so a post-loop read is
        # an honest refusal instead of a silent divergence.
        self.env.pop(var, None)
        self.env.pop(stop_key, None)

    # -- top level ---------------------------------------------------------
    def run(self, stmts: list[dict]) -> str:
        for p in self.params:
            if not _NAME_RE.match(p):
                raise EmitRefusal(f"invalid_identifier:{p!r}")
            self.used.add(p)
            self.env[p] = f"%{p}"
        self.new_block("entry")
        terminated = self.emit_stmts(stmts)
        if not terminated:
            raise EmitRefusal("missing_return")
        header = ", ".join(f"i32 %{p}" for p in self.params)
        out = [f"define i32 @{self.fn_name}({header}) {{"]
        for label, lines in self.blocks:
            out.append(f"{label}:")
            out.extend(lines)
        out.append("}")
        return "\n".join(out) + "\n"


def emit_prog_to_llvm(prog: dict, fn_name: str = "f",
                      params: list[str] | None = None) -> dict:
    """Emit hub Program-IR Term-JSON as LLVM IR text (the dialect
    `parse_llvm_cfg` speaks).

    Returns ``{"ok": True, "text": <.ll>, "params": [...], "blockers": []}``
    or ``{"ok": False, "text": None, "params": None, "blockers": [...]}``.

    Function parameters come from leading ``ProgDefFnParam`` statements,
    or from `params` (which wins when given — the lift drops DefFnParam,
    so re-emission of a lifted program passes them explicitly).
    """
    try:
        stmts = _stmts(prog)
        ir_params: list[str] = []
        while stmts and stmts[0].get("type") == "ProgDefFnParam":
            p = stmts.pop(0)
            if p.get("default") is not None:
                raise EmitRefusal("param_default_unsupported")
            name = p.get("name")
            if not isinstance(name, str):
                raise EmitRefusal(f"invalid_identifier:{name!r}")
            ir_params.append(name)
        for st in stmts:
            if st.get("type") == "ProgDefFnParam":
                raise EmitRefusal("param_not_at_top")
        use_params = list(params) if params is not None else ir_params
        text = _Emitter(fn_name, use_params).run(stmts)
    except EmitRefusal as e:
        return {"ok": False, "text": None, "params": None,
                "blockers": [e.blocker]}
    return {"ok": True, "text": text, "params": use_params, "blockers": []}


__all__ = ["emit_prog_to_llvm", "EmitRefusal"]
