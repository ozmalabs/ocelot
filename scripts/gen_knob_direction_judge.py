#!/usr/bin/env python3
"""Tranche 8: knob_edit POLARITY. seeds/self_optimisation.json v1.3.0:
judge_knob_experiment_outcome reads the delta's `knob_direction`.
  increase_fires -> supported iff variant_reforms > control_reforms
  otherwise (decrease_fires, or absent: the pre-tranche-8 behaviour)
                 -> supported iff variant_reforms < control_reforms
equal -> inconclusive; any regression or the wrong-way move -> refuted.
The builder (_compose_knob_variant) scores the concern content against the
agent's held direction lexicon (VariationOp rule_literal_edit
direction_lexicon_more/_fewer) and steps the knob down for increase_fires.
Idempotent; preserves the file's indent=1 / no-trailing-newline format."""
import json
from pathlib import Path
P = Path(__file__).resolve().parents[1] / "seeds/self_optimisation.json"
d = json.loads(P.read_text())
r = [r for r in d["rules"] if r["name"] == "judge_knob_experiment_outcome"][0]
if d["version"] == "1.3.0":
    print("already applied"); raise SystemExit(0)
A = lambda n, k: {"type": "Attr", "node": {"type": "Var", "name": n}, "key": k}
L = lambda v: {"type": "Lit", "value": v}
V, C = A("exp", "variant_reforms"), A("exp", "control_reforms")
INC = {"type": "Eq", "a": A("delta", "knob_direction"), "b": L("increase_fires")}
better = {"type": "IfThenElse", "cond": INC, "then": {"type": "Gt", "a": V, "b": C}, "other": {"type": "Lt", "a": V, "b": C}}
outcome = {"type": "IfThenElse", "cond": {"type": "Gt", "a": A("exp", "regressions"), "b": L(0)}, "then": L("refuted"),
           "other": {"type": "IfThenElse", "cond": better, "then": L("supported"),
                     "other": {"type": "IfThenElse", "cond": {"type": "Eq", "a": V, "b": C}, "then": L("inconclusive"), "other": L("refuted")}}}
done = False
for e in r["effects"]:
    if e[0] == "set_attr" and e[2] == "outcome":
        e[3] = {"__term__": outcome}; done = True
assert done
r["comment"] = (r.get("comment") or "") + (" v1.3.0 (tranche 8): direction-aware -- delta.knob_direction=='increase_fires' "
               "supports MORE reform marks (the concern said the reform fires too rarely); absent/decrease_fires keeps the fewer-supports verdict.")
d["version"] = "1.3.0"
P.write_text(json.dumps(d, indent=1, ensure_ascii=True)); print("self_optimisation 1.3.0")
