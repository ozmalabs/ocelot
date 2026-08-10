#!/usr/bin/env python3
"""BLOCK 215000 -- authoring tool that EMITS seeds/grievance_succeed.json.

This is a one-off seed BUILDER (emits graph data only; not agent runtime), of
the same class as the other tools/ authoring scripts. Every agent DECISION is a
rule inside the emitted seed; this file only assembles the JSON. Run:

    python3 tools/build_grievance_seed.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "grievance_succeed.json")

EFF_THRESH = 5   # efficacy >= 5 => HIGH (a viable path to win) => SUCCEED channel


# ---- term helpers (integer-native; every Lit is a whole number) -------------
def V(name):            return {"type": "Var", "name": name}
def L(v):               return {"type": "Lit", "value": float(v)}
def A(var, key):        return {"type": "Attr", "node": V(var), "key": key}
def AT(term, key):      return {"type": "Attr", "node": term, "key": key}
def Minus(a, b):        return {"type": "Minus", "a": a, "b": b}
def IDiv(a, b):         return {"type": "IDiv", "a": a, "b": b}
def Ashr(a, b):         return {"type": "Ashr", "a": a, "b": b}
def Gte(a, b):          return {"type": "Gte", "a": a, "b": b}
def Eq(a, b):           return {"type": "Eq", "a": a, "b": b}
def Maxi(items):        return {"type": "Max", "items": items}
def Times(items):       return {"type": "Times", "items": items}
def Plus(items):        return {"type": "Plus", "items": items}
def And(items):         return {"type": "And", "items": items}
def Not(arg):           return {"type": "Not", "arg": arg}
def Neigh(node, et):    return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}
def Sum(source, var, value):
    return {"type": "Sum", "source": source, "var_name": var, "value": value}
def Argmax(source, var, value):
    return {"type": "Argmax", "source": source, "var_name": var, "value": value}
def T(term):            return {"__term__": term}


ENABLED = Eq(A("gp", "enabled"), L(1))


seed = {
    "id": "grievance_succeed",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": [],
    "area": "retina",
    "description": (
        "BLOCK 215000 -- SPITE-TO-SUCCEED: a GRIEVANCE (an appraised slight from a "
        "specific rival) AMPLIFIES the value of the agent's OWN achievement -- the "
        "CONSTRUCTIVE face of spite (underdog / chip-on-shoulder / vindication), "
        "nearly the inverse of destructive spite (harm-the-other-at-self-cost, block "
        "213000). Every decision is a RULE over the LANDED 204000 core_emotions "
        "economy: gs_choose_action is Argmax_c (total_value(c) + amp(c)) over the "
        "agent's candidate Appraisals; the amplification amp is the ONLY new term and "
        "it is graph data. The grievance magnitude is a LEAKY ACCUMULATOR -- a Sum of "
        "196000 scale2 (Ashr, x2^-k) decayed slight contributions, idempotent under "
        "the run_rules fixpoint (a pure function of immutable Slight nodes + "
        "adapter-advanced now_epoch). Efficacy gates the CHANNEL: HIGH efficacy "
        "(>=5, a viable path to win) fires gs_amplify_succeed -> amp = G*max(0,effort-"
        "rival_ach)*observed_by_rival, raising OWN competence candidates (self-"
        "benefiting, directed, witnessed); LOW efficacy fires gs_amplify_destroy -> "
        "amp = G*rival_harm on the destroy candidates (self-costly, ties 213000). "
        "The SAME grievance, one knob (efficacy), flips succeed<->destroy. "
        "Integer-native (Sum/Ashr/IDiv/Max/Times/Plus/Minus/Gte/Eq/And/Not/Argmax/"
        "Attr; no Rust, no new Term). OFF by default: self_load_only, nothing "
        "depends_on it, every rule guards on HeldGrievanceParams.enabled -- absent it "
        "every existing path is byte-identical. A glass-box named-knob MODEL of the "
        "underdog effect; the contribution is the attribution + the efficacy-gates-"
        "channel unification of constructive vs destructive spite, not new psychology."
    ),
    "microtheory": {
        "name": "grievance_succeed",
        "description": (
            "A grievance is a leaky accumulator built from appraised slights by a "
            "specific rival; it re-weights the agent's OWN achievement valuation. "
            "Efficacy (competence-belief) is the switch: with a path to win the "
            "grievance drives constructive success (vindication); with no path the "
            "same grievance collapses into destructive spite."
        ),
    },
    "nodes": [],
    "edges": [],
    "productions": [
        {"provenance": "seed:grievance_succeed:gparams",
         "src": {"type": "EmotionHub", "var": "hub"},
         "edge_type": "has_grievance_params",
         "tgt": {"type": "HeldGrievanceParams", "var": "gp"}},
        {"provenance": "seed:grievance_succeed:grievance",
         "src": {"type": "EmotionHub", "var": "hub"},
         "edge_type": "has_grievance",
         "tgt": {"type": "Grievance", "var": "gr"}},
        {"provenance": "seed:grievance_succeed:slight",
         "src": {"type": "Grievance", "var": "gr"},
         "edge_type": "from_slight",
         "tgt": {"type": "Slight", "var": "sl"}},
        {"provenance": "seed:grievance_succeed:candidate",
         "src": {"type": "EmotionHub", "var": "hub"},
         "edge_type": "has_candidate",
         "tgt": {"type": "Appraisal", "var": "c"}},
        {"provenance": "seed:grievance_succeed:decision",
         "src": {"type": "EmotionHub", "var": "hub"},
         "edge_type": "has_action_decision",
         "tgt": {"type": "AchieveDecision", "var": "dec"}},
    ],
    "rules": [
        # ---- (0) the grievance magnitude: leaky accumulator = Sum of scale2-decayed
        #          slight contributions. magnitude = Sum_s ( s.magnitude >> ((now - s.epoch)/half_life) ).
        #          Idempotent SET: pure function of immutable Slight nodes + now_epoch.
        {"name": "gs_grievance_from_slights",
         "area": "retina", "order": 0, "latency_class": "hard_realtime",
         "comment": "The grievance BUILDS from slights and DECAYS via the 196000 "
                    "scale2 (Ashr) half-life law. A held grudge = large half_life "
                    "(slow decay); a fleeting slight = small half_life. No slight -> "
                    "empty Sum -> magnitude 0 -> no amplification.",
         "match": [["hub", "has_grievance_params", "gp"], ["hub", "has_grievance", "gr"]],
         "where": ENABLED,
         "effects": [
             ["set_attr", "gr", "magnitude", T(
                 Sum(Neigh(V("gr"), "from_slight"), "sl",
                     Ashr(A("sl", "magnitude"),
                          IDiv(Minus(A("gr", "now_epoch"), A("sl", "epoch")),
                               Maxi([L(1), A("gr", "half_life")])))))],
         ]},

        # ---- (1a) SUCCEED channel (HIGH efficacy): amplify OWN achievement.
        #           amp = G * max(0, effort - rival_ach) * observed_by_rival.
        {"name": "gs_amplify_succeed",
         "area": "retina", "order": 1, "latency_class": "hard_realtime",
         "comment": "HIGH efficacy (a viable path to win): the grievance raises the "
                    "value of surpassing the SPECIFIC rival's standing, WITNESSED by "
                    "them, scaled by grievance magnitude. Self-benefiting (own output "
                    "rises). amp lands on the candidate; gs_choose_action ranks by "
                    "total_value + amp. This is WHERE the competence amplification lives.",
         "match": [["hub", "has_grievance_params", "gp"], ["hub", "has_grievance", "gr"],
                   ["hub", "has_candidate", "c"]],
         "where": And([ENABLED,
                       Eq(A("c", "kind_succeed"), L(1)),
                       Gte(A("gp", "efficacy"), L(EFF_THRESH))]),
         "effects": [
             ["set_attr", "c", "amp", T(
                 Times([Times([A("gr", "magnitude"),
                               Maxi([L(0), Minus(A("c", "effort"), A("gr", "rival_ach"))])]),
                        A("c", "observed_by_rival")]))],
         ]},

        # ---- (1b) DESTROY channel (LOW efficacy): the same grievance collapses into
        #           destructive spite. amp = G * rival_harm on the destroy candidates.
        {"name": "gs_amplify_destroy",
         "area": "retina", "order": 1, "latency_class": "hard_realtime",
         "comment": "LOW efficacy (no path to win): gs_amplify_succeed is gated OFF; "
                    "the grievance instead values HARMING the rival -- self-costly "
                    "(destroy candidates carry individual_benefit = -sabotage). Ties "
                    "block 213000's harm-the-other-at-self-cost. The SAME grievance, "
                    "the efficacy knob flips the channel.",
         "match": [["hub", "has_grievance_params", "gp"], ["hub", "has_grievance", "gr"],
                   ["hub", "has_candidate", "c"]],
         "where": And([ENABLED,
                       Eq(A("c", "kind_destroy"), L(1)),
                       Not(Gte(A("gp", "efficacy"), L(EFF_THRESH)))]),
         "effects": [
             ["set_attr", "c", "amp", T(Times([A("gr", "magnitude"), A("c", "rival_harm")]))],
         ]},

        # ---- (5) the decision: Argmax over candidates by (landed total_value + amp).
        #          The 204000 total_value is UNCHANGED; amp is the only added term.
        {"name": "gs_choose_action",
         "area": "retina", "order": 5, "latency_class": "hard_realtime",
         "comment": "The agent's choice: Argmax_c (total_value(c) + amp(c)) over its "
                    "candidate Appraisals. total_value is computed by the unchanged "
                    "204000 core_emotions rules; amp is the grievance amplification. "
                    "Read off the winner: output (competence produced), rival_harm, "
                    "kind_succeed, effort. Restraint/effort FALLS OUT of the Argmax.",
         "match": [["hub", "has_grievance_params", "gp"], ["hub", "has_action_decision", "dec"]],
         "where": ENABLED,
         "effects": [
             ["set_attr", "dec", "chosen_output", T(
                 AT(Argmax(Neigh(V("hub"), "has_candidate"), "c",
                           Plus([A("c", "total_value"), A("c", "amp")])), "output"))],
             ["set_attr", "dec", "chosen_rival_harm", T(
                 AT(Argmax(Neigh(V("hub"), "has_candidate"), "c",
                           Plus([A("c", "total_value"), A("c", "amp")])), "rival_harm"))],
             ["set_attr", "dec", "chosen_kind_succeed", T(
                 AT(Argmax(Neigh(V("hub"), "has_candidate"), "c",
                           Plus([A("c", "total_value"), A("c", "amp")])), "kind_succeed"))],
             ["set_attr", "dec", "chosen_effort", T(
                 AT(Argmax(Neigh(V("hub"), "has_candidate"), "c",
                           Plus([A("c", "total_value"), A("c", "amp")])), "effort"))],
         ]},
    ],
}


def main():
    with open(OUT, "w") as f:
        json.dump(seed, f, indent=1)
        f.write("\n")
    # integer-native self-check
    bad = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), float) \
               and not float(o["value"]).is_integer():
                bad.append(o["value"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(seed)
    assert bad == [], bad
    print("wrote", OUT, "-- integer-native OK, rules:", [r["name"] for r in seed["rules"]])


if __name__ == "__main__":
    main()
