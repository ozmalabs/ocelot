# GenInfer relation-transfer v1 protocol (2026-10-03)

## Question

Can the full-seed substrate infer a reusable 2-D integer-linear relation from one set of typed examples, then apply its graph-minted generator to a different held-out relation signature?

## Task and splits

Each training and transfer signature encodes a relation from named vector examples `(predicate, x, y, value)`. The learner receives the training base signature and its transformed training observation first. Only after training closure and graph readback are recorded does the runner add the separate held-out base signature and held-out transformed observation. The target matrix is used by the fixture builder and independent analyzer to make labels; it is not passed as a learner parameter.

Test three invertible maps: `[1,0,1,1]`, `[1,1,0,1]`, and `[2,1,1,1]`. Each has the four training points `(0,0),(1,0),(0,1),(1,1)` and a separate four-point held-out signature `(0,0),(1,1),(2,1),(1,2)`, with disjoint predicate IDs. Repeat each with GenInfer enabled and disabled, three fresh substrates per cell. Add three enabled identity-map controls, where no new generator should be minted, and three enabled corrupted-held-out controls, where one transfer label is perturbed after training acquisition.

Total: 30 fresh substrates. The identity matrix is excluded from GenInfer's new-generator class; it is a no-new-structure control. The corrupted-held-out arm measures whether a training-acquired transform is incorrectly counted as exact held-out success when a transfer label violates it.

## Gates and measurements

- Capture source/native hashes and refuse stale engine builds.
- Confirm no held-out signature or target is present during training closure.
- For every enabled nonidentity clean cell, require the exact target matrix to be newly present after training, the training observation to settle as a transformed recognition without a task quantum, and the later held-out signature to reference that same acquired generator and match every independent held-out row oracle.
- Disabled controls must not acquire the target linear generator through GenInfer. Report any alternate recognition route and any task quanta without silently crediting it as learned-generator transfer.
- Identity controls must not mint a new linear generator.
- Corrupted-held-out controls must be scored against the exact row oracle; a `recognized_transformed` label alone is not a transfer pass.
- Record training/held-out status, transform provenance, generator inventory before/after each stage, quanta, closure work/time, and source stability.

## Interpretation boundary

This tests an existing parameterized learner and graph-minted 2-D linear generator on a new relation-task encoding. The candidate matrix family, relation schema, coordinates, and task split are designed inputs. A pass would demonstrate transfer of a relation inferred from examples within this bounded class, not autonomous task discovery, induction of new operator classes, natural-task prevalence, broad self-improvement, or general polynomial tractability.
