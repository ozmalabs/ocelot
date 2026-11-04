# P18 observed-model and experiment results

**Protocol:** `linear-p18-v1`  
**Held-out allocation:** run once after standalone preregistration commit `f3e92aa8`.  
**Analyzer:** frozen v1 analyzer; raw scorecard and analysis JSON are preserved outside git.

## Registered outcome

The held-out allocation completed all 1,600 rows across 400 paired worlds (200 object-mechanism and 200 temporal worlds, each across four arms). Integrity and conformance **PASS**. All three structural control sets passed 100/100: ambiguous models, missing windows, and irregular windows. All five tampering probes were detected. There were no allocation, source, result, receipt, input audit or resource limit failures.

The learned-model arm succeeded on 200/200 worlds in both families. The held-vocabulary-search comparator also succeeded on 200/200 in both families, while passive and fixed-probe arms each succeeded on 0/200. Because the strongest comparator tied the native learned-model arm, the registered efficacy threshold is **NOT_ESTABLISHED**. The learned arm did not use fewer interventions than the strongest comparator; the temporal continuation sample is an observation, not an intervention.

| Family | Learned model | Held-vocabulary search | Passive | Fixed probe | Gain vs strongest comparator |
|---|---:|---:|---:|---:|---:|
| `object_mechanism` | 200/200 | 200/200 | 0/200 | 0/200 | 0 pp |
| `temporal_latent` | 200/200 | 200/200 | 0/200 | 0/200 | 0 pp |

The structural mechanism result is positive and bounded: observed action receipts induced categorical transition hypotheses with support receipts; disagreement between source-bound model predictions caused a native graph rule to propose a probe; the independent world executed the action and verified its result; and that result supported one hypothesis while disputing another. For temporal worlds, native residual rules proposed latent candidates from three regular observed windows and validated them against a fresh continuation. Across the learned arms, 400 refinements were linked to actual simulator results.

These results establish neither a benefit over a competent fixed-vocabulary search nor unrestricted causal discovery. Claims remain limited to the declared finite categorical object and partial temporal worlds. There is no physical, robotic, general-science or calibrated-probability evidence. No capability level closes.

Exact runtime provenance: loaded extension SHA-256 `b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1`; build receipt SHA-256 `6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1`; build source fingerprint `73c04733538d88f983beb5139e2dfae4633e686738f9161f56a8b2678e8e2c54`; source bundle SHA-256 `27c063f1ee1ddc1d704df204697d1439bc09e829d30d2e06b7a05c73212b931d`.

The v1 implementation is commit `7bb77beb`; the standalone freeze is commit `f3e92aa8`. Development used 8 worlds per family/arm (64 rows) and 10 controls per kind; it passed integrity/conformance and the five tamper probes, with efficacy NOT_ESTABLISHED. The focused P18 mechanism/profile bundle passed 86 tests. Raw held-out files remain outside git: scorecard SHA-256 `d2637c42bcb83f3556e25c9e458457c89262eee3bac19cbe4c68683ba3fd7027`, analyzer SHA-256 `f663ec1553893f4c1f681301259ad0b8b7220c8dfb3ab44047f4a4c130c89627`.

P19 entry is supported for generic process invention and reusable strategy search because the P18 native model views, result-linked refinement path, P16 execution boundary and P17 behavioral consumers are present. P18's registered comparative efficacy remains NOT_ESTABLISHED.
