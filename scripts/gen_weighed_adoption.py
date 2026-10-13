#!/usr/bin/env python3
"""Plan P5c (2026-10-10): EVERYTHING IS WEIGHED. Patches two frozen seeds by
human decision ("regression is only relative to the frame").

Until now the adoption gate held two absolute vetoes:
  adoption_safety v1.0  adopt_denied_on_regression    regressions > 0 -> never
  adoption_safety v1.2  adopt_denied_on_quality_drop  any quality drop -> never
and the declared-witness judge refuted on any regression. A "regression" was
any unflagged reply that changed. The child (scripts/convo_child_run.py) now
reports a change in the frame it is measured in: worse (a regression), better
(improved_changes) or lateral (lateral_changes: same quality, different text,
which the frame cannot tell apart).

seeds/adoption_safety.json v1.3.0
  * AdoptionWeighing{fix_weight, gain_weight, harm_weight, lateral_weight,
    min_net}: the exchange rates, held as data;
  * weighed net = fix_weight * flagged fixes + gain_weight * improved - harm_weight * regressions (incl.
    broken fixes) - lateral_weight * lateral;
  * adopt_weighed_net records it on every Experiment whose child reported
    (ingest time, as the regression veto did -- no race with adoption);
    adopt_denied_on_weighed_net denies one below min_net. A delta with a
    declared witness is weighed by its own judge instead. The two absolute
    vetoes are removed; adopt_denied_on_overridden_verdict (a verdict
    consistency check, not a harm rule) stays.
seeds/self_optimisation.json v1.8.0
  * judge_declared_witness_outcome: the measure moving the declared way
    supports only if the same weighed net (the witness move counting as one
    fix) reaches min_net; outweighed by harm it refutes. Without an
    AdoptionWeighing node the old rule holds (any regression refutes).
Idempotent.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AS = ROOT / "seeds/adoption_safety.json"
SO = ROOT / "seeds/self_optimisation.json"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def NN(x): return Not(Eq(x, L(None)))
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def T(x): return {"__term__": x}
def Let(n, v, b): return {"type": "Let", "name": n, "value": v, "body": b}


W = {"type": "Argmin", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "AdoptionWeighing"},
                                  "var_name": "w", "predicate": L(True)}, "var_name": "_x", "value": L(0), "default": None}


def n0(x): return Ite(Eq(x, L(None)), L(0), x)


def weighed(benefit):
    """fix*benefit + gain*improved - harm*regressions - lateral*lateral, with W bound to 'aw'."""
    return Minus(Plus(Times(A("aw", "fix_weight"), benefit), Times(A("aw", "gain_weight"), n0(A("exp", "improved_changes")))),
                 Plus(Times(A("aw", "harm_weight"), n0(A("exp", "regressions"))),
                      Times(A("aw", "lateral_weight"), n0(A("exp", "lateral_changes")))))


# Weighed at INGEST TIME, like the regression veto it replaces: every input
# (fixes, regressions, lateral, improved) is on the Experiment before any rule
# runs, so the denial cannot race perform_adoptions. A delta that DECLARES a
# witness is weighed by its own judge instead (judge_declared_witness_outcome
# below counts the witness move as the fix), and an overridden verdict is
# denied by adopt_denied_on_overridden_verdict.
BENEFIT = n0(A("exp", "flagged_changed"))
NET = Let("aw", W, weighed(BENEFIT))
READY = And(NN(A("exp", "regressions")), NN(W), Eq(A("delta", "witness_kind"), L(None)),
            Not(Eq(A("exp", "adopted"), L(True))), Not(Eq(A("exp", "adopt_denied"), L(True))))
MATCH = [["exp", "has_delta", "delta"]]

WEIGHING_NODE = {"local_id": 0, "type": "AdoptionWeighing", "attrs": {
    "name": "adoption_weighing", "fix_weight": 1.0, "gain_weight": 0.5, "harm_weight": 1.5,
    "lateral_weight": 0.25, "min_net": 1.0,
    "description": "The exchange rates the adoption gate weighs a trial by (plan P5c): a fixed flagged turn (or a "
                   "declared witness moving the right way) is worth fix_weight; an unflagged turn made better "
                   "gain_weight; a turn made worse in the quality frame, or a broken fix, costs harm_weight; a "
                   "lateral change (same quality, different text -- the frame cannot see it) costs lateral_weight. "
                   "A trial is adopted only if its net reaches min_net."}}

RECORD = {"name": "adopt_weighed_net",
          "comment": "P5c: every judged conversation trial carries its weighed net (inspectable).",
          "match": MATCH, "where": READY,
          "effects": [["set_attr_if_different", "exp", "weighed_net", T(NET)]]}
DENY = {"name": "adopt_denied_on_weighed_net",
        "comment": "P5c: a trial whose weighed net is below min_net is not adopted -- harm is weighed against what "
                   "the trial fixed, not vetoed by its mere presence.",
        "match": MATCH, "where": And(READY, Lt(NET, A(W, "min_net"))),
        "effects": [["set_attr", "exp", "adopt_denied", True],
                    ["set_attr", "exp", "adopt_denied_reason",
                     "the trial's weighed net (fixes and improvements against regressions and lateral changes, "
                     "seeds/adoption_safety.json AdoptionWeighing) is below the minimum"]]}

d = json.loads(AS.read_text())
if d["version"] != "1.3.0" or "--force" in __import__("sys").argv:
    assert d["version"] in ("1.2.0", "1.3.0"), d["version"]
    d["rules"] = [r for r in d["rules"] if r["name"] not in ("adopt_denied_on_regression", "adopt_denied_on_quality_drop",
                                                             "adopt_weighed_net", "adopt_denied_on_weighed_net")]
    d["rules"] = [RECORD, DENY] + d["rules"]
    d["nodes"] = [WEIGHING_NODE]
    d["version"] = "1.3.0"
    d["microtheory"]["description"] = ("a trial is adopted when what it fixes outweighs what it harms, in the "
                                       "frame it is measured in; the exchange rates are held as data")
    if "v1.3.0 (2026-10-10" not in d["description"]:
        d["description"] += (" || v1.3.0 (2026-10-10, plan P5c, human decision: everything is weighed): the absolute "
                             "regression and quality-drop vetoes are replaced by a weighed net over the child's "
                             "frame-relative report (fixes, improved, regressions = worse in the quality frame or "
                             "now failing, lateral = same quality, different text) with AdoptionWeighing exchange "
                             "rates (scripts/gen_weighed_adoption.py).")
    AS.write_text(json.dumps(d, indent=2) + "\n")

s = json.loads(SO.read_text())
if s["version"] != "1.8.0":
    assert s["version"] == "1.7.0", s["version"]
    j = next(r for r in s["rules"] if r["name"] == "judge_declared_witness_outcome")
    verdict = j["effects"][1][3]["__term__"]          # Let c / Let v / Ite(regressions > 0, refuted, ...)
    inner = verdict["body"]["body"]
    old_reg, by_measure = inner["cond"], inner["other"]
    better = by_measure["cond"]
    weighed_verdict = Let("aw", W, Ite(
        Eq(V("aw"), L(None)),
        inner,                                        # no exchange rates held: the v1.7.0 rule
        Ite(better,
            Ite(Gte(weighed(L(1)), A("aw", "min_net")), L("supported"), L("refuted")),
            by_measure["other"])))
    verdict["body"]["body"] = weighed_verdict
    j["comment"] = ("The verdict for a delta that declares a witness: the variant's measure moving the declared way "
                    "supports unless the trial's harm outweighs it (seeds/adoption_safety.json AdoptionWeighing; "
                    "the move counts as one fix); unchanged is inconclusive, the other way refutes. v1.8.0 (P5c): "
                    "a regression is weighed, not an automatic refutation.")
    s["version"] = "1.8.0"
    s["description"] += (" || v1.8.0 (2026-10-10, plan P5c): judge_declared_witness_outcome weighs the trial's "
                         "regressions and lateral changes against the witness move (scripts/gen_weighed_adoption.py).")
    SO.write_text(json.dumps(s, indent=1) + "\n")
print("adoption_safety", json.loads(AS.read_text())["version"], "self_optimisation", json.loads(SO.read_text())["version"])
