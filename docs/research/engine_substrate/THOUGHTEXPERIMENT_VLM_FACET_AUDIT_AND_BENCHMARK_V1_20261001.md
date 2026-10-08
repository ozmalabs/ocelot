# Thoughtexperiment VLM facet audit and benchmark plan v1

## Purpose and scope

The held `vision_language_model` Concept names CLIP, ALIGN, Flamingo, joint vision-language representation, and zero-shot classification. The all-domain selector correctly recognizes a narrower held mechanism—reliability-weighted fusion of feature channels—but that does not establish the end-to-end VLM. This document separates source-level facets from measured task capability and specifies the benchmark needed before making a VLM claim.

## Source-linked facet inventory

| Facet | Current evidence | Assessment |
|---|---|---|
| Image ingestion | [`VisionWorld.ingest`](../../../domains/vision_world.py#L61) maps flat image values to `Image`, `Sense`, `Field`, and `Patch` graph nodes. [`GraphEye`](../../../domains/photon_eye.py#L339) supplies a graph-resident photon-event visual apparatus. | Implemented input/representation paths exist. This does not show a shared text-image representation. |
| Visual features and shape processing | `VisionWorld` reads retained kernels and `ShapeSignature` nodes; `photon_eye.py` has the live retinal/transduction implementation; `vision_floor` rules select visual kernels. The substrate-backed Omniglot `run_grapheme` panel scores 77/80 (96.25%) on one alphabet with held-out writers. | Visual recognition has a measured narrow result. This is seen-class/new-writer handwriting recognition; no VLM claim follows. See [results](THOUGHTEXPERIMENT_OMNIGLOT_GRAPH_RECOGNITION_V1_RESULTS_20261001.md). |
| Text and language processing | The [`language` domain](../../../domains/language.py) and language concepts provide a separate text-processing path. | Text processing exists independently. A shared embedding or score against image features was not found in the audited implementation surface. |
| Cross-modal association | [`seeds/cross_modal.json`](../../../seeds/cross_modal.json) installs grapheme-to-phoneme association by co-presentation (`bind_grapheme_phoneme`) and read/write recall rules. The nominal `run_cross_modal` in `domains/reading_runners.py` delegates to `run_grapheme`, so it does not measure binding. A separate source-locked task uses the repository FSDD release and reaches 80% held-out read-aloud and 70% dictation; a one-digit shifted-binding control falls to 0% in both directions. | The narrow grapheme↔spoken-digit association is causally relevant in this task. It is not image-caption alignment or joint semantic embedding. See [binding results](THOUGHTEXPERIMENT_GRAPHEME_AUDIO_BINDING_V1_RESULTS_20261001.md) and [control results](THOUGHTEXPERIMENT_GRAPHEME_AUDIO_PERMUTED_BINDING_V1_RESULTS_20261001.md). |
| Reliability-weighted fusion | [`reliability_weighted_score_term`](../../../domains/combinatorial_recognizer.py#L100) and `predict_reliability_weighted_term` combine two feature-channel likelihoods using reliability exponents. | Implemented channel-fusion mechanism. It does not itself add a visual channel or learn image-text alignment. |
| Joint vision-language representation | The held Concept in [`seeds/vision_computer.json`](../../../seeds/vision_computer.json#L48) describes CLIP/ALIGN/Flamingo and claims a substrate analogue, but a source search across `domains/*.py` found no image-text contrastive objective, shared embedding scorer, or paired image-caption alignment pipeline. | Held concept only; executable joint representation not established. |
| Zero-shot image classification/retrieval | Named in the same held Concept; no image-text prompt scoring or held-out label-description comparison path was identified in the audited Python domains. | Not established. |

These are source inventory judgments, not runtime outcome measurements. The distinction is material: image input, text processing, and generic channel fusion can all exist without the composition that defines a VLM.

## Benchmark protocol to execute after an image-text scorer exists

### Task

Evaluate paired image-caption understanding on a frozen dataset with object/category-disjoint train, development, and test partitions. The primary task is candidate-caption retrieval for each image; the secondary task is zero-shot classification by scoring class descriptions without training examples from test classes. Keep test images, captions, class names, and paraphrases out of all seed construction and proposal prompts.

### Arms and controls

1. Full image-text system.
2. Vision-only and text-only controls using the same candidate set.
3. Random-score and shuffled image-caption controls.
4. Modality ablations: remove image, remove text, and corrupt one modality at a time.
5. Direct execution and Thoughtexperiment branch/proposal execution, with no adoption until held-out evaluation completes.

### Measures

Primary: image-to-caption Recall@1 and caption-to-image Recall@1 on test pairs. Secondary: zero-shot macro accuracy, calibration/error by category, intact-to-corrupted performance drop, proposal/derivation status, training/query exposure, CPU time, peak memory, and complete branch isolation/adoption receipts. Report all seeds and per-category outcomes; do not pool away failures.

### Claim gates

- **Input gate:** image and text enter through documented substrate interfaces; modality IDs and test-split provenance are captured.
- **Alignment gate:** paired image-text scoring is performed by the substrate-held mechanism, not by a host or LLM fallback.
- **Generalization gate:** test categories and paraphrases are held out and split hashes are fixed before fitting or proposal.
- **Utility gate:** full system beats both unimodal controls and shuffled-pair controls on preregistered test measures; uncertainty intervals and per-category failures are reported.
- **Thoughtexperiment gate:** Direct and branch arms agree on the measured proposal and outcomes; source and candidate fingerprints are stable; no candidate state leaks into the primary before authorization.

This is a future protocol, not an executed evaluation. Before implementation, preregister the exact dataset and hashes, prompt/caption construction rules, scoring interface, minimum useful effect, resource budget, and allowed LLM boundary. A manually written image-text scorer can validate the benchmark plumbing but cannot count as substrate learning.

## Immediate next action

The next capability-building experiment should first select or construct a minimal image-text scoring operator under explicit custody. Measure it against the unimodal and shuffled controls above, then allow the Thoughtexperiment harness to propose a change and compare branch outcomes. Keep the report's current status at “VLM facets partially present; joint representation and zero-shot behavior unestablished” until those runtime gates pass.
