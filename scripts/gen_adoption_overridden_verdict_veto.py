#!/usr/bin/env python3
"""adoption_safety v1.1.0: no adoption on a verdict the agent itself overrode.

`mark_adopt_ready_*` marks an Experiment adopt_ready as soon as the generic
judge writes outcome 'supported'. Family judges (seeds/self_optimisation.json,
e.g. judge_performance_experiment_outcome) can then OVERRIDE that outcome in
the same run_rules fixpoint. perform_adoptions only reads adopt_ready, so the
parent adopted a change its own final verdict had refuted. Measured in tranche
23's smoke run: an experiment ended adopted=True with outcome='refuted'.

Paper 02c (successor landscapes are present candidates): a revision is
authorised only by the present organisation's own conditions. A provisional
verdict that the present state has since contradicted is not that warrant.

`adopt_denied_on_overridden_verdict` vetoes adoption when adopt_ready is set,
the Experiment is not yet adopted, and its outcome is now something other
than 'supported'. An Experiment carrying no outcome at all is left alone.
Like adopt_denied_on_regression, it is a standing veto: the authored
mark_adopt_ready_* bodies stay byte-identical. Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/adoption_safety.json"
VERSION = "1.1.0"
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
    "name": "adopt_denied_on_overridden_verdict",
    "comment": ("adoption_safety v1.1.0: an adopt-ready Experiment whose final outcome is no longer "
                "'supported' (a family judge overrode the generic verdict) is never adopted."),
    "match": [["exp", "has_delta", "delta"]],
    "where": {"type": "And", "items": [
        Eq(A("exp", "adopt_ready"), L(True)),
        Not(Eq(A("exp", "adopted"), L(True))),
        Not(Eq(A("exp", "adopt_denied"), L(True))),
        Not(Eq(A("exp", "outcome"), L(None))),
        Not(Eq(A("exp", "outcome"), L("supported")))]},
    "effects": [
        ["set_attr", "exp", "adopt_denied", True],
        ["set_attr", "exp", "adopt_denied_reason",
         "the experiment was marked adopt-ready on a provisional 'supported' verdict that a later judge "
         "overrode: a change the agent's own final verdict does not support is never adopted"]]}
suffix = (" || v1.1.0 (2026-10-10): adopt_denied_on_overridden_verdict -- an adopt-ready "
          "Experiment whose outcome a family judge has since overridden away from 'supported' "
          "is vetoed (measured: tranche 23 smoke run, adopted=True with outcome='refuted'; "
          "scripts/gen_adoption_overridden_verdict_veto.py).")
# Textual splice: the seed is hand-formatted, so re-serialising it would churn
# every line. Version, description suffix, and the rule appended to `rules`.
text = P.read_text()
text = text.replace(f'"version": "{d["version"]}"', f'"version": "{VERSION}"', 1)
desc_json = json.dumps(d["description"], ensure_ascii=True)
assert desc_json in text, "description not found verbatim"
text = text.replace(desc_json, json.dumps(d["description"] + suffix, ensure_ascii=True), 1)
tail = "\n    }\n  ]\n}"
assert text.rstrip().endswith(tail.strip()) and text.rstrip()[-len(tail):] == tail, "unexpected seed tail"
body = text.rstrip()[:-len(tail)]
rule_txt = json.dumps(rule, indent=2, ensure_ascii=True).replace("\n", "\n    ")
text = body + "\n    },\n    " + rule_txt + "\n  ]\n}\n"
check = json.loads(text)
assert check["version"] == VERSION and check["rules"][-1]["name"] == rule["name"]
assert check["rules"][:-1] == d["rules"]
P.write_text(text)
print("adoption_safety", VERSION)
