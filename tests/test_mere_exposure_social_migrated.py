"""BLOCK 293000 -- MERE-EXPOSURE x INITIAL-VALENCE gate. The LIKING is the graph's
own discrete 3-state regard Concept (the marginal <sigma> relaxed by
can_native_update_3state under run_rules()), PRODUCED by the CAN belief-update
primitive concept_apply_evidence inside record_hate_incident -- NOT Python. This
file gates the Zajonc mere-exposure x initial-valence INTERACTION expressed as
CROSSING LATENCY: a NEUTRAL prior crosses to regard>0 FAST, every NEGATIVE prior
resists (strictly greater, CI-separated latency), up to never-within-budget; the
felt-quality (dynamical:valence) TRACKS the produced state at every step (the
qualia coupling); the crystallized-negative is a DELAY not a permanent identity
lock (identity_field stays 0 via the confirmed API); the effect depends on the
belief update (ablation falsifier); the produced grid EQUALS the analytic oracle
EXACTLY; and no new seed auto-loads (byte-identity when absent)."""
import hashlib
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.mere_exposure_world import (                       # noqa: E402
    MereExposureWorld, predicted_crossing_latency,
    DEFAULT_ALPHA, CROSS_THRESHOLD)

CANON_MD5 = "7efe75eba05b006cafd15dbb4b7da246"   # canonical .so after native-only CAN cutover

BUDGET = 30
N = 60
BLOCK = 293000

# The pre-registered conditions (SS3 recipes); the two deeper crystallized recipes
# exercise the depth-scaled-latency -> never-crosses boundary.
CONDITIONS = {
    "neutral":            "neutral",
    "negative_noncryst":  "negative_noncryst",
    "negative_cryst_mid": "negative_cryst",
    "negative_cryst_deep": [dict(alpha=0.6)] * 12,
    "negative_cryst_verydeep": [dict(alpha=0.6)] * 15,
}
GRID_COLS = [1, 2, 4, 5, 12, 26, 30]
JITTER_ALPHAS = {"warm": [0.5, 0.6, 0.7], "default": [0.25, 0.3, 0.35],
                 "hostile": [0.12, 0.15, 0.18]}


def _qual_sign(state):
    return None if state == 0 else (1 if state > 0 else -1)


def _oracle_state(ext0, n):
    ext = ext0 + DEFAULT_ALPHA * n
    return 1 if ext > CROSS_THRESHOLD else (-1 if ext < -CROSS_THRESHOLD else 0)


def _run(recipe, *, alpha=DEFAULT_ALPHA, budget=BUDGET):
    w = MereExposureWorld(alpha=alpha)
    seeded = w.seed_initial_valence(recipe)
    tr = w.exposure_trajectory(budget=budget)
    return seeded, tr


def _boot_ci(xs, reps=2000, seed=BLOCK):
    xs = np.asarray(xs, float)
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def _latency_cohort(recipe, band, rng):
    alphas = JITTER_ALPHAS[band]
    lat = []
    for _ in range(N):
        a = float(rng.choice(alphas))
        w = MereExposureWorld(alpha=a)
        w.seed_initial_valence(recipe)
        tr = w.exposure_trajectory(budget=BUDGET)
        lat.append(float(tr["crossing_latency"]) if tr["crossed"] else float(BUDGET + 1))
    return lat


# ------------------------------------------------------------------- (a) grid==oracle
def test_produced_regard_and_qualia_grid_equals_oracle_exactly():
    """PRODUCED-not-hand-set: the graph's produced regard-state SIGN and qualia
    valence equal the analytic crossing-latency oracle at EVERY (condition, n) cell,
    and the produced crossing latency equals the oracle -- the dynamics PRODUCE the
    pre-registered crossings, they are not written by the test."""
    for cname, recipe in CONDITIONS.items():
        seeded, tr = _run(recipe)
        ext0 = seeded["regard_external_field"]
        for n in GRID_COLS:
            cell = tr["trajectory"][n - 1]
            ostate = _oracle_state(ext0, n)
            assert cell["state"] == ostate, (cname, n, cell, ostate)
            assert cell["qval"] == _qual_sign(ostate), (cname, n, cell)
        assert tr["crossing_latency"] == predicted_crossing_latency(ext0, budget=BUDGET), \
            (cname, tr["crossing_latency"])


# ------------------------------------------------------------ (b) interaction as latency
def test_interaction_neutral_crosses_first_negatives_strictly_later_ci_separated():
    """The INTERACTION (not a main effect): the NEUTRAL prior crosses to regard>0 in
    the FEWEST encounters (2 at alpha=0.3), while every NEGATIVE condition has a
    STRICTLY GREATER crossing latency, CI-separated ABOVE neutral (jittered-alpha
    cohort). Initial valence sets HOW MANY exposures liking takes."""
    # neutral crosses immediately-fast (the boundary as latency, at 2 for alpha=0.3)
    seeded_n, tr_n = _run("neutral")
    assert tr_n["crossing_latency"] == 2, tr_n["crossing_latency"]

    rng = np.random.default_rng(BLOCK)
    neutral_ci = _boot_ci(_latency_cohort("neutral", "default", rng))
    for cname, recipe in CONDITIONS.items():
        if cname == "neutral":
            continue
        neg_ci = _boot_ci(_latency_cohort(recipe, "default", rng))
        assert neg_ci[0] > neutral_ci[1], (cname, neutral_ci, neg_ci)  # separated ABOVE

    # deterministic monotone in prior depth, up to never-within-budget
    det = {c: _run(r)[1]["crossing_latency"] for c, r in CONDITIONS.items()}
    order = ["neutral", "negative_noncryst", "negative_cryst_mid",
             "negative_cryst_deep", "negative_cryst_verydeep"]
    vals = [det[c] if det[c] is not None else (BUDGET + 1) for c in order]
    assert all(vals[i] < vals[i + 1] for i in range(len(vals) - 1)), vals


# --------------------------------------------------------- (c) crystallized outcome
def test_crystallized_negative_is_depth_scaled_delay_not_permanent_identity_lock():
    """The crystallized-negative behaviour EXACTLY as the prior stage measured: a
    DELAY (depth-scaled latency) up to never-within-budget, NOT a permanent
    identity-level immunity. The crux: identity_field stays 0.0 through the confirmed
    record_hate_incident path (which writes external_field only), so `crystallized`
    is a deep negative external_field, not an identity commitment. The very-deep
    prior does NOT cross within the budget (the boundary's strong form as latency)."""
    mid_seed, mid_tr = _run(CONDITIONS["negative_cryst_mid"])
    deep_seed, deep_tr = _run(CONDITIONS["negative_cryst_deep"])
    vd_seed, vd_tr = _run(CONDITIONS["negative_cryst_verydeep"])

    # identity_field is 0 through the confirmed path in every crystallized recipe
    for s in (mid_seed, deep_seed, vd_seed):
        assert abs(s["regard_identity_field"]) < 1e-9, s["regard_identity_field"]
        assert s["crystallized"] is True, s          # the pattern flag DID crystallize

    # depth scales the latency: mid < deep, and very-deep NEVER crosses within budget
    assert mid_tr["crossing_latency"] == 12, mid_tr["crossing_latency"]
    assert deep_tr["crossing_latency"] == 26, deep_tr["crossing_latency"]
    assert mid_tr["crossing_latency"] < deep_tr["crossing_latency"]
    assert vd_tr["crossing_latency"] is None and vd_tr["crossed"] is False, vd_tr


# --------------------------------------------------------- (d) qualia tracks state
def test_qualia_tracks_produced_state_at_every_step():
    """QUALIA-TRACKS-STATE: at EVERY step of EVERY condition the produced
    dynamical:valence sign equals sign(regard_state) (+1 / -1, or absent at state 0).
    The felt quality is coupled to the produced dynamics -- this is what makes it a
    qualia experiment, not a decorative label."""
    for cname, recipe in CONDITIONS.items():
        _seeded, tr = _run(recipe)
        for cell in tr["trajectory"]:
            assert cell["qval"] == _qual_sign(cell["state"]), (cname, cell)


# --------------------------------------------------------- (e) ablation falsifier
def test_ablation_falsifier_frozen_update_collapses_the_effect():
    """FALSIFIER: freeze the belief update (alpha=0 on the positive encounters) and
    regard NEVER crosses in ANY condition -- neutral never warms, negative never
    recovers -- so the exposure effect VANISHES. If a crossing survived with the
    update frozen the effect would not be coming from the belief-update pathway."""
    for cname, recipe in CONDITIONS.items():
        w = MereExposureWorld(alpha=0.0)   # positive encounters apply +0.0 evidence
        w.seed_initial_valence(recipe)     # seeding uses the recipe's own alpha
        tr = w.exposure_trajectory(budget=BUDGET)
        assert tr["crossed"] is False, (cname, tr["crossing_latency"])


def test_personality_distinct_crossing_latencies():
    """PERSONALITY contrast: belief-plasticity alpha rescales the per-encounter step
    and thus the crossing latency. From a neutral prior a WARM (high-plasticity)
    agent crosses in strictly fewer encounters than a HOSTILE (low-plasticity) one."""
    warm = _run("neutral", alpha=0.6)[1]["crossing_latency"]
    default = _run("neutral", alpha=DEFAULT_ALPHA)[1]["crossing_latency"]
    hostile = _run("neutral", alpha=0.15)[1]["crossing_latency"]
    assert warm < default < hostile, (warm, default, hostile)


# --------------------------------------------- (f) native-only / integer discipline
def test_canonical_so_untouched():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    if os.path.exists(so):
        md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
        assert md5 == CANON_MD5


def test_no_new_seed_authored_and_absent_from_load_all():
    """The adapter authors NO new seed (prereg SS8): there is no
    mere_exposure_social.json, and nothing named mere_exposure is in load_all_seeds
    -- the base tree is byte-identical when the adapter is absent."""
    assert not os.path.exists(
        os.path.join(ROOT, "seeds", "mere_exposure_social.json"))
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert not any("mere_exposure" in s for s in seeds), \
        [s for s in seeds if "mere_exposure" in s]


def test_produced_regard_state_is_integer_native():
    """Integer discipline: the PRODUCED discrete liking (regard state, the felt/
    attitude quantity) is an integer at every step in every condition -- the mapping
    introduces no non-integer state."""
    for cname, recipe in CONDITIONS.items():
        _seeded, tr = _run(recipe)
        for cell in tr["trajectory"]:
            assert float(cell["state"]).is_integer(), (cname, cell)


def test_source_audit_no_forbidden_tokens():
    """The adapter is a WORLD ADAPTER: no graph rule engine, no if/else selecting
    the liking, no reward/punishment shaping. Source-audit the adapter for the
    forbidden tokens (all must be zero)."""
    src = open(os.path.join(ROOT, "domains", "mere_exposure_world.py")).read()
    for pat in ("graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule("):
        assert src.count(pat) == 0, pat
    for tok in ("reward_signal", "reinforce", "backprop", "gradient"):
        assert not re.search(r"\b" + re.escape(tok) + r"\b", src), tok


# ------------------------------------------------------------ (g) default == today
def test_default_no_encounters_reproduces_neutral_true_zero():
    """default == today: a freshly-instantiated target with NO encounters reproduces
    the bare no-exposure state -- regard state 0, external_field 0, identity_field 0,
    qualia valence absent -- so the adapter absent changes nothing (the effect is
    entirely the exposure encounters, not a biased baseline)."""
    w = MereExposureWorld()
    r = w.read()
    assert r["regard_state"] == 0, r
    assert abs(r["regard_external_field"]) < 1e-9, r
    assert abs(r["regard_identity_field"]) < 1e-9, r
    assert r["qualia_valence"] is None, r
    # and the accumulator is SYMMETRIC about true zero (no negative-default advantage)
    wp = MereExposureWorld(); wp.encounter(positive=True); wp.encounter(positive=True)
    wn = MereExposureWorld(); wn.encounter(positive=False); wn.encounter(positive=False)
    assert wp.regard_state() == 1 and wn.regard_state() == -1
    assert abs(wp.regard_external_field() + wn.regard_external_field()) < 1e-9, \
        (wp.regard_external_field(), wn.regard_external_field())
