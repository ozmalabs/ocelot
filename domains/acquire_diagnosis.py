"""acquire_diagnosis — the AGENT DIAGNOSES that its acquisition stack is ONE op.

The agent's OWN abstraction machinery (analogy.abstract_patterns / _skeletonize)
recognises that read_and_ground / compute_grounding / extract_function /
self_ascent are the SAME cognitive operation re-instanced. The method is the
agent's, not an assertion:

  1. REPRESENT each acquisition capability as a STRUCTURE — a Concept node whose
     `predicate` is the ACQUIRE pipeline as a Term-tree:
         VERIFY( ITERATE( COMPREHEND( SOURCE ) ) )
     with the FOUR VARYING parameters (SOURCE / COMPREHEND / BEDROCK / VERIFY) as
     Attr leaves (the hollow-able operands), and the fixed pipeline NESTING as the
     operation SHAPE.
  2. RUN analogy.abstract_patterns over the installed Concept nodes — the agent's
     own _skeletonize hollows the Attr leaves (the four parameters -> '?band')
     and keeps the operation shape, de-duplicating by skeleton.
  3. The OUTPUT: ALL five capabilities collapse to ONE skeleton — the agent
     RECOGNISING they are one operation. 5 specifics -> 1 skeleton = the MDL
     compression (the general subsumes the N specifics).

This is the agent's iterate_to_n unification (order_n_composition) diagnosed ONE
LEVEL UP, over the whole ACQUIRE pipeline, by its OWN analogy machinery. No LLM
invents the abstraction; the shared skeleton is the abstract_patterns output,
read verbatim.
"""
from __future__ import annotations

from typing import Any

from domains import analogy as _analogy


# The FIVE acquisition capabilities, each as its (SOURCE, COMPREHEND, BEDROCK,
# VERIFY) parameter set — the four knobs that VARY across the specifics. The
# pipeline SHAPE (the Term-tree nesting) is identical; only these four leaves
# differ, and they hollow under skeletonize.
ACQUISITION_CAPABILITIES: dict[str, dict[str, str]] = {
    # read_and_ground — concept-grounding.
    "read_and_ground": {
        "source": "held_gloss_or_wiki_local",
        "comprehend": "genus_differentia_grammar",
        "bedrock": "seeded_concept_primitives",
        "verify": "coheres_reaches_primitives",
    },
    # compute_grounding — computation.
    "compute_grounding": {
        "source": "held_computational_def",
        "comprehend": "computational_def_grammar",
        "bedrock": "held_compute_primitives",
        "verify": "grounded_combination_evaluates",
    },
    # extract_function + ground — function-from-prose.
    "extract_function": {
        "source": "oeis_local_prose_and_values",
        "comprehend": "math_prose_grammar",
        "bedrock": "held_compute_primitives",
        "verify": "reproduces_ground_truth_values",
    },
    # self_ascent — ACQUIRE iterated over a frontier (ascend).
    "self_ascent": {
        "source": "frontier_concept_def",
        "comprehend": "computational_def_grammar",
        "bedrock": "held_compute_primitives",
        "verify": "goal_concept_grounds",
    },
}


def _attr_leaf(key: str) -> dict[str, Any]:
    """An Attr leaf over the subject — the hollow-able operand slot the agent's
    _skeletonize collapses to '?band'. The four PARAMETERS are exactly these
    leaves; everything else is the operation SHAPE."""
    return {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": key}


def acquire_pipeline_predicate(source: str, comprehend: str, bedrock: str,
                               verify: str) -> dict[str, Any]:
    """The ACQUIRE pipeline as a Term-tree `predicate` (the form
    analogy.abstract_patterns reads): the SOURCE -> COMPREHEND -> ITERATE
    (COMPOSE to bedrock) -> VERIFY composition, with the FOUR parameters as Attr
    leaves and the pipeline NESTING as the operation shape.

        VERIFY( ITERATE( COMPREHEND( SOURCE ) ) )

    The four leaves hollow under _skeletonize; the Verify/Iterate/Comprehend/
    Source nesting is the SHAPE that survives — so two capabilities that differ
    ONLY in the four parameters skeletonize to the SAME thing."""
    return {
        "type": "Verify",
        "signal": _attr_leaf(verify),
        "over": {
            "type": "Iterate",                 # COMPOSE = iterate_to_n to bedrock
            "bedrock": _attr_leaf(bedrock),
            "structure": {
                "type": "Comprehend",
                "grammar": _attr_leaf(comprehend),
                "form": {
                    "type": "Source",
                    "where": _attr_leaf(source),
                },
            },
        },
    }


def install_acquisition_structures(substrate,
                                   capabilities: dict[str, dict[str, str]] | None
                                   = None) -> list:
    """REPRESENT each acquisition capability as a Concept node the agent can
    abstract over — `predicate` = the ACQUIRE pipeline Term-tree (the four params
    as Attr leaves). Returns the installed node ids. These are graph DATA the
    agent's analogy machinery reads; no decision lives here."""
    caps = capabilities if capabilities is not None else ACQUISITION_CAPABILITIES
    ids = []
    for name, p in caps.items():
        pred = acquire_pipeline_predicate(p["source"], p["comprehend"],
                                          p["bedrock"], p["verify"])
        nid = substrate.add_node("Concept", {
            "name": name, "origin": "acquisition_stack",
            "predicate": pred,
            # record the four parameters as graph data (the instance's knobs).
            "acquire_source": p["source"], "acquire_comprehend": p["comprehend"],
            "acquire_bedrock": p["bedrock"], "acquire_verify": p["verify"],
        })
        ids.append(nid)
    return ids


def diagnose(substrate, capabilities: dict[str, dict[str, str]] | None = None
             ) -> dict[str, Any]:
    """The AGENT'S DIAGNOSIS: install the acquisition capabilities as structures,
    run analogy.abstract_patterns (its OWN abstraction machinery) over them, and
    return the shared skeleton it abstracts + the MDL compression.

    Returns {n_specifics, n_skeletons, shared_skeleton, members, compression,
    parameters_per_member} — the agent recognising the N specifics are ONE
    operation. `shared_skeleton` is the abstract_patterns output VERBATIM (the
    hollowed pipeline); `n_skeletons == 1` is the recognition; `n_specifics ->
    1` is the compression (1 general subsumes N specifics)."""
    caps = capabilities if capabilities is not None else ACQUISITION_CAPABILITIES
    install_acquisition_structures(substrate, caps)

    # the AGENT'S abstraction: _skeletonize over each installed predicate, dedup
    # by skeleton. (min_depth small — the pipeline is depth-4 anyway.)
    patterns = _analogy.abstract_patterns(substrate, min_depth=2)
    members = [name for name, _origin, _skel in patterns]
    skeletons = {str(skel): skel for _name, _origin, skel in patterns}
    shared = next(iter(skeletons.values())) if len(skeletons) == 1 else None

    n_spec = len(caps)
    n_skel = len(skeletons)
    return {
        "n_specifics": n_spec,
        "n_skeletons": n_skel,
        "shared_skeleton": shared,
        "all_skeletons": list(skeletons.values()),
        "members": members,
        "compression": f"{n_spec} specifics -> {n_skel} operation "
                       f"(MDL: 1 general subsumes {n_spec})",
        "parameters_per_member": {
            name: {"SOURCE": p["source"], "COMPREHEND": p["comprehend"],
                   "BEDROCK": p["bedrock"], "VERIFY": p["verify"]}
            for name, p in caps.items()},
        "is_one_operation": (n_skel == 1),
    }


__all__ = [
    "ACQUISITION_CAPABILITIES", "acquire_pipeline_predicate",
    "install_acquisition_structures", "diagnose",
]
