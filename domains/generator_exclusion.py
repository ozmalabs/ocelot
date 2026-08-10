"""Brick 6 — RECURSIVE self-improvement (turn 3): EXCLUSION (the Γ boundary)
vs the SIMILARITY guide (the fuzzy interior) that plateaued.

Turn 1 added a distance-to-target guide — the fuzzy INTERIOR, "how close is a
term" — and it moved the bound ONCE. Turn 2 showed it does NOT compound:
enriching the same positive signal saturates (similarity is the interior, and
the interior is bounded).

The thesis under test (the (G,Γ) admissibility thesis applied to the generator's
OWN search): a structure is defined by EXCLUSION — what a solution is NOT — and
exclusions ACCUMULATE across problems (each one permanently removes a region of
the production space). So exclusion should COMPOUND where similarity flatlined:
problem N is searched with the Γ learned from problems 1..N-1.

This module builds TWO distinct kinds of exclusion (kept separate so their
miss-costs can be measured independently):

  1. SOUND exclusions — provable from the target/types; never rule out a real
     solution. Soundness = zero added misses, verified empirically.
       - DOMINANCE: a partial term already at least as large as the best known
         solution cannot be a PROPER sub-term of anything smaller, so it cannot
         lead to a strictly-smaller solution. (Brick-6 returns the FIRST/smallest
         hit; once we know a solution of size m exists, terms of size >= m that
         are not themselves the solution are dead as building blocks.)
       - INTEGER-UNREACHABLE: for all-integer targets, a term whose output is
         non-integer AND cannot be repaired to the integer target by the
         remaining size budget under the available ops. We take the CONSERVATIVE
         version: only the canonical observational-equivalence prune is fully
         sound here; we add a *checked* integer-distance dominance that we VERIFY
         adds zero misses, and disable it otherwise.

  2. LEARNED exclusions — the COMPOUNDING part, statistical, harvested across
     SOLVED problems per target-CLASS. A class = a signature of target
     properties (arity, output sign/parity/monotonicity, #distinct outputs). A
     structural pattern (an operator, a constant magnitude, a 2-op sub-shape)
     that is RARE-OR-ABSENT in the solutions of a class becomes a
     `GeneratorExclusion{class, pattern, evidence}` graph node. These HARD-prune
     (drop any term CONTAINING an excluded pattern) and ACCUMULATE across the
     sequence — the agent's learned Γ for the class.

Graph-resident: exclusions are GeneratorExclusion nodes (mirrors the existing
DesignExclusion / LanguageExclusion shapes). Weightless: structural patterns +
counts, no trained net, no LLM.

ADDITIVE: brick-6 `exclude=None` and the turn-1/turn-2 guides are untouched.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from domains.generator import _signature, _num, synthesize
from domains.generator_self_improve import (
    _subterm_dicts, _term_from_dict,
)


# ===========================================================================
# TARGET CLASS — the signature of target properties an exclusion is scoped to.
# Two problems share a class iff they share this signature. Learned exclusions
# only transfer WITHIN a class (Γ for that class).
# ===========================================================================

def target_class(examples: Sequence[tuple[dict, Any]]) -> str:
    """A compact, hashable description of the target's output PROPERTIES.

    arity        — coarse bucket of the number of distinct input variables
                   (small=<=2, med=3-4, big>=5). Coarse on purpose: the
                   operator-level exclusions ("Div is useless for integer
                   arithmetic") are arity-INDEPENDENT, so a*b+c (arity 3) and
                   a*a+b (arity 2) must share a class for Γ to TRANSFER. Keying
                   on exact arity would put every problem in its own class and
                   kill the compounding the thesis is about.
    sign         — all outputs >=0 (nonneg) / all <=0 / mixed
    parity       — all even / all odd / mixed (only meaningful for integers)
    integer      — all outputs integer-valued

    Deliberately does NOT include #distinct-outputs or other example-dependent
    richness measures: those vary with the specific spec rows chosen, not with
    which OPERATORS are admissible, so including them would fragment the class
    and stop Γ from transferring. The class names exactly the properties that
    scope which structural patterns can appear in a solution.
    """
    envs = [env for env, _ in examples]
    outs = [_num(o) for _, o in examples]
    var_names: list[str] = []
    for env in envs:
        for k in env:
            if k not in var_names:
                var_names.append(k)
    n_vars = len(var_names)
    arity = "sm" if n_vars <= 2 else ("md" if n_vars <= 4 else "bg")

    all_int = all(abs(o - round(o)) < 1e-9 for o in outs)
    nonneg = all(o >= -1e-9 for o in outs)
    nonpos = all(o <= 1e-9 for o in outs)
    sign = "nonneg" if nonneg else ("nonpos" if nonpos else "mixed")

    if all_int:
        ints = [int(round(o)) for o in outs]
        all_even = all(i % 2 == 0 for i in ints)
        all_odd = all(i % 2 != 0 for i in ints)
        parity = "even" if all_even else ("odd" if all_odd else "mixed")
    else:
        parity = "na"

    return (f"arity={arity}|int={int(all_int)}|sign={sign}|parity={parity}")


# ===========================================================================
# STRUCTURAL PATTERNS of a Term — the vocabulary an exclusion is over.
#
# A pattern is a small, hashable structural feature. Mining looks at which
# patterns appear in the SUB-TERMS of solutions for a class, and which appear
# only in the explored-but-never-useful set. Patterns:
#   ("op", NAME)            — operator NAME appears anywhere
#   ("bigconst", k)         — a Lit with |value| >= k appears (k in {3,4,5})
#   ("shape", (P,C))        — a parent op P with a direct child op/leaf C
# These are deliberately coarse + conservative: a pattern excluded must be
# ABSENT from every solution sub-term in the class.
# ===========================================================================

_LEAF_TAG = {"Var": "Var", "Lit": "Lit"}
_BIG_THRESHOLDS = (3, 4, 5)


def _child_dicts(d: dict) -> list[dict]:
    kids = []
    for kid in d.get("items", []) or []:
        kids.append(kid)
    for key in ("a", "b", "arg", "cond", "then", "other"):
        kid = d.get(key)
        if isinstance(kid, dict):
            kids.append(kid)
    return kids


def _node_token(d: dict) -> str:
    t = d.get("type", "?")
    return t


def term_patterns(d: dict) -> set:
    """All structural patterns present in term dict `d` (and its sub-terms)."""
    pats: set = set()
    for sub in _subterm_dicts(d):
        t = _node_token(sub)
        if t not in _LEAF_TAG:
            pats.add(("op", t))
        if t == "Lit":
            v = sub.get("value")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                for k in _BIG_THRESHOLDS:
                    if abs(v) >= k:
                        pats.add(("bigconst", k))
        # 2-op sub-shape: parent op + each direct child's op/leaf token
        if t not in _LEAF_TAG:
            for kid in _child_dicts(sub):
                ck = _node_token(kid)
                pats.add(("shape", (t, ck)))
    return pats


# ===========================================================================
# SOUND exclusions — never miss a real solution. Verified empirically.
# ===========================================================================

def make_sound_exclude(best_known_size: int | None,
                       all_integer_target: bool):
    """Build a SOUND exclude(term, sig, target)->bool.

    DOMINANCE: if we already know a solution exists at size m (best_known_size),
    any non-matching term of size >= m is useless as a building block: composing
    it into anything yields size > m, and brick-6 already enumerates size<=m
    fully before that. (Matching terms are never passed here — register() checks
    the target first.) This is provably sound for finding the MINIMAL solution.

    The exclude hook does not receive `size`; we recover it from the term dict.
    """
    def exclude(term, sig, target) -> bool:
        if best_known_size is not None:
            d = term.to_dict() if hasattr(term, "to_dict") else term
            sz = _term_size(d)
            if sz >= best_known_size:
                return True  # dominated: cannot lead to a strictly-smaller sol
        return False
    return exclude


def _term_size(d: dict) -> int:
    return 1 + sum(_term_size(k) for k in _child_dicts(d))


# ===========================================================================
# LEARNED exclusions — the compounding bet. Mined across solved problems of a
# class; stored as GeneratorExclusion graph nodes; HARD-prune containing terms.
# ===========================================================================

def _solution_subterm_sigs_and_pats(substrate, solution_term, envs):
    """The patterns present in a solution and all its sub-terms (the USEFUL
    structural vocabulary for this solved problem)."""
    sol_dict = solution_term.to_dict()
    return term_patterns(sol_dict)


def record_solution_patterns(substrate, cls: str, solution_term) -> None:
    """Mark every pattern that DID appear in this class's solution as 'seen in a
    solution' — a SolutionPattern graph node. Learned exclusions may only target
    patterns NEVER recorded here (conservative: absent from every solution)."""
    pats = term_patterns(solution_term.to_dict())
    existing = {}
    for n in substrate.nodes("SolutionPattern"):
        a = substrate.node(n)["attrs"]
        existing[(a.get("cls"), a.get("pattern"))] = n
    for p in pats:
        key = (cls, repr(p))
        if key in existing:
            nid = existing[key]
            a = substrate.node(nid)["attrs"]
            substrate.set_attr(nid, "count", int(a.get("count", 0)) + 1)
        else:
            substrate.add_node("SolutionPattern", {
                "cls": cls, "pattern": repr(p), "count": 1,
                "origin": "generator_exclusion",
            })


def _solution_patterns_for_class(substrate, cls: str) -> set:
    out = set()
    for n in substrate.nodes("SolutionPattern"):
        a = substrate.node(n)["attrs"]
        if a.get("cls") == cls:
            out.add(a.get("pattern"))
    return out


# Universe of candidate patterns to consider excluding. Mirrors term_patterns'
# vocabulary but enumerated so we can name patterns NEVER seen in any solution.
def _candidate_pattern_universe(ops: Sequence[str]) -> list:
    cands: list = []
    for op in ops:
        cands.append(("op", op))
    for k in _BIG_THRESHOLDS:
        cands.append(("bigconst", k))
    # 2-op shapes: parent op x child op/leaf
    child_tokens = list(ops) + ["Var", "Lit"]
    for p in ops:
        for c in child_tokens:
            cands.append(("shape", (p, c)))
    return cands


def learn_exclusions(substrate, cls: str, explored_pattern_counts: dict,
                     ops: Sequence[str], min_evidence: int = 2) -> list:
    """Mine LEARNED exclusion candidates for `cls`.

    A candidate pattern is an exclusion iff:
      - it was EXPLORED (appears in the not-useful frontier) with evidence
        >= min_evidence across the class's solved problems, AND
      - it is ABSENT from EVERY recorded solution of the class (conservative —
        never exclude a pattern seen in any solution).

    Stores each as a GeneratorExclusion graph node (idempotent; bumps evidence).
    Returns the list of (pattern, evidence) newly-known for the class.
    """
    sol_pats = _solution_patterns_for_class(substrate, cls)
    universe = _candidate_pattern_universe(ops)

    # existing exclusions for this class
    existing = {}
    for n in substrate.nodes("GeneratorExclusion"):
        a = substrate.node(n)["attrs"]
        if a.get("cls") == cls:
            existing[a.get("pattern")] = n

    learned = []
    for pat in universe:
        rep = repr(pat)
        if rep in sol_pats:
            continue  # appeared in a solution -> NEVER exclude (conservative)
        ev = explored_pattern_counts.get(pat, 0)
        if ev < min_evidence:
            continue  # not enough evidence it's explored-but-useless
        if rep in existing:
            nid = existing[rep]
            a = substrate.node(nid)["attrs"]
            substrate.set_attr(nid, "evidence", int(a.get("evidence", 0)) + ev)
        else:
            substrate.add_node("GeneratorExclusion", {
                "cls": cls, "pattern": rep, "evidence": ev,
                "origin": "generator_exclusion",
            })
        learned.append((pat, ev))
    return learned


def excluded_patterns_for_class(substrate, cls: str) -> set:
    """The accumulated learned Γ for a class: the set of excluded patterns."""
    out = set()
    for n in substrate.nodes("GeneratorExclusion"):
        a = substrate.node(n)["attrs"]
        if a.get("cls") == cls:
            out.add(_parse_pattern(a.get("pattern")))
    return out


def _parse_pattern(rep: str):
    # patterns are tuples of str/int/nested-tuple; repr round-trips via eval on a
    # tiny, fully-controlled vocabulary (no untrusted input).
    return eval(rep, {"__builtins__": {}}, {})


# ===========================================================================
# The EXCLUSION GUIDE — SOUND exclusions ALWAYS + accumulated LEARNED Γ for the
# target's class. This is the exclude(term, sig, target) the synthesizer drops.
# ===========================================================================

def make_exclude(substrate, examples, ops, best_known_size=None,
                 use_sound=True, use_learned=True):
    """Compose the admissibility-grammar exclude hook for this target.

    SOUND part (always, if use_sound): dominance by best_known_size.
    LEARNED part (if use_learned): drop any term containing an excluded pattern
      from the target's class — the accumulated Γ.
    """
    cls = target_class(examples)
    all_int = "int=1" in cls
    sound = make_sound_exclude(best_known_size, all_int) if use_sound else None
    learned = excluded_patterns_for_class(substrate, cls) if use_learned else set()

    def exclude(term, sig, target) -> bool:
        if sound is not None and sound(term, sig, target):
            return True
        if learned:
            d = term.to_dict() if hasattr(term, "to_dict") else term
            pats = term_patterns(d)
            if pats & learned:
                return True
        return False

    return exclude, {"cls": cls, "n_learned": len(learned),
                     "learned": sorted(repr(p) for p in learned),
                     "sound_dominance": best_known_size}


# ===========================================================================
# Harvesting explored-but-useless pattern counts from a solved problem's trace.
# Returns {pattern: count} for patterns in NON-solution explored terms.
# ===========================================================================

def harvest_explored_patterns(substrate, solve_result, envs) -> dict:
    """From a solved synthesize() result (return_trace=True), count structural
    patterns appearing in EXPLORED distinct-behaviour terms that are NOT in the
    solution's sub-terms. These are the 'explored-but-never-useful' patterns —
    candidates for class-learned exclusions."""
    if not solve_result.get("fits"):
        return {}
    sol_pats = term_patterns(solve_result["term"].to_dict())
    counts: dict = {}
    trace = solve_result.get("trace", {})
    for sig, (size, term) in trace.items():
        d = term.to_dict() if hasattr(term, "to_dict") else term
        for p in term_patterns(d):
            if p in sol_pats:
                continue  # this pattern WAS useful here
            counts[p] = counts.get(p, 0) + 1
    return counts
