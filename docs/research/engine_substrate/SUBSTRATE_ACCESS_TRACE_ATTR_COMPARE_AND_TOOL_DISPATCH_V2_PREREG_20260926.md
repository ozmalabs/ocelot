# Access trace effect-read and tool-dispatch v2 preregistration

Date: 2026-09-26

## Question

Can the default-off native access trace record the direct old-value read performed by `SetAttrIfDifferent` on both changed and unchanged branches, and the attempted `UseTool` dispatch with its concrete tool identifier, while preserving traced/untraced semantics?

## Changes under evaluation

Add event kind 17, `effect_attr_compare_read`, immediately after `SetAttrIfDifferent` reads the prior node attribute and before testing equality. Add event kind 18, `term_tool_dispatch`, after argument evaluation and immediately before native-to-Python callback dispatch; its resource field records the tool symbol. These are diagnostic observations only. They do not record callback-internal reads/writes or scheduler work and do not change matching or effect behavior.

## Paired design

Run three fresh worker processes. Each creates fresh native substrates and runs plain and traced arms for three controlled cases:

1. `SetAttrIfDifferent` changes an existing integer attribute.
2. `SetAttrIfDifferent` sees the requested value already present.
3. A matched rule evaluates one registered `UseTool` callback.

For cases 1–2, compare final attribute, progress count, and terminal status. The trace oracle requires one concrete compare-read row in both conditions and a write row only when the value changes. For case 3, independently count handler calls and require one matching dispatch row for the named tool. In every plain arm, trace rows must be empty; in every traced arm, dropped count must be zero. Replicate the semantic/event signature across all three fresh workers. Capture a frozen source/native lock before workers and recheck after.

## Limits

The event establishes that a comparison read or dispatch was attempted at the rule boundary. It does not trace callback internals, identify callback graph effects, complete host/scheduler attribution, or establish access-trace completeness. Three tiny mechanism fixtures do not estimate frequency, performance overhead, or task-level locality. No general partition may rely on this vocabulary without separate coverage and parity evidence.
