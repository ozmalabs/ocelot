#!/usr/bin/env python3
"""comprehension_health v1.1.0 (2026-10-10, conversation turn ring): the
history rules read the SHAPE, not every Message.

Only the last N turns stay attended (seeds/conversation_turn_ring.json, the
reading aperture applied to turns).
  * note_recurring_speech_act_divergence: the recurrence of a shallow/deep
    reader disagreement is held as a TurnShape{shape_kind:'divergence',
    sig_comp_kind, sig_shadow_speech_act}. `tally_divergence_class` folds each
    attended disagreeing turn into it; the note rule fires on the shape's
    oldest member once it has 3 members (first_member, marked by
    mark_divergence_shape_first_member right after the tally, so one rule
    pass folds, marks and files), with the same concern, content and
    about_message as before (v1.0: the class's earliest turn by shadow_seq,
    counted over all Messages).
  * note_comprehension_latency_gap: "m is the newest shadow-read turn" was a
    scan over every Message; it is now m.shadow_seq == agent.latest_shadow_seq,
    a datum the adapter writes next to the counter
    (WorldAdapter._record_shadow_health).
The rule objects are replaced in place; the rest of the hand-formatted seed
is untouched. Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/comprehension_health.json"
VERSION = "1.1.0"


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or0(x): return {"type": "IfThenElse", "cond": Eq(x, L(None)), "then": L(""), "other": x}


text = P.read_text()
d = json.loads(text)
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)
rules = {r["name"]: r for r in d["rules"]}

old_div = rules["note_recurring_speech_act_divergence"]
concern_guard = old_div["where"]["items"][-1]          # no SelfConcern with this exact content
assert concern_guard["type"] == "Not" and "SelfConcern" in json.dumps(concern_guard)
TALLY = {
    "name": "tally_divergence_class",
    "comment": "Fold an attended shallow/deep reader disagreement into its class TurnShape (the conceptual tier the recurrence rule reads).",
    "match": [["agent", "received", "m"]],
    "where": And(Eq(A("m", "speech_act_divergence"), L(1.0)),
                 Not(Eq(A("m", "divergence_tallied"), L(1)))),
    "effects": [
        ["add_node_if_absent", "sh", "TurnShape", {
            "shape_kind": "divergence",
            "sig_comp_kind": {"__term__": Or0(A("m", "comp_kind"))},
            "sig_shadow_speech_act": {"__term__": Or0(A("m", "shadow_speech_act"))}}],
        ["add_edge", "agent", "has_turn_shape", "sh"],
        ["add_edge", "sh", "has_member", "m"],
        ["add_edge", "m", "member_of", "sh"],
        ["set_attr", "m", "divergence_tallied", 1]],
}
new_div = dict(old_div)
FIRST = {
    "name": "mark_divergence_shape_first_member",
    "comment": "The oldest member of a divergence TurnShape is its first_member (the turn the concern names), marked while that turn is attended; loaded right after the tally so one pass folds, marks and files.",
    "match": [["agent", "received", "m"], ["m", "member_of", "sh"]],
    "where": And(
        Eq(A("sh", "shape_kind"), L("divergence")),
        Not({"type": "Exists", "source": {"type": "Neighbours", "node": V("sh"), "edge_type": "first_member"},
             "var_name": "_f", "predicate": L(True)}),
        Eq(V("m"), {"type": "Argmin", "source": {"type": "Neighbours", "node": V("sh"), "edge_type": "has_member"},
                    "var_name": "x", "value": V("x"), "default": None})),
    "effects": [["add_edge", "sh", "first_member", "m"]],
}
new_div["match"] = [["agent", "has_turn_shape", "sh"], ["sh", "first_member", "m"]]
new_div["where"] = And(
    Eq(A("sh", "shape_kind"), L("divergence")),
    Eq(A("m", "speech_act_divergence"), L(1.0)),
    Not(Eq(A("m", "divergence_health_noted"), L(1.0))),
    {"type": "Gte", "a": {"type": "Count", "source": {"type": "Neighbours", "node": V("sh"), "edge_type": "has_member"}},
     "b": L(3.0)},
    concern_guard)

old_lat = rules["note_comprehension_latency_gap"]
items = old_lat["where"]["items"]
scan = items[-1]
assert scan["type"] == "Not" and '"node_type": "Message"' in json.dumps(scan)
new_lat = dict(old_lat)
new_lat["where"] = dict(old_lat["where"], items=items[:-1] + [
    Eq(A("m", "shadow_seq"), A("agent", "latest_shadow_seq"))])


def replace_rule(t, name, new_obj, extra_before=None):
    key = '"name": "%s"' % name
    k = t.index(key)
    start = t.rindex("{", 0, k)
    obj, end = json.JSONDecoder().raw_decode(t, start)
    assert obj["name"] == name
    indent = t[t.rindex("\n", 0, start) + 1:start]
    body = json.dumps(new_obj, indent=1, ensure_ascii=False).replace("\n", "\n" + indent)
    if extra_before is not None:
        body = "".join(json.dumps(x, indent=1, ensure_ascii=False).replace("\n", "\n" + indent)
                       + ",\n" + indent for x in extra_before) + body
    return t[:start] + body + t[end:]


text = replace_rule(text, "note_recurring_speech_act_divergence", new_div, extra_before=[TALLY, FIRST])
text = replace_rule(text, "note_comprehension_latency_gap", new_lat)
desc = json.dumps(d["description"], ensure_ascii=False)
assert desc in text
text = text.replace(desc, json.dumps(d["description"] + " || v1.1.0 (2026-10-10, conversation turn ring): "
                                     "the recurrence rule reads a TurnShape tally and its oldest member, and the latency rule "
                                     "compares with agent.latest_shadow_seq, instead of scanning every Message "
                                     "(scripts/gen_comprehension_health_shapes.py).", ensure_ascii=False), 1)
text = text.replace('"version": "%s"' % d["version"], '"version": "%s"' % VERSION, 1)
dep = json.dumps(d["depends_on"])
new_dep = json.dumps(d["depends_on"] + ["conversation_turn_ring"])
assert ('"depends_on": ' + dep) in text, dep
text = text.replace('"depends_on": ' + dep, '"depends_on": ' + new_dep, 1)
check = json.loads(text)
names = [r["name"] for r in check["rules"]]
k = names.index("tally_divergence_class")
assert check["version"] == VERSION and names[k:k + 3] == [
    "tally_divergence_class", "mark_divergence_shape_first_member", "note_recurring_speech_act_divergence"]
P.write_text(text)
print("comprehension_health", VERSION, [r["name"] for r in check["rules"]])
