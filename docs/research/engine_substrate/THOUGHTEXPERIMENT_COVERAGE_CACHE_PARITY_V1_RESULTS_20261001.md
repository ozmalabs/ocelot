# Thoughtexperiment coverage-index cache parity v1 results

**Result:** all preregistered parity gates pass. Reusing the frozen covered-keyword index preserves complete selector outputs for the three candidate postulates and leaves the semantic graph unchanged.

Three fresh full-seed workers each compared default coverage recomputation with the precomputed index for `diffusion_model_vision`, `variational_autoencoder`, and `vision_language_model`, using the same exact default harvested shape library. All nine candidate/worker output pairs are exactly equal. All three graph digests are unchanged before/after, worker PIDs are distinct, boot/shape identities agree, and the source/seed fingerprint remains stable. Each worker loaded 731 seeds with 11 recorded failures.

Median timings on this host (seconds per postulate) were:

| Postulate | Default recompute | Cached index | Relative change |
|---|---:|---:|---:|
| `diffusion_model_vision` | 2.007 | 1.904 | 5.1% faster |
| `variational_autoencoder` | 1.970 | 1.889 | 4.1% faster |
| `vision_language_model` | 1.992 | 1.859 | 6.7% faster |

These timings include only the compared `synthesize_gaps` calls with shape resolution held constant and are descriptive for three postulates on one host. They do not establish scaling or end-to-end improvement. The result validates the optional index reuse under the preregistered fixed-graph invariant; callers remain responsible for not reusing the index after graph or implementation-surface changes.

See the [preregistration](THOUGHTEXPERIMENT_COVERAGE_CACHE_PARITY_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_coverage_cache_parity_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_coverage_cache_parity_v1_raw_20261001.json).
