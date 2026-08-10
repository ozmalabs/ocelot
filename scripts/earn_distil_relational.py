"""EARN distil — RELATIONAL (geometry) distillation: rule out the weak-MSE confound before concluding "needs scale".

MSE distil of raw 768-d wav2vec2 features into a ~1.3M net plateaued ~0.53 and held only 32-37% cross-speaker regardless of
front-end. But MSE spends capacity matching high-variance dims that may not be discriminative. The recogniser is trajectory-
DTW on COSINE GEOMETRY -- so distil the GEOMETRY: match the student's within-utterance pairwise cosine-similarity matrix to
the teacher's (relational/RKD distillation), the structure the DTW actually uses. If a 1.3M net with relational distil JUMPS
to >=55, it was the OBJECTIVE not the scale (cheap holds it); if it still stalls ~37, "needs depth/context/scale" is robust
across objectives -- a solid landing. Best cheap front-end so far (log-mel-80) + relational loss; fair full-utterance eval.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.earn_distil_relational
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
import torch.nn.functional as F

from scripts.phase0_learned_latent import w2v_all_layers, recog, fit_pca, pca_apply, KMAX, NWAY, N_TEST
from scripts.earn_distil_frozen import TCN
from scripts.earn_distil_logmel import logmel, N_MELS
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

torch.manual_seed(0); np.random.seed(0)

LAYER = 6
N_DISTIL = 160
N_BANK_UTT = 220
EPOCHS = 60
LR = 1.5e-3
MSE_W = 0.1            # small anchor term alongside the relational (geometry) loss


def main():
    print("=" * 100)
    print("EARN distil — RELATIONAL (cosine-geometry) distillation on log-mel-80: objective vs scale")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-5:], spks[:-5]

    print(f"  [distil] {N_DISTIL} (log-mel-80, wav2vec2-L6) pairs...", flush=True)
    Xin, Ytg = [], []
    n = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if n >= N_DISTIL:
                break
            x, fs = load_flac(f); x = np.asarray(x, np.float64); n += 1
            w2 = w2v_all_layers(x, fs)[LAYER].astype(np.float32)
            lm = logmel(x); T = min(lm.shape[0], w2.shape[0])
            Xin.append(lm[:T]); Ytg.append(w2[:T])
        if n >= N_DISTIL:
            break
    Xc = np.concatenate(Xin, 0); xmu, xsd = Xc.mean(0), Xc.std(0) + 1e-5
    Yc = np.concatenate(Ytg, 0); ymu, ysd = Yc.mean(0), Yc.std(0) + 1e-5
    Xin = [((m - xmu) / xsd).astype(np.float32) for m in Xin]
    Ytg = [((m - ymu) / ysd).astype(np.float32) for m in Ytg]

    enc = TCN(din=N_MELS)
    npar = sum(p.numel() for p in enc.parameters())
    print(f"  [distil] params {npar/1e6:.2f}M; training {EPOCHS} epochs (relational + {MSE_W} MSE)...", flush=True)
    opt = torch.optim.Adam(enc.parameters(), lr=LR)
    order = list(range(len(Xin)))
    for ep in range(EPOCHS):
        np.random.shuffle(order); tot = 0.0
        for i in order:
            xi = torch.from_numpy(Xin[i])[None]; yi = torch.from_numpy(Ytg[i])[None]
            T = yi.shape[1]
            if T > 400:                                   # subsample frames to cap the Gram cost
                idx = torch.from_numpy(np.linspace(0, T - 1, 400).astype(np.int64)); yi = yi[:, idx]
            opt.zero_grad()
            pred = enc(xi)
            if T > 400:
                pred = pred[:, idx]
            ps = F.normalize(pred[0], dim=1); ts = F.normalize(yi[0], dim=1)
            Gp = ps @ ps.t(); Gt = ts @ ts.t()            # cosine-similarity geometry (what DTW uses)
            rel = ((Gp - Gt) ** 2).mean()
            mse = ((pred - yi) ** 2).mean()
            loss = rel + MSE_W * mse
            loss.backward(); opt.step(); tot += loss.item()
        if ep % 10 == 0 or ep == EPOCHS - 1:
            print(f"    epoch {ep:2d}  loss {tot/len(order):.4f}", flush=True)
    enc.eval()

    def encode_full(x):
        lm = (logmel(x) - xmu) / xsd
        with torch.inference_mode():
            return enc(torch.from_numpy(lm.astype(np.float32))[None])[0].numpy()

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
                z = encode_full(x); fps = z.shape[0] / (len(x) / fs)
                for (w, t0, t1) in segs:
                    if len(w) < MINW or int(t1 * fs) - int(t0 * fs) < int(0.05 * fs):
                        continue
                    a, b = int(t0 * fps), max(int(t0 * fps) + 1, int(t1 * fps))
                    zw = z[a:b]
                    if zw.shape[0] >= 1:
                        out.append((w, sp, zw))
            if nu >= cap:
                break
        return out

    print("  [eval] encoding bank + test (full-utterance context)...", flush=True)
    bank_w = gather(train_spk, N_BANK_UTT)
    test_w = gather(test_spk, 999)
    vc = defaultdict(int)
    for (w, sp, z) in bank_w:
        vc[w] += 1
    vocab = [w for w, c in sorted(vc.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2]
    vset = set(vocab)
    mu_p, V_p = fit_pca([z for (w, sp, z) in bank_w])
    bank = defaultdict(list); cnt = defaultdict(int)
    for (w, sp, z) in bank_w:
        if w in vset and cnt[w] < KMAX:
            bank[w].append(pca_apply(z, mu_p, V_p)); cnt[w] += 1
    eff = [w for w in vocab if bank[w]]; effset = set(eff)
    PW = np.stack([np.stack([e.mean(0) for e in bank[w]]).mean(0) for w in eff]); PW /= (np.linalg.norm(PW, axis=1, keepdims=True) + 1e-9)
    toks = [(w, pca_apply(z, mu_p, V_p)) for (w, sp, z) in test_w if w in effset][:N_TEST]
    acc = 100 * np.mean([recog(z, bank, eff, PW) == w for (w, z) in toks])

    rng = np.random.RandomState(1); keys = [w for (w, sp, z) in bank_w]; keys = [keys[i] for i in rng.permutation(len(keys))]
    bs = defaultdict(list); cs = defaultdict(int)
    for (w, sp, z), kw in zip(bank_w, keys):
        if kw in vset and cs[kw] < KMAX:
            bs[kw].append(pca_apply(z, mu_p, V_p)); cs[kw] += 1
    effs = [w for w in vocab if bs[w]]; PWs = np.stack([np.stack([e.mean(0) for e in bs[w]]).mean(0) for w in effs]); PWs /= (np.linalg.norm(PWs, axis=1, keepdims=True) + 1e-9)
    sh = 100 * np.mean([recog(z, bs, effs, PWs) == w for (w, z) in toks if w in set(effs)])

    print("\n" + "=" * 100)
    print(f"  {npar/1e6:.2f}M-param log-mel-80 RELATIONAL-distilled net, FROZEN, @{len(eff)}-way, {len(toks)} cross-speaker tokens:")
    print(f"    RELATIONAL distil arm:    {acc:.1f}%   (anchors: MSE-distil mel 37 / cochleagram 32 / wav2vec2-raw 81.2 / within 46.1)")
    print(f"    label-shuffle control:    {sh:.1f}%   (chance {100/len(eff):.2f}%)")
    print("-" * 100)
    if acc >= 55:
        print(f"  IT WAS THE OBJECTIVE — relational distil holds {acc:.0f}% (vs MSE's 37). The geometry transfers into a 1.3M net;")
        print("  cheap DOES hold a large fraction of the invariance. The floor is club-scale with the right (geometry) objective.")
    elif acc >= 44:
        print(f"  PARTLY — {acc:.0f}% (vs MSE 37, within 46): the geometry objective helps and reaches ~within-speaker, but not 81.")
        print("  Objective matters AND scale matters; a bigger net with this objective is the lever to pin the floor.")
    else:
        print(f"  NOT THE OBJECTIVE — {acc:.0f}% ~= MSE 37: a better (geometry) objective doesn't rescue a 1.3M net. 'Needs depth/")
        print("  context/scale' is ROBUST across objectives. The invariance is genuinely not toy-cheap on this rig. Honest landing.")
    print("=" * 100)


if __name__ == "__main__":
    main()
