"""position_binding — GENERIC letter-position / slot BINDING (graph-native, donkey=0).

THE COMPONENT (isolated by ATTENTIONAL dyslexia + LETTER-POSITION dyslexia): binds each ITEM to a
(GROUP, POSITION) slot — group = word/string, position = within-group index — keeping items bound to
their OWN group. Under attentional lesion/LOAD with MULTIPLE simultaneous groups, bindings CROSS:
a letter migrates to a FLANKING group at the SAME position (fig|bee -> fib|gee). GENERIC: any items
in grouped positions.

THE KEY DISTINCTION FROM THE BUFFER (what makes it a SEPARATE component):
  buffer          fails LENGTH-SCALED within a SINGLE string (capacity/decay).
  position-binding fails FLANKER-MODULATED MIGRATION between MULTIPLE strings (binding/attention):
                   ISOLATED string -> NO migration; FLANKED -> migration; scales with #flankers /
                   proximity, NOT single-string length. ORTHOGONAL axes -> a double dissociation.

MECHANISM (held Terms): each item holds a BINDING STRENGTH to its own (group,position). A competing
flanking group at the same position exerts COMPETITION = load * (#flankers at that position) /
proximity. The held decision Gt(competition, binding_strength) -> the binding SWAPS group (migration)
at the same position. No length term enters -> migration is flanker-driven, length-independent.

ALL decisions are HELD Terms (Times for competition, Gt for the swap gate) run by the Rust evaluator;
Python only lays out the groups (mechanical adapter) + scores migration-vs-truth in the gate. No LLM.
"""
from __future__ import annotations
import substrate_rs as _srs

_S = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}


def _ev(term, env=None):
    return _S.evaluate(term, env or {})


def competition_term(n_flankers, load, proximity=1.0):
    """HELD competition strength at a position = load * #flankers * proximity. The cross-group pull
    on a binding. Rises with flankers, NOT with single-string length (length never enters)."""
    return {"type": "Times", "items": [_L(float(load)), _L(float(n_flankers)), _L(float(proximity))]}


def migrate_gate_term(n_flankers, load, binding_strength, proximity=1.0):
    """HELD swap decision: the binding MIGRATES (swaps group at the same position) iff competition
    exceeds the binding-strength floor. Gt over the competition term — the Rust evaluator decides."""
    return {"type": "Gt", "a": competition_term(n_flankers, load, proximity), "b": _L(float(binding_strength))}


def migrate_prob_term(n_flankers, load, binding_strength, proximity=1.0, sharp=4.0):
    """GRADED migration probability (the refinement of the binary gate): a held LOGISTIC of
    (competition - binding_floor), 1/(1+exp(-sharp*(comp-floor))). Smooth in competition (rises
    gradually with flankers/load) instead of the binary Gt step. All held Terms (Exp/Neg/Plus/Div)."""
    comp = competition_term(n_flankers, load, proximity)
    margin = {"type": "Minus", "a": comp, "b": _L(float(binding_strength))}
    z = {"type": "Times", "items": [_L(float(sharp)), margin]}
    # 1 / (1 + exp(-z))
    return {"type": "Div", "a": _L(1.0),
            "b": {"type": "Plus", "items": [_L(1.0), {"type": "Exp", "arg": {"type": "Neg", "arg": z}}]}}


class PositionBinder:
    """Binds items -> (group, position) slots across MULTIPLE simultaneous groups, with cross-group
    competition (attention). load=0 (intact) keeps every item in its own group; load>0 (attentional
    lesion) lets bindings at a position SWAP to a flanking group when competition > binding_strength.

    binding_strength: the per-item binding floor (intact attention = strong).
    load:             attentional load / lesion severity (0 = intact)."""

    def __init__(self, binding_strength=0.5, load=0.0):
        self.binding_strength = binding_strength
        self.load = load

    def bind(self, groups):
        """groups = list of item-sequences (e.g. [['f','i','g'], ['b','e','e']]). Returns the bound
        slots [(item, group_id, position)] — the intact binding (each item in its own group)."""
        slots = []
        for gid, seq in enumerate(groups):
            for pos, it in enumerate(seq):
                slots.append((it, gid, pos))
        return slots

    def _pos_binding_strength(self, pos, length):
        """Per-position binding floor: EXTERIOR letters (first/last) bind STRONGER than interior
        (the exterior-letter effect — migrations spare word ends). interior -> the base floor; ends
        -> base + a bonus. Held-comparable scalar; no length-scaling of the COMPETITION (length only
        shapes which positions are 'interior', not the flanker-driven competition itself)."""
        if length <= 1:
            return self.binding_strength + 0.5
        if pos == 0 or pos == length - 1:
            return self.binding_strength + 0.5               # exterior: strongly bound
        return self.binding_strength

    def read(self, groups):
        """Read the groups back THROUGH the binder. With multiple groups and load>0, an item at a
        position whose held migrate-gate fires SWAPS with the item at the SAME position in an
        ADJACENT group (position-preserving cross-group migration). Returns the recalled groups.

        Migration is FLANKER-driven + GRADED: a position migrates iff competition (load*#flankers)
        exceeds THAT position's binding floor (exterior letters bind stronger -> spared). An ISOLATED
        group (no flanker at that position) never migrates. Length never enters the competition."""
        out = [list(g) for g in groups]
        maxlen = max((len(g) for g in groups), default=0)
        for pos in range(maxlen):
            present = [gid for gid, g in enumerate(groups) if pos < len(g)]
            n_flankers = len(present) - 1                      # other groups sharing this position
            if n_flankers < 1:
                continue                                       # isolated at this position -> no migration
            # per-position floor: each present group's own length sets its exterior/interior status.
            # migrate the pair (g0,g1) iff BOTH their position-floors are exceeded (interior positions).
            g0, g1 = present[0], present[1]
            floor = max(self._pos_binding_strength(pos, len(groups[g0])),
                        self._pos_binding_strength(pos, len(groups[g1])))
            if not bool(_ev(migrate_gate_term(n_flankers, self.load, floor))):
                continue
            out[g0][pos], out[g1][pos] = out[g1][pos], out[g0][pos]
        return out

    def migrations(self, groups):
        """Count position-preserving cross-group migrations under the current load (vs intact)."""
        recalled = self.read(groups)
        n = 0
        for gid, g in enumerate(groups):
            for pos, it in enumerate(g):
                if pos < len(recalled[gid]) and recalled[gid][pos] != it:
                    n += 1
        return n

    def expected_migrations(self, groups):
        """GRADED expected migration count = sum of per-position held migration PROBABILITIES (the
        smooth refinement of the binary count). Rises SMOOTHLY with competition (flankers/load) — no
        saturating step. Still flanker-driven (isolated positions contribute 0); length never enters."""
        maxlen = max((len(g) for g in groups), default=0)
        total = 0.0
        for pos in range(maxlen):
            present = [gid for gid, g in enumerate(groups) if pos < len(g)]
            n_flankers = len(present) - 1
            if n_flankers < 1:
                continue
            g0, g1 = present[0], present[1]
            floor = max(self._pos_binding_strength(pos, len(groups[g0])),
                        self._pos_binding_strength(pos, len(groups[g1])))
            total += float(_ev(migrate_prob_term(n_flankers, self.load, floor)))
        return total
