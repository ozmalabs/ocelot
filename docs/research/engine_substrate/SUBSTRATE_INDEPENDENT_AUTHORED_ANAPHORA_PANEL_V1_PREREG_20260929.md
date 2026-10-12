# Independently authored anaphora transfer panel v1 preregistration

Date: 2026-09-29, before source lock and capture.

## Question and claim boundary

Measure whether ordinary default-boot message ingestion and comprehension
resolve a small set of separately authored cross-turn reference tasks, including
antecedent variation, recency, a three-turn pronoun chain, deictic forms, and
negative controls. The fixed cases and independent expected referents are in
[`anaphora_independent_task_suite_v1.json`](../../../evaluation/substrate_capability/anaphora_independent_task_suite_v1.json).

This is a narrow, assistant-authored surface-transfer probe for one existing
held-structure route. It is not a natural-language sample, an independent
human-authored benchmark, evidence of learned acquisition, or a general
language capability estimate. PersonaChat files are excluded because the
repository's standard learning path consumes that corpus and persisted learned
state is present.

## Frozen protocol

For every suite row, construct a fresh `WorldAdapter()` and process each turn
in order using only `receive_utterance(..., speech_act="statement",
speaker="user")` and `comprehend()`. Do not change rules, seeds, or the suite.
The independent oracle is the literal expected referent and Intent membership
in the suite, not the system output. Unknown and first-turn cases are negative
controls. Run ten fresh worker processes, each covering the complete suite in
fixed order, with one new adapter per case.

Lock the suite, protocol, runner/analyzer, production adapter and language
sources, relevant resolved seeds, native extension/build manifest, Rust closure
sources, and Cargo lock. Separately time adapter initialization and every
receive/comprehend call. Save projections, full-graph digests, graph sizes,
worker CPU/wall time, and peak RSS. Require stable inputs, unique PIDs, complete
coverage, exact case oracles, and repeatable per-case graph digests.

## Interpretation

Report per-case oracle outcomes, failures, and resource distributions. Do not
pool the 110 case-worker rows as an accuracy estimate or replace failed inputs.
Passing would establish only the enumerated behavior under the measured build;
failing cases delimit this route's current surface/recency envelope.
