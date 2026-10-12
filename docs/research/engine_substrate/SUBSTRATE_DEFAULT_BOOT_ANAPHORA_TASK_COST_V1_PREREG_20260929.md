# Default-boot anaphora task cost v1 preregistration

Date: 2026-09-29, before confirmatory capture.

## Question and scope

Measure default adapter boot and a two-turn, independently authored anaphora
task through the ordinary user-facing `WorldAdapter.receive_utterance` and
`WorldAdapter.comprehend` APIs. This complements the bare-adapter selective
seed-load profile with default core boot and lazy intent/discourse seed loads.
It is one frozen task, not a natural conversation distribution or general
throughput estimate.

## Frozen task and execution

Use the existing anaphora task/oracle from `tests/test_intent_migrated.py`:
first ingest and comprehend `the question matters`, then ingest and comprehend
`answer it`. Use `WorldAdapter()` with its default core seeds; do not supply
`seeds=()`, remove/re-add rules, enable audit counters, use `run_rules_report`,
or substitute direct graph construction for utterance ingestion. Record
default adapter construction, each receive call, each comprehend call, first
and second message seed inventory, installed target-rule match order, the
second message's `it` referent and Intent `about_concept`, complete graph
digests, graph sizes, process CPU/RSS, and phase wall/CPU time.

After measuring the two-turn task output, separately run ordinary native
closure until a no-progress probe: record the first post-task `run_rules`
progress and time, then a second `run_rules` progress/time and require zero
progress plus unchanged graph identity. Do not include this diagnostic settle
in the measured two-turn task span. This distinguishes user-facing task
completion from a full native fixed-point check.

Run ten fresh processes with identical inputs and distinct PIDs. Scale audit
counters remain disabled throughout. Lock the runner, analyzer, protocol,
test oracle source, WorldAdapter, seed loader/registry, relevant seed
manifests, native binary/build manifest, and native engine source.

## Gates

- Ten unique fresh PIDs and stable source/native fingerprints.
- The second message's `it` Mention refers exactly to Concept `question`; its
  Intent exists and `about_concept` includes `question`.
- All workers have the same task-output projection and complete terminal graph
  digest; report first/second receive and comprehend progress separately.
- Post-task native closure is followed by a zero-progress, unchanged-graph
  probe; if the first settle makes progress, report that separately.
- Scale counter snapshots remain all zero; report medians, ranges and every
  worker without outlier deletion.

No latency threshold is preregistered. Process launch and source fingerprint
time are outside the child task span; the result remains a small task-specific
operational profile.

## Development smoke disclosure

Before locking, one excluded worker verified that default boot plus the
two-turn task passes the reference oracle. It observed 17 configured core
seeds, then lazy graph Seed records for `conversation`, `intent`, `psychology`,
and `relations` after the first receive; the second receive added none. Both
turns comprehended, and the post-task settle and terminal probe made no
progress. The smoke did not select timing thresholds or alter the ten-worker
design; its raw file is a temporary harness check, not confirmatory evidence.
