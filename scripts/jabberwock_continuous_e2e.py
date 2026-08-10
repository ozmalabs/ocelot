"""End-to-end continuous recognition: the jabberwock's local_min SEGMENTER ->
strong PEEL+VELOCITY feature per unit -> open-vocab nearest-exemplar RECOGNISER -> WER.

One feature space throughout (cochleagram band-trajectory), so no A1-patch mismatch:
  1. frame each utterance (band_trajectory + CMVN), quantise to units (k-means).
  2. SEGMENT with the agent's graph-native local_min chunker (~1 unit/word, c82b67d8).
  3. each unit-chunk's frames -> strong feature (per-frame L2 -> peel segment env ->
     velocity -> fixed length) -> embedding.
  4. RECOGNISE: cosine to nearest TRAIN exemplar (open vocab; exemplars labelled by
     proportional alignment of train units to transcript words). Collapse dups -> hyp.
WER vs reference, head-to-head with NO-segmentation (whole-utterance) as the floor proxy.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_continuous_e2e.py [n_train] [n_test]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
import scripts.librispeech_wer as L
from scripts.context_invariant_librispeech_accept import frames_of, kmeans, quantize, words_of
from domains.forward_segmentation import forward_segment

Lf = 12


def _cmvn(M):
    M = np.asarray(M, float)
    return (M - M.mean(0)) / (M.std(0) + 1e-6)


def _rs(X, L=Lf):
    m = len(X)
    if m == L:
        return X
    idx = np.linspace(0, m - 1, L); lo = np.floor(idx).astype(int); hi = np.clip(lo + 1, 0, m - 1)
    w = (idx - lo)[:, None]
    return X[lo] * (1 - w) + X[hi] * w


def _emb(Mc):
    Mc = np.asarray(Mc, float)
    if len(Mc) < 2:
        Mc = np.vstack([Mc, Mc])
    A = Mc / np.clip(np.linalg.norm(Mc, axis=1, keepdims=True), 1e-9, None)   # per-frame L2
    P = A - A.mean(0)                                                         # peel segment env
    V = np.vstack([np.zeros((1, A.shape[1])), np.diff(P, axis=0)])            # velocity
    F = np.concatenate([_rs(P), _rs(V)], axis=1).reshape(-1)
    return F / max(np.linalg.norm(F), 1e-9)


def _segment(sub, M, C):
    units = quantize(M, C)
    res = forward_segment(sub, [units], n_passes=1, boundary_mode="local_min", bidirectional=True)
    chunks = (res["chunked"] or [[(u,) for u in units]])[0]
    spans, s = [], 0
    for c in chunks:
        spans.append((s, s + len(c))); s += len(c)
    return spans                                   # frame spans per unit-chunk


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    pairs = L.gather_pairs(limit=n_train + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    train = [p for p in pairs if p[1] not in test_spk][:n_train]
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    print("=" * 88)
    print("END-TO-END continuous: agent local_min segmenter -> peel+velocity -> exemplar recogniser")
    print("=" * 88)
    print(f"  train {len(train)} / test {len(test)} (held-out speakers)")

    sub = srs.Substrate()
    t0 = time.time()
    Mtr = []
    for i, (path, sp, ch, ut, tr) in enumerate(train):
        try:
            x, fs = L.load_flac(path); Mtr.append((_cmvn(frames_of(x, fs)), words_of(tr)))
        except Exception:
            continue
        if (i + 1) % 50 == 0:
            print(f"   framed train {i+1}/{len(train)} [{time.time()-t0:.0f}s]", flush=True)
    C = kmeans(np.concatenate([m for m, _ in Mtr], 0), 48)

    # build exemplars: segment each train utt, proportional-align units to words
    E, W = [], []
    for M, words in Mtr:
        if not words:
            continue
        spans = _segment(sub, M, C); nc = len(spans)
        for j, (a, b) in enumerate(spans):
            wi = min(int(j * len(words) / max(nc, 1)), len(words) - 1)
            E.append(_emb(M[a:b])); W.append(words[wi])
    E = np.array(E)
    print(f"  exemplars: {len(E)} (open vocab {len(set(W))} words)", flush=True)

    def transcribe(M, segmented):
        if segmented:
            spans = _segment(sub, M, C)
        else:
            spans = [(0, len(M))]
        out = []
        for a, b in spans:
            w = W[int((E @ _emb(M[a:b])).argmax())]
            if not out or out[-1] != w:
                out.append(w)
        return out

    def wer(segmented):
        te = ref = hyp = 0
        for (path, sp, ch, ut, tr) in test:
            try:
                x, fs = L.load_flac(path); M = _cmvn(frames_of(x, fs))
            except Exception:
                continue
            rf = words_of(tr); h = transcribe(M, segmented)
            te += L.levenshtein_words(rf, h); ref += len(rf); hyp += len(h)
        return te / max(ref, 1), hyp, ref

    seg_w, seg_h, ref = wer(True)
    no_w, no_h, _ = wer(False)
    print("\n" + "=" * 88)
    print(f"  NO segmentation (1 chunk/utt) : WER {no_w:.3f}  hyp/ref {no_h}/{ref} = {no_h/max(ref,1):.2f}x")
    print(f"  + agent SEGMENTER (local_min)  : WER {seg_w:.3f}  hyp/ref {seg_h}/{ref} = {seg_h/max(ref,1):.2f}x")
    print(f"  (old valley+exact pipeline floor: ~0.93, hyp/ref 0.26x)")
    print("=" * 88)
    print(f"  delta WER (no-seg - seg) = {no_w-seg_w:+.3f}  "
          f"-> {'segmentation + strong feature recover words' if no_w-seg_w > 0.02 else 'still limited'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
