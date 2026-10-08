# Thoughtexperiment A8 quantum-route transfer v1 — preregistration

**Question:** Can the graph-authored A8 structural composer select and repair a chosen-action rule from a different navigation representation, then produce useful behavior in isolated portal-maze experiments?

## Scope

The target is `qf_hop_route` from `seeds/quanta_navigation.json`. The task uses the production quanta rules, coarse space quantization, portals, and `ControlResponse` action vocabulary. This is a transfer from cell-gradient navigation to a partitioned-space route rule, not a new A8 operator: the target is faulted with the existing `flip_comparison` EditOp, and the prompted composer receives the explicit cue words naming the `qf_hop_route` rule plus `flip/comparison`.

Each order worker loads only the minimum agent core, relation vocabulary, and quantum-navigation seed; applies the fixed polarity fault to `qf_hop_route`; captures the full host candidate list; then asks production `ground_concern` to compose one proposal. The no-cue control uses only the common `test/send/judge/structure/gradient` predicates. It must use the graph route and abstain from structural edits. The prompted route must report `served_by: graph`, choose `flip_comparison` on exactly `qf_hop_route`, and leave the primary target unchanged.

## Held-out worlds

The scoring stage uses two 5×5 rooms separated by a one-cell portal opening. Case H1 has a vertical wall at column 2 except for the opening at row 2; the agent starts at `(0,0)` and the goal is `(0,4)`. Case H2 rotates the partition: a horizontal wall at row 2 except for the opening at column 2; the agent starts at `(0,0)` and goal is `(4,0)`. Both worlds are quantized from floor/wall observations through `space_quantize`; navigation is scored by production qf flood/hop rule closure and world movement. A pass requires reaching the goal within 16 valid moves, crossing the opening, never moving into a wall, and ending with `closed == 0` and no false closed-world hypothesis.

Every host reference candidate is evaluated once per world in an isolated full-copy branch. A graph proposal with the same locked semantic rule digest as a host candidate reuses that exact outcome; otherwise it is evaluated independently. Source and fault controls run through the same worlds. Receipts verify the changed target rule, and the primary graph/rule revision must remain unchanged for every branch.

## Staged gates

Before order capture, freeze this protocol, runner, analyzer, all adapters, relevant source modules and seed manifests, native build inputs, and loaded binary. The order artifact must contain no held-out outcomes. Inspect complete worker coverage, stable source hashes, exact graph attribution, intended target and operator, target preservation, no-cue abstention, and no outcome fields. Do not score if any gate fails.

Score all host candidates and controls only after the order gate passes. Report case-level path, success, wall contact, portal crossing, step count, closure work, receipts, branch isolation, graph/host semantic identity, and complete cost ledgers. Retain every preregistered prediction failure. A pass supports transfer to these two portal-maze worlds; it does not establish arbitrary task transfer, autonomous target discovery, natural-task prevalence, economic advantage, or self-improvement.
