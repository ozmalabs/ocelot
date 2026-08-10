"""universal_loop_phaseAB_piper — the PIPER (neural TTS) voicebox swap-in.

This module is the ONLY thing that changes between the espeak Phase-C run (commit
3d724209, plateau 0.420 < CMVN 0.570, diagnosed (a) FORWARD MODEL too coarse) and the
Piper re-run. It provides drop-in `synth(W,V)` and `build_voice_space(...)` with the
SAME signatures + the SAME voice-dict shape ({"id","variant","pitch","rate"}) the
UNCHANGED loop (`scripts.universal_loop_phaseC.Loop`) manipulates, so the loop logic —
coarse-match / adapt-V coordinate descent / order-N iterate / argmin — is reused
byte-for-byte. Only the world (the mouth) is swapped: espeak formant-synth -> Piper
neural vocoder.

The DIAGNOSIS that motivated this was QUALITY, not voice COUNT. Piper ships single-
speaker models (num_speakers=1 each), so V-coverage now leans on:
  · the few neural VOICE MODELS (en_US-lessac, fr_FR-siwis, de_DE-thorsten, es_ES-davefx
    — distinct neural timbres = the `variant` axis the loop hill-climbs), and
  · the CONTINUOUS prosody knobs Piper exposes: length_scale (speaking rate — the loop's
    `rate` axis) and noise_w_scale (phoneme-duration variability, a controllable prosodic
    proxy mapped from the loop's `pitch` axis).
Honest: this is single-timbre-family per language vs espeak's 104 variant pool. The make-
or-break floor diagnostic tests whether neural QUALITY flips the true-vs-wrong separation
positive regardless of count.

DONKEY BOUNDARY (unchanged): Piper = the WORLD/voicebox the agent CONTROLS and HEARS; it
is NEVER inverted by the agent, NEVER part of a decision — only re-voiced and re-heard via
the loop's residual-min search over the real nonlinear synth. Pure world I/O. The features
are the agent's OWN front end (learned_voice_shape.residual_track, empty library = CMVN),
the SAME feature the DtwTo recognizer reads on real clips.

Run via scripts/universal_loop_phaseC_piper.py with the project .venv python (Piper lives
there, NOT system python).
"""
from __future__ import annotations

import os
import sys
import math
import random
import subprocess
import tempfile
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import domains.self_directed_speech_world as W
import domains.learned_voice_shape as LVS

# reuse the espeak Phase A+B's constants + the things the loop imports unchanged.
from scripts.universal_loop_phaseAB import (
    _CELL, _DIGITS, FS, babble_library, nearest_term, min_residual_term,
    coverage_test, build_real_probe, fresh, _dist_summary,
)

# the agent's UNCHANGED graph-resident DtwTo plumbing (re-exported for the runner).
from scripts.dtw_trajectory_loso import (
    _Pred, _V, _Lit, _Attr, _Nb, _DtwTo, _MinOver, _Argmin, _traj_tuple,
    QUERY_NODE_TYPE, QUERY_TRAJ_ATTR, EX_TRAJ_ATTR)


# ===========================================================================
# PIPER voicebox config — the neural mouth.
# ===========================================================================

_VOICE_DIR = os.environ.get(
    "PIPER_VOICE_DIR", os.path.expanduser("~/.cache/ozma/piper_voices"))

# The neural voice models = the discrete `variant` axis. For a clean CROSS-SPEAKER (same-language,
# different-talker) study, the ENGLISH voices below are the real speaker pool: 7 en_US + 5 en_GB,
# male & female, genuine VTL/timbre/accent diversity -- so the agent's recognition-vs-N-speakers curve
# samples the actual speaker (key) manifold instead of one warped voice. The fr/de/es voices are kept
# for back-compat but are a CROSS-LANGUAGE confound (a French TTS voicing English digits), not speakers.
_PIPER_MODELS = {
    # en_US speakers
    "lessac":   "en_US-lessac-medium.onnx",
    "amy":      "en_US-amy-medium.onnx",
    "ryan":     "en_US-ryan-medium.onnx",
    "hfc_female": "en_US-hfc_female-medium.onnx",
    "hfc_male": "en_US-hfc_male-medium.onnx",
    "kusal":    "en_US-kusal-medium.onnx",
    "joe":      "en_US-joe-medium.onnx",
    "bryce":    "en_US-bryce-medium.onnx",
    "john":     "en_US-john-medium.onnx",
    "norman":   "en_US-norman-medium.onnx",
    "sam":      "en_US-sam-medium.onnx",
    "kristin":  "en_US-kristin-medium.onnx",
    "ljspeech": "en_US-ljspeech-high.onnx",
    "danny":    "en_US-danny-low.onnx",
    "kathleen": "en_US-kathleen-low.onnx",
    # en_GB speakers
    "alan":     "en_GB-alan-medium.onnx",
    "alba":     "en_GB-alba-medium.onnx",
    "cori":     "en_GB-cori-medium.onnx",
    "jenny":    "en_GB-jenny_dioco-medium.onnx",
    "northern": "en_GB-northern_english_male-medium.onnx",
    # French speakers (for the MULTILINGUAL cross-speaker study: same-language, different-talker)
    "siwis":    "fr_FR-siwis-medium.onnx",
    "gilles":   "fr_FR-gilles-low.onnx",
    "tom":      "fr_FR-tom-medium.onnx",
    "fr_mls":   "fr_FR-mls_1840-low.onnx",
    "upmc":     "fr_FR-upmc-medium.onnx",
    # German speakers
    "thorsten": "de_DE-thorsten-medium.onnx",
    "eva_k":    "de_DE-eva_k-x_low.onnx",
    "karlsson": "de_DE-karlsson-low.onnx",
    "kerstin":  "de_DE-kerstin-low.onnx",
    "ramona":   "de_DE-ramona-low.onnx",
    "pavoque":  "de_DE-pavoque-low.onnx",
    # Spanish speakers (es_ES + es_MX)
    "davefx":   "es_ES-davefx-medium.onnx",
    "carlfm":   "es_ES-carlfm-x_low.onnx",
    "sharvard": "es_ES-sharvard-medium.onnx",
    "ald":      "es_MX-ald-medium.onnx",
    "claude_es": "es_MX-claude-high.onnx",
}

# same-language speaker pools per language for the MULTILINGUAL cross-speaker study.
LANG_VOICES = {
    "fr": ["siwis", "gilles", "tom", "fr_mls", "upmc"],
    "de": ["thorsten", "eva_k", "karlsson", "kerstin", "ramona", "pavoque"],
    "es": ["davefx", "carlfm", "sharvard", "ald", "claude_es"],
}
# digit words 1-9 per language (the recognition vocabulary).
LANG_DIGITS = {
    "en": ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"],
    "fr": ["un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"],
    "de": ["eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun"],
    "es": ["uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"],
}

# the clean same-language speaker pool for cross-speaker studies (excludes the fr/de/es confounds).
ENGLISH_VOICES = ["lessac", "amy", "ryan", "hfc_female", "hfc_male", "kusal", "joe",
                  "bryce", "john", "norman", "sam", "kristin", "ljspeech", "danny", "kathleen",
                  "alan", "alba", "cori", "jenny", "northern"]
LANG_VOICES["en"] = ENGLISH_VOICES

# voice cache: model name -> loaded PiperVoice (lazy; loading is ~0.6s, synth ~0.03-0.1s).
_VOICE_CACHE: dict = {}


def _piper_available():
    try:
        import piper  # noqa: F401
    except Exception:
        return False
    return any(os.path.exists(os.path.join(_VOICE_DIR, fn))
               for fn in _PIPER_MODELS.values())


def piper_models_present():
    """The variant names whose model file actually exists on disk (the usable pool)."""
    return [k for k, fn in _PIPER_MODELS.items()
            if os.path.exists(os.path.join(_VOICE_DIR, fn))]


def _get_voice(variant):
    """Load (and cache) the PiperVoice for a `variant` (= model key). World I/O."""
    from piper import PiperVoice
    fn = _PIPER_MODELS.get(variant)
    if fn is None:
        return None
    path = os.path.join(_VOICE_DIR, fn)
    if not os.path.exists(path):
        return None
    v = _VOICE_CACHE.get(variant)
    if v is None:
        v = PiperVoice.load(path)
        _VOICE_CACHE[variant] = v
    return v


def _knobs_to_synconfig(pitch, rate):
    """Map the loop's UNCHANGED continuous knobs (pitch 0..99, rate 80..300 — the espeak
    axes the loop's adapt-V steps) onto Piper's controllable prosody. The loop code never
    changes; this is the world adapter translating its V-coordinates into the neural mouth:
      · rate (words/min, ~80..300, espeak default ~175) -> length_scale (duration multiplier;
        FASTER speech = SHORTER frames = SMALLER length_scale). length_scale = 175 / rate,
        clamped to a sane neural range so prosody stays on-manifold.
      · pitch (0..99, espeak default ~50) -> noise_w_scale (phoneme-duration stochasticity,
        Piper's main per-utterance prosodic-variability knob — a controllable proxy for the
        talker-variation axis; Piper medium models are single-speaker with no f0 knob, so
        this is the honest available prosody control). pitch 0..99 -> noise_w 0.2..1.4.
    Pure deterministic translation, no decision."""
    from piper import SynthesisConfig
    length_scale = 175.0 / max(40.0, float(rate))      # rate up -> shorter
    length_scale = min(1.8, max(0.55, length_scale))
    noise_w = 0.2 + (float(pitch) / 99.0) * 1.2         # 0.2 .. 1.4
    noise_w = min(1.4, max(0.2, noise_w))
    return SynthesisConfig(length_scale=length_scale, noise_scale=0.667,
                           noise_w_scale=noise_w, normalize_audio=False)


def synth(word, voice):
    """THE PIPER VOICEBOX: synth(word W, voice V) -> cmvn cochleagram features. SAME
    signature + return as the espeak `synth`; the loop calls it UNCHANGED. The agent
    controls the neural mouth's knobs (model timbre via `variant`, rate via length_scale,
    prosody via noise_w mapped from `pitch`); the world voices `word`, the audio is
    resampled to 8 kHz mono (matching SC + the cochlea, via ffmpeg exactly like the espeak
    path), and the agent's OWN front end (learned_voice_shape.residual_track, empty library
    = CMVN) turns the heard audio into the feature trajectory the recognizer reads. Pure
    world I/O + the agent's own feature derivation; Piper is NEVER inverted."""
    v = _get_voice(voice["variant"])
    if v is None:
        return None
    cfg = _knobs_to_synconfig(voice["pitch"], voice["rate"])
    try:
        chunks = list(v.synthesize(word, cfg))
    except Exception:
        return None
    if not chunks:
        return None
    sr = chunks[0].sample_rate
    audio = np.concatenate([ch.audio_int16_array for ch in chunks]).astype(np.int16)
    if audio.size == 0:
        return None
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "r.wav")
        out = os.path.join(d, "o.wav")
        with wave.open(raw, "wb") as wv:
            wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr)
            wv.writeframes(audio.tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                        "-ar", str(FS), "-ac", "1", "-sample_fmt", "s16", out],
                       check=True, capture_output=True)
        with wave.open(out, "rb") as wv:
            x = (np.frombuffer(wv.readframes(wv.getnframes()), dtype=np.int16)
                 .astype(np.float64) / 32768.0)
    if x.size == 0:
        return None
    return LVS.residual_track(x, FS, [])


def build_voice_space(n_voices, seed=0):
    """Derive the PIPER V-space: each voice V is a (variant=neural model, pitch, rate)
    dict — SAME shape the loop manipulates. We span the available neural models (distinct
    timbres) x a pitch grid (-> noise_w prosody) x a rate grid (-> length_scale), sampled
    diversely. With few models the grid leans on the continuous prosody axes; the diagnosis
    was quality not count, so this is the valid first test. Returns a list of voice dicts."""
    rng = random.Random(seed)
    variants = piper_models_present()
    if not variants:
        return []
    pitch_grid = [20, 40, 60, 80, 99]                  # -> noise_w 0.44..1.40
    rate_grid = [130, 160, 175, 200, 230]              # words/min -> length_scale
    combos = [(v, p, r) for v in variants for p in pitch_grid for r in rate_grid]
    rng.shuffle(combos)
    voices = []
    for v, p, r in combos[:n_voices]:
        voices.append({"id": f"{v}@p{p}r{r}", "variant": v, "pitch": p, "rate": r})
    return voices


# variant list for the loop's hill-climb neighbourhood (the discrete VTL/timbre axis).
def piper_variants():
    return sorted(piper_models_present())
