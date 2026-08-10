"""bigville R8 (block 256000) -- LIFE-GOALS & DREAMS (the identity / soul layer)
gates: a GROUNDED long-horizon life-goal ORIENTS sub-goal selection (the
decision_value Argmax) + the ablation control; the DREAM is held on the
UNGROUNDED side of the grounding boundary (source-audit); the dream REGULATES
AFFECT (HEADLINE) -- temporary relief under R7-induced aversive valence WITHOUT
changing material state + the dreamless-twin control; the dream COLLAPSES into a
leave-goal on threshold OR a recruiter's grounded path, else stays LATENT
(resignation). Gates mirror BIGVILLE_GOAL_PREREG.md.

No soul-layer decision lives in Python -- every orient / audit / relief /
collapse / latent verdict is a seed rule (bigville_goal_life /
bigville_goal_dream). The adapter arms one-shots, wires edges, ticks and reads
(source-audit at the foot of this file). ZERO new Rust: the Argmax, the Sum, the
add_node mint, Exists, Max are all PRE-EXISTING DSL Terms.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_goal_world import (                              # noqa: E402
    BigvilleGoalWorld, SAVE, LEISURE, AIM_WEALTH)
from worlds.bigville_time_world import DAY                            # noqa: E402


def _pool(w):
    return sorted(w._cell_at.keys())


def _world():
    w = BigvilleGoalWorld(day_range=16)
    w.set_phase(DAY)
    w.add_bank("scrooge", _pool(w)[0], reserves=100000, salary=0, fair_rate_bp=500)
    return w


# ================================================ G-life-goal-orients + control
def _orienting_soul(w, name):
    """A soul weighing a lower-appeal SAVE (serves the wealth aim) against a
    higher-appeal LEISURE (serves nothing). Base appeal favours LEISURE."""
    P = _pool(w)
    w.make_soul(name, P[10], coin=1000)
    w.add_choicepoint(name)
    w.add_suboption(name, SAVE, base_appeal=1.0, serves_aim=AIM_WEALTH)
    w.add_suboption(name, LEISURE, base_appeal=2.0, serves_aim=0.0)


def test_life_goal_orients_subgoal_choice():
    """A become-wealthy life-goal tips the decision_value Argmax so the
    lower-base-appeal SAVE beats the higher-base-appeal LEISURE -- a long-horizon
    bias over the reachable satisficing pull."""
    w = _world()
    _orienting_soul(w, "ada")
    w.set_life_goal("ada", aim=AIM_WEALTH, orient_weight=3.0)
    w.orient("ada")
    assert w.chosen_subgoal_of("ada") == SAVE, "life-goal orients toward SAVE"


def test_ablate_life_goal_removes_the_long_horizon_bias():
    """ABLATION (load-bearing): drop the has_life_goal edge -> the Argmax bias sum
    is empty -> the base appeal alone decides -> LEISURE wins. Same cast, same
    options -- the life-goal was what moved it."""
    w = _world()
    _orienting_soul(w, "ada")
    w.set_life_goal("ada", aim=AIM_WEALTH, orient_weight=3.0)
    w.orient("ada")
    assert w.chosen_subgoal_of("ada") == SAVE, "with life-goal: SAVE"
    w.ablate_life_goal("ada")
    w.orient("ada")
    assert w.chosen_subgoal_of("ada") == LEISURE, "ablated: no bias -> LEISURE"


# ================================================ G-dream-is-ungrounded (audit)
def test_dream_is_ungrounded_unlike_the_life_goal():
    """Source-audit of the grounding boundary: the DREAM carries ungrounded=1 and
    NO grounded_path edge (the ungrounded side), while the LIFE-GOAL carries
    grounded_flag=1 and a real path_to edge (the grounded side)."""
    w = _world()
    P = _pool(w)
    w.make_soul("bob", P[10], coin=100)
    w.set_life_goal("bob", aim=AIM_WEALTH, orient_weight=3.0)
    w.set_dream("bob", kind="join_navy")
    w.audit("bob")
    # the life-goal is on the GROUNDED side
    assert w.lifegoal_grounded_of("bob") == 1, "life-goal marked grounded"
    assert w.lifegoal_has_path("bob"), "life-goal holds a real path_to (grounded)"
    # the dream is on the UNGROUNDED side
    ds = w.dream_state("bob")
    assert ds["ungrounded"] == 1, "dream marked ungrounded"
    assert not ds["has_grounded_path"], "dream holds NO grounded_path (ungrounded)"


# ================================================ G-dream-regulates-affect (HEADLINE)
def _distressed_soul(w, name, *, with_dream):
    """Induce aversive valence through the REAL R7 channel: a mortgage + income
    collapse -> foreclosure -> bf_homeless_affect drops valence / raises arousal.
    Optionally give the soul a dream to invoke."""
    P = _pool(w)
    w.make_soul(name, P[10], coin=1000)
    w.attach_affect(name, concern_mag=4.0, concern_drop=3.0, arousal=0.0, valence=5.0)
    w.add_house("h_%s" % name, 200, apprec=0)
    w.mortgage(name, "h_%s" % name, principal=500, payment=30, term=3)
    w.set_char(name, coin=0)                   # the income collapse (R4/R7 shock)
    for _ in range(5):
        w.period()
    if with_dream:
        # collapse_threshold far below so it RELIEVES, not collapses, this gate.
        w.set_dream(name, relief_valence=3.0, relief_arousal=2.0,
                    aversive_threshold=5.0, collapse_threshold=-100.0)


def test_dream_regulates_affect_headline():
    """The escape valve: under R7-induced distress, invoking the dream RAISES
    valence and LOWERS arousal (temporary relief) while the MATERIAL state is
    UNCHANGED -- homeless still 1, mortgage balance identical. Relief without
    resolution (glass-box: the debt is still there; the soul just feels better)."""
    w = _world()
    _distressed_soul(w, "cara", with_dream=True)
    aff_before = w.affect_state("cara")
    homeless_before = w.homeless_of("cara")
    balance_before = w.balance_of("cara")
    assert aff_before["valence"] < 5.0, "the R7 shock made the present aversive"
    assert aff_before["arousal"] > 0.0, "distress raised arousal"
    w.invoke_relief("cara")
    aff_after = w.affect_state("cara")
    assert aff_after["valence"] > aff_before["valence"], "dream RELIEVES valence"
    assert aff_after["arousal"] < aff_before["arousal"], "dream LOWERS arousal"
    assert w.dream_state("cara")["invoked"] == 1, "the dream was invoked once"
    # THE MATERIAL STATE IS UNCHANGED -- relief without resolution.
    assert w.homeless_of("cara") == homeless_before == 1, "still homeless (unchanged)"
    assert w.balance_of("cara") == balance_before, "mortgage balance unchanged"


def test_dreamless_twin_has_no_relief_valve():
    """ABLATION (the isolation): the identical R7 shock on a DREAMLESS soul leaves
    valence at the distressed floor -- no relief valve. The dream (its presence)
    was what moved the affect, not the passage of the invocation phase."""
    wd = _world()
    _distressed_soul(wd, "cara", with_dream=True)
    v_before = wd.affect_state("cara")["valence"]
    wd.invoke_relief("cara")
    v_dream = wd.affect_state("cara")["valence"]

    wn = _world()
    _distressed_soul(wn, "cara", with_dream=False)
    wn.invoke_relief("cara")                    # arm the phase; no dream to match
    v_dreamless = wn.affect_state("cara")["valence"]

    assert v_dreamless == v_before, "dreamless: valence stays at the distress floor"
    assert v_dream > v_dreamless, "the dream's relief is a strict ablation delta"


# ================================================ G-dream-collapses + control
def _soul_with_affect(w, name, *, valence):
    P = _pool(w)
    w.make_soul(name, P[10], coin=1000)
    w.attach_affect(name, concern_mag=4.0, concern_drop=3.0,
                    arousal=0.0, valence=float(valence))


def test_dream_collapses_on_unbearable_valence():
    """Push valence past the collapse threshold (the present unbearable) -> the
    dream COLLAPSES into an actionable leave-goal and the soul ACTS (leaves)."""
    w = _world()
    _soul_with_affect(w, "dan", valence=2.0)
    w.set_dream("dan", collapse_threshold=3.0, aversive_threshold=5.0)
    w.try_collapse("dan")
    ds = w.dream_state("dan")
    assert ds["collapsed"] == 1, "the dream collapsed"
    assert ds["latent"] == 0, "no longer latent"
    assert w.left_of("dan") == 1, "the soul ACTS -- it leaves"
    assert w.action_goal_kinds("dan") == ["leave"], "exactly one leave-goal minted"
    assert w.resigned_of("dan") == 0, "collapse is not resignation"


def test_dream_collapses_when_a_recruiter_grounds_a_path():
    """A grounded PATH appearing (a recruiter mints a grounded_path edge) collapses
    the dream regardless of valence -- the ungrounded escape became reachable."""
    w = _world()
    _soul_with_affect(w, "eve", valence=5.0)     # NOT aversive
    w.set_dream("eve", collapse_threshold=-100.0, aversive_threshold=5.0)
    w.recruiter_arrives("eve")                   # the path appears in the belief
    w.try_collapse("eve")
    ds = w.dream_state("eve")
    assert ds["has_grounded_path"], "the recruiter grounded a path"
    assert ds["collapsed"] == 1, "the grounded path collapsed the dream"
    assert w.left_of("eve") == 1, "the soul leaves"
    assert w.action_goal_kinds("eve") == ["leave"], "one leave-goal minted"


def test_below_threshold_no_path_stays_latent_control():
    """CONTROL: below the collapse threshold + no grounded path -> the dream stays
    LATENT (held, NOT acted) -- resignation, the learned-helplessness floor. A
    dream that never activates is the abuse line."""
    w = _world()
    _soul_with_affect(w, "fay", valence=2.0)
    w.set_dream("fay", collapse_threshold=-100.0, aversive_threshold=5.0)
    w.try_collapse("fay")
    ds = w.dream_state("fay")
    assert ds["collapsed"] == 0, "no collapse below threshold + no path"
    assert w.left_of("fay") == 0, "the soul does NOT leave (held, not acted)"
    assert ds["latent"] == 1, "the dream stays LATENT"
    assert w.resigned_of("fay") == 1, "resignation is marked (the abuse line)"
    assert w.action_goal_kinds("fay") == [], "no leave-goal minted"


# ==================================================================== source-audit
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every soul-layer DECISION is a seed rule, not Python. The adapter arms
    one-shots, wires edges, ticks and reads -- it never COMPUTES an orient choice /
    ungrounded verdict / relief / collapse / latent outcome in Python."""
    import json
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_goal_world.py")).read()
    world_src = re.sub(r"GOAL_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    life = json.load(open(os.path.join(_ROOT, "seeds", "bigville_goal_life.json")))
    dream = json.load(open(os.path.join(_ROOT, "seeds", "bigville_goal_dream.json")))
    rule_names = {r["name"] for r in life["rules"]} | {r["name"] for r in dream["rules"]}
    assert rule_names == {
        "gg_lifegoal_grounded", "gg_orient_choice",
        "gg_dream_ungrounded", "gg_dream_relief",
        "gg_dream_collapse_threshold", "gg_dream_collapse_path", "gg_dream_latent",
    }, "the seven soul-layer decisions are RULES"
    # no Python rule engine in the adapter
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    # the DECISION OUTPUTS appear ONLY in the seeds -- executable adapter code never
    # branches on them (they are opaque attrs it sets by name and reads back).
    for out in ("chosen_subgoal", "collapsed", "invoked", "ungrounded", "left",
                "resigned", "latent"):
        assert ("if " + out) not in code, \
            "decision output %s must live in a rule where/effects, not an adapter branch" % out


def test_the_argmax_and_mint_are_existing_terms_no_new_rust():
    """At the source level: the orient choice is the PRE-EXISTING Argmax Term over
    a Sum/IfThenElse (the decision_value family), the collapse mints via the
    PRE-EXISTING add_node effect, and the ungrounded/path audits use the
    PRE-EXISTING Exists Term -- NO new Rust. runners/dsl carries no diff (the
    discipline ledger verifies the empty diff + own-engine md5)."""
    import json
    life = json.load(open(os.path.join(_ROOT, "seeds", "bigville_goal_life.json")))
    dream = json.load(open(os.path.join(_ROOT, "seeds", "bigville_goal_dream.json")))
    both = json.dumps(life) + json.dumps(dream)
    assert '"Argmax"' in both, "the orient choice uses the Argmax decision_value Term"
    assert '"Sum"' in both and '"IfThenElse"' in both, "the life-goal bias is a Sum/IfThenElse"
    assert '"Exists"' in both, "the grounding-boundary audit uses the Exists Term"
    # the collapse mints an ActionGoal via the existing add_node effect
    minted = [eff for r in dream["rules"] for eff in r.get("effects", [])
              if eff[0] == "add_node" and eff[2] == "ActionGoal"]
    assert len(minted) == 2, "both collapse rules mint an ActionGoal via add_node"
    assert True
