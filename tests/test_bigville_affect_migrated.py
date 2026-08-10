"""bigville R17 (block 265000) -- AFFECT CLOSES THE LOOP: felt grief changes
behaviour, and the failure modes are reachable. Gates mirror BIGVILLE_AFFECT_PREREG.md
and the spec sec0 capstone ("AFFECT MUST CLOSE THE LOOP -- FELT, NOT REGISTERED").

  * G-affect-modulates-decision (HEADLINE): grief is a TERM in the decision_value
    Argmax -- a grieving agent and a content one in the SAME situation pick DIFFERENT
    actions (content -> work; grieving -> withdraw/drink/snap by severity). The
    FALSIFIER is the affect-blind control: ablate affect_gain -> identical choices
    under grief and contentment = the proven DIORAMA. Passes ONLY if behaviour diverges.
  * G-negative-spiral: grief -> worse decision -> worse outcome (income down) -> more
    grief; REACHABLE + ENDOGENOUS (falls out of the coupling). Ablate -> no spiral.
  * G-escapable-by-co-regulation (recovery = ethics arm): the SAME spiral with support
    (the reused 239000 co-regulation) BENDS -- window widens, regulation rises, work
    reachable, recovery. Breakdown vs recovery is a MEASURED function of support.
  * G-affect-propagates (generational): a grief-narrowed parent can't co-regulate the
    child (239000) -> the child's window narrows -> the child's adult priors shift down
    (R14). Ablate the coupling -> no cross-generation transfer.
  * ETHICS: felt grief is a harm-analog; every induction binds induce->measure->RESTORE
    and the RESTORE is co-regulation, not a reset; NO reward/punishment token anywhere.

No decision lives in Python -- the action choice, the outcome, the hardship feedback,
the regulation read, the caregiving contagion, and every reused 239000/R14 rule is a
seed rule. The adapter mints nodes at ingest, delivers world facts, arms one-shots,
ticks and reads (source-audit at the foot). ZERO new Rust.
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

from worlds.bigville_affect_world import BigvilleAffectWorld           # noqa: E402
from worlds.bigville_time_world import DAY                             # noqa: E402

_SEEDS = ("bigville_affect_grief", "bigville_affect_decide",
          "bigville_affect_spiral", "bigville_affect_coreg",
          "bigville_affect_propagate")


def _world(day_range=24):
    w = BigvilleAffectWorld(day_range=day_range)
    w.set_phase(DAY)
    return w


def _pool(w):
    return sorted(w._cell_at.keys())


# ============================================ G-affect-modulates-decision (HEADLINE)
def test_affect_modulates_decision_headline():
    """HEADLINE: two persons in the SAME situation (identical Action menu) -- one
    GRIEVING (high grief_distress), one CONTENT -- pick DIFFERENT actions. Grief is a
    TERM in the decision_value Argmax, so the content one chooses work and the
    grieving one does NOT (it withdraws / self-medicates / snaps). If a grieving agent
    made the same choice as a content one, the grief would be NARRATION."""
    w = _world()
    P = _pool(w)
    w.make_villager("content", P[10])                     # grief_distress = 0
    w.make_villager("griever", P[11])
    w.set_affect("griever", grief_distress=8.0)           # severe grief
    a_content = w.decide("content")
    a_griever = w.decide("griever")
    assert a_content == 1, "a CONTENT agent works (base_value wins): %s" % w.chosen_label_of("content")
    assert a_griever != 1, "a GRIEVING agent does NOT work -- grief shifted the choice"
    assert a_content != a_griever, "felt grief MEASURABLY changes the chosen action"


def test_affect_blind_ablation_is_the_diorama():
    """THE FALSIFIER (the affect-blind control): ablate the affect->decision_value
    coupling (affect_gain=0) and re-run -- grief no longer enters the Argmax, so the
    grieving agent and the content agent make the IDENTICAL choice (work). That is the
    proven DIORAMA; the gate would FAIL if the rung looked like this. It does not: the
    ONLY difference from the headline is affect_gain, and it flips divergence to
    identity -- proving the divergence above was the coupling, not a confound."""
    w = _world()
    P = _pool(w)
    w.make_villager("content", P[10], affect_gain=0.0)
    w.make_villager("griever", P[11], affect_gain=0.0)
    w.set_affect("griever", grief_distress=8.0)
    assert w.decide("content") == w.decide("griever") == 1, (
        "affect-blind: grief and contentment pick the SAME action (work) = DIORAMA")


def test_grief_escalates_graded_withdraw_drink_snap():
    """Under coupling, the chosen action ESCALATES with distress along the already-built
    behavioural sinks: content -> work; mild grief -> WITHDRAWAL (R7 income spiral);
    more -> SELF-MEDICATION (drink); severe -> a lowered SNAP threshold (R15 violence
    reachable). The Argmax crosses each boundary as eff_distress climbs."""
    w = _world()
    P = _pool(w)
    expect = {0.0: 1, 4.0: 2, 6.0: 3, 8.0: 4}   # work / withdraw / drink / snap
    for i, (d, code) in enumerate(sorted(expect.items())):
        nm = "g%d" % i
        w.make_villager(nm, P[10 + i])
        w.set_affect(nm, grief_distress=d)
        assert w.decide(nm) == code, (
            "distress %.0f should choose %s, got %s"
            % (d, {1: "work", 2: "withdraw", 3: "drink", 4: "snap"}[code],
               w.chosen_label_of(nm)))


def test_three_grief_sources_from_imported_rungs():
    """Grief is source-AGNOSTIC (grief is grief): a DEATH (R14 bereavement -- a REAL
    just_died kin), a FAILED DREAM (R8), a FORECLOSURE (R7) each raise grief_distress
    through the SAME af_grief_from_loss and each shift the decision. The bereavement
    arm rides an ACTUAL R14 death (bl_death fires)."""
    w = _world()
    P = _pool(w)
    # R14 bereavement -- a real death drives the mourner's grief.
    w.make_villager("mourner", P[10]); w.make_villager("kin", P[11])
    w.endow_health("kin", health=50.0)
    w.bereave_by_death("mourner", "kin", 8.0, cause=2.0)
    assert w.is_dead("kin"), "the kin actually DIED (R14 bl_death)"
    assert w.grief_of("mourner") == 8.0 and w.decide("mourner") != 1, "bereavement grieves + shifts"
    # R8 failed dream.
    w.make_villager("dreamer", P[12]); w.suffer_failed_dream("dreamer", 6.0)
    assert w.grief_of("dreamer") == 6.0 and w.decide("dreamer") == 3, "failed dream -> drink"
    # R7 foreclosure.
    w.make_villager("evicted", P[13]); w.suffer_foreclosure("evicted", 4.0)
    assert w.grief_of("evicted") == 4.0 and w.decide("evicted") == 2, "foreclosure -> withdraw"


# ================================================== G-negative-spiral (endogenous)
def test_negative_spiral_reachable_and_endogenous():
    """The failure mode that makes it REAL: grief -> worse decision -> worse outcome
    (income down) -> more grief. Over live-periods the coupled agent's grief RISES and
    the action ESCALATES to snap; coin FALLS. The CONTROL (affect_gain=0, SAME initial
    loss) works every period, coin RISES, grief DECAYS to 0 -- no spiral. The spiral is
    ENDOGENOUS: nothing scripts it; ablating the coupling removes it."""
    w = _world()
    P = _pool(w)
    w.make_villager("coupled", P[10], coin=3.0)
    w.make_villager("blind", P[40], coin=3.0, affect_gain=0.0)
    w.suffer_failed_dream("coupled", 6.0)
    w.suffer_failed_dream("blind", 6.0)
    assert w.grief_of("coupled") == w.grief_of("blind") == 6.0, "same initial loss"
    for _ in range(6):
        w.live_period("coupled")
        w.live_period("blind")
    # coupled: grief climbed, coin fell, escalated to snap (R15 reachable).
    assert w.grief_of("coupled") > 6.0, "coupled grief SPIRALED UP (%.1f)" % w.grief_of("coupled")
    assert w.coin_of("coupled") < 3.0, "coupled income FELL (%.1f)" % w.coin_of("coupled")
    assert w.chosen_label_of("coupled") == "snap", "coupled escalated to snap"
    assert w.conflict_of("coupled") > 0.0, "snapping produced conflict (R15 violence reachable)"
    # blind: no spiral -- ablation is load-bearing.
    assert w.grief_of("blind") < 6.0, "affect-blind grief DECAYED (%.1f) -- no spiral" % w.grief_of("blind")
    assert w.coin_of("blind") > 3.0, "affect-blind income ROSE (worked every period)"
    assert w.chosen_label_of("blind") == "work"


# ============================================ G-escapable-by-co-regulation (RESTORE)
def test_escapable_by_coregulation_recovery_vs_breakdown():
    """The recovery arm = the ethics arm. Two agents with the IDENTICAL loss + one
    spiral step: one receives co-regulation (the reused 239000 rules widen its window),
    the other faces it ALONE (the window narrows). Support -> regulation up -> the
    regulated choice (work) reachable -> RECOVERY; no support -> BREAKDOWN. The outcome
    is a MEASURED function of support presence ('does well if it can'), and the RESTORE
    is co-regulation, NEVER a reset (the window widens through the dynamics)."""
    w = _world(day_range=28)
    P = _pool(w)
    for nm, cell in (("sup", P[10]), ("alone", P[60])):
        w.make_villager(nm, cell, coin=3.0)
        w.suffer_failed_dream(nm, 6.0)
        w.live_period(nm)                       # one shared spiral step
    assert w.grief_of("sup") == w.grief_of("alone"), "identical pre-intervention state"
    reg_sup = w.support("sup", episodes=10)     # co-regulation (RESTORE, not reset)
    reg_alone = w.stress_alone("alone", episodes=10)
    assert reg_sup > reg_alone, "co-regulation raised regulation (%.2f > %.2f)" % (reg_sup, reg_alone)
    for _ in range(5):
        w.live_period("sup")
        w.live_period("alone")
    assert w.grief_of("sup") < w.grief_of("alone"), (
        "supported RECOVERS, alone BREAKS DOWN: %.1f < %.1f"
        % (w.grief_of("sup"), w.grief_of("alone")))
    assert w.chosen_label_of("sup") == "work", "the regulated choice became reachable again"
    assert w.chosen_label_of("alone") == "snap", "unsupported ran to breakdown"


# ==================================================== G-affect-propagates (generation)
def test_affect_propagates_across_a_generation():
    """A grief-narrowed parent CAN'T co-regulate the child (239000): the parent's grief
    clears its caregiving support -> the child's stress episodes resolve NARROW -> the
    child's window shrinks -> the child's adult priors shift DOWN (R14 bl_come_of_age).
    The CONTROL (gen_gain=0) decouples grief from caregiving -> the child of the SAME
    temperament is reared regulated -> priors UNSHIFTED (high). The failure mode crosses
    a generation only through the coupling."""
    w = _world()
    P = _pool(w)
    nat = dict(nat_world_safe=0.5, nat_others_trust=0.5, nat_self_worth=0.5)
    w.make_villager("gp_coupled", P[5]); w.suffer_failed_dream("gp_coupled", 8.0)
    w.make_villager("gp_ablate", P[6], gen_gain=0.0); w.suffer_failed_dream("gp_ablate", 8.0)
    pa = w.rear_child_of("gp_coupled", "child_c", P[50], episodes=8, **nat)
    pb = w.rear_child_of("gp_ablate", "child_a", P[70], episodes=8, **nat)
    for ax in ("world_safe", "others_trust", "self_worth"):
        assert pa[ax] < 0.5 < pb[ax], (
            "grief crosses a generation on %s: grieving-parent child %.3f MIS-SET (<0.5), "
            "ablated-parent child %.3f SECURE (>0.5)" % (ax, pa[ax], pb[ax]))
    assert w.window_of("child_c")["narrow_count"] > 0, "the child's window NARROWED"
    assert w.window_of("child_a")["widen_count"] > 0, "the ablated child's window WIDENED"


# ============================================================= ETHICS + discipline
def test_ethics_restore_and_no_reward_punishment_tokens():
    """ETHICS: felt grief is a harm-analog, so the induce arm is RESTORED by
    co-regulation (a measurable recovery, not a reset). No reward/punishment token in
    any seed RULE logic (scoped to rules/nodes/edges/concepts -- the prose descriptions
    legitimately DISCUSS the ethics protocol)."""
    # induce -> measure -> RESTORE: a grieving, spiralling agent is co-regulated back.
    w = _world(day_range=28)
    P = _pool(w)
    w.make_villager("harmed", P[10], coin=3.0)
    w.suffer_failed_dream("harmed", 6.0)
    for _ in range(3):
        w.live_period("harmed")
    before = w.grief_of("harmed")
    w.support("harmed", episodes=12)            # RESTORE = co-regulation
    for _ in range(5):
        w.live_period("harmed")
    assert w.grief_of("harmed") < before, "the induced grief was RESTORED (recovered), not reset"
    for sid in _SEEDS:
        seed = json.load(open(os.path.join(_ROOT, "seeds", sid + ".json")))
        blob = json.dumps(dict(rules=seed["rules"], nodes=seed.get("nodes", []),
                               edges=seed.get("edges", []),
                               concepts=seed.get("concepts", []))).lower()
        for token in ("reward", "punish", "penalty", "penalis", "penaliz"):
            assert token not in blob, "%s rule logic carries a %s token" % (sid, token)


def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every DECISION is a seed rule, not Python. The adapter mints nodes at ingest,
    delivers world facts, arms one-shots, ticks and reads -- it never COMPUTES a chosen
    action / outcome / regulation / prior in Python, and runs no Python rule engine. NO
    reward/punishment token. The decision PARAMETERS (base_value / grief_affinity /
    affect_gain / regulation) appear only in the mechanical ingest tables, never in a
    branch."""
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_affect_world.py")).read()
    for pat in (r"AFFECT_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n",
                r"ACTION_MENU\s*=\s*\[[\s\S]*?\]\n"):
        world_src = re.sub(pat, "", world_src, count=1)
    code = _strip_py(world_src)
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule", "add_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    for token in ("reward", "punish", "penalty", "penalis", "penaliz"):
        assert token not in code.lower(), "NO reward/punishment token (%s)" % token
    for param in ("grief_affinity", "base_value", "affect_gain", "regulation",
                  "grief_distress", "widen_count"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_seeds_self_load_only_rule_names_and_zero_new_rust():
    """Discipline: the five seeds are self_load_only (loaded ONLY by the R17 adapter ->
    cannot regress another suite); the rule set is exactly the nine named decisions; no
    rule mints/destroys a node (set_attr only); and every Term used is an EXISTING DSL
    Term -- proving ZERO new Rust (no exotic term type crept into a seed)."""
    seeds = {sid: json.load(open(os.path.join(_ROOT, "seeds", sid + ".json")))
             for sid in _SEEDS}
    for sid, s in seeds.items():
        assert s.get("self_load_only") is True, "%s must be self_load_only" % sid
        assert s.get("depends_on") == [], "%s declares no seed deps (reuse by import)" % sid
    names = {r["name"] for s in seeds.values() for r in s["rules"]}
    assert names == {
        "af_grief_from_loss", "af_choose_action",
        "af_outcome_work", "af_outcome_withdraw", "af_outcome_drink", "af_outcome_snap",
        "af_hardship_grief", "af_regulation_from_coreg", "af_grief_narrows_caregiving",
    }, "the nine affect decisions are RULES"
    # no node minted/destroyed by any rule (affect is attrs on existing nodes).
    for s in seeds.values():
        for r in s["rules"]:
            for eff in r.get("effects", []):
                assert eff[0] not in ("add_node", "del_node"), "%s mints/destroys a node" % r["name"]
    # every Term type is an EXISTING DSL term (zero new Rust).
    allowed = {"Lit", "Var", "Attr", "Plus", "Minus", "Times", "Div", "Min", "Max",
               "Eq", "Gt", "Gte", "Lt", "Lte", "And", "Or", "Not", "IfThenElse",
               "Sum", "Count", "Abs", "Argmax", "Argmin", "NodesOfType", "Neighbours"}
    seen = set()

    def _walk(o):
        if isinstance(o, dict):
            if "type" in o and isinstance(o["type"], str):
                seen.add(o["type"])
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
    for s in seeds.values():
        _walk(s["rules"])
    assert seen <= allowed, "NON-EXISTING Term type in a seed (would need new Rust): %s" % (seen - allowed)
