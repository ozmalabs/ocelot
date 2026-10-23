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

After the restored-ceiling correction, all 10 tests in
`tests/test_p22_development.py` pass. The P22 runner self-check passes and
reports `heldout_accessed=false`; its lineage-tamper controls reject the
mutated fixtures. The analyzer self-check passes all nine negative and
positive controls, including missing/partial/mismatched resource sources.
The development continuation on fresh D4 draws 0576/0577 remains in progress.
