"""Shared w_supergraph -> integer lattice quantization for
seeds/core_emotions.json's em_weighted_contribution rule (block 204000).

That seed is INTEGER-NATIVE ONLY (tests/test_core_emotions_migrated.py's
integer_audit/integer_values_audit enforce it) -- a continuous [0,1] trait
must be rendered as a stepped integer BEFORE it enters the graph (CLAUDE.md's
BASE-AS-DIMENSION invariant: in-frame is integer, the continuum lives in the
map that produces the step, never in the frame itself).

Every HeldEmotionParams construction site across this seed's consumers
(domains/harvest_world.py, domains/harvest_spite_world.py,
worlds/glassbox_r1_world.py, worlds/langsim_world.py,
worlds/langsim_syntax_world.py, domains/marshmallow_world.py,
worlds/bigville_ocelot_adapter.py, scripts/core_emotions_measure.py,
scripts/emotion_phenotype_measure.py) computes w_supergraph_q/w_scale_bits
through this ONE function -- the scale is derived once, from real named
per-consumer contribution magnitudes, never a per-file literal.
"""
from __future__ import annotations

import math

# A generic drawn-trait decimal-precision floor, matching bigville's own
# named DRAW_CLIP_DECIMALS where that generator is available (read live,
# below) -- the same source-precision anchor LOG_WEIGHT_QUANTIZATION_PREREG.md
# established for affect_coupling's log-weights, reused here for consistency.
_GENERIC_DRAW_DECIMALS = 4


def _contribution_ceilings() -> list[float]:
    """Real, named ceilings on |supergraph_contribution| this seed's actual
    consumers produce -- read live from each module's own declared constant,
    not restated here. A new consumer with a larger range extends this list,
    not a hand-picked SCALE."""
    ceilings = []
    try:
        from domains.harvest_world import K as _harvest_k
        ceilings.append(float(_harvest_k))  # future_yield's own carrying-capacity bound
    except ImportError:
        pass
    try:
        from worlds.glassbox_r1_world import G_CONTRIB as _glassbox_g
        ceilings.append(float(_glassbox_g))
    except ImportError:
        pass
    try:
        from worlds.langsim_world import G_CONTRIB as _langsim_g
        ceilings.append(float(_langsim_g))
    except ImportError:
        pass
    # scripts/core_emotions_measure.py + scripts/emotion_phenotype_measure.py's
    # own canonical G1-G4 fixtures (fulfilment=300, harm=-800) -- the widest
    # real contribution range already exercised in this tree.
    ceilings.append(800.0)
    return ceilings


def derive_scale_bits() -> int:
    """B: bits of w_supergraph's [0,1] -> integer lattice. Two independent
    anchors, MIN not max (never encode precision the steps can't support --
    the identifiability guard CLAUDE.md's BASE-AS-DIMENSION section names):

      - source-precision ceiling: bits needed to represent a population
        drawn to DRAW_CLIP_DECIMALS decimal places without losing real
        source precision (bigville's own generator constant where
        importable, else the same named generic default).
      - consumer-resolution ceiling: bits needed so no live caller's own
        contribution range is quantized coarser than that caller's OWN
        integer magnitude already is -- matching resolution to what the
        contribution signal itself can support, not inventing headroom.
    """
    try:
        from worlds.bigville_town100_world import DRAW_CLIP_DECIMALS as decimals
    except ImportError:
        decimals = _GENERIC_DRAW_DECIMALS
    source_ceiling = math.ceil(math.log2(10 ** decimals))

    max_contribution = max(_contribution_ceilings())
    consumer_ceiling = max(1, math.ceil(math.log2(max_contribution + 1)))

    return int(min(source_ceiling, consumer_ceiling))


def quantize_weight(w, bits: int | None = None) -> tuple[float, float]:
    """w (a continuous [0,1]-drawn knob) -> (W, B): W is w's integer index on
    a 2**B lattice, ATTENUATION-ONLY above the reference weight 1.0 (a clamp,
    not an amplifier -- matches every existing consumer's own w in
    {0} u [1,inf) contract, so w>=1 stays byte-identical to today's sign gate
    while w in (0,1) genuinely varies for the first time). Returns floats
    (this seed's own convention -- HeldEmotionParams attrs are Value::Float
    holding exact integers, per can_register_quantization.json's precedent)."""
    if bits is None:
        bits = derive_scale_bits()
    clamped = min(max(float(w), 0.0), 1.0)
    return float(round(clamped * (2 ** bits))), float(bits)


__all__ = ["derive_scale_bits", "quantize_weight"]
