"""LLVM IR interpreter — concrete-value evaluation of substrate-resident IR.

Walks the substrate graph from a result value back through its producers,
computing each instruction's value from its operands' values, with a
binding map for input SSA values (function parameters).

This is the **verification primitive**: it lets the agent (and tests)
prove that optimization pipelines preserve semantics. Differential
testing — interpret before optimization, optimize, interpret after,
assert the values agree on random inputs — turns the abstract validity
arguments in `compiler_theory.json` into concrete demonstrations.

Per the architecture rule this is a world-adapter-shaped function:
mechanical translation from graph state to a concrete value. No
decisions over graph state, no reasoning — just compute.

Semantics match the runtime semantics the LLVM IR text adapter speaks:

  * Integer arithmetic: i64 wrapping (Python int → wrap at i64 boundary)
  * Bitwise: as `i64`
  * Shifts: out-of-range counts return 0 (substrate convention, matches
    the IDiv/IRem silent-zero pattern; LLVM calls this poison)
  * Signed division/remainder: truncate toward zero, sign follows dividend
  * Comparison: returns 1 (true) or 0 (false)
  * select: standard ternary

Divide-by-zero raises `ZeroDivisionError` — the interpreter exposes the
trap that LLVM's UB would also expose. Folding rules with the UB-guard
clause refuse to fold these cases, so the trap stays in the runtime.
"""
from __future__ import annotations


_I64_MOD = 1 << 64
_I64_MIN = -(1 << 63)
_I64_MAX = (1 << 63) - 1


def _wrap_i64(v: int) -> int:
    """Two's-complement wrap a Python int into the i64 range."""
    v = v % _I64_MOD
    if v > _I64_MAX:
        v -= _I64_MOD
    return v


def interpret(substrate, root: int, bindings: dict[int, int]) -> int:
    """Compute the runtime value of `root` (an LLVMValue or LLVMConstant
    NodeID) under `bindings` (NodeID → int for input LLVMValues).

    Recursive — caches via the bindings dict so a shared subexpression
    is computed once per call."""
    # Already-bound value (input parameter, or memoized result).
    if root in bindings:
        return bindings[root]

    node = substrate.node(root)
    ntype = node["type"]

    if ntype == "LLVMConstant":
        v = node["attrs"]["value"]
        return _wrap_i64(int(v))

    if ntype != "LLVMValue":
        raise ValueError(
            f"interpret({root}): expected LLVMValue or LLVMConstant; "
            f"got {ntype!r}"
        )

    producers = substrate.in_neighbours(root, "produces")
    if not producers:
        raise ValueError(
            f"interpret({root}): no producer and no binding — is this "
            f"a function input that wasn't bound?"
        )
    inst = producers[0]
    opcode = substrate.node(inst)["attrs"]["opcode"]

    if opcode == "phi":
        # A phi's value is path-dependent — only the forward interpreter
        # (interpret_cfg), which knows the edge taken, can commit it.
        # Refuse BEFORE walking operands: a loop phi's latch operand
        # chain leads back to the phi itself (unbounded recursion).
        raise ValueError(
            "interpret: phi is path-dependent — use interpret_cfg "
            "(the backward producer-walk cannot evaluate it)"
        )

    # All instructions we support take >= 1 operand.
    op0 = interpret(substrate, substrate.neighbours(inst, "uses_op0")[0], bindings)

    if opcode == "ret":
        result = op0
        bindings[root] = result
        return result

    # Two-operand ops.
    op1 = interpret(substrate, substrate.neighbours(inst, "uses_op1")[0], bindings)

    def _shift_count(b):
        # 0..63 inclusive; otherwise the substrate convention returns 0.
        return b if 0 <= b < 64 else None

    if opcode == "add":   result = _wrap_i64(op0 + op1)
    elif opcode == "sub": result = _wrap_i64(op0 - op1)
    elif opcode == "mul": result = _wrap_i64(op0 * op1)
    elif opcode == "and": result = op0 & op1
    elif opcode == "or":  result = op0 | op1
    elif opcode == "xor": result = op0 ^ op1
    elif opcode == "shl":
        n = _shift_count(op1)
        result = _wrap_i64(op0 << n) if n is not None else 0
    elif opcode == "lshr":
        n = _shift_count(op1)
        if n is None:
            result = 0
        else:
            au = op0 & ((1 << 64) - 1)
            result = _wrap_i64(au >> n)
    elif opcode == "ashr":
        n = _shift_count(op1)
        if n is None:
            result = 0 if op0 >= 0 else -1
        else:
            result = op0 >> n  # Python int >> is arithmetic
    elif opcode == "sdiv":
        if op1 == 0:
            # LLVM UB. The folding rules' guard means we never reach
            # this from valid programs that the optimizer touched.
            raise ZeroDivisionError("sdiv by 0 — LLVM undefined behaviour")
        # Truncate toward zero (C / LLVM sdiv semantics).
        q = op0 // op1
        if (op0 % op1 != 0) and ((op0 < 0) != (op1 < 0)):
            q += 1
        result = _wrap_i64(q)
    elif opcode == "srem":
        if op1 == 0:
            raise ZeroDivisionError("srem by 0 — LLVM undefined behaviour")
        q = op0 // op1
        if (op0 % op1 != 0) and ((op0 < 0) != (op1 < 0)):
            q += 1
        result = _wrap_i64(op0 - q * op1)
    elif opcode == "icmp_eq":  result = 1 if op0 == op1 else 0
    elif opcode == "icmp_ne":  result = 0 if op0 == op1 else 1
    elif opcode == "icmp_slt": result = 1 if op0 < op1 else 0
    elif opcode == "icmp_sle": result = 1 if op0 <= op1 else 0
    elif opcode == "icmp_sgt": result = 1 if op0 > op1 else 0
    elif opcode == "icmp_sge": result = 1 if op0 >= op1 else 0
    elif opcode == "select":
        op2 = interpret(substrate,
                        substrate.neighbours(inst, "uses_op2")[0],
                        bindings)
        result = op1 if op0 else op2
    else:
        raise ValueError(f"interpret: unsupported opcode {opcode!r}")

    bindings[root] = result
    return result


__all__ = ["interpret"]
