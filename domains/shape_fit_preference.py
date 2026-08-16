"""shape_fit_preference -- "an agent likes things by shape" (user's own
framing). A preference primitive that is a direct READ-OFF of the sd
loop's own decode fluency, not a third scalar Concept updated by ad hoc
evidence -- qualitatively different from regard_for/pity_for/removal_
desire_for's own evidence-accumulation family.

SHAPE_FIT_PREFERENCE_PREREG.md: Reber, Winkielman & Schwarz (2004) --
fluent processing (good fit to a held representation) is liked more;
Berlyne (1971) -- NOT monotonic, an inverted-U (the Wundt curve) over
novelty relative to what is already known. Reuses 100% of already-
verified infrastructure: ShapeDecode's covered_count/goal_relations are
already plain Value dict fields (zero new plumbing), and
shared_arousal.mint_target_arousal's target param is generic string
bookkeeping (a clean reuse for a non-agent stimulus identifier).

Pure world-adapter code (CLAUDE.md's architecture rule): the DECISION
(how well does this goal fit the held codebook) is entirely the engine's
own ShapeDecode Term; this module only computes the inverted-U arithmetic
from its already-decided covered_count/goal_relations and dispatches the
arousal update via the existing concept_apply_evidence-free TargetArousal
bookkeeping shared_arousal.py already established.
"""
from __future__ import annotations

from domains.shared_arousal import mint_target_arousal

# shared_arousal.record_targeted_incident's own default `decay` value,
# reused verbatim (not re-derived) -- the same constant hate_attribution.py
# already redeclared locally for the same reason (shared_arousal.py
# exports no named constant, only a parameter default).
AROUSAL_DECAY = 0.7


def decode_fit(inner, goal_signature: list, *, codebook_type: str = "ShapeSignature",
               beam: int = 3, max_steps: int = 8, cand_k: int = 3) -> dict:
    """Decode `goal_signature` (an item_signature-shaped relation list)
    against the held `codebook_type` codebook. Thin wrapper over the
    engine's own ShapeDecode Term -- the fit DECISION is entirely Rust's;
    this just shapes the call and reads back covered_count/goal_relations."""
    result = inner.evaluate({
        "type": "ShapeDecode",
        "goal": {"type": "Lit", "value": goal_signature},
        "codebook_type": codebook_type,
        "beam": beam, "max_steps": max_steps, "cand_k": cand_k,
        "wild_objects": False,
    }, {})
    return result


def preference_from_shape(inner, mt, target: str, goal_signature: list, *,
                          codebook_type: str = "ShapeSignature") -> dict:
    """`target` is a stimulus identifier (shared_arousal's own generic,
    string-keyed target bookkeeping, reused for a non-agent object here).
    `goal_signature` is the observed stimulus's own relation-set
    (domains.meta_shape.item_signature's own output shape).

    Returns {preference, fluency, covered_count, goal_relations,
    arousal_level} -- SHAPE_FIT_PREFERENCE_PREREG.md Sec2:
        fluency = covered_count / goal_relations
        preference = 4 * fluency * (1 - fluency)   [inverted-U, peak at fluency=0.5]
    Novelty (1-fluency) ALSO feeds the SAME shared arousal pool every
    other rung in this arc reads/writes -- a separate side observable,
    not folded into `preference` itself (Sec2: no citable interaction
    form exists to justify combining them into one formula)."""
    decode = decode_fit(inner, goal_signature, codebook_type=codebook_type)
    goal_relations = decode["goal_relations"]
    covered_count = decode["covered_count"]
    fluency = (covered_count / goal_relations) if goal_relations > 0 else 0.0
    preference = 4.0 * fluency * (1.0 - fluency)

    novelty_intensity = 1.0 - fluency
    arousal_node = mint_target_arousal(inner, mt, target)
    current_arousal = inner.node(arousal_node)["attrs"]["level"]
    new_arousal = current_arousal * AROUSAL_DECAY + novelty_intensity
    inner.set_attr(arousal_node, "level", new_arousal)

    return {
        "preference": preference,
        "fluency": fluency,
        "covered_count": covered_count,
        "goal_relations": goal_relations,
        "arousal_level": new_arousal,
    }


__all__ = ["decode_fit", "preference_from_shape"]
