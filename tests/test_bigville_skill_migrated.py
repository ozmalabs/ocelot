"""bigville R6 (block 254000) -- SKILL DYNAMICS gates: skill scales production yield
(HEADLINE) + the skill-ablation control; LEARNING-BY-DOING with diminishing returns
+ the learn-ablation control; TEACHING as the teacher's DECISION -- faster-than-solo,
the willing-REFUSAL of a competitive threat, and a COERCED teacher who transfers but
SABOTAGES (247 power lever + 234 stated!=held). Gates mirror BIGVILLE_SKILL_PREREG.md.

No skill-dynamics decision lives in Python -- every learn / willing-vs-refuse /
coercion-success / sabotage is a seed rule (bigville_skill_learn / _teach). The
adapter only arms one-shots, wires edges, co-locates, ticks, reads (source-audit at
the foot of this file).
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_skill_world import BigvilleSkillWorld, FISHING, FISH, BAIT  # noqa: E402
from worlds.bigville_time_world import DAY                                       # noqa: E402

FARM_CELL = (2, 2)
FISH_CELL = (2, 4)


def _yield_world(farmer_skill, fisher_skill):
    """Two FISHING shops (input bait), keepers with the given fishing skill levels."""
    w = BigvilleSkillWorld(day_range=16)
    w.set_phase(DAY)
    w.make_learner("farmer", FARM_CELL)
    w.make_learner("fisher", FISH_CELL)
    if farmer_skill is not None:
        w.set_learnable_skill("farmer", FISHING, farmer_skill)
    if fisher_skill is not None:
        w.set_learnable_skill("fisher", FISHING, fisher_skill)
    w.add_shop("fs_farm", good=FISH, price=3, cell=FARM_CELL, keeper="farmer",
               activity=FISHING, input_good=BAIT, stock=0, input_qty=9)
    w.add_shop("fs_fish", good=FISH, price=3, cell=FISH_CELL, keeper="fisher",
               activity=FISHING, input_good=BAIT, stock=0, input_qty=9)
    w.set_hours(1)
    w.refresh_open()
    return w


# ==================================================== G-skill-scales-yield HEADLINE
def test_skill_scales_yield_headline():
    """The farmer's fishing yield << the fisherman's -- skill scales production yield
    (be_produce mints output proportional to skill)."""
    w = _yield_world(1.0, 5.0)
    yf = w.yield_of("fs_farm")
    yF = w.yield_of("fs_fish")
    assert yf == 1.0, "low-skill farmer yields his skill level (1)"
    assert yF == 5.0, "high-skill fisherman yields his skill level (5)"
    assert yF > yf, "skill scales yield: fisherman >> farmer"
    assert (yF - yf) == 4.0


def test_ablate_skill_yields_equal():
    """ABLATION (skill load-bearing): equalize the two fishing skill levels -> the two
    yields become EQUAL. The skill DIFFERENTIAL is what drives the yield gap."""
    w = _yield_world(3.0, 3.0)
    yf = w.yield_of("fs_farm")
    yF = w.yield_of("fs_fish")
    assert yf == yF == 3.0, "equal skill -> equal yield (differential ablated)"


def test_off_specialty_yields_zero():
    """A keeper with NO fishing skill produces 0 (grounds specialization -- an R4
    invariant re-asserted here)."""
    w = _yield_world(None, 5.0)          # farmer has no Skill node at all
    assert w.yield_of("fs_farm") == 0.0, "off-specialty (no skill) -> zero yield"
    assert w.yield_of("fs_fish") == 5.0


# ======================================================== G-learning-by-doing
def _practice_curve(learn_rate, steps=6, start=1.0):
    w = BigvilleSkillWorld(day_range=16)
    w.set_phase(DAY)
    w.make_learner("farmer", FARM_CELL)
    w.set_learnable_skill("farmer", FISHING, start)
    w.set_skill_attr("farmer", learn_rate=learn_rate)
    curve = [round(w.skill_level("farmer", FISHING), 6)]
    for _ in range(steps):
        w.practice("farmer", FISHING)
        curve.append(round(w.skill_level("farmer", FISHING), 6))
    return w, curve


def test_learning_by_doing_rises_with_diminishing_returns():
    """The farmer practising fishing -> skill RISES over runs, monotone, with strictly
    DIMINISHING per-step gains (never a linear +k forever)."""
    w, curve = _practice_curve(0.3, steps=6)
    assert curve[-1] > curve[0], "practice raises the skill"
    assert all(curve[i + 1] > curve[i] for i in range(len(curve) - 1)), "monotone up"
    gains = [round(curve[i + 1] - curve[i], 6) for i in range(len(curve) - 1)]
    assert all(gains[i] > gains[i + 1] for i in range(len(gains) - 1)), \
        "strictly diminishing returns"
    assert w.practice_count_of("farmer") == 6, "each practice counted"


def test_ablate_learning_is_flat():
    """ABLATION (learning load-bearing): learn_rate=0 -> the skill is FLAT across the
    same practice sequence."""
    _w, curve = _practice_curve(0.0, steps=6)
    assert len(set(curve)) == 1, "learn_rate=0 -> no gain, skill flat"
    assert curve[0] == curve[-1] == 1.0


# ================================================================= G-teaching
def _teach_world(is_rival):
    w = BigvilleSkillWorld(day_range=16)
    w.set_phase(DAY)
    w.make_learner("farmer", FARM_CELL)
    w.make_learner("fisher", FISH_CELL)
    w.set_learnable_skill("farmer", FISHING, 1.0)
    w.set_learnable_skill("fisher", FISHING, 8.0)
    w.set_skill_attr("farmer", learn_rate=0.3, is_rival=float(is_rival))
    # teacher: benevolent baseline, protects trade from rivals, low personal power
    w.set_skill_attr("fisher", teach_benevolence=2.0, rival_weight=5.0,
                     teach_rate=0.5, sabotage_rate=0.12, power=1.0)
    return w


def test_teaching_beats_solo_practice():
    """The taught curve DOMINATES the solo-practice curve at every step and ends
    strictly higher (teach_rate 0.5 > learn_rate 0.3)."""
    # solo
    _s, solo = _practice_curve(0.3, steps=5)
    # taught (non-rival, willing)
    w = _teach_world(is_rival=0)
    w.arrange_teaching("fisher", "farmer", FISHING)
    taught = [round(w.skill_level("farmer", FISHING), 6)]
    for _ in range(5):
        w.teach("farmer")
        taught.append(round(w.skill_level("farmer", FISHING), 6))
    assert all(taught[i] >= solo[i] for i in range(len(solo))), \
        "taught dominates solo at every step"
    assert taught[-1] > solo[-1], "taught ends strictly higher"
    assert taught[1] > solo[1], "a single willing teach gains more than a single practice"


def test_willing_teacher_teaches_non_rival():
    """A single willing teach of a NON-rival learner transfers at teach_rate (sincere:
    stated == held)."""
    w = _teach_world(is_rival=0)
    w.arrange_teaching("fisher", "farmer", FISHING)
    before = w.skill_level("farmer", FISHING)
    w.teach("farmer")
    after = w.skill_level("farmer", FISHING)
    assert after > before, "willing teacher transfers skill"
    assert w.teach_outcome_of("farmer") == 1, "outcome = willing"
    assert w.stated_minus_held("farmer") == 0.0, "sincere: stated == held (no sabotage)"
    assert w.sabotaged_of("farmer") == 0


def test_teacher_refuses_competitive_threat():
    """Willingness is a real decision: with the learner a competitive threat
    (is_rival=1) and NO coercion, the fisherman REFUSES -- no transfer."""
    w = _teach_world(is_rival=1)
    w.arrange_teaching("fisher", "farmer", FISHING)
    before = w.skill_level("farmer", FISHING)
    w.teach("farmer")
    assert w.skill_level("farmer", FISHING) == before, "refused -> no skill transfer"
    assert w.teach_outcome_of("farmer") == 0, "outcome = refused"
    assert w.refused_of("farmer") == 1


def test_coerced_teacher_transfers_but_degraded_and_sabotages():
    """247 + 234: a powerful coercer forces the rival-refusing teacher (coerced=1); the
    coerced teacher THEN transfers but DEGRADED (0 < coerced_gain < willing_gain), the
    sabotage readable as stated != held."""
    # willing gain (reference) on a non-rival learner
    wref = _teach_world(is_rival=0)
    wref.arrange_teaching("fisher", "farmer", FISHING)
    g0 = wref.skill_level("farmer", FISHING)
    wref.teach("farmer")
    willing_gain = wref.skill_level("farmer", FISHING) - g0

    # coerced path: rival learner + a powerful coercer (John)
    w = _teach_world(is_rival=1)
    w.make_learner("john", FARM_CELL)
    w.set_skill_attr("john", power=9.0)          # power >> teacher.power (1.0)
    w.arrange_teaching("fisher", "farmer", FISHING)
    w.wire_coercion("john", "fisher")
    w.coerce("john", "fisher")
    assert w.coerced_of("farmer") == 1, "247 lever: power dominance forces coercion"
    c0 = w.skill_level("farmer", FISHING)
    w.teach("farmer")
    coerced_gain = w.skill_level("farmer", FISHING) - c0
    assert coerced_gain > 0.0, "coerced teacher DOES transfer (not a refusal)"
    assert coerced_gain < willing_gain, "but DEGRADED vs a willing teacher"
    assert w.teach_outcome_of("farmer") == 2, "outcome = coerced/degraded"
    assert w.sabotaged_of("farmer") == 1
    # the 234 deception atom: professes teach_rate, delivers sabotage_rate
    assert w.stated_rate_of("farmer") == 0.5
    assert w.held_rate_of("farmer") == 0.12
    assert w.stated_minus_held("farmer") > 0.0, "stated != held -> sabotage readable"


def test_weak_coercer_cannot_force_the_transfer():
    """Lever load-bearing: a WEAK coercer (power < teacher.power) -> bs_coerce does not
    fire -> coerced=0 -> the teacher still REFUSES the rival (no transfer)."""
    w = _teach_world(is_rival=1)
    w.make_learner("weak", FARM_CELL)
    w.set_skill_attr("weak", power=0.5)          # power < teacher.power (1.0)
    w.arrange_teaching("fisher", "farmer", FISHING)
    w.wire_coercion("weak", "fisher")
    w.coerce("weak", "fisher")
    assert w.coerced_of("farmer") == 0, "insufficient power -> no coercion"
    before = w.skill_level("farmer", FISHING)
    w.teach("farmer")
    assert w.skill_level("farmer", FISHING) == before, "still refuses -> no transfer"
    assert w.teach_outcome_of("farmer") == 0


# ==================================================================== source-audit
def _strip_py(src: str) -> str:
    """Remove docstrings/prose (triple-quoted), line comments, and string literals,
    leaving only EXECUTABLE code -- so a decision parameter named in prose does not
    read as a Python decision."""
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every skill-dynamics DECISION is a seed rule, not Python. The adapter arms
    one-shots, wires edges, co-locates, ticks and reads -- it never COMPUTES a learn/
    willing-vs-refuse/coercion/sabotage outcome in Python."""
    import json
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_skill_world.py")).read()
    # drop the declared mechanical DEFAULTS table (the R4 ECON_DEFAULTS pattern: attr
    # keys set so a rule never reads a missing key -- ingest, not a decision)
    world_src_no_defaults = re.sub(r"SKILL_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "",
                                   world_src, count=1)
    code = _strip_py(world_src_no_defaults)
    # the five decisions must be RULE names in the seeds
    learn = json.load(open(os.path.join(_ROOT, "seeds", "bigville_skill_learn.json")))
    teach = json.load(open(os.path.join(_ROOT, "seeds", "bigville_skill_teach.json")))
    rule_names = {r["name"] for r in learn["rules"]} | {r["name"] for r in teach["rules"]}
    assert rule_names == {"bs_practice", "bs_teach_willing", "bs_teach_refuse",
                          "bs_coerce", "bs_teach_coerced"}, "the five decisions are RULES"
    # no Python rule engine anywhere in the adapter
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule", "run_rules("):
        assert banned not in code or banned == "run_rules(", None
    assert "graph_rewrite" not in code and "make_rule" not in code, \
        "adapter must not run/author the Python rule engine"
    # the DECISION PARAMETERS (what makes willing/refuse/coerce/sabotage come out one
    # way vs another) appear ONLY in the seeds -- executable adapter code never reads
    # them to branch. They are opaque attrs it sets via **kw and never names in code.
    for param in ("teach_benevolence", "rival_weight", "teach_rate", "sabotage_rate",
                  "is_rival"):
        assert param not in code, \
            f"decision parameter {param} must live in the rule `where`, not adapter code"
    # and there is no `if` branching on a skill-decision outcome attr
    for outcome in ("teach_outcome", "coerced", "held_rate", "stated_rate"):
        assert f"if " + outcome not in code, f"{outcome} is read-off only, never a branch"


def test_decisions_are_decision_value_comparisons():
    """The willingness decision is a decision_value threshold (benevolence -
    rival_weight*is_rival > 0) and coercion a power-dominance threshold -- the same
    Argmax/threshold family as ss_choose_burn / the R4 credit-trust call."""
    import json
    teach = json.load(open(os.path.join(_ROOT, "seeds", "bigville_skill_teach.json")))
    by = {r["name"]: r for r in teach["rules"]}
    willing_src = json.dumps(by["bs_teach_willing"]["where"])
    assert "teach_benevolence" in willing_src and "rival_weight" in willing_src, \
        "willingness is a benevolence - rival_weight*is_rival decision_value"
    coerce_src = json.dumps(by["bs_coerce"]["where"])
    assert "power" in coerce_src, "coercion is a power-dominance decision"
