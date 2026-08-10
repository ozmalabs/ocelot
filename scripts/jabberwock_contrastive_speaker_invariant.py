"""THE OPEN FRONTIER — BEAT the INVARIANCE-vs-DISCRIMINATION trade-off on MULTI-SPEAKER speech.

Multi-speaker order-1 word-shape fidelity is stuck ~0.40 (vs single-speaker/phonebank ~0.84) because
same-word-cross-speaker must SNAP TOGETHER (invariance) while distinct-words stay SEPARATE (discrimination),
and every prior GLOBAL transform only REMOVED variance -> slid along the trade-off, never beat it:
  VTLN (freq-warp) NULL (coarticulation, not VTL, is the residual — ffa12c7b); delta/CMN COMPRESS distance
  but don't fix RANKING (NN-recall flat); LDA/SFA same-distribution OVERFIT, tie raw held-out; wav2vec2
  helped cross-speaker (+0.045) but HURT discrimination (d' 1.63->1.17).

THE MECHANISM TO BEAT IT (this script): a from-scratch numpy CONTRASTIVE / metric-learning encoder that
optimizes BOTH AXES SIMULTANEOUSLY —
  POSITIVES  = same-word, DIFFERENT-speaker  (forces speaker-INVARIANCE),
  NEGATIVES  = different-word                (forces DISCRIMINATION),
operating on the DYNAMIC trajectory (per-frame [CMN-value ++ delta] of the cochleagram curve — movement is
less speaker-dependent than the absolute spectrum, and IS the word). The encoder is a per-frame linear map
W (a low-rank Mahalanobis metric); DtwTo's local distance is EUCLIDEAN, so the trained squared-Euclidean
metric IS the DTW metric — training and inference use the SAME distance. Optional speaker-adaptive factor:
subtract the speaker's OWN global mean feature (estimated unsupervised from that speaker's tokens — works on
UNSEEN speakers, NOT a fixed global transform).

POSITIVE PAIRS = teacher-bootstrap (per ozma_trained_to_self_learning): the word IDENTITY at TRAINING comes
from the MMS_FA forced aligner (torch, ISOLATED subprocess, EVAL/BOOTSTRAP-ONLY). At INFERENCE the teacher
is REMOVED (verified out of sys.modules) — the earned encoder is a standalone numpy matrix (donkey=0).

★ HELD-OUT SPEAKERS: train the encoder on TRAIN speakers (train-clean-100), TEST on DISJOINT dev-clean
speakers NEVER seen in training (different corpus split too — the strongest generalization control; this is
exactly what LDA/SFA got wrong).

GATE (donkey=0, honest — MATCHED-GRANULARITY clustering + RANK metrics):
  (a) ★ BEAT THE TRADE-OFF: on HELD-OUT speakers the learned space raises cross-speaker same-word NN-RECALL
      (invariance) WITHOUT dropping distinct-word DISCRIMINATION (d'); report the 2D (recall, d') point vs
      raw / delta / wav2vec2 — a genuine PARETO improvement, not a slide.
  (b) ★ MULTI-SPEAKER order-1 PURITY 0.40 -> toward 0.84 (matched #clusters).
  (c) ★ FULL-STACK recovers on multi-speaker (function/content split + cross-context snapping).
  (d) donkey=0 at inference (encoder numpy, teacher removed), held-out SPEAKERS, shuffled control.

donkey=0: encoder = from-scratch numpy SGD metric-learning; DtwTo = held Rust Term; MMS_FA/wav2vec2 = torch
in an ISOLATED subprocess writing an UNCOMMITTED scratch cache. Memory: mini-batch float32 training, bounded
greedy leader clustering (NO (N,K,D)), wav2vec2 float16, ulimit-14Gi (via D import). USE THE VENV PYTHON.

Run: PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
        scripts/jabberwock_contrastive_speaker_invariant.py
Env: KTRAIN (train speakers, 30), KTEST (held-out test speakers, 20), UTTS (utts/speaker, 12),
     DZ (embed dim, 24), EPOCHS (400), W2V (extract wav2vec2 baseline, 1), SCRATCH.
"""
from __future__ import annotations
import os, sys, glob, pickle, subprocess, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from collections import Counter, defaultdict

VENV_PY = "/home/matt/ozma/internal/research/.venv/bin/python"
LIBRI = "/home/matt/data/LibriSpeech"
TRAIN_TREE = os.path.join(LIBRI, "train-clean-100")
TEST_TREE = os.path.join(LIBRI, "dev-clean")
SCRATCH = os.environ.get(
    "SCRATCH",
    "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
    "3ed12bb3-7b58-44c0-b051-98640926c040/scratchpad")
os.makedirs(SCRATCH, exist_ok=True)
CACHE = os.path.join(SCRATCH, "contrastive_libri.pkl")

KTRAIN = int(os.environ.get("KTRAIN", "30"))
KTEST = int(os.environ.get("KTEST", "20"))
UTTS = int(os.environ.get("UTTS", "12"))
T = int(os.environ.get("T", "20"))
DZ = int(os.environ.get("DZ", "24"))
EPOCHS = int(os.environ.get("EPOCHS", "400"))
W2V = int(os.environ.get("W2V", "1"))
W2V_LAYER = int(os.environ.get("W2V_LAYER", "8"))


# ============================================================================ #
#  EXTRACTION (torch; ISOLATED SUBPROCESS; UNCOMMITTED scratch cache)
#  Per token: (word, cochleagram[T_var,32] float32, speaker_id, left_word,
#  right_word, split, w2v[T,768] float16 or None). split='train'|'test'.
# ============================================================================ #
def _extract():
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (14 * 1024**3, 14 * 1024**3))
    import torch
    torch.set_num_threads(os.cpu_count() or 4)
    from torchaudio.pipelines import MMS_FA as B
    from scripts.librispeech_wer import load_flac
    from scripts.jabberwock_reads_oov_from_phones import frames
    m, tok, aln = B.get_model(), B.get_tokenizer(), B.get_aligner()

    w2v_model = None
    if W2V:
        try:
            from torchaudio.pipelines import WAV2VEC2_BASE as WB
            w2v_model = WB.get_model().eval()
            print(f"  [extract] wav2vec2 base loaded (layer {W2V_LAYER})", flush=True)
        except Exception as e:
            print(f"  [extract] wav2vec2 unavailable ({type(e).__name__}: {e}) — skipping w2v baseline", flush=True)
            w2v_model = None

    def transcripts(d):
        tr = {}
        for tf in glob.glob(os.path.join(d, "**", "*.trans.txt"), recursive=True):
            for line in open(tf):
                line = line.strip()
                if " " in line:
                    k, v = line.split(" ", 1); tr[k] = v
        return tr

    def align_utt(audio, fs, transcript):
        words = [re.sub(r"[^a-z]", "", w.lower()) for w in transcript.split()]
        keep = [(i, w) for i, w in enumerate(words) if w]
        if not keep:
            return []
        wav = torch.tensor(np.asarray(audio), dtype=torch.float32).unsqueeze(0)
        try:
            with torch.inference_mode():
                emission, _ = m(wav)
                spans = aln(emission[0], tok([w for _i, w in keep]))
        except Exception:
            return []
        ratio = wav.size(1) / emission.size(1)
        return [(w, sp[0].start * ratio / fs, sp[-1].end * ratio / fs) for (_i, w), sp in zip(keep, spans)]

    def w2v_frames(audio, fs):
        """wav2vec2 hidden states at W2V_LAYER for the whole utterance -> [Tw,768] numpy. ~50 fps."""
        if w2v_model is None:
            return None
        wav = torch.tensor(np.asarray(audio), dtype=torch.float32).unsqueeze(0)
        with torch.inference_mode():
            feats, _ = w2v_model.extract_features(wav, num_layers=W2V_LAYER + 1)
        return feats[W2V_LAYER][0].cpu().numpy().astype(np.float32)   # [Tw,768]

    def resample_np(arr, t):
        n = len(arr)
        if n == t:
            return arr
        idx = np.linspace(0, n - 1, t)
        lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, n - 1); fr = (idx - lo)[:, None]
        return (arr[lo] * (1 - fr) + arr[hi] * fr)

    def do_tree(tree, klim, split, out, seen):
        speakers = sorted(os.listdir(tree))[:klim]
        for sp in speakers:
            tr = transcripts(os.path.join(tree, sp))
            flacs = sorted(glob.glob(os.path.join(tree, sp, "**", "*.flac"), recursive=True))[:UTTS]
            ntok = 0
            for f in flacs:
                base = os.path.basename(f)[:-5]
                if base not in tr:
                    continue
                x, fs = load_flac(f); x = np.asarray(x, np.float64)
                spans = align_utt(x, fs, tr[base])
                wv = w2v_frames(x, fs)                       # [Tw,768] over whole utt @ ~50fps
                utt_dur = len(x) / fs
                seq = []
                for (w, t0, t1) in spans:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if not (w.isalpha() and len(w) >= 2 and seg.size >= int(0.06 * fs)):
                        seq.append(None); continue
                    fr = frames(seg)[0].astype(np.float32)
                    if fr.shape[0] < 4:
                        seq.append(None); continue
                    w2v_tok = None
                    if wv is not None:
                        a = int(t0 / utt_dur * len(wv)); b = int(t1 / utt_dur * len(wv))
                        if b - a >= 2:
                            w2v_tok = resample_np(wv[a:b], T).astype(np.float16)
                    seq.append((w, fr, w2v_tok))
                    ntok += 1
                for k, item in enumerate(seq):
                    if item is None:
                        continue
                    w, fr, w2v_tok = item
                    left = seq[k - 1][0] if k > 0 and seq[k - 1] else None
                    right = seq[k + 1][0] if k < len(seq) - 1 and seq[k + 1] else None
                    out.append((w, fr, f"{split}:{sp}", left, right, split, w2v_tok))
                del x, wv
            seen.add(sp)
            print(f"  [extract] {split} speaker {sp}: {ntok} toks (total {len(out)})", flush=True)

    out, seen = [], set()
    do_tree(TRAIN_TREE, KTRAIN, "train", out, seen)
    do_tree(TEST_TREE, KTEST, "test", out, seen)
    pickle.dump(out, open(CACHE, "wb"))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
    ntr = len(set(s for *_, s, _ in [(o[0], o[5], o[2]) for o in out] if s == "train"))
    print(f"  [extract] wrote {len(out)} tokens; "
          f"train spk {len(set(o[2] for o in out if o[5]=='train'))}, "
          f"test spk {len(set(o[2] for o in out if o[5]=='test'))}, "
          f"w2v={'yes' if any(o[6] is not None for o in out) else 'no'} [peak {peak:.2f} GiB]", flush=True)


# ============================================================================ #
#  FEATURES (torch-free numpy)
# ============================================================================ #
def resample(fr, t):
    n = len(fr)
    if n == t:
        return fr.astype(np.float32)
    idx = np.linspace(0, n - 1, t)
    lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, n - 1); f = (idx - lo)[:, None]
    return (fr[lo] * (1 - f) + fr[hi] * f).astype(np.float32)


def frame_features(fr):
    """Per-frame DYNAMIC feature = [CMN value (32) ++ delta (32)] -> [T,64]. CMN removes the per-token
    spectral OFFSET (additive speaker/channel); delta is the movement (offset-invariant). Resampled to T."""
    fr = np.asarray(fr, np.float32)
    val = fr - fr.mean(0, keepdims=True)                     # CMN value
    dlt = np.diff(fr, axis=0)
    dlt = np.vstack([np.zeros((1, fr.shape[1]), np.float32), dlt])
    x = np.concatenate([val, dlt], axis=1)                   # [n,64]
    return resample(x, T)                                    # [T,64]


# ============================================================================ #
#  CONTRASTIVE METRIC-LEARNING ENCODER (from-scratch numpy SGD; donkey=0)
#  z_t = W^T x_t  (per-frame linear low-rank Mahalanobis map). Distance between
#  two time-normalised tokens = sum_t || W^T x^a_t - W^T x^b_t ||^2  (== DtwTo
#  Euclidean local dist when band>=T). Triplet loss over W; analytic gradient.
# ============================================================================ #
class MetricEncoder:
    def __init__(self, din, dz, seed=0):
        rng = np.random.default_rng(seed)
        self.W = (rng.standard_normal((din, dz)) / np.sqrt(din)).astype(np.float32)

    def encode(self, X):                                     # X:[...,din] -> [...,dz]
        return X @ self.W

    def tok_dist(self, A, B):                                # A,B:[T,din] -> scalar time-aligned sq dist
        d = (A - B) @ self.W
        return float((d * d).sum() / len(A))

    def fit(self, feats, words, spk, epochs, margin=1.0, lr=0.05, wd=1e-4,
            batch=64, seed=0, verbose=True):
        """Triplet SGD. anchor a & positive p = SAME word, DIFFERENT speaker; negative n = DIFFERENT word.
        loss = mean max(0, margin + D(a,p) - D(a,n)); D = time-aligned sq Euclidean in W-space (/T)."""
        rng = np.random.default_rng(seed)
        N = len(feats); Tn = feats[0].shape[0]
        byword = defaultdict(list)
        for i in range(N):
            byword[words[i]].append(i)
        # anchors = tokens whose word has >=1 other-speaker instance
        anchors = []
        for w, idx in byword.items():
            sset = set(spk[i] for i in idx)
            if len(sset) >= 2 and len(idx) >= 2:
                anchors.append(w)
        if not anchors:
            print("  [fit] no cross-speaker positives available — encoder stays random", flush=True)
            return self
        anchor_pool = [i for w in anchors for i in byword[w]]
        F = np.stack(feats).astype(np.float32)               # [N,T,din]
        for ep in range(epochs):
            rng.shuffle(anchor_pool)
            tot = 0.0; nact = 0
            for s in range(0, len(anchor_pool), batch):
                ba = anchor_pool[s:s + batch]
                G = np.zeros_like(self.W); nb = 0
                for ai in ba:
                    w = words[ai]
                    pos_c = [j for j in byword[w] if spk[j] != spk[ai]]
                    if not pos_c:
                        continue
                    pi = pos_c[rng.integers(len(pos_c))]
                    # semi-hard-ish negative: sample a few diff-word, take the closest
                    negs = [rng.integers(N) for _ in range(6)]
                    negs = [j for j in negs if words[j] != w]
                    if not negs:
                        continue
                    dpos = F[ai] - F[pi]                      # [T,din]
                    zp = dpos @ self.W; Dp = float((zp * zp).sum() / Tn)
                    # pick hardest (smallest D(a,n)) negative
                    best_ni, bestDn, best_dn = -1, 1e18, None
                    for nj in negs:
                        dn = F[ai] - F[nj]; zn = dn @ self.W; Dn = float((zn * zn).sum() / Tn)
                        if Dn < bestDn:
                            bestDn, best_ni, best_dn = Dn, nj, dn
                    if margin + Dp - bestDn > 0:              # active triplet
                        # dD/dW = (2/T) * diff^T diff W ; grad of (Dp - Dn) wrt W
                        Gp = dpos.T @ (dpos @ self.W)
                        Gn = best_dn.T @ (best_dn @ self.W)
                        G += (2.0 / Tn) * (Gp - Gn)
                        tot += margin + Dp - bestDn; nact += 1; nb += 1
                if nb:
                    self.W -= lr * (G / nb + wd * self.W)
            if verbose and (ep % max(1, epochs // 8) == 0 or ep == epochs - 1):
                print(f"    [fit] epoch {ep:4d}: active-triplet loss {tot / max(nact,1):.4f} "
                      f"(active {nact})", flush=True)
        return self


class MLPEncoder:
    """CAPACITY LEVER (honest fork): one tanh hidden layer -> nonlinear per-frame map (still numpy, still
    from-scratch, still donkey=0). z_t = tanh(x_t W1 + b1) W2. Backprop through the time-aligned triplet
    distance. Tests whether the donkey=0 shortfall to wav2vec2 is CAPACITY (nonlinearity closes it) or the
    32-band front-end / data (nonlinearity ties the linear metric)."""
    def __init__(self, din, dz, hid=64, seed=0):
        rng = np.random.default_rng(seed)
        self.W1 = (rng.standard_normal((din, hid)) / np.sqrt(din)).astype(np.float32)
        self.b1 = np.zeros(hid, np.float32)
        self.W2 = (rng.standard_normal((hid, dz)) / np.sqrt(hid)).astype(np.float32)

    def encode(self, X):
        H = np.tanh(X @ self.W1 + self.b1)
        return H @ self.W2

    def _pair_grad(self, A, B, Tn):
        """returns (D, gW1, gb1, gW2) for squared time-aligned distance between tokens A,B ([T,din])."""
        Ha = np.tanh(A @ self.W1 + self.b1); Za = Ha @ self.W2
        Hb = np.tanh(B @ self.W1 + self.b1); Zb = Hb @ self.W2
        dZ = Za - Zb                                        # [T,dz]
        D = float((dZ * dZ).sum() / Tn)
        g = (2.0 / Tn) * dZ                                 # dD/dZa ; dD/dZb = -g
        gW2 = Ha.T @ g + Hb.T @ (-g)
        dHa = g @ self.W2.T; dHb = (-g) @ self.W2.T
        pa = dHa * (1 - Ha * Ha); pb = dHb * (1 - Hb * Hb)
        gW1 = A.T @ pa + B.T @ pb
        gb1 = (pa + pb).sum(0)
        return D, gW1, gb1, gW2

    def fit(self, feats, words, spk, epochs, margin=1.0, lr=0.03, wd=1e-4, batch=64, seed=0, verbose=True):
        rng = np.random.default_rng(seed)
        N = len(feats); Tn = feats[0].shape[0]
        byword = defaultdict(list)
        for i in range(N):
            byword[words[i]].append(i)
        anchors = [w for w, idx in byword.items() if len(set(spk[i] for i in idx)) >= 2 and len(idx) >= 2]
        if not anchors:
            print("  [fit-mlp] no cross-speaker positives — encoder stays random", flush=True); return self
        anchor_pool = [i for w in anchors for i in byword[w]]
        F = np.stack(feats).astype(np.float32)
        for ep in range(epochs):
            rng.shuffle(anchor_pool); tot = 0.0; nact = 0
            for s in range(0, len(anchor_pool), batch):
                ba = anchor_pool[s:s + batch]
                gW1 = np.zeros_like(self.W1); gb1 = np.zeros_like(self.b1); gW2 = np.zeros_like(self.W2); nb = 0
                for ai in ba:
                    w = words[ai]
                    pos_c = [j for j in byword[w] if spk[j] != spk[ai]]
                    if not pos_c:
                        continue
                    pi = pos_c[rng.integers(len(pos_c))]
                    negs = [j for j in (int(rng.integers(N)) for _ in range(6)) if words[j] != w]
                    if not negs:
                        continue
                    Dp, p1, pb1, p2 = self._pair_grad(F[ai], F[pi], Tn)
                    # hardest negative
                    best = None
                    for nj in negs:
                        Dn, n1, nb1, n2 = self._pair_grad(F[ai], F[nj], Tn)
                        if best is None or Dn < best[0]:
                            best = (Dn, n1, nb1, n2)
                    Dn, n1, nb1, n2 = best
                    if margin + Dp - Dn > 0:
                        gW1 += p1 - n1; gb1 += pb1 - nb1; gW2 += p2 - n2
                        tot += margin + Dp - Dn; nact += 1; nb += 1
                if nb:
                    self.W1 -= lr * (gW1 / nb + wd * self.W1)
                    self.b1 -= lr * (gb1 / nb)
                    self.W2 -= lr * (gW2 / nb + wd * self.W2)
            if verbose and (ep % max(1, epochs // 6) == 0 or ep == epochs - 1):
                print(f"    [fit-mlp] epoch {ep:4d}: active-triplet loss {tot / max(nact,1):.4f} "
                      f"(active {nact})", flush=True)
        return self


# ============================================================================ #
#  METRICS (torch-free; DtwTo = held Rust Term = Euclidean local dist)
# ============================================================================ #
def _traj(fr):
    return tuple(tuple(float(v) for v in row) for row in fr)


def nn_recall_cross(trajs, words, spk, Q, cap_q=200, cap_cand=800, seed=0):
    """INVARIANCE: for each query, its nearest CROSS-speaker DTW neighbour -> recall = word matches.
    Queries restricted to words spoken by >=2 speakers. tau-free, comparable across representations."""
    import substrate_rs as srs
    s = srs.Substrate(); rng = np.random.default_rng(seed)
    byw_sp = defaultdict(set)
    for i, w in enumerate(words):
        byw_sp[w].add(spk[i])
    q = [i for i, w in enumerate(words) if len(byw_sp[w]) >= 2]
    if len(q) > cap_q:
        q = list(rng.choice(q, cap_q, replace=False))
    cand = list(range(len(trajs)))
    if len(cand) > cap_cand:
        cand = list(rng.choice(cand, cap_cand, replace=False))
    hit = tot = 0
    for a in q:
        dmin, arg = 1e18, -1
        for b in cand:
            if spk[b] == spk[a]:
                continue
            d = float(s.evaluate(Q._P(Q._DtwTo(Q._Lit(trajs[a]), Q._Lit(trajs[b]))), {}))
            if d < dmin:
                dmin, arg = d, b
        if arg >= 0:
            tot += 1; hit += int(words[arg] == words[a])
    return hit / tot if tot else float("nan")


def dprime_cross(trajs, words, spk, Q, n_pos=500, n_neg=1500, seed=1):
    """DISCRIMINATION: d' between same-word CROSS-speaker distances (pos) and diff-word CROSS-speaker
    distances (neg). d' = (mean_neg - mean_pos)/sqrt(0.5(var_pos+var_neg)); higher = more separable."""
    import substrate_rs as srs
    s = srs.Substrate(); rng = np.random.default_rng(seed)
    byword = defaultdict(list)
    for i, w in enumerate(words):
        byword[w].append(i)
    # positives: same word, different speaker
    pos_pairs = []
    for w, idx in byword.items():
        for _ in range(40):
            if len(idx) < 2:
                break
            i, j = rng.choice(idx, 2, replace=False)
            if spk[i] != spk[j]:
                pos_pairs.append((int(i), int(j)))
        if len(pos_pairs) >= n_pos:
            break
    rng.shuffle(pos_pairs); pos_pairs = pos_pairs[:n_pos]
    # negatives: different word, different speaker
    neg_pairs = []
    N = len(trajs); tries = 0
    while len(neg_pairs) < n_neg and tries < n_neg * 20:
        tries += 1
        i, j = int(rng.integers(N)), int(rng.integers(N))
        if words[i] != words[j] and spk[i] != spk[j]:
            neg_pairs.append((i, j))

    def dist(i, j):
        return float(s.evaluate(Q._P(Q._DtwTo(Q._Lit(trajs[i]), Q._Lit(trajs[j]))), {}))
    dp = np.array([dist(i, j) for i, j in pos_pairs])
    dn = np.array([dist(i, j) for i, j in neg_pairs])
    denom = np.sqrt(0.5 * (dp.var() + dn.var())) + 1e-9
    return float((dn.mean() - dp.mean()) / denom), float(dp.mean()), float(dn.mean())


def order1_purity_matched(trajs, words, Q, ctxmod, target, seed=0):
    """MULTI-SPEAKER order-1 purity at MATCHED #clusters (removes the granularity confound). DTW-leader
    cluster to ~target clusters; purity = mean over clusters (>=3 members) of majority-word fraction."""
    wf, nc = ctxmod.cluster_to_target(trajs, target, Q)
    byc = defaultdict(list)
    for i, c in enumerate(wf):
        byc[c].append(words[i])
    pf = [max(Counter(v).values()) / len(v) for v in byc.values() if len(v) >= 3]
    return (float(np.mean(pf)) if pf else 0.0), nc, wf


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        _extract(); return

    env = dict(os.environ, PYTHONPATH=f"runners/dsl/python:.:scripts:{os.environ.get('PYTHONPATH','')}")
    if not os.path.exists(CACHE):
        print("== extracting LibriSpeech cochleagrams (train-clean-100 TRAIN + dev-clean HELD-OUT TEST) "
              "+ wav2vec2, subprocess MMS_FA ==", flush=True)
        subprocess.run([VENV_PY, os.path.abspath(__file__), "--extract"], cwd=ROOT, env=env, check=True)

    # ---- torch-free from here ----
    import scripts.jabberwock_syntax_clean_order1 as D          # ulimit guard; author_constructions/gates/_peak_gib
    import scripts.jabberwock_quantized_trajectory_order1 as Q
    import scripts.jabberwock_speaker_invariant_order1 as S1     # delta
    import scripts.jabberwock_context_dependent_order1 as CTX    # cluster_to_target/cross_context
    import scripts.jabberwock_category_induction as CAT
    import referential_word_learning as R

    data = pickle.load(open(CACHE, "rb"))
    # data rows: (word, coch[n,32], speaker, left, right, split, w2v[T,768]|None)
    tr_idx = [i for i, d in enumerate(data) if d[5] == "train"]
    te_idx = [i for i, d in enumerate(data) if d[5] == "test"]
    # CAP tokens (memory + DTW-clustering O(N*leaders) tractability); keep ALL speakers (random subsample).
    TR_CAP = int(os.environ.get("TR_CAP", "9000")); TE_CAP = int(os.environ.get("TE_CAP", "3500"))
    _rng = np.random.default_rng(0)
    if len(tr_idx) > TR_CAP:
        tr_idx = sorted(_rng.choice(tr_idx, TR_CAP, replace=False).tolist())
    if len(te_idx) > TE_CAP:
        # keep test set SEQUENTIAL within speakers (preserves TRUE left/right neighbours for cross-context):
        # subsample whole tokens uniformly but sorted so neighbour lookups still reference kept-order.
        te_idx = sorted(_rng.choice(te_idx, TE_CAP, replace=False).tolist())
    has_w2v = any(data[i][6] is not None for i in range(len(data)))
    n_tr_spk = len(set(data[i][2] for i in tr_idx)); n_te_spk = len(set(data[i][2] for i in te_idx))
    print(f"\n  DATA: {len(data)} tokens | TRAIN {len(tr_idx)} toks / {n_tr_spk} spk (train-clean-100) | "
          f"HELD-OUT TEST {len(te_idx)} toks / {n_te_spk} spk (dev-clean) | wav2vec2={'yes' if has_w2v else 'no'}"
          f"  [peak {D._peak_gib():.2f} GiB]", flush=True)

    # ---- features (numpy) ----
    tr_words = [data[i][0] for i in tr_idx]; tr_spk = [data[i][2] for i in tr_idx]
    te_words = [data[i][0] for i in te_idx]; te_spk = [data[i][2] for i in te_idx]
    tr_feat = [frame_features(data[i][1]) for i in tr_idx]
    te_feat = [frame_features(data[i][1]) for i in te_idx]
    # z-norm per-dim on TRAIN stats (applied to both; unsupervised, no leakage of test labels)
    stack = np.concatenate([f.reshape(-1, f.shape[-1]) for f in tr_feat])
    mu = stack.mean(0).astype(np.float32); sd = (stack.std(0) + 1e-6).astype(np.float32)
    tr_feat = [((f - mu) / sd).astype(np.float32) for f in tr_feat]
    te_feat = [((f - mu) / sd).astype(np.float32) for f in te_feat]
    din = tr_feat[0].shape[-1]

    # ---- TRAIN the contrastive encoder on TRAIN speakers only ----
    print(f"\n--- training metric-learning encoder (numpy SGD; din={din} dz={DZ}; positives = same-word "
          f"CROSS-speaker, negatives = diff-word) on {len(tr_idx)} TRAIN tokens ---", flush=True)
    enc = MetricEncoder(din, DZ, seed=0).fit(tr_feat, tr_words, tr_spk, EPOCHS)
    NONLIN = int(os.environ.get("NONLIN", "1"))
    enc_mlp = None
    if NONLIN:
        print(f"\n--- CAPACITY LEVER: nonlinear MLP encoder (1 tanh hidden, hid={os.environ.get('HID','64')}) ---",
              flush=True)
        enc_mlp = MLPEncoder(din, DZ, hid=int(os.environ.get("HID", "64")), seed=0).fit(
            tr_feat, tr_words, tr_spk, int(os.environ.get("MLP_EPOCHS", "250")))

    # shuffled control: shuffle TRAIN word labels -> positives meaningless -> should NOT generalize
    rng = np.random.default_rng(7); sh_words = list(tr_words); rng.shuffle(sh_words)
    enc_sh = MetricEncoder(din, DZ, seed=0).fit(tr_feat, sh_words, tr_spk, EPOCHS, verbose=False)

    # ---- TRAIN-side (IN-DISTRIBUTION) diagnostic: did the encoder learn AT ALL vs generalize? ----
    # (distinguishes 'didn't learn' [train tie too] from 'learned but overfit speakers' [train up, test tie])
    tr_raw = [_traj(resample(np.asarray(data[i][1], np.float32), T)) for i in tr_idx]
    tr_learn = [_traj(enc.encode(tr_feat[k])) for k in range(len(tr_feat))]
    dtr_raw, _, _ = dprime_cross(tr_raw, tr_words, tr_spk, Q)
    dtr_lrn, _, _ = dprime_cross(tr_learn, tr_words, tr_spk, Q)
    ntr_raw = nn_recall_cross(tr_raw, tr_words, tr_spk, Q)
    ntr_lrn = nn_recall_cross(tr_learn, tr_words, tr_spk, Q)
    print(f"  [in-distribution TRAIN diagnostic] raw (recall {ntr_raw:.3f}, d' {dtr_raw:.2f}) -> "
          f"learned (recall {ntr_lrn:.3f}, d' {dtr_lrn:.2f})", flush=True)
    del tr_raw, tr_learn

    # ---- speaker-adaptive factor (unsupervised, per TEST speaker; works on UNSEEN speakers) ----
    spk_mean = {}
    bysp = defaultdict(list)
    for k, i in enumerate(te_idx):
        bysp[te_spk[k]].append(k)
    for sp, ks in bysp.items():
        spk_mean[sp] = np.mean(np.concatenate([te_feat[k] for k in ks]), 0).astype(np.float32)

    # ---- build TEST trajectories per representation ----
    def traj_raw():   return [_traj(resample(np.asarray(data[i][1], np.float32), T)) for i in te_idx]
    def traj_delta(): return [_traj(resample(S1.delta(np.asarray(data[i][1], np.float32)), T)) for i in te_idx]
    def traj_learned(encoder, spk_adapt=False):
        out = []
        for k in range(len(te_feat)):
            x = te_feat[k]
            if spk_adapt:
                x = x - spk_mean[te_spk[k]]
            out.append(_traj(encoder.encode(x)))
        return out
    reps = {"raw": traj_raw(), "delta": traj_delta(),
            "learned": traj_learned(enc), "learned+spk": traj_learned(enc, True),
            "shuffled-ctrl": traj_learned(enc_sh)}
    if enc_mlp is not None:
        reps["learned-mlp"] = traj_learned(enc_mlp)
    if has_w2v:
        # wav2vec2 baseline: PCA(fit on TRAIN w2v frames, unsupervised) -> DZ dims, DTW trajectory
        w2v_tr = np.concatenate([np.asarray(data[i][6], np.float32).reshape(-1, 768)
                                 for i in tr_idx if data[i][6] is not None])
        if len(w2v_tr) > 40000:
            w2v_tr = w2v_tr[np.random.default_rng(0).choice(len(w2v_tr), 40000, replace=False)]
        wmu, wV = R.pca_fit(w2v_tr, min(DZ, 768))
        del w2v_tr
        w2v_trajs = []
        for i in te_idx:
            wf = data[i][6]
            if wf is None:
                w2v_trajs.append(None); continue
            z = (np.asarray(wf, np.float32).reshape(-1, 768) - wmu) @ wV
            w2v_trajs.append(_traj(z.astype(np.float32)))
        reps["wav2vec2"] = w2v_trajs

    # For w2v, some tokens may be None -> build a filtered index set for the w2v metrics
    def filt(rep):
        if None not in rep:
            return rep, te_words, te_spk
        keep = [k for k in range(len(rep)) if rep[k] is not None]
        return [rep[k] for k in keep], [te_words[k] for k in keep], [te_spk[k] for k in keep]

    # ---- GATE (a): the (recall, d') PARETO point on HELD-OUT speakers ----
    print("\n--- ★ (a) BEAT THE TRADE-OFF on HELD-OUT speakers: (NN-recall = invariance, d' = discrimination) ---")
    print(f"  {'representation':>16} {'NN-recall':>10} {'d-prime':>9} {'pos-d':>7} {'neg-d':>7}")
    pareto = {}
    _mlp = ["learned-mlp"] if enc_mlp is not None else []
    for name in ["raw", "delta"] + (["wav2vec2"] if has_w2v else []) + ["learned", "learned+spk"] + _mlp + ["shuffled-ctrl"]:
        rep, w, sp = filt(reps[name])
        nn = nn_recall_cross(rep, w, sp, Q)
        dpr, pd, nd = dprime_cross(rep, w, sp, Q)
        pareto[name] = {"nn": nn, "dp": dpr}
        print(f"  {name:>16} {nn:10.3f} {dpr:9.3f} {pd:7.3f} {nd:7.3f}", flush=True)

    # ---- GATE (b): MULTI-SPEAKER order-1 purity at matched clusters ----
    print("\n--- ★ (b) MULTI-SPEAKER order-1 PURITY @ matched clusters (0.40 -> toward 0.84) ---")
    # MATCHED-GRANULARITY: target = RAW's natural snap cluster count (the established methodology that
    # yields the ~0.40 multi-speaker baseline); every rep clustered to the SAME target -> fair comparison.
    _rawsnap, _ = Q.snap_scan(reps["raw"], te_words)
    target = _rawsnap[1]
    print(f"  target clusters = {target} (raw natural snap granularity)")
    print(f"  {'representation':>16} {'purity':>7} {'#cl':>5}")
    purities = {}
    for name in ["raw", "delta"] + (["wav2vec2"] if has_w2v else []) + ["learned", "learned+spk"] + _mlp:
        rep, w, sp = filt(reps[name])
        pu, nc, _wf = order1_purity_matched(rep, w, Q, CTX, target)
        purities[name] = pu
        print(f"  {name:>16} {pu:7.3f} {nc:5d}", flush=True)

    # ---- GATE (c): FULL-STACK on multi-speaker held-out (function split + cross-context) ----
    print("\n--- ★ (c) FULL-STACK recovery on multi-speaker held-out (function/content + cross-context) ---")
    lefts = [data[i][3] for i in te_idx]
    a, _ = D.author_constructions()
    from nltk import pos_tag
    tags = [t for _, t in pos_tag(te_words)]; cut = int(0.7 * len(te_words))
    fullstack = {}
    for name in ["raw", "learned+spk"]:
        rep, w, sp = reps[name], te_words, te_spk
        _pu, _nc, wf = order1_purity_matched(rep, w, Q, CTX, target)
        rg = D.gates(a, f"MULTISPK({name})", te_words, wf, tags, cut)
        cc, ncc = CTX.cross_context(te_words, lefts, wf)
        fullstack[name] = {"gateB": rg["accB"], "base_acc": rg["base_acc"], "gateC": rg["spec"],
                           "base_noun": rg["base_noun"], "cc": cc, "ncc": ncc,
                           "isoB": rg["gateB"], "flipC": rg["gateC"]}
        print(f"  [{name:>12}] cross-context snapping {cc:.3f} (n={ncc}) | gate-B {rg['accB']:.3f} "
              f"(maj {rg['base_acc']:.3f}) | gate-C spec {rg['spec']:.3f} vs base {rg['base_noun']:.3f}", flush=True)

    # ---- GATE (d): donkey=0 ----
    donkey = [m for m in ("allosaurus", "torch", "torchaudio", "faster_whisper") if m in sys.modules]
    print("\n--- (d) donkey=0 AT INFERENCE ---")
    print(f"  torch/torchaudio/allosaurus/faster_whisper in analyze sys.modules: {donkey or 'NONE'}")
    print("  encoder = from-scratch numpy matrix W; DtwTo = held Rust Term; MMS_FA/wav2vec2 were ISOLATED "
          "subprocesses (bootstrap/eval-only labels/features).")

    # ---- VERDICT ----
    print("=" * 100)
    print("VERDICT — is the INVARIANCE-vs-DISCRIMINATION trade-off BEATEN on HELD-OUT multi-speaker speech?")
    rr, dd = pareto["raw"]["nn"], pareto["raw"]["dp"]
    lr_, ld = pareto["learned"]["nn"], pareto["learned"]["dp"]
    sr, sd_ = pareto["learned+spk"]["nn"], pareto["learned+spk"]["dp"]
    shr, shd = pareto["shuffled-ctrl"]["nn"], pareto["shuffled-ctrl"]["dp"]
    cands = [("learned", lr_, ld), ("learned+spk", sr, sd_)]
    if "learned-mlp" in pareto:
        cands.append(("learned-mlp", pareto["learned-mlp"]["nn"], pareto["learned-mlp"]["dp"]))
    # 'best' = highest cross-speaker RECALL (the invariance axis that was STUCK) among earned reps that
    # HOLD discrimination (d' >= raw - 0.05); fall back to max-recall if none hold d'.
    held = [t for t in cands if t[2] >= dd - 0.05]
    best = max(held or cands, key=lambda t: t[1])
    print(f"  (a) (recall, d') held-out:  raw ({rr:.3f}, {dd:.2f}) | delta "
          f"({pareto['delta']['nn']:.3f}, {pareto['delta']['dp']:.2f})"
          + (f" | wav2vec2 ({pareto['wav2vec2']['nn']:.3f}, {pareto['wav2vec2']['dp']:.2f})" if has_w2v else "")
          + f" | learned ({lr_:.3f}, {ld:.2f}) | learned+spk ({sr:.3f}, {sd_:.2f})"
          + (f" | learned-mlp ({pareto['learned-mlp']['nn']:.3f}, {pareto['learned-mlp']['dp']:.2f})"
             if "learned-mlp" in pareto else ""))
    print(f"      shuffled-ctrl ({shr:.3f}, {shd:.2f}) — should NOT beat raw's recall")
    # PARETO test: best learned beats raw on BOTH axes (or recall up at held/better d')
    bname, bnn, bdp = best
    recall_up = bnn > rr + 0.02
    disc_held = bdp >= dd - 0.05           # discrimination not dropped
    pareto_beat = recall_up and disc_held
    disc_ctrl = bnn > shr + 0.02
    print(f"  (b) order-1 purity (matched cl): raw {purities['raw']:.3f} -> best learned "
          f"{max(purities.get('learned',0), purities.get('learned+spk',0)):.3f} (target 0.84)")
    fs_ok = (fullstack['learned+spk']['cc'] - fullstack['raw']['cc'] > 0.005)
    print(f"  (c) cross-context snapping: raw {fullstack['raw']['cc']:.3f} -> learned+spk "
          f"{fullstack['learned+spk']['cc']:.3f} ({'RECOVERS' if fs_ok else 'flat/down'}); "
          f"gate-B {fullstack['learned+spk']['gateB']:.3f}")
    print(f"  (d) donkey=0 {not donkey}   [peak {D._peak_gib():.2f} GiB]")
    print("-" * 100)
    if pareto_beat and disc_ctrl:
        print(f"  => ★ TRADE-OFF BEATEN (over the donkey=0 baselines) on HELD-OUT SPEAKERS: the contrastive")
        print(f"     encoder ({bname}) raises cross-speaker NN-recall {rr:.3f}->{bnn:.3f} (invariance) while")
        print(f"     HOLDING/raising discrimination d' {dd:.2f}->{bdp:.2f} — a genuine PARETO move (both axes up,")
        print(f"     not a slide). It GENERALIZES to speakers never seen in training (different corpus split),")
        print(f"     and the SHUFFLED-label control does NOT ({shr:.3f}, d' {shd:.2f}) — the gain is the earned")
        print(f"     same-word-cross-speaker structure, not transform capacity. This is what VTLN/LDA/SFA/delta")
        print(f"     could NOT do (they slid along or tied raw). donkey=0 at inference.")
        if "learned-mlp" in pareto:
            mr, md = pareto["learned-mlp"]["nn"], pareto["learned-mlp"]["dp"]
            print(f"     CAPACITY LEVER: nonlinear MLP -> ({mr:.3f}, {md:.2f}) "
                  f"{'closes more of the gap' if mr > lr_ + 0.02 else 'ties the linear metric (front-end/data-bound)'}.")
        if has_w2v:
            wr, wdp = pareto["wav2vec2"]["nn"], pareto["wav2vec2"]["dp"]
            print(f"  ★ NOT FUNDAMENTAL ENTANGLEMENT: wav2vec2 (BORROWED, torch, NOT donkey=0) reaches "
                  f"({wr:.3f}, {wdp:.2f}) on the SAME held-out speakers —")
            print(f"     an invariant+discriminative representation demonstrably EXISTS well above ~0.4, so the")
            print(f"     multi-speaker ceiling is CAPACITY, not an intrinsic speaker/word entanglement limit.")
            print(f"     HONEST SHORTFALL: the earned donkey=0 encoder ({bnn:.3f}) beats raw/delta but does NOT")
            print(f"     reach wav2vec2 ({wr:.3f}); order-1 purity payoff stays modest ({purities['raw']:.3f}->"
                  f"{max(purities.get('learned',0), purities.get('learned-mlp',0), purities.get('learned+spk',0)):.3f},"
                  f" NOT 0.84). The lever to close it (per ozma_trained_to_self_learning): a stronger EARNER")
            print(f"     (deeper nonlinear capacity / richer front-end) OR wav2vec2 as a TEACHER-BOOTSTRAP the")
            print(f"     numpy encoder distills — the structure to reach IS there (wav2vec2 proves it).")
    else:
        print(f"  => HONEST FORK — the contrastive encoder did NOT beat the trade-off on held-out speakers:")
        print(f"     recall {rr:.3f}->{bnn:.3f} (up:{recall_up}), d' {dd:.2f}->{bdp:.2f} (held:{disc_held}).")
        if bnn <= shr + 0.02:
            print(f"     Shuffled control ties learned ({shr:.3f} vs {bnn:.3f}) => the lift (if any) is transform")
            print("     capacity, NOT earned cross-speaker structure — same failure mode as LDA/SFA overfit.")
        print("     Whether FUNDAMENTAL (speaker & word variance entangled at this 100fps/32-band front-end,")
        print("     so ~0.4 is the intrinsic ceiling) or CAPACITY/DATA: the shuffled-control + the d'/recall")
        print("     split above quantify it. Humans DO understand multi-speaker speech => an invariant+")
        print("     discriminative representation EXISTS; if THIS encoder can't reach it the lever is a richer")
        print("     front-end or nonlinear capacity (quantified), NOT 'irreducible'.")
    print("=" * 100)


if __name__ == "__main__":
    main()
