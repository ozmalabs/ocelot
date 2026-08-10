"""PROTOCOL 13 GATE for the motion-energy rung.

A Python AST walk over `scripts/motion_energy_measure.py`, never a substring
selector (this arc's record on substring selectors is 0-5).  Adapted from
`test_gapabduce_ast_migrated.py`, whose clauses this reuses verbatim:

  * the verdict functions are read from the runner's OWN `VERDICTS` tuple (a
    divergence is itself a failure -- NON-VACUITY);
  * SUBSCRIPT INDICES ARE PRUNED by explicit descent (`ast.walk` cannot prune);
  * MODULE-LEVEL NAME BINDINGS ARE RESOLVED TO THEIR LITERALS (a name bound to a
    literal IS a literal);
  * NO ORDERING COMPARISON AGAINST A NON-ZERO LITERAL (inline or named) -- an
    ordering against a tuned constant is slidable, hence a threshold; an EQUALITY
    is not tunable; orderings are admitted ONLY between two MEASURED quantities
    or against the sentinel `0`.  This is exactly why the motion-energy verdicts
    are clean: `opponent > 0.0` / `< 0.0` (sign against 0), `kstar != 0`
    (equality), `R[k*] > R[0]` and `abs(cnull) < abs(cpos)` (MEASURED vs
    MEASURED), `opp_perframe == 0.0` (equality);
  * the swept axes (`S_GRID`, `K_GRID`) are ITERATED, never COMPARED against;
  * the dead-instrument arms ABORT (`return 2` engine divergence, `return 3`
    failed control), never warn.

POSITIVE-CONTROLLED (12.3): an INLINE non-zero-literal ordering must turn it RED,
a NAMED one must turn it RED, an axis comparison must turn it RED, and the
unmodified source must be asserted GREEN in the same suite.
"""
from __future__ import annotations
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "motion_energy_measure.py"

AXES = ("S_GRID", "K_GRID")

# the exact verdict body the positive controls overwrite
_FALS_BODY = "    return all(R[0] >= R[k] for k in K_GRID)"


def _module() -> ast.Module:
    return ast.parse(RUNNER.read_text())


def _as_number(node: ast.AST, consts: dict[str, float]):
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


def _module_consts(mod: ast.Module) -> dict[str, float]:
    out: dict[str, float] = {}
    for node in mod.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            v = _as_number(node.value, {})
            if v is not None:
                out[node.targets[0].id] = v
    return out


def _descend(node: ast.AST):
    """Recursive descent that PRUNES a Subscript's index (an index is
    addressing, not a threshold).  `ast.walk` cannot prune."""
    yield node
    for name, field in ast.iter_fields(node):
        if isinstance(node, ast.Subscript) and name == "slice":
            continue
        items = field if isinstance(field, list) else [field]
        for item in items:
            if isinstance(item, ast.AST):
                yield from _descend(item)


def _verdict_names(mod: ast.Module) -> list[str]:
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
                if not isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                    continue  # equality is not tunable
                for side in (node.left, right):
                    v = _as_number(side, consts)
                    if v is not None and v != 0.0:
                        bad.append(f"ordering-threshold:{name}:{v}")
            for side in operands:
                for sub in _descend(side):
                    if isinstance(sub, ast.Name) and sub.id in AXES:
                        bad.append(f"axis-compared:{name}:{sub.id}")
    return bad


def test_the_runner_declares_every_verdict_it_defines():
    mod = _module()
    names = _verdict_names(mod)
    defs = _verdict_defs(mod)
    assert names, "VERDICTS is empty -- the gate would scan nothing"
    missing = sorted(set(names) - set(defs))
    assert not missing, f"declared but not defined: {missing}"


def test_no_threshold_enters_any_verdict():
    assert scan(RUNNER.read_text()) == []


def test_the_gate_bites_on_an_INLINE_threshold():
    src = RUNNER.read_text().replace(
        _FALS_BODY, "    return all(R[k] < 0.5 for k in K_GRID)")
    assert "R[k] < 0.5" in src, "injection did not land"
    found = scan(src)
    assert any(f.startswith("ordering-threshold:v_isi_falsified") for f in found), found


def test_the_gate_bites_on_a_NAMED_threshold():
    # inject a named threshold at module scope + use it in a verdict, one
    # indirection away from an inline literal.
    src = "MEV_TOL = 0.5\n" + RUNNER.read_text().replace(
        _FALS_BODY, "    return all(R[k] < MEV_TOL for k in K_GRID)")
    assert "MEV_TOL = 0.5" in src and "< MEV_TOL" in src, "injection did not land"
    found = scan(src)
    assert any(f.startswith("ordering-threshold:v_isi_falsified") for f in found), (
        "THE NAMED-THRESHOLD HOLE IS OPEN: the gate did not resolve a "
        f"module-level name binding to its literal. found={found}")


def test_the_gate_bites_on_an_axis_compared_against():
    src = RUNNER.read_text().replace(
        _FALS_BODY, "    return all(R[k] > max(K_GRID) for k in K_GRID)")
    found = scan(src)
    assert any(f.startswith("axis-compared:v_isi_falsified") for f in found), found


def test_subscript_indices_are_PRUNED_not_counted():
    src = "VERDICTS = (\"v_x\",)\ndef v_x(h):\n    return h[-1] == 0\n"
    assert scan(src) == []


def test_a_named_literal_in_a_SUBSCRIPT_is_still_pruned():
    src = ("IDX = 1\nVERDICTS = (\"v_x\",)\n"
           "def v_x(h):\n    return h[IDX] == 0\n")
    assert scan(src) == []


def test_the_dead_instrument_arms_ABORT_rather_than_warn():
    src = RUNNER.read_text()
    assert "return 2" in src and "ABORT: engine divergence" in src
    assert "return 3" in src and "ABORT: control failed" in src
