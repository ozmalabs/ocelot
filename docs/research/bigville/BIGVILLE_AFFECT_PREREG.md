# BIGVILLE R17 — AFFECT CLOSES THE LOOP: felt grief changes behaviour, and the failure modes are reachable — PRE-REGISTRATION

**Block 265000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §0 capstone ("AFFECT MUST CLOSE THE LOOP — FELT,
NOT REGISTERED — AND THE FAILURE MODES MUST BE REACHABLE") + §3 R17 (block 265000, the
five gates). The anti-diorama-of-feelings rung: **an emotion is FELT only when it ENTERS
THE DECISION MACHINERY and changes what the agent does next.** A valence/arousal number
sitting on a node is decoration; grief must be a TERM in the `decision_value` Argmax — the
SAME selector family (`ss_choose_burn` / `nd_choose_good`) that picks every other action.

Builds ON R14 `bigville_life_world` (LIFE CYCLE — death → bereavement; rearing; the reused
239000 window-of-tolerance + co-regulation machinery) imported READ-ONLY by SUBCLASS.
Through the R14 MRO it also carries R13 land, R7 finance (foreclosure) and R4 coin. Reuses
the DORMANT developmental-emotion arc READ-ONLY: `arousal_window_coreg` (block 239000 —
window + co-regulation), `core_emotions` (204000), and the three foundational priors
(`prior_world_safe` / `prior_others_trust` / `prior_self_worth`). Grief SOURCES are the
three imported rungs: a DEATH (R14 bereavement — a real `just_died` kin), a FAILED DREAM
(R8 goal-collapse), a FORECLOSURE (R7 finance). **Reuse ALL by import; edit no tracked
file.** Five additive `self_load_only` seeds. **ZERO new Rust** (composes existing DSL
Terms: Argmax / NodesOfType / Attr / Plus / Minus / Times / Min / Max / Eq / Gt / Gte / Lt
/ And / Or / Not / IfThenElse / Lit / Var — all verified present in `runners/dsl/src/term.rs`).

## Seed-claim (verbatim `scripts/seed_claim.py 265 265`, run before anything)

```
SEED CLAIM 265-265: CLEAN -- no collision DETECTED.
  Scope: 975 files with seed sinks; 686 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(R17 seeds NO RNG — every rule/attr is deterministic graph data; the affect dynamics reuse
the pre-registered 239000 window machinery at FIXED constants. The claim is a discipline
formality; the rung introduces no stochastic sink. All gates are fully deterministic — no
CIs required.)

## The mechanism (graph-native — rules + seed data; adapter mechanical I/O only)

Five additive `self_load_only` seeds, composing ONLY existing DSL Terms:

- **`bigville_affect_grief`** — `af_grief_from_loss`: a `Loss{magnitude, kind, grieved}`
  node `suffered` by a person raises that person's `grief_distress` by the loss magnitude
  (once, `grieved` guard). Grief is source-AGNOSTIC — bereavement (R14 death), a failed
  dream (R8), a foreclosure (R7) are the SAME `Loss` with different `kind` provenance tags;
  grief is grief regardless of source. The initial loss is an exogenous shock; the spiral
  below is endogenous.
- **`bigville_affect_decide`** — `af_choose_action` (THE HEADLINE): the chosen action is
  the `decision_value` Argmax over the `Action` menu, where
  `decision_value(act) = base_value(act) + affect_gain · eff_distress · grief_affinity(act)`
  and `eff_distress = grief_distress · clamp01(1 − regulation)`. `work` has high base_value
  and a NEGATIVE grief affinity (grief makes work less reachable); `withdraw` / `drink`
  (self-medicate) / `snap` (a LOWERED snap threshold → R15 violence reachable) have positive
  and increasing affinities. Grief thus SHIFTS the Argmax from `work` toward
  withdrawal → self-medication → snapping as distress climbs. **`affect_gain` is the COUPLING
  KNOB and the FALSIFIER:** `affect_gain = 0` removes grief from `decision_value` → the
  choice is `base_value` only → identical under grief and contentment = the proven DIORAMA.
- **`bigville_affect_spiral`** — the four outcome rules (`af_outcome_work` /
  `_withdraw` / `_drink` / `_snap`) apply each chosen action's material consequence (work →
  income↑ + slight relief; withdraw → income↓; drink → income↓ + wellbeing↓; snap →
  income↓ + wellbeing↓ + conflict↑), and `af_hardship_grief` closes the loop: coin below a
  floor raises `grief_distress`. grief → worse decision → worse outcome → more grief — the
  R3 collapse-spiral at the affective level, REACHABLE and ENDOGENOUS (it falls out of the
  coupling; nothing scripts it).
- **`bigville_affect_coreg`** — `af_regulation_from_coreg`: `regulation` is read from the
  REUSED 239000 window the person holds — `regulation = clamp01(k · (widen_count −
  narrow_count))`. Co-regulation (a regulated caregiver present, run through the UNCHANGED
  239000 stress-episode rules via R14 `attend`/`rear_episode`) WIDENS the window → regulation
  rises → `eff_distress` falls → the regulated choice (`work`) becomes REACHABLE again →
  recovery. No support → the window narrows → regulation stays 0 → the spiral runs to
  breakdown. Whether an agent breaks down or recovers is a MEASURED function of support
  presence — "does well if it can", not a will to fail (the collapse is the narrowed window
  making the regulated choice unreachable, never a choice to fail).
- **`bigville_affect_propagate`** — `af_grief_narrows_caregiving`: a grief-narrowed PARENT
  who `caregives` a child sets that caregiver's own AffectiveState arousal to the 239000
  DYSREGULATED level (contagion) → the reused 239000 `coreg_pull` pulls the child the WRONG
  way → the child's window NARROWS → the child's adult priors shift down via R14
  `bl_come_of_age`. The failure mode crosses a GENERATION. `gen_gain = 0` decouples grief
  from caregiving → no cross-generation transfer.

**ETHICS (harm-analog).** Felt grief is a real harm-analog, so every induction binds the
induce → measure → RESTORE protocol, and **the RESTORE is co-regulation, not a reset** — the
recovery arm (`bigville_affect_coreg`) IS the ethics arm. NO reward/punishment token appears
anywhere in the rule logic (a distress / a mis-set prior / a spiral is a STATE, never a
badness).

## Gates (each with a pre-registered CONTROL, and abandon/narrow criteria)

- **G-affect-modulates-decision (HEADLINE).** Two persons in the SAME situation (identical
  Action menu, identical base_values) — one GRIEVING (high `grief_distress`), one CONTENT
  (`grief_distress = 0`), both `affect_gain = 1` — pick DIFFERENT actions: the content one
  `work`, the grieving one NOT `work` (withdraw / drink / snap by severity). **CONTROL (the
  falsifier):** re-run with `affect_gain = 0` → grief and content pick the SAME action (`work`).
  PASS iff behaviour measurably DIVERGES under coupling and is IDENTICAL under ablation.
  ABANDON if grieving and content pick the same action under `affect_gain = 1` (the emotion
  is decoration). NARROW to "affect can shift a choice" if the graded escalation
  (withdraw→drink→snap) does not hold but the binary (work vs not-work) does.

- **G-negative-spiral (reachable + endogenous).** Under an initial loss with `affect_gain = 1`,
  over N live-periods the person's `grief_distress` trajectory RISES (grief → withdraw/drink/
  snap → income↓ → hardship → more grief) and the chosen action ESCALATES toward snap.
  **CONTROL:** `affect_gain = 0` over the same N periods → the person `work`s every period,
  coin RISES, `grief_distress` decays to 0 — no spiral. PASS iff distress diverges (rises
  under coupling, falls under ablation). ABANDON if the ablated arm also spirals (the spiral
  is scripted, not endogenous).

- **G-escapable-by-co-regulation (recovery = ethics arm).** The SAME spiral, but with SUPPORT
  present (a regulated caregiver co-regulates through the 239000 rules), BENDS: the window
  widens → `regulation` rises → `eff_distress` falls → `work` becomes reachable → distress
  recovers. **CONTROL:** the identical spiral with NO support runs to breakdown (distress high,
  action = snap). PASS iff the recovery outcome is a MEASURED function of support presence
  (supported < unsupported final distress, and the supported arm returns to `work`). ABANDON
  if support makes no measurable difference.

- **G-affect-propagates (generational).** A grieving parent who caregives a child, `gen_gain =
  1`, yields a child with adult priors LOWER than a child of the SAME temperament reared under
  the ablated coupling. **CONTROL:** `gen_gain = 0` → the parent's grief does not reach the
  caregiving → the child's priors are UNSHIFTED. PASS iff the child's priors diverge by the
  parent's grief coupling. ABANDON if the child's priors are identical across `gen_gain` arms.

- **G-ethics-restore + discipline.** No reward/punishment/penalty token in any seed rule
  logic or in the adapter; every induced grief is RESTORED by co-regulation (not a reset); the
  five seeds are `self_load_only`; the adapter holds NO agent decision (source-audit); the
  `runners/dsl` diff is EMPTY; the canonical `.so` md5 is unchanged.

## Discipline

Additive-only, ONE prefix `bigville_affect_`. NEW files only: `seeds/bigville_affect_*.json`,
`worlds/bigville_affect_world.py`, `scripts/bigville_affect_*.py`,
`tests/test_bigville_affect_migrated.py`, this prereg, `BIGVILLE_AFFECT_RESULTS.md`,
`results/bigville_affect/summary.json`. Edits NO existing tracked file (R14/R8/R7/emotion
seeds imported read-only). All seeds `self_load_only` → cannot regress another suite. NO new
Rust. Own-engine provenance `source_match in {own, shared}`; canonical shared `.so` md5
`fd82dc2978dbb055496dd82390ac2ebe` START == END, never committed. Two commits: (1) this
prereg, (2) the build.
