# Embodied Pareto compatibility profiles

The Pareto operation is now owned by the domain-independent
`cognitive_pareto` faculty; see `docs/cognitive_pareto.md`. The embodied names
below are retained as a compatibility interface for existing motor seeds and
are bridged into that general faculty. They are not a separate decision system.

Humanoids, racing cars, and aircraft all face the same kind of decision:
produce an effect without pretending that energy, time, wear, precision, and
structural risk are interchangeable. `embodied_pareto_profile` is therefore a
small, zero-dependency substrate primitive rather than a feature owned by any
one simulator.

Each profile is a graph node with named, directed dimensions. Each candidate
is an immutable measured point with exactly one verified value for every
dimension. The graph relates candidates with `dominates_embodied_pareto_candidate`
and leaves every non-dominated candidate on the frontier. There are no weights,
sums, or hidden winner-selection constants in the core.

Domain context remains mandatory. A short, well-planned trajectory and a long,
wasteful trajectory can occupy different parts of the frontier; neither is
called better unless it is no worse on every declared dimension. Learning
value is also separate from immediate task performance. An unsafe exploration
may add useful causal evidence without becoming a viable motor default.

The current bindings are:

- humanoid gait: directed progress, lateral error, tilt, height deficit,
  support deficit, energy, and prediction residual;
- racing: pace, fuel cost, tyre cost, and contact risk;
- aircraft and generic motor programs: the same primitive is loaded beneath
  the morphology-neutral six-axis controller, ready for flight-path,
  control-effort, energy, and structural-envelope profiles.

Dominance evaluation is recruited as a bounded System 2 task. The hard
real-time loop may continue using an already viable frontier member while the
frontier is updated asynchronously. A separate context-sensitive policy can
choose among frontier members; that choice must remain explicit and must not
be smuggled into the Pareto substrate as a scalar score.
