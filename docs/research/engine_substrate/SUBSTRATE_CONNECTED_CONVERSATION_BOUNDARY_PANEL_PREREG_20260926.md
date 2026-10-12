# Connected conversation boundary panel preregistration

## Question

Across additional authored connected-conversation workloads, what boundary and frame-interaction structures does the live substrate graph expose, and how do the interaction projection and native closure work scale as concurrent goals increase?

## Workloads and ownership rule

Run three fresh-process replicates of: (1) `phase3_common_ground_stress.json` (10 ordered events, two origin Goals), and (2) generated same-addressee concurrent-goal sequences at N=2/4/8, following the fixture's declared construction order (all request origins/Goals first, then selection/execution/action-result triplets in task order). Every selection/execution/action-result is explicitly linked with `for_goal` to its intended Goal. For common-ground stress, each `origin` starts a Goal frame, each `independent` event starts a standalone event frame, and continuations/outcomes are assigned to the frame of their explicit Goal when present, otherwise the latest origin frame. A Goal belongs to its origin frame.

All workloads are materialized incrementally through `domains.discourse_state` and native `conversation_discourse_state` rules. Run full native closure after each event. Do not infer frame ownership from graph or trace results. Report direct cross-frame edges, shared boundary-node incidences and the induced pairwise frame interaction graph separately. The projection connects two frames if a direct graph edge joins their owned nodes or a shared unowned boundary node is incident to both; this projection can become a clique around a shared bus and must not be interpreted as independent pairwise factors.

## Measures and gates

Capture every event's closure status/progress, graph digest, nodes/edges, final frame owners, boundary-node degrees, interaction edges, exact interaction treewidth for at most eight frames, goal lifecycle/provenance, total candidate pairs and Term evaluations, and process peak RSS. Require three distinct fresh PIDs with identical per-case graph/checkpoint digests and counters; all events and goals owned once; all closures fixed-point; all goals resolved with only their intended transition events; exact recomputation of edge/boundary/frame counts and treewidth; no external model/tool calls; stable fixture, protocol, rule-seed, materializer, Rust/native build locks.

## Claim boundary

These are authored fixture and generated task-family measurements, not a random sample of everyday conversation or perception workloads. They measure native graph structure and ordinary global closure, not partitioned closure, learned cuts, a production boundary scheduler, or speedup. Shared-state projection width is a graph diagnostic, not a direct inference treewidth unless factor semantics justify that interpretation.
