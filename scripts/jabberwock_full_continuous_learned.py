"""FULL continuous pass, head-to-head per-chunk recogniser: raw peel+velocity nearest-
exemplar (the old path) vs the LEARNED graph-native recogniser (bg-fit PCA->LDA encoder
+ class centroids, decision = native topk_dot / held Dot Term over WordCentroid nodes).

Same audio, same frontend, same prominent segmenter (corpus TP) for BOTH — only the
per-chunk recognition differs. Isolates the recognition-accuracy lever in the real
continuous setting. Reports WER (acoustic-only + bigram-LM Viterbi) and hyp/ref for each.
Cross-speaker (held-out dev-side speakers).
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
from domains.learned_speech_recogniser import LearnedSpeechRecogniser, install_templates, feature

TOPK = 5


def _emb_raw(fr):
    fr = np.asarray(fr, float)
    return _feat(fr, fr.mean(0))


def _spans_batch(Ms, C):
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


def _viterbi(cands, logbg, vi, lam=2.0):
    if not cands:
        return []
    st = [list(c.items()) for c in cands]
    dp = [{w: s for w, s in st[0]}]; bp = [{w: None for w, _ in st[0]}]
    for t in range(1, len(st)):
        d, b = {}, {}
        for w, s in st[t]:
            bv, bw = -1e18, None
            for pw, pv in dp[t - 1].items():
                sc = pv + lam * (logbg[vi[pw], vi[w]] if pw in vi and w in vi else -8.0)
                if sc > bv:
                    bv, bw = sc, pw
            d[w] = bv + s; b[w] = bw
        dp.append(d); bp.append(b)
    w = max(dp[-1], key=dp[-1].get); seq = [w]
    for t in range(len(st) - 1, 0, -1):
        w = bp[t][w]; seq.append(w)
    seq.reverse()
    o = []
    for w in seq:
        if not o or o[-1] != w:
            o.append(w)
    return o


def _collapse(words):
    o = []
    for w in words:
        if not o or o[-1] != w:
            o.append(w)
    return o


def _bigram(stream, vocab):
    vi = {w: i for i, w in enumerate(vocab)}; V = len(vocab)
    big = np.ones((V, V)); prev = None
    for w in stream:
        if w in vi:
            if prev is not None:
                big[vi[prev], vi[w]] += 1
            prev = w
        else:
            prev = None
    return np.log(big / big.sum(1, keepdims=True)), vi


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    train = _load("train-clean-100_*.pkl", 12)
    print("FULL CONTINUOUS — raw-exemplar vs LEARNED recogniser (same segmentation):", flush=True)

    # OLD path: raw peel+velocity exemplars
    by = defaultdict(list)
    for w, fr in train:
        if len(by[w]) < per:
            by[w].append(fr)
    E, EW = [], []
    for w, frs in by.items():
        for fr in frs:
            E.append(_emb_raw(fr)); EW.append(w)
    E = np.array(E)
    C = kmeans(np.concatenate([fr for _w, fr in train[:1500]], 0), 48)
    train_stream = [w for w, _ in train]
    logbg_old, vi_old = _bigram(train_stream, sorted(set(EW)))
    print(f"  raw exemplars={len(E)} vocab={len(vi_old)}", flush=True)

    # NEW path: the learned graph-native recogniser (booted from the seed)
    sub = srs.Substrate(); install_templates(sub)
    rec = LearnedSpeechRecogniser(sub)
    logbg_new, vi_new = _bigram(train_stream, rec._words)
    print(f"  learned templates={len(rec._words)} (encoder {rec.lda.shape[1]}d)", flush=True)

    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    test = [p for p in pairs if p[1] in test_spk][:n_test]

    Ms, refs = [], []
    for (path, sp_, ch, ut, tr) in test:
        try:
            Ms.append(frames(L.load_flac(path)[0])[0]); refs.append(L.normalise(tr))
        except Exception as e:
            print("  frame fail", e)
    all_spans = _spans_batch(Ms, C)

    def run():
        oa = ol = ona = onl = ref = 0
        ha = hl = nha = nhl = 0
        t0 = time.time()
        for M, words, spans in zip(Ms, refs, all_spans):
            old_c, new_c = [], []
            for a, b in spans:
                # OLD: raw nearest-exemplar top-k
                sims = E @ _emb_raw(M[a:b]); best = {}
                for j in np.argsort(-sims)[:80]:
                    if EW[j] not in best:
                        best[EW[j]] = float(sims[j])
                    if len(best) >= TOPK:
                        break
                old_c.append(best)
                # NEW: learned recogniser top-k (encode -> native topk_dot)
                emb = rec.encode(feature(M[a:b], np.asarray(M[a:b], float).mean(0)))
                new_c.append(dict(rec.ground_topk(emb, TOPK)))
            oa_h = _collapse([max(c, key=c.get) for c in old_c]) if old_c else []
            ol_h = _viterbi(old_c, logbg_old, vi_old)
            na_h = _collapse([max(c, key=c.get) for c in new_c]) if new_c else []
            nl_h = _viterbi(new_c, logbg_new, vi_new)
            oa += L.levenshtein_words(words, oa_h); ol += L.levenshtein_words(words, ol_h)
            ona += L.levenshtein_words(words, na_h); onl += L.levenshtein_words(words, nl_h)
            ref += len(words); ha += len(oa_h); hl += len(ol_h); nha += len(na_h); nhl += len(nl_h)
        return oa, ol, ona, onl, ref, ha, hl, nha, nhl, time.time() - t0

    oa, ol, ona, onl, ref, ha, hl, nha, nhl, dt = run()
    print("\n==========================================================")
    print(f"  OLD raw-exemplar  acoustic : WER {oa/max(ref,1):.3f}  hyp/ref {ha/max(ref,1):.2f}x")
    print(f"  OLD raw-exemplar  +LM      : WER {ol/max(ref,1):.3f}  hyp/ref {hl/max(ref,1):.2f}x")
    print(f"  NEW learned       acoustic : WER {ona/max(ref,1):.3f}  hyp/ref {nha/max(ref,1):.2f}x")
    print(f"  NEW learned       +LM      : WER {onl/max(ref,1):.3f}  hyp/ref {nhl/max(ref,1):.2f}x")
    print(f"  delta (old+LM - new+LM) = {(ol-onl)/max(ref,1):+.3f}   [{dt:.0f}s]")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
