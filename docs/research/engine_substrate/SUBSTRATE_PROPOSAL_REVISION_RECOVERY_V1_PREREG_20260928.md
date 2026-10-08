# Staged proposal-revision recovery v1

## Question

Can revision-stamped max/count/decision stages fail closed while incomplete, then resume after an interruption and commit only a complete, internally consistent result?

## Protocol

Use three fresh workers and N=2/8/32/64. Build one proposal graph and settle revision 0 completely. Lower the prior winner's score, create revision 1, and inject cuts after 0, 1, 2, or 3 of the max/count/decision closures. Every derived field carries its own revision stamp; `resolved_revision` is updated only by a commit rule whose guard requires all three stamps to equal the current event revision. Before resuming, capture whether current revision 1 is committed and the stamps on max/count/decision. A recovery driver reads those stamps, executes missing stages in order, then runs commit. The independent score oracle checks the final state. Record native work per stage, graph/event sizes, and cut/resume decisions.

## Gates

All setup and resumed closures must reach fixed point. Before commit, a cut state must never advertise `resolved_revision=1`. Resume must run exactly the missing stages and commit only after all stamps equal 1. Final maximum, tie count, ambiguity, and selection must match the Python oracle. All four cutpoints pass in all workers and sizes. Integer work counters replicate across workers, ignoring time fields. Revision event retention remains bounded to one current event.

## Limits

Cuts are injected between completed closure calls in one live process. This does not test process termination, durable graph persistence, torn native effects inside a single closure, concurrent updates, or crash recovery across a machine restart. It establishes fail-closed stage recovery only for the authored protocol and fixture.
