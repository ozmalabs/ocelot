# Targeted attribute unindex v4 preregistration

Date: 2026-10-06

## Question

Can deletion and retyping remove an indexed node by using its old attribute map, avoiding a scan over every value bucket while preserving the exact index state and branch isolation measured in v3?

## Change and comparison

Change `TypedGraph::unindex_node` to accept the node's before-image attributes. For each present `(key, value)` pair, visit only the declared `(node_type, key)` index and remove the node ID from that value's bitmap; remove the value bucket if empty. Update delete, retype, and restore replacement call sites to pass the old node attributes. Keep all other behavior unchanged.

Repeat the v3 7,164/16,384/50,771 unique-value panel, 21 paired repetitions per cell, using its same set-attribute, insert, delete, and retype cases, shared/eager arms, and parent/sibling exact-query gates. Compare v4 medians with the preserved v3 capture. Report mutation times and fork-plus-write totals separately by operation and size.

## Gate and limits

All exact branch, parent, sibling, source-stability, and baseline-query gates must pass. A successful targeted-unindex result should reduce shared delete/retype first-write time with population while leaving set/insert semantics unchanged. This remains graph-level synthetic evidence; whole-Substrate closure, memory, concurrent branches, and natural-task frequency remain unmeasured.
