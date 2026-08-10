#!/usr/bin/env python3
"""Generate graph-native quantity/operator grounding for synthesis.

The graph decides which held operator shape a request evokes and which held
number words it grounds.  ``domains.prog_synthesis`` only transcribes those
facts into the already-existing ``SynthEnumerate{ops,consts}`` interface.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "program_synthesis_grounding.json"


def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(node, key):
    return {"type": "Attr", "node": V(node), "key": key}


def neighbours(node, edge):
    return {
        "type": "Neighbours",
        "node": V(node),
        "edge_type": edge,
        "any_type": False,
    }


def filter_(source, var, predicate):
    return {
        "type": "Filter",
        "source": source,
        "var_name": var,
        "predicate": predicate,
    }


def count(source):
    return {"type": "Count", "source": source}


def in_(member, container):
    return {"type": "In", "member": member, "container": container}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def not_(arg):
    return {"type": "Not", "arg": arg}


def and_(*items):
    return {"type": "And", "items": list(items)}


def exists(source, var, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var,
        "predicate": predicate,
    }


def term(value):
    return {"__term__": value}


def trigger_score(shape, token):
    return count(filter_(
        A(shape, "trigger_tokens"),
        token,
        in_(V(token), A("message", "ps_tokens")),
    ))


def eligible_shapes():
    return filter_(
        neighbours("agent", "has_synthesis_operator_shape"),
        "shape",
        gte(
            trigger_score("shape", "shape_token"),
            A("shape", "minimum_trigger_matches"),
        ),
    )


def selected_shape():
    return {
        "type": "Argmax",
        "source": eligible_shapes(),
        "var_name": "candidate_shape",
        "value": trigger_score("candidate_shape", "candidate_token"),
        "default": None,
    }


NUMBER_WORDS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve",
)


OPERATOR_SHAPES = (
    {
        "name": "thresholded_greater_branch",
        "trigger_tokens": [
            "MORE", "GREATER", "EXCEEDS", "ABOVE", "THAN", "TIMES",
            "THRESHOLD", "WHEN", "OTHERWISE", "ELSE",
        ],
        "minimum_trigger_matches": 5,
        "ops": ["Times", "Gt", "IfThenElse"],
        "description": "scaled or direct greater-than gate with two outcomes",
    },
    {
        "name": "thresholded_lower_branch",
        "trigger_tokens": [
            "LESS", "BELOW", "UNDER", "THAN", "TIMES", "THRESHOLD",
            "WHEN", "OTHERWISE", "ELSE",
        ],
        "minimum_trigger_matches": 5,
        "ops": ["Times", "Lt", "IfThenElse"],
        "description": "scaled or direct less-than gate with two outcomes",
    },
)


def manifest():
    nodes = []
    edges = []
    local_id = 1
    for shape in OPERATOR_SHAPES:
        nodes.append({
            "local_id": local_id,
            "type": "SynthesisOperatorShape",
            "attrs": shape,
        })
        edges.append({
            "src": {"role": "agent_root"},
            "type": "has_synthesis_operator_shape",
            "tgt": {"local": local_id},
            "attrs": {},
        })
        local_id += 1
    for value, word in enumerate(NUMBER_WORDS):
        nodes.append({
            "local_id": local_id,
            "type": "SynthesisQuantityLexeme",
            "attrs": {
                "token": word.upper(),
                "value": value,
                "source": "held_number_lexicon",
            },
        })
        edges.append({
            "src": {"role": "agent_root"},
            "type": "has_synthesis_quantity_lexeme",
            "tgt": {"local": local_id},
            "attrs": {},
        })
        local_id += 1

    quantity_rule = {
        "name": "ps_ground_held_quantity_lexeme",
        "area": "program_synthesis",
        "latency_class": "background",
        "batch": True,
        "comment": "Exact surface-token equality grounds every matching "
        "held number lexeme onto the request. The vocabulary is graph data "
        "and can be taught without changing this rule.",
        "match": [
            ["agent", "received", "message"],
            ["agent", "has_synthesis_quantity_lexeme", "quantity"],
        ],
        "where": and_(
            eq(A("message", "ps_write_request"), L(1)),
            in_(A("quantity", "token"), A("message", "ps_surface_tokens")),
            not_(exists(
                neighbours("message", "ps_grounds_quantity"),
                "held_quantity",
                eq(V("held_quantity"), V("quantity")),
            )),
        ),
        "effects": [[
            "add_edge", "message", "ps_grounds_quantity", "quantity",
        ]],
    }

    shape_rule = {
        "name": "ps_select_synthesis_operator_shape",
        "area": "program_synthesis",
        "latency_class": "background",
        "comment": "Collapse matching held meta-shapes by trigger coverage. "
        "The winning graph node supplies the enumerator's operator inventory; "
        "the adapter only transcribes the decided fact.",
        "match": [["agent", "received", "message"]],
        "where": and_(
            eq(A("message", "ps_write_request"), L(1)),
            not_(eq(A("message", "ps_operator_shape_selected"), L(1))),
            gte(count(eligible_shapes()), L(1)),
        ),
        "effects": [
            ["set_attr", "message", "ps_enum_ops", term({
                "type": "Attr", "node": selected_shape(), "key": "ops",
            })],
            ["set_attr", "message", "ps_enum_operator_shape", term({
                "type": "Attr", "node": selected_shape(), "key": "name",
            })],
            ["set_attr", "message", "ps_operator_shape_selected", 1],
        ],
    }

    return {
        "id": "program_synthesis_grounding",
        "version": "1.0.0",
        "depends_on": ["program_synthesis"],
        "capability_keys": [
            "synthesis_quantity_grounding",
            "synthesis_shape_directed_operator_retrieval",
        ],
        "description": "Graph-native grounding for program synthesis. Held "
        "number lexemes become request quantities; request meta-shape "
        "collapses onto a held operator inventory before SynthEnumerate. "
        "All values and scores are integers.",
        "microtheory": {
            "name": "program_synthesis_grounding",
            "description": "quantity and operator-shape proposal grounding",
        },
        "nodes": nodes,
        "edges": edges,
        "productions": [
            {
                "src": {"type": "Agent", "var": "s"},
                "edge_type": "has_synthesis_operator_shape",
                "tgt": {"type": "SynthesisOperatorShape", "var": "t"},
                "provenance": "seed:program_synthesis_grounding:operator-shape",
            },
            {
                "src": {"type": "Agent", "var": "s"},
                "edge_type": "has_synthesis_quantity_lexeme",
                "tgt": {"type": "SynthesisQuantityLexeme", "var": "t"},
                "provenance": "seed:program_synthesis_grounding:quantity-lexeme",
            },
            {
                "src": {"type": "Message", "var": "s"},
                "edge_type": "ps_grounds_quantity",
                "tgt": {"type": "SynthesisQuantityLexeme", "var": "t"},
                "provenance": "seed:program_synthesis_grounding:grounds-quantity",
            },
            {
                "src": {"type": "Message", "var": "s"},
                "edge_type": "ps_grounds_quantity",
                "tgt": {"type": "SynthesisQuantity", "var": "t"},
                "provenance": "seed:program_synthesis_grounding:explicit-quantity",
            },
        ],
        "rules": [quantity_rule, shape_rule],
        "reflexes": [],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(manifest(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
