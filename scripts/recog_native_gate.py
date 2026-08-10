"""GATE: the recogniser DECISION compiled to the native topk_dot primitive == the
graph-resident held Dot Term + argmax loop over WordCentroid nodes (bit-for-bit
top-k), and the learned open-vocab recogniser lifts per-chunk accuracy over raw
peel+velocity on CLEAN words (the per-chunk recognition the continuous pass needs).

  fidelity : ground_topk (native topk_dot) == the held-Dot loop, same words & order.
  lift     : learned recogniser top1/top5 vs raw _feat nearest-exemplar, clean
             cross-speaker dev words in the recogniser vocab.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners", "dsl", "python"))
import numpy as np
import substrate_rs as srs
from collections import defaultdict
from domains.learned_speech_recogniser import LearnedSpeechRecogniser, install_templates, feature
from scripts.jabberwock_lifts_speech_phonebank import _load
from scripts.jabberwock_learned_encoder import _feat


def main():
    sub = srs.Substrate(); install_templates(sub)
    rec = LearnedSpeechRecogniser(sub)
    print("=" * 80)
    print(f"RECOGNISER NATIVE GATE ({len(rec._words)} templates, encoder {rec.lda.shape[1]}d)")
    print("=" * 80)

    # 1) fidelity: native topk_dot == held-Dot loop (force loop by hiding the native fn)
    rng = np.random.default_rng(0)
    dim = rec._cmat.shape[1]
    embs = [rng.standard_normal(dim).astype(np.float32) for _ in range(40)]
    embs = [e / max(np.linalg.norm(e), 1e-9) for e in embs]

    import substrate_rs
    nat = substrate_rs._native
    saved = getattr(nat, "topk_dot", None)
    mism = 0
    for e in embs:
        native = rec.ground_topk(e, 5)                       # native topk_dot
        try:
            if saved is not None:
                del nat.topk_dot
            loop = rec.ground_topk(e, 5)                     # held-Dot loop fallback
        finally:
            if saved is not None:
                nat.topk_dot = saved
        nw = [w for w, _ in native]; lw = [w for w, _ in loop]
        if nw != lw or not np.allclose([s for _w, s in native], [s for _w, s in loop], atol=1e-4):
            mism += 1
    print(f"  fidelity: native==held-Dot loop on {len(embs)} embeddings, mismatches: {mism}")
    fid_ok = mism == 0

    # 2) lift on clean cross-speaker dev words (in the recogniser vocab)
    train = _load("train-clean-100_*.pkl", 10)
    dev = _load("dev-clean_*.pkl", 10)
    vset = set(rec._words)
    by = defaultdict(list)
    for w, fr in train:
        if w in vset and len(by[w]) < 20:
            by[w].append(fr)
    E, EW = [], []
    for w, frs in by.items():
        for fr in frs:
            E.append(_feat(fr, np.asarray(fr, float).mean(0))); EW.append(w)
    E = np.array(E)
    qry = [(w, fr) for w, fr in dev if w in vset]
    np.random.default_rng(1).shuffle(qry); qry = qry[:500]

    raw1 = lr1 = lr5 = 0
    for w, fr in qry:
        # raw nearest-exemplar
        sims = E @ _feat(fr, np.asarray(fr, float).mean(0))
        raw1 += (EW[int(sims.argmax())] == w)
        # learned recogniser top-k
        emb = rec.encode(feature(fr, np.asarray(fr, float).mean(0)))
        cand = [c for c, _s in rec.ground_topk(emb, 5)]
        lr1 += (cand[0] == w); lr5 += (w in cand)
    n = len(qry)
    print(f"  clean-word top1: raw _feat {raw1/n:.3f}  ->  learned {lr1/n:.3f}  "
          f"(top5 {lr5/n:.3f}, {n} queries, vocab {len(rec._words)})")
    lift_ok = lr1 / n > raw1 / n + 0.03

    print("=" * 80)
    ok = fid_ok and lift_ok
    print(f"  fidelity {'OK' if fid_ok else 'FAIL'} | lift {'OK' if lift_ok else 'FAIL'}")
    print(f"  {'GATE PASS' if ok else 'GATE FAIL'}: native decision == held Dot Term; learned "
          f"recogniser lifts per-chunk recognition on clean words.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
