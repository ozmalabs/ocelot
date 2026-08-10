"""filter_graph_probe — re-run the 84b034ed 3x3 matrix with the WIRED FILTER-GRAPH.

THE MOVE (the user's correction): the front end is a GRAPH OF CONNECTABLE FILTERS, not
a fixed pipeline.  The REL-FILTER node (relational shape over RAW LPC poles) was a
DANGLING node at 31.3% — not a rep failure, but a node with no incoming STABILIZER
edge (the poles jitter off the blurry cochlea).  The fix is to WIRE it: insert a
DEJITTER node (formant tracking / continuity stabilization, from owned ops) between
LPC_POLES and RELATIONAL_RANK.  This probe asks whether wiring the de-jitter edge
REVIVES the filter node and whether the stable pure-filter rep then beats REL-BAND.

REPS — three WIRED GRAPHS from domains/filter_graph (the agent's composition):
  (A) REL-BAND          SIGNAL -> GAMMATONE -> RELATIONAL_RANK            (current best)
  (B) REL-FILTER DANGLE  SIGNAL -> LPC_POLES -> RELATIONAL_RANK           (31.3% broken)
  (C) REL-FILTER WIRED   SIGNAL -> LPC_POLES -> DEJITTER -> RELATIONAL_RANK (the fix)
B and C differ by EXACTLY the wired DEJITTER edge.

CONDITIONS — identical venue to 84b034ed (FSDD 10-way, chance 10%, N>=150):
  (i)   v -> v                  ceiling per rep
  (ii)  v -> whisper WITHIN-spk  source axis alone
  (iii) v -> whisper CROSS-spk   compounding (fist + carrier at once)
Whisper = the controlled owned-LPC synth (filter identical, residual -> noise) from
scripts.voiced_whisper_probe.  Recognition in EVERY cell = the native DtwTo Term
(substrate.evaluate) argmin over VOICED exemplars.  SHUFFLE backstop on the best cell.

BASELINES TO BEAT (84b034ed):
  REL-BAND    83.3% | 67.3% | 60.7%
  REL-FILTER  31.3% | 18.7% | 18.7%   (dangling)

THE QUESTIONS:
  Q1 does wiring de-jitter REVIVE the filter node (C ceiling >> B's 31.3%)?
  Q2 does the WIRED pure-filter rep then BEAT REL-BAND — close the whisper drop AND
     hold compounding?  (prediction: an excitation-free stable filter beats band
     energy that still carries the source spectrum)
READ THE NUMBERS: k/N + % every cell, drops, whether C's gains clear the pooled SE.

Run: python -m scripts.filter_graph_probe [n_train] [n_test] [seed]
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
from scripts.voiced_whisper_probe import (load_wav, synth_whisper, gather_files,
                                          _DIGITS)
from domains import filter_graph as FG


CHANCE = 1.0 / len(_DIGITS)

# The three WIRED graphs (built once; evaluate() flows a clip through each).
GRAPHS = {
    "REL-BAND": (FG.build_band_graph(), "RELATIONAL_RANK"),
    "REL-FILTER-DANGLE": (FG.build_filter_dangling_graph(), "RELATIONAL_RANK"),
    "REL-FILTER-WIRED": (FG.build_filter_wired_graph(), "RELATIONAL_RANK"),
}
REP_ORDER = ["REL-BAND", "REL-FILTER-DANGLE", "REL-FILTER-WIRED"]


def rep_of(name, x, fs):
    g, sink = GRAPHS[name]
    return g.evaluate(sink, x, fs)


def all_reps(x, fs):
    return {name: rep_of(name, x, fs) for name in REP_ORDER}


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    rng = np.random.default_rng(seed)

    t0 = time.time()
    files = gather_files()
    speakers = sorted({f[2] for f in files})
    print("=" * 72, flush=True)
    print("FILTER-GRAPH PROBE — wired de-jitter edge — FSDD digits (10-way)",
          flush=True)
    print("=" * 72, flush=True)
    print(f"speakers: {speakers}  (chance {100*CHANCE:.1f}%)", flush=True)
    print("\nTHE WIRED GRAPHS (the agent's composition):", flush=True)
    for name in REP_ORDER:
        g, sink = GRAPHS[name]
        print(f"  {name:18s} {g.describe(sink)}", flush=True)
    print(f"\nbaselines to beat (84b034ed):  REL-BAND 83.3|67.3|60.7  "
          f"REL-FILTER(dangling) 31.3|18.7|18.7", flush=True)

    # ---- speaker split (LOSO for the cross-speaker condition) ----------------
    n_hold = max(1, len(speakers) // 3)
    held_out = set(speakers[:n_hold])
    train_spk = [s for s in speakers if s not in held_out]
    print(f"\ncross-speaker held-out test speakers: {sorted(held_out)}", flush=True)
    print(f"cross-speaker train speakers: {train_spk}", flush=True)

    # ---- within-speaker disjoint-clip split (conditions i, ii) ---------------
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

    # ---- cross-speaker split (condition iii) ---------------------------------
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

    # ---- de-jitter sanity: native order-1 jitter raw vs stabilized -----------
    print("DE-JITTER VERIFICATION (native order-1 total variation, owned yardstick):",
          flush=True)
    jr_all, js_all, nshow = [], [], 0
    for path, w, sp in within_test[:40]:
        x, fs = load_wav(path)
        raw = FG._lpc_poles_op(x, fs)
        if raw is None or len(raw) < 4:
            continue
        stab = FG.dejitter_trajectory(raw)
        jr, js = FG.measure_jitter(raw), FG.measure_jitter(stab)
        if jr == jr and js == js:
            jr_all.append(jr); js_all.append(js)
            if nshow < 5:
                print(f"  {os.path.basename(path):18s} jitter raw={jr:8.1f} -> "
                      f"stab={js:8.1f}  ({100*(1-js/jr):+.0f}%)", flush=True)
                nshow += 1
    if jr_all:
        mr, ms = float(np.mean(jr_all)), float(np.mean(js_all))
        print(f"  MEAN over {len(jr_all)} clips: raw={mr:.1f} -> stab={ms:.1f}  "
              f"(jitter reduced {100*(1-ms/mr):.0f}%)\n", flush=True)

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
                exs = build_lexicon(within_ex[rep]); te = within_te[(rep, cond)]
            else:
                exs = build_lexicon(cross_ex[rep]); te = cross_te[(rep, cond)]
            c, t, acc, se = score(exs, te)
            teardown(exs)
            results[(rep, label)] = (c, t, acc, se)
            print(f"  {label:22s} {c:>4d}/{t:<4d} = {100*acc:5.2f}%  "
                  f"(SE {100*se:.2f}%)", flush=True)
        print("", flush=True)

    # ---- VERDICT — full matrix + drops ---------------------------------------
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
            dline += f"  {'':9s}{100*(ceil_acc-acc):+5.1f}pt"
        print(dline, flush=True)
    print(f"\n  chance = {100*CHANCE:.1f}%", flush=True)

    # ---- THE QUESTIONS -------------------------------------------------------
    print("\n" + "=" * 72, flush=True)
    print("THE QUESTIONS", flush=True)
    print("=" * 72, flush=True)

    def pooled_se(ka, kb):
        return 100 * ((results[ka][3] ** 2 + results[kb][3] ** 2) ** 0.5)

    # Q1 — does wiring de-jitter REVIVE the filter node?
    b_ceil = results[("REL-FILTER-DANGLE", "v->v (within)")]
    c_ceil = results[("REL-FILTER-WIRED", "v->v (within)")]
    pse = pooled_se(("REL-FILTER-DANGLE", "v->v (within)"),
                    ("REL-FILTER-WIRED", "v->v (within)"))
    revive = 100 * (c_ceil[2] - b_ceil[2])
    print(f"\n  Q1 REVIVE the filter node (ceiling):", flush=True)
    print(f"      DANGLE {100*b_ceil[2]:.1f}%  ->  WIRED {100*c_ceil[2]:.1f}%  "
          f"(lift {revive:+.1f}pt, pooled SE {pse:.1f}pt)", flush=True)
    if revive > pse and c_ceil[2] > b_ceil[2] + 0.05:
        print("      >>> WIRING REVIVES the filter node (lift clears pooled SE).",
              flush=True)
    elif revive > pse:
        print("      >>> de-jitter lifts above SE but modestly.", flush=True)
    else:
        print("      >>> de-jitter does NOT revive C: the pole ESTIMATES are too poor "
              "on this data (garbage-in deeper than jitter). Honest result.",
              flush=True)

    # Q2 — does WIRED pure-filter then BEAT REL-BAND?
    print(f"\n  Q2 does WIRED filter BEAT REL-BAND (per condition):", flush=True)
    for label, _, _ in CONDS:
        a = results[("REL-BAND", label)]
        c = results[("REL-FILTER-WIRED", label)]
        d = 100 * (c[2] - a[2])
        ps = pooled_se(("REL-BAND", label), ("REL-FILTER-WIRED", label))
        verdict = ("WIRED beats BAND (>SE)" if d > ps else
                   "WIRED beats BAND (<SE)" if d > 0 else
                   "BAND still ahead")
        print(f"      {label:22s} BAND {100*a[2]:5.1f}%  WIRED {100*c[2]:5.1f}%  "
              f"(diff {d:+5.1f}pt, pooled SE {ps:.1f}pt)  {verdict}", flush=True)

    # whisper drop comparison
    print(f"\n  whisper DROP from ceiling (smaller = source hurt less):", flush=True)
    for rep in REP_ORDER:
        ceil = results[(rep, "v->v (within)")][2]
        wd = 100 * (ceil - results[(rep, "v->whisp (within)")][2])
        cd = 100 * (ceil - results[(rep, "v->whisp (CROSS)")][2])
        print(f"      {rep:18s} within-whisp {wd:+5.1f}pt   cross-whisp {cd:+5.1f}pt",
              flush=True)

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
    print(f"  best cell = ({brep}, {blabel}) true {100*results[best_cell][2]:.1f}%",
          flush=True)
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
