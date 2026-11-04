# Phase 15 review and remaining cognition gaps

**Review date:** 2026-10-22. **Reviewed HEAD:** `41bb53fe`; evaluation freeze `e0483bc2`, implementation `11fb8c43`. This is an evidence review, not a new execution schedule. [The canonical linear plan](COGNITION_BUILD_PLAN_20261010.md) owns follow-up Phases 16–22.

## Evidence checked

Read the P15 preregistration, results, runner/analyzer, operator-authoring and generation seed generators, and P6–P14 outcome ledgers. Read both archived P15 JSON artifacts and independently recomputed their SHA-256 hashes. The raw scorecard hash is `2805a9c041624583dfbcca6e1e05f1783113dab3b0ee10f584b5210559d12438`; analyzer hash is `e5fabd74ec3933d85f85aa2966234a6a531cca581cde4ae35b7c38751f31b407`. Both match the published ledger. The stored analysis reports 600 paired worlds, 1,800 scored rows, zero listed integrity failures and an unestimable trend. No held-out evaluation or implementation test was rerun. Native module paths were inspected to verify what the provenance code hashes. The native binary and build metadata were already dirty; neither was changed by this review.

## Findings

### 1. Native macro outcomes are positive; recursive improvement remains unestablished

Full system solved 600/600; unchanged and adaptive each solved 196/600. Full-versus-unchanged gaps are 100, 72 and 30 percentage points across the three checkpoints. Full success is flat, the control becomes more successful, and the frozen conditional-logistic trend is separated/unestimable. Keep its `NOT_ESTABLISHED` result unchanged. More work (+2 declared units/task) and negligible timing differences establish no efficiency advantage. Curriculum matching unchanged gives no independent benefit on this panel; it does not prove curriculum is useless.

### 2. The scored task path bypasses active operator execution

`evaluation/process_mastery/linear_p15_v1.py::_run_task` (lines 355–364 at review) computes commutator powers in a Python loop, creates the expected state from that computed power, and chooses `operator if arm == "full_system" else comm` before invoking native `ProcessApply`. The graph proposal, approval, ancestry and funding paths are exercised elsewhere, but the scored application is not read from an agent-selected active `InventionOperator`/expression path. The result verifies native algebra under the adapter's treatment, not the full agent's operator choice. Mutating or removing an active expression must change or block the next scored execution in a future end-to-end test. Independent world goals must not be derived from whichever operator is promoted.

### 3. Proposals instantiate a fixed grammar path

`gen_invention_operator_authorship_seed.py` explicitly recognizes the `commutator_square` recipe, operands and v1 candidate name. `gen_recursive_process_improvement_seed.py` installs named v1→v2→v3 successors. This is useful graph construction/lifecycle evidence; it is not open-ended operator search driven by task residuals. Candidate names/powers cannot be the curriculum or task generator in the next improvement experiment. Later-phase search must operate over general permitted expression data, record its actual selection evidence and retain the existing approval boundaries.

### 4. The declared native-binary fingerprint hashes Python source

The runner's `provenance()` uses `Path(substrate_rs.__file__)` for `engine_binary_sha256`. The imported path is `runners/dsl/python/substrate_rs/__init__.py`; its hash is exactly the frozen value `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`. At freeze `e0483bc2`, the tracked `_native.abi3.so` instead hashes to `a6ec6b37db89ad17fef19c7231ecf3531f8771a8ccf82b0b872bf19227f816e7` (computed from `git show`, not the dirty working library). Thus P15's frozen fingerprint authenticates the wrapper, not the loaded native binary. The archived records alone do not establish the execution-time native artifact identity. Keep raw outcomes and original protocol intact; qualify native provenance as `NOT_ESTABLISHED` rather than asserting a native hash match. A later reconstruction cannot retroactively prove which binary ran. Future protocols need separate wrapper, loaded-extension, engine-source and build-metadata hashes and dirty-artifact rejection. Audit earlier protocols for the same pattern without assuming all have it.

### 5. Several foundations still need behavioral closure

| Earlier evidence | Remaining obligation | Follow-up |
|---|---|---|
| P6 several opaque process forms, missing native comparator panels | Honest executable support matrix and actual world/receipt adapters; unsupported kinds remain blocked | 16, then 18/19 |
| P7 validated acquired-axis candidates; no later decision consumer | Use an acquired distinction to change a prediction/action, learn significance, revise/retire it on counterexamples | 17 |
| P8 supplied finite hypotheses; finite graph refinement | Induce hypotheses from observed traces and connect experiments to actual simulator state and model updates | 18 |
| P10 exact-context replay, 0-point strategy advantage | Novel goal-directed search and generalization beyond memorized traces; working primitive-search and legality controls | 19 |
| P11 fresh arm has no target learner | Executable fresh/source/mismatched target learners and learning-curve comparison | 20 |
| P12 single-primitive ceiling, equal success | Multi-step observational acquisition where information and action costs are counted; no requirement for teacher-directed framing | 20 |
| P13 all arms at 100%; positive costed chunk reuse | Delayed behavior under declared finite memory and interference; no artificial damage to controls | 21 |
| P15 operator-aligned goals and preselected successors | Independent task distributions, actual graph-selected changes, cost-matched repeated checkpoints and a ceiling-safe estimator | 22 after 16–21 |

## Disposition

P15 remains complete as an implementation/reporting cycle with its registered trend criterion unmet. Its positive outcomes remain native macro/construction/lifecycle evidence with the execution-path and provenance qualifications above. No L1–L7 capability level closes from this review. Do not patch the frozen runner, change its p-values or rescore the same held-out allocation. Implement new protocols on untouched task allocations only after the native execution and provenance gates in Phase 16 pass.
