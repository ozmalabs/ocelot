"""analysis_by_synthesis — recognize by INVERTING the agent's OWN generative model (BPL-faithful),
NOT a learned feature. graph-native, earn-not-borrow, donkey=0.

THE BPL INVERSION: BPL recognizes a character by finding which class's generative PROGRAM best
explains the query — render-and-compare in the generated shape space (shape-context + TPS warping),
NOT a learned discriminative feature. The jabberwock ALREADY HOLDS the generator (segmenter/parser
dd171c02, writer-physics motor eae5048b, allographic Substitute ea55902d, shape-math). This wires
the generator into recognition via the held deformation/shape distances.

TWO modes (both held Terms; no learned feature, no borrowed net):
  RENDER-AND-COMPARE (the strong one): each char -> its normalized stroke POINT-SET (the rendered
    program); classify by the held ShapeContextDist + TpsDeformDist (BPL's two-stage render score) —
    the class whose rendered program best matches (lowest deformation distance) wins. Style-factored
    by translation+scale normalization + the deformation metric's own warp tolerance.
  PROGRAM-SPACE (the cheap one): parse into part-shapes (held segmenter), compare programs via held
    StructSim. (Weaker — alignment-brittle; kept for completeness.)

numpy is used ONLY as a world-adapter to load + normalize + resample the trace into a point-set
(flagged); the COMPARISON (the recognition decision) is HELD Rust Terms (ShapeContextDist /
TpsDeformDist / StructSim). No learned feature is computed; recognition is INVERSION, not lookup.

Superseded (2026-07-02) by the graph-resident stroke codebook + segmentation-by-recognition
decode for handwriting: domains/stroke_codebook.py + domains/ink_decode.py (design
scratchpad/HANDWRITING_DESIGN.md). No behavior change here; this module is unmodified otherwise.
"""
from __future__ import annotations
import numpy as _np                 # ADAPTER: load/normalize/resample the trace point-set
import substrate_rs as _srs
import domains.omniglot_world as _ow
import domains.trace_segmenter as _ts

_S = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}
_WILD = "·?·"


def point_set(path, N=80):
    """ADAPTER: a trace -> a normalized, resampled stroke POINT-SET (the rendered program in shape
    space). Translation+scale normalized (factors out position+size = style); orientation KEPT
    (Omniglot chars have canonical orientation). numpy only; no learned feature."""
    strokes = _ow.load_strokes(path)
    pts = []
    for st in strokes:
        pts.extend([list(map(float, p)) for p in st])
    a = _np.asarray(pts, float)
    if len(a) < 3:
        return None
    a = a - a.mean(0)
    a = a / (_np.abs(a).max() + 1e-9)
    d = _np.sqrt((_np.diff(a, axis=0) ** 2).sum(1))
    cum = _np.concatenate([[0.0], _np.cumsum(d)])
    if cum[-1] == 0:
        return None
    u = _np.linspace(0.0, cum[-1], N)
    return _np.stack([_np.interp(u, cum, a[:, 0]), _np.interp(u, cum, a[:, 1])], 1).tolist()


def _dist(qa, sa, term):
    """A held deformation/shape distance between two point-sets (the render-and-compare score)."""
    return float(_S.evaluate({"type": term, "a": _L(qa), "b": _L(sa)}, {}))


def render_compare_score(query_ps, support_ps):
    """BPL's two-stage render-and-compare: ShapeContextDist + TpsDeformDist (held Terms). LOWER =
    the candidate's rendered program better explains the query. The recognition decision is the
    held metric's, not a learned feature."""
    if query_ps is None or support_ps is None:
        return float("inf")
    sc = _dist(query_ps, support_ps, "ShapeContextDist")
    tp = _dist(query_ps, support_ps, "TpsDeformDist")
    return sc + tp


def classify_render(query_ps, support_sets):
    """Classify a query by inverting the generator: argmin over candidates of the render-and-compare
    score. Returns the winning index. Pure held-Term inversion — no learned feature."""
    scores = [render_compare_score(query_ps, s) for s in support_sets]
    return int(_np.argmin(scores)), scores


# ---- program-space (cheap, weaker) — parse + StructSim over part-shapes ----

def program_signature(path, K=6, M=6):
    """Parse the trace into K fixed part-shapes (turn profiles = the residual-recurrence law),
    style-factored (rotation-relative turns). The generative PROGRAM as a relation-system."""
    strokes = _ow.load_strokes(path)
    pts = []
    for st in strokes:
        pts.extend([list(map(float, p)) for p in st])
    a = _np.asarray(pts, float)
    if len(a) < 4:
        return None
    d = _np.sqrt((_np.diff(a, axis=0) ** 2).sum(1))
    cum = _np.concatenate([[0.0], _np.cumsum(d)])
    if cum[-1] == 0:
        return None
    u = _np.linspace(0.0, cum[-1], K * M + 1)
    rs = _np.stack([_np.interp(u, cum, a[:, 0]), _np.interp(u, cum, a[:, 1])], 1)
    d2 = _np.diff(rs, axis=0)
    ang = _np.arctan2(d2[:, 1], d2[:, 0])
    turn = _np.concatenate([_np.diff(_np.unwrap(ang)), [0.0]])
    return [list(turn[i * M:(i + 1) * M]) for i in range(K)]


def program_score(query_prog, support_prog):
    """Held StructSim over the two programs (soft part-shape match). HIGHER = better program match."""
    if query_prog is None or support_prog is None:
        return -1.0
    return float(_S.evaluate({"type": "StructSim", "a": _L(query_prog), "b": _L(support_prog),
                              "wild": _WILD}, {}))


def classify_program(query_prog, support_progs):
    scores = [program_score(query_prog, s) for s in support_progs]
    return int(_np.argmax(scores)), scores
