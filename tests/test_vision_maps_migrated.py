"""RUNG 4 — ORIENTATION MAP TOPOGRAPHY: the lateral interaction, and the
measure that reads a map out.

WHY THIS RUNG EXISTS. Every vision result committed before it measured
SINGLE-UNIT tuning and explicitly disclaimed "no map topography is measured".
In real V1 orientation preference forms a smooth MAP, and the verified research
(105-agent pass, VISION_DEVELOPMENT_ARC.md) is 3-0 that maps emerge WITHOUT
visual experience: ferret maps appear P31-36 with no correlation to eye opening
(Chapman/Stryker/Bonhoeffer 1996) and are present in dark-reared animals
(White/Coppola/Fitzpatrick 2001). The map is built by WAVES, before vision.

Before this rung there was NO MECHANISM by which a map could form: Units sat at
random receptive-field centres with NO lateral interactions at all, under a hard
GLOBAL winner-take-all in which exactly one unit learns per step. Nearby units
could not know about each other by any route.

TWO CLASSES OF GATE, and the second is the one that matters:

  1. The MECHANISM is graph-native — `vm_burst_lateral` is a seed rule, the
     ablation is `MapParams.lateral` (graph DATA, not a Python code path), and
     `lateral=0` reproduces the committed hard-WTA behaviour byte-identically.
  2. The MEASURE is calibrated — PROTOCOL 1, "a gate whose measure passes noise
     is not a gate". The orientation readout must recover an ideal Gabor; an
     ideal map must score smooth; RANDOM tuning must score AT the shuffled null.
     Stage 1's sign classifiers passed random noise 50-75% of the time AND
     failed an ideal Gabor, which is exactly why these are gated here and not
     taken on trust.

HONEST KNOWN GAPS, pinned by `test_known_gaps_are_pinned` so they cannot be
quietly forgotten — see VISION_RUNG4_PREREG.md for the measured numbers.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.cortex_sheet import (  # noqa: E402
    add_cortex, map_smoothness, map_stats, orientation_difference,
    preferred_orientation, retinotopic_centres, sheet_pairs, shuffled_null)

MAPS_SEED = os.path.join(ROOT, "seeds", "vision_maps.json")
GH = GW = 6


def _boot(lateral=0.0, *, seed=1, eta=5e-4, h=16, w=16):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_maps"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", float(eta))
    s.set_attr(s.nodes("MapParams")[0], "lateral", float(lateral))
    return s, WaveWorld(s, h=h, w=w, seed=seed)


def _gabor(theta_deg, n=7, lam=4.0, sigma=2.0):
    t = np.radians(theta_deg)
    c = np.arange(n) - (n - 1) / 2.0
    yy, xx = np.meshgrid(c, c, indexing="ij")
    yp = -xx * np.sin(t) + yy * np.cos(t)
    xp = xx * np.cos(t) + yy * np.sin(t)
    return (np.exp(-(xp ** 2 + yp ** 2) / (2 * sigma ** 2))
            * np.cos(2 * np.pi * yp / lam))


# --------------------------------------------------------------------------- #
#  1. THE MEASURE — calibrated before it is ever pointed at the agent.
# --------------------------------------------------------------------------- #
def test_orientation_readout_recovers_an_ideal_gabor():
    """PROTOCOL 1. The per-unit preferred-orientation readout must recover the
    orientation of an IDEAL Gabor. If this fails, every map statistic built on
    it is meaningless — and Stage 1 shipped a sign classifier that failed
    exactly this check.

    The readout returns the orientation the RF's Fourier energy sits at, which
    is perpendicular to the bars — a CONSTANT 90-degree offset applied to every
    unit alike, so it cannot affect a statistic that reads only DIFFERENCES."""
    for th in (0, 15, 30, 45, 60, 75, 90, 120, 150):
        got = (preferred_orientation(_gabor(th)) - 90.0) % 180.0
        assert orientation_difference(got, th) < 5.0, (
            f"ideal Gabor at {th} deg read back as {got:.1f} deg")


def test_orientation_difference_is_axial():
    """Orientation is axial (mod 180): 179 and 1 degrees are 2 apart, not 178.
    Getting this wrong inflates every difference and would flatter the data and
    the null alike, hiding the error."""
    assert orientation_difference(179.0, 1.0) == pytest.approx(2.0)
    assert orientation_difference(0.0, 90.0) == pytest.approx(90.0)
    assert orientation_difference(10.0, 20.0) == pytest.approx(10.0)
    assert 0.0 <= orientation_difference(123.4, 5.6) <= 90.0


def test_an_ideal_map_scores_smooth_and_random_tuning_scores_at_the_null():
    """PROTOCOL 1's two-sided calibration, and the one that actually bites.

    An ideal map (orientation ramping across the sheet) must score STRONGLY
    NEGATIVE against its shuffled-position null. RANDOM tuning must score AT the
    null (d ~ 0) — this is the "does the measure pass noise?" check that Stage
    1's classifiers failed.

    The shuffled-position null is the right null because it destroys topography
    while holding the tuning DISTRIBUTION exactly fixed."""
    ps = sheet_pairs(GH, GW)

    ideal = [(180.0 * j / GW) % 180.0 for _i in range(GH) for j in range(GW)]
    d_ideal = map_smoothness(ideal, ps) - shuffled_null(ideal, ps, n_perm=500, seed=1)
    assert d_ideal < -15.0, f"an ideal map did not score smooth (d={d_ideal:+.2f})"

    ds = []
    for sd in range(20):
        rng = np.random.default_rng(1000 + sd)
        th = list(rng.uniform(0, 180, GH * GW))
        ds.append(map_smoothness(th, ps) - shuffled_null(th, ps, n_perm=200, seed=sd))
    m = float(np.mean(ds))
    assert abs(m) < 2.0, (
        f"RANDOM tuning does not sit at the shuffled null (d={m:+.3f}) — the "
        "measure passes noise, so it is not a gate")


def test_the_null_holds_the_tuning_distribution_fixed():
    """The shuffled null must be a permutation of the SAME values — if it
    changed the tuning distribution, an arm could win by becoming less tuned
    rather than more map-like."""
    ps = sheet_pairs(GH, GW)
    th = [0.0] * (GH * GW)          # degenerate: every unit identical
    # Every permutation is identical => observed and null must coincide exactly.
    assert map_smoothness(th, ps) == pytest.approx(0.0)
    assert shuffled_null(th, ps, n_perm=50, seed=0) == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
#  2. THE MECHANISM is graph-native, and the ablation is DATA.
# --------------------------------------------------------------------------- #
def test_the_lateral_interaction_is_a_rule_not_python():
    """CLAUDE.md's architecture rule + PROTOCOL 0. Which units burst is the
    graph's DECISION — an Argmax over `act` in a seed rule's where-clause,
    gated on MapParams.lateral — never a Python branch. The adapter may wire
    sheet geometry and read the map back out; it may not decide."""
    with open(MAPS_SEED) as f:
        seed = json.load(f)
    r = [x for x in seed["rules"] if x["name"] == "vm_burst_lateral"][0]
    blob = json.dumps(r["where"])
    assert '"Argmax"' in blob, "the winner is not chosen by the graph"
    assert "cortical_neighbour" in json.dumps(r["match"])
    assert "lateral" in blob, "the ablation is not read from graph data"
    mp = [n for n in seed["nodes"] if n["type"] == "MapParams"][0]["attrs"]
    assert mp["lateral"] == 0.0, "the new mechanism must ship OFF (PROTOCOL 9)"

    src = open(os.path.join(ROOT, "domains", "cortex_sheet.py")).read()
    for banned in ("argmax", "np.argmax", "sorted(", ".sort("):
        assert banned not in src, f"the adapter ranks/selects: {banned}"
    for ln in src.splitlines():
        if "set_attr" in ln:
            assert '"bursting"' not in ln, f"the adapter decides a burst: {ln.strip()}"


def test_lateral_off_is_the_committed_hard_winner_take_all():
    """PROTOCOL 9 — defaults preserve committed results. With lateral=0 exactly
    ONE unit may be crowned per step by wv_unit_burst_winner's Argmax (units
    bursting beyond that are wv_unit_burst_sustain's tail of previous winners,
    which is the committed behaviour). Switching lateral on must strictly
    INCREASE the number of units learning per step — that is the mechanism."""
    counts = {}
    for lat in (0.0, 1.0):
        s, w = _boot(lat, seed=11)
        us = add_cortex(w, GH, GW, rf=7)
        tot = 0
        for i in range(40):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
            tot += sum(1 for u in us
                       if float(s.node(u)["attrs"]["bursting"]) == 1.0)
        counts[lat] = tot / 40.0
    assert counts[1.0] > counts[0.0] + 0.5, (
        f"the lateral rule did not fire: {counts[0.0]:.2f} -> {counts[1.0]:.2f} "
        "bursting units/step")


def test_the_sheet_is_retinotopic_and_adjacency_is_symmetric():
    """The adapter's TWO mechanical facts. Retinotopy is anatomy (the same kind
    of positional fact as the retina's own grid), and cortical adjacency is
    symmetric. Neither is a decision; both are gated so they cannot silently
    change under the result."""
    s, w = _boot(seed=12)
    cs = retinotopic_centres(w, GH, GW, rf=7)
    assert len(cs) == GH * GW
    # Cortically adjacent => retinally adjacent (monotone, non-decreasing).
    for k in range(GH * GW - 1):
        i, j = divmod(k, GW)
        if j + 1 < GW:
            assert cs[k + 1][1] >= cs[k][1], "retinotopy is not monotone in x"
    us = add_cortex(w, GH, GW, rf=7)
    idx = {u: k for k, u in enumerate(us)}
    for u in us:
        for v in s.neighbours(u, "cortical_neighbour"):
            back = list(s.neighbours(v, "cortical_neighbour"))
            assert u in back, "cortical adjacency is not symmetric"
        assert len(list(s.neighbours(u, "cortical_neighbour"))) <= 4
    assert len(sheet_pairs(GH, GW)) == 2 * GH * (GW - 1)
    assert len(idx) == GH * GW


def test_the_rule_terminates_and_does_not_burst_everything():
    """The lateral rule must reach a fixpoint and burst only the winner's
    NEIGHBOURHOOD — if it bursted the whole sheet there would be no competition
    left and every unit would chase the same component (no map, by
    construction). The retained global Argmax is the inhibition half of the
    Mexican hat."""
    s, w = _boot(1.0, seed=13)
    us = add_cortex(w, GH, GW, rf=7)
    peak = 0
    for i in range(40):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
        peak = max(peak, sum(1 for u in us
                             if float(s.node(u)["attrs"]["bursting"]) == 1.0))
    assert 0 < peak < GH * GW, (
        f"{peak}/{GH * GW} units burst — competition is gone")
    for u in us:
        assert np.all(np.isfinite(w.receptive_field(u))), "weights diverged"


# --------------------------------------------------------------------------- #
#  3. HONEST KNOWN GAPS — pinned so they cannot be quietly forgotten.
# --------------------------------------------------------------------------- #
def test_known_gaps_are_pinned():
    """PROTOCOL 8 — scope discipline. These are the things rung 4 does NOT
    show, recorded as an executable reminder rather than prose that rots.

    * NO PINWHEELS / SINGULARITIES are demonstrated. A 6x6 sheet over a 16x16
      retina cannot resolve one, and none is claimed. `map_stats` deliberately
      returns no pinwheel count — if someone adds one, this gate makes them
      confront the fact that the sheet is far too small to support the claim.
    * The neighbourhood kernel is a TOP HAT (binary, radius 1, fixed), not a
      graded Gaussian that shrinks over training as a textbook SOM's does.
    * `lateral=0` is NOT expected to be null — cortical neighbours have
      overlapping receptive fields (retinotopy, which is anatomy), so they see
      partly-shared input and some smoothness arises without any lateral
      interaction. That is why the pre-registered mechanism test is the
      INTERACTION (PROTOCOL 4), not "ON beats its own null".
    """
    s, w = _boot(1.0, seed=14)
    us = add_cortex(w, GH, GW, rf=7)
    for i in range(20):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    st = map_stats(w, us, GH, GW, n_perm=20, seed=0)
    assert "pinwheel" not in st, (
        "a pinwheel statistic appeared — a 6x6 sheet over a 16x16 retina "
        "cannot resolve a singularity; do not claim one")
    assert st["n_pairs"] == 2 * GH * (GW - 1)
    with open(MAPS_SEED) as f:
        blob = json.dumps(json.load(f))
    assert "TOP HAT" in blob, (
        "the top-hat (non-graded, non-shrinking) neighbourhood simplification "
        "is no longer named in the seed's own comment")
