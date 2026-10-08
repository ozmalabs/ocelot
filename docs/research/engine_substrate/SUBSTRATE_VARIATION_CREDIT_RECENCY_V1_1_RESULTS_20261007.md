# Variation credit v1.1 (recency window): results (2026-10-07)

Protocol: [preregistration](SUBSTRATE_VARIATION_CREDIT_RECENCY_V1_1_PREREG_20261007.md).

## Outcome

The recency window does not help. Panel A's primary gate G1 failed. The window was preregistered as the seed default; it is removed from the default and remains available as an opt-in `VariationPolicy.window` attribute.

## Panel A: sequential shift

120 paired sequences: 4 same-kind shift pairs × 30 replicates, each 8 A → 8 B → 4 A episodes. [Raw report](../../../evaluation/reports/variation_credit_shift_v1_1_20261007.json).

| Gate | Comparison | Paired Δ | 95% CI | Result |
|---|---|---:|---|---|
| G1 adaptation | window4 − unbounded, phase B | +1.1 | −0.03 to 2.19 | **fail** |
| G2 no shift harm | window4 − frozen, phase B | +36.5 | 32.9 to 40.3 | pass |
| G3 whole sequence | window4 − frozen, all 20 episodes | +29.8 | 28.0 to 31.8 | pass |

Mean score per pair and phase (frozen / unbounded / window4):

| Pair | A | B (after shift) | A again |
|---|---|---|---|
| d1→d2 | 11.9 / 57.8 / 54.0 | 25.0 / 62.2 / 61.9 | 11.8 / 50.0 / 32.4 |
| d3→d4 | 34.3 / 83.1 / 82.7 | 49.5 / 70.1 / 71.9 | 35.4 / 87.2 / 73.2 |
| d5→d6 | 61.8 / 80.4 / 80.5 | 20.4 / 48.3 / 49.2 | 61.5 / 84.3 / 74.2 |
| d7→d8 | 75.5 / 82.7 / 82.4 | 16.7 / 72.8 / 74.8 | 78.3 / 86.9 / 80.0 |

Findings:

- **Credit that keeps learning adapts to a shift without forgetting.** Unbounded credit beats frozen after the shift in every pair. v1's harm (8.9 vs 20.6) came from its held-out design, where evaluation episodes were frozen and could not update credit. It was not caused by the credit rule itself.
- **The window costs retention.** On returning to A, window4 is 7–18 points below unbounded in every pair, because it has forgotten A's winners.
- **Seed default.** It stays unbounded, which is v1.0.0's behaviour.

## Panel B: v1 held-out gate repeated with window4

[Raw report](../../../evaluation/reports/variation_credit_adoption_v1_1_window4_20261007.json).

- **Gate:** passes. 9/12 improve, 0 harm, aggregate Δ +35.5 (lower CI 19.8). The rollback check also passes.
- **Against unbounded:** worse than v1's unbounded run (+39.4).
- **Interference extra:** d1 after training on d1 then d2 drops to 10.6, versus 46.1 unbounded.

## Implication for the next gate

In this world, recency is the wrong lever. Two levers remain:

- **Context.** Concern features would let credit separate the A and B regimes. The authored world has no such features.
- **Exploration.** In every arm, the first post-shift episodes still try most of the menu.

Both require concerns with observable features. That is the real-judge gate (gate 2), not a further change to the authored world.
