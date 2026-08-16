"""Regression for seeds/hate_attribution.json + domains/hate_attribution.py
-- global+stable negative attribution about ANOTHER agent, generalizing
ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md's self-directed residual outward.
See docs/research/psychology_affect/HATE_ATTRIBUTION_PREREG.md.
"""
from __future__ import annotations

import json

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import ensure_can_seed
from domains.hate_attribution import (
    HATE_STABILITY_THRESHOLD, mint_target_pattern, record_hate_incident,
)


def _fresh(name="test_mt"):
    s = sr.Substrate()
    inner = s._inner
    ensure_can_seed(inner)
    for seed_path in ("seeds/shared_arousal.json", "seeds/hate_attribution.json"):
        d = json.load(open(seed_path))
        inner.load_seed_manifest(engine_rules_only(d))
    mt = inner.add_node("Microtheory", {"name": name, "temperature": 1.5})
    return inner, mt


# ---------------------------------------------------------------------
# 3. First encounter -> first_encounter, never global_other.
# ---------------------------------------------------------------------
def test_first_encounter_is_never_global_other():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    r = record_hate_incident(inner, mt, pat, negative=True)
    assert r["attribution_locus"] == "first_encounter"
    assert r["confirm_streak"] == 0
    assert not r["crystallized"]


# ---------------------------------------------------------------------
# 1. A negative incident confirming an already-negative pattern -> global_other.
# ---------------------------------------------------------------------
def test_confirming_incident_is_global_other():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    record_hate_incident(inner, mt, pat, negative=True)
    r = record_hate_incident(inner, mt, pat, negative=True)
    assert r["attribution_locus"] == "global_other"
    assert r["confirm_streak"] == 1


# ---------------------------------------------------------------------
# 2. A positive incident against an established negative pattern -> specific_act.
# ---------------------------------------------------------------------
def test_disconfirming_incident_is_specific_act():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    record_hate_incident(inner, mt, pat, negative=True)
    r = record_hate_incident(inner, mt, pat, negative=False)
    assert r["attribution_locus"] == "specific_act"


# ---------------------------------------------------------------------
# 4. A specific_act resets confirm_streak to 0.
# ---------------------------------------------------------------------
def test_specific_act_resets_confirm_streak():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Sam")
    record_hate_incident(inner, mt, pat, negative=True)
    r_confirm = record_hate_incident(inner, mt, pat, negative=True)
    assert r_confirm["confirm_streak"] == 1
    r_exception = record_hate_incident(inner, mt, pat, negative=False)
    assert r_exception["attribution_locus"] == "specific_act"
    assert r_exception["confirm_streak"] == 0
    r_after = record_hate_incident(inner, mt, pat, negative=True)
    assert r_after["attribution_locus"] == "global_other"
    assert r_after["confirm_streak"] == 1


# ---------------------------------------------------------------------
# 5. Crystallization requires the threshold, not the first confirmation.
# ---------------------------------------------------------------------
def test_crystallization_requires_the_stability_threshold():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    # call 0 is first_encounter (streak 0); calls 1..threshold-1 are
    # global_other, incrementing the streak by 1 each time; the streak
    # only reaches HATE_STABILITY_THRESHOLD on call index
    # HATE_STABILITY_THRESHOLD itself -- HATE_STABILITY_THRESHOLD+1 total
    # calls to reach it.
    results = [record_hate_incident(inner, mt, pat, negative=True)
               for _ in range(HATE_STABILITY_THRESHOLD + 1)]
    for r in results[:-1]:
        assert not r["crystallized"]
    assert results[-1]["crystallized"]
    assert results[-1]["crystallized_this_call"]
    assert results[-1]["confirm_streak"] == HATE_STABILITY_THRESHOLD
    # below-threshold incidents never crystallize even though several are global_other
    below_threshold_global = [r for r in results[:-1] if r["attribution_locus"] == "global_other"]
    assert len(below_threshold_global) == HATE_STABILITY_THRESHOLD - 1  # first call is first_encounter


# ---------------------------------------------------------------------
# 6. removal_desire only receives evidence on the crystallizing incident.
# ---------------------------------------------------------------------
def test_removal_desire_evidence_gated_on_crystallization():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    # HATE_STABILITY_THRESHOLD+1 calls reaches crystallization (see the
    # threshold test above); one more call afterward confirms the gate
    # only opens once.
    results = [record_hate_incident(inner, mt, pat, negative=True)
               for _ in range(HATE_STABILITY_THRESHOLD + 2)]
    for r in results[:HATE_STABILITY_THRESHOLD]:
        assert r["removal_desire_external_field"] == 0.0
    crystallizing = results[HATE_STABILITY_THRESHOLD]
    assert crystallizing["crystallized_this_call"]
    assert crystallizing["removal_desire_external_field"] > 0.0
    after = results[HATE_STABILITY_THRESHOLD + 1]
    assert not after["crystallized_this_call"]
    assert after["removal_desire_external_field"] == pytest.approx(
        crystallizing["removal_desire_external_field"])


# ---------------------------------------------------------------------
# 7. Per-target isolation, within ONE substrate.
# ---------------------------------------------------------------------
def test_hate_toward_one_target_does_not_touch_another():
    inner, mt = _fresh()
    alex = mint_target_pattern(inner, mt, "Alex")
    sam = mint_target_pattern(inner, mt, "Sam")
    for _ in range(HATE_STABILITY_THRESHOLD + 1):
        record_hate_incident(inner, mt, alex, negative=True)
    assert bool(inner.node(alex)["attrs"]["crystallized"])

    r_sam = record_hate_incident(inner, mt, sam, negative=True)
    assert r_sam["attribution_locus"] == "first_encounter"
    assert not r_sam["crystallized"]
    assert not bool(inner.node(sam)["attrs"]["crystallized"])


# ---------------------------------------------------------------------
# Idempotent minting.
# ---------------------------------------------------------------------
def test_minting_target_pattern_is_idempotent():
    inner, mt = _fresh()
    p1 = mint_target_pattern(inner, mt, "Alex")
    p2 = mint_target_pattern(inner, mt, "Alex")
    assert p1 == p2


# ---------------------------------------------------------------------
# No prior seed was edited.
# ---------------------------------------------------------------------
def test_no_prior_seed_was_edited():
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain",
             "seeds/can_native_reimplementation.json",
             "seeds/shared_arousal.json"],
            capture_output=True, text=True, timeout=10, cwd=".",
        )
    except Exception:
        pytest.skip("git unavailable")
    assert out.returncode == 0
    assert out.stdout.strip() == "", out.stdout
