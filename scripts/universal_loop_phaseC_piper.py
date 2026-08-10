"""universal_loop_phaseC_piper — Phase C re-run with PIPER (neural TTS) as the voicebox,
the LOOP UNCHANGED.

Phase C (espeak, commit 3d724209) PLATEAUED at cross-speaker LOSO 0.420 < CMVN 0.570 and a
forward-model-floor diagnostic PINNED the cause as (a) the FORWARD MODEL: espeak too coarse
— the true-word best-adapted residual (0.442) was NOT below the best wrong-word (0.441),
separation -0.021 NEGATIVE (the synthetic-vs-real gap larger than the between-word
distance). The pre-written lever is a RICHER GENERATOR.

This script swaps ONLY the synth backend (espeak -> Piper neural vocoder) and re-runs the
SAME loop logic — coarse-match / adapt-V coordinate-descent / order-N iterate / argmin —
imported UNCHANGED from scripts.universal_loop_phaseC. The swap is done by rebinding the
`synth` + `build_voice_space` symbols inside the phaseC module namespace to the Piper
voicebox (scripts.universal_loop_phaseAB_piper). Nothing in the loop is edited.

It runs the make-or-break FLOOR DIAGNOSTIC (true-word vs best-wrong adapted-residual
separation) and the LOSO table (CMVN / Piper-static / Piper-loop) to completion, with a
PRE-SYNTHESISED grid (Piper synths cached offline; the loop's adapt re-synthesises live
only the small adapted neighbourhood). Held-out REAL speakers NEVER banked; LOSO ungameable.

MUST run with the project .venv python (Piper lives there, NOT system python).

Run: .venv/bin/python -m scripts.universal_loop_phaseC_piper [n_held_spk] [n_loso_per_word] [grid] [seed]
Env: PHASEC_MAX_SYNTHS, PHASEC_PASSES, PHASEC_K (loop budget); PHASEC_DIAG_N (floor-diag clips).
"""
from __future__ import annotations

import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

# --- the UNCHANGED loop module; we swap its world (synth/build_voice_space) below ---
import scripts.universal_loop_phaseC as pc

# the Piper voicebox swap-in — SAME synth(W,V) signature + voice-dict shape the loop uses.
from scripts.universal_loop_phaseAB_piper import (
    synth as piper_synth, build_voice_space as piper_build_voice_space,
    piper_variants, piper_models_present, _piper_available)

# reuse the runner pieces from the espeak phaseC: library build, the two-regime runner,
# the CMVN baseline, the per-word subsample, the curve formatter — ALL unchanged. They
# call the module-level `synth`/`build_voice_space`, which we rebind to Piper.
from scripts.universal_loop_phaseC import (
    build_library, run_static_and_loop, run_cmvn_baseline, _subsample_per_word,
    _curve_str, h_trajectory, static_match, _residual_term, Loop)
from scripts.universal_loop_phaseAB import _DIGITS, fresh as ab_fresh
from scripts.dtw_trajectory_loso import (
    QUERY_TRAJ_ATTR, EX_TRAJ_ATTR, _traj_tuple)
from scripts.sc_loso_frontend_norm import build_split
import domains.self_directed_speech_world as W


def _swap_in_piper():
    """THE ONLY SWAP: rebind the world (synth + build_voice_space) inside the phaseC module
    namespace to Piper. The loop logic (Loop.recognise/adapt_v/coarse_topk, build_library,
    run_static_and_loop) calls these module-level symbols — so after this rebind the
    UNCHANGED loop runs on the neural mouth. No loop code is edited."""
    pc.synth = piper_synth
    pc.build_voice_space = piper_build_voice_space


# ===========================================================================
# The make-or-break FLOOR DIAGNOSTIC (the direct test), Piper edition.
# Mirrors /tmp/phaseC_diag.py from the espeak run: for each REAL LOSO clip, FULL-adapt V
# at EVERY word (no top-k pruning, k = all words, wide budget) and compare the best-adapted
# residual at the TRUE word vs the best WRONG word. Separation = (wrong - true): >0 means
# Piper renders the real talker well enough that the true word reachably wins.
# ===========================================================================

def floor_diagnostic(library, voices, cache, loso_probe, k_all, budget):
    """The absolute ceiling the inversion could ever reach + the separation signal."""
    s, _p = ab_fresh()
    variants = piper_variants()
    loop = Loop(s, variants, max_synths_per_word=budget, n_passes=1, k=k_all,
                synth_cache=cache)

    coarse_correct = full_correct = tot = 0
    true_resids, wrong_resids = [], []
    t0 = time.time()
    for i, (w, x, fs) in enumerate(loso_probe):
        h = h_trajectory(x, fs)
        # coarse argmin over the whole library (no adapt) — the static readout.
        loop.s.set_attr(loop.qn, QUERY_TRAJ_ATTR, h)
        best_per_word_coarse = {}
        seed_voice = {}
        for (ww, voice, feats) in library:
            loop.s.set_attr(loop.cn, EX_TRAJ_ATTR, _traj_tuple(feats))
            d = loop.s.evaluate(loop.resid_term, {"q": loop.qn, "c": loop.cn})
            d = float(d) if d is not None else float("inf")
            cur = best_per_word_coarse.get(ww)
            if cur is None or d < cur:
                best_per_word_coarse[ww] = d
                seed_voice[ww] = voice
        coarse_word = min(best_per_word_coarse.items(), key=lambda kv: kv[1])[0]
        coarse_correct += int(coarse_word == w)

        # FULL adapt at EVERY word (no pruning) — the perfect-convergence ceiling.
        per_word_adapt = {}
        for ww in best_per_word_coarse:
            v0 = seed_voice[ww]
            r, _v, _curve, _u = loop.adapt_v(h, ww, v0, budget)
            per_word_adapt[ww] = r
        full_word = min(per_word_adapt.items(), key=lambda kv: kv[1])[0]
        full_correct += int(full_word == w)
        tot += 1
        if w in per_word_adapt:
            true_resids.append(per_word_adapt[w])
        wrong = [r for ww, r in per_word_adapt.items() if ww != w]
        if wrong:
            wrong_resids.append(min(wrong))
        if (i + 1) % 10 == 0:
            el = time.time() - t0
            print(f"    [diag] {i+1}/{len(loso_probe)}  coarse {coarse_correct/(i+1):.3f} "
                  f"full {full_correct/(i+1):.3f}  synths {loop.n_synths}  {el:.1f}s",
                  flush=True)
    loop.close()
    tr = np.asarray(true_resids); wr = np.asarray(wrong_resids)
    n = min(tr.size, wr.size)
    frac = float(np.mean(tr[:n] < wr[:n])) if n else float("nan")
    return {
        "coarse_acc": coarse_correct / max(tot, 1),
        "full_acc": full_correct / max(tot, 1),
        "true_med": float(np.median(tr)) if tr.size else float("nan"),
        "wrong_med": float(np.median(wr)) if wr.size else float("nan"),
        "sep": (float(np.median(wr)) - float(np.median(tr)))
                if (tr.size and wr.size) else float("nan"),
        "frac_true_lt_wrong": frac, "n": tot, "synths": loop.n_synths,
    }


def main():
    if not _piper_available():
        print("[ABORT] Piper not importable or no voice models present — STOPPING. "
              "No silent espeak fallback (that was the prior run's error).", flush=True)
        print("[MARKER] UNIVERSAL_LOOP_PHASEC_PIPER_ABORT_NO_PIPER", flush=True)
        return
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return

    _swap_in_piper()

    n_held_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    n_loso_per = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    grid = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20240610
    max_synths = int(os.environ.get("PHASEC_MAX_SYNTHS", "12"))
    n_passes = int(os.environ.get("PHASEC_PASSES", "3"))
    k = int(os.environ.get("PHASEC_K", "5"))
    diag_n = int(os.environ.get("PHASEC_DIAG_N", "60"))

    chance = 1.0 / len(_DIGITS)
    t_start = time.time()
    models = piper_models_present()
    print(f"[config] held_spk={n_held_spk} loso_per_word={n_loso_per} grid={grid} "
          f"seed={seed} | max_synths/word={max_synths} passes={n_passes} k={k}",
          flush=True)
    print(f"[voicebox] PIPER neural models present: {len(models)} {models} "
          f"(V = model-timbre x rate(length_scale) x pitch(noise_w); single-speaker each "
          f"-- diversity from neural timbre + continuous prosody, NOT count)", flush=True)

    # ---- donkey-audit voicing: prove Piper synth(W,V) works on-manifold ----
    vsmall = piper_build_voice_space(2, seed=seed)
    demo = piper_synth("five", vsmall[0]) if vsmall else None
    print(f"[A] Piper synth(W,V) wired: synth('five', {vsmall[0]['id'] if vsmall else '?'}) "
          f"-> {len(demo) if demo else 0} cmvn frames x "
          f"{len(demo[0]) if demo else 0} bands", flush=True)
    if not demo:
        print("[ABORT] Piper synth returned no features — STOPPING (no espeak fallback).",
              flush=True)
        print("[MARKER] UNIVERSAL_LOOP_PHASEC_PIPER_ABORT_NO_SYNTH", flush=True)
        return

    # ---- the SAME robust SC LOSO split the yardstick uses ----
    train_clips, seen_probe, loso_probe = build_split(120, n_held_spk, 20, seed=seed)
    seen_probe = _subsample_per_word(seen_probe, min(8, n_loso_per), seed)
    loso_probe = _subsample_per_word(loso_probe, n_loso_per, seed)
    print(f"[probe] subsampled: {len(seen_probe)} seen-speaker, {len(loso_probe)} "
          f"cross-speaker LOSO (held-out, NEVER banked)", flush=True)

    # ---- CMVN 0.570 baseline (the wall) ----
    print("\n[baseline] CMVN (the agent's blind_guess on the cmvn front end) ...",
          flush=True)
    cmvn_seen, cmvn_loso = run_cmvn_baseline(train_clips, seen_probe, loso_probe)
    print(f"[CMVN] seen {cmvn_seen:.3f}  cross-speaker LOSO {cmvn_loso:.3f}  "
          f"gap {cmvn_seen - cmvn_loso:+.3f}  (the wall; canonical 0.570)", flush=True)

    # ---- PRE-SYNTHESISE the Piper (W,V) grid offline into the library (compute mgmt) ----
    print(f"\n[library] PRE-SYNTHESISING the Piper (W,V) grid (V={grid}) -> production "
          f"memory (offline; the loop adapts over this grid + small live re-synth) ...",
          flush=True)
    tb = time.time()
    library, voices, cache = build_library(grid, seed)
    print(f"[library] {len(library)} Piper exemplars over {len(voices)} voices "
          f"({len(cache)} synths, {time.time()-tb:.1f}s)", flush=True)

    # ===================================================================
    # (1) THE FLOOR DIAGNOSTIC — the make-or-break separation signal (Piper).
    # ===================================================================
    diag_probe = _subsample_per_word(loso_probe, max(1, diag_n // len(_DIGITS)), seed)
    print(f"\n[diagnostic] FLOOR DIAGNOSTIC (Piper): FULL adapt at EVERY word, k=all, "
          f"budget={max_synths}, on {len(diag_probe)} LOSO clips -> true-vs-wrong "
          f"separation ...", flush=True)
    diag = floor_diagnostic(library, voices, cache, diag_probe, k_all=len(_DIGITS),
                            budget=max_synths)
    print(f"[diagnostic] coarse argmin (no adapt) acc {diag['coarse_acc']:.3f} | "
          f"FULL-adapt-every-word ceiling {diag['full_acc']:.3f}", flush=True)
    print(f"[diagnostic] TRUE-word adapted residual median {diag['true_med']:.3f}  vs  "
          f"best WRONG-word median {diag['wrong_med']:.3f}", flush=True)
    print(f"[diagnostic] SEPARATION (wrong-true) {diag['sep']:+.3f}  "
          f"frac(true<wrong) {diag['frac_true_lt_wrong']:.3f}  (n={diag['n']}, "
          f"{diag['synths']} synths)  <<< MAKE-OR-BREAK: >0 = Piper renders the talker "
          f"well enough for the true word to reachably win", flush=True)

    # ===================================================================
    # (2) STATIC + LOOP on the SAME probes (the LOSO table), loop UNCHANGED.
    # ===================================================================
    print(f"\n[phaseC] static lower bound + the analysis-by-synthesis LOOP (Piper, "
          f"loop UNCHANGED) ...", flush=True)
    R = run_static_and_loop(library, voices, cache, seen_probe, loso_probe,
                            max_synths, n_passes, k)
    ls = R["loop_seen"]; ll = R["loop_loso"]

    # ===================================================================
    # REPORT
    # ===================================================================
    print("\n" + "=" * 78, flush=True)
    print("UNIVERSAL CLOSED LOOP — PHASE C (PIPER) — analysis-by-synthesis LOOP (SC LOSO)",
          flush=True)
    print("=" * 78, flush=True)
    print(f"  {'regime':24s} {'seen':>8s} {'LOSO':>8s} {'gap':>8s}", flush=True)
    print(f"  {'CMVN (the wall)':24s} {cmvn_seen:8.3f} {cmvn_loso:8.3f} "
          f"{cmvn_seen - cmvn_loso:8.3f}", flush=True)
    print(f"  {'espeak-static (prior)':24s} {'   -   ':>8s} {0.400:8.3f} {'   -   ':>8s}",
          flush=True)
    print(f"  {'espeak-loop (prior)':24s} {'   -   ':>8s} {0.420:8.3f} {'   -   ':>8s}",
          flush=True)
    print(f"  {'PIPER-static (floor)':24s} {R['static_seen']:8.3f} {R['static_loso']:8.3f} "
          f"{R['static_seen'] - R['static_loso']:8.3f}", flush=True)
    print(f"  {'PIPER-LOOP':24s} {ls['acc']:8.3f} {ll['acc']:8.3f} "
          f"{ls['acc'] - ll['acc']:8.3f}", flush=True)
    print("-" * 78, flush=True)
    print(f"  chance {chance:.3f} | CMVN target 0.570 (canonical) / {cmvn_loso:.3f} "
          f"(this split)", flush=True)
    gap_vs_cmvn = ll["acc"] - cmvn_loso
    gap_vs_static = ll["acc"] - R["static_loso"]
    gap_vs_espeak = ll["acc"] - 0.420
    print(f"  PIPER-LOOP vs CMVN (this split):   {gap_vs_cmvn:+.3f} "
          f"(CMVN {cmvn_loso:.3f} -> LOOP {ll['acc']:.3f})", flush=True)
    print(f"  PIPER-LOOP vs PIPER-STATIC floor:  {gap_vs_static:+.3f}", flush=True)
    print(f"  PIPER-LOOP vs espeak-LOOP (0.420): {gap_vs_espeak:+.3f}", flush=True)
    print(f"  loop compute: {ll['synths_per_probe']:.1f} synths/probe (LOSO), "
          f"{R['total_synths']} total world calls", flush=True)

    # convergence curves
    print("\n  [convergence] residual-vs-adapt-step for the winning word "
          "(first LOSO probes):", flush=True)
    for (true_w, pred_w, curve) in ll["curves"][:8]:
        mark = "OK " if pred_w == true_w else "x  "
        drop = (curve[0] - curve[-1]) if len(curve) >= 2 else 0.0
        print(f"    {mark}true={true_w:6s} pred={pred_w if pred_w else '-':6s}  "
              f"resid {_curve_str(curve)}  (drop {drop:+.3f})", flush=True)

    # the loop's own top-k-pruned diagnostic (for parity with espeak report)
    tr = ll["true_resid"]; wr = ll["wrong_resid"]
    tr_med = float(np.median(tr)) if tr.size else float("nan")
    wr_med = float(np.median(wr)) if wr.size else float("nan")
    print(f"\n  [loop-diag] min adapted residual (top-k pruned): TRUE median {tr_med:.3f} "
          f"(n={tr.size})  vs best WRONG median {wr_med:.3f} (n={wr.size})  "
          f"sep {wr_med - tr_med:+.3f}", flush=True)

    # ===================================================================
    # VERDICT — wall-falls / lifts-but-caps / no-lift
    # ===================================================================
    print("-" * 78, flush=True)
    beat = max(0.570, cmvn_loso)
    sep_pos = (not np.isnan(diag["sep"])) and diag["sep"] > 1e-6
    beats_cmvn = ll["acc"] > beat + 1e-6
    beats_espeak = ll["acc"] > 0.420 + 1e-6
    if sep_pos and beats_cmvn:
        verdict = (f"WALL FALLS: Piper's floor separation is POSITIVE ({diag['sep']:+.3f}, "
                   f"frac true<wrong {diag['frac_true_lt_wrong']:.3f}) AND the UNCHANGED "
                   f"loop reaches cross-speaker LOSO {ll['acc']:.3f}, BEATING CMVN "
                   f"({cmvn_loso:.3f} this split / 0.570 canonical) by {ll['acc']-beat:+.3f}. "
                   f"The loop was right all along; espeak's mouth was the limit. The neural "
                   f"generator renders the real talker closely enough that the true word "
                   f"reachably wins — and factoring out the inferred speaker V clears the "
                   f"wall. The first number past the wall.")
    elif beats_espeak or sep_pos:
        verdict = (f"LIFTS-BUT-CAPS: Piper helped — LOSO {ll['acc']:.3f} "
                   f"(espeak-loop 0.420, {gap_vs_espeak:+.3f}); floor separation "
                   f"{diag['sep']:+.3f} (espeak -0.021) — but still < CMVN "
                   f"({cmvn_loso:.3f} this split / 0.570 canonical; {gap_vs_cmvn:+.3f}). "
                   f"Neural QUALITY moved the floor as predicted, but the few single-"
                   f"speaker Piper models cap V-COVERAGE: the inferred speaker can't be "
                   f"reached closely enough across all real talkers. NEXT LEVER: a "
                   f"MULTI-SPEAKER Piper model (vctk / libritts) to widen the timbre "
                   f"manifold. Do not rescue.")
    else:
        verdict = (f"NO-LIFT: Piper did NOT beat espeak (LOSO {ll['acc']:.3f} vs espeak-loop "
                   f"0.420, {gap_vs_espeak:+.3f}; floor separation {diag['sep']:+.3f} vs "
                   f"espeak -0.021). Neural quality was NOT the limit. The wall is not the "
                   f"forward model's timbre — REVISIT the diagnosis (feature front end / "
                   f"the DtwTo residual / the V-axis itself), not the mouth.")
    print(f"  VERDICT: {verdict}", flush=True)
    print(f"  [timing] total {time.time()-t_start:.0f}s", flush=True)
    print("[MARKER] UNIVERSAL_LOOP_PHASEC_PIPER_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
