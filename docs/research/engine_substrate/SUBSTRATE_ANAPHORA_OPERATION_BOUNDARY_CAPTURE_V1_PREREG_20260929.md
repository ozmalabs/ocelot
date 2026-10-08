# Anaphora operation-boundary capture v1 preregistration

Date: 2026-09-29, before source lock and capture.

## Question and claim boundary

For the eleven frozen assistant-authored anaphora tasks, what boundary does
ordinary per-utterance comprehension expose in the complete substrate graph,
and do runtime-observed node pairs favor the task's turn ownership over
balanced-ID and dependency-min-fill partitions?

This is a structural diagnostic on one small held-structure task family. It is
not a natural-task locality estimate, a learned-frame result, a completeness
claim for runtime tracing, or evidence that partitioned execution is safe or
faster. The general Microtheory-scoped engine API is not presumed to implement
these message frames.

## Frozen task and ownership convention

Use the input cases in
[`anaphora_independent_task_suite_v1.json`](../../../evaluation/substrate_capability/anaphora_independent_task_suite_v1.json)
without changing text, order, or expected labels. Each turn's frame is the
message plus every graph node first created during that turn's
`receive_utterance`/`comprehend` interval, except nodes of these predeclared
shared resource types, which remain global/unassigned in every partition arm:
`Agent`, `Concept`, `CommonGround`, `DiscourseState`, `Interlocutor`,
`LexicalEntry`, `Rule`, `Seed`, and `SeedSummary`. Any task node not assigned by
this rule is a protocol failure; a global node may not be reassigned after
dependency inspection. This is explicit operational ownership, not a learned
partition.

For each case execute paired fresh adapters in one fresh worker process:
ordinary tracing-off and runtime-access-tracing-on. Both use the same default
boot and production ingestion APIs. Trace only the `comprehend()` closure for
each turn; report receive-time/out-of-rule accesses as unobserved. Capture the
complete final graph, all node types and attributes, per-turn ownership, trace
rows and drops, active static rule read/write declarations and wildcard flags,
and the independent anaphora projection/oracle. Run ten fresh worker
processes. Exact trace-mode/off graph and task-oracle parity is required.

## Partition comparison

For each traced checkpoint and the final graph, keep dependency classes
separate:

1. all concrete typed state-graph edges;
2. observed runtime access endpoint pairs from the trace;
3. static rule read/write key sets and wildcard flags, without fabricating
   node pairs for key-only/wildcard declarations.

Compare exactly three partitions over the assigned turn-owned nodes, leaving
all global nodes explicit:

1. frozen turn ownership;
2. balanced stable-ID groups, matching the frozen frame-size multiset;
3. dependency-min-fill: deterministic min-fill over the undirected union of
   concrete state edges and observed access endpoint pairs, tie-broken by
   stable node ID, grouped in min-fill order to the frozen frame sizes.

At each checkpoint report owner sizes, cross-frame concrete edges, global
boundary incidences, cross-frame and global-boundary trace counts, pairwise
co-ownership recall against the frozen ownership, separator/boundary node
sets, and min-fill induced-width upper bound. Also report static potential
coupling separately. Report discovery/export/partition cost separately from
comprehension time. This capture does not attempt scoped closure: record that
cell as `unsupported_generic_message_scope` because the existing scoped API is
not message-frame based. Do not interpret state-graph width as inference
treewidth.

## Gates and outputs

Require ten distinct processes; matching before/after locks; exact case and
turn coverage; all positive and negative task oracles; trace-on/off semantic
graph parity; zero trace drops; exactly one owner per non-global task node;
complete graph identity/type/attribute readback; independent partition-metric
reconstruction; and preservation of static wildcard declarations. Any failed
gate makes the affected metric inconclusive; no workload repair or partition
retuning is allowed after capture.

Keep raw per-worker full graphs, traces, lock, independent analysis, and a
results note. A later scoped-execution study requires a separate native
message-frame ownership contract, boundary notifications, and exact
monolithic parity/omission controls.
