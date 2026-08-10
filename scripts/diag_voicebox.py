"""diag_voicebox — isolate WHY varied-voice synthesis isn't recognised.

Controls:
  A. SINGLE-clip trajectory (no averaging) synthesized at a NEUTRAL voice, recognised
     against a bank that INCLUDES re-synthesised exemplars of the same digits.
  B. Self-consistency: bank the SYNTHESISED clips themselves, then recognise held-out
     synthesised clips — does the voicebox at least produce a self-consistent space?
  C. Klatt-LF vs source-filter synth at neutral voice.
  D. Acoustic distance: cochleagram of synth(five) vs real FSDD five vs real FSDD four
     — is synth closer to the wrong digit?
"""
from __future__ import annotations
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from substrate_rs import Substrate
import domains.self_directed_speech_world as W
from domains.stt_pipeline import STTPipeline, STTParams


def extract_traj(x, fs):
    sub = Substrate(); pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub); pipe._ensure_audio_pipeline(sub); pipe.ingest(sub, x); sub.tick(50000)
    best = None
    for s in sub.nodes("AcousticSign"):
        t = sub.node(s)["attrs"].get("trajectory")
        if t and (best is None or len(t) > len(best)):
            best = t
    return np.array([float(v) for v in best], dtype=np.float32) if best else None


def main():
    digits = W._DIGIT_WORDS["en"]
    fs = W._TARGET_FS
    s = Substrate(); pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(s); pipe._ensure_audio_pipeline(s); W.install_speech_world_rules(s)
    train_idx = W.fsdd_index_for([sp for sp in W.fsdd_speakers() if sp != W.fsdd_speakers()[-1]])
    cell = "digit|fsdd|en"

    # one trajectory per digit from a single clip; remember that clip's f0 region.
    traj1 = {}
    for w in digits:
        p = train_idx[w][0]
        x, _ = W.load_fsdd_clip(p)
        traj1[w] = extract_traj(x, fs)

    # ---- Experiment B: SELF-CONSISTENT synth space ----
    # bank synth(digit) at a few neutral-ish voices, then recognise synth(digit) at a
    # HELD-OUT voice. If even this is at floor, the voicebox space is not separable.
    print("=== B: self-consistent synth space (bank synth, recognise held-out synth) ===")
    bank_voices = [(120.0, 4.0), (150.0, 4.0), (110.0, 5.0)]
    test_voices = [(135.0, 4.0), (100.0, 4.0)]
    for w in digits:
        t = traj1[w]
        if t is None:
            continue
        for f0, q in bank_voices:
            a = pipe.speak_trajectory(s, t, f0_hz=f0, q_factor=q)
            W.bank_exemplar(s, w, cell, a, fs)
    tot = cor = 0
    for w in digits:
        t = traj1[w]
        if t is None:
            continue
        for f0, q in test_voices:
            a = pipe.speak_trajectory(s, t, f0_hz=f0, q_factor=q)
            ch = W.feature_channels(s, a, fs)
            g = W.blind_guess(s, ch, cell, restrict_to=None)
            tot += 1; cor += (g == w)
    print(f"  self-consistent synth recognition: {cor}/{tot} = {cor/max(tot,1):.3f}")

    # ---- Experiment A: real-bank, neutral synth ----
    print("\n=== A: REAL FSDD bank, recognise NEUTRAL synth (no vtl warp) ===")
    s2 = Substrate(); pipe2 = STTPipeline(STTParams(sample_rate=fs))
    pipe2.attach(s2); pipe2._ensure_audio_pipeline(s2); W.install_speech_world_rules(s2)
    for w in digits:
        for p in train_idx[w][:15]:
            x, _ = W.load_fsdd_clip(p); W.bank_exemplar(s2, w, cell, x, fs)
    tot = cor = 0; conf = {}
    for w in digits:
        t = traj1[w]
        if t is None:
            continue
        a = pipe2.speak_trajectory(s2, t, f0_hz=120.0, q_factor=4.0)
        ch = W.feature_channels(s2, a, fs)
        g = W.blind_guess(s2, ch, cell, restrict_to=None)
        tot += 1; cor += (g == w)
        conf[w] = g
    print(f"  neutral synth vs real bank: {cor}/{tot} = {cor/max(tot,1):.3f}")
    print(f"  guesses: {conf}")

    # ---- Experiment D: acoustic distance synth vs real ----
    print("\n=== D: is synth(w) closer to real(w) than to real(other)? ===")
    def feat(x):
        return np.asarray(W.feature_channels(s2, x, fs)[0], dtype=np.float64)
    # real centroids
    real_cent = {}
    for w in digits:
        fs_list = [feat(W.load_fsdd_clip(p)[0]) for p in train_idx[w][:15]]
        real_cent[w] = np.mean(fs_list, axis=0)
    nearest_right = 0
    for w in digits:
        t = traj1[w]
        if t is None:
            continue
        a = pipe2.speak_trajectory(s2, t, f0_hz=120.0, q_factor=4.0)
        fv = feat(a)
        dists = {ww: float(np.linalg.norm(fv - real_cent[ww])) for ww in digits}
        nn = min(dists, key=dists.get)
        nearest_right += (nn == w)
        mark = "OK" if nn == w else f"-> {nn}"
        print(f"  {w:6s} nearest real centroid: {nn:6s} {mark}  (self d={dists[w]:.3f}, min d={dists[nn]:.3f})")
    print(f"  synth nearest-correct: {nearest_right}/{len(digits)}")
    print("[MARKER] DIAG_VOICEBOX_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
