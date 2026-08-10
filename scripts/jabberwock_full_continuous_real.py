"""FULL continuous pass on REAL audio (no concatenation shortcut): one consistent
cochleagram stream per utterance, segmented + recognised + LM-rescored.

  CLEAN exemplars (forced-aligned phonebank words, peel+velocity)
  TEST: real LibriSpeech utt -> phonebank cochleagram (frames(), feature-consistent)
        -> quantise -> agent local_min SEGMENTER (fresh substrate) -> per-chunk
        peel+velocity -> open-vocab top-k cosine -> bigram-LM Viterbi -> collapse -> WER.
Cross-speaker (held-out). Reports WER + chunks/ref-words for acoustic-only vs +LM.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
from collections import defaultdict
import scripts.librispeech_wer as L
from scripts.jabberwock_lifts_speech_phonebank import _load
from scripts.jabberwock_learned_encoder import _feat
from scripts.jabberwock_reads_oov_from_phones import frames
from scripts.context_invariant_librispeech_accept import kmeans, quantize
from domains.forward_segmentation import forward_segment

TOPK = 5


def _emb(fr):
    fr = np.asarray(fr, float)
    return _feat(fr, fr.mean(0))


def _spans_batch(Ms, C):
    """Segment ALL utterances together (corpus TP = the agent's statistical learning
    over the whole stream), with the prominent-trough boundary rule (local_min AND
    below median) — the grid-robust word-scale rule that fixes 100fps over-seg. The
    segmentation runs in the native primitive. Returns frame-spans per utterance."""
    seqs = [[int(u) for u in quantize(M, C)] for M in Ms]
    sub = srs.Substrate()
    chunked = forward_segment(sub, seqs, n_passes=1, boundary_mode="prominent")["chunked"]
    out = []
    for seq, chunks in zip(seqs, chunked or [[(u,) for u in s] for s in seqs]):
        sp, s = [], 0
        for c in chunks:
            sp.append((s, s + len(c))); s += len(c)
        out.append(sp)
    return out


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    train = _load("train-clean-100_*.pkl", 12)
    print("FULL CONTINUOUS (real audio):", flush=True)
    by = defaultdict(list)
    for w, fr in train:
        if len(by[w]) < per:
            by[w].append(fr)
    E, EW = [], []
    for w, frs in by.items():
        for fr in frs:
            E.append(_emb(fr)); EW.append(w)
    E = np.array(E); vocab = sorted(set(EW)); vi = {w: i for i, w in enumerate(vocab)}; V = len(vocab)
    C = kmeans(np.concatenate([fr for _w, fr in train[:1500]], 0), 48)
    big = np.ones((V, V)); prev = None
    for w, _ in train:
        if w in vi:
            if prev is not None:
                big[vi[prev], vi[w]] += 1
            prev = w
        else:
            prev = None
    logbg = np.log(big / big.sum(1, keepdims=True))
    print(f"  exemplars={len(E)} vocab={V}", flush=True)

    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    test = [p for p in pairs if p[1] in test_spk][:n_test]

    def topk(M, sp):
        out = []
        for a, b in sp:
            sims = E @ _emb(M[a:b]); best = {}
            for j in np.argsort(-sims)[:80]:
                w = EW[j]
                if w not in best:
                    best[w] = float(sims[j])
                if len(best) >= TOPK:
                    break
            out.append(best)
        return out

    def dec_ac(cs):
        o = []
        for c in cs:
            w = max(c, key=c.get)
            if not o or o[-1] != w:
                o.append(w)
        return o

    def dec_lm(cs, lam=2.0):
        if not cs:
            return []
        st = [list(c.items()) for c in cs]
        dp = [{w: s for w, s in st[0]}]; bp = [{w: None for w, _ in st[0]}]
        for t in range(1, len(st)):
            d, b = {}, {}
            for w, s in st[t]:
                bv, bw = -1e18, None
                for pw, pv in dp[t - 1].items():
                    sc = pv + lam * logbg[vi[pw], vi[w]]
                    if sc > bv:
                        bv, bw = sc, pw
                d[w] = bv + s; b[w] = bw
            dp.append(d); bp.append(b)
        w = max(dp[-1], key=dp[-1].get); seq = [w]
        for t in range(len(st) - 1, 0, -1):
            w = bp[t][w]; seq.append(w)
        seq.reverse(); o = []
        for w in seq:
            if not o or o[-1] != w:
                o.append(w)
        return o

    te_a = te_l = ref = ha = hl = 0; t0 = time.time()
    # Frame all utterances, then segment them TOGETHER (corpus TP), then recognise.
    Ms, refs = [], []
    for (path, sp_, ch, ut, tr) in test:
        try:
            Ms.append(frames(L.load_flac(path)[0])[0]); refs.append(L.normalise(tr))
        except Exception as e:
            print("  frame fail", e)
    all_spans = _spans_batch(Ms, C)
    for i, (M, words, spans) in enumerate(zip(Ms, refs, all_spans)):
        cs = topk(M, spans)
        a = dec_ac(cs); l = dec_lm(cs)
        te_a += L.levenshtein_words(words, a); te_l += L.levenshtein_words(words, l)
        ref += len(words); ha += len(a); hl += len(l)
        if (i + 1) % 10 == 0:
            print(f"   {i+1}/{len(Ms)} [{time.time()-t0:.0f}s]", flush=True)
    print("\n==========================================================")
    print(f"  acoustic-only : WER {te_a/max(ref,1):.3f}  hyp/ref {ha}/{ref} = {ha/max(ref,1):.2f}x")
    print(f"  + LM rescore  : WER {te_l/max(ref,1):.3f}  hyp/ref {hl}/{ref} = {hl/max(ref,1):.2f}x")
    print(f"  (old valley+exact floor ~0.93/0.26x; {time.time()-t0:.0f}s)")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
