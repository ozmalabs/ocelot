# Graph-native asynchronous cognitive core — implementation result

Implemented from `Async Cognitive Core-7d1c3308.plan.md` on branch
`gamma-substrate/async-cognitive-core`. Engine **851fd92fb26a**, built in this
worktree from its own Rust source. Canonical post-merge engine
**04e5b0f43b50**, `source_match="own"`.

## What landed

- **One explicit native cycle boundary.** `cognitive_cycle.rs` defines the
  historically distinct legacy plans plus `area_serial` / `area_parallel`.
  `WorldAdapter.tick`, `cognitive_tick`, `master_tick`, native `tick`, and
  autonomous `start_agent` now enter through that boundary instead of silently
  implementing unrelated phase sequences.
- **Semantic areas separated from execution safety.** Rules carry optional
  `area`, `order`, and `latency_class` metadata. Legacy rules intern no defaults
  and export byte-identically. `area_scheduler.rs` derives read/write
  dependencies and SCCs; a name never authorizes parallel mutation.
- **Native graph-requested work.** `CognitiveTask` nodes move through explicit
  statuses. Pure Rust workers consume immutable materialized payloads, and
  `TaskResult` journals fold in deterministic
  `(logical_time, area, task-node)` order with source-epoch validation.
- **One graph writer remains.** Arbitrary rewrite mutation is still serial.
  Parallelism is strictly between graph decision and serial result fold.
- **Area regulation as graph policy.** The cognitive scheduler seed provides
  dependency readiness, stale rearm, per-area logical clocks, supersession,
  salience-driven effort, worker feedback bounded by measured capacity,
  graph-visible shedding, and epoch-deduped residual projection.
- **Reflexes are order-0 runtime work.** Rust owns refractory checks, stimulus
  evaluation, and firing stamps. It exposes one reflex at a time so external
  callbacks still interleave exactly as before; graph-only reflexes can later
  enter independent task components.
- **Thermodynamic commitment.** Wait, refine, and commit coexist as
  `CommitOption` nodes. Concrete `EffectFootprint` data derives information
  destruction and irreversibility; scoring also accounts for epistemic gain,
  goal work, option loss, uncertainty, resources, delay, and opportunity.
  Hard approval remains a separate non-tradeable host boundary.
- **Representative effect routes.** Generic world actions, HTTP fetch, browser
  application, speech emission, runtime installation, imagination's existing
  commit path, and teaching persistence now share the commitment boundary.
  Browser option workspaces are retired after each decision so they cannot
  pollute later action selection. Checkpoint save intentionally remains pure
  mechanical serialization: minting a decision into the live graph immediately
  before snapshot changed the object being saved and failed round-trip fidelity.
- **The eye's thread falls out.** `GraphEye._worker` is deleted. Sobel X/Y become
  generic `vision_convolve` cognitive tasks; `worker_capacity` is an external
  capacity envelope, while graph area state controls desired workers. Outputs
  are identical at 1, 2, and 4 workers.
- **Reading maps onto generic areas.** A separate self-loaded seed maps the five
  existing logical cortices and stages to `CognitiveArea` without changing
  the established reading execution path.

## Measured result

Six real CPU-bound DFT tasks over identical 900-value inputs:

| workers | runtime wall |
|---:|---:|
| 1 | 47.131 ms |
| 4 | 15.172 ms |

**3.11× actual CPU speedup**, with identical outputs. This is not the old
sleep-based concurrency demonstration.

## Gates

- New/affected async core, task, reflex, autonomous, vision, commitment,
  persistence, installation, fetch/browser, voice, world-loop, adoption, and
  self-correction suites: all focused runs green (102 + 60 + 45 + 40 + 26 +
  18 + 12 + 8 nodes across the recorded runs).
- Engine provenance + baseline-list structural gates: **18 passed**.
- Standing vision oracle in the isolated worktree: **214 passed, 10 skipped,
  0 failed**. Re-run after merge in canonical main with its optional
  dependencies present: **224 passed, 0 failed**.
- GraphEye worker-count parity and native speedup gates pass.
- Persistence/rule checkpoint fidelity after the save-boundary correction:
  **8 passed**.

## Enumerated baseline result — conditioned, not dismissed

The full `failure_baseline.py verify` sweep ran for 32 minutes in the isolated
worktree: **543 held, 0 stale, 31 new node IDs**. It is not called green and the
list was not rewritten. The worktree lacks the canonical tree's large untracked
acquired/taught state; a direct seven-file comparison measured **70 failures in
the worktree versus 8 in canonical main** under otherwise matching commands.
After merge and canonical-engine rebuild, the exact same seven files again
measured **8 failures / 143 passes**, identical to canonical before the merge;
none of the worktree-only 31 node IDs survived under that condition. This
establishes the condition difference without rewriting or hand-waving the
enumerated list.

## Honest boundaries

- The inverse dirty index is built and inspectable, but legacy serial mode still
  uses the proven dependency scan until whole-suite shadow equality is
  established.
- Native workers currently use bounded scoped Rust threads rather than the
  older disconnected L2 dispatcher objects; the graph-facing task semantics,
  deterministic fold, and measured parallelism are real.
- Area clocks are event-driven by task completion, not independent periodic
  wall clocks. Wall time alone never improves cognition.
- Pure task computation is parallel; general non-confluent rule mutation is
  deliberately not.
- Checkpoint serialization remains outside the cognitive gate because evaluating
  the gate on the live graph changes snapshot identity. A detached preflight is
  the remaining clean route if checkpoint choice itself must become cognitive.
