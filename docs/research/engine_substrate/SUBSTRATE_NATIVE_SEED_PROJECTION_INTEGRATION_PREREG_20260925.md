# Native seed projection integration gate preregistration

Date: 2026-09-25  
Status: preregistered before production-source edit

## Objective

Apply the measured top-level field projection inside `PySubstrate::load_seed_manifest`, the common native boundary for Python call sites. Preserve all currently consumed fields and their existing JSON conversion, parse, graph mutation, rule registration, and report behavior. Preserve the caller's Python dictionary without mutation.

## Contract

`load_seed_manifest` accepts a JSON-shaped mapping whose native semantics are defined by ten top-level keys: `nodes`, `edges`, `productions`, `rules`, `reflexes`, `id`, `self_modification_patchable_rules`, `area`, `order`, and `latency_class`. Other top-level fields are ignored by the native loader. This integration explicitly makes that behavior independent of whether ignored fields themselves can be serialized. Data in a consumed field continues through the existing serializer and parser and retains its existing error behavior.

## Frozen baseline and probes

- Full-corpus baseline: the 737-ID, 833-physical-manifest worker state in `substrate_seed_boot_prefix_scale_v1_20260925.json`, using its complete graph, grammar, exported rule-store, access/order, active-rule count, and full boot-report fingerprints.
- Contract probes: plain root object, unknown large JSON field, unknown non-JSON Python object, each consumed key's presence/absence on minimal manifests, malformed consumed node/edge/rule/reflex/production values, and root non-dict. Record exception class/message and graph state after each failed call; malformed consumed-field cases must preserve pre-call state if they did before the change.
- Runtime: four fresh full-corpus processes, two cold and two warm in C-W-W-C order, with no interception wrapper and no retained manifest references. Report wall, CPU, peak RSS, and exact fingerprints. Compare each result to the frozen pre-change baseline. This is a before/after envelope on one host, not a broad speed claim.

## Pass gates

1. Rust/Python source, build provenance, protocol, and runner hashes are locked and unchanged during the probe.
2. All consumed-field contract probes preserve baseline behavior; the documented ignored-key serialization change is the only intentional difference.
3. Four full-corpus boots match every frozen state/report fingerprint exactly and match one another.
4. No caller-visible Python manifest is mutated; no new load failures occur.

Any failed gate rejects adoption. A passing gate establishes the optimization for the common Python-to-PyO3 path and this frozen corpus; it does not cover native Rust callers, arbitrary schemas, or all application semantics.

## Harness note

The first full-corpus invocation completed four workers but failed state parity because its fingerprint helper used `ensure_ascii=False`, unlike the frozen baseline's canonical `json.dumps` default. The corrected run matched the baseline but the probe generator mistakenly included `id` in the supposedly ID-absent case. That report is retained as an excluded harness artifact. The harness now tests a genuinely absent `id` in the contract matrix, then reruns the full four-worker gate.

The next run passed parity and the corrected contract matrix. A final reproducibility review found the lock omitted the runner's own hash; that report is retained as an otherwise passing but incompletely source-locked attempt. The final run records and verifies protocol, runner, source, and native-build hashes.
