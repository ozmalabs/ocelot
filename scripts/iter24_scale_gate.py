"""iter-24 GATE — does the agent's SELF-DERIVED SCALE-invariant relation lift the
perceptual ceiling, ESPECIALLY cross-speaker (the VTL-dominated number)?

The reasoning loop closed at iter-24: synthesize_gaps over the iter-23 RESIDUAL frame
fires the agent's acquired re_represent shape STRUCTURALLY onto the band-INDEX axis;
domains/scale_invariant_representation.py is the agent's COMPOSITION of that derived
gap (landmark-position SPACINGS via Argmax-peak + Minus -> the configuration of
relations that a uniform band-index (VTL) shift cancels by construction). This script
ENACTS + GATES it, head-to-head with iter-23 and the baselines.

SAME gold-span gate as scripts/iter23_relational_gate.py (faster-whisper gold word-
spans on LibriSpeech -> front-end -> within / cross-speaker DTW consistency,
shuffle-controlled). Front-ends compared:

  SURFACE        : raw gammatone band trajectory (the 0.20-ceiling baseline)
  RELATIONAL     : iter-23 value-difference (shift-invariant only — cancels LEVEL)
  SCALE-INV      : iter-24 landmark spacing (the agent's scale-invariant relation —
                   invariant to the VTL band-index shift)
  STACKED        : value-difference + landmark spacing (invariant to BOTH shift+scale)

CROSS-SPEAKER NN is the key number: VTL is the dominant cross nuisance, so if scale-
invariance works, cross should move off chance. Refs: surface within ~0.20 / cross
~chance; shallow-CNN gold-span 0.32; SSL 0.49.

NO tuning, no search. World-adapter only: forced alignment -> the agent's front-ends
-> the agent's DTW consistency metric. The scale-invariant numbers are the agent's
composition evaluated natively; this script reports them.

Run: python -m scripts.iter24_scale_gate [n_speakers] [utts_per_spk]
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as SL
from domains.relational_representation import apply_relational
from domains.scale_invariant_representation import apply_scale_invariant, apply_stacked
from scripts.continuous_speech_recognition import frames_of, words_of
from scripts.iter14_segmentation_consistency import (
    within_speaker_dtw, shuffle_within, intra_inter_separation,
)
from scripts.iter15_goldspan_gate import gold_spans, cross_separation, cross_nn


def _shuf(xs, seed=0):
    rng = random.Random(seed + 99)
    ys = list(xs)
    rng.shuffle(ys)
    return ys


def report_frontend(tag, chunks, probe):
    n_words = len(set(c[1] for c in chunks))
    wsep, wim, wxm, wnin, _ = intra_inter_separation(chunks)
    sh_ch = [(b, w, s) for (b, _, s), w in
             zip(chunks, _shuf([c[1] for c in chunks]))]
    wssep, _, _, _, _ = intra_inter_separation(sh_ch)
    wnn, wnt, _ = within_speaker_dtw(chunks, max_n=probe)
    wsh, _, _ = shuffle_within(chunks, max_n=probe)
    xsep, xim, xxm, xnin, _ = cross_separation(chunks)
    xnn, xnt = cross_nn(chunks)
    print(f"\n[{tag}]  segs={len(chunks)}  distinct words={n_words}  "
          f"chance~{1.0/max(n_words,1):.3f}")
    print(f"  WITHIN sep  {wsep:+.3f}  (intra {wim:.3f} < inter {wxm:.3f}? "
          f"n={wnin})  [shuffle {wssep:+.3f}]")
    print(f"  WITHIN NN   {wnn:.3f}   (n={wnt})  [shuffle {wsh:.3f}]")
    print(f"  CROSS  sep  {xsep:+.3f}  (intra {xim:.3f} < inter {xxm:.3f}? "
          f"n={xnin})")
    print(f"  CROSS  NN   {xnn:.3f}   (n={xnt})  [chance {1.0/max(n_words,1):.3f}]")
    return {"within_nn": wnn, "within_nn_shuf": wsh, "within_sep": wsep,
            "within_sep_shuf": wssep, "cross_nn": xnn, "cross_sep": xsep,
            "chance": 1.0 / max(n_words, 1)}


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    utts = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    probe = int(os.environ.get("PROBE", "450"))
    nsp = int(os.environ.get("NSPACINGS", "6"))
    random.seed(1)
    np.random.seed(1)

    pairs = SL.gather_pairs()
    by_spk = defaultdict(list)
    for p in pairs:
        by_spk[p[1]].append(p)
    spk_sorted = sorted(by_spk, key=lambda s: -len(by_spk[s]))[:n_spk]
    sel = []
    for s in spk_sorted:
        ps = list(by_spk[s])
        random.shuffle(ps)
        sel.extend(ps[:utts])
    print("=== iter-24 GATE: the agent's self-derived SCALE-invariant relation ===")
    print(f"LibriSpeech dev-clean: {len(spk_sorted)} speakers x <= {utts} utts "
          f"= {len(sel)} utts  (n_spacings={nsp})")

    from faster_whisper import WhisperModel
    wmodel = WhisperModel("tiny", device="cpu", compute_type="int8")

    print("\nForced alignment + gammatone framing...")
    t0 = time.time()
    raw = []
    gold_idx = []
    n_used = 0
    for path, sp, ch, ut, transcript in sel:
        try:
            x, fs = SL.load_flac_8k(path)
        except Exception:
            continue
        dur = len(x) / fs
        if dur < 0.4:
            continue
        M = frames_of(x, fs)
        nf = M.shape[0]
        if nf < 4:
            continue
        try:
            gs = gold_spans(wmodel, path)
        except Exception:
            gs = []
        spans = []
        for w, ts, te in gs:
            fa = int(round(ts / dur * nf))
            fb = int(round(te / dur * nf))
            fa = max(0, min(fa, nf - 1))
            fb = max(fa + 1, min(fb, nf))
            if len(w) >= 3 and fb - fa >= 2:
                spans.append((w, fa, fb))
        if not spans:
            continue
        words = words_of(transcript)
        raw.append((M, words, sp))
        gold_idx.append((len(raw) - 1, spans))
        n_used += 1
    print(f"  {n_used} utts framed + aligned ({time.time()-t0:.0f}s); "
          f"gold segs {sum(len(g[1]) for g in gold_idx)}")
    if n_used < 8:
        print("Too few usable utterances — aborting.")
        return

    def gold_chunks(normed):
        out = []
        for ridx, spans in gold_idx:
            M = normed[ridx][0]
            spk = normed[ridx][2]
            nf = M.shape[0]
            for w, fa, fb in spans:
                a = max(0, min(fa, nf - 1))
                b = max(a + 1, min(fb, nf))
                seg = np.asarray(M[a:b], dtype=np.float64)
                if seg.shape[0] >= 2:
                    out.append((seg, w, spk))
        return out

    surface = [(M, w, s) for M, w, s in raw]
    relational = [(apply_relational(M), w, s) for M, w, s in raw]
    scale_inv = [(apply_scale_invariant(M, n_spacings=nsp), w, s)
                 for M, w, s in raw]
    stacked = [(apply_stacked(M, n_spacings=nsp), w, s) for M, w, s in raw]

    print("\n" + "=" * 70)
    print("GOLD-SPAN consistency — SURFACE / RELATIONAL / SCALE-INV / STACKED")
    print("  metric = full-DTW intra/inter SEPARATION + same-word NN-acc")
    print("  refs: surface within ~0.20 / cross ~chance; shallow-CNN 0.32; SSL 0.49")
    print("=" * 70)

    results = {}
    for tag, normed in [("SURFACE (raw bands)", surface),
                        ("RELATIONAL (iter-23 value-diff)", relational),
                        ("SCALE-INV (iter-24 landmark spacing)", scale_inv),
                        ("STACKED (value-diff + spacing)", stacked)]:
        ch = gold_chunks(normed)
        results[tag] = report_frontend(tag, ch, probe)

    print("\n" + "=" * 70)
    print("GATE VERDICT — CROSS-speaker is the key (VTL-dominated)")
    print("=" * 70)
    surf = results["SURFACE (raw bands)"]
    sci = results["SCALE-INV (iter-24 landmark spacing)"]
    stk = results["STACKED (value-diff + spacing)"]
    print(f"  SURFACE    within-NN {surf['within_nn']:.3f}  cross-NN "
          f"{surf['cross_nn']:.3f}  (chance {surf['chance']:.3f})")
    print(f"  SCALE-INV  within-NN {sci['within_nn']:.3f} (shuf "
          f"{sci['within_nn_shuf']:.3f})  cross-NN {sci['cross_nn']:.3f}  "
          f"cross-sep {sci['cross_sep']:+.3f}")
    print(f"  STACKED    within-NN {stk['within_nn']:.3f} (shuf "
          f"{stk['within_nn_shuf']:.3f})  cross-NN {stk['cross_nn']:.3f}  "
          f"cross-sep {stk['cross_sep']:+.3f}")
    best_cross = max(sci["cross_nn"], stk["cross_nn"])
    if best_cross > surf["cross_nn"] + 0.03 and best_cross > sci["chance"] * 2:
        print("  >>> CROSS LIFT: scale-invariant moves cross-speaker NN off chance "
              "above surface. VTL band-index invariance helps cross-speaker.")
    elif max(sci["within_nn"], stk["within_nn"]) >= 0.32:
        print("  >>> WITHIN PASS (0.32) but check cross.")
    else:
        print("  >>> NO LIFT: scale-invariant does not move cross-speaker off chance "
              "above surface. Report residual honestly.")


if __name__ == "__main__":
    main()
