"""implied_rule — the general IMPLIED-RULE induction faculty.

A domain-agnostic cognitive process (NOT an ARC-AGI solver): given a set of
OBSERVED INSTANCES from some scenario — states, changes, events, any structured
observations — induce the RULE they IMPLY by ANTI-UNIFICATION (least-general
generalization). The implied rule is the most-specific pattern that covers every
instance: where the instances AGREE the rule fixes the value; where they DIFFER
the rule abstracts to a variable (``WILD``). This is induction proper — the rule
the examples logically entail — not random hypothesis sampling, and it is not
domain-specific: it accepts arbitrary scenarios with arbitrary changes. The
agent's win-rule (the rule a game's score follows) is just ONE application; the
same faculty induces "a bird has feathers" from birds or "value V becomes 0" from
a set of cell changes.

The operator is the same generalization ``_discover_invariants`` already performs
(keep the invariant, mark what varied ``independent_of``) — lifted to a general,
recursive least-general-generalization over arbitrary nested structure, so the
agent can apply it to ANY scenario it points it at, dynamically.
"""
from __future__ import annotations

# The abstracted-variable marker: a position whose value VARIED across the
# instances, so the implied rule does not constrain it (it is independent_of it).
WILD = ("·?·",)


def anti_unify(values: list):
    """Least-general generalization over a list of structured VALUES — the core
    implied-rule operator. Recurses through nested dicts / tuples / lists / sets:

      · all equal               → that value (a fixed constant of the rule)
      · all dicts               → a dict over the SHARED keys, each anti-unified
                                  (a key missing from some instance is dropped —
                                  the rule only constrains what all instances have)
      · all tuples/lists, =len  → element-wise anti-unification
      · all sets/frozensets     → the INTERSECTION (the members always present —
                                  the implied "these always hold")
      · otherwise differ        → WILD (abstract the difference to a variable)

    Empty → WILD. One value → itself. Domain-agnostic: the values can be cell
    changes, animal descriptions, sensor readings — anything structured."""
    vals = list(values)
    if not vals:
        return WILD
    first = vals[0]
    if all(v == first for v in vals[1:]):
        return first
    if all(isinstance(v, dict) for v in vals):
        keys = set(vals[0])
        for v in vals[1:]:
            keys &= set(v)
        return {k: anti_unify([v[k] for v in vals])
                for k in sorted(keys, key=repr)}
    if all(isinstance(v, (tuple, list)) for v in vals) and \
            len({len(v) for v in vals}) == 1:
        n = len(vals[0])
        return tuple(anti_unify([v[i] for v in vals]) for i in range(n))
    if all(isinstance(v, (set, frozenset)) for v in vals):
        inter = set(vals[0])
        for v in vals[1:]:
            inter &= set(v)
        return frozenset(inter)
    return WILD


def _wild_paths(pattern, prefix=()) -> list:
    """The paths in an induced pattern that are abstracted (WILD) — i.e. what the
    rule is INDEPENDENT OF (the variables it generalises over)."""
    if pattern == WILD:
        return [prefix]
    out: list = []
    if isinstance(pattern, dict):
        for k in pattern:
            out.extend(_wild_paths(pattern[k], prefix + (k,)))
    elif isinstance(pattern, tuple):
        for i, p in enumerate(pattern):
            out.extend(_wild_paths(p, prefix + (i,)))
    return out


def _fixed_count(pattern) -> int:
    """How many leaf positions the rule FIXES (its specificity / information). A
    more-fixed rule is a stronger, more-compressive claim — the MDL handle for
    ranking competing implied rules."""
    if pattern == WILD:
        return 0
    if isinstance(pattern, dict):
        return sum(_fixed_count(v) for v in pattern.values())
    if isinstance(pattern, tuple):
        return sum(_fixed_count(v) for v in pattern)
    if isinstance(pattern, (set, frozenset)):
        return len(pattern)
    return 1


def covers(pattern, instance) -> bool:
    """Does ``instance`` satisfy the induced rule? WILD matches anything; a dict
    pattern requires its keys to match (instance may have more); a set pattern
    requires its members to be a SUBSET of the instance's. The test by which the
    agent decides the rule APPLIES to a new scenario (and, for a win-rule, whether
    the condition the score follows is now satisfied)."""
    if pattern == WILD:
        return True
    if isinstance(pattern, dict):
        if not isinstance(instance, dict):
            return False
        return all(k in instance and covers(pattern[k], instance[k])
                   for k in pattern)
    if isinstance(pattern, tuple):
        if not isinstance(instance, (tuple, list)) or len(instance) != len(pattern):
            return False
        return all(covers(p, instance[i]) for i, p in enumerate(pattern))
    if isinstance(pattern, (set, frozenset)):
        if not isinstance(instance, (set, frozenset)):
            return False
        return pattern <= set(instance)
    return pattern == instance


def induce_rule(instances: list) -> dict | None:
    """Induce the RULE a set of instances IMPLIES. Returns the generalized
    ``pattern`` (the rule), the ``abstracted`` paths (what it is independent of),
    a ``fixed`` specificity score (MDL rank), and ``support`` (how many instances
    it was induced from). None on no instances. General over any scenario."""
    insts = list(instances)
    if not insts:
        return None
    pattern = anti_unify(insts)
    return {
        "pattern": pattern,
        "abstracted": _wild_paths(pattern),
        "fixed": _fixed_count(pattern),
        "support": len(insts),
    }
