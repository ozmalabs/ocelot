#!/usr/bin/env python3
"""Author the `invariant_miner` seed (Track I, I2.4 / I2.5 / I4.5).

Walls are explained before they are fought (Track I §3.3).

I2.4: a library of candidate homomorphisms held as `InvariantCandidate`
data. `perm_parity` (S_n -> Z2) is computed per permutation schema with the
`PermParity` Term; a schema of parity 0 `preserves_invariant` it.

I2.5: when a `SolveTask` is stuck, every invented process in its domain
preserves an invariant, and the task's state and goal DISAGREE on that
invariant, no amount of the invented family can finish the task. The graph
mints a `WallExplanation{invariant, family}` naming why, then breaks the
wall with the cheapest held process that CHANGES the invariant (parity 1),
and returns the task to `active`.

I4.5: the family law "every invented process is even" is promoted to a
`ProcessLaw` with a STRUCTURAL PROOF CERTIFICATE when every member is
proven even by construction: a commutator is always even (parity is a
homomorphism to an abelian group), and a conjugate s·t·s⁻¹ has the parity
of t, so a conjugate of a proven-even process is proven even. The
certificate is checked rule by rule over the `has_arg0` derivation edges;
it does not rely on the probe fingerprints. (`theorem_core` holds runtime
predicates, not proofs, so the certificate is recorded here.)
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (  # noqa: E402
    A, And, Append, Argmin, Count, Eq, Exists, Filter, Gt, In, L, Let, Lt, N, Not, OFFLINE_AREA,
    ONLINE_AREA, Or, PApply, PParity, Pick, Plus, StringConcat, T, ToJsonString, V, ZERO,
    is_none, not_none, policy_on, productions, rule,
)

SEED_ID = "invariant_miner"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"
CONJ_OPS = ["conjugate", "conjugate_closure"]


def invented(var="d"):
    return Filter(N(var, "has_invented_process"), "iv", Eq(A("iv", "status"), L("active")))


def parity_rules():
    return [
        rule("im_parity_of_schema", OFFLINE_AREA, 80,
             "I2.4: compute the perm_parity homomorphism of every permutation schema.",
             [["agent", "has_invariant_miner_policy", "pol"], ["agent", "has_process_schema", "s"]],
             And(policy_on(), Eq(A("s", "kind"), L("permutation")), not_none(A("s", "params")),
                 Not(Eq(A("s", "parity_checked"), L(1)))),
             [["set_attr", "s", "parity", T(PParity(A("s", "params")))],
              ["set_attr", "s", "parity_checked", 1]]),
        rule("im_preserves_parity", OFFLINE_AREA, 81,
             "I2.4: an even permutation preserves the parity of every state it acts on.",
             [["agent", "has_invariant_miner_policy", "pol"],
              ["agent", "has_invariant_candidate", "inv"],
              ["agent", "has_process_schema", "s"]],
             And(policy_on(), Eq(A("inv", "name"), L("perm_parity")),
                 Eq(A("s", "parity_checked"), L(1)), Eq(A("s", "parity"), ZERO),
                 Not(In(V("inv"), N("s", "preserves_invariant")))),
             [["add_edge", "s", "preserves_invariant", "inv", {}]]),
    ]


def family_preserves_parity():
    fam = invented()
    return And(Gt(Count(fam), ZERO),
               Not(Exists(fam, "fx", Not(Eq(A("fx", "parity"), ZERO)))))


def wall_rules():
    match = [
        ["agent", "has_invariant_miner_policy", "pol"],
        ["agent", "has_solve_task", "t"],
        ["t", "about_domain", "d"],
        ["agent", "has_invariant_candidate", "inv"],
    ]
    open_wall = Exists(N("t", "explained_by_wall"), "ow", Eq(A("ow", "status"), L("open")))
    breakers = Filter(N("d", "has_held_process"), "h",
                      And(Eq(A("h", "status"), L("active")), Eq(A("h", "parity"), L(1))))
    breaker = Argmin(breakers, "h", A("h", "cost"))
    with_b = lambda term: T(Let("bk", breaker, term))  # noqa: E731
    break_match = [
        ["agent", "has_invariant_miner_policy", "pol"],
        ["agent", "has_solve_task", "t"],
        ["t", "explained_by_wall", "w"],
        ["t", "about_domain", "d"],
    ]
    return [
        rule("im_explain_parity_wall", ONLINE_AREA, 20,
             "I2.5: a stuck task whose state and goal differ in parity, in a domain whose every "
             "invented process is even, cannot be finished by the invented family. Name the wall.",
             match,
             And(policy_on(), Eq(A("t", "status"), L("stuck")), Eq(A("inv", "name"), L("perm_parity")),
                 Eq(A("d", "kind"), L("permutation")), family_preserves_parity(),
                 Not(Eq(PParity(A("t", "state")), PParity(A("t", "goal")))),
                 Lt(Count(N("t", "explained_by_wall")), A("pol", "max_walls")), Not(open_wall)),
             [
                 ["add_node", "w", "WallExplanation", {
                     "invariant": "perm_parity",
                     "family": "invented",
                     "family_size": T(Count(invented())),
                     "domain": T(A("d", "name")),
                     "state_parity": T(PParity(A("t", "state"))),
                     "goal_parity": T(PParity(A("t", "goal"))),
                     "status": "open",
                 }],
                 ["add_edge", "t", "explained_by_wall", "w", {}],
                 ["add_edge", "agent", "has_wall_explanation", "w", {}],
             ]),
        rule("im_break_parity_wall", ONLINE_AREA, 21,
             "I2.5: break the wall with the cheapest held process that changes the invariant "
             "(an odd permutation), then resume solving.",
             break_match,
             And(policy_on(), Eq(A("w", "status"), L("open")), Gt(Count(breakers), ZERO)),
             [
                 ["set_attr", "t", "state", with_b(PApply(A("bk", "params"), A("t", "state")))],
                 ["set_attr", "t", "steps", T(Plus(A("t", "steps"), L(1)))],
                 ["set_attr", "t", "moves", with_b(Plus(A("t", "moves"), A("bk", "cost")))],
                 ["set_attr", "t", "trace", with_b(Append(A("t", "trace"), V("bk")))],
                 ["set_attr", "w", "breaking_process", with_b(A("bk", "name"))],
                 ["set_attr", "w", "status", "broken"],
                 ["set_attr", "t", "status", "active"],
             ]),
        rule("im_wall_unbreakable", ONLINE_AREA, 21,
             "I2.5: no held process changes the invariant; the wall stands (reported, not fought).",
             break_match,
             And(policy_on(), Eq(A("w", "status"), L("open")), Eq(Count(breakers), ZERO)),
             [["set_attr", "w", "status", "unbreakable"]]),
    ]


def proof_rules():
    proven = lambda var: Eq(A(var, "parity_proof"), L("even_by_construction"))  # noqa: E731
    match = [["agent", "has_invariant_miner_policy", "pol"], ["agent", "has_process_schema", "s"],
             ["s", "has_arg0", "x"]]
    held_even = And(Eq(A("x", "provenance"), L("held")), Eq(A("x", "parity_checked"), L(1)),
                    Eq(A("x", "parity"), ZERO))
    member_ok = lambda var: proven(var)  # noqa: E731
    return [
        rule("im_proof_commutator_even", OFFLINE_AREA, 85,
             "I4.5 certificate step: a commutator [a,b] is even for any a, b (parity is a "
             "homomorphism into the abelian group Z2).",
             [["agent", "has_invariant_miner_policy", "pol"], ["agent", "has_process_schema", "s"]],
             And(policy_on(), Eq(A("s", "kind"), L("permutation")), Eq(A("s", "operator"), L("commutator")),
                 Not(proven("s"))),
             [["set_attr", "s", "parity_proof", "even_by_construction"]]),
        rule("im_proof_conjugate_preserves", OFFLINE_AREA, 86,
             "I4.5 certificate step: a conjugate s·t·s⁻¹ has the parity of t; it is proven even when "
             "t is a held process of exact parity 0 or t is itself proven even.",
             match,
             And(policy_on(), Eq(A("s", "kind"), L("permutation")),
                 Or(*[Eq(A("s", "operator"), L(op)) for op in CONJ_OPS]),
                 Or(proven("x"), held_even), Not(proven("s"))),
             [["set_attr", "s", "parity_proof", "even_by_construction"]]),
        rule("im_family_parity_law", OFFLINE_AREA, 87,
             "I4.5: when every active invented process in a permutation domain carries the "
             "structural certificate, promote 'the invented family is even' to a proven law.",
             [["agent", "has_invariant_miner_policy", "pol"], ["agent", "has_process_domain", "d"]],
             And(policy_on(), Eq(A("d", "kind"), L("permutation")), Gt(Count(invented()), ZERO),
                 Not(Exists(invented(), "fx", Not(member_ok("fx")))),
                 Not(Exists(N("agent", "has_process_law"), "lw",
                            And(Eq(A("lw", "kind"), L("family_invariant")),
                                Eq(A("lw", "domain"), A("d", "name")),
                                Eq(A("lw", "family_size"), Count(invented())))))),
             [
                 ["add_node", "law", "ProcessLaw", {
                     "kind": "family_invariant",
                     "statement": T(StringConcat(L("every invented process in "), A("d", "name"),
                                                 L(" preserves perm_parity"))),
                     "domain": T(A("d", "name")),
                     "family_size": T(Count(invented())),
                     "invariant": "perm_parity",
                     "proof_kind": "structural_induction",
                     "proof_steps": "commutator_even; conjugate_preserves_parity",
                     "proven": 1,
                     "status": "proven",
                 }],
                 ["add_edge", "agent", "has_process_law", "law", {}],
             ],
             batch=True),
    ]


def build():
    specs = [
        ("Agent", "has_invariant_miner_policy", "InvariantMinerPolicy"),
        ("Agent", "has_invariant_candidate", "InvariantCandidate"),
        ("ProcessSchema", "preserves_invariant", "InvariantCandidate"),
        ("SolveTask", "explained_by_wall", "WallExplanation"),
        ("Agent", "has_wall_explanation", "WallExplanation"),
        ("Agent", "has_process_law", "ProcessLaw"),
    ]
    return {
        "id": SEED_ID,
        "version": "1.0.0",
        "depends_on": ["process_schema"],
        "self_load_only": True,
        "area": OFFLINE_AREA,
        "description": (
            "Track I I2.4/I2.5/I4.5: invariants as candidate homomorphisms, wall explanations "
            "that name why an invented family cannot finish a task, the cheapest wall-breaking "
            "held process, and structural proof certificates for family invariants."
        ),
        "microtheory": {
            "name": SEED_ID,
            "description": "Explain a wall by an invariant before fighting it.",
        },
        "nodes": [
            {"local_id": 0, "type": "InvariantMinerPolicy", "attrs": {
                "name": "core_invariant_miner_policy", "enabled": 0.0, "max_walls": 3.0}},
            {"local_id": 1, "type": "InvariantCandidate", "attrs": {
                "name": "perm_parity", "applies_to_kind": "permutation",
                "homomorphism": "PermParity", "codomain": "Z2"}},
            {"local_id": 2, "type": "InvariantCandidate", "attrs": {
                "name": "det_sign", "applies_to_kind": "integer_matrix",
                "homomorphism": "MatDet sign", "codomain": "{-1, 1}",
                "note": "data only: no matrix domain is in PMB v1 yet"}},
        ],
        "edges": [
            {"src": {"role": "agent_root"}, "type": "has_invariant_miner_policy", "tgt": {"local": 0}, "attrs": {}},
            {"src": {"role": "agent_root"}, "type": "has_invariant_candidate", "tgt": {"local": 1}, "attrs": {}},
            {"src": {"role": "agent_root"}, "type": "has_invariant_candidate", "tgt": {"local": 2}, "attrs": {}},
        ],
        "productions": productions(SEED_ID, specs),
        "rules": parity_rules() + wall_rules() + proof_rules(),
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
