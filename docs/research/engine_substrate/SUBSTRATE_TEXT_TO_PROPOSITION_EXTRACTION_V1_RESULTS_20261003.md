# Text-to-proposition extraction v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_TEXT_TO_PROPOSITION_EXTRACTION_V1_PREREG_20261003.md)  
Runner: [`text_to_proposition_extraction_v1.py`](../../../evaluation/substrate_capability/text_to_proposition_extraction_v1.py)  
Cases: [`text_to_proposition_extraction_v1_cases_20261003.json`](../../../evaluation/substrate_capability/text_to_proposition_extraction_v1_cases_20261003.json)  
Lock: [`text_to_proposition_extraction_v1_lock_20261003.json`](../../../evaluation/substrate_capability/text_to_proposition_extraction_v1_lock_20261003.json)  
Raw capture: [`text_to_proposition_extraction_v1_raw_20261003.json`](../../../evaluation/reports/text_to_proposition_extraction_v1_raw_20261003.json)

## Result

All 21 parser calls (seven utterances, three fresh empty graphs per utterance) passed integrity checks and all 21 locked source/input hashes matched. Among the 18 assertion calls, exact value recovery is 15/18, but complete role-bearing proposition recovery is 0/18. Component results:

| Component | Correct | Scored | Observation |
|---|---:|---:|---|
| Exact value | 15 | 18 | All `14` variants pass; `29` is missing in all three baseline captures |
| Subject/source | 0 | 18 | Possessive forms produce subject `secret`; active paraphrase produces `I`; no speaker role |
| Predicate | 0 | 18 | Baseline forms produce predicate `code`; active paraphrase produces `use`; none yields target `has_secret_code` |
| Polarity | 0 | 18 | No polarity field is present, including on the negated statement |
| Complete target proposition | 0 | 18 | No assertion has all expected relation, speaker role, value, and polarity |
| Query target | 3 | 3 | Parser selects `my secret code` as a `table`/`know` target |

The full-boot live capture independently has the same 14/29 asymmetry, supporting transfer of that specific failure into the actual text route. The query target score is only a parser dispatch result: the paired live graph audit finds no `MemoryRetrievalRequest`, so it is not retrieval handoff. See the [live/structured boundary audit](../../../evaluation/reports/live_structured_memory_boundary_v1_audit_20261003.json).

## Interpretation and limits

The front end often locates a surface value but does not form the neutral predicate/argument/polarity record required by the proposition ingress. Its gap list notices `not` and unrecognized `29`, but this is not yet a usable typed proposition or calibrated uncertainty. The parser can classify a query target; the downstream query-to-memory edge remains absent in the measured live route. Empty-graph direct results isolate the parser and are not production end-to-end metrics. No external LLM or semantic provider supplied the answers in this assay.

## Next gate

The immediate bridge should be evaluated against these same locked cases: measure any upstream extractor separately, then pass its structured record to the explicit-ingress contract panel and onward to episodic memory. Require counterbalanced-value parity, explicit source/polarity and ambiguity handling, and held-out paraphrases before counting extraction transfer. Keep candidate proposal, structure adoption, and outcome-based self-improvement as later separate gates.
