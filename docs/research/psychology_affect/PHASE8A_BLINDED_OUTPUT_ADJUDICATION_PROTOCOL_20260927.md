# Phase 8A blinded output adjudication protocol v1

**Status:** Superseded before annotation by the dated v2 amendment below.
No packet was produced and no annotations were collected under v1.

**Scope:** Blinded scoring of the fixed 74-event v5 response traces for the
conversational manifold, ELIZA floor, Gemma 3 4B CPU, and Qwen 3.5 9B CPU.
This protocol does not create human-response references and does not score
memory, learning, provenance, or cost from prose.

## Sampling and blinding

1. Use the same 74 fixed event IDs and event order. A packet contains the
   current signal, interaction mode/relation, held facts supplied for that
   event, the preceding eight signal/response pairs from that response track,
   and the response being rated. Do not include corpus labels, expected state,
   dispatch path, system/model name, seed, or runtime trace in the rater view.
2. Randomize response aliases independently within each case. The same alias
   must not identify a system across cases. Keep the alias-to-system/run key
   outside the rater packet and do not disclose it until both independent
   annotation files are locked.
3. Two raters independently score every applicable response. They may not
   consult system identity, expected corpus labels, or one another's scores.
   A third adjudicator resolves disagreements only after both files are
   locked; retain both original labels and the adjudication record.
4. Raw records establish that the Gemma seed-42/43 and Qwen seed-42/43
   responses are identical across all 74 cases. Therefore annotate one unique
   response per model/case, cite both repeated raw runs as repeatability
   evidence, and do not count the duplicate seeds as independent samples.
   ELIZA and the target each contribute their single current v5 response per
   case. If a response pair ceases to be identical on a later collection,
   revise the sampling plan before annotation rather than silently collapsing
   different outputs.

## Per-response rubric

Raters assign `1.0`, `0.5`, or `0.0` for each applicable behavioral dimension.
Use `not_applicable` only when the event cannot test that dimension under the
fixed annotations; record the reason. Every `0.5` or `0.0` requires a short
evidence note quoting or pointing to the relevant input/context/response span.
Fluency, length, politeness, and stylistic preference are not independent
grounds for a higher score.

| Dimension | 1.0 | 0.5 | 0.0 |
|---|---|---|---|
| Interpretation | Identifies the communicative move and its material content/target. | Move is broadly right but a material role, scope, or target is uncertain/wrong. | Wrong move/target, or no interpretable response when one is required. |
| Grounding | Referential and factual content is supported by the visible input, supplied history/facts, or explicitly marked uncertainty. | Core referent is supported but a material relation/detail is unsupported or left unresolved. | Invents or misbinds material content, or presents unsupported content as established. |
| Action | For action cases, performs/reports only the authorized requested action, or appropriately refuses/defers when blocked. | Partially addresses the action or leaves a material execution status unclear. | Wrong/unauthorized action, false execution claim, or misses the required action boundary. |
| Repair | Requests the missing information when needed, targets the actual gap, and proceeds without needless repair when enough evidence exists. | Repair is relevant but too broad, incomplete, or unnecessary. | Fails to repair a material ambiguity/gap, or blocks a sufficiently supported task with irrelevant repair. |
| Calibration | Confidence, uncertainty, and limits match available evidence; diagnostic failure is explicit when needed. | Slight over/understatement that does not reverse the decision. | Material overclaim, false certainty, concealed failure, or unsupported refusal. |

Applicability is determined from the fixed Phase 0 case annotations, but those
labels remain hidden until the independent score files are locked. A reply
surface alone cannot prove execution, world truth, memory, or learning.

## Aggregation and reporting

- Resolve adjudication first, then unblind and join scores to case IDs and
  system/run provenance.
- For each system and behavioral dimension, average the adjudicated per-case
  scores over applicable cases; report the denominator, excluded/not-applicable
  case IDs, failures, and case-level scores.
- Use a paired nonparametric bootstrap over fixed case IDs (10,000 resamples,
  with replacement) for the 95% percentile interval. Resample the same case
  indices jointly across systems. The two duplicate LLM seeds do not increase
  `n`; each event is one independent case unit in this fixed-suite estimate.
- Report exact agreement and weighted Cohen's kappa for the two raters before
  adjudication. Do not hide disagreement behind the final score.
- Keep `memory` and `learning` unavailable until a separately preregistered,
  comparable probe set exists; keep `provenance` tied to raw/system traces and
  `cost` tied to raw resource measurements and an explicit normalization
  denominator. Never infer any of these four from response wording.
- This packet can at most make interpretation, grounding, action, repair, and
  calibration eligible for scoring. It cannot by itself make Phase 8
  empirically complete or release the comparative gate.

## Current input evidence

The current matched v5 raw files are:

- target: `evaluation/reports/phase8_corpus_report_20260927_event_scoped_reference_v3.json`;
- ELIZA: `evaluation/reports/phase8_eliza_floor_event_context_v5_history8_20260926.json`;
- Gemma 3 4B CPU: seed 42 and seed 43 reports dated 2026-09-25;
- Qwen 3.5 9B CPU: seed 42 and seed 43 reports dated 2026-09-26.

The v1 draft's assertion that both seeded pairs matched was incorrect. The
machine comparison actually confirms 74/74 exact matches for Gemma, while
only 1/74 Qwen outputs match (73 differ). See the v2 amendment below; it
supersedes the v1 sampling statement before packet creation.

## Dated amendment v2 — 2026-09-27

The response comparison was rerun before packet generation. Gemma seed 42/43
outputs match exactly on 74/74 cases and are represented as one anonymous
track, with both runs retained in private provenance. Qwen seed 42/43 outputs
match on only 1/74 cases, so both remain distinct anonymous tracks with their
own preceding-eight-turn histories. Each case therefore contains five tracks:
target, ELIZA, Gemma, Qwen seed 42, and Qwen seed 43.

For inference, first average the two Qwen seed scores within each case, then
compare systems over the 74 paired case units. Do not treat 148 Qwen outputs as
independent cases. The two Qwen tracks are repeat observations nested within
case; report their within-case differences separately. The existing case-paired
bootstrap resamples the 74 case IDs and preserves that nesting.

The packet generator is versioned as schema v2. The rater packet contains no
system names, seed values, corpus labels, or runtime traces; a separate private
key maps each per-case alias to system and, for Qwen, run index. This amendment
corrects sampling only; the rubric, score dimensions, blindness rules, and
limits on memory/learning/provenance/cost remain unchanged. No scoring has
occurred, and Phase 8 remains blocked pending independent annotation,
adjudication, and comparable evidence for the remaining release dimensions.
