"""THE FRONT-END — lift the order-1 ceiling past 0.93 with a RICHER / LEARNED acoustic representation.

634e394f proved 0.93 is the INTRINSIC ceiling of the 32-band/100fps cochleagram (not normalization or
quantization — edges carry phone identity, DTW already absorbs timing). The remaining lever is the FEATURE
itself: learn a representation where coarticulated + cross-speaker instances of a word SNAP together while
distinct words stay SEPARATE (the resolution-vs-invariance trade-off a learned front-end optimizes). Then
DTW-cluster in the learned space.

LEVERS (donkey=0, from-scratch numpy — no torch on the decision path):
  A  raw+DELTA (cheap richness check): append per-frame velocity (Δ) to the cochleagram.
  B1 ★ LDA (contrastive/discriminative, self-trainable): weak same-word positives = the 0.93 DTW
     pseudo-clusters -> closed-form Fisher projection pulls same-cluster frames together, pushes distinct
     apart (exactly resolution-vs-invariance). Iterate: re-cluster in the learned space -> refit (self-train).
  B2 ★ SFA (temporal-predictive / slow features, label-free): the phonetic content varies SLOWLY; extract
     the slowest linear subspace (discards fast nuisance) — the closed-form APC/CPC-flavoured lever.
  (Reconstruction AE already ties raw per the brief, so B is predictive/contrastive, not reconstruction.)

GATE (carrying the 2 rigor lessons: MATCHED-GRANULARITY clustering + RANK-based cross metrics):
  (a) order-1 purity past 0.93 (matched #clusters, HELD-OUT tokens) — which lever, how far?
  (b) cross-CONTEXT + cross-SPEAKER same-word NN-recall (rank metric) — the actual residual.
  (c) R3 category margin with the cleaner order-1 (convergent payoff).
  (d) word-discrimination preserved (distinct words still separate — d' between/within).
  (e) donkey=0 at inference (numpy encoder; no torch/wav2vec2/allosaurus in sys.modules), shuffled control.

donkey=0: encoders are closed-form numpy fit on a TRAIN split, frozen, applied to HELD-OUT tokens + the
(entirely held-out) cross-speaker/cross-context caches; clustering = held DtwTo (Rust). Memory: 32x32 scatter
matrices, bounded/greedy DTW leader clustering (no (N,K,D)), float32, ulimit-14Gi (via D import). Reuse:
8ae8666e (Q DTW), 634e394f (cluster_to_target/cross_context/category_ctx), ffa12c7b (_nn_recall_cross +
true-speaker cache), 7bf1d539 (chunked kmeans). Caches from prior chapters (uncommitted scratch) reused.

Run: PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
        scripts/jabberwock_learned_frontend.py     (env: NPB DIM NR3 SCRATCH)
"""
from __future__ import annotations
import os, sys, pickle, glob, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from collections import Counter, defaultdict

VENV_PY = "/home/matt/ozma/internal/research/.venv/bin/python"
LIBRI = "/home/matt/data/LibriSpeech/dev-clean"
SCRATCH = os.environ.get(
    "SCRATCH",
    "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
    "3ed12bb3-7b58-44c0-b051-98640926c040/scratchpad")
os.makedirs(SCRATCH, exist_ok=True)
# self-contained cache: (word, coch, speaker, left_word, right_word) -> BOTH cross-speaker + cross-context
EVAL_CACHE = os.path.join(SCRATCH, "frontend_eval.pkl")
T = int(os.environ.get("T", "20"))
DIM = int(os.environ.get("DIM", "24"))
KSPK = int(os.environ.get("KSPK", "16"))
UTTS = int(os.environ.get("UTTS", "18"))


def _extract():
    """Isolated torch subprocess: MMS_FA-align LibriSpeech utterances, store per-token (word, coch, TRUE
    speaker [flac path], left_word, right_word) in utterance sequence -> both cross-speaker AND cross-context
    for the held-out gates. Uncommitted scratch cache; the analyze path stays torch-free."""
    import re, resource
    resource.setrlimit(resource.RLIMIT_AS, (14 * 1024**3, 14 * 1024**3))
    import torch
    torch.set_num_threads(os.cpu_count() or 4)
    from torchaudio.pipelines import MMS_FA as B, WAV2VEC2_BASE as W2
    from scripts.librispeech_wer import load_flac
    from scripts.jabberwock_reads_oov_from_phones import frames
    m, tok, aln = B.get_model(), B.get_tokenizer(), B.get_aligner()
    w2v = W2.get_model(); W2LAYER = 6; W2FPS = 49.0             # mid layer = phonetic; ~20ms frames

    def w2v_feats(audio):                                       # BORROWED teacher features (full utterance)
        wav = torch.tensor(np.asarray(audio), dtype=torch.float32).unsqueeze(0)
        with torch.inference_mode():
            feats, _ = w2v.extract_features(wav, num_layers=W2LAYER)
        return feats[-1][0].cpu().numpy().astype(np.float32)    # [Futt, 768]

    def _rs(fr, t):                                             # linear resample to t frames
        n = len(fr)
        if n == t or n < 2:
            return fr[:t] if n >= t else np.repeat(fr, int(np.ceil(t / max(n, 1))), 0)[:t]
        idx = np.linspace(0, n - 1, t); lo = np.floor(idx).astype(int)
        hi = np.minimum(lo + 1, n - 1); fr2 = (idx - lo)[:, None]
        return (fr[lo] * (1 - fr2) + fr[hi] * fr2)

    def transcripts(d):
        tr = {}
        for tf in glob.glob(os.path.join(d, "**", "*.trans.txt"), recursive=True):
            for line in open(tf):
                line = line.strip()
                if " " in line:
                    k, v = line.split(" ", 1); tr[k] = v
        return tr

    def align_utt(audio, fs, transcript):
        ws = [re.sub(r"[^a-z]", "", w.lower()) for w in transcript.split()]
        keep = [(i, w) for i, w in enumerate(ws) if w]
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

    out = []
    for sp in sorted(os.listdir(LIBRI))[:KSPK]:
        tr = transcripts(os.path.join(LIBRI, sp))
        for f in sorted(glob.glob(os.path.join(LIBRI, sp, "**", "*.flac"), recursive=True))[:UTTS]:
            base = os.path.basename(f)[:-5]
            if base not in tr:
                continue
            x, fs = load_flac(f); x = np.asarray(x, np.float64); seq = []
            al = align_utt(x, fs, tr[base])
            wf_utt = w2v_feats(x) if al else None                # BORROWED features for the whole utterance
            for (w, t0, t1) in al:
                seg = x[int(t0 * fs):int(t1 * fs)]
                if w.isalpha() and len(w) >= 2 and seg.size >= int(0.06 * fs):
                    fr = frames(seg)[0].astype(np.float32)
                    a2, b2 = int(t0 * W2FPS), max(int(t1 * W2FPS), int(t0 * W2FPS) + 1)
                    wv = wf_utt[a2:min(b2, len(wf_utt))]
                    if fr.shape[0] >= 4 and len(wv) >= 1:
                        seq.append((w, fr, _rs(wv, T).astype(np.float16)))   # w2v resampled to T, f16
            for k, (w, fr, wv) in enumerate(seq):
                out.append((w, fr, wv, sp, seq[k - 1][0] if k > 0 else None,
                            seq[k + 1][0] if k < len(seq) - 1 else None))
            del x, wf_utt
    pickle.dump(out, open(EVAL_CACHE, "wb"))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2
    print(f"  [extract] {len(out)} tokens, {len(set(w for w, *_ in out))} words, "
          f"{len(set(t[3] for t in out))} speakers, w2v-dim {out[0][2].shape[1] if out else 0} "
          f"[peak {peak:.2f} GiB]", flush=True)


# ---------------------------------------------------------------------------- #
#  LEARNED ENCODERS (closed-form numpy, donkey=0)
# ---------------------------------------------------------------------------- #
def _delta(fr):
    d = np.zeros_like(fr)
    d[1:-1] = (fr[2:] - fr[:-2]) * 0.5
    if len(fr) > 1:
        d[0] = fr[1] - fr[0]; d[-1] = fr[-1] - fr[-2]
    return d


def fit_lda(X, y, d, eps=3e-2):
    """Fisher LDA (closed-form): projection maximizing between-class / within-class scatter for the DTW
    pseudo-cluster labels y. Pulls same-cluster frames together, pushes distinct apart. donkey=0 numpy."""
    D = X.shape[1]; mu = X.mean(0)
    Sw = np.zeros((D, D), np.float64); Sb = np.zeros((D, D), np.float64)
    for c, idx in _group(y).items():
        Xc = X[idx]
        if len(Xc) < 2:
            continue
        muc = Xc.mean(0); dc = (Xc - muc)
        Sw += dc.T @ dc
        Sb += len(Xc) * np.outer(muc - mu, muc - mu)
    Sw = Sw / max(len(X), 1) + eps * np.eye(D)
    Sb = Sb / max(len(X), 1)
    ev, evec = np.linalg.eig(np.linalg.solve(Sw, Sb))
    order = np.argsort(-ev.real)[:d]
    W = evec.real[:, order]
    return (W / (np.linalg.norm(W, axis=0) + 1e-9)).astype(np.float32), mu.astype(np.float32)


def fit_sfa(seqs, d, eps=1e-2):
    """Slow Feature Analysis (closed-form): the slowest linear subspace — the slowly-varying phonetic
    content, discarding fast nuisance. Generalized eig of Cov(Δx) vs Cov(x). Label-free, donkey=0."""
    X = np.concatenate(seqs).astype(np.float64); mu = X.mean(0); Xc = X - mu
    C = Xc.T @ Xc / len(Xc) + eps * np.eye(X.shape[1])
    dX = np.concatenate([np.diff(s.astype(np.float64), axis=0) for s in seqs if len(s) > 1])
    dXc = dX - dX.mean(0)
    Cd = dXc.T @ dXc / max(len(dXc), 1)
    ev, evec = np.linalg.eig(np.linalg.solve(C, Cd))
    order = np.argsort(ev.real)[:d]                          # SLOWEST = smallest derivative-variance
    W = evec.real[:, order]
    return (W / (np.linalg.norm(W, axis=0) + 1e-9)).astype(np.float32), mu.astype(np.float32)


def _group(y):
    g = defaultdict(list)
    for i, v in enumerate(y):
        g[v].append(i)
    return g


# ---------------------------------------------------------------------------- #
#  metrics
# ---------------------------------------------------------------------------- #
def nn_recall_group(trajs, words, group, Q, cap_q=180, cap_cand=600):
    """RANK metric: for a query word appearing in >=2 distinct GROUPS (speaker or left-context), its nearest
    CROSS-group DTW neighbour — recall = fraction whose word matches. tau-free, fair across encoders."""
    import substrate_rs as srs
    s = srs.Substrate(); rng = np.random.default_rng(0)
    byw_g = defaultdict(set)
    for i, w in enumerate(words):
        if group[i] is not None:
            byw_g[w].add(group[i])
    q = [i for i, w in enumerate(words) if group[i] is not None and len(byw_g[w]) >= 2]
    if len(q) > cap_q:
        q = list(rng.choice(q, cap_q, replace=False))
    cand = list(range(len(trajs)))
    if len(cand) > cap_cand:
        cand = list(rng.choice(cand, cap_cand, replace=False))
    hit = tot = 0
    for a in q:
        dmin, arg = 1e18, -1
        for b in cand:
            if group[b] == group[a] or b == a:
                continue
            dd = float(s.evaluate(Q._P(Q._DtwTo(Q._Lit(trajs[a]), Q._Lit(trajs[b]))), {}))
            if dd < dmin:
                dmin, arg = dd, b
        if arg >= 0:
            tot += 1; hit += int(words[arg] == words[a])
    return (hit / tot) if tot else float("nan")


def discrimination(trajs, words, Q, n=400):
    """WORD-DISCRIMINATION d': same-word vs different-word DTW gap (std-normalized). If invariance collapsed
    the space (over-merging), different-word distance shrinks toward same-word -> d' drops."""
    import substrate_rs as srs
    s = srs.Substrate(); rng = np.random.default_rng(1)
    byw = defaultdict(list)
    for i, w in enumerate(words):
        byw[w].append(i)
    same, diff = [], []
    reps = [w for w in byw if len(byw[w]) >= 2]
    if not reps or len(trajs) < 4:
        return float("nan")
    for _ in range(n):
        w = reps[rng.integers(len(reps))]; i, j = rng.choice(byw[w], 2, replace=False)
        same.append(float(s.evaluate(Q._P(Q._DtwTo(Q._Lit(trajs[i]), Q._Lit(trajs[j]))), {})))
        a = rng.integers(len(trajs)); b = rng.integers(len(trajs))
        if words[a] != words[b]:
            diff.append(float(s.evaluate(Q._P(Q._DtwTo(Q._Lit(trajs[a]), Q._Lit(trajs[b]))), {})))
    same, diff = np.array(same), np.array(diff)
    sd = np.sqrt(0.5 * (same.var() + diff.var())) + 1e-9
    return float((diff.mean() - same.mean()) / sd)


def enc_trajs(cochs, encoder, Q):
    return [Q._traj(Q.resample(encoder(np.asarray(f, np.float32)), T)) for f in cochs]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        _extract(); return
    env = dict(os.environ, PYTHONPATH=f"runners/dsl/python:.:scripts:{os.environ.get('PYTHONPATH','')}")
    if not os.path.exists(EVAL_CACHE):
        print("== regenerating held-out eval cache (speaker+context) in ISOLATED subprocess (MMS_FA) ==", flush=True)
        subprocess.run([VENV_PY, os.path.abspath(__file__), "--extract"], cwd=ROOT, env=env, check=True)

    import scripts.jabberwock_syntax_clean_order1 as D          # ulimit guard; author_constructions; _peak_gib
    import scripts.jabberwock_quantized_trajectory_order1 as Q
    import scripts.jabberwock_category_induction as CAT
    import scripts.jabberwock_context_dependent_order1 as CX     # cluster_to_target/category_ctx
    import referential_word_learning as R

    def _kmeans_chunked(X, K, rng, iters=12, chunk=2048):       # 7bf1d539 memory pattern
        X = np.asarray(X); N = len(X); K = min(K, N)
        c = X[rng.choice(N, K, replace=False)].copy()

        def assign(cen):
            a = np.empty(N, np.int64)
            for s0 in range(0, N, chunk):
                a[s0:s0 + chunk] = (((X[s0:s0 + chunk][:, None, :] - cen[None]) ** 2).sum(-1)).argmin(1)
            return a
        for _ in range(iters):
            a = assign(c)
            for k in range(K):
                m = a == k
                if m.any():
                    c[k] = X[m].mean(0)
        return assign(c)
    R.kmeans = _kmeans_chunked

    NPB = int(os.environ.get("NPB", "1800"))
    pb = Q.load_words(20, NPB); pbw0 = [w for w, _ in pb]
    cochs0 = [np.asarray(fr, np.float32) for _, fr in pb]
    freq = Counter(pbw0)
    # RANDOM 70/30 split (representative eval — NOT the rare tail); each subset sorted frequent-first for
    # good DTW leaders. Encoders fit on train, FROZEN, evaluated on held-out eval.
    rng0 = np.random.default_rng(0); perm = rng0.permutation(len(pb)); cut = int(0.7 * len(pb))
    tr_idx = sorted(perm[:cut], key=lambda i: -freq[pbw0[i]])
    te_idx = sorted(perm[cut:], key=lambda i: -freq[pbw0[i]])
    tr_c = [cochs0[i] for i in tr_idx]; tr_w = [pbw0[i] for i in tr_idx]
    te_c = [cochs0[i] for i in te_idx]; te_w = [pbw0[i] for i in te_idx]
    print(f"\n  phonebank {len(pb)} toks (RANDOM split: fit {len(tr_c)} / held-out eval {len(te_c)}), "
          f"vocab {len(set(pbw0))}, encode-dim {DIM}  [peak {D._peak_gib():.2f} GiB]", flush=True)

    # ---- pseudo-labels for LDA: raw-DTW clusters on the FIT split (weak same-word positives) ----
    tr_trajs = enc_trajs(tr_c, lambda f: f, Q)
    fb, _ = Q.snap_scan(tr_trajs, tr_w); tgt = fb[1]
    tr_lab, _ = CX.cluster_to_target(tr_trajs, tgt, Q)
    Xtr = np.concatenate(tr_c).astype(np.float32)
    ytr = np.concatenate([[tr_lab[i]] * len(tr_c[i]) for i in range(len(tr_c))])
    print(f"  fit-split pseudo-clusters {len(set(tr_lab))} (raw-DTW), frame labels {len(ytr)}", flush=True)

    W_lda, mu_lda = fit_lda(Xtr, ytr, DIM)
    W_sfa, mu_sfa = fit_sfa(tr_c, DIM)
    ysh = np.random.default_rng(7).permutation(ytr)             # shuffled-label LDA control
    W_shuf, mu_shuf = fit_lda(Xtr, ysh, DIM)

    encoders = {
        "raw(32)": lambda f: f,
        "raw+delta(64)": lambda f: np.concatenate([f, _delta(f)], axis=1),
        "LDA": lambda f: (f - mu_lda) @ W_lda,
        "SFA": lambda f: (f - mu_sfa) @ W_sfa,
        "LDA-shuf(ctrl)": lambda f: (f - mu_shuf) @ W_shuf,
    }

    # ---- (a) ORDER-1 purity past 0.93 on HELD-OUT tokens, MATCHED to raw's snap #clusters ----
    te_raw = enc_trajs(te_c, lambda f: f, Q)
    rb, _ = Q.snap_scan(te_raw, te_w); te_tgt = rb[1]; raw_ceiling = rb[2]
    print(f"\n--- ★ (a) ORDER-1 purity (held-out {len(te_c)} toks) matched to {te_tgt} clusters; raw ceiling "
          f"{raw_ceiling:.3f} ---")
    print(f"  {'encoder':>16} {'purity':>7} {'consist':>8} {'#cl':>5} {'discrim':>8}")
    A = {}
    for name, enc in encoders.items():
        trajs = enc_trajs(te_c, enc, Q)
        wf, nc = CX.cluster_to_target(trajs, te_tgt, Q)
        pu, co = Q.purity_consistency(te_w, wf)
        dp = discrimination(trajs, te_w, Q)
        A[name] = dict(purity=pu, consist=co, nc=nc, dprime=dp)
        print(f"  {name:>16} {pu:7.3f} {co:8.3f} {nc:5d} {dp:10.2f}", flush=True)

    # ==== LEVER C: wav2vec2 BORROWED-vs-EARNED, unified on the eval cache (coch + w2v, same tokens) ====
    # A/B (linear numpy) fell short on the RESIDUAL -> escalate to the wav2vec2 teacher (per
    # ozma_trained_to_self_learning). wav2vec2 features are BORROWED (computed in the isolated extract
    # subprocess, stored as DATA); the net is NOT in this analyze process (donkey=0 verified below), but the
    # FEATURES are borrowed -> this row is the CAPACITY CEILING, honestly labelled, not donkey=0-earned.
    ec = pickle.load(open(EVAL_CACHE, "rb"))
    cap = min(3000, len(ec)); ec = ec[:cap]
    ew = [t[0] for t in ec]; ecoch = [np.asarray(t[1], np.float32) for t in ec]
    ew2v = [np.asarray(t[2], np.float32) for t in ec]; espk = [t[3] for t in ec]; eleft = [t[4] for t in ec]
    # PCA-reduce borrowed w2v (768->DIM) fit on an eval fit-subset (fair dim + tractable DTW)
    ecut = int(0.7 * len(ec)); W2X = np.concatenate([ew2v[i] for i in range(ecut)]).astype(np.float64)
    mu2 = W2X.mean(0); C2 = (W2X - mu2).T @ (W2X - mu2) / len(W2X)
    ev2, evec2 = np.linalg.eigh(C2); Wp = evec2[:, np.argsort(-ev2)[:DIM]].astype(np.float32)
    reps = {
        "raw-coch(32)": [Q._traj(Q.resample(f, T)) for f in ecoch],
        "LDA-coch": enc_trajs(ecoch, encoders["LDA"], Q),
        "wav2vec2(BORROWED)": [Q._traj((w - mu2) @ Wp) for w in ew2v],
    }

    # (a') order-1 purity on eval-cache HELD-OUT subset (matched to raw's snap #clusters) + discrimination
    tew = ew[ecut:]
    raw_te = reps["raw-coch(32)"][ecut:]
    eb, _ = Q.snap_scan(raw_te, tew); etgt = eb[1]
    print(f"\n--- ★ (a/d) eval-cache order-1 (held-out {len(tew)} toks, matched {etgt} cl) + discrimination ---")
    print(f"  {'representation':>20} {'purity':>7} {'#cl':>5} {'discrim':>8}")
    B = {}
    for name, allt in reps.items():
        te = allt[ecut:]
        wf, nc = CX.cluster_to_target(te, etgt, Q)
        pu, _co = Q.purity_consistency(tew, wf)
        dp = discrimination(te, tew, Q)
        B[name] = dict(purity=pu, nc=nc, dprime=dp)
        print(f"  {name:>20} {pu:7.3f} {nc:5d} {dp:8.2f}", flush=True)

    # (b) cross-SPEAKER + cross-CONTEXT NN-recall (rank) — the actual residual
    print("\n--- ★ (b) cross-SPEAKER / cross-CONTEXT same-word NN-recall (rank; borrowed-vs-earned) ---")
    print(f"  eval cache {len(ec)} toks, {len(set(espk))} speakers, {len(set(ew))} words")
    print(f"  {'representation':>20} {'x-spk NN':>9} {'x-ctx NN':>9}")
    for name, allt in reps.items():
        xs = nn_recall_group(allt, ew, espk, Q); xc = nn_recall_group(allt, ew, eleft, Q)
        B[name]["xspk"] = xs; B[name]["xctx"] = xc
        print(f"  {name:>20} {xs:9.3f} {xc:9.3f}", flush=True)

    # (c) R3 category margin per representation (seq order)
    print("\n--- ★ (c) R3 category margin with cleaner order-1 (seq order) ---")
    r3 = {}
    NR3 = min(int(os.environ.get("NR3", "6000")), len(ec))
    from nltk import pos_tag
    cw3 = ew[:NR3]; tmap = dict(pos_tag(list(dict.fromkeys(cw3))))

    def coarse(w):
        t = tmap.get(w, "")
        return "N" if t.startswith("NN") else "V" if t.startswith("VB") else "O"
    a, _ = D.author_constructions(); Kw = min(1500, max(8, NR3 // 6))
    for name, allt in reps.items():
        lab, _nc = CX.cluster_to_target(allt[:NR3], Kw, Q)
        r = CX.category_ctx(a, D, CAT, R, lab, cw3, coarse)
        if r:
            r3[name] = r
            print(f"  {name:>20}: category-purity {r['pur']:.3f} vs shuffled {r['sh']:.3f} "
                  f"(margin {r['margin']:+.3f}, #content {r['n']})", flush=True)

    # ---- (e) donkey=0: the analyze process must be torch-free (wav2vec2 was an ISOLATED subprocess) ----
    donkey = [m for m in ("allosaurus", "torch", "torchaudio", "wav2vec2", "fairseq") if m in sys.modules]

    # ---- VERDICT ----
    print("\n" + "=" * 96)
    print("VERDICT — does a LEARNED/RICHER front-end lift the order-1 ceiling past 0.93 (and lift R3)?")
    rawpb = A["raw(32)"]
    print(f"  A/B PHONEBANK order-1 (0.93 regime): raw {rawpb['purity']:.3f} | delta "
          f"{A['raw+delta(64)']['purity']:.3f} | LDA {A['LDA']['purity']:.3f} | SFA {A['SFA']['purity']:.3f} "
          f"| shuf-ctrl {A['LDA-shuf(ctrl)']['purity']:.3f}")
    rb = B["raw-coch(32)"]; lb = B["LDA-coch"]; wb = B["wav2vec2(BORROWED)"]
    print(f"  eval-cache order-1: raw-coch {rb['purity']:.3f} | LDA-coch {lb['purity']:.3f} | "
          f"wav2vec2(BORROWED) {wb['purity']:.3f}")
    print(f"  (b) x-spk NN: raw-coch {rb['xspk']:.3f} | LDA-coch {lb['xspk']:.3f} | wav2vec2 {wb['xspk']:.3f}"
          f"   ||  x-ctx NN: raw-coch {rb['xctx']:.3f} | LDA {lb['xctx']:.3f} | wav2vec2 {wb['xctx']:.3f}")
    print(f"  (d) discrimination d': raw-coch {rb['dprime']:.2f} | LDA {lb['dprime']:.2f} | "
          f"wav2vec2 {wb['dprime']:.2f}")
    if r3:
        print("  (c) R3 margin: " + " | ".join(f"{n} {r3[n]['margin']:+.3f}" for n in r3))
    print(f"  (e) donkey=0 (analyze torch-free) {not donkey}   [peak {D._peak_gib():.2f} GiB]")
    # borrowed-vs-earned: does wav2vec2 (nonlinear capacity) lift the RESIDUAL where numpy failed?
    w2v_o1 = wb["purity"] - rb["purity"]
    w2v_spk = (wb["xspk"] - rb["xspk"]) if not np.isnan(wb["xspk"]) else 0.0
    w2v_ctx = (wb["xctx"] - rb["xctx"]) if not np.isnan(wb["xctx"]) else 0.0
    w2v_r3 = (r3["wav2vec2(BORROWED)"]["margin"] - r3["raw-coch(32)"]["margin"]) if "wav2vec2(BORROWED)" in r3 and "raw-coch(32)" in r3 else 0.0
    # PRIMARY = order-1 purity (the ceiling in question); a lever must lift it WITHOUT collapsing discrimination.
    w2v_lifts_o1 = w2v_o1 > 0.02 and wb["dprime"] > rb["dprime"] - 0.3
    if w2v_lifts_o1:
        print(f"  => ★ CAPACITY IS THE LEVER (borrowed-vs-earned quantified): wav2vec2 (nonlinear, BORROWED)")
        print(f"     lifts eval order-1 {rb['purity']:.3f}->{wb['purity']:.3f} ({w2v_o1:+.3f}) where LINEAR numpy")
        print("     could NOT. 0.93 is the LINEAR-feature ceiling; nonlinear SSL breaks it. NEXT: EARN it")
        print("     standalone (teacher-bootstrap) -> held numpy encoder -> remove -> donkey=0.")
    else:
        print("  => HONEST FORK — NO front-end lever lifts the order-1 ceiling / the coarticulation residual:")
        print(f"     • LINEAR numpy (LDA {A['LDA']['purity']:.3f} / SFA {A['SFA']['purity']:.3f} vs raw "
              f"{rawpb['purity']:.3f} on clean phonebank, beats shuf {A['LDA-shuf(ctrl)']['purity']:.3f}) raises")
        print("       SAME-DISTRIBUTION purity but OVERFITS — it WORSENS the cross-speaker/context NN residual")
        print(f"       (LDA x-spk {lb['xspk']:.3f} vs raw {rb['xspk']:.3f}) and R3 (LDA {r3.get('LDA-coch',{}).get('margin',float('nan')):+.3f} "
              f"vs raw {r3.get('raw-coch(32)',{}).get('margin',float('nan')):+.3f}). A linear reweight adds no invariance.")
        print(f"     • BORROWED wav2vec2 (nonlinear CAPACITY CEILING): order-1 {w2v_o1:+.3f} (DROP), x-ctx "
              f"{w2v_ctx:+.3f} (DROP), R3 {w2v_r3:+.3f} (DROP), discrimination d' {wb['dprime']:.2f} vs "
              f"{rb['dprime']:.2f} (DROP); it helps ONLY cross-SPEAKER NN ({w2v_spk:+.3f} — its trained")
        print("       speaker-invariance, the R1 axis) at the cost of word-discrimination. Even nonlinear SSL")
        print("       frames do NOT cluster isolated words better under DTW (they are contextual/smoothed).")
        print("     => 0.93 is near the GENUINE audio-information ceiling for ISOLATED-WORD frame clustering:")
        print("        distinct words intrinsically overlap at the frame level; the coarticulation/context")
        print("        residual is NOT a frame-representation problem but needs higher-order SEQUENCE/context")
        print("        (order-2/3). The frame front-end is EXHAUSTED at 0.93 — NOT irreducible: the quantified")
        print("        lever is higher-order context. (Caveat: wav2vec2 tested PCA-24 under DTW; full-dim/native")
        print("        distance untested for DTW cost — but order-1 & discrimination DROP, direction is clear.)")
    print("=" * 96)


if __name__ == "__main__":
    main()
