# Live follow-up context binding v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_LIVE_FOLLOWUP_CONTEXT_BINDING_V1_PREREG_20261003.md)  
Digest amendment: [v1.1](SUBSTRATE_LIVE_FOLLOWUP_CONTEXT_BINDING_V1_1_AMENDMENT_20261003.md)

## Integrity and findings

Nine fresh source-locked workers completed: three each for a prior known answer, a prior unknown-fact answer, and the same follow-up as a fresh first turn. All worker records, source checks, prompt identity checks, and the amended v1.1 semantic replicate gates pass. The preregistered raw graph digest gate fails for both two-turn conditions; it passes for the fresh control. The only replicate differences in the two-turn conditions are generated `SystemModel.attrs.runtime_s` and `ts`; the v1.1 analyzer excludes only those two fields and retains all raw digests.

The prior known-answer prompt consistently returns a long organisation description. The prior unknown-fact prompt consistently says the system does not hold the requested “most important” fact and asks the user to supply it. In both conditions, the identical follow-up `Can you explain that in simpler terms?` produces exactly the same reply: `What information should I use to answer that?` The follow-up also produces that exact reply as a fresh first turn. The preregistered lexical overlap between each prior assistant reply and its follow-up reply is zero in both context conditions. This is direct evidence that the reply does not vary with these two tested answer contexts; it does not prove the model has no other form of context use.

| Condition | Median nodes / edges | Explicitly owned Goals | Direct cross-frame edges | Exact frame interaction width | Median RSS |
|---|---:|---:|---:|---:|---:|
| Known-answer context | 25,090 / 11,582 | 1 | 2 | 1 | 1,720.7 MiB |
| Unknown-fact context | 25,115 / 11,647 | 2 | 1 | 1 | 1,721.2 MiB |
| Fresh-turn control | 25,054 / 11,501 | 1 | 0 | 0 | 1,721.8 MiB |

The known-answer graph contains explicit cross-frame `responds_to` and `follows_event` edges despite its earlier generic `communicate` Goal lacking a `comprehends` link to its Message. The unknown-fact graph has a cross-frame `follows_event` link and explicitly owned `answer_topic` Goals for both prompts. Thus graph-level sequence linkage exists in both contexts, but the identical generic follow-up response and zero lexical overlap provide no evidence that the follow-up answer used the prior answer's content. The fresh control shows the same response without any prior turn. This distinction matters: event linkage and Goal ownership are not evidence of grounded context use.

Only two prior-answer types, one follow-up phrasing, and three replicates per condition were measured. RSS includes full-seed boot and is not a per-frame estimate. This is a bounded live-route capability result, not a broad discourse benchmark.

## Next gate

Add a task with an externally checkable answer that must be selected from the immediately preceding turn (for example, choose which of two previously stated values was larger), with counterbalanced values, a same-question fresh-turn control, and a semantically similar but incorrect prior-context control. Require the correct answer to change when the prior values are swapped, alongside explicit graph reference evidence. This tests content use rather than mere event continuity.

Artifacts: [capture](../../../evaluation/reports/live_followup_context_binding_v1_20261003.jsonl.gz), [v1 analysis with raw digest failures](../../../evaluation/reports/live_followup_context_binding_v1_analysis_20261003.json), [v1.1 semantic analysis](../../../evaluation/reports/live_followup_context_binding_v1_1_analysis_20261003.json), [runner](../../../evaluation/substrate_capability/live_followup_context_binding_v1.py), [amended analyzer](../../../evaluation/substrate_capability/analyze_live_followup_context_binding_v1_1.py), and [source lock](../../../evaluation/substrate_capability/live_followup_context_binding_v1_lock_20261003.json).
