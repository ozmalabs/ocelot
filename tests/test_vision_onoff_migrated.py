"""RUNG 6 — THE SIGNED SIMPLE LAYER (ON/OFF split): gates.

Gates the MEASURE and the FREEZE as hard as the mechanism (PROTOCOL 1: a gate
whose measure passes noise is not a gate), and PINS the honest known gaps
(PROTOCOL 8) so a later change cannot quietly turn a negative into a claim.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.onoff_world import (add_onoff_retina, add_signed_units, freeze,
                                 thaw, set_params, signed_rf, channel_rf,
                                 weights, install_signed_rf, segregation)
from domains.complex_cells import cell_stats, gabor, grating, binarize, present

H = W = 16
RF = 7
PERIOD = 4.0


def _world(*, seed=0, n_units=4, split=1.0, subnorm=1.0, eta=5e-4, onoff=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_onoff"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", 0.0)
    w = WaveWorld(s, h=H, w=W, seed=seed)
    bip = add_onoff_retina(w)
    us = add_signed_units(w, bip, n_units, rf=RF, seed=seed)
    set_params(w, onoff=onoff, split=split, subnorm=subnorm, oo_eta=eta,
               oo_wmax=2.0, frozen=0.0, homeo=1.0, theta_rate=0.05)
    return w, us, bip


def _waves(w, n, every=5):
    for i in range(n):
        w.step(ignite_k=1 if i % every == 0 else 0)


# --------------------------------------------------------------------------- #
#  PROTOCOL 9 — DEFAULTS PRESERVE COMMITTED RESULTS
# --------------------------------------------------------------------------- #
def test_onoff_is_off_by_default_in_the_manifest():
    """Every committed result must reproduce byte-identically, so the whole
    layer ships inert."""
    import json
    d = json.load(open(os.path.join(ROOT, "seeds", "vision_onoff.json")))
    attrs = d["nodes"][0]["attrs"]
    assert attrs["onoff"] == 0.0, "the layer must ship OFF (PROTOCOL 9)"
    assert attrs["frozen"] == 0.0


def test_layer_is_inert_when_onoff_is_zero():
    """`onoff=0` must mean NOTHING happens — no burst, no learning."""
    w, us, bip = _world(onoff=0.0)
    before = weights(w, us).copy()
    _waves(w, 30)
    assert np.abs(weights(w, us) - before).max() == 0.0
    onb = [b for (r, c, p), b in bip.items() if p == 1]
    assert all(float(w.s.node(b)["attrs"]["bursting"]) == 0.0 for b in onb)


# --------------------------------------------------------------------------- #
#  THE FREEZE — the bug rung 5 found. A gate that has never failed isn't a gate.
# --------------------------------------------------------------------------- #
def test_oja_zero_is_NOT_a_freeze_which_is_why_the_real_freeze_exists():
    """THE DEFECT, PINNED. `bh_potentiate`/`bh_depress`/`bh_scale` are each gated
    on `WaveParams.oja == 0.0`, so setting oja=0 to "stop learning" switches the
    OTHER learning rule ON. This test FAILS on the defective freeze — i.e. it
    asserts the defect is real — and its counterpart passes on the fixed one."""
    w, us, _ = _world()
    _waves(w, 60)
    before = weights(w, us).copy()
    set_params(w, frozen=0.0)                      # NOT frozen ...
    for p in w.s.nodes("WaveParams"):
        w.s.set_attr(p, "oja", 0.0)                # ... and the trap is armed
    cell_stats(w, us, key="rate", period=PERIOD)
    moved = float(np.abs(weights(w, us) - before).max())
    assert moved > 0.0, (
        "if this ever stops moving, `oja=0` became a real freeze and this test "
        "should be retired — but as of rung 6 it is NOT one")


def test_the_real_freeze_is_exact():
    """The fix: `OnOffParams.frozen` gates EVERY learning rule in this seed, so
    a probe cannot train what it measures. Verified exact, not assumed."""
    w, us, _ = _world()
    _waves(w, 60)
    before = weights(w, us).copy()
    freeze(w)
    cell_stats(w, us, key="rate", period=PERIOD)
    assert np.abs(weights(w, us) - before).max() == 0.0


def test_the_real_freeze_also_freezes_the_threshold():
    """Adaptation IS plasticity. A probe that let theta chase the probe stimulus
    would be the instrument training itself — the same class of bug as
    `oja=0` is not a freeze."""
    w, us, _ = _world()
    _waves(w, 60)
    freeze(w)
    th = [float(w.s.node(u)["attrs"]["theta"]) for u in us]
    cell_stats(w, us, key="rate", period=PERIOD)
    assert [float(w.s.node(u)["attrs"]["theta"]) for u in us] == th


# --------------------------------------------------------------------------- #
#  THE RULES ACTUALLY FIRE — the silent failure mode (`vf_temporal_diff never
#  fired`), and the one that really bit this rung.
# --------------------------------------------------------------------------- #
def test_both_learning_rules_actually_fire():
    """REGRESSION. `oo_learn_oja` referenced an UNBOUND `r` in its `where`, so it
    never fired and the `subnorm=0` arm was silently "no learning at all"
    (max |dw| = 0.000000 at every eta) while looking like a result. A rule that
    cannot fire is a null arm, and a null arm passed off as a mechanism is worse
    than a failure."""
    for subnorm in (1.0, 0.0):
        w, us, _ = _world(subnorm=subnorm)
        before = weights(w, us).copy()
        _waves(w, 120)
        moved = float(np.abs(weights(w, us) - before).max())
        assert moved > 1e-6, f"subnorm={subnorm} learning rule never fired"


def test_the_split_drives_both_channels_from_one_wave_field():
    """ON and OFF must be COMPLEMENTARY reads of the SAME wave field: ON bursts
    where the retina burst, OFF where it did not. Segregation is an OUTCOME, so
    the waves themselves must never be hand-segregated."""
    w, us, bip = _world()
    _waves(w, 12)
    on = np.mean([float(w.s.node(b)["attrs"]["bursting"])
                  for (r, c, p), b in bip.items() if p == 1])
    off = np.mean([float(w.s.node(b)["attrs"]["bursting"])
                   for (r, c, p), b in bip.items() if p == -1])
    assert abs((on + off) - 1.0) < 1e-6, "ON/OFF must partition the same field"
    assert 0.0 < on < 1.0


def test_split_ablation_is_data_and_collapses_off_onto_on():
    """The control must differ from the arm in the SIGN and nothing else —
    identical anatomy, identical synapse count, identical rules (rung 4's lesson:
    an ablation that also removes anatomy is not null)."""
    wa, ua, ba = _world(split=1.0)
    wb, ub, bb = _world(split=0.0)
    assert len(ba) == len(bb)
    assert len(weights(wa, ua)) == len(weights(wb, ub))
    _waves(wa, 12)
    _waves(wb, 12)
    g = lambda w, b, p: np.mean([float(w.s.node(n)["attrs"]["bursting"])
                                 for (r, c, pol), n in b.items() if pol == p])
    assert abs(g(wb, bb, 1) - g(wb, bb, -1)) < 1e-9, "split=0 => OFF behaves as ON"
    assert abs(g(wa, ba, 1) - g(wa, ba, -1)) > 1e-6, "split=1 => OFF inverts"


# --------------------------------------------------------------------------- #
#  THE MEASURE (PROTOCOL 1) — calibrate on an ideal, a floor, and a duration
# --------------------------------------------------------------------------- #
def test_dale_holds_every_weight_stays_non_negative():
    """A neuron's synapses are sign-constant. The SIGN must come from the
    PATHWAY, never from a negative weight — that is the entire architecture."""
    w, us, _ = _world()
    _waves(w, 300)
    ws = weights(w, us)
    assert ws.min() >= 0.0, "Dale violated: a weight went negative"


def test_the_effective_rf_is_signed_even_though_every_weight_is_not():
    """The claim rung 5 showed was impossible without a split: frac(w<0)=0.0000
    yet the EFFECTIVE RF (w_ON - w_OFF) takes both signs."""
    w, us, _ = _world()
    _waves(w, 300)
    assert weights(w, us).min() >= 0.0
    d = signed_rf(w, us[0])
    assert (d > 0).any() and (d < 0).any(), "effective RF must be signed"


def test_ideal_split_gabor_scores_near_the_top_of_the_measure():
    """PROTOCOL 1: the measure must score an IDEAL exemplar high, through the
    identical frozen probe. This is the TARGET the SESOI is scaled from."""
    w, us, _ = _world(n_units=2)
    install_signed_rf(w, us[0], gabor(RF, 0.0, 0.0, period=PERIOD))
    install_signed_rf(w, us[1], gabor(RF, 90.0, 0.0, period=PERIOD))
    set_params(w, oo_eta=0.0)          # theta adapts; NO weight moves
    _waves(w, 400)
    freeze(w)
    st = cell_stats(w, us, key="rate", period=PERIOD)
    assert st["osi"].mean() > 0.75, f"ideal scored {st['osi'].mean():.4f}"


def test_WITHOUT_the_threshold_even_a_perfect_cell_reads_as_unoriented():
    """THE MEASURED REASON THE THRESHOLD IS IN THE MODEL, pinned.

    The OFF channel's tonic drive (SUM w- = 5.613) sits above the signal, so act
    never reaches 0 at any orientation, rectification never bites and F0 is flat.
    The split makes the FILTER signed; the THRESHOLD is what makes the RESPONSE
    signed. Without it, an ideal split-Gabor scores ~0.0006."""
    w, us, _ = _world(n_units=2)
    install_signed_rf(w, us[0], gabor(RF, 0.0, 0.0, period=PERIOD))
    install_signed_rf(w, us[1], gabor(RF, 90.0, 0.0, period=PERIOD))
    set_params(w, homeo=0.0)           # theta pinned at 0 => no iceberg
    freeze(w)
    st = cell_stats(w, us, key="rate", period=PERIOD)
    assert st["osi"].mean() < 0.05, (
        f"the no-threshold cell scored {st['osi'].mean():.4f}; if this ever "
        "rises, the tonic-drive diagnosis has changed and the rung's rationale "
        "must be re-derived")


def test_the_probe_is_repeatable_under_the_real_freeze():
    """The duration confound, at its root: a FROZEN probe must return the same
    number twice. Anisotropy failed exactly this for nine attempts."""
    w, us, _ = _world()
    _waves(w, 200)
    freeze(w)
    a = cell_stats(w, us, key="rate", period=PERIOD)["osi"]
    b = cell_stats(w, us, key="rate", period=PERIOD)["osi"]
    assert np.allclose(a, b)


def test_the_untrained_floor_is_high_and_is_stated_not_assumed_zero():
    """PROTOCOL 1 + rung 3's lesson ('the floor is 0.103, not 0 — ">0" was never
    evidence'). With a WORKING response pathway a RANDOM RF has genuine chance
    orientation structure, so the untrained floor is ~0.32, NOT ~0. Any claim
    must clear THIS, and the pre-registered design is an INTERACTION for exactly
    this reason (PROTOCOL 4: test the interaction when the control is non-null).
    """
    osis = []
    for sd in (0, 1, 2):
        w, us, _ = _world(seed=sd, n_units=6)
        set_params(w, oo_eta=0.0)      # theta adapts; NO weight moves
        _waves(w, 400)
        freeze(w)
        osis.append(cell_stats(w, us, key="rate", period=PERIOD)["osi"].mean())
    assert 0.15 < float(np.mean(osis)) < 0.55, (
        f"untrained floor {np.mean(osis):.4f} moved; the SESOI is scaled off "
        "this and every arm comparison depends on it")


# --------------------------------------------------------------------------- #
#  THE MECHANISM IS NOT A NULL INSTRUMENT (PROTOCOL 1's positive control)
# --------------------------------------------------------------------------- #
@pytest.mark.slow
def test_positive_control_a_biased_ensemble_grows_the_shown_orientation():
    """Given a PERFECTLY BIASED ensemble (one orientation, ever), the rule must
    grow a cell that prefers THAT orientation. Rung 3's eta was a null instrument
    and only its positive control revealed it.

    This is a POSITIVE CONTROL, NOT AN ARM: the stimulus is hand-built and is
    exactly what the paradigm rule forbids handing the agent."""
    rng = np.random.default_rng(0)
    w, us, _ = _world(n_units=6)
    set_params(w, oo_eta=0.0)
    _waves(w, 400)                     # settle theta first
    set_params(w, oo_eta=5e-4)
    for _ in range(1500):
        present(w, binarize(grating((H, W), 0.0, float(rng.uniform(0, 2*np.pi)),
                                    PERIOD)))
    freeze(w)
    st = cell_stats(w, us, key="rate", period=PERIOD)
    assert st["osi"].mean() > 0.6, f"OSI {st['osi'].mean():.4f} — null instrument?"
    # CONJUNCTIVE (PROTOCOL 4): a mechanism must not pass by making itself inert.
    pk = st["tuning"].max(axis=1)
    bs = np.maximum(st["baseline"], 1e-9)
    assert float((pk / bs).mean()) > 5.0, "selective but silent is not a cell"
    # and it must prefer the orientation it was actually SHOWN (bin 0 == 0 deg)
    prefs = [int(np.argmax(st["tuning"][i])) for i in range(len(us))]
    assert sum(p == 0 for p in prefs) >= 4, f"prefs {prefs} — not what was shown"


# --------------------------------------------------------------------------- #
#  PROTOCOL 8 — pin what is NOT claimed
# --------------------------------------------------------------------------- #
@pytest.mark.slow
def test_THE_NEGATIVE_waves_do_not_develop_orientation_and_this_is_pinned():
    """THE RUNG'S ACTUAL RESULT, PINNED (PROTOCOL 8).

    The mechanism is CAPABLE (the positive control grows the shown orientation
    from a biased ensemble, OSI 0.878, peak/base 20.6, clumpiness 0.718). But on
    the FORMATIVE input — the agent's own waves — it produces NOTHING above the
    untrained floor: OSI stays ~0.32 (floor 0.3168) and the cells never become
    responsive (peak/base ~1.5 against the ideal's 6.44).

    Convergence measured this out to 6400 steps: at eta=5e-4 the rule RUNS AWAY
    (drift 0.004 -> 0.461, clumpiness -> 0.85) and at eta=1e-4 it is stable but
    empty (OSI 0.283 -> 0.329, i.e. the floor). Both of PROTOCOL 2's stop
    conditions at once, which is why NO confirmatory arm was run and seeds
    8000-8999 remain clean.

    If this test ever starts FAILING because OSI rose, that is a real result and
    needs its own prospective pre-registration — not a quiet edit here."""
    w, us, _ = _world(seed=7, n_units=6, eta=1e-4)
    set_params(w, oo_eta=0.0)
    _waves(w, 400)                      # theta settles
    set_params(w, oo_eta=1e-4)
    _waves(w, 1600)
    freeze(w)
    st = cell_stats(w, us, key="rate", period=PERIOD)
    pk = st["tuning"].max(axis=1)
    bs = np.maximum(st["baseline"], 1e-9)
    assert st["osi"].mean() < 0.55, (
        f"OSI {st['osi'].mean():.4f} rose above the floor band — if real, this "
        "needs its own pre-registration (PROTOCOL 5)")
    assert float((pk / bs).mean()) < 3.0, (
        "the wave-trained cells became responsive — that would be a NEW result")


def test_no_python_decides_anything_the_ablations_are_graph_data():
    """PROTOCOL 0 / CLAUDE.md: every ablation is the agent's own configuration,
    never a fork in the host."""
    src = open(os.path.join(ROOT, "domains", "onoff_world.py")).read()
    for tok in ("if split", "if subnorm", "if frozen", "if onoff"):
        assert tok not in src, f"{tok!r} — an ablation became a Python branch"
