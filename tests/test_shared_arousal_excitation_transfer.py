"""Regression for seeds/shared_arousal.json + domains/shared_arousal.py --
excitation transfer between co-target beliefs (Zillmann 1971/1983; Dutton
& Aron 1974). See docs/research/psychology_affect/
SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.shared_arousal import (
    mint_target_arousal, mint_target_concept, record_targeted_incident,
)


def _fresh_mt():
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    d = json.load(open("seeds/shared_arousal.json"))
    inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": "test_mt", "temperature": 1.5})
    return inner, mt


# ---------------------------------------------------------------------
# 1. Prediction 1 -- elevated arousal strictly amplifies a co-target
#    incident's effect.
# ---------------------------------------------------------------------
def test_hostility_driven_arousal_amplifies_a_co_target_desire_incident():
    inner, mt = _fresh_mt()
    hostility = mint_target_concept(inner, mt, "regard_for", "Alex")
    desire = mint_target_concept(inner, mt, "desire_for", "Alex")
    arousal = mint_target_arousal(inner, mt, "Alex")

    record_targeted_incident(inner, hostility, arousal, evidence=-1.0,
                             intensity=0.8, base_alpha=0.3)
    treatment = record_targeted_incident(inner, desire, arousal, evidence=1.0,
                                         intensity=0.1, base_alpha=0.3)

    inner2, mt2 = _fresh_mt()
    desire_ctrl = mint_target_concept(inner2, mt2, "desire_for", "Alex")
    arousal_ctrl = mint_target_arousal(inner2, mt2, "Alex")
    control = record_targeted_incident(inner2, desire_ctrl, arousal_ctrl,
                                       evidence=1.0, intensity=0.1, base_alpha=0.3)

    assert control["effective_alpha"] == pytest.approx(0.3)
    assert treatment["effective_alpha"] > control["effective_alpha"]
    assert treatment["external_field"] > control["external_field"]


# ---------------------------------------------------------------------
# 2. Prediction 2 -- symmetry: desire-driven arousal amplifies a later
#    hostility incident too, not a one-way special case.
# ---------------------------------------------------------------------
def test_desire_driven_arousal_amplifies_a_later_hostility_incident():
    inner, mt = _fresh_mt()
    hostility = mint_target_concept(inner, mt, "regard_for", "Alex")
    desire = mint_target_concept(inner, mt, "desire_for", "Alex")
    arousal = mint_target_arousal(inner, mt, "Alex")

    record_targeted_incident(inner, desire, arousal, evidence=1.0,
                             intensity=0.8, base_alpha=0.3)
    r = record_targeted_incident(inner, hostility, arousal, evidence=-1.0,
                                 intensity=0.1, base_alpha=0.3)
    assert r["effective_alpha"] > 0.3


# ---------------------------------------------------------------------
# 3. Prediction 3 -- arousal decays without fresh spikes.
# ---------------------------------------------------------------------
def test_arousal_decays_over_time_without_a_fresh_spike():
    inner, mt = _fresh_mt()
    concept = mint_target_concept(inner, mt, "regard_for", "Alex")
    arousal = mint_target_arousal(inner, mt, "Alex")
    record_targeted_incident(inner, concept, arousal, evidence=-1.0,
                             intensity=0.8, base_alpha=0.3)
    level_after_spike = inner.node(arousal)["attrs"]["level"]
    # a second incident with zero intensity (no new arousal contribution)
    # still reads the DECAYED level, strictly lower than the spike
    r = record_targeted_incident(inner, concept, arousal, evidence=-1.0,
                                 intensity=0.0, base_alpha=0.3)
    assert r["arousal_level"] < level_after_spike


# ---------------------------------------------------------------------
# 4. Prediction 4 -- arousal is per-target, not global.
# ---------------------------------------------------------------------
def test_arousal_does_not_leak_across_different_targets():
    inner, mt = _fresh_mt()
    alex_hostility = mint_target_concept(inner, mt, "regard_for", "Alex")
    alex_arousal = mint_target_arousal(inner, mt, "Alex")
    sam_desire = mint_target_concept(inner, mt, "desire_for", "Sam")
    sam_arousal = mint_target_arousal(inner, mt, "Sam")

    record_targeted_incident(inner, alex_hostility, alex_arousal, evidence=-1.0,
                             intensity=0.8, base_alpha=0.3)
    r = record_targeted_incident(inner, sam_desire, sam_arousal, evidence=1.0,
                                 intensity=0.1, base_alpha=0.3)
    assert r["effective_alpha"] == pytest.approx(0.3)


# ---------------------------------------------------------------------
# 5. Idempotent minting.
# ---------------------------------------------------------------------
def test_minting_target_concept_and_arousal_is_idempotent():
    inner, mt = _fresh_mt()
    c1 = mint_target_concept(inner, mt, "regard_for", "Alex")
    c2 = mint_target_concept(inner, mt, "regard_for", "Alex")
    a1 = mint_target_arousal(inner, mt, "Alex")
    a2 = mint_target_arousal(inner, mt, "Alex")
    assert c1 == c2
    assert a1 == a2


# ---------------------------------------------------------------------
# 6. No prior seed was edited (task charter).
# ---------------------------------------------------------------------
def test_no_prior_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "seeds/can_native_reimplementation.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout


# ---------------------------------------------------------------------
# 7. depends_on / dependency hygiene.
# ---------------------------------------------------------------------
def test_seed_manifest_dependencies_and_productions():
    d = json.load(open("seeds/shared_arousal.json"))
    assert d["depends_on"] == ["can_native_reimplementation"]
    assert len(d["productions"]) == 1
    prod = d["productions"][0]
    assert prod["src"]["type"] == "Microtheory"
    assert prod["edge_type"] == "has_target_arousal"
    assert prod["tgt"]["type"] == "TargetArousal"
    assert d["rules"] == []
