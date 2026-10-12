# Live frame explicit-ownership crosswalk v1 preregistration

Date: 2026-10-04

## Question

How much of each operational task cut in the current two-request live capture
is independently recoverable using the conservative explicit graph relations
used by the five-task ownership analyzer?

## Method

Use only worker 0's retained full graph and task-boundary node-ID lists from the
source-locked v1.2 frame capture. Reconstruct a conservative ownership set per
turn from the inbound Message ID, Goals explicitly linked by `comprehends`,
those Goals' `origin_event` references, and DiscourseEvents explicitly linked
through `for_goal`. Do not include response candidates, child goals, receipts,
or nodes inferred from reachability. Independently compare each reconstructed
set with the operational cut's `owned_node_ids`; report exact ID set
intersection, precision, recall, Jaccard, node-type disagreements, overlap
between turns, crossing edge counts, and hashes of the source capture and raw
analysis inputs.

## Limits

This is one two-request authored self-report sequence from one retained full
graph. The operational task sets are protocol supplied; the relation projection
is a conservative diagnostic. Agreement does not validate annotations,
complete factor dependencies, natural task prevalence, or partition speed.
