# Rooted frame-proposal panel v1 preregistration

Date: 2026-09-28
Status: preregistered before the confirmatory capture

## Question

Can a simple, task-agnostic graph procedure propose useful local frames around live task inputs, and how do its boundary costs and recovery of protocol-declared operational nodes change with radius? This is a diagnostic of algorithmic framing, not a claim that the substrate learns concepts or that a radius neighborhood is the correct semantic frame.

## Workload and source

Reuse the two-prompt live self-report workload from [task-boundary v2.1](SUBSTRATE_LIVE_SELF_REPORT_TASK_BOUNDARY_V2_1_PREREG_20260927.md): `report your organisation` and the known route-shortfall prompt `describe who you are`. Run three fresh workers on the current source snapshot under a new complete input lock. Preserve the existing route/lifecycle checks and exact declared task-boundary computation.

## Candidate framing algorithm

For each inbound Message, form an undirected adjacency view of every typed edge in the final runtime graph. Starting only from that inbound Message ID, generate BFS neighborhoods for radii (r=0,1,2). Do not use the protocol-declared owned-node set in proposal construction. Freeze these radii and the edge-direction treatment before capture; do not tune them on the observed membership scores.

For each proposed set, record frame size, the exact number of crossing edge incidences, unique external node count and type histogram, width upper bound on its induced state graph, and the SHA-256 of sorted member IDs. Compare membership to the protocol-declared operational set only after proposal construction, reporting precision, recall, and Jaccard. The operational set is an imperfect reference label and does not include all perceptual input or all task-relevant work.

For boundary external nodes, retain node type and attribute-key/type-name histograms, without raw attribute values. This makes the captured state projection inspectable while avoiding a false claim that every attribute is a task-relevant interface variable. Report exact variable/domain interface and runtime operation-dependency coverage as unavailable unless the capture contains direct evidence for them.

## Primary measurements and controls

Primary outputs are radius-wise frame size and crossing incidence, with unique external nodes as a separate measure. Secondary outputs are reference-label precision/recall/Jaccard, induced-width upper bound, and external-boundary type/attribute-key summaries. Count candidate construction time separately from task execution. Require identical candidate and declared-cut structural signatures across all three workers for each turn, stable source locks, full graph semantic parity, and existing task lifecycle/control gates.

Include the declared operational frame as a descriptive comparator, not as an input to the BFS proposal. Preserve the failed-route prompt as a separately labeled negative task outcome; do not count it as a successful capability instance. No hypothesis test or population estimate is planned for this two-prompt fixture.

## Claim limits and next gate

This is one authored task family and a deterministic generic baseline. BFS radius is not learned framing, and reference-label overlap is not task correctness. The final graph can miss transient reads and access dependencies. Edge-boundary attributes are only a candidate interface inventory; no attribute is asserted task-relevant without operation-level access evidence. A successful run would justify a subsequent independently sampled multi-family study with traced access/factor scopes and boundary-domain measurements. It cannot establish cheap-cut prevalence or general tractability.
