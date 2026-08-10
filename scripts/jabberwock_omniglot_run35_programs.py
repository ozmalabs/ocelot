"""OMNIGLOT RUN 35 GATE 0 -- PROGRAM TOKENIZATION: order-N applied WITHIN a single stroke.

THE REFRAME THIS RUN FALSIFIES-OR-LICENSES (creator, 2026-07-05, verbatim): "time is not a
dimension, it is a series of collapses. circles are not circles, they are a 2D view of a
sinusoid, that is itself, stepped." Translation to this codebase: the `seg` relations
(`StrokeQuantize`'s per-segment relative-turn quantum, one independent value per equal-arc-
length step) are ALREADY the phase-step view of a stroke -- but the entire closed 2x2 (runs
32/34c/34d, commits 13ebc282/8323f2a9/cc673ee1) measured those steps as INDEPENDENT
observations, one identity per stroke hashed over the WHOLE per-step vector, with no notion that
a run of steps might be the SAME underlying program token repeated. A circle is not `n`
independent turn-tokens, it is ONE program token: `repeat(turn=k) x n`. A line is `repeat(turn=0)
x n`. A spiral/clothoid is a turn RAMP. A hook is a program change-point. HYPOTHESIS: class-grain
stroke information lives in the STEP PROGRAM (run-length/ramp structure ACROSS steps), which
per-step quantization is provably blind to -- order-N one grain further down than character
composition, and "a different featureset" per the closed map's own demand.

METHOD: see `domains/stroke_programs.py`'s module docstring for the complete, pre-registered
tokenization method (level-run segmentation + ramp promotion + parameter quantization) -- stated
there BEFORE this script computes a single real number against it, cited verbatim here rather
than duplicated:
  - per-segment turn sequence: `stroke_turn_sequence` (denoised, `StrokeQuantize`'s own residual
    read, zero new geometry).
  - PASS 1 level runs: greedy online-mean grouping, tolerance = half the median bin width of
    THIS GATE'S OWN CITED level edges (`results/run34d_checkpoints/edges_report.json`'s
    `turn_edges` -- the SAME denoised, adaptive, deduped-and-guarded edges run 34d already fit
    on the IDENTICAL 1500-stroke LEARN population).
  - PASS 2 ramp promotion: maximal monotonic runs of consecutive ARC entries merge into one
    RAMP token.
  - token parameters: LINE carries a raw step-count length; ARC quantizes its level under the
    cited level edges; RAMP quantizes `k0` under the same level edges and `dk` under a fresh
    quantile/equal-mass delta-edge set fit ONCE over every ramp `dk` this run's own LEARN
    population produces (`domains.adaptive_bins.compute_quantile_edges`, reused verbatim).
  - IDENTITY: fine grain = the full program string (tokens + quantized params); coarse grain =
    token TYPES only.

THIS GATE MINTS NOTHING: pure measurement over the SAME 1500-stroke LEARN population run 34d
used (background[:5], drawers 01-14, DENOISED via `mouse_model.denoise_path_global`, global
mode) -- no `teach()` call, no codebook growth, no seed write anywhere in this script or in
`domains/stroke_programs.py`. Every substrate touch is a throwaway `substrate_rs.Substrate()`
used only to reach the existing `StrokeQuantize` Term's residual read.

PRE-REGISTERED METRICS (definitions stated here BEFORE any number below is computed):
  P1a. PROGRAM-IDENTITY ENTROPY (Shannon bits) + id count + top-share, at BOTH grains (fine:
       full quantized program string; coarse: token types only), over every non-degenerate
       (`!= "∅"`) program in the LEARN population. Comparison row (cited, never re-run):
       the closed 2x2's per-STEP cells all sat at ~0 bits / 1-2 ids (uniform bins, run26/34c)
       or 3.9968 bits / 83 ids at INSTANCE grain only (run32 ADAPT, undenoised). ANY material
       program-space entropy is this reframe's first confirmation. NOTE ON UNITS: 34d's own
       P1a counted per ACCEPTED SPAN (Viterbi-segmented sub-strokes, n=10142 over 1500 strokes,
       ~6.8 spans/stroke); THIS gate counts per STROKE (n<=1500, one program per stroke, per the
       launch brief's own "each stroke becomes a PROGRAM STRING") -- the comparison is
       qualitative (bits/id-count shape), not a literal same-N recount; stated here so the
       difference is never silently glossed over in the final report.
  P1b. CLASS-GRAIN COHERENCE FRACTION (34c/34d's own metric, VERBATIM): an identity is COHERENT
       iff some (alphabet, character) class it appears in was independently produced by >=3
       distinct drawers; coherence fraction = coherent / distinct identities. ALSO reported:
       its converse, the INSTANCE-GRAIN FRACTION (identities confined to exactly one drawer
       across every class they appear in -- run 32's own un-denoised ADAPT failure signature,
       ~99% / 82 of 83). Both at fine and coarse grain.
  P1c. PER-CLASS PROGRAM CONSISTENCY: for the first `P1C_N_ALPHABETS` LEARN alphabets (in LEARN
       order) x first `P1C_N_CHARS_PER_ALPHABET` characters each (sorted-directory order, the
       SAME 30-character deterministic slice), using each drawer's FIRST stroke of that
       character (index 0 -- Omniglot's per-character stroke order is drawer-consistent by
       construction of the task, a documented assumption, not independently re-verified here):
       the POOLED fraction of same-character drawer-PAIRS whose programs match EXACTLY, at each
       grain, versus a SHUFFLED-CLASS NULL (run-33's own law: "report excess over null, not
       raw" -- `P1C_NULL_REPS` count-matched reshuffles of the SAME per-character group sizes,
       averaged).

PRE-REGISTERED VERDICT (stated BEFORE any real number is computed):
  CONFIRMED iff ALL THREE hold:
    (a) fine-grain program entropy >= `BAR_ENTROPY_BITS` (1.5 bits);
    (b) fine-grain P1c excess-over-null >= `BAR_EXCESS_FACTOR` (2x) the null's own value (a
        null of exactly 0.0 is treated as "any positive excess clears the bar" -- an honest
        edge case, not a divide-by-zero);
    (c) fine-grain P1b instance-grain fraction <= `BAR_INSTANCE_FRAC_MAX` (0.50) -- "well below
        run-32's ~99%".
  NULL otherwise. This gate STOPS after reporting either way -- it licenses or kills the full
  RUN 35 build; the eval/coverage machinery (P2-style proposal-layer measurement) is explicitly
  OUT OF SCOPE for this gate and is not built here regardless of the verdict.

DISCIPLINE (CLAUDE.md / ops law): pure measurement, single foreground invocation, expected
wall time minutes (1500 strokes x one denoise + one StrokeQuantize residual read each, the same
per-stroke cost class as run 34d's own gather-edges stage, ~40s/1500 strokes there). Checkpoints
under `results/run35_checkpoints/` (this run's own dir); `results/run34d_checkpoints/` (and
every other `run*_checkpoints/`) is READ-ONLY reference, touched only via `open(..., "r")`.
`seeds/stroke_shapes.json` (a parallel-session-owned, already-dirty file) is never opened by
this script -- verify with `md5sum` before/after any invocation. Every module this script
touches (`domains/stroke_programs.py`, new, this run's own) is NOT one of the parallel-session-
owned shared modules named in `scripts/jabberwock_omniglot_run34d_interaction.py`'s own header
(`domains/mouse_model.py`, `ink_decode.py`, `abs_read.py`, `novelty_calibration.py`,
`stroke_codebook.py`, `homework_loop.py`,
`scripts/jabberwock_omniglot_dynamic_quantization.py`) -- those five/six modules are READ via
their EXISTING public functions only (`ink.ingest_ink`, `mouse_model.denoise_path_global`,
`adaptive_bins._raw_span_values`/`compute_quantile_edges`, `gate.LEARN_ALPHABETS_N`/`DK`/
`LEARN_DRAWERS` constants), never edited, never called for anything that mutates a codebook or
persists a seed.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run35_programs.py --stage gate0
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

import numpy as np

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate   # constants ONLY -- no
                                                                    # gate.boot()/run_learn()
                                                                    # call anywhere below.
from domains import adaptive_bins as ab
from domains import mouse_model as mm
from domains import omniglot_world as ow
from domains import stroke_programs as sp

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run35_checkpoints")
RUN34D_DIR = os.path.join(ROOT, "results", "run34d_checkpoints")   # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS -- byte-identical to run 34d where they overlap (comparability).
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = gate.LEARN_ALPHABETS_N            # 5
LEARN_DRAWERS = gate.LEARN_DRAWERS                    # 01..14
LEARN_STROKE_CAP = 1500                               # run 16/25's saturation-verified cap.
DK = gate.DK                                          # segments=8 -- the SAME grain the `seg`
                                                       # relations already use.

P1C_N_ALPHABETS = 3
P1C_N_CHARS_PER_ALPHABET = 10
P1C_NULL_REPS = 100
P1C_NULL_SEED = 20260705

# Pre-registered verdict bars (stated BEFORE any real number is computed -- see module header).
BAR_ENTROPY_BITS = 1.5
BAR_EXCESS_FACTOR = 2.0
BAR_INSTANCE_FRAC_MAX = 0.50


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _run34d(name: str) -> str:
    return os.path.join(RUN34D_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _donkey0() -> bool:
    return "torch" not in sys.modules


# ---------------------------------------------------------------------------------------------
# LOCAL gather routine (34d's `_collect_learn_strokes_tagged`, EXTENDED with a per-(alphabet,
# character, drawer) stroke index -- P1c's own "first stroke of this character" selector).
# Pure I/O gather, no decode, no decision.
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
                for si, st in enumerate(ow.load_strokes(f)):
                    if len(out) >= cap:
                        break
                    if st.shape[0] < 2:
                        continue
                    out.append((st.tolist(), d, alph, char, si))
    return out


def _dn(points) -> list:
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 3:
        return pts.tolist()
    return mm.denoise_path_global(pts).tolist()


# ---------------------------------------------------------------------------------------------
# P1a/P1b -- identity entropy + class-grain coherence, at a given grain.
# ---------------------------------------------------------------------------------------------
def _entropy_block(idents: list) -> dict:
    non_degenerate = [i for i in idents if i != "∅"]
    hist = ab.family_histogram(non_degenerate)
    rep = ab.entropy_report(non_degenerate)
    rep["n_degenerate"] = len(idents) - len(non_degenerate)
    return rep


def _coherence_block(records: list, key_fn) -> dict:
    """`records`: list of (ident, alph, char, drawer). `key_fn(ident)` selects which identity
    string a record contributes (fine or coarse). An identity is COHERENT iff some class
    (alph, char) it appears in was independently produced by >= 3 distinct drawers; the
    CONVERSE instance-grain fraction counts identities whose best class-span is exactly 1."""
    coherence: dict[str, dict] = {}
    for (ident, alph, char, drawer) in records:
        k = key_fn(ident)
        if k == "∅":
            continue
        class_key = f"{alph}::{char}"
        slot = coherence.setdefault(k, {})
        drawers = slot.setdefault(class_key, [])
        if drawer not in drawers:
            drawers.append(drawer)
    n_distinct = len(coherence)
    n_coherent = 0
    n_instance_only = 0
    per_id_best = {}
    for ident, classes in coherence.items():
        best = max((len(ds) for ds in classes.values()), default=0)
        per_id_best[ident] = best
        if best >= 3:
            n_coherent += 1
        if best <= 1:
            n_instance_only += 1
    return {
        "n_distinct_ids": n_distinct, "n_coherent": n_coherent,
        "coherence_fraction": (n_coherent / n_distinct) if n_distinct else 0.0,
        "n_instance_only": n_instance_only,
        "instance_fraction": (n_instance_only / n_distinct) if n_distinct else 0.0,
        "per_id_best": per_id_best,
    }


# ---------------------------------------------------------------------------------------------
# P1c -- per-class program consistency vs a count-matched shuffled-class null.
# ---------------------------------------------------------------------------------------------
def _match_fraction(groups: list) -> tuple:
    """`groups`: list of lists of identity strings (one list per class). Pooled (matched,
    total) same-class-pair count -- a class with <2 members contributes (0, 0)."""
    matched, total = 0, 0
    for members in groups:
        n = len(members)
        for i in range(n):
            for j in range(i + 1, n):
                total += 1
                if members[i] == members[j]:
                    matched += 1
    return matched, total


def _p1c_block(class_members: dict, rng: np.random.Generator) -> dict:
    """`class_members`: {(alph, char): [identity_str, ...]} (one entry per present drawer's
    first stroke of that character). Returns raw pooled fraction, count-matched shuffled null
    (mean over `P1C_NULL_REPS`), and excess = raw - null."""
    groups = list(class_members.values())
    sizes = [len(g) for g in groups]
    matched, total = _match_fraction(groups)
    raw = (matched / total) if total else 0.0

    flat = [m for g in groups for m in g]
    null_fracs = []
    for _ in range(P1C_NULL_REPS):
        perm = rng.permutation(flat).tolist()
        idx = 0
        shuffled_groups = []
        for sz in sizes:
            shuffled_groups.append(perm[idx:idx + sz])
            idx += sz
        m, t = _match_fraction(shuffled_groups)
        if t:
            null_fracs.append(m / t)
    null_mean = float(np.mean(null_fracs)) if null_fracs else 0.0
    excess = raw - null_mean
    bar = (BAR_EXCESS_FACTOR * null_mean) if null_mean > 0 else 0.0
    excess_clears_bar = bool(excess > 0) if null_mean <= 0 else bool(raw >= bar)
    return {
        "n_classes": len(groups), "n_classes_with_pairs": sum(1 for g in groups if len(g) >= 2),
        "n_pairs": total, "n_matched": matched, "raw_fraction": raw,
        "null_mean": null_mean, "excess": excess, "bar": bar,
        "excess_clears_bar": excess_clears_bar,
    }


def stage_gate0():
    print(f"\n{SEP}\n  STAGE: gate0 (RUN 35 -- program tokenization, order-N WITHIN the stroke)\n{SEP}")
    t_start = time.time()

    # -------------------------------------------------------------------------------------- #
    # verify -- recipe check + cite run34d's level edges (READ-ONLY reference, never re-fit).
    # -------------------------------------------------------------------------------------- #
    edges_path = _run34d("edges_report.json")
    if not os.path.exists(edges_path):
        print(f"  WALL: missing prerequisite {edges_path} (run34d must have completed).")
        return 1
    edges_report = _load_json(edges_path)
    level_edges = edges_report["turn_edges"]
    tol_deg = sp.tol_deg_from_edges(level_edges)

    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    print(f"  recipe check  LEARN_ALPHABETS_N={LEARN_ALPHABETS_N}  DK={DK}  "
          f"LEARN_STROKE_CAP={LEARN_STROKE_CAP}")
    print(f"  learn_alphabets={learn_alphabets}")
    print(f"  CITED level_edges (run34d, denoised+adaptive, {len(level_edges)-1} eff bins): "
          f"{[round(v, 2) for v in level_edges]}")
    print(f"  tol_deg = 0.5 * median(diff(level_edges)) = {tol_deg:.4f} degrees")
    if not ow.have_data("background"):
        print("  WALL: Omniglot background data not found.")
        return 1

    # -------------------------------------------------------------------------------------- #
    # gather -- SAME 1500-stroke LEARN population as run34d.
    # -------------------------------------------------------------------------------------- #
    strokes = _collect_learn_strokes_tagged(learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP)
    print(f"\n  LEARN population: {len(strokes)} strokes  DENOISE=global  "
          f"segments={DK['segments']} (n_steps={DK['segments']-1} per stroke)")

    # -------------------------------------------------------------------------------------- #
    # PHASE 1 -- tokenize every stroke's turn sequence into (unquantized) promoted runs;
    # pool every ramp delta observed so `delta_edges` can be fit from THIS run's own LEARN
    # population (mint-nothing: a throwaway substrate per stroke, no graph state retained).
    # -------------------------------------------------------------------------------------- #
    t0 = time.time()
    per_stroke = []   # (promoted, raw_deltas, alph, char, drawer, stroke_idx, n_turn_steps)
    pooled_deltas: list = []
    n_degenerate = 0
    for (points, drawer, alph, char, si) in strokes:
        dpts = _dn(points)
        s = srs.Substrate()
        turn_seq = sp.stroke_turn_sequence(s, dpts, segments=DK["segments"],
                                           max_knots=DK["max_knots"])
        if not turn_seq:
            n_degenerate += 1
            per_stroke.append(([], [], alph, char, drawer, si, 0))
            continue
        res = sp.tokenize_turn_sequence(turn_seq, tol_deg, level_edges, delta_edges=None)
        pooled_deltas.extend(res["raw_deltas"])
        per_stroke.append((res["promoted"], res["raw_deltas"], alph, char, drawer, si,
                           len(turn_seq)))
    print(f"  PHASE 1 (tokenize, gather ramp deltas): {len(strokes)} strokes in "
          f"{time.time()-t0:.1f}s  degenerate(<2 knots)={n_degenerate}  "
          f"pooled_ramp_deltas={len(pooled_deltas)}")

    # -------------------------------------------------------------------------------------- #
    # delta edges -- fit ONCE over this run's own pooled ramp deltas.
    # -------------------------------------------------------------------------------------- #
    delta_edges = sp.gather_delta_edges(pooled_deltas)
    print(f"  delta_edges ({sp.DEFAULT_DELTA_BINS} requested -> {len(delta_edges)-1} "
          f"effective): {[round(v, 2) for v in delta_edges]}")

    # -------------------------------------------------------------------------------------- #
    # PHASE 2 -- finalize every stroke's program (fine + coarse strings).
    # -------------------------------------------------------------------------------------- #
    records = []   # (fine, coarse, alph, char, drawer, stroke_idx, n_tokens, n_turn_steps)
    for (promoted, _raw_deltas, alph, char, drawer, si, n_steps) in per_stroke:
        if not promoted:
            records.append(("∅", "∅", alph, char, drawer, si, 0, n_steps))
            continue
        tokens = sp.finalize_tokens(promoted, level_edges, delta_edges)
        fine = sp.format_fine(tokens)
        coarse = sp.format_coarse(tokens)
        records.append((fine, coarse, alph, char, drawer, si, len(tokens), n_steps))
    _save_json({"records": records, "tol_deg": tol_deg, "level_edges": level_edges,
               "delta_edges": delta_edges, "learn_alphabets": learn_alphabets},
              _ckpt("programs.json"))
    print(f"  PHASE 2 (finalize) complete -- saved -> {_ckpt('programs.json')}")

    # -------------------------------------------------------------------------------------- #
    # tokenization stats -- tokens/stroke distribution (compression sanity check).
    # -------------------------------------------------------------------------------------- #
    n_tok_counts = [r[6] for r in records if r[0] != "∅"]
    tok_hist: dict = {}
    for n in n_tok_counts:
        tok_hist[str(n)] = tok_hist.get(str(n), 0) + 1
    print(f"\n  TOKENIZATION STATS: n_strokes={len(records)}  degenerate={n_degenerate}  "
          f"tokens/stroke mean={np.mean(n_tok_counts):.2f}  median={np.median(n_tok_counts):.1f}  "
          f"n_steps/stroke=7 (DK['segments']-1)  histogram={tok_hist}")

    # -------------------------------------------------------------------------------------- #
    # P1a -- identity entropy, fine + coarse.
    # -------------------------------------------------------------------------------------- #
    fine_idents = [r[0] for r in records]
    coarse_idents = [r[1] for r in records]
    p1a_fine = _entropy_block(fine_idents)
    p1a_coarse = _entropy_block(coarse_idents)
    print(f"\n  P1a FINE   entropy={p1a_fine['entropy_bits']:.4f} bits "
          f"(max {p1a_fine['max_entropy_bits']:.4f})  n_ids={p1a_fine['n_families']}  "
          f"n_obs={p1a_fine['n_observations']}  top_share={p1a_fine['top_family_share']:.4f}  "
          f"n_degenerate={p1a_fine['n_degenerate']}")
    print(f"  P1a COARSE entropy={p1a_coarse['entropy_bits']:.4f} bits "
          f"(max {p1a_coarse['max_entropy_bits']:.4f})  n_ids={p1a_coarse['n_families']}  "
          f"n_obs={p1a_coarse['n_observations']}  top_share={p1a_coarse['top_family_share']:.4f}")
    print(f"  (cited 2x2 comparison row -- per-STEP cells: run26/34c uniform-bin ~0 bits/1-2 "
          f"ids; run32 ADAPT undenoised 3.9968 bits/83 ids INSTANCE-grain; NOTE unit differs, "
          f"see header)")

    # -------------------------------------------------------------------------------------- #
    # P1b -- class-grain coherence + converse instance-fraction, fine + coarse.
    # -------------------------------------------------------------------------------------- #
    fine_records = [(r[0], r[2], r[3], r[4]) for r in records]
    coarse_records = [(r[1], r[2], r[3], r[4]) for r in records]
    p1b_fine = _coherence_block(fine_records, key_fn=lambda x: x)
    p1b_coarse = _coherence_block(coarse_records, key_fn=lambda x: x)
    print(f"\n  P1b FINE   coherence={p1b_fine['n_coherent']}/{p1b_fine['n_distinct_ids']}="
          f"{p1b_fine['coherence_fraction']:.4f}   instance-only="
          f"{p1b_fine['n_instance_only']}/{p1b_fine['n_distinct_ids']}="
          f"{p1b_fine['instance_fraction']:.4f}")
    print(f"  P1b COARSE coherence={p1b_coarse['n_coherent']}/{p1b_coarse['n_distinct_ids']}="
          f"{p1b_coarse['coherence_fraction']:.4f}   instance-only="
          f"{p1b_coarse['n_instance_only']}/{p1b_coarse['n_distinct_ids']}="
          f"{p1b_coarse['instance_fraction']:.4f}")
    print(f"  (cited RUN32 ADAPT instance-grain fraction: ~0.988 (82/83), the failure signature)")

    # -------------------------------------------------------------------------------------- #
    # P1c -- per-class program consistency vs count-matched shuffled-class null.
    # -------------------------------------------------------------------------------------- #
    p1c_alphabets = learn_alphabets[:P1C_N_ALPHABETS]
    class_members_fine: dict = {}
    class_members_coarse: dict = {}
    for (fine, coarse, alph, char, drawer, si, _nt, _ns) in records:
        if si != 0 or alph not in p1c_alphabets:
            continue
        chars_this_alph = [os.path.basename(c) for c in
                           ow.characters(alph, "background")[:P1C_N_CHARS_PER_ALPHABET]]
        if char not in chars_this_alph:
            continue
        key = (alph, char)
        class_members_fine.setdefault(key, []).append(fine)
        class_members_coarse.setdefault(key, []).append(coarse)

    rng_fine = np.random.default_rng(P1C_NULL_SEED)
    rng_coarse = np.random.default_rng(P1C_NULL_SEED + 1)
    p1c_fine = _p1c_block(class_members_fine, rng_fine)
    p1c_coarse = _p1c_block(class_members_coarse, rng_coarse)
    print(f"\n  P1c FINE   classes={p1c_fine['n_classes']} "
          f"(with>=2 drawers: {p1c_fine['n_classes_with_pairs']})  pairs={p1c_fine['n_pairs']}  "
          f"raw={p1c_fine['raw_fraction']:.4f}  null={p1c_fine['null_mean']:.4f}  "
          f"excess={p1c_fine['excess']:.4f}  bar(2x null)={p1c_fine['bar']:.4f}  "
          f"clears_bar={p1c_fine['excess_clears_bar']}")
    print(f"  P1c COARSE classes={p1c_coarse['n_classes']} "
          f"(with>=2 drawers: {p1c_coarse['n_classes_with_pairs']})  "
          f"pairs={p1c_coarse['n_pairs']}  raw={p1c_coarse['raw_fraction']:.4f}  "
          f"null={p1c_coarse['null_mean']:.4f}  excess={p1c_coarse['excess']:.4f}  "
          f"bar(2x null)={p1c_coarse['bar']:.4f}  clears_bar={p1c_coarse['excess_clears_bar']}")

    # -------------------------------------------------------------------------------------- #
    # PRE-REGISTERED VERDICT.
    # -------------------------------------------------------------------------------------- #
    cond_a = p1a_fine["entropy_bits"] >= BAR_ENTROPY_BITS
    cond_b = p1c_fine["excess_clears_bar"]
    cond_c = p1b_fine["instance_fraction"] <= BAR_INSTANCE_FRAC_MAX
    confirmed = bool(cond_a and cond_b and cond_c)
    print(f"\n{SEP}\n  RUN 35 GATE 0 -- PRE-REGISTERED VERDICT\n{SEP}")
    print(f"  (a) fine entropy >= {BAR_ENTROPY_BITS} bits: {p1a_fine['entropy_bits']:.4f} -> "
          f"{'PASS' if cond_a else 'FAIL'}")
    print(f"  (b) fine P1c excess clears {BAR_EXCESS_FACTOR}x null: "
          f"raw={p1c_fine['raw_fraction']:.4f} null={p1c_fine['null_mean']:.4f} -> "
          f"{'PASS' if cond_b else 'FAIL'}")
    print(f"  (c) fine instance-grain fraction <= {BAR_INSTANCE_FRAC_MAX}: "
          f"{p1b_fine['instance_fraction']:.4f} -> {'PASS' if cond_c else 'FAIL'}")
    print(f"\n  *** VERDICT: {'CONFIRMED' if confirmed else 'NULL'} -- "
          f"{'the program-space reframe finds class-grain structure per-step quantization was '
             'blind to; RUN 35 proper (eval/coverage machinery) is licensed.' if confirmed else
             'the reframe does NOT clear its own pre-registered bars at Gate 0; do NOT build '
             'the eval/coverage machinery this run.'} ***")

    out = dict(
        tol_deg=tol_deg, level_edges=level_edges, delta_edges=delta_edges,
        n_strokes=len(records), n_degenerate=n_degenerate,
        tokens_per_stroke=dict(mean=float(np.mean(n_tok_counts)) if n_tok_counts else 0.0,
                               median=float(np.median(n_tok_counts)) if n_tok_counts else 0.0,
                               histogram=tok_hist),
        p1a=dict(fine=p1a_fine, coarse=p1a_coarse),
        p1b=dict(fine={k: v for k, v in p1b_fine.items() if k != "per_id_best"},
                 coarse={k: v for k, v in p1b_coarse.items() if k != "per_id_best"}),
        p1c=dict(fine=p1c_fine, coarse=p1c_coarse),
        verdict=dict(confirmed=confirmed, cond_entropy=cond_a, cond_excess=cond_b,
                     cond_instance_frac=cond_c,
                     bars=dict(entropy_bits=BAR_ENTROPY_BITS, excess_factor=BAR_EXCESS_FACTOR,
                              instance_frac_max=BAR_INSTANCE_FRAC_MAX)),
    )
    _save_json(out, _ckpt("gate0_report.json"))
    print(f"\n  saved -> {_ckpt('gate0_report.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"\n  [gate0 total wall time: {time.time()-t_start:.1f}s]")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["gate0"])
    args = p.parse_args()
    return {"gate0": stage_gate0}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
