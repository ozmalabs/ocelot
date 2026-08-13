"""One-off seed-authoring script (CLAUDE.md: "tools/* -- one-off authoring/
capture scripts that EMIT seed manifests, deletable, not agent runtime") --
EMITS seeds/entity_concept_correspondence.json: the general SmEntity <->
Microtheory identity-correspondence mechanism (docs/research/engine_substrate/
ENTITY_RESOLUTION_PREREG.md/_RESULTS.md).

Two Rules mint a `denotes` edge SmEntity -> Microtheory:
  1. sm_entity_denotes_believer_exact -- name equality (the OLD naming-
     convention bridge's case, now an explicit graph fact via a Rule instead
     of a Python string format).
  2. sm_entity_denotes_believer_by_name_tokens -- fires only when rule 1
     does not apply. Uses the native Covers Term (Set/FrozenSet subset test)
     over a precomputed `name_tokens` frozenset attr on both sides -- the
     SAME token-containment relation domains/name_variant_merge.py already
     uses (in Python) for SmEntity<->SmEntity alias merging, expressed here
     graph-natively for the cross-type SmEntity<->Resident case. An explicit
     ambiguity guard (Not Exists another candidate Resident) refuses to
     mint when more than one candidate matches -- no silent over-merge.

One Gamma production registers `denotes` as admissible SmEntity->Microtheory
(declarative; rule effects write via graph.insert_edge directly and do not
gate through check_edge today -- a corpus-wide, pre-existing property, see
ENTITY_RESOLUTION_PREREG.md sec3).
"""
from __future__ import annotations

import json
import os


def V(n):
    return {"type": "Var", "name": n}


def Attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def Lit(v):
    return {"type": "Lit", "value": v}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Not(arg):
    return {"type": "Not", "arg": arg}


def And(*items):
    return {"type": "And", "items": list(items)}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Covers(pattern, instance):
    return {"type": "Covers", "pattern": pattern, "instance": instance}


def FixedCount(pattern):
    return {"type": "FixedCount", "pattern": pattern}


def Exists(source, var_name, predicate):
    return {"type": "Exists", "source": source, "var_name": var_name,
            "predicate": predicate}


def NodesOfType(t):
    return {"type": "NodesOfType", "node_type": t}


def Neighbours(node, edge_type):
    return {"type": "Neighbours", "node": node, "edge_type": edge_type}


# --------------------------------------------------------------------------- #
#  shared sub-terms
# --------------------------------------------------------------------------- #
def _already_denotes(evar):
    """Not(Exists a denotes edge already out of `evar`)."""
    return Not(Exists(Neighbours(V(evar), "denotes"), "_ex", Lit(True)))


def _token_subset_either_way(evar, rvar):
    return Or(
        Covers(Attr(V(evar), "name_tokens"), Attr(V(rvar), "name_tokens")),
        Covers(Attr(V(rvar), "name_tokens"), Attr(V(evar), "name_tokens")),
    )


def _ambiguity_guard(evar, rvar):
    """Not(Exists another Resident r2 != r that ALSO token-subset-matches e)
    -- the no-over-merge discipline, cross-type. r2 must itself have a
    belief Mt (has_belief_mt) to count as a genuine rival candidate."""
    return Not(Exists(
        NodesOfType("Resident"), "r2",
        And(
            Not(Eq(V("r2"), V(rvar))),
            Exists(Neighbours(V("r2"), "has_belief_mt"), "_mt2", Lit(True)),
            _token_subset_either_way(evar, "r2"),
        ),
    ))


RULE_EXACT = {
    "name": "sm_entity_denotes_believer_exact",
    "match": [
        ["e", "is_entity", "e"],
        ["r", "has_belief_mt", "mt"],
    ],
    "where": And(
        Eq(Attr(V("e"), "name"), Attr(V("r"), "name")),
        _already_denotes("e"),
    ),
    "effects": [
        ["add_edge", "e", "denotes", "mt"],
    ],
}

RULE_TOKENS = {
    "name": "sm_entity_denotes_believer_by_name_tokens",
    "match": [
        ["e", "is_entity", "e"],
        ["r", "has_belief_mt", "mt"],
    ],
    "where": And(
        Not(Eq(Attr(V("e"), "name"), Attr(V("r"), "name"))),
        Gt(FixedCount(Attr(V("e"), "name_tokens")), Lit(0)),
        _token_subset_either_way("e", "r"),
        _already_denotes("e"),
        _ambiguity_guard("e", "r"),
    ),
    "effects": [
        ["add_edge", "e", "denotes", "mt"],
    ],
}

SEED = {
    "id": "entity_concept_correspondence",
    "version": "1.0.0",
    "depends_on": ["core"],
    "description": (
        "THE GENERAL SmEntity<->Microtheory identity-correspondence "
        "mechanism (ENTITY_RESOLUTION_PREREG.md/_RESULTS.md), replacing "
        "domains/reasoning_can_bridge.py's old f'{entity}_beliefs' "
        "string-format coincidence. Two rungs, Occam-ordered: (1) exact "
        "name equality -- the old convention's case, now an explicit "
        "denotes edge minted by a Rule instead of a Python string format; "
        "(2) name-TOKEN containment (the native Covers Set/FrozenSet "
        "subset test over a precomputed name_tokens frozenset attr, "
        "mirroring domains/name_variant_merge.py's already-shipped "
        "SmEntity<->SmEntity alias-containment relation, applied "
        "cross-type) -- fires only when (1) does not apply, and refuses "
        "to mint when more than one Resident candidate token-matches "
        "(the no-over-merge discipline; a genuine ambiguity is a null, "
        "never a guess). name_tokens is mechanically precomputed by "
        "domains/reasoning_can_bridge.py (reusing name_variant_merge."
        "_name_tokens, no new tokenizer) before these rules run; the "
        "DECISION stays entirely in the Covers/Not(Exists) Term tree "
        "each Rule evaluates -- CLAUDE.md's rule/shape split, execution "
        "over held name structure, not acquisition (no codebook grows)."
    ),
    "nodes": [
        {
            "local_id": 1,
            "type": "Concept",
            "attrs": {
                "name": "entity_concept_correspondence",
                "description": (
                    "sentinel: entity_concept_correspondence seed loaded "
                    "(ensure_seeds idempotency guard, the ensure_seeds "
                    "sentinel-Concept idiom domains/inference_generation.py "
                    "already uses)"
                ),
            },
        },
    ],
    "edges": [],
    "productions": [
        {
            "src": {"type": "SmEntity", "var": "src"},
            "edge_type": "denotes",
            "tgt": {"type": "Microtheory", "var": "tgt"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "entity_concept_correspondence",
        },
    ],
    "rules": [RULE_EXACT, RULE_TOKENS],
}


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "seeds", "entity_concept_correspondence.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
