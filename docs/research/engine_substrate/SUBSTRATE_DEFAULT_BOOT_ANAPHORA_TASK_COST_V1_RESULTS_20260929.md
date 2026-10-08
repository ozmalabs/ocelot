# Default-boot anaphora task cost v1 results

## Result

The locked current-source capture completed ten fresh processes and passes
**88/88 independent checks**. Every worker used `WorldAdapter()` with its
default 17-seed core configuration, then ran the frozen user-facing task via
`receive_utterance` and `comprehend`: “the question matters” followed by
“answer it.” The first receive lazily added the graph Seed records for
`conversation`, `intent`, `psychology`, and `relations`; the second added no
new seeds. All workers resolved the second message's `it` to `question`, and
its Intent includes `question` among the `about_concept` values. The target
rule readback is identical across workers. Native post-task settle and
terminal probe both make zero progress; complete task and terminal graph
digests match across all ten runs. Scale counters remain zero.

| Stage | Median wall | Median CPU | Wall range |
|---|---:|---:|---:|
| Python module imports in worker | 5.10 ms | 5.10 ms | 4.79–6.11 ms |
| Default adapter/core boot | 30.84 ms | 31.13 ms | 26.50–72.84 ms |
| First receive, including lazy seed load | 33.23 ms | 33.12 ms | 31.92–34.58 ms |
| First `comprehend` | 432 μs | 433 μs | 424–543 μs |
| Second receive | 104 μs | 104 μs | 100–120 μs |
| Second `comprehend` | 272 μs | 273 μs | 250–315 μs |
| Two-turn measured worker span | 85.09 ms | 85.22 ms | 81.18–129.36 ms |

Median peak RSS was **45,060 KiB** (range 44,572–45,768 KiB). The worker span
excludes process launch and pre-task source fingerprinting. Timed stages leave
about 15 ms of its median in task projection, graph snapshot/digest, and
harness readback, which remain to be separately attributed. The adapter-init
wall tail is broad, and the full-span maximum is 129 ms; this small sample does
not establish a latency bound.

## Interpretation and limits

This is stronger path coverage than the bare-adapter seed replay: it includes
default core boot, lazy seed acquisition through `receive_utterance`, and the
ordinary `comprehend` path on a second authored rule topology. It is still one
two-turn synthetic benchmark selected from an existing functional test, not a
conversation-distribution sample or broad capability estimate. The seed and
rule topology changes after the first message, while no scale counters were
enabled; the counter-on overhead result from the separate discourse fixture
must not be used to adjust these timings.

Next expand to longer held-out utterance sequences and an independently
authored production ingestion task, instrument graph readback separately, and
collect counter-off timing with task-quality oracles under a locked route.

## Artifacts

- [Preregistration](SUBSTRATE_DEFAULT_BOOT_ANAPHORA_TASK_COST_V1_PREREG_20260929.md)
- [Runner](../../../scripts/substrate_default_boot_anaphora_task_cost_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_default_boot_anaphora_task_cost_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/default_boot_anaphora_task_cost_v1_lock_20260929.json)
- [Ten-worker raw capture](../../../evaluation/reports/default_boot_anaphora_task_cost_v1_raw_20260929.json)
- [Independent analysis](../../../evaluation/reports/default_boot_anaphora_task_cost_v1_analysis_20260929.json)

Claim boundary: one two-turn task on default boot and ordinary utterance and
comprehension APIs. No natural prevalence, general conversation quality,
throughput, broad runtime scaling, or general capability claim follows.
