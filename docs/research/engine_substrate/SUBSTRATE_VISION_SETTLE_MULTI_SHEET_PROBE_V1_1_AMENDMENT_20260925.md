# Vision settling multi-sheet probe — v1.1 amendment

The v1 probe and preregistration are preserved. It failed before writing raw output because `engine_rules_only(vision_settle)` loads the seed's existing singleton `SettleParams`, while the fixture added a second one. The rule's `PickUnique(SettleParams)` correctly panicked on ambiguity; no inference from that aborted execution is made.

V1.1 changes only parameter setup: after loading the seed manifest, require exactly one existing `SettleParams` and set its `settle` attr to 1.0. The two-sheet graph, act assignments, sole loaded rule, cap, predictions, and analyzer remain unchanged. This is a diagnostic repair after the failed v1 setup, not confirmatory evidence.
