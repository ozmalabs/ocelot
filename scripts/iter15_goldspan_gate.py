"""iter-15 STEP 1 (GATE) — is OUR front-end representation sufficient with GOLD
word spans?

The continuous-speech chunk-consistency bottleneck was diagnosed (model-mining,
mine_ssl_goldspan) as the BOUNDARIES, not the representation: an SSL+shallow-CNN
front-end given correct word boundaries jumps within-NN 0.142->0.492 (3.5x). This
gate asks the SAME question of the AGENT'S OWN front-end before we build a better
segmenter on top of it:

  Feed the agent's proven stack — gammatone band trajectory (frames_of) ->
  invariant_transform -> per-speaker CMVN — GOLD forced word-spans (faster-whisper
  word timestamps) on LibriSpeech, and measure same-word WITHIN-speaker +
  CROSS-speaker DTW consistency (the iter-14 separation + NN metric, shuffle-
  controlled).

GATE DECISION (stated up front, not tuned to the outcome):
  * within-NN ~0.3-0.5  -> the representation is PROVEN sufficient with gold spans;
    the entire remaining gap is the SEGMENTER -> proceed to Step 2 (build it).
  * within-NN far below ~0.3 -> the representation is weaker than even shallow CNN
    with gold spans -> STOP; report that the representation needs work too; do NOT
    build the segmenter on a false premise.

We report gold-span within/cross numbers against the agent's CURRENT proportional/
landmark consistency (~0.11 separation / ~0.13 NN).

World-adapter only: forced alignment (external I/O) -> gold frame spans -> the
agent's front-end -> the agent's DTW consistency metric. No agent reasoning in
Python; no tuning; shuffle controls reported on every number.

Run: python -m scripts.iter15_goldspan_gate [n_speakers] [utts_per_spk]
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as SL
from domains.invariant_units import invariant_transform, canonical_log_centroid
from scripts.continuous_speech_recognition import frames_of, words_of
from scripts.iter13_continuous_xspeaker import apply_per_speaker
from scripts.iter14_segmentation_consistency import (
    within_speaker_dtw, shuffle_within, intra_inter_separation, full_dtw,
)


# --------------------------------------------------------------------------
# Forced alignment: faster-whisper word timestamps -> (word, t0, t1) seconds.
# External I/O only.
# --------------------------------------------------------------------------

def gold_spans(wmodel, path):
    segs, _ = wmodel.transcribe(path, word_timestamps=True, language="en",
                                beam_size=1)
    out = []
    for s in segs:
        for w in (s.words or []):
            tok = "".join(ch for ch in w.word.lower()
                          if ch.isalpha() or ch == "'")
            if tok:
                out.append((tok, float(w.start), float(w.end)))
    return out


def cross_separation(chunks, max_pairs=2000, seed=0):
    """Same-word CROSS-speaker DTW separation (intra = same word, DIFFERENT
    speaker; inter = different word, any speaker). Mirror of the within-speaker
    intra_inter_separation but across speakers — the harder invariance test."""
    rng = random.Random(seed)
    by_w = defaultdict(list)
    for i, (_, w, s) in enumerate(chunks):
        if len(w) >= 4:
            by_w[w].append(i)
    intra = []
    for w, idxs in by_w.items():
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                if chunks[idxs[a]][2] != chunks[idxs[b]][2]:
                    intra.append((idxs[a], idxs[b]))
    rng.shuffle(intra)
    intra = intra[:max_pairs]
    allidx = [i for i, (_, w, _) in enumerate(chunks) if len(w) >= 4]
    inter = []
    for _ in range(len(intra) * 4):
        if len(inter) >= len(intra) or len(allidx) < 2:
            break
        i, j = rng.sample(allidx, 2)
        if chunks[i][1] != chunks[j][1]:
            inter.append((i, j))
    if not intra or not inter:
        return 0.0, 0.0, 0.0, len(intra), len(inter)
    idd = [full_dtw(chunks[i][0], chunks[j][0]) for i, j in intra]
    xdd = [full_dtw(chunks[i][0], chunks[j][0]) for i, j in inter]
    im, xm = float(np.mean(idd)), float(np.mean(xdd))
    return (xm - im) / xm if xm > 0 else 0.0, im, xm, len(intra), len(inter)


def cross_nn(chunks, max_q=140, seed=0):
    """Same-word CROSS-speaker nearest-neighbour accuracy (neighbour pool = a
    DIFFERENT speaker). The hard invariance probe."""
    rng = random.Random(seed)
    by_w = defaultdict(list)
    for i, (_, w, s) in enumerate(chunks):
        by_w[w].append(i)
    q = []
    for i, (_, w, s) in enumerate(chunks):
        if len(w) < 4:
            continue
        if any(chunks[j][2] != s for j in by_w[w] if j != i):
            q.append(i)
    rng.shuffle(q)
    q = q[:max_q]
    n = len(chunks)
    hit = tot = 0
    for i in q:
        s = chunks[i][2]
        best = (1e18, None)
        for j in range(n):
            if j == i or chunks[j][2] == s:
                continue
            d = full_dtw(chunks[i][0], chunks[j][0])
            if d < best[0]:
                best = (d, j)
        if best[1] is not None:
            tot += 1
            hit += (chunks[best[1]][1] == chunks[i][1])
    return (hit / tot if tot else 0.0), tot


def main():
    n_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    utts = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    probe = int(os.environ.get("PROBE", "450"))
    variant = os.environ.get("XN_VARIANT", "uVTLN+ps_CMVN+PR")
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
    print(f"=== iter-15 GATE: OUR front-end + GOLD word spans ===")
    print(f"LibriSpeech dev-clean: {len(spk_sorted)} speakers x <= {utts} utts "
          f"= {len(sel)} utts; XN variant={variant}")

    from faster_whisper import WhisperModel
    wmodel = WhisperModel("tiny", device="cpu", compute_type="int8")

    # ---- frame OUR front-end once per utterance, store raw band matrix + gold
    # spans (in frame units) + words + speaker. The gold span (t0,t1) sec maps to
    # frames by t/duration * n_frames (robust to frames_of's adaptive frame count).
    print("\nForced alignment + gammatone framing...")
    t0 = time.time()
    raw = []                              # (M_raw, words, spk) for canonical+CMVN
    gold_idx = []                         # parallel: [(spk, [(word, fa, fb)])]
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

    canonical = canonical_log_centroid([M for M, _, _ in raw])

    # build gold-span chunk sets under TWO front-ends:
    #   INV : per-utterance invariant_transform (the agent's BEFORE front-end)
    #   CMVN: per-speaker CMVN (the agent's proven cross-speaker fix)
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

    inv = [(invariant_transform(M, canonical), w, s) for M, w, s in raw]
    cmvn = apply_per_speaker(raw, canonical, variant)

    print("\n" + "=" * 66)
    print("GOLD-SPAN consistency on OUR front-end (within + cross speaker)")
    print("  metric = full-DTW intra/inter SEPARATION + same-word NN-acc")
    print("  agent CURRENT (proportional/landmark): sep ~+0.11, within-NN ~0.13")
    print("=" * 66)

    for tag, normed in [("INV (per-utt invariant)", inv),
                        (f"CMVN ({variant})", cmvn)]:
        ch = gold_chunks(normed)
        n_words = len(set(c[1] for c in ch))
        wsep, wim, wxm, wnin, _ = intra_inter_separation(ch)
        sh_ch = [(b, w, s) for (b, _, s), w in
                 zip(ch, _shuf([c[1] for c in ch]))]
        wssep, _, _, _, _ = intra_inter_separation(sh_ch)
        wnn, wnt, _ = within_speaker_dtw(ch, max_n=probe)
        wsh, _, _ = shuffle_within(ch, max_n=probe)
        xsep, xim, xxm, xnin, _ = cross_separation(ch)
        xnn, xnt = cross_nn(ch)
        print(f"\n[{tag}]  segs={len(ch)}  distinct words={n_words}  "
              f"chance~{1.0/max(n_words,1):.3f}")
        print(f"  WITHIN sep  {wsep:+.3f}  (intra {wim:.3f} < inter {wxm:.3f}? "
              f"n={wnin})  [shuffle {wssep:+.3f}]")
        print(f"  WITHIN NN   {wnn:.3f}   (n={wnt})  [shuffle {wsh:.3f}]")
        print(f"  CROSS  sep  {xsep:+.3f}  (intra {xim:.3f} < inter {xxm:.3f}? "
              f"n={xnin})")
        print(f"  CROSS  NN   {xnn:.3f}   (n={xnt})")

    print("\n" + "=" * 66)
    print("GATE VERDICT")
    print("=" * 66)
    # re-evaluate on the CMVN front-end (the proven one) for the gate decision.
    ch = gold_chunks(cmvn)
    wnn, _, _ = within_speaker_dtw(ch, max_n=probe)
    wsep, _, _, _, _ = intra_inter_separation(ch)
    print(f"  CMVN gold-span within-NN = {wnn:.3f}  within-sep = {wsep:+.3f}")
    if wnn >= 0.3:
        print("  >>> PASS: representation is SUFFICIENT with gold spans "
              "(within-NN >= 0.3).")
        print("      The remaining gap is the SEGMENTER -> proceed to Step 2.")
    elif wnn >= 0.22:
        print("  >>> MARGINAL: within-NN in [0.22, 0.3). Representation is in "
              "the gold-span band but below the 0.3 target; Step 2 is justified "
              "but the ceiling is modest. Proceed with that caveat.")
    else:
        print("  >>> FAIL: within-NN < 0.22 even with gold spans. The "
              "representation is weaker than shallow-CNN-with-gold-spans; the "
              "gap is NOT only segmentation. STOP — do not build the segmenter "
              "on a false premise; report representation needs work too.")


def _shuf(xs, seed=0):
    rng = random.Random(seed + 99)
    ys = list(xs)
    rng.shuffle(ys)
    return ys


if __name__ == "__main__":
    main()
