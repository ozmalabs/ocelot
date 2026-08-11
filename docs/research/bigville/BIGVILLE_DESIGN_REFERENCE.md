# Bigville — Design Reference & Duplication Audit

> Status: engineering reference, 2026-07-31. Purpose: make future bigville
> capability work **reuse the canonical primitives** instead of reinventing
> them, and record what already exists and what is known-broken. Every claim
> below was read from the actual seed/world/memory files; rule and node names
> are cited verbatim. Where a mechanism was not verified, it is flagged.

---

## 1. Purpose & scope

**Bigville** is a live "glass-box town" of graph-resident cognitive agents — a
society simulation built on the (G, Γ) typed-graph substrate. Townspeople have
drives, affect, bonds, memory, jobs, coin, property, health, and a place on a
grid; they work, trade, gossip, fall ill, grieve, scheme, steal, and are
governed by recognized law. It is the social analogue of "jabberwock plays
Doom": one Rust runtime executing graph data, no per-step LLM.

The subsystem is large — ~100 `bigville_*.json` seeds, ~80 `bigville_*_world.py`
adapters, ~130 `BIGVILLE_*.md` prereg/results docs. That size is the problem
this document solves. A builder adding a new capability should be able to answer
two questions from this doc alone:

1. **Does this already exist, and how do I reuse it?** → §3 (canonical
   primitives), §4 (seed inventory).
2. **What is known-broken or duplicated?** → §6 (audit).

Do **not** invent a new recognition mechanism, a new relationship scalar, a new
verdict rule, or a new affect node without checking §3 and §6 first. Several
already have canonical forms, and at least one (recognition) is currently
duplicated three ways — see §6.

Canonical framings (project memory): `ozma_world_facts_vs_human_frames`,
`ozma_agent_decision_is_a_collapse`, `ozma_town_time_is_the_bell`,
`ozma_bond_is_first_class_interpersonal_affect`, `ozma_maem_cognitive_core`.

---

## 2. The architecture rule (supreme constraint)

From `gamma-substrate/CLAUDE.md`. **The agent is a graph running in Rust.
Python is only the world adapter.** Every agent *decision* is a graph
Rule/collapse expressed as data, never Python control flow.

The split:

- **Rust runtime (`substrate_rs`)** runs the graph: matches Rules, evaluates
  Term-trees, fires Reflexes, schedules ticks, serialises/deserialises, runs
  primitive ops. The agent's reasoning **is** graph data (Rules, Concepts,
  Microtheories, Frames, Reflexes, Productions).
- **Python world adapter** does exactly two things: **ingest** (external event
  → substrate nodes/edges) and **emit** (read graph state → external output),
  with `substrate.tick()` / `run_rules()` between. ~50–100 lines each. A thin
  I/O-boundary classifier is tolerated only when it converts an opaque external
  form to the smallest graph token and no Rust primitive can do it.

**Hard NOs (do not write these in Python):**

- No Python rule engine (`gr.run`, `_match`, `_apply`, `make_rule`) in new code.
- No `if`/`else` that reads graph state and decides what the agent does next —
  that is a **Rule**.
- No Python object holding agent state (concept index, rule list, etc.). State
  lives in the substrate; Python may cache, never own.
- No Python helpers wrapping reasoning (`recognise_X`, `revise_Y`, `decide_Z`).
- No constructing the agent at runtime — seeds boot it (`boot_core`).

When the DSL genuinely can't express something, the escape hatch is **Rust**: a
new DSL `Term` (`runners/dsl/src/term.rs`), a graph op
(`runners/dsl/src/substrate.rs`), exposed via PyO3 (`runners/dsl/src/py.rs`) as
a one-line handoff. Never "primitive in Python," never "composition in Python."

For bigville specifically this means: a townsperson's every choice — whom to
recognize, whether it was theft, guilty or not, whom to help, whether to
enforce — is an `Argmax`-collapse Rule reading that agent's own params. The
adapter only ingests world events and reads results.

---

## 3. Canonical primitives & patterns to REUSE

This is the heart of the reference. Each primitive gives: what it is, the graph
shape, the seed that defines it, and when to use it.

### 3.1 Agent-decision-is-a-collapse (THE decision idiom)

**Never** a threshold, comparator, or `IfThenElse` over one input. A decision is
an `Argmax` over candidate **stance nodes**, valued by a Term that reads the
**deciding agent's own held params**. Because the value Term reads the agent's
own attributes, identical evidence yields different verdicts — agents **diverge**
structurally. Setting every disposition equal collapses everyone onto one
verdict: that is the built-in falsifier.

Canonical shape (`ozma_agent_decision_is_a_collapse`):

```
set_attr r <choice_key>
  Attr(
    node = Argmax(
      source = NodesOfType("<Stance>"),   # the candidate menu
      var    = s,
      value  = Times(                      # sign · <term in the agent's own params>
                 Attr(s, "sign"),          # +1 for the pro pole, -1 for the con pole
                 <lean: mixes r's own attrs with the situation>)),
    key = "label")                         # read the winning stance's label
```

**Stance-node convention:** each candidate is a node `{label, sign:±1}` (e.g.
`{label:"recognize", sign:+1}`, `{label:"reject", sign:-1}`). The `Argmax`
maximises `sign · lean`, so the pro pole wins iff `lean > 0`. The chosen
`label` is written to the agent; a follow-up "grant" rule reads that label and
adds the committing edge (see 3.3).

**Canonical generic faculty:** `seeds/agent_judgment.json` (block 312000),
rules `jc_conclude` / `jc_act`. `jc_conclude` sets
`Conclusion.verdict = Attr(Argmax over graded signed Stance nodes valued by
-(stance.pole - lean)², "label")` where `lean` mixes evidence·credence +
disposition − deference·subject_standing. `jc_act` enacts a condemning
conclusion by that agent's own sanction, only when `town.acting==1` (so
deliberation reads original standing; action applies after — no within-fixpoint
cascade). **`bigville_court` composes this** (`depends_on: [..., agent_judgment]`).

Live examples of the same family: `rc_recognize` (recognition),
`th_recognize_theft` / `th_vote` / `con_duty` (theft), `own_decide`
(ownership), `af_choose_action`, `nd_choose_good`, `ss_choose_burn` (drama
scheming), `bt_decide_sleep`, `gg_orient_choice`, `bs_teach_willing`.

### 3.2 World-fact vs human-frame

The uniqueness thesis (`ozma_world_facts_vs_human_frames`,
`BIGVILLE_FACTS_VS_FRAMES.md`). For **every** effect that mutates a
body/coin/property/standing/office, ask: world-fact or human-frame?

- **WORLD-FACT** — the engine may enforce unconditionally: a body loses health
  and dies; a struck body is harmed; coin is conserved; a deposit has finite
  stock; a sound is heard in earshot; a bell rings; a tired body sleeps.
  **Any agent can cause any death, including the mayor's — no role is exempt.**
  Examples: `rc_strike` (kill), `th_take` (take what another holds), `bl_death`,
  `bl_acute`, extraction/conservation rules.
- **HUMAN-FRAME** — real for an agent only if that agent RECOGNIZES it: a law's
  bindingness, an office's authority, property, money-as-medium, a verdict, a
  censure's sting, who is "on the council." Must be agent-held and contestable.
- **SMUGGLED (the anti-pattern)** — a rule whose effect fires the moment a
  status attr is set, with no recognition, no reach, no enactor. A frame wearing
  physics' clothes. Do not write these.

Two hard invariants: **never fire a frame on a status attr alone** (it must be
recognized by the affected agent AND enacted by an agent with reach), and
**never let the substrate forbid a usurpation** (a title is inert; nothing the
engine does may make a frame un-contestable).

### 3.3 Recognition = Count(recognizers)  ← THE canonical frame primitive

Authority, ownership, and office are all **recognition**, never a hardcoded
edge/flag. The shape is identical everywhere:

```
set_attr <claim> "authority" (or "recognition")
  Count(InNeighbours(<claim>, "recognizes"))     # emergent, never a fact
```

Recognition is *granted* by a per-agent collapse (3.1): each agent decides
`{recognize, reject}`; a "grant" rule reads the `recognize` label and adds the
`recognizes` edge; the count rule then reads authority off the edge population.
A decree/effect under the claim is **recognition-gated** by matching
`r -recognizes-> claim` in the rule — a rejecter never matches and is untouched
(`rc_decree_tribute`).

Defined in **`seeds/bigville_recognition.json`** (block 324000, R33):
`rc_strike` (world-fact kill), `rc_recognize` (the `{recognize,reject}` collapse
valued by `fear_weight·claimant.shown_force + opportunism − loyalty_prior`),
`rc_grant` (commit the `recognizes` edge), `rc_authority`
(`Count(InNeighbours "recognizes")`), `rc_decree_tribute` (recognition-gated
effect).

The falsifier that proves it's a frame: the same physical taking of property
**nobody** recognizes → standing 0 → not a crime.

**Reuse this for any new office/title/property/law.** As of this writing it is
reimplemented three times (see §6.1); prefer `bigville_recognition` and depend
on it rather than re-authoring the `recognizes`-count pair.

### 3.4 Bond(A→B) — the first-class interpersonal-affect model

**"How A feels about B" already exists. Do NOT invent a scalar `regard`/
`affinity`/`loyalty` attr or a new node** (`ozma_bond_is_first_class_interpersonal_affect`
— this was corrected twice on the constable case).

The model (`seeds/bigville_bond_update.json`, block 277000; world
`worlds/bigville_bond_world.py`): a **per-agent, directed, subjective,
updatable** bond held as

```
A -holds_bond-> Bond -toward-> B
```

Three dissociable slots on the `Bond` node:

- **six signed relational emotions**: `affect_affection`, `affect_resentment`,
  `affect_trust`, `affect_gratitude`, `affect_contempt`, `affect_fear`;
- **belief / ToM slot**: `belief_trust`, `predicts_harm_rate`, `disp_code`
  (decode B's observed signature against a held DispositionGenerator codebook —
  generalizes `bd_mary_infers`);
- **approach-avoidance**: `attraction` (+ a romantic sub-value), over a graded
  `tie_strength` and an earned `band`.

**To read warmth ("how A feels about B") do exactly this:** match
`A -holds_bond-> bond`, `bond -toward-> B`, and read

```
affect_affection − affect_resentment      # the canonical warmth scalar
```

This is precisely what `bigville_fast_bond` (`fb_fast_bond`, block 287000) reads
to nudge a directed impulse, and what `con_duty` reads for constable
forbearance. **Compose `bigville_bond_update` for the dynamics** rather than
duplicating them — 7 `bond_*` rules already evolve the feeling from social
events: `bond_belief_infer`, `bond_event_benefit` (reciprocity up),
`bond_event_betrayal` (down harder — negativity bias), `bond_gossip_update`
(third-party), `bond_similarity_attraction`, `bond_proximity_familiarity`,
`bond_band_assign`.

Directed conduct that reads bonds: `bigville_conduct` (`conduct_couple_harm/
help/transfer`), `bigville_supergraph_conduct` (`conduct_supergraph_value`),
`bigville_speech_decide`.

### 3.5 Self-affect stack (distinct from Bond — this is about the self)

Bond is interpersonal. The **self's** affective state is a separate, also
first-class stack. Which seed owns which:

| Layer | Seed | Node / mechanism |
|---|---|---|
| Base affect contract | `affective_state_core.json` | every agent owns a neutral `AffectiveState` (valence, arousal); Psi `ModulatorState` projects into it; `psi_select_initial_leading_drive` / `psi_switch_leading_drive` / `psi_project_canonical_affect` |
| Drive system | `drives.json` (block 207000) | `Drive{name,v_d,c_d,v_0,weight,decay,gain,loss,half_life}`; MicroPsi demand eqns (`drive_urge`, `drive_urgency`, decay) |
| Modulator space | `modulators.json` (207000) | `ModulatorState`; emotions as regions (`emx_fear/anger/joy/grief/...`) set by drives |
| Window of tolerance + co-regulation | `arousal_window_coreg.json` (239000) | `WindowOfTolerance` [lo,hi]; `dysreg_onset_hyper/hypo`; `coreg_pull` (a regulated caregiver widens the window); `episode_resolve_widen/narrow` |
| Window as a settable knob | `window_knob_coreg.json` (241000) | formal width knob + bidirectional dyad |
| Frustration / snap | `snap_frustration.json` (242000) | accumulating frustration residual crossing the upper bound → `snap_threshold_fire` |
| Attachment | `harlow_attachment.json` (233000) | infant `EmotionHub`; contact-comfort vs feed mother; `hl_select_initial_target` / `hl_switch_target` |

Rides the **real** `AffectiveState.arousal` — new affect work should hook this,
not mint a parallel arousal attr. The bigville-side affect faculties
(`bigville_affect_*`, `bigville_stress`, `bigville_motivation`,
`bigville_attention`, `bigville_flow`, `bigville_memory`) all reuse this stack.

### 3.6 Bell-time — no forced global clock

`ozma_town_time_is_the_bell`. **There is no global `now`/`day`/`sunday` flag.**
Time is a shared *perceptual event*: the church bell.

`seeds/bigville_bells.json` (block 320000): the church `has_bell` a `Bell`; the
sexton rings it (one exogenous act, `ring_armed`); `bl_ring` emits a
`BellPeal{hour,kind,call_strength}`. Each agent **learns the hour by hearing**
(`bl_hear_awake` sets `known_hour`; an agent who hears no bell never knows the
time — unknown = absence) and **chooses** its response by collapse
(`bl_wake_rested`, `bl_decide`, `bl_attend`). Scheduling rides bell counts, not
a modulus: `bigville_bell_schedule` / `bigville_council_bylaw` (`cb_beadle_counts`
increments on each curfew peal; the interval is a held `Bylaw`/`Law`, not
`now_day % cadence`).

**Do not** introduce a forced counter. Measured remnant (block 348000, §6.8):
the ONLY genuine `Mod(<global-day>)` forced clock left is
`bigville_council_gov`'s `cm_convene` (`Mod(now_day,cadence)`), and it is already
superseded by the bell-time `bigville_council_bylaw` (`cb_beadle_counts`).
`now_epoch > due_epoch` term-expiry comparisons in the econ seeds are legitimate
in-frame integer timestamps, not this defect.

### 3.7 Conservation & the effect-ordering ("store-first") rule

**Coin/material is conserved.** Every transfer credits one account and debits
another for the same amount; boundary crossings are logged (`bw_inn_stay`'s
`external_influx`). Dedicated conservation seeds: `bigville_integ2_conserve`
(closes the R4/R17 wage leak — every affect-outcome coin move gets a matching
counter-move against a `WagePool`).

**Effect ordering (load-bearing engine fact).** Within a `batch:false` rule,
effects apply **sequentially**. Consequences:

- An effect that **writes** an attr must come **after** every effect that
  **reads** it (the C6 `ac_work` precedent: `store += min(yield,stock)` must be
  ordered before `dep.stock -= min(yield,stock)`, else the second reads the
  already-written value).
- When a value depends on several attrs you **also** mutate, **store the
  computed amounts first, then transfer against the stable stored values** —
  the "store-first" pattern. Canonical example `th_collect` (its own comment
  says so): the collected `take_dmg`/`take_fine` amounts are written onto the
  offense **first**, then every coin transfer reads those stable stored values,
  so the take terms don't re-read `debt_damages` after it is mutated.

If you write coin/resource transfers, walk the effect list in order and check
every read happens before the corresponding write.

### 3.8 The two-incoming-edge matching gotcha

Documented in `CLAUDE.md`: **two same-type incoming edges on one node can break
`run_rules` matching for that edge type.** A corollary the matcher relies on: a
matcher will not bind two distinct match-vars to the *same* node for the same
edge pattern. Practical effects in bigville:

- Give a "shortcut"/second relation a **distinct edge type** to avoid the
  collision (the writer-dims precedent used `wrote_transform` for exactly this).
- Role-distinctness (a theft witness must not be the owner or the taker) is
  currently enforced with **explicit `Not Eq` guards** — `th_take` has
  `Not Eq(taker, holder)`, `th_recognize_theft` has `Not Eq(taker, owner)`.
  Prefer explicit guards over relying on the binding quirk when the distinctness
  is semantically required.

When a rule "silently doesn't fire," suspect duplicate incoming edge types
before anything else.

### 3.9 Epoch-guard once-per-pulse

Per-epoch decay/streak/metabolism/collection rules must fire **once per pulse**
without a fixpoint loop. The pattern: gate the rule on an epoch-counter / armed
flag that the effect advances, so it matches exactly once per pulse (the
memory/stress/flow/action precedent). Examples: `bigville_action`'s
`ac_metabolize`, `bigville_memory`'s `mem_decay`, the beadle's
`cb_beadle_counts` (once per curfew peal), `bi2_*` sinks (`wsink_armed`). Use an
`*_armed` flag set by the adapter as mechanical world-delivery when the pulse is
exogenous (e.g. `journal_armed`).

### 3.10 Canonical Agent attribute vocabulary (audit 6.5)

There is no `Agent` *node type* in bigville — an "agent" is any node a faculty's
collapse reads decision params off (a `Villager`, a cast `resident`, a
`Councillor`, a juror). Attribute names have historically been coined per-seed.
This is the **canonical vocabulary** a new faculty should draw from before
minting a fresh param; the drawn-Normal defaults are the cast generators'
(`scripts/bigville_town_seed.py` for the 30-cast, `worlds/bigville_town100_world.py`
for the 100-cast). **Kind** fixes the range: `lognorm` is strictly `>0`
(unbounded above, ~1.0-centred multiplier), `logit` is bounded `(0,1)`, `normal`
is unbounded signed, `int`/`bool` are exact in-frame integer state (§3.6/§3.7).

**Universal state (every embodied agent carries these; world-facts, §3.2):**

| attr | kind | meaning |
|---|---|---|
| `coin` | int | conserved money (§3.7 — never magicked) |
| `alive` | bool | liveness world-fact |
| `energy` / `hunger` / `health` | int/lognorm | metabolic state (`bigville_move_energy`, `bigville_action`) |

**Affect (ride the real stack, §3.5 — do NOT mint a parallel arousal/valence):**

| attr | kind | base·sd | read by |
|---|---|---|---|
| `arousal` | logit-ish | — | `AffectiveState.arousal`; MAEM attention/flow/stress |
| `valence` / `mood_bias` | normal | 0.0·0.3 | mood-toned collapses |
| `w_supergraph` | lognorm | 1.0·0.45 | emotion-regulator weight (self-editable instinct) |
| `w_spite` | lognorm | 0.06·0.6 | spite drive weight (`snap_frustration`, conduct) |

**Social / decision params (the collapse-lean inputs, per §3.1):**

| attr | kind | base·sd | primary faculty |
|---|---|---|---|
| `charm_weight` | lognorm | 1.2·0.55 | persuasion / reputation |
| `claim_weight` | lognorm | 2.0·0.3 | how strongly a claim is pressed |
| `cred_on` | lognorm | 1.0·0.12 | credibility given to others |
| `hostile_weight` | lognorm | 1.0·0.3 | hostility appraisal |
| `difficulty_penalty` | lognorm | 1.0·0.35 | effort aversion |
| `fear_weight`, `opportunism`, `loyalty_prior`, `shown_force` | lognorm/normal | (recognition) | `bigville_recognition` lean: `fear_weight·force + opportunism − loyalty` |
| `lawfulness`, `deference`, `prop_skepticism`, `doubt`, `duty`, `legitimacy`, `alliance_to_taker` | lognorm/logit | (theft) | `bigville_theft` leans (ownership grant / juror / duty) |
| `snap_pressure`, `spite` | lognorm | (conduct) | violence / conduct collapses |
| `role_identity` | string | — | labour/cast role tag (`bigville_cast100`) |

**Three foundational priors** (Bowlby/Erikson setpoints, `ozma_three_foundational_priors`;
logit, base 0.6·sd 0.55): `prior_world_safe`, `prior_others_trust`, `prior_self_worth`.

**Rule of thumb.** Before adding a new decision param, check this table: reuse
the canonical name and kind if one fits (a lean should compose existing params,
not coin synonyms). A genuinely new dimension is fine — add a row here and draw
it in the cast generator with an explicit `kind`, so a fresh faculty knows what
an agent carries and in what range. Zero-variance across a population is the
tell of cloning (`sigma_scale=0`); real casts draw each param ~Normal.

---

## 4. Seed inventory by domain ("what already exists")

Grouped map of the ~100 `bigville_*` seeds plus the shared affect stack. Block
numbers are taken from each seed's `description`. Rule names are the seed's own.
Nearly all bigville seeds are `self_load_only: true` (loaded explicitly by their
demonstrator); the only default-load exceptions are `bigville_move_nav`,
`bigville_move_energy`, `bigville_townspeople_30`.

### Governance, law & justice
| Seed | Block | Mechanism | Key rules |
|---|---|---|---|
| `agent_judgment` (shared) | 312000 | GENERIC decision-by-collapse over signed Stances | `jc_conclude`, `jc_act` |
| `bigville_recognition` | 324000 | authority = Count(recognizers); usurpation possible | `rc_strike`, `rc_recognize`, `rc_grant`, `rc_authority`, `rc_decree_tribute` |
| `bigville_court` (v2) | 313000 | council sits as court, rewired onto agent_judgment collapse | `ct_hear`, `ct_condemn`, `ct_verdict_guilty`, `ct_verdict_acquit`, `ct_sentence` |
| `bigville_sentence` | 315000 | sentencing by collapse, bounded by `SentenceLaw[min,max]` | `sn_sentence` |
| `bigville_jail` | 314000 | custodial term; `Jail -holds_inmate->` | `jl_imprison`, `jl_serve_day`, `jl_release` |
| `bigville_theft` | 337000 | theft as recognized frame + law (see §6, composition debt) | 16 rules: `own_recognition`, `own_decide`, `own_grant`, `th_take`, `th_recognize_theft`, `th_grant_theft`, `th_standing`, `th_charge`, `th_vote`, `th_cast_guilty`, `th_verdict`, `th_restitution`, `th_penalty`, `con_office`, `con_duty`, `th_collect` |
| `bigville_laws_enforcement` | 247000 | laws as held `knows_law` objects; violation witnessed → enforced; removal motion | `bl_detect_violation`, `bl_enforce`, `bl_decline`, `bl_mary_files_motion`, `bl_council_removes` |
| `bigville_legislature` | 310000 | `CouncilAct`; laws named/valued/amendable; censure effect | `leg_vote/tally/pass/amend/repeal/enact`, `law_tax_charge`, `ca_censure_effect` |
| `bigville_council_gov` | 268000 | two-tier council: public address vs private captured vote | `cm_convene`, `cm_public_address`, `cm_member_vote`, `cm_private_decision`, `cm_institutional_gap`, … |
| `bigville_council_board` | 268000 | noticeboard: clerk renders minutes (with bias), residents read | `cm_clerk_writes`, `cm_post_notice`, `cm_resident_reads` |
| `bigville_council_bylaw` | 322000 | meeting schedule as a Bylaw on bell-time | `cb_beadle_counts`, `cb_ring_assembly`, `cb_convene` |
| `bigville_viol_prosecute` | 263000 | prosecution through corruptible council | `bv_prosecute`, `bv_council_convict/acquit`, `bv_warn`, `bv_punish` |

### Economy, money & property
| Seed | Block | Mechanism | Key rules |
|---|---|---|---|
| `bigville_resource_extract` | 300000 | Sugarscape deposits + growback + proximity-gated extraction | `rx_growback`, `rx_extract`, `rx_deliver` |
| `bigville_trades` | 301000 | tradesmen transform raw → goods | `tf_transform`, `tf_sell` |
| `bigville_prices` | 302000 | emergent scarcity prices (supply/demand imbalance) | `pr_note_unmet`, `pr_scarce_raise`, `pr_glut_lower` |
| `bigville_labour` | 303000 | labour mobility with role-identity friction (Roy model) | `lm_wage`, `lm_switch` |
| `bigville_econloop` | 304000 | closed self-balancing loop (supply+price+labour) | `ec_extract`, `ec_price_glut/scarce`, `ec_wage`, `ec_switch` |
| `bigville_econ_exchange` | 252000 | local co-located buy + credit | `be_exchange`, `be_credit` |
| `bigville_econ_production` | 252000 | production needs skill; store-open derivation | `be_shop_open/shut`, `be_produce` |
| `bigville_econ_supply` | 252000 | up-chain supply network + credit `Owe` | `be_restock`, `be_restock_credit`, `be_repay` |
| `bigville_econ_debt` | 252000 | default + creditor affect flip | `be_default`, `be_default_affect` |
| `bigville_econ_expectation` | 252000 | store hours as prediction-and-residual | `be_expect_surprise` |
| `bigville_fin_bank` | 255000 | bank entity; interest via `IDiv` (cross-frame multiplicative base) | `bf_accrue`, `bf_set_rate`, `bf_salary`, `bf_insolvent` |
| `bigville_fin_tenure` | 255000 | own/mortgage/rent, foreclosure, equity, rentier lever | `bf_mortgage_pay/miss`, `bf_foreclose`, `bf_rent_pay/miss`, `bf_evict`, `bf_homeless_affect`, … |
| `bigville_fisc_state` | 257000 | council-set tax → Treasury; graft | `fs_set_tax`, `fs_collect`, `fs_pay_salary`, `fs_graft`, `fs_levy`, … |
| `bigville_fisc_church` | 257000 | voluntary donation-funded church (no lever) | `fc_tithe`, `fc_donate_occasional`, `fc_stipend`, `fc_charity`, `fc_counsel`, … |
| `bigville_land_market` | 261000 | land acquisition: buy / homestead / grant | `bl_buy`, `bl_buy_fail`, `bl_claim`, `bl_grant` |
| `bigville_land_tenure` | 261000 | land as root of tenure/collateral; trespass; land tax | `bl_build`, `bl_build_trespass`, `bl_foreclose_land`, `bl_land_tax`, `bl_tax_forfeit`, `bl_enclosure_reversal` |
| `bigville_fin_tenure`/`bigville_coll_*` | 264000 | collection & eviction as acts with a doer who feels it | `bc_collect_self/hired/miss`, `bc_deliver`, `bc_pay_wage`; `bc_evict`, `bc_moral_injury`, `bc_pick_cheapest_hands` |
| `bigville_market_trader` | 318000 | visiting trader sells non-local (exotic) goods | `mt_open`, `mt_refuse_local`, `mt_grant_access`, `mt_buy`, `mt_depart` |
| `bigville_build_construct` / `_mutate` | 260000 | construction consumes materials+labour+time; mutable world re-routes nav | `bb_consume/raise/trespass/addon`, `bbnav_wall_off`, `bb_church_expand`, `bb_demolish` |

### Social, relationships & conduct
| Seed | Block | Mechanism | Key rules |
|---|---|---|---|
| `bigville_bond_update` | 277000 | **Bond(A→B)** dynamics — the canonical interpersonal-affect model (§3.4) | `bond_belief_infer`, `bond_event_benefit/betrayal`, `bond_gossip_update`, `bond_similarity_attraction`, `bond_proximity_familiarity`, `bond_band_assign` |
| `bigville_fast_bond` | 287000 | fast gut-pull nudge from `affection − resentment` | `fb_fast_bond` |
| `bigville_conduct` | 281000 | directed conduct coupled to the held Bond | `conduct_couple_harm/help/transfer` |
| `bigville_supergraph_conduct` | 282000 | supergraph valuation (actor stake + weighted target effect) | `conduct_supergraph_value` |
| `bigville_decision_core` | 279000 | conduct decision as one collapse with residual-driven depth | `dc_collapse_pass/settle/deepen/writeback/no_writeback` |
| `bigville_speech_decide` | 278000 | whether/whom/what-kind to speak, from Bond+norms+affect | `sp_choose_utterance`, `sp_noticeable_absence`, `sp_set_chosen_loudness` |
| `bigville_surprise_gate` | 284000 | decision fires on surprise (obs ≠ social prediction) | `sg_provide_directed`, `sg_surprise`, `sg_absorb` |
| `bigville_drama_social` | 245000 | small-cast emergent political drama (psychopath mayor + ToM pastor) | `bd_john_public_face`, `bd_mary_infers/forms_goal/claims`, `bd_villager_backs` |
| `bigville_loop_reputation` | 253000 | economy→affect→society (badmouth, opinion flip) | `bl_badmouth`, `bl_townsfolk_opinion` |
| `bigville_loud_comm` / `_class` | 267000 | utterance loudness scales earshot; classroom chatter | `lo_choose_loudness`, `lo_deliver_content`, `lo_observe_act`; `lo_chatter_distracts`, `lo_control_restores` |
| `bigville_news_*`, `bigville_publisher_role`, `bigville_report`, `bigville_hold`, `bigville_write`, `bigville_headline`, `bigville_column_alloc`, `bigville_foreign_dispatch` | 269000–318000 | the press: reporter→publisher→print→reach→coalition; capture/bias as word-choice; copyfitting | e.g. `np_reporter_writes`, `np_reader_learns`, `np_coalition_forms`, `pub_role_gathers`, `write_free/captured/laundered` |

### Affect & psychology (self)
See §3.5 for the shared stack. Bigville-specific affect faculties:
| Seed | Block | Mechanism | Key rules |
|---|---|---|---|
| `bigville_affect_grief` | 265000 | source-agnostic `Loss` → grief_distress | `af_grief_from_loss` |
| `bigville_affect_decide` | 265000 | chosen action = decision_value Argmax over Action menu | `af_choose_action` |
| `bigville_affect_coreg` / `_propagate` / `_spiral` | 265000 | co-regulation → regulation; grief narrows caregiving; the endogenous negative spiral | `af_regulation_from_coreg`, `af_grief_narrows_caregiving`, `af_outcome_work/withdraw/drink/snap`, `af_hardship_grief` |
| `bigville_goal_dream` / `_life` | 256000 | ungrounded escape fantasy + grounded life-goal (soul) | `gg_dream_ungrounded/relief/collapse_*`, `gg_lifegoal_grounded`, `gg_orient_choice` |
| `bigville_time_concern` | 251000 | witnessing a collapse fires concern (rides arousal/valence) | `bt_concern` |
| `bigville_journal_nightly` | 274000 | graph-native first-person diary from own state | `jn_write_entry` |

### Material, food & tools
| Seed | Block | Mechanism | Key rules |
|---|---|---|---|
| `bigville_foodstuff` | 333000 | food lifecycle: storage, spoilage, preparation, integer portions | `fs_spoil`, `fs_rot`, `fs_prepare`, `fs_eat`, `fs_nofood`, `hq_ration` |
| `bigville_nutrition` | 332000 | density/variety/deficiency + taste/spice + ale | `nu_eat`, `nu_metabolize`, `nu_deficiency`, `nu_psych` |
| `bigville_tools` | 336000 | tools as effectiveness multipliers; fitness is DATA; **ownership = recognition** | `tl_gather`, `tl_strike`, `tl_prep`, `oc_recognition` |

### Cognition — the MAEM core (C1–C6)
The integrated Motivation→Attention→Emotion→Memory core (`ozma_maem_cognitive_core`),
each rung reproducing a textbook signature as graph-native collapse:
| Seed | C-rung | Block | Signature | Key rules |
|---|---|---|---|---|
| `bigville_motivation` | C1 | 325000 | drive divergence (Psi + SDT) | `mv_urge`, `mv_arousal`, `mv_bootstrap`, `mv_refresh`, `mv_switch` |
| `bigville_attention` | C2 | 327000 | inverted-U (Yerkes-Dodson) | `at_focus`, `at_complete` |
| `bigville_memory` | C3 | 326000 | forgetting curve (Tulving+OCC+ACT-R) | `mem_appraise`, `mem_decay`, `mem_recall`, `mem_mood` |
| `bigville_stress` | C4 | 328000 | chronic-load breakdown (McEwen) | `al_accumulate`, `al_break`, `al_cope`, `al_recover`, `al_rest` |
| `bigville_flow` | C5 | 329000 | flow at challenge≈skill (Csikszentmihalyi); Creation value = Count(appreciators) | `fl_state`, `fl_streak`, `fl_generate`, `fl_worth` |
| `bigville_action` | C6 | 330000 | thermodynamics of agency (cost + impact, conserved) | `ac_work`, `ac_eat`, `ac_rest`, `ac_metabolize` |
| `bigville_cognition` | integ | 331000 | the closed cognitive loop on one agent (depends `bigville_memory`) | `cg_metabolize`, `cg_state`, `cg_eat`, `cg_work`, `cg_break`, `cg_recover`, … |

### Perception, movement & time
| Seed | Block | Mechanism | Key rules |
|---|---|---|---|
| `bigville_move_nav` | 249000 | Bellman-flood grid movement over a walkable map-belief (default-load) | `mv_seed_goal`, `mv_relax`, `mv_pick_hop` |
| `bigville_move_energy` | 249000 | graded energy → hop budget; hunger-modulated cost (default-load) | `mv_energy_budget`, `mv_deplete` |
| `bigville_need_choice` / `_drive_goal` | 250000 | which good to target (Argmax over reachable satisfiers); drive → spatial goal | `nd_seed_here`, `nd_relax`, `nd_choose_good`, `nd_arbitrate`, `nd_form_*_goal` |
| `bigville_bells` / `_bell_schedule` | 320000/323000 | church bell = the only clock (§3.6) | `bl_ring`, `bl_hear_awake`, `bl_wake_rested`, `bl_decide`, `bl_attend` |
| `bigville_time_sleep` | 251000 | autonomous sleep decision + exhaustion collapse | `bt_decide_sleep`, `bt_collapse`, `bt_replenish`, `bt_wake` |

### Life-cycle & world-frontier
| Seed | Block | Mechanism | Key rules |
|---|---|---|---|
| `bigville_life_health` | 262000 | health = one variable, two timescales (aging = illness); death is the unifying decision | `bl_age`, `bl_acute`, `bl_recover`, `bl_death` |
| `bigville_life_inheritance` | 262000 | death → inheritance (land/house/coin conserved; commons fallback) | `bl_inherit_land/house/coin`, `bl_inherit_commons_*` |
| `bigville_life_rearing` | 262000 | rearing shapes the three foundational priors from care quality | `bl_come_of_age` |
| `bigville_fert_decide` | 271000 | fertility as quantity-quality graph decision (never keyed on wealth) | `bf_oldage`, `bf_quantity_quality`, `bf_mortality_replace` |
| `bigville_doctor_care` / `bigville_infant_care` | 270000/272000 | health as money-gated market good; infant mortality | `bd_checkup(_public)`, `bd_treat(_public)`, `bd_onset`, `bd_recover`; `bi_wellbaby(_public)`, `bi_onset` |
| `bigville_school_*` | 266000 | affect-gated classroom; funding→open; generational hinge | `sc_acquire`, `sc_fail_*`, `sc_school_open/close`, `sc_come_of_age`, `sc_master_quality` |
| `bigville_skill_learn` / `_teach` | 254000 | learning-by-doing (diminishing returns); teaching as decision+coercion | `bs_practice`; `bs_teach_willing/refuse`, `bs_coerce`, `bs_teach_coerced` |
| `bigville_world_*` | 259000 | open economy: frontier (Giantville), travellers as full agents, inn, scope-gating (compute thesis) | `bw_news_secondhand`, `bw_inn_stay`, `bw_run_in_scope`, `bw_dissolve_on_leave`, `bw_recruiter_grounds_path` |
| `bigville_viol_*` | 263000 | violence: the act (value-decision), evidence pipeline, fifth route to death | `bv_trigger/refrain`, `bv_witness_evidence`, `bv_form_belief`, `bv_death_tag` |

### Casts (mechanical data, no rules)
`bigville_townspeople_30` / `_50`, `bigville_cast100` — heterogeneous agents with
drawn-Normal params on the town map. Population = distribution over seeds.

---

## 5. How to add a new capability (decision checklist)

Run this checklist before writing any new bigville seed:

1. **Prereg first.** Write `BIGVILLE_<NAME>_PREREG.md` with pass/fail gates and
   at least one **falsifier** (an ablation that must break the observable).
   Deltas within ~3× the per-episode step are noise — **power the gate** before
   any endgame claim, and record eval-subset coverage.
2. **World-fact or human-frame?** (§3.2) For every body/coin/property/standing/
   office mutation, decide. World-facts the engine may enforce; frames must be
   recognized by the affected agent AND enacted with reach. Never fire a frame
   on a status attr; never let the substrate forbid a usurpation.
3. **Is each decision a collapse?** (§3.1) Any "who decides / whether / whom" is
   an `Argmax` over signed Stance nodes valued by the deciding agent's own
   params — never a threshold/comparator. Ship the "set every disposition equal
   → one verdict" falsifier.
4. **Does a primitive already exist? Reuse, don't reinvent.** (§3, §6)
   - office/title/property/law → **`bigville_recognition`** (Count(recognizers))
   - "how A feels about B" → **`Bond(A→B)`**, read `affection − resentment`; for
     dynamics depend on `bigville_bond_update`. Do **not** mint a scalar/`Regard`.
   - a verdict over a panel → **`bigville_court`** / `agent_judgment`.
   - self affect/arousal → hook `AffectiveState` via the §3.5 stack.
   - time → bell peals, never a forced counter.
5. **Conservation & effect-ordering check.** (§3.7) Coin/material conserved;
   reads before writes; store-first when a value depends on attrs you mutate.
6. **Edge-type check.** (§3.8) No two same-type incoming edges on one node;
   distinct edge types for shortcut relations; explicit `Not Eq` guards for
   required role-distinctness.
7. **`self_load_only: true`** unless the seed is genuinely core (nav/energy/cast
   are the only defaults). The demonstrator loads it explicitly.
8. **Gate as `tests/test_<name>_migrated.py`.** Add to the migrated bench.
9. **`.so` stays untouched.** New capability = new Rust `Term` + graph data, or
   graph data alone — never a change to the compiled binary for a capability.
   (New Terms are a separate, deliberate Rust change with their own gates.)
10. **Commit as a LEDGER block.** One block number, headline + honest residuals.

Anti-tuning discipline is absolute: gate the *qualitative signature* science
established, never a tuned number; synthetic-proven mechanism ≠ benchmark value
— report both.

---

## 6. Duplication / fix / update audit

Each finding was verified by reading the cited files. Severity: **blocking** /
**should-fix** / **nice-to-have**.

### 6.1 Recognition primitive is duplicated three ways — RESOLVED (count unified, block 354000)

**STATUS: RESOLVED for the COUNT (6.4 Step B, block 354000).** `bigville_recognition`
v1.1.0 gained `rc_count` — the ONE canonical count, parameterised over the claim node
(matches a bare `[r -recognizes-> claim]` edge, per-claim by the match-bound join) and
writes `claim.recognition = Count(...)`. `bigville_theft` v1.3.0 now `depends_on:
[bigville_recognition]`, deletes its `own_recognition`, and composes `rc_count` (the
adapter loads recognition first). `rc_authority` is retained (legacy `authority` attr).
`bigville_tools`' `oc_recognition` MAY compose `rc_count` the same way (not migrated here —
out of Step B scope, tools gate left untouched). The COLLAPSE half (per-decision leans)
stays per-seed: it is finding 6.2 (shared stance codebook + `for_decision` scope), not 6.1
— routing ownership's `legitimacy·deference − prop_skepticism` through recognition's
`fear·force + opportunism − loyalty` needs the deferred scoping. Gate: theft/court/co-load/
tools/recognition suites all green (37); falsifier
`test_the_ownership_count_genuinely_moved_to_bigville_recognition`.

The original finding (kept for record):

The `Count(InNeighbours "recognizes")` + grant-collapse pattern is authored
**three times**:

- `bigville_recognition.json`: `rc_authority` (`claim.authority = Count(...)`) +
  `rc_recognize`/`rc_grant` collapse.
- `bigville_theft.json`: `own_recognition` (`claim.recognition = Count(...)`) +
  `own_decide`/`own_grant` collapse (ownership), AND `con_office`
  (`con.authority = Count(InNeighbours "recognizes_office")`).
- `bigville_tools.json`: `oc_recognition` (`claim.recognition = Count(...)`) —
  count-only, no collapse (the adapter seeds `recognizes` edges directly).

All three compute the identical thing off the identical edge type. **The case
for one canonical primitive is strong.** Concrete fix: promote
`bigville_recognition` to the canonical recognition seed and have `theft`/`tools`
`depend_on` it; factor the count rule to a single `rc_authority`-style rule
parameterised over the claim/office node, and the grant-collapse to a single
`rc_recognize`/`rc_grant` pair reused with different `lean` Terms (recognition's
`fear_weight·force + opportunism − loyalty` vs ownership's
`legitimacy·deference − prop_skepticism`). Risk: the three seeds use different
attr names (`authority` vs `recognition`) and different `recognizes` vs
`recognizes_office` edge types; unifying naming touches the theft/tools gates —
do it behind the migrated bench, not blind. **Note:** the edge type `recognizes`
is currently overloaded across office-authority (recognition), ownership (theft),
and tool-ownership (tools) claims on the same graph — a real collision risk if
two are ever co-loaded (see 6.7).

**STATUS: DEFERRED — plan documented (block 349000), gated behind 6.7.** This is
6.4-Step-B and cannot land before 6.7-scoping (a co-load of two recognition
families is exactly what unifying invites). Exact steps: (a) land 6.7 scoping so
counts are per-claim; (b) promote `bigville_recognition` to canonical; factor the
count to one `rc_authority`-style rule parameterised over the claim node, and the
grant-collapse to one `rc_recognize`/`rc_grant` pair reused with different `lean`
Terms (recognition's `fear_weight·force + opportunism − loyalty` vs ownership's
`legitimacy·deference − prop_skepticism`); (c) reconcile the attr names
(`authority` vs `recognition`) and edge types (`recognizes` vs
`recognizes_office`) — pick one, migrate theft/tools behind their benches;
(d) `theft`/`tools` `depends_on: [bigville_recognition]`, delete the local
copies, rewrite the source-audit gates to assert the composed wire.

### 6.2 Stance-node collapse scaffolding duplicated — DEFERRED w/ plan (block 349000)

Each collapse mints its **own** stance node type with the identical
`{label, sign:±1}` shape, and the adapters mint them per-world:
`RecogChoice` (recognition), `OwnStance` / `TheftStance` / `GuiltStance` /
`DutyStance` (theft), plus `agent_judgment`'s `Stance` (denounce/condemn/doubt/
exonerate, poles). Verified: `TheftStance/GuiltStance/OwnStance/DutyStance` are
minted in `worlds/bigville_theft_world.py` (lines ~36–42); `RecogChoice` in
`worlds/bigville_recognition_world.py`. The `Argmax(NodesOfType("<Stance>"),
value=sign·lean)` scaffold is byte-for-byte the same modulo the `lean` Term and
the node-type string. **Candidate for a shared stance codebook** — one
`{recognize/reject}` (binary) and one graded pole set, minted once by a shared
loader, referenced by node-type parameter. Nice-to-have caveat: distinct
node-types are currently what keeps two co-loaded collapses from reading each
other's stances (`NodesOfType` is global — see 6.7), so a shared codebook needs a
per-decision scoping mechanism (a `for_decision` tag on the stance + a match
filter). Severity should-fix; the scoping requirement makes it non-trivial.

**STATUS: DEFERRED — plan documented (block 349000), gated behind 6.7.** The
distinct node-types (`TheftStance`/`GuiltStance`/`OwnStance`/`DutyStance`/
`RecogChoice`) are the ONLY thing preventing cross-reads today, so a shared
codebook is unsafe until 6.7's `for_decision` scoping lands. Exact steps: (a) land
6.7 scoping; (b) define two shared stance codebooks minted once by a loader — a
binary `{recognize:+1, reject:−1}` and a graded pole set — each stance carrying
`for_decision -> <decision node>`; (c) rewrite every `Argmax(NodesOfType("X"))`
to `Argmax(InNeighbours(decision,"for_decision"), value=sign·lean)`, passing the
node-type/`lean` as the only per-collapse difference; (d) delete the per-world
stance minting from the adapters (the loader seeds them). Gate: the 6.7 co-load
falsifier plus every existing collapse gate unchanged.

### 6.3 Verdict is duplicated; theft should compose the court — RESOLVED (block 355000)

**STATUS: RESOLVED (6.4 Step C, block 355000).** `bigville_theft` v1.4.0 deletes
`th_vote`/`th_cast_guilty`/`th_verdict` and COMPOSES `bigville_court`: `th_charge` mints a
court Charge/Matter (`about_subject` + `town has_charge`, `weight = theft_standing`,
`threshold = Count(on_council)·0.5+0.5` = strict majority, `penalty=0` so `ct_sentence` is an
economic no-op), `th_refer` seats each juror's `considers` edge, `agent_judgment`'s
`jc_conclude` collapses per juror, and `bigville_court`'s `ct_verdict_*` aggregates.
`th_restitution`/`th_penalty` read `off.status=="guilty"`. The juror lean
(`lawfulness·theft_standing − doubt`) is reproduced through `jc_conclude`'s lean by mapping
`credence=lawfulness`, `punitiveness=−doubt` (defendant standing 0 ⇒ deference term vanishes).
**Deviation:** rather than generalise `bigville_court` to a `has_juror` panel, theft seats
jurors on the court's existing `on_council` panel — composing with ZERO changes to
`bigville_court`, keeping the jail-via-court + agent_judgment gates byte-green. Gate: 52 green
(theft/court/jail/agent_judgment/recognition/co-load/tools); falsifier
`test_the_verdict_genuinely_moved_to_bigville_court`.

The original finding (kept for record):

`bigville_court` already provides a panel-verdict faculty rewired onto
`agent_judgment` (`ct_hear`, `ct_condemn`, `ct_verdict_guilty/acquit`,
`ct_sentence`; `depends_on: [bigville_legislature, agent_judgment]`).
`bigville_theft` **reimplements the whole verdict path**: `th_vote` (juror
`{guilty,acquit}` collapse), `th_cast_guilty`, `th_verdict` (majority via
`2·Count(guilty_vote) > Count(voted_on)`). This is a parallel court. Concrete
fix: theft's charge (`th_charge` mints an `Offense`) should feed
`agent_judgment`/`bigville_court`'s `Matter`/`Charge`, and the theft seed should
depend on `bigville_court`, deleting `th_vote`/`th_cast_guilty`/`th_verdict`.
Risk: court's verdict is a councillor collapse valued by `agent_judgment`'s lean;
theft's juror collapse is valued by `lawfulness·theft_standing − doubt` — the
lean Term differs and the panel is jurors not councillors, so composing means
generalising court to accept a juror panel and a per-offense lean. Medium risk;
gate both the theft and court migrated suites.

**STATUS: DEFERRED — plan documented (block 349000), this is 6.4-Step-C.** Exact
steps: (a) generalise `bigville_court`'s panel from `has_member` (councillors) to
accept a `has_juror` panel and a per-`Matter` `lean` attr, so `ct_hear`/
`ct_condemn`/`ct_verdict_*` range over jurors with the offense's lean; (b) make
theft's `th_charge` mint a court `Matter`/`Charge` (the offense IS the matter)
instead of driving `th_vote`; (c) **reconcile the fine sink (6.10):**
`bigville_court`'s `ct_sentence` fines the `Treasury`, theft's `th_penalty` fines
`court.coin` — pick one (Treasury is the canonical town coffer) and update
`th_penalty`/`th_restitution` and the coin-conservation gate together;
(d) delete `th_vote`/`th_cast_guilty`/`th_verdict`, `depends_on:
[..., bigville_court]`, rewrite the theft verdict gates to assert the composed
court's verdict. Gate BOTH `test_theft_migrated` and `test_court_migrated`.

### 6.4 Composition debt in `bigville_theft` — RESOLVED (blocks 354000–357000)

**STATUS: RESOLVED.** The theft-composition refactor landed in four gated commits
(`BIGVILLE_THEFT_COMPOSE_PREREG.md`): **Step B (354000)** unified the recognition count
(theft `depends_on bigville_recognition`, `own_recognition` deleted, canonical `rc_count`);
**Step C (355000)** composed the court (deleted `th_vote`/`th_cast_guilty`/`th_verdict`,
`th_charge` mints a court Charge/Matter that `jc_conclude`+`ct_verdict` decide, fine sink
reconciled to the Treasury — 6.10); **Step D (356000)** composed `bigville_bond_update` (the
constable's Bond evolves from a benefit/betrayal history, not a static scalar); **Step E
(357000)** shrank the adapter (stance codebooks moved to seed `nodes`). `bigville_theft` is now
`depends_on: [bigville_recognition, bigville_court, bigville_bond_update]`. Each step shipped a
prereg + `=off` falsifier; theft/court/co-load/tools/recognition/jail/agent_judgment gates green
throughout (54). Skipped 6.2 (shared stance codebook — distinct stance node types retained,
`for_decision` scoping deferred). The theft-specific rules that legitimately remain theft's own:
`th_take`, `th_recognize_theft`, `th_standing`, `th_charge`, `th_refer`, `th_restitution`,
`th_penalty`, `con_office`, `con_duty`, `th_collect`, `own_decide`, `own_grant`.

The original finding (kept for record):

`bigville_theft.json` has `depends_on: []` and **self-seeds three things that
already have canonical seeds**, instead of composing them:

- **Ownership recognition** — reimplements the recognition primitive
  (`own_recognition`/`own_decide`/`own_grant`) instead of depending on
  `bigville_recognition` (6.1).
- **The verdict** — reimplements the court (`th_vote`/`th_cast_guilty`/
  `th_verdict`) instead of depending on `bigville_court` (6.3).
- **Bonds/jurors** — `con_duty` reads a `Bond`'s `affect_affection −
  affect_resentment` correctly (good — it reuses the canonical warmth scalar),
  **but** `worlds/bigville_theft_world.py` seeds the `Bond` node, the
  `holds_bond`/`toward` edges, the `has_juror` panel, and the `OwnershipClaim`/
  `recognizes` edges **directly in the adapter** (verified lines ~62–155), and
  the seed does not depend on `bigville_bond_update`, so the bond never *evolves*
  (no benefit/betrayal/gossip dynamics — it is a static seeded feeling).

Wiring that would replace the seeding: `bigville_theft` should
`depend_on: [bigville_recognition, bigville_court, bigville_bond_update]`; the
demonstrator loads those seeds; the adapter's job shrinks to ingesting the
world-fact take (`th_take`) and reading results. The theft-specific rules that
remain legitimately theft's own: `th_take` (world-fact), `th_recognize_theft`
(the wire to recognition — this is the correct kind of composition, a collapse
reading `w -recognizes-> claim`), `th_standing`, `th_charge`, `th_restitution`,
`th_penalty`, `th_collect`. **This is the top structural finding to relay.**

**STATUS: DEFERRED — the in-place rewrite is BLOCKED by two hard obstacles
(audited block 349000, NOT attempted to keep the 15 theft gates green):**

1. **The source-audit gate pins the re-seeded rules.**
   `tests/test_theft_migrated.py::test_no_python_decides_theft_or_law`
   (lines 277–309) *asserts the presence* of `own_recognition`, `own_decide`,
   `own_grant`, `th_vote`, `th_verdict` in the theft seed and inspects their
   `OwnStance`/`GuiltStance`/`Argmax`/`Count` internals. Deleting them (the whole
   point of 6.4) fails this gate. The gate itself must be rewritten as part of
   the migration — legitimate, but it means "keep all 15 green unchanged" is
   impossible; the audit is pinning the *duplicated* structure.
2. **Composition needs 6.1 + 6.3 + 6.7, which are neither contained nor
   independent.** Depending on `bigville_recognition` co-loads its `recognizes`
   edges and `RecogChoice`/`rc_authority` `Count(InNeighbours "recognizes")` onto
   the *same* `recognizes` edge theft's `own_recognition` counts → the global-
   scope collision (6.7) fires the moment both are present. Depending on
   `bigville_court` needs court generalised to a juror panel + per-offense lean
   and the fine-sink reconciled (theft fines `court.coin`; court fines the
   Treasury — 6.10). Depending on `bigville_bond_update` loads benefit/betrayal/
   gossip rules that would mutate the constable's *seeded static* Bond during
   `settle()`, changing the `constable_choice` outcomes the gates assert.

**CONCRETE MIGRATION PLAN (do in this order, each step its own gated commit):**

- **Step A — land 6.7 scoping first (prerequisite).** Add a `for_claim` edge from
  each `recognizes` edge's target-claim scope and rewrite the recognition count
  to a *scoped* count (see 6.7's plan). Until counts are per-claim, no two
  recognition families can co-load. Gate: a NEW co-load test (two claims, one
  town) that today would cross-contaminate.
- **Step B — unify recognition (6.1).** Promote `bigville_recognition` to the
  canonical seed; parameterise `rc_authority`/`rc_recognize`/`rc_grant` over the
  claim node and the `lean` Term. Rename theft's ownership attrs to the canonical
  set (`recognition`→ keep, but route through the shared rule) behind the theft
  bench. Delete `own_recognition`/`own_decide`/`own_grant`; `bigville_theft`
  `depends_on: [bigville_recognition]`. Rewrite the source-audit gate to assert
  the *composed* wire (theft reads `w -recognizes-> claim`; the count rule lives
  in `bigville_recognition`).
- **Step C — compose the court (6.3).** Generalise `bigville_court` to accept a
  juror panel (`has_juror`) and a per-offense `lean` (`lawfulness·theft_standing
  − doubt`); make theft's `th_charge` mint a `Matter`/`Charge` court hears.
  Delete `th_vote`/`th_cast_guilty`/`th_verdict`; reconcile the fine sink (pick
  `Treasury` and update `th_penalty`/`th_restitution` + the coin-conservation
  gate). `depends_on: [..., bigville_court]`.
- **Step D — evolve the bond (6.4 part 3 / 6.10).** `depends_on:
  [bigville_bond_update]`; move the constable's Bond from an adapter-seeded static
  node to one the bond dynamics evolve. The `constable_choice` gates must be
  re-derived from the *evolved* warmth (seed a benefit/betrayal history, not a
  final scalar). This is the step most likely to move gate numbers — power it.
- **Step E — shrink the adapter.** Once B–D land, delete the codebook/`Bond`/
  `has_juror`/`OwnershipClaim` minting from `bigville_theft_world.py`; the
  demonstrator loads the four seeds and the adapter only arms `th_take` and reads.

Risk is high and the steps are strictly ordered (A gates B, B+C gate D). Do NOT
start mid-chain. Each step is a full prereg + falsifier per §7.

### 6.5 No canonical Agent schema / attribute vocabulary — RESOLVED (§3.10, block 347000)

Agent params are scattered per-seed with no documented vocabulary. Observed
decision params, by seed: `fear_weight`, `opportunism`, `loyalty_prior`,
`shown_force` (recognition); `lawfulness`, `ally_taker`/`alliance_to_taker`,
`deference`, `prop_skepticism`, `doubt`, `duty`, `legitimacy` (theft);
`role_identity` (labour/cast); `snap_pressure`, `spite`, `w_supergraph`,
`w_spite` (violence/conduct); plus universal ones `coin`, `alive`, `energy`,
`hunger`, `health`. There is no single place that says which attrs an "agent"
carries or their ranges. **Fixed** by documenting the canonical vocabulary in
**§3.10** (universal state, affect, social/decision params, foundational priors —
each with kind and drawn-Normal base·sd taken from the cast generators). The
kind fixes the range (`lognorm` >0, `logit` (0,1), `normal` signed, `int`/`bool`
in-frame). A `bigville_agent_core` *seed* was deliberately NOT added: there is no
`Agent` node type to attach defaults to (an agent is any node a lean reads), and
the cast generators already draw the defaults — a seed would duplicate them. The
doc table is the single source a new faculty consults before coining a param.

### 6.6 Debt has no ongoing collector loop — CONFIRMED (known residual, nice-to-have)

`th_penalty` splits an unpaid remainder into `debt_damages` + `debt_fine`;
`th_collect` collects "repeating as they earn until cleared" — but nothing in
the theft seed generates income, and `th_collect` only fires when the debtor's
coin is topped up externally. There is no autonomous income/collection loop in
`bigville_theft`; collection is driven by the adapter arming an `earn()` event.
The economy seeds (`bigville_labour`, `bigville_econloop`, `bigville_action`
`ac_work`) *do* produce income, but theft is not composed with them. Fix: when
theft depends on the economy loop (6.4-style composition), `th_collect` becomes a
standing per-epoch rule (epoch-guard, §3.9) that bites as the debtor's real
wage/output accrues. Nice-to-have; the current behaviour is honest (documented in
the v1.2.0 description) not wrong.

### 6.7 Global `NodesOfType` / overloaded edge types — DEFERRED w/ plan (block 349000)

`Argmax(NodesOfType("Stance"))` and `Count(InNeighbours(_, "recognizes"))` are
**global** — they scan every node of that type / every `recognizes` edge in the
graph, not a per-decision or per-claim scope. Today this is safe only because
each demonstrator loads one collapse family in isolation (`self_load_only`) and
uses distinct node/edge names. The moment two recognition frames (office
authority + ownership + tool-ownership all use the `recognizes` edge) or two
stance families are co-loaded on one town, they will read each other's edges/
stances. This is latent, not yet triggered. Fix: scope by a claim/decision tag
in the match (a `for_claim`/`for_decision` edge the count/argmax filters on)
before any full-town integration that co-loads these. Ties directly into 6.1/6.2.

**STATUS: MEASURED — the count concern does NOT manifest (block 353000).** The
co-load falsifier now exists (`tests/test_recognition_coload_migrated.py`): it
co-loads `bigville_recognition` + `bigville_theft` on ONE town with an agent
recognizing BOTH an authority claim and an ownership claim via the shared
`recognizes` edge, and MEASURES the counts — `authority = 2` and `recognition = 2`
(each scoped to its own claim), NOT 4. The counts are `InNeighbours` of a
**match-bound claim node**, so they are inherently per-claim; the shared
`recognizes` edge type is harmless. Stance collapses are scoped by distinct node
TYPE (`RecogChoice` vs `OwnStance`/`TheftStance`/…), which `NodesOfType` respects.
**So 6.7 is NOT a blocking prerequisite for 6.1/6.4** — the counts are already
scoped. The ONLY way to introduce the bug is a naive shared *stance* codebook
(6.2) that drops the distinct types without a `for_decision` tag — which is a
6.2-local requirement, not a global one. The gate is now the regression guard: if
any recognition count is ever made global, it goes red. **Consequence for 6.4:
Step-A ("land 6.7 scoping first") is OBVIATED** — 6.4 may compose
`bigville_recognition` directly (per-claim counts stay correct under co-load); the
real remaining 6.4 obstacles are the source-audit-gate rewrite, the court
generalisation (6.3), the fine-sink reconciliation (6.10), and the bond evolution
(Step D). The original latent-fix plan (kept below for the 6.2 case) was: Not
landed as a live change because it is not contained: every count/argmax rule across
`bigville_recognition`, `bigville_theft`, `bigville_tools` (and every stance
collapse) plus each adapter that seeds the edges would change together, and there
is no co-load gate today to prove the fix (the bug is latent). Adding untested
scoping scaffolding with no falsifier would violate §7. **Exact fix:**

1. **Tag every scoped edge.** When an adapter seeds `w -recognizes-> claim`, also
   seed `claim -for_claim-> claim` (a self-tag) OR give the count a scope var:
   change `th_standing`/`rc_authority` from `Count(InNeighbours(claim,
   "recognizes"))` (global over ALL `recognizes` edges) to a count that matches
   `[w, "recognizes", claim]` in the rule's `match` (binding the specific claim),
   so the count is already per-claim via the join — this is the cheapest fix and
   needs no new DSL if the count can read a match-bound neighbour set.
2. **Scope every stance collapse.** Add `for_decision` from each stance node to
   its decision node; change `Argmax(NodesOfType("TheftStance"))` to
   `Argmax(InNeighbours(decision, "for_decision"))` so a collapse reads only its
   OWN stances, not every stance of that type in the town. `NodesOfType` is the
   global smell; the argmax should range over a decision-scoped neighbour set.
3. **Gate it.** Write a co-load falsifier: two claims (or two decisions) on ONE
   town; assert each count/collapse reads only its own scope. Today that test
   would fail (cross-contamination); after the fix it passes. THIS test is the
   prerequisite for any full-town integration and for 6.4-Step-A.

### 6.8 Forced-clock remnants — MEASURED & RESOLVED (block 348000)

Re-swept every bigville seed (block 348000). **The genuine forced-clock defect —
a `Mod(<global-day-counter>)` scheduler — exists in exactly ONE rule:**
`bigville_council_gov`'s `cm_convene` (`Mod(now_day, cadence)==0`). Everything
else the original finding implicated is either already migrated or a legitimate
in-frame integer timestamp:

- **`cm_convene` (`bigville_council_gov`)** — the sole `Mod(now_day)` forced
  clock. It is **already superseded** by the bell-time
  `bigville_council_bylaw` (`cb_beadle_counts` counts curfew `BellPeal`s →
  `cb_ring_assembly` → `cb_convene`; `depends_on: [bigville_legislature,
  bigville_bells]`, block 322000, gated green by
  `test_council_bylaw_migrated.py`). The council's *scheduling* migration
  therefore landed as a separate seed; `bigville_council_gov` is retained only
  for its two-tier public/private governance content, now marked LEGACY in its
  description. **Not rewritten in place** because the `bigville_council`
  gate's whole interface is the day-modulus `convene(now_day, cadence)` plus an
  off-cadence control falsifier (`7 % 3 != 0 → no meeting`); a bell-time rewrite
  would break that green gate for zero new capability (the bell path exists).
- **`now_epoch`/`due_epoch` in `bigville_econ_debt`/`_supply`/`_exchange`** —
  all `Gt` term-expiry comparisons (`be_default`: an `Owe` unpaid past its term,
  `now_epoch > due_epoch`). These are **legitimate in-frame integer coordinates**
  (§3.6/§3.7), NOT a forced clock every agent is driven by. Left as-is by design.
- **Jail day-advance / market day** — no `Mod`-based global day counter found in
  `bigville_jail*` / `bigville_market*` (jail/market gates run on armed pulses /
  bell counts, not a day modulus). The original finding's "jail day advance,
  market day" list did not reproduce as `Mod` forced clocks.
- **`bigville_bell_schedule` / `bigville_council_bylaw`** — the token `now_day`
  appears only in their *prose* ("NOT `now_day % cadence`"); both are fully
  bell-migrated.

**Concrete in-place plan (deferred, for whoever retires `cm_convene`'s
modulus):** (1) give the meeting node a `days_since_meeting` counter and a
`meeting_interval` (mirroring `bigville_council_bylaw`'s `Law`); (2) replace
`cm_convene`'s `Mod(now_day,cadence)==0` guard with `Gte(days_since_meeting,
meeting_interval)` fired by a `BellPeal`-counting rule (the `cb_beadle_counts`
pattern) and reset on convene; (3) rewrite `BigvilleCouncilWorld.convene(...)`
to ring N curfew peals instead of passing `now_day`/`cadence`; (4) rewrite the
`test_bigville_council_migrated` on/off-cadence gate to assert "convenes after
`interval` peals / not before." Since `bigville_council_bylaw` already provides
exactly this behaviour, the cleaner route is to fold `council_gov`'s governance
content ONTO `bigville_council_bylaw`'s convene and delete `cm_convene` — a
consolidation gated by both suites, out of scope for a doc/seed-note pass.

### 6.9 `self_load_only` vs default-load inconsistency — RESOLVED (block 346000)

`bigville_townspeople_30` was the only cast seed WITHOUT `self_load_only`, so it
was swept into every `load_all_seeds` boot while `bigville_townspeople_50` and
`bigville_cast100` (identical kind: data-only inhabitant registers, no rules)
were not. Verified both demonstrators that use the 30-cast (`bigville_loop_world`,
`bigville_integ2_world`) read the file by path and never relied on default-load.
**Fixed:** added `self_load_only: true` to the JSON and to the generator
(`scripts/bigville_town_seed.py::build_seed_manifest`) so a regenerate keeps it —
all three casts now self-load, chosen by the demonstrator (`bigville_move_nav`/
`bigville_move_energy` remain the intentional default-loaders).

### 6.10 Collected residuals from seed descriptions & preregs

Gathered known-limitations (from seed descriptions / prereg honesty sections):

- **Bond static in theft** — no benefit/betrayal/gossip evolution absent
  `bigville_bond_update` (6.4).
- **Witness reach not modelled in theft** — `th_recognize_theft` matches any
  `has_resident` witness, not line-of-sight; the richer evidence/occlusion
  pipeline exists separately in `bigville_viol_evidence` (`bv_witness_evidence`
  is line-of-sight) and is not composed into theft.
- **Single-offense / single-claim constraints from the edge gotcha** (§3.8) —
  role-distinctness leans on explicit `Not Eq` guards; co-loading multiple
  offenses/claims on shared edge types is untested.
- **MAEM reductions** (`ozma_maem_cognitive_core`): `arousal`/`mood` use a
  max/dominant proxy (no sum-over-node-set in the DSL — the weighted aggregate
  is the flagged refinement); `bigville_cognition` integration uses two concrete
  drives, not C1's N-drive node set (robustness over generality, flagged).
- **Verdict-comparator divergence — RESOLVED (block 355000).** `bigville_court`'s
  `ct_sentence` fines the **Treasury**; `bigville_theft`'s `th_penalty`/`th_collect` used to
  fine **`court.coin`**. Reconciled in 6.4 Step C: theft's fine + damages now flow to the
  town **Treasury** (`tr.collected`), the same coffer, and the coin-conservation gate was
  updated with it (`court_coin()` reads the Treasury).
- **Gaps not deduped by content** (surfacing list) and similar are conversation-
  side, not bigville — noted only to avoid confusion.

---

## 7. Conventions

**File layout**
- Seeds: `seeds/bigville_<domain>.json` — graph data (rules/nodes/concepts),
  `id` + `version` + `depends_on` + `description` (with block number) +
  `self_load_only`.
- World adapters: `worlds/bigville_<name>_world.py` — mechanical ingest/emit
  only (`add_node`/`add_edge_unchecked`/`tick`/read-back). No decisions.
- Gates: `tests/test_<name>_migrated.py` — part of the migrated bench
  (`pytest tests/ -k migrated`), the regression guard.
- Prereg/results: `BIGVILLE_<NAME>_PREREG.md` (gates + falsifier, written
  first) and `BIGVILLE_<NAME>_RESULTS.md`.

**LEDGER block-number convention.** Each capability lands as one commit headed
`bigville <Rn> / <block-number>: <headline>` with honest residuals in the body.
Block numbers are monotonic (…324000 recognition, 336000 tools, 337000 theft…)
and appear in the seed `description`, so a seed is traceable to its commit.

**Gate / falsifier discipline.** Every capability ships (a) a positive gate
reproducing the qualitative signature, and (b) at least one falsifier / `=off`
ablation that must destroy the observable. Power the gate before any endgame
claim; deltas within ~3× the per-episode step are noise; report synthetic
mechanism and benchmark value separately.

**`.so` untouched.** A new capability never modifies the compiled binary. It is
graph data, or (deliberately, with its own Rust gates) a new DSL `Term`. If you
find yourself wanting to change the `.so` to add a *capability*, stop — the
capability belongs in graph data.

**The architecture rule (§2) overrides everything here.** If a convention seems
to invite a Python decision, it is being misread — the decision is a Rule.
