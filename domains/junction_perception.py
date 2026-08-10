"""junction_perception — RICHER sub-stroke RELATION perception (admissible
world-adapter I/O). Cheap O(1)-per-pair geometric detectors that translate the
motor TRACE into TYPED, confidence-scored, attributed relation EDGES on the
relation-graph the held order-invariant binder already consumes. NO algebra
change, NO reasoning, NO decision-if over graph state — purely geometric
translation trace→graph, the SAME category as the held stroke_relations
perception (relation_feats).

The held perception (relation_feats) gives only {end-junction, along/T, free} at
each part's own endpoints, on thin Omniglot traces — mostly free/end. This adds
the two families the grounding converges on, each an O(1) test per sub-stroke
pair (whole pass O(n²) over a handful of parts):

  TOPOLOGICAL contact set:
    • contact (point-to-segment distance < stroke-width-relative eps; arc-len t
      of nearest point -> start/end/along)
    • X (crossing): segment-segment intersection by the ORIENTATION straddle
      predicate (signed-area / cross-product sign tests, no division), interior
      on both -> crossing
    • T (touch/abut): a contact where one part's ENDPOINT meets another's
      INTERIOR (occluder/occluded) — T vs X disambiguated by interior-vs-endpoint
  ABSTRACT / region set (the IDS operators — strongest cheap+robust+distinctive):
    • contains (enclosure): winding-number of B's centroid vs a closed-ish loop A
    • relative position: sign of bbox-centroid difference -> above/below/left/right

Each detector emits edge(A->B, type, attrs={t, angle, side, confidence}). The
relation per part = the multiset of its typed edges (its structural role) — a
richer relation-pattern the held StructSim/binder discriminates by, additive on
the same edge slot. Topology-first; metrics (angle/offset) ride as SOFT
attributes, not hard keys. Thresholds stroke-width-relative -> scale-invariant.
"""
from __future__ import annotations
import math
import numpy as np


def _pts(stroke) -> np.ndarray:
    return np.asarray(stroke, dtype=float)[:, :2]


def _stroke_width_scale(parts) -> float:
    """A stroke-width-relative length unit: a fraction of the whole-character
    frame diagonal. Makes every threshold scale-invariant (no absolute pixels)."""
    allp = np.vstack([_pts(p) for p in parts])
    diag = float(np.hypot(*(allp.max(0) - allp.min(0))))
    return max(diag, 1e-6)


def _point_seg_dist(pt, a, b):
    """Distance from point pt to segment a-b, plus the arc-length fraction t in
    [0,1] of the nearest point. O(1)."""
    ab = b - a
    L2 = float(ab @ ab)
    if L2 < 1e-12:
        return float(np.hypot(*(pt - a))), 0.0
    t = float(((pt - a) @ ab) / L2)
    t = min(1.0, max(0.0, t))
    proj = a + t * ab
    return float(np.hypot(*(pt - proj))), t


def _min_endpoint_to_polyline(ep, poly):
    """Nearest distance from endpoint ep to polyline poly, with the nearest
    segment's interior-vs-endpoint flag + global arc-len fraction. O(|poly|)."""
    best_d, best_t, best_interior = float("inf"), 0.0, False
    n = len(poly)
    for k in range(n - 1):
        d, t = _point_seg_dist(ep, poly[k], poly[k + 1])
        if d < best_d:
            best_d = d
            seg_frac = (k + t) / (n - 1)
            best_t = seg_frac
            # interior iff not at the very ends of the whole polyline
            best_interior = 0.12 < seg_frac < 0.88
    return best_d, best_t, best_interior


def _orient(p, q, r) -> float:
    """Signed area (z of cross product) of (q-p)x(r-p). Sign = orientation. O(1)."""
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def _segments_cross(p1, p2, p3, p4) -> bool:
    """Do segments p1p2 and p3p4 properly straddle (cross)? Orientation/straddle
    predicate — sign tests only, no division. O(1)."""
    d1 = _orient(p3, p4, p1)
    d2 = _orient(p3, p4, p2)
    d3 = _orient(p1, p2, p3)
    d4 = _orient(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _polylines_cross_interior(A, B):
    """Any interior segment-pair crossing between polylines A and B (mid-segment,
    neither at a shared endpoint)? Returns (crossed, ti, tj) arc-len fractions."""
    na, nb = len(A), len(B)
    for i in range(na - 1):
        for j in range(nb - 1):
            if _segments_cross(A[i], A[i + 1], B[j], B[j + 1]):
                ti = (i + 0.5) / (na - 1)
                tj = (j + 0.5) / (nb - 1)
                # interior on BOTH (not at the polyline ends) = a true X
                if 0.1 < ti < 0.9 and 0.1 < tj < 0.9:
                    return True, ti, tj
    return False, 0.0, 0.0


def _winding_inside(pt, loop) -> bool:
    """Is pt inside the (closed-ish) polyline loop? Ray-cast parity. O(|loop|).
    Treated as closed by joining last->first."""
    n = len(loop)
    if n < 3:
        return False
    inside = False
    x, y = float(pt[0]), float(pt[1])
    j = n - 1
    for i in range(n):
        xi, yi = float(loop[i][0]), float(loop[i][1])
        xj, yj = float(loop[j][0]), float(loop[j][1])
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def _is_loopish(poly, scale) -> bool:
    """Does the polyline (near-)close on itself (endpoints meet)? cheap O(1)."""
    return float(np.hypot(*(poly[0] - poly[-1]))) < 0.25 * scale


def relation_edges(parts) -> list[dict]:
    """The enriched relation perception: a list of TYPED, confidence-scored edges
    over the sub-stroke parts. Each edge = {src, tgt, type, attrs}. Mechanical
    geometric translation; no decision over graph state.

    Edge types: contact / T / X / contains / above / below / left / right.
    src/tgt are part indices (0-based). attrs carry t (arc-len), angle, side,
    confidence (all SOFT — quantized attributes, not hard keys)."""
    polys = [_pts(p) for p in parts if _pts(p).shape[0] >= 2]
    n = len(polys)
    if n == 0:
        return []
    scale = _stroke_width_scale(parts)
    eps = 0.10 * scale                       # stroke-width-relative contact threshold
    cents = [poly.mean(0) for poly in polys]
    edges: list[dict] = []

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            A, B = polys[i], polys[j]

            # --- RELATIVE POSITION (ordinal, bbox-centroid sign) — always available ---
            dx = float(cents[j][0] - cents[i][0])
            dy = float(cents[j][1] - cents[i][1])
            if abs(dx) >= abs(dy):
                rtype = "right" if dx > 0 else "left"
                conf = min(1.0, abs(dx) / (0.5 * scale + 1e-9))
            else:
                rtype = "below" if dy > 0 else "above"   # +y downward in image frame
                conf = min(1.0, abs(dy) / (0.5 * scale + 1e-9))
            edges.append({"src": i, "tgt": j, "type": rtype,
                          "attrs": {"confidence": round(conf, 3)}})

            # --- CONTAINMENT (winding) — B inside a loopish A ---
            if _is_loopish(A, scale) and _winding_inside(cents[j], A):
                edges.append({"src": i, "tgt": j, "type": "contains",
                              "attrs": {"confidence": 1.0}})

            # only test contact/T/X for j>i to avoid double-emitting symmetric edges
            if j <= i:
                continue

            # --- X (crossing): interior segment crossing, neither terminating ---
            crossed, ti, tj = _polylines_cross_interior(A, B)
            if crossed:
                edges.append({"src": i, "tgt": j, "type": "X",
                              "attrs": {"ti": round(ti, 3), "tj": round(tj, 3), "confidence": 1.0}})
                continue

            # --- contact / T : an endpoint of one meets the other ---
            # B's endpoints vs A's polyline, and A's endpoints vs B's polyline
            best = None
            for (ep, host, host_idx, ep_owner) in (
                    (B[0], A, i, j), (B[-1], A, i, j), (A[0], B, j, i), (A[-1], B, j, i)):
                d, t, interior = _min_endpoint_to_polyline(ep, host)
                if d < eps and (best is None or d < best[0]):
                    best = (d, t, interior, host_idx, ep_owner)
            if best is not None:
                d, t, interior, host_idx, ep_owner = best
                conf = round(1.0 - d / eps, 3)
                if interior:
                    # endpoint meets interior -> T (occluder/occluded): ep_owner abuts host_idx
                    edges.append({"src": ep_owner, "tgt": host_idx, "type": "T",
                                  "attrs": {"t": round(t, 3), "confidence": conf}})
                else:
                    edges.append({"src": min(i, j), "tgt": max(i, j), "type": "contact",
                                  "attrs": {"t": round(t, 3), "confidence": conf}})
    return edges


def part_relation_signature(n_parts: int, edges: list[dict]) -> list[list[str]]:
    """Per part, the SORTED multiset of its typed relation labels (its structural
    role / relation-pattern) — what the order-invariant binder corresponds by.
    Mechanical aggregation of the typed edges; no decision."""
    sig: list[list[str]] = [[] for _ in range(n_parts)]
    for e in edges:
        s, t, ty = e["src"], e["tgt"], e["type"]
        if 0 <= s < n_parts:
            sig[s].append(f"{ty}>")          # outgoing role
        if 0 <= t < n_parts:
            sig[t].append(f"<{ty}")          # incoming role
    return [sorted(s) for s in sig]
