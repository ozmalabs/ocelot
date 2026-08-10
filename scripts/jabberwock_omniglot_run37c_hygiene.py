"""OMNIGLOT RUN 37C -- GAP C, INGEST HYGIENE: the degenerate-zero-length-stroke filter.

The smallest of the three run-37 gap-closure runs (`results/run37_checkpoints/plan.json`,
commit 67005b35 -- the jabberwock's own plan, grounding Gap C as ARGMAX-BY-RELEVANCE /
`browse_rule`). RUN 36 (commit 5aa6bcb6) found: "ACTIONABLE ARTIFACT FOUND: 5/30 top
confusions are driven by DEGENERATE ZERO-LENGTH STROKES (stray single-point strokes in the
raw mouse traces, Keble/Kannada) matched as the 'distinguishing' element -- a data-hygiene
ingest filter, not a mechanism". This script builds and gates that filter.

THE 5 FLAGGED PAIRS (`results/run36_checkpoints/difference_element.json`, the rows with
`ink_fraction == 0.0` EXACTLY among the top-30 most-confused pairs -- a zero ink fraction
means the "distinguishing" stroke run 36's greedy per-stroke matcher picked out carries NO
ARC LENGTH AT ALL, the signature of a degenerate stroke, not a real geometric feature):
  Keble      block=18 r=0 true_ci=15(character16) pred_ci=13(character14)  unmatched   (5 vs 2 strokes)
  Kannada    block=17 r=1 true_ci=15(character16) pred_ci=8(character09)   unmatched   (4 vs 1 strokes)
  Keble      block=19 r=1 true_ci=13(character14) pred_ci=1(character02)   worst_matched (5 vs 5)
  Keble      block=19 r=1 true_ci=8(character09)  pred_ci=15(character16)  worst_matched (6 vs 6)
  Keble      block=19 r=1 true_ci=19(character20) pred_ci=13(character14) unmatched    (4 vs 5)

THE FILTER (`domains/omniglot_world.py`, this run's only code change): an opt-in
`drop_degenerate=False` param on `load_strokes`/`load_strokes_t` (threaded through
`trajectory`'s `per_stroke=True` branch, the only branch that takes strokes rather than raw
points). PRE-REGISTERED CRITERION (stated here BEFORE any gate below is run, `omniglot_world.
_is_degenerate_stroke`'s own docstring, quoted verbatim): "a stroke is DEGENERATE iff it is a
single recorded sample (m==1 -- no motion is even representable) OR every recorded sample sits
at the exact same (x, y) (m>=2 but zero arc length -- the pointer never moved between BREAKs).
This is NOT a size threshold: a short-but-real stroke that moves even one sub-pixel (a dot, a
tick -- genuine glyph elements in several alphabets) has nonzero arc length and is NOT
degenerate -- it MUST survive." Defaults stay `False` everywhere -- every pre-existing caller
in the codebase (LEARN, decode, the run-36 diagnostic itself) is byte-identical unless this
gate's own `DropDegenerateFilter` context is active.

WIRING FOR "EVERYWHERE STROKES LOAD" (this gate's own mechanism, NOT a module edit):
`abs_read.stage_parse_char`'s theta-grid staging and `jabberwock_omniglot_dynamic_
quantization.decode_char_signature`'s structural-proposal decode both do a LATE-BOUND
`ow.load_strokes(path)` (module-attribute lookup at call time, the SAME idiom `jabberwock_
plans_gap_closure.py` uses to redirect `teach()`), and `omniglot_world.trajectory`'s own
internal call to `load_strokes` resolves through the SAME module global namespace. So
`DropDegenerateFilter` (below) patches `domains.omniglot_world.load_strokes`/`load_strokes_t`
for the life of the `with` block, and EVERY caller downstream -- exemplar staging, query
staging, the structural shortlist decode -- gets filtered strokes, with zero edits to
`abs_read.py`, `jabberwock_omniglot_dynamic_quantization.py`, or any other module. The
module's own default (`False`) never changes.

GATES (this script, each independently invoked and checkpointed):
  --stage verify    Cite the run-26 baseline numbers verbatim (`results/run26_checkpoints/
                    eval_baseline.json` -- filter OFF IS exactly that protocol, nothing to
                    re-run there) PLUS a cheap correctness spot-check: reproduce run26's own
                    per-episode logic for block 0 (20 episodes, filter OFF, the SAME `run26.
                    learn.json` codebook) and confirm pred_full/in_shortlist/pred_shortlist
                    match `eval_baseline.json`'s own first 20 records EXACTLY -- this is the
                    "my clone of the eval loop is faithful" check, done ONCE before trusting
                    the filter-ON numbers below. Also records `seeds/stroke_shapes.json`'s
                    md5 (parallel-session-owned per `jabberwock_plans_gap_closure.py`'s own
                    header -- this run never writes there, only reads the hash for the record).
  --stage targeted  Re-run run 36's OWN difference-element analysis
                    (`_normalize_glyph`/`_greedy_stroke_match`, reused verbatim, not
                    reimplemented) on the 5 flagged pairs above, loading strokes with
                    `drop_degenerate=True`. PRE-REGISTERED EXPECTATION: the degenerate stroke
                    no longer appears as the worst-matched/unmatched element (ink_fraction no
                    longer ~0.0) for 5/5 pairs.
  --stage eval      Full n=400, SAME protocol as run26's own "baseline" arm (byte-identical
                    POWER_SEED / block order / query order -- so episodes are PAIRWISE
                    comparable against `eval_baseline.json` by record index), but with
                    `DropDegenerateFilter` active for every stroke load (exemplar + query,
                    decode + verdict paths). Reuses run26's OWN `learn.json` codebook
                    (READ-ONLY reference -- re-LEARNing is out of scope; the codebook's own
                    growth is not what this run tests). Reports full-dwell / coverage@10 /
                    shortlist accuracy with Wilson CIs, PLUS a per-episode newly-covered/
                    newly-lost diff against `eval_baseline.json`. PRE-REGISTERED EXPECTATION
                    (stated before any number below is computed): a CI-separated gain is
                    UNLIKELY -- the artifact drove 5/30 of a 30-pair TOP-CONFUSION slice, not
                    5% of all 400 episodes -- the success shape is the 5 targeted pairs fixed
                    AND no regression elsewhere, not a moved headline number.
  --stage report    Consolidate every checkpoint into the final table.

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run37c.log`, per-block checkpoints under `results/run37c_checkpoints/`
(every OTHER run*_checkpoints dir, including run26's own `learn.json`/`eval_baseline.json`
and run36's `difference_element.json`, READ-ONLY reference -- never written here). `.venv`
python (needs `substrate_rs`).

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run37c_hygiene.py --stage verify
  ... --stage targeted
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

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run25_number as run25
import scripts.jabberwock_omniglot_run26_homework as run26
import scripts.jabberwock_omniglot_run36_failures as run36
from domains import abs_read as ar
from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run37c_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")   # READ-ONLY reference.
RUN36_DIR = os.path.join(ROOT, "results", "run36_checkpoints")   # READ-ONLY reference.
STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")   # parallel-session-
                                                                          # owned -- READ-ONLY.
os.makedirs(CKPT_DIR, exist_ok=True)

WAY = run25.WAY                                        # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET    # 20
R_TARGET = run25.R_TARGET                              # 2 -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS              # 10
POWER_SEED = run25.POWER_SEED                          # gate.SEED + 1500, byte-identical to
                                                        # run25/26/36's own eval seed.
SHORTLIST_K = run26.SHORTLIST_K                        # 10 (of 20)
DK = gate.DK
PER_CALL_BUDGET_SECONDS = 480.0                        # leaves >100s headroom under the 600s
                                                        # foreground cap; eval checkpoints per
                                                        # block.

# Cited VERBATIM from results/run26_checkpoints/eval_baseline.json -- filter OFF IS exactly
# this protocol, nothing to re-derive.
BASELINE_FULL_DWELL = dict(acc=0.805, ci=(0.7633481418022936, 0.8408493586537856), n=400, k=322)
BASELINE_COVERAGE10 = dict(cov=0.715, ci=(0.6688804833361408, 0.7570292301001117), n=400, k=286)
BASELINE_SHORTLIST_ACC = dict(acc=0.62, ci=(0.5715045437377642, 0.6662125056220046), n=400, k=248)

# The 5 degenerate-stroke-artifact pairs (results/run36_checkpoints/difference_element.json,
# the exact rows with ink_fraction == 0.0 among the top-30 most-confused pairs). Cited here,
# re-verified against the checkpoint file itself in stage_targeted (never hand-trusted alone).
TARGETED_PAIRS = [
    dict(alph="Keble", block_idx=18, r=0, true_ci=15, pred_ci=13),
    dict(alph="Kannada", block_idx=17, r=1, true_ci=15, pred_ci=8),
    dict(alph="Keble", block_idx=19, r=1, true_ci=13, pred_ci=1),
    dict(alph="Keble", block_idx=19, r=1, true_ci=8, pred_ci=15),
    dict(alph="Keble", block_idx=19, r=1, true_ci=19, pred_ci=13),
]


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


# ===============================================================================================
# THE FILTER WIRING -- patch the SHARED module attribute for the life of the `with` block, so
# every late-bound `ow.load_strokes(...)` call anywhere downstream (abs_read.stage_parse_char,
# gate.decode_char_signature, run25._stage_candidates/_raw_stroke_points) resolves through the
# filtered version. `omniglot_world.load_strokes`'s own default stays False; nothing outside
# this gate is edited.
# ===============================================================================================
class DropDegenerateFilter:
    def __enter__(self):
        self._orig_strokes = ow.load_strokes
        self._orig_strokes_t = ow.load_strokes_t

        def _ls(path, *a, **kw):
            kw["drop_degenerate"] = True
            return self._orig_strokes(path, *a, **kw)

        def _lst(path, *a, **kw):
            kw["drop_degenerate"] = True
            return self._orig_strokes_t(path, *a, **kw)

        ow.load_strokes = _ls
        ow.load_strokes_t = _lst
        return self

    def __exit__(self, *exc):
        ow.load_strokes = self._orig_strokes
        ow.load_strokes_t = self._orig_strokes_t
        return False


# ===============================================================================================
# ONE EPISODE'S worth of the run26 "baseline"-arm protocol (byte-identical logic to
# `run26.stage_eval("baseline")`'s own per-block body, reused as a function so `verify` and
# `eval` share ONE implementation rather than two hand-copied ones).
# ===============================================================================================
def _run_block(s, native, cache, alph, r, spec) -> list:
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    scratch0 = srs.Substrate()
    _, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                        thetas=ar.DEFAULT_PARSE_THETAS)
    exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, DK)
                 for ci in range(WAY)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]

    records = []
    for qi, q_drawer in spec["queries"]:
        path = drawer_files[qi][q_drawer]
        rec = {"true": qi, "alph": alph, "r": r}
        qn0 = ar.stage_parse_char(scratch0, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS)
        w0 = ar.parse_marginal_verdict(scratch0, qn0)
        rec["pred_full"] = cand0.get(w0, -1) if w0 is not None else -1

        qd = gate.decode_char_signature(s, path, cache, DK)
        shortlist = ar.propose_top_k(native, qd["composed_sig"], exemplar_composed,
                                      k=SHORTLIST_K)
        rec["in_shortlist"] = bool(qi in shortlist)
        scratch_s = srs.Substrate()
        cand_s = {}
        for ci in shortlist:
            node = ar.stage_parse_char(scratch_s, drawer_files[ci][ex_drawer],
                                        is_query=False, name=str(ci))
            cand_s[node] = ci
        qn_s = ar.stage_parse_char(scratch_s, path, is_query=True)
        w_s = ar.parse_marginal_verdict(scratch_s, qn_s)
        rec["pred_shortlist"] = cand_s.get(w_s, -1) if w_s is not None else -1
        records.append(rec)
    return records


# ===============================================================================================
# STAGE: verify -- cite the baseline, spot-check the clone-loop is faithful (filter OFF).
# ===============================================================================================
def stage_verify() -> int:
    print(f"\n{SEP}\n  STAGE: verify -- cite run26 baseline, spot-check the clone eval loop\n{SEP}")
    print(f"  CITED (results/run26_checkpoints/eval_baseline.json, filter OFF IS this protocol"
          f" -- not re-derived):")
    print(f"    full-dwell:    acc={100*BASELINE_FULL_DWELL['acc']:.1f}%  95% CI "
          f"[{100*BASELINE_FULL_DWELL['ci'][0]:.1f}%, {100*BASELINE_FULL_DWELL['ci'][1]:.1f}%]  "
          f"n={BASELINE_FULL_DWELL['n']} k={BASELINE_FULL_DWELL['k']}")
    print(f"    coverage@{SHORTLIST_K}:    cov={100*BASELINE_COVERAGE10['cov']:.1f}%  95% CI "
          f"[{100*BASELINE_COVERAGE10['ci'][0]:.1f}%, {100*BASELINE_COVERAGE10['ci'][1]:.1f}%]  "
          f"n={BASELINE_COVERAGE10['n']} k={BASELINE_COVERAGE10['k']}")
    print(f"    shortlist acc: acc={100*BASELINE_SHORTLIST_ACC['acc']:.1f}%  95% CI "
          f"[{100*BASELINE_SHORTLIST_ACC['ci'][0]:.1f}%, {100*BASELINE_SHORTLIST_ACC['ci'][1]:.1f}%]"
          f"  n={BASELINE_SHORTLIST_ACC['n']} k={BASELINE_SHORTLIST_ACC['k']}")

    md5_now = _md5(STROKE_SHAPES_PATH)
    print(f"\n  seeds/stroke_shapes.json md5 (parallel-session-owned, this run never writes "
          f"there): {md5_now}")

    print(f"\n  spot-check: block 0, filter OFF, must reproduce eval_baseline.json's own first "
          f"{WAY} records EXACTLY (pred_full / in_shortlist / pred_shortlist).")
    baseline_records = _load_json(os.path.join(RUN26_DIR, "eval_baseline.json"))["records"][:WAY]

    t0 = time.time()
    s = run26._load_graph(os.path.join(RUN26_DIR, "learn.json"))
    native = s._inner
    print(f"  learn.json loaded ({time.time()-t0:.1f}s).")

    qualifying = sorted(a for a in ow.alphabets("evaluation") if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]
    rng = np.random.default_rng(POWER_SEED)
    spec = run25._block_spec(test_alphabets[0], rng, WAY, EPISODES_PER_ALPHABET)
    cache: dict = {}
    got = _run_block(s, native, cache, test_alphabets[0], 0, spec)

    mismatches = []
    for i, (g, b) in enumerate(zip(got, baseline_records)):
        for key in ("pred_full", "in_shortlist", "pred_shortlist"):
            if g[key] != b[key]:
                mismatches.append((i, key, g[key], b[key]))
    ok = not mismatches
    print(f"  {len(got)} episodes reproduced -- {'EXACT MATCH' if ok else f'{len(mismatches)} MISMATCHES'}")
    for i, key, gv, bv in mismatches[:10]:
        print(f"    MISMATCH episode {i} {key}: got={gv} baseline={bv}")

    out = dict(baseline_full_dwell=BASELINE_FULL_DWELL, baseline_coverage10=BASELINE_COVERAGE10,
               baseline_shortlist_acc=BASELINE_SHORTLIST_ACC, stroke_shapes_md5=md5_now,
               spot_check_ok=ok, n_mismatches=len(mismatches))
    _save_json(out, _ckpt("verify.json"))
    print(f"\n  VERIFY: {'PASS' if ok else 'FAIL -- STOP, do not trust the eval stage'}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0 if ok else 1


# ===============================================================================================
# STAGE: targeted -- P3-style re-analysis of the 5 flagged pairs, filter ON at the source.
# ===============================================================================================
def stage_targeted() -> int:
    print(f"\n{SEP}\n  STAGE: targeted -- the 5 degenerate-stroke pairs, filter ON\n{SEP}")
    diff_path = os.path.join(RUN36_DIR, "difference_element.json")
    diff = _load_json(diff_path)
    zero_rows = [r for r in diff["rows"] if r["ink_fraction"] < 1e-9]
    print(f"  {len(diff['rows'])} rows in difference_element.json; "
          f"{len(zero_rows)} with ink_fraction==0.0 (the degenerate-artifact pairs).")
    if len(zero_rows) != 5:
        print(f"  WALL: expected exactly 5 zero-ink-fraction pairs (RUN 36's own cited count), "
              f"found {len(zero_rows)} -- STOP, the citation no longer matches the checkpoint.")
        return 1
    got_pairs = {(r["alph"], r["block_idx"], r["true_ci"], r["pred_ci"]) for r in zero_rows}
    want_pairs = {(p["alph"], p["block_idx"], p["true_ci"], p["pred_ci"]) for p in TARGETED_PAIRS}
    if got_pairs != want_pairs:
        print(f"  WALL: the 5 zero-ink-fraction pairs in the checkpoint do not match this "
              f"script's own cited TARGETED_PAIRS -- STOP.\n    checkpoint: {sorted(got_pairs)}"
              f"\n    cited:      {sorted(want_pairs)}")
        return 1

    blocks26_full, _ = run36._reconstruct_run26_blocks(run25, ow)
    native = srs.Substrate()._inner

    def _worst(gm):
        if gm["unmatched_true"] or gm["unmatched_pred"]:
            cands = ([("true", i, gm["t_arc"][i] / gm["t_tot"]) for i in gm["unmatched_true"]] +
                      [("pred", j, gm["p_arc"][j] / gm["p_tot"]) for j in gm["unmatched_pred"]])
            side, idx, frac = min(cands, key=lambda c: c[2])
            return "unmatched", side, frac
        i, j, c = max(gm["matched"], key=lambda m: m[2])
        return "worst_matched", "true", gm["t_arc"][i] / gm["t_tot"]

    results = []
    for row in zero_rows:
        blk = blocks26_full[row["block_idx"]]
        true_path = blk["drawer_files"][row["true_ci"]][blk["ex_drawer"]]
        pred_path = blk["drawer_files"][row["pred_ci"]][blk["ex_drawer"]]

        true_raw, pred_raw = ow.load_strokes(true_path), ow.load_strokes(pred_path)
        gm_before = run36._greedy_stroke_match(native, true_raw, pred_raw)
        wk_before, ws_before, frac_before = _worst(gm_before)

        true_f = ow.load_strokes(true_path, drop_degenerate=True)
        pred_f = ow.load_strokes(pred_path, drop_degenerate=True)
        gm_after = run36._greedy_stroke_match(native, true_f, pred_f)
        wk_after, ws_after, frac_after = _worst(gm_after)

        passed = frac_after > 1e-9
        results.append(dict(
            alph=row["alph"], block_idx=row["block_idx"], r=row["r"],
            true_ci=row["true_ci"], pred_ci=row["pred_ci"],
            n_true_before=gm_before["n_true"], n_pred_before=gm_before["n_pred"],
            n_true_after=gm_after["n_true"], n_pred_after=gm_after["n_pred"],
            worst_kind_before=wk_before, worst_kind_after=wk_after,
            ink_fraction_before=frac_before, ink_fraction_after=frac_after,
            fixed=passed))
        print(f"  {row['alph']:<10} block={row['block_idx']:>2} true_ci={row['true_ci']:>2} "
              f"pred_ci={row['pred_ci']:>2}  strokes before=({gm_before['n_true']} vs "
              f"{gm_before['n_pred']}) after=({gm_after['n_true']} vs {gm_after['n_pred']})  "
              f"ink_frac before={frac_before:.3f} after={frac_after:.3f}  "
              f"{'FIXED' if passed else 'STILL DEGENERATE'}")

    n_fixed = sum(1 for r in results if r["fixed"])
    print(f"\n  TARGETED VERDICT: {n_fixed}/{len(results)} pairs no longer degenerate-stroke-"
          f"driven (pre-registered expectation: 5/5).")
    _save_json(dict(rows=results, n_fixed=n_fixed, n_total=len(results)),
               _ckpt("targeted_verdict.json"))
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: eval -- full n=400, filter ON everywhere strokes load.
# ===============================================================================================
def stage_eval() -> int:
    print(f"\n{SEP}\n  STAGE: eval -- n=400, filter ON (exemplar+query, decode+verdict paths)\n{SEP}")
    out_path = _ckpt("eval_filtered.json")
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

    qualifying = sorted(a for a in ow.alphabets("evaluation") if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  test_alphabets={test_alphabets}")
    print(f"  blocks={len(blocks)} (target n={len(blocks)*WAY})  SHORTLIST_K={SHORTLIST_K}  "
          f"resuming at block {state['block_idx']}")

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
            recs = _run_block(s, native, cache, alph, r, spec)
            state["records"].extend(recs)
            state["block_idx"] += 1
            _save_json(state, out_path)
            print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
                  f"{len(state['records'])} episodes so far, {time.time()-t_loop0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        run26._finalize_eval(state)
        _save_json(state, out_path)
        print(f"\n  EVAL COMPLETE: n={len(state['records'])}")
        fd, cov, sl = state["full_dwell"], state["coverage"], state["shortlist_acc"]
        print(f"    full-dwell (filter ON):   acc={100*fd['acc']:.1f}%  95% CI "
              f"[{100*fd['ci'][0]:.1f}%, {100*fd['ci'][1]:.1f}%]  n={fd['n']} k={fd['k']}")
        print(f"    coverage@{SHORTLIST_K} (filter ON): cov={100*cov['cov']:.1f}%  95% CI "
              f"[{100*cov['ci'][0]:.1f}%, {100*cov['ci'][1]:.1f}%]  n={cov['n']} k={cov['k']}")
        print(f"    shortlist acc (filter ON): acc={100*sl['acc']:.1f}%  95% CI "
              f"[{100*sl['ci'][0]:.1f}%, {100*sl['ci'][1]:.1f}%]  n={sl['n']} k={sl['k']}")
        for name, filt, base in (("full-dwell", fd, BASELINE_FULL_DWELL),
                                  ("coverage", cov, BASELINE_COVERAGE10),
                                  ("shortlist", sl, BASELINE_SHORTLIST_ACC)):
            sep = gate._ci_separated(tuple(filt["ci"]), tuple(base["ci"]))
            print(f"    {name}: CI-separated from baseline = {sep}"
                  f"{'  (unexpected -- investigate)' if sep else '  (expected null)'}")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- "
              f"re-run '--stage eval' to continue.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: report -- final table + newly-covered/newly-lost episode diff vs eval_baseline.json.
# ===============================================================================================
def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 37C -- INGEST HYGIENE -- FINAL REPORT\n{SEP}")
    for name in ("verify", "targeted_verdict", "eval_filtered"):
        p = _ckpt(f"{name}.json")
        print(f"  {name}.json: {'present' if os.path.exists(p) else 'MISSING'}")

    tv_path = _ckpt("targeted_verdict.json")
    if os.path.exists(tv_path):
        tv = _load_json(tv_path)
        print(f"\n  TARGETED (Gap C's own 5 flagged pairs): {tv['n_fixed']}/{tv['n_total']} "
              f"no longer degenerate-stroke-driven.")

    ev_path = _ckpt("eval_filtered.json")
    if not os.path.exists(ev_path) or not _load_json(ev_path).get("done"):
        print("\n  eval not yet COMPLETE -- report is partial (targeted-only).")
        print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
        return 0

    ev = _load_json(ev_path)
    fd, cov, sl = ev["full_dwell"], ev["coverage"], ev["shortlist_acc"]
    print(f"\n  n=400 TABLE (filter ON vs cited baseline, filter OFF):")
    print(f"    {'metric':<14} {'baseline':>22}   {'filter ON':>22}   CI-separated")
    def _fmt(d, acc_key):
        return f"{100*d[acc_key]:5.1f}% [{100*d['ci'][0]:5.1f},{100*d['ci'][1]:5.1f}]"
    rows = [("full-dwell", BASELINE_FULL_DWELL, fd, "acc"),
            ("coverage@10", BASELINE_COVERAGE10, cov, "cov"),
            ("shortlist", BASELINE_SHORTLIST_ACC, sl, "acc")]
    for label, base, filt, key in rows:
        sep = gate._ci_separated(tuple(filt["ci"]), tuple(base["ci"]))
        print(f"    {label:<14} {_fmt(base, key):>22}   {_fmt(filt, key):>22}   {sep}")

    baseline_records = _load_json(os.path.join(RUN26_DIR, "eval_baseline.json"))["records"]
    filt_records = ev["records"]
    assert len(baseline_records) == len(filt_records) == 400, (
        "episode count mismatch -- the two chains are not directly comparable")

    def _diff(key, pass_test):
        newly_covered, newly_lost = [], []
        for i, (b, f) in enumerate(zip(baseline_records, filt_records)):
            b_pass, f_pass = pass_test(b), pass_test(f)
            if not b_pass and f_pass:
                newly_covered.append(i)
            elif b_pass and not f_pass:
                newly_lost.append(i)
        return newly_covered, newly_lost

    nc_fd, nl_fd = _diff("full", lambda r: r["pred_full"] == r["true"])
    nc_cov, nl_cov = _diff("cov", lambda r: r["in_shortlist"])
    nc_sl, nl_sl = _diff("sl", lambda r: r["pred_shortlist"] == r["true"])

    print(f"\n  PER-EPISODE DIFF (paired by record index -- byte-identical POWER_SEED/block/"
          f"query order between chains):")
    print(f"    full-dwell:  newly-covered={len(nc_fd)}  newly-lost={len(nl_fd)}"
          f"  (indices covered={nc_fd[:20]}  lost={nl_fd[:20]})")
    print(f"    coverage@10: newly-covered={len(nc_cov)}  newly-lost={len(nl_cov)}"
          f"  (indices covered={nc_cov[:20]}  lost={nl_cov[:20]})")
    print(f"    shortlist:   newly-covered={len(nc_sl)}  newly-lost={len(nl_sl)}"
          f"  (indices covered={nc_sl[:20]}  lost={nl_sl[:20]})")

    print(f"\n  PRE-REGISTERED SUCCESS SHAPE: the 5 targeted pairs fixed (see TARGETED above) "
          f"AND no regression (newly-lost should not exceed newly-covered by a meaningful "
          f"margin) -- a CI-separated headline gain was explicitly flagged as UNLIKELY "
          f"(5/30 of a top-confusion SLICE, not 5% of all 400 episodes).")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


STAGES = {
    "verify": stage_verify,
    "targeted": stage_targeted,
    "eval": stage_eval,
    "report": stage_report,
}


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
