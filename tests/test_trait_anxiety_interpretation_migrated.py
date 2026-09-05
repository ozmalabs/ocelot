"""BLOCK 292000 -- TRAIT-ANXIETY NEGATIVE INTERPRETATION BIAS gate. The anxiety
LABEL is the graph's own read-off (the REAL emx_anxiety region predicate + the
mod_securing formula), NOT Python; the SKEPTICISM trait writes ONE additive
set-point offset (ms.skepticism_bias) that bends securing. This file gates the
MacLeod & Mathews TRAIT x AMBIGUITY DISSOCIATION: personality bends ONLY the
AMBIGUOUS interpretation, SAFE (all 0) and THREAT (all 1) are personality-
invariant -- an INTERACTION, not a main effect -- and the interaction depends on
the bias hook (ablation falsifier), the produced grid EQUALS the analytic oracle
EXACTLY, and no new seed auto-loads (byte-identity when absent)."""
import hashlib
import json
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import domains.disposition as disp                              # noqa: E402
import domains.trait_modulator_bridge as tmb                    # noqa: E402
from domains.trait_anxiety_world import (                       # noqa: E402
    TraitAnxietyWorld, AMBIGUITY_BANDS, SKEPTICISM_LEVELS,
    ANXIETY_CODE, COMPETENCE, K, SECURING_HI,
    securing as oracle_securing, anxiety_fires as oracle_anxiety,
    _DRIVE_OVER, _MS_OVER)

CANON_MD5 = "a32ed336662eaa9eb6df27b7112541ac"   # canonical .so after native-only CAN cutover

N = 60
JITTER = 10
LOW_SKEP = (-4, -2)
HIGH_SKEP = (2, 4)


def _boot_ci(xs, reps=2000, seed=292000):
    xs = np.asarray(xs, float)
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def _jitter_offsets(band):
    if band == "safe":
        return np.arange(-JITTER, 1)
    if band == "threat":
        return np.arange(0, JITTER + 1)
    return np.arange(-JITTER, JITTER + 1)


def _cohort_rate(world, band, eu, skep_levels, rng):
    offs = _jitter_offsets(band)
    hits = []
    for _ in range(N):
        d = int(rng.choice(offs)); lvl = int(rng.choice(list(skep_levels)))
        hits.append(1.0 if world.classify(eu + d, lvl)["anxiety"] else 0.0)
    return hits


# ------------------------------------------------------------------- (a) grid==oracle
def test_produced_grid_equals_oracle_exactly():
    """PRODUCED-not-hand-set discipline: the graph's produced anxiety label AND
    securing value equal the analytic oracle at EVERY cell of the trait x
    ambiguity grid -- the dynamics PRODUCE the pre-registered labels, they are not
    written by the test."""
    w = TraitAnxietyWorld()
    for band, eu in AMBIGUITY_BANDS.items():
        for lvl in SKEPTICISM_LEVELS:
            c = w.classify(eu, lvl)
            assert c["securing"] == oracle_securing(eu, lvl), (band, lvl, c)
            assert c["anxiety"] == bool(oracle_anxiety(eu, lvl)), (band, lvl, c)
            # the label is the graph's ms.emotion == anxiety code, not a bool set here
            assert (c["emotion_code"] == ANXIETY_CODE) == c["anxiety"], (band, lvl, c)


# ------------------------------------------------------------ (b) interaction shape
def test_interaction_ambiguous_high_skep_ci_separated_above_low():
    """In the AMBIGUOUS band the high-skepticism anxiety RATE is CI-separated
    ABOVE the low-skepticism rate -- rising trait-anxiety bends the SAME ambiguous
    stimulus from safe to threat (the interaction, with bootstrap CIs)."""
    w = TraitAnxietyWorld()
    rng = np.random.default_rng(292000)
    eu = AMBIGUITY_BANDS["ambiguous"]
    low = _cohort_rate(w, "ambiguous", eu, LOW_SKEP, rng)
    high = _cohort_rate(w, "ambiguous", eu, HIGH_SKEP, rng)
    ci_low, ci_high = _boot_ci(low), _boot_ci(high)
    assert ci_high[0] > ci_low[1], (ci_low, ci_high)          # separated ABOVE
    assert np.mean(high) > np.mean(low)


# --------------------------------------------------------- (c) dissociation (invariance)
def test_dissociation_safe_all_none_threat_all_anxiety_personality_invariant():
    """The DISSOCIATION: in the SAFE band NO personality produces anxiety (all 0)
    and in the THREAT band ALL personalities produce anxiety (all 1). The
    endpoints are personality-INVARIANT -> the effect is an INTERACTION, not a
    main effect of skepticism."""
    w = TraitAnxietyWorld()
    for lvl in SKEPTICISM_LEVELS:
        assert w.classify(AMBIGUITY_BANDS["safe"], lvl)["anxiety"] is False, lvl
        assert w.classify(AMBIGUITY_BANDS["threat"], lvl)["anxiety"] is True, lvl
    # and the ambiguous band DOES move (both labels present across the sweep)
    amb = {lvl: w.classify(AMBIGUITY_BANDS["ambiguous"], lvl)["anxiety"]
           for lvl in SKEPTICISM_LEVELS}
    assert set(amb.values()) == {True, False}, amb


# --------------------------------------------------------- (d) ablation falsifier
def _classify_bias_ablated(w, eu, skep_level):
    native = w._native()
    w._set(w.drive, "exploration_urge", eu)
    for k, v in _DRIVE_OVER.items():
        w._set(w.drive, k, v)
    w._set(w.drive, "exploration_urge", eu)
    w._set(w.ms, "competence", COMPETENCE)
    w._set(w.ms, "competence_epoch", _MS_OVER["epoch"])
    w._set(w.ms, "emotion_epoch", -1.0)
    disp.set_trait_seed(w, "skepticism", float(skep_level))
    tmb.sync_traits_to_modulator(w, run=False)
    w._set(w.ms, "skepticism_bias", 0.0)                 # THE ABLATION
    native.run_rules()
    a = w._attrs(w.ms)
    return dict(securing=int(a.get("securing") or 0),
                anxiety=(int(a.get("emotion") or 0) == ANXIETY_CODE))


def test_ablation_falsifier_ambiguous_effect_vanishes_with_bias_zero():
    """With skepticism_bias forced to 0 the ambiguous-band personality effect
    VANISHES: every deterministic cell collapses to the no-bias securing
    (eu + K = 50, none), and the jittered high vs low cohorts are NOT
    CI-separated. If it survived, the effect would not be coming from the
    trait->set-point pathway."""
    w = TraitAnxietyWorld()
    eu = AMBIGUITY_BANDS["ambiguous"]
    no_bias = eu + K
    for lvl in SKEPTICISM_LEVELS:
        c = _classify_bias_ablated(w, eu, lvl)
        assert c["securing"] == no_bias, (lvl, c)         # skep no longer moves it
        assert c["anxiety"] is False, (lvl, c)
    # jittered cohorts under ablation: NOT separated
    rng = np.random.default_rng(292000)
    offs = _jitter_offsets("ambiguous")

    def rate(levels):
        return [1.0 if _classify_bias_ablated(w, eu + int(rng.choice(offs)),
                                              int(rng.choice(list(levels))))["anxiety"]
                else 0.0 for _ in range(N)]
    ci_low, ci_high = _boot_ci(rate(LOW_SKEP)), _boot_ci(rate(HIGH_SKEP))
    assert not (ci_high[0] > ci_low[1]), (ci_low, ci_high)   # NO separation


# --------------------------------------------------- (e) native-only / integer discipline
def test_canonical_so_untouched():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    if os.path.exists(so):
        md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
        assert md5 == CANON_MD5


def test_no_new_seed_authored_and_absent_from_load_all():
    """The adapter authors NO new seed (prereg §8): there is no
    trait_anxiety_interpretation.json, and nothing named trait_anxiety is in
    load_all_seeds -- the base tree is byte-identical when the adapter is absent
    (self_load_only taken one step further: no seed file to gate)."""
    assert not os.path.exists(
        os.path.join(ROOT, "seeds", "trait_anxiety_interpretation.json"))
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert not any("trait_anxiety" in s for s in seeds), \
        [s for s in seeds if "trait_anxiety" in s]


def test_integer_native_no_non_integer_lits_in_the_grid():
    """Integer discipline: every PRODUCED securing value over the whole grid is an
    integer (the mapping introduces no non-integer float), and the analytic oracle
    it is checked against is likewise integer-valued -- no non-integer float Lit
    is introduced by this rung."""
    w = TraitAnxietyWorld()
    for band, eu in AMBIGUITY_BANDS.items():
        for lvl in SKEPTICISM_LEVELS:
            sec = w.classify(eu, lvl)["securing"]
            assert float(sec).is_integer(), (band, lvl, sec)
            assert float(oracle_securing(eu, lvl)).is_integer(), (band, lvl)


def test_pinned_rule_names_present_on_the_spine():
    """The load-bearing modulator/emotion rules are the REAL pinned graph rules
    (not reinvented): mod_securing produces securing, emx_anxiety classifies it,
    emx_readoff writes ms.emotion. Assert they are present on the booted spine."""
    w = TraitAnxietyWorld()
    names = {row.get("name") for row in w._native().export_rules()}
    for r in ("mod_securing", "emx_anxiety", "emx_readoff"):
        assert r in names, (r, sorted(n for n in names if n and n.startswith(("mod_", "emx_")))[:20])


def test_source_audit_no_forbidden_tokens():
    """The adapter is a WORLD ADAPTER: no graph rule engine, no if/else selecting
    the emotion, no reward/punishment shaping. Source-audit the adapter for the
    forbidden tokens (all must be zero)."""
    src = open(os.path.join(ROOT, "domains", "trait_anxiety_world.py")).read()
    for pat in ("graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule("):
        assert src.count(pat) == 0, pat
    for tok in ("reward_signal", "reinforce", "backprop", "gradient"):
        assert not re.search(r"\b" + re.escape(tok) + r"\b", src), tok


# ------------------------------------------------------------ (f) default == today
def test_default_skepticism_level_zero_reproduces_no_bias_label():
    """default == today: a default-skepticism (level 0 => skepticism_bias 0) agent
    reproduces the bare no-bias emotion label -- in every band the level-0 cell's
    securing equals eu + K (the bias-free securing) and its anxiety label matches
    the no-bias prediction."""
    w = TraitAnxietyWorld()
    for band, eu in AMBIGUITY_BANDS.items():
        c = w.classify(eu, 0)
        assert w.skepticism_bias_read() == 0, (band, w.skepticism_bias_read())
        assert c["securing"] == eu + K, (band, c["securing"], eu + K)
        assert c["anxiety"] == ((eu + K) > SECURING_HI), (band, c)
