# Anaphora transfer panel v1.1 amendment

Date: 2026-09-29, before the v1.1 lock and capture.

## Reason

The v1 capture passed the five functional oracles in ten fresh processes, but
its runner timed each case as one interval containing both `WorldAdapter()`
construction and utterance processing. The preregistration requires boot and
task operation costs to be separable. The v1 raw record is retained and is not
relabelled as satisfying that timing gate.

## Change and frozen scope

Repeat the same five cases, same fixed order, ten fresh processes, default
production APIs, negative controls, and exact semantic oracles from v1. Make no
case, input, rule, seed, or success-criterion changes. In v1.1 separately time
`WorldAdapter()` construction for each case; retain the combined
adapter-plus-case interval as a conservation check. All receive/comprehend
intervals remain separately recorded. Use new runner, analyzer, protocol,
lock, raw, and analysis paths. The v1 lock and captures remain immutable.

## Gates

Require all v1 semantic, graph-repeatability, fresh-process, and source/native
fingerprint gates, plus positive adapter initialization wall/CPU measurements
for every case and a worker-time accounting check that adapter initialization
and turn operations are contained within the recorded adapter-plus-case
interval (allowing clock-call overhead). Report any timing-accounting gate
failure; do not use v1.1 as a cost result if it fails.
