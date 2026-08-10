"""OMNIGLOT RUN 17b -- FULL-N COMPLETION of RUN 17 (same protocol, same seed, same arms).

RUN 17's own gate (scripts/jabberwock_omniglot_run17_close.py, logged in
results/omniglot_gate_run17_close.log) hit its hard deadline at 340/400 main-cache episodes
and shed the PARSE-MARGINAL arm to zero episodes (the budget logic shed the CHEAPEST arm
first -- measured 1.1s/block vs the main path's ~19s/block -- an ordering error this run
corrects). Two phases were pure overhead a second run does not need to repeat:

  - the PILOT (RUN 17 already measured every per-block cost -- reused here as constants);
  - the TUNING grid search (RUN 17's own Phase 2.5 already picked the winning weights on the
    DISJOINT tuning split -- Malayalam/Manipuri/Mongolian/Old_Church_Slavonic_(Cyrillic)/
    Oriya, 100 episodes, zero TEST-alphabet contact, logged + asserted there). The weights
    are therefore FROZEN DATA in this run: (sc_w, tps_w, smooth_w) = (1.0, 0.5, 0.5).

This run: identical LEARN (cap 1500, saturation-verified), identical block specs (the SAME
POWER_SEED rng consumed in the SAME alphabet x repeat order -- byte-identical exemplar/query
drawer draws to RUN 15 Phase 1 / RUN 16 / RUN 17), ALL 20 main blocks FIRST (arms 1-5 at the
full n=400 -- the non-negotiable core is completed before anything else can consume budget),
THEN the 20 parse-marginal blocks (LEVER 4 at full n=400; specs are recorded during the main
pass, so a deadline here can only shorten the parse arm, never arms 1-5).

Every classification decision is a held Term (see RUN 17's own module docstring; this script
adds no new decision surface). donkey=0.

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run17b_completion.py
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
import scripts.jabberwock_omniglot_run17_close as r17
from domains import omniglot_world as ow

SEP = "=" * 92

FROZEN_WEIGHTS = (1.0, 0.5, 0.5)      # RUN 17 Phase 2.5's winning weights (disjoint tuning
                                       # split, 100 episodes, tuning acc 75.0% -- see
                                       # results/omniglot_gate_run17_close.log). DATA, frozen.
RUNTIME_BUDGET_SECONDS = 560.0         # ~40s headroom under the 600s foreground cap.
FAMILY_A_ANCHOR = r17.FAMILY_A_ANCHOR
RUN15_ADOPTED = r17.RUN15_ADOPTED
RUN16_SCTPS_FULL = r17.RUN16_SCTPS_FULL


def main():
    t0 = time.time()
    print(SEP)
    print("OMNIGLOT RUN 17b -- FULL-N COMPLETION: arms 1-5 at the exact n=400 RUN 15 Phase 1")
    print("scope (RUN 17 stopped honestly at 340) + PARSE MARGINAL at full scope (RUN 17's")
    print("budget logic shed the cheapest arm first -- 0 episodes -- corrected here).")
    print(SEP)

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    print(f"\n  LEARN caps (RUN 16/17's own reduced, saturation-verified cap): "
          f"{gate.LEARN_ALPHABETS_N} background alphabets, drawers "
          f"{gate.LEARN_DRAWERS[0]}-{gate.LEARN_DRAWERS[-1]}, capped at "
          f"{r17.LEARN_STROKE_CAP} pen-down strokes. ink-decode params: {gate.DK}")
    print(f"  FROZEN FUSION WEIGHTS (RUN 17 Phase 2.5, disjoint tuning split, zero TEST "
          f"contact): sc_w={FROZEN_WEIGHTS[0]}, tps_w={FROZEN_WEIGHTS[1]}, "
          f"smooth_w={FROZEN_WEIGHTS[2]}")

    print(f"\n{SEP}\n  PHASE 1: LEARN\n{SEP}")
    lr = gate.run_learn(s, ag, native, learn_alphabets, gate.LEARN_DRAWERS,
                         r17.LEARN_STROKE_CAP, gate.DK, gate.GROWTH_WINDOW)
    growth = lr["growth"]
    print(f"  processed {lr['n_strokes']} pen-down strokes "
          f"({lr['n_degenerate_skipped']} degenerate skipped) in {lr['elapsed']:.1f}s.")
    sat_pass = None
    if len(growth) >= 3:
        first = np.mean([g["new_quanta"] for g in growth[:1]])
        last = np.mean([g["new_quanta"] for g in growth[-2:]])
        sat_pass = last <= max(3.0, 0.3 * first) if first > 0 else True
        print(f"  saturation check: first-window new={first:.1f} -> last-2-windows mean "
              f"new={last:.1f}  VERDICT: {'PASS' if sat_pass else 'FAIL'}")
    import domains.stroke_codebook as sc
    print(f"  final LEARN codebook size: {len(sc._existing_names(s, 'stroke'))} stroke quanta "
          f"(RUN 15/16/17 all produced 7).")

    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= r17.WAY)
    test_alphabets = qualifying[:r17.N_TEST_ALPHABETS]
    print(f"\n  TEST alphabets (sorted-name {r17.N_TEST_ALPHABETS}-prefix, RUN 15/16/17's own "
          f"set): {test_alphabets}")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2: MAIN ARMS AT FULL n -- all 20 (alphabet x repeat) blocks, specs recorded for
    #  the parse pass below. The rng consumption order is byte-identical to RUN 15/16/17.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2: MAIN ARMS (target n="
          f"{len(test_alphabets) * r17.R_TARGET * r17.WAY})\n{SEP}")
    cache: dict = {}
    official_rng = np.random.default_rng(r17.POWER_SEED)
    main_records = []
    specs_done = []
    hard_deadline = t0 + RUNTIME_BUDGET_SECONDS
    budget_notes = []
    stopped_early = None
    for alph in test_alphabets:
        for r in range(r17.R_TARGET):
            if time.time() > hard_deadline:
                stopped_early = (alph, r)
                break
            spec = r17._block_spec(alph, official_rng, r17.WAY, r17.EPISODES_PER_ALPHABET)
            blk = r17._run_block_main(s, native, gate.DK, cache, spec, r17.WAY, FROZEN_WEIGHTS)
            main_records.extend(blk["records"])
            specs_done.append((alph, r, spec))
        if stopped_early:
            break
    if stopped_early:
        note = (f"HARD DEADLINE during the MAIN pass at {stopped_early!r} -- "
                f"{len(main_records)} episodes scored (honest, not a crash).")
        print(f"  {note}")
        budget_notes.append(note)
    print(f"  main pass complete: {len(main_records)} episodes over {len(specs_done)} blocks "
          f"in {time.time() - t0:.0f}s total so far.")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 3: PARSE-MARGINAL ARM over the SAME recorded specs (identical episodes).
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 3: PARSE MARGINAL (same episodes, LEVER 4)\n{SEP}")
    parse_records = []
    parse_stopped = None
    for alph, r, spec in specs_done:
        if time.time() > hard_deadline:
            parse_stopped = (alph, r)
            break
        pblk = r17._run_block_parse(spec, r17.WAY)
        parse_records.extend(pblk["records"])
    if parse_stopped:
        note = (f"HARD DEADLINE during the PARSE pass at {parse_stopped!r} -- "
                f"{len(parse_records)} parse episodes scored (arms 1-5 already complete).")
        print(f"  {note}")
        budget_notes.append(note)
    print(f"  parse pass complete: {len(parse_records)} episodes.")

    # ------------------------------------------------------------------------------------- #
    #  REPORT
    # ------------------------------------------------------------------------------------- #
    trues = [r_["true"] for r_ in main_records]

    def _report(name, preds, trues_):
        acc, ci, k = r17._acc_ci(preds, trues_)
        shuf = list(trues_)
        np.random.default_rng(r17.POWER_SEED + 1).shuffle(shuf)
        acc_s, _, _ = r17._acc_ci(preds, shuf)
        print(f"  {name:<26} n={len(trues_):>4}  k={k:>3}  acc={100*acc:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]  shuffled={100*acc_s:5.1f}%")
        return dict(acc=acc, ci=ci, k=k, n=len(trues_))

    print(f"\n  {len(main_records)} main episodes / {len(parse_records)} parse episodes.\n")
    r_control = _report("CONTROL (adopted)", [x["w_adopted"] for x in main_records], trues)
    r_full = _report("SC+TPS FULL DWELL", [x["w_full"] for x in main_records], trues)
    r_tuned = _report("TUNED FUSION", [x["w_tuned"] for x in main_records], trues)
    r_smooth = _report("+SMOOTH (full dwell)", [x["w_smooth"] for x in main_records], trues)
    r_single = _report("+SCTPS (full dwell)", [x["w_single"] for x in main_records], trues)
    if parse_records:
        p_true = [x["true"] for x in parse_records]
        r_parse = _report("PARSE MARGINAL", [x["w_parse"] for x in parse_records], p_true)
    else:
        r_parse = None
        print(f"  {'PARSE MARGINAL':<26} 0 episodes (deadline) -- see BUDGET NOTES.")

    print(f"\n{SEP}\n  VERDICTS (n={len(main_records)})\n{SEP}")
    ci_c = r_control["ci"]
    overlaps_run15 = not (ci_c[1] < RUN15_ADOPTED["ci"][0] or RUN15_ADOPTED["ci"][1] < ci_c[0])
    print(f"  CONTROL REPRODUCTION: {100*r_control['acc']:.1f}% "
          f"{[round(100*x,1) for x in ci_c]} vs RUN 15's 26.8% [22.6, 31.3] (n=400) -- "
          f"{'CI-OVERLAP (consistent)' if overlaps_run15 else 'CI-SEPARATED (investigate)'}")

    def _verdict(name, res, base_ci, base_label):
        sep = gate._ci_separated(res["ci"], base_ci)
        print(f"  {name} vs {base_label}: -- "
              f"{'CI-SEPARATED' if sep else 'NOT CI-SEPARATED'}")
        return sep

    _verdict(f"SC+TPS FULL DWELL {100*r_full['acc']:.1f}%", r_full, ci_c, "CONTROL")
    _verdict(f"SC+TPS FULL DWELL {100*r_full['acc']:.1f}%", r_full, RUN16_SCTPS_FULL["ci"],
             "RUN 16's n=200 73.5% [67.0, 79.1]")
    _verdict(f"TUNED FUSION {100*r_tuned['acc']:.1f}%", r_tuned, r_full["ci"], "FULL DWELL")
    _verdict(f"+SMOOTH {100*r_smooth['acc']:.1f}%", r_smooth, r_full["ci"], "FULL DWELL")
    _verdict(f"+SCTPS {100*r_single['acc']:.1f}%", r_single, r_full["ci"], "FULL DWELL")
    if r_parse is not None:
        _verdict(f"PARSE MARGINAL {100*r_parse['acc']:.1f}%", r_parse, r_full["ci"],
                 "FULL DWELL")

    print(f"\n  FAMILY-A ANCHOR ({100*FAMILY_A_ANCHOR:.1f}%) CI-TOUCH CHECK:")
    arms = [("SC+TPS FULL DWELL", r_full), ("TUNED FUSION", r_tuned), ("+SMOOTH", r_smooth),
            ("+SCTPS", r_single)] + ([("PARSE MARGINAL", r_parse)] if r_parse else [])
    for name, res in arms:
        touch = r17._touches(res["ci"], FAMILY_A_ANCHOR)
        print(f"    {name:<24}: CI {[round(100*x,1) for x in res['ci']]} "
              f"{'TOUCHES' if touch else 'does NOT touch'} the anchor.")
    best_arm = max(arms, key=lambda kv: kv[1]["acc"])
    print(f"\n  BEST ARM: {best_arm[0]} at {100*best_arm[1]['acc']:.1f}% "
          f"{[round(100*x,1) for x in best_arm[1]['ci']]}")

    print(f"\n  BUDGET NOTES: {budget_notes if budget_notes else 'none -- full scope completed.'}")
    donkey0 = "torch" not in sys.modules
    print(f"  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")
    print(f"\n  total runtime: {time.time() - t0:.1f}s (budget {RUNTIME_BUDGET_SECONDS:.0f}s)")
    print(SEP)
    print("  OVERALL: PASS" if donkey0 and sat_pass is not False else "  OVERALL: FAIL")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
