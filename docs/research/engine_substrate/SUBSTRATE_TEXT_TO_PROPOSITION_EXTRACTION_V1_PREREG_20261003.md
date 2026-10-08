# Text-to-proposition extraction v1 preregistration

Date: 2026-10-03  
Runner: [`text_to_proposition_extraction_v1.py`](../../../evaluation/substrate_capability/text_to_proposition_extraction_v1.py)  
Cases: [`text_to_proposition_extraction_v1_cases_20261003.json`](../../../evaluation/substrate_capability/text_to_proposition_extraction_v1_cases_20261003.json)

## Question

Before episodic memory and answer generation, does the substrate's ordinary comprehension front end convert raw fact statements into the intended role-bearing neutral proposition, preserve counterbalanced values and polarity, and classify a matching query target?

## Design

Run each of seven fixed utterances three times on a fresh empty `WorldAdapter` graph. Invoke `domains.comprehend_text.comprehend_text` directly, which is the parser used by the live `WorldAdapter` routes, to isolate comprehension from turns, boot profiles, memory, and reply generation. Inputs include the prior positive pair (14 and 29), punctuation and lexical paraphrases, negation, and the matching question. Capture the composed relation, gaps, parser dispatch, expected proposition fields, and query target. The question arm tests only target classification; it does not claim a retrieval request was made.

## Scoring

For assertions, score value, subject/source, predicate, and polarity separately against the fixture's role-bearing target (`speaker` / `has_secret_code` / exact value / affirmed or negated). A complete proposition requires all four fields. For the question, score the exact `my secret code` target in the parser dispatch. Report each case and replicate, plus each component count. Integrity requires all expected rows, expected statement/question classification, stable locked sources, and no missing or extra captures.

## Limits

This direct isolated assay measures the actual comprehension function without the full conversational boot. It is diagnostic of the text-to-relation stage and not an end-to-end conversation outcome. Empty-graph behavior can differ from fully seeded production parsing; interpret alongside the prior live conversation capture, which used full boot and independently records the exact 14/29 asymmetry. No language model or external semantic provider participates. No value match by itself establishes correct proposition structure or truth. The downstream query-to-memory handoff is scored in a separate gate.
