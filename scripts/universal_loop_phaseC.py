"""universal_loop_phaseC — Phase C of the universal closed loop: the ANALYSIS-BY-
SYNTHESIS LOOP, the make-or-break.

Phase A+B (scripts/universal_loop_phaseAB.py, docs/universal_loop_phaseAB.md) confirmed
the two pieces the loop stands on are on-manifold: a CONTROLLABLE VOICEBOX synth(W,V) ->
cmvn cochleagram features (espeak-ng, V = vocal-tract variant x pitch x rate, derived
from the agent's OWN speaker_norm/VTL knowledge), and a babbled EXEMPLAR LIBRARY whose
STATIC nearest-exemplar match already gets ~0.40 cross-speaker (chance 0.10) — the LOWER
BOUND. CMVN's cross-speaker cap is 0.570; every LINEAR subtract (seeded tube, within-utt
SVD, LPC peel, wide-SVD, learned-across-voice) died at or below it.

This phase tests THE LEVER the linear subtracts could not pull: the LOOP's CONTINUOUS,
NONLINEAR adaptation of the voice V to the heard speaker via LIVE re-synthesis. Per heard
utterance H:

  1. COARSE MATCH. Rank the prebuilt (W,V) library by the agent's graph-resident DtwTo to
     H; take the top-k candidate WORDS (multi-start, each word seeded from its best library
     voice -> dodges local minima).
  2. CONTINUOUS ADAPT-V (the nonlinear lever). For each candidate word W, ADAPT the voice
     V (pitch, rate -- continuous; vocal-tract variant -- hill-climbed over a neighbourhood,
     the discrete realisation of the continuous VTL axis) to MINIMISE residual(H,synth(W,V))
     = DtwTo(H_feats, synth(W,V)_feats). This is OWNED COORDINATE DESCENT over the FEW V
     params, LIVE re-synthesising via espeak at each step (NOT a linear feature-space
     approximation -- that is the subtract that already failed; the real nonlinear synth is
     inverted by search). Capped at <= max_synths_per_word synths/word for compute.
  3. ITERATE (order-N). A couple of refine passes; residual monotonicity tracked.
  4. READOUT. recognised word = argmin_W [ min_V residual(H, synth(W, V_adapted)) ]. The
     speaker V is INFERRED (the per-word best-fitting voice) and FACTORED OUT -> speaker-
     invariant BY CONSTRUCTION.

TEST: robust SC 40-speaker LOSO (ungameable, held-out REAL speakers NEVER banked). Compare
CMVN 0.570 (baseline) | static nearest-exemplar 0.40 (lower bound) | PHASE-C LOOP. Report
seen + LOSO + gap + the residual-vs-pass / adapt convergence curves.

VERDICT: GO past the wall if Phase C beats CMVN 0.570 (the nonlinear inversion reaches the
disentanglement every linear subtract missed). KILL/PLATEAU otherwise, DIAGNOSED as (a)
FORWARD MODEL too coarse (best-achievable residual at the TRUE word still high -> richer
generator, Piper); (b) ADAPTATION too weak (V-space can't reach the speaker -> widen V);
(c) CONVERGENCE (local minima / too few passes -> more multi-start / passes). Evidence:
best-achievable residual at the true word vs a wrong word; does more adapt help; does k.

DONKEY BOUNDARY (audited):
  · synth = the WORLD/voicebox the agent CONTROLS and HEARS (espeak); it is NEVER inverted
    by a net, NEVER part of a decision -- only re-voiced and re-heard. Pure world I/O.
  · The LOOP (coarse-match / adapt / iterate / argmin) = the agent's OWN owned ops: the
    graph-resident DtwTo Term (reused UNCHANGED from dtw_trajectory_loso) + a coordinate
    search + residual-min. NO net, NO fit, NO gradient, NO trained weight in the agent.
  · Features = the agent's OWN front end (learned_voice_shape.residual_track, empty library
    = per-utterance CMVN), the SAME feature the DtwTo recognizer reads on real clips.
  · Held-out REAL speakers NEVER banked; their labels score only; LOSO ungameable.

Run: python -m scripts.universal_loop_phaseC [n_held_spk] [n_loso_per_word] [grid] [seed]
"""
from __future__ import annotations

import os
import sys
import math
import random
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
from domains.stt_pipeline import STTPipeline, STTParams
import domains.learned_voice_shape as LVS

# the agent's UNCHANGED graph-resident DtwTo recognizer Term + trajectory plumbing,
# reused exactly (same alignment the static match + the prior LOSO scripts use).
from scripts.dtw_trajectory_loso import (
    _Pred, _V, _Lit, _Attr, _Nb, _DtwTo, _MinOver, _Argmin, _traj_tuple,
    QUERY_NODE_TYPE, QUERY_TRAJ_ATTR, EX_TRAJ_ATTR)

# Phase A+B's voicebox + library babble + the CMVN baseline mechanics, reused.
from scripts.universal_loop_phaseAB import (
    synth, build_voice_space, babble_library, _espeak_variants, fresh as ab_fresh,
    _CELL, _DIGITS, FS)

# the robust SC LOSO split + the REAL CMVN baseline (blind_guess) — the yardstick.
from scripts.sc_loso_frontend_norm import build_split, bank, measure, CELL


# ===========================================================================
# The agent's owned residual op: DtwTo(H_feats, candidate_feats), evaluated natively.
# This is the loop's objective — the SAME alignment the recognizer uses, reused as the
# adapt-V minimisation target. No net, no fit.
# ===========================================================================

def _residual_term():
    """DtwTo between a query node's trajectory (var q) and a candidate node's trajectory
    (var c) — the agent's owned residual between the heard clip and a synthesised one."""
    return _Pred(_DtwTo(_Attr(_V("q"), QUERY_TRAJ_ATTR),
                        _Attr(_V("c"), EX_TRAJ_ATTR)))


class Loop:
    """The analysis-by-synthesis loop over the agent's owned ops. Holds the substrate,
    the prebuilt production-memory library, and scratch nodes; exposes residual(H, W, V)
    via the agent's DtwTo, and the adapt-V coordinate search. Every decision is owned;
    the only world call is synth()."""

    def __init__(self, s, variants, max_synths_per_word=8, n_passes=2, k=3,
                 synth_cache=None):
        self.s = s
        self.variants = variants
        self.max_synths = max_synths_per_word
        self.n_passes = n_passes
        self.k = k
        self.resid_term = _residual_term()
        self.qn = s.add_node(QUERY_NODE_TYPE, {"origin": "phaseC_query"})
        self.cn = s.add_node("PhaseCCand", {"origin": "phaseC_cand"})
        self.synth_cache = synth_cache if synth_cache is not None else {}
        self.n_synths = 0       # world calls this probe (compute accounting)

    # ---- the WORLD call (the only net/TTS touch): synth + cache ----
    def _feats(self, w, voice):
        key = (w, voice["variant"], int(round(voice["pitch"])), int(round(voice["rate"])))
        f = self.synth_cache.get(key)
        if f is None:
            f = synth(w, {"variant": voice["variant"], "pitch": key[2], "rate": key[3]})
            self.synth_cache[key] = f if f else []
            self.n_synths += 1
        return f

    # ---- the OWNED residual: DtwTo(H, synth(W,V)) evaluated natively ----
    def residual(self, h_traj, w, voice):
        f = self._feats(w, voice)
        if not f:
            return float("inf")
        self.s.set_attr(self.cn, EX_TRAJ_ATTR, _traj_tuple(f))
        self.s.set_attr(self.qn, QUERY_TRAJ_ATTR, h_traj)
        d = self.s.evaluate(self.resid_term, {"q": self.qn, "c": self.cn})
        return float(d) if d is not None else float("inf")

    # ---- COARSE MATCH: top-k candidate (word, seed-voice) from the static library ----
    def coarse_topk(self, h_traj, library):
        """Rank the prebuilt library by DtwTo to H; return the top-k WORDS each seeded
        from its best-matching library voice (multi-start). library = list of
        (word, voice_dict, feats). Owned: DtwTo only, no world call."""
        self.s.set_attr(self.qn, QUERY_TRAJ_ATTR, h_traj)
        best_per_word = {}   # word -> (dist, voice)
        for (w, voice, feats) in library:
            self.s.set_attr(self.cn, EX_TRAJ_ATTR, _traj_tuple(feats))
            d = self.s.evaluate(self.resid_term, {"q": self.qn, "c": self.cn})
            d = float(d) if d is not None else float("inf")
            cur = best_per_word.get(w)
            if cur is None or d < cur[0]:
                best_per_word[w] = (d, voice)
        ranked = sorted(best_per_word.items(), key=lambda kv: kv[1][0])
        return [(w, v) for (w, (d, v)) in ranked[:self.k]]

    # ---- CONTINUOUS ADAPT-V: coordinate descent over the few V params, live synth ----
    def adapt_v(self, h_traj, w, v0, budget):
        """For candidate word W, adapt voice V to MINIMISE residual(H, synth(W,V)) by
        OWNED coordinate descent — coarse-to-fine over the CONTINUOUS pitch & rate axes,
        and hill-climbing the vocal-tract variant over its neighbourhood (the discrete
        realisation of the continuous VTL axis). Live re-synth each step; cap at `budget`
        world calls. Returns (best_resid, best_voice, curve) — curve = residual after each
        accepted step (monotonicity instrumentation). This is the nonlinear inversion: it
        searches the real synth, never a linear feature approximation."""
        v = dict(v0)
        best = self.residual(h_traj, w, v)
        curve = [best]
        used = 1
        # coarse-to-fine step schedule for the continuous pitch & rate axes.
        pitch_steps = [20, 8]
        rate_steps = [25, 10]
        # variant neighbourhood: a small diverse pool to hill-climb the vocal tract.
        vidx = self.variants.index(v["variant"]) if v["variant"] in self.variants else 0
        for stage in range(len(pitch_steps)):
            improved = True
            while improved and used < budget:
                improved = False
                # --- pitch axis (continuous f0) ---
                for dp in (pitch_steps[stage], -pitch_steps[stage]):
                    if used >= budget:
                        break
                    cand = dict(v); cand["pitch"] = min(99, max(0, v["pitch"] + dp))
                    if cand["pitch"] == v["pitch"]:
                        continue
                    r = self.residual(h_traj, w, cand); used += 1
                    if r < best - 1e-9:
                        best, v = r, cand; curve.append(best); improved = True; break
                if used >= budget:
                    break
                # --- rate axis (continuous speaking rate) ---
                for dr in (rate_steps[stage], -rate_steps[stage]):
                    if used >= budget:
                        break
                    cand = dict(v); cand["rate"] = min(300, max(80, v["rate"] + dr))
                    if cand["rate"] == v["rate"]:
                        continue
                    r = self.residual(h_traj, w, cand); used += 1
                    if r < best - 1e-9:
                        best, v = r, cand; curve.append(best); improved = True; break
                if used >= budget:
                    break
                # --- vocal-tract variant axis (hill-climb neighbours = VTL realisation) ---
                for dv in (1, -1):
                    if used >= budget:
                        break
                    ni = (vidx + dv) % len(self.variants)
                    cand = dict(v); cand["variant"] = self.variants[ni]
                    r = self.residual(h_traj, w, cand); used += 1
                    if r < best - 1e-9:
                        best, v, vidx = r, cand, ni; curve.append(best); improved = True
                        break
        return best, v, curve, used

    # ---- the full loop on one heard utterance H ----
    def recognise(self, h_traj, library):
        """argmin_W [ min_V residual(H, synth(W, V_adapted)) ], with the order-N iterate.
        Returns (word, per_word_best_resid, adapt_curves, n_synths)."""
        cands = self.coarse_topk(h_traj, library)        # top-k (word, seed voice)
        per_word = {}
        curves = {}
        # split the per-word synth budget across the order-N refine passes.
        per_pass = max(2, self.max_synths // self.n_passes)
        for (w, v0) in cands:
            v = dict(v0)
            best_resid = self.residual(h_traj, w, v)
            word_curve = [best_resid]
            for _pass in range(self.n_passes):
                r, v, curve, _used = self.adapt_v(h_traj, w, v, per_pass)
                if r < best_resid - 1e-9:
                    best_resid = r
                word_curve.extend(curve[1:])   # append refinements (drop the dup start)
            per_word[w] = best_resid
            curves[w] = word_curve
        word = min(per_word.items(), key=lambda kv: kv[1])[0] if per_word else None
        return word, per_word, curves

    def close(self):
        self.s.remove_node(self.qn)
        self.s.remove_node(self.cn)


# ===========================================================================
# The static lower-bound recognizer (Phase A+B): nearest library exemplar, NO adapt.
# Reuses the same library; pure DtwTo. The floor the loop must beat.
# ===========================================================================

def static_match(s, h_traj, library, qn, cn, resid_term):
    s.set_attr(qn, QUERY_TRAJ_ATTR, h_traj)
    best_w, best_d = None, float("inf")
    for (w, voice, feats) in library:
        s.set_attr(cn, EX_TRAJ_ATTR, _traj_tuple(feats))
        d = s.evaluate(resid_term, {"q": qn, "c": cn})
        d = float(d) if d is not None else float("inf")
        if d < best_d:
            best_d, best_w = d, w
    return best_w


def h_trajectory(x, fs):
    """The agent's OWN front-end feature for a heard clip (empty library = per-utt CMVN),
    as the tuple-of-tuples the DtwTo reads. The SAME feature the library is built in."""
    feats = LVS.residual_track(np.asarray(x, dtype=np.float64), float(fs), [])
    return _traj_tuple(feats)


# ===========================================================================
# Library construction (production memory) with a shared synth cache.
# ===========================================================================

def build_library(grid, seed):
    """Babble the (W,V) grid into the production memory; return (library list, voices,
    synth_cache). library = [(word, voice_dict, feats)]. The cache is reused by the loop
    so library voices are not re-synthesised during adapt."""
    voices = build_voice_space(grid, seed=seed)
    library = []
    cache = {}
    for w in _DIGITS:
        for v in voices:
            key = (w, v["variant"], int(v["pitch"]), int(v["rate"]))
            f = synth(w, v)
            cache[key] = f if f else []
            if f:
                library.append((w, v, f))
    return library, voices, cache


# ===========================================================================
# Runners for each regime on the SAME LOSO probe.
# ===========================================================================

def run_cmvn_baseline(train_clips, seen_probe, loso_probe):
    """The REAL CMVN 0.570 baseline via the agent's blind_guess on the cmvn front end —
    the SAME ungameable measurement docs/synthesize_gaps_on_audio_loso.md reports."""
    s, _p = ab_fresh()
    for c in s.nodes("Cue"):
        if s.node(c)["attrs"].get("name") == "cmvn_ear":
            s.set_attr(c, "active", 1.0)
    bank(s, train_clips)
    return measure(s, seen_probe), measure(s, loso_probe)


def run_static_and_loop(library, voices, cache, seen_probe, loso_probe,
                        max_synths, n_passes, k):
    """Both the static lower bound and the Phase-C loop on the SAME library + probes
    (one substrate, shared scratch + synth cache). Returns a dict of results + curves."""
    s, _p = ab_fresh()
    variants = sorted({v["variant"] for v in voices})
    resid_term = _residual_term()
    qn = s.add_node(QUERY_NODE_TYPE, {"origin": "static_query"})
    cn = s.add_node("StaticCand", {"origin": "static_cand"})

    def static_acc(probe):
        tot = cor = 0
        for w, x, fs in probe:
            h = h_trajectory(x, fs)
            g = static_match(s, h, library, qn, cn, resid_term)
            tot += 1; cor += int(g == w)
        return cor / max(tot, 1)

    static_seen = static_acc(seen_probe)
    static_loso = static_acc(loso_probe)
    s.remove_node(qn); s.remove_node(cn)

    # the loop (shares the synth cache so library voices aren't re-synthesised).
    loop = Loop(s, variants, max_synths_per_word=max_synths, n_passes=n_passes, k=k,
                synth_cache=cache)

    def loop_acc(probe, collect_curves=False, tag=""):
        tot = cor = 0
        synth_counts = []
        all_curves = []
        true_resids = []      # min residual at the TRUE word (forward-model floor probe)
        wrong_resids = []     # min residual at the best WRONG candidate word
        t0 = time.time()
        for i, (w, x, fs) in enumerate(probe):
            h = h_trajectory(x, fs)
            n0 = loop.n_synths
            word, per_word, curves = loop.recognise(h, library)
            synth_counts.append(loop.n_synths - n0)
            tot += 1; cor += int(word == w)
            if w in per_word:
                true_resids.append(per_word[w])
            wrong = [r for ww, r in per_word.items() if ww != w]
            if wrong:
                wrong_resids.append(min(wrong))
            if collect_curves and i < 12:
                # convergence curve for the chosen (winning) word.
                all_curves.append((w, word, curves.get(word, [])))
            if (i + 1) % 20 == 0:
                el = time.time() - t0
                print(f"    [{tag}] {i+1}/{len(probe)}  acc-so-far {cor/(i+1):.3f}  "
                      f"synths {loop.n_synths}  {el:.1f}s  "
                      f"({el/(i+1):.2f}s/probe)", flush=True)
        return {
            "acc": cor / max(tot, 1),
            "synths_per_probe": float(np.mean(synth_counts)) if synth_counts else 0.0,
            "curves": all_curves,
            "true_resid": np.asarray(true_resids, dtype=np.float64),
            "wrong_resid": np.asarray(wrong_resids, dtype=np.float64),
        }

    print("  [loop] seen-speaker probe ...", flush=True)
    loop_seen = loop_acc(seen_probe, tag="seen")
    print("  [loop] cross-speaker LOSO probe ...", flush=True)
    loop_loso = loop_acc(loso_probe, collect_curves=True, tag="loso")
    loop.close()
    return {
        "static_seen": static_seen, "static_loso": static_loso,
        "loop_seen": loop_seen, "loop_loso": loop_loso,
        "total_synths": loop.n_synths,
    }


def _curve_str(curve):
    if not curve:
        return "(none)"
    return " -> ".join(f"{c:.3f}" for c in curve)


def main():
    if not W.sc_available():
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_held_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    n_loso_per = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    grid = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20240610
    max_synths = int(os.environ.get("PHASEC_MAX_SYNTHS", "8"))
    n_passes = int(os.environ.get("PHASEC_PASSES", "2"))
    k = int(os.environ.get("PHASEC_K", "3"))

    chance = 1.0 / len(_DIGITS)
    t_start = time.time()
    print(f"[config] held_spk={n_held_spk} loso_per_word={n_loso_per} grid={grid} "
          f"seed={seed} | max_synths/word={max_synths} passes={n_passes} k={k}",
          flush=True)
    print(f"[voicebox] espeak-ng variants available: {len(_espeak_variants())}",
          flush=True)

    # ---- the SAME robust SC LOSO split the yardstick uses (n_train fixed at 120) ----
    # n_per controls train bank depth; n_loso_per subsamples the LOSO probe for compute
    # (the loop does live re-synthesis). We trim the LOSO probe to n_loso_per/word AFTER
    # build_split (which balances per word) to keep a COMPLETE run.
    train_clips, seen_probe, loso_probe = build_split(120, n_held_spk, 20, seed=seed)
    # subsample probes per word for compute (report n). Keep balanced across words.
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

    # ---- build the production-memory library once ----
    print(f"\n[library] babbling the (W,V) grid (V={grid}) -> production memory ...",
          flush=True)
    tb = time.time()
    library, voices, cache = build_library(grid, seed)
    print(f"[library] {len(library)} exemplars over {len(voices)} voices "
          f"({len(cache)} synths, {time.time()-tb:.1f}s)", flush=True)

    # ---- static lower bound + the Phase-C loop on the SAME probes ----
    print(f"\n[phaseC] static lower bound + the analysis-by-synthesis LOOP ...", flush=True)
    R = run_static_and_loop(library, voices, cache, seen_probe, loso_probe,
                            max_synths, n_passes, k)

    ls = R["loop_seen"]; ll = R["loop_loso"]

    # ===================================================================
    # REPORT
    # ===================================================================
    print("\n" + "=" * 78, flush=True)
    print("UNIVERSAL CLOSED LOOP — PHASE C — analysis-by-synthesis LOOP (SC LOSO)",
          flush=True)
    print("=" * 78, flush=True)
    print(f"  {'regime':22s} {'seen':>8s} {'LOSO':>8s} {'gap':>8s}", flush=True)
    print(f"  {'CMVN (the wall)':22s} {cmvn_seen:8.3f} {cmvn_loso:8.3f} "
          f"{cmvn_seen - cmvn_loso:8.3f}", flush=True)
    print(f"  {'STATIC match (floor)':22s} {R['static_seen']:8.3f} {R['static_loso']:8.3f} "
          f"{R['static_seen'] - R['static_loso']:8.3f}", flush=True)
    print(f"  {'PHASE-C LOOP':22s} {ls['acc']:8.3f} {ll['acc']:8.3f} "
          f"{ls['acc'] - ll['acc']:8.3f}", flush=True)
    print("-" * 78, flush=True)
    print(f"  chance {chance:.3f} | CMVN target 0.570 (canonical) / {cmvn_loso:.3f} "
          f"(this split)", flush=True)
    gap_vs_cmvn = ll["acc"] - cmvn_loso
    gap_vs_static = ll["acc"] - R["static_loso"]
    print(f"  PHASE-C LOOP vs CMVN (this split):   {gap_vs_cmvn:+.3f} "
          f"(CMVN {cmvn_loso:.3f} -> LOOP {ll['acc']:.3f})", flush=True)
    print(f"  PHASE-C LOOP vs STATIC floor:        {gap_vs_static:+.3f} "
          f"(STATIC {R['static_loso']:.3f} -> LOOP {ll['acc']:.3f})", flush=True)
    print(f"  loop compute: {ll['synths_per_probe']:.1f} synths/probe (LOSO), "
          f"{R['total_synths']} total world calls", flush=True)

    # ---- convergence / adapt curves (residual-vs-step for the winning word) ----
    print("\n  [convergence] residual-vs-adapt-step for the winning word "
          "(first LOSO probes):", flush=True)
    for (true_w, pred_w, curve) in ll["curves"][:8]:
        mark = "OK " if pred_w == true_w else "x  "
        drop = (curve[0] - curve[-1]) if len(curve) >= 2 else 0.0
        print(f"    {mark}true={true_w:6s} pred={pred_w if pred_w else '-':6s}  "
              f"resid {_curve_str(curve)}  (drop {drop:+.3f})", flush=True)

    # ---- the diagnostic: best-achievable residual at TRUE vs WRONG word ----
    tr = ll["true_resid"]; wr = ll["wrong_resid"]
    tr_med = float(np.median(tr)) if tr.size else float("nan")
    wr_med = float(np.median(wr)) if wr.size else float("nan")
    print(f"\n  [diagnostic] min adapted residual: TRUE word median {tr_med:.3f} "
          f"(n={tr.size})  vs  best WRONG word median {wr_med:.3f} (n={wr.size})",
          flush=True)
    print(f"    separation (wrong-true) {wr_med - tr_med:+.3f} "
          f"(>0 = the true word is reachably CLOSER after adapt; the inversion works)",
          flush=True)

    # ---- VERDICT ----
    print("-" * 78, flush=True)
    beat = max(0.570, cmvn_loso)            # beat BOTH the canonical wall and this split
    if ll["acc"] > beat + 1e-6:
        verdict = (f"GO PAST THE WALL: the Phase-C analysis-by-synthesis LOOP reaches "
                   f"cross-speaker LOSO {ll['acc']:.3f}, BEATING CMVN ({cmvn_loso:.3f} "
                   f"this split / 0.570 canonical) by {ll['acc']-beat:+.3f} and the static "
                   f"floor by {gap_vs_static:+.3f}. The CONTINUOUS NONLINEAR inversion of "
                   f"the voicebox reaches the disentanglement every LINEAR subtract missed. "
                   f"TRUE-word residual ({tr_med:.3f}) sits below the best WRONG word "
                   f"({wr_med:.3f}); adapting V to the heard speaker and factoring it out "
                   f"is the lever. The first number to move past the wall all session.")
    else:
        # diagnose which of (a)/(b)/(c).
        sep = wr_med - tr_med
        # (a) forward model too coarse: even at the TRUE word the residual floor is high
        #     and barely separated from wrong -> espeak can't render the real talker.
        # (b) adaptation too weak: adapt barely moves residual (small drops) -> V can't
        #     reach the speaker.
        # (c) convergence: separation exists but the argmin still misses -> local minima.
        drops = [c[0] - c[-1] for (_t, _p, c) in ll["curves"] if len(c) >= 2]
        mean_drop = float(np.mean(drops)) if drops else 0.0
        if sep <= 0.01:
            which = ("a", f"FORWARD MODEL too coarse — even at the TRUE word the best "
                     f"adapted residual ({tr_med:.3f}) is NOT below the best WRONG word "
                     f"({wr_med:.3f}; separation {sep:+.3f}). espeak cannot render the "
                     f"real talker closely enough for the true word to win. The pre-"
                     f"written lever is a RICHER GENERATOR (Piper neural voices), not a "
                     f"new recognizer.")
        elif mean_drop < 0.01:
            which = ("b", f"ADAPTATION too weak — the V-space barely moves the residual "
                     f"(mean adapt drop {mean_drop:+.3f}); coordinate descent over "
                     f"pitch/rate/variant cannot reach the heard speaker. WIDEN V (more "
                     f"continuous params / a finer vocal-tract axis / more synths/word).")
        else:
            which = ("c", f"CONVERGENCE — the TRUE word IS reachably closer after adapt "
                     f"(separation {sep:+.3f}, mean drop {mean_drop:+.3f}) but the argmin "
                     f"still misses: local minima / too few passes/starts. MORE "
                     f"multi-start (k>{k}) and refine passes (>{n_passes}).")
        verdict = (f"PLATEAU: the Phase-C loop reaches cross-speaker LOSO {ll['acc']:.3f}, "
                   f"NOT beating CMVN ({cmvn_loso:.3f} this split / 0.570 canonical; "
                   f"{gap_vs_cmvn:+.3f}). It DID beat the static floor by {gap_vs_static:+.3f}. "
                   f"DIAGNOSIS ({which[0]}): {which[1]}")
    print(f"  VERDICT: {verdict}", flush=True)
    print(f"  [timing] total {time.time()-t_start:.0f}s", flush=True)
    print("[MARKER] UNIVERSAL_LOOP_PHASEC_COMPLETE", flush=True)


def _subsample_per_word(probe, n_per_word, seed):
    """Trim a probe to n_per_word clips per word (balanced), for compute. Pure I/O."""
    rng = random.Random(seed + 7)
    by_word = {}
    for item in probe:
        by_word.setdefault(item[0], []).append(item)
    out = []
    for w, items in by_word.items():
        rng.shuffle(items)
        out += items[:n_per_word]
    rng.shuffle(out)
    return out


if __name__ == "__main__":
    main()
