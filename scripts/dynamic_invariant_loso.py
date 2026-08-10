"""dynamic_invariant_loso — does the agent's ORDER-N DYNAMIC formant invariant cross
the cross-speaker wall the STATIC formant levers left standing?

The sharp all-pole VTL run (docs/allpole_vtl_loso.md) lifted cross-speaker LOSO to
0.410 with the best STATIC source-normalized front end (CMVN + sharp all-pole VTL),
but a residual seen-vs-cross gap of +0.040 persists. That residual is DYNAMIC —
coarticulation / register / the WAY formants MOVE — which no static feature can
cancel: CMVN cancels per-band gain, the VTL invariant cancels the vocal-tract-length
SCALING of the static formant level, but the way F2 sweeps into a vowel (the
articulatory GESTURE) is what's left, and the static formant doesn't see it.

The named next move (NOT a new normalization, NOT a sweep): the agent's OWN
order-N-over-time operator (domains/order_n_concepts, recursive Minus over per-frame
samples) on the VTL-normalized sharp formant track — order-1 = transition VELOCITY
(the formant MOTION), order-2 = curvature. The gesture is shared across speakers even
when the absolute formants differ by VTL, so the order-N TRANSITION SHAPE of the
(already VTL-normalized) log-formant track should be MORE speaker-invariant than the
static formant level.

This reuses the SAME robust SC 40-speaker LOSO split (build_split / bank / measure
from sc_loso_frontend_norm, ungameable: 120 train / 40 held-out DISJOINT speakers, the
held-out clips NEVER banked, full-lexicon blind_guess) and A/Bs:

  (S)  SEED              — the 3-cue seed front end.
  (B)  STATIC-BEST       — +CMVN +sharp-allpole-VTL (the static-best = 0.410).
  (D1) +DYN(order-1)     — STATIC-BEST + the order-1 (velocity / transition) dynamic
                           VTL-formant invariant. The test: does the MOVING formant
                           lift cross-speaker LOSO ABOVE the static best?
  (D2) +DYN(order-2)     — STATIC-BEST + the order-2 (curvature) dynamic invariant
                           (ablation: velocity vs acceleration).
  (Do) +DYN(order-1) ONLY on CMVN (no static VTL) — the dynamic invariant standing
                           IN PLACE OF the static VTL, to isolate dynamics from level.

Everything else held fixed; the dynamic regimes differ from STATIC-BEST only by ADDING
the order-N-over-time cue. Any lift is the formant MOTION.

NO-DONKEY: the all-pole formant + VTL normalization + the order-N-over-time operator
are the agent's graph-resident composable DSP (Levinson-Durbin + root-finding + the
F_i - mean invariant + the order-N Minus-tree evaluated natively); SC load + the
speaker split are world-adapter mechanics; recognition is the agent's own blind_guess;
held-out speakers' clips are NEVER banked; LOSO is the ungameable yardstick.

Run: python -m scripts.dynamic_invariant_loso [n_train_spk] [n_held_spk] [n_per]
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

# the regimes A/B'd on the SAME robust real LOSO. The dynamic regimes differ from the
# STATIC-BEST only by ADDING the order-N-over-time formant invariant — so any lift is
# the formant MOTION (the dynamic gesture), not a new normalization.
REGIMES = [
    ("SEED", []),
    ("STATIC-BEST", ["cmvn_ear", "vtl_formant_allpole"]),        # the 0.410 static best
    ("+DYN(o1)", ["cmvn_ear", "vtl_formant_allpole", "vtl_formant_dynamic"]),
    ("+DYN(o2)", ["cmvn_ear", "vtl_formant_allpole", "vtl_formant_dynamic"]),  # order=2
    ("DYNonly(o1)", ["cmvn_ear", "vtl_formant_dynamic"]),         # dynamics w/o static VTL
]
# which regimes set the dynamic cue to order-2 (the ablation). All others use order-1.
ORDER2_REGIMES = {"+DYN(o2)"}


def fresh(active_cues, dyn_order=1):
    """A fresh substrate with the speech world + the named cues gated into the agent's
    graph-resident front end. World-adapter construction (no decision over state).
    dyn_order sets the order of the dynamic VTL-formant cue (1=velocity, 2=curvature)
    when it is gated in — the velocity-vs-acceleration ablation."""
    W.reset_caches()
    s = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=FS))
    pipe.attach(s)
    pipe._ensure_audio_pipeline(s)
    W.install_speech_world_rules(s)
    W.install_cell(s, "digit", "sc", "en")
    for c in s.nodes("Cue"):
        a = s.node(c)["attrs"]
        if a.get("name") in active_cues:
            s.set_attr(c, "active", 1.0)        # gate in the cue
            if a.get("name") == "vtl_formant_dynamic":
                s.set_attr(c, "order", float(dyn_order))
    return s, pipe


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20240608

    train_clips, seen_probe, loso_probe = build_split(n_train_spk, n_held_spk, n_per,
                                                      seed=seed)

    results = {}
    for name, cues in REGIMES:
        order = 2 if name in ORDER2_REGIMES else 1
        s, _pipe = fresh(cues, dyn_order=order)
        bank(s, train_clips)
        seen = measure(s, seen_probe)
        loso = measure(s, loso_probe)
        results[name] = (seen, loso)
        print(f"\n[{name:12s}] active cues={FE.n_active(s)}  "
              f"seen-speaker {seen:.3f}   cross-speaker LOSO {loso:.3f}   "
              f"gap {seen - loso:+.3f}", flush=True)

    seed_seen, seed_loso = results["SEED"]
    chance = 1.0 / len(W.sc_words())
    print("\n" + "=" * 74, flush=True)
    print("SPEECH-COMMANDS ROBUST CROSS-SPEAKER LOSO — DYNAMIC (order-N) formant invariant",
          flush=True)
    print("=" * 74, flush=True)
    print(f"  {'regime':12s} {'seen':>8s} {'LOSO':>8s} {'seen-LOSO gap':>14s} "
          f"{'LOSO lift':>11s}", flush=True)
    for name, _ in REGIMES:
        seen, loso = results[name]
        lift = loso - seed_loso
        print(f"  {name:12s} {seen:8.3f} {loso:8.3f} {seen - loso:14.3f} "
              f"{lift:+11.3f}", flush=True)

    stat_seen, stat_loso = results["STATIC-BEST"]
    d1_seen, d1_loso = results["+DYN(o1)"]
    d2_seen, d2_loso = results["+DYN(o2)"]
    do_seen, do_loso = results["DYNonly(o1)"]
    print("-" * 74, flush=True)
    print(f"  chance {chance:.3f}; SEED LOSO {seed_loso:.3f} "
          f"(seen {seed_seen:.3f}, gap {seed_seen - seed_loso:+.3f})", flush=True)
    print(f"  STATIC-BEST (CMVN+sharp-VTL) LOSO {stat_loso:.3f} "
          f"(seen {stat_seen:.3f}, gap {stat_seen - stat_loso:+.3f}) "
          f"— the static wall", flush=True)
    # the decisive comparison: the DYNAMIC invariant ON TOP OF the static best.
    dyn1_on_static = d1_loso - stat_loso
    dyn2_on_static = d2_loso - stat_loso
    print(f"  +DYN(order-1 velocity)  on STATIC-BEST: {dyn1_on_static:+.3f} LOSO "
          f"(LOSO {d1_loso:.3f}) — the formant MOTION", flush=True)
    print(f"  +DYN(order-2 curvature) on STATIC-BEST: {dyn2_on_static:+.3f} LOSO "
          f"(LOSO {d2_loso:.3f}) — the velocity-vs-accel ablation", flush=True)
    print(f"  DYN(o1)-only on CMVN (no static VTL): LOSO {do_loso:.3f} "
          f"(vs static VTL LOSO {stat_loso:.3f}) — dynamics standing in for level",
          flush=True)
    # cross-the-wall check: does the dynamic invariant CLOSE the seen-vs-cross gap?
    print(f"  residual seen-vs-cross gap: STATIC-BEST {stat_seen - stat_loso:+.3f}, "
          f"+DYN(o1) {d1_seen - d1_loso:+.3f}, +DYN(o2) {d2_seen - d2_loso:+.3f}",
          flush=True)

    best_dyn = max(dyn1_on_static, dyn2_on_static)
    best_gap = min(d1_seen - d1_loso, d2_seen - d2_loso)
    static_gap = stat_seen - stat_loso
    if best_dyn > 0.02:
        verdict = ("YES", f"the ORDER-N DYNAMIC formant invariant LIFTS cross-speaker "
                   f"LOSO +{best_dyn:.3f} ABOVE the static best — the formant MOTION "
                   f"carries cross-speaker-invariant structure the static formant can't.")
    elif best_dyn > 0.005:
        verdict = ("PARTIAL", f"the dynamic invariant moves cross-speaker LOSO further "
                   f"than the static best ({best_dyn:+.3f}) but the lift is modest.")
    else:
        verdict = ("NO", f"the order-N dynamic formant invariant does NOT lift "
                   f"cross-speaker LOSO above the static best ({best_dyn:+.3f}). The "
                   f"residual is deeper than formant DYNAMICS too.")
    crossed = best_gap < static_gap - 0.005
    wall = ("CLOSES the seen-vs-cross gap" if best_gap < 0.005 else
            ("NARROWS the gap" if crossed else "moves the wall but does not close it"))
    print(f"  => {verdict[0]}: {verdict[1]}", flush=True)
    print(f"  => WALL: the dynamic invariant {wall} "
          f"(static gap {static_gap:+.3f} -> best-dyn gap {best_gap:+.3f}).", flush=True)
    print("[MARKER] DYNAMIC_INVARIANT_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
