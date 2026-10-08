# Analysis amendment: held-topic runtime interface trace v1

The first analysis script assumed a `whole_graph_semantic_sha256` field that the reused held-topic worker does not emit. It stopped with `KeyError` after reading the completed capture and did not modify it. The immutable compressed raw capture and experiment lock are retained. A separate v1.1 analyzer compares repeated worker outcomes and frame/access signatures directly, verifies source inputs against the original lock, and audits task-quality gates separately from capture integrity.

The current-source replay also exposes a task-quality failure on the frozen “Can you tell me about copper?” turn: all three workers ask for clarification instead of releasing the held answer. Preserve that failed capability gate alongside the valid structural/access observations. Do not compare this run's task quality to the historical v1.6 success without checking the source-lock difference.
