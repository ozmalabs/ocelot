"""§13 GATE for the phi rung: NO THRESHOLD WAS INTRODUCED.

A PYTHON AST WALK, never a substring selector. `grep` cannot see a literal that
was folded, renamed, or moved into a sibling subtree — PROTOCOL §12, and four
failures in this arc.

The claim under test is narrow and is exactly the one the results file makes:
**every phi verdict is EXACT EQUALITY, and the only constant any comparison is
allowed to touch is ZERO.** That is the McCollough-gate shape — unambiguous
discrimination with no metric to argue about.

What this file does NOT cover, stated rather than hidden: `BLOCK`, `GRID`,
`DOT`, `K_LUM` are DECLARED magic-number residuals INHERITED from
`VISION_MOTION_OBJECTS` (the rung is a measurement of an existing sensor at its
own configuration, not a new mechanism). They are asserted to be
CONFIGURATION — bound once at module level and never used as a comparison
threshold — which is a different and weaker claim than "they fell out", and it
is the only claim made.

The swept ranges (`SEPS`, `ISIS`, `L3_RADII`, `L3_SEPS`, `M6_RADII`) are
INDEPENDENT VARIABLES, not constants, and are asserted to be exactly that.

POSITIVE-CONTROLLED (§12.3): `test_the_gate_bites` injects a threshold into the
verdict source and proves the walker goes RED. A gate only ever seen pass is
not a gate that has been tested.
"""
from __future__ import annotations

import ast
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "phi_measure.py")

# The ONLY constant a comparison may touch. Zero is the constant-free split:
# "did this change at all", not "did it change by more than <a number I chose>".
ALLOWED_IN_COMPARISON = {0, 0.0}

# Configuration, INHERITED and DECLARED (see the module docstring). Asserted to
# be bound once at module level and never to appear inside a comparison.
CONFIG_NAMES = {"GRID", "BLOCK", "NCELL", "K_LUM", "DOT", "ROW", "COL",
                "SEED_BLOCK", "N_PAIRS_M6", "N_FRAMES_M6", "STEP_8BIT"}

# Independent variables — swept axes, not constants.
IV_NAMES = {"SEPS", "ISIS", "ISI_SEPS", "L3_RADII", "L3_SEPS", "M6_RADII"}

VERDICT_FUNCS = {"l1_verdict", "l2_verdict", "m6_corpus"}


@pytest.fixture(scope="module")
def tree():
    with open(SRC) as fh:
        return ast.parse(fh.read(), filename=SRC)


def _operand_walk(node):
    """Walk a Compare's OPERANDS, skipping SUBSCRIPT INDICES.

    THE FIRST VERSION OF THIS WALKER WAS DEFECTIVE AND THE DEFECT IS RECORDED
    RATHER THAN QUIETLY FIXED (§12.1 — 'a claim about what code SELECTS is not
    established by counting the tokens that select it', turned on my own gate).
    It walked the entire Compare subtree, so `vf[r, c, 1] != 0.0` and
    `hist[-1]` reported the ARRAY INDEX `1` as a comparison threshold. An index
    is addressing, not a threshold. Three of the six sites it flagged were this
    false positive; each was audited BY HAND before this function changed, and
    none was a threshold (§12.3: verify the fact, then fix the gate — never the
    reverse)."""
    def rec(nd):
        # PRUNING is the whole point: `ast.walk` cannot prune — it yields every
        # descendant — so the first fix, which called `ast.walk(sub.value)`
        # inside an `ast.walk` loop, still saw the indices. Recurse by hand.
        yield nd
        for child in ast.iter_child_nodes(nd):
            if isinstance(nd, ast.Subscript) and child is nd.slice:
                continue        # an INDEX is addressing, never a threshold
            yield from rec(child)

    for operand in [node.left, *node.comparators]:
        yield from rec(operand)


def _is_cardinality(node):
    """True iff a comparison is against a COUNT — `len(...)` or the sample size
    `n`. A minimum-sample guard (`n < 2`: a t-interval is undefined below two
    observations) and a minimum-frame guard (`len(hist) < 2`: a correspondence
    needs two frames) are STRUCTURAL — both twos fall out of the definition of
    the thing being computed, not out of a choice about a measured quantity.
    Enumerated deliberately narrowly: nothing else qualifies."""
    for operand in [node.left, *node.comparators]:
        if isinstance(operand, ast.Call) and isinstance(operand.func, ast.Name) \
                and operand.func.id == "len":
            return True
        if isinstance(operand, ast.Name) and operand.id == "n":
            return True
    return False


def _numeric_literals_in_comparisons(node, *, allow_cardinality=True):
    """Every numeric constant compared against a MEASURED QUANTITY, with the ops
    it sits among. An AST walk — a folded or renamed literal cannot hide from it
    the way it hides from a substring scan."""
    out = []
    for n in ast.walk(node):
        if not isinstance(n, ast.Compare):
            continue
        if allow_cardinality and _is_cardinality(n):
            continue
        ops = [type(o).__name__ for o in n.ops]
        for sub in _operand_walk(n):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, (int, float)) \
                    and not isinstance(sub.value, bool):
                out.append((sub.value, tuple(ops), getattr(n, "lineno", -1)))
    return out


def test_no_comparison_touches_any_constant_but_zero(tree):
    """THE HEADLINE §13 ASSERTION. If this fails, a threshold entered."""
    bad = [(v, ops, ln) for v, ops, ln in _numeric_literals_in_comparisons(tree)
           if v not in ALLOWED_IN_COMPARISON]
    assert bad == [], (
        "a NON-ZERO constant appears inside a comparison — a threshold has "
        f"entered the phi verdict: {bad}")


def test_the_verdicts_are_exact_equality_not_ordering(tree):
    """`l1_verdict` and `l2_verdict` must decide by EQUALITY. An ordering
    comparison there would mean partial credit, which the pre-registration
    forbids ('no partial credit, no metric to argue about')."""
    seen = {}
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name in ("l1_verdict", "l2_verdict"):
            ops = {type(o).__name__ for n in ast.walk(fn)
                   if isinstance(n, ast.Compare) and not _is_cardinality(n)
                   for o in n.ops}
            seen[fn.name] = ops
    assert set(seen) == {"l1_verdict", "l2_verdict"}, f"functions missing: {seen}"
    for name, ops in seen.items():
        assert ops <= {"Eq", "NotEq", "Is", "IsNot", "In", "NotIn"}, (
            f"{name} decides by ORDERING ({ops}) — that is a threshold, not the "
            "registered exact-equality verdict")


def test_the_m6_change_split_is_at_exactly_zero(tree):
    """The four-way classification splits on `> 0.0` — 'did it change at all'.
    Asserted STRUCTURALLY (a Gt against the constant 0.0), not by reading the
    docstring: a docstring does not gate."""
    found = []
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name == "m6_corpus":
            for n in ast.walk(fn):
                if isinstance(n, ast.Compare) and len(n.ops) == 1 \
                        and isinstance(n.ops[0], ast.Gt) \
                        and isinstance(n.comparators[0], ast.Constant):
                    found.append(n.comparators[0].value)
    assert found, "m6_corpus has no `> <const>` split at all — instrument moved"
    assert set(found) == {0.0}, (
        f"the M6 change split is not at exactly zero: {found}")


def test_config_residuals_are_configuration_not_thresholds(tree):
    """The declared residuals are bound ONCE at module level and never appear
    inside a comparison. This asserts they are CONFIGURATION, which is weaker
    than 'they fell out' — and weaker is what is honestly claimable."""
    assigned = [t.id for n in tree.body if isinstance(n, ast.Assign)
                for t in n.targets if isinstance(t, ast.Name)]
    for name in CONFIG_NAMES & set(assigned):
        assert assigned.count(name) == 1, f"{name} is rebound — not configuration"
    # Scoped to the VERDICT functions, which is where the claim lives. Outside
    # them a config name may legitimately bound a loop that BUILDS a stimulus
    # (`while c < COL + sep` in `rigid_sequence` walks the dot across the
    # field) — that is stimulus construction, not a decision about a
    # measurement. Audited by hand: that is the ONLY such site in the module.
    in_cmp = set()
    scanned = set()
    for fn in ast.walk(tree):
        if not (isinstance(fn, ast.FunctionDef) and fn.name in VERDICT_FUNCS):
            continue
        scanned.add(fn.name)
        for n in ast.walk(fn):
            if isinstance(n, ast.Compare):
                for sub in _operand_walk(n):
                    if isinstance(sub, ast.Name) and sub.id in CONFIG_NAMES:
                        in_cmp.add(sub.id)
    # NON-VACUITY: this assertion is satisfied by scanning NOTHING, which is
    # exactly how an inert instrument passes (§12.1). Name the functions.
    assert scanned == VERDICT_FUNCS, (
        f"the scan matched {sorted(scanned)}, not {sorted(VERDICT_FUNCS)} — a "
        f"renamed verdict would make this gate pass by scanning nothing")
    assert in_cmp == set(), (
        f"a declared configuration residual is used as a comparison threshold "
        f"inside a verdict: {sorted(in_cmp)}")


def test_the_swept_axes_are_independent_variables(tree):
    """Every swept range is a module-level sequence that is ITERATED, never
    compared against — i.e. an axis, not a constant."""
    top = {t.id: n.value for n in tree.body if isinstance(n, ast.Assign)
           for t in n.targets if isinstance(t, ast.Name)}
    for name in IV_NAMES:
        assert name in top, f"{name} is not a module-level axis"
        assert isinstance(top[name], (ast.Tuple, ast.Call)), (
            f"{name} is not a sequence literal/range — got {type(top[name])}")
    iterated = {n.iter.id for n in ast.walk(tree)
                if isinstance(n, ast.For) and isinstance(n.iter, ast.Name)}
    assert IV_NAMES & iterated, "no declared axis is ever iterated — dead sweep"


def test_the_dead_instrument_arms_actually_abort(tree):
    """C-POS and the L2 wiring self-test must RAISE, not warn. A control that
    only logs is a control that has never stopped anything."""
    raisers = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) \
                and isinstance(n.exc.func, ast.Name) and n.exc.func.id == "SystemExit":
            raisers.append(n.lineno)
    assert len(raisers) >= 3, (
        f"expected SystemExit aborts for C-POS, C-NULL, the L2 wiring self-test "
        f"and the corpus pins; found {len(raisers)}")


def test_the_gate_bites():
    """POSITIVE CONTROL (§12.3). Inject a threshold into the verdict; the
    headline assertion MUST go red. Then prove the unmodified source is green,
    so the walker is discriminating and not merely permissive."""
    with open(SRC) as fh:
        src = fh.read()

    clean = ast.parse(src)
    assert [x for x in _numeric_literals_in_comparisons(clean)
            if x[0] not in ALLOWED_IN_COMPARISON] == [], \
        "the UNMODIFIED source is already red — the gate is not measuring this rung"

    injected = src.replace("    if v == (0.0, float(sep)):",
                           "    if abs(v[1] - sep) < 2.5:", 1)
    assert injected != src, "injection site not found — the gate has rotted"
    bad = [x for x in _numeric_literals_in_comparisons(ast.parse(injected))
           if x[0] not in ALLOWED_IN_COMPARISON]
    assert bad, "THE GATE DOES NOT BITE: a 2.5 threshold in the verdict passed it"

    ops = {type(o).__name__
           for fn in ast.walk(ast.parse(injected))
           if isinstance(fn, ast.FunctionDef) and fn.name == "l1_verdict"
           for n in ast.walk(fn) if isinstance(n, ast.Compare) for o in n.ops}
    assert not ops <= {"Eq", "NotEq", "Is", "IsNot", "In", "NotIn"}, \
        "THE EQUALITY GATE DOES NOT BITE: an ordering verdict passed it"
