"""universe_recovery_frontend — the ACOUSTIC SENSE SWAP, measured cross-speaker.

THESIS (memory ozma_trained_model_is_partial_universe_recovery). The raw
cochleagram is the CRUDEST universe-recovery: it reads the exterior's surface
spectrum but never recovers SPEAKER-NORMALISATION (Ladefoged-Broadbent; the
absolute-features wall capped cross-speaker LOSO ~0.50). A trained self-supervised
speech model (wav2vec2-class) is a PARTIAL universe-recovery whose MID layers ARE
speaker-normalised (existing probe /tmp/ssl_w2v2.log: cross-speaker same-word
separation +0.088, isolated +0.148, layer ~4-7).

THE DONKEY LINE — PERCEIVE WITH IT, DON'T THINK WITH IT.
  · The SSL model is the SENSE (the read of the exterior's structure). It appears
    in this experiment ONLY as the feature extractor (a fixed forward pass on the
    waveform -> a per-frame feature matrix). NO net is in the recognition decision.
  · The COGNITION is the AGENT'S OWNED OPS: 1-NN over DTW trajectory distance (the
    agent's nearest-exemplar Argmin, the SAME recogniser the world uses), held
    BYTE-IDENTICAL across both senses. No fit, no gradient, no net in the decision.

HEAD-TO-HEAD (isolated-word cross-speaker LOSO, the cleanest test of the SENSE):
  · COCHLEAGRAM-CMVN acoustic — a gammatone/log-mel cochleagram per-frame matrix,
    per-utterance CMVN (the crude spectral front end; the ~0.50 absolute-features
    bar). The OLD sense.
  · SSL-RECOVERY acoustic — wav2vec2-base mid-layer features per frame (the partial
    universe-recovery; speaker-normalised). The NEW sense.
  SAME agent recogniser (1-NN over length-normalised DTW) on BOTH. The ONLY thing
  that changes is the acoustic sense; the cognition is identical.

ROBUST LOSO: a banked exemplar lexicon is built ONLY from TRAIN speakers; the
HELD-OUT speakers' clips are NEVER banked (ungameable cross-speaker). Per held-out
clip: read the SENSE -> 1-NN DTW against the train bank -> argmin word.

PREDICTION: the SSL universe-recovery sense lifts cross-speaker FAR over the
cochleagram (it recovered the speaker-normalisation the cochleagram couldn't) ->
the wall was the SENSE (crude recovery), not the cognition.
KILL: if SSL acoustic does NOT beat the cochleagram cross-speaker, the
partial-universe-recovery claim fails -> say so plainly.

DONKEY AUDIT (printed at run): net touches FEATURE READ ONLY; decision = owned
1-NN DTW; held-out speakers never banked; CortexLoop untouched; LOSO ungameable.

Run: python -m scripts.universe_recovery_frontend [n_train_spk] [n_held_spk] [n_bank_per] [n_test_per] [ssl_layer]
"""
from __future__ import annotations

import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.self_directed_speech_world as W
from scripts.frame_inference_v1 import _dtw  # the agent's owned DTW (Euclidean/frame)

FS = W._TARGET_FS  # 8 kHz, the cochlea front-end rate
SSL_SR = 16000     # wav2vec2 expects 16 kHz


# ===========================================================================
# SENSE 1 — COCHLEAGRAM-CMVN  (the crude spectral front end; the ~0.50 bar).
# A gammatone-spaced (ERB) log filterbank cochleagram per frame, per-utterance
# CMVN. This is the ABSOLUTE-features sense: surface spectrum, NO speaker
# normalisation beyond per-utterance mean/var removal. Owned boundary DSP.
# ===========================================================================

_MEL_FB = {}


def _erb_filterbank(n_bands, sr, n_fft):
    """A gammatone-style ERB-spaced triangular log filterbank (the cochleagram
    band layout). Cached per (n_bands, sr, n_fft)."""
    key = (n_bands, sr, n_fft)
    if key in _MEL_FB:
        return _MEL_FB[key]
    import librosa
    # mel scale approximates the ERB/cochlear place map closely enough for the
    # crude-cochleagram baseline; this is the standard surface spectral sense.
    fb = librosa.filters.mel(sr=sr, n_fft=n_fft, n_mels=n_bands, fmin=50.0,
                             fmax=sr / 2)
    _MEL_FB[key] = fb
    return fb


def cochleagram_cmvn(x, sr=FS, n_bands=32, hop_ms=10.0, win_ms=25.0):
    """Per-frame log cochleagram (gammatone/ERB bands) with per-utterance CMVN.
    Returns (T x n_bands). The crude spectral sense — no speaker recovery."""
    import librosa
    x = np.asarray(x, dtype=np.float32)
    if x.size < int(sr * 0.02):
        return np.zeros((0, n_bands), dtype=np.float32)
    n_fft = 512
    hop = max(1, int(sr * hop_ms / 1000.0))
    win = max(n_fft, int(sr * win_ms / 1000.0))
    n_fft = 1 << (int(win - 1).bit_length())  # power-of-two >= win
    S = np.abs(librosa.stft(x, n_fft=n_fft, hop_length=hop,
                            win_length=win, center=True)) ** 2
    fb = _erb_filterbank(n_bands, sr, n_fft)
    coch = fb @ S                                   # (n_bands x T)
    coch = np.log(coch + 1e-6).T.astype(np.float32)  # (T x n_bands)
    if coch.shape[0] == 0:
        return coch
    # per-utterance CMVN — the absolute-removal move (the ~0.50 bar).
    mu = coch.mean(axis=0, keepdims=True)
    sd = coch.std(axis=0, keepdims=True) + 1e-6
    return (coch - mu) / sd


# ===========================================================================
# SENSE 2 — SSL-RECOVERY  (the partial universe-recovery; speaker-normalised).
# wav2vec2-base mid-layer per-frame features. The net is a FIXED forward pass:
# the SENSE, never the decision. We L2-normalise frames (cosine geometry, the
# standard SSL metric) so the SAME _dtw (Euclidean per frame) measures cosine
# distance up to a monotone transform — the agent's owned trajectory distance.
# ===========================================================================

class SSLSense:
    """Fixed wav2vec2 forward pass -> per-frame mid-layer feature matrix. NET =
    FEATURE READ ONLY. No fit, no gradient, no net in the recognition decision."""

    def __init__(self, layer=7, model_name="facebook/wav2vec2-base"):
        import torch
        from transformers import AutoModel
        torch.set_num_threads(max(1, (os.cpu_count() or 2) // 2))
        self.torch = torch
        self.layer = layer
        self.name = model_name
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
        self.n_layers = self.model.config.num_hidden_layers

    def read(self, x, sr_in=FS):
        """x: waveform at sr_in. Returns (T x D) L2-normed mid-layer features."""
        import numpy as _np
        torch = self.torch
        x = _np.asarray(x, dtype=_np.float32)
        if x.size < 64:
            return _np.zeros((0, self.model.config.hidden_size), dtype=_np.float32)
        # wav2vec2 expects 16 kHz; resample from the 8 kHz cochlea rate (linear,
        # owned boundary DSP — this is part of the SENSE's input conditioning).
        if sr_in != SSL_SR:
            n_out = max(1, int(round(x.size * SSL_SR / sr_in)))
            idx = _np.linspace(0, x.size - 1, n_out)
            x = _np.interp(idx, _np.arange(x.size), x).astype(_np.float32)
        with torch.no_grad():
            w = torch.from_numpy(_np.ascontiguousarray(x))[None, :]
            w = (w - w.mean()) / (w.std() + 1e-7)
            out = self.model(w, output_hidden_states=True)
            h = out.hidden_states[self.layer][0].cpu().numpy().astype(_np.float32)
        # L2-normalise per frame (cosine geometry; _dtw Euclidean over unit
        # vectors == sqrt(2-2cos) monotone in cosine distance).
        n = _np.linalg.norm(h, axis=1, keepdims=True)
        return h / _np.maximum(n, 1e-9)


# ===========================================================================
# THE AGENT'S COGNITION — 1-NN over DTW trajectory distance. IDENTICAL for both
# senses. bank: list of (word, repr). Returns argmin word. NO net here.
# ===========================================================================

def recognise_1nn(test_repr, bank):
    if test_repr.shape[0] == 0 or not bank:
        return None
    best_w, best_d = None, float("inf")
    for w, r in bank:
        d = _dtw(test_repr, r)
        if d < best_d:
            best_d, best_w = d, w
    return best_w


# ===========================================================================
# ROBUST CROSS-SPEAKER LOSO HARNESS — bank from TRAIN speakers only; test on
# HELD-OUT speakers' clips (NEVER banked). Same split feeds both senses so the
# comparison is apples-to-apples (same clips, same recogniser, only the SENSE
# differs).
# ===========================================================================

def build_split(n_train_spk, n_held_spk, n_bank_per, n_test_per, seed=20240611):
    words = W.sc_words()
    rng = random.Random(seed)
    speakers = W.sc_speakers(words)
    rng.shuffle(speakers)
    held_spk = speakers[:n_held_spk]
    train_spk = speakers[n_held_spk:n_held_spk + n_train_spk]

    def carve(spk_list, per):
        """word -> list of (waveform, speaker). Per speaker, up to `per` clips per
        word (cap to keep the bank/test bounded). Mechanical I/O."""
        items = []
        for spk in spk_list:
            idx = W.sc_index_for([spk], words)
            for w in words:
                paths = idx.get(w, [])
                rng.shuffle(paths)
                for p in paths[:per]:
                    x, _fs = W.load_sc_clip(p)
                    if x.size >= int(FS * 0.1):
                        items.append((x, w, spk))
        return items

    bank_items = carve(train_spk, n_bank_per)
    test_items = carve(held_spk, n_test_per)
    return words, train_spk, held_spk, bank_items, test_items


def loso_accuracy(sense_read, bank_items, test_items, max_test=None, seed=0):
    """Extract the SENSE for every bank + test clip ONCE, then 1-NN DTW each test
    clip cross-speaker. Returns (acc, n_evaluated)."""
    t0 = time.time()
    bank = []
    for x, w, _spk in bank_items:
        r = sense_read(x)
        if r.shape[0] >= 2:
            bank.append((w, r))
    t_bank = time.time() - t0

    rng = random.Random(seed + 5)
    tests = list(test_items)
    rng.shuffle(tests)
    if max_test:
        tests = tests[:max_test]

    t0 = time.time()
    hit = tot = 0
    for x, truth, _spk in tests:
        r = sense_read(x)
        if r.shape[0] < 2:
            continue
        g = recognise_1nn(r, bank)
        if g is None:
            continue
        tot += 1
        hit += int(g == truth)
    t_test = time.time() - t0
    acc = hit / tot if tot else 0.0
    return acc, tot, len(bank), t_bank, t_test


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        print("[MARKER] UNIVERSE_RECOVERY_FRONTEND_ABORT", flush=True)
        return

    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    n_bank_per = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    n_test_per = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    ssl_layer = int(sys.argv[5]) if len(sys.argv) > 5 else 7

    random.seed(1)
    np.random.seed(1)

    print("=" * 78, flush=True)
    print("UNIVERSE-RECOVERY FRONT END — acoustic SENSE swap, cross-speaker LOSO",
          flush=True)
    print("=" * 78, flush=True)
    print("DONKEY AUDIT:", flush=True)
    print("  · SSL net = the SENSE (feature READ only; a fixed forward pass on the",
          flush=True)
    print("    waveform). NO net in the recognition DECISION.", flush=True)
    print("  · COGNITION = the agent's OWNED 1-NN over DTW trajectory distance,",
          flush=True)
    print("    BYTE-IDENTICAL across both senses. No fit / gradient / net in the decision.",
          flush=True)
    print("  · LOSO: bank built from TRAIN speakers ONLY; HELD-OUT speakers' clips",
          flush=True)
    print("    NEVER banked (ungameable cross-speaker). CortexLoop untouched.",
          flush=True)
    print("-" * 78, flush=True)

    t0 = time.time()
    (words, train_spk, held_spk, bank_items,
     test_items) = build_split(n_train_spk, n_held_spk, n_bank_per, n_test_per)
    K = len(words)
    chance = 1.0 / K
    print(f"[split] {K} digits {words}", flush=True)
    print(f"[split] {len(train_spk)} TRAIN, {len(held_spk)} HELD-OUT speakers "
          "(disjoint; held clips NEVER banked)", flush=True)
    print(f"[split] bank clips {len(bank_items)} (train), test clips "
          f"{len(test_items)} (held-out)  built in {time.time()-t0:.0f}s", flush=True)
    print(f"[split] chance = {chance:.3f}", flush=True)

    # ---- SENSE 1: cochleagram-CMVN (the crude spectral front end) ----
    print("\n" + "=" * 78, flush=True)
    print("SENSE 1 — COCHLEAGRAM-CMVN (gammatone/ERB log filterbank, per-utt CMVN)",
          flush=True)
    print("  the crude spectral front end — the absolute-features ~0.50 bar",
          flush=True)
    print("=" * 78, flush=True)
    t0 = time.time()
    coch_acc, coch_n, coch_bank, cb_t, ct_t = loso_accuracy(
        lambda x: cochleagram_cmvn(x, sr=FS), bank_items, test_items)
    print(f"  cochleagram-CMVN cross-speaker LOSO acc = {coch_acc:.3f}  "
          f"(n={coch_n}, bank={coch_bank})", flush=True)
    print(f"  [timing] bank {cb_t:.0f}s + test {ct_t:.0f}s = "
          f"{time.time()-t0:.0f}s", flush=True)

    # ---- SENSE 2: SSL-recovery (wav2vec2 mid-layer) ----
    print("\n" + "=" * 78, flush=True)
    print(f"SENSE 2 — SSL-RECOVERY (wav2vec2-base layer {ssl_layer}, speaker-normalised",
          flush=True)
    print("  partial universe-recovery). NET = FEATURE READ ONLY.", flush=True)
    print("=" * 78, flush=True)
    t0 = time.time()
    ssl = SSLSense(layer=ssl_layer)
    print(f"  loaded {ssl.name} ({ssl.n_layers} transformer layers), reading layer "
          f"{ssl_layer}  ({time.time()-t0:.0f}s)", flush=True)
    t0 = time.time()
    ssl_acc, ssl_n, ssl_bank, sb_t, st_t = loso_accuracy(
        lambda x: ssl.read(x, sr_in=FS), bank_items, test_items)
    print(f"  SSL-recovery cross-speaker LOSO acc = {ssl_acc:.3f}  "
          f"(n={ssl_n}, bank={ssl_bank})", flush=True)
    print(f"  [timing] bank {sb_t:.0f}s + test {st_t:.0f}s = "
          f"{time.time()-t0:.0f}s", flush=True)

    # ---- VERDICT ----
    lift = ssl_acc - coch_acc
    print("\n" + "=" * 78, flush=True)
    print("VERDICT — does the universe-recovery SENSE lift cross-speaker over the",
          flush=True)
    print("          crude cochleagram, with the agent's cognition held identical?",
          flush=True)
    print("=" * 78, flush=True)
    print(f"  cochleagram-CMVN  cross-speaker = {coch_acc:.3f}  (n={coch_n})",
          flush=True)
    print(f"  SSL-recovery      cross-speaker = {ssl_acc:.3f}  (n={ssl_n})",
          flush=True)
    print(f"  LIFT (SSL - cochleagram)        = {lift:+.3f}", flush=True)
    print(f"  chance = {chance:.3f}", flush=True)
    print("-" * 78, flush=True)
    BAR = 0.05
    if lift > BAR:
        rel = (ssl_acc - coch_acc) / max(coch_acc, 1e-6) * 100.0
        print(f"  CLAIM HOLDS: the SSL partial-universe-recovery SENSE lifts "
              f"cross-speaker by {lift:+.3f} ({rel:+.0f}% relative) over the crude "
              f"cochleagram, SAME owned recogniser. The WALL was the SENSE (crude "
              f"recovery), not the cognition: a fuller universe-recovery (the "
              f"speaker-normalised mid-layer) recovered the invariance the "
              f"cochleagram could not.", flush=True)
    elif lift > 0:
        print(f"  WEAK: SSL edges the cochleagram by only {lift:+.3f} (< {BAR} bar). "
              f"The sense helps but not decisively here.", flush=True)
    else:
        print(f"  KILL: the SSL universe-recovery sense does NOT beat the cochleagram "
              f"cross-speaker ({lift:+.3f}). The partial-universe-recovery claim FAILS "
              f"on this task — the wall was not (only) the crude sense.", flush=True)
    print("-" * 78, flush=True)
    print("DONKEY BOUNDARY (audit): net touched the FEATURE READ ONLY; the "
          "recognition decision was the agent's owned 1-NN DTW for BOTH senses; "
          "held-out speakers were NEVER banked; LOSO ungameable; CortexLoop "
          "untouched.", flush=True)
    print("\n[MARKER] UNIVERSE_RECOVERY_FRONTEND_COMPLETED", flush=True)


if __name__ == "__main__":
    main()
