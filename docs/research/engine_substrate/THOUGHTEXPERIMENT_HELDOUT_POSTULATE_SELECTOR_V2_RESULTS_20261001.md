# Held-out postulate selector v2 results

**Result:** the normal open-gap selector prunes the held-out scale-cancellation derivation in both Direct and receipt arms. The derivation is reproducible, but it does not count as a new open capability because the speech codebase already implements it.

## Panel

All nine gates pass across three fresh full-seed workers. Derivation-only synthesis (`prune=False`) returns one order-1 scale-cancellation gap in each arm. Normal selector synthesis (`prune=True`) returns zero gaps in both arms. Surface-only controls also return no scale-cancellation derivation. Direct and receipt outputs match, the exact selected donor remains Concept 15504 in `computer_vision`, and the canonical graph states are equal.

## Selector reason

The source-locked reason probe recomputes the actual full-boot `_covered_keywords()` set and calls `is_gap()` on the captured implication. Its verdict is `already in speech codebase`, matched by `domains/sound_graph.py`. The first selector rejection therefore has a concrete implementation match. `domains/speaker_norm.py` also contains vocal-tract-length normalization logic, but the selector reports `sound_graph.py` first for this candidate's keys.

## Interpretation

This closes the current held-out candidate as a capability-gain result: the architecture can derive the implication structurally and correctly avoid retaining it as an open gap when its speech implementation already covers the capability. It does not demonstrate discovery of a novel useful gap or task improvement. This is a positive selector-integrity result and a negative novelty result.

Next select a held-out postulate/shape pair whose derived capability is not already covered, preregister an independent task utility oracle before transfer, and require retained candidate → implementation/proposal → held-out outcome improvement. Keep derivability, openness, and utility as separate measured gates.

See [selector protocol](THOUGHTEXPERIMENT_HELDOUT_POSTULATE_SELECTOR_V2_PREREG_20261001.md), [selector capture](../../../evaluation/reports/thoughtexperiment_heldout_postulate_selector_v2_raw_20261001.json), [reason protocol](THOUGHTEXPERIMENT_HELDOUT_SELECTOR_REASON_V1_PREREG_20261001.md), and [reason capture](../../../evaluation/reports/thoughtexperiment_heldout_selector_reason_v1_raw_20261001.json).
