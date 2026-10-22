# Linear P13 results

**Draw completed:** 2026-10-22 using the frozen protocol in
[`COGNITION_LINEAR_P13_PREREG.md`](COGNITION_LINEAR_P13_PREREG.md). The registered
allocation was run once. Raw records and analysis remain outside git at
`/tmp/linear-p13-heldout.json` and `/tmp/linear-p13-heldout-analysis.json`.

| Archived artifact | SHA-256 |
|---|---|
| Raw 900-record scorecard | `ff22fcf0317a47bafb6305caad4df40d4cec6cc9e7692fa858ff4444f83babf8` |
| Analyzer output | `0329ecf127171c1c4880fb6041764a20147e4456f03e6415601cdb8119362668` |
| Frozen implementation commit | `8bb8232a52eeded2ebdad71e0bd76dcb898c07e0` |
| Frozen protocol commit | `f0624e1e6a88e89531158c9b5d58b71e357e739d` |

The runner provenance matched the frozen runner, analyzer, profile, world
adapter, engine-source and engine-binary hashes. The scorecard contains 800
paired records (200 per arm) and 100 restart controls. There were no missing
or duplicate arms, no world or primitive-access hash mismatches, no hidden
answer/strategy audit failures, and no failed task completions.

## Registered outcomes

| Arm | Accuracy | Mean delayed primitive steps | Mean native rule steps | Mean graph-node growth | Mean serialized graph bytes | Mean boot seconds | Mean declared budget debit |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full sleep | 100% | 1 | 212 | 77 | 255,219 | 0.2424 | 7 |
| P1 replay-only | 100% | 32 | 261 | 56 | 241,155 | 0.2437 | 1 |
| Matched-compute awake rehearsal | 100% | 32 | 269 | 63 | 250,488 | 0.2432 | 0 |
| No offline work | 100% | 32 | 217 | 46 | 238,392 | 0.2421 | 0 |

The primary delayed-accuracy gain over replay-only was **0 percentage points**
against the preregistered **≥10-point** criterion: **FAIL**. New-task loss was
0 points against the ≤2-point limit. Since every arm solved every task, this
panel does not show a sleep-driven accuracy or retention advantage.

Full sleep produced one cost-positive process library chunk per stream. Its
complete package cost was 39 units versus 64 inline units for the two source
traces. Amortizing the package over those sources and charging one retrieval
and application for the delayed task gives 20.5 units against 32 primitive
steps, a **35.9375%** exact-work reduction against the registered **≥25%**
criterion: **PASS**. The delayed trace used the library process in 200/200
streams. The strategy subpanel obtained an approved funded request and a
verified strategy recall in 200/200 full-sleep streams; the mean compatible
strategy candidate count was 2. Strategy yield remains observed task evidence,
not proof.

The 200 full-sleep streams each recorded six sleep-stage receipts: two replay
receipts and one each for consolidation, decay, library and advisory
recombination. Declared budget debits averaged 7 units: 4 later-stage debits,
2 cycle-admission/replay debits and 1 approved strategy-recall debit. Budget
balance fell by 2 units net after epoch refill. Replay-only declared one
cycle-admission debit per stream. No external world actions occurred in any
arm.

Awake rehearsal work averaged 51 native rule steps against 50 sleep-stage
steps, within the frozen 5% compute-matching bound. It required 17 additional
one-primitive rehearsal tasks per stream; these exposures are included in the
reported mean of 22. The other arms had five evidence exposures each (two long
source tasks, two strategy-subpanel source tasks and one interference event).

All 100 interrupt/restart controls completed. Foreground demand left the next
stage pending; graph reload preserved the cursor; the next quiet epoch resumed
the consolidate stage; and repeated ticks at that epoch produced no duplicate
receipt or debit. Sleep-receipt provenance, `not_observed` labels, shared
budget evidence, pairing, answer/strategy audits, task completions, allocation,
awake-compute matching and restart controls had zero analyzer failures.

## Interpretation and next entry

P13's registered primary criterion is a failure; it remains a failure in this
ledger. The positive library work result is limited to a synthetic permutation
domain with a verified 32-step repeated trace. It establishes cost-accounted
reuse under the tested native process rules, not general program/capability
trace extraction or broad retention benefit. Strategy recall is likewise
limited to same-shape, same-epoch graph-held tasks. The experiment used no
physical action sink, so external observed-outcome parity is unavailable.
Human comparison is `UNAVAILABLE_PROTOCOL_NOT_MATCHED`; this result does not
close any whole capability level.

Phase 14 may begin only from these supported inputs: the verified process
library and its equivalence witnesses, observed-yield strategy entries with
funded recall/application receipts, P1 replay receipts, and exact held-out
task outcomes. It may not assume that sleep improves delayed accuracy. Proof
claims remain limited to proof-admitting domains with native checking; bounded
fingerprints are not proofs. Complete I4.5 and I7.3 before adopting I7.1
operator authorship into the live loop.

Verification after the draw: the frozen P13 test command passed 25 tests.
The integration bundle passed 60 tests and the expanded bundle including
`tests/test_process_lifting.py` passed 65 tests during E2 validation. Earlier
P10 (0-point) and P12 (0-point) advantage failures remain unchanged.
