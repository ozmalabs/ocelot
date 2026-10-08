# Recursive self-improvement execution plan (2026-10-06)

## Purpose

Close the five gaps identified by the 2026-10-06 codebase audit, in an order
where each step uses only mechanisms that already exist as graph data or
opt-in Rust, and each step is measured before the next depends on it. The
target is recursive self-improvement: the substrate improving how it
improves. The audit found the loop's links (gap notice, graph-native choice,
judge rules, durable gated adoption, codebook growth at four grains) but no
measured case of the improver changing itself, no resolution on minted
structure, no grain/aperture search around map induction, no held-out
adoption measurement, and composition saturating at length 2.

Approximation in this architecture is exact: it is the choice of grain
(dynamic quantization), aperture (quotient) and frame (shift). Every work
package below keeps in-frame values integer and keeps equality exact at the
chosen grain; nothing adds fuzzy tolerance.

## Work packages

### WP1 — Mints carry the aperture they were minted at (gap 1)

Design source: `MINTING_AT_APERTURE.md`, `ONE_LOOP_MANY_GRAINS.md`,
`PER_OBSERVER_APERTURE.md`.

- Shared idiom, as graph data: every sd-loop mint writes `minted_aperture`
  (the dimensions the minting observation resolved: its `aperture` attr if
  set, else its `dim_types`), `minted_grain` (its `grain` attr, else none),
  `minted_dim_types` and `minted_signature` (the residual it was minted
  from). Applied to `sd_mint_quantum`, `sd_mint_generator`,
  `sd_mint_quadratic_generator`, and the `LatentDimension` mint in
  `sd_recognize_dim` (written by `set_attr` after `add_node_if_absent`, so
  existing dedup keys are unchanged).
- New opt-in seed `aperture_minting`: a projected (observer-aperture)
  decode with a non-empty residual MAY mint, and the axis inherits the
  observer's `resolves`/`grain`; and a refinement rule links a finer axis to
  a coarser one (`refines_at_aperture`) when the coarse aperture is a strict
  subset of the fine one and the fine signature projected onto the coarse
  aperture equals the coarse signature exactly.
- Gates: existing sd-loop and aperture tests unchanged; new tests for
  provenance on each mint kind, coarse mint at aperture, refinement link,
  and three negative controls (equal aperture, different content, flag off).

### WP2 — Improve the improver: outcome-credited variation policy (gap 2)

Design source: `seeds/variation_ops.json` (priority is editable graph data;
`tests/test_agent_authors_new_rule_migrated.py` gates that an edit flips the
pick), `seeds/self_optimisation.json` (judge rules write
`Experiment.outcome`).

- Record the chosen variation on the Experiment (`used_variation` edge,
  mechanical stamp of the Program's own verdict).
- New seed `variation_credit`: a graph rule credits each judged Experiment
  to a `VariationCredit{op, kind, trials, supports}` node, and
  `variation_pick` (revised, backward compatible) ranks eligible ops by
  `priority × (trials − supports + 1)/(trials + 2) × 2` for the concern's
  kind, and excludes an op already refuted for the same concern. With no
  history the factor is 1, so the default pick is unchanged.
- Measurement (preregistered): a sequence of improvement episodes drawn
  from 12 concern distributions, outcomes supplied by an authored
  experiment world (disclosed), comparing adaptive-policy against
  frozen-policy (credit rules absent) on held-out episodes: experiments to
  first supported fix. Second order: the same comparison after the policy
  itself has been adopted through a snapshot.

### WP3 — Map induction at a substrate-chosen grain, with an MDL witness (gap 3)

Design source: v1.4 correspondence stage (this session), robust order-N
witness, frame/continuum invariant.

- Opt-in Rust (feature `geninfer_grain_ladder`, runtime attr
  `gen_grain_levels`): if no exact map exists at grain 0, re-quantize base
  and goal coordinates (`⌊(v−min)/2^g⌋`) for g = 1..L and run the same exact
  search; report the first grain at which an exact map exists.
- Opt-in MDL witness (runtime attr `gen_mdl_enabled`): over the
  correspondence hypotheses, accept the map that minimizes description length
  (matrix bits + unexplained-row bits) only if it beats the raw description;
  return the unexplained rows as `outliers` so the seed can carry them as
  their own residual quantum.
- Measurement: planted rotations/reflections between different drawers'
  Omniglot drawings (positive), cross-character pairs (false-explain
  control), same-drawing planted maps (exact control); report recovery and
  false-explain rate per grain and witness.

### WP4 — Held-out adoption gate (gap 4)

`GENERAL_INTELLIGENCE_EXPANSION_PLAN.md` P3-E1 requires signed P2 and P0/P1
custody evidence that does not exist, so P3-E1 itself cannot be executed;
its preflight is run to record the blocker. Its statistical decision rule
(paired Δ ≥ +5 pp, bootstrap lower CI > 0, Holm-adjusted one-sided
permutation p ≤ 0.05, harm family, byte-for-byte rollback of non-improve
proposals) is applied to the WP2 policy adoption over 12 distributions × 30
held-out paired seeds. Labelled as P3-E1-shaped, not P3-E1.

### WP5 — Compositional growth: minted composites become primitives (gap 5)

Design source: `DimInfer` length-≤2 composition (`COMPOSITION_DESIGN.md`),
`DIMGEN_PROGRAM_IR_RESULTS.md`.

- Opt-in Rust: a `DimensionGenerator{kind:"composite", generators, ks}`
  applies its named steps in order; `DimInfer` can use it like any
  generator, so a held composite plus one more step reaches length 3, and so
  on.
- Opt-in seed rule (agent attr `gen_chunk_enabled`): when an observation is
  recognized through a length-2 composite, mint the composite as a new
  `DimensionGenerator` (`composed_from` edges, WP1 provenance).
- Measurement: length-3 and length-4 targets after length-2 exposure, with
  chunking on vs off, plus alias and random-observation false-chunk
  controls.

## Order and stopping rules

WP1 → WP2 → WP5 → WP3 → WP4. A work package that fails its gate is
reported as failed; later packages do not depend on a failed claim. All
runtime changes are opt-in and default-off; no default-on change is made in
this plan.

## Claim boundary

Passing all five establishes, on authored and selected real inputs: mints
with aperture provenance and exact refinement; a measured case of the
substrate's variation policy improving from its own experiment outcomes
under a held-out decision rule; exact map induction at a substrate-chosen
grain; and composition growing beyond length 2 from minted structure. It does
not establish unattended recursive self-improvement: candidate construction,
the experiment world in WP2/WP4, and adoption custody remain authored or
human-gated.

## Status (2026-10-06)

Executed. WP1, WP2+WP4 and WP5 (v1.1) passed. WP3's grain ladder is negative on real data and its MDL witness passed (exploratory). See [results](RECURSIVE_SELF_IMPROVEMENT_RESULTS_20261006.md).

Deviations from this plan:
- WP2's credit factor reads `VariationCredit` inside `variation_pick`; it does not write `VariationOp.priority`. This keeps authored priorities intact and makes rollback a single attribute.
- WP3's ladder is a `grain` field plus a seed-level grain choice, not a separate feature. It is gated at runtime by `gen_grains` (a list; renamed from the planned `gen_grain_levels` so the seed keeps its audited no-bound shape).
- WP5 needed a v1.1 amendment (shear generators) to obtain genuinely deep targets.
