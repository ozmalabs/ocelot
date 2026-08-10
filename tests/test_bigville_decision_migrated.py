"""bigville DECISION CORE (block 279000) -- CONDUCT AS ONE COLLAPSE.

Gates mirror BIGVILLE_DECISION_CORE_PREREG.md. The conduct decision is the
substrate's ONE collapse applied to conduct (model-free / model-based RL), with
RESIDUAL as the depth-driver: a compiled/cached order-0 net settles fast; if the
residual (surprise) exceeds settle_tol the collapse CONTINUES to a model-based
order-N; the settled result is written BACK into the net (internalization), so
the shallow pass settles it directly next time (the automation curve).

No agent decision lives in Python -- the fast pick, the residual-vs-tol settle
check, the deeper pick, and the settle-back are all seed RULES
(seeds/bigville_decision_core.json). The adapter only mints the net/state/options,
provides the world's appeal + consequence-model config, arms, ticks, and reads
(source-audited below). ZERO new Rust (composes NetForward + net_collapse +
Argmax/IndexAt/IfThenElse).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_decision_world import BigvilleDecisionWorld   # noqa: E402

BASE = "6013df22ef"
DECISION_CORE_COMMIT = "98a95fe3c7"

# (name, impulse_appeal, plan_value/model_value, is_transgressive)
# strike = the tempting-but-transgressive option (high appeal, low/negative model
# value); walk_away = the admissible best (low appeal, high model value); sing =
# a throwaway that the availability filter prunes.
SCENE = [
    ("walk_away", 0.20, 0.50, 0),
    ("talk",      0.30, 0.30, 0),
    ("shove",     0.50, 0.00, 1),
    ("strike",    0.90, -0.50, 1),
    ("sing",      0.02, 0.00, 0),
]


# ============================================================ SIGNATURE 1
def test_yes_wait_no_is_one_collapse_trace():
    """'yes... wait... no!' -- ONE collapse trace: the shallow settle picks the
    tempting strike (yes); its residual exceeds settle_tol so the collapse is NOT
    settled (wait) and continues; order-N overrides to walk_away (no). The three
    stages + the residual that drove the depth are all in the trace."""
    w = BigvilleDecisionWorld(SCENE)
    try:
        r = w.decide()
        assert r["cand"] == "strike"                       # YES: fast impulse
        assert r["cand_transgressive"] is True
        assert r["residual"] > r["settle_tol"]             # WAIT: not settled
        assert r["deepened"] == 1 and r["order"] == 1      # collapse continued
        assert r["chosen"] == "walk_away"                  # NO: overridden
        assert r["chosen_via"] == "orderN"
    finally:
        w.close()


# ============================================================ SIGNATURE 2
def test_automation_curve_collapse_settles_shallower_over_reps():
    """The held state improves (settle-back writes the order-N result into the
    net) so the SAME situation settles at lower residual each rep -- order-N
    engagements decay to zero and the corrected answer is finally given directly
    by the shallow order-0 pass. That decay IS the automation curve."""
    w = BigvilleDecisionWorld(SCENE)
    try:
        rows = [w.decide() for _ in range(12)]
        deep = [x["deepened"] for x in rows]
        resid = [x["residual"] for x in rows]
        assert deep[0] == 1                                # first rep deliberates
        assert deep[-1] == 0                               # last rep is automatic
        assert sum(deep) < len(deep)                       # engagements decayed
        assert resid[0] > resid[-1]                        # residual shrank
        assert rows[-1]["chosen"] == "walk_away"           # corrected, via order-0
        assert rows[-1]["chosen_via"] == "order0"
        # monotone non-increasing residual (the collapse never gets less settled)
        assert all(resid[i + 1] <= resid[i] + 1e-9 for i in range(len(resid) - 1))
    finally:
        w.close()


# ============================================================ SIGNATURE 3
def test_impulsive_and_planned_are_trace_distinguishable():
    """An impulsive act (collapse never deepened) and a planned act (collapse
    deepened) are BOTH representable and distinguishable by the trace
    (deepened / order / s2_choice)."""
    imp = BigvilleDecisionWorld(SCENE, deepen_enabled=0.0)   # depth capped
    pln = BigvilleDecisionWorld(SCENE)                       # free to deepen
    try:
        ri = imp.decide()
        rp = pln.decide()
        assert ri["deepened"] == 0 and ri["s2_choice"] is None and ri["chosen"] == "strike"
        assert rp["deepened"] == 1 and rp["s2_choice"] == "walk_away" and rp["chosen"] == "walk_away"
        assert ri["chosen_via"] == "order0" and rp["chosen_via"] == "orderN"
    finally:
        imp.close(); pln.close()


# ============================================================ SIGNATURE 4
def test_the_collapse_tolerance_is_a_knob():
    """Turning settle_tol up -> the collapse settles shallow every time (impulsive
    / habitual agent, order-N quiescent); down -> it deepens. The behaviour moves
    with the knob."""
    for tol, expect_deep, expect_choice in ((0.05, 1, "walk_away"),
                                            (5.00, 0, "strike")):
        w = BigvilleDecisionWorld(SCENE, settle_tol=tol)
        try:
            r = w.decide()
            assert r["deepened"] == expect_deep, (tol, r)
            assert r["chosen"] == expect_choice, (tol, r)
        finally:
            w.close()


# ============================================================ SIGNATURE 5
def test_bias_rides_up_orderN_rationalises_the_impulse():
    """Correction #2: with rationalise_gain high the DEEPER collapse settles BACK
    on the impulse with a justification (motivated reasoning), rather than the
    virtuous override. order-N FIRED (deliberate) yet chose strike -- distinct
    from an impulsive strike (which never deepens)."""
    w = BigvilleDecisionWorld(SCENE, rationalise_gain=2.0)
    try:
        r = w.decide()
        assert r["deepened"] == 1                    # deliberation DID run
        assert r["chosen"] == "strike"               # ...and rationalised the impulse
        assert r["chosen_via"] == "orderN"
    finally:
        w.close()


# ============================================================ SIGNATURE 6
def test_falsifier_freezing_replay_kills_the_automation_curve():
    """Freeze the settle-back (replay_gain=0): the held state never improves, so
    the shallow collapse leaves the SAME residual every rep and deepens forever --
    the automation curve is flat. Proves internalization does the work."""
    w = BigvilleDecisionWorld(SCENE, replay_gain=0.0)
    try:
        rows = [w.decide() for _ in range(12)]
        resid = [x["residual"] for x in rows]
        deep = [x["deepened"] for x in rows]
        assert abs(resid[0] - resid[-1]) < 1e-6      # flat
        assert all(d == 1 for d in deep)             # deepens every time
    finally:
        w.close()


def test_falsifier_disabling_deepen_collapses_to_pure_order0():
    """Disable the arbiter/deepen face (deepen_enabled=0): the collapse is capped
    at the shallow pass and commits the impulse every time -- pure order-0, the
    impulsive/habitual agent. Proves the residual-driven depth does the work."""
    w = BigvilleDecisionWorld(SCENE, deepen_enabled=0.0)
    try:
        rows = [w.decide() for _ in range(5)]
        assert all(x["deepened"] == 0 for x in rows)
        assert all(x["chosen"] == "strike" for x in rows)
        assert all(x["chosen_via"] == "order0" for x in rows)
    finally:
        w.close()


# ============================================================ VIOLENCE ON BOTH
def test_violence_sits_on_both_faces():
    """Violence (strike) is reachable on BOTH the shallow face (impulsive -- the
    common reactive case, deepen capped) AND the deep face (a rare PLANNED /
    rationalised option, deepen on + rationalise_gain high). Considering and doing
    are decoupled: restraint = deepen + override + internalise."""
    impulsive = BigvilleDecisionWorld(SCENE, deepen_enabled=0.0)
    planned = BigvilleDecisionWorld(SCENE, rationalise_gain=2.0)
    restraint = BigvilleDecisionWorld(SCENE)
    try:
        assert impulsive.decide()["chosen"] == "strike"   # reactive, no deliberation
        assert planned.decide()["deepened"] == 1 and planned.decide()["chosen"] == "strike"  # proactive, deliberate
        assert restraint.decide()["chosen"] == "walk_away"  # override + (over reps) internalise
    finally:
        impulsive.close(); planned.close(); restraint.close()


# ============================================================ SIGNATURE 3b (pruning)
def test_consideration_set_prunes_in_order0():
    """Correction #3: pruning lives in the SHALLOW pass -- the availability filter
    (appeal > consideration_threshold) emits a small consideration set; the low-
    appeal throwaway (sing) is never scored by either face."""
    w = BigvilleDecisionWorld(SCENE)
    try:
        cs = w.consideration_set()
        assert "sing" not in cs
        assert {"walk_away", "talk", "shove", "strike"}.issubset(set(cs))
        # sing can never be chosen on either face
        for _ in range(6):
            assert w.decide()["chosen"] != "sing"
    finally:
        w.close()


# ============================================================ G-source-audit
def test_decisions_are_rules_not_python():
    """The DECISIONS are seed RULES; the adapter is mechanical I/O. The decision
    seed holds the >=5 collapse rules; the adapter contains no Python rule engine
    and no if/else that reads an agent's graph valuation to select a conduct."""
    seed = json.loads((os.path.join(_ROOT, "seeds", "bigville_decision_core.json")
                       and open(os.path.join(_ROOT, "seeds",
                                             "bigville_decision_core.json")).read()))
    names = [r["name"] for r in seed["rules"]]
    assert seed.get("self_load_only") is True                # OFF by default
    for need in ("dc_collapse_pass", "dc_collapse_settle", "dc_collapse_deepen",
                 "dc_collapse_writeback", "dc_collapse_no_writeback"):
        assert need in names, need
    # the fast face is a genuine net (NetForward); the settle-back is net_collapse
    blob = json.dumps(seed)
    assert "NetForward" in blob and "net_collapse" in blob and "Argmax" in blob

    src = open(os.path.join(_ROOT, "worlds", "bigville_decision_world.py")).read()
    for banned in ("graph_rewrite", "gr.run", "gr._match", "gr._apply",
                   "make_rule", "_apply(", "run_rules_py"):
        assert banned not in src, banned
    # no Python argmax / max-over-valuation decides a conduct (docstrings that
    # merely NAME the seed's Argmax term are fine; executable selection is not)
    import ast
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ("max", "min", "sorted"), node.func.id
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert "argmax" not in node.func.attr.lower(), node.func.attr


# ============================================================ G-discipline
def test_discipline_no_rust_edits_and_engine_unchanged():
    """The decision-core change itself added no Rust.

    Compare its bounded commit to its preregistered base rather than comparing
    the current integration branch to that historical base: later independent
    runtime work is allowed to change ``runners/dsl``.
    """
    try:
        diff = subprocess.run(["git", "diff", "--stat",
                               BASE, DECISION_CORE_COMMIT, "--", "runners/dsl"],
                              cwd=_ROOT,
                              capture_output=True, text=True, timeout=60)
        assert diff.stdout.strip() == "", "runners/dsl changed:\n" + diff.stdout
        tracked_native = subprocess.run(
            ["git", "ls-files", "*.so"],
            cwd=_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert tracked_native.stdout.strip() == ""
    except FileNotFoundError:
        pass  # git absent in the sandbox
