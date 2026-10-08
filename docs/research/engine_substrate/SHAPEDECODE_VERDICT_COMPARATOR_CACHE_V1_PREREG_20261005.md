# ShapeDecode verdict-comparator cache v1 — preregistration

**Question:** Does the parsed-codebook cache improve a second seed-authored candidate-at-a-time ShapeDecode route, using the existing `vision_verdict_comparator` graph rules and `VdSignature` codebook?

## Design

Replay the seed's active V0 `hamming` arm on one Observation orbit per fresh Substrate. The seed itself supplies the nested ShapeDecode under `MaxOver` and `Argmax`; the harness constructs a 16-part held codebook plus 0/16/48/112 distractors (nominal totals 16/32/64/128 plus any seed-authored VdSignature nodes), and presents the exact tile held as `r00`. Use five paired replicates, scan/cache mode, and traced/untraced runs (80 workers). Each replicate shares the generated tiles and insertion order across modes. Shuffle the locked case order with seed 20261006.

## Gates and measurements

Lock the engine binary, Rust source, seed JSON, world adapter, runner, analyzer, and protocol. Use unique fresh processes and source-manifest validation. Require exact graph-produced winner/readback parity, all workers to choose `r00`, traced/untraced outcome parity, complete traces, and scan/cache closure-work parity. Record VdSignature population visits, parsed parts, cache hits/misses, candidate work, untraced closure wall/CPU time, and RSS. This is an end-to-end rule-closure replay with an existing seed-defined term shape; it does not establish natural-task prevalence or general tractability.

## Boundary

This route exercises an existing authored evaluation seed rather than an independently sampled production interaction. It measures one probe per substrate, one active comparator arm, 16 true regions, one resolution, and one-host closure. It does not cover Surface(Text), malformed codebook entries, exclusions, multi-probe cache lifetime, larger region counts, mutation lifecycle, or natural-task distribution.
