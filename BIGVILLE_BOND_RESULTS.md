# BIGVILLE RUNG 1/3 — THE HELD BOND — RESULTS

**Block 277000.** Pre-registration: `BIGVILLE_BOND_PREREG.md` (commit
`90fb092b97d47a156b6a30f6e0eeaa1d8c79af69`, committed BEFORE any number here).
Design blueprint: `BIGVILLE_SPEECH_SCIENCE.md` Addenda 2/3/4. Base `b53bdacae0`.
Engine: own build `_native.abi3.so` md5 `10f65be659e0d9a9290aff39f7f5b92a`
(`scripts/engine_build.sh`; `runners/dsl` diff vs base EMPTY). Seed
`seeds/bigville_bond_update.json` blob `8e23416d4ce879481b29859afe5fca02b1635ed3`.

The relationship representation moved OUT of the sim (a bare, symmetric, static
`A -kin/hates-> B` WORLD edge) and INTO the agent graph as a per-agent, DIRECTED,
subjective, updatable **`Bond(A→B)`** with THREE dissociable slots + an EARNED
tie_strength/band. Every update DECISION is a seed RULE (7 `bond_*` rules composing
existing DSL Terms — Attr/Plus/Times/Minus/Gt/Eq/And/IfThenElse/Abs/Argmax/
Neighbours); the adapter only ingests/arms/reads. ZERO new Rust.

## Two creator sharpenings, both baked in
1. **"You do not need to LIKE your kin."** The kin prior forces NO positive affect or
   attraction — the affect/attraction slots and the structural tie-band are INDEPENDENT.
   Genetics contributes only a small `altruism_bias` + a small tie head-start.
2. **"A step-brother can be MORE kin than kin."** The kin-band is EARNED from
   care/cohabitation (a graded `tie_strength` built by rules), NOT assigned by a genetic
   edge. A chosen/adopted tie can reach `family` and exceed a neglected blood tie.

## Gates (all green): `pytest tests/test_bigville_bond_migrated.py -q` → **11 passed**

### G-forms — a Bond FORMS directed with three slots, kin forces no feeling
`Alice` blood-kin to `Bob`, elaborated then ticked (glass-box, straight off the graph):
```
Bond(Alice→Bob)  belief_trust 0.0 · affect_affection 0.0 · affect_trust 0.0 ·
                 attraction 0.0 · tie_strength 1.0 · band consequential_stranger ·
                 altruism_bias 0.3
```
All three slots present; **affect and attraction are ZERO** (no liking forced onto kin);
genetics shows only as `altruism_bias=0.3` + a tie head-start of 1.0; band is EARNED
(`consequential_stranger`, NOT auto-`family`). Elaboration is real: fed a benign
observation, the ToM decode (generalized `bd_mary_infers`, per-Bond codebook) infers
`belief_disposition=trustworthy`, `belief_trust=+1.0`.

### G-asymmetry — A→B ≠ B→A after the same event
`Bob` defaults on a loan to `Alice` (valence −1, magnitude 2). Bond(Alice→Bob) sours
while Bond(Bob→Alice) is untouched:
```
Bond(Alice→Bob)  affect_trust −6.0 · attraction −6.0 · affect_resentment 6.0 · tie 0.0
Bond(Bob→Alice)  affect_trust  0.0 · attraction  0.0 · affect_resentment 0.0 · tie 0.5
```
A shared symmetric world edge could not represent this directed divergence.

### G-dynamic-asymmetric — betrayal drops HARDER than kindness raises (negativity bias)
Equal magnitude M=2, fresh acquaintance bonds:
```
kindness (gift,  +M):  affect_trust  = +2.0
betrayal (eviction,−M): affect_trust = −6.0     →  |Δ_betrayal| = 3× |Δ_kindness|
```
The 3× is `neg_weight/pos_weight` — a **tunable knob**, not a hard-coded magic ratio
(only the *direction* of the asymmetry is the science; Gottman 5:1 is contested). The
betrayal also raises resentment/contempt/fear and triggers the global re-appraisal
(standing affection/gratitude scaled by `reappraise_factor`).

### G-third-party — gossip shifts a bond A never directly experienced, weighted by source
C bad-mouths B (content −1). A has NEVER met B (`belief_trust` starts 0):
```
A trusts C   (belief_trust A→C = +1):  A→B belief_trust  0 → −0.5   (revised down)
A distrusts C(belief_trust A→C = −1):  A→B belief_trust  0 → +0.5   (discounted/inverted)
```
The INDIRECT reputation path (generalizes `bl_badmouth`/`bl_townsfolk_opinion`): A updates
B from what C says, weighted by A's trust in C — gossip is evidence, never ground truth.

### G-falsifier — update_gain=0 freezes every bond to its static prior (the old behavior)
The SAME battery (betrayal + hostile observation + similarity + cohabitation) applied to a
frozen bond (`update_gain=0`) vs a live one:
```
FROZEN:  affect_trust 0 · attraction 0 · resentment 0 · belief_trust 0 · band unchanged  (= prior)
LIVE:    affect_trust <0 · attraction <0 · resentment >0 · belief_trust moved
```
Zeroing the coupling knob reproduces the OLD bare-label behavior exactly — proving the
bonds are genuinely dynamic (mirrors `af_choose_action`'s `affect_gain` falsifier).

### earned-kin (sharpening 2) — chosen/adopted exceeds neglected blood
`Ma` holds a blood-kin bond (then neglected + one rift) and a `chosen` bond (5 rounds of
cohabitation + care). Built purely from history:
```
Bond(Ma→Chosen)  tie_strength 13.5 · band family
Bond(Ma→Blood)   tie_strength  0.75 · band consequential_stranger
```
The chosen tie reaches `family` and far exceeds the withered blood tie — kinship is EARNED.

### decouple (sharpening 1) — a resented, avoided, yet deeply-bonded family member
A deep earned tie (`band=family`), then a grave betrayal (magnitude 5): the structural band
stays `family` while the feeling goes negative — `attraction < 0` (wants to avoid) and
`affect_resentment > 0` (resents). Band and liking are independent.

### belief/affect dissociation (§A4) — cognitive vs affective ToM are separate slots
A benign observation drives `belief_disposition=trustworthy` while the affect slot carries
its own (independent) emotions — the two do not collapse to one like/dislike scalar.

## G-source-audit / discipline (all green)
- The seven decisions are RULES (`bond_belief_infer`, `bond_event_benefit`,
  `bond_event_betrayal`, `bond_gossip_update`, `bond_similarity_attraction`,
  `bond_proximity_familiarity`, `bond_band_assign`); the adapter invokes no Python rule
  engine (`graph_rewrite`/`gr.run`/`_match`/`_apply`/`make_rule`) and holds no if/else over
  a bond's graph valuation — conditionals are over world/config state only.
- **NO Rust:** `git diff b53bdacae0 -- runners/dsl` EMPTY. No committed `.so`
  (`_native.abi3.so` is git-ignored).
- **Additive only:** `seeds/bigville_bond_update.json`, `worlds/bigville_bond_world.py`,
  `tools/author_bigville_bond_seeds.py`, `tests/test_bigville_bond_migrated.py`, this
  prereg/results. NO tracked seed edited (all-new `bigville_bond_*`, seed `self_load_only`).
- `tests/test_failure_baseline_migrated.py` → **11 passed** (fail-set ⊆
  `results/failure_baseline.json`; ZERO new reds).

## Design deltas from the prereg (both from creator sharpenings, registered mid-task)
- The prereg had a structural kin/rival band. Sharpening 2 makes the band an **EARNED**
  pure-tie_strength ladder (family/intimate/friend/acquaintance/consequential_stranger/
  stranger); genetic relatedness is only a small prior. "rival" as a band is dropped —
  rivalry lives in the (independent) affect/attraction slots, satisfying sharpening 1's
  independence. Betrayal now ERODES tie_strength (`tie_erode` knob) so a tie decays with
  betrayal/neglect while a moderate betrayal leaves a deep tie's band intact (decoupling).

## Honest scope
Synthetic mechanism demo (focused 2–4 agent scenes, not a full town run) — mechanism-proven
≠ benchmark value. Rung 1 delivers the REPRESENTATION + update dynamics; the `romantic`
sub-value is carried as a slot but its courtship→pairing consumer is rung 3. Rung 2
(emergent speech) reads the relational-affect slot; rung 3 (attraction-driven
movement/pairing) reads the attraction slot — both shaped to be readable here.
