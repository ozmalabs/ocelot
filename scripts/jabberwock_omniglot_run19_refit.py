"""OMNIGLOT RUN 19 -- EARNED PARSE JOINS THE MARGINALIZATION + TOKEN-REFIT (scratchpad/
HANDWRITING_DESIGN.md's section of the same name), off RUN 17b's 80.5% [76.3, 84.1] parse-
marginal headline (results/omniglot_gate_run17_close.log) which itself BYPASSES the earned
stroke-codebook layer entirely (its own `stage_parse_char` re-segments every character at a
fixed theta grid, never touching `ink_decode.decode_ink`'s own learned segmentation). Standing
rules bind this run (CLAUDE.md): POWER THE GATE BEFORE THE ENDGAME, mechanism != benchmark value
(report both), eval-subset coverage is part of every claim, every classification decision is a
held Term (audits scan `domains/abs_read.py`), and a tuning-free run (no new weights -- every
DEFAULT_PARSE_*/DEFAULT_REFIT_BETA constant this run uses is REUSED verbatim, never re-tuned
here).

FIVE ARMS, off the SAME (alphabet, repeat) block spec / decode cache RUN 15/16/17/17b already
established (`jabberwock_omniglot_run17_close._block_spec`, the SAME `POWER_SEED` rng consumed
in the SAME order -- byte-identical exemplar/query drawer draws):

  1. CONTROL -- `domains.abs_read.stage_parse_char`/`parse_marginal_verdict`, theta grid ONLY
     (55/70/85), ALL `way`=20 candidates staged -- byte-identical to RUN 17b's own PARSE
     MARGINAL arm. MUST reproduce 80.5% [76.3, 84.1].
  2. +EARNED-PARSE-HYPOTHESIS (LEVER 1a) -- the SAME theta grid PLUS `stage_parse_char`'s new
     `earned_stroke_points` param (the decode cache's own already-decoded per-stroke spans,
     `ink_decode.decode_ink`'s lattice output, no second decode), ALL 20 candidates -- LEARN
     finally contributes structure to the verdict instead of being bypassed.
  3. SHORTLIST+MARGINAL (LEVER 1b, the budget curve) -- theta grid ONLY, staged over the
     `abs_rerank_targeted(delta=0, use_appearance=True)` shortlist (the SAME "adopted" control
     RUN 15/16/17 already compute) instead of all 20 candidates; ALSO reported at a WIDER
     shortlist (`propose_top_k(k=10)`) as the curve's second point -- at 20-way the budget
     saving is minor by construction, the arm exists to prove the layered architecture (search
     narrows the marginalization's candidate pool without changing its own machinery).
  4. TOKEN-REFIT (LEVER 2) -- `domains.abs_read.program_refit_rerank`, a GENERAL directional
     program-explains-observation faculty (knows NOTHING of characters) over the SAME delta=0+
     appearance shortlist, treating each candidate's own RAW per-stroke points (the decode
     cache's `stroke_points`, unsegmented) as the "program" fitted to the query's own raw
     per-stroke points.
  5. TOKEN-REFIT + MARGINAL-OVER-PARSES (the full stack) -- `program_refit_rerank` over the
     SAME shortlist, but the "parts" on both sides are LEVER 1a's own RICHER hypothesis set:
     the theta-grid canonical parts (`canonical_parse.canonical_parts` at 55/70/85) UNIONED
     with the earned segmentation's own parts (`abs_read._earned_parts_from_stroke_points`) --
     the directional TPS-fit metric (lever 2) operating over the multi-grain parse
     representation (lever 1a), rather than raw unsegmented strokes. This is THIS SCRIPT's own
     explicit interpretation of "token-refit with 1a's hypothesis set" (the design names the
     combination but not its exact wiring) -- reported honestly as such.

Arms 1-2 (and the CORE trio 1/2/4, per the launch instructions) are the NON-NEGOTIABLE floor and
are NEVER scope-capped by this script's own budget logic; if the projected runtime exceeds
budget, arms 3 and 5 are shed FIRST (in that order -- 3's wide-shortlist data point first, then
3 entirely, then 5), the CORRECT "cheapest-per-information arm last" shed order given the launch
instruction that the core trio (control / earned-parse / token-refit) must survive; only if the
core trio ITSELF cannot fit does R (repeats) drop from 2 to 1, exactly RUN 17's own precedent.

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /usr/bin/python3 scripts/jabberwock_omniglot_run19_refit.py
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

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run17_close as r17
from domains import abs_read as ar
from domains import canonical_parse as cp
from domains import omniglot_world as ow

SEP = "=" * 92

WAY = r17.WAY
EPISODES_PER_ALPHABET = r17.EPISODES_PER_ALPHABET
R_TARGET = r17.R_TARGET
POWER_SEED = r17.POWER_SEED
N_TEST_ALPHABETS = r17.N_TEST_ALPHABETS
LEARN_STROKE_CAP = r17.LEARN_STROKE_CAP
FAMILY_A_ANCHOR = r17.FAMILY_A_ANCHOR
RUN17B_PARSE_MARGINAL = {"acc": 0.805, "ci": (0.763, 0.841), "n": 400}   # results/
                                                                          # omniglot_gate_run17_
                                                                          # close.log's RUN 17b
                                                                          # completion block.

# Family A's own marginal-inference recipe, REUSED VERBATIM (tuning-free run: no new weights).
PARSE_THETAS = ar.DEFAULT_PARSE_THETAS
PARSE_WHOLE_N = ar.DEFAULT_PARSE_WHOLE_N
PARSE_PER_PART = ar.DEFAULT_PARSE_PER_PART
PARSE_PART_W, PARSE_SC_W, PARSE_BETA = r17.PARSE_PART_W, r17.PARSE_SC_W, r17.PARSE_BETA
WIDE_SHORTLIST_K = ar.DEFAULT_WIDEN_TO   # 10 -- reused verbatim, the SAME "proposal ranks up to
                                          # W" constant `abs_rerank_targeted`'s own widen lever
                                          # already uses; not a new weight.
REFIT_BETA = ar.DEFAULT_REFIT_BETA       # reused verbatim (recognition_graph's own default).

RUNTIME_BUDGET_SECONDS = 520.0           # RUN 17's own budget value, reused verbatim (~80s
                                          # headroom under the 600s foreground cap) -- a live
                                          # calibration pilot (WAY=20, small LEARN) measured
                                          # decode ~11s/block + core-trio arms ~7.8s/block,
                                          # projecting ~490s for the CORE TRIO at full n=400,
                                          # comfortably inside this budget.


def _rich_parts(path: str, stroke_points: list, thetas, per_part: int) -> list:
    """LEVER 1a's hypothesis set, as plain point-set "parts" (no graph): theta-grid canonical
    parts (`canonical_parse.canonical_parts`, re-reading the file's own raw strokes -- cheap
    numpy corner-split, no re-decode) UNIONED with the earned segmentation's own parts
    (`abs_read._earned_parts_from_stroke_points`, off the ALREADY-decoded `stroke_points` the
    caller's own decode cache carries -- no second ink-decode). Used ONLY by the "full stack"
    arm's `program_refit_rerank` call -- this function performs no ranking/decision itself,
    purely mechanical part collection."""
    strokes = ow.load_strokes(path)
    parts = []
    for th in thetas:
        parts.extend(p.tolist() for p in cp.canonical_parts(strokes, th, per_part=per_part))
    parts.extend(p.tolist() for p in ar._earned_parts_from_stroke_points(stroke_points, per_part))
    return parts


def _stage_and_verdict(exemplar_paths, exemplar_stroke_points, query_path, query_stroke_points,
                        candidate_idxs, *, use_earned: bool) -> int:
    """Mechanical scratch-substrate staging + ONE `parse_marginal_verdict` evaluate, shared by
    arms 1/2/3 (they differ only in WHICH candidates are staged and whether the earned
    ParseHyp is attached) -- never a ranking of this function's own; the classification
    decision is `parse_marginal_verdict`'s own held Argmax."""
    scratch = srs.Substrate()
    cand_of: dict[int, int] = {}
    for ci in candidate_idxs:
        kwargs = dict(thetas=PARSE_THETAS, whole_n=PARSE_WHOLE_N, per_part=PARSE_PER_PART,
                      name=str(ci))
        if use_earned:
            kwargs["earned_stroke_points"] = exemplar_stroke_points[ci]
        node = ar.stage_parse_char(scratch, exemplar_paths[ci], is_query=False, **kwargs)
        cand_of[node] = ci
    q_kwargs = dict(thetas=PARSE_THETAS, whole_n=PARSE_WHOLE_N, per_part=PARSE_PER_PART)
    if use_earned:
        q_kwargs["earned_stroke_points"] = query_stroke_points
    qn = ar.stage_parse_char(scratch, query_path, is_query=True, **q_kwargs)
    winner = ar.parse_marginal_verdict(scratch, qn, part_w=PARSE_PART_W, sc_w=PARSE_SC_W,
                                        beta=PARSE_BETA)
    return cand_of.get(winner, -1) if winner is not None else -1


def _episode_run19(s, native, dk, qd, exemplar_composed, exemplar_stroke_points,
                    exemplar_paths, query_path, way: int, run_lever3: bool, run_lever5: bool,
                    run_wide: bool) -> dict:
    t_parts = {}

    t0 = time.time()
    adopted = ar.abs_rerank_targeted(
        s, qd["composed_sig"], qd["stroke_points"], exemplar_composed, exemplar_stroke_points,
        delta=0.0, use_widen=False, use_appearance=True, turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
        segments=dk["segments"])
    shortlist = list(adopted.get("shortlist0") or [])
    t_parts["adopted"] = time.time() - t0

    t0 = time.time()
    w_control = _stage_and_verdict(exemplar_paths, exemplar_stroke_points, query_path,
                                    qd["stroke_points"], range(way), use_earned=False)
    t_parts["parse_control"] = time.time() - t0

    t0 = time.time()
    w_earned = _stage_and_verdict(exemplar_paths, exemplar_stroke_points, query_path,
                                   qd["stroke_points"], range(way), use_earned=True)
    t_parts["parse_earned"] = time.time() - t0

    w_shortlist = w_wide = -1
    wide_shortlist: list = []
    if run_lever3 and shortlist:
        t0 = time.time()
        w_shortlist = _stage_and_verdict(exemplar_paths, exemplar_stroke_points, query_path,
                                          qd["stroke_points"], shortlist, use_earned=False)
        t_parts["parse_shortlist"] = time.time() - t0
        if run_wide:
            t0 = time.time()
            wide_shortlist = ar.propose_top_k(native, qd["composed_sig"], exemplar_composed,
                                               k=WIDE_SHORTLIST_K)
            w_wide = _stage_and_verdict(exemplar_paths, exemplar_stroke_points, query_path,
                                         qd["stroke_points"], wide_shortlist, use_earned=False)
            t_parts["parse_wide"] = time.time() - t0

    w_refit = -1
    active = shortlist if shortlist else list(range(way))
    t0 = time.time()
    raw_program_parts = [[item[0] for item in exemplar_stroke_points[ci]] for ci in active]
    raw_program_by_ci = [[] for _ in range(way)]
    for pos, ci in enumerate(active):
        raw_program_by_ci[ci] = raw_program_parts[pos]
    raw_observed_parts = [item[0] for item in qd["stroke_points"]]
    refit = ar.program_refit_rerank(native, raw_program_by_ci, raw_observed_parts, active,
                                     beta_corr=REFIT_BETA)
    w_refit = refit["winner"] if refit["winner"] is not None else -1
    t_parts["token_refit"] = time.time() - t0

    w_refit_full = -1
    if run_lever5:
        t0 = time.time()
        rich_program_by_ci = [[] for _ in range(way)]
        for ci in active:
            rich_program_by_ci[ci] = _rich_parts(exemplar_paths[ci], exemplar_stroke_points[ci],
                                                  PARSE_THETAS, PARSE_PER_PART)
        rich_observed_parts = _rich_parts(query_path, qd["stroke_points"], PARSE_THETAS,
                                           PARSE_PER_PART)
        refit_full = ar.program_refit_rerank(native, rich_program_by_ci, rich_observed_parts,
                                              active, beta_corr=REFIT_BETA)
        w_refit_full = refit_full["winner"] if refit_full["winner"] is not None else -1
        t_parts["token_refit_full_stack"] = time.time() - t0

    return dict(w_control=w_control, w_earned=w_earned, w_shortlist=w_shortlist, w_wide=w_wide,
                w_refit=w_refit, w_refit_full=w_refit_full, shortlist_size=len(shortlist),
                wide_size=len(wide_shortlist), timing=t_parts)


def _run_block(s, native, dk, cache, spec, way, run_lever3, run_lever5, run_wide) -> dict:
    t0 = time.time()
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, dk)
                 for ci in range(way)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]
    exemplar_stroke_points = [e["stroke_points"] for e in exemplars]
    exemplar_paths = [drawer_files[ci][ex_drawer] for ci in range(way)]
    records = []
    for qi, q_drawer in spec["queries"]:
        query_path = drawer_files[qi][q_drawer]
        qd = gate.decode_char_signature(s, query_path, cache, dk)
        rec = _episode_run19(s, native, dk, qd, exemplar_composed, exemplar_stroke_points,
                              exemplar_paths, query_path, way, run_lever3, run_lever5, run_wide)
        rec["true"] = qi
        records.append(rec)
    return dict(records=records, elapsed=time.time() - t0)


def main():
    t0 = time.time()
    print(SEP)
    print("OMNIGLOT RUN 19 -- EARNED PARSE JOINS THE MARGINALIZATION + TOKEN-REFIT: LEVER 1a")
    print("(earned-parse hypothesis), LEVER 1b (shortlist+marginal budget curve), LEVER 2")
    print("(token-refit AbS), and the full stack, off RUN 17b's 80.5% parse-marginal headline.")
    print(SEP)

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    print(f"\n  LEARN caps (RUN 15/16/17's own reduced, saturation-verified cap): "
          f"{gate.LEARN_ALPHABETS_N} background alphabets, drawers "
          f"{gate.LEARN_DRAWERS[0]}-{gate.LEARN_DRAWERS[-1]}, capped at {LEARN_STROKE_CAP} "
          f"pen-down strokes. ink-decode params: {gate.DK}")
    print(f"  Parse recipe (Family A's own, REUSED VERBATIM -- tuning-free run): thetas="
          f"{PARSE_THETAS}, whole_n={PARSE_WHOLE_N}, per_part={PARSE_PER_PART}, "
          f"part_w={PARSE_PART_W}, sc_w={PARSE_SC_W}, beta={PARSE_BETA}. "
          f"wide_shortlist_k={WIDE_SHORTLIST_K}, refit_beta={REFIT_BETA}.")

    print(f"\n{SEP}\n  PHASE 1: LEARN\n{SEP}")
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
        print(f"  saturation check: first-window new={first:.1f} -> last-2-windows mean "
              f"new={last:.1f}  VERDICT: {'PASS' if sat_pass else 'FAIL'}")
    import domains.stroke_codebook as sc
    final_codebook = len(sc._existing_names(s, "stroke"))
    print(f"  final LEARN codebook size: {final_codebook} stroke quanta "
          f"(RUN 15/16/17/17b all produced 7).")

    qualifying = sorted(a for a in ow.alphabets("evaluation")
                        if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]
    print(f"\n  TEST alphabets (sorted-name {N_TEST_ALPHABETS}-prefix, RUN 15/16/17/17b's own "
          f"set): {test_alphabets}")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2: PILOT + RUNTIME BUDGET PROJECTION -- ONE block (20 episodes), all six arms,
    #  timed per-episode-part (`_episode_run19`'s own `timing` dict) so the shed decision below
    #  is grounded in MEASURED per-arm cost, not a guess.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2: PILOT + RUNTIME BUDGET PROJECTION\n{SEP}")
    cache: dict = {}
    pilot_rng = np.random.default_rng(POWER_SEED)
    pilot_spec = r17._block_spec(test_alphabets[0], pilot_rng, WAY, EPISODES_PER_ALPHABET)
    pilot = _run_block(s, native, gate.DK, cache, pilot_spec, WAY, run_lever3=True,
                        run_lever5=True, run_wide=True)
    n_blocks = len(test_alphabets) * R_TARGET
    per_part_totals: dict = {}
    for rec in pilot["records"]:
        for k, v in rec["timing"].items():
            per_part_totals[k] = per_part_totals.get(k, 0.0) + v
    print(f"  PILOT block ({test_alphabets[0]!r}, repeat 0, {WAY} episodes, ALL SIX ARMS): "
          f"{pilot['elapsed']:.1f}s total. Per-arm-part totals (this one block): "
          + ", ".join(f"{k}={v:.2f}s" for k, v in per_part_totals.items()))

    # PILOT-SCALE (n=WAY, ONE block, UNPOWERED) per-arm accuracy -- a mechanism-check data
    # point for whatever arm(s) the budget shedding below drops from the POWERED test, so the
    # shortlist budget curve (LEVER 1b) and the token-refit/full-stack comparison (LEVER 2) are
    # still reported even if they cannot run at full n=400. Explicitly labeled unpowered.
    pilot_trues = [r_["true"] for r_ in pilot["records"]]

    def _pilot_report(name, preds):
        acc, ci, k = r17._acc_ci(preds, pilot_trues)
        print(f"    {name:<38} n={len(pilot_trues):>3}  k={k:>2}  acc={100*acc:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]")
        return dict(acc=acc, ci=ci, k=k, n=len(pilot_trues))

    print(f"\n  PILOT-SCALE per-arm accuracy (n={WAY}, ONE block, UNPOWERED -- mechanism check "
          f"only, not a claim):")
    _pilot_report("CONTROL (parse-marginal)", [x["w_control"] for x in pilot["records"]])
    _pilot_report("+EARNED-PARSE (1a)", [x["w_earned"] for x in pilot["records"]])
    _pilot_report("SHORTLIST+MARGINAL (1b)", [x["w_shortlist"] for x in pilot["records"]])
    _pilot_report("SHORTLIST+MARGINAL (wide, k=10)", [x["w_wide"] for x in pilot["records"]])
    _pilot_report("TOKEN-REFIT (2)", [x["w_refit"] for x in pilot["records"]])
    _pilot_report("TOKEN-REFIT + MARGINAL (full stack)",
                  [x["w_refit_full"] for x in pilot["records"]])
    pilot_mean_shortlist = float(np.mean([x["shortlist_size"] for x in pilot["records"]]))
    pilot_mean_wide = float(np.mean([x["wide_size"] for x in pilot["records"]]))
    print(f"    -- PILOT mean shortlist size: {pilot_mean_shortlist:.2f} / {WAY}; mean "
          f"wide-shortlist size: {pilot_mean_wide:.2f} / {WAY} (the LEVER 1b budget curve's "
          f"two points, vs CONTROL's full {WAY}-way staging).")

    elapsed_so_far = time.time() - t0
    per_block_full = pilot["elapsed"]
    per_block_core = per_block_full - per_part_totals.get("parse_shortlist", 0.0) \
        - per_part_totals.get("parse_wide", 0.0) - per_part_totals.get("token_refit_full_stack", 0.0)
    per_block_no_wide = per_block_full - per_part_totals.get("parse_wide", 0.0)

    projected_full = elapsed_so_far + per_block_full * n_blocks
    projected_no_wide = elapsed_so_far + per_block_no_wide * n_blocks
    projected_core_plus5 = elapsed_so_far + (per_block_full - per_part_totals.get("parse_wide", 0.0)
                                              - per_part_totals.get("parse_shortlist", 0.0)) * n_blocks
    projected_core_only = elapsed_so_far + per_block_core * n_blocks
    print(f"\n  projections for {n_blocks} blocks ({R_TARGET} x {len(test_alphabets)} "
          f"alphabets): ALL SIX ARMS {projected_full:.0f}s | drop wide-shortlist "
          f"{projected_no_wide:.0f}s | drop lever-3 entirely (keep full-stack) "
          f"{projected_core_plus5:.0f}s | CORE TRIO ONLY (control/earned/refit) "
          f"{projected_core_only:.0f}s  vs {RUNTIME_BUDGET_SECONDS:.0f}s budget.")

    budget_notes = []
    run_lever3 = run_lever5 = run_wide = True
    r_used = R_TARGET
    if projected_full > RUNTIME_BUDGET_SECONDS:
        run_wide = False
        note = (f"projected ALL-SIX {projected_full:.0f}s > {RUNTIME_BUDGET_SECONDS:.0f}s "
                f"budget -- shedding lever-3's WIDE-shortlist data point first (projected "
                f"{projected_no_wide:.0f}s).")
        print(f"  {note}")
        budget_notes.append(note)
        if projected_no_wide > RUNTIME_BUDGET_SECONDS:
            run_lever3 = False
            note2 = (f"still over budget -- shedding LEVER 3 (shortlist+marginal) entirely, "
                     f"keeping the full stack (projected {projected_core_plus5:.0f}s).")
            print(f"  {note2}")
            budget_notes.append(note2)
            if projected_core_plus5 > RUNTIME_BUDGET_SECONDS:
                run_lever5 = False
                note3 = (f"still over budget -- shedding the FULL STACK arm too, keeping only "
                         f"the non-negotiable CORE TRIO (control/earned-parse/token-refit) "
                         f"(projected {projected_core_only:.0f}s).")
                print(f"  {note3}")
                budget_notes.append(note3)
                if projected_core_only > RUNTIME_BUDGET_SECONDS:
                    r_used = 1
                    projected_r1 = elapsed_so_far + per_block_core * len(test_alphabets) * r_used
                    note4 = (f"even the CORE TRIO alone projects over budget at R={R_TARGET} -- "
                             f"reducing to R={r_used} (projected {projected_r1:.0f}s), the "
                             f"LAST resort per the launch instruction 'cap arms not n'.")
                    print(f"  {note4}")
                    budget_notes.append(note4)
    else:
        print(f"  within budget -- running ALL SIX per-episode computations for the full "
              f"scope (R={R_TARGET}, {len(test_alphabets)} alphabets).")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 3: POWERED TEST
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 3: POWERED TEST (target n={len(test_alphabets)*r_used*WAY})\n{SEP}")
    official_rng = np.random.default_rng(POWER_SEED)
    all_records = []
    hard_deadline = t0 + RUNTIME_BUDGET_SECONDS
    stopped_early = None
    for alph in test_alphabets:
        for r in range(r_used):
            if time.time() > hard_deadline:
                stopped_early = (alph, r)
                break
            spec = r17._block_spec(alph, official_rng, WAY, EPISODES_PER_ALPHABET)
            blk = _run_block(s, native, gate.DK, cache, spec, WAY, run_lever3, run_lever5,
                              run_wide)
            all_records.extend(blk["records"])
        if stopped_early:
            break
    if stopped_early:
        note = (f"HARD DEADLINE reached at {stopped_early!r} -- stopped early with "
                f"{len(all_records)} episodes scored (honest, not a crash).")
        print(f"  {note}")
        budget_notes.append(note)

    trues = [r_["true"] for r_ in all_records]

    def _report(name, preds, trues_):
        acc, ci, k = r17._acc_ci(preds, trues_)
        shuf = list(trues_)
        np.random.default_rng(POWER_SEED + 1).shuffle(shuf)
        acc_s, _, _ = r17._acc_ci(preds, shuf)
        print(f"  {name:<32} n={len(trues_):>4}  k={k:>3}  acc={100*acc:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]  shuffled={100*acc_s:5.1f}%")
        return dict(acc=acc, ci=ci, k=k, n=len(trues_))

    print(f"\n  {len(all_records)} episodes scored "
          f"(lever3={'on' if run_lever3 else 'off'}, wide={'on' if run_wide else 'off'}, "
          f"lever5={'on' if run_lever5 else 'off'}, R={r_used}).\n")
    r_control = _report("CONTROL (parse-marginal)", [x["w_control"] for x in all_records], trues)
    r_earned = _report("+EARNED-PARSE (1a)", [x["w_earned"] for x in all_records], trues)
    r_refit = _report("TOKEN-REFIT (2)", [x["w_refit"] for x in all_records], trues)
    if run_lever3:
        r_shortlist = _report("SHORTLIST+MARGINAL (1b)",
                              [x["w_shortlist"] for x in all_records], trues)
        mean_shortlist = float(np.mean([x["shortlist_size"] for x in all_records]))
        print(f"    -- mean shortlist size: {mean_shortlist:.2f} / {WAY} candidates "
              f"(budget saving vs CONTROL's full {WAY}-way staging).")
        if run_wide:
            r_wide = _report("SHORTLIST+MARGINAL (wide, k=10)",
                             [x["w_wide"] for x in all_records], trues)
            mean_wide = float(np.mean([x["wide_size"] for x in all_records]))
            print(f"    -- mean wide-shortlist size: {mean_wide:.2f} / {WAY} candidates.")
        else:
            r_wide = None
    else:
        r_shortlist = r_wide = None
    if run_lever5:
        r_full_stack = _report("TOKEN-REFIT + MARGINAL (full stack)",
                               [x["w_refit_full"] for x in all_records], trues)
    else:
        r_full_stack = None

    print(f"\n{SEP}\n  VERDICTS (n={len(all_records)})\n{SEP}")
    ci_c = r_control["ci"]
    overlaps_17b = not (ci_c[1] < RUN17B_PARSE_MARGINAL["ci"][0]
                        or RUN17B_PARSE_MARGINAL["ci"][1] < ci_c[0])
    print(f"  CONTROL REPRODUCTION: {100*r_control['acc']:.1f}% "
          f"{[round(100*x,1) for x in ci_c]} vs RUN 17b's 80.5% [76.3, 84.1] (n=400) -- "
          f"{'CI-OVERLAP (consistent)' if overlaps_17b else 'CI-SEPARATED (investigate)'}")

    def _verdict(name, res, base_ci, base_label):
        sep = gate._ci_separated(res["ci"], base_ci)
        print(f"  {name} vs {base_label}: {100*res['acc']:.1f}% -- "
              f"{'CI-SEPARATED' if sep else 'NOT CI-SEPARATED'}")
        return sep

    _verdict("+EARNED-PARSE (1a)", r_earned, ci_c, "CONTROL")
    if r_shortlist is not None:
        _verdict("SHORTLIST+MARGINAL (1b)", r_shortlist, ci_c, "CONTROL")
    if r_wide is not None:
        _verdict("SHORTLIST+MARGINAL (wide)", r_wide, ci_c, "CONTROL")
    _verdict("TOKEN-REFIT (2)", r_refit, ci_c, "CONTROL")
    if r_full_stack is not None:
        _verdict("TOKEN-REFIT + MARGINAL (full stack)", r_full_stack, r_refit["ci"],
                 "TOKEN-REFIT alone")

    print(f"\n  FAMILY-A ANCHOR ({100*FAMILY_A_ANCHOR:.1f}%) / 96.7 (BPL's own reported ceiling) "
          f"CI-TOUCH CHECK:")
    arms = [("CONTROL", r_control), ("+EARNED-PARSE (1a)", r_earned),
            ("TOKEN-REFIT (2)", r_refit)]
    if r_shortlist is not None:
        arms.append(("SHORTLIST+MARGINAL (1b)", r_shortlist))
    if r_wide is not None:
        arms.append(("SHORTLIST+MARGINAL (wide)", r_wide))
    if r_full_stack is not None:
        arms.append(("TOKEN-REFIT + MARGINAL (full stack)", r_full_stack))
    for name, res in arms:
        touch_a = r17._touches(res["ci"], FAMILY_A_ANCHOR)
        touch_96 = r17._touches(res["ci"], 0.967)
        print(f"    {name:<38}: CI {[round(100*x,1) for x in res['ci']]} "
              f"Family-A-anchor {'TOUCHES' if touch_a else 'does NOT touch'}; "
              f"96.7 {'TOUCHES' if touch_96 else 'does NOT touch'}.")
    best_arm = max(arms, key=lambda kv: kv[1]["acc"])
    print(f"\n  BEST ARM: {best_arm[0]} at {100*best_arm[1]['acc']:.1f}% "
          f"{[round(100*x,1) for x in best_arm[1]['ci']]}")

    print(f"\n  BUDGET NOTES: {budget_notes if budget_notes else 'none -- full scope completed.'}")
    donkey0 = "torch" not in sys.modules
    print(f"  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")
    print(f"\n  total runtime: {time.time() - t0:.1f}s (internal budget "
          f"{RUNTIME_BUDGET_SECONDS:.0f}s + {600 - RUNTIME_BUDGET_SECONDS:.0f}s import/report "
          f"headroom)")
    print(SEP)
    print("  OVERALL: PASS" if donkey0 and sat_pass is not False else "  OVERALL: FAIL")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
