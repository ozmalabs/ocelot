"""sc_loso_frontend_norm — the DECISIVE cross-speaker test on REAL multi-speaker data.

The physics-model LOSO run (docs/physics_parent_loso.md) proved the cross-speaker
speaker-invariance wall is a FRONT-END problem: even a real FSDD bank gets LOSO ~0.35
with the seed cochleagram+L2 front end, and the lever is SOURCE NORMALIZATION at the
front end (CMVN over the cochleagram / the VTL-invariant formant pattern), not a
better voicebox. FSDD has only a handful of speakers (LOSO = ONE held-out speaker).

This script makes that test ROBUST and REAL: Google Speech Commands (/tmp/sc — ~2500
real speakers, the spoken digits zero..nine), with a LEAVE-MANY-SPEAKERS-OUT probe
(N held-out speaker hashes whose clips are NEVER banked). It runs the SAME bank-level
A/B as synth_parent_loso_probe, but A/B's the agent's FRONT-END REPRESENTATION:

  (S) SEED          — the 3-cue seed front end (gammatone_flat + fft_ear + allpole).
  (C) +CMVN         — seed + the source-normalized cochlear ear (per-utterance mean
                      AND variance normalization — speaker per-band gain cancels).
  (V) +VTL          — seed + the VTL-invariant formant pattern (F_i - mean(F1..F3);
                      vocal-tract-length shift on the log-band axis cancels).
  (B) +BOTH         — seed + CMVN + VTL (the full source-normalized representation).

Each regime reports SEEN-SPEAKER and cross-speaker LOSO on the SAME robust probe, so
we read both the absolute lift and the residual seen-vs-cross gap. NO-DONKEY: the
front-end cues are the agent's graph-resident, composable-DSP representation; the
SC load + speaker split are world-adapter mechanics; recognition is the agent's own
blind_guess (many-settings Argmax-of-product) over its banked exemplars; the held-out
speakers' clips are NEVER banked; LOSO is the ungameable yardstick.

Run: python -m scripts.sc_loso_frontend_norm [n_train_spk] [n_held_spk] [n_per]
"""
from __future__ import annotations

import os
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
import domains.agent_frontend as FE
from domains.stt_pipeline import STTPipeline, STTParams

CELL = "digit|sc|en"
FS = W._TARGET_FS

# the four front-end regimes A/B'd on the SAME robust real LOSO. Each names the
# repertoire cues to gate IN on top of the 3-cue seed front end (the agent's
# source-normalization representation).
REGIMES = [
    ("SEED", []),
    ("+CMVN", ["cmvn_ear"]),
    ("+VTL", ["vtl_formant"]),
    ("+BOTH", ["cmvn_ear", "vtl_formant"]),
]


def fresh(active_cues):
    """A fresh substrate with the speech world + the named source-normalization cues
    gated into the agent's graph-resident front end. World-adapter construction."""
    W.reset_caches()
    s = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=FS))
    pipe.attach(s)
    pipe._ensure_audio_pipeline(s)
    W.install_speech_world_rules(s)
    W.install_cell(s, "digit", "sc", "en")
    for c in s.nodes("Cue"):
        if s.node(c)["attrs"].get("name") in active_cues:
            s.set_attr(c, "active", 1.0)        # gate in the normalization cue
    return s, pipe


def bank(s, train_clips):
    """Bank the train clips (real, seen-speaker) as exemplars — the agent grows its
    cell's lexicon + bank. Held-out speakers' clips are NEVER passed here."""
    for w, x, fs in train_clips:
        W.bank_exemplar(s, w, CELL, x, FS)


def measure(s, probe):
    tot = cor = 0
    for w, x, fs in probe:
        ch = W.feature_channels(s, x, fs)
        g = W.blind_guess(s, ch, CELL, restrict_to=None)   # full lexicon — ungameable
        tot += 1
        cor += int(g == w)
    return cor / max(tot, 1)


def build_split(n_train_spk, n_held_spk, n_per, seed=20240608):
    """Build the robust real LOSO split over Speech Commands: pick N_train and N_held
    DISJOINT speaker hashes; the train clips (n_per per word per train-speaker, capped)
    are the bank; the held-out speakers' clips are the cross-speaker probe (never
    banked); a disjoint slice of train-speaker clips is the seen-speaker probe.
    Probe-construction mechanics — pure I/O."""
    words = W.sc_words()
    rng = random.Random(seed)
    speakers = W.sc_speakers(words)
    rng.shuffle(speakers)
    held_spk = speakers[:n_held_spk]
    train_spk = speakers[n_held_spk:n_held_spk + n_train_spk]
    print(f"[split] {len(words)} words {words}", flush=True)
    print(f"[split] {len(train_spk)} TRAIN speakers, {len(held_spk)} HELD-OUT speakers "
          f"(disjoint; held clips NEVER banked)", flush=True)

    train_idx = W.sc_index_for(train_spk, words)
    held_idx = W.sc_index_for(held_spk, words)

    # bank: up to n_per train clips per word (balanced across train speakers).
    train_clips, seen_probe = [], []
    for w in words:
        paths = list(train_idx.get(w, []))
        rng.shuffle(paths)
        train_clips += [(w,) + W.load_sc_clip(p) for p in paths[:n_per]]
        # seen-speaker probe: a DISJOINT slice of train-speaker clips (not banked).
        # A wide slice (20/word) so the seen-speaker baseline is a stable estimate.
        for p in paths[n_per:n_per + 20]:
            seen_probe.append((w,) + W.load_sc_clip(p))

    # cross-speaker LOSO probe: held-out speakers' clips (NEVER banked), balanced.
    loso_probe = []
    for w in words:
        paths = list(held_idx.get(w, []))
        rng.shuffle(paths)
        for p in paths[:max(1, n_held_spk)]:
            loso_probe.append((w,) + W.load_sc_clip(p))

    print(f"[split] bank {len(train_clips)} train clips, "
          f"{len(seen_probe)} seen-speaker probes, "
          f"{len(loso_probe)} cross-speaker LOSO probes", flush=True)
    return train_clips, seen_probe, loso_probe


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    train_clips, seen_probe, loso_probe = build_split(n_train_spk, n_held_spk, n_per)

    results = {}
    for name, cues in REGIMES:
        s, _pipe = fresh(cues)
        bank(s, train_clips)
        seen = measure(s, seen_probe)
        loso = measure(s, loso_probe)
        results[name] = (seen, loso)
        print(f"\n[{name:6s}] active cues={FE.n_active(s)}  "
              f"seen-speaker {seen:.3f}   cross-speaker LOSO {loso:.3f}   "
              f"gap {seen - loso:+.3f}", flush=True)

    seed_seen, seed_loso = results["SEED"]
    print("\n" + "=" * 68, flush=True)
    print("SPEECH-COMMANDS ROBUST CROSS-SPEAKER LOSO — front-end source-normalization",
          flush=True)
    print("=" * 68, flush=True)
    print(f"  {'regime':8s} {'seen':>8s} {'LOSO':>8s} {'seen-LOSO gap':>14s} "
          f"{'LOSO lift':>11s}", flush=True)
    for name, _ in REGIMES:
        seen, loso = results[name]
        lift = loso - seed_loso
        print(f"  {name:8s} {seen:8.3f} {loso:8.3f} {seen - loso:14.3f} "
              f"{lift:+11.3f}", flush=True)

    # verdict: which normalization lifts the cross-speaker LOSO most, beyond noise.
    best_name = max(("+CMVN", "+VTL", "+BOTH"),
                    key=lambda n: results[n][1])
    best_loso = results[best_name][1]
    lift = best_loso - seed_loso
    chance = 1.0 / len(W.sc_words())
    print("-" * 68, flush=True)
    print(f"  chance {chance:.3f}; SEED cross-speaker LOSO {seed_loso:.3f} "
          f"(seen {seed_seen:.3f}, gap {seed_seen - seed_loso:+.3f})", flush=True)
    print(f"  best source-normalized: {best_name} LOSO {best_loso:.3f} "
          f"(lift {lift:+.3f} over seed)", flush=True)
    residual_gap = results[best_name][0] - best_loso
    print(f"  residual seen-vs-cross gap under {best_name}: {residual_gap:+.3f}",
          flush=True)
    if lift > 0.02:
        print(f"  => YES: front-end source-normalization ({best_name}) LIFTS the real "
              f"cross-speaker LOSO by {lift:+.3f}. The wall is a front-end problem and "
              f"this representation moves it.", flush=True)
    else:
        print(f"  => NO: front-end source-normalization does NOT lift the robust real "
              f"cross-speaker LOSO (best {lift:+.3f}). The residual is deeper than the "
              f"normalization tested.", flush=True)
    print("[MARKER] SC_LOSO_FRONTEND_NORM_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
