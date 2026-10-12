# Finite-key closure checker hardening v1.1 protocol

## Question

Does the finite-key static analyzer fail closed on malformed top-level rule/edge containers while continuing to admit its positive recursive finite-key fixture, and does that admitted rule still parse and reach the expected native fixed point?

## Fixed cases

The analyzer `self_check()` fixture set is the frozen syntax set. Four added malformed-input controls use object and string values for `rule_specs`, and object and null values for `initial_edges`. They must all be rejected with a reason. The existing positive finite-key rule must remain accepted; the fresh-node, computed-key, mutation, unsupported-clause, invalid-inventory, duplicate-fact, and edge-attribute replacement controls must remain rejected as registered.

The positive rule is loaded into the current native `Substrate`, one link fact is inserted, and native closure must return `fixed_point`, exactly three nodes and three edges, two progressing firings, and exact expected edges. The native access set must match the existing fixture contract.

## Provenance and admission

A pre-run lock covers the protocol, runner, checker, independent analyzer, native parser/effect/runtime sources, and loaded native extension. The runner captures the shared `substrate-run-manifest-v1` and nonempty parent console log. The independent analyzer validates all checker fixture outcomes, native graph/status/progress/access gates, lock stability, manifest and log integrity, and explicit input presence. Any source/build/input drift invalidates the run.

## Interpretation boundary

This is a checker input-validation repair and one accepted-rule parser/runtime parity probe. It does not validate every accepted syntax combination, prove the checker complete, or expand the finite-key closure theorem beyond its existing monotone insertion fragment.
