"""PROTOCOL §13 GATE for the appearance-partition rung (109000-109999).

A Python AST walk over `scripts/appearance_measure.py`, never a substring
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
  * **NO ORDERING COMPARISON AGAINST A NON-ZERO LITERAL** (inline or named),
    because an ordering against a constant is a threshold: you can SLIDE it to
    adjust sensitivity.  An equality is not tunable.  Orderings are admitted
    only between two MEASURED quantities, or against the sentinel `0`;
  * the swept axes (`Q_GRID`, `START_GRID`, `N_GRID`, `COL_GRID`) are
    ITERATED, never compared against;
  * the dead-instrument arms ABORT, never warn.

AND TWO CLAUSES THIS RUNG NEEDS THAT ITS PREDECESSORS DID NOT:

  * **`P_tol` MUST NOT READ ITS OWN `appearance_residual`.**  The whole claim
    of this rung is that appearance is PARTITIONED OUT of the verdict rather
    than compared against a loosened threshold.  If any branch of `p_tol`
    tested the residual, the "partition" would be a tolerance with the number
    hidden in a variable name.  Asserted structurally: the residual
    accumulator appears in no `ast.Compare` and no `ast.If` test inside
    `p_tol`.
  * **`p_tol` REACHES NO SUBSTRATE AND NO TERM** -- a diagnostic must not be
    computed by the component it checks.

POSITIVE-CONTROLLED FOUR WAYS (§12.3), with the injection site asserted
present before every injection: a gate you have only ever seen pass is not a
gate you have tested, and an injection that does not land turns a positive
control into a tautology.
"""
from __future__ import annotations
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "appearance_measure.py"

AXES = ("Q_GRID", "START_GRID", "N_GRID", "COL_GRID")

# The injection site: a verdict body line, quoted once.
SITE = "    return _fa_silent(R) == 0"


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
    """Read from the runner's OWN tuple.  Its elements are NAMES (function
    references), so a renamed verdict cannot silently drop out of the scan."""
    for node in mod.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == "VERDICTS":
            return [e.id for e in node.value.elts if isinstance(e, ast.Name)]
    raise AssertionError("the runner declares no VERDICTS tuple")


def _verdict_defs(mod: ast.Module) -> dict[str, ast.FunctionDef]:
    names = set(_verdict_names(mod))
    return {n.name: n for n in mod.body
            if isinstance(n, ast.FunctionDef) and n.name in names}


def scan(source: str) -> list[str]:
    """Every §13 violation in the verdict functions of `source`."""
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
    """NON-VACUITY: the gate scans the functions the RUNNER names."""
    mod = _module()
    names = _verdict_names(mod)
    defs = _verdict_defs(mod)
    assert names, "VERDICTS is empty -- the gate would scan nothing"
    missing = sorted(set(names) - set(defs))
    assert not missing, f"declared but not defined: {missing}"


def test_the_declared_axes_exist_in_the_runner():
    mod = _module()
    bound = {n.targets[0].id for n in mod.body
             if isinstance(n, ast.Assign) and len(n.targets) == 1
             and isinstance(n.targets[0], ast.Name)}
    assert set(AXES) <= bound, f"axis names not bound in runner: {set(AXES) - bound}"


def test_no_threshold_enters_any_verdict():
    """The headline §13 assertion on the UNMODIFIED source."""
    assert scan(RUNNER.read_text()) == []


def test_the_gate_bites_on_an_INLINE_threshold():
    """POSITIVE CONTROL 1 (§12.3)."""
    src = RUNNER.read_text()
    assert SITE in src, "injection site missing -- the control is vacuous"
    poisoned = src.replace(SITE, "    return _fa_silent(R) < 2400")
    assert "_fa_silent(R) < 2400" in poisoned
    found = scan(poisoned)
    assert any(f.startswith("ordering-threshold:v_c1_partition") for f in found), found


def test_the_gate_bites_on_a_NAMED_threshold():
    """POSITIVE CONTROL 2: **A NAME BOUND TO A LITERAL IS A LITERAL.**"""
    src = RUNNER.read_text()
    assert SITE in src and "DOT = 4" in src, "injection sites missing"
    poisoned = (src.replace("DOT = 4", "CHECK_TOL = 2400\nDOT = 4")
                   .replace(SITE, "    return _fa_silent(R) < CHECK_TOL"))
    assert "CHECK_TOL = 2400" in poisoned and "< CHECK_TOL" in poisoned
    found = scan(poisoned)
    assert any(f.startswith("ordering-threshold:v_c1_partition") for f in found), (
        "THE NAMED-THRESHOLD HOLE IS OPEN: the gate did not resolve a "
        f"module-level name binding to its literal. found={found}")


def test_the_NAMED_clause_is_LOAD_BEARING_not_decorative():
    """VACUITY GATE ON THE CLAUSE ITSELF (§13.2): with the name resolver
    BLINDED, the named injection must scan to `[]`."""
    src = RUNNER.read_text()
    poisoned = (src.replace("DOT = 4", "CHECK_TOL = 2400\nDOT = 4")
                   .replace(SITE, "    return _fa_silent(R) < CHECK_TOL"))
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
    poisoned = src.replace(SITE, "    return _fa_silent(R) > max(Q_GRID)")
    found = scan(poisoned)
    assert any(f.startswith("axis-compared:v_c1_partition") for f in found), found


def test_subscript_indices_are_PRUNED_not_counted():
    src = "def v_x(h):\n    return h[-1] == 0\nVERDICTS = (v_x,)\n"
    assert scan(src) == []


def test_a_named_literal_in_a_SUBSCRIPT_is_still_pruned():
    src = ("IDX = 1\ndef v_x(h):\n    return h[IDX] == 0\nVERDICTS = (v_x,)\n")
    assert scan(src) == []


def test_the_dead_instrument_arms_ABORT_rather_than_warn():
    """A rung that measures through a failed wiring control publishes a perfect
    fake null."""
    src = RUNNER.read_text()
    assert "return 2" in src and "ABORT: engine divergence" in src
    assert "return 3" in src and "ABORT: wiring control failed" in src


# --------------------------------------------------------------------------- #
#  THE TWO CLAUSES THIS RUNG NEEDS THAT ITS PREDECESSORS DID NOT
# --------------------------------------------------------------------------- #
def _fn(name: str) -> ast.FunctionDef:
    return next(n for n in _module().body
                if isinstance(n, ast.FunctionDef) and n.name == name)


def test_the_predicate_NEVER_READS_its_own_appearance_residual():
    """**THE PARTITION IS NOT A TOLERANCE, ASSERTED STRUCTURALLY.**

    A "tolerant" operator that compared its appearance residual against
    anything would be a LOOSENED THRESHOLD with the number hidden in a
    variable name -- precisely the move that turns a refuser into a selector,
    and precisely what §13 forbids.  The residual accumulator must appear in
    NO comparison and NO branch test inside `p_tol`: it is COUNTED and
    RETURNED, never READ."""
    fn = _fn("p_tol")
    bad: list[str] = []
    for node in _descend(fn):
        if isinstance(node, ast.Compare):
            for side in [node.left, *node.comparators]:
                for sub in _descend(side):
                    if isinstance(sub, ast.Name) and sub.id == "resid":
                        bad.append(f"residual-compared:{ast.dump(node)[:60]}")
        if isinstance(node, ast.If):
            for sub in _descend(node.test):
                if isinstance(sub, ast.Name) and sub.id == "resid":
                    bad.append("residual-branched")
    assert bad == [], bad
    # NON-VACUITY: the accumulator must actually be present, or the scan above
    # is protecting a name that does not exist.
    names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    assert "resid" in names, "the residual accumulator is not named `resid`"


def test_the_residual_clause_is_LOAD_BEARING_not_decorative():
    """VACUITY GATE ON THE CLAUSE ABOVE (§13.2): a `p_tol` that DID read its
    residual must be caught by it."""
    src = RUNNER.read_text()
    site = "    if all(o == 0 for o in off):"
    assert site in src, "injection site missing -- the control is vacuous"
    poisoned = src.replace(site, "    if resid > 3:\n        return False, None, resid, 'TOL'\n" + site)
    mod = ast.parse(poisoned)
    fn = next(n for n in mod.body
              if isinstance(n, ast.FunctionDef) and n.name == "p_tol")
    caught = False
    for node in _descend(fn):
        if isinstance(node, ast.Compare):
            for side in [node.left, *node.comparators]:
                for sub in _descend(side):
                    if isinstance(sub, ast.Name) and sub.id == "resid":
                        caught = True
    assert caught, "the residual clause is DECORATIVE -- it missed a real read"


def test_the_predicate_is_NOT_computed_by_the_Term():
    """INSTRUMENT DISCIPLINE: a diagnostic must not be computed by the
    component it checks.  `p_tol` must reach no substrate and no Term."""
    fn = _fn("p_tol")
    called = {n.func.id for n in ast.walk(fn)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    attrs = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
    assert "Term" not in called and "Lit" not in called, called
    assert "evaluate" not in attrs and "run_rules" not in attrs, attrs


def test_the_analytic_expectation_is_ENUMERATED_not_quoted():
    """C2's ceiling must be COMPUTED IN THE RUNNER, before the arm is read --
    the GapAbduce template.  A remembered approximation is a magic number."""
    fn = _fn("analytic_rect")
    # it must actually loop over the position axis, not return a constant
    loops = [n for n in ast.walk(fn) if isinstance(n, ast.For)]
    assert len(loops) >= 2, "analytic_rect does not enumerate"
    names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    assert "COL_GRID" in names, "the enumeration does not read the position axis"
    consts = [n.value for n in ast.walk(fn)
              if isinstance(n, ast.Constant) and isinstance(n.value, float)]
    assert consts == [], f"a float literal in the analytic expectation: {consts}"
