"""THE BABBLING LOOP — learn the phone INVERSION from self-produced audio, PERCEIVE real speech.

The agent learns speech by PRODUCING it: a strong realistic synth (XTTS, many voices) produces
clean audio for KNOWN words -> the phone labels are FREE+EXACT (the agent chose the words; the CMU
pronunciation is the per-word phone target). The agent earns its OWN from-scratch phone recogniser
(the validated lineage: cochleagram frames -> ctxd context+delta+energy feature -> PCA->LDA encoder +
per-phone centroids, with EM/Viterbi forced-alignment to the KNOWN phone sequence). Then it INVERTS
that forward model to PERCEIVE *real* external speech (LibriSpeech dev-clean) with 0 synth calls.

EARN-NOT-BORROW: the recogniser is the agent's own held structure; XTTS/piper only generated the
training audio (a bone-conduction scaffold). donkey=0 AT INFERENCE: this script imports no TTS/torch;
recognition is cochleagram (substrate_rs) + numpy. The synth audio is read off disk as plain wavs.

Conditions (all evaluated on the SAME real dev-clean frames, same shared phone set):
  xtts        — trained ONLY on XTTS self-produced audio   [THE HEADLINE: transfer to real]
  piper       — trained ONLY on weak-synth (piper) audio   [STRONG-SYNTH-MATTERS control]
  xtts+reverb — XTTS audio convolved with a room IR        [CLEAN-CHANNEL / bone-conduction control]
  real(EM)    — trained on REAL labelled train-clean audio [SUPERVISED CEILING]
  real(flat)  — real, flat-start no-EM                     [passive proportional reference]
  kmeans*     — unsupervised k-means on real, oracle-named [generous PASSIVE-unsupervised baseline]

Run (project python; needs substrate_rs + nltk cmudict; NO torch/TTS):
  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/babble_transfer.py
"""
import glob
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve

from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_earns_phone_model import ctxd, fit_model, phone_emission, viterbi_align
from scripts.jabberwock_subword_recognizer import _load_ph

BABBLE = os.environ.get("BABBLE_OUT", "/home/matt/babble_work/babble")
FS = 16000
EM_ITERS = 3
# energy OFF for ALL conditions: the real dev-clean phonebank cache predates the energy channel
# (e=None -> 576-dim shape feature); synth frames() carry energy (594-dim). Force the shared
# shape-only feature everywhere so train and eval dims match and the comparison is fair.
USE_ENERGY = False
# 39-phone ARPAbet (no stress) — the shared inventory the per-frame acc is scored over
CMU39 = set("AA AE AH AO AW AY B CH D DH EH ER EY F G HH IH IY JH K L M N NG OW OY P R S SH "
            "T TH UH UW V W Y Z ZH".split())


def _room_ir(rt60=0.35, fs=FS, seed=0):
    """synthetic exponential-decay room impulse response (a reverberant, NON-clean channel)."""
    rng = np.random.default_rng(seed)
    n = int(rt60 * fs)
    t = np.arange(n) / fs
    ir = rng.standard_normal(n) * np.exp(-6.9 * t / rt60)
    ir[0] += 1.0
    return (ir / np.linalg.norm(ir)).astype(np.float32)


def load_synth_samples(subdir, reverb=False):
    """read <word>__*.wav clips -> [(word, M, e, phones)] using the agent's own cochleagram frames()."""
    d = os.path.join(BABBLE, subdir)
    ir = _room_ir() if reverb else None
    out = []
    for wav in sorted(glob.glob(os.path.join(d, "*.wav"))):
        word = os.path.basename(wav).split("__")[0]
        ph = cmu_phones(word)
        if not ph:
            continue
        x, sr = sf.read(wav, dtype="float64")
        if x.ndim > 1:
            x = x.mean(1)
        if sr != FS or len(x) < int(0.06 * FS):
            continue
        if ir is not None:
            x = fftconvolve(x, ir)[:len(x) + len(ir) - 1]
            x = x / (np.abs(x).max() + 1e-9)
        try:
            M, e = frames(x)
        except Exception:
            continue
        if M.shape[0] < max(4, len(ph)):
            continue
        out.append((word, M, e, [str(p) for p in ph]))
    return out


def em_train(samples, iters=EM_ITERS):
    """earn the phone model: ctxd features, flat-start proportional labels, then EM/Viterbi
    forced-alignment to the KNOWN phone sequence. Returns (enc, cent, cphone, phones_set, pi)."""
    phones_set = sorted({p for _w, _M, _e, ph in samples for p in ph})
    pi = {p: i for i, p in enumerate(phones_set)}; nP = len(phones_set)
    feats = [ctxd(M, e=(e if USE_ENERGY else None)) for _w, M, e, _ph in samples]
    pjs = [[pi[p] for p in ph] for _w, _M, _e, ph in samples]
    labels = []
    for cx, (_w, _M, _e, ph) in zip(feats, samples):
        n = len(cx); P = len(ph)
        labels.append([pi[ph[int(i * P / n)]] for i in range(n)])
    iv = {i: p for p, i in pi.items()}
    enc = cent = cphone = None
    for it in range(iters + 1):
        X = np.concatenate(feats); Y = [iv[i] for s in labels for i in s]
        enc, cent, cphone = fit_model(X, Y, phones_set, pi)
        if it == iters:
            break
        new = []
        for cx, pj in zip(feats, pjs):
            emis = phone_emission(cx, enc, cent, cphone, nP)
            new.append(viterbi_align(emis, pj))
        labels = new
    return enc, cent, cphone, phones_set, pi


def flat_train(samples):
    """passive proportional reference: flat-start only, no EM forced-alignment."""
    return em_train(samples, iters=0)


def load_real_samples(glob_pat, cap):
    """real LibriSpeech words from the phonebank cache -> [(word, M, e, phones)]."""
    out = []
    for (w, fr, ph, e) in _load_ph(glob_pat, cap, with_energy=True):
        out.append((w, np.asarray(fr, float), np.asarray(e, float) if e is not None else None,
                    [str(p) for p in ph]))
    return out


def build_eval(real_dev, shared):
    """per-frame eval set on real dev: ctxd features + proportional phone label (the lineage proxy).
    Restricted to frames whose true phone is in the shared inventory."""
    Xs, Ys = [], []
    for (_w, M, e, ph) in real_dev:
        cx = ctxd(M, e=(e if USE_ENERGY else None))
        n = len(cx); P = len(ph)
        lab = [ph[int(i * P / n)] for i in range(n)]
        for k in range(n):
            if lab[k] in shared:
                Xs.append(cx[k]); Ys.append(lab[k])
    return np.asarray(Xs), Ys


def per_frame_acc(model, Xe, Ye, shared):
    enc, cent, cphone, phones_set, pi = model
    can = [j for j in range(len(phones_set)) if phones_set[j] in shared]  # restrict to shared phones
    if not can:
        return 0.0
    cmask = np.array([cphone[c] in set(can) for c in range(len(cphone))])
    cent_s, cphone_s = cent[cmask], cphone[cmask]
    sims = enc(Xe) @ cent_s.T
    pred = cphone_s[sims.argmax(1)]
    return float(np.mean([phones_set[pred[k]] == Ye[k] for k in range(len(Ye))]))


def kmeans_oracle(real_train, real_dev, shared, K=None):
    """generous PASSIVE-unsupervised baseline: k-means on real frames (NO labels), name each
    cluster by its majority TRUE phone on TRAIN (oracle naming), score per-frame on dev."""
    K = K or len(shared)
    Xtr = np.concatenate([ctxd(M, e=(e if USE_ENERGY else None)) for _w, M, e, _ph in real_train])
    # train labels (proportional) used ONLY to name clusters (the oracle leak; a generous upper bound)
    ytr = []
    for (_w, M, e, ph) in real_train:
        n = len(M); P = len(ph)
        ytr += [ph[int(i * P / n)] for i in range(n)]
    rng = np.random.default_rng(0)
    C = Xtr[rng.choice(len(Xtr), K, replace=False)].copy()
    for _ in range(8):
        lab = ((Xtr[:, None, :] - C[None]) ** 2).sum(2).argmin(1) if len(Xtr) < 4000 else \
            np.argmin((Xtr ** 2).sum(1)[:, None] - 2 * Xtr @ C.T + (C ** 2).sum(1)[None, :], axis=1)
        for k in range(K):
            m = Xtr[lab == k]
            if len(m):
                C[k] = m.mean(0)
    from collections import Counter
    name = {}
    for k in range(K):
        cnt = Counter(ytr[i] for i in range(len(ytr)) if lab[i] == k and ytr[i] in shared)
        name[k] = cnt.most_common(1)[0][0] if cnt else None
    Xe, Ye = build_eval(real_dev, shared)
    de = np.argmin((Xe ** 2).sum(1)[:, None] - 2 * Xe @ C.T + (C ** 2).sum(1)[None, :], axis=1)
    return float(np.mean([name[de[k]] == Ye[k] for k in range(len(Ye))]))


def main():
    t0 = time.time()
    print("=" * 90)
    print("BABBLING LOOP — recogniser trained on SELF-PRODUCED audio PERCEIVES real speech (donkey=0)")
    print("=" * 90)

    # ---- real eval data (the test): LibriSpeech dev-clean held words from the phonebank cache ----
    real_dev = load_real_samples("dev-clean_*.pkl", 8)
    real_dev = real_dev[:1500]
    shared = CMU39
    Xe, Ye = build_eval(real_dev, shared)
    from collections import Counter
    maj = Counter(Ye).most_common(1)[0]
    print(f"  REAL dev eval: {len(real_dev)} words, {len(Ye)} frames over {len(set(Ye))} phones")
    print(f"  baselines: uniform chance 1/{len(shared)} = {1/len(shared):.3f}   "
          f"majority-phone ('{maj[0]}') = {maj[1]/len(Ye):.3f}")
    print("-" * 90, flush=True)

    results = {}

    # ---- MAIN: trained ONLY on XTTS self-produced audio ----
    xs = load_synth_samples("xtts")
    print(f"  [xtts]  {len(xs)} self-produced clips", flush=True)
    m = em_train(xs)
    results["xtts(EM)"] = per_frame_acc(m, Xe, Ye, shared)
    print(f"  [xtts]  per-frame phone acc on REAL = {results['xtts(EM)']:.3f}", flush=True)

    # ---- STRONG-SYNTH-MATTERS: weak synth (piper) ----
    ps = load_synth_samples("piper")
    print(f"  [piper] {len(ps)} weak-synth clips", flush=True)
    if ps:
        m = em_train(ps)
        results["piper(EM)"] = per_frame_acc(m, Xe, Ye, shared)
        print(f"  [piper] per-frame phone acc on REAL = {results['piper(EM)']:.3f}", flush=True)

    # ---- CLEAN-CHANNEL: XTTS through a reverberant room IR ----
    xr = load_synth_samples("xtts", reverb=True)
    print(f"  [xtts+reverb] {len(xr)} reverb-degraded clips", flush=True)
    m = em_train(xr)
    results["xtts+reverb(EM)"] = per_frame_acc(m, Xe, Ye, shared)
    print(f"  [xtts+reverb] per-frame phone acc on REAL = {results['xtts+reverb(EM)']:.3f}", flush=True)

    # ---- SUPERVISED CEILING + PASSIVE references: real labelled audio ----
    real_train = load_real_samples("train-clean-100_*.pkl", 6)
    real_train = real_train[:4000]
    print(f"  [real]  {len(real_train)} real labelled train words (ceiling + passive refs)", flush=True)
    m = em_train(real_train)
    results["real(EM)=ceiling"] = per_frame_acc(m, Xe, Ye, shared)
    print(f"  [real(EM) ceiling]   per-frame = {results['real(EM)=ceiling']:.3f}", flush=True)
    m = flat_train(real_train)
    results["real(flat)=passive"] = per_frame_acc(m, Xe, Ye, shared)
    print(f"  [real(flat) passive] per-frame = {results['real(flat)=passive']:.3f}", flush=True)
    results["kmeans-oracle=passive*"] = kmeans_oracle(real_train, real_dev, shared)
    print(f"  [kmeans oracle-named passive*] per-frame = {results['kmeans-oracle=passive*']:.3f}", flush=True)

    print("=" * 90)
    print("  SUMMARY (per-frame phone accuracy on REAL LibriSpeech dev-clean):")
    print(f"    uniform chance                 {1/len(shared):.3f}")
    print(f"    majority-phone baseline        {maj[1]/len(Ye):.3f}")
    for k in ["kmeans-oracle=passive*", "real(flat)=passive", "piper(EM)", "xtts+reverb(EM)",
              "xtts(EM)", "real(EM)=ceiling"]:
        if k in results:
            print(f"    {k:30s} {results[k]:.3f}")
    print("=" * 90)
    print(f"  donkey=0 at inference: this process imported no TTS/torch (synth audio read as wavs).")
    print(f"  total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
