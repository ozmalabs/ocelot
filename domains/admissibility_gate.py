"""admissibility_gate — the ONE admissibility gate every grounded / constructed
object passes through, COLLAPSED into the core manifold-confidence-interval-collapse
(domains/verify_collapse.py -> scripts/native_collapse.py).

THE DEFECT THIS FIXES (the per-site disease — "fixing the outcome")
==================================================================
The SAME operation — "does the grounded/constructed object reproduce ALL the
problem's constraints?" — was hand-bolted on (or omitted) per-site:

  · cmsg115 (autonomous_hle_construct_or_stall): math_hat's grounding got a
    HAND-WRITTEN self-check (does the candidate reproduce the description's stated
    properties? are the construction operators all accounted?) — it CAUGHT a
    spurious S^1.
  · cmsg116 (autonomous_hle_construct_y + construction_operators): the CONSTRUCTOR
    had NO such check — it built Y with H_1=Z^2 and did NOT catch that an infinite
    H_1 is INCONSISTENT with the question's own presupposition ("rank of Ker as a
    FREE GROUP" of finite rank REQUIRES [pi_1,pi_1] finite-index, i.e. H_1 FINITE).
    A human caught it by hand.
  · the BG_2 / lattices "verify-vs-known" is the SAME operation a THIRD time (does
    the derived value reproduce a known constraint?).

THREE bolt-ons of ONE operation (missed once). That is fixing the OUTCOME — patching
each site. The SYSTEMIC fix ([[ozma_fix_the_fixer]]) = make EVERY grounded /
constructed object pass through ONE admissibility gate.

THE COLLAPSE IT IS (NOT a 4th hand-check)
=========================================
The gate IS the core loop's manifold-confidence-interval-collapse used as the
admissibility mechanism. A candidate object is ADMITTED only if its forward-model
properties COLLAPSE consistently against ALL the constraints the problem imposes;
the binary verify-vs-known is the DEGENERATE point-collapse (verify_collapse already
delegates math-verify to the native collapse, cmsg99). This module does NOT
re-implement the collapse — it COMPOSES the held native collapse
(verify_collapse.verify_by_collapse) over the union of the problem's constraints:

  (a) the description's STATED properties      (the cmsg115 check)
  (b) the asked-invariant's WELL-DEFINEDNESS    (the cmsg116 gap — derived from the
      PRESUPPOSITIONS                            QUESTION TYPE, e.g. "rank ... as a
                                                 FINITE free group" => H_1 finite)
  (c) the un-accounted CONSTRUCTION residual    (the cmsg115 un-synthesizable ops)

Each constraint contributes ONE entry to the revealed AGREEMENT SEQUENCE the native
collapse contracts over: 1.0 if the object's forward model reproduces the constraint,
0.0 if it BREAKS it (the agent's OWN hard Γ-prune, verify_collapse._agree). The
object is ADMITTED iff the interval FULLY contracts (every constraint satisfied — the
binary verify's pass, the degenerate point-collapse); a single broken constraint
makes the object INADMISSIBLE BY CONSTRUCTION ([[ozma_recognition_is_a_conjunction]]
— admissibility is binary), so you never "spend" on it; the stall NAMES ITSELF.

INTEGRITY (presuppositions DERIVED from the QUESTION, never a regex, never the answer)
=====================================================================================
`presuppositions_from_question` DERIVES the well-definedness constraints — it does
NOT string-match the raw question (the old `_is_finite_free_group_rank_question`
regex + the hard-coded `h1_free_rank == 0` are GONE). It delegates to
domains/presupposition_derivation, which COMPREHENDS the asked invariant via the
HELD general reader (construction_grammar.comprehend_structure -> the typed term
free_rank OF kernel OF Hurewicz — STRUCTURE, so a paraphrase fires), ACQUIRES the
needed general theorems by READING them as Claims (Ker(Hurewicz)=[pi1,pi1];
finite-free-rank => finite index; index=|H_1|), and CHAINS them through the
DERIVATION ENGINE to the constraint H_1 finite (free rank 0). The conclusion is the
engine's checkable output, NOT an assertion; an un-grounded fact STALLS at a named
residual, never hard-coded. The answer is read ONLY at the end, to verify; it is
NEVER fed into the gate.

THE NAMED RESIDUAL (constraint-derivation breadth)
==================================================
The gate is SYSTEMIC (one mechanism). Its honest limit is the BREADTH of
constraint-DERIVATION: a presupposition the gate's question-type readers do not yet
recognise leaves that constraint UN-DERIVED (the gate cannot collapse against a
constraint it never read). That named limit IS the result — never a faked catch.

DONKEY: the only arithmetic is the agree-count (an integer count of satisfied
constraints) and the native softmax inside verify_collapse. No fit, no gradient, no
tuned parameter; no new Rust, no new primitive. The gate is COMPOSITION over the
held native collapse + a question-type constraint reader.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from domains.verify_collapse import verify_by_collapse, _agree


# ==========================================================================
# A CONSTRAINT — one (label, got, want) the problem imposes on the object's
# forward-model properties. `got` is what the object's forward model produced;
# `want` is what the constraint requires. `kind` names which of the three
# constraint-sources it came from (stated / presupposition / construction), purely
# for the trace — the collapse treats them uniformly (one agreement each).
# ==========================================================================

@dataclass
class Constraint:
    label: str
    got: Any
    want: Any
    kind: str = "stated"          # "stated" | "presupposition" | "construction"
    note: str = ""

    def agreement(self) -> float:
        # the agent's OWN hard symbol-equality (the Γ-prune verify_collapse uses):
        # a "want" that is a PREDICATE (callable) is satisfied iff it returns truthy
        # on `got`; otherwise it is the opaque value-equality _agree.
        if callable(self.want):
            try:
                return 1.0 if self.want(self.got) else 0.0
            except Exception:                       # noqa: BLE001
                return 0.0
        return _agree(self.got, self.want)


# ==========================================================================
# (b) THE WELL-DEFINEDNESS PRESUPPOSITIONS — DERIVED (comprehension + the derivation
# engine over held facts), NOT a regex with a hard-coded conclusion.
#
# What must hold for the ASKED INVARIANT to be WELL-POSED. THE FIX (the user's call:
# "no regexes. have the agent fix this"): the presupposition is the OUTPUT of a
# DERIVATION, not a surface string-match asserting its answer. The disease this
# replaces was `_is_finite_free_group_rank_question` — a REGEX that string-matched
# "rank"+"free group"+("kernel" near "hurewicz") on the raw question, then HARD-CODED
# `h1_free_rank == 0`. A paraphrase MISSED it; the conclusion was never derived.
#
# Now `presuppositions_from_question` DELEGATES to presupposition_derivation, which:
#   1. COMPREHENDS the asked invariant via the HELD general reader
#      (construction_grammar.comprehend_structure) into a TYPED term
#      free_rank OF (kernel OF (hurewicz_map)) — STRUCTURE, not a string match. A
#      paraphrase that types to the same tree fires; H_1-asked-directly types a
#      DIFFERENT tree and does NOT.
#   2. ACQUIRES the general theorems by READING them as held Claims (cited):
#      Ker(Hurewicz)=[pi1,pi1]; finite-free-rank => finite index; index=|H_1|.
#   3. DERIVES the presupposition by CHAINING the facts through the derivation engine
#      (derivation_engine.derive): finite-free-rank -> finite-index -> index=|H_1|
#      -> H_1 finite => H_1 free rank 0. The conclusion is the engine's goal-tree
#      root (a checkable chain), NEVER a hard-coded literal. The answer is never read.
#
# An un-grounded fact STALLS the derivation (the named residual, acquire-by-reading),
# never a faked catch. See domains/presupposition_derivation.py.
# ==========================================================================

# the property KEY the homology forward model reports H_1 finiteness under. A
# constructed object's homology read is {free, torsion}; "H_1 finite" <=> free == 0.
_H1_FREE_KEY = "h1_free_rank"


def presuppositions_from_question(qtext: str) -> List[Dict[str, Any]]:
    """DERIVE the well-definedness PRESUPPOSITIONS from the QUESTION (never the
    answer) by COMPREHENSION + DERIVATION (NOT a regex + a hard-coded conclusion).
    Returns a list of {label, property, predicate, note}: the gate evaluates each
    predicate against the object's forward-model property `property` and turns it
    into a presupposition Constraint.

    The presupposition is the OUTPUT of presupposition_derivation.derive_
    presuppositions: the general reader TYPES the asked invariant (free_rank OF
    kernel OF Hurewicz — a structural read, so a PARAPHRASE fires and H_1-asked-
    directly does not), the agent READS the needed general theorems as Claims, and
    the DERIVATION ENGINE chains them to H_1 finite => free rank 0. The conclusion
    (`predicate`) is DERIVED — its target value comes from the derivation, not a
    literal `== 0`.

    The honest residual: if a needed fact cannot be grounded by reading, the
    derivation STALLS at that named un-held fact (never hard-coded); the empty list
    is returned and the stall is reported through derive_presuppositions' trace."""
    from domains import presupposition_derivation as _pd
    return _pd.derive_presuppositions(qtext)["presuppositions"]


# ==========================================================================
# THE GATE RESULT — the collapse verdict + the full constraint trace.
# ==========================================================================

@dataclass
class GateResult:
    admitted: bool
    confidence: float
    collapsed: bool
    partial: bool
    wall: bool
    constraints: List[Constraint] = field(default_factory=list)
    undrivable_presuppositions: List[str] = field(default_factory=list)
    reason: str = ""

    def trace(self) -> str:
        lines = []
        for c in self.constraints:
            ok = "OK " if c.agreement() >= 1.0 else "BREAK"
            lines.append(f"    [{ok}] ({c.kind}) {c.label}: got={c.got!r} "
                         f"want={'<predicate>' if callable(c.want) else c.want!r}")
        for u in self.undrivable_presuppositions:
            lines.append(f"    [UN-DERIVED presupposition] {u}")
        return "\n".join(lines)


# ==========================================================================
# THE ONE GATE — collapse the object's forward-model properties against ALL the
# problem's constraints, through the held native collapse. ADMIT iff full collapse.
# ==========================================================================

def admit(*, constraints: List[Constraint],
          undrivable: Optional[List[str]] = None,
          substrate=None) -> GateResult:
    """THE SINGLE ADMISSIBILITY GATE. Route the object's per-constraint AGREEMENTS
    through the held native collapse (verify_collapse.verify_by_collapse) and ADMIT
    iff the confidence interval FULLY contracts onto the candidate (every constraint
    reproduced). One broken constraint => inadmissible BY CONSTRUCTION.

    `constraints` is the union of the description's stated-property constraints, the
    asked-invariant's presupposition constraints, and the construction-residual
    constraints — all uniform here. `undrivable` names any presupposition no
    question-type reader recognised (the constraint-derivation-breadth residual),
    carried into the result for the honest report; it does NOT count as satisfied."""
    agreements = [c.agreement() for c in constraints]
    out = verify_by_collapse(agreements, substrate=substrate)
    admitted = bool(out["collapsed"])
    # the first broken constraint (parity with the per-site guards' diagnostic).
    broke = next((c for c in constraints if c.agreement() < 1.0), None)
    if admitted:
        reason = (f"ADMITTED — native collapse confidence {out['confidence']:.6f} "
                  f"(FULL contraction: all {len(constraints)} problem constraints "
                  f"reproduced; the binary verify's POINT collapse)")
    else:
        why = (f"{broke.kind} constraint BROKE: {broke.label}" if broke
               else "no constraint satisfied")
        reason = (f"INADMISSIBLE — native collapse confidence {out['confidence']:.6f} "
                  f"(the interval did NOT fully contract; {why}). Inadmissible BY "
                  f"CONSTRUCTION — the object fails a problem constraint.")
    return GateResult(
        admitted=admitted, confidence=out["confidence"],
        collapsed=bool(out["collapsed"]), partial=bool(out["partial"]),
        wall=bool(out["wall"]), constraints=list(constraints),
        undrivable_presuppositions=list(undrivable or []), reason=reason)


# ==========================================================================
# CONSTRAINT BUILDERS — turn each constraint SOURCE into Constraints. These are
# mechanical translations (a property dict / a presupposition spec / a residual
# count) into the uniform Constraint the gate collapses. NO decision — the gate's
# collapse is the one mechanism.
# ==========================================================================

def stated_property_constraints(object_props: Dict[str, Any],
                                stated_props: Dict[str, Any]) -> List[Constraint]:
    """(a) The description's STATED properties (the cmsg115 check, as constraints).
    For each property the description STATED, the object's forward model must
    reproduce it: got = object_props[k], want = stated_props[k]. Unstated properties
    impose NO constraint (they are not in `stated_props`)."""
    cs: List[Constraint] = []
    for k, want in stated_props.items():
        if want is None:
            continue
        cs.append(Constraint(label=f"stated {k}", got=object_props.get(k),
                             want=want, kind="stated"))
    return cs


def presupposition_constraints(qtext: str,
                               object_props: Dict[str, Any]
                               ) -> tuple[List[Constraint], List[str]]:
    """(b) The asked-invariant's WELL-DEFINEDNESS presuppositions (the cmsg116 gap,
    as constraints) — DERIVED FROM THE QUESTION, never the answer. Returns
    (constraints, undrivable): each derived presupposition becomes a Constraint
    whose `got` is the object's forward-model property and whose `want` is the
    presupposition predicate; `undrivable` lists any presupposition whose required
    property the object's forward model did not report (the constraint cannot be
    collapsed — the named breadth residual)."""
    cs: List[Constraint] = []
    undrivable: List[str] = []
    for pre in presuppositions_from_question(qtext):
        prop = pre["property"]
        if prop not in object_props:
            undrivable.append(
                f"{pre['label']} (the forward model did not report {prop!r})")
            continue
        cs.append(Constraint(label=pre["label"], got=object_props[prop],
                             want=pre["predicate"], kind="presupposition",
                             note=pre.get("note", "")))
    return cs, undrivable


def construction_residual_constraints(unaccounted: List[str]) -> List[Constraint]:
    """(c) The un-accounted CONSTRUCTION residual (the cmsg115 un-synthesizable
    operators, as constraints). Each un-synthesizable construction operator the
    grounding leaves unexplained is a BROKEN constraint (got=present, want=accounted)
    — the object cannot reproduce a construction it has no operator for."""
    return [Constraint(label=f"un-synthesizable construction op: {op}",
                       got="un-accounted", want="accounted", kind="construction")
            for op in unaccounted]


# ==========================================================================
# THE GROUNDING/CONSTRUCTION GATE — the ONE entry every site routes through. Given
# the object's forward-model properties + the description's stated properties + the
# question text + the construction residual, build the union of constraints and
# collapse. This is what math_hat-grounding, the constructor, and verify-vs-known
# all call — ONE gate, the held collapse.
# ==========================================================================

def gate_object(*, object_props: Dict[str, Any],
                stated_props: Optional[Dict[str, Any]] = None,
                question_text: str = "",
                unaccounted_construction: Optional[List[str]] = None,
                substrate=None) -> GateResult:
    """Route a grounded / constructed object through the ONE admissibility gate.

    `object_props`  : the object's forward-model properties (homology free/torsion,
                      b0/b1/b2, etc.) — whatever the held forward model derived.
    `stated_props`  : the description's STATED properties (cmsg115's (a)).
    `question_text` : the QUESTION (for the well-definedness presuppositions, (b)) —
                      the answer is NEVER passed here.
    `unaccounted_construction` : the un-synthesizable construction operators (c).

    Builds the union of (a)+(b)+(c) as Constraints and collapses through the held
    native collapse; ADMIT iff the interval fully contracts. The cmsg116 fidelity
    gap (H_1=Z^2 vs the finite-H_1 presupposition) is caught HERE, by the SAME
    mechanism that catches cmsg115's spurious S^1 (un-accounted operators) and admits
    BG_2 / lattices (their derivations reproduce their constraints)."""
    pre_cs, undrivable = presupposition_constraints(question_text, object_props)
    constraints = (
        stated_property_constraints(object_props, stated_props or {})
        + pre_cs
        + construction_residual_constraints(unaccounted_construction or [])
    )
    return admit(constraints=constraints, undrivable=undrivable,
                 substrate=substrate)


__all__ = [
    "Constraint", "GateResult", "admit", "gate_object",
    "presuppositions_from_question", "stated_property_constraints",
    "presupposition_constraints", "construction_residual_constraints",
]
