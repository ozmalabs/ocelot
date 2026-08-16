"""bigville_theory_of_mind -- the canonical, explicitly-named entry point
for a resident's Theory-of-Mind BELIEF about another resident (as
opposed to the resident's own affective reaction TO that resident).

TOM_SYSTEM_UNIFICATION_RESULTS.md: bigville has no bespoke ToM node type
-- a resident's belief about another resident's mind/circumstances is
the SAME per-(resident, target) CAN Concept every target-scoped belief
in this arc already uses (shared_arousal.mint_target_concept), under the
naming convention `<aspect>_for:<target>`. This module names that
SPECIFIC sub-convention explicitly, so a future rung reaches for
`mint_resident_tom_belief` by name instead of re-deriving the pattern
from prose comments or forking a parallel representation -- exactly the
duplication `ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md` and
`HATE_PITY_TOM_UNDERSTANDING_PREREG.md` both avoided by reusing this
same primitive.

**The distinction this module draws, precisely**: not every target-scoped
Concept is a ToM belief. `regard_for`/`desire_for`/`removal_desire_for`/
`pity_for` (all minted via `mint_target_concept` directly, no wrapper
needed) are the RESIDENT's OWN affective/motivational states -- how they
feel about or want to do to the target, not a claim about the target's
mind. `controllability_for` (this arc's first genuine instance) is
different in kind: it attributes a property of the TARGET's own agency/
circumstances (do they control their behavior or not) -- that attribution
IS what Theory of Mind means (Premack & Woodruff 1978's own definition:
attributing mental states to another). `mint_resident_tom_belief` is for
THAT category specifically.

Known target-scoped Concepts in this arc, by category:
  resident's own affect/motivation (plain mint_target_concept):
    regard_for:<target>, desire_for:<target>, removal_desire_for:<target>,
    pity_for:<target>
  resident's ToM belief ABOUT the target (mint_resident_tom_belief):
    controllability_for:<target>  -- Weiner 1980/1985's controllability
                                      attribution, HATE_PITY_TOM_
                                      UNDERSTANDING_PREREG.md
"""
from __future__ import annotations

from domains.shared_arousal import mint_target_concept


def mint_resident_tom_belief(inner, mt, aspect: str, target: str):
    """The resident's ToM belief about `target`'s `aspect` (e.g.
    `aspect='controllability'` mints/returns `controllability_for:
    <target>`). Idempotent -- delegates entirely to `mint_target_concept`'s
    own idempotent lookup; this is a NAME for the pattern, not a new
    mechanism."""
    return mint_target_concept(inner, mt, "%s_for" % aspect, target)


__all__ = ["mint_resident_tom_belief"]
