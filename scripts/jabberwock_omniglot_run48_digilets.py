"""jabberwock_omniglot_run48_digilets.py -- RUN 48: THE TRUE PEN TEST, on DigiLeTs. Licensed by
run 47 (`1dc699e0`, this arc's own running memory): on real pen data the stroke grain REVIVES
under generalization (UCI held-out-STROKE Gate A: 18.4x the shuffled null) but the naive
two-layer union HARMED one-shot (UCI Gate B: continuous-only 74.5% vs hard-gated union 47.7%,
McNemar 7/66 p<1e-4) because shortlist COVERAGE was only 52-56% -- population-level identity
CONSISTENCY did not convert to per-episode discriminative RECALL. Run 47's own diagnosis named
TWO conflated causes: (1) UCI is a SINGLE-WRITER corpus, so the LEARN codebook never saw
cross-writer variation of the same class; (2) the union used a HARD shortlist gate that
DISCARDS a correct-but-unshortlisted answer outright, no matter how strong the continuous
verdict is underneath. DigiLeTs (Fabi/Otte/Butz, IEEE TCDS 2022 -- see
`LITERATURE_POSITIONING.md` finding F) resolves both at once: 77 writers x 62 classes x 5
instances = 23,870 trajectories, genuinely MANY-WRITER pen data, and this run's own SOFT FUSION
arm removes the hard shortlist gate entirely. This is the regime the whole arc lacked -- the
true pen test.

CORPUS (`domains/pen_world.py::load_digilets_samples` / `digilets_writer_split`, added this run):
200Hz Wacom pen, raw text format verified against the corpus's own `scripts/data.py`. A
PER-WRITER background/held-out split (NOT per-class, per-instance -- the point of this run is
genuine cross-writer generalization): 40 background writers for LEARN (adaptive-edge fit +
codebook growth), the other 37 held out with ZERO contact until Gate A/B.

MACHINERY REUSE (per this arc's own convention -- `scripts/jabberwock_omniglot_run45_foveate.py`
importing `run44b` as a module is the precedent): imports
`scripts.jabberwock_omniglot_run47_pendata` as `run47` and reuses its edge-fit
(`fit_edges_on_learn`), frozen-edge tokenization (`tokenize_with_frozen_edges`), SEED-WRITE-
ISOLATED codebook growth (`run_codebook_growth` -- see that function's own docstring for the
run-47 incident this closes; UNMODIFIED here, so the same isolation applies verbatim), Gate-A
consistency block (`_p1c_block`/`_entropy_block`), quantized-identity bags (`_ident_bags`/
`_combined_similarity`), the per-stroke geometric verdict (`domains.per_stroke_abs.program_score`,
via `run47.ps`), and the general statistics helpers (`wilson_ci`, `_mcnemar`, `_md5`, `_donkey0`,
`_save_json`/`_load_json`, `_saturation_verdict`, `_print_growth`, `DK`, `MAX_STROKES`,
`POINTSET_N`, `GROWTH_WINDOW`, `SATURATION_FRAGMENT_CAP`, `BAR_EXCESS_FACTOR`, `RNG_SEED`,
`P1C_NULL_REPS`). Nothing about run 47's own machinery is changed; this script only adds NEW
pieces: the writer-split population gathering, the SOFT FUSION arm, and the lambda calibration.

CRITICAL SEED-WRITE GUARD (run-47's own incident, restated as a HARD requirement this run
verifies FIRST, before any LEARN): `run47.run_codebook_growth` monkeypatches
`domains.stroke_codebook.teach` to a throwaway temp `seeds_dir` for the duration of every call --
`seeds/stroke_shapes.json` must be provably UNCHANGED across this run. `--stage unit_sanity`
below asserts the md5 before AND immediately after a CANARY `run_codebook_growth` call on a
tiny synthetic stroke (not real data) -- if that assertion fails, this run hard-stops before
`--stage learn` ever touches real background strokes. `--stage summary` re-asserts the SAME
md5 against the value captured at `unit_sanity` time.

GATE A -- CROSS-WRITER QUANTIZATION RETENTION: the LEARN-fit adaptive edges, FROZEN, applied to
the 37 held-out WRITERS' own strokes (all 62 TRAINED classes, writers NEVER seen during LEARN)
-- class-consistency vs a count-matched shuffled-class null, bar >=2x (`run47.BAR_EXCESS_FACTOR`,
unchanged). Cited alongside run 47's own UCI number (18.4x, same-corpus-family, but UCI's
"held-out" was held-out STROKES from the SAME single writer -- this run's held-out writers are a
strictly harder, more honest cross-writer generalization test).

GATE B -- END-TO-END ONE-SHOT, THREE ARMS, McNEMAR-PAIRED ON THE SAME EPISODES, cross-writer
(exemplar and query drawn from DIFFERENT held-out writers, same true class), at BOTH 20-way
(a seeded 20-class subset of the 62) and full 62-way:
  (i)   CONTINUOUS-ONLY: `per_stroke_abs.program_score`, argmin over candidates. Cited baselines:
        run-47 UCI 74.5% [68.4,79.8] (n=220, 20-way, single-writer); run-47 QuickDraw 29.5%
        [23.9,35.9] (n=220, 8-way, cross-writer touch).
  (ii)  HARD-GATE UNION: run-47's own mechanism, unmodified semantics -- argmin geo_score
        RESTRICTED to the top-K (K = n_way // 2, the arc's own ~50% shortlist convention)
        quantized bag-overlap shortlist. Cited: this is the arm that HARMED both of run 47's
        corpora (UCI 47.7%, QuickDraw 18.6%) via a ~52-56% coverage ceiling. Reproduced here as
        the CONTROL that failed, on the SAME episodes as the new arm.
  (iii) SOFT FUSION (this run's new mechanism, NO hard shortlist): fused_score = normalized
        geo_score - lambda * combined_quantized_similarity, argmin over ALL candidates -- the
        quantized signal RE-RANKS every candidate continuously instead of discarding any of
        them outright. `lambda=0` reproduces arm (i) EXACTLY (sanity-checked in `--stage
        calibrate`). `lambda` is FROZEN by `--stage calibrate` BEFORE any Gate B number is
        computed, via a background-writer-split calibration (the 39b/44b protocol: background-
        only tuning is legal; the frozen value never sees held-out data) -- and gated by a
        background-sanity STOP transplanted from run 45's own gate (`465d57da`): the calibrated
        arm must score >= baseline - 3pp on the SAME background episodes used to pick it, or
        this run hard-stops that N-way's Gate B before spending any held-out eval budget.
PRIMARY: McNemar (iii) vs (i) AND (iii) vs (ii), on the SAME episodes, both N-way sizes.
PRE-REGISTERED PREDICTIONS (stated before any Gate B number is computed): cross-writer LEARN
raises shortlist coverage above UCI's 52-56% (more writers seen during LEARN -> the codebook has
actually seen cross-writer variation of each class); soft fusion beats hard-gate (structurally,
by construction, since it cannot discard the correct candidate outright -- the interesting
question is by how much); the OPEN question this run exists to answer is whether soft fusion
beats CONTINUOUS-ONLY (arm i) -- if it does, the two-layer architecture finally ADDS on the
regime (cross-writer, many-writer LEARN) it was structurally starved of; if it does not, that is
reported as the finding, not hidden (STOP: (iii) broken >= fixed vs (i)).

HONESTY ON CORPUS DIFFICULTY: DigiLeTs is 62-way (10 digits + 26 lower + 26 upper), a HARDER
discrimination problem than Omniglot's within-alphabet 20-way, and the two are not directly
comparable numbers -- this run's headline is a CROSS-WRITER PEN-CHARACTER one-shot number, not
an Omniglot-comparable or BPL/human-comparable one. Stated in every report, not just here.

EXECUTION (ops law, binding, unchanged from every run in this arc): every invocation <=540s
foreground, intra-stage timing printed, checkpointed to `results/run48_checkpoints/` (every
other `results/run*_checkpoints/` directory is READ-ONLY reference, never written here).
`.venv` python for stages that need `substrate_rs`; system `python3` is fine for pure-loader
unit tests. NEVER run in background; NEVER end a turn with a live process.

ADDITIVE REPORTING (coordinator, mid-run, folded in BEFORE calibrate/gate_b were ever executed
-- no gate mechanics, RNG streams, or STOP conditions changed): (1) ARM ATTRIBUTION printed with
every Gate B report -- arm (i) continuous-only is near-zero-learned-prior (the cleanest
"identical-methods-as-Omniglot-80.5" comparator), arm (iii) soft-fusion uses the cross-writer
LEARN codebook (a modest nonzero prior) -- "does a wider training set help" is a DIFFERENT claim
from (i), kept separate in every report. (2) MATCHED N-WAY labeling -- 20-way is the human/BPL-
comparable number (Lake's protocol is 20-way), 62-way is context. (3) HOMOGLYPH CONFUSABILITY --
DigiLeTs' 62 classes pool digits + both letter cases (0/O/o, 1/l/I, 2/Z/z, 5/S/s, 6/G, 8/B,
9/g/q, c/C, k/K, p/P, u/U, v/V, w/W, x/X -- `HOMOGLYPH_GROUPS`), pairs unresolvable in isolation
even for a human, capping accuracy for a LABELING reason, not a method reason. Every Gate B
report now includes: a per-arm confusion table of the top error pairs, RAW accuracy vs accuracy
EXCLUDING homoglyph-collision errors (the method's real ceiling), and a THIRD Gate B run
(`--stage gate_b_20way_clean`) on a seeded homoglyph-FREE 20-way subset (`_way20_classes_clean`)
-- the cleanest human-comparable number this corpus can give. If most errors turn out to be
homoglyph collisions, that SUPPORTS the impoverished-corpus thesis as strongly as a clean ~95
would: the method hit the corpus's own labeling ceiling, not a limit of its own reasoning.

Run (from the gamma-substrate repo root):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run48_digilets.py --stage <STAGE>
Stages, in dependency order:
  unit_sanity -> learn -> gate_a -> calibrate ->
      gate_b_20way -> gate_b_62way -> gate_b_20way_clean -> summary
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import scripts.jabberwock_omniglot_run47_pendata as run47
from domains import pen_world as pw

SEP = "=" * 92
EPS = 1e-9

CKPT_DIR = os.path.join(ROOT, "results", "run48_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS (stated before any real-data number is computed).
# ------------------------------------------------------------------------------------------- #
N_BACKGROUND_WRITERS = 40           # of 77 -- the other 37 are held out, zero contact until
                                    # Gate A/B (per the launch brief's "e.g. 40 writers").
WRITER_SPLIT_SEED = 20260706

POOL_SHUFFLE_SEED = 20260707
EDGE_FIT_STROKE_CAP = 6000          # cheap tokenize-only pass (~7ms/stroke per run-47's own
                                    # measured rate) -- ~42s at this cap.
LEARN_STROKE_CAP = 2000             # heavy decode_ink codebook-growth pass (~157ms/stroke per
                                    # run-47's own measured rate) -- ~314s at this cap, the SAME
                                    # cap run 47 used for QuickDraw for the same reason.

WAY20_SEED = run47.RNG_SEED + 70    # seeded 20-of-62 class subset, fixed before any Gate B run.
N_WAY20 = 20

CALIBRATION_N_EPISODES = 150        # background-only, cheap (score computation is shared across
                                    # the whole lambda grid -- see `_score_episodes`).
LAMBDA_GRID = [0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0]
SANITY_MARGIN = 0.03                # background-sanity STOP bound, transplanted from run 45's
                                    # own gate (`465d57da`): armed must be >= baseline - 3pp.

GATE_B_N_EPISODES = 220             # matches run-47's own convention (n=220 both corpora).

# ------------------------------------------------------------------------------------------- #
# HOMOGLYPH CONFUSABILITY (additive reporting requirement -- coordinator, mid-run): DigiLeTs'
# 62 classes pool digits + both letter cases, so it contains pairs that are intrinsically
# ambiguous IN ISOLATION (no word context) even for a human reader -- 0/O/o, 1/l/I, 2/Z/z,
# 5/S/s, 6/G, 8/B, 9/g/q, and the same-letter case pairs c/C, k/K, p/P, u/U, v/V, w/W, x/X
# (o/O, s/S, z/Z are already covered by the digit groups above -- one connected-component
# grouping, not double-counted). These groups CAP the corpus's achievable accuracy below 100%
# for a LABELING reason, not a method reason -- reported separately below, never folded
# silently into the headline number.
HOMOGLYPH_GROUPS = [
    ("0", "O", "o"), ("1", "l", "I"), ("2", "Z", "z"), ("5", "S", "s"),
    ("6", "G"), ("8", "B"), ("9", "g", "q"),
    ("c", "C"), ("k", "K"), ("p", "P"), ("u", "U"), ("v", "V"), ("w", "W"), ("x", "X"),
]
SYMBOL_TO_HOMOGLYPH_GROUP = {sym: gid for gid, grp in enumerate(HOMOGLYPH_GROUPS) for sym in grp}
WAY20_CLEAN_SEED = run47.RNG_SEED + 72   # a SEPARATE seeded 20-way subset with NO two classes
                                          # sharing a homoglyph group -- the cleanest human-
                                          # comparable number this corpus can give.


def _is_homoglyph_pair(sym_a: str, sym_b: str) -> bool:
    ga, gb = SYMBOL_TO_HOMOGLYPH_GROUP.get(sym_a), SYMBOL_TO_HOMOGLYPH_GROUP.get(sym_b)
    return ga is not None and ga == gb


def _homoglyph_free_class_pool() -> list:
    """Every class with NO homoglyph partner in this pool, PLUS exactly one representative per
    homoglyph group (its lowest-index member in `DIGILETS_SYMBOLS` recording order) -- any
    20-way subset drawn from this pool is, by construction, collision-free."""
    pool = []
    seen_groups = set()
    for idx, sym in enumerate(pw.DIGILETS_SYMBOLS):
        gid = SYMBOL_TO_HOMOGLYPH_GROUP.get(sym)
        if gid is None:
            pool.append(idx)
        elif gid not in seen_groups:
            pool.append(idx)
            seen_groups.add(gid)
    return pool

# Cited run-47 numbers (READ FROM `results/run47_checkpoints/`, not re-derived -- see the
# `_run47_citations` loader below, which reads them live so a citation can never silently drift
# from the checkpoint it claims to cite).


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    run47._save_json(obj, path)


def _load_json(path: str):
    return run47._load_json(path)


def _run47_citations() -> dict:
    """Read run 47's OWN checkpoints live (READ-ONLY -- `results/run47_checkpoints/` is never
    written by this script) so every citation in this run's reports is provably the exact
    number run 47 produced, not a hand-copied constant that could drift."""
    out = {}
    gau = os.path.join(ROOT, "results", "run47_checkpoints", "gate_a_uci.json")
    gbu = os.path.join(ROOT, "results", "run47_checkpoints", "gate_b_uci.json")
    gbq = os.path.join(ROOT, "results", "run47_checkpoints", "gate_b_quickdraw.json")
    if os.path.exists(gau):
        d = run47._load_json(gau)
        out["uci_gate_a_mult"] = d["p1c_fine"]["mult_vs_null"]
    if os.path.exists(gbu):
        d = run47._load_json(gbu)["report"]
        out["uci_gate_b"] = {k: d[k] for k in ("n", "n_way", "shortlist_k",
                             "acc_continuous_only", "acc_quantized_proposal",
                             "shortlist_coverage", "mcnemar_ii_vs_i")}
    if os.path.exists(gbq):
        d = run47._load_json(gbq)["report"]
        out["quickdraw_gate_b"] = {k: d[k] for k in ("n", "n_way", "shortlist_k",
                                   "acc_continuous_only", "acc_quantized_proposal",
                                   "shortlist_coverage", "mcnemar_ii_vs_i")}
    return out


# ============================================================================================= #
#  STAGE: unit_sanity -- the seed-guard MUST be verified here, before any LEARN.
# ============================================================================================= #
def stage_unit_sanity():
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    ok_all = True

    md5_before = run47._md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 (BEFORE this run touches anything): {md5_before}")

    print("\n  (a) DigiLeTs loader round-trip (via domains.pen_world), FULL 77-writer corpus")
    t0 = time.time()
    samples = pw.load_digilets_samples()
    print(f"      n_samples={len(samples)}  (expected 77*62*5=23870)  "
         f"[{time.time()-t0:.1f}s]")
    n_writers = len({s["writer_id"] for s in samples})
    classes = sorted({s["class"] for s in samples})
    ok_a = (len(samples) == 77 * 62 * 5 and n_writers == 77 and classes == list(range(62)))
    print(f"      n_writers={n_writers}  n_classes={len(classes)}  -> "
         f"{'PASS' if ok_a else 'FAIL'}")
    ok_all &= ok_a

    print("\n  (b) writer-split leakage check (real data)")
    background, heldout = pw.digilets_writer_split(samples, n_background=N_BACKGROUND_WRITERS,
                                                    seed=WRITER_SPLIT_SEED)
    bg_writers = {s["writer_id"] for s in background}
    ho_writers = {s["writer_id"] for s in heldout}
    ok_b = (bg_writers.isdisjoint(ho_writers) and len(bg_writers) == N_BACKGROUND_WRITERS and
           len(ho_writers) == n_writers - N_BACKGROUND_WRITERS and
           len(background) + len(heldout) == len(samples))
    print(f"      n_background_writers={len(bg_writers)}  n_heldout_writers={len(ho_writers)}  "
         f"disjoint={bg_writers.isdisjoint(ho_writers)}  -> {'PASS' if ok_b else 'FAIL'}")
    ok_all &= ok_b

    print("\n  (c) dt sanity (honest report, not assumed -- per this module's own convention)")
    dts = []
    for s in samples[:500]:
        t = s["t_ms"]
        if len(t) > 1:
            dts.extend(np.diff(t).tolist())
    dts = np.asarray(dts)
    print(f"      n_dt={len(dts)}  median={np.median(dts):.2f}ms  mean={dts.mean():.2f}ms  "
         f"p95={np.percentile(dts, 95):.2f}ms  max={dts.max():.2f}ms  "
         f"n_outliers(>200ms)={int((dts > 200).sum())} ({100*(dts>200).mean():.2f}%)")
    print(f"      (semi-uniform, as documented -- rare large gaps exist; downstream geometry "
         f"here uses POSITION only, never raw dt, so this is reported, not corrected for)")

    print("\n  (d) SEED-WRITE GUARD CANARY -- a tiny SYNTHETIC growth call, real seeds untouched")
    canary_stroke = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
    gr = run47.run_codebook_growth([canary_stroke], {"level_edges": [0, 90, 180, 270, 360],
                                    "len_edges": [0, 1, 2]}, window=1)
    md5_after_canary = run47._md5(STROKE_SHAPES_SEED)
    ok_d = (md5_after_canary == md5_before)
    print(f"      canary growth: n_strokes={gr['n_strokes']}  final_codebook={gr['final_codebook']}")
    print(f"      seeds/stroke_shapes.json md5 AFTER canary: {md5_after_canary}  -> "
         f"{'PASS (unchanged)' if ok_d else 'FAIL -- SEED WRITE LEAK, STOP EVERYTHING'}")
    ok_all &= ok_d
    if not ok_d:
        raise SystemExit("HARD STOP: the seed-write guard failed on a SYNTHETIC canary before "
                         "any real LEARN was attempted. Do not proceed.")

    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}"
         f"\n{SEP}")
    _save_json({"ok_all": ok_all, "stroke_shapes_md5_before": md5_before,
               "n_samples": len(samples), "n_writers": n_writers,
               "n_background_writers": len(bg_writers), "n_heldout_writers": len(ho_writers)},
              _ckpt("unit_sanity.json"))
    print(f"  donkey=0: {'PASS' if run47._donkey0() else 'FAIL'}")
    if not ok_all:
        raise SystemExit(1)
    return 0


def _require_unit_sanity() -> dict:
    path = _ckpt("unit_sanity.json")
    if not os.path.exists(path):
        raise SystemExit("WALL: run --stage unit_sanity first.")
    d = _load_json(path)
    if not d.get("ok_all"):
        raise SystemExit("WALL: unit_sanity did not pass.")
    return d


# ============================================================================================= #
#  SHARED: writer-split population loading + pooled stroke gathering.
# ============================================================================================= #
def _load_split():
    samples = pw.load_digilets_samples()
    background, heldout = pw.digilets_writer_split(samples, n_background=N_BACKGROUND_WRITERS,
                                                    seed=WRITER_SPLIT_SEED)
    return background, heldout


def _gather_pooled_strokes(samples: list, *, cap: int, seed: int = POOL_SHUFFLE_SEED) -> list:
    """Every pen-down stroke (capped at `run47.MAX_STROKES` per instance, points>=2), pooled
    across ALL given samples then SHUFFLED (seeded) so a capped prefix is diverse across
    writers AND classes rather than biased toward whichever writer/class sorts first."""
    pooled = []
    for s in samples:
        for st in s["strokes"][:run47.MAX_STROKES]:
            if st.shape[0] >= 2:
                pooled.append(st.tolist())
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(pooled))
    if cap is not None:
        order = order[:cap]
    return [pooled[i] for i in order]


# ============================================================================================= #
#  STAGE: learn -- writer-split BACKGROUND adaptive edges + codebook growth.
# ============================================================================================= #
def stage_learn():
    print(f"\n{SEP}\n  STAGE: learn (adaptive edges + codebook growth, DigiLeTs BACKGROUND "
         f"writers)\n{SEP}")
    t0 = time.time()
    _require_unit_sanity()
    background, heldout = _load_split()
    print(f"  n_background_instances={len(background)}  n_heldout_instances={len(heldout)}")

    pooled = _gather_pooled_strokes(background, cap=None)
    print(f"  n_pooled_background_strokes (all, capped {run47.MAX_STROKES}/instance) = {len(pooled)}")
    edge_fit_points = pooled[:EDGE_FIT_STROKE_CAP]
    growth_points = pooled[:LEARN_STROKE_CAP]
    print(f"  edge-fit population: {len(edge_fit_points)} (cap {EDGE_FIT_STROKE_CAP})")
    print(f"  growth population:   {len(growth_points)} (cap {LEARN_STROKE_CAP})")

    frozen = run47.fit_edges_on_learn(edge_fit_points)
    print(f"\n  turn_edges ({len(frozen['level_edges'])-1} eff bins): "
         f"{[round(v,2) for v in frozen['level_edges']]}")
    print(f"  len_edges  ({len(frozen['len_edges'])-1} eff bins): "
         f"{[round(v,2) for v in frozen['len_edges']]}")
    print(f"  delta_edges ({len(frozen['delta_edges'])-1} eff bins): "
         f"{[round(v,2) for v in frozen['delta_edges']]}")
    print(f"  tol_deg={frozen['tol_deg']:.4f}  n_degenerate_learn={frozen['n_degenerate_learn']}")
    print(f"  occupancy entropy: turn={frozen['edges_report']['turn_occupancy']['entropy_bits']:.3f} "
         f"bits (max {frozen['edges_report']['turn_occupancy']['max_entropy_bits']:.3f}), "
         f"len={frozen['edges_report']['len_occupancy']['entropy_bits']:.3f} bits "
         f"(max {frozen['edges_report']['len_occupancy']['max_entropy_bits']:.3f})")
    print(f"  [edge-fit elapsed so far: {time.time()-t0:.1f}s]")

    print(f"\n  codebook growth (fresh boot_core(), SEED-WRITE ISOLATED, "
         f"{len(growth_points)} LEARN strokes)...")
    lr = run47.run_codebook_growth(growth_points, frozen, window=run47.GROWTH_WINDOW)
    run47._print_growth(lr["growth"])
    sat = run47._saturation_verdict(lr["growth"])
    print(f"\n  final codebook size: {lr['final_codebook']}  "
         f"(fragmentation cap {run47.SATURATION_FRAGMENT_CAP})")
    print(f"  SATURATION VERDICT: "
         f"{'PASS (flattens)' if sat else ('FAIL (no flattening)' if sat is False else 'INCONCLUSIVE (too few windows)')}")
    fragmentation_stop = lr["final_codebook"] > run47.SATURATION_FRAGMENT_CAP and sat is not True
    if fragmentation_stop:
        print(f"  FRAGMENTATION-CLAUSE STOP: codebook exceeded {run47.SATURATION_FRAGMENT_CAP} "
             f"without flattening.")

    md5_after = run47._md5(STROKE_SHAPES_SEED)
    us = _require_unit_sanity()
    seed_guard_ok = (md5_after == us["stroke_shapes_md5_before"])
    print(f"\n  seeds/stroke_shapes.json md5 AFTER learn: {md5_after}  "
         f"UNCHANGED={seed_guard_ok}")
    if not seed_guard_ok:
        raise SystemExit("HARD STOP: seeds/stroke_shapes.json changed during --stage learn.")

    out = {"n_background_instances": len(background), "n_heldout_instances": len(heldout),
          "n_pooled_background_strokes": len(pooled), "level_edges": frozen["level_edges"],
          "len_edges": frozen["len_edges"], "delta_edges": frozen["delta_edges"],
          "tol_deg": frozen["tol_deg"], "edges_report": frozen["edges_report"],
          "n_degenerate_learn": frozen["n_degenerate_learn"], "growth": lr["growth"],
          "final_codebook": lr["final_codebook"], "n_growth_strokes": lr["n_strokes"],
          "saturation_pass": sat, "fragmentation_stop": bool(fragmentation_stop),
          "seed_guard_ok": bool(seed_guard_ok)}
    _save_json(out, _ckpt("learn.json"))
    print(f"\n  saved -> {_ckpt('learn.json')}")
    print(f"  donkey=0: {'PASS' if run47._donkey0() else 'FAIL'}")
    print(f"  [learn wall time: {time.time()-t0:.1f}s]")
    return 0


def _require_learn() -> dict:
    path = _ckpt("learn.json")
    if not os.path.exists(path):
        raise SystemExit("WALL: run --stage learn first.")
    return _load_json(path)


# ============================================================================================= #
#  STAGE: gate_a -- cross-writer quantization retention.
# ============================================================================================= #
def stage_gate_a():
    print(f"\n{SEP}\n  STAGE: gate_a (cross-writer quantization retention, FROZEN LEARN edges "
         f"-> held-out WRITERS)\n{SEP}")
    t0 = time.time()
    frozen = _require_learn()
    _, heldout = _load_split()
    n_ho_writers = len({s["writer_id"] for s in heldout})
    print(f"  n_heldout_instances={len(heldout)}  n_heldout_writers={n_ho_writers} "
         f"(ZERO contact with the LEARN edge fit)")

    stroke_points = []
    for s in heldout:
        for st in s["strokes"][:run47.MAX_STROKES]:
            if st.shape[0] >= 2:
                stroke_points.append((st.tolist(), s["class"]))
    print(f"  n_heldout_strokes={len(stroke_points)}")

    records, n_degenerate = run47.tokenize_with_frozen_edges(stroke_points, frozen)
    print(f"  n_degenerate={n_degenerate}  [{time.time()-t0:.1f}s]")

    fine_idents = [r[0] for r in records]
    p3_fine = run47._entropy_block(fine_idents)
    print(f"\n  ENTROPY fine (held-out writers): {p3_fine['entropy_bits']:.4f} bits  "
         f"n_ids={p3_fine['n_families']}")

    class_members_fine, class_members_coarse = {}, {}
    for (fine, coarse, cls) in records:
        class_members_fine.setdefault(cls, []).append(fine)
        class_members_coarse.setdefault(cls, []).append(coarse)
    rng_fine = np.random.default_rng(run47.RNG_SEED + 80)
    rng_coarse = np.random.default_rng(run47.RNG_SEED + 81)
    p1c_fine = run47._p1c_block(class_members_fine, rng_fine)
    p1c_coarse = run47._p1c_block(class_members_coarse, rng_coarse)
    print(f"\n  HELD-OUT-WRITER CONSISTENCY fine:   raw={p1c_fine['raw_fraction']:.5f} "
         f"null={p1c_fine['null_mean']:.5f}  mult={run47._f(p1c_fine['mult_vs_null'],'.2f')}x  "
         f"clears_{run47.BAR_EXCESS_FACTOR}x={p1c_fine['excess_clears_bar']}")
    print(f"  HELD-OUT-WRITER CONSISTENCY coarse: raw={p1c_coarse['raw_fraction']:.5f} "
         f"null={p1c_coarse['null_mean']:.5f}  mult={run47._f(p1c_coarse['mult_vs_null'],'.2f')}x  "
         f"clears_{run47.BAR_EXCESS_FACTOR}x={p1c_coarse['excess_clears_bar']}")

    cite = _run47_citations()
    print(f"\n  RUN-47 CITATIONS (read live from results/run47_checkpoints/, not re-derived):")
    print(f"    UCI Gate A (held-out STROKES, single writer): "
         f"{cite.get('uci_gate_a_mult', 'N/A')}x")
    print(f"    mousewriting reference (OMNIGLOT_ARC.md): 1-2 identities at every 2x2 cell")

    gate_a_pass = p1c_fine["excess_clears_bar"] or p1c_coarse["excess_clears_bar"]
    print(f"\n  GATE A -- CROSS-WRITER (>=2x null on genuinely UNSEEN writers, either grain): "
         f"{'PASS' if gate_a_pass else 'FAIL'}")

    out = {"n_heldout_instances": len(heldout), "n_heldout_writers": n_ho_writers,
          "n_heldout_strokes": len(stroke_points), "n_degenerate": n_degenerate,
          "p3_entropy_fine": p3_fine, "p1c_fine": p1c_fine, "p1c_coarse": p1c_coarse,
          "run47_citations": cite, "gate_a_pass": bool(gate_a_pass)}
    _save_json(out, _ckpt("gate_a.json"))
    print(f"\n  saved -> {_ckpt('gate_a.json')}")
    print(f"  donkey=0: {'PASS' if run47._donkey0() else 'FAIL'}")
    print(f"  [gate_a wall time: {time.time()-t0:.1f}s]")
    return 0


def _require_gate_a() -> dict:
    path = _ckpt("gate_a.json")
    if not os.path.exists(path):
        raise SystemExit("WALL: run --stage gate_a first.")
    return _load_json(path)


# ============================================================================================= #
#  GATE B MACHINERY -- shared by calibrate / gate_b_20way / gate_b_62way.
# ============================================================================================= #
def _way62_classes() -> list:
    return list(range(62))


def _way20_classes() -> list:
    rng = np.random.default_rng(WAY20_SEED)
    return sorted(int(i) for i in rng.choice(62, size=N_WAY20, replace=False))


def _way20_classes_clean() -> list:
    """The homoglyph-FREE 20-way subset (additive reporting requirement): sampled from
    `_homoglyph_free_class_pool()` only, so no two chosen classes can be confused with each
    other in isolation -- the cleanest human/BPL-comparable number this corpus can give."""
    pool = _homoglyph_free_class_pool()
    rng = np.random.default_rng(WAY20_CLEAN_SEED)
    idx = rng.choice(len(pool), size=N_WAY20, replace=False)
    return sorted(int(pool[i]) for i in idx)


def _index_by_writer_class(samples: list) -> dict:
    idx: dict = {}
    for s in samples:
        idx.setdefault(s["writer_id"], {}).setdefault(s["class"], []).append(s)
    return idx


def _score_episodes(samples: list, way_classes: list, n_episodes: int, seed: int,
                    frozen: dict) -> list:
    """The ONE expensive pass: for `n_episodes` cross-writer one-shot episodes (exemplar and
    query for the TRUE class drawn from DIFFERENT writers; other classes' exemplars from any
    writer), compute `geo_scores` (continuous SC+TPS distance, one per candidate class) and
    `sims` (quantized combined-similarity, one per candidate class) ONCE. Every downstream arm
    decision (continuous-only, hard-gate at any K, soft-fusion at any lambda) is a CHEAP
    re-ranking of these same two vectors -- see `_apply_arms` -- so a whole lambda grid costs
    one pass, not one pass per lambda."""
    idx = _index_by_writer_class(samples)
    writers = sorted(w for w in idx if all(c in idx[w] and len(idx[w][c]) >= 1
                                           for c in way_classes))
    n_way = len(way_classes)
    assert len(writers) >= 2, "need >=2 writers with every way_class present"
    rng = np.random.default_rng(seed)
    episodes = []
    for ep in range(n_episodes):
        true_cls = way_classes[int(rng.integers(0, n_way))]
        ex_writer, ex_sample = {}, {}
        for c in way_classes:
            w = writers[int(rng.integers(0, len(writers)))]
            insts = idx[w][c]
            ex_writer[c] = w
            ex_sample[c] = insts[int(rng.integers(0, len(insts)))]
        other_writers = [w for w in writers if w != ex_writer[true_cls]]
        qw = other_writers[int(rng.integers(0, len(other_writers)))]
        q_insts = idx[qw][true_cls]
        query = q_insts[int(rng.integers(0, len(q_insts)))]

        candidate_strokes = [ex_sample[c]["strokes"] for c in way_classes]
        q_ps = run47._stroke_point_sets_from_arrays(query["strokes"])
        cand_ps = [run47._stroke_point_sets_from_arrays(cs) for cs in candidate_strokes]
        if not q_ps or any(not cps for cps in cand_ps):
            continue        # degenerate (no usable points) -- honest skip, never a crash.
        geo_scores = [run47.ps.program_score(q_ps, cps) for cps in cand_ps]

        candidate_bags = [run47._ident_bags(cs, frozen) for cs in candidate_strokes]
        query_bag = run47._ident_bags(query["strokes"], frozen)
        sims = [run47._combined_similarity(query_bag, cb) for cb in candidate_bags]
        jitter = rng.uniform(0.0, 1e-9, size=len(sims)).tolist()
        sims = [s + j for s, j in zip(sims, jitter)]

        true_idx = way_classes.index(true_cls)
        episodes.append({"geo_scores": geo_scores, "sims": sims, "true_idx": true_idx,
                         "ex_writer_true": ex_writer[true_cls], "q_writer": qw})
        if (ep + 1) % 50 == 0:
            print(f"    ... scored {ep+1}/{n_episodes} episodes", flush=True)
    return episodes


def _soft_fusion_idx(geo_scores: list, sims: list, lam: float) -> int:
    """`fused = normalized(geo_scores) - lam*sims`, argmin over ALL candidates -- no hard
    shortlist, so the correct candidate can never be discarded outright the way arm (ii)'s
    shortlist gate can discard it. `lam=0` reproduces `argmin(geo_scores)` EXACTLY (the
    continuous-only baseline) since the normalization is monotonic."""
    g = np.asarray(geo_scores, dtype=float)
    s = np.asarray(sims, dtype=float)
    g_range = float(g.max() - g.min())
    norm_g = (g - g.min()) / (g_range + EPS)
    fused = norm_g - lam * s
    return int(np.argmin(fused))


def _apply_arms(episodes: list, shortlist_k: int, lam: float) -> list:
    """CHEAP per-episode arm decisions from already-computed `geo_scores`/`sims`. Records the
    actual PREDICTED index (not just a correct/incorrect boolean) for each arm -- needed for
    the homoglyph-confusion accounting in `_gate_b_report` (additive reporting requirement)."""
    out = []
    for e in episodes:
        geo, sims, true_idx = e["geo_scores"], e["sims"], e["true_idx"]
        pred_i = int(np.argmin(geo))
        order = sorted(range(len(sims)), key=lambda i: -sims[i])
        shortlist = set(order[:shortlist_k])
        pred_ii = min(shortlist, key=lambda i: geo[i])
        pred_iii = _soft_fusion_idx(geo, sims, lam)
        out.append({"true_idx": true_idx, "in_shortlist": true_idx in shortlist,
                   "pred_i": pred_i, "pred_ii": pred_ii, "pred_iii": pred_iii,
                   "correct_i": pred_i == true_idx, "correct_ii": pred_ii == true_idx,
                   "correct_iii": pred_iii == true_idx})
    return out


def _homoglyph_arm_stats(records: list, way_classes: list, pred_key: str, correct_key: str,
                         top_n: int = 10) -> dict:
    """RAW accuracy vs accuracy EXCLUDING homoglyph-collision errors (treating a wrong answer
    that is a homoglyph partner of the true class as if it were correct -- the method's real
    ceiling on this corpus, since these pairs are unresolvable in isolation even for a human),
    plus a confusion table of the top error pairs (by symbol, not raw class index)."""
    n = len(records)

    def sym(idx: int) -> str:
        return pw.DIGILETS_SYMBOLS[way_classes[idx]]

    n_correct = sum(r[correct_key] for r in records)
    n_homoglyph_err = 0
    confusion = Counter()
    for r in records:
        if not r[correct_key]:
            t_sym, p_sym = sym(r["true_idx"]), sym(r[pred_key])
            confusion[(t_sym, p_sym)] += 1
            if _is_homoglyph_pair(t_sym, p_sym):
                n_homoglyph_err += 1
    n_other_err = (n - n_correct) - n_homoglyph_err
    return dict(acc_raw=n_correct / n, n_correct=n_correct, n_errors=n - n_correct,
               n_homoglyph_errors=n_homoglyph_err, n_other_errors=n_other_err,
               acc_excl_homoglyph=(n_correct + n_homoglyph_err) / n,
               top_confusions=[{"true": a, "pred": b, "count": c}
                               for (a, b), c in confusion.most_common(top_n)])


def _gate_b_report(records: list, way_classes: list, shortlist_k: int, lam: float) -> dict:
    n = len(records)
    n_way = len(way_classes)
    acc_i = sum(r["correct_i"] for r in records) / n
    acc_ii = sum(r["correct_ii"] for r in records) / n
    acc_iii = sum(r["correct_iii"] for r in records) / n
    ci_i = run47.wilson_ci(sum(r["correct_i"] for r in records), n)
    ci_ii = run47.wilson_ci(sum(r["correct_ii"] for r in records), n)
    ci_iii = run47.wilson_ci(sum(r["correct_iii"] for r in records), n)
    coverage = sum(r["in_shortlist"] for r in records) / n
    mc_ii_i = run47._mcnemar([r["correct_i"] for r in records], [r["correct_ii"] for r in records])
    mc_iii_i = run47._mcnemar([r["correct_i"] for r in records], [r["correct_iii"] for r in records])
    mc_iii_ii = run47._mcnemar([r["correct_ii"] for r in records], [r["correct_iii"] for r in records])
    homo_i = _homoglyph_arm_stats(records, way_classes, "pred_i", "correct_i")
    homo_ii = _homoglyph_arm_stats(records, way_classes, "pred_ii", "correct_ii")
    homo_iii = _homoglyph_arm_stats(records, way_classes, "pred_iii", "correct_iii")
    return dict(n=n, n_way=n_way, way_classes=way_classes,
               way_symbols=[pw.DIGILETS_SYMBOLS[c] for c in way_classes],
               shortlist_k=shortlist_k, lam=lam,
               acc_continuous_only=acc_i, ci_continuous_only=list(ci_i),
               acc_hard_gate_union=acc_ii, ci_hard_gate_union=list(ci_ii),
               acc_soft_fusion=acc_iii, ci_soft_fusion=list(ci_iii),
               shortlist_coverage=coverage,
               mcnemar_hard_vs_continuous=mc_ii_i, mcnemar_soft_vs_continuous=mc_iii_i,
               mcnemar_soft_vs_hard=mc_iii_ii,
               stop_hard_harms=bool(mc_ii_i["broken"] >= mc_ii_i["fixed"]),
               stop_soft_harms_vs_continuous=bool(mc_iii_i["broken"] >= mc_iii_i["fixed"]),
               homoglyph_continuous_only=homo_i, homoglyph_hard_gate_union=homo_ii,
               homoglyph_soft_fusion=homo_iii)


def _print_gate_b_report(rep: dict, label: str) -> None:
    print(f"\n  {label}: n={rep['n']}  N-way={rep['n_way']}  shortlist_K={rep['shortlist_k']}  "
         f"lambda={rep['lam']}")
    print(f"  ARM ATTRIBUTION: (i) continuous-only = near-zero-learned-prior (pure per-stroke "
         f"SC+TPS geometry, the CLEANEST 'identical-methods-as-Omniglot-80.5' comparator); "
         f"(iii) soft-fusion = uses the cross-writer LEARN codebook (a modest, nonzero prior) "
         f"-- 'does a wider training set help' is a DIFFERENT claim from (i), reported separately.")
    print(f"  (i)   CONTINUOUS-ONLY:  acc={100*rep['acc_continuous_only']:.1f}%  "
         f"CI=[{100*rep['ci_continuous_only'][0]:.1f},{100*rep['ci_continuous_only'][1]:.1f}]")
    print(f"  (ii)  HARD-GATE UNION:  acc={100*rep['acc_hard_gate_union']:.1f}%  "
         f"CI=[{100*rep['ci_hard_gate_union'][0]:.1f},{100*rep['ci_hard_gate_union'][1]:.1f}]  "
         f"coverage={100*rep['shortlist_coverage']:.1f}%")
    print(f"  (iii) SOFT FUSION:      acc={100*rep['acc_soft_fusion']:.1f}%  "
         f"CI=[{100*rep['ci_soft_fusion'][0]:.1f},{100*rep['ci_soft_fusion'][1]:.1f}]")
    m1, m2, m3 = rep["mcnemar_hard_vs_continuous"], rep["mcnemar_soft_vs_continuous"], rep["mcnemar_soft_vs_hard"]
    print(f"  McNemar (ii)  vs (i):  fixed={m1['fixed']}  broken={m1['broken']}  p={m1['p']:.4g}  "
         f"STOP(hard harms)={rep['stop_hard_harms']}")
    print(f"  McNemar (iii) vs (i):  fixed={m2['fixed']}  broken={m2['broken']}  p={m2['p']:.4g}  "
         f"STOP(soft harms vs continuous)={rep['stop_soft_harms_vs_continuous']}")
    print(f"  McNemar (iii) vs (ii): fixed={m3['fixed']}  broken={m3['broken']}  p={m3['p']:.4g}")

    print(f"\n  HOMOGLYPH CONFUSABILITY (0/O/o, 1/l/I, 2/Z/z, 5/S/s, 6/G, 8/B, 9/g/q, and "
         f"same-letter case pairs -- unresolvable in isolation, a LABELING ceiling not a "
         f"method ceiling):")
    for arm_label, key in (("(i)   continuous-only", "homoglyph_continuous_only"),
                           ("(ii)  hard-gate union", "homoglyph_hard_gate_union"),
                           ("(iii) soft fusion", "homoglyph_soft_fusion")):
        h = rep[key]
        print(f"    {arm_label}: raw_acc={100*h['acc_raw']:.1f}%  "
             f"acc_excl_homoglyph={100*h['acc_excl_homoglyph']:.1f}%  "
             f"(errors: {h['n_homoglyph_errors']} homoglyph / {h['n_other_errors']} other "
             f"of {h['n_errors']} total)")
    print(f"    top confusion pairs (i)   continuous-only: {rep['homoglyph_continuous_only']['top_confusions'][:6]}")
    print(f"    top confusion pairs (iii) soft-fusion:     {rep['homoglyph_soft_fusion']['top_confusions'][:6]}")


# ============================================================================================= #
#  STAGE: calibrate -- lambda, FROZEN on BACKGROUND writers, background-sanity STOP.
# ============================================================================================= #
def _calibrate_one_way(background: list, way_classes: list, frozen: dict, label: str,
                       seed: int) -> dict:
    print(f"\n  -- calibrating on BACKGROUND writers, {label} ({len(way_classes)}-way, "
         f"n={CALIBRATION_N_EPISODES}) --")
    t0 = time.time()
    episodes = _score_episodes(background, way_classes, CALIBRATION_N_EPISODES, seed, frozen)
    shortlist_k = max(1, len(way_classes) // 2)
    baseline_records = _apply_arms(episodes, shortlist_k, 0.0)
    acc_baseline = sum(r["correct_i"] for r in baseline_records) / len(baseline_records)

    sweep = []
    for lam in LAMBDA_GRID:
        recs = _apply_arms(episodes, shortlist_k, lam)
        acc_soft = sum(r["correct_iii"] for r in recs) / len(recs)
        sweep.append({"lam": lam, "acc_soft": acc_soft, "delta_vs_baseline": acc_soft - acc_baseline})
        print(f"    lambda={lam:5.2f}  acc_soft={100*acc_soft:5.1f}%  "
             f"delta={100*(acc_soft-acc_baseline):+.1f}pp")

    passing = [row for row in sweep if row["delta_vs_baseline"] >= -SANITY_MARGIN]
    if passing:
        best = max(passing, key=lambda r: (r["acc_soft"], -r["lam"]))
        sanity_pass = True
    else:
        best = max(sweep, key=lambda r: r["acc_soft"])
        sanity_pass = False
    print(f"\n  BACKGROUND-SANITY ({label}): baseline={100*acc_baseline:.1f}%  "
         f"best_lambda={best['lam']}  best_soft={100*best['acc_soft']:.1f}%  "
         f"delta={100*best['delta_vs_baseline']:+.1f}pp  bound=-{100*SANITY_MARGIN:.0f}pp  "
         f"-> {'PASS' if sanity_pass else 'HARD STOP'}")
    return {"label": label, "n_way": len(way_classes), "n_episodes": len(episodes),
           "shortlist_k": shortlist_k, "acc_baseline": acc_baseline, "sweep": sweep,
           "frozen_lambda": best["lam"], "frozen_lambda_acc_soft": best["acc_soft"],
           "sanity_pass": bool(sanity_pass), "elapsed": time.time() - t0}


def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (lambda, FROZEN on BACKGROUND writers, "
         f"background-sanity STOP)\n{SEP}")
    t0 = time.time()
    frozen = _require_learn()
    background, _ = _load_split()

    way20 = _way20_classes()
    way62 = _way62_classes()
    way20_clean = _way20_classes_clean()
    print(f"  20-way class subset (seeded, MAY include homoglyph pairs): {way20}")
    print(f"  20-way-CLEAN class subset (seeded, homoglyph-FREE by construction): {way20_clean} "
         f"({[pw.DIGILETS_SYMBOLS[c] for c in way20_clean]})")

    cal20 = _calibrate_one_way(background, way20, frozen, "20-way", run47.RNG_SEED + 90)
    cal62 = _calibrate_one_way(background, way62, frozen, "62-way", run47.RNG_SEED + 91)
    cal20_clean = _calibrate_one_way(background, way20_clean, frozen, "20-way-clean",
                                     run47.RNG_SEED + 92)

    out = {"way20_classes": way20, "way62_classes": way62, "way20_clean_classes": way20_clean,
          "cal20": cal20, "cal62": cal62, "cal20_clean": cal20_clean}
    _save_json(out, _ckpt("calibrate.json"))
    print(f"\n  saved -> {_ckpt('calibrate.json')}")
    print(f"  donkey=0: {'PASS' if run47._donkey0() else 'FAIL'}")
    print(f"  [calibrate wall time: {time.time()-t0:.1f}s]")
    return 0


def _require_calibrate() -> dict:
    path = _ckpt("calibrate.json")
    if not os.path.exists(path):
        raise SystemExit("WALL: run --stage calibrate first.")
    return _load_json(path)


# ============================================================================================= #
#  STAGE: gate_b_20way / gate_b_62way -- the real held-out-WRITER eval.
# ============================================================================================= #
def _run_gate_b(label: str, way_classes: list, cal: dict, seed: int) -> int:
    matched_note = ("  <-- MATCHED N-WAY: Lake's BPL protocol is 20-way; this is the "
                    "human/BPL-COMPARABLE number." if len(way_classes) == 20 else
                    "  <-- CONTEXT ONLY (62-way is harder than, and not directly comparable "
                    "to, Omniglot's 20-way).")
    print(f"\n{SEP}\n  STAGE: gate_b_{label} (one-shot {len(way_classes)}-way, cross-WRITER, "
         f"held-out only){matched_note}\n{SEP}")
    t0 = time.time()
    if not cal["sanity_pass"]:
        print(f"  BACKGROUND-SANITY STOP fired for {label} at --stage calibrate "
             f"(lambda={cal['frozen_lambda']} scored {100*cal['frozen_lambda_acc_soft']:.1f}% "
             f"vs baseline {100*cal['acc_baseline']:.1f}%, outside the -{100*SANITY_MARGIN:.0f}pp "
             f"bound). STOPPING -- not spending held-out eval budget on a failed calibration.")
        out = {"skipped": True, "reason": "background_sanity_stop", "calibration": cal}
        _save_json(out, _ckpt(f"gate_b_{label}.json"))
        return 0

    frozen = _require_learn()
    _, heldout = _load_split()
    lam = cal["frozen_lambda"]
    shortlist_k = cal["shortlist_k"]
    print(f"  n_way={len(way_classes)}  frozen_lambda={lam} (from --stage calibrate)  "
         f"shortlist_K={shortlist_k}  n_heldout_instances={len(heldout)}")

    episodes = _score_episodes(heldout, way_classes, GATE_B_N_EPISODES, seed, frozen)
    print(f"  n_episodes_scored={len(episodes)} (target {GATE_B_N_EPISODES})  "
         f"[{time.time()-t0:.1f}s]")
    records = _apply_arms(episodes, shortlist_k, lam)
    rep = _gate_b_report(records, way_classes, shortlist_k, lam)
    _print_gate_b_report(rep, f"GATE B {label.upper()}")

    out = {"skipped": False, "report": rep, "calibration_used": {"frozen_lambda": lam,
          "shortlist_k": shortlist_k, "cal_sanity_pass": cal["sanity_pass"]}}
    _save_json(out, _ckpt(f"gate_b_{label}.json"))
    print(f"\n  saved -> {_ckpt(f'gate_b_{label}.json')}")
    print(f"  donkey=0: {'PASS' if run47._donkey0() else 'FAIL'}")
    print(f"  [gate_b_{label} wall time: {time.time()-t0:.1f}s]")
    return 0


def stage_gate_b_20way():
    cal = _require_calibrate()
    way20 = cal["way20_classes"]
    return _run_gate_b("20way", way20, cal["cal20"], run47.RNG_SEED + 100)


def stage_gate_b_62way():
    cal = _require_calibrate()
    way62 = cal["way62_classes"]
    return _run_gate_b("62way", way62, cal["cal62"], run47.RNG_SEED + 101)


def stage_gate_b_20way_clean():
    """The homoglyph-FREE 20-way subset (additive reporting requirement): the cleanest
    human/BPL-comparable number this corpus can give, since no two candidate classes can be
    confused with each other in isolation by construction."""
    cal = _require_calibrate()
    way20_clean = cal["way20_clean_classes"]
    return _run_gate_b("20way_clean", way20_clean, cal["cal20_clean"], run47.RNG_SEED + 102)


# ============================================================================================= #
#  STAGE: summary
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 48 SCOREBOARD (THE TRUE PEN TEST, DigiLeTs)\n{SEP}")
    needed = ["unit_sanity.json", "learn.json", "gate_a.json", "calibrate.json",
             "gate_b_20way.json", "gate_b_62way.json", "gate_b_20way_clean.json"]
    missing = [n for n in needed if not os.path.exists(_ckpt(n))]
    if missing:
        print(f"  INCOMPLETE -- missing checkpoints: {missing}")
        return 1
    data = {n: _load_json(_ckpt(n)) for n in needed}

    md5_before = data["unit_sanity.json"]["stroke_shapes_md5_before"]
    md5_after = run47._md5(STROKE_SHAPES_SEED)
    print(f"\n  SEED-GUARD: seeds/stroke_shapes.json md5 before={md5_before}  after={md5_after}  "
         f"UNCHANGED={md5_before == md5_after}")

    lrn = data["learn.json"]
    print(f"\n  LEARN SATURATION (DigiLeTs, {data['unit_sanity.json']['n_background_writers']} "
         f"background writers):")
    print(f"    final_codebook={lrn['final_codebook']}  saturation_pass={lrn['saturation_pass']}  "
         f"fragmentation_stop={lrn['fragmentation_stop']}")
    print(f"    (mousewriting reference: 5-7 top-level quanta before flattening; run-47 UCI/QD "
         f"both saturated well past that)")

    ga = data["gate_a.json"]
    cite = ga["run47_citations"]
    print(f"\n  GATE A -- CROSS-WRITER RETENTION (held-out WRITERS, frozen LEARN edges):")
    print(f"    DigiLeTs: raw={ga['p1c_fine']['raw_fraction']:.5f}  "
         f"null={ga['p1c_fine']['null_mean']:.5f}  "
         f"mult={run47._f(ga['p1c_fine']['mult_vs_null'],'.2f')}x  PASS={ga['gate_a_pass']}")
    print(f"    (cited, not re-derived) run-47 UCI held-out-STROKE (single writer): "
         f"{cite.get('uci_gate_a_mult','N/A')}x")

    print(f"\n  LAMBDA CALIBRATION (background-writer split, background-sanity bound "
         f"-{100*SANITY_MARGIN:.0f}pp):")
    for key, cal in (("20-way", data["calibrate.json"]["cal20"]),
                     ("62-way", data["calibrate.json"]["cal62"]),
                     ("20-way-clean", data["calibrate.json"]["cal20_clean"])):
        print(f"    {key}: frozen_lambda={cal['frozen_lambda']}  "
             f"baseline={100*cal['acc_baseline']:.1f}%  "
             f"armed={100*cal['frozen_lambda_acc_soft']:.1f}%  "
             f"sanity_pass={cal['sanity_pass']}")

    print(f"\n  MATCHED N-WAY: 20-way is the human/BPL-comparable number (Lake's protocol is "
         f"20-way); 62-way is context only; 20-way-CLEAN (homoglyph-free by construction) is "
         f"the cleanest human-comparable number this corpus can give.")
    for key in ("gate_b_20way.json", "gate_b_62way.json", "gate_b_20way_clean.json"):
        gb = data[key]
        label = key.replace("gate_b_", "").replace(".json", "").upper()
        print(f"\n  GATE B {label}:")
        if gb.get("skipped"):
            print(f"    SKIPPED -- {gb.get('reason')}")
            continue
        rep = gb["report"]
        print(f"    n={rep['n']}  (i) continuous={100*rep['acc_continuous_only']:.1f}%  "
             f"(ii) hard-gate={100*rep['acc_hard_gate_union']:.1f}%  "
             f"(iii) soft-fusion={100*rep['acc_soft_fusion']:.1f}%")
        print(f"    coverage(hard-gate)={100*rep['shortlist_coverage']:.1f}%  "
             f"McNemar(iii vs i) p={rep['mcnemar_soft_vs_continuous']['p']:.4g}  "
             f"STOP(soft harms vs continuous)={rep['stop_soft_harms_vs_continuous']}")
        hi, hiii = rep["homoglyph_continuous_only"], rep["homoglyph_soft_fusion"]
        print(f"    homoglyph: (i) raw={100*hi['acc_raw']:.1f}% excl={100*hi['acc_excl_homoglyph']:.1f}%  "
             f"(iii) raw={100*hiii['acc_raw']:.1f}% excl={100*hiii['acc_excl_homoglyph']:.1f}%")

    print(f"\n  RUN-47 CITED BASELINES (single-writer UCI / cross-writer-touch QuickDraw):")
    uci_gb = cite.get("uci_gate_b", {})
    qd_gb = cite.get("quickdraw_gate_b", {})
    if uci_gb:
        print(f"    UCI      n={uci_gb['n']} {uci_gb['n_way']}-way: continuous="
             f"{100*uci_gb['acc_continuous_only']:.1f}%  hard-gate="
             f"{100*uci_gb['acc_quantized_proposal']:.1f}%  coverage="
             f"{100*uci_gb['shortlist_coverage']:.1f}%")
    if qd_gb:
        print(f"    QuickDraw n={qd_gb['n']} {qd_gb['n_way']}-way: continuous="
             f"{100*qd_gb['acc_continuous_only']:.1f}%  hard-gate="
             f"{100*qd_gb['acc_quantized_proposal']:.1f}%  coverage="
             f"{100*qd_gb['shortlist_coverage']:.1f}%")

    print(f"\n  HONESTY NOTE: DigiLeTs is 62-way (10 digits + 26 lower + 26 upper) -- a HARDER "
         f"discrimination problem than Omniglot's within-alphabet 20-way. This is a cross-writer "
         f"PEN-CHARACTER one-shot number, not an Omniglot/BPL/human-comparable one.")

    print(f"\n{SEP}\n  RUN 48 COMPLETE -- see final agent report for full narrative.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                  choices=["unit_sanity", "learn", "gate_a", "calibrate",
                          "gate_b_20way", "gate_b_62way", "gate_b_20way_clean", "summary"])
    args = p.parse_args()
    fn = {"unit_sanity": stage_unit_sanity, "learn": stage_learn, "gate_a": stage_gate_a,
         "calibrate": stage_calibrate, "gate_b_20way": stage_gate_b_20way,
         "gate_b_62way": stage_gate_b_62way, "gate_b_20way_clean": stage_gate_b_20way_clean,
         "summary": stage_summary}[args.stage]
    return fn()


if __name__ == "__main__":
    sys.exit(main())
