"""EARN — the per-speaker AFFINE WARP on the borrowed wav2vec2 latent (the non-trivial earn beyond CMVN).

The jabberwock's ratified pivot: "delta rule learns CMVN" is trivial (a free running mean); the smallest NON-trivial earn
is a learned per-speaker AFFINE WARP — speakers differ by vocal-tract length, which WARPS+ROTATES formant geometry
(multiplicative), and CMVN can only SHIFT (additive). Adapt that warp online, per speaker, from a SELF-SUPERVISED temporal
objective, nothing frozen but the PCA coordinate + wav2vec2 warm-start. This is the numpy/torch RULER first (lock the science
before any graph-native port — the documented practice). If the warp beats CMVN, the agent's own trainer earning it is
justified; if not, the warp adds nothing on this latent and we go back to the Omniglot climb.

  z      = PCA64(wav2vec2-L6)                 (frozen coordinate)
  znorm  = (z - mean_s) / std_s               (per-speaker CMVN = the FLOOR; D=I, UV=0 reproduces this)
  z'     = D_s ⊙ znorm + (znorm Vs) Usᵀ       (D diag = VTL rescale; rank-2 UV = rotation; init D=1, U=V=0 => z'=CMVN)
  loss   = InfoNCE(next-frame | shared AR pred A z'_t vs in-stream negatives)   (self-supervised, no labels)
  eval   = 400-way cross-speaker trajectory-DTW on z'

PRE-COMMITTED BAR (the jabberwock's): CMVN-only floor ~= 97. EARNED = AFFINE >= 98.0 AND >= +1.0 over the CMVN-only ablation,
mean over 3 seeds, shuffle at chance. 96-97 = reproduced CMVN (no value). < 96 = the warp HURT (content damaged).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.earn_affine_warp
"""
from __future__ import annotations

import os
import pickle
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import torch
import torch.nn.functional as F

from scripts.phase0_learned_latent import recog, dtw, KMAX, NWAY, N_TEST

CACHE = "/tmp/p0lat_cache_L6.pkl"
PCA_D = 64
RANK = 2
EPOCHS = 40
LR = 0.05
TEMP = 0.1
SEEDS = (0, 1, 2)


def _l2(M):
    M = np.asarray(M, np.float32); n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


def pca_basis(frames, d=PCA_D):
    X = np.concatenate(frames, 0).astype(np.float32)
    if X.shape[0] > 40000:
        X = X[np.linspace(0, X.shape[0] - 1, 40000).astype(int)]
    mu = X.mean(0)
    _, _, Vt = np.linalg.svd(X - mu, full_matrices=False)
    return mu, Vt[:d].T.astype(np.float32)


def run_rig(bank_words, test_words, vocab):
    """bank_words/test_words: list of (w, sp, traj64). trajectory-DTW 400-way."""
    bank = defaultdict(list); cnt = defaultdict(int)
    for (w, sp, tr) in bank_words:
        if w in vocab and cnt[w] < KMAX:
            bank[w].append(_l2(tr)); cnt[w] += 1
    eff = [w for w in vocab if bank[w]]; effset = set(eff)
    PW = np.stack([np.stack([e.mean(0) for e in bank[w]]).mean(0) for w in eff]); PW /= (np.linalg.norm(PW, axis=1, keepdims=True) + 1e-9)
    toks = [(w, _l2(tr)) for (w, sp, tr) in test_words if w in effset][:N_TEST]
    return 100 * np.mean([recog(tr, bank, eff, PW) == w for (w, tr) in toks]), len(toks), eff


def main():
    print("=" * 100)
    print("EARN — per-speaker AFFINE WARP vs CMVN-only on the wav2vec2 latent (the non-trivial earn; ruler first)")
    print("=" * 100)
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train, test = data["train"], data["test"]               # (w, sp, uid, cold_feat, lat768)

    # frozen PCA coordinate on bank latents
    mu_p, Vp = pca_basis([lat for (w, sp, uid, cf, lat) in train])
    def proj(lat):
        return ((np.asarray(lat, np.float32) - mu_p) @ Vp).astype(np.float32)

    # per-speaker CMVN stats (mean/std in PCA space, from the speaker's own frames)
    allw = [(w, sp, proj(lat)) for (w, sp, uid, cf, lat) in train] + \
           [(w, sp, proj(lat)) for (w, sp, uid, cf, lat) in test]
    bysp_frames = defaultdict(list)
    for (w, sp, z) in allw:
        bysp_frames[sp].append(z)
    cmvn = {}
    for sp, zs in bysp_frames.items():
        X = np.concatenate(zs, 0); cmvn[sp] = (X.mean(0), X.std(0) + 1e-5)
    def znorm(z, sp):
        mu, sd = cmvn[sp]; return (z - mu) / sd

    vc = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        vc[w] += 1
    vocab = set(w for w, c in sorted(vc.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2)

    train_z = [(w, sp, znorm(proj(lat), sp)) for (w, sp, uid, cf, lat) in train]
    test_z = [(w, sp, znorm(proj(lat), sp)) for (w, sp, uid, cf, lat) in test]

    # ---- CMVN-only floor (deterministic) ----
    cmvn_acc, ntok, eff = run_rig(train_z, test_z, vocab)
    print(f"\n  CMVN-only floor (D=I, UV=0):   {cmvn_acc:.1f}%   ({ntok} tokens, {len(eff)}-way)")

    # shuffle control on CMVN-only
    rng = np.random.RandomState(7); keys = [w for (w, sp, z) in train_z]; keys = [keys[i] for i in rng.permutation(len(keys))]
    sh_bank = [(kw, sp, z) for (w, sp, z), kw in zip(train_z, keys)]
    sh_acc, _, _ = run_rig(sh_bank, test_z, vocab)
    print(f"  label-shuffle control:         {sh_acc:.1f}%   (chance {100/len(eff):.2f}%)")

    speakers = sorted(bysp_frames)
    sp_streams = {sp: torch.from_numpy(np.concatenate([znorm(z, sp) for (w, s2, z) in allw if s2 == sp], 0)) for sp in speakers}

    affine_runs = []
    for seed in SEEDS:
        torch.manual_seed(seed); np.random.seed(seed)
        A = torch.eye(PCA_D, requires_grad=True)
        D = {sp: torch.ones(PCA_D, requires_grad=True) for sp in speakers}
        U = {sp: (0.01 * torch.randn(PCA_D, RANK)).requires_grad_(True) for sp in speakers}
        V = {sp: (0.01 * torch.randn(PCA_D, RANK)).requires_grad_(True) for sp in speakers}
        params = [A] + [D[s] for s in speakers] + [U[s] for s in speakers] + [V[s] for s in speakers]
        opt = torch.optim.Adam(params, lr=LR)

        def warp(zt, sp):
            return D[sp] * zt + (zt @ V[sp]) @ U[sp].t()

        for ep in range(EPOCHS):
            tot = 0.0
            for sp in speakers:
                Z = sp_streams[sp]
                if Z.shape[0] < 6:
                    continue
                zp = warp(Z, sp)                            # [T,64]
                zn = F.normalize(zp, dim=1)
                pred = F.normalize(zp[:-1] @ A.t(), dim=1)  # predict next
                logits = (pred @ zn.t()) / TEMP             # [T-1, T]
                tgt = torch.arange(1, Z.shape[0])
                loss = F.cross_entropy(logits, tgt)
                opt.zero_grad(); loss.backward(); opt.step(); tot += loss.item()
            if ep % 10 == 0 or ep == EPOCHS - 1:
                print(f"    [seed {seed}] epoch {ep:2d}  infoNCE {tot/len(speakers):.3f}", flush=True)

        with torch.inference_mode():
            def warped_words(words):
                out = []
                for (w, sp, z) in words:
                    zt = torch.from_numpy(z.astype(np.float32))
                    out.append((w, sp, (D[sp] * zt + (zt @ V[sp]) @ U[sp].t()).numpy()))
                return out
            bk = warped_words(train_z); ts = warped_words(test_z)
        acc, _, _ = run_rig(bk, ts, vocab)
        affine_runs.append(acc)
        print(f"  AFFINE warp [seed {seed}]:        {acc:.1f}%   ({acc-cmvn_acc:+.1f} vs CMVN-only)")

    aff = float(np.mean(affine_runs)); margin = aff - cmvn_acc
    print("\n" + "=" * 100)
    print(f"  CMVN-only floor:        {cmvn_acc:.1f}%")
    print(f"  AFFINE warp (mean/3):   {aff:.1f}%   ({margin:+.1f} over CMVN-only;  seeds {[round(a,1) for a in affine_runs]})")
    print(f"  shuffle:                {sh_acc:.1f}%   (chance {100/len(eff):.2f}%)")
    print("-" * 100)
    if aff >= 98.0 and margin >= 1.0:
        print(f"  EARNED — the per-speaker affine WARP beats CMVN by {margin:+.1f} (>=+1.0) at {aff:.1f}% (>=98.0). The agent's own")
        print("  trainer earns a real lift on the borrowed midpoint that a running mean PROVABLY can't (the VTL warp/rotation).")
        print("  Justifies the graph-native port (the trainer as faculty). Then back to the Omniglot climb.")
    elif aff >= cmvn_acc - 1.0:
        print(f"  REPRODUCED-CMVN — affine {aff:.1f} ~= CMVN {cmvn_acc:.1f} ({margin:+.1f}, under the +1.0 bar). The warp earns nothing")
        print("  beyond the free running mean on THIS latent (wav2vec2 already speaker-robust; little linear warp left to remove).")
        print("  Honest: the trainer adds no value here — don't port, go back to Omniglot (the trainer's real climb).")
    else:
        print(f"  WARP HURT — affine {aff:.1f} < CMVN {cmvn_acc:.1f}: the learned warp damaged content (the self-sup target pulled")
        print("  away from word identity). The warp is the wrong earn on this latent. Back to Omniglot.")
    print("=" * 100)


if __name__ == "__main__":
    main()
