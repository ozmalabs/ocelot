"""jabberwock_handtransform_run80.py -- RUN 80: THE RICHER HAND-TRANSFORM.

RUN 79 was DECISIVE on two fronts, on the SAME held-out-writer letter corpus: (i) pure per-class
exemplar ACCUMULATION cannot generalize across letter classes -- analytically proven
(flip_to_right=0 at every K) and measured (UNSEEN accuracy never rises above cold, -6.1pp
dilution at K=13); (ii) a POSE TRANSFORM (baseline/x-height/slant, estimated from a writer's ink
with ZERO per-letter labels) delivers a real, K-independent lift across EVERY class: run 69's own
condition A (no adaptation) 15.0% -> condition D (pose-transform ALONE, generic cross bank) 34.7%
(+19.7pp) -> condition E (pose + full own-writer bank, within-writer) 55.0%. The 34.7->55 gap is
the open question run 79 named but did not answer: is it SHARED STYLE (a richer, still-general
hand-transform beyond pose's global-affine slice -- would generalize to unseen letters, like pose
does) or per-letter IDIOSYNCRASY (would not)?

THE HYPOTHESIS (pre-registered, stated before any RUN 80 number is computed): a writer's hand is a
TRANSFORM of canonical letterforms; pose (global affine: baseline, x-height scale, slant shear) is
only its CRUDEST slice. The RICHER transform is the writer's SHARED ALLOGRAPH STYLE beyond affine
-- roundedness/curvature, stroke-proportion, aspect, loop-size -- expressed as a per-landmark
(arc-length-position-indexed, CLASS-INDEPENDENT) residual displacement field, estimated from a
FEW labeled letters and pooled the same "systematic bias survives averaging, idiosyncratic noise
does not" way `domains/episode_style.py` (RUN 42) and `seeds/writer_dimensions.json`'s
`wd_infer_writer` rule both already use elsewhere in this arc, just at LANDMARK resolution
instead of a single scalar moment (shear/aspect) or a single discrete pose delta.

THE MECHANISM (closed-form throughout, donkey=0 -- no trained style-transfer net anywhere):
  1. CANONICAL TEMPLATE per class (`build_canonical_templates`): the per-landmark MEDIAN
     population-frame `pose_canon` (run 69's own writer-relative-pose primitive, reused verbatim,
     with x_height/slant fixed to run 69's own `population_frame` and baseline always LOCAL per
     instance -- run 69's own established convention) over EVERY background-writer lowercase
     glyph instance of that class (not run 69's own capped M_BANK=3-exemplar bank -- a materially
     larger, more robust pool, since a stable canonical prototype is exactly what a median over
     many instances is for). This is what pose-only (condition D) implicitly compares a query
     AGAINST via the generic cross bank's own per-exemplar pose canons; here it is condensed to a
     single robust prototype per class instead of a bank of individual exemplars.
  2. PER-LETTER DEFORMATION, given K ground-truth-labeled letters of a held-out writer (run 79's
     own `draw_kshot`/`build_writer_words`, reused verbatim -- K is a count of LABELED WORDS, same
     convention as runs 78/79, not individual letters; a word contributes several labeled letters
     at once): for each labeled letter, its `pose_own` canon (already writer-relative-pose-
     normalized under THAT writer's own frame, run 69's own field, already present in run 78's own
     letter records) MINUS its class's canonical template is the per-landmark RESIDUAL -- the
     non-affine deformation pose does not explain, in a frame where translation/scale/slant are
     already factored out.
  3. THE SHARED STYLE EXTRACTION (`extract_style_field`): the per-landmark MEAN residual, pooled
     across every labeled letter regardless of class (landmark index i means "i/N of the way along
     this glyph's own arc length" for EVERY letter, by construction of the shared CANON_N
     arc-length resample -- the SAME index-correspondence convention runs 66-79's `inv`/`pose_own`
     canons already rely on for DTW). A CONSISTENCY diagnostic accompanies every estimate:
     `explained_ratio` = ||mean residual||^2 / mean_k(||residual_k||^2), which is 1.0 if every
     labeled letter pushes each landmark in exactly the same direction (a real, shared,
     class-independent style) and falls to its `null_ratio` = 1/K under pure per-letter
     idiosyncratic noise (the standard variance-of-the-mean argument) -- checked BOTH on a
     positive synthetic control (consistent offset -> ratio landing at 1.0) and a negative one
     (independent random noise -> ratio landing near 1/K) in `tests/test_run80_migrated.py` BEFORE
     any real-corpus number is trusted.
  4. APPLY TO UNSEEN (`styled_template`): canonical_template[c] + the shared field, for ANY class
     c -- including classes that never appeared among the K labeled letters. This is the
     generalization claim made mechanical: the field is indexed by LANDMARK POSITION, never by
     letter identity, so it transfers to an unseen class's template exactly the way pose transfers
     (pose is estimated from a writer's overall ink and applied to every class uniformly; this
     field is estimated from K labeled letters and applied to every class -- including ones never
     labeled -- the same way).

THE 3 ARMS (measured on UNSEEN letters -- classes ABSENT from a draw's K labeled words -- as a
function of K, on run 78/79's OWN held-out-writer letter corpus, so the within-run A/B/C
comparison is apples-to-apples and CI-comparable; run 69's own condition A/D/E numbers are cited
alongside, live-recomputed via `r79.run69_pose_decomposition_anchor`, as the external, corpus-
level context the task's pre-registered ~15/34.7/55 figures refer to -- NOT re-derived as
numerically-identical targets, since they come from a different corpus draw, exactly run 79's own
citation discipline):
  A  cold       = invariant-channel-only cost (`invA_only`, NEW light native precompute, `_class_
                  cost` against run 77's own `cross_charbank` = run 69's own `cross_bank`) argmin
                  -- no pose, no style, the true no-adaptation floor on THIS corpus.
  B  pose-only  = run 78/79's own `cross_row` field UNCHANGED (= invA + PRIMARY_LAMBDA_POSE *
                  pose-in-writer's-own-frame-vs-cross-bank, i.e. condition D's own formula,
                  ALREADY CACHED, zero new compute) argmin -- pose transform alone, zero per-letter
                  labels, exactly run 69's condition D mechanism applied to this corpus.
  C  pose+style = invA_only[c] + PRIMARY_LAMBDA_POSE * DTW(query pose_own, styled_template(c))
                  for EVERY class c (never touches the K letters' own per-class exemplar pool --
                  isolates the TRANSFORM's own generalizing power from the already-refuted
                  accumulation mechanism, the same isolation condition D itself uses against
                  condition E's bank) argmin -- THIS run's contribution.
  ceiling (scale only, not an arm) = run 69's own condition E (pose + full own-writer bank,
                  within-writer), cited live, reachable only for SEEN classes with a real bank --
                  shown for scale, never used as a bar any arm here is expected to meet.

PRE-REGISTERED READ (stated before any number is computed):
  WIN if arm C's UNSEEN accuracy sits materially above arm B's (stated bar: > 42.0%, roughly
  midway from pose-only 34.7% toward ceiling 55%) AND is Wilson-CI-separated above arm B, AND the
  style field's `explained_ratio` is materially above its own `null_ratio` (real, consistent
  signal, not an averaging-noise artifact) -- fast adaptation SOLVED: a few labeled letters infer
  the writer's hand well enough to read letters that writer never labeled at all.
  NULL if arm C does not lift materially above arm B (regardless of the consistency number, since a
  real-but-non-discriminative style component is possible, and is reported as such) -- the
  remaining 34.7->55 gap is per-letter IDIOSYNCRASY, not a further generalizing transform; pose
  is ~the transform ceiling, and closing the rest of the gap needs per-class coverage (harvest),
  not a richer transform.

SEED GUARD / DISCIPLINE: `OZMA_SEED_PERSIST_DISABLED=1`; md5(seeds/stroke_shapes.json) asserted
UNCHANGED before AND after every stage. donkey=0 throughout (median pooling + a per-landmark mean
residual field + the SAME held DTW comparator runs 66-79 use for their own decode -- no SGD-
trained net, no learned weights, no style-transfer net of any kind). `results/run6{9}_checkpoints/`
and `results/run7{7,8,9}_checkpoints/` are READ-ONLY (citation/reused-module/reused-checkpoint
only) -- this script writes ONLY `results/run80_checkpoints/*`. NO git add/commit.

EXECUTION (ops law): every invocation <=540s FOREGROUND, checkpointed under
`results/run80_checkpoints/`, block-resumable. `.venv` python needed for `read` (light native
DTW precompute of the invariant-only channel, cross_charbank already exists, reused verbatim) and
`bootstrap` (the K-shot sweep's own new native DTW calls, query pose_own vs each class's styled
template -- a SINGLE template per class, not a bank, so materially CHEAPER per query than any
prior run's bank-based decode); `prep` is pure numpy (canonical-template median pooling +
structural validation) and runs under either interpreter. NEVER run in background; NEVER end a
turn with a live process.

Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 \\
    scripts/jabberwock_handtransform_run80.py --stage <prep|read|bootstrap|summary>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import scripts.jabberwock_fewshot_run79 as r79
import scripts.jabberwock_cursive_curriculum_run66 as cc66

r78 = r79.r78
r77 = r79.r77
r73 = r79.r73
r69 = r79.r69

SEP = "=" * 92
STROKE_SHAPES_SEED = r79.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run80_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run80.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN78_CKPT_DIR = r78.CKPT_DIR                                          # READ-ONLY.
RUN77_CKPT_DIR = r78.RUN77_CKPT_DIR                                    # READ-ONLY.
RUN69_CKPT_DIR = os.path.join(ROOT, "results", "run69_checkpoints")    # READ-ONLY.
RUN78_PREP = os.path.join(RUN78_CKPT_DIR, "prep.json")
RUN78_READ = os.path.join(RUN78_CKPT_DIR, "read.json")
RUN77_PREP = os.path.join(RUN77_CKPT_DIR, "prep.json")
RUN69_PREP = os.path.join(RUN69_CKPT_DIR, "prep.json")

CANON_N = r69.CANON_N                          # 24 -- arc-length-resampled landmark count.
LOWER_CLASSES = r69.LOWER_CLASSES              # 10..35, canonical class ids for 'a'..'z'.
SYMBOLS = r69.SYMBOLS

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS -- reused verbatim from the arc's own shared weights where one
#  exists; NEW constants for this run's own richer-transform sweep are marked NEW.
# ------------------------------------------------------------------------------------------- #
PRIMARY_LAMBDA_POSE = r78.PRIMARY_LAMBDA_POSE      # 1.0, r69's own pre-registered pose weight.
K_VALUES = r79.K_VALUES                            # [1,2,3,5,8,13,20] -- SAME grid as run 79.
N_KSHOT_SEEDS = r79.N_KSHOT_SEEDS                  # 5 -- same draw-order averaging convention.
MIN_BG_COVERAGE = 5                                # NEW -- min bg instances to trust a template.
PER_CALL_BUDGET_SECONDS = 480.0

BAR_UNSEEN_C = 42.0                                # NEW -- pre-registered WIN bar (task's own bar).

# Calibration numbers this run reports against (dynamically recomputed live -- see
# `r79.run69_pose_decomposition_anchor` -- these are FALLBACK citations only).
COLD_CITE = 15.0
POSE_ONLY_CITE = 34.7
CEILING_CITE = 55.0


# ============================================================================================= #
#  I/O + seed guard (identical pattern to the whole arc).
# ============================================================================================= #
def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _save(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f)


def _load(path):
    with open(path) as f:
        return json.load(f)


def _require(name):
    p = _ckpt(name)
    if not os.path.exists(p):
        raise SystemExit(f"WALL: run the stage that produces {name} first.")
    return _load(p)


def _seed_guard(stage, before=None):
    cur = _md5(STROKE_SHAPES_SEED)
    if before is not None and cur != before:
        raise SystemExit(f"HARD STOP: seeds/stroke_shapes.json md5 changed during {stage} "
                          f"({before} -> {cur}).")
    return cur


def _wilson(k, n):
    return r79._wilson(k, n)


# ============================================================================================= #
#  CANONICAL TEMPLATES -- pure numpy, closed-form median pooling, NO native calls (donkey=0).
#  Reuses run 69's OWN pose_canon/local_frame_of/_group_by_writer/_index_by_writer_sample
#  primitives verbatim, on a materially LARGER background pool than run 69's own capped
#  M_BANK=3-exemplar cross_bank (a stable per-class prototype wants many instances, not a few).
# ============================================================================================= #
def build_canonical_templates(prep69: dict, dw=None, all_glyphs=None) -> dict:
    if dw is None:
        dw = r69.dww.load_deepwriting(r69.SPLIT)
    if all_glyphs is None:
        all_glyphs = r69.dww.extract_char_glyphs(dw)
    by_writer = r69._group_by_writer(all_glyphs)
    ws_index = r69._index_by_writer_sample(all_glyphs)
    bg_writers = set(prep69["bg_writers"])
    pop = prep69["population_frame"]

    per_class_points = defaultdict(list)
    for w in bg_writers:
        for g in by_writer.get(w, []):
            if g["class"] not in LOWER_CLASSES:
                continue
            baseline, _topline = r69.local_frame_of(g, ws_index)
            canon = r69.pose_canon(g["strokes"], baseline, pop["x_height"], pop["slant_deg"],
                                   CANON_N)
            per_class_points[g["class"]].append(np.asarray(canon, dtype=float))

    templates, coverage = {}, {}
    for c in LOWER_CLASSES:
        li = c - 10
        pts = per_class_points.get(c, [])
        coverage[str(li)] = len(pts)
        if len(pts) < MIN_BG_COVERAGE:
            templates[str(li)] = None
            continue
        arr = np.stack(pts, axis=0)                       # (n_inst, CANON_N, 2)
        templates[str(li)] = np.median(arr, axis=0).tolist()
    return {"templates": templates, "coverage": coverage, "n_bg_writers": len(bg_writers)}


# ============================================================================================= #
#  THE RICHER TRANSFORM -- pure Python/numpy, native-free (dependency-injected distance/DTW).
#  Importable and fully unit-testable without substrate_rs (see tests/test_run80_migrated.py).
# ============================================================================================= #
def extract_style_field(pool_letters: list, canonical_templates: dict) -> dict:
    """The per-landmark MEAN residual (`pose_own` actual minus the class's canonical template),
    pooled across every labeled letter regardless of class -- the SHARED, class-independent style
    field. `explained_ratio` = ||mean residual||^2 / mean_k(||residual_k||^2): 1.0 for a perfectly
    consistent (every letter pushes each landmark the same way) style, -> its own `null_ratio` =
    1/n under pure per-letter idiosyncratic noise (no shared component at all)."""
    residuals = []
    for l in pool_letters:
        tmpl = canonical_templates.get(str(l["true_li"]))
        if tmpl is None:
            continue
        residuals.append(np.asarray(l["pose_own"], dtype=float) - np.asarray(tmpl, dtype=float))
    n = len(residuals)
    if n == 0:
        return {"field": None, "n": 0, "explained_ratio": None, "null_ratio": None}
    stack = np.stack(residuals, axis=0)                   # (n, CANON_N, 2)
    field = stack.mean(axis=0)
    if n < 2:
        return {"field": field.tolist(), "n": n, "explained_ratio": None, "null_ratio": None}
    numerator = float(np.sum(field ** 2))
    denom = float(np.mean(np.sum(stack ** 2, axis=(1, 2))))
    explained_ratio = numerator / denom if denom > 1e-12 else None
    return {"field": field.tolist(), "n": n, "explained_ratio": explained_ratio,
           "null_ratio": 1.0 / n}


def styled_template(canonical_templates: dict, li: int, field) -> list | None:
    """canonical_template[li] + the shared style field -- APPLICABLE TO ANY CLASS, including one
    that never appeared among the K labeled letters (the field is landmark-indexed, not
    class-indexed) -- the generalization mechanism made concrete."""
    tmpl = canonical_templates.get(str(li))
    if tmpl is None or field is None:
        return None
    return (np.asarray(tmpl, dtype=float) + np.asarray(field, dtype=float)).tolist()


def class_cost_with_style(cost_fn, query_pose_own, canonical_templates: dict, field,
                          invA_row: list, lam: float = PRIMARY_LAMBDA_POSE) -> list:
    """The 26-class ARM C cost vector: invA (unchanged, real cross-bank invariant-channel cost) +
    lam * DTW(query pose_own, styled_template(c)) for every class c, computed against ONE
    prototype per class (never the writer's own accumulated pool -- isolates the transform's own
    generalizing power, same isolation condition D uses against condition E's bank). Degrades to
    invA-only (never crashes) when no style estimate is available for this draw."""
    out = list(invA_row)
    if field is None:
        return out
    for c in range(26):
        templ = styled_template(canonical_templates, c, field)
        if templ is None:
            continue
        out[c] = out[c] + lam * cost_fn(query_pose_own, templ)
    return out


def evaluate_richer_transform_one_k(writer_words: dict, canonical_templates: dict,
                                    invA_only: dict, cost_fn, k: int, n_seeds: int,
                                    lam: float = PRIMARY_LAMBDA_POSE) -> dict:
    """THE CORE SWEEP STEP: for K, draws `n_seeds` independent K-word samples per qualifying writer
    (run 79's own `draw_kshot`/`qualifying_writers`, reused verbatim), estimates the shared style
    field from the K words' letters, and measures arm A (invA-only)/B (cached pose-only cross_row)
    /C (pose+style) argmin accuracy on every HELD letter whose TRUE class is UNSEEN (absent from
    the K words) -- SEEN held letters are skipped entirely (out of scope for this run's own
    headline; arm C never touches per-class accumulation, so a seen/unseen split for arm C itself
    is not meaningful the way it was for run 79's accumulation-only mechanism)."""
    qualifying = r79.qualifying_writers(writer_words, k)
    agg = {
        "k": k, "n_qualifying_writers": len(qualifying), "unseen_n": 0,
        "arm_a_ok": 0, "arm_b_ok": 0, "arm_c_ok": 0, "n_draws": 0,
        "explained_ratios": [], "null_ratios": [], "n_residuals_list": [],
    }
    for seed in range(n_seeds):
        for w in qualifying:
            words_w = writer_words[w]
            chosen, held = r79.draw_kshot(words_w, k, seed, w)
            pool_letters = [l for wid in chosen for l in words_w[wid]]
            seen_classes = {l["true_li"] for l in pool_letters}
            style = extract_style_field(pool_letters, canonical_templates)
            agg["n_draws"] += 1
            agg["n_residuals_list"].append(style["n"])
            if style["explained_ratio"] is not None:
                agg["explained_ratios"].append(style["explained_ratio"])
                agg["null_ratios"].append(style["null_ratio"])
            for wid in held:
                for l in words_w[wid]:
                    if l["true_li"] in seen_classes:
                        continue
                    agg["unseen_n"] += 1
                    a_row = invA_only[str(l["lid"])]
                    agg["arm_a_ok"] += int(int(np.argmin(a_row)) == l["true_li"])
                    agg["arm_b_ok"] += int(int(np.argmin(l["cross_row"])) == l["true_li"])
                    c_row = class_cost_with_style(cost_fn, l["pose_own"], canonical_templates,
                                                  style["field"], a_row, lam)
                    agg["arm_c_ok"] += int(int(np.argmin(c_row)) == l["true_li"])
    return agg


# ============================================================================================= #
#  STAGE: prep -- canonical templates (pure numpy, one-time dataset load) + structural summary.
# ============================================================================================= #
def build_prep() -> dict:
    if not os.path.exists(RUN78_PREP) or not os.path.exists(RUN78_READ):
        raise SystemExit("WALL: run 78's prep.json/read.json not found -- run 78 must have "
                          "completed its own prep+read stages first (read-only dependency).")
    if not os.path.exists(RUN69_PREP):
        raise SystemExit("WALL: run 69's prep.json not found (needed for bg_writers + "
                          "population_frame, read-only dependency).")
    r78_read = _load(RUN78_READ)
    if not r78_read.get("done"):
        raise SystemExit("WALL: run 78's read.json is not COMPLETE.")

    p78 = _load(RUN78_PREP)
    letters = p78["letters"]
    prep69 = _load(RUN69_PREP)
    templ_out = build_canonical_templates(prep69)

    writer_words = r79.build_writer_words(letters)
    k_writer_counts = {str(k): len(r79.qualifying_writers(writer_words, k)) for k in K_VALUES}

    return {
        "canonical_templates": templ_out["templates"],
        "template_coverage": templ_out["coverage"],
        "n_bg_writers": templ_out["n_bg_writers"],
        "n_letters": len(letters), "n_writers": len(writer_words),
        "k_values": K_VALUES, "k_writer_counts": k_writer_counts,
        "run78_n_test_letters": p78["n_test_letters"],
    }


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep -- canonical templates (median pose-canon pooling over ALL "
          f"background instances, pure numpy) + structural validation\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    out = build_prep()
    out["stroke_shapes_md5"] = md5_before
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)

    cov = out["template_coverage"]
    n_covered = sum(1 for v in out["canonical_templates"].values() if v is not None)
    print(f"  background writers = {out['n_bg_writers']}  test letters = {out['n_letters']} "
          f"(borrowed from run 78's own {out['run78_n_test_letters']})", flush=True)
    print(f"  canonical templates: {n_covered}/26 classes covered (>= {MIN_BG_COVERAGE} bg "
          f"instances)", flush=True)
    cov_vals = sorted(cov.values())
    print(f"  bg instances/class: min={cov_vals[0]} median={cov_vals[len(cov_vals)//2]} "
          f"max={cov_vals[-1]}", flush=True)
    for k in K_VALUES:
        print(f"    K={k:>3}: {out['k_writer_counts'][str(k)]}/{out['n_writers']} writers qualify",
              flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read -- THE ONLY NEW NATIVE PRECOMPUTE. Invariant-channel-only cost (arm A) for every
#  test letter, against run 77's own cross_charbank (= run 69's own cross_bank), cached ONCE
#  (K-independent -- reused by every draw in bootstrap without recomputation).
# ============================================================================================= #
def stage_read():
    print(f"\n{SEP}\n  STAGE: read -- native invA-only precompute (arm A, cold/no-pose channel) "
          f"for every test letter\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    _require("prep.json")
    p78 = _load(RUN78_PREP)
    letters = p78["letters"]
    run77_prep = _load(RUN77_PREP)
    cross_charbank = run77_prep["cross_charbank"]

    out_path = _ckpt("read.json")
    state = _load(out_path) if os.path.exists(out_path) else {"invA_only": {}, "done": False}
    if state.get("done"):
        print(f"  read already COMPLETE ({len(state['invA_only'])} letters).", flush=True)
        return 0

    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    for l in letters:
        key = str(l["lid"])
        if key in state["invA_only"]:
            continue
        state["invA_only"][key] = r69._class_cost(native, l["inv"], cross_charbank, "inv")
        n_new += 1
        if n_new % 200 == 0:
            _save(state, out_path)
            _seed_guard("read", md5_before)
            print(f"    ... {len(state['invA_only'])}/{len(letters)}  [{time.time()-t0:.1f}s]",
                  flush=True)
            if time.time() > deadline:
                print(f"  WALL-BUDGET -- re-invoke --stage read to resume.", flush=True)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  read COMPLETE: {len(state['invA_only'])} letters  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: bootstrap -- THE K-SHOT SWEEP (native DTW: query pose_own vs each class's ONE styled
#  template -- cheap, a single prototype per class, not a bank).
# ============================================================================================= #
def stage_bootstrap():
    print(f"\n{SEP}\n  STAGE: bootstrap -- K-shot richer-transform sweep (arm A/B/C on UNSEEN "
          f"letters) + style consistency\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("bootstrap")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    cost_fn = lambda a, b: cc66.dtw(native, a, b)

    prep = _require("prep.json")
    rd = _require("read.json")
    if not rd.get("done"):
        raise SystemExit("WALL: read not COMPLETE -- re-invoke --stage read.")

    canonical_templates = prep["canonical_templates"]
    invA_only = rd["invA_only"]
    p78 = _load(RUN78_PREP)
    letters = p78["letters"]
    writer_words = r79.build_writer_words(letters)
    print(f"  letters={len(letters)}  writers={len(writer_words)}  "
          f"templates covered={sum(1 for v in canonical_templates.values() if v is not None)}/26  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    out_path = _ckpt("bootstrap.json")
    state = _load(out_path) if os.path.exists(out_path) else {"per_k": {}, "done_k": []}
    done_k = set(state["done_k"])
    deadline = time.time() + PER_CALL_BUDGET_SECONDS

    for k in K_VALUES:
        if k in done_k:
            print(f"  K={k} already done (cached).", flush=True)
            continue
        agg = evaluate_richer_transform_one_k(writer_words, canonical_templates, invA_only,
                                              cost_fn, k, N_KSHOT_SEEDS)
        state["per_k"][str(k)] = agg
        done_k.add(k)
        state["done_k"] = sorted(done_k)
        _save(state, out_path)
        _seed_guard("bootstrap", md5_before)
        a_pct = 100 * agg["arm_a_ok"] / agg["unseen_n"] if agg["unseen_n"] else float("nan")
        b_pct = 100 * agg["arm_b_ok"] / agg["unseen_n"] if agg["unseen_n"] else float("nan")
        c_pct = 100 * agg["arm_c_ok"] / agg["unseen_n"] if agg["unseen_n"] else float("nan")
        mean_er = float(np.mean(agg["explained_ratios"])) if agg["explained_ratios"] else float("nan")
        mean_null = float(np.mean(agg["null_ratios"])) if agg["null_ratios"] else float("nan")
        print(f"    K={k:>3}  writers={agg['n_qualifying_writers']:>3}  unseen_n={agg['unseen_n']:>6}"
              f"  A={a_pct:6.1f}%  B={b_pct:6.1f}%  C={c_pct:6.1f}%  "
              f"explained_ratio={mean_er:.3f} (null={mean_null:.3f})  [{time.time()-t0:.1f}s]",
              flush=True)
        if time.time() > deadline:
            print(f"  WALL-BUDGET: {len(done_k)}/{len(K_VALUES)} K values done -- re-invoke "
                  f"--stage bootstrap to resume.", flush=True)
            return 2

    # -- corpus-level context anchor: run 69's own condA/condD/condE, recomputed live. --
    anchor = r79.run69_pose_decomposition_anchor()
    state["pose_anchor"] = anchor
    _save(state, out_path)
    _seed_guard("bootstrap", md5_before)
    print(f"\n  run69 live anchor (external corpus, context only): condA={anchor['condA_no_pose_cross_pct']:.1f}%"
          f"  condD={anchor['condD_pose_only_cross_pct']:.1f}%  "
          f"condE={anchor['condE_pose_plus_bank_within_pct']:.1f}%", flush=True)
    print(f"\n  saved -> {out_path}  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: summary -- THE UNSEEN-letter accuracy table, consistency number, WIN/NULL verdict.
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 80 SCOREBOARD (THE RICHER HAND-TRANSFORM)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: {md5_now == prep['stroke_shapes_md5']})")
    boot = _require("bootstrap.json")
    if len(boot.get("done_k", [])) < len(K_VALUES):
        print(f"  WALL: bootstrap not COMPLETE ({len(boot.get('done_k', []))}/{len(K_VALUES)} K "
              f"values) -- re-invoke --stage bootstrap.")
        return 1

    anchor = boot.get("pose_anchor") or r79.run69_pose_decomposition_anchor()
    print(f"\n  CALIBRATION (run 69's own condition A/D/E, live, external corpus -- context, not a "
          f"numerically-identical target; task's own citations: cold~{COLD_CITE:.1f}%, "
          f"pose-only~{POSE_ONLY_CITE:.1f}%, ceiling~{CEILING_CITE:.1f}%):")
    print(f"    condA (no adaptation at all)             = {anchor['condA_no_pose_cross_pct']:.1f}%")
    print(f"    condD (pose-transform ONLY, zero labels) = {anchor['condD_pose_only_cross_pct']:.1f}%")
    print(f"    condE (pose + full own bank, within)     = {anchor['condE_pose_plus_bank_within_pct']:.1f}%"
          f"  (ceiling, scale only -- only reachable for SEEN classes with a real bank)")

    print(f"\n  === THE UNSEEN-LETTER ACCURACY TABLE (THIS run's own corpus, apples-to-apples "
          f"A/B/C) ===")
    hdr = (f"  {'K':>4}{'writers':>9}{'unseen_n':>10}{'A_cold':>9}{'B_pose':>9}{'C_pose+style':>13}"
          f"{'C_CI':>18}{'explained_r':>13}{'null_r':>9}{'avg_labels':>11}")
    print(hdr)
    rows = []
    for k in K_VALUES:
        agg = boot["per_k"][str(k)]
        n = agg["unseen_n"]
        a_pct = 100 * agg["arm_a_ok"] / n if n else float("nan")
        b_pct = 100 * agg["arm_b_ok"] / n if n else float("nan")
        c_pct = 100 * agg["arm_c_ok"] / n if n else float("nan")
        c_ci = _wilson(agg["arm_c_ok"], n) if n else (float("nan"),) * 2
        b_ci = _wilson(agg["arm_b_ok"], n) if n else (float("nan"),) * 2
        mean_er = float(np.mean(agg["explained_ratios"])) if agg["explained_ratios"] else float("nan")
        mean_null = float(np.mean(agg["null_ratios"])) if agg["null_ratios"] else float("nan")
        avg_labels = float(np.mean(agg["n_residuals_list"])) if agg["n_residuals_list"] else float("nan")
        rows.append({"k": k, "n": n, "a_pct": a_pct, "b_pct": b_pct, "c_pct": c_pct,
                    "c_ci": c_ci, "b_ci": b_ci, "mean_er": mean_er, "mean_null": mean_null,
                    "avg_labels": avg_labels})
        print(f"  {k:>4}{agg['n_qualifying_writers']:>9}{n:>10}{a_pct:>8.1f}%{b_pct:>8.1f}%"
              f"{c_pct:>12.1f}%   [{100*c_ci[0]:>5.1f},{100*c_ci[1]:>5.1f}]{mean_er:>13.3f}"
              f"{mean_null:>9.3f}{avg_labels:>11.1f}")
    print(f"  {'ceil':>4}{'--':>9}{'--':>10}{'--':>9}{'--':>9}"
          f"{anchor['condE_pose_plus_bank_within_pct']:>11.1f}%  (scale only, SEEN-only, "
          f"different corpus)")

    print(f"\n  === STYLE CONSISTENCY (is the shared field real signal or averaging noise?) ===")
    for r in rows:
        if np.isnan(r["mean_er"]):
            continue
        ratio_to_null = r["mean_er"] / r["mean_null"] if r["mean_null"] > 1e-12 else float("nan")
        print(f"    K={r['k']:>3}  explained_ratio={r['mean_er']:.3f}  null_ratio={r['mean_null']:.3f}"
              f"  ratio_to_null={ratio_to_null:.2f}x  (>>1x = real shared style; ~=1x = averaging "
              f"noise)")

    print(f"\n  === THE VERDICT: does a richer hand-transform generalize to UNSEEN letters? ===")
    print(f"  pre-registered bar: arm C UNSEEN accuracy > {BAR_UNSEEN_C:.1f}% AND Wilson-CI-"
          f"separated above arm B (pose-only) at that K.")
    win_ks = []
    for r in rows:
        if np.isnan(r["c_pct"]) or r["n"] == 0:
            continue
        sep = 100 * r["c_ci"][0] > 100 * r["b_ci"][1]
        bar_met = r["c_pct"] > BAR_UNSEEN_C
        print(f"    K={r['k']:>3}: C={r['c_pct']:.1f}% CI=[{100*r['c_ci'][0]:.1f},{100*r['c_ci'][1]:.1f}]"
              f"  vs B={r['b_pct']:.1f}% CI=[{100*r['b_ci'][0]:.1f},{100*r['b_ci'][1]:.1f}]  "
              f"CI-separated-above-B={sep}  bar_met(>{BAR_UNSEEN_C:.0f}%)={bar_met}")
        if sep and bar_met:
            win_ks.append(r["k"])

    any_er_real = any(not np.isnan(r["mean_er"]) and r["mean_er"] > 2 * r["mean_null"] for r in rows)
    if win_ks:
        verdict = ("WIN"
                   if any_er_real else
                   "WIN (accuracy bar met) but style consistency is WEAK -- report both facts, "
                   "the accuracy lift may not be driven by a genuinely consistent shared style")
        conclusion = (f"WIN at K={win_ks} -- the richer hand-transform materially lifts UNSEEN-"
                      f"letter accuracy above pose-only, CI-separated -- fast adaptation via an "
                      f"explicit generalizing transform is SUPPORTED at this featureset/corpus "
                      f"scale.")
    else:
        verdict = "NULL"
        conclusion = ("NULL -- the richer (pose+style) transform never CI-separates materially "
                      "above pose-only on UNSEEN letters at any swept K -- the 34.7->55 (pose-only"
                      "->ceiling) gap does not localize to a further GENERALIZING transform; pose "
                      "is ~the transform ceiling for this featureset, and closing the rest of the "
                      "gap needs per-class coverage (harvest), i.e. per-letter idiosyncrasy, not a "
                      "richer shared-style transform.")
    print(f"\n  VERDICT: {verdict}")
    print(f"  {conclusion}")

    print(f"\n  ANOMALIES / HONEST RESIDUALS:")
    print(f"    given char+word segmentation throughout (this arc's own standing convention).")
    print(f"    canonical templates use a per-instance LOCAL baseline but a single POPULATION "
          f"x_height/slant (run 69's own population_frame) -- NOT the labeled writer's own frame; "
          f"the style field therefore captures the RESIDUAL after both the population-vs-writer "
          f"pose gap AND any true non-affine style, an intentional non-separation documented here "
          f"(separating them fully would need a second, population-relative pose estimate per "
          f"labeled letter -- out of this run's scope, noted as a follow-on).")
    print(f"    arm C never touches the K labeled letters' own per-class exemplar accumulation "
          f"(deliberately, to isolate the TRANSFORM from the already-refuted run-79 accumulation "
          f"mechanism) -- a FUSED arm (transform AND accumulation together) is a natural next step "
          f"but is out of this run's own pre-registered scope.")
    print(f"    K=20's qualifying-writer count is materially lower than K<=13's (writer word-"
          f"budget caps), same caveat run 79 itself reported.")
    print(f"    pose-decomposition anchor (condA/D/E) is measured on run 69's OWN held-out sample, "
          f"not literally the same instances as this run's own letter set -- cited as directional, "
          f"corpus-level context, per run 79's own citation discipline.")

    _save({
        "rows": [{k2: (v if not isinstance(v, tuple) else list(v)) for k2, v in r.items()}
                for r in rows],
        "pose_anchor": anchor, "win_ks": win_ks, "verdict": verdict, "conclusion": conclusion,
    }, _ckpt("summary.json"))
    _seed_guard("summary", md5_now)
    print(f"\n  saved -> {_ckpt('summary.json')}")
    print(f"\n{SEP}\n  RUN 80 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["prep", "read", "bootstrap", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "read": stage_read, "bootstrap": stage_bootstrap,
           "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
