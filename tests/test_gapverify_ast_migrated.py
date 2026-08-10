"""PROTOCOL 13 GATE for the intermediate-verification rung.

A Python AST walk over `scripts/gapverify_measure.py`, never a substring
selector (this arc's record on substring selectors is 0-5, and the fifth
happened INSIDE the test written to warn about substring selectors).

The machinery is the gapabduce rung's, carried forward deliberately rather than
re-invented -- including the clause it earned (**A NAME BOUND TO A LITERAL IS A
LITERAL**) and the reason it cannot be built on `ast.walk` (**`ast.walk` CANNOT
PRUNE**, so a Subscript's index -- which is ADDRESSING, not a threshold --
cannot be excluded from a flat queue).

What it asserts, structurally:

  * the verdict functions are bound as `ast.FunctionDef` nodes BY NAME, read
    from the runner's OWN `VERDICTS` tuple -- the gate carries no copy, and a
    divergence between the two is itself a failure (NON-VACUITY);
  * SUBSCRIPT INDICES ARE PRUNED by an explicit recursive descent;
  * MODULE-LEVEL NAME BINDINGS ARE RESOLVED TO THEIR LITERALS;
  * NO ORDERING COMPARISON AGAINST A NON-ZERO LITERAL, inline or named.  An
    ordering against a constant is a threshold -- you can SLIDE it to adjust
    sensitivity.  An EQUALITY is not tunable: moving `== 1` to `== 2` tests a
    different proposition.  Orderings are admitted only between two MEASURED
    quantities, or against the sentinel `0`;
  * the swept axes (`S_GRID`, `K_GRID`, `T_GRID`) are ITERATED, never compared
    against -- they are independent variables;
  * the dead-instrument arms ABORT (`return 2` on engine divergence, `return 3`
    on a failed wiring control), never warn.

**WHY THIS RUNG'S REGISTERED PREDICTIONS ARE NOT THRESHOLDS.** `CLIFF_VERIFIED`
and `CLIFF_DISAGREE` are compared by SET EQUALITY against a prediction written
into the pre-registration BEFORE the run.  That is 3 clause 7 (state your
prediction in advance), not 13 (do not tune a constant against the answer): a
set equality has no sensitivity to slide, and changing a member asserts a
different proposition rather than a weaker one.

POSITIVE-CONTROLLED FOUR WAYS (12.3), because a gate you have only ever seen
pass is not a gate you have tested: an INLINE threshold injection must turn it
RED, a NAMED threshold injection must turn it RED, an AXIS comparison must turn
it RED, and the unmodified source must be asserted GREEN in the same test.  The
name-resolution clause is additionally VACUITY-GATED against itself: with the
resolver blinded, the named injection must scan CLEAN -- proving the clause is
load-bearing rather than decorative (13.2).
"""
from __future__ import annotations
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "gapverify_measure.py"

AXES = ("S_GRID", "K_GRID", "T_GRID")


# --------------------------------------------------------------------------- #
#  the walker
# --------------------------------------------------------------------------- #
def _module() -> ast.Module:
    return ast.parse(RUNNER.read_text())


def _module_consts(mod: ast.Module, *, resolve_names: bool = True) -> dict[str, float]:
    """Every module-level NAME bound to a numeric literal.

    `resolve_names=False` BLINDS the resolver, and exists so the clause can be
    vacuity-gated against itself (13.2)."""
    if not resolve_names:
        return {}
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
    """Recursive descent that PRUNES a Subscript's index.  `ast.walk` cannot
    prune -- it is a flat queue over every descendant."""
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


def scan(source: str, *, resolve_names: bool = True) -> list[str]:
    """Every 13 violation in the verdict functions of `source`."""
    mod = ast.parse(source)
    consts = _module_consts(mod, resolve_names=resolve_names)
    defs = _verdict_defs(mod)
    bad: list[str] = []
    for name, fn in defs.items():
        for node in _descend(fn):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left, *node.comparators]
            for op, right in zip(node.ops, node.comparators):
                if not isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                    continue
                for side in (node.left, right):
                    v = _as_number(side, consts)
                    if v is not None and v != 0.0:
                        bad.append(f"ordering-threshold:{name}:{v}")
            for side in operands:
                for sub in _descend(side):
                    if isinstance(sub, ast.Name) and sub.id in AXES:
                        bad.append(f"axis-compared:{name}:{sub.id}")
    return bad


# the injection site: a one-line verdict whose replacement is unambiguous.
_SITE = "    return len(violations) == 0"


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
    """POSITIVE CONTROL 1 (12.3)."""
    src = RUNNER.read_text().replace(_SITE, "    return len(violations) < 3")
    assert "len(violations) < 3" in src, "injection did not land"
    found = scan(src)
    assert any(f.startswith("ordering-threshold:v_a0_coord") for f in found), found


def test_the_gate_bites_on_a_NAMED_threshold():
    """POSITIVE CONTROL 2 (12.3): **A NAME BOUND TO A LITERAL IS A LITERAL.**
    Closing a threshold BY NAMING IT went GREEN on the walker rung."""
    src = RUNNER.read_text().replace(
        "DOT = 4              #", "CHECK_TOL = 3\nDOT = 4              #"
    ).replace(_SITE, "    return len(violations) < CHECK_TOL")
    assert "CHECK_TOL = 3" in src and "< CHECK_TOL" in src, "injection did not land"
    found = scan(src)
    assert any(f.startswith("ordering-threshold:v_a0_coord") for f in found), (
        "THE NAMED-THRESHOLD HOLE IS OPEN: the gate did not resolve a "
        f"module-level name binding to its literal. found={found}")


def test_the_name_resolution_clause_is_LOAD_BEARING_not_decorative():
    """13.2 pointed at the gate itself: with the resolver BLINDED the named
    injection must scan CLEAN.  If it were still caught, the clause would be
    decorative and the previous test would prove nothing."""
    src = RUNNER.read_text().replace(
        "DOT = 4              #", "CHECK_TOL = 3\nDOT = 4              #"
    ).replace(_SITE, "    return len(violations) < CHECK_TOL")
    assert scan(src, resolve_names=False) == [], (
        "the blinded scan still fired -- this test is not measuring what it "
        "claims to measure")


def test_the_gate_bites_on_an_axis_compared_against():
    """POSITIVE CONTROL 3: a swept axis is an INDEPENDENT VARIABLE."""
    src = RUNNER.read_text().replace(
        _SITE, "    return len(violations) > max(K_GRID)")
    found = scan(src)
    assert any(f.startswith("axis-compared:v_a0_coord") for f in found), found


def test_subscript_indices_are_PRUNED_not_counted():
    """A negative index in a subscript is addressing, not a threshold."""
    src = "VERDICTS = (\"v_x\",)\ndef v_x(h):\n    return h[-1] == 0\n"
    assert scan(src) == []


def test_a_named_literal_in_a_SUBSCRIPT_is_still_pruned():
    """The prune and the name-resolution must not fight."""
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


def test_the_registered_predictions_are_SET_EQUALITIES_not_orderings():
    """The cliff verdicts compare against predictions registered in advance.
    This asserts they are compared by EQUALITY -- a set equality has no
    sensitivity to slide -- and that the gate saw them (non-vacuity)."""
    mod = _module()
    defs = _verdict_defs(mod)
    for name in ("v_a3_cliff", "v_a3_disagreement"):
        fn = defs[name]
        cmps = [n for n in _descend(fn) if isinstance(n, ast.Compare)]
        assert cmps, f"{name} compares nothing"
        for c in cmps:
            assert all(isinstance(op, (ast.Eq, ast.NotEq)) for op in c.ops), (
                f"{name} decides by an ORDERING, not an equality")
