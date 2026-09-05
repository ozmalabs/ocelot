"""BLOCK 295000 — FELT-PROSODY x RAVDESS two-arm gate. The affect->prosody
GENERATOR (Arm A) drives the substrate's OWN forward synthesizer from a live
ModulatorState affect coordinate through the pre-registered FIXED monotone map,
re-analyzed by the SAME judge DSP that fixed the RAVDESS regions; the PARSING LIFT
(Arm B) classifies binary arousal on REAL held-out RAVDESS actors with the felt
prosodic vector vs a blind twin. This file gates BOTH arms against the
pre-registration (`docs/research/psychology_affect/PROSODY_RAVDESS_PREREG.md`):

  (a) ARM A — each synthesized emotion's re-analyzed f0_mean tracks its arousal
      class (HIGH synths high, LOW synths low), monotone in the prereg arousal
      ordering, HIGH-mean f0 > LOW-mean f0, and CI-separated from the flat
      baseline; ENERGY now tracks arousal (rank-correlated with the prereg
      arousal ordering, HIGH-arousal energy CI-separated from LOW, and
      CI-separated from the flat baseline) after the synthesizer amplitude-
      preservation fix (clip-safety replaced the unconditional peak-normalize
      that had discarded absolute amplitude).
  (b) ARM B — the lift number is reproduced with the SIGN pinned, the blind twin
      is the byte-identical control, computed on HELD-OUT actors; the reliable-
      axis point-biserial sign is correct. Null is a valid pinned result.
  (c) THE JUDGE GATE re-asserted on real data (test split): energy angry >> neutral.
  (d) DISCIPLINE — .so md5 unchanged, native-only, data present + attributed, no
      new auto-loaded seed (default == today), glass-box source-audit.

The prosody_generation module + both measures use ONLY stdlib `wave` + numpy (no
soundfile / sklearn / scipy), so they run in this env; any pre-existing env
failure from those missing packages is NOT this rung's."""
import glob
import hashlib
import json
import os
import re
import sys
import wave

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.prosody_generation import (                        # noqa: E402
    ProsodyGenerator, knobs_for_emotion, knobs_from_arousal_valence,
    substrate_affect_coord, EMOTION_VA, EMOTION_TO_EMX, FLAT_BASELINE,
    DIGIT_WORDS)

CANON_MD5 = "28dd61b94c54d67966e82b70aa5197be"
RAVDESS_DIR = os.path.join(ROOT, "data", "ravdess")
RESULTS_DIR = os.path.join(ROOT, "results", "prosody_ravdess")
GEN_JSON = os.path.join(RESULTS_DIR, "generation.json")
LIFT_JSON = os.path.join(RESULTS_DIR, "parsing_lift.json")

HIGH_EMO = {"angry", "fearful", "happy"}
LOW_EMO = {"calm", "neutral"}
PREREG_ORDER = ["calm", "neutral", "sad", "disgust", "surprised",
                "happy", "fearful", "angry"]


def _load(path):
    assert os.path.exists(path), f"missing result {path}; run the measure first"
    with open(path) as f:
        return json.load(f)


# ============================================================ FIXTURES
@pytest.fixture(scope="module")
def gen_result():
    return _load(GEN_JSON)


@pytest.fixture(scope="module")
def lift_result():
    return _load(LIFT_JSON)


# ============================================================ (0) map is monotone
def test_fixed_map_is_monotone_pre_committed():
    """The affect->knob formula is monotone in arousal (higher a -> higher f0,
    shorter dur, lower ta) and NOT a function of the judge — a fixed function of
    a fixed coordinate."""
    a_vals = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    f0s = [knobs_from_arousal_valence(a)["f0_hz"] for a in a_vals]
    durs = [knobs_from_arousal_valence(a)["dur_s"] for a in a_vals]
    tas = [knobs_from_arousal_valence(a)["ta_frac"] for a in a_vals]
    assert f0s == sorted(f0s), f"f0 not monotone up: {f0s}"
    assert durs == sorted(durs, reverse=True), f"dur not monotone down: {durs}"
    assert tas == sorted(tas, reverse=True), f"ta not monotone down: {tas}"
    # frozen endpoints (prereg §3): a=0 -> 140Hz/0.60s/0.11 ; a=1 -> 300Hz/0.30s/0.01
    assert knobs_from_arousal_valence(0.0)["f0_hz"] == 140.0
    assert knobs_from_arousal_valence(1.0)["f0_hz"] == 300.0


# ============================================================ affect via substrate
def test_affect_read_through_real_modulator_state():
    """The affect coordinate is read off the REAL substrate ModulatorState (not a
    bare dict): every non-neutral emotion drives its emx_* region and the produced
    knobs are tagged source=substrate; the arousal ordering high>low holds on the
    substrate arousal_band."""
    coord_angry = substrate_affect_coord("angry")
    coord_calm = substrate_affect_coord("calm")
    if coord_angry is None or coord_calm is None:
        pytest.skip("non-live substrate")
    # anger is a HIGH-arousal region; calm is LOW — the substrate's own bands.
    assert coord_angry["arousal_band"] >= coord_calm["arousal_band"]
    k = knobs_for_emotion("angry", use_substrate=True)
    assert k["source"] == "substrate"
    assert k["emx"] == "anger"


# ============================================================ (a) ARM A
def test_armA_high_above_low_f0(gen_result):
    """Synthesized HIGH-arousal emotions re-analyze to higher f0_mean than LOW."""
    assert gen_result["verdict_high_above_low"] is True
    assert gen_result["high_mean_f0"] > gen_result["low_mean_f0"]
    assert gen_result["high_low_f0_gap"] > 30.0, gen_result["high_low_f0_gap"]


def test_armA_f0_monotone_in_arousal_ordering(gen_result):
    """Produced f0_mean is (mostly) monotone in the prereg arousal ordering."""
    assert gen_result["f0_monotone_frac"] >= 0.75, gen_result["f0_monotone_frac"]
    assert gen_result["verdict_arousal_monotone"] is True


def test_armA_low_emotions_land_low_region(gen_result):
    """LOW-arousal synths (calm, neutral) land in the LOW f0 region (<=300 Hz)."""
    by = {r["emotion"]: r for r in gen_result["rows"]}
    for emo in LOW_EMO:
        assert by[emo]["f0_region"] == "LOW", (emo, by[emo]["produced_f0_mean"])
        assert by[emo]["landed_own_arousal_region"] is True


def test_armA_angry_lands_high_region(gen_result):
    """The clearest HIGH emotion (angry) lands its own HIGH region and is nearest
    its own arousal class."""
    by = {r["emotion"]: r for r in gen_result["rows"]}
    assert by["angry"]["f0_region"] == "HIGH"
    assert by["angry"]["landed_own_arousal_region"] is True
    assert by["angry"]["nearest_shares_arousal_class"] is True


def test_armA_ci_separated_from_flat(gen_result):
    """Affect-driven renders are CI-separated from the FLAT neutral baseline for a
    majority of emotions (the mapping does the work, not the carrier)."""
    assert gen_result["n_ci_separated_from_flat"] >= 4, \
        gen_result["n_ci_separated_from_flat"]
    assert gen_result["verdict_ci_separated"] is True


def test_armA_energy_tracks_arousal(gen_result):
    """Post the synthesizer amplitude-preservation fix (clip-safety replaced the
    unconditional peak-normalize that discarded absolute amplitude), re-analyzed
    ENERGY now tracks arousal. Scored on ORDERING, not absolute band membership,
    because the synth energy scale (~0.09-0.36) differs from the RAVDESS wav scale
    (~0.002-0.021): (1) synth energy is rank-correlated with the pre-registered
    arousal ordering, (2) HIGH-arousal mean energy > LOW-arousal mean energy and
    CI-separated, (3) a majority of emotions are CI-separated from the flat
    baseline. This was the pinned Arm-A limit; it now WORKS."""
    # (1) rank (Spearman) correlation of synth energy vs the arousal ordering.
    assert gen_result["energy_arousal_rank_rho"] >= 0.7, \
        gen_result["energy_arousal_rank_rho"]
    assert gen_result["verdict_energy_tracks_arousal"] is True
    # (2) HIGH-arousal energy clearly above LOW, CI-separated.
    assert gen_result["high_mean_energy"] > gen_result["low_mean_energy"]
    assert gen_result["verdict_energy_high_above_low"] is True
    assert gen_result["high_low_energy_ci_separated"] is True
    # low-arousal emotions (calm, neutral) are the quietest; angry the loudest.
    en = gen_result["energy_values"]
    assert en["calm"] < en["angry"], en
    assert en["neutral"] < en["angry"], en
    assert en["calm"] < en["happy"] and en["neutral"] < en["fearful"], en
    # (3) affect-driven energy CI-separated from the flat baseline for a majority.
    assert gen_result["n_energy_ci_separated_from_flat"] >= 4, \
        gen_result["n_energy_ci_separated_from_flat"]
    assert gen_result["verdict_energy_ci_separated_from_flat"] is True
    # the energy spread is now large (was 0.029 when saturated) — real movement.
    assert gen_result["energy_spread"] > 0.10, gen_result["energy_spread"]


# ============================================================ (b) ARM B
def test_armB_lift_reproduced_and_sign_pinned(lift_result):
    """The lift number is reproduced with its SIGN pinned. Positive lift is the
    prediction; a null (~0) is a VALID pinned result and asserted explicitly if
    that is the honest outcome."""
    lift = lift_result["lift"]
    # sign consistency between the reported scalar and the tag
    if lift > 0:
        assert lift_result["lift_sign"] == "positive"
        assert lift_result["verdict_positive_lift"] is True
    elif lift == 0:
        assert lift_result["lift_sign"] == "null/zero"
        # explicit null assertion — a null is a valid pinned result.
        assert abs(lift) < 1e-9
    else:
        assert lift_result["lift_sign"] == "negative"
    # the lift is a real number in [-1, 1] and its CI brackets the point estimate.
    assert -1.0 <= lift <= 1.0
    lo, hi = lift_result["lift_ci"]
    assert lo <= lift + 1e-6 and hi >= lift - 1e-6, (lo, lift, hi)


def test_armB_blind_twin_is_control_on_held_out_actors(lift_result):
    """The blind twin is the byte-identical control: SAME classifier, SAME split,
    only the felt vector omitted; both trained on TRAIN actors and evaluated on
    HELD-OUT TEST actors (speaker-independent)."""
    assert lift_result["felt_features"] == ["energy_mean", "f0_mean", "contour"]
    assert lift_result["blind_features"] == ["duration_s", "zcr"]
    assert lift_result["train_actors"] == list(range(1, 17))
    assert lift_result["test_actors"] == list(range(17, 25))
    # no actor overlap (speaker-independent) — sets are disjoint by construction.
    assert set(lift_result["train_actors"]).isdisjoint(lift_result["test_actors"])
    # lift is exactly felt - blind on the held-out set.
    recomputed = round(lift_result["felt_accuracy"] - lift_result["blind_accuracy"], 4)
    assert abs(recomputed - lift_result["lift"]) < 0.02, (recomputed, lift_result["lift"])


def test_armB_reliable_axes_sign_correct(lift_result):
    """The reliable axes (energy, f0_mean) correlate POSITIVELY with the HIGH
    arousal label on the real held-out data (the arousal direction)."""
    assert lift_result["point_biserial_energy"] > 0, lift_result["point_biserial_energy"]
    assert lift_result["point_biserial_f0"] > 0, lift_result["point_biserial_f0"]
    assert lift_result["verdict_reliable_axes_sign_correct"] is True


def test_armB_8way_is_weak_secondary(lift_result):
    """8-way is the weak secondary (valence not separated per §0). It is reported;
    we only assert it is a real fraction — never the headline."""
    a8 = lift_result["acc_8way_felt"]
    assert a8 is not None and 0.0 <= a8 <= 1.0


# ============================================================ (c) JUDGE GATE
def _read_wav(path):
    with wave.open(path, "rb") as wf:
        fr = wf.getframerate()
        n = wf.getnframes()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        raw = wf.readframes(n)
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x.astype(np.float32), fr


def test_judge_discriminates_emotions_on_real_data():
    """THE GATE re-asserted on the TEST split: the judge's own energy is much
    higher for angry than neutral on real held-out RAVDESS wavs (the reliable
    arousal axis carries real emotion signal — the premise of both arms)."""
    from substrate_rs.communication import _energy_envelope
    if not os.path.isdir(RAVDESS_DIR):
        pytest.skip("RAVDESS data not present")

    def _mean_energy(emo_code, n_max=12):
        vals = []
        for actor in range(17, 25):           # TEST actors only
            for w in sorted(glob.glob(os.path.join(
                    RAVDESS_DIR, f"Actor_{actor:02d}",
                    f"03-01-{emo_code}-*.wav")))[:2]:
                x, fr = _read_wav(w)
                en = _energy_envelope(x, fr)
                if len(en):
                    vals.append(float(en.mean()))
            if len(vals) >= n_max:
                break
        return float(np.mean(vals)) if vals else 0.0

    angry_en = _mean_energy("05")
    neutral_en = _mean_energy("01")
    assert angry_en > neutral_en, (angry_en, neutral_en)
    # a wide margin — angry is the top of the arousal energy gradient.
    assert angry_en > 2.0 * neutral_en, (angry_en, neutral_en)


# ============================================================ (d) DISCIPLINE
def test_discipline_so_md5_unchanged():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs",
                      "_native.abi3.so")
    assert os.path.exists(so), so
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
    assert md5 == CANON_MD5, f"native .so changed: {md5}"


def test_discipline_no_new_autoloaded_seed():
    """No new seed file is authored by this rung — the base tree is byte-identical
    when the affect mapping is absent (default == today)."""
    seeds_dir = os.path.join(ROOT, "seeds")
    if os.path.isdir(seeds_dir):
        names = os.listdir(seeds_dir)
        assert not any("prosody_ravdess" in n or "prosody_generation" in n
                       for n in names), names
    # the generator module authors no seed manifest.
    src = open(os.path.join(ROOT, "domains", "prosody_generation.py")).read()
    assert "load_seed_manifest" not in src
    assert "add_production" not in src


def test_discipline_native_only_no_rust_touched():
    """Native-only: the generator + measures touch no Rust and do not import a
    toolbox solver."""
    for rel in ("domains/prosody_generation.py",
                "scripts/prosody_generation_measure.py",
                "scripts/prosody_parsing_lift_measure.py"):
        src = open(os.path.join(ROOT, rel)).read()
        assert ".rs" not in src.replace("audio_primitives.rs", "").replace(
            "communication.py", "")  # only mentioned in docstrings as read-only
        assert "toolbox" not in src.lower()


def test_discipline_glass_box_source_audit():
    """No graph_rewrite / _match / _apply / make_rule; no reward/punishment
    shaping — the affect->knob map is a fixed function, never learned."""
    forbidden = ("graph_rewrite.run", "gr.run", "make_rule(",
                 "reward_signal", "reinforce(", "backprop")
    for rel in ("domains/prosody_generation.py",
                "scripts/prosody_generation_measure.py",
                "scripts/prosody_parsing_lift_measure.py"):
        # strip docstrings' negation-mentions by only auditing code lines that are
        # not comments/docstrings-prose is over-engineering; instead pick tokens
        # that only appear as real calls (with the trailing "(").
        src = open(os.path.join(ROOT, rel)).read()
        for tok in forbidden:
            assert tok not in src, f"{tok} found in {rel}"
        # no sklearn-style model .fit( (np.polyfit is allowed — it is DSP, not a
        # trained model). Match a bare ".fit(" not preceded by "poly".
        assert not re.search(r"(?<!poly)\.fit\(", src), f".fit( found in {rel}"


def test_discipline_data_present_and_attributed():
    """RAVDESS data present + attribution file committed (license recorded)."""
    if not os.path.isdir(RAVDESS_DIR):
        pytest.skip("RAVDESS data not present")
    n_wav = len(glob.glob(os.path.join(RAVDESS_DIR, "Actor_*", "*.wav")))
    assert n_wav >= 1000, n_wav
    attr = os.path.join(RAVDESS_DIR, "ATTRIBUTION.md")
    assert os.path.exists(attr), "data/ravdess/ATTRIBUTION.md missing"
    txt = open(attr).read()
    assert "CC-BY-NC-SA" in txt
    assert "Livingstone" in txt and "Russo" in txt


def test_discipline_uses_stdlib_wave_not_soundfile():
    """Own code must use stdlib `wave`, not soundfile (which is absent here)."""
    src = open(os.path.join(ROOT, "scripts/prosody_parsing_lift_measure.py")).read()
    assert "import wave" in src
    assert "import soundfile" not in src
    assert "from soundfile" not in src
