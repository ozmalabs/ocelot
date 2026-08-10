"""spatial_attention — GENERIC string-spanning SPATIAL-ATTENTION window/gradient (graph-native).

THE LAST COMPONENT (isolated by NEGLECT dyslexia: one SIDE of the string lost, island->land): a
spatial-attention GRADIENT over a spatial extent — each position gets an attention WEIGHT from the
gradient; positions below an attention THRESHOLD DROP. A lesion SHIFTS/STEEPENS the gradient so ONE
SIDE falls below threshold -> LATERALIZED, SIDE-SPECIFIC errors (the neglected side; the other side
intact). GENERIC: any spatially-arranged items.

THE NEW AXIS (separate from all 4 built): the failure is SPATIAL-SIDE (lateralized — left/right, set
by the gradient SLOPE) — NOT length (buffer), NOT flankers (position-binding), NOT case (allographic),
NOT form (motor). FLIP the gradient slope -> FLIP the neglected side. Length never enters the gate.

MECHANISM (held Terms): attention weight at position p = base + slope*p (a linear gradient; held
Plus/Times). The held Gt(weight, threshold) decides whether position p is ATTENDED. lesion -> a
non-zero slope tilts attention to one side; the low-attention SIDE drops. The variable is SPATIAL
SIDE (slope sign), orthogonal to length and flankers.

ALL decisions are HELD Terms (Plus/Times gradient, Gt gate) run by the Rust evaluator; Python only
lays out positions (adapter) + scores drops in the gate. No LLM.
"""
from __future__ import annotations
import substrate_rs as _srs

_S = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}


def _ev(term, env=None):
    return _S.evaluate(term, env or {})


def weight_term(base, slope, position):
    """HELD attention weight at a position = base + slope*position (a linear spatial gradient).
    slope<0 -> attention falls toward the RIGHT (high positions neglected); slope>0 -> toward the
    LEFT (low positions neglected); slope=0 -> flat (fully attended). Length never enters."""
    return {"type": "Plus", "items": [_L(float(base)),
                                      {"type": "Times", "items": [_L(float(slope)), _L(float(position))]}]}


def attend_gate_term(base, slope, position, threshold):
    """HELD attend decision: position is ATTENDED iff its gradient weight exceeds the threshold.
    Gt over the weight term — the Rust evaluator decides; below-threshold positions DROP."""
    return {"type": "Gt", "a": weight_term(base, slope, position), "b": _L(float(threshold))}


def drop_prob_term(base, slope, position, threshold, sharp=8.0):
    """GRADED drop probability (the refinement of the binary gate): a held LOGISTIC of
    (threshold - weight), 1/(1+exp(-sharp*(thr-weight))). Smooth in the gradient weight — the drop
    likelihood rises gradually as a position's attention falls toward/below threshold, instead of the
    binary Gt step. All held Terms (Exp/Neg/Plus/Div). High on the neglected side, low on the attended."""
    w = weight_term(base, slope, position)
    margin = {"type": "Minus", "a": _L(float(threshold)), "b": w}
    z = {"type": "Times", "items": [_L(float(sharp)), margin]}
    return {"type": "Div", "a": _L(1.0),
            "b": {"type": "Plus", "items": [_L(1.0), {"type": "Exp", "arg": {"type": "Neg", "arg": z}}]}}


class SpatialAttention:
    """A string-spanning spatial-attention window. base/slope define the gradient; threshold the
    attention floor. slope=0 (intact) attends everything; slope!=0 (neglect lesion) tilts attention
    to one side so the OTHER side drops -> lateralized side-specific errors. FLIP slope -> FLIP side.

    The gradient is SPATIAL: it depends on POSITION, not length/flankers/case/form (the new axis)."""

    def __init__(self, base=1.0, slope=0.0, threshold=0.3):
        self.base = base
        self.slope = slope
        self.threshold = threshold

    def attended(self, position):
        """Is `position` above the attention floor? (held Gt over the held gradient weight)."""
        return bool(_ev(attend_gate_term(self.base, self.slope, position, self.threshold)))

    def read(self, items):
        """Read a spatially-arranged item sequence THROUGH the attention window. Positions whose
        held attention weight falls below threshold DROP (a neglect error). Returns the recalled
        items + the dropped positions. With a tilted gradient, drops are LATERALIZED to one side."""
        recalled, dropped = [], []
        for pos, it in enumerate(items):
            if self.attended(pos):
                recalled.append(it)
            else:
                dropped.append(pos)
        return recalled, dropped

    def dropped_side(self, items):
        """Which SIDE are the drops on? 'left' (low positions), 'right' (high positions), 'none', or
        'both'. The lateralization signature — follows the gradient slope."""
        _, dropped = self.read(items)
        if not dropped:
            return "none"
        n = len(items)
        mid = (n - 1) / 2.0
        left = [p for p in dropped if p < mid]
        right = [p for p in dropped if p > mid]
        if left and not right:
            return "left"
        if right and not left:
            return "right"
        return "both"

    def n_dropped(self, items):
        return len(self.read(items)[1])

    def drop_profile(self, items):
        """GRADED per-position drop PROBABILITY across the string (held logistic of threshold-weight).
        A SMOOTH gradient: high on the neglected side, falling toward the attended side — the human
        graded-neglect shape, not a binary cliff. Returns a list of probabilities by position."""
        return [float(_ev(drop_prob_term(self.base, self.slope, pos, self.threshold)))
                for pos in range(len(items))]

    def expected_dropped(self, items):
        """GRADED expected drop count = sum of per-position drop probabilities (smooth in the gradient)."""
        return sum(self.drop_profile(items))
