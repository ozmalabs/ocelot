# PREREG — Supergraph conduct valuation (block 282000-a)

`seed_claim 282000 282999`: CLEAN. Canonical `.so` `fd82dc2978dbb055496dd82390ac2ebe`;
**NO Rust**.

## Honest correction up front

The reframe — "the town is a supergraph, so conduct value = self-value +
w_supergraph(me→target)·(target's fulfilment delta)" — assumed that per-pair
weighted sum already existed in the emotion framework. **It did not**
(`TOWN_SUPERGRAPH_BRIDGE_DESIGN.md` sec 1, file:line-cited). Today the supergraph
is (a) a per-candidate scalar magnitude the world adapter publishes, and (b) a
per-AGENT sign-only gate `w_supergraph` used inside an `IfThenElse/Gt`
(`core_emotions.json:620-703`), never as a multiplier. So this block BUILDS the
per-pair form, grounded in three existing pieces rather than inventing wholesale:
- the ONE multiplicative `w_supergraph·magnitude` precedent
  (`bigville_coll_evict.json` `bc_pick_cheapest_hands`) — the Term shape;
- the DEAD, purpose-named Bond slot `altruism_bias` (minted by
  `bigville_bond_world.py:64`, read by zero rules) — the per-pair weight's home;
- the per-agent `w_supergraph` gate — kept as a global multiplier on top.

## The claim

ONE action-type-agnostic rule `conduct_supergraph_value` replaces the three
hand-tuned `conduct_couple_{harm,help,transfer}` rules (281000):

```
plan_value(d) = plan_base(d) + ( ep.w_supergraph · bond_w(m→o) ) · target_effect(d)
bond_w(m→o)   = altruism_bias + k·affect_affection − k·affect_resentment
```

The sign of the coupling now lives in `target_effect` (harm LOWERS the target's
fulfilment < 0; help/transfer RAISE it > 0) times a SIGNED per-pair weight
`bond_w`, so harming a resented rival (bond_w<0 × effect<0) scores UP, helping a
loved friend (bond_w>0 × effect>0) scores UP. `target_effect` is adapter-published
per directed DecAction (the existing magnitude-in-adapter split). Load INSTEAD OF
`bigville_conduct` (both write `plan_value` — supersede, never coexist).

## Pre-registered signatures

1. **Byte parity on harm** — side by side with `valuation="couple"` (281000): the
   supergraph rule reproduces `harm→rival` and `harm→friend` plan-values exactly
   (the 1.6 / −1.9 fixtures).
2. **Chosen-action parity** — every 281000 signature: rival+friend → care aimed at
   the friend, not harm; provoked lone rival → deliberated (`deepened=1`), directed
   harm; neutral → not harmed.
3. **Directedness orderings** — harm→rival > harm→friend; help→friend > help→rival.
4. **NEW — psychopathy knob** — `ep.w_supergraph = 0` zeroes ALL per-pair care
   (every directed plan → plan_base); a global psychopath weights no one.
5. **NEW — `altruism_bias` revived** — a kin prior (0.3) with zero affect raises
   help above its base: care without liking.
6. **Spite as a signed per-pair weight** — resentment makes bond_w negative → harm
   scores above its base.
7. **FALSIFIER** — `conduct_k=0 ∧ altruism_bias=0` → bond_w=0 → plan_value =
   plan_base → no directedness.

## Scope / discipline

Additive: new seed `bigville_supergraph_conduct.json` (ONE rule, `self_load_only`)
+ adapter publishing `target_effect` + minting an `EmotionParams(w_supergraph)`
node + the gate. Composes existing DSL Terms (coll_evict shape) — ZERO new Rust.
Does NOT touch the gated 279000 decision core (that is the per-actor SCOPING swap,
deferred to 282000-b) or the emotion seeds. Canonical `.so` untouched.
