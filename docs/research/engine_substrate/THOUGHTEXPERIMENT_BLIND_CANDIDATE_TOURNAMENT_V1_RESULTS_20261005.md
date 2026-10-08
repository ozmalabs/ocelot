# Blind candidate tournament v1 results

The source-locked evaluation passes semantic gates across three fresh
workers and two task conditions. The proposal pool contains three candidates
per condition. In `repair_needed`, branch execution measures the boolean
effect toggle at gain 20 against no-op and same-size placebo gains of 0. The
graph selects the sole candidate that clears both margins, despite receiving
no operator label or target UID. Three disjoint canary examples pass; after
selection the harness binds the live UID/revision/hash, and Rust CAS commits
once. Revision advances 0→1 and two fresh final examples both pass.

In `no_repair`, the live rule already matches the oracle and the no-op and
placebo controls both score 20. The graph rejects every candidate, emits one
`no_causally_supported_patch` abort, and leaves the target revision at 0.
Candidate outputs and decisions are identical across workers. Candidate
rehearsal uses shared-graph-page CoW branches; the primary revision remains
unchanged until CAS.

| Median measured phase | Time |
|---|---:|
| No-op rehearsal, three repetitions | 2.275 ms |
| Placebo rehearsal, three repetitions | 4.466 ms |
| Candidate rehearsal pool | 12.478 ms |
| Graph selection tick | 0.180 ms |

These timings summarize six tiny case-worker observations and exclude
process startup. The capture does not separately time canary rehearsal,
canary/commit tick, or final verification, so no full-lifecycle cost claim is
made. The experiment uses one fixed rule family and harness-authored task
labels; it establishes a narrow integration result for proposal generation,
behavioral scoring, graph-native evidence gating, no-repair abstention, canary,
and CAS. It does not establish broad induction, natural task transfer, or
self-improvement.

During the first tournament attempt, CAS refused the effect patch as
`malformed_clause`: RulePatch's effect parser accepted `set_attr` but omitted
the engine's supported `set_attr_if_different` effect. The native parser now
accepts that operation through the same `EffectArg` path. The rebuilt binary's
source provenance matches the Rust tree, and the source-locked recapture
commits the patch with receipt reason `ok`.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_BLIND_CANDIDATE_TOURNAMENT_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_blind_candidate_tournament_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v1_lock_20261005.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_blind_candidate_tournament_v1_20261005.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_blind_candidate_tournament_v1_analysis_20261005.json)
