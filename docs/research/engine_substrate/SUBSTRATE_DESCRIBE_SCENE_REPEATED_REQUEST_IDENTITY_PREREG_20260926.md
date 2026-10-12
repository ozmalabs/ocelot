# Describe-scene repeated-request identity probe preregistration

## Question

Does the attached-scene `describe_scene` route preserve one-to-one request/parent-Goal identity across repeated instructions against the same scene?

## Source-grounded prediction

`comprehend_describe_directive_*` is guarded by absence of `scene --described_by--> _i`, so it appears to mint at most one parent Goal for a scene. `_act_describe_scene` subsequently selects the last `describe_scene` Goal from the full graph and `_bind_goal_to_inbound` binds it to each inbound request. Prediction: the second request will not produce a new parent Goal and may add a second `comprehends`/`originated_in` binding to the first request's Goal. This is a prediction to be tested, not a presumed result.

## Protocol

- Run three fresh Python processes, each booting the full seed set and attaching the same three-percept scene once.
- In each worker issue two identical `describe what you see` instructions sequentially from the same speaker.
- Capture each turn's inbound Message, origin event, Goal inventory before/after, Goals comprehending the inbound, scene `described_by` parents, parent Goal attributes and links, newly created utterance subgoals, lifecycle events, reply, and elapsed time.
- Fingerprint source inputs before and after every worker and after all workers. Lock the protocol, runner, Python producer/rule authoring sources, native extension/build manifest, and current commit.
- Report route success, identity mapping, and lifecycle emission separately. Do not infer concurrency behavior from this sequential probe.

## Gates

The identity gate passes only if each request maps to exactly one distinct parent Goal, each such Goal comprehends only its own request, and each Goal originates in that request's inbound event. A failed identity gate is a valid finding when the complete graph projections and source fingerprints are available. Lifecycle presence is descriptive; this probe does not require a producer integration. Replies must be nonempty in both turns for route operation to count as demonstrated.

## Limits

This is a repeated-request identity probe for one route, same scene, sequential execution, and one authored scene fixture. It does not establish concurrent safety, workload prevalence, external-effect safety, scale, or general Goal ownership semantics. No source change is part of this probe.
