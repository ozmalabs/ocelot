"""OMNIGLOT RUN 37A -- GAP A: JUDGE-A-TRIAL-BY-ITS-RESULT, the CONTRASTIVE VERDICT.

`results/run37_checkpoints/plan.json` (commit 67005b35, the jabberwock's own plan) grounds
Gap A -- RUN 36's (commit 5aa6bcb6) finding that, of the 78 full-dwell errors at n=400, 32.1%
pick the rank-1/2 nearest impostor (vs 10.5% chance under uniform confusion across 19
impostors) and that for multi-stroke confused pairs the element that actually DISTINGUISHES
the true class from its nearest impostor carries a median 0.187 of the ink -- a comparator
that weighs all ink equally lets a small hook get outvoted by shared mass. This is the
highest-value run of the RUN 37 plan (Gap A, per the plan's own salience ordering).

THE MECHANISM (`domains/contrastive_verdict.py`, see that module's own top-of-file docstring
for the full design -- this docstring only restates what is BINDING for this gate):
  1. TRIGGER -- ALWAYS contrast the top-2 (pre-registered parameter-free choice; a margin-
     calibrated trigger was considered and rejected as one more knob no cheaper than "always").
  2. TOP-2 -- `cv.top2_candidates`, pure composition of `abs_read.parse_marginal_pair_error`
     (an ALREADY-EXPOSED per-candidate score vector -- RUN 25's own `_c2_scale_probe`
     precedent -- so NO new Rust accessor was needed, contrary to the plan's own contingency
     for "if only the argmax is exposed").
  3. DIFFERENCE REGION -- `cv.difference_elements`, a per-stroke greedy alignment between the
     top-2 candidates' own EXEMPLAR files, REUSING `run36._greedy_stroke_match`/
     `_normalize_glyph` VERBATIM (design: "the matcher is exactly what the [RUN 37C] artifact
     distorted"). Every stroke load in this script goes through `run37c_hygiene.
     DropDegenerateFilter` -- MANDATORY, wrapping the ENTIRE eval loop below, exactly as
     RUN 37C's own `stage_eval` does.
  4. CONTRASTIVE SCORE -- held `MinOver(PointSetDist)` region distance, held `Argmin` verdict
     (`cv.contrastive_pick`). FINAL verdict = the contrastive winner (judge the trial by the
     RESULT of the focused look), global winner on every fallback branch.

GATE DESIGN (this script, clones the RUN 26/34/37C eval skeleton):
  Arms, on the SAME 400 episodes, SAME protocol (`run25._block_spec`, `POWER_SEED =
  gate.SEED + 1500`, WAY=20, R_TARGET=2, N_TEST_ALPHABETS=10 sorted-name prefix, alph OUTER /
  r INNER block order -- byte-identical to `results/run26_checkpoints/eval_baseline.json`):
    GLOBAL       -- `ar.stage_parse_char` + `ar.parse_marginal_verdict` (`DEFAULT_PARSE_
                    THETAS`), UNCHANGED -- must reproduce 80.5% [76.3, 84.1] k=322 EXACTLY
                    (RUN 37C already proved the degenerate filter changes this arm's accuracy
                    by ZERO episodes at n=400 -- this is a protocol guard, not a new claim).
    CONTRASTIVE  -- the mechanism above, computed from the SAME staged `scratch0`/`node0` the
                    GLOBAL arm already built for this episode (no second staging pass).
  PRIMARY analysis (pre-registered, `stage_report`): PAIRED McNemar on same-episode flips --
  fixed (global-wrong -> contrastive-right) vs broken (global-right -> contrastive-wrong),
  EXACT two-sided binomial test (`scipy.stats.binomtest(k=fixed, n=fixed+broken, p=0.5)`) --
  the powered test for a +1.5-4pp expected effect a plain accuracy-CI comparison cannot see at
  n=400. Also: accuracies with Wilson CIs, per-alphabet fixed/broken (prediction: concentrates
  in Ge_ez/Kannada, RUN 36's own near-rank-mass alphabets), the RANK of the true class in the
  GLOBAL ranking for every error episode (a fix is only POSSIBLE when the true class is
  EXACTLY the global runner-up -- rank 2 -- since the contrastive pass only ever chooses
  between the global top-2; this is the mechanism's own a-priori ceiling, reported alongside
  the observed fixed/broken counts, not tuned to it), and the `cv_decision` breakdown
  (two_sided / one_sided / fallback_* / skipped) as the "how much real material did the
  focused look have to work with" instrument (fire-RATE is trivially 100% under "always
  contrast" -- this breakdown is the honest substitute).

  STOPS (checked in `stage_report`, never silently bypassed): GLOBAL must reproduce 80.5%
  k=322 EXACTLY -- a mismatch is a protocol bug, STOP. `broken >= fixed` means the mechanism
  HARMS -- report and stop, never re-tune the formula against the outcome.

  Secondary (named, not executed this run -- wall-clock priority per the design's own
  "if wall-clock allows; else name it as follow-up"): the SAME contrastive pass on the
  SHORTLIST path (62.0% baseline, `SHORTLIST_K=10`) is a natural follow-up but is NOT run
  here; the primary full-dwell arms above are this run's whole scope.

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run37a.log`, per-BLOCK checkpoints under `results/run37a_checkpoints/`
(every OTHER run*_checkpoints dir, including run26's own `learn.json`/`eval_baseline.json`
and run36's own checkpoints, READ-ONLY reference -- never written here). `.venv` python
(needs `substrate_rs`). `seeds/stroke_shapes.json` is READ (md5 recorded, per
`run37c_hygiene.py`'s own parallel-session discipline) but never written.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run37a_contrastive.py --stage guard
  ... --stage eval        (re-invoke until COMPLETE -- checkpointed per block)
  ... --stage report
"""
from __future__ import annotations

import argparse
import hashlib
import json
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
from scipy.stats import binomtest

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run25_number as run25
import scripts.jabberwock_omniglot_run26_homework as run26
from domains import abs_read as ar
from domains import contrastive_verdict as cv
from domains import omniglot_world as ow
from scripts.jabberwock_omniglot_run37c_hygiene import DropDegenerateFilter

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run37a_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")   # READ-ONLY reference.
STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")   # parallel-session-
                                                                          # owned -- READ-ONLY.
os.makedirs(CKPT_DIR, exist_ok=True)

WAY = run25.WAY                                        # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET    # 20
R_TARGET = run25.R_TARGET                              # 2 -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS              # 10
POWER_SEED = run25.POWER_SEED                          # gate.SEED + 1500, byte-identical to
                                                        # RUN 15/16/17/25/26/36/37C's own eval seed.
PER_CALL_BUDGET_SECONDS = 480.0                        # leaves >100s headroom under the 600s
                                                        # foreground cap; eval checkpoints per
                                                        # block.

# Cited VERBATIM from results/run26_checkpoints/eval_baseline.json (== RUN 25/17b's own C0
# control) -- the GLOBAL arm's own reproduction target.
BASELINE_FULL_DWELL = dict(acc=0.805, ci=(0.7633481418022936, 0.8408493586537856), n=400, k=322)


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    run26._save_json(obj, path)


def _load_json(path: str):
    return run26._load_json(path)


def _md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _donkey0() -> bool:
    return run26._donkey0()


def _test_alphabets():
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    return qualifying[:N_TEST_ALPHABETS]


# =============================================================================================
# RANK-OF-TRUTH instrument (reporting only, never a decision): where the true class sits in the
# GLOBAL ranking (by `parse_marginal_pair_error`, lower = better) -- mirrors `abs_read.
# proposal_rank`'s own held `Count(FilterList(Lt(...)))` idiom, flipped for a lower-is-better
# metric. The contrastive pass can only ever recover an error episode when the true class is
# EXACTLY rank 2 (the global runner-up) -- it never looks past the top-2 -- so this is the
# mechanism's own a-priori ceiling, computed independently of any observed outcome.
# =============================================================================================
def _rank_lower_better_term(pairs: list, true_score: float) -> dict:
    return {"type": "Count", "source": {
        "type": "FilterList", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
        "predicate": {"type": "Lt",
                      "a": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                            "index": {"type": "Lit", "value": 0}},
                      "b": {"type": "Lit", "value": float(true_score)}}}}


def _true_class_rank(native, pairs: list, true_idx: int):
    true_score = None
    for s, ci in pairs:
        if ci == true_idx:
            true_score = s
            break
    if true_score is None:
        return None
    n_better = int(native.evaluate(_rank_lower_better_term(pairs, true_score), {}) or 0)
    return n_better + 1


# =============================================================================================
# ONE EPISODE'S worth of both arms -- staged ONCE (scratch0/node0), GLOBAL verdict read off
# exactly as run26/run37c's own `_run_block`, CONTRASTIVE computed from the SAME staged nodes.
# =============================================================================================
def _run_block(alph: str, r: int, spec: dict) -> list:
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    scratch0 = srs.Substrate()
    native = scratch0._inner
    node0, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                            thetas=ar.DEFAULT_PARSE_THETAS)

    # Exemplar raw strokes, cached ONCE per block (filter active for the life of this call --
    # see stage_eval's own `with DropDegenerateFilter():` wrapping every block).
    exemplar_raw = {ci: ow.load_strokes(drawer_files[ci][ex_drawer]) for ci in range(WAY)}

    records = []
    for qi, q_drawer in spec["queries"]:
        path = drawer_files[qi][q_drawer]
        rec = {"true": qi, "alph": alph, "r": r}

        qn0 = ar.stage_parse_char(scratch0, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
        w0 = ar.parse_marginal_verdict(scratch0, qn0)
        pred_full = cand0.get(w0, -1) if w0 is not None else -1
        rec["pred_full"] = pred_full

        full_pairs = [(ar.parse_marginal_pair_error(scratch0, qn0, node0[ci]), ci)
                      for ci in range(WAY)]
        rec["true_rank"] = _true_class_rank(native, full_pairs, qi)

        top2 = cv.top2_candidates(scratch0, qn0, node0)
        rec["top1_matches_global"] = bool(top2 and top2[0][1] == pred_full)

        if len(top2) < 2:
            rec["pred_contrastive"] = pred_full
            rec["cv_decision"] = "skipped_lt2_candidates"
        else:
            cand1_idx, cand2_idx = top2[0][1], top2[1][1]
            query_raw = ow.load_strokes(path)
            cp = cv.contrastive_pick(native, query_raw, exemplar_raw[cand1_idx],
                                      exemplar_raw[cand2_idx], cand1_idx, cand2_idx)
            rec["pred_contrastive"] = cp["winner"]
            rec["cv_decision"] = cp["decision"]
            rec["cv_kind"] = cp.get("kind")
            rec["cv_single_stroke"] = bool(cp.get("single_stroke"))
            rec["cv_count_mismatch"] = bool(cp.get("count_mismatch"))
            rec["cv_ok"] = bool(cp.get("ok"))
        records.append(rec)
    return records


# =============================================================================================
# STAGE: guard -- protocol reproduction (byte-identical to eval_baseline.json's block 0) PLUS
# the top2/global consistency check, mirroring run37c_hygiene.stage_verify's own precedent.
# =============================================================================================
def stage_guard() -> int:
    print(f"\n{SEP}\n  STAGE: guard -- protocol reproduction + top2/global consistency\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_PATH)
    print(f"  seeds/stroke_shapes.json md5 (parallel-session-owned, this run never writes "
          f"there): {md5_now}")

    baseline_records = _load_json(os.path.join(RUN26_DIR, "eval_baseline.json"))["records"][:WAY]
    test_alphabets = _test_alphabets()
    rng = np.random.default_rng(POWER_SEED)
    spec = run25._block_spec(test_alphabets[0], rng, WAY, EPISODES_PER_ALPHABET)

    t0 = time.time()
    with DropDegenerateFilter():
        got = _run_block(test_alphabets[0], 0, spec)
    print(f"  block 0 ({test_alphabets[0]!r}) computed in {time.time()-t0:.1f}s.")

    mismatches = []
    for i, (g, b) in enumerate(zip(got, baseline_records)):
        if g["pred_full"] != b["pred_full"]:
            mismatches.append((i, g["pred_full"], b["pred_full"]))
    ok = not mismatches
    print(f"  GLOBAL arm vs eval_baseline.json, block 0 ({len(got)} episodes): "
          f"{'EXACT MATCH' if ok else f'{len(mismatches)} MISMATCHES'}")
    for i, gv, bv in mismatches[:10]:
        print(f"    MISMATCH episode {i}: got pred_full={gv} baseline={bv}")

    n_consistent = sum(1 for g in got if g["top1_matches_global"])
    print(f"\n  top2_candidates()[0] vs parse_marginal_verdict's own Argmax winner: "
          f"{n_consistent}/{len(got)} consistent "
          f"{'(OK)' if n_consistent == len(got) else '(MISMATCH -- investigate before trusting downstream)'}")

    decisions = {}
    for g in got:
        decisions[g.get("cv_decision", "?")] = decisions.get(g.get("cv_decision", "?"), 0) + 1
    print(f"  contrastive cv_decision breakdown on block 0: {decisions}")

    guard_ok = ok and (n_consistent == len(got))
    out = dict(guard_ok=guard_ok, spot_check_mismatches=len(mismatches),
               top2_consistency=n_consistent, top2_total=len(got),
               stroke_shapes_md5=md5_now, decisions_block0=decisions)
    _save_json(out, _ckpt("guard.json"))
    print(f"\n  GUARD: {'PASS -- proceed to --stage eval' if guard_ok else 'FAIL -- STOP'}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0 if guard_ok else 1


def _require_guard():
    p = _ckpt("guard.json")
    if not os.path.exists(p):
        print("  WALL: run --stage guard first.")
        sys.exit(1)
    g = _load_json(p)
    if not g.get("guard_ok"):
        print("  WALL: --stage guard did not PASS -- fix the protocol mismatch before --stage eval.")
        sys.exit(1)
    return g


# =============================================================================================
# STAGE: eval -- full n=400, filter ON for every stroke load (exemplar + query).
# =============================================================================================
def stage_eval() -> int:
    print(f"\n{SEP}\n  STAGE: eval -- n=400, GLOBAL + CONTRASTIVE, filter ON\n{SEP}")
    _require_guard()
    out_path = _ckpt("eval_run37a.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval already COMPLETE (n={len(state['records'])}).")
        return 0

    test_alphabets = _test_alphabets()
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  test_alphabets={test_alphabets}")
    print(f"  blocks={len(blocks)} (target n={len(blocks)*WAY}) resuming at block "
          f"{state['block_idx']}")

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        alph, r = blocks[i]
        run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    with DropDegenerateFilter():
        while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
            alph, r = blocks[state["block_idx"]]
            spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
            recs = _run_block(alph, r, spec)
            state["records"].extend(recs)
            state["block_idx"] += 1
            _save_json(state, out_path)
            print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
                  f"{len(state['records'])} episodes so far, {time.time()-t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        _save_json(state, out_path)
        print(f"\n  EVAL COMPLETE: n={len(state['records'])}")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- "
              f"re-run '--stage eval' to continue.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# =============================================================================================
# STAGE: report -- McNemar FIRST, then accuracies/CIs, per-alphabet, rank-of-fixed, decisions.
# =============================================================================================
def _wilson(k: int, n: int) -> tuple:
    return gate.wilson_ci(k, n)


def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 37A -- CONTRASTIVE VERDICT -- FINAL REPORT\n{SEP}")
    ev_path = _ckpt("eval_run37a.json")
    if not os.path.exists(ev_path) or not _load_json(ev_path).get("done"):
        print("  eval not yet COMPLETE -- run --stage eval to completion first.")
        return 1
    records = _load_json(ev_path)["records"]
    n = len(records)
    print(f"  n={n}")

    # ---- PROTOCOL STOP: GLOBAL must reproduce 80.5% k=322 EXACTLY. ---------------------------
    k_full = sum(1 for r in records if r["pred_full"] == r["true"])
    acc_full = k_full / n
    ci_full = _wilson(k_full, n)
    global_ok = (k_full == BASELINE_FULL_DWELL["k"])
    print(f"\n  GLOBAL (protocol guard): acc={100*acc_full:.1f}% 95% CI "
          f"[{100*ci_full[0]:.1f}%, {100*ci_full[1]:.1f}%] k={k_full}/{n} "
          f"(must equal cited k={BASELINE_FULL_DWELL['k']}) -- "
          f"{'MATCH' if global_ok else 'MISMATCH -- STOP, protocol bug, do not trust CONTRASTIVE'}")
    if not global_ok:
        return 1

    k_contrastive = sum(1 for r in records if r["pred_contrastive"] == r["true"])
    acc_contrastive = k_contrastive / n
    ci_contrastive = _wilson(k_contrastive, n)

    # ---- PRIMARY: paired McNemar on same-episode flips. --------------------------------------
    fixed = [r for r in records
             if r["pred_full"] != r["true"] and r["pred_contrastive"] == r["true"]]
    broken = [r for r in records
              if r["pred_full"] == r["true"] and r["pred_contrastive"] != r["true"]]
    n_fixed, n_broken = len(fixed), len(broken)
    n_discordant = n_fixed + n_broken
    if n_discordant:
        bt = binomtest(n_fixed, n_discordant, 0.5, alternative="two-sided")
        p_value = float(bt.pvalue)
    else:
        p_value = 1.0

    print(f"\n  {'='*80}")
    print(f"  McNEMAR (PRIMARY, paired, exact two-sided binomial on discordant pairs):")
    print(f"  {'='*80}")
    print(f"    fixed  (global WRONG -> contrastive RIGHT): {n_fixed}")
    print(f"    broken (global RIGHT -> contrastive WRONG): {n_broken}")
    print(f"    discordant total: {n_discordant}   p-value: {p_value:.4f}")
    if n_discordant == 0:
        print(f"    (no discordant pairs at all -- the two arms never disagree)")
    elif n_broken >= n_fixed:
        print(f"    STOP CONDITION: broken >= fixed -- the mechanism HARMS or is a wash, "
              f"per pre-registration this is reported as the finding, not re-tuned.")
    else:
        print(f"    fixed > broken: the mechanism nets POSITIVE on this sample "
              f"({'CI/p SIGNIFICANT' if p_value < 0.05 else 'not significant at p<0.05'}).")

    print(f"\n  ACCURACIES (Wilson 95% CI):")
    print(f"    GLOBAL:      acc={100*acc_full:.1f}%  [{100*ci_full[0]:.1f}%, "
          f"{100*ci_full[1]:.1f}%]  k={k_full}/{n}")
    print(f"    CONTRASTIVE: acc={100*acc_contrastive:.1f}%  [{100*ci_contrastive[0]:.1f}%, "
          f"{100*ci_contrastive[1]:.1f}%]  k={k_contrastive}/{n}")
    ci_sep = gate._ci_separated(tuple(ci_contrastive), tuple(ci_full))
    print(f"    CI-separated: {ci_sep}  (McNemar above is the POWERED test for this effect "
          f"size -- CI overlap here does not contradict a significant McNemar p-value)")

    # ---- Per-alphabet fixed/broken. -----------------------------------------------------------
    print(f"\n  PER-ALPHABET fixed/broken:")
    per_alph: dict = {}
    for r in records:
        d = per_alph.setdefault(r["alph"], dict(fixed=0, broken=0, n=0))
        d["n"] += 1
    for r in fixed:
        per_alph[r["alph"]]["fixed"] += 1
    for r in broken:
        per_alph[r["alph"]]["broken"] += 1
    for alph in sorted(per_alph):
        d = per_alph[alph]
        print(f"    {alph:<22} n={d['n']:>3}  fixed={d['fixed']:>2}  broken={d['broken']:>2}")

    # ---- Rank-of-truth for GLOBAL error episodes: bounds what's fixable. ----------------------
    error_records = [r for r in records if r["pred_full"] != r["true"]]
    rank_hist: dict = {}
    for r in error_records:
        rk = r.get("true_rank")
        key = str(rk) if rk is not None else "unknown"
        rank_hist[key] = rank_hist.get(key, 0) + 1
    n_rank2 = rank_hist.get("2", 0)
    print(f"\n  RANK OF TRUE CLASS among GLOBAL error episodes ({len(error_records)} errors) -- "
          f"the mechanism can ONLY fix rank==2 (the global runner-up):")
    for k in sorted(rank_hist, key=lambda x: (x != "unknown", int(x) if x.isdigit() else 0)):
        print(f"    rank {k:<8} {rank_hist[k]:>3}")
    print(f"    A-PRIORI CEILING: {n_rank2}/{len(error_records)} error episodes have the true "
          f"class at rank 2 -- fixed ({n_fixed}) must be <= this ceiling "
          f"{'(CONSISTENT)' if n_fixed <= n_rank2 else '(ANOMALY -- investigate: a fix happened outside the mechanism bound)'}")

    # ---- cv_decision breakdown (the fire-rate substitute). -------------------------------------
    decisions: dict = {}
    for r in records:
        decisions[r.get("cv_decision", "?")] = decisions.get(r.get("cv_decision", "?"), 0) + 1
    print(f"\n  cv_decision BREAKDOWN (all {n} episodes -- 'always contrast top-2' means every "
          f"episode ENTERS the pass; this is what it found once inside):")
    for k in sorted(decisions):
        print(f"    {k:<28} {decisions[k]:>4}  ({100*decisions[k]/n:.1f}%)")

    single_stroke_fixed = sum(1 for r in fixed if r.get("cv_single_stroke"))
    one_sided_fixed = sum(1 for r in fixed if r.get("cv_decision") == "one_sided")
    print(f"\n  Among FIXED episodes: single_stroke degenerate-compare={single_stroke_fixed}/"
          f"{n_fixed}  one_sided={one_sided_fixed}/{n_fixed}")

    out = dict(n=n, global_acc=acc_full, global_ci=list(ci_full), global_k=k_full,
               contrastive_acc=acc_contrastive, contrastive_ci=list(ci_contrastive),
               contrastive_k=k_contrastive, n_fixed=n_fixed, n_broken=n_broken,
               mcnemar_p=p_value, per_alphabet=per_alph, rank_hist=rank_hist,
               n_rank2_ceiling=n_rank2, cv_decisions=decisions,
               single_stroke_fixed=single_stroke_fixed, one_sided_fixed=one_sided_fixed)
    _save_json(out, _ckpt("report.json"))
    print(f"\n  report.json written.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


STAGES = {"guard": stage_guard, "eval": stage_eval, "report": stage_report}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=list(STAGES.keys()))
    args = ap.parse_args()
    t0 = time.time()
    rc = STAGES[args.stage]()
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
