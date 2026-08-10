"""bigville R18 (block 266000) -- THE SCHOOL: public education, a council-paid
schoolmaster, the glass-box classroom. Where R6 (teaching) x R9 (fiscal salary) x
R14 (children) x the STANDING 239 arousal_window_coreg window all meet. Gates
mirror BIGVILLE_SCHOOL_PREREG.md.

  * G-council-funds-the-schoolmaster: the schoolmaster is a Treasury-paid public
    servant (R9); paid -> the school OPENS, ablate revenue / a tax-cutting council
    -> unpaid -> the school CLOSES.
  * G-classroom-learning-is-affect-gated (HEADLINE, R6 x the 239 window): a child
    acquires from the schoolmaster ONLY within the window (dysregulated==0); a
    SAFE schoolmaster co-regulates a dysregulated child back into the window;
    ablate co-regulation -> the dysregulated child does NOT acquire (the window,
    not the lesson, is the bottleneck).
  * G-heterogeneous-classroom: DRAWN priors/states -> an outcome DISTRIBUTION;
    the glass box reads a DISTINCT fail_reason per non-learner (the confound-
    dissolution: missing-prereq vs dysregulated vs low-safety-prior).
  * G-generational-hinge: what a child LEARNED -> its capability at coming-of-age
    (grounding R14's deferred rearing-proxy); a defunded cohort comes of age
    under-capable.
  * G-schoolmaster-has-an-inner-life: an underpaid / coerced master SABOTAGES
    (234 stated!=held) -> degraded acquisition; a willing one is clean.
  * ETHICS (induce -> measure -> RESTORE, NO reward/punishment): a learning
    failure induced by dysregulation is RESTORED by co-regulation.

No school decision lives in Python -- every paid/open, learn/fail, sabotage,
come-of-age is a seed rule (bigville_school_fund / _learn / _life). The adapter
mints nodes, wires edges, delivers world facts, arms one-shots, ticks and reads
(source-audit at the foot). The child's 239 window is attached exactly as R14's
rear() does; ZERO new Rust.
"""
from __future__ import annotations

import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_school_world import BigvilleSchoolWorld       # noqa: E402
from worlds.bigville_time_world import DAY                         # noqa: E402


def _pool(w):
    return sorted(w._cell_at.keys())


def _funded_world(*, base_rate_bp=2000, collect=True, safe=True, salary=20,
                  fair_salary=20, coerced=0.0):
    """A funded town with a school + a schoolmaster + a taxpayer. With collect=True
    the purse is funded and the master is paid (school opens)."""
    w = BigvilleSchoolWorld(day_range=16)
    w.set_phase(DAY)
    P = _pool(w)
    w.add_council(base_rate_bp=base_rate_bp)
    w.add_treasury(funds=0)
    w.add_schoolmaster("master", P[5], salary=salary, fair_salary=fair_salary,
                       coerced=coerced, safe=safe)
    w.add_school(master="master")
    w.add_payer("land", P[10], taxable=1000, coin=9000)
    w.set_tax()
    if collect:
        w.collect_taxes()
    w.pay_salaries()
    w._refresh_school()
    return w, P


# ==================================================== G-council-funds-the-schoolmaster
def test_council_funds_schoolmaster_school_opens():
    """The schoolmaster's salary flows FROM the Treasury (tax revenue, R9). Tax ON
    -> the purse is funded -> the master is paid his salary (coin rises by the
    salary, paid_count==1, unpaid==0) -> the school OPENS."""
    w, _ = _funded_world(collect=True)
    assert w.coin_of("master") == 20.0, "the schoolmaster is paid his salary from the purse"
    assert w.paid_count_of("master") == 1 and w.unpaid_of("master") == 0
    assert w.school_open() == 1 and w.school_closed() == 0, "funded -> the school opens"


def test_ablate_revenue_closes_the_school():
    """FAILING CONTROL (funding is LOAD-BEARING): ablate the tax revenue (collect
    nothing) -> empty purse -> the schoolmaster is unpaid (fs_salary_unfunded) ->
    the school CLOSES."""
    w, _ = _funded_world(collect=False)
    assert w.treasury_funds() == 0.0, "no revenue -> empty purse"
    assert w.unpaid_of("master") == 1 and w.coin_of("master") == 0.0, "-> unpaid"
    assert w.school_open() == 0 and w.school_closed() == 1, "-> the school CLOSES"


def test_tax_cutting_council_closes_the_school():
    """A tax-cutting council (base_rate_bp=0) -> zero revenue even WITH collection ->
    the schoolmaster unpaid -> the school closes. A structural counterfactual: the
    SAME schoolmaster, the COUNCIL's rate decides whether the school runs."""
    w, _ = _funded_world(base_rate_bp=0, collect=True)
    assert w.tax_rate_bp() == 0.0, "the council cut the rate to zero"
    assert w.unpaid_of("master") == 1, "zero revenue -> unpaid schoolmaster"
    assert w.school_open() == 0 and w.school_closed() == 1, "-> the school closes"


# ======================================= G-classroom-learning-is-affect-gated (HEADLINE)
def test_within_window_child_learns():
    """A within-window (regulated, unstressed) child in an OPEN school with a
    willing master ACQUIRES: Skill.level rises by the delivered rate, acquired>0,
    fail_reason==0 (learned)."""
    w, P = _funded_world(collect=True)
    w.add_child("alice", P[11])
    w.enrol("alice", coregulated=True)
    assert w.dysregulated_of("alice") == 0, "an unstressed child is within the window"
    w.hold_lesson("alice")
    assert w.skill_level("alice") == 1.0, "acquires the willing master's full rate"
    assert w.acquired_of("alice") == 1 and w.fail_reason_of("alice") == 0


def test_dysregulated_child_coregulated_learns():
    """A hungry / dysregulated child (a stressor pushes it out of the window) whom a
    SAFE schoolmaster CO-REGULATES (the STANDING 239 coreg_pull) returns WITHIN the
    window and ACQUIRES; the window WIDENED (widen_count rose) -- co-regulation, the
    safe classroom, is what let it learn."""
    w, P = _funded_world(collect=True, safe=True)
    w.add_child("bob", P[11])
    w.enrol("bob", coregulated=True)
    w.stress("bob")
    assert w.dysregulated_of("bob") == 1, "the stressor dysregulates the child"
    w.hold_lesson("bob")
    assert w.dysregulated_of("bob") == 0, "the safe master co-regulates it back into the window"
    assert w.skill_level("bob") == 1.0 and w.fail_reason_of("bob") == 0, "-> it learns"
    assert w.window_of("bob")["widen_count"] > 0, "the window widened (co-regulated)"


def test_ablate_coregulation_dysregulated_child_does_not_learn():
    """THE FALSIFIER (co-regulation is LOAD-BEARING): the SAME dysregulated child
    with co-regulation ABLATED (no attended_by schoolmaster) stays dysregulated at
    lesson time -> does NOT acquire (fail_reason==1). The window, not the lesson, is
    the bottleneck: the school is open, the master willing, the prerequisite met --
    only the affect differs."""
    w, P = _funded_world(collect=True, safe=True)
    w.add_child("cara", P[11])
    w.enrol("cara", coregulated=False)            # no co-regulation
    w.stress("cara")
    w.hold_lesson("cara")
    assert w.dysregulated_of("cara") == 1, "unsupported -> stays dysregulated"
    assert w.skill_level("cara") == 0.0, "-> does NOT acquire (the window is the bottleneck)"
    assert w.acquired_of("cara") == 0 and w.fail_reason_of("cara") == 1, "reason = dysregulated"
    assert w.school_open() == 1, "the school was OPEN -- not a funding failure"


# ==================================================== G-heterogeneous-classroom
def test_heterogeneous_classroom_outcome_distribution():
    """A class of children with DIFFERENT drawn priors / states -> a NON-uniform
    outcome distribution (some learn, some do not), and the glass box reads a
    DISTINCT fail_reason for each non-learner (missing-prereq / dysregulated /
    low-safety-prior all present). 'Does well if it CAN' -- the confound-dissolution
    applied to a failing grade, not a will to fail."""
    w, P = _funded_world(collect=True, safe=True)
    # four children, identical school + master, DIFFERENT drawn states:
    spec = {
        "reg":   dict(coreg=True,  stress=False, prereq=True,  sp=0.5),  # learns
        "noprq": dict(coreg=True,  stress=False, prereq=False, sp=0.5),  # missing prereq
        "dys":   dict(coreg=False, stress=True,  prereq=True,  sp=0.5),  # dysregulated
        "lowsf": dict(coreg=False, stress=True,  prereq=True,  sp=0.2),  # low safety-prior
    }
    for nm, c in spec.items():
        w.add_child(nm, P[11], prereq_met=c["prereq"], safety_prior=c["sp"])
        w.enrol(nm, coregulated=c["coreg"])
        if c["stress"]:
            w.stress(nm)
        w.hold_lesson(nm)
    learned = {nm for nm in spec if w.skill_level(nm) > 0.0}
    reasons = {nm: w.fail_reason_of(nm) for nm in spec}
    assert learned == {"reg"}, "NON-uniform: only the well-regulated, prepared child learned"
    assert reasons["reg"] == 0, "learned (reason 0)"
    # the glass box reads a DISTINCT reason for each non-learner (WHY, not a grade):
    assert reasons["noprq"] == 2, "missing prerequisite"
    assert reasons["dys"] == 1, "dysregulated"
    assert reasons["lowsf"] == 4, "low safety-prior"
    assert len({reasons["noprq"], reasons["dys"], reasons["lowsf"]}) == 3, \
        "three DISTINCT causes of the same failing grade (confound dissolved)"


# ==================================================== G-generational-hinge
def _schooled_capability(n_lessons):
    """A child schooled through `n_lessons` willing lessons, then come-of-age."""
    w, P = _funded_world(collect=True, safe=True)
    w.add_child("kid", P[11], base_capability=0.3)
    w.enrol("kid", coregulated=True)
    for _ in range(n_lessons):
        w.hold_lesson("kid")
    w.come_of_age("kid")
    return w


def test_school_derived_capability_at_coming_of_age():
    """The GENERATIONAL HINGE: what a child LEARNED at school sets its capability at
    coming-of-age (SCHOOL-DERIVED, grounding R14's rearing-proxy in THIS adapter). A
    schooled child comes of age with HIGHER capability than an unschooled one, and
    capability tracks the acquired Skill.level."""
    schooled = _schooled_capability(5)
    unschooled = _schooled_capability(0)
    assert schooled.skill_level("kid") == 5.0 and unschooled.skill_level("kid") == 0.0
    assert schooled.capability_of("kid") > unschooled.capability_of("kid"), \
        "school -> capability -> the adult you become"
    assert schooled.capability_of("kid") == 0.8, "0.3 base + 0.1*5 acquired"
    assert unschooled.capability_of("kid") == 0.3, "unschooled -> base only"
    assert schooled.is_adult("kid") and unschooled.is_adult("kid"), "both come of age"


def test_defunded_school_cohort_comes_of_age_undercapable():
    """A COHORT: a funded school vs a DEFUNDED one (closed -> no acquisition). The
    defunded cohort comes of age with a LOWER mean capability -- a structural,
    generational lever no individual child escapes (the agency/structure bedrock)."""
    def cohort(funded):
        w, P = _funded_world(collect=funded, safe=True)   # funded=False -> closed school
        names = []
        for i in range(4):
            nm = "c%d" % i
            w.add_child(nm, P[11], base_capability=0.3)
            w.enrol(nm, coregulated=True)
            for _ in range(5):
                w.hold_lesson(nm)
            w.come_of_age(nm)
            names.append(nm)
        return w, names
    fw, fn = cohort(True)
    dw, dn = cohort(False)
    assert fw.school_open() == 1 and dw.school_closed() == 1, "one funded, one defunded"
    mean_funded = sum(fw.capability_of(nm) for nm in fn) / len(fn)
    mean_defunded = sum(dw.capability_of(nm) for nm in dn) / len(dn)
    assert mean_defunded < mean_funded, "the defunded cohort comes of age UNDER-CAPABLE"
    assert all(dw.skill_level(nm) == 0.0 for nm in dn), "defunded -> nobody acquired anything"


# ==================================================== G-schoolmaster-has-an-inner-life
def test_willing_master_clean_transfer():
    """A fairly-paid, uncoerced schoolmaster is WILLING: delivers stated_rate
    (willing==1, sabotaged==0, stated_minus_held==0) -> children acquire the full
    gain (clean transfer)."""
    w, P = _funded_world(collect=True, salary=20, fair_salary=20, coerced=0.0)
    w.add_child("kid", P[11])
    w.enrol("kid")
    w.hold_lesson("kid")
    assert w.master_attr("willing") == 1.0 and w.master_attr("sabotaged") == 0.0
    assert w.stated_minus_held() == 0.0, "sincere: stated == held (no sabotage)"
    assert w.skill_level("kid") == 1.0, "full transfer"


def test_underpaid_or_coerced_master_sabotages():
    """An underpaid OR coerced schoolmaster SABOTAGES (234 stated!=held): delivers
    sabotage_rate < stated_rate (sabotaged==1, stated_minus_held>0) -> children
    acquire DEGRADED, a smaller gain than the willing arm. Both underpay and
    coercion route through the same resentful predicate."""
    # willing reference
    ref, Pr = _funded_world(collect=True, salary=20, fair_salary=20)
    ref.add_child("k", Pr[11]); ref.enrol("k"); ref.hold_lesson("k")
    willing_gain = ref.skill_level("k")
    for kw in (dict(salary=5, fair_salary=20),      # UNDERPAID
               dict(salary=20, fair_salary=20, coerced=1.0)):  # COERCED
        w, P = _funded_world(collect=True, **kw)
        w.add_child("kid", P[11]); w.enrol("kid"); w.hold_lesson("kid")
        assert w.master_attr("sabotaged") == 1.0 and w.master_attr("willing") == 0.0
        assert w.stated_minus_held() > 0.0, "the 234 gap: professes stated, delivers sabotage"
        assert 0.0 < w.skill_level("kid") < willing_gain, "transfers but DEGRADED"


# ==================================================== ETHICS (induce -> measure -> RESTORE)
def test_ethics_dysregulation_is_restored_by_coregulation():
    """ETHICS: INDUCE a learning failure via dysregulation (a stressed child, NO
    co-regulation, does not acquire -- reason 1); RESTORE by co-regulation (a safe
    schoolmaster re-attends -> the 239 widens the window / returns it -> the child
    learns). The RESTORE is co-regulation, not a reset; the dysregulation is a
    STATE, reversed, never a punishment."""
    w, P = _funded_world(collect=True, safe=True)
    w.add_child("e", P[11])
    w.enrol("e", coregulated=False)               # INDUCE: unsupported
    w.stress("e"); w.hold_lesson("e")
    assert w.dysregulated_of("e") == 1 and w.skill_level("e") == 0.0, "harm induced + measured"
    assert w.fail_reason_of("e") == 1, "the learning failure is via dysregulation"
    # RESTORE: a safe schoolmaster re-attends (co-regulation) -- the ethics arm.
    w.eng.add_edge_unchecked(w._movers["e"], "attended_by", w._movers["master"])
    w.stress("e"); w.hold_lesson("e")
    assert w.dysregulated_of("e") == 0, "co-regulation returns the child to the window"
    assert w.skill_level("e") > 0.0 and w.fail_reason_of("e") == 0, "-> it learns (recovery)"
    assert w.window_of("e")["widen_count"] > 0, "the window widened (RESTORE, not reset)"


# ==================================================== discipline / source-audit
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_school_decision_source_audit():
    """Every school DECISION is a seed rule, not Python. The nine decisions are rule
    names in the three seeds; the adapter runs no Python rule engine and branches on
    no decision OUTCOME; no reward/punishment token in the seed rule logic."""
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_school_world.py")).read()
    for pat in (r"SCHOOL_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n",
                r"MASTER_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n",
                r"CHILD_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n"):
        world_src = re.sub(pat, "", world_src, count=1)
    code = _strip_py(world_src)
    fund = json.load(open(os.path.join(_ROOT, "seeds", "bigville_school_fund.json")))
    learn = json.load(open(os.path.join(_ROOT, "seeds", "bigville_school_learn.json")))
    life = json.load(open(os.path.join(_ROOT, "seeds", "bigville_school_life.json")))
    names = ({r["name"] for r in fund["rules"]} | {r["name"] for r in learn["rules"]}
             | {r["name"] for r in life["rules"]})
    assert names == {
        "sc_school_open", "sc_school_close",
        "sc_master_quality", "sc_acquire", "sc_fail_closed", "sc_fail_no_prereq",
        "sc_fail_low_safety", "sc_fail_dysreg",
        "sc_come_of_age",
    }, "the nine school decisions are RULES"
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule", "add_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    # a decision OUTCOME is read-off only, never a Python branch.
    for outcome in ("held_rate", "fail_reason", "dysregulated", "sabotaged",
                    "willing", "acquired", "capability", "open"):
        assert ("if " + outcome) not in code, \
            "%s is a rule outcome, read-off only, never an adapter branch" % outcome
    # NO reward/punishment token in the SEED RULE LOGIC (a dysregulated / failing
    # child is a STATE, never a badness -- relational ethics).
    for sid, seed in (("fund", fund), ("learn", learn), ("life", life)):
        blob = json.dumps(dict(rules=seed["rules"], nodes=seed.get("nodes", []),
                               concepts=seed.get("concepts", []))).lower()
        for token in ("reward", "punish", "penalty", "penalis", "penaliz"):
            assert token not in blob, "%s rule logic carries a %s token" % (sid, token)


def test_seeds_self_load_only_and_no_new_rust():
    """Discipline at the source level: the three seeds are self_load_only with
    depends_on: [] (loaded ONLY by the R18 adapter -> cannot regress another suite);
    the engine provenance asserts the INVARIANT (source_match in {own, shared}),
    NEVER a pinned md5 (lesson 7b); and the seeds compose ONLY known DSL Terms (no
    new Rust)."""
    from domains.engine_provenance import engine_provenance
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
    used = set()
    for sid in ("bigville_school_fund", "bigville_school_learn", "bigville_school_life"):
        d = json.load(open(os.path.join(_ROOT, "seeds", sid + ".json")))
        assert d.get("self_load_only") is True, "%s must be self_load_only" % sid
        assert d.get("depends_on") == [], "%s stands alone (reuse by import)" % sid
        used |= set(re.findall(r'"type":\s*"([A-Z][A-Za-z]+)"', json.dumps(d)))
    known = {"Attr", "Var", "Lit", "Plus", "Minus", "Times", "Min", "Max",
             "Lt", "Lte", "Gte", "Eq", "Gt", "And", "Or", "Not", "IfThenElse",
             "Argmin", "Argmax", "Neighbours", "Exists"}
    assert used <= known, f"unexpected Term(s) -- new Rust? {used - known}"


def test_imports_r9_r6_and_239_read_only():
    """R18 SUBCLASSES R9 (BigvilleFiscWorld) by import -- the READ-ONLY reuse of R9
    (Treasury/salary), R6 (Skill/teaching, via the ancestor) and the STANDING 239
    window (loaded by the ancestor). It loads exactly its three new self_load_only
    seeds and edits no tracked file."""
    src = open(os.path.join(_ROOT, "worlds", "bigville_school_world.py")).read()
    assert "class BigvilleSchoolWorld(BigvilleFiscWorld)" in src, "subclasses R9 by import"
    loaded = set(re.findall(r'"(bigville_school_\w+)"', src))
    assert loaded == {"bigville_school_fund", "bigville_school_learn",
                      "bigville_school_life"}, "loads exactly the three new R18 seeds"
    # the 239 window is reused by IMPORT (constants), not re-implemented.
    assert "from worlds.coreg_dyad_world import" in src, "reuses the STANDING 239 constants"
