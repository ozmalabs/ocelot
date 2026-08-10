"""HOW FAR DOES COVERAGE GO -- the N-speaker curve out to MANY real speakers (VCTK, 109 talkers).

The 12-voice curve confirmed the COVERAGE WALL (held-out recall 41%->64%, still climbing at N=8). The agent's
developmental bet: cross-talker word recognition is earned from a DISTRIBUTION of talkers. So map the curve out
to N=64 real, distinct speakers (VCTK multi-speaker model) on a held-out set of UNSEEN VCTK speakers, and see
WHERE held-out recognition saturates -- the answer to "how many speakers crack it". Plain 1-NN vs the project-out
(WCCN) at the top N. Scored against the known word.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_vctk_curve
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scipy.signal import resample_poly
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from scripts.jabberwock_project_out import vec_of, wccn

FS = 8000
WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
N_VALUES = [1, 2, 4, 8, 16, 32, 64]
N_TRAIN, N_HELD = 64, 12
RENDS = 3                  # bank 0,1 ; test 2 (12 held-out speakers keeps per-point noise low)


def main():
    print("=" * 96)
    print("VCTK COVERAGE CURVE — held-out recognition of UNSEEN speakers vs N banked real speakers (out to 64).")
    print("=" * 96)
    from piper import PiperVoice, SynthesisConfig
    v = PiperVoice.load(os.path.expanduser("~/.cache/ozma/piper_voices/en_GB-vctk-medium.onnx"))

    def synth(word, sid):
        cfg = SynthesisConfig(length_scale=1.0, noise_scale=0.667, noise_w_scale=0.8, speaker_id=sid)
        ch = list(v.synthesize(word, cfg))
        a = np.concatenate([c.audio_int16_array for c in ch]).astype(np.float64) / 32768.0
        return resample_poly(a, FS, ch[0].sample_rate)

    train_sids = list(range(N_TRAIN))           # speakers 0..63
    held_sids = list(range(N_TRAIN, N_TRAIN + N_HELD))   # 64..75 -- UNSEEN
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    print(f"  {N_TRAIN} train speakers, {N_HELD} held-out UNSEEN | {len(WORDS)} words | {RENDS} renditions")
    print("  synthesising 76 real speakers x 9 words (VCTK)...", flush=True)
    vecs = {}
    for sid in train_sids + held_sids:
        for w in WORDS:
            for r in range(RENDS):
                try:
                    x = synth(w, sid)
                    vecs[(sid, w, r)] = vec_of(SDW.feature_channels(s, np.asarray(x, dtype=np.float64), FS))
                except Exception:
                    pass
        if sid % 16 == 15:
            print(f"    ...{sid+1} speakers done", flush=True)
    D = min(len(x) for x in vecs.values())
    for k in vecs:
        vecs[k] = vecs[k][:D]

    def bank(train, project):
        X = np.stack([vecs[(sp, w, r)] for sp in train for w in WORDS for r in (0, 1) if (sp, w, r) in vecs])
        y = np.array([w for sp in train for w in WORDS for r in (0, 1) if (sp, w, r) in vecs])
        W = wccn(X, y) if project else np.eye(D)
        Xn = X @ W; Xn /= (np.linalg.norm(Xn, axis=1, keepdims=True) + 1e-9)
        return Xn, y, W

    def recall(train, project):
        Xn, y, W = bank(train, project)
        hits = tot = 0
        for sp in held_sids:
            for w in WORDS:
                if (sp, w, 2) not in vecs:
                    continue
                q = vecs[(sp, w, 2)] @ W; q /= (np.linalg.norm(q) + 1e-9)
                tot += 1; hits += int(y[int(np.argmax(Xn @ q))] == w)
        return hits / tot if tot else 0.0

    print(f"\n  held-out recall vs N (chance {100/len(WORDS):.0f}%):")
    print(f"    {'N speakers':>11}{'PLAIN':>10}")
    plain = []
    for N in N_VALUES:
        p = recall(train_sids[:N], False)
        plain.append((N, p))
        print(f"    {N:>11}{p*100:>9.0f}%")
    pj = recall(train_sids[:N_VALUES[-1]], True)

    print("\n" + "=" * 96)
    first, last = plain[0][1], plain[-1][1]
    # find where it effectively saturates (within 3pt of the max)
    mx = max(p for _n, p in plain)
    knee = next((n for n, p in plain if p >= mx - 0.03), N_VALUES[-1])
    print(f"  COVERAGE CURVE: held-out recall {first*100:.0f}% (N=1) -> {last*100:.0f}% (N={N_VALUES[-1]}), peak {mx*100:.0f}%.")
    print(f"  Effectively saturates by ~N={knee} speakers. project-out (WCCN) at N={N_VALUES[-1]}: {pj*100:.0f}% (vs plain {last*100:.0f}%).")
    if last >= 0.85:
        print(f"  THE WALL DISSOLVES WITH COVERAGE: recognising UNSEEN speakers reaches {last*100:.0f}% once enough talkers are")
        print("  banked -- the agent's developmental bet confirmed. It was never a representation/authoring problem; it")
        print("  was speaker COVERAGE. Cross-talker recognition is earned from a DISTRIBUTION of talkers, as predicted.")
    elif last - first > 0.15:
        print(f"  STRONG COVERAGE EFFECT ({first*100:.0f}->{last*100:.0f}%) but not yet saturated -- more speakers would push further;")
        print("  the project-out / a sharper feature is the lever to reach human-level from here.")
    else:
        print(f"  coverage plateaus at {mx*100:.0f}% -- diminishing returns; the residual gap is representational, not coverage.")
    print("=" * 96)


if __name__ == "__main__":
    main()
