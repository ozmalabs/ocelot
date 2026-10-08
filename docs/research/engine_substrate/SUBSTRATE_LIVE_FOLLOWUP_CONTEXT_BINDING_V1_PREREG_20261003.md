# Live follow-up context binding v1 preregistration

Date: 2026-10-03  
Status: preregistered before runner implementation and capture.

## Question

Does the same follow-up prompt use the immediately preceding answer context, as measured by explicit graph identity links and a preregistered lexical content diagnostic?

## Workload

Run three exact conditions through `WorldAdapter.converse` in a fresh full-seed process, with three replicates per condition and no graph reset within a multi-turn condition:

1. **Known-answer context:** `How are you organised?` (question), followed by `Can you explain that in simpler terms?` (question).
2. **Unknown-fact context:** `What part of your organisation is most important?` (question), followed by the identical follow-up, `Can you explain that in simpler terms?` (question).
3. **Fresh-turn control:** `Can you explain that in simpler terms?` (question) as the first and only turn.

The prior prompts reuse prompts already measured in the distinct-turn frame experiment. The known-answer arm should yield an organisation description; the unknown-fact arm previously yielded an explicit lack-of-held-knowledge answer. Capture all replies/routes/goals and final graphs. Do not filter based on outcome.

## Measurements

For every inbound Message, independently identify its frame root by exact text and node identity. Attribute Goals/Events only by the established explicit graph relations (`comprehends`, `for_goal`, `originated_in`, `origin_event`, `represents_message`). Report per-turn reply, route, Goal kind/lifecycle, and exact graph edges connecting nodes owned by different prompt roots. Also compute a lexical context diagnostic: lowercase alphanumeric token overlap between the prior assistant reply and the follow-up assistant reply, excluding this fixed stop list: `a, an, and, are, as, at, be, can, did, do, for, from, how, i, in, is, it, me, my, of, on, or, please, that, the, their, them, they, this, to, us, was, we, what, when, where, which, who, why, with, you, your`. Report both overlap count and shared tokens; do not treat lexical overlap as semantic grounding.

The fresh-turn control has no prior answer, so its overlap is null. No claim of contextual use follows from adjacency or lexical overlap alone. Compare with explicit graph edge evidence and preserve each raw graph for inspection.

## Integrity and claim limits

Require nine unique PIDs, three workers per condition, complete worker records, source stability, exactly the expected inbound Messages per worker, and exact raw graph digest parity across replicates within each condition. If raw parity fails, retain the v1 failure and any post-capture semantic comparison as a separate amendment. All prompt/route/task outcomes remain in the analysis. This controlled authored panel measures only one positive-knowledge prompt, one prior unknown-fact prompt, and one fixed follow-up; it is not a broad discourse or natural-conversation capability estimate.
