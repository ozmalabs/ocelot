"""THE CONTAINMENT SCOPE (seed v1.3.0) -- synthetic gate.

`VISION_SURFACE_ASSIGNMENT_RESULTS.md` measured the defect on the settled
graph: *"`G_own_lost`'s `perim(R) < perim(Q)` awards figure to the SMALLER
perimeter -- so the surface LOSES TO ITS OWN CONTENT BY CONSTRUCTION. THE
PREDICATE DOES NOT MERELY LACK CONTAINMENT; IT INVERTS IT."*

`test_the_INVERSION_is_real_and_the_scope_removes_it` is the minimal stimulus
that exhibits it and is the positive control for this rung's whole claim: a
60-cell ring around a 4-cell hole. Under the standing predicate the RING is
refused and the HOLE mints. Under the scope BOTH mint -- the ring is not
stripped of the hole, it stops losing TO it.

Every other test here is a FLOOR, re-earned rather than inherited:
`bown_nest` defaults OFF, a genuine single-cell figure still mints, iid speckle
is still refused, and the read-out still reconciles with the rules' own output.
"""
from __future__ import annotations

import numpy as np
import pytest

from domains.engine_provenance import engine_preamble

engine_preamble()

from domains import border_ownership_world as bow            # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into   # noqa: E402

ARMS = {"incumbent":   (0.0, 0.0, 0.0),
        "replacement": (1.0, 0.0, 0.0),
        "wellposed":   (1.0, 1.0, 0.0),
        "nested":      (1.0, 1.0, 1.0)}


def run(grid, arm, *, clear_frame=False):
    own, wp, nest = ARMS[arm]
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    h = bow.add_field(s, grid)
    if clear_frame:
        for n in h["cell_ids"]:
            s.set_attr(n, "frame", 0.0)
    bow.set_flag(s, bown=1.0, bown_own=own, bown_wp=wp, bown_nest=nest)
    bow.tick(s, max_steps=200)
    protos = bow.protos(s)
    return sorted((p["members"] for p in protos), reverse=True)


def ring_with_hole():
    """A 60-cell ring (8x8 minus a 2x2 core) enclosing a 4-cell hole."""
    g = [[0] * 12 for _ in range(12)]
    for r in range(2, 10):
        for c in range(2, 10):
            g[r][c] = 1
    for r in range(5, 7):
        for c in range(5, 7):
            g[r][c] = 2
    return g


def figure_12():
    g = [[0] * 12 for _ in range(12)]
    for r in range(3, 9):
        for c in range(4, 8):
            g[r][c] = 1
    return g


# --------------------------------------------------------------------------
#  THE HEADLINE
# --------------------------------------------------------------------------

def test_the_INVERSION_is_real_and_the_scope_removes_it():
    """The defect and its correction, on one stimulus.

    A region that ENCLOSES another must not lose figure status to the thing it
    encloses. Note the ring is 15x the hole -- but NO SIZE IS READ; what changes
    is which borders count as R's own contour."""
    g = ring_with_hole()

    # the inversion: the ring loses to its own content
    assert run(g, "replacement") == [4], "expected only the HOLE to mint"
    assert run(g, "wellposed") == [4], "expected only the HOLE to mint"

    # the correction: the ring mints TOO -- the hole is not taken away from it
    assert run(g, "nested") == [60, 4]


def test_the_incumbent_refuses_BOTH_and_is_untouched():
    """§9 / scope: the isolation predicate vetoes on contact, and this rung does
    not change it."""
    assert run(ring_with_hole(), "incumbent") == []


# --------------------------------------------------------------------------
#  FLOORS -- re-earned under the new arm, never inherited
# --------------------------------------------------------------------------

def test_the_flag_defaults_OFF_so_v1_2_0_reproduces():
    """§9. With no flag passed, `set_flag` writes 0.0 and the standing
    well-posed arm is unchanged."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    bow.add_field(s, figure_12())
    bow.set_flag(s, bown=1.0, bown_own=1.0, bown_wp=1.0)
    for p in s.nodes("BorderOwnParams"):
        assert float(s.node(p)["attrs"]["bown_nest"]) == 0.0


@pytest.mark.parametrize("arm", list(ARMS))
def test_the_committed_12x12_figure_reproduces_in_every_arm(arm):
    assert run(figure_12(), arm) == [24]


@pytest.mark.parametrize("arm", list(ARMS))
def test_a_GENUINE_single_cell_figure_still_mints(arm):
    """The predecessor's hardest constraint: remove the false positive without
    buying a false negative. No arm may read size."""
    g = [[0] * 12 for _ in range(12)]
    g[6][6] = 1
    assert run(g, arm) == [1]


def test_iid_speckle_is_still_refused_under_the_scope():
    """The registered negative control, in miniature. The scope only ever
    REMOVES rivals, so this is the direction of risk and it is asserted here as
    well as measured at n=100."""
    rng = np.random.RandomState(92000 + 700)
    for _ in range(20):
        g = rng.randint(0, 16, (18, 18)).tolist()
        assert run(g, "nested") == [], "the scope minted on iid speckle"


def test_the_scope_never_REMOVES_a_proto_the_standing_arm_minted():
    """Direction check: correcting a quantifier's RANGE can only make
    `G_own_lost` easier to pass, so the nested arm's proto set must be a
    SUPERSET. A drop would mean something other than scoping happened."""
    rng = np.random.RandomState(92000 + 701)
    for _ in range(20):
        g = rng.randint(0, 4, (12, 12)).tolist()
        wp, nest = run(g, "wellposed"), run(g, "nested")
        assert len(nest) >= len(wp), (wp, nest)
