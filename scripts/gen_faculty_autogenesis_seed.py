#!/usr/bin/env python3
"""Generate the graph-native faculty acquisition and meta-repair spine.

A domain may state that a faculty is needed and attach observed examples.  It
does not install an implementation.  The general program-synthesis faculty
authors one, this seed installs the accepted Program, and a synthesis failure
is turned into a concern about the *authoring faculty* itself.  The existing
program-self-modification loop then works on that meta-faculty; after a proven
repair the original need is retried one order higher.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Count(source):
    return {"type": "Count", "source": source}


def Neighbours(var, edge_type):
    return {"type": "Neighbours", "node": V(var), "edge_type": edge_type}


def Plus(*items):
    return {"type": "Plus", "items": list(items)}


def T(term):
    return {"__term__": term}


def production(name, src, edge, tgt):
    return {
        "provenance": f"faculty_autogenesis:{name}",
        "src": {"type": src, "var": "src"},
        "edge_type": edge,
        "tgt": {"type": tgt, "var": "tgt"},
    }


def install_rule():
    return {
        "name": "fa_install_self_authored_faculty",
        "area": "faculty_autogenesis",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "An accepted synthesis result becomes a held faculty. "
        "The host neither selects nor installs an implementation.",
        "match": [
            ["agent", "has_faculty_need", "need"],
            ["need", "has_faculty_synthesis_message", "message"],
            ["goal", "about_message", "message"],
            ["goal", "accepted_program", "program"],
            ["program", "ir_subgraph", "root"],
        ],
        "where": Eq(A("need", "status"), L("synthesizing")),
        "effects": [
            ["add_edge", "agent", "holds_faculty", "program"],
            ["add_edge", "need", "installed_faculty", "program"],
            ["set_attr", "program", "faculty_kind", T(A("need", "kind"))],
            ["set_attr", "program", "self_authored", 1],
            ["set_attr", "program", "integer_native", 1],
            ["set_attr", "need", "status", "installed"],
        ],
    }


def escalate_rule():
    return {
        "name": "fa_escalate_unbuildable_faculty_to_meta_faculty_repair",
        "area": "faculty_autogenesis",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Failure to add a task faculty is evidence against the "
        "faculty-authoring faculty, never permission for a host shortcut.",
        "match": [
            ["agent", "has_faculty_need", "need"],
            ["need", "has_faculty_synthesis_message", "message"],
            ["goal", "about_message", "message"],
        ],
        "where": {
            "type": "And",
            "items": [
                Eq(A("need", "status"), L("synthesizing")),
                Eq(A("goal", "status"), L("gapped")),
                Eq(Count(Neighbours("need", "has_meta_faculty_gap")), L(0)),
            ],
        },
        "effects": [
            ["add_node", "gap", "MetaFacultyGap", {
                "status": "open",
                "kind": "faculty_authoring_failure",
                "failed_faculty_kind": T(A("need", "kind")),
                "order_n": T(Plus(A("need", "order_n"), L(1))),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_node", "concern", "SelfConcern", {
                "status": "noted",
                "source": "implicit",
                "kind": "code_write",
                "content": "extend faculty autogenesis to express an unbuildable held faculty",
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_node", "escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "faculty_authoring_failure",
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_node", "task", "SystemTwoTaskSet", {
                "area": "program_self_modification",
                "enabled": 1,
                "integer_native": 1,
            }],
            ["add_edge", "need", "has_meta_faculty_gap", "gap"],
            ["add_edge", "gap", "about_failed_faculty_need", "need"],
            ["add_edge", "gap", "raises_meta_faculty_concern", "concern"],
            ["add_edge", "need", "has_authoring_self_concern", "concern"],
            ["add_edge", "agent", "has_self_concern", "concern"],
            ["add_edge", "escalation", "about_context", "gap"],
            ["add_edge", "escalation", "recruits_task_set", "task"],
            ["set_attr", "need", "status", "repairing_meta_faculty"],
        ],
    }


def retry_rule():
    return {
        "name": "fa_retry_faculty_after_meta_faculty_consolidation",
        "area": "faculty_autogenesis",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["agent", "has_faculty_need", "need"],
            ["need", "has_authoring_self_concern", "concern"],
            ["need", "has_faculty_synthesis_message", "message"],
        ],
        "where": {
            "type": "And",
            "items": [
                Eq(A("need", "status"), L("repairing_meta_faculty")),
                Eq(A("concern", "status"), L("resolved")),
            ],
        },
        "effects": [
            ["set_attr", "message", "faculty_synthesis_retired", 1],
            ["set_attr", "need", "order_n", T(Plus(A("need", "order_n"), L(1)))],
            ["set_attr", "need", "status", "requested"],
        ],
    }


def manifest():
    productions = (
        ("agent_need", "Agent", "has_faculty_need", "FacultyNeed"),
        ("need_example", "FacultyNeed", "has_faculty_example", "FacultyExample"),
        ("need_message", "FacultyNeed", "has_faculty_synthesis_message", "Message"),
        ("need_program", "FacultyNeed", "installed_faculty", "Program"),
        ("held_faculty", "Agent", "holds_faculty", "Program"),
        ("need_meta_gap", "FacultyNeed", "has_meta_faculty_gap", "MetaFacultyGap"),
        ("need_concern", "FacultyNeed", "has_authoring_self_concern", "SelfConcern"),
    )
    return {
        "id": "faculty_autogenesis",
        "version": "1.0.0",
        "depends_on": ["program_synthesis", "program_self_modification"],
        "area": "general_cognition",
        "latency_class": "soft_realtime",
        "description": "General graph-native need -> synthesize -> verify -> "
        "install faculty loop. A failure recursively targets the authoring "
        "meta-faculty and retries only after proof-carrying consolidation.",
        "nodes": [],
        "edges": [],
        "productions": [production(*row) for row in productions],
        "rules": [install_rule(), escalate_rule(), retry_rule()],
    }


def main():
    output = ROOT / "seeds" / "faculty_autogenesis.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(manifest()['rules'])} rules)")


if __name__ == "__main__":
    main()
