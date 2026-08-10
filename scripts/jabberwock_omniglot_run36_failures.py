"""OMNIGLOT RUN 36 -- FAILURE TAXONOMY: "what do the glyphs or words we fail on have in
common." PURE ANALYSIS -- no training, no new mechanism, no mint, no teach(). Reads the
already-scored, already-committed `results/run26_checkpoints/eval_baseline.json` (n=400,
full-dwell 80.5% [76.3,84.1], the arc's own verdict-layer ceiling after six independent nulls)
and cross-checks against `results/run34_checkpoints/verdict_raw.json` (a DIFFERENT episode
chain, same protocol family: WAY=20, R_TARGET=2, N_TEST_ALPHABETS=10, same 10 sorted-name test
alphabets, `denoise=False`). Every number below is measured from files already on disk plus
cheap re-derivation (median stroke counts, pairwise continuous-comparator distances,
per-stroke greedy matches) -- nothing here re-runs the eval loop or touches the live agent.

PROTOCOL-GUARD (binding, checked in `stage guard` before anything downstream is trusted):
`eval_baseline.json` stores EPISODE-RELATIVE indices (`true`=qi, `pred_full`/`pred_shortlist`
=ci) into that BLOCK's own 20-way lineup -- `chars = sorted(ow.characters(alph,
"evaluation"))[:WAY]` (deterministic, no RNG) gives the class directory for any index; the
exemplar DRAWER per class (`ex_drawer`, shared by every candidate in a block) requires
replaying `run25._block_spec`'s own RNG draws in the SAME order the eval loop consumed them:
`official_rng = np.random.default_rng(run25.POWER_SEED)`, one `_block_spec` call per block in
`[(alph, r) for alph in test_alphabets for r in range(R_TARGET)]` order (alph OUTER, r INNER --
`eval_baseline.json`'s own record order is exactly this, 20 queries per block, block_idx =
record_idx // 20). `run34`'s `verdict_raw.json` uses a DIFFERENT, independent per-block RNG
(`rng_seed=gate.SEED+1500; rng=default_rng(rng_seed + r*9973 + sha1(alph)%100000)`, plan order
r OUTER alph INNER) -- reconstructed the same way but keyed directly, no sequential replay
needed. Both reconstructions are verified against the cited per-alphabet error table
(Ge_ez 20/40, Kannada 13/40, Aurek-Besh 3/40, Glagolitic 3/40, total 78/400) before any
downstream number is computed -- if this guard fails, STOP.

PRE-REGISTERED PREDICTIONS (stated here BEFORE the corresponding numbers are computed):
  P1 STROKE-COUNT: low-stroke-count classes (1-2 strokes: little arrangement to carry
     identity) fail MORE OFTEN than high-stroke-count classes, across all three outcome
     definitions (full-dwell error, proposal-blind, shortlist error).
  P2 CONFUSION GEOMETRY: full-dwell errors are overwhelmingly RANK-1/2 nearest-impostor
     confusions (the predicted class is one of the 1-2 geometrically closest classes to the
     true one in that block's own SC+TPS exemplar space), not random misses across the 19
     impostors. AND: failed episodes' true classes have a CLOSER nearest impostor than passed
     episodes' true classes (an alphabet-geometry effect, not a comparator coin-flip on equally
     easy geometry).
  P3 DIFFERENCE ELEMENT: for the most-confused true/predicted pairs, the element that
     distinguishes them (worst-matched or unmatched stroke under a per-stroke greedy match) is
     SMALL -- median ink fraction (arc length / total glyph arc length) well under 0.2, i.e.
     "they differ by a hook."
  P4 REPLICATE STABILITY: failing on a class in r=0 predicts failing on the SAME class in r=1
     (class-level property, not episode noise) -- and per-class failure propensity correlates
     positively between run26 (own protocol) and run34's raw arm (different episode chain, same
     protocol family).
  P5 BLIND VS VERDICT: proposal-blind failures and full-dwell-verdict failures are PARTLY
     overlapping but substantially DIFFERENT populations at the class level (first cut, episode
     level: only 21/78 verdict errors were proposal-blind) -- and blindness correlates with a
     DIFFERENT property (stroke count and/or ink-complexity) than verdict confusion does.

METHODOLOGY NOTES (stated honestly, not buried):
  - The "SC+TPS-style distance" reused throughout is `abs_read.sctps_verdict_term` (unweighted
    `Plus([ShapeContextDist, TpsDeformDist])` over `whole_figure_point_set`-normalized
    whole-figure point sets) -- the SAME comparator `abs_read.sctps_rerank`/RUN 16's
    reconciliation established as this arc's verdict-layer comparator family. It is a
    deliberately simpler stand-in for the actual eval-time verdict
    (`predict_smooth_marginal_sc_term`, a part-marginal fusion over theta-grid `ParseHyp`s) --
    using the full marginal verdict pairwise (class vs class, not query vs candidate-pool) has
    no direct meaning, so the whole-figure SC+TPS distance is the closest available apples-to-
    apples PAIRWISE geometry read off this exact comparator family. Computed once per block
    between EXEMPLAR files only (`drawer_files[ci][ex_drawer]`, the block's own shared
    exemplar per class) -- 20 blocks x C(20,2)=190 pairs = 3800 evaluates, ~10s total.
  - Per-stroke greedy match (stage `difference`) uses the Rust `PointSetDist` Term (order/
    count-invariant point-cloud distance) between EACH glyph's own strokes, both glyphs
    independently centre+abs-max normalized (the SAME convention `whole_figure_point_set` uses)
    so ink fraction is comparable across characters of different physical size. This is a
    coarse, self-contained stand-in for a real stroke-correspondence model -- stated here so it
    is never mistaken for a calibrated result.
  - "Program-token count" (stage `blind_vs_verdict`) is NOT `stroke_programs.py`'s calibrated,
    denoised, adaptive-edge tokenizer (that pipeline depends on run34d's cited edge fit and
    mouse-model denoising, out of scope for a measurement-only run) -- it is a much simpler,
    self-contained per-class total point-count (ink volume) proxy, labelled as such throughout.

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run36.log`, checkpoints under `results/run36_checkpoints/` (all other
run*_checkpoints dirs READ-ONLY reference). `.venv` python (needs `substrate_rs`).

Stages (run in order, each checkpointed):
  --stage guard        Reconstruct run26 + run34 block/RNG chains; verify the cited
                        per-alphabet error table EXACTLY before proceeding.
  --stage stroke_count  P1.
  --stage confusion     P2 (the 20 exemplar distance matrices + rank/nearest-impostor stats).
  --stage difference    P3 (needs `confusion`'s matrices).
  --stage replicate     P4 (needs `guard`'s run34 reconstruction).
  --stage blind         P5.
  --stage report        Print the final consolidated tables from every checkpoint.
  --stage all           Run every stage in sequence (fast enough to fit one invocation).
"""
from __future__ import annotations

import argparse
import hashlib
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
CKPT_DIR = os.path.join(ROOT, "results", "run36_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")   # READ-ONLY reference.
RUN34_DIR = os.path.join(ROOT, "results", "run34_checkpoints")   # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

CITED_PER_ALPH_FULL_DWELL_ERRORS = {
    "Angelic": 4, "Atemayar_Qelisayer": 9, "Atlantean": 4, "Aurek-Besh": 3, "Avesta": 6,
    "Ge_ez": 20, "Glagolitic": 3, "Gurmukhi": 9, "Kannada": 13, "Keble": 7,
}
CITED_TOTAL_FULL_DWELL_ERRORS = 78
CITED_TOTAL_PROPOSAL_BLIND = 114
CITED_TOTAL_SHORTLIST_ERRORS = 152
CITED_OVERLAP_BLIND_AND_ERROR = 21


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


# ===============================================================================================
# STAGE: guard -- reconstruct both episode chains, map indices -> class directories.
# ===============================================================================================
def _run25_deps():
    import scripts.jabberwock_omniglot_run25_number as run25
    from domains import omniglot_world as ow
    return run25, ow


def _test_alphabets(run25, ow) -> list:
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= run25.WAY)
    return qualifying[:run25.N_TEST_ALPHABETS]


def _reconstruct_run26_blocks(run25, ow) -> list:
    """Block order == `eval_baseline.json`'s own record order: alph OUTER, r INNER, one
    `_block_spec` draw per block off a SINGLE sequentially-advanced `POWER_SEED` stream."""
    test_alphabets = _test_alphabets(run25, ow)
    rng = np.random.default_rng(run25.POWER_SEED)
    blocks = []
    for alph in test_alphabets:
        for r in range(run25.R_TARGET):
            spec = run25._block_spec(alph, rng, run25.WAY, run25.EPISODES_PER_ALPHABET)
            chars = sorted(ow.characters(alph, "evaluation"))[:run25.WAY]
            blocks.append(dict(alph=alph, r=r, chars=chars,
                                ex_drawer=spec["ex_drawer"], drawer_files=spec["drawer_files"]))
    return blocks, test_alphabets


def _reconstruct_run34_blocks(run25, ow) -> list:
    """`verdict_raw.json`'s own block order: r OUTER, alph INNER, one INDEPENDENT per-block RNG
    keyed by `(r, alph)` via a sha1 hash -- byte-identical to
    `jabberwock_omniglot_run34_mouse.stage_verdict`'s own construction."""
    test_alphabets = _test_alphabets(run25, ow)
    gate_seed = 20260702           # scripts.jabberwock_omniglot_dynamic_quantization.SEED,
    power_offset = 1500            # cited verbatim -- avoids importing the full gate module.
    rng_seed = gate_seed + power_offset
    blocks = []
    for r in range(run25.R_TARGET):
        for alph in test_alphabets:
            alph_hash = int(hashlib.sha1(alph.encode()).hexdigest()[:8], 16) % 100000
            rng = np.random.default_rng(rng_seed + r * 9973 + alph_hash)
            spec = run25._block_spec(alph, rng, run25.WAY, run25.EPISODES_PER_ALPHABET)
            chars = sorted(ow.characters(alph, "evaluation"))[:run25.WAY]
            blocks.append(dict(alph=alph, r=r, chars=chars,
                                ex_drawer=spec["ex_drawer"], drawer_files=spec["drawer_files"]))
    return blocks, test_alphabets


def stage_guard() -> int:
    print(f"\n{SEP}\n  STAGE: guard -- protocol-guard (reconstruct + verify the cited table)\n{SEP}")
    run25, ow = _run25_deps()
    records = _load_eval_baseline()
    print(f"  eval_baseline.json: n={len(records)}")

    blocks26, test_alphabets = _reconstruct_run26_blocks(run25, ow)
    assert len(blocks26) == 20, f"expected 20 run26 blocks, got {len(blocks26)}"
    assert len(records) == 400

    per_alph_err = defaultdict(int)
    per_alph_tot = defaultdict(int)
    full_err_idx, blind_idx, sl_err_idx = [], [], []
    for i, r in enumerate(records):
        per_alph_tot[r["alph"]] += 1
        if r["pred_full"] != r["true"]:
            per_alph_err[r["alph"]] += 1
            full_err_idx.append(i)
        if not r["in_shortlist"]:
            blind_idx.append(i)
        if r["pred_shortlist"] != r["true"]:
            sl_err_idx.append(i)

    print(f"\n  per-alphabet full-dwell errors (measured vs cited):")
    all_match = True
    for alph in test_alphabets:
        got, want = per_alph_err[alph], CITED_PER_ALPH_FULL_DWELL_ERRORS[alph]
        ok = got == want
        all_match = all_match and ok
        print(f"    {alph:<22} {got:>3}/{per_alph_tot[alph]:<3} (cited {want})  "
              f"{'OK' if ok else 'MISMATCH -- STOP'}")

    overlap = len(set(full_err_idx) & set(blind_idx))
    print(f"\n  totals: full_dwell_errors={len(full_err_idx)} (cited {CITED_TOTAL_FULL_DWELL_ERRORS})"
          f"  proposal_blind={len(blind_idx)} (cited {CITED_TOTAL_PROPOSAL_BLIND})"
          f"  shortlist_errors={len(sl_err_idx)} (cited {CITED_TOTAL_SHORTLIST_ERRORS})"
          f"  overlap(err&blind)={overlap} (cited {CITED_OVERLAP_BLIND_AND_ERROR})")

    guard_ok = (all_match and len(full_err_idx) == CITED_TOTAL_FULL_DWELL_ERRORS
                and len(blind_idx) == CITED_TOTAL_PROPOSAL_BLIND
                and len(sl_err_idx) == CITED_TOTAL_SHORTLIST_ERRORS
                and overlap == CITED_OVERLAP_BLIND_AND_ERROR)
    print(f"\n  PROTOCOL GUARD: {'PASS -- proceeding' if guard_ok else 'FAIL -- STOP, do not trust downstream numbers'}")
    if not guard_ok:
        return 1

    # run34 cross-check reconstruction (verified against its own recorded 'alphs'/'trues').
    blocks34, test_alphabets34 = _reconstruct_run34_blocks(run25, ow)
    run34 = _load_json(os.path.join(RUN34_DIR, "verdict_raw.json"))
    assert len(run34["trues"]) == 400 and len(blocks34) == 20
    ok34 = True
    for bi, blk in enumerate(blocks34):
        for qi in range(20):
            i = bi * 20 + qi
            if run34["alphs"][i] != blk["alph"] or run34["trues"][i] != qi:
                ok34 = False
    print(f"  run34 verdict_raw.json block reconstruction: {'OK' if ok34 else 'MISMATCH -- STOP'}"
          f"  (n={len(run34['trues'])}, acc={np.mean([p == t for p, t in zip(run34['preds'], run34['trues'])]):.3f})")
    if not ok34:
        return 1

    out = dict(guard_ok=True, ok34=True,
               test_alphabets=test_alphabets,
               blocks26=[{k: v for k, v in b.items() if k != "drawer_files"} for b in blocks26],
               blocks34=[{k: v for k, v in b.items() if k != "drawer_files"} for b in blocks34],
               full_err_idx=full_err_idx, blind_idx=blind_idx, sl_err_idx=sl_err_idx)
    _save_json(out, _ckpt("guard.json"))
    print(f"\n  guard.json written -- {len(full_err_idx)} full-dwell errors, "
          f"{len(blind_idx)} proposal-blind, {len(sl_err_idx)} shortlist errors, all confirmed.")
    return 0


def _require_guard():
    p = _ckpt("guard.json")
    if not os.path.exists(p):
        print("  WALL: run --stage guard first.")
        sys.exit(1)
    return _load_json(p)


# ===============================================================================================
# STAGE: stroke_count -- P1.
# ===============================================================================================
def _bucket(n: float) -> str:
    r = int(round(n))
    return str(r) if r < 5 else "5+"


def stage_stroke_count() -> int:
    print(f"\n{SEP}\n  STAGE: stroke_count -- P1 (low-stroke classes fail more?)\n{SEP}")
    guard = _require_guard()
    run25, ow = _run25_deps()
    records = _load_eval_baseline()

    # Median stroke count per class, over its own 20 drawer files (deterministic, no RNG).
    class_dirs = sorted({c for alph in guard["test_alphabets"]
                          for c in sorted(ow.characters(alph, "evaluation"))[:run25.WAY]})
    print(f"  {len(class_dirs)} unique classes across {len(guard['test_alphabets'])} test alphabets")
    stroke_count = {}
    for cd in class_dirs:
        counts = [len(ow.load_strokes(f)) for f in ow.drawings(cd)]
        stroke_count[cd] = float(np.median(counts))
    _save_json(stroke_count, _ckpt("class_stroke_count.json"))

    full_err_idx, blind_idx, sl_err_idx = (set(guard["full_err_idx"]), set(guard["blind_idx"]),
                                            set(guard["sl_err_idx"]))
    blocks26 = guard["blocks26"]

    def true_class_dir(i):
        blk = blocks26[i // 20]
        return blk["chars"][records[i]["true"]]

    buckets = ["1", "2", "3", "4", "5+"]
    tables = {}
    for name, err_set in [("full_dwell_error", full_err_idx), ("proposal_blind", blind_idx),
                           ("shortlist_error", sl_err_idx)]:
        fail_n = {b: 0 for b in buckets}
        tot_n = {b: 0 for b in buckets}
        for i in range(len(records)):
            b = _bucket(stroke_count[true_class_dir(i)])
            tot_n[b] += 1
            if i in err_set:
                fail_n[b] += 1
        tables[name] = {b: dict(fail=fail_n[b], total=tot_n[b],
                                 rate=(fail_n[b] / tot_n[b] if tot_n[b] else None)) for b in buckets}
        print(f"\n  {name}: failure rate by median-stroke-count bucket")
        for b in buckets:
            t = tables[name][b]
            r = f"{100 * t['rate']:.1f}%" if t["rate"] is not None else "n/a"
            print(f"    strokes={b:<3}  fail={t['fail']:>3}/{t['total']:<3}  rate={r}")

    _save_json(tables, _ckpt("stroke_count_tables.json"))
    print(f"\n  stroke_count_tables.json written.")
    return 0


# ===============================================================================================
# STAGE: confusion -- P2 (the core). Per-block 20x20 exemplar SC+TPS distance matrix.
# ===============================================================================================
def stage_confusion() -> int:
    print(f"\n{SEP}\n  STAGE: confusion -- P2 (rank of predicted among 19 impostors)\n{SEP}")
    guard = _require_guard()
    run25, ow = _run25_deps()
    from domains import abs_read as ar
    import substrate_rs as srs
    native = srs.Substrate()._inner

    out_path = _ckpt("confusion_matrices.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(matrices={})

    # Re-derive the FULL per-block spec (need drawer_files, not stored in guard.json) once.
    blocks26_full, _ = _reconstruct_run26_blocks(run25, ow)
    t0 = time.time()
    for bi, blk in enumerate(blocks26_full):
        key = str(bi)
        if key in state["matrices"]:
            continue
        drawer_files, ex_drawer = blk["drawer_files"], blk["ex_drawer"]
        point_sets = []
        for ci in range(run25.WAY):
            path = drawer_files[ci][ex_drawer]
            ps = ar.whole_figure_point_set(run25._raw_stroke_points(path))
            point_sets.append(ps)
        M = [[0.0] * run25.WAY for _ in range(run25.WAY)]
        for ci in range(run25.WAY):
            for cj in range(ci + 1, run25.WAY):
                if point_sets[ci] is None or point_sets[cj] is None:
                    d = float("nan")
                else:
                    term = ar.sctps_verdict_term(point_sets[ci], point_sets[cj])
                    d = float(native.evaluate(term, {}) or float("nan"))
                M[ci][cj] = M[cj][ci] = d
        state["matrices"][key] = M
        _save_json(state, out_path)
        print(f"  block {bi:>2} ({blk['alph']:<22} r={blk['r']}) matrix done "
              f"({time.time() - t0:.1f}s elapsed total)")

    print(f"\n  confusion_matrices.json complete -- {len(state['matrices'])}/20 blocks.")

    # ---- P2 analysis: rank of predicted among 19 impostors; nearest-impostor distance. ------
    records = _load_eval_baseline()
    blocks26 = guard["blocks26"]
    full_err_idx = set(guard["full_err_idx"])
    ranks = []
    nearest_impostor_error = []
    nearest_impostor_pass = []
    for i, r in enumerate(records):
        bi = i // 20
        M = state["matrices"][str(bi)]
        t, p = r["true"], r["pred_full"]
        dists = [(cj, M[t][cj]) for cj in range(20) if cj != t and not np.isnan(M[t][cj])]
        if not dists:
            continue
        dists_sorted = sorted(dists, key=lambda x: x[1])
        nearest = dists_sorted[0][1]
        if i in full_err_idx:
            if p is not None and p >= 0 and p != t:
                rank = 1 + sum(1 for cj, d in dists if d < M[t][p])
                ranks.append(rank)
            nearest_impostor_error.append(nearest)
        else:
            nearest_impostor_pass.append(nearest)

    rank_hist = Counter(ranks)
    print(f"\n  impostor-RANK histogram of the predicted class among 19 impostors, "
          f"{len(ranks)} full-dwell errors (rank 1 = geometrically nearest impostor):")
    for k in sorted(rank_hist):
        print(f"    rank {k:>2}: {rank_hist[k]:>3}  ({100 * rank_hist[k] / len(ranks):.1f}%)")
    top2 = sum(v for k, v in rank_hist.items() if k <= 2)
    print(f"  rank<=2 share: {top2}/{len(ranks)} = {100 * top2 / len(ranks):.1f}%")

    def _stats(xs):
        a = np.asarray(xs, dtype=float)
        return dict(n=len(a), mean=float(a.mean()), median=float(np.median(a)),
                    p25=float(np.percentile(a, 25)), p75=float(np.percentile(a, 75)))

    err_stats = _stats(nearest_impostor_error)
    pass_stats = _stats(nearest_impostor_pass)
    print(f"\n  nearest-impostor distance -- FAILED episodes:  {err_stats}")
    print(f"  nearest-impostor distance -- PASSED episodes:  {pass_stats}")

    out = dict(ranks=ranks, rank_hist=dict(rank_hist),
               nearest_impostor_error=nearest_impostor_error,
               nearest_impostor_pass=nearest_impostor_pass,
               err_stats=err_stats, pass_stats=pass_stats)
    _save_json(out, _ckpt("confusion_analysis.json"))
    print(f"\n  confusion_analysis.json written.")
    return 0


# ===============================================================================================
# STAGE: difference -- P3. Top ~30 most-confused pairs, per-stroke greedy match, ink fraction.
# ===============================================================================================
def _normalize_glyph(strokes: list) -> tuple:
    allpts = np.concatenate([np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes], axis=0)
    center = allpts.mean(0)
    scale = float(np.abs(allpts - center).max()) or 1e-9
    normed = [(np.asarray(s, dtype=float).reshape(-1, 2) - center) / scale for s in strokes]
    arclens = []
    for s in normed:
        if s.shape[0] < 2:
            arclens.append(0.0)
            continue
        d = np.diff(s, axis=0)
        arclens.append(float(np.sqrt((d ** 2).sum(1)).sum()))
    total = sum(arclens) or 1e-9
    return normed, arclens, total


def _greedy_stroke_match(native, true_strokes, pred_strokes):
    t_norm, t_arc, t_tot = _normalize_glyph(true_strokes)
    p_norm, p_arc, p_tot = _normalize_glyph(pred_strokes)
    costs = {}
    for i, ts in enumerate(t_norm):
        for j, ps in enumerate(p_norm):
            term = {"type": "PointSetDist",
                    "a": {"type": "Lit", "value": ts.tolist()},
                    "b": {"type": "Lit", "value": ps.tolist()}}
            costs[(i, j)] = float(native.evaluate(term, {}) or float("nan"))
    order = sorted(costs.items(), key=lambda kv: kv[1])
    used_i, used_j, matched = set(), set(), []
    for (i, j), c in order:
        if i in used_i or j in used_j:
            continue
        used_i.add(i)
        used_j.add(j)
        matched.append((i, j, c))
    unmatched_true = [i for i in range(len(t_norm)) if i not in used_i]
    unmatched_pred = [j for j in range(len(p_norm)) if j not in used_j]
    return dict(matched=matched, unmatched_true=unmatched_true, unmatched_pred=unmatched_pred,
                t_arc=t_arc, t_tot=t_tot, p_arc=p_arc, p_tot=p_tot,
                n_true=len(t_norm), n_pred=len(p_norm))


SMALL_STROKE_INK_FRACTION_THRESHOLD = 0.20   # pre-registered (P3): "well under 0.2".


def stage_difference() -> int:
    print(f"\n{SEP}\n  STAGE: difference -- P3 (the difference element)\n{SEP}")
    guard = _require_guard()
    run25, ow = _run25_deps()
    from domains import abs_read as ar
    import substrate_rs as srs
    native = srs.Substrate()._inner

    conf_path = _ckpt("confusion_matrices.json")
    if not os.path.exists(conf_path):
        print("  WALL: run --stage confusion first.")
        return 1
    matrices = _load_json(conf_path)["matrices"]

    records = _load_eval_baseline()
    blocks26_full, _ = _reconstruct_run26_blocks(run25, ow)
    full_err_idx = guard["full_err_idx"]

    # Build one row per error episode: (block_idx, true_ci, pred_ci, distance), dedup identical
    # (block_idx, true_ci, pred_ci) triples (a repeat query hitting the same confusion within one
    # block is the SAME geometric pair, scored once).
    seen = set()
    rows = []
    for i in full_err_idx:
        bi = i // 20
        r = records[i]
        t, p = r["true"], r["pred_full"]
        if p is None or p < 0 or p == t:
            continue
        key = (bi, t, p)
        if key in seen:
            continue
        seen.add(key)
        d = matrices[str(bi)][t][p]
        rows.append(dict(block_idx=bi, alph=blocks26_full[bi]["alph"], r=blocks26_full[bi]["r"],
                          true_ci=t, pred_ci=p, dist=d,
                          true_dir=blocks26_full[bi]["chars"][t],
                          pred_dir=blocks26_full[bi]["chars"][p]))
    rows.sort(key=lambda x: x["dist"])
    print(f"  {len(rows)} unique (block, true, pred) confused pairs from {len(full_err_idx)} "
          f"full-dwell errors; taking the {min(30, len(rows))} closest by exemplar distance.")
    top = rows[:30]

    results = []
    for row in top:
        blk = blocks26_full[row["block_idx"]]
        true_path = blk["drawer_files"][row["true_ci"]][blk["ex_drawer"]]
        pred_path = blk["drawer_files"][row["pred_ci"]][blk["ex_drawer"]]
        true_strokes = ow.load_strokes(true_path)
        pred_strokes = ow.load_strokes(pred_path)
        if not true_strokes or not pred_strokes:
            continue
        gm = _greedy_stroke_match(native, true_strokes, pred_strokes)
        count_diff = gm["n_true"] - gm["n_pred"]
        if gm["unmatched_true"] or gm["unmatched_pred"]:
            # Count-mismatch case: the smallest unmatched stroke on whichever side has the extra.
            cands = ([("true", i, gm["t_arc"][i] / gm["t_tot"]) for i in gm["unmatched_true"]] +
                     [("pred", j, gm["p_arc"][j] / gm["p_tot"]) for j in gm["unmatched_pred"]])
            side, idx, frac = min(cands, key=lambda c: c[2])
            worst_kind = "unmatched"
        else:
            # Equal counts: the worst-MATCHED (highest-cost) pair; report the true-side fraction.
            i, j, c = max(gm["matched"], key=lambda m: m[2])
            side, idx, frac = "true", i, gm["t_arc"][i] / gm["t_tot"]
            worst_kind = "worst_matched"
        results.append(dict(**row, n_true_strokes=gm["n_true"], n_pred_strokes=gm["n_pred"],
                             count_diff=count_diff, worst_kind=worst_kind, worst_side=side,
                             ink_fraction=frac))
        print(f"    {row['alph']:<22} true={row['true_dir'].split('/')[-1]:<8} "
              f"pred={row['pred_dir'].split('/')[-1]:<8} dist={row['dist']:.3f} "
              f"strokes({gm['n_true']} vs {gm['n_pred']}) {worst_kind}={side} ink_frac={frac:.3f}")

    fracs = [r["ink_fraction"] for r in results]
    if fracs:
        print(f"\n  ink-fraction of the difference element ({len(fracs)} pairs): "
              f"median={np.median(fracs):.3f}  mean={np.mean(fracs):.3f}  "
              f"p25={np.percentile(fracs,25):.3f}  p75={np.percentile(fracs,75):.3f}")
        small = sum(1 for f in fracs if f < SMALL_STROKE_INK_FRACTION_THRESHOLD)
        print(f"  fraction < {SMALL_STROKE_INK_FRACTION_THRESHOLD}: {small}/{len(fracs)} "
              f"= {100*small/len(fracs):.1f}%")
    off_by_one_small = sum(1 for r in results if abs(r["count_diff"]) == 1
                            and r["ink_fraction"] < SMALL_STROKE_INK_FRACTION_THRESHOLD)
    print(f"  pairs where stroke COUNTS differ by exactly one SMALL stroke "
          f"(<{SMALL_STROKE_INK_FRACTION_THRESHOLD} ink): {off_by_one_small}/{len(results)}")

    _save_json(dict(rows=results, ink_fractions=fracs, off_by_one_small=off_by_one_small),
               _ckpt("difference_element.json"))
    print(f"\n  difference_element.json written.")
    return 0


# ===============================================================================================
# STAGE: replicate -- P4. Class-level stability r0 vs r1; run26 vs run34 correlation.
# ===============================================================================================
def stage_replicate() -> int:
    print(f"\n{SEP}\n  STAGE: replicate -- P4 (class-property vs episode-noise)\n{SEP}")
    guard = _require_guard()
    records = _load_eval_baseline()
    blocks26 = guard["blocks26"]

    # Per (alph, ci) class: fail indicator at r=0 and r=1 (chars list is IDENTICAL across r for
    # a given alphabet -- the same 20 classes reappear).
    fail26 = {}   # (alph, ci) -> {0: bool, 1: bool}
    for i, r in enumerate(records):
        blk = blocks26[i // 20]
        key = (blk["alph"], r["true"])
        fail26.setdefault(key, {})[blk["r"]] = (r["pred_full"] != r["true"])

    ff = fp = pf = pp = 0
    for key, d in fail26.items():
        if 0 not in d or 1 not in d:
            continue
        if d[0] and d[1]:
            ff += 1
        elif d[0] and not d[1]:
            fp += 1
        elif not d[0] and d[1]:
            pf += 1
        else:
            pp += 1
    n = ff + fp + pf + pp
    p_fail_r1_given_fail_r0 = ff / (ff + fp) if (ff + fp) else float("nan")
    p_fail_r1_given_pass_r0 = pf / (pf + pp) if (pf + pp) else float("nan")
    print(f"  run26 within-protocol r0-vs-r1 contingency (n={n} classes with both replicates):")
    print(f"    fail-fail={ff}  fail-pass={fp}  pass-fail={pf}  pass-pass={pp}")
    print(f"    P(fail r1 | fail r0)={p_fail_r1_given_fail_r0:.3f}   "
          f"P(fail r1 | pass r0)={p_fail_r1_given_pass_r0:.3f}   "
          f"(if class-property: LHS >> RHS; if episode-noise: LHS ~= RHS ~= overall fail rate "
          f"{78/400:.3f})")

    # run26 vs run34 per-class failure-RATE correlation (0/0.5/1 over each protocol's own 2 reps).
    run25, ow = _run25_deps()
    blocks34, _ = _reconstruct_run34_blocks(run25, ow)
    run34 = _load_json(os.path.join(RUN34_DIR, "verdict_raw.json"))
    fail34 = {}
    for i in range(len(run34["trues"])):
        blk = blocks34[i // 20]
        qi = run34["trues"][i]
        key = (blk["alph"], qi)
        fail34.setdefault(key, {})[blk["r"]] = (run34["preds"][i] != qi)

    rate26, rate34 = [], []
    for key in fail26:
        if key not in fail34:
            continue
        d26, d34 = fail26[key], fail34[key]
        if len(d26) < 2 or len(d34) < 2:
            continue
        rate26.append((int(d26[0]) + int(d26[1])) / 2.0)
        rate34.append((int(d34[0]) + int(d34[1])) / 2.0)
    rate26_a = np.asarray(rate26)
    rate34_a = np.asarray(rate34)
    corr = float(np.corrcoef(rate26_a, rate34_a)[0, 1]) if len(rate26) > 1 else float("nan")
    print(f"\n  per-class failure-RATE correlation, run26 vs run34-raw "
          f"(different episode chain, same protocol family), n={len(rate26)} classes:")
    print(f"    Pearson r = {corr:.3f}")
    both_never = sum(1 for a, b in zip(rate26, rate34) if a == 0 and b == 0)
    both_some = sum(1 for a, b in zip(rate26, rate34) if a > 0 and b > 0)
    only26 = sum(1 for a, b in zip(rate26, rate34) if a > 0 and b == 0)
    only34 = sum(1 for a, b in zip(rate26, rate34) if a == 0 and b > 0)
    print(f"    both-never-fail={both_never}  both-sometimes-fail={both_some}  "
          f"only-run26-fails={only26}  only-run34-fails={only34}")

    out = dict(contingency=dict(ff=ff, fp=fp, pf=pf, pp=pp,
                                 p_fail_r1_given_fail_r0=p_fail_r1_given_fail_r0,
                                 p_fail_r1_given_pass_r0=p_fail_r1_given_pass_r0),
               cross_run=dict(n=len(rate26), pearson_r=corr, both_never=both_never,
                               both_some=both_some, only26=only26, only34=only34,
                               rate26=rate26, rate34=rate34))
    _save_json(out, _ckpt("replicate_stability.json"))
    print(f"\n  replicate_stability.json written.")
    return 0


# ===============================================================================================
# STAGE: blind -- P5. Proposal-blind vs verdict-error populations at class level.
# ===============================================================================================
def _total_points(strokes) -> int:
    return sum(len(s) for s in strokes)


def stage_blind() -> int:
    print(f"\n{SEP}\n  STAGE: blind -- P5 (proposal-blind vs verdict-error contrast)\n{SEP}")
    guard = _require_guard()
    run25, ow = _run25_deps()
    records = _load_eval_baseline()
    blocks26 = guard["blocks26"]

    def true_class_key(i):
        blk = blocks26[i // 20]
        return (blk["alph"], blk["chars"][records[i]["true"]])

    blind_classes = {true_class_key(i) for i in guard["blind_idx"]}
    error_classes = {true_class_key(i) for i in guard["full_err_idx"]}
    overlap = blind_classes & error_classes
    union = blind_classes | error_classes
    print(f"  CLASS-level: proposal_blind_classes={len(blind_classes)}  "
          f"full_dwell_error_classes={len(error_classes)}  overlap={len(overlap)}  "
          f"jaccard={len(overlap)/len(union):.3f}")

    sc_path = _ckpt("class_stroke_count.json")
    stroke_count = _load_json(sc_path) if os.path.exists(sc_path) else {}
    if not stroke_count:
        print("  (class_stroke_count.json missing -- run --stage stroke_count first for the "
              "stroke-count contrast; proceeding with ink-volume proxy only.)")

    all_classes = {true_class_key(i) for i in range(len(records))}
    ink_volume = {}
    for alph, cd in all_classes:
        pts = [_total_points(ow.load_strokes(f)) for f in ow.drawings(cd)]
        ink_volume[cd] = float(np.median(pts))

    def _summ(classes, label):
        sc = [stroke_count.get(cd) for _, cd in classes if stroke_count.get(cd) is not None]
        iv = [ink_volume[cd] for _, cd in classes]
        print(f"    {label:<28} n={len(classes):>3}  "
              f"median_stroke_count={np.median(sc) if sc else float('nan'):.2f}  "
              f"median_ink_points={np.median(iv):.1f}")

    print(f"\n  stroke-count / ink-volume (median points per drawer file) by population:")
    _summ(blind_classes - error_classes, "blind-only")
    _summ(error_classes - blind_classes, "error-only")
    _summ(overlap, "blind & error")
    _summ(all_classes - blind_classes - error_classes, "neither")

    out = dict(blind_classes=sorted(list(blind_classes)), error_classes=sorted(list(error_classes)),
               overlap=sorted(list(overlap)),
               jaccard=len(overlap) / len(union) if union else None,
               ink_volume=ink_volume)
    _save_json(out, _ckpt("blind_vs_verdict.json"))
    print(f"\n  blind_vs_verdict.json written.")
    return 0


# ===============================================================================================
# STAGE: report -- consolidate every checkpoint.
# ===============================================================================================
def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 36 -- FAILURE TAXONOMY -- FINAL REPORT\n{SEP}")
    for name in ["guard", "class_stroke_count", "stroke_count_tables", "confusion_matrices",
                 "confusion_analysis", "difference_element", "replicate_stability",
                 "blind_vs_verdict"]:
        p = _ckpt(f"{name}.json")
        print(f"  {name}.json: {'present' if os.path.exists(p) else 'MISSING'}")
    return 0


STAGES = {
    "guard": stage_guard,
    "stroke_count": stage_stroke_count,
    "confusion": stage_confusion,
    "difference": stage_difference,
    "replicate": stage_replicate,
    "blind": stage_blind,
    "report": stage_report,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                     choices=list(STAGES.keys()) + ["all"])
    args = ap.parse_args()
    order = ["guard", "stroke_count", "confusion", "difference", "replicate", "blind", "report"]
    stages = order if args.stage == "all" else [args.stage]
    for s in stages:
        rc = STAGES[s]()
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
