# Proposal revision and resolver invalidation v1

## Question

Can a materialized tie-aware resolver keep its derived state correct when proposals are added, tied, removed, or rescored after an earlier fixed point?

## Protocol

Use three fresh workers and N=2/8/32/64. Generate N proposals with one unique maximum and reach fixed point. Install a refresh formulation that writes `max_score`, writes `is_top` as a boolean for every currently adjacent proposal, writes `top_count`, writes `ambiguous` as a boolean, and writes `selected_label` as the unique top label or the empty-string sentinel. Settle, then apply ordered transitions: (1) add a proposal with a new higher score; (2) add a second proposal tied at that score; (3) remove the tied proposal edge; (4) lower the higher proposal's score below the original maximum. Settle and capture graph projection, native operation counters, and elapsed time at each phase.

## Gates

Each phase must reach fixed point. Initial and higher-score states select the unique maximum, have `top_count=1`, and `ambiguous=false`. The tied state has `top_count=2`, `ambiguous=true`, and empty selection. Removing the tied edge restores the unique selection and clears ambiguity. Lowering the higher proposal's score restores the original winner. Every adjacent proposal's `is_top` value must match an independent Python score oracle. Integer work counters must replicate across three workers, excluding elapsed and `_ns` timing values.

## Limits

This is a controlled transition sequence on one proposal family and four sizes. The empty string is the authored no-selection sentinel; this does not establish a general deletion or truth-maintenance facility. No learned proposal generation, concurrent mutation, production integration, or complexity guarantee is tested. The stale-state failure of a one-way annotation scheme is recorded as motivating evidence, not used as the corrected formulation's result.
