"""babble_rich_world_stage1_loso — STAGE 1 of the babble-with-a-rich-generated-world.

Does a LEARNED across-voice shape (not the off-manifold seeded tube) break past
CMVN's 0.570 cross-speaker cap, AND does a TTS-generated world transfer to real
speech? This is STAGE 1 (the LEARNED voice-shape library + predict-subtract); the
full closed-loop self-spoken babble is LATER.

THE CLEAN PATH (ozma_bootstrap_forward_model_from_generation): a trained TTS is the
WORLD (it generates on-manifold diverse speech); the agent LEARNS its OWN voice-shape
library from it (owned mean+SVD, NO net), and recognises on the residual with its
UNCHANGED DtwTo. The seeded-prototype KILL (docs/seeded_prototype_loso.md) showed a
GUESSED shape peels the word; this tests whether a LEARNED shape does not.

THREE REGIMES on the SAME robust SC 40-speaker LOSO (ungameable; held-out REAL
speakers never banked), all recognised by the SAME agent DtwTo trajectory recognizer:

  (a) CMVN                — the 0.570 baseline: per-utterance mean-subtract residual
                            (no learned library), DtwTo over the trajectory.
  (b) LEARNED-FROM-TTS    — voice-shapes LEARNED from the TTS-generated world
                            (diverse synthetic speakers), predict-subtract, DtwTo.
  (c) LEARNED-FROM-REAL   — the honest CONTROL: voice-shapes LEARNED from the REAL SC
                            TRAIN speakers (each train speaker's consistent shape),
                            predict-subtract, DtwTo.

This separates two questions:
  · does a LEARNED across-voice shape beat CMVN at all?  -> compare (c) vs CMVN.
  · does the TTS world TRANSFER to real?                 -> compare (b) vs (c).

DONKEY BOUNDARY (audited): TTS = the WORLD only (the audio the shapes are learned
FROM); the voice-shape library = LEARNED via owned mean+SVD+projection
(domains/learned_voice_shape) — NO net, NO gradient, NO weight; recognition = the
agent's graph-resident DtwTo (reused UNCHANGED from scripts/dtw_trajectory_loso); the
SC load + 40-speaker split = world-adapter mechanics (reused verbatim from
scripts/sc_loso_frontend_norm); held-out REAL speakers' clips NEVER banked; LOSO
ungameable.

Run: python -m scripts.babble_rich_world_stage1_loso \
        [n_train_spk] [n_held_spk] [n_per] [n_tts_voices] [k] [seed]
"""
from __future__ import annotations

import os
import sys
import random
import subprocess
import tempfile
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
from domains.stt_pipeline import STTPipeline, STTParams
import domains.learned_voice_shape as LVS

# reuse the SAME robust SC LOSO split + bank mechanics (ungameable, held-out never banked)
from scripts.sc_loso_frontend_norm import build_split, bank, CELL, FS
# reuse the agent's UNCHANGED graph-resident DtwTo recognizer mechanics.
from scripts.dtw_trajectory_loso import (
    dtw_predict_term, _traj_tuple, mark_words, _Pred,
    QUERY_NODE_TYPE, QUERY_TRAJ_ATTR, EX_TRAJ_ATTR)

# the digit words the TTS world generates (the SC digit lexicon).
_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine"]


# ---------------------------------------------------------------------------
# THE RICH GENERATED WORLD — a trained TTS voicing the digit words in MANY diverse
# voices. espeak-ng exposes ~100 named voice VARIANTS (en+adam, en+Alicia, ...); we
# cross them with a pitch grid to make many distinct on-manifold "speakers". Piper is
# preferred when importable (more realistic), espeak-ng is the in-thesis fallback. This
# is the WORLD: the audio the agent learns its voice-shapes FROM; never inverted, never
# used for recognition. Pure world I/O.
# ---------------------------------------------------------------------------

def _espeak_variants():
    """The named voice variants espeak-ng ships (en+<variant>), the cheap diverse
    'speaker' pool. Mechanical parse of `espeak-ng --voices=variant`."""
    try:
        out = subprocess.run(["espeak-ng", "--voices=variant"],
                             capture_output=True, text=True, check=True).stdout
    except Exception:
        return []
    vs = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 5 and parts[4].startswith("!v/"):
            vs.append(parts[4].split("/", 1)[1])
    return vs


def _espeak_say(text, voice, pitch):
    """Voice `text` through espeak-ng with a named variant + pitch, resampled to 8 kHz
    mono (matching SC/FSDD + the cochlea). Pure world I/O."""
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "r.wav")
        out = os.path.join(d, "o.wav")
        subprocess.run(["espeak-ng", "-v", voice, "-p", str(pitch), "-w", raw, text],
                       check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                        "-ar", str(FS), "-ac", "1", "-sample_fmt", "s16", out],
                       check=True, capture_output=True)
        with wave.open(out, "rb") as w:
            fs = w.getframerate()
            x = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
                 .astype(np.float32) / 32768.0)
        return x, fs


def generate_tts_world(n_voices, seed=0):
    """GENERATE the rich world: n_voices distinct TTS 'speakers', each saying every
    digit word once. Returns {voice_id: [waveform per word]} — the per-voice utterance
    pools the agent learns its voice-shapes FROM. Pure world I/O (the TTS is the WORLD;
    never inverted, never used for recognition)."""
    rng = random.Random(seed)
    variants = _espeak_variants()
    if not variants:
        return {}
    pitch_grid = [25, 50, 75, 99]                 # espeak pitch range, diverse f0
    # build n_voices distinct (variant, pitch) speakers, sampled diversely.
    voices = []
    combos = [(v, p) for v in variants for p in pitch_grid]
    rng.shuffle(combos)
    for v, p in combos[:n_voices]:
        voices.append((f"{v}@{p}", f"en+{v}", p))
    world = {}
    for vid, voice, pitch in voices:
        clips = []
        for w in _DIGITS:
            try:
                x, fs = _espeak_say(w, voice, pitch)
                if x.size:
                    clips.append(x)
            except Exception:
                continue
        if clips:
            world[vid] = clips
    return world


# ---------------------------------------------------------------------------
# Learn the REAL-speaker control library from the SAME banked train clips, grouped by
# REAL speaker. This is the (c) regime: each train speaker's consistent shape learned
# by the SAME owned mean+SVD. Pure world-adapter feature derivation.
# ---------------------------------------------------------------------------

def real_voice_clips(n_train_spk, n_held_spk, n_per, seed):
    """The REAL SC TRAIN speakers' clips, grouped {speaker_hash: [waveform]} — the (c)
    control's learning pool. Uses the SAME train-speaker split as the bank (the held-out
    speakers are NEVER included). World-adapter mechanics."""
    words = W.sc_words()
    rng = random.Random(seed)
    speakers = W.sc_speakers(words)
    rng.shuffle(speakers)
    train_spk = speakers[n_held_spk:n_held_spk + n_train_spk]
    # gather per-speaker clips from the SAME train-speaker pool the bank draws from.
    train_idx = W.sc_index_for(train_spk, words)
    rng2 = random.Random(seed + 1)
    per_spk_word = {}
    for w in words:
        paths = list(train_idx.get(w, []))
        rng2.shuffle(paths)
        # bank uses up to n_per per word TOTAL across speakers; here we want each
        # speaker's clips so the shape is per-speaker. Group this word's paths by spk.
        grouped = {}
        for p in paths:
            m = W._SC_FN.match(os.path.basename(p))
            if m:
                grouped.setdefault(m.group(1), []).append(p)
        for spk, plist in grouped.items():
            for p in plist[:max(1, n_per // 10 + 1)]:
                per_spk_word.setdefault(spk, []).append(p)
    # load the waveforms.
    out = {}
    for spk, plist in per_spk_word.items():
        clips = []
        for p in plist:
            try:
                x, fs = W.load_sc_clip(p)
                if x.size:
                    clips.append(np.asarray(x, dtype=np.float64))
            except Exception:
                continue
        if len(clips) >= 2:                       # need >=2 utterances to learn a shape
            out[spk] = clips
    return out


# ---------------------------------------------------------------------------
# The DtwTo recognizer over a chosen residual trajectory. We reuse the agent's
# UNCHANGED graph-resident DtwTo Term; only the TRAJECTORY fed in changes per regime
# (CMVN residual vs learned-shape residual). The recognizer never changes.
# ---------------------------------------------------------------------------

def _residual_traj(x, fs, library):
    """The residual per-frame trajectory for one clip under a given learned library
    (empty library -> CMVN per-utterance mean-subtract). The agent's feature; the
    recognizer that aligns it is unchanged."""
    return LVS.residual_track(x, fs, library)


def write_exemplar_residuals(s, cell_key, library):
    """Write each banked exemplar's residual trajectory (under `library`) onto its node
    as the `traj` attr the DtwTo recognizer reads. Mechanical feature derivation."""
    n = 0
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        if a.get("origin") != "speech_world" or a.get("cell_key") != cell_key:
            continue
        for ex in s.neighbours(c, "has_exemplar"):
            ea = s.node(ex)["attrs"]
            aud = ea.get("audio")
            if aud is None:
                continue
            x = np.asarray(aud, dtype=np.float64)
            fs = float(ea.get("fs", FS))
            s.set_attr(ex, EX_TRAJ_ATTR, _traj_tuple(_residual_traj(x, fs, library)))
            n += 1
    return n


def measure_dtw(s, probe, library):
    """Cross-speaker LOSO under the agent's UNCHANGED DtwTo recognizer over the residual
    trajectory (subtracting the nearest learned shape from `library`; empty -> CMVN)."""
    qn = s.add_node(QUERY_NODE_TYPE, {"origin": "dtw_probe"})
    term = _Pred(dtw_predict_term())
    tot = cor = 0
    for w, x, fs in probe:
        s.set_attr(qn, QUERY_TRAJ_ATTR, _traj_tuple(_residual_traj(x, fs, library)))
        pred = s.evaluate(term, {"q": qn})
        guess = s.node(pred)["attrs"].get("name") if pred is not None else None
        tot += 1
        cor += int(guess == w)
    s.remove_node(qn)
    return cor / max(tot, 1)


def fresh():
    """A fresh substrate with the speech world + the digit|sc|en cell. The DtwTo
    recognizer reads the trajectory directly, so no front-end cues need gating."""
    W.reset_caches()
    s = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=FS))
    pipe.attach(s)
    pipe._ensure_audio_pipeline(s)
    W.install_speech_world_rules(s)
    W.install_cell(s, "digit", "sc", "en")
    return s, pipe


def run_regime(name, train_clips, seen_probe, loso_probe, library):
    """Bank the train clips, write residual trajectories under `library`, measure
    seen + LOSO with the agent's unchanged DtwTo. Same banked exemplars every regime;
    only the subtracted library changes."""
    s, _p = fresh()
    bank(s, train_clips)
    n_traj = write_exemplar_residuals(s, CELL, library)
    n_words = mark_words(s, CELL)
    seen = measure_dtw(s, seen_probe, library)
    loso = measure_dtw(s, loso_probe, library)
    print(f"[{name:18s}] exemplars={n_traj} words={n_words}  "
          f"seen {seen:.3f}  cross-speaker LOSO {loso:.3f}  gap {seen - loso:+.3f}",
          flush=True)
    return seen, loso


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    n_tts_voices = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    k = int(sys.argv[5]) if len(sys.argv) > 5 else 3
    seed = int(sys.argv[6]) if len(sys.argv) > 6 else 20240608

    print(f"[config] train_spk={n_train_spk} held_spk={n_held_spk} n_per={n_per} "
          f"tts_voices={n_tts_voices} k={k} seed={seed}", flush=True)

    train_clips, seen_probe, loso_probe = build_split(n_train_spk, n_held_spk, n_per,
                                                      seed=seed)
    chance = 1.0 / len(W.sc_words())

    # ---- learn the TTS-world voice-shape library (the rich generated world) ----
    print("\n[world] generating the rich TTS world (diverse synthetic speakers) ...",
          flush=True)
    tts_world = generate_tts_world(n_tts_voices, seed=seed)
    print(f"[world] generated {len(tts_world)} TTS voices x {len(_DIGITS)} digits "
          f"= {sum(len(v) for v in tts_world.values())} clips", flush=True)
    tts_library = LVS.learn_library(tts_world, FS, k=k)
    print(f"[learn] TTS library: {len(tts_library)} learned voice-shapes "
          f"(owned mean+SVD, k={k})", flush=True)

    # ---- learn the REAL-train-speaker control library (the honest control) ----
    real_world = real_voice_clips(n_train_spk, n_held_spk, n_per, seed)
    real_library = LVS.learn_library(real_world, FS, k=k)
    print(f"[learn] REAL library: {len(real_library)} learned voice-shapes from real "
          f"SC train speakers (owned mean+SVD, k={k})", flush=True)

    print("\n[run] three regimes, SAME split + SAME banked exemplars + SAME DtwTo:",
          flush=True)
    cmvn_seen, cmvn_loso = run_regime("CMVN", train_clips, seen_probe, loso_probe, [])
    tts_seen, tts_loso = run_regime("LEARNED-FROM-TTS", train_clips, seen_probe,
                                    loso_probe, tts_library)
    real_seen, real_loso = run_regime("LEARNED-FROM-REAL", train_clips, seen_probe,
                                      loso_probe, real_library)

    print("\n" + "=" * 78, flush=True)
    print("BABBLE RICH WORLD — STAGE 1 — robust SC 40-speaker cross-speaker LOSO",
          flush=True)
    print("=" * 78, flush=True)
    print(f"  {'regime':20s} {'seen':>8s} {'LOSO':>8s} {'seen-LOSO gap':>14s} "
          f"{'vs CMVN':>9s}", flush=True)
    for nm, se, lo in (("CMVN", cmvn_seen, cmvn_loso),
                       ("LEARNED-FROM-TTS", tts_seen, tts_loso),
                       ("LEARNED-FROM-REAL", real_seen, real_loso)):
        print(f"  {nm:20s} {se:8.3f} {lo:8.3f} {se - lo:14.3f} "
              f"{lo - cmvn_loso:+9.3f}", flush=True)
    print("-" * 78, flush=True)
    print(f"  chance {chance:.3f}", flush=True)

    lift_c = real_loso - cmvn_loso          # (c) vs CMVN: does a LEARNED shape beat CMVN?
    transfer = tts_loso - real_loso         # (b) vs (c): does the TTS world TRANSFER?
    print(f"  (c) LEARNED-FROM-REAL vs CMVN:   {lift_c:+.3f} "
          f"(CMVN {cmvn_loso:.3f} -> REAL {real_loso:.3f})  "
          f"<- does a LEARNED across-voice shape beat CMVN?", flush=True)
    print(f"  (b) LEARNED-FROM-TTS vs (c):     {transfer:+.3f} "
          f"(REAL {real_loso:.3f} -> TTS {tts_loso:.3f})  "
          f"<- does the TTS world TRANSFER to real?", flush=True)
    print("-" * 78, flush=True)

    # VERDICT 1: does a LEARNED across-voice shape beat CMVN at all? (c vs CMVN)
    if lift_c > 0.02:
        v1 = (f"YES: the LEARNED across-voice shape (from REAL train speakers) LIFTS "
              f"cross-speaker LOSO {lift_c:+.3f} above CMVN's {cmvn_loso:.3f}. A genuine "
              f"on-manifold per-speaker template disentangles where the per-utterance "
              f"mean and the off-manifold seeded tube could not.")
    elif lift_c > 0.005:
        v1 = (f"MARGINAL: the LEARNED-from-real shape moves LOSO {lift_c:+.3f} above "
              f"CMVN — a small lift, not decisive.")
    else:
        v1 = (f"NO (KILL): the LEARNED across-voice shape does NOT beat CMVN "
              f"({lift_c:+.3f}). The across-voice learned template still can't "
              f"disentangle the speaker linearly — the residual is deeper than a linear "
              f"template and needs the full closed-loop babble. No rescue.")
    print(f"  VERDICT 1 (learned-shape vs CMVN): {v1}", flush=True)

    # VERDICT 2: does the TTS-generated world transfer to real? (b vs c)
    if real_loso <= cmvn_loso + 0.005:
        v2 = (f"N/A: (c) did not beat CMVN, so transfer of the TTS world to a working "
              f"learned-shape is moot — the across-voice template itself is the blocker.")
    elif transfer > -0.02:
        v2 = (f"YES: the TTS-generated world TRANSFERS — LEARNED-FROM-TTS {tts_loso:.3f} "
              f"approaches LEARNED-FROM-REAL {real_loso:.3f} ({transfer:+.3f}). The "
              f"generated world is on-manifold enough that shapes learned from it work "
              f"on real held-out speakers.")
    else:
        v2 = (f"NO: the TTS world does NOT transfer — LEARNED-FROM-TTS {tts_loso:.3f} "
              f"falls {-transfer:.3f} below LEARNED-FROM-REAL {real_loso:.3f}. The "
              f"generated world is too synthetic; its learned shapes are off the real "
              f"speaker manifold. No rescue.")
    print(f"  VERDICT 2 (TTS world transfer): {v2}", flush=True)
    print(f"  NOTE: this is STAGE 1 (the learned voice-shape library + predict-subtract); "
          f"the full closed-loop self-spoken babble is later.", flush=True)
    print("[MARKER] BABBLE_RICH_WORLD_STAGE1_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
