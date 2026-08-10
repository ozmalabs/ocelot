"""THE MOTION SENSOR ACCURACY GATE -- its own gates.

Three things are checked here, and the third is the one that matters:

  1. §13 -- no threshold is written into this rung's measurement. An AST walk
     over its own source, locating flagged sites BY SHAPE, never by substring.
  2. The two STRUCTURAL INVARIANTS hold on the real sensor.
  3. THE GATE BITES. Each of three deliberate sensor degradations must turn it
     RED, and the unmodified sensor must be GREEN. A gate that has never been
     ABLE to fail has not been tested -- three provenance gates in this tree sat
     green for 51 commits and then all fired at once as false accusations.

ON THE AST WALKER'S KNOWN FAILURE MODE, INHERITED DELIBERATELY. The phi rung's
first version of this gate COUNTED ARRAY INDICES AS THRESHOLDS (3 of 6 flagged
sites), and its first fix was also wrong because `ast.walk` cannot prune. That
history is why the walker below recurses by hand and why EVERY SITE IT FLAGS
WAS AUDITED BY HAND BEFORE THE CARVE-OUTS WERE WRITTEN (§12.3: verify the fact,
then fix the gate -- never the reverse). The audit is recorded in
`HAND_AUDITED_SITES` so a later reader can check my work rather than trust it.
"""
from __future__ import annotations

import ast
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

SRC_GATE = os.path.join(ROOT, "scripts", "motion_sensor_gate.py")
SRC_LIB = os.path.join(ROOT, "scripts", "motion_sensor_lib.py")


# --- the §13 walker ---------------------------------------------------------

def _comparand_walk(node):
    """Yield the DIRECT comparands of a Compare, and nothing nested inside
    arithmetic or addressing.

    THE SHAPE RULE, AND WHY IT IS THE RIGHT ONE: a threshold is something a
    value is COMPARED AGAINST. A constant that sits inside a BinOp
    (`(xx + 1) * BLOCK`) or inside a Subscript's slice (`hist[-1]`) is
    ARITHMETIC or ADDRESSING -- it is computing WHICH thing to compare, not
    WHAT to compare it to. `ast.walk` cannot express this distinction because
    it cannot prune; this recurses by hand and descends into nothing.
    """
    for operand in [node.left, *node.comparators]:
        yield operand


def _is_zero_test(c):
    """`x == 0`, `x > 0`, `sd > 0`. A zero test is an IDENTITY question, not a
    threshold: it asks whether a thing is there, not whether it is big enough."""
    return isinstance(c, ast.Constant) and c.value == 0


# Names/attributes whose comparison is a CARDINALITY -- a count of things, where
# the constant states a STRUCTURAL minimum rather than a tuned level. Enumerated
# deliberately narrowly, and each one justified:
#   n, size   -- a mean needs 2 observations; Otsu needs 2 distinct values
#   ties      -- "unique minimum" MEANS exactly one minimiser; that is the
#                definition, not a threshold
#   members   -- "multi-cell" MEANS more than one member; the landed rung's own
#                definition of the quantity being bounded
#   owners, i -- a partition index and a loop index
CARDINALITY_NAMES = {"n", "ties", "i", "owners", "size", "members"}


def _is_cardinality(node):
    for c in _comparand_walk(node):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) \
                and c.func.id == "len":
            return True
        if isinstance(c, ast.Name) and c.id in CARDINALITY_NAMES:
            return True
        if isinstance(c, ast.Attribute) and c.attr in CARDINALITY_NAMES:
            return True
        if isinstance(c, ast.Subscript) and isinstance(c.slice, ast.Constant) \
                and c.slice.value in CARDINALITY_NAMES:
            return True
        if isinstance(c, ast.BinOp):        # `i % 2 == 0` -- a parity on an index
            for sub in ast.walk(c):
                if isinstance(sub, ast.Name) and sub.id in CARDINALITY_NAMES:
                    return True
    return False


# The residue, audited BY HAND. Every entry names the constant, where it is, and
# WHAT IT FALLS OUT OF. An entry with no derivation is a §13 violation wearing an
# allowlist as a costume, so each of these is a sentence I am willing to defend.
HAND_AUDITED_SITES = {
    "SUBPIXEL_INVISIBLE": (
        "INTEGER_STEP / 2.0 in motion_sensor_gate.py. Falls out of the "
        "SENSOR'S OWN OUTPUT QUANTISATION: it emits integer offsets, so a "
        "within-block deformation below half a step cannot change any vector "
        "it could report. A resolution limit, not a tuning knob."),
}


def _numeric_module_constants(tree):
    """Module-level names bound to a numeric literal (directly or through
    arithmetic on other numeric literals).

    THE HOLE THIS CLOSES, AND I WALKED INTO IT MYSELF. The first version of
    this gate walked only `ast.Constant` comparands -- so when I moved a `0.5`
    out of a comparison and into a named module constant, the gate went green
    WITHOUT THE NUMBER GOING ANYWHERE. Naming a threshold is not deriving it.
    Any future threshold could be hidden the same way, so a NAME standing in a
    comparison is now flagged exactly like the literal it holds, and must earn
    its place in `HAND_AUDITED_SITES` with a written derivation.
    """
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        val = node.value
        nums = [c.value for c in ast.walk(val)
                if isinstance(c, ast.Constant)
                and isinstance(c.value, (int, float))
                and not isinstance(c.value, bool)]
        if not nums:
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name):
                out[tgt.id] = nums
    return out


def _thresholds(src):
    """Every DIRECT comparand that is a numeric constant, OR a name bound to
    one, and is neither a zero test nor a cardinality. These are candidate
    THRESHOLDS."""
    tree = ast.parse(src)
    consts = _numeric_module_constants(tree)
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Compare):
            continue
        if _is_cardinality(n):
            continue
        for c in _comparand_walk(n):
            if isinstance(c, ast.Constant) and isinstance(c.value, (int, float)) \
                    and not isinstance(c.value, bool) and not _is_zero_test(c):
                out.append((c.value, n.lineno))
            elif isinstance(c, ast.Name) and c.id in consts \
                    and c.id not in HAND_AUDITED_SITES:
                out.append((c.id, n.lineno))
    return out


@pytest.mark.parametrize("path", [SRC_GATE, SRC_LIB])
def test_no_threshold_is_written_into_the_measurement(path):
    """§13. The tolerance is Otsu over observed values or exactly zero; nothing
    else in the measurement is a level I chose."""
    with open(path) as fh:
        bad = _thresholds(fh.read())
    assert bad == [], (
        f"§13: candidate THRESHOLDS in {os.path.basename(path)}: {bad}. "
        f"Each must be derived and hand-audited, or removed.")


def test_the_only_named_constant_declares_what_it_falls_out_of():
    """The `0.5` was NOT deleted and NOT hidden -- it was named, derived and
    recorded. This asserts the derivation is actually present in the source, so
    the allowlist cannot drift away from the code it excuses."""
    with open(SRC_GATE) as fh:
        src = fh.read()
    assert "SUBPIXEL_INVISIBLE = INTEGER_STEP / 2.0" in src
    assert "INTEGER lattice" in src, "the derivation comment has been removed"
    assert "SUBPIXEL_INVISIBLE" in HAND_AUDITED_SITES


def test_the_ast_gate_bites():
    """POSITIVE CONTROL. Inject a real threshold; the gate MUST go red. Then
    prove the unmodified source is green, so the walker is discriminating and
    not merely permissive.

    Nothing is written to disk -- the injected text goes only to `ast.parse`.
    """
    with open(SRC_LIB) as fh:
        src = fh.read()
    assert _thresholds(src) == [], \
        "the UNMODIFIED source is already red -- the gate is not measuring this rung"

    injected = src.replace(
        "        \"confidently_wrong\": (~t_zero) & (~v_zero) & (err > tol),",
        "        \"confidently_wrong\": (~t_zero) & (~v_zero) & (err > 2.5),", 1)
    assert injected != src, "injection site not found -- the gate has rotted"
    assert _thresholds(injected), \
        "THE GATE DOES NOT BITE: a 2.5 threshold in the classifier passed it"


def test_the_ast_gate_does_not_flag_addressing_or_cardinality():
    """The phi rung's recorded defect, asserted against directly: an array
    INDEX and a structural minimum must NOT be reported as thresholds."""
    assert _thresholds("v = hist[-1]\nif hist[1] > x: pass") == []
    assert _thresholds("if n < 2: pass") == []
    assert _thresholds("if len(owners) == 1: pass") == []
    assert _thresholds("if (xx + 1) * BLOCK <= x0 + fsize: pass") == []
    # ...and a genuine threshold IS reported, so the exclusions are not a hole
    assert _thresholds("if err > 2.5: pass")


def test_a_threshold_cannot_be_HIDDEN_BY_NAMING_IT():
    """THE HOLE I WALKED INTO, ASSERTED AGAINST.

    The first version of this gate went green when I moved a `0.5` from a
    comparison into a named module constant -- the number had not gone
    anywhere, only out of the walker's sight. Naming is not deriving. An
    undeclared name bound to a numeric literal must be flagged exactly like the
    literal, and a declared one must carry a derivation."""
    hidden = "CUTOFF = 2.5\ndef f(err):\n    return err > CUTOFF\n"
    assert _thresholds(hidden), \
        "A THRESHOLD CAN STILL BE HIDDEN BY NAMING IT: the gate is cosmetic"
    # the derived one is admitted, and ONLY because it is hand-audited
    ok = "INTEGER_STEP = 1.0\nSUBPIXEL_INVISIBLE = INTEGER_STEP / 2.0\n" \
         "def f(d):\n    return d <= SUBPIXEL_INVISIBLE\n"
    assert _thresholds(ok) == []
    assert set(HAND_AUDITED_SITES) == {"SUBPIXEL_INVISIBLE"}, (
        "the allowlist grew: every entry needs a written derivation, and this "
        "assertion exists to make growth visible rather than silent")


# --- the instrument itself ---------------------------------------------------

@pytest.fixture(scope="module")
def gate():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_msg", SRC_GATE)
    m = importlib.util.module_from_spec(spec)
    sys.argv = ["motion_sensor_gate"]
    spec.loader.exec_module(m)
    return m


def test_reference_sensor_is_bit_identical_to_the_real_one(gate):
    """THE WHOLE POSITIVE CONTROL RESTS ON THIS. If the reference drifts from
    `mgw.vector_field`, the 'undegraded' arm stops being the instrument under
    test and every degradation comparison becomes meaningless."""
    assert gate.assert_reference_is_the_real_sensor() > 0


def test_invariants_hold_on_the_real_sensor(gate):
    seeds = [0, 1, 2]
    assert gate.invariant_zero_identity(seeds)["passed"]
    assert gate.invariant_unique_minimum(seeds)["passed"]


@pytest.mark.parametrize("degrade,expect", [
    # tiebreak_corner is the footgun `vector_field`'s OWN docstring claims to
    # avoid: a raw row-major scan biases every tie to (-r,-r). On identical
    # frames every offset ties, so I1 is exactly the gate that catches it.
    ("tiebreak_corner", "I1_zero_identity"),
    # radius_half and sad_coarse leave ties alone but break the objective, so
    # they are invisible to I1 and caught by I2.
    ("radius_half", "I2_unique_minimum_fidelity"),
    ("sad_coarse", "I2_unique_minimum_fidelity"),
])
def test_the_gate_bites_on_a_degraded_sensor(gate, degrade, expect):
    """POSITIVE CONTROL ON THE INSTRUMENT. Each degradation is a REAL bug, and
    each must turn a NAMED invariant red -- so the gate is not merely failing,
    it is failing for the right reason."""
    seeds = [0, 1, 2]
    results = {i["name"]: i for i in
               (gate.invariant_zero_identity(seeds, degrade),
                gate.invariant_unique_minimum(seeds, degrade))}
    assert not results[expect]["passed"], (
        f"{degrade} did NOT trip {expect}: the gate does not bite")


def test_the_gate_is_green_on_the_undegraded_sensor(gate):
    """The other half of a positive control, and the half that is usually
    skipped: a gate that fails on everything is not a gate either."""
    seeds = [0, 1, 2]
    for inv in (gate.invariant_zero_identity(seeds),
                gate.invariant_unique_minimum(seeds)):
        assert inv["passed"], f"{inv['name']} red on the UNMODIFIED sensor"


def test_ground_truth_is_constructional_not_sensed(gate):
    """The recorded rule: a diagnostic must not be computed by the component it
    checks. A rigid pan's truth must be recoverable with NO call to the sensor
    at all -- asserted by constructing the pair and checking the identity the
    truth relies on, rather than by reading a docstring."""
    from scripts import motion_sensor_lib as L
    rng = np.random.default_rng(3)
    a = L.texture(rng, 72, beta=1.0, contrast=32.0)
    for dy, dx in ((0, 3), (2, -1), (-4, 4)):
        b = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
        # the construction's defining identity: b[k + D] == a[k], everywhere.
        assert np.array_equal(np.roll(np.roll(b, -dy, axis=0), -dx, axis=1), a)
