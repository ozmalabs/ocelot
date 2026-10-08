# Held-topic request-form panel v1 preregistration

Date: 2026-09-28  
Status: preregistered before execution

## Question

The paired held-topic replay answered six of seven query cases. Its sole miss, “Can you tell me about copper?”, was routed as `honest_capability`, despite a held fact for copper. This panel tests whether that outcome depends on wording or reflects a wider failure to use held factual evidence for ordinary requests. It is diagnostic and does not alter source or oracle criteria after observation.

## Fixed held content and prompts

Each prompt is issued in a fresh worker after the same three teaching operations have loaded these facts:

| ID | Prompt | Topic | Role |
|---|---|---|---|
| P1 | Tell me about copper. | copper | direct request |
| P2 | Please tell me about copper. | copper | polite direct request |
| P3 | What can you tell me about copper? | copper | indirect request / ability form |
| P4 | Can you tell me about copper? | copper | replicated miss |
| P5 | What do you know about copper? | copper | established held-answer control |
| P6 | What is copper? | copper | established table-path control |
| N1 | What do you know about unobtainium? | unobtainium | unknown-topic no-leak control |

Expected held answer: `Copper conducts electricity and heat.` The positive quality outcome requires exactly this reply, a supported HeldAnswer for copper, matching TopicGroundingEvidence, one `answer_topic` Goal for copper, and a released production receipt linked to the answer/goal. A truthful clarification can be recorded as an honest response, but it does not count as retrieval success. N1 must remain unresolved and must not reveal the copper answer.

## Design and measurements

Run two fresh processes, each booting the full current runtime and independently teaching the same facts. Prompt order is fixed as listed in both workers so state accumulation is comparable; every prompt is asked once. Record the complete comprehension dispatch, message route, reply, Goals, HeldAnswers, grounding evidence, receipts, grounder calls, and total graph counts using the established v1.6 capture boundary. Before and after the run, lock the Python/seed source closure, native extension/build, benchmark script, preregistration, Git commit, Python/platform, current working directory, selected environment variables, native package path, and content digest of the complete `data/` tree.

The primary report is per-prompt exact supported retrieval and worker agreement. Route labels are diagnostic, not quality oracles. P1–P4 are not collapsed into one pooled natural-language estimate. This small authored set cannot estimate population performance, general language understanding, or frame-locality prevalence.

## Decision rules

* If only P4 fails while P1–P3 succeed, investigate the specific `Can you ...?` capability/request interpretation before considering any code change.
* If P3 and P4 fail together, inspect the ability-form arbitration boundary; do not infer that all request forms fail.
* If P1/P2 fail too, broaden the diagnosis to held-fact retrieval/release rather than request parsing.
* If N1 leaks the copper answer or resolves without evidence, treat the run as an honesty/control failure regardless of positive performance.
* Any source, runtime-data, worker, or graph-signature instability invalidates confirmatory interpretation and requires a corrected rerun.

## Artifacts and execution

Runner: `scripts/substrate_held_topic_request_form_panel_v1.py`  
Run lock: `evaluation/substrate_capability/held_topic_request_form_panel_v1_lock_20260928.json`  
Raw: `evaluation/reports/held_topic_request_form_panel_v1_20260928.json`

Generate the lock with `python3 scripts/substrate_held_topic_request_form_panel_v1.py --lock`; execute only after review with `OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_held_topic_request_form_panel_v1.py`. The script verifies locked input identity before and after workers. Raw worker data is immutable after capture; analysis is reported separately.
