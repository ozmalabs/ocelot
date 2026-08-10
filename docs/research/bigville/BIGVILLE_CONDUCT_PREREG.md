# PREREG — Directed, Bond-coupled conduct + `help` (block 281000)

`seed_claim 281000 281999`: CLEAN — no collision detected. Canonical `.so`
`fd82dc2978dbb055496dd82390ac2ebe`; **NO Rust** (`git diff HEAD -- runners/dsl`
empty at land).

## The claim

The payoff of the arc: the affordance vocabulary (280000) offers agent-directed
actions whenever a target is in range; the decision core (279000) collapses over
them; and the held **Bond** (277000) decides WHOM. Conduct is *directed* by
relationships — you help/give to those you care for; and if you ever harm, it is
the resented rival, never the loved friend. Violence stays rare (a low prior that
needs deliberation) but is representable and correctly aimed. This also resolves
the "multi-target arbitration belongs in the collapse" residual of 280000.

Two parts:
1. **`help` joins the vocabulary** (280000 seed) — harm's pro-social mirror
   (Spelke/Hamlin core-knowledge help-vs-hinder). Same precondition as harm (an
   agent in range) but a HIGH prior. Added now per the science doc's
   deferred-until-multi-agent-norms build order.
2. **Bond → plan_value coupling as seed rules** (`bigville_conduct.json`) — each
   directed action's DEEP (model-based) value reads the held Bond toward its
   target: `harm.plan = plan_base + resent_gain·resentment − aff_gain·affection`;
   `help/transfer.plan = plan_base + aff_gain·affection`. The FAST pull (impulse =
   base_weight) is unchanged; the Bond only shapes the deep re-score. Reading held
   affect is a RULE (graph read), not adapter arithmetic.

## Pre-registered signatures (deterministic)

1. **Directedness** — harm→rival > harm→friend; help→friend > help→rival;
   harm→loved-friend driven below its base.
2. **Care aimed at the cared-for** — rival + friend present, no strong
   provocation → the collapse picks a pro-social action aimed at the FRIEND, not
   harm, not aimed at the rival.
3. **Never harm the loved** — no scene makes the collapse harm a loved friend.
4. **Provoked deliberate harm is directed** — a deeply resented + disliked lone
   rival makes the fast pro-social response mis-fit (high residual) → the collapse
   DEEPENS → harm, aimed at that rival (`deepened == 1`). Violence rare but real.
5. **Neutral acquaintance is not harmed.**
6. **FALSIFIER** — `conduct_resent_gain = conduct_affection_gain = 0` → plan_value
   collapses to plan_base for every directed action → no directedness (rival
   indistinguishable from friend).

## G-discipline

Additive: `bigville_conduct.json` + `bigville_conduct_world.py` +
`build_bigville_conduct.py` + `test_bigville_conduct_migrated.py`; plus `help`
added to the 280000 vocabulary (`world_affordances.json` / its builder / its gate).
Seeds `self_load_only`. Composes existing DSL Terms — ZERO new Rust. Canonical
`.so` untouched. Source-audited (no Python rule engine, no argmax/min/max over a
valuation in the adapter).
