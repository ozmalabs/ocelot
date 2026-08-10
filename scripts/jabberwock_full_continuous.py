"""ASSEMBLE the full continuous pass — every rung wired, end to end:
  CLEAN exemplars (forced-aligned phonebank words, peel+velocity)  [da4473c6]
  -> agent's local_min SEGMENTER re-discovers word boundaries        [c82b67d8]
  -> open-vocab RECOGNITION (top-k cosine over clean exemplars)      [da4473c6]
  -> LM RESCORE (bigram over the corpus; Viterbi over the top-k)     [context lever]
  -> collapse -> WER.

Feature-consistent throughout (phonebank cochleagram), so no re-framing wall:
'continuous' test sentences are consecutive dev words (real corpus order) concatenated
into one frame stream; the segmenter does NOT see the word cuts. Cross-speaker (dev) vs
clean train exemplars. Reports WER: NO-seg | +agent-seg (acoustic-only) | +seg+LM.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_full_continuous.py [n_sent] [win] [per_word]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
from collections import Counter, defaultdict
from scripts.jabberwock_lifts_speech_phonebank import _load
from scripts.jabberwock_learned_encoder import _feat
from scripts.context_invariant_librispeech_accept import kmeans, quantize
from scripts.librispeech_wer import levenshtein_words
from domains.forward_segmentation import forward_segment

TOPK = 5


def _emb(fr):
    fr = np.asarray(fr, float)
    return _feat(fr, fr.mean(0))


def _segment(M, C):
    units = quantize(M, C)
    sub = srs.Substrate()                          # FRESH per call: forward_segment adds
    chunks = (forward_segment(sub, [units], n_passes=1, boundary_mode="local_min")["chunked"]
              or [[(u,) for u in units]])[0]        # nodes; a shared substrate accumulates
    spans, s = [], 0                                # stale Transitions -> over-segmentation.
    for c in chunks:
        spans.append((s, s + len(c))); s += len(c)
    return spans


def main():
    n_sent = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    win = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 15

    train = _load("train-clean-100_*.pkl", 12)
    dev = _load("dev-clean_*.pkl", 12)
    print("=" * 86)
    print("FULL CONTINUOUS PASS — clean exemplars + agent segmenter + open-vocab recog + LM")
    print("=" * 86)

    # clean forced-aligned exemplars + codebook for the segmenter
    by = defaultdict(list)
    for w, fr in train:
        if len(by[w]) < per:
            by[w].append(fr)
    E, EW = [], []
    for w, frs in by.items():
        for fr in frs:
            E.append(_emb(fr)); EW.append(w)
    E = np.array(E)
    vocab = sorted(set(EW)); vi = {w: i for i, w in enumerate(vocab)}; V = len(vocab)
    C = kmeans(np.concatenate([fr for _w, fr in train[:1500]], 0), 48)

    # bigram LM over the train word stream (corpus order)
    big = np.ones((V, V))
    prev = None
    for w, _ in train:
        if w in vi:
            if prev is not None:
                big[vi[prev], vi[w]] += 1
            prev = w
        else:
            prev = None
    logbg = np.log(big / big.sum(1, keepdims=True))
    print(f"  clean exemplars={len(E)}  vocab={V}", flush=True)

    # build 'continuous' test sentences from consecutive dev words (real order)
    sents = []
    i = 0
    while len(sents) < n_sent and i + win <= len(dev):
        seg = dev[i:i + win]; i += win
        M = np.vstack([fr for _w, fr in seg])
        sents.append((M, [w for w, _ in seg]))

    def topk_for(M, spans):
        out = []
        for a, b in spans:
            sims = E @ _emb(M[a:b])
            best = {}
            for j in np.argsort(-sims)[:60]:
                w = EW[j]
                if w not in best:
                    best[w] = float(sims[j])
                if len(best) >= TOPK:
                    break
            out.append(best)
        return out

    def decode_acoustic(cands):
        out = []
        for c in cands:
            w = max(c, key=c.get)
            if not out or out[-1] != w:
                out.append(w)
        return out

    def decode_lm(cands, lam):
        # Viterbi over per-chunk top-k candidate words; acoustic sim + lam*bigram.
        if not cands:
            return []
        states = [list(c.items()) for c in cands]      # [(word, sim)]
        dp = [{w: s for w, s in states[0]}]; bp = [{w: None for w, _ in states[0]}]
        for t in range(1, len(states)):
            d, b = {}, {}
            for w, s in states[t]:
                best, bw = -1e18, None
                for pw, pv in dp[t - 1].items():
                    sc = pv + lam * logbg[vi[pw], vi[w]]
                    if sc > best:
                        best, bw = sc, pw
                d[w] = best + s; b[w] = bw
            dp.append(d); bp.append(b)
        w = max(dp[-1], key=dp[-1].get); seq = [w]
        for t in range(len(states) - 1, 0, -1):
            w = bp[t][w]; seq.append(w)
        seq.reverse()
        out = []
        for w in seq:
            if not out or out[-1] != w:
                out.append(w)
        return out

    def run(mode):
        te = ref = hyp = 0
        for M, words in sents:
            spans = _segment(M, C) if mode != "noseg" else [(0, len(M))]
            cands = topk_for(M, spans)
            if mode == "lm":
                h = decode_lm(cands, 2.0)
            else:
                h = decode_acoustic(cands)
            te += levenshtein_words(words, h); ref += len(words); hyp += len(h)
        return te / max(ref, 1), hyp, ref

    t0 = time.time()
    no = run("noseg"); ac = run("seg"); lm = run("lm")
    print("\n" + "=" * 86)
    print(f"  NO segmentation             : WER {no[0]:.3f}  hyp/ref {no[1]}/{no[2]} = {no[1]/max(no[2],1):.2f}x")
    print(f"  + agent segmenter (acoustic): WER {ac[0]:.3f}  hyp/ref {ac[1]}/{ac[2]} = {ac[1]/max(ac[2],1):.2f}x")
    print(f"  + segmenter + LM rescore    : WER {lm[0]:.3f}  hyp/ref {lm[1]}/{lm[2]} = {lm[1]/max(lm[2],1):.2f}x")
    print(f"  ({time.time()-t0:.0f}s; old valley+exact pipeline floor ~0.93/0.26x)")
    print("=" * 86)
    print(f"  acoustic->+LM delta = {ac[0]-lm[0]:+.3f}   full chain vs no-seg = {no[0]-lm[0]:+.3f}")
    print("  Full continuous pass assembled: clean forced-aligned exemplars + the jabberwock's local_min")
    print("  segmenter + open-vocab top-k recognition + LM rescore. Every rung wired end to end.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
