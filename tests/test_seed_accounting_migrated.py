"""Gates for the seed-accounting audit (VISION_SEED_ACCOUNTING_RESULTS.md).

THE REUSABLE GATE this rung leaves behind is `seed_audit.check_block`. A future
rung asserts, at PRE-REGISTRATION time, that its declared block is a superset of
what its runner measurably draws:

    from seed_audit import check_block
    ok, outside = check_block(["scripts/my_rung.py"], 82000, 82999)
    assert ok, f"draws outside declared block: {outside}"

That one line, existing earlier, would have caught the resolution rung's K-arm
collision BEFORE the rung ran rather than at its end.

VISION_PROTOCOL.md §1.1 / the dead-instrument rule: zero consumption is a
LEGITIMATE result (the k-scope and block-unit rungs consumed none by design), so
a detector reporting zero everywhere and a clean tree look IDENTICAL. Every gate
below is therefore POSITIVE-CONTROLLED -- it is shown to fire on a planted
defect and to go quiet when the defect is removed.
"""
from __future__ import annotations

import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

from seed_audit import analyse_file, check_block, measured_seeds  # noqa: E402


def _ranges(seeds):
    out = []
    for x in sorted(seeds):
        if out and x == out[-1][1] + 1:
            out[-1][1] = x
        else:
            out.append([x, x])
    return [(a, b) for a, b in out]


# --- V3: blind recovery of the known defect --------------------------------

def test_recovers_resolution_rungs_four_scattered_subranges():
    """The audited defect. `resolution_scale_measure.py` declares SEED_BLOCK =
    79000 and contains NO literal '79200' anywhere; recovering its true draws
    needs constant propagation + range() expansion + interprocedural binding.

    This is the test that proves the instrument is not a substring scan
    (§12: a selector that matches by substring is not a selector)."""
    r = analyse_file(os.path.join(SCRIPTS, "resolution_scale_measure.py"))
    assert _ranges(r["seeds"]) == [
        (79200, 79249), (79400, 79449), (79700, 79749), (79800, 79849)
    ]
    assert r["unknown_sinks"] == 0

    # The claim is that the number is not a CODE literal. A substring check is
    # the wrong selector and went red here on first run: '79200' DOES appear in
    # the file -- in the docstring, where the resolution rung recorded its own
    # post-hoc audit. Prose is not what the analyser reads. So the selector is
    # fixed (not the gate weakened, §5/§12): assert over AST integer constants.
    import ast
    tree = ast.parse(open(os.path.join(SCRIPTS,
                                       "resolution_scale_measure.py")).read())
    literals = {n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, int)}
    assert 79200 not in literals, "if it were a code literal this proves nothing"
    assert not (literals & set(range(79000, 80000)) - {79000}), \
        "only the BASE 79000 may appear literally; every draw must be derived"


def test_k_arm_allocation_collides_with_what_the_rung_consumed():
    """The rung's prereg allocated 79200-79399 to the K arm. The rung itself
    consumed 79200-79249. That arm cannot run on its declared range."""
    drawn = measured_seeds([os.path.join(SCRIPTS, "resolution_scale_measure.py")])
    k_arm = set(range(79200, 79400))
    assert drawn & k_arm, "the K-arm collision must be detectable from source"
    assert min(drawn & k_arm) == 79200
    assert max(drawn & k_arm) == 79249


# --- V1: this rung audits ITSELF before auditing anyone else ----------------

def test_self_audit_declared_superset_of_measured():
    """V1. If the tool cannot report THIS rung's own consumption, it does not
    work and no other number it produces may be quoted."""
    me = os.path.join(SCRIPTS, "seed_audit_selfcheck.py")
    r = analyse_file(me)
    assert _ranges(r["seeds"]) == [(82000, 82049), (82300, 82349)]
    assert r["unknown_sinks"] == 0

    ok, outside = check_block([me], 82000, 82999)
    assert ok and outside == []


def test_the_gate_can_actually_fail():
    """A gate that has never been ABLE to fail has not been tested. Declaring a
    block too NARROW for what is measurably drawn must go red."""
    me = os.path.join(SCRIPTS, "seed_audit_selfcheck.py")
    ok, outside = check_block([me], 82000, 82099)
    assert not ok
    assert outside[0] == 82300 and outside[-1] == 82349


# --- V2: planted-collision positive control --------------------------------

def test_planted_collision_is_detected_and_removal_restores_clean(tmp_path):
    """V2. Plant a script drawing a seed measurably inside the resolution
    rung's CONSUMED range, and show the detector fires -- then that removing it
    goes quiet. This is what separates a working detector from one that reports
    zero everywhere."""
    victim = measured_seeds(
        [os.path.join(SCRIPTS, "resolution_scale_measure.py")])
    assert 79210 in victim, "precondition: 79210 is really consumed"

    planted = tmp_path / "planted_rung.py"
    planted.write_text(textwrap.dedent(
        """
        import numpy as np
        BASE = 79000
        def go():
            for t in range(5):
                yield np.random.default_rng(BASE + 210 + t)
        """
    ))
    drawn = measured_seeds([str(planted)])
    assert 79210 in drawn, "planted draw must be recovered through BASE + 210 + t"
    assert drawn & victim, "COLLISION must be detected"

    # ...and the same file declared against a free block goes red on the gate.
    ok, outside = check_block([str(planted)], 82000, 82999)
    assert not ok and 79210 in outside

    planted.unlink()
    assert measured_seeds([str(tmp_path)]) == set(), "removal restores clean"


# --- coverage honesty: the tool must SAY when it cannot see ----------------

def test_unresolvable_seeds_are_reported_unknown_not_silently_dropped(tmp_path):
    """The tool under-reports; it must never over-report. A data-dependent seed
    must surface as an unknown sink rather than vanishing or being guessed."""
    f = tmp_path / "opaque.py"
    f.write_text(textwrap.dedent(
        """
        import os, numpy as np
        def go(pool):
            a = np.random.default_rng(hash(pool) % 2**31)   # data-dependent
            b = np.random.default_rng(int(os.environ["S"]))  # runtime
            return a, b
        """
    ))
    r = analyse_file(str(f))
    assert r["seeds"] == []
    assert r["unknown_sinks"] == 2, "both must be COUNTED as unseen, not dropped"


def test_module_boundary_is_a_declared_blind_spot(tmp_path):
    """Interprocedural analysis is INTRA-FILE. A seed imported from another
    module is invisible -- asserted here so the limit is a tested property of
    the tool rather than a claim in prose."""
    (tmp_path / "consts.py").write_text("BLOCK = 82500\n")
    f = tmp_path / "user.py"
    f.write_text("import numpy as np\nfrom consts import BLOCK\n"
                 "r = np.random.default_rng(BLOCK + 1)\n")
    r = analyse_file(str(f))
    assert r["seeds"] == [], "cross-module constants are NOT resolved"
    assert r["unknown_sinks"] == 1, "but the sink is still COUNTED"


@pytest.mark.parametrize("sink,expected", [
    ("np.random.default_rng(82001)", [82001]),
    ("random.Random(82002)", [82002]),
    ("np.random.RandomState(82003)", [82003]),
    ("random.seed(82004)", [82004]),
    ("torch.manual_seed(82005)", [82005]),
])
def test_each_supported_sink_form_is_recognised(tmp_path, sink, expected):
    f = tmp_path / "s.py"
    f.write_text(f"import random, numpy as np, torch\nx = {sink}\n")
    assert analyse_file(str(f))["seeds"] == expected
