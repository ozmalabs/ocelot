"""SHARPEN LARGE VOCAB — the agent's EAR IS BAND-LIMITED TO 4kHz. Give it a 16kHz ear.

The diagnostic chain ended upstream: the agent's ear samples at FS=8000 (Nyquist 4kHz), but the fricative
detail that separates confusable onsets (s/f/th in six/fix, sat/fat) lives at 4-8kHz -- "six" has 0.0% energy
above 4kHz at 8kHz. The consonant detail is LOW-PASSED AWAY before any cue sees it; no re-rank/positional/cue
can recover what was never sampled. Piper voices are natively 22050Hz, downsampled to 8kHz at synth.

This raises the ear to 16kHz (Nyquist 8kHz) so the cochleagram's 80-7500Hz bands carry REAL fricative energy,
and measures large-vocab recognition at 8kHz vs 16kHz, cross-speaker LOSO + WCCN, full cues, on the
onset-confusable CVC vocab + the realistic vocab. If 16kHz sharpens it, the lever is the EAR, not the cues.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_hifi_ear
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.agent_frontend as FE
from domains.speech_world import SpeechWorld, _resample
from scripts.universal_loop_phaseAB_piper import _get_voice, _knobs_to_synconfig
from scripts.jabberwock_largevocab_diag import WORDS, SPEAKERS, RENDS, set_active
from scripts.jabberwock_positional_cues import CVC, evaluate

RATES = [8000, 16000]


def synth_native(word, voice):
    """piper -> raw audio at its NATIVE sample rate (NOT downsampled to 8kHz)."""
    v = _get_voice(voice["variant"])
    if v is None:
        return None
    cfg = _knobs_to_synconfig(voice.get("pitch", 50), voice.get("rate", 175))
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
    return (audio.astype(np.float64) / 32768.0), sr


def main():
    print("=" * 96)
    print("HI-FI EAR — does a 16kHz ear (restoring the 4-8kHz fricative band) break the large-vocab ceiling?")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    FE.install_curated_frontend(s)
    fe = next(n for n in s.nodes("FrontEnd"))
    allnames = [s.node(c)["attrs"].get("name") for et in ("has_cue", "repertoire") for c in s.neighbours(fe, et)]
    set_active(s, fe, allnames)
    n_full = len(allnames)
    full = list(range(n_full))

    vocab = sorted(set(CVC) | set(WORDS))
    print(f"  synth native + extract full cues at {RATES}Hz for {len(vocab)} words...", flush=True)
    native = {}
    for v in SPEAKERS:
        for w in vocab:
            for r in range(RENDS):
                got = synth_native(w, {"variant": v, "pitch": 50, "rate": 175})
                if got is not None:
                    native[(v, w, r)] = got

    feats_by_fs = {}
    for fs in RATES:
        feats = {}
        for k, (x, sr) in native.items():
            xr = _resample(x, sr, fs)
            feats[k] = FE.feature_channels(s, np.asarray(xr, dtype=np.float64), fs)
        feats_by_fs[fs] = feats
        print(f"  extracted at {fs}Hz", flush=True)

    print(f"\n  {'vocab':<26}{'ear':>8}{'top-1':>9}{'recall':>9}")
    summary = {}
    for label, words in (("CVC onset-confusable", CVC), ("realistic mixed", WORDS)):
        base = None
        for fs in RATES:
            t1, ik = evaluate(feats_by_fs[fs], words, full)
            if base is None:
                base = t1
            tag = f"({(t1-base)*100:+.0f}pt)" if fs != RATES[0] else ""
            print(f"  {label:<26}{fs:>8}{t1*100:>8.0f}%{ik*100:>8.0f}%  {tag}")
            summary[(label, fs)] = t1

    print("\n" + "=" * 96)
    dc = summary[("CVC onset-confusable", 16000)] - summary[("CVC onset-confusable", 8000)]
    dr = summary[("realistic mixed", 16000)] - summary[("realistic mixed", 8000)]
    print(f"  16kHz ear vs 8kHz: CVC {dc*100:+.0f}pt | realistic {dr*100:+.0f}pt top-1")
    if dc > 0.05 or dr > 0.05:
        print("  THE EAR WAS THE CEILING: restoring the 4-8kHz fricative band sharpens large-vocab recognition --")
        print("  the agent was DEAF to the consonant detail that separates confusable words. Raise the ear to 16kHz")
        print("  (speech_world.FS) + keep the 80-7500Hz bands; a real, no-gradient recogniser fix upstream of all cues.")
    else:
        print(f"  16kHz does not break it (CVC {dc*100:+.0f}, real {dr*100:+.0f}) -- the band-limit was not the binding")
        print("  constraint at this vocab/coverage; the residual ceiling stays the cipher's language prior.")
    print("=" * 96)


if __name__ == "__main__":
    main()
