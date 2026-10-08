# Default-boot anaphora transfer panel v1 preregistration

Date: 2026-09-29, before capture.

## Question

Does the measured default-boot production route preserve its narrow anaphora
behavior across distinct antecedent shapes, pronouns, and a three-turn chain,
and what CPU/wall/RSS envelope does this small transfer panel have?

This is a task-derived functional and operating-cost panel. It is not a
natural-dialogue sample, a general language capability estimate, a frame
locality result, or evidence that the system learned the rule during these
tasks. The grammar, seed concepts, and rule are held structure.

## Frozen cases and oracle

Each case uses a fresh `WorldAdapter()` and only the ordinary
`receive_utterance` and `comprehend` APIs. Scale-audit counters remain off.

| Case | Turns | Expected result |
|---|---|---|
| `three_turn_it_chain` | `the question is hard`; `i need it answered`; `consider it` | Final `it` refers to `question`; final Intent has `question` in `about_concept` |
| `this_transfer` | `the question matters`; `explain this` | Final `this` refers to `question` and Intent carries it |
| `that_transfer` | `the question matters`; `explain that` | Final `that` refers to `question` and Intent carries it |
| `unknown_antecedent_negative` | `the foobletwizz exploded`; `consider it` | Final `it` has no `refers_to` edge and no inherited `about_concept` |
| `unresolved_first_turn_negative` | `answer it` | `it` has no `refers_to` edge |

These cases are adapted from the existing anaphora integration fixtures in
`tests/test_intent_migrated.py`; they are not represented as independently
authored or held-out tasks. The negative controls prevent a transfer score
from counting indiscriminate binding as success.

## Capture and gates

Run ten fresh worker processes, each executing all five cases in the fixed
order with a new default adapter per case. Lock the protocol, runner, analyzer,
oracle source, default boot and ingestion sources, resolved seed manifests,
native extension/build manifest, Rust closure sources, and Cargo lock. Require
distinct process IDs, stable pre/post fingerprints, all case rows, exact
pronoun/referent/Intent oracles, and repeatable graph digests per case. Record
adapter construction, each receive/comprehend wall and process-CPU interval,
process peak RSS, and total worker CPU/wall. Do not fold process launch or
post-task readback into the per-turn operation times.

The result reports per-case success and resource distributions. It does not
pool cases into an accuracy estimate or extrapolate a production throughput.
Any failure is retained as a failed row; no case may be replaced after capture.

## Outputs

Versioned source lock, raw per-worker records, independent analyzer output,
and a concise results note. This capture supplements the two-turn cost profile;
it does not replace it.
