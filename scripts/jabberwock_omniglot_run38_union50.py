"""OMNIGLOT RUN 38 -- DOES THE THIRD MODALITY (COMMITTED SHAPE) EXTEND THE 50-WAY UNION?

RUN 25 (commit 6da31cee, `results/omniglot_gate_run25_number.log`) measured, at 50-way pooled
real Omniglot (`jabberwock_transfer_gate.pool_evaluation_characters(50)`), n=200:
  STRUCTURAL   acc=49.0%  coverage@10=53.5%
  APPEARANCE   acc=53.5%  coverage@10=61.5%
  UNION (2-way, structural shortlist UNION appearance shortlist)
               acc=66.5% [59.7,72.7]  coverage@union=76.5%  mean width=16.6
vs the RUN 24 full-dwell anchor 84.8% [79.8,88.7] @ n=250 (cited, not re-measured) -- the
different-angles-don't-overlap law (RUN 16), confirmed at scale.

RUN 37B (commit 6c1483b6) added a THIRD proposal modality, `domains/committed_shape.py`'s
committed-shape match (coarse per-stroke program-type identity, exact-then-1-edit,
`union_candidates` additive-only by construction), and at 20-way it moved coverage@10
71.5->76.5 (McNemar 20 fixed / 0 broken) and shortlist accuracy 62.0->66.0 (18/2,
p=0.0004), concentrated 100% in 1-2-stroke classes (RUN 36's own bucket convention).

THIS RUN asks whether the third modality extends the union at 50-way, where RUN 25's own
law -- "different angles don't overlap" -- has the most room (three modalities, not two).

PROTOCOL (clones RUN 25's workstream B EXACTLY): SAME `SCALE_SEED = gate.SEED + 24000`, SAME
`tg.pool_evaluation_characters(50)` candidate pool, SAME `tg._block_spec_pooled` block
construction (one continuing `np.random.default_rng(SCALE_SEED)` stream, block 0 byte-
identical to RUN 25's own "pilot" block), SAME structural (`ar.propose_top_k`, k=10) and
appearance (`ar.propose_appearance_top_m`, m=10) shortlist computation, SAME
`ar.stage_parse_char`/`parse_marginal_verdict` staged-verdict mechanism. RUN 25 itself
achieved n=200 (4 blocks) before its own 540s budget ran out (target was n=250/5 blocks) --
this run's ALIGNED-n comparison is at n=200 (the first 4 blocks of the SAME rng stream); if
wall-clock allows, blocks continue toward n=400 and BOTH n=200 and full-n are reported
(pre-registered, not chosen after the fact).

LEARN is NOT re-run: `results/run26_checkpoints/learn.json` is RUN 25's own LEARN output
byte-for-byte (`LEARN_ALPHABETS_N=5`, `LEARN_STROKE_CAP=1500`, `gate.DK`, deterministic
-- no RNG in `gate.run_learn` -- confirmed against `results/run26_checkpoints/
learn_meta.json`), so loading it is equivalent to re-running RUN 25's own LEARN, at zero
cost. READ-ONLY reference, never written here.

THE THIRD MODALITY is wired ADDITIVELY on top of the run-25 2-way union, per RUN 37A's law
(BINDING, cca938fd): "FOCUSED/WEAK EVIDENCE SUPPLEMENTS INTEGRATED EVIDENCE, NEVER REPLACES
IT." UNION-3 = `committed_shape.union_candidates(UNION-2, committed_proposal)` -- UNION-2's
own members and order are ALWAYS an unmodified prefix; the committed-shape proposal
(`propose_by_committed_shape`, k=`K_ADD_DEFAULT`=5) contributes only genuinely NEW indices.

DEGENERATE-STROKE FILTER (RUN 37C, `omniglot_world.load_strokes(..., drop_degenerate=True)`):
applied ONLY to the stroke lists fed into `committed_shape.commit_shape` (the explicit kwarg,
not the `DropDegenerateFilter` monkeypatch -- no other call in this script's `_run_block`
requests `drop_degenerate`, so the structural/appearance modalities are BYTE-IDENTICAL to
RUN 25's own computation; only the new modality's own stroke read is filtered, exactly as
RUN 37B's docstring specifies for "the commit computation only").

ARMS (same episodes, all four verdicts computed per query):
  STRUCTURAL-ALONE / APPEARANCE-ALONE -- RUN 25's own two single-modality arms (context).
  UNION-2   -- RUN 25's own union (structural shortlist UNION appearance shortlist). PROTOCOL
              GUARD: must reproduce RUN 25's cited k EXACTLY at n=200 (k_cov=153, k_acc=133)
              -- both modalities and the verdict mechanism are fully deterministic (no RNG
              downstream of the block spec), so this is an EXACT-match guard, not merely a
              CI-overlap one; CI-overlap is reported too as a fallback signal.
  UNION-3   -- UNION-2 unioned additively with the committed-shape proposal (this run's
              question).

PRIMARY (pre-registered): paired McNemar on COVERAGE flips, UNION-2 vs UNION-3 (fixed = true
class enters the candidate set; broken MUST be 0 by construction -- asserted as a STOP, not
merely reported, exactly as RUN 37B's own `stage_report` does). SECONDARY: paired McNemar on
converted-verdict ACCURACY flips (UNION-2 vs UNION-3 predictions). PREDICTIONS (stated before
any number is computed): (1) coverage gain concentrates in 1-2-stroke true classes (RUN 36's
own median-stroke-count bucket over each candidate's own drawer files, RUN 37B's bucket);
(2) accuracy follows coverage at roughly RUN 16's own historical ~70% conversion rate;
(3) the gap to the RUN 24 full-dwell anchor (84.8%) narrows but does not close.

STOPS: UNION-2 fails to reproduce RUN 25's cited numbers (exact k or, failing that, CI-
overlap) -> protocol bug, STOP, do not trust UNION-3. Coverage `broken > 0` for UNION-2 vs
UNION-3 -> impossible under a pure-additive union, STOP (bug in `union_candidates`'s own
wiring or in this script, not a research finding). Union width exceeding the pre-registered
cap (`2*SHORTLIST_K + K_ADD` = 25) paired with a CI-separated accuracy REGRESSION -> report
as the RUN-11 "widening hurts" dilution family and stop recommending the modality (report
still completes).

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run38.log`, per-BLOCK checkpoints under `results/run38_checkpoints/`
(every other `run*_checkpoints` dir, including `run26/learn.json` and `run35/programs.json`,
READ-ONLY reference -- never written here). `seeds/stroke_shapes.json` is read-only
(md5 recorded, per RUN 37C's own parallel-session discipline) -- never written here. `.venv`
python (needs `substrate_rs`).

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run38_union50.py --stage guard
  ... --stage eval        (re-invoke until COMPLETE or the full-n target is reached --
                            checkpointed per block; safe to stop after the aligned-n=200
                            checkpoint and still get a valid report)
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
import scripts.jabberwock_omniglot_run36_failures as run36
import scripts.jabberwock_transfer_gate as tg
from domains import abs_read as ar
from domains import committed_shape as cs
from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run38_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")   # READ-ONLY reference.
RUN35_DIR = os.path.join(ROOT, "results", "run35_checkpoints")   # READ-ONLY reference.
STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")   # parallel-session-
                                                                          # owned -- READ-ONLY.
os.makedirs(CKPT_DIR, exist_ok=True)

WAY = run25.SCALE_WAY_TARGET                           # 50
SHORTLIST_K = run25.SCALE_SHORTLIST_K                  # 10
SCALE_SEED = run25.SCALE_SEED                          # gate.SEED + 24000, byte-identical
DK = gate.DK
K_ADD = cs.K_ADD_DEFAULT                               # 5 -- pre-registered committed-shape cap
MAX_UNION2_WIDTH_CAP = 2 * SHORTLIST_K                  # 20 -- structural + appearance, disjoint
MAX_UNION3_WIDTH_CAP = MAX_UNION2_WIDTH_CAP + K_ADD     # 25 -- pre-registered explosion guard
N_BLOCKS_ALIGNED = 4                                    # RUN 25's own realized n=200 (4 x 50)
N_BLOCKS_FULL = 8                                       # extended target n=400 if budget allows
PER_CALL_BUDGET_SECONDS = 480.0                         # leaves >100s headroom under the 600s
                                                         # foreground cap; eval checkpoints per
                                                         # block.

# Cited VERBATIM from results/omniglot_gate_run25_number.log's own workstream-B block
# (n=200, way=50) -- the protocol-guard target for this run's UNION-2 arm.
RUN25_STRUCTURAL = dict(acc=0.490, ci=(0.422, 0.559), cov=0.535, n=200, k_acc=98, k_cov=107)
RUN25_APPEARANCE = dict(acc=0.535, ci=(0.466, 0.603), cov=0.615, n=200, k_acc=107, k_cov=123)
RUN25_UNION2 = dict(acc=0.665, ci=(0.597, 0.727), cov=0.765, n=200, k_acc=133, k_cov=153,
                     mean_width=16.6)
RUN24_FULL_DWELL_ANCHOR = run25.RUN24_FULL_DWELL_ANCHOR   # {"acc":0.848,"ci":(0.798,0.887),"n":250}


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


def _wilson(k: int, n: int) -> tuple:
    return gate.wilson_ci(k, n)


def _acc_ci(preds, trues) -> dict:
    return tg._acc_ci(preds, trues)


# ===============================================================================================
# ONE BLOCK (way=50 queries) -- structural-alone / appearance-alone / UNION-2 / UNION-3, all on
# the SAME exemplar pool + queries. Structural/appearance staging is BYTE-IDENTICAL to RUN 25's
# own `_run_block_B`; the committed-shape modality is the only new computation, and it is the
# ONLY caller in this function that requests `drop_degenerate=True`.
# ===============================================================================================
def _run_block(native, s, cache, edges, candidates, spec, way) -> list:
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, DK)
                 for ci in range(way)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]
    cand_raw_slices = [tg._raw_frame_slices(drawer_files[ci][ex_drawer]) for ci in range(way)]
    exemplar_commits = [
        cs.commit_shape(ow.load_strokes(drawer_files[ci][ex_drawer], drop_degenerate=True),
                         segments=DK["segments"], max_knots=DK["max_knots"], **edges)
        for ci in range(way)
    ]

    records = []
    for qi, q_drawer in spec["queries"]:
        qpath = drawer_files[qi][q_drawer]
        rec: dict = {"true": qi}

        qd = gate.decode_char_signature(s, qpath, cache, DK)
        q_composed = qd["composed_sig"]
        q_raw_slices = tg._raw_frame_slices(qpath)

        shortlist_struct = ar.propose_top_k(native, q_composed, exemplar_composed, k=SHORTLIST_K)
        shortlist_app = ar.propose_appearance_top_m(native, q_raw_slices, cand_raw_slices,
                                                      m=SHORTLIST_K)
        rec["in_structural"] = bool(qi in shortlist_struct)
        rec["in_appearance"] = bool(qi in shortlist_app)

        query_commit = cs.commit_shape(ow.load_strokes(qpath, drop_degenerate=True),
                                        segments=DK["segments"], max_knots=DK["max_knots"],
                                        **edges)
        committed = cs.propose_by_committed_shape(query_commit, exemplar_commits, k=K_ADD)
        rec["query_commit"] = query_commit
        rec["match_kind"] = cs.match_kind(query_commit, exemplar_commits)
        rec["in_committed"] = bool(qi in committed)

        union2 = sorted(set(shortlist_struct) | set(shortlist_app))
        union3 = cs.union_candidates(union2, committed)
        rec["union2_width"] = len(union2)
        rec["union3_width"] = len(union3)
        rec["committed_added"] = len(union3) - len(union2)
        rec["committed_only_new"] = [c for c in committed if c not in set(union2)]
        rec["struct_only_count"] = len(set(shortlist_struct) - set(shortlist_app))
        rec["app_only_count"] = len(set(shortlist_app) - set(shortlist_struct))
        rec["both_sa_count"] = len(set(shortlist_struct) & set(shortlist_app))
        rec["in_union2"] = bool(qi in union2)
        rec["in_union3"] = bool(qi in union3)

        # STRUCTURAL-ALONE verdict (RUN 25's own arm, context).
        scratch_s = srs.Substrate()
        cand_s = {}
        for ci in shortlist_struct:
            node = ar.stage_parse_char(scratch_s, drawer_files[ci][ex_drawer], is_query=False,
                                        name=str(ci))
            cand_s[node] = ci
        qn_s = ar.stage_parse_char(scratch_s, qpath, is_query=True)
        w_s = ar.parse_marginal_verdict(scratch_s, qn_s)
        rec["pred_structural"] = cand_s.get(w_s, -1) if w_s is not None else -1

        # APPEARANCE-ALONE verdict (RUN 25's own arm, context).
        scratch_a = srs.Substrate()
        cand_a = {}
        for ci in shortlist_app:
            node = ar.stage_parse_char(scratch_a, drawer_files[ci][ex_drawer], is_query=False,
                                        name=str(ci))
            cand_a[node] = ci
        qn_a = ar.stage_parse_char(scratch_a, qpath, is_query=True)
        w_a = ar.parse_marginal_verdict(scratch_a, qn_a)
        rec["pred_appearance"] = cand_a.get(w_a, -1) if w_a is not None else -1

        # UNION-2 verdict (RUN 25's own union arm).
        scratch_u2 = srs.Substrate()
        cand_u2 = {}
        for ci in union2:
            node = ar.stage_parse_char(scratch_u2, drawer_files[ci][ex_drawer], is_query=False,
                                        name=str(ci))
            cand_u2[node] = ci
        qn_u2 = ar.stage_parse_char(scratch_u2, qpath, is_query=True)
        w_u2 = ar.parse_marginal_verdict(scratch_u2, qn_u2)
        rec["pred_union2"] = cand_u2.get(w_u2, -1) if w_u2 is not None else -1

        # UNION-3 verdict -- only re-staged when the union genuinely differs from UNION-2
        # (additive-invariant optimization, RUN 37B's own precedent: `union3 == union2` as
        # sets means the SAME verdict mechanism over the SAME members produces the SAME
        # winner, so the second staging pass would be wasted work).
        if set(union3) == set(union2):
            rec["pred_union3"] = rec["pred_union2"]
        else:
            scratch_u3 = srs.Substrate()
            cand_u3 = {}
            for ci in union3:
                node = ar.stage_parse_char(scratch_u3, drawer_files[ci][ex_drawer],
                                            is_query=False, name=str(ci))
                cand_u3[node] = ci
            qn_u3 = ar.stage_parse_char(scratch_u3, qpath, is_query=True)
            w_u3 = ar.parse_marginal_verdict(scratch_u3, qn_u3)
            rec["pred_union3"] = cand_u3.get(w_u3, -1) if w_u3 is not None else -1

        records.append(rec)
    return records


# ===============================================================================================
# STAGE: guard -- sanity (candidate pool, edges, LEARN load) + ONE block's timing (block 0,
# byte-identical construction to RUN 25's own "pilot" block).
# ===============================================================================================
def stage_guard() -> int:
    print(f"\n{SEP}\n  STAGE: guard -- sanity + block-0 timing\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_PATH)
    print(f"  seeds/stroke_shapes.json md5 (parallel-session-owned, this run never writes "
          f"there): {md5_now}")

    candidates, pool_size = tg.pool_evaluation_characters(WAY)
    way = len(candidates)
    print(f"  pooled {pool_size} qualifying evaluation characters, way={way} (target {WAY}).")
    ok_way = (way == WAY)
    if not ok_way:
        print(f"  WALL: way={way} != target {WAY} -- pool composition has drifted since RUN 25.")

    edges = cs.load_cited_program_edges(os.path.join(RUN35_DIR, "programs.json"))
    print(f"  CITED committed-shape edges (results/run35_checkpoints/programs.json, never "
          f"refit here): tol_deg={edges['tol_deg']:.4f}  "
          f"level_edges({len(edges['level_edges'])-1} bins)  "
          f"delta_edges({len(edges['delta_edges'])-1} bins)")

    src = os.path.join(RUN26_DIR, "learn.json")
    t0 = time.time()
    s = run26._load_graph(src)
    native = s._inner
    print(f"  learn.json loaded ({time.time()-t0:.1f}s) -- RUN 25's own LEARN output "
          f"(byte-identical protocol per learn_meta.json), READ-ONLY reference.")

    cache: dict = {}
    rng = np.random.default_rng(SCALE_SEED)
    spec0 = tg._block_spec_pooled(candidates, rng, way)
    t0 = time.time()
    block0 = _run_block(native, s, cache, edges, candidates, spec0, way)
    elapsed0 = time.time() - t0
    print(f"  block 0 (way={way}, {way} queries, all 4 arms): {elapsed0:.1f}s")

    projected_aligned = elapsed0 * N_BLOCKS_ALIGNED
    projected_full = elapsed0 * N_BLOCKS_FULL
    print(f"  projection: {N_BLOCKS_ALIGNED} blocks (aligned n={N_BLOCKS_ALIGNED*way}) = "
          f"{projected_aligned:.0f}s;  {N_BLOCKS_FULL} blocks (full n={N_BLOCKS_FULL*way}) = "
          f"{projected_full:.0f}s")

    match_kinds = {}
    for g in block0:
        match_kinds[g["match_kind"]] = match_kinds.get(g["match_kind"], 0) + 1
    n_added = sum(1 for g in block0 if g["committed_added"] > 0)
    width_ok = all(g["union3_width"] >= g["union2_width"] >= min(SHORTLIST_K, way) for g in block0)
    print(f"  committed-shape match_kind on block 0: {match_kinds}")
    print(f"  episodes where committed shape added a genuinely new candidate: "
          f"{n_added}/{len(block0)}")
    print(f"  additive-width sanity (union3 >= union2 >= shortlist size): "
          f"{'OK' if width_ok else 'VIOLATION -- investigate union_candidates'}")

    guard_ok = ok_way and width_ok
    out = dict(guard_ok=guard_ok, stroke_shapes_md5=md5_now, edges=edges, way=way,
               candidates=candidates, elapsed0=elapsed0, match_kinds_block0=match_kinds,
               n_added_block0=n_added, width_ok=width_ok)
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
        print("  WALL: --stage guard did not PASS -- fix the protocol mismatch before "
              "--stage eval.")
        sys.exit(1)
    return g


# ===============================================================================================
# STAGE: eval -- checkpointed per block, toward N_BLOCKS_FULL (n=400); safe to stop after
# N_BLOCKS_ALIGNED (n=200) and still get a valid aligned-n report.
# ===============================================================================================
def stage_eval() -> int:
    print(f"\n{SEP}\n  STAGE: eval -- toward n={N_BLOCKS_FULL*WAY} (aligned checkpoint at "
          f"n={N_BLOCKS_ALIGNED*WAY})\n{SEP}")
    guard = _require_guard()
    edges = guard["edges"]
    candidates = guard["candidates"]
    way = guard["way"]
    out_path = _ckpt("eval_run38.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval already COMPLETE (n={len(state['records'])}).")
        return 0

    src = os.path.join(RUN26_DIR, "learn.json")
    t0 = time.time()
    s = run26._load_graph(src)
    native = s._inner
    print(f"  learn.json loaded ({time.time()-t0:.1f}s) -- READ-ONLY reference.")

    print(f"  target blocks: {N_BLOCKS_FULL} (aligned checkpoint at {N_BLOCKS_ALIGNED}), "
          f"resuming at block {state['block_idx']}")

    # Re-seed and FAST-FORWARD the rng deterministically to the resume point -- the SAME
    # idiom RUN 37B's own `stage_eval` uses to make checkpointed resumption byte-identical
    # to an uninterrupted run.
    rng = np.random.default_rng(SCALE_SEED)
    for _ in range(state["block_idx"]):
        tg._block_spec_pooled(candidates, rng, way)

    cache: dict = {}
    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t_loop0 = time.time()
    while state["block_idx"] < N_BLOCKS_FULL and time.time() < hard_deadline:
        spec = tg._block_spec_pooled(candidates, rng, way)
        recs = _run_block(native, s, cache, edges, candidates, spec, way)
        state["records"].extend(recs)
        state["block_idx"] += 1
        _save_json(state, out_path)
        tag = " <-- ALIGNED n=200 CHECKPOINT" if state["block_idx"] == N_BLOCKS_ALIGNED else ""
        print(f"  block {state['block_idx']}/{N_BLOCKS_FULL} done -- "
              f"{len(state['records'])} episodes so far, {time.time()-t_loop0:.1f}s this "
              f"call{tag}")

    if state["block_idx"] >= N_BLOCKS_FULL:
        state["done"] = True
        _save_json(state, out_path)
        print(f"\n  EVAL COMPLETE: n={len(state['records'])}")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{N_BLOCKS_FULL} blocks done -- "
              f"re-run '--stage eval' to continue (report can already run at n="
              f"{min(state['block_idx'], N_BLOCKS_ALIGNED)*way if state['block_idx'] >= N_BLOCKS_ALIGNED else 'not yet aligned'}).")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: report
# ===============================================================================================
def _bucket_of_candidates(candidates: list) -> dict:
    """Median stroke count per CANDIDATE (over its own drawer files, RUN 36's own convention),
    independent of block/ex_drawer -- the same 50 candidates are used in every block."""
    out = {}
    for ci, cd in enumerate(candidates):
        counts = [len(ow.load_strokes(f)) for f in ow.drawings(cd)]
        out[ci] = run36._bucket(float(np.median(counts)))
    return out


def _mcnemar_block(name: str, fixed_n: int, broken_n: int, allow_nonzero_broken: bool) -> dict:
    n_disc = fixed_n + broken_n
    p = float(binomtest(fixed_n, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    print(f"\n  {'='*80}\n  McNEMAR -- {name}\n  {'='*80}")
    print(f"    fixed  : {fixed_n}")
    print(f"    broken : {broken_n}"
          + ("" if allow_nonzero_broken else
             ("  (MUST be 0 by construction)" if broken_n == 0 else
              "  <-- STOP: nonzero broken under a pure-additive union is a PROTOCOL BUG")))
    print(f"    discordant total: {n_disc}   p-value: {p:.4g}")
    return dict(fixed=fixed_n, broken=broken_n, discordant=n_disc, p=p)


def _report_at_n(records: list, candidates: list, buckets: dict, label: str) -> dict:
    n = len(records)
    print(f"\n{SEP}\n  REPORT @ {label} (n={n})\n{SEP}")

    k_struct_acc = sum(1 for r in records if r["pred_structural"] == r["true"])
    k_struct_cov = sum(1 for r in records if r["in_structural"])
    k_app_acc = sum(1 for r in records if r["pred_appearance"] == r["true"])
    k_app_cov = sum(1 for r in records if r["in_appearance"])
    k_u2_acc = sum(1 for r in records if r["pred_union2"] == r["true"])
    k_u2_cov = sum(1 for r in records if r["in_union2"])
    k_u3_acc = sum(1 for r in records if r["pred_union3"] == r["true"])
    k_u3_cov = sum(1 for r in records if r["in_union3"])

    def _row(tag, k_acc, k_cov):
        acc, ci_acc = k_acc / n, _wilson(k_acc, n)
        cov, ci_cov = k_cov / n, _wilson(k_cov, n)
        print(f"  {tag:<12} acc={100*acc:5.1f}% 95%CI[{100*ci_acc[0]:5.1f},{100*ci_acc[1]:5.1f}] "
              f"k={k_acc:>3}/{n:<3}   cov={100*cov:5.1f}% 95%CI[{100*ci_cov[0]:5.1f},"
              f"{100*ci_cov[1]:5.1f}] k={k_cov:>3}/{n}")
        return dict(acc=acc, ci_acc=ci_acc, k_acc=k_acc, cov=cov, ci_cov=ci_cov, k_cov=k_cov, n=n)

    r_struct = _row("STRUCTURAL", k_struct_acc, k_struct_cov)
    r_app = _row("APPEARANCE", k_app_acc, k_app_cov)
    r_u2 = _row("UNION-2", k_u2_acc, k_u2_cov)
    r_u3 = _row("UNION-3", k_u3_acc, k_u3_cov)

    # ---- PROTOCOL GUARD (only meaningful at n=200, the aligned checkpoint). -------------------
    guard_result = None
    if n == RUN25_UNION2["n"]:
        exact_acc = (k_u2_acc == RUN25_UNION2["k_acc"])
        exact_cov = (k_u2_cov == RUN25_UNION2["k_cov"])
        ci_overlap_acc = not (r_u2["ci_acc"][1] < RUN25_UNION2["ci"][0]
                               or RUN25_UNION2["ci"][1] < r_u2["ci_acc"][0])
        print(f"\n  PROTOCOL GUARD vs RUN 25's cited UNION-2 @ n=200 "
              f"(acc={100*RUN25_UNION2['acc']:.1f}% k={RUN25_UNION2['k_acc']}, "
              f"cov={100*RUN25_UNION2['cov']:.1f}% k={RUN25_UNION2['k_cov']}):")
        print(f"    accuracy k EXACT match: {'YES' if exact_acc else 'NO'} "
              f"(got k={k_u2_acc}, cited k={RUN25_UNION2['k_acc']})")
        print(f"    coverage k EXACT match: {'YES' if exact_cov else 'NO'} "
              f"(got k={k_u2_cov}, cited k={RUN25_UNION2['k_cov']})")
        print(f"    accuracy CI-overlap (fallback signal): {ci_overlap_acc}")
        guard_result = dict(exact_acc=exact_acc, exact_cov=exact_cov,
                             ci_overlap_acc=ci_overlap_acc)
        if not (exact_acc and exact_cov):
            if not ci_overlap_acc:
                print(f"    STOP CANDIDATE: UNION-2 fails to reproduce RUN 25 both exactly "
                      f"AND within CI -- treat as a protocol bug; UNION-3 conclusions below "
                      f"are NOT trustworthy until this is resolved.")
            else:
                print(f"    NOTE: exact-k reproduction failed but CI overlaps -- inspect for "
                      f"a benign nondeterminism source (should not exist in this pipeline; "
                      f"every decision here is a held Argmax/Argmin over deterministic "
                      f"inputs) before trusting UNION-3 fully.")

    # ---- PRIMARY: paired McNemar, coverage, UNION-2 vs UNION-3. -------------------------------
    cov_fixed_idx = [i for i, r in enumerate(records) if not r["in_union2"] and r["in_union3"]]
    cov_broken_idx = [i for i, r in enumerate(records) if r["in_union2"] and not r["in_union3"]]
    mc_cov = _mcnemar_block("PRIMARY -- COVERAGE flips, UNION-2 -> UNION-3",
                             len(cov_fixed_idx), len(cov_broken_idx),
                             allow_nonzero_broken=False)
    coverage_stop = len(cov_broken_idx) > 0
    if coverage_stop:
        print(f"    STOP: broken coverage > 0 is impossible under a pure-additive union -- "
              f"investigate `union_candidates` wiring in this script before trusting "
              f"anything below.")

    # ---- Per-stroke-bucket concentration of gained-coverage episodes. -------------------------
    bucket_order = ["1", "2", "3", "4", "5+"]
    bucket_totals = {b: 0 for b in bucket_order}
    bucket_fixed = {b: 0 for b in bucket_order}
    for i, r in enumerate(records):
        b = buckets[r["true"]]
        bucket_totals[b] += 1
        if i in cov_fixed_idx:
            bucket_fixed[b] += 1
    print(f"\n  PER-STROKE-BUCKET concentration of gained-coverage episodes (median stroke "
          f"count of the TRUE candidate; prediction: concentrates in 1-2):")
    for b in bucket_order:
        tot, fx = bucket_totals[b], bucket_fixed[b]
        rate = f"{100*fx/tot:.1f}%" if tot else "n/a"
        print(f"    strokes={b:<3}  gained={fx:>3}/{tot:<3}  share-of-episodes-in-bucket={rate}")
    low_stroke_fixed = bucket_fixed["1"] + bucket_fixed["2"]
    n_fixed = len(cov_fixed_idx)
    if n_fixed:
        print(f"    1-2-stroke share of ALL gained-coverage episodes: {low_stroke_fixed}/"
              f"{n_fixed} = {100*low_stroke_fixed/n_fixed:.1f}%")
    else:
        print(f"    1-2-stroke share of ALL gained-coverage episodes: n/a (0 gained)")

    # ---- SECONDARY: paired McNemar, accuracy, UNION-2 vs UNION-3. -----------------------------
    acc_fixed = [r for r in records
                 if r["pred_union2"] != r["true"] and r["pred_union3"] == r["true"]]
    acc_broken = [r for r in records
                  if r["pred_union2"] == r["true"] and r["pred_union3"] != r["true"]]
    mc_acc = _mcnemar_block("SECONDARY -- ACCURACY flips, UNION-2 -> UNION-3",
                             len(acc_fixed), len(acc_broken), allow_nonzero_broken=True)
    if mc_acc["discordant"] == 0:
        print(f"    (no discordant pairs -- the two arms never disagree on the verdict)")
    elif mc_acc["broken"] >= mc_acc["fixed"]:
        print(f"    NOTE: broken >= fixed -- widening diluted the verdict as often as (or "
              f"more than) it helped (the RUN-11 dilution risk this design measures for).")
    else:
        print(f"    fixed > broken: coverage gains are converting to accuracy gains "
              f"({'significant at p<0.05' if mc_acc['p'] < 0.05 else 'not significant at p<0.05'}).")
    conversion_rate = (mc_acc["fixed"] / n_fixed) if n_fixed else float("nan")
    if n_fixed:
        print(f"    CONVERSION: {mc_acc['fixed']}/{n_fixed} = {100*conversion_rate:.1f}% of "
              f"gained-coverage episodes converted to a correct verdict (RUN 16's cited "
              f"historical rate: ~70%).")
    else:
        print(f"    CONVERSION: n/a (0 gained-coverage episodes).")

    # ---- Union width distributions. ------------------------------------------------------------
    w2 = [r["union2_width"] for r in records]
    w3 = [r["union3_width"] for r in records]
    added = [r["committed_added"] for r in records]
    hist2, hist3 = {}, {}
    for w in w2:
        hist2[str(w)] = hist2.get(str(w), 0) + 1
    for w in w3:
        hist3[str(w)] = hist3.get(str(w), 0) + 1
    max_w3 = max(w3)
    print(f"\n  UNION-2 WIDTH: mean={np.mean(w2):.2f} median={np.median(w2):.1f} "
          f"max={max(w2)} (cap={MAX_UNION2_WIDTH_CAP})  "
          f"histogram={dict(sorted(hist2.items(), key=lambda kv: int(kv[0])))}")
    print(f"  UNION-3 WIDTH: mean={np.mean(w3):.2f} median={np.median(w3):.1f} "
          f"max={max_w3} (cap={MAX_UNION3_WIDTH_CAP})  "
          f"histogram={dict(sorted(hist3.items(), key=lambda kv: int(kv[0])))}")
    print(f"  committed_added: mean={np.mean(added):.2f}  "
          f"episodes_with_addition={sum(1 for a in added if a>0)}/{n} "
          f"({100*sum(1 for a in added if a>0)/n:.1f}%)")
    width_exploded = max_w3 > MAX_UNION3_WIDTH_CAP

    # ---- Commit engagement stats (match_kind, exact-match rate vs 20-way RUN 37B). -------------
    match_kinds: dict = {}
    for r in records:
        match_kinds[r["match_kind"]] = match_kinds.get(r["match_kind"], 0) + 1
    print(f"\n  ENGAGEMENT -- match_kind breakdown (all {n} episodes, 50-way pool -- more "
          f"exemplars per query than 37B's 20-way, exact-match rate predicted to RISE):")
    for k in sorted(match_kinds):
        print(f"    {k:<8} {match_kinds[k]:>4}  ({100*match_kinds[k]/n:.1f}%)")
    all_commits = [r["query_commit"] for r in records]
    commit_hist: dict = {}
    for c in all_commits:
        commit_hist[c] = commit_hist.get(c, 0) + 1
    n_distinct = len(commit_hist)
    top = sorted(commit_hist.items(), key=lambda kv: -kv[1])[:10]
    top3_share = sum(c for _, c in top[:3]) / len(all_commits) if all_commits else 0.0
    print(f"  COMMIT-TYPE ENGAGEMENT: {n_distinct} distinct committed shapes among {n} queries; "
          f"top-3 share={100*top3_share:.1f}%")
    print(f"  top 10 by frequency: {top}")

    # ---- Per-modality unique-contribution table. ------------------------------------------------
    n_struct_only = sum(r["struct_only_count"] for r in records)
    n_app_only = sum(r["app_only_count"] for r in records)
    n_both_sa = sum(r["both_sa_count"] for r in records)
    n_committed_only_new = sum(len(r["committed_only_new"]) for r in records)
    committed_only_gain_episodes = sum(1 for r in records if r["committed_only_new"]
                                        and any(c == r["true"] for c in r["committed_only_new"]))
    print(f"\n  PER-MODALITY UNIQUE-CONTRIBUTION (summed candidate counts across all "
          f"{n} episodes):")
    print(f"    structural-only candidates (in struct, not in appearance): {n_struct_only} "
          f"(mean {n_struct_only/n:.2f}/query)")
    print(f"    appearance-only candidates (in appearance, not in struct): {n_app_only} "
          f"(mean {n_app_only/n:.2f}/query)")
    print(f"    shared struct+appearance candidates: {n_both_sa} (mean {n_both_sa/n:.2f}/query)")
    print(f"    committed-shape-only NEW candidates (not already in UNION-2): "
          f"{n_committed_only_new} (mean {n_committed_only_new/n:.2f}/query)")
    print(f"    episodes where committed-shape's OWN unique addition included the TRUE class: "
          f"{committed_only_gain_episodes} (this is exactly the coverage-fixed count when the "
          f"true class was struct/appearance-blind AND committed-shape-only-found)")

    # ---- Honest anomalies. -----------------------------------------------------------------------
    print(f"\n  {'='*80}\n  HONEST ANOMALIES @ {label}\n  {'='*80}")
    anomalies = []
    if coverage_stop:
        anomalies.append("coverage broken > 0 -- PROTOCOL BUG (see PRIMARY McNemar above).")
    if width_exploded:
        anomalies.append(f"union-3 width exceeded the pre-registered cap "
                          f"({max_w3} > {MAX_UNION3_WIDTH_CAP}).")
    if width_exploded and mc_acc["broken"] > mc_acc["fixed"]:
        anomalies.append("width explosion PAIRED WITH a net accuracy REGRESSION -- the "
                          "RUN-11 'widening hurts' dilution family; recommend NOT adopting "
                          "the modality as configured.")
    if n_fixed == 0:
        anomalies.append("zero gained-coverage episodes -- committed-shape never engaged "
                          "where UNION-2 was already blind.")
    if not anomalies:
        print("  none -- the modality behaved as designed (pure-additive coverage gain, "
              "no width explosion).")
    else:
        for a in anomalies:
            print(f"  - {a}")

    gap_to_full_dwell = RUN24_FULL_DWELL_ANCHOR["acc"] - r_u3["acc"]
    print(f"\n  GAP TO RUN-24 FULL-DWELL ANCHOR ({100*RUN24_FULL_DWELL_ANCHOR['acc']:.1f}% "
          f"{[round(100*x,1) for x in RUN24_FULL_DWELL_ANCHOR['ci']]} @ "
          f"n={RUN24_FULL_DWELL_ANCHOR['n']}): UNION-3 leaves {100*gap_to_full_dwell:.1f}pp "
          f"unclosed (UNION-2 left "
          f"{100*(RUN24_FULL_DWELL_ANCHOR['acc']-r_u2['acc']):.1f}pp).")

    return dict(n=n, r_struct=r_struct, r_app=r_app, r_u2=r_u2, r_u3=r_u3,
                guard_result=guard_result, mc_cov=mc_cov, mc_acc=mc_acc,
                coverage_stop=coverage_stop, width_exploded=width_exploded,
                bucket_totals=bucket_totals, bucket_fixed=bucket_fixed,
                match_kinds=match_kinds, n_distinct_commits=n_distinct, top3_share=top3_share,
                anomalies=anomalies)


def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 38 -- 50-WAY UNION + COMMITTED SHAPE -- FINAL REPORT\n{SEP}")
    ev_path = _ckpt("eval_run38.json")
    if not os.path.exists(ev_path):
        print("  eval not started -- run --stage eval first.")
        return 1
    state = _load_json(ev_path)
    records = state["records"]
    n = len(records)
    print(f"  n={n} (block_idx={state['block_idx']}, done={state.get('done')})")
    if n < N_BLOCKS_ALIGNED * WAY:
        print(f"  NOT YET at the aligned n={N_BLOCKS_ALIGNED*WAY} checkpoint -- re-run "
              f"--stage eval to continue.")
        return 1

    guard = _require_guard()
    candidates = guard["candidates"]
    buckets = _bucket_of_candidates(candidates)

    aligned_records = records[:N_BLOCKS_ALIGNED * WAY]
    aligned = _report_at_n(aligned_records, candidates, buckets,
                            f"ALIGNED n={N_BLOCKS_ALIGNED*WAY} (matched to RUN 25)")

    full = None
    if n > N_BLOCKS_ALIGNED * WAY:
        full = _report_at_n(records, candidates, buckets, f"FULL n={n}")
    else:
        print(f"\n  (no FULL-n report beyond the aligned n={N_BLOCKS_ALIGNED*WAY} checkpoint "
              f"-- eval stopped there; re-run --stage eval to extend toward "
              f"n={N_BLOCKS_FULL*WAY}.)")

    out = dict(aligned=aligned, full=full, n_total=n, done=state.get("done"))
    _save_json(out, _ckpt("report.json"))
    print(f"\n  report.json written.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# MAIN
# ===============================================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["guard", "eval", "report"], required=True)
    args = ap.parse_args()
    if args.stage == "guard":
        return stage_guard()
    if args.stage == "eval":
        return stage_eval()
    return stage_report()


if __name__ == "__main__":
    sys.exit(main())
