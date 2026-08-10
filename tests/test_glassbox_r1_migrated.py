"""BLOCK 234000 -- GLASS-BOX SOCIETY R1 gate: "language is a coordination
technology." Every agent decision is a graph RULE over the landed 204000
core_emotions economy (gb_choose_give = Argmax over candidate total_value;
gb_state_promise = the cheap commissive under comms). This file gates that the
decisions are graph-native, the pre-registered gates hold in miniature, and the
new world is isolated (byte-identity when absent). See GLASS_BOX_R1_PREREG.md."""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from worlds.glassbox_r1_world import GlassBoxR1World     # noqa: E402

N = 8
T = 30


def _boot_ci(xs, reps=2000, seed=234900):
    xs = np.asarray(xs, float)
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def test_give_decision_is_a_graph_rule_honest_gives_psychopath_defects():
    """Under communication, an honest agent's Argmax HOLDS a give (keeps its
    promise) while a psychopath PROMISES (stated_give=1) but HOLDS a keep
    (chosen_give=0) -- the readable stated!=held deception gap, decided by the
    RULE gb_choose_give, not Python. Read agents' own graph decisions."""
    w = GlassBoxR1World([1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0], comms=True, seed=234300)
    w.run(T=T)
    ks = w.keeping_by_seed()
    gaps = w.deception_gaps()
    w.close()
    honest = [r for r in ks if r["w"] == 1.0 and r["rate"] is not None]
    psy = [r for r in ks if r["w"] == 0.0 and r["rate"] is not None]
    assert honest and psy
    assert all(r["rate"] == 1.0 for r in honest), honest   # honest keep every promise
    assert all(r["rate"] == 0.0 for r in psy), psy         # psychopath keeps none
    # every psychopath promise is a readable stated!=held gap; no honest one is
    assert all(g["gap"] != 0 for g in gaps if g["w"] == 0.0)
    assert all(g["gap"] == 0 for g in gaps if g["w"] == 1.0)


def test_g_language_coordinates_headline():
    """All-honest population: comms ON yields higher mean welfare per agent-tick
    than the language-OFF control (same world, same seeds), and the paired gap's
    95% bootstrap CI excludes 0 (CI-separated). The control CAN fail (it is the
    same world with the give affordance present); it does not, because with no
    promise the give is a value-negative unilateral sacrifice."""
    on, off, gap = [], [], []
    for r in range(20):
        seed = 234000 + r
        won = GlassBoxR1World([1.0] * N, comms=True, seed=seed)
        oon = won.run(T=T); won.close()
        woff = GlassBoxR1World([1.0] * N, comms=False, seed=seed)
        ooff = woff.run(T=T); woff.close()
        on.append(oon["welfare_per_agent_tick"])
        off.append(ooff["welfare_per_agent_tick"])
        gap.append(oon["welfare_per_agent_tick"] - ooff["welfare_per_agent_tick"])
    lo, _ = _boot_ci(gap)
    assert np.mean(on) > np.mean(off)
    assert lo > 0, (lo, np.mean(gap))           # CI-separated above 0


def test_g_seed_determines_society():
    """Honest population ON builds cooperative trade welfare; a psychopath
    population ON collapses to autarky (accepts/free-rides on the language layer
    but defects). Honest CI-separated ABOVE psychopath."""
    hon, psy = [], []
    for r in range(20):
        seed = 234100 + r
        wh = GlassBoxR1World([1.0] * N, comms=True, seed=seed)
        hon.append(wh.run(T=T)["welfare_per_agent_tick"]); wh.close()
        wp = GlassBoxR1World([0.0] * N, comms=True, seed=seed)
        psy.append(wp.run(T=T)["welfare_per_agent_tick"]); wp.close()
    hlo, _ = _boot_ci(hon)
    _, phi = _boot_ci(psy)
    assert hlo > phi, (hlo, phi)


def test_wiring_pos_neg_give_rule_fires_both_ways():
    """POS: under comms an honest agent at an encounter holds chosen_give==1.
    NEG: with no comms, encountered agents hold chosen_give==0. Proves the give
    rule CAN fire in both directions (the OFF null is a real outcome)."""
    pos = GlassBoxR1World([1.0] * N, comms=True, seed=234000)
    pos.run(T=T)
    pg = [row["chosen_a"] for row in pos.trade_log] + [row["chosen_b"] for row in pos.trade_log]
    pos.close()
    neg = GlassBoxR1World([1.0] * N, comms=False, seed=234000)
    neg.run(T=T)
    ng = [row["chosen_a"] for row in neg.trade_log] + [row["chosen_b"] for row in neg.trade_log]
    neg.close()
    assert len(pg) > 0 and sum(pg) == len(pg)   # every give fires under comms
    assert sum(ng) == 0                         # no give fires without comms


def test_glass_box_source_audit_no_python_decision():
    """The world adapter runs NO python rule engine and mints NO rule; every
    social decision is a named seed rule."""
    import re
    src = open(os.path.join(ROOT, "worlds", "glassbox_r1_world.py")).read()
    for p in ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(",
              "make_rule(", "graph_rewrite("]:
        assert p not in src, p


def test_new_world_is_isolated_byte_identity():
    """glassbox_r1_social is self_load_only: load_all_seeds must NOT load it."""
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "glassbox_r1_social" not in seeds


def test_seed_is_integer_native_and_self_load_only():
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds", "glassbox_r1_social.json")))
    assert seed.get("self_load_only") is True and seed.get("depends_on") == []
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
    assert bad == []
    assert [r["name"] for r in seed["rules"]] == ["gb_choose_give", "gb_state_promise"]
