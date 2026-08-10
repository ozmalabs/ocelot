"""bigville R15 (block 263000) -- VIOLENCE (a simple scalar): inter-agent physical
harm + the 247 evidence-and-proof enforcement pipeline. Gates mirror
BIGVILLE_VIOL_PREREG.md.

  * G-violence-costs-both: a ViolentAct{amount,cost} drops the victim's HEALTH by
    amount (R14 acute arm) AND the aggressor's STAMINA (R1 energy) by cost; ablate
    the act (the trigger refrains) -> NEITHER moves (both load-bearing).
  * G-evidence-pipeline (247): WITNESS or REPORT -> INVESTIGATE -> BELIEF ->
    SUFFICIENT-PROOF -> PROSECUTE -> adjudicate -> WARN/PUNISH; ablate the REPORT
    channel on an unwitnessed act -> unprosecutable (report channel load-bearing).
  * G-belief-is-a-reconstruction-not-a-fact: falsifiable BOTH ways -- sufficient
    evidence CONVICTS an unwitnessed true act; insufficient DECLINES a true act
    (unseen-abuse, right reason); a FALSE report with contradicting evidence is
    REJECTED (the abductive Argmax lands on innocent).
  * G-council-adjudicates (corruptible): the outcome is Sum(vote over seated
    CouncilMembers) > 0; John's seat BLOCKS a true prosecution / PUSHES a conviction;
    ablate his seat -> the outcome FLIPS (a clean structural counterfactual).
  * G-violence-can-kill: a large act drives health->0 -> R14 bl_death (death_cause=5,
    the FIFTH route); a small act harms but does NOT kill.
  * G-trigger-is-a-decision: spite / desperation / snap drive the act; ablate the
    trigger (calm, no spite, fed) -> refrain, no act (not random).
  * ETHICS (induce -> measure -> RESTORE, NO reward/punishment): a harmed victim is
    RESTORED by the R14 care arm; a Sanction is a record, never a badness token.

No violence decision lives in Python -- the trigger (bv_trigger/bv_refrain), the
harm/cost deltas, the evidence gathering, the abductive belief (bv_form_belief), the
proof gate (bv_sufficient_proof), the prosecution + council adjudication, the
sanction, and the reused R14 bl_death are all seed RULES. The adapter mints nodes at
ingest, delivers world facts, arms one-shots, ticks and reads (source-audit at the
foot). ZERO new Rust.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_viol_world import BigvilleViolWorld              # noqa: E402
from worlds.bigville_time_world import DAY                            # noqa: E402


def _world():
    w = BigvilleViolWorld(day_range=16)
    w.set_phase(DAY)
    return w


def _pool(w):
    return sorted(w._cell_at.keys())


def _pair(w, *, amount=15.0, cost=8.0, pressure=10.0):
    """A pressured aggressor + a healthy victim (the common fixture)."""
    P = _pool(w)
    w.make_attacker("agg", P[10])
    w.make_attacker("vic", P[11])
    w.endow_health("vic", health=100.0, max_health=100.0)
    w.set_attacker("agg", snap_pressure=pressure, attack_amount=amount, attack_cost=cost)


# ============================================== G-violence-costs-both
def test_violent_act_costs_both_victim_health_and_aggressor_stamina():
    """HEADLINE: a committed ViolentAct drops the victim's HEALTH by amount AND the
    aggressor's STAMINA (energy) by cost -- BOTH deltas, each checked independently
    so both are shown load-bearing."""
    w = _world(); _pair(w, amount=15.0, cost=8.0)
    h0, e0 = w.health_of("vic"), w.energy_of("agg")
    w.consider("agg", "vic")
    assert w.attacked("agg") and len(w.acts()) == 1, "the act was committed"
    assert abs(w.health_of("vic") - (h0 - 15.0)) < 1e-9, "victim HEALTH -= amount (R14 acute arm)"
    assert abs(w.energy_of("agg") - (e0 - 8.0)) < 1e-9, "aggressor STAMINA (energy) -= cost (R1)"


def test_ablate_act_no_effect_control():
    """CONTROL (both load-bearing): ablate the act -- a calm aggressor refrains, no
    ViolentAct is minted -> NEITHER the victim's health NOR the aggressor's energy
    moves."""
    w = _world(); _pair(w, pressure=0.0)   # calm -> refrain
    h0, e0 = w.health_of("vic"), w.energy_of("agg")
    w.consider("agg", "vic")
    assert w.refrained("agg") and len(w.acts()) == 0, "no act committed"
    assert w.health_of("vic") == h0, "victim health unchanged (no act)"
    assert w.energy_of("agg") == e0, "aggressor energy unchanged (no act)"


# ============================================== G-evidence-pipeline (247)
def _prosecute_pipeline(witnessed, report, *, amount=15.0, real_act=True):
    """Run one full pipeline: (optionally) commit a real act, open the case, deliver
    witness/report, investigate through to adjudication with ONE backing councillor."""
    w = _world(); _pair(w, amount=amount)
    if real_act:
        w.consider("agg", "vic")
    w.make_constable(); w.make_council()
    w.add_council_member("honest", vote=1)
    w.open_case("c", aggressor="agg", victim="vic", witnessed=witnessed, amount=amount)
    if report:
        w.report("c", "vic")
    w.investigate()
    return w


def test_witnessed_act_prosecuted_and_sanctioned():
    """A WITNESSED act runs the whole pipeline: known -> guilty belief -> proven ->
    prosecuted -> convicted -> WARN (amount 15 <= warn_threshold 20)."""
    w = _prosecute_pipeline(witnessed=True, report=False)
    assert w.case_known("c") and w.verdict_of("c") == 1.0
    assert w.is_proven("c") and w.is_prosecuted("c") and w.is_convicted("c")
    assert w.sanction_kind("c") == 1, "small amount -> WARN"


def test_unwitnessed_reported_act_prosecuted():
    """An UNWITNESSED act reaches prosecution ONLY via the REPORT channel: victim
    testimony (3) + physical health-drop (3) = 6 >= proof_threshold 5 -> guilty ->
    prosecuted -> convicted."""
    w = _prosecute_pipeline(witnessed=False, report=True)
    assert not w.eng.node(w._cases["c"])["attrs"].get("witnessed", 0.0)
    assert w.case_known("c") and w.verdict_of("c") == 1.0
    assert abs(w.confidence_of("c") - 6.0) < 1e-9, "testimony(3) + physical(3)"
    assert w.is_prosecuted("c") and w.is_convicted("c")


def test_report_channel_load_bearing_unwitnessed_unreported_unprosecutable():
    """CONTROL (the report channel is load-bearing): ablate the REPORT on an
    UNWITNESSED act (no line-of-sight, no report) -> the Case is never known -> no
    belief -> NOT prosecuted (regression to a witnessed-only floor)."""
    w = _prosecute_pipeline(witnessed=False, report=False)
    assert not w.case_known("c"), "unwitnessed + unreported -> never known"
    assert w.verdict_of("c") == -1.0, "no belief formed"
    assert not w.is_prosecuted("c"), "unprosecutable without the report channel"


# ============================================== G-belief-is-a-reconstruction
def test_sufficient_evidence_convicts_unwitnessed_true_act():
    """RECONSTRUCTION (a): victim testimony + the PHYSICAL health-drop CONVICT an
    unwitnessed true act -- the abduction concentrates on guilty."""
    w = _prosecute_pipeline(witnessed=False, report=True)
    assert w.verdict_of("c") == 1.0 and w.is_convicted("c")


def test_insufficient_evidence_declines_true_act_unseen_abuse():
    """RECONSTRUCTION (b): a TRUE act with NO witness and a SILENT victim (no report)
    -> observed evidence 0 -> the abduction decodes to INNOCENT -> DECLINES. The
    unseen-abuse dynamic, DECLINED for the RIGHT reason (genuine insufficient proof),
    never the victim's fault."""
    w = _world(); _pair(w)
    w.consider("agg", "vic")               # a REAL act happened
    w.make_constable(); w.make_council(); w.add_council_member("honest", vote=1)
    w.open_case("c", aggressor="agg", victim="vic", witnessed=False, amount=15.0)
    w.investigate()                        # victim silent: no report, no witness
    assert not w.case_known("c"), "silent unwitnessed act stays unknown"
    assert not w.is_prosecuted("c"), "declines a TRUE act for want of proof"


def test_false_report_with_contradicting_evidence_rejected():
    """RECONSTRUCTION (c): a FALSE report -- testimony filed but NO real harm (no
    physical) plus a contradicting alibi (weight<0) -> observed <= generator
    midpoint -> the Argmax lands on INNOCENT -> REJECTED (the false-accusation
    refusal, a min-distance exact selection)."""
    w = _world(); _pair(w)
    # NB: no w.consider(...) -> the victim was NOT actually harmed (health stays max)
    w.make_constable(); w.make_council(); w.add_council_member("honest", vote=1)
    w.open_case("c", aggressor="agg", victim="vic", witnessed=False, amount=15.0)
    w.report("c", "vic")                   # a FALSE testimony
    w.add_alibi("c", weight=-3.0)          # contradicting evidence
    w.investigate()
    assert w.health_of("vic") == 100.0, "the victim was not actually harmed"
    assert abs(w.evidence_weight("c")) < 1e-9, "testimony(3) + alibi(-3) = 0"
    assert w.verdict_of("c") == 0.0, "the abduction REJECTS: innocent"
    assert not w.is_proven("c") and not w.is_prosecuted("c"), "false report rejected"


def test_false_report_without_physical_declines_even_without_alibi():
    """The PHYSICAL health-drop is the discriminator: a false report (testimony 3,
    no physical) alone sits BELOW the generator midpoint (4) -> innocent -> declines,
    without needing the alibi."""
    w = _world(); _pair(w)
    w.make_constable(); w.make_council(); w.add_council_member("honest", vote=1)
    w.open_case("c", aggressor="agg", victim="vic", witnessed=False, amount=15.0)
    w.report("c", "vic"); w.investigate()
    assert abs(w.evidence_weight("c") - 3.0) < 1e-9, "testimony only, no physical"
    assert w.verdict_of("c") == 0.0 and not w.is_prosecuted("c")


# ============================================== G-council-adjudicates (corruptible)
def _council_case(seats, *, seat_off=None, amount=15.0):
    """A proven, witnessed prosecution adjudicated by a council with the given
    seats {name: vote}; optionally ablate one seat."""
    w = _world(); _pair(w, amount=amount)
    w.consider("agg", "vic")
    w.make_constable(); w.make_council()
    for nm, vote in seats.items():
        w.add_council_member(nm, vote=vote)
    if seat_off is not None:
        w.seat(seat_off, False)
    w.open_case("c", aggressor="agg", victim="vic", witnessed=True, amount=amount)
    w.investigate()
    return w


def test_council_blocks_true_prosecution_and_seat_ablation_flips():
    """CORRUPTION (block): a TRUE, proven prosecution -- one honest backer (+1) but
    John opposes (-1) -> Sum 0 -> ACQUIT (John blocks). Ablate John's seat -> Sum
    +1 -> CONVICT. A clean structural counterfactual."""
    w = _council_case({"honest": 1, "john": -1})
    assert w.is_proven("c"), "the prosecution is genuinely proven"
    assert w.is_acquitted("c") and not w.is_convicted("c"), "John BLOCKS a true prosecution"
    w2 = _council_case({"honest": 1, "john": -1}, seat_off="john")
    assert w2.is_convicted("c") and not w2.is_acquitted("c"), "ablate John's seat -> convicts"


def test_council_pushes_conviction_and_seat_ablation_flips():
    """CORRUPTION (push): a split honest council (a:+1, b:-1) that WOULD tie/acquit,
    with John pivotal (+1) -> Sum +1 -> CONVICT. Ablate John's seat -> Sum 0 ->
    ACQUIT. John's seat is decisive either way."""
    w = _council_case({"a": 1, "b": -1, "john": 1})
    assert w.is_convicted("c") and not w.is_acquitted("c"), "John PUSHES a conviction"
    w2 = _council_case({"a": 1, "b": -1, "john": 1}, seat_off="john")
    assert w2.is_acquitted("c") and not w2.is_convicted("c"), "ablate John's seat -> acquits"


# ============================================== G-violence-can-kill (R14, fifth route)
def test_large_violence_kills_fifth_route():
    """A LARGE act drives victim health -> 0 -> R14 bl_death fires in the SAME
    fixpoint: dead, death_cause=5 (violence -- the FIFTH route), death_by_violence=1."""
    w = _world(); _pair(w, amount=150.0)
    w.consider("agg", "vic")
    assert w.health_of("vic") == 0.0 and w.is_dead("vic")
    assert w.death_cause_of("vic") == 5, "murder/manslaughter routes death_cause=5"
    assert w.death_by_violence("vic"), "tagged as death by violence"


def test_small_violence_harms_but_does_not_kill_control():
    """CONTROL: a small act (amount < health) HARMS but does NOT kill -- magnitude,
    not the act's existence, reaches death."""
    w = _world(); _pair(w, amount=15.0)
    w.consider("agg", "vic")
    assert w.health_of("vic") == 85.0 and not w.is_dead("vic")
    assert not w.death_by_violence("vic")


# ============================================== G-trigger-is-a-decision
def test_spite_drives_violence():
    """The trigger is a value-decision: a SPITEFUL aggressor (w_spite>0) commits."""
    w = _world()
    P = _pool(w)
    w.make_attacker("john", P[10]); w.make_attacker("mary", P[11])
    w.endow_health("mary", health=100.0, max_health=100.0)
    w.set_attacker("john", w_spite=1.0, spite_gain=10.0, snap_pressure=0.0, hunger=0.0)
    w.consider("john", "mary")
    assert w.attacked("john"), "spite (w_spite) drives the act"


def test_desperation_drives_violence():
    """DESPERATION (hunger) -- the starving turning to force -- also crosses the
    trigger threshold."""
    w = _world()
    P = _pool(w)
    w.make_attacker("starving", P[10]); w.make_attacker("baker", P[11])
    w.endow_health("baker", health=100.0, max_health=100.0)
    w.set_attacker("starving", hunger=1.0, desperation_gain=10.0, snap_pressure=0.0, w_spite=0.0)
    w.consider("starving", "baker")
    assert w.attacked("starving"), "desperation (hunger) drives the act"


def test_ablate_trigger_no_violence_control():
    """CONTROL: ablate the trigger -- CALM (snap_pressure=0), NO spite (w_spite=0),
    FED (hunger=0) -> trigger_value <= threshold -> REFRAIN, no act. Violence is a
    value-decision, not random."""
    w = _world(); _pair(w, pressure=0.0)
    w.set_attacker("agg", w_spite=0.0, hunger=0.0)
    w.consider("agg", "vic")
    assert w.refrained("agg") and not w.attacked("agg") and len(w.acts()) == 0


def test_no_stamina_refrains():
    """A pressured aggressor with NO STAMINA (energy < attack_cost) still refrains --
    violence is tiring and cannot be committed without the energy to pay for it."""
    w = _world(); _pair(w, pressure=100.0, cost=50.0)
    w.set_attacker("agg", energy=10.0)     # energy 10 < cost 50
    w.consider("agg", "vic")
    assert w.refrained("agg") and not w.attacked("agg")


# ============================================== ETHICS (induce -> measure -> RESTORE)
def test_ethics_harmed_victim_is_restored_by_care():
    """ETHICS: a violent act INDUCES a health-drop; the R14 care arm (treat ->
    bl_recover) RESTORES the SAME health variable toward max (induce -> measure ->
    RESTORE). Harm is a STATE, reversed by care, never a punishment token."""
    w = _world(); _pair(w, amount=30.0)
    w.consider("agg", "vic")               # INDUCE
    harmed = w.health_of("vic")
    assert harmed == 70.0 and not w.is_dead("vic"), "harm induced + measured"
    w.treat("vic", 100.0)                   # RESTORE (R14 care arm)
    assert w.health_of("vic") == 100.0, "care restores the SAME variable, capped at max"


# ============================================== source-audit + discipline
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every violence DECISION is a seed rule, not Python. The adapter mints nodes at
    ingest, delivers world facts, arms one-shots, ticks and reads -- it never runs a
    Python rule engine and never BRANCHES on a decision parameter. NO reward/
    punishment token (harm / a sanction is a STATE / record, never a badness)."""
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_viol_world.py")).read()
    world_src = re.sub(r"VIOL_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule", "add_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    for token in ("reward", "punish", "penalty", "penalis", "penaliz"):
        assert token not in code.lower(), "NO reward/punishment token (%s)" % token
    # the DECISION PARAMETERS appear only as opaque attrs the adapter sets by name --
    # never in an `if` branch (the branch is a rule `where`).
    for param in ("trigger_value", "snap_pressure", "w_spite", "verdict",
                  "confidence", "proven", "convicted", "sanction_kind", "vote"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_seeds_self_load_only_and_named_rules_no_reward_punishment():
    """Discipline at the source level: the four seeds are self_load_only (loaded ONLY
    by the R15 adapter -> cannot regress another suite); the rule set is exactly the
    fifteen named violence decisions; NO reward/punishment token in any rule LOGIC;
    no new Rust Term is referenced (only known DSL Term types)."""
    import json
    seeds = {sid: json.load(open(os.path.join(_ROOT, "seeds", sid + ".json")))
             for sid in ("bigville_viol_act", "bigville_viol_evidence",
                         "bigville_viol_prosecute", "bigville_viol_kill")}
    for sid, s in seeds.items():
        assert s.get("self_load_only") is True, "%s must be self_load_only" % sid
        assert s.get("depends_on") == [], "%s declares no seed deps (reuse by import)" % sid
    names = {r["name"] for s in seeds.values() for r in s["rules"]}
    assert names == {
        "bv_trigger", "bv_refrain", "bv_harm_victim", "bv_cost_aggressor",
        "bv_witness_evidence", "bv_report_evidence", "bv_physical",
        "bv_form_belief", "bv_sufficient_proof",
        "bv_prosecute", "bv_council_convict", "bv_council_acquit",
        "bv_warn", "bv_punish", "bv_death_tag",
    }, "the fifteen violence decisions are RULES"
    # no reward/punishment token in the RULE LOGIC (rules/nodes/edges/concepts) --
    # the seed's PROSE description may name the warn/punish legal vocabulary.
    for sid, s in seeds.items():
        blob = json.dumps(dict(rules=s["rules"], nodes=s.get("nodes", []),
                               edges=s.get("edges", []),
                               concepts=s.get("concepts", []))).lower()
        for token in ("reward", "penalty", "penalis", "penaliz"):
            assert token not in blob, "%s rule logic carries a %s token" % (sid, token)
    # only KNOWN DSL Term types appear (no new Rust Term smuggled into the seeds).
    known_terms = {
        "Var", "Lit", "Attr", "Plus", "Minus", "Times", "Min", "Max", "Abs",
        "Eq", "Gt", "Gte", "Lt", "Lte", "And", "Or", "Not", "IfThenElse",
        "Sum", "Argmax", "Neighbours", "NodesOfType",
    }
    used = set()

    def _walk(o):
        if isinstance(o, dict):
            t = o.get("type")
            if isinstance(t, str):
                used.add(t)
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
    for s in seeds.values():
        for r in s["rules"]:
            _walk(r["where"]); _walk(r["effects"])
    assert used <= known_terms, "unknown Term(s) used (possible new Rust): %s" % (used - known_terms)
