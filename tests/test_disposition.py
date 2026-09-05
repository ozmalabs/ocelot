"""Gates for DISPOSITION as a REAL CAN-relaxable DYNAMICAL QUALIA AXIS on the
agent (domains/disposition.py + the `dynamical:disposition` /
`dynamical:disposition_pull` axes in seeds/qualia_space.json).

The premise: the agent's cognitive disposition (conservative ↔ permissive — its
willingness to mint referents / form associations) is not a static config knob
but a felt scalar the substrate genuinely RELAXES and CRYSTALLISES, the
structural twin of self-worth (domains/can_self_worth_bridge.py). It is SEEDED
with a starting temperament (a tweak) but PRODUCED/moved by the SAME native
identity dynamics (can_native_identity_field_feedback) as any crystallised
feeling.

These gates pin exactly that:

  1. ensure_disposition is idempotent and mints a SAFE-DEFAULT (mildly
     conservative) starting temperament on a fresh agent — today's behaviour.
  2. DISTRIBUTION: two agents seeded at different points read two DISTINCT
     standing disposition_levels — people sit on a distribution.
  3. MOVEMENT: disposition_field is MOVED by relaxation from evidence (produced
     by the CAN rule, not hand-written) — the trait shifts, and a genuinely
     GRADED shift (distinct intermediate levels), not a saturating jump.
  4. SIGNATURE: `dynamical:disposition` appears as a coordinate in the agent's
     own qualia signature, and the live `dynamical:disposition_pull` appears
     only in the overlay (the unsettled point).
  5. The axis GRADES (does not saturate like commitment) — the honest headline.
"""
from __future__ import annotations

import json
import pathlib

import substrate_rs as sr
from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp

ROOT = pathlib.Path(disp.__file__).resolve().parent.parent
QUALIA = ROOT / "seeds" / "qualia_space.json"


class _Agent:
    """A `.s` substrate handle + an `.agent` hub node — the shape
    domains/disposition.py accepts (getattr(agent, 's', agent))."""
    def __init__(self):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})


def _agent():
    return _Agent()


def _disp_dims(sig):
    return {t[0] for t in sig}


def _disp_coord(sig):
    for t in sig:
        if t[0] == "dynamical:disposition":
            return t
    return None


# ---------------------------------------------------------------------------
# 1. ensure_disposition — idempotent + seeded SAFE DEFAULT
# ---------------------------------------------------------------------------
def test_ensure_disposition_idempotent_and_seeded_default():
    a = _agent()
    c1 = disp.ensure_disposition(a)
    c2 = disp.ensure_disposition(a)
    assert c1 is not None
    assert c1 == c2, "ensure_disposition must be idempotent (first-found wins)"

    # exactly one disposition Mt + one disposition Concept — never a second.
    inner = a.s
    mts = [m for m in inner.nodes("Microtheory")
           if inner.node(m)["attrs"].get("name") == disp.DISPOSITION_MT_NAME]
    concepts = [n for n in inner.nodes("Concept")
                if inner.node(n)["attrs"].get("name") == disp.DISPOSITION_CONCEPT_NAME]
    assert len(mts) == 1 and len(concepts) == 1

    # the SAFE DEFAULT is today's mildly-conservative behaviour.
    assert disp.disposition_level(a) == int(disp.DEFAULT_DISPOSITION_SEED)
    assert disp.DEFAULT_DISPOSITION_SEED < 0, "default temperament is conservative"


def test_disposition_field_ensure_false_reads_default_without_minting():
    """A default run adds NOTHING to the graph — reading with ensure=False on a
    fresh graph returns the safe default and mints no node (the auto_approve.
    get_policy discipline)."""
    a = _agent()
    val = disp.disposition_field(a, ensure=False)
    assert val == float(disp.DEFAULT_DISPOSITION_SEED)
    # no disposition Mt was minted by a pure read.
    inner = a.s
    mts = [m for m in inner.nodes("Microtheory")
           if inner.node(m)["attrs"].get("name") == disp.DISPOSITION_MT_NAME]
    assert mts == []


# ---------------------------------------------------------------------------
# 2. DISTRIBUTION — two seeds → two distinct disposition_level readings
# ---------------------------------------------------------------------------
def test_two_seeds_give_two_distinct_disposition_levels():
    conservative = _agent()
    disp.set_disposition_seed(conservative, -3.0)
    open_minded = _agent()
    disp.set_disposition_seed(open_minded, +2.0)

    lc = disp.disposition_level(conservative)
    lo = disp.disposition_level(open_minded)
    assert lc == -3
    assert lo == +2
    assert lc != lo, "distinct seeds must place agents at distinct standing levels"


def test_seed_tweak_places_agent_on_the_distribution():
    """set_disposition_seed is a STARTING-POINT tweak: it (re)writes the standing
    trait and reads back the new level, from anywhere on the axis."""
    a = _agent()
    for seed, expect in [(-4.0, -4), (-1.0, -1), (0.0, 0), (2.0, 2), (4.0, 4)]:
        assert disp.set_disposition_seed(a, seed) == expect


# ---------------------------------------------------------------------------
# 3. MOVEMENT — disposition_field MOVED by relaxation from evidence (produced)
# ---------------------------------------------------------------------------
def test_disposition_field_moves_under_relaxation_from_evidence():
    """The trait is PRODUCED by the CAN identity rule, not set by us: seed a
    neutral agent, feed sustained openness evidence, and the standing field must
    move positive — driven by can_native_identity_field_feedback, then mirrored.
    We assert MOVEMENT and DIRECTION, never a hand-written target."""
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    assert disp.disposition_field(a) == 0.0

    before = disp.disposition_field(a)
    disp.relax_disposition(a, +1.0, ticks=3)
    after = disp.disposition_field(a)
    assert after > before, "sustained openness evidence must move the trait up"
    assert disp.disposition_level(a) > 0

    # and it is reversible under sustained counter-evidence (real dynamics, not
    # a ratchet): drive negative long enough to overcome the built ledger.
    disp.relax_disposition(a, -1.0, ticks=12)
    assert disp.disposition_field(a) < after, "sustained counter-evidence reverses it"
    assert disp.disposition_level(a) < 0


def test_movement_is_graded_not_saturating():
    """The HEADLINE honest claim: disposition GRADES. Under consecutive
    +evidence ticks the level must pass through DISTINCT intermediate
    coordinates (1, then 2, then 3, …) before clamping — unlike commitment,
    which would jump straight to the clamp on the first committed tick."""
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    levels = [disp.relax_disposition(a, +1.0, ticks=1) for _ in range(6)]
    # strictly increasing through the graded band, then clamped at +4.
    assert levels[0] == 1 and levels[1] == 2 and levels[2] == 3 and levels[3] == 4
    assert {1, 2, 3, 4} <= set(levels), levels
    assert max(levels) == 4, "clamps at half_width, does not run away"
    # the graded band has >= 4 distinct positive levels — genuine spread, not
    # the 1-level saturation of dynamical:commitment.
    assert len({lv for lv in levels if lv > 0}) >= 4


def test_pure_flip_flop_from_neutral_stays_neutral():
    """An UNESTABLISHED trait fed equal +/− evidence stays near neutral — the
    ledger balances, the render is neutral, the field decays toward zero. Real
    CAN behaviour (the same clamp-toward-zero the identity rule uses)."""
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    for _ in range(10):
        disp.relax_disposition(a, +1.0, ticks=1)
        disp.relax_disposition(a, -1.0, ticks=1)
    assert disp.disposition_level(a) == 0
    assert abs(disp.disposition_field(a)) <= 1.0


# ---------------------------------------------------------------------------
# 4. SIGNATURE — dynamical:disposition appears in the agent's own signature
# ---------------------------------------------------------------------------
def test_dynamical_disposition_appears_in_the_signature():
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    disp.relax_disposition(a, +1.0, ticks=3)   # settle a +3 standing trait

    sig = disp.disposition_signature(a)
    assert "dynamical:disposition" in _disp_dims(sig), sig
    coord = _disp_coord(sig)
    assert coord is not None
    assert coord[1] == "field"
    assert coord[2] == 3, ("the standing coordinate is the produced, quantised "
                           "trait", coord)


def test_live_disposition_pull_is_overlay_only_the_unsettled_point():
    """A LIVE momentary pull (external_field) with no crystallised movement is
    the unsettled point: `dynamical:disposition_pull` present in the OVERLAY,
    `dynamical:disposition` absent from the standing signature. The gap between
    them is 'I'm being pulled to open up but my temperament hasn't moved.'"""
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    disp.pull_disposition(a, +3.0)

    cryst = disp.disposition_signature(a)
    over = disp.disposition_signature(a, overlay=True)
    # no crystallised disposition yet (standing field is still 0)...
    assert "dynamical:disposition" not in _disp_dims(cryst)
    # ...but a live pull is present in the overlay.
    assert "dynamical:disposition_pull" in _disp_dims(over)
    # the pull axis is overlay-only (never in the crystallised signature).
    assert "dynamical:disposition_pull" not in _disp_dims(cryst)


# ---------------------------------------------------------------------------
# 5. The axis exists in the regenerated seed with the graded quantum
# ---------------------------------------------------------------------------
def test_seed_declares_graded_disposition_axis():
    """The seed must declare `dynamical:disposition` on `field:disposition_field`
    with quantum=1.0 (the field's own integer step → genuine spread), and the
    overlay `dynamical:disposition_pull` on `field:disposition_external`."""
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    s.load_seed_manifest(json.load(open(ROOT / "seeds" / "shape_vocabulary.json")), ag)
    summ = s.load_seed_manifest(json.load(open(QUALIA)), ag)
    assert summ.get("rules_skipped") == []

    dims = {s.node(n)["attrs"]["name"]: s.node(n)["attrs"]
            for n in s.nodes("QualiaDimension")}
    assert "dynamical:disposition" in dims
    assert "dynamical:disposition_pull" in dims

    d = dims["dynamical:disposition"]
    assert d["source"] == "field:disposition_field"
    assert float(d["quantum"]) == 1.0, "quantum=1.0 == the field's own integer step"
    assert float(d["half_width"]) == 4.0
    assert not d.get("overlay"), "the standing trait is crystallised, not overlay"

    p = dims["dynamical:disposition_pull"]
    assert p["source"] == "field:disposition_external"
    assert p.get("overlay"), "the live pull is an overlay axis"



# ---------------------------------------------------------------------------
# 6. CRYSTALLISATION / PERSISTENCE — the identity-field property (can_ops.rs):
#    "Identity is NEVER frozen — strong-enough external evidence still overcomes
#    it — but it resists ordinary perturbations." A SUSTAINED disposition
#    CRYSTALLISES into a standing trait that STICKS: after N same-direction
#    steps, a LONE contrary nudge does NOT flip it, but SUSTAINED contrary
#    evidence does. This is "the agent has BECOME conservative/permissive."
#
#    These gates are the layer-3 headline: experience -> temperament, via the
#    SAME native dynamics (can_native_identity_field_feedback) that crystallise
#    any felt state into character. They MOVE the felt state through the real
#    rule and only ASSERT the standing-vs-perturbation behaviour — never a
#    hand-written field.
# ---------------------------------------------------------------------------
def test_sustained_evidence_crystallises_a_standing_conservative_trait():
    """N consecutive conservative steps accrue into the crystallised standing
    trait: the level walks conservative one graded step per tick and settles
    (clamped at the -4 half-width). The trait is now a STANDING coordinate the
    agent occupies — not a transient reading."""
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    walk = [disp.relax_disposition(a, -1.0, ticks=1) for _ in range(8)]
    # graded descent through distinct coordinates, then clamped standing at -4.
    assert walk[0] == -1 and walk[1] == -2 and walk[2] == -3 and walk[3] == -4
    assert disp.disposition_level(a) == -4
    # the standing trait is in the agent's OWN signature — it has BECOME this.
    coord = _disp_coord(disp.disposition_signature(a))
    assert coord is not None and coord[1] == "field" and coord[2] == -4, coord


def test_crystallised_trait_resists_a_single_contrary_nudge():
    """The identity-field property, made concrete on disposition: an agent driven
    conservative for N steps has CRYSTALLISED a conservative trait; a SINGLE
    contrary (permissive) nudge does NOT flip it — the accrued evidence ledger
    keeps the rendered trait on the conservative side. Identity resists ordinary
    perturbation. (The lone contrary sigma is integrated by the rule, but the
    cumulative log-odds still favours conservative, so the STANDING sign holds —
    exactly can_ops.rs' 'resists ordinary perturbations'.)"""
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    for _ in range(5):                       # crystallise a firm conservative trait
        disp.relax_disposition(a, -1.0, ticks=1)
    crystal = disp.disposition_level(a)
    assert crystal <= -3, crystal            # genuinely established, not marginal

    # ONE lone permissive nudge — an ordinary contrary perturbation.
    after = disp.relax_disposition(a, +1.0, ticks=1)
    # the STANDING trait does NOT flip to permissive; it stays conservative.
    assert after < 0, (crystal, after)
    assert after <= crystal + 1, (crystal, after)   # no sign flip, no runaway
    # it has NOT become permissive on the strength of a single contrary datum.
    assert disp.disposition_level(a) < 0


def test_established_permissive_trait_also_resists_a_single_contrary_nudge():
    """Symmetric: a crystallised PERMISSIVE trait resists a lone conservative
    nudge — the property is direction-agnostic (it is identity, not a sign
    convention)."""
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    for _ in range(5):
        disp.relax_disposition(a, +1.0, ticks=1)
    crystal = disp.disposition_level(a)
    assert crystal >= +3, crystal
    after = disp.relax_disposition(a, -1.0, ticks=1)   # lone contrary nudge
    assert after > 0, (crystal, after)                 # stays permissive
    assert disp.disposition_level(a) > 0


def test_sustained_contrary_evidence_does_overcome_the_trait():
    """The other half of the property: identity is NEVER frozen. A crystallised
    conservative trait, given SUSTAINED contrary (permissive) evidence, DOES
    reverse — the ledger's log-odds eventually flip and the field walks all the
    way across. It resists an ordinary perturbation but yields to a persistent
    one. (Contrast test_crystallised_trait_resists_a_single_contrary_nudge: same
    trait, one nudge holds, many nudges move it — that gap IS the hysteresis of a
    real standing temperament.)"""
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    for _ in range(5):
        disp.relax_disposition(a, -1.0, ticks=1)
    assert disp.disposition_level(a) < 0                # crystallised conservative

    # sustained permissive evidence — enough to unwind the accrued ledger AND
    # build the opposite one. The trait MUST cross to the permissive side.
    final = disp.disposition_level(a)
    for _ in range(30):
        final = disp.relax_disposition(a, +1.0, ticks=1)
    assert final > 0, "sustained contrary evidence must overcome the trait"
    assert disp.disposition_level(a) > 0                # has BECOME permissive


def test_single_nudge_holds_but_sustained_moves_from_the_same_crystal():
    """The two behaviours proved on ONE crystallised trait, to pin the CONTRAST
    directly: from a firm conservative crystal, a lone permissive nudge leaves
    the standing sign conservative; continuing that same evidence to saturation
    flips it permissive. Ordinary perturbation resisted; sustained evidence
    obeyed — the standing dynamical:disposition coordinate is stable under a lone
    contrary nudge and movable under sustained contrary evidence."""
    a = _agent()
    disp.set_disposition_seed(a, 0.0)
    for _ in range(5):
        disp.relax_disposition(a, -1.0, ticks=1)
    crystal = disp.disposition_level(a)
    assert crystal < 0

    lone = disp.relax_disposition(a, +1.0, ticks=1)     # ordinary perturbation
    assert lone < 0, (crystal, lone)                    # STILL conservative

    moved = lone
    for _ in range(30):                                 # sustained contrary drive
        moved = disp.relax_disposition(a, +1.0, ticks=1)
    assert moved > 0, (crystal, lone, moved)            # now permissive
    # the contrast is the whole point: one contrary datum did not move the sign,
    # a persistent stream of them did.
    assert (lone < 0) and (moved > 0)
