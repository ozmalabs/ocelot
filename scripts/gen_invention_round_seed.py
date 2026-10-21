#!/usr/bin/env python3
"""Author the `invention_round` seed (Track I, I2.2 / I2.3 / I3.3, laws for I4.5).

An `InventionRound` is a budgeted episode of invention over one
`ProcessDomain`. It is opened by the graph in two situations:

* IMPASSE: a `SolveTask` in the domain is `stuck` (held processes cannot
  reduce its distance to goal) and no round exists for the domain;
* OFFLINE: an offline `MemoryCycle` (consolidation scheduler) is pending and
  the domain has held processes but no round yet.

Funding goes through the generic ThinkingBudget pending-request contract
(`ThinkingBudgetRequest{status: pending, cost, requester_kind}` +
`draws_on_thinking_budget`); with no ThinkingBudget node at all the round
opens directly.

While a round is `active`, one rule per operator applies that operator over
the domain's held processes, computes the candidate's fingerprint on the
domain probes, and MINTS it only when it is novel by effect (no schema in
the domain has that fingerprint), not the identity, and precise
(`0 < support <= policy.max_support`, or support undefined for kinds whose
support is probe-relative). The conjugation-closure rule (I2.3) then
conjugates every precise invention by every held process until no novel
conjugate remains: closure under conjugation by single held processes is
closure under conjugation by any word of them.

Laws fall out of the same algebra and are recorded as `ProcessLaw` nodes:
orders (`a^k = I`), commuting pairs, and conjugation-inverts relations.
A law in a permutation domain whose probes include the identity state is
EXACT (the identity probe's image is the permutation itself); otherwise it
is verified on probes only.

I3.3 strategy library: `StrategyRecord{kind, operator, trials, yields}` is
kept live per (domain kind, operator). A new round in a domain kind with
records enables operators by `SoftWeights` over their yield rates; untried
operators keep an optimistic prior so they are still explored.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (  # noqa: E402
    A, And, Count, Div, Eq, Exists, Filter, FilterList, Gt, Gte, IfThenElse, In, L,
    Let, Lt, Lte, MapList, Max, N, NodesWhere, Not, Nth, OFFLINE_AREA, Or, PCommutator,
    PCompose, PConjugate, PFingerprint, PInverse, PPower, PSupport, Plus, SoftWeights,
    StringConcat, Sum, T, Times, V, Vec, ZERO, is_none, not_none, policy_on, productions,
    rule,
)

SEED_ID = "invention_round"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"
BASE_OPERATORS = ["inverse", "compose", "conjugate", "commutator", "power2", "power3", "root2"]
BINARY = {"compose", "conjugate", "commutator"}


# ---------------------------------------------------------------- helpers --

def tree(var):
    """The expression tree of a schema, falling back to its name."""
    return IfThenElse(is_none(A(var, "expr_tree")), A(var, "name"), A(var, "expr_tree"))


def novel_in_domain(fp):
    return Not(Exists(NodesWhere("ProcessSchema", "fingerprint", fp), "x",
                      Eq(A("x", "domain"), A("d", "name"))))


def precise(proc):
    sup = PSupport(proc)
    return Or(is_none(sup), And(Gt(sup, ZERO), Lte(sup, A("pol", "max_support"))))


def under_cap():
    return Lt(Count(N("d", "has_invented_process")), A("pol", "max_invented"))


def round_active(op_name=None):
    items = [policy_on(), Eq(A("r", "status"), L("active"))]
    if op_name is not None:
        items.append(In(L(op_name), A("r", "enabled_ops")))
    return items


def mint_effects(proc, fp, op, cost, name, expr, args):
    effects = [
        ["add_node", "s", "ProcessSchema", {
            "kind": T(A(args[0], "kind")),
            "domain": T(A("d", "name")),
            "domain_kind": T(A("d", "kind")),
            "name": T(name),
            "params": T(proc),
            "fingerprint": T(fp),
            "support": T(PSupport(proc)),
            "cost": T(cost),
            "provenance": f"invented_by:{op}",
            "operator": op,
            "expr_tree": T(expr),
            "invariants": [],
            "status": "active",
            "fingerprint_checked": 1,
            "dedup_checked": 1,
            "indexed": 1,
            "invented": 1,
        }],
        ["add_edge", "agent", "has_process_schema", "s", {}],
        ["add_edge", "d", "has_invented_process", "s", {}],
        ["add_edge", "s", "has_arg0", args[0], {}],
    ]
    if len(args) > 1:
        effects.append(["add_edge", "s", "has_arg1", args[1], {}])
    return effects


def binary_operator_rule(op, order):
    a, b = A("a", "params"), A("b", "params")
    proc = {"commutator": PCommutator(a, b), "conjugate": PConjugate(a, b),
            "compose": PCompose(a, b)}[op]
    cost = {"commutator": Times(L(2.0), Plus(A("a", "cost"), A("b", "cost"))),
            "conjugate": Plus(A("a", "cost"), Times(L(2.0), A("b", "cost"))),
            "compose": Plus(A("a", "cost"), A("b", "cost"))}[op]
    name = {"commutator": StringConcat(L("["), A("a", "name"), L(","), A("b", "name"), L("]")),
            "conjugate": StringConcat(A("b", "name"), L("·"), A("a", "name"), L("·"), A("b", "name"), L("⁻¹")),
            "compose": StringConcat(A("a", "name"), L("·"), A("b", "name"))}[op]
    fp = PFingerprint(proc, A("d", "probes"))
    return rule(
        f"ir_invent_{op}", OFFLINE_AREA, 30 + order,
        f"I2.2: apply `{op}` over pairs of held processes in the round's domain; mint the result "
        "only if it is novel by effect, not the identity, and precise.",
        [
            ["agent", "has_invention_policy", "pol"],
            ["agent", "has_invention_round", "r"],
            ["r", "about_domain", "d"],
            ["d", "has_held_process", "a"],
            ["d", "has_held_process", "b"],
        ],
        And(*round_active(op), Not(Eq(V("a"), V("b"))), under_cap(),
            not_none(fp), Not(Eq(fp, A("d", "identity_fingerprint"))), precise(proc),
            novel_in_domain(fp)),
        mint_effects(proc, fp, op, cost, name, Vec(L(op), tree("a"), tree("b")), ["a", "b"]),
    )


def unary_operator_rule(op, order):
    a = A("a", "params")
    proc = {"inverse": PInverse(a), "power2": PPower(a, 2), "power3": PPower(a, 3)}[op]
    cost = {"inverse": A("a", "cost"), "power2": Times(L(2.0), A("a", "cost")),
            "power3": Times(L(3.0), A("a", "cost"))}[op]
    suffix = {"inverse": "⁻¹", "power2": "²", "power3": "³"}[op]
    fp = PFingerprint(proc, A("d", "probes"))
    return rule(
        f"ir_invent_{op}", OFFLINE_AREA, 30 + order,
        f"I2.2: apply `{op}` to each held process in the round's domain; mint if novel, "
        "not the identity, and precise.",
        [
            ["agent", "has_invention_policy", "pol"],
            ["agent", "has_invention_round", "r"],
            ["r", "about_domain", "d"],
            ["d", "has_held_process", "a"],
        ],
        And(*round_active(op), under_cap(), not_none(fp),
            Not(Eq(fp, A("d", "identity_fingerprint"))), precise(proc), novel_in_domain(fp)),
        mint_effects(proc, fp, op, cost, StringConcat(A("a", "name"), L(suffix)),
                     Vec(L(op), tree("a")), ["a"]),
    )


def root_relation_rule():
    fp = PFingerprint(PCompose(A("x", "params"), A("x", "params")), A("d", "probes"))
    return rule(
        "ir_record_square_root", OFFLINE_AREA, 38,
        "I2.1 root(2): a held process x whose square has the effect of an invented process a "
        "is recorded as `x -root_of-> a` (a search over the library, not a mint).",
        [
            ["agent", "has_invention_policy", "pol"],
            ["agent", "has_invention_round", "r"],
            ["r", "about_domain", "d"],
            ["d", "has_held_process", "x"],
            ["d", "has_invented_process", "a"],
        ],
        And(*round_active("root2"), not_none(A("a", "fingerprint")),
            Eq(fp, A("a", "fingerprint")), Not(In(V("a"), N("x", "root_of")))),
        [["add_edge", "x", "root_of", "a", {"k": 2}]],
    )


def closure_rule():
    t, s = A("t", "params"), A("s", "params")
    proc = PConjugate(t, s)
    fp = PFingerprint(proc, A("d", "probes"))
    return rule(
        "ir_conjugation_closure", OFFLINE_AREA, 40,
        "I2.3: conjugate every precise invention by every held process; mint novel conjugates "
        "of the same precision. Iterated to fixpoint this is closure under conjugation by any "
        "word of held processes (the probe's three_cycle_closure, as a rule).",
        [
            ["agent", "has_invention_policy", "pol"],
            ["agent", "has_invention_round", "r"],
            ["r", "about_domain", "d"],
            ["d", "has_invented_process", "t"],
            ["d", "has_held_process", "s"],
        ],
        And(*round_active(), Eq(A("pol", "closure_enabled"), L(1.0)),
            Eq(A("t", "status"), L("active")), not_none(A("t", "support")),
            Eq(A("t", "support"), A("pol", "max_support")), under_cap(),
            not_none(fp), Eq(PSupport(proc), A("t", "support")), novel_in_domain(fp)),
        mint_effects(
            proc, fp, "conjugate_closure",
            Plus(A("t", "cost"), Times(L(2.0), A("s", "cost"))),
            StringConcat(A("s", "name"), L("⟨"), A("t", "name"), L("⟩")),
            Vec(L("conjugate"), tree("t"), tree("s")), ["t", "s"],
        ),
    )


# -------------------------------------------------------------- laws -------

def law_effects(kind, statement, extra, about):
    attrs = {
        "kind": kind,
        "statement": T(statement),
        "domain": T(A("d", "name")),
        "exact": T(A("d", "exact_probes")),
        "evidence": "fingerprint_equality",
        "status": "verified",
    }
    attrs.update(extra)
    effects = [
        ["add_node", "law", "ProcessLaw", attrs],
        ["add_edge", "agent", "has_process_law", "law", {}],
    ]
    for v in about:
        effects.append(["add_edge", "law", "about_process", v, {}])
    return effects


def no_order_law_yet():
    return Not(Exists(N("agent", "has_process_law"), "lw",
                      And(Eq(A("lw", "kind"), L("order")), In(V("a"), N("lw", "about_process")))))


def order_law_rule(k):
    fp = PFingerprint(PPower(A("a", "params"), k), A("d", "probes"))
    return rule(
        f"ir_law_order_{k}", OFFLINE_AREA, 50 + k,
        f"Law: the smallest k with a^k = identity on the probes (here k = {k}).",
        [
            ["agent", "has_invention_policy", "pol"],
            ["agent", "has_invention_round", "r"],
            ["r", "about_domain", "d"],
            ["d", "has_held_process", "a"],
        ],
        And(*round_active(), not_none(fp), Eq(fp, A("d", "identity_fingerprint")), no_order_law_yet()),
        law_effects("order", StringConcat(A("a", "name"), L(f"^{k} = I")), {"k": float(k)}, ["a"]),
    )


def commute_law_rule():
    fp = PFingerprint(PCommutator(A("a", "params"), A("b", "params")), A("d", "probes"))
    return rule(
        "ir_law_commute", OFFLINE_AREA, 60,
        "Law: two held processes commute when their commutator is the identity on the probes.",
        [
            ["agent", "has_invention_policy", "pol"],
            ["agent", "has_invention_round", "r"],
            ["r", "about_domain", "d"],
            ["d", "has_held_process", "a"],
            ["d", "has_held_process", "b"],
        ],
        And(*round_active(), Lt(V("a"), V("b")), not_none(fp),
            Eq(fp, A("d", "identity_fingerprint"))),
        law_effects("commute", StringConcat(A("a", "name"), L(" and "), A("b", "name"), L(" commute")),
                    {}, ["a", "b"]),
    )


def conjugation_inverts_law_rule():
    conj_fp = PFingerprint(PConjugate(A("a", "params"), A("b", "params")), A("d", "probes"))
    inv_fp = PFingerprint(PInverse(A("a", "params")), A("d", "probes"))
    return rule(
        "ir_law_conjugation_inverts", OFFLINE_AREA, 61,
        "Law: b·a·b⁻¹ = a⁻¹ (b reverses a), when a is not its own inverse.",
        [
            ["agent", "has_invention_policy", "pol"],
            ["agent", "has_invention_round", "r"],
            ["r", "about_domain", "d"],
            ["d", "has_held_process", "a"],
            ["d", "has_held_process", "b"],
        ],
        And(*round_active(), Not(Eq(V("a"), V("b"))), not_none(conj_fp),
            Eq(conj_fp, inv_fp), Not(Eq(inv_fp, A("a", "fingerprint")))),
        law_effects("conjugation_inverts",
                    StringConcat(A("b", "name"), L("·"), A("a", "name"), L("·"), A("b", "name"),
                                 L("⁻¹ = "), A("a", "name"), L("⁻¹")),
                    {}, ["a", "b"]),
    )


# ------------------------------------------------------- round lifecycle ---

def _record_rate(op_name_term):
    recs = Filter(N("agent", "has_strategy_record"), "sr",
                  And(Eq(A("sr", "kind"), A("d", "kind")), Eq(A("sr", "operator"), op_name_term)))
    rate = Sum(recs, "sr2", Div(A("sr2", "yields"), Max(L(1.0), A("sr2", "trials"))))
    return IfThenElse(Gt(Count(recs), ZERO), rate, A("pol", "strategy_prior"))


def enabled_ops_term():
    ops = Filter(N("agent", "has_invention_operator"), "o", Eq(A("o", "enabled"), L(1.0)))
    all_names = MapList(ops, "o", A("o", "name"))
    weighted = SoftWeights(ops, "o", _record_rate(A("o", "name")), A("pol", "strategy_temperature"))
    kept = FilterList(weighted, "w", Gte(Nth(V("w"), 1), A("pol", "strategy_min_weight")))
    guided = MapList(kept, "w", {"type": "Attr", "node": Nth(V("w"), 0), "key": "name"})
    has_records = Gt(Count(Filter(N("agent", "has_strategy_record"), "sr",
                                  Eq(A("sr", "kind"), A("d", "kind")))), ZERO)
    return IfThenElse(And(Eq(A("pol", "strategy_enabled"), L(1.0)), has_records), guided, all_names)


def no_round_for_domain():
    return Not(Exists(N("agent", "has_invention_round"), "rr", Eq(A("rr", "domain"), A("d", "name"))))


def round_attrs(trigger, status):
    n_held = Count(N("d", "has_held_process"))
    return {
        "status": status,
        "trigger": trigger,
        "domain": T(A("d", "name")),
        "domain_kind": T(A("d", "kind")),
        "n_held": T(n_held),
        "enabled_ops": T(enabled_ops_term()),
    }


def open_round_rules():
    out = []
    for trigger in ("impasse", "offline"):
        if trigger == "impasse":
            match = [["agent", "has_invention_policy", "pol"], ["agent", "has_solve_task", "t"],
                     ["t", "about_domain", "d"]]
            cond = [Eq(A("t", "status"), L("stuck"))]
            link = [["add_edge", "t", "triggered_invention_round", "r", {}]]
        else:
            match = [["agent", "has_invention_policy", "pol"], ["agent", "has_memory_cycle", "cycle"],
                     ["agent", "has_process_domain", "d"]]
            cond = [Eq(A("pol", "offline_enabled"), L(1.0)), Eq(A("cycle", "mode"), L("offline")),
                    Gt(Count(N("d", "has_held_process")), ZERO)]
            link = [["add_edge", "cycle", "has_invention_round", "r", {}]]
        base = [policy_on()] + cond + [no_round_for_domain()]
        # Budgeted: through the generic ThinkingBudget pending-request contract.
        out.append(rule(
            f"ir_open_round_on_{trigger}_budgeted", OFFLINE_AREA, 20,
            f"Open an InventionRound for the domain ({trigger}); request its cost from ThinkingBudget "
            "through the generic pending-request contract.",
            match + [["agent", "has_thinking_budget", "budget"]],
            And(*base),
            [
                ["add_node", "req", "ThinkingBudgetRequest", {
                    "status": "pending", "cost": T(A("pol", "round_cost")),
                    "requester_kind": "invention_round"}],
                ["add_node", "r", "InventionRound", round_attrs(trigger, "awaiting_budget")],
                ["add_edge", "agent", "has_invention_round", "r", {}],
                ["add_edge", "r", "about_domain", "d", {}],
                ["add_edge", "r", "funded_by", "req", {}],
                ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
            ] + link,
            batch=False,
        ))
        out.append(rule(
            f"ir_open_round_on_{trigger}_unbudgeted", OFFLINE_AREA, 20,
            f"Open an InventionRound for the domain ({trigger}) directly when the agent holds no "
            "ThinkingBudget at all.",
            match,
            And(*base, Eq(Count(N("agent", "has_thinking_budget")), ZERO)),
            [
                ["add_node", "r", "InventionRound", round_attrs(trigger, "active")],
                ["add_edge", "agent", "has_invention_round", "r", {}],
                ["add_edge", "r", "about_domain", "d", {}],
            ] + link,
            batch=False,
        ))
    return out


def funding_rules():
    return [
        rule("ir_round_funded", OFFLINE_AREA, 21,
             "A round whose budget request was approved becomes active.",
             [["agent", "has_invention_round", "r"], ["r", "funded_by", "req"]],
             And(Eq(A("r", "status"), L("awaiting_budget")), Eq(A("req", "status"), L("approved"))),
             [["set_attr", "r", "status", "active"]]),
        rule("ir_round_denied", OFFLINE_AREA, 21,
             "A round whose budget request was denied is closed as denied.",
             [["agent", "has_invention_round", "r"], ["r", "funded_by", "req"]],
             And(Eq(A("r", "status"), L("awaiting_budget")), Eq(A("req", "status"), L("denied"))),
             [["set_attr", "r", "status", "denied"]]),
    ]


def strategy_rules():
    yields = Count(Filter(NodesWhere("ProcessSchema", "operator", A("rec", "operator")), "x",
                          Eq(A("x", "domain_kind"), A("rec", "kind"))))
    binary_ops = L(sorted(BINARY))
    trials = Sum(
        Filter(N("agent", "has_invention_round"), "rr",
               And(Eq(A("rr", "domain_kind"), A("rec", "kind")),
                   In(A("rec", "operator"), A("rr", "enabled_ops")),
                   Not(Eq(A("rr", "status"), L("awaiting_budget"))),
                   Not(Eq(A("rr", "status"), L("denied"))))),
        "rr2",
        IfThenElse(In(A("rec", "operator"), binary_ops),
                   Times(A("rr2", "n_held"), Max(ZERO, Plus(A("rr2", "n_held"), L(-1)))),
                   A("rr2", "n_held")),
    )
    return [
        rule("ir_strategy_record_mint", OFFLINE_AREA, 70,
             "I3.3: keep one StrategyRecord per (domain kind, operator) the agent has tried.",
             [["agent", "has_invention_policy", "pol"], ["agent", "has_invention_round", "r"],
              ["agent", "has_invention_operator", "op"]],
             And(policy_on(), Eq(A("r", "status"), L("active")), In(A("op", "name"), A("r", "enabled_ops"))),
             [["add_node_if_absent", "rec", "StrategyRecord", {
                 "kind": T(A("r", "domain_kind")), "operator": T(A("op", "name"))}],
              ["add_edge", "agent", "has_strategy_record", "rec", {}]]),
        rule("ir_strategy_record_update", OFFLINE_AREA, 71,
             "I3.3: yields = inventions minted by the operator in domains of this kind; trials = "
             "candidate applications offered by rounds that enabled it.",
             [["agent", "has_invention_policy", "pol"], ["agent", "has_strategy_record", "rec"]],
             And(policy_on(), Or(Not(Eq(A("rec", "yields"), yields)), Not(Eq(A("rec", "trials"), trials)))),
             [["set_attr", "rec", "yields", T(yields)], ["set_attr", "rec", "trials", T(trials)]],
             batch=True),
    ]


def build():
    rules = open_round_rules() + funding_rules()
    order = 0
    for op in ["commutator", "conjugate", "compose"]:
        rules.append(binary_operator_rule(op, order))
        order += 1
    for op in ["inverse", "power2", "power3"]:
        rules.append(unary_operator_rule(op, order))
        order += 1
    rules.append(root_relation_rule())
    rules.append(closure_rule())
    rules += [order_law_rule(k) for k in range(2, 7)]
    rules += [commute_law_rule(), conjugation_inverts_law_rule()]
    rules += strategy_rules()
    specs = [
        ("Agent", "has_invention_policy", "InventionPolicy"),
        ("Agent", "has_invention_round", "InventionRound"),
        ("InventionRound", "about_domain", "ProcessDomain"),
        ("InventionRound", "funded_by", "ThinkingBudgetRequest"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("SolveTask", "triggered_invention_round", "InventionRound"),
        ("MemoryCycle", "has_invention_round", "InventionRound"),
        ("ProcessSchema", "has_arg0", "ProcessSchema"),
        ("ProcessSchema", "has_arg1", "ProcessSchema"),
        ("ProcessSchema", "root_of", "ProcessSchema"),
        ("Agent", "has_process_law", "ProcessLaw"),
        ("ProcessLaw", "about_process", "ProcessSchema"),
        ("Agent", "has_strategy_record", "StrategyRecord"),
        ("Agent", "has_tolerance", "Tolerance"),
        ("Tolerance", "governs_policy", "InventionPolicy"),
    ]
    return {
        "id": SEED_ID,
        "version": "1.0.0",
        "depends_on": ["process_schema", "invention_operators"],
        "self_load_only": True,
        "area": OFFLINE_AREA,
        "description": (
            "Track I I2: budgeted invention rounds over a domain's held processes "
            "(commutator, conjugate, compose, inverse, powers, roots), novelty and precision "
            "by effect, conjugation closure, discovered laws, and a yield-guided strategy library."
        ),
        "microtheory": {
            "name": SEED_ID,
            "description": "Invent by algebra over held processes; keep what is new by effect and precise.",
        },
        "nodes": [
            {"local_id": 0, "type": "InventionPolicy", "attrs": {
                "name": "core_invention_policy", "enabled": 0.0, "offline_enabled": 1.0,
                "round_cost": 4.0, "max_support": 3.0, "max_invented": 6000.0,
                "closure_enabled": 1.0, "strategy_enabled": 1.0, "strategy_temperature": 0.05,
                "strategy_min_weight": 0.02, "strategy_prior": 0.5}},
            {"local_id": 1, "type": "Tolerance", "attrs": {
                "name": "invention_max_support", "governs_attr": "max_support", "default": 3.0,
                "min": 1.0, "max": 8.0, "step": 1.0, "direction": "widen_up"}},
            {"local_id": 2, "type": "Tolerance", "attrs": {
                "name": "invention_strategy_min_weight", "governs_attr": "strategy_min_weight",
                "default": 0.02, "min": 0.0, "max": 0.5, "step": 0.01, "direction": "widen_down"}},
        ],
        "edges": [
            {"src": {"role": "agent_root"}, "type": "has_invention_policy", "tgt": {"local": 0}, "attrs": {}},
            {"src": {"role": "agent_root"}, "type": "has_tolerance", "tgt": {"local": 1}, "attrs": {}},
            {"src": {"local": 1}, "type": "governs_policy", "tgt": {"local": 0}, "attrs": {}},
            {"src": {"role": "agent_root"}, "type": "has_tolerance", "tgt": {"local": 2}, "attrs": {}},
            {"src": {"local": 2}, "type": "governs_policy", "tgt": {"local": 0}, "attrs": {}},
        ],
        "productions": productions(SEED_ID, specs),
        "rules": rules,
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
