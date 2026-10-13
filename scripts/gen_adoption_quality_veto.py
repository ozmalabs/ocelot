#!/usr/bin/env python3
"""adoption_safety v1.2.0 (2026-10-10, plan P1 judge v2): no adoption that
makes any replayed turn's reply quality worse.

The dispatched conversation child scores every probe's reply on both passes
with ReplyQuality (domains/reply_quality.py: 0 inappropriate, 1 acceptable-
minimal, 2 appropriate) and reports `quality_drops` (turns whose quality fell)
and `quality_delta` (variant mean minus control mean); ingest copies both onto
the Experiment. Gate Q0 found the measure agrees with labels (kappa 0.94;
the labels came from blind sub-agent labellers, not humans --
docs/research/engine_substrate/OPEN_ENDED_P1_JUDGE_V2_RESULTS_20261010.md).

`adopt_denied_on_quality_drop` vetoes adoption when quality_drops > 0 or
quality_delta < 0. An Experiment with no quality report (an ARC child, a
pre-P0 record) is left alone: both attrs must be present. Like the other two
vetoes it is a standing rule, and it names the Experiment type, so it is
self-improvement-loop machinery the loop cannot vary
(seeds/improvement_integrity.json). Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/adoption_safety.json"
VERSION = "1.2.0"
d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}


rule = {
    "name": "adopt_denied_on_quality_drop",
    "comment": "Judge v2 (plan P1): a variant that lowers any replayed turn's reply quality, or the mean, is never adopted.",
    "match": [["exp", "has_delta", "delta"]],
    "where": {"type": "And", "items": [
        Not(Eq(A("exp", "quality_drops"), L(None))),
        Not(Eq(A("exp", "quality_delta"), L(None))),
        {"type": "Or", "items": [
            {"type": "Gt", "a": A("exp", "quality_drops"), "b": L(0)},
            {"type": "Lt", "a": A("exp", "quality_delta"), "b": L(0.0)}]},
        Not(Eq(A("exp", "adopt_denied"), L(True)))]},
    "effects": [
        ["set_attr", "exp", "adopt_denied", True],
        ["set_attr", "exp", "adopt_denied_reason",
         "judge v2: the dispatched child reported a reply-quality drop (quality_drops > 0 or "
         "quality_delta < 0): a variant that makes a reply worse is never adopted"]],
}
assert rule["name"] not in [r["name"] for r in d["rules"]]
# textual edit: the seed is hand-formatted, keep every other byte
text = P.read_text()
last = d["rules"][-1]["name"]
k = text.index('"name": "%s"' % last)
start = text.rindex("{", 0, k)
_obj, end = json.JSONDecoder().raw_decode(text, start)
indent = text[text.rindex("\n", 0, start) + 1:start]
body = json.dumps(rule, indent=2, ensure_ascii=False).replace("\n", "\n" + indent)
text = text[:end] + ",\n" + indent + body + text[end:]
desc = json.dumps(d["description"], ensure_ascii=False)
assert desc in text
text = text.replace(desc, json.dumps(d["description"] + (
    " || v1.2.0 (2026-10-10, plan P1 judge v2): adopt_denied_on_quality_drop vetoes adoption when the "
    "child's ReplyQuality report shows any turn's quality fell or the mean fell "
    "(scripts/gen_adoption_quality_veto.py)."), ensure_ascii=False), 1)
text = text.replace('"version": "%s"' % d["version"], '"version": "%s"' % VERSION, 1)
check = json.loads(text)
assert check["version"] == VERSION and [r["name"] for r in check["rules"]][-1] == rule["name"]
P.write_text(text)
print("adoption_safety", VERSION, [r["name"] for r in check["rules"]])
