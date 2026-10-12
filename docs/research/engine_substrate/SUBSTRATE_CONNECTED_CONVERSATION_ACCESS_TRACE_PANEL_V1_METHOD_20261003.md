# Connected-conversation access-trace panel v1 method

Date: 2026-10-03  
Status: preregistered replay against a previously source-locked baseline.

## Question

What concrete graph and attribute accesses occur during native rule closure on the existing connected-conversation panel, how do they relate to task-frame owners and boundary nodes, and does enabling access tracing preserve the exact captured graph states?

## Design

Use the same three fresh-process replicates and 12 cases as `SUBSTRATE_CONNECTED_CONVERSATION_BOUNDARY_PANEL_V1_RESULTS_20260926.md`: one common-ground stress case and concurrent-goal cases with 2, 4, and 8 goals. Enable the native runtime access trace only around each closure call, alongside the existing per-rule scale audit. Capture static `rule_access_sets()` signatures after closure. Enrich each observed access with its rule name and any task-frame labels available for the node and peer; leave shared/unowned endpoints explicitly unlabeled.

The historical source-locked capture is the untraced baseline. Compare every final graph and every per-checkpoint graph digest with the same replicate/case in that baseline. Require source stability within each worker, zero dropped trace rows, fixed-point closures, valid task ownership, valid frame-interaction reconstruction, and successful attribution of every concrete event UID to a loaded rule. The shared `substrate-run-manifest-v1` must record the current native build, explicit source/data inputs, parent console log, CPU time, and peak RSS.

Report observed access counts by operation kind, rule, and owner relation (same frame, cross frame, one endpoint shared/unowned, or neither endpoint owned). Report static read/write signatures and wildcard flags separately from concrete events. Do not interpret an unobserved access as proof of absence: the tracing implementation documents partial coverage, and most captured closures may make no progress. Instrumented timing is descriptive only; it is not compared as a speed result to the historical untraced run.

## Claim boundary

This is an access-fidelity and state-preservation probe on one authored stress fixture and generated same-addressee concurrent-goal workloads. Exact graph parity establishes that tracing preserved the captured graph states for these cases. The panel does not establish trace completeness, partition safety, natural-task prevalence, or speedup. Any partitioned-closure claim needs a separate source-derived interface and exact monolithic/partitioned parity experiment with shared-boundary and high-coupling controls.
