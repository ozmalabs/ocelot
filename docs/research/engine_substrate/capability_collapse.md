# M-by-N capability collapse and continuous control

`capability_collapse` is the domain-neutral cognition function beneath motor,
perception, language, planning, and future faculties. It does not implement a
privileged System 1/System 2 switch or one organism-wide controller.

The architecture is **M-by-N**:

- **M parallel authority scopes**, learned from independent and causally coupled
  sensor/effector/resource domains;
- **N recursive capability orders** inside each scope, all represented by the
  same `CapabilityProgram` type.

```text
 parent authority scope
      ▲ unresolved typed residuals
      │
      └───────────┐       scoped constraint / expiring override
                  │                    │
 local scope A    │                    ▼                 local scope B
   order 0 ──► order 1 ──► ... ──► order N                 order 0 ──► ...
      │                                                        │
      └──── continuous effective outcome                       └──── outcome
```

Independent scopes cycle at independent rates. One outcome is required only per
conflict domain, not per organism. An outcome may itself be a compound program
controlling arbitrarily many effectors.

## Continuous local cycle

A scheduler or physical adapter advances a scope's integer
`cycle_request_epoch`. The graph then:

1. rearms only that scope;
2. immediately exposes its `holds_default_capability_outcome`;
3. evaluates its current capability envelope;
4. corrects locally when a held program covers the condition;
5. continues the viable default when the local chain is exhausted;
6. publishes only unresolved residual channels to its parent scope;
7. incorporates a valid parent lease without stopping local feedback;
8. completes only its own epoch.

The adapter never chooses between a default and override. The graph publishes
one `effective_capability_outcome` for the scope. A settled local correction
replaces the provisional default; one valid lease replaces both. Conflicting
leases are explicitly refused.

An override is a scoped lease with integer `valid_from_epoch` and
`expires_after_epoch`. Expiry returns effective authority locally. The parent
therefore need not seize an entire body or permanently replace a fast loop.

## Multidimensional capability envelopes

A channel-mode `CapabilityProgram` owns any number of
`CapabilityResidualChannel` nodes. Each channel carries integer:

- `observed_quanta` and `boundary_quanta`;
- `precision_quanta` and the program's minimum accepted precision;
- `control_demand_quanta` and `proactive_boundary_quanta`;
- its graph-held baseline boundary for revaluation.

A trusted channel opens deeper cognition when either:

```text
observed_quanta > boundary_quanta                 # reactive failure
control_demand_quanta > proactive_boundary_quanta # anticipated consequence
```

Channels are never summed into a single score. A small structural-safety channel
can therefore open cognition independently of a large harmless sensory channel.
The upstream Pareto/goal machinery may derive `control_demand_quanta` from value,
efficacy, uncertainty, urgency, or expected consequence without hard-coding
those domains here.

The legacy scalar path remains supported for already migrated consumers, but
new cognition should use channel envelopes.

## Residual propagation

When no local higher program covers a breached channel, the graph mints one
idempotent `CapabilityResidualReport` per state/program/channel/epoch. It contains
only the typed unresolved evidence and points at the parent authority scope.
Local sensory state and local decision machinery are not copied upward.

The parent can respond by supplying:

- a new higher-order program;
- a changed target or constraint represented in the consumer's graph;
- an expiring `CapabilityOverrideLease`;
- a combined meta-program for multiple child scopes.

Repeated parent corrections can subsequently compile downward.

## Learning authority topology

Authority scopes are body-plan properties, not anatomical constants. A
`ControlCouplingObservation` records integer interference, precision, and its
structure-derived boundary. Trusted interference above that boundary creates:

- reciprocal `requires_joint_settlement_with` relations;
- a parent scope coordinating the affected children;
- a `CapabilityCouplingResidual` requesting a combined program.

Thus fingers may initially cycle independently, while observed tendon, grasp,
load, or task coupling produces hand-level programs. Limb interactions can
similarly produce posture or whole-body scopes. An octopus-like body can retain
many broad peripheral authorities; a humanoid can have many narrow fast scopes
under stronger shared coordination.

## Practice, automaticity, and revaluation

Practice is not raw repetition. A deeper settlement produces evidence only after
the world marks it as success or failure and supplies a `CapabilityContext`.

For scalar programs, evidence is keyed by:

```text
(program, task-level outcome basin, residual band)
```

For channel programs, each breached dimension is credited separately:

```text
(program, residual channel, task-level outcome basin, observed band)
```

Compilation requires:

- the configured number of successful integer receipts at that band;
- the configured number of distinct contexts;
- no more than the allowed failures;
- an explicit consolidation receipt when consolidation is required.

Only the evidenced channel boundary expands. Other dimensions do not inherit
fictional competence. A compiled `CapabilityOutcome` should represent a
task-invariant basin or combined policy, not a fixed actuator trace; it can link
to `CapabilityInvariant` nodes and control many authority scopes.

A verified failure of automatic execution dominates old success evidence. The
graph removes the compiled edge, restores learned channel boundaries to their
baselines, and marks the program `revaluation_required`. This prevents an unsafe
revoke/recompile fixed-point and models goal devaluation, damage, context shift,
or loss of skill.

Measurable automaticity includes:

- lower achieved collapse order;
- fewer cognitive evaluations;
- fewer upward residual reports and authority transfers;
- broader verified channel envelopes;
- survival under novel contexts, perturbation, and concurrent scopes;
- explicit re-escalation after failure or devaluation.

## Full-body scaling requirement

Nothing in the seed names limbs, joints, motors, or a fixed action width. The
execution gates instantiate 64 independently clocked scopes—enough to exceed a
simple humanoid inventory of fingers, toes, gaze, jaw, spine, limbs, and
whole-body auxiliaries—then advance only one without imposing a global barrier.
The same tests discover a coupled domain and apply one compound outcome to two
children.

This does not yet provide a detailed humanoid hand model. It establishes the
required substrate invariant: adding fingers increases graph data and learned
coupling structure, not controller code or architectural depth.

## Scientific provenance

The mechanisms are engineering commitments motivated by convergent results,
not claims that the graph is a literal anatomical model:

- hierarchical frontal control: Badre et al. (2009),
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC2990342/>;
- simultaneous level-specific prediction errors: Diuk et al. (2013),
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC3865543/>;
- automaticity and reduced higher-control demand: Poldrack et al. (2005),
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC6725010/>;
- corticostriatal action bracketing and habit compilation: Smith and Graybiel
  (2013), <https://pmc.ncbi.nlm.nih.gov/articles/PMC3951965/>;
- proactive allocation from expected reward and efficacy: Frömer et al. (2021),
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC7884731/>;
- motor-equivalent solutions preserving task variables: de Freitas et al.
  (2011), <https://pubmed.ncbi.nlm.nih.gov/21676927/>;
- consolidation as post-practice stabilisation: Nettersheim et al. (2015),
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC4412892/>;
- peripheral elaboration of octopus arm control: Gutnick et al. (2020),
  <https://www.sciencedirect.com/science/article/pii/S096098222031191X>;
- flexible human locomotor burst generators: Ivanenko et al. (2013),
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC4408427/>.

## Runtime and files

The authoring script `scripts/gen_capability_collapse_seed.py` emits
`seeds/capability_collapse.json`. Python performs no runtime selection,
arbitration, learning, or override decision. The Rust rule engine executes the
graph to a fixed point.

Load the module explicitly or declare it as a faculty dependency:

```python
WorldAdapter(seeds=("capability_collapse",))
```

The seed is dormant until graph states or continuous cycle requests are present.
