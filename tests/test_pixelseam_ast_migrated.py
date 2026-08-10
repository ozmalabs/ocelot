"""PROTOCOL 13 GATE for the pixel-seam rung (104000-104999).

A Python AST walk over `scripts/pixelseam_measure.py`, never a substring
selector (this arc's record on substring selectors is 0-5, and the fifth
happened INSIDE the test written to warn about substring selectors).

What it asserts, structurally:

  * the verdict functions are bound as `ast.FunctionDef` nodes BY NAME, read
    from the runner's OWN `VERDICTS` tuple -- the gate carries no copy, and a
    divergence between the two is itself a failure (NON-VACUITY);
  * **SUBSCRIPT INDICES ARE PRUNED** by an explicit recursive descent -- an
    index is ADDRESSING, not a threshold.  `ast.walk` CANNOT PRUNE, which is
    why this gate is not built on it;
  * **MODULE-LEVEL NAME BINDINGS ARE RESOLVED TO THEIR LITERALS** -- a name
    bound to a literal IS a literal;
  * **NO ORDERING COMPARISON AGAINST A NON-ZERO LITERAL** (inline or named).
    An ordering against a constant is a threshold because you can SLIDE it to
    adjust sensitivity; an equality is not tunable.  Orderings are admitted
    only between two MEASURED quantities, or against the sentinel `0`;
  * the swept axes (`Q_GRID`, `START_GRID`) are ITERATED, never compared
    against -- they are INDEPENDENT VARIABLES;
  * the dead-instrument arms ABORT (`return 2` engine divergence, `return 3`
    wiring control), never warn.

**WHAT THIS GATE DELIBERATELY DOES NOT FORBID, and the reason is declared in
the pre-registration:** `MIN_LIVE = 3` is a POWER floor -- how many live
observations a cell must carry before it is REPORTED at all.  It is applied
identically to every cell, it never touches an outcome, and it lives in
`main()`, not in any verdict.  The gate scans verdict functions; a power floor
that migrated INTO one would therefore be caught.

POSITIVE-CONTROLLED THREE WAYS (12.3), because a gate you have only ever seen
pass is not a gate you have tested.
"""
from __future__ import annotations
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "pixelseam_measure.py"

# The axes.  Named here, but their PRESENCE in the runner is asserted below, so
# a rename cannot silently empty this tuple's meaning.
AXES = ("Q_GRID", "START_GRID")

# The injection site: a verdict body line, quoted once.  Its presence in the
# unmodified runner is asserted before every injection (an injection that does
# not land turns the positive control into a tautology -- the supervisor's
# first verification of a gate of this shape landed on the wrong node).
SITE = "    return n_live_explained == 0"


def _module() -> ast.Module:
    return ast.parse(RUNNER.read_text())


def _as_number(node: ast.AST, consts: dict[str, float]) -> float | None:
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
    """Every module-level NAME bound to a numeric literal.  A gate that only
    inspects `ast.Constant` at the comparison site is blind to `TOL = 2` /
    `x < TOL`, and that blindness went GREEN on the walker rung."""
    out: dict[str, float] = {}
    for node in mod.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            v = _as_number(node.value, {})
            if v is not None:
                out[node.targets[0].id] = v
    return out


def _descend(node: ast.AST):
    """Recursive descent that PRUNES a Subscript's index.  `ast.walk` is a flat
    queue over every descendant and cannot prune a subtree."""
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


def test_the_declared_axes_exist_in_the_runner():
    """A gate whose axis tuple has gone stale forbids nothing.  Assert the
    names it protects are actually bound at module level."""
    mod = _module()
    bound = {n.targets[0].id for n in mod.body
             if isinstance(n, ast.Assign) and len(n.targets) == 1
             and isinstance(n.targets[0], ast.Name)}
    assert set(AXES) <= bound, f"axis names not bound in runner: {set(AXES) - bound}"


def test_no_threshold_enters_any_verdict():
    """The headline 13 assertion on the UNMODIFIED source."""
    assert scan(RUNNER.read_text()) == []


def test_the_gate_bites_on_an_INLINE_threshold():
    """POSITIVE CONTROL 1 (12.3)."""
    src = RUNNER.read_text()
    assert SITE in src, "injection site missing -- the control is vacuous"
    poisoned = src.replace(SITE, "    return n_live_explained < 2400")
    assert "n_live_explained < 2400" in poisoned
    found = scan(poisoned)
    assert any(f.startswith("ordering-threshold:v_p4_live") for f in found), found


def test_the_gate_bites_on_a_NAMED_threshold():
    """POSITIVE CONTROL 2 (12.3): **A NAME BOUND TO A LITERAL IS A LITERAL.**
    Closing a threshold by NAMING it went GREEN on the walker rung."""
    src = RUNNER.read_text()
    assert SITE in src and "DOT = 4" in src, "injection sites missing"
    poisoned = (src.replace("DOT = 4", "CHECK_TOL = 2400\nDOT = 4")
                   .replace(SITE, "    return n_live_explained < CHECK_TOL"))
    assert "CHECK_TOL = 2400" in poisoned and "< CHECK_TOL" in poisoned
    found = scan(poisoned)
    assert any(f.startswith("ordering-threshold:v_p4_live") for f in found), (
        "THE NAMED-THRESHOLD HOLE IS OPEN: the gate did not resolve a "
        f"module-level name binding to its literal. found={found}")


def test_the_NAMED_clause_is_LOAD_BEARING_not_decorative():
    """VACUITY GATE ON THE CLAUSE ITSELF (13.2): with the name resolver
    BLINDED, the named injection must scan to `[]` -- i.e. the resolution is
    what catches it, not something else that would have caught it anyway."""
    src = RUNNER.read_text()
    poisoned = (src.replace("DOT = 4", "CHECK_TOL = 2400\nDOT = 4")
                   .replace(SITE, "    return n_live_explained < CHECK_TOL"))
    mod = ast.parse(poisoned)
    defs = _verdict_defs(mod)
    blind: list[str] = []
    for name, fn in defs.items():
        for node in _descend(fn):
            if not isinstance(node, ast.Compare):
                continue
            for op, right in zip(node.ops, node.comparators):
                if not isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                    continue
                for side in (node.left, right):
                    v = _as_number(side, {})        # <- resolver BLINDED
                    if v is not None and v != 0.0:
                        blind.append(name)
    assert blind == [], (
        "the named-threshold clause is DECORATIVE -- the blinded scan caught "
        f"it anyway: {blind}")


def test_the_gate_bites_on_an_axis_compared_against():
    """POSITIVE CONTROL 3: a swept axis is an INDEPENDENT VARIABLE."""
    src = RUNNER.read_text()
    assert SITE in src
    poisoned = src.replace(SITE, "    return n_live_explained > max(Q_GRID)")
    found = scan(poisoned)
    assert any(f.startswith("axis-compared:v_p4_live") for f in found), found


def test_subscript_indices_are_PRUNED_not_counted():
    """An index is ADDRESSING, not a threshold."""
    src = "VERDICTS = (\"v_x\",)\ndef v_x(h):\n    return h[-1] == 0\n"
    assert scan(src) == []


def test_a_named_literal_in_a_SUBSCRIPT_is_still_pruned():
    """The prune and the name-resolution must not fight."""
    src = ("IDX = 1\nVERDICTS = (\"v_x\",)\n"
           "def v_x(h):\n    return h[IDX] == 0\n")
    assert scan(src) == []


def test_the_dead_instrument_arms_ABORT_rather_than_warn():
    """A rung that measures through a failed wiring control publishes a perfect
    fake null."""
    src = RUNNER.read_text()
    assert "return 2" in src and "ABORT: engine divergence" in src
    assert "return 3" in src and "ABORT: wiring control failed" in src


def test_the_requirement_diagnosis_RETURNS_EACH_LABEL_ON_A_CONSTRUCTED_BREAK():
    """POSITIVE-CONTROL THE INSTRUMENT, NOT ONLY THE HYPOTHESIS (§1 clause 4).

    A diagnosis that returned one label for everything would be a LOOKUP, and
    every "which requirement failed" row in the results would be decoration.
    Each case below breaks EXACTLY ONE requirement by construction, so a label
    that never fires is a dead branch and this test says so."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_ps", RUNNER)
    ps = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ps)

    ok = [[["px", 0, 0, 7], ["px", 0, 1, 7]],
          [["px", 0, 4, 7], ["px", 0, 5, 7]],
          [["px", 0, 8, 7], ["px", 0, 9, 7]]]
    cases = {
        "ok": ok,
        "R3": [[], ok[1], ok[2]],
        "R4": [ok[0], ok[1] + [["px", 5, 5, 7]], ok[2]],
        "R5": [ok[0], [["px", 0, 4, 7], ["px", 0, 9, 7]], ok[2]],
        "R6": [ok[0], [["px", 0, 4, 8], ["px", 0, 5, 7]], ok[2]],
        "R7": [ok[0], ok[0], ok[0]],
        "R1": [ok[0]],
    }
    got = {want: ps.diagnose(frames) for want, frames in cases.items()}
    assert got == {k: k for k in cases}, got
    # and it must catch a break in a LATER pair, not only the first
    assert ps.diagnose([ok[0], ok[1],
                        [["px", 0, 9, 7], ["px", 0, 10, 7]]]) == "R5"


def test_the_requirement_diagnosis_is_NOT_computed_by_the_Term():
    """INSTRUMENT DISCIPLINE: a diagnostic must not be computed by the
    component it checks.  `diagnose` must reach no substrate and no Term."""
    mod = _module()
    fn = next(n for n in mod.body
              if isinstance(n, ast.FunctionDef) and n.name == "diagnose")
    called = {n.func.id for n in ast.walk(fn)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    attrs = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
    assert "Term" not in called and "Lit" not in called, called
    assert "evaluate" not in attrs and "run_rules" not in attrs, attrs
