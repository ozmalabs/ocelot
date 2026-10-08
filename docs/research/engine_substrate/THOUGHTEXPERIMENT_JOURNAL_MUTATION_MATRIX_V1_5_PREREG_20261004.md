# Thoughtexperiment journal mutation matrix v1.5 preregistration

Date: 2026-10-04

## Objective

Resolve whether journal residual parity remains meaningful when a branch's
edge-read aperture hides existing primary edges. Distinguish changes to the
branch's observation view from changes to its underlying semantic graph.

## Method

Repeat the fixed v1.4 20-case matrix and add one case: narrow the edge-read
scope to one fixture node, perform a tracked node attribute write, capture the
scoped serialization, finish the mutation journal, and compare the journal
against a whole-graph diff after clearing the aperture. Also retain the diff of the narrow scoped serialization as a diagnostic.
Require (a) the independent full-state diff to match the journal, (b) the
scoped-view diff to show hidden edges as removed, and (c) clearing the view restriction to
restore the same semantic serialization used by the full-state oracle. Existing
revision, derived-index, checkpoint, source-lock, and divergence checks remain
in force. The evaluator and analyzer are locked before execution.

## Claim limits

This is one fixture and one narrowing/widening sequence. It tests semantic
residual construction across a read aperture; it does not establish behavior
for arbitrary scope changes interleaved with edge writes, concurrent branches,
or all caller paths. Scope-induced edge omissions in a scoped serialization
must not be interpreted as primary-graph deletions.
