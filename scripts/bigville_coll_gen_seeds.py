#!/usr/bin/env python3
"""bigville R16 (block 264000) SEED BUILDER -- emits the COLLECTION + EVICTION
(moral-injury) rule seeds that DE-MAGICALIZE R7.

A TOOL (a seed BUILDER that emits graph data, explicitly allowed by
experiments/gamma-substrate/CLAUDE.md -- the same class as
`bigville_fin_gen_seeds.py`). It writes two self-contained seed manifests the Rust
runtime loads. NO agent decision lives here -- every R16 DECISION (collect vs miss,
deliver honestly vs pocket, pay the wage, perform the eviction, feel the injury or
not, pick the cheapest hands) is a RULE in the emitted JSON; this file only
assembles Term-trees over the PRE-EXISTING DSL (Attr/Var/Lit/Plus/Minus/Times/IDiv/
Eq/Gt/Gte/Lt/And/Not/Argmax/Neighbours). ZERO new Rust.

R7 is left LOADED BUT DORMANT: R16 never arms R7's rent/mortgage pay rules and
never lets R7's `missed` reach `term`, so R7's magical auto-debit / auto-seizure
never fire. Payment is routed through a COLLECTOR who must REACH the payer (R1
proximity); seizure through an ENFORCER who must REACH the home and FEELS it
(w_supergraph). R7's `bf_homeless_affect` is REUSED verbatim to book the evicted
family's distress -- R16 only adds the perpetrator-side mirror.

  seeds/bigville_coll_collect.json -- collection is an ACT:
        bc_collect_self / bc_collect_hired / bc_collect_miss / bc_deliver /
        bc_pay_wage.
  seeds/bigville_coll_evict.json   -- eviction is enforcement WITH a doer who feels:
        bc_evict / bc_moral_injury / bc_no_injury / bc_pick_cheapest_hands.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEEDS = os.path.join(ROOT, "seeds")

BP = 10000
HALF_BP = 5000


# ---- Term-tree helpers (compose EXISTING DSL Terms; no new Rust) -------------
def var(n):
    return {"type": "Var", "name": n}


def lit(v):
    return {"type": "Lit", "value": float(v)}


def ilit(v):
    return {"type": "Lit", "value": int(v)}


def attr(node, key):
    """Read attr as a number, default 0 (the `Plus[Attr, 0]` idiom the R4/R6/R7
    seeds use so a missing key never aborts a match)."""
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": var(node), "key": key}, lit(0)]}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def times(*items):
    return {"type": "Times", "items": list(items)}


def idiv(a, b):
    return {"type": "IDiv", "a": a, "b": b}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def a_and(*items):
    return {"type": "And", "items": list(items)}


def term(t):
    return {"__term__": t}


# ============================================================ COLLECTION IS AN ACT
def build_collect():
    rules = []

    # rental scaffolding shared by the collect rules:
    #   collector -collects_for-> rental ; rental -landlord-> ll ; tenant -rents->
    #   rental ; both is_at the SAME cell (R1 proximity).
    def prox_match(collector):
        return [
            [collector, "collects_for", "rental"],
            ["rental", "landlord", "ll"],
            ["tenant", "rents", "rental"],
            [collector, "is_at", "cell"],
            ["tenant", "is_at", "cell"],
        ]

    # --- bc_collect_self: the owner collects his OWN rent (small owner, free) ---
    # ll binds BOTH collector (collects_for source) and landlord (landlord target);
    # distinct edge types on distinct roles -> no same-type-edge gotcha.
    rules.append({
        "name": "bc_collect_self",
        "match": prox_match("ll"),
        "where": a_and(
            eq(attr("ll", "collect_armed"), lit(1.0)),
            eq(attr("rental", "r16_evicted"), lit(0.0)),
            eq(attr("rental", "hired"), lit(0.0)),
            gte(attr("tenant", "coin"), attr("rental", "rent")),
        ),
        "effects": [
            ["set_attr", "tenant", "coin",
             term(minus(attr("tenant", "coin"), attr("rental", "rent")))],
            ["set_attr", "ll", "coin",
             term(plus(attr("ll", "coin"), attr("rental", "rent")))],
            ["set_attr", "rental", "arr", 0.0],
            ["set_attr", "ll", "collect_armed", 0.0],
        ],
    })

    # --- bc_collect_hired: a HIRED agent collects into his OWN hands ------------
    # (hired=1, collector != owner). The rent enters the collector's `collected`
    # bucket, NOT yet the owner's coin -- delivery (and its honesty) is bc_deliver.
    rules.append({
        "name": "bc_collect_hired",
        "match": prox_match("collector"),
        "where": a_and(
            eq(attr("collector", "collect_armed"), lit(1.0)),
            eq(attr("rental", "r16_evicted"), lit(0.0)),
            eq(attr("rental", "hired"), lit(1.0)),
            gte(attr("tenant", "coin"), attr("rental", "rent")),
        ),
        "effects": [
            ["set_attr", "tenant", "coin",
             term(minus(attr("tenant", "coin"), attr("rental", "rent")))],
            ["set_attr", "collector", "collected",
             term(plus(attr("collector", "collected"), attr("rental", "rent")))],
            ["set_attr", "collector", "stated_collected",
             term(plus(attr("collector", "stated_collected"), attr("rental", "rent")))],
            ["set_attr", "rental", "arr", 0.0],
            ["set_attr", "collector", "collect_armed", 0.0],
        ],
    })

    # --- bc_collect_miss: collector REACHES an insolvent tenant (DISJOINT) ------
    # coin < rent -> arrears += 1, no transfer. (Covers self AND hired.) If the
    # collector is NOT proximate, NEITHER collect rule matches at all -> the
    # `failed to find the payer` case: no transfer, and NOT a tenant default.
    rules.append({
        "name": "bc_collect_miss",
        "match": [
            ["collector", "collects_for", "rental"],
            ["tenant", "rents", "rental"],
            ["collector", "is_at", "cell"],
            ["tenant", "is_at", "cell"],
        ],
        "where": a_and(
            eq(attr("collector", "collect_armed"), lit(1.0)),
            eq(attr("rental", "r16_evicted"), lit(0.0)),
            lt(attr("tenant", "coin"), attr("rental", "rent")),
        ),
        "effects": [
            ["set_attr", "rental", "arr",
             term(plus(attr("rental", "arr"), lit(1.0)))],
            ["set_attr", "collector", "collect_armed", 0.0],
        ],
    })

    # --- bc_deliver: the hired collector delivers to the owner; HONESTY BITES ---
    # delivered = IDiv(collected*deliver_bp + 5000, 10000) (round-half-up on
    # integers, the R7 interest idiom over the pre-existing IDiv Term). The skim
    # `collected - delivered` goes to the collector's OWN coin (pocketed). An
    # honest collector (deliver_bp=10000) delivers ALL: held_delivered ==
    # stated_collected; a saboteur (deliver_bp<10000) leaves held < stated -- the
    # 234 stated!=held atom, on collection.
    delivered = idiv(plus(times(attr("collector", "collected"),
                                attr("collector", "deliver_bp")), ilit(HALF_BP)),
                     ilit(BP))
    rules.append({
        "name": "bc_deliver",
        "match": [
            ["collector", "collects_for", "rental"],
            ["rental", "landlord", "ll"],
        ],
        "where": a_and(
            eq(attr("collector", "deliver_armed"), lit(1.0)),
            eq(attr("rental", "hired"), lit(1.0)),
            gt(attr("collector", "collected"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "ll", "coin", term(plus(attr("ll", "coin"), delivered))],
            ["set_attr", "collector", "held_delivered",
             term(plus(attr("collector", "held_delivered"), delivered))],
            ["set_attr", "collector", "coin",
             term(plus(attr("collector", "coin"),
                       minus(attr("collector", "collected"), delivered)))],
            ["set_attr", "collector", "collected", 0.0],
            ["set_attr", "collector", "deliver_armed", 0.0],
        ],
    })

    # --- bc_pay_wage: the owner PAYS the hired collector a wage -----------------
    # owner NETS delivered - wage; the collector's take is wage + skim. Scale
    # economics: self-collect (hired=0) pays no wage; a large owner pays a cut.
    rules.append({
        "name": "bc_pay_wage",
        "match": [
            ["collector", "collects_for", "rental"],
            ["rental", "landlord", "ll"],
        ],
        "where": a_and(
            eq(attr("collector", "wage_armed"), lit(1.0)),
            eq(attr("rental", "hired"), lit(1.0)),
            gt(attr("rental", "wage"), lit(0.0)),
            gte(attr("ll", "coin"), attr("rental", "wage")),
        ),
        "effects": [
            ["set_attr", "ll", "coin",
             term(minus(attr("ll", "coin"), attr("rental", "wage")))],
            ["set_attr", "collector", "coin",
             term(plus(attr("collector", "coin"), attr("rental", "wage")))],
            ["set_attr", "collector", "wage_armed", 0.0],
        ],
    })

    return {
        "id": "bigville_coll_collect",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R16 (block 264000) -- COLLECTION IS AN ACT (de-magicalizes R7's "
            "auto-debit). Rent transfers ONLY when a collector REACHES the payer (R1 "
            "proximity: collector and tenant is_at the SAME MoveCell) and acts. "
            "bc_collect_self: a small owner collects his own rent free (tenant.coin-=rent, "
            "ll.coin+=rent). bc_collect_hired: a paid agent collects into his OWN hands "
            "(collected/stated_collected buckets), delivery is separate. bc_collect_miss: "
            "collector reaches an insolvent tenant -> arrears++ (DISJOINT on coin<rent; "
            "covers both). bc_deliver: the hired collector delivers delivered=IDiv("
            "collected*deliver_bp+5000,10000) to the owner and POCKETS the skim into his "
            "own coin -- an honest deliver_bp=10000 gives held_delivered==stated_collected, "
            "a saboteur leaves held<stated (the 234 stated!=held atom, on collection). "
            "bc_pay_wage: the owner pays the hired collector a wage (R4/R6), so the owner "
            "NETS rent-wage and the collector's take is wage+skim. If the collector is not "
            "proximate NO rule fires -> no transfer at all (failed to find the payer). "
            "Every decision a RULE; composes existing Terms; zero new Rust."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


# ============================================ EVICTION IS ENFORCEMENT WITH A DOER
def build_evict():
    rules = []

    # --- bc_evict: the enforcement ACT (a doer reaches the home + executes) -----
    # NOT a state-flip: requires doer -enforces_for-> rental, the doer is_at the
    # home's cell (house -at_home_cell-> cell), arrears past term. No doer / no
    # reach / nobody willing -> eviction does NOT happen even at arr>=term.
    # Sets tenant.homeless=1 -> R7 bf_homeless_affect books the family's distress.
    rules.append({
        "name": "bc_evict",
        "match": [
            ["doer", "enforces_for", "rental"],
            ["tenant", "rents", "rental"],
            ["rental", "rented_house", "house"],
            ["house", "at_home_cell", "cell"],
            ["doer", "is_at", "cell"],
        ],
        "where": a_and(
            eq(attr("doer", "evict_armed"), lit(1.0)),
            eq(attr("rental", "r16_evicted"), lit(0.0)),
            gte(attr("rental", "arr"), attr("rental", "term")),
        ),
        "effects": [
            ["set_attr", "rental", "r16_evicted", 1.0],
            ["set_attr", "tenant", "homeless", 1.0],
            ["set_attr", "doer", "did_evict",
             term(plus(attr("doer", "did_evict"), lit(1.0)))],
            ["set_attr", "doer", "evict_armed", 0.0],
        ],
    })

    # --- bc_moral_injury (HEADLINE): the perpetrator-side MIRROR of victim distress
    # a doer WITH empathy (w_supergraph>0) takes an affective HIT (arousal up,
    # valence down -- guilt/moral injury) performing the eviction. Booked once per
    # eviction (rental.injury_booked guard). The mirror of R7's bf_homeless_affect.
    rules.append({
        "name": "bc_moral_injury",
        "match": [
            ["doer", "enforces_for", "rental"],
            ["doer", "has_affective_state", "aff"],
        ],
        "where": a_and(
            eq(attr("rental", "r16_evicted"), lit(1.0)),
            eq(attr("rental", "injury_booked"), lit(0.0)),
            gt(attr("doer", "w_supergraph"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "aff", "arousal",
             term(plus(attr("aff", "arousal"), attr("doer", "injury_mag")))],
            ["set_attr", "aff", "valence",
             term(minus(attr("aff", "valence"), attr("doer", "injury_drop")))],
            ["set_attr", "doer", "moral_injury", 1.0],
            ["set_attr", "doer", "injury_total",
             term(plus(attr("doer", "injury_total"), attr("doer", "injury_mag")))],
            ["set_attr", "rental", "injury_booked", 1.0],
        ],
    })

    # --- bc_no_injury: the PSYCHOPATH path (w_supergraph=0, e.g. John) ----------
    # closes the bookkeeping with ZERO affect change. Ablate empathy (w->0) -> the
    # injury vanishes; a psychopath evicts as cheaply as any other chore.
    rules.append({
        "name": "bc_no_injury",
        "match": [["doer", "enforces_for", "rental"]],
        "where": a_and(
            eq(attr("rental", "r16_evicted"), lit(1.0)),
            eq(attr("rental", "injury_booked"), lit(0.0)),
            eq(attr("doer", "w_supergraph"), lit(0.0)),
        ),
        "effects": [
            ["set_attr", "rental", "injury_booked", 1.0],
            ["set_attr", "doer", "zero_injury_evictions",
             term(plus(attr("doer", "zero_injury_evictions"), lit(1.0)))],
        ],
    })

    # --- bc_pick_cheapest_hands: the emergent OFFLOAD read-off (measure-first) --
    # For a rental with candidate doers (rental -candidate-> doer), the graph's
    # Argmax over candidates by -(ask_wage + w_supergraph*injury_mag) -- the REAL
    # cost of the act (what you PAY plus what the hands FEEL) -- writes the winner's
    # w_supergraph onto the rental as picked_w. No edge is wired to a computed node
    # (AddEdge binds match-vars only); this is the gb_choose_give scalar-Argmax
    # pattern. The banality of eviction (low-empathy hands win) FALLS OUT of the
    # cost minimization -- it is not scripted.
    cost_neg = minus(lit(0.0),
                     plus(attr("c", "ask_wage"),
                          times(attr("c", "w_supergraph"), attr("c", "injury_mag"))))
    winner = {"type": "Argmax",
              "source": {"type": "Neighbours", "node": var("rental"),
                         "edge_type": "candidate", "any_type": False},
              "var_name": "c", "value": cost_neg}
    rules.append({
        "name": "bc_pick_cheapest_hands",
        "match": [["rental", "landlord", "ll"]],
        "where": eq(attr("rental", "pick_armed"), lit(1.0)),
        "effects": [
            ["set_attr", "rental", "picked_w",
             term({"type": "Attr", "node": winner, "key": "w_supergraph"})],
            ["set_attr", "rental", "picked_ask_wage",
             term({"type": "Attr", "node": winner, "key": "ask_wage"})],
            ["set_attr", "rental", "pick_armed", 0.0],
        ],
    })

    return {
        "id": "bigville_coll_evict",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE R16 (block 264000) -- EVICTION IS ENFORCEMENT WITH A DOER WHO FEELS "
            "IT (de-magicalizes R7's auto-seizure). bc_evict is the ACT: a doer "
            "-enforces_for-> rental must REACH the home (house -at_home_cell-> cell, R1) "
            "with arrears past term -> r16_evicted=1, tenant.homeless=1 (reusing R7 "
            "bf_homeless_affect for the family's distress), did_evict++. No doer / no reach "
            "-> the eviction does NOT happen at the same arrears. bc_moral_injury (HEADLINE) "
            "is the perpetrator-side MIRROR: a doer with empathy (w_supergraph>0) takes an "
            "affective HIT (arousal up/valence down = guilt) performing it; bc_no_injury is "
            "the psychopath path (w=0, John) closing the books with ZERO injury -- ablate "
            "empathy and the injury vanishes. bc_pick_cheapest_hands is the emergent offload "
            "read-off: the graph's Argmax over candidate doers by -(ask_wage + "
            "w_supergraph*injury_mag) writes the cost-minimizing doer's empathy to picked_w "
            "(the gb_choose_give scalar pattern -- no computed-node edge) so the banality of "
            "eviction can be MEASURED, not scripted. Every decision a RULE; composes "
            "existing Terms (incl Argmax/Neighbours); zero new Rust."),
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


def main():
    os.makedirs(SEEDS, exist_ok=True)
    for seed in (build_collect(), build_evict()):
        path = os.path.join(SEEDS, seed["id"] + ".json")
        with open(path, "w") as f:
            json.dump(seed, f, indent=1)
        print("wrote", path, "--", len(seed["rules"]), "rules")


if __name__ == "__main__":
    main()
