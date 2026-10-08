#!/usr/bin/env python3
"""Tranche 5: a REPEATED unhandled instruction gets an honest reply.

Measured: on a fresh full-seed agent, "Condense the data." twice -> first
"... I've filed it as a gap", second "ERROR: no communicative response could
be generated." note_unhandled_instruction_gap is deduped on the existing
SelfConcern (correct: one concern), but that also suppressed its reply, so
the turn fell through to the adapter's error surface. This also made the
paired-control replay of every flagged instruction turn an error, so the
corrected judge could not attribute a broken fix to the delta.

Adds `reply_known_instruction_gap` to seeds/gap_awareness.json (v1.9.0):
identical guards to note_unhandled_instruction_gap except it fires when the
SelfConcern for this predicate+content ALREADY exists; it files nothing new
and replies that the gap is already filed. Inserted textually so the
hand-authored file's formatting is preserved; idempotent.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "seeds/gap_awareness.json"
text = P.read_text(); d = json.loads(text)
if any(r["name"] == "reply_known_instruction_gap" for r in d["rules"]):
    print("already present"); raise SystemExit(0)
base = next(r for r in d["rules"] if r["name"] == "note_unhandled_instruction_gap")
where = json.loads(json.dumps(base["where"]))
last = where["items"][-1]
assert last["type"] == "Not" and last["arg"]["type"] == "Exists" and last["arg"]["source"]["node_type"] == "SelfConcern"
where["items"][-1] = last["arg"]
V = lambda n: {"type": "Var", "name": n}
A = lambda n, k: {"type": "Attr", "node": V(n), "key": k}
L = lambda v: {"type": "Lit", "value": v}
rule = {
    "name": "reply_known_instruction_gap",
    "comment": ("A REPEATED unhandled instruction whose gap is already filed: same guards as "
                "note_unhandled_instruction_gap, but the matching SelfConcern exists, so nothing new is filed; "
                "reply honestly that the gap is already filed (tranche 5; the dedup previously left the turn with "
                "no reply and the adapter error surface)."),
    "match": base["match"], "where": where,
    "effects": [
        ["set_attr", "m", "instruction_gap_noted", 1.0],
        ["set_attr", "m", "self_improvement_route", "filed_concern"],
        ["set_attr", "m", "comprehended", 1.0],
        ["add_node", "reply", "Message", {"from": "agent", "text": {"__term__": {"type": "StringConcat", "parts": [
            L("I still hold no faculty to "), A("m", "comp_predicate"), L(" '"), A("m", "comp_content"),
            L("' -- that gap is already filed for me to work on.")]}}}],
        ["add_edge", "reply", "responds_to", "m"],
        ["add_edge", "agent", "sent", "reply"],
    ],
}
# insert right after the base rule's JSON object, at the base rule's indentation
blob = json.dumps(rule, indent=2, ensure_ascii=True)
i = text.index('"name": "note_unhandled_instruction_gap"')
start = text.rfind("{", 0, i); line_start = text.rfind("\n", 0, start) + 1
indent = text[line_start:start]
depth, j = 0, start
while True:
    c = text[j]
    if c == '"':
        j += 1
        while text[j] != '"':
            j += 2 if text[j] == "\\" else 1
    elif c == "{": depth += 1
    elif c == "}":
        depth -= 1
        if depth == 0: break
    j += 1
ins = ",\n" + "\n".join(indent + ln for ln in blob.splitlines())
out = text[:j + 1] + ins + text[j + 1:]
out = out.replace('"version": "1.8.0"', '"version": "1.9.0"', 1)
json.loads(out)
P.write_text(out)
print("inserted reply_known_instruction_gap; gap_awareness 1.9.0")
