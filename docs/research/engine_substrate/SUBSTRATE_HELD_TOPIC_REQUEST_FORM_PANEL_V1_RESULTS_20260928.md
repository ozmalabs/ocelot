# Held-topic request-form panel v1 results

Date: 2026-09-28  
Protocol: [preregistration](SUBSTRATE_HELD_TOPIC_REQUEST_FORM_PANEL_V1_PREREG_20260928.md)  
Amendment: [pre-task lock and capture corrections](SUBSTRATE_HELD_TOPIC_REQUEST_FORM_PANEL_V1_AMENDMENT_20260928.md)

## Result

The two fresh workers completed all seven prompts with matching semantic signatures. Their source/runtime locks were stable before and after each worker, and the final lock matches. The independent analyzer passes six gates: two distinct processes, stable worker locks, matching final lock, repeated semantic signatures, complete prompt set, and both unknown-topic controls.

| Prompt | Route | Exact supported answer | Workers |
|---|---|---:|---:|
| Tell me about copper. | `instruction` | 0/2 | Replies “I am Jabberwock.”; routes to a self-report Goal about `me` |
| Please tell me about copper. | `instruction` | 0/2 | Same self-report result |
| What can you tell me about copper? | `meta` | 2/2 | Returns the held copper fact |
| Can you tell me about copper? | `honest_capability` | 0/2 | Asks what information would ground an answer; creates an unresolved copper Goal |
| What do you know about copper? | `meta` | 2/2 | Returns the held copper fact |
| What is copper? | `table` | 2/2 | Returns the held copper fact |
| What do you know about unobtainium? | `meta` | 2/2 control | Stays unresolved and does not leak the copper answer |

The primary outcome requires a turn-linked released receipt for the exact held answer, a supported copper answer/evidence, and a copper `answer_topic` Goal. The analyzer checks the receipt against the current inbound message and its released Goal/answer IDs; a pre-existing HeldAnswer elsewhere in the graph cannot make a turn pass. Controls passed 6/6 worker outcomes. The four newly authored ordinary request forms passed 2/8, with success limited to “What can you tell me about copper?”

## Interpretation

This is not one `can`-wording failure. The two imperative forms are parsed as instructions with `Tell` as the action and `me` as its target, then incorrectly answer with a self-identity report. The “What can you tell me…” form returns the correct fact through a `meta` dispatch. The exact “Can you tell me…” form reaches the explicit `honest_capability` branch, asks for grounding information, and leaves its copper Goal unresolved even though supported copper evidence is already held. The known “What do you know…” form also labels dispatch `self_identity` but returns the right topic answer, while “What is…” uses the table route. This points to a language arbitration/release coordination gap spanning imperative self-report parsing and polar capability handling, rather than a failure of fact storage or the table answer path.

Do not change the oracle to count clarification as retrieval. A user may genuinely ask about ability, but the fixed form also has a conventional request reading; in either interpretation, the graph has a held copper answer and the runtime's own answer-topic Goal reports unresolved. Next use blinded human judgments to separate literal ability questions from indirect requests, then test a preregistered set of minimally paired subjects, modal auxiliaries, and imperative forms. Keep the current reply-quality and graph-receipt criteria. Any implementation change should be evaluated against these frozen cases plus held-out paraphrases and explicit negative controls.

## Scope and cost

The panel contains one taught fact, seven hand-authored forms, fixed order, and two processes. It does not estimate general language capability, natural request-form prevalence, general retrieval accuracy, or frame-locality frequency. Full-runtime boot took 12.24 s and 12.39 s in the two workers; this includes the current local seed/runtime state and is not a general boot-time estimate.

## Artifacts

- [Preregistered runner](../../../scripts/substrate_held_topic_request_form_panel_v1.py)
- [Independent turn-level analyzer](../../../scripts/analyze_substrate_held_topic_request_form_panel_v1.py)
- [Raw two-worker capture](../../../evaluation/reports/held_topic_request_form_panel_v1_20260928.json)
- [Analysis and gates](../../../evaluation/reports/held_topic_request_form_panel_v1_analysis_20260928.json)
- [Source and runtime lock](../../../evaluation/substrate_capability/held_topic_request_form_panel_v1_lock_20260928.json)
