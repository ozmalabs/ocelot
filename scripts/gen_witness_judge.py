#!/usr/bin/env python3
"""self_optimisation v1.7.0 (2026-10-10, plan P3b): DECLARED WITNESSES and one
generic judge replace the five family judges.

Until v1.6.0 every family that is judged on its own observable (not the
generic score sign) had its own judge rule: performance (replay turn ms vs a
baseline), knob (reform marks), rule literal (the picked rule's witness
fires), datum feedback (an interlocutor belief), shape mint (classified
parties). All five had the same shape: any regression refutes; otherwise the
variant's measure moved the declared way -> supported, unchanged ->
inconclusive, moved the other way -> refuted.

Now a SeedDelta DECLARES its witness:
  witness_kind          what is measured (latency / reforms / rule_witness_fires /
                        interlocutor_belief / classified_parties)
  witness_direction     'increase' | 'decrease' (which way supports)
  witness_control_attr  attr holding the control measure ...
  witness_control_on    ... on 'exp' or on 'delta' (latency's baseline is
                        stamped on the delta at dispatch)
  witness_variant_attr  attr on the Experiment holding the variant measure
and ONE rule, judge_declared_witness_outcome, reads the declaration.

The family -> witness mapping is graph data: one `declare_witness_<family>`
rule per family marker, each writing the declaration only when none is held
yet. They run before the judge, in the old judges' precedence (a family
witness beats the performance objective, as the later family judge used to
overwrite the performance verdict). A delta built by a future FamilyProgram
(plan P4) declares its witness directly and needs no marker. The verdict
matrix is pinned against the frozen v1.6.0 judges
(tests/fixtures/family_judges_self_optimisation_v1_6_0.json). Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/self_optimisation.json"
VERSION = "1.7.0"
OLD = ("judge_performance_experiment_outcome", "judge_knob_experiment_outcome",
       "judge_rule_literal_outcome", "judge_datum_feedback_outcome", "judge_shape_mint_outcome")


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def T(x): return {"__term__": x}
def NotNull(x): return Not(Eq(x, L(None)))
def ByName(n, key_term): return {"type": "AttrByName", "node": V(n), "name": key_term}


def declare(family, marker_where, kind, direction, control_attr, variant_attr, control_on="exp"):
    return {
        "name": "declare_witness_" + family,
        "comment": f"The {family} family's delta is judged on its own observable: declare it as the delta's witness.",
        "match": [["exp", "has_delta", "delta"]],
        "where": And(*marker_where, Eq(A("delta", "witness_kind"), L(None))),
        "effects": [
            ["set_attr", "delta", "witness_kind", kind],
            ["set_attr", "delta", "witness_direction", direction],
            ["set_attr", "delta", "witness_control_attr", control_attr],
            ["set_attr", "delta", "witness_control_on", control_on],
            ["set_attr", "delta", "witness_variant_attr", variant_attr]],
    }


def dir_from(attr):
    # the family's own direction attr: 'increase_fires' -> increase, else decrease
    return T(Ite(Eq(A("delta", attr), L("increase_fires")), L("increase"), L("decrease")))


DECLARES = [
    declare("knob", [Eq(A("delta", "knob_edit"), L(1.0))], "reforms", dir_from("knob_direction"),
            "control_reforms", "variant_reforms"),
    declare("rule_literal", [Eq(A("delta", "rule_literal_edit"), L(1.0))], "rule_witness_fires",
            dir_from("rule_literal_direction"), "control_witness_fires", "variant_witness_fires"),
    declare("datum_feedback", [Eq(A("delta", "datum_feedback_edit"), L(1.0))], "interlocutor_belief",
            "decrease", "control_belief", "variant_belief"),
    declare("shape_mint", [Eq(A("delta", "shape_mint_edit"), L(1.0))], "classified_parties",
            "increase", "control_belief", "variant_belief"),
    declare("performance", [Eq(A("delta", "performance_objective"), L(1.0)),
                            Not(Eq(A("delta", "deep_reader_edit"), L(1.0)))],
            "latency", "decrease", "baseline_avg_turn_ms", "avg_turn_ms", control_on="delta"),
]

CONTROL = Ite(Eq(A("delta", "witness_control_on"), L("delta")),
              ByName("delta", A("delta", "witness_control_attr")),
              ByName("exp", A("delta", "witness_control_attr")))
VARIANT = ByName("exp", A("delta", "witness_variant_attr"))
c, v = V("c"), V("v")
better = Ite(Eq(A("delta", "witness_direction"), L("increase")),
             {"type": "Gt", "a": v, "b": c}, {"type": "Lt", "a": v, "b": c})
VERDICT = {"type": "Let", "name": "c", "value": CONTROL, "body": {
    "type": "Let", "name": "v", "value": VARIANT, "body":
        Ite({"type": "Gt", "a": A("exp", "regressions"), "b": L(0)}, L("refuted"),
            Ite(better, L("supported"), Ite(Eq(v, c), L("inconclusive"), L("refuted"))))}}

JUDGE = {
    "name": "judge_declared_witness_outcome",
    "comment": ("The verdict for a delta that declares a witness: any regression refutes; otherwise the "
                "variant's measure moving the declared way supports, unchanged is inconclusive, the other "
                "way refutes. Overrides the generic score-sign verdict (same match-clause 'analysed' "
                "sequencing as the family judges it replaces)."),
    "match": [["exp", "has_delta", "delta"], ["exp", "analysed", "run"]],
    "where": And(
        NotNull(A("delta", "witness_kind")),
        Not(Eq(A("exp", "witness_judged"), L(True))),
        NotNull(CONTROL),
        NotNull(VARIANT)),
    "effects": [
        ["set_attr", "exp", "witness_judged", True],
        ["set_attr", "exp", "outcome", T(VERDICT)]],
}

d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)
names = [r["name"] for r in d["rules"]]
assert all(n in names for n in OLD), names
first = min(names.index(n) for n in OLD)
kept = [r for r in d["rules"] if r["name"] not in OLD]
insert_at = sum(1 for r in d["rules"][:first] if r["name"] not in OLD)
d["rules"] = kept[:insert_at] + DECLARES + [JUDGE] + kept[insert_at:]
d["version"] = VERSION
d["description"] += (" || v1.7.0 (2026-10-10, plan P3b): the five family judges (performance, knob, rule "
                     "literal, datum feedback, shape mint) are replaced by DECLARED WITNESSES -- a delta's "
                     "witness_kind / witness_direction / witness_control_attr / witness_variant_attr, written "
                     "by one declare_witness_<family> rule per family marker -- and one generic rule, "
                     "judge_declared_witness_outcome (scripts/gen_witness_judge.py). Same verdicts "
                     "(tests/test_witness_judge_migrated.py pins the matrix against the frozen v1.6.0 "
                     "judges); the per-family *_judged flags become witness_judged.")
P.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
print("self_optimisation", VERSION, [r["name"] for r in d["rules"]])
