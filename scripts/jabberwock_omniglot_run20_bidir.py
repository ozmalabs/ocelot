"""OMNIGLOT RUN 20 -- BIDIRECTIONAL COVERAGE-CONSTRAINED REFIT (scratchpad/HANDWRITING_DESIGN.md
does not carry a "RUN 20" section by name; the design is commit e43fba60's own "NEXT (run 20)"
paragraph + results/omniglot_gate_run19_refit.log's diagnostic appendix): RUN 19 named TOKEN-
REFIT unconstrained (`domains.abs_read.program_refit_rerank`) ACTIVELY HARMFUL -- 25.5%
[20.0, 32.0] at n=200, dominated by ATTRACTOR programs (generic/simple candidate parts that
cheaply explain any query because unexplained observation ink costs the directional metric
NOTHING). THE FIX (`domains.abs_read.program_refit_bidir_rerank`, added this run, purely
additive): the refit score becomes program->ink soft-min PLUS ink->program soft-min (every
observed part must be explained by some program part AND vice versa), part-count normalised by
the MEAN each direction already takes (no new tuned weight -- a unit-weight sum of two already-
established per-part means, the SAME "symmetric sum of two directed soft-mins" shape
`recognition_graph._joint_pair_dist` already establishes for the unrelated symmetric family).

Standing rules bind this run (CLAUDE.md): POWER THE GATE BEFORE THE ENDGAME, mechanism !=
benchmark value (report both), every classification decision is a held Term (audits scan
`domains/abs_read.py`), tuning-free (every DEFAULT_PARSE_*/DEFAULT_REFIT_BETA constant this run
uses is REUSED verbatim, never re-tuned here).

FOUR ARMS, off the SAME (alphabet, repeat) block spec / decode cache RUN 15-19 already
established (`jabberwock_omniglot_run17_close._block_spec`, the SAME `POWER_SEED` rng consumed
in the SAME order -- byte-identical exemplar/query drawer draws):

  1. CONTROL -- `domains.abs_read.stage_parse_char`/`parse_marginal_verdict`, theta grid ONLY,
     ALL `way`=20 candidates staged -- byte-identical to RUN 17b/19's own PARSE MARGINAL arm.
     MUST reproduce ~79-80.5% [CI].
  2. UNIDIRECTIONAL REFIT (RUN 19's own metric, UNCHANGED) -- `program_refit_rerank` over the
     SAME delta=0+appearance shortlist RUN 19 used, over the SAME raw per-stroke points. Kept
     here as the reproducing mechanism-check control (must land back near RUN 19's 25.5%) so
     the bidirectional arm's separation from it is measured on THIS run's own n, not merely
     cited from a different log.
  3. BIDIRECTIONAL REFIT (THE FIX, LEVER 2 of the design) -- `program_refit_bidir_rerank`, same
     shortlist, same raw parts. THE question: does it separate from arm 2's null, and where does
     it land relative to arm 1's marginal control?
  4. FULL STACK (bidirectional refit JOINED to the marginalization, `refit_bidir_plus_marginal_
     rerank`) -- ONE combined held Term per candidate (parse-marginal error + bidirectional
     refit score, summed at unit weight), over the SAME shortlist. Per the launch instructions,
     this arm is attempted ONLY if arm 3 clears a PRE-REGISTERED competitiveness bar measured at
     PILOT scale (see `BIDIR_COMPETITIVE_THRESHOLD` below) -- decided BEFORE the powered phase,
     never post-hoc. If arm 3 doesn't clear it, arm 4 is skipped and the reason is reported
     honestly (the launch instructions permit this: "only if (2) is at least competitive, else
     report why not attempted").

Arms 1-3 (control / unidirectional-reference / bidirectional-fix) are the NON-NEGOTIABLE CORE per
the launch instructions ("control + arm 2 are the core") and are NEVER scope-capped by this
script's own budget logic; arm 4 (the full stack) is shed FIRST if the projected runtime exceeds
budget, exactly RUN 19's own "cap arms not n" shedding precedent; only if the core itself cannot
fit does R (repeats) drop, the LAST resort.

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /usr/bin/python3 scripts/jabberwock_omniglot_run20_bidir.py
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
RUN19_TOKEN_REFIT = {"acc": 0.255, "ci": (0.200, 0.320), "n": 200}       # results/
                                                                          # omniglot_gate_run19_
                                                                          # refit.log's TOKEN-
                                                                          # REFIT (2) arm.

# Family A's own marginal-inference recipe, REUSED VERBATIM (tuning-free run: no new weights).
PARSE_THETAS = ar.DEFAULT_PARSE_THETAS
PARSE_WHOLE_N = ar.DEFAULT_PARSE_WHOLE_N
PARSE_PER_PART = ar.DEFAULT_PARSE_PER_PART
PARSE_PART_W, PARSE_SC_W, PARSE_BETA = r17.PARSE_PART_W, r17.PARSE_SC_W, r17.PARSE_BETA
REFIT_BETA = ar.DEFAULT_REFIT_BETA       # reused verbatim (recognition_graph's own default).

# PRE-REGISTERED (decided before any pilot number is seen, per the launch instruction that the
# full-stack gating must not be a post-hoc call): arm 3 (bidirectional refit) must clear this
# PILOT-scale accuracy bar for arm 4 (the full stack) to be attempted at all. 0.40 is chosen as
# "clearly separated from RUN 19's harmful ~25.5% band, and a plausible floor for a single-
# distance-family reconciliation metric to be worth joining to the richer marginal ensemble" --
# not tuned to this run's own result.
BIDIR_COMPETITIVE_THRESHOLD = 0.40

RUNTIME_BUDGET_SECONDS = 520.0           # RUN 17/19's own budget value, reused verbatim (~80s
                                          # headroom under the 600s foreground cap).


def _stage_and_verdict(exemplar_paths, query_path, candidate_idxs, *, way: int) -> tuple:
    """Mechanical scratch-substrate staging + ONE `parse_marginal_verdict` evaluate -- the
    CONTROL arm, byte-identical to RUN 17b/19's own theta-grid-only staging. Returns
    `(predicted_index, scratch, query_node, {candidate_index: node_id})` -- the scratch/qn/
    cand_nodes are reused by the FULL-STACK arm so the parse-marginal side of its own combined
    Term is evaluated over the SAME staged graph, never a second staging pass."""
    scratch = srs.Substrate()
    cand_of: dict[int, int] = {}
    for ci in candidate_idxs:
        node = ar.stage_parse_char(scratch, exemplar_paths[ci], is_query=False,
                                    thetas=PARSE_THETAS, whole_n=PARSE_WHOLE_N,
                                    per_part=PARSE_PER_PART, name=str(ci))
        cand_of[node] = ci
    qn = ar.stage_parse_char(scratch, query_path, is_query=True, thetas=PARSE_THETAS,
                              whole_n=PARSE_WHOLE_N, per_part=PARSE_PER_PART)
    winner = ar.parse_marginal_verdict(scratch, qn, part_w=PARSE_PART_W, sc_w=PARSE_SC_W,
                                        beta=PARSE_BETA)
    pred = cand_of.get(winner, -1) if winner is not None else -1
    node_of_ci = {ci: n for n, ci in cand_of.items()}
    return pred, scratch, qn, node_of_ci


def _episode_run20(s, native, dk, qd, exemplar_composed, exemplar_stroke_points,
                    exemplar_paths, query_path, way: int, run_full_stack: bool) -> dict:
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
    w_control, scratch, qn, node_of_ci = _stage_and_verdict(exemplar_paths, query_path,
                                                             range(way), way=way)
    t_parts["parse_control"] = time.time() - t0

    active = shortlist if shortlist else list(range(way))
    raw_program_parts = [[item[0] for item in exemplar_stroke_points[ci]] for ci in active]
    raw_program_by_ci = [[] for _ in range(way)]
    for pos, ci in enumerate(active):
        raw_program_by_ci[ci] = raw_program_parts[pos]
    raw_observed_parts = [item[0] for item in qd["stroke_points"]]

    t0 = time.time()
    refit_uni = ar.program_refit_rerank(native, raw_program_by_ci, raw_observed_parts, active,
                                         beta_corr=REFIT_BETA)
    w_refit_uni = refit_uni["winner"] if refit_uni["winner"] is not None else -1
    t_parts["refit_uni"] = time.time() - t0

    t0 = time.time()
    refit_bidir = ar.program_refit_bidir_rerank(native, raw_program_by_ci, raw_observed_parts,
                                                 active, beta_corr=REFIT_BETA)
    w_refit_bidir = refit_bidir["winner"] if refit_bidir["winner"] is not None else -1
    t_parts["refit_bidir"] = time.time() - t0

    w_full_stack = -1
    if run_full_stack:
        t0 = time.time()
        joined = ar.refit_bidir_plus_marginal_rerank(
            scratch, qn, node_of_ci, raw_program_by_ci, raw_observed_parts, active,
            beta_corr=REFIT_BETA, part_w=PARSE_PART_W, sc_w=PARSE_SC_W, beta=PARSE_BETA)
        w_full_stack = joined["winner"] if joined["winner"] is not None else -1
        t_parts["full_stack"] = time.time() - t0

    return dict(w_control=w_control, w_refit_uni=w_refit_uni, w_refit_bidir=w_refit_bidir,
                w_full_stack=w_full_stack, shortlist_size=len(shortlist), timing=t_parts)


def _run_block(s, native, dk, cache, spec, way, run_full_stack) -> dict:
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
        rec = _episode_run20(s, native, dk, qd, exemplar_composed, exemplar_stroke_points,
                              exemplar_paths, query_path, way, run_full_stack)
        rec["true"] = qi
        records.append(rec)
    return dict(records=records, elapsed=time.time() - t0)


def main():
    t0 = time.time()
    print(SEP)
    print("OMNIGLOT RUN 20 -- BIDIRECTIONAL COVERAGE-CONSTRAINED REFIT: CONTROL, UNIDIRECTIONAL")
    print("REFIT (reproducing control), BIDIRECTIONAL REFIT (the fix), and the FULL STACK if")
    print("bidirectional clears the pre-registered competitiveness bar.")
    print(SEP)

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    print(f"\n  LEARN caps (RUN 15-19's own reduced, saturation-verified cap): "
          f"{gate.LEARN_ALPHABETS_N} background alphabets, drawers "
          f"{gate.LEARN_DRAWERS[0]}-{gate.LEARN_DRAWERS[-1]}, capped at {LEARN_STROKE_CAP} "
          f"pen-down strokes. ink-decode params: {gate.DK}")
    print(f"  Parse recipe (Family A's own, REUSED VERBATIM -- tuning-free run): thetas="
          f"{PARSE_THETAS}, whole_n={PARSE_WHOLE_N}, per_part={PARSE_PER_PART}, "
          f"part_w={PARSE_PART_W}, sc_w={PARSE_SC_W}, beta={PARSE_BETA}, "
          f"refit_beta={REFIT_BETA}.")

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
          f"(RUN 15-19 all produced 7).")

    qualifying = sorted(a for a in ow.alphabets("evaluation")
                        if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]
    print(f"\n  TEST alphabets (sorted-name {N_TEST_ALPHABETS}-prefix, RUN 15-19's own set): "
          f"{test_alphabets}")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2: PILOT -- ONE block (20 episodes), all four arms (incl. the full stack, so its
    #  UNPOWERED pilot accuracy is available to decide arm 3's competitiveness gate below),
    #  timed per-episode-part for the budget projection.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2: PILOT + COMPETITIVENESS GATE + BUDGET PROJECTION\n{SEP}")
    cache: dict = {}
    pilot_rng = np.random.default_rng(POWER_SEED)
    pilot_spec = r17._block_spec(test_alphabets[0], pilot_rng, WAY, EPISODES_PER_ALPHABET)
    pilot = _run_block(s, native, gate.DK, cache, pilot_spec, WAY, run_full_stack=True)
    n_blocks = len(test_alphabets) * R_TARGET
    per_part_totals: dict = {}
    for rec in pilot["records"]:
        for k, v in rec["timing"].items():
            per_part_totals[k] = per_part_totals.get(k, 0.0) + v
    print(f"  PILOT block ({test_alphabets[0]!r}, repeat 0, {WAY} episodes, ALL FOUR ARMS): "
          f"{pilot['elapsed']:.1f}s total. Per-arm-part totals (this one block): "
          + ", ".join(f"{k}={v:.2f}s" for k, v in per_part_totals.items()))

    pilot_trues = [r_["true"] for r_ in pilot["records"]]

    def _pilot_report(name, preds):
        acc, ci, k = r17._acc_ci(preds, pilot_trues)
        print(f"    {name:<38} n={len(pilot_trues):>3}  k={k:>2}  acc={100*acc:5.1f}%  "
              f"95% CI [{100*ci[0]:5.1f}%, {100*ci[1]:5.1f}%]")
        return acc

    print(f"\n  PILOT-SCALE per-arm accuracy (n={WAY}, ONE block, UNPOWERED -- mechanism check "
          f"only, not a claim):")
    _pilot_report("CONTROL (parse-marginal)", [x["w_control"] for x in pilot["records"]])
    _pilot_report("UNIDIRECTIONAL REFIT (RUN 19)", [x["w_refit_uni"] for x in pilot["records"]])
    pilot_bidir_acc = _pilot_report("BIDIRECTIONAL REFIT (fix)",
                                     [x["w_refit_bidir"] for x in pilot["records"]])
    _pilot_report("FULL STACK (joined)", [x["w_full_stack"] for x in pilot["records"]])
    pilot_mean_shortlist = float(np.mean([x["shortlist_size"] for x in pilot["records"]]))
    print(f"    -- PILOT mean shortlist size: {pilot_mean_shortlist:.2f} / {WAY}.")

    full_stack_competitive = pilot_bidir_acc >= BIDIR_COMPETITIVE_THRESHOLD
    print(f"\n  COMPETITIVENESS GATE (pre-registered, decided now, before any powered number): "
          f"bidirectional refit pilot accuracy {100*pilot_bidir_acc:.1f}% "
          f"{'>=' if full_stack_competitive else '<'} threshold "
          f"{100*BIDIR_COMPETITIVE_THRESHOLD:.0f}% -> full-stack arm "
          f"{'ATTEMPTED at powered scale' if full_stack_competitive else 'SKIPPED'}.")

    elapsed_so_far = time.time() - t0
    per_block_full = pilot["elapsed"]
    per_block_core = per_block_full - per_part_totals.get("full_stack", 0.0)
    projected_full = elapsed_so_far + per_block_full * n_blocks
    projected_core = elapsed_so_far + per_block_core * n_blocks

    run_full_stack = full_stack_competitive
    r_used = R_TARGET
    budget_notes = []
    if run_full_stack and projected_full > RUNTIME_BUDGET_SECONDS:
        run_full_stack = False
        note = (f"projected WITH-full-stack {projected_full:.0f}s > "
                f"{RUNTIME_BUDGET_SECONDS:.0f}s budget -- shedding the full-stack arm first "
                f"(projected core-only {projected_core:.0f}s), per 'cap arms not n'.")
        print(f"  {note}")
        budget_notes.append(note)
    projected_now = projected_core if not run_full_stack else projected_full
    if projected_now > RUNTIME_BUDGET_SECONDS:
        r_used = 1
        projected_r1 = elapsed_so_far + (per_block_full if run_full_stack else per_block_core) \
            * len(test_alphabets) * r_used
        note2 = (f"even the CORE arms alone project over budget at R={R_TARGET} -- reducing to "
                 f"R={r_used} (projected {projected_r1:.0f}s), the LAST resort per 'cap arms "
                 f"not n'.")
        print(f"  {note2}")
        budget_notes.append(note2)
    if not budget_notes:
        print(f"  within budget (projected {projected_now:.0f}s vs {RUNTIME_BUDGET_SECONDS:.0f}s "
              f"budget) -- running the full scope (R={r_used}, {len(test_alphabets)} "
              f"alphabets, full_stack={'on' if run_full_stack else 'off'}).")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 3: POWERED TEST
    # ------------------------------------------------------------------------------------- #
    n_target = len(test_alphabets) * r_used * WAY
    print(f"\n{SEP}\n  PHASE 3: POWERED TEST (target n={n_target})\n{SEP}")
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
            blk = _run_block(s, native, gate.DK, cache, spec, WAY, run_full_stack)
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

    print(f"\n  {len(all_records)} episodes scored (R={r_used}, "
          f"full_stack={'on' if run_full_stack else 'off'}).\n")
    r_control = _report("CONTROL (parse-marginal)", [x["w_control"] for x in all_records], trues)
    r_refit_uni = _report("UNIDIRECTIONAL REFIT (RUN 19)",
                          [x["w_refit_uni"] for x in all_records], trues)
    r_refit_bidir = _report("BIDIRECTIONAL REFIT (fix)",
                            [x["w_refit_bidir"] for x in all_records], trues)
    mean_shortlist = float(np.mean([x["shortlist_size"] for x in all_records]))
    print(f"    -- mean shortlist size: {mean_shortlist:.2f} / {WAY} candidates.")
    if run_full_stack:
        r_full_stack = _report("FULL STACK (joined)", [x["w_full_stack"] for x in all_records],
                               trues)
    else:
        r_full_stack = None

    print(f"\n{SEP}\n  VERDICTS (n={len(all_records)})\n{SEP}")
    ci_c = r_control["ci"]
    overlaps_17b = not (ci_c[1] < RUN17B_PARSE_MARGINAL["ci"][0]
                        or RUN17B_PARSE_MARGINAL["ci"][1] < ci_c[0])
    print(f"  CONTROL REPRODUCTION: {100*r_control['acc']:.1f}% "
          f"{[round(100*x,1) for x in ci_c]} vs RUN 17b's 80.5% [76.3, 84.1] (n=400) -- "
          f"{'CI-OVERLAP (consistent)' if overlaps_17b else 'CI-SEPARATED (investigate)'}")

    ci_u = r_refit_uni["ci"]
    overlaps_19 = not (ci_u[1] < RUN19_TOKEN_REFIT["ci"][0]
                       or RUN19_TOKEN_REFIT["ci"][1] < ci_u[0])
    print(f"  UNIDIRECTIONAL-REFIT REPRODUCTION: {100*r_refit_uni['acc']:.1f}% "
          f"{[round(100*x,1) for x in ci_u]} vs RUN 19's 25.5% [20.0, 32.0] (n=200) -- "
          f"{'CI-OVERLAP (consistent)' if overlaps_19 else 'CI-SEPARATED (investigate)'}")

    def _verdict(name, res, base_ci, base_label):
        sep = gate._ci_separated(res["ci"], base_ci)
        print(f"  {name} vs {base_label}: {100*res['acc']:.1f}% -- "
              f"{'CI-SEPARATED' if sep else 'NOT CI-SEPARATED'}")
        return sep

    print()
    sep_from_uni = _verdict("BIDIRECTIONAL REFIT (fix)", r_refit_bidir, ci_u,
                            "UNIDIRECTIONAL REFIT")
    _verdict("BIDIRECTIONAL REFIT (fix)", r_refit_bidir, ci_c, "CONTROL")
    if r_full_stack is not None:
        _verdict("FULL STACK (joined)", r_full_stack, r_refit_bidir["ci"],
                 "BIDIRECTIONAL REFIT alone")
        _verdict("FULL STACK (joined)", r_full_stack, ci_c, "CONTROL")

    print(f"\n  FAMILY-A ANCHOR ({100*FAMILY_A_ANCHOR:.1f}%) / 96.7 (BPL's own reported ceiling) "
          f"CI-TOUCH CHECK:")
    arms = [("CONTROL", r_control), ("UNIDIRECTIONAL REFIT", r_refit_uni),
            ("BIDIRECTIONAL REFIT", r_refit_bidir)]
    if r_full_stack is not None:
        arms.append(("FULL STACK", r_full_stack))
    for name, res in arms:
        touch_a = r17._touches(res["ci"], FAMILY_A_ANCHOR)
        touch_96 = r17._touches(res["ci"], 0.967)
        print(f"    {name:<22}: CI {[round(100*x,1) for x in res['ci']]} "
              f"Family-A-anchor {'TOUCHES' if touch_a else 'does NOT touch'}; "
              f"96.7 {'TOUCHES' if touch_96 else 'does NOT touch'}.")
    best_arm = max(arms, key=lambda kv: kv[1]["acc"])
    print(f"\n  BEST ARM: {best_arm[0]} at {100*best_arm[1]['acc']:.1f}% "
          f"{[round(100*x,1) for x in best_arm[1]['ci']]}")

    print(f"\n  THE MECHANISM CHECK (must-hold per the launch instructions): bidirectional refit "
          f"{'DID' if sep_from_uni and r_refit_bidir['acc'] > r_refit_uni['acc'] else 'did NOT'} "
          f"separate from RUN 19's harmful directional-only null "
          f"({100*r_refit_uni['acc']:.1f}% -> {100*r_refit_bidir['acc']:.1f}%).")

    print(f"\n  BUDGET NOTES: {budget_notes if budget_notes else 'none -- full scope completed.'}")
    print(f"  full-stack competitiveness gate: pilot bidirectional accuracy "
          f"{100*pilot_bidir_acc:.1f}% vs {100*BIDIR_COMPETITIVE_THRESHOLD:.0f}% threshold -> "
          f"{'attempted' if full_stack_competitive else 'SKIPPED (reason above)'}"
          f"{'' if full_stack_competitive == run_full_stack else ' (later shed by budget)'}.")
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
