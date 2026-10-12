# Scoped pending and global fallback for remaining queues v1 preregistration

Date: 2026-09-26

## Question

When a scoped settlement fires writers that enqueue `SetRuleClause` and `FbSample`, does it leave both queue families pending, and does ordinary global fallback drain them and recover the full-closure graph?

## Design

For `N={1,2,4,8}` independent writer/target pairs, three fresh-process replications construct equivalent full, scoped-only, and scoped-then-global-fallback arms. Each writer queues one rule edit and one sample and deletes its trigger. Scoped settlement starts from one `Microtheory` owner linked to all anchors and uses a progress budget of 10,000 so every independent writer can fire. Full and fallback arms must converge to the same whole-graph state; scoped-only must report pending deferred effects and is expected to remain incomplete.

Audit captures are split at the scoped/fallback boundary. Scoped phases must enqueue `N` items per family and drain none. Full closure must enqueue/drain `N` items in one batch per family. Fallback phase begins with the queued records already pending, so it must enqueue none and drain `N` items in one batch. Every writer must receive producer attribution for both enqueues.

## Limits

This is a synthetic owner-linked fixture, not a general scoped-closure correctness proof. It tests only `rule_edits` and `fb_samples`; prior v2 covers scoped pending/fallback for RulePatch, TrackIdentity, and NetCollapse. It measures queue correctness and parity, not natural queue prevalence or throughput. Framebuffer I/O is a local static shared-memory frame.
