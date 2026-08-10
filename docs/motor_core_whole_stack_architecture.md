# Consolidated embodied motor core

## Outcome

Ground vehicles, aerial bodies, humanoids, and helicopters now use the same
architectural boundaries even where their plant models remain different:

1. Python exposes opaque effectors and mechanically stamps physical receipts.
2. Rust-evaluated graph rules infer state, learn consequences, select actions,
   and publish an opaque command.
3. Hard-real-time rules protect the local sensorimotor deadline.
4. Soft-real-time rules perform receipt-backed adaptation.
5. Background rules consolidate or replay experience.

This is a consolidation of ownership and scheduling, not a claim that one
kinematic model describes wheels, rotors, articulated legs, and autorotation.
Body-specific seeds retain the consequences needed by their physics.

Ordinary learned action competition is also consolidated, rather than merely
sharing a schema. Each domain computes its established deterministic
body-specific cost, writes its negation as a domain-neutral grounded option
value, and gives collapse/release authority to `motor_decision_collapse`.
The common core publishes both an opaque token and the exact winning graph
node. This preserves contextual identity when several memories share a token.

| Domain | Shared learned competition | Direct paths intentionally retained |
|---|---|---|
| Ground/racecar | learned forward-planning action models | babble, damage recalibration, probes |
| Aerial | learned flight-control action models | babble and emergency experiment paths |
| Humanoid | support- and state-conditioned walking primary | balance reflex, gait interruption, get-up, tonic control, program release |
| Helicopter | contextual energy/viability memories; compact fallback | reset-bounded calibration intervention |

Plant learning counts and decision-habit counts are separate. A collapse
settle-back increments `decision_experience_count`; it never fabricates a
physical receipt or alters the forward model's `experience_count`.

## The implemented stack

| Layer | Checked-in graph artifact | Responsibility |
|---|---|---|
| Shared state and plasticity spine | `embodied_sensorimotor_core` | Delayed/noisy body belief, efference copy, exact receipt credit, plant envelope, consolidation and default-mode replay |
| Shared embodiment priors | `embodied_motor_priors` | Actor-scoped embodied episodes, relational body facts, continuity, viability and receipt-grounded causal capability |
| Shared collapse | `motor_decision_collapse` | Scoped order-0 default/learned proposal, residual-authorized deeper valuation, settle-back and one-shot episode publication |
| Shared compound motor programs | `embodied_motor_program` | Passive-dynamics-referenced analysis by synthesis across arbitrary compatible opaque effector groups |
| Shared structural body model | `embodied_structural_limits` | Specification-grounded weakest-component envelopes, conservative action admissibility, measured utilization, fatigue and overload interrupts |
| Ground | `embodied_adaptation` | Morphology-agnostic local locomotor models and damage adaptation |
| Aerial | `aerial_adaptation` | Three-dimensional thrust/yaw consequences and flight viability |
| Humanoid | `humanoid_adaptation` | Joint, support, balance, gait-memory and recovery consequences |
| Helicopter | `helicopter_autorotation` | Rotor-energy management, hidden power-loss inference and landing viability |
| Host boundary | `embodied_graph_transducer` | Edge insertion, raw pose/state copying, cardinality checks and reporting projection only |

The historical Python `MotorCortex` is explicitly a compatibility component,
not this core. Graph-only persistence is separated from legacy Python cortex
rehydration.

### Calibration receipts are not full episodes

Primitive humanoid calibration originally became expensive when every twitch
was normalized into the complete multimodal adaptive population. The graph
grew provenance-correctly, but matching time grew with that history: the full
competence gate was still running after sixteen minutes.

Primitive verified receipts now author a lightweight `adaptive_learning`
request directly. Support-phase movement still enters the full body-belief,
efference-copy and multimodal receipt lifecycle. This keeps the biological
distinction between local calibration plasticity and integrated movement
experience without a host shortcut.

The shared lifecycle also advances one `AdaptiveClock` from verified receipt
epochs. Expired eligibility traces and fully credited outcomes keep their
nodes and causal provenance, but graph rules move their agent-root edges from
active to archival indexes. The live temporal-credit join is therefore bounded
by the biological eligibility horizon instead of repeatedly scanning the
entire movement history.

## Scheduling is authored data

Every rule manifest carries `latency_class` and `area`. The three sheets have
different semantics:

- **Hard**: body-state publication, local interruption, release, exact causal
  bookkeeping and bounded action publication.
- **Soft**: verified-receipt learning and model revision that may be
  interrupted without missing the motor deadline.
- **Background**: consolidation, replay and structural memory work.

Humanoid analysis-by-synthesis expansion and fixpoint closure remain hard
because they construct the command that must be released now. Shape-library
storage remains background work: active locomotion retains new coordinated
programs as working motor memory, while an explicit episode/lifetime boundary
recruits offline graph consolidation. Static, non-locomoting library import
may recruit the same sheet immediately.

The audit deliberately does not assert a preferred count. A larger hard sheet
is not automatically better: it can mean lower response latency or that slow
work has leaked into the deadline. Counts are compared with a Git parent so a
reviewer sees the change and evaluates its meaning.

## Actor and episode scoping

Candidate selection must not scan every option of a type in a shared
substrate. Each selector is structurally audited:

- its source must be a graph neighbourhood;
- that neighbourhood's variables must be connected through the rule match to
  an actor or episode; and
- `NodesOfType` is forbidden inside a candidate selector.

The shared motor collapse illustrates the full path. An actor-bound policy and
actor-bound embodied episode open a transient decision state. The episode's
opaque options are copied into that state's `in_episode` scope. Collapse reads
only the union of `in_scene` and `in_episode`, then publishes the exact winning
node once back to the same episode. Domains epoch-stamp all locally eligible
options before arming and remove context options that are no longer eligible.
This allows multiple actors, episodes, support phases, and contextual memories
to coexist without cross-contaminating consideration sets.

## Deterministic structural benchmark

`scripts/audit_motor_core_manifests.py` reads
`protocols/motor_core_audit_v1.json` and the nine declared seed manifests. It
does not import PyBullet, boot a substrate, or run a simulator. Its JSON report
contains:

- per-manifest and aggregate hard/soft/background rule populations;
- per-area sheet populations;
- candidate-selector scope evidence and violations;
- manifest identity and latency-class invariants; and
- a hard-sheet comparison against an explicit revision or `HEAD^1`.

Missing manifests at the baseline are reported as unavailable and excluded
from the comparable delta; they are never silently treated as zero. There are
no hard-coded expected rule totals.

```bash
python scripts/audit_motor_core_manifests.py
python scripts/audit_motor_core_manifests.py \
  --baseline-revision <revision> \
  --json-out results/motor_core_manifest_audit.json
```

The benchmark is a structural regression gate. Behavioral competence still
requires the preregistered simulator experiments; this report establishes
where cognition lives, what owns the deadline, and whether candidates remain
locally scoped.
