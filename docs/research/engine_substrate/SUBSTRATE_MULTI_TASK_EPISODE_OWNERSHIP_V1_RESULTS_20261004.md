# Multi-task episode ownership v1 results

Two fresh workers replayed the same five authored prompts sequentially in one
full-seed graph each. Both produced 25,457 nodes and 12,325 edges. Whole-graph
hashes differed only in eight `ts`/`runtime_s` diagnostic fields; after removing
those measured fields, normalized graph digests, task outputs, ownership sets,
and cross-owner edges reproduce exactly. The independent analyzer recomputes
the projections and cross-edge list from both retained graphs and passes.

The conservative per-prompt owner projection contains 5, 1, 1, 1, and 5 nodes.
Only scene description and self-report action receive explicit Goals, both of
kind `report_self`; this is the wrong Goal kind for scene description. That
prompt receives “I am Jabberwock.” The concern-authoring prompt is classified
as an instruction but receives a clarification question about “two.” The
unknown-word and self-knowledge prompts have no `comprehends`-linked Goal.
These outcomes show task-routing interference in the accumulated episode;
the pass gates establish reproducibility, not task correctness. In particular,
this runner records graph interpretation dispatch fields and replies, not the
task-action contract used by the isolated harvest.

No task-owner sets overlap, but three typed graph edges cross between adjacent
prompt owners. All three are `responds_to`; they encode dialog adjacency. Thus
prompt ownership is not edge-disjoint even in this small episode. These links
do not establish causal or inference-factor dependency, and the conservative
projection omits outbound response messages. This is one fixed task order and
two workers, not natural-task prevalence, a learned partition, or a tractability
result. The next run should capture explicit task-action outcomes, vary task
order, and include independent owner annotations before measuring partition
quality or execution cost.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_MULTI_TASK_EPISODE_OWNERSHIP_V1_PREREG_20261004.md)
- [Digest amendment](SUBSTRATE_MULTI_TASK_EPISODE_OWNERSHIP_V1_AMENDMENT_20261004.md)
- [Capture runner](../../../evaluation/substrate_capability/multi_task_episode_ownership_v1.py)
- [Source lock](../../../evaluation/substrate_capability/multi_task_episode_ownership_v1_lock_20261004.json)
- [Capture](../../../evaluation/reports/multi_task_episode_ownership_v1_20261004.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_multi_task_episode_ownership_v1.py)
- [Independent analysis](../../../evaluation/reports/multi_task_episode_ownership_v1_analysis_20261004.json)
- [Initial raw-digest probe](../../../evaluation/reports/multi_task_episode_ownership_v1_initial_raw_digest_probe_20261004.json)

Reproduce from the repository root with `python3 evaluation/substrate_capability/multi_task_episode_ownership_v1.py --lock` when making a new versioned run, then run the capture and `python3 evaluation/substrate_capability/analyze_multi_task_episode_ownership_v1.py`.
