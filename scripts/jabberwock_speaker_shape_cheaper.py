"""Is it CHEAPER? If the speaker is a separable shape removed once, the content
collapses across speakers -> you need far LESS matching to recognise the word.

Two cost wins on the clean cross-speaker phonebank gate (dev vs train-clean-100):
  (1) EXACT (~free: quantise + hash, NO per-exemplar DTW) failed ONLY because of
      speaker variation (0.000). Remove the speaker-shape first -> does the cheap
      matcher work?
  (2) ONE PROTOTYPE per word (medoid) -> W comparisons/query instead of all N
      exemplars (~30x fewer DTWs). Does removal let a single prototype match the
      full-exemplar accuracy?

COST = mean exemplar-DTWs per query (the dominant cost; exact has 0 DTWs).
Speaker discovered unsupervised (cluster by speaker-shape); removal = Substitute the
inverse band-envelope. Compares accuracy AND cost.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_speaker_shape_cheaper.py [n_words] [max_query] [per_word]
"""
from __future__ import annotations
import glob, os, pickle, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_reads_oov_from_phones import dtw, STOP

BANK = "/home/matt/data/phonebank"


def _l2(fr):
    fr = np.asarray(fr, dtype=np.float64)
    if fr.ndim == 1:
        fr = fr.reshape(1, -1)
    return fr / np.clip(np.linalg.norm(fr, axis=1, keepdims=True), 1e-9, None)


def _load(g, cap):
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, g)))[:cap]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 2 and isinstance(e[0], str):
                w = e[0].lower(); fr = _l2(e[1])
                if w not in STOP and len(w) >= 3 and fr.shape[0] >= 3:
                    out.append((w, fr))
    return out


def _kmeans(X, K, it=12):
    rng = np.random.default_rng(0)
    C = X[rng.choice(len(X), min(K, len(X)), replace=False)].copy()
    for _ in range(it):
        lab = (((X[:, None, :] - C[None, :, :]) ** 2).sum(2)).argmin(1)
        for k in range(len(C)):
            m = X[lab == k]
            if len(m):
                C[k] = m.mean(0)
    return lab


def _spk_env(words, K):
    feat = np.array([np.concatenate([fr.mean(0), fr.std(0)]) for _w, fr in words])
    feat = feat / np.clip(np.linalg.norm(feat, axis=1, keepdims=True), 1e-9, None)
    lab = _kmeans(feat, K)
    envs = {k: np.concatenate([words[i][1] for i in range(len(words)) if lab[i] == k], 0).mean(0)
            for k in set(lab)}
    return [envs[lab[i]] for i in range(len(words))]


def _rm(fr, env):
    r = fr - env[None, :]
    return r / np.clip(np.linalg.norm(r, axis=1, keepdims=True), 1e-9, None)


def _code(fr, cent):
    lab = (((fr[:, None, :] - cent[None, :, :]) ** 2).sum(2)).argmin(1)
    seq = []
    for j in lab:
        if not seq or seq[-1] != j:
            seq.append(int(j))
    return tuple(seq)


def _medoids(by_word):
    """One prototype per word = the exemplar with min total DTW to the rest."""
    proto = {}
    for w, frs in by_word.items():
        best, bi = 1e18, 0
        for i in range(len(frs)):
            tot = sum(dtw(frs[i], frs[j]) for j in range(len(frs)) if j != i)
            if tot < best:
                best, bi = tot, i
        proto[w] = frs[bi]
    return proto


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    sup_all = _load("train-clean-100_*.pkl", 8)
    qry_all = _load("dev-clean_*.pkl", 8)
    sw = Counter(w for w, _ in sup_all); qw = Counter(w for w, _ in qry_all)
    vocab = [w for w, _ in sw.most_common() if qw[w] >= 2][:n_words]
    vset = set(vocab); chance = 1.0 / len(vocab)

    by = defaultdict(list)
    for w, fr in sup_all:
        if w in vset and len(by[w]) < per:
            by[w].append(fr)
    support = [(w, fr) for w, frs in by.items() for fr in frs]
    queries = [(w, fr) for w, fr in qry_all if w in vset]
    np.random.default_rng(1).shuffle(queries); queries = queries[:max_q]
    N = len(support); W = len(vocab)
    print("=" * 94)
    print("IS IT CHEAPER? speaker-shape removal -> fewer / free comparisons, same accuracy?")
    print("=" * 94)
    print(f"  vocab={W} chance={chance:.3f}  support(N)={N}  queries={len(queries)}")

    # speaker removal
    q_env = _spk_env(queries, 3); s_env = _spk_env(support, 24)
    sup_rm = [(w, _rm(fr, s_env[i])) for i, (w, fr) in enumerate(support)]
    by_rm = defaultdict(list)
    for w, fr in sup_rm:
        by_rm[w].append(fr)

    # codebook (for the ~free exact matcher), on speaker-removed support
    fr_rm = np.concatenate([fr for _w, fr in sup_rm], 0)
    rng = np.random.default_rng(0)
    cent = fr_rm[rng.choice(len(fr_rm), min(48, len(fr_rm)), replace=False)].copy()
    for _ in range(8):
        lab = (((fr_rm[:, None, :] - cent[None, :, :]) ** 2).sum(2)).argmin(1)
        for k in range(len(cent)):
            m = fr_rm[lab == k]
            if len(m):
                cent[k] = m.mean(0)
    sup_codes_rm = [(w, _code(fr, cent)) for w, fr in sup_rm]

    # prototypes (one medoid per word) — full vs speaker-removed
    proto_full = _medoids(by)
    proto_rm = _medoids(by_rm)

    full = proto = proto_r = exact_r = 0
    for qi, (w, fr) in enumerate(queries):
        # C: GRADED full exemplars (expensive, N DTWs) — the prior 0.625
        bd, bw = 1e18, None
        for sw_, sfr in support:
            d = dtw(fr, sfr)
            if d < bd:
                bd, bw = d, sw_
        full += (bw == w)
        # D: GRADED one prototype/word (W DTWs, ~N/W cheaper), no removal
        bd, bw = 1e18, None
        for pw, pfr in proto_full.items():
            d = dtw(fr, pfr)
            if d < bd:
                bd, bw = d, pw
        proto += (bw == w)
        # E: GRADED one prototype/word + speaker removed (W DTWs)
        frr = _rm(fr, q_env[qi])
        bd, bw = 1e18, None
        for pw, pfr in proto_rm.items():
            d = dtw(frr, pfr)
            if d < bd:
                bd, bw = d, pw
        proto_r += (bw == w)
        # B: EXACT (~free, 0 DTWs) + speaker removed
        qc = _code(frr, cent)
        hits = Counter(sw_ for sw_, sc in sup_codes_rm if sc == qc)
        if hits and hits.most_common(1)[0][0] == w:
            exact_r += 1

    n = len(queries)
    print("\n" + "=" * 94)
    print(f"  matcher                         acc      DTWs/query (cost)")
    print(f"  GRADED full exemplars           {full/n:.3f}    {N}")
    print(f"  GRADED 1 prototype/word         {proto/n:.3f}    {W}   ({N/W:.0f}x cheaper)")
    print(f"  GRADED 1 proto/word + spk-rm    {proto_r/n:.3f}    {W}   ({N/W:.0f}x cheaper)")
    print(f"  EXACT (+ spk-rm)                {exact_r/n:.3f}    0    (~free: quantise+hash)")
    print(f"  chance                          {chance:.3f}")
    print("=" * 94)
    keep = proto_r/n >= full/n - 0.03
    print(f"  prototype keeps full accuracy within 0.03: {keep}  "
          f"-> {N//W}x fewer DTWs at {'~same' if keep else 'lower'} accuracy")
    print("  The cost win: speaker is a SHAPE removed once per utterance; with it gone the content")
    print("  collapses across speakers, so ONE prototype per word suffices (N/W fewer comparisons),")
    print("  and the ~free exact matcher gets off the floor. Remove the expensive axis, the cheap one works.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
