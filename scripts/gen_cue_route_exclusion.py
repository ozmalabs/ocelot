#!/usr/bin/env python3
"""Tranche 5: cue_route_pick excludes routes already REFUTED for this verb.

seeds/variation_ops.json v1.6.0. A cue-set-edit experiment carries
SeedDelta{cue_concept_added: verb, cue_route: route}; once its Experiment is
judged `refuted` (under the corrected replay judge: a change into the error
surface is refuted), the held route pick no longer proposes that route for
that verb. A (human-gated) retry of the same concern therefore tries the next
pooled route instead of repeating the refuted one. Graph join inside the held
Program -- no Python reads the outcome. Idempotent.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "seeds/variation_ops.json"
V = lambda n: {"type": "Var", "name": n}
A = lambda n, k: {"type": "Attr", "node": V(n), "key": k}
L = lambda v: {"type": "Lit", "value": v}
EXCL = {"type": "Not", "arg": {"type": "Exists", "source": {"type": "NodesOfType", "node_type": "SeedDelta"},
        "var_name": "rd", "predicate": {"type": "And", "items": [
            {"type": "Eq", "a": A("rd", "cue_concept_added"), "b": V("verb")},
            {"type": "Eq", "a": A("rd", "cue_route"), "b": A("c", "instruction_route")},
            {"type": "Exists", "source": {"type": "InNeighbours", "node": V("rd"), "edge_type": "has_delta"},
             "var_name": "rx", "predicate": {"type": "Eq", "a": A("rx", "outcome"), "b": L("refuted")}}]}}}
text = P.read_text(); d = json.loads(text)
node = next(n for n in d["nodes"] if n["attrs"].get("name") == "cue_route_pick")
prog = json.loads(node["attrs"]["program"])
items = prog["other"]["body"]["value"]["source"]["predicate"]["items"]
if not any("cue_concept_added" in json.dumps(it) for it in items):
    items.append(EXCL)
    node["attrs"]["program"] = json.dumps(prog)
    d["version"] = max(d["version"], "1.6.0", key=lambda v: tuple(map(int, v.split("."))))
    if "v1.6.0 (2026" not in d["description"]: d["description"] += (" v1.6.0 (2026-10-07, tranche 5): cue_route_pick excludes a route already refuted for the same verb"
                         " (SeedDelta.cue_route joined to its Experiment's outcome), so a retry tries the next pooled route"
                         " (scripts/gen_cue_route_exclusion.py).")
    P.write_text(json.dumps(d, indent=1, ensure_ascii=False) + ("\n" if text.endswith("\n") else ""))
# v1.9.0: a route judged INCONCLUSIVE (no fix observed) is excluded too -- the
# corrected judge returns inconclusive when the paired control already fails
# the turn, so re-proposing that route can never show a fix.
if '"value": "refuted"}}]}}}' in json.dumps(EXCL):
    pass
_rx = EXCL["arg"]["predicate"]["items"][2]
_new_pred = {"type": "In", "member": A("rx", "outcome"), "container": L(["refuted", "inconclusive"])}
for n in d["nodes"]:
    if n["attrs"].get("name") == "cue_route_pick":
        _pr = json.loads(n["attrs"]["program"])
        for it in _pr["other"]["body"]["value"]["source"]["predicate"]["items"]:
            if it.get("type") == "Not" and it["arg"].get("type") == "Exists" and "cue_concept_added" in json.dumps(it):
                _ex = it["arg"]["predicate"]["items"][2]
                if _ex["predicate"] != _new_pred:
                    _ex["predicate"] = _new_pred
                    n["attrs"]["program"] = json.dumps(_pr)
                    d["version"] = max(d["version"], "1.9.0", key=lambda v: tuple(map(int, v.split("."))))
                    if "v1.9.0 (2026" not in d["description"]: d["description"] += (" v1.9.0 (2026-10-07, tranche 5): cue_route_pick also excludes a route judged"
                                         " inconclusive for the verb (no fix observed).")
                    P.write_text(json.dumps(d, indent=1, ensure_ascii=False) + ("\n" if text.endswith("\n") else ""))
        prog = json.loads(n["attrs"]["program"]) if n["attrs"].get("name") == "cue_route_pick" else prog
node = next(n for n in d["nodes"] if n["attrs"].get("name") == "cue_route_pick")
prog = json.loads(node["attrs"]["program"])
# v1.7.0 EXPLORATION (opt-in): with VariationOp{cue_set_edit}.explore_unscored
# == 1 the pick returns the best untried pooled route even when nothing scores
# (bigram overlap 0) -- under the corrected judge the replay experiment is the
# validator, so an unscored proposal costs one refutable trial, not a false
# adoption. Absent -> the honest-abstain behaviour is unchanged.
body = prog["other"]["body"]["body"]
inner = body["other"]
if inner["cond"].get("type") != "Or":
    explore = {"type": "Eq", "b": L(1), "a": {"type": "Attr", "key": "explore_unscored", "node": {
        "type": "Argmin", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "VariationOp"},
        "var_name": "v", "predicate": {"type": "Eq", "a": A("v", "name"), "b": L("cue_set_edit")}},
        "var_name": "x", "value": L(0), "default": None}}}
    inner["cond"] = {"type": "Or", "items": [inner["cond"], explore]}
    node["attrs"]["program"] = json.dumps(prog)
    d["version"] = max(d["version"], "1.7.0", key=lambda v: tuple(map(int, v.split("."))))
    if "v1.7.0 (2026" not in d["description"]: d["description"] += (" v1.7.0 (2026-10-07, tranche 5): opt-in VariationOp{cue_set_edit}.explore_unscored==1 lets"
                         " cue_route_pick propose the best untried pooled route when no route scores; absent -> unchanged.")
    P.write_text(json.dumps(d, indent=1, ensure_ascii=False) + ("\n" if text.endswith("\n") else ""))
# v1.10.0 ROUTE OVERRIDE (tranche 6): the pick abstained whenever the verb
# already carried a route. But an instruction gap FILED for that verb is the
# agent's own evidence that the held route does not handle it (measured:
# 'summarise' -> self_report, yet "Summarise the data." is unhandled). The
# abstain now requires routed AND no filed instruction gap for the verb; the
# candidate pool already excludes the verb's own Concept, so an override
# proposes a DIFFERENT pooled route, validated (and regression-guarded) by the
# replay experiment like any cue edit.
node = next(n for n in d["nodes"] if n["attrs"].get("name") == "cue_route_pick")
prog = json.loads(node["attrs"]["program"])
GAP = {"type": "Exists", "source": {"type": "NodesOfType", "node_type": "SelfConcern"}, "var_name": "gq",
       "predicate": {"type": "And", "items": [{"type": "Eq", "a": A("gq", "kind"), "b": L("instruction")},
                                              {"type": "Eq", "a": A("gq", "predicate"), "b": V("verb")}]}}
if "SelfConcern" not in json.dumps(prog["cond"]):
    prog["cond"] = {"type": "And", "items": [prog["cond"], {"type": "Not", "arg": GAP}]}
    node["attrs"]["program"] = json.dumps(prog)
    d["version"] = max(d["version"], "1.10.0", key=lambda v: tuple(map(int, v.split("."))))
    if "v1.10.0 (2026" not in d["description"]:
        d["description"] += (" v1.10.0 (2026-10-08, tranche 6): cue_route_pick no longer abstains for an already-routed verb"
                             " when an instruction gap is filed for it (route override, replay-validated).")
    P.write_text(json.dumps(d, indent=1, ensure_ascii=False) + ("\n" if text.endswith("\n") else ""))
print("variation_ops", d["version"])
