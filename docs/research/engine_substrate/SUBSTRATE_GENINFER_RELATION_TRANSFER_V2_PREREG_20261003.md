# GenInfer relation transfer v2 preregistration (2026-10-03)

## Question and scope

Does the full-seed substrate acquire previously absent integer 2-D linear
generators from training observations, retain them, and use the same acquired
generator on distinct held-out observations? This evaluates one bounded
operator learner, not general self-improvement.

## Protocol

The v1 task family exposed aliases: its two shear maps were explained by
per-relation coordinate shifts or a pre-existing named generator. Before
locking v2, four one-run exploratory probes exercised candidate matrices using
the v1 runner's same fresh-core training/held-out sequence. All four candidates
were acquired at training and attributed on held-out: `[2,1,1,2]`,
`[2,-1,1,1]`, `[1,1,1,2]`, and `[1,2,2,1]`. These pilots are task-selection
data, not scored replication. To limit search growth while preserving three
distinct cases, this capture uses the first three listed candidates as its
fixed task set.

The source-locked panel has 30 fresh-core cases: three enabled and three
disabled repetitions per each of the three matrices; three enabled identity
controls; and three corrupted-heldout controls per target matrix. Training
uses the same four-point signature as v1. Held-out uses a distinct four-point
signature and is inserted only after the training closure and generator state
are captured. Corruption changes one held-out coordinate after training.
There are no task labels or target matrices inserted into the learner beyond
the observations used to form each case.

## Locked measures and pass criteria

For each enabled nonidentity case, require (1) the exact target matrix was
absent initially, (2) it exists as a graph `DimensionGenerator` after the
training closure, (3) training did not mint a `CapabilityAxis` task quantum,
(4) the held-out transform receipt names that same training-acquired
generator, and (5) all held-out rows exactly match the preregistered matrix.
Every enabled repeat for every matrix must meet all five conditions for the
three-family gate to pass. Disabled cases must not acquire the target matrix;
identity controls must not mint an identity generator; corrupted heldouts must
not exactly match. Capture must preserve the lock's code, native binary, seed
closure, case inputs, and source manifest.

The analyzer reports per-family and aggregate counts, control outcomes, and
closure/wall timing distributions. Timing is descriptive for these small
fixtures. Failed gates remain failures; the task family or criteria will not
be changed after capture. A later task-family change requires a new version,
preregistration, lock, and capture.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_geninfer_relation_transfer_v2.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_geninfer_relation_transfer_v2.py`
- Source lock: `evaluation/substrate_capability/substrate_geninfer_relation_transfer_v2_lock_20261003.json`
- Raw capture: `evaluation/reports/substrate_geninfer_relation_transfer_v2_20261003.json`
- Analysis: `evaluation/reports/substrate_geninfer_relation_transfer_v2_analysis_20261003.json`
