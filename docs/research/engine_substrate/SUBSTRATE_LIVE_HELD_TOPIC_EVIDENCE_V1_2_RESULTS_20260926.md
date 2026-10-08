# Live held-topic evidence and answer release v1.2 (2026-09-26)

## Result

Three fresh full-source-locked workers passed all **31 gates**. Each worker learned three answers through `learn_from_teacher`, then answered five held-evidence questions exactly across `meta`, `table`, and `honest_capability` comprehension routes. Every positive turn selected one same-event `answer_topic` Goal, had a supported `HeldAnswer → TopicGroundingEvidence` path, and released the exact answer through a matching production receipt. The sixth turn, about unknown `unobtainium`, stayed unresolved and returned the unknown-topic floor without leaking copper's answer.

The unknown no-result grounder ran **twice per turn in all three workers**, both invocations with `allow_web=False`. V1.1's semantic gates all passed except an over-specific exactly-one-call condition; its raw and failed analysis are retained. V1.2 follows the preregistered requirement of at least one counted no-result call and reports the repeated invocation count as evidence.

Source inspection narrows the likely repeat path: `_answer_topic_reply` has one primary call during topic fulfillment and two later recovery/retry call sites in `WorldAdapter.converse`. Each can re-enter the grounding fallback when the first attempt returns no held answer. The current raw capture counts grounder calls but does not record caller stacks, so attributing the two observed calls to a particular retry site remains a hypothesis. A follow-up trace should record call-site identity and whether new graph evidence or a completed fetch arrived between invocations before changing retry behavior.

**V1.3 follow-up resolves this attribution.** Across three fresh workers, both calls are confirmed but arise from different layers: the first is the inline local attempt at `WorldAdapter.converse` → `_answer_topic_reply`; the second is graph-request fulfillment at `converse` → `_dispatch_pending_io` → `fetch_dispatch.scan_and_sync_ground`. The first sees the same-topic `GroundRequest` and `SearchRequest` requested, with Goal outcome unset. The second sees that same `GroundRequest` running and Goal outcome pending. Node and edge counts are unchanged between calls. Thus the second invocation is not a retry site; it is a repeated local check immediately followed by fulfillment of the already-authored GroundRequest. This is a specific duplicated-work candidate. It is not yet safe to remove the inline attempt: that attempt can produce a local answer before dispatch, so a matched local-hit/miss control must verify answer latency, receipt ownership, and search supersession before a change. V1.3's source-locked diagnostic passed all 31 inherited semantic gates; details are linked in the plan entry below.

## Work and structure

Median full-seed boot was 12.07 s. Each `learn_from_teacher` call took 0.28–0.46 ms median and registered zero native candidate enumerations and zero Term evaluations within the measured operation. This is the graph-ingest/apply cost after boot, not the cost of acquiring evidence from an external teacher.

Per query turn, median native work ranged from 53,560 to 67,669 candidate enumerations and 541,770 to 630,849 Term evaluations; median turn time ranged from 122.98 to 284.56 ms. These counters cover all active rules invoked in the `converse` interval and are not attributable solely to the answer-topic rules. They also show the repeated unknown grounding path incurs a full turn closure despite returning no answer.

The final full-seed graph has 25,216 nodes and 12,096 edges. Each supported answer's measured task projection contains 11 nodes, 11 internal edges, and 9–10 boundary incidences. The unknown projection contains 8 nodes and 8 internal edges. Boundary counts are restricted to the protocol's explicit task-edge list; they are not full graph cuts or treewidth measurements. Successful answer Goals retain `status=active` while carrying `outcome=resolved`; the unknown Goal likewise remains active with `outcome=unresolved`. Output release succeeds, but Goal terminalization is not established by this route.

## Limits and lineage

The evidence set and prompts are authored fixtures. The repeated three-worker result confirms these six turns and this held-answer path; it does not estimate language coverage, retrieval quality, natural workload structure, general tractability, or scaling. Query costs include the complete full-seed active rule set and adapter work. Goal `outcome` values are recorded, but status remains `active`; `gap_awareness.json` explicitly consumes `outcome=unresolved` as its knowledge-gap decision datum, while this evidence does not establish a general Goal terminal-status contract. Treat it as an unresolved lifecycle specification question, not a demonstrated bug.

The initial v1 worker failed on an unsupported `out_edges` call before preserving a raw payload. V1.1 amended the edge projection, then its worker smoke check found that `Substrate.nodes()` yields NodeIDs; this was fixed before the locked run. The v1.1 locked run persisted its raw workers and exposed the exactly-one grounder assertion mismatch. V1.2 changes only that analyzer condition and keeps the raw v1.1 failure preserved.

## Artifacts

- Original preregistration: [v1 protocol](SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_PREREG_20260926.md)
- Harness amendment: [v1.1](SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_1_AMENDMENT_20260926.md)
- Analysis amendment: [v1.2](SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_2_AMENDMENT_20260926.md)
- Runner: [`substrate_live_held_topic_evidence_v1_2.py`](../../../scripts/substrate_live_held_topic_evidence_v1_2.py)
- Source lock: [full source closure](../../../evaluation/substrate_capability/live_held_topic_evidence_v1_2_lock_20260926.json)
- Raw workers: [three source-stable captures](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_2_workers_raw_20260926.json)
- Gates and full measurements: [analysis capture](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_2_20260926.json)
- Preserved v1.1 assertion failure: [raw workers](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_1_workers_raw_20260926.json), [failed gates](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_1_20260926.json)
