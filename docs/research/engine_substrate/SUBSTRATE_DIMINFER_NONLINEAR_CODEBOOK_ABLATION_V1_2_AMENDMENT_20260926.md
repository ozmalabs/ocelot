# Full-seed nonlinear DimInfer codebook ablation v1.2 amendment

The v1 harness failure and the v1.1 single-cell harness smoke check are retained as development records and are not part of the confirmatory capture. The smoke check exposed a second interface distinction: codebook `ShapeSignature.signature` is serialized JSON text, while an `Observation.signature` and its initial `residual` must be native relation-list values. V1.1 had passed JSON text for all three fields, so closure ran but did not match the intended fixture.

V1.2 corrects the Observation fields to the list-valued representation used by the full-seed GenMint capture. It retains the v1.1 correction to invoke `native.run_rules()` through the production native facade. The 72-cell design, transform operators, paired codebook ablation, GenInfer-off setting, metrics, and acceptance gates remain unchanged. The v1 and v1.1 harness records are not efficacy results; only the v1.2 locked capture can support conclusions.
