# Linear P19 v1 preregistration

**Status:** frozen before held-out access. **Protocol:** `linear-p19-v1`. **Freeze commit:** must contain this file alone.

## Question and registered criteria

This evaluation tests whether generic graph-authored process invention and receipt-learned strategy reuse improve goal completion in two finite worlds: four-position permutations and irreversible two-object preparation/sealing. It compares `invention_discovery` against `measured_greedy` and `native_primitive_search`. The task generator uses independent world-side randomness; it does not read learned candidates or strategies. The hidden witness used to create each goal is never included in the agent task.

The primary criterion is an observed solve-rate gain of at least **20 percentage points** for invention over the stronger of the two comparators, pooled over the four equally sized family/task-kind cells. The threshold and comparison were fixed before held-out access. The following mechanism criteria are also required:

- At least one held-out, non-template expression must solve its task and receive an independently verified world receipt.
- At least one strategy learned from a verified source receipt must solve a target with both a changed initial state and a changed goal through native strategy replay.
- Every task must be matched across all three arms with identical world/task hashes. Each arm is limited to eight world primitive operations and 4,096 model-query units per task.
- All 100 impossible-goal, illegal-action and precondition-failure controls must preserve world state and classify the control correctly. Control allocation is 34 impossible-goal, 33 illegal-action and 33 precondition-failure cases.
- No task input may contain a witness, solution or goal-action field. Every world receipt and runtime artifact must pass the analyzer’s integrity checks.

An absent candidate-specific human approval is `AWAITING_CANDIDATE_APPROVAL`, not a zero-skill failure. If any invention trial is awaiting approval, the primary efficacy result is `NOT_ESTABLISHED`; the analyzer will still report all completed outcomes, failures, costs, controls and mechanism counts. A proposal can reach a world only when the approval manifest contains an explicit human approval for the exact `family/task_kind/seed/expression_digest`. Approvals do not transfer between candidates or bindings. Development uses clearly labeled synthetic approval fixtures only to validate the gate and is never scored as evidence.

## Worlds, tasks and split

Each family has two task kinds: `process_effect` and `multi_step_constraint`. Permutation tasks expose four held primitive permutations over four positions and use hidden sequences of length three or five. Irreversible-object tasks expose `prepare_0`, `seal_0`, `prepare_1` and `seal_1`; sealing requires prior preparation and cannot be reversed. Process-effect goals complete one object; multi-step goals complete both. The agent receives the initial state, goal and primitive affordances, but not the witness.

The task allocation is deterministic and frozen by seed. It contains 200 tasks in each of the four cells, for 800 matched worlds and 2,400 arm rows. Development uses eight tasks per cell. Held-out seeds are disjoint from development and controls and from the recorded P16–P18 allocations.

| Split and cell | Seed block | Count |
|---|---:|---:|
| Development, permutation/process effect | 29,000,000–29,000,007 | 8 |
| Development, permutation/multi-step | 29,010,000–29,010,007 | 8 |
| Development, irreversible/process effect | 29,020,000–29,020,007 | 8 |
| Development, irreversible/multi-step | 29,030,000–29,030,007 | 8 |
| Held-out, permutation/process effect | 29,200,000–29,200,199 | 200 |
| Held-out, permutation/multi-step | 29,210,000–29,210,199 | 200 |
| Held-out, irreversible/process effect | 29,220,000–29,220,199 | 200 |
| Held-out, irreversible/multi-step | 29,230,000–29,230,199 | 200 |
| Development controls | 29,100,000–29,100,099 | 100 |
| Held-out controls | 29,300,000–29,300,099 | 100 |

Control kinds occupy consecutive portions of their block in the registered order: 34 impossible-goal, then 33 illegal-action, then 33 precondition-failure seeds. The held-out allocation SHA-256 is recorded in the machine-readable freeze record below. The runner rejects held-out execution unless this preregistration is committed and the immediately preceding commit changes only this preregistration file.

## Arms, accounting and analysis

`invention_discovery` boots a fresh cognition-on graph for each task, enables the bounded open-process search/adoption and strategy-discovery policies, and disables unrelated solving/invention policies. It records every attempted expression status, exact candidate digest, approval outcome, native application, world receipt and unseen-binding replay. An unapproved proposal remains non-actionable.

`measured_greedy` repeatedly evaluates every currently legal one-step primitive by Hamming distance and selects the minimum with a stable lexical tie-break. Its model-query count is the number of legal action outcomes evaluated. `native_primitive_search` repeatedly replans in the complete supplied finite transition model using native graph rules and emits one primitive at a time. Its model-query count is the cumulative native frontier expansion count. Invention’s model-query count is the number of native graph expression attempts, including residual, failed and unsupported attempts. These denominators are reported by arm; the shared 4,096 ceiling is a maximum count, not an assertion that one query has identical runtime across adapters. Primitive actions and elapsed time are reported separately.

The analyzer reports per-cell solve rates, matched-world and answer-exposure checks, all row statuses, receipt integrity, failed-search counts, primitive/model-query costs and nondominated resource frontiers. A missing arm, changed task hash, invalid receipt, over-cap row, control error or runtime-provenance mismatch fails structural analysis. Efficacy `FAIL` does not erase a valid negative result; missing approvals or incomplete structural evidence remain `NOT_ESTABLISHED`.

The development self-check completed all 32 task rows across arms and all 100 controls. Native primitive search solved 32/32 within the registered primitive/query caps; measured greedy solved 27/32. The invention adapter completed 8/32 tasks under synthetic candidate-specific development approvals; 16 candidates failed independent world execution and 8 tasks produced no candidate. Eight verified receipts produced strategies that solved a changed state and goal binding. These development outcomes did not change thresholds or allocations and are not held-out evidence. The 58-test focused P19/planner bundle passed before this freeze.

## Runtime provenance at freeze

The loaded native extension is attested from the imported extension object, not inferred from the Python wrapper. The build receipt’s source inputs match the current engine source, the native symbols bind to the loaded extension, and the runtime attestation reports `ATTESTED`. Exact runner, analyzer, source bundle, wrapper, extension, build receipt, cognition-on profile, world adapter, dependency closure and both split-allocation hashes are retained below. Any mismatch prevents held-out access.

P19_FREEZE_JSON: {"phase":"linear-p19-v1","development_allocation_sha256":"fadba2c1cce5e138d81facc456c50be279b0601ef045d4f8844ddbc0fd270f4c","heldout_allocation_sha256":"07f2f16738efa764aa378ef548760cf17ef8040b6564e02c3ce1b639f89fdde7","runner_sha256":"6136da7a7e5c7c1ca936cae36272064cd106967d17688d08cd53bbcfb9954309","analyzer_sha256":"358c10a8466882aaac46dacad759a532be9b14d68721dd7e0a7f369f886bd50f","source_bundle_sha256":"87d94aff5acfc74472e6ee07cb33c911749ea1450125cad2550154ce64f4242f","wrapper_sha256":"b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5","loaded_extension_sha256":"16b94f563be757ad9293e4921864466052d02e3fa07102ecff9e014b0b76a12b","build_receipt_sha256":"c350006f11edc703ae3668c302aedb9ae04aa61659e4752b6fb2bcdb7e4916a1","profile_sha256":"a78c24d45f416530c86542569788d85b7a92897b55939fe3b9c39533a88f7147","world_adapter_sha256":"7253bdf4b806f0e8170353203810b10dd4cb5e350a37c6d2434961a03f5658fc","dependency_closure_sha256":"918f0b77bb15f1790a4c12d4ad34026027c4c7c19333d5b1aeec5d1fb669c35d","runtime_status":"ATTESTED","native_build_source_fingerprint":"73c04733538d88f983beb5139e2dfae4633e686738f9161f56a8b2678e8e2c54","git_commit":"3161b5a251e4717746dd9a6aa2d89f98e3976a68","python":"3.13.5"}

## Execution and artifacts

After the standalone freeze commit, run `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p19_v1 --split heldout --preregistration docs/research/engine_substrate/COGNITION_LINEAR_P19_PREREG.md --output <external-raw-scorecard.json>`. Add `--approval-manifest <candidate-approval.json>` only when that file contains explicit exact-digest human approvals. Analyze the resulting frozen scorecard with `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.analyze_linear_p19_v1 <external-raw-scorecard.json> --output <external-analysis.json>`. Keep raw scorecard and analysis bytes outside git and record their SHA-256 values in the results ledger. No held-out draw, adapter tuning or threshold adjustment is authorized before this file’s standalone commit.
