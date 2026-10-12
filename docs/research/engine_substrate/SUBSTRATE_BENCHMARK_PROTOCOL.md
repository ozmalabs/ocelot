# Substrate benchmark protocol

**Version:** 1.2. **Status:** benchmark families and measurement rules are defined, but no confirmatory result is claimed. Protocol changes after a pilot must be versioned. A frozen confirmatory run records this file’s content hash and does not tune against its test split.

**Parent plan:** [`SUBSTRATE_CAPABILITY_AND_TRACTABILITY_MEASUREMENT_PLAN.md`](SUBSTRATE_CAPABILITY_AND_TRACTABILITY_MEASUREMENT_PLAN.md). **Inventory:** [`SUBSTRATE_CAPABILITY_MAP.md`](SUBSTRATE_CAPABILITY_MAP.md).

## 1. Purpose and claim boundary

This protocol defines how to produce comparable evidence about substrate capability, tractability, reliability, and cost. Each experiment tests a bounded claim about a named execution path and input family. Results do not, by themselves, establish general intelligence, safe unrestricted agency, or performance outside the measured envelope.

Use a two-part question for every experiment:

1. **Capability:** does the identified path produce correct/useful outputs on the task distribution, including held-out structural variation?
2. **Cost and boundary:** how do resource use, failure, approximation, refusal, and quality change as relevant input dimensions grow or shift?

An experiment that measures only speed, only a unit-level mechanism, or only in-distribution task score cannot answer both questions.

## 2. Run states

Every run is labelled as exactly one of:

- **Discovery:** unrestricted exploration; may change implementation and hypotheses. Its data are not confirmatory.
- **Pilot:** checks data/runner/instrumentation and estimates variance or scale on development inputs. It may set thresholds and sample sizes but cannot support the final claim.
- **Confirmatory:** frozen code, protocol, inputs/splits, metrics, exclusions, and analysis; no tuning after the freeze. All deviations are reported and invalidate the affected confirmatory claim unless preregistered as a protocol amendment before unblinding.
- **Replication:** a fresh run or task sample following an already frozen protocol, with no changes to the evaluated implementation after freeze.

Do not relabel a failed confirmatory run as a pilot. A new protocol version may test a revised hypothesis while preserving the original result.

## 3. Freeze and provenance requirements

Use the shared machine-readable capture in [`scripts/substrate_run_manifest.py`](../../../scripts/substrate_run_manifest.py) for new substrate runs. Store its `substrate-run-manifest-v1` object in the raw run report. Pass every benchmark-relevant runner, protocol/preregistration, native source, generator, data, and analysis path explicitly so content hashes are recorded. The manifest records current native extension and build-manifest hashes, source fingerprint and stale status, dirty workspace fingerprints, toolchain, hardware, command argv, relevant environment variables, start/end time, and exit status. A dirty-workspace fingerprint summarizes all porcelain status, hashes the content of tracked dirty files, and inventories untracked paths; it deliberately does not hash contents of unrelated untracked artifacts. Explicit input hashes are authoritative for run dependencies.

Use `start_console_capture` / `finish_console_capture` from the helper to tee parent-process stdout/stderr into `evaluation/run_logs/` and record the relative path, hash, byte count, and capture scope. If subprocess output is captured separately by a runner, hash and list those logs too. If no log artifact is available, set `stdout_stderr_capture` to null and explain the limitation; missing capture limits reconstruction of warnings and failures. The structured record must still preserve raw per-instance data, outcomes, and checks.

Before pilot and confirmatory execution, record:

1. repository commit, dirty-tree status, and patch hash if dirty;
2. Rust/Python versions, compiler/toolchain, dependency lock hashes, build flags, and native extension/binary hashes;
3. operating system, CPU model/core count, RAM, storage, accelerator details if used, and relevant runtime configuration;
4. benchmark protocol version/hash, runner source hash, benchmark generator hash, and analysis script hash;
5. seed, data source/version/hash, split identifiers, environment variables affecting execution, and exact command;
6. wall start/end, exit status, stdout/stderr, resource logs, raw per-episode/per-instance records, and exclusions;
7. execution path: Rust/native, Python/host, graph-authored rule, adapter, simulator, or external service; identify state ownership and boundary crossings;
8. evaluation custody: project-self-custodied, technically separated, or externally evaluated. Process/key/container separation is not independent custody.

If any required field cannot be obtained, record it as missing and limit the claim accordingly. Do not substitute a moving branch name for a commit or a human description for a content hash.

## 4. Workload and split construction

### 4.1 Select workloads before confirmatory outcomes

For each capability family, select (a) a representative workload from active substrate use and (b) a controlled synthetic family with known structure or ground truth. Record selection rationale and exclusions before running the confirmatory split. Keep the selected workload set stable between the baseline and candidate conditions.

At least one confirmatory family must stress the mechanism’s proposed tractability condition, and one must violate it. For cheap-cut claims this means both low-boundary/decomposable structures and high-boundary/strongly coupled controls. For exact inference, include inputs within and beyond the supported-width gate. For induction, include recurring novelty and one-off/adversarial residual controls.

### 4.2 Separate novelty axes

Report results separately on:

- **new instance:** same generator and structural family, unseen seed/contents;
- **new composition:** familiar primitives in a held-out combination;
- **new structural family:** different graph/task topology or dependency form;
- **new domain/modality:** distinct observation/action/task interface;
- **distribution shift:** changed noise, missingness, scale, or mechanism parameters.

Do not call new random seeds “new domains.” Record which factors were known during development. Freeze final test inputs and prevent their use in tuning or prompt/rule/seed edits.

### 4.3 Paired runs and controls

Use paired instance seeds and matched resource budgets when comparing conditions. Randomize condition order where order or cache warming may matter. Include:

- frozen/current implementation baseline;
- budget-matched simple baseline (e.g. reactive, exhaustive small-case solver, or generic matcher as appropriate);
- mechanism ablation that removes the proposed feature while preserving other components;
- positive control that demonstrates the task is solvable by the measurement setup;
- negative/null control where the target capability should not activate (for example, a non-recurring residual should not cause a recurrence mint).

Choose baselines per experiment and justify them before confirmatory runs. No single baseline is appropriate for every subsystem.

## 5. Shared benchmark record

Use one raw record per instance/episode and one summary per run. Raw records should include:

```json
{
  "run_id": "stable-run-id",
  "protocol_version": "1.1",
  "condition": "baseline-or-candidate",
  "instance_id": "stable-instance-id",
  "split": "development-or-confirmatory",
  "seed": 0,
  "input_structure": {
    "nodes": null,
    "edges": null,
    "max_degree": null,
    "treewidth_exact": null,
    "treewidth_upper_bound": null,
    "boundary_width": null,
    "hierarchy_depth": null,
    "rule_count": null,
    "pattern_size": null,
    "domain_size": null,
    "horizon": null
  },
  "outcome": {
    "status": "success-or-failure-or-abstain-or-timeout-or-progress_budget_reached-or-repeated_graph_state-or-refusal",
    "quality": null,
    "exact": null,
    "reason": null,
    "ground_truth_ref": null
  },
  "cost": {
    "wall_time_ns": null,
    "cpu_time_ns": null,
    "peak_rss_bytes": null,
    "allocations": null,
    "rule_matches": null,
    "rule_firings": null,
    "fixpoint_passes": null,
    "graph_writes": null,
    "nodes_minted": null,
    "search_expansions": null,
    "solver_iterations": null
  },
  "path": {
    "native_or_host": "",
    "entrypoint": "",
    "state_owner": "",
    "boundary_crossings": null
  },
  "failure_trace_ref": null
}
```

`null` means unavailable/not applicable; it must not be interpreted as zero. Implementations may extend this record, but must preserve the shared field meanings. Raw records are append-only after execution; any correction is a new record linked to the original.

## 6. Outcome and resource reporting

Report at least:

- number attempted, succeeded, failed, abstained, timed out, refused, crashed, and excluded;
- task-quality distribution with numerator/denominator and confidence interval;
- paired difference to baseline and confidence interval for the primary metric;
- latency and CPU distributions (median, p90, p95, p99 where sample size permits), not only mean;
- peak resident memory and graph/search growth;
- cost per successful outcome as well as cost per attempt;
- results by structural/input stratum and the worst supported stratum;
- instrumentation overhead from matched instrumented/uninstrumented runs;
- all thresholds, stopping criteria, and exclusions fixed before confirmatory execution.

For proportions, use a preregistered interval method appropriate to sample size; for paired outcomes, use the paired instance as the analysis unit. For multiple primary comparisons, preregister a correction or a hierarchy of hypotheses. Report raw counts so the result can be independently recomputed. Never hide timeouts/refusals by excluding them from quality denominators without also reporting intention-to-test results.

## 7. Tractability experiment modules

### 7.1 Closure and matching

Vary independently: graph size, edge density, rule count/body size, candidate bindings, read/write overlap, rule selectivity, no-op fraction, mutation locality, and fresh-node minting. Record fixpoint passes, match attempts, actual firings, writes, graph growth, and cost per useful state change. Include finite closure, cyclic no-op, deduplicated mint, unguarded fresh mint, and adversarial candidate explosion.

Primary questions: does the run terminate within budget; which input dimension predicts cost; does the restricted termination class behave as stated; are costs localized to changed areas; does incremental/scheduled execution preserve the reference result?

### 7.2 Inference

Vary node count, treewidth (exact when feasible and upper bound otherwise), state/domain size, factor arity, frustration/conditioning, evidence density, and graph family. Compare exact junction-tree output against exhaustive ground truth on small cases; compare heuristic/approximate quality and convergence on larger cases. Record exact/approximate/refusal status explicitly.

Primary questions: where is exact inference feasible; what controls wall time and memory; is refusal calibrated to the declared gate; does low width predict cost in the supported family; does low width alone predict solution quality (it need not)?

### 7.3 Recognition and transform

Vary frame/observation size, pattern size/width, degree, type constraints, number of candidates, transform composition length, residual size, and distractors. Use known transforms and anti-controls. Compare against exhaustive matching or a trusted small-instance oracle where feasible.

Primary questions: cost and false-match rate by size/structure; which stages dominate; is matching confined to the intended frame; how often does residual reach inference/mint; are transform/mint outcomes reusable on held-out instances?

### 7.4 Cheap-cut and frame hierarchy

Before sampling, define the frame boundary variables/state, cut cost, allowed approximation, and correctness criterion. Measure exact decomposition width where feasible, heuristic bounds on larger graphs, boundary-size distribution, cross-frame dependency counts, hierarchy depth, cut update cost after mutation, and factorisation error. Compare learned/authored cuts against a simple baseline partition and the monolithic reference.

The hypothesis is supported only if the preregistered workload set shows that the specified cut procedure finds small boundaries at acceptable cost and partitioned execution preserves the declared semantics/accuracy. A few hand-selected easy graphs are insufficient. Report high-width counterexamples and frequencies.

### 7.5 Induction economics

Measure the complete residual-to-adoption path: residual frequency, rung entered, candidate count, search depth, CPU/wall/memory, proposal/evaluation cost, false mint/adoption, rollback, reuse count, and improvement or regression on held-out tasks. Partition results into ordinary, recurring novelty, one-off novelty, and adversarial cases.

Report application cost separately from acquisition and maintenance cost. Compute break-even reuse count only from measured costs, and show sensitivity to reuse distribution. “Rare” means a rate over a named representative distribution with uncertainty and tails—not a qualitative impression.

## 8. Capability experiment modules

| Capability | Primary outcome | Required contrast / ablation | Critical failure modes |
|---|---|---|---|
| Graph/rule engine | Correct final state and closure status under budget | Reference interpreter or exhaustive small cases; incremental/scheduled vs baseline | Nontermination, missed binding, duplicate growth, order-sensitive semantic drift |
| Inference | Answer quality/exactness and calibrated uncertainty | Ground truth, baseline solver, feature ablation | False exact label, local-minimum quality, nonconvergence, unsafe over-budget attempt |
| Perception/shape | Recognition/transform accuracy and residual calibration | Held structure disabled, positive/negative controls | False recognition, forced mint, domain-specific adapter leakage |
| Memory | Retrieval accuracy, provenance correctness, retention | No-memory/reset-memory and corrupted-memory controls | Stale/conflicting evidence used as fact, unbounded growth, irreversible loss |
| Learning | Held-out gain and prior-task retention | Frozen, memory-only, and guarded-learning controls | Overfit, negative transfer, false mint/adoption, failed rollback |
| Planning/action | Completion, cost, calibration, safe abstention | Reactive and budget-matched planner baselines | Unverified success, budget breach, action outside authority |
| Transfer | Held-composition/domain success and negative transfer | Memorization/nearest-template baseline; frozen source-domain model | Post-cutoff tuning, leakage, degradation on prior tasks |
| Reliability | Replay agreement, recovery, safe degradation | Clean run and injected fault controls | Silent state divergence, lost provenance, unbounded resource use |

Action/tool/learning experiments must obey the safety, authority, and evaluator-custody constraints in `GENERAL_INTELLIGENCE_EXPANSION_PLAN.md`. This protocol does not relax them.

## 9. Pilot-to-confirmatory procedure

1. Select one engine workload and one structural stress family from the initial map. Record why they represent active use and the relevant failure boundary.
2. Build a runner that emits the shared raw record and a clean provenance manifest. On tiny inputs, reconcile every reported counter against hand-computable expected counts.
3. Run a pilot only on development inputs. Measure instrumentation overhead, variance, and runtime so confirmatory sample size and time/resource caps are feasible.
4. Freeze the hypothesis, primary metric, structural strata, baselines, ablations, sample size, interval/test method, exclusions, timeout policy, and analysis code.
5. Freeze implementation and confirmatory split hashes. Run baseline and candidate on paired instances in randomized order.
6. Validate record completeness and recompute summary statistics from raw rows. Preserve all failed/crashed/timed-out rows.
7. Publish result, including nulls, deviations, source/build hashes, and exact claim boundary. Open a new protocol version for follow-up hypotheses.

Do not set numerical pass thresholds before the pilot establishes measurement variance and task difficulty; do not set them after viewing confirmatory outcomes. The preregistration must state quantitative thresholds before the confirmatory run.

## 10. Initial confirmatory candidates

These are candidates for the next planning increment, not yet preregistered experiments:

### Candidate A — rule closure and candidate-growth envelope

Use a controlled family with known finite closures, varying graph/rule/match dimensions and a deliberately nonterminating mint control that must hit a resource budget and report failure. Include a representative seeded workload after its exact active path and data provenance are audited. Measure runner counters, memory, and time. Compare full rescans with the supported incremental path only where semantics are intended to match.

### Candidate B — bounded-width inference plus over-width refusal

Extend the existing CAN junction-tree evidence across widths/domain sizes, compare exact solutions to exhaustive ground truth at small sizes, and test explicit refusal beyond the configured bound. Pair with sparse loopy cases where local minima occur to separate topology from optimization quality.

### Candidate C — structural census of real task graphs

Freeze a representative set of graph snapshots from at least two distinct workload families. Compute node/edge/degree distributions, exact treewidth where tractable, heuristic width bounds at larger sizes, separator/boundary candidates, and extraction cost. Analyze only graph structure first; do not infer factorisation correctness until a semantic partition test exists.

Select one candidate for the first pilot after instrumentation and provenance are available. Candidates A and B are more controlled; C directly tests the cheap-cut hypothesis. The selected choice and the reason must be recorded before pilot outcomes.

## 11. Required artifacts and ownership

Initial execution packet:

1. [`SUBSTRATE_CAPABILITY_MAP.md`](SUBSTRATE_CAPABILITY_MAP.md) — source-linked inventory and evidence grades.
2. This protocol — shared benchmark definitions and run rules.
3. Machine-readable run-record schema and example manifest (next implementation artifact).
4. Instrumentation mapping: metric → existing counter or required addition → owner/path → overhead test.
5. Pilot preregistration naming benchmark family, code/data hashes, baselines, metrics, and stop rules.
6. Result document with raw artifact references and explicit pass/fail/inconclusive decision.

For each artifact, record a maintainer and review date in the work tracker. Do not assign reviewers as independent evaluators unless actual institutional separation exists.

## 12. Stop and interpretation rules

- Stop a run on the preregistered wall/CPU/memory budget; preserve partial records and report timeout/OOM as outcomes.
- Keep wall/CPU/memory timeout distinct from an engine's internal work budget. For rule execution, record the requested progress budget, returned progress count, and typed status (`fixed_point`, `progress_budget_reached`, or `repeated_graph_state`). Preserve a post-run probe as a cross-check during the status API's validation period. Never record budget exhaustion or a repeated graph state as successful settlement. The current budget is checked between passes, so report potential pass-granularity overshoot; it is not a hard CPU, wall-time, or memory cap.
- If instrumentation changes the semantic result, stop and fix/re-audit instrumentation before measuring capability.
- If candidate and reference disagree, preserve the case as a correctness failure; do not exclude it as a benchmark anomaly without a preregistered rule.
- If a structural condition fails (for example, the claimed small cut is absent), report the counterevidence and reassess the claim. Do not silently switch to a more favorable structural metric.
- If the baseline is invalid or the task is unsolvable by positive control, mark inconclusive and repair only in a new pilot/protocol version.
- If one domain or stratum fails, do not average it away when the claim says the capability spans all domains/strata.
- No benchmark result authorizes unrestricted tools, physical effects, self-modification, or safety claims.

## 13. First execution decision

Complete the source/path audit and metric mapping for the Rust rule runner before launching the first substantive pilot. The first target is closure/matching because it underlies much of the substrate and can be measured with controlled known-answer families. In parallel, define—but do not yet claim—the graph snapshot sampling frame for Candidate C. The CAN inference family is the first existing solver to extend because its current exact result already has ground-truth and refusal logic.

The first confirmatory run should begin only when: the active entrypoint is identified; counters are reconciled on small cases; build/run provenance is complete; thresholds and resource limits are preregistered; and baseline/candidate conditions are frozen. Until then, work remains in inventory, harness, and pilot status.
