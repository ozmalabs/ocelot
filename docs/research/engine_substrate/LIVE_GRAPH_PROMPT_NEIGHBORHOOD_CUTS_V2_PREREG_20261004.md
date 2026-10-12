# Live graph prompt-neighborhood cut measurement v2

Date: 2026-10-04

## Motivation and question

The v1 pilot's same-type comparator contained only 2–8 other Message nodes
per graph, and their root-degree gaps reached 15–29. It therefore did not
provide a close degree-matched null. V2 keeps that complete same-type census
and adds a broader degree-ranked non-Message control arm, with actual degree
gaps reported for both.

Do inbound-prompt neighborhoods show low graph boundary cost relative to (a)
all other Message roots available in the same graph and (b) a wider set of
non-Message nodes nearest in graph degree?

## Fixed method

Use the same five unique graphs from the locked two-replicate authored-prompt
harvest. For each prompt Message, use radii 1, 2, 3 and traversal hub cutoffs
10, 100, 1000, and none. Neighborhoods remain weakly connected, with original
edges used to count cuts.

Control arm A is a census of all other Message nodes, up to 64, ordered by
absolute degree gap and deterministic SHA-256 tie-break. Control arm B selects
up to 64 non-Message nodes by the same ordering. For both arms record sample
count and min/median/max degree gap; for B also record exact-degree matches.
Measure frame size/fraction, frontier, crossing edges, outside boundary nodes,
crossing edges per frame node, and prompt percentile within each arm. No
provisional ownership labels are used.

## Gates and claims

Lock archive, prior path analysis, protocol, runner, and current-source hashes
before execution. Analyze all 5 × 3 × 4 cells. Report prompt vs each control
arm separately and never call a degree-ranked set “matched” without showing
the actual gaps. A result counts as consistent only within this finite panel;
the four radii/cutoff combinations are sensitivity settings, not independent
replicates. Require direction and degree-gap summaries across all settings.

This measures prompt-centered local sparsity, not automatic frame discovery,
separator uniqueness, treewidth, or task ownership. Non-Message controls
introduce node-type confounding; same-type Message controls are a small census.
Five authored prompts are not a prevalence sample of natural tasks.
