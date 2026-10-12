#!/usr/bin/env python3
"""Tranche 24: an adoption reopens the concerns it may now make answerable.

Measured on tranche 23's production run: the agent adopted a generalised
receipt pair (disposition_generalise) for statements that are not responses.
That adoption put a second class -- the 19 statements with no
language_statement_act -- exactly one guard away from a held pair. Rebuilt
then, the builder succeeds. But the loop never asked again:
  (1) variation_pick excluded a family that had abstained for a concern,
      forever (variation_ops v1.13.0);
  (2) no rule reopened an abstained concern;
  (3) in production a retry only executes inside the `concern` host action,
      which the scheduler requests only while a StandingConcern is pending.

This is the decision-opening grammar of paper 02c applied to the agent's own
improver: a standing verdict ('abstained') is retained until a represented
change in the conditions that produced it. The change here is the agent's own
repertoire: the count of Adoption nodes (the repertoire epoch).

  * self_optimisation v1.6.0 -- close_abstained_variant stamps
    SeedDelta.abstain_epoch = the number of Adoptions at abstention.
  * variation_ops v1.21.0 -- an abstention excludes its family only at the
    epoch it was recorded (an unstamped abstention still excludes).
  * instruction_repair_retry v1.4.0 -- irr_reopen_on_new_capability marks
    retry_requested on a promoted concern of a policy-listed kind
    (reopen_kinds, default ['unanswered', 'comprehension']) when every one of
    its experiments abstained, all at older epochs, none is in flight, and
    reopen_count < max_reopens (default 2).
  * cognitive_scheduler v1.0.3 -- supervise_requested_retry (+ _rearm)
    requests the `concern` host action while a SelfConcern carries
    retry_requested, so the executor runs in production.
Idempotent, per seed by version.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Ex(t, var, pred): return {"type": "Exists", "source": {"type": "NodesOfType", "node_type": t}, "var_name": var,
                              "predicate": pred}
def Ifnull0(x): return {"type": "IfThenElse", "cond": Eq(x, L(None)), "then": L(0), "other": x}


EPOCH = {"type": "Count", "source": {"type": "NodesOfType", "node_type": "Adoption"}}


def vtuple(v): return tuple(map(int, v.split(".")))


def load(name):
    p = ROOT / "seeds" / f"{name}.json"
    text = p.read_text()
    return p, json.loads(text), text.endswith("\n")


def save(p, d, nl):
    p.write_text(json.dumps(d, indent=1, ensure_ascii=True) + ("\n" if nl else ""))


# 1. self_optimisation: stamp the epoch at abstention ------------------------
p, d, nl = load("self_optimisation")
if vtuple(d["version"]) < (1, 6, 0):
    r = next(r for r in d["rules"] if r["name"] == "close_abstained_variant")
    r["effects"].append(["set_attr", "delta", "abstain_epoch", {"__term__": EPOCH}])
    d["description"] += (" || v1.6.0 (2026-10-10, tranche 24): close_abstained_variant stamps "
                         "SeedDelta.abstain_epoch = the count of Adoptions at abstention (the agent's repertoire "
                         "epoch), so an abstention can be reconsidered once the repertoire changes "
                         "(scripts/gen_reopen_on_new_capability.py).")
    d["version"] = "1.6.0"
    save(p, d, nl)
    print("self_optimisation 1.6.0")

# 2. variation_ops: abstention excludes only at its own epoch ----------------
p, d, nl = load("variation_ops")
if vtuple(d["version"]) < (1, 21, 0):
    prog_node = next(n for n in d["nodes"] if n["type"] == "Program" and n["attrs"]["name"] == "variation_pick")
    prog = json.loads(prog_node["attrs"]["program"])
    hits = []

    def walk(x):
        if isinstance(x, dict):
            if x.get("type") == "And" and Eq(A("rd", "variant_abstained"), L(1.0)) in x.get("items", []):
                hits.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(prog)
    assert len(hits) == 1, len(hits)
    hits[0]["items"].append(Or(Eq(A("rd", "abstain_epoch"), L(None)), Eq(A("rd", "abstain_epoch"), EPOCH)))
    prog_node["attrs"]["program"] = json.dumps(prog)
    d["description"] += (" v1.21.0 (2026-10-10, tranche 24): an abstention excludes its family for the concern only "
                         "at the repertoire epoch it was recorded (SeedDelta.abstain_epoch == the current count of "
                         "Adoptions; unstamped abstentions still exclude) -- after the agent adopts something, a "
                         "family that abstained may be tried again (scripts/gen_reopen_on_new_capability.py).")
    d["version"] = "1.21.0"
    save(p, d, nl)
    print("variation_ops 1.21.0")

# 3. instruction_repair_retry: reopen on a new capability --------------------
p, d, nl = load("instruction_repair_retry")
if vtuple(d["version"]) < (1, 4, 0):
    pol = next(n for n in d["nodes"] if n["type"] == "InstructionRetryPolicy")
    pol["attrs"]["reopen_kinds"] = ["unanswered", "comprehension"]
    pol["attrs"]["max_reopens"] = 2
    mine = Eq(A("e", "axis_tag"), A("st", "name"))
    mine_d = Eq(A("rd", "concern_key"), A("st", "name"))
    abst = Eq(A("rd", "variant_abstained"), L(1.0))
    rule = {
        "name": "irr_reopen_on_new_capability",
        "comment": ("tranche 24: a promoted concern whose every experiment abstained is reopened once the agent's "
                    "repertoire (count of Adoptions) has changed since its last abstention."),
        "match": [["ag", "has_instruction_retry_policy", "pol"], ["ag", "has_self_concern", "sc"],
                  ["sc", "promoted_to", "st"]],
        "where": And(
            Eq(A("pol", "enabled"), L(1)),
            {"type": "In", "member": A("sc", "kind"), "container": A("pol", "reopen_kinds")},
            Eq(A("sc", "status"), L("promoted")),
            Not(Eq(A("sc", "retry_requested"), L(1))),
            {"type": "Lt", "a": Ifnull0(A("sc", "reopen_count")), "b": A("pol", "max_reopens")},
            # at most once per repertoire epoch: one reopen per represented change
            Not(Eq(A("sc", "reopened_at_epoch"), EPOCH)),
            # it has been tried, and every trial abstained (none in flight, none judged)
            Ex("Experiment", "e", mine),
            Not(Ex("Experiment", "e", And(mine, Not(Eq(A("e", "outcome"), L("abstained")))))),
            # every abstention predates the current repertoire epoch
            Ex("SeedDelta", "rd", And(mine_d, abst, Not(Eq(A("rd", "abstain_epoch"), L(None))))),
            Not(Ex("SeedDelta", "rd", And(mine_d, abst, Or(Eq(A("rd", "abstain_epoch"), L(None)),
                                                          Eq(A("rd", "abstain_epoch"), EPOCH)))))),
        "effects": [
            ["set_attr", "sc", "retry_requested", 1],
            ["set_attr", "sc", "reopen_count", {"__term__": {"type": "Plus", "items": [Ifnull0(A("sc", "reopen_count")), L(1)]}}],
            ["set_attr", "sc", "reopened_at_epoch", {"__term__": EPOCH}],
            ["set_attr", "sc", "reopen_reason",
             "my repertoire changed (an adoption) since every variation for this concern abstained"]]}
    d["rules"].append(rule)
    d["description"] += ("\n\nv1.4.0 (tranche 24): `irr_reopen_on_new_capability` reopens a promoted concern of a "
                         "policy-listed kind (reopen_kinds) whose every experiment abstained, all at an older "
                         "repertoire epoch (SeedDelta.abstain_epoch < count of Adoptions), up to max_reopens. An "
                         "adoption can put a class the builder abstained on within reach (measured: tranche 23).\n")
    d["version"] = "1.4.0"
    save(p, d, nl)
    print("instruction_repair_retry 1.4.0")

# 4. cognitive_scheduler: request `concern` while a retry is marked -----------
p, d, nl = load("cognitive_scheduler")
if vtuple(d["version"]) < (1, 0, 3):
    PENDING_SC = Ex("StandingConcern", "source", None)  # placeholder shape, not used directly

    def retarget(rule, name):
        r = copy.deepcopy(rule)
        r["name"] = name
        n = [0]

        def fix(x):
            if isinstance(x, dict):
                # the per-source predicate over pending StandingConcerns, in where and in the Argmax filter
                src = x.get("source")
                if x.get("var_name") == "source" and isinstance(src, dict) \
                        and src.get("type") == "NodesOfType" and src.get("node_type") == "StandingConcern":
                    x["source"] = {"type": "NodesOfType", "node_type": "SelfConcern"}
                    x["predicate"] = Eq(A("source", "retry_requested"), L(1))
                    n[0] += 1
                    return
                for v in x.values():
                    fix(v)
            elif isinstance(x, list):
                for v in x:
                    fix(v)
        fix(r)
        for eff in r["effects"]:
            if isinstance(eff, list) and len(eff) > 3 and isinstance(eff[3], dict) and eff[3].get("source_type"):
                eff[3]["source_type"] = "SelfConcern"
        assert n[0] >= 2, (name, n[0])
        r["comment"] = ("tranche 24: request the `concern` host action while a SelfConcern carries retry_requested "
                        "(its executor runs the agent's own retry); one in-flight concern request at a time.")
        return r
    base = {r["name"]: r for r in d["rules"]}
    d["rules"].append(retarget(base["supervise_pending_concern"], "supervise_requested_retry"))
    d["rules"].append(retarget(base["supervise_pending_concern_rearm"], "supervise_requested_retry_rearm"))
    if "description" in d:
        d["description"] += (" v1.0.3 (tranche 24): supervise_requested_retry(+_rearm) -- the `concern` host action "
                             "is also requested while a SelfConcern carries retry_requested (before this an agent "
                             "retry ran only if another concern happened to be pending).")
    d["version"] = "1.0.3"
    save(p, d, nl)
    print("cognitive_scheduler 1.0.3")
