# Bigville disposition generator — RESULTS

Registered design: `BIGVILLE_DISPOSITION_GENERATOR_PREREG.md`. **All 9
predictions confirmed** (4 bigville-side, 4 ocelot-side, 1 addendum).

## 1. Live runs

### Bigville side (`worlds/bigville_social_seed.py`, sibling repo)

```
P1 reproducibility byte-identical: True
P2 homophily: same-role rate=0.2527 baseline=0.1024 ratio=2.47x
P3 distribution shape: mild=0.882 extreme=0.000 n=558
P3b kind distribution: {'acquaintance': 299, 'blood_kin': 65, 'chosen': 128, 'feud': 66}
P4 total bonds=558 residents=100 avg=5.58
```

### Ocelot side (`scripts/bigville_disposition_apply_demo.py`)

```
=== Prediction 4: group membership (own buckets + one out-group) ===
resident=Verity Peaseblossom groups=['class:poor', 'group:high', 'group:low', 'role:labourer', 'workplace_kind:market']

=== Prediction 5: override wins, no accumulation with generated ===
generated belief_trust would have been -1.0000; override=1.75; applied external_field=1.7500

=== Prediction 6: override-only person with no generated bond ===
Verity Peaseblossom in generated bonds? False ; applied via override? True

=== Prediction 7: self-belief domain = role ===
resident=Barnaby Furlong role=labourer self={'self_efficacy': -0.6892, 'deservingness': -0.1436}

=== Prediction 8: per-resident isolation ===
B present before B applied? False
B present after B applied? True
```

### Addendum: backend-agnostic visibility (`seed_generated_relationships`)

```
relationships before: 0
minted=558 triples=558 match=True
feud example: Garnet Hollow -> Horace Yarrow strength=-2.0000 kind=feud
blood_kin example: Verity Peaseblossom -> Ida Ditchwater strength=1.0000 kind=blood_kin
```

## 2. Predictions

1. **Reproducibility** — `PASS`. Two in-process `generate_disposition_seed(305000)`
   calls are dict-equal.
2. **Homophily** — `PASS`, and comfortably past the 1.5× registered bar:
   same-role partners are chosen at **2.47×** the uniform-random baseline
   rate (25.3% observed vs. 10.2% baseline implied by role population
   share).
3. **Distribution shape** — `PASS`. 88.2% of the 558 generated bonds have
   `|belief_trust| < 0.5` (bar: >60%); **zero** are `>= 1.5` (bar: <15%).
   This falls out of `bigville_bond_world.PRIORS` honestly:
   acquaintance (299) and chosen (128) — 76.5% of all bonds — carry
   `belief_trust=0.0` by that table's own design; only `feud` (66,
   `belief_trust=-1.0`) and `blood_kin` (65, `belief_trust=0.0` too,
   since `PRIORS["blood_kin"]` only sets `genetic_kin`/`altruism_bias`/
   `tie_strength`) contribute any variation at all — "most relationships
   are unremarkable" is the REAL shape of the reused prior table, not a
   filter added to make this prediction pass.
4. **Group membership** — `PASS`. Every sampled resident's `groups` list
   is exactly the 4 owned buckets (`class:`, `group:`, `role:`,
   `workplace_kind:`) plus exactly one `group:<opposite-tier>` out-group
   bucket (5 entries total, confirmed for `Verity Peaseblossom`:
   `class:poor`, `group:low` (own) + `group:high` (out), `role:labourer`,
   `workplace_kind:market`).
5. **Override precedence, no accumulation** — `PASS`, and the sharpest
   confirmation: the target's GENERATED `belief_trust` would have been
   `-1.0000` (a `feud`-kind bond); the override `regard=1.75` landed the
   Concept's `external_field` at exactly `1.7500`, not `0.7500`
   (`-1.0 + 1.75`) — confirming the pre-resolve-then-apply-once design
   actually prevents the additive-`concept_apply_evidence` accumulation
   bug the PREREG named as the most failure-prone claim.
6. **Override-only additions** — `PASS`. A target absent from every
   generated bond (`Verity Peaseblossom` was not in `CAST[20]`'s sampled
   bonds) is still minted and carries the override's `admiration=0.9`.
7. **Self-belief domain = role** — `PASS`. `Barnaby Furlong` (role
   `labourer`) got `self_efficacy_for:labourer` / `deservingness_
   belief_for:labourer` landed exactly at the generated prior values
   (`-0.6892`, `-0.1436`), on the same Microtheory as his own `self_worth`
   / `trust_mayor` Concepts, no name collision.
8. **Per-resident isolation** — `PASS`. Resident B's `Resident` node does
   not exist until B's own `apply_resident_dispositions` call runs, even
   after A's has already run.
9. **Backend-agnostic visibility (addendum)** — `PASS`.
   `seed_generated_relationships` minted exactly 558 relationships (=
   `sample_people_in_life`'s own 558 triples, same draw); every `feud`
   relationship's `strength` is negative (`Garnet Hollow -> Horace
   Yarrow`: `-2.0000`), every other kind's is non-negative (`blood_kin`
   example: `1.0000`) — matching `TOWNSPEOPLE_50_RELATIONSHIP_KIND`'s
   own `("feud", -0.8)` sign convention exactly. A bare `from_town100()`
   town's `_relationships` stays empty (opt-in confirmed).

## 3. Honesty notes

**Does establish**: a working generate/apply split across the two-repo
boundary (`docs/features/bigville.md`'s stated adapter boundary), reusing
— not reinventing — bigville's own `_draw_clip`/RNG-stream convention and
its own `bigville_bond_world.PRIORS` kind vocabulary, and ocelot's own
target-scoped/domain-scoped Concept families built across Phases A-G plus
`RESIDENT_TRUST_PREREG.md`/`SELF_EFFICACY_PREREG.md`/`ENVY_PREREG.md` —
zero new Concepts, zero new engine code. Confirms the additive-evidence
override hazard named in the PREREG was real and is actually prevented
by resolving (target, aspect) to one value before any
`concept_apply_evidence` call. Confirms Tajfel et al. 1971's minimal
group paradigm needs no rich justification: an arbitrary SES-tier bucket
carries a real, generated, hand-tunable disposition exactly like a named
person does. **Confirms the user's own architectural correction**: the
generated backstory is NOT ocelot-exclusive — `seed_generated_
relationships` puts the identical draw on the SAME `ActorContext.
nearby_residents` channel every backend already reads
(`bigville/backends/{ocelot,llm,human,cheap}.py` via `PromptBuilder`),
so an LLM backend sees a resident's pre-existing feuds/kin/friends
exactly as an Ocelot backend does, without either depending on the
other. `domains/bigville_disposition_apply.py` remains real and useful
— it is Ocelot's OWN deeper projection (into `regard_for`/trust/
resentment_debt/etc), not the only projection.

**Does NOT establish**: relationship DYNAMICS over time — this is a
STATIC backstory prior; `BigvilleBondWorld.tick()`/`hear_gossip`/
`experience_event` (gossip spread, tie erosion) are real, existing
mechanisms in bigville that this rung does not call or consume.
`admiration_for`/`pity_for`/`controllability_for` have no bond-slot
analogue and are NOT generated (only reachable via hand-tuned override)
— an honest, named residual, not silently patched. Does not regenerate
or touch `bigville_cast100.json`'s own 13 `_PARAM_SPEC` params — fully
additive, confirmed by `test_streams_isolated_from_cast100_and_each_
other` (bigville-side). Does not project into townview's `rels` display
schema — named follow-on in the plan, not built here.

## 4. Files

- `docs/research/bigville/BIGVILLE_DISPOSITION_GENERATOR_PREREG.md`
- `docs/research/bigville/BIGVILLE_DISPOSITION_GENERATOR_RESULTS.md` (this file)
- `../bigville/worlds/bigville_social_seed.py` (sibling repo, new; incl.
  `seed_generated_relationships`/`_world_strength`)
- `../bigville/tests/test_bigville_disposition_seed.py` (sibling repo, new, 11/11)
- `../bigville/seeds/bigville_dispositions_cast100.json` (sibling repo, generated)
- `seeds/bigville_dispositions_cast100.json` (copied from the sibling repo)
- `domains/bigville_disposition_apply.py` (new)
- `tests/test_bigville_disposition_apply.py` (new, 8/8)
- `scripts/bigville_disposition_apply_demo.py` (new)
