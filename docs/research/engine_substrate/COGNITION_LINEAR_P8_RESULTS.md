# Linear P8 results — learned model fixtures and experiments

Status: frozen P8 held-out draw reported. Results establish native behavior on finite graph fixtures. They do not establish open-world causal learning, calibrated information gain or external intervention.

## Provenance and completion

The preregistration is [`COGNITION_LINEAR_P8_PREREG.md`](COGNITION_LINEAR_P8_PREREG.md), frozen at `df072293`. Runner metadata reports engine commit `df0722938f7915c5ad4e2ba3c234f0029e771df5`, source bundle SHA256 `60cd79a5ec7b46fa35842ad69ea66fd575389eab9ebacbd246546b905ace001a`, engine source bundle `516e30d5902c21b683f90e9ff7d1251f85b2e451256ccafaced094271cdd4749`, and native binary `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`.

Raw artifacts remain outside git:

- `/tmp/linear-p8-heldout.json` — SHA256 `5bc0b7c6d8bd282a74b58943c103ef30aa2f9e17df5b1bd996f5d8f008a19235`.
- `/tmp/linear-p8-analysis.json` — SHA256 `7c33a849eec99a4960334432f8a2919d8ee75316293478a71f75e6d2300cb3f5`.

All 1,100 rows completed without missing adapters or timeouts. The input-answer exposure counter was zero. Boot/profile integration and focused P8 tests passed before the draw.

## Results

| Panel | Result | Classification |
|---|---:|---|
| Learned selector, finite mechanisms | 200/200 identified | `MECHANISM_PASS` within supplied hypothesis sets |
| Fixed-probe comparator | 100/200 identified | Comparator baseline |
| Passive equal-exposure comparator | 0/200 identified | Comparator baseline |
| Interaction count | 200 per arm | Equal one-interaction cap in each arm |
| Regular latent fixtures | 100/100 held-out continuations verified; 100 nonrecurring cases remained unknown | `MECHANISM_PASS` |
| Missing-evidence controls | 100/100 unknown | `PASS` fail-closed control |
| Irregular-sampling controls | 100/100 unknown | `PASS` fail-closed control |
| Funded projection revisions | 100/100 produced a result-linked audit and changed version | `MECHANISM_PASS` for graph projection fixture |
| Agent-visible hidden answers | 0/1,100 | `PASS` for fixture isolation |

The learned selector exceeded the fixed probe by 50 percentage points and passive exposure by 100 points on these cases. All arms received the same explicit competing hypotheses and probe outcome predictions; only the learned arm selected through native policy rules. The fixed and passive arms are mechanical comparators. These results do not show that the system induced the supplied hypotheses from raw mechanism worlds. P8.02's observed-trace induction has separate native acceptance evidence.

The latent panel required three complete regular windows and a fourth held-out continuation. Irregular or insufficient input stayed unknown. The refinement panel approved one budget-backed probe, ingested an observed result and advanced a finite projection fixture with a linked audit. It does not show an external simulator or actuator changed state.

## Criteria and supported next entry

The registered identification threshold (≥20-point gain or the declared intervention-saving alternative with bounded accuracy loss) passed on the supplied finite portfolio. Latent continuation and funded graph-refinement criteria passed on their fixtures. General model induction from open observations, probabilistic distributions, numeric VOI under uncertain priors, and real intervention/refinement remain `NOT_ESTABLISHED`. Human comparison is unavailable.

Phase 9 may consume typed observed-effect candidates, source-bound counterexamples and the finite graph experiment interface. It must retain the limits above and cannot claim general learned causal models from supplied hypothesis cases.
