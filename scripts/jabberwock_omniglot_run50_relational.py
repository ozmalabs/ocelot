"""OMNIGLOT RUN 50 GATE 0 -- THE CRUX FALSIFIER for the N-layer / amortized-BPL hypothesis.

THE HYPOTHESIS (creator, verbatim): "Does it mean we need N layers, not two? The compute
requirements of BPL are the failure, not the outcome." Operationalized (entry 38/49): BPL's edge
over our training-free verdict is a LEARNED WITHIN-CLASS VARIATION PRIOR (NOT an orthogonal
motor signal -- run 49 proved motor is a redundant paraphrase of shape) -- a model of how a
class's form VARIES, which BPL gets from 30 background alphabets + per-decision MCMC search.
THE BET this run tests: that prior can be AMORTIZED into a cheap, mechanically-learned layer
(the codebook/statistic IS the cached search) rather than re-searched per decision. The candidate
layer: a RELATIONAL-VARIATION prior at the COMPOSITIONAL level (`domains/character_compose.py`'s
arrangement relations -- where composition already gave +21pp, run 3) -- the single most-likely
orthogonal, cheaply-learnable layer never yet built. This run tests whether that signal is
ORTHOGONAL and ADDITIVE to SC+TPS (licensing the N-layer/amortized-BPL programme -- one piece of
the layer set found) or REDUNDANT the way motor was (this PARTICULAR layer/grain is not it --
"wrong layer, keep searching", never "compute is unavoidable": a human recognises a novel
character in milliseconds with no per-decision search, so a low-compute route provably exists;
BPL's MCMC is one expensive route to it, not the only one).

CORPUS: Omniglot (mouse, MULTI-STROKE -- where arrangement/relations LIVE; DigiLeTs is 66%
single-stroke, relations are structurally absent there, per run 49's own honesty note). PURE
MEASUREMENT -- no eval-accuracy spend, no minting, background alphabets ONLY (the SAME 5 LEARN
alphabets `scripts/jabberwock_omniglot_dynamic_quantization.py`'s own LEARN stage already uses,
via `results/run26_checkpoints/learn.json`'s already-grown codebook, READ-ONLY). NO eval-alphabet
contact anywhere in this script (asserted structurally: `ow.alphabets("evaluation")` is never
called).

THE TWO NEW PIECES (`domains/relational_variation.py`, this run's own PART 1 build):
  1. A background relational-variation model: for every MULTI-STROKE (>=2 strokes) background
     class, over its own drawers, per-stroke `rel`/whole-character `cpose` bins are aligned
     across drawers (the FIXED greedy matcher, `scripts.jabberwock_omniglot_run39_motorplan.
     greedy_match` -- run36's own `_greedy_stroke_match` has a falsy-zero bug, `v or nan`, that
     silently discards a genuine zero-cost/identical-stroke match; run39's `_pointset_cost`
     already carries the fix, reused here rather than re-fixed) and pooled into a per-slot
     (rel_x/y/o/s, cpose_x/y/o/s) VARIANCE, mechanical statistics only, no search. Pooling across
     classes gives ONE class-general tightness weight per slot (`slot_weights`) -- the amortized
     twin of BPL's per-class variation prior.
  2. `relational_distance` -- a per-candidate scalar (lower = more similar), the arrangement
     mismatch between query and candidate WEIGHTED by that learned tightness (a mismatch on a
     TIGHT slot costs more than an equal mismatch on a LOOSE slot) -- Mahalanobis-in-relation-
     space at the COMPOSITIONAL grain (run 44's own version of this idea, at the whole-shape/
     affine grain, nulled; this is the untested grain).

THE VERDICT -- run 49's EXACT orthogonality-diagnostic method, reused, not re-invented (`m_true`/
`m_false`/correlation): r_true vs r_false means + separation ratio (vs geo's own, and vs run 49's
motor 1.5x/corr 0.48 benchmarks); corr(r, geo_score); THE KEY 2x2 run 49 could not compute
(motor was globally redundant) -- among episodes SC+TPS gets WRONG, does r rank the true class
BETTER (the orthogonal-add potential); among geo-correct episodes, does r stay consistent.

PRE-REGISTERED BARS (stated here, before any number below is computed):
  LICENSED  if corr(r, geo) is MATERIALLY LOWER than run 49's motor corr=0.48 AND r ranks
            true-class-better on a MATERIAL fraction (bar: >30%) of geo-WRONG episodes AND
            r_true < r_false with non-trivial separation.
  REDUNDANT if corr is high (near/above 0.48) or the conditional-on-geo-wrong lift is below the
            30% bar -- reported as "this candidate layer/grain is redundant with SC+TPS; a
            different orthogonal layer remains to be found", NEVER as evidence the amortization
            itself is impossible (the human existence proof settles compute-avoidability as a
            fact, not a hypothesis under test here).

EXECUTION (ops law, binding): every invocation <=540s foreground, `stdbuf -oL ... | tee -a
results/omniglot_gate_run50.log`, intra-stage checkpoints under `results/run50_checkpoints/`
(every OTHER `results/run*_checkpoints/` directory is READ-ONLY reference, never written here).
`.venv` python (needs `substrate_rs`). `OZMA_SEED_PERSIST_DISABLED=1` is set at import time
(belt-and-suspenders on top of the durable `commit 21aa6123` guard -- a decode call on a drawer
outside LEARN's own 01-14 range could in principle OOV-mint; this run's own decode calls must
never persist to the real `seeds/stroke_shapes.json` regardless).

Stages, in dependency order:
  unit_sanity      seed-guard (before) + protocol guard (replay run26's own block/RNG chain,
                    verify the CITED per-alphabet error table from `run36`'s own citation,
                    read-only) + run `tests/test_relational_variation_migrated.py`.
  learn_relational Build the background relational-variation model (multi-stroke classes only).
  gate0            Background multi-stroke 20-way episodes -- geo_score (SC+TPS) + r
                    (relational_distance) per candidate, the orthogonality table, the
                    conditional-on-geo-wrong lift, the differ-by-a-hook check.
  summary          Print the final consolidated verdict.

Run (from the gamma-substrate repo root):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run50_relational.py --stage <STAGE>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")   # belt-and-suspenders, see docstring.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run25_number as run25
import scripts.jabberwock_omniglot_run26_homework as run26
import scripts.jabberwock_omniglot_run36_failures as run36
from domains import abs_read as ar
from domains import omniglot_world as ow
from domains import relational_variation as rv

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run50_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")     # READ-ONLY reference.
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
RUN50_SEED = gate.SEED + 9000            # this run's own seed, distinct from every prior run's.
DK = gate.DK                             # the SAME reduced bins the standing codebook was
                                          # grown at -- load-bearing, per run26's own note.
MIN_STROKES_MULTI = 2                    # "multi-stroke" filter, pre-registered.
LEARN_DRAWERS_FOR_VARIATION = [f"{i:02d}" for i in range(1, 11)]   # 10 of 20 drawers per class
                                          # -- enough to estimate a within-class spread cheaply
                                          # (wall-clock, not a search parameter).
WAY = 20
N_BLOCKS_PER_ALPHABET = 2                # 4 alphabets x 2 blocks x 20 queries = 160 episodes.
EX_DRAWERS_POOL = [f"{i:02d}" for i in range(15, 21)]   # exemplar drawers OUTSIDE the variation
                                          # model's own 01-10 range -- independent instances.
N_BOOT = 500                             # bootstrap CI reps, fixed seed.

# RUN 49's OWN CITED BENCHMARKS (motor verdict, `83f91a0e`) -- the comparison bars this run's
# own pre-registration is stated against, cited verbatim, never re-derived here.
RUN49_MOTOR_CORR = 0.48
RUN49_MOTOR_SEPARATION = 1.5
RUN49_GEO_SEPARATION_CITED = 2.3
CONDITIONAL_LIFT_BAR = 0.30              # pre-registered: >30% of geo-wrong episodes improved.


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


def _bootstrap_ci(values: list, statfn, n_boot: int = N_BOOT, seed: int = RUN50_SEED) -> tuple:
    """Percentile bootstrap 95% CI of `statfn(resample)` over `values` (a list of per-episode
    rows -- `statfn` receives a resampled list of the SAME rows). Pure reporting statistic, no
    decision."""
    rng = np.random.default_rng(seed)
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    stats = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        stats.append(statfn([values[i] for i in idx]))
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return (float(lo), float(hi))


# ============================================================================================= #
# STAGE: unit_sanity
# ============================================================================================= #
def _test_alphabets_run36_style():
    """Cited-verbatim reconstruction (read-only) of run36's own `_test_alphabets` -- the 10
    EVALUATION alphabets `results/run26_checkpoints/eval_baseline.json` was scored against.
    Used ONLY for the protocol guard (verifying run26's own recorded numbers, never touching
    eval data itself beyond re-deriving which alphabet/drawer a stored index refers to)."""
    return run36._test_alphabets(run25, ow)


def stage_unit_sanity() -> int:
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    ok_all = True
    md5_before = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 (BEFORE this run touches anything): {md5_before}")
    print(f"  OZMA_SEED_PERSIST_DISABLED={os.environ.get('OZMA_SEED_PERSIST_DISABLED')!r} "
          f"(belt-and-suspenders on top of the durable commit-21aa6123 guard)")

    # ---- (a) protocol guard: replay run26's own block/RNG chain, verify run36's CITED table. ---
    print("\n  (a) PROTOCOL GUARD -- replay run26's eval_baseline.json block/RNG chain, verify "
          "run36's cited per-alphabet error table (read-only; run36_checkpoints untouched).")
    records = run36._load_eval_baseline()
    blocks26, test_alphabets = run36._reconstruct_run26_blocks(run25, ow)
    ok_a = len(blocks26) == 20 and len(records) == 400
    from collections import defaultdict
    per_alph_err = defaultdict(int)
    for i, r in enumerate(records):
        if r["pred_full"] != r["true"]:
            per_alph_err[r["alph"]] += 1
    table_ok = all(per_alph_err[a] == run36.CITED_PER_ALPH_FULL_DWELL_ERRORS[a]
                   for a in test_alphabets)
    total_err = sum(1 for r in records if r["pred_full"] != r["true"])
    ok_a = ok_a and table_ok and total_err == run36.CITED_TOTAL_FULL_DWELL_ERRORS
    print(f"      blocks={len(blocks26)} records={len(records)} total_full_dwell_errors="
          f"{total_err} (cited {run36.CITED_TOTAL_FULL_DWELL_ERRORS}) table_matches={table_ok} "
          f"-> {'PASS' if ok_a else 'FAIL'}")
    ok_all &= ok_a

    # ---- (b) the 5 LEARN background alphabets are exactly run26's own, no eval-alphabet touch --
    learn_alphs = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    ok_b = learn_alphs == _load_json(os.path.join(RUN26_DIR, "learn_meta.json"))["learn_alphabets"]
    print(f"\n  (b) LEARN alphabets match run26's own citation: {learn_alphs} -> "
          f"{'PASS' if ok_b else 'FAIL'}")
    ok_all &= ok_b

    # ---- (c) tests/test_relational_variation_migrated.py -----------------------------------
    print("\n  (c) tests/test_relational_variation_migrated.py")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_relational_variation_migrated.py", "-q"],
        cwd=ROOT, env={**os.environ}, capture_output=True, text=True, timeout=120)
    print(proc.stdout[-4000:])
    if proc.returncode != 0:
        print(proc.stderr[-4000:])
    ok_c = proc.returncode == 0
    print(f"      -> {'PASS' if ok_c else 'FAIL'}")
    ok_all &= ok_c

    md5_after = _md5(STROKE_SHAPES_SEED)
    ok_seed = md5_after == md5_before
    print(f"\n  seeds/stroke_shapes.json md5 AFTER unit_sanity: {md5_after}  "
          f"UNCHANGED={ok_seed}")
    ok_all &= ok_seed
    if not ok_seed:
        raise SystemExit("HARD STOP: seed write detected during --stage unit_sanity.")

    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}"
          f"\n{SEP}")
    _save_json({"ok_all": ok_all, "stroke_shapes_md5_before": md5_before,
                "protocol_guard_ok": bool(ok_a), "learn_alphabets": learn_alphs},
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


# ============================================================================================= #
# SHARED -- load the standing background codebook (READ-ONLY reference), multi-stroke filter.
# ============================================================================================= #
def _load_codebook_substrate():
    return run26._load_graph(os.path.join(RUN26_DIR, "learn.json"))


def _multi_stroke_classes(alphabets: list) -> dict:
    """`{alphabet: [class_dir, ...]}` -- median RAW pen-stroke count (over all 20 drawers)
    `>= MIN_STROKES_MULTI`. Deterministic (sorted), no RNG."""
    out = {}
    for alph in alphabets:
        chars = ow.characters(alph, "background")
        qualifying = []
        for cdir in chars:
            counts = [len(ow.load_strokes(f)) for f in ow.drawings(cdir)]
            if counts and float(np.median(counts)) >= MIN_STROKES_MULTI:
                qualifying.append(cdir)
        out[alph] = sorted(qualifying)
    return out


def _files_by_drawer(cdir: str) -> dict:
    files = {}
    for f in ow.drawings(cdir):
        d = f.split("/")[-1].split("_")[-1].replace(".txt", "")
        files[d] = f
    return files


# ============================================================================================= #
# STAGE: learn_relational -- the background relational-variation model.
# ============================================================================================= #
def stage_learn_relational() -> int:
    print(f"\n{SEP}\n  STAGE: learn_relational (background relational-variation model, "
          f"multi-stroke classes only)\n{SEP}")
    t0 = time.time()
    _require_unit_sanity()
    md5_before = _md5(STROKE_SHAPES_SEED)

    s = _load_codebook_substrate()
    native = s._inner
    learn_alphs = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    multi = _multi_stroke_classes(learn_alphs)
    counts = {a: len(cs) for a, cs in multi.items()}
    total_multi = sum(counts.values())
    total_chars = sum(len(ow.characters(a, "background")) for a in learn_alphs)
    print(f"  LEARN alphabets: {learn_alphs}")
    print(f"  multi-stroke classes (median raw stroke count >= {MIN_STROKES_MULTI}) per "
          f"alphabet: {counts}  total={total_multi}/{total_chars}")

    cache: dict = {}
    per_class_variances = []
    n_classes_used = 0
    n_decoded = 0
    for alph in learn_alphs:
        for cdir in multi[alph]:
            files_by_drawer = _files_by_drawer(cdir)
            drawer_files = [files_by_drawer[d] for d in LEARN_DRAWERS_FOR_VARIATION
                             if d in files_by_drawer]
            if len(drawer_files) < 2:
                continue
            decoded = [gate.decode_char_signature(s, f, cache, DK) for f in drawer_files]
            n_decoded += len(decoded)
            ref = decoded[0]
            others = [(d["stroke_points"], d["composed_sig"]) for d in decoded[1:]]
            var = rv.class_slot_variances(native, ref["stroke_points"], ref["composed_sig"],
                                           others, turn_bins=DK["turn_bins"])
            if var is not None:
                per_class_variances.append(var)
                n_classes_used += 1
        print(f"    ... {alph}: {len(multi[alph])} multi-stroke classes processed "
              f"[elapsed {time.time()-t0:.1f}s, decodes so far={n_decoded}]", flush=True)

    pooled = rv.pool_variation(per_class_variances)
    weights = rv.slot_weights(pooled)
    split = rv.tight_loose_split(pooled)

    print(f"\n  pooled across {pooled['_n_classes']} classes (of {total_multi} qualifying, "
          f"{n_classes_used} had >=2 usable instances):")
    for slot in rv.ALL_SLOTS:
        print(f"    {slot:<9} variance={pooled[slot]:8.4f}  weight={weights[slot]:6.3f}  "
              f"tightness={'TIGHT' if slot in split['tight'] else 'LOOSE'}")
    print(f"  median variance: {split['median_variance']:.4f}")
    print(f"  TIGHT slots: {split['tight']}")
    print(f"  LOOSE slots: {split['loose']}")

    out = {"learn_alphabets": learn_alphs, "multi_stroke_counts": counts,
           "total_multi_stroke": total_multi, "total_characters": total_chars,
           "n_classes_pooled": pooled["_n_classes"], "per_class_variances": per_class_variances,
           "pooled_variance": {s: pooled[s] for s in rv.ALL_SLOTS},
           "weights": weights, "tight_loose_split": split, "elapsed": time.time() - t0}
    _save_json(out, _ckpt("learn_relational.json"))
    print(f"\n  saved -> {_ckpt('learn_relational.json')}")

    md5_after = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5 AFTER learn_relational: {md5_after}  "
          f"UNCHANGED={md5_after == md5_before}")
    if md5_after != md5_before:
        raise SystemExit("HARD STOP: seed write detected during --stage learn_relational.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [learn_relational wall time: {time.time()-t0:.1f}s]")
    return 0


def _require_learn_relational() -> dict:
    p = _ckpt("learn_relational.json")
    if not os.path.exists(p):
        raise SystemExit("WALL: run --stage learn_relational first.")
    return _load_json(p)


# ============================================================================================= #
# STAGE: gate0 -- the orthogonality diagnostic.
# ============================================================================================= #
def _episode_alphabets(multi: dict) -> list:
    """Alphabets with >= WAY multi-stroke classes -- the ones that can host a genuine within-
    alphabet WAY-way episode. Deterministic order (the LEARN alphabet list's own order)."""
    return [a for a, cs in multi.items() if len(cs) >= WAY]


def stage_gate0() -> int:
    print(f"\n{SEP}\n  STAGE: gate0 (background multi-stroke {WAY}-way episodes -- geo_score vs "
          f"relational_distance)\n{SEP}")
    t0 = time.time()
    _require_unit_sanity()
    lr = _require_learn_relational()
    weights = lr["weights"]
    md5_before = _md5(STROKE_SHAPES_SEED)

    s = _load_codebook_substrate()
    native = s._inner
    learn_alphs = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    multi = _multi_stroke_classes(learn_alphs)
    ep_alphs = _episode_alphabets(multi)
    print(f"  alphabets with >= {WAY} multi-stroke classes (host within-alphabet {WAY}-way "
          f"episodes): {ep_alphs}")
    if not ep_alphs:
        raise SystemExit("WALL: no LEARN alphabet has >= WAY multi-stroke classes.")

    way_classes_by_alph = {a: multi[a][:WAY] for a in ep_alphs}

    cache: dict = {}
    rng = np.random.default_rng(RUN50_SEED)
    records = []
    n_blocks = 0
    for alph in ep_alphs:
        way_classes = way_classes_by_alph[alph]
        files_by_drawer = {cdir: _files_by_drawer(cdir) for cdir in way_classes}
        for _b in range(N_BLOCKS_PER_ALPHABET):
            ex_drawer = EX_DRAWERS_POOL[int(rng.integers(len(EX_DRAWERS_POOL)))]
            exemplar_files = [files_by_drawer[cdir].get(ex_drawer) for cdir in way_classes]
            if any(f is None for f in exemplar_files):
                continue    # honest skip -- an alphabet lacking that drawer for some class.
            exemplars = [gate.decode_char_signature(s, f, cache, DK) for f in exemplar_files]
            exemplar_ps = [ar.whole_figure_point_set(run25._raw_stroke_points(f))
                           for f in exemplar_files]
            n_blocks += 1

            # 20x20 exemplar geo distance matrix (for the differ-by-a-hook check below).
            M = [[0.0] * WAY for _ in range(WAY)]
            for ci in range(WAY):
                for cj in range(ci + 1, WAY):
                    if exemplar_ps[ci] is None or exemplar_ps[cj] is None:
                        d = float("nan")
                    else:
                        term = ar.sctps_verdict_term(exemplar_ps[ci], exemplar_ps[cj])
                        d = float(native.evaluate(term, {}) or float("nan"))
                    M[ci][cj] = M[cj][ci] = d
            r_M = [[0.0] * WAY for _ in range(WAY)]
            for ci in range(WAY):
                for cj in range(ci + 1, WAY):
                    rr = rv.relational_distance(native, exemplars[ci]["stroke_points"],
                                                 exemplars[ci]["composed_sig"],
                                                 exemplars[cj]["stroke_points"],
                                                 exemplars[cj]["composed_sig"], weights)["r"]
                    r_M[ci][cj] = r_M[cj][ci] = rr

            # DIFFER-BY-A-HOOK, simplified analogue of run36's own methodology (that run's full
            # per-stroke ink-fraction machinery is out of scope for a cheap gate0 falsifier):
            # this block's own off-diagonal r_M distribution, used below to ask "where geo
            # thinks two exemplars are near-duplicates (smallest M), does r keep them apart
            # (a HIGH percentile rank in the block's own r_M distribution) or agree they're
            # close too (a LOW percentile rank, i.e. r is just as confused)."
            r_offdiag = [r_M[ci][cj] for ci in range(WAY) for cj in range(ci + 1, WAY)]

            for true_idx in range(WAY):
                q_drawer = int(rng.integers(20)) + 1
                q_drawer = f"{q_drawer:02d}"
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
                q_ps = ar.whole_figure_point_set(run25._raw_stroke_points(q_file))
                qd = gate.decode_char_signature(s, q_file, cache, DK)

                geo_scores, r_scores = [], []
                for ci in range(WAY):
                    if q_ps is None or exemplar_ps[ci] is None:
                        geo_scores.append(float("nan"))
                    else:
                        term = ar.sctps_verdict_term(q_ps, exemplar_ps[ci])
                        geo_scores.append(float(native.evaluate(term, {}) or float("nan")))
                    rr = rv.relational_distance(native, qd["stroke_points"], qd["composed_sig"],
                                                 exemplars[ci]["stroke_points"],
                                                 exemplars[ci]["composed_sig"], weights)
                    r_scores.append(rr["r"])

                nearest_impostor = min((M[true_idx][cj] for cj in range(WAY)
                                        if cj != true_idx and M[true_idx][cj] == M[true_idx][cj]),
                                       default=float("nan"))
                nearest_impostor_ci = min(
                    ((cj, M[true_idx][cj]) for cj in range(WAY)
                     if cj != true_idx and M[true_idx][cj] == M[true_idx][cj]),
                    key=lambda x: x[1], default=(None, float("nan")))[0]

                hook_r = (r_M[true_idx][nearest_impostor_ci]
                          if nearest_impostor_ci is not None else None)
                hook_r_percentile = (
                    float(np.mean([1.0 if x <= hook_r else 0.0 for x in r_offdiag]))
                    if hook_r is not None and r_offdiag else None)

                records.append(dict(alph=alph, block=n_blocks - 1, true_idx=true_idx,
                                     geo_scores=geo_scores, r_scores=r_scores,
                                     nearest_impostor_geo=nearest_impostor,
                                     nearest_impostor_idx=nearest_impostor_ci,
                                     r_to_nearest_impostor=hook_r,
                                     hook_r_percentile=hook_r_percentile))
            print(f"    ... {alph} block {n_blocks} scored ({WAY} queries) "
                  f"[elapsed {time.time()-t0:.1f}s, n_episodes={len(records)}]", flush=True)

    print(f"\n  n_episodes={len(records)}  n_blocks={n_blocks}  n_way={WAY}")
    _save_json({"records": records, "n_blocks": n_blocks, "ep_alphs": ep_alphs,
                "way_classes_by_alph": way_classes_by_alph, "elapsed": time.time() - t0},
               _ckpt("gate0_raw.json"))
    print(f"  saved raw -> {_ckpt('gate0_raw.json')}")

    md5_after = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5 AFTER gate0: {md5_after}  "
          f"UNCHANGED={md5_after == md5_before}")
    if md5_after != md5_before:
        raise SystemExit("HARD STOP: seed write detected during --stage gate0.")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [gate0 wall time: {time.time()-t0:.1f}s]")
    return 0


def _require_gate0_raw() -> dict:
    p = _ckpt("gate0_raw.json")
    if not os.path.exists(p):
        raise SystemExit("WALL: run --stage gate0 first.")
    return _load_json(p)


def _rank_of_true(scores: list, true_idx: int) -> "int | None":
    """1-based rank of the true class by ASCENDING score (1 = best/lowest -- the argmin
    convention every score here shares). `None` if the true score is NaN (degenerate query)."""
    t = scores[true_idx]
    if t != t:
        return None
    return 1 + sum(1 for i, v in enumerate(scores) if i != true_idx and v == v and v < t)


# ============================================================================================= #
# STAGE: analysis -- the orthogonality table (run 49's exact method).
# ============================================================================================= #
def stage_analysis() -> int:
    print(f"\n{SEP}\n  STAGE: analysis -- THE ORTHOGONALITY TABLE\n{SEP}")
    raw = _require_gate0_raw()
    records = raw["records"]
    n = len(records)
    print(f"  n_episodes={n}")

    geo_true = [r["geo_scores"][r["true_idx"]] for r in records]
    geo_false = [np.mean([v for i, v in enumerate(r["geo_scores"])
                           if i != r["true_idx"] and v == v]) for r in records]
    r_true = [r["r_scores"][r["true_idx"]] for r in records]
    r_false = [np.mean([v for i, v in enumerate(r["r_scores"]) if i != r["true_idx"]])
               for r in records]

    geo_true_mean, geo_false_mean = float(np.nanmean(geo_true)), float(np.nanmean(geo_false))
    r_true_mean, r_false_mean = float(np.mean(r_true)), float(np.mean(r_false))
    geo_sep = geo_false_mean / geo_true_mean if geo_true_mean else float("nan")
    r_sep = r_false_mean / r_true_mean if r_true_mean else float("nan")

    print(f"\n  GEO (SC+TPS):  true_mean={geo_true_mean:.4f}  false_mean={geo_false_mean:.4f}  "
          f"separation(false/true)={geo_sep:.3f}x  (run 16 cited ~{RUN49_GEO_SEPARATION_CITED}x)")
    print(f"  R (relational): true_mean={r_true_mean:.4f}  false_mean={r_false_mean:.4f}  "
          f"separation(false/true)={r_sep:.3f}x  (run 49's motor was "
          f"{RUN49_MOTOR_SEPARATION}x)")

    r_gap_ci = _bootstrap_ci(list(zip(r_true, r_false)),
                              lambda rows: np.mean([b for _a, b in rows]) -
                                           np.mean([a for a, _b in rows]))
    print(f"  R gap (false-true) bootstrap 95% CI: {r_gap_ci}")

    # ---- correlation(r, geo), flattened over every (episode, candidate) pair -----------------
    geo_flat, r_flat = [], []
    for rec in records:
        for gv, rv_ in zip(rec["geo_scores"], rec["r_scores"]):
            if gv == gv:
                geo_flat.append(gv)
                r_flat.append(rv_)
    corr = float(np.corrcoef(geo_flat, r_flat)[0, 1]) if len(geo_flat) > 2 else float("nan")
    print(f"\n  corr(r, geo) over {len(geo_flat)} (episode, candidate) pairs: {corr:.4f}  "
          f"(run 49's motor: {RUN49_MOTOR_CORR})")

    def _corr_stat(rows):
        g = [a for a, _b in rows]
        rr = [b for _a, b in rows]
        if len(g) < 3 or np.std(g) == 0 or np.std(rr) == 0:
            return float("nan")
        return float(np.corrcoef(g, rr)[0, 1])
    corr_ci = _bootstrap_ci(list(zip(geo_flat, r_flat)), _corr_stat)
    print(f"  corr(r, geo) bootstrap 95% CI: {corr_ci}")

    # ---- THE KEY 2x2 -- conditional on geo right/wrong, does r help or stay consistent -------
    geo_wrong_rows, geo_correct_rows = [], []
    for rec in records:
        geo_pred_rank = _rank_of_true(rec["geo_scores"], rec["true_idx"])
        r_pred_rank = _rank_of_true(rec["r_scores"], rec["true_idx"])
        if geo_pred_rank is None or r_pred_rank is None:
            continue
        row = dict(geo_rank=geo_pred_rank, r_rank=r_pred_rank)
        if geo_pred_rank == 1:
            geo_correct_rows.append(row)
        else:
            geo_wrong_rows.append(row)

    n_geo_wrong = len(geo_wrong_rows)
    n_improved = sum(1 for row in geo_wrong_rows if row["r_rank"] < row["geo_rank"])
    n_r_fixes_fully = sum(1 for row in geo_wrong_rows if row["r_rank"] == 1)
    frac_improved = n_improved / n_geo_wrong if n_geo_wrong else float("nan")
    ci_improved = _wilson(n_improved, n_geo_wrong) if n_geo_wrong else (0.0, 0.0)
    print(f"\n  CONDITIONAL ON GEO WRONG (n={n_geo_wrong}):")
    print(f"    r ranks true class BETTER than geo did: {n_improved}/{n_geo_wrong} = "
          f"{100*frac_improved:.1f}%  95% CI [{100*ci_improved[0]:.1f},{100*ci_improved[1]:.1f}]  "
          f"(pre-registered bar: >{100*CONDITIONAL_LIFT_BAR:.0f}%)")
    print(f"    r ranks true class #1 outright (geo missed it, r would have got it): "
          f"{n_r_fixes_fully}/{n_geo_wrong} = {100*n_r_fixes_fully/n_geo_wrong if n_geo_wrong else 0:.1f}%")

    n_geo_correct = len(geo_correct_rows)
    n_r_also_correct = sum(1 for row in geo_correct_rows if row["r_rank"] == 1)
    mean_r_rank_when_geo_correct = (float(np.mean([row["r_rank"] for row in geo_correct_rows]))
                                     if geo_correct_rows else float("nan"))
    print(f"\n  CONDITIONAL ON GEO CORRECT (n={n_geo_correct}):")
    print(f"    r ALSO correct (stays consistent): {n_r_also_correct}/{n_geo_correct} = "
          f"{100*n_r_also_correct/n_geo_correct if n_geo_correct else 0:.1f}%")
    print(f"    mean r-rank of true class: {mean_r_rank_when_geo_correct:.2f} "
          f"(1.0 = perfectly consistent)")

    # ---- differ-by-a-hook -----------------------------------------------------------------
    hook_percentiles = [r["hook_r_percentile"] for r in records
                         if r.get("hook_r_percentile") is not None]
    hook_mean = float(np.mean(hook_percentiles)) if hook_percentiles else float("nan")
    print(f"\n  DIFFER-BY-A-HOOK (simplified analogue of run 36's own methodology): mean "
          f"percentile rank of r_M at the geo-NEAREST-impostor exemplar pair, within that "
          f"block's own r_M distribution (n={len(hook_percentiles)}): {hook_mean:.3f}  "
          f"(0.5 = no effect; >0.5 = r keeps the geo-closest pairs MORE separated than a "
          f"typical pair; <0.5 = r is equally or more confused by them)")

    # ---- pre-registered verdict --------------------------------------------------------------
    corr_lower_than_motor = corr < RUN49_MOTOR_CORR - 0.05    # "materially lower", a stated
                                                               # margin, not a bare inequality.
    lift_bar_met = (n_geo_wrong > 0) and (frac_improved > CONDITIONAL_LIFT_BAR)
    separation_ok = r_true_mean < r_false_mean and r_sep > 1.05
    licensed = corr_lower_than_motor and lift_bar_met and separation_ok
    print(f"\n{SEP}\n  PRE-REGISTERED VERDICT\n{SEP}")
    print(f"    corr(r,geo)={corr:.3f} materially < run49 motor {RUN49_MOTOR_CORR}-0.05="
          f"{RUN49_MOTOR_CORR-0.05:.2f}: {corr_lower_than_motor}")
    print(f"    conditional-on-geo-wrong lift {100*frac_improved:.1f}% > "
          f"{100*CONDITIONAL_LIFT_BAR:.0f}% bar: {lift_bar_met}")
    print(f"    r_true<r_false with non-trivial separation ({r_sep:.3f}x > 1.05x): "
          f"{separation_ok}")
    print(f"    -> {'LICENSED (this layer is orthogonal + additive -- one piece of the N-layer '
                    'set)' if licensed else 'REDUNDANT AT THIS GRAIN (wrong layer here -- keep '
                    'searching; NOT evidence the amortization is impossible)'}")

    out = dict(n_episodes=n, geo_true_mean=geo_true_mean, geo_false_mean=geo_false_mean,
               geo_separation=geo_sep, r_true_mean=r_true_mean, r_false_mean=r_false_mean,
               r_separation=r_sep, r_gap_bootstrap_ci=r_gap_ci, corr_r_geo=corr,
               corr_bootstrap_ci=corr_ci, n_geo_wrong=n_geo_wrong, n_improved=n_improved,
               frac_improved=frac_improved, ci_improved=list(ci_improved),
               n_r_fixes_fully=n_r_fixes_fully, n_geo_correct=n_geo_correct,
               n_r_also_correct=n_r_also_correct,
               mean_r_rank_when_geo_correct=mean_r_rank_when_geo_correct,
               hook_mean_percentile=hook_mean, n_hook_pairs=len(hook_percentiles),
               corr_lower_than_motor=bool(corr_lower_than_motor),
               lift_bar_met=bool(lift_bar_met), separation_ok=bool(separation_ok),
               licensed=bool(licensed))
    _save_json(out, _ckpt("analysis.json"))
    print(f"\n  saved -> {_ckpt('analysis.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ============================================================================================= #
# STAGE: summary
# ============================================================================================= #
def stage_summary() -> int:
    print(f"\n{SEP}\n  RUN 50 GATE 0 -- FINAL SUMMARY\n{SEP}")
    needed = ["unit_sanity.json", "learn_relational.json", "gate0_raw.json", "analysis.json"]
    missing = [nm for nm in needed if not os.path.exists(_ckpt(nm))]
    if missing:
        print(f"  INCOMPLETE -- missing checkpoints: {missing}")
        return 1
    us = _load_json(_ckpt("unit_sanity.json"))
    lr = _load_json(_ckpt("learn_relational.json"))
    an = _load_json(_ckpt("analysis.json"))

    md5_before = us["stroke_shapes_md5_before"]
    md5_after = _md5(STROKE_SHAPES_SEED)
    print(f"\n  SEED GUARD: before={md5_before}  after={md5_after}  "
          f"UNCHANGED={md5_before == md5_after}")
    print(f"  PROTOCOL GUARD: {'PASS' if us['protocol_guard_ok'] else 'FAIL'}")

    print(f"\n  BACKGROUND MULTI-STROKE POOL: {lr['multi_stroke_counts']}  "
          f"total={lr['total_multi_stroke']}/{lr['total_characters']}  "
          f"pooled from {lr['n_classes_pooled']} classes")
    split = lr["tight_loose_split"]
    print(f"  TIGHT slots ({len(split['tight'])}): {split['tight']}")
    print(f"  LOOSE slots ({len(split['loose'])}): {split['loose']}")

    print(f"\n  ORTHOGONALITY TABLE (n={an['n_episodes']} episodes, {WAY}-way, background-only):")
    print(f"    geo (SC+TPS):    true={an['geo_true_mean']:.4f}  false={an['geo_false_mean']:.4f}"
          f"  separation={an['geo_separation']:.3f}x")
    print(f"    r (relational):  true={an['r_true_mean']:.4f}  false={an['r_false_mean']:.4f}  "
          f"separation={an['r_separation']:.3f}x  (run49 motor: {RUN49_MOTOR_SEPARATION}x)")
    print(f"    corr(r,geo)={an['corr_r_geo']:.3f} CI={an['corr_bootstrap_ci']}  "
          f"(run49 motor: {RUN49_MOTOR_CORR})")
    print(f"    conditional-on-geo-wrong lift: {100*an['frac_improved']:.1f}% "
          f"CI={[round(100*x,1) for x in an['ci_improved']]}  (n_geo_wrong={an['n_geo_wrong']})")
    print(f"    conditional-on-geo-correct consistency: "
          f"{100*an['n_r_also_correct']/an['n_geo_correct'] if an['n_geo_correct'] else 0:.1f}%")
    print(f"    differ-by-a-hook mean percentile: {an['hook_mean_percentile']:.3f} "
          f"(n={an['n_hook_pairs']})")

    print(f"\n  {'='*40}\n  VERDICT: {'LICENSED' if an['licensed'] else 'REDUNDANT AT THIS GRAIN'}"
          f"\n  {'='*40}")
    if an["licensed"]:
        print("  The relational-variation layer is ORTHOGONAL and ADDITIVE to SC+TPS -- one "
              "piece of the N-layer / amortized-BPL set the creator's hypothesis predicted. "
              "BUILD is licensed (not executed in this gate0 run).")
    else:
        print("  This candidate layer/grain (compositional-arrangement variation) is REDUNDANT "
              "with what SC+TPS already measures -- it is NOT evidence that amortized, low-"
              "compute recognition is impossible (a human recognises a novel character in "
              "milliseconds with no per-decision search, so a low-compute route provably "
              "exists; BPL's MCMC is one expensive route to it, not the only one). The correct "
              "reading is: wrong layer/grain, keep searching for the orthogonal piece.")

    overall = (bool(us["ok_all"]) and bool(us["protocol_guard_ok"]) and md5_before == md5_after
               and _donkey0())
    print(f"\n{SEP}\n  INVARIANTS: seed_guard={md5_before==md5_after}  "
          f"protocol_guard={us['protocol_guard_ok']}  donkey0={_donkey0()}  "
          f"OVERALL={'PASS' if overall else 'FAIL'}\n{SEP}")
    return 0 if overall else 1


# ============================================================================================= #
# MAIN
# ============================================================================================= #
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                   choices=["unit_sanity", "learn_relational", "gate0", "analysis", "summary"])
    args = p.parse_args()
    t0 = time.time()
    fn = {"unit_sanity": stage_unit_sanity, "learn_relational": stage_learn_relational,
          "gate0": stage_gate0, "analysis": stage_analysis, "summary": stage_summary}[args.stage]
    rc = fn()
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())
