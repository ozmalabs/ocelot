# Anaphora join-order v1.1 current-source amendment

Date: 2026-09-28 local

The v1.0 capture completed at 2026-09-28 05:59 local with stable input hashes. A subsequent `substrate/world_adapter.py` edit was observed at 06:03 local and changed that file's SHA-256 from the captured `7dceff…57fd79a` to `15cb8f…2b77c2c`. The run manifest therefore describes a valid but no-longer-current adapter snapshot. The file's current changes are broad; this amendment does not assume they are irrelevant to task ingestion.

Version 1.1 repeats the exact registered 48-worker design against the current source, uses a new source/native lock and separate raw/analysis paths, and retains all v1 captures. The task, oracle, seed closure, worker count, counters, and analysis gates do not change. The v1.0 result remains valid only for its recorded input hashes; do not pool timing or candidate counts across source versions unless exact parity is established.
