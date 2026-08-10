#!/usr/bin/env python3
"""AUTHORING SCRIPT for the bigville R15 (block 263000) VIOLENCE seeds. Emits
`seeds/bigville_viol_act.json` + `seeds/bigville_viol_evidence.json` +
`seeds/bigville_viol_prosecute.json` + `seeds/bigville_viol_kill.json` -- deeply
nested Term-tree JSON is error-prone by hand, so this one-off builder emits it
(the `tools/*` / `scripts/*_gen_seeds` authoring pattern; NOT agent runtime,
deletable). It writes ONLY graph data (Rules composing PRE-EXISTING DSL Terms);
it makes NO decision and adds NO Rust.

VIOLENCE -- a simple SCALAR, reusing everything (spec §2.9 + §3 R15):
  * THE ACT (bigville_viol_act): `bv_trigger` is the value-DECISION to attack
    (trigger_value = snap_pressure + w_spite*spite_gain + hunger*desperation_gain
    vs trigger_threshold, gated on STAMINA energy>=cost) -- the outward form of the
    242 snap / spite / desperation, NOT random; `bv_refrain` is the disjoint
    decline arm. A committed ViolentAct costs BOTH: `bv_harm_victim`
    (victim.health -= amount, last_cause=5 violence -> R14 bl_death at zero) +
    `bv_cost_aggressor` (aggressor.energy -= cost, R1).
  * THE 247 PIPELINE (bigville_viol_evidence): WITNESS (bv_witness_evidence,
    line-of-sight) OR REPORT (bv_report_evidence, a testimony Message) opens the
    Case (known=1) + logs Evidence; bv_physical logs the victim's health-drop as
    PHYSICAL evidence (the corroboration a false report lacks); bv_form_belief is
    the ABDUCTION (observed = Sum of evidence weights; verdict = Argmax over the
    constable's held CaseGenerator codebook by fit -|predicts-observed| -- a
    RECONSTRUCTION, not a fact); bv_sufficient_proof requires guilty AND
    confidence >= proof_threshold (the decision_value).
  * THE CORRUPTIBLE STATE (bigville_viol_prosecute): bv_prosecute files with the
    council; bv_council_convict / bv_council_acquit adjudicate over the
    backing-graph (Sum of vote over SEATED CouncilMembers > 0); bv_warn / bv_punish
    sanction by AMOUNT magnitude (warn if amount<=warn_threshold else punish).
  * THE FIFTH ROUTE (bigville_viol_kill): R14 bl_death is reused UNCHANGED;
    bv_death_tag only records death_by_violence=1 on death_cause==5 (a read-back).

Relational-ethics (harm-analog): induce -> measure -> RESTORE. NO reward/punish/
penalty token in any rule logic (a Sanction is a record/censure, never a badness
score on a person; the victim's silence is genuine insufficient proof, never
fault). ZERO new Rust.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED_DIR = os.path.join(ROOT, "seeds")

# ---- deterministic scalar parameters (glass-box; NO RNG) ----
WITNESS_W = 6.0        # a line-of-sight witness observation
TESTIMONY_W = 3.0      # a filed report (victim/bystander testimony)
PHYSICAL_W = 3.0       # the victim's real health-drop, as corroboration
GUILTY_PREDICTS = 8.0  # the guilty generator predicts strong evidence
INNOCENT_PREDICTS = 0.0
PROOF_THRESHOLD = 5.0  # the decision_value: sufficient-proof confidence


# ---------------------------------------------------------------- term helpers
def V(name):
    return {"type": "Var", "name": name}


def L(v):
    return {"type": "Lit", "value": (float(v) if isinstance(v, (int, float)) else v)}


def A(node, key):
    """Attr read coerced through Plus[Attr, 0.0] so a MISSING numeric key reads as
    0.0 (the R7/R13/R14 defensive pattern) -- never a match failure on an absent
    attr."""
    return {"type": "Plus", "items": [
        {"type": "Attr", "node": V(node), "key": key}, L(0.0)]}


def AttrRaw(node, key):
    return {"type": "Attr", "node": V(node), "key": key}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Lte(a, b):
    return {"type": "Lte", "a": a, "b": b}


def And(items):
    return {"type": "And", "items": items}


def Or(items):
    return {"type": "Or", "items": items}


def Not(arg):
    return {"type": "Not", "arg": arg}


def Plus(items):
    return {"type": "Plus", "items": items}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Times(items):
    return {"type": "Times", "items": items}


def Min(items):
    return {"type": "Min", "items": items}


def Max(items):
    return {"type": "Max", "items": items}


def Abs(arg):
    return {"type": "Abs", "arg": arg}


def IfThenElse(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def Neighbours(node, edge_type):
    return {"type": "Neighbours", "node": V(node), "edge_type": edge_type,
            "any_type": False}


def NodesOfType(t):
    return {"type": "NodesOfType", "node_type": t}


def Sum(source, var_name, value):
    return {"type": "Sum", "source": source, "var_name": var_name, "value": value}


def Argmax(source, var_name, value):
    return {"type": "Argmax", "source": source, "var_name": var_name, "value": value}


def T(term):
    return {"__term__": term}


def rule(name, match, where, effects, *, batch=False):
    return {"name": name, "batch": bool(batch),
            "match": match, "where": where, "effects": effects}


def seed(sid, description, rules):
    return {
        "id": sid, "version": "1.0.0", "depends_on": [], "self_load_only": True,
        "description": description,
        "nodes": [], "edges": [], "productions": [], "concepts": [],
        "rules": rules,
    }


# =============================================================== THE ACT seed
def act_rules():
    # trigger_value: the outward-facing form of the 242 frustration-SNAP, of spite
    # (w_spite), or of DESPERATION (hunger) -- a value-decision, not chance.
    trigger_value = Plus([
        A("m", "snap_pressure"),
        Times([A("m", "w_spite"), A("m", "spite_gain")]),
        Times([A("m", "hunger"), A("m", "desperation_gain")]),
    ])
    can_pay = Gte(A("m", "energy"), A("m", "attack_cost"))

    # bv_trigger: the DECISION to commit a violent act. Fires iff considered AND
    # trigger_value crosses threshold AND the aggressor has the stamina to pay.
    # Mints a ViolentAct{amount,cost} + the harms/by edges. Violence is REACHABLE
    # only through this value-decision (ablate the trigger -> bv_refrain).
    bv_trigger = rule(
        "bv_trigger",
        [["m", "considers_violence", "target"]],
        And([
            Eq(A("m", "consider_armed"), L(1.0)),
            Eq(A("m", "attacked"), L(0.0)),
            Gt(trigger_value, A("m", "trigger_threshold")),
            can_pay,
        ]),
        [
            ["add_node", "act", "ViolentAct", {
                "amount": T(A("m", "attack_amount")),
                "cost": T(A("m", "attack_cost")),
                "applied_victim": 0.0, "applied_cost": 0.0}],
            ["add_edge", "act", "harms", "target"],
            ["add_edge", "act", "by", "m"],
            ["set_attr", "m", "attacked", 1.0],
            ["set_attr", "m", "consider_armed", 0.0],
        ],
    )

    # bv_refrain: the DISJOINT decline arm. Fires iff considered AND (the value is
    # below threshold OR there is no stamina) -- a calm / fed / un-spiteful agent
    # refrains, and NO act is minted (the trigger's failable control).
    bv_refrain = rule(
        "bv_refrain",
        [["m", "considers_violence", "target"]],
        And([
            Eq(A("m", "consider_armed"), L(1.0)),
            Eq(A("m", "attacked"), L(0.0)),
            Or([Lte(trigger_value, A("m", "trigger_threshold")), Not(can_pay)]),
        ]),
        [
            ["set_attr", "m", "refrained", 1.0],
            ["set_attr", "m", "consider_armed", 0.0],
        ],
    )

    # bv_harm_victim: G-violence-costs-both (victim arm). The act drops the victim's
    # HEALTH by amount (the R14 acute arm shape, health := max(0, health-amount)),
    # tagging last_cause=5 (violence) so R14 bl_death routes death_cause=5 at zero.
    bv_harm_victim = rule(
        "bv_harm_victim",
        [["act", "harms", "v"], ["v", "has_life", "life"]],
        Eq(A("act", "applied_victim"), L(0.0)),
        [
            ["set_attr", "life", "health",
             T(Max([L(0.0), Minus(A("life", "health"), A("act", "amount"))]))],
            ["set_attr", "life", "last_cause", 5.0],
            ["set_attr", "act", "applied_victim", 1.0],
        ],
    )

    # bv_cost_aggressor: G-violence-costs-both (aggressor arm). The act costs the
    # aggressor STAMINA (R1 energy := max(0, energy-cost)) -- violence is tiring, so
    # it can't be endless.
    bv_cost_aggressor = rule(
        "bv_cost_aggressor",
        [["act", "by", "agg"]],
        Eq(A("act", "applied_cost"), L(0.0)),
        [
            ["set_attr", "agg", "energy",
             T(Max([L(0.0), Minus(A("agg", "energy"), A("act", "cost"))]))],
            ["set_attr", "act", "applied_cost", 1.0],
        ],
    )
    return [bv_trigger, bv_refrain, bv_harm_victim, bv_cost_aggressor]


# =========================================================== THE EVIDENCE seed
def evidence_rules():
    # bv_witness_evidence: the constable had LINE-OF-SIGHT (witnessed=1, a world
    # fact) -> the Case becomes known + a witness Evidence is logged (once).
    bv_witness_evidence = rule(
        "bv_witness_evidence",
        [["con", "investigates", "case"]],
        And([
            Eq(A("case", "witnessed"), L(1.0)),
            Eq(A("case", "witness_logged"), L(0.0)),
        ]),
        [
            ["add_node", "ev", "Evidence", {"kind": 1.0, "weight": WITNESS_W}],
            ["add_edge", "case", "has_evidence", "ev"],
            ["set_attr", "case", "witness_logged", 1.0],
            ["set_attr", "case", "known", 1.0],
        ],
    )

    # bv_report_evidence: the constable was TOLD -- a testimony Message (report)
    # from the victim or a bystander opens the case + logs a testimony Evidence.
    # This is the REPORT CHANNEL: ablate it on an unwitnessed act and the case is
    # never known (regression to a witnessed-only floor).
    bv_report_evidence = rule(
        "bv_report_evidence",
        [["case", "reported_by", "rep"]],
        Eq(A("case", "report_logged"), L(0.0)),
        [
            ["add_node", "ev", "Evidence", {"kind": 2.0, "weight": TESTIMONY_W}],
            ["add_edge", "case", "has_evidence", "ev"],
            ["set_attr", "case", "report_logged", 1.0],
            ["set_attr", "case", "known", 1.0],
        ],
    )

    # bv_physical: a KNOWN case whose victim's health ACTUALLY dropped -> the
    # health-drop is logged as PHYSICAL evidence (the corroboration a FALSE report
    # -- where the victim is unharmed -- lacks).
    bv_physical = rule(
        "bv_physical",
        [["con", "investigates", "case"], ["case", "against_victim", "v"],
         ["v", "has_life", "life"]],
        And([
            Eq(A("case", "known"), L(1.0)),
            Eq(A("case", "physical_logged"), L(0.0)),
            Lt(A("life", "health"), A("life", "max_health")),
        ]),
        [
            ["add_node", "ev", "Evidence", {"kind": 3.0, "weight": PHYSICAL_W}],
            ["add_edge", "case", "has_evidence", "ev"],
            ["set_attr", "case", "physical_logged", 1.0],
        ],
    )

    # bv_form_belief: ABDUCTION (the case-reconstruction / manifold move). observed
    # := Sum of the case's evidence weights; the verdict is the Argmax over the
    # constable's HELD CaseGenerator codebook by fit -|predicts - observed| (a
    # min-distance exact selection between guilty/innocent). A RECONSTRUCTION, not a
    # fact: strong evidence concentrates on guilty; weak/contradicted stays innocent.
    observed = Sum(Neighbours("case", "has_evidence"), "e", A("e", "weight"))
    fit_g = Minus(L(0.0), Abs(Minus(A("g", "predicts_evidence"), observed)))
    best_gen = Argmax(Neighbours("con", "has_case_generator"), "g", fit_g)
    bv_form_belief = rule(
        "bv_form_belief",
        [["con", "investigates", "case"]],
        And([
            Eq(A("case", "known"), L(1.0)),
            Eq(A("case", "belief_formed"), L(0.0)),
        ]),
        [
            ["set_attr", "case", "verdict",
             T({"type": "Attr", "node": best_gen, "key": "verdict"})],
            ["set_attr", "case", "confidence", T(observed)],
            ["add_node", "bel", "Belief", {
                "verdict": T({"type": "Attr", "node": best_gen, "key": "verdict"}),
                "confidence": T(observed)}],
            ["add_edge", "con", "believes", "bel"],
            ["set_attr", "case", "belief_formed", 1.0],
        ],
    )

    # bv_sufficient_proof: "SUFFICIENT PROOF" is the belief crossing a confidence
    # threshold (the decision_value). Only a GUILTY verdict with confidence >=
    # proof_threshold is proven; insufficient evidence (or an innocent verdict)
    # DECLINES -- the unseen-abuse / false-accusation floor, for the RIGHT reason.
    bv_sufficient_proof = rule(
        "bv_sufficient_proof",
        [["con", "investigates", "case"]],
        And([
            Eq(A("case", "belief_formed"), L(1.0)),
            Eq(A("case", "verdict"), L(1.0)),
            Gte(A("case", "confidence"), A("con", "proof_threshold")),
            Eq(A("case", "proven"), L(0.0)),
        ]),
        [["set_attr", "case", "proven", 1.0]],
    )
    return [bv_witness_evidence, bv_report_evidence, bv_physical,
            bv_form_belief, bv_sufficient_proof]


# ========================================================= THE PROSECUTE seed
def prosecute_rules():
    # bv_prosecute: a PROVEN case is prosecuted WITH THE COUNCIL (the state). Mints
    # a Prosecution carrying the act's magnitude (amount) + the accused label.
    bv_prosecute = rule(
        "bv_prosecute",
        [["con", "investigates", "case"], ["con", "files_with", "council"]],
        And([
            Eq(A("case", "proven"), L(1.0)),
            Eq(A("case", "prosecuted"), L(0.0)),
        ]),
        [
            ["add_node", "pros", "Prosecution", {
                "about": T(AttrRaw("case", "aggressor")),
                "amount": T(A("case", "amount")),
                "adjudicated": 0.0, "convicted": 0.0, "sanctioned": 0.0}],
            ["add_edge", "pros", "at_council", "council"],
            ["set_attr", "case", "prosecuted", 1.0],
        ],
    )

    # the council backing-graph: Sum of vote over SEATED CouncilMembers. Each
    # seated member contributes its vote (+1 back / -1 oppose); John's seat is a
    # bloc that can tip the sum either way (structural corruption of justice).
    council_sum = Sum(NodesOfType("CouncilMember"), "cm",
                      IfThenElse(Eq(A("cm", "is_seated"), L(1.0)),
                                 A("cm", "vote"), L(0.0)))

    # bv_council_convict: the council ADJUDICATES -- convicts iff the seated
    # backing sums above zero. Corruptible: John (vote=-1) can BLOCK a true
    # prosecution of an ally; John (vote=+1) can PUSH a false one. Ablate John's
    # seat (is_seated=0) -> the sum flips -> the outcome flips.
    bv_council_convict = rule(
        "bv_council_convict",
        [["pros", "at_council", "council"]],
        And([
            Eq(A("pros", "adjudicated"), L(0.0)),
            Gt(council_sum, L(0.0)),
        ]),
        [
            ["add_node", "conv", "Conviction", {"about": T(AttrRaw("pros", "about"))}],
            ["add_edge", "pros", "conviction", "conv"],
            ["set_attr", "pros", "convicted", 1.0],
            ["set_attr", "pros", "adjudicated", 1.0],
        ],
    )

    # bv_council_acquit: the disjoint acquittal arm -- seated backing <= 0 -> no
    # conviction (the biased council leaves the accused untouched).
    bv_council_acquit = rule(
        "bv_council_acquit",
        [["pros", "at_council", "council"]],
        And([
            Eq(A("pros", "adjudicated"), L(0.0)),
            Lte(council_sum, L(0.0)),
        ]),
        [
            ["set_attr", "pros", "convicted", 0.0],
            ["set_attr", "pros", "acquitted", 1.0],
            ["set_attr", "pros", "adjudicated", 1.0],
        ],
    )

    # bv_warn / bv_punish: MAGNITUDE, not the trigger, sets the severity. A small
    # amount (stupid fight) -> a WARNING; a large amount -> PUNISHMENT. A Sanction
    # is a graph record (a censure), never a reward/punishment token on a person.
    bv_warn = rule(
        "bv_warn",
        [["pros", "at_council", "council"]],
        And([
            Eq(A("pros", "convicted"), L(1.0)),
            Eq(A("pros", "sanctioned"), L(0.0)),
            Lte(A("pros", "amount"), A("council", "warn_threshold")),
        ]),
        [
            ["add_node", "s", "Sanction", {"kind": 1.0,
                                           "about": T(AttrRaw("pros", "about"))}],
            ["add_edge", "pros", "sanction", "s"],
            ["set_attr", "pros", "sanction_kind", 1.0],
            ["set_attr", "pros", "sanctioned", 1.0],
        ],
    )
    bv_punish = rule(
        "bv_punish",
        [["pros", "at_council", "council"]],
        And([
            Eq(A("pros", "convicted"), L(1.0)),
            Eq(A("pros", "sanctioned"), L(0.0)),
            Gt(A("pros", "amount"), A("council", "warn_threshold")),
        ]),
        [
            ["add_node", "s", "Sanction", {"kind": 2.0,
                                           "about": T(AttrRaw("pros", "about"))}],
            ["add_edge", "pros", "sanction", "s"],
            ["set_attr", "pros", "sanction_kind", 2.0],
            ["set_attr", "pros", "sanctioned", 1.0],
        ],
    )
    return [bv_prosecute, bv_council_convict, bv_council_acquit, bv_warn, bv_punish]


# ============================================================== THE KILL seed
def kill_rules():
    # bv_death_tag: R14 bl_death is REUSED UNCHANGED (health<=0 -> dead,
    # death_cause = last_cause). Violence tags last_cause=5, so a death BY violence
    # arrives as death_cause=5; this rule only READS that back into a glass-box
    # death_by_violence flag (the FIFTH route to death). No death decision here.
    bv_death_tag = rule(
        "bv_death_tag",
        [["p", "has_life", "life"]],
        And([
            Eq(A("p", "just_died"), L(1.0)),
            Eq(A("p", "death_cause"), L(5.0)),
            Eq(A("p", "death_by_violence"), L(0.0)),
        ]),
        [["set_attr", "p", "death_by_violence", 1.0]],
    )
    return [bv_death_tag]


def main():
    seeds = {
        "bigville_viol_act": seed(
            "bigville_viol_act",
            "BIGVILLE R15 (block 263000) -- THE VIOLENT ACT. bv_trigger is the "
            "value-DECISION to commit violence (trigger_value = snap_pressure + "
            "w_spite*spite_gain + hunger*desperation_gain vs trigger_threshold, "
            "gated on STAMINA energy>=attack_cost) -- the outward form of the 242 "
            "frustration-SNAP / spite / DESPERATION, NOT random; bv_refrain is the "
            "disjoint decline arm (ablate the trigger -> refrain, no act). A "
            "committed ViolentAct{amount,cost} costs BOTH: bv_harm_victim drops the "
            "victim's HEALTH by amount (the R14 acute arm, last_cause=5 violence -> "
            "R14 bl_death routes death_cause=5 at zero -- the FIFTH route to death) "
            "and bv_cost_aggressor drops the aggressor's STAMINA (R1 energy) by "
            "cost. Magnitude is a scalar. NO reward/punishment token. ZERO new Rust.",
            act_rules()),
        "bigville_viol_evidence": seed(
            "bigville_viol_evidence",
            "BIGVILLE R15 (block 263000) -- THE 247 EVIDENCE-AND-PROOF PIPELINE (NOT "
            "omniscience). The constable learns of an act by WITNESS "
            "(bv_witness_evidence, line-of-sight) OR REPORT (bv_report_evidence, a "
            "testimony Message -- the load-bearing report channel); bv_physical logs "
            "the victim's real health-drop as PHYSICAL evidence (the corroboration a "
            "false report lacks). bv_form_belief is the ABDUCTION: observed = Sum of "
            "evidence weights, verdict = Argmax over the constable's held "
            "CaseGenerator codebook by fit -|predicts-observed| (a RECONSTRUCTION, "
            "not a fact -- the manifold-of-projections move). bv_sufficient_proof "
            "requires a GUILTY verdict with confidence >= proof_threshold (the "
            "decision_value); insufficient/contradicted evidence DECLINES for the "
            "RIGHT reason (unseen-abuse / false-accusation floor). ZERO new Rust.",
            evidence_rules()),
        "bigville_viol_prosecute": seed(
            "bigville_viol_prosecute",
            "BIGVILLE R15 (block 263000) -- PROSECUTION THROUGH THE CORRUPTIBLE "
            "COUNCIL (R9 / 247). bv_prosecute files a proven case with the council; "
            "bv_council_convict / bv_council_acquit adjudicate over the "
            "backing-graph (Sum of vote over SEATED CouncilMembers > 0 -> a "
            "Conviction) -- John's seat is a bloc that can BLOCK a true prosecution "
            "(vote=-1) or PUSH a false one (vote=+1); ablate his seat (is_seated=0) "
            "and the outcome flips (a clean structural counterfactual). bv_warn / "
            "bv_punish sanction by AMOUNT magnitude (warn if amount<=warn_threshold "
            "else punish) -- magnitude, not the trigger, sets the severity. A "
            "Sanction is a graph record (censure), NOT a reward/punishment token on "
            "a person. ZERO new Rust.",
            prosecute_rules()),
        "bigville_viol_kill": seed(
            "bigville_viol_kill",
            "BIGVILLE R15 (block 263000) -- THE FIFTH ROUTE TO DEATH. R14 bl_death "
            "is reused UNCHANGED (health<=0 -> dead, death_cause = last_cause); "
            "violence tags last_cause=5, so a death BY violence arrives as "
            "death_cause=5. bv_death_tag only READS that back into a glass-box "
            "death_by_violence flag -- no death decision lives here (murder / "
            "manslaughter is the acute health arm at magnitude). ZERO new Rust.",
            kill_rules()),
    }
    for sid, s in seeds.items():
        path = os.path.join(SEED_DIR, sid + ".json")
        with open(path, "w") as f:
            json.dump(s, f, indent=1)
            f.write("\n")
        print("wrote", path, "(%d rules)" % len(s["rules"]))


if __name__ == "__main__":
    main()
