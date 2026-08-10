"""ANALYSIS-BY-SYNTHESIS recognition — the agent's OWN pick.

The agent's compression-payoff selector (agent_improves_speech_decide.py) chose, at
the recognition level (payoff 4, score 3999): "recovering causes from effects is an
INVERSE problem that needs a FORWARD model (articulation->acoustics) to invert — an
internal synthesiser the loop can run and match against." It unifies speech_
perception + perception_production_link + acoustic_cues + generative_collapse.

This ENACTS that pick on FSDD cross-speaker digit recognition. The forward model's
key speaker degree-of-freedom is VOCAL-TRACT LENGTH (the whisper finding: the message
is in the FILTER/tract, not the source). So:

  forward model g(digit, alpha) = the agent's digit prototype, warped along the
                                  log-frequency (cochlear band) axis by VTL factor alpha
  recognition  = argmin_digit  min_alpha  dist(observed, g(digit, alpha))

The inner min over alpha INVERTS the speaker (recovers the digit's gesture under the
best-fit tract), exactly the inverse-problem the agent named. Baseline = the same
nearest-prototype match with NO warp (alpha=1). If analysis-by-synthesis beats the
baseline cross-speaker, the agent's pick pays off.

Cochlea is the held op (substrate_rs.speech._audio.cochlea / a1_responses). The warp
+ match is world-adapter MEASUREMENT (reads, doesn't decide).

Run: python scripts/speech_analysis_by_synthesis.py [test_speaker] [n_per]
"""
from __future__ import annotations
import os
import re
import sys
import time
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio, seed_speech_grammar

DATA = "/tmp/fsdd/recordings"
FN = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")
N_BANDS = 24
N_WIN = 12


def load_wav(path):
    with wave.open(path, "rb") as w:
        fs = w.getframerate(); n = w.getnframes(); buf = w.readframes(n)
    arr = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr * 0.7 / peak).astype(np.float32), fs


def feat(s, bank, samples, fs):
    """(bands x windows) cochlear trajectory via HELD cochlea ops."""
    buf = _audio.audio_from_array(s, samples, sample_rate=fs)
    resps = _audio.a1_responses(s, buf, bank)
    out = np.zeros((len(bank), N_WIN), np.float32)
    for bi, r in enumerate(resps):
        resp = _audio.audio_to_array(s, r).astype(np.float32)
        if resp.ndim > 1:
            resp = resp.mean(axis=1)
        n = len(resp)
        if n == 0:
            continue
        wl = max(1, n // N_WIN)
        for w in range(N_WIN):
            seg = resp[w * wl:(w + 1) * wl]
            if len(seg):
                out[bi, w] = float(np.sqrt(np.mean(seg ** 2)))
    # per-utterance energy normalise (factor out overall gain/loudness).
    nrm = np.linalg.norm(out)
    return out / nrm if nrm > 1e-8 else out


def warp_bands(proto, alpha):
    """Forward model's speaker DOF: resample the band (log-freq) axis by VTL alpha.
    alpha>1 = longer tract (lower formants) -> shift energy down the bands."""
    nb = proto.shape[0]
    src = np.arange(nb)
    tgt = np.clip(src * alpha, 0, nb - 1)
    out = np.empty_like(proto)
    for w in range(proto.shape[1]):
        out[:, w] = np.interp(src, tgt, proto[:, w])
    return out


ALPHAS = np.linspace(0.80, 1.25, 10)   # candidate vocal-tract factors to invert over


def main():
    test_spk = sys.argv[1] if len(sys.argv) > 1 else "george"
    n_per = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    files = []
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            files.append((os.path.join(DATA, fn), int(m.group(1)), m.group(2)))
    s = Substrate()
    _audio.seed_audio_grammar(s)    # register AudioBuffer / Filter vocabulary in Γ
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)

    print("=" * 78)
    print(f"ANALYSIS-BY-SYNTHESIS (the agent's pick) — FSDD cross-speaker")
    print(f"  held-out test speaker = {test_spk}; {n_per}/digit/speaker; "
          f"{N_BANDS} bands x {N_WIN} win")
    print("=" * 78)

    t0 = time.time()
    train, test = {d: [] for d in range(10)}, []
    for path, digit, spk in files:
        samples, fs = load_wav(path)
        f = feat(s, bank, samples, fs)
        if spk == test_spk:
            test.append((digit, f))
        else:
            train[digit].append(f)
    print(f"  featurised {len(files)} utts in {time.time()-t0:.1f}s "
          f"(train {sum(len(v) for v in train.values())}, test {len(test)})")

    # FORWARD MODEL = the agent's per-digit prototype (mean production).
    proto = {d: np.mean(train[d], axis=0) for d in range(10) if train[d]}

    # CANONICAL tract = the global mean spectral envelope over ALL train (digit-
    # AND speaker-agnostic). VTLN normalises every utterance's tract to this.
    def env(f):
        return f.mean(axis=1)                       # per-band envelope (time-averaged)
    canonical = np.mean([env(f) for v in train.values() for f in v], axis=0)

    def vtln(f):
        # estimate ONE speaker warp per utterance: align its envelope to canonical
        # (digit-agnostic — the nuisance is the SPEAKER's tract, not the hypothesis).
        a_star = min(ALPHAS, key=lambda a: float(np.linalg.norm(env(warp_bands(f, a)) - canonical)))
        return warp_bands(f, a_star)

    proto_n = {d: np.mean([vtln(f) for f in train[d]], axis=0) for d in range(10) if train[d]}

    def predict_baseline(f):
        return min(proto, key=lambda d: float(np.linalg.norm(f - proto[d])))

    def predict_perhyp(f):                            # WRONG inversion: per-digit warp
        return min(proto, key=lambda d: min(
            float(np.linalg.norm(f - warp_bands(proto[d], a))) for a in ALPHAS))

    def predict_vtln(f):                              # RIGHT inversion: one tract/utt
        fn = vtln(f)
        return min(proto_n, key=lambda d: float(np.linalg.norm(fn - proto_n[d])))

    # The project's KNOWN cross-speaker lever: relational rank (held shape_signature)
    # — gain/monotone-invariant. Compare where the invariance actually lives.
    from substrate_rs import Substrate as _Sub  # held op already imported via s
    def rel(f):
        return np.asarray(s.shape_signature([float(x) for x in f.flatten()]), np.float32)
    proto_r = {d: rel(proto[d]) for d in proto}
    def predict_rel(f):
        r = rel(f)
        return min(proto_r, key=lambda d: float(np.linalg.norm(r - proto_r[d])))

    nb = nh = nv = nr = 0
    for digit, f in test:
        nb += (predict_baseline(f) == digit)
        nh += (predict_perhyp(f) == digit)
        nv += (predict_vtln(f) == digit)
        nr += (predict_rel(f) == digit)
    n = len(test)
    print(f"\n  baseline (nearest prototype, no warp):        {nb}/{n} = {nb/n:.1%}")
    print(f"  per-hypothesis warp (unconstrained inversion): {nh}/{n} = {nh/n:.1%}")
    print(f"  VTLN analysis-by-synthesis (one tract/utt):    {nv}/{n} = {nv/n:.1%}")
    print(f"  relational rank (shape_signature, held lever):  {nr}/{n} = {nr/n:.1%}")
    dv = (nv - nb) / n
    print(f"\n  VERDICT: forward-model VTL warp {'HELPS' if dv > 0 else 'is a NULL'} "
          f"cross-speaker ({dv:+.1%}); relational rank delta {(nr-nb)/n:+.1%}.")
    print("=" * 78)


if __name__ == "__main__":
    main()
