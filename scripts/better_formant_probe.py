"""better_formant_probe — DOES A BETTER FORMANT ESTIMATOR REVIVE THE FILTER REP?

The filter-graph (domains/filter_graph) localized the cross-speaker bottleneck to ONE
node: formant ESTIMATION.  The pure-FILTER relational rep is the MOST source-invariant
of all reps (voiced->whisper drop only +4.0pt vs REL-BAND +16.0) — the filter
DIRECTION is right (excitation-independent) — BUT its ceiling is only 28.7% (vs
REL-BAND 83.3%) because the LPC pole/formant estimates (lpc_formants_bw) are too poor
on this blurry 8 kHz data.  So a BETTER formant-estimation node should REVIVE the
filter rep and, given its source-invariance, could BEAT REL-BAND especially on whisper.

THE BETTER NODE (the agent's named gap: cepstral liftering / cepstrum / homomorphic
deconvolution): estimate formants from the SPECTRAL ENVELOPE separated from the source.
A speech frame is SOURCE * FILTER (convolution); in the log-spectral domain that is an
ADDITION the cepstrum separates by quefrency — LOW quefrency = the smooth FILTER
envelope, HIGH quefrency = the SOURCE comb (voiced) / noise (whisper).  LIFTER to the
envelope, peak-pick the formants from THAT (robust whether excitation is harmonic or
noise).  Authored as a native Rust primitive cepstral_formants (audio_primitives::
cepstral_formants) — same flat [f,bw,...] layout as lpc_formants_bw, a DROP-IN
replacement on the filter path.  Slotted into the filter-graph as the CEPSTRAL_POLES
node feeding (via DEJITTER) the SAME relational-rank readout.

THE MATRIX — 3 reps x 3 conditions, SAME native DtwTo nearest-exemplar in every cell:
  REPS:
    (A) REL-BAND          the library's current best (relational over 32 bands).
    (B) REL-FILTER-LPC    the OLD poor estimate (LPC roots) — the baseline to beat
                          (ceiling 28.7%).
    (C) REL-FILTER-BETTER the cepstral-envelope formant node + DEJITTER (the NEW node).
  CONDITIONS:
    (i)   voiced -> voiced                 (the ceiling per rep)
    (ii)  voiced -> whisper WITHIN-speaker  (the source axis alone)
    (iii) voiced -> whisper CROSS-speaker   (the compounding: fist + carrier at once)

Recognition in EVERY cell = the native DtwTo Term (substrate.evaluate) argmin over
VOICED exemplars.  Whisper synth = the controlled owned-LPC synth (filter identical,
residual -> RMS-matched noise).  No .fit / net / sweep.  SHUFFLE backstop on best cell.

VENUE / SPLIT IDENTICAL to scripts/filter_compound_probe.py (commit 520014c1).

QUESTIONS:
  Q1 does the BETTER estimator REVIVE the filter ceiling (C >> B's 28.7%)?
  Q2 does the revived pure-filter rep then BEAT REL-BAND — close the gap at ceiling
     AND, given its source-invariance, WIN on whisper / compounding?
READ THE NUMBERS: k/N + % every cell, drops, pooled-SE on the comparisons.

Run: python -m scripts.better_formant_probe [n_train] [n_test] [seed]
"""
from __future__ import annotations

import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.recognition_graph as RG
from scripts.invariant_units_accept import band_trajectory_matrix
from scripts.voiced_whisper_probe import (load_wav, synth_whisper, gather_files,
                                          _DIGITS)
from domains.relational_shape import relational_shape
from domains.filter_relational import filter_relational, cepstral_filter_relational


CHANCE = 1.0 / len(_DIGITS)


# ---------------------------------------------------------------------------
# Representations.  All are frames x D trajectories DtwTo matches over.
# (A) REL-BAND, (B) REL-FILTER-LPC, (C) REL-FILTER-BETTER (cepstral + dejitter).
# ---------------------------------------------------------------------------
def relational_band_rep(x, fs, n_anchors=6):
    M = band_trajectory_matrix(x, fs)
    if M is None or len(M) < 2:
        return None
    return relational_shape(M, n_anchors=n_anchors)


def relational_filter_lpc_rep(x, fs, n_anchors=6):
    return filter_relational(x, fs, n_anchors=n_anchors)


def relational_filter_better_rep(x, fs, n_anchors=6):
    # cepstral-envelope formants -> dejitter is applied INSIDE the filter graph for the
    # graph-native path; here we use the trajectory + relational composition directly
    # (the dejitter median is a continuity stabilizer over the SAME trajectory).
    from domains.filter_graph import dejitter_trajectory
    from domains.filter_relational import cepstral_formant_trajectory
    M = cepstral_formant_trajectory(x, fs)
    if M is None or len(M) < 2:
        return None
    Ms = dejitter_trajectory(M)
    if Ms is None or len(Ms) < 2:
        return None
    return relational_shape(Ms, n_anchors=n_anchors)


REPS = {
    "REL-BAND": relational_band_rep,
    "REL-FILTER-LPC": relational_filter_lpc_rep,
    "REL-FILTER-BETTER": relational_filter_better_rep,
}
REP_ORDER = ["REL-BAND", "REL-FILTER-LPC", "REL-FILTER-BETTER"]


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


def all_reps(x, fs):
    return {name: fn(x, fs) for name, fn in REPS.items()}


# ---------------------------------------------------------------------------
def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    rng = np.random.default_rng(seed)

    t0 = time.time()
    files = gather_files()
    speakers = sorted({f[2] for f in files})
    print("=" * 72, flush=True)
    print("BETTER-FORMANT (cepstral envelope) REVIVES THE FILTER REP? — FSDD (10-way)",
          flush=True)
    print("=" * 72, flush=True)
    print(f"speakers: {speakers}  (chance {100*CHANCE:.1f}%)", flush=True)
    print("baselines (520014c1): REL-BAND 83.3/67.3/60.7 ; "
          "REL-FILTER-LPC 28.7/24.7/18.7", flush=True)

    # ---- speaker split for the CROSS-speaker condition (LOSO-style) ----------
    speakers = sorted(speakers)
    n_hold = max(1, len(speakers) // 3)
    held_out = set(speakers[:n_hold])
    train_spk = [s for s in speakers if s not in held_out]
    print(f"cross-speaker held-out test speakers: {sorted(held_out)}", flush=True)
    print(f"cross-speaker train speakers: {train_spk}", flush=True)

    # ---- WITHIN-speaker disjoint-clip split (conditions i, ii) ---------------
    by_key = defaultdict(list)
    for path, digit, sp, idx in files:
        by_key[(sp, digit)].append((path, idx))
    within_train, within_test = [], []
    for (sp, digit), lst in by_key.items():
        lst = sorted(lst, key=lambda t: t[1])
        cut = int(round(0.7 * len(lst)))
        for p, _ in lst[:cut]:
            within_train.append((p, _DIGITS[digit], sp))
        for p, _ in lst[cut:]:
            within_test.append((p, _DIGITS[digit], sp))

    # ---- CROSS-speaker split (condition iii) ---------------------------------
    cross_train = [(p, _DIGITS[d], sp) for (p, d, sp, _) in files
                   if sp not in held_out]
    cross_test = [(p, _DIGITS[d], sp) for (p, d, sp, _) in files
                  if sp in held_out]

    rng.shuffle(within_train); rng.shuffle(within_test)
    rng.shuffle(cross_train); rng.shuffle(cross_test)
    within_train = within_train[:n_train]
    within_test = within_test[:n_test]
    cross_train = cross_train[:n_train]
    cross_test = cross_test[:n_test]

    print(f"\nwithin-speaker: {len(within_train)} voiced exemplars, "
          f"{len(within_test)} test clips (disjoint clips, same speakers)", flush=True)
    print(f"cross-speaker : {len(cross_train)} voiced exemplars, "
          f"{len(cross_test)} test clips (HELD-OUT speakers)", flush=True)
    print(f"per-clip resolution within={100.0/max(len(within_test),1):.3f}%  "
          f"cross={100.0/max(len(cross_test),1):.3f}%\n", flush=True)

    # ---- precompute exemplar (voiced) reps -----------------------------------
    def build_exemplar_reps(train_files, tag):
        print(f"computing {tag} exemplar (voiced) reps...", flush=True)
        store = {r: [] for r in REP_ORDER}
        for path, w, sp in train_files:
            x, fs = load_wav(path)
            reps = all_reps(x, fs)
            if any(reps[r] is None for r in REP_ORDER):
                continue
            for r in REP_ORDER:
                store[r].append((reps[r], w))
        print(f"  usable {tag} exemplars: {len(store[REP_ORDER[0]])} "
              f"({time.time()-t0:.0f}s)", flush=True)
        return store

    within_ex = build_exemplar_reps(within_train, "within-speaker")
    cross_ex = build_exemplar_reps(cross_train, "cross-speaker")

    # ---- precompute test reps ------------------------------------------------
    def build_test_reps(test_files, conds, tag):
        print(f"computing {tag} test reps ({'+'.join(conds)})...", flush=True)
        store = {(r, c): [] for r in REP_ORDER for c in conds}
        for path, w, sp in test_files:
            x, fs = load_wav(path)
            sigs = {}
            if "voiced" in conds:
                sigs["voiced"] = x
            if "whisper" in conds:
                sigs["whisper"] = synth_whisper(x, seed=seed)
            for c, sig in sigs.items():
                reps = all_reps(sig, fs)
                if any(reps[r] is None for r in REP_ORDER):
                    continue
                for r in REP_ORDER:
                    store[(r, c)].append((reps[r], w))
        for c in conds:
            print(f"  {tag} {c}: {len(store[(REP_ORDER[0], c)])} usable "
                  f"({time.time()-t0:.0f}s)", flush=True)
        return store

    within_te = build_test_reps(within_test, ["voiced", "whisper"], "within-speaker")
    cross_te = build_test_reps(cross_test, ["whisper"], "cross-speaker")
    print("", flush=True)

    # ---- native DtwTo nearest-exemplar ---------------------------------------
    sub = Substrate()
    sign = sub.add_node("HeardSign", {})
    err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                          RG._Attr(RG._V("w"), "rep")))

    def build_lexicon(train_reprs, shuffle=False):
        exs = []
        words = [w for _, w in train_reprs]
        if shuffle:
            import random
            words = list(words)
            random.Random(7).shuffle(words)
        for (M, _), w in zip(train_reprs, words):
            c = sub.add_node("Exemplar", {"word": w})
            sub.set_attr(c, "rep", as_tuple(M))
            exs.append((c, w))
        return exs

    def teardown(exs):
        for c, _ in exs:
            sub.remove_node(c)

    def score(exs, test_reprs):
        corr = tot = 0
        for M, w in test_reprs:
            sub.set_attr(sign, "rep", as_tuple(M))
            best_d, best_w = 1e18, None
            for c, ew in exs:
                d = sub.evaluate(err, {"s": sign, "w": c})
                if d < best_d:
                    best_d, best_w = d, ew
            corr += int(best_w == w)
            tot += 1
        acc = corr / max(tot, 1)
        se = (acc * (1 - acc) / max(tot, 1)) ** 0.5
        return corr, tot, acc, se

    # ---- THE MATRIX ----------------------------------------------------------
    CONDS = [
        ("v->v (within)", "within", "voiced"),
        ("v->whisp (within)", "within", "whisper"),
        ("v->whisp (CROSS)", "cross", "whisper"),
    ]
    results = {}
    for rep in REP_ORDER:
        print("=" * 72, flush=True)
        print(f"REP {rep} — native DtwTo nearest-exemplar over VOICED exemplars",
              flush=True)
        print("=" * 72, flush=True)
        for label, venue, cond in CONDS:
            if venue == "within":
                exs = build_lexicon(within_ex[rep])
                te = within_te[(rep, cond)]
            else:
                exs = build_lexicon(cross_ex[rep])
                te = cross_te[(rep, cond)]
            c, t, acc, se = score(exs, te)
            teardown(exs)
            results[(rep, label)] = (c, t, acc, se)
            print(f"  {label:22s} {c:>4d}/{t:<4d} = {100*acc:5.2f}%  "
                  f"(SE {100*se:.2f}%)", flush=True)
        print("", flush=True)

    # ---- VERDICT — full matrix + drops from ceiling --------------------------
    print("=" * 72, flush=True)
    print("MATRIX — reps x conditions (k/N, %, drop from that rep's v->v ceiling)",
          flush=True)
    print("=" * 72, flush=True)
    hdr = f"  {'rep':18s}"
    for label, _, _ in CONDS:
        hdr += f" {label:>22s}"
    print(hdr, flush=True)
    for rep in REP_ORDER:
        ceil_acc = results[(rep, CONDS[0][0])][2]
        line = f"  {rep:18s}"
        for label, _, _ in CONDS:
            c, t, acc, se = results[(rep, label)]
            line += f"  {c:>3d}/{t:<3d}={100*acc:4.1f}%"
        print(line, flush=True)
        dline = f"  {'  drop:':18s}"
        for label, _, _ in CONDS:
            acc = results[(rep, label)][2]
            drop = 100 * (ceil_acc - acc)
            dline += f"  {'':9s}{drop:+5.1f}pt"
        print(dline, flush=True)
    print(f"\n  chance = {100*CHANCE:.1f}%", flush=True)

    # ---- THE QUESTIONS -------------------------------------------------------
    print("\n" + "=" * 72, flush=True)
    print("THE QUESTIONS", flush=True)
    print("=" * 72, flush=True)

    def get(rep, label):
        return results[(rep, label)][2]

    def pooled_se(rep_a, la, rep_b, lb):
        sa = results[(rep_a, la)][3]
        sb = results[(rep_b, lb)][3]
        return 100 * ((sa ** 2 + sb ** 2) ** 0.5)

    # Q1: does the BETTER estimator REVIVE the filter ceiling (C >> B's 28.7%)?
    b_ceil = get("REL-FILTER-LPC", "v->v (within)")
    c_ceil = get("REL-FILTER-BETTER", "v->v (within)")
    pse1 = pooled_se("REL-FILTER-LPC", "v->v (within)",
                     "REL-FILTER-BETTER", "v->v (within)")
    print(f"\n  Q1 REVIVAL (v->v ceiling): REL-FILTER-LPC {100*b_ceil:.1f}%  ->  "
          f"REL-FILTER-BETTER {100*c_ceil:.1f}%  "
          f"(diff {100*(c_ceil-b_ceil):+.1f}pt, pooled SE {pse1:.1f}pt)", flush=True)
    if c_ceil - b_ceil > pse1 and c_ceil > b_ceil:
        print("      >>> the BETTER estimator REVIVES the filter ceiling above SE.",
              flush=True)
    elif c_ceil > b_ceil:
        print("      >>> higher but NOT above pooled SE — suggestive, not resolved.",
              flush=True)
    else:
        print("      >>> NO revival — formant estimation off THIS cochlea is "
              "fundamentally bounded (resolution limit, not method). The lever is the "
              "cochlea / front-end resolution itself.", flush=True)

    # Q2: does the revived filter rep BEAT REL-BAND, esp. on whisper / compounding?
    print("\n  Q2 does REL-FILTER-BETTER BEAT REL-BAND?", flush=True)
    for label, _, _ in CONDS:
        a = get("REL-BAND", label)
        c = get("REL-FILTER-BETTER", label)
        pse = pooled_se("REL-BAND", label, "REL-FILTER-BETTER", label)
        verdict = "C WINS" if (c - a) > pse else ("A WINS" if (a - c) > pse else "TIE")
        print(f"      {label:22s}  REL-BAND {100*a:5.1f}%  REL-FILTER-BETTER "
              f"{100*c:5.1f}%  (diff {100*(c-a):+5.1f}pt, pooled SE {pse:.1f}pt) "
              f"-> {verdict}", flush=True)

    # ---- SHUFFLE backstop on the best cell -----------------------------------
    print("\n" + "=" * 72, flush=True)
    print("SHUFFLE BACKSTOP — best cell (labels permuted -> must collapse to chance)",
          flush=True)
    print("=" * 72, flush=True)
    best_cell = max(results.keys(), key=lambda k: results[k][2])
    brep, blabel = best_cell
    bvenue = next(v for (lab, v, _) in CONDS if lab == blabel)
    bcond = next(co for (lab, _, co) in CONDS if lab == blabel)
    ex_store = within_ex if bvenue == "within" else cross_ex
    te_store = within_te if bvenue == "within" else cross_te
    exs = build_lexicon(ex_store[brep], shuffle=True)
    c, t, acc, se = score(exs, te_store[(brep, bcond)])
    teardown(exs)
    print(f"  best cell = ({brep}, {blabel}) "
          f"true {100*results[best_cell][2]:.1f}%", flush=True)
    print(f"  SHUFFLED  {c}/{t} = {100*acc:.1f}%  (chance {100*CHANCE:.1f}%)",
          flush=True)
    if acc <= CHANCE + 2 * se + 0.03:
        print("  >>> shuffle collapses to chance — the best cell's signal is real.",
              flush=True)
    else:
        print("  >>> shuffle did NOT collapse — investigate (leakage?).", flush=True)

    print(f"\n  total wall: {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
