# Held-out polyomino v1 negative-control mint side effects

**Run:** 2026-09-29, post-hoc audit of the 12 distinct perceived added-cell controls in the sealed v1 capture.

All 108 source observations reduce to 12 unique base/goal signature pairs, each repeated nine times across clean, sigma-8, and sigma-12 arms. Each unique pair was decoded once against a fresh codebook under an independently locked replay. In all 12/12 cases:

- the observation ended with `status=minted` and had no `has_transform` target;
- exactly one new `CapabilityAxis` appeared and was attached through the Observation's `minted` edge;
- the axis carried `source=concern_induction` and `is_axis=1`;
- the Agent's `codebook_epoch` remained `0.0`.

This confirms that the added-cell controls route into an actual graph mutation, rather than merely reporting an abstract mint decision. The unchanged `codebook_epoch` shows that this low-level axis creation is not the same event as Python-side `grow_part_library` codebook growth. The audit used a fresh graph for each distinct input. It does not establish whether repeated observations in one live graph are deduplicated, whether these axes are useful or harmful, how they affect later inference, or whether the path rolls back. The controls represent valid novel cell structures as well as negatives for known-transform classification, so this is not a false-mint rate estimate.

Artifacts: [audit specification](SUBSTRATE_HELDOUT_POLYOMINO_V1_NEGATIVE_MINT_SIDE_EFFECT_AUDIT_20260929.md), [runner](../../../evaluation/substrate_capability/audit_heldout_polyomino_v1_negative_mint_side_effects.py), [source lock](../../../evaluation/substrate_capability/heldout_polyomino_v1_negative_mint_side_effects_lock_20260929.json), [raw side-effect capture](../../../evaluation/reports/heldout_polyomino_transform_transfer_v1_graph_replay/negative_mint_side_effects.json).
