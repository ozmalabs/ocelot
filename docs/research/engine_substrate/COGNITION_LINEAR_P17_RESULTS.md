# P17 matched later-behavior results

**Protocol:** `linear-p17-v2`  
**Held-out allocation:** run once after the standalone v2 preregistration commit `815da7a8`.  
**Analysis:** frozen v2 analyzer; raw scorecard and analysis JSON are preserved outside git.

## Registered outcome

The held-out allocation completed all 1,600 paired rows (200 worlds per family × two families × four arms) and all 400 structural controls (100 each for orthogonal and reversal controls in each family). Integrity, conformance, and registered efficacy all **PASS**. There were no analyzer failures and all five tampering probes were detected.

For each family, acquired behavior succeeded on 200/200 later tasks. Frozen, shuffled, and no-experience each succeeded on 0/200, so acquired gained 100 percentage points over each registered comparator, exceeding the 20-point threshold. All four control strata passed 100/100. No wrong-owner/stale-source acceptance, post-contestation action, target-field leak, missing pair, unverified receipt, or provenance mismatch was reported.

| Family | Acquired | Frozen | Shuffled | No experience | Gain vs each control |
|---|---:|---:|---:|---:|---:|
| `tool_contact` | 200/200 | 0/200 | 0/200 | 0/200 | +100 pp |
| `social_request_repair` | 200/200 | 0/200 | 0/200 | 0/200 | +100 pp |

The primary outcome combines correct later prediction and authorized action confirmed by an independently verified simulator receipt. Action accuracy and prediction/action success were both 100% in acquired arms and 0% in every control arm. The result demonstrates the registered causal use of acquired distinctions in these finite categorical tasks. It does not establish real-world qualia, consciousness, human-relative significance, open-world tool learning, or general strategy quality. No capability level closes.

The exact runtime was attested: extension SHA-256 `b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1`; build receipt SHA-256 `6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1`; build source fingerprint `73c04733538d88f983beb5139e2dfae4633e686738f9161f56a8b2678e8e2c54`. The frozen source bundle is `138495281c1c85c79502f44d87dc559315aa305829ea8f471405db80045fffc0`.

## Invalid v1 freeze

The first v1 raw allocation is preserved at `/tmp/cognition-linear-p17-heldout.json`, SHA-256 `372742d0525e3401146ff5df937ab28f5ad3adce50d873b0345d80855268d103`. The preregistration contained a mistyped build source fingerprint. The frozen analyzer rejected the artifact before producing a report; it is not scored or interpreted. The corrected v2 protocol used a disjoint held-out offset of 2,000,000 and a separately frozen runner/analyzer and preregistration. The v2 raw allocation SHA-256 is `1037a08e64238182040f5728e0e3963f5f013f1f8a1123cabbb86d164cd9a290`; its analyzer output SHA-256 is `223035e4e010562bf56d52617f88fb887dbd4ee1b61f41df803f8440033e53bf`.

## Resources and provenance

Each trained arm received five episodes per task; no-experience received none. The fixed exposure budget was 1,000 units, with a maximum of 50 ticks and 100,000 rule steps per tick. Mean graph nodes per task were 121 for acquired, 88 for frozen, 68 for no-experience, and 130 for shuffled in the development panel; held-out resource counts are in the raw scorecard. These synthetic-world counts are descriptive and are not extrapolated to deployment memory or latency.

The v2 runner/analyzer implementation is commit `712eae5f`; the standalone v2 preregistration is commit `815da7a8`. Development used 8 worlds per family/arm, 64 rows, and 400 controls; it passed integrity, conformance, efficacy, and all five tampering probes. The focused P17 integration/regression bundle passed 79 tests. Raw held-out files remain outside git.

P18 entry is supported for observation-built finite world models and verified simulator experiments, bounded by P16's finite receipt interface and P17's demonstrated source-bound behavioral consumer. No capability level closes.
