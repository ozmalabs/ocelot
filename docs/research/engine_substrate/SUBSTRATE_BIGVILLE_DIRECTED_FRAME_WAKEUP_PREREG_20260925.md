# Bigville directed-frame wakeup preregistration

**Question.** Does the caller event queue wake the correct reader frame when cross-frame CAN dependencies are directed, and does an omitted-wakeup control expose stale state?

## Locked design

- Use the first 12 residents in `seeds/bigville_cast100.json`, built through `worlds.bigville_can_beliefs`, and only the loaded `can_native_update_3state` rule.
- Inject directed `causal_influence` edges of weight 1.0 between each frame's `world_safe` Concept in three topologies: chain (`i → i+1`), leaves-to-hub (`i → 0`), and hub-to-leaves (`0 → i`). Edge direction follows the CAN rule's outgoing-neighbor read: a source Concept reads target Concept state, so a changed target must wake its source frame.
- For each topology, run three fresh-process arms from a settled common model: full round-robin rescan; event queue with its directed static dependency relation; and notification-omission control that runs only the directly mutated frame.
- Apply one authored scenario evidence update at the dependency-relevant end of each topology: chain frame 11; leaves-to-hub frame 0; hub-to-leaves frame 11.
- Record final states, candidate/Term counters, frame turns/enqueues, independent full-graph residuals, and whether event state exactly matches full scan. State equality and full-graph fixed-point validity are separate checks.
- Lock the runner, this protocol, base replay runner, cast, CAN seed, builder, and native scheduler source hashes before executing.

## Decision rules

The expected event arm must terminate with zero independently recomputed full-graph residuals. The omission control should either be detectably stale (positive residual) or be explicitly reported as an insensitive mutation; it must not be silently counted as a successful control. Full/event exact state equality is reported but is not required to imply general basin equivalence.

This is a mechanism diagnostic on a project-authored model with injected links. It does not estimate natural dependency direction prevalence, exercise dynamic edge mutation, or validate native GALS. Preserve all failures and issue an amendment before changing the locked conditions.
