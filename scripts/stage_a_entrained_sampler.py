"""stage_a_entrained_sampler — Stage A of the active-transducer interface plan
(docs/active_transducer_interface_plan.md): the SELF-CLOCKING RHYTHMIC SAMPLER.

Tests the thesis "the passive interface failed the frame; the active interface
fixes it." (memory ozma_interface_layer_is_active_transduction).

The PASSIVE read (domains.prosody_syllable.extract_syllables) counts envelope
peaks — ~0.751 reliable cross-speaker (sonorant-internal dips under-count). The
ACTIVE read (domains.prosody_syllable.entrain_theta) is an entrained theta
oscillator whose PHASE emits syllable boundaries; it INTEGRATES over time so a
brief dip does not split a syllable. Both feed the SAME owned soft excluder
(prosody_excluder) into the SAME agent collapse (weighted_admissibility) — the
frame and the cognition are unchanged; only the READ differs.

MEASURES (cross-speaker, held-out speakers never banked; same harness/splits as
the f8576bbc KILL):
 (a) BOUNDARY RELIABILITY — cross-speaker syllable-COUNT accuracy of the entrained
     oscillator vs the passive peak-counter (the 0.751 baseline) + n.
 (b) THE FRAME (four-way) — acoustic-only | multi-frame-no-prosody |
     multi-frame-with-PASSIVE-syllable | multi-frame-with-OSCILLATOR-syllable,
     swept over the prosody weight. Does the oscillator-based frame LIFT where the
     passive one was flat-to-negative (-0.006)?

VERDICT: does the ACTIVE read beat the PASSIVE on (a) reliability AND (b) lift?
If reliability up but no lift -> the vocab uniformity, not the interface, is the
limiter (attribute correctly). If reliability NOT up -> rhythm isn't the fix.

DONKEY: oscillator = owned DSP transduction (no net/fit, frozen constants; it is
the SENSE). syllable frame + weighted-admissibility collapse unchanged (the
agent's). Held-out never banked. Reuses the under_determined_real harness.

Run: python -m scripts.stage_a_entrained_sampler [n_train_spk] [n_held_spk] \
        [n_per] [n_ctx] [max_items]
"""
from __future__ import annotations

import os
import sys
import random
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.self_directed_speech_world as W
import domains.frame_inference_v2 as F2
import domains.under_determined_real as U
import domains.prosody_syllable as P
import scripts.under_determined_real as UR
from scripts.frame_inference_v1 import infer_talker_frame


# ===========================================================================
# Build the cross-speaker test set ONCE. Per item, cache: the expensive acoustic
# DTW excluder; the real sentence item (real neighbours); the truth index; AND both
# syllable reads on the SAME held-out clip — the PASSIVE peak-count and the ACTIVE
# entrained-oscillator count — each turned into its own prosody soft excluder, plus
# the true dictionary count (for the reliability diagnostic). Same set decoded under
# every condition. The held-out clip sees no labels; the dictionary never sees audio.
# ===========================================================================

def build_test_set(train, held, vocab, items, rel_bank, max_items=3000,
                   seed=7, est="pctl", mode="frac", verbose=True):
    rng = random.Random(seed)
    by_word = {}
    for it in items:
        by_word.setdefault(it["target"], []).append(it)
    held_speakers = list(held.items())
    rng.shuffle(held_speakers)
    spk_frames = {}
    test = []
    t_acou = 0.0
    t_pass = 0.0
    t_osc = 0.0
    n_pass_correct = 0
    n_osc_correct = 0
    used = 0
    while used < max_items:
        progressed = False
        for spk, (ctx, word_clips) in held_speakers:
            if used >= max_items:
                break
            fr = spk_frames.get(spk)
            if fr is None:
                fr = infer_talker_frame(ctx, estimator=est)
                spk_frames[spk] = fr
            realizable = [w for w in word_clips if by_word.get(w)]
            if not realizable:
                continue
            w = rng.choice(realizable)
            it = rng.choice(by_word[w])
            x = rng.choice(word_clips[w])
            true_count = P.word_count(w)
            # --- the expensive acoustic read (DTW 1-NN) ---
            ta = time.time()
            acou_e = UR.acoustic_excluder(x, fr, rel_bank, vocab, mode=mode)
            t_acou += time.time() - ta
            # --- PASSIVE read: envelope peak-count (the 0.751 baseline) ---
            tp = time.time()
            pc, ps = P.extract_syllables(x)
            pass_e = P.prosody_excluder(pc, vocab, extracted_stress=ps,
                                        use_stress=False)
            t_pass += time.time() - tp
            n_pass_correct += int(pc == true_count)
            # --- ACTIVE read: entrained theta oscillator (the self-clocking read) ---
            to = time.time()
            oc, os_ = P.entrain_theta(x)
            osc_e = P.prosody_excluder(oc, vocab, extracted_stress=os_,
                                       use_stress=False)
            t_osc += time.time() - to
            n_osc_correct += int(oc == true_count)
            test.append((acou_e, pass_e, osc_e, it, vocab.index(w)))
            used += 1
            progressed = True
            if verbose and used % 500 == 0:
                print(f"    ... {used} items  (acou {t_acou:.0f}s / pass {t_pass:.2f}s "
                      f"/ osc {t_osc:.2f}s)", flush=True)
        if not progressed:
            break
    pass_acc = n_pass_correct / max(used, 1)
    osc_acc = n_osc_correct / max(used, 1)
    return test, t_acou, t_pass, t_osc, pass_acc, osc_acc


# ===========================================================================
# Decode one item under the four conditions. All share the cached acoustic
# excluder + n-gram excluders; the two prosody conditions differ ONLY in which
# syllable read built the prosody soft excluder.
# ===========================================================================

def decode_item(acou_e, pass_e, osc_e, item, fwd, bwd, fwd2, bwd2, vocab,
                lm_weight=1.0, sheaf_depth=2, pros_weight=1.0):
    g_acoustic = int(np.argmax(acou_e))

    ctx_e = U.context_excluder(item["prev"], fwd, vocab)
    excl = [acou_e, ctx_e]
    wv = [1.0, lm_weight]
    if sheaf_depth >= 1:
        excl.append(U.future_excluder(item["next"], bwd, vocab)); wv.append(lm_weight)
    if sheaf_depth >= 2:
        excl.append(U.future2_excluder(item["next2"], bwd2, vocab)); wv.append(lm_weight)

    g_noprosody = int(np.argmax(F2.weighted_admissibility(excl, wv)))
    g_passive = int(np.argmax(F2.weighted_admissibility(excl + [pass_e],
                                                        wv + [pros_weight])))
    g_oscillator = int(np.argmax(F2.weighted_admissibility(excl + [osc_e],
                                                           wv + [pros_weight])))
    return g_acoustic, g_noprosody, g_passive, g_oscillator


def run(test, vocab, fwd, bwd, fwd2, bwd2, lm_weight=1.0, sheaf_depth=2,
        pros_weight=1.0):
    agg = {"acoustic": [0, 0], "noprosody": [0, 0],
           "passive": [0, 0], "oscillator": [0, 0]}
    for acou_e, pass_e, osc_e, it, truth in test:
        ga, gb, gc, gd = decode_item(acou_e, pass_e, osc_e, it, fwd, bwd, fwd2, bwd2,
                                     vocab, lm_weight=lm_weight,
                                     sheaf_depth=sheaf_depth, pros_weight=pros_weight)
        agg["acoustic"][0] += int(ga == truth); agg["acoustic"][1] += 1
        agg["noprosody"][0] += int(gb == truth); agg["noprosody"][1] += 1
        agg["passive"][0] += int(gc == truth); agg["passive"][1] += 1
        agg["oscillator"][0] += int(gd == truth); agg["oscillator"][1] += 1
    return {k: (agg[k][0] / max(agg[k][1], 1), agg[k][1]) for k in agg}


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    if not os.path.isdir("/tmp/LibriSpeech"):
        print("LibriSpeech not found at /tmp/LibriSpeech — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    n_ctx = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    max_items = int(sys.argv[5]) if len(sys.argv) > 5 else 3000

    vocab = U.sc_vocab()
    K = len(vocab)
    chance = 1.0 / K

    print("=" * 84, flush=True)
    print("STAGE A — SELF-CLOCKING RHYTHMIC SAMPLER (entrained theta oscillator)",
          flush=True)
    print("  active read (entrain_theta) vs passive read (peak-count) -> same frame",
          flush=True)
    print("=" * 84, flush=True)

    # --- DONKEY AUDIT of the oscillator: owned DSP, integrates, no net. ---
    print("[donkey] oscillator = damped-driven / gradient-frequency phase-locked "
          "theta oscillator on the voiced-energy onset envelope.", flush=True)
    print(f"[donkey]   f0={P._THETA_F0_HZ}Hz band[{P._THETA_F_LO},{P._THETA_F_HI}]Hz "
          f"tau_f={P._TAU_F_S}s (slow -> INERTIA) K_phase={P._K_PHASE} "
          f"K_freq={P._K_FREQ}", flush=True)
    print(f"[donkey]   voice-gate {P._VOICE_GATE_FRAC} + {P._GATE_HOLD_MS}ms hold "
          f"(rides sonorant-internal dips); count = driven phase-wraps "
          f"(drive>={P._CYCLE_DRIVE_MIN}). Frozen constants, no net/fit.", flush=True)

    # --- DONKEY AUDIT of the dictionary + vocab uniformity (the f8576bbc concern). ---
    import collections as _c
    dist = _c.Counter(P.word_count(w) for w in vocab)
    surv = np.mean([sum(P.word_count(v) == P.word_count(w) for v in vocab)
                    for w in vocab])
    print(f"[dict] SC-vocab ({K}) syllable-count distribution: {dict(sorted(dist.items()))}",
          flush=True)
    print(f"[dict] mean candidates surviving an exact count match = {surv:.1f}/{K} "
          f"(~{surv/K:.0%} of vocab) — the uniformity that limited the passive frame.",
          flush=True)

    # --- the REAL language model (counted from LibriSpeech transcripts). ---
    print("[LM] counting REAL word n-gram from LibriSpeech transcripts ...", flush=True)
    fwd, bwd, fwd2, bwd2, n_utts = U.count_ngram()
    items = U.target_instances(vocab)
    print(f"[LM] {n_utts} real utterances; {len(items)} real test items", flush=True)

    # --- split + acoustic bank (built once). ---
    train, held = UR.build_split(vocab, n_train_spk, n_held_spk, n_per, n_ctx)
    print("[bank] building frame-relative acoustic bank ...", flush=True)
    t0 = time.time()
    rel_bank = UR.build_rel_bank(train, vocab, "pctl", "frac")
    nbank = sum(len(v) for v in rel_bank.values())
    print(f"[bank] {nbank} exemplars over {K} words ({time.time()-t0:.0f}s)", flush=True)

    # --- build the cross-speaker test set ONCE (acoustic DTW + both syllable reads). ---
    print("[test] building cross-speaker test set (acoustic + passive + oscillator reads) ...",
          flush=True)
    test, t_acou, t_pass, t_osc, pass_acc, osc_acc = build_test_set(
        train, held, vocab, items, rel_bank, max_items=max_items)
    n = len(test)
    print(f"[test] {n} cross-speaker test items", flush=True)

    # ===================================================================
    # (a) BOUNDARY RELIABILITY — the headline reliability comparison.
    # ===================================================================
    print("\n" + "=" * 84, flush=True)
    print("(a) BOUNDARY RELIABILITY — cross-speaker syllable-COUNT accuracy", flush=True)
    print("=" * 84, flush=True)
    print(f"  PASSIVE peak-counter  : {pass_acc:.3f}   (the f8576bbc 0.751 baseline)",
          flush=True)
    print(f"  ACTIVE  theta-oscillator: {osc_acc:.3f}   (over passive {osc_acc-pass_acc:+.3f})",
          flush=True)
    print(f"  n={n}", flush=True)
    rel_win = osc_acc > pass_acc
    print(f"  -> the ACTIVE read is {'MORE' if rel_win else 'NOT more'} reliable "
          f"cross-speaker than the passive peak-counter.", flush=True)
    print(f"  reads cost: acoustic {1000*t_acou/max(n,1):.1f} ms/item | passive "
          f"{1000*t_pass/max(n,1):.2f} ms/item | oscillator {1000*t_osc/max(n,1):.2f} "
          f"ms/item (both prosody reads << acoustic).", flush=True)

    # ===================================================================
    # (b) THE FRAME — four-way at the principled cell, then a weight sweep.
    # ===================================================================
    print("\n" + "=" * 84, flush=True)
    print("(b) THE FRAME — acoustic | +n-gram | +PASSIVE-syl | +OSCILLATOR-syl",
          flush=True)
    print(f"  chance {chance:.3f}  vocab {K}  held {len(held)} speakers  n={n}",
          flush=True)
    print("=" * 84, flush=True)
    r = run(test, vocab, fwd, bwd, fwd2, bwd2, lm_weight=1.0, sheaf_depth=2,
            pros_weight=1.0)
    a = r["acoustic"][0]; b = r["noprosody"][0]
    cpass = r["passive"][0]; cosc = r["oscillator"][0]
    print(f"  (1) acoustic-only                = {a:.3f}", flush=True)
    print(f"  (2) +n-gram (no syllable)        = {b:.3f}   (over acoustic {b-a:+.3f})",
          flush=True)
    print(f"  (3) +n-gram +PASSIVE syllable    = {cpass:.3f}   (lift over (2) "
          f"{cpass-b:+.3f})", flush=True)
    print(f"  (4) +n-gram +OSCILLATOR syllable = {cosc:.3f}   (lift over (2) "
          f"{cosc-b:+.3f})", flush=True)
    print(f"  ACTIVE-vs-PASSIVE frame delta     = {cosc-cpass:+.3f}", flush=True)

    # --- prosody-weight sweep: both reads, side by side. ---
    print("\n  -- prosody-weight sweep (lm_w=1.0, sheaf=2) --", flush=True)
    print(f"  {'pros_w':>7s} {'noProsody':>10s} {'PASSIVE':>9s} {'p-lift':>8s} "
          f"{'OSCILL':>9s} {'o-lift':>8s} {'osc-pass':>9s}", flush=True)
    osc_lift_at_1 = None
    pass_lift_at_1 = None
    best_osc_lift = -9.0
    for pw in [0.25, 0.5, 1.0, 2.0, 4.0]:
        rp = run(test, vocab, fwd, bwd, fwd2, bwd2, lm_weight=1.0, sheaf_depth=2,
                 pros_weight=pw)
        bb = rp["noprosody"][0]; pp = rp["passive"][0]; oo = rp["oscillator"][0]
        print(f"  {pw:7.2f} {bb:10.3f} {pp:9.3f} {pp-bb:+8.3f} {oo:9.3f} "
              f"{oo-bb:+8.3f} {oo-pp:+9.3f}", flush=True)
        best_osc_lift = max(best_osc_lift, oo - bb)
        if pw == 1.0:
            osc_lift_at_1 = oo - bb
            pass_lift_at_1 = pp - bb

    # ===================================================================
    # VERDICT
    # ===================================================================
    print("\n" + "=" * 84, flush=True)
    print("VERDICT — does the ACTIVE read beat the PASSIVE on (a) reliability AND "
          "(b) lift?", flush=True)
    print("=" * 84, flush=True)
    BAR = 0.01
    print(f"  (a) reliability: passive {pass_acc:.3f} -> oscillator {osc_acc:.3f} "
          f"({osc_acc-pass_acc:+.3f})", flush=True)
    print(f"  (b) frame lift @pros_w=1.0: passive {pass_lift_at_1:+.3f} | "
          f"oscillator {osc_lift_at_1:+.3f} (best osc over sweep {best_osc_lift:+.3f})",
          flush=True)
    print("-" * 84, flush=True)
    if rel_win and osc_lift_at_1 is not None and osc_lift_at_1 > BAR:
        print(f"  CONFIRMED: the ACTIVE self-clocking read is BOTH more reliable "
              f"({osc_acc-pass_acc:+.3f}) AND makes the syllable frame CARVE "
              f"({osc_lift_at_1:+.3f} lift) where the passive read was flat-to-negative. "
              f"The passive INTERFACE failed the frame; the active interface fixes it.",
              flush=True)
    elif rel_win:
        print(f"  PARTIAL: the ACTIVE read IS more reliable ({osc_acc-pass_acc:+.3f}) "
              f"but the frame STILL does not lift past {BAR} ({osc_lift_at_1:+.3f}). "
              f"=> the limiter is the VOCAB UNIFORMITY ({surv:.1f}/{K} survive a count "
              f"match) + the real n-gram already over-determining these items, NOT the "
              f"interface. Reliability was necessary but not sufficient on THIS vocab.",
              flush=True)
    else:
        print(f"  KILL: the entrained oscillator is NOT more reliable cross-speaker "
              f"than the peak-counter ({osc_acc:.3f} vs {pass_acc:.3f}). Entrainment "
              f"on isolated single-word clips has too little sustained rhythm to lock "
              f"to -> rhythm is not the fix in THIS (isolated-word) regime. The active "
              f"read needs connected speech (a real syllable train) to entrain.",
              flush=True)
    print(f"  CHAIN: acoustic {a:.3f} | +n-gram {b:.3f} | +passive-syl {cpass:.3f} "
          f"| +oscillator-syl {cosc:.3f} | chance {chance:.3f}", flush=True)

    print("\n[MARKER] STAGE_A_ENTRAINED_SAMPLER_COMPLETED", flush=True)


if __name__ == "__main__":
    main()
