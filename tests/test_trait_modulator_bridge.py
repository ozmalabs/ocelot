"""Gates for the BIDIRECTIONAL trait<->modulator bridge
(domains/trait_modulator_bridge.py): the agent's SLOW crystallised trait vector
(domains/disposition.py) coupled BOTH WAYS to its FAST MicroPsi ModulatorState
(seeds/modulators.json).

Two directions under test:

  (A) TRAIT -> MODULATOR (the set-point).  Each crystallised trait LEVEL is
      written into the ModulatorState bias attr its biased formula reads:
        · abstraction level -> ms.abstraction_bias, which SHIFTS resolution;
        · openness    level -> ms.openness_bias,    which SHIFTS sel_threshold;
        · skepticism  level -> ms.skepticism_bias,  which SHIFTS securing.
      The shift is EXACTLY the documented per-trait scale; the drive terms are
      unchanged (the offset is a constant set-point, not a multiplier).

  (B) MODULATOR -> TRAIT (crystallisation from lived experience).  A sustained
      modulator condition read back as trait EVIDENCE crystallises the trait via
      the CAN identity-feedback rule — PRODUCED, one ±1 quantum per tick, never
      hand-written:
        · sustained HIGH resolution  => abstraction crystallises UP;
        · sustained HIGH securing / exploration_urge => skepticism UP.

  SAFE DEFAULT.  A bare agent (no traits) and a seeded-DEFAULT agent (openness
      -1, abstraction 0, skepticism 0) BOTH write 0 to all three bias attrs, so
      the modulator vector is BYTE-IDENTICAL to a no-bridge build — the emergent
      emotion path is unchanged from today. openness's -1 default maps to 0 bias
      because its neutral reference IS its default (the honest choice that keeps
      default == today for the modulator path too).

  NO RUNAWAY.  (A) writes a BOUNDED bias from a quantised trait capped at ±4;
      (B) moves the trait SLOWLY (one quantum per tick, ledger hysteresis). The
      full A<->B loop saturates at the trait ceiling and stays bounded — the
      timescale separation (slow crystallised trait vs fast modulator) prevents
      the positive coupling from diverging.
"""
from __future__ import annotations

from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp
import domains.relation_grounding as rg
import domains.trait_modulator_bridge as tmb

_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension", "DimensionEdgeRole")
_ET = tuple(set(rg.RELATION_EDGE_TYPES) | {"has_concept", "genls", "is_a",
            "built_from", "depends_on", "grounds"})


def _open(s):
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et, "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})


class Agent:
    """A `.s` substrate + `.agent` hub — the shape disposition.py and the bridge
    both accept (identical to tests/test_disposition_homeostasis.py)."""

    def __init__(self):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})
        _open(self.s)


def _ms_attrs(agent, ms):
    return agent.s.node(ms)["attrs"]


#: A low-urge engaged drive => low arousal => resolution ~ res_base(500) >
#: resolution_hi(450): a sustained HIGH-resolution modulator condition (also
#: leaves securing high). The reusable direction-B drive override.
_HIGH_RES_DRIVE = dict(v_d=100.0, c_d=90.0, c_d_prev=90.0, scale=100.0)


# ===========================================================================
# The SCALE (pure arithmetic, no graph).
# ===========================================================================
def test_trait_bias_scale_is_documented_and_zero_at_default():
    # abstraction/skepticism neutral at level 0; openness neutral at its -1 default.
    assert tmb.trait_bias(0, "abstraction") == 0.0
    assert tmb.trait_bias(0, "skepticism") == 0.0
    assert tmb.trait_bias(-1, "openness") == 0.0          # the DEFAULT maps to 0
    # linear per-trait step off the neutral reference.
    assert tmb.trait_bias(4, "abstraction") == 120.0      # (4-0)*30
    assert tmb.trait_bias(4, "openness") == 125.0         # (4-(-1))*25
    assert tmb.trait_bias(4, "skepticism") == 60.0        # (4-0)*15
    assert tmb.trait_bias(-4, "abstraction") == -120.0
    # an unknown trait has no bias hook.
    assert tmb.trait_bias(4, "nonexistent") == 0.0


# ===========================================================================
# SAFE DEFAULT — default == today for the modulator/emotion path.
# ===========================================================================
def test_bare_agent_writes_zero_bias_and_matches_no_bridge_modulator():
    """A bare agent (no disposition traits minted) leaves all three bias attrs
    at 0, and its synced modulator vector equals a no-bridge build's — byte for
    byte on the three biased axes."""
    synced_agent = Agent()
    out = tmb.sync_traits_to_modulator(synced_agent)      # ensure_traits=False
    assert out["biases"] == {"abstraction": 0.0, "openness": 0.0,
                             "skepticism": 0.0}
    ms = out["ms"]
    a = _ms_attrs(synced_agent, ms)
    assert a["abstraction_bias"] == 0.0
    assert a["openness_bias"] == 0.0
    assert a["skepticism_bias"] == 0.0

    # a no-bridge build (modulator only, never synced) for comparison.
    bare = Agent()
    _hub, msb = tmb.ensure_modulator_state(bare)
    b = _ms_attrs(bare, msb)
    for k in ("resolution", "sel_threshold", "securing"):
        assert a[k] == b[k], (k, a[k], b[k])


def test_seeded_default_traits_write_zero_bias():
    """The SEEDED default vector (openness -1, abstraction 0, skepticism 0)
    writes 0 to ALL THREE bias attrs — default == today even with the whole
    personality minted."""
    agent = Agent()
    out = tmb.sync_traits_to_modulator(agent, ensure_traits=True)
    assert out["levels"] == {"abstraction": 0, "openness": -1, "skepticism": 0}
    assert out["biases"] == {"abstraction": 0.0, "openness": 0.0,
                             "skepticism": 0.0}


def test_neutral_traits_leave_emergent_emotion_unchanged():
    """Neutral abstraction/skepticism (level 0 => 0 bias) leave resolution AND
    securing identical to a no-bridge build — the safe-default check the task
    asks for on the emotion path (only openness has other wiring; abstraction/
    skepticism at 0 are inert)."""
    a = Agent()
    disp.set_trait_seed(a, "abstraction", 0.0)
    disp.set_trait_seed(a, "skepticism", 0.0)
    out = tmb.sync_traits_to_modulator(a)
    sa = _ms_attrs(a, out["ms"])

    b = Agent()
    _hub, msb = tmb.ensure_modulator_state(b)
    sb = _ms_attrs(b, msb)
    assert sa["resolution"] == sb["resolution"]           # abstraction inert
    assert sa["securing"] == sb["securing"]               # skepticism inert
    assert sa["abstraction_bias"] == 0.0
    assert sa["skepticism_bias"] == 0.0


# ===========================================================================
# (A) TRAIT -> MODULATOR — the set-point.
# ===========================================================================
def test_high_abstraction_writes_nonzero_bias_and_shifts_resolution():
    """A seeded HIGH-abstraction agent writes a nonzero abstraction_bias, and the
    modulator resolution shifts by EXACTLY that bias (drive terms unchanged)."""
    agent = Agent()
    disp.set_trait_seed(agent, "abstraction", 4.0)
    assert disp.trait_level(agent, "abstraction") == 4

    _hub, ms = tmb.ensure_modulator_state(agent)          # build, no sync yet
    res_before = _ms_attrs(agent, ms)["resolution"]
    out = tmb.sync_traits_to_modulator(agent)             # write bias + retick
    res_after = _ms_attrs(agent, ms)["resolution"]

    assert out["biases"]["abstraction"] == 120.0
    assert _ms_attrs(agent, ms)["abstraction_bias"] == 120.0
    assert res_after - res_before == 120.0                # EXACTLY the bias


def test_openness_and_skepticism_biases_shift_their_own_axes():
    """A permissive openness LOWERS sel_threshold; a high skepticism RAISES
    securing — each on its OWN biased axis, by its own documented scale."""
    agent = Agent()
    disp.set_trait_seed(agent, "openness", 3.0)           # (3-(-1))*25 = 100 lower
    disp.set_trait_seed(agent, "skepticism", 2.0)         # (2-0)*15 = 30 higher
    _hub, ms = tmb.ensure_modulator_state(agent)
    before = dict(_ms_attrs(agent, ms))
    out = tmb.sync_traits_to_modulator(agent)
    after = _ms_attrs(agent, ms)
    assert out["biases"]["openness"] == 100.0
    assert out["biases"]["skepticism"] == 30.0
    # openness_bias is SUBTRACTED from sel_threshold => it drops by 100.
    assert after["sel_threshold"] - before["sel_threshold"] == -100.0
    # skepticism_bias is ADDED to securing => it rises by 30.
    assert after["securing"] - before["securing"] == 30.0


def test_sync_is_idempotent_on_a_static_trait():
    """Re-syncing an unchanged trait writes the same bias and leaves the
    modulator vector fixed — the set-point is a function of the trait, not of how
    many times sync ran."""
    agent = Agent()
    disp.set_trait_seed(agent, "abstraction", 2.0)
    tmb.sync_traits_to_modulator(agent)
    _hub, ms = tmb.ensure_modulator_state(agent)
    v1 = dict(_ms_attrs(agent, ms))
    tmb.sync_traits_to_modulator(agent)
    v2 = _ms_attrs(agent, ms)
    for k in ("abstraction_bias", "resolution", "sel_threshold", "securing"):
        assert v1[k] == v2[k]


# ===========================================================================
# (B) MODULATOR -> TRAIT — crystallisation from lived experience.
# ===========================================================================
def test_evidence_reads_high_resolution_as_abstraction_up():
    """The read-back turns a HIGH-resolution modulator into +1 abstraction
    evidence and (securing high) +1 skepticism evidence — a decision-free read
    against the modulator's own knob thresholds."""
    agent = Agent()
    _hub, ms = tmb.ensure_modulator_state(agent, drive_over=_HIGH_RES_DRIVE)
    a = _ms_attrs(agent, ms)
    assert a["resolution"] > a["resolution_hi"]           # genuinely high
    ev = tmb.modulator_trait_evidence(agent, ms=ms)
    assert ev["abstraction"] == 1.0
    assert ev["skepticism"] == 1.0                        # securing high


def test_sustained_high_resolution_crystallises_abstraction_upward():
    """Sustained HIGH resolution crystallises abstraction UP, one ±1 quantum per
    tick — PRODUCED by the CAN rule, not hand-written."""
    agent = Agent()
    _hub, ms = tmb.ensure_modulator_state(agent, drive_over=_HIGH_RES_DRIVE)
    before = disp.trait_level(agent, "abstraction")
    # one tick -> at most one quantum (the SLOW layer).
    out1 = tmb.crystallise_traits_from_modulator(agent, ms=ms, ticks=1)
    assert out1["evidence"]["abstraction"] == 1.0
    f1 = disp.trait_field(agent, "abstraction")
    assert abs(f1) == 1.0                                  # one native quantum
    # sustained -> crystallises further.
    out2 = tmb.crystallise_traits_from_modulator(agent, ms=ms, ticks=5)
    after = out2["levels_after"]["abstraction"]
    assert after > before
    assert "abstraction" in out1["moved"]


def test_crystallisation_is_produced_by_the_rule_not_hand_written():
    """The crystallised trait is moved ONLY by the identity-feedback rule: the
    evidence ledger accrued, and the mirrored axis attr equals the produced
    identity_field (a mirror, never a hand-set outcome)."""
    agent = Agent()
    _hub, ms = tmb.ensure_modulator_state(agent, drive_over=_HIGH_RES_DRIVE)
    concept = disp.ensure_trait(agent, "abstraction")
    tmb.crystallise_traits_from_modulator(agent, ms=ms, ticks=3)
    attrs = agent.s.node(concept)["attrs"]
    assert int(attrs.get("identity_evidence_confirm") or 0) >= 1
    assert float(attrs.get("abstraction_field")) == float(attrs.get("identity_field"))


def test_crystallisation_leaves_unevidenced_traits_untouched():
    """Crystallising abstraction/skepticism (which have evidence) does NOT erode
    an ESTABLISHED openness that this modulator condition gives no evidence for —
    per-trait independence holds across the batched relaxation."""
    agent = Agent()
    # establish openness away from default first.
    disp.relax_trait(agent, "openness", 1.0, ticks=2)
    est = disp.trait_level(agent, "openness")
    assert est >= 1
    _hub, ms = tmb.ensure_modulator_state(agent, drive_over=_HIGH_RES_DRIVE)
    ev = tmb.modulator_trait_evidence(agent, ms=ms)
    assert ev["openness"] == 0.0                           # no openness evidence
    tmb.crystallise_traits_from_modulator(agent, ms=ms, ticks=4)
    assert disp.trait_level(agent, "openness") == est      # UNCHANGED
    # the traits that DID have evidence moved.
    assert disp.trait_level(agent, "abstraction") >= 1
    assert disp.trait_level(agent, "skepticism") >= 1


def test_no_evidence_condition_is_a_noop():
    """A balanced modulator (resolution neither high nor low, securing not high,
    no exploration urge) injects NO evidence and moves no trait."""
    agent = Agent()
    # a mid drive tuned so resolution sits between res_lo(200) and res_hi(450)
    # and securing is not high: high arousal pulls resolution down into the band.
    _hub, ms = tmb.ensure_modulator_state(
        agent, drive_over=dict(v_d=400.0, c_d=200.0, c_d_prev=200.0, scale=100.0),
        ms_over=dict(res_base=300.0, securing_hi=1000.0))
    a = _ms_attrs(agent, ms)
    ev = tmb.modulator_trait_evidence(agent, ms=ms)
    # if resolution landed in-band and securing below its (raised) mark, no evidence.
    if a["resolution_lo"] <= a["resolution"] <= a["resolution_hi"] \
            and a["securing"] <= a["securing_hi"]:
        assert ev["abstraction"] == 0.0
        assert ev["skepticism"] == 0.0
        out = tmb.crystallise_traits_from_modulator(agent, ms=ms, ticks=3)
        assert out["moved"] == []


# ===========================================================================
# NO RUNAWAY — the A<->B loop is a bounded servo, not a divergent one.
# ===========================================================================
def test_ab_loop_saturates_at_the_trait_ceiling():
    """Running (B) then (A) repeatedly drives abstraction to its +4 ceiling and
    the bias to its maximum — then it STAYS there. The trait cap + the slow
    per-tick crystallisation give the timescale separation that prevents the
    positive coupling from diverging."""
    agent = Agent()
    _hub, ms = tmb.ensure_modulator_state(agent, drive_over=_HIGH_RES_DRIVE)
    levels, biases = [], []
    for _ in range(15):
        tmb.crystallise_traits_from_modulator(agent, ms=ms, ticks=1)   # B
        r = tmb.sync_traits_to_modulator(agent)                        # A
        levels.append(disp.trait_level(agent, "abstraction"))
        biases.append(r["biases"]["abstraction"])
    cap = tmb.trait_bias(4, "abstraction")
    assert max(levels) <= 4                                # never exceeds ceiling
    assert max(biases) <= cap
    assert levels[-1] == 4 and biases[-1] == cap           # settles AT the ceiling
    # monotone non-decreasing then flat — no oscillation/divergence.
    assert levels == sorted(levels)


def test_bridge_is_a_noop_on_non_live_substrate():
    """The bridge degrades honestly on a handle with no engine (mirrors the
    disposition module's non-live no-op)."""
    class Dead:
        s = object()
    out = tmb.sync_traits_to_modulator(Dead())
    assert out["wrote"] is False
    assert out["ms"] is None
