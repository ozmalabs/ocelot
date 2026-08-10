"""OMNIGLOT RUN 52 -- THE MINIMAL LOOP-FLIP: VARIATION-AWARE COMPOSITION.

WHY THIS IS NOT ANOTHER BOLT-ON (runs 45/49/51 all nulled as bolt-ons -- see those commits):
the concept-evidence run 50 proved real and orthogonal (`domains/relational_variation.py`'s
background-learned per-slot TIGHTNESS weights, corr(r,geo)=0.093) cannot be ADDED/gated/
conditioned onto the geometry verdict after the fact (run 51, definitively -- 13/14 geo-correct
broken, 0/7 geo-wrong fixed, STOP at the free background-sanity gate). It must PARTICIPATE in a
verdict natively. THE MINIMAL LOOP-FLIP tested here: the COMPOSITION verdict (the character-
arrangement matcher, `domains/character_compose.py`'s composed `strokeq`/`rel`/`cpose_*`
signatures, the "bins propose" half of run 16's own "bins propose, continuous decides"
synthesis) currently scores every arrangement RELATION at an EQUAL, hardcoded weight of `1.0`
(`assignment_coverage_term`'s per-slot `_field_score(i, 1.0)` calls). Make that weight be run
50's own LEARNED per-slot TIGHTNESS -- a mismatch on a slot the background model found TIGHT
(identity-bearing, e.g. `rel_s`/`cpose_s` in this arc's own LEARN pool) costs more than an equal
mismatch on a LOOSE (free-to-vary, e.g. `rel_o`/`cpose_o`) slot. UNCONDITIONAL, native, no
margin gate (51's mis-firing condition is gone -- there is no "firing" here at all, EVERY
comparison uses the weighted metric), no additive-on-top-of-geo (51's dilution mechanism is
gone -- this never touches the geometry verdict; see the CORRECTION below).

CORRECTION TO THE LAUNCH BRIEF (this arc's own honesty law, stated up front, mirroring run 44's
own precedent of correcting its brief before any number is computed): the brief's own framing
implies the composition/arrangement score and the continuous SC+TPS geometry verdict
(`domains.abs_read.parse_marginal_pair_error`, the standing 80.5% GUARD every run 44-51 cites)
are ALREADY combined ("how composed signatures enter the verdict / parse_marginal"). Reading the
actual standing code (traced exhaustively before writing any of this run's own code) shows they
are NOT -- `parse_marginal_pair_error_term`'s call chain (`recognition_graph.
smoothdeform_error_term`/`marginal_part_error_term`/`shapecontext_error_term`) never imports or
calls `character_compose`/`assignment_coverage_term`/`_coverage_term` anywhere, and vice versa;
they are two parallel, never-fused pipelines (continuous point-set geometry vs. discrete
quantized-relation composition). `assignment_coverage_term` itself is ALSO not the ADOPTED
composition metric in the standing gate script (`scripts/jabberwock_omniglot_dynamic_
quantization.py`) -- the naive whole-tuple-membership `_coverage_term` is (33.8%, the "one-shot
composition" headline); `assignment_coverage_term` is a superseding-ATTEMPT diagnostic arm that
measured WORSE TWICE ("STRICTNESS IS THE SIGNAL", `abs_read.py`'s own module docstring, lines
10-14) as a FINAL verdict, though it remains the natural per-slot-decomposable structure this
run's tightness weights need (the naive `_coverage_term`'s whole-4-tuple-or-nothing `In` check
has no per-slot hook to weight at all). THIS RUN THEREFORE TESTS THE MINIMAL LOOP-FLIP AT THE
LEVEL WHERE IT IS STRUCTURALLY MEANINGFUL: does tightness-weighting `assignment_coverage_term`
improve ITS OWN classification accuracy over its own equal-weight control, on the SAME
composition-only comparison, still never touching the geometry pipeline. This is honestly a
narrower conversion test than "does the 80.5% headline move" -- and is reported as exactly that,
not oversold. A WIN here still validates the loop-flip DIRECTION (a concept's variation model
CAN act as the compositional metric itself, natively, not bolted on) and licenses the next step
(wiring composition INTO the geometry verdict, or building a genuinely fused metric) even though
this run does not itself touch the 80.5% number.

THE BUILD (`domains/character_compose.py::assignment_coverage_term`, in place -- see that
function's own "RUN 52" docstring section): a new `weights: Optional[dict] = None` kwarg
replaces the FOUR hardcoded `1.0` pose-slot weights (`rel_x`/`rel_y`/`rel_o`/`rel_s`) and the
FOUR hardcoded `1.0` cpose weights (`cpose_x`/`cpose_y`/`cpose_o`/`cpose_s`) with
`weights.get(slot, 1.0)`. `weights=None` (every pre-existing call site) is BYTE-IDENTICAL to the
pre-RUN-52 function (verified: `tests/test_character_composition_migrated.py`'s full 94-test
suite, unmodified, stays green). The SAME `MaxOver`/`Sum`/`Plus`/`IfThenElse` Term shape --
no new stage, no new machinery, one constant replaced by DATA (run 50's own frozen
`results/run50_checkpoints/learn_relational.json`'s `weights`, READ-ONLY, never recomputed).

GATE (run-26-style protocol -- POWER_SEED-flavoured deterministic block/query construction,
`WAY=20`-way episodes, held `Argmax` decision, `Argmin`-free-of-Python-ranking discipline --
MULTI-STROKE FOCUS, run 50/51's own convention, since composition/arrangement relations are
structurally ABSENT on single-stroke glyphs): composition classification needs a WITHIN-ALPHABET
`WAY=20` pool of multi-stroke classes, which (per run 50's own measurement) only 4 of the 5 LEARN
background alphabets have (`Anglo-Saxon_Futhorc`, `Arcadian`, `Armenian`,
`Asomtavruli_(Georgian)`) -- reused verbatim via `scripts.jabberwock_omniglot_run50_relational`'s
own `_multi_stroke_classes`/`_episode_alphabets`/`_files_by_drawer` (READ-ONLY function reuse,
not duplicated). SANITY population: 1 block per episode-alphabet (n = WAY * 4 = 80 -- HONEST,
not forced to a round n=100: this run's own structural population is smaller than run 44b/51's
because composition classification needs a qualifying WITHIN-ALPHABET multi-stroke WAY-pool,
run 44b/51's continuous-geometry background population does not). EVAL population: 2 MORE blocks
per episode-alphabet, same continuing RNG stream (no block overlap with SANITY) -- n = WAY * 4 *
2 = 160, matching run 50's own gate0 population size exactly (same underlying data, a fresh
independent draw).

ARMS: GUARD = `assignment_coverage_term(..., identity_weight=0.0, weights=None)` (equal weight,
arrangement-only -- run 50's own scope precedent, isolating the comparison to exactly what the
tightness weights model); ARM W = the SAME call with `weights=`run 50's own frozen per-slot
tightness. Both arms score EVERY candidate (no shortlist, no margin gate, no conditional firing
-- "unconditional, native" per the launch brief) via the SAME held `Argmax` idiom.

BACKGROUND-SANITY STOP FIRST (standing rule since commit 465d57da, reused verbatim): armed (ARM
W) accuracy on the SANITY population must be >= GUARD accuracy - 3pp, checked BEFORE the EVAL
population is even touched by either arm's own stage -- HARD STOP, no eval spend, if it fails.

PRIMARY (if sanity passes): paired McNemar, ARM W vs GUARD, on the EVAL population. PRE-
REGISTERED STOP (never re-tuned against this eval): broken >= fixed -- even tightness-weighting
the composition metric NATIVELY does not convert; the loop-flip must go DEEPER than reweighting
an existing metric's constants (a fuller generative-concept build, where the concept predicts
the PARSE itself, not merely reweights a match/mismatch indicator).

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run52.log`, per-block checkpoints under `results/run52_checkpoints/`
(every OTHER `results/run*_checkpoints/` directory is READ-ONLY reference, never written here),
NEVER `run_in_background`. `.venv` python (needs `substrate_rs`). `OZMA_SEED_PERSIST_DISABLED=1`
set at import time (belt-and-suspenders on top of the durable commit-21aa6123 guard, run 50/51's
own precedent -- a decode call here must never persist to the real `seeds/stroke_shapes.json`).

Stages, in dependency order:
  unit_sanity  seed-guard (before) + `tests/test_varcomp_migrated.py` +
               `tests/test_character_composition_migrated.py` (regression: the `weights` kwarg
               addition must not have moved any pre-existing test) +
               `tests/test_relational_variation_migrated.py` (run 50's own suite, unaffected).
  sanity       THE HARD STOP -- GUARD vs ARM W accuracy on the SANITY population (n=80),
               before any EVAL population is touched.
  eval         GUARD vs ARM W on the EVAL population (n=160), re-invoke until COMPLETE.
  report       background-sanity FIRST, tight/loose weight structure, McNemar + accuracies/CIs,
               fixed/broken structure, the does-the-loop-flip-convert verdict, honest anomalies.

Run (from the gamma-substrate repo root):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run52_varcomp.py --stage <STAGE>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")   # belt-and-suspenders, run 50/51's own
                                                             # precedent, see docstring.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from scipy.stats import binomtest

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run50_relational as run50
from domains import character_compose as cc
from domains import relational_variation as rv

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run52_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")     # READ-ONLY reference.
RUN50_DIR = os.path.join(ROOT, "results", "run50_checkpoints")     # READ-ONLY reference.
LEARN_RELATIONAL_PATH_50 = os.path.join(RUN50_DIR, "learn_relational.json")
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
RUN52_SEED = gate.SEED + 11000            # this run's own seed, distinct from every prior run's
                                           # (run50: +9000, run51 reuses POWER_SEED=+1500).
DK = gate.DK                              # the SAME reduced bins the standing codebook was grown
                                           # at -- load-bearing, per run26/50's own note.
WAY = 20
N_BLOCKS_SANITY = 1                       # per episode-alphabet -- n = WAY * n_ep_alphs.
N_BLOCKS_EVAL = 2                         # per episode-alphabet, SAME continuing RNG stream --
                                           # n = WAY * n_ep_alphs * 2 (matches run50's own gate0).
EX_DRAWERS_POOL = run50.EX_DRAWERS_POOL   # drawers 15-20, OUTSIDE the variation model's own
                                           # 01-10 LEARN range -- independent instances.
SANITY_MARGIN = 0.03                      # HARD STOP: armed_acc must be >= baseline_acc - 3pp.
N_BOOT = 500


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


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


def _md5(path: str) -> str:
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _donkey0() -> bool:
    return "torch" not in sys.modules


def _wilson(k: int, n: int) -> tuple:
    return gate.wilson_ci(k, n)


def _mcnemar(correct_a: list, correct_b: list) -> dict:
    """`fixed`: a WRONG -> b RIGHT. `broken`: a RIGHT -> b WRONG."""
    fixed = sum(1 for a, b in zip(correct_a, correct_b) if (not a) and b)
    broken = sum(1 for a, b in zip(correct_a, correct_b) if a and (not b))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


# --------------------------------------------------------------------------------------------- #
# `_argmax_pairs_term` -- duplicated locally per this codebase's own established convention of a
# small, pure, call-site-local Term builder (see `domains/abs_read.py`'s own identical comment at
# its own copy) rather than a shared import across scripts/domains.
# --------------------------------------------------------------------------------------------- #
def _argmax_pairs_term(pairs: list) -> dict:
    return {"type": "Argmax", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


def _argmax_ci(native, pairs: list) -> int:
    w = native.evaluate(_argmax_pairs_term(pairs), {})
    return int(w[1]) if w is not None else -1


# ============================================================================================= #
# STAGE: unit_sanity
# ============================================================================================= #
def stage_unit_sanity() -> int:
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    ok_all = True
    md5_before = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 (BEFORE this run touches anything): {md5_before}")
    print(f"  OZMA_SEED_PERSIST_DISABLED={os.environ.get('OZMA_SEED_PERSIST_DISABLED')!r}")

    for test_file in ("tests/test_varcomp_migrated.py",
                       "tests/test_character_composition_migrated.py",
                       "tests/test_relational_variation_migrated.py"):
        print(f"\n  running {test_file} ...")
        proc = subprocess.run([sys.executable, "-m", "pytest", test_file, "-q"],
                               cwd=ROOT, env={**os.environ}, capture_output=True, text=True,
                               timeout=180)
        print(proc.stdout[-4000:])
        if proc.returncode != 0:
            print(proc.stderr[-4000:])
        ok = proc.returncode == 0
        print(f"      -> {'PASS' if ok else 'FAIL'}")
        ok_all &= ok

    if not os.path.exists(LEARN_RELATIONAL_PATH_50):
        print(f"\n  WALL: {LEARN_RELATIONAL_PATH_50} missing -- run 50's own learn_relational "
              f"checkpoint is required (READ-ONLY reuse, never recomputed here).")
        ok_all = False

    md5_after = _md5(STROKE_SHAPES_SEED)
    ok_seed = md5_after == md5_before
    print(f"\n  seeds/stroke_shapes.json md5 AFTER unit_sanity: {md5_after}  UNCHANGED={ok_seed}")
    ok_all &= ok_seed
    if not ok_seed:
        raise SystemExit("HARD STOP: seed write detected during --stage unit_sanity.")

    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}"
          f"\n{SEP}")
    _save_json({"ok_all": bool(ok_all), "stroke_shapes_md5_before": md5_before},
               _ckpt("unit_sanity.json"))
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    if not ok_all:
        raise SystemExit(1)
    return 0


def _require_unit_sanity() -> dict:
    p = _ckpt("unit_sanity.json")
    if not os.path.exists(p):
        raise SystemExit("WALL: run --stage unit_sanity first.")
    d = _load_json(p)
    if not d.get("ok_all"):
        raise SystemExit("WALL: unit_sanity did not pass.")
    return d


def _require_weights() -> dict:
    return _load_json(LEARN_RELATIONAL_PATH_50)["weights"]


# ============================================================================================= #
# SHARED -- the population (READ-ONLY reuse of run 50's own multi-stroke episode-alphabet
# machinery), and one block's own GUARD/ARM-W scoring.
# ============================================================================================= #
def _episode_population():
    """`{alph: way_classes}` for the 4 qualifying LEARN background alphabets (run 50's own
    `_episode_alphabets`, reused verbatim, not recomputed)."""
    learn_alphs = run50.ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    multi = run50._multi_stroke_classes(learn_alphs)
    ep_alphs = run50._episode_alphabets(multi)
    return {a: multi[a][:WAY] for a in ep_alphs}


def _run_one_block(s, native, way_classes: list, files_by_drawer: dict, rng, cache: dict,
                    weights: dict) -> "list | None":
    """One block (one exemplar drawer draw + WAY queries, run 50's own `stage_gate0` inner-loop
    shape, reused): returns a list of per-query records `{true, guard_pred, armw_pred,
    guard_correct, armw_correct}`, or `None` (an honest skip -- an alphabet lacking that drawer
    for some class, run 50's own precedent)."""
    ex_drawer = EX_DRAWERS_POOL[int(rng.integers(len(EX_DRAWERS_POOL)))]
    exemplar_files = [files_by_drawer[cdir].get(ex_drawer) for cdir in way_classes]
    if any(f is None for f in exemplar_files):
        return None
    exemplars = [gate.decode_char_signature(s, f, cache, DK) for f in exemplar_files]
    exemplar_sigs = [e["composed_sig"] for e in exemplars]

    records = []
    for true_idx in range(WAY):
        q_drawer = f"{int(rng.integers(20)) + 1:02d}"
        tries = 0
        while (q_drawer == ex_drawer or
               files_by_drawer[way_classes[true_idx]].get(q_drawer) is None):
            q_drawer = f"{int(rng.integers(20)) + 1:02d}"
            tries += 1
            if tries > 40:
                break
        q_file = files_by_drawer[way_classes[true_idx]].get(q_drawer)
        if q_file is None:
            continue
        qd = gate.decode_char_signature(s, q_file, cache, DK)
        q_sig = qd["composed_sig"]

        guard_pairs = [(float(native.evaluate(cc.assignment_coverage_term(
            q_sig, exemplar_sigs[ci], identity_weight=0.0), {}) or 0.0), ci)
            for ci in range(WAY)]
        armw_pairs = [(float(native.evaluate(cc.assignment_coverage_term(
            q_sig, exemplar_sigs[ci], identity_weight=0.0, weights=weights), {}) or 0.0), ci)
            for ci in range(WAY)]
        guard_pred = _argmax_ci(native, guard_pairs)
        armw_pred = _argmax_ci(native, armw_pairs)
        records.append(dict(true=true_idx, guard_pred=guard_pred, armw_pred=armw_pred,
                             guard_correct=bool(guard_pred == true_idx),
                             armw_correct=bool(armw_pred == true_idx)))
    return records


# ============================================================================================= #
# STAGE: sanity -- THE HARD STOP.
# ============================================================================================= #
SANITY_STATE_PATH = _ckpt("sanity_state.json")
SANITY_PATH = _ckpt("sanity.json")


def stage_sanity() -> int:
    print(f"\n{SEP}\n  STAGE: sanity (THE HARD STOP -- GUARD vs ARM W, SANITY population)"
          f"\n{SEP}")
    if os.path.exists(SANITY_PATH):
        frozen = _load_json(SANITY_PATH)
        print(f"  ALREADY FROZEN: {SANITY_PATH}")
        _print_sanity(frozen)
        return 0
    _require_unit_sanity()
    weights = _require_weights()
    print(f"  READ (read-only) run 50's own frozen per-slot weights: {weights}")

    md5_before = _md5(STROKE_SHAPES_SEED)
    population = _episode_population()
    ep_alphs = sorted(population)
    print(f"  episode-alphabets (>= {WAY} multi-stroke classes): {ep_alphs}")
    if not ep_alphs:
        raise SystemExit("WALL: no episode-alphabet qualifies.")

    state = _load_json(SANITY_STATE_PATH) if os.path.exists(SANITY_STATE_PATH) else dict(
        alph_idx=0, records=[])

    s = run50._load_codebook_substrate()
    native = s._inner
    cache: dict = {}
    rng = np.random.default_rng(RUN52_SEED)
    # Replay the RNG draws for every alphabet fully processed in a prior invocation, by actually
    # RE-RUNNING `_run_one_block` (discarding its output -- already in `state["records"]`) for
    # each one, so a resumed call's own draws continue the SAME deterministic stream (mirrors
    # run50/51's own resume-by-replay discipline; a no-op placeholder here would silently
    # DE-SYNC the RNG stream between the original run and a resumed one).
    for i in range(state["alph_idx"]):
        alph = ep_alphs[i]
        way_classes = population[alph]
        files_by_drawer = {cdir: run50._files_by_drawer(cdir) for cdir in way_classes}
        for _b in range(N_BLOCKS_SANITY):
            _run_one_block(s, native, way_classes, files_by_drawer, rng, cache, weights)

    hard_deadline = time.time() + 460.0
    t0 = time.time()
    # NOTE: resume granularity is per-ALPHABET (not per-block) -- re-running `_run_one_block`
    # for an alphabet already fully recorded would double-RECORD it (but is required to
    # correctly re-consume its RNG draws, see the replay loop above, whose own output is
    # discarded); only the alphabet INDEX is checkpointed, never re-appended to `state["records"]`.
    while state["alph_idx"] < len(ep_alphs) and time.time() < hard_deadline:
        alph = ep_alphs[state["alph_idx"]]
        way_classes = population[alph]
        files_by_drawer = {cdir: run50._files_by_drawer(cdir) for cdir in way_classes}
        for _b in range(N_BLOCKS_SANITY):
            recs = _run_one_block(s, native, way_classes, files_by_drawer, rng, cache, weights)
            if recs:
                state["records"].extend(recs)
        state["alph_idx"] += 1
        _save_json(state, SANITY_STATE_PATH)
        print(f"  alphabet {state['alph_idx']}/{len(ep_alphs)} ({alph!r}) done -- "
              f"{len(state['records'])} episodes so far, {time.time()-t0:.1f}s this call",
              flush=True)

    if state["alph_idx"] < len(ep_alphs):
        print(f"\n  PARTIAL: {state['alph_idx']}/{len(ep_alphs)} alphabets done -- re-invoke to "
              f"continue.")
        return 0

    records = state["records"]
    n = len(records)
    k_guard = sum(1 for r in records if r["guard_correct"])
    k_armw = sum(1 for r in records if r["armw_correct"])
    acc_guard, acc_armw = k_guard / n, k_armw / n
    passed = acc_armw >= acc_guard - SANITY_MARGIN
    frozen = dict(n=n, k_guard=k_guard, k_armw=k_armw, acc_guard=acc_guard, acc_armw=acc_armw,
                  sanity_margin=SANITY_MARGIN, passed=bool(passed), ep_alphs=ep_alphs)
    _save_json(frozen, SANITY_PATH)
    _print_sanity(frozen)

    md5_after = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 AFTER sanity: {md5_after}  "
          f"UNCHANGED={md5_after == md5_before}")
    if md5_after != md5_before:
        raise SystemExit("HARD STOP: seed write detected during --stage sanity.")
    return 0


def _print_sanity(frozen: dict) -> None:
    print(f"\n  ---- BACKGROUND-SANITY GATE (n={frozen['n']}, {frozen['ep_alphs']}) ----")
    print(f"    GUARD  (equal-weight composition):     acc={100*frozen['acc_guard']:.1f}%  "
          f"k={frozen['k_guard']}/{frozen['n']}")
    print(f"    ARM W  (tightness-weighted composition): acc={100*frozen['acc_armw']:.1f}%  "
          f"k={frozen['k_armw']}/{frozen['n']}")
    delta = frozen["acc_armw"] - frozen["acc_guard"]
    print(f"    delta = {100*delta:+.1f}pp   hard-stop bound = GUARD - "
          f"{100*frozen['sanity_margin']:.0f}pp")
    print(f"    VERDICT: {'PASS -- proceed to --stage eval' if frozen['passed'] else 'STOP -- do NOT spend any eval budget'}")


def _require_sanity() -> dict:
    if not os.path.exists(SANITY_PATH):
        print("  WALL: run --stage sanity to completion first.")
        sys.exit(1)
    return _load_json(SANITY_PATH)


# ============================================================================================= #
# STAGE: eval -- GUARD vs ARM W on the EVAL population (n=160, SAME continuing RNG stream as
# sanity, so the SANITY blocks are never re-drawn).
# ============================================================================================= #
EVAL_STATE_PATH = _ckpt("eval_state.json")
EVAL_PATH = _ckpt("eval.json")


def stage_eval() -> int:
    print(f"\n{SEP}\n  STAGE: eval (GUARD vs ARM W, EVAL population)\n{SEP}")
    sanity = _require_sanity()
    if not sanity["passed"]:
        print("  WALL: sanity STOPPED -- per this run's own binding rule, NO eval budget may "
              "be spent. Report the sanity finding and stop here.")
        return 1
    weights = _require_weights()
    md5_before = _md5(STROKE_SHAPES_SEED)

    population = _episode_population()
    ep_alphs = sorted(population)

    state = _load_json(EVAL_STATE_PATH) if os.path.exists(EVAL_STATE_PATH) else dict(
        alph_idx=0, records=[])

    s = run50._load_codebook_substrate()
    native = s._inner
    cache: dict = {}
    # THE SAME RNG SEED as --stage sanity, but the stream must first consume EXACTLY the draws
    # --stage sanity already made (N_BLOCKS_SANITY blocks per alphabet) before this stage's own
    # EVAL blocks begin -- replaying sanity's own per-alphabet loop shape (same function, same
    # block count, same population) reproduces that exact prefix deterministically.
    rng = np.random.default_rng(RUN52_SEED)
    for alph in ep_alphs:
        way_classes = population[alph]
        files_by_drawer = {cdir: run50._files_by_drawer(cdir) for cdir in way_classes}
        for _b in range(N_BLOCKS_SANITY):
            _run_one_block(s, native, way_classes, files_by_drawer, rng, cache, weights)
    print(f"  replayed {len(ep_alphs)} alphabets x {N_BLOCKS_SANITY} SANITY block(s) each to "
          f"advance the RNG stream past --stage sanity's own draws (no block overlap).")

    for i in range(state["alph_idx"]):
        way_classes = population[ep_alphs[i]]
        files_by_drawer = {cdir: run50._files_by_drawer(cdir) for cdir in way_classes}
        for _b in range(N_BLOCKS_EVAL):
            _run_one_block(s, native, way_classes, files_by_drawer, rng, cache, weights)

    hard_deadline = time.time() + 460.0
    t0 = time.time()
    while state["alph_idx"] < len(ep_alphs) and time.time() < hard_deadline:
        alph = ep_alphs[state["alph_idx"]]
        way_classes = population[alph]
        files_by_drawer = {cdir: run50._files_by_drawer(cdir) for cdir in way_classes}
        for _b in range(N_BLOCKS_EVAL):
            recs = _run_one_block(s, native, way_classes, files_by_drawer, rng, cache, weights)
            if recs:
                state["records"].extend(recs)
        state["alph_idx"] += 1
        _save_json(state, EVAL_STATE_PATH)
        print(f"  alphabet {state['alph_idx']}/{len(ep_alphs)} ({alph!r}) done -- "
              f"{len(state['records'])} episodes so far, {time.time()-t0:.1f}s this call",
              flush=True)

    if state["alph_idx"] < len(ep_alphs):
        print(f"\n  PARTIAL: {state['alph_idx']}/{len(ep_alphs)} alphabets done -- re-invoke to "
              f"continue.")
        return 0

    records = state["records"]
    n = len(records)
    k_guard = sum(1 for r in records if r["guard_correct"])
    k_armw = sum(1 for r in records if r["armw_correct"])
    out = dict(n=n, k_guard=k_guard, k_armw=k_armw, acc_guard=k_guard / n, acc_armw=k_armw / n,
               ep_alphs=ep_alphs, records=records, done=True)
    _save_json(out, EVAL_PATH)
    print(f"\n  EVAL COMPLETE: n={n}  GUARD acc={100*k_guard/n:.1f}% k={k_guard}  "
          f"ARM W acc={100*k_armw/n:.1f}% k={k_armw}")

    md5_after = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 AFTER eval: {md5_after}  "
          f"UNCHANGED={md5_after == md5_before}")
    if md5_after != md5_before:
        raise SystemExit("HARD STOP: seed write detected during --stage eval.")
    return 0


def _require_eval() -> dict:
    if not os.path.exists(EVAL_PATH) or not _load_json(EVAL_PATH).get("done"):
        print("  WALL: run --stage eval to completion first.")
        sys.exit(1)
    return _load_json(EVAL_PATH)


# ============================================================================================= #
# STAGE: report.
# ============================================================================================= #
def stage_report() -> int:
    print(f"\n{SEP}\n  RUN 52 -- VARIATION-AWARE COMPOSITION -- FINAL REPORT\n{SEP}")
    md5_now = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5: {md5_now}")

    sanity = _require_sanity()
    lr = _load_json(LEARN_RELATIONAL_PATH_50)
    weights = lr["weights"]
    split = lr["tight_loose_split"]

    print(f"\n{'='*35}  SANITY-GATE (decides everything)  {'='*35}")
    _print_sanity(sanity)

    print(f"\n  ---- TIGHT/LOOSE WEIGHT STRUCTURE (run 50's own frozen model, READ-ONLY) ----")
    for slot in split["ordered_tightest_first"]:
        tag = "TIGHT" if slot in split["tight"] else "LOOSE"
        print(f"    {slot:<9} weight={weights[slot]:7.4f}  variance={split['variances'][slot]:8.4f}"
              f"  [{tag}]")
    wvals = list(weights.values())
    print(f"    weight range: min={min(wvals):.4f} max={max(wvals):.4f} "
          f"ratio={max(wvals)/min(wvals):.2f}x  "
          f"({'REAL structure to learn' if max(wvals)/min(wvals) > 2.0 else 'NEARLY FLAT -- mechanism starved, per the run-28 engagement-vs-outcome law'})")

    if not sanity["passed"]:
        print(f"\n  {'='*30}  SANITY STOPPED -- NO EVAL WAS RUN, PER THIS RUN'S OWN BINDING "
              f"RULE  {'='*30}")
        print(f"  (ARM W background accuracy {100*sanity['acc_armw']:.1f}% fell more than "
              f"{100*sanity['sanity_margin']:.0f}pp below GUARD {100*sanity['acc_guard']:.1f}%)")
        print(f"\n  VERDICT: even NATIVE tightness-weighting of the composition metric harms "
              f"in-sample background accuracy before any eval-alphabet-analogue episode is "
              f"spent -- the loop-flip does not convert at the METRIC-REWEIGHT level; the next "
              f"lever must go DEEPER than reweighting an existing metric's constants (a fuller "
              f"generative-concept build where the concept PREDICTS the parse, not merely "
              f"reweights a match/mismatch indicator).")
        return 0

    ev = _require_eval()
    records = ev["records"]
    n = len(records)
    print(f"\n  ---- EVAL POPULATION (n={n}, {ev['ep_alphs']}) ----")

    correct_guard = [r["guard_correct"] for r in records]
    correct_armw = [r["armw_correct"] for r in records]
    k_guard, k_armw = sum(correct_guard), sum(correct_armw)
    ci_guard = _wilson(k_guard, n)
    ci_armw = _wilson(k_armw, n)
    print(f"    GUARD (equal-weight):       acc={100*k_guard/n:.1f}%  "
          f"[{100*ci_guard[0]:.1f}%,{100*ci_guard[1]:.1f}%]  k={k_guard}/{n}")
    print(f"    ARM W (tightness-weighted): acc={100*k_armw/n:.1f}%  "
          f"[{100*ci_armw[0]:.1f}%,{100*ci_armw[1]:.1f}%]  k={k_armw}/{n}")
    print(f"    CI-separated: {gate._ci_separated(tuple(ci_armw), tuple(ci_guard))}")

    mc = _mcnemar(correct_guard, correct_armw)
    print(f"\n  ---- McNEMAR (ARM W vs GUARD, n={n}) ----")
    print(f"    fixed={mc['fixed']}  broken={mc['broken']}  discordant={mc['discordant']}  "
          f"p={mc['p']:.4g}")

    out = dict(n=n, acc_guard=dict(acc=k_guard / n, ci=list(ci_guard), k=k_guard),
               acc_armw=dict(acc=k_armw / n, ci=list(ci_armw), k=k_armw), mcnemar=mc,
               weights=weights, tight_loose_split=split)
    _save_json(out, _ckpt("report.json"))
    print(f"\n  report.json written.")

    print(f"\n  {'='*30}  DOES THE LOOP-FLIP CONVERT?  {'='*30}")
    if mc["discordant"] and mc["fixed"] > mc["broken"] and \
            gate._ci_separated(tuple(ci_armw), tuple(ci_guard)):
        print(f"  WIN: tightness-weighting the composition metric NATIVELY converts to accuracy "
              f"-- the first crack via the loop-flip direction (the concept's variation model "
              f"CAN act as the compositional metric itself). This licenses the fuller "
              f"generative-concept build (wiring composition into the geometry verdict, or a "
              f"concept that predicts the parse).")
    elif mc["discordant"] and mc["fixed"] > mc["broken"]:
        print(f"  WEAK POSITIVE: fixed > broken but not CI-separated -- suggestive, not "
              f"conclusive; report as a lead validating the DIRECTION, not a converted result.")
    elif mc["discordant"] and mc["broken"] >= mc["fixed"]:
        print(f"  NULL (STOP CONDITION): broken >= fixed -- even concept-as-COMPOSITION-METRIC "
              f"(native, unconditional, no bolt-on) is not enough. The loop-flip must go DEEPER "
              f"than reweighting an existing metric's constants: the concept must PREDICT the "
              f"parse itself (a genuinely generative use of the variation model), not merely "
              f"reweight a match/mismatch indicator inside the existing coverage Term. This "
              f"localizes FURTHER than run 51 (bolt-on architecture) -- it rules out NATIVE "
              f"metric-reweighting too -- while still being forward progress: it narrows what "
              f"'participate in the verdict' must mean.")
    else:
        print(f"  NULL: no discordant pairs / no effect either direction.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  seeds/stroke_shapes.json md5 (post-run, must equal the pre-run value above): "
          f"{_md5(STROKE_SHAPES_SEED)}")
    return 0


STAGES = {"unit_sanity": stage_unit_sanity, "sanity": stage_sanity, "eval": stage_eval,
          "report": stage_report}


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
