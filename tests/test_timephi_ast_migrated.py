"""PROTOCOL §13 GATE for the TIME-PHI rung (`VISION_TIMEPHI_PREREG.md`).

No magic number enters this rung's verdicts. Asserted STRUCTURALLY, by a Python
AST walk that locates the verdict functions **BY SHAPE** — resolving them as
`ast.FunctionDef` nodes whose `name` is in the runner's own `VERDICTS` tuple —
**never by substring**. Four substring selectors have failed in this arc, and the
phi rung's own first gate counted ARRAY INDICES as thresholds.

Two defects of the phi rung's gate are fixed here by construction:

  * **`ast.walk` CANNOT PRUNE.** Its first fix was also wrong for this reason.
    This gate uses an explicit recursive descent that can skip a subtree.
  * **A SUBSCRIPT INDEX IS ADDRESSING, NOT A THRESHOLD.** `v["offset"]`,
    `a3[N][S]`, `t.split(...)[1]` are pruned before any constant is counted.

A non-zero constant is admitted ONLY against a cardinality (`len(...)`). Every
other comparison in a verdict must be an EQUALITY (`==` / `!=` / `is`), because
an ordering comparison there would be partial credit, which the registration
forbids.

The gate is POSITIVE-CONTROLLED (§12.3) and NON-VACUOUS: it must bind every name
in `VERDICTS`, so a rename cannot make it pass by scanning nothing.
"""
import ast
import pathlib

import pytest

RUNNER = (pathlib.Path(__file__).resolve().parents[1]
          / "scripts" / "timephi_measure.py")

# The declared §13 residuals — stimulus CONFIGURATION, inherited from the phi
# rung. The claim asserted about them is the weaker, honest one: they are bound
# exactly once and never appear inside a verdict comparison.
RESIDUALS = ("DOT", "FIELD_H", "FIELD_W", "RAW_N", "BG", "FG", "ROW")
# The swept axes — INDEPENDENT VARIABLES. They must be iterated, never compared.
AXES = ("S_GRID", "K_GRID", "P_GRID", "ISI_S", "NOISE_LO", "NOISE_HI")

EQUALITY = (ast.Eq, ast.NotEq, ast.Is, ast.IsNot, ast.In, ast.NotIn)


def _src() -> str:
    return RUNNER.read_text()


def _tree(src: str) -> ast.Module:
    return ast.parse(src)


def _verdict_names(tree: ast.Module) -> tuple[str, ...]:
    """Read the runner's OWN declared verdict tuple. The gate does not carry its
    own copy — a divergence between the two is itself a failure."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "VERDICTS":
                    return tuple(e.value for e in node.value.elts)
    raise AssertionError("runner declares no VERDICTS tuple")


def _verdict_defs(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    names = _verdict_names(tree)
    found = {n.name: n for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef) and n.name in names}
    missing = set(names) - set(found)
    assert not missing, f"declared verdicts with no FunctionDef: {sorted(missing)}"
    return found


def _walk_pruned(node: ast.AST):
    """Recursive descent that PRUNES subscript indices — an index is addressing,
    not a threshold. `ast.walk` cannot do this; that is why it is not used."""
    yield node
    for field, value in ast.iter_fields(node):
        if isinstance(node, ast.Subscript) and field == "slice":
            continue                      # PRUNED: v["offset"], a3[N][S], x[1]
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, ast.AST):
                yield from _walk_pruned(item)


def _is_cardinality(node: ast.AST) -> bool:
    """`len(...)` — a count, against which a non-zero constant is legitimate."""
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "len")


def _int_of(node: ast.AST):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _int_of(node.operand)
        return None if inner is None else -inner
    return None


# --------------------------------------------------------------------------- #
def test_gate_binds_every_declared_verdict_by_name_NON_VACUITY():
    """A gate that scans nothing passes trivially. It must bind ALL of them."""
    defs = _verdict_defs(_tree(_src()))
    assert len(defs) == len(_verdict_names(_tree(_src()))) >= 13
    for name, fn in defs.items():
        assert isinstance(fn, ast.FunctionDef)
        assert fn.body, f"{name} has an empty body"


def test_no_nonzero_constant_is_compared_against_a_measured_quantity():
    """§13: the only non-zero constants a verdict may compare against are
    CARDINALITIES. Everything else must be 0 (a sign/emptiness test) or a
    structural literal on the OTHER side of an equality."""
    offenders = []
    for name, fn in _verdict_defs(_tree(_src())).items():
        for node in _walk_pruned(fn):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left] + list(node.comparators)
            for op, side in zip(node.ops, node.comparators):
                for a, b in ((node.left, side), (side, node.left)):
                    c = _int_of(b)
                    if c is None or c == 0:
                        continue
                    if _is_cardinality(a):
                        continue          # admitted: a count
                    if isinstance(op, EQUALITY):
                        continue          # admitted: an exact-equality verdict
                    offenders.append((name, ast.dump(node)[:140]))
            del operands
    assert not offenders, f"non-zero constant vs a measured quantity: {offenders}"


def test_verdicts_decide_by_equality_not_by_ordering():
    """An ordering comparison inside a verdict is PARTIAL CREDIT, which the
    pre-registration forbids. The only admitted orderings are against a
    cardinality or against the SENTINEL 0 (`diverged_at >= 0` — a sign test on
    an integer sentinel, not a tuned threshold)."""
    offenders = []
    for name, fn in _verdict_defs(_tree(_src())).items():
        for node in _walk_pruned(fn):
            if not isinstance(node, ast.Compare):
                continue
            for op, right in zip(node.ops, node.comparators):
                if isinstance(op, EQUALITY):
                    continue
                if _is_cardinality(node.left) or _is_cardinality(right):
                    continue
                if _int_of(right) == 0:
                    continue              # sign test against a sentinel
                # `gap <= confirm` compares two MEASURED quantities to each
                # other — no constant is involved, so no number entered.
                if isinstance(node.left, ast.Call) and isinstance(right, ast.Call):
                    continue
                offenders.append((name, ast.dump(node)[:140]))
    assert not offenders, f"ordering comparison in a verdict: {offenders}"


def test_declared_residuals_are_bound_once_and_never_in_a_verdict_comparison():
    """The §13 residuals are CONFIGURATION. The claim is deliberately weaker
    than 'they fell out': each is bound exactly once, and none is ever compared
    against inside a verdict."""
    tree = _tree(_src())
    for r in RESIDUALS:
        binds = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                 for t in n.targets
                 if isinstance(t, ast.Name) and t.id == r]
        assert len(binds) == 1, f"{r} bound {len(binds)} times, expected 1"
    for name, fn in _verdict_defs(tree).items():
        for node in _walk_pruned(fn):
            if not isinstance(node, ast.Compare):
                continue
            for side in [node.left] + list(node.comparators):
                for sub in _walk_pruned(side):
                    if isinstance(sub, ast.Name) and sub.id in RESIDUALS:
                        # DOT appears only as `2 * DOT * DOT` — the dot's own
                        # cell count, a CARDINALITY derived from the stimulus,
                        # on the constant side of an EQUALITY.
                        assert sub.id == "DOT" and any(
                            isinstance(o, ast.Eq) for o in node.ops), (
                            f"{name}: residual {sub.id} inside a verdict "
                            f"comparison")


def test_swept_axes_are_iterated_never_compared_against():
    """An independent variable that gets COMPARED against has stopped being an
    axis and become a threshold."""
    offenders = []
    for name, fn in _verdict_defs(_tree(_src())).items():
        for node in _walk_pruned(fn):
            if not isinstance(node, ast.Compare):
                continue
            for side in [node.left] + list(node.comparators):
                for sub in _walk_pruned(side):
                    if isinstance(sub, ast.Name) and sub.id in AXES:
                        offenders.append((name, sub.id))
    assert not offenders, f"a swept axis used as a threshold: {offenders}"


def test_the_dead_instrument_arms_ABORT_rather_than_warn():
    """§1 clause 4 / §10.2: a failed wiring control or a diverged engine must
    STOP the run, not print and continue."""
    src = _src()
    assert 'print(f"ABORT: engine divergence' in src
    assert "return 2" in src
    assert 'R["ABORT"] = "A0 wiring control failed"' in src
    assert "return 3" in src


# ------------------------- THE POSITIVE CONTROL ---------------------------- #
# §12.3: a gate you have only ever seen PASS is not a gate you have tested.
def _run_checks_on(src: str) -> list[str]:
    """Re-run the two constant-sensitive walks against arbitrary source."""
    tree = _tree(src)
    failures = []
    for name, fn in _verdict_defs(tree).items():
        for node in _walk_pruned(fn):
            if not isinstance(node, ast.Compare):
                continue
            for op, right in zip(node.ops, node.comparators):
                c = _int_of(right)
                if c is not None and c != 0 and not isinstance(op, EQUALITY) \
                        and not _is_cardinality(node.left):
                    failures.append(f"const:{name}")
                if not isinstance(op, EQUALITY) and _int_of(right) != 0 \
                        and not _is_cardinality(node.left) \
                        and not _is_cardinality(right) \
                        and not (isinstance(node.left, ast.Call)
                                 and isinstance(right, ast.Call)):
                    failures.append(f"ordering:{name}")
    return failures


def test_gate_is_GREEN_on_the_unmodified_runner():
    assert _run_checks_on(_src()) == []


@pytest.mark.parametrize("injection,anchor", [
    # a tolerance band smuggled into the aperture verdict
    ('    return all(abs(a3[N][S]["offset"][1] - S) < 2.5\n'
     '               for N in a3 for S in S_GRID)\n',
     "def v_a3_p2(a3) -> bool:"),
    # a partial-credit ordering on the correction magnitude
    ('    return all(int(v["correction"]) > 12\n'
     '               for t, v in a6.items() if "-P1-" in t)\n',
     "def v_a6a_p5(a6) -> bool:"),
])
def test_gate_goes_RED_when_a_real_threshold_is_injected(injection, anchor):
    """Inject a genuine threshold into a verdict; the walker MUST flag it.
    This is what proves the gate discriminates rather than permits."""
    src = _src()
    i = src.index(anchor)
    j = src.index("\n\n\n", i)
    doc_end = src.index('"""', src.index('"""', i) + 3) + 3
    poisoned = src[:doc_end] + "\n" + injection + src[j:]
    assert _run_checks_on(poisoned), (
        "the gate did not fire on an injected threshold — it is permissive")
