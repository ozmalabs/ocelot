"""EARN-NOT-BORROW, stage 1 — the FROZEN distil arm: can a CLUB-SCALE (~2M) net on a CHEAP cochleagram front-end HOLD
wav2vec2's 81%-class cross-speaker invariance? (the efficiency-floor question + pipeline de-risk for the 3-arm rig.)

The jabberwock locked design (C): distil-init a ~3M conv encoder to reproduce wav2vec2 layer-6 features, then 3 arms
(FROZEN / DYNAMIC / SCRATCH). This is the cheapest arm first: distil a small TCN (cochleagram->768, MSE to wav2vec2 L6 on
a small unlabelled init set), FREEZE it, run the UNCHANGED 400-way cross-speaker trajectory-DTW rig. The borrowed init is a
MIDPOINT (admissible per the creator: live warm-start, but here measured frozen as the pure-borrow baseline). PRE-REGISTERED
(jabberwock): FROZEN ~= 73%. Reads: >=60 = club-scale HOLDS the invariance (destination is ~2M not 95M, floor reachable);
~25 = the small cochleagram-input net can't even hold a distilled copy -> the invariance needs the big raw-waveform rig.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.earn_distil_frozen
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
import torch.nn as nn

from scripts.phase0_learned_latent import (
    w2v_all_layers, _coch, _l2rows, recog, fit_pca, pca_apply, dtw,
    KMAX, NWAY, N_TEST, FPS,
)
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

torch.manual_seed(0)
np.random.seed(0)

LAYER = 6
N_DISTIL = 160        # unlabelled init utterances (train speakers)
N_BANK_UTT = 220
EPOCHS = 60
LR = 1.5e-3
PCA_D = 64


def coch_aligned(x, fs, nframes):
    """raw cochleagram (log power) resampled to nframes -> encoder input [nframes,40]."""
    M = np.asarray(cochleagram_log(x, fs), np.float32)
    if M.shape[0] != nframes:
        idx = np.linspace(0, M.shape[0] - 1, nframes)
        M = np.stack([np.interp(idx, np.arange(M.shape[0]), M[:, j]) for j in range(M.shape[1])], 1).astype(np.float32)
    return M


def cochleagram_log(x, fs):
    from domains.filter_settings import cochleagram
    nf = max(4, int(len(x) / fs * FPS))
    M = np.asarray(cochleagram(np.asarray(x, np.float64), fs, n_frames=nf), np.float64)
    return np.log(np.maximum(M, 1e-8))


class TCN(nn.Module):
    """~2M-param causal-agnostic dilated conv encoder: cochleagram(40) -> 768, matching wav2vec2 L6."""
    def __init__(self, din=40, dh=256, dout=768, dils=(1, 2, 4, 8, 16)):
        super().__init__()
        self.inp = nn.Conv1d(din, dh, 5, padding=2)
        self.blocks = nn.ModuleList([nn.Conv1d(dh, dh, 3, padding=d, dilation=d) for d in dils])
        self.norms = nn.ModuleList([nn.GroupNorm(1, dh) for _ in dils])
        self.head = nn.Conv1d(dh, dout, 1)
        self.act = nn.GELU()

    def forward(self, x):                       # x: [B, T, 40]
        h = self.act(self.inp(x.transpose(1, 2)))
        for c, n in zip(self.blocks, self.norms):
            h = h + self.act(n(c(h)))
        return self.head(h).transpose(1, 2)     # [B, T, 768]


def main():
    print("=" * 100)
    print("EARN stage 1 — FROZEN distil arm: can a ~2M cochleagram-input net HOLD wav2vec2's cross-speaker invariance?")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-5:], spks[:-5]

    # ---- distil set: (cochleagram input, wav2vec2-L6 target) per utterance ----
    print(f"  [distil] building {N_DISTIL} (cochleagram -> wav2vec2-L6) pairs...", flush=True)
    Xin, Ytg = [], []
    n = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if n >= N_DISTIL:
                break
            x, fs = load_flac(f); x = np.asarray(x, np.float64); n += 1
            w2 = w2v_all_layers(x, fs)[LAYER]            # [F,768]
            ci = coch_aligned(x, fs, w2.shape[0])        # [F,40]
            Xin.append(ci); Ytg.append(w2.astype(np.float32))
        if n >= N_DISTIL:
            break
    # global standardisation
    Xc = np.concatenate(Xin, 0); xmu, xsd = Xc.mean(0), Xc.std(0) + 1e-5
    Yc = np.concatenate(Ytg, 0); ymu, ysd = Yc.mean(0), Yc.std(0) + 1e-5
    Xin = [((m - xmu) / xsd).astype(np.float32) for m in Xin]
    Ytg = [((m - ymu) / ysd).astype(np.float32) for m in Ytg]

    enc = TCN(din=Xc.shape[1])
    npar = sum(p.numel() for p in enc.parameters())
    print(f"  [distil] encoder params = {npar/1e6:.2f}M; training {EPOCHS} epochs (MSE)...", flush=True)
    opt = torch.optim.Adam(enc.parameters(), lr=LR)
    order = list(range(len(Xin)))
    for ep in range(EPOCHS):
        np.random.shuffle(order); tot = 0.0
        for i in order:
            xi = torch.from_numpy(Xin[i])[None]; yi = torch.from_numpy(Ytg[i])[None]
            opt.zero_grad()
            pred = enc(xi)
            loss = ((pred - yi) ** 2).mean()
            loss.backward(); opt.step(); tot += loss.item()
        if ep % 10 == 0 or ep == EPOCHS - 1:
            print(f"    epoch {ep:2d}  mse {tot/len(order):.4f}", flush=True)
    enc.eval()

    def encode(coch_word):
        ci = (coch_word - xmu) / xsd
        with torch.inference_mode():
            z = enc(torch.from_numpy(ci.astype(np.float32))[None])[0].numpy()
        return z

    # ---- eval: per-word cochleagram -> encoder -> trajectory-DTW (bank train spk, test eval spk) ----
    def gather(spk_list, cap):
        # FAIR eval (matches the wav2vec2 audit): encode the FULL utterance (context) ONCE, then slice word frames.
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
                Mfull = cochleagram_log(x, fs)                 # [F,32] whole utterance
                if Mfull.shape[0] < 2:
                    continue
                zfull = encode(Mfull)                          # [F,768] encoded WITH context
                fps = Mfull.shape[0] / (len(x) / fs)
                for (w, t0, t1) in segs:
                    if len(w) < MINW:
                        continue
                    s0, s1 = int(t0 * fs), int(t1 * fs)
                    if s1 - s0 < int(0.05 * fs):
                        continue
                    a, b = int(t0 * fps), max(int(t0 * fps) + 1, int(t1 * fps))
                    zw = zfull[a:b]
                    if zw.shape[0] < 1:
                        continue
                    out.append((w, sp, zw))
            if nu >= cap:
                break
        return out

    print("  [eval] encoding bank + test words...", flush=True)
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

    # label-shuffle sanity
    rng = np.random.RandomState(1); keys = [w for (w, sp, z) in bank_w]; keys = [keys[i] for i in rng.permutation(len(keys))]
    bs = defaultdict(list); cs = defaultdict(int)
    for (w, sp, z), kw in zip(bank_w, keys):
        if kw in vset and cs[kw] < KMAX:
            bs[kw].append(pca_apply(z, mu_p, V_p)); cs[kw] += 1
    effs = [w for w in vocab if bs[w]]; PWs = np.stack([np.stack([e.mean(0) for e in bs[w]]).mean(0) for w in effs]); PWs /= (np.linalg.norm(PWs, axis=1, keepdims=True) + 1e-9)
    sh = 100 * np.mean([recog(z, bs, effs, PWs) == w for (w, z) in toks if w in set(effs)])

    print("\n" + "=" * 100)
    print(f"  {npar/1e6:.2f}M-param cochleagram-input distilled net, FROZEN, @{len(eff)}-way, {len(toks)} cross-speaker tokens:")
    print(f"    FROZEN distil arm:        {acc:.1f}%   (anchors: cochleagram 11.5 / wav2vec2-raw 81.2 / within 46.1)")
    print(f"    label-shuffle control:    {sh:.1f}%   (chance {100/len(eff):.2f}%)")
    print("-" * 100)
    if acc >= 60:
        print(f"  HOLDS — a ~{npar/1e6:.1f}M net on a CHEAP cochleagram front-end carries {acc:.0f}% of wav2vec2's cross-speaker")
        print("  invariance (distilled). The destination is CLUB-SCALE, not 95M — the efficiency floor is reachable. Pipeline")
        print("  de-risked; proceed to the DYNAMIC vs FROZEN vs SCRATCH 3-arm differential.")
    elif acc >= 35:
        print(f"  PARTIAL — {acc:.0f}% held: a small cochleagram net captures much but not most of the invariance. The front-end")
        print("  (cochleagram vs raw waveform) or the net size is leaving signal on the table; worth one capacity/front-end bump.")
    else:
        print(f"  WEAK — {acc:.0f}%: the small cochleagram-input net can't hold even a distilled copy. The invariance may need the")
        print("  raw-waveform big rig; club-scale holding is unproven. Diagnose front-end vs capacity before the 3-arm build.")
    print("=" * 100)


if __name__ == "__main__":
    main()
