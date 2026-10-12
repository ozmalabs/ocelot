# Offline candidate-snapshot efficacy v1 preregistration

## Question and scope

Does a substrate-acquired linear `DimensionGenerator`, stored in an isolated candidate snapshot, improve exact held-out transfer over an untrained frozen snapshot and equal training exposure without consolidation? Does evaluating that candidate through the partial graph-page CoW backend preserve the eager-copy semantic oracle exactly?

This is a local diagnostic in the authored 2-D integer-linear GenMint family. Its generated tasks are visible in the source and are not project-held or independently custodied. It is not formal P3-E1, a natural-task transfer result, autonomous meta-learning, or an adoption decision. The experiment does not change the primary graph or production baseline.

## Fixed panel

Use the six cells `prior_matrix`, `shearA`, and `shearB`, each with `adjacent_01` and `opposite_03` training layouts. Use the six fixed training points and 16 deterministic held-out geometries from GenMint matrix-family reuse v3. Add eight deterministic negative geometries per cell whose target is nonlinear (`r² + c`, `r - c²`); these are outside the linear generator class. Run five fresh-process replicates per cell with a randomized cell order (30 workers total).

Each worker constructs one fully initialized baseline and records its canonical graph/grammar/rule digest. From that same baseline it creates three independent arms:

1. **Candidate:** fork with `fork_shared_graph_pages_experiment`, enable GenInfer, and provide the fixed training examples. Freeze the resulting candidate snapshot by digest. Evaluate it twice from child branches: once by eager full copy and once by shared graph pages. Disable GenInfer during evaluation to prevent further acquisition.
2. **Frozen:** fork by eager full copy, provide no training examples, disable GenInfer, and evaluate the same held-out tasks.
3. **Exposure without consolidation:** fork by eager full copy, provide the same training examples with GenInfer disabled, disable GenInfer during evaluation, and evaluate the same tasks.

Every arm receives identical positive and negative evaluation inputs. No arm receives evaluation labels through its Observation target field except as the task's observed signature; scoring is recomputed independently from the locked transformation definition. The candidate snapshot itself is never evaluated mutably: evaluation occurs on child branches.

## Outcomes and gates

Primary measure: exact target-match rate on all 16 positive held-outs, by cell, replicate, and arm. Report acquisition rate separately; a failed acquisition remains in the denominator. Report the paired candidate-minus-frozen and candidate-minus-exposure score differences with all 30 cell/replicate values. Secondary measures: positive held-out routing through the training-acquired generator; false acceptance of negative tasks (claimed transformed/covered but independent output is not exact); new `DimensionGenerator` minting during evaluation; per-arm training, fork, and evaluation wall/CPU time; graph size; and peak RSS. Record `CapabilityAxis` mints and `status=minted` separately as novelty signals. Without an independent oracle for whether those axes are appropriate, classify them as unadjudicated novelty rather than false mint or false acceptance.

Integrity and isolation gates: exact randomized 30-worker schedule; source/native hashes; complete rows; baseline unchanged after every branch; candidate snapshot unchanged after both evaluation children; sibling/eager and shared-page candidate outputs, statuses, generator routes, residuals, and final branch semantics exactly equal; held-out bases/targets reconstructed independently; and all results retained, including misses and errors. A failed integrity gate blocks the associated efficacy claim.

No adoption is performed. A positive result permits only the claim that this bounded authored family gained exact held-out transfer from a retained substrate-acquired object. A negative result narrows the current GenMint capability. The CoW comparison is semantic parity evidence on this learning workload, not a general performance, API compatibility, or vLLM claim.

## Pilot amendment (before confirmatory lock)

A single diagnostic cell exposed an ambiguity in the initial false-mint measure: negative nonlinear tasks can receive `status=minted` and a new `CapabilityAxis` while producing no `DimensionGenerator` and no selected transform. This is not enough evidence to call the event either a false mint or a correct discovery. The locked panel therefore reports axis/novelty signals separately and reserves false-mint scoring for a newly created `DimensionGenerator` on the negative task family. The pilot is excluded from the 30-cell confirmatory capture. This amendment precedes lock creation and does not alter task inputs, arm assignment, or the primary outcome.

## Cost-report amendment (after initial capture)

The initial 30-cell capture passed semantic and isolation analysis but omitted per-arm negative-task closure time from the serialized rows, despite the runner measuring an aggregate interval. Preserve that capture as `initial_pilot`; add negative-task wall/CPU closure sums and whole candidate-branch validation wall/CPU to every row. Refresh the source lock and rerun the same fixed 30-cell schedule. This changes measurement completeness only; tasks, arms, scoring, and gates remain fixed. The initial capture is not used to estimate confirmatory costs.

## Analysis and reproduction

Use a separate analyzer over the raw capture; it must check locked schedule and hashes, recompute every expected input and output, verify branch isolation, and summarize paired scores/costs without dropping failures. Preserve the source lock, runner, raw capture, analyzer, and results note. Reproduction commands are recorded with the result after capture.
