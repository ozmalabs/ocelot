"""synth_parent_loso_probe — the ACTUAL experiment, cheaply: does adding the
voicebox's VARIED-VOICE synthetic exemplars to a real-FSDD-train bank lift the
HUMAN cross-speaker LOSO probe?

Three banks, same human-FSDD LOSO probe (held-out speaker, full lexicon, blind_guess):
  (1) REAL-ONLY      — N real FSDD train exemplars/digit (the espeak-parent analogue
                       for the recognizer: only real seen-speaker clips).
  (2) REAL + ESPEAK  — real train + espeak parent_say clips (what the espeak parent
                       actually banks).
  (3) REAL + SYNTH   — real train + the voicebox's varied-voice (f0 x vtl x q) synthetic
                       exemplars (the PHYSICS-MODEL varied-voice parent).

If (3) lifts LOSO over (1)/(2), the varied-voice physics parent closes the cross-speaker
gap. If it does not (synth lands off-manifold), the voicebox isn't good enough yet and
the move is to fix the voicebox / front end, not run the long parent loop.

This is the A/B the task asks for, run at the BANK level (the loop's banking is what
ultimately drives recognition), so it answers the question in minutes not hours.
"""
from __future__ import annotations
import os, sys, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from substrate_rs import Substrate
import domains.self_directed_speech_world as W
import domains.parent_teacher as P
from domains.stt_pipeline import STTPipeline, STTParams

DIGITS = W._DIGIT_WORDS["en"]
FS = W._TARGET_FS
CELL = "digit|fsdd|en"


def extract_traj(x, fs):
    sub = Substrate(); pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub); pipe._ensure_audio_pipeline(sub); pipe.ingest(sub, x); sub.tick(50000)
    best = None
    for s in sub.nodes("AcousticSign"):
        t = sub.node(s)["attrs"].get("trajectory")
        if t and (best is None or len(t) > len(best)):
            best = t
    return np.array([float(v) for v in best], dtype=np.float32) if best else None


def _resample_vtl(audio, vtl):
    audio = np.asarray(audio, dtype=np.float32)
    if vtl == 1.0 or audio.size == 0:
        return audio
    n = max(1, int(round(audio.size / vtl)))
    idx = np.clip((np.arange(n) * vtl).astype(int), 0, audio.size - 1)
    return np.ascontiguousarray(audio[idx])


def fresh():
    s = Substrate(); pipe = STTPipeline(STTParams(sample_rate=FS))
    pipe.attach(s); pipe._ensure_audio_pipeline(s); W.install_speech_world_rules(s)
    return s, pipe


def loso_probe(loso_speakers, n_per=6, seed=99993):
    idx = W.fsdd_index_for(loso_speakers)
    rng = random.Random(seed); probes = []
    for w in DIGITS:
        paths = list(idx.get(w, [])); rng.shuffle(paths)
        for p in paths[:n_per]:
            x, fs = W.load_fsdd_clip(p); probes.append((w, x, fs))
    return probes


def measure(s, probe):
    tot = cor = 0
    for w, x, fs in probe:
        ch = W.feature_channels(s, x, fs)
        g = W.blind_guess(s, ch, CELL, restrict_to=None)
        tot += 1; cor += (g == w)
    return cor / max(tot, 1)


def main():
    n_real = 18
    train_spk = [sp for sp in W.fsdd_speakers() if sp != W.fsdd_speakers()[-1]]
    loso_spk = [W.fsdd_speakers()[-1]]
    train_idx = W.fsdd_index_for(train_spk)
    probe = loso_probe(loso_spk)
    seen_probe = []  # seen-speaker held-out clips (train speakers, unbanked indices)
    for w in DIGITS:
        for p in train_idx[w][n_real: n_real + 6]:
            x, fs = W.load_fsdd_clip(p); seen_probe.append((w, x, fs))
    print(f"[setup] train {train_spk}; LOSO held-out {loso_spk}; "
          f"{len(probe)} LOSO probes, {len(seen_probe)} seen-speaker probes", flush=True)

    # per-digit trajectory for the synthetic voices.
    traj = {w: extract_traj(W.load_fsdd_clip(train_idx[w][0])[0], FS) for w in DIGITS}

    def bank_real(s, pipe):
        for w in DIGITS:
            for p in train_idx[w][:n_real]:
                x, _ = W.load_fsdd_clip(p); W.bank_exemplar(s, w, CELL, x, FS)

    # (1) REAL-ONLY
    s1, p1 = fresh(); bank_real(s1, p1)
    seen1, loso1 = measure(s1, seen_probe), measure(s1, probe)
    print(f"\n(1) REAL-ONLY        seen {seen1:.3f}  LOSO {loso1:.3f}", flush=True)

    # (2) REAL + ESPEAK (the espeak parent's banked exemplars: IDS + ADS register)
    s2, p2 = fresh(); bank_real(s2, p2)
    for w in DIGITS:
        for reg in ("IDS", "ADS"):
            ex, efs = P.parent_say(w, "en", register=reg)
            for _ in range(6):           # match synth count below (~ per-digit budget)
                W.bank_exemplar(s2, w, CELL, ex, efs)
    seen2, loso2 = measure(s2, seen_probe), measure(s2, probe)
    print(f"(2) REAL + ESPEAK    seen {seen2:.3f}  LOSO {loso2:.3f}", flush=True)

    # (3) REAL + SYNTH varied-voice (the physics-model varied-voice parent)
    f0s = [95.0, 130.0, 190.0, 230.0]; vtls = [0.85, 1.0, 1.15]; qs = [3.0, 5.0]
    s3, p3 = fresh(); bank_real(s3, p3)
    n_synth = 0
    for w in DIGITS:
        t = traj[w]
        if t is None:
            continue
        for f0 in f0s:
            for vtl in vtls:
                for q in qs:
                    a = p3.speak_trajectory(s3, t, f0_hz=f0, q_factor=q)
                    a = _resample_vtl(a, vtl)
                    if np.asarray(a).size <= 1 or not np.any(np.abs(a) > 1e-5):
                        continue
                    W.bank_exemplar(s3, w, CELL, a, FS); n_synth += 1
    seen3, loso3 = measure(s3, seen_probe), measure(s3, probe)
    print(f"(3) REAL + SYNTH     seen {seen3:.3f}  LOSO {loso3:.3f}  "
          f"({n_synth} synth exemplars added)", flush=True)

    # (4) SYNTH-ONLY (the pure varied-voice parent with NO real seen-speaker clips —
    #     the strongest form of the hypothesis: can synth alone teach human LOSO?)
    s4, p4 = fresh()
    for w in DIGITS:
        t = traj[w]
        if t is None:
            continue
        for f0 in f0s:
            for vtl in vtls:
                for q in qs:
                    a = p4.speak_trajectory(s4, t, f0_hz=f0, q_factor=q)
                    a = _resample_vtl(a, vtl)
                    if np.asarray(a).size <= 1 or not np.any(np.abs(a) > 1e-5):
                        continue
                    W.bank_exemplar(s4, w, CELL, a, FS)
    seen4, loso4 = measure(s4, seen_probe), measure(s4, probe)
    print(f"(4) SYNTH-ONLY       seen {seen4:.3f}  LOSO {loso4:.3f}", flush=True)

    print("\n========== VERDICT ==========", flush=True)
    print(f"  human seen-speaker:  real {seen1:.3f} | +espeak {seen2:.3f} | "
          f"+synth {seen3:.3f} | synth-only {seen4:.3f}", flush=True)
    print(f"  human LOSO (x-spk):  real {loso1:.3f} | +espeak {loso2:.3f} | "
          f"+synth {loso3:.3f} | synth-only {loso4:.3f}", flush=True)
    d_synth = loso3 - loso1; d_espeak = loso2 - loso1
    print(f"\n  varied-voice SYNTH parent lifts LOSO over real-only by {d_synth:+.3f}", flush=True)
    print(f"  espeak parent lifts LOSO over real-only by            {d_espeak:+.3f}", flush=True)
    if d_synth > 0.02 and d_synth > d_espeak:
        print("  => YES: the physics-model varied-voice parent closes cross-speaker gap "
              "more than espeak. Run the long loop.", flush=True)
    else:
        print("  => NO: synth exemplars do NOT lift the human LOSO (synthetic-vs-human "
              "domain shift dominates). The voicebox is off-manifold vs real speech; "
              "the move is to fix the voicebox/front end, not run the long parent loop.",
              flush=True)
    print("[MARKER] SYNTH_PARENT_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
