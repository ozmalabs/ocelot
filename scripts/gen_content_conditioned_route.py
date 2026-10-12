#!/usr/bin/env python3
"""Tranche 7: CONTENT-CONDITIONED instruction routes.

A route Concept may carry `route_object_scope: "other"`: it then claims a turn
only when no mention of the message refers to the agent itself
(yourself/yourselves -- the same self-reference test
conversation_self_reply.instruction_self_report_identity uses). This lets one
verb hold two routes keyed on its object: "summarise the data" -> world_action,
"summarise yourself" -> self_report. Absent attr -> unconditioned (all held
verbs unchanged).

Applied textually to the two route-claiming rules in
seeds/comprehend_instruction.json (v2.4.0) to keep the hand-authored file
intact; idempotent.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "seeds/comprehend_instruction.json"
text = P.read_text()
DONE_CI = "route_object_scope" in text
SELF = {"type": "Exists", "source": {"type": "Neighbours", "node": {"type": "Var", "name": "m"}, "edge_type": "has_mention"},
        "var_name": "sm", "predicate": {"type": "Exists", "source": {"type": "Neighbours", "node": {"type": "Var", "name": "sm"},
        "edge_type": "refers_to"}, "var_name": "sc", "predicate": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "TypeOf", "node": {"type": "Var", "name": "sc"}}, "b": {"type": "Lit", "value": "Concept"}},
            {"type": "In", "member": {"type": "Attr", "node": {"type": "Var", "name": "sc"}, "key": "name"},
             "container": {"type": "Lit", "value": ["yourself", "yourselves"]}}]}}}
COND = {"type": "Or", "items": [
    {"type": "Not", "arg": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "vc"}, "key": "route_object_scope"},
                             "b": {"type": "Lit", "value": "other"}}},
    {"type": "Not", "arg": SELF}]}
n = 0
for route in (() if DONE_CI else ("comprehend_text", "world_action")):
    anchor = (' "key": "instruction_route"\n          },\n          "b": {\n           "type": "Lit",\n'
              f'           "value": "{route}"\n          }}\n         }}')
    assert text.count(anchor) == 1, (route, text.count(anchor))
    blob = json.dumps(COND, indent=1)
    ins = ",\n" + "\n".join("         " + ln for ln in blob.splitlines())
    text = text.replace(anchor, anchor + ins, 1); n += 1
text = text.replace('"version": "2.3.0"', '"version": "2.4.0"', 1)
text = text.replace('"_verbs_as_data_note": "v2.3.0', '"_verbs_as_data_note": "v2.4.0 (tranche 7): a route Concept with route_object_scope=\'other\' claims a turn only when no mention refers to the agent itself (content-conditioned route; absent -> unconditioned). v2.3.0', 1)
json.loads(text); P.write_text(text); print("patched", n, "rules; comprehend_instruction 2.4.0")

# instruction_understanding.iu_mint_candidate_interpretation must honour the
# same scope, else a scoped world_action Concept still mints an
# interpreted_instruction Goal for "summarise yourself" (measured: the self
# reply changed from the full self-report to "I am Jabberwock.").
IU = ROOT / "seeds/instruction_understanding.json"
iu = IU.read_text()
if "route_object_scope" not in iu:
    cond = json.loads(json.dumps(COND).replace('"name": "vc"', '"name": "predicate_concept"')
                      .replace('"name": "m"}, "edge_type": "has_mention"', '"name": "message"}, "edge_type": "has_mention"'))
    i = iu.index('"name": "iu_mint_candidate_interpretation"')
    key = '"key": "instruction_route"}, "b": {"type": "Lit", "value": "self_report"}}}'
    j = iu.index(key, i) + len(key)
    iu = iu[:j] + ", " + json.dumps(cond) + iu[j:]
    iu = iu.replace('"version": "1.0.0"', '"version": "1.1.0"', 1)
    json.loads(iu); IU.write_text(iu); print("instruction_understanding 1.1.0")
