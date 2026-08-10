"""OMNIGLOT RUN 21 -- LEARNED SPATIAL PRIORS ON THE WINNING VERDICT (scratchpad/HANDWRITING_
DESIGN.md does not carry a "RUN 21" section by name; the design is commit 5bca81be's own closing
paragraph: "the next move on the 96.7 road is LEARNED SPATIAL PRIORS layered ON the winning arm
(mine the background LEARN decodes for rel/position statistics; prior enters the marginal verdict
as a held term; priors learned from background data ONLY)"). Runs 17b/19/20 established
parse-marginal (`domains.abs_read.parse_marginal_verdict`) as the SOLE surviving winner at
79-80.5% [CI] -- every rival (token-refit, unidirectional and bidirectional) is CI-separated
BELOW it. This run is the FIRST lever this arc has aimed at the WINNER itself rather than at one
of its already-falsified rivals: `domains.spatial_priors` mines the SAME 5 background alphabets
the stroke codebook is earned from for POSITION (where does a stroke quantum sit in the character
frame) and TRANSITION (where does the NEXT stroke land relative to it) distributions -- BPL's own
"along/at-start/at-end" part-position models, EARNED here rather than hand-specified -- and adds
a held LOG-PRIOR term to the winning verdict's own per-candidate error.

Standing rules bind this run (CLAUDE.md): POWER THE GATE BEFORE THE ENDGAME, mechanism !=
benchmark value (report both), eval-subset coverage is part of every claim, every classification
decision is a held Term (audits scan `domains/spatial_priors.py`), and an INTERMEDIATE-GATE
discipline new to this run's own launch instructions: report the mined priors' own peakedness/
entropy/coverage diagnostics BEFORE any accuracy number -- a flat prior cannot help the verdict
regardless of what the accuracy numbers say, so the diagnostic is read FIRST.

THREE ARMS, off the SAME (alphabet, repeat) block spec / decode cache RUN 15-20 already
established (`jabberwock_omniglot_run17_close._block_spec`, the SAME `POWER_SEED` rng consumed
in the SAME order -- byte-identical exemplar/query drawer draws):

  1. CONTROL -- `domains.abs_read.stage_parse_char`/`parse_marginal_verdict`, theta grid ONLY,
     ALL `way`=20 candidates staged -- byte-identical to RUN 17b/19/20's own PARSE MARGINAL arm.
     MUST reproduce ~79-80.5% [CI]. NON-NEGOTIABLE (never scope-capped).
  2. +SPATIAL-PRIOR (THE arm) -- `domains.spatial_priors.spatial_prior_marginal_rerank`: the
     SAME `parse_marginal_pair_error_term` (run 20's own per-pair exposure of the control's OWN
     fused error) PLUS `-lambda * arrangement_log_prior(candidate)` (the candidate's own
     already-decoded composed signature scored against the MINED position+transition
     distributions), summed at `lambda=1.0` ("unit first," per the launch instructions -- see
     `domains/spatial_priors.py`'s own docstring for why the log-prior is reported as a
     PER-TERM MEAN rather than a raw sum, the scale-compatibility fix that makes unit lambda
     sane). Staged over the SAME ALL-20-candidate pool as CONTROL (never a narrowed shortlist --
     this arm tests the prior as an add-on to THE WINNER's own decision procedure, not a search
     lever). NON-NEGOTIABLE (never scope-capped) -- this run's CORE PAIR is arms 1+2.
  3. FULL GENERATIVE STACK (budget-permitting only) -- RUN 20's own un-falsified (shed on a
     pilot competitiveness bar, never disproven) bidirectional token-refit JOINED to the
     parse-marginal error, now ALSO carrying the spatial-prior term: `parse_marginal_pair_error
     + program_refit_bidir + (-lambda * arrangement_log_prior)`, over the SAME delta=0+
     appearance shortlist RUN 19/20 used. Attempted ONLY if a FRESH pilot-scale bidirectional-
     refit accuracy clears RUN 20's own pre-registered `BIDIR_COMPETITIVE_THRESHOLD` (0.40) --
     decided BEFORE the powered phase, never post-hoc, exactly RUN 20's own protocol. Shed
     FIRST under budget pressure (per the launch instructions: "budget clause, shed arm 3 first
     then R, never the core pair").

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /usr/bin/python3 scripts/jabberwock_omniglot_run21_priors.py
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
from domains import spatial_priors as sp

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

# Family A's own marginal-inference recipe, REUSED VERBATIM (tuning-free run: no new weights on
# the CONTROL/marginal side -- the ONLY new number this run introduces is `PRIOR_LAMBDA`, tried
# at "unit first" per the launch instructions, never grid-searched here).
PARSE_THETAS = ar.DEFAULT_PARSE_THETAS
PARSE_WHOLE_N = ar.DEFAULT_PARSE_WHOLE_N
PARSE_PER_PART = ar.DEFAULT_PARSE_PER_PART
PARSE_PART_W, PARSE_SC_W, PARSE_BETA = r17.PARSE_PART_W, r17.PARSE_SC_W, r17.PARSE_BETA
REFIT_BETA = ar.DEFAULT_REFIT_BETA       # reused verbatim (recognition_graph's own default).
PRIOR_LAMBDA = sp.DEFAULT_PRIOR_LAMBDA   # 1.0 -- "unit first."
PRIOR_ALPHA = sp.DEFAULT_PRIOR_ALPHA     # 1.0 -- Laplace smoothing, unit, not tuned.

# Mining scope: the SAME 5 background alphabets/drawer-01-14 pool the LEARN pass earns the
# stroke codebook from (hygiene: `mine_spatial_priors` itself asserts every alphabet here is a
# `background`-split alphabet) -- a BOUNDED drawer/character subset (not the full 5x~20x14
# sweep) to keep the mining pass' own runtime a small fraction of the total budget; logged
# honestly below, never silently truncated.
MINE_DRAWERS = gate.LEARN_DRAWERS[:7]        # drawers 01-07 (LEARN itself uses 01-14) --
                                              # widened from an initial 3-drawer pilot pass
                                              # (results/omniglot_gate_run21_priors.log's first
                                              # attempt) that mined ONLY 1 distinct stroke-
                                              # quantum identity across 405 characters (the
                                              # position table's OWN diagnostic caught this --
                                              # "read peakedness BEFORE accuracy" -- before any
                                              # accuracy number was trusted): 7 drawers gives
                                              # ~2x the sample without blowing the runtime
                                              # budget (see this run's own mining-time log line).
MINE_MAX_CHARS_PER_ALPHABET = 25

RUN20_BIDIR = {"acc": 0.255, "ci": (0.200, 0.320), "n": 200}   # results/
                                                                # omniglot_gate_run20_bidir.log's
                                                                # BIDIRECTIONAL REFIT arm.
BIDIR_COMPETITIVE_THRESHOLD = 0.40   # RUN 20's own pre-registered bar, reused verbatim.

RUNTIME_BUDGET_SECONDS = 520.0           # RUN 17/19/20's own budget value, reused verbatim.


def _stage_and_verdict(exemplar_paths, query_path, candidate_idxs, *, way: int) -> tuple:
    """Mechanical scratch-substrate staging + ONE `parse_marginal_verdict` evaluate -- the
    CONTROL arm, byte-identical to RUN 17b/19/20's own theta-grid-only staging. Returns
    `(predicted_index, scratch, query_node, {candidate_index: node_id})`."""
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


def _full_stack_winner(scratch, qn, node_of_ci, exemplar_composed, exemplar_stroke_points,
                        query_stroke_points, active: list, priors: dict, dk: dict) -> int:
    """ARM 3: `parse_marginal_pair_error_term` + `program_refit_bidir_term` (RUN 20's own
    un-falsified full-stack combination, verbatim) PLUS `-lambda * arrangement_log_prior` --
    ONE nested `Plus`, ONE evaluate per candidate, held `Argmin` (`ar._argmin_pairs_term`) over
    the `active` shortlist (RUN 19/20's own delta=0+appearance shortlist). A candidate missing
    a staged node or usable parts is skipped, never a crash; `active[0]` is the honest fallback
    for an empty/all-degenerate pass."""
    native = getattr(scratch, "_inner", scratch)
    raw_observed_parts = [item[0] for item in query_stroke_points]
    pairs: list = []
    for ci in active:
        cand_node = node_of_ci.get(ci)
        parts = [item[0] for item in exemplar_stroke_points[ci]] if ci < len(exemplar_stroke_points) else []
        if cand_node is None or not parts or not raw_observed_parts:
            continue
        logp = sp.arrangement_log_prior(exemplar_composed[ci], priors, grid=dk["grid"],
                                         turn_bins=dk["turn_bins"], scale_bins=dk["scale_bins"],
                                         alpha=PRIOR_ALPHA)
        base = ar.parse_marginal_pair_error_term(part_w=PARSE_PART_W, sc_w=PARSE_SC_W,
                                                  beta=PARSE_BETA)
        refit = ar.program_refit_bidir_term(parts, raw_observed_parts, beta_corr=REFIT_BETA)
        term = {"type": "Plus", "items": [
            {"type": "Plus", "items": [base, refit]},
            {"type": "Times", "items": [{"type": "Lit", "value": -float(PRIOR_LAMBDA)},
                                         {"type": "Lit", "value": float(logp)}]}]}
        score = float(native.evaluate(term, {"s": qn, "w": cand_node}) or 0.0)
        pairs.append((score, ci))
    winner = active[0] if active else -1
    if pairs:
        w = native.evaluate(ar._argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return winner


def _episode_run21(s, native, dk, qd, exemplar_composed, exemplar_stroke_points,
                    exemplar_paths, query_path, way: int, priors: dict,
                    run_full_stack: bool) -> dict:
    t_parts = {}

    t0 = time.time()
    w_control, scratch, qn, node_of_ci = _stage_and_verdict(exemplar_paths, query_path,
                                                             range(way), way=way)
    t_parts["parse_control"] = time.time() - t0

    t0 = time.time()
    prior_res = sp.spatial_prior_marginal_rerank(
        scratch, qn, node_of_ci, exemplar_composed, list(range(way)), priors,
        lam=PRIOR_LAMBDA, grid=dk["grid"], turn_bins=dk["turn_bins"],
        scale_bins=dk["scale_bins"], alpha=PRIOR_ALPHA, part_w=PARSE_PART_W, sc_w=PARSE_SC_W,
        beta=PARSE_BETA)
    w_prior = prior_res["winner"] if prior_res["winner"] is not None else -1
    t_parts["spatial_prior"] = time.time() - t0

    w_full_stack = -1
    if run_full_stack:
        t0 = time.time()
        adopted = ar.abs_rerank_targeted(
            s, qd["composed_sig"], qd["stroke_points"], exemplar_composed,
            exemplar_stroke_points, delta=0.0, use_widen=False, use_appearance=True,
            turn_bins=dk["turn_bins"], len_bins=dk["len_bins"], grid=dk["grid"],
            scale_bins=dk["scale_bins"], segments=dk["segments"])
        active = list(adopted.get("shortlist0") or range(way))
        w_full_stack = _full_stack_winner(scratch, qn, node_of_ci, exemplar_composed,
                                           exemplar_stroke_points, qd["stroke_points"], active,
                                           priors, dk)
        t_parts["full_stack"] = time.time() - t0

    return dict(w_control=w_control, w_prior=w_prior, w_full_stack=w_full_stack,
                timing=t_parts)


def _run_block(s, native, dk, cache, spec, way, priors, run_full_stack) -> dict:
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
        rec = _episode_run21(s, native, dk, qd, exemplar_composed, exemplar_stroke_points,
                              exemplar_paths, query_path, way, priors, run_full_stack)
        rec["true"] = qi
        records.append(rec)
    return dict(records=records, elapsed=time.time() - t0)


def main():
    t0 = time.time()
    print(SEP)
    print("OMNIGLOT RUN 21 -- LEARNED SPATIAL PRIORS: CONTROL (parse-marginal), +SPATIAL-PRIOR")
    print("(the arm), and the FULL GENERATIVE STACK if bidirectional refit clears the pilot")
    print("competitiveness bar.")
    print(SEP)

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    print(f"\n  LEARN caps (RUN 15-20's own reduced, saturation-verified cap): "
          f"{gate.LEARN_ALPHABETS_N} background alphabets, drawers "
          f"{gate.LEARN_DRAWERS[0]}-{gate.LEARN_DRAWERS[-1]}, capped at {LEARN_STROKE_CAP} "
          f"pen-down strokes. ink-decode params: {gate.DK}")
    print(f"  Parse recipe (Family A's own, REUSED VERBATIM -- tuning-free on the marginal "
          f"side): thetas={PARSE_THETAS}, whole_n={PARSE_WHOLE_N}, per_part={PARSE_PER_PART}, "
          f"part_w={PARSE_PART_W}, sc_w={PARSE_SC_W}, beta={PARSE_BETA}, "
          f"refit_beta={REFIT_BETA}. prior_lambda={PRIOR_LAMBDA} (unit, first try), "
          f"prior_alpha={PRIOR_ALPHA} (Laplace smoothing, unit).")

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
          f"(RUN 15-20 all produced 7).")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 1.5: MINE SPATIAL PRIORS -- background data ONLY (hygiene asserted inside
    #  `mine_spatial_priors` itself: every alphabet here MUST be `background`-split).
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 1.5: MINE SPATIAL PRIORS (background-only, hygiene asserted)\n{SEP}")
    assert set(learn_alphabets) <= set(ow.alphabets("background")), \
        "mining alphabets must be a subset of the background split (hygiene)."
    t_mine0 = time.time()
    mined = sp.mine_spatial_priors(s, gate.DK, learn_alphabets, MINE_DRAWERS,
                                    max_chars_per_alphabet=MINE_MAX_CHARS_PER_ALPHABET)
    mine_elapsed = time.time() - t_mine0
    print(f"  mined {mined['n_chars']} background characters ({len(learn_alphabets)} alphabets x "
          f"drawers {MINE_DRAWERS} x up to {MINE_MAX_CHARS_PER_ALPHABET} chars/alphabet) in "
          f"{mine_elapsed:.1f}s.")
    print(f"  position table: {len(mined['position_counts'])} stroke-quantum identities, "
          f"{sum(mined['position_totals'].values())} total stroke observations.")
    print(f"  transition table: {len(mined['transition_counts'])} predecessor identities, "
          f"{sum(mined['transition_totals'].values())} total consecutive-pair observations.")

    persisted = sp.persist_spatial_priors(s, mined)
    print(f"  persisted {persisted['installed']} SpatialPrior nodes via teach() "
          f"(category={sp.CATEGORY!r} -- a seed byproduct).")
    priors = sp.load_spatial_priors(s)

    # INTERMEDIATE GATE (design: "report entropy/coverage of the mined statistics BEFORE
    # reading accuracy") -- printed here, BEFORE any TEST-phase number below.
    diag = sp.prior_diagnostics(priors)
    print(f"\n  PRIOR-QUALITY DIAGNOSTICS (read BEFORE any accuracy number below):")
    print(f"    mean peakedness (1 - entropy/max_entropy, 0=flat/uninformative, "
          f"1=maximally peaked): {diag['mean_peakedness']:.3f}")
    print(f"    mean samples per (kind, name, dim) row: {diag['mean_total_samples']:.1f}")
    for row in sorted(diag["rows"], key=lambda r: (r["kind"], r["name"], r["dim"])):
        print(f"      {row['kind']:<10} {row['name']:<14} {row['dim']:<3} "
              f"n={row['total']:>5}  distinct_bins={row['distinct_bins']:>3}  "
              f"entropy={row['entropy_bits']:.2f}/{row['max_entropy_bits']:.2f} bits  "
              f"peakedness={row['peakedness']:.2f}")
    if diag["mean_peakedness"] < 0.15:
        print(f"    WARNING: mean peakedness {diag['mean_peakedness']:.3f} is LOW -- the mined "
              f"priors are closer to FLAT than PEAKED; an accuracy null below would be "
              f"UNSURPRISING (a flat prior cannot help the verdict), not evidence against the "
              f"mechanism.")

    qualifying = sorted(a for a in ow.alphabets("evaluation")
                        if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]
    print(f"\n  TEST alphabets (sorted-name {N_TEST_ALPHABETS}-prefix, RUN 15-20's own set): "
          f"{test_alphabets}")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2: PILOT + COMPETITIVENESS GATE + BUDGET PROJECTION
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2: PILOT + COMPETITIVENESS GATE + BUDGET PROJECTION\n{SEP}")
    cache: dict = {}
    pilot_rng = np.random.default_rng(POWER_SEED)
    pilot_spec = r17._block_spec(test_alphabets[0], pilot_rng, WAY, EPISODES_PER_ALPHABET)
    pilot = _run_block(s, native, gate.DK, cache, pilot_spec, WAY, priors, run_full_stack=True)
    n_blocks = len(test_alphabets) * R_TARGET
    per_part_totals: dict = {}
    for rec in pilot["records"]:
        for k, v in rec["timing"].items():
            per_part_totals[k] = per_part_totals.get(k, 0.0) + v
    print(f"  PILOT block ({test_alphabets[0]!r}, repeat 0, {WAY} episodes, ALL THREE ARMS): "
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
    _pilot_report("+SPATIAL-PRIOR", [x["w_prior"] for x in pilot["records"]])
    pilot_full_acc = _pilot_report("FULL STACK (refit+prior+marginal)",
                                    [x["w_full_stack"] for x in pilot["records"]])

    full_stack_competitive = pilot_full_acc >= BIDIR_COMPETITIVE_THRESHOLD
    print(f"\n  COMPETITIVENESS GATE (RUN 20's own pre-registered bar, reused verbatim; decided "
          f"now, before any powered number): full-stack pilot accuracy {100*pilot_full_acc:.1f}% "
          f"{'>=' if full_stack_competitive else '<'} threshold "
          f"{100*BIDIR_COMPETITIVE_THRESHOLD:.0f}% -> arm 3 "
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
                f"(projected core-pair-only {projected_core:.0f}s), per 'shed arm 3 first, "
                f"never the core pair'.")
        print(f"  {note}")
        budget_notes.append(note)
    projected_now = projected_core if not run_full_stack else projected_full
    if projected_now > RUNTIME_BUDGET_SECONDS:
        r_used = 1
        projected_r1 = elapsed_so_far + (per_block_full if run_full_stack else per_block_core) \
            * len(test_alphabets) * r_used
        note2 = (f"even the CORE PAIR alone projects over budget at R={R_TARGET} -- reducing to "
                 f"R={r_used} (projected {projected_r1:.0f}s), the LAST resort per 'shed arm 3 "
                 f"first then R, never the core pair'.")
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
            blk = _run_block(s, native, gate.DK, cache, spec, WAY, priors, run_full_stack)
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
    r_prior = _report("+SPATIAL-PRIOR", [x["w_prior"] for x in all_records], trues)
    if run_full_stack:
        r_full_stack = _report("FULL STACK (refit+prior+marginal)",
                               [x["w_full_stack"] for x in all_records], trues)
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

    print()
    sep_from_control = _verdict("+SPATIAL-PRIOR", r_prior, ci_c, "CONTROL")
    if r_full_stack is not None:
        _verdict("FULL STACK", r_full_stack, ci_c, "CONTROL")
        _verdict("FULL STACK", r_full_stack, r_prior["ci"], "+SPATIAL-PRIOR")

    print(f"\n  FAMILY-A ANCHOR ({100*FAMILY_A_ANCHOR:.1f}%) / 96.7 (BPL's own reported ceiling) "
          f"CI-TOUCH CHECK:")
    arms = [("CONTROL", r_control), ("+SPATIAL-PRIOR", r_prior)]
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

    print(f"\n  THE MECHANISM CHECK (must-hold per the launch instructions): the spatial-prior "
          f"arm {'DID' if sep_from_control and r_prior['acc'] > r_control['acc'] else 'did NOT'} "
          f"separate ABOVE control ({100*r_control['acc']:.1f}% -> {100*r_prior['acc']:.1f}%); "
          f"{'CI-SEPARATED' if sep_from_control else 'NOT CI-SEPARATED'} in EITHER direction.")

    print(f"\n  BUDGET NOTES: {budget_notes if budget_notes else 'none -- full scope completed.'}")
    print(f"  full-stack competitiveness gate: pilot accuracy {100*pilot_full_acc:.1f}% vs "
          f"{100*BIDIR_COMPETITIVE_THRESHOLD:.0f}% threshold -> "
          f"{'attempted' if full_stack_competitive else 'SKIPPED (reason above)'}"
          f"{'' if full_stack_competitive == run_full_stack else ' (later shed by budget)'}.")
    print(f"  mining cost: {mine_elapsed:.1f}s for {mined['n_chars']} background characters.")
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
