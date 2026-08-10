"""universal_loop_phaseAB — Phase A + B of the universal closed loop (no loop yet).

The plan (docs/universal_closed_loop_plan.md) converges on perception = analysis-by-
synthesis: invert a controllable forward model (the voicebox) to recognise. Before
spending on the expensive loop (Phase C), this build confirms the two pieces the loop
stands on are SOUND and ON-MANIFOLD:

  A — a CONTROLLABLE VOICEBOX  synth(word W, voice V) -> cmvn cochleagram features.
      The TTS (espeak-ng; Piper preferred when present) is the WORLD/voicebox the
      agent CONTROLS and HEARS. V is a voice/speaker parameter set the agent derives
      from its OWN speaker_norm/VTL knowledge: a vocal-tract-length scale (VTL — shifts
      ALL formants, domains/speaker_norm), a pitch/f0, and a speaking rate. We span
      that V-space across the cheaply-available espeak named variants x pitch x rate to
      get tens of distinct ON-MANIFOLD voices.

  B — PRODUCTION MEMORY + the COVERAGE TEST. Babble the full (W,V) grid -> the
      EXEMPLAR LIBRARY (each entry = (W, V, its synth cmvn features)) = the agent's own
      production memory. Then the Phase-B gate: for a sample of REAL held-out SC speaker
      clips, find the nearest library exemplar by the agent's graph-resident DtwTo and
      report (1) COVERAGE/CORRECTNESS = fraction whose nearest synthetic exemplar is the
      SAME WORD (the static-library analysis-by-synthesis lower bound; chance 0.10);
      (2) the RESIDUAL distribution (are real clips near the synthetic manifold or
      orphaned?); (3) whether coverage SCALES with library size / V-diversity (sweep a
      couple of grid sizes).

NO LOOP. This is the de-risking gate: if the synthetic production memory COVERS real
speech (close, mostly-correct-word nearest exemplars), Phase C's adapt+iterate has a
sound manifold; if real clips are ORPHANED (far + wrong word, coverage near chance),
the V-space is too narrow / the world too synthetic and we widen BEFORE the loop.

DONKEY BOUNDARY (audited):
  · TTS = the WORLD/voicebox only — it generates the audio the agent hears; it is NEVER
    inverted in reasoning, NEVER part of a decision. synth() is pure world I/O.
  · V = derived from the AGENT'S OWN speaker knowledge (VTL scale from speaker_norm,
    pitch/f0, rate) — not arbitrary TTS flags; the variant pool just realises distinct
    vocal tracts on-manifold.
  · The EXEMPLAR LIBRARY = the agent's babble outputs (its production memory), the
    cmvn cochleagram features the agent's own front end produces (learned_voice_shape /
    agent_frontend), keyed by (W, V).
  · MATCHING = the agent's graph-resident DtwTo (the SAME Term reused UNCHANGED from
    scripts/dtw_trajectory_loso), evaluated natively in Rust. No net, no fit, no weight.
  · Held-out REAL speakers are NEVER banked; their labels score only; LOSO ungameable.

Run: python -m scripts.universal_loop_phaseAB \
        [n_held_spk] [n_real_per_word] [rate_seed]
"""
from __future__ import annotations

import os
import sys
import math
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

# the agent's UNCHANGED graph-resident DtwTo recognizer Term + trajectory plumbing.
from scripts.dtw_trajectory_loso import (
    _Pred, _V, _Lit, _Attr, _Nb, _DtwTo, _MinOver, _Argmin, _traj_tuple,
    QUERY_NODE_TYPE, QUERY_TRAJ_ATTR, EX_TRAJ_ATTR)

FS = W._TARGET_FS
_CELL = "digit|sc|en"
_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine"]


# ===========================================================================
# A — THE CONTROLLABLE VOICEBOX  synth(W, V)
# ===========================================================================
# V is a voice/speaker parameter set the agent derives from its OWN speaker_norm/VTL
# knowledge: vocal-tract-length scale (VTL — shifts all formants on the log-band axis,
# the speaker_norm lever), pitch/f0, and speaking rate. We realise V over the espeak-ng
# named variants (distinct vocal tracts) crossed with a pitch grid and a rate grid. The
# TTS is the WORLD; the agent controls these knobs and hears the output.

def _espeak_variants():
    """The named voice variants espeak-ng ships (en+<variant>) — the cheap diverse
    vocal-tract pool. Mechanical parse of `espeak-ng --voices=variant`. Pure world I/O."""
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


def build_voice_space(n_voices, seed=0):
    """Derive the V-space from the agent's OWN speaker knowledge: each voice V is a
    (vocal-tract variant, pitch f0, rate) tuple. VTL (vocal-tract length) is the
    speaker_norm lever (it shifts ALL formants — the α·F_i scaling); pitch is f0; rate
    is speaking speed (talker-difficulty axis). We span the espeak variant pool (distinct
    vocal tracts) x a pitch grid x a rate grid, sampled diversely, to get n_voices
    distinct ON-MANIFOLD speakers. Returns a list of voice dicts. World-adapter setup."""
    rng = random.Random(seed)
    variants = _espeak_variants()
    if not variants:
        return []
    pitch_grid = [20, 40, 60, 80, 99]                  # f0 spread (espeak pitch 0..99)
    rate_grid = [130, 160, 190]                        # words/min — the rate axis
    combos = [(v, p, r) for v in variants for p in pitch_grid for r in rate_grid]
    rng.shuffle(combos)
    voices = []
    for v, p, r in combos[:n_voices]:
        voices.append({"id": f"{v}@p{p}r{r}", "variant": v, "pitch": p, "rate": r})
    return voices


def synth(word, voice):
    """THE VOICEBOX: synth(word W, voice V) -> cmvn cochleagram features (the ordered
    per-frame residual trajectory the agent's recognizer reads). The agent controls the
    TTS knobs derived from its VTL/pitch/rate knowledge; the world voices `word` in that
    voice, resampled to 8 kHz mono (matching SC + the cochlea), and the agent's OWN front
    end (learned_voice_shape.residual_track, empty library = CMVN) turns the heard audio
    into features. Pure world I/O + the agent's own feature derivation; NO net in the
    decision, the TTS is never inverted."""
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "r.wav")
        out = os.path.join(d, "o.wav")
        subprocess.run(["espeak-ng", "-v", f"en+{voice['variant']}",
                        "-p", str(voice["pitch"]), "-s", str(voice["rate"]),
                        "-w", raw, word], check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                        "-ar", str(FS), "-ac", "1", "-sample_fmt", "s16", out],
                       check=True, capture_output=True)
        with wave.open(out, "rb") as wv:
            x = (np.frombuffer(wv.readframes(wv.getnframes()), dtype=np.int16)
                 .astype(np.float64) / 32768.0)
    if x.size == 0:
        return None
    # the agent's OWN front end produces the cmvn feature trajectory (empty library ->
    # per-utterance CMVN, the SAME residual the DtwTo recognizer reads on real clips).
    return LVS.residual_track(x, FS, [])


# ===========================================================================
# B — PRODUCTION MEMORY (the exemplar library) + the COVERAGE TEST
# ===========================================================================

def babble_library(s, voices, words=_DIGITS):
    """BABBLE the full (W,V) grid -> the EXEMPLAR LIBRARY = the agent's production
    memory. Each entry = (W, V, its synth cmvn features), stored as an Exemplar node
    (hung off the cell's word Concept via has_exemplar) with the `traj` attr the DtwTo
    recognizer reads + a `name` attr = the word. The library lives in the graph; the
    agent's recognizer ranges over it. Returns the count of exemplars written. Owned:
    the features are the agent's own front end; the TTS is the world the agent spoke
    through."""
    n = 0
    for w in words:
        # the cell's word Concept (install_cell registered the grammar for these);
        # mark is_word so the Argmin ranges over it, name=word for the readout.
        cid = W._word_concept(s, w, _CELL)
        s.set_attr(cid, "name", w)
        s.set_attr(cid, "is_word", 1.0)
        for v in voices:
            feats = synth(w, v)
            if not feats:
                continue
            ex = s.add_node("Exemplar", {"word": w, "name": w, "voice": v["id"],
                                         "cell_key": _CELL,
                                         "origin": "production_memory"})
            s.set_attr(ex, EX_TRAJ_ATTR, _traj_tuple(feats))
            s.add_edge(cid, "has_exemplar", ex)
            n += 1
    return n


def nearest_term():
    """The agent's graph-resident NEAREST-EXEMPLAR decision over the production memory,
    composed from owned ops (the SAME DtwTo / MinOver / Argmin reused from
    dtw_trajectory_loso). predict(query) = Argmin over is_word Concepts w of
    (MinOver e in has_exemplar(w) of DtwTo(query_traj, traj(e))). Evaluated natively."""
    word_dist = _MinOver(_Nb(_V("w"), "has_exemplar"), "e",
                         _DtwTo(_Attr(_V("q"), QUERY_TRAJ_ATTR),
                                _Attr(_V("e"), EX_TRAJ_ATTR)))
    is_word = {"type": "NodesWhere", "node_type": "Concept",
               "attr_key": "is_word", "value": _Lit(1.0)}
    return _Argmin(is_word, "w", word_dist)


def min_residual_term():
    """The agent's MIN nearest-exemplar DTW distance to the query over the WHOLE library
    (regardless of word) — the residual = how close the real clip is to the synthetic
    manifold. MinOver e in (all production-memory exemplars) of DtwTo(query, traj(e))."""
    allex = {"type": "NodesWhere", "node_type": "Exemplar",
             "attr_key": "origin", "value": _Lit("production_memory")}
    return _MinOver(allex, "e",
                    _DtwTo(_Attr(_V("q"), QUERY_TRAJ_ATTR),
                           _Attr(_V("e"), EX_TRAJ_ATTR)))


def coverage_test(s, real_probe):
    """THE PHASE-B GATE. For each REAL held-out clip: extract the agent's cmvn feature
    trajectory, write it on a query node, and via the agent's OWN DtwTo evaluate (1) the
    nearest-exemplar WORD (Argmin term) and (2) the min residual distance to the whole
    library. Returns (correct/total, [residuals], [is_correct per clip]). Held-out real
    speakers never banked; labels score only."""
    qn = s.add_node(QUERY_NODE_TYPE, {"origin": "coverage_probe"})
    pred_term = _Pred(nearest_term())
    resid_term = _Pred(min_residual_term())
    tot = cor = 0
    residuals = []
    correct_flags = []
    for w, x, fs in real_probe:
        feats = LVS.residual_track(np.asarray(x, dtype=np.float64), float(fs), [])
        s.set_attr(qn, QUERY_TRAJ_ATTR, _traj_tuple(feats))
        pred = s.evaluate(pred_term, {"q": qn})
        guess = s.node(pred)["attrs"].get("name") if pred is not None else None
        resid = s.evaluate(resid_term, {"q": qn})
        residuals.append(float(resid) if resid is not None else float("nan"))
        is_cor = int(guess == w)
        correct_flags.append(is_cor)
        tot += 1
        cor += is_cor
    s.remove_node(qn)
    return cor / max(tot, 1), residuals, correct_flags


# ---------------------------------------------------------------------------
# World-adapter mechanics: the REAL held-out SC probe (never banked).
# ---------------------------------------------------------------------------

def build_real_probe(n_held_spk, n_real_per_word, seed):
    """A sample of REAL held-out SC speaker clips (the coverage-test probe). Held-out
    speakers are disjoint from anything else; their clips are NEVER added to the library.
    Pure I/O."""
    words = W.sc_words()
    rng = random.Random(seed)
    speakers = W.sc_speakers(words)
    rng.shuffle(speakers)
    held_spk = speakers[:n_held_spk]
    held_idx = W.sc_index_for(held_spk, words)
    probe = []
    for w in words:
        paths = list(held_idx.get(w, []))
        rng.shuffle(paths)
        for p in paths[:n_real_per_word]:
            probe.append((w,) + W.load_sc_clip(p))
    return probe, words


def fresh():
    """A fresh substrate with the speech world + the digit|sc|en cell (which registers
    the Concept/Exemplar/has_exemplar/is_word grammar the production memory uses). The
    DtwTo recognizer reads trajectories directly, so no front-end cue gating is needed.
    World-adapter construction."""
    W.reset_caches()
    s = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=FS))
    pipe.attach(s)
    pipe._ensure_audio_pipeline(s)
    W.install_speech_world_rules(s)
    W.install_cell(s, "digit", "sc", "en")
    return s, pipe


def _dist_summary(vals, label):
    a = np.asarray([v for v in vals if not math.isnan(v)], dtype=np.float64)
    if a.size == 0:
        return f"  {label}: (no data)"
    qs = np.percentile(a, [10, 25, 50, 75, 90])
    return (f"  {label}: n={a.size} mean={a.mean():.3f} sd={a.std():.3f} "
            f"min={a.min():.3f} p10={qs[0]:.3f} p25={qs[1]:.3f} med={qs[2]:.3f} "
            f"p75={qs[3]:.3f} p90={qs[4]:.3f} max={a.max():.3f}")


def run_grid(grid_size, real_probe, words, seed):
    """Babble a (W,V) grid of `grid_size` voices into the production memory, then run
    the coverage test. Returns (n_exemplars, n_voices, coverage, residuals, flags)."""
    voices = build_voice_space(grid_size, seed=seed)
    s, _p = fresh()
    n_ex = babble_library(s, voices, words)
    cov, resid, flags = coverage_test(s, real_probe)
    # residual of CORRECT-word clips vs WRONG-word clips (is the manifold orphaning the
    # wrong ones, or is everything just far?).
    resid = np.asarray(resid, dtype=np.float64)
    flags = np.asarray(flags, dtype=np.int64)
    return {
        "n_voices": len(voices), "n_ex": n_ex, "coverage": cov,
        "resid": resid, "flags": flags,
        "resid_correct": resid[flags == 1], "resid_wrong": resid[flags == 0],
    }


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_held_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    n_real_per_word = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20240610

    chance = 1.0 / len(_DIGITS)
    variants = _espeak_variants()
    print(f"[config] held_spk={n_held_spk} real_per_word={n_real_per_word} seed={seed}",
          flush=True)
    print(f"[voicebox] espeak-ng named vocal-tract variants available: {len(variants)} "
          f"(V = variant x pitch x rate, derived from VTL/pitch/rate knowledge)",
          flush=True)

    # ---- A: prove synth(W,V) works (a quick sanity voicing) ----
    vsmall = build_voice_space(2, seed=seed)
    demo = synth("five", vsmall[0]) if vsmall else None
    print(f"[A] synth(W,V) voicebox wired: synth('five', {vsmall[0]['id'] if vsmall else '?'}) "
          f"-> {len(demo) if demo else 0} cmvn frames "
          f"x {len(demo[0]) if demo else 0} bands", flush=True)

    # ---- the REAL held-out probe (never banked) ----
    real_probe, words = build_real_probe(n_held_spk, n_real_per_word, seed)
    print(f"[probe] {len(real_probe)} REAL held-out SC clips ({len(words)} words, "
          f"{n_held_spk} held-out speakers, NEVER banked)", flush=True)

    # ---- B: sweep a couple of grid sizes (does coverage scale with V-diversity?) ----
    grid_sizes = [10, 30, 60]
    print(f"\n[B] babbling the (W,V) grid -> production memory, then the COVERAGE TEST "
          f"(nearest synthetic exemplar by the agent's DtwTo). grids={grid_sizes}",
          flush=True)
    results = []
    for gs in grid_sizes:
        r = run_grid(gs, real_probe, words, seed)
        results.append(r)
        print(f"\n[grid V={r['n_voices']:3d}] exemplars={r['n_ex']:4d}  "
              f"COVERAGE/CORRECTNESS {r['coverage']:.3f}  (chance {chance:.3f})",
              flush=True)
        print(_dist_summary(r["resid"], "residual (nearest-exemplar DTW dist), ALL"),
              flush=True)
        print(_dist_summary(r["resid_correct"], "residual, CORRECT-word clips "), flush=True)
        print(_dist_summary(r["resid_wrong"],   "residual, WRONG-word clips   "), flush=True)

    # ===================================================================
    # REPORT
    # ===================================================================
    print("\n" + "=" * 78, flush=True)
    print("UNIVERSAL CLOSED LOOP — PHASE A+B — synth(W,V) voicebox + production memory",
          flush=True)
    print("=" * 78, flush=True)
    print(f"  {'V-grid':>7s} {'exemplars':>10s} {'coverage':>9s} {'med-resid':>10s} "
          f"{'resid wrong-correct':>20s}", flush=True)
    for r in results:
        rc = r["resid_correct"]; rw = r["resid_wrong"]
        med = np.nanmedian(r["resid"]) if r["resid"].size else float("nan")
        gap = ((np.nanmedian(rw) if rw.size else float("nan")) -
               (np.nanmedian(rc) if rc.size else float("nan")))
        print(f"  {r['n_voices']:7d} {r['n_ex']:10d} {r['coverage']:9.3f} "
              f"{med:10.3f} {gap:20.3f}", flush=True)
    print("-" * 78, flush=True)
    print(f"  chance {chance:.3f}", flush=True)

    best = max(results, key=lambda r: r["coverage"])
    cov = best["coverage"]
    scales = results[-1]["coverage"] - results[0]["coverage"]
    rc = best["resid_correct"]; rw = best["resid_wrong"]
    med_all = float(np.nanmedian(best["resid"])) if best["resid"].size else float("nan")
    med_c = float(np.nanmedian(rc)) if rc.size else float("nan")
    med_w = float(np.nanmedian(rw)) if rw.size else float("nan")

    print(f"  best coverage {cov:.3f} at V={best['n_voices']} "
          f"({best['n_ex']} exemplars); coverage scaling (V={grid_sizes[0]}->"
          f"{grid_sizes[-1]}): {scales:+.3f}", flush=True)
    print(f"  residual: median(all)={med_all:.3f}  median(correct-word)={med_c:.3f}  "
          f"median(wrong-word)={med_w:.3f}  (wrong should be FARTHER if on-manifold)",
          flush=True)

    # ---- VERDICT (the Phase-B gate) ----
    above_chance = cov - chance
    orphaned = (med_c >= med_w - 1e-6)         # correct not closer than wrong = orphaned
    print("-" * 78, flush=True)
    if above_chance > 0.10 and not orphaned:
        verdict = (f"GO: real held-out clips have CLOSE, mostly-correct-word nearest "
                   f"synthetic exemplars — coverage {cov:.3f} is {above_chance:+.3f} "
                   f"above chance ({chance:.3f}) and correct-word clips sit CLOSER to "
                   f"the synthetic manifold (median {med_c:.3f}) than wrong-word ones "
                   f"({med_w:.3f}). The synthetic production memory COVERS real speech; "
                   f"Phase C's adapt+iterate has a sound manifold to refine on. BUILD C.")
    elif above_chance > 0.05:
        verdict = (f"GO (weak): coverage {cov:.3f} is {above_chance:+.3f} above chance "
                   f"({chance:.3f}) — the static library reaches real speech above "
                   f"chance, though the margin is modest (correct-word median {med_c:.3f} "
                   f"vs wrong {med_w:.3f}). The manifold is reachable; Phase C's "
                   f"adaptation is exactly what should close the residual. Proceed to C, "
                   f"instrumenting residual-vs-pass convergence.")
    else:
        verdict = (f"REVISIT: real held-out clips are ORPHANED — coverage {cov:.3f} is "
                   f"only {above_chance:+.3f} above chance ({chance:.3f}) and the nearest "
                   f"synthetic exemplar is {'no closer for correct words' if orphaned else 'far'} "
                   f"(correct median {med_c:.3f} vs wrong {med_w:.3f}). The V-space is too "
                   f"narrow or the espeak TTS world too synthetic to cover real speakers. "
                   f"WIDEN V (more vocal tracts / a richer generator — e.g. Piper neural "
                   f"voices) BEFORE spending on Phase C. Do not rescue.")
    print(f"  VERDICT: {verdict}", flush=True)
    print(f"  NOTE: Phase A+B only — NO loop. This is the de-risking gate confirming the "
          f"forward model + production memory are on-manifold before the expensive "
          f"Phase-C analysis-by-synthesis loop.", flush=True)
    print("[MARKER] UNIVERSAL_LOOP_PHASEAB_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
