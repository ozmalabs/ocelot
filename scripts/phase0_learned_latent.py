"""PHASE 0 (learned representation) — does a RICHER-THAN-LPC learned latent break the cross-speaker wall, and is the gain EARNABLE?

The jabberwock's fail-fast: open a pretrained SSL model (wav2vec2-base, LibriSpeech-960h, SELF-supervised, no labels), one
forward pass for per-frame latents on the EXISTING 400-way cross-speaker rig, run the UNCHANGED trajectory-DTW recogniser
cold. The BRUTAL hook (its Part 3): a frozen net WILL beat the cochleagram by BORROWED invariance (thousands of training
speakers) -- which violates the dynamism constraint (2). So the decisive question is not "latent > cochleagram" but
"does the FACTORISATION step (the part learnable online) beat the RAW-latent baseline". Four conditions, identical rig:
  COLD  = CMVN cochleagram (anchor ~11.5)                          -- the cheap ear
  RAW-L = wav2vec2 latent, best layer (within-speaker probe)       -- BORROWED invariance baseline
  CMVN-L= per-speaker CMVN on the latent (cheap slow-factor remove) -- earnable
  SFA-L = project out the speaker SUBSPACE (fit on TRAIN speakers)  -- the earnable mechanism (the novel step)
PRE-COMMITTED (the agent's): KEEP if best-factorised >= 28.8 (half the 11.5->46.1 gap) AND best-factorised > RAW-L (the
gain is EARNED, not borrowed). KILL if RAW-L <= ~14 (latent no better than the ear) -> wall is the ceiling. DENT/CLOSED if
RAW-L is high but factorisation <= RAW-L -> borrowed from a frozen net, fails constraint (2); ~25-30% is the honest
training-free ceiling, accept it. Two corrected runs max (layer re-pick / CMVN-on-latent), then dead.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.phase0_learned_latent
"""
from __future__ import annotations

import glob
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import torch
import torchaudio
from torchaudio import pipelines as TP

from scripts.jabberwock_reads_oov_from_phones import dtw, FS
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
from domains.filter_settings import cochleagram
from domains.cmvn import apply_cmvn

N_BANK = 220
KMAX = 5
NWAY = 400
N_TEST = 260
PRUNE = 30
FPS = 50
PCA_D = 64
SFA_K = 16
PICK_FILES = 50
DEFAULT_LAYER = 8

_W2V = None


def w2v_all_layers(x, fs):
    global _W2V
    if _W2V is None:
        _W2V = TP.WAV2VEC2_BASE.get_model().eval()
    x = np.asarray(x, dtype=np.float32)
    if fs != 16000:
        x = torchaudio.functional.resample(torch.from_numpy(x), fs, 16000).numpy()
    x = (x - x.mean()) / (x.std() + 1e-6)            # per-utterance z-norm (standard wav2vec2-base practice)
    with torch.inference_mode():
        feats, _ = _W2V.extract_features(torch.from_numpy(x)[None, :])
    return [f[0].numpy().astype(np.float32) for f in feats]   # 12 x [frames,768] @ ~49fps


def _coch(x):
    nf = max(4, int(len(x) / FS * FPS))
    return np.asarray(cochleagram(np.asarray(x, dtype=np.float64), FS, n_frames=nf), dtype=np.float64)


def _l2rows(M):
    M = np.asarray(M, np.float32)
    n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


def cold_feat(M):
    return _l2rows(apply_cmvn(M))


def recog(fr, bank, vocab, PW):
    pv = fr.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
    top = np.argsort(-(PW @ pv))[:PRUNE]
    best, arg = 1e18, None
    for i in top:
        c = vocab[i]
        d = min(dtw(fr, e) for e in bank[c])
        if d < best:
            best, arg = d, c
    return arg


def fit_pca(frames_list, d=PCA_D):
    X = np.concatenate(frames_list, 0).astype(np.float32)
    if X.shape[0] > 30000:
        idx = np.linspace(0, X.shape[0] - 1, 30000).astype(int); X = X[idx]
    mu = X.mean(0)
    U, S, Vt = np.linalg.svd(X - mu, full_matrices=False)
    return mu, Vt[:d].T.astype(np.float32)


def pca_apply(M, mu, V):
    return _l2rows((np.asarray(M, np.float32) - mu) @ V)


def score(bank_words, test_words, feat_of, vset, vocab):
    """Build a bank + prototypes from train words, recognise test tokens. feat_of(word_traj, speaker)->traj (already final-space)."""
    bank = defaultdict(list); cnt = defaultdict(int)
    for (w, sp, tr) in bank_words:
        if w in vset and cnt[w] < KMAX:
            bank[w].append(tr); cnt[w] += 1
    PW = np.stack([np.stack([e.mean(0) for e in bank[w]]).mean(0) for w in vocab])
    PW /= (np.linalg.norm(PW, axis=1, keepdims=True) + 1e-9)
    toks = [(w, tr) for (w, sp, tr) in test_words if w in vset][:N_TEST]
    return 100 * np.mean([recog(tr, bank, vocab, PW) == w for (w, tr) in toks]), len(toks)


def main():
    print("=" * 100)
    print("PHASE 0 (learned latent) — wav2vec2 SSL latent vs cochleagram, RAW vs FACTORISED (earned-not-borrowed test)")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-5:], spks[:-5]

    # ---- LAYER PICK: within-speaker pooled 1-NN over the 12 layers on a small train subset ----
    print(f"  [pick] extracting 12 layers on {PICK_FILES} train files for the within-speaker layer probe...", flush=True)
    pool = defaultdict(list)   # layer -> list of (w, spk, pooled768)
    nf = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if nf >= PICK_FILES:
                break
            x, fs = load_flac(f); x = np.asarray(x, np.float64); nf += 1
            try:
                segs = align_utt(x, fs, t)
            except Exception:
                continue
            Ls = w2v_all_layers(x, fs); fps = len(Ls[0]) / (len(x) / fs)
            for (w, t0, t1) in segs:
                if len(w) < MINW:
                    continue
                a, b = int(t0 * fps), max(int(t0 * fps) + 1, int(t1 * fps))
                for li, M in enumerate(Ls):
                    seg = M[a:b]
                    if seg.shape[0] >= 1:
                        pool[li].append((w, sp, seg.mean(0)))
        if nf >= PICK_FILES:
            break
    layer_acc = {}
    for li in range(12):
        rows = pool[li]
        byw = defaultdict(list)
        for (w, sp, v) in rows:
            byw[w].append((sp, v))
        vv = [w for w, l in byw.items() if len(l) >= 4]
        if len(vv) < 20:
            layer_acc[li] = 0.0; continue
        bankv = {w: np.stack([v for (sp, v) in byw[w][: len(byw[w]) // 2]]).mean(0) for w in vv}
        names = list(bankv); B = _l2rows(np.stack([bankv[w] for w in names]))
        ok = []
        for w in vv:
            for (sp, v) in byw[w][len(byw[w]) // 2:]:
                q = v / (np.linalg.norm(v) + 1e-9)
                ok.append(int(names[int(np.argmax(B @ q))] == w))
        layer_acc[li] = 100 * np.mean(ok) if ok else 0.0
    L = max(layer_acc, key=layer_acc.get)
    print("  [pick] within-speaker pooled acc by layer: " + ", ".join(f"{li}:{layer_acc[li]:.0f}" for li in range(12)))
    print(f"  [pick] chosen layer L = {L} (probe winner; DEFAULT_LAYER={DEFAULT_LAYER})\n", flush=True)
    del pool

    # ---- MAIN: extract layer L for all files, slice words, gather (cochleagram cold + latentL trajectory) ----
    def gather(spk_list, cap):
        out = []; nu = 0
        for sp in spk_list:
            for (f, t) in by_spk[sp]:
                if nu >= cap:
                    break
                x, fs = load_flac(f); x = np.asarray(x, np.float64); nu += 1
                try:
                    segs = align_utt(x, fs, t)
                except Exception:
                    continue
                M = w2v_all_layers(x, fs)[L]; fps = len(M) / (len(x) / fs)
                for (w, t0, t1) in segs:
                    if len(w) < MINW:
                        continue
                    s0, s1 = int(t0 * fs), int(t1 * fs)
                    if s1 - s0 < int(0.05 * fs):
                        continue
                    a, b = int(t0 * fps), max(int(t0 * fps) + 1, int(t1 * fps))
                    lat = M[a:b]
                    if lat.shape[0] < 1:
                        continue
                    out.append((w, sp, cold_feat(_coch(x[s0:s1])), lat.astype(np.float32)))
            if nu >= cap:
                break
        return out

    print("  [main] extracting layer L for bank + test...", flush=True)
    train_words = gather(train_spk, N_BANK)
    test_words = gather(test_spk, 999)
    vocab_counts = defaultdict(int)
    for (w, sp, cf, lat) in train_words:
        vocab_counts[w] += 1
    vocab = [w for w, c in sorted(vocab_counts.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2]
    vset = set(vocab)
    print(f"  [main] {len(vocab)}-way; bank {len(train_words)} words, test {len(test_words)} words\n", flush=True)

    # COLD (cochleagram)
    cold = score([(w, sp, cf) for (w, sp, cf, lat) in train_words],
                 [(w, sp, cf) for (w, sp, cf, lat) in test_words], None, vset, vocab)[0]

    # latent PCA spaces. RAW: fit PCA on raw bank latents.
    bank_lat = [lat for (w, sp, cf, lat) in train_words]
    mu_r, V_r = fit_pca(bank_lat)
    raw_bank = [(w, sp, pca_apply(lat, mu_r, V_r)) for (w, sp, cf, lat) in train_words]
    raw_test = [(w, sp, pca_apply(lat, mu_r, V_r)) for (w, sp, cf, lat) in test_words]
    rawL, ntok = score(raw_bank, raw_test, vset, vset, vocab)

    # CMVN-on-latent: per-speaker mean/std removal in 768-space (oracle grouping, as the LPC phase-0), then PCA.
    spk_stat = {}
    for grp in (train_words, test_words):
        bysp = defaultdict(list)
        for (w, sp, cf, lat) in grp:
            bysp[sp].append(lat)
        for sp, L_ in bysp.items():
            X = np.concatenate(L_, 0); spk_stat[sp] = (X.mean(0), X.std(0) + 1e-5)
    def cmvn_lat(lat, sp):
        mu, sd = spk_stat[sp]; return (lat - mu) / sd
    cm_bank_raw = [(w, sp, cmvn_lat(lat, sp)) for (w, sp, cf, lat) in train_words]
    cm_test_raw = [(w, sp, cmvn_lat(lat, sp)) for (w, sp, cf, lat) in test_words]
    mu_c, V_c = fit_pca([t for (w, sp, t) in cm_bank_raw])
    cm_bank = [(w, sp, pca_apply(t, mu_c, V_c)) for (w, sp, t) in cm_bank_raw]
    cm_test = [(w, sp, pca_apply(t, mu_c, V_c)) for (w, sp, t) in cm_test_raw]
    cmvnL = score(cm_bank, cm_test, vset, vset, vocab)[0]

    # SFA: speaker subspace from TRAIN-speaker means (general, not oracle on test); project out; then PCA.
    sp_means = []
    bysp_tr = defaultdict(list)
    for (w, sp, cf, lat) in train_words:
        bysp_tr[sp].append(lat)
    for sp, L_ in bysp_tr.items():
        sp_means.append(np.concatenate(L_, 0).mean(0))
    SM = np.stack(sp_means); SM = SM - SM.mean(0)
    _, _, Vt = np.linalg.svd(SM, full_matrices=False)
    Vsp = Vt[:SFA_K].T.astype(np.float32)          # [768, k] speaker directions
    def sfa(lat):
        lat = np.asarray(lat, np.float32); return lat - (lat @ Vsp) @ Vsp.T
    sf_bank_raw = [(w, sp, sfa(lat)) for (w, sp, cf, lat) in train_words]
    sf_test_raw = [(w, sp, sfa(lat)) for (w, sp, cf, lat) in test_words]
    mu_s, V_s = fit_pca([t for (w, sp, t) in sf_bank_raw])
    sf_bank = [(w, sp, pca_apply(t, mu_s, V_s)) for (w, sp, t) in sf_bank_raw]
    sf_test = [(w, sp, pca_apply(t, mu_s, V_s)) for (w, sp, t) in sf_test_raw]
    sfaL = score(sf_bank, sf_test, vset, vset, vocab)[0]

    # within-speaker ceiling on the cochleagram (the 46.1 anchor) for the gap bar
    within = []
    for sp, words in list(defaultdict(list, {s: [t for t in train_words if t[1] == s] for s in train_spk}).items())[:6]:
        ww = [(w, cf) for (w, s, cf, lat) in words if w in vset]
        if len(ww) < 16:
            continue
        h = len(ww) // 2; b = defaultdict(list)
        for (w, cf) in ww[:h]:
            b[w].append(cf)
        pw = np.stack([np.stack([e.mean(0) for e in b[w]]).mean(0) for w in b]); pw /= (np.linalg.norm(pw, axis=1, keepdims=True) + 1e-9)
        bv = list(b)
        ok = [int(recog(cf, b, bv, pw) == w) for (w, cf) in ww[h:] if w in b]
        if ok:
            within.append(100 * np.mean(ok))
    within_ceil = float(np.mean(within)) if within else 46.1

    best_fact = max(cmvnL, sfaL)
    halfgap = cold + (within_ceil - cold) / 2
    print("\n" + "=" * 100)
    print(f"  layer L={L}; @{len(vocab)}-way, {ntok} cross-speaker tokens:")
    print(f"    COLD  cochleagram CMVN:              {cold:.1f}%   (anchor)")
    print(f"    RAW-L wav2vec2 latent (borrowed):    {rawL:.1f}%   ({rawL-cold:+.1f} vs cold)")
    print(f"    CMVN-L per-speaker CMVN on latent:   {cmvnL:.1f}%   ({cmvnL-rawL:+.1f} vs RAW-L)")
    print(f"    SFA-L speaker-subspace projected:    {sfaL:.1f}%   ({sfaL-rawL:+.1f} vs RAW-L)")
    print(f"    WITHIN-speaker ceiling:              {within_ceil:.1f}%")
    print(f"    pre-registered KEEP bar (half-gap):  {halfgap:.1f}%")
    print("-" * 100)
    if rawL <= cold + 2.5:
        print(f"  KILL — RAW-L {rawL:.1f} ~= cold {cold:.1f}: even a rich SSL latent is no more speaker-invariant than the cheap")
        print("  ear. The cross-speaker wall IS the training-free ceiling; the learned-representation frontier closes too.")
    elif best_fact >= halfgap and best_fact > rawL + 1.5:
        print(f"  KEEP — the FACTORISATION is EARNED: best-factorised {best_fact:.1f} clears the half-gap bar ({halfgap:.1f}) AND beats")
        print(f"  the borrowed RAW-L {rawL:.1f} (+{best_fact-rawL:.1f}). The slow/fast split adds real speaker-invariance on TOP of the")
        print("  frozen latent -> the online destination is justified. Proceed to the SFA/online learner.")
    else:
        print(f"  DENT / CLOSED — RAW-L {rawL:.1f} beats cold (borrowed invariance from a frozen net) but the EARNABLE step does NOT")
        print(f"  beat it (best-factorised {best_fact:.1f} <= RAW-L+1.5). Per the brutal call: the gain is BORROWED not earned, fails")
        print(f"  the dynamism constraint (2). ~{max(cold,rawL):.0f}% is the honest training-free ceiling — accept it, bank the discipline.")
        print("  Do NOT fund the online-CPC build on a dent.")
    print("=" * 100)


if __name__ == "__main__":
    main()
