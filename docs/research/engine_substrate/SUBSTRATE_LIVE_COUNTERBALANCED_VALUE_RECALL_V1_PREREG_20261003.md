# Live counterbalanced value recall v1 preregistration

Date: 2026-10-03  
Status: preregistered before runner implementation and capture.

## Question

Can the live substrate retain a user-stated value across turns and answer an identical follow-up with the value that changes across counterbalanced contexts?

## Conditions and exact task oracle

Run three fresh-process conditions, three workers each, with no graph reset within each multi-turn worker:

* `value_14`: statement `My secret code is 14.` followed by question `What is my secret code?`; follow-up succeeds only if the assistant reply contains the standalone numeral `14` and does not contain standalone `29`.
* `value_29`: statement `My secret code is 29.` followed by the identical follow-up; success only if the reply contains standalone `29` and not `14`.
* `fresh_control`: ask only `What is my secret code?`; success only if neither `14` nor `29` appears as a standalone numeral.

The oracle is exact value selection/abstention, not stylistic similarity. Preserve all outcomes and do not drop failures. Capture replies, routes, new Message and Goal IDs/statuses after each turn, final full graph, raw digest, process metrics, and source provenance.

## Graph analysis

Reconstruct frame roots from exact inbound Message text. Attribute Goals only through explicit `comprehends`; Events only through `for_goal`, Goal `originated_in`, Goal `origin_event`, or `represents_message`. Report whether the recall Goal links to the question Message, whether any owned event/edge links it to the statement Message, plus direct and boundary-mediated cross-frame interaction. This graph evidence is separate from the behavioral oracle: correct output does not by itself prove which memory path caused it, and a cross-turn edge does not count as recall.

## Integrity and limitations

Require nine unique worker PIDs, three per condition, complete output records, source stable before/after each worker and at capture end, and exactly the expected inbound Messages. Exact raw graph digests are a preregistered replicate gate; if generated timing attrs cause failure, retain the raw failure and add any semantic replicate analysis only as a separately documented amendment. This is a small controlled test of one explicit value pair on repository source, not a broad memory, arithmetic, or general reasoning benchmark.
