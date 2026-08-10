"""RUNG 7 — retinal lateral inhibition: the gates.

Gates PROTOCOL §0 (ablations are graph DATA, never a Python code path), §1 (the
MEASURE is calibrated before the agent — floor, ideal, and duration), §2
(convergence), §8 (what is NOT claimed), §9 (defaults preserve committed
results) and §10 (engine provenance).

**THE MEASURES ARE GATED TOO**, which is the point of §1: `SD`'s floor is
ANALYTIC (rung 6's complementary split forces `C_ON,OFF = -C_ON,ON` exactly, so
`SD = 0`), and a test asserts the instrument actually returns it. A measure whose
floor is derived rather than hoped-for is the strongest instrument this ladder
has had — and it is worth nothing unless the code reproduces it.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.seed_registry  # noqa: F401,E402
from domains.lateral_world import (  # noqa: E402
    add_lateral_retina, channels, freeze_lateral, gains, install_gains,
    set_lat_params,
)
from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

H = W = 16


def _world(*, seed=0, lateral=1.0, learn_gain=1.0, radius2=1.0, eta=2e-3):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", 0.0)
    w = WaveWorld(s, h=H, w=W, seed=seed)
    anat = add_lateral_retina(w)
    set_lat_params(w, lateral=lateral, learn_gain=learn_gain, radius2=radius2,
                   lat_eta=eta, lat_gmax=2.0, frozen=0.0)
    return w, anat


def _waves(w, n, every=5):
    for i in range(n):
        w.step(ignite_k=1 if i % every == 0 else 0)


# --------------------------------------------------------------------------- #
#  PROTOCOL 9 — DEFAULTS PRESERVE COMMITTED RESULTS
# --------------------------------------------------------------------------- #
def test_the_seed_ships_inert_so_every_committed_result_reproduces():
    """`lateral = 0` in the MANIFEST, read off the file itself."""
    path = os.path.join(ROOT, "seeds", "vision_lateral.json")
    with open(path) as fh:
        man = json.load(fh)
    attrs = man["nodes"][0]["attrs"]
    assert attrs["lateral"] == 0.0, (
        "vision_lateral must ship INERT (PROTOCOL 9) or every result committed "
        "before rung 7 silently changes")
    assert attrs["lat_g0"] == 0.0, (
        "the layer must start as a PURE CENTRE with NO surround — the "
        "centre-surround profile is the thing being GROWN. A non-zero lat_g0 "
        "would hand the agent the answer (PROTOCOL 0)")


def test_layer_off_is_completely_inert():
    w, anat = _world(lateral=0.0)
    g0 = gains(w, anat["hcells"]).copy()
    _waves(w, 100)
    assert np.abs(gains(w, anat["hcells"]) - g0).max() == 0.0
    on, off = channels(w, anat["bipolars"])
    assert on.max() == 0.0 and off.max() == 0.0, (
        "lateral=0 must leave the bipolars silent — the layer is not selected")


# --------------------------------------------------------------------------- #
#  THE FREEZE  (rung 5 measured 47.9 max|dw| per probe from `oja=0`)
# --------------------------------------------------------------------------- #
def test_the_real_freeze_is_exact():
    w, anat = _world()
    _waves(w, 200)
    freeze_lateral(w)
    g = gains(w, anat["hcells"]).copy()
    _waves(w, 150)
    assert np.abs(gains(w, anat["hcells"]) - g).max() == 0.0, (
        "the freeze must be EXACT — a probe that lets the layer learn is the "
        "instrument training itself (rung 5's 47.9-per-probe trap)")


# --------------------------------------------------------------------------- #
#  THE RULES ACTUALLY FIRE  (rung 6's `oo_learn_oja` silently never did)
# --------------------------------------------------------------------------- #
def test_the_learning_rule_actually_fires():
    """A rule that cannot fire fails SILENTLY and reads as a result."""
    w, anat = _world()
    g0 = gains(w, anat["hcells"]).copy()
    _waves(w, 200)
    dg = np.abs(gains(w, anat["hcells"]) - g0)
    assert dg.max() > 0.0, "lat_learn_gain NEVER FIRED — the arm is a null arm"
    assert (dg > 0).mean() > 0.9, (
        f"only {(dg>0).mean():.1%} of gains moved — the rule is firing for "
        "some cells only, which would silently bias every population statistic")


def test_both_channels_are_alive_once_a_surround_exists():
    """THE OFF CHANNEL IS CREATED BY THE PREDICTOR.

    With g=0 the OFF channel is SILENT (resid = c >= 0) — correct biology, and
    the reason this rung matters: only a non-zero prediction makes a
    non-bursting cell a DECREMENT with something to report.
    """
    w, anat = _world(learn_gain=0.0)          # g pinned at 0: pure centre
    _waves(w, 60)
    on, off = channels(w, anat["bipolars"])
    assert on.max() > 0.0
    assert off.max() == 0.0, (
        "with NO surround the OFF channel must be silent — if it is not, the "
        "OFF channel is coming from somewhere other than the residual")

    w2, anat2 = _world()                       # learned surround
    _waves(w2, 800)
    on2, off2 = channels(w2, anat2["bipolars"])
    assert off2.max() > 0.0, (
        "once a surround is learned the OFF channel MUST come alive — that is "
        "the residual-mint claim (VISION_PRIOR_ART: 'that quantum IS the OFF "
        "channel')")


# --------------------------------------------------------------------------- #
#  THE MEASURE (PROTOCOL 1) — floor, ideal, duration
# --------------------------------------------------------------------------- #
def test_THE_ANALYTIC_FLOOR_the_rung6_split_scores_exactly_zero():
    """**THE INSTRUMENT'S KEYSTONE.** Rung 6's `x_OFF = 1 - x_ON` is an affine
    map with negative slope, so `C_ON,OFF(d) = -C_ON,ON(d)` IDENTICALLY and the
    shape departure is EXACTLY 0. Not approximately: exactly. If this drifts,
    the instrument is wrong and no other number in rung 7 means anything.
    """
    from scripts.rung7_lib import (complementary_channels, corr_by_distance,
                                   raw_burst_movie, shape_departure,
                                   space_constant)
    w, _ = _world()
    burst = raw_burst_movie(w, 250)
    on, off = complementary_channels(burst)
    ds, Cnn = corr_by_distance(on, on)
    _, Cnf = corr_by_distance(on, off)
    assert np.allclose(Cnn + Cnf, 0.0, atol=1e-9), (
        "C_ON,OFF must equal -C_ON,ON IDENTICALLY under the complementary "
        "split — this is rung 6's whole diagnosis, reproduced")
    assert abs(shape_departure(Cnn, Cnf)) < 1e-9, (
        "SD's floor is ANALYTIC and must be 0 exactly")
    assert abs(space_constant(ds, Cnn) - space_constant(ds, Cnf)) < 1e-9, (
        "degenerate channels must have IDENTICAL space constants")


def test_the_measure_is_not_a_null_instrument():
    """PROTOCOL 1's ideal exemplar: a hand-installed surround MUST move SD off
    its floor. (Rung 3's eta was a null instrument; only this check found it.)"""
    from scripts.rung7_lib import (corr_by_distance, record_channels,
                                   shape_departure)
    w, anat = _world(learn_gain=0.0)
    install_gains(w, anat["hcells"], 0.5, 0.5)   # the balanced-DoG reference
    freeze_lateral(w)
    on, off = record_channels(w, anat, 250)
    ds, Cnn = corr_by_distance(on, on)
    _, Cnf = corr_by_distance(on, off)
    sd = shape_departure(Cnn, Cnf)
    assert sd > 0.2, (
        f"SD={sd:.4f}: a PERFECT centre-surround failed to move the statistic "
        "off its analytic floor of 0 => the statistic is a NULL INSTRUMENT and "
        "every arm measured with it is meaningless")


def test_SD_is_undefined_not_zero_when_the_OFF_channel_does_not_exist():
    """`nan`, not 0. With g=0 there is no OFF channel to be degenerate WITH,
    and reporting 0 ('maximally degenerate') would be a lie of exactly the kind
    this ladder keeps retracting."""
    from scripts.rung7_lib import shape_departure
    assert np.isnan(shape_departure(np.array([0.4, 0.2, 0.1]), np.array([])))
    assert np.isnan(shape_departure(np.array([0.4, 0.2, 0.1]),
                                    np.array([0.0, 0.0, 0.0])))


def test_the_CS_index_reads_the_installed_gain_exactly():
    """CS = g1 + g2 BY CONSTRUCTION (each h_k is a MEAN over its ring, so a ring
    sums to -g_k). Calibrated against hand-installed references: floor 0."""
    from scripts.rung7_lib import cs_index, effective_rf
    w, anat = _world(learn_gain=0.0)
    install_gains(w, anat["hcells"], 0.0, 0.0)
    assert abs(cs_index(effective_rf(w, anat))) < 1e-6, (
        "pure centre MUST score CS=0 — the floor is analytic")
    w2, anat2 = _world(learn_gain=0.0)
    install_gains(w2, anat2["hcells"], 0.5, 0.5)
    assert abs(cs_index(effective_rf(w2, anat2)) - 1.0) < 1e-6, (
        "a balanced DoG MUST score CS=1.0")


def test_the_effective_RF_is_a_centre_surround_not_a_blob():
    """The SHAPE, not just the index: centre positive, every surround ring
    negative, and the far ring WEAKER than the near one."""
    from scripts.rung7_lib import effective_rf
    w, anat = _world(learn_gain=0.0)
    install_gains(w, anat["hcells"], 0.5, 0.5)
    rf = effective_rf(w, anat)
    assert rf[2, 2] > 0, "the centre must be excitatory"
    ring1 = [rf[1, 2], rf[3, 2], rf[2, 1], rf[2, 3]]
    ring2 = [rf[0, 2], rf[4, 2], rf[2, 0], rf[2, 4]]
    assert all(v < 0 for v in ring1), f"ring 1 must be inhibitory, got {ring1}"
    assert all(v < 0 for v in ring2), f"ring 2 must be inhibitory, got {ring2}"
    assert abs(np.mean(ring2)) < abs(np.mean(ring1)), (
        "the far ring must be WEAKER than the near ring — a centre-surround, "
        "not a uniform inhibitory blob")


# --------------------------------------------------------------------------- #
#  PROTOCOL 0 — ABLATIONS ARE GRAPH DATA
# --------------------------------------------------------------------------- #
def test_no_python_decides_anything_the_ablations_are_graph_data():
    """No branch on an ablation flag in the adapter: every ablation is DATA the
    RULES read.

    Checks the CODE, not the prose. A plain substring grep over the file fired
    on this module's own docstring (which contains the sentence "there is no
    `if lateral` ... in this file") — a gate that a comment can trip is a gate
    that will be silenced by rewording rather than by fixing. So the source is
    parsed and every `if`/`while` TEST is rendered back to code and inspected;
    docstrings and comments are invisible to it by construction.
    """
    import ast
    path = os.path.join(ROOT, "domains", "lateral_world.py")
    with open(path) as fh:
        tree = ast.parse(fh.read())
    flags = {"lateral", "learn_gain", "radius2", "frozen", "onoff"}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.If, ast.While, ast.IfExp)):
            continue
        test_src = ast.unparse(node.test)
        for f in flags:
            assert f not in test_src, (
                f"`{ast.unparse(node.test)}` branches on the ablation flag "
                f"`{f}` in lateral_world.py — that is an agent DECISION in "
                "Python. The ablation belongs on the LatParams node, read by "
                "the rule's `where` (PROTOCOL 0 / CLAUDE.md)")


def test_radius2_ablation_is_data_and_pins_g2_with_anatomy_intact():
    """`radius2=0` must pin g2=0 while the neighbour2 edges still stand — an
    ablation that also removes anatomy is not null (rung 4's lesson)."""
    w, anat = _world(radius2=0.0)
    n2 = len(w.s.neighbours(w.cells[(8, 8)], "neighbour2"))
    assert n2 == 8, f"the radius-2 anatomy must remain wired, got {n2} edges"
    _waves(w, 400)
    g = gains(w, anat["hcells"])
    assert np.abs(g[:, 1]).max() == 0.0, "radius2=0 must pin g2 at 0"
    assert g[:, 0].max() > 0.0, "radius2=0 must leave the NEAR surround learning"


def test_learn_gain_ablation_pins_the_gain():
    w, anat = _world(learn_gain=0.0)
    install_gains(w, anat["hcells"], 0.3, 0.3)
    g0 = gains(w, anat["hcells"]).copy()
    _waves(w, 300)
    assert np.abs(gains(w, anat["hcells"]) - g0).max() == 0.0, (
        "learn_gain=0 is the FIXED-gain control and must not move")


# --------------------------------------------------------------------------- #
#  DALE — the sign lives in the PATHWAY, never in a weight
# --------------------------------------------------------------------------- #
def test_dale_holds_every_gain_stays_non_negative():
    w, anat = _world()
    _waves(w, 1200)
    g = gains(w, anat["hcells"])
    assert g.min() >= 0.0, (
        f"a gain went NEGATIVE ({g.min():.4f}) — Dale is broken. The horizontal "
        "cell is a SIGN-CONSTANT inhibitory pathway; only its MAGNITUDE is "
        "learned. A signed weight here would be the hand-built-DoG error in "
        "disguise")
    assert g.max() <= 2.0 + 1e-9, "gains must stay clipped to [0, lat_gmax]"


# --------------------------------------------------------------------------- #
#  PROTOCOL 2 — CONVERGENCE (the gate that stopped rungs 5 and 6)
# --------------------------------------------------------------------------- #
@pytest.mark.slow
def test_the_rule_converges_on_its_own_input_distribution():
    """Drift -> 0 AND a plateau at NON-ZERO structure, with 0 NaN.

    Pinned at the measured values (eta=2e-3, seed 3000): drift falls to <0.03
    by 6400 steps and CS plateaus near the DC-cancelling balance of ~1.0. This
    is the check that stopped rung 5 and rung 6, and it is pinned because a
    change that breaks it silently invalidates every arm above it.
    """
    w, anat = _world(seed=3000, eta=2e-3)
    _waves(w, 4800)
    g_a = gains(w, anat["hcells"]).copy()
    _waves(w, 1600)
    g_b = gains(w, anat["hcells"])
    drift = float(np.linalg.norm(g_b - g_a)) / float(np.linalg.norm(g_b))
    assert int(np.isnan(g_b).sum()) == 0, "NaN in the gains"
    assert drift < 0.05, f"drift {drift:.4f} — the rule has not settled"
    cs = float(g_b.sum(axis=1).mean())
    assert cs > 0.5, (
        f"CS={cs:.4f} — converged to NOTHING. A rule that settles at no "
        "structure is rung 6's second stop condition")


@pytest.mark.slow
def test_THE_HEADLINE_waves_grow_a_surround_that_breaks_the_degeneracy():
    """RUNG 7's claim, pinned: from `g = 0` (a pure centre), the agent's OWN
    waves grow a centre-surround, and the ON/OFF channels stop being degenerate.

    Compare against the analytic floor of 0 that the SAME instrument returns for
    rung 6's split on the SAME kind of input.
    """
    from scripts.rung7_lib import (corr_by_distance, record_channels,
                                   shape_departure, space_constant)
    w, anat = _world(seed=3000, eta=2e-3)
    _waves(w, 6400)
    g = gains(w, anat["hcells"])
    assert g.sum(axis=1).mean() > 0.5, "no surround grew"
    freeze_lateral(w)
    on, off = record_channels(w, anat, 300)
    ds, Cnn = corr_by_distance(on, on)
    _, Cnf = corr_by_distance(on, off)
    sd = shape_departure(Cnn, Cnf)
    assert sd > 0.0595, (
        f"SD={sd:.4f} did not clear the SESOI — the degeneracy did NOT break")
    snn, snf = space_constant(ds, Cnn), space_constant(ds, Cnf)
    assert snf > snn, (
        f"space constants {snn:.3f}/{snf:.3f}: the ON/OFF correlation function "
        "must have DIFFERENT spatial dependence from ON/ON — that is Miller "
        "1994's precondition and the entire point of the rung")


# --------------------------------------------------------------------------- #
#  PROTOCOL 8 — WHAT IS NOT CLAIMED
# --------------------------------------------------------------------------- #
def test_NOT_CLAIMED_the_degeneracy_break_is_not_caused_by_LEARNING():
    """**A PIN ON AN HONEST BOUNDARY, not on a result.**

    A hand-installed FIXED surround breaks the degeneracy just as well as a
    learned one. So the break is a property of LATERAL INHIBITION (the
    subtraction), NOT of learning it. What learning earns is that the gain is
    DERIVED rather than hand-set, and the Atick & Redlich prediction that only a
    derived gain can make. Anyone reading rung 7 as "learning breaks the
    degeneracy" is reading it wrong, and this test says so in code.
    """
    from scripts.rung7_lib import (corr_by_distance, record_channels,
                                   shape_departure)
    w, anat = _world(learn_gain=0.0)
    install_gains(w, anat["hcells"], 0.5, 0.5)
    freeze_lateral(w)
    on, off = record_channels(w, anat, 250)
    ds, Cnn = corr_by_distance(on, on)
    _, Cnf = corr_by_distance(on, off)
    assert shape_departure(Cnn, Cnf) > 0.0595, (
        "a FIXED surround must also break the degeneracy — if it does not, the "
        "boundary recorded in VISION_RUNG7_PREREG.md is wrong")


def test_NOT_CLAIMED_no_orientation_selectivity_is_measured_here():
    """Rung 7 mints NO SUnit and NO cortical Unit. It is a claim about the
    RETINA's output statistics and nothing else. Whether these channels let a
    cortical cell develop orientation is the NEXT rung's question, and this
    test pins that rung 7 does not silently answer it."""
    w, _ = _world()
    assert len(w.s.nodes("SUnit")) == 0
    assert len(w.s.nodes("Unit")) == 0
