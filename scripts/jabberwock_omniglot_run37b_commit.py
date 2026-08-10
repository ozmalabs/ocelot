"""OMNIGLOT RUN 37B -- GAP B, THE COMMITTED SHAPE: a THIRD PROPOSAL MODALITY, ADDITIVE ONLY.

`results/run37_checkpoints/plan.json` (commit 67005b35, the jabberwock's own plan) grounds
Gap B -- RUN 36's (5aa6bcb6) finding that 1-2-stroke classes carry the proposal/shortlist
failure mass (proposal-blind 31-40%, shortlist-error 41-49% vs 21-24% at 4+ strokes, because
the structural composed-signature proposal has almost no ARRANGEMENT to grab onto when a
glyph is 1-2 strokes), redesigned under RUN 37A's law (cca938fd, BINDING): "FOCUSED/WEAK
EVIDENCE SUPPLEMENTS INTEGRATED EVIDENCE, NEVER REPLACES IT." RUN 37A tried a focused-look
VERDICT REPLACEMENT and it harmed broadly; Gap B is built the other way -- a weak, focused
PROPOSAL modality that only ever ADDS candidates into the union with the existing structural
shortlist, never removes or reorders anyone. The arc's one repeatedly-confirmed positive
lever, PROPOSAL UNION (RUN 25: +13pp at 50-way unioning modalities that don't overlap), is the
shape this run measures.

THE MECHANISM (`domains/committed_shape.py`, see that module's own top-of-file docstring for
the full design -- this docstring restates only what is BINDING for this gate):
  1. COMMIT -- each candidate/query glyph commits a coarse per-stroke program-type identity
     (`committed_shape.commit_shape`: denoise each stroke globally (`mouse_model.
     denoise_path_global`) -> RUN 35's own per-stroke program tokenizer
     (`stroke_programs.tokenize_turn_sequence`) -> COARSE grain (token types only, e.g.
     "L-A-R") -> joined across strokes in draw order with ";", e.g. "L-A-R;L"). Cited edges
     (`tol_deg`/`level_edges`/`delta_edges`) come VERBATIM from `results/run35_checkpoints/
     programs.json` -- RUN 35's own already-fit LEARN population, never refit here.
  2. PROPOSE -- `committed_shape.propose_by_committed_shape`: exact committed-shape match
     first; a pre-registered 1-token-edit-distance fallback ONLY when exact match is empty;
     capped at `K_ADD` (5, never tuned per-query).
  3. UNION -- `committed_shape.union_candidates`: the existing structural shortlist
     (`abs_read.propose_top_k`, `SHORTLIST_K=10`) is ALWAYS an unmodified, order-preserved
     PREFIX of the result; committed-shape candidates contribute only genuinely NEW indices.
     This is RUN 37A's law enforced STRUCTURALLY (see `committed_shape.py`'s own docstring
     and `tests/test_committed_shape_migrated.py`'s own additive-invariant gate), not by
     discipline alone.
  4. VERDICT -- the SAME `abs_read.stage_parse_char` + `parse_marginal_verdict` staged over
     whichever candidate set (shortlist-only for BASELINE, the union for the UNION arm) --
     the verdict MECHANISM never changes, only which candidates it is asked to stage and
     choose among (exactly run26/37c's own shortlist-arm staging, extended to a wider set).

Every stroke load in this script goes through `run37c_hygiene.DropDegenerateFilter` --
MANDATORY (RUN 37C's own filter protects the per-stroke geometry the commit tokenizer reads,
same as RUN 37A's difference-element matcher needed it).

GATE DESIGN (this script, clones the RUN 26/34/37A/37C eval skeleton):
  Arms, on the SAME 400 episodes, SAME protocol (`run25._block_spec`, `POWER_SEED =
  gate.SEED + 1500`, WAY=20, R_TARGET=2, N_TEST_ALPHABETS=10 sorted-name prefix, alph OUTER /
  r INNER block order -- byte-identical to `results/run26_checkpoints/eval_baseline.json`):
    BASELINE  -- the standard structural shortlist@10 (`abs_read.propose_top_k` -> stage the
                 shortlist -> `parse_marginal_verdict`). Must reproduce coverage 71.5%
                 [66.9,75.7] k=286 and shortlist acc 62.0% [57.2,66.6] k=248 EXACTLY (protocol
                 guard, cited verbatim from `eval_baseline.json`'s own `coverage`/
                 `shortlist_acc` blocks).
    UNION     -- baseline shortlist UNIONED with committed-shape proposals (step 3 above),
                 verdict = the SAME `parse_marginal_verdict` staged over the union's members
                 (an OPTIMIZATION, not a semantic difference: when the union equals the
                 shortlist as a set -- i.e. the committed-shape modality added nothing new --
                 the union verdict is byte-identical to the baseline verdict by construction,
                 so this script skips the redundant second staging pass and copies the
                 baseline prediction; `tests/test_committed_shape_migrated.py`'s own additive
                 invariant is what makes this optimization safe).

  PRIMARY (pre-registered, `stage_report`): PAIRED McNemar on COVERAGE flips (does the query's
  true class enter or leave the candidate set) -- fixed (baseline query NOT covered -> union
  covered) vs broken (baseline covered -> union NOT covered). Because `union_candidates` is a
  pure superset by construction, `broken` on coverage MUST be exactly 0 -- this script asserts
  it as a structural invariant, not merely reports it; a nonzero value is a WALL (protocol
  bug), not a finding. PREDICTION (stated before any number is computed): gained-coverage
  episodes CONCENTRATE in 1-2-stroke true classes (RUN 36's own bucket convention,
  `run36_failures._bucket` on the median stroke count of the true class over its own 20
  drawer files, reused verbatim -- not reimplemented). SECONDARY McNemar: shortlist-ACCURACY
  flips (`pred_shortlist` vs `pred_union`) -- here `broken` CAN be nonzero (a query already
  covered by the baseline shortlist can still flip to a wrong verdict once more candidates
  enter the SAME parse-marginal argmax pool -- the run-11 "widening hurts" dilution risk this
  design is built to detect, not assume away). PREDICTION: coverage gains convert to accuracy
  gains at roughly RUN 16's own historical ~70% rate when the true exemplar is newly present.

  STOPS (checked in `stage_report`, never silently bypassed): BASELINE must reproduce the
  cited coverage/shortlist-acc k values EXACTLY -- a mismatch is a protocol bug, STOP, do not
  trust the UNION arm. Coverage `broken > 0` is impossible by construction and is itself a
  STOP (a bug in `union_candidates`, not a research finding) if it ever fires. A union-width
  explosion (max width exceeding the pre-registered cap `SHORTLIST_K + K_ADD = 15`) paired
  with a shortlist-accuracy REGRESSION (UNION CI below BASELINE CI) is reported as the
  DILUTION finding (RUN 11's own "widening hurts" family) and this script stops recommending
  the modality, though it still completes the report.

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run37b.log`, per-BLOCK checkpoints under `results/run37b_checkpoints/`
(every OTHER run*_checkpoints dir, including run26's own `learn.json`/`eval_baseline.json`,
run35's own `programs.json`, and run34d's own `edges_report.json`, READ-ONLY reference --
never written here). `.venv` python (needs `substrate_rs`). `seeds/stroke_shapes.json` is
READ (md5 recorded, per `run37c_hygiene.py`'s own parallel-session discipline) but never
written -- verify with `md5sum` before/after any invocation.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run37b_commit.py --stage guard
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
import scripts.jabberwock_omniglot_run36_failures as run36
from domains import abs_read as ar
from domains import committed_shape as cs
from domains import omniglot_world as ow
from scripts.jabberwock_omniglot_run37c_hygiene import DropDegenerateFilter

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run37b_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")   # READ-ONLY reference.
RUN35_DIR = os.path.join(ROOT, "results", "run35_checkpoints")   # READ-ONLY reference.
STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")   # parallel-session-
                                                                          # owned -- READ-ONLY.
os.makedirs(CKPT_DIR, exist_ok=True)

WAY = run25.WAY                                        # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET    # 20
R_TARGET = run25.R_TARGET                              # 2 -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS              # 10
POWER_SEED = run25.POWER_SEED                          # gate.SEED + 1500, byte-identical to
                                                        # RUN 15/16/17/25/26/36/37A/37C's own
                                                        # eval seed.
SHORTLIST_K = run26.SHORTLIST_K                        # 10 (of 20)
DK = gate.DK                                           # segments=8, max_knots=16 -- the SAME
                                                        # grain run35's own edges were fit on.
K_ADD = cs.K_ADD_DEFAULT                               # 5 -- pre-registered committed-shape cap.
MAX_UNION_WIDTH_CAP = SHORTLIST_K + K_ADD              # 15 -- pre-registered explosion guard.
PER_CALL_BUDGET_SECONDS = 480.0                        # leaves >100s headroom under the 600s
                                                        # foreground cap; eval checkpoints per
                                                        # block.

# Cited VERBATIM from results/run26_checkpoints/eval_baseline.json's own `coverage`/
# `shortlist_acc` blocks -- the BASELINE arm's own reproduction target.
BASELINE_COVERAGE10 = dict(cov=0.715, ci=(0.6688804833361408, 0.7570292301001117), n=400, k=286)
BASELINE_SHORTLIST_ACC = dict(acc=0.62, ci=(0.5715045437377642, 0.6662125056220046), n=400, k=248)


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


def _wilson(k: int, n: int) -> tuple:
    return gate.wilson_ci(k, n)


# =============================================================================================
# ONE EPISODE's worth of both arms -- shortlist staged once, committed-shape proposed from the
# SAME query/exemplar raw strokes (filtered under DropDegenerateFilter -- see stage_eval's own
# `with` block), union verdict computed ONLY when the union differs from the shortlist (the
# additive-invariant optimization named in the module docstring).
# =============================================================================================
def _run_block(s, native, cache, edges, alph: str, r: int, spec: dict) -> list:
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, DK)
                 for ci in range(WAY)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]

    # Committed-shape identity for every exemplar in this block (denoise+tokenize once each;
    # `ow.load_strokes` resolves through DropDegenerateFilter's patch for the life of the call).
    exemplar_commits = [
        cs.commit_shape(ow.load_strokes(drawer_files[ci][ex_drawer]),
                         segments=DK["segments"], max_knots=DK["max_knots"], **edges)
        for ci in range(WAY)
    ]

    records = []
    for qi, q_drawer in spec["queries"]:
        path = drawer_files[qi][q_drawer]
        rec = {"true": qi, "alph": alph, "r": r}

        qd = gate.decode_char_signature(s, path, cache, DK)
        shortlist = ar.propose_top_k(native, qd["composed_sig"], exemplar_composed,
                                      k=SHORTLIST_K)
        rec["in_shortlist"] = bool(qi in shortlist)

        query_commit = cs.commit_shape(ow.load_strokes(path), segments=DK["segments"],
                                        max_knots=DK["max_knots"], **edges)
        committed = cs.propose_by_committed_shape(query_commit, exemplar_commits, k=K_ADD)
        union = cs.union_candidates(shortlist, committed)
        rec["query_commit"] = query_commit
        rec["match_kind"] = cs.match_kind(query_commit, exemplar_commits)
        rec["n_committed_candidates"] = len(committed)
        rec["committed_added"] = len(union) - len(shortlist)
        rec["union_width"] = len(union)
        rec["in_union"] = bool(qi in union)

        # BASELINE verdict -- shortlist members only (byte-identical to run26/37c's own
        # shortlist-arm staging).
        scratch_s = srs.Substrate()
        cand_s = {}
        for ci in shortlist:
            node = ar.stage_parse_char(scratch_s, drawer_files[ci][ex_drawer],
                                        is_query=False, name=str(ci))
            cand_s[node] = ci
        qn_s = ar.stage_parse_char(scratch_s, path, is_query=True)
        w_s = ar.parse_marginal_verdict(scratch_s, qn_s)
        rec["pred_shortlist"] = cand_s.get(w_s, -1) if w_s is not None else -1

        # UNION verdict -- only re-staged when the union genuinely differs from the shortlist
        # (additive-invariant optimization; see module docstring).
        if set(union) == set(shortlist):
            rec["pred_union"] = rec["pred_shortlist"]
        else:
            scratch_u = srs.Substrate()
            cand_u = {}
            for ci in union:
                node = ar.stage_parse_char(scratch_u, drawer_files[ci][ex_drawer],
                                            is_query=False, name=str(ci))
                cand_u[node] = ci
            qn_u = ar.stage_parse_char(scratch_u, path, is_query=True)
            w_u = ar.parse_marginal_verdict(scratch_u, qn_u)
            rec["pred_union"] = cand_u.get(w_u, -1) if w_u is not None else -1
        records.append(rec)
    return records


# =============================================================================================
# STAGE: guard -- protocol reproduction (block 0 vs eval_baseline.json) + a cheap engagement
# spot-check (mirrors run37a/run37c's own stage_guard/stage_verify precedent).
# =============================================================================================
def stage_guard() -> int:
    print(f"\n{SEP}\n  STAGE: guard -- protocol reproduction + committed-shape engagement spot-check\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_PATH)
    print(f"  seeds/stroke_shapes.json md5 (parallel-session-owned, this run never writes "
          f"there): {md5_now}")

    edges = cs.load_cited_program_edges(os.path.join(RUN35_DIR, "programs.json"))
    print(f"  CITED committed-shape edges (results/run35_checkpoints/programs.json, RUN 35's "
          f"own already-fit LEARN population, never refit here):")
    print(f"    tol_deg={edges['tol_deg']:.4f}  level_edges({len(edges['level_edges'])-1} "
          f"bins)={[round(v, 2) for v in edges['level_edges']]}")
    print(f"    delta_edges({len(edges['delta_edges'])-1} bins)="
          f"{[round(v, 2) for v in edges['delta_edges']]}")

    baseline_records = _load_json(os.path.join(RUN26_DIR, "eval_baseline.json"))["records"][:WAY]
    test_alphabets = _test_alphabets()
    rng = np.random.default_rng(POWER_SEED)
    spec = run25._block_spec(test_alphabets[0], rng, WAY, EPISODES_PER_ALPHABET)
    src = os.path.join(RUN26_DIR, "learn.json")
    t0 = time.time()
    s = run26._load_graph(src)
    native = s._inner
    print(f"  learn.json loaded ({time.time()-t0:.1f}s).")

    cache: dict = {}
    t0 = time.time()
    with DropDegenerateFilter():
        got = _run_block(s, native, cache, edges, test_alphabets[0], 0, spec)
    print(f"  block 0 ({test_alphabets[0]!r}) computed in {time.time()-t0:.1f}s.")

    mismatches = []
    for i, (g, b) in enumerate(zip(got, baseline_records)):
        for key in ("in_shortlist", "pred_shortlist"):
            if g[key] != b[key]:
                mismatches.append((i, key, g[key], b[key]))
    ok = not mismatches
    print(f"  BASELINE arm vs eval_baseline.json, block 0 ({len(got)} episodes): "
          f"{'EXACT MATCH' if ok else f'{len(mismatches)} MISMATCHES'}")
    for i, key, gv, bv in mismatches[:10]:
        print(f"    MISMATCH episode {i} {key}: got={gv} baseline={bv}")

    # Additive-invariant spot-check: union_width can never be SMALLER than the shortlist it
    # was built from (the real membership-superset check is `union_candidates`'s own unit
    # gate, `tests/test_committed_shape_migrated.py`; this is the cheap per-episode structural
    # signature available from the recorded fields alone).
    width_ok = all(g["union_width"] >= min(SHORTLIST_K, WAY) for g in got)
    print(f"  additive-width sanity (union_width always >= shortlist size): "
          f"{'OK' if width_ok else 'VIOLATION -- investigate union_candidates'}")

    match_kinds = {}
    for g in got:
        match_kinds[g["match_kind"]] = match_kinds.get(g["match_kind"], 0) + 1
    print(f"  committed-shape match_kind on block 0: {match_kinds}")
    n_added = sum(1 for g in got if g["committed_added"] > 0)
    print(f"  episodes where the union genuinely added candidates: {n_added}/{len(got)}")

    guard_ok = ok and width_ok
    out = dict(guard_ok=guard_ok, spot_check_mismatches=len(mismatches),
               stroke_shapes_md5=md5_now, edges=edges, match_kinds_block0=match_kinds,
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
        print("  WALL: --stage guard did not PASS -- fix the protocol mismatch before --stage eval.")
        sys.exit(1)
    return g


# =============================================================================================
# STAGE: eval -- full n=400, filter ON for every stroke load (exemplar + query).
# =============================================================================================
def stage_eval() -> int:
    print(f"\n{SEP}\n  STAGE: eval -- n=400, BASELINE + UNION, filter ON\n{SEP}")
    guard = _require_guard()
    edges = guard["edges"]
    out_path = _ckpt("eval_run37b.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval already COMPLETE (n={len(state['records'])}).")
        return 0

    src = os.path.join(RUN26_DIR, "learn.json")
    t0 = time.time()
    s = run26._load_graph(src)
    native = s._inner
    print(f"  learn.json loaded ({time.time()-t0:.1f}s) -- READ-ONLY reference, re-LEARN out "
          f"of scope for this run.")

    test_alphabets = _test_alphabets()
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  test_alphabets={test_alphabets}")
    print(f"  blocks={len(blocks)} (target n={len(blocks)*WAY})  SHORTLIST_K={SHORTLIST_K}  "
          f"K_ADD={K_ADD}  resuming at block {state['block_idx']}")

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        alph, r = blocks[i]
        run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)

    cache: dict = {}
    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t_loop0 = time.time()
    with DropDegenerateFilter():
        while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
            alph, r = blocks[state["block_idx"]]
            spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
            recs = _run_block(s, native, cache, edges, alph, r, spec)
            state["records"].extend(recs)
            state["block_idx"] += 1
            _save_json(state, out_path)
            print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
                  f"{len(state['records'])} episodes so far, {time.time()-t_loop0:.1f}s this call")

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
# STAGE: report -- coverage McNemar FIRST, then shortlist-acc McNemar + CIs, union width,
# engagement stats, per-stroke-bucket concentration, honest anomalies.
# =============================================================================================
def _class_stroke_buckets(records: list, test_alphabets: list) -> dict:
    """`{record_index: bucket_str}` via RUN 36's OWN `_bucket` (median stroke count of the
    TRUE class over its 20 drawer files), reused verbatim -- not reimplemented."""
    chars_by_alph = {a: sorted(ow.characters(a, "evaluation"))[:WAY] for a in test_alphabets}
    stroke_count: dict = {}
    out = {}
    for i, r in enumerate(records):
        cd = chars_by_alph[r["alph"]][r["true"]]
        if cd not in stroke_count:
            counts = [len(ow.load_strokes(f)) for f in ow.drawings(cd)]
            stroke_count[cd] = float(np.median(counts))
        out[i] = run36._bucket(stroke_count[cd])
    return out


def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 37B -- COMMITTED SHAPE -- FINAL REPORT\n{SEP}")
    ev_path = _ckpt("eval_run37b.json")
    if not os.path.exists(ev_path) or not _load_json(ev_path).get("done"):
        print("  eval not yet COMPLETE -- run --stage eval to completion first.")
        return 1
    records = _load_json(ev_path)["records"]
    n = len(records)
    print(f"  n={n}")

    # ---- PROTOCOL STOP: BASELINE must reproduce cited coverage/shortlist-acc EXACTLY. --------
    k_cov = sum(1 for r in records if r["in_shortlist"])
    k_sl = sum(1 for r in records if r["pred_shortlist"] == r["true"])
    cov_ok = (k_cov == BASELINE_COVERAGE10["k"])
    sl_ok = (k_sl == BASELINE_SHORTLIST_ACC["k"])
    print(f"\n  BASELINE (protocol guard): coverage k={k_cov}/{n} (cited "
          f"k={BASELINE_COVERAGE10['k']}) -- {'MATCH' if cov_ok else 'MISMATCH'}; "
          f"shortlist-acc k={k_sl}/{n} (cited k={BASELINE_SHORTLIST_ACC['k']}) -- "
          f"{'MATCH' if sl_ok else 'MISMATCH'}")
    if not (cov_ok and sl_ok):
        print("  STOP: protocol bug -- BASELINE does not reproduce the cited numbers, "
              "do not trust the UNION arm below.")
        return 1

    ci_cov_base = _wilson(k_cov, n)
    ci_sl_base = _wilson(k_sl, n)

    k_cov_u = sum(1 for r in records if r["in_union"])
    k_sl_u = sum(1 for r in records if r["pred_union"] == r["true"])
    ci_cov_u = _wilson(k_cov_u, n)
    ci_sl_u = _wilson(k_sl_u, n)

    # ---- PRIMARY: paired McNemar on COVERAGE flips. -------------------------------------------
    cov_fixed = [r for r in records if not r["in_shortlist"] and r["in_union"]]
    cov_broken = [r for r in records if r["in_shortlist"] and not r["in_union"]]
    n_cov_fixed, n_cov_broken = len(cov_fixed), len(cov_broken)
    print(f"\n  {'='*80}\n  McNEMAR #1 (PRIMARY) -- COVERAGE flips (true class enters/leaves "
          f"the candidate set):\n  {'='*80}")
    print(f"    fixed  (baseline NOT covered -> union covered): {n_cov_fixed}")
    print(f"    broken (baseline covered -> union NOT covered): {n_cov_broken}")
    if n_cov_broken > 0:
        print(f"    STOP: broken coverage > 0 is IMPOSSIBLE under a pure-additive union "
              f"(union_candidates only ever adds indices) -- this is a PROTOCOL BUG in the "
              f"union wiring, not a research finding. Investigate before trusting anything "
              f"below.")
        return 1
    print(f"    broken == 0 -- CONFIRMED structurally additive (as designed).")
    n_cov_discordant = n_cov_fixed + n_cov_broken
    cov_p = float(binomtest(n_cov_fixed, n_cov_discordant, 0.5, alternative="two-sided").pvalue) \
        if n_cov_discordant else 1.0
    print(f"    discordant total: {n_cov_discordant}   p-value (informational -- one-sided by "
          f"construction since broken=0): {cov_p:.4g}")

    # Per-stroke-bucket concentration of the gained-coverage episodes.
    test_alphabets = _test_alphabets()
    buckets_by_idx = _class_stroke_buckets(records, test_alphabets)
    fixed_idx = {i for i, r in enumerate(records) if not r["in_shortlist"] and r["in_union"]}
    bucket_order = ["1", "2", "3", "4", "5+"]
    bucket_totals = {b: 0 for b in bucket_order}
    bucket_fixed = {b: 0 for b in bucket_order}
    for i in range(n):
        b = buckets_by_idx[i]
        bucket_totals[b] += 1
        if i in fixed_idx:
            bucket_fixed[b] += 1
    print(f"\n  PER-STROKE-BUCKET concentration of gained-coverage episodes (RUN 36's own "
          f"median-stroke-count bucket on the TRUE class; prediction: concentrates in 1-2):")
    for b in bucket_order:
        tot = bucket_totals[b]
        fx = bucket_fixed[b]
        rate = f"{100*fx/tot:.1f}%" if tot else "n/a"
        print(f"    strokes={b:<3}  gained={fx:>3}/{tot:<3}  share-of-episodes-in-bucket={rate}")
    low_stroke_fixed = bucket_fixed["1"] + bucket_fixed["2"]
    print(f"    1-2-stroke share of ALL gained-coverage episodes: "
          f"{low_stroke_fixed}/{n_cov_fixed} = "
          f"{100*low_stroke_fixed/n_cov_fixed:.1f}%" if n_cov_fixed else
          f"    1-2-stroke share of ALL gained-coverage episodes: n/a (0 gained)")

    # ---- SECONDARY: paired McNemar on SHORTLIST-ACCURACY flips. -------------------------------
    sl_fixed = [r for r in records
                if r["pred_shortlist"] != r["true"] and r["pred_union"] == r["true"]]
    sl_broken = [r for r in records
                 if r["pred_shortlist"] == r["true"] and r["pred_union"] != r["true"]]
    n_sl_fixed, n_sl_broken = len(sl_fixed), len(sl_broken)
    n_sl_discordant = n_sl_fixed + n_sl_broken
    sl_p = float(binomtest(n_sl_fixed, n_sl_discordant, 0.5, alternative="two-sided").pvalue) \
        if n_sl_discordant else 1.0
    print(f"\n  {'='*80}\n  McNEMAR #2 (SECONDARY) -- SHORTLIST-ACCURACY flips:\n  {'='*80}")
    print(f"    fixed  (baseline WRONG -> union RIGHT): {n_sl_fixed}")
    print(f"    broken (baseline RIGHT -> union WRONG): {n_sl_broken}")
    print(f"    discordant total: {n_sl_discordant}   p-value: {sl_p:.4f}")
    if n_sl_discordant == 0:
        print(f"    (no discordant pairs -- the two arms never disagree on accuracy)")
    elif n_sl_broken >= n_sl_fixed:
        print(f"    NOTE: broken >= fixed on accuracy -- widening the candidate pool let the "
              f"verdict pick a WRONG member as often as (or more than) it picked a newly-"
              f"available RIGHT one (the run-11 dilution risk this design measures for, not "
              f"assumes away).")
    else:
        print(f"    fixed > broken: coverage gains are converting to accuracy gains "
              f"({'significant at p<0.05' if sl_p < 0.05 else 'not significant at p<0.05'}).")
    conversion_rate = (n_sl_fixed / n_cov_fixed) if n_cov_fixed else float("nan")
    print(f"    CONVERSION: {n_sl_fixed}/{n_cov_fixed} = {100*conversion_rate:.1f}% of "
          f"gained-coverage episodes converted to a correct verdict (RUN 16's own cited "
          f"historical rate: ~70%)." if n_cov_fixed else
          f"    CONVERSION: n/a (0 gained-coverage episodes).")

    # ---- Accuracies with Wilson CIs, both arms. -----------------------------------------------
    print(f"\n  COVERAGE@{SHORTLIST_K}+committed (Wilson 95% CI):")
    print(f"    BASELINE: cov={100*k_cov/n:.1f}%  [{100*ci_cov_base[0]:.1f}%, "
          f"{100*ci_cov_base[1]:.1f}%]  k={k_cov}/{n}")
    print(f"    UNION:    cov={100*k_cov_u/n:.1f}%  [{100*ci_cov_u[0]:.1f}%, "
          f"{100*ci_cov_u[1]:.1f}%]  k={k_cov_u}/{n}")
    print(f"    CI-separated: {gate._ci_separated(tuple(ci_cov_u), tuple(ci_cov_base))}  "
          f"(McNemar #1 above is the POWERED test for the paired effect)")

    print(f"\n  SHORTLIST ACCURACY (Wilson 95% CI):")
    print(f"    BASELINE: acc={100*k_sl/n:.1f}%  [{100*ci_sl_base[0]:.1f}%, "
          f"{100*ci_sl_base[1]:.1f}%]  k={k_sl}/{n}")
    print(f"    UNION:    acc={100*k_sl_u/n:.1f}%  [{100*ci_sl_u[0]:.1f}%, "
          f"{100*ci_sl_u[1]:.1f}%]  k={k_sl_u}/{n}")
    ci_sep_sl = gate._ci_separated(tuple(ci_sl_u), tuple(ci_sl_base))
    print(f"    CI-separated: {ci_sep_sl}  (McNemar #2 above is the POWERED test for the "
          f"paired effect)")

    # ---- Union width distribution. -------------------------------------------------------------
    widths = [r["union_width"] for r in records]
    added = [r["committed_added"] for r in records]
    max_width = max(widths)
    width_hist: dict = {}
    for w in widths:
        width_hist[str(w)] = width_hist.get(str(w), 0) + 1
    print(f"\n  UNION WIDTH distribution (cap={MAX_UNION_WIDTH_CAP}, SHORTLIST_K={SHORTLIST_K} "
          f"+ K_ADD={K_ADD}):")
    print(f"    mean={np.mean(widths):.2f}  median={np.median(widths):.1f}  max={max_width}  "
          f"histogram={dict(sorted(width_hist.items(), key=lambda kv: int(kv[0])))}")
    print(f"    committed_added: mean={np.mean(added):.2f}  "
          f"episodes_with_addition={sum(1 for a in added if a > 0)}/{n} "
          f"({100*sum(1 for a in added if a > 0)/n:.1f}%)")
    width_exploded = max_width > MAX_UNION_WIDTH_CAP

    # ---- Engagement stats -- match_kind breakdown + commit-type vacuity check (run-28 lesson). -
    match_kinds: dict = {}
    for r in records:
        match_kinds[r["match_kind"]] = match_kinds.get(r["match_kind"], 0) + 1
    print(f"\n  ENGAGEMENT -- match_kind breakdown (all {n} episodes):")
    for k in sorted(match_kinds):
        print(f"    {k:<8} {match_kinds[k]:>4}  ({100*match_kinds[k]/n:.1f}%)")

    all_commits = [r["query_commit"] for r in records]
    commit_hist: dict = {}
    for c in all_commits:
        commit_hist[c] = commit_hist.get(c, 0) + 1
    n_distinct = len(commit_hist)
    top = sorted(commit_hist.items(), key=lambda kv: -kv[1])[:10]
    top3_share = sum(c for _, c in top[:3]) / len(all_commits) if all_commits else 0.0
    print(f"\n  COMMIT-TYPE ENGAGEMENT (query commits, n={len(all_commits)}): "
          f"{n_distinct} distinct committed shapes.")
    print(f"    top 10 by frequency: {top}")
    print(f"    top-3 share of all queries: {100*top3_share:.1f}%  "
          f"{'(VACUOUS -- most glyphs collapse onto a handful of types, per the run-28 lesson)' if top3_share > 0.5 else '(engaged -- meaningfully spread across types)'}")

    # ---- Honest anomalies / dilution finding. ---------------------------------------------------
    print(f"\n  {'='*80}\n  HONEST ANOMALIES\n  {'='*80}")
    anomalies = []
    if width_exploded:
        anomalies.append(f"union width exceeded the pre-registered cap ({max_width} > "
                          f"{MAX_UNION_WIDTH_CAP})")
    if width_exploded and ci_sep_sl and k_sl_u < k_sl:
        anomalies.append("width explosion PAIRED WITH a CI-separated shortlist-accuracy "
                          "REGRESSION -- the RUN-11 'widening hurts' dilution family; "
                          "recommend NOT adopting this modality as configured.")
    if n_cov_fixed == 0:
        anomalies.append("zero gained-coverage episodes -- the committed-shape modality "
                          "never engaged where the shortlist was already blind (check "
                          "match_kind engagement above).")
    if not anomalies:
        print("  none -- the modality behaved as designed (pure-additive coverage gain, "
              "no width explosion).")
    else:
        for a in anomalies:
            print(f"  - {a}")

    out = dict(
        n=n, baseline_coverage=dict(k=k_cov, ci=list(ci_cov_base)),
        union_coverage=dict(k=k_cov_u, ci=list(ci_cov_u)),
        baseline_shortlist_acc=dict(k=k_sl, ci=list(ci_sl_base)),
        union_shortlist_acc=dict(k=k_sl_u, ci=list(ci_sl_u)),
        mcnemar_coverage=dict(fixed=n_cov_fixed, broken=n_cov_broken, p=cov_p),
        mcnemar_shortlist_acc=dict(fixed=n_sl_fixed, broken=n_sl_broken, p=sl_p),
        conversion_rate=conversion_rate,
        bucket_totals=bucket_totals, bucket_fixed=bucket_fixed,
        union_width=dict(mean=float(np.mean(widths)), median=float(np.median(widths)),
                         max=max_width, histogram=width_hist),
        match_kinds=match_kinds, n_distinct_commits=n_distinct, top_commits=top,
        top3_share=top3_share, anomalies=anomalies,
    )
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
