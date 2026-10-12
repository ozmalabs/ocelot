# Stage A disjoint-pair mixed-write preregistration

## Question

Does Stage A compare mode derive and roll back a multi-variable rule drain when every binding touches a distinct node pair and replaces attributes on a pre-existing cross-node edge?

## Fixture and contrast

For binding counts 1, 2, 6, 16, and 32, create disjoint `(x,y)` pairs. Each pair has one `trigger` edge `x -> y`; a pre-existing `derived` edge `x -> y` begins with `{value:-1, marker:i}`. Node `x` begins with `watched=i+10`. One rule matches `(x,trigger,y)` and applies `AddEdge(x, derived, y, {value:Attr(x, watched)})`. Compare fresh identical graphs with Stage A compare disabled/enabled.

This targets a rule admitted by the static temporal/write coupling analysis; the runtime proposal conflict check must still establish node disjointness. A node-attribute write was removed because the static gate conservatively excludes any multi-variable rule writing a matched variable, even when this fixture's pairs are disjoint. The committed path remains authoritative in compare mode.

## Gates

Every size and replicate must have exact graph-dictionary equality, correct edge-attribute oracle values, exact pair and derived-edge counts, progress/terminal parity, at least one compared drain, and zero divergence, unsound drains, or conflict fallbacks. Run three fresh worker processes. Lock protocol, runner, Rust sources, native extension and manifest, and commit at each worker's start/end.

## Claim boundary

This covers only disjoint two-variable pairs and pre-existing edge-attribute replacement. It does not establish correctness for overlapping pairs, shared hubs, node writes, read/write coupling across bindings, deletions, minting, wider rule interactions, or natural workload prevalence.
