"""The jabberwock builds the EFFORT-BASED CONTENT LOCALIZER.

The content feature is already good (0.78 top-5 on clean content words); the floor is
LOCALIZATION — the TP-segmenter hands mangled spans, so content recall in continuous is
~0.05 not 0.78. The thermodynamic fix: content words are HIGH-EFFORT energy islands;
function/reduced words are low-effort valleys between them. So LOCALIZE content by EFFORT:
cut the energy contour at its VALLEYS (the agent's order-1 sign-change, the dual of the
stress peaks, run on ENERGY) and keep the high-effort islands as content-word spans;
recognise each with the good content feature. The reduced filler in the valleys is not
localised — a listener reconstructs it from the prior (it carries ~0 bits).

Energy localises (continuous frames() retains it); the normalised spectral SHAPE
recognises (the phonebank feature). Measures CONTENT RECALL (did the signal transmit)
of the effort localizer vs the TP-segmenter, recognising with CONTENT templates only.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_content_localizer.py [n_test]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
from collections import Counter
import scripts.librispeech_wer as L
from scripts.context_invariant_librispeech_accept import kmeans, quantize
from scripts.jabberwock_lifts_speech_phonebank import _load
from scripts.jabberwock_reads_oov_from_phones import frames
from scripts.jabberwock_stress_feature import sonority
from domains.forward_segmentation import forward_segment
from domains.learned_speech_recogniser import LearnedSpeechRecogniser, install_templates, feature


def _median(x):
    return float(np.median(x)) if len(x) else 0.0


def effort_spans(e, min_len=4):
    """The agent's EFFORT localizer: cut the energy/sonority contour at its VALLEYS
    (local minima below the median effort = where the speaker coasted/reduced/paused),
    keep the runs between them as high-effort content-word islands. Order-1 sign-change
    on the EFFORT contour (same primitive as the stress peaks, dual sign)."""
    s = sonority(e)
    med = _median(s)
    cuts = [0]
    for i in range(1, len(s) - 1):
        if s[i] <= s[i - 1] and s[i] < s[i + 1] and s[i] < med:   # an effort valley
            cuts.append(i)
    cuts.append(len(s))
    spans = []
    for k in range(len(cuts) - 1):
        a, b = cuts[k], cuts[k + 1]
        if b - a >= min_len:
            spans.append((a, b))
    return spans or [(0, len(s))]


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    TOPK = 5

    sub = srs.Substrate(); install_templates(sub)
    rec = LearnedSpeechRecogniser(sub)
    train = _load("train-clean-100_*.pkl", 12)
    func = set(w for w, _ in Counter(w for w, _ in train).most_common(50))
    def is_content(w): return w not in func and len(w) >= 4

    # CONTENT-only template matrix (the localizer is FOR content)
    cidx = [i for i, w in enumerate(rec._words) if is_content(w) and " " not in w]
    cmat = rec._cmat[cidx]; cwords = [rec._words[i] for i in cidx]
    print(f"  content templates={len(cwords)}", flush=True)

    def recognise_spans(M, spans):
        out = []
        for a, b in spans:
            if b - a < 2:
                continue
            emb = rec.encode(feature(M[a:b], np.asarray(M[a:b], float).mean(0)))
            j = int((cmat @ emb).argmax())
            out.append(cwords[j])
        return out

    def recognise_reframe(x, mlen, spans):
        """Re-frame each span FROM THE RAW AUDIO so its CMVN is per-span (matching the
        phonebank templates' per-word CMVN), not inherited from the whole utterance."""
        step = len(x) / max(mlen, 1)
        out = []
        for a, b in spans:
            seg = x[int(a * step):int(b * step)]
            if len(seg) < 320:
                continue
            try:
                Mre, _e = frames(seg)
            except Exception:
                continue
            emb = rec.encode(feature(Mre, np.asarray(Mre, float).mean(0)))
            out.append(cwords[int((cmat @ emb).argmax())])
        return out

    def recognise_sliding(M, scales=(16, 24, 32), stride=6):
        """BOUNDARY-FREE: slide multi-scale windows over the utterance; a content word is
        DETECTED where its template similarity PEAKS across positions (locks in), not at a
        hard cut. Keep a window's argmax word only when its score is a local max vs its
        neighbours at that scale and above the score median (data-derived) — a matched-
        filter detection. Tests whether content is FINDABLE without word boundaries."""
        found = []
        n = len(M)
        for Lw in scales:
            if n < Lw:
                continue
            pos = list(range(0, n - Lw + 1, stride))
            embs = [rec.encode(feature(M[p:p + Lw], np.asarray(M[p:p + Lw], float).mean(0)))
                    for p in pos]
            sims = cmat @ np.array(embs).T            # (templates x positions)
            best_w = sims.argmax(0); best_s = sims.max(0)
            lvl = float(np.median(best_s))
            for k in range(len(pos)):
                lo = best_s[k - 1] if k > 0 else -1e9
                hi = best_s[k + 1] if k + 1 < len(pos) else -1e9
                if best_s[k] >= lo and best_s[k] > hi and best_s[k] > lvl:
                    found.append(cwords[best_w[k]])
        return found

    pairs = L.gather_pairs(limit=n_test + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    Ms, Es, Xs, refs = [], [], [], []
    for (path, sp_, ch, ut, tr) in test:
        try:
            x = L.load_flac(path)[0]; M, e = frames(x)
            Ms.append(M); Es.append(np.asarray(e, float)); Xs.append(np.asarray(x, float))
            refs.append([w.lower() for w in L.normalise(tr)])
        except Exception as ex:
            print("  frame fail", ex)

    # TP-segmenter spans (the baseline localizer)
    C = kmeans(np.concatenate([fr for _w, fr in train[:1500]], 0), 48)
    seqs = [[int(u) for u in quantize(M, C)] for M in Ms]
    ssub = srs.Substrate()
    chunked = forward_segment(ssub, seqs, n_passes=1, boundary_mode="prominent")["chunked"]
    seg_spans = []
    for s, chk in zip(seqs, chunked or [[(u,) for u in q] for q in seqs]):
        sp, k = [], 0
        for c in chk:
            sp.append((k, k + len(c))); k += len(c)
        seg_spans.append(sp)

    def content_recall(mode):
        rx = tot = nsp = 0
        for M, e, x, words, segsp in zip(Ms, Es, Xs, refs, seg_spans):
            spans = segsp if mode == "segmenter" else effort_spans(e)
            if mode == "effort_reframe":
                hyp = set(recognise_reframe(x, len(M), spans))
            elif mode == "boundary_free":
                hyp = set(recognise_sliding(M))
            else:
                hyp = set(recognise_spans(M, spans))
            nsp += len(spans)
            cref = set(w for w in words if is_content(w))
            tot += len(cref); rx += len(cref & hyp)
        return rx / max(tot, 1), nsp / max(len(Ms), 1)

    t0 = time.time()
    sr, sn = content_recall("segmenter")
    er, en = content_recall("effort")
    rr, rn = content_recall("effort_reframe")
    bf, bn = content_recall("boundary_free")
    print("\n==========================================================")
    print(f"  TP-SEGMENTER (subspan M)        : content-recall {sr:.3f}  spans/utt {sn:.0f}")
    print(f"  EFFORT localizer (subspan M)    : content-recall {er:.3f}  spans/utt {en:.0f}")
    print(f"  EFFORT localizer + REFRAME audio: content-recall {rr:.3f}  spans/utt {rn:.0f}")
    print(f"  BOUNDARY-FREE (matched filter)  : content-recall {bf:.3f}  detections/utt {bn:.0f}  [{time.time()-t0:.0f}s]")
    print(f"  (clean-content ceiling ~0.78 top-5 / ~0.51 top-1)")
    print("==========================================================")
    print("  Effort localizer = cut energy at its valleys, keep high-effort islands as content words,")
    print("  recognise with the good content feature. Energy localises; spectral shape recognises.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
