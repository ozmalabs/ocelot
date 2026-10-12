# Cross-family edit-op CoW integration v1 results

The locked run completed across recurrence and conversation, with four workers
per family. In each worker the native graph-Term selector chose the sole
training winner: `editops_edge_once:out:candidate:has_mint_offer:any` for
recurrence and `editops_edge_once:in:m:responds_to:any` for conversation. Both
selected repairs passed all held-out cases on full-copy and shared-graph-page
branches. All 13 independent analyzer checks passed, including backend semantic
parity, all-wrong/tie abstention, source controls, atomic proposal-receipt
return, unchanged primary rules, and stale-retry rejection.

Median measured all-candidate training lifecycle was 19.37 ms for full-copy
and 3.68 ms for shared pages; held-out lifecycle was 3.59 ms and 3.07 ms,
respectively. A single-candidate snapshot median was 0.239 ms versus 0.076 ms;
receipt adoption was 0.171 ms and selector cost 1.326 ms. These are small,
authored workloads and local timings, so they show this branch mechanism works
and merits scale measurements; they do not establish a general speedup.

The experiment demonstrates candidate generation from a supplied fault and
cue, branch-local rule evaluation, training selection, held-out validation,
and return of an evidence receipt. Fault diagnosis, autonomous choice of a
repair family, general task acquisition, and activation of a newly minted rule
remain untested. This is substrate-assisted structural search under a harness,
not self-improvement.
