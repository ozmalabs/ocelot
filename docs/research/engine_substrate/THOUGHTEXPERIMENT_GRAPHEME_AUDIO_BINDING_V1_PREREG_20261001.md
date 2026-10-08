# Thoughtexperiment grapheme–audio binding v1 preregistration

## Question

Can the substrate's graph-resident co-presentation rules recall a bound spoken digit from a held-out writer's grapheme and a bound grapheme from a held-out speaker's spoken digit?

## Fixed task

Use the existing `scripts/jabberwock_cross_modal.py` task with the repository-local FSDD release at `data/fsdd-current/free-spoken-digit-dataset-26eb9aaf76e81b692f806f9140c2d2777410d7a1/recordings` and Omniglot evaluation strokes. The runner uses 10 grapheme/digit identities; grapheme gallery exemplars and audio gallery exemplars are co-presented to fire `bind_grapheme_phoneme`; held-out writer samples exercise grapheme→audio recall, and held-out speakers exercise audio→grapheme recall. Set `n_test=40`, giving 40 read-aloud and 40 dictation queries per worker.

Run three fresh workers. Fingerprint the runner, seed manifest, visual/audio feature extraction and recognition sources, native extension, all selected Omniglot files, and all 3,000 selected FSDD WAV files before and after. Capture exact integer successes inferred from the runner's one-decimal percentages and known 40-query denominators, worker PIDs, held-out identities, binding count, and full stdout.

## Measures and limits

Primary measures are read-aloud and dictation accuracy; chance for 10-way labels is 10%. Require 10/10 graph binding edges, exactly 40 queries per direction, repeatable outcomes, fresh workers, and stable source/data hashes. Report modality recognition as a limitation: this runner's end-to-end scores include visual/audio recognition errors as well as binding. It has no shuffled-pair or permuted-binding control, so it establishes task execution and observed transfer, not the causal contribution or incremental utility of the binding rules. It is a narrow grapheme↔spoken-digit result, not image-text alignment or a VLM result. See [results](THOUGHTEXPERIMENT_GRAPHEME_AUDIO_BINDING_V1_RESULTS_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_grapheme_audio_binding_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_grapheme_audio_binding_v1_raw_20261001.json).
