"""stable_parse_geometric_abs — THE ONE UNTESTED CLEAN COMBINATION in the handwriting arc:
combine the STABLE bootstrapped sub-stroke inventory (c5d35d18) with PER-STROKE GEOMETRIC
correspondence AbS (bfe3f4a6). Use the stable inventory to ESTABLISH the stroke correspondence
(which query stroke <-> which support stroke, by shared held-medoid IDENTITY), but score each
corresponded stroke pair by its CONTINUOUS GEOMETRY (held ShapeContextDist + TpsDeformDist) —
NOT a histogram. Keep the stable parse AND the geometry together. graph-native, earn-not-borrow,
donkey=0.

THE ARC SO FAR: holistic coarse whole-char AbS (~61%) keeps being the earned ceiling because every
FINER decomposition loses geometry. TWO pieces were each validated SEPARATELY:
  - c5d35d18: a STABLE bootstrapped inventory (Gemma-clustered background sub-strokes -> held MEDOID
    point-sets; stability 0.27->0.34) — but used as a stroke-identity HISTOGRAM it only gets ~23%
    (the histogram THROWS AWAY geometry).
  - bfe3f4a6: per-stroke GEOMETRIC correspondence AbS (held ShapeContextDist/TpsDeformDist) — but it
    nulled at ~40% because the per-stroke PARSE/correspondence was UNSTABLE across drawers (~65% of
    chars differ in stroke COUNT, so the permutation search matched mismatched strokes).

THE HYPOTHESIS: the per-stroke geometric AbS nulled because the CORRESPONDENCE was unstable. The
stable inventory gives each stroke a STABLE IDENTITY label (nearest held medoid). If we correspond
query<->support strokes by SHARED IDENTITY (stable) and then score each corresponded pair by held
CONTINUOUS GEOMETRY (not a histogram), do we BEAT holistic coarse AbS (~61%)?
  - YES  -> the parse genuinely WAS the lever (it needed stability AND geometry together).
  - NO   -> holistic AbS is the GENUINE earned ceiling; the gap to BPL/Gemma is irreducibly data +
            the discretization tradeoff. A DEFINITIVE bottom for the arc.

THE SCORE (lower = candidate's program better explains the query):
  PARSE query+support into per-stroke point-sets (held segmenter; whole-char normalized so each
    stroke keeps its position = inter-stroke geometry — same as bfe3f4a6).
  STABLE-IDENTITY CORRESPONDENCE: label every stroke by its nearest held MEDOID (held
    ShapeContextDist over the c5d35d18 inventory). Correspond query stroke i <-> the support stroke of
    the SAME identity that is geometrically closest (stable label first, geometry breaks ties);
    unmatched-identity strokes pay a parse-mismatch cost.
  PER-STROKE CONTINUOUS GEOMETRY: each corresponded pair scored by held TpsDeformDist +
    ShapeContextDist (the actual point-sets, NOT histogram bins).
  TOTAL = sum of corresponded per-stroke geometric costs + parse-mismatch cost. Argmin over candidates.

EARN-NOT-BORROW / donkey=0: the inventory's medoids are HELD geometry (c5d35d18; Gemma was the
read-only teacher for the CLUSTERING only, already crystallized into held medoids — 0 Gemma calls at
recognition). Every DISTANCE and the correspondence DECISION are held Rust Terms (ShapeContextDist /
TpsDeformDist) + bounded search. numpy is ADAPTER-ONLY (load/normalize/resample/label-bookkeeping).
No learned feature, no borrowed net in the inference. No LLM.
"""
from __future__ import annotations
import numpy as _np                 # ADAPTER: point-set load/normalize/resample + label bookkeeping
import substrate_rs as _srs
import domains.per_stroke_abs as _ps

_S = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}
PARSE_COST = 0.5                     # cost per unmatched (identity-orphan) stroke (matches per_stroke_abs)


def _scd(a, b):
    """Held ShapeContextDist between two point-sets (Belongie 2002). Used for stable-identity labels."""
    return float(_S.evaluate({"type": "ShapeContextDist", "a": _L(a), "b": _L(b)}, {}))


def parse_with_identity(path, medoids, N=24, max_strokes=6):
    """PARSE a char into per-stroke point-sets AND label each stroke with its stable IDENTITY = the
    index of the nearest held MEDOID (held ShapeContextDist over the bootstrapped inventory, c5d35d18).
    Returns (strokes, labels) — the actual point-sets are KEPT (geometry), the label = the stable
    identity used for correspondence. NO histogram collapse. NO Gemma (held medoids only)."""
    strokes = _ps.stroke_point_sets(path, N=N, max_strokes=max_strokes)
    labels = []
    for s in strokes:
        d = [_scd(s, m) for m in medoids]
        labels.append(int(_np.argmin(d)))
    return strokes, labels


def _stroke_geo_cost(qs, ss):
    """PER-STROKE CONTINUOUS geometric cost (held Terms): TpsDeformDist + ShapeContextDist between the
    two actual stroke point-sets. LOWER = the support stroke warps onto the query stroke better. This is
    the geometry the histogram threw away — kept here per corresponded stroke pair."""
    return _ps._stroke_warp_cost(qs, ss)


def stable_correspondence_score(q_strokes, q_labels, s_strokes, s_labels):
    """Correspond query<->support strokes by SHARED STABLE IDENTITY, score each pair by CONTINUOUS
    geometry. The stable medoid label decides WHO matches WHOM (the stable parse establishes the
    correspondence); the held geometric warp then scores each corresponded pair on its actual shape.

    For each query stroke, find the support stroke(s) of the SAME identity label and take the
    geometrically closest (held warp cost) as its correspondent; a support stroke is used at most once.
    Query strokes with no same-identity support partner pay PARSE_COST (identity orphan). Leftover
    support strokes also pay PARSE_COST (description-length penalty, as in per_stroke_abs).
    LOWER total = the candidate's stable-parse program better explains the query."""
    nq, ns = len(q_strokes), len(s_strokes)
    if nq == 0 or ns == 0:
        return PARSE_COST * max(nq, ns, 1)
    used_s = set()
    total = 0.0
    matched_q = 0
    # greedy by best same-identity geometric pair, globally cheapest first (stable label gates eligibility)
    cands = []
    for i in range(nq):
        for j in range(ns):
            if q_labels[i] == s_labels[j]:                  # STABLE IDENTITY gates the correspondence
                cands.append((_stroke_geo_cost(q_strokes[i], s_strokes[j]), i, j))
    cands.sort()
    used_q = set()
    for c, i, j in cands:
        if i in used_q or j in used_s:
            continue
        total += c                                          # CONTINUOUS geometry scores the pair
        used_q.add(i); used_s.add(j); matched_q += 1
    # identity-orphan query strokes (no same-identity support) + leftover support strokes: parse cost
    total += PARSE_COST * (nq - matched_q)                  # unmatched query strokes
    total += PARSE_COST * (ns - len(used_s))                # unmatched support strokes
    return total


def classify(query_strokes, query_labels, support_parsed):
    """Classify a query by stable-parse + per-stroke-geometry AbS: argmin over candidates of the
    stable-correspondence geometric score. support_parsed = [(strokes, labels), ...]. Pure held-Term
    inversion (held medoid labels + held geometric warp) — no learned feature, no Gemma, no LLM."""
    scores = [stable_correspondence_score(query_strokes, query_labels, ss, sl)
              for (ss, sl) in support_parsed]
    return int(_np.argmin(scores)), scores
