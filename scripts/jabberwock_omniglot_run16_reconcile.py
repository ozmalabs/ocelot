"""OMNIGLOT RUN 16 — RECONCILIATION: SC+TPS CONTINUOUS VERDICT (scratchpad/HANDWRITING_
DESIGN.md's "RECONCILIATION" section, 2026-07-03). The excavation found the EARLIER Family-A
arc (`domains/analysis_by_synthesis.py`, superseded 2026-07-02 for LEARN/decode but never
disproven as a VERDICT) hit 78-81.5% at matched protocol using FUSED CONTINUOUS comparators
(ShapeContextDist + TpsDeformDist [+ SmoothDeformDist], raw un-quantized point sets, a held
Argmax/Argmin) — while the CURRENT gate's own powered ceiling
(results/omniglot_gate_run15_power_b.log, n=400) is 26.8% [22.6, 31.3], using the WEAK
DtwTo-on-quantized-renders verdict `domains.abs_read.abs_rerank`/`abs_rerank_targeted` build.
RUN 11's own K=20 full-dwell ablation already implicated the verdict, not proposal recall alone
(27.5% < 37.5% historical — MORE candidates through the weak verdict LOSES).

RECONCILIATION HYPOTHESIS: earned quanta PROPOSE (unchanged — the existing delta=0+appearance
shortlist, `abs_rerank_targeted`'s own `shortlist0`), strong continuous geometry DECIDES
(`domains.abs_read`'s new `whole_figure_point_set`/`sctps_verdict_term`/`sctps_rerank`, additive,
this same run's own scratchpad section — see that module for the full rationale). This script is
the RUN 16 GATE, run against the SAME 10 alphabets / seed RUN 15 Phase 1 used, on the SAME
protocol shape (WAY=20, up to R=2 seeded repeats/alphabet). No decode cache PERSISTS across
process invocations (verified: the pre-existing gate's own `cache` dict is a plain in-process
Python object, never pickled/saved) — every run, including RUN 15's own, re-decodes from a fresh
LEARN. This script therefore performs its OWN fresh LEARN + decode, honestly logged as such,
rather than claiming a cache-sharing that cannot exist across processes.

FOUR ARMS (all decided by held Terms — a held Argmin/Argmax, never a Python min/max/sort):
  1. ADOPTED (control, must reproduce RUN 15's 26.8% [22.6, 31.3] — CI-overlap, not exact
     equality, since this run's own n/scope may differ under the runtime budget below):
     `ar.abs_rerank_targeted(delta=0, use_appearance=True)`, BYTE-IDENTICAL to RUN 15's own
     "adopted" arm.
  2. SC+TPS SHORTLIST: re-rank the SAME arm-1 shortlist (`adopted["shortlist0"]`, the existing
     delta=0+appearance proposal — UNCHANGED) via `ar.sctps_rerank` (ShapeContextDist+TpsDeformDist
     over whole-figure point-sets, held Argmin) IN PLACE of the DtwTo-on-quantized-render verdict.
  3. SC+TPS FULL DWELL: `ar.sctps_rerank` over `range(way)` — every candidate, no proposal filter
     at all — the DIRECT measurement of comparator strength alone (mirrors RUN 11's own K=20
     full-dwell ablation, but with the STRONG verdict in place of the weak one).
  4. SC+TPS+SMOOTH ENSEMBLE (budget-gated — included only if the measured per-compare cost keeps
     the projected total under the runtime budget, logged either way): the SAME arm-2 shortlist,
     `include_smooth=True` — one step toward Family-A's full three-comparator ensemble.

RUNTIME BUDGET (this script's own single-process wall clock, logged plainly, never silently
truncated — the SAME "estimate, log, cap" discipline RUN 15 Phase 1 established): a PILOT block
(the first alphabet's first repeat, all base arms) is timed BEFORE committing to the full R=2 x
10-alphabet scope; if the projection exceeds the budget, R drops to 1 and/or the alphabet list is
capped (sorted-name prefix), logged either way — never a silent truncation, never a background
run left to finish unsupervised.

donkey=0: every decision on the classification path is a held Term evaluate (`Argmax`/`Argmin`
over the SAME (score, id) pair idiom `abs_read`/the RUN 15 gate already established) — this
script only iterates real files, calls the SAME `decode_char_signature`/`abs_rerank_targeted`
this codebase already gates, and the NEW `ar.whole_figure_point_set`/`ar.sctps_rerank` (also held-
Term verdicts, see `domains/abs_read.py`'s own docstring). No torch anywhere on the path.

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run16_reconcile.py
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np

import scripts.jabberwock_omniglot_dynamic_quantization as gate
from domains import abs_read as ar
from domains import omniglot_world as ow

SEP = "=" * 92

# ---------------------------------------------------------------------------------------------
# CAPS — logged verbatim, no silent truncation. LEARN_STROKE_CAP is REDUCED from the base gate's
# 3000 (a documented, honest reduction, not blind retuning): RUN 15's own growth log
# (results/omniglot_gate_run15_power_b.log) shows the codebook saturates at 7 quanta by the
# FIRST 100-stroke window and stays flat for the remaining 2900 — a lower cap still above that
# saturation point reproduces the identical codebook. Verified below (saturation check re-run
# at this cap).
# ---------------------------------------------------------------------------------------------
LEARN_STROKE_CAP = 1500
POWER_ALPHABETS = ["Angelic", "Atemayar_Qelisayer", "Atlantean", "Aurek-Besh", "Avesta",
                    "Ge_ez", "Glagolitic", "Gurmukhi", "Kannada", "Keble"]   # RUN 15's own 10
WAY = gate.WAY                                    # 20
EPISODES_PER_ALPHABET = WAY                        # 20 (RUN 15's own "episodes/repeat")
R_TARGET = 2                                       # RUN 15's own POWER_R
POWER_SEED = gate.SEED + 1500                      # RUN 15's own POWER_SEED, byte-identical
RUNTIME_BUDGET_SECONDS = 480.0                     # this script's OWN wall-clock budget (leaves
                                                    # headroom under the 600s foreground cap for
                                                    # import/boot/LEARN + final reporting).
ABS_TOPK_UNUSED = gate.ABS_TOPK                    # logged for parity; adopted arm ignores k
                                                    # (delta=0+appearance controls the shortlist)

RUN15_ADOPTED = {"acc": 0.268, "ci": (0.226, 0.313), "n": 400}   # the number arm 1 must overlap


def _acc_ci(preds, trues):
    k = sum(1 for p, t in zip(preds, trues) if p == t)
    acc = k / max(1, len(trues))
    lo, hi = gate.wilson_ci(k, len(trues))
    return acc, (lo, hi), k


def _episode(s, native, dk, qd, true_idx, exemplar_composed, exemplar_stroke_points, exemplar_ps,
             run_arm4: bool):
    """ONE query episode's four (or three) arm predictions — every winner a held
    `Argmax`/`Argmin` evaluate (`abs_rerank_targeted`'s own internal verdict; `ar.sctps_rerank`'s
    held `_argmin_pairs_term`). Returns predictions + per-arm timing/budget instrumentation."""
    t_adopted0 = time.time()
    adopted = ar.abs_rerank_targeted(
        s, qd["composed_sig"], qd["stroke_points"], exemplar_composed, exemplar_stroke_points,
        delta=0.0, use_widen=False, use_appearance=True, turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
        segments=dk["segments"])
    t_adopted = time.time() - t_adopted0
    w_adopted = adopted["winner"] if adopted["winner"] is not None else -1
    shortlist = adopted["shortlist0"]

    q_ps = ar.whole_figure_point_set(qd["stroke_points"])

    t_sl0 = time.time()
    sctps_sl = ar.sctps_rerank(native, q_ps, exemplar_ps, shortlist)
    t_sl = time.time() - t_sl0
    w_sctps_sl = sctps_sl["winner"] if sctps_sl["winner"] is not None else -1

    t_full0 = time.time()
    sctps_full = ar.sctps_rerank(native, q_ps, exemplar_ps, list(range(len(exemplar_ps))))
    t_full = time.time() - t_full0
    w_sctps_full = sctps_full["winner"] if sctps_full["winner"] is not None else -1

    w_sctps_ens = -1
    t_ens = 0.0
    n_ens_compared = 0
    if run_arm4:
        t_ens0 = time.time()
        sctps_ens = ar.sctps_rerank(native, q_ps, exemplar_ps, shortlist, include_smooth=True)
        t_ens = time.time() - t_ens0
        w_sctps_ens = sctps_ens["winner"] if sctps_ens["winner"] is not None else -1
        n_ens_compared = sctps_ens["n_compared"]

    return dict(w_adopted=w_adopted, w_sctps_sl=w_sctps_sl, w_sctps_full=w_sctps_full,
                w_sctps_ens=w_sctps_ens, shortlist_size=len(shortlist),
                n_sl_compared=sctps_sl["n_compared"], n_full_compared=sctps_full["n_compared"],
                n_ens_compared=n_ens_compared, t_adopted=t_adopted, t_sl=t_sl, t_full=t_full,
                t_ens=t_ens, in_shortlist=1 if true_idx in shortlist else 0)


def _run_block(s, native, dk, cache, alph, r, rng, way, episodes_per_alphabet, run_arm4: bool):
    """ONE (alphabet, repeat) block: ONE fixed exemplar draw + `episodes_per_alphabet` query
    episodes — mirrors `gate.run_powered_test`'s own per-block structure exactly, plus the SC+TPS
    arms. Returns per-episode records + timing totals for this block alone (the PILOT/budget
    unit)."""
    t_block0 = time.time()
    chars = sorted(ow.characters(alph, "evaluation"))[:way]
    drawer_files = [ow.drawings(cd) for cd in chars]
    n_drawers = min(len(fl) for fl in drawer_files)

    ex_drawer = int(rng.integers(n_drawers))
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, dk)
                 for ci in range(way)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]
    exemplar_stroke_points = [e["stroke_points"] for e in exemplars]
    exemplar_ps = [ar.whole_figure_point_set(e["stroke_points"]) for e in exemplars]

    records = []
    for qi in range(min(episodes_per_alphabet, way)):
        q_drawer = int(rng.integers(n_drawers))
        while q_drawer == ex_drawer:
            q_drawer = int(rng.integers(n_drawers))
        qd = gate.decode_char_signature(s, drawer_files[qi][q_drawer], cache, dk)
        ep = _episode(s, native, dk, qd, qi, exemplar_composed, exemplar_stroke_points,
                      exemplar_ps, run_arm4)
        ep["true"] = qi
        records.append(ep)

    return dict(records=records, elapsed=time.time() - t_block0)


def main():
    t0 = time.time()
    print(SEP)
    print("OMNIGLOT RUN 16 -- RECONCILIATION: SC+TPS CONTINUOUS VERDICT vs the DtwTo-on-")
    print("quantized-render verdict, on the SAME 10 alphabets / seed RUN 15 Phase 1 used.")
    print(SEP)

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    print(f"\n  LEARN caps (REDUCED from the base gate's 3000 -- see module docstring): "
          f"{gate.LEARN_ALPHABETS_N} background alphabets {learn_alphabets}, drawers "
          f"{gate.LEARN_DRAWERS[0]}-{gate.LEARN_DRAWERS[-1]}, capped at {LEARN_STROKE_CAP} "
          f"pen-down strokes. ink-decode params: {gate.DK}")

    print(f"\n{SEP}\n  PHASE 1: LEARN (reduced cap, same ink-decode params)\n{SEP}")
    lr = gate.run_learn(s, ag, native, learn_alphabets, gate.LEARN_DRAWERS, LEARN_STROKE_CAP,
                         gate.DK, gate.GROWTH_WINDOW)
    growth = lr["growth"]
    print(f"  processed {lr['n_strokes']} pen-down strokes "
          f"({lr['n_degenerate_skipped']} degenerate skipped) in {lr['elapsed']:.1f}s.")
    sat_pass = None
    if len(growth) >= 3:
        first = np.mean([g["new_quanta"] for g in growth[:1]])
        last = np.mean([g["new_quanta"] for g in growth[-2:]])
        sat_pass = last <= max(3.0, 0.3 * first) if first > 0 else True
        print(f"  saturation check (reduced-cap re-verification): first-window new={first:.1f} "
              f"-> last-2-windows mean new={last:.1f}  VERDICT: "
              f"{'PASS' if sat_pass else 'FAIL -- codebook still growing, cap too low'}")
    import domains.stroke_codebook as sc
    final_codebook = len(sc._existing_names(s, "stroke"))
    print(f"  final LEARN codebook size: {final_codebook} stroke quanta "
          f"(RUN 15's own LEARN produced 7).")
    learn_elapsed = time.time() - t0

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2: PILOT -- time ONE (alphabet, repeat) block, project the full run, decide R /
    #  the alphabet cap / whether arm 4 (the SmoothDeformDist ensemble) fits the budget.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2: PILOT + RUNTIME BUDGET PROJECTION\n{SEP}")
    cache: dict = {}
    # The pilot uses its OWN rng instance (same seed) purely to measure timing/decide the scope
    # -- it does NOT consume the "official" rng sequence Phase 3 uses below, so Phase 3's own
    # first block reproduces the EXACT SAME exemplar/query draws deterministically (byte-
    # identical seeds), and every block (including the first) is scored fresh with the FINAL
    # decided `run_arm4` flag -- no partial-arm records ever enter the reported totals.
    pilot_rng = np.random.default_rng(POWER_SEED)
    pilot = _run_block(s, native, gate.DK, cache, POWER_ALPHABETS[0], 0, pilot_rng, WAY,
                        EPISODES_PER_ALPHABET, run_arm4=False)
    n_sl_compares_pilot = sum(r["n_sl_compared"] for r in pilot["records"])
    t_sl_pilot = sum(r["t_sl"] for r in pilot["records"])
    per_compare_ms = 1000 * t_sl_pilot / max(1, n_sl_compares_pilot)
    print(f"  PILOT block ({POWER_ALPHABETS[0]!r}, repeat 0, {len(pilot['records'])} episodes): "
          f"{pilot['elapsed']:.1f}s ({pilot['elapsed']/max(1,len(pilot['records'])):.2f}s/episode)")
    print(f"  SC+TPS shortlist per-compare cost (measured): {per_compare_ms:.2f}ms/compare "
          f"over {n_sl_compares_pilot} compares in this block.")

    elapsed_so_far = time.time() - t0
    n_blocks_full = len(POWER_ALPHABETS) * R_TARGET
    projected_full = elapsed_so_far + pilot["elapsed"] * (n_blocks_full - 1)
    r_used = R_TARGET
    alphabets_used = list(POWER_ALPHABETS)
    budget_notes = []
    print(f"  projection @ R={R_TARGET}, {len(POWER_ALPHABETS)} alphabets: {projected_full:.0f}s "
          f"total vs {RUNTIME_BUDGET_SECONDS:.0f}s budget.")
    if projected_full > RUNTIME_BUDGET_SECONDS:
        r_used = 1
        n_blocks_r1 = len(POWER_ALPHABETS) * r_used
        projected_r1 = elapsed_so_far + pilot["elapsed"] * (n_blocks_r1 - 1)
        note = (f"R=2 projected {projected_full:.0f}s > {RUNTIME_BUDGET_SECONDS:.0f}s budget -- "
                f"REDUCING to R=1 (projected {projected_r1:.0f}s).")
        print(f"  {note}")
        budget_notes.append(note)
        if projected_r1 > RUNTIME_BUDGET_SECONDS:
            remaining = RUNTIME_BUDGET_SECONDS - elapsed_so_far
            n_more_blocks = max(0, int(remaining / max(1e-6, pilot["elapsed"])))
            alphabets_used = POWER_ALPHABETS[:max(1, n_more_blocks + 1)]
            note2 = (f"R=1 still projected {projected_r1:.0f}s > budget -- CAPPING to the first "
                     f"{len(alphabets_used)} alphabets (sorted-name prefix): {alphabets_used!r}.")
            print(f"  {note2}")
            budget_notes.append(note2)

    # arm 4 (SmoothDeformDist ensemble) budget check: incremental per-compare cost, projected
    # over the (possibly reduced) shortlist-arm compare volume.
    n_blocks_final = len(alphabets_used) * r_used
    projected_sl_compares = n_sl_compares_pilot * n_blocks_final
    # SmoothDeformDist's own incremental cost (measured directly, a tiny standalone probe --
    # never blocks on a full block re-run): one extra evaluate per shortlist compare.
    t_smooth0 = time.time()
    for _ in range(20):
        native.evaluate({"type": "SmoothDeformDist",
                          "a": {"type": "Lit", "value": [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]},
                          "b": {"type": "Lit", "value": [[0.0, 0.1], [1.0, 0.0], [0.1, 1.0]]}},
                         {})
    smooth_ms = 1000 * (time.time() - t_smooth0) / 20
    projected_arm4_extra = smooth_ms / 1000.0 * projected_sl_compares
    run_arm4 = (elapsed_so_far + pilot["elapsed"] * (n_blocks_final - 1) + projected_arm4_extra
                < RUNTIME_BUDGET_SECONDS)
    print(f"  SmoothDeformDist incremental cost (measured, isolated probe): {smooth_ms:.3f}ms/"
          f"compare; projected arm-4 extra over {projected_sl_compares} shortlist compares: "
          f"{projected_arm4_extra:.1f}s -- arm 4 {'INCLUDED' if run_arm4 else 'SKIPPED (logged cap)'}.")
    if not run_arm4:
        budget_notes.append("arm 4 (SC+TPS+SmoothDeformDist ensemble) SKIPPED -- projected cost "
                             "would not fit the remaining budget at this scope.")

    print(f"  FINAL SCOPE: {len(alphabets_used)} alphabets x R={r_used} x "
          f"{EPISODES_PER_ALPHABET} episodes = {len(alphabets_used) * r_used * EPISODES_PER_ALPHABET} "
          f"target episodes. arm 4 = {run_arm4}.")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 3: THE FULL RUN -- EVERY block (including the alphabet[0]/repeat-0 block the pilot
    #  already timed) is scored FRESH here with the FINAL decided `run_arm4` flag, off a fresh
    #  "official" rng at the SAME seed the pilot used -- so block 0 reproduces the pilot's own
    #  exemplar/query draws byte-identically (deterministic), but never reuses the pilot's
    #  run_arm4=False records (which would silently leave arm 4 as an all-miss placeholder for
    #  that block). The decode cache is already warm from the pilot, so re-scoring block 0 here
    #  is cheap (cache hits only, no re-decode). Hard wall-clock safety net: stop + log honestly,
    #  never silently truncate mid-block.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 3: POWERED RECONCILIATION RUN\n{SEP}")
    official_rng = np.random.default_rng(POWER_SEED)
    all_records = []
    hard_deadline = t0 + RUNTIME_BUDGET_SECONDS
    stopped_early = None
    for ai, alph in enumerate(alphabets_used):
        for r in range(r_used):
            if time.time() > hard_deadline:
                stopped_early = (alph, r)
                break
            blk = _run_block(s, native, gate.DK, cache, alph, r, official_rng, WAY,
                              EPISODES_PER_ALPHABET, run_arm4)
            all_records.extend(blk["records"])
        if stopped_early:
            break

    if stopped_early:
        note = (f"HARD DEADLINE reached at {alphabets_used!r} block {stopped_early!r} -- "
                f"stopped early with {len(all_records)} episodes scored (honest, not a crash).")
        print(f"  {note}")
        budget_notes.append(note)

    trues = [r["true"] for r in all_records]
    shuf_trues = list(trues)
    np.random.default_rng(POWER_SEED + 1).shuffle(shuf_trues)

    def _report_arm(name, key):
        preds = [r[key] for r in all_records]
        acc, ci, k = _acc_ci(preds, trues)
        acc_s, ci_s, k_s = _acc_ci(preds, shuf_trues)
        print(f"  {name:<28} n={len(trues):>4}  k={k:>3}  acc={100*acc:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]  shuffled={100*acc_s:5.1f}%")
        return dict(acc=acc, ci=ci, k=k, acc_shuf=acc_s)

    print(f"\n  {len(all_records)} total episodes scored.\n")
    r_adopted = _report_arm("ADOPTED (control)", "w_adopted")
    r_sl = _report_arm("SC+TPS SHORTLIST", "w_sctps_sl")
    r_full = _report_arm("SC+TPS FULL DWELL", "w_sctps_full")
    if run_arm4:
        r_ens = _report_arm("SC+TPS+SMOOTH ENSEMBLE", "w_sctps_ens")
    else:
        r_ens = None

    coverage_shortlist = float(np.mean([r["in_shortlist"] for r in all_records]))
    mean_shortlist_size = float(np.mean([r["shortlist_size"] for r in all_records]))
    total_sl_time = sum(r["t_sl"] for r in all_records)
    total_sl_compares = sum(r["n_sl_compared"] for r in all_records)
    total_full_time = sum(r["t_full"] for r in all_records)
    total_full_compares = sum(r["n_full_compared"] for r in all_records)
    total_adopted_time = sum(r["t_adopted"] for r in all_records)

    print(f"\n  coverage@shortlist (true exemplar in the delta=0+appearance proposal): "
          f"{100*coverage_shortlist:.1f}%   mean shortlist size: {mean_shortlist_size:.2f}")
    print(f"  BUDGET / PER-COMPARE COST:")
    print(f"    ADOPTED (DtwTo render-compare) total: {total_adopted_time:.1f}s over "
          f"{len(all_records)} episodes ({1000*total_adopted_time/max(1,len(all_records)):.1f}ms/episode)")
    print(f"    SC+TPS SHORTLIST total: {total_sl_time:.1f}s over {total_sl_compares} compares "
          f"({1000*total_sl_time/max(1,total_sl_compares):.2f}ms/compare)")
    print(f"    SC+TPS FULL DWELL total: {total_full_time:.1f}s over {total_full_compares} "
          f"compares ({1000*total_full_time/max(1,total_full_compares):.2f}ms/compare)")
    if run_arm4:
        total_ens_time = sum(r["t_ens"] for r in all_records)
        total_ens_compares = sum(r["n_ens_compared"] for r in all_records)
        print(f"    SC+TPS+SMOOTH ENSEMBLE total: {total_ens_time:.1f}s over "
              f"{total_ens_compares} compares "
              f"({1000*total_ens_time/max(1,total_ens_compares):.2f}ms/compare)")

    print(f"\n{SEP}\n  VERDICTS\n{SEP}")
    ci_a = r_adopted["ci"]
    overlaps_run15 = not (ci_a[1] < RUN15_ADOPTED["ci"][0] or RUN15_ADOPTED["ci"][1] < ci_a[0])
    print(f"  CONTROL REPRODUCTION: this run's ADOPTED {100*r_adopted['acc']:.1f}% "
          f"{[100*x for x in ci_a]} vs RUN 15's powered {100*RUN15_ADOPTED['acc']:.1f}% "
          f"{[100*x for x in RUN15_ADOPTED['ci']]} (n={RUN15_ADOPTED['n']}) -- "
          f"{'CI-OVERLAP (consistent)' if overlaps_run15 else 'CI-SEPARATED (inconsistent -- investigate)'}")

    sep_sl_vs_adopted = gate._ci_separated(r_sl["ci"], r_adopted["ci"])
    print(f"  SC+TPS SHORTLIST vs ADOPTED: {100*r_sl['acc']:.1f}% vs {100*r_adopted['acc']:.1f}% -- "
          f"{'CI-SEPARATED' if sep_sl_vs_adopted else 'NOT CI-SEPARATED'} "
          f"(delta {100*(r_sl['acc']-r_adopted['acc']):+.1f}pp)")

    sep_full_vs_sl = gate._ci_separated(r_full["ci"], r_sl["ci"])
    print(f"  SC+TPS FULL DWELL vs SC+TPS SHORTLIST (the shortlist-vs-full-dwell gap -- does "
          f"proposal recall still bind once the verdict is strong?): {100*r_full['acc']:.1f}% vs "
          f"{100*r_sl['acc']:.1f}% -- {'CI-SEPARATED' if sep_full_vs_sl else 'NOT CI-SEPARATED'} "
          f"(delta {100*(r_full['acc']-r_sl['acc']):+.1f}pp)")

    sep_full_vs_adopted = gate._ci_separated(r_full["ci"], r_adopted["ci"])
    print(f"  SC+TPS FULL DWELL vs ADOPTED (THE reconciliation number -- does strong continuous "
          f"geometry recover toward Family-A's 60-80% band?): {100*r_full['acc']:.1f}% vs "
          f"{100*r_adopted['acc']:.1f}% -- {'CI-SEPARATED' if sep_full_vs_adopted else 'NOT CI-SEPARATED'} "
          f"(delta {100*(r_full['acc']-r_adopted['acc']):+.1f}pp)")

    if r_ens is not None:
        sep_ens_vs_sl = gate._ci_separated(r_ens["ci"], r_sl["ci"])
        print(f"  SC+TPS+SMOOTH ENSEMBLE vs SC+TPS SHORTLIST: {100*r_ens['acc']:.1f}% vs "
              f"{100*r_sl['acc']:.1f}% -- {'CI-SEPARATED' if sep_ens_vs_sl else 'NOT CI-SEPARATED'} "
              f"(delta {100*(r_ens['acc']-r_sl['acc']):+.1f}pp)")

    no_cap_msg = (f"none -- full R={R_TARGET}/{len(POWER_ALPHABETS)}-alphabet target scope "
                  f"completed within budget.")
    print(f"\n  BUDGET NOTES: {budget_notes if budget_notes else no_cap_msg}")

    import sys as _sys
    donkey0 = "torch" not in _sys.modules
    print(f"  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")

    total_elapsed = time.time() - t0
    print(f"\n  total runtime: {total_elapsed:.1f}s (budget {RUNTIME_BUDGET_SECONDS:.0f}s + "
          f"{600 - RUNTIME_BUDGET_SECONDS:.0f}s import/report headroom)")
    print(SEP)
    print("  OVERALL: PASS" if donkey0 and sat_pass is not False else "  OVERALL: FAIL")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
