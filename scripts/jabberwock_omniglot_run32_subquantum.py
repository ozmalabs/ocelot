"""OMNIGLOT RUN 32 -- OPTION R: REPRESENTATION CHANGE, ATTACK THE BIN GRAIN (SUB-QUANTUM).

THE DECISION BEING EXECUTED (creator, commit df70601e, third-fork OPTION R): the standing
verdict-layer ceiling (six independent nulls, ~80.5% at n=400) and the reproducer-diagnosis
arc both point at the SAME residual — run 28's calibration measured `results/
run28_checkpoints/calibration_report.json`: **10,230 of 10,231 real LEARN spans resolve to
ONE family** under the pre-existing UNIFORM turn/length bins (`domains/stroke_codebook.
DEFAULT_TURN_BINS=16`/`DEFAULT_LEN_BINS=8`, equal-WIDTH cells over the full `(-180,180]`/
`[0,1)` range). Real handwriting's per-segment turn/length values are NOT uniformly
distributed over that range — almost every observation lands in the same one or two central
cells regardless of bin COUNT. The featureset carries ~zero discriminative information at
the grain that defines recognition IDENTITY; the +21pp arrangement layer and the continuous
AbS verdict have been working AROUND a dead layer, not through it.

THE BET: DATA-PLACED (quantile / equal-mass) quantization — bin edges positioned by the
LEARN distribution's OWN structure, per dimension (turn, length), held as GRAPH DATA
(`domains/adaptive_bins.py`) rather than a fixed uniform COUNT — revives the stroke grain.
Machinery: `runners/dsl/src/strokes.rs`'s `StrokeQuantize`/`StrokeRender` Terms extended with
optional `turn_edges`/`len_edges`/`emit_residual` fields (see `runners/dsl/src/term.rs`'s doc
for the full semantics) — the UNIFORM-count path is BYTE-IDENTICAL when these are absent
(verified: `tests/test_adaptive_bins_migrated.py`, 19/19 green; full regression 907/907
green post-change). Edges apply to the FINE grain ONLY (the grain that carries recognition
identity and the grain run 28's calibration measured the collapse on) — coarse/mid/subfine
stay on their existing uniform bins, deliberately out of scope (near-miss tolerance bands,
not identity carriers; run 5/9/14's fragmentation/recursion/noise nulls forbid touching
those).

WHAT FIVE RUNS OF NULLS ALREADY FALSIFIED (this design must not repeat them):
  - FINER UNIFORM BINS FRAGMENT (run 5, run 25) -- NOT repeated here: bin COUNT is unchanged
    (`DEFAULT_TURN_BINS`/`DEFAULT_LEN_BINS`), only PLACEMENT moves.
  - RECURSION COLLAPSES (run 14: sub-stroke codebook -> 4 quanta) -- NOT repeated: this lever
    touches the FINE grain once, no new recursive sub-grain.
  - QUANTIZED LONG-RANGE RELATIONS CARRY NOISE (runs 9+14) -- NOT repeated: no new relation
    type, only WHERE the existing seg/pose relations' bin boundaries sit.

PRE-REGISTERED BAR (non-negotiable, stated before any arm result below is computed): a
finer/better featureset must beat or feed the CONTINUOUS verdict layer that already consumes
sub-bin signal ("bins propose, continuous decides," commit 7743c2de) — the deliverable
metric is the PROPOSAL layer: **coverage@10 at n=400 vs baseline 71.5% [66.9, 75.7]**
(`results/run26_checkpoints/eval_baseline.json`).

ARMS:
  (1) CONTROL -- run-26 baseline REUSED VERBATIM (71.5% coverage / 62.0% shortlist / 80.5%
      full-dwell, n=400). Never re-run; its own LEARN recipe pins the OLD uniform bins.
  (2) ADAPT -- adaptive (quantile) turn/length edges on the FINE grain only. Fresh LEARN +
      fresh CFAR calibration (new bins require recalibration -- the DTW-fallback in-family
      distance distribution changes when the fine grain's own family-resolution changes).
  (3) ADAPT+RESIDUAL -- ADAPT's codebook/edges PLUS the sub-bin residual emitted at decode
      time (`StrokeQuantize(..., emit_residual=True)`) consumed by `domains/abs_read.py`'s
      `propose_top_k` residual-aware tiebreak (`query_residuals`/`exemplar_residuals`,
      `DEFAULT_RESIDUAL_WEIGHT`) -- SAME LEARN graph as arm 2 (the residual is a
      decode/proposal-time lever, not a codebook-growth difference). Residual-only (no
      adaptive edges) is OMITTED by design -- residuals of MISPLACED bins inherit the
      misplacement (documented, not run).

AMENDMENT (2026-07-05, pre-registered BEFORE the re-run, coordinator-directed -- and the
run's FIRST REAL FINDING, from the first live gather-edges + the killed first learn attempt):
  FINDING (prominent, first-class): the raw LEARN span distribution is DEGENERATE in a way
  that mechanistically EXPLAINS the run-28 identity collapse. (1) TURN has a POINT MASS at
  exactly 0.0 degrees -- four consecutive quantiles landed on 0.0 (locally-straight
  segments); the informative structure lives in the TAILS: the quantile edges concentrate
  resolution in [-40, +32] degrees where writing actually turns, while UNIFORM bins waste
  half the range beyond +/-90 degrees where no mass lives. (2) LENGTH collapses onto
  1/segments EXACTLY: with equal-ARC-LENGTH resampling, per-segment normalized length is
  1/segments BY CONSTRUCTION -- the dimension is INFORMATION-FREE, an artifact of the
  extractor. One dead dimension + one point-massed dimension = the 10,230/10,231 collapse.
  The first learn attempt HUNG on the pre-amendment edges: an epsilon-nudge on the equal
  quantiles manufactured near-zero-width bins, point-mass values scattered across them under
  float jitter, every span minted fresh (47,833 seed-lines before the kill).
  FIX (pre-registered, `domains/adaptive_bins.py`): (a) DEDUPE equal/near-equal quantiles
  (min bin width = domain_width * MIN_BIN_WIDTH_FRAC = 1e-3, documented) -- FEWER effective
  bins where mass is point-like; (b) KEEP the length dimension with its deduped (~2-3
  effective) bins and REPORT its measured occupancy entropy (~0 bits expected) -- a dimension
  dead by construction is a falsifiable RECORD, never silently dropped; (c) GUARD:
  strictly-increasing edges asserted post-dedupe, hard-fail (`DegenerateEdgesError`).
  SEED ISOLATION (the df70601e hazard, now live-confirmed): running boot/learn outside
  pytest's tmp-redirect persists every mint into `seeds/stroke_shapes.json` via `teach()` --
  a parallel-session-owned file. This script now redirects ALL of its own teach() persistence
  to `results/run32_checkpoints/seeds/` (the live-graph install is unaffected; only the
  manifest write moves). The 47,833-line mutation from the killed attempt was reverted.
  OPS (binding): stages run FOREGROUND only; learn checkpoints intra-stage in stroke batches
  (graph+meta saved together every batch, run31's stress-gated pattern) so every invocation
  completes <=540s and no >90s window passes without a checkpoint write; an intra-stage
  RUNAWAY guard aborts if the codebook exceeds 10x the control top-level count mid-learn
  (the fragmentation mode cannot hang the stage again).

PRIMARY PREDICTION:
  P1. coverage@10 at n=400 vs CONTROL, Wilson CIs -- the deliverable.
  P2. Span-family ENTROPY at LEARN (the identity-collapse metric, in BITS): distribution of
      the SAME ~10,231-span population over families, CONTROL (old bins, ALREADY MEASURED --
      `results/run28_checkpoints/calibration_report.json`'s own `per_family` histogram) vs
      ADAPT (new bins, measured by this run's OWN `--stage calibrate` on the freshly-grown
      ADAPT codebook -- `calibrate_dtw_thresholds`'s `by_family`/`per_family` scope covers
      EVERY accepted span at ANY tier, the exact population run 28 measured the collapse on).
      Must spread meaningfully vs the 1-family (H=0.0 bits) collapse -- report family count +
      entropy in bits, before/after.
      P2 REINTERPRETATION (amendment): any entropy gain can come from the TURN dimension's
      tail resolution ONLY (length is dead by construction, recorded as ~0 bits in the edges
      report). If deduped adaptive turn bins still leave spans in ~1 family, the P2 STOP
      fires with the distribution-is-degenerate finding now fully mechanistically explained
      -- a clean, valuable terminus. If entropy spreads, proceed to the full gate as
      pre-registered.

SECONDARY:
  P3. LEARN saturation must STILL HOLD under adaptive edges (growth curve flattens; codebook
      stays O(10s) not O(100s) -- PRE-REGISTERED STOP: quanta >3x the CONTROL codebook count
      WITHOUT a P1 coverage gain = fragmentation-repeat, stop, that corridor is closed).
  P4. Round-trip unweighted arrangement on the run-27 practice set vs the 0.8356 ceiling.
  P5. Reading-mints on the 10 held-out practice alphabets (CFAR recalibrated; false-novelty
      probe 0/50 must hold).
  P6. Shortlist accuracy moves only through coverage (anomaly check).
  P7. Full-dwell on arm graphs spot-checked at block 0 must stay ~baseline -- the continuous
      verdict is codebook-independent by construction (it never touches the stroke codebook
      at all, `ar.stage_parse_char`/`ar.parse_marginal_verdict` on a fresh scratch
      Substrate) -- a shift here is a protocol bug, not a finding.

STOPS: P2 fails (spans stay collapsed under quantile edges -- the distribution ITSELF is
degenerate, not the bins; report and stop, a deep finding in its own right); P3 fragmentation
stop above; if ADAPT nulls P1 at power but P2/P4/P5 confirm internals, report EXACTLY that
shape ("featureset revived but proposal-blind tail unmoved") -- the eval residual analysis
(newly-covered/lost episodes) is mandatory either way.

EXECUTION: staged + checkpointed under `results/run32_checkpoints/` (run26-31 checkpoint
dirs READ-ONLY reference data, NEVER written here). Every stage is a single blocking call,
never backgrounded; LEARN/calibrate/eval each fit one foreground invocation at this
population size (see the stage docstrings for measured wall-clock precedent from run26/28).

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run32_subquantum.py --stage verify
      ... --stage gather-edges
      ... --stage learn --arm adapt
      ... --stage calibrate --arm adapt
      ... --stage entropy-report
      ... --stage eval --arm {control,adapt,adapt_residual}   (block-checkpointed, re-invoke)
      ... --stage report
"""
from __future__ import annotations

import argparse
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
import scripts.jabberwock_omniglot_run29_consume as run29
from domains import abs_read as ar
from domains import adaptive_bins as ab
from domains import ink_decode as ink
from domains import novelty_calibration as nc
from domains import omniglot_world as ow
from domains import stroke_codebook as sc

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run32_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")     # READ-ONLY reference.
RUN28_DIR = os.path.join(ROOT, "results", "run28_checkpoints")     # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# SEED ISOLATION (AMENDMENT -- the df70601e hazard, live-confirmed by the killed first learn
# attempt: 47,833 lines of mints appended to the parallel-session-owned
# seeds/stroke_shapes.json, since reverted): redirect EVERY teach() persistence this script's
# own process performs (boot-time mints via gate.boot(), LEARN mints via
# stroke_codebook.grow_stroke_quantum, calibrate-time decode mints) to this run's OWN seeds
# dir. The LIVE-GRAPH install is byte-identical -- only the manifest WRITE location moves
# (mechanical host I/O, the same redirect every seed-isolated test fixture already applies).
# ---------------------------------------------------------------------------------------------
from pathlib import Path as _Path
from domains.teach import teach as _real_teach
RUN32_SEEDS_DIR = os.path.join(CKPT_DIR, "seeds")
os.makedirs(RUN32_SEEDS_DIR, exist_ok=True)


def _isolated_teach(*a, **k):
    return _real_teach(*a, **{**k, "seeds_dir": _Path(RUN32_SEEDS_DIR)})


sc.teach = _isolated_teach                     # stroke_codebook's module-level binding
import domains.character_compose as _cc_mod
_cc_mod.teach = _isolated_teach                # character_compose's module-level binding
import domains.teach as _teach_mod
_teach_mod.teach = _isolated_teach             # every LAZY `from domains.teach import teach`
                                               # (reflective_faculty's boot-time mints et al.)

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS -- byte-identical to run 26/28 where they overlap (the LEARN/
# calibration recipe this run's edges are fit against MUST match, or the two arms are not
# comparable).
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N            # 5
LEARN_DRAWERS = gate.LEARN_DRAWERS                    # 01..14
LEARN_STROKE_CAP = 1500                               # run 16/25's saturation-verified cap;
                                                       # SAME cap run 28's calibration used.
DK = gate.DK
GROWTH_WINDOW = gate.GROWTH_WINDOW
SHORTLIST_K = 10
R_TARGET = run25.R_TARGET
WAY = run25.WAY
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS
POWER_SEED = run25.POWER_SEED
PER_CALL_BUDGET_SECONDS = 460.0

ARMS = ("adapt", "adapt_residual")     # CONTROL is reused, never grown by this script.
CONTROL_COVERAGE = {"cov": 0.715, "note": "run26_checkpoints/eval_baseline.json, n=400"}


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _run26(name: str) -> str:
    return os.path.join(RUN26_DIR, name)


def _run28(name: str) -> str:
    return os.path.join(RUN28_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=gate._json_default if hasattr(gate, "_json_default") else str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _donkey0() -> bool:
    return "torch" not in sys.modules


def _save_graph(s, path: str) -> None:
    run29._save_graph(s, path)


def _load_graph(path: str):
    return run29._load_graph(path)


def _test_alphabets() -> list:
    return run29._test_alphabets()


def _eval_class_ids(test_alphabets: list) -> set:
    return run29._eval_class_ids(test_alphabets)


# ---------------------------------------------------------------------------------------------
# STAGE: verify -- the LEARN prerequisite this run's CONTROL/edge-fit population must match
# (run26's own learn_meta.json: alphabets, drawers, cap, DK) + run28's calibration_report.json
# (the CONTROL entropy measurement, P2's "before").
# ---------------------------------------------------------------------------------------------
def stage_verify():
    print(f"\n{SEP}\n  STAGE: verify (RUN 32 -- recipe check against run26/run28 read-only refs)\n{SEP}")
    learn_meta_src = _run26("learn_meta.json")
    calib_report_src = _run28("calibration_report.json")
    eval_baseline_src = _run26("eval_baseline.json")
    missing = [p for p in (learn_meta_src, calib_report_src, eval_baseline_src) if not os.path.exists(p)]
    if missing:
        print(f"  WALL: missing prerequisite file(s): {missing}")
        return 1
    learn_meta = _load_json(learn_meta_src)
    calib_report = _load_json(calib_report_src)
    eval_base = _load_json(eval_baseline_src)

    checks = [
        ("gate.SEED", gate.SEED, gate.SEED),
        ("LEARN_ALPHABETS_N", LEARN_ALPHABETS_N, gate.LEARN_ALPHABETS_N),
        ("DK", DK, gate.DK),
        ("LEARN_STROKE_CAP", LEARN_STROKE_CAP, 1500),
        ("learn_alphabets", learn_meta["learn_alphabets"], ow.alphabets("background")[:LEARN_ALPHABETS_N]),
        ("n_strokes", learn_meta["n_strokes"], LEARN_STROKE_CAP),
    ]
    ok = True
    for label, a, b in checks:
        match = (a == b)
        ok = ok and match
        print(f"  recipe check  {label:<20} run32={a!r}  reference={b!r}  {'MATCH' if match else 'MISMATCH -- PROTOCOL DRIFT'}")
    n_families_ok = calib_report.get("n_families", 0) > 0
    print(f"  run28 calibration_report sanity: n_families={calib_report.get('n_families')}  "
          f"n_spans_measured={calib_report.get('n_spans_measured')}  {'OK' if n_families_ok else 'EMPTY -- WALL'}")
    ok = ok and n_families_ok
    cov = eval_base.get("coverage", {})
    print(f"  run26 CONTROL coverage@{SHORTLIST_K}: {cov}")
    if not ok:
        print("  WALL: a prerequisite is incomplete or mismatched -- this run must NOT proceed.")
        return 1
    print("  RECIPE VERIFIED -- proceeding.")
    _save_json(dict(verified=True, control_coverage=cov, control_calib_report_path=calib_report_src),
               _ckpt("verify.json"))
    print(f"  saved -> {_ckpt('verify.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: gather-edges -- gather the SAME LEARN population (background[:5], drawers 01-14, cap
# 1500) run26/28 iterate, compute quantile edges. Cheap (no codebook growth, ~1500 single
# StrokeQuantize-at-bins=1 evaluates) -- single invocation, no checkpointing needed mid-stage.
# ---------------------------------------------------------------------------------------------
def stage_gather_edges():
    print(f"\n{SEP}\n  STAGE: gather-edges (RUN 32 -- quantile/equal-mass edges from the LEARN population)\n{SEP}")
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

    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    print(f"  gathering LEARN population: alphabets={learn_alphabets}  drawers="
          f"{LEARN_DRAWERS[0]}-{LEARN_DRAWERS[-1]}  cap={LEARN_STROKE_CAP}  DK={DK}")
    t0 = time.time()
    # SAME gather routine run28's own calibration stage uses (identical population).
    from scripts.jabberwock_omniglot_run28_plastic import _collect_learn_strokes
    strokes = _collect_learn_strokes(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
    print(f"  gathered {len(strokes)} raw strokes in {time.time()-t0:.1f}s -- extracting raw "
          f"per-segment turn/length values (StrokeQuantize @ bins=1, emit_residual)")

    t1 = time.time()
    learn_values = ab.gather_learn_span_values(s, strokes, segments=DK["segments"],
                                                max_knots=DK["max_knots"])
    print(f"  extracted {learn_values['n_spans']} span values from {learn_values['n_strokes']} "
          f"strokes in {time.time()-t1:.1f}s ({len(learn_values['turn'])} turn / "
          f"{len(learn_values['len'])} len observations)")

    report = ab.compute_adaptive_edges(learn_values, turn_bins=DK["turn_bins"], len_bins=DK["len_bins"])
    print(f"  METHOD: {report['method']} (amendment: dedupe min_width_frac={ab.MIN_BIN_WIDTH_FRAC})")
    print(f"  turn_edges: requested {report['turn_bins_requested']} bins -> "
          f"{report['turn_bins_effective']} EFFECTIVE after dedupe: "
          f"{[round(v, 2) for v in report['turn_edges']]}")
    print(f"  len_edges:  requested {report['len_bins_requested']} bins -> "
          f"{report['len_bins_effective']} EFFECTIVE after dedupe: "
          f"{[round(v, 4) for v in report['len_edges']]}")
    t_occ, l_occ = report["turn_occupancy"], report["len_occupancy"]
    print(f"  TURN occupancy entropy: {t_occ['entropy_bits']:.4f} bits "
          f"(max {t_occ['max_entropy_bits']:.4f})  counts={t_occ['counts']}")
    print(f"  LEN  occupancy entropy: {l_occ['entropy_bits']:.4f} bits "
          f"(max {l_occ['max_entropy_bits']:.4f})  counts={l_occ['counts']}"
          f"  <- the dead-by-construction dimension's falsifiable record (amendment (b))")
    uniform_turn = list(np.linspace(-180.0, 180.0, DK["turn_bins"] + 1))
    uniform_len = list(np.linspace(0.0, 1.0, DK["len_bins"] + 1))
    print(f"  (uniform turn edges for comparison: {[round(float(v), 2) for v in uniform_turn]})")
    print(f"  (uniform len edges for comparison:  {[round(float(v), 4) for v in uniform_len]})")

    _save_json(report, out_path)
    print(f"  saved -> {out_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _load_edges():
    report = _load_json(_ckpt("edges_report.json"))
    return report["turn_edges"], report["len_edges"]


# ---------------------------------------------------------------------------------------------
# STAGE: learn --arm {adapt,adapt_residual} -- fresh LEARN pass with adaptive edges wired
# into the FINE-grain decode/mint path. AMENDMENT ops law: BATCH-CHECKPOINTED (graph + meta
# saved TOGETHER every BATCH_STROKES, run31's "graph state and meta bookkeeping must advance
# together" discipline) so every invocation completes <=540s foreground and no >90s window
# passes without a checkpoint write; re-invoke until COMPLETE. An intra-stage RUNAWAY guard
# aborts if the top-level codebook exceeds RUNAWAY_FACTOR x the control's own count mid-learn
# (the mint-explosion mode that hung the first attempt structurally cannot hang this one).
# `adapt_residual` REUSES the SAME graph as `adapt` (the residual lever is decode/proposal-
# time, not codebook-growth-time) -- a copy, not a second LEARN pass.
# ---------------------------------------------------------------------------------------------
BATCH_STROKES = 250            # ~20-40s of healthy work + a few s graph save per checkpoint.
RUNAWAY_FACTOR = 10.0          # intra-stage abort threshold (the pre-registered P3 STOP at 3x
                                # is evaluated at finalize; 10x mid-learn = the explosion mode).


def _collect_learn_strokes_with_drawer(alphabets: list, drawers: list, cap: int) -> list:
    """`run_learn`'s own iteration order (alphabet -> character -> drawer -> stroke),
    reproduced with the DRAWER carried alongside each stroke (run_learn tags
    `writer=f"bg_{d}"` on ingest/decode -- byte-identical writer tagging requires it).
    Degenerate (<2-point) strokes are skipped and do NOT count toward `cap`, matching
    `_collect_learn_strokes`'s own filter. Pure I/O gather, no decode, no decision."""
    out = []
    for alph in alphabets:
        if len(out) >= cap:
            break
        for cdir in ow.characters(alph, "background"):
            if len(out) >= cap:
                break
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
                    out.append((st.tolist(), d))
    return out


def stage_learn(arm: str):
    print(f"\n{SEP}\n  STAGE: learn --arm {arm}\n{SEP}")
    if arm not in ARMS:
        print(f"  WALL: unknown arm {arm!r} -- must be one of {ARMS}")
        return 1
    out_graph = _ckpt(f"learn_{arm}.json")
    out_meta = _ckpt(f"learn_meta_{arm}.json")
    if os.path.exists(out_graph) and os.path.exists(out_meta):
        print(f"  learn --arm {arm} already COMPLETE -- {out_graph}")
        return 0

    if arm == "adapt_residual":
        adapt_graph, adapt_meta = _ckpt("learn_adapt.json"), _ckpt("learn_meta_adapt.json")
        if not (os.path.exists(adapt_graph) and os.path.exists(adapt_meta)):
            print("  WALL: run 'learn --arm adapt' first (adapt_residual reuses its LEARN graph).")
            return 1
        import shutil
        shutil.copy(adapt_graph, out_graph)
        meta = _load_json(adapt_meta)
        meta["reused_from"] = adapt_graph
        _save_json(meta, out_meta)
        print(f"  arm adapt_residual REUSES arm adapt's LEARN graph verbatim (same codebook; "
              f"the residual lever is a decode/proposal-time consumer, not a growth-time one).")
        print(f"  saved -> {out_graph}, {out_meta}")
        return 0

    if not os.path.exists(_ckpt("edges_report.json")):
        print("  WALL: run stage 'gather-edges' first.")
        return 1
    turn_edges, len_edges = _load_edges()

    control_meta = _load_json(_run26("learn_meta.json"))
    control_top = control_meta["grain_report"].get("top", control_meta["grain_report"].get("total"))
    runaway_cap = max(50.0, RUNAWAY_FACTOR * float(control_top))

    partial_graph = _ckpt(f"learn_partial_{arm}.json")
    progress_path = _ckpt(f"learn_progress_{arm}.json")
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
    strokes = _collect_learn_strokes_with_drawer(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
    print(f"  LEARN alphabets: {learn_alphabets}  drawers {LEARN_DRAWERS[0]}-{LEARN_DRAWERS[-1]}  "
          f"population={len(strokes)}  DK={DK}")
    print(f"  ADAPTIVE EDGES engaged on the FINE grain: turn={len(turn_edges)-1} effective bins, "
          f"len={len(len_edges)-1} effective bins")

    t0 = time.time()
    total = len(strokes)
    while prog["n_done"] < total and (time.time() - t0) < PER_CALL_BUDGET_SECONDS:
        batch = strokes[prog["n_done"]:prog["n_done"] + BATCH_STROKES]
        tb = time.time()
        for (points, d) in batch:
            ink_node = ink.ingest_ink(s, points, writer=f"bg_{d}", max_knots=DK["max_knots"])
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
        # CHECKPOINT: graph + meta together, every batch (run31's discipline).
        _save_graph(s, partial_graph)
        _save_json(prog, progress_path)
        print(f"  [batch] {prog['n_done']}/{total} strokes  codebook_top={grain_now['top']}  "
              f"total={grain_now['total']}  batch_wall={time.time()-tb:.1f}s  checkpointed.")

        # INTRA-STAGE RUNAWAY GUARD (amendment): the explosion mode aborts, never hangs.
        if grain_now["top"] > runaway_cap:
            prog["runaway_abort"] = dict(top=grain_now["top"], cap=runaway_cap,
                                          control_top=control_top)
            _save_json(prog, progress_path)
            print(f"\n  *** RUNAWAY ABORT: codebook top {grain_now['top']} > {runaway_cap} "
                  f"({RUNAWAY_FACTOR}x control {control_top}) -- the fragmentation mode; "
                  f"stopping per amendment. ***")
            return 2

    if prog["n_done"] < total:
        print(f"\n  PARTIAL: {prog['n_done']}/{total} strokes -- re-invoke "
              f"'--stage learn --arm {arm}' to continue (checkpoints saved).")
        print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
        return 0

    # FINALIZE.
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

    adapt_top = grain.get("top", grain.get("total"))
    frag_ratio = (adapt_top / control_top) if control_top else None
    p3_frag_stop = bool(frag_ratio is not None and frag_ratio > 3.0)
    print(f"  P3 fragmentation check: control_top={control_top}  adapt_top={adapt_top}  "
          f"ratio={frag_ratio}  {'FLAG -- >3x control (P1-conditional STOP per pre-registration)' if p3_frag_stop else 'OK'}")

    ab.store_adaptive_edges(s, turn_edges, len_edges)
    _save_graph(s, out_graph)
    _save_json(dict(n_strokes=prog["n_done"], elapsed=prog["elapsed_total"], grain_report=grain,
                     learn_alphabets=learn_alphabets, sat_pass=sat_pass,
                     growth=growth, growth_tail=growth[-3:] if growth else [],
                     turn_edges=turn_edges, len_edges=len_edges,
                     p3_control_top=control_top, p3_adapt_top=adapt_top,
                     p3_frag_ratio=frag_ratio, p3_frag_stop=p3_frag_stop),
               out_meta)
    print(f"  saved -> {out_graph}, {out_meta}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: calibrate --arm {adapt,adapt_residual} -- LEVER 1's CFAR pass, REQUIRED under new
# bins (the in-family DTW distance distribution changes when fine-grain family-resolution
# changes). ALSO the P2 entropy measurement's "after" half: `calibrate_dtw_thresholds`'s own
# `by_family`/`per_family` scope (EVERY accepted span, any tier) is EXACTLY the population
# run 28 measured the CONTROL collapse on. ~65-130s precedent (run28's own calibrate: 63.5s
# post-fix) -- single foreground invocation.
# ---------------------------------------------------------------------------------------------
def stage_calibrate(arm: str):
    """AMENDMENT ops law: measurement is BATCH-CHECKPOINTED (per-stroke `_measure_stroke`
    calls accumulated into a pairs list; graph + meta saved together every batch — decode CAN
    mint on a rare OOV, so graph state and pair bookkeeping must advance together, run31's
    own discipline) because decode at codebook ~132 costs ~0.6s/stroke and a monolithic
    1500-stroke pass would blow the 540s foreground budget. Re-invoke until COMPLETE; the
    final invocation applies the identical pre-registered max+margin formula via
    `calibrate_dtw_thresholds(measured_pairs=...)`. `adapt_residual` COPIES adapt's
    calibrated graph/report verbatim (same codebook, same edges, same LEARN population,
    deterministic decode — a re-run would be byte-identical; documented, not re-measured)."""
    print(f"\n{SEP}\n  STAGE: calibrate --arm {arm} (LEVER 1 -- CFAR, adaptive-edges-aware, batched)\n{SEP}")
    if arm not in ARMS:
        print(f"  WALL: unknown arm {arm!r} -- must be one of {ARMS}")
        return 1
    out_graph = _ckpt(f"calibrated_{arm}.json")
    out_report = _ckpt(f"calibration_report_{arm}.json")
    if os.path.exists(out_graph) and os.path.exists(out_report):
        print(f"  calibrate --arm {arm} already COMPLETE -- {out_graph}")
        report = _load_json(out_report)
        print(f"  n_families={report['n_families']}  n_spans_measured={report['n_spans_measured']}")
        return 0

    if arm == "adapt_residual":
        src_graph, src_report = _ckpt("calibrated_adapt.json"), _ckpt("calibration_report_adapt.json")
        if not (os.path.exists(src_graph) and os.path.exists(src_report)):
            print("  WALL: run 'calibrate --arm adapt' to completion first (adapt_residual copies it).")
            return 1
        import shutil
        shutil.copy(src_graph, out_graph)
        rep = _load_json(src_report)
        rep["reused_from"] = src_graph
        _save_json(rep, out_report)
        print("  arm adapt_residual COPIES arm adapt's calibrated graph/report verbatim "
              "(same codebook, same edges, deterministic decode -- re-measurement would be "
              "byte-identical).")
        print(f"  saved -> {out_graph}, {out_report}")
        return 0

    learn_graph = _ckpt(f"learn_{arm}.json")
    learn_meta_path = _ckpt(f"learn_meta_{arm}.json")
    if not (os.path.exists(learn_graph) and os.path.exists(learn_meta_path)):
        print(f"  WALL: run 'learn --arm {arm}' first.")
        return 1
    learn_meta = _load_json(learn_meta_path)
    turn_edges, len_edges = learn_meta["turn_edges"], learn_meta["len_edges"]

    partial_graph = _ckpt(f"calibrate_partial_{arm}.json")
    progress_path = _ckpt(f"calibrate_progress_{arm}.json")
    if os.path.exists(partial_graph) and os.path.exists(progress_path):
        s = _load_graph(partial_graph)
        prog = _load_json(progress_path)
        print(f"  RESUMING measurement at stroke {prog['n_done']}/{LEARN_STROKE_CAP}")
    else:
        s = _load_graph(learn_graph)
        prog = dict(n_done=0, pairs=[])

    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    from scripts.jabberwock_omniglot_run28_plastic import _collect_learn_strokes
    strokes = _collect_learn_strokes(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
    print(f"  LEARN population: {len(strokes)} strokes  "
          f"(margin={nc.DEFAULT_MARGIN}, min_family_samples={nc.DEFAULT_MIN_FAMILY_SAMPLES})")

    t0 = time.time()
    total = len(strokes)
    while prog["n_done"] < total and (time.time() - t0) < PER_CALL_BUDGET_SECONDS:
        batch = strokes[prog["n_done"]:prog["n_done"] + BATCH_STROKES]
        tb = time.time()
        for points in batch:
            pairs = nc._measure_stroke(s, points, DK, turn_edges=turn_edges, len_edges=len_edges)
            prog["pairs"].extend([[fam, float(d)] for (fam, d) in pairs])
            prog["n_done"] += 1
        _save_graph(s, partial_graph)
        _save_json(prog, progress_path)
        print(f"  [batch] {prog['n_done']}/{total} strokes measured  pairs={len(prog['pairs'])}  "
              f"batch_wall={time.time()-tb:.1f}s  checkpointed.")

    if prog["n_done"] < total:
        print(f"\n  PARTIAL: {prog['n_done']}/{total} strokes -- re-invoke "
              f"'--stage calibrate --arm {arm}' to continue (checkpoints saved).")
        print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
        return 0

    # FINALIZE: identical pre-registered formula on the collected pairs.
    try:
        report = nc.calibrate_dtw_thresholds(
            s, [], DK, measured_pairs=[(fam, d) for (fam, d) in prog["pairs"]])
    except nc.EmptyCalibrationError as e:
        print(f"  WALL: EMPTY CALIBRATION -- {e}")
        _save_json(dict(error=str(e)), out_report)
        return 1
    report["n_strokes_measured"] = prog["n_done"]         # provenance from the batching meta.
    print(f"  n_strokes_measured={report['n_strokes_measured']}  "
          f"n_spans_measured={report['n_spans_measured']}  n_families={report['n_families']}")
    print(f"  calibrated_families (per-family threshold): {report['calibrated_families']}")
    print(f"  pooled_families (data-starved): {len(report['pooled_families'])}")
    print(f"  global pooled calibration: {report['global']}")

    _save_graph(s, out_graph)
    _save_json(report, out_report)
    print(f"  saved -> {out_graph}, {out_report}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: entropy-report -- P2, the pre-registered STOP gate. Compares the CONTROL histogram
# (run28's ALREADY-MEASURED calibration_report.json, old uniform bins) against this run's OWN
# ADAPT histogram (calibration_report_adapt.json) -- both measured by the IDENTICAL
# `calibrate_dtw_thresholds` scope (every accepted span, any tier) over the SAME LEARN
# population, so the two `per_family` dicts are directly comparable family-count/mass
# distributions.
# ---------------------------------------------------------------------------------------------
def _measure_identity_hist(arm_label: str, graph_src: str, turn_edges, len_edges):
    """Batched, checkpointed identity-grain measurement over the SAME 1500-stroke LEARN
    population: decode every stroke on a COPY of `graph_src` and histogram, per accepted
    span, BOTH (a) the RESOLVED IDENTITY (`r["name"]` — the deepest match, the value
    downstream character composition actually consumes, `ink_decode._resolved_identity`,
    DISCRIMINATION item (a)) and (b) the prototype-anchored FAMILY ROOT (the run-28 scope).
    Mechanical: ingest + decode + read-back of already-decided fields; the graph copy is a
    THROWAWAY (measurement never persists back to the arm's calibrated graph — decode-time
    mints on the saturated graph are COUNTED and reported, then discarded with the copy).
    Returns the finished dict, or None if the budget expired (re-invoke)."""
    from domains import stroke_codebook as _sc
    from scripts.jabberwock_omniglot_run28_plastic import _collect_learn_strokes
    partial_graph = _ckpt(f"entropy_partial_{arm_label}.json")
    progress_path = _ckpt(f"entropy_progress_{arm_label}.json")
    done_path = _ckpt(f"identity_hist_{arm_label}.json")
    if os.path.exists(done_path):
        return _load_json(done_path)

    if os.path.exists(partial_graph) and os.path.exists(progress_path):
        s = _load_graph(partial_graph)
        prog = _load_json(progress_path)
        print(f"  [{arm_label}] RESUMING at stroke {prog['n_done']}/{LEARN_STROKE_CAP}")
    else:
        s = _load_graph(graph_src)
        prog = dict(n_done=0, identity_hist={}, family_hist={}, n_mints=0, n_oov=0)

    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    strokes = _collect_learn_strokes(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
    t0 = time.time()
    total = len(strokes)
    while prog["n_done"] < total and (time.time() - t0) < PER_CALL_BUDGET_SECONDS:
        batch = strokes[prog["n_done"]:prog["n_done"] + BATCH_STROKES]
        tb = time.time()
        for points in batch:
            ink_node = ink.ingest_ink(s, points, max_knots=DK["max_knots"])
            res = ink.decode_ink(s, ink_node, min_span=DK["min_span"], max_span=DK["max_span"],
                                  segments=DK["segments"], turn_bins=DK["turn_bins"],
                                  len_bins=DK["len_bins"], grid=DK["grid"],
                                  scale_bins=DK["scale_bins"],
                                  turn_edges=turn_edges, len_edges=len_edges)
            for r in res.get("recognized", []):
                ident = r.get("name")
                if ident:
                    prog["identity_hist"][ident] = prog["identity_hist"].get(ident, 0) + 1
                fam = _sc._prototype_anchor(_sc._sub(s), r.get("family") or r.get("name")) \
                    or (r.get("family") or r.get("name"))
                if fam:
                    prog["family_hist"][fam] = prog["family_hist"].get(fam, 0) + 1
            prog["n_mints"] += len(res.get("minted", []))
            prog["n_oov"] += len(res.get("oov", []))
            prog["n_done"] += 1
        _save_graph(s, partial_graph)
        _save_json(prog, progress_path)
        print(f"  [{arm_label}] [batch] {prog['n_done']}/{total}  identities="
              f"{len(prog['identity_hist'])}  families={len(prog['family_hist'])}  "
              f"batch_wall={time.time()-tb:.1f}s  checkpointed.")

    if prog["n_done"] < total:
        print(f"  [{arm_label}] PARTIAL -- re-invoke '--stage entropy-report' to continue.")
        return None

    result = dict(identity_hist=prog["identity_hist"], family_hist=prog["family_hist"],
                   n_mints_during_measurement=prog["n_mints"], n_oov=prog["n_oov"],
                   n_strokes=prog["n_done"])
    _save_json(result, done_path)
    for p in (partial_graph, progress_path):
        if os.path.exists(p):
            os.remove(p)
    return result


def stage_entropy_report():
    """P2 — the identity-collapse metric, before/after, at TWO grains (documented refinement
    of the header's P2, measured not assumed): (a) FAMILY-ROOT grain (the run-28 scope:
    `_measure_stroke` anchors every refinement child back to its prototype-bearing root — the
    scope the 10,230/10,231 collapse was originally measured in); (b) RESOLVED-IDENTITY grain
    (`r["name"]`, the deepest match — the value downstream signatures/proposals actually
    consume, so THIS grain is where proposal-layer information content lives). Both reported;
    the P2 verdict is evaluated at the IDENTITY grain, with the root grain printed alongside
    (an identity-grain spread that vanishes at root grain is a finding about WHERE the new
    information sits, not a contradiction)."""
    print(f"\n{SEP}\n  STAGE: entropy-report (P2 -- the identity-collapse metric, before/after)\n{SEP}")
    control_calib = _run28("calibration_report.json")
    adapt_calib = _ckpt("calibration_report_adapt.json")
    control_graph = _run28("calibrated_learn.json")
    adapt_graph = _ckpt("calibrated_adapt.json")
    missing = [p for p in (control_calib, adapt_calib, control_graph, adapt_graph)
               if not os.path.exists(p)]
    if missing:
        print(f"  WALL: missing prerequisite file(s): {missing} -- run 'calibrate --arm adapt' first.")
        return 1

    turn_edges, len_edges = _load_edges()
    control_hist_res = _measure_identity_hist("control", control_graph, None, None)
    if control_hist_res is None:
        return 0
    adapt_hist_res = _measure_identity_hist("adapt", adapt_graph, turn_edges, len_edges)
    if adapt_hist_res is None:
        return 0

    def _row(label, hist):
        rep = ab.entropy_report([k for k, v in hist.items() for _ in range(v)]) if hist else \
            dict(n_families=0, n_observations=0, entropy_bits=0.0, top_family_share=None)
        print(f"    {label:<18} n={rep['n_observations']:>6}  groups={rep['n_families']:>4}  "
              f"entropy={rep['entropy_bits']:.4f} bits  top_share="
              f"{rep['top_family_share'] if rep['top_family_share'] is not None else '-'}")
        return rep

    print(f"\n  IDENTITY GRAIN (r['name'], what downstream composition consumes -- the P2 verdict grain):")
    ctrl_ident = _row("CONTROL (uniform)", control_hist_res["identity_hist"])
    adapt_ident = _row("ADAPT (quantile)", adapt_hist_res["identity_hist"])
    print(f"\n  FAMILY-ROOT GRAIN (prototype anchor -- the run-28 collapse's original scope):")
    ctrl_fam = _row("CONTROL (uniform)", control_hist_res["family_hist"])
    adapt_fam = _row("ADAPT (quantile)", adapt_hist_res["family_hist"])
    print(f"\n  measurement-time mints (counted, discarded with the throwaway graph copies): "
          f"control={control_hist_res['n_mints_during_measurement']}  "
          f"adapt={adapt_hist_res['n_mints_during_measurement']}")

    spread = bool(adapt_ident["entropy_bits"] > ctrl_ident["entropy_bits"] + 0.1
                  and adapt_ident["n_families"] > ctrl_ident["n_families"])
    print(f"\n  P2 (spans spread meaningfully under quantile edges, IDENTITY grain): "
          f"{'CONFIRMED' if spread else 'STOP -- NOT SPREADING (report + stop per pre-registration)'}")

    result = dict(identity=dict(control=ctrl_ident, adapt=adapt_ident),
                  family_root=dict(control=ctrl_fam, adapt=adapt_fam),
                  control_measurement=control_hist_res, adapt_measurement=adapt_hist_res,
                  p2_spread_confirmed=spread,
                  verdict_grain="identity (r['name'] -- what downstream composition consumes)")
    _save_json(result, _ckpt("entropy_report.json"))
    print(f"\n  saved -> {_ckpt('entropy_report.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0 if spread else 2


# ---------------------------------------------------------------------------------------------
# STAGE: eval --arm {adapt,adapt_residual} -- P1's own measurement, block-checkpointed exactly
# per run26's stage_eval (SAME test alphabets, SAME POWER_SEED rng replay, SAME SHORTLIST_K,
# n=400): coverage@10 + shortlist accuracy on the arm's calibrated graph; full-dwell (P7
# spot-check) at block 0 only. The CONTROL is run26's eval_baseline.json, REUSED verbatim
# (never re-run). The `adapt_residual` arm passes the query's/exemplars' own sub-bin
# residuals into `ar.propose_top_k`'s residual-aware tiebreak; `adapt` passes None (proposal
# arithmetic byte-identical to the pre-run-32 path). A DISK-BACKED decode cache
# (eval_cache_{arm}.json) persists exemplar/query decodes across invocations -- decode at
# codebook 132 is ~10x costlier than run26's, and blocks re-decode the same drawings.
# ---------------------------------------------------------------------------------------------
def _finalize_eval(state: dict) -> None:
    records = state["records"]
    full_records = [r for r in records if "pred_full" in r]
    if full_records:
        k_full = sum(1 for r in full_records if r["pred_full"] == r["true"])
        acc_full = k_full / len(full_records)
        state["full_dwell"] = dict(acc=acc_full, ci=list(gate.wilson_ci(k_full, len(full_records))),
                                    n=len(full_records), k=k_full)
    n = len(records)
    k_cov = sum(1 for r in records if r["in_shortlist"])
    k_sl = sum(1 for r in records if r["pred_shortlist"] == r["true"])
    state["coverage"] = dict(cov=(k_cov / n if n else 0.0), ci=list(gate.wilson_ci(k_cov, n)),
                              k=k_cov, n=n)
    state["shortlist_acc"] = dict(acc=(k_sl / n if n else 0.0), ci=list(gate.wilson_ci(k_sl, n)),
                                   k=k_sl, n=n)


def stage_eval(arm: str):
    print(f"\n{SEP}\n  STAGE: eval --arm {arm}\n{SEP}")
    if arm not in ARMS:
        print(f"  WALL: unknown arm {arm!r} -- must be one of {ARMS}")
        return 1
    graph_src = _ckpt(f"calibrated_{arm}.json")
    if not os.path.exists(graph_src):
        print(f"  WALL: run 'calibrate --arm {arm}' first.")
        return 1
    ent = _load_json(_ckpt("entropy_report.json")) if os.path.exists(_ckpt("entropy_report.json")) else None
    if ent is None or not ent.get("p2_spread_confirmed"):
        print("  WALL: eval is GATED on P2 (entropy-report must be complete and CONFIRMED).")
        return 1

    out_path = _ckpt(f"eval_{arm}.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False)
    if state.get("done"):
        print(f"  eval --arm {arm} already COMPLETE (n={len(state['records'])}).")
        return 0

    turn_edges, len_edges = _load_edges()
    use_residual = (arm == "adapt_residual")
    s = _load_graph(graph_src)
    native = s._inner

    cache_path = _ckpt(f"eval_cache_{arm}.json")
    cache = _load_json(cache_path) if os.path.exists(cache_path) else {}

    test_alphabets = _test_alphabets()
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  arm={arm}  test_alphabets={test_alphabets}  blocks={len(blocks)} "
          f"(target n={len(blocks) * WAY})  SHORTLIST_K={SHORTLIST_K}  use_residual={use_residual}  "
          f"resuming at block {state['block_idx']}  cache_entries={len(cache)}")

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

        full_dwell_this_block = (state["block_idx"] == 0)      # P7 spot-check only.
        scratch0 = cand0 = None
        if full_dwell_this_block:
            scratch0 = srs.Substrate()
            _, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                                thetas=ar.DEFAULT_PARSE_THETAS)

        exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, DK,
                                                 turn_edges=turn_edges, len_edges=len_edges,
                                                 collect_residuals=use_residual)
                     for ci in range(WAY)]
        exemplar_composed = [e["composed_sig"] for e in exemplars]
        exemplar_residuals = [e.get("residuals") or [] for e in exemplars] if use_residual else None

        for qi, q_drawer in spec["queries"]:
            path = drawer_files[qi][q_drawer]
            rec = {"true": qi, "alph": alph, "r": r}
            if full_dwell_this_block:
                qn0 = ar.stage_parse_char(scratch0, path, is_query=True,
                                           thetas=ar.DEFAULT_PARSE_THETAS)
                w0 = ar.parse_marginal_verdict(scratch0, qn0)
                rec["pred_full"] = cand0.get(w0, -1) if w0 is not None else -1

            qd = gate.decode_char_signature(s, path, cache, DK, turn_edges=turn_edges,
                                             len_edges=len_edges, collect_residuals=use_residual)
            if use_residual:
                shortlist = ar.propose_top_k(native, qd["composed_sig"], exemplar_composed,
                                              k=SHORTLIST_K,
                                              query_residuals=qd.get("residuals") or [],
                                              exemplar_residuals=exemplar_residuals)
            else:
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
            state["records"].append(rec)

        state["block_idx"] += 1
        _save_json(state, out_path)
        _save_json(cache, cache_path)
        print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
              f"{len(state['records'])} episodes so far, {time.time() - t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        _finalize_eval(state)
        _save_json(state, out_path)
        print(f"\n  EVAL COMPLETE for {arm}: n={len(state['records'])}")
        if "full_dwell" in state:
            fd = state["full_dwell"]
            print(f"    full-dwell spot-check (P7, block 0):  acc={100*fd['acc']:.1f}%  "
                  f"n={fd['n']}")
        cov, sl = state["coverage"], state["shortlist_acc"]
        print(f"    coverage@{SHORTLIST_K}:      {100*cov['cov']:.1f}%  95% CI "
              f"[{100*cov['ci'][0]:.1f}%, {100*cov['ci'][1]:.1f}%]  n={cov['n']}")
        print(f"    shortlist accuracy:  {100*sl['acc']:.1f}%  95% CI "
              f"[{100*sl['ci'][0]:.1f}%, {100*sl['ci'][1]:.1f}%]  n={sl['n']}")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- re-invoke "
              f"'--stage eval --arm {arm}' to continue.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: report -- assemble everything against the reused CONTROL.
# ---------------------------------------------------------------------------------------------
def stage_report():
    print(f"\n{SEP}\n  RUN 32 -- SUB-QUANTUM (OPTION R) -- FINAL REPORT\n{SEP}")
    ev_base = _load_json(_run26("eval_baseline.json"))
    ent = _load_json(_ckpt("entropy_report.json")) if os.path.exists(_ckpt("entropy_report.json")) else None
    edges = _load_json(_ckpt("edges_report.json")) if os.path.exists(_ckpt("edges_report.json")) else None

    print(f"\n  EDGES (amendment-deduped quantile): "
          f"turn {edges['turn_bins_requested']}->{edges['turn_bins_effective']} eff, "
          f"len {edges['len_bins_requested']}->{edges['len_bins_effective']} eff" if edges else "  EDGES: missing")
    if ent:
        ci_, ai_ = ent["identity"]["control"], ent["identity"]["adapt"]
        print(f"  P2 IDENTITY-GRAIN ENTROPY: control {ci_['entropy_bits']:.4f} bits "
              f"({ci_['n_families']} ids) -> adapt {ai_['entropy_bits']:.4f} bits "
              f"({ai_['n_families']} ids)  "
              f"{'CONFIRMED' if ent['p2_spread_confirmed'] else 'STOP'}")

    base_cov, base_sl = ev_base["coverage"], ev_base["shortlist_acc"]
    base_fd = ev_base.get("full_dwell")
    print(f"\n  CONTROL (run26 baseline, reused): coverage@{SHORTLIST_K}="
          f"{100*base_cov['cov']:.1f}% [{100*base_cov['ci'][0]:.1f},{100*base_cov['ci'][1]:.1f}]  "
          f"shortlist={100*base_sl['acc']:.1f}%  "
          f"full_dwell={100*base_fd['acc']:.1f}%" if base_fd else "")

    base_records = ev_base["records"]
    summary = {}
    for arm in ARMS:
        p = _ckpt(f"eval_{arm}.json")
        if not os.path.exists(p):
            print(f"\n  ARM {arm}: eval not started.")
            continue
        ev = _load_json(p)
        if not ev.get("done"):
            print(f"\n  ARM {arm}: eval IN PROGRESS ({ev.get('block_idx')} blocks).")
            continue
        cov, sl = ev["coverage"], ev["shortlist_acc"]
        sep_cov = gate._ci_separated(tuple(cov["ci"]), tuple(base_cov["ci"]))
        print(f"\n  ARM {arm}: n={cov['n']}")
        print(f"    coverage@{SHORTLIST_K}={100*cov['cov']:.1f}% "
              f"[{100*cov['ci'][0]:.1f},{100*cov['ci'][1]:.1f}]  vs control "
              f"{100*base_cov['cov']:.1f}%  CI-separated: {sep_cov}  (P1)")
        print(f"    shortlist_acc={100*sl['acc']:.1f}% "
              f"[{100*sl['ci'][0]:.1f},{100*sl['ci'][1]:.1f}]  vs control {100*base_sl['acc']:.1f}%  (P6)")
        if "full_dwell" in ev:
            fd = ev["full_dwell"]
            print(f"    full-dwell block-0 spot-check: {100*fd['acc']:.1f}% (n={fd['n']}) "
                  f"vs control full-dwell {100*base_fd['acc']:.1f}%  (P7)")
        # Newly-covered / lost episode analysis (mandatory per pre-registration): records
        # align by construction -- SAME POWER_SEED, SAME block/episode order as run26.
        n_align = min(len(base_records), len(ev["records"]))
        newly = sum(1 for i in range(n_align)
                    if ev["records"][i]["in_shortlist"] and not base_records[i]["in_shortlist"])
        lost = sum(1 for i in range(n_align)
                   if not ev["records"][i]["in_shortlist"] and base_records[i]["in_shortlist"])
        print(f"    episode residual: newly_covered={newly}  lost={lost}  (aligned n={n_align})")
        summary[arm] = dict(coverage=cov, shortlist=sl, newly_covered=newly, lost=lost,
                             ci_separated_vs_control=bool(sep_cov),
                             full_dwell=ev.get("full_dwell"))

    _save_json(dict(control=dict(coverage=base_cov, shortlist=base_sl, full_dwell=base_fd),
                     entropy=ent and dict(identity=ent["identity"],
                                           p2=ent["p2_spread_confirmed"]),
                     arms=summary), _ckpt("report.json"))
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
                             "eval", "report"])
    p.add_argument("--arm", choices=ARMS, default=None)
    args = p.parse_args()
    t0 = time.time()
    if args.stage == "verify":
        rc = stage_verify()
    elif args.stage == "gather-edges":
        rc = stage_gather_edges()
    elif args.stage == "learn":
        if not args.arm:
            print("  WALL: --stage learn requires --arm {adapt,adapt_residual}")
            rc = 1
        else:
            rc = stage_learn(args.arm)
    elif args.stage == "calibrate":
        if not args.arm:
            print("  WALL: --stage calibrate requires --arm {adapt,adapt_residual}")
            rc = 1
        else:
            rc = stage_calibrate(args.arm)
    elif args.stage == "entropy-report":
        rc = stage_entropy_report()
    elif args.stage == "eval":
        if not args.arm:
            print("  WALL: --stage eval requires --arm {adapt,adapt_residual}")
            rc = 1
        else:
            rc = stage_eval(args.arm)
    elif args.stage == "report":
        rc = stage_report()
    else:
        rc = 1
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
