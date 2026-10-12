# Thoughtexperiment journal mutation matrix v1.6 preregistration

Date: 2026-10-04

## Objective

Check semantic residual completeness for mixed edge writes under a narrowed
edge-read aperture, focusing on pre-existing edges that remain in the underlying
graph but are hidden from the branch's current view.

## Method

Repeat the fixed v1.5 21-case source-locked matrix and add five cases:
replace a hidden existing edge by triple, delete a hidden edge using an
identity retained before narrowing, batch-delete two hidden edges, delete an
edge visible through a one-hop aperture, and insert a new edge through a
narrowed aperture. Each sequence captures the branch view and mutation journal,
then clears the aperture before serializing the underlying branch state. Compare
the journal residual to an independent full-state graph diff. Retain the scoped
view diff as a diagnostic. Require all 26 rows to match, revisions to advance
for semantic mutations, and all source-lock and divergence controls to pass.

The source was adjusted before this preregistration so edge replacement looks
up hidden underlying identity for its before-image, while single and batch edge
deletions record the actual prior edge attributes regardless of view
visibility. Those changes are included in the source hash lock.

## Claim limits

The tested paths are direct graph operations in one single-threaded fixture.
This does not cover arbitrary interleavings, concurrency, caller-level
permissions for stale edge identities, or performance. Narrow scope controls
observation; it is not a mutation authorization boundary.
