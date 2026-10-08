# Order-sensitive scoped/full continuation v3.1 amendment

Date: 2026-10-01

## Pilot stop and protocol correction

An unguarded shared-sink last-match pilot was started before the preregistered capture. It did not reach a terminal report within 30 seconds. The rule rewrote the shared sink once per binding; each subsequent pass alternated values within the drain and therefore continued to report progress. The worker process was interrupted, and process inspection found no remaining worker. It produced no raw capture and is excluded from all counts and claims.

Before creating the source/native lock, the protocol and runner were revised to make the continuation one-shot: the rule checks `Not(Eq(Attr(sink, "probe_done"), true))`, writes the selected NodeID for each binding in its first drain, then sets `probe_done=true`. The marker makes subsequent matching fail, allowing fixed-point settlement while preserving last-match behavior within the collected binding snapshot. No locked data had been captured under the unguarded version.

## Confirmatory result

The locked v3 run completed 27 fresh workers and passed the selected-node equality gate in all 27. Strict byte-order graph parity still fails in 18/27 because final edge-vector order differs; the canonical state/order analysis finds the same node arrays and edge-fact multisets in all 27. The strict failure and the pilot stop remain disclosed in the [v3 result](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V3_RESULTS_20261001.md).
