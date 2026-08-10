"""The STRUCTURAL rung: phone PARTS + StructSim skeleton, on real cross-speaker
LibriSpeech (the full four-stage transfer the agent's consideration named).

Whole-trajectory DTW already lifted exact->graded (0.000 -> 0.625, prior commit).
This builds the NEXT rung the consideration named: decompose -> RELATE -> MATCH by
StructSim (graded part-leaf + hard skeleton) -> residual articulatory LAW.

  DECOMPOSE  acoustically (NO phone labels -> no answer leak): segment the frame
             trajectory at spectral-change peaks into PARTS (phone/syllable-like).
  PART LEAF  graded: each part = its mean cochleagram shape (L2) CONCAT its mean
             VELOCITY (the residual / articulatory law — VTL/speaker-invariant: a
             multiplicative speaker shift cancels in the difference).
  SKELETON   hard: temporal order of parts, via monotonic part-level DTW; the local
             leaf is the held StructSim numeric leaf exp(-||a-b||) over part vectors.

Three matchers, SAME clean force-aligned instances, SAME cross-speaker split
(dev-clean queries vs train-clean-100 support, disjoint speakers):
  EXACT      categorical code-sequence equality            (lexical_access regime)
  WHOLE-DTW  frame-level cosine DTW                          (the prior lift)
  STRUCTURAL part-level DTW with StructSim residual leaf     (this rung)

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_speech_structural_rung.py [n_words] [max_query] [per_word_support]
"""
from __future__ import annotations
import glob, os, pickle, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_reads_oov_from_phones import dtw, STOP   # frame-level cosine DTW + stoplist

BANK = "/home/matt/data/phonebank"


def _l2(fr):
    fr = np.asarray(fr, dtype=np.float64)
    if fr.ndim == 1:
        fr = fr.reshape(1, -1)
    return fr / np.clip(np.linalg.norm(fr, axis=1, keepdims=True), 1e-9, None)


def _load(split_glob, cap):
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, split_glob)))[:cap]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 2 and isinstance(e[0], str):
                w = e[0].lower()
                fr = _l2(e[1])
                if w not in STOP and len(w) >= 3 and fr.shape[0] >= 3:
                    out.append((w, fr))
    return out


def _segments(fr, target=6, min_len=2):
    """Acoustic decomposition (NO labels): boundaries at spectral-change peaks.
    Returns a list of (start, end) frame spans (>= min_len), ~target parts."""
    n = fr.shape[0]
    if n <= min_len * 2:
        return [(0, n)]
    flux = 1.0 - np.sum(fr[1:] * fr[:-1], axis=1)          # len n-1; flux[k]=change frame k->k+1
    # candidate boundaries = local maxima of flux (boundary sits at frame k+1), strongest first
    cand = [k for k in range(1, len(flux) - 1) if flux[k] >= flux[k - 1] and flux[k] >= flux[k + 1]]
    cand.sort(key=lambda k: -flux[k])
    bnds = []
    for k in cand:
        b = k + 1
        if all(abs(b - x) >= min_len for x in bnds) and b >= min_len and (n - b) >= min_len:
            bnds.append(b)
        if len(bnds) >= target - 1:
            break
    bnds = sorted(bnds)
    spans, s = [], 0
    for b in bnds:
        spans.append((s, b)); s = b
    spans.append((s, n))
    return [sp for sp in spans if sp[1] - sp[0] >= 1]


def _parts(fr):
    """Part descriptors: per segment, mean cochleagram shape (L2) CONCAT mean
    velocity (the residual). Returns an (n_parts x 64) array."""
    out = []
    for (s, e) in _segments(fr):
        seg = fr[s:e]
        mean = seg.mean(0)
        mean = mean / max(np.linalg.norm(mean), 1e-9)
        vel = (seg[1:] - seg[:-1]).mean(0) if e - s >= 2 else np.zeros(fr.shape[1])
        out.append(np.concatenate([mean, vel]))
    return np.asarray(out)


def _part_dtw(A, B):
    """Monotonic part-level DTW; local leaf = 1 - StructSim numeric leaf
    exp(-||a-b||) over part vectors (the held StructSim leaf). Length-normalised."""
    n, m = len(A), len(B)
    if n == 0 or m == 0:
        return 1e9
    D = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(2))
    L = 1.0 - np.exp(-D)                                   # 1 - StructSim numeric leaf
    dp = np.full((n + 1, m + 1), 1e18); dp[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i, j] = L[i - 1, j - 1] + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])
    return dp[n, m] / (n + m)


def _code(fr, cent):
    lab = (((fr[:, None, :] - cent[None, :, :]) ** 2).sum(2)).argmin(1)
    seq = []
    for j in lab:
        if not seq or seq[-1] != j:
            seq.append(int(j))
    return tuple(seq)


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_query = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    per_word = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    print("=" * 94)
    print("STRUCTURAL RUNG: phone PARTS + StructSim residual leaf, cross-speaker LibriSpeech")
    print("=" * 94)
    support_all = _load("train-clean-100_*.pkl", 8)
    query_all = _load("dev-clean_*.pkl", 8)
    sup_w = Counter(w for w, _ in support_all); qry_w = Counter(w for w, _ in query_all)
    vocab = [w for w, _ in sup_w.most_common() if qry_w[w] >= 2][:n_words]
    vset = set(vocab); chance = 1.0 / len(vocab)
    print(f"  vocab (top {n_words}, both splits): {vocab}\n  chance={chance:.3f}")

    by = defaultdict(list)
    for w, fr in support_all:
        if w in vset and len(by[w]) < per_word:
            by[w].append(fr)
    support = [(w, fr) for w, frs in by.items() for fr in frs]
    sup_parts = [(w, _parts(fr)) for w, fr in support]

    frames = np.concatenate([fr for _w, fr in support], 0)
    rng = np.random.default_rng(0)
    cent = frames[rng.choice(len(frames), size=min(48, len(frames)), replace=False)].copy()
    for _ in range(8):
        lab = (((frames[:, None, :] - cent[None, :, :]) ** 2).sum(2)).argmin(1)
        for k in range(len(cent)):
            m = frames[lab == k]
            if len(m):
                cent[k] = m.mean(0)
    sup_codes = [(w, _code(fr, cent)) for w, fr in support]

    q = [(w, fr) for w, fr in query_all if w in vset]
    np.random.default_rng(1).shuffle(q)
    q = q[:max_query]
    print(f"  support={len(support)}  queries={len(q)}  (mean parts/word="
          f"{np.mean([len(p) for _w, p in sup_parts]):.1f})")

    def _augres(fr):
        """append per-frame VELOCITY (residual) channel, re-L2 each frame."""
        d = np.vstack([np.zeros((1, fr.shape[1])), fr[1:] - fr[:-1]])
        aug = np.concatenate([fr, d], axis=1)
        return aug / np.clip(np.linalg.norm(aug, axis=1, keepdims=True), 1e-9, None)
    sup_aug = [(w, _augres(fr)) for w, fr in support]

    ex = wh = st = rs = 0
    for w, fr in q:
        qc = _code(fr, cent)
        hits = Counter(sw for sw, sc in sup_codes if sc == qc)
        if hits and hits.most_common(1)[0][0] == w:
            ex += 1
        bd, bw = 1e18, None
        for sw, sfr in support:
            d = dtw(fr, sfr)
            if d < bd:
                bd, bw = d, sw
        if bw == w:
            wh += 1
        qp = _parts(fr)
        bd, bw = 1e18, None
        for sw, sp in sup_parts:
            d = _part_dtw(qp, sp)
            if d < bd:
                bd, bw = d, sw
        if bw == w:
            st += 1
        qa = _augres(fr)
        bd, bw = 1e18, None
        for sw, sa in sup_aug:
            d = dtw(qa, sa)
            if d < bd:
                bd, bw = d, sw
        if bw == w:
            rs += 1

    n = len(q)
    print("\n" + "=" * 94)
    print(f"  EXACT      categorical        : {ex/n:.3f}")
    print(f"  WHOLE-DTW  frame-level (prior): {wh/n:.3f}")
    print(f"  FRAME+RESIDUAL DTW            : {rs/n:.3f}   (frame (X) velocity channel = articulatory residual)")
    print(f"  STRUCTURAL parts+StructSim res: {st/n:.3f}")
    print(f"  chance                        : {chance:.3f}")
    print("=" * 94)
    d_vs_whole = st/n - wh/n
    d_res = rs/n - wh/n
    print(f"  residual-channel vs whole-DTW: {d_res:+.3f}   structural-parts vs whole-DTW: {d_vs_whole:+.3f}")
    print(f"  best matcher: {max([('exact',ex),('whole',wh),('frame+residual',rs),('structural',st)], key=lambda t: t[1])[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
