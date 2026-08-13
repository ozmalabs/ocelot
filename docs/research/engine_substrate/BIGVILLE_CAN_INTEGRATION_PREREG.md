# Per-resident Causal Attitude Networks for Bigville — PREREG

**Status: PREREG. Written before any `mt_*` call in this rung executes, and
before `bigville_cast100.json` is regenerated with the new trait.** Per this
project's standing discipline against post-hoc rationalization
(`CAN_BELIEF_QUANTIZATION_PREREG.md`, same convention): what follows is the
design, the grounding citations, and the predictions, written before the
live two-resident demonstration is run.

## 0. Charter

> "Ideally being able to have distributions of this similar to Psi would
> allow the Bigville demo to have a much more realistic and dynamic cast. It
> may not be entirely tractable, but we may be able to get some factors in."
> — followed, after discussion, by "yes, do them all."

Read precisely: extend `bigville_cast100.json`'s existing 12-field
drawn-Normal `params` pattern with a 13th, trait-level, MIXTURE-drawn
resolution parameter, and give each resident a real, individually
parameterized CAN belief network whose representational resolution is set
by that trait (modulated by the existing arousal-driven `resolution_level`
state). This is explicitly a WIRING rung, not a full-simulation rung: two
residents, one scenario, real measured numbers — not 100 residents on a
live tick loop.

## 1. What is already real (verified by direct read before building)

1. **`seeds/bigville_motivation.json`** (`bigville_motivation.json:6`)
   implements Dörner Psi / Bach MicroPsi + SDT: `Drive{kind,level,setpoint,
   weight}` nodes, `mv_urge` (urge = weight·max(0,setpoint−level)),
   `mv_arousal` (arousal = max urge; `resolution_level =
   max(0, 1 − res_gain·arousal)`, Yerkes-Dodson shape — high arousal drives
   resolution DOWN), `mv_switch` (hysteresis via `selection_threshold`).
   `resolution_level` here is a **STATE** variable, recomputed every time
   `mv_arousal` fires, driven by the agent's current dominant urge — not a
   per-agent trait.
2. **`seeds/bigville_cast100.json`** (100 residents,
   `worlds/bigville_town100_world.py:313-375`'s `generate_cast100`) already
   carries a `params` dict of 12 individually-drawn-Normal scalar traits per
   resident (`_PARAM_SPEC`, `bigville_town100_world.py:97-110`): `arousal,
   charm_weight, claim_weight, cred_on, hostile_weight, mood_bias,
   prior_others_trust, prior_self_worth, prior_world_safe, valence,
   w_spite, w_supergraph`. Each is drawn `Normal(mean, sd)` then clipped
   (`_draw_clip`, `:288-294`) — **simple clipped-Normal, not a mixture** —
   confirmed by direct read, not assumed. `test_cast100_migrated.py`'s own
   `test_drawn_params_have_variance` (`:76-80`) iterates `_PARAM_SPEC`
   only, so a 13th key added OUTSIDE `_PARAM_SPEC` (own draw path) does not
   collide with or get silently swept into that test — a new assertion is
   added for it explicitly (§5).
3. **`runners/dsl/src/can_ops.rs`** (read in full) confirms the structural
   fact this rung's scoping decision rests on: `mt_id: NodeID` in every
   function (`mt_concepts`, `mt_mean_field_marginal`, `mt_energy`,
   `audit_basin`, …) is used ONLY via `g.neighbours(mt_id,
   Some(has_concept_edge))` (`can_ops.rs:142-144`) and one node-attr read for
   `temperature` (`:207`, default 1.0 if absent). **`mt` does not need to be
   a distinct `Microtheory`-typed node — it only needs to be ANY node that
   owns `has_concept` edges to Concept nodes and optionally carries a
   `temperature` attr.** Concept state (`state`, `external_field`,
   `identity_field`, `target_state`) are stored as attrs **on the Concept
   node itself** (`can_ops.rs:33-48`), which is the load-bearing consequence
   for scoping (§2 below): if two Mts shared one Concept node they would
   share its σ/h/identity — genuine independence per resident requires
   DISTINCT Concept nodes per resident, not a shared vocabulary with only
   distinct edge weights.
4. **`tests/test_can_ops.py`** (`_fresh_substrate`/`_build_small_mt`,
   `:14-42`) is the exact, already-working calling convention: `_native.
   Substrate()`, `add_production` for the (Microtheory/Concept) ×
   (has_concept/causal_influence) admissibility pairs (Γ — `add_edge`
   enforces the admissibility grammar and raises `InadmissibleEdge`
   otherwise, confirmed by reading `py.rs:1714-1757`), `add_node("Concept",
   {...})`, `add_edge(mt, "has_concept", concept, {})`,
   `add_edge(a, "causal_influence", b, {"weight": ...})`. This rung reuses
   this convention exactly — no new Rust, no new node types, per the task's
   explicit scope bound.
5. **Real, already-wired Bigville topics a CAN network can attach to**
   (found by direct search, not invented):
   - `bd_villager_backs` (`seeds/bigville_drama_social.json:534-560`,
     comment at `:538`) computes `cred_john = seen_benevolent·charm_weight −
     seen_hostile·hostile_weight` vs. `cred_mary = heard_claim·(claim_weight
     − difficulty_penalty)` and decides whether a villager backs Mary's
     accusation against John — **using the exact same param names**
     (`charm_weight`, `hostile_weight`, `claim_weight`, `cred_on`) that
     `bigville_cast100.json`'s `_PARAM_SPEC` already draws per resident.
     This is the single most direct, reusable grounding available: two
     attitude objects ("is the mayor trustworthy," "is Mary's claim
     credible") already have a real formula in this codebase driven by
     exactly the scalar traits cast100 residents already carry.
   - `bl_townsfolk_opinion` / `Badmouth` (`seeds/bigville_loop_reputation.
     json:13-232`) generalizes the same standing-vs-testimony arithmetic
     town-wide: `backs_debtor` compares `standing` against
     `badmouthed·badmouth_weight` — a third real, reusable attitude object
     ("is this debtor trustworthy"), driven by `w_spite`/`hostile_weight`-
     shaped inputs.
   - The three foundational IWM/SDT priors (`bigville_town_seed.py:60-64`
     comment, same param names present in cast100's own `_PARAM_SPEC`):
     `prior_world_safe`, `prior_others_trust`, `prior_self_worth` — Bowlby's
     own theory holds these are CORRELATED in secure attachment (positive
     self-model and positive other-model co-occur), a real, literature-
     grounded coupling, not invented.
   - `market_fair`/`watch_effective`/`guild_loyalty`-style topics were
     checked and found **NOT wired anywhere** in the economy/trade/law
     worlds — excluded from this rung's Concept vocabulary as genuinely
     speculative, per the task's own instruction not to invent fictional
     topics.

## 2. Scoping decision (registered)

**Per-resident Microtheory, per-resident Concept nodes, shared Concept
NAMES/structure as a template.** Each of the two demo residents gets:
- one `Microtheory` node (`temperature` = β, held fixed at 1.5 across both
  residents — isolates resolution as the manipulated variable) linked from
  a `Resident` node via `has_belief_mt` (a new edge type, Γ-declared);
- **5 distinct `Concept` nodes**, all residents using the SAME five names
  as a template but each resident's own DISTINCT node instances (per point
  1.3 above — independence requires this): `trust_mayor`, `claim_credible`,
  `world_safe`, `self_worth`, `debtor_trustworthy`. All five map directly
  onto the real, already-wired formulas in §1.5.
- **5 `causal_influence` edges** (a sparse structural template, matching
  Bigville's own documented sparse-relationship philosophy —
  `bigville_town_seed.py`'s own `RELATIONSHIPS` comment: "NOT all-pairs —
  each inhabitant carries only a few ties"), same PAIRS for every resident,
  but J magnitude computed per-resident (§3) — not literally identical
  values, since the whole point (`bigville_motivation.json`'s own
  docstring, quoted in the task) is "different weight profiles diverge on
  the same world; uniform profiles collapse the divergence":
  1. `trust_mayor` — `claim_credible` (J<0 structurally: believing the
     accusation and trusting its target are in tension — mirrors
     `bd_villager_backs`' two-sided comparison directly)
  2. `trust_mayor` — `world_safe` (J>0: general safety-of-the-world belief
     supports trust in a specific authority figure)
  3. `world_safe` — `self_worth` (J>0: Bowlby IWM correlation, §1.5)
  4. `claim_credible` — `debtor_trustworthy` (J>0: a shared
     credulity/skepticism disposition — someone quick to believe one
     negative claim is quicker to believe another)
  5. `trust_mayor` — `debtor_trustworthy` (J>0: generalized institutional/
     social trust)

This is NOT a full multi-resident interaction network (residents do not
share nodes or influence each other's networks in this rung — that is
explicitly the next rung, per the task's scope bound) — it is 2 (or more)
fully independent, individually-parameterized 5-node CAN networks.

## 3. The trait-level resolution parameter — mixture design, cited

Per `CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md` §7 point 4 and
§8 point 2: **do not design around a single unimodal population curve** —
the real CRT literature shows a population is a MIXTURE of a floor-heavy/
naive subgroup and a ceiling-heavy/exposed subgroup, not one bell curve.
Two-component draw, in **continuous space** (the cross-frame generative
map, per `CLAUDE.md`'s BASE-AS-DIMENSION/frame-continuum invariant), then
**rounded and clamped to an integer bin count** (the in-frame stored
datum — the draw is a map, the storage is a lattice value):

- **floor component** (naive/general population): `Normal(mean=3.0, sd=1.0)`.
  Anchored to the research doc's §8 point 1 LOW end ("the LOW end (2–3)
  covers the CRT-style floor/coarse-vocabulary regime already tested
  directly in `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3, its own 'coarse'
  condition used `J ∈ {-1,0,+1}`, 3 values") and point 3 ("Anchor a
  'coarse' test condition to 2–3 bins").
- **ceiling component** (exposed/educated population): `Normal(mean=7.5,
  sd=2.0)`. Anchored to §6.3's convergent Miller (1956)/Preston & Colman
  (2000) finding (reliable single-dimension discrimination: 4–8, best
  psychometric performance at exactly 7) and §8 point 1's explicit
  instruction to extend the HIGH end slightly PAST both cited ceilings
  (9–12) "so a genuine 'too fine to be useful' regime is actually inside
  the tested window" — mean 7.5 sd 2.0 places most mass in 4–11, spanning
  both the convergent optimum and the deliberately-past-ceiling band.
- **mixing weight**: `P(ceiling component) = 0.35`. Grounded, not invented:
  Frederick's own combined N=3,428 sample (§2.1) found **17%** of
  participants answering all three CRT items correctly (the observed FLOOR
  of a "ceiling-leaning" subgroup's prevalence in a general/unfiltered
  population); Stieger & Reips' (N=2,137) university-degree/experienced
  cell scored 3/3 in **~33%** of cases (§2.2, "one-third… scored 3/3" — the
  observed prevalence within an educated/exposed SUBGROUP, an upper
  reference point for how large the ceiling-leaning share of a mixed
  population plausibly runs once exposure/education correlate with it).
  0.35 sits just inside that empirically-bracketed [0.17, 0.33] range as a
  single defensible point estimate, deliberately not tuned to produce a
  particular demo outcome (chosen and written down before either resident
  is picked for the live demo, §6).
- **range clamp**: `[2, 12]` integer bins — §8 point 1's full registered
  crossover-PREREG test range.

This is implemented as `_draw_resolution_bins` in
`worlds/bigville_town100_world.py`, called once per resident immediately
after the existing 12-param comprehension (so every existing param's RNG
draw sequence, and therefore its value, is byte-unchanged on regeneration —
verified in RESULTS via the existing `test_same_seed_identical_cast_and_map`
gate).

## 4. State/trait interaction — registered before measuring

`resolution_level` (state, `bigville_motivation.json`'s `mv_arousal`) and
the new `resolution_bins` (trait, this rung) are different UNITS — one a
[0,1] continuous modulator, the other an integer bin count — so they cannot
simply be added. **Design: trait sets the CEILING; state scales a FRACTION
of it (multiplicative, then re-quantized to the integer lattice)**:

```
effective_bins = max(2, round(resolution_bins · resolution_level))
```

where `resolution_level = max(0, 1 − res_gain·arousal)` reuses the EXISTING
`mv_arousal` formula verbatim (no redesign needed — confirmed clean,
additive composition, not a case requiring `resolution_level`'s own
mechanic to change). `res_gain = 1.0` is used for this rung's demo (a
documented, honestly-labeled DEMO CHOICE, not a fitted/measured value —
`bigville_motivation.json`'s `res_gain` is per-agent-declared and is not
currently set anywhere for cast100 residents, since cast100 and
bigville_motivation have zero existing connection, confirmed by grep before
this rung began). With `res_gain=1.0` and cast100's own `arousal` param
already clipped to `[0,1]` (`_PARAM_SPEC`), `resolution_level` stays in
`[0,1]` cleanly. The floor of 2 matches the same floor used for the trait
draw itself (below 2 bins there is no discriminable distinction possible —
a degenerate unary "on/off" case the substrate's own `distance_to_target`
"Unknown = zero vector" convention already treats as the natural floor).

**Honest limitation, registered before measuring**: this composition is
NOT wired as a live graph rule in this rung (no `set_attr` production
computing `effective_bins` inside `run_rules`) — per the task's explicit
scope bound ("does NOT need to wire full multi-resident interaction, full
simulation-tick integration"), it is computed once, mechanically, at
demo-setup time, exactly the same class of operation
`CAN_BELIEF_QUANTIZATION_PREREG.md §2.2` already used to build its
coarse/fine J-vocabularies (test-harness/demo setup, not a live agent
decision). Wiring it as a `bigville_motivation.json` rule (so
`effective_bins` recomputes every tick as arousal changes) is named as
clean, straightforward follow-on work, not built here.

## 5. What `effective_bins` DOES to the network — the quantization mechanism

Per the creator's own words (quoted in `CAN_BELIEF_QUANTIZATION_PREREG.md
§0`): "lower metacognition leads to lack of nuance — this can be
mechanically explained by the quantisation of causal linkage." This rung
reuses that EXACT mechanism (already validated in the prior CAN rung,
`CAN_BELIEF_QUANTIZATION_RESULTS.md`), now driven by a real per-resident
trait instead of a hand-set experimental condition:

1. For each of the 5 structural edges (§2), a **"true" continuous coupling**
   is computed from a fixed structural base value (same conceptual
   relationship for every resident — "believing the accusation opposes
   trusting its target" is a real, general claim) PLUS a small per-resident
   nuance term drawn from that resident's OWN real params (`mood_bias`,
   `w_supergraph` deviation from the population mean) — isolating
   resolution as the manipulated variable while keeping the "true"
   relationship genuinely resident-specific, not a shared constant (mirrors
   `CAN_BELIEF_QUANTIZATION_PREREG.md §2.2`'s own "same true draw, only the
   ENCODING differs" isolation discipline, extended so the "true" draw
   itself is grounded in real per-resident data rather than a synthetic
   `Uniform(-1,1)`).
2. That continuous value is **quantized to the resident's own personal
   vocabulary**, sized by `effective_bins`: `k` evenly-spaced levels across
   `[-1, +1]` (`linspace(-1, 1, effective_bins)`), nearest-level rounding —
   the exact "vocabulary size" mechanism `CAN_BELIEF_QUANTIZATION_PREREG.md
   §2.2`'s coarse (`k∈{-1,0,+1}`, 3 values) / fine (9 values) conditions
   already used, generalized from a fixed 2-level experimental manipulation
   to a per-resident-real integer.
3. `identity_field` per Concept is set directly from the resident's own
   long-standing priors (`prior_world_safe`, `prior_self_worth`,
   `prior_others_trust`, scaled `2·(p−0.5)` to `[-1,1]`) — NOT quantized,
   since identity is a continuous personality attribute, not "causal
   linkage" resolution, per `can_ops.rs`'s own doc comment that identity
   "is NEVER frozen" and is architecturally distinct from `J`.
4. The SAME scenario evidence is injected identically into both demo
   residents via `concept_apply_evidence` (§6) — holding the "what happened
   in the world" input fixed so any measured difference in outcome is
   attributable to resolution, not to different evidence.

## 6. Live demonstration — design, registered before running

Two residents are selected from the real, regenerated
`bigville_cast100.json`: the one with the LOWEST `resolution_bins` among
the 100 and the one with the HIGHEST, breaking ties by index order (a
mechanical, non-cherry-picked selection rule, fixed before the population
is drawn). Both get a personal CAN network built per §2–5. The SAME
scenario evidence — "the town witnesses a public, hostile confrontation
between Mary and John" — is applied identically to both:
`concept_apply_evidence(claim_credible, evidence=+1.0, alpha=0.6)` and
`concept_apply_evidence(trust_mayor, evidence=-0.6, alpha=0.6)`. Both
networks are then relaxed (`mt_relax_to_marginal`) and audited
(`mt_audit_basin`), plus a 20-restart multi-start sweep (smaller than
`CAN_BELIEF_QUANTIZATION_PREREG.md`'s 40, since N=5 is far smaller than
that rung's N=4/8/16 complete graphs — proportionately fewer restarts are
needed to survey a 5-node state space) reseeding each Concept's `state` to
an i.i.d. `{-1,+1}` choice, to get a basin-COUNT reading (mean-field alone
only reports the ONE basin reached from whatever `state` currently holds —
confirmed already true of `audit_basin` by `CAN_BELIEF_QUANTIZATION_
RESULTS.md` Q2, re-verified by direct read of `can_ops.rs:400-436` again
in this rung).

**Predictions, registered before running:**
1. The coarse (low-`effective_bins`) resident's quantized edge weights will
   show a HIGHER mean absolute rounding error vs. the "true" continuous
   values than the fine resident's (near-definitional manipulation check,
   reported as such, not as a finding).
2. Per this project's own prior finding on this exact mechanism
   (`CAN_BELIEF_QUANTIZATION_RESULTS.md`'s own honest null: coarse did NOT
   show fewer/shallower basins than fine at small N — the opposite trend
   was measured at N=4/8), **no directional basin-count prediction is
   registered as the primary expectation** — this rung explicitly does NOT
   assume the naive "coarse → fewer states" intuition, since it was already
   falsified once on this exact engine. What IS predicted, following that
   prior rung's OWN positive finding instead: the coarse resident's
   mean-field/basin outcomes should show measurably **higher frustration
   and/or a shallower dominant-basin margin** (the prior rung's actual
   confirmed direction — coarse's landscape being "less STABLE," not
   "less numerous").
3. **Honest null, registered as fully acceptable**: if frustration,
   coverage, and basin count all land within noise of each other between
   the two residents, that is reported as a clean null — this rung's N=5,
   5-edge network is much smaller than the prior rung's N=4/8/16 complete
   graphs, and a null here would be informative about a floor effect
   (network too small for resolution to matter), not silently
   reinterpreted as confirmation.

## 7. What this rung explicitly does NOT do

Per the task's own scope bound: no full multi-resident interaction (no
resident's Concept nodes couple to another resident's), no live
simulation-tick integration (no `run_rules` fixpoint recomputing
`effective_bins`/relaxing networks every tick), no Matthew-effects/
collapse-failure-avoidance-learning mechanism (explicitly the next rung),
no shape-recognition/compression tractability layer (named as future work
in `CAN_BELIEF_QUANTIZATION_PREREG.md §4.5` already, untouched here), no
new Rust Term or `can_ops.rs` function (the existing PyO3 surface is
sufficient, confirmed in §1.4 before writing any code).

## 8. Worktree

`/home/matt/ozmadev/ocelot-worktrees/bigville-can-integration`, branch
`bigville-can-integration`, base `main @ d061b2d`.
