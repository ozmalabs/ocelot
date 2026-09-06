"""BLOCK 296000 — PHASIC vs TONIC AROUSAL, a missing affect DIMENSION.

Prereg: `docs/research/psychology_affect/PHASIC_AROUSAL_DIMENSION_PREREG.md`.

The substrate collapsed PHASIC (onset/startle/action-readiness) and TONIC
(sustained) arousal onto one arousal scalar. For a threat drive that scalar is the
DECAYED threat_precision, so FEAR (whose precision has decayed — the very thing
that distinguishes it from anxiety) read LOW arousal, inverting RAVDESS (fear is
near-top, vocally loud/high-F0). The phasic signal was ALREADY computed and thrown
away: `threat_c0` (the un-decayed ONSET magnitude, 1024 for fear) is the head of
the same freshness Ashr that yields the decayed precision — read only inside
`drive_threat_precision`, never routed to arousal.

This rung adds a NEW additive PHASIC axis: a per-drive `arousal_contrib_phasic`
(threat_c0 for threat drives, the SAME urge*urgency//SCALE else-branch otherwise)
and a modulator-level `arousal_phasic` / `arousal_band_phasic` (residual path
unchanged, bands by the SAME band_hi/band_mid). Nothing existing reads the new
attrs; emotion classification keeps reading the TONIC arousal_band. This file
gates:

  (a) ADDITIVE — all 11 canonical emotions' TONIC arousal_band + emotion labels
      (+ tendency, valence, n_fired) are BYTE-IDENTICAL with the phasic axis
      present (default == today); the phasic attrs are the ONLY additions.
  (b) SEPARATED — fear reads arousal_band_phasic HIGH(2) while its tonic
      arousal_band stays LOW(0): the collapsed dimension recovered.
  (c) GEOMETRY — calm/sad phasic band LOW; anxiety/anger phasic band HIGH.
  (d) NO NEW CONSTANT — the phasic contribution uses ONLY existing signals
      (threat_c0 / urge*urgency): the emitted seed rules introduce no new Lit
      constant beyond the ones the tonic rules already use, and the .so is
      byte-identical (SEED-ONLY change).

SEED-ONLY: `_native.abi3.so` md5 UNCHANGED (7efe75…); the change is two rules in
the emitter + regenerated seeds/{drives,modulators}.json, NO Rust."""
import hashlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.modulator_emergence_measure import (          # noqa: E402
    CANON, BLEND_CANON, CORE, BLEND, TEND, VAL_OF, BAND_OF, _case)

CANON_MD5 = "7efe75eba05b006cafd15dbb4b7da246"


# ------------------------------------------------------- (a) ADDITIVE / default==today
def test_phasic_axis_is_purely_additive_canonical_byte_identical():
    """All 11 canonical emotions reproduce byte-identically on the TONIC axis with
    the phasic axis present: same emotion label, action_tendency, valence, tonic
    arousal_band, one-fire-each. The phasic axis reads NOTHING that classification
    reads, so it cannot move any canonical emotion (default == today)."""
    for nm in CORE:
        a, fired = _case(*CANON[nm])
        assert fired == [nm], (nm, fired)
        assert int(a["action_tendency"]) == TEND[nm], (nm, a["action_tendency"])
        assert int(a["emotion"]) == TEND[nm], (nm, a["emotion"])
        assert int(a["valence"]) == VAL_OF[nm], (nm, a["valence"])
        assert int(a["arousal_band"]) == BAND_OF[nm], (nm, a["arousal_band"])
        assert int(a["n_fired"]) == 1 and int(a["n_blend"]) == 0, nm
        # the phasic attrs are PRESENT (the new axis exists) ...
        assert "arousal_phasic" in a and "arousal_band_phasic" in a, nm


def test_phasic_axis_does_not_disturb_blends():
    """The 3 free blend regions (bliss/angst/grief) still fire only their own hit
    with no core emotion — the phasic axis is inert to classification."""
    for nm in BLEND:
        a, fired = _case(*BLEND_CANON[nm])
        assert fired == [nm], (nm, fired)
        assert int(a["n_fired"]) == 0, (nm, a["n_fired"])


# ------------------------------------------------------- (b) SEPARATED (fear)
def test_fear_phasic_high_tonic_low_dimension_separated():
    """THE HEADLINE: fear reads arousal_band_phasic HIGH(2) via its threat_c0 ONSET
    (1024 >= band_hi 600) while its TONIC arousal_band stays LOW(0) via the decayed
    threat_precision (128 < band_mid 150). The dimension the substrate had collapsed
    onto one scalar is recovered — fear is phasic-HIGH, tonic-LOW."""
    a, fired = _case(*CANON["fear"])
    assert fired == ["fear"]
    assert int(a["arousal_band"]) == 0, ("tonic", a["arousal_band"])
    assert int(a["arousal_band_phasic"]) == 2, ("phasic", a["arousal_band_phasic"])
    # the scalars: tonic decayed precision LOW, phasic onset HIGH.
    assert int(a["arousal"]) == 128, a["arousal"]
    assert int(a["arousal_phasic"]) == 1024, a["arousal_phasic"]


# ------------------------------------------------------- (c) GEOMETRY
def test_calm_and_sad_phasic_band_low():
    """calm (bliss region) and sad have NO threat channel, so their phasic
    contribution takes the SAME urge*urgency//SCALE branch as tonic and stays LOW —
    fear cannot be raised by a mechanism that would also raise the low emotions."""
    a_calm, _ = _case(*BLEND_CANON["bliss"])       # calm -> bliss region
    a_sad, _ = _case(*CANON["sadness"])
    assert int(a_calm["arousal_band_phasic"]) == 0, a_calm["arousal_band_phasic"]
    assert int(a_sad["arousal_band_phasic"]) == 0, a_sad["arousal_band_phasic"]


def test_anxiety_and_anger_phasic_band_high():
    """anxiety shares fear's threat onset (threat_c0=1024) so it is ALSO phasic-HIGH
    (correct: anxiety is high-arousal on both axes). anger's urge*urgency is already
    high on both axes (no threat channel). So the phasic axis is not a fear-only
    special case, and anger stays HIGH without any threat contribution."""
    a_anx, _ = _case(*CANON["anxiety"])
    a_ang, _ = _case(*CANON["anger"])
    assert int(a_anx["arousal_band_phasic"]) == 2, a_anx["arousal_band_phasic"]
    assert int(a_ang["arousal_band_phasic"]) == 2, a_ang["arousal_band_phasic"]
    # anxiety is HIGH on both axes (onset persists); anger HIGH on both.
    assert int(a_anx["arousal_band"]) == 2 and int(a_ang["arousal_band"]) == 2


# ------------------------------------------------------- (d) NO NEW CONSTANT / SEED-ONLY
def _collect_lits(term, acc):
    if isinstance(term, dict):
        if term.get("type") == "Lit":
            acc.add(term["value"])
        for k in ("a", "b", "arg", "cond", "then", "other", "node", "source", "value"):
            if k in term:
                _collect_lits(term[k], acc)
        for x in term.get("items", []):
            _collect_lits(x, acc)
    return acc


def test_phasic_contrib_uses_only_existing_signals_no_new_constant():
    """The phasic rules use ONLY existing signals — threat_c0 (the onset attr, which
    PRE-DATES this rung) and urge*urgency//SCALE — and introduce NO new numeric
    constant beyond the ones the tonic arousal rules already use. Every Lit in the
    two new rules also appears in a tonic arousal rule; every attribute they READ is
    an attribute the tonic rules already read (only the WRITE targets are new)."""
    drives = json.load(open(os.path.join(ROOT, "seeds", "drives.json")))
    mods = json.load(open(os.path.join(ROOT, "seeds", "modulators.json")))
    dr = {r["name"]: r for r in drives["rules"]}
    mo = {r["name"]: r for r in mods["rules"]}

    # the new rules exist
    assert "drive_arousal_contrib_phasic" in dr
    assert "mod_arousal_phasic" in mo

    def rule_lits(r):
        acc = set()
        for eff in r.get("effects", []):
            if isinstance(eff, list) and len(eff) >= 4 and isinstance(eff[3], dict):
                _collect_lits(eff[3].get("__term__", {}), acc)
        _collect_lits(r.get("where", {}), acc)
        return acc

    # phasic-contrib Lits ⊆ tonic-contrib Lits (same guard 1.0, same threat==1)
    tonic_c = rule_lits(dr["drive_arousal_contrib"])
    phasic_c = rule_lits(dr["drive_arousal_contrib_phasic"])
    assert phasic_c <= tonic_c, (phasic_c - tonic_c)

    # phasic-arousal Lits ⊆ tonic-arousal Lits (same band cuts 0/1/2, same guard)
    tonic_a = rule_lits(mo["mod_arousal"])
    phasic_a = rule_lits(mo["mod_arousal_phasic"])
    assert phasic_a <= tonic_a, (phasic_a - tonic_a)

    # the ONLY attribute the phasic threat branch reads that the tonic one does not
    # is threat_c0 (the onset) — replacing threat_precision (the decay). Confirm the
    # phasic rule reads threat_c0 and the tonic rule reads threat_precision.
    assert "threat_c0" in json.dumps(dr["drive_arousal_contrib_phasic"])
    assert "threat_precision" in json.dumps(dr["drive_arousal_contrib"])
    # and the phasic contrib does NOT read the decayed precision.
    assert "threat_precision" not in json.dumps(dr["drive_arousal_contrib_phasic"])


def test_phasic_axis_read_by_nothing_but_prosody():
    """No seed RULE reads the phasic attrs — they are additive outputs. Every
    emx_* region predicate and mod_resolution read the TONIC arousal/arousal_band,
    never the phasic ones. (The prosody world adapter reads the phasic band; that
    is Python, not a seed rule.)"""
    mods = json.load(open(os.path.join(ROOT, "seeds", "modulators.json")))
    for r in mods["rules"]:
        if r["name"] == "mod_arousal_phasic":
            continue  # the only writer
        blob = json.dumps(r)
        assert "arousal_phasic" not in blob, r["name"]
        assert "arousal_band_phasic" not in blob, r["name"]
    drives = json.load(open(os.path.join(ROOT, "seeds", "drives.json")))
    for r in drives["rules"]:
        if r["name"] == "drive_arousal_contrib_phasic":
            continue
        assert "arousal_contrib_phasic" not in json.dumps(r), r["name"]


def test_seed_only_so_md5_unchanged():
    """SEED-ONLY change: the cognition core .so is byte-identical."""
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs",
                      "_native.abi3.so")
    assert os.path.exists(so), so
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
    assert md5 == CANON_MD5, f"native .so changed: {md5}"
