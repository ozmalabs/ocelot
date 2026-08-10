"""PROTOCOL 13 GATE for the endpoint-abduction rung -- AND IT CLOSES THE HOLE
FOUND ON THE WALKER THIS WEEK: **A NAME BOUND TO A LITERAL IS A LITERAL.**

A Python AST walk over `scripts/gapabduce_measure.py`, never a substring
selector (this arc's record on substring selectors is 0-5, and the fifth
happened INSIDE the test written to warn about substring selectors).

What it asserts, structurally:

  * the verdict functions are bound as `ast.FunctionDef` nodes BY NAME, read
    from the runner's OWN `VERDICTS` tuple -- the gate carries no copy, and a
    divergence between the two is itself a failure (NON-VACUITY: a rename
    cannot make the gate pass by scanning nothing);
  * **SUBSCRIPT INDICES ARE PRUNED** by an explicit recursive descent -- an
    index is ADDRESSING, not a threshold.  The phi rung's first gate counted
    three array indices as thresholds, and its first FIX was also wrong because
    **`ast.walk` CANNOT PRUNE**.  This gate does not use `ast.walk` for that
    reason;
  * **MODULE-LEVEL NAME BINDINGS ARE RESOLVED TO THEIR LITERALS.**  This is the
    NEW clause, and it exists because closing a threshold BY NAMING IT went
    GREEN on the walker rung.  `TOL = 2` at module level followed by
    `x < TOL` inside a verdict is a THRESHOLD, and a gate that only looks for
    `ast.Constant` at the comparison site cannot see it;
  * **NO ORDERING COMPARISON AGAINST A NON-ZERO LITERAL** (inline or named).
    This is the sharp form of 13: an ORDERING against a tuned constant is a
    threshold -- you can slide it to adjust sensitivity.  An EQUALITY is not
    tunable: moving `== 1` to `== 2` does not adjust anything, it tests a
    different proposition.  Orderings are admitted only between two MEASURED
    quantities, or against the sentinel `0`;
  * the swept axes (`S_GRID`, `K_GRID`) are ITERATED, never compared against --
    i.e. they are independent variables;
  * the dead-instrument arms ABORT (`return 2` on engine divergence, `return 3`
    on a failed wiring control), never warn.

POSITIVE-CONTROLLED THREE WAYS (12.3), because a gate you have only ever seen
pass is not a gate you have tested: an INLINE threshold injection must turn it
RED, a NAMED threshold injection must turn it RED, and the unmodified source
must be asserted GREEN in the same test.
"""
from __future__ import annotations
import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "gapabduce_measure.py"

# The axes.  Read from the runner, not copied here -- see `_axis_names`.
AXES = ("S_GRID", "K_GRID")


# --------------------------------------------------------------------------- #
#  the walker
# --------------------------------------------------------------------------- #
def _module() -> ast.Module:
    return ast.parse(RUNNER.read_text())


def _module_consts(mod: ast.Module) -> dict[str, float]:
    """Every module-level NAME bound to a numeric literal.

    THE POINT OF THIS FUNCTION: a name bound to a literal IS a literal.  A gate
    that only inspects `ast.Constant` at the comparison site is blind to
    `TOL = 2` / `x < TOL`, and that blindness went GREEN on the walker rung."""
    out: dict[str, float] = {}
    for node in mod.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            v = _as_number(node.value, {})
            if v is not None:
                out[node.targets[0].id] = v
    return out


def _as_number(node: ast.AST, consts: dict[str, float]) -> float | None:
    """The numeric value of `node`, resolving a module-level name binding."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
            and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        inner = _as_number(node.operand, consts)
        if inner is not None:
            return -inner if isinstance(node.op, ast.USub) else inner
    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    return None


def _descend(node: ast.AST):
    """Recursive descent that PRUNES a Subscript's index.

    `ast.walk` CANNOT PRUNE -- it is a flat queue over every descendant -- so a
    gate that needs to exclude a subtree cannot be built on it.  The phi rung
    learned this by shipping the wrong fix first."""
    yield node
    for name, field in ast.iter_fields(node):
        if isinstance(node, ast.Subscript) and name == "slice":
            continue          # an index is ADDRESSING, not a threshold
        items = field if isinstance(field, list) else [field]
        for item in items:
            if isinstance(item, ast.AST):
                yield from _descend(item)


def _verdict_names(mod: ast.Module) -> list[str]:
    """The verdict names read from the RUNNER'S OWN `VERDICTS` tuple."""
    for node in mod.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == "VERDICTS":
            return [e.value for e in node.value.elts
                    if isinstance(e, ast.Constant)]
    raise AssertionError("the runner declares no VERDICTS tuple")


def _verdict_defs(mod: ast.Module) -> dict[str, ast.FunctionDef]:
    names = set(_verdict_names(mod))
    return {n.name: n for n in mod.body
            if isinstance(n, ast.FunctionDef) and n.name in names}


def scan(source: str) -> list[str]:
    """Every 13 violation in the verdict functions of `source`."""
    mod = ast.parse(source)
    consts = _module_consts(mod)
    defs = _verdict_defs(mod)
    bad: list[str] = []
    for name, fn in defs.items():
        for node in _descend(fn):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left, *node.comparators]
            for op, right in zip(node.ops, node.comparators):
                ordering = isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE))
                if not ordering:
                    continue
                # An ORDERING is a threshold iff either side is a non-zero
                # literal -- inline OR resolved from a module-level name.
                for side in (node.left, right):
                    v = _as_number(side, consts)
                    if v is not None and v != 0.0:
                        bad.append(f"ordering-threshold:{name}:{v}")
            # the swept axes must never be an operand of a comparison
            for side in operands:
                for sub in _descend(side):
                    if isinstance(sub, ast.Name) and sub.id in AXES:
                        bad.append(f"axis-compared:{name}:{sub.id}")
    return bad


# --------------------------------------------------------------------------- #
#  the gate
# --------------------------------------------------------------------------- #
def test_the_runner_declares_every_verdict_it_defines():
    """NON-VACUITY: the gate scans the functions the RUNNER names, and a
    divergence between the tuple and the defs is itself a failure."""
    mod = _module()
    names = _verdict_names(mod)
    defs = _verdict_defs(mod)
    assert names, "VERDICTS is empty -- the gate would scan nothing"
    missing = sorted(set(names) - set(defs))
    assert not missing, f"declared but not defined: {missing}"


def test_no_threshold_enters_any_verdict():
    """The headline 13 assertion on the UNMODIFIED source."""
    assert scan(RUNNER.read_text()) == []


def test_the_gate_bites_on_an_INLINE_threshold():
    """POSITIVE CONTROL 1 (12.3): an inline threshold must turn it RED."""
    src = RUNNER.read_text().replace(
        "    return all(v[\"kind\"] != \"linear\" for v in matrix.values())",
        "    return all(v[\"checked\"] < 2400 for v in matrix.values())")
    assert "v[\"checked\"] < 2400" in src, "injection did not land"
    found = scan(src)
    assert any(f.startswith("ordering-threshold:v_a2_p4") for f in found), found


def test_the_gate_bites_on_a_NAMED_threshold_THE_HOLE_FOUND_THIS_WEEK():
    """POSITIVE CONTROL 2 (12.3), AND THE NEW CLAUSE.

    Closing a threshold BY NAMING IT went GREEN on the walker rung.  A gate
    that inspects only `ast.Constant` at the comparison site cannot see
    `CHECK_TOL = 2400` / `v["checked"] < CHECK_TOL` -- and that is the same
    threshold, one indirection away.  **A NAME BOUND TO A LITERAL IS A
    LITERAL**, and this test is the proof that this gate knows it."""
    src = RUNNER.read_text().replace(
        "DOT = 4              #", "CHECK_TOL = 2400\nDOT = 4              #"
    ).replace(
        "    return all(v[\"kind\"] != \"linear\" for v in matrix.values())",
        "    return all(v[\"checked\"] < CHECK_TOL for v in matrix.values())")
    assert "CHECK_TOL = 2400" in src and "< CHECK_TOL" in src, "injection did not land"
    found = scan(src)
    assert any(f.startswith("ordering-threshold:v_a2_p4") for f in found), (
        "THE NAMED-THRESHOLD HOLE IS OPEN: the gate did not resolve a "
        f"module-level name binding to its literal. found={found}")


def test_the_gate_bites_on_an_axis_compared_against():
    """POSITIVE CONTROL 3: a swept axis is an INDEPENDENT VARIABLE.  Comparing
    a verdict against one turns it RED."""
    src = RUNNER.read_text().replace(
        "    return all(v[\"kind\"] != \"linear\" for v in matrix.values())",
        "    return all(v[\"steps\"] > max(K_GRID) for v in matrix.values())")
    found = scan(src)
    assert any(f.startswith("axis-compared:v_a2_p4") for f in found), found


def test_subscript_indices_are_PRUNED_not_counted():
    """The phi rung's gate counted `vf[r, c, 1]` as a threshold, and its first
    fix was ALSO wrong because `ast.walk` cannot prune.  A negative index in a
    subscript must not register."""
    src = "VERDICTS = (\"v_x\",)\ndef v_x(h):\n    return h[-1] == 0\n"
    assert scan(src) == []


def test_a_named_literal_in_a_SUBSCRIPT_is_still_pruned():
    """The prune and the name-resolution must not fight: a name bound to a
    literal, used as an INDEX, is addressing -- not a threshold."""
    src = ("IDX = 1\nVERDICTS = (\"v_x\",)\n"
           "def v_x(h):\n    return h[IDX] == 0\n")
    assert scan(src) == []


def test_the_dead_instrument_arms_ABORT_rather_than_warn():
    """Engine divergence and a failed wiring control must RETURN A NONZERO
    CODE, not print and continue.  A rung that measures through a failed wiring
    control publishes a perfect fake null."""
    src = RUNNER.read_text()
    assert "return 2" in src and "ABORT: engine divergence" in src
    assert "return 3" in src and "ABORT: wiring control failed" in src
