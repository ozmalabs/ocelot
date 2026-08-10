"""prosody_syllable_frame — add the PROSODY / SYLLABLE-STRUCTURE frame to the
multi-frame weighted-admissibility collapse and test whether it lifts cross-speaker.

THE FRAME (the cheapest, highest-constraint one): "how many + what type of
syllables." From the held-out clip's audio, an OWNED envelope-DSP extractor reads
the syllable COUNT (+ a coarse stress position); the lexicon (a stated English
pronunciation dictionary, domains.prosody_syllable.WORD_SYLLABLES) gives each
vocab word's KNOWN count. The PROSODY frame is a SOFT EXCLUDER over the vocab:
words whose dictionary count mismatches the extracted count are carved (graded by
how far off); matching words abstain. It is COUPLED to the lexical frame (carves
the candidate word by its syllable shape), NOT orthogonal.

THE TEST (cross-speaker, held-out speakers never banked) — three conditions on the
SAME real test items (the same per-item acoustic DTW read, computed ONCE):
  (a) ACOUSTIC-ONLY              — acoustic soft-excluder argmax (single frame).
  (b) MULTI-FRAME WITHOUT PROSODY — acoustic + real n-gram (context + future sheaf),
                                    weighted-admissibility collapse (the existing).
  (c) MULTI-FRAME WITH PROSODY    — (b) + the prosody/syllable soft excluder added
                                    to the SAME weighted-admissibility collapse.
Report (a) vs (b) vs (c), the LIFT from adding prosody, and the EXTRACTION COST
(envelope DSP time vs the acoustic DTW time). Also report the raw cross-speaker
syllable-COUNT accuracy of the extractor (the KILL diagnostic).

PREDICTION: the syllable frame lifts cross-speaker (carves the word by syllable
count, a cheap strong constraint) and costs ~nothing vs the DTW.
KILL: if the cross-speaker syllable-count extraction is unreliable / the vocab's
syllable counts are too uniform to constrain, so prosody does NOT help — say so
plainly with the syllable-count accuracy as evidence.

DONKEY: syllable extractor = owned envelope DSP (peak-count + dip + prominence, no
net/fit; domains.prosody_syllable); word syllable structures = lexicon/dictionary
(world knowledge); prosody frame = owned soft excluder; collapse = the agent's
weighted_admissibility (frame_inference_v2). Held-out SPEAKERS realise the audio,
never banked. The dictionary never sees audio; the LM never sees audio.

Run: python -m scripts.prosody_syllable_frame [n_train_spk] [n_held_spk] \
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
# Build the cross-speaker test set ONCE. Each entry carries the per-item acoustic
# excluder (the expensive DTW, done once), the real sentence item (real neighbours),
# the truth index, AND the prosody excluder + extracted/true syllable count for the
# SAME held-out clip (the cheap envelope DSP, also done once). The same set is then
# decoded under every condition.
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
    t_pros = 0.0
    n_syl_correct = 0
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
            # --- the expensive acoustic read (DTW 1-NN) ---
            ta = time.time()
            acou_e = UR.acoustic_excluder(x, fr, rel_bank, vocab, mode=mode)
            t_acou += time.time() - ta
            # --- the cheap prosody read (envelope peak-count) on the SAME clip ---
            tp = time.time()
            syl_count, syl_stress = P.extract_syllables(x)
            pros_e = P.prosody_excluder(syl_count, vocab,
                                        extracted_stress=syl_stress, use_stress=False)
            t_pros += time.time() - tp
            n_syl_correct += int(syl_count == P.word_count(w))
            test.append((acou_e, pros_e, it, vocab.index(w)))
            used += 1
            progressed = True
            if verbose and used % 500 == 0:
                print(f"    ... {used} items  (acou {t_acou:.0f}s / pros {t_pros:.2f}s)",
                      flush=True)
        if not progressed:
            break
    syl_acc = n_syl_correct / max(used, 1)
    return test, t_acou, t_pros, syl_acc


# ===========================================================================
# Decode one item under the three conditions. All share the cached acoustic
# excluder. (b)/(c) add the real n-gram frames (context + future sheaf) exactly as
# scripts.under_determined_real.collapse_item does; (c) additionally adds the
# prosody soft excluder to the SAME weighted-admissibility intersection.
# ===========================================================================

def decode_item(acou_e, pros_e, item, fwd, bwd, fwd2, bwd2, vocab,
                lm_weight=1.0, sheaf_depth=2, pros_weight=1.0):
    K = len(vocab)
    # --- (a) acoustic-only ---
    g_acoustic = int(np.argmax(acou_e))

    # --- build the real n-gram excluders (same as under_determined_real) ---
    ctx_e = U.context_excluder(item["prev"], fwd, vocab)
    excl = [acou_e, ctx_e]
    wv = [1.0, lm_weight]
    if sheaf_depth >= 1:
        excl.append(U.future_excluder(item["next"], bwd, vocab)); wv.append(lm_weight)
    if sheaf_depth >= 2:
        excl.append(U.future2_excluder(item["next2"], bwd2, vocab)); wv.append(lm_weight)

    # --- (b) multi-frame WITHOUT prosody ---
    g_noprosody = int(np.argmax(F2.weighted_admissibility(excl, wv)))

    # --- (c) multi-frame WITH prosody (add the prosody excluder to the SAME set) ---
    excl_p = excl + [pros_e]
    wv_p = wv + [pros_weight]
    g_prosody = int(np.argmax(F2.weighted_admissibility(excl_p, wv_p)))

    return g_acoustic, g_noprosody, g_prosody


def run(test, vocab, fwd, bwd, fwd2, bwd2, lm_weight=1.0, sheaf_depth=2,
        pros_weight=1.0):
    agg = {"acoustic": [0, 0], "noprosody": [0, 0], "prosody": [0, 0]}
    for acou_e, pros_e, it, truth in test:
        ga, gb, gc = decode_item(acou_e, pros_e, it, fwd, bwd, fwd2, bwd2, vocab,
                                 lm_weight=lm_weight, sheaf_depth=sheaf_depth,
                                 pros_weight=pros_weight)
        agg["acoustic"][0] += int(ga == truth); agg["acoustic"][1] += 1
        agg["noprosody"][0] += int(gb == truth); agg["noprosody"][1] += 1
        agg["prosody"][0] += int(gc == truth); agg["prosody"][1] += 1
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
    print("PROSODY / SYLLABLE-STRUCTURE FRAME — cross-speaker multi-frame collapse",
          flush=True)
    print("=" * 84, flush=True)

    # --- DONKEY AUDIT of the dictionary: the vocab's syllable-count distribution. ---
    import collections as _c
    dist = _c.Counter(P.word_count(w) for w in vocab)
    print(f"[dict] {len(P.WORD_SYLLABLES)} words; SC-vocab ({K}) syllable-count "
          f"distribution: {dict(sorted(dist.items()))}", flush=True)
    print(f"[dict] source = stated English pronunciation dictionary "
          f"(domains.prosody_syllable.WORD_SYLLABLES; CMUdict unavailable offline). "
          f"e.g. " + ", ".join(f"{w}:{P.word_count(w)}"
                               for w in ["no", "seven", "visual", "zero"] if w in vocab),
          flush=True)
    # how hard does the count alone partition? mean candidates surviving a count match.
    surv = np.mean([sum(P.word_count(v) == P.word_count(w) for v in vocab)
                    for w in vocab])
    print(f"[dict] mean candidates SURVIVING an exact syllable-count match = "
          f"{surv:.1f}/{K} (a count match alone carves the vocab to ~{surv/K:.0%}).",
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

    # --- build the cross-speaker test set ONCE (acoustic DTW + prosody DSP). ---
    print("[test] building cross-speaker test set (acoustic reads + prosody reads) ...",
          flush=True)
    test, t_acou, t_pros, syl_acc = build_test_set(
        train, held, vocab, items, rel_bank, max_items=max_items)
    n = len(test)
    print(f"[test] {n} cross-speaker test items", flush=True)
    print(f"[cost] acoustic DTW reads: {t_acou:.1f}s total ({1000*t_acou/max(n,1):.1f} "
          f"ms/item)  |  prosody envelope reads: {t_pros:.2f}s total "
          f"({1000*t_pros/max(n,1):.2f} ms/item)  |  prosody is "
          f"{t_acou/max(t_pros,1e-6):.0f}x CHEAPER than the acoustic frame", flush=True)
    print(f"[KILL diagnostic] cross-speaker syllable-COUNT extraction accuracy = "
          f"{syl_acc:.3f} (extracted count == dictionary count, over the test items)",
          flush=True)

    # === THE COMPARISON (principled cell: lm_w=1.0, full sheaf, pros_w=1.0). ===
    print("\n" + "=" * 84, flush=True)
    print("CROSS-SPEAKER ACCURACY — (a) acoustic-only | (b) +n-gram | (c) +n-gram+prosody",
          flush=True)
    print(f"  chance {chance:.3f}  vocab {K}  held {len(held)} speakers  n={n}", flush=True)
    print("=" * 84, flush=True)

    r = run(test, vocab, fwd, bwd, fwd2, bwd2, lm_weight=1.0, sheaf_depth=2,
            pros_weight=1.0)
    a = r["acoustic"][0]; b = r["noprosody"][0]; c = r["prosody"][0]
    print(f"  (a) acoustic-only              = {a:.3f}", flush=True)
    print(f"  (b) multi-frame WITHOUT prosody = {b:.3f}   (over acoustic {b-a:+.3f})",
          flush=True)
    print(f"  (c) multi-frame WITH prosody    = {c:.3f}   (over (b) PROSODY LIFT "
          f"{c-b:+.3f})", flush=True)

    # --- prosody-weight surface (REPORTED, the verdict reads pros_w=1.0). ---
    print("\n  -- prosody-weight surface (lm_w=1.0, sheaf=2; verdict reads pros_w=1.0) --",
          flush=True)
    print(f"  {'pros_w':>7s} {'(b)noProsody':>13s} {'(c)Prosody':>11s} {'lift':>8s}",
          flush=True)
    lift_at_1 = None
    for pw in [0.5, 1.0, 2.0, 4.0]:
        rp = run(test, vocab, fwd, bwd, fwd2, bwd2, lm_weight=1.0, sheaf_depth=2,
                 pros_weight=pw)
        bb = rp["noprosody"][0]; cc = rp["prosody"][0]
        print(f"  {pw:7.1f} {bb:13.3f} {cc:11.3f} {cc-bb:+8.3f}", flush=True)
        if pw == 1.0:
            lift_at_1 = cc - bb

    # --- prosody added DIRECTLY to the acoustic (no n-gram), to isolate its carve. ---
    agg = {"ac": [0, 0], "acp": [0, 0]}
    for acou_e, pros_e, it, truth in test:
        ga = int(np.argmax(acou_e))
        gp = int(np.argmax(F2.weighted_admissibility([acou_e, pros_e], [1.0, 1.0])))
        agg["ac"][0] += int(ga == truth); agg["ac"][1] += 1
        agg["acp"][0] += int(gp == truth); agg["acp"][1] += 1
    ac = agg["ac"][0] / max(agg["ac"][1], 1)
    acp = agg["acp"][0] / max(agg["acp"][1], 1)
    print(f"\n  isolate: acoustic {ac:.3f} -> acoustic+prosody {acp:.3f} "
          f"(prosody alone over acoustic {acp-ac:+.3f})", flush=True)

    # === VERDICT ===
    print("\n" + "=" * 84, flush=True)
    print("VERDICT — does the cheap syllable frame lift cross-speaker, at what cost?",
          flush=True)
    print("=" * 84, flush=True)
    BAR = 0.01
    cost_ratio = t_acou / max(t_pros, 1e-6)
    print(f"  prosody lift over the multi-frame baseline (pros_w=1.0): {lift_at_1:+.3f}",
          flush=True)
    print(f"  prosody lift over the acoustic alone:                    {acp-ac:+.3f}",
          flush=True)
    print(f"  extraction cost: prosody {1000*t_pros/max(n,1):.2f} ms/item vs acoustic "
          f"{1000*t_acou/max(n,1):.1f} ms/item ({cost_ratio:.0f}x cheaper)", flush=True)
    print(f"  cross-speaker syllable-count extraction accuracy: {syl_acc:.3f}", flush=True)
    print("-" * 84, flush=True)
    if lift_at_1 is not None and lift_at_1 > BAR:
        print(f"  CONFIRMED: the cheap syllable-structure frame LIFTS cross-speaker "
              f"recognition by {lift_at_1:+.3f} over the multi-frame baseline at "
              f"~{cost_ratio:.0f}x less cost than the acoustic frame — it carves the "
              f"word by syllable count (a strong cheap constraint), coupled to the "
              f"lexical frame.", flush=True)
    else:
        print(f"  KILL: the syllable frame does NOT lift cross-speaker past the {BAR} "
              f"bar ({lift_at_1:+.3f}). Evidence: cross-speaker syllable-count "
              f"extraction accuracy is {syl_acc:.3f}", flush=True)
        if surv / K > 0.7:
            print(f"  ...and the vocab's syllable counts are too UNIFORM "
                  f"({surv:.1f}/{K} survive a count match) to constrain much.",
                  flush=True)
        print(f"  (extraction is still ~{cost_ratio:.0f}x cheaper than the acoustic, "
              f"so the cost is not the issue — the constraint/extraction is.", flush=True)
    print(f"  CHAIN: acoustic {a:.3f} | +n-gram {b:.3f} | +n-gram+prosody {c:.3f} "
          f"| chance {chance:.3f}", flush=True)

    print("\n[MARKER] PROSODY_SYLLABLE_FRAME_COMPLETED", flush=True)


if __name__ == "__main__":
    main()
