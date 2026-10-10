#!/usr/bin/env python3
"""variation_ops v1.18.0 (tranche 20): ROUTE CREDIT in cue_route_pick -- the
improver learns, from its own judged experiments, which route tends to fix an
unrouted verb, and that experience transfers to the NEXT verb.

cue_route_pick Argmaxes route-carrying Concepts by character-bigram overlap
with the gap verb (a spelling similarity; it carries no outcome information),
and excludes routes already refuted for the SAME verb. So every new verb starts
from scratch: measured on the endemic stream (tranche 20 smoke), the first
pick was refuted for 3 of 4 verbs, and the second route then worked.

Opt-in VariationOp{cue_set_edit}.route_credit == 1 makes the candidate value

    100 * (supported(route) + 1) / (judged(route) + 2)  +  bigram(candidate)

Here judged(route) and supported(route) count the agent's own SeedDeltas with
that cue_route whose Experiment reached a verdict (supported, refuted or
inconclusive), and whose verdict was supported. This is the same
Laplace-smoothed outcome credit the family-level VariationCredit uses
(tranche 8), one level down (route instead of family) and keyed by route
across all verbs. With no history every route scores 50, so the pick is
exactly the bigram pick: decision-equivalent at zero experience. Absent or 0
leaves the Program's choice byte-identical. Idempotent.

DEFAULT ON (route_credit = 1): the preregistered endemic-RSI gate E3
(docs/research/engine_substrate/SUBSTRATE_ENDEMIC_RSI_V1_PREREG_20261010.md)
passed in run v1.1. Over the second half of a natural 51-request stream, the
agent spent 1.00 experiments per self-fixed verb with route credit against
1.29 without it (21 vs 15 first-try fixes, 21 fixes each).
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/variation_ops.json"
VERSION = "1.18.0"
d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}


prog_node = next(n for n in d["nodes"] if n["type"] == "Program" and n["attrs"].get("name") == "cue_route_pick")
prog = json.loads(prog_node["attrs"]["program"])
best_let = prog["other"]["body"]
assert best_let["type"] == "Let" and best_let["name"] == "best"
argmax = best_let["value"]
assert argmax["type"] == "Argmax" and argmax["var_name"] == "c"
bigram = argmax["value"]


def judged(route, outcomes):
    return {"type": "Count", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "SeedDelta"},
                                        "var_name": "cd", "predicate": {"type": "And", "items": [
        {"type": "Eq", "a": A("cd", "cue_route"), "b": route},
        {"type": "Exists", "source": {"type": "InNeighbours", "node": V("cd"), "edge_type": "has_delta"},
         "var_name": "cx", "predicate": {"type": "In", "member": A("cx", "outcome"), "container": L(outcomes)}}]}}}


route = A("c", "instruction_route")
credit = {"type": "Div",
          "a": {"type": "Plus", "items": [judged(route, ["supported"]), L(1)]},
          "b": {"type": "Plus", "items": [judged(route, ["supported", "refuted", "inconclusive"]), L(2)]}}
op = {"type": "Argmin", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "VariationOp"},
                                   "var_name": "v", "predicate": {"type": "Eq", "a": A("v", "name"), "b": L("cue_set_edit")}},
      "var_name": "x", "value": L(0), "default": None}
argmax["value"] = {"type": "IfThenElse",
                   "cond": {"type": "Eq", "a": V("route_credit_on"), "b": L(1)},
                   "then": {"type": "Plus", "items": [{"type": "Times", "items": [credit, L(100)]}, bigram]},
                   "other": bigram}
prog["other"]["body"] = {"type": "Let", "name": "route_credit_on",
                         "value": {"type": "Attr", "node": op, "key": "route_credit"}, "body": best_let}
prog_node["attrs"]["program"] = json.dumps(prog)
for n in d["nodes"]:
    if n["type"] == "VariationOp" and n["attrs"].get("name") == "cue_set_edit":
        n["attrs"]["route_credit"] = 1    # default ON: preregistered gate E3 passed (endemic RSI v1.1)
d["description"] += (" v1.18.0 (2026-10-10, tranche 20): opt-in VariationOp{cue_set_edit}.route_credit==1 ranks "
                     "cue_route_pick candidates by the Laplace-smoothed success rate of their route over the agent's own "
                     "judged cue experiments (all verbs), plus the bigram score as tie-break -- experience fixing one "
                     "verb orders the next verb's attempt (scripts/gen_cue_route_credit.py). 0/absent -> unchanged. "
                     "Default 1: the preregistered endemic-RSI gate E3 passed (tranche 20).")
d["version"] = VERSION
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("variation_ops", VERSION)
