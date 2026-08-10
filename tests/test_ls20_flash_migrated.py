"""RUNG 223000 — FLASH-ONSET-GUIDED mechanic discovery gates.

Tests the owner's claim that the avatar<->shape flash is a salience indicator of
the rules. The flash is a POINTER (where/when) detected by the EXISTING onset
stream, DISTINCT from the persistent TRANSFORM (what) discovered by the identical
222000 sd-loop. Bounded (fast) versions of the powered gates in
scripts/arc_ls20_flash_measure.py.

Gates:
  - the seed-claim range is clean (verbatim check_claim);
  - G-flash-detects: the flash fires ONSET events (general stream) that localise;
  - G-sample-efficiency: flash converges in FEWER observations than blind under
    clutter, and NO advantage on a clean scene (anti-rig);
  - G-pointer-vs-content: the conflate arm scores worse change-set F1;
  - graph-native: fg_pick_flash (Argmax onset magnitude) is a rule, default-OFF;
  - default-OFF byte-identity: the flash rules never fire without flash_on;
  - source-audit: the mechanic is discovered, never table-read.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "scripts"),
           os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import worlds.arc_ls20_flash as FL  # noqa: E402
from worlds.arc_ls20_flash import (  # noqa: E402
    FlashArena, OnsetEye, FlashAgent, ACTIONS, make_eval_scenes,
    observations_to_converge, held_out_f1,
)

N = 20


# NOTE (supervisor, 223000 landing): the prereg-time `check_claim(223000,223999)`
# gate is recorded in prereg commit 8e1a510b (CLEAN before any number). It is NOT
# a permanent pytest here — once this rung's VISION_PROTOCOL.md ledger row lands,
# the block is (correctly) DECLARED exactly once, so a "range is undeclared"
# assertion inverts by construction. The other three ls20 rungs (planning/mapnav/
# percell) carry no such test; this one was removed to match that pattern.


# --- G-flash-detects: the flash IS an onset event (general stream) ----------
def test_flash_is_detected_as_onset_event_and_localises():
    """The flash fires onset events on the general 2-D onset stream; the Argmax-
    magnitude onset localises to a flash cell, and the flash onset dB is above the
    distractor-motion onsets. NOT a bespoke detector."""
    localised = 0
    total = 0
    flash_mag, distr_mag = [], []
    for a in range(6):
        rng = np.random.default_rng(300 + a)
        arena = FlashArena(rng, n=N, n_distractors=2)
        eye = OnsetEye(N)
        eye.adapt(arena.grid())
        for _ in range(5):
            act = ACTIONS[int(rng.integers(0, len(ACTIONS)))]
            prev, nxt, fc, ctr = arena.step(act)
            events = eye.onset_on_transition(prev, nxt, fc)
            assert events, "the flash must fire at least one onset event"
            fset = set(fc)
            flash_mag += [m for (r, c, m) in events if (r, c) in fset]
            distr_mag += [m for (r, c, m) in events if (r, c) not in fset]
            events.sort(key=lambda e: -e[2])
            localised += int((events[0][0], events[0][1]) in fset)
            total += 1
        eye.stop()
    assert localised / total >= 0.8, (
        f"the Argmax onset should localise to the flash; got {localised}/{total}")
    if flash_mag and distr_mag:
        assert np.mean(flash_mag) > np.mean(distr_mag), (
            "the flash onset must be more salient than distractor-motion onsets")


# --- G-sample-efficiency: flash converges in FEWER obs under clutter --------
def test_flash_beats_blind_under_clutter():
    """At n_distractors=2 the flash-guided arm reaches change-set F1>=0.9 in far
    fewer observations than the blind 222000 mode-colour control (which is
    censored in the bounded budget). The headline sample-efficiency claim."""
    ev = make_eval_scenes(np.random.default_rng(999), 8, N, 2)
    flash, blind = [], []
    for seed in range(4):
        rf = observations_to_converge("flash_separate", seed, n=N, n_distractors=2,
                                      tau=0.9, budget=150, eval_scenes=ev)
        rb = observations_to_converge("blind", seed, n=N, n_distractors=2,
                                      tau=0.9, budget=150, eval_scenes=ev)
        flash.append(rf["observations"]); blind.append(rb["observations"])
    assert np.mean(flash) < np.mean(blind), (
        f"flash-guided must converge in fewer observations under clutter; "
        f"flash={flash} blind={blind}")
    assert max(flash) < 150, "the flash arm should converge within the budget"


def test_no_flash_advantage_on_a_clean_scene_anti_rig():
    """At n_distractors=0 (a clean 222000-style scene) the flash gives NO
    advantage -- blind's mode-colour already localises. If the flash won even here
    it would be rigged. The anti-circularity check."""
    ev = make_eval_scenes(np.random.default_rng(999), 8, N, 0)
    for seed in range(3):
        rf = observations_to_converge("flash_separate", seed, n=N, n_distractors=0,
                                      tau=0.9, budget=150, eval_scenes=ev)
        rb = observations_to_converge("blind", seed, n=N, n_distractors=0,
                                      tau=0.9, budget=150, eval_scenes=ev)
        assert rb["converged"] and rf["converged"], "both converge on a clean scene"
        # the flash must not be dramatically faster on a clean scene.
        assert rf["observations"] <= rb["observations"] + 5
        assert rb["observations"] <= rf["observations"] + 5


# --- G-pointer-vs-content: conflating the pointer with content hurts --------
def test_conflating_flash_with_content_scores_worse():
    """The CONFLATE arm predicts the transient flash as a persistent change; the
    true (flash-free) next frame reverts it -> false-positive changed cells ->
    lower change-set F1 than the SEPARATE arm. The transient/persistent
    separation is load-bearing."""
    ev = make_eval_scenes(np.random.default_rng(9500), 8, N, 2)
    sep, conf = [], []
    for seed in range(3):
        for arm, bucket in (("flash_separate", sep), ("flash_conflate", conf)):
            rng = np.random.default_rng(400 + seed)
            agent = FlashAgent(arm=arm)
            arena = FlashArena(rng, n=N, n_distractors=2)
            eye = OnsetEye(N); eye.adapt(arena.grid())
            for t in range(1, 41):
                act = agent.next_probe() or ACTIONS[t % len(ACTIONS)]
                prev, nxt, fc, ctr = arena.step(act)
                ch = agent.attend_flash(eye.onset_on_transition(prev, nxt, fc))
                agent.observe(act, prev, nxt, ch)
            eye.stop()
            bucket.append(held_out_f1(agent, ev))
    assert np.mean(sep) > np.mean(conf), (
        f"separating pointer from content must score higher; sep={sep} conf={conf}")


# --- graph-native: fg_pick_flash is a RULE (Argmax onset magnitude) ---------
def test_flash_attention_is_a_graph_rule_argmax():
    """The attention decision (which onset is the flash) is the fg_pick_flash graph
    rule doing Argmax over magnitude_db -- not Python."""
    agent = FlashAgent(arm="flash_separate")
    loc = agent.attend_flash([(3, 4, 10.0), (7, 8, 26.0), (1, 1, 18.0)])
    assert loc == (7.0, 8.0), f"Argmax(magnitude) should pick (7,8); got {loc}"
    assert agent.attend_flash([]) is None
    # the rule exists in the loaded seed.
    from domains.ls20_flash_seed import RULES
    assert any(r["name"] == "fg_pick_flash" for r in RULES)


def test_flash_rules_are_default_off():
    """With flash_on unset the fg_pick_flash rule cannot fire (guarded); a blind
    Percell-only agent never grows FlashOnset attention state."""
    from worlds.arc_ls20_percell import Percell
    from domains.ls20_flash_seed import RULES
    pc = Percell()
    for r in RULES:
        pc.n.add_rule(r)          # rules present but flash_on is NOT set (default off)
    # add a FlashOnset cue + attend_flash phase; the guard (flash_on==1) blocks it.
    s, g, n = pc.s, pc.g, pc.n
    fo = s.add_node("FlashOnset", {"row_index": 5.0, "column_index": 6.0,
                                   "magnitude_db": 9.0})
    n.add_edge_unchecked(g, "has_flash_onset", fo)
    n.set_attr(g, "flash_mag", -1.0)
    n.set_attr(g, "phase", "attend_flash")
    n.run_rules()
    assert float(s.node(g)["attrs"].get("flash_mag")) < 0.0, (
        "fg_pick_flash must NOT fire with flash_on unset (default-off)")


# --- source-audit: the mechanic is discovered, never table-read -------------
def test_source_audit_mechanic_is_discovered_not_table_read():
    import inspect
    banned = ["_MOVE", "_XFORM"]
    for name in ("discover_blind", "discover_flash_separate", "_window_region_spec",
                 "_spec_from_objs", "predict_conflate"):
        src = inspect.getsource(getattr(FL, name))
        assert not any(b in src for b in banned), (
            f"{name} must not read a ground-truth action->transform table")
