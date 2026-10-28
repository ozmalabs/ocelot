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
At that point the attestation reported `DEVELOPMENT_ONLY` with
`artifact_tree_dirty`; the later clean-source attestation is recorded below.

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

## Clean-source native attestation (2026-10-23)

The P16–P22 implementation/evidence bundle is committed as
`c94aa1c8649dedb4e13d84e85df38df3ca912e5f`. After a release rebuild,
`linear_p22_v1.provenance()` reports `ATTESTED` with no issues. The loaded
extension hash is
`5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07`; the
build-receipt hash is
`661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66`; the
P22 source-bundle hash is
`539131da9af055a94439aa17a4c6651fa3766707c74f775c13a4da32e1a760cd`. Runner
and analyzer self-checks pass with no held-out access. Source cleanliness is
now established for a future freeze, while missing approved lineages, complete
resource/approval measurements, and frozen wall-time records still prohibit
P22.E2/E3.

## Restored Loopover generation-zero continuation (2026-10-23)

The digest-valid root checkpoint from Loopover draws 0510/0511 was restored and
continued on fresh distinct-goal training draws 0513/0514. The restored
generation-zero checkpoint digest is unchanged, the saved native graph matches
the root snapshot, and cumulative resource/rule-work digests verify. The
continuation reached 30,000 total reserved attempts: the root had used 20,000,
leaving 10,000 for continuation. The first new task used that remainder; the
second task received no attempts. A single candidate remains unqualified
(qualification count 0). This record has no approval, receipt, validation
world, or held-out access. Cumulative counters report 228.641 s, 39 native
rule steps, 1,258,934,272 bytes peak RSS, and 30,000 search attempts.

The complete uncompressed JSON had SHA-256
`b5016774abcb656ec80152862812a2480192318360a973eed5a0cfc6ea0e2471`; it is
retained as deterministic gzip at
[`p22_loopover_generation1_training_0513_0514.json.gz`](../../../evaluation/process_mastery/results/p22_loopover_generation1_training_0513_0514.json.gz),
SHA-256 `60bf3c8022d446b9f7494b0d01e1a5c3e4bf8fcb189c8b6500192a5aa205de82`.
This verifies restored continuation and cumulative accounting, but creates no
generation-one child. It also shows that the root's remaining global search
budget was insufficient for two new tasks; a future root/continuation plan
must reserve the inherited budget for both tasks without silently resetting
the ceiling.

## Explicit cumulative cap continuation control (2026-10-23)

The training probe now accepts a bounded explicit graph-wide attempt ceiling
(30,000 default, at most 120,000), exposes it in the CLI, and records both the
inherited and requested ceiling. On restoration, it updates only the policy
limit; prior attempts remain charged. A follow-up on fresh distinct-goal draws
0515/0516 used inherited cap 30,000 and requested cap 100,000. Both tasks
received their full 10,000 attempts. Cumulative work is 40,000 attempts
(20,000 from the root plus 20,000 new), 335.909 s, 46 native rule steps, and
1,419,657,216 bytes peak RSS. One candidate remains unqualified (qualification
count 0), with no approval, receipt, validation, or held-out allocation. The
native resource and merged rule-work digests verify. Increasing the explicit
ceiling fixes the earlier second-task starvation but does not produce a
qualified child.

The complete JSON SHA-256 is
`cf3a092738de51da0b41822d3a86b124e7a10516b3da3e690e5544f66488b6bd`; it is
retained as deterministic gzip at
[`p22_loopover_generation1_training_0515_0516_cap100k.json.gz`](../../../evaluation/process_mastery/results/p22_loopover_generation1_training_0515_0516_cap100k.json.gz),
SHA-256 `bcda44aa9df03b6c36f6a54c24a3b56f6f265af62bd58c1a0548de8b5bddcab1`.
The cap control's continuation, ceiling rejection, and default-cap regressions
pass. This remains development-only negative qualification evidence.

## Restored native learner task path (2026-10-23)

`score_restored_checkpoint_task` boots an explicitly supplied learner profile,
restores the complete immutable checkpoint graph, and submits a fresh task into
the native process domain retained by that graph. It runs native rules to
quiescence or a declared round limit and reports task status, native rule
steps/rounds, and approval/receipt counts. A regression confirms that an
attested generation-zero checkpoint's process solves a non-identity task
through the native solver on a fresh graph. No approval or simulated action is
created. The adapter, ablation, and independent-improvement bundle passes 28
tests. This supplies a continuation execution primitive, not a complete
four-arm checkpoint comparison or efficacy result; no held-out allocation was
accessed.

## Registered-world continuation guard (2026-10-23)

The restored task evaluator now accepts only an exact `agent_view` from a
registered v2 training draw. It rejects held-out/validation splits and any
mutation to the world record before booting the learner. The restored native
domain receives the registered world’s visible held processes, checking
existing schemas for active status, parameter and digest agreement. The task
retains the registered training-world identity. The D4 regression confirms
native solving on draw 0015 and rejects the same draw's held-out view. The
28-test P22.03 bundle passes, as do runner and analyzer self-checks; neither
self-check accesses held-out data. This closes a split-provenance gap for the
single-task continuation primitive, not the complete four-arm checkpoint
comparison or its resource/effect gates.

## Common checkpoint panel with cumulative primitive ceiling (2026-10-23)

`compare_restored_checkpoint_panel` runs each named, digest-valid checkpoint
against every common registered v2 training world. Each cell uses a fresh
learner graph and the same hard native rule-step ceiling. Outcomes retain
native quiescence/budget exhaustion, per-rule work, runtime counters, resource
snapshots, and newly created approval/receipt counts. The comparator reports
ceiling equality separately from actual resource matching and cumulative
primitive-work equality. A D4 regression exercises four checkpoint identities
on one registered training world with zero new approvals or receipts. Those
checkpoint identities share one captured graph, so the fixture verifies
comparison plumbing only and supplies no distinct-arm or efficacy evidence.
The P22.03 adapter/ablation/estimand suite passes 29 tests.

### Compute-cap measurement correction (2026-10-23)

Audit showed that `run_rules(max_steps)` may report more progress than its
argument when a batch-safe rule performs multiple graph updates in one pass.
The comparator now calls this a rule-progress limit and retains detected
scheduler overruns. The separate cumulative primitive ceiling is applied via
the native SolverPolicy's per-task max_steps after subtracting the checkpoint's
recorded prior primitive work, then verified against the post-run native graph
resource snapshot. Equal ceilings remain budget controls, not proof of equal
realized resources or efficiency.

## Four-arm native checkpoint scoring diagnostic (2026-10-23)

The isolated four-arm development runner can opt into generation-zero
checkpoint capture. Each captured root includes the complete native graph,
resource snapshot, runtime counters, and digest-bound native rule-work. The
capture path requires isolated per-arm RSS and complete rule-work measurement.
On D4 training draw 0520, the four distinct policy graphs all solved the
training task and produced valid roots with no approvals or receipts. They were
restored separately and scored on registered training draw 0521. All four
solved 1/1 under the same cumulative primitive ceiling 30,000; each ended at
cumulative primitive work 2, with no approval or receipt added. Cumulative
native term evaluations were 4,363 unchanged, 4,363 invention-only, 5,713
adaptive-only, and 5,709 full.

The vectors are not resource matched. The scoring pass ran multiple fresh
learners inside one process, so it did not produce arm-isolated wall-time or
RSS measures; graph/resource fields and native work also differ. Efficiency is
therefore inadmissible. This selected one-world training diagnostic establishes
no effect or efficacy; draws 0520 and 0521 are consumed for development. The
root JSON is
[`p22_four_arm_checkpoint_roots_d4_0520.json`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_roots_d4_0520.json),
SHA-256 `bb88741136b5c2dc88daa33cdd0bbe6dbb94b261c45292b2cdef0b79c1661aee`.
The cumulative evaluation is deterministic gzip at
[`p22_four_arm_checkpoint_eval_d4_0521_cumulative.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_d4_0521_cumulative.json.gz),
raw SHA-256 `42f54ebdff262d011fba04684c71cd067d7709d612bf82ec6e6338deb38260d8`,
gzip SHA-256 `868dad46eb06d6e7c3665fbec61cd49558b0643b0de89909fc316874f7aba477`.
A preliminary same-allocation artifact with increment-only native counters is
retained at
[`p22_four_arm_checkpoint_eval_d4_0521.json`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_d4_0521.json)
(SHA-256 `cad103a69a9ccf12f0bb420ca85df3e530e1b2b88850a512b09ebb22d7940ae3`)
and superseded for cumulative accounting; it is not an independent rerun.

## Loopover checkpoint panel counterpart (2026-10-23)

The same isolated generation-zero capture and registered training-world panel
ran for Loopover v2. Four arm roots trained on draw 0520 were scored on the
common registered draw 0521. All four ended without solving; none added an
approval or receipt. Unchanged/adaptive-only cumulative primitive work was 2;
invention-only/full was 130, all below the common 30,000 ceiling. Digest-bound
native term evaluations were 15,661 unchanged, 18,011 adaptive-only, 34,110
invention-only, and 36,537 full. This shows the primitive-work vectors differ
in Loopover despite equal ceilings and common data. As with D4, the in-process
scoring panel lacks per-arm isolated RSS/wall-time, so resource matching and
efficiency remain false. The result is a selected single-world training
diagnostic with no efficacy claim; draws 0520/0521 are consumed.

The root artifact is
[`p22_four_arm_checkpoint_roots_loopover_0520.json`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_roots_loopover_0520.json),
SHA-256 `3cbcc409fb0572dc6cfb0cc3d013f0084c2ae21ab12e3705dca181bb9818e346`.
The cumulative panel is deterministic gzip at
[`p22_four_arm_checkpoint_eval_loopover_0521_cumulative.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_loopover_0521_cumulative.json.gz),
raw SHA-256 `d24d98ba20ed7497cfb7c1f51e386851b53164f6985349e6d882efae68d1ad51`,
gzip SHA-256 `b517c8ed698641017c2401ce17a7dc61244b1f43b1178247e9e2fd463cf742b5`.

## Isolated checkpoint resource-measurement refresh (2026-10-23)

Added `evaluation.process_mastery.p22_checkpoint_panel`, which verifies each
checkpoint and registered training view, starts a separate process for every
arm/world cell, and attaches isolated `perf_counter` wall time and `ru_maxrss`
peak memory to the cumulative native resource snapshot. The updated snapshot
is resealed and reverified. Both family panels now report every declared
contract dimension as measured with no measurement gaps, while still reporting
`resource_matched=false` and `efficiency_comparable=false` because actual
vectors differ.

D4 remains 1/1 in all arms at cumulative primitive work 2. Loopover remains
0/1 in all arms at cumulative primitive work 2/2/130/130 (unchanged,
adaptive-only, invention-only, full). Isolated wall time and RSS remain
arm-specific measurements; the in-process JSON artifacts above are retained
as preliminary diagnostics and the isolated outputs supersede them for
resource coverage. Isolated D4 output is
[`p22_four_arm_checkpoint_eval_d4_0521_isolated.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_d4_0521_isolated.json.gz),
compressed SHA-256 `11a838c6ca87d83b11808631c5510e38164597522f61d1a3bc8c968323ddbb6b`,
raw SHA-256 `264f379a6d5f63c2f8bfbd90f7ffed812a17451eabd762980d43837e81d9554e`.
Loopover output is
[`p22_four_arm_checkpoint_eval_loopover_0521_isolated.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_loopover_0521_isolated.json.gz),
compressed SHA-256 `4a83adddb30551a1664be1088e16d4690771414146f9d61397abf007698b7b0a`,
raw SHA-256 `844831e0c8c3d7c8c6b66d44e1959376be3d5e68ed9cdb6c4948fd0803bad27a`.
The isolated-runner provenance closure test and worker measurement/split
regressions pass; there are still no approved descendant checkpoints or
independent-goal efficacy data.

## Curriculum-path correction and expanded root panels (2026-10-23)

A path audit found that the first restored-checkpoint evaluator directly added
`SolveTask` for all arms, bypassing the native `ProcessCurriculumPolicy` in
adaptive checkpoints. The earlier scores above are retained as preliminary
records and superseded for outcome validity. The evaluator now submits the
same `ProcessCurriculumEvidence` to every arm and allows enabled native
curriculum rules to select and dispatch the task. Fresh corrected isolated
panels on training draw 0521 score D4 at 1/1 in each arm and Loopover at 0/1
in each arm. All resource dimensions and native-work digests verify; resources
remain unmatched and no approvals or receipts were added. See the exact
corrected raw artifacts and hashes in the P22 build-plan record.

The corrected evaluator then scored the same generation-zero roots on common
training draws 0522–0533 in each family. Every arm solved 4/12 D4 worlds and
1/12 Loopover worlds; all paired score differences across the four root arms
were zero. All worlds were retained, complete resource coverage was measured,
all resource/work digests verified, and the primitive ceilings held. Some
arm/world cells used different cumulative primitive work and the realized
resource vectors were not matched. No approval or receipt was added. These
are multi-world baseline-development diagnostics only: they contain no
approved descendants, do not measure learning across generations, and support
neither efficiency nor efficacy claims. Corrected gzip artifacts are
[`p22_four_arm_checkpoint_eval_d4_0522_0533.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_d4_0522_0533.json.gz)
and
[`p22_four_arm_checkpoint_eval_loopover_0522_0533.json.gz`](../../../evaluation/process_mastery/results/p22_four_arm_checkpoint_eval_loopover_0522_0533.json.gz);
the build plan records compressed and decompressed SHA-256 digests. Draws
0520–0533 are consumed for development, and no validation or held-out worlds
were accessed.

The resource audit found complete measurement coverage with no unavailable
dimensions, but realized treatment work differs. Median cumulative term
evaluations by arm were 4,280 / 7,684 / 37,546 / 41,023 on D4 and
23,015 / 28,637 / 41,516 / 47,069 on Loopover (unchanged, adaptive-only,
invention-only, full). Median primitive work was 2 / 2 / 198 / 198 on D4 and
3 / 3 / 131 / 131 on Loopover. Captured cumulative wall time and process peak
RSS also vary by arm. Fixed ceilings were respected, but efficiency remains
inadmissible under the frozen matching rule. The build-plan ledger records
the per-family wall-time/RSS ranges; no post-hoc work padding or ceiling
change is allowed to manufacture a resource match.

## Native held-out runner repair (2026-10-23)

Code review found that the frozen P22 runner still used the expression-only
checkpoint scorer, despite P22.03 requiring restored learner evaluation. The
runner now restores each digest-bound checkpoint in a fresh worker and gives
the native solver the same externally assigned answer-free task. Such a task
is marked evaluation-only and is excluded from training-exposure data and
counts. The analyzer now requires a native learner/task outcome, respects the
primitive and rule-progress ceilings, and records zero approvals and receipts;
worker failures remain rows and invalidate the panel. The standalone freeze
must be committed and verified before the runner constructs any registered
held-out world. The focused P22 bundle passes 50 tests, and runner/analyzer
self-checks pass without held-out access. This repairs the scoring consumer
path; no registered held-out world has been read, no preregistration has been
frozen, and approved descendant lineages remain absent.

## Isolated wall-time scope correction (2026-10-23)

The first worker timer began after native learner boot. It now starts before
boot, so the per-cell wall-time snapshot includes boot, restore, and scoring
(Python process import/startup remains outside that interval). Earlier
isolated panels retain valid scores, RSS and work digests, but their
worker-wall-time values omit boot and are superseded for timing only. A
controlled-delay regression confirms the updated interval is digest-bound.
Fresh D4 and Loopover panels on training draws 0546–0549 each scored 1/4 in
every arm. All 32 arm/world outcomes completed, resource/work digests
verified, ceilings held, and no approvals or receipts were added. The values
remain unmatched and the roots are generation zero, so no efficiency or
efficacy claim follows. Exact artifact hashes and per-arm timing/resource
medians are recorded in the build plan.

## Matched-resource claim gate (2026-10-23)

A final analyzer audit found that score thresholds alone could mark the
registered phase `PASS` even when measured paired resources differed. The
contract says such outcomes support capability observations only. The
analyzer now separates score-threshold success from resource matching and
requires complete all-arm, all-generation, all-world matching across
`MATCHED_RESOURCE_FIELDS` for a registered phase pass; wall time remains a
separately reported outcome. A synthetic held-out regression supplies score-threshold success
with one resource mismatch and verifies `NOT_ESTABLISHED` / `CAPABILITY_ONLY`.
The focused P22 suite passes 53 tests; runner and analyzer self-checks pass.
No registered held-out allocation was accessed. This tightens claim
classification and does not create approved lineages or efficacy evidence.

## D4 candidate-specific adoption and generation-one checkpoint (2026-10-23)

The reviewer approved only expression digest
`badd1251ee4eb9c779233a3631b307d68ec6e34da40daeb993f8c0be0641d255` and
reported 12 seconds of review. The guarded CLI reconstructed candidate `#1089`
from distinct training draws 0406/0407, verified its binding, consumed one
human approval (`#6708`), executed one guarded transition on training world
`p22:d4-v2:train:0406`, and verified receipt `#6710`. The observed state was
`[2,0,3,1]`. It captured generation-one checkpoint
`p22-d4-g1-badd1251ee4e` with digest
`f3d6c15ac7f9187cef0e4c7ca21f3615958955565101a891fbc8796c997e6ed6`, linked
to generation-zero digest
`e80842b7932ce9bbcc326254c6844caf64ec6fc0ac8600d62f89d5f088ca52cf`.
Independent validation confirms both immutable digests, the parent link, and
consecutive generation numbering. Cumulative primitive work increased from
47,676 to 47,677. The artifact contains no validation worlds and its SHA-256
is `7435894f1b65c8c62d0d7b401f0db73f1513372ee24f66dd2c01b552aafcab9b`.

The candidate-specific authorization is exhausted. It permits no later
generation, Loopover action, preregistration, or held-out allocation. This is
one D4 lineage edge only and does not establish learning efficacy or satisfy
the cross-family three-generation panel. The first integrated rerun produced
95 passing tests and two failures caused by CLI tests that assumed the fixed
one-shot result path remained unused. Those tests now create temporary
request-bound paths. The complete affected P22 bundle passes 97 tests in
286.89 seconds. Runner and analyzer self-checks pass, and no held-out world
was accessed.

## Post-approval candidate development probes (2026-10-23)

Fresh Loopover training draws 0550/0551 exhausted 5,000 attempts per request
without a candidate (`NO_CANDIDATE_FIRST_TRIAL`). Draws 0552/0553 at 10,000
attempts per request produced candidate `#20764` (digest
`412a124b06f87edc4c98076398f57877ea75416399cef105cabff411f852671e`) on the
second task, with no qualification. Draws 0554/0555 produced a different
unqualified candidate (digest
`c3454b7f307e9df1b8b4389355bd9db5c88f14e11003060e2fe05edba1732d40`). A
restored generation-zero continuation from the 0552/0553 graph on distinct
draws 0556/0557 again left `#20764` unqualified: attempts on both goals were
residual. The four training-only artifacts have SHA-256 values, respectively,
`b5460060d8497cfe12bcfb0bdf3962254ce9f430a0efad364c3a10d8c7ecdacf`,
`f37e818b9fea0ec389ed44d8bf49bd336c786dcd599f45833daee74309135e38`,
`cc71cfdc1fc2b93b46cb8141c589ca08cc47d167675886e6dc85f78c5bb2eab5`, and
`3f6b36166863b27cca30744963056a6dd0968cabbe89a699a6ae64112c439c06`.
All four used distinct training goals, had empty validation allocations, and
created no approval or world receipt. Draws 0550–0557 are consumed development
data; none produced an approval-ready Loopover candidate.

A separate continuation restored the approved D4 generation-one graph and
searched distinct training draws 0560/0561 at 10,000 attempts per request.
It completed without validation access or a new action. The graph reports the
parent's one historical approval and receipt; no new approval, receipt, or
generation-two checkpoint was created. New candidates remained unqualified
on both task outcomes. The raw artifact
[`p22_d4_generation2_training_0560_0561.json`](../../../evaluation/process_mastery/results/p22_d4_generation2_training_0560_0561.json)
has SHA-256
`504e01786e2f141eede6f0d664cf39c87c33e44132ef5daf69d52b9c2ccf1158`.
Draws 0560/0561 are consumed for development. The one-action D4 authorization
is exhausted, so any later generation requires a new candidate-specific
approval.

## D4 generation-two candidate and restored-parent approval path (2026-10-23)

A second D4 continuation from the same generation-one checkpoint on fresh
distinct training draws 0562/0563 produced candidate `#6731`, digest
`1e3590935d290140171bd81f966a1dcc336e72278231d844b6411f7a2286f9b4`. Its
native qualification records witnesses on both draws, but its exact effect is
the identity permutation `[[0,1,2,3]]`. It is therefore a qualified but
non-improving candidate; no adoption, approval, receipt, or generation-two
checkpoint was created. The graph's one approval and receipt are inherited
from the generation-one parent. The training-only probe artifact has SHA-256
`f068f8ab759f78c3d38bfe994f8c0c9c65a1fadf530b09804450dbba0594a27a`.

The candidate's exact request is recorded in
[`COGNITION_P22_APPROVAL_REQUEST_D4_0562_0563.md`](COGNITION_P22_APPROVAL_REQUEST_D4_0562_0563.md).
It asks for one identity-effect transition and conditional generation-two
checkpoint only, and states that the result cannot count as improvement. The
machine binding fixes the generation-one parent artifact SHA-256, checkpoint
digest, training trials, and search ceilings. The guarded CLI now loads that
parent record from its hashed artifact, verifies its complete checkpoint
digest and graph snapshot, and refuses any changed parent or ceilings before
claiming the one-shot output. A negative-digest CLI probe confirms the parent
is loaded and verified before rejection; the target output remains unclaimed.

The Loopover continuation of the 0554/0555 root on fresh draws 0564/0565 also
left its candidate unqualified, with no approval or receipt. Its artifact
[`p22_candidate_continuation_loopover_0564_0565.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_loopover_0564_0565.json)
has SHA-256 `5d1b41f73548634f8074652a0c1ae0300b71542d4c72970cf94eaebe1b976e15`.
No validation worlds were accessed. A further fresh Loopover pair 0566/0567
produced one candidate, digest
`72450d51db7b385f4fff8d68e3989a512873b9c52b88b76a52e28f6fc9c14ae5`, but it
remained unqualified with residual outcomes, no approval, and no receipt. Its
raw artifact
[`p22_candidate_probe_loopover_0566_0567.json`](../../../evaluation/process_mastery/results/p22_candidate_probe_loopover_0566_0567.json)
has SHA-256 `c792a40b44f0cfe9e30ec325d17d2ed235b1a9dbf7e4158f8e3a20845193543d`.
Draws 0564–0567 are consumed training-only development data.

## D4 identity candidate action (2026-10-23)

The exact candidate `#6731` was approved with digest
`1e3590935d290140171bd81f966a1dcc336e72278231d844b6411f7a2286f9b4` and
reviewer-reported review time of 12 seconds. The one-shot CLI verified the
request hash and restored generation-one parent before consuming human
approval `#16727`. It performed exactly one guarded transition on training draw
0562 and returned verified receipt `#16730`; the observed state remained
`[0,1,2,3]`, matching the candidate's identity effect. The conditional child
checkpoint `p22-d4-g2-1e3590935d29` is generation 2, digest
`5799cb611c33a58de30c2590bbaa5f294794f0a9f9705707454072645bb694fc`, and links
to parent digest
`f3d6c15ac7f9187cef0e4c7ca21f3615958955565101a891fbc8796c997e6ed6`.
Cumulative primitive work is 107,073. The raw result
[`p22_approved_candidate_d4_0562_0563.json`](../../../evaluation/process_mastery/results/p22_approved_candidate_d4_0562_0563.json)
has SHA-256 `8c6e6392c47a7f9fb8f212df0bc747df3a88a02fc8d190358e0841082d41bd25`
and remains outside version control. This authorized action extends the D4
lineage by one generation but cannot count as improvement. No validation or
held-out world was accessed, and this approval authorizes no further action.

## D4 generation-two continuation (2026-10-23)

An attempted pair on draws 0570/0571 was rejected by the distinct-goal
preflight because both generated the same goal. The rejection occurred before
learner boot or native search and is preserved in
[`p22_candidate_continuation_d4_0570_0571_preflight.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_d4_0570_0571_preflight.json),
SHA-256 `54d73db5463edca2133111a5b4f367a1299c1b1cb79b087d42d37684329d47ac`.
Those draws are not reused.

The digest-valid generation-two D4 checkpoint was restored for distinct
training draws 0572/0573. The graph ceiling was explicitly raised from the
inherited 60,000 to 120,000 without resetting the parent's 15,946 reserved
attempts; although the probe requested a 10,000 per-request ceiling and
measured native rule work, inspection found restored requests still used the
parent's 5,000 cap. Both tasks terminalized stuck after 5,000 attempts each.
Three candidate records were present, but none qualified on the new training goals. The two
approvals and receipts in the graph are inherited from the parent; no new
approval, action, receipt, validation world or held-out world was created.
Artifact [`p22_candidate_continuation_d4_0572_0573.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_d4_0572_0573.json)
has SHA-256 `e8cf05934a774824fbfbcce73d246b285717a155235a291f08beec74f6efe018`.
The D4 generation-two lineage therefore has no generation-three candidate
from this pair. Draws 0570–0573 are consumed training-only development data.

A second fresh pair 0574/0575 requested 20,000 attempts per request from the
same parent. It exposed the same restored-policy bug: both new requests still
had the inherited 5,000 maximum, both tasks ended stuck, and four candidates
were recorded without qualification on either new goal. Raw artifact
[`p22_candidate_continuation_d4_0574_0575.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_d4_0574_0575.json)
has SHA-256 `69cbf546dfd86f6783200b782519e0d981f3d1c7ffb5463026ca31d0cd4e82a7`.
These two continuations are ceiling-censored diagnostics, not evidence against
the higher requested budgets. The continuation code now reapplies the bound
per-request ceiling after restoring the checkpoint, reports each native
request's actual `max_attempts`, and has a regression proving a restored
request takes the new ceiling. That regression passes. A fresh pair 0576/0577
is running under the corrected code; it uses no validation or held-out worlds.

## High-ceiling Loopover generation-zero probe (2026-10-23)

A fresh distinct-goal Loopover probe on draws 0568/0569 completed at a
30,000-attempt per-request ceiling (90,000 global ceiling). It recorded one
candidate, `#30830`, digest
`20db63f2bf032030ffc2293e3361aeb58d4b7a9e3d887f4b34429054ba475da8`; the
candidate had zero independent-goal qualification witnesses. Both tasks
terminalized stuck after 30,000 attempts, and the runner returned
`NO_CANDIDATE_FIRST_TRIAL` because the first training task produced no
candidate. No approval, receipt, validation or held-out world was created.
The raw artifact
[`p22_candidate_probe_loopover_0568_0569.json`](../../../evaluation/process_mastery/results/p22_candidate_probe_loopover_0568_0569.json)
has SHA-256 `f7a3312131002cd7dead4b469fb56e5f68a2887361e7709ebe2346a8ec968fd1`.
This higher-ceiling fresh pair still provides no qualified Loopover
generation-one candidate. Draws 0568/0569 are consumed training-only data.

## Corrected-ceiling D4 generation-two continuation (2026-10-23)

After fixing the restored per-request ceiling, the D4 generation-two parent was
continued on fresh distinct draws 0576/0577. The result confirms the requested
and actual limits now agree: both requests used `max_attempts=20,000` and
exhausted that limit, with both tasks stuck. Three candidate records were
present; candidate `#16750` (`flip_r` composed with the identity, digest
`75c8a4559ab843b8154bc031dab1f527d18f39595e9fc9f0c6f3c0b9d7a63b73`) had only
residual trials on the new draws, and no candidate qualified across them.
Approval/receipt totals of two are inherited from the generation-two parent;
there was no new approval, transition or receipt, and no validation/held-out
access. The raw artifact
[`p22_candidate_continuation_d4_0576_0577.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_d4_0576_0577.json)
has SHA-256 `e2a9013ad48fa3cc2acc6a7c8e41d174ea92635a9732e0b367b0fe598705a49a`.
The generation-three candidate gate remains unmet. A further D4 pair 0582/0583
is running at the 30,000 per-request ceiling; Loopover 0580/0581 is also in
progress.

The fresh Loopover pair 0580/0581 completed with actual per-request ceilings
of 10,000 and 10,000 global attempts, both tasks stuck. It produced one
candidate `#10761`, digest
`9d2cca990f4676eb687009efb1b7f3eb425e9e95903549a021ff0ccad454b6ef`, with
zero independent-goal qualification witnesses; its recorded attempts on the
second training goal were all residual. There was no approval, receipt,
validation or held-out access. The raw artifact
[`p22_candidate_probe_loopover_0580_0581.json`](../../../evaluation/process_mastery/results/p22_candidate_probe_loopover_0580_0581.json)
has SHA-256 `3bed527bf1fcc1ec9e1a9638672dd3e6c42e78f06a7c29e62b9bcd49dc53ead7`.
Draws 0580/0581 are consumed training-only data. A fresh Loopover pair
0584/0585 is running at a 30,000 per-request ceiling.

## Interrupted Loopover probes (2026-10-23)

The final polling cell for probes 0584/0585 and 0586/0587 was interrupted.
The subsequent PID audit found both probe processes absent and neither native
result artifact had been written. Their candidate and completion outcomes are
unknown, so they are not counted as completed attempts or qualification
failures. To preserve the split and prevent accidental reuse, the two expected
output paths now contain explicit interruption records:
[`p22_candidate_probe_loopover_0584_0585.json`](../../../evaluation/process_mastery/results/p22_candidate_probe_loopover_0584_0585.json),
SHA-256 `9df712c64c3e41ea1f6593e7012c1576b6c2b5d936d7ad28d47207c06d701094`,
and
[`p22_candidate_probe_loopover_0586_0587.json`](../../../evaluation/process_mastery/results/p22_candidate_probe_loopover_0586_0587.json),
SHA-256 `039310b9e6729540bb3c9ed4cdd1bca76e0510def97e8784a992293afb8ad950`.
Both were training-only, had empty validation allocations, and used no
approval flags. Draws 0584–0587 are consumed but provide no candidate result.
The independent D4 0582/0583 process (PID 899940) was still live at the audit
and remains under observation.

The D4 0582/0583 continuation has since completed. Both restored requests used
the actual 30,000-attempt per-request limit and both tasks ended stuck. Three
candidate records were present; the fresh candidate `#25875` (digest
`760c713b16dc2c1fc5e360ff77879a56395bfde2603a593080afcf3090950952`,
`rot90` composed with `flip_r`) had only residual trials on draw 0583. No
candidate qualified across the two new goals. Approval and receipt totals of
two are inherited from the generation-two parent; no new approval, action or
receipt occurred. Validation and held-out allocations were empty. Raw artifact
[`p22_candidate_continuation_d4_0582_0583.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_d4_0582_0583.json)
has SHA-256 `203bb0f1a2ee146f1cc7bb9a1a6d21f5f64c028332f6a6b4a1b98831ca8dbb5a`.
The D4 generation-three candidate gate remains unmet. Draws 0582/0583 are
consumed training-only data.

## Higher-ceiling Loopover development search (2026-10-23)

Fresh distinct training draws 0588/0589 used 30,000 attempts per request and
exhausted the 60,000 global attempt ceiling. Both tasks ended stuck. Candidate
`#30761` (digest
`7beebaba165b6774992cda6c44b046f093060678fd0c0832fb86408bbcb23c2c`) had no
independent-goal witness on draw 0588 and only residual trials on draw 0589;
the global cap stopped further search. No approval or receipt was created,
and validation and held-out allocations were empty. Raw artifact
[`p22_candidate_probe_loopover_0588_0589.json`](../../../evaluation/process_mastery/results/p22_candidate_probe_loopover_0588_0589.json)
has SHA-256 `d4f3ff9c27b91e87d6753defd6ef3c0ad3c3bde9992fa1a67eefcfce06d4d13f`.
Draws 0588/0589 are consumed training-only data. This adds no Loopover
generation-one candidate.

## Maximum-global-ceiling Loopover development search (2026-10-23)

Fresh distinct training draws 0590/0591 used 30,000 attempts per request and
the runner's maximum 120,000 global ceiling. Both tasks ended stuck. Candidate
`#827` (digest
`1bb67071f24bbd2cbc45b8ed55951b166d5a1496aaa044ad030f938550b38a07`) had no
qualified independent-goal trial; its 24 recorded second-goal trials were
residual despite funded requests. No approval or receipt was created, and
validation and held-out allocations were empty. Raw artifact
[`p22_candidate_probe_loopover_0590_0591.json`](../../../evaluation/process_mastery/results/p22_candidate_probe_loopover_0590_0591.json)
has SHA-256 `615cff996516b940a387fbfccc69766d61128b13e172c4b4dffc64b7c736bbc5`.
Draws 0590/0591 are consumed training-only data. This adds no Loopover
generation-one candidate.

## Maximum-ceiling D4 generation-two continuation (2026-10-23)

The digest-valid parent checkpoint `p22-d4-g2-1e3590935d29` (generation 2,
digest `5799cb611c33a58de30c2590bbaa5f294794f0a9f9705707454072645bb694fc`)
was restored on fresh distinct training draws 0592/0593. The continuation
raised the graph-wide ceiling from 60,000 to 120,000; both new requests used
30,000 attempts and both tasks ended stuck. Four candidate records were
present. Candidate `#16769` (digest
`a54ed68b85a26c7caad1c3ac3fff9f2a122b145643c34a5a5f75358d3ac8da42`) had
mixed verified and residual trials on draw 0593 but no qualification across
both new goals. Approval and receipt totals of two are inherited from the
parent; there was no new action or receipt. Validation and held-out
allocations were empty. Raw artifact
[`p22_candidate_continuation_d4_0592_0593.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_d4_0592_0593.json)
has SHA-256 `4ec2ad7a3c50eeb24e93d5bc86b49c1136e5bbda9989cce914baf795753747a0`.
Draws 0592/0593 are consumed training-only data. The D4 generation-three
candidate gate remains unmet.

## Loopover higher-tick development diagnostic (2026-10-23)

Fresh distinct training draws 0596/0597 used 60 rule-processing ticks (twice
the earlier 30-tick setting), 30,000 attempts per request and the 120,000
global ceiling. Both tasks ended stuck. Candidate `#30761` (digest
`76608f5df8181234dc6fa45b57f2155a838269edc96bf5dcfce9f368da688681`) remained
unqualified; its 24 funded trials on draw 0597 were all residual. No approval
or receipt was created, and validation and held-out allocations were empty.
Raw artifact
[`p22_candidate_probe_loopover_0596_0597.json`](../../../evaluation/process_mastery/results/p22_candidate_probe_loopover_0596_0597.json)
has SHA-256 `c7796ed1acf60d1b7614fbb24f1c66e707790ab3ec8e43f9c8fad2e20f347901`.
Draws 0596/0597 are consumed training-only data. Loopover still has no
approved generation-one descendant.

## Repeated Loopover higher-tick development diagnostic (2026-10-23)

A second fresh distinct Loopover pair, draws 0602/0603, used 60
rule-processing ticks, 30,000 attempts per request and a 120,000 global
ceiling. Both tasks ended stuck. Candidate `#30761` (digest
`e12f3bd35e6d7df28b8faba319cdc9ee4a2cc8d903ed11a08ba916061ff41615`) had 24
funded but residual trials on the second goal; it did not qualify across the
two goals. No approval or receipt was created, and validation and held-out
allocations were empty. Raw artifact
[`p22_candidate_probe_loopover_0602_0603.json`](../../../evaluation/process_mastery/results/p22_candidate_probe_loopover_0602_0603.json)
has SHA-256 `c56d7a14a7547fd98432cddc3d784b2e3ee7d753539d3f048d9c0ed7c7b522ce`.
Draws 0602/0603 are consumed training-only data. This reproduces the 0596/0597
higher-tick result and adds no Loopover generation-one candidate.

## Multi-goal Loopover training panel (2026-10-23)

The development probe and CLI now accept 2–8 training draws. Distinct-goal
mode validates pairwise uniqueness across the full panel; same-goal mode
validates the target across every task. The focused P22 development and CLI
regression bundle passes 18 tests, including multi-goal execution and
duplicate-goal rejection.

A fresh four-goal Loopover panel on draws 0609–0612 used 20,000 attempts per
request and an overall ceiling of 120,000. All four tasks ended stuck and
exactly 80,000 attempts were reserved. Candidate `#20761` (digest
`511a61ca014c0f64f432bfc01eaceb66179fde572f76efbbe9912c3cf829324b`) was
tested on each of the three later goals, producing 72 residual trials and no
qualification across the panel. No approval or receipt was created, and
validation and held-out allocations were empty. Raw artifact
[`p22_training_panel_loopover_0609_0612.json`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0609_0612.json)
has SHA-256 `4a210aad83c838104b197d626306cbdad23f19f96625531e1dd5e9b9ee64186f`.
Draws 0609–0612 are consumed training-only data. This does not create an
approved Loopover generation-one descendant.

## Eight-goal Loopover qualification panel (2026-10-23)

Eight fresh pairwise-distinct Loopover training goals, draws 0613–0620, were
run with 10,000 attempts per request and an 80,000 global ceiling. The full
ceiling was reserved; all eight tasks remained stuck. Candidate `#10761`
(digest
`8928e5557188ed65ab42e5bebe3bca73b9d8a2724dddb022dbb0e0cbb7623104`) was
tested 24 times on each of the seven later goals. All 168 candidate trials
were residual and no qualification was created. No approval or receipt was
created, and validation and held-out allocations were empty. Raw artifact
[`p22_training_panel_loopover_0613_0620.json`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0613_0620.json)
has SHA-256 `9e6b079b60ded36688ff7bb34eafa1fc695d0a6726c7f7815f9931a7f58acdf8`.
Draws 0613–0620 are consumed training-only data. This does not provide a
Loopover generation-one descendant or a registered efficacy estimate.

## Reproducible training-only continuation CLI (2026-10-23)

The development CLI now accepts a parent result artifact, a checkpoint record
path and an exact checkpoint digest as a separate training-only continuation
binding. It verifies that the artifact is repository-local, binds its SHA-256
and the checkpoint identity into the output, requires distinct training goals
with no validation worlds, and rejects any combination with candidate
approval flags. The affected CLI tests and `tests/test_p22_development.py`
pass 16 tests.

An end-to-end low-budget smoke restored D4 checkpoint
`p22-d4-g2-1e3590935d29` on draws 0600/0601. The one-attempt global limit was
already consumed by the restored graph, so both new requests created zero
attempts; approval and receipt totals remained the parent's two each, with no
validation or held-out access. This verifies source binding and restoration,
not search efficacy. Raw smoke artifact
[`p22_candidate_continuation_cli_smoke_d4_0600_0601.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_cli_smoke_d4_0600_0601.json)
has SHA-256 `979c16de4d5242aae0678ea95dbb35cd0a8926c575b34933f9ed19cc28bac850`.

The first smoke pair 0598/0599 was rejected before learner boot because both
draws generated the same goal. It created no search attempts, approvals,
receipts, validation or held-out exposures. Its explicit consumed-draw record
[`p22_candidate_continuation_cli_preflight_d4_0598_0599.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_cli_preflight_d4_0598_0599.json)
has SHA-256 `89aa8390bf9a071039f60539e73384506655bb67bca124d375999be7962e7667`.

## Repeated D4 generation-two continuation (2026-10-23)

The same digest-valid generation-two parent was restored on fresh distinct
training draws 0594/0595 at the 120,000 global and 30,000 per-request ceilings.
Both tasks ended stuck. Three candidate records were present; candidate
`#16750` (digest
`b904536f49cf9b86ecca03c09449b15934ccf097d3a9978782ef5e07b3dc379c`) had an
identity effect and residual trials only on draw 0595. No candidate qualified
across both new goals. The two approvals and receipts are inherited from the
generation-two parent; no new action or receipt occurred. Validation and
held-out allocations were empty. Raw artifact
[`p22_candidate_continuation_d4_0594_0595.json`](../../../evaluation/process_mastery/results/p22_candidate_continuation_d4_0594_0595.json)
has SHA-256 `a7c07f4b99314644737ce3d577384de52bab5300c782de127f1b3a06b311a119`.
Draws 0594/0595 are consumed training-only data. The D4 generation-three
candidate gate remains unmet.

The focused `tests/test_p22_development.py` and
`tests/test_run_p22_development_probe_cli.py` suites pass: 15 tests in
228.48 seconds. The P22 runner self-check passes and reports
`heldout_accessed=false`; its lineage-tamper controls reject the mutated
fixtures. The analyzer self-check passes all nine negative and positive
controls, including missing/partial/mismatched resource sources. These checks
do not interpret any continuation as an efficacy result.

## D4 five-goal generation-two continuation (2026-10-23)

The first fresh set, draws 0629–0634, failed the distinct-goal preflight because
0629 and 0632 both generated `[2,0,3,1]`. It stopped before learner boot and
reserved zero search attempts. Its explicit consumed-draw record is
[`p22_training_panel_preflight_d4_0629_0634.json`](../../../evaluation/process_mastery/results/p22_training_panel_preflight_d4_0629_0634.json),
SHA-256 `83233e380a974db74b956ff2dff471632ebea8bad887f2adaaa6f041dd393581`.

The next five fresh draws, 0635–0639, generated five distinct D4 goals. The
runner restored parent checkpoint `p22-d4-g2-1e3590935d29` (generation 2,
digest `5799cb611c33a58de30c2590bbaa5f294794f0a9f9705707454072645bb694fc`)
and reserved 10,000 attempts for each task, 50,000 total, under the 120,000
global ceiling. All five tasks ended stuck. Candidate `#26693`, digest
`211bacf1856f917926bfff4811ff2e08d76d3f0deac3d803a898a2d5c02cc958`, has
effect `[[1,0,3,2]]` and qualified twice: qualification `#66758` on draws
0635/0637 and `#66759` on 0635/0638. The second qualification is not included
in the pending candidate-specific approval.

No new approval or receipt was created; totals of two each are inherited from
the parent. Validation and held-out allocations are empty. Raw result
[`p22_training_panel_continuation_d4_0635_0639.json`](../../../evaluation/process_mastery/results/p22_training_panel_continuation_d4_0635_0639.json)
has SHA-256 `da014e9efc9e9522d15920bc5bb131424963269f359accab7e663086316fa81a`.
The exact request
[`COGNITION_P22_APPROVAL_REQUEST_D4_0635_0639.md`](COGNITION_P22_APPROVAL_REQUEST_D4_0635_0639.md)
binds qualification `#66758`, its two training witnesses, the complete
candidate expression and effect, the parent artifact/checkpoint digests, and
the one-shot output path. It is awaiting explicit user approval and reviewer
seconds. The proposed transition is non-identity, but it is only a lineage
action and is not efficacy evidence.

The adoption verifier previously required exactly one qualification record
for a candidate, which rejected candidates with multiple valid independent
goal pairs. It now accepts an exact `qualification_id` and checks only that
record's witness keys; ambiguous approvals without that identifier still
fail closed. Unit regressions cover explicit selection, ambiguity, and
witness mismatch. The focused development and CLI regression suite passed: 20 tests in 213.80 seconds, including the existing single-qualification guarded-adoption path and the new ambiguous-qualification controls.

## Loopover eight-goal follow-up (2026-10-23)

Eight fresh pairwise-distinct Loopover training goals, draws 0643–0650, used
10,000 attempts per task and exhausted the full 80,000-attempt global ceiling.
All eight tasks ended stuck. Candidate `#10761` (digest
`2e4d1ba7cfa4eecbea8cf59ab4ac1f7d3f3a5544cd473216ccf3ec7cf4156986`) had no
qualification and produced 24 residual independent-goal trials on each of the
seven later goals, 168 total. No approval or receipt was created; validation
and held-out allocations were empty. Raw result
[`p22_training_panel_loopover_0643_0650.json`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0643_0650.json)
has SHA-256 `a2a9d36048c23c86a552c4f9058d3d81fd67c44a6f8c21d9d3f64f681073c51f`.
Draws 0643–0650 are consumed. Loopover still has no generation-one
descendant or registered efficacy estimate.

## Loopover eight-goal 60-tick diagnostic (2026-10-23)

Fresh distinct goals 0651–0658 were searched with 60 rule-processing ticks,
10,000 attempts per task, and the full 80,000-attempt global ceiling. The
runner returned `NO_CANDIDATE_FIRST_TRIAL`: two candidates were minted, but
neither received an independent-goal trial. Both remained unqualified. No
approval, receipt, validation, or held-out access occurred. Raw artifact
[`p22_training_panel_loopover_0651_0658_ticks60.json`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0651_0658_ticks60.json)
has SHA-256 `81c9bbba9773c2742e8becd0f6eda5c4b2c1bcb48ee7b624a33d26c01378f138`.
Draws 0651–0658 are consumed. Increasing rule-processing ticks did not
produce a Loopover generation-one candidate.

## Loopover same-world checkpoint panel (2026-10-23)

The registered generation-zero `unchanged`, `adaptive_only`, `invention_only`,
and `full` checkpoints were restored in isolated workers and scored on four
fresh training worlds, draws 0659–0662. All cells used the same world IDs and
30,000 cumulative primitive-work / 20,000 native-rule-progress ceilings.
Every arm solved 1/4 worlds. Budget compliance and all contract resource
measurements passed, but observed resource matching did not: actual cumulative
primitive work differed on three of four worlds, and budget, search,
curriculum, graph-size, rule-step and runtime costs also varied. The evaluator
returned `resource_matched=false` and `efficiency_comparable=false`; this
panel is development-only, not an efficacy estimate. Raw artifact
[`p22_checkpoint_panel_loopover_0659_0662.json`](../../../evaluation/process_mastery/results/p22_checkpoint_panel_loopover_0659_0662.json)
has SHA-256 `a326b1ad58f874a74e8a7c25825dd0011d903378e9ce5fe8cbed40c1483cafac`.
The run had no held-out access.

## D4 same-world checkpoint panel (2026-10-23)

The four generation-zero D4 arm checkpoints were restored in isolated workers
and scored on fresh training draws 0664–0667 under common 30,000 cumulative
primitive-work and 20,000 native-rule-progress ceilings. Every arm scored
identically on every world and solved 3/4. All budgets were respected and all
resource dimensions were measured, but actual resource matching failed on draw
0665: full and invention each used 206 cumulative primitive units while
unchanged and adaptive used 2. The panel therefore reports
`resource_matched=false` and `efficiency_comparable=false`; it is development
evidence, not an efficacy estimate. Raw artifact
[`p22_checkpoint_panel_d4_0664_0667.json`](../../../evaluation/process_mastery/results/p22_checkpoint_panel_d4_0664_0667.json)
has SHA-256 `0fdca8d7ad50d9bbb2fd9dd29a3687785062df2d5d5a9fb9a1245902f4f159d6`.
No held-out data was accessed.

## D4 frozen lineage checkpoint comparison (2026-10-23)

The exact generation-one parent `p22-d4-g1-badd1251ee4e` and generation-two
child `p22-d4-g2-1e3590935d29` were scored on four fresh pairwise-distinct
D4 training goals (draws 0668, 0669, 0670, 0672). The first pass exposed that
the restored child could continue its in-checkpoint open-process search and
exceed the 120,000 cumulative primitive ceiling on two cells. Both invalid
records remain preserved at
[`p22_lineage_pair_d4_0668_0672.json`](../../../evaluation/process_mastery/results/p22_lineage_pair_d4_0668_0672.json)
(SHA-256 `58bac3ecb82c57257835128e367a27f84da129b400e3f01ee7fd1ad3f85e9dd0`)
and
[`p22_lineage_pair_d4_0668_0672_budget_guard_v2.json`](../../../evaluation/process_mastery/results/p22_lineage_pair_d4_0668_0672_budget_guard_v2.json)
(SHA-256 `a51cc590efcefa63dd5ef25b5620858f30c59f0fd481c96b61f529b34f47f9d4`).

The corrected `p22_frozen_process_scoring_v1` profile enables the same native
solver/schema executor for each checkpoint and turns off checkpoint-side
search, adoption, independent-improvement, and curriculum policies. The native
solver now checks the selected process's declared primitive cost against the
remaining ceiling before changing task state. The corrected run kept every
cell within budget and scored both checkpoints at 2/4, with identical
per-world scores `[1,0,1,0]`. Cumulative primitive totals were 47,678/47,678/
47,678/47,677 for the parent and 107,075/107,075/107,075/107,074 for the
child; the difference reflects accumulated lineage work. This records no
observed score gain and is not an efficiency comparison. Raw corrected result
[`p22_lineage_pair_d4_0668_0672_frozen_v3.json`](../../../evaluation/process_mastery/results/p22_lineage_pair_d4_0668_0672_frozen_v3.json)
has SHA-256 `bafa4acc05af36bb927ea9258ab208c6b275f5a29c235ff6eb7e1b3bcb1253eb`.
No validation or held-out world was accessed.

## Loopover four-goal, 30,000-attempt qualification panel (2026-10-23)

Four fresh, pairwise-distinct Loopover training goals 0673–0676 each received
30,000 search attempts, exhausting the 120,000 graph-wide ceiling. All four
tasks ended stuck. Candidate `#30761` (digest
`b87a67e14b59e7ce250f5d6a23d44ddbd338b9e14bfae8bab8fbb8c8b43317a0`) had 24
residual independent-goal trials on each of the three later goals, 72 total,
and remained unqualified. The larger per-goal allocation did not produce a
generation-one candidate. There were zero approvals, receipts, validation
worlds or held-out exposures. Resource measurements report 50 native rule
steps, 1,008.78 seconds, peak RSS 6,359,154,688 bytes, 120,774 graph nodes,
599,054 edges and 1,347 training-data payload bytes.

The raw JSON SHA-256 is
`7b6ee08a094a1e1eea1c2d49cc8023f4ba9f1f2be2bf5f9566f53b8a9e7957d7`; the
decompressed content of the deterministic gzip artifact
[`p22_training_panel_loopover_0673_0676_p30k.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0673_0676_p30k.json.gz)
matches that hash. The gzip SHA-256 is
`ed95e7c721311197e59d3788a89d02952b75870a4ba764437e90cc3ca4c99b53`. Draws
0673–0676 are consumed training-only evidence. This panel adds no candidate
authorization, efficacy or held-out result.

## Two-held-process candidate transfer extension (2026-10-23)

The native search grammar now tests a digest-attested candidate followed by
two held processes on a distinct training task, preserving both source schema
digests, the nested expression tree, composed parameters, finite effect
fingerprint and cumulative declared work. The rule applies only to stuck
training tasks and uses the shared global and per-request attempt counters. A
focused four-element regression generated and verified the expression on a
second distinct training goal. The search/qualification/CLI suite passed 44
tests; the arm/checkpoint/profile suite passed 93 tests.

On fresh Loopover v2 training goals 0680/0681, each task received 10,000
attempts (20,000 total). Both tasks ended stuck. Candidate `#10761` (digest
`586f9baa5497dd7a205f5d6a23d44ddbd338b9e14bfae8bab8fbb8c8b43317a0`) had 156
residual independent-goal trials on the second goal: 24 from the existing
one-step rule and 132 from the new two-step rule. It did not qualify. The run
took 334.859 seconds, with 26 native rule steps, 1,105,047,552 bytes peak RSS,
20,768 nodes, 101,008 edges and 2,982,288,403 native term evaluations. There
were zero approvals, receipts, validation worlds or held-out exposures.

Raw JSON SHA-256 is
`f3bd632aba0dc9c41defbc98a8b0e897a5ae0e048ca2bef4173ee10142402aa3`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0680_0681_two_step.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0680_0681_two_step.json.gz)
has SHA-256 `815fab0a70752e6144e2e0121df3b5c5c3fba860757947a909b30c726efbec78`
and decompresses to that raw digest. Draws 0680/0681 are consumed
training-only data. Search coverage increased, but Loopover qualification
remains unmet.

## Eight-goal two-held-process qualification panel (2026-10-23)

The two-held-process search ran on eight fresh pairwise-distinct Loopover v2
training goals, draws 0682–0689, using transfer depth 2, 10,000 attempts per
task and an 80,000 global ceiling. All eight tasks ended stuck after using
their full allocations. Candidate `#10761` (digest
`896b9d0e7ee618bc93ae007b16a0e0db777574f230e2708c0d0a3725a028ff38`, effect
`[[0,1,7,3,4,5,2,6,8]]`) produced 156 residual trials on each of the seven
later goals: 24 one-step and 132 two-step, 1,092 residual trials total. It did
not qualify. Search reservations matched the 80,000 ceiling. There were no new
approvals or receipts, no validation allocation, and no held-out exposure.

The run took 2,008.991 seconds, with 104 native rule steps, 4,099,854,336
bytes peak RSS, 80,786 graph nodes, 402,562 edges and 17,197,490,299 native
term evaluations. Raw JSON SHA-256 is
`8a393b22267e07cd7934cf14ea1a31f4b80bd7779c1ef44fe0bdcb16f89cac6b`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0682_0689_two_step.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0682_0689_two_step.json.gz)
has SHA-256 `999070499e348746c11799e98e7cff1ef879d099fc64718641412812aac0aa2e`
and decompresses to the raw digest. Draws 0682–0689 are consumed training-only
data. The larger panel still produced no Loopover generation-one candidate or
efficacy result.

## Alternate-source proposal probe (2026-10-23)

Fresh pairwise-distinct Loopover training draws 0690/0691 used transfer depth
2 and 10,000 attempts per task. Both tasks remained stuck; the source task on
draw 0690 produced no candidate (`NO_CANDIDATE_FIRST_TRIAL`). The probe
reserved 20,000 attempts, created no approval or receipt, and accessed no
validation or held-out worlds. Runtime was 138.517 seconds, with 21 native
rule steps, 1,040,207,872 bytes peak RSS, 20,765 graph nodes, 100,713 edges
and 1,273,376,617 native term evaluations.

Raw JSON SHA-256 is
`db28bf9ff5ba62600e5ea170762e9204579130dbde44c029a1c05bf939bf1f13`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0690_0691_two_step.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0690_0691_two_step.json.gz)
has SHA-256 `704c76b31f3a49da352d1184a4ff438669f71830dd0358857a0a92972609b59c`
and decompresses to that raw digest. Draws 0690/0691 are consumed. This is a
proposal-generation miss, not a qualification failure or efficacy result.

## Rotated-source transfer probe (2026-10-23)

Fresh pairwise-distinct Loopover training goals 0692/0693 used transfer depth
2 and 10,000 attempts per task. Both tasks remained stuck. The source task
produced candidate `#10761` (digest
`1c0be6708dc57d66c495808d5b13e3a6615ea3c7f3df4b57f11b0718a14a5d15`, effect
`[[6,7,5,0,1,8,3,4,2]]`), but its 24 one-step and 132 two-step trials on the
second goal were all residual. It did not qualify. The run reserved 20,000
attempts and created no approval or receipt; validation and held-out worlds
were not accessed.

Runtime was 334.002 seconds, with 26 native rule steps, 1,047,445,504 bytes
peak RSS, 20,768 graph nodes, 101,008 edges and 2,996,940,314 native term
evaluations. Raw JSON SHA-256 is
`ab0127077c6e137770b236dc600dcbbcccdb3e516b590497d9158fedb7c3b3fa`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0692_0693_two_step.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0692_0693_two_step.json.gz)
has SHA-256 `37276ef26615c1dd50a0d7919e0a81b753ac61e727dd9afc4d784f255595929d`
and decompresses to that raw digest. Draws 0692/0693 are consumed
training-only data; the rotated source produced a different candidate but no
qualified Loopover descendant.

## Second rotated-source transfer probe (2026-10-23)

Fresh pairwise-distinct Loopover training goals 0694/0695 used transfer depth
2 and 10,000 attempts per task. Both tasks remained stuck. Candidate `#10761`
(digest `ec771adfec77c25484a4d94ef870b5980d35b1ca5a76fc5c543f02ca2fc93c89`,
effect `[[1,8,2,3,4,5,6,7,0]]`) had 24 residual one-step and 132 residual
two-step trials on the second goal; it did not qualify. The run reserved
20,000 attempts, created no approvals or receipts, and accessed no validation
or held-out worlds.

Runtime was 339.686 seconds, with 26 native rule steps, 1,047,400,448 bytes
peak RSS, 20,768 graph nodes, 101,008 edges and 2,996,267,572 native term
evaluations. Raw JSON SHA-256 is
`ef819f5161fe2c04124b766c4fcbaae1140f94c17619ca4314f225194ce6fc2c`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0694_0695_two_step.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0694_0695_two_step.json.gz)
has SHA-256 `1c691650d8d3a3886dfb3ba42e01a9fa074c95d6fc92d51cbdfd49c46b8aac8d`
and decompresses to that raw digest. Draws 0694/0695 are consumed. This new
source expression also failed to qualify on its independent training goal.

## Ordered two-held-process proposal panel (2026-10-23)

The transfer grammar now includes the candidate-first, candidate-middle and
candidate-last orderings around two held processes. A fresh four-goal
pairwise-distinct Loopover panel on draws 0696–0699 used transfer depth 2,
10,000 attempts per task and a 40,000 global ceiling. All tasks ended stuck.
The first task produced no candidate; candidate `#20764` (digest
`642521f05b9b9d32ce35c60d8a211d1e541f58e144ff7d4b6dd7c99719e0c48c`, effect
`[[0,5,3,4,7,8,6,1,2]]`) was minted later and received no independent-goal
trials. The run is `NO_CANDIDATE_FIRST_TRIAL`, not a transfer qualification
failure. It created no approvals or receipts and accessed no validation or
held-out worlds.

Runtime was 213.217 seconds, with 43 native rule steps, 2,042,884,096 bytes
peak RSS, 40,774 graph nodes, 200,662 edges and 2,553,665,815 native term
evaluations. Raw JSON SHA-256 is
`fe8d3040e1c5a60d61fd4c5a6b09e8a080a529e8d68599317e73fc859bc5f442`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0696_0699_ordered_two_step.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0696_0699_ordered_two_step.json.gz)
has SHA-256 `0ad9d02dc75dab2aab41336502bc516e2db7edebc8e31c53e6c20b832e34e35c`
and decompresses to that raw digest. Draws 0696–0699 are consumed. This panel
does not exercise candidate transfer in the additional orderings.

## Order-complete two-held-process transfer probe (2026-10-23)

Native search now covers candidate-first, candidate-middle and candidate-last
placements around two held processes. Bounded graph tests verify all three
orderings against exact finite effects. The combined search/development/CLI
suite passes 48 tests; the arm/checkpoint/profile suite passes 93.

On fresh pairwise-distinct Loopover training draws 0700/0701, candidate
`#10761` (digest
`7042a5a6d5d8d2512e5709a4bbc853a777ec915fe9e3c1df0295740c571fdd93`, effect
`[[2,0,1,4,5,3,7,8,6]]`) had 24 one-step and 396 two-step trials on the
independent goal. The two-step trials cover all three orderings; all 420
attempts were residual, with no qualification. Both tasks were stuck after
10,000 attempts each. There were no approvals, receipts, validation worlds or
held-out exposures.

Runtime was 690.952 seconds, with 28 native rule steps, 1,054,629,888 bytes
peak RSS, 20,768 graph nodes, 101,536 edges and 8,401,352,553 native term
evaluations. Raw JSON SHA-256 is
`6fb4a0f514d54037ce4449e897504bc59e3fa422d3dffbef00b2aeeb12d5dfb2`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0700_0701_ordered_two_step.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0700_0701_ordered_two_step.json.gz)
has SHA-256 `f7f34eddd98af40ca222fafcbdb0cd666a7f67ed0c56b0154705cf30a7865aa7`
and decompresses to that raw digest. Draws 0700/0701 are consumed
training-only evidence. The expanded composition orders are exercised but do
not produce a qualified Loopover descendant.

## Four-goal order-complete transfer follow-up

On fresh pairwise-distinct Loopover training draws 0702–0705, candidate
`#10761` (digest
`7b545b5edd49897aaa0388f297c582f160aae19b51fb4bc9144e5ec54bf177e5`, effect
`[[0,1,3,4,5,8,2,6,7]]`) received 24 one-step and 396 two-step trials on
each of the three later goals. All 1,260 trials were residual and none
qualified. All four tasks remained stuck after 10,000 attempts each; the run
reserved 40,000 attempts total. There were no approvals, receipts, validation
worlds, or held-out exposures.

Runtime was 1,972.488 seconds, with 58 native rule steps, 2,204,278,784 bytes
peak RSS, 40,774 graph nodes, 203,110 edges, and 23,797,065,371 native term
evaluations. Raw JSON SHA-256 is
`8e841ee9cc5813deb92dd427eeba2720e8066db94dcf0f25aaf7e8b00e2a5813`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0702_0705_ordered_two_step.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0702_0705_ordered_two_step.json.gz)
has SHA-256 `02a926896a211ddf270dff8eb7b0ee24523fda1db14eac8a5d5915ddfe318101`
and decompresses to that raw digest. Draws 0702–0705 are consumed training
evidence. The larger panel still produced no qualified Loopover descendant or
efficacy estimate; P22.E2–E3 remain open.

## Four-goal order-complete transfer replication

Fresh pairwise-distinct Loopover training draws 0706–0709 each reserved
10,000 attempts, 40,000 total. All four tasks ended stuck. Candidate `#10761`
(digest `66a45a72d8556d656eaeef1c239f6242302f37f0dc98ca48ebdbb29ae27c7db6`,
effect `[[7,2,0,3,1,5,4,8,6]]`) received 24 one-step and 396 two-step trials
on each of the three later goals. All 1,260 trials were residual and none
qualified. There were no approvals, receipts, validation worlds, or held-out
exposures.

The result snapshot records 40,773 graph nodes, 203,108 edges, 61,624,419
serialized graph bytes and 27,360,206 native graph-memory bytes. Raw JSON
SHA-256 is
`2df324d46aa81e067f2f2f08073e3712d62ab627de6d805fc8ce694101066144`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0706_0709_ordered_two_step.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0706_0709_ordered_two_step.json.gz)
has SHA-256 `8e2681213134d9b8c8eaf548252cba388745072aef96ede9fed8e98f1a2e528a`
and decompresses to the raw digest. Draws 0706–0709 are consumed training
evidence. The replication still produced no qualified Loopover descendant or
efficacy estimate; P22.E2–E3 remain open.

## D4 generation-two continuation qualification

A distinct-goal continuation preflight on draws 0710–0713 was rejected before
learner boot because draws 0710 and 0713 generated the same goal; no search or
candidate action occurred. On fresh distinct draws 0718–0721, the verified
generation-two parent `p22-d4-g2-1e3590935d29` (digest
`5799cb611c33a58de30c2590bbaa5f294794f0a9f9705707454072645bb694fc`) produced
candidate `#16750` (digest
`75c8a4559ab843b8154bc031dab1f527d18f39595e9fc9f0c6f3c0b9d7a63b73`, effect
`[[2,3,0,1]]`). It qualified on three independent-goal pairs: 0718/0719
(`#56758`), 0718/0720 (`#56759`), and 0718/0721 (`#56760`). Of 306 recorded
trials, 48 were verified and 258 residual. All four tasks ended stuck.

The continuation recorded 55,946 search attempts, 165 native rule steps,
416.280 seconds, peak RSS 1,300,021,248 bytes, 56,761 graph nodes, 256,306
edges and 3,804,368,537 native term evaluations. Approval and receipt counts
of two are inherited from the parent; this run created none and accessed no
validation or held-out worlds. Raw JSON SHA-256 is
`f3b1bf771b45e2d1c9d73eaa9efd667f8c0f7f670cbfbb82f1c4e6f94099d614`; the
deterministic gzip artifact
[`p22_training_panel_continuation_d4_0718_0721.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_continuation_d4_0718_0721.json.gz)
has SHA-256 `8a08579df5bcff5be800a44ab529cff6358f8a05025e4429dfbd8e1c3abb1313`
and decompresses to the raw digest. Draws 0718–0721 are consumed training
evidence. The qualified candidate has not been adopted and creates no
generation-three checkpoint or improvement result.

Candidate `#16750` supersedes the earlier unapproved `#26693` request because
it qualified on three independent-goal pairs rather than two. The
candidate-specific request for `#16750` is recorded in
[`COGNITION_P22_APPROVAL_REQUEST_D4_0718_0721.md`](COGNITION_P22_APPROVAL_REQUEST_D4_0718_0721.md);
the prior request is marked superseded. No adoption has been performed.

The exact generation-two parent and 0718–0721 training draws were replayed
without approval flags before submission. Candidate `#16750`, qualification
`#56758`, and witnesses 0718/0719 reproduced exactly; the replay added no
approval or receipt and used no validation worlds. Compressed replay SHA-256
is `db3a6176f5e0e29ecb3eec8da184db62f38e40706a343fc86048f2ff25d57647`
(raw SHA-256 `21738f213e8c269b8db67b0a797b0fea6d3eeda37f24ed3b828ad1e0c4f95746`).

## Three-held-process Loopover transfer result

The native search seed now supports a training-only transfer depth of three:
a digest-attested candidate composed with three held processes. Four rules
cover every position of the candidate while the graph matcher enumerates the
held-process bindings. The focused native search/development/CLI bundle passes
49 tests, including exact finite effects for all four positions. The P22
arm/checkpoint/profile bundle passes 93 tests. Runtime provenance at commit
`77e4343e6b24642b357f12be932712c6dea7b983` is `ATTESTED`, with matching build
sources, verified native binding, and no issues; the source-bundle digest is
`eef27325ad6ab9508fcab710697dbb54cfda17b471c84fee0fad2cffa50c0b89`.

On fresh pairwise-distinct Loopover training draws 0722–0725, candidate
`#10761` (digest
`4e818dbce301c1699cf22dafe914e489d7423d3becc60575d44fa9875a5132e4`, effect
`[[1,2,6,0,4,5,8,3,7]]`) received 132 two-held and 5,280 three-held trials on
each of the three later goals. All 16,236 trials were residual; none
qualified. All four tasks remained stuck after 10,000 attempts each, exactly
reserving 40,000 globally. There were no approvals, receipts, validation
worlds, or held-out exposures.

Runtime was 1,387.363 seconds, with 55 native rule steps, peak RSS
2,469,576,704 bytes, 40,774 graph nodes, 248,974 edges, 74,961,131 serialized
graph bytes, 27,360,601 native graph-memory bytes, and 13,579,431,373 native
term evaluations. Raw JSON SHA-256 is
`5c92372bf4c3f878aad260d70f83aa6191b4fc72b83e4281448250110fe94cfe`; the
deterministic gzip artifact
[`p22_training_panel_loopover_0722_0725_three_held.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0722_0725_three_held.json.gz)
has SHA-256 `1c306200f3e0a0a348af96894e9ca24931ffdffd181fb243995ad445f35d3988`
and decompresses to the raw digest. Draws 0722–0725 are consumed training
evidence. This grammar expansion still produces no qualified Loopover
descendant or efficacy estimate; P22.E2–E3 remain open.

After this seed change, the D4 generation-three request was replayed from its
exact parent with its bound depth of two. It still reconstructs candidate
`#16750`, qualification `#56758`, and witnesses 0718/0719 exactly; inherited
approval and receipt totals remain unchanged and validation is empty. The
compressed replay SHA-256 is
`8404827040182163d3960b2ab9d236ca1730355ecebfa0348f3096533f7c7a8e`
(raw SHA-256 `84d0efc1d930a652aed709d5010f8c492cc8193b430ceb0eea7aa852fc44addb`).


## Registered full-arm D4 continuation (2026-10-24)

The preflight on D4 draws 0973–0976 rejected duplicate goals before learner
boot; it reserved no search attempts (raw SHA-256
`92b9e39c2f35c176decd0a8757927fe9b2b53b014786cd34c3ec479713c63705`). A
fresh pairwise-distinct panel on draws 0977–0980 restored the registered full
generation-zero parent `fa79f67d5ea71d15f5b70f43efd2c2047af3c84b9258b25c61a0d97d84bf8b7b`.
It completed with four candidates, zero approvals or receipts, and empty
validation and held-out lists. The raw result is
[`p22_training_panel_registered_root_full_d4_0977_0980_novel.json`](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_full_d4_0977_0980_novel.json),
SHA-256 `3848a3633e1314c331a2df8ed9b7df7503963f87a507d5addcbd0646db8da7e7`.

Candidate `#1539` (`inverse:rot90`, digest
`77425927da7e05d5dbc469dc97dd15b3c52eeec9b29bf192d7b7f5758cf9c3c3`)
qualified on the independent training goals 0977 and 0979 (`#11860`). Its
recorded effect `[[1,3,0,2]]` equals active root process `rot90`, so the
candidate fails the novelty criterion and received no approval packet.
Derived candidate `#6121` did not qualify. This search adds no checkpoint
descendant or improvement evidence.

## Unchanged-arm passive checkpoint descendants (2026-10-24)

Restored the registered unchanged generation-zero checkpoint for D4 and
Loopover and captured generation-one through generation-three checkpoints with
`capture_passive_checkpoint`. Independent validation confirms all six
checkpoint digests, resource snapshots, family root hashes, process digests,
parameters and sequential parent links. Each declares zero added primitive
work and carries no approval or receipt. The raw artifact is
[`p22_passive_unchanged_lineages_0520.json`](../../../evaluation/process_mastery/results/p22_passive_unchanged_lineages_0520.json),
SHA-256 `98f2494659a73b3de2bfc8a61bab25f97182e17cd30c162fa8a821f1bc77b0c9`.
These captures are structural no-op controls and have no new training
exposures. They do not satisfy adaptive-only descendant requirements or the
resource-matched development gate; no held-out worlds were accessed.


## Training-exposed passive control descendants (2026-10-24)

The unchanged and adaptive-only roots in each family were restored and
advanced across the same preregistered training draws 0600–0602. The runner
used a 10-unit primitive-work ceiling for each new unchanged-arm solver task;
adaptive-only curriculum remained enabled and invention stayed disabled. All
six curriculum tasks completed. The unchanged arm solved D4 0600/0601, ended
stuck on 0602, and ended stuck on all three Loopover tasks.

The resulting 12 generation-one through generation-three checkpoints have
valid resource snapshots, exact sequential parent links and unchanged root
process expressions. There were zero approvals and world receipts, and no
validation or held-out worlds were accessed. The artifact is
[`p22_passive_control_training_lineages_0600_0602.json`](../../../evaluation/process_mastery/results/p22_passive_control_training_lineages_0600_0602.json),
SHA-256 `11478f6b590f5923464c7ec2f1b4f04c0c9dd2bdbd601f02bf9c00905ed2d0b3`.
All six unchanged/adaptive cumulative checkpoint resource snapshot pairs
miss exact matching; native rule work, training exposure counts and training
data bytes differ. A common-world scoring panel has not yet measured per-world
resource matching for these descendants. This is partial lineage evidence and
does not satisfy the P22 resource-match gate.

## Registered full-root D4 repeat qualification panel (2026-10-24)

Fresh training draws 0981–0984 restored the registered full-arm g0 checkpoint
`fa79f67d5ea71d15f5b70f43efd2c2047af3c84b9258b25c61a0d97d84bf8b7b`. All
four tasks remained stuck after 9,208 reserved attempts. Candidate `#1867`
(digest
`84854777d0e3b48f447ecd04236a794eff39a46546edb3f19e47f506492ce66a`) repeats
the expression previously recorded as `#9396`; its six independent-goal
trials on 0982–0984 were residual, with no qualification. There were no
approvals, receipts, validation worlds, or held-out accesses. The raw artifact
[`p22_training_panel_registered_root_full_d4_0981_0984_novel.json`](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_full_d4_0981_0984_novel.json)
has SHA-256
`7a81a117072460372b0d6003a36c1665c86ba9ac8497c2987f25601426689048`.

## Registered full-root D4 candidate request (2026-10-24)

On distinct training draws 0985–0988 with 60 search ticks, candidate `#1541`
(`power2:rot90`, digest
`15ab127dc160101ea078c7eea5b91b5339bc4ca6a73a20048c5facb27656b651`, effect
`[[3,2,1,0]]`) qualified on pairs 0985/0986 (`#12259`) and 0985/0987
(`#12260`). The selected 0985/0986 transfer child `#4022` has effect
`[[0,2,1,3]]`; both effects differ from the full root's active `rot90` and
`flip_r`. Exact replay reproduced the candidate and both qualifications.
Source and replay results had zero approvals or receipts and empty validation
and held-out allocations. Raw SHA-256 values are
`8adab01214d86cbde56c2eca1d92ea0ce0b201f82373d94043d4c6c4b2e2f083` and
`b91b3dfcf59c234f0c91f8ce01c54607c972d7d13f68411f5f1df11181d72d24`.
The [candidate-specific full-arm D4 request](COGNITION_P22_APPROVAL_REQUEST_D4_FULL_0985_0986.md)
binds qualification `#12259` and the registered full-arm generation-zero
parent to one training transition and conditional g1 checkpoint. It awaits
exact user approval. No transition or checkpoint was created.

The full-root approval packet now binds a replay captured with complete native
rule-work identity coverage; its candidate, qualification records, and witness
pairs match the uninstrumented source panel. The CLI regression checks both
artifact hashes, the full-root parent, selected witness pair, source/child
novelty, zero action evidence, and the unused output path. The focused CLI
module passes 10 tests. No adoption was executed.


## Passive-control common-world scoring and resource match (2026-10-24)

The 12 unchanged/adaptive-only descendants were scored in isolated native
learners on the same unused training worlds 0603–0606 for each family. The
common ceilings were 120,000 cumulative primitive work and 20,000 native rule
progress. All 48 rows completed within both ceilings; no approval, receipt,
validation, or held-out access occurred. D4 scored 2/4 for each control arm at
each generation. Loopover scored 0/4 for each arm/generation. These are
selected development outcomes and do not establish efficacy.

None of the 24 per-world unchanged/adaptive resource pairs matched exactly.
Differences included native rule steps and term evaluations, training
exposures and bytes, retrieval/proposal/verification/refinement work, budget
spent, graph bytes/memory, and peak RSS. The 48-row panel is
[`p22_control_descendant_resource_panel_0603_0606.json`](../../../evaluation/process_mastery/results/p22_control_descendant_resource_panel_0603_0606.json),
SHA-256 `047eee711378c306e342f251f5f6aa33a7c344a952bbe3071d565cb3702d2c5d`.
It contains only two arms; exact four-arm resource matching remains untested
and the P22 freeze gate remains closed.

## Identity effects excluded from native improvement qualification (2026-10-24)

A D4 full-arm g1 continuation on fresh distinct training draws 0830–0833
qualified source candidate `#9440` (effect `[[1,0,3,2]]`), while its selected
transfer trial derived child `#12379` with identity effect `[[0,1,2,3]]`. The
historical artifact remains preserved; no approval or action was created. This
candidate cannot count as an improving descendant.

The qualification rule previously checked whether source and transfer effects
were active or approved-adopted, but identity could pass when the domain had no
identity process installed. Permutation domains now carry a domain-bound
`identity_effect_digest`; native qualification requires source and transfer
child effects to differ from it. New and restored P22 domains populate that
fingerprint. The generator and checked-in seed are synchronized. A regression
covers an identity transfer without an installed identity process.

Verification: `tests/test_independent_improvement.py
 tests/test_p22_development.py tests/test_run_p22_development_probe_cli.py` —
43 passed. Diagnostic raw SHA-256:
`4461debc542c0bd3de79e61b8812057cdeb7588c1d28ec74fe5bd192158aab5c`. No new
approval, receipt, validation, or held-out access occurred. The guard repair
creates no descendant and establishes no efficacy result.

## Identity effects excluded from native improvement qualification (2026-10-24)

A D4 full-arm g1 continuation on fresh distinct training draws 0830–0833
qualified source candidate `#9440` (effect `[[1,0,3,2]]`), while its selected
transfer trial derived child `#12379` with identity effect `[[0,1,2,3]]`. The
historical artifact remains preserved; no approval or action was created. This
candidate cannot count as an improving descendant.

The qualification rule previously checked whether source and transfer effects
were active or approved-adopted, but identity could pass when the domain had no
identity process installed. Permutation domains now carry a domain-bound
`identity_effect_digest`; native qualification requires source and transfer
child effects to differ from it. New and restored P22 domains populate that
fingerprint. The generator and checked-in seed are synchronized. A regression
covers an identity transfer without an installed identity process.

Verification: `tests/test_independent_improvement.py
 tests/test_p22_development.py tests/test_run_p22_development_probe_cli.py` —
43 passed. Diagnostic raw SHA-256:
`4461debc542c0bd3de79e61b8812057cdeb7588c1d28ec74fe5bd192158aab5c`. No new
approval, receipt, validation, or held-out access occurred. The guard repair
creates no descendant and establishes no efficacy result.

## D4 full-arm generation-one continuation under the identity guard (2026-10-24)

From parent checkpoint `p22-d4-g1-15ab127dc160` (digest
`e83c1fb3b84f589b8ca400b4b39fa03d8c04528aba262adc3b53a4c1eeca9af9`), fresh
training goals 0002/0003 qualified candidate `#9440` (digest
`2d2cb9ecda29351e1d0f513498eb6089c0f48b2dc1f8ee8650ebb2bbf39cdc46`) as
qualification `#32385` with witnesses 0988/0003. Its selected transfer child
`#22382` has non-identity effect `[[3,1,2,0]]`. The exact training-only replay
reproduced the source candidate, qualification, witnesses, and child digest.

The source reserved 30,811 attempts, recorded 170 native rule steps, 619.116
seconds wall-time and 937,930,752-byte peak RSS. Native rule identity coverage
is complete with no unresolved rules. Source and replay raw hashes are
`b30b06795498887643b1c325372cf2e90086e0fbb654455ba7d24f0286334792` and
`6a73de04a148a0f4b6c319342b043dd70f3caeadf5f46523a4137c0f90b21594`.
They inherit one approval/receipt, add none, and contain no validation or
held-out allocation. The candidate-specific [request](COGNITION_P22_APPROVAL_REQUEST_D4_FULL_G1_0002_0003.md)
binds one proposed action on training draw 0002 to the exact parent and replay;
it remains unapproved.

## D4 invention-only generation-two post-guard continuation (2026-10-24)

On fresh distinct training draws 0004/0005 from checkpoint
`p22-d4-g2-84854777d0e3`, each task used 10,000 additional attempts and
remained stuck. The identity candidate `#25873` remained in the artifact but
received zero native qualifications under the repaired guard; its identity
transfer child `#56760` also received zero. Candidate `#9459` had a missing
qualification kind and was excluded. No improving generation-three candidate
was found.

The panel added 20,000 attempts and brought cumulative reserved attempts to
64,280. It recorded 226 native rule steps, 3,628.322 seconds wall-time, and
3,130,404,864-byte peak RSS. Raw artifact SHA-256
`5c6f85a29afc5d72d21fdea84f2c182d1af6a3f215169ad0f1197a48c92a2469`, resource
snapshot SHA-256
`809b6718fab6d77acb7a1281372cfdba08f1167599ee573a08424b2bf1fbb98b`, and
native-rule-work SHA-256
`79519697f192951e6482e62ff85114c70dfe0e6b00dbca84a9baf3244d975ca6`
(complete identity coverage, no unresolved rules). It inherits two approvals
and receipts, adds none, and has no validation or held-out allocation.

## Loopover invention-only generation-one continuation (2026-10-24)

Continued from checkpoint `p22-loopover-g1-2638da0f23ae` (digest
`c91670f7a91ba3d9f958f865dc85c4d4596d852a8a97c0e99e1f8d3d7b925057`) on
fresh distinct training goals 0006/0007. Each task used 10,000 new attempts and
remained stuck. Candidates `#16551`, `#21555`, and `#31572` received zero
independent-goal qualifications; no approval-eligible candidate resulted.

The run recorded 76 native rule steps, 1,479.115 seconds wall-time,
2,028,687,360-byte peak RSS, and 40,000 cumulative reserved attempts. Raw
artifact SHA-256
`873a947db4155d2bd76eb3ca788f091193311c606b926f016f8c2d69bb656994`, resource
snapshot SHA-256
`f1c5d78a0ab297829b6824951194697900ca1d070525b3d990412ae56b3abe1f`, and
native-rule-work SHA-256
`104ebf9249f67611192b1d133a69d40e9e16648bc6f49f4c8e541dc3518ae5db`
(complete identity coverage, no unresolved rules). It inherits one approval and
receipt, adds none, and has no validation or held-out allocation.

## Loopover invention-only g1 continuation detail

The 0006/0007 run produced three candidates (`#16551`, `#21555`, `#31572`),
with zero qualifications. Each new task used 10,000 attempts and ended stuck.
No approval or receipt was added; validation and held-out allocations are
empty. The measured run and provenance hashes are recorded in the build plan
and capability assessment.

## Loopover invention-only generation-one higher-ceiling continuation (2026-10-24)

On fresh distinct training draws 0008/0009, the per-request cap was raised to
20,000. Both tasks remained stuck. Candidates `#16551`, `#21555`, and `#61575`
received zero independent-goal qualifications. The run reserved 40,000 new
attempts and reached 60,000 cumulative attempts; it recorded 72 native rule
steps, 475.228 seconds wall-time and 2,029,527,040-byte peak RSS.

Raw artifact SHA-256
`5c38cd3528105ede92cb7270bea100fb4728746a3662260509433d42d009f99f`, resource
snapshot SHA-256
`840622b7be7feceb2f03c84a25ada5d0e79fab7e852925e8152ea01463d8c75b`, and
native-rule-work SHA-256
`5d5b650e086b6b04cf663f1e0ce15ca5f27c5027f904c96e6798cadb3f8e9d15`
(complete identity coverage, no unresolved rules). One approval and receipt
are inherited; no new action, validation, or held-out allocation occurred.

## Loopover invention-only generation-one 30,000-attempt continuation

On fresh distinct goals 0010/0011, both tasks used 30,000 attempts and ended
stuck. Candidates `#16551`, `#21555`, and `#51572` received zero
independent-goal qualifications. The continuation reserved 60,000 new
attempts, bringing the branch total to 80,000; it recorded 76 native rule
steps, 1,516.177 seconds wall-time and 2,029,036,544-byte peak RSS.

Raw artifact SHA-256
`d62900c64cd62432609f7b4eb37261825f6ea26ec6df932bb778348a7e69209a`, resource
snapshot SHA-256
`4e93010e1ee3b158c716ef6354f85004e076b4d8f7575784bfa65e84e3eb4886`, and
native-rule-work SHA-256
`53750fdf767df6857b50cb7386be84a5a08a727ad1530f51e6dae44cdcc676ba`
(complete identity coverage, no unresolved rules). One approval and receipt
are inherited; no new action or held-out allocation occurred.

## Loopover invention-only g1 maximum cumulative panel

Four fresh distinct goals 0016–0019 were searched at 25,000 attempts each,
reaching the 120,000 cumulative ceiling. All tasks remained stuck; candidates
`#16551`, `#21555`, `#71575`, `#96579`, and `#121583` had zero
independent-goal qualifications. The run recorded 95 native rule steps,
871.714 seconds wall-time and 2,029,412,352-byte peak RSS. There was one
inherited approval/receipt and no new action, validation, or held-out access.

Raw artifact SHA-256
`a7481175d53701789a94d0573eb9ea203aa8390ad29bef050f2767a001445238`, resource
snapshot SHA-256
`8df416ef8603affe313dcfeaf60a42370e5ba143ab19cae20cc6535bae634776`, and
native-rule-work SHA-256
`8b1fac6b3604a9d46b31f9ae831c785281d2865d9ad37932b48f1bd05ee0426b`
(complete identity coverage, no unresolved rules).

A separate allocation preflight sequencing error briefly launched an invalid
0012–0015 panel because draw 0015 had already been allocated. The process was
terminated after six observed seconds and produced no terminal search result.
An `INTERRUPTED_INVALID_ALLOCATION` marker was recorded at the expected path,
with unknown attempt count; draws 0012–0015 are consumed and excluded. No
approval or adoption flags were supplied.

## Loopover full-arm max-branch g0 continuation

Restored `p22-loopover-full-g0` (digest
`d6d3c24fa68c512767e43d45c79985597d659cd28f726b04786100fa25f52f8c`) on fresh
distinct goals 0020–0023. All four tasks used 25,000 attempts and returned
`NO_CANDIDATE_FIRST_TRIAL`; two candidates appeared but neither qualified.
There were zero approvals and receipts, with empty validation and held-out
allocations.

The run recorded 56 native rule steps, 820.077 seconds wall-time and
937,930,752-byte peak RSS. Raw artifact SHA-256
`5c12bd508ab64ea162a0827d13731a25174d662d80334b94b477c7f8d9238352`, resource
snapshot SHA-256
`26a21cc577c6c936201e5bffbc8c66116d54101d171772b076ffd3552dd715f1`, and
native-rule-work SHA-256
`a7b18b8ebe4e6fd6f62c71c2c2c02c213f295b172c1cfe591e890e8e7faaccc4`
(complete identity coverage, no unresolved rules).

## Loopover full-arm five-goal maximum panel

The registered generation-zero checkpoint `p22-loopover-full-g0` was continued
on five fresh pairwise-distinct training goals 0029–0033. Every task remained
stuck and the runner returned `NO_CANDIDATE_FIRST_TRIAL`; four candidates
(`#49548`, `#73552`, `#97556`, `#121560`) had zero independent-goal
qualifications. The run used the full 120,000-attempt ceiling at 24,000 per
task. It recorded 69 native rule steps, 280.434 seconds wall-time and
937,930,752-byte peak RSS.

Raw artifact SHA-256
`fd2903160db7124acd1611c420002739bb3b4a5c7716fa9ea8ce555d24361fda`, resource
snapshot SHA-256
`209447192085eb321545a4804246195ea8cc3854dbdf7f03b5697f21de21dc2b`, and
native-rule-work SHA-256
`43e44de5c72702ec0ab829578229884140c9038b8a8e2f3393d80f454c4d0a2a`
(complete identity coverage, no unresolved rules). There were zero approvals,
receipts, validation allocations, and held-out worlds.

## Loopover full-arm transfer-headroom correction

The five-goal full-root panel on 0029–0033 used all 24,000 attempts on each
world for base search and generated four candidates with no transfer trials.
On four fresh distinct goals 0034–0037, reducing the per-request cap to 10,000
preserved transfer headroom. Candidate `#1611` (digest
`c9f470ba163917fc8061b27fe6a0fc93e1626d6bb435718aa5f3a120403ffc29`, effect
`[[0,1,2,5,3,4,7,8,6]]`) qualified as `#41560` on goals 0034/0035. Its selected
transfer child `#16963` has digest
`e5604deb448518c2a11190497120513c1266a8a64081096511385b77aac31aaf` and effect
`[[3,0,1,2,6,4,7,5,8]]`. Both source and child differ from all twelve active
processes in the registered full-arm root and are non-identity. Exact replay
reproduced the candidate, qualification, witness pair and child. No approval,
receipt, validation or held-out allocation was created.

The source reserved 40,000 attempts, recorded 70 native rule steps, 1,219.864
seconds wall-time and 937,930,752-byte peak RSS. Source and replay SHA-256
values are `f3b5bafad8bf9e9046500494e79c77effc1039e265812b14a6fe656c5bdda6c8`
and `8560eb7903e13fc75150b64da70bfb6356bc5f9cea7dc9341a38ab439446c01a`.
Native-rule-work SHA-256 is
`47cd8dd3a24e748bd72fd8453721ffc5f1ddee33af01565e8d8bd1211e8947e0`
(complete identity coverage, no unresolved rules). The [request](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G0_0034_0035.md)
for one generation-one transition from this exact parent remains awaiting
separate authorization.

## Approved D4 full-arm generation-two transition (2026-10-25)

The exact candidate digest `2d2cb9ecda29351e1d0f513498eb6089c0f48b2dc1f8ee8650ebb2bbf39cdc46` was approved with 12 reviewer-reported seconds. The guarded runner consumed approval `#32278`, executed one transition on training world `p22:d4-v2:train:0002`, verified receipt `#32282`, and captured generation-two checkpoint `p22-d4-g2-2d2cb9ecda29` (digest `2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) from the registered full-arm g1 parent `e83c1fb3b84f589b8ca400b4b39fa03d8c04528aba262adc3b53a4c1eeca9af9`. Exactly one new approval and receipt were added; there were no validation or held-out worlds.

The native resource snapshot digest is `eb89ad86f5d23a099b189c6d463a68d872cfbb6abbf4219b73261839ec15d19d`, and native-rule-work digest is `01c27914add95bffd035218cff92d26cf1ab7e4977e96cda3eb3692318bebce0`; both verify with complete rule identity coverage. The run reserved 30,703 cumulative search attempts, recorded 168 native rule steps, 766.366 seconds cumulative wall time, and 937,930,752-byte process peak RSS. The new per-process RSS observation binds PID `962325` and its timestamp. The child carries 275,271 cumulative primitive work, above the historical 120,000 ceiling; it remains subject to the final shared preflight and ceiling selection. Raw result `evaluation/process_mastery/results/p22_approved_candidate_d4_full_g1_0002_0003.json` SHA-256: `0bfd5df9c522276da17d2fc162fccf7dfb07f222b7152f61e351144ba1b8d39b`. This is a single authorized training transition, not an efficacy outcome or authorization for a later action.

## Approved Loopover full-arm generation-one transition (2026-10-25)

The exact candidate digest `c9f470ba163917fc8061b27fe6a0fc93e1626d6bb435718aa5f3a120403ffc29` was approved with 12 reviewer-reported seconds. The guarded runner consumed approval `#41561`, executed one transition on training world `p22:loopover-v2:train:0034`, verified receipt `#41564`, and captured generation-one checkpoint `p22-loopover-g1-c9f470ba1639` (digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`) from the registered full-arm g0 parent `d6d3c24fa68c512767e43d45c79985597d659cd28f726b04786100fa25f52f8c`. Exactly one new approval and receipt were added; there were no validation or held-out worlds.

The native resource snapshot digest is `0716c484a817f83809a2606afec03c19e9131d9b7ae326d6195cfdabc7a632d8`, and native-rule-work digest is `d616e684c71d70d027bb2f8a822b5802f787da1a33ae593bdd45f04d555ad0d5`; both verify with complete rule identity coverage. The run reserved 40,000 cumulative search attempts, recorded 74 native rule steps, 1,199.911 seconds cumulative wall time, and 937,930,752-byte process peak RSS. The new per-process RSS observation binds PID `1012438` and its timestamp. The child carries 192,281 cumulative primitive work, above the historical 120,000 ceiling; it remains subject to the final shared preflight and ceiling selection. Raw result `evaluation/process_mastery/results/p22_approved_candidate_loopover_full_g0_0034_0035.json` SHA-256: `1123e5168092c3b288cb2f6064748300a9b7a67c67997e8e96f13423781a19a2`. This is a single authorized training transition, not an efficacy outcome or authorization for a later action.

## D4 full-arm g2 P26 search continuation (2026-10-25)

Restored the approved full-arm g2 checkpoint `p22-d4-g2-2d2cb9ecda29` (digest `2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) and searched four fresh, pairwise-distinct training goals 0210–0213. The repaired P26 configuration used exact-effect deduplication, a 10,000-attempt discovery tranche and a 5,000-attempt transfer reserve per request, 60 search ticks and transfer depth 3. All four tasks remained stuck after 10,000 discovery attempts each; no transfer reserve was used. The branch added 40,000 attempts to the checkpoint's 30,703 inherited attempts (70,703 total, below the 120,000 graph ceiling). Its read-only attempt projection covers all 70,703 attempts. The four new requests contain 2,706 verified and 37,294 residual attempts and only eight exact effect digests; all three candidate records surfaced in the result are inherited from the parent, with no new candidate or qualification. Two approvals and two receipts are inherited; this run added no approval, receipt, adoption or checkpoint. Validation and held-out allocations are empty.

Resource snapshot digest `80e3c38619b349095e9881e9df238fb9145e8d9b3bb30ead81becd04f719aa86` and native-rule-work digest `610a8c791947644578d9b9c0be18c41602bd6cb4acbc676ba55b7deebb419a8c` verify; native-rule identity coverage is complete with zero unresolved rules. The snapshot records 222 cumulative native rule steps, 6,387.325 seconds cumulative wall time and 2,297,323,520-byte process peak RSS, attributed to PID `1204612` with a timestamp. Raw result SHA-256 is `b693e56dfc59c24904ccca819cb7ff64c0f7a25a5df83a3d44598fee25891be5`; read-only attempt projection SHA-256 is `4956a81843e8cd260ee1dd5871145dd7e11a5f396bf9a96192fdc224eaae467e`. This is bounded negative training-search evidence; it produces no new descendant and does not close the lineage, matched-resource or held-out gates.

## Loopover full-arm g1 P26 search continuation (2026-10-25)

Restored the approved full-arm g1 checkpoint `p22-loopover-g1-c9f470ba1639` (digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`) and searched four fresh, pairwise-distinct training goals 0214–0217. The P26 configuration used exact-effect deduplication, 10,000 discovery attempts and a 5,000-attempt transfer reserve per request, 60 search ticks, transfer depth 3 and the unchanged 120,000 graph-wide ceiling. All four tasks remained stuck. The branch added 55,000 attempts to 40,000 inherited attempts (95,000 total). It recorded a new candidate `#51571` (digest `6b78af5ad17a9c32d982b8348c21061da12fbdf21b30c58cb5be38dcafa391be`), but its 15,000 independent-goal trials were all residual and it has no qualification; it is not eligible for an approval packet. The other reported candidate `#16963` is inherited from the parent. The read-only attempt projection covers all 95,000 attempts; the four new requests contain 5 verified and 54,995 residual attempts, with 6,477 exact effect digests. One approval and one receipt are inherited; none were added, and no checkpoint was created. Validation and held-out allocations are empty.

Resource snapshot digest `b3ebdbfe3f3729ca934ce0131a49a718f9671f116bfa47ae50ce77c96853a2b0` and native-rule-work digest `823f2112054e3b247a32acbde44c039d1020d9f26fc2209d0641134c3fb6a48a` verify; native-rule identity coverage is complete with zero unresolved rules. The snapshot records 128 cumulative native rule steps, 2,606.411 seconds cumulative wall time and a 3,959,488,512-byte process peak RSS attributed to PID `1588606` with a timestamp. Raw result SHA-256 is `56f826af5f72eed9aee080a7098cc93662fb26cf55eae5129594c1f96c1795b1`; read-only attempt projection SHA-256 is `32c762c636232acc71656eeefa4e00fa3f0d0b72efd8f75a1aef8bf3ddef20f9`. This is training-only negative qualification evidence; the candidate cannot be adopted, and the lineage, matched-resource and held-out gates remain open.

## Loopover full-arm g1 P26 follow-up search (2026-10-25)

Restored the same immutable full-arm g1 checkpoint on fresh distinct training goals 0218–0221. Exact-effect deduplication, a 10,000-attempt discovery tranche, a 5,000-attempt independent-transfer reserve per request, 60 ticks and depth 3 were used. All four tasks remained stuck. The branch reserved 60,000 attempts over four requests and added them to 40,000 inherited attempts (100,000 total under the 120,000 ceiling). The read-only attempt projection covers all 100,000 attempts; the four new requests contain 31 verified and 59,969 residual attempts, with 5,488 exact effect digests. Two new candidates were recorded: `#71577` (digest `bd2aeeca58bc3afa3ce34bdb9156508f26c5c57f5d047f46248aad528ff53916`) and `#71671` (digest `68720f6e6e869718cd5c9cb001f6694e5a4ebaad4184e123632aeda8cfdc12e1`). Their 20,000 independent-goal trials were all residual, with no qualification; neither is eligible for approval. The third candidate record, `#16963`, is inherited. The run inherited one approval and one receipt, adding neither, and created no checkpoint. Validation and held-out allocations are empty.

Resource snapshot digest `67b56014d81aec637a3ea89a7a61c94e6f3442150fd0c2f7302fe5763b393918` and native-rule-work digest `59063617c5b3ec8e268d73865609fc3b3b01464caa0a6aa6ad2ceb177ce6a514` verify; native-rule identity coverage is complete with zero unresolved rules. Cumulative native rule steps are 122, cumulative wall time is 2,615.018 seconds, and process peak RSS is 3,958,472,704 bytes, attributed to PID `1693102` with a timestamp. Raw result SHA-256 is `c2342f710a5879d16319d6723e4bd977702f8dc1b6babec1f26f289e16b03e23`; read-only attempt projection SHA-256 is `185e4185a407ec29fd09688c11a4c70f8ccbdb41b7333aa1d7ba5f69a6e7a2a8`. This is bounded negative training-search evidence; it creates no descendant and does not close P22's lineage, resource or held-out gates.

## Loopover full-arm g1 second follow-up search (2026-10-25)

Restored the immutable full-arm g1 checkpoint again and searched fresh distinct training goals 0222–0225 with exact-effect deduplication, the 10,000 discovery/5,000 transfer-reserve configuration, 60 ticks and depth 3. All four tasks remained stuck. The branch added 55,000 reserved attempts to 40,000 inherited attempts (95,000 total under the 120,000 graph ceiling); three requests used the 5,000 transfer reserve and the fourth did not. The read-only projection covers all 95,000 attempts; the four new requests contain four verified and 54,996 residual attempts, with 4,355 exact effect digests. Candidate `#81580` (digest `9b2840fbd6a5e095ec6280d967467054b2479d7f41a35784eab7277bbd8e0bbb`) received 15,000 independent-goal trials, all residual, and no qualification. Candidate `#16963` is inherited. One approval and receipt are inherited; none were added, and no checkpoint was created. Validation and held-out allocations are empty.

Resource snapshot digest `04d5bb084c383ea0367b42281beff8c11cbf0a627e3b52aa58ea321f0be74ef0` and native-rule-work digest `8ae83638c6ed4dfd136d5d34b6e1ed065dddc264e61c800fd783986545da5993` verify; identity coverage is complete with zero unresolved rules. The snapshot records 121 cumulative native rule steps, 2,336.745 seconds cumulative wall time and a 3,958,915,072-byte process peak RSS attributed to PID `1797381` with a timestamp. Raw result SHA-256 is `cf1feb14da5a3448e8146a87e5006c5885b075e7480a99859272644d98e9c7ad`; read-only attempt projection SHA-256 is `1a0abb081d08b0703d2cbb5a7a63c67d9e513477dee31463a6e2609f6fe86384`. This is bounded negative training evidence; it creates no new descendant or approval candidate.

## D4 invention-only g2 continuation (2026-10-26, draws 0460–0463)

Continued from `p22-d4-g2-84854777d0e3` (digest
`d8a916474c8e3bafd44dda0082fd7c71ccb3dac1c0a2daf9bbe7f759c70fb4df`) on four
pairwise-distinct training goals. The run completed all four tasks, which
remained stuck, and added 43,528 attempts to the 44,280-attempt parent graph.
The read-only attempt export covers 87,808 unique IDs (76,685 residual and
11,123 verified). No candidate qualified: `#9456` received six independent-goal
trials (one verified, five residual); `#9459` received 112 (four verified, 108
residual), but its inherited qualification remains invalid because `kind` is
missing; identity-effect candidate `#25873` received 3,528 (408 verified,
3,120 residual); and `#12174` received none. All four task rows are `stuck`.

No approval, receipt, adoption, checkpoint, validation allocation or held-out
access was added. The run inherited two approvals and receipts. Resource
snapshot `7a370c33020519fcdb3adba1746e9464dbffb17cd330b1691d8d2fcadedceb1d`
and native-work snapshot
`2e5e1b95f4b2506205b5c356a9003938c6355ad67115a584f8374761c8e610b9` validate;
native-rule identity coverage is complete with zero unresolved rules. It
records 256 cumulative native rule steps, 12,418.743 seconds wall time, and
3,250,761,728-byte peak RSS attributed to PID `520363`. Cumulative declared
primitive work is 905,115, above the 600,000 development ceiling, so the branch
cannot supply an admissible invention-only g3 checkpoint.

Raw result SHA-256 is
`cce5862dc39d8cbff22c95dbce314477d13dc22da8772d5e6905942a109d86ae`; read-only
attempt-export SHA-256 is
`221e1fec7a9f74afe4f50d8e0a2ea0aad60517ede37d402ec1df37ee72af384d`. This is
negative training-search evidence only; the invention-only g3 descendant and
P22 resource, preregistration and held-out gates remain open.

## Supplementary isolated resource-panel remeasurement (2026-10-26)

Re-ran the existing eight-cell resource panel for approved checkpoints
`p22-d4-g2-2d2cb9ecda29` and `p22-loopover-g1-c9f470ba1639` on their registered
common training worlds. All eight cells completed with all 20 resource fields
measured and valid snapshot digests; no approvals or receipts were added, and
validation/held-out access remained false. Maximum isolated worker wall time
was 24.791 seconds, worker peak RSS was 3,518,386,176 bytes, and maximum
cumulative primitive work was 275,274. Scores remained 1/4 and 2/4 respectively.

The remeasurement is preserved separately as
`p22_resource_panel_new_approved_checkpoints_0609_0612_0622_0625_rerun_20261026.json.gz`
(SHA-256
`39c1f486e48117da5df14534cd6b6def345549f60a823bd4f68534c085977a88`). The
original artifact remains intact at its original path with its original hash
`5683a2e475ec5f9821f9dc1df3cc02c743d928b66fb5eca6e0ff79d96362f6dc`. The preserved partial manifest remains the original artifact (SHA-256
`b82e4e36d89861f081a46c93874a1edd053f2ef61a393adbb5176e09b05ac53c`); it
reconciles 26/32 checkpoints and 104/104 cells, leaving six descendants and
per-field ceilings outstanding. No efficacy inference follows.

## D4 full-arm g2 reduced-budget continuation (2026-10-26, draws 0480–0483)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
pairwise-distinct training goals. The reduced 5,000-attempt per-request cap
reserved 12,646 new attempts over the parent's 30,703 (43,349 cumulative); all
four tasks remained stuck. The attempt export covers 43,349 unique IDs (39,518
residual and 3,831 verified) and eight exact effects. No new candidate
qualified: `#4022` and `#6521` each received six independent-goal trials (one
verified, five residual); inherited `#22382` received none; and `#39809`
received 2,646 (374 verified, 2,272 residual). No adoption or checkpoint was
created. Two approvals and receipts are inherited; this branch added none.
Validation and held-out allocations are empty.

Resource snapshot `30b7c423cf0a5ad3a0a7165c06022ef88e2e7a057494dc2278dab6dcfbf5c26c`
and native-work snapshot
`b587f553e155e0ce9f87fa800fc68f7bd290507bc765247fca2ed077c814242b` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 219 cumulative native rule steps, 3,219.310 seconds cumulative wall
time, 2,296,702,928-byte peak RSS attributed to PID `1283039`, and 374,888
cumulative declared primitive work, within the 600,000 development ceiling.

Raw result SHA-256 is
`0f5b801aa2170c5eba43f3cc9fd6a77c48d756edbef1061ac5d608b6ccd8f041`; read-only
attempt-export SHA-256 is
`5a42de6066b7947e316f3b7bea07c40917617de70ea060318cd2c28e01bfe5a1`. This
negative training-only search does not create an admissible D4 full-arm g3
descendant; final resource, preregistration and held-out gates remain open.

## D4 full-arm g2 reduced-budget continuation (2026-10-26, draws 0488–0491)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
pairwise-distinct training goals. The 5,000-attempt per-request cap reserved
12,646 new attempts over the parent's 30,703 (43,349 cumulative); all four tasks
remained stuck. The export covers 43,349 unique IDs (39,580 residual, 3,769
verified) and eight exact effects. No candidate qualified: `#4022` and `#6521`
each received six independent-goal trials (one verified, five residual);
inherited `#22382` received none; candidate `#37306` received 2,646 (320
verified, 2,326 residual). `#37306` has the same expression digest as the
nonqualifying candidate in the preceding budgeted branch. No adoption or
checkpoint was created. Two approvals and receipts are inherited; no new
approval, receipt, validation allocation or held-out access occurred.

Resource snapshot
`b5b99101f5144112c71cc7108319794763d5cfa97a4935b00f85c7fc46a62219` and
native-work snapshot
`7d4e1a39501e55264c55bc59f4022fe68521ea66517415046299839fc745690b` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 220 cumulative native rule steps, 3,295.398 seconds cumulative wall
time, 2,297,593,856-byte peak RSS attributed to PID `1457064`, and 373,198
cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`67085a5d9f363d0285de710fb0634216875535d441f40b50f8324837951d91cc`; read-only
attempt-export SHA-256 is
`feb03f977b9d611154a80460a5c477b4ab8fb95d7ad196d71c518a40bd020a8b`. This
negative search does not create an admissible D4 full-arm g3 descendant; final
resource, preregistration and held-out gates remain open.

## D4 full-arm g2 reduced-budget continuation (2026-10-26, draws 0512–0515)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` on four
pairwise-distinct training goals. The 5,000-attempt per-request cap added 12,646
attempts to the parent's 30,703 (43,349 cumulative); all four tasks remained
stuck. The read-only export covers 43,349 unique IDs (39,474 residual, 3,875
verified) and eight exact effects. No candidate qualified: `#4022` and `#6521`
each received six independent-goal trials (one verified, five residual);
inherited `#22382` received none; and `#39809` received 2,646 (350 verified,
2,296 residual). Candidate `#39809` has the same expression digest as the
nonqualifying candidates in the two prior budgeted branches. No adoption or
checkpoint was created. Two approvals and receipts are inherited; none were
added. Validation and held-out allocations are empty.

Resource snapshot
`83a2941457e5a09e5a66f6ec27676f050376ec54369c54790bc8ffd5df03826f` and
native-work snapshot
`bc359cdd5757b0248f5403804a943fcdfecb3e68a77ce2fe7cb7798ffbdc774e` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 219 cumulative native rule steps, 3,368.066 seconds cumulative wall
time, 2,296,610,816-byte peak RSS attributed to PID `1633654`, and 373,333
cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`2a4622f13a1ba9499d83b2bc0c04a71f3208f7bce88881ad24004778c7681b29`; read-only
attempt-export SHA-256 is
`aee84b43b61124f0ac2a534ebc29eecf9986d422f91ad93dba81fab82502f4d5`. This is
negative training-search evidence; it does not produce an admissible D4
full-arm g3 descendant, and final P22 gates remain open.

## D4 full-arm g2 reduced-budget continuation (2026-10-26, draws 0524–0527)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
distinct training goals with the fixed 2,500 discovery / 2,500 transfer
reserve per request and exact-effect deduplication. The graph contains 43,349
unique attempt IDs (30,703 inherited and 12,646 new); the new attempts include
11,151 residual and 1,495 verified records across eight exact effects. All
four tasks remained stuck. No candidate qualified: `#4022` and `#6521` each
received six independent-goal trials, inherited `#22382` received none, and
branch-local `#37306` received 2,646. `#37306` has expression digest
`a13113e9485e0a9d0f392a4a4e16e0a4a807d60d98d98bab117263700bbf23ec`, already
seen in prior nonqualifying branches. No new approval, receipt, adoption or
checkpoint was created; two approvals and receipts are inherited. Validation
and held-out allocations are empty.

**Allocation caveat:** These draw IDs overlap the earlier four-arm common-root
scoring panel on draws 0522–0533. Preserve this run as exploratory negative
training evidence only; it is not a fresh independent-goal sample and cannot
count toward a lineage or efficacy gate.

Resource snapshot `74518da0051d7eb31fddd35beeb8610c4cf11735f9c89b7266411a22703c3cbe`
and native-work snapshot
`638b70a16992d7869ce7c4f69dbd69ea1b756d09ce5f6f00da0feaae6512687b` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 219 native steps, 3,414.471 seconds cumulative wall time,
2,297,049,088-byte peak RSS attributed to PID `2014117`, and 373,333 cumulative
declared primitive work, within the 600,000 ceiling. Raw result SHA-256 is
`6c1abfd38a86fe9cc2ba214da4d58b8977ae02ef9f55880723646d7bf44b2575`; the
read-only attempt export SHA-256 is
`dcbec63d92b200e3f36b5634ff20b4d0464758a72a3f1a831913074ad030864d` and covers
all 43,349 unique attempts. This is negative training-only evidence and does
not supply an admissible D4 full-arm g3 descendant; P22.E2–E3 remain open.

## D4 full-arm g2 reduced-budget continuation (2026-10-26, draws 0534–0537)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
distinct training goals. The draw IDs were checked against the retained P22
training artifacts and do not overlap the earlier 0522–0533 common-root panel.
The fresh requests used 10,000 discovery attempts in total under the fixed
2,500 discovery / 2,500 transfer reserve per request and exact-effect
deduplication. All four tasks remained stuck and produced no new candidate or
qualification. The export contains 40,703 unique attempt IDs (37,192 residual,
3,511 verified) and eight exact effects. No new approval, receipt, adoption or
checkpoint was created; two approvals and receipts are inherited. Validation
and held-out allocations are empty.

Resource snapshot `b25b5ff3bf52090bd52eb4d9ad3dc5bd8362a83ea7ae1283048c81ad2536543d`
and native-work snapshot
`6e460980c9ae36c2defdce0af74d560d0bba1daa3e64b2f9c00a3e8ddd29054a` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 211 native steps, 3,024.638 seconds cumulative wall time,
2,296,172,544-byte peak RSS attributed to PID `2435662`, and 348,078 cumulative
declared primitive work, within the 600,000 ceiling. Raw result SHA-256 is
`ca4276e3bf8dc119ac5a08b6facd15511fd876020f7e0f46ac2cda6d27e8ee3f`; the
read-only attempt export SHA-256 is
`9c130a341172d31194d14f4b46dc5ab7a6277c1f1f0b35777e4d5b6ce63c6372` and covers
all 40,703 unique attempts. This negative training-only branch supplies no
D4 full-arm g3 descendant; P22.E2–E3 remain open.

## D4 full-arm g2 reduced-budget continuation (2026-10-26, draws 0538–0541)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
fresh distinct training goals. Draws 0538–0541 were checked against retained
P22 artifacts and were unused. The four requests each used 2,500 discovery
attempts under the fixed 2,500 discovery / 2,500 transfer reserve and
exact-effect deduplication. All tasks remained stuck; no new candidate or
qualification was produced. The read-only export contains 40,703 unique
attempt IDs (37,216 residual, 3,487 verified) and eight exact effects. No new
approval, receipt, adoption or checkpoint was created; two approvals and
receipts are inherited. Validation and held-out allocations are empty.

Resource snapshot `d6fc47b660b9fc5e9f1692f4ca3437407371d9be81dfd5c4a8e31c963e324cc3`
and native-work snapshot
`03658f2365e3ad7b470f5996b234360d69e733d801b92578bc159b03820b3495` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 211 native steps, 2,734.368 seconds cumulative wall time,
2,297,028,608-byte peak RSS attributed to PID `3342815`, and 349,792 cumulative
declared primitive work, within the 600,000 ceiling. Raw result SHA-256 is
`11bffb547fa03ea3bdad4f442dd4f1786f27700ad9946163ee9a2b9842be5eaf`; the
read-only attempt export SHA-256 is
`7ccd23e6a5a24c21a723086f3fe5e1c9446e6043481be78518eb368e0f544ae7` and covers
all 40,703 unique attempts. This negative training-only branch supplies no
D4 full-arm g3 descendant; P22.E2–E3 remain open.

## D4 full-arm g2 continuation (2026-10-26, draws 0542–0545)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
fresh, distinct training goals. Draws 0542–0545 were checked against retained
P22 artifacts and were unused. Each request used the 5,000-attempt discovery
allowance; the 5,000-attempt transfer reserve remained unused. The branch added
20,000 attempts to the parent's 30,703, for 50,703 unique attempt IDs in the
read-only export (45,715 residual, 4,988 verified) across eight exact effects.
All four tasks stayed stuck. Candidates `#4022` and `#6521` each received six
independent-goal trials (one verified, five residual); inherited `#22382`
received none. No candidate qualified. No new approval, receipt, adoption or
checkpoint was created; two approvals and receipts are inherited. Validation
and held-out allocations are empty.

Resource snapshot
`7a8c00214bd52c3c734185bf54478517bd79aa199532e7868457ab59eed04c94` and
native-work snapshot
`d9616b3fcddfde735cfdabf3504eacce33b0e76475a5102ccafe20acb36c831b` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 216 cumulative native rule steps, 3,332.524 seconds cumulative wall
time, 2,297,192,448-byte peak RSS attributed to PID `3493676`, and 454,982
cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`6cb405cb2691eb27bbf2a1697b9e928b714db1c72e5d62d99ba51ea24fbeb0f7`; read-only
attempt-export SHA-256 is
`b5f20da7c24c5bc2dcc43fbc05199cc45081c49f6579ca15e566ec6d1a06ad01` and covers
all 50,703 unique attempts. This negative training-only branch creates no
admissible D4 full-arm g3 descendant; P22.E2–E3 remain open.

## D4 full-arm g2 continuation (2026-10-26, draws 0550–0553)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
fresh, pairwise-distinct training goals. Draws 0550–0553 were checked against
retained P22 artifacts and were unused. The read-only attempt export contains
43,349 unique IDs (39,405 residual, 3,944 verified) across eight exact effects.
All four tasks remained stuck. Candidate `#32300` received 2,646 independent-
goal trials (342 verified, 2,304 residual), but its expression digest
`a13113e9485e0a9d0f392a4a4e16e0a4a807d60d98d98bab117263700bbf23ec` repeats
candidate `#37306` from prior nonqualifying branches. Candidates `#4022` and
`#6521` each received six independent-goal trials (one verified, five
residual); inherited `#22382` received none. No candidate qualified. No new
approval, receipt, adoption or checkpoint was created; two approvals and
receipts are inherited. Validation and held-out allocations are empty.

Resource snapshot
`023607e0c839913d262afd24834912dc41d5c86bd94ee72237cb9952efbf64cf` and
native-work snapshot
`6badb4f85d69b336bede439df3fbba51021aff640355ea84b9cd274ca1565815` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 226 cumulative native rule steps, 3,104.439 seconds cumulative wall
time, 2,297,196,544-byte peak RSS attributed to PID `3682828`, and 402,210
cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`606dd9d3ccd2c662fcf304816c9ce976cb98a8679b35fdc27246417de9ee7e35`; read-only
attempt-export SHA-256 is
`7637f0811c4d705fb46e9fee7ca438e9f13755a43d8b441338c78f6fcd10802a` and covers
all 43,349 unique attempts. This negative training-only branch creates no
admissible D4 full-arm g3 descendant; P22.E2–E3 remain open.

## D4 full-arm g2 continuation (2026-10-26, draws 0578–0581)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
fresh, pairwise-distinct training goals. All four tasks remained stuck. The
branch added 12,646 attempts to the 30,703-attempt parent graph. Its read-only
export contains 43,349 unique IDs (39,579 residual, 3,770 verified) across
eight exact effects. Candidates `#4022` and `#6521` each received six
independent-goal trials (one verified, five residual); inherited `#22382`
received none. Candidate `#37306` received 2,646 trials (346 verified, 2,300
residual), with the same expression digest
`a13113e9485e0a9d0f392a4a4e16e0a4a807d60d98d98bab117263700bbf23ec` seen in
prior nonqualifying branches. No candidate qualified. No new approval, receipt,
adoption or checkpoint was created; two approvals and receipts are inherited.
Validation and held-out allocations are empty.

Resource snapshot
`92495282d6e052c3135b2c1d6cd216b26015ef9139ca128505c6d488505a2fa5` and
native-work snapshot
`dd0a47be5ce36802999974edc7493c2f715935ed8eba42606b597c8f163fad1f` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 219 cumulative native rule steps, 3,336.086 seconds cumulative wall
time, 2,296,807,424-byte peak RSS attributed to PID `133305`, and 373,598
cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`55fa22fdad29a2e36d1c49276ef024068aabf2e08378ad0ae23571e1d3d63363`; read-only
attempt-export SHA-256 is
`8c50defdaa6cdf75ae7e2f5ae3d626d387b4808332214f73085baa8d7aa7a20d` and covers
all attempts. This negative training-only branch creates no admissible D4
full-arm g3 descendant; P22.E2–E3 remain open.

## D4 full-arm g2 continuation (2026-10-26, draws 0554–0557)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
fresh, pairwise-distinct training goals. Draws 0554–0557 were checked against
retained P22 artifacts and were unused. The branch added 10,000 attempts to the
30,703-attempt parent graph. The read-only export contains 40,703 unique
attempt IDs (37,155 residual, 3,548 verified) across eight exact effects. All
four tasks remained stuck. Candidates `#4022` and `#6521` each received six
independent-goal trials (one verified, five residual); inherited `#22382`
received none. No candidate qualified. No new approval, receipt, adoption or
checkpoint was created; two approvals and receipts are inherited. Validation
and held-out allocations are empty.

Resource snapshot
`aad355a3713c1b9a1e81cb3d614cbff358545736f73933085d0643a79b65af2c` and
native-work snapshot
`5f273858aaab1ca39c5c173b6658d574ca79c573165a80f1c57b53a2f64ff3da` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 211 cumulative native rule steps, 2,809.388 seconds cumulative wall
time, 2,297,036,800-byte peak RSS attributed to PID `3856289`, and 348,159
cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`6ef30bb9db76d6a0e8104cc7903e46f5baaa9b26c06df2648ea0d7b8499b48e0`; read-only
attempt-export SHA-256 is
`d776211708b876efd9570582bc68a0b8b2575f86b8363be02013bd7d0be0baf2` and covers
all 40,703 unique attempts. This negative training-only branch creates no
admissible D4 full-arm g3 descendant; P22.E2–E3 remain open.

## D4 full-arm g2 continuation (2026-10-26, draws 0566–0569)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
fresh, pairwise-distinct training goals. Draws 0566–0569 were checked against
retained P22 artifacts and were unused. The branch added 12,646 attempts to the
30,703-attempt parent graph; the read-only export contains 43,349 unique IDs
(39,555 residual, 3,794 verified) across eight exact effects. All four tasks
stayed stuck. Candidates `#4022` and `#6521` each received six independent-
goal trials (one verified, five residual); inherited `#22382` received none.
Candidate `#39809` received 2,646 trials (288 verified, 2,358 residual), but
repeats the nonqualifying expression digest
`a13113e9485e0a9d0f392a4a4e16e0a4a807d60d98d98bab117263700bbf23ec`. No
candidate qualified. No new approval, receipt, adoption or checkpoint was
created; two approvals and receipts are inherited. Validation and held-out
allocations are empty.

Resource snapshot
`42ec3e647e733da54d365b2105aff08dca56be2f928a2f6eca71b1f0954f6690` and
native-work snapshot
`e1b093811bcbfa2ad59465f15afa7efa30618e3770f3ffe73173a5a16ec6c7a5` validate;
native-rule identity coverage is complete with zero unresolved rules. The run
records 220 cumulative native rule steps, 3,274.522 seconds cumulative wall
time, 2,296,815,616-byte peak RSS attributed to PID `4146357`, and 372,352
cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`74942828fc31735d76356b9e2471ac50ee6a2dc120ef505f0cbc8c59e7dd5800`; read-only
attempt-export SHA-256 is
`ed21babdb8053eb6155a842156165f9de76bbaa1a29f91f67d5a97c7cf7aed49` and covers
all 43,349 unique attempts. This negative training-only branch creates no
admissible D4 full-arm g3 descendant; P22.E2–E3 remain open.


**P22 Loopover full-arm g1 qualification (2026-10-26; draws 0126–0129):** Four fresh, pairwise-distinct training goals were searched from checkpoint `p22-loopover-g1-c9f470ba1639` (digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`); all four tasks stayed stuck. The branch added 17,500 attempts to its 40,000-attempt parent graph. Its read-only export covers 57,500 unique attempts (57,461 residual, 39 verified) and 6,719 exact effects. Candidate `#44071` (digest `20e47b09a3ffcac98a672c43a43cb94c6bccc4a5ae958428d54ff9845ab28b5e`) qualified under `independent_goal_composition` on distinct training worlds 0126/0128; exact replay reproduced the candidate, qualification `#59086`, witness attempts and worlds, and the byte-identical attempt export. Transfer child `#51580` has digest `50b021ab7c8ebc706d9238bdee527c67ed0ae19a77bba2dc0a6115fe97d1a818`; direct audit found both its non-identity effect and the source effect absent from all 12 active parent processes. Candidate-specific [approval request](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0126_0128.md) is prepared and awaits exact approval; no action, new receipt or checkpoint was created. One approval/receipt are inherited. Validation and held-out allocations are empty. Source resource/native-work digests `bad1db222202cf3bde4e71095b506b5725865905fe91db10052a715657c5d4eb` and `95985d3a446e5e883ea9f9b1a6186a35b45d4d14827ef7696cd07d8f09d32849` validate with complete native-rule identity coverage and zero unresolved rules. The source records 127 native steps, 1,570.792 seconds wall time, 3,957,927,936-byte peak RSS (PID `343274`), and 292,794 cumulative declared primitive work. Raw [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0126_0129_budget5k_p26.json) SHA-256 `500787ceac7f618e2a99dcb0bd814a6f649418d18dd5f61bc5e6d36fff21eca0`; exact [replay](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g1_0126_0129_budget5k_p26_replay.json) SHA-256 `33fc4106307607f533376b98ffa42cd4fdff7b13cdcdf167bb507a6fefee6673`; read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_full_g1_0126_0129_budget5k.json) SHA-256 `3909dd2341bcbd16dd7e2361964f4a6d5e6263b62233712f05caf450344bae8f` is byte-identical to replay. The Loopover full-arm g2 descendant remains pending exact approval; the P22 manifest, freeze and held-out gates remain open.

## D4 invention-only g2 continuation (2026-10-26; draws 0008–0011)

Continued from checkpoint `p22-d4-g2-84854777d0e3` (digest
`d8a916474c8e3bafd44dda0082fd7c71ccb3dac1c0a2daf9bbe7f759c70fb4df`) on four
fresh distinct training goals. All remained stuck. The branch added 7,646
attempts (6,571 residual, 1,075 verified) across eight exact effects to its
44,280-attempt parent graph; the complete read-only export covers 51,926 unique
attempt IDs. No new candidate qualified; the identity-effect candidate is
ineligible. Two approvals and receipts are inherited; no new approval, receipt,
adoption or checkpoint was created. Validation and held-out allocations are
empty.

Resource snapshot `2e37fab0540a78f7358bbd1dff2495ce575b7fa20eaef4139a20da9a3776287`
and native-work snapshot
`ceaa57406d20217e7da618a3204620e2554176747a9985766f420f328e1f90b3` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 247 cumulative native rule steps, 6,717.936 seconds cumulative wall
time, 3,130,683,392-byte peak RSS (PID `427423`), and 551,764 cumulative
declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`e2979e30ecadda906b00ef896ff1571b4ad29d306278396fd1ce40c08b0c1f68`; read-only
attempt-export SHA-256 is
`ae73bac3654c6e0e9f49a3482df5d1818af9f39454eb182c3c8b28cbed4ea2ce`. This
negative training-only result produces no admissible D4 invention-only g3
descendant. The six missing descendants and final P22 gates remain open.

## D4 invention-only g2 continuation (2026-10-26; draws 0040–0043)

Continued from checkpoint `p22-d4-g2-84854777d0e3` on four fresh distinct
training goals. All remained stuck. The branch added 7,646 attempts (6,544
residual, 1,102 verified) across eight exact effects to its 44,280-attempt
parent graph; the complete read-only export covers 51,926 unique IDs. No new
candidate qualified; identity-effect candidate `#25873` received 2,646
independent-goal trials and remains ineligible. Two approvals and receipts are
inherited; no new approval, receipt, adoption or checkpoint was created.
Validation and held-out allocations are empty.

Resource snapshot `4acc5f3028b921e4e1e724f0925d2078ae74a2cdd60182876062881e08de6a3c`
and native-work snapshot
`d17007b25371cad3ab66812f7b9e07f2e51ddebbee65dbb320178d3c7aa52a30` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 247 cumulative native rule steps, 6,424.865 seconds cumulative wall
time, 3,131,285,504-byte peak RSS (PID `807125`), and 551,692 cumulative
declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`2427f7e8546b2e7494053605f1112d28bca86152a4efcd7523c0f392db6c53b1`; read-only
attempt-export SHA-256 is
`4ec21ad8fd359ec0e8d18c217c30369adf3cda2d29d1f5a9318bcfe194de49ff`. This
negative training-only result produces no admissible D4 invention-only g3
descendant. The six missing descendants and final P22 gates remain open.

## Loopover invention-only g2 continuation (2026-10-26; draws 0130–0133)

Continued from checkpoint `p22-loopover-g1-2638da0f23ae` (digest
`c91670f7a91ba3d9f958f865dc85c4d4596d852a8a97c0e99e1f8d3d7b925057`) on four
fresh distinct training goals. All remained stuck. The branch added 10,000
attempts (9,995 residual, five verified) across 1,868 exact effects to its
20,000-attempt parent graph; the complete read-only export covers 30,000 unique
IDs. Candidates `#24075` and `#25422` received 3,386 and 1,614 independent-goal
trials without qualification; inherited candidates `#16551`, `#21555`, and
`#6542` did not qualify. One approval and receipt are inherited; no new
approval, receipt, adoption or checkpoint was created. Validation and
held-out allocations are empty.

Resource snapshot
`007842bafc019d86539902c66a551540b7202bdf4d2e163ac10670e9fdbc01cb` and
native-work snapshot
`96d65b04ab4dae4d766bf99b69de27bf1fadf2c6eae30a91127e3c373895716c` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 92 cumulative native rule steps, 175.632 seconds cumulative wall time,
2,029,764,608-byte peak RSS (PID `1139692`), and 152,038 cumulative declared
primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`83b8d38524d30224e0391c8ea585633c7cbecc4ff5ca7f317dd5e1da5225fea9`; read-only
attempt-export SHA-256 is
`fd4037ba736311388251b229d9a9bd775c9a62aed1cce79f4c93d8564e6495d8`. This
negative training-only result creates no Loopover invention-only g2
qualification or descendant. The six missing descendants and final P22 gates
remain open.

## Loopover invention-only g2 continuation (2026-10-26; draws 0134–0137)

Continued from registered g1 checkpoint `p22-loopover-g1-2638da0f23ae` on four
fresh distinct training goals. All remained stuck. The branch added 5,000
attempts, all residual, across 749 exact effects to its 20,000-attempt parent
graph; the read-only export covers 25,000 unique IDs. No new candidate
qualified or was minted; inherited candidates `#16551`, `#21555`, and `#6542`
remain unqualified. One approval and receipt are inherited; no new approval,
receipt, adoption or checkpoint was created. Validation and held-out
allocations are empty.

Resource snapshot
`3569ace652725afdb0472884effba37d5d8ef767b7924046fa46a08108683d32` and
native-work snapshot
`e806ead1fe7c6adfbfbb7779681d6b54055e321c7ab34e03fa53d9bd2b57c706` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 86 cumulative native rule steps, 121.861 seconds cumulative wall time,
2,030,137,344-byte peak RSS (PID `1152504`), and 121,828 cumulative declared
primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`5016ca02154b8674cb0bfff196af00442a9f09f8462c3bd70b1f8a493d73fd3e`; read-only
attempt-export SHA-256 is
`5248be615a849c3cf3504c63186bd5cafe2b77ad815cc95c34108599fb90ba53`. This
negative training-only result creates no Loopover invention-only g2
qualification or descendant. The six missing descendants and final P22 gates
remain open.

## Loopover invention-only g2 continuation (2026-10-26; draws 0138–0141)

Continued from registered g1 checkpoint `p22-loopover-g1-2638da0f23ae` on four
fresh distinct training goals. All remained stuck. The branch added 8,750
attempts (8,749 residual, one verified) across 1,336 exact effects to its
20,000-attempt parent graph; the read-only export covers 28,750 unique IDs.
Candidate `#24075` received 3,750 independent-goal trials without
qualification; no new candidate qualified. One approval and receipt are
inherited; no new approval, receipt, adoption or checkpoint was created.
Validation and held-out allocations are empty.

Resource snapshot
`9252a286ae8d980398ffcbae0ff922022dca395a0000fe1406b0b979965f822c` and
native-work snapshot
`5be28b87d19ed8b16c22ac2c7b46d2bdda5fa69111b14de2f83dd8ffe6c42a9a` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 91 cumulative native rule steps, 149.769 seconds cumulative wall time,
2,029,862,912-byte peak RSS (PID `1159042`), and 142,204 cumulative declared
primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`966f58ca84fdcef7dd9f23b44846266122717ea807914929e751c17546ef0928`;
read-only attempt-export SHA-256 is
`e3512d5d7fbc32f292f6786e631345385dba1b4b739987334d38966f4643ec4d`. This
negative training-only result creates no Loopover invention-only g2
qualification or descendant. The six missing descendants and final P22 gates
remain open.

## Loopover invention-only g2 continuation (2026-10-26; draws 0142–0145)

Continued from registered g1 checkpoint `p22-loopover-g1-2638da0f23ae` on four
fresh distinct training goals. All remained stuck. The branch added 8,750
attempts (8,749 residual, one verified) across 1,361 exact effects to its
20,000-attempt parent graph; the read-only export covers 28,750 unique IDs.
Candidate `#25328` received 3,750 independent-goal trials without
qualification. One approval and receipt are inherited; no new approval,
receipt, adoption or checkpoint was created. Validation and held-out
allocations are empty.

Resource snapshot
`25fce80dc72b9662eb2e4d5183297ab814db85426cd245a6f0878c9f437819d4` and
native-work snapshot
`eecbc3c7bb619fdbff3ff2592be984d32b6cb98f6af126c35fe3e212dad8c990` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 91 cumulative native rule steps, 149.617 seconds cumulative wall time,
2,030,530,560-byte peak RSS (PID `1168535`), and 145,954 cumulative declared
primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`2870ced2379aeebf0cb48930bc76577b7389f0c2a46d1e6cad4d911e45f0b4fe`; read-only
attempt-export SHA-256 is
`70ebdb70897ab1964836b28275a93ed94a9ddb0cb23d32c08f76082b6d59cceb`. This
negative training-only result creates no Loopover invention-only g2
qualification or descendant. The six missing descendants and final P22 gates
remain open.

## Loopover invention-only g2 continuation (2026-10-26; draws 0146–0149)

Continued from registered g1 checkpoint `p22-loopover-g1-2638da0f23ae` on four
fresh distinct training goals. All remained stuck. The branch added 8,750
attempts (8,749 residual, one verified) across 1,634 exact effects to its
20,000-attempt parent graph; the read-only export covers 28,750 unique IDs.
Candidate `#22822` received 3,750 independent-goal trials without
qualification. One approval and receipt are inherited; no new approval,
receipt, adoption or checkpoint was created. Validation and held-out
allocations are empty.

Resource snapshot
`eb81f361fbfd9ba57f4aa41d9cacdfa45ea3f7dc829a12f7570b439d04f433ef` and
native-work snapshot
`951f41d5b2f71db1329dfbb895775696850236d6323a39a8b0f26bdc02bfa144` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 97 cumulative native rule steps, 213.806 seconds cumulative wall time,
2,029,629,440-byte peak RSS (PID `1177077`), and 155,422 cumulative declared
primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`d01b8bc9b12ac92b88d11c13bb99d607bddc4c2f0754877eef4d02079aedc24b`; read-only
attempt-export SHA-256 is
`6560569c24b1b16c1fff9bd39d276d697f7df819ac9372b2bc717f98561dc99f`. This
negative training-only result creates no Loopover invention-only g2
qualification or descendant. The six missing descendants and final P22 gates
remain open.

## Loopover invention-only g2 continuation (2026-10-26; draws 0150–0153)

Continued from registered g1 checkpoint `p22-loopover-g1-2638da0f23ae` on four
fresh distinct training goals. All remained stuck. The branch added 10,000
attempts (9,992 residual, eight verified) across 1,821 exact effects to its
20,000-attempt parent graph; the read-only export covers 30,000 unique IDs.
Candidates `#22915` and `#25329` received 3,386 and 1,614 independent-goal
trials without qualification. One approval and receipt are inherited; no new
approval, receipt, adoption or checkpoint was created. Validation and
held-out allocations are empty.

Resource snapshot
`5e27716cc4a8758e8c84a7a9c5cb3f4ac4fe2ffe09cd615cf7edcaab93b40378` and
native-work snapshot
`831c7d5324b5241581b7fa48fcaa853fc5c4e6336ea59a12b762999f18da1a86` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 93 cumulative native rule steps, 175.782 seconds cumulative wall time,
2,030,374,912-byte peak RSS (PID `1189893`), and 150,266 cumulative declared
primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`10e7a01feb41caba42d60be265cddb6ae389a6b7210c37e9f109f9ea2a4f8159`;
read-only attempt-export SHA-256 is
`8150fa90cedbf3bd10119a276a0e777d0c1a7b43010c7efec1503cdd13834ceb`. This
negative training-only result creates no Loopover invention-only g2
qualification or descendant. The six missing descendants and final P22 gates
remain open.

## Loopover invention-only g2 continuation (2026-10-26; draws 0154–0157)

Continued from registered g1 checkpoint `p22-loopover-g1-2638da0f23ae` on four
fresh distinct training goals. All remained stuck. The branch added 8,750
attempts (8,749 residual, one verified) across 1,345 exact effects to its
20,000-attempt parent graph; the read-only export covers 28,750 unique IDs.
Candidate `#26581` received 3,750 independent-goal trials without
qualification. One approval and receipt are inherited; no new approval,
receipt, adoption or checkpoint was created. Validation and held-out
allocations are empty.

Resource snapshot
`8d33cf078f46278cd7e7c31d24ed30ee4efe638199d07206b243b0a55e0fca61` and
native-work snapshot
`8e0d3c13ad2523e90c3722c1d550b674d1ef05786edad8908fc0383665487ca6` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 91 cumulative native rule steps, 149.649 seconds cumulative wall time,
2,030,141,440-byte peak RSS (PID `1199770`), and 142,204 cumulative declared
primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`82b456b1f52784be4d5cf872f4320ec628159b147de1b6146dd0d0993dd88d15`; read-only
attempt-export SHA-256 is
`24f06d4bf5c7e7de282e698c6e141515beb325fe7f35475ebbfa2009992e7958`. This
negative training-only result creates no Loopover invention-only g2
qualification or descendant. The six missing descendants and final P22 gates
remain open.

## Loopover invention-only g2 continuation (2026-10-26; draws 0158–0161)

Continued from registered g1 checkpoint `p22-loopover-g1-2638da0f23ae` on four
fresh distinct training goals. All remained stuck. The branch added 8,750
attempts (8,736 residual, 14 verified) across 1,362 exact effects to its
20,000-attempt parent graph; the read-only export covers 28,750 unique IDs.
Candidate `#24075` received 3,750 independent-goal trials without
qualification. One approval and receipt are inherited; no new approval,
receipt, adoption or checkpoint was created. Validation and held-out
allocations are empty.

Resource snapshot
`66c2f1db0edf9394f621d38fce7703d61064d79734d4645d548dbe5ad53b2d09` and
native-work snapshot
`95f005db3a6e1c5be77169c6c6de2eb470623d6854ed9828a661a3e7d80d794a` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 91 cumulative native rule steps, 160.203 seconds cumulative wall time,
2,030,497,792-byte peak RSS (PID `1209004`), and 145,954 cumulative declared
primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`785f8e26b156694f6c06172334cbc185ed1a87f06da055e8283bc5052b4a5436`;
read-only attempt-export SHA-256 is
`560d698ed4ad0da1d0006d2fca17254cdcdab826ffd397198da09110b5de9208`. This
negative training-only result creates no Loopover invention-only g2
qualification or descendant. The six missing descendants and final P22 gates
remain open.

## D4 full-arm g2 continuation (2026-10-26; draws 0588–0591)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` (digest
`2078f32af3e8951d14b7705b38a7f2bfa5074420f3eb105fc9183b6a03919123`) on four
fresh distinct training goals. All remained stuck. The branch added 5,000
attempts (4,277 residual, 723 verified) across eight exact effects to its
30,703-attempt parent graph; the read-only export covers 35,703 unique IDs. No
candidate qualified. Inherited `#9440` received 222 independent-goal trials;
`#4022` and `#6521` each received six. Two approvals and receipts are
inherited; no new approval, receipt, adoption or checkpoint was created.
Validation and held-out allocations are empty.

Resource snapshot
`4938ff74b003358faa5195c68cfc87dbcf8e53a673a76176d2dc90b60b2551e5` and
native-work snapshot
`5613b1bc469beb82b260a6c8aa86ac7ee08867cbc043cd98623a86ecd218a42e` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 208 cumulative native rule steps, 2,521.384 seconds cumulative wall
time, 2,296,659,968-byte peak RSS (PID `1222519`), and 309,089 cumulative
declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`07e808d8df1e9b63f461827857892439d6aa732b0c799b253876f23e5d18354e`; read-only
attempt-export SHA-256 is
`37f2dc9c2106473c8523aa1a61bf9052512f0654bb68393519ac9bda08636d58`. This
negative training-only result creates no admissible D4 full-arm g3 descendant.
The six missing descendants and final P22 gates remain open.

## D4 full-arm g2 continuation (2026-10-26; draws 0653–0656)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` on four fresh
distinct training goals. All remained stuck. The branch added 5,000 attempts
(4,324 residual, 676 verified) across eight exact effects to its 30,703-attempt
parent graph; the read-only export covers 35,703 unique IDs. No candidate
qualified. Inherited `#9440` received 222 independent-goal trials; `#4022` and
`#6521` each received six. Two approvals and receipts are inherited; no new
approval, receipt, adoption or checkpoint was created. Validation and held-out
allocations are empty.

Resource snapshot
`15ac1d43c20084b10506298b217f01b96d221a34cd38450c0ad3fa196e9f258c` and
native-work snapshot
`86967b66e7008b6a8dc7c53f8a76ded665e04852932dfb96b37e96cbb24aa3da` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 208 cumulative native rule steps, 2,534.064 seconds cumulative wall
time, 2,297,507,840-byte peak RSS (PID `1372752`), and 309,314 cumulative
declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`96a2713ad2183ff859247b8659f2f886596606301f3aad674828b01103d8b11a`; read-only
attempt-export SHA-256 is
`7925feab25ffd38b7e1d854a22fd50e4d80960215fce6560ad1b608817565fd2`. This
negative training-only result creates no admissible D4 full-arm g3 descendant.
The six missing descendants and final P22 gates remain open.

## D4 full-arm g2 continuation (2026-10-26; draws 0657–0660)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` on four fresh
distinct training goals with 5,000 attempts per request, split between 2,500
discovery and 2,500 transfer reserve. All remained stuck. The branch added
10,000 attempts (8,825 residual, 1,175 verified) across eight exact effects to
its 30,703-attempt parent graph; the read-only export covers 40,703 unique
IDs. No candidate qualified. Inherited `#9440` received 222 independent-goal
trials; `#4022` and `#6521` each received six. Two approvals and receipts are
inherited; no new approval, receipt, adoption or checkpoint was created.
Validation and held-out allocations are empty.

Resource snapshot
`81f36b05d444e0e9aac286fdf4a3d87d777cd3ab527b00e66696ef81a60079c4` and
native-work snapshot
`c2116b7aa39f8b2c5334411c65e0b044d4a7e22a74747e708abf1a601f642965` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 211 cumulative native rule steps, 2,693.555 seconds cumulative wall
time, 2,297,155,584-byte peak RSS (PID `1497237`), and 348,237 cumulative
declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`81177acaf5d17ce6591f0ecc34e086edad221ea3511425f49a0144aa75d2f1a3`; read-only
attempt-export SHA-256 is
`1392f4758c3fc619997082cad300e28696c81e0a8202502bac4bf086487c9e71`. This
negative training-only result creates no admissible D4 full-arm g3 descendant.
The six missing descendants and final P22 gates remain open.

## D4 full-arm g2 continuation (2026-10-26; draws 0673–0676)

Continued from approved checkpoint `p22-d4-g2-2d2cb9ecda29` on four fresh
distinct training goals with 5,000 attempts per request, split between 2,500
discovery and 2,500 transfer reserve. All remained stuck. The branch added
12,646 attempts (11,132 residual, 1,514 verified) across eight exact effects to
its 30,703-attempt parent graph; the read-only export covers 43,349 unique IDs.
No candidate qualified. Candidate `#32300` received 2,646 independent-goal
trials but repeats expression digest
`a13113e9485e0a9d0f392a4a4e16e0a4a807d60d98d98bab117263700bbf23ec` from prior
nonqualifying branches; `#4022` and `#6521` each received six trials. Two
approvals and receipts are inherited; no new approval, receipt, adoption or
checkpoint was created. Validation and held-out allocations are empty.

Resource snapshot
`86346185a124353a323f23509dfca32012694a56a2200fc82eda0a17bd34bf21` and
native-work snapshot
`3065b74e20105a148fb091d33c354a6014ae62e8584d9ba3a53ef1a07db23463` validate
with complete native-rule identity coverage and zero unresolved rules. The run
records 226 cumulative native rule steps, 3,063.034 seconds cumulative wall
time, 2,297,614,336-byte peak RSS (PID `1636671`), and 402,539 cumulative
declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 is
`9bb6ebf4bac4ddfafcad64c7c3ea76e08284bfd374f1fb9512b35a0f41200cb3`; read-only
attempt-export SHA-256 is
`0dc48a9f53603676f1418e249ea3cbea02636a36d0e675094ed7300746aef541`. This
negative training-only result creates no admissible D4 full-arm g3 descendant.
The six missing descendants and final P22 gates remain open.

## D4 full-arm g2 continuation (2026-10-27; draws 0681–0684)

Four fresh, pairwise-distinct training goals remained stuck. The complete read-only export contains 43,349 unique attempt IDs and eight exact effects. Candidate `#34803` received 2,646 independent-goal trials without qualification and repeats expression digest `a13113e9485e0a9d0f392a4a4e16e0a4a807d60d98d98bab117263700bbf23ec`; inherited candidates `#9440`, `#4022`, and `#6521` received 222, six, and six trials. Two approvals and receipts are inherited; the branch created no approval, receipt, adoption, checkpoint, validation, or held-out allocation. Resource snapshot `d085b621a07ac346fba61dde93d6793097be3ff110b207ad7f11ddaeb6b24601` and native-work snapshot `11b11621313e80b0ae897b2c53ddae79682b87f55028c8a1dd3699003c2e9b86` validate with complete native-rule identity coverage and zero unresolved rules. It records 220 cumulative native rule steps, 3,267.971 seconds wall time, 2,297,864,192-byte peak RSS (PID `1796769`), and 372,854 cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 `8b1e1219b9cd26517f4cfc48ddb0a192ab76a4301055bd3285e86811b711147d`; read-only attempt-export SHA-256 `6f11b84e6963250050d615935353440a4d172d9a8ae147827f1ab7dc40427a7f`. This produced no admissible D4 full-arm g3 descendant; the six missing descendants and final P22 gates remain open.

## Loopover invention-only g2 continuation (2026-10-27; draws 0162–0165)

Four fresh distinct training tasks remained stuck. The branch added 10,000 attempts (9,993 residual, seven verified) across 4,918 exact effects to its 20,000-attempt parent graph; the full export covers 30,000 unique IDs. Candidate `#24072` received 7,500 independent-goal trials and inherited candidate `#6542` received 15,000 trials, without qualification. One approval and receipt are inherited; no new approval, receipt, adoption, checkpoint, validation, or held-out allocation was added. Resource snapshot `a7fd8baae930223d4f9e5108535f34aa94d5895bf417ac8cb2c9c095a75a2f4f` and native-work snapshot `9127d7c2df61ff2a17d039ab4da7c61a5b5ce72896b2e4f51dcb57bc75df0874` validate with complete native-rule identity coverage and no unresolved rules. It records 82 cumulative native rule steps, 171.573 seconds wall time, 2,030,620,672-byte peak RSS (PID `1983039`), and 157,504 cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 `16210949da2d56a371e59b750408b36a5f867df6c57e2f01f65d6f582fac36ff`; read-only attempt-export SHA-256 `9d6f70169d64936c6bfa594af19791ec8c7206d8bc02761c861a3c7c1410348d`. No admissible Loopover invention-only g2 candidate was produced; the g3 descendant and final P22 gates remain open.

## D4 full-arm g2 continuation (2026-10-27; draws 0685–0688)

Four fresh distinct training tasks remained stuck. The complete read-only export contains 40,703 unique attempt IDs across eight exact effects; no new candidate qualified or was recorded. Inherited candidates `#9440`, `#4022`, and `#6521` received 222, six, and six trials, respectively. Two approvals and receipts are inherited; no new approval, receipt, adoption, checkpoint, validation, or held-out allocation was created. Resource snapshot `8efdce6d12138e5b0c410f46ed9d2bf8e5585e8ea05e84f472030a56417d5009` and native-work snapshot `718285557ab82d9f6337eae2b23516c7feb40bf75666eacc909f0d9c33ee4346` validate with complete native-rule identity coverage and zero unresolved rules. It records 211 cumulative native rule steps, 2,689.648 seconds wall time, 2,297,597,952-byte peak RSS (PID `1996172`), and 349,002 cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 `e20b8105adea5c3adf33c2dfcbd4611ad6de97d96bed5e645083a891b9b8f2fd`; read-only attempt-export SHA-256 `97d3a8b0540b8e5732a79fe656e2b48f51aca08303fc6e14746495f5d5ca0990`. No admissible D4 full-arm g3 descendant was produced; the six missing descendants and final P22 gates remain open.

## D4 full-arm g2 continuation (2026-10-27; draws 0694, 0695, 0697, 0698)

Four fresh distinct training tasks remained stuck. The complete read-only export contains 40,703 unique attempt IDs across eight exact effects; no new candidate qualified or was recorded. Inherited candidates `#9440`, `#4022`, and `#6521` received 222, six, and six trials. Two approvals and receipts are inherited; no new approval, receipt, adoption, checkpoint, validation, or held-out allocation was created. Resource snapshot `b3a3864f0cc1acc0c0fdfc05915010ee197ddacce56024aff0d0994ea4698c16` and native-work snapshot `86400f8d5db193860c7922057f97a60082b2bf2dbc682e2d67d5f91fabd359d6` validate with complete native-rule identity coverage and zero unresolved rules. It records 211 cumulative native rule steps, 2,715.463 seconds wall time, 2,325,463,040-byte peak RSS (PID `2130542`), and 348,237 cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 `c28cc0e7d6b3d4bf2de6969bc49966623cac67c585faac551f9776226e1ee2f1`; read-only attempt-export SHA-256 `4786e0bb043ef0118d8ffcd9444160438b00e2fd0de9ae95ae9e61ce572f39ad`. No admissible D4 full-arm g3 descendant was produced; the six missing descendants and final P22 gates remain open.

## Loopover invention-only g2 continuation (2026-10-27; draws 0166–0169)

Four fresh distinct training tasks remained stuck. The complete read-only export contains 30,000 unique attempt IDs across 4,000 exact effects; no new candidate qualified or was recorded. Inherited candidate `#6542` received 15,000 independent-goal trials without qualification. One approval and receipt are inherited; no new approval, receipt, adoption, checkpoint, validation, or held-out allocation was added. Resource snapshot `5ddbb965d650f2aa90e53711a7b6effa456eb32ef0119cb97836360b95ec5f53` and native-work snapshot `6acfe8629bbe70486be533d833e6218577272b4778b0fcbac35f04a4b6f2b72e` validate with complete native-rule identity coverage and no unresolved rules. It records 86 cumulative native rule steps, 122.046 seconds wall time, 2,030,555,136-byte peak RSS (PID `2266643`), and 142,092 cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 `2531bddee9b1afdee88a54fc5bf6089eaa31b16ef758f095c02480a36d5517ae`; read-only attempt-export SHA-256 `5f6c13608332aabdfb5b450344647e66dcaad2406196c6c53ccb896f250876bd`. No admissible Loopover invention-only g2 candidate was produced; the g3 descendant and final P22 gates remain open.

## Loopover full-arm g1 continuation (2026-10-27; draws 0170–0173)

Four fresh distinct training tasks remained stuck. The complete read-only export contains 48,750 unique attempt IDs across 6,468 exact effects. Candidate `#42821` received 3,750 independent-goal trials without qualification; inherited candidate `#1611` received 16,236 trials, also without qualification. One approval and receipt are inherited; no new approval, receipt, adoption, checkpoint, validation, or held-out allocation was added. Resource snapshot `8228e73e5dc98541a399ab67a210f03f6d17c38a16a479ec3fef79389578b3d8` and native-work snapshot `3178ad3d86ccff0df1ed30ae43bc834c42d624c8edaa6ec5eef9ec5e3403d372` validate with complete native-rule identity coverage and no unresolved rules. It records 121 cumulative native rule steps, 1,321.332 seconds wall time, 3,958,210,560-byte peak RSS (PID `2272627`), and 240,032 cumulative declared primitive work, within the 600,000 ceiling.

Raw result SHA-256 `764539c0dab3e99a031077ebe79802bde989bb9e9cc798a453ebed4b2d0b397d`; read-only attempt-export SHA-256 `db131ff5c635de8b8c1bd4c3d3fef384cef91fa9fc00fc80de00ea09d9dc2303`. No admissible Loopover full-arm g2 descendant was produced; the six missing descendants and final P22 gates remain open.

## Loopover full-arm g1 continuation (2026-10-27; draws 0174–0177)

Four fresh distinct training tasks remained stuck. Candidate `#41661` (expression digest `0161d4a90b5a2c8f07dbf673ce09ef7c4dbf0bafaf4047af36891a2eabee92f9`, effect `[[1,2,6,0,4,5,3,7,8]]`) qualified as `#50336` under `independent_goal_composition` on worlds 0174/0177, witness attempts `#41601`/`#47877`. Exact replay reproduced the candidate, qualification and witness keys; the source and replay attempt exports are byte-identical (48,750 IDs, 48,709 residual and 41 verified). The verified independent-goal attempt `#47877` also produced transfer child `#49083` (digest `d260654d9a5e77ca5a42bfcfd764eaa0358ee42abb89f1bfec456050f8639dc0`, effect `[[6,4,2,0,7,5,3,1,8]]`). Both non-identity effects are absent from all 12 active parent processes; the child remains unapproved with zero further qualifications. One approval and receipt are inherited. Candidate-specific [approval request](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0174_0177.md) is awaiting exact approval; no action, receipt or checkpoint was added. Validation and held-out allocations are empty. Resource snapshot `1fd99993760a1a6b8d82ac82ad57b6dafa827a25f5a9ca1b6b398112be42a040` and native-work snapshot `7a153632cf733794e4c5befb3d29c30d6b6c125dd6cc15fa7f1b7882a7342531` validate with complete rule identity coverage and no unresolved rules. The source records 124 native rule steps, 1,314.329 seconds wall time, 3,959,246,848-byte peak RSS (PID `2286726`), and 233,212 cumulative declared primitive work, below the 600,000 ceiling.

Source result SHA-256 `940b012c2feeaf9ffeb88bb252a6d5122d0730b89ecb8bd1a5ef94610977998d`; replay result SHA-256 `035ce23d6bfc727d4826204b532d0dcadf75ca2edd5c01406a388be430a130a5`; shared attempt-export SHA-256 `d92c50c0d4b70256a82b00055fea863948f34f718c059d5fb0eee86636eaca71`. No admissible g2 checkpoint was produced; the six missing descendants and final P22 gates remain open.

## Loopover g1 approvals and checkpoint audit refresh (2026-10-27)

The exact approvals were consumed once each: invention-only candidate `#31572` (12-second review) created checkpoint `p22-loopover-g2-7fb1f08e6ac6`, digest `6417726b217eb40db7bf2d6cfcb1424f0bffe2721db590fedb58d4ff5ec26050`, with verified receipt `#81592`; full-arm candidate `#41661` (12-second review) created checkpoint `p22-loopover-g2-0161d4a90b5a`, digest `477cfe40ae8db6158b7543f52ebf4b555a8bfb24cd524150ea0548508fe1b50b`, with verified receipt `#51591`. Their action result artifact SHA-256 values are `fc9acda4981e44d75c20a290a27fb3cc05c77c6ae99f288c0533c6cb028f90e7` and `0ef9e291f351285fcaf06c627ec6c923a1c055c9d5b4c8419eec79d6b8284f3d`, respectively.

The resource audit now includes both approved descendants: 28 unique checkpoints, 20/20 measured resource fields each, valid checkpoint and snapshot digests, and zero audit issues. Four g3 descendants remain missing (D4 invention-only/full and Loopover invention-only/full); the final resource ceilings and isolated wall-time panel are not frozen/complete, and held-out access remains closed. Audit status is `PASS_PARTIAL_INCOMPLETE`, not a capability or efficacy result.

The supplementary isolated resource panel was rebuilt with 16 completed cells for four checkpoints, including both new Loopover g2 descendants, on the same four registered Loopover training worlds (0622–0625). Every cell measured all 20 fields with a valid snapshot; the panel added zero approvals/receipts and did not access validation or held-out data. The reconciled manifest covers 28/32 checkpoints and 112 cells, with zero issues; four g3 descendants and the resource freeze remain open. Manifest SHA-256: `ff0a7cff640b84cf710f2d5e47e09179b5948a30db16e0560b55c651c9671095`.

## Generation-two continuation searches (2026-10-28)

Seven fresh distinct-goal continuations were run from the exact approved g2 checkpoints: two Loopover invention-only (draws 0180–0183 and 0190–0193), two Loopover full-arm (0184–0187 and 0194–0197), two D4 invention-only (0905/0990/0991/0994 and 0975/0976/0977/0980), and one D4 full-arm (0902/0904/0906/0907). Proposal search was solver-disabled. All tasks remained stuck; no new candidate qualified or was adopted, and no action/receipt/checkpoint was produced. Validation and held-out allocations are empty. D4 invention's inherited malformed qualification `#15845` on `#9459` was excluded. Complete result and attempt-export links and compressed SHA-256 digests are in the [canonical plan entry](COGNITION_BUILD_PLAN_20261010.md). These are development-only negative results and leave all final gates open.

**Further full-arm generation-two continuations (2026-10-28):** Loopover draws 0200–0203 and D4 draws 0912–0915 completed from their approved g2 checkpoints. All tasks were stuck; no candidate qualified or was adopted. These training-only exports have empty validation/held-out allocations. Candidate/resource details and compressed artifact hashes are in the [canonical plan](COGNITION_BUILD_PLAN_20261010.md).

**Loopover full-arm repeat (2026-10-28):** Draws 0204–0207 remained stuck and reproduced the same two unqualified candidate digests seen on 0200–0203. No action, receipt, checkpoint, validation or held-out allocation resulted. See the canonical plan for complete hashes and resource snapshot.

**Loopover invention-only g2 continuation (2026-10-28):** Draws 0208–0211 completed with no qualification or adoption, and no validation or held-out allocation. The exact compressed artifact hashes and complete resource measurements are in the canonical plan.

**D4 invention-only g2 continuation (2026-10-28):** Draws 0981–0984 completed without a new qualification, adoption, or checkpoint. The inherited malformed `#9459` qualification was excluded. No validation or held-out allocation occurred; exact hashes and resource totals are in the canonical plan.

**D4 full-arm g2 continuation (2026-10-28):** Draws 0916/0917/0918/0920 completed with no qualification, approval, adoption or checkpoint. Candidate effects repeated previously recorded candidates. Empty validation/held-out allocation and exact resource/artifact hashes are recorded in the canonical plan.

**Loopover invention-only repeated continuation (2026-10-28):** Draws 0212–0215 reproduced the three candidates from 0208–0211 with no qualifications or checkpoint. No validation or held-out allocation occurred; hashes are in the canonical plan.


**P22 Loopover full-arm g2 continuation after source-request handoff repair (2026-10-28; draws 0220–0223):** Continued from the exact full-arm g2 parent on four fresh distinct training goals, with 2,500 attempts per request, 1,000 discovery attempts plus a 1,500 transfer reserve, depth 3, effect deduplication, and no validation allocation. The complete read-only export contains 60,000 cumulative attempt IDs (59,957 residual, 43 verified) across 7,245 exact effects. The repaired terminal-source eligibility generated 6,000 separate-goal trials across inherited candidates `#16963` (4,912) and `#51583` (1,088); neither qualified. Candidate `#55601` received zero trials. Two approvals and receipts are inherited; this run created no approval, receipt, adoption or checkpoint. All four tasks remained stuck; validation and held-out allocations are empty. Resource snapshot `a9f347d72d4a9602e64fb56b40715d89880470c9f8390ef0d67894e6c371cbe2` and native-work snapshot `4e930e494964a2286ae81dedfb73e0e0722532c803c924dfe4a6b61a2146fbfc` validate with complete native-rule identity coverage and zero unresolved rules. The run records 161 cumulative native-rule steps, 1,539.263 seconds cumulative wall time, 5,427,687,424-byte process peak RSS, and 315,742 cumulative declared primitive work, within the 600,000 ceiling. Compressed [result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g2_0220_0223_budget2500_discovery1000_transfer1500_p26.json.gz) SHA-256 `f8263a7105984162e64fb56b40715d89880470c9f8390ef0d67894e6c371cbe2`; complete read-only [attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_full_g2_0220_0223_budget2500_discovery1000_transfer1500.json.gz) SHA-256 `d6b2542b89df5a34985138b0cd54c880ae10198c99241e890b0fc9ade1b19ccb` covers all IDs. The eligibility fix changes only source-request lifecycle acceptance; two-trial, independent-goal, training-split, novelty, digest, and approval requirements remain intact. No admissible Loopover full-arm g3 descendant was produced; P22.E2–E3 and final resource, freeze, and held-out gates remain open.


**Loopover invention-only g2 continuation after source-request handoff repair (2026-10-28; draws 0224–0227):** Four fresh distinct training tasks remained stuck. The repaired lifecycle eligibility generated 6,000 separate-goal trials for inherited candidates `#16551`, `#21555`, and `#45496` (3,824 / 1,088 / 1,088); none qualified. The complete read-only export has 90,000 cumulative attempt IDs (89,990 residual, 10 verified) across 11,856 effects. Two approvals and receipts are inherited. No new approval, receipt, adoption, checkpoint, validation, or held-out allocation occurred. Resource snapshot `675575b6f928e14c4e1a4de61279b1edc0217513a9ec6b481d4a56784210b19c` and native-work snapshot `d98e76923157a85524abbda745e8e2e21c8f45c46c09ffd11bc75d13ef45f116` validate with complete identity coverage and zero unresolved rules; 159 native steps, 4,313.138 seconds wall time, 8,831,000,576-byte peak RSS, and 572,478 primitive work remain within the ceiling. Compressed result SHA-256 `fc0398cc557173d00cb3b78c21f40b04fbe36520e899e54f9810e91388bde5e8`; attempt export SHA-256 `e343e87bdbafe2fcd4a0444a80824dfe454ae80ea23f9fbf888356a871506ae4`. No Loopover invention-only g3 descendant was produced; all final P22 gates remain open.
