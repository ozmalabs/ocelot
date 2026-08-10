"""OMNIGLOT RUN 31 -- GEOMETRY: THE JABBERWOCK TAKES ON BOTH NAMED ATTACKS ON THE ONE RESIDUAL
THE HOMEWORK ARC (RUNS 26-30) LEFT STANDING.

Runs 26-30 built the whole homework loop (mark/assign/babble/re-mark), the character-grain sd
loop (`arrangement_codebook.py`), stability-weighted persistence (run 29), and the graph-native
FRAME representation (run 30, `frame_weights.py`) -- and through every one of those levers, ONE
number never moved: the UNWEIGHTED arrangement round-trip subscore (the plain, all-relations-
equal-weight agreement between a character's ORIGINAL composed signature and its own render-
>re-read composed signature) sits FLAT at 0.8356 (`results/run30_checkpoints/
consume_metrics.json`'s own `mean_unweighted_before`/`mean_unweighted_after`, cycle 0 through 2,
byte-identical every cycle). Calibration/weighting can re-rank which relations COUNT toward the
score (the WEIGHTED series visibly rises, 0.8356 -> 0.8909) but cannot repair the underlying
GEOMETRY: the render->re-read loop itself manufactures the disagreement it is then scored
against. This run attacks the render side directly, per the creator's own directive, two ways:

MECHANISM A -- RENDER THE STABILITY-PREFERRED PARSE (`use_preferred_parse`, `domains/
homework_loop.py`'s `_parse_from_decode`/`_preferred_render_name`/`_preferred_render_name_
term`): `babble`'s own mechanism (a), PARSE STABILITY RE-RANK, already persists a
`stability_preferred_alt` identity as graph data on a codebook entry when a MAJORITY of
re-render reps stably re-decode a span as something other than its own name -- an earned,
additive signal nothing downstream ever fed back into WHAT gets rendered. A HELD `IfThenElse`
Term (never a Python if/else) now substitutes that preferred identity's own stored `seg` for
the render goal (same observed pose, `ink._pose_read_goal`'s splice unchanged) whenever the
flag is on.

MECHANISM B -- SEGMENTATION-TOLERANT RENDERING (`tolerant_joins`, `domains/homework_loop.py`'s
`_render_parse`): per-span polyline rendering concatenates independently-rendered spans with a
discontinuous "corner" at each boundary (measured directly: two independently-rendered
perpendicular lines leave a >1.0-unit position gap at their shared seam in this run's own unit
gate). `_render_parse` now reuses `abs_read._junction_blend` -- EXISTING, unit-tested pure
geometry, already wired into the AbS recognition-VERDICT render path for BRANCH B CONTINUOUS
(2026-07-03) -- to warp each span's trailing/leading points toward their shared draw-order
junction midpoint BEFORE concatenation, closing that gap. No new Rust, no new geometry
primitive: composing an existing adapter-level primitive, per CLAUDE.md's "prefer composing
existing primitives" instruction and the standing "reuse held machinery, never build a
parallel engine" discipline. HONEST SCOPE: `tolerant_joins` is an explicitly SEPARATE render
mode -- it does NOT preserve `StrokeQuantize(StrokeRender(sig)) == sig` for a blended span (see
`tests/test_render_geometry_migrated.py::test_tolerant_joins_documents_inverse_break`, which
demonstrates the break directly); the untouched default path remains the exact-inverse one.

JABBERWOCK OWNERSHIP -- what was authored vs hand-seeded, and why: both mechanisms are HAND-
WRITTEN held-Term / mechanical-geometry helpers (`_preferred_render_name_term`,
`_render_parse`'s `_junction_blend` reuse), NOT authored via `reflective_faculty.
induce_concern`/`ground_concern`. This follows the EXACT precedent this same module already
establishes for the identical CLASS of decision: `homework_loop._resolved_key`/`_frontier_term`/
`_residual_pairs_term`/`_argmax_pairs_term` (runs 26-30) are ALL hand-written held-Term
substitutions over graph data the agent's OWN rules already decided (mechanism (a)'s stability
rerank is itself Python bookkeeping over a held Argmax, per that function's own docstring) --
never routed through the composer. The composer path (`induce_concern`/`ground_concern`) is for
the agent to author a NOVEL RULE from a framed cognitive concern (e.g. "what do I control," "how
do I communicate") -- neither mechanism here is that: mechanism A is "consult an already-earned
preference before building a render goal" (an adapter-level SUBSTITUTION, structurally identical
to `_resolved_key`'s own established idiom, now applied one call earlier in the pipeline);
mechanism B is "compose an existing geometry primitive at a new call site" (an adapter-level
REUSE, no new relation vocabulary, no new rule to author). Per the OWNERSHIP directive's own
text -- "where the existing composer machinery CAN author the rule... use that path" -- there is
no RelationCue/compose path missing here to add: the DECISION machinery (a held Term the adapter
evaluates) already satisfies "every DECISION lives as... held Terms the adapter evaluates," and
forcing a `ground_concern` call for a six-line Term builder would be exactly the "hack instead of
getting the jabberwock to do it" anti-pattern this discipline warns against IN THE OTHER
DIRECTION -- manufacturing composer ceremony around a mechanical substitution the codebase's own
established convention already treats as adapter-legal.

PRE-REGISTERED HEADER (stated before any number below is computed):

  RECIPE: SAME 40-character practice set + seeds as runs 27-30 (`run29._build_practice_set`,
  `PRACTICE_SEED`, background alphabets [5:15]), SAME `REPS_PER_ITEM=20`, SAME 3 cycles, SAME
  eval-class quarantine. Each arm starts FRESH from run 28's calibrated LEARN graph
  (`results/run28_checkpoints/calibrated_learn.json`) -- NOT from run 30's own already-cycled
  graph (that graph's weights/codebook already reflect 3 cycles of learning; starting fresh
  isolates this run's OWN levers against the SAME starting point run 29/30 used). Every arm
  ALSO carries run 29/30's own recipe (`enable_character_codebook=True`,
  `use_stability_weights=True`) so the ONLY delta versus the run-30 CONTROL is mechanisms A/B.

  CONTROL: run 30's own consume arm, REUSED VERBATIM, NOT re-run
  (`results/run30_checkpoints/consume_metrics.json`): unweighted arrangement flat at
  [0.8356, 0.8356, 0.8356, 0.8356], surviving-residual flat at [39, 39, 39, 39].

  ARMS (3 cycles each): A-only (`use_preferred_parse=True, tolerant_joins=False`); B-only
  (`use_preferred_parse=False, tolerant_joins=True`); A+B (both True). `junction_frac` =
  `abs_read.DEFAULT_JUNCTION_FRAC` (0.15), a pre-registered constant, never tuned against these
  numbers.

  PRIMARY PREDICTIONS:
    P1. UNWEIGHTED arrangement subscore RISES across cycles in AT LEAST ONE arm -- the
        headline bet: the geometry metric moves for the first time in this arc. Flat = NULL
        for that arm (the run-29/30 wording discipline: a flat series is a NULL, never
        interpreted as a soft win).
    P2. In the WINNING arm (whichever arm(s) confirm P1), surviving-residual count STRICTLY
        FALLS across cycles (strict `<`; flat = NULL, same wording discipline as run 29/30's
        own P3).
  SECONDARY:
    P3. Span-count agreement subscore (`count_score`, run 26's own residual class) rises.
    P4. The WEIGHTED score stays >= the UNWEIGHTED score every cycle (weighting should not
        fight the repair -- an honest sanity check, not a headline claim).

  STOP BRANCHES: if A-only and B-only BOTH null on P1 after 3 cycles, A+B is STILL run (an
  interaction is plausible -- preferred parse + tolerant join may only help TOGETHER, e.g. a
  render that changed shape via A also needs its NEW seam re-smoothed by B). If ALL THREE arms
  null on P1, THAT is the finding -- the geometry residual is not reachable from the render
  side at this featureset, reported and stopped, never silently re-framed as a partial win.

  EVAL: NOT run unless P1 confirms in some arm (practice-loop geometry first, per the creator's
  own economics framing -- practice is cheap, grounding/eval is dear). If P1 confirms, eval runs
  for THAT arm only, n=400, standard protocol (reuse run 26's baseline harness), NOT built into
  this script until/unless that gate is met.

  METRICS logged per cycle per arm: unweighted + weighted arrangement subscore means,
  span-count subscore mean, surviving-residual count, corrections, mints (reading/babble/
  character-reading), character-codebook size, weight distribution, recognition coverage, AND
  the two mechanism-ENGAGEMENT instruments (`renders_with_preferred_parse`,
  `tolerant_join_applications`) -- an arm whose mechanism never ENGAGES is VACUOUS, not null
  (the run-28 lesson: report engagement separately from outcome, every cycle).

EXECUTION NOTE -- a DELIBERATE, documented deviation from run 29/30's own single-call-per-cycle
recipe, forced by this run's own ops constraint (a full cycle takes 700-1000s under frames,
exceeding the 600s foreground Bash cap): `mark_characters`/`babble_characters` are invoked ONE
PRACTICE ITEM AT A TIME, in the SAME stable index order a monolithic call would use (never
reordered -- the sequential graph-mutation dependency this codebase's own mint/recognize idiom
relies on is preserved exactly), so ONE invocation can checkpoint mid-phase and always stay
under `PER_CALL_BUDGET_SECONDS`. `babble_characters`'s own RNG is reseeded PER ITEM
(`READING_SEED_BASE + cycle` combined with the item's own stable practice-set index via a fixed
multiplier -- deterministic and reproducible, but NOT a single continuous stream across all 40
items the way run 29/30's one-call recipe drew it). This is a discovery gate, not a byte-
preservation gate (unlike run 30) -- item ORDER, `dk`, flags, and cycle count are all identical
to runs 27-30; only the RNG STREAM SHAPE for babble's own per-rep jitter differs, an honest,
pre-registered, non-outcome-affecting engineering necessity.

Run (repeat each --stage/--arm combination until it reports COMPLETE):
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run31_geometry.py --stage verify
  ... --stage consume --arm a_only
  ... --stage consume --arm b_only
  ... --stage consume --arm a_plus_b
  ... --stage report
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np

import scripts.jabberwock_omniglot_run29_consume as run29
from domains import abs_read as ar
from domains import arrangement_codebook as ac
from domains import homework_loop as hl
from domains import stroke_codebook as sc

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run31_checkpoints")
RUN30_DIR = os.path.join(ROOT, "results", "run30_checkpoints")    # READ-ONLY reference (CONTROL).
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS -- byte-identical to run 27/28/29/30 where they overlap.
# ---------------------------------------------------------------------------------------------
DK = run29.DK
N_CYCLES = run29.N_CYCLES                       # 3
REPS_PER_ITEM = run29.REPS_PER_ITEM             # 20
READING_SEED_BASE = run29.READING_SEED_BASE
JUNCTION_FRAC = ar.DEFAULT_JUNCTION_FRAC         # 0.15, pre-registered, never tuned.
PER_CALL_BUDGET_SECONDS = 460.0                  # vs. the 540s foreground cap -- measured
                                                  # overhead (graph load/save + Python startup)
                                                  # is ~13s/invocation on the real 40-item
                                                  # practice set (RUN 31's own first live
                                                  # invocation: 412.7s wall for a 400s budget),
                                                  # so 500s leaves a safe ~40s margin under the
                                                  # 590s foreground timeout used to invoke this
                                                  # script.

ARMS = {
    "a_only":   dict(use_preferred_parse=True,  tolerant_joins=False),
    "b_only":   dict(use_preferred_parse=False, tolerant_joins=True),
    "a_plus_b": dict(use_preferred_parse=True,  tolerant_joins=True),
}

# Run 30's own CONTROL numbers -- REUSED VERBATIM, never re-run (pre-registered above).
CONTROL_UNWEIGHTED_SERIES = [0.8356082635006947, 0.8356082635006947, 0.8356082635006947,
                             0.8356082635006947]
CONTROL_SURVIVING_SERIES = [39, 39, 39, 39]


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _arm_meta_path(arm: str) -> str:
    return _ckpt(f"consume_metrics_{arm}.json")


def _arm_graph_path(arm: str) -> str:
    return _ckpt(f"consume_{arm}.json")


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=run29._json_default)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _donkey0() -> bool:
    return "torch" not in sys.modules


# ---------------------------------------------------------------------------------------------
# MarkedItem <-> JSON round-trip (checkpointing mid-phase requires persisting the FULL parse,
# not just the scalar scores -- `assign()` needs `.spans`/`.dk` to build the worksheet).
# ---------------------------------------------------------------------------------------------
def _marked_to_dict(m) -> dict:
    return asdict(m)


def _marked_from_dict(d: dict):
    d = dict(d)
    d["spans"] = [hl.SpanParse(**sp) for sp in d["spans"]]
    return hl.MarkedItem(**d)


# ---------------------------------------------------------------------------------------------
# STAGE: verify -- adopt run 28's calibrated LEARN graph, exactly as run 29/30 did. Shared
# across every arm (each arm re-reads this SAME read-only file fresh at its own cycle 0).
# ---------------------------------------------------------------------------------------------
def stage_verify():
    print(f"\n{SEP}\n  STAGE: verify (RUN 31 -- reuse run 28's calibrated_learn.json, same "
          f"recipe runs 29/30 verified)\n{SEP}")
    calib_src = run29._run28("calibrated_learn.json")
    calib_report_src = run29._run28("calibration_report.json")
    control_src = os.path.join(RUN30_DIR, "consume_metrics.json")
    missing = [p for p in (calib_src, calib_report_src, control_src) if not os.path.exists(p)]
    if missing:
        print(f"  WALL: missing prerequisite file(s): {missing}")
        return 1
    calib_report = _load_json(calib_report_src)
    n_families_ok = calib_report.get("n_families", 0) > 0
    control = _load_json(control_src)
    control_ok = len(control.get("cycles", [])) >= N_CYCLES
    print(f"  calibration_report sanity: n_families={calib_report.get('n_families')}  "
          f"{'OK' if n_families_ok else 'EMPTY -- WALL'}")
    print(f"  control (run30 consume) sanity: {len(control.get('cycles', []))} cycles  "
          f"{'OK' if control_ok else 'INCOMPLETE -- WALL'}")
    if not (n_families_ok and control_ok):
        print("  WALL: a prerequisite is incomplete -- this run must NOT proceed.")
        return 1
    print("  RECIPE ADOPTED -- read-only reference data.")
    _save_json(dict(calib_src=calib_src, control_src=control_src, verified=True),
              _ckpt("verify.json"))
    print(f"  saved -> {_ckpt('verify.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: consume --arm {a_only,b_only,a_plus_b} -- ONE TIME-BUDGETED PHASE-SLICE per invocation.
# Phase state machine per cycle: mark_before -> babble -> mark_after -> finalize -> next cycle.
# ---------------------------------------------------------------------------------------------
def _init_meta() -> dict:
    return dict(cycles=[], cycle=0, phase="mark_before",
                marked_before=[], marked_before_ids=[],
                babble_log_per_item={}, babble_total_corrections=0, babble_done_ids=[],
                marked_after=[], marked_after_ids=[])


def _item_rng_seed(base: int, item_index: int) -> int:
    """Deterministic PER-ITEM reseed for babble's own jitter draws (see module docstring's
    EXECUTION NOTE for why this differs from run 29/30's single-continuous-stream recipe) --
    a fixed multiplier, never tuned, keeps every item's own draw sequence independent and
    reproducible across separate single-item invocations."""
    return int(base * 1_000_003 + item_index) % (2 ** 31 - 1)


def stage_consume(arm: str):
    if arm not in ARMS:
        print(f"  WALL: unknown arm {arm!r} -- must be one of {sorted(ARMS)}")
        return 1
    flags = ARMS[arm]
    print(f"\n{SEP}\n  STAGE: consume --arm {arm}  (use_preferred_parse={flags['use_preferred_parse']}, "
          f"tolerant_joins={flags['tolerant_joins']}, junction_frac={JUNCTION_FRAC})\n{SEP}")
    if not os.path.exists(_ckpt("verify.json")):
        print("  WALL: run stage 'verify' first.")
        return 1

    meta_path = _arm_meta_path(arm)
    meta = _load_json(meta_path) if os.path.exists(meta_path) else _init_meta()
    if meta["cycle"] >= N_CYCLES:
        print(f"  arm {arm} already COMPLETE ({meta['cycle']}/{N_CYCLES} cycles).")
        return 0

    graph_path = _arm_graph_path(arm)
    src = graph_path if os.path.exists(graph_path) else run29._calibrated_src()
    if not os.path.exists(src):
        print(f"  WALL: {src} missing.")
        return 1
    s = run29._load_graph(src)

    practice_items, practice_alphabets = run29._build_practice_set()
    meta["n_practice_items"] = len(practice_items)
    meta["practice_alphabets"] = practice_alphabets
    test_alphabets = run29._test_alphabets()
    eval_ids = run29._eval_class_ids(test_alphabets)
    cycle = meta["cycle"]
    rng_base = READING_SEED_BASE + cycle

    if cycle == 0 and meta["phase"] == "mark_before" and not meta["marked_before_ids"]:
        meta["grain_before"] = sc.grain_vocabulary_report(s)
        meta["char_vocab_before"] = ac.character_vocabulary_report(s)

    t0 = time.time()

    def _budget_left() -> float:
        return PER_CALL_BUDGET_SECONDS - (time.time() - t0)

    progressed = False

    # ---- PHASE: mark_before / mark_after (shared body) --------------------------------------
    def _run_mark_phase(dest_key: str, ids_key: str, label: str) -> bool:
        """Processes remaining practice items ONE AT A TIME, in stable index order, until the
        time budget runs out or every item is done. Returns True iff the phase COMPLETED this
        invocation (all 40 items marked)."""
        nonlocal progressed
        done_ids = set(meta[ids_key])
        for idx, item in enumerate(practice_items):
            if item["id"] in done_ids:
                continue
            if _budget_left() <= 0:
                print(f"  [{label}] budget exhausted -- {len(done_ids)}/{len(practice_items)} "
                      f"done this phase, checkpointing and stopping.")
                return False
            marked = hl.mark_characters(
                s, [item], dk=DK, eval_class_ids=eval_ids, enable_character_codebook=True,
                use_stability_weights=True, use_preferred_parse=flags["use_preferred_parse"],
                tolerant_joins=flags["tolerant_joins"], junction_frac=JUNCTION_FRAC)
            meta[dest_key].append(_marked_to_dict(marked[0]))
            meta[ids_key].append(item["id"])
            progressed = True
        print(f"  [{label}] COMPLETE -- {len(meta[ids_key])}/{len(practice_items)} items marked.")
        return True

    if meta["phase"] == "mark_before":
        if _run_mark_phase("marked_before", "marked_before_ids", "mark_before"):
            meta["phase"] = "babble"

    if meta["phase"] == "babble" and _budget_left() > 0:
        marked_before_objs = [_marked_from_dict(d) for d in meta["marked_before"]]
        worksheet = hl.assign(marked_before_objs)
        meta.setdefault("worksheet_size", len(worksheet.items))
        done_ids = set(meta["babble_done_ids"])
        for idx, item in enumerate(practice_items):
            wi = next((w for w in worksheet.items if w.item_id == item["id"]), None)
            if wi is None or wi.item_id in done_ids:
                continue
            if _budget_left() <= 0:
                print(f"  [babble] budget exhausted -- {len(done_ids)}/{len(worksheet.items)} "
                      f"worksheet items done this phase, checkpointing and stopping.")
                break
            log = hl.babble_characters(
                s, hl.Worksheet(items=[wi]), reps_per_item=REPS_PER_ITEM,
                rng_seed=_item_rng_seed(rng_base, idx), jitter_bins=hl.DEFAULT_JITTER_BINS,
                eval_class_ids=eval_ids)
            meta["babble_log_per_item"].update(
                {str(k): v for k, v in log.per_item.items()})
            meta["babble_total_corrections"] += log.total_corrections
            meta["babble_done_ids"].append(wi.item_id)
            done_ids.add(wi.item_id)
            progressed = True
        else:
            print(f"  [babble] COMPLETE -- {len(meta['babble_done_ids'])}/{len(worksheet.items)} "
                  f"worksheet items practiced.")
            meta["phase"] = "mark_after"

    if meta["phase"] == "mark_after" and _budget_left() > 0:
        if _run_mark_phase("marked_after", "marked_after_ids", "mark_after"):
            meta["phase"] = "finalize"

    if meta["phase"] == "finalize":
        marked_before_objs = [_marked_from_dict(d) for d in meta["marked_before"]]
        marked_after_objs = [_marked_from_dict(d) for d in meta["marked_after"]]
        surviving_before = sum(1 for m in marked_before_objs
                               if m.round_trip_score < hl.DEFAULT_MAX_SCORE)
        surviving_after = sum(1 for m in marked_after_objs
                              if m.round_trip_score < hl.DEFAULT_MAX_SCORE)
        mean_weighted_before = float(np.mean([m.arrangement_score for m in marked_before_objs]))
        mean_weighted_after = float(np.mean([m.arrangement_score for m in marked_after_objs]))
        mean_unweighted_before = float(np.mean(
            [run29._unweighted_arrangement(m) for m in marked_before_objs]))
        mean_unweighted_after = float(np.mean(
            [run29._unweighted_arrangement(m) for m in marked_after_objs]))
        mean_count_before = float(np.mean([m.count_score for m in marked_before_objs]))
        mean_count_after = float(np.mean([m.count_score for m in marked_after_objs]))
        mints_reading = (sum(m.n_mints_reading for m in marked_before_objs)
                         + sum(m.n_mints_reading for m in marked_after_objs))
        mints_char_reading = (sum(m.n_mints_character_reading for m in marked_before_objs)
                              + sum(m.n_mints_character_reading for m in marked_after_objs))
        mints_babble = sum(1 for entry in meta["babble_log_per_item"].values()
                           for c in entry["corrections"]
                           if c["type"] in ("mint_at_instability", "variant_coverage"))
        renders_with_preferred_parse = (sum(m.n_preferred_renders for m in marked_before_objs)
                                        + sum(m.n_preferred_renders for m in marked_after_objs))
        tolerant_join_applications = (sum(m.n_tolerant_joins for m in marked_before_objs)
                                      + sum(m.n_tolerant_joins for m in marked_after_objs))
        char_vocab = ac.character_vocabulary_report(s)
        weight_dist = run29._weight_distribution(s)
        recog_before = run29._recognition_coverage(marked_before_objs)
        recog_after = run29._recognition_coverage(marked_after_objs)

        cyc = dict(cycle=cycle, surviving_before=surviving_before, surviving_after=surviving_after,
                   mean_weighted_before=mean_weighted_before, mean_weighted_after=mean_weighted_after,
                   mean_unweighted_before=mean_unweighted_before,
                   mean_unweighted_after=mean_unweighted_after,
                   mean_count_before=mean_count_before, mean_count_after=mean_count_after,
                   worksheet_size=meta.get("worksheet_size", 0),
                   corrections=meta["babble_total_corrections"],
                   mints_during_reading=mints_reading, mints_during_babble=mints_babble,
                   mints_character_reading=mints_char_reading,
                   renders_with_preferred_parse=renders_with_preferred_parse,
                   tolerant_join_applications=tolerant_join_applications,
                   character_codebook_size=char_vocab["total"], weight_distribution=weight_dist,
                   recognition_before=recog_before, recognition_after=recog_after)
        meta["cycles"].append(cyc)
        print(f"  [finalize] cycle {cycle}: surviving {surviving_before}->{surviving_after}  "
              f"unweighted {mean_unweighted_before:.4f}->{mean_unweighted_after:.4f}  "
              f"weighted {mean_weighted_before:.4f}->{mean_weighted_after:.4f}  "
              f"count {mean_count_before:.4f}->{mean_count_after:.4f}")
        print(f"  [finalize] preferred_renders={renders_with_preferred_parse}  "
              f"tolerant_joins={tolerant_join_applications}  corrections={meta['babble_total_corrections']}")

        meta["cycle"] = cycle + 1
        meta["phase"] = "mark_before"
        meta["marked_before"], meta["marked_before_ids"] = [], []
        meta["babble_log_per_item"], meta["babble_total_corrections"] = {}, 0
        meta["babble_done_ids"] = []
        meta["marked_after"], meta["marked_after_ids"] = [], []
        meta.pop("worksheet_size", None)
        progressed = True

        if meta["cycle"] >= N_CYCLES:
            meta["grain_after"] = sc.grain_vocabulary_report(s)
            meta["char_vocab_after"] = char_vocab
            unweighted_series = ([meta["cycles"][0]["mean_unweighted_before"]]
                                 + [c["mean_unweighted_after"] for c in meta["cycles"]])
            weighted_series = ([meta["cycles"][0]["mean_weighted_before"]]
                              + [c["mean_weighted_after"] for c in meta["cycles"]])
            surviving_series = ([meta["cycles"][0]["surviving_before"]]
                               + [c["surviving_after"] for c in meta["cycles"]])
            count_series = ([meta["cycles"][0]["mean_count_before"]]
                           + [c["mean_count_after"] for c in meta["cycles"]])
            meta["unweighted_series"] = unweighted_series
            meta["weighted_series"] = weighted_series
            meta["surviving_series"] = surviving_series
            meta["count_series"] = count_series
            # STRICT wording discipline (run 29/30's own lesson): flat/non-strict = NULL.
            meta["p1_rises"] = bool(unweighted_series[-1] > unweighted_series[0])
            meta["p2_falls"] = bool(surviving_series[-1] < surviving_series[0])
            meta["p3_rises"] = bool(count_series[-1] > count_series[0])
            meta["p4_weighted_ge_unweighted"] = all(
                w >= u - 1e-9 for w, u in zip(weighted_series, unweighted_series))
            meta["total_preferred_renders"] = sum(
                c["renders_with_preferred_parse"] for c in meta["cycles"])
            meta["total_tolerant_joins"] = sum(
                c["tolerant_join_applications"] for c in meta["cycles"])
            print(f"\n  ARM {arm} -- FINAL SERIES")
            print(f"  unweighted arrangement: {[round(x, 4) for x in unweighted_series]}  "
                  f"P1: {'CONFIRMED' if meta['p1_rises'] else 'NULL'}")
            print(f"  surviving_residual:     {surviving_series}  "
                  f"P2: {'CONFIRMED' if meta['p2_falls'] else 'NULL (n/a if P1 null)'}")
            print(f"  span-count subscore:    {[round(x, 4) for x in count_series]}  "
                  f"P3: {'CONFIRMED' if meta['p3_rises'] else 'NULL'}")
            print(f"  weighted arrangement:   {[round(x, 4) for x in weighted_series]}  "
                  f"P4: {'HOLDS' if meta['p4_weighted_ge_unweighted'] else 'VIOLATED'}")
            print(f"  engagement totals: preferred_renders={meta['total_preferred_renders']}  "
                  f"tolerant_joins={meta['total_tolerant_joins']}")

    # ALWAYS persist the graph, regardless of which phase(s) ran or completed this invocation --
    # mark_characters/babble_characters both mutate `s` (minting, weight updates) even when a
    # phase does not finish within this call's budget; saving only at `finalize` would silently
    # discard those mutations while `meta`'s own done-ids still claimed them recorded (a real
    # bug caught before this ever ran against real data -- graph state and `meta` bookkeeping
    # must advance together, every single invocation).
    run29._save_graph(s, graph_path)

    if not progressed:
        print("  WALL: no progress made this invocation (unexpected phase state) -- inspect "
              f"meta at {meta_path}.")
        _save_json(meta, meta_path)
        return 1

    _save_json(meta, meta_path)
    print(f"  saved -> {graph_path}, {meta_path}")
    print(f"  phase now: cycle={meta['cycle']}/{N_CYCLES}  phase={meta['phase']}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    if meta["cycle"] >= N_CYCLES:
        print(f"\n  arm {arm} CONSUME COMPLETE.")
    return 0


# ---------------------------------------------------------------------------------------------
# STAGE: report -- combine all three arms against the run-30 CONTROL (reused verbatim).
# ---------------------------------------------------------------------------------------------
def stage_report():
    print(f"\n{SEP}\n  RUN 31 -- GEOMETRY -- FINAL REPORT\n{SEP}")
    print(f"\n  CONTROL (run 30 consume arm, reused verbatim, NOT re-run):")
    print(f"    unweighted arrangement: {[round(x, 4) for x in CONTROL_UNWEIGHTED_SERIES]}  (flat)")
    print(f"    surviving_residual:     {CONTROL_SURVIVING_SERIES}  (flat)")

    any_p1 = False
    all_p1_null = True
    summary = {}
    for arm in ARMS:
        meta_path = _arm_meta_path(arm)
        if not os.path.exists(meta_path):
            print(f"\n  ARM {arm}: not started.")
            continue
        meta = _load_json(meta_path)
        if meta.get("cycle", 0) < N_CYCLES:
            print(f"\n  ARM {arm}: IN PROGRESS ({meta.get('cycle', 0)}/{N_CYCLES} cycles, "
                  f"phase={meta.get('phase')}) -- re-invoke --stage consume --arm {arm} to advance.")
            continue
        print(f"\n  ARM {arm}:")
        print(f"    unweighted arrangement: {[round(x, 4) for x in meta['unweighted_series']]}  "
              f"P1: {'CONFIRMED' if meta['p1_rises'] else 'NULL'}")
        print(f"    surviving_residual:     {meta['surviving_series']}  "
              f"P2: {'CONFIRMED' if meta['p2_falls'] else 'NULL'}")
        print(f"    span-count subscore:    {[round(x, 4) for x in meta['count_series']]}  "
              f"P3: {'CONFIRMED' if meta['p3_rises'] else 'NULL'}")
        print(f"    weighted arrangement:   {[round(x, 4) for x in meta['weighted_series']]}  "
              f"P4: {'HOLDS' if meta['p4_weighted_ge_unweighted'] else 'VIOLATED'}")
        print(f"    engagement: preferred_renders={meta['total_preferred_renders']}  "
              f"tolerant_joins={meta['total_tolerant_joins']}")
        summary[arm] = meta
        any_p1 = any_p1 or meta["p1_rises"]
        all_p1_null = all_p1_null and (not meta["p1_rises"])

    if len(summary) < len(ARMS):
        print(f"\n  WALL: not every arm has completed 3 cycles -- re-invoke the missing "
              f"--stage consume --arm <name> calls before drawing a final verdict.")
        _save_json(dict(partial=True, summary=summary), _ckpt("report.json"))
        return 1

    print(f"\n{SEP}\n  VERDICT\n{SEP}")
    if all_p1_null:
        print("  ALL THREE ARMS NULL ON P1 -- the geometry residual is not reachable from the "
              "render side at this featureset. This is the finding, reported and stopped.")
    else:
        winners = [a for a, m in summary.items() if m["p1_rises"]]
        print(f"  P1 CONFIRMED in: {winners}. Eval stage gated on this -- NOT run in this "
              f"script; a follow-up eval pass (n=400, standard protocol) is the next step for "
              f"{winners}.")
    print(f"  NOTE: engagement counts above are the mechanism-VACUOUS check -- an arm with 0 "
          f"engagement and a null P1 is uninformative about the mechanism, not evidence against "
          f"it (the run-28 lesson).")

    _save_json(dict(partial=False, summary=summary, all_p1_null=all_p1_null), _ckpt("report.json"))
    print(f"\n  saved -> {_ckpt('report.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# MAIN
# ===============================================================================================
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["verify", "consume", "report"])
    p.add_argument("--arm", choices=sorted(ARMS), default=None)
    args = p.parse_args()
    t0 = time.time()
    if args.stage == "verify":
        rc = stage_verify()
    elif args.stage == "consume":
        if not args.arm:
            print("  WALL: --stage consume requires --arm {a_only,b_only,a_plus_b}")
            rc = 1
        else:
            rc = stage_consume(args.arm)
    elif args.stage == "report":
        rc = stage_report()
    else:
        rc = 1
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
