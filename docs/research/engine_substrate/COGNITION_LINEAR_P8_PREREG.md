# Linear P8 evaluation preregistration v1

Status: frozen before held-out execution. This panel measures native fixture mechanisms for selecting funded probes, retaining/updating finite hypotheses and validating regular-window residuals. It does not establish open-world model induction, calibrated VOI or external-world refinement.

## Frozen provenance

- Phase: `linear-p8-v1`; runner `evaluation/process_mastery/linear_p8_v1.py`; analyzer `evaluation/process_mastery/analyze_linear_p8_v1.py`.
- Freeze commit: `4376ec53d663845c953568f2ab912930e0ec18ba`.
- Runner SHA256: `9c03b6ec692619b15e7a01c9b6e7dc7de079bb29f7dc8c61beab9c87a0fcef88`.
- Analyzer SHA256: `9a868acf504b9d4576a562c2ad3c814c37b53d3b44d392975303386a835d85ee`.
- Source/seed/profile bundle SHA256: `60cd79a5ec7b46fa35842ad69ea66fd575389eab9ebacbd246546b905ace001a`.
- Engine source bundle SHA256: `516e30d5902c21b683f90e9ff7d1251f85b2e451256ccafaced094271cdd4749`.
- Native engine binary SHA256: `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`.
- Limits: 2,000 rule steps per tick, at most 30 ticks, declared 32 hypotheses and 32 funded experiment requests.
- Development self-check scorecard SHA256: `6b7d44ddc66613bb335a3114415582a4bc2d9d830df3cd0c1540b3510a2aa808` at `/tmp/linear-p8-dev-selfcheck.json`; runner and analyzer self-checks pass.

## Allocation and arms

| Panel | Seeds | Allocation |
|---|---:|---:|
| Finite mechanism worlds | 3,000,000–3,000,199 | 200 worlds × learned selector, passive equal-exposure, fixed-probe arms |
| Regular temporal/latent worlds | 3,000,200–3,000,399 | 200 worlds, half with a recurring latent relation and half with a nonrecurring relation |
| Missing-evidence controls | 3,000,400–3,000,499 | 100 worlds with fewer than three complete residual windows |
| Ambiguous/irregular controls | 3,000,500–3,000,599 | 100 worlds with irregular sampling |
| Funded refinement panel | 3,000,600–3,000,699 | 100 distinct observed-result/projection-revision trials |

Mechanism arms receive the same explicit two-hypothesis portfolio, probe predictions, world outcome and one-interaction cap. The learned arm runs Rust graph rules to refuse the noninformative probe and select the lowest-cost distinguishing probe. The passive arm receives one noninformative observation. The fixed arm mechanically executes the same named probe; external scoring measures whether it happened to distinguish the supplied alternatives. Hypotheses are supplied alternatives for this panel, not claims that this 200-world arm learned them from experience. P8.02 induction is separately established only by its source-bound mechanism tests.

The temporal panel provides three complete regular windows and one fresh continuation where applicable. Controls remove enough evidence or regular sampling. The refinement panel funds a distinguishing probe, adds an observed result, and checks for a result-linked native projection revision. All hidden truth remains in detached scorecard fields, never in agent input.

## Measures and thresholds

1. **Probe selection and identification:** report completion, selected probe, interaction count, portfolio support/disconfirmation and identification rate by arm. The proposed criterion is at least 20 percentage points higher identification or at least 25% fewer interventions with no more than a 2-point accuracy loss. This runner uses a supplied finite hypothesis portfolio and a fixed one-step outcome; passing does not establish learning those models in an open world.
2. **VOI:** only qualitative separation of predicted outcomes is established. Unknown hypothesis probabilities remain unknown; the runner does not calculate or claim numeric information gain.
3. **Latent verification:** a candidate must explain the recurrent pattern and predict the held-out continuation. Report candidate rate, verification rate, and false candidates on nonrecurring, missing and irregular controls. Re-induction applies only to the declared regular-window fixture.
4. **Funded refinement:** require a unique approved budget request, an observed outcome and a changed projection version with a linked audit. Require zero unsupported certifications and at least one verified completion. The graph projection fixture does not represent a physical actuator or external service.
5. **Status and leakage:** missing adapters remain explicit `UNSUPPORTED`; source/answer exposure is a failure. Human intervention comparisons remain unavailable.

## Reproduction

```bash
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/linear_p8_v1.py --self-check --output /tmp/linear-p8-selfcheck.json
.venv/bin/python evaluation/process_mastery/analyze_linear_p8_v1.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/linear_p8_v1.py --split heldout --n 200 --output /tmp/linear-p8-heldout.json
.venv/bin/python evaluation/process_mastery/analyze_linear_p8_v1.py /tmp/linear-p8-heldout.json
```

Keep held-out raw rows and analysis outside git and record their hashes. Seeds, adapters, analyzer and thresholds are frozen for this version.
