"""OMNIGLOT RUN 34d -- THE FINAL CELL: ADAPTIVE EDGES x DENOISED POINTS (THE 2x2 INTERACTION).

THE STANDING 2x2 (mouse-observation-model x bin-placement, each axis nulled with the other
OFF):

  |                | raw points                          | denoised points                |
  |----------------|--------------------------------------|---------------------------------|
  | uniform bins   | collapse, 2 ids (run26/28 CONTROL)   | collapse, TIGHTER, 1 id (34c)  |
  | adaptive edges | 83 ids, INSTANCE-grain (run32 NULL)  | *** THIS RUN ***                |

Run 32 (commit 13ebc282) revived identity entropy (0.0014 -> 3.9968 bits, 2 -> 83 identities)
by re-placing turn/length bin edges on the LEARN population's own quantile structure -- but
82 of the 83 identities were `stroke_18814ab760d8__ref_turn_*` children of ONE root, i.e.
PER-DRAWER refinements of a single stroke shape, not per-CHARACTER structure: coverage@10
nulled (69.5% [64.8,73.8] vs control 71.5% [66.9,75.7], a DIFFERENT episode set, not a larger
one). Run 34c (commit 8323f2a9) ran the orthogonal axis -- the SAME uniform bins, but every
raw point globally denoised first (`mouse_model.denoise_path_global`, 34b's proven inverse,
89.6% point-mass dissolution, no hallucinated curvature) -- and the identity collapse got
MARGINALLY TIGHTER (1 id, not 2), because de-staircasing removes exactly the jitter that
occasionally tipped a stroke into a second bin under uniform placement: uniform bins were
never going to reveal structure denoising alone can expose.

THE HYPOTHESIS THIS RUN TESTS: run-32's 83-way fragmentation was ITSELF pixel-staircase
INSTANCE noise -- each drawer's own mouse-sensor jitter, quantized finely enough by adaptive
placement to mint its own near-duplicate quantum. If that diagnosis is right, denoising BEFORE
computing adaptive edges (and before every decode that consumes them) should collapse the
83 drawer-specific artifacts back into CLASS-grain structure: same-or-more entropy than run
32's un-denoised ADAPT arm, but with identities that are COHERENT across multiple drawers of
the SAME character (34c's own new P1b metric, never measurable in run 32 because run 32's
un-denoised population was ~100% single-drawer singletons by inspection). Each single-variable
run measured its lever in isolation; interactions are exactly what isolation cannot see.

ISOLATING NOTHING FURTHER: this is the FULL interaction cell -- BOTH levers on at once. There
is no third variable to hold fixed; the two prior runs (32, 34c) already measured each lever
alone. This run's bin COUNT still matches `gate.DK` (`DEFAULT_TURN_BINS`/`DEFAULT_LEN_BINS`,
run-32's own convention: the lever is PLACEMENT, not count) and edges are fit via
`domains/adaptive_bins.py` UNCHANGED (`compute_quantile_edges`'s dedupe/strictly-increasing
guards, run 32's amendment, reused verbatim, mandatory here too since the point-mass at 0 deg
survives partially even after denoising per 34c's own 1-identity finding) -- the ONE change
from run 32's own recipe is that `gather-edges`, `learn`, `calibrate`, `entropy-report`, `eval`,
and `falsenovelty` all consume points passed through `mouse_model.denoise_path_global` FIRST
(34c's own `_dn` helper, reused verbatim), so the edges themselves are fit to the DENOISED
distribution, not the raw staircase.

WHY A NEW SCRIPT, NOT A NEW ARM: same discipline as 34c's own header -- `domains/mouse_model.py`,
`ink_decode.py`, `abs_read.py`, `novelty_calibration.py`, `stroke_codebook.py`,
`homework_loop.py`, and `scripts/jabberwock_omniglot_dynamic_quantization.py` are shared,
parallel-session-owned modules; this script touches NONE of them (`domains/adaptive_bins.py`
is READ via its existing public API only -- `gather_learn_span_values`/`compute_adaptive_edges`/
`store_adaptive_edges`, exactly as run 32 already calls them -- never edited). Every edges/
denoise injection point is either an existing kwarg on an unmodified shared function
(`ink.decode_ink`'s own `turn_edges=`/`len_edges=`, `nc._measure_stroke`'s own `turn_edges=`/
`len_edges=`) or a raw-point pre-processing step performed IN THIS SCRIPT before handing
already-denoised points to an unmodified shared function (`_dn`, 34c's own convention). ONE
place has no edges-aware kwarg upstream (`run28_plastic._count_false_novelty` calls
`ink.decode_ink` without `turn_edges`/`len_edges` -- fine for run 32/34c, whose codebooks were
uniform-binned, but WRONG here, since this run's codebook is edges-binned and a mismatched
bin boundary would misclassify every probe span as OOV, not a real false-novelty count): this
script defines its OWN `_count_false_novelty_denoised` (an edges-aware, denoised clone of
`run28_plastic`'s function, in this file only) rather than silently reusing the wrong one.

PRE-REGISTERED CONTROLS (CITED, never re-run/re-grown -- read-only reference data):
  RUN26_CONTROL   coverage@10 = 71.5% [66.9, 75.7]  n=400 k=286  (results/run26_checkpoints/
                  eval_baseline.json) -- UNIFORM bins, RAW points.
  RUN32_ADAPT     coverage@10 = 69.5% [64.8, 73.8]  n=400 k=278  newly_covered=34 lost=42
                  (results/run32_checkpoints/report.json arms.adapt) -- ADAPTIVE edges, RAW
                  points; identity entropy 3.9968 bits / 83 ids, top_family_share 40.1%,
                  INSTANCE-grain fragmentation (82/83 ids are per-drawer ref_turn children of
                  ONE root -- coherence ~0 by inspection, never formally measured).
  RUN34C          coverage@10 = 72.0% [67.4, 76.2]  (results/omniglot_gate_run34c.log) --
                  UNIFORM bins, DENOISED points; identity entropy ~0 bits / 1 id (TIGHTER than
                  control's 2 ids/0.0014 bits).

PRE-REGISTERED METRIC DEFINITIONS (stated before any number below is computed):
  P1a. IDENTITY-GRAIN ENTROPY (Shannon bits, base 2) of `res["name"]` over every ACCEPTED span
       (any tier) decoded from the SAME 1500-stroke LEARN population (background[:5], drawers
       01-14), on THIS run's own denoised + adaptive-edges + calibrated graph -- directly
       comparable to RUN32_ADAPT's 3.9968 bits / 83 ids (SAME population, SAME grain, SAME
       measurement method).
  P1b. CLASS-GRAIN COHERENCE FRACTION (34c's own metric, reused verbatim): for every distinct
       identity name observed, record (identity, class_key=(alphabet,character_dir), drawer)
       triples from its occurrences; an identity is COHERENT iff some class_key it appears in
       was independently produced by >=3 distinct drawers. Coherence fraction = coherent /
       distinct identities. THE DECISIVE CONTRAST (stated before any number is seen): vs run
       32's un-denoised ADAPT arm (82/83 ids are single-drawer ref_turn children -- coherence
       ~0 by inspection) --
         - similar-or-higher entropy WITH MATERIALLY HIGHER coherence => the interaction is
           real: denoising collapsed drawer-instance noise while adaptive placement still
           reveals real turn-angle structure at the CLASS grain -- the cell the 2x2 predicted.
         - similar entropy with similarly-near-zero coherence => noise was NOT the fragmenter;
           the 83-way split reflects genuine per-instance shape variation adaptive placement
           over-resolves regardless of denoising -- the cell nulls, and the interaction
           hypothesis is falsified honestly.
  P2. coverage@10 at n=400 (SAME test alphabets/protocol/POWER_SEED/WAY/R_TARGET as run
      17b/25/26/32/34c's own C0), Wilson 95% CI, vs RUN26_CONTROL (the deliverable) AND cited
      against RUN32_ADAPT (69.5%) -- beating BOTH matters; beating neither, one, or the other
      are all reported as the exact shape observed, not collapsed to a single verdict.
  P3. LEARN saturation (growth-curve flattening) AND the fragmentation clause (run 32's own):
      codebook top-level count > 3x RUN26_CONTROL's own top-level count (5) WITHOUT a P2
      coverage gain = fragmentation-repeat, report, corridor closes at this cell too.
  P4. False-novelty probe (`run28_plastic._build_false_novelty_probe()`'s own 50-item single-
      stroke probe, real strokes from the LEARN alphabets, genuinely mastered material) --
      DENOISED and measured EDGES-AWARE via this script's own `_count_false_novelty_denoised`
      (see rationale above) -- must mint 0/50 spurious quanta on this run's own calibrated
      graph.

STOPS (pre-registered):
  - P3's fragmentation clause fires (>3x control top with no P2 gain) -> report, this cell
    closes on fragmentation grounds regardless of P1/P2 shape.
  - P1-fragmentation-repeat (coherence stays near-zero, matching run 32's un-denoised shape)
    PLUS P2-null (coverage does not beat control at power) => the 2x2 is COMPLETE and the
    mousewriting stroke featureset is CLOSED AT EVERY MEASURED CELL: neither axis alone nor
    both together move the proposal-layer deliverable beyond the ~70-72% band this featureset
    has produced in all four cells. This is reported AS the finding, not as a failure to find
    one -- a fully-measured 2x2 with a consistent null is a completed research object.
  - If P1 shows genuine coherence gain (interaction confirmed at the mechanism level) but P2
    still nulls at power, report EXACTLY that shape ("mechanism revived, proposal-layer flat")
    -- mechanism-level and deliverable-level verdicts are reported independently, never
    collapsed into one number.

EXECUTION (ops law, binding): every invocation <=540s foreground, intra-stage batch
checkpointing (34c's/32's pattern: BATCH_STROKES=200 given denoise's ~27ms/stroke cost stacks
with edges-aware decode), stdbuf+tee to `results/omniglot_gate_run34d.log`, checkpoints under
`results/run34d_checkpoints/` (run26-34c checkpoint dirs READ-ONLY reference, never written
here). SEED ISOLATION: every `teach()` persistence this process performs is redirected to
`results/run34d_checkpoints/seeds/` (run 32/34c's own pattern) -- `seeds/stroke_shapes.json`
(a PARALLEL-SESSION-OWNED, already-dirty file) is never touched by this script.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run34d_interaction.py --stage verify
      ... --stage gather-edges   (batch-checkpointed, re-invoke until COMPLETE)
      ... --stage learn          (batch-checkpointed, re-invoke until COMPLETE)
      ... --stage calibrate      (batch-checkpointed, re-invoke until COMPLETE)
      ... --stage entropy-report (P1a/P1b, batch-checkpointed, re-invoke until COMPLETE)
      ... --stage eval           (P2, block-checkpointed, re-invoke until COMPLETE)
      ... --stage falsenovelty   (P4, single call)
      ... --stage report
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

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
import scripts.jabberwock_omniglot_run28_plastic as run28
import scripts.jabberwock_omniglot_run29_consume as run29
from domains import abs_read as ar
from domains import adaptive_bins as ab
from domains import character_compose as cc
from domains import ink_decode as ink
from domains import mouse_model as mm
from domains import novelty_calibration as nc
from domains import omniglot_world as ow
from domains import stroke_codebook as sc

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run34d_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")    # READ-ONLY reference.
RUN32_DIR = os.path.join(ROOT, "results", "run32_checkpoints")    # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# SEED ISOLATION (run 32/34c's own pattern, reused verbatim): redirect EVERY teach()
# persistence this process performs to this run's OWN seeds dir. seeds/stroke_shapes.json
# (parallel-session-owned, already dirty) is never touched -- the live-graph install is
# unaffected, only the manifest WRITE location moves.
# ---------------------------------------------------------------------------------------------
RUN34D_SEEDS_DIR = os.path.join(CKPT_DIR, "seeds")
os.makedirs(RUN34D_SEEDS_DIR, exist_ok=True)
from domains.teach import teach as _real_teach


def _isolated_teach(*a, **k):
    return _real_teach(*a, **{**k, "seeds_dir": Path(RUN34D_SEEDS_DIR)})


sc.teach = _isolated_teach
cc.teach = _isolated_teach
import domains.teach as _teach_mod
_teach_mod.teach = _isolated_teach

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS -- byte-identical to run 26/32/34c where they overlap.
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N            # 5
LEARN_DRAWERS = gate.LEARN_DRAWERS                    # 01..14
LEARN_STROKE_CAP = 1500                               # run 16/25's saturation-verified cap.
DK = gate.DK                                          # bin COUNT unchanged -- the lever is
                                                       # placement (edges) + denoise, not count.
GROWTH_WINDOW = gate.GROWTH_WINDOW
SHORTLIST_K = 10
R_TARGET = run25.R_TARGET
WAY = run25.WAY
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS
POWER_SEED = run25.POWER_SEED
PER_CALL_BUDGET_SECONDS = 460.0
BATCH_STROKES = 200          # denoise (~27ms/stroke) + edges-aware decode stack -- 34c's
                              # smaller-than-run32 batch size, kept here for the same reason.
RUNAWAY_FACTOR = 10.0         # structural mid-learn abort guard (run 32's amendment).

RUN26_CONTROL_COVERAGE = {"cov": 0.715, "ci": (0.6689, 0.7570), "n": 400, "k": 286,
                           "note": "run26_checkpoints/eval_baseline.json"}
RUN32_ADAPT_COVERAGE = {"cov": 0.695, "ci": (0.6482, 0.7381), "n": 400, "k": 278,
                         "newly_covered": 34, "lost": 42,
                         "note": "run32_checkpoints/report.json arms.adapt"}


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _run26(name: str) -> str:
    return os.path.join(RUN26_DIR, name)


def _run32(name: str) -> str:
    return os.path.join(RUN32_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _donkey0() -> bool:
    return "torch" not in sys.modules


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((centre - adj) / denom, (centre + adj) / denom)


def _ci_separated(a: tuple, b: tuple) -> bool:
    return a[1] < b[0] or b[1] < a[0]


def _save_graph(s, path: str) -> None:
    run29._save_graph(s, path)


def _load_graph(path: str):
    return run29._load_graph(path)


# ---------------------------------------------------------------------------------------------
# THE ONE DENOISE HOOK (34c's `_dn`, reused verbatim): every raw stroke passes through the
# GLOBAL constrained smoother (34b's own principled inverse, default params) before it ever
# reaches ingest/decode/edge-fitting -- LEARN, gather-edges, calibrate, entropy measurement,
# eval, and the false-novelty probe all consume denoised points.
# ---------------------------------------------------------------------------------------------
def _dn(points) -> list:
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 3:
        return pts.tolist()
    return mm.denoise_path_global(pts).tolist()


# ---------------------------------------------------------------------------------------------
# LOCAL gather routine (34c's `_collect_learn_strokes_tagged`, reused verbatim): SAME
# iteration order as run32's `_collect_learn_strokes_with_drawer` (alphabet -> character ->
# drawer -> stroke), carrying (alphabet, character) alongside each stroke's drawer id -- P1b's
# raw material. Pure I/O gather, no decode, no decision.
# ---------------------------------------------------------------------------------------------
def _collect_learn_strokes_tagged(alphabets: list, drawers: list, cap: int) -> list:
    out = []
    for alph in alphabets:
        if len(out) >= cap:
            break
        for cdir in ow.characters(alph, "background"):
            if len(out) >= cap:
                break
            char = os.path.basename(cdir)
            files_by_drawer = {}
            for f in ow.drawings(cdir):
                d = f.split("/")[-1].split("_")[-1].replace(".txt", "")
                files_by_drawer[d] = f
            for d in drawers:
                if len(out) >= cap:
                    break
                f = files_by_drawer.get(d)
                if f is None:
                    continue
                for st in ow.load_strokes(f):
                    if len(out) >= cap:
                        break
                    if st.shape[0] < 2:
                        continue
                    out.append((st.tolist(), d, alph, char))
    return out


# ---------------------------------------------------------------------------------------------
# STAGE: verify -- prerequisites present (run26 control, run32 ADAPT report, run34c citation,
# real data). Batch-checkpointing not needed -- pure file-existence + recipe-constant checks.
# ---------------------------------------------------------------------------------------------
def stage_verify():
    print(f"\n{SEP}\n  STAGE: verify (RUN 34d -- recipe/citation check)\n{SEP}")
    needed = [_run26("learn_meta.json"), _run26("eval_baseline.json"),
              _run32("entropy_report.json"), _run32("report.json")]
    missing = [p for p in needed if not os.path.exists(p)]
    if missing:
        print(f"  WALL: missing prerequisite file(s): {missing}")
        return 1
    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print("  WALL: Omniglot data not found.")
        return 1
    control_meta = _load_json(_run26("learn_meta.json"))
    control_cov = _load_json(_run26("eval_baseline.json"))["coverage"]
    run32_ent = _load_json(_run32("entropy_report.json"))
    run32_report = _load_json(_run32("report.json"))
    run32_adapt_cov = run32_report["arms"]["adapt"]["coverage"]
    checks = [
        ("gate.SEED", gate.SEED, gate.SEED),
        ("LEARN_ALPHABETS_N", LEARN_ALPHABETS_N, gate.LEARN_ALPHABETS_N),
        ("DK (bin count)", DK, gate.DK),
        ("LEARN_STROKE_CAP", LEARN_STROKE_CAP, 1500),
        ("learn_alphabets", control_meta["learn_alphabets"],
         ow.alphabets("background")[:LEARN_ALPHABETS_N]),
        ("n_strokes", control_meta["n_strokes"], LEARN_STROKE_CAP),
    ]
    ok = True
    for label, a, b in checks:
        match = (a == b)
        ok = ok and match
        print(f"  recipe check  {label:<20} run34d={a!r}  reference={b!r}  "
              f"{'MATCH' if match else 'MISMATCH -- PROTOCOL DRIFT'}")
    print(f"  RUN26 CONTROL coverage@{SHORTLIST_K}: {control_cov}")
    print(f"  RUN32 ADAPT coverage@{SHORTLIST_K} (cited): {run32_adapt_cov}")
    print(f"  RUN32 identity entropy (cited): control={run32_ent['identity']['control']} "
          f"adapt={run32_ent['identity']['adapt']}")
    if not ok:
        print("  WALL: a prerequisite is incomplete or mismatched -- this run must NOT proceed.")
        return 1
    print("  RECIPE VERIFIED -- proceeding.")
    _save_json(dict(verified=True, control_top=control_meta["grain_report"].get("top"),
                     control_coverage=control_cov, run32_adapt_coverage=run32_adapt_cov,
                     run32_entropy_control=run32_ent["identity"]["control"],
                     run32_entropy_adapt=run32_ent["identity"]["adapt"]),
               _ckpt("verify.json"))
    print(f"  saved -> {_ckpt('verify.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: gather-edges -- gather the SAME 1500-stroke LEARN population, DENOISE each stroke,
# extract raw per-segment turn/length values (StrokeQuantize @ bins=1, emit_residual, run32's
# own `adaptive_bins.gather_learn_span_values`, UNMODIFIED), then compute quantile/equal-mass
# edges (`adaptive_bins.compute_adaptive_edges`, UNMODIFIED -- dedupe + strictly-increasing
# guards apply exactly as in run 32; the denoised distribution may still carry a partial
# point-mass near 0 deg per 34c's own 1-identity finding, so the guard is not academic here).
# Batch-checkpointed (denoise dominates cost) -- re-invoke until COMPLETE.
# ---------------------------------------------------------------------------------------------
def stage_gather_edges():
    print(f"\n{SEP}\n  STAGE: gather-edges (RUN 34d -- quantile edges from the DENOISED LEARN population)\n{SEP}")
    if not os.path.exists(_ckpt("verify.json")):
        print("  WALL: run stage 'verify' first.")
        return 1
    out_path = _ckpt("edges_report.json")
    if os.path.exists(out_path):
        print(f"  gather-edges already COMPLETE -- {out_path}")
        report = _load_json(out_path)
        print(f"  turn_edges={report['turn_edges']}")
        print(f"  len_edges={report['len_edges']}")
        return 0

    progress_path = _ckpt("gather_progress.json")
    if os.path.exists(progress_path):
        prog = _load_json(progress_path)
        print(f"  RESUMING at stroke {prog['n_done']}/{LEARN_STROKE_CAP}")
    else:
        prog = dict(n_done=0, turn=[], len=[])

    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    strokes = _collect_learn_strokes_tagged(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
    print(f"  LEARN population: {len(strokes)} strokes  DENOISE=global before edge-fitting")

    s, _ag, _native = gate.boot()   # scratch boot -- gather is a throwaway-ink measurement,
                                     # no growth carried across batches or invocations.
    t0 = time.time()
    total = len(strokes)
    while prog["n_done"] < total and (time.time() - t0) < PER_CALL_BUDGET_SECONDS:
        batch = strokes[prog["n_done"]:prog["n_done"] + BATCH_STROKES]
        tb = time.time()
        for (points, d, alph, char) in batch:
            dpts = _dn(points)
            lv = ab.gather_learn_span_values(s, [dpts], segments=DK["segments"],
                                              max_knots=DK["max_knots"])
            prog["turn"].extend(lv["turn"])
            prog["len"].extend(lv["len"])
            prog["n_done"] += 1
        _save_json(prog, progress_path)
        print(f"  [batch] {prog['n_done']}/{total} strokes  turn_vals={len(prog['turn'])}  "
              f"len_vals={len(prog['len'])}  batch_wall={time.time()-tb:.1f}s  checkpointed.")

    if prog["n_done"] < total:
        print(f"\n  PARTIAL: {prog['n_done']}/{total} strokes -- re-invoke '--stage gather-edges' "
              f"to continue (checkpoints saved).")
        print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
        return 0

    learn_values = dict(turn=prog["turn"], len=prog["len"], n_strokes=total,
                         n_spans=len(prog["turn"]) + 0)
    report = ab.compute_adaptive_edges(learn_values, turn_bins=DK["turn_bins"],
                                        len_bins=DK["len_bins"])
    print(f"  METHOD: {report['method']} (dedupe min_width_frac={ab.MIN_BIN_WIDTH_FRAC})")
    print(f"  turn_edges: requested {report['turn_bins_requested']} bins -> "
          f"{report['turn_bins_effective']} EFFECTIVE after dedupe: "
          f"{[round(v, 2) for v in report['turn_edges']]}")
    print(f"  len_edges:  requested {report['len_bins_requested']} bins -> "
          f"{report['len_bins_effective']} EFFECTIVE after dedupe: "
          f"{[round(v, 4) for v in report['len_edges']]}")
    t_occ, l_occ = report["turn_occupancy"], report["len_occupancy"]
    print(f"  TURN occupancy entropy (denoised): {t_occ['entropy_bits']:.4f} bits "
          f"(max {t_occ['max_entropy_bits']:.4f})  counts={t_occ['counts']}")
    print(f"  LEN  occupancy entropy (denoised): {l_occ['entropy_bits']:.4f} bits "
          f"(max {l_occ['max_entropy_bits']:.4f})  counts={l_occ['counts']}")
    run32_edges = _load_json(_run32("edges_report.json"))
    print(f"  (cited RUN32 raw-points turn_edges effective bins: "
          f"{run32_edges['turn_bins_effective']}, TURN occupancy entropy: "
          f"{run32_edges['turn_occupancy']['entropy_bits']:.4f} bits -- comparison point for "
          f"how much denoising alone changes edge placement)")

    _save_json(report, out_path)
    for p in (progress_path,):
        if os.path.exists(p):
            os.remove(p)
    print(f"  saved -> {out_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _load_edges():
    report = _load_json(_ckpt("edges_report.json"))
    return report["turn_edges"], report["len_edges"]


# ---------------------------------------------------------------------------------------------
# STAGE: learn -- fresh LEARN pass: every raw stroke DENOISED, decoded under the DENOISED
# ADAPTIVE edges from gather-edges. Batch-checkpointed (graph+meta together every batch, run
# 31/32's stress-gated pattern), re-invoke until COMPLETE. Intra-stage RUNAWAY guard (run 32's
# amendment) aborts if the codebook explodes mid-learn.
# ---------------------------------------------------------------------------------------------
def stage_learn():
    print(f"\n{SEP}\n  STAGE: learn (RUN 34d -- DENOISE + ADAPTIVE EDGES, the interaction cell)\n{SEP}")
    out_graph, out_meta = _ckpt("learn.json"), _ckpt("learn_meta.json")
    if os.path.exists(out_graph) and os.path.exists(out_meta):
        print(f"  learn already COMPLETE -- {out_graph}")
        return 0
    if not os.path.exists(_ckpt("edges_report.json")):
        print("  WALL: run stage 'gather-edges' first.")
        return 1
    turn_edges, len_edges = _load_edges()

    control_meta = _load_json(_run26("learn_meta.json"))
    control_top = control_meta["grain_report"].get("top", control_meta["grain_report"].get("total"))
    runaway_cap = max(50.0, RUNAWAY_FACTOR * float(control_top))

    partial_graph, progress_path = _ckpt("learn_partial.json"), _ckpt("learn_progress.json")
    if os.path.exists(partial_graph) and os.path.exists(progress_path):
        s = _load_graph(partial_graph)
        prog = _load_json(progress_path)
        print(f"  RESUMING at stroke {prog['n_done']}/{LEARN_STROKE_CAP} "
              f"(codebook top so far: {prog.get('last_top')})")
    else:
        s, ag_node, native = gate.boot()
        prog = dict(n_done=0, growth=[], win_recognized=0, win_oov=0, win_minted=0,
                    win_codebook_start=len(sc._existing_names(s, "stroke")),
                    n_degenerate_skipped=0, elapsed_total=0.0, last_top=None)
        print(f"  FRESH boot -- codebook at boot: {prog['win_codebook_start']} stroke quanta")

    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    strokes = _collect_learn_strokes_tagged(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
    print(f"  LEARN alphabets: {learn_alphabets}  drawers {LEARN_DRAWERS[0]}-{LEARN_DRAWERS[-1]}  "
          f"population={len(strokes)}  DK={DK}  DENOISE=global  "
          f"ADAPTIVE EDGES: turn={len(turn_edges)-1} eff bins, len={len(len_edges)-1} eff bins")

    t0 = time.time()
    total = len(strokes)
    while prog["n_done"] < total and (time.time() - t0) < PER_CALL_BUDGET_SECONDS:
        batch = strokes[prog["n_done"]:prog["n_done"] + BATCH_STROKES]
        tb = time.time()
        for (points, d, alph, char) in batch:
            dpts = _dn(points)
            ink_node = ink.ingest_ink(s, dpts, writer=f"bg_{d}", max_knots=DK["max_knots"])
            res = ink.decode_ink(s, ink_node, writer=f"bg_{d}", min_span=DK["min_span"],
                                  max_span=DK["max_span"], segments=DK["segments"],
                                  turn_bins=DK["turn_bins"], len_bins=DK["len_bins"],
                                  grid=DK["grid"], scale_bins=DK["scale_bins"],
                                  enable_substroke=True,
                                  turn_edges=turn_edges, len_edges=len_edges)
            prog["n_done"] += 1
            prog["win_recognized"] += len(res["recognized"])
            prog["win_oov"] += len(res["oov"])
            prog["win_minted"] += len(res["minted"])
            if prog["n_done"] % GROWTH_WINDOW == 0:
                cb = len(sc._existing_names(s, "stroke"))
                reuse = prog["win_recognized"] / max(1, prog["win_recognized"] + prog["win_oov"])
                prog["growth"].append({
                    "n": prog["n_done"], "codebook": cb,
                    "new_quanta": cb - prog["win_codebook_start"],
                    "recognized": prog["win_recognized"], "oov": prog["win_oov"],
                    "minted": prog["win_minted"], "reuse_rate": reuse,
                })
                prog["win_codebook_start"] = cb
                prog["win_recognized"] = prog["win_oov"] = prog["win_minted"] = 0

        grain_now = sc.grain_vocabulary_report(s)
        prog["last_top"] = grain_now["top"]
        prog["elapsed_total"] += time.time() - tb
        _save_graph(s, partial_graph)
        _save_json(prog, progress_path)
        print(f"  [batch] {prog['n_done']}/{total} strokes  codebook_top={grain_now['top']}  "
              f"total={grain_now['total']}  batch_wall={time.time()-tb:.1f}s  checkpointed.")

        if grain_now["top"] > runaway_cap:
            prog["runaway_abort"] = dict(top=grain_now["top"], cap=runaway_cap,
                                          control_top=control_top)
            _save_json(prog, progress_path)
            print(f"\n  *** RUNAWAY ABORT: codebook top {grain_now['top']} > {runaway_cap} "
                  f"({RUNAWAY_FACTOR}x control {control_top}) -- stopping. ***")
            return 2

    if prog["n_done"] < total:
        print(f"\n  PARTIAL: {prog['n_done']}/{total} strokes -- re-invoke '--stage learn' "
              f"to continue (checkpoints saved).")
        print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
        return 0

    growth = prog["growth"]
    sat_pass = None
    if len(growth) >= 3:
        first = np.mean([g["new_quanta"] for g in growth[:1]])
        last = np.mean([g["new_quanta"] for g in growth[-2:]])
        sat_pass = bool(last <= max(3.0, 0.3 * first) if first > 0 else True)
    grain = sc.grain_vocabulary_report(s)
    print(f"  COMPLETE: {prog['n_done']} strokes in {prog['elapsed_total']:.1f}s total wall. "
          f"saturation={'PASS' if sat_pass else ('FAIL' if sat_pass is False else 'UNKNOWN')}")
    print(f"  codebook grain report: {grain}")

    our_top = grain.get("top", grain.get("total"))
    frag_ratio = (our_top / control_top) if control_top else None
    p3_frag_stop = bool(frag_ratio is not None and frag_ratio > 3.0)
    print(f"  P3 fragmentation check: control_top={control_top}  our_top={our_top}  "
          f"ratio={frag_ratio}  (cited RUN32 ADAPT top=83)  "
          f"{'FLAG -- >3x control' if p3_frag_stop else 'OK'}")

    ab.store_adaptive_edges(s, turn_edges, len_edges)
    _save_graph(s, out_graph)
    _save_json(dict(n_strokes=prog["n_done"], elapsed=prog["elapsed_total"], grain_report=grain,
                     learn_alphabets=learn_alphabets, sat_pass=sat_pass,
                     growth=growth, growth_tail=growth[-3:] if growth else [],
                     turn_edges=turn_edges, len_edges=len_edges,
                     p3_control_top=control_top, p3_our_top=our_top,
                     p3_frag_ratio=frag_ratio, p3_frag_stop=p3_frag_stop),
               out_meta)
    print(f"  saved -> {out_graph}, {out_meta}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: calibrate -- CFAR pass on denoised points, edges-aware, batch-checkpointed.
# ---------------------------------------------------------------------------------------------
def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (RUN 34d -- CFAR, denoised + adaptive edges)\n{SEP}")
    out_graph, out_report = _ckpt("calibrated.json"), _ckpt("calibration_report.json")
    if os.path.exists(out_graph) and os.path.exists(out_report):
        print(f"  calibrate already COMPLETE -- {out_graph}")
        report = _load_json(out_report)
        print(f"  n_families={report.get('n_families')}  n_spans_measured={report.get('n_spans_measured')}")
        return 0

    learn_graph, learn_meta_path = _ckpt("learn.json"), _ckpt("learn_meta.json")
    if not (os.path.exists(learn_graph) and os.path.exists(learn_meta_path)):
        print("  WALL: run stage 'learn' to completion first.")
        return 1
    learn_meta = _load_json(learn_meta_path)
    turn_edges, len_edges = learn_meta["turn_edges"], learn_meta["len_edges"]

    partial_graph, progress_path = _ckpt("calibrate_partial.json"), _ckpt("calibrate_progress.json")
    if os.path.exists(partial_graph) and os.path.exists(progress_path):
        s = _load_graph(partial_graph)
        prog = _load_json(progress_path)
        print(f"  RESUMING measurement at stroke {prog['n_done']}/{LEARN_STROKE_CAP}")
    else:
        s = _load_graph(learn_graph)
        prog = dict(n_done=0, pairs=[])

    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    strokes = run28._collect_learn_strokes(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
    print(f"  LEARN population: {len(strokes)} strokes  DENOISE=global  ADAPTIVE EDGES engaged  "
          f"(margin={nc.DEFAULT_MARGIN}, min_family_samples={nc.DEFAULT_MIN_FAMILY_SAMPLES})")

    t0 = time.time()
    total = len(strokes)
    while prog["n_done"] < total and (time.time() - t0) < PER_CALL_BUDGET_SECONDS:
        batch = strokes[prog["n_done"]:prog["n_done"] + BATCH_STROKES]
        tb = time.time()
        for points in batch:
            pairs = nc._measure_stroke(s, _dn(points), DK, turn_edges=turn_edges, len_edges=len_edges)
            prog["pairs"].extend([[fam, float(d)] for (fam, d) in pairs])
            prog["n_done"] += 1
        _save_graph(s, partial_graph)
        _save_json(prog, progress_path)
        print(f"  [batch] {prog['n_done']}/{total} strokes measured  pairs={len(prog['pairs'])}  "
              f"batch_wall={time.time()-tb:.1f}s  checkpointed.")

    if prog["n_done"] < total:
        print(f"\n  PARTIAL: {prog['n_done']}/{total} strokes -- re-invoke '--stage calibrate' "
              f"to continue (checkpoints saved).")
        print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
        return 0

    try:
        report = nc.calibrate_dtw_thresholds(
            s, [], DK, measured_pairs=[(fam, d) for (fam, d) in prog["pairs"]])
    except nc.EmptyCalibrationError as e:
        print(f"  WALL: EMPTY CALIBRATION -- {e}")
        _save_json(dict(error=str(e)), out_report)
        return 1
    report["n_strokes_measured"] = prog["n_done"]
    print(f"  n_strokes_measured={report['n_strokes_measured']}  "
          f"n_spans_measured={report['n_spans_measured']}  n_families={report['n_families']}")
    print(f"  calibrated_families: {report['calibrated_families']}")
    print(f"  pooled_families (data-starved): {len(report['pooled_families'])}")
    print(f"  global pooled calibration: {report['global']}")

    _save_graph(s, out_graph)
    _save_json(report, out_report)
    print(f"  saved -> {out_graph}, {out_report}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: entropy-report -- P1a (identity-grain entropy) + P1b (class-grain coherence), measured
# on a THROWAWAY copy of THIS run's own calibrated graph, over the SAME 1500-stroke LEARN
# population, denoised + edges-aware, tagged with (alphabet, character, drawer) provenance.
# ---------------------------------------------------------------------------------------------
def stage_entropy_report():
    print(f"\n{SEP}\n  STAGE: entropy-report (P1a identity entropy, P1b class-grain coherence)\n{SEP}")
    calib_graph = _ckpt("calibrated.json")
    if not os.path.exists(calib_graph):
        print("  WALL: run 'calibrate' to completion first.")
        return 1
    turn_edges, len_edges = _load_edges()

    partial_graph, progress_path = _ckpt("entropy_partial.json"), _ckpt("entropy_progress.json")
    done_path = _ckpt("identity_hist.json")
    if os.path.exists(done_path):
        result = _load_json(done_path)
    else:
        if os.path.exists(partial_graph) and os.path.exists(progress_path):
            s = _load_graph(partial_graph)
            prog = _load_json(progress_path)
            print(f"  RESUMING at stroke {prog['n_done']}/{LEARN_STROKE_CAP}")
        else:
            s = _load_graph(calib_graph)
            prog = dict(n_done=0, identity_hist={}, n_mints=0, n_oov=0,
                        coherence={})   # coherence[ident][class_key_str] = [drawers...]

        learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
        strokes = _collect_learn_strokes_tagged(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
        t0 = time.time()
        total = len(strokes)
        while prog["n_done"] < total and (time.time() - t0) < PER_CALL_BUDGET_SECONDS:
            batch = strokes[prog["n_done"]:prog["n_done"] + BATCH_STROKES]
            tb = time.time()
            for (points, d, alph, char) in batch:
                dpts = _dn(points)
                ink_node = ink.ingest_ink(s, dpts, max_knots=DK["max_knots"])
                res = ink.decode_ink(s, ink_node, min_span=DK["min_span"], max_span=DK["max_span"],
                                      segments=DK["segments"], turn_bins=DK["turn_bins"],
                                      len_bins=DK["len_bins"], grid=DK["grid"],
                                      scale_bins=DK["scale_bins"],
                                      turn_edges=turn_edges, len_edges=len_edges)
                class_key = f"{alph}::{char}"
                for r in res.get("recognized", []):
                    ident = r.get("name")
                    if not ident:
                        continue
                    prog["identity_hist"][ident] = prog["identity_hist"].get(ident, 0) + 1
                    slot = prog["coherence"].setdefault(ident, {})
                    drawers = slot.setdefault(class_key, [])
                    if d not in drawers:
                        drawers.append(d)
                prog["n_mints"] += len(res.get("minted", []))
                prog["n_oov"] += len(res.get("oov", []))
                prog["n_done"] += 1
            _save_graph(s, partial_graph)
            _save_json(prog, progress_path)
            print(f"  [batch] {prog['n_done']}/{total}  identities={len(prog['identity_hist'])}  "
                  f"batch_wall={time.time()-tb:.1f}s  checkpointed.")

        if prog["n_done"] < total:
            print(f"\n  PARTIAL: {prog['n_done']}/{total} strokes -- re-invoke "
                  f"'--stage entropy-report' to continue.")
            print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
            return 0

        result = dict(identity_hist=prog["identity_hist"], coherence=prog["coherence"],
                      n_mints_during_measurement=prog["n_mints"], n_oov=prog["n_oov"],
                      n_strokes=prog["n_done"])
        _save_json(result, done_path)
        for p in (partial_graph, progress_path):
            if os.path.exists(p):
                os.remove(p)

    # P1a -- Shannon entropy over the identity histogram.
    hist = result["identity_hist"]
    n_obs = sum(hist.values())
    n_ids = len(hist)
    if n_obs > 0 and n_ids > 0:
        probs = np.array(list(hist.values()), dtype=float) / n_obs
        entropy_bits = float(-(probs * np.log2(probs)).sum())
        max_entropy = float(np.log2(n_ids)) if n_ids > 1 else 0.0
        top_share = float(max(hist.values()) / n_obs)
    else:
        entropy_bits = max_entropy = top_share = 0.0
    print(f"\n  P1a IDENTITY-GRAIN ENTROPY (this run, denoised+adaptive-edges): "
          f"n={n_obs}  ids={n_ids}  entropy={entropy_bits:.4f} bits "
          f"(max {max_entropy:.4f})  top_share={top_share:.4f}")
    run32_ent = _load_json(_run32("entropy_report.json"))["identity"]
    print(f"  cited CONTROL (run26/28, raw uniform, undenoised): "
          f"{run32_ent['control']['entropy_bits']:.4f} bits / {run32_ent['control']['n_families']} ids")
    print(f"  cited RUN32 ADAPT (adaptive edges, undenoised): "
          f"{run32_ent['adapt']['entropy_bits']:.4f} bits / {run32_ent['adapt']['n_families']} ids "
          f"(top_family_share={run32_ent['adapt']['top_family_share']:.4f})")
    p1a_spread = bool(entropy_bits > run32_ent["control"]["entropy_bits"] + 0.1 and
                       n_ids > run32_ent["control"]["n_families"])
    p1a_vs_adapt = "similar-or-higher" if entropy_bits >= run32_ent["adapt"]["entropy_bits"] - 0.5 \
        else "LOWER than run32 ADAPT"
    print(f"  P1a (spread vs CONTROL): {'CONFIRMED' if p1a_spread else 'NULL -- stayed ~0'}  "
          f"  vs RUN32 ADAPT: {p1a_vs_adapt}")

    # P1b -- class-grain coherence fraction (34c's own metric).
    coherence = result["coherence"]
    n_distinct_ids = len(coherence)
    n_coherent = 0
    per_id_best = {}
    for ident, classes in coherence.items():
        best = max((len(drawers) for drawers in classes.values()), default=0)
        per_id_best[ident] = best
        if best >= 3:
            n_coherent += 1
    coherence_frac = (n_coherent / n_distinct_ids) if n_distinct_ids else 0.0
    print(f"\n  P1b CLASS-GRAIN COHERENCE: {n_coherent}/{n_distinct_ids} identities have >=1 "
          f"class reached by >=3 distinct drawers  fraction={coherence_frac:.4f}")
    print(f"  (cited RUN32 ADAPT coherence: ~0 by inspection -- 82/83 ids were single-drawer "
          f"ref_turn children of ONE root; never formally measured there)")
    print(f"  per-identity best same-class drawer-span (top 10 by occurrence count): " +
          ", ".join(f"{k}={v}" for k, v in
                    sorted(per_id_best.items(), key=lambda kv: -hist.get(kv[0], 0))[:10]))

    interaction_shape = (
        "INTERACTION CONFIRMED (entropy spread + materially higher coherence than run32 ADAPT)"
        if (p1a_spread and coherence_frac > 0.15) else
        "MECHANISM-ONLY (entropy spread but coherence stayed low -- fragmentation persists)"
        if p1a_spread else
        "FRAGMENTATION-REPEAT (entropy did not spread beyond control under denoise+edges)"
    )
    print(f"\n  P1 INTERACTION VERDICT: {interaction_shape}")

    out = dict(identity=dict(n_observations=n_obs, n_ids=n_ids, entropy_bits=entropy_bits,
                             max_entropy_bits=max_entropy, top_share=top_share,
                             p1a_spread_vs_control=p1a_spread),
               coherence=dict(n_distinct_ids=n_distinct_ids, n_coherent=n_coherent,
                              coherence_fraction=coherence_frac, per_id_best=per_id_best),
               interaction_shape=interaction_shape,
               cited_run32=run32_ent)
    _save_json(out, _ckpt("entropy_report.json"))
    print(f"\n  saved -> {_ckpt('entropy_report.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# LOCAL decode_char_signature clone -- BYTE-IDENTICAL to `gate.decode_char_signature`'s
# ingest/decode/compose recipe (the composed_sig arm ONLY), with TWO changes: every raw stroke
# is denoised before `ink.ingest_ink`, AND `turn_edges`/`len_edges` thread into `ink.decode_ink`
# (`compose_character_signature` itself needs neither -- it composes from already-resolved
# stroke_points/identities, not raw geometry). `scripts/jabberwock_omniglot_dynamic_
# quantization.py` (the shared "gate" module) is NOT modified -- this is a new, separate
# function in this script only.
# ---------------------------------------------------------------------------------------------
def _decode_char_signature_denoised_edges(s, path, cache, dk, turn_edges, len_edges) -> dict:
    cached = cache.get(path)
    if cached is not None:
        return cached
    stroke_points = []
    for st in ow.load_strokes(path):
        if st.shape[0] < 2:
            continue
        dpts = _dn(st.tolist())
        ink_node = ink.ingest_ink(s, dpts, max_knots=dk["max_knots"])
        res = ink.decode_ink(s, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                              segments=dk["segments"], turn_bins=dk["turn_bins"],
                              len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
                              enable_substroke=True, turn_edges=turn_edges, len_edges=len_edges)
        knots = s.node(ink_node)["attrs"].get("knots") or []
        stroke_points.extend(cc.decode_result_to_stroke_points(knots, res))
    composed = cc.compose_character_signature(
        s._inner, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
    out = dict(composed_sig=composed["signature"])
    cache[path] = out
    return out


# ---------------------------------------------------------------------------------------------
# STAGE: eval -- P2, coverage@10 at n=400, SAME protocol as run17b/25/26/32/34c's own C0, on
# THIS run's denoised+adaptive-edges+calibrated graph via `_decode_char_signature_denoised_edges`.
# Block-checkpointed.
# ---------------------------------------------------------------------------------------------
def stage_eval():
    print(f"\n{SEP}\n  STAGE: eval (RUN 34d -- P2 coverage@{SHORTLIST_K})\n{SEP}")
    graph_src = _ckpt("calibrated.json")
    if not os.path.exists(graph_src):
        print("  WALL: run 'calibrate' to completion first.")
        return 1
    turn_edges, len_edges = _load_edges()

    out_path = _ckpt("eval.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval already COMPLETE (n={len(state['records'])}).")
        return 0

    s = _load_graph(graph_src)
    native = s._inner
    cache: dict = {}    # in-process only, block boundaries are the checkpoint unit.

    test_alphabets = run29._test_alphabets()
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  test_alphabets={test_alphabets}  blocks={len(blocks)} "
          f"(target n={len(blocks) * WAY})  SHORTLIST_K={SHORTLIST_K}  "
          f"resuming at block {state['block_idx']}")

    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        alph, r = blocks[i]
        run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)

    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
        drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]

        full_dwell_this_block = (state["block_idx"] == 0)     # anomaly spot-check only.
        scratch0 = cand0 = None
        if full_dwell_this_block:
            scratch0 = srs.Substrate()
            _, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                                thetas=ar.DEFAULT_PARSE_THETAS)

        exemplars = [_decode_char_signature_denoised_edges(s, drawer_files[ci][ex_drawer], cache,
                                                            DK, turn_edges, len_edges)
                     for ci in range(WAY)]
        exemplar_composed = [e["composed_sig"] for e in exemplars]

        for qi, q_drawer in spec["queries"]:
            path = drawer_files[qi][q_drawer]
            rec = {"true": qi, "alph": alph, "r": r}
            if full_dwell_this_block:
                qn0 = ar.stage_parse_char(scratch0, path, is_query=True,
                                          thetas=ar.DEFAULT_PARSE_THETAS,
                                          denoise=True, denoise_kwargs={"mode": "global"})
                w0 = ar.parse_marginal_verdict(scratch0, qn0)
                rec["pred_full"] = cand0.get(w0, -1) if w0 is not None else -1

            qd = _decode_char_signature_denoised_edges(s, path, cache, DK, turn_edges, len_edges)
            shortlist = ar.propose_top_k(native, qd["composed_sig"], exemplar_composed,
                                          k=SHORTLIST_K)
            rec["in_shortlist"] = bool(qi in shortlist)
            state["records"].append(rec)

        state["block_idx"] += 1
        _save_json(state, out_path)
        print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
              f"{len(state['records'])} episodes so far, {time.time()-t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        records = state["records"]
        n = len(records)
        k_cov = sum(1 for r in records if r["in_shortlist"])
        state["coverage"] = dict(cov=(k_cov / n if n else 0.0), ci=list(wilson_ci(k_cov, n)),
                                 k=k_cov, n=n)
        full_records = [r for r in records if "pred_full" in r]
        if full_records:
            k_full = sum(1 for r in full_records if r["pred_full"] == r["true"])
            state["full_dwell"] = dict(acc=k_full / len(full_records),
                                       ci=list(wilson_ci(k_full, len(full_records))),
                                       n=len(full_records), k=k_full)
        state["done"] = True
        _save_json(state, out_path)
        cov = state["coverage"]
        print(f"\n  EVAL COMPLETE: n={n}  coverage@{SHORTLIST_K}={100*cov['cov']:.1f}%  "
              f"95% CI [{100*cov['ci'][0]:.1f}%, {100*cov['ci'][1]:.1f}%]  k={cov['k']}")
        if "full_dwell" in state:
            fd = state["full_dwell"]
            print(f"  full-dwell block-0 spot-check: {100*fd['acc']:.1f}% (n={fd['n']}) -- "
                  f"anomaly check only, not a pre-registered prediction of this run.")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- "
              f"re-invoke '--stage eval' to continue.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: falsenovelty -- P4, 0/50 false-mint probe on this run's own calibrated graph, denoised
# AND edges-aware (`run28_plastic._count_false_novelty` does NOT thread turn_edges/len_edges --
# fine for run32/34c's own codebooks, wrong here since this codebook was grown under adaptive
# edges; a mismatched bin boundary would misclassify every probe span as OOV, a false ANOMALY,
# not a real false-novelty measurement. This script defines its own edges-aware clone below,
# in this file only -- `run28_plastic.py` itself is never touched.)
# ---------------------------------------------------------------------------------------------
def _count_false_novelty_denoised(s, probe_strokes: list, dk: dict, turn_edges, len_edges) -> int:
    total = 0
    for points in probe_strokes:
        dpts = _dn(points)
        ink_node = ink.ingest_ink(s, dpts, max_knots=dk["max_knots"])
        res = ink.decode_ink(s, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                              segments=dk["segments"], turn_bins=dk["turn_bins"],
                              len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
                              turn_edges=turn_edges, len_edges=len_edges)
        total += len(res.get("minted", []))
    return total


def stage_falsenovelty():
    print(f"\n{SEP}\n  STAGE: falsenovelty (RUN 34d -- P4, edges-aware false-novelty probe)\n{SEP}")
    graph_src = _ckpt("calibrated.json")
    if not os.path.exists(graph_src):
        print("  WALL: run 'calibrate' to completion first.")
        return 1
    turn_edges, len_edges = _load_edges()
    out_path = _ckpt("falsenovelty.json")
    if os.path.exists(out_path):
        result = _load_json(out_path)
        print(f"  falsenovelty already COMPLETE -- {result['false_novelty']}/{result['n_probe']}")
        return 0

    s = _load_graph(graph_src)
    probe = run28._build_false_novelty_probe()
    count = _count_false_novelty_denoised(s, probe, DK, turn_edges, len_edges)
    print(f"  false_novelty={count}/{len(probe)}  {'PASS (0/50)' if count == 0 else 'ANOMALY -- nonzero'}")
    result = dict(false_novelty=count, n_probe=len(probe))
    _save_json(result, out_path)
    print(f"  saved -> {out_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: report -- final verdicts, P1-P4, honest anomalies, the 2x2 completion statement.
# ---------------------------------------------------------------------------------------------
def stage_report():
    print(f"\n{SEP}\n  RUN 34d -- THE FINAL 2x2 CELL -- FINAL REPORT\n{SEP}")

    def _opt(name):
        p = _ckpt(name)
        return _load_json(p) if os.path.exists(p) else None

    learn_meta = _opt("learn_meta.json")
    ent = _opt("entropy_report.json")
    ev = _opt("eval.json")
    fn = _opt("falsenovelty.json")

    print(f"\n  CONTROLS (cited, never re-run):")
    print(f"    RUN26 CONTROL (uniform/raw):    coverage@{SHORTLIST_K}="
          f"{100*RUN26_CONTROL_COVERAGE['cov']:.1f}% "
          f"[{100*RUN26_CONTROL_COVERAGE['ci'][0]:.1f},{100*RUN26_CONTROL_COVERAGE['ci'][1]:.1f}]  "
          f"n={RUN26_CONTROL_COVERAGE['n']}")
    print(f"    RUN32 ADAPT (adaptive/raw):     coverage@{SHORTLIST_K}="
          f"{100*RUN32_ADAPT_COVERAGE['cov']:.1f}% "
          f"[{100*RUN32_ADAPT_COVERAGE['ci'][0]:.1f},{100*RUN32_ADAPT_COVERAGE['ci'][1]:.1f}]  "
          f"n={RUN32_ADAPT_COVERAGE['n']}  entropy=3.9968 bits/83 ids, INSTANCE-grain")
    print(f"    RUN34C (uniform/denoised):      coverage@{SHORTLIST_K}=72.0% [67.4,76.2]  "
          f"entropy~0 bits/1 id")

    if ent:
        ida = ent["identity"]
        coh = ent["coherence"]
        print(f"\n  P1a IDENTITY ENTROPY (denoised + adaptive edges): {ida['entropy_bits']:.4f} bits "
              f"/ {ida['n_ids']} ids  top_share={ida['top_share']:.4f}")
        print(f"    vs RUN26/28 CONTROL: {ent['cited_run32']['control']['entropy_bits']:.4f} bits / "
              f"{ent['cited_run32']['control']['n_families']} ids")
        print(f"    vs RUN32 ADAPT (undenoised): {ent['cited_run32']['adapt']['entropy_bits']:.4f} "
              f"bits / {ent['cited_run32']['adapt']['n_families']} ids")
        print(f"  P1b CLASS-GRAIN COHERENCE: {coh['n_coherent']}/{coh['n_distinct_ids']} = "
              f"{coh['coherence_fraction']:.4f}  (cited RUN32 ADAPT: ~0, 82/83 single-drawer)")
        print(f"  P1 INTERACTION VERDICT: {ent.get('interaction_shape')}")
    else:
        print("\n  P1: entropy-report not yet complete.")

    if learn_meta:
        print(f"\n  P3 SATURATION/FRAGMENTATION: sat_pass={learn_meta.get('sat_pass')}  "
              f"control_top={learn_meta.get('p3_control_top')}  "
              f"our_top={learn_meta.get('p3_our_top')}  (cited RUN32 ADAPT top=83)  "
              f"ratio={learn_meta.get('p3_frag_ratio')}  "
              f"frag_stop={learn_meta.get('p3_frag_stop')}")
    else:
        print("\n  P3: learn_meta.json not yet present.")

    if ev and ev.get("done"):
        cov = ev["coverage"]
        sep_control = _ci_separated(tuple(cov["ci"]), tuple(RUN26_CONTROL_COVERAGE["ci"]))
        sep_adapt = _ci_separated(tuple(cov["ci"]), tuple(RUN32_ADAPT_COVERAGE["ci"]))
        print(f"\n  P2 COVERAGE@{SHORTLIST_K} (THE DELIVERABLE): n={cov['n']}  "
              f"{100*cov['cov']:.1f}% [{100*cov['ci'][0]:.1f}%, {100*cov['ci'][1]:.1f}%]")
        print(f"    vs RUN26 CONTROL {100*RUN26_CONTROL_COVERAGE['cov']:.1f}% "
              f"[{100*RUN26_CONTROL_COVERAGE['ci'][0]:.1f}%,{100*RUN26_CONTROL_COVERAGE['ci'][1]:.1f}%]  "
              f"CI-separated: {sep_control}")
        print(f"    vs RUN32 ADAPT   {100*RUN32_ADAPT_COVERAGE['cov']:.1f}% "
              f"[{100*RUN32_ADAPT_COVERAGE['ci'][0]:.1f}%,{100*RUN32_ADAPT_COVERAGE['ci'][1]:.1f}%]  "
              f"CI-separated: {sep_adapt}")
        base_recs_path = _run26("eval_baseline.json")
        run32_adapt_eval_path = _run32("eval_adapt.json")
        if os.path.exists(base_recs_path):
            base_records = _load_json(base_recs_path)["records"]
            n_align = min(len(base_records), len(ev["records"]))
            newly = sum(1 for i in range(n_align)
                        if ev["records"][i]["in_shortlist"] and not base_records[i]["in_shortlist"])
            lost = sum(1 for i in range(n_align)
                       if not ev["records"][i]["in_shortlist"] and base_records[i]["in_shortlist"])
            print(f"    episode residual vs RUN26 CONTROL (aligned n={n_align}, SAME POWER_SEED/"
                  f"block order): newly_covered={newly}  lost={lost}")
        if os.path.exists(run32_adapt_eval_path):
            adapt_records = _load_json(run32_adapt_eval_path)["records"]
            n_align2 = min(len(adapt_records), len(ev["records"]))
            newly2 = sum(1 for i in range(n_align2)
                        if ev["records"][i]["in_shortlist"] and not adapt_records[i]["in_shortlist"])
            lost2 = sum(1 for i in range(n_align2)
                       if not ev["records"][i]["in_shortlist"] and adapt_records[i]["in_shortlist"])
            print(f"    episode residual vs RUN32 ADAPT (aligned n={n_align2}): "
                  f"newly_covered={newly2}  lost={lost2}")
        if "full_dwell" in ev:
            fd = ev["full_dwell"]
            print(f"    full-dwell block-0 anomaly check: {100*fd['acc']:.1f}% (n={fd['n']})")
    else:
        print("\n  P2: eval not yet complete.")

    if fn:
        print(f"\n  P4 FALSE-NOVELTY PROBE: {fn['false_novelty']}/{fn['n_probe']}  "
              f"{'PASS' if fn['false_novelty'] == 0 else 'ANOMALY'}")
    else:
        print("\n  P4: falsenovelty not yet complete.")

    if ent and ev and ev.get("done"):
        p1_frag_repeat = "FRAGMENTATION-REPEAT" in ent.get("interaction_shape", "") or \
            "MECHANISM-ONLY" in ent.get("interaction_shape", "")
        cov = ev["coverage"]
        p2_null = not _ci_separated(tuple(cov["ci"]), tuple(RUN26_CONTROL_COVERAGE["ci"]))
        if p1_frag_repeat and p2_null:
            print(f"\n  *** 2x2 COMPLETE: every cell of the mouse-observation-model x bin-"
                  f"placement matrix is now measured. Neither axis alone (run32 ADAPT, run34c "
                  f"denoise) nor both together (this run) move coverage@{SHORTLIST_K} beyond "
                  f"this featureset's ~70-72% band. The mousewriting stroke featureset is "
                  f"CLOSED at every measured cell. ***")
        elif not p1_frag_repeat and p2_null:
            print(f"\n  *** MECHANISM REVIVED, PROPOSAL-LAYER FLAT: P1 shows the interaction "
                  f"is real at the identity-coherence level, but P2 coverage still nulls at "
                  f"power vs RUN26 CONTROL -- report both, do not collapse to one verdict. ***")
        elif not p2_null:
            print(f"\n  *** P2 MOVEMENT: coverage@{SHORTLIST_K} is CI-separated from RUN26 "
                  f"CONTROL -- the FIRST proposal-layer movement in this featureset's history. "
                  f"Report the direction and magnitude precisely. ***")

    _save_json(dict(control=RUN26_CONTROL_COVERAGE, run32_adapt=RUN32_ADAPT_COVERAGE,
                     entropy=ent, learn_meta=learn_meta, eval=ev, falsenovelty=fn),
               _ckpt("report.json"))
    print(f"\n  saved -> {_ckpt('report.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# MAIN
# ===============================================================================================
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["verify", "gather-edges", "learn", "calibrate", "entropy-report",
                             "eval", "falsenovelty", "report"])
    args = p.parse_args()
    t0 = time.time()
    rc = {
        "verify": stage_verify,
        "gather-edges": stage_gather_edges,
        "learn": stage_learn,
        "calibrate": stage_calibrate,
        "entropy-report": stage_entropy_report,
        "eval": stage_eval,
        "falsenovelty": stage_falsenovelty,
        "report": stage_report,
    }[args.stage]()
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
