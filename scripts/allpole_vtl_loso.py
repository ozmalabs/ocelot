"""allpole_vtl_loso — does the agent's SHARP all-pole formant make the VTL lever BITE?

The robust SC LOSO run (docs/sc_loso_frontend_norm.md) found: on real 40-speaker
Speech Commands LOSO, CMVN lifts cross-speaker LOSO +0.04-0.08 (the dominant lever),
but the VTL-invariant formant (vtl_formant) BARELY MOVED / sometimes hurt — because
its formant estimate is the COARSE gammatone ArgMax-over-log-bands (the gammatone
wall), too blurry for F_i - mean(F1..F3) to be a sharp cross-speaker invariant. The
named next move: NOT a new normalization, but the SHARPER ALL-POLE formant the agent
already owns (iter-43 LPC-root formants at full waveform resolution) feeding the SAME
VTL normalization.

This script reuses the SAME robust SC 40-speaker LOSO split (build_split from
sc_loso_frontend_norm, ungameable: 120 train / 40 held-out DISJOINT speakers, the
held-out clips NEVER banked, full-lexicon blind_guess) and A/B's four regimes:

  (S) SEED                  — the 3-cue seed front end.
  (C) +CMVN                 — seed + the source-normalized cochlear ear (dominant).
  (Vc) +CMVN+VTL(coarse)    — + the COARSE gammatone-ArgMax VTL formant (the one that
                              barely moved). The control: the SAME VTL invariant on the
                              BLURRY formant.
  (Va) +CMVN+VTL(allpole)   — + the SHARP all-pole VTL formant (F_i - mean over the
                              LPC-root formant Hz). The test: does the sharp formant
                              make the SAME VTL invariant finally bite ON TOP of CMVN?

NO-DONKEY: the all-pole formant + VTL normalization are the agent's graph-resident,
composable-DSP representation (Levinson-Durbin + root-finding + the F_i - mean Term);
SC load + speaker split are world-adapter mechanics; recognition is the agent's own
blind_guess over its banked exemplars; held-out speakers' clips are NEVER banked;
LOSO is the ungameable yardstick.

Run: python -m scripts.allpole_vtl_loso [n_train_spk] [n_held_spk] [n_per]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
import domains.agent_frontend as FE
from domains.stt_pipeline import STTPipeline, STTParams

# reuse the SAME robust SC LOSO split builder + bank/measure mechanics (ungameable).
from scripts.sc_loso_frontend_norm import build_split, bank, measure, CELL, FS

# the four front-end regimes A/B'd on the SAME robust real LOSO. Each names the
# repertoire cues to gate IN on top of the 3-cue seed front end. The two VTL regimes
# are IDENTICAL except for WHICH formant estimate feeds the SAME F_i - mean invariant
# (coarse gammatone vs sharp all-pole) — so any difference is the formant sharpness.
REGIMES = [
    ("SEED", []),
    ("+CMVN", ["cmvn_ear"]),
    ("+CMVN+VTLc", ["cmvn_ear", "vtl_formant"]),            # coarse gammatone VTL
    ("+CMVN+VTLa", ["cmvn_ear", "vtl_formant_allpole"]),    # sharp all-pole VTL
]


def fresh(active_cues):
    """A fresh substrate with the speech world + the named cues gated into the agent's
    graph-resident front end. World-adapter construction (no decision over state)."""
    W.reset_caches()
    s = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=FS))
    pipe.attach(s)
    pipe._ensure_audio_pipeline(s)
    W.install_speech_world_rules(s)
    W.install_cell(s, "digit", "sc", "en")
    for c in s.nodes("Cue"):
        if s.node(c)["attrs"].get("name") in active_cues:
            s.set_attr(c, "active", 1.0)        # gate in the cue
    return s, pipe


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
        print(f"\n[{name:12s}] active cues={FE.n_active(s)}  "
              f"seen-speaker {seen:.3f}   cross-speaker LOSO {loso:.3f}   "
              f"gap {seen - loso:+.3f}", flush=True)

    seed_seen, seed_loso = results["SEED"]
    chance = 1.0 / len(W.sc_words())
    print("\n" + "=" * 72, flush=True)
    print("SPEECH-COMMANDS ROBUST CROSS-SPEAKER LOSO — sharp all-pole VTL formant",
          flush=True)
    print("=" * 72, flush=True)
    print(f"  {'regime':12s} {'seen':>8s} {'LOSO':>8s} {'seen-LOSO gap':>14s} "
          f"{'LOSO lift':>11s}", flush=True)
    for name, _ in REGIMES:
        seen, loso = results[name]
        lift = loso - seed_loso
        print(f"  {name:12s} {seen:8.3f} {loso:8.3f} {seen - loso:14.3f} "
              f"{lift:+11.3f}", flush=True)

    cmvn_seen, cmvn_loso = results["+CMVN"]
    vtlc_seen, vtlc_loso = results["+CMVN+VTLc"]
    vtla_seen, vtla_loso = results["+CMVN+VTLa"]
    print("-" * 72, flush=True)
    print(f"  chance {chance:.3f}; SEED LOSO {seed_loso:.3f} "
          f"(seen {seed_seen:.3f}, gap {seed_seen - seed_loso:+.3f})", flush=True)
    print(f"  +CMVN LOSO {cmvn_loso:.3f} (lift over SEED {cmvn_loso - seed_loso:+.3f}) "
          f"— the dominant lever", flush=True)
    # the decisive comparison: VTL ON TOP OF CMVN, coarse vs sharp formant.
    coarse_on_cmvn = vtlc_loso - cmvn_loso
    sharp_on_cmvn = vtla_loso - cmvn_loso
    print(f"  +VTL(coarse gammatone) on CMVN: {coarse_on_cmvn:+.3f} LOSO "
          f"(LOSO {vtlc_loso:.3f}) — the cue that barely moved", flush=True)
    print(f"  +VTL(SHARP all-pole)   on CMVN: {sharp_on_cmvn:+.3f} LOSO "
          f"(LOSO {vtla_loso:.3f}) — the sharp-formant test", flush=True)
    bite = sharp_on_cmvn - coarse_on_cmvn
    print(f"  sharp-vs-coarse VTL delta (does the sharp formant bite further): "
          f"{bite:+.3f}", flush=True)

    # cross-the-wall check: does the sharp VTL CLOSE the seen-vs-cross gap?
    print(f"  residual seen-vs-cross gap: +CMVN {cmvn_seen - cmvn_loso:+.3f}, "
          f"+VTLc {vtlc_seen - vtlc_loso:+.3f}, +VTLa {vtla_seen - vtla_loso:+.3f}",
          flush=True)

    if sharp_on_cmvn > 0.02 and bite > 0.01:
        print(f"  => YES: the SHARP all-pole formant makes the VTL lever BITE — "
              f"+{sharp_on_cmvn:.3f} LOSO on top of CMVN ({bite:+.3f} vs the coarse "
              f"VTL). Sharpening the formant, not a new normalization, is the move.",
              flush=True)
    elif sharp_on_cmvn > coarse_on_cmvn + 0.01:
        print(f"  => PARTIAL: the sharp formant moves the VTL lever further than the "
              f"coarse one ({bite:+.3f}) but the absolute on-CMVN lift "
              f"({sharp_on_cmvn:+.3f}) is modest.", flush=True)
    else:
        print(f"  => NO: the sharp all-pole formant does NOT make the VTL lever bite "
              f"further on top of CMVN ({sharp_on_cmvn:+.3f} vs coarse "
              f"{coarse_on_cmvn:+.3f}). The residual is deeper than formant sharpness.",
              flush=True)
    print("[MARKER] ALLPOLE_VTL_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
