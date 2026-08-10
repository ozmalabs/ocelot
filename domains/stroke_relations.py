"""stroke_relations — the RELATIONS piece of the generative-program faculty (BPL's stroke relations).

BPL's program is parts PLUS relations: how each stroke attaches to the others (its endpoints meet
another stroke's endpoint = an end-junction, meet another stroke's interior = an along/T-junction, or
are free terminals). The relations are the writer-invariant TOPOLOGY that ties the parts into a
character — what distinguishes an 'L' (two parts meeting end-to-end) from a 'T' (one part meeting
another along its middle) even when the metric is similar.

This world adapter computes each canonical part's RELATION SIGNATURE (mechanical geometry, like the
canonical parse): for each of its two endpoints — its position + a 3-way junction type [end / along /
free]. Stored as a Stroke attr; matched by a graph Term (part correspondence over the relation
signature). No decision here — junction detection is perception; the relational MATCH is the graph.
"""
from __future__ import annotations

import numpy as np


def relation_feats(parts, junc_thresh: float = 0.30) -> list[list]:
    """Per canonical part, its RELATION SIGNATURE: for each endpoint, [x, y, is_end_junction,
    is_along_junction, is_free] — does the endpoint meet another part's ENDPOINT (end-junction), its
    INTERIOR (along/T-junction), or nothing (free terminal)? 10-dim (2 endpoints x 5). Parts in the
    shared normalised frame, so junctions are writer-invariant character structure."""
    ps = [np.asarray(p, dtype=float)[:, :2] for p in parts if np.asarray(p).shape[0] >= 2]
    out = []
    for i, p in enumerate(ps):
        feat = []
        for ep in (p[0], p[-1]):
            feat += [float(ep[0]), float(ep[1])]
            best, best_is_end = float("inf"), False
            for j, q in enumerate(ps):
                if j == i:
                    continue
                d2 = ((q - ep) ** 2).sum(axis=1)
                k = int(d2.argmin())
                dk = float(np.sqrt(d2[k]))
                if dk < best:
                    best, best_is_end = dk, (k == 0 or k == q.shape[0] - 1)
            if best < junc_thresh:
                feat += ([1.0, 0.0, 0.0] if best_is_end else [0.0, 1.0, 0.0])
            else:
                feat += [0.0, 0.0, 1.0]
        out.append(feat)
    return out


__all__ = ["relation_feats"]
