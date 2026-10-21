#!/usr/bin/env python3
"""Author the `process_schema` seed (Track I, I1.1 / I1.3 / I1.4).

One candidate-process representation for every process the agent holds.
A `ProcessSchema` node carries:

    kind         permutation | generator_step | program | capability |
                 transition | motor | delta | ...
    domain       the `ProcessDomain.name` whose probe battery defines effects
    params       the process VALUE the Rust process-algebra Terms dispatch on
                 (None for kinds without an exact evaluator)
    pre / post   simple predicate values where the source form has them
    invariants   filled by `invariant_miner`
    cost         primitive steps (held = 1; invented = operator cost formula)
    provenance   held | invented_by:<op> | lifted | induced | library_learned
    fingerprint  `EffectFingerprint(params, domain.probes)`
    realised_by  the native node it views (a Node value; see below)

Nothing is migrated. A VIEW RULE per existing native form mints the schema:
DimensionGenerator, Program, CapabilityProgram, TransitionHypothesis,
EmbodiedMotorProgram, FamilyProgram. `DimensionGenerator` and
`FamilyProgram` nodes are edge-less, and rules can bind match variables
only through edges, so every view rule iterates with one `Pick` of an
unviewed node per pass and records the source as a `realised_by` Node attr
rather than an edge (no effect can add an edge to a computed node).

I1.3: a `ProcessDomain` holds its probe battery as graph data; one rule
computes each schema's fingerprint and support from it.
I1.4: dedup by effect, keeping the cheapest: a newly fingerprinted schema
whose effect is already held at a lower (or equal, older) cost is marked
`merged`; a costlier older duplicate is merged into it.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (  # noqa: E402
    A, And, Count, Eq, Exists, Filter, Gt, IfThenElse, L, Let, Lt, N, Not, NodesOfType, Or,
    OFFLINE_AREA, PFingerprint, PSupport, Pick, T, V, Vec, ZERO, not_none,
    policy_on, productions, rule,
)


def IndexedMap(source, item_name, index_name, value):
    return {"type": "IndexedMap", "source": source, "item_name": item_name,
            "index_name": index_name, "value": value}

SEED_ID = "process_schema"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"

# Asymmetric, origin-normalised probe shapes (sorted relation lists), so the
# eight dihedral transforms all have distinct effects on them.
F_PENTOMINO = [["cell", 0, 1], ["cell", 0, 2], ["cell", 1, 0], ["cell", 1, 1], ["cell", 2, 1]]
L_HEXOMINO = [["cell", 0, 0], ["cell", 1, 0], ["cell", 2, 0], ["cell", 3, 0], ["cell", 3, 1], ["cell", 0, 1]]
SHAPE_PROBES = [sorted(F_PENTOMINO), sorted(L_HEXOMINO)]
SHAPE_DOMAIN = "shape_coords_2d"


def held_for(domain_var="d", schema_var="s"):
    return And(
        Eq(A(schema_var, "domain"), A(domain_var, "name")),
        Eq(A(schema_var, "status"), L("active")),
    )


def domain_identity_rule():
    identity_probe = Exists(
        A("d", "probes"), "pr",
        Not(Exists(IndexedMap(V("pr"), "px", "pi", Eq(V("px"), V("pi"))), "pb", Not(V("pb")))),
    )
    return rule(
        "ps_domain_identity_fingerprint", OFFLINE_AREA, 10,
        "Record the identity process's fingerprint on a domain's probe battery (the empty "
        "sequence applied to every probe), so laws and identity checks compare like with like. "
        "A permutation domain whose probes include the identity state has EXACT fingerprints: "
        "the identity probe's image is the permutation itself.",
        [["agent", "has_process_schema_policy", "pol"], ["agent", "has_process_domain", "d"]],
        And(policy_on(), Not(Eq(A("d", "identity_checked"), L(1)))),
        [
            ["set_attr", "d", "identity_fingerprint", T(PFingerprint(Vec(L("seq")), A("d", "probes")))],
            ["set_attr", "d", "exact_probes",
             T(IfThenElse(And(Eq(A("d", "kind"), L("permutation")), identity_probe), L(1), L(0)))],
            ["set_attr", "d", "identity_checked", 1],
        ],
    )


def fingerprint_rule():
    return rule(
        "ps_fingerprint_from_domain_probes", OFFLINE_AREA, 11,
        "I1.3: a schema's effect is its behaviour on its domain's fixed probe battery. "
        "Unevaluable kinds get fingerprint None (honest: no exact evaluator).",
        [
            ["agent", "has_process_schema_policy", "pol"],
            ["agent", "has_process_schema", "s"],
            ["agent", "has_process_domain", "d"],
        ],
        And(policy_on(), Eq(A("s", "domain"), A("d", "name")),
            Not(Eq(A("s", "fingerprint_checked"), L(1)))),
        [
            ["set_attr", "s", "fingerprint", T(PFingerprint(A("s", "params"), A("d", "probes")))],
            ["set_attr", "s", "support", T(PSupport(A("s", "params")))],
            ["set_attr", "s", "fingerprint_checked", 1],
        ],
    )


def index_held_rule():
    return rule(
        "ps_index_held_process", OFFLINE_AREA, 12,
        "Link each active held schema to its domain (`has_held_process`), so invention rules "
        "join over distinct edge types and stay semi-naive.",
        [
            ["agent", "has_process_schema_policy", "pol"],
            ["agent", "has_process_schema", "s"],
            ["agent", "has_process_domain", "d"],
        ],
        And(policy_on(), held_for(), Eq(A("s", "provenance"), L("held")),
            Not(Eq(A("s", "indexed"), L(1)))),
        [
            ["add_edge", "d", "has_held_process", "s", {}],
            ["set_attr", "s", "indexed", 1],
        ],
    )


def _same_effect(a, b):
    return And(
        Eq(A(b, "domain"), A(a, "domain")),
        Eq(A(a, "status"), L("active")),
        Not(Eq(V(a), V(b))),
        not_none(A(b, "fingerprint")),
        Eq(A(a, "fingerprint"), A(b, "fingerprint")),
    )


def merge_newcomer_rule():
    return rule(
        "ps_merge_newcomer_into_cheaper_effect", OFFLINE_AREA, 13,
        "I1.4: a newly fingerprinted schema whose effect is already held at lower cost "
        "(or equal cost by an already-checked or older schema) is the same process; mark it "
        "merged into the cheaper one.",
        [
            ["agent", "has_process_schema_policy", "pol"],
            ["agent", "has_process_schema", "b"],
            ["agent", "has_process_schema", "a"],
        ],
        And(
            policy_on(),
            Eq(A("b", "fingerprint_checked"), L(1)),
            Not(Eq(A("b", "dedup_checked"), L(1))),
            Eq(A("b", "status"), L("active")),
            _same_effect("a", "b"),
            Or(
                Lt(A("a", "cost"), A("b", "cost")),
                And(Eq(A("a", "cost"), A("b", "cost")),
                    Or(Eq(A("a", "dedup_checked"), L(1)), Lt(V("a"), V("b")))),
            ),
        ),
        [
            ["set_attr", "b", "status", "merged"],
            ["add_edge", "b", "merged_into", "a", {}],
            ["set_attr", "b", "dedup_checked", 1],
        ],
    )


def merge_older_costlier_rule():
    return rule(
        "ps_merge_older_costlier_effect", OFFLINE_AREA, 14,
        "I1.4: a newly fingerprinted schema that is CHEAPER than an already-checked schema "
        "with the same effect replaces it; the older, costlier one is merged.",
        [
            ["agent", "has_process_schema_policy", "pol"],
            ["agent", "has_process_schema", "b"],
            ["agent", "has_process_schema", "a"],
        ],
        And(
            policy_on(),
            Eq(A("b", "fingerprint_checked"), L(1)),
            Not(Eq(A("b", "dedup_checked"), L(1))),
            Eq(A("b", "status"), L("active")),
            Eq(A("a", "dedup_checked"), L(1)),
            _same_effect("a", "b"),
            Lt(A("b", "cost"), A("a", "cost")),
        ),
        [
            ["set_attr", "a", "status", "merged"],
            ["add_edge", "a", "merged_into", "b", {}],
        ],
    )


def settle_dedup_rule():
    return rule(
        "ps_settle_dedup_check", OFFLINE_AREA, 15,
        "Close the dedup check for a fingerprinted schema once the merge rules have run.",
        [["agent", "has_process_schema_policy", "pol"], ["agent", "has_process_schema", "s"]],
        And(policy_on(), Eq(A("s", "fingerprint_checked"), L(1)),
            Not(Eq(A("s", "dedup_checked"), L(1)))),
        [["set_attr", "s", "dedup_checked", 1]],
    )


def _unviewed(src_type):
    return Filter(
        NodesOfType(src_type), "g",
        Not(Exists(NodesOfType("ProcessSchema"), "vs", Eq(A("vs", "realised_by"), V("g")))),
    )


def view_rule(src_type, kind, domain_term, params_term, extra=None, order=5):
    """Mint one ProcessSchema for one not-yet-viewed native node per pass."""
    picked = Pick(_unviewed(src_type))

    def of_g(term):
        return T(Let("g", picked, term))

    attrs = {
        "kind": kind,
        "domain": of_g(domain_term),
        "name": of_g(A("g", "name")),
        "params": of_g(params_term),
        "pre": None,
        "post": None,
        "invariants": [],
        "cost": 1.0,
        "provenance": "held",
        "source_type": src_type,
        "realised_by": of_g(V("g")),
        "status": "active",
    }
    for k, v in (extra or {}).items():
        attrs[k] = of_g(v)
    return rule(
        f"ps_view_{src_type[0].lower()}{''.join('_' + c.lower() if c.isupper() else c for c in src_type[1:])}",
        OFFLINE_AREA, order,
        f"I1.1 view rule: mint the ProcessSchema view of one {src_type} per pass "
        "(no migration; the native node stays authoritative and is recorded as `realised_by`).",
        [["agent", "has_process_schema_policy", "pol"]],
        And(policy_on(), Eq(A("pol", "view_enabled"), L(1.0)), Gt(Count(_unviewed(src_type)), ZERO)),
        [
            ["add_node", "s", "ProcessSchema", attrs],
            ["add_edge", "agent", "has_process_schema", "s", {}],
        ],
        batch=True,
    )


def view_rules():
    gen_params = Vec(
        L("gen"), A("g", "kind"), A("g", "coord_dims"), A("g", "modulus"),
        A("g", "matrix"), A("g", "offset"), L(1),
    )
    native = lambda t: L(f"native:{t}")  # noqa: E731
    return [
        view_rule("DimensionGenerator", "generator_step", L(SHAPE_DOMAIN), gen_params),
        view_rule("Program", "program", native("Program"), L(None),
                  extra={"construction": A("g", "construction")}),
        view_rule("CapabilityProgram", "capability", native("CapabilityProgram"), L(None),
                  extra={"order": A("g", "order")}),
        view_rule("TransitionHypothesis", "transition", native("TransitionHypothesis"), L(None),
                  extra={"pre_state_kind": A("g", "source_state_kind"),
                         "action_kind": A("g", "action_kind"),
                         "post_state_kind": A("g", "successor_state_kind")}),
        view_rule("EmbodiedMotorProgram", "motor", native("EmbodiedMotorProgram"), L(None)),
        view_rule("FamilyProgram", "family_program", native("FamilyProgram"), L(None)),
    ]


def build():
    specs = [
        ("Agent", "has_process_schema_policy", "ProcessSchemaPolicy"),
        ("Agent", "has_process_schema", "ProcessSchema"),
        ("Agent", "has_process_domain", "ProcessDomain"),
        ("ProcessDomain", "has_held_process", "ProcessSchema"),
        ("ProcessDomain", "has_invented_process", "ProcessSchema"),
        ("ProcessSchema", "merged_into", "ProcessSchema"),
    ]
    return {
        "id": SEED_ID,
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "area": OFFLINE_AREA,
        "description": (
            "Track I I1: one ProcessSchema representation for every held process, minted by "
            "view rules over the six native forms, fingerprinted on each domain's probe "
            "battery, and deduplicated by effect keeping the cheapest."
        ),
        "microtheory": {
            "name": SEED_ID,
            "description": "A process is known by its effect on a fixed battery of probe states.",
        },
        "nodes": [
            {"local_id": 0, "type": "ProcessSchemaPolicy", "attrs": {
                "name": "core_process_schema_policy", "enabled": 0.0, "view_enabled": 1.0}},
            {"local_id": 1, "type": "ProcessDomain", "attrs": {
                "name": SHAPE_DOMAIN, "kind": "generator_step", "probes": SHAPE_PROBES,
                "description": "Shape signatures ['cell', r, c]; the DimensionGenerator view domain."}},
        ],
        "edges": [
            {"src": {"role": "agent_root"}, "type": "has_process_schema_policy",
             "tgt": {"local": 0}, "attrs": {}},
            {"src": {"role": "agent_root"}, "type": "has_process_domain",
             "tgt": {"local": 1}, "attrs": {}},
        ],
        "productions": productions(SEED_ID, specs),
        "rules": view_rules() + [
            domain_identity_rule(),
            fingerprint_rule(),
            index_held_rule(),
            merge_newcomer_rule(),
            merge_older_costlier_rule(),
            settle_dedup_rule(),
        ],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
