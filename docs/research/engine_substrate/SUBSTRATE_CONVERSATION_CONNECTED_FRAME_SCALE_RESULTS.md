# Conversation connected-frame scale results

## Outcome

The preregistered 24-worker run completed and every arm reported a fixed point. At N=1, all three pairs matched and the expected answer was selected. At N=2/4/8, **0 of 3** full/scoped pairs matched. Full closure passed all expected winner checks at N=2, but failed some deliberations at N=4 and N=8; scoped closure failed at least one deliberation in every connected size. The independently recomputed audit confirms the failure pattern.

| Deliberations | Full candidate pairs | Scoped candidate pairs | Full Term evaluations | Scoped Term evaluations | Full median wall | Scoped median wall | Projection parity |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 | 109 | 323 | 784 | 0.145 ms | 0.158 ms | 3/3 |
| 2 | 78 | 392 | 646 | 2,429 | 0.181 ms | 0.236 ms | 0/3 |
| 4 | 176 | 1,569 | 1,528 | 10,487 | 0.292 ms | 0.559 ms | 0/3 |
| 8 | 372 | 6,241 | 3,292 | 43,801 | 0.418 ms | 1.820 ms | 0/3 |

## Interpretation

The fixture placed the same mutable `DeliberativeCandidate` node in two deliberation ledgers. That node has one graph-global `status`, score, and trace, even though each frame treats it as a candidate. Full closure can select/reject that object while processing one deliberation, changing the candidate set observed by another. Scoped closure's round-robin order produced a different final projection; at N=4 it left a middle deliberation at `no_candidate`, while full closure selected candidates there (though some different deliberations failed their expected-winner checks). This is direct evidence that the current graph representation does not give a shared candidate independent per-deliberation state, and that schedule parity is not guaranteed for this aliasing pattern. It is not a clean estimate of tractability on ordinary conversation workloads or proof that valid disjoint scopes are generally incorrect.

Because semantic parity failed, the work and timing columns are descriptive only and do not support a speedup or scaling claim. The measured increase in scoped work is consistent with the prior disconnected result, but cannot be interpreted independently of the changed semantics.

The next structural question is whether connected frames can be represented through shared read-only evidence while keeping candidate/selection state frame-local, or whether the native rule path needs explicit per-deliberation candidate identity. Then rerun the locked parity design on that representation, and retain a deliberate aliasing control to ensure shared mutable candidates are detected. Do not use this result as evidence for general frame locality until the representation and semantic contract are resolved.

Artifacts: [preregistration](SUBSTRATE_CONVERSATION_CONNECTED_FRAME_SCALE_PREREG_20260925.md), [runner](../../../scripts/substrate_conversation_connected_frame_scale.py), [independent audit](../../../scripts/analyze_substrate_conversation_connected_frame_scale.py), [raw report](../../../evaluation/reports/substrate_conversation_connected_frame_scale_20260925.json), and [lock](../../../evaluation/substrate_capability/conversation_connected_frame_scale_lock_20260925.json).
