"""test_vision_compose_migrated — RUNG 8: COMPOSE THE EYE WITH THE CORTEX.

Pins the four things rung 8 actually established (`VISION_RUNG8_PREREG.md`):

  1. **DEFAULTS ARE OFF** (PROTOCOL §9) — `compose = 0.0` ships inert, so every
     result committed before rung 8 reproduces byte-identically.
  2. **THE COMPOSITION IS ONE ADMISSIBILITY STATEMENT** — the seed adds NO rule
     to either seed; it is a production (`LBipolar -[oo_pre]-> OOSynapse`) plus
     a params node. `vision_lateral` / `vision_onoff` are NOT edited.
  3. **THE CORTEX IS GRAIN-AGNOSTIC** — rung 6's SUnit rules bind their
     presynaptic channel by an UNTYPED traversal, so they read rung 7's
     LBipolars: the composed layer activates and learns.
  4. **THE GATE THAT FAILED, PINNED AS A FACT** — an IDEAL split-Gabor is BLIND
     on the composed pathway (OSI ~0.13 vs 1.0 on rung 6's channels), because
     theta is an EMA of the FORMATIVE drive and the probe drives ~2.2x harder.
     This is pinned so that a future rung cannot quietly "fix" the readout and
     believe it has grown selectivity — the failure is the rung's finding, and
     a regression here means someone changed the measure (PROTOCOL §5).

Rung 8 stopped at the calibration gate and burned NO confirmatory seed
(13000-13999 allocated, unused, clean).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.seed_registry  # noqa: F401,E402

SEED_PATH = os.path.join(ROOT, "seeds", "vision_compose.json")


def _manifest():
    with open(SEED_PATH) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
#  1. DEFAULTS OFF
# --------------------------------------------------------------------------- #
def test_compose_ships_off_by_default():
    """PROTOCOL §9: every new mechanism ships off, so committed results stand."""
    m = _manifest()
    params = [n for n in m["nodes"] if n["type"] == "ComposeParams"]
    assert len(params) == 1, "expected exactly one ComposeParams node"
    assert params[0]["attrs"]["compose"] == 0.0, (
        "vision_compose must ship compose=0.0 — an on-by-default mechanism "
        "silently changes every result committed before rung 8.")


# --------------------------------------------------------------------------- #
#  2. COMPOSE, DON'T MODIFY
# --------------------------------------------------------------------------- #
def test_composition_adds_no_rule_to_either_seed():
    """The composition is ANATOMY, not new cognition: rung 8 adds no rule.

    If this ever fails, the claim in VISION_RUNG8_PREREG.md §2 — that the cortex
    is grain-agnostic and the composition is one admissibility statement — is no
    longer what the seed does.
    """
    m = _manifest()
    assert m["rules"] == [], (
        f"vision_compose must add NO rule; found {[r['name'] for r in m['rules']]}")
    assert m["depends_on"] == ["vision_waves", "vision_lateral", "vision_onoff"]


def test_composition_is_exactly_one_production():
    """The whole composition: `LBipolar -[oo_pre]-> OOSynapse`.

    Gamma REJECTED that edge until this production existed
    (`InadmissibleEdge`), which is the substrate enforcing its own grammar —
    so this production IS the composition, stated as graph data.
    """
    prods = _manifest()["productions"]
    assert len(prods) == 1, f"expected exactly one production, got {len(prods)}"
    p = prods[0]
    assert (p["src"]["type"], p["edge_type"], p["tgt"]["type"]) == (
        "LBipolar", "oo_pre", "OOSynapse")


def test_rung6_and_rung7_seeds_are_not_edited():
    """`compose, don't modify` — pinned against the two seeds rung 8 composes."""
    for seed_id, ver in (("vision_onoff", "1.0.0"), ("vision_lateral", "1.0.0")):
        with open(os.path.join(ROOT, "seeds", f"{seed_id}.json")) as fh:
            m = json.load(fh)
        assert m["version"] == ver, (
            f"{seed_id} version moved to {m['version']} — rung 8 must COMPOSE "
            "these seeds, never modify them.")
        assert "vision_compose" not in json.dumps(m), (
            f"{seed_id} references vision_compose — the dependency must point "
            "the other way, or the composition has leaked into the composed.")


# --------------------------------------------------------------------------- #
#  3. THE CORTEX IS GRAIN-AGNOSTIC (the enabling finding)
# --------------------------------------------------------------------------- #
def test_onoff_rules_bind_their_channel_by_untyped_traversal():
    """WHY the composition needs no rule: `Bipolar` appears in the SUnit rules
    ONLY in comments. The rules bind `["b", "oo_pre", "sy"]` — untyped — so an
    LBipolar matches exactly as a Bipolar does."""
    with open(os.path.join(ROOT, "seeds", "vision_onoff.json")) as fh:
        m = json.load(fh)
    for name in ("oo_sunit_activate", "oo_learn_sub"):
        r = [x for x in m["rules"] if x["name"] == name][0]
        body = dict(r)
        body.pop("comment", None)
        assert "Bipolar" not in json.dumps(body), (
            f"{name} binds its presynaptic channel BY TYPE outside its comment "
            "— the cortex would no longer be grain-agnostic and rung 8's "
            "composition would need a rule after all.")


def test_composed_cortex_activates_and_learns_on_rung7_channels():
    """The load-bearing runtime fact: rung 6's SUnits, on rung 7's LBipolars,
    ACTIVATE and LEARN. An inert arm looking stable is exactly the false
    positive the eye agent's positive controls caught three times."""
    from domains.onoff_world import weights
    from scripts.rung8_lib import build, run_waves

    w, us, _anat, _bip = build(seed=0, n_units=6, channels="lateral")
    pre_types = set()
    for syn in w.s.in_neighbours(us[0], "oo_post"):
        for b in w.s.in_neighbours(syn, "oo_pre"):
            pre_types.add(w.s.node(b)["type"])
    assert pre_types == {"LBipolar"}

    w0 = weights(w, us)
    run_waves(w, 200)
    assert max(abs(float(w.s.node(u)["attrs"]["act"])) for u in us) > 0.0, (
        "the composed cortex never activated on rung 7's channels")
    assert float(np.abs(weights(w, us) - w0).max()) > 0.0, (
        "no weight moved — the learning rules are not firing on these channels")


# --------------------------------------------------------------------------- #
#  4. THE FAILED GATE, PINNED (so it cannot be quietly "fixed")
# --------------------------------------------------------------------------- #
def test_NOT_CLAIMED_the_probe_is_blind_on_the_composed_pathway():
    """RUNG 8'S ACTUAL FINDING, pinned as a fact rather than a footnote.

    An IDEAL split-Gabor — a PERFECT cell — scores ~0.13 on the composed
    pathway against 1.0 on rung 6's own channels, so the probe cannot support
    ANY claim here, positive or negative. Rung 8 therefore stopped and burned no
    confirmatory seed.

    The cause is measured (`VISION_RUNG8_PREREG.md` §D): theta is an EMA of the
    cell's own drive on the FORMATIVE input, and rung 7's retina is a predictive
    coder optimised for that input — so waves are CHEAP (act 0.861) while the
    out-of-distribution grating probe is EXPENSIVE (act 1.902, ~2.2x). Theta
    lands below the probe and the iceberg never bites. Rung 6's channels got
    away with it only because they do NOT decorrelate (5.32 vs 5.12).

    If this test starts failing because the ideal cell now scores HIGH, someone
    has changed the readout — which PROTOCOL §5 requires be a NEW prospective
    pre-registration, not a rescue of this gate.
    """
    from scripts.rung8_lib import (
        adapt_theta, build, develop_retina, ideal_split_gabor, osi_of,
    )

    w, us, _a, _b = build(seed=0, n_units=6, channels="lateral")
    develop_retina(w, 3000)
    for u in us:
        ideal_split_gabor(w, u, theta=0.0, phase=0.0)
    adapt_theta(w, 400)
    o_lat, _ = osi_of(w, us)

    w2, us2, _a2, _b2 = build(seed=0, n_units=6, channels="degenerate")
    for u in us2:
        ideal_split_gabor(w2, u, theta=0.0, phase=0.0)
    adapt_theta(w2, 400)
    o_deg, _ = osi_of(w2, us2)

    assert o_deg.mean() > 0.85, (
        f"rung 6's ideal cell scores {o_deg.mean():.4f} — the reproduction "
        "control is broken, so nothing else here is interpretable.")
    assert o_lat.mean() < 0.5, (
        f"the ideal cell now scores {o_lat.mean():.4f} on the composed pathway "
        "(rung 8 measured 0.1290). If the readout was changed to achieve this, "
        "PROTOCOL §5 requires a NEW prospective pre-registration — a failed "
        "gate is never rescued by changing the measure.")


def test_the_OFF_channel_is_dead_at_g0_and_alive_once_developed():
    """The instrument bug rung 8 found before its gate (the fourth in this arc).

    At `lat_g0 = 0` the residual IS the raw centre `c >= 0`, so
    `OFF = max(-c, 0) == 0`: the OFF channel is identically dead at init, and a
    cortex probed there has no signed filter to use. `develop_retina` brings the
    retina to its own fixed point — the state every rung-7 claim is measured at
    — before the cortex is probed.
    """
    from domains.complex_cells import binarize, grating, present
    from domains.lateral_world import channels
    from domains.onoff_world import set_params
    from scripts.rung8_lib import build, develop_retina

    w, us, anat, _b = build(seed=0, n_units=6, channels="lateral")
    set_params(w, oo_eta=0.0)
    present(w, binarize(grating((16, 16), 0.0, 0.0, 4.0)))
    _on, off = channels(w, anat["bipolars"])
    assert float(off.max()) <= 1e-9, (
        f"OFF max {off.max():.6f} at g=0 — the dead-OFF fact rung 8's "
        "develop_retina exists for no longer holds; re-derive the calibration.")

    develop_retina(w, 3000)
    present(w, binarize(grating((16, 16), 0.0, 0.0, 4.0)))
    on2, off2 = channels(w, anat["bipolars"])
    assert float(off2.mean()) > 0.05, (
        f"OFF mean {off2.mean():.4f} after development — the retina did not "
        "grow a surround, so the composed pathway is not rung 7's.")
    assert abs(float(on2.mean()) - float(off2.mean())) < 0.05, (
        "ON/OFF are not balanced after development — rung 7's channels are not "
        "in the state its claims were measured at.")
