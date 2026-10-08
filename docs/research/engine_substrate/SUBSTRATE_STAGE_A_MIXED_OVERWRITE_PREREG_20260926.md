# Stage A mixed overwrite rollback preregistration

## Question

Does Stage A compare mode correctly derive, undo, and reconstruct a multi-binding rule drain that combines a node-attribute overwrite with an overwrite of attributes on pre-existing edges?

## Fixture and contrast

For binding counts 1, 2, 6, 16, and 32, create independent self-loop `trigger` matches. Each node begins with `watched=i+10`, `observed=-1`; each has a pre-existing self-loop `derived` edge with `{value:-1, marker:i}`. One rule applies `SetAttr(x, observed, Attr(x, watched))` and `AddEdge(x, derived, x, {value:Attr(x, watched)})`. Compare fresh identical graphs with Stage A compare disabled/enabled. Stage A compare is diagnostic: it derives each proposal, undoes it, then ordinary closure commits the reference result.

## Gates

For every size and replicate require exact graph-dictionary equality between arms, all node observations equal their input `watched` values, each derived self-edge has exactly `{value:watched}`, no duplicate edges, progress/terminal behavior parity, at least one Stage A compared drain, and zero divergence, unsound drains, or conflict fallbacks. Run three fresh worker processes and lock source, extension, build manifest, protocol, runner, and commit at worker start/end.

## Claim boundary

This isolates `SetAttr` plus existing-edge attribute replacement across independent one-variable bindings. It does not establish behavior for contended/multi-variable bindings, deletes, mints, rule order interactions, concurrent writers, or production workload distributions.
