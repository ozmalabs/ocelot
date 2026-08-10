"""BLOCK 213000 -- SPITE + SKILL gate. Two NEW knobs (w_spite, order_n) on the
204000 core_emotions value economy, wired into the 212000 HARVEST commons. Every
agent decision is a graph RULE (ss_decision_value -> ss_choose_harvest /
ss_choose_burn over decision_value); this file gates that the decisions are
graph-native, spite is distinct from indifference, skill gates the anticipated
sanction, and the new world is isolated (neutral byte-identity vs 212000)."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.harvest_spite_world import HarvestSpiteWorld   # noqa: E402
from domains.harvest_world import HarvestWorld              # noqa: E402


def test_g_spite_malice_is_not_indifference():
    """Three agents in ONE bare commons: only the spiteful agent (w_spite>0) takes
    the self-costly BURN. Payoff-max and the indifferent psychopath both grab
    benefit-max and never burn -- malice != indifference. The RULE ss_choose_burn,
    not Python, decides."""
    hw = HarvestSpiteWorld([0.0, 0.0, 0.0], w_spites=[0.0, 0.0, 1.0],
                           order_ns=[1.0, 1.0, 1.0], comms=False, enforcement=0)
    hw.step()
    rows = hw.decisions()
    hw.close()
    payoff, psych, spite = rows
    assert payoff["burns"] == 0 and psych["burns"] == 0    # neither harms
    assert spite["burns"] == 1 and spite["chosen_burn"] > 0  # the spiteful one burns
    assert payoff["chosen_harvest"] == 20 and psych["chosen_harvest"] == 20
    assert spite["chosen_harvest"] == 0                    # forgoes its own take
    # payoff-max and psychopath are behaviourally identical (indifference)
    assert payoff["chosen_harvest"] == psych["chosen_harvest"]


def test_g_spite_burn_is_self_costly():
    """The spiteful agent's own yield is STRICTLY lower than the identical
    psychopath's -- it pays to harm (the definition of spite, not indifference)."""
    hw = HarvestSpiteWorld([0.0, 0.0], w_spites=[0.0, 1.0], order_ns=[1.0, 1.0],
                           comms=False, enforcement=0)
    o = hw.outcome(T=40)
    hw.close()
    psych_yield, spite_yield = o["per_agent_yield"]
    assert spite_yield < psych_yield          # self-costly
    assert o["per_agent_burned"][1] > 0       # and it burned the commons


def test_g_skill_order_n_gates_the_sanction():
    """SELFISH agent, 2x2 skill x environment: only strategic (order_n>=1) x
    enforced restrains. The anticipated sanction enters decision_value iff
    order_n>0 -- a myopic agent ignores it and grabs; in the bare commons (no
    sanction) BOTH grab. An order_n x environment interaction."""
    def h(order_n, enforcement, comms):
        hw = HarvestSpiteWorld([0.0] * 6, w_spites=[0.0] * 6, order_ns=[float(order_n)] * 6,
                               comms=comms, enforcement=enforcement)
        hw.step(); v = hw.decisions()[0]["chosen_harvest"]; hw.close()
        return v
    assert h(0, 0, False) == 20      # myopic, bare -> grab
    assert h(0, 25, True) == 20      # myopic, enforced -> ignores sanction, grab
    assert h(1, 0, False) == 20      # strategic, bare -> nothing to anticipate, grab
    assert h(1, 25, True) < 20       # strategic, enforced -> RESTRAINS (calculation)


def test_g_2d_cooperation_from_calculation_vs_care():
    """Under enforcement a high-skill psychopath cooperates by CALCULATION -- zero
    its order_n and it flips to defection. A prosocial agent cooperates by CARE --
    zeroing order_n does NOT flip it. Same behaviour, different knob."""
    def h(w_sg, order_n):
        hw = HarvestSpiteWorld([w_sg] * 6, w_spites=[0.0] * 6, order_ns=[float(order_n)] * 6,
                               comms=True, enforcement=25)
        hw.step(); v = hw.decisions()[0]["chosen_harvest"]; hw.close()
        return v
    assert h(0.0, 1) < 20 and h(0.0, 0) == 20     # psychopath: cooperates then FLIPS
    assert h(1.0, 1) < 20 and h(1.0, 0) < 20      # prosocial: cooperates, does NOT flip


def test_neutral_byte_identity_vs_212000():
    """A neutral spite-world agent (w_spite=0, order_n=1) reproduces the 212000
    HarvestWorld harvest decision in the bare commons -- decision_value == core
    total_value at neutral knobs. Default-OFF isolation."""
    ws = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    a = HarvestWorld(list(ws), comms=False)
    a.step()
    a_h = [max(0, int(a.s.node(d)["attrs"]["chosen_harvest"])) for d in a.decs]
    a.close()
    b = HarvestSpiteWorld(list(ws), comms=False, enforcement=0)
    b.step()
    b_h = [r["chosen_harvest"] for r in b.decisions()]
    b.close()
    assert a_h == b_h


def test_g_graph_native_source_audit():
    """The adapter takes NO agent decision: no rule-engine calls; the knobs live in
    the seed, read by ss_decision_value."""
    src = open(os.path.join(ROOT, "domains", "harvest_spite_world.py")).read()
    for pat in ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule("]:
        assert len(re.findall(re.escape(pat), src)) == 0, pat
    seed = open(os.path.join(ROOT, "seeds", "spite_skill.json")).read()
    assert "w_spite" in seed and "order_n" in seed and "ss_decision_value" in seed


def test_g_discipline_integer_native_and_isolated():
    """Seed is self_load_only with empty depends_on; every Lit is integer-valued."""
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds", "spite_skill.json")))
    assert seed["self_load_only"] is True
    assert seed["depends_on"] == []
    bad = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), float) \
               and not float(o["value"]).is_integer():
                bad.append(o["value"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(seed)
    assert bad == [], bad
