# Edge identity site scaling — current-source preregistration

Date: 2026-10-03

Repeat the rule-local `find_edge_identity_sites` field-count sweep against
current source. Use fresh synthetic rules with 1, 2, 4, 8, 16, 32, 64, 128,
and 256 direct bound attribute fields on one fresh-node `add_node` effect.
Also include one constant and one computed-valued field in each rule; neither
is an eligible identity dimension under the current direct-attribute grammar.

Run two warmups and seven timed calls per size. The expected eligible site
count is `m + choose(m,2) + 1[m>2]`, plus one relation-level edge site.
Require the observed site count and eligible field set to match this formula,
and require unsupported constant/computed keys to be absent from every
identity signature. Freeze the runner, analyzer, protocol, and current
`domains/edit_ops.py` hash before capture; preserve per-trial timing.

This isolates proposal-site discovery cost. `find_edge_identity_sites` takes a
rule, not a task graph, so this experiment cannot estimate materialization or
native Term selection cost as graph size grows. Report that boundary
explicitly; complete composer scaling on large host graphs is a separate gate.
No extrapolation beyond the measured field counts or this host is permitted.
