# P22 four-arm development wiring probe

This is a development-only native wiring diagnostic, not a preregistered
comparison. Four fresh cognition-on graphs were run per family on the same
eight v2 **training** worlds (draws 0250–0257): unchanged, adaptive-only,
invention-only, and full. Every arm received the same answer-free task inputs
and held primitive schemas. Each graph used the declared shared ThinkingBudget
capacity of 64. Candidate digest attestation ran when a graph minted a
candidate; no candidate-specific approval or world action was created. The
initial run did not read validation worlds; the later read-only development
validation refresh is reported below. No held-out world was read.

| Family | Unchanged solved | Adaptive-only solved | Invention-only solved | Full solved | Candidate proposals (invention-only / full) |
|---|---:|---:|---:|---:|---:|
| D4 v2 | 3/8 | 3/8 | 3/8 | 3/8 | 5 / 1 |
| Loopover v2 | 1/8 | 1/8 | 1/8 | 1/8 | 0 / 0 |

The runner also records successful native graph-rule progress firings in its
digest-bound resource snapshot (this is not match-enumeration count): D4 used
9/67/24/96 for unchanged/adaptive/invention/full; Loopover used
16/109/29/138. This counter is an additional work denominator, not a claim
that resource matching has passed. The graph-native runner made zero external
model calls. Allocator/resident-memory measurement remains unavailable; the
later timing refresh below adds observed per-arm elapsed wall time.

Resource comparison treats unmeasured runtime counters as unavailable rather
than as zero. This matters for older snapshots that predate rule-step
instrumentation; they cannot pass an exact resource-match check by omission.
The refreshed snapshot records canonical full-graph persistence bytes (nodes
and edges), edge and node counts, and the native runtime's graph-memory byte
estimate. These are separate measurements: the native estimate is not process
RSS, and neither is allocator-wide memory.

These counts are training-panel diagnostics and must not be interpreted as
generalization or treatment effects. No arm had a candidate approval or a
world receipt. The resource comparator correctly reports mismatches across
budget requests/spend, native solver work, search attempts/work, task and
outcome counts, and serialized graph size. Consequently, neither equal
cumulative compute nor an efficiency comparison is established.

A native settlement rule now marks funded search requests `global_attempt_ceiling`
after the aggregate native-attempt count reaches the configured limit, and the
P22 bridge records that status as a terminal `search_attempt_ceiling` outcome.
This allowed all four arms to terminalize all eight tasks in both families and
released the sequential curriculum scheduler. The first four-arm run exposed
overshoot from simultaneous grammar activations; that pre-repair run is
preserved in the prior plan record and hashes. The current raw records below
are the refreshed run after the hard-cap repair.

**Hard-cap repair and refreshed run (2026-10-23):** Added native
`AddNodeWithinCounter`, which reads and increments the shared policy counter in
the same graph mutation that creates an attempt node. A denied claim leaves the
attempt variable unbound, so its later edge effects do nothing. The cap-one,
two-task, three-process reproduction now creates exactly one attempt; the
focused regression verifies `attempts_reserved == attempt_nodes`. The
eight-world four-arm rerun creates exactly 64 attempts and records 64
reservations in each invention-enabled arm, and zero in the arms with invention
disabled. Solved counts remain D4 3/8 in every arm and Loopover 1/8 in every
arm, so these remain wiring diagnostics rather than treatment effects. Resource
vectors are still unequal, allocator memory remains unavailable, and no
efficiency claim is supported. Independent-goal approved lineages and
exact candidate authorizations remain open, so P22.E2/E3 are still gated.

**Timing and memory instrumentation refresh (2026-10-23):** The runner records
per-arm elapsed wall time from before cognition-on boot through the final
resource snapshot. Each arm runs in a separate worker process and records its
`ru_maxrss` high-water mark. This refresh also corrects a prior accounting
under-count: `serialized_graph_bytes` summed node records but omitted edges. It
now measures the canonical complete `graph_to_dict()` representation; snapshots
also record edge/node counts and `memory_total_bytes()` from the native runtime.
The D4 arms use 275,805–372,400 serialized bytes and 163,135–205,280 native
graph-memory bytes; Loopover uses 283,098–388,032 serialized bytes and
169,144–226,542 native graph-memory bytes. Peak process RSS was 64.8–65.6 MB
for D4 and 64.9–65.6 MB for Loopover. Elapsed times were 0.246–0.284 s for D4
and 0.247–0.308 s for Loopover. RSS includes Python and native runtime overhead;
native graph-memory bytes are the substrate's estimate, not allocator-wide
usage. These single-run timings include boot and task setup and remain
scheduling-sensitive; they are observed outcomes, not exact-match dimensions.
The exact resource vectors remain unequal, so no efficiency comparison is
supported. Solved counts, attempt caps and proposal counts are unchanged.

Current raw records after the read-only validation refresh:

- [`p22_four_arm_v2_d4.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_d4.json), SHA-256 `c1814594234d8527a1dcd9f5f774096529716cf243f7b554aa9abdd821c7ec3c`.
- [`p22_four_arm_v2_loopover.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_loopover.json), SHA-256 `7018aae3336debf19d4a2a8e2331bb01f9436d34875c2b5a41af4e069a80a982`.

Reproduce with:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_four_arm_development.py \
  --family d4 --training-draws 250 251 252 253 254 255 256 257 \
  --validation-draws 350 351 352 353 354 355 356 357 \
  --output evaluation/process_mastery/results/p22_four_arm_v2_d4.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_four_arm_development.py \
  --family loopover --training-draws 250 251 252 253 254 255 256 257 \
  --validation-draws 350 351 352 353 354 355 356 357 \
  --output evaluation/process_mastery/results/p22_four_arm_v2_loopover.json
```

Runtime-dependent elapsed time and RSS fields vary between runs, so complete
artifact byte equality is not expected. The current raw artifact hash binds
each observed run; the deterministic allocation and outcome fields reproduce
from the command above. This diagnostic does not close the four-arm learner
gate, candidate authorization, matched resource accounting, preregistration,
or held-out evaluation.

## Read-only unapproved-candidate validation refresh

Each arm now passes every native-verified `unapproved_candidate` through the
existing answer-free v2 validation-panel scorer. The adapter never approves
or executes a candidate in a world. D4 validation draws 0350–0357 produced
five candidate nodes in invention-only (three unique expression digests, with
all duplicates retained) and one in full; each candidate scored 1/8. The
invention-only and full arms share one expression digest, which is counted in
both arms and is not treated as independent evidence. Unchanged and
adaptive-only produced no proposals. Loopover produced no candidates in any
arm, so it has no candidate-score denominator and is not assigned a zero
candidate score. Task solving remains 3/8 for every D4 arm and 1/8 for every
Loopover arm. These small selected development panels establish neither
generalization nor an arm effect.

The runtime resource vector now includes the number of native candidate
validation evaluations (D4: 40 invention-only and 8 full; Loopover: 0 all
arms). Every candidate row retains its digest and all eight validation world
outcomes. Approval and world-receipt counts remain zero. Training draws
0250–0257 and validation draws 0350–0357 are consumed development allocations
and excluded from any later preregistered use. No held-out draws were read.

## Higher-ceiling learner-adapter pilot

The 64-attempt cap in the eight-world panel did not produce any Loopover
proposals. To test whether that was only a development ceiling issue, a second
four-arm panel used two v2 training worlds (draws 0260–0261), two disjoint
answer-free validation worlds (0360–0361), and the same 10,000-attempt global
ceiling in every arm. All eight arm/family runs terminalized. D4 invention-only
and full each produced two candidates after 4,765 attempts; their candidate
digests and nonactionable scores matched across the two arms (0/2 and 1/2).
Loopover invention-only and full each produced one candidate at the full
10,000-attempt ceiling; both scored 0/2. Unchanged and adaptive-only produced
no candidates in either family. All arms solved 0/2 training worlds. No
approval or world receipt was created. Resource vectors remain unequal, and
these tiny development panels do not estimate learning or efficacy.

These results establish that the native proposal and validation adapters can
produce a candidate in both claimed families under a larger common ceiling.
They also show that the former zero-proposal Loopover result was sensitive to
the 64-attempt development cap. The 10,000-attempt ceiling is a development
diagnostic only and is not frozen for E2.

- [`p22_four_arm_v2_search_10000_d4.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_search_10000_d4.json), SHA-256 `137342e58337f8b863c1f4ea0ff942f28ef7d6b02a6acca126fd409326194255`.
- [`p22_four_arm_v2_search_10000_loopover.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_search_10000_loopover.json), SHA-256 `892428406f308c1d4e46b9cd2ab46941a5a577083a10341fe9f854be858375d4`.

Reproduce with `scripts/run_p22_four_arm_development.py` using the corresponding
family, `--training-draws 260 261`, `--validation-draws 360 361`,
`--search-attempt-ceiling 10000`, and each family-specific output path above.
Training draws 0260–0261 and validation draws 0360–0361 are consumed
development allocations and excluded from any preregistered use.

## Eight-task higher-ceiling panel

The common 10,000-attempt ceiling was then tested on eight newly allocated
training and validation worlds per family (training 0270–0277, validation
0370–0377). All four arms terminalized. D4 solved 5/8 in every arm; Loopover
solved 2/8 in every arm. D4 invention-only and full each generated three
proposals with the same three expression digests; their validation scores were
1/8, 2/8 and 0/8 by digest. Loopover invention-only generated two proposals
and full generated one; every candidate scored 0/8. Unchanged and adaptive-only
generated no candidates. No approvals or receipts were created. These outcomes
show that candidate proposal and validation execute in both family adapters,
but the candidates show weak or absent validation performance and the four
arms show no training-score separation. The measured resource vectors differ,
and candidate-generation costs remain part of those vectors. No efficacy or
efficiency claim follows.

- [`p22_four_arm_v2_search_10000_8_d4.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_search_10000_8_d4.json), SHA-256 `e6e9ef629a5fdd68cd9f2011fe316d9ee907b81d2d52c599ce602289baba0b63`.
- [`p22_four_arm_v2_search_10000_8_loopover.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_search_10000_8_loopover.json), SHA-256 `efa9eb7127fdeadc51e201e239ac44ebca943f4fbf63c5582cf8ae4498f53a48`.

Reproduce with the same runner, family-specific output path, training draws
`270 271 272 273 274 275 276 277`, validation draws `370 371 372 373 374 375
376 377`, and `--search-attempt-ceiling 10000`. All four policy settings use
the same cap. These train and validation allocations are consumed and excluded
from preregistered use.

## Distinct-goal training qualification diagnostic

A separate training-only probe used two independently generated v2 goals per
family instead of repeating one target. D4 draws 0200/0201 produced two
proposals; Loopover draws 0206/0207 produced one. None qualified on the second
task. The candidates were scored nonactionably on the same eight development
validation worlds (D4 successes: 3/8 and 0/8; Loopover: 0/8). These are
candidate frequencies, not matched effects; all approval and receipt counts
were zero. The results show the current native qualification route does not
establish a candidate trained across independently generated goals. They do
not establish that independent-goal improvement is impossible.

Candidate node IDs are local to a graph. In particular, the Loopover row
reused `#2945` but had digest
`09d1361d650273ec4f84c613d9a13dd995083abb78d36d2ea602d5f15dd9fcda`, which
differs from the `#2945` digest in the candidate-specific approval request.
Only the complete digest and binding can identify an authorized candidate.
Training draws 0200–0207 and validation draws 0201–0208 are consumed
development allocations and must be excluded from later preregistered draws.

- [`p22_distinct_goal_training_probe_d4.json`](../../../evaluation/process_mastery/results/p22_distinct_goal_training_probe_d4.json), SHA-256 `ebe7a180ca81690d5c256e0262d2d2ef0b077947f3b7169c90ae98544b18753a`.
- [`p22_distinct_goal_training_probe_loopover.json`](../../../evaluation/process_mastery/results/p22_distinct_goal_training_probe_loopover.json), SHA-256 `72845529c7d5238d3920627fa7ba929079a340d811efd82a21ad8406408f290d`.

## Follow-up native composition mechanism result

The zero-qualification outcomes above are retained as the result for those
specific training pairs. A later development repair added digest-attested
candidate composition before broad recursive expansion, specialized child
candidate minting, and atomic global plus per-request reservation. Selected
training fixtures now qualify one source proposal in each family. The Loopover
pair was selected after inspecting generated process relations; neither pair
supports an efficacy claim. No approval, action receipt, or checkpoint was
created. See [`COGNITION_P22_CROSS_GOAL_COMPOSITION_20261023.md`](COGNITION_P22_CROSS_GOAL_COMPOSITION_20261023.md)
for exact candidate digests, raw hashes, consumed allocations, test results,
and limits. These later outcomes do not rewrite the earlier probe or make its
validation draws available for preregistration.

## Resource coverage audit refresh (2026-10-23)

The native snapshot now records the exact canonical JSON byte size of all
training `ProcessCurriculumEvidence`, `SolveTask`, and
`ProcessCurriculumOutcome` node payloads. The byte definition explicitly
excludes edges, while the separate `serialized_graph_bytes` remains the full
canonical graph readback. Each snapshot carries a digest-bound measurement
coverage map so missing contract dimensions cannot be silently represented as
zero. Exact graph counters, shared-budget use, recorded search/solver work,
caller-provided native steps/model calls, graph memory estimate, and optional
isolated-process RSS are measured where instrumented. Retrieval work, proposal
and verification work units, model-refinement cost, definition/decoder cost,
approval labor, rollback cost, and wall time are not all present in the native
snapshot; several remain unavailable to the full contract, so E2 stays open.

Two fresh eight-task diagnostics on the common 10,000-attempt ceiling exercised
the updated snapshot. D4 draws 0278–0285 solved 3/8 in every arm and produced
five invention-only and four full candidate nodes. Loopover draws 0278–0285
solved 1/8 in every arm and produced no candidate nodes. Resource vectors
remain unequal. Process RSS ranged 62.5–85.4 MiB in D4 and 62.2–141.0 MiB in
Loopover; invention-enabled arm wall times were much higher and scheduling
sensitive (up to 28.7 s for D4 and 71.2 s for Loopover). These measurements
are development diagnostics, not efficiency effects. No approvals or action
receipts were created. Training draws 0278–0285 and validation draws 0378–0385
are consumed and excluded from preregistered use.

- [`p22_four_arm_v2_resource_audit_d4.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_resource_audit_d4.json), SHA-256 `5b939219c2b1793a83cd46335696cac558bf5183598a06a66586ad46336c7944`.
- [`p22_four_arm_v2_resource_audit_loopover.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_resource_audit_loopover.json), SHA-256 `34dd301bcfc15d12ed21ee7382925295707a4d48e20c9ec6d575eea27b8d8e2c`.

Verification: `tests/test_p22_resource_accounting.py tests/test_p22_four_arm_development.py` — 10 passed. The refreshed raw outputs include all statuses and per-arm measurement coverage; no held-out allocation was accessed.

**Event-cost instrumentation refresh (2026-10-23):** Snapshots now retain
ThinkingBudget cost by `requester_kind` and digest-bound event counts for
proposal attempts/records, qualifications, candidate-validation evaluations,
and approvals. The comparator also includes these counters in each arm's
resource vector; a missing validation counter prevents a complete match. This
does not equate event counts with compute cost: proposal/verification work
units, retrieval, model refinement, definition/decoder, rollback and human
approval costs remain incomplete or unavailable. Re-running the same consumed
development allocation reproduced the arm outcomes (D4: 3/8 each; Loopover:
1/8 each), proposal counts (D4 5 invention-only/4 full; Loopover 0), and
resource mismatch under the enhanced snapshot schema. These are the same
development worlds, not a new independent sample or held-out access.

- [`p22_four_arm_v2_resource_audit_v2_d4.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_resource_audit_v2_d4.json), SHA-256 `ab39b5d474b725e25e3fd121e9d67fad6c7a2a992724024999349ab460735e6d`.
- [`p22_four_arm_v2_resource_audit_v2_loopover.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_resource_audit_v2_loopover.json), SHA-256 `6ce7e75eb09996011176a60edb6abe32e544fba55f4a261a0ae0803608b379d7`.

Verification: `tests/test_p22_resource_accounting.py tests/test_checkpoint_world_adapter.py` — 20 passed. The artifact-level resource/four-arm suite passes 10 tests.

## Distinct-goal probe failure retention (2026-10-23)

The training-proposal probe previously raised when the first training task
produced no candidate, so the run's allocation and failed task were lost. The
runner now returns a terminal `NO_CANDIDATE_FIRST_TRIAL` result with both task
identities, goal digests, statuses and associated request/attempt counters. A
candidate minted on the second task is retained but cannot qualify without a
first-task source candidate.

On a fresh pair selected only for distinct generated goals, D4 draws 0286/0287
produced two candidates; one qualified through the independent-goal
composition rule and scored 4/8 in the eight-world development validation
panel, while the other was unqualified and scored 1/8. Loopover draws
0286/0287 produced no first-task candidate; a second-task candidate scored
0/8 and remained unqualified. Both task pairs were distinct-goal pairs. No
candidate was approved or executed: approval and receipt counts were zero.
These small selected training pairs establish neither broad qualification
reliability nor efficacy. Both training allocations and validation draws
0386–0393 are consumed development data.

- [`p22_distinct_goal_probe_v2_d4.json`](../../../evaluation/process_mastery/results/p22_distinct_goal_probe_v2_d4.json), SHA-256 `c95eee38922ca153a3aeb8bc8c9ac0889b3e7be1b6cc36b0f8888f8d0897bc2b`.
- [`p22_distinct_goal_probe_v2_loopover.json`](../../../evaluation/process_mastery/results/p22_distinct_goal_probe_v2_loopover.json), SHA-256 `df9cd15f44dd1f7eae2b8ab6200210b951c96bddeee5f69462e7c5e553430ab7`.

Verification before the configurable-cap extension: `tests/test_p22_development.py` — 4 passed in 194.39 s. The D4
and Loopover probe artifacts preserve the candidate/attempt differences rather
than imputing a qualification outcome.

## Additional independent-goal qualification probes (2026-10-23)

Two additional fresh distinct-goal pairs per family were selected before
search and run through the same bounded development probe. D4 draws 0288/0289
produced one unqualified candidate (1/8 validation); draws 0290/0291 produced
one qualified candidate (0/8 validation) and one unqualified candidate (4/8).
Loopover draws 0288/0289 and 0290/0291 each produced one candidate, with zero
qualifications and 0/8 validation outcomes. All four pairs had distinct
generated goals. No approvals or world receipts were created. Together with
the preceding fresh pair, these observations are 1/3 qualified D4 pairs and
0/3 Loopover pairs; this is a small diagnostic, not a preregistered rate or an
efficacy estimate. Qualification did not imply validation success. Training
draws 0288–0291 and validation draws 0394–0409 are consumed development data.

- [`p22_independent_goal_qualification_d4_288_289.json`](../../../evaluation/process_mastery/results/p22_independent_goal_qualification_d4_288_289.json), SHA-256 `9c268fb261437eddd03c6bd3dfdcf48632aa2b82dc72213eea5e8b7568fce162`.
- [`p22_independent_goal_qualification_d4_290_291.json`](../../../evaluation/process_mastery/results/p22_independent_goal_qualification_d4_290_291.json), SHA-256 `75defe736b0aa3c11d84b88dff958759819468b8f060071a56802a85d2bba0c7`.
- [`p22_independent_goal_qualification_loopover_288_289.json`](../../../evaluation/process_mastery/results/p22_independent_goal_qualification_loopover_288_289.json), SHA-256 `171e1030b83de72dbba18478ec289b2c9c592c68826e513c7fc36431689d5274`.
- [`p22_independent_goal_qualification_loopover_290_291.json`](../../../evaluation/process_mastery/results/p22_independent_goal_qualification_loopover_290_291.json), SHA-256 `405ac00b96aea40116ae9ff8b23c79ad5276d28a6fb099c2274c203829cbc6cd`.

## Per-request search-ceiling diagnostic (2026-10-23)

The proposal-probe CLI now exposes the per-request attempt ceiling while
keeping the global ceiling fixed at 30,000. Both limits are validated and
recorded. The first 20,000-cap experiment on Loopover draws 0292/0293 applied
20,000 to both global and per-request limits; its first task consumed the
entire global budget, leaving no second-task search. Preserve this result as a
confounded ceiling diagnostic, not a comparison to the earlier 5,000-per-
request runs. Its validation draws 0410–0417 are consumed.

A fresh pair, Loopover draws 0294/0295, used a 20,000 per-request ceiling with
the 30,000 global ceiling unchanged. It generated one candidate after 20,000
attempts on the first request; the second used the remaining 10,000 attempts.
The candidate did not qualify and scored 0/8 on validation draws 0418–0425.
No approval or receipt was created. This supports only that a higher search
ceiling can expose a proposal path on a selected pair; it does not demonstrate
qualification, useful behavior or efficacy. Both training pairs and validation
blocks are consumed development data.

- [`p22_loopover_high_ceiling_probe_292_293.json`](../../../evaluation/process_mastery/results/p22_loopover_high_ceiling_probe_292_293.json), SHA-256 `0665606f79a8d47a6bde579e5948c1d8d450ce11c91b5b0b1db378a32109bd05`.
- [`p22_loopover_per_request_20k_probe_294_295.json`](../../../evaluation/process_mastery/results/p22_loopover_per_request_20k_probe_294_295.json), SHA-256 `f61e50fbdbeaf31ecaa19c2335bfbefa5f17129923b328e3af45778272b48ea3`.

After separating the global and per-request ceilings, `tests/test_p22_development.py` passes 5 tests in 178.34 s, including cap validation and failure retention.

## Isolated native rule-work capture (2026-10-23)

The development probe now has an opt-in `--measure-native-rule-work` mode. It
captures the native runtime's per-rule enumeration, candidate/binding,
expression-evaluation, pushdown and effect counters, joins them to rule names
in a single isolated graph store, hashes the snapshot, and disables/resets the
process-global audit counters on completion. Capture refuses to start if an
audit is already active or has accumulated rows, and refuses ambiguous
multi-store attribution.

A fresh D4 distinct-goal probe on training draws 0296/0297 and validation
draws 0426–0433 completed with one candidate (digest
`55ae292fc250aa05ee486c8adda841b151a76147f2a4f107dc7cb66a5097482d`),
2/8 nonactionable validation successes, zero approvals and zero world
receipts. Across 178 native rules, the capture recorded 1,547 rule
enumerations, 580,108 candidate pairs/tests, 301,479,018 term evaluations,
251,759 where evaluations, 6,284 node insertions and 28,716 edge insertion
attempts. The two recursive compose-attempt rules accounted for the largest
term-evaluation counts (88,958,067 and 80,755,784); these figures are runtime
work counters, not comparable operation units or a causal efficiency result.
The capture includes native work from the isolated probe through candidate
validation, but excludes Python-side world construction/validation and does
not measure allocator memory or end-to-end wall time. Training draws 0296/0297
and validation draws 0426–0433 are consumed development data.

- [`p22_native_rule_work_probe_d4_296_297.json`](../../../evaluation/process_mastery/results/p22_native_rule_work_probe_d4_296_297.json), SHA-256 `73103afcc5461f8eb0714899478892ca91a0db08606d272f266c6b54f762864f`.
- Per-rule snapshot SHA-256: `074873677cf83eea9c967ce790177fa23269e038464db72e7d98cd006507a17d`.

Verification: the isolated capture and audit-cleanup test passes. P22.E2/E3
remain open; this diagnostic does not supply balanced four-arm resource
vectors, approved cross-family lineages, or held-out efficacy evidence.

## Four-arm native-work comparison diagnostic (2026-10-23)

The four-arm runner can now capture the same per-rule runtime counters inside
each isolated arm worker. The verified native work payload is included in the
digest-bound resource snapshot, and resource comparison expands each captured
metric across arms (with zero used only when a captured metric has no events in
that arm). Partial capture across arms makes the comparison incomplete. Native
rule names are attached where an audit identity is available; any unmatched
rule indices are retained and marked `PARTIAL`, while aggregate metric totals
remain available for comparison. The analyzer resource adapter now exposes
native term evaluations as a separately sourced resource when captured and
keeps it `UNAVAILABLE` otherwise.

A fresh two-task D4 panel used training draws 0302/0303, validation draws
0434/0435, a 64-attempt ceiling and all four arms. Every arm solved 1/2 tasks.
Unchanged and adaptive-only generated no proposal; invention-only and full
generated one each. Per-arm term evaluations were 2,725 unchanged, 6,454
adaptive-only, 58,023 invention-only and 62,136 full; rule enumerations were
1,386, 4,346, 3,331 and 6,296. The resource comparison correctly reported
unequal vectors, including native work. Each arm captured complete counters;
all approval and world-receipt counts were zero. These tiny development
outcomes do not estimate efficacy or efficiency and remain unbalanced in total
resource use. Training 0302/0303 and validation 0434/0435 are consumed.

- [`p22_four_arm_native_rule_work_d4_302_303.json`](../../../evaluation/process_mastery/results/p22_four_arm_native_rule_work_d4_302_303.json), SHA-256 `e21657f58aa06738832d9313cb041aa6022fa802d47eb0327e9e757680ca7335`.

Verification: resource accounting, four-arm, analyzer and checkpoint-adapter
modules pass 32 tests after integration; the full four-arm integration test
also checks isolated capture on a single arm. P22.E2/E3 remain open.

After adding explicit rule-identity coverage, a fresh D4 panel on draws
0304/0305 (validation 0436/0437; ceiling 64) confirmed complete capture in all
four arms and the same expected resource mismatch. Every arm solved 1/2;
invention-only/full proposed one candidate each. Term evaluations were 2,717
unchanged, 6,446 adaptive-only, 37,629 invention-only and 41,742 full. No
approval or receipt was created. Draws are consumed development data.

- [`p22_four_arm_native_rule_work_d4_304_305.json`](../../../evaluation/process_mastery/results/p22_four_arm_native_rule_work_d4_304_305.json), SHA-256 `6ef40d74f94ffd08e89c913b01a5e3f1a9c1aaef8a6941dd4c1ad5216c423776`.

Checkpoint capture now carries digest-verified native rule-work totals into
the immutable generation snapshot. Descendants must preserve every measured
metric and cannot reduce cumulative term evaluations or other recorded native
work. The regression test accepts a monotone descendant and rejects a
descendant at 9 term evaluations after a parent at 10. This is accounting
mechanism evidence only; it does not create an approved lineage. The exact P22
E2 bundle (`test_improvement_estimand.py`, `test_independent_improvement.py`,
`test_checkpoint_world_adapter.py`, `test_improvement_causal_ablation.py`,
`test_analyze_linear_p22_v1.py`) passes 41 tests after this change.

The analyzer also requires a distinct candidate-selection allocation in
addition to training, validation and evaluation. It rejects missing selection
IDs and any repeated identity across these four blocks; held-out payloads must
include at least 200 selection worlds per family. The six analyzer tests and
standalone `--self-check` pass. This gate was implemented without accessing
held-out worlds.

## Exact candidate-binding reconstruction (2026-10-23)

The proposal probe now supports training-only reconstruction (`--validation-count 0`)
and emits each candidate's exact approval binding: expression tree/digest,
effect digest, parameters, guard state, domain, epochs and native status. This
lets a candidate-specific request be checked against a fresh graph without
replaying or inspecting validation outcomes. Fresh graph reconstructions of
the previously selected training pairs reproduced the qualified source
candidate in each family: D4 draws 0200/0202, digest
`8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788`; and
Loopover draws 0015/0026, digest
`f8277f0f8d7df4de63aed09cfc4f265ed2f6d9293034ae73ec18fdb9babfe75d`.
Parameters, guards, epoch triples `[0,0,0]` and two distinct-goal
qualification witnesses match the source artifacts. Both reconstructed runs
had empty validation allocations, zero approvals and zero receipts. The
Loopover reconstruction caught and corrected a one-character digest
transcription error in the candidate request document; the raw native
artifacts agree on the corrected digest above. These are reproductions of
consumed training pairs, not fresh qualification-rate evidence. No action was
attempted.

- [`p22_candidate_binding_reconstruction_d4_200_202.json`](../../../evaluation/process_mastery/results/p22_candidate_binding_reconstruction_d4_200_202.json), SHA-256 `9e903ccadb7127aeeba55a7e2be85bc1713f278047a00214f50086cf497b5668`.
- [`p22_candidate_binding_reconstruction_loopover_015_026.json`](../../../evaluation/process_mastery/results/p22_candidate_binding_reconstruction_loopover_015_026.json), SHA-256 `b79b41a785784c2abbe04761be49c881f09f0967742ce6cb496a4d84ee312834`.

The two-family binding regression passes. Exact candidate-specific approval
and checkpoint execution remain separate gates.

The E2 analyzer now makes `native_rule_term_evaluations` a required resource
field, matched across arms, so checkpoint rows must carry its verified native
counter source. Missing captures remain invalid/unavailable rather than an
imputed zero. The analyzer self-check includes a cross-family selection-split
reuse case. Resource accounting, checkpoint-adapter and analyzer tests pass
29 cases; standalone analyzer self-check passes.

## Native operation-cost category adapter (2026-10-23)

The resource adapter now attributes digest-bound native term evaluations to six disjoint rule classes: retrieval, proposal, verification, model refinement, definition decode, and rollback. It emits a measured value only when native rule identity coverage is complete. The counts are native rule-evaluation work units and do not represent wall time or human effort. Approval cost remains unavailable beyond an event count. A focused synthetic adapter regression verifies each category and source binding; this does not retroactively alter previously recorded snapshots or resource comparisons. The broader P22 E2 bundle passes 54 tests after the change. Candidate-specific approvals, checkpoint lineages, matched resource vectors, preregistration, and held-out results remain outstanding.

A read-only adapter audit over the existing D4 0304/0305 native-rule-work artifact derives measured term-evaluation costs for retrieval/proposal/verification/refinement: unchanged 40/20/92/8, adaptive-only 140/64/112/28, invention-only 200/24,635/7,724/20, and full 260/24,659/7,736. Definition-decode and rollback costs are measured zero in these four graphs under complete rule-identity coverage. The original raw artifact bytes and SHA-256 remain unchanged. These are categorized views of already captured development work, not a new sample or evidence of resource matching.

## Passive control checkpoint path (2026-10-23)

Added `capture_passive_checkpoint` for unchanged/adaptive-only arm generations. It snapshots cumulative work and parent binding while preserving the exact expression and creates no approval, candidate adoption, or world-action receipt. Checkpoint digests now support both approved descendants and this no-adoption form; the manifest loader accepts passive descendants only on the two control arms and verifies unchanged expression/parameters. The runner's lineage structural check validates all 24 parent links in the manifest and the self-check rejects a modified link. The 55-test focused P22 E2 bundle passes. No candidate-specific invention approval, checkpoint manifest, preregistration or held-out access was added.

The runner now has an end-to-end synthetic manifest validation fixture across both families, all four arms, and all three generations. It accepts passive unchanged/adaptive descendants with no approval or world receipt, accepts digest-bound invention/full descendants with the required approval/receipt IDs, and rejects changed passive expressions or missing invention-arm evidence. The focused P22 E2 bundle passes 56 tests. These generated in-test fixtures do not create live candidate approvals, checkpoint lineages, or held-out evidence.

The passive control-lineage test also binds cumulative native runtime steps and per-rule work through a descendant, then rejects a runtime-step regression and a term-evaluation regression. The full P22 E2 focused bundle remains green at 56 tests.

## Held-out resource preflight

Before generating any sealed evaluation world, the runner now requires exactly one frozen isolated wall-time measurement for each scored family/arm/generation checkpoint, source-backed measured values for every analyzer resource field, and values within every frozen ceiling. The regression fixture provides complete native runtime/rule counters but partial approval-cost evidence and confirms the runner rejects the manifest before held-out construction. The full focused P22 E2 bundle passes 57 tests. Approval event counts still do not measure review effort, so no freeze is yet admissible.

## Approved candidate-specific simulator actions (2026-10-23)

The exact approved D4 and Loopover candidates were reconstructed in fresh
training-only graphs. The native adoption rule consumed one approval for each,
then the finite permutation simulator accepted exactly one guard-satisfied
transition and returned one verified native receipt. D4 `#752` used digest
`8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788` on
training draw 0200; Loopover `#5761` used digest
`f8277f0f8d7df4de63aed09cfc4f265ed2f6d9293034ae73ec18fdb9babfe75d` on draw
0015. Result hashes are `f5d9335585ceecd90ab73300c079df256c959da34d105526d3d4411c230a2a0d`
and `e4ee1eec3ce70cb6d66442590f3d38a7a852d9b90e600ec51a16b29cf2374f6a`.
No validation or held-out worlds were materialized. These one-step receipts
do not create multi-generation lineages or establish benefit; later adoption
requires separate exact approval. The D4 guarded-adoption regression and the
broader P22 mechanism/resource bundle pass, 56 tests total.

## Human approval-effort measurement path (2026-10-23)

P22 `approval_cost` is now operationally defined as reviewer-reported seconds
per exact candidate approval. The native resource snapshot reports zero only
when the graph contains no approval events; when approvals exist it sums the
durations only if every event carries a finite nonnegative
`human_review_seconds` value with source `reviewer_self_report`. Missing or
mixed records remain `PARTIAL_EVENT_COUNT`, which continues to fail held-out
preflight. New simulated-adoption requests must provide the reviewer duration
before approval creation. The two previously approved actions predate this
instrument and remain unmeasured; no durations were inferred or backfilled.
The focused P22 mechanism, resource, checkpoint, and manifest bundle passes
69 tests, and both runner/analyzer self-checks pass. This closes the prospective instrumentation gap, not the historical candidate
cost gap or remaining lineage, four-arm, and preregistration requirements.

Two fresh distinct-goal training-only probes exercised the updated resource
path on draws 0400/0402. D4 produced the previously seen expression digest
`8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788`, but it
did not qualify on this pair; Loopover produced digest
`69e3cd2750ed7d498a29b00ec9191a0b46918217b1d2e036482c42eec466dc77`, also
unqualified. Both used empty validation allocations and created zero
approvals and receipts. These draws are consumed development evidence, not
approval requests or qualification-rate estimates.

- [`p22_approval_cost_instrument_probe_d4_400_402.json`](../../../evaluation/process_mastery/results/p22_approval_cost_instrument_probe_d4_400_402.json), SHA-256 `e5b4319869a2f8e68b38621def0e30cc0132e0616625f4b9911d1b4c6618d92a`.
- [`p22_approval_cost_instrument_probe_loopover_400_402.json`](../../../evaluation/process_mastery/results/p22_approval_cost_instrument_probe_loopover_400_402.json), SHA-256 `92c65796517bc3af415c4a86eb9074ea872c3259f381af9e78668b7dda3da827`.

## Prospective generation-one checkpoint capture (2026-10-23)

The training-only exact-adoption probe can now capture an identity-process
generation-zero ancestor before approval, then bind a verified one-step receipt
to a generation-one child. The child snapshot includes the reviewer self-report
and cumulative runtime/resource counters; the ancestor retains zero approval
cost. Native rule-work snapshots now support non-destructive cumulative reads,
so both checkpoints carry a digest-bound snapshot from the same capture window.
Regression coverage checks parent digest, generation, approval and receipt IDs,
resource snapshots, and preservation of the recorded native-rule identity
coverage status. The focused 62-test P22 bundle and runner/analyzer self-checks
passed before this final capture refinement; the combined resource, checkpoint,
four-arm and synthetic adoption modules pass 33 tests. Some
repeated captures initially reported partial identity coverage because the
adapter joined store-namespaced audit IDs as local indices. New captures now
use `p22_native_rule_work_v2`, retaining both the audit ID and store-local
index; digest verification continues to accept historical v1 snapshots.
The two-store capture regression and the synthetic generation-zero/generation-
one test now require complete native-rule identity coverage and pass. Existing
raw artifacts were not rewritten; any genuinely partial resource capture still
fails E2 preflight. No candidate approval or world action was performed during
this implementation work.

The P22 provenance closure now hashes `p22_development.py` and both development
CLI entry points (`run_p22_development_probe.py` and
`run_p22_four_arm_development.py`) in addition to the learner modules. A
provenance check confirms all three paths are included in the source bundle.
The current attestation reports `DEVELOPMENT_ONLY` with `artifact_tree_dirty`,
so no freeze or held-out run is admissible from this worktree.

The four-arm diagnostic now also places each arm's `perf_counter` duration in
the digest-bound resource snapshot's runtime counters, and marks its coverage
as measured. The same-world four-arm D4 regression passes with exact agreement
between the result field and snapshot value. This measures each arm through
training and candidate-validation work; it is development instrumentation and
does not replace the frozen isolated-worker wall-time records required by E2.
The resource comparator includes the measured elapsed time in its arm vectors
and marks unequal durations as a resource mismatch; the wall-time validation
and comparison regression passes.

## Fresh four-arm resource refresh (2026-10-23)

After the wall-time snapshot/comparator corrections, a fresh four-world
training-only diagnostic ran all four arms on D4 draws 0500–0503 and Loopover
draws 0500–0503, with a shared 64-attempt ceiling and complete native rule-work
capture. All arms solved 2/4 tasks in each family. D4 invention-only/full
produced two/one candidates; Loopover produced none. Both common-world runs
were terminal, had empty validation allocations, and created no approval or
receipt. Every contract resource dimension was measured, including native rule
work and arm wall time, but the realized vectors remained unequal; the
comparator marks `wall_time_seconds` unmatched in both families. These
training-only outcomes do not estimate efficacy, and the resource mismatches
continue to preclude efficiency claims.

- [`p22_four_arm_resource_refresh_d4_0500_0503.json`](../../../evaluation/process_mastery/results/p22_four_arm_resource_refresh_d4_0500_0503.json), SHA-256 `8a4f3ae3aad55780d0719fa160a2ee4fb9280cea493300f98324f85b96b4dd68`.
- [`p22_four_arm_resource_refresh_loopover_0500_0503.json`](../../../evaluation/process_mastery/results/p22_four_arm_resource_refresh_loopover_0500_0503.json), SHA-256 `95215bfd4349e0d4963a2002e54baacb34d57e2f9250e405ab1aa141022d5d1b`.

The resource-accounting and four-arm development modules pass 16 tests.
Runner/analyzer self-checks remain passing. No preregistration or held-out
world was accessed.

## Loopover no-candidate probe and resource-snapshot repair (2026-10-23)

Fresh distinct-goal Loopover training draws 0504/0505 produced no candidate
on the first task; both requests consumed 5,000 attempts, with zero validation
worlds, approvals, or receipts. The raw artifact retained a complete v2
native-rule-work payload at top level (947 rule enumerations and
1,270,873,417 term evaluations), but inspection found that its separate
`resource_snapshot` omitted the captured native work. The snapshot is therefore
not a complete resource record and must not be used for arm matching. The raw
file remains unchanged:

- [`p22_approval_cost_instrument_probe_loopover_0504_0505.json`](../../../evaluation/process_mastery/results/p22_approval_cost_instrument_probe_loopover_0504_0505.json), SHA-256 `4cf83e4ddbee922a26d0164058f4f12fd5e11dee959474e891af218095c62c90`.

The non-adoption return path now binds native rule work and runtime counters
into its resource snapshot, including measured wall time, attempt reservations,
and validation-evaluation count. Approved checkpoint reconstruction now rejects
any nonempty validation allocation. A fast training-only regression verifies
the v2 payload and digest are present in the resource snapshot; the validation
guard and exact generation-one checkpoint tests pass. The sequential-capture
regression and broader P22 bundles also pass. This fixes future records; it
does not rewrite or upgrade the consumed 0504/0505 artifact.

## Immutable native graph checkpoint state (2026-10-23)

New native checkpoints carry the canonical complete graph snapshot in
addition to the compact resource snapshot. The graph hash is included in the
checkpoint digest, and verification checks that the graph contains the same
active process expression and parameters. The manifest loader refuses a root
or descendant that does not carry this state. A restore helper loads the graph into a normally
booted agent and verifies byte-canonical equality before native work resumes.
This closes checkpoint-state persistence for future lineages, but does not
make the current parameter-level scorer a full learner continuation. The
checkpoint restore, passive-lineage, and manifest validation regressions pass;
no held-out panel was read and no approval was created.

The training-only proposal runner accepts a digest-valid parent checkpoint and
continues on disjoint training IDs after restoring the graph. Per-rule work
from the prior graph and the new native store is merged into a digest-bound v3
payload with per-capture identities; cumulative runtime counters and approval
events remain in the restored graph/resource record. Merge validation rejects
duplicate capture inputs and inconsistent totals. The resource accounting,
restored-probe, and candidate-action subset passes 16 tests. This makes later
generation execution possible after exact approval, but no additional
candidate was approved or adopted.

## Fresh Loopover generation-zero root (2026-10-23)

A training-only probe on independent Loopover v2 draws 0510/0511 ran with a
10,000-attempt ceiling per task and captured a generation-zero ancestor after
training search. Its full native graph, resource snapshot, and per-rule work
all pass their digest checks. The goals differ, the first task produced no
candidate, and the second produced one unapproved candidate without
independent-trial qualification. The root has complete measured resource
coverage, 20,000 reserved search attempts, 22 native rule steps, 101.925 s
elapsed, and 1,136,861,184 bytes process peak RSS. It has zero validation
worlds, approvals, or receipts; it establishes no learned generation or
efficacy.

- [`p22_generation_zero_root_loopover_0510_0511.json`](../../../evaluation/process_mastery/results/p22_generation_zero_root_loopover_0510_0511.json), SHA-256 `a22093e99013320e42fe50c27938121e3d22e8e5bcc931fbebcc9c914ecb510c`.

## Repeated-draw Loopover root diagnostic (2026-10-23)

A follow-up training-only run on distinct draws 0511/0512 emitted a
generation-zero root and one unqualified candidate (digest
`fb7e3d70756562027d9acb693ff8e97d4c7007eb25665e9eedc3504f21ef36f4`). Draw
0511 had already appeared in the preceding root diagnostic, so this result is
repeated development exposure, not an independent trial or a valid
preregistration allocation. It has no validation worlds, approvals, or
receipts. Its complete raw artifact is retained at
[`p22_candidate_root_loopover_0511_0512.json`](../../../evaluation/process_mastery/results/p22_candidate_root_loopover_0511_0512.json),
SHA-256 `235196b6f7b6c61bd37ed2a75b92d31b2c3a24dea7d48e287c3f79706c61c65f`.
The targeted checkpoint-continuation, resource-snapshot, exact candidate-action
and resource-accounting regressions pass (17 tests). The result does not
advance the lineage or resource-match gates.

## Native graph-backed checkpoint scoring (2026-10-23)

Strict scoring now reads the selected process parameters from the immutable
checkpoint graph and verifies that they agree with the checkpoint manifest.
It selects an active ProcessSchema for the generation-zero ancestor or passive
controls, and the approved adopted candidate for an invention descendant.
Unattested development fixtures retain their explicit fixture-only path. A
captured ancestor and its approved child were scored on the same
training-derived control world: the ancestor scored 0 and the adopted process
scored 1. The component-ablation regression now exercises this actual captured
lineage rather than hand-built permutation records. The prescribed P22.03
command passes 27 tests. This is a bounded expression-path dependence control,
not a held-out causal estimate; matched four-arm independent-goal evaluation
remains open.
