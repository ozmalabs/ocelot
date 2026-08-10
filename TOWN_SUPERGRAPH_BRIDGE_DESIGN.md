# TOWN = SUPERGRAPH — bridge design (conduct → supergraph valuation)

READ-ONLY study + design pass for block 282000. Every claim below cites a
file:line I actually read. Nothing here edits code, seeds, or tests.

Goal (architect's reframe): re-express the three hand-tuned
`conduct_couple_{harm,help,transfer}` rules as ONE supergraph valuation —
`plan_value = self_value + w_supergraph(me→target) · (target's fulfilment
delta)` — where the held `Bond` IS the per-partner `w_supergraph`, and make
the town ONE supergraph over resident-subgraphs, each resident deciding at
its own reference frame.

---

## Sec 1 — How `supergraph_value` / `w_supergraph` compute TODAY

**Headline finding: there is NO per-pair weighted sum anywhere. The
existing "supergraph" is (a) a single scalar magnitude published by the
world adapter + (b) a per-AGENT sign-only gate.** The `Σ w(me→other)·f(other)`
form the reframe assumes does not exist yet — it must be built.

### 1a. The core fulfilment rule (`em_fulfilment_value`)
`seeds/core_emotions.json:620-703`. Term structure (read at 657-700):

```
fulfilment_value  =  [ w_supergraph > 0 ] ? supergraph_contribution : 0   +   mood_bias
```
- `w_supergraph` is read off the EmotionParams node `ep`
  (`core_emotions.json:670`) — used SIGN-ONLY inside an `IfThenElse/Gt` gate
  (`:662-688`), never as a multiplier.
- `supergraph_contribution` is read off the Appraisal node `ap`
  (`core_emotions.json:683`) — a single pre-computed scalar, NOT a sum over
  partners.
- guarded on `ep.enabled == 1` (`:636-650`).

`em_total_value` (`seeds/core_emotions.json:705-766`):
`total_value = happiness + fulfilment_value` (`:740-762`), where `happiness`
(`em_happiness`, `core_emotions.json:~575-616`) `= (individual_benefit −
individual_cost) + mood_bias` (`:594`, `:602`, `:611`). This is the
self-frame ledger.

So the value stack is: **self ledger (`happiness`) + gated collective scalar
(`fulfilment_value`)**. Psychopathy = `w_supergraph = 0` collapses the second
term; spite is a *separate* knob `w_spite` added in `ss_decision_value`
(`seeds/spite_skill.json:29`), NOT a negative `w_supergraph`.

### 1b. Where the numbers actually come from — the ADAPTER, not a rule
No rule ever writes `supergraph_contribution`, `supergraph_value`, or
`w_supergraph` (verified by scanning every seed's `set_attr` effect targets —
the only fulfilment write-backs are `fulfilment_value` and `hit_fulfilment`).
They are published by world adapters:
- `w_supergraph` is an EmotionParams attr, default `1.0`, per-agent scalar:
  `worlds/langsim_world.py:62` (`EP_DEFAULTS`), `worlds/glassbox_r1_world.py:57`.
- `supergraph_contribution` is written per-candidate by the world:
  `worlds/langsim_world.py:301-303` (give-candidate gets `G_CONTRIB`,
  keep-candidate gets `0.0`); `worlds/glassbox_r1_world.py:158-160`.

### 1c. The ONE multiplicative precedent (the template for the bridge)
`bc_pick_cheapest_hands` in `seeds/bigville_coll_evict.json` is the only place
`w_supergraph` is used as a WEIGHT rather than a gate. It Argmaxes candidate
doers `c` by `−(ask_wage + w_supergraph · injury_mag)`
(`bigville_coll_evict.json:635-672`: `Times` of `c.w_supergraph` at `:646` and
`c.injury_mag` at `:663`), reading `w_supergraph` per-candidate-doer. **This is
structurally exactly the reframe's `self_cost + w_supergraph · harm_to_other`
and is the proof the DSL already expresses it.**

### 1d. Modulator-layer fulfilment (`emx_fulfilment`)
`seeds/modulators.json:2698-2806`: fires `hit_fulfilment = 1` iff
`d.supergraph_value > 0 AND ms.w_supergraph > 0` (`:2762-2791`). Again a
boolean predicate over an adapter-published `supergraph_value` (on a Drive
node; default set in `domains/doom_emotion_narration_ingest.py:62`) gated by a
per-agent `w_supergraph` on the ModulatorState. Confirms the pattern is
uniform: **magnitude = adapter; `w_supergraph` = per-agent sign gate.**

---

## Sec 2 — Reference frame / level of selection

`core_emotions.json:7` states the governing principle explicitly:
*"THE REFERENCE-FRAME-PER-EMOTION PRINCIPLE: each emotion's value function
reads value at a LEVEL OF SELECTION — the individual emotions read the
individual ledger (happiness = benefit−cost); FULFILMENT reads the SUPERGRAPH
(w_supergraph gates the contribution term)."*

**There is no `reference_frame` / `level_of_selection` node or attr.** The
"level of selection" is encoded *structurally*, as WHICH ledger a value term
reads: `individual_benefit/individual_cost` = self frame; `supergraph_contribution`
= the level above. The frame is implicit in the term, not a first-class datum.
The knob that says "how much do I weight the level above me" is the single
scalar `w_supergraph` — currently one number per agent, undirected.

Consequence for the reframe: "each resident decides at its own reference
frame" has **no existing representation to hang on** — it must be introduced.
The natural home is the actor hub already minted per resident
(`ConductState`, `worlds/bigville_conduct_world.py:60`) and the `in_scene`
edge that already scopes a resident's candidate actions (Sec 5).

---

## Sec 3 — Does fulfilment enter a DECISION today?

**Two separate valuation stacks exist, and they do NOT meet.**

1. **Emotion-economy selectors DO read fulfilment.** `total_value` /
   `decision_value` (which include the gated `fulfilment_value`) are the
   Argmax key in the glassbox/harvest/spite family: `glassbox_r1_social.json:29`
   ("the graph's Argmax over its two candidate Appraisals by total_value"),
   `spite_skill.json:29` (`decision_value = individual_benefit − gated_cost +
   mood_bias + fulfilment_value + spite_value`). So fulfilment already drives
   action selection in the 234000/212000/213000 line.

2. **The 279000 decision core does NOT read fulfilment.** It Argmaxes over
   `NodesOfType("DecAction")` by `impulse` (shallow, `bigville_decision_core.json:61-77`)
   and by `plan_value + rationalise_gain · impulse` (deep,
   `bigville_decision_core.json:~799-854`; `plan_value` at `:835`,
   `rationalise_gain` at `:846`, `impulse` at `:854`). `plan_value` is set
   *directly* by my conduct rules; nothing in the core consults
   `total_value` / `fulfilment_value` / `supergraph_contribution`.

So the decision core and the supergraph/fulfilment economy are today
**disjoint**. The conduct coupling (281000) is in fact the *only* bridge that
exists between per-pair relationship state and the decision core's
`plan_value` — and it is hand-tuned, not framed as `w_supergraph`.

**Design implication:** the bridge should compute the supergraph term
*inside the `plan_value` valuation* (the coll_evict template), NOT try to make
the decision core read the emotion economy's `total_value` (different node
type — Appraisal vs DecAction — and different fixpoint). Keep `plan_value` as
the single decision-core currency; make it a supergraph sum.

---

## Sec 4 — Bond ↔ `w_supergraph` relationship

**No existing bridge. The Bond is a separate, richer representation that
SHOULD FEED a per-pair `w_supergraph` — and there is already a dead slot named
for exactly this job.**

Bond node slots (`worlds/bigville_bond_world.py:61-64`):
`affect_trust, affect_gratitude, affect_resentment, affect_contempt,
affect_affection, affect_fear, attraction, romantic, tie_strength, band_code,
**altruism_bias**`. The Bond is DIRECTED: `holds_bond` (actor→Bond) +
`toward` (Bond→target) (`bigville_bond_world.py:130-131`,
`bigville_conduct_world.py:99-102`).

Key finding: **`altruism_bias` is minted but read by ZERO rules** (grep over
all seeds returns no reader). It is seeded as a per-pair prior — e.g. blood-kin
gets `altruism_bias=0.3` (`bigville_bond_world.py:76`). It is the natural,
purpose-named home for the per-pair `w_supergraph(me→target)`.

Two candidate mappings for `w_supergraph(me→target)`:
- **(A) Direct: `w_supergraph(me→target) := Bond.altruism_bias`** — cleanest;
  uses the dead slot as-is; keeps the care weight dissociable from the
  transient affect slots (matches `bigville_bond_world.py:70-72` "you do not
  need to like your kin").
- **(B) Derived: `w_supergraph(me→target) := f(altruism_bias, affect_affection,
  affect_resentment)`** — e.g. `altruism_bias + k·affect_affection −
  k·affect_resentment`, so a resented rival earns a NEGATIVE per-pair weight
  (the spite region, per-pair) and affection raises care. This reproduces the
  current conduct behaviour (harm rises with resentment, help rises with
  affection) as a *sign of a single per-pair weight* rather than two separate
  gains.

Recommendation: **(B)**, because it is behaviour-preserving for conduct AND
gives spite a principled per-pair form (`spite_skill.json:7` frames `w_spite`
as "the negative-social MIRROR of `w_supergraph`" — a signed per-pair
`w_supergraph` subsumes both). Keep the global per-agent `w_supergraph`
(psychopathy knob, EmotionParams) as a MULTIPLIER on top: effective weight =
`ep.w_supergraph · bond_w(me→target)`, so a global psychopath (`ep.w_supergraph
= 0`) zeroes ALL per-pair care regardless of Bond — which is exactly the
desired semantics.

---

## Sec 5 — THE BRIDGE PLAN

### 5.1 The valuation (replaces the 3 conduct rules with 1 supergraph rule)

Target form:
```
plan_value(d)  =  self_value(d)  +  w_super_eff(m→o) · target_fulfilment_delta(d, o)
w_super_eff(m→o)  =  ep.w_supergraph            (global psychopathy gate/scale, EmotionParams)
                   · bond_w(m→o)                (per-pair, from Bond — Sec 4B)
```
where, matching the existing conduct match
(`m in_scene d`, `d aims_at o`, `m holds_bond bond`, `bond toward o`):
- `self_value(d) = d.plan_base` (the vocabulary default,
  `bigville_conduct_world.py:33` `_DIR_PLAN`) — for `harm` this is negative
  (`−0.40`), for `help/transfer` positive (`0.60/0.55`), i.e. the actor's own
  stake in the act.
- `target_fulfilment_delta(d, o)` = how much the act changes the TARGET's
  fulfilment. Sign is intrinsic to the action type: `harm` LOWERS it (negative
  delta), `help/transfer` RAISE it (positive delta). Magnitude is an action
  attr the affordance vocabulary/world publishes (the same way
  `supergraph_contribution`/`injury_mag` are adapter-published today —
  Sec 1b/1c), e.g. `d.target_effect`. **This keeps magnitude in the adapter
  and weight in the graph, honouring the existing split.**

Then the single rule (one `set_attr d plan_value` per directed DecAction) is
the coll_evict Term shape (`bigville_coll_evict.json:635-672`): a `Plus` of
`plan_base` and a `Times` of `w_super_eff` and `target_effect`. The three
`conduct_couple_*` rules collapse into ONE `conduct_supergraph_value` rule
whose match is action-type-agnostic (drop the `Eq d.name` guard — the sign now
lives in `target_effect`, not in three separate rule bodies).

**Behaviour equivalence to 281000:** with `bond_w = altruism_bias +
k·affect_affection − k·affect_resentment` and `target_effect` carrying the
action sign, a resented rival (high `affect_resentment` → negative `bond_w`)
times a negative harm-delta yields a POSITIVE contribution to harming them
(harm scores UP) — reproducing `conduct_couple_harm`
(`bigville_conduct.json` `conduct_couple_harm`: `plan_base +
resent_gain·affect_resentment − affection_gain·affect_affection`). Help/transfer
toward a loved target (positive `bond_w` × positive delta) score UP —
reproducing `conduct_couple_help/transfer`. The two hand-tuned gains
(`conduct_resent_gain`, `conduct_affection_gain`) become the single `k` inside
`bond_w`. FALSIFIER preserved: `k = 0 AND altruism_bias = 0` → `bond_w = 0` →
`plan_value = plan_base` → no directedness (same falsifier as
`bigville_conduct.json` description).

### 5.2 Per-actor scoping = reference frame

The decision core currently Argmaxes over GLOBAL `NodesOfType("DecAction")`
(`bigville_decision_core.json:63-65`), filtered only by
`act.impulse > m.consideration_threshold` (`:70-86`). For a town of many
residents this pools every resident's actions into one selection — wrong.

But the scoping edge ALREADY EXISTS: DecActions are minted with
`m in_scene d` (`bigville_conduct_world.py:75`). **The reference frame of a
resident = the set `Neighbours(m, "in_scene")`.** The minimal, correct change
is to swap the Argmax source in the decision core from
`NodesOfType("DecAction")` to `Neighbours(m, "in_scene")` (the actor hub `m`
is already bound by the core's `m has_net rn` match,
`bigville_decision_core.json:23`). Each resident then decides only over its own
in-scene afforded actions — one supergraph, resident-scoped subgraphs, each at
its own frame. This is a change to the GATED 279000 core (see 5.3).

### 5.3 What is pure-additive seed vs what touches gated code

**Pure-additive (new seed `seeds/bigville_supergraph_conduct.json`,
`self_load_only`, nothing depends on it):**
- the single `conduct_supergraph_value` rule (Sec 5.1). It writes `plan_value`
  exactly like the conduct rules do, so it drops into the existing decision
  loop with zero core change. Ship it depending on `bigville_conduct` being
  *absent* (or superseding it) to avoid a double-write on `plan_value` in the
  fixpoint.
- a `bond_w` derivation rule (or fold it inline) reading Bond
  `altruism_bias/affect_affection/affect_resentment` — all existing slots
  (`bigville_bond_world.py:61-64`); `altruism_bias` currently dead (Sec 4).
- the world adapter publishes `target_effect` per directed DecAction
  (mechanical, same class as `supergraph_contribution`/`injury_mag` —
  admissible adapter I/O, `worlds/langsim_world.py:301-303` precedent).

**Touches the gated 279000 decision core (needs its own gate + parity):**
- the per-actor scoping swap (Sec 5.2). Changing the Argmax `source` in
  `dc_collapse_pass` / `dc_collapse_settle` / `dc_collapse_deepen` (five
  occurrences of `NodesOfType("DecAction")` at
  `bigville_decision_core.json:63,134,205,294,366,436,802,881,960,...`) is a
  semantic change to a gated block — do it behind a flag or a v1.1.0 with a
  parity test (single-actor case must stay byte-identical, since for one actor
  `Neighbours(m,"in_scene") == NodesOfType("DecAction")`).

**Does NOT touch emotion seeds.** The bridge deliberately does NOT route
`plan_value` through `em_total_value`/`fulfilment_value`
(`core_emotions.json:620-766`) — those operate on Appraisal nodes in a
different fixpoint (Sec 3). The bridge re-uses the *pattern* (`w_super · magnitude`)
not the *nodes*.

---

## Sec 6 — Gaps, risks, recommended minimal first build

### Honest gaps / risks
1. **`w_supergraph` is per-agent today, not per-pair.** The reframe's
   `w_supergraph(me→target)` is a NEW quantity. Do not overload the
   EmotionParams `w_supergraph` (that stays the global psychopathy scalar);
   introduce the per-pair weight as `bond_w` on the Bond (Sec 4). Naming
   discipline matters — calling the Bond-derived weight `w_supergraph` risks
   confusing it with the global gate that multiplies it.
2. **`target_fulfilment_delta` is a magnitude the world must publish.** Today
   nothing computes a target's fulfilment change from an action; the adapter
   will supply `target_effect` per action type. This is honest (matches the
   existing adapter-publishes-magnitude split) but it means "fulfilment delta"
   is a stipulated action attr, NOT yet the target's own `em_fulfilment`
   readout. A later rung could ground it in the target's actual fulfilment
   response; the first build should not.
3. **Double-write hazard in the fixpoint.** Both `bigville_conduct`'s three
   rules and the new single rule write `plan_value` on the same DecAction. Do
   not load both (spite_skill's fresh-key discipline, `spite_skill.json:29`,
   is the precedent — but here we deliberately reuse `plan_value`, so
   supersede rather than coexist).
4. **Scoping change is in gated code.** Sec 5.2 is the only piece that touches
   279000; it carries the highest regression risk and needs the single-actor
   parity gate. Everything else is additive.
5. **Sign convention must be unambiguous.** Whether `target_effect` for `harm`
   is negative (and `bond_w` for a rival negative, product positive) must be
   pinned with a table + a test, or the harm-a-rival behaviour silently flips.

### Recommended minimal first build (block 282000)
**Do the pure-additive half first; defer the gated scoping swap.**

1. New seed `seeds/bigville_supergraph_conduct.json` (`self_load_only`,
   `depends_on: []`) with ONE rule `conduct_supergraph_value`:
   `plan_value = plan_base + (ep.w_supergraph · bond_w) · target_effect`,
   `bond_w = altruism_bias + k·affect_affection − k·affect_resentment`, matched
   on the existing `m in_scene d / d aims_at o / m holds_bond bond / bond toward o`.
   Uses only `Plus/Minus/Times/Attr` — zero new Rust, coll_evict Term shape
   (`bigville_coll_evict.json:635-672`).
2. Adapter change (mechanical): publish `target_effect` per directed DecAction
   in `worlds/bigville_conduct_world.py` alongside `plan_base`
   (`bigville_conduct_world.py:69-77`); read back nothing new.
3. Gate: a parity test showing the new single rule reproduces the three
   `conduct_couple_*` outcomes on the 281000 fixtures (rival→harm-up,
   loved→help/transfer-up, violence-rare) AND the falsifier
   (`k=0 ∧ altruism_bias=0` → `plan_value = plan_base`, no directedness).
4. Keep `bigville_conduct` and the new seed mutually exclusive at load time
   (supersede) to avoid the `plan_value` double-write.

Defer to 282000-b: the per-actor `Neighbours(m,"in_scene")` scoping swap in
the 279000 core, behind its own version bump + single-actor byte-parity gate.
That is the "town is one supergraph, each resident at its frame" step, and it
is the one change that touches gated code — isolate it.

This sequencing lands the *valuation* reframe additively and provably
behaviour-preserving first, and quarantines the *scoping* reframe (the only
gated-code touch) into a second, separately-gated step.
