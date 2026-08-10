"""filter_compound_probe — GOAL 1 (PURIFY toward the filter) + GOAL 2 (the
COMPOUNDING torture test: cross-speaker x whisper), in ONE do-contrast matrix.

THE TWO MOVES from the voiced<->whisper falsifier (ozma_whisper_message_is_the_filter):
  GOAL 1 — the band-energy relational shape PASSED the within-speaker whisper
    falsifier (67.5% v->whisper vs 28.7% surface) but dropped 15.6 pts from its
    83.1% ceiling EVEN WITH THE LPC FILTER HELD IDENTICAL, because gammatone band
    ENERGY reflects the EXCITATION (harmonic pulses vs noise) too — the rep is MOSTLY
    but not PURELY filter.  PURIFY: read the SAME relational composition over the LPC
    POLE / FORMANT trajectory (the pure, excitation-independent vocal-tract filter)
    instead of the 32 band energies.  PREDICTION: the pole/formant relational rep
    CLOSES the whisper drop because it discards the excitation the band rep carries.
  GOAL 2 — COMPOUND both axes at once: train VOICED on some speakers, test WHISPERED
    on HELD-OUT speakers (the FIST and the CARRIER both change).  Does (C) hold where
    (A)/(B) break?

THE MATRIX — 3 reps x 3 conditions, SAME native DtwTo nearest-exemplar in every cell:
  REPS:
    (A) SURFACE   raw gammatone band-energy trajectory (frames x 32).
    (B) RELATIONAL band-energy — domains.relational_shape over the 32 bands (current
        whisper-falsifier winner).
    (C) RELATIONAL FILTER/POLE — domains.filter_relational: the SAME relational
        composition (ordinal rank + whole-unit self-similarity) over the LPC
        formant/pole trajectory (F1/F2/F3 + bandwidths) = the PURE filter.
  CONDITIONS:
    (i)   voiced -> voiced                 (the ceiling per rep)
    (ii)  voiced -> whisper WITHIN-speaker  (the source axis alone)
    (iii) voiced -> whisper CROSS-speaker   (the compounding: fist + carrier at once)

Recognition in EVERY cell = the native DtwTo Term (substrate.evaluate) argmin over
VOICED exemplars.  Whisper synth = the controlled owned-LPC synth from
scripts.voiced_whisper_probe (filter identical, residual -> RMS-matched noise).
No .fit / net / sweep.  SHUFFLE backstop on the best cell.

VENUE: FSDD digits (10-way, chance 10%).
  within-speaker (i,ii): train+test DISJOINT clips of the SAME speakers.
  cross-speaker (iii):   LOSO — train exemplars from a set of speakers; whisper test
    clips from the HELD-OUT speakers.  The whisper test set for (ii) and (iii) is the
    SAME clips' synth-whisper; only the exemplar pool's speaker overlap differs.

READ THE NUMBERS: k/N + % for every cell + the DROP from ceiling per rep per
condition.  Any claimed improvement must clear the pooled SE.  Honest NULL/HARM is a
genuine result (the pole estimates off a blurry cochlea may be jittery -> the purer
rep NOISIER not better; or the compound may break all reps toward chance).

Run: python -m scripts.filter_compound_probe [n_train] [n_test] [seed]
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
from domains.filter_relational import filter_relational


CHANCE = 1.0 / len(_DIGITS)


# ---------------------------------------------------------------------------
# Representations.  All three are frames x D trajectories DtwTo matches over.
# ---------------------------------------------------------------------------
def surface_rep(x, fs):
    M = band_trajectory_matrix(x, fs)
    return M if M is not None and len(M) >= 2 else None


def relational_band_rep(x, fs, n_anchors=6):
    M = band_trajectory_matrix(x, fs)
    if M is None or len(M) < 2:
        return None
    return relational_shape(M, n_anchors=n_anchors)


def relational_filter_rep(x, fs, n_anchors=6):
    return filter_relational(x, fs, n_anchors=n_anchors)


REPS = {
    "SURFACE": surface_rep,
    "REL-BAND": relational_band_rep,
    "REL-FILTER": relational_filter_rep,
}
REP_ORDER = ["SURFACE", "REL-BAND", "REL-FILTER"]


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


def all_reps(x, fs):
    out = {}
    for name, fn in REPS.items():
        out[name] = fn(x, fs)
    return out


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
    print("FILTER-PURITY + COMPOUNDING PROBE — FSDD digits (10-way)", flush=True)
    print("=" * 72, flush=True)
    print(f"speakers: {speakers}  (chance {100*CHANCE:.1f}%)", flush=True)

    # ---- speaker split for the CROSS-speaker condition (LOSO-style) ----------
    # Hold out a subset of speakers entirely; the rest are the cross-speaker
    # exemplar pool.  The WITHIN-speaker conditions use a disjoint-clip split.
    speakers = sorted(speakers)
    n_hold = max(1, len(speakers) // 3)
    held_out = set(speakers[:n_hold])         # cross-speaker TEST speakers
    train_spk = [s for s in speakers if s not in held_out]
    print(f"cross-speaker held-out test speakers: {sorted(held_out)}", flush=True)
    print(f"cross-speaker train speakers: {train_spk}", flush=True)

    # ---- WITHIN-speaker disjoint-clip split (conditions i, ii) ---------------
    by_key = defaultdict(list)
    for path, digit, sp, idx in files:
        by_key[(sp, digit)].append((path, idx))
    within_train, within_test = [], []   # within-speaker exemplars / test clips
    for (sp, digit), lst in by_key.items():
        lst = sorted(lst, key=lambda t: t[1])
        cut = int(round(0.7 * len(lst)))
        for p, _ in lst[:cut]:
            within_train.append((p, _DIGITS[digit], sp))
        for p, _ in lst[cut:]:
            within_test.append((p, _DIGITS[digit], sp))

    # ---- CROSS-speaker split (condition iii) ---------------------------------
    # Exemplars: ALL clips from non-held-out speakers (voiced).
    # Test: clips from held-out speakers (whispered).
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
    # (i)   within test, VOICED
    # (ii)  within test, WHISPER
    # (iii) cross  test, WHISPER
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
    # cell key: (rep, condition_label)
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
    hdr = f"  {'rep':12s}"
    for label, _, _ in CONDS:
        hdr += f" {label:>22s}"
    print(hdr, flush=True)
    for rep in REP_ORDER:
        ceil_acc = results[(rep, CONDS[0][0])][2]
        line = f"  {rep:12s}"
        for label, _, _ in CONDS:
            c, t, acc, se = results[(rep, label)]
            line += f"  {c:>3d}/{t:<3d}={100*acc:4.1f}%"
        print(line, flush=True)
        # drops
        dline = f"  {'  drop:':12s}"
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

    def drop(rep, label):
        return 100 * (results[(rep, CONDS[0][0])][2] - results[(rep, label)][2])

    def pooled_se(rep_a, la, rep_b, lb):
        sa = results[(rep_a, la)][3]
        sb = results[(rep_b, lb)][3]
        return 100 * ((sa ** 2 + sb ** 2) ** 0.5)

    # Q1: does (C) REL-FILTER close the within-speaker whisper drop vs (B) REL-BAND?
    db = drop("REL-BAND", "v->whisp (within)")
    dc = drop("REL-FILTER", "v->whisp (within)")
    print(f"\n  Q1 within-speaker whisper DROP:  REL-BAND {db:+.1f}pt  vs  "
          f"REL-FILTER {dc:+.1f}pt", flush=True)
    # compare the two whisper accuracies directly with pooled SE
    acc_b = results[("REL-BAND", "v->whisp (within)")][2]
    acc_c = results[("REL-FILTER", "v->whisp (within)")][2]
    pse = pooled_se("REL-BAND", "v->whisp (within)",
                    "REL-FILTER", "v->whisp (within)")
    diff = 100 * (acc_c - acc_b)
    print(f"      v->whisper acc:  REL-BAND {100*acc_b:.1f}%  REL-FILTER "
          f"{100*acc_c:.1f}%  (diff {diff:+.1f}pt, pooled SE {pse:.1f}pt)", flush=True)
    if dc < db and diff > pse:
        print("      >>> (C) CLOSES the within-speaker whisper drop above SE.",
              flush=True)
    elif dc < db:
        print("      >>> (C) has the smaller drop but NOT above pooled SE — report "
              "as suggestive, not resolved.", flush=True)
    else:
        print("      >>> (C) does NOT close the drop (pole estimates likely jittery "
              "off a blurry cochlea). Honest null/harm.", flush=True)

    # Q2: does (C) hold the CROSS-speaker x whisper compounding where A/B break?
    print(f"\n  Q2 CROSS-speaker x whisper (compounding):", flush=True)
    for rep in REP_ORDER:
        c, t, acc, se = results[(rep, "v->whisp (CROSS)")]
        print(f"      {rep:12s} {c}/{t} = {100*acc:.1f}% (SE {100*se:.1f}%, "
              f"chance {100*CHANCE:.1f}%)", flush=True)
    best_cross = max(REP_ORDER, key=lambda r: results[(r, "v->whisp (CROSS)")][2])
    acc_best = results[(best_cross, "v->whisp (CROSS)")][2]
    print(f"      best compounding cell: {best_cross} at {100*acc_best:.1f}%",
          flush=True)

    # ---- SHUFFLE backstop on the best cell -----------------------------------
    print("\n" + "=" * 72, flush=True)
    print("SHUFFLE BACKSTOP — best cell (labels permuted -> must collapse to chance)",
          flush=True)
    print("=" * 72, flush=True)
    # pick the best cell overall (rep, label)
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
