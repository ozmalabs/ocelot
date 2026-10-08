# Preregistration: scoped fallback for graph-native RulePatch transactions

**Question.** When scoped settlement queues a graph-native RulePatch transaction, does the pending flag followed by global closure commit the rule revision and reach the same downstream state as ordinary full closure?

**Why this queue.** This is distinct from deferred graph-attribute writes and numerical weight updates: draining the queue mutates the live rule vector, refreshes its derived access/JIT state, and writes a durable receipt back into the graph. The changed rule then fires against frame-owned output state.

**Frozen matrix.** One, two, or four output frames; two fresh-process repeats; three arms (`full`, `scoped_only`, `scoped_fallback`). A graph-authored `RulePatch` targets a uniquely named, unprotected rule at its current UID/revision/content-hash. It changes that rule's `where` clause from `Lit(false)` to `Lit(true)`. The target rule has one shared signal and writes a completion attribute on each frame-owned output. A controller-owned writer queues `ApplyRulePatch` once and marks its trigger done. The scoped arm has a one-progress-step budget; fallback runs global closure only after `deferred_effects_pending` is true.

**Gates.** Scoped arms must hit the one-step budget and report pending deferred work. Full and fallback arms must reach fixed point; terminal closure is zero-work. Fallback must exactly match full on target rule revision/content hash, patch receipt status/revision, controller trigger, and every frame output. The scoped-only control must retain a pending receipt, unchanged revision, and no completed outputs. Fresh PIDs and all locked hashes must match.

**Claim boundary.** This tests one RulePatch `where` transaction and a small frame-output family. It does not establish arbitrary rule-edit safety, concurrent patch behavior, multiple-queue interactions, fallback cost, natural task prevalence, or complete dependency notifications. No engine behavior is modified.
