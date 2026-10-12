# Live conversation task-graph harvest v2 results

The current-source, provenance-guarded harvest completed ten fresh workers over
five authored task conditions. The source lock remained stable; all worker
records were captured; both graph digests match within every condition; and
the independent analyzer passed all gates. Six of ten task contracts passed.
This remains a selected authored panel, not a natural-task sample.

Explicit ownership is sparse. Only scene description and self-report action
have a prompt-linked Goal, and both links identify `report_self`; scene
description fails its task contract in both workers, so that link is a concrete
misrouting signal rather than evidence of correct task ownership. The other
three conditions have no explicit prompt-linked Goal. Each graph has one
request root and therefore one ownership frame under the conservative rule;
there are no direct cross-frame edges or owner conflicts. This zero-interaction
result is a design consequence of one request per worker and does not test
multi-frame factorization. Frame-boundary incidence counts range from 17 to 40
against frames of one or five nodes, while the graphs contain roughly 25,000
nodes and 11,000 edges.

The current typed-path audit reinforces why reachability cannot substitute for
ownership: in scene description, five Goals are reachable without high-degree
hubs, including multiple unrelated response Goals; in the other four tasks no
Goal is reachable without hubs. A blinded review packet now includes one graph
per task and holds the second replicate out, but has no independent human
labels yet. Treat it as an adjudication instrument, not scored mapping accuracy.

## Reproduction and review artifacts

- [Preregistration](SUBSTRATE_LIVE_CONVERSATION_TASK_GRAPH_HARVEST_V2_PREREG_20261004.md)
- [Source lock](../../../evaluation/substrate_capability/live_conversation_task_graph_harvest_v2_lock_20261004.json)
- [Capture runner](../../../evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py)
- [Raw graph archive](../../../evaluation/reports/live_conversation_task_graph_harvest_v2_20261004.jsonl.gz)
- [Independent ownership analysis](../../../evaluation/substrate_capability/analyze_live_conversation_task_graph_harvest_v2.py)
- [Analysis record](../../../evaluation/reports/live_conversation_task_graph_harvest_v2_analysis_20261004.json)
- [Typed-path analysis](../../../evaluation/substrate_capability/analyze_live_conversation_task_anchor_paths_v2.py)
- [Typed-path record](../../../evaluation/reports/live_conversation_task_anchor_paths_v2_20261004.json)
- [Blinded review-packet builder](../../../evaluation/substrate_capability/build_live_task_anchor_review_packet_v2.py)
- [Blinded review packet](../../../evaluation/reports/live_conversation_task_anchor_review_packet_v2_20261004.json)

Reproduce the capture with `python3 evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py`, then run the two analyzers. Build the review packet with `python3 evaluation/substrate_capability/build_live_task_anchor_review_packet_v2.py`.
