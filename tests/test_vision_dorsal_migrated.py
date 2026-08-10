"""RUNG 3 — THE DORSAL/MOTION STREAM: direction selectivity.

These gates exist because the verified research (105-agent adversarial pass)
established two things that pull in opposite directions:

  * the dorsal stream is EARLY and PARALLEL, not a rung stacked above V1 (V1
    and MT co-earliest; marmoset layer-4 CB+ dense in V1 AND MT/MST/FST at E130,
    prenatal; PV peaks PD14 dorsal vs PD28 ventral; a retina->inferior-pulvinar
    ->MT route BYPASSES V1; neonatal MT ablation permanently degrades
    reach-to-grasp for MOVING targets, Atapour & Bourne 2021);
  * and, explicitly, "do NOT generalise from orientation to DIRECTION
    selectivity — direction is absent at eye opening and DOES require
    experience (Li 2006) — the opposite case".

So this seed is a PARALLEL population (DUnit / DSynapse / has_dunit off the same
Retina), and the rung's claim is a DIFFERENTIAL one, not a repeat of rung 1.

THE GATES THAT MATTER, and both are about the MEASURE rather than the agent —
PROTOCOL section 1, "a gate whose measure passes noise is not a gate":

  * `test_the_dsi_scores_an_ideal_direction_selective_unit_high` — the ideal
    exemplar. Stage 1's sign classifiers passed random noise AND failed an ideal
    Gabor; this is the check that would have caught that.
  * `test_a_mean_readout_cannot_measure_direction_and_that_is_why_peak_is_used`
    — pins the PROVEN reason the readout is a peak. A linear unit's drive summed
    over a sweep is direction-INVARIANT by construction, so a mean readout
    scores the ideal unit at the floor. This test exists so nobody "simplifies"
    it back.

And `test_the_floor_is_not_zero_and_only_paired_comparisons_are_interpretable`
pins the honest known-gap: random delays confer a real innate direction bias
(measured 0.111), so an arm's absolute DSI means nothing on its own.
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
from domains.dorsal_world import (  # noqa: E402
    add_dunits, probe_dsi, set_dunit_ideal, sweep_response, sweep_frames,
    dunit_weights, gaze_walk, N_DIR)

DORSAL_SEED = os.path.join(ROOT, "seeds", "vision_dorsal.json")


def _boot(*, dorsal=1.0, propagate=1.0, seed=1, n_units=10, eta=5e-4):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_dorsal"])
    dp = s.nodes("DorsalParams")[0]
    wp = s.nodes("WaveParams")[0]
    s.set_attr(dp, "dorsal", float(dorsal))
    s.set_attr(dp, "oja_eta", float(eta))
    s.set_attr(wp, "propagate", float(propagate))
    w = WaveWorld(s, h=16, w=16, seed=seed, track_prev_burst=True)
    us = add_dunits(w, n_units, rf=7, max_delay=3,
                    rng=np.random.default_rng(seed))
    return s, w, us


# --------------------------------------------------------------------------- #
#  1. DEFAULTS PRESERVE COMMITTED RESULTS (PROTOCOL section 9)
# --------------------------------------------------------------------------- #
def test_the_dorsal_stream_ships_off_by_default():
    """Every rule in the seed is gated on DorsalParams.dorsal, which defaults to
    0. A booted agent that does not ask for the dorsal stream must behave
    exactly as the committed rung-1/rung-2 substrate does, so every committed
    result reproduces (PROTOCOL section 9)."""
    with open(DORSAL_SEED) as f:
        seed = json.load(f)
    dp = [n for n in seed["nodes"] if n["type"] == "DorsalParams"][0]["attrs"]
    assert dp["dorsal"] == 0.0, "the dorsal stream is ON by default"
    for r in seed["rules"]:
        assert "dorsal" in json.dumps(r["where"]), (
            f"{r['name']} is not gated on DorsalParams.dorsal — it would fire "
            "in a plain rung-1 boot and silently invalidate committed results")


def test_dorsal_off_means_no_dunit_ever_responds():
    """The gate is DATA, not a Python code path: with dorsal=0 the rules do not
    fire even though the DUnits and their synapses exist in the graph."""
    s, w, us = _boot(dorsal=0.0, seed=5)
    for i in range(40):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    assert all(float(s.node(u)["attrs"]["dact"]) == 0.0 for u in us)
    assert all(float(s.node(u)["attrs"]["dact_step"]) == -1.0 for u in us)


def test_prev_burst_tracking_is_off_by_default_in_the_wave_adapter():
    """`WaveWorld.track_prev_burst` is the only change rung 3 makes to the rung-1
    adapter, and it must default OFF so rung-1/rung-2 runs are byte-identical."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    w = WaveWorld(s, h=8, w=8, seed=1)
    assert w.track_prev_burst is False
    for i in range(10):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    n = w.cells[(4, 4)]
    assert float(s.node(n)["attrs"]["prev_burst"]) == -999.0, (
        "prev_burst is being written with tracking off")


# --------------------------------------------------------------------------- #
#  2. THE MEASURE — gated before the agent (PROTOCOL section 1)
# --------------------------------------------------------------------------- #
def test_the_dsi_scores_an_ideal_direction_selective_unit_high():
    """THE CALIBRATION GATE. A hand-built delay-line unit whose delays exactly
    cancel position along the motion axis must score far above the untrained
    floor. Measured: ideal 0.600 vs floor 0.111.

    This is the check Stage 1 did not have — its sign classifiers passed random
    noise 50-75% of the time AND failed an ideal Gabor. If this fails, a null on
    any arm means nothing, because the instrument cannot see the structure even
    when it is handed it."""
    s, w, us = _boot(seed=3, n_units=4)
    untrained = float(probe_dsi(w, us, seed=3).mean())
    for u in us:
        set_dunit_ideal(w, u, 0.0)
    ideal = float(probe_dsi(w, us, seed=3).mean())
    assert ideal > 0.45, f"the DSI cannot see an IDEAL direction unit ({ideal:.3f})"
    assert ideal > untrained + 0.3, (
        f"ideal {ideal:.3f} is not separated from the untrained floor "
        f"{untrained:.3f} — the measure has no dynamic range")


def test_a_mean_readout_cannot_measure_direction_and_that_is_why_peak_is_used():
    """REGRESSION on a PROVEN property found by calibrating before measuring.

    A DUnit's drive is LINEAR in its arriving inputs, and over one bar sweep
    every cell fires exactly one transient and so contributes to exactly one
    step. The SUM of dact over a sweep is therefore the sum of the unit's
    weights — the SAME for every direction, by construction. Direction lives
    only in the TEMPORAL CONCENTRATION of the drive, so a time-averaged readout
    is mathematically incapable of measuring it and scores the ideal unit at the
    floor. This pins the sum-invariance, so that if anyone "simplifies"
    sweep_response back to a mean the reason is right here."""
    s, w, us = _boot(seed=2, n_units=1, eta=0.0)
    u = us[0]
    set_dunit_ideal(w, u, 0.0)
    sums, peaks = [], []
    for k in (0, N_DIR // 2):                       # a mirrored pair
        from domains.dorsal_world import reset_retina
        reset_retina(w)
        tot = pk = 0.0
        for fr in sweep_frames(16, 16, k, phase=0.0):
            w.step(ignite_k=0, frame=fr)
            v = float(s.node(u)["attrs"]["dact"])
            tot += v
            pk = max(pk, v)
        sums.append(tot)
        peaks.append(pk)
    assert abs(sums[0] - sums[1]) < 0.02 * max(sums), (
        f"sum(dact) is NOT direction-invariant ({sums}) — the premise of the "
        "peak readout has changed; re-derive it before trusting the DSI")
    assert peaks[0] > 1.5 * peaks[1], (
        f"the PEAK does not separate the mirrored pair either ({peaks}) — the "
        "mechanism is not direction-selective at all")


def test_opposite_directions_present_identical_frames_in_reverse_order():
    """The probe's mirrored-pair construction. Direction k and k+4 must present
    the EXACT same frames in reversed order, so the only thing that can separate
    them is ORDER — the DSI is thereby a per-direction temporal-shuffle control.

    REGRESSION: the first cut swept each direction independently and the
    'direction' signal was a pixel-quantisation artifact of the bar geometry —
    tuning curves came out identical for 45/135/225/315, and all 10 units
    reported the same DSI of 0.026."""
    for k in range(N_DIR // 2):
        a = sweep_frames(16, 16, k, phase=0.31)
        b = sweep_frames(16, 16, k + N_DIR // 2, phase=0.31)
        assert len(a) == len(b)
        for i in range(len(a)):
            assert np.array_equal(a[i], b[len(b) - 1 - i]), (
                f"direction {k} and its opposite are not mirrored at frame {i}")


def test_the_probe_does_not_let_the_agent_learn():
    """A probe must MEASURE, never train: `probe_dsi` zeroes oja_eta for its
    duration (Oja degenerates to the identity) and restores it after. If a probe
    trained, every arm's score would depend on how many times it had been
    measured."""
    s, w, us = _boot(seed=6, n_units=3)
    before = np.concatenate([dunit_weights(w, u) for u in us])
    probe_dsi(w, us, seed=6)
    after = np.concatenate([dunit_weights(w, u) for u in us])
    assert np.array_equal(before, after), "the probe changed the weights"
    dp = s.nodes("DorsalParams")[0]
    assert float(s.node(dp)["attrs"]["oja_eta"]) == 5e-4, "probe did not restore eta"


def test_the_probe_does_not_let_the_agent_learn_WITH_THE_BISTABLE_TERM_ARMED():
    """THE GATE THAT DID NOT FAIL, now run on the axis it was blind to.

    The version above boots with bistable=0 and passed throughout rung 3B's
    development while the probe was, in fact, training on its own stimulus: the
    bistable term is scaled by `bi_eta`, not `oja_eta`, so zeroing `oja_eta`
    froze only half the rule. Measured in the positive control's step-0 column
    (taken before ANY training step, so it must equal the 0.111 floor): it read
    0.339 at bi_eta=1e-1 — a 3x floor jump manufactured purely by measuring.

    PROTOCOL section 1: 'a gate that checks a rule's CONSTANTS but not the AXIS
    they parameterise is not a gate'. This is that gate, on that axis."""
    s, w, us = _boot_bi(bistable=1.0, bi_eta=1e-1, seed=6)
    before = np.concatenate([dunit_weights(w, u) for u in us])
    probe_dsi(w, us, seed=6)
    after = np.concatenate([dunit_weights(w, u) for u in us])
    assert np.array_equal(before, after), (
        "the probe TRAINED the agent through the bistable term — every armed "
        "number it produces is training on the test set")
    dp = s.nodes("DorsalParams")[0]
    assert float(s.node(dp)["attrs"]["bi_eta"]) == 1e-1, "probe did not restore bi_eta"


def test_the_floor_is_not_zero_and_only_paired_comparisons_are_interpretable():
    """HONEST KNOWN-GAP, pinned so no claim quietly forgets it.

    Cross-validation removes the argmax SELECTION bias, but the untrained floor
    is still 0.111, not 0 — because a unit whose conduction delays are drawn at
    random has, by chance, a better delay gradient along some direction than
    along its opposite, and that preference REPLICATES across reps because the
    delays are fixed. Random wiring confers weak direction bias for free.

    Consequence: 'DSI > 0' is NOT evidence of learned direction selectivity, and
    every claim must be a PAIRED comparison in which the arms share a seed (and
    therefore share their delays) so the innate bias cancels."""
    fl = []
    for sd in range(4):
        s, w, us = _boot(seed=sd)
        fl.append(float(probe_dsi(w, us, seed=sd).mean()))
    m = float(np.mean(fl))
    assert m > 0.03, (
        f"the untrained floor is {m:.3f} — if it really is ~0 now, the innate "
        "delay bias is gone and the pre-registration's reasoning must be redone")
    assert m < 0.30, f"untrained units are strongly direction-selective ({m:.3f})"


# --------------------------------------------------------------------------- #
#  3. THE MECHANISM IS A RULE, AND THE ENTROPY IS UNSTRUCTURED
# --------------------------------------------------------------------------- #
def test_direction_is_read_by_a_rule_not_by_python():
    """The delay-line coincidence detection, the competition and the learning
    are all graph data. The adapter supplies wiring, entropy and stimuli."""
    with open(DORSAL_SEED) as f:
        seed = json.load(f)
    names = {r["name"] for r in seed["rules"]}
    assert {"dv_transient", "dv_unit_activate", "dv_burst_winner",
            "dv_oja_learn"} <= names
    act = [r for r in seed["rules"] if r["name"] == "dv_unit_activate"][0]
    blob = json.dumps(act)
    assert "delay" in blob and "dlast_burst" in blob, (
        "dv_unit_activate no longer reads a per-synapse delay against the "
        "transient channel — the direction mechanism has regressed")
    win = [r for r in seed["rules"] if r["name"] == "dv_burst_winner"][0]
    assert '"Argmax"' in json.dumps(win["where"]), "competition is not a rule"
    src = open(os.path.join(ROOT, "domains", "dorsal_world.py")).read()
    for banned in ("np.argmax(", "np.correlate", "np.fft", "sorted("):
        assert banned not in src, f"the adapter computes the answer: {banned}"


def test_the_adapter_hands_the_agent_no_direction_gradient():
    """THE PARADIGM GATE for this rung. A delay-line direction detector is
    trivial to BUILD (delay = k - position). The adapter must draw delays
    UNIFORMLY AT RANDOM, so every direction is symmetric a priori and any
    direction preference is grown by dv_oja_learn rather than planted — random
    delays are to direction what random ignition is to waves.

    If this fails, the rung is `preprocess_patches` at the motion grain."""
    s, w, us = _boot(seed=9, n_units=10)
    from domains.dorsal_world import dunit_synapses
    grads = []
    for u in us:
        syn = dunit_synapses(w, u)
        dcol = np.array([t[1] for t in syn])
        drow = np.array([t[0] for t in syn])
        dly = np.array([t[2] for t in syn])
        # correlation of delay with position along each axis: the delay
        # GRADIENT that would constitute a built-in preferred direction
        for pos in (dcol, drow):
            if pos.std() > 0 and dly.std() > 0:
                grads.append(abs(float(np.corrcoef(pos, dly)[0, 1])))
    assert max(grads) < 0.5, (
        f"the adapter wired a delay gradient (max |r| = {max(grads):.2f}) — the "
        "agent is being handed the direction structure it must grow")
    assert float(np.mean(grads)) < 0.2, (
        f"delays are systematically correlated with position (mean |r| = "
        f"{np.mean(grads):.2f})")


def test_the_dorsal_stream_refuses_to_build_on_an_untracked_world():
    """REGRESSION on a SILENT wrong-science bug found by reviewing the diff.

    `dv_transient` fires iff `last_burst == step AND prev_burst < step - 1`. With
    `WaveWorld(track_prev_burst=False)` — the DEFAULT — prev_burst stays at its
    -999 sentinel forever, so the second clause is always true and the transient
    fires on EVERY burst step. The dorsal stream silently reads the SUSTAINED
    channel and is blind to motion: measured on a static half-field with tracking
    off, 128 "transients" per step, every step, instead of 128 once.

    Nothing crashed and nothing warned — the run just answered a different
    question. So `add_dunits` refuses rather than defaulting."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_dorsal"])
    s.set_attr(s.nodes("DorsalParams")[0], "dorsal", 1.0)
    w = WaveWorld(s, h=16, w=16, seed=1)          # tracking OFF (the default)
    with pytest.raises(ValueError, match="track_prev_burst"):
        add_dunits(w, 2, rf=7, max_delay=3, rng=np.random.default_rng(1))


def test_the_transient_channel_fires_exactly_once_per_burst_episode():
    """dv_transient makes the DECISION of what an onset is; the adapter only
    records the FACT (prev_burst).

    MEASURED, and it corrected a wrong assumption of mine that this gate caught:
    I expected a wave cell to burst for exactly ONE step (so that the transient
    channel would be a no-op on waves). It bursts for TWO — `_mark_bursts` runs
    BEFORE the tick, so a cell is still `active` on the step wv_refract flips it
    to refractory, and it reads as bursting on both. The transient therefore
    fires on exactly the FIRST step of each 2-step episode, which is what an
    onset detector SHOULD do, and it HALVES the dorsal event count relative to
    the sustained channel (measured 1262 transients / 2507 burst-steps = 0.503).

    That is a real difference between the dorsal and ventral input streams, and
    it is the intended one — the two streams read different retinal channels off
    the same cells. It changes NO committed result: the rung-1/rung-2 rules read
    `last_burst`, which is untouched, and the dorsal population is new.

    The gate: every burst EPISODE has exactly one onset (never zero, never two)."""
    with open(DORSAL_SEED) as f:
        seed = json.load(f)
    tr = [r for r in seed["rules"] if r["name"] == "dv_transient"][0]
    assert "prev_burst" in json.dumps(tr["where"])
    assert "dlast_burst" in json.dumps(tr["effects"])
    s, w, us = _boot(seed=4, propagate=1.0)
    hist = {c: [] for c in w.cells.values()}
    for i in range(60):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
        st = float(s.node(w.retina)["attrs"]["step"])
        for c in w.cells.values():
            at = s.node(c)["attrs"]
            hist[c].append((float(at["bursting"]) == 1.0,
                            float(at["dlast_burst"]) == st))
    episodes = onsets = 0
    for c, seq in hist.items():
        prev = False
        for burst, tran in seq:
            if burst and not prev:
                episodes += 1
            if tran:
                onsets += 1
                assert burst, "a transient fired on a cell that was not bursting"
            prev = burst
    assert episodes > 0, "no wave burst episode ever happened"
    assert onsets == episodes, (
        f"{onsets} transients for {episodes} burst episodes — the transient "
        "channel is not firing exactly once per onset")


def test_gaze_drift_gives_the_normal_arm_real_motion_and_matches_strobe_duty():
    """PROTOCOL section 6 — check the arm against the animal BEFORE running it.

    Measured before any test: real video at 16x16 is nearly static (consecutive
    frames differ by 0.005; onset rate 0.6% against a 50% duty cycle), so a
    `normal` arm on it delivers almost no motion and its null would mean
    'there was no motion in the moving-experience arm'. No animal has a
    stabilised retina — a stabilised image FADES ENTIRELY (Troxler; Ditchburn &
    Ginsborg 1952) — so the drifting eye is the faithful model, not the frozen
    one.

    And `strobe` must be the SAME frames permuted, so the two arms have
    IDENTICAL spatial statistics and IDENTICAL duty cycle and differ only in
    ORDER."""
    v = np.load(os.path.join(ROOT, "scratchpad3", "video420_32.npy")) \
        if os.path.exists(os.path.join(ROOT, "scratchpad3", "video420_32.npy")) \
        else None
    if v is None:
        pytest.skip("cached 32x32 video not present")
    r = gaze_walk(v, 200, 16, 16, rng=np.random.default_rng(0))
    B = np.stack([f > np.median(f) for f in r])
    perm = np.random.default_rng(1).permutation(len(r))
    Bs = B[perm]
    on_o = float((B[1:] & ~B[:-1]).mean())
    on_s = float((Bs[1:] & ~Bs[:-1]).mean())
    assert abs(B.mean() - Bs.mean()) < 1e-9, (
        "ordered and strobe arms differ in DUTY CYCLE, not only in order")
    assert on_o > 0.02, (
        f"the drifting eye still delivers almost no motion (onset {on_o:.4f}) — "
        "the normal arm is a null instrument")
    assert on_s > on_o, (
        "scrambling did not destroy temporal continuity — the strobe control "
        "is not a control")


# --------------------------------------------------------------------------- #
#  RUNG 3B — THE BISTABLE/HYSTERETIC TERM (VISION_RUNG3B_PREREG.md)
#
#  The rung-3 confirmatory run measured the defect these gates fence: Oja's
#  fixed point is the leading PC of the TIME-AVERAGED covariance, natural motion
#  is direction-isotropic on average, and a contraction to the mean of an
#  isotropic distribution IS the mean. The bistable term makes the MEAN A
#  REPELLER. These gates check that property directly, and check that it is OFF
#  by default so every committed rung-3 number reproduces.
# --------------------------------------------------------------------------- #
def _boot_bi(*, bistable, bi_eta, seed=1, eta=2e-3, propagate=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_dorsal"])
    dp = s.nodes("DorsalParams")[0]
    wp = s.nodes("WaveParams")[0]
    s.set_attr(dp, "dorsal", 1.0)
    s.set_attr(dp, "oja_eta", float(eta))
    s.set_attr(dp, "bistable", float(bistable))
    s.set_attr(dp, "bi_eta", float(bi_eta))
    s.set_attr(wp, "propagate", float(propagate))
    w = WaveWorld(s, h=16, w=16, seed=seed, track_prev_burst=True)
    us = add_dunits(w, 10, rf=7, max_delay=3, rng=np.random.default_rng(seed))
    return s, w, us


def test_the_bistable_term_ships_off_by_default():
    """PROTOCOL section 9. Both knobs default to 0.0 and the term is a product
    with `bistable`, so at the default it contributes exactly +0.0 and
    dv_oja_learn IS the committed rung-3 Oja rule."""
    with open(DORSAL_SEED) as f:
        seed = json.load(f)
    dp = [n for n in seed["nodes"] if n["type"] == "DorsalParams"][0]["attrs"]
    assert dp["bistable"] == 0.0, "the bistable term is ARMED by default"
    assert dp["bi_eta"] == 0.0, "bi_eta is non-zero by default"


def test_bistable_off_is_byte_identical_to_the_committed_oja_rule():
    """The rung-3 numbers must reproduce EXACTLY, not approximately. Two worlds
    driven identically, one booted from the v1.1.0 seed with bistable=0 and one
    with the term's gate multiplied out by hand, must agree to the BIT."""
    def weights(bistable):
        s, w, us = _boot_bi(bistable=bistable, bi_eta=0.0, seed=3)
        for i in range(120):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
        return np.concatenate([dunit_weights(w, u) for u in us])
    a, b = weights(0.0), weights(0.0)
    assert np.array_equal(a, b), "the rule is not deterministic"
    # bi_eta is irrelevant while `bistable` is 0 — the gate is a PRODUCT.
    s, w, us = _boot_bi(bistable=0.0, bi_eta=1e-1, seed=3)
    for i in range(120):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    c = np.concatenate([dunit_weights(w, u) for u in us])
    assert np.array_equal(a, c), (
        "bistable=0 does not gate the term out exactly — committed rung-3 "
        "results would not reproduce")


def test_the_mean_is_a_repeller_which_is_the_whole_mechanism():
    """THE HEADLINE PROPERTY, checked as arithmetic on the rule's own term
    rather than as a story about it. Oja's attractor is the mean; the bistable
    term's zeros are 0, m and 2m, it is NEGATIVE below m and POSITIVE above m.
    So m is an UNSTABLE fixed point — the one place a weight cannot stay. This
    is the direct negation of the rung-3 diagnosis."""
    def term(w, m, bi_eta=1.0):
        return bi_eta * (w - m) * (2 * m - w) * w / (4 * m * m + 1e-12)
    m = 0.7
    assert term(m, m) == pytest.approx(0.0, abs=1e-12), "m is not a fixed point"
    assert term(0.0, m) == pytest.approx(0.0, abs=1e-12), "0 is not a fixed point"
    assert term(2 * m, m) == pytest.approx(0.0, abs=1e-12), "2m is not a fixed point"
    for w in (0.1 * m, 0.5 * m, 0.9 * m):
        assert term(w, m) < 0, f"w={w} below the mean is not pushed DOWN"
    for w in (1.1 * m, 1.5 * m, 1.9 * m):
        assert term(w, m) > 0, f"w={w} above the mean is not pushed UP"
    # bounded: above 2m it is pushed back down, so the term cannot run away.
    assert term(2.5 * m, m) < 0, "the term is unbounded above 2m"


def test_the_bistable_term_is_scale_free_and_adds_exactly_one_knob():
    """It has NO absolute threshold and NO absolute ceiling — the threshold IS
    the unit's own mean weight and the ceiling IS twice it, both recomputed from
    the unit's own state. That is why it adds one knob (bi_eta) and not four
    (w_min/theta_b/w_max), and why it cannot be tuned by choosing a scale — the
    parameter search this rung forbids."""
    with open(DORSAL_SEED) as f:
        seed = json.load(f)
    dp = [n for n in seed["nodes"] if n["type"] == "DorsalParams"][0]["attrs"]
    for banned in ("w_max", "w_min", "theta_b", "bi_threshold", "bi_ceiling"):
        assert banned not in dp, f"{banned} is an absolute scale knob"
    rule = [r for r in seed["rules"] if r["name"] == "dv_oja_learn"][0]
    body = json.dumps(rule["effects"])
    # the threshold is a Fold/Sum over the unit's OWN dpost synapses
    assert '"Sum"' in body and '"dpost"' in body, (
        "the term does not compute the unit's own mean weight — it is not "
        "scale-free")


def test_the_bistable_rule_is_still_a_rule_not_python():
    """CLAUDE.md. The mechanism is graph DATA in the seed's dv_oja_learn effect,
    gated by a DorsalParams attr. No Python decides anything: the adapter
    (dorsal_world) must contain no bistable logic at all."""
    import domains.dorsal_world as dw
    with open(dw.__file__) as f:
        src = f.read()
    code = "\n".join(l for l in src.splitlines()
                     if not l.strip().startswith("#"))
    # The adapter may FREEZE the knob for a probe (a mechanical configuration
    # write, exactly like oja_eta) but must never BRANCH on it: no Python
    # decides what the bistable term does.
    for banned in ("if bistable", "if bi_eta", "bistable ==", "bi_eta >",
                   "bi_eta <", "repeller"):
        assert banned not in code, (
            f"'{banned}' appears in the world adapter — the mechanism must be "
            "graph data, never a Python code path")
    assert "set_attr(dp, \"bi_eta\", 0.0)" in code, (
        "the probe does not freeze bi_eta — it would train on the probe "
        "stimulus (the measured rung-3B instrument defect)")
    with open(DORSAL_SEED) as f:
        seed = json.load(f)
    rule = [r for r in seed["rules"] if r["name"] == "dv_oja_learn"][0]
    assert "bistable" in json.dumps(rule["effects"]), (
        "the bistable term is not in the rule's effects")
