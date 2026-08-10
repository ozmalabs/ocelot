"""Is the single-word unit the limit? Test by FREEING it: a span-lattice decode where
each recognition unit is 1..K adjacent segmenter chunks (not fixed at one), scored by
the learned recogniser, and a bigram-LM Viterbi over the lattice CHOOSES how many
chunks form each word. Head-to-head vs the hard 1-chunk = 1-word decode, same audio,
same frontend, same prominent segmenter.

If variable-span beats hard-1-chunk, the binding constraint was the WORD-UNIT
assumption (a word split across chunks can be re-merged by the decoder), not the
per-chunk classifier and not the segmenter boundary precision alone.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
from collections import defaultdict
import scripts.librispeech_wer as L
from scripts.jabberwock_lifts_speech_phonebank import _load
from scripts.jabberwock_reads_oov_from_phones import frames
from scripts.context_invariant_librispeech_accept import kmeans, quantize
from domains.forward_segmentation import forward_segment
from domains.learned_speech_recogniser import LearnedSpeechRecogniser, install_templates, feature

TOPK = 5
KMAX = 3            # a unit may span up to KMAX adjacent chunks


def _chunks(Ms, C):
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


def _collapse(ws):
    o = []
    for w in ws:
        if not o or o[-1] != w:
            o.append(w)
    return o


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    lam = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    train = _load("train-clean-100_*.pkl", 12)
    C = kmeans(np.concatenate([fr for _w, fr in train[:1500]], 0), 48)

    sub = srs.Substrate(); install_templates(sub)
    rec = LearnedSpeechRecogniser(sub)
    n_multi = sum(1 for w in rec._words if " " in w)
    # LM over ACTUAL single words (template labels may be multi-word units).
    svocab = sorted({w for w, _ in train})
    vi = {w: i for i, w in enumerate(svocab)}; V = len(svocab)
    big = np.ones((V, V)); prev = None
    for w, _ in train:
        if w in vi:
            if prev is not None:
                big[vi[prev], vi[w]] += 1
            prev = w
        else:
            prev = None
    logbg = np.log(big / big.sum(1, keepdims=True))

    def _bg(pw, w):
        return logbg[vi[pw], vi[w]] if (pw in vi and w in vi) else -8.0

    print(f"FREE THE UNIT (multi-scale): span-lattice (1..{KMAX} chunks) vs hard 1-chunk", flush=True)
    print(f"  templates={len(rec._words)} ({n_multi} multi-word units)", flush=True)

    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    Ms, refs = [], []
    for (path, sp_, ch, ut, tr) in test:
        try:
            Ms.append(frames(L.load_flac(path)[0])[0]); refs.append(L.normalise(tr))
        except Exception as e:
            print("  frame fail", e)
    all_spans = _chunks(Ms, C)

    def topk_span(M, a, b):
        emb = rec.encode(feature(M[a:b], np.asarray(M[a:b], float).mean(0)))
        return rec.ground_topk(emb, TOPK, qdur=b - a)        # duration-aware: span frames

    def hard(M, spans):
        out = []
        for a, b in spans:
            cand = topk_span(M, a, b)
            if cand:
                out.extend(cand[0][0].split())     # expand multi-word labels
        return _collapse(out)

    def lattice(M, spans):
        # boundaries 0..N over chunks; a unit = chunks[i:j], 1<=j-i<=KMAX. A unit's
        # label may be MULTI-WORD ("of the"); it emits that whole word sequence and the
        # LM state is its LAST actual word. dp[j] : {last_word: (score, (i, label))}.
        N = len(spans)
        if N == 0:
            return []
        dp = [dict() for _ in range(N + 1)]
        dp[0][None] = (0.0, (None, None, None))     # (score, (prev_i, prev_last, label))
        for j in range(1, N + 1):
            for i in range(max(0, j - KMAX), j):
                if not dp[i]:
                    continue
                a = spans[i][0]; b = spans[j - 1][1]
                for label, ac in topk_span(M, a, b):
                    ws = label.split()
                    if not ws:
                        continue
                    internal = lam * sum(_bg(ws[t], ws[t + 1]) for t in range(len(ws) - 1))
                    last = ws[-1]
                    for pw, (ps, _bp) in dp[i].items():
                        entry = lam * (_bg(pw, ws[0]) if pw is not None else 0.0)
                        sc = ps + ac + entry + internal
                        cur = dp[j].get(last)
                        if cur is None or sc > cur[0]:
                            dp[j][last] = (sc, (i, pw, label))
        if not dp[N]:
            return []
        last = max(dp[N], key=lambda k: dp[N][k][0])
        labels, j = [], N
        while j > 0:
            sc, (i, pw, label) = dp[j][last]
            labels.append(label); j, last = i, pw
        labels.reverse()
        words = []
        for lab in labels:
            words.extend(lab.split())
        lattice._nmulti += sum(1 for lab in labels if " " in lab)
        lattice._nunits += len(labels)
        lattice._precollapse += len(words)
        return _collapse(words)
    lattice._nmulti = lattice._nunits = lattice._precollapse = 0

    th = tl = ref = hh = hl = 0; t0 = time.time()
    for M, words, spans in zip(Ms, refs, all_spans):
        h = hard(M, spans); lt = lattice(M, spans)
        th += L.levenshtein_words(words, h); tl += L.levenshtein_words(words, lt)
        ref += len(words); hh += len(h); hl += len(lt)
    print("\n==========================================================")
    print(f"  HARD 1-chunk=1-word : WER {th/max(ref,1):.3f}  hyp/ref {hh/max(ref,1):.2f}x")
    print(f"  SPAN-LATTICE (1..{KMAX}) : WER {tl/max(ref,1):.3f}  hyp/ref {hl/max(ref,1):.2f}x")
    print(f"  delta (hard - lattice) = {(th-tl)/max(ref,1):+.3f}   [{time.time()-t0:.0f}s]")
    print(f"  lattice: {lattice._nunits} units, {lattice._nmulti} multi-word selected "
          f"({100*lattice._nmulti/max(lattice._nunits,1):.0f}%); "
          f"pre-collapse {lattice._precollapse} -> post {hl} words (ref {ref})")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
