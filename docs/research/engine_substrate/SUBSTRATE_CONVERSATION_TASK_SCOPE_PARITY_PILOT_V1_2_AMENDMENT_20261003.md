# Conversation task-scope parity pilot v1.2 amendment

Date: 2026-10-03

V1.2 extends the same paired closure protocol to the three-frame-count levels actually present in the panel: concurrent goals at 2, 4, and 8 frames, plus the common-ground stress case at 4 frames. The capture's free-text `claim_boundary` string mistakenly lists a three-frame case; no three-frame case was run. The locked `configuration.cases` and each result's measured `frame_count` show the actual four-case design. This wording error does not change data or gates and is corrected in the results summary.

V1.2 creates one task-specific `Microtheory` node per observed frame using the native node insertion surface, then adds the event/goal ownership edges as symmetric unchecked measurement annotations. It records the scope IDs and each per-scope quiescence report. The source lock does not include `term.rs` directly, although it locks the reused v1.3 panel runner, native binary/build manifest, and the core rewrite/substrate/graph/access-trace/FFI sources. Treat v1.2 as an exploratory extension; add the term evaluator source and independent case-matrix checks before calling a follow-up confirmatory.

Across three fresh workers, all 12 paired final graphs and all 198 checkpoint graphs match. Goal statuses match, and all 1,005 per-scope quiescence reports show zero progress and no pending deferred effects; every report still marks frame notifications incomplete. This extends the parity signal across frame counts and a common-ground stress case, while leaving factorization, dynamic repartition safety, and speedup open.

Artifacts: [v1.2 runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_2.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_2.py), [source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_2_lock_20261003.json), [capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_2_20261003.json), and [analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_2_analysis_20261003.json).
