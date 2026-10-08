# Live conversation semantically distinct frame scale v1 preregistration

Date: 2026-10-03  
Status: preregistered before runner implementation and capture.

## Question

Does boundary-mediated interaction width still grow with the number of task frames when one live conversation contains semantically distinct requests, and does an explicit follow-up sequence couple more strongly than independent requests?

## Workload

Use full-seed `WorldAdapter.converse` workers with no graph reset, three replicates per arm, and the following exact three-turn sequences:

* Independent request arm: `How are you organised?` (question), `quorplezap the door` (statement), `report your organisation` (statement). These are existing repository-authored prompt routes. Preserve route success/failure as observed, including any missing task Goal.
* Follow-up arm: `report your organisation` (statement), `Can you explain that in simpler terms?` (question), `What part of your organisation is most important?` (question). The latter two are context-dependent follow-ups and have no prior task oracle; their replies/routes are descriptive outcomes, not correctness gates.

Three fresh processes per arm produce six workers. No graph nodes or ownership edges are added. Record each prompt, reply, task/action results, newly observed Message/Goal identities, route timing, final graph and raw digest, peak RSS, and source provenance. Do not filter workers by route success.

## Ownership and topology analysis

Independently derive each frame from the exact inbound interlocutor Message text and graph identity. Assign Goals only through explicit `comprehends` relations; assign DiscourseEvents only through explicit `for_goal`, Goal `originated_in`, Goal `origin_event`, or `represents_message` identity references. Conflicting candidates stay unowned. Report task-oracle status for existing prompts separately; no oracle is invented for the two follow-ups. For each graph, report frame sizes/types, unmatched prompts, owner conflicts, unique unowned boundary neighbors, direct cross-frame edges, shared-boundary-induced interaction graph, and exact interaction treewidth (three frames maximum).

## Integrity gates and claim limits

Require six unique PIDs, exactly three workers per arm, all worker outputs present, source hashes stable before/after capture, exactly three expected inbound prompt Messages per worker, and exact raw graph digest parity within each identical-sequence arm. Route or goal-ownership failures are retained as capability outcomes, not capture exclusions. If generated timing attrs defeat raw replicate parity, preserve the raw failure and make any semantic normalization a separately documented post-capture amendment that excludes only evidenced volatile fields.

This is a six-worker, two-sequence, repository-authored diagnostic. It can contrast independent and dependent requests on this source snapshot; it does not estimate natural conversation prevalence, prove a distributional locality hypothesis, or establish tractability at general scale. Follow-up turns are not required to answer correctly.
