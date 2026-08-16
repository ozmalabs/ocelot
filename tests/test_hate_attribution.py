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
    first = record_hate_incident(inner, mt, pat, negative=True)
    r = record_hate_incident(inner, mt, pat, negative=True)
    assert r["attribution_locus"] == "global_other"
    # HATE_STABILITY_AROUSAL_COUPLING_PREREG.md Sec2: streak_increment is
    # 1+arousal_level (read BEFORE this incident's own update), not a bare
    # +1 -- at incident 0's post-update arousal this is 1+0.8=1.8, not 1.
    assert r["confirm_streak"] == pytest.approx(1.0 + first["arousal_level"])


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
    r0 = record_hate_incident(inner, mt, pat, negative=True)
    r_confirm = record_hate_incident(inner, mt, pat, negative=True)
    assert r_confirm["confirm_streak"] == pytest.approx(1.0 + r0["arousal_level"])
    r_exception = record_hate_incident(inner, mt, pat, negative=False)
    assert r_exception["attribution_locus"] == "specific_act"
    assert r_exception["confirm_streak"] == 0
    r_after = record_hate_incident(inner, mt, pat, negative=True)
    assert r_after["attribution_locus"] == "global_other"
    # streak reset to 0 by the exception, then incremented by
    # 1+arousal_level -- arousal itself is UNAFFECTED by the reset (every
    # incident contributes regardless of locus), so this is 1 +
    # r_exception's own post-update arousal_level, not 1.
    assert r_after["confirm_streak"] == pytest.approx(1.0 + r_exception["arousal_level"])


# ---------------------------------------------------------------------
# 5. Crystallization requires the threshold, not the first confirmation.
# ---------------------------------------------------------------------
def test_crystallization_requires_the_stability_threshold():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    # HATE_STABILITY_AROUSAL_COUPLING_PREREG.md Sec2: confirm_streak
    # increments by 1+arousal_level, not a bare +1 -- with arousal
    # compounding across back-to-back confirming incidents the streak
    # OVERSHOOTS HATE_STABILITY_THRESHOLD rather than landing on it
    # exactly, so drive incidents until crystallization is observed
    # instead of assuming a fixed call count.
    results = []
    for _ in range(10):
        r = record_hate_incident(inner, mt, pat, negative=True)
        results.append(r)
        if r["crystallized_this_call"]:
            break
    else:
        pytest.fail("did not crystallize within 10 incidents")
    for r in results[:-1]:
        assert not r["crystallized"]
    assert results[-1]["crystallized"]
    assert results[-1]["confirm_streak"] >= HATE_STABILITY_THRESHOLD
    # the FIRST global_other confirmation alone is not enough -- it takes
    # at least two confirming incidents even with arousal amplification
    global_other_before_crystallizing = [r for r in results[:-1] if r["attribution_locus"] == "global_other"]
    assert len(global_other_before_crystallizing) >= 1


# ---------------------------------------------------------------------
# 6. removal_desire only receives evidence on the crystallizing incident.
# ---------------------------------------------------------------------
def test_removal_desire_evidence_gated_on_crystallization():
    inner, mt = _fresh()
    pat = mint_target_pattern(inner, mt, "Alex")
    results = []
    for _ in range(10):
        r = record_hate_incident(inner, mt, pat, negative=True)
        results.append(r)
        if r["crystallized_this_call"]:
            break
    else:
        pytest.fail("did not crystallize within 10 incidents")
    for r in results[:-1]:
        assert r["removal_desire_external_field"] == 0.0
    crystallizing = results[-1]
    assert crystallizing["removal_desire_external_field"] > 0.0
    after = record_hate_incident(inner, mt, pat, negative=True)
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
