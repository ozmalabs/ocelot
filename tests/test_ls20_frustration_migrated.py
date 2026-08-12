"""Gates for BLOCK 226000 — FUTILE repetition -> FRUSTRATION -> STOP.

The frustration modulator tracks FUTILITY (repetition WITHOUT understanding-gain),
NOT mere repetition. Every decision is a graph rule; the adapter is mechanical.
"""
import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains.frustration_world import FrustrationWorld, run_episode, CAP  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402


# --------------------------------------------------------------------------
# G-frustration-tracks-futility (HEADLINE + teeth): identical repetition, but
# a PRODUCTIVE repeat (a gain observable set) never raises frustration.
# --------------------------------------------------------------------------
def test_futile_repetition_raises_frustration():
    w = FrustrationWorld(enabled=True)
    fr = 0.0
    for e in range(6):
        fr, brk = w.observe("S|A")          # same (state,action), no gain
    assert fr > 0.0, "futile repetition must raise frustration"


def test_productive_repetition_stays_flat_THE_TEETH():
    """The gate that FAILS a plain repeat-counter: the SAME (state,action)
    repeated, but each repeat yields understanding -> frustration stays 0."""
    w = FrustrationWorld(enabled=True)
    fr = None
    for e in range(10):
        fr, brk = w.observe("S|A", d_hyp=1)   # identical sig, but a real gain
        assert brk == 0.0, "a productive repeat must never break the loop"
    assert fr == 0.0, "productive repetition must NOT raise frustration"


def test_futile_and_productive_are_separated_at_W():
    """Frustration after W=6 repeats: futile high, productive 0."""
    rf = run_episode("futile", 226000, enabled=True, measure_horizon=6)
    rp = run_episode("productive", 226000, enabled=True, measure_horizon=6)
    assert rf["loop_traj"][5] > 0.0
    assert rp["loop_traj"][5] == 0.0


def test_gain_by_any_of_the_three_observables_suppresses_frustration():
    """d_hyp OR d_state OR s_drop each count as understanding-gain."""
    for gain in ("d_hyp", "d_state", "s_drop"):
        w = FrustrationWorld(enabled=True)
        for e in range(8):
            fr, brk = w.observe("S|A", **{gain: 1})
        assert fr == 0.0, f"gain via {gain} must suppress frustration"


# --------------------------------------------------------------------------
# G-breaks-the-loop: regulation ON breaks a futile cycle in FEWER steps than OFF.
# --------------------------------------------------------------------------
def test_regulation_on_breaks_the_futile_loop_off_does_not():
    on = run_episode("futile", 226000, enabled=True)
    off = run_episode("futile", 226000, enabled=False)
    assert on["break_step"] is not None, "ON must break the futile loop"
    assert off["break_step"] is None, "OFF must never self-stop (the cycling owner saw)"
    assert on["steps_to_break"] < off["steps_to_break"]
    assert off["steps_to_break"] == CAP


# --------------------------------------------------------------------------
# G-no-false-break (selectivity): regulation does NOT break a PRODUCTIVE loop.
# --------------------------------------------------------------------------
def test_regulation_does_not_break_a_productive_loop():
    for i in range(20):
        rp = run_episode("productive", 226000 + i, enabled=True)
        assert rp["break_step"] is None, "must NOT stop an agent still gaining"


# --------------------------------------------------------------------------
# G-narration (208000 tie-in): the stop is narrated from graph state.
# --------------------------------------------------------------------------
def test_break_is_narrated_from_graph_state():
    r = run_episode("futile", 226000, enabled=True)
    assert r["narration"] is not None
    assert "frustrat" in r["narration"].lower()
    assert "stop" in r["narration"].lower()


# --------------------------------------------------------------------------
# G-graph-native: the decision is a rule reading the modulator; the adapter has
# NO `if repeated: stop`, no rule-engine calls.
# --------------------------------------------------------------------------
def test_decisions_are_rules_not_python():
    man = manifest_for("ls20_frustration")
    names = {r["name"] for r in man["rules"]}
    assert {"fr_mark_futile", "fr_accumulate", "fr_break"} <= names
    # the futility judgement is a rule with an Exists recurrence match + no-gain
    fr = next(r for r in man["rules"] if r["name"] == "fr_mark_futile")
    assert "Exists" in str(fr["where"]), "recurrence must be a graph MATCH"


def test_adapter_has_no_forbidden_agent_logic():
    src = open(os.path.join(_ROOT, "domains", "frustration_world.py")).read()
    # strip docstrings/comments so the audit scans CODE, not prose.
    code = re.sub(r'"""[\s\S]*?"""', "", src)
    code = "\n".join(ln.split("#", 1)[0] for ln in code.splitlines())
    for bad in ("graph_rewrite.run", "gr.run(", "._match(", "._apply(", "make_rule"):
        assert bad not in code, f"adapter must not contain {bad!r}"
    # the adapter never DECIDES the stop on a recurrence count; the ONLY stop
    # condition it reads is break_now, set by the fr_break RULE.
    assert 'a.get("break_now")' in code
    assert "break_now" in code and re.search(r"if\s+repeated", code) is None


# --------------------------------------------------------------------------
# G-discipline: default-OFF byte-identity.
# --------------------------------------------------------------------------
def test_seed_is_self_load_only_and_default_off():
    man = manifest_for("ls20_frustration")
    assert man["self_load_only"] is True
    assert man["depends_on"] == []


def test_disabled_never_breaks_even_when_futile():
    w = FrustrationWorld(enabled=False)
    for e in range(CAP):
        fr, brk = w.observe("S|A")            # futile, but regulation OFF
        assert brk == 0.0
    assert fr == 0.0, "with enabled=0 the frustration rules must not fire"


def test_ls20_frustration_absent_from_full_boot():
    """self_load_only seeds are skipped by load_all_seeds -> byte-identical."""
    import json
    import glob
    d = json.load(open(os.path.join(_ROOT, "seeds", "ls20_frustration.json")))
    assert d.get("self_load_only") is True
    # nothing depends_on it
    for f in glob.glob(os.path.join(_ROOT, "seeds", "*.json")):
        try:
            dd = json.load(open(f))
        except Exception:
            continue
        # a LIST-rooted file in seeds/ (`_recovered_f16_rules.json`) declares no
        # depends_on at all — the same guard the seed loader itself applies.
        if not isinstance(dd, dict):
            continue
        assert "ls20_frustration" not in (dd.get("depends_on") or [])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
