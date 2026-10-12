# Deferred queue audit v2 preregistration

Date: 2026-09-26

## Question

Can the scale audit account for deferred rule work by queue family, distinguishing enqueue production inside an enumerated rule from between-pass drain batches, drained item counts, and drain wall time? Does the accounting conserve queue items and preserve full/scoped semantic controls on a mixed workload?

## Instrumentation

Add opt-in counters for five deferred families: `rule_edits`, `rule_patches`, `fb_samples`, `track_identity`, and `net_collapses`. Enqueue totals are globally attributed by family and per producer RuleIdx when scale audit is enabled. Each drain reports batch count, dequeued item count, and elapsed wall nanoseconds by family. Drained item count includes stale or rejected records. Queue entries do not currently retain producer identity, so drain cost cannot be assigned back to an individual producer rule. No queue scheduling, effect ordering, or apply semantics change.

## Workload and controls

Reuse the frozen mixed deferred-effect fixture containing one rule firing that enqueues one RulePatch, one TrackIdentity operation, and one NetCollapse operation. Sweep one, two, and four percept pairs, two replicates, and three arms: monolithic full closure, scoped closure only, and scoped closure followed by global fallback when deferred work remains. Each arm runs in a fresh process. Scale counters reset immediately before each settlement call and are captured immediately afterward; terminal cleanup is outside the measured counter window.

The independent oracle is the exact state already returned by the fixture: patch revision/status, all generated identities, network weights and surprise, observation/controller state, and output flags. Full closure and scoped-plus-fallback must match. Scoped-only must expose pending deferred work. For each family in full closure, enqueued items must equal drained items and exactly one drain batch must be recorded; per-rule rows must attribute the three enqueue families to the fixture's writer RuleIdx. Scoped-only is expected to enqueue the three records and drain none before reporting pending work. Fallback counters apply only to the fallback settlement phase.

## Provenance and limits

Lock protocol, runner, analyzer, Rust sources, binding, build manifest, and native extension before workers; record three process replicates at each size/arm and verify inputs after capture. The time counter includes the complete queue drain function, including validation and graph mutation, but excludes queue-production time, subsequent rule closure, and external host work. Instrumented timings are descriptive and include audit overhead. This single mixed fixture does not measure queue-family prevalence, scheduler scan cost, complete work outside a RuleUID, or general tractability.
