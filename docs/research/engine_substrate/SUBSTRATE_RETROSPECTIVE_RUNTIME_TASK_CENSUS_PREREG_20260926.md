# Retrospective runtime task graph and rule-work census protocol

**Status:** exploratory reanalysis of a prior locked capture; not a preregistration for a new runtime experiment.

## Purpose

Extract graph size/degree/boundary statistics and native closure work from the existing connected-discourse task census. The source capture already exists; this analysis will not alter or rerun it. The objective is to test whether the prior synthetic degree result has a measurable task-derived structural counterpart and identify what a fresh replication must lock.

## Frozen inputs

- Raw capture: `evaluation/reports/substrate_discourse_connected_task_census_v1_20260926.json`
- Input lock: `evaluation/substrate_capability/discourse_connected_task_census_lock_20260926.json`
- Rule seed path named by the original runner: `seeds/conversation_discourse_state.json`

The analyzer will verify raw-to-lock identity, graph digests, graph/reference integrity, cross-arm graph equality, frame-owner membership, and conservation of recorded closure counters. It will independently compute directed in/out degree, weak degree, edge-type counts, owned-frame internal/cross-frame edges, and node/edge boundary counts. It will read rule join arity and variable count from the seed and compare rule names with recorded runtime access summaries.

## Analysis limits

The original seed and materializer no longer match the capture's locked hashes. The capture therefore supports a provenance-bound retrospective analysis, not a current-source reproduction. This is one authored dialogue fixture with three arms over the same task, not a population sample. Frame labels are fixture-derived and supplied by the original runner. Static access summaries are not a complete dynamic dependency proof. The capture contains no task corpus sufficient to estimate natural degree/width frequencies.

No causal claim, significance test, scaling extrapolation, natural-task frequency estimate, or new substrate speed claim will be made. A fresh follow-up must relock the current fixture, producer/materializer, rules, native artifact, and analyzer, then replicate across independently authored task families.
