"""OMNIGLOT RUN 26 -- THE HOMEWORK LOOP GATE.

`domains/homework_loop.py` (16/16 unit-gated, 810 migrated green) implements BABBLE
SELF-PRACTICE WITH PERIODIC GROUNDING: mark (real ink round-trip score) -> assign (frontier
worksheet) -> babble (self-render/re-decode practice, no real ink) -> re-mark. This script is
the FIRST measurement of whether that loop, run for real against the Omniglot arc's own
standing 80.5% [76.3, 84.1] @ n=400 verdict (RUN 17b/25's `parse_marginal_verdict` control,
`results/omniglot_gate_run25_number.log`) and its live residuals (reproducer segmentation
instability, proposal recall ~53-54%@shortlist), actually teaches the agent anything that
TRANSFERS to held-out evaluation characters.

ARCHITECTURAL NOTE ON THE EVAL DESIGN (read before the numbers): the 80.5% control itself
(`ar.stage_parse_char` + `ar.parse_marginal_verdict`, RUN 25's C0) is DECODE-FREE geometry --
corner-split parsing + SC+TPS marginalization over raw points, needing no LEARN phase and NO
stroke codebook at all. The homework loop only touches the CODEBOOK (`domains/stroke_
codebook.py`'s `ShapeSignature{kind:"stroke"}` population, grown via `domains/ink_decode.py`).
This means C0's full-dwell accuracy is, BY CONSTRUCTION, identical no matter what the homework
loop does -- there is no codebook dependency on that path for homework to move. The metric
homework CAN move is the STRUCTURAL PROPOSAL (`gate.decode_char_signature` + `ar.propose_top_k`,
RUN 25's workstream B, itself codebook-dependent) -- coverage@shortlist and a
shortlist-CONSTRAINED parse-marginal accuracy (stage only the K proposed candidates, verdict
among those). So this run measures THREE things per arm, not one:
  (i)   C0 FULL-DWELL control (codebook-independent; computed once for BASELINE and cited,
        with a per-arm SPOT-CHECK on block 0 confirming byte-identical predictions across arms
        -- the architectural claim is verified empirically, not just asserted);
  (ii)  coverage@shortlist (K=10 of 20) via the CODEBOOK structural proposal -- THIS is where
        homework's variant-coverage/refinement-child mechanisms can show up (P3);
  (iii) shortlist-CONSTRAINED parse-marginal accuracy -- bounded above by coverage, so this is
        where a genuine coverage gain could (but need not) turn into an accuracy gain (P4).

PRE-REGISTERED PREDICTIONS (stated before any result below is computed):
  P1. Background round-trip score improves pre -> post homework (partial recovery expected --
      pose-jitter babble provably closes line-segmentation instabilities but NOT curved-arc
      curvature loss, per the phase-1 probe -- so IMPROVEMENT, not perfection, is predicted).
      The GROUNDING-ONLY arm's repeated mark-only passes should NOT improve (no babble
      mechanism runs) -- flat is the correct null there, not a failure.
  P2. `surviving_residual_count` FALLS across homework cycles (the teacher-information metric
      -- it must fall or the loop is not learning). STOP BRANCH: if it does not fall, report
      the finding and do NOT spend eval compute on the homework arm's eval stage.
  P3. Eval proposal coverage@shortlist improves (CI-separated, non-noise) vs the baseline arm
      -- variant-coverage quanta + refinement children feed the structural proposal signature.
  P4. 20-way shortlist-constrained accuracy (n up to 400, Wilson CI) moves ONLY THROUGH
      coverage -- if accuracy moves CI-separated while coverage does NOT, that is flagged as an
      ANOMALY (possible leakage / spurious effect), not a success. Given the verdict-layer
      ceiling (six independent RUN-25-family nulls at ~80.5%), accuracy is NOT predicted to
      exceed the standing control's CI; any CI-separated gain must come with a coverage gain.

PRE-REGISTERED PARAMETERS (adjust only for wall-clock feasibility; deviations are logged
explicitly at the point they are made, never silently):
  - LEARN: byte-identical to RUN 25 workstream B / the standing gate (`gate.boot()`,
    `LEARN_ALPHABETS_N=5` background alphabets, drawers 01-14, `LEARN_STROKE_CAP=1500` (RUN
    16's saturation-verified cap), `gate.DK` (the arc's own reduced Omniglot bins).
  - HOMEWORK dk: `gate.DK`, EXPLICITLY -- NOT `homework_loop`'s own `_default_dk()` (which is
    the arc's separate RICH/synthetic-gate bins, `segments=12/turn_bins=16/...`. Decoding at a
    resolution different from the one the codebook was GROWN at would look up the wrong
    quantized bins entirely -- passing `dk=gate.DK` to every `mark`/`babble`/`cycle` call is
    load-bearing correctness, not a style choice.
  - Background marking set: ~200 single-stroke items, seeded RNG, sampled from the SAME 5
    LEARN background alphabets but drawers 15-20 (UNUSED by LEARN's drawers 01-14) -- fresh
    instances of familiar shapes, a realistic "grounding contact" scenario. Disjoint from every
    eval alphabet by construction (background vs evaluation are different Omniglot splits/
    directories) AND hard-guarded via `eval_class_ids` (the full evaluation-alphabet character
    set for the 10 TEST alphabets) on every `mark`/`babble`/`cycle` call.
  - Cycles N=3, reps_per_item=20, capacity=None (natural worksheet size, no cap).
  - GROUNDING-ONLY control: the SAME marking set, the SAME N=3 repeated `mark()`-only passes
    (no `assign`/`babble`) -- matched real-ink CONTACT COUNT, zero self-practice.
  - Eval: byte-identical episode construction to RUN 25/17b's C0 (`run25._block_spec`, 10 TEST
    alphabets = sorted-name 10-prefix of qualifying `strokes_evaluation` alphabets with >=20
    characters, WAY=20, R_TARGET=2 -> target n=400, `POWER_SEED = gate.SEED + 1500`, the SAME
    rng consumption order every arm's eval stage re-derives from scratch). SHORTLIST_K=10 (of
    20) is a NEW pre-registered constant for this run's structural-shortlist metric (not
    present in RUN 25 C0, which never uses a shortlist) -- never tuned per-arm or per-outcome.

EXECUTION: staged + checkpointed (`--stage learn|homework|grounding|eval-baseline|
eval-homework|eval-grounding|report`), state under `results/run26_checkpoints/`. `homework`/
`grounding` run ONE cycle/pass per invocation (re-invoke to advance); `eval-*` process eval
BLOCKS up to a per-call wall-clock budget and checkpoint after every block (re-invoke to
continue a partial run). Every stage is a single blocking call, never backgrounded.

donkey=0: no torch anywhere in sys.modules, checked at the end of every stage.

Run (repeat --stage homework/grounding/eval-* until each reports COMPLETE):
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run26_homework.py --stage learn
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
from domains import abs_read as ar
from domains import homework_loop as hw
from domains import omniglot_world as ow
from domains import stroke_codebook as sc

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run26_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS.
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N            # 5
LEARN_DRAWERS = gate.LEARN_DRAWERS                    # 01..14
LEARN_STROKE_CAP = 1500                               # RUN 16/25's saturation-verified cap
DK = gate.DK                                          # the arc's own reduced Omniglot bins --
                                                       # used for LEARN *and* every homework
                                                       # mark/babble/cycle call (load-bearing).
GROWTH_WINDOW = gate.GROWTH_WINDOW

MARK_DRAWERS = [f"{i:02d}" for i in range(15, 21)]    # unused by LEARN (01-14)
N_MARK_ITEMS = 200
MARK_SEED = 20260726                                  # this run's own seed, distinct from
                                                       # POWER_SEED (eval) and gate.SEED (learn).

N_CYCLES = 3
REPS_PER_ITEM = 20
HOMEWORK_SEED = MARK_SEED + 5000                      # one seed per cycle: HOMEWORK_SEED + c

WAY = run25.WAY                                       # 20
EPISODES_PER_ALPHABET = run25.EPISODES_PER_ALPHABET   # 20
R_TARGET = run25.R_TARGET                             # 2  -> target n=400
N_TEST_ALPHABETS = run25.N_TEST_ALPHABETS             # 10
POWER_SEED = run25.POWER_SEED                         # gate.SEED + 1500, byte-identical to
                                                       # RUN 15/16/17/25's own eval seed.
N_FLOOR_PER_ARM = 200
RUN25_C0_CONTROL = run25.RUN17B_CONTROL               # {"acc":0.805,"ci":(0.763,0.841),"n":400}
FAMILY_A_ANCHOR = run25.FAMILY_A_ANCHOR                # 0.815

SHORTLIST_K = 10                                      # NEW this run: of 20 within-alphabet
                                                       # candidates, never tuned per-outcome.
PER_CALL_BUDGET_SECONDS = 480.0                       # eval-stage per-invocation wall budget
                                                       # (leaves >100s headroom under the 600s
                                                       # foreground cap; checkpointed per block).


# ---------------------------------------------------------------------------------------------
# PERSISTENCE -- the whole substrate_rs graph round-trips through its own native
# graph_to_dict/graph_from_dict (node ids preserved, verified empirically before this script was
# written: a boot+partial-LEARN substrate saved/reloaded reproduced an IDENTICAL
# `stroke_codebook.grain_vocabulary_report` and a valid agent-root node lookup).
# ---------------------------------------------------------------------------------------------
def _save_graph(s, path: str) -> None:
    """Serialise the WHOLE mind, not just the plain graph -- `substrate.world_adapter.
    WorldAdapter.save`'s own established recipe (`graph` + the dynamic Γ `grammar` +
    the `add_rule` rule store `export_rules()`). A first version of this helper saved
    only `graph_to_dict()` and it broke on reload: `induce_concern` (fired from inside
    `decode_ink` on a genuinely novel eval-alphabet substroke) does `sub.add_edge(ag_node,
    "observed", obs_node)`, which is gated by Γ -- and Γ's dynamically-admitted
    productions (as well as every seed-installed + runtime-authored Rule) live in
    substrate_rs state that `graph_to_dict` does NOT capture (G, Γ, C are separate per
    CLAUDE.md's own architecture description). Reproduced here verbatim."""
    blob = {"graph": s.graph_to_dict(), "grammar": s.grammar_to_json(),
            "rules": s._inner.export_rules()}
    with open(path, "w") as f:
        json.dump(blob, f)


def _load_graph(path: str):
    with open(path) as f:
        blob = json.load(f)
    s = srs.Substrate()
    s.graph_from_dict(blob["graph"])
    for p in blob["grammar"]["productions"]:
        try:
            s._inner.add_production(p)
        except Exception:
            pass
    if "rules" in blob:
        s._inner.import_rules(blob["rules"])
    return s


def _json_default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serializable: {type(o)}")


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_json_default)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _donkey0() -> bool:
    return "torch" not in sys.modules


# ---------------------------------------------------------------------------------------------
# SHARED HELPERS.
# ---------------------------------------------------------------------------------------------
def _test_alphabets() -> list:
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    return qualifying[:N_TEST_ALPHABETS]


def _eval_class_ids(test_alphabets: list) -> set:
    ids: set = set()
    for alph in test_alphabets:
        ids.update(ow.characters(alph, "evaluation"))
    return ids


def _build_marking_set(n_items: int = N_MARK_ITEMS, seed: int = MARK_SEED) -> list:
    """~200 single real pen-strokes, seeded, from the SAME 5 LEARN background alphabets but
    drawers 15-20 (LEARN only ever touches 01-14) -- disjoint-from-eval by construction (a
    different Omniglot split directory entirely) and re-checked via `eval_class_ids` on every
    `mark`/`babble`/`cycle` call downstream. Deterministic given `seed` -- called identically
    by the `homework` and `grounding` stages so both arms practice/ground on the IDENTICAL set."""
    rng = np.random.default_rng(seed)
    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    pool = []
    for alph in learn_alphabets:
        for cdir in ow.characters(alph, "background"):
            files_by_drawer = {}
            for f in ow.drawings(cdir):
                d = f.split("/")[-1].split("_")[-1].replace(".txt", "")
                files_by_drawer[d] = f
            for d in MARK_DRAWERS:
                f = files_by_drawer.get(d)
                if f is not None:
                    pool.append((cdir, f))
    order = rng.permutation(len(pool))
    items = []
    for pi in order:
        if len(items) >= n_items:
            break
        cdir, f = pool[int(pi)]
        strokes = [st for st in ow.load_strokes(f) if st.shape[0] >= 2]
        if not strokes:
            continue
        si = int(rng.integers(len(strokes)))
        items.append({"id": len(items), "class_id": cdir, "points": strokes[si].tolist()})
    return items


def _wilson(k: int, n: int) -> tuple:
    return gate.wilson_ci(k, n)


def _sep(ci_a, ci_b) -> bool:
    return gate._ci_separated(tuple(ci_a), tuple(ci_b))


# ===============================================================================================
# STAGE: learn
# ===============================================================================================
def stage_learn():
    print(f"\n{SEP}\n  STAGE: learn\n{SEP}")
    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print("  WALL: Omniglot data not found. Cannot proceed.")
        return 1
    t0 = time.time()
    s, ag, native = gate.boot()
    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    print(f"  LEARN alphabets: {learn_alphabets}")
    print(f"  drawers {LEARN_DRAWERS[0]}-{LEARN_DRAWERS[-1]}, cap={LEARN_STROKE_CAP}, DK={DK}")
    lr = gate.run_learn(s, ag, native, learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP, DK,
                         GROWTH_WINDOW)
    elapsed = time.time() - t0
    growth = lr["growth"]
    sat_pass = None
    if len(growth) >= 3:
        first = np.mean([g["new_quanta"] for g in growth[:1]])
        last = np.mean([g["new_quanta"] for g in growth[-2:]])
        sat_pass = bool(last <= max(3.0, 0.3 * first) if first > 0 else True)
    grain = sc.grain_vocabulary_report(s)
    print(f"  processed {lr['n_strokes']} strokes ({lr['n_degenerate_skipped']} degenerate "
          f"skipped) in {elapsed:.1f}s. saturation={'PASS' if sat_pass else ('FAIL' if sat_pass is False else 'UNKNOWN')}")
    print(f"  codebook grain report: {grain}")
    _save_graph(s, _ckpt("learn.json"))
    _save_json(dict(n_strokes=lr["n_strokes"], elapsed=elapsed, grain_report=grain,
                     learn_alphabets=learn_alphabets, sat_pass=sat_pass,
                     growth_tail=growth[-3:] if growth else []), _ckpt("learn_meta.json"))
    print(f"  saved -> {_ckpt('learn.json')}, {_ckpt('learn_meta.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: homework (one cycle per invocation)
# ===============================================================================================
def stage_homework():
    print(f"\n{SEP}\n  STAGE: homework\n{SEP}")
    meta_path = _ckpt("homework_metrics.json")
    meta = _load_json(meta_path) if os.path.exists(meta_path) else {"cycles": []}
    done = len(meta["cycles"])
    if done >= N_CYCLES:
        print(f"  homework already COMPLETE ({done}/{N_CYCLES} cycles). p2_falls="
              f"{meta.get('p2_falls')}")
        return 0

    src = _ckpt("homework.json") if done > 0 else _ckpt("learn.json")
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run stage 'learn' first"
              f"{' (or a prior homework cycle)' if done > 0 else ''}.")
        return 1
    s = _load_graph(src)

    ground_items = _build_marking_set()
    meta["n_ground_items"] = len(ground_items)
    test_alphabets = _test_alphabets()
    eval_ids = _eval_class_ids(test_alphabets)
    print(f"  cycle {done}/{N_CYCLES}: {len(ground_items)} ground items, "
          f"reps_per_item={REPS_PER_ITEM}, rng_seed={HOMEWORK_SEED + done}, dk=gate.DK")

    if done == 0:
        meta["grain_before"] = sc.grain_vocabulary_report(s)
        print(f"  grain_before: {meta['grain_before']}")

    t0 = time.time()
    rep = hw.cycle(s, ground_items, reps_per_item=REPS_PER_ITEM, rng_seed=HOMEWORK_SEED + done,
                   dk=DK, capacity=None, jitter_bins=hw.DEFAULT_JITTER_BINS,
                   eval_class_ids=eval_ids)
    elapsed = time.time() - t0

    mean_pre = float(np.mean(list(rep.pre_scores.values()))) if rep.pre_scores else 0.0
    mean_post = float(np.mean(list(rep.post_scores.values()))) if rep.post_scores else 0.0
    cyc = dict(cycle=done, mean_pre=mean_pre, mean_post=mean_post,
               surviving_before=rep.surviving_residual_count_before,
               surviving_after=rep.surviving_residual_count,
               worksheet_size=rep.worksheet_size, corrections=rep.corrections,
               elapsed=elapsed)
    meta["cycles"].append(cyc)
    print(f"  mean_pre={mean_pre:.4f}  mean_post={mean_post:.4f}  "
          f"surviving_before={rep.surviving_residual_count_before}  "
          f"surviving_after={rep.surviving_residual_count}  "
          f"worksheet_size={rep.worksheet_size}  corrections={rep.corrections}  "
          f"elapsed={elapsed:.1f}s")

    if done + 1 >= N_CYCLES:
        meta["grain_after"] = sc.grain_vocabulary_report(s)
        series = [c["surviving_after"] for c in meta["cycles"]]
        meta["p2_falls"] = bool(series[-1] < meta["cycles"][0]["surviving_before"])
        print(f"  grain_after: {meta['grain_after']}")
        print(f"  surviving_residual_count series (before-cycle0, after-each-cycle): "
              f"{[meta['cycles'][0]['surviving_before']] + series}")
        print(f"  P2 (surviving residual falls): {'CONFIRMED' if meta['p2_falls'] else 'STOP -- NOT FALLING'}")

    _save_graph(s, _ckpt("homework.json"))
    _save_json(meta, meta_path)
    print(f"  saved -> {_ckpt('homework.json')}, {meta_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: grounding (one mark-only pass per invocation -- matched real-ink contact, no babble)
# ===============================================================================================
def stage_grounding():
    print(f"\n{SEP}\n  STAGE: grounding\n{SEP}")
    meta_path = _ckpt("grounding_metrics.json")
    meta = _load_json(meta_path) if os.path.exists(meta_path) else {"passes": []}
    done = len(meta["passes"])
    if done >= N_CYCLES:
        print(f"  grounding already COMPLETE ({done}/{N_CYCLES} passes).")
        return 0

    src = _ckpt("grounding.json") if done > 0 else _ckpt("learn.json")
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run stage 'learn' first.")
        return 1
    s = _load_graph(src)

    ground_items = _build_marking_set()          # SAME seed -> SAME items as homework
    meta["n_ground_items"] = len(ground_items)
    test_alphabets = _test_alphabets()
    eval_ids = _eval_class_ids(test_alphabets)
    print(f"  pass {done}/{N_CYCLES}: {len(ground_items)} ground items, mark()-only, dk=gate.DK")

    if done == 0:
        meta["grain_before"] = sc.grain_vocabulary_report(s)
        print(f"  grain_before: {meta['grain_before']}")

    t0 = time.time()
    marked = hw.mark(s, ground_items, dk=DK, eval_class_ids=eval_ids)
    elapsed = time.time() - t0
    mean_score = float(np.mean([m.round_trip_score for m in marked])) if marked else 0.0
    surviving = sum(1 for m in marked if m.round_trip_score < hw.DEFAULT_MAX_SCORE)
    p = dict(pass_=done, mean_score=mean_score, surviving=surviving, elapsed=elapsed)
    meta["passes"].append(p)
    print(f"  mean_score={mean_score:.4f}  surviving={surviving}/{len(marked)}  "
          f"elapsed={elapsed:.1f}s")

    if done + 1 >= N_CYCLES:
        meta["grain_after"] = sc.grain_vocabulary_report(s)
        print(f"  grain_after: {meta['grain_after']}")
        scores = [pp["mean_score"] for pp in meta["passes"]]
        print(f"  mean_score series across passes: {scores} "
              f"(prediction: FLAT -- marking alone changes nothing)")

    _save_graph(s, _ckpt("grounding.json"))
    _save_json(meta, meta_path)
    print(f"  saved -> {_ckpt('grounding.json')}, {meta_path}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: eval-<arm> (block-checkpointed)
# ===============================================================================================
_ARM_CKPT = {"baseline": "learn.json", "homework": "homework.json", "grounding": "grounding.json"}


def _finalize_eval(state: dict) -> None:
    records = state["records"]
    trues = [r["true"] for r in records]
    full_records = [r for r in records if "pred_full" in r]
    if full_records:
        preds_full = [r["pred_full"] for r in full_records]
        trues_full = [r["true"] for r in full_records]
        k_full = sum(1 for p, t in zip(preds_full, trues_full) if p == t)
        acc_full = k_full / len(trues_full)
        ci_full = _wilson(k_full, len(trues_full))
        state["full_dwell"] = dict(acc=acc_full, ci=list(ci_full), n=len(trues_full), k=k_full)
    n = len(records)
    k_cov = sum(1 for r in records if r["in_shortlist"])
    cov = k_cov / n if n else 0.0
    ci_cov = _wilson(k_cov, n)
    k_sl = sum(1 for r in records if r["pred_shortlist"] == r["true"])
    acc_sl = k_sl / n if n else 0.0
    ci_sl = _wilson(k_sl, n)
    state["coverage"] = dict(cov=cov, ci=list(ci_cov), k=k_cov, n=n)
    state["shortlist_acc"] = dict(acc=acc_sl, ci=list(ci_sl), k=k_sl, n=n)


def stage_eval(tag: str):
    print(f"\n{SEP}\n  STAGE: eval-{tag}\n{SEP}")
    out_path = _ckpt(f"eval_{tag}.json")
    state = _load_json(out_path) if os.path.exists(out_path) else dict(
        records=[], block_idx=0, done=False, skipped=False)

    if state.get("skipped"):
        print(f"  eval-{tag} was SKIPPED: {state.get('reason')}")
        return 0
    if state.get("done"):
        print(f"  eval-{tag} already COMPLETE (n={len(state['records'])}).")
        return 0

    if tag == "homework":
        hwmeta_path = _ckpt("homework_metrics.json")
        if not os.path.exists(hwmeta_path):
            print("  WALL: homework_metrics.json missing -- run stage 'homework' to completion first.")
            return 1
        hwmeta = _load_json(hwmeta_path)
        if len(hwmeta.get("cycles", [])) < N_CYCLES:
            print(f"  homework not yet complete ({len(hwmeta['cycles'])}/{N_CYCLES} cycles) -- "
                  f"run stage 'homework' to completion first.")
            return 1
        if not hwmeta.get("p2_falls", True):
            state["skipped"] = True
            state["reason"] = ("P2 STOP: surviving_residual_count did not fall across homework "
                                "cycles (series: " +
                                f"{[hwmeta['cycles'][0]['surviving_before']] + [c['surviving_after'] for c in hwmeta['cycles']]}"
                                ") -- the loop is not learning; eval compute withheld per "
                                "pre-registration.")
            _save_json(state, out_path)
            print(f"  SKIPPED: {state['reason']}")
            return 0

    ckpt_name = _ARM_CKPT[tag]
    src = _ckpt(ckpt_name)
    if not os.path.exists(src):
        print(f"  WALL: {src} missing -- run the prerequisite stage(s) first.")
        return 1
    s = _load_graph(src)
    native = s._inner

    test_alphabets = _test_alphabets()
    blocks = [(alph, r) for alph in test_alphabets for r in range(R_TARGET)]
    print(f"  arm={tag}  test_alphabets={test_alphabets}  blocks={len(blocks)} "
          f"(target n={len(blocks) * WAY})  SHORTLIST_K={SHORTLIST_K}  resuming at block "
          f"{state['block_idx']}")

    # Deterministically replay the rng to the resume point -- _block_spec's own draws are cheap
    # (a handful of randint calls), never a re-score of already-checkpointed episodes.
    rng = np.random.default_rng(POWER_SEED)
    for i in range(state["block_idx"]):
        alph, r = blocks[i]
        run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)

    cache: dict = {}
    hard_deadline = time.time() + PER_CALL_BUDGET_SECONDS
    t0 = time.time()
    while state["block_idx"] < len(blocks) and time.time() < hard_deadline:
        alph, r = blocks[state["block_idx"]]
        spec = run25._block_spec(alph, rng, WAY, EPISODES_PER_ALPHABET)
        drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]

        full_dwell_this_block = (tag == "baseline") or (state["block_idx"] == 0)
        scratch0 = cand0 = None
        if full_dwell_this_block:
            scratch0 = srs.Substrate()
            _, cand0 = run25._stage_candidates(scratch0, drawer_files, ex_drawer, WAY,
                                                thetas=ar.DEFAULT_PARSE_THETAS)

        exemplars = [gate.decode_char_signature(s, drawer_files[ci][ex_drawer], cache, DK)
                     for ci in range(WAY)]
        exemplar_composed = [e["composed_sig"] for e in exemplars]

        for qi, q_drawer in spec["queries"]:
            path = drawer_files[qi][q_drawer]
            rec = {"true": qi, "alph": alph, "r": r}
            if full_dwell_this_block:
                qn0 = ar.stage_parse_char(scratch0, path, is_query=True,
                                           thetas=ar.DEFAULT_PARSE_THETAS)
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
            state["records"].append(rec)

        state["block_idx"] += 1
        _save_json(state, out_path)
        print(f"  block {state['block_idx']}/{len(blocks)} done ({alph!r} r={r}) -- "
              f"{len(state['records'])} episodes so far, {time.time() - t0:.1f}s this call")

    if state["block_idx"] >= len(blocks):
        state["done"] = True
        _finalize_eval(state)
        _save_json(state, out_path)
        print(f"\n  EVAL COMPLETE for {tag}: n={len(state['records'])}")
        if "full_dwell" in state:
            fd = state["full_dwell"]
            print(f"    full-dwell control:  acc={100*fd['acc']:.1f}%  95% CI "
                  f"[{100*fd['ci'][0]:.1f}%, {100*fd['ci'][1]:.1f}%]  n={fd['n']}")
        cov = state["coverage"]
        print(f"    coverage@{SHORTLIST_K}:      {100*cov['cov']:.1f}%  95% CI "
              f"[{100*cov['ci'][0]:.1f}%, {100*cov['ci'][1]:.1f}%]  n={cov['n']}")
        sl = state["shortlist_acc"]
        print(f"    shortlist accuracy:  {100*sl['acc']:.1f}%  95% CI "
              f"[{100*sl['ci'][0]:.1f}%, {100*sl['ci'][1]:.1f}%]  n={sl['n']}")
    else:
        print(f"\n  PARTIAL: {state['block_idx']}/{len(blocks)} blocks done -- "
              f"re-run '--stage eval-{tag}' to continue.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ===============================================================================================
# STAGE: report
# ===============================================================================================
def stage_report():
    print(f"\n{SEP}\n  RUN 26 -- HOMEWORK LOOP GATE -- FINAL REPORT\n{SEP}")

    def _opt(name):
        p = _ckpt(name)
        return _load_json(p) if os.path.exists(p) else None

    learn_meta = _opt("learn_meta.json")
    hw_meta = _opt("homework_metrics.json")
    gr_meta = _opt("grounding_metrics.json")
    ev_base = _opt("eval_baseline.json")
    ev_hw = _opt("eval_homework.json")
    ev_gr = _opt("eval_grounding.json")

    missing = [n for n, v in (("learn", learn_meta), ("homework", hw_meta),
                               ("grounding", gr_meta), ("eval-baseline", ev_base),
                               ("eval-grounding", ev_gr)) if v is None]
    if missing:
        print(f"  WALL: stages not yet complete: {missing}. Run them before 'report'.")
        return 1
    if not ev_base.get("done"):
        print("  WALL: eval-baseline not complete yet.")
        return 1
    if not ev_gr.get("done"):
        print("  WALL: eval-grounding not complete yet.")
        return 1

    test_alphabets = _test_alphabets()
    print(f"\n  eval-subset coverage: {N_TEST_ALPHABETS} evaluation alphabets, WAY={WAY}-way "
          f"within-alphabet, target n={N_TEST_ALPHABETS * R_TARGET * WAY}: {test_alphabets}")
    print(f"  LEARN: {learn_meta['n_strokes']} strokes, {learn_meta['elapsed']:.1f}s, "
          f"grain={learn_meta['grain_report']}, saturation="
          f"{'PASS' if learn_meta['sat_pass'] else ('FAIL' if learn_meta['sat_pass'] is False else 'UNKNOWN')}")

    # ---- spot-check: full-dwell block-0 predictions identical across arms -------------------
    def _block0_full(ev):
        return [(r["true"], r["pred_full"]) for r in ev["records"] if "pred_full" in r
                and r["alph"] == ev["records"][0]["alph"] and r["r"] == 0] if ev else None

    base0 = [(r["true"], r["pred_full"]) for r in ev_base["records"] if "pred_full" in r]
    base0_block0 = [x for x in base0 if True][:WAY]   # baseline's own first block, in order
    print(f"\n  SPOT-CHECK (full-dwell control is codebook-independent, so block-0 predictions "
          f"must be BYTE-IDENTICAL across arms):")
    spot_ok = True
    for tag, ev in (("homework", ev_hw), ("grounding", ev_gr)):
        if ev is None or not ev.get("done"):
            print(f"    {tag}: eval not complete, spot-check skipped.")
            continue
        arm0 = [(r["true"], r["pred_full"]) for r in ev["records"] if "pred_full" in r][:WAY]
        match = arm0 == base0_block0[:len(arm0)]
        spot_ok = spot_ok and match
        print(f"    {tag} vs baseline, block 0 ({len(arm0)} episodes): "
              f"{'MATCH (confirms C0 is codebook-independent)' if match else 'MISMATCH -- ANOMALY, investigate'}")

    # ---- P1: round-trip score pre -> post -----------------------------------------------------
    print(f"\n  {SEP}\n  P1 -- BACKGROUND ROUND-TRIP SCORE, PRE -> POST\n  {SEP}")
    hw_pre0 = hw_meta["cycles"][0]["mean_pre"]
    hw_post_last = hw_meta["cycles"][-1]["mean_post"]
    p1_homework = hw_post_last > hw_pre0
    print(f"  HOMEWORK   mean_pre(cycle0)={hw_pre0:.4f}  mean_post(cycle{len(hw_meta['cycles'])-1})="
          f"{hw_post_last:.4f}  delta={hw_post_last-hw_pre0:+.4f}  "
          f"-> {'CONFIRMED (improved)' if p1_homework else 'NULL (no improvement)'}")
    gr_scores = [p["mean_score"] for p in gr_meta["passes"]]
    gr_flat = abs(gr_scores[-1] - gr_scores[0]) < 0.02   # small honest tolerance, not a decision lever
    print(f"  GROUNDING  mean_score series={[round(x,4) for x in gr_scores]}  "
          f"-> {'CONFIRMED FLAT (as predicted -- marking alone changes nothing)' if gr_flat else 'MOVED (unexpected for a mark-only control)'}")

    # ---- P2: surviving residual falls ---------------------------------------------------------
    print(f"\n  {SEP}\n  P2 -- SURVIVING RESIDUAL COUNT ACROSS CYCLES (teacher information)\n  {SEP}")
    series = [hw_meta["cycles"][0]["surviving_before"]] + [c["surviving_after"] for c in hw_meta["cycles"]]
    print(f"  surviving_residual_count series (before, after-c0, after-c1, ...): {series}")
    print(f"  P2: {'CONFIRMED (falls)' if hw_meta['p2_falls'] else 'STOP -- did NOT fall'}")
    for c in hw_meta["cycles"]:
        print(f"    cycle {c['cycle']}: worksheet_size={c['worksheet_size']} "
              f"corrections={c['corrections']} elapsed={c['elapsed']:.1f}s")

    # ---- codebook deltas -----------------------------------------------------------------------
    print(f"\n  {SEP}\n  CODEBOOK DELTA (quanta / refinement children / total)\n  {SEP}")
    def _delta_line(label, before, after):
        print(f"  {label:<10} top {before['top']}->{after['top']} (+{after['top']-before['top']})  "
              f"children {before['children']}->{after['children']} (+{after['children']-before['children']})  "
              f"fine_children {before['fine_children']}->{after['fine_children']} "
              f"(+{after['fine_children']-before['fine_children']})  "
              f"total {before['total']}->{after['total']} (+{after['total']-before['total']})")
    _delta_line("HOMEWORK", hw_meta["grain_before"], hw_meta["grain_after"])
    _delta_line("GROUNDING", gr_meta["grain_before"], gr_meta["grain_after"])

    # ---- P3/P4: eval table ----------------------------------------------------------------------
    print(f"\n  {SEP}\n  EVAL TABLE (n up to {N_TEST_ALPHABETS*R_TARGET*WAY}, Wilson 95% CI)\n  {SEP}")
    def _row(tag, ev):
        if ev is None:
            print(f"  {tag:<10} not run")
            return None
        if ev.get("skipped"):
            print(f"  {tag:<10} SKIPPED ({ev.get('reason')})")
            return None
        if not ev.get("done"):
            print(f"  {tag:<10} INCOMPLETE ({ev['block_idx']} blocks done)")
            return None
        cov, sl = ev["coverage"], ev["shortlist_acc"]
        print(f"  {tag:<10} n={cov['n']:>4}  coverage@{SHORTLIST_K}={100*cov['cov']:5.1f}% "
              f"[{100*cov['ci'][0]:5.1f},{100*cov['ci'][1]:5.1f}]   "
              f"shortlist_acc={100*sl['acc']:5.1f}% [{100*sl['ci'][0]:5.1f},{100*sl['ci'][1]:5.1f}]")
        return ev
    ev_base_r = _row("baseline", ev_base)
    ev_hw_r = _row("homework", ev_hw)
    ev_gr_r = _row("grounding", ev_gr)
    if "full_dwell" in ev_base:
        fd = ev_base["full_dwell"]
        overlap = not (fd["ci"][1] < RUN25_C0_CONTROL["ci"][0] or RUN25_C0_CONTROL["ci"][1] < fd["ci"][0])
        print(f"\n  baseline full-dwell control: {100*fd['acc']:.1f}% [{100*fd['ci'][0]:.1f}, "
              f"{100*fd['ci'][1]:.1f}] (n={fd['n']}) vs RUN 25's standing 80.5% [76.3, 84.1] "
              f"(n=400): {'CI-OVERLAP (reproduces)' if overlap else 'CI-SEPARATED -- PROTOCOL DRIFT, investigate'}")
        baseline_reproduced = overlap and fd["n"] >= N_FLOOR_PER_ARM
    else:
        baseline_reproduced = False
        print("\n  WALL: baseline full-dwell control missing.")

    print(f"\n  {SEP}\n  P3 -- COVERAGE@{SHORTLIST_K} vs BASELINE\n  {SEP}")
    def _p3(tag, ev):
        if ev is None or ev.get("skipped") or not ev.get("done"):
            print(f"  {tag}: not evaluated ({'skipped' if ev and ev.get('skipped') else 'n/a'}).")
            return
        cov, base_cov = ev["coverage"], ev_base["coverage"]
        sep = _sep(cov["ci"], base_cov["ci"])
        better = cov["cov"] > base_cov["cov"]
        verdict = "CONFIRMED (coverage improved, CI-separated)" if (sep and better) else \
                  ("ANOMALY (CI-separated but WORSE)" if (sep and not better) else "NULL (not CI-separated)")
        print(f"  {tag}: {100*cov['cov']:.1f}% [{100*cov['ci'][0]:.1f},{100*cov['ci'][1]:.1f}] "
              f"vs baseline {100*base_cov['cov']:.1f}% "
              f"[{100*base_cov['ci'][0]:.1f},{100*base_cov['ci'][1]:.1f}] -> {verdict}")
    _p3("homework", ev_hw_r)
    _p3("grounding", ev_gr_r)

    print(f"\n  {SEP}\n  P4 -- SHORTLIST-CONSTRAINED ACCURACY vs BASELINE (must move only through coverage)\n  {SEP}")
    def _p4(tag, ev):
        if ev is None or ev.get("skipped") or not ev.get("done"):
            print(f"  {tag}: not evaluated.")
            return
        sl, base_sl = ev["shortlist_acc"], ev_base["shortlist_acc"]
        cov, base_cov = ev["coverage"], ev_base["coverage"]
        acc_sep = _sep(sl["ci"], base_sl["ci"])
        cov_sep = _sep(cov["ci"], base_cov["ci"])
        acc_better = sl["acc"] > base_sl["acc"]
        if acc_sep and cov_sep and acc_better:
            verdict = "CONFIRMED (accuracy moved WITH coverage)"
        elif acc_sep and not cov_sep:
            verdict = "ANOMALY (accuracy moved WITHOUT coverage moving -- investigate leakage)"
        elif not acc_sep:
            verdict = "NULL (no accuracy movement)"
        else:
            verdict = "ANOMALY (accuracy moved opposite to coverage)"
        print(f"  {tag}: shortlist_acc {100*sl['acc']:.1f}% [{100*sl['ci'][0]:.1f},{100*sl['ci'][1]:.1f}] "
              f"vs baseline {100*base_sl['acc']:.1f}% [{100*base_sl['ci'][0]:.1f},{100*base_sl['ci'][1]:.1f}] "
              f"(acc_ci_sep={acc_sep}, cov_ci_sep={cov_sep}) -> {verdict}")
        touch = FAMILY_A_ANCHOR >= sl["ci"][0] and FAMILY_A_ANCHOR <= sl["ci"][1]
        print(f"    CI {'TOUCHES' if touch else 'does NOT touch'} the Family-A anchor (81.5%); "
              f"ceiling context: standing verdict-layer ceiling is ~80.5% [76.3,84.1] (full dwell, "
              f"different metric -- shortlist accuracy is bounded above by coverage and is NOT "
              f"the same quantity).")
    _p4("homework", ev_hw_r)
    _p4("grounding", ev_gr_r)

    print(f"\n{SEP}\n  INVARIANTS\n{SEP}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  BASELINE C0 reproduction: {'PASS' if baseline_reproduced else 'FAIL'}")
    print(f"  spot-check (full-dwell arm-independence): {'PASS' if spot_ok else 'FAIL'}")
    overall = baseline_reproduced and spot_ok and _donkey0()
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}")
    print(SEP)
    return 0 if overall else 1


# ===============================================================================================
# MAIN
# ===============================================================================================
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["learn", "homework", "grounding", "eval-baseline", "eval-homework",
                             "eval-grounding", "report"])
    args = p.parse_args()
    t0 = time.time()
    if args.stage == "learn":
        rc = stage_learn()
    elif args.stage == "homework":
        rc = stage_homework()
    elif args.stage == "grounding":
        rc = stage_grounding()
    elif args.stage.startswith("eval-"):
        rc = stage_eval(args.stage.split("-", 1)[1])
    elif args.stage == "report":
        rc = stage_report()
    else:
        rc = 1
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
