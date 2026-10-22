# Linear P12 results

**Status:** evidence closeout complete with limits. The registered social-
acquisition advantage is `FAIL`; the isolated explain/rebuild and safety
criteria pass. This bounded single-primitive panel closes no capability level.

## Frozen held-out draw

The preregistration was frozen separately in
[`COGNITION_LINEAR_P12_PREREG.md`](COGNITION_LINEAR_P12_PREREG.md), commit
`1de4e725`. The held-out runner metadata matches the preregistered runner
(`7b78c4f7db522c2baff4b631d34b89aeb7f9f01f4d3eca946deee079e6374181`), source
bundle (`10693dad22498f192100a9aa60c9bfc6f02bef3dacde98893f302e2a1babf24b`),
native engine source (`4326812f782ec8e324bdccc0c11d5424d3ad3a71f8dd0b723fb20cf4cee434f9`)
and binary (`b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`).
Runtime commit was `1de4e725445754c997056d150730a27477398a7a`; Python was 3.13.5.
Raw records and analyzer output are archived outside git at
`/tmp/linear-p12-heldout.json` and `/tmp/linear-p12-heldout-analysis.json`.

The fixed draw completed all 1,500 records: 200 each for observation,
demonstration, instruction and reward-only; 100 each for shuffled, missing and
body-mismatch controls; 200 isolated rebuild receivers; and 100 each for
source-ID and source-expression redaction controls. The registered seed offset
was 12,100,000. Limits were 24 ticks, 1,000 steps per tick, budget 12, eight
declared evidence opportunities, three native effect probes, and at most three
world action calls.

| Measure | Held-out result | Registered interpretation |
|---|---:|---|
| Social own-trial success (observation + demonstration + instruction) | 600/600 (100%) | Treatment outcome |
| Reward-only own-trial success | 200/200 (100%) | Comparator outcome |
| Social own-trial gain | 0 percentage points | `FAIL` against ≥20 points |
| Social schema adoptions | 600/600 | Mechanism observed; not efficacy |
| Reward-only schema adoptions | 200/200 | Mechanism observed; not efficacy |
| Rebuild adoption | 200/200 (100%) | `PASS` against ≥95% |
| Rebuild exact effect agreement | 200/200 (100%) | `PASS` against ≥95% |
| Source-ID redaction agreement | 100/100 (100%) | `PASS` |
| Source-expression redaction agreement | 100/100 (100%) | `PASS` |
| Shuffled/missing/body-mismatch controls | 0/100 adoptions and own-trial successes each | `PASS` |
| Pairing, allocation, input-audit, completion failures | 0 | `PASS` |
| False own grounding / unverified adoptions | 0 / 0 | `PASS` |
| Human comparison | unavailable | No protocol-matched baseline |

The advantage failure is valid: all arms were present, paired-world hash
failures and missing pairs were zero, and the runner/source/engine provenance
matched the frozen record. Preserve it as a failure; do not retune or rerun the
held-out allocation. The equal success rates do not show that social learning
has no benefit outside this fixture; they show that this registered test did
not meet its threshold.

## Work, evidence and limits

All social records declared eight evidence opportunities. Social arms averaged
one informative opportunity; reward-only averaged two, consisting of two
authorized own probes. Social arms used one world action call for the scored
trial; reward-only used three calls including its probes and scored trial.
Mean budget request debits were 2 and mean budget remaining was 10 in every
arm. Mean graph growth was 19 nodes / 6,218 estimated bytes for observation,
20 / 6,507 for demonstration, 27 / 6,802 for instruction, and 24 / 7,662 for
reward-only. Mean boot times were 0.0681s, 0.0472s, 0.0678s and 0.0681s,
respectively. Each social arm averaged two receipts. Rebuild averaged one
evidence exposure, two budget debits, 10 remaining units, 8 nodes / 2,774
estimated bytes, 0.0516s boot time and a three-token explanation.

The evaluator's expected effect is not supplied to the learner. Reward-only
candidate acquisition uses positive scalar feedback from its own authorized
action receipts, then separately funds native effect verification. Other arms
use the same shared model bank and their declared social evidence. The runner
uses native ProcessApply and P5 action authorization; Python provides world
events and evaluation I/O. The panel measures one primitive effect under the
minimal PMB profile, not broad natural-language understanding, multi-step
social learning, general process-map acquisition or human parity.

The raw scorecard SHA-256 is
`e8149e327ef71ea4b862345c71bb4b3b7fce7b6c59f3fa8165ab698250423789`; the
analysis SHA-256 is
`ae66046c2aea0d37c44743aeafdac8999e989d6c0f3537c283664bdec2afc138`. Runner
and analyzer self-checks passed, and the preregistered P12 acceptance bundle
passed (54 tests). The adjacent verb self-repair module remains unverified
because the environment lacks its `requests` dependency; its collection
failure is not a P12 held-out regression.

## Next supported entry

Phase 13 may proceed using P12's verified episodes/processes, the P1 replay
scheduler and Phase 10 traces. Treat the P12 social advantage as failed and do
not assume fresh process-map learning. Phase 13 must establish its own delayed
behavior, compute/storage cost and safety outcomes before claiming sleep or
library-reuse benefit. No L1 or L6 capability claim follows from this panel;
human comparison remains unavailable.
