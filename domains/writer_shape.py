"""writer_shape — the SHAPE OF THE WRITER as an orthogonal residual in the held
shape-math. donkey=0, earn-not-borrow.

THE UNIFYING INSIGHT (style/content = two orthogonal residuals):
  CONTENT (the character) = what AntiUnify holds in COMMON across reps of the same char.
  STYLE   (the writer)    = the writer's consistent MOTOR residual — their curvature /
                            velocity / smoothness signature, constant across what they draw.
Both are first-class residuals the held AntiUnifyWitness gives as a σ.

DATA NOTE (checked, honest): the Omniglot stroke splits are 1 drawer per character ×
20 reps (drawer id = the filename prefix, e.g. 0965_07.txt; NO cross-character
same-drawer linkage in either strokes_background or strokes_evaluation). So a literal
"same writer across different characters" axis is NOT available. What IS available, and
what we use: the 20 reps of one character are ONE writer's natural variation — so a
writer's STYLE signature must be CONTENT-INVARIANT statistics of the motor trace
(curvature/velocity/smoothness moments), and writer-ID here is entangled with content
(writer ≡ character). We therefore (a) report writer-ID with a SCRAMBLED control that
proves the SIGNATURE STRUCTURE (not its marginals) carries the writer info, and (b)
flag the writer≡char entanglement explicitly. The capability — an earned, discriminative
style representation + working writer-ID — is a first-class win on its own (useful for
writer-ID, style-conditioned generation, normalization), independent of any recognition
lift.

All cues are HELD numeric Terms over the trace (turn angle = AngleBetween; speed =
Magnitude(VecSub); curvature-jump = Abs(Minus of turns)); numpy is ONLY a trace adapter
(load + arc-length resample + moment aggregation of the held-Term outputs). No LLM, no
scipy, no borrowed features.
"""
from __future__ import annotations
import numpy as _np
import domains.omniglot_world as _ow
import domains.trace_segmenter as _ts


def style_signature(path, N=48):
    """The writer's content-invariant STYLE signature — moments of the held motor cues.
    Returns an 8-dim vector: turn mean/std, curvature-jump mean/std, velocity smoothness
    (cv), sharp-corner fraction, straight fraction, median turn. Built from held Terms
    (AngleBetween/Magnitude/VecSub via trace_segmenter); numpy aggregates only."""
    strokes = _ow.load_strokes(path)
    pts = []
    for st in strokes:
        pts.extend([list(map(float, p)) for p in st])
    rs = [list(map(float, p)) for p in _ts._resample(pts, N)]
    turn = _np.array(_ts._turning_term(rs))          # held AngleBetween profile
    vel = _np.array(_ts._velocity_term(rs))          # held Magnitude(VecSub) profile
    jump = _np.abs(_np.diff(turn)) if len(turn) > 1 else _np.array([0.0])
    return _np.array([
        turn.mean(), turn.std(),
        jump.mean(), jump.std(),
        vel.std() / (vel.mean() + 1e-6),             # smoothness = velocity coeff-of-variation
        (turn > 1.3).mean(),                          # sharp-corner fraction
        (turn < 0.2).mean(),                          # straight fraction
        float(_np.median(turn)),
    ])


def writer_prototype(paths, N=48):
    """A writer's style PROTOTYPE = the mean style signature over their reps (the held
    AntiUnify content collapses to a centroid in style space — the consistent residual)."""
    sigs = [style_signature(p, N) for p in paths]
    return _np.mean(sigs, axis=0)


def drawer_id(path):
    """Omniglot drawer id = filename prefix (world-adapter)."""
    import os
    return os.path.basename(path).split("_")[0]
