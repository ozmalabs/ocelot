"""Generate morphology-neutral hierarchical effector control.

An effector is addressable by itself, as a member of any named subsection,
and through nested subsections.  A hierarchical program binds an arbitrary
child motor program to a subsection and deterministically unrolls that intent
to primitive effector assignments.  Overlapping subsections retain every
assignment: overlap is executable only when all involved bindings explicitly
declare ``superpose``; otherwise the parent program fails closed.

The seed deliberately knows no limbs, joints, vehicles, or command alphabet.
It creates singleton scopes from a discovered morphology and materializes only
the composite scopes a body plan or learned program actually names.
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


def Plus(*items):
    return {"type": "Plus", "items": list(items)}


def P0(var, key):
    return Plus(A(var, key), L(0))


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def And(*items):
    return {"type": "And", "items": list(items)}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Not(arg):
    return {"type": "Not", "arg": arg}


def Neighbours(var, edge_type):
    return {"type": "Neighbours", "node": V(var), "edge_type": edge_type}


def Filter(source, var_name, predicate):
    return {
        "type": "Filter",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def Count(source):
    return {"type": "Count", "source": source}


def Exists(source, var_name, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def T(term):
    return {"__term__": term}


def singleton_scope_rule():
    scopes = Neighbours("topology", "has_embodied_control_subsection")
    known = Exists(
        scopes,
        "scope",
        And(
            Eq(A("scope", "scope_kind"), L("singleton")),
            Exists(
                Neighbours("scope", "addresses_embodied_effector"),
                "member",
                Eq(V("member"), V("effector")),
            ),
        ),
    )
    return {
        "name": "hec_materialize_singleton_scope_for_each_effector",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -30,
        "batch": True,
        "comment": "Every primitive remains independently addressable; composite scopes are created only when named or learned.",
        "match": [["topology", "has_embodied_effector", "effector"]],
        "where": And(
            Eq(P0("topology", "subsection_hierarchy_ready"), L(0)),
            Not(known),
        ),
        "effects": [
            ["add_node", "scope", "EmbodiedControlSubsection", {
                "scope_kind": "singleton",
                "status": "ready",
                "member_count": 1,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "topology", "has_embodied_control_subsection", "scope"],
            ["add_edge", "scope", "addresses_embodied_effector", "effector"],
        ],
    }


def rooted_subsection_rule():
    rooted = Exists(
        Neighbours("topology", "has_embodied_control_subsection"),
        "scope",
        And(
            Eq(A("scope", "scope_kind"), L("rooted_subsection")),
            Exists(
                Neighbours("scope", "rooted_at_embodied_effector"),
                "root",
                Eq(V("root"), V("effector")),
            ),
        ),
    )
    return {
        "name": "hec_materialize_rooted_subsection_for_each_effector",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -29,
        "batch": True,
        "comment": "One O(N) rooted scope per discovered control point represents the mechanically distal subsection beginning there.",
        "match": [
            ["topology", "has_embodied_effector", "effector"],
            ["topology", "has_embodied_control_subsection", "singleton"],
            ["singleton", "addresses_embodied_effector", "effector"],
        ],
        "where": And(
            Eq(P0("topology", "subsection_hierarchy_ready"), L(0)),
            Eq(A("singleton", "scope_kind"), L("singleton")),
            Not(rooted),
        ),
        "effects": [
            ["add_node", "scope", "EmbodiedControlSubsection", {
                "scope_kind": "rooted_subsection",
                "status": "ready",
                "member_count": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "topology", "has_embodied_control_subsection", "scope"],
            ["add_edge", "scope", "rooted_at_embodied_effector", "effector"],
            ["add_edge", "scope", "contains_embodied_control_subsection", "singleton"],
        ],
    }


def nest_mechanically_distal_subsection_rule():
    source_shallower = Gt(P0("target", "mount_depth"), P0("source", "mount_depth"))
    parent = "source_scope"
    child = "target_scope"
    existing = Exists(
        Neighbours(parent, "contains_embodied_control_subsection"),
        "known",
        Eq(V("known"), V(child)),
    )
    return {
        "name": "hec_nest_directly_distal_rooted_subsection",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -28,
        "batch": True,
        "comment": "Direct mechanical adjacency and observed mount depth, not anatomical names, form the rooted body-section hierarchy.",
        "match": [
            ["topology", "has_embodied_effector_relation", "relation"],
            ["relation", "has_embodied_effector_source", "source"],
            ["relation", "has_embodied_effector_target", "target"],
            ["topology", "has_embodied_control_subsection", "source_scope"],
            ["source_scope", "rooted_at_embodied_effector", "source"],
            ["topology", "has_embodied_control_subsection", "target_scope"],
            ["target_scope", "rooted_at_embodied_effector", "target"],
        ],
        "where": And(
            Eq(P0("topology", "subsection_hierarchy_ready"), L(0)),
            Eq(P0("relation", "mechanical_path_known"), L(1)),
            Eq(P0("relation", "mechanical_path_length"), L(1)),
            source_shallower,
            Not(existing),
        ),
        "effects": [[
            "add_edge", parent, "contains_embodied_control_subsection", child,
        ]],
    }


def nest_reverse_mechanically_distal_subsection_rule():
    """The topology pair order is canonical, not necessarily proximal-first."""
    rule = nest_mechanically_distal_subsection_rule()
    rule["name"] = "hec_nest_reverse_ordered_directly_distal_subsection"
    rule["where"] = And(
        Eq(P0("topology", "subsection_hierarchy_ready"), L(0)),
        Eq(P0("relation", "mechanical_path_known"), L(1)),
        Eq(P0("relation", "mechanical_path_length"), L(1)),
        Gt(P0("source", "mount_depth"), P0("target", "mount_depth")),
        Not(Exists(
            Neighbours("target_scope", "contains_embodied_control_subsection"),
            "known",
            Eq(V("known"), V("source_scope")),
        )),
    )
    rule["effects"] = [[
        "add_edge", "target_scope", "contains_embodied_control_subsection", "source_scope",
    ]]
    return rule


def inherit_nested_scope_member_rule():
    return {
        "name": "hec_unroll_nested_subsection_membership",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -27,
        "batch": True,
        "comment": "A subsection recursively addresses every primitive addressed by its child subsections.",
        "match": [
            ["parent", "contains_embodied_control_subsection", "child"],
            ["child", "addresses_embodied_effector", "effector"],
        ],
        "where": Not(Exists(
            Neighbours("parent", "addresses_embodied_effector"),
            "known",
            Eq(V("known"), V("effector")),
        )),
        "effects": [[
            "add_edge", "parent", "addresses_embodied_effector", "effector",
        ]],
    }


def reconcile_scope_width_rule():
    members = Neighbours("scope", "addresses_embodied_effector")
    return {
        "name": "hec_reconcile_named_subsection_width",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -26,
        "batch": True,
        "match": [["topology", "has_embodied_control_subsection", "scope"]],
        "where": Not(Eq(P0("scope", "member_count"), Count(members))),
        "effects": [["set_attr", "scope", "member_count", T(Count(members))]],
    }


def close_static_subsection_hierarchy_rule():
    scopes = Neighbours("topology", "has_embodied_control_subsection")
    singletons = Filter(
        scopes, "singleton_scope",
        Eq(A("singleton_scope", "scope_kind"), L("singleton")),
    )
    rooted = Filter(
        scopes, "rooted_scope",
        Eq(A("rooted_scope", "scope_kind"), L("rooted_subsection")),
    )
    incomplete_width = Exists(
        scopes, "width_scope",
        Not(Eq(
            P0("width_scope", "member_count"),
            Count(Neighbours("width_scope", "addresses_embodied_effector")),
        )),
    )
    incomplete_inheritance = Exists(
        scopes, "parent_scope",
        Exists(
            Neighbours(
                "parent_scope", "contains_embodied_control_subsection"
            ),
            "child_scope",
            Exists(
                Neighbours("child_scope", "addresses_embodied_effector"),
                "child_effector",
                Not(Exists(
                    Neighbours(
                        "parent_scope", "addresses_embodied_effector"
                    ),
                    "parent_effector",
                    Eq(V("parent_effector"), V("child_effector")),
                )),
            ),
        ),
    )
    return {
        "name": "hec_close_immutable_effector_subsection_hierarchy",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -25,
        "batch": False,
        "comment": "Once the immutable plant topology has one singleton and one rooted scope per effector and recursive membership is closed, retire its construction rules from the hot path.",
        "match": [["episode", "has_embodied_effector_topology", "topology"]],
        "where": And(
            Eq(P0("topology", "topology_facts_complete"), L(1)),
            Eq(P0("topology", "subsection_hierarchy_ready"), L(0)),
            Eq(Count(Neighbours("topology", "has_embodied_effector")),
               P0("topology", "effector_count")),
            Eq(Count(singletons), P0("topology", "effector_count")),
            Eq(Count(rooted), P0("topology", "effector_count")),
            Not(incomplete_width),
            Not(incomplete_inheritance),
        ),
        "effects": [[
            "set_attr", "topology", "subsection_hierarchy_ready", 1,
        ]],
    }


def unroll_program_binding_rule():
    existing = Filter(
        Neighbours("parent", "has_embodied_effector_program_assignment"),
        "assignment",
        And(
            Exists(
                Neighbours("assignment", "comes_from_embodied_program_binding"),
                "source_binding",
                Eq(V("source_binding"), V("binding")),
            ),
            Exists(
                Neighbours("assignment", "targets_embodied_effector"),
                "target_effector",
                Eq(V("target_effector"), V("effector")),
            ),
        ),
    )
    return {
        "name": "hec_unroll_subsection_program_to_primitive_assignment",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -20,
        "batch": True,
        "comment": "The binding is preserved while one explicit assignment is emitted for every addressed primitive.",
        "match": [
            ["parent", "includes_embodied_program_binding", "binding"],
            ["binding", "targets_embodied_control_subsection", "scope"],
            ["binding", "invokes_embodied_child_motor_program", "child_program"],
            ["scope", "addresses_embodied_effector", "effector"],
        ],
        "where": And(
            Eq(A("parent", "status"), L("assembling")),
            Eq(Count(existing), L(0)),
        ),
        "effects": [
            ["add_node", "assignment", "EmbodiedEffectorProgramAssignment", {
                "composition_operator": T(A("binding", "composition_operator")),
                "status": "assigned",
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "parent", "has_embodied_effector_program_assignment", "assignment"],
            ["add_edge", "assignment", "comes_from_embodied_program_binding", "binding"],
            ["add_edge", "assignment", "targets_embodied_effector", "effector"],
            ["add_edge", "assignment", "invokes_embodied_child_motor_program", "child_program"],
        ],
    }


def close_program_binding_rule():
    assignments = Filter(
        Neighbours("parent", "has_embodied_effector_program_assignment"),
        "assignment",
        Exists(
            Neighbours("assignment", "comes_from_embodied_program_binding"),
            "source_binding",
            Eq(V("source_binding"), V("binding")),
        ),
    )
    return {
        "name": "hec_close_fully_unrolled_program_binding",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -19,
        "batch": True,
        "match": [
            ["parent", "includes_embodied_program_binding", "binding"],
            ["binding", "targets_embodied_control_subsection", "scope"],
        ],
        "where": And(
            Eq(A("parent", "status"), L("assembling")),
            Gt(Count(Neighbours("scope", "addresses_embodied_effector")), L(0)),
            Eq(
                Count(assignments),
                Count(Neighbours("scope", "addresses_embodied_effector")),
            ),
            Not(Eq(A("binding", "status"), L("resolved"))),
        ),
        "effects": [["set_attr", "binding", "status", "resolved"]],
    }


def reject_implicit_overlap_rule():
    return {
        "name": "hec_reject_undeclared_or_exclusive_effector_overlap",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -18,
        "batch": False,
        "comment": "Graph order never resolves actuator contention. Every overlapping binding must explicitly opt into superposition.",
        "match": [
            ["parent", "has_embodied_effector_program_assignment", "first"],
            ["parent", "has_embodied_effector_program_assignment", "second"],
            ["first", "targets_embodied_effector", "effector"],
            ["second", "targets_embodied_effector", "effector"],
        ],
        "where": And(
            Eq(A("parent", "status"), L("assembling")),
            Not(Eq(V("first"), V("second"))),
            Or(
                Not(Eq(A("first", "composition_operator"), L("superpose"))),
                Not(Eq(A("second", "composition_operator"), L("superpose"))),
            ),
        ),
        "effects": [
            ["set_attr", "parent", "status", "rejected"],
            ["set_attr", "parent", "rejection_reason", "unresolved_effector_overlap"],
            ["add_edge", "parent", "has_conflicting_embodied_effector", "effector"],
        ],
    }


def close_hierarchical_program_rule():
    bindings = Neighbours("parent", "includes_embodied_program_binding")
    resolved = Filter(
        bindings,
        "binding",
        Eq(A("binding", "status"), L("resolved")),
    )
    return {
        "name": "hec_close_explicitly_composed_hierarchical_program",
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "order": -17,
        "batch": False,
        "comment": "A closed program is itself reusable as a child program at any higher body scope.",
        "match": [["agent", "has_embodied_hierarchical_control_program", "parent"]],
        "where": And(
            Eq(A("parent", "status"), L("assembling")),
            Gt(Count(bindings), L(0)),
            Eq(Count(bindings), Count(resolved)),
        ),
        "effects": [
            ["set_attr", "parent", "status", "ready"],
            ["set_attr", "parent", "binding_count", T(Count(bindings))],
            ["set_attr", "parent", "assignment_count", T(Count(
                Neighbours("parent", "has_embodied_effector_program_assignment")
            ))],
        ],
    }


def manifest():
    return {
        "id": "hierarchical_effector_control",
        "version": "1.1.0",
        "depends_on": ["decision_core"],
        "area": "hierarchical_effector_control",
        "latency_class": "hard_realtime",
        "description": "Morphology-neutral lazy body-subsection addressing and deterministic unrolling of nested, overlapping motor-program bindings to primitive effectors.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": "hierarchical_effector_control:scope",
                "src": {"type": "EmbodiedEffectorTopology", "var": "topology"},
                "edge_type": "has_embodied_control_subsection",
                "tgt": {"type": "EmbodiedControlSubsection", "var": "scope"},
            },
            {
                "provenance": "hierarchical_effector_control:nested_scope",
                "src": {"type": "EmbodiedControlSubsection", "var": "parent"},
                "edge_type": "contains_embodied_control_subsection",
                "tgt": {"type": "EmbodiedControlSubsection", "var": "child"},
            },
            {
                "provenance": "hierarchical_effector_control:scope_member",
                "src": {"type": "EmbodiedControlSubsection", "var": "scope"},
                "edge_type": "addresses_embodied_effector",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "hierarchical_effector_control:scope_root",
                "src": {"type": "EmbodiedControlSubsection", "var": "scope"},
                "edge_type": "rooted_at_embodied_effector",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "hierarchical_effector_control:topology_relation",
                "src": {"type": "EmbodiedEffectorTopology", "var": "topology"},
                "edge_type": "has_embodied_effector_relation",
                "tgt": {"type": "EmbodiedEffectorRelation", "var": "relation"},
            },
            {
                "provenance": "hierarchical_effector_control:relation_source",
                "src": {"type": "EmbodiedEffectorRelation", "var": "relation"},
                "edge_type": "has_embodied_effector_source",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "hierarchical_effector_control:relation_target",
                "src": {"type": "EmbodiedEffectorRelation", "var": "relation"},
                "edge_type": "has_embodied_effector_target",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "hierarchical_effector_control:program",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_hierarchical_control_program",
                "tgt": {"type": "EmbodiedHierarchicalControlProgram", "var": "program"},
            },
            {
                "provenance": "hierarchical_effector_control:binding",
                "src": {"type": "EmbodiedHierarchicalControlProgram", "var": "program"},
                "edge_type": "includes_embodied_program_binding",
                "tgt": {"type": "EmbodiedProgramBinding", "var": "binding"},
            },
            {
                "provenance": "hierarchical_effector_control:binding_scope",
                "src": {"type": "EmbodiedProgramBinding", "var": "binding"},
                "edge_type": "targets_embodied_control_subsection",
                "tgt": {"type": "EmbodiedControlSubsection", "var": "scope"},
            },
            {
                "provenance": "hierarchical_effector_control:binding_program",
                "src": {"type": "EmbodiedProgramBinding", "var": "binding"},
                "edge_type": "invokes_embodied_child_motor_program",
                "tgt": {"type": "Unknown", "var": "child_program"},
            },
            {
                "provenance": "hierarchical_effector_control:assignment",
                "src": {"type": "EmbodiedHierarchicalControlProgram", "var": "program"},
                "edge_type": "has_embodied_effector_program_assignment",
                "tgt": {"type": "EmbodiedEffectorProgramAssignment", "var": "assignment"},
            },
            {
                "provenance": "hierarchical_effector_control:assignment_binding",
                "src": {"type": "EmbodiedEffectorProgramAssignment", "var": "assignment"},
                "edge_type": "comes_from_embodied_program_binding",
                "tgt": {"type": "EmbodiedProgramBinding", "var": "binding"},
            },
            {
                "provenance": "hierarchical_effector_control:assignment_effector",
                "src": {"type": "EmbodiedEffectorProgramAssignment", "var": "assignment"},
                "edge_type": "targets_embodied_effector",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
            {
                "provenance": "hierarchical_effector_control:assignment_program",
                "src": {"type": "EmbodiedEffectorProgramAssignment", "var": "assignment"},
                "edge_type": "invokes_embodied_child_motor_program",
                "tgt": {"type": "Unknown", "var": "child_program"},
            },
            {
                "provenance": "hierarchical_effector_control:conflict",
                "src": {"type": "EmbodiedHierarchicalControlProgram", "var": "program"},
                "edge_type": "has_conflicting_embodied_effector",
                "tgt": {"type": "EmbodiedEffector", "var": "effector"},
            },
        ],
        "rules": [
            singleton_scope_rule(),
            rooted_subsection_rule(),
            nest_mechanically_distal_subsection_rule(),
            nest_reverse_mechanically_distal_subsection_rule(),
            inherit_nested_scope_member_rule(),
            reconcile_scope_width_rule(),
            close_static_subsection_hierarchy_rule(),
            unroll_program_binding_rule(),
            close_program_binding_rule(),
            reject_implicit_overlap_rule(),
            close_hierarchical_program_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "hierarchical_effector_control.json"
    payload = manifest()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output.relative_to(ROOT)} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
