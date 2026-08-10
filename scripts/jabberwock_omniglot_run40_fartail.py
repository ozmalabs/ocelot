"""OMNIGLOT RUN 40 -- WHAT ARE THE FAR-TAIL ERRORS MADE OF? PURE ANALYSIS, phase 0 of the
gap-closure plan. No training, no new mechanism, no mint, no teach(). donkey=0.

Run 36 (`scripts/jabberwock_omniglot_run36_failures.py`, `results/run36_checkpoints/`,
READ-ONLY reference here) found, at run-26's own baseline (n=400, full-dwell 80.5%
[76.3,84.1]): 78 full-dwell errors, impostor-rank of the predicted class among the true
class's 19 impostors distributed as rank<=2: 25/78 (32.1%, "near-duplicate arbitration"),
rank 3-10: 34/78 ("mid"), rank 11-19: 19/78 ("far-tail" -- the true class scored TERRIBLY,
UNDIAGNOSED). This run diagnoses the far tail (with the near/mid bands as contrast) against a
matched control sample of passed episodes.

REUSE DISCIPLINE (binding, per the launch brief): the episode-replay / block reconstruction /
rank computation is REUSED VERBATIM from run36 via IMPORT of its pure helper functions
(`_run25_deps`, `_test_alphabets`, `_reconstruct_run26_blocks`, the cited-table constants) --
never by re-invoking run36's own `stage_*` functions (those WRITE to
`results/run36_checkpoints/`, a READ-ONLY dir for this run). `results/run36_checkpoints/
confusion_analysis.json`'s own `ranks` list (order-aligned with `guard.json`'s `full_err_idx`,
verified below) is read directly rather than recomputed -- it is already the exact machinery
this run's band split needs.

FALSY-ZERO BUG (found in run36's own `_greedy_stroke_match`/`stage_confusion`, fixed HERE, in
this run's own local copy, per the launch brief): both used
`float(native.evaluate(term, {}) or float("nan"))` -- when a genuine distance is exactly 0.0
(two identical point sets, or Python numeric artifacts), `0.0 or float("nan")` evaluates to
`nan` because `0.0` is FALSY in Python. Fixed here via `_eval_dist` (explicit `is None` check,
never a truthiness check on the numeric result). This run's OWN pairwise distance computations
(within-class matrices, true-pair distances, per-theta greedy matches) all route through
`_eval_dist`.

LEGAL USE OF OTHER DRAWERS (stated once, per the launch brief -- "using other drawers is legal
here; say so in the header"): items 2/3 below (exemplar/query representativeness) measure
distance from a class's block-assigned exemplar/query FILE to the class's OTHER 19 drawer
files. This is DIAGNOSIS, not classification -- no eval decision anywhere in this script reads
another drawer; the 400-episode verdict this run diagnoses was already scored (run26,
CITED not re-grown) using only the block's own single shared exemplar per candidate.

LEGAL USE OF `mark_characters` ON EVAL FILES (stated once): item 1(b) (round-trip fidelity)
calls `domains.homework_loop.mark_characters` directly on eval query/exemplar files WITHOUT
`eval_class_ids` (which would raise `EvalLeakageError` by design -- that guard exists to stop
the homework loop from TRAINING on held-out answers before a live eval). Here there is no
training: the agent graph is loaded FRESH from `results/run26_checkpoints/learn.json` (read-
only), `mark_characters` is called once for measurement, and the resulting (possibly OOV-
minted) graph is discarded -- never saved, never fed back into any live eval pipeline. This is
the same "diagnosis, not classification" contract as items 2/3, stated once here for the
round-trip-fidelity measurement specifically.

PRE-REGISTERED THRESHOLDS AND CLASSIFICATION (stated BEFORE any downstream number is computed;
see `stage classify`): outlier/unstable thresholds are the CONTROL sample's own p90 (p10 for
fidelity, where LOWER is worse) -- never a hand-picked constant. Classification priority order
(an error can trigger more than one flag; the FIRST match wins, decided here, before results
are seen):
  1. COUNT-MISMATCH   -- query and exemplar have different stroke counts (deterministic fact,
                          not a threshold).
  2. PARSE-UNSTABLE   -- the query's per-theta greedy-match distance to the exemplar has a
                          coefficient of variation across `DEFAULT_PARSE_THETAS_FINE` beyond
                          the control's own p90 CV, OR the query's `mark_characters` round-trip
                          `overall` score is below the control's own p10.
  3. BOTH-OUTLIER     -- both exemplar and query typicality (mean SC+TPS distance to their
                          class's other 19 drawers) exceed the control's own p90.
  4. EXEMPLAR-OUTLIER -- exemplar typicality only exceeds the control's own p90.
  5. QUERY-OUTLIER    -- query typicality only exceeds the control's own p90.
  6. GENUINE-DIVERGENCE -- none of the above triggers, but the query-exemplar SC+TPS distance
                          itself still exceeds the control's own p90 (both files individually
                          "fine", still far apart -- the mystery class).
  (else)              -- UNFLAGGED (passed every check; should be rare among the 78 errors,
                          common among controls -- a sanity check on the thresholds themselves).

PRE-REGISTERED DIRECTIONAL PREDICTIONS (stated before the numbers, per the launch brief):
  D1. The far-tail band (rank 11-19) is disproportionately EXEMPLAR-OUTLIER and/or
      QUERY-OUTLIER and/or PARSE-UNSTABLE relative to the near band (rank<=2), which should be
      dominated by GENUINE-DIVERGENCE-adjacent near-duplicate geometry (both files fine, the
      comparator just can't tell two genuinely close classes apart) or BOTH files fine with a
      close impostor (not this run's own outlier axes at all).
  D2. EXEMPLAR-OUTLIER is more fixable in principle (a variation/nuisance model around a known-
      outlier exemplar could still cover the query) than QUERY-OUTLIER (no prior can know THIS
      query itself is an odd token) -- reasoned through in the final report, not assumed a free
      win for either.
  D3. COUNT-MISMATCH and PARSE-UNSTABLE are the parse-robustness-fixable bucket; the fraction
      of the far tail landing there gates how much of the 5pp phase-3/parse-robustness work can
      actually recover.

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run40.log`, checkpoints under `results/run40_checkpoints/` (every other
`run*_checkpoints/` dir READ-ONLY reference, in particular `run36`). `.venv` python (needs
`substrate_rs`). `seeds/stroke_shapes.json` is untouched by this script (md5-checked in the
launch brief, not by this file -- this script never calls `teach()`/never writes seeds).

Stages (run in order, each checkpointed):
  --stage guard      Re-verify run36's cited per-alphabet table (import, no write to run36's
                     own dir); read `run36_checkpoints/confusion_analysis.json`'s ranks,
                     zip with `full_err_idx`, split into near(<=2)/mid(3-10)/far(11-19) bands;
                     draw the ~80-episode matched control (stratified by alphabet, seeded).
  --stage files      Resolve exemplar_path/query_path per sampled episode (full block replay,
                     RETAINING `queries` this time -- run36's own reconstruction drops it).
  --stage class_matrices  Within-class 20x20 SC+TPS distance matrix for every class dir touched
                     by the sample; typicality (mean dist to other 19) + rank per drawer.
  --stage true_pair  Query-exemplar SC+TPS distance (normalized, the standard convention) +
                     a RAW (un-normalized) twin + stroke counts, per sampled episode.
  --stage parse      Per-episode theta-grid (DEFAULT_PARSE_THETAS_FINE) greedy-match distance
                     variance (query vs exemplar) + `mark_characters` round-trip fidelity.
  --stage classify   Apply the pre-registered thresholds; band x diagnosis table.
  --stage report     Print the final consolidated deliverable.
  --stage all        Run every stage in sequence.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run40_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")   # READ-ONLY reference.
RUN36_DIR = os.path.join(ROOT, "results", "run36_checkpoints")   # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

CONTROL_N = 80
CONTROL_SEED = 20260705140  # this run's own seed.


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _load_eval_baseline() -> list:
    return _load_json(os.path.join(RUN26_DIR, "eval_baseline.json"))["records"]


def _eval_dist(native, term: dict) -> float:
    """THE falsy-zero fix: `native.evaluate(term, {})` can legitimately return `0.0`; the
    run36 idiom `float(x or float('nan'))` silently corrupts every genuine-zero distance into
    NaN. Explicit `is None` check instead."""
    v = native.evaluate(term, {})
    return float(v) if v is not None else float("nan")


# ===============================================================================================
# REUSE (import, not copy) -- run36's pure block-reconstruction / RNG-replay machinery.
# ===============================================================================================
def _run36():
    import scripts.jabberwock_omniglot_run36_failures as run36
    return run36


def _run25_deps():
    run36 = _run36()
    return run36._run25_deps()


def _reconstruct_run26_blocks_with_queries(run25, ow) -> tuple:
    """SAME as run36's `_reconstruct_run26_blocks` (byte-identical RNG replay: `POWER_SEED`,
    one `_block_spec` draw per block, alph OUTER / r INNER) but RETAINS `spec["queries"]`
    (run36 drops it -- it never needed the per-query drawer, only `ex_drawer`). This is the
    ONE addition to run36's reconstruction this run needs; everything else is verbatim."""
    run36 = _run36()
    test_alphabets = run36._test_alphabets(run25, ow)
    rng = np.random.default_rng(run25.POWER_SEED)
    blocks = []
    for alph in test_alphabets:
        for r in range(run25.R_TARGET):
            spec = run25._block_spec(alph, rng, run25.WAY, run25.EPISODES_PER_ALPHABET)
            chars = sorted(ow.characters(alph, "evaluation"))[:run25.WAY]
            blocks.append(dict(alph=alph, r=r, chars=chars, ex_drawer=spec["ex_drawer"],
                                drawer_files=spec["drawer_files"], queries=spec["queries"]))
    return blocks, test_alphabets


# ===============================================================================================
# STAGE: guard -- re-verify run36's cited table; band split; matched control sample.
# ===============================================================================================
def stage_guard() -> int:
    print(f"\n{SEP}\n  STAGE: guard -- protocol guard + band split + control sample\n{SEP}")
    run36 = _run36()
    run25, ow = _run25_deps()
    records = _load_eval_baseline()

    blocks26, test_alphabets = run36._reconstruct_run26_blocks(run25, ow)
    assert len(blocks26) == 20 and len(records) == 400

    per_alph_err = defaultdict(int)
    per_alph_tot = defaultdict(int)
    full_err_idx, sl_err_idx, blind_idx = [], [], []
    for i, r in enumerate(records):
        per_alph_tot[r["alph"]] += 1
        if r["pred_full"] != r["true"]:
            per_alph_err[r["alph"]] += 1
            full_err_idx.append(i)
        if not r["in_shortlist"]:
            blind_idx.append(i)
        if r["pred_shortlist"] != r["true"]:
            sl_err_idx.append(i)

    all_match = True
    print("  per-alphabet full-dwell errors (measured vs run36-cited):")
    for alph in test_alphabets:
        got = per_alph_err[alph]
        want = run36.CITED_PER_ALPH_FULL_DWELL_ERRORS.get(alph, got if alph not in
                                                            run36.CITED_PER_ALPH_FULL_DWELL_ERRORS
                                                            else None)
        ok = (alph not in run36.CITED_PER_ALPH_FULL_DWELL_ERRORS) or (got == want)
        all_match = all_match and ok
        tag = "OK" if ok else "MISMATCH -- STOP"
        cited_s = f"(cited {run36.CITED_PER_ALPH_FULL_DWELL_ERRORS.get(alph, '?')})"
        print(f"    {alph:<22} {got:>3}/{per_alph_tot[alph]:<3} {cited_s}  {tag}")

    guard_ok = (all_match and len(full_err_idx) == run36.CITED_TOTAL_FULL_DWELL_ERRORS
                and len(blind_idx) == run36.CITED_TOTAL_PROPOSAL_BLIND
                and len(sl_err_idx) == run36.CITED_TOTAL_SHORTLIST_ERRORS)
    print(f"\n  totals: full_dwell_errors={len(full_err_idx)} (cited "
          f"{run36.CITED_TOTAL_FULL_DWELL_ERRORS})  proposal_blind={len(blind_idx)} (cited "
          f"{run36.CITED_TOTAL_PROPOSAL_BLIND})  shortlist_errors={len(sl_err_idx)} (cited "
          f"{run36.CITED_TOTAL_SHORTLIST_ERRORS})")
    print(f"\n  PROTOCOL GUARD (own replay): {'PASS' if guard_ok else 'FAIL -- STOP'}")
    if not guard_ok:
        return 1

    # Cross-check against run36's OWN checkpointed guard.json (read-only reference) --
    # independent confirmation the two replays agree exactly.
    run36_guard = _load_json(os.path.join(RUN36_DIR, "guard.json"))
    cross_ok = (run36_guard["full_err_idx"] == full_err_idx
                and run36_guard["blind_idx"] == blind_idx
                and run36_guard["sl_err_idx"] == sl_err_idx)
    print(f"  cross-check vs run36_checkpoints/guard.json: {'MATCH' if cross_ok else 'MISMATCH -- STOP'}")
    if not cross_ok:
        return 1

    # ---- band split: reuse run36's OWN confusion_analysis.json ranks (order-aligned with
    # full_err_idx -- both built by the SAME "enumerate records, append on full-dwell-error"
    # loop, verified by length here). ------------------------------------------------------
    conf = _load_json(os.path.join(RUN36_DIR, "confusion_analysis.json"))
    ranks = conf["ranks"]
    assert len(ranks) == len(full_err_idx) == 78, \
        f"rank/error-index length mismatch: {len(ranks)} vs {len(full_err_idx)}"

    def _band(rank: int) -> str:
        if rank <= 2:
            return "near"
        if rank <= 10:
            return "mid"
        return "far"

    errors = []
    for idx, rank in zip(full_err_idx, ranks):
        r = records[idx]
        errors.append(dict(idx=idx, rank=rank, band=_band(rank), alph=r["alph"], true=r["true"],
                            pred_full=r["pred_full"]))
    band_counts = Counter(e["band"] for e in errors)
    print(f"\n  band split (78 errors): near(<=2)={band_counts['near']}  "
          f"mid(3-10)={band_counts['mid']}  far(11-19)={band_counts['far']}")
    assert band_counts["near"] == 25 and band_counts["far"] == 19, \
        "band split does not match the launch brief's cited 25/34/19 split -- STOP"

    # ---- matched control: stratified-by-alphabet random sample of ~80 PASSED episodes,
    # weights = each alphabet's own share of the 322 passed episodes (so the control mirrors
    # the pool's own alphabet-difficulty mix, not a uniform-over-alphabets draw). ------------
    passed_idx = [i for i in range(400) if i not in set(full_err_idx)]
    assert len(passed_idx) == 322
    by_alph = defaultdict(list)
    for i in passed_idx:
        by_alph[records[i]["alph"]].append(i)
    rng = np.random.default_rng(CONTROL_SEED)
    weights = np.array([len(by_alph[a]) for a in test_alphabets], dtype=float)
    weights /= weights.sum()
    target_per_alph = {a: int(round(w * CONTROL_N)) for a, w in zip(test_alphabets, weights)}
    control_idx = []
    for a in test_alphabets:
        pool = by_alph[a]
        k = min(target_per_alph[a], len(pool))
        chosen = rng.choice(pool, size=k, replace=False)
        control_idx.extend(int(x) for x in chosen)
    control_idx = sorted(control_idx)
    print(f"\n  matched control: n={len(control_idx)} passed episodes, stratified by alphabet "
          f"(seed={CONTROL_SEED})")
    print(f"    per-alphabet: { {a: sum(1 for i in control_idx if records[i]['alph']==a) for a in test_alphabets} }")

    out = dict(guard_ok=True, cross_ok=True, test_alphabets=test_alphabets,
               full_err_idx=full_err_idx, blind_idx=blind_idx, sl_err_idx=sl_err_idx,
               errors=errors, band_counts=dict(band_counts), control_idx=control_idx)
    _save_json(out, _ckpt("guard.json"))
    print(f"\n  guard.json written -- 78 errors banded, {len(control_idx)} control episodes.")
    return 0


def _require(name: str) -> dict:
    p = _ckpt(f"{name}.json")
    if not os.path.exists(p):
        print(f"  WALL: run --stage {name.split('.')[0]} (or its producing stage) first.")
        sys.exit(1)
    return _load_json(p)


# ===============================================================================================
# STAGE: files -- resolve exemplar_path/query_path per sampled episode.
# ===============================================================================================
def stage_files() -> int:
    print(f"\n{SEP}\n  STAGE: files -- resolve exemplar/query paths per sampled episode\n{SEP}")
    guard = _require("guard")
    run25, ow = _run25_deps()
    blocks, test_alphabets = _reconstruct_run26_blocks_with_queries(run25, ow)
    records = _load_eval_baseline()

    all_idx = [(e["idx"], e["band"], e["rank"]) for e in guard["errors"]] + \
              [(i, "control", None) for i in guard["control_idx"]]

    episodes = []
    for idx, band, rank in all_idx:
        bi, qi = idx // 20, idx % 20
        blk = blocks[bi]
        r = records[idx]
        assert r["true"] == qi
        # spec["queries"] is [(qi, q_drawer), ...] in qi order (0..way-1) -- direct index.
        q_qi, q_drawer = blk["queries"][qi]
        assert q_qi == qi
        ex_drawer = blk["ex_drawer"]
        true_ci = qi
        pred_ci = r["pred_full"]
        exemplar_path = blk["drawer_files"][true_ci][ex_drawer]
        query_path = blk["drawer_files"][true_ci][q_drawer]
        pred_exemplar_path = (blk["drawer_files"][pred_ci][ex_drawer]
                               if band != "control" and pred_ci is not None and pred_ci >= 0
                               else None)
        episodes.append(dict(idx=idx, band=band, rank=rank, alph=blk["alph"], r=blk["r"],
                              true_ci=true_ci, pred_ci=pred_ci, true_dir=blk["chars"][true_ci],
                              pred_dir=(blk["chars"][pred_ci] if pred_exemplar_path else None),
                              ex_drawer=ex_drawer, q_drawer=q_drawer,
                              exemplar_path=exemplar_path, query_path=query_path,
                              pred_exemplar_path=pred_exemplar_path))
    n_err = sum(1 for e in episodes if e["band"] != "control")
    print(f"  resolved {len(episodes)} episodes ({n_err} errors + "
          f"{len(episodes) - n_err} control)")
    _save_json(dict(episodes=episodes), _ckpt("files.json"))
    print(f"  files.json written.")
    return 0


# ===============================================================================================
# STAGE: class_matrices -- within-class 20x20 SC+TPS distance matrix + typicality/rank.
# ===============================================================================================
def stage_class_matrices() -> int:
    print(f"\n{SEP}\n  STAGE: class_matrices -- within-class typicality (20 drawers/class)\n{SEP}")
    files = _require("files")
    run25, ow = _run25_deps()
    from domains import abs_read as ar
    import substrate_rs as srs
    native = srs.Substrate()._inner

    needed_classes = sorted({e["true_dir"] for e in files["episodes"]})
    print(f"  {len(needed_classes)} distinct classes touched by the sample")

    out_path = _ckpt("class_matrices.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(matrices={}, drawer_ids={})

    t0 = time.time()
    n_done_this_call = 0
    for ci, cd in enumerate(needed_classes):
        if cd in state["matrices"]:
            continue
        drawer_paths = ow.drawings(cd)   # 20 files, sorted by drawer index == list index.
        ps_list = [ar.whole_figure_point_set(run25._raw_stroke_points(p)) for p in drawer_paths]
        n = len(ps_list)
        M = [[0.0] * n for _ in range(n)]
        for a in range(n):
            for b in range(a + 1, n):
                if ps_list[a] is None or ps_list[b] is None:
                    d = float("nan")
                else:
                    term = ar.sctps_verdict_term(ps_list[a], ps_list[b])
                    d = _eval_dist(native, term)
                M[a][b] = M[b][a] = d
        state["matrices"][cd] = M
        state["drawer_ids"][cd] = [os.path.basename(p) for p in drawer_paths]
        n_done_this_call += 1
        if n_done_this_call % 20 == 0:
            _save_json(state, out_path)
            print(f"    {ci + 1}/{len(needed_classes)} classes done "
                  f"({time.time() - t0:.1f}s elapsed this call)")
        if time.time() - t0 > 480:
            print(f"  time budget guard hit -- checkpointing partial progress "
                  f"({n_done_this_call} classes this call), re-run stage to continue.")
            _save_json(state, out_path)
            return 0

    _save_json(state, out_path)
    print(f"\n  class_matrices.json complete -- {len(state['matrices'])}/{len(needed_classes)} "
          f"classes ({time.time() - t0:.1f}s this call).")

    # ---- typicality: mean distance from each drawer to the other 19; rank (1=most typical). --
    typicality = {}
    for cd, M in state["matrices"].items():
        n = len(M)
        means = []
        for a in range(n):
            others = [M[a][b] for b in range(n) if b != a and not np.isnan(M[a][b])]
            means.append(float(np.mean(others)) if others else float("nan"))
        order = sorted(range(n), key=lambda a: (np.isnan(means[a]), means[a]))
        rank_of = {a: (r + 1) for r, a in enumerate(order)}
        typicality[cd] = dict(mean_dist=means, rank=[rank_of[a] for a in range(n)],
                               drawer_ids=state["drawer_ids"][cd])
    _save_json(typicality, _ckpt("class_typicality.json"))
    print(f"  class_typicality.json written for {len(typicality)} classes.")
    return 0


def _drawer_idx(drawer_ids: list, path: str) -> int:
    base = os.path.basename(path)
    return drawer_ids.index(base)


# ===============================================================================================
# STAGE: true_pair -- query-exemplar SC+TPS distance (normalized + raw), stroke counts.
# ===============================================================================================
def _raw_unnormalized_point_set(stroke_points: list, n_points: int = 80):
    """The un-normalized twin of `abs_read.whole_figure_point_set`: SAME concatenate +
    arc-length resample, but SKIPS the centre+abs-max normalization step -- isolates how much
    of a pair's distance is GLOBAL FRAME (position/scale) vs surviving-after-normalization
    shape divergence when compared against the standard (normalized) distance."""
    pts = []
    for item in stroke_points:
        arr = np.asarray(item[0], dtype=float).reshape(-1, 2)
        pts.extend(arr.tolist())
    a = np.asarray(pts, dtype=float)
    if a.shape[0] < 3:
        return None
    d = np.sqrt((np.diff(a, axis=0) ** 2).sum(1))
    cum = np.concatenate([[0.0], np.cumsum(d)])
    if cum[-1] == 0:
        return None
    u = np.linspace(0.0, cum[-1], n_points)
    return np.stack([np.interp(u, cum, a[:, 0]), np.interp(u, cum, a[:, 1])], 1).tolist()


def stage_true_pair() -> int:
    print(f"\n{SEP}\n  STAGE: true_pair -- query-exemplar distance decomposition\n{SEP}")
    files = _require("files")
    run25, ow = _run25_deps()
    from domains import abs_read as ar
    import substrate_rs as srs
    native = srs.Substrate()._inner

    out = []
    t0 = time.time()
    for e in files["episodes"]:
        q_raw = run25._raw_stroke_points(e["query_path"])
        x_raw = run25._raw_stroke_points(e["exemplar_path"])
        q_ps = ar.whole_figure_point_set(q_raw)
        x_ps = ar.whole_figure_point_set(x_raw)
        q_ps_raw = _raw_unnormalized_point_set(q_raw)
        x_ps_raw = _raw_unnormalized_point_set(x_raw)
        n_q_strokes = len(ow.load_strokes(e["query_path"]))
        n_x_strokes = len(ow.load_strokes(e["exemplar_path"]))
        if q_ps is not None and x_ps is not None:
            dist_norm = _eval_dist(native, ar.sctps_verdict_term(q_ps, x_ps))
        else:
            dist_norm = float("nan")
        if q_ps_raw is not None and x_ps_raw is not None:
            dist_raw = _eval_dist(native, ar.sctps_verdict_term(q_ps_raw, x_ps_raw))
        else:
            dist_raw = float("nan")
        out.append(dict(idx=e["idx"], band=e["band"], alph=e["alph"],
                         dist_normalized=dist_norm, dist_raw=dist_raw,
                         n_query_strokes=n_q_strokes, n_exemplar_strokes=n_x_strokes,
                         count_mismatch=(n_q_strokes != n_x_strokes)))
    elapsed = time.time() - t0
    print(f"  {len(out)} episodes scored in {elapsed:.1f}s")
    n_mismatch = sum(1 for o in out if o["count_mismatch"])
    print(f"  stroke-count mismatch (query vs exemplar): {n_mismatch}/{len(out)} "
          f"({100 * n_mismatch / len(out):.1f}%)")
    for band in ("near", "mid", "far", "control"):
        vals = [o["dist_normalized"] for o in out if o["band"] == band]
        if vals:
            print(f"    {band:<8} n={len(vals):>3}  dist_normalized median={np.median(vals):.3f} "
                  f"mean={np.mean(vals):.3f}")
    _save_json(dict(rows=out), _ckpt("true_pair.json"))
    print(f"\n  true_pair.json written.")
    return 0


# ===============================================================================================
# STAGE: parse -- theta-grid parse-stability variance + mark_characters round-trip fidelity.
# ===============================================================================================
def _normalize_glyph_local(strokes: list) -> tuple:
    """Local copy of run36's `_normalize_glyph`, verbatim (no falsy-zero exposure here --
    this function does no native evaluate)."""
    allpts = np.concatenate([np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes], axis=0)
    center = allpts.mean(0)
    scale = float(np.abs(allpts - center).max()) or 1e-9
    normed = [(np.asarray(s, dtype=float).reshape(-1, 2) - center) / scale for s in strokes]
    return normed


def _greedy_match_dist(native, true_parts: list, pred_parts: list) -> float:
    """Local copy of run36's `_greedy_stroke_match`, WITH THE FALSY-ZERO BUG FIXED (routes
    through `_eval_dist`, never `x or float('nan')`). Returns the MEAN matched-pair cost
    (unmatched parts, on count mismatch, are not folded in here -- this stage measures
    per-theta SHAPE distance under whatever the theta happened to segment, not count
    mismatch, which `true_pair`'s own `count_mismatch` flag already covers at the raw-stroke
    grain)."""
    if not true_parts or not pred_parts:
        return float("nan")
    t_norm = _normalize_glyph_local(true_parts)
    p_norm = _normalize_glyph_local(pred_parts)
    costs = {}
    for i, ts in enumerate(t_norm):
        for j, ps in enumerate(p_norm):
            term = {"type": "PointSetDist",
                    "a": {"type": "Lit", "value": ts.tolist()},
                    "b": {"type": "Lit", "value": ps.tolist()}}
            costs[(i, j)] = _eval_dist(native, term)
    order = sorted(costs.items(), key=lambda kv: (np.isnan(kv[1]), kv[1]))
    used_i, used_j, matched_costs = set(), set(), []
    for (i, j), c in order:
        if i in used_i or j in used_j or np.isnan(c):
            continue
        used_i.add(i)
        used_j.add(j)
        matched_costs.append(c)
    return float(np.mean(matched_costs)) if matched_costs else float("nan")


def stage_parse() -> int:
    print(f"\n{SEP}\n  STAGE: parse -- theta-grid stability + round-trip fidelity\n{SEP}")
    files = _require("files")
    run25, ow = _run25_deps()
    from domains import abs_read as ar
    from domains import canonical_parse as cp
    import substrate_rs as srs
    native = srs.Substrate()._inner

    theta_grid = ar.DEFAULT_PARSE_THETAS_FINE   # reused verbatim -- (40,50,60,70,80,90).
    print(f"  theta grid (reused from abs_read.DEFAULT_PARSE_THETAS_FINE): {theta_grid}")

    out = []
    t0 = time.time()
    for ei, e in enumerate(files["episodes"]):
        q_strokes = ow.load_strokes(e["query_path"])
        x_strokes = ow.load_strokes(e["exemplar_path"])
        per_theta = []
        for th in theta_grid:
            q_parts = cp.canonical_parts(q_strokes, th, per_part=ar.DEFAULT_PARSE_PER_PART)
            x_parts = cp.canonical_parts(x_strokes, th, per_part=ar.DEFAULT_PARSE_PER_PART)
            d = _greedy_match_dist(native, x_parts, q_parts)
            per_theta.append(d)
        arr = np.asarray(per_theta, dtype=float)
        valid = arr[~np.isnan(arr)]
        if len(valid) >= 2 and np.mean(valid) > 1e-9:
            cv = float(np.std(valid) / np.mean(valid))
        else:
            cv = float("nan")
        out.append(dict(idx=e["idx"], band=e["band"], alph=e["alph"],
                         per_theta_dist=per_theta, theta_cv=cv,
                         theta_mean=float(np.mean(valid)) if len(valid) else float("nan"),
                         theta_std=float(np.std(valid)) if len(valid) else float("nan")))
        if (ei + 1) % 40 == 0:
            print(f"    {ei + 1}/{len(files['episodes'])} episodes theta-scored "
                  f"({time.time() - t0:.1f}s elapsed)")
    elapsed_theta = time.time() - t0
    print(f"  theta-grid stability: {len(out)} episodes in {elapsed_theta:.1f}s")
    for band in ("near", "mid", "far", "control"):
        vals = [o["theta_cv"] for o in out if o["band"] == band and not np.isnan(o["theta_cv"])]
        if vals:
            print(f"    {band:<8} n={len(vals):>3}  theta_cv median={np.median(vals):.4f} "
                  f"p90={np.percentile(vals, 90):.4f}")

    # ---- round-trip fidelity (homework_loop.mark_characters, query + exemplar files). --------
    import scripts.jabberwock_omniglot_run26_homework as run26hw
    from domains import homework_loop as hl
    import scripts.jabberwock_omniglot_dynamic_quantization as gate
    t1 = time.time()
    s = run26hw._load_graph(os.path.join(RUN26_DIR, "learn.json"))
    print(f"  learn.json loaded ({time.time() - t1:.1f}s) -- FRESH copy, discarded after this "
          f"stage, never saved/fed back (see header: legal diagnostic use of mark_characters "
          f"on eval files, eval_class_ids intentionally omitted).")

    query_items = [dict(id=e["idx"], class_id=e["true_dir"],
                         strokes=[st.tolist() for st in ow.load_strokes(e["query_path"])])
                   for e in files["episodes"]]
    exemplar_items = [dict(id=e["idx"], class_id=e["true_dir"],
                            strokes=[st.tolist() for st in ow.load_strokes(e["exemplar_path"])])
                       for e in files["episodes"]]
    query_items = [it for it in query_items if it["strokes"]]
    exemplar_items = [it for it in exemplar_items if it["strokes"]]

    t2 = time.time()
    marked_q = hl.mark_characters(s, query_items, dk=gate.DK, eval_class_ids=None)
    print(f"  mark_characters(query, n={len(query_items)}) done in {time.time() - t2:.1f}s")
    t3 = time.time()
    marked_x = hl.mark_characters(s, exemplar_items, dk=gate.DK, eval_class_ids=None)
    print(f"  mark_characters(exemplar, n={len(exemplar_items)}) done in {time.time() - t3:.1f}s")

    fid_by_idx = {}
    for it, m in zip(query_items, marked_q):
        fid_by_idx[it["id"]] = dict(q_overall=m.round_trip_score, q_family=m.family_score,
                                     q_count=m.count_score, q_arrangement=m.arrangement_score)
    for it, m in zip(exemplar_items, marked_x):
        fid_by_idx.setdefault(it["id"], {}).update(
            x_overall=m.round_trip_score, x_family=m.family_score,
            x_count=m.count_score, x_arrangement=m.arrangement_score)

    for row in out:
        row.update(fid_by_idx.get(row["idx"], {}))

    for band in ("near", "mid", "far", "control"):
        vals = [o.get("q_overall") for o in out if o["band"] == band and o.get("q_overall") is not None]
        if vals:
            print(f"    {band:<8} n={len(vals):>3}  q_overall(round-trip) median={np.median(vals):.4f} "
                  f"p10={np.percentile(vals, 10):.4f}")

    _save_json(dict(rows=out), _ckpt("parse.json"))
    print(f"\n  parse.json written ({time.time() - t0:.1f}s total this stage).")
    return 0


# ===============================================================================================
# STAGE: classify -- pre-registered thresholds (from control) + band x diagnosis table.
# ===============================================================================================
def stage_classify() -> int:
    print(f"\n{SEP}\n  STAGE: classify -- pre-registered thresholds + band x diagnosis\n{SEP}")
    files = _require("files")
    typicality = _require("class_typicality")
    true_pair = _require("true_pair")
    parse = _require("parse")

    ep_by_idx = {e["idx"]: e for e in files["episodes"]}
    tp_by_idx = {r["idx"]: r for r in true_pair["rows"]}
    ps_by_idx = {r["idx"]: r for r in parse["rows"]}

    def _typ(cd: str, path: str) -> float:
        t = typicality[cd]
        di = _drawer_idx(t["drawer_ids"], path)
        return t["mean_dist"][di]

    rows = []
    for idx, e in ep_by_idx.items():
        tp = tp_by_idx[idx]
        ps = ps_by_idx[idx]
        ex_typ = _typ(e["true_dir"], e["exemplar_path"])
        q_typ = _typ(e["true_dir"], e["query_path"])
        rows.append(dict(idx=idx, band=e["band"], rank=e["rank"], alph=e["alph"],
                          exemplar_typicality=ex_typ, query_typicality=q_typ,
                          dist_normalized=tp["dist_normalized"], dist_raw=tp["dist_raw"],
                          count_mismatch=tp["count_mismatch"], theta_cv=ps["theta_cv"],
                          q_overall=ps.get("q_overall")))

    control_rows = [r for r in rows if r["band"] == "control"]

    def _p(key, pct):
        vals = [r[key] for r in control_rows if r[key] is not None and not
                (isinstance(r[key], float) and np.isnan(r[key]))]
        return float(np.percentile(vals, pct))

    thr_ex_typ_p90 = _p("exemplar_typicality", 90)
    thr_q_typ_p90 = _p("query_typicality", 90)
    thr_theta_cv_p90 = _p("theta_cv", 90)
    thr_q_overall_p10 = _p("q_overall", 10)
    thr_dist_p90 = _p("dist_normalized", 90)
    print(f"  PRE-REGISTERED THRESHOLDS (control p90/p10, n={len(control_rows)}):")
    print(f"    exemplar_typicality p90 = {thr_ex_typ_p90:.4f}")
    print(f"    query_typicality    p90 = {thr_q_typ_p90:.4f}")
    print(f"    theta_cv            p90 = {thr_theta_cv_p90:.4f}")
    print(f"    q_overall           p10 = {thr_q_overall_p10:.4f}")
    print(f"    dist_normalized     p90 = {thr_dist_p90:.4f}")

    def _classify(r) -> str:
        if r["count_mismatch"]:
            return "COUNT-MISMATCH"
        theta_bad = (not np.isnan(r["theta_cv"])) and r["theta_cv"] > thr_theta_cv_p90
        fid_bad = (r["q_overall"] is not None) and r["q_overall"] < thr_q_overall_p10
        if theta_bad or fid_bad:
            return "PARSE-UNSTABLE"
        ex_bad = r["exemplar_typicality"] > thr_ex_typ_p90
        q_bad = r["query_typicality"] > thr_q_typ_p90
        if ex_bad and q_bad:
            return "BOTH-OUTLIER"
        if ex_bad:
            return "EXEMPLAR-OUTLIER"
        if q_bad:
            return "QUERY-OUTLIER"
        if (not np.isnan(r["dist_normalized"])) and r["dist_normalized"] > thr_dist_p90:
            return "GENUINE-DIVERGENCE"
        return "UNFLAGGED"

    for r in rows:
        r["diagnosis"] = _classify(r)

    table = defaultdict(lambda: defaultdict(int))
    for r in rows:
        table[r["band"]][r["diagnosis"]] += 1

    diag_order = ["COUNT-MISMATCH", "PARSE-UNSTABLE", "BOTH-OUTLIER", "EXEMPLAR-OUTLIER",
                  "QUERY-OUTLIER", "GENUINE-DIVERGENCE", "UNFLAGGED"]
    band_order = ["near", "mid", "far", "control"]
    print(f"\n  BAND x DIAGNOSIS TABLE:")
    header = f"    {'diagnosis':<20}" + "".join(f"{b:>10}" for b in band_order)
    print(header)
    for d in diag_order:
        line = f"    {d:<20}" + "".join(f"{table[b][d]:>10}" for b in band_order)
        print(line)
    totals = {b: sum(table[b].values()) for b in band_order}
    print(f"    {'TOTAL':<20}" + "".join(f"{totals[b]:>10}" for b in band_order))

    far_total = totals["far"]
    far = table["far"]
    fixable_exemplar = far["EXEMPLAR-OUTLIER"] + far["BOTH-OUTLIER"]
    fixable_parse = far["PARSE-UNSTABLE"] + far["COUNT-MISMATCH"]
    irreducible_query = far["QUERY-OUTLIER"]
    mystery = far["GENUINE-DIVERGENCE"] + far["UNFLAGGED"]
    print(f"\n  FAR-TAIL FIXABILITY (n={far_total}):")
    print(f"    (a) exemplar-expansion-fixable (EXEMPLAR-OUTLIER + BOTH-OUTLIER): "
          f"{fixable_exemplar}/{far_total} = {100*fixable_exemplar/far_total:.1f}%")
    print(f"    (b) parse-robustness-fixable (PARSE-UNSTABLE + COUNT-MISMATCH): "
          f"{fixable_parse}/{far_total} = {100*fixable_parse/far_total:.1f}%")
    print(f"    (c) irreducible one-exemplar bad luck (QUERY-OUTLIER): "
          f"{irreducible_query}/{far_total} = {100*irreducible_query/far_total:.1f}%")
    print(f"    (d) mystery (GENUINE-DIVERGENCE + UNFLAGGED): "
          f"{mystery}/{far_total} = {100*mystery/far_total:.1f}%")

    # ---- HONEST SURPRISE, reported per the launch brief's "report honestly" instruction: -----
    # COUNT-MISMATCH turned out NON-DISCRIMINATING (control 58.8%, near 72.0%, mid 52.9%, far
    # 52.6% -- roughly FLAT across bands, near even HIGHER than far). It is a ubiquitous
    # background condition the marginal verdict already tolerates (consistent with the
    # architecture: `marginal_part_error_term` marginalises over theta-grid ParseHyps and never
    # requires exact stroke-count correspondence) -- NOT a driver of far-tail failure
    # specifically. Priority-1 gating on it (as pre-registered) therefore SWALLOWS most of the
    # far tail into a bucket that is equally present in passed control episodes, which is
    # misleading as a "parse-robustness-fixable" headline. A SECOND, ADJUSTED classification is
    # reported below (count-mismatch DEMOTED from an exclusive gate to an orthogonal reported
    # flag, priority order PARSE-UNSTABLE > BOTH > EXEMPLAR > QUERY > GENUINE-DIVERGENCE >
    # UNFLAGGED) -- this is a POST-HOC honesty correction, clearly labelled as such, NOT a
    # silent replacement of the pre-registered primary table (printed first, unchanged).
    def _classify_adjusted(r) -> str:
        theta_bad = (not np.isnan(r["theta_cv"])) and r["theta_cv"] > thr_theta_cv_p90
        fid_bad = (r["q_overall"] is not None) and r["q_overall"] < thr_q_overall_p10
        if theta_bad or fid_bad:
            return "PARSE-UNSTABLE"
        ex_bad = r["exemplar_typicality"] > thr_ex_typ_p90
        q_bad = r["query_typicality"] > thr_q_typ_p90
        if ex_bad and q_bad:
            return "BOTH-OUTLIER"
        if ex_bad:
            return "EXEMPLAR-OUTLIER"
        if q_bad:
            return "QUERY-OUTLIER"
        if (not np.isnan(r["dist_normalized"])) and r["dist_normalized"] > thr_dist_p90:
            return "GENUINE-DIVERGENCE"
        return "UNFLAGGED"

    for r in rows:
        r["diagnosis_adjusted"] = _classify_adjusted(r)

    table_adj = defaultdict(lambda: defaultdict(int))
    mismatch_rate = defaultdict(lambda: [0, 0])
    for r in rows:
        table_adj[r["band"]][r["diagnosis_adjusted"]] += 1
        mismatch_rate[r["band"]][1] += 1
        if r["count_mismatch"]:
            mismatch_rate[r["band"]][0] += 1

    diag_order_adj = ["PARSE-UNSTABLE", "BOTH-OUTLIER", "EXEMPLAR-OUTLIER", "QUERY-OUTLIER",
                       "GENUINE-DIVERGENCE", "UNFLAGGED"]
    print(f"\n  COUNT-MISMATCH rate by band (query stroke count != exemplar stroke count) --"
          f" the honest surprise, roughly FLAT:")
    for b in band_order:
        k, n = mismatch_rate[b]
        print(f"    {b:<8} {k:>3}/{n:<3} = {100*k/n:.1f}%")

    print(f"\n  ADJUSTED BAND x DIAGNOSIS TABLE (count-mismatch demoted to an orthogonal flag, "
          f"NOT a priority-1 gate -- post-hoc honesty correction, see comment above):")
    header = f"    {'diagnosis':<20}" + "".join(f"{b:>10}" for b in band_order)
    print(header)
    for d in diag_order_adj:
        line = f"    {d:<20}" + "".join(f"{table_adj[b][d]:>10}" for b in band_order)
        print(line)
    totals_adj = {b: sum(table_adj[b].values()) for b in band_order}
    print(f"    {'TOTAL':<20}" + "".join(f"{totals_adj[b]:>10}" for b in band_order))

    far_adj = table_adj["far"]
    control_adj = table_adj["control"]
    near_adj = table_adj["near"]
    fixable_exemplar_adj = far_adj["EXEMPLAR-OUTLIER"] + far_adj["BOTH-OUTLIER"]
    fixable_parse_adj = far_adj["PARSE-UNSTABLE"]
    irreducible_query_adj = far_adj["QUERY-OUTLIER"]
    mystery_adj = far_adj["GENUINE-DIVERGENCE"] + far_adj["UNFLAGGED"]
    control_exemplar_rate = (control_adj["EXEMPLAR-OUTLIER"] + control_adj["BOTH-OUTLIER"]) / totals_adj["control"]
    near_exemplar_rate = (near_adj["EXEMPLAR-OUTLIER"] + near_adj["BOTH-OUTLIER"]) / totals_adj["near"]
    far_exemplar_rate = fixable_exemplar_adj / far_total
    print(f"\n  ADJUSTED FAR-TAIL FIXABILITY (n={far_total}):")
    print(f"    (a) exemplar-expansion-fixable (EXEMPLAR-OUTLIER + BOTH-OUTLIER): "
          f"{fixable_exemplar_adj}/{far_total} = {100*far_exemplar_rate:.1f}%  "
          f"[vs near {100*near_exemplar_rate:.1f}%, control {100*control_exemplar_rate:.1f}%]")
    print(f"    (b) parse-robustness-fixable (PARSE-UNSTABLE only -- count-mismatch excluded, "
          f"non-discriminating): {fixable_parse_adj}/{far_total} = {100*fixable_parse_adj/far_total:.1f}%")
    print(f"    (c) irreducible one-exemplar bad luck (QUERY-OUTLIER): "
          f"{irreducible_query_adj}/{far_total} = {100*irreducible_query_adj/far_total:.1f}%")
    print(f"    (d) mystery (GENUINE-DIVERGENCE + UNFLAGGED): "
          f"{mystery_adj}/{far_total} = {100*mystery_adj/far_total:.1f}%")

    out = dict(thresholds=dict(exemplar_typicality_p90=thr_ex_typ_p90,
                                query_typicality_p90=thr_q_typ_p90,
                                theta_cv_p90=thr_theta_cv_p90,
                                q_overall_p10=thr_q_overall_p10,
                                dist_normalized_p90=thr_dist_p90),
               rows=rows, table={b: dict(table[b]) for b in band_order},
               far_tail_fixability=dict(fixable_exemplar=fixable_exemplar,
                                         fixable_parse=fixable_parse,
                                         irreducible_query=irreducible_query,
                                         mystery=mystery, far_total=far_total),
               table_adjusted={b: dict(table_adj[b]) for b in band_order},
               mismatch_rate_by_band={b: mismatch_rate[b] for b in band_order},
               far_tail_fixability_adjusted=dict(fixable_exemplar=fixable_exemplar_adj,
                                                  fixable_parse=fixable_parse_adj,
                                                  irreducible_query=irreducible_query_adj,
                                                  mystery=mystery_adj, far_total=far_total,
                                                  far_exemplar_rate=far_exemplar_rate,
                                                  near_exemplar_rate=near_exemplar_rate,
                                                  control_exemplar_rate=control_exemplar_rate))
    _save_json(out, _ckpt("classify.json"))
    print(f"\n  classify.json written.")
    return 0


# ===============================================================================================
# STAGE: report -- consolidate.
# ===============================================================================================
def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 40 -- FAR-TAIL DIAGNOSIS -- FINAL REPORT\n{SEP}")
    for name in ["guard", "files", "class_matrices", "class_typicality", "true_pair", "parse",
                 "classify"]:
        p = _ckpt(f"{name}.json")
        print(f"  {name}.json: {'present' if os.path.exists(p) else 'MISSING'}")
    return 0


STAGES = {
    "guard": stage_guard,
    "files": stage_files,
    "class_matrices": stage_class_matrices,
    "true_pair": stage_true_pair,
    "parse": stage_parse,
    "classify": stage_classify,
    "report": stage_report,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=list(STAGES.keys()) + ["all"])
    args = ap.parse_args()
    order = ["guard", "files", "class_matrices", "true_pair", "parse", "classify", "report"]
    stages = order if args.stage == "all" else [args.stage]
    for st in stages:
        rc = STAGES[st]()
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
