"""jabberwock_omniglot_run47_pendata.py -- RUN 47: THE STROKE-GRAIN REBUILD ON PEN DATA, first
run of the post-Omniglot arc. Licensed by run 46 (`7930cc6c`, `OMNIGLOT_ARC.md` addendum 2): the
stroke grain is FERTILE on real pen/touch data (UCI pen: 1,826 identities at 17.1x the shuffled
null; QuickDraw touch: 684 at 3.76x) -- this run REBUILDS the grain with the existing
quantization/codebook machinery and measures what SURVIVES quantization (Gate A) and what it
BUYS end-to-end (Gate B), against a protected continuous-only baseline.

CORPORA (`domains/pen_world.py`, promoted from run 46's one-off loaders):
  - UCI Character Trajectories: 200Hz Wacom pen, 20 single-stroke classes, ONE writer for the
    WHOLE corpus (UCI CAVEAT, unchanged from run 46 -- every UCI result below is per-INSTANCE,
    not per-writer; UCI one-shot episodes are honestly WITHIN-WRITER).
  - QuickDraw raw ndjson, EXTENDED from run 46's 6 categories to 18
    (`pen_world.QD_CATEGORIES_BACKGROUND` + `pen_world.QD_CATEGORIES_HELDOUT`, decided BEFORE
    any eval number below, per module docstring): 10 background (LEARN codebook fit ONLY) + 8
    held-out (ZERO contact until Gate A/B). Device-split via `pen_world.stream_quickdraw_touch`
    (the run-46 integer-delta classifier, unmodified).

LEARN (this run's own step 2): per-corpus ADAPTIVE quantile edges
(`domains.adaptive_bins.compute_adaptive_edges`, fit FRESH on this run's own pen/touch
population -- Omniglot's edges are never reused, per that module's own discipline) fit on a
LEARN split ONLY (UCI: 60% per class; QuickDraw: the 10 background categories' touch subset),
PLUS the standard multi-grain codebook growth (`domains.ink_decode.decode_ink` +
`domains.stroke_codebook`, the SAME machinery `scripts/jabberwock_omniglot_dynamic_
quantization.py::run_learn` drives) on the identical LEARN population, fresh `boot_core()`
substrate + an explicit seed-write isolation (see `run_codebook_growth`'s own docstring for the
mid-run incident this closes) so `seeds/stroke_shapes.json` stays untouched, verified by an md5
check in `--stage unit_sanity` / `--stage summary`. PRE-REGISTERED PREDICTION (stated before
either growth curve is computed): the codebook grows well past mousewriting's 5-7 top-level
quanta before flattening; if it does not flatten by >200 top-level quanta (run-32's fragmentation
clause, transplanted), this run STOPS and reports the honest non-saturation rather than pushing
forward on a runaway codebook.

GATE A -- QUANTIZATION RETENTION (the core question): the SAME LEARN-fit adaptive edges,
FROZEN, are applied to the HELD-OUT split's own strokes (never touched by the edge fit) --
tokenized into fine/coarse program-type strings (`domains.stroke_programs`, run-46's exact
tokenize-as-identity protocol) -- and class-consistency vs a count-matched shuffled-class null
is computed on the HELD-OUT population only (`_p1c_block`, moved here verbatim from run 46).
This is a GENERALIZATION test run 46 itself never ran (run 46 fit its adaptive edges on the SAME
population it measured -- a mild circularity this run closes): does a codebook LEARNED on one
split of data still carry class signal on strokes it has never seen? BAR: quantized identity
retains >= 2x the shuffled null (the same licensing bar run 46 used), reported side-by-side with
run 46's own same-population citations (17.1x pen, 3.76x touch, cited not re-derived).

GATE B -- END-TO-END ONE-SHOT, three arms, McNemar-paired on the SAME episodes:
  (i)   CONTINUOUS-ONLY baseline: `domains.per_stroke_abs.classify` -- the arc's own established
        per-stroke SC+TPS (ShapeContextDist + TpsDeformDist) correspondence-AbS program score,
        argmin over candidates. Reused UNMODIFIED (only the point-set EXTRACTION is new, taking
        already-loaded stroke arrays directly rather than an Omniglot file path -- mechanical
        adapter code, not a new verdict).
  (ii)  QUANTIZED-PROPOSAL + continuous verdict: the SAME per-candidate SC+TPS score vector as
        (i), but the WINNER is argmin restricted to a shortlist -- the top-K candidates by
        quantized fine-grain program-type bag-overlap similarity to the query (the "bins
        propose, continuous decides" two-layer synthesis, `OMNIGLOT_ARC.md` section 2.5).
  (iii) QUANTIZED-ONLY: argmax quantized bag-overlap similarity alone, no continuous geometry --
        the pure-grain diagnostic (no bar; reports the grain's standalone worth).
PRIMARY: McNemar arm(ii) vs arm(i) on the SAME episodes. PRE-REGISTERED PREDICTION: on pen data
the quantized grain ADDS (unlike mousewriting, where it never could -- the corpus killed
stroke-interior information; run 46 revived it). STOP: arm(ii) broken >= fixed -> the union
harms even here, reported as the finding, not hidden.

CLAUDE.md SELF-CHECK (restated verbatim from run 46's own docstring, unmodified discipline):
this script is pure numerical/data-science research over pre-built world-adapter-class feature
extractors and the arc's own established held-Term geometric primitives (ShapeContextDist,
TpsDeformDist, native Rust evaluate calls) -- explicitly out of scope for the "no Python
decisions" rule in the same way `scripts/jabberwock_pendata_run46.py` and every other Omniglot-
arc gate script already is. No `torch`, no borrowed model, anywhere in this script (`_donkey0()`
checked in every stage's report). No write to any `results/run*_checkpoints/` directory other
than this run's own `results/run47_checkpoints/`. `seeds/stroke_shapes.json` must stay
untouched -- verified by an md5 checkpoint, not merely asserted, and THIS RUN'S OWN FIRST PASS
GOT IT WRONG (disclosed honestly, not hidden): `boot_core()` not loading the "stroke_shapes"
seed only means codebook growth STARTS from an empty codebook -- it does NOT mean
`stroke_codebook.grow_stroke_quantum`'s internal `teach()` calls stay in memory. `teach()`
persists every newly-minted quantum to `seeds/<category>.json` on disk BY DEFAULT (the same
mechanism every `tests/test_*_migrated.py` file's own `_isolate_seed_writes` fixture exists to
neutralize), and the first `learn_uci`/`learn_quickdraw` run really did mutate
`seeds/stroke_shapes.json` for real. Caught by this stage's own md5 check, fixed by
`run_codebook_growth` monkeypatching `domains.stroke_codebook.teach` to a throwaway temp
`seeds_dir` for the call's duration (see that function's own docstring) -- every checkpoint in
this file's final `results/run47_checkpoints/` was produced AFTER the fix, byte-identical to
the pre-fix numbers, and re-verified clean by a fresh `unit_sanity` + `summary` pass. The
remediation attempt (a `git checkout --` on the accidentally-mutated file) is its own separate,
honestly-reported incident -- see the run's final report for the full account.

EXECUTION DISCIPLINE (ops law, unchanged from every prior run in this arc): every stage is a
separate `--stage` invocation, self-contained, checkpointed to `results/run47_checkpoints/`,
printed with wall-clock timing; intra-stage checkpoints inside the two heaviest stages
(QuickDraw streaming, Gate B episode loops). <=540s foreground per invocation.

Run (from the gamma-substrate repo root):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run47_pendata.py --stage <STAGE>
Stages, in dependency order:
  unit_sanity -> device_split -> learn_uci -> learn_quickdraw -> gate_a_uci ->
  gate_a_quickdraw -> gate_b_uci -> gate_b_quickdraw -> summary
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from scipy.stats import binomtest

import substrate_rs as srs
from domains import adaptive_bins as ab
from domains import ink_decode as ink
from domains import pen_world as pw
from domains import per_stroke_abs as ps
from domains import stroke_codebook as sc
from domains import stroke_programs as sp

SEP = "=" * 92
EPS = 1e-9

CKPT_DIR = os.path.join(ROOT, "results", "run47_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS (stated before any real-data number is computed).
# ------------------------------------------------------------------------------------------- #
DK = dict(max_knots=16, min_span=2, max_span=10, segments=8, turn_bins=12, len_bins=6,
         grid=4, scale_bins=6)                    # byte-identical DEFAULT to run46's tokenizer
                                                    # DK plus decode_ink's own extra knobs.
GROWTH_WINDOW = 100                                # strokes per growth-curve row.
SATURATION_FRAGMENT_CAP = 200                      # run-32 fragmentation-clause transplant:
                                                    # codebook must flatten by this many top-
                                                    # level quanta, else STOP and report honest
                                                    # non-saturation.

UCI_TRAIN_FRAC = 0.6
UCI_SPLIT_SEED = 20260706

QD_LOAD_CAP_PER_CAT = 1200          # device_split / LEARN-gather cap per category.
QD_TOUCH_CAP_PER_CAT = 500          # cap on touch drawings kept per category after split.
QD_SPLIT_RAW_CAP = 6000             # raw-line ceiling per category while streaming for split.
QD_LEARN_STROKE_CAP = 2000          # CODEBOOK-GROWTH stroke cap (round-robin across the 10
                                    # background categories, 200/category) -- the arc's own
                                    # established LEARN_STROKE_CAP convention (1500-3000 pen-
                                    # down strokes, `jabberwock_omniglot_dynamic_quantization.py`
                                    # / run46's P3_STROKE_CAP), added AFTER a live timing
                                    # measurement on UCI showed ~157ms/decode_ink-stroke --
                                    # the full 9,967-stroke pooled QuickDraw LEARN population
                                    # would take ~26 minutes, far over this run's own <=540s
                                    # per-invocation budget. The ADAPTIVE-EDGE fit (a much
                                    # cheaper tokenize-only pass) still runs on the FULL pooled
                                    # population -- only the heavier decode_ink codebook-growth
                                    # loop is capped.

P1C_NULL_REPS = 100
RNG_SEED = 20260706

BAR_EXCESS_FACTOR = 2.0             # the run-46 licensing bar, unchanged.
RUN46_UCI_RAW_MULT = 17.1           # cited, NOT re-derived (results/run46_checkpoints/p3p4p5_uci.json)
RUN46_QD_RAW_MULT = 3.76            # cited, NOT re-derived (results/run46_checkpoints/p3p4p5_quickdraw.json)

# Gate B geometry / shortlist knobs (pre-registered; per_stroke_abs's own N/max_strokes
# defaults kept byte-identical to every existing caller).
POINTSET_N = 24
MAX_STROKES = 6
GATE_B_N_EPISODES = 220
GATE_B_UCI_SHORTLIST_K = 10          # of 20 -- the arc's own established shortlist@10 convention.
GATE_B_QD_SHORTLIST_K = 4            # of 8 -- proportionally matched.


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _donkey0() -> bool:
    return "torch" not in sys.modules


def _f(x, spec: str = ".4f") -> str:
    if x is None:
        return "None"
    return format(x, spec)


def _md5(path: str) -> str:
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple:
    """Copied verbatim (formula) from `scripts/jabberwock_omniglot_run34_mouse.py` / run46 --
    the arc's own standard 95% Wilson interval."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((centre - adj) / denom, (centre + adj) / denom)


def _mcnemar(base_correct: list, arm_correct: list) -> dict:
    """Copied verbatim (formula) from `scripts/jabberwock_omniglot_run44_metric.py`."""
    fixed = sum(1 for b, a in zip(base_correct, arm_correct) if (not b) and a)
    broken = sum(1 for b, a in zip(base_correct, arm_correct) if b and (not a))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


# ============================================================================================= #
#  STAGE: unit_sanity
# ============================================================================================= #
def stage_unit_sanity():
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    ok_all = True

    md5_before = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5 (BEFORE this run touches anything): {md5_before}")

    print("\n  (a) UCI loader round-trip (via domains.pen_world)")
    samples = pw.load_uci_samples()
    print(f"      n_samples={len(samples)}  classes={sorted(set(s['class'] for s in samples))}")
    s0 = samples[0]
    t = s0["t_ms"]
    ok_a = (bool(np.all(np.diff(t) > 0)) and bool(np.allclose(np.diff(t), t[1] - t[0])) and
           bool(np.all(np.isfinite(s0["pos_xy"]))))
    print(f"      -> {'PASS' if ok_a else 'FAIL'}")
    ok_all &= ok_a

    print("\n  (b) QuickDraw category files present (18 total: 10 background + 8 held-out)")
    missing = [c for c in pw.QD_CATEGORIES if not os.path.exists(pw.QD_FILES[c])]
    for c in pw.QD_CATEGORIES:
        tag = "background" if c in pw.QD_CATEGORIES_BACKGROUND else "held-out"
        valid = pw.probe_category_valid(c)
        print(f"      {c:10s} [{tag:10s}]  present={os.path.exists(pw.QD_FILES[c])}  "
              f"valid_category_name={valid}")
    ok_b = len(missing) == 0
    print(f"      -> {'PASS' if ok_b else 'FAIL'} (missing={missing})")
    ok_all &= ok_b

    print("\n  (c) uci_class_split leakage check (real data)")
    learn, heldout = pw.uci_class_split(samples, train_frac=UCI_TRAIN_FRAC, seed=UCI_SPLIT_SEED)
    learn_keys = {s["idx"] for s in learn}
    heldout_keys = {s["idx"] for s in heldout}
    ok_c = learn_keys.isdisjoint(heldout_keys) and len(learn) + len(heldout) == len(samples)
    print(f"      n_learn={len(learn)}  n_heldout={len(heldout)}  disjoint={learn_keys.isdisjoint(heldout_keys)}")
    print(f"      -> {'PASS' if ok_c else 'FAIL'}")
    ok_all &= ok_c

    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}"
          f"\n{SEP}")
    _save_json({"ok_all": ok_all, "stroke_shapes_md5_before": md5_before}, _ckpt("unit_sanity.json"))
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0 if ok_all else 1


# ============================================================================================= #
#  STAGE: device_split (extended 18-category)
# ============================================================================================= #
def stage_device_split():
    print(f"\n{SEP}\n  STAGE: device_split (QuickDraw mouse vs touch, 18 categories)\n{SEP}")
    t0 = time.time()
    per_cat = {}
    pooled_fracs = []
    for cat in pw.QD_CATEGORIES:
        draws, n_bad = pw.load_quickdraw_drawings(pw.QD_FILES[cat], limit=QD_LOAD_CAP_PER_CAT)
        fracs = [pw.pooled_integer_delta_fraction(d["strokes_xy"]) for d in draws]
        per_cat[cat] = fracs
        pooled_fracs.extend(fracs)
        print(f"  loaded {cat:10s} n={len(draws):4d}  n_bad_lines={n_bad}  "
              f"mean_frac={np.mean(fracs):.3f}", flush=True)

    split = pw.find_split_threshold(pooled_fracs)
    thresh = split["threshold"]
    print(f"\n  chosen threshold = {thresh:.4f}  (method={split['method']})")

    report = {"threshold": thresh, "threshold_method": split["method"], "per_category": {}}
    n_touch_total = n_mouse_total = 0
    for cat in pw.QD_CATEGORIES:
        fracs = np.asarray(per_cat[cat])
        n_touch = int((fracs < thresh).sum())
        n_mouse = int((fracs >= thresh).sum())
        n = len(fracs)
        lo, hi = wilson_ci(n_touch, n) if n else (0.0, 0.0)
        report["per_category"][cat] = {"n": n, "n_touch": n_touch, "n_mouse": n_mouse,
                                       "touch_frac": (n_touch / n) if n else 0.0,
                                       "touch_frac_wilson_ci": [lo, hi]}
        n_touch_total += n_touch
        n_mouse_total += n_mouse
        print(f"  {cat:10s} n={n:4d}  touch={n_touch:4d} ({100*n_touch/max(1,n):.1f}%)  mouse={n_mouse:4d}")

    n_pooled = n_touch_total + n_mouse_total
    lo_p, hi_p = wilson_ci(n_touch_total, n_pooled)
    report["pooled"] = {"n": n_pooled, "n_touch": n_touch_total, "n_mouse": n_mouse_total,
                        "touch_frac": n_touch_total / max(1, n_pooled),
                        "touch_frac_wilson_ci": [lo_p, hi_p]}
    print(f"\n  POOLED (18 cats): n={n_pooled}  touch={n_touch_total} "
          f"({100*n_touch_total/max(1,n_pooled):.1f}%, 95% CI [{100*lo_p:.1f},{100*hi_p:.1f}])")

    _save_json(report, _ckpt("device_split.json"))
    print(f"\n  saved -> {_ckpt('device_split.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [device_split wall time: {time.time()-t0:.1f}s]")
    return 0


def _load_device_split() -> dict:
    path = _ckpt("device_split.json")
    if not os.path.exists(path):
        raise SystemExit("WALL: run --stage device_split first.")
    return _load_json(path)


# ============================================================================================= #
#  SHARED: adaptive-edge fit (LEARN) + frozen-edge tokenization (held-out), moved here from
#  run 46's `_tokenize_population`, SPLIT into a fit phase and a freeze-and-apply phase.
# ============================================================================================= #
def fit_edges_on_learn(stroke_points: list) -> dict:
    """`stroke_points`: list of raw `[[x,y],...]` point-lists. Fits BOTH the adaptive
    turn/length edges (`adaptive_bins.compute_adaptive_edges`) AND the ramp-delta edges
    (`stroke_programs.gather_delta_edges`, phase-1 tokenize with `delta_edges=None`) on this
    population ONLY -- the LEARN split. Returns the frozen edge set + tol_deg."""
    agent = srs.Substrate()
    learn_values = ab.gather_learn_span_values(agent, stroke_points, segments=DK["segments"],
                                               max_knots=DK["max_knots"])
    edges_report = ab.compute_adaptive_edges(learn_values, turn_bins=DK["turn_bins"],
                                             len_bins=DK["len_bins"])
    level_edges = edges_report["turn_edges"]
    len_edges = edges_report["len_edges"]
    tol_deg = sp.tol_deg_from_edges(level_edges)

    pooled_deltas = []
    n_degenerate = 0
    for points in stroke_points:
        s = srs.Substrate()
        turn_seq = sp.stroke_turn_sequence(s, points, segments=DK["segments"],
                                           max_knots=DK["max_knots"])
        if not turn_seq:
            n_degenerate += 1
            continue
        res = sp.tokenize_turn_sequence(turn_seq, tol_deg, level_edges, delta_edges=None)
        pooled_deltas.extend(res["raw_deltas"])
    delta_edges = sp.gather_delta_edges(pooled_deltas)

    return {"level_edges": level_edges, "len_edges": len_edges, "delta_edges": delta_edges,
           "tol_deg": tol_deg, "edges_report": edges_report, "n_learn_strokes": len(stroke_points),
           "n_degenerate_learn": n_degenerate}


def tokenize_with_frozen_edges(stroke_points: list, frozen: dict) -> tuple:
    """`stroke_points`: list of `(points, tag)`. Applies the FROZEN LEARN edges (no fitting) --
    returns `(records, n_degenerate)` where `records` = list of `(fine, coarse, tag)`."""
    level_edges, delta_edges, tol_deg = frozen["level_edges"], frozen["delta_edges"], frozen["tol_deg"]
    records = []
    n_degenerate = 0
    for (points, tag) in stroke_points:
        s = srs.Substrate()
        turn_seq = sp.stroke_turn_sequence(s, points, segments=DK["segments"],
                                           max_knots=DK["max_knots"])
        if not turn_seq:
            n_degenerate += 1
            records.append(("∅", "∅", tag))
            continue
        res = sp.tokenize_turn_sequence(turn_seq, tol_deg, level_edges, delta_edges=delta_edges)
        records.append((res["fine"], res["coarse"], tag))
    return records, n_degenerate


def _entropy_block(idents: list) -> dict:
    non_degenerate = [i for i in idents if i != "∅"]
    rep = ab.entropy_report(non_degenerate)
    rep["n_degenerate"] = len(idents) - len(non_degenerate)
    return rep


def _match_fraction(groups: list) -> tuple:
    matched, total = 0, 0
    for members in groups:
        n = len(members)
        for i in range(n):
            for j in range(i + 1, n):
                total += 1
                if members[i] == members[j]:
                    matched += 1
    return matched, total


def _p1c_block(class_members: dict, rng: np.random.Generator, n_reps: int = P1C_NULL_REPS) -> dict:
    """Verbatim (semantics) from run 46's own `_p1c_block`."""
    groups = list(class_members.values())
    sizes = [len(g) for g in groups]
    matched, total = _match_fraction(groups)
    raw = (matched / total) if total else 0.0
    flat = [m for g in groups for m in g]
    null_fracs = []
    for _ in range(n_reps):
        perm = rng.permutation(flat).tolist()
        idx = 0
        shuffled = []
        for sz in sizes:
            shuffled.append(perm[idx:idx + sz])
            idx += sz
        m, t = _match_fraction(shuffled)
        if t:
            null_fracs.append(m / t)
    null_mean = float(np.mean(null_fracs)) if null_fracs else 0.0
    excess = raw - null_mean
    mult = (raw / null_mean) if null_mean > 0 else None
    bar = (BAR_EXCESS_FACTOR * null_mean) if null_mean > 0 else 0.0
    clears_bar = bool(excess > 0) if null_mean <= 0 else bool(raw >= bar)
    return {"n_classes": len(groups), "n_pairs": total, "n_matched": matched, "raw_fraction": raw,
           "null_mean": null_mean, "excess": excess, "mult_vs_null": mult, "bar": bar,
           "excess_clears_bar": clears_bar}


# ============================================================================================= #
#  LEARN + CODEBOOK GROWTH (the "standard multi-grain codebook growth" per this run's brief) --
#  a fresh in-memory boot_core() substrate, ink.decode_ink loop, growth-curve windows -- the
#  SAME machinery `jabberwock_omniglot_dynamic_quantization.py::run_learn` drives.
# ============================================================================================= #
def _boot_fresh():
    from substrate.boot_core import boot_core
    s, ag = boot_core()
    return s, ag


def run_codebook_growth(stroke_sources: list, edges: dict, *, window: int = GROWTH_WINDOW) -> dict:
    """`stroke_sources`: list of raw `[[x,y],...]` point-lists (one pen-down stroke each).
    Fresh `boot_core()` substrate for the GRAPH state. SEED-WRITE ISOLATION (post-hoc fix,
    documented honestly in this run's own final report): `boot_core()` NOT loading the
    "stroke_shapes" seed only means growth starts from an EMPTY codebook -- it does NOT mean
    `stroke_codebook.grow_stroke_quantum`'s internal `teach()` calls stay in memory. `teach()`
    PERSISTS every newly-minted quantum to `seeds/<category>.json` on disk by default (the SAME
    mechanism every `tests/test_*_migrated.py` file's own `_isolate_seed_writes` fixture exists
    to neutralize) -- an incident this run's first pass through `learn_uci`/`learn_quickdraw`
    hit for real (see the final report's honest-anomalies section). This wrapper monkeypatches
    `domains.stroke_codebook.teach` for the DURATION of one growth call, redirecting
    `seeds_dir` to a throwaway temp directory, then restores the original binding --
    `seeds/stroke_shapes.json` is provably untouched by any call made AFTER this fix (verified
    by the run's own md5 checkpoint)."""
    import shutil
    import tempfile
    from domains.teach import teach as _real_teach

    tmp_seeds_dir = tempfile.mkdtemp(prefix="run47_seed_isolation_")
    _orig_teach = sc.teach
    sc.teach = lambda *a, **k: _real_teach(*a, **{**k, "seeds_dir": tmp_seeds_dir})
    try:
        s, ag = _boot_fresh()
        turn_edges, len_edges = edges["level_edges"], edges["len_edges"]
        growth = []
        n_strokes = n_degenerate_skipped = 0
        win_recognized = win_oov = win_minted = win_codebook_start = 0
        t_start = time.time()
        for points in stroke_sources:
            pts = np.asarray(points, dtype=float)
            if pts.shape[0] < 2:
                n_degenerate_skipped += 1
                continue
            ink_node = ink.ingest_ink(s, pts.tolist(), writer="learn", max_knots=DK["max_knots"])
            res = ink.decode_ink(s, ink_node, writer="learn", min_span=DK["min_span"],
                                 max_span=DK["max_span"], segments=DK["segments"],
                                 turn_bins=DK["turn_bins"], len_bins=DK["len_bins"],
                                 grid=DK["grid"], scale_bins=DK["scale_bins"],
                                 enable_substroke=False, turn_edges=turn_edges, len_edges=len_edges)
            n_strokes += 1
            win_recognized += len(res["recognized"])
            win_oov += len(res["oov"])
            win_minted += len(res["minted"])
            if n_strokes % window == 0:
                cb = len(sc._existing_names(s, "stroke"))
                reuse_rate = win_recognized / max(1, win_recognized + win_oov)
                growth.append({"n": n_strokes, "codebook": cb, "new_quanta": cb - win_codebook_start,
                               "recognized": win_recognized, "oov": win_oov, "minted": win_minted,
                               "reuse_rate": reuse_rate, "elapsed": time.time() - t_start})
                win_codebook_start = cb
                win_recognized = win_oov = win_minted = 0
        final_codebook = len(sc._existing_names(s, "stroke"))
        return {"growth": growth, "n_strokes": n_strokes, "n_degenerate_skipped": n_degenerate_skipped,
               "final_codebook": final_codebook, "elapsed": time.time() - t_start}
    finally:
        sc.teach = _orig_teach
        shutil.rmtree(tmp_seeds_dir, ignore_errors=True)


def _saturation_verdict(growth: list) -> "bool | None":
    if len(growth) < 6:
        return None
    first = np.mean([g["new_quanta"] for g in growth[:3]])
    last = np.mean([g["new_quanta"] for g in growth[-3:]])
    reuse_first = np.mean([g["reuse_rate"] for g in growth[:3]])
    reuse_last = np.mean([g["reuse_rate"] for g in growth[-3:]])
    return bool(last <= max(3.0, 0.3 * first) and reuse_last >= reuse_first)


def _print_growth(growth: list) -> None:
    print(f"  {'strokes':>8}  {'codebook':>8}  {'+new/win':>9}  {'recognized':>10}  "
         f"{'oov':>6}  {'minted':>7}  {'reuse%':>7}  {'elapsed':>8}")
    for row in growth:
        print(f"  {row['n']:>8}  {row['codebook']:>8}  {row['new_quanta']:>9}  "
             f"{row['recognized']:>10}  {row['oov']:>6}  {row['minted']:>7}  "
             f"{100*row['reuse_rate']:>6.1f}%  {row['elapsed']:>7.1f}s")


# ============================================================================================= #
#  STAGE: learn_uci
# ============================================================================================= #
def stage_learn_uci():
    print(f"\n{SEP}\n  STAGE: learn_uci (adaptive edges + codebook growth, UCI pen LEARN split)\n{SEP}")
    t0 = time.time()
    samples = pw.load_uci_samples()
    learn, heldout = pw.uci_class_split(samples, train_frac=UCI_TRAIN_FRAC, seed=UCI_SPLIT_SEED)
    print(f"  n_learn={len(learn)}  n_heldout={len(heldout)}  (per-class {UCI_TRAIN_FRAC:.0%} train)")

    learn_points = [s["pos_xy"].tolist() for s in learn]
    frozen = fit_edges_on_learn(learn_points)
    print(f"\n  turn_edges ({len(frozen['level_edges'])-1} eff bins): "
         f"{[round(v,2) for v in frozen['level_edges']]}")
    print(f"  len_edges  ({len(frozen['len_edges'])-1} eff bins): "
         f"{[round(v,2) for v in frozen['len_edges']]}")
    print(f"  delta_edges ({len(frozen['delta_edges'])-1} eff bins): "
         f"{[round(v,2) for v in frozen['delta_edges']]}")
    print(f"  tol_deg={frozen['tol_deg']:.4f}  n_degenerate_learn={frozen['n_degenerate_learn']}")
    print(f"\n  MOUSEWRITING CONTRAST: run-28's uniform bins collapsed 10,230/10,231 real LEARN "
         f"spans into ONE family (dead length dim + point-mass turn dim). Pen-data occupancy "
         f"entropy: turn={frozen['edges_report']['turn_occupancy']['entropy_bits']:.3f} bits "
         f"(max {frozen['edges_report']['turn_occupancy']['max_entropy_bits']:.3f}), "
         f"len={frozen['edges_report']['len_occupancy']['entropy_bits']:.3f} bits "
         f"(max {frozen['edges_report']['len_occupancy']['max_entropy_bits']:.3f}).")

    print(f"\n  codebook growth (fresh boot_core(), {len(learn_points)} LEARN strokes)...")
    lr = run_codebook_growth(learn_points, frozen, window=GROWTH_WINDOW)
    _print_growth(lr["growth"])
    sat = _saturation_verdict(lr["growth"])
    print(f"\n  final codebook size: {lr['final_codebook']}  "
         f"(fragmentation cap {SATURATION_FRAGMENT_CAP})")
    print(f"  SATURATION VERDICT: {'PASS (flattens)' if sat else ('FAIL (no flattening)' if sat is False else 'INCONCLUSIVE (too few windows)')}")
    fragmentation_stop = lr["final_codebook"] > SATURATION_FRAGMENT_CAP and sat is not True
    if fragmentation_stop:
        print(f"  FRAGMENTATION-CLAUSE STOP: codebook exceeded {SATURATION_FRAGMENT_CAP} without "
             f"flattening -- reporting honest non-saturation, per run-32's transplanted clause.")

    out = {"n_learn": len(learn), "n_heldout": len(heldout), "level_edges": frozen["level_edges"],
          "len_edges": frozen["len_edges"], "delta_edges": frozen["delta_edges"],
          "tol_deg": frozen["tol_deg"], "edges_report": frozen["edges_report"],
          "n_degenerate_learn": frozen["n_degenerate_learn"], "growth": lr["growth"],
          "final_codebook": lr["final_codebook"], "n_strokes": lr["n_strokes"],
          "saturation_pass": sat, "fragmentation_stop": bool(fragmentation_stop),
          "heldout_idx": [list(s["idx"]) if isinstance(s["idx"], tuple) else s["idx"] for s in heldout],
          "learn_idx": [list(s["idx"]) if isinstance(s["idx"], tuple) else s["idx"] for s in learn]}
    _save_json(out, _ckpt("learn_uci.json"))
    print(f"\n  saved -> {_ckpt('learn_uci.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [learn_uci wall time: {time.time()-t0:.1f}s]")
    return 0


# ============================================================================================= #
#  STAGE: learn_quickdraw
# ============================================================================================= #
def _gather_qd_touch(categories: list, threshold: float, cap: int) -> dict:
    out = {}
    for cat in categories:
        touch, mouse, n_bad = pw.stream_quickdraw_touch(pw.QD_FILES[cat], threshold, cap=cap,
                                                         raw_cap=QD_SPLIT_RAW_CAP)
        out[cat] = touch
        print(f"  {cat:10s} touch={len(touch):4d}  mouse={len(mouse):4d}  n_bad={n_bad}", flush=True)
    return out


def stage_learn_quickdraw():
    print(f"\n{SEP}\n  STAGE: learn_quickdraw (adaptive edges + codebook growth, QuickDraw "
         f"touch LEARN=background categories)\n{SEP}")
    t0 = time.time()
    ds = _load_device_split()
    thresh = ds["threshold"]
    print(f"  device threshold={thresh:.4f}  background categories={pw.QD_CATEGORIES_BACKGROUND}")

    per_cat_touch = _gather_qd_touch(pw.QD_CATEGORIES_BACKGROUND, thresh, QD_TOUCH_CAP_PER_CAT)

    learn_points = []
    for cat, draws in per_cat_touch.items():
        for d in draws:
            for st in d["strokes_xy"][:MAX_STROKES]:
                if st.shape[0] >= 2:
                    learn_points.append(st.tolist())
    print(f"\n  n_learn_strokes (pooled across {len(pw.QD_CATEGORIES_BACKGROUND)} background "
         f"categories) = {len(learn_points)}")

    frozen = fit_edges_on_learn(learn_points)
    print(f"\n  turn_edges ({len(frozen['level_edges'])-1} eff bins): "
         f"{[round(v,2) for v in frozen['level_edges']]}")
    print(f"  len_edges  ({len(frozen['len_edges'])-1} eff bins): "
         f"{[round(v,2) for v in frozen['len_edges']]}")
    print(f"  tol_deg={frozen['tol_deg']:.4f}")

    # CODEBOOK GROWTH runs on a CAPPED round-robin subset (see QD_LEARN_STROKE_CAP's own
    # comment) -- the adaptive-edge fit above already used the FULL pooled population; only
    # the much heavier decode_ink loop is capped, per this run's own live timing measurement.
    cap_per_cat = max(1, QD_LEARN_STROKE_CAP // len(pw.QD_CATEGORIES_BACKGROUND))
    growth_points = []
    for cat, draws in per_cat_touch.items():
        n_taken = 0
        for d in draws:
            for st in d["strokes_xy"][:MAX_STROKES]:
                if st.shape[0] < 2:
                    continue
                growth_points.append(st.tolist())
                n_taken += 1
                if n_taken >= cap_per_cat:
                    break
            if n_taken >= cap_per_cat:
                break
    print(f"\n  codebook growth (fresh boot_core(), {len(growth_points)} LEARN strokes, "
         f"capped round-robin at {cap_per_cat}/category of {len(learn_points)} pooled)...")
    lr = run_codebook_growth(growth_points, frozen, window=GROWTH_WINDOW)
    _print_growth(lr["growth"])
    sat = _saturation_verdict(lr["growth"])
    print(f"\n  final codebook size: {lr['final_codebook']}")
    print(f"  SATURATION VERDICT: {'PASS (flattens)' if sat else ('FAIL (no flattening)' if sat is False else 'INCONCLUSIVE (too few windows)')}")
    fragmentation_stop = lr["final_codebook"] > SATURATION_FRAGMENT_CAP and sat is not True
    if fragmentation_stop:
        print(f"  FRAGMENTATION-CLAUSE STOP: codebook exceeded {SATURATION_FRAGMENT_CAP} without "
             f"flattening.")

    out = {"n_learn_strokes": len(learn_points), "level_edges": frozen["level_edges"],
          "len_edges": frozen["len_edges"], "delta_edges": frozen["delta_edges"],
          "tol_deg": frozen["tol_deg"], "edges_report": frozen["edges_report"],
          "growth": lr["growth"], "final_codebook": lr["final_codebook"],
          "n_strokes": lr["n_strokes"], "saturation_pass": sat,
          "fragmentation_stop": bool(fragmentation_stop), "threshold": thresh}
    _save_json(out, _ckpt("learn_quickdraw.json"))
    print(f"\n  saved -> {_ckpt('learn_quickdraw.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [learn_quickdraw wall time: {time.time()-t0:.1f}s]")
    return 0


def _load_learn(name: str) -> dict:
    path = _ckpt(name)
    if not os.path.exists(path):
        raise SystemExit(f"WALL: run the corresponding learn stage first ({name} missing).")
    return _load_json(path)


# ============================================================================================= #
#  GATE A -- QUANTIZATION RETENTION.
# ============================================================================================= #
def stage_gate_a_uci():
    print(f"\n{SEP}\n  STAGE: gate_a_uci (quantization retention, FROZEN LEARN edges -> held-out)\n{SEP}")
    t0 = time.time()
    learn_report = _load_learn("learn_uci.json")
    samples = pw.load_uci_samples()
    heldout_idx = {tuple(x) if isinstance(x, list) else x for x in learn_report["heldout_idx"]}
    heldout = [s for s in samples if s["idx"] in heldout_idx]
    print(f"  n_heldout={len(heldout)} (0 contact with the edge fit)")

    stroke_points = [(s["pos_xy"].tolist(), s["class"]) for s in heldout]
    records, n_degenerate = tokenize_with_frozen_edges(stroke_points, learn_report)
    print(f"  n_degenerate={n_degenerate}")

    fine_idents = [r[0] for r in records]
    p3_fine = _entropy_block(fine_idents)
    print(f"\n  ENTROPY fine (held-out): {p3_fine['entropy_bits']:.4f} bits  "
         f"n_ids={p3_fine['n_families']}")

    class_members_fine: dict = {}
    class_members_coarse: dict = {}
    for (fine, coarse, cls) in records:
        class_members_fine.setdefault(cls, []).append(fine)
        class_members_coarse.setdefault(cls, []).append(coarse)
    rng_fine = np.random.default_rng(RNG_SEED + 30)
    rng_coarse = np.random.default_rng(RNG_SEED + 31)
    p1c_fine = _p1c_block(class_members_fine, rng_fine)
    p1c_coarse = _p1c_block(class_members_coarse, rng_coarse)
    print(f"\n  HELD-OUT CONSISTENCY fine:   raw={p1c_fine['raw_fraction']:.5f} "
         f"null={p1c_fine['null_mean']:.5f}  mult={_f(p1c_fine['mult_vs_null'],'.2f')}x  "
         f"clears_{BAR_EXCESS_FACTOR}x={p1c_fine['excess_clears_bar']}")
    print(f"  HELD-OUT CONSISTENCY coarse: raw={p1c_coarse['raw_fraction']:.5f} "
         f"null={p1c_coarse['null_mean']:.5f}  mult={_f(p1c_coarse['mult_vs_null'],'.2f')}x  "
         f"clears_{BAR_EXCESS_FACTOR}x={p1c_coarse['excess_clears_bar']}")
    print(f"\n  RUN-46 SAME-POPULATION CITATION (edges fit on the SAME data measured): "
         f"{RUN46_UCI_RAW_MULT}x")
    gate_a_pass = p1c_fine["excess_clears_bar"] or p1c_coarse["excess_clears_bar"]
    print(f"  GATE A-UCI (>=2x null on GENERALIZED held-out strokes, either grain): "
         f"{'PASS' if gate_a_pass else 'FAIL'}")

    out = {"n_heldout": len(heldout), "n_degenerate": n_degenerate,
          "p3_entropy_fine": p3_fine, "p1c_fine": p1c_fine, "p1c_coarse": p1c_coarse,
          "run46_raw_citation_mult": RUN46_UCI_RAW_MULT, "gate_a_pass": bool(gate_a_pass)}
    _save_json(out, _ckpt("gate_a_uci.json"))
    print(f"\n  saved -> {_ckpt('gate_a_uci.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [gate_a_uci wall time: {time.time()-t0:.1f}s]")
    return 0


def stage_gate_a_quickdraw():
    print(f"\n{SEP}\n  STAGE: gate_a_quickdraw (quantization retention, FROZEN background-LEARN "
         f"edges -> held-out categories)\n{SEP}")
    t0 = time.time()
    learn_report = _load_learn("learn_quickdraw.json")
    ds = _load_device_split()
    thresh = ds["threshold"]

    per_cat_touch = _gather_qd_touch(pw.QD_CATEGORIES_HELDOUT, thresh, QD_TOUCH_CAP_PER_CAT)
    stroke_points = []
    for cat, draws in per_cat_touch.items():
        for d in draws:
            for st in d["strokes_xy"][:MAX_STROKES]:
                if st.shape[0] >= 2:
                    stroke_points.append((st.tolist(), cat))
    print(f"\n  n_heldout_strokes (8 held-out categories, ZERO contact with the LEARN edge fit) "
         f"= {len(stroke_points)}")

    records, n_degenerate = tokenize_with_frozen_edges(stroke_points, learn_report)
    print(f"  n_degenerate={n_degenerate}")

    fine_idents = [r[0] for r in records]
    p3_fine = _entropy_block(fine_idents)
    print(f"\n  ENTROPY fine (held-out categories): {p3_fine['entropy_bits']:.4f} bits  "
         f"n_ids={p3_fine['n_families']}")

    class_members_fine: dict = {}
    class_members_coarse: dict = {}
    for (fine, coarse, cat) in records:
        class_members_fine.setdefault(cat, []).append(fine)
        class_members_coarse.setdefault(cat, []).append(coarse)
    rng_fine = np.random.default_rng(RNG_SEED + 40)
    rng_coarse = np.random.default_rng(RNG_SEED + 41)
    p1c_fine = _p1c_block(class_members_fine, rng_fine)
    p1c_coarse = _p1c_block(class_members_coarse, rng_coarse)
    print(f"\n  HELD-OUT-CATEGORY CONSISTENCY fine:   raw={p1c_fine['raw_fraction']:.5f} "
         f"null={p1c_fine['null_mean']:.5f}  mult={_f(p1c_fine['mult_vs_null'],'.2f')}x  "
         f"clears_{BAR_EXCESS_FACTOR}x={p1c_fine['excess_clears_bar']}")
    print(f"  HELD-OUT-CATEGORY CONSISTENCY coarse: raw={p1c_coarse['raw_fraction']:.5f} "
         f"null={p1c_coarse['null_mean']:.5f}  mult={_f(p1c_coarse['mult_vs_null'],'.2f')}x  "
         f"clears_{BAR_EXCESS_FACTOR}x={p1c_coarse['excess_clears_bar']}")
    print(f"\n  RUN-46 SAME-POPULATION CITATION (6 cats, edges fit on the SAME data measured): "
         f"{RUN46_QD_RAW_MULT}x")
    gate_a_pass = p1c_fine["excess_clears_bar"] or p1c_coarse["excess_clears_bar"]
    print(f"  GATE A-QuickDraw (>=2x null on GENERALIZED held-out CATEGORIES, either grain): "
         f"{'PASS' if gate_a_pass else 'FAIL'}")

    out = {"n_heldout_strokes": len(stroke_points), "n_degenerate": n_degenerate,
          "p3_entropy_fine": p3_fine, "p1c_fine": p1c_fine, "p1c_coarse": p1c_coarse,
          "run46_raw_citation_mult": RUN46_QD_RAW_MULT, "gate_a_pass": bool(gate_a_pass)}
    _save_json(out, _ckpt("gate_a_quickdraw.json"))
    print(f"\n  saved -> {_ckpt('gate_a_quickdraw.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [gate_a_quickdraw wall time: {time.time()-t0:.1f}s]")
    return 0


# ============================================================================================= #
#  GATE B -- END-TO-END ONE-SHOT, three arms.
# ============================================================================================= #
def _stroke_point_sets_from_arrays(strokes_xy: list, *, N: int = POINTSET_N,
                                   max_strokes: int = MAX_STROKES) -> list:
    """Mechanical adapter twin of `domains.per_stroke_abs.stroke_point_sets` -- SAME whole-
    drawing normalization + per-stroke arc-length resample, taking already-loaded stroke arrays
    directly (no Omniglot file path). Reused geometry, new I/O only."""
    arrs = [np.asarray(s, float) for s in strokes_xy if len(s)]
    if not arrs:
        return []
    allp = np.concatenate(arrs, 0)
    if len(allp) < 3:
        return []
    mn = allp.mean(0)
    scale = np.abs(allp - mn).max() + 1e-9
    out = []
    for a0 in arrs[:max_strokes]:
        a = (a0 - mn) / scale
        if len(a) < 2:
            continue
        d = np.sqrt((np.diff(a, axis=0) ** 2).sum(1))
        cum = np.concatenate([[0.0], np.cumsum(d)])
        if cum[-1] == 0:
            continue
        u = np.linspace(0.0, cum[-1], N)
        out.append(np.stack([np.interp(u, cum, a[:, 0]), np.interp(u, cum, a[:, 1])], 1).tolist())
    return out


def _ident_bags(strokes_xy: list, frozen: dict) -> tuple:
    """Per-drawing quantized identity, BOTH grains (multiset, as sorted tuples) -- one fine +
    one coarse token string per pen-down stroke (capped at MAX_STROKES, matching the geometric
    verdict's own cap), via the FROZEN LEARN edges. MID-RUN CORRECTION (found via this stage's
    own diagnostics, see run report): fine-grain tokens are too SPECIFIC for a bag-overlap
    shortlist on their own -- Gate A's own raw exact-match fraction is only ~1-3% even for
    same-class pairs (it is still >>null, but rare in absolute terms), so an all-fine
    similarity collapses to near-total ties across candidates and a naive stable sort then
    silently falls back to INSERTION ORDER (alphabetical class order) -- exactly reproducing
    chance-level shortlist coverage while looking like a real ranking. Both grains are now
    carried so the caller can combine them (coarse's much higher raw match rate, per Gate A,
    gives real tie-breaking resolution) and ties are broken with an explicit RNG jitter, never
    silently by insertion order."""
    pts_list = [(s.tolist() if hasattr(s, "tolist") else s) for s in strokes_xy[:MAX_STROKES]]
    tagged = [(p, 0) for p in pts_list if len(p) >= 2]
    records, _ = tokenize_with_frozen_edges(tagged, frozen)
    fine = tuple(sorted(r[0] for r in records))
    coarse = tuple(sorted(r[1] for r in records))
    return fine, coarse


def _bag_overlap(a: tuple, b: tuple) -> float:
    """Normalized multiset-overlap similarity: |intersection| / max(|a|,|b|,1)."""
    from collections import Counter
    ca, cb = Counter(a), Counter(b)
    inter = sum((ca & cb).values())
    return inter / max(len(a), len(b), 1)


COARSE_SIM_WEIGHT = 0.5   # combined similarity = fine_overlap + COARSE_SIM_WEIGHT*coarse_overlap
                          # -- coarse's much higher raw base rate (Gate A) gives real
                          # resolution; fine still dominates when it DOES match exactly.


def _combined_similarity(q_bags: tuple, c_bags: tuple) -> float:
    q_fine, q_coarse = q_bags
    c_fine, c_coarse = c_bags
    return _bag_overlap(q_fine, c_fine) + COARSE_SIM_WEIGHT * _bag_overlap(q_coarse, c_coarse)


def _run_one_shot_episode(query_strokes: list, candidate_strokes: list, candidate_bags: list,
                          query_bag: tuple, true_idx: int, shortlist_k: int,
                          tie_rng: np.random.Generator) -> dict:
    """One episode's worth of all three arms. `candidate_strokes`: list of stroke-array lists,
    one per candidate/class (N candidates). Returns per-arm predicted index + shortlist info.
    Ties in the quantized similarity are broken by an explicit RNG jitter (`tie_rng`), never by
    Python's stable-sort insertion order (see `_ident_bags`'s own docstring for why that silent
    fallback is a real artifact, not a theoretical concern)."""
    q_ps = _stroke_point_sets_from_arrays(query_strokes)
    cand_ps = [_stroke_point_sets_from_arrays(cs) for cs in candidate_strokes]
    # ONE geometric pass -- SAME per_stroke_abs.program_score the arc already established.
    geo_scores = [ps.program_score(q_ps, cps) for cps in cand_ps]
    pred_i = int(np.argmin(geo_scores))          # ARM (i): CONTINUOUS-ONLY baseline.

    sims = [_combined_similarity(query_bag, cb) for cb in candidate_bags]
    jitter = tie_rng.uniform(0.0, 1e-6, size=len(sims))
    order = sorted(range(len(sims)), key=lambda i: -(sims[i] + jitter[i]))
    shortlist = set(order[:shortlist_k])
    in_shortlist = true_idx in shortlist
    # ARM (ii): argmin geo_scores RESTRICTED to the shortlist (reuses the SAME geo_scores).
    pred_ii = min(shortlist, key=lambda i: geo_scores[i])
    pred_iii = int(order[0])                       # ARM (iii): QUANTIZED-ONLY, jittered argmax.

    return dict(pred_i=pred_i, pred_ii=pred_ii, pred_iii=pred_iii,
               correct_i=(pred_i == true_idx), correct_ii=(pred_ii == true_idx),
               correct_iii=(pred_iii == true_idx), in_shortlist=in_shortlist)


def _gate_b_report(records: list, n: int, shortlist_k: int, n_way: int) -> dict:
    ci = records
    acc_i = sum(r["correct_i"] for r in ci) / n
    acc_ii = sum(r["correct_ii"] for r in ci) / n
    acc_iii = sum(r["correct_iii"] for r in ci) / n
    ci_i = wilson_ci(sum(r["correct_i"] for r in ci), n)
    ci_ii = wilson_ci(sum(r["correct_ii"] for r in ci), n)
    ci_iii = wilson_ci(sum(r["correct_iii"] for r in ci), n)
    coverage = sum(r["in_shortlist"] for r in ci) / n
    mc = _mcnemar([r["correct_i"] for r in ci], [r["correct_ii"] for r in ci])
    stop = mc["broken"] >= mc["fixed"]
    return dict(n=n, n_way=n_way, shortlist_k=shortlist_k,
               acc_continuous_only=acc_i, ci_continuous_only=list(ci_i),
               acc_quantized_proposal=acc_ii, ci_quantized_proposal=list(ci_ii),
               acc_quantized_only=acc_iii, ci_quantized_only=list(ci_iii),
               shortlist_coverage=coverage, mcnemar_ii_vs_i=mc,
               stop_union_harms=bool(stop))


def stage_gate_b_uci():
    print(f"\n{SEP}\n  STAGE: gate_b_uci (one-shot 20-way, WITHIN-WRITER per UCI CAVEAT, "
         f"held-out only)\n{SEP}")
    t0 = time.time()
    learn_report = _load_learn("learn_uci.json")
    samples = pw.load_uci_samples()
    heldout_idx = {tuple(x) if isinstance(x, list) else x for x in learn_report["heldout_idx"]}
    heldout = [s for s in samples if s["idx"] in heldout_idx]
    by_class: dict = {}
    for s in heldout:
        by_class.setdefault(s["class"], []).append(s)
    classes = sorted(by_class.keys())
    n_way = len(classes)
    print(f"  n_way={n_way}  classes={classes}  n_heldout={len(heldout)}")
    for c in classes:
        assert len(by_class[c]) >= 2, f"class {c} needs >=2 held-out samples for exemplar+query"

    rng = np.random.default_rng(RNG_SEED + 50)
    records = []
    t_batch = time.time()
    for ep in range(GATE_B_N_EPISODES):
        true_cls = classes[int(rng.integers(0, n_way))]
        exemplar_by_cls = {}
        for c in classes:
            insts = by_class[c]
            exemplar_by_cls[c] = insts[int(rng.integers(0, len(insts)))]
        pool = [s for s in by_class[true_cls] if s["idx"] != exemplar_by_cls[true_cls]["idx"]]
        query = pool[int(rng.integers(0, len(pool)))]

        candidate_strokes = [[exemplar_by_cls[c]["pos_xy"]] for c in classes]
        candidate_bags = [_ident_bags([exemplar_by_cls[c]["pos_xy"]], learn_report) for c in classes]
        true_idx = classes.index(true_cls)
        query_bag = _ident_bags([query["pos_xy"]], learn_report)
        rec = _run_one_shot_episode([query["pos_xy"]], candidate_strokes, candidate_bags,
                                    query_bag, true_idx, GATE_B_UCI_SHORTLIST_K, rng)
        rec["episode"] = ep
        records.append(rec)
        if (ep + 1) % 50 == 0:
            print(f"  ... {ep+1}/{GATE_B_N_EPISODES} episodes  "
                 f"[{time.time()-t_batch:.1f}s for last block]", flush=True)
            t_batch = time.time()

    rep = _gate_b_report(records, GATE_B_N_EPISODES, GATE_B_UCI_SHORTLIST_K, n_way)
    print(f"\n  n={rep['n']}  N-way={rep['n_way']}  shortlist_K={rep['shortlist_k']}")
    print(f"  (i)   CONTINUOUS-ONLY:      acc={100*rep['acc_continuous_only']:.1f}%  "
         f"CI=[{100*rep['ci_continuous_only'][0]:.1f},{100*rep['ci_continuous_only'][1]:.1f}]")
    print(f"  (ii)  QUANTIZED-PROPOSAL:   acc={100*rep['acc_quantized_proposal']:.1f}%  "
         f"CI=[{100*rep['ci_quantized_proposal'][0]:.1f},{100*rep['ci_quantized_proposal'][1]:.1f}]  "
         f"shortlist_coverage={100*rep['shortlist_coverage']:.1f}%")
    print(f"  (iii) QUANTIZED-ONLY:       acc={100*rep['acc_quantized_only']:.1f}%  "
         f"CI=[{100*rep['ci_quantized_only'][0]:.1f},{100*rep['ci_quantized_only'][1]:.1f}]")
    print(f"\n  McNemar (ii) vs (i): fixed={rep['mcnemar_ii_vs_i']['fixed']}  "
         f"broken={rep['mcnemar_ii_vs_i']['broken']}  p={rep['mcnemar_ii_vs_i']['p']:.4f}")
    print(f"  STOP (broken >= fixed, union harms): {rep['stop_union_harms']}")

    _save_json({"report": rep, "records": records}, _ckpt("gate_b_uci.json"))
    print(f"\n  saved -> {_ckpt('gate_b_uci.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [gate_b_uci wall time: {time.time()-t0:.1f}s]")
    return 0


def stage_gate_b_quickdraw():
    print(f"\n{SEP}\n  STAGE: gate_b_quickdraw (one-shot N-way cross-writer, held-out "
         f"categories only)\n{SEP}")
    t0 = time.time()
    learn_report = _load_learn("learn_quickdraw.json")
    ds = _load_device_split()
    thresh = ds["threshold"]
    classes = pw.QD_CATEGORIES_HELDOUT
    n_way = len(classes)
    print(f"  n_way={n_way}  classes={classes}")

    per_cat_touch = _gather_qd_touch(classes, thresh, QD_TOUCH_CAP_PER_CAT)
    for c in classes:
        assert len(per_cat_touch[c]) >= 2, f"category {c} needs >=2 touch drawings"
        print(f"  {c:10s} touch_pool={len(per_cat_touch[c])}")

    rng = np.random.default_rng(RNG_SEED + 60)
    records = []
    t_batch = time.time()
    for ep in range(GATE_B_N_EPISODES):
        true_cls = classes[int(rng.integers(0, n_way))]
        exemplar_by_cls = {}
        for c in classes:
            pool = per_cat_touch[c]
            exemplar_by_cls[c] = pool[int(rng.integers(0, len(pool)))]
        # query: a DIFFERENT record (different key_id -- QuickDraw's raw format carries no
        # persistent user id; "different anonymous users" is operationalized as "a different
        # independently-contributed key_id record", the dataset's own anonymization unit --
        # stated honestly, not a synthetic proxy for a field the corpus doesn't have).
        qpool = [d for d in per_cat_touch[true_cls] if d["key_id"] != exemplar_by_cls[true_cls]["key_id"]]
        query = qpool[int(rng.integers(0, len(qpool)))]

        candidate_strokes = [exemplar_by_cls[c]["strokes_xy"] for c in classes]
        candidate_bags = [_ident_bags(exemplar_by_cls[c]["strokes_xy"], learn_report) for c in classes]
        true_idx = classes.index(true_cls)
        query_bag = _ident_bags(query["strokes_xy"], learn_report)
        rec = _run_one_shot_episode(query["strokes_xy"], candidate_strokes, candidate_bags,
                                    query_bag, true_idx, GATE_B_QD_SHORTLIST_K, rng)
        rec["episode"] = ep
        records.append(rec)
        if (ep + 1) % 50 == 0:
            print(f"  ... {ep+1}/{GATE_B_N_EPISODES} episodes  "
                 f"[{time.time()-t_batch:.1f}s for last block]", flush=True)
            t_batch = time.time()

    rep = _gate_b_report(records, GATE_B_N_EPISODES, GATE_B_QD_SHORTLIST_K, n_way)
    print(f"\n  n={rep['n']}  N-way={rep['n_way']}  shortlist_K={rep['shortlist_k']}")
    print(f"  (i)   CONTINUOUS-ONLY:      acc={100*rep['acc_continuous_only']:.1f}%  "
         f"CI=[{100*rep['ci_continuous_only'][0]:.1f},{100*rep['ci_continuous_only'][1]:.1f}]")
    print(f"  (ii)  QUANTIZED-PROPOSAL:   acc={100*rep['acc_quantized_proposal']:.1f}%  "
         f"CI=[{100*rep['ci_quantized_proposal'][0]:.1f},{100*rep['ci_quantized_proposal'][1]:.1f}]  "
         f"shortlist_coverage={100*rep['shortlist_coverage']:.1f}%")
    print(f"  (iii) QUANTIZED-ONLY:       acc={100*rep['acc_quantized_only']:.1f}%  "
         f"CI=[{100*rep['ci_quantized_only'][0]:.1f},{100*rep['ci_quantized_only'][1]:.1f}]")
    print(f"\n  McNemar (ii) vs (i): fixed={rep['mcnemar_ii_vs_i']['fixed']}  "
         f"broken={rep['mcnemar_ii_vs_i']['broken']}  p={rep['mcnemar_ii_vs_i']['p']:.4f}")
    print(f"  STOP (broken >= fixed, union harms): {rep['stop_union_harms']}")

    _save_json({"report": rep, "records": records}, _ckpt("gate_b_quickdraw.json"))
    print(f"\n  saved -> {_ckpt('gate_b_quickdraw.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [gate_b_quickdraw wall time: {time.time()-t0:.1f}s]")
    return 0


# ============================================================================================= #
#  STAGE: summary
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 47 SCOREBOARD\n{SEP}")
    needed = ["unit_sanity.json", "device_split.json", "learn_uci.json", "learn_quickdraw.json",
             "gate_a_uci.json", "gate_a_quickdraw.json", "gate_b_uci.json", "gate_b_quickdraw.json"]
    missing = [n for n in needed if not os.path.exists(_ckpt(n))]
    if missing:
        print(f"  INCOMPLETE -- missing checkpoints: {missing}")
        return 1
    data = {n: _load_json(_ckpt(n)) for n in needed}

    md5_before = data["unit_sanity.json"]["stroke_shapes_md5_before"]
    md5_after = _md5(STROKE_SHAPES_SEED)
    print(f"\n  seeds/stroke_shapes.json md5: before={md5_before}  after={md5_after}  "
         f"UNCHANGED={md5_before == md5_after}")

    lu, lq = data["learn_uci.json"], data["learn_quickdraw.json"]
    print(f"\n  LEARN SATURATION:")
    print(f"    UCI pen:      final_codebook={lu['final_codebook']}  saturation_pass={lu['saturation_pass']}")
    print(f"    QD touch:     final_codebook={lq['final_codebook']}  saturation_pass={lq['saturation_pass']}")
    print(f"    (mousewriting reference: 5-7 top-level quanta before flattening)")

    gau, gaq = data["gate_a_uci.json"], data["gate_a_quickdraw.json"]
    print(f"\n  GATE A -- QUANTIZATION RETENTION (held-out, frozen LEARN edges):")
    print(f"    UCI:  raw={gau['p1c_fine']['raw_fraction']:.5f}  null={gau['p1c_fine']['null_mean']:.5f}  "
         f"mult={_f(gau['p1c_fine']['mult_vs_null'],'.2f')}x  (run46 same-population citation "
         f"{gau['run46_raw_citation_mult']}x)  PASS={gau['gate_a_pass']}")
    print(f"    QD:   raw={gaq['p1c_fine']['raw_fraction']:.5f}  null={gaq['p1c_fine']['null_mean']:.5f}  "
         f"mult={_f(gaq['p1c_fine']['mult_vs_null'],'.2f')}x  (run46 same-population citation "
         f"{gaq['run46_raw_citation_mult']}x)  PASS={gaq['gate_a_pass']}")

    gbu, gbq = data["gate_b_uci.json"]["report"], data["gate_b_quickdraw.json"]["report"]
    print(f"\n  GATE B -- ONE-SHOT (n={gbu['n']} UCI / n={gbq['n']} QuickDraw):")
    print(f"    UCI  (i) continuous={100*gbu['acc_continuous_only']:.1f}%  "
         f"(ii) quant+cont={100*gbu['acc_quantized_proposal']:.1f}%  "
         f"(iii) quant-only={100*gbu['acc_quantized_only']:.1f}%  "
         f"McNemar p={gbu['mcnemar_ii_vs_i']['p']:.4f}  STOP={gbu['stop_union_harms']}")
    print(f"    QD   (i) continuous={100*gbq['acc_continuous_only']:.1f}%  "
         f"(ii) quant+cont={100*gbq['acc_quantized_proposal']:.1f}%  "
         f"(iii) quant-only={100*gbq['acc_quantized_only']:.1f}%  "
         f"McNemar p={gbq['mcnemar_ii_vs_i']['p']:.4f}  STOP={gbq['stop_union_harms']}")

    print(f"\n{SEP}\n  RUN 47 COMPLETE -- see final agent report for full narrative.\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                  choices=["unit_sanity", "device_split", "learn_uci", "learn_quickdraw",
                          "gate_a_uci", "gate_a_quickdraw", "gate_b_uci", "gate_b_quickdraw",
                          "summary"])
    args = p.parse_args()
    fn = {"unit_sanity": stage_unit_sanity, "device_split": stage_device_split,
         "learn_uci": stage_learn_uci, "learn_quickdraw": stage_learn_quickdraw,
         "gate_a_uci": stage_gate_a_uci, "gate_a_quickdraw": stage_gate_a_quickdraw,
         "gate_b_uci": stage_gate_b_uci, "gate_b_quickdraw": stage_gate_b_quickdraw,
         "summary": stage_summary}[args.stage]
    return fn()


if __name__ == "__main__":
    sys.exit(main())
