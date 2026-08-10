"""domains/motor_verdict.py -- RUN 49: THE MOTOR-PROGRAM VERDICT, graph-native, training-free.

THE BOTTLENECK THIS ATTACKS (run 48, `8e4b7aee`): the whole-shape continuous verdict
(`per_stroke_abs.program_score`, SC+TPS fused over per-stroke point-sets) IGNORES stroke-
INTERIOR / motor structure -- exactly the level BPL's own generative motor programs exploit and
this arc's own verdict never has. Pen data HAS that structure (run 46: 17.1x class-grain
information at the stroke grain) but every prior attempt to use it was a PROPOSAL (recall-
limited: run 47's shortlist coverage 52-56%, three honest negatives -- UCI/QuickDraw/DigiLeTs,
`OMNIGLOT_ARC.md` Addendum 2 + run 48). THIS MODULE builds a real MOTOR DISTANCE and fuses it
INTO the verdict (never replaces it -- RUN 37A's law, `cca938fd`, BINDING), so the discriminative
motor-program information can act at decision time on the FULL candidate set, not a shortlist.

MOTOR PROGRAM OF A GLYPH (`glyph_motor_program`) -- three ingredients, per this run's own launch
brief, each already-held machinery, reused not reinvented:
  (1) per-stroke FINE-grain program-token tuple (`domains/stroke_programs.py`'s own
      `tokenize_turn_sequence`/`format_fine` -- level-runs/ramps/change-points on the per-segment
      turn residual `StrokeQuantize` already computes; FINE, not COARSE, so bin PARAMETERS
      participate, not just token TYPES -- a grain richer than `committed_shape`'s own coarse
      commit string).
  (2) the run-39 pen-up channel's LIVE features (`domains/motor_plan.py`: start-position +
      transition-sector agreement; run 39's own gate0 licensed these two and explicitly killed
      order/direction as population-CONVENTION, not identity -- this module never uses them).
  (3) stroke count.
No denoising: `mouse_model.denoise_path_global` targets the Bresenham/mousewriting staircase
artifact (`OMNIGLOT_ARC.md` sec 5) that real pen data does not carry (Addendum 2, run 46) --
`scripts.jabberwock_omniglot_run47_pendata.fit_edges_on_learn`/`tokenize_with_frozen_edges`
already established this convention for pen corpora (no denoise call anywhere in that module);
this module follows it, unmodified.

MOTOR DISTANCE (`motor_distance`) -- a three-part composite, EQUAL pre-registered weights
(`W_PROGRAM = W_PENUP = W_COUNT = 1/3`, stated here BEFORE any real number is computed, never
tuned against any eval outcome -- only the OUTER fusion weight `w_m`/`lam` is background-
calibrated, per this run's own launch brief):
  PROGRAM  -- per-ALIGNED-stroke fine-program-token edit distance (`committed_shape.
              _token_edit_distance`, reused VERBATIM -- a standard list-Levenshtein -- normalized
              into [0,1] by the longer token sequence's own length), aligned by the SAME held
              greedy stroke matcher `domains/motor_plan.py` already uses
              (`scripts.jabberwock_omniglot_run39_motorplan.greedy_match`, the FALSY-ZERO BUG
              already fixed at its source -- `float(v) if v is not None else float("nan")`, never
              `v or nan` -- so no local re-fix is needed; this module imports that same function,
              never a parallel copy, exactly `motor_plan.py`'s own reuse discipline). An unmatched
              stroke (stroke-count mismatch) scores the maximum distance 1.0 -- an honest penalty
              for missing evidence, never silently imputed as agreement.
  PEN-UP   -- `1 - motor_plan.motor_plan_agreement(...)["m"]`, REUSED VERBATIM (not re-derived):
              the SAME spatial correspondence (`greedy_match`) underlies both channels, so this
              module computes it once conceptually and asks two questions of it (WHAT was drawn
              at each aligned stroke vs. HOW the pen moved between them).
  COUNT    -- `|n_a - n_b| / max(n_a, n_b, 1)`: the glyph's own stroke-count disagreement, a
              THIRD, separate term from PROGRAM's per-pair unmatched penalty above -- PROGRAM
              penalizes missing per-stroke IDENTITY evidence at each unmatched slot; COUNT
              penalizes the structural PLAN-LENGTH difference itself (a scalar fact, present even
              when the two counts are close but not zero apart) -- not double-counting the same
              event, both reported separately (never hidden inside the composite, per this arc's
              own engagement-reporting law, `OMNIGLOT_ARC.md` sec 3).

THE FUSED VERDICT (`fused_score_pairs`/`fused_argmin`) -- `final_score(ci) = geo_score(ci) + w_m *
m(query, ci)`, `w_m` SPREAD-MATCHED (RUN 44b's own protocol, `domains.deform_metric.derive_w_aff`,
reused VERBATIM -- pure arithmetic, no Omniglot-specific staging inside it: `target =
median(existing-term spreads on background) / spread(new term)`; run 49 has exactly ONE existing
term, `geo_score`, where run 44b had three -- `derive_w_m` below passes `spread_geo` three times,
`median([spread_geo]*3) == spread_geo`, reproducing the SAME formula on a single-existing-term
ensemble, reported as such, not disguised as a richer ensemble) then LAMBDA-scaled (a background-
calibration grid sweep, mirroring `scripts.jabberwock_omniglot_run48_digilets.stage_calibrate`'s
own pattern, under the SAME background-sanity STOP, `465d57da`'s transplant). `lam=0.0` recovers
`argmin(geo_scores)` alone BYTE-IDENTICALLY (the SUPPLEMENT invariant, RUN 37A's law) -- gated by
`tests/test_motor_verdict_migrated.py`. Winner = held `Argmin` (`abs_read._argmin_pairs_term`,
reused verbatim, the SAME idiom `domains/motor_plan.py`'s own `combined_verdict` uses), never a
Python `min()`/`argmin()` -- source-audited (mirrors `test_motor_supplement_migrated.py`'s own
Gate 4).

ARCHITECTURE (CLAUDE.md): this module MINTS NOTHING -- no `teach()`, no `add_node`/`add_edge`, no
`run_rules()`, no `decode_ink()` anywhere below (source-audited). It is a WORLD-ADAPTER-class
feature extractor + a held-Term-scored distance/fusion, the same class `domains/motor_plan.py`/
`domains/committed_shape.py` already are.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import substrate_rs as srs

from domains import abs_read as ar
from domains import committed_shape as cs
from domains import deform_metric as dm
from domains import motor_plan as mp
from domains import stroke_programs as sp
from scripts import jabberwock_omniglot_run39_motorplan as gate0

EMPTY_TOKEN = "∅"          # the sentinel `stroke_programs.format_fine` uses for a
                                # degenerate (<2-knot) stroke -- reused verbatim, not redefined.

MAX_STROKES_DEFAULT = 6          # matches run47/48's own `MAX_STROKES` convention (a caller
                                 # scoring real corpora should pass that value explicitly).

# Pre-registered EQUAL weights for the three motor-distance components (module docstring) --
# stated here, before any real number is computed, NEVER tuned against an eval outcome. Only
# the OUTER `w_m`/`lam` fusion weight is background-calibrated (see `derive_w_m`/the run-49 gate
# script's own `--stage calibrate`).
W_PROGRAM = 1.0 / 3.0
W_PENUP = 1.0 / 3.0
W_COUNT = 1.0 / 3.0


# ------------------------------------------------------------------------------------------- #
#  MOTOR PROGRAM -- per-stroke fine tokens + pen-up-ready normalized xy + stroke count.
# ------------------------------------------------------------------------------------------- #
def stroke_fine_tokens(points, *, tol_deg: float, level_edges: list, delta_edges: list,
                        segments: int, max_knots: int) -> tuple:
    """One stroke's FINE-grain program-token tuple: `stroke_programs.stroke_turn_sequence` (the
    EXISTING held `StrokeQuantize` residual read, reused verbatim) -> `tokenize_turn_sequence` ->
    `format_fine` (e.g. `"line(3)|arc(2,3)"`) -> split on `"|"` into a tuple, the same
    string-to-tuple idiom `committed_shape.commit_tokens` uses for the COARSE grain, applied here
    to the FINE grain (bin parameters participate, not just token types). `(EMPTY_TOKEN,)` for a
    degenerate (<2-point or <2-knot) stroke -- an honest empty program, never a crash. No
    denoising (see module docstring)."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        return (EMPTY_TOKEN,)
    s = srs.Substrate()
    turn_seq = sp.stroke_turn_sequence(s, pts.tolist(), segments=segments, max_knots=max_knots)
    if not turn_seq:
        return (EMPTY_TOKEN,)
    res = sp.tokenize_turn_sequence(turn_seq, tol_deg, level_edges, delta_edges=delta_edges)
    fine = res["fine"]
    return (EMPTY_TOKEN,) if fine == EMPTY_TOKEN else tuple(fine.split("|"))


def glyph_motor_program(strokes_xy: list, *, edges: dict, segments: int, max_knots: int,
                         max_strokes: int = MAX_STROKES_DEFAULT) -> dict:
    """The glyph's motor program (module docstring): `strokes_xy` -- a list of per-stroke
    `(k, 2)` arrays, OWN DRAW ORDER (mechanical -- the caller's own loader order, e.g.
    `pen_world.load_digilets_samples`'s own `"strokes"` field). `edges`: `{"tol_deg",
    "level_edges", "delta_edges"}`, FROZEN by a LEARN stage upstream (this function never fits
    an edge set itself -- a caller passes an already-fit dict, e.g. read from
    `results/run48_checkpoints/learn.json`).

    Returns `{"fine_tokens": [tuple, ...], "norm_xy": [...], "n_strokes": int}` -- `norm_xy` is
    `gate0.normalize_glyph_xy`'s own output (reused verbatim, the SAME [-1,1]^2 glyph frame
    `motor_plan.motor_plan_agreement`'s start-cell/transition-sector features are defined over)."""
    used = [np.asarray(s, dtype=float) for s in strokes_xy[:max_strokes] if len(s) >= 1]
    fine_tokens = [stroke_fine_tokens(s, tol_deg=edges["tol_deg"], level_edges=edges["level_edges"],
                                       delta_edges=edges["delta_edges"], segments=segments,
                                       max_knots=max_knots) for s in used]
    norm_xy = gate0.normalize_glyph_xy(used) if used else []
    return {"fine_tokens": fine_tokens, "norm_xy": norm_xy, "n_strokes": len(used)}


# ------------------------------------------------------------------------------------------- #
#  MOTOR DISTANCE -- program (aligned edit distance) + pen-up (1 - agreement) + count.
# ------------------------------------------------------------------------------------------- #
def _normalized_token_edit(a: tuple, b: tuple) -> float:
    """`committed_shape._token_edit_distance` (standard list-Levenshtein, reused verbatim),
    normalized into `[0, 1]` by the longer token sequence's own length -- bounded, comparable in
    scale to the pen-up/count components below (an un-normalized edit count would grow with
    program length and dominate the composite for long programs, never licensed against any eval
    -- this is a STATED, PRE-REGISTERED normalization, not a tuned one)."""
    d = cs._token_edit_distance(a, b)
    return d / max(len(a), len(b), 1)


def motor_distance(native, prog_a: dict, prog_b: dict) -> dict:
    """m(A, B) -- see module docstring for the three-part composite and its pre-registered equal
    weights. Alignment is the SAME held greedy stroke matcher (`gate0.greedy_match`, spatial
    `PointSetDist` correspondence, falsy-zero-fixed at its source) `motor_plan.
    motor_plan_agreement` already uses -- one correspondence, read for two evidence channels.

    Returns `{"m", "program", "pen_up", "count", "n_matched", "n_a", "n_b", "pen_up_detail"}` --
    every sub-score reported, never hidden inside the composite (this arc's own engagement-
    reporting law)."""
    n_a, n_b = prog_a["n_strokes"], prog_b["n_strokes"]

    if n_a == 0 or n_b == 0:
        program = 1.0
        n_matched = 0
    else:
        mapping = gate0.greedy_match(native, prog_b["norm_xy"], prog_a["norm_xy"])   # a_idx->b_idx
        n_matched = len(mapping)
        dists = [_normalized_token_edit(prog_a["fine_tokens"][a_idx], prog_b["fine_tokens"][b_idx])
                 for a_idx, b_idx in mapping.items()]
        n_unmatched = max(n_a, n_b) - n_matched
        program = (sum(dists) + n_unmatched * 1.0) / max(n_a, n_b, 1)

    if n_a >= 1 and n_b >= 1 and prog_a["norm_xy"] and prog_b["norm_xy"]:
        agree = mp.motor_plan_agreement(native, prog_a["norm_xy"], prog_b["norm_xy"])
        pen_up = 1.0 - agree["m"]
    else:
        pen_up = 1.0
        agree = None

    count = abs(n_a - n_b) / max(n_a, n_b, 1)

    m = W_PROGRAM * program + W_PENUP * pen_up + W_COUNT * count
    return {"m": m, "program": program, "pen_up": pen_up, "count": count,
            "n_matched": n_matched, "n_a": n_a, "n_b": n_b, "pen_up_detail": agree}


# ------------------------------------------------------------------------------------------- #
#  FUSION -- spread-matched w_m (RUN 44b protocol) + lambda-scaled, held Argmin winner.
# ------------------------------------------------------------------------------------------- #
def spread_of_scores(scores_per_episode: list) -> float:
    """Mechanical statistic (mean, over episodes, of the across-candidate standard deviation) --
    RUN 44b's own `spread` quantity (`scripts.jabberwock_omniglot_run44b_spread.stage_spread`'s
    own per-episode `np.std` reduction), the same reduction applied to any score channel."""
    stds = [float(np.std(np.asarray(scores, dtype=float))) for scores in scores_per_episode
            if len(scores) > 1]
    return float(np.mean(stds)) if stds else 0.0


def derive_w_m(spread_geo: float, spread_m: float) -> float:
    """RUN 44b's own spread-matching arithmetic (`domains.deform_metric.derive_w_aff`, reused
    VERBATIM -- pure median/divide, no Omniglot-specific staging inside it): `target =
    median(existing-term spreads) / spread(new term)`. Run 49 has exactly ONE existing term
    (`geo_score`) where run 44b had three (smoothdeform/part/sc) -- passing `spread_geo` three
    times reproduces the identical formula on a single-existing-term ensemble
    (`median([spread_geo]*3) == spread_geo`), reported as such."""
    return dm.derive_w_aff(spread_geo, spread_geo, spread_geo, spread_m)


def fused_score_pairs(geo_scores: list, m_scores: list, w_m: float, lam: float) -> list:
    """`(score, candidate_index)` pairs for the FUSED verdict: `final = geo_score + lam * w_m *
    m` (module docstring). `lam=0.0` makes every pair's score equal to its own `geo_score` --
    `fused_argmin` at `lam=0.0` is therefore BYTE-IDENTICAL to `argmin(geo_scores)` alone (the
    SUPPLEMENT invariant, RUN 37A's law), gated directly by
    `tests/test_motor_verdict_migrated.py`."""
    return [(g + lam * w_m * m, i) for i, (g, m) in enumerate(zip(geo_scores, m_scores))]


def fused_argmin(native, geo_scores: list, m_scores: list, w_m: float, lam: float) -> Optional[int]:
    """Winner = held `Argmin` (`abs_read._argmin_pairs_term`, reused verbatim -- the SAME idiom
    `domains/motor_plan.py`'s own `combined_verdict` uses), never a Python `min()`/`argmin()`."""
    pairs = fused_score_pairs(geo_scores, m_scores, w_m, lam)
    w = native.evaluate(ar._argmin_pairs_term(pairs), {})
    return int(w[1]) if w is not None else None


__all__ = [
    "EMPTY_TOKEN", "MAX_STROKES_DEFAULT", "W_PROGRAM", "W_PENUP", "W_COUNT",
    "stroke_fine_tokens", "glyph_motor_program", "motor_distance",
    "spread_of_scores", "derive_w_m", "fused_score_pairs", "fused_argmin",
]
