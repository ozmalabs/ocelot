# Retrospective live action-route work comparison protocol

**Status:** exploratory retrospective comparison of two already-captured, independently source-locked route measurements.

## Inputs and question

Compare lifecycle event-helper work for the two-request `describe_scene` capture v1.5 and the two-turn `self_report` capture v1.7. The question is whether native candidate/Term work differs across these two route/task fixtures under the same full-seed source closure, native artifact, build manifest, Python runtime, and platform.

## Frozen comparison fields

Use only the final raw captures and their independently passing analyses. Verify exact equality of the 1,669-file source-closure maps, native extension hash, native build manifest hash, Python/platform fingerprint, and exact two-request/six-helper-call schedule. Aggregate the already captured production-helper counters by route and event kind; report raw totals and ratios descriptively. Do not merge helper work with whole-turn timing or infer necessary vs. wasted rule work.

## Limits

This is a post hoc comparison, not a randomized or matched-content experiment. The route tasks differ: `describe_scene` uses a concrete scene and a threaded serialized schedule; `self_report` asks for the organisation and runs sequentially. The three process captures per route are runtime replications of the same fixture, not six independent task families. No causal route effect, natural-route frequency, quality comparison, or broad substrate performance estimate follows.
