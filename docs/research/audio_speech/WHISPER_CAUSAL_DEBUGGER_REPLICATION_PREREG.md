# Preregistration amendment: balanced autonomous Whisper replication

Status: frozen after the initial indices-20--29 prospective rejection, before
decoding or inspecting any recording with index 30--49.

Date: 2026-07-28 (Australia/Melbourne)

## Why this amendment exists

The first autonomous run discovered a candidate component on a balanced
6+6+6 panel, but prospective validation rejected it. The candidate preserved
speech while increasing null false transcripts from 19 to 28.

The trace exposed two design defects:

1. null discovery evidence contained only baseline-positive nulls, so an
   intervention received credit for removing false transcripts but no penalty
   for creating new ones on baseline-empty nulls;
2. the hierarchy opened only the maximum-utility coarse attention component,
   although the original intervention grammar admitted heads under every
   positive coarse attention component.

These are defects in the autonomous experimental design, not evidence for a
different component identity. This amendment freezes the repair before a new
untouched replication fold is inspected.

## Frozen amendment

- Model, weights, decoder settings, no-retraining constraint, intervention
  implementation, graph/host boundary, normalization, and weight-identity
  gates remain unchanged.
- Calibration uses recording indices 10--19.
- The calibration panel contains, when available:
  - 12 non-empty wrong speech transcripts;
  - 12 exact-correct speech transcripts;
  - 12 null controls with a non-empty baseline transcript;
  - 12 null controls with an empty baseline transcript.
- Filename traversal is a fixed Latin-square order over digit and speaker.
- Causal utility becomes:

  `speech errors removed + null errors removed - new null errors - correct speech lost`

- A candidate must have positive utility, restore baseline behavior after hook
  removal, lose no correct speech controls, and create no new null errors.
- Every positive-utility coarse attention component opens its heads. The graph
  tests all enabled heads and authors the maximum-utility admitted candidate.
- Coarse MLP effects remain diagnostic but do not open head search because an
  MLP has no published head decomposition.
- The deterministic same-cardinality control remains graph-authored before
  replication.

## Untouched replication

Recording indices 30--39 are the new prospective replication fold. A
deterministic balanced set contains one recording per digit/speaker and its
matched phase-scrambled null.

The unchanged graph-native gates require:

- at least 50% reduction in non-empty wrong speech transcripts;
- at least 50% reduction in null false transcripts;
- less than one percentage point loss of exact speech accuracy;
- fewer combined failures than the deterministic control;
- byte-identical weights and no allocated gradients.

Indices 40--49 remain untouched for external replication. A rejected outcome
will be reported as rejection, not converted into another in-fold search.
