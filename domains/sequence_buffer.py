"""sequence_buffer — a DOMAIN-GENERIC sequence working-memory BUFFER (graph-native, donkey=0).

THE MISSING COMPONENT (95ea818d): the dissociation logic named a SEQUENCE WORKING-MEMORY as the
missing central primitive. It is ITEM-AGNOSTIC: the graphemic buffer (letters), the phonological
buffer (sounds), and any sequence-holding store are INSTANCES of ONE generic mechanism. Built once,
generically — serves reading, writing, AND speech.

WHAT IT IS: an ordered store of ABSTRACT ITEMS bound to POSITIONS, CAPACITY-LIMITED / DECAYING.
Items are ANY type (graphemes/phonemes/tokens/parts); the buffer doesn't care. Ops:
  WRITE  load a sequence -> (item, position) bindings, each with a retention STRENGTH.
  HOLD   retain with DECAY/INTERFERENCE: strength = retention^(distance from the read head) (a
         residual-recurrence — the new sequence_order/position_buffer RelationCues name these).
  READ   retrieve item-at-position; retrieval FAILS (-> order/position error) when strength falls
         below a noise threshold, which happens MORE for longer sequences (the defining signature).

THE SIGNATURE (item-type-INDEPENDENT): retrieval error SCALES WITH LENGTH; errors are ORDER/POSITION
(transposition / deletion / insertion / substitution) — exactly graphemic-buffer-disorder.

GRAPH-NATIVE: WRITE/HOLD/READ are HELD Terms (Fold over positions; Pow for decay; comparisons for
the capacity gate) run by the Rust evaluator. numpy is used ONLY as a world-adapter to score
retrieval-vs-truth in the gate (NOT in the buffer mechanism). No LLM. The decay/capacity (not the
data structure) produces the length-signature; an unbounded store (retention=1, no noise) shows none.
"""
from __future__ import annotations
import substrate_rs as _srs

_S = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}
_V = lambda n: {"type": "Var", "name": n}


def _ev(term, env=None):
    return _S.evaluate(term, env or {})


def write_term(items):
    """WRITE: a HELD Fold loading the sequence into (item, position) bindings. Returns the held
    Term that evaluates to a list of [item, position] pairs (item-agnostic — items pass through)."""
    # Fold over an index list, appending [item_at_i, i]. Items supplied as a Lit; positions 0..n-1.
    n = len(items)
    idxs = list(range(n))
    body = {"type": "Append", "seq": _V("acc"),
            "item": {"type": "Vec", "items": [
                {"type": "IndexAt", "seq": _L(list(items)), "index": _V("i")},
                _V("i")]}}
    return {"type": "Fold", "source": _L(idxs), "init": _L([]), "acc_name": "acc", "var_name": "i",
            "body": body}


def strength_term(position, n, retention):
    """HOLD: the retention STRENGTH of the item at `position` in a length-n buffer, read at the end:
    strength = retention ^ (distance from the read head) = retention^(n-1-position). A held Pow over
    a residual-recurrence decay. retention<1 -> earlier items decay more; retention=1 -> no decay."""
    dist = (n - 1) - position
    return {"type": "Pow", "a": _L(float(retention)), "b": _L(float(dist))}


def bowed_strength_term(position, n, retention, primacy=0.7):
    """U-SHAPED SERIAL-POSITION strength (the human bow): the MAX of a RECENCY trace (retention^
    (n-1-pos), strong at the END) and a PRIMACY trace (primacy^pos, strong at the START). Both held
    Pow; held Max. Ends are strong (one trace covers each), the MIDDLE is weakest (both traces low)
    -> error is U-shaped (primacy + recency, medial worst), replacing the recency-only monotone."""
    recency = {"type": "Pow", "a": _L(float(retention)), "b": _L(float((n - 1) - position))}
    prim = {"type": "Pow", "a": _L(float(primacy)), "b": _L(float(position))}
    return {"type": "Max", "items": [recency, prim]}


def bowed_read_term(position, n, retention, threshold, primacy=0.7):
    """READ with the BOWED (U-shaped) strength: retrievable iff bowed-strength > threshold. The held
    Gt over bowed_strength_term — interior positions (weakest) drop first -> medial-worst errors."""
    return {"type": "Gt", "a": bowed_strength_term(position, n, retention, primacy), "b": _L(float(threshold))}


def read_term(position, n, retention, threshold):
    """READ: retrieve the item-at-position IF its held strength exceeds the capacity/noise threshold,
    else FAIL (Lt gate). The held decision: Gt(strength, threshold). Returns a held Bool Term =
    'is the item at this position still retrievable?'."""
    return {"type": "Gt", "a": strength_term(position, n, retention), "b": _L(float(threshold))}


class SequenceBuffer:
    """A generic capacity-limited / decaying sequence working-memory. ITEM-AGNOSTIC.

    retention (0<r<=1): per-position decay base (r<1 = capacity-limited; r=1 = the degenerate
                        unbounded store, the discriminative control).
    threshold:          the noise/capacity floor; an item is RETRIEVABLE iff its strength > threshold.
    All retention/retrieval DECISIONS are HELD Terms (Pow/Gt/Fold) — the Rust evaluator decides."""

    def __init__(self, retention=0.82, threshold=0.18, bowed=False, primacy=0.7):
        self.retention = retention
        self.threshold = threshold
        self.bowed = bowed           # True -> U-shaped serial-position (primacy+recency, medial worst)
        self.primacy = primacy
        self.items = None
        self.n = 0

    def write(self, items):
        """Load a sequence (ANY item-type). The bindings are built by the HELD write Fold."""
        bindings = _ev(write_term(list(items)))      # held Fold -> [[item, pos], ...]
        self.items = [list(b) for b in bindings]
        self.n = len(self.items)
        return self

    def retrievable(self, position):
        """Is the item at `position` still above the capacity/noise floor? (held Gt over held Pow).
        bowed=True uses the U-shaped serial-position curve (primacy+recency); else recency-only."""
        if self.bowed:
            return bool(_ev(bowed_read_term(position, self.n, self.retention, self.threshold, self.primacy)))
        return bool(_ev(read_term(position, self.n, self.retention, self.threshold)))

    def strength(self, position):
        if self.bowed:
            return float(_ev(bowed_strength_term(position, self.n, self.retention, self.primacy)))
        return float(_ev(strength_term(position, self.n, self.retention)))

    def read(self):
        """READ the whole buffer back. Positions whose held strength fell below threshold FAIL and
        produce an ORDER/POSITION error: a failed slot is DROPPED (deletion) and, with the freed
        capacity, the read head MIS-BINDS — the next surviving item slides into the empty slot
        (transposition/shift). Returns the recalled item sequence (item-agnostic)."""
        if self.items is None:
            return []
        survived = []
        for it, pos in self.items:
            if self.retrievable(int(pos)):
                survived.append(it)
            # else: the slot is lost -> the following survivors shift left (position error)
        return survived

    def recall_positions(self):
        """The list of positions whose item survived retrieval (for order/position error scoring)."""
        return [int(pos) for it, pos in (self.items or []) if self.retrievable(int(pos))]
