"""EARN distil — RAW-WAVEFORM front-end: can a ~3M net WITH THE SAME INPUT wav2vec2 gets HOLD its cross-speaker invariance?

The cochleagram-input distil arm held only 32% (fair eval) — distil MSE plateaued at 0.55 (~45% var), the cochleagram (32
bands, 50fps) is too lossy to reproduce wav2vec2's raw-waveform features. This swaps the front-end to RAW WAVEFORM (a small
wav2vec2-style strided-conv feature encoder + dilated-conv context), distils to wav2vec2-L6, FROZEN, fair full-utterance eval
on the 400-way cross-speaker rig. Isolates front-end-vs-capacity: if a small raw net holds >=60, the destination is CLUB-SCALE
(the 81%-class invariance lives in ~3M not 95M — efficiency floor reachable, the borrowed midpoint compresses); if it stalls,
the invariance needs scale/the transformer's long context and club-scale holding is the open question.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.earn_distil_raw
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

from scripts.phase0_learned_latent import w2v_all_layers, _l2rows, recog, fit_pca, pca_apply, KMAX, NWAY, N_TEST
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

torch.manual_seed(0); np.random.seed(0)

LAYER = 6
N_DISTIL = 160
N_BANK_UTT = 220
EPOCHS = 50
LR = 1e-3
MAXSEC = 8.0


class RawEnc(nn.Module):
    """~3M wav2vec2-style raw-waveform feature encoder (strided convs, total stride 320 -> 50fps) + dilated context -> 768."""
    def __init__(self, dout=768):
        super().__init__()
        cfgs = [(1, 128, 10, 5), (128, 256, 3, 2), (256, 256, 3, 2), (256, 256, 3, 2),
                (256, 256, 3, 2), (256, 256, 2, 2), (256, 256, 2, 2)]
        self.convs = nn.ModuleList([nn.Conv1d(i, o, k, stride=s) for (i, o, k, s) in cfgs])
        self.cnorms = nn.ModuleList([nn.GroupNorm(1, o) for (_, o, _, _) in cfgs])
        self.tcn = nn.ModuleList([nn.Conv1d(256, 256, 3, padding=d, dilation=d) for d in (1, 2, 4, 8, 16)])
        self.tnorms = nn.ModuleList([nn.GroupNorm(1, 256) for _ in (1, 2, 4, 8, 16)])
        self.head = nn.Conv1d(256, dout, 1)
        self.act = nn.GELU()

    def forward(self, x):                          # x: [B, samples]
        h = x[:, None, :]
        for c, n in zip(self.convs, self.cnorms):
            h = self.act(n(c(h)))
        for c, n in zip(self.tcn, self.tnorms):
            h = h + self.act(n(c(h)))
        return self.head(h).transpose(1, 2)        # [B, T, 768]


def znorm_wav(x):
    x = np.asarray(x, np.float32); return (x - x.mean()) / (x.std() + 1e-6)


def main():
    print("=" * 100)
    print("EARN distil — RAW-WAVEFORM front-end: can a ~3M net with wav2vec2's own input hold the cross-speaker invariance?")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-5:], spks[:-5]

    print(f"  [distil] {N_DISTIL} (raw-waveform -> wav2vec2-L6) pairs...", flush=True)
    Xw, Ytg = [], []
    n = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if n >= N_DISTIL:
                break
            x, fs = load_flac(f); x = np.asarray(x, np.float64)[: int(MAXSEC * 16000)]; n += 1
            w2 = w2v_all_layers(x, fs)[LAYER].astype(np.float32)
            Xw.append(znorm_wav(x)); Ytg.append(w2)
        if n >= N_DISTIL:
            break
    Yc = np.concatenate(Ytg, 0); ymu, ysd = Yc.mean(0), Yc.std(0) + 1e-5
    Ytg = [((m - ymu) / ysd).astype(np.float32) for m in Ytg]

    enc = RawEnc()
    npar = sum(p.numel() for p in enc.parameters())
    print(f"  [distil] params {npar/1e6:.2f}M; training {EPOCHS} epochs (MSE, aligned to wav2vec2 frames)...", flush=True)
    opt = torch.optim.Adam(enc.parameters(), lr=LR)
    order = list(range(len(Xw)))
    for ep in range(EPOCHS):
        np.random.shuffle(order); tot = 0.0
        for i in order:
            xi = torch.from_numpy(Xw[i])[None]
            yi = torch.from_numpy(Ytg[i])[None]
            opt.zero_grad()
            pred = enc(xi)                         # [1,T',768]
            T = min(pred.shape[1], yi.shape[1])
            loss = ((pred[:, :T] - yi[:, :T]) ** 2).mean()
            loss.backward(); opt.step(); tot += loss.item()
        if ep % 10 == 0 or ep == EPOCHS - 1:
            print(f"    epoch {ep:2d}  mse {tot/len(order):.4f}", flush=True)
    enc.eval()

    def encode_full(x):
        with torch.inference_mode():
            return enc(torch.from_numpy(znorm_wav(x))[None])[0].numpy()

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
                    if len(w) < MINW:
                        continue
                    if int(t1 * fs) - int(t0 * fs) < int(0.05 * fs):
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
    print(f"  {npar/1e6:.2f}M-param RAW-WAVEFORM distilled net, FROZEN, @{len(eff)}-way, {len(toks)} cross-speaker tokens:")
    print(f"    RAW-waveform distil arm:  {acc:.1f}%   (anchors: cochleagram-distil 32 / wav2vec2-raw 81.2 / within 46.1)")
    print(f"    label-shuffle control:    {sh:.1f}%   (chance {100/len(eff):.2f}%)")
    print("-" * 100)
    if acc >= 60:
        print(f"  HOLDS — a ~{npar/1e6:.1f}M raw-waveform net carries {acc:.0f}% of wav2vec2's cross-speaker invariance. The destination")
        print("  is CLUB-SCALE (~3M not 95M); the front-end WAS the cochleagram limit. The efficiency floor is reachable.")
    elif acc >= 45:
        print(f"  PARTIAL — {acc:.0f}%: raw input lifts it past the cochleagram (32) toward within-speaker (46) but not to 81. The")
        print("  transformer's long context / SSL scale holds some invariance a small net misses; capacity/context is the next lever.")
    else:
        print(f"  STILL WEAK — {acc:.0f}%: even with raw input a small distilled net doesn't hold it. The invariance leans on scale/")
        print("  long-context the SSL net supplies; club-scale holding via simple distillation is unproven on this rig.")
    print("=" * 100)


if __name__ == "__main__":
    main()
