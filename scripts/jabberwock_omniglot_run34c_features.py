"""OMNIGLOT RUN 34c -- THE DENOISE-FEATURES ARM: DOES DE-STAIRCASING FIX CLASS-GRAIN COHERENCE?

THE REMAINING CELL of the mouse-observation-model matrix (run 34/34b, commits 70bdfc01/
fb31eacc): Gate-0b PASSED (the GLOBAL constrained smoother `mouse_model.denoise_path_global`
dissolves the pixel staircase 89.6%, passes curved 0.186px + straight-line 0.153px fidelity).
DENOISE-VERDICT (34b) NULLED at the continuous comparator (83.5% raw vs 82.8% denoised, n=400,
CIs overlapping) -- expected, since SC+TPS already absorbs pixel noise upstream of any bin.
DENOISE-FEATURES is the other arm, never run: pixel-staircase noise was always more plausibly a
QUANTIZED-features problem than a continuous-comparator one, because run 32 (commit 13ebc282)
showed stroke IDENTITIES revive under finer bins but FRAGMENT at INSTANCE grain (each drawer's
own staircase noise mints its own near-duplicate quantum: identity entropy rose 0.0014->4.0
bits but over 83 largely-singleton per-drawer refinements of ONE root stroke, not per-CHARACTER
structure) -- and pixel-staircase noise IS instance noise, drawer-specific mouse-sensor
artifact, not character-level signal. This run asks: does the GLOBAL denoiser, run BEFORE
quantization (not after, as a bin-placement fix like run 32's adaptive edges), collapse that
instance-level noise back out and let the SAME UNIFORM bins recover class-grain coherence
instead of drawer-instance fragmentation -- and does that move the PROPOSAL metric,
coverage@10?

ISOLATING THE VARIABLE (pre-registered): UNIFORM DK bins throughout (`gate.DK`, byte-identical
bin COUNT and PLACEMENT to run26's own control recipe) -- run 32's adaptive (quantile) edges
are DELIBERATELY NOT used here, so any effect measured is attributable to denoising ALONE, not
to bin placement (the two levers must never be conflated: run 32 already isolated placement-at-
fixed-noise, this run isolates noise-at-fixed-placement). The ONE variable changed vs CONTROL:
every raw stroke passes through `mouse_model.denoise_path_global` (RUN 34b's own principled
GLOBAL inverse, default params, `mode="global"`) once, at ingest, before any decode -- LEARN,
calibration, evaluation, and the round-trip practice pass all consume denoised points, mirroring
`abs_read.stage_parse_char`'s own established "denoise the file's raw strokes ONCE, feed the
SAME denoised strokes everywhere downstream" convention (34's own DENOISE-VERDICT arm).

WHY A NEW SCRIPT, NOT A NEW ARM ON AN EXISTING ONE: `domains/mouse_model.py`, `ink_decode.py`,
`abs_read.py`, `novelty_calibration.py`, `stroke_codebook.py`, `homework_loop.py`, and
`scripts/jabberwock_omniglot_dynamic_quantization.py` are shared, parallel-session-owned
modules (the run34/34b mouse arc's own wiring lives there, `denoise=False` default everywhere,
additive). This script touches NONE of them. Every denoise/mouse-render injection point below
is either (a) a pre-registered kwarg call already landed and additive (`ink.ingest_ink`'s own
`denoise=`, `abs_read.stage_parse_char`'s own `denoise=`), or (b) a raw-point pre-processing
step performed IN THIS SCRIPT before handing already-denoised points to an UNMODIFIED shared
function (the `stage_parse_char` convention, generalized), or (c) for the ONE place no kwarg
exists (`domains.homework_loop`'s private `_decode_stroke_full`/`_render_parse`, used inside
`mark_characters` for the round-trip pass), an IN-PROCESS module-attribute rebind performed by
THIS SCRIPT ONLY (never touching the .py file on disk) -- the exact "redirect a module-level
binding without editing the source" pattern run 32's own `sc.teach = _isolated_teach` seed-
isolation already established as legitimate in this codebase (CLAUDE.md's "cache for
performance, substrate is the source of truth" -- this is a process-local dispatch swap, not an
agent decision, not persisted, not visible to any other process/session).

PRE-REGISTERED CONTROLS (CITED, never re-run/re-grown -- read-only reference data):
  RUN26_CONTROL      = results/run26_checkpoints/eval_baseline.json
                       coverage@10 = 71.5% [66.9, 75.7]  (k=286/400)
                       shortlist_acc = 62.0% [57.2, 66.6]  full_dwell = 80.5% [76.3, 84.1]
  RUN32_ENTROPY      = results/run32_checkpoints/entropy_report.json  (READ-ONLY, IDENTITY grain)
                       control (raw uniform bins):  0.0014 bits / 2 ids  (top_family_share ~1.0)
                       adapt   (adaptive bins, undenoised): 4.00 bits / 83 ids (instance-grain
                       fragmentation -- 82 of 83 are `stroke_18814ab760d8__ref_turn_*` children
                       of ONE root, i.e. per-drawer refinements, not per-character structure)
  RUN27_ARRANGEMENT  = 0.8356  (`results/omniglot_gate_run27.log`'s own round-trip unweighted
                       arrangement subscore, mean_score=0.9376, surviving=39/40, n=40 practice
                       characters)

PRE-REGISTERED METRIC DEFINITIONS (stated before any number below is computed):
  P1a. IDENTITY-GRAIN ENTROPY (Shannon bits, base 2) of `res["name"]` (the deepest-match
       identity, the value downstream composition actually consumes -- run 32's own P2 grain)
       over the population of every ACCEPTED span (any tier) decoded from the SAME 1500-stroke
       LEARN population (background[:5], drawers 01-14), measured on THIS run's OWN denoised +
       calibrated graph -- directly comparable to RUN32_ENTROPY's two cited rows (SAME
       population, SAME grain, SAME measurement method: `_measure_identity_hist`-equivalent
       decode-and-histogram over a THROWAWAY graph copy).
  P1b. CLASS-GRAIN COHERENCE FRACTION (this run's own new metric, not measured by run 32):
       for every stroke occurrence in the P1a population, record the triple (identity_name,
       class_key, drawer) where `class_key = (alphabet, character_dir_basename)` and `drawer`
       is the two-digit Omniglot drawer id ("01".."14") the occurrence's SOURCE FILE was drawn
       by. For each DISTINCT identity name observed >=1 time: it is COHERENT iff there EXISTS
       at least one class_key such that the set of distinct drawers producing that
       (identity, class_key) pair has size >= 3 (i.e. the SAME stroke quantum was independently
       recognized in the SAME character across at least 3 different drawers' own hands --
       the signature of a genuine per-CHARACTER stroke shape, not a single drawer's own
       instance-specific staircase artifact, which by construction can only ever touch ONE
       drawer). The reported fraction = (#coherent identities) / (#distinct identities
       observed). A LOW fraction under denoising would mean the population still fragments by
       drawer even after de-staircasing (the noise was not the cause); a HIGH fraction (rising
       vs run 32's own un-denoised adaptive-arm structure, where 82/83 ids were single-root
       ref_turn children -- effectively per-decode singletons, coherence ~0 by inspection)
       would be the mechanism-level confirmation this run is built to find.
  P2. coverage@10 at n=400 (SAME test alphabets/protocol/POWER_SEED/WAY/R_TARGET as run
      17b/25/26's own C0), Wilson 95% CI, vs RUN26_CONTROL. THE DELIVERABLE.
  P3. LEARN saturation (growth-curve flattening, SAME formula run26/32 use) AND run-32's own
      fragmentation clause: codebook top-level count > 3x RUN26_CONTROL's own top-level count
      (5) WITHOUT a P2 coverage gain = fragmentation-repeat, report and treat the corridor as
      closed (uniform bins at fixed placement make fragmentation unlikely a priori, but this is
      measured, not assumed).
  P4. Round-trip UNWEIGHTED arrangement subscore (`homework_loop.mark_characters`,
      `use_stability_weights=False` so `arrangement_score` IS the unweighted value) on the
      SAME 40-item practice set runs 27-31 use (`_build_practice_set(seed=gate.SEED+9000)`,
      background alphabets [5:15]), with the MOUSE-RENDER comparator: the render step's own
      output is put through `mouse_model.mouse_render` (forward pixel/grid quantization) BEFORE
      re-decode, and BOTH the original stroke decode and the re-decode of the (now corpus-
      quantized) render are denoised via `mouse_model.denoise_path_global` -- i.e. the full
      round trip now respects the SAME observation model real corpus files are assumed to obey
      on both sides of the render, not just at corpus-ingest time. Compared to RUN27_ARRANGEMENT
      = 0.8356 (that ceiling's own render used NEITHER mouse-quantization NOR denoising).
  P5. False-novelty probe: `run28_plastic._build_false_novelty_probe()`'s own 50 single-stroke
      probe (real strokes from the LEARN alphabets themselves, genuinely mastered material) --
      DENOISED before counting -- must mint 0/50 spurious quanta on this run's OWN calibrated
      graph (a positive count would mean CFAR recalibration under denoising is unsound, an
      honest anomaly to report, not silently averaged away).

STOPS (pre-registered):
  - P3's fragmentation clause fires (>3x control top with no P2 gain) -> report, corridor closed.
  - If P1a shows entropy stays ~0 (denoising alone doesn't spread identities under UNIFORM
    bins -- plausible: uniform bins may have been misplaced independent of noise, run 32's own
    finding) -> report that shape explicitly and STILL RUN P2/P4/P5 (coverage and round-trip
    are not entropy-derived; they are independent evidence and must be measured regardless of
    P1's outcome -- never gate compute on a single internal metric when the deliverable metric
    is cheap enough to just measure).
  - A P1-null + P2-null + P4-null full house closes the mouse-features cell honestly: pixel
    noise was not, after all, a quantized-features problem on this corpus at this bin
    placement -- the corridor DENOISE-VERDICT (nulled) + DENOISE-FEATURES (nulled) together
    would mean the mouse observation-model arc's remaining lever is neither comparator nor
    features, and the next lever is a different featureset entirely (report exactly that shape).

EXECUTION (ops law, binding): every invocation <=540s foreground, intra-stage batch
checkpointing (run 32's stress-gated pattern, reused verbatim: BATCH_STROKES=250, graph+meta
saved together every batch), stdbuf+tee to `results/omniglot_gate_run34c.log`, checkpoints
under `results/run34c_checkpoints/` (run26-34 checkpoint dirs READ-ONLY reference, never
written here). Global denoise costs ~27ms/stroke (measured in 34b: 40.6s/1500 strokes) on TOP
of existing ingest/decode cost -- budgeted into BATCH_STROKES/PER_CALL_BUDGET_SECONDS below.
SEED ISOLATION: every `teach()` persistence this process performs is redirected to
`results/run34c_checkpoints/seeds/` (run 32's own pattern) -- `seeds/stroke_shapes.json`
(a PARALLEL-SESSION-OWNED, already-dirty file) is never touched by this script.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run34c_features.py --stage verify
      ... --stage learn          (batch-checkpointed, re-invoke until COMPLETE)
      ... --stage calibrate      (batch-checkpointed, re-invoke until COMPLETE)
      ... --stage entropy-report (P1a/P1b, batch-checkpointed, re-invoke until COMPLETE)
      ... --stage eval           (P2, block-checkpointed, re-invoke until COMPLETE)
      ... --stage practice       (P4, single call)
      ... --stage falsenovelty   (P5, single call)
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
from domains import character_compose as cc
from domains import homework_loop as hl
from domains import ink_decode as ink
from domains import mouse_model as mm
from domains import novelty_calibration as nc
from domains import omniglot_world as ow
from domains import stroke_codebook as sc

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run34c_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")    # READ-ONLY reference.
RUN32_DIR = os.path.join(ROOT, "results", "run32_checkpoints")    # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# SEED ISOLATION (run 32's own pattern, reused verbatim): redirect EVERY teach() persistence
# this process performs to this run's OWN seeds dir. seeds/stroke_shapes.json (parallel-
# session-owned, already dirty) is never touched -- the live-graph install is unaffected, only
# the manifest WRITE location moves.
# ---------------------------------------------------------------------------------------------
RUN34C_SEEDS_DIR = os.path.join(CKPT_DIR, "seeds")
os.makedirs(RUN34C_SEEDS_DIR, exist_ok=True)
from domains.teach import teach as _real_teach


def _isolated_teach(*a, **k):
    return _real_teach(*a, **{**k, "seeds_dir": Path(RUN34C_SEEDS_DIR)})


sc.teach = _isolated_teach
cc.teach = _isolated_teach
import domains.teach as _teach_mod
_teach_mod.teach = _isolated_teach

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS -- byte-identical to run 26 where they overlap (uniform bins, SAME
# LEARN recipe/population -- the ONE variable changed below is denoise, injected at every raw-
# point entry, never a recipe change).
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N            # 5
LEARN_DRAWERS = gate.LEARN_DRAWERS                    # 01..14
LEARN_STROKE_CAP = 1500                               # run 16/25's saturation-verified cap.
DK = gate.DK                                          # UNIFORM bins -- NOT run 32's adaptive
                                                       # edges (isolates the denoise variable).
GROWTH_WINDOW = gate.GROWTH_WINDOW
SHORTLIST_K = 10
R_TARGET = run25.R_TARGET
WAY = run25.WAY
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS
POWER_SEED = run25.POWER_SEED
PER_CALL_BUDGET_SECONDS = 460.0
BATCH_STROKES = 200          # denoise adds ~27ms/stroke on top of decode -- smaller batch than
                              # run32's 250 to keep every checkpoint window comfortably <90s.
RUNAWAY_FACTOR = 10.0         # structural mid-learn abort (uniform bins should never approach
                              # this; the guard exists so a surprise cannot hang the stage).

RUN26_CONTROL_COVERAGE = {"cov": 0.715, "ci": (0.6689, 0.7570), "n": 400, "k": 286,
                           "note": "run26_checkpoints/eval_baseline.json"}
RUN27_ARRANGEMENT = 0.8356    # results/omniglot_gate_run27.log, mean_score=0.9376, surviving=39/40


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
# THE ONE VARIABLE: denoise every raw stroke through the GLOBAL constrained smoother (34b's own
# principled inverse, default params) before it ever reaches ingest/decode. Applied uniformly
# everywhere in this script -- LEARN, calibrate, entropy measurement, eval, practice, probe.
# ---------------------------------------------------------------------------------------------
def _dn(points) -> list:
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 3:
        return pts.tolist()
    return mm.denoise_path_global(pts).tolist()


# ---------------------------------------------------------------------------------------------
# STAGE: verify -- prerequisites present (run26 control, run32 entropy citation, real data).
# ---------------------------------------------------------------------------------------------
def stage_verify():
    print(f"\n{SEP}\n  STAGE: verify (RUN 34c -- recipe/citation check)\n{SEP}")
    needed = [_run26("learn_meta.json"), _run26("eval_baseline.json"),
              _run32("entropy_report.json")]
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
    checks = [
        ("gate.SEED", gate.SEED, gate.SEED),
        ("LEARN_ALPHABETS_N", LEARN_ALPHABETS_N, gate.LEARN_ALPHABETS_N),
        ("DK (uniform)", DK, gate.DK),
        ("LEARN_STROKE_CAP", LEARN_STROKE_CAP, 1500),
        ("learn_alphabets", control_meta["learn_alphabets"],
         ow.alphabets("background")[:LEARN_ALPHABETS_N]),
        ("n_strokes", control_meta["n_strokes"], LEARN_STROKE_CAP),
    ]
    ok = True
    for label, a, b in checks:
        match = (a == b)
        ok = ok and match
        print(f"  recipe check  {label:<20} run34c={a!r}  reference={b!r}  "
              f"{'MATCH' if match else 'MISMATCH -- PROTOCOL DRIFT'}")
    print(f"  RUN26 CONTROL coverage@{SHORTLIST_K}: {control_cov}")
    print(f"  RUN32 identity entropy (cited): control={run32_ent['identity']['control']} "
          f"adapt={run32_ent['identity']['adapt']}")
    if not ok:
        print("  WALL: a prerequisite is incomplete or mismatched -- this run must NOT proceed.")
        return 1
    print("  RECIPE VERIFIED -- proceeding.")
    _save_json(dict(verified=True, control_top=control_meta["grain_report"].get("top"),
                     control_coverage=control_cov,
                     run32_entropy_control=run32_ent["identity"]["control"],
                     run32_entropy_adapt=run32_ent["identity"]["adapt"]),
               _ckpt("verify.json"))
    print(f"  saved -> {_ckpt('verify.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: learn -- fresh LEARN pass, UNIFORM bins, every raw stroke denoised once at ingest.
# Batch-checkpointed (graph+meta together every BATCH_STROKES), re-invoke until COMPLETE.
# ---------------------------------------------------------------------------------------------
def _collect_learn_strokes_tagged(alphabets: list, drawers: list, cap: int) -> list:
    """SAME iteration order as `run32_subquantum._collect_learn_strokes_with_drawer`
    (alphabet -> character -> drawer -> stroke), additionally carrying (alphabet, character)
    alongside each stroke's own drawer id -- the raw material P1b's class-grain coherence
    metric needs (drawer/class provenance the flat `_collect_learn_strokes` discards). Pure
    I/O gather, no decode, no decision."""
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


def stage_learn():
    print(f"\n{SEP}\n  STAGE: learn (RUN 34c -- DENOISE-FEATURES, uniform bins)\n{SEP}")
    out_graph, out_meta = _ckpt("learn.json"), _ckpt("learn_meta.json")
    if os.path.exists(out_graph) and os.path.exists(out_meta):
        print(f"  learn already COMPLETE -- {out_graph}")
        return 0

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
          f"population={len(strokes)}  DK={DK}  DENOISE=global (mouse_model.denoise_path_global)")

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
                                  enable_substroke=True)
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
          f"ratio={frag_ratio}  "
          f"{'FLAG -- >3x control' if p3_frag_stop else 'OK'}")

    _save_graph(s, out_graph)
    _save_json(dict(n_strokes=prog["n_done"], elapsed=prog["elapsed_total"], grain_report=grain,
                     learn_alphabets=learn_alphabets, sat_pass=sat_pass,
                     growth=growth, growth_tail=growth[-3:] if growth else [],
                     p3_control_top=control_top, p3_our_top=our_top,
                     p3_frag_ratio=frag_ratio, p3_frag_stop=p3_frag_stop),
               out_meta)
    print(f"  saved -> {out_graph}, {out_meta}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: calibrate -- CFAR pass on denoised points, uniform bins, batch-checkpointed.
# ---------------------------------------------------------------------------------------------
def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (RUN 34c -- CFAR on denoised points, uniform bins)\n{SEP}")
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
    print(f"  LEARN population: {len(strokes)} strokes  DENOISE=global  "
          f"(margin={nc.DEFAULT_MARGIN}, min_family_samples={nc.DEFAULT_MIN_FAMILY_SAMPLES})")

    t0 = time.time()
    total = len(strokes)
    while prog["n_done"] < total and (time.time() - t0) < PER_CALL_BUDGET_SECONDS:
        batch = strokes[prog["n_done"]:prog["n_done"] + BATCH_STROKES]
        tb = time.time()
        for points in batch:
            pairs = nc._measure_stroke(s, _dn(points), DK)
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
# population, denoised, tagged with (alphabet, character, drawer) provenance.
# ---------------------------------------------------------------------------------------------
def stage_entropy_report():
    print(f"\n{SEP}\n  STAGE: entropy-report (P1a identity entropy, P1b class-grain coherence)\n{SEP}")
    calib_graph = _ckpt("calibrated.json")
    if not os.path.exists(calib_graph):
        print("  WALL: run 'calibrate' to completion first.")
        return 1

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
                                      scale_bins=DK["scale_bins"])
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
    print(f"\n  P1a IDENTITY-GRAIN ENTROPY (this run, denoised+uniform-bins): "
          f"n={n_obs}  ids={n_ids}  entropy={entropy_bits:.4f} bits "
          f"(max {max_entropy:.4f})  top_share={top_share:.4f}")
    run32_ent = _load_json(_run32("entropy_report.json"))["identity"]
    print(f"  cited CONTROL (run32, raw uniform, undenoised): "
          f"{run32_ent['control']['entropy_bits']:.4f} bits / {run32_ent['control']['n_families']} ids")
    print(f"  cited ADAPTIVE-RAW (run32, adaptive bins, undenoised): "
          f"{run32_ent['adapt']['entropy_bits']:.4f} bits / {run32_ent['adapt']['n_families']} ids")
    p1a_spread = bool(entropy_bits > run32_ent["control"]["entropy_bits"] + 0.1 and
                       n_ids > run32_ent["control"]["n_families"])
    print(f"  P1a (spread vs CONTROL): {'CONFIRMED' if p1a_spread else 'NULL -- stayed ~0'}")

    # P1b -- class-grain coherence fraction.
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
    print(f"  per-identity best same-class drawer-span (top 10 by occurrence count): " +
          ", ".join(f"{k}={v}" for k, v in
                    sorted(per_id_best.items(), key=lambda kv: -hist.get(kv[0], 0))[:10]))

    out = dict(identity=dict(n_observations=n_obs, n_ids=n_ids, entropy_bits=entropy_bits,
                             max_entropy_bits=max_entropy, top_share=top_share,
                             p1a_spread_vs_control=p1a_spread),
               coherence=dict(n_distinct_ids=n_distinct_ids, n_coherent=n_coherent,
                              coherence_fraction=coherence_frac, per_id_best=per_id_best),
               cited_run32=run32_ent)
    _save_json(out, _ckpt("entropy_report.json"))
    print(f"\n  saved -> {_ckpt('entropy_report.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# LOCAL decode_char_signature clone -- BYTE-IDENTICAL to `gate.decode_char_signature`'s
# ingest/decode/compose recipe (the composed_sig arm ONLY -- the arm `ar.propose_top_k`
# actually consumes; the sorted/rel2/substroke ablation arms that function also computes are
# NOT needed here and are omitted, not touched), with ONE change: every raw stroke is denoised
# before `ink.ingest_ink`. `scripts/jabberwock_omniglot_dynamic_quantization.py` (the shared
# "gate" module) is NOT modified -- this is a new, separate function in this script only.
# ---------------------------------------------------------------------------------------------
def _decode_char_signature_denoised(s, path, cache, dk) -> dict:
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
                              enable_substroke=True)
        knots = s.node(ink_node)["attrs"].get("knots") or []
        stroke_points.extend(cc.decode_result_to_stroke_points(knots, res))
    composed = cc.compose_character_signature(
        s._inner, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
    out = dict(composed_sig=composed["signature"])
    cache[path] = out
    return out


# ---------------------------------------------------------------------------------------------
# STAGE: eval -- P2, coverage@10 at n=400, SAME protocol as run17b/25/26's own C0, on THIS
# run's denoised+calibrated graph via `_decode_char_signature_denoised`. Block-checkpointed.
# ---------------------------------------------------------------------------------------------
def stage_eval():
    print(f"\n{SEP}\n  STAGE: eval (RUN 34c -- P2 coverage@{SHORTLIST_K})\n{SEP}")
    graph_src = _ckpt("calibrated.json")
    if not os.path.exists(graph_src):
        print("  WALL: run 'calibrate' to completion first.")
        return 1

    out_path = _ckpt("eval.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval already COMPLETE (n={len(state['records'])}).")
        return 0

    s = _load_graph(graph_src)
    native = s._inner
    cache_path = _ckpt("eval_cache.json")
    cache: dict = {}    # in-process only (composed_sig is not JSON-round-trippable cheaply
                        # here); re-invocation re-decodes already-visited paths within a block
                        # boundary only -- blocks themselves are checkpointed, not individual
                        # decodes, matching run26/32's own eval cache discipline in spirit.

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

        full_dwell_this_block = (state["block_idx"] == 0)     # P7-style anomaly spot-check.
        scratch0 = cand0 = None
        if full_dwell_this_block:
            scratch0 = srs.Substrate()
            _, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                                thetas=ar.DEFAULT_PARSE_THETAS)

        exemplars = [_decode_char_signature_denoised(s, drawer_files[ci][ex_drawer], cache, DK)
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

            qd = _decode_char_signature_denoised(s, path, cache, DK)
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
# STAGE: practice -- P4, round-trip UNWEIGHTED arrangement with the MOUSE-RENDER comparator.
# In-process-only rebind of `homework_loop._decode_stroke_full` (denoise both sides) and
# `homework_loop._render_parse` (forward mouse-quantize the render before re-decode) -- NEVER
# writes to homework_loop.py; the file on disk is untouched, and the rebind is local to this
# process (never persisted, never visible to any other session).
# ---------------------------------------------------------------------------------------------
_ORIG_DECODE_STROKE_FULL = hl._decode_stroke_full
_ORIG_RENDER_PARSE = hl._render_parse


def _decode_stroke_full_denoised(agent, points, dk):
    return _ORIG_DECODE_STROKE_FULL(agent, _dn(points), dk)


def _render_parse_mouse(native, parse, dk, jitter_by_idx=None, tolerant_joins=False,
                        junction_frac=ar.DEFAULT_JUNCTION_FRAC):
    pts, n_joins = _ORIG_RENDER_PARSE(native, parse, dk, jitter_by_idx=jitter_by_idx,
                                      tolerant_joins=tolerant_joins,
                                      junction_frac=junction_frac)
    if pts:
        arr = np.asarray(pts, dtype=float)
        if arr.ndim == 2 and arr.shape[0] > 0:
            pts = mm.mouse_render(arr).tolist()
    return pts, n_joins


def _unweighted_arrangement(m) -> float:
    return m.arrangement_score_unweighted if m.arrangement_score_unweighted is not None \
        else m.arrangement_score


def stage_practice():
    print(f"\n{SEP}\n  STAGE: practice (RUN 34c -- P4 round-trip, MOUSE-RENDER comparator)\n{SEP}")
    graph_src = _ckpt("calibrated.json")
    if not os.path.exists(graph_src):
        print("  WALL: run 'calibrate' to completion first.")
        return 1
    out_path = _ckpt("practice.json")
    if os.path.exists(out_path):
        print(f"  practice already COMPLETE -- {out_path}")
        result = _load_json(out_path)
        print(f"  mean_arrangement(unweighted)={result['mean_arrangement_unweighted']:.4f}")
        return 0

    s = _load_graph(graph_src)
    practice_items, practice_alphabets = run29._build_practice_set()
    test_alphabets = run29._test_alphabets()
    eval_ids = run29._eval_class_ids(test_alphabets)
    print(f"  {len(practice_items)} practice characters from {practice_alphabets}  "
          f"(SAME seed/slice as runs 27-31)  DENOISE=global (both sides)  "
          f"MOUSE-RENDER=grid quantize after render")

    hl._decode_stroke_full = _decode_stroke_full_denoised
    hl._render_parse = _render_parse_mouse
    try:
        t0 = time.time()
        marked = hl.mark_characters(s, practice_items, dk=DK, eval_class_ids=eval_ids)
        elapsed = time.time() - t0
    finally:
        hl._decode_stroke_full = _ORIG_DECODE_STROKE_FULL
        hl._render_parse = _ORIG_RENDER_PARSE

    def _mean(attr):
        vals = [getattr(m, attr) for m in marked if getattr(m, attr) is not None]
        return float(np.mean(vals)) if vals else 0.0

    mean_family = _mean("family_score")
    mean_count = _mean("count_score")
    mean_arrangement_raw = _mean("arrangement_score")
    arr_vals = [_unweighted_arrangement(m) for m in marked]
    mean_arrangement_unweighted = float(np.mean(arr_vals)) if arr_vals else 0.0
    surviving = sum(1 for m in marked if m.round_trip_score < hl.DEFAULT_MAX_SCORE)
    mints_reading = sum(m.n_mints_reading for m in marked)

    print(f"  n_items={len(marked)}  elapsed={elapsed:.1f}s")
    print(f"  mean family={mean_family:.4f}  count={mean_count:.4f}  "
          f"arrangement(raw)={mean_arrangement_raw:.4f}  "
          f"arrangement(unweighted)={mean_arrangement_unweighted:.4f}")
    print(f"  surviving={surviving}/{len(marked)}  mints_reading={mints_reading}")
    print(f"  vs RUN27_ARRANGEMENT (undenoised, unquantized render) = {RUN27_ARRANGEMENT}")

    result = dict(n_items=len(marked), practice_alphabets=practice_alphabets,
                 mean_family=mean_family, mean_count=mean_count,
                 mean_arrangement_raw=mean_arrangement_raw,
                 mean_arrangement_unweighted=mean_arrangement_unweighted,
                 surviving=surviving, mints_reading=mints_reading, elapsed=elapsed,
                 vs_run27_arrangement=RUN27_ARRANGEMENT)
    _save_json(result, out_path)
    print(f"  saved -> {out_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: falsenovelty -- P5, 0/50 false-mint probe on this run's own calibrated graph, denoised.
# ---------------------------------------------------------------------------------------------
def stage_falsenovelty():
    print(f"\n{SEP}\n  STAGE: falsenovelty (RUN 34c -- P5, false-novelty probe)\n{SEP}")
    graph_src = _ckpt("calibrated.json")
    if not os.path.exists(graph_src):
        print("  WALL: run 'calibrate' to completion first.")
        return 1
    out_path = _ckpt("falsenovelty.json")
    if os.path.exists(out_path):
        result = _load_json(out_path)
        print(f"  falsenovelty already COMPLETE -- {result['false_novelty']}/{result['n_probe']}")
        return 0

    s = _load_graph(graph_src)
    probe = run28._build_false_novelty_probe()
    probe_denoised = [_dn(p) for p in probe]
    count = run28._count_false_novelty(s, probe_denoised, DK)
    print(f"  false_novelty={count}/{len(probe)}  {'PASS (0/50)' if count == 0 else 'ANOMALY -- nonzero'}")
    result = dict(false_novelty=count, n_probe=len(probe))
    _save_json(result, out_path)
    print(f"  saved -> {out_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: report -- final verdicts, P1-P5, honest anomalies.
# ---------------------------------------------------------------------------------------------
def stage_report():
    print(f"\n{SEP}\n  RUN 34c -- DENOISE-FEATURES -- FINAL REPORT\n{SEP}")

    def _opt(name):
        p = _ckpt(name)
        return _load_json(p) if os.path.exists(p) else None

    learn_meta = _opt("learn_meta.json")
    ent = _opt("entropy_report.json")
    ev = _opt("eval.json")
    practice = _opt("practice.json")
    fn = _opt("falsenovelty.json")

    print(f"\n  CONTROL (cited, never re-run): coverage@{SHORTLIST_K}="
          f"{100*RUN26_CONTROL_COVERAGE['cov']:.1f}% "
          f"[{100*RUN26_CONTROL_COVERAGE['ci'][0]:.1f},{100*RUN26_CONTROL_COVERAGE['ci'][1]:.1f}]  "
          f"n={RUN26_CONTROL_COVERAGE['n']}")

    if ent:
        ida = ent["identity"]
        coh = ent["coherence"]
        print(f"\n  P1a IDENTITY ENTROPY: {ida['entropy_bits']:.4f} bits / {ida['n_ids']} ids  "
              f"(cited control: {ent['cited_run32']['control']['entropy_bits']:.4f} bits / "
              f"{ent['cited_run32']['control']['n_families']} ids;  cited adaptive-raw: "
              f"{ent['cited_run32']['adapt']['entropy_bits']:.4f} bits / "
              f"{ent['cited_run32']['adapt']['n_families']} ids)  "
              f"{'CONFIRMED spread' if ida['p1a_spread_vs_control'] else 'NULL -- stayed ~0'}")
        print(f"  P1b CLASS-GRAIN COHERENCE: {coh['n_coherent']}/{coh['n_distinct_ids']} = "
              f"{coh['coherence_fraction']:.4f} (identities with >=1 class reached by "
              f">=3 distinct drawers)")
    else:
        print("\n  P1: entropy-report not yet complete.")

    if learn_meta:
        print(f"\n  P3 SATURATION/FRAGMENTATION: sat_pass={learn_meta.get('sat_pass')}  "
              f"control_top={learn_meta.get('p3_control_top')}  "
              f"our_top={learn_meta.get('p3_our_top')}  "
              f"ratio={learn_meta.get('p3_frag_ratio')}  "
              f"frag_stop={learn_meta.get('p3_frag_stop')}")
    else:
        print("\n  P3: learn_meta.json not yet present.")

    if ev and ev.get("done"):
        cov = ev["coverage"]
        sep = _ci_separated(tuple(cov["ci"]), tuple(RUN26_CONTROL_COVERAGE["ci"]))
        print(f"\n  P2 COVERAGE@{SHORTLIST_K} (THE DELIVERABLE): n={cov['n']}  "
              f"{100*cov['cov']:.1f}% [{100*cov['ci'][0]:.1f}%, {100*cov['ci'][1]:.1f}%]  "
              f"vs control {100*RUN26_CONTROL_COVERAGE['cov']:.1f}% "
              f"[{100*RUN26_CONTROL_COVERAGE['ci'][0]:.1f}%,{100*RUN26_CONTROL_COVERAGE['ci'][1]:.1f}%]  "
              f"CI-separated: {sep}")
        base_recs_path = _run26("eval_baseline.json")
        if os.path.exists(base_recs_path):
            base_records = _load_json(base_recs_path)["records"]
            n_align = min(len(base_records), len(ev["records"]))
            newly = sum(1 for i in range(n_align)
                        if ev["records"][i]["in_shortlist"] and not base_records[i]["in_shortlist"])
            lost = sum(1 for i in range(n_align)
                       if not ev["records"][i]["in_shortlist"] and base_records[i]["in_shortlist"])
            print(f"    episode residual (aligned n={n_align}, SAME POWER_SEED/block order): "
                  f"newly_covered={newly}  lost={lost}")
        if "full_dwell" in ev:
            fd = ev["full_dwell"]
            print(f"    full-dwell block-0 anomaly check: {100*fd['acc']:.1f}% (n={fd['n']})")
    else:
        print("\n  P2: eval not yet complete.")

    if practice:
        print(f"\n  P4 ROUND-TRIP UNWEIGHTED ARRANGEMENT (MOUSE-RENDER comparator): "
              f"{practice['mean_arrangement_unweighted']:.4f}  vs RUN27_ARRANGEMENT="
              f"{RUN27_ARRANGEMENT}  (n={practice['n_items']}, surviving="
              f"{practice['surviving']}/{practice['n_items']})")
    else:
        print("\n  P4: practice not yet complete.")

    if fn:
        print(f"\n  P5 FALSE-NOVELTY PROBE: {fn['false_novelty']}/{fn['n_probe']}  "
              f"{'PASS' if fn['false_novelty'] == 0 else 'ANOMALY'}")
    else:
        print("\n  P5: falsenovelty not yet complete.")

    _save_json(dict(control=RUN26_CONTROL_COVERAGE, entropy=ent, learn_meta=learn_meta,
                     eval=ev, practice=practice, falsenovelty=fn),
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
                    choices=["verify", "learn", "calibrate", "entropy-report", "eval",
                             "practice", "falsenovelty", "report"])
    args = p.parse_args()
    t0 = time.time()
    rc = {
        "verify": stage_verify,
        "learn": stage_learn,
        "calibrate": stage_calibrate,
        "entropy-report": stage_entropy_report,
        "eval": stage_eval,
        "practice": stage_practice,
        "falsenovelty": stage_falsenovelty,
        "report": stage_report,
    }[args.stage]()
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
