"""mine_whisper.py — reverse-engineer Whisper's representation to extract
a FORWARD-DESIGNABLE insight for the substrate speech agent.

NOT a port. We probe Whisper's front-end + encoder to answer:
  1. What front-end design choices does the agent's gammatone+patch
     trajectory lack that Whisper makes (log-mel, dynamic-range floor,
     fixed affine norm, time resolution)?
  2. Does the SAME word cluster ACROSS speakers in Whisper, and at
     which DEPTH does invariance emerge (front-end vs deep encoder)?
  3. How does the agent's own unit representation score on the same
     invariance metric?

Metric: speaker-invariance of a word representation = how well same-word
clusters separate across speakers. We use two numbers per representation:
  - silhouette score with WORD as the label (higher = words separate
    regardless of speaker),
  - 1-NN word-classification accuracy under LEAVE-ONE-SPEAKER-OUT
    (train on 5 speakers, test on the held-out one) — the honest test
    of speaker-invariance.

Data: FSDD digits in /tmp/fsdd/recordings, speakers george/jackson/
lucas/nicolas/theo/yweweler. We sample a balanced subset.
"""
from __future__ import annotations

import os
import re
import wave
import math
import numpy as np

DATA_DIR = "/tmp/fsdd/recordings"
_FN = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")

# ---- data ----------------------------------------------------------

def load_wav(path):
    with wave.open(path, "rb") as w:
        fs = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return x, fs


def gather(n_per_class_per_speaker=3, digits=range(10)):
    """Balanced subset: n recordings per (digit, speaker)."""
    items = []  # (path, digit, speaker)
    buckets = {}
    for fn in sorted(os.listdir(DATA_DIR)):
        m = _FN.match(fn)
        if not m:
            continue
        d, spk, idx = int(m.group(1)), m.group(2), int(m.group(3))
        if d not in digits:
            continue
        key = (d, spk)
        buckets.setdefault(key, [])
        if len(buckets[key]) < n_per_class_per_speaker:
            buckets[key].append(os.path.join(DATA_DIR, fn))
    for (d, spk), paths in buckets.items():
        for p in paths:
            items.append((p, d, spk))
    return items


# ---- agent front-end (faithful numpy reproduction) -----------------
# Mirrors runners/dsl/src/auditory_cortex.rs + pipeline_runtime.rs:
#   gammatone_band -> hair_cell_envelope -> evaluate_patch (freq-weighted
#   sum across bands + duration-matched LPF) -> extract_trajectory
#   (resample to 32 frames) -> unit L2 normalise.  LINEAR magnitude,
#   no log compression, no per-feature standardisation.

import math as _math
_LOG_LO, _LOG_HI = _math.log(80.0), _math.log(7500.0)
BANDS = [_math.exp(_LOG_LO + (_LOG_HI - _LOG_LO) * i / 31.0) for i in range(32)]

# 25-patch library centres+sigmas (auditory_cortex.py _DEFAULT_PATCHES),
# sorted by name as lexical_access does.
_PATCHES = [
    ("p0400_b", 400, 500), ("p0400_f", 400, 300), ("p0400_m", 400, 300),
    ("p0400_n", 400, 150), ("p0400_u", 400, 200),
    ("p0800_b", 800, 700), ("p0800_d", 800, 300), ("p0800_m", 800, 400),
    ("p0800_n", 800, 200), ("p0800_u", 800, 300),
    ("p1500_b", 1500, 900), ("p1500_d", 1500, 400), ("p1500_m", 1500, 500),
    ("p1500_n", 1500, 300), ("p1500_u", 1500, 400),
    ("p3000_b", 3000, 1500), ("p3000_f", 3000, 1200), ("p3000_m", 3000, 900),
    ("p3000_n", 3000, 500), ("p3000_u", 3000, 700),
    ("p5500_b", 5500, 2500), ("p5500_f", 5500, 2000), ("p5500_m", 5500, 1500),
    ("p5500_n", 5500, 800), ("p5500_u", 5500, 1200),
]
_PATCHES.sort(key=lambda t: t[0])


def gammatone_env(x, fs, fc, env_cut=50.0):
    # FIR gammatone (order 4) impulse, energy-normalised, then
    # half-wave rectify + one-pole LPF envelope (hair_cell_envelope).
    dur = 0.025
    L = int(dur * fs)
    t = np.arange(L) / fs
    b = 2.0 * math.pi * 1.019 * (24.7 + 0.108 * fc)
    g = t ** 3 * np.exp(-b * t) * np.cos(2 * math.pi * fc * t)
    e = np.sqrt(np.sum(g * g))
    if e > 0:
        g = g / e
    y = np.convolve(x, g, mode="same")
    y = np.maximum(y, 0.0)  # half-wave rectify
    # one-pole LPF
    tau = 1.0 / (2 * math.pi * env_cut)
    a = math.exp(-1.0 / (tau * fs))
    out = np.empty_like(y)
    acc = 0.0
    for i in range(len(y)):
        acc = a * acc + (1 - a) * y[i]
        out[i] = acc
    return out


def agent_trajectory(x, fs, n_frames=32):
    envs = [gammatone_env(x, fs, fc) for fc in BANDS]
    bc = np.array(BANDS)
    patch_bufs = []
    for name, c, sigma in _PATCHES:
        w = np.exp(-0.5 * ((bc - c) / sigma) ** 2)
        w = w / (w.sum() + 1e-9)
        combined = np.zeros_like(envs[0])
        for bi, env in enumerate(envs):
            combined += w[bi] * env
        # duration LPF (use ~80ms sustained default cutoff)
        cut = 1000.0 / (2 * math.pi * 80.0)
        tau = 1.0 / (2 * math.pi * cut)
        a = math.exp(-1.0 / (tau * fs))
        sm = np.empty_like(combined)
        acc = 0.0
        for i in range(len(combined)):
            acc = a * acc + (1 - a) * combined[i]
            sm[i] = acc
        patch_bufs.append(sm)
    # resample each patch buffer to n_frames, row-major [frame][patch]
    n_src = len(patch_bufs[0])
    flat = []
    for tf in range(n_frames):
        sp = tf * n_src / n_frames
        i0 = int(sp); i1 = min(i0 + 1, n_src - 1)
        frac = sp - i0
        for buf in patch_bufs:
            flat.append(buf[i0] * (1 - frac) + buf[i1] * frac)
    v = np.array(flat, dtype=np.float32)
    nrm = np.linalg.norm(v)
    if nrm > 1e-9:
        v = v / nrm
    return v


# ---- Whisper front-end + encoder ----------------------------------

def whisper_logmel(x, fs, fe):
    import librosa  # noqa
    if fs != 16000:
        x = _resample(x, fs, 16000)
    feat = fe(x, sampling_rate=16000, return_tensors="np")
    # (1, 80, 3000) padded to 30s; trim to the voiced region by energy.
    mel = feat["input_features"][0]  # 80 x 3000
    return mel


def _resample(x, fs, target):
    n = int(round(len(x) * target / fs))
    if n <= 1:
        return x
    xp = np.linspace(0, 1, len(x))
    fp = np.linspace(0, 1, n)
    return np.interp(fp, xp, x).astype(np.float32)


def trim_active(mel, keep=64):
    """Pick the `keep` most energetic mel frames (Whisper pads to 3000
    frames of silence). Returns a fixed-length pooled vector: mean over
    the active frames. Mean-pooling = a coarse word-level summary,
    matching how we summarise the agent trajectory."""
    energy = mel.mean(axis=0)  # per-frame
    order = np.argsort(energy)[::-1][:keep]
    active = mel[:, np.sort(order)]
    return active.mean(axis=1)  # 80-vec


# ---- metrics -------------------------------------------------------

def silhouette_by_word(X, words):
    """Cosine silhouette using WORD as cluster label."""
    X = np.asarray(X)
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    D = 1.0 - Xn @ Xn.T
    words = np.asarray(words)
    sil = []
    for i in range(len(X)):
        same = (words == words[i])
        same[i] = False
        if same.sum() == 0:
            continue
        a = D[i, same].mean()
        bs = []
        for w in set(words):
            if w == words[i]:
                continue
            mask = words == w
            if mask.sum():
                bs.append(D[i, mask].mean())
        if not bs:
            continue
        b = min(bs)
        sil.append((b - a) / max(a, b, 1e-9))
    return float(np.mean(sil)) if sil else 0.0


def loso_1nn(X, words, speakers):
    """Leave-one-speaker-out 1-NN word accuracy (cosine). The honest
    speaker-invariance test."""
    X = np.asarray(X)
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    words = np.asarray(words); speakers = np.asarray(speakers)
    correct = total = 0
    for held in set(speakers):
        te = speakers == held
        tr = ~te
        if tr.sum() == 0 or te.sum() == 0:
            continue
        sim = Xn[te] @ Xn[tr].T  # (n_te, n_tr)
        nn = sim.argmax(axis=1)
        pred = words[tr][nn]
        correct += int((pred == words[te]).sum())
        total += int(te.sum())
    return correct / max(total, 1)


# ---- main ----------------------------------------------------------

def main():
    items = gather(n_per_class_per_speaker=3)
    print(f"{len(items)} recordings, "
          f"{len(set(s for _,_,s in items))} speakers, "
          f"{len(set(d for _,d,_ in items))} digits")

    # Load audio once.
    audio = []
    for p, d, spk in items:
        x, fs = load_wav(p)
        audio.append((x, fs, str(d), spk))

    words = [a[2] for a in audio]
    speakers = [a[3] for a in audio]

    # --- agent units ---
    print("\nComputing agent gammatone+patch trajectories...")
    agent_X = [agent_trajectory(x, fs) for x, fs, _, _ in audio]
    agent_sil = silhouette_by_word(agent_X, words)
    agent_loso = loso_1nn(agent_X, words, speakers)
    print(f"  AGENT trajectory (32x25, linear-mag, L2):  "
          f"sil={agent_sil:+.3f}  LOSO-1NN={agent_loso:.3f}")

    # --- Whisper front-end (log-mel, mean-pooled active frames) ---
    print("\nLoading Whisper-tiny...")
    import torch
    from transformers import WhisperFeatureExtractor, WhisperModel
    fe = WhisperFeatureExtractor.from_pretrained("openai/whisper-tiny")
    model = WhisperModel.from_pretrained("openai/whisper-tiny")
    model.eval()

    mels = [whisper_logmel(x, fs, fe) for x, fs, _, _ in audio]
    fe_X = [trim_active(m) for m in mels]
    fe_sil = silhouette_by_word(fe_X, words)
    fe_loso = loso_1nn(fe_X, words, speakers)
    print(f"  WHISPER log-mel front-end (80, pooled):    "
          f"sil={fe_sil:+.3f}  LOSO-1NN={fe_loso:.3f}")

    # --- Whisper encoder per-layer hidden states ---
    print("\nProbing Whisper encoder hidden states per layer...")
    n_layers = model.config.encoder_layers
    layer_states = {l: [] for l in range(n_layers + 1)}  # 0 = embeddings
    with torch.no_grad():
        for m in mels:
            inp = torch.tensor(m[None, :, :], dtype=torch.float32)
            out = model.encoder(inp, output_hidden_states=True)
            hs = out.hidden_states  # tuple (n_layers+1) x (1, T, d)
            # Active-frame pooling at the encoder's time res (conv
            # downsamples by 2 -> 1500 frames). Use energy of the
            # log-mel resampled to T to pick active frames.
            for l, h in enumerate(hs):
                hh = h[0].numpy()  # T x d
                T = hh.shape[0]
                # energy proxy: mel frame energy resampled to T
                en = m.mean(axis=0)
                idx = np.linspace(0, len(en) - 1, T).astype(int)
                ent = en[idx]
                topk = np.argsort(ent)[::-1][:max(8, T // 20)]
                pooled = hh[np.sort(topk)].mean(axis=0)
                layer_states[l].append(pooled)

    print(f"\n  layer | silhouette(word) | LOSO-1NN word-acc")
    print(f"  ------|------------------|------------------")
    for l in range(n_layers + 1):
        Xl = layer_states[l]
        sl = silhouette_by_word(Xl, words)
        ll = loso_1nn(Xl, words, speakers)
        tag = "embeds(conv front-end)" if l == 0 else f"enc layer {l}"
        print(f"  {l:5d} | {sl:+.3f}           | {ll:.3f}   {tag}")

    print("\n  --- SUMMARY ---")
    print(f"  agent units:            sil={agent_sil:+.3f} LOSO={agent_loso:.3f}")
    print(f"  whisper log-mel pooled: sil={fe_sil:+.3f} LOSO={fe_loso:.3f}")
    print(f"  whisper conv embeds:    sil={silhouette_by_word(layer_states[0],words):+.3f} "
          f"LOSO={loso_1nn(layer_states[0],words,speakers):.3f}")
    print(f"  whisper final enc:      sil={silhouette_by_word(layer_states[n_layers],words):+.3f} "
          f"LOSO={loso_1nn(layer_states[n_layers],words,speakers):.3f}")


if __name__ == "__main__":
    main()
