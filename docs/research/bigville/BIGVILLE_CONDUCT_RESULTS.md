# RESULTS — Directed, Bond-coupled conduct + `help` (block 281000)

All six pre-registered signatures reproduce. **`test_bigville_conduct_migrated.py`
7/7 + `test_world_affordances_migrated.py` 10/10 (now 9 types) + decision core /
bond / baseline 33/33 unchanged — 50/50 on the canonical engine
`fd82dc2978dbb055496dd82390ac2ebe`**. `runners/dsl` diff EMPTY — ZERO new Rust.
Prereg `BIGVILLE_CONDUCT_PREREG.md`.

## What landed

- `help` added to the affordance vocabulary (`world_affordances.json`, now 9
  ActionTypes / 18 rules) — harm's pro-social mirror: precondition = an agent in
  range, base_weight **0.70** (HIGH), effect raises the target's vital state.
- `seeds/bigville_conduct.json` — 3 `conduct_couple_*` rules (harm/help/transfer)
  reading the held Bond's `affect_resentment` / `affect_affection` into each
  directed action's `plan_value`. Gains are knobs on the ConductState.
- `worlds/bigville_conduct_world.py` — the loop: mint actor + co-present targets
  with held Bonds + directed/non-directed options, run provision + coupling +
  the decision collapse, read back the chosen action AND its target.

## The measured signatures

| # | signature | measured |
|---|---|---|
| 1 | directedness | rival(resent 3, aff −1) + friend(aff 3): harm→Rival **1.6** > harm→Friend **−1.9**; help→Friend **2.1** > help→Rival **0.1** |
| 2 | care aimed at the cared-for | rival+friend+food → chosen **help → Friend** (deepened); not harm, not aimed at rival |
| 3 | never harm the loved | harm→loved-friend plan strongly negative; collapse never picks harm→friend |
| 4 | provoked deliberate harm is directed | resented+disliked lone rival (resent 5, aff −4) → chosen **harm → Foe, deepened=1** (fast pro-social response mis-fit → residual → deepen → harm) |
| 5 | neutral not harmed | neutral acquaintance → chosen **help** (fast pro-social default), not harm |
| 6 | FALSIFIER | gains=0 → harm→R **−0.40** == harm→F **−0.40**; help→R **0.60** == help→F **0.60** — no directedness |

## What this establishes — the arc closes

Relationships, speech, and now conduct are ONE loop on ONE collapse over what the
world affords:

- **Whom you act on reads the held Bond** — help/giving flow to the cared-for,
  harm (if ever) to the resented. The relationship is not a sim edge; it is held
  affect the conduct rule reads, and it *directs* the choice.
- **The fast default is pro-social.** Seeing anyone, the shallow collapse settles
  on the high-prior action (help/greet). Violence is not an impulse here — it only
  appears when the fast pro-social response is a bad enough fit (high residual)
  that the collapse DEEPENS and a strongly resented target out-scores every
  alternative. "Greet… wait… no" — deliberation revealing the automatic warmth is
  wrong *for this person*. Rare, deliberate, directed.
- **The drift is reversed, end to end.** No rule enumerates or "considers"
  transgressions; the world offers a low-weight `harm` affordance when a body is
  present, the Bond shapes its deep value, and the collapse settles — almost always
  elsewhere.

## Honest residuals (NOT patched)

- **Standalone still.** The conduct loop runs on a synthetic scene (targets +
  held Bonds passed in). Wiring it into the live integ5/play town — residents'
  real proximity → `sees`, their real Bonds → the coupling, per resident per tick
  — is the next block, and carries a performance question (a collapse per resident).
- **The affect provenance is 277000's.** This block READS `affect_affection` /
  `affect_resentment`; the bond-update rules that EARN them from experience/gossip
  are block 277000 (gated separately). The full chain experience → bond → conduct
  is proven in two linked pieces, not one run.
- **`communicate` not yet Bond-directed here.** Speaking warmly vs barbed by
  relationship is the speech faculty's job (278000); the conduct coupling covers
  harm/help/transfer. Directed communicate is a natural add.
- **Player viz not done.** The player showing residents deliberate (deepen) only
  when provoked, and violence as the rare directed event, is deferred with the
  town integration.
