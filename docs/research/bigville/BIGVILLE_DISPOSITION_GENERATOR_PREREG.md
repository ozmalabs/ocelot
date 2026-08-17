# Bigville disposition generator — PRE-REGISTRATION

**Committed BEFORE measurement** (fixed in the approved build plan,
`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`, before any
code in this rung was written). Gates fixed here may not move to make a
number pass.

## Goal

Give bigville residents a REASONABLE pre-existing disposition backstory —
toward specific PEOPLE in their life and toward GROUP buckets — at
world-generation time, fully sampled and hand-tunable, feeding the
target-scoped/domain-scoped Concept families built across Phases A–G
(`regard_for`, `removal_desire_for`, `pity_for`, `admiration_for`,
`devaluation_for`, `controllability_for`, trust `competence_for`/
`willingness_for`, `resentment_debt`/`gratitude_debt`, `TargetArousal`,
`self_efficacy_for:<domain>`, `deservingness_belief_for:<domain>`).

## Architecture (corrected mid-session — see honesty note)

**Generation lives in the sibling `bigville` repo** (it owns cast
generation and the pre-existing `bigville_bond_world.py` relationship
graph; it has NO dependency on `substrate_rs` at all — confirmed by
reading `pyproject.toml`, `numpy` only). **Application lives in ocelot**
(it owns the Concept/TargetPattern representation those generated values
feed). This is the correct split under `docs/features/bigville.md`'s
stated adapter boundary — corrected from an earlier draft of this plan
that proposed building the sampler ocelot-side, before checking that
bigville has its own real, unexported bond-graph machinery and its own
`_draw_clip`/RNG-stream convention already built for exactly this kind of
draw.

- **Bigville** (`worlds/bigville_social_seed.py`, new): samples
  `self_priors` (self_efficacy_prior, deservingness_prior,
  ingroup_affinity, outgroup_suspicion — own `_draw_clip`/RNG-stream
  convention, own param table, separate from `_PARAM_SPEC` so
  `bigville_cast100.json` stays byte-unchanged) and `bonds` (a
  homophily-biased slice of 3–8 people-in-life relationships per
  resident, REUSING `bigville_bond_world.py`'s own `PRIORS` kind
  vocabulary — blood_kin/chosen/acquaintance/feud — verbatim, not
  reinvented). Exports `seeds/bigville_dispositions_cast100.json`.
- **Ocelot** (`domains/bigville_disposition_apply.py`, new): reads that
  exported JSON (copied into `seeds/`) and mechanically applies it via
  the EXISTING `mint_target_pattern` / `mint_trust_beliefs` /
  `mint_domain_self_efficacy` / `mint_domain_deservingness_belief` /
  `concept_apply_evidence` primitives — zero new engine code, zero new
  Concepts, zero new decisions. `overrides` (hand-tuning) are resolved
  into the SAME per-(target, aspect) value dict as the generated values
  BEFORE any `concept_apply_evidence` call, because that primitive is
  ADDITIVE (`h += alpha·evidence`, confirmed in
  `runners/dsl/src/py.rs`) — applying generated-then-override as two
  calls would silently SUM instead of override.

## Predictions

1. **Reproducibility.** Same seed ⇒ `generate_disposition_seed` produces
   a byte-identical dict across two in-process calls (bigville-side gate).
2. **Homophily.** Same-role people-in-life partners are chosen at a rate
   more than 1.5× the uniform-random baseline rate implied by the role's
   population share (bigville-side gate).
3. **Distribution shape.** Most generated person-bond `belief_trust`
   values are mild (`|v| < 0.5` for >60% of bonds); very few are extreme
   (`|v| >= 1.5` for <15%) — the real shape bigville's own `PRIORS`
   table produces (acquaintance/chosen carry zero affect by design; only
   blood_kin/feud pre-load nonzero values), not a fudged post-hoc filter.
4. **Group membership.** Every resident's own `class`/`group`/`role`/
   `workplace_kind` bucket receives `ingroup_affinity`; exactly ONE
   out-group SES-tier bucket receives `outgroup_suspicion`.
5. **Override precedence, no accumulation.** An explicit override value
   for a (target, aspect) always wins, and lands EXACTLY at the override
   value (not summed with the generated value) — the sharpest, most
   failure-prone claim given `concept_apply_evidence`'s additive
   semantics.
6. **Override-only additions.** A hand-tuned person/group target with NO
   generated counterpart is still created and applied.
7. **Self-belief domain = role, no collision.** `self_efficacy_for:
   <role>` / `deservingness_belief_for:<role>` land the generated prior
   exactly, on the SAME per-resident Microtheory as every other applied
   aspect, without colliding with target-scoped Concepts.
8. **Per-resident isolation.** Applying resident A's dispositions does
   not create or perturb resident B's own Resident node/beliefs.

## What this explicitly does NOT establish

Relationship DYNAMICS over time (gossip spread, tie erosion) — this is a
STATIC backstory prior, not a live update loop; bigville's own
`BigvilleBondWorld.tick()`/`hear_gossip`/`experience_event` machinery is
untouched and unconsumed here. Does not touch or depend on
`bigville_cast100.json`'s own 13 `_PARAM_SPEC` params — fully additive.
Does not map `admiration_for`/`pity_for`/`controllability_for` from any
bond slot (no natural bond-slot analogue exists for these three) — they
stay at their generated-fresh (zero) default unless hand-tuned, an
honest residual, not silently patched over.

## Addendum — backend-agnostic visibility (registered after prediction 8,
## before its own measurement; the ORIGINAL 8 above are unchanged)

The user's own steer, after the first 8 predictions were already measured:
*"the idea is that the same data can be fed into LLMs if desired instead
of ocelot."* This is a real, previously-unaddressed gap, not a reframing
— `domains/bigville_disposition_apply.py` is an OCELOT-SPECIFIC consumer
(it writes Concept nodes on `substrate_rs`); an LLM backend has NO path
to the generated backstory through it. Bigville already has the right,
existing, backend-agnostic channel: `BigvilleGame._relationship_signal`
exposes held `tie_strength`/`band_code` on every actor's `ActorContext`
(`nearby_residents`), read by `PromptBuilder` for ANY backend
(`bigville/backends/{ocelot,llm,human,cheap}.py`) — landed THIS SAME DAY
(commit `1b79a0f`), and `world.set_relationship`/`TOWNSPEOPLE_50_
RELATIONSHIP_KIND` is the established (kind, signed-strength) convention
already used to seed pre-existing relationships (`from_townspeople_50`).

**Prediction 9**: `seed_generated_relationships(world, cast, seed)`
(new, `worlds/bigville_social_seed.py`) — bridging the SAME
`sample_people_in_life` draw into `world.set_relationship` — mints
exactly as many relationships as `sample_people_in_life` returns
triples, each readable back via `world.relationship(holder, toward)`
with the matching `kind`, and `feud`-kind relationships carry NEGATIVE
`strength` (matching `TOWNSPEOPLE_50_RELATIONSHIP_KIND`'s own
`"rival_of": ("feud", -0.8)` convention exactly), while every other kind
carries non-negative `strength`. Opt-in only (mirrors
`seed_workplace_relationships`'s own documented precedent) — a bare
`from_town100()` town's `_relationships` stays empty.

## Files

- `worlds/bigville_social_seed.py` (bigville repo, new; extended with
  `seed_generated_relationships`/`_world_strength`)
- `tests/test_bigville_disposition_seed.py` (bigville repo, new; extended
  with 3 backend-agnostic-visibility tests)
- `seeds/bigville_dispositions_cast100.json` (bigville repo, generated;
  copied into ocelot's `seeds/`)
- `domains/bigville_disposition_apply.py` (ocelot, new — the
  OCELOT-SPECIFIC consumer; one of potentially several backend consumers
  of the same generated data)
- `tests/test_bigville_disposition_apply.py` (ocelot, new)
- `docs/research/bigville/BIGVILLE_DISPOSITION_GENERATOR_RESULTS.md` (this
  rung's results, paired with this file)
