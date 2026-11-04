# Linear P9 held-out results

Status: frozen evaluation completed; limits retained. The raw scorecard and analyzer output are archived outside the repository at `/tmp/linear-p9-heldout.json` and `/tmp/linear-p9-analysis.json`.

## Registered primary outcome

The held-out draw completed all 1,500 rows: 200 exact-effect cases per arm, 200 irreversible/stochastic cases per arm, and 100 alias/invalid-inverse controls per arm. Every row was `COMPLETED`.

| Family / arm | Passed | Total | Rate |
|---|---:|---:|---:|
| Exact inverse, operators on | 200 | 200 | 100% |
| Exact inverse, operators off | 0 | 200 | 0% |
| Exact inverse, held only | 0 | 200 | 0% |
| Irreversible/stochastic evaluator controls, operators on | 200 | 200 | 100% |
| Irreversible/stochastic evaluator controls, operators off | 200 | 200 | 100% |
| Irreversible/stochastic evaluator controls, held only | 200 | 200 | 100% |
| Alias/invalid-inverse controls, operators on | 100 | 100 | 100% |
| Alias/invalid-inverse controls, operators off | 100 | 100 | 100% |
| Alias/invalid-inverse controls, held only | 100 | 100 | 100% |

The primary exact-effect coverage difference was **+100 percentage points** (paired: 200 operators-on-only successes, 0 operators-off-only successes). All 200 exact candidates matched the scorer-only inverse and passed native application on three fresh states. There were zero exact verification failures and zero target-answer leaks. The runner reported zero actions and zero interactions in every arm.

Each exact treatment/control started with a 10-unit budget. The Track I on/off rounds each spent 4 units, leaving 6; the held-only arm retained all 10. The operator-off treatment still paid the same round setup cost, as preregistered.

The 200 irreversible fixtures returned no exact inverse for the singular matrix. The detached native finite-distribution evaluator retained both supplied outcomes and reported unknown mass `0.25` in all arms. These are evaluator conformance checks with an explicit finite input; they do not show that an agent learned a stochastic model. The control family retained both distinct schemas despite their collision on the constant partial probe, confirmed different effects on a fresh state, and refused exact inverses for singular and malformed values.

## Runtime and provenance

Mean total per-trial wall time (including agent boot) and mean graph-node count were:

| Family / arm | Mean seconds | Mean graph nodes |
|---|---:|---:|
| Exact, operators on | 0.0436 | 762 |
| Exact, operators off | 0.0435 | 760 |
| Exact, held only | 0.0244 | 741 |
| Irreversible/stochastic, operators on | 0.0545 | 756 |
| Irreversible/stochastic, operators off | 0.0551 | 756 |
| Irreversible/stochastic, held only | 0.0353 | 740 |
| Controls, operators on | 0.0503 | 757 |
| Controls, operators off | 0.0536 | 757 |
| Controls, held only | 0.0319 | 741 |

Rows also record graph edges. Separate boot-time and heap/RSS measurements were not captured by the frozen runner; total elapsed time includes boot, and graph-node/edge counts are the available memory-growth proxy. No external action sink was invoked. The scorecard flags no agent-input target leaks. There was no protocol-matched human baseline, so human comparison is unavailable.

- Preregistration: [`COGNITION_LINEAR_P9_PREREG.md`](COGNITION_LINEAR_P9_PREREG.md), SHA-256 `5bf2452a936731d58933fdf2ba59a537937d35c89203aee8e602f256d2123c5b`
- Freeze commit: `829f824b3295f77f876b5d1f2026924b6aff8e97`
- Held-out scorecard SHA-256: `fe576ce01ed0a1f706ca893b580e747e51641839663632f8de7e96c37d495210`
- Analyzer output SHA-256: `4033f94ef8e073ac60a0bfe8f685438ed12214eebf96df5541340ea10a1d9a39`
- Held-out runner commit recorded in the scorecard: `829f824b3295f77f876b5d1f2026924b6aff8e97`
- Frozen engine binary SHA-256: `9a65cdd66870bd64204b72dce98732ab6c81d7fe504ca96b772b9729348d078d`

## Classification and next entry

The preregistered exact-effect threshold passed, with zero verification failures and zero answer leaks. Both control families passed. This closes P9's finite evaluator/invention acceptance and authorizes P10.01 contract work for parametric process lifting and goal interfaces.

The result supports only funded inverse invention over the supplied finite 3-cycle family, plus the tested parity-wall and repair/distribution evaluator boundaries. It does not establish general process induction, autonomous operator discovery, learned stochastic distributions, external refinement, downstream puzzle solving, or any whole capability level. Inherited P3/P4 failures and limitations remain unchanged. P10 must use its specified discovered-strategy, greedy and primitive-search arms; no supplied solution or placement strategy is authorized.
