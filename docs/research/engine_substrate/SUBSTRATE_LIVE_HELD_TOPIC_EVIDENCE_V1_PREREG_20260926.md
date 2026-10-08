# Live held-topic evidence and answer release v1 preregistration (2026-09-26)

## Question

Can the live substrate apply separately ingested, graph-supported topic answers across independently authored content items and multiple comprehension routes, while refusing a same-turn unknown-topic control? What native candidate and Term work does evidence ingestion cost versus live query-and-release?

## Fixed evidence panel

In each fresh full-seed worker, use the production `learn_from_teacher` interface to ingest these three answer records before querying:

- `copper` → `Copper conducts electricity and heat.`
- `basalt` → `Basalt is a fine-grained igneous rock formed when lava cools quickly.`
- `hexagon` → `A hexagon has six straight sides and six angles.`

Then run these six turns in order, with `speech_act="question"` and speaker `alice`:

1. `What do you know about copper?` — `meta` dispatch with external-topic Goal.
2. `What do you know about basalt?` — `meta` dispatch with external-topic Goal.
3. `What do you know about hexagon?` — `meta` dispatch with external-topic Goal.
4. `What is copper?` — held table route.
5. `Can you tell me about copper?` — honest-capability comprehension route with held topic fulfillment.
6. `What do you know about unobtainium?` — unknown-topic negative control; replace `domains.topic_grounding.ground_topic` with a counted deterministic no-result stub for this turn only to prohibit network variability.

The fact answers, prompts, and route classifications are frozen from fixture selection. The pilot is not confirmatory and must not be pooled with the capture.

## Measurement and gates

Run three workers in distinct fresh processes. Lock the full Python/seed/native closure, this protocol, runner, native extension, build manifest, and commit. Record full-seed boot separately; measure each `learn_from_teacher` operation independently from each `converse` interval, resetting native audit counters at each boundary. Record candidate enumeration, tested candidates, Term evaluations/units, graph writes, elapsed time, and exact per-turn route/Goal/evidence/reply/release identity. Report whole-graph nodes/edges and the directly task-owned Message/Goal/HeldAnswer/TopicGroundingEvidence/receipt/reply subgraph, including boundary incidences.

Require stable source fingerprints, three PIDs, exact ordered route/answer signature replication, each positive answer equal to the held answer, one same-event `answer_topic` Goal keyed to the selected topic, supported referent-linked `TopicGroundingEvidence`, a released receipt whose surface equals the answer and commits the selected answer Goal or HeldAnswer, no answer leakage across facts, and the unknown control to remain unresolved with no copper surface and a counted no-result grounding call. Record Goal `status` and `outcome` separately; do not assume terminal status from a released reply.

This is one authored evidence/task panel. It does not estimate natural language coverage, retrieval quality, asymptotic complexity, or broad tractability. Failed semantic or provenance gates are retained and analyzed as failures; do not change prompts or expected routes after capture.
