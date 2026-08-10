"""EARN distil — LOG-MEL-80 front-end (the tractable front-end diagnosis; raw-waveform was CPU-prohibitive).

The 32-band cochleagram net held only 32% (distil MSE 0.55). Raw-waveform input is the fairest test but is CPU-prohibitive
(34 min wall reached only epoch 0). Log-mel-80 is the middle ground: far richer than the 32-band cochleagram (the suspected
bottleneck) yet still a CHEAP front-end, fast to train at B=1. Distil a ~1.3M TCN(80->768) to wav2vec2-L6, FROZEN, fair
full-utterance eval on the 400-way cross-speaker rig. If log-mel-80 distils MUCH better than the cochleagram's 32, the
FRONT-END was the limit (a richer cheap front-end suffices -> floor reachable); if it also stalls ~35, it's capacity / the
SSL net's long-context, not the front-end.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.earn_distil_logmel
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

from scripts.phase0_learned_latent import w2v_all_layers, recog, fit_pca, pca_apply, KMAX, NWAY, N_TEST
from scripts.earn_distil_frozen import TCN, _l2rows
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

torch.manual_seed(0); np.random.seed(0)

LAYER = 6
N_DISTIL = 160
N_BANK_UTT = 220
EPOCHS = 60
LR = 1.5e-3
N_MELS = 80

_MEL = torchaudio.transforms.MelSpectrogram(sample_rate=16000, n_fft=400, hop_length=320, n_mels=N_MELS)


def logmel(x):
    with torch.inference_mode():
        M = _MEL(torch.from_numpy(np.asarray(x, np.float32)))   # [80, T]
    return torch.log(M + 1e-6).t().numpy().astype(np.float32)   # [T, 80]


def main():
    print("=" * 100)
    print("EARN distil — LOG-MEL-80 front-end: does a richer-but-cheap front-end hold wav2vec2's cross-speaker invariance?")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-5:], spks[:-5]

    print(f"  [distil] {N_DISTIL} (log-mel-80 -> wav2vec2-L6) pairs...", flush=True)
    Xin, Ytg = [], []
    n = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if n >= N_DISTIL:
                break
            x, fs = load_flac(f); x = np.asarray(x, np.float64); n += 1
            w2 = w2v_all_layers(x, fs)[LAYER].astype(np.float32)
            lm = logmel(x)
            T = min(lm.shape[0], w2.shape[0])
            Xin.append(lm[:T]); Ytg.append(w2[:T])
        if n >= N_DISTIL:
            break
    Xc = np.concatenate(Xin, 0); xmu, xsd = Xc.mean(0), Xc.std(0) + 1e-5
    Yc = np.concatenate(Ytg, 0); ymu, ysd = Yc.mean(0), Yc.std(0) + 1e-5
    Xin = [((m - xmu) / xsd).astype(np.float32) for m in Xin]
    Ytg = [((m - ymu) / ysd).astype(np.float32) for m in Ytg]

    enc = TCN(din=N_MELS)
    npar = sum(p.numel() for p in enc.parameters())
    print(f"  [distil] params {npar/1e6:.2f}M; training {EPOCHS} epochs...", flush=True)
    opt = torch.optim.Adam(enc.parameters(), lr=LR)
    order = list(range(len(Xin)))
    for ep in range(EPOCHS):
        np.random.shuffle(order); tot = 0.0
        for i in order:
            xi = torch.from_numpy(Xin[i])[None]; yi = torch.from_numpy(Ytg[i])[None]
            opt.zero_grad(); pred = enc(xi)
            loss = ((pred - yi) ** 2).mean()
            loss.backward(); opt.step(); tot += loss.item()
        if ep % 10 == 0 or ep == EPOCHS - 1:
            print(f"    epoch {ep:2d}  mse {tot/len(order):.4f}", flush=True)
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
    print(f"  {npar/1e6:.2f}M-param LOG-MEL-80 distilled net, FROZEN, @{len(eff)}-way, {len(toks)} cross-speaker tokens:")
    print(f"    LOG-MEL-80 distil arm:    {acc:.1f}%   (anchors: 32-band cochleagram-distil 32 / wav2vec2-raw 81.2 / within 46.1)")
    print(f"    label-shuffle control:    {sh:.1f}%   (chance {100/len(eff):.2f}%)")
    print("-" * 100)
    if acc >= 55:
        print(f"  FRONT-END WAS THE LIMIT — log-mel-80 holds {acc:.0f}% (vs 32-band cochleagram's 32). A richer CHEAP front-end")
        print("  suffices; the destination is club-scale. The 32-band cochleagram was throwing away the detail the invariance needs.")
    elif acc >= 40:
        print(f"  PARTLY FRONT-END — {acc:.0f}% (vs 32 cochleagram): richer input helps but doesn't reach 81. Some invariance leans")
        print("  on the SSL net's long context/scale a small net misses; front-end is part, capacity/context the rest.")
    else:
        print(f"  NOT THE FRONT-END — {acc:.0f}% ~= cochleagram 32: a richer cheap front-end doesn't help. The invariance leans on")
        print("  scale / long-context the 95M SSL net supplies, not the input representation. Club-scale holding is the harder build.")
    print("=" * 100)


if __name__ == "__main__":
    main()
