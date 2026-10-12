# Daemon experiment-close → MetaShape bridge preregistration (2026-09-26)

## Question

Does the daemon's graph-selected `close` host-action implementation pass ready experiment conclusions through `teach()`, allowing the installed MetaShape growth rules to recognize a repeated held-basis relation pattern?

## Locked procedure

1. Set `OZMA_SEED_PERSIST_DISABLED=1` before creating the adapter. This preserves in-graph behavior while preventing writes to real seed manifests.
2. Create a fresh `WorldAdapter(seeds=())` and load only `meta_shape_growth` with its declared dependency closure. Record the exact successful seed set, load errors, source hashes, and baseline `ShapeObservation`/`MetaShape` counts.
3. Add two graph facts of type `Experiment`, each with `status="done"`, `outcome="supported"`, `conclusion_ready=True`, `taught=False`, empty `hypothesis`/`game`/`run_dir`, and distinct `axis_tag` (`bridge_a`, `bridge_b`). Do not add `SeedDelta`; the close routine must supply its documented empty defaults.
4. Call the daemon's `_close_tick(adapter)` once. Do not call `teach()` or `close_experiment_loop()` directly.
5. Record each Experiment's `taught` state, `TaughtHint`/`ShapeObservation` statuses and counts, and newly added MetaShape identities. Hash all direct production and runner sources plus the native extension.

## Adjudication

Bridge success requires both experiments marked taught; two new ShapeObservations with residual then recognized statuses; and at least one new MetaShape after the second observation. Failure, different statuses, missing source-lock integrity, or an unblocked persistence attempt is reported as such without changing the locked inputs.

This tests a controlled daemon host-action seam. It does not show that natural daemon operation produces ready experiments at any frequency, that the experiment outcomes are valid, or that the minted MetaShape improves future task performance.
