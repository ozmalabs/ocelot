# w_supergraph magnitude fix — RESULTS

Registered design: `SUPERGRAPH_WEIGHT_MAGNITUDE_PREREG.md`. **All 6
predictions confirmed.**

## 1. Live measurements

```
B (derived, live, no literal) = 10

$ python3 -m pytest tests/test_core_emotions_migrated.py -q
15 passed   (includes the widened integer_values_audit sweeping
             w in {0,0.1,0.25,0.4785,0.5,0.75,0.9114,1.0,2.0,250.0} x
             contribution in {0,-3,3,60,-60,300,-800,987} -- 0 non-integer
             cells found, confirming Times(Int,Int)'s closure at the
             VALUE level, not just the AST-name level)

# Prediction 4 -- graded, monotone fulfilment at a fixed real contribution
w=0.00 -> fulfilment_value=0.0    hit_fulfilment=0.0  arousal=50.0  (unfired,
                                                                     unchanged endpoint)
w=0.10 -> fulfilment_value=29.0   hit_fulfilment=1.0  arousal=29.0
w=0.25 -> fulfilment_value=75.0   hit_fulfilment=1.0  arousal=75.0
w=0.50 -> fulfilment_value=150.0  hit_fulfilment=1.0  arousal=150.0
w=0.75 -> fulfilment_value=225.0  hit_fulfilment=1.0  arousal=225.0
w=0.90 -> fulfilment_value=270.0  hit_fulfilment=1.0  arousal=270.0
w=1.00 -> fulfilment_value=300.0  hit_fulfilment=1.0  arousal=300.0  (unchanged
                                                                       endpoint,
                                                                       exact)
distinct: 7/7   monotone: True

# Prediction 5 -- the real flagship scenario (bigville, monopoly_four_players)
participants: ['Alice', 'Bob', 'Cara', 'Dan']
before (each participant's own reach): {'Alice': 1, 'Bob': 1, 'Cara': 1, 'Dan': 1}

  Alice opens the game box IN PLACE (shared, never moved to self):
  after: {'Alice': 330, 'Bob': 330, 'Cara': 330, 'Dan': 330}
  supergraph_contribution (others only) = 987
  collective_success (all)              = 1320

  Alice moves the box to herself FIRST, then opens it (hoarding):
  after: {'Alice': 330, 'Bob': 0, 'Cara': 0, 'Dan': 0}
  supergraph_contribution (others only) = -3

# The population payoff -- a real 100-resident w_supergraph draw
# (bigville's own declared generator: mean=0.5, sd=0.2, clip=[0,1],
# default_rng(305000)), evaluated at BOTH real flagship contribution values
w: min=0.0207 max=0.9899 mean=0.5038 sd=0.1919 zero-draws=0/100

contribution=987 (sharing):  93 distinct fulfilment_values / 100
                              range 20.0 .. 977.0
contribution=-3  (hoarding): 3 distinct fulfilment_values / 100
                              range -3.0 .. -1.0

$ python3 -m pytest tests/test_harvest_commons_migrated.py tests/test_spite_skill_migrated.py \
    tests/test_spite_to_succeed_migrated.py tests/test_glassbox_r1_migrated.py \
    tests/test_langsim_migrated.py tests/test_langsim_syntax_migrated.py \
    tests/test_marshmallow_migrated.py tests/test_abusive_r4_migrated.py \
    tests/test_abusive_u0_migrated.py tests/test_abusive_r5_migrated.py \
    tests/test_abusive_r6_migrated.py tests/test_abusive_r7_migrated.py \
    tests/test_abusive_n4_migrated.py tests/test_modulator_emergence_migrated.py \
    tests/test_emotion_phenotype_migrated.py tests/test_affect_coupling.py \
    tests/test_target_scoped_coupling.py tests/test_disposition_transport.py \
    tests/test_bigville_ocelot_adapter.py -q
4 pre-existing failures (stale .so md5 pins, unrelated -- see sec3),
all else green, ZERO test edits beyond the one source_audit fix (sec3)

$ (cd /home/matt/ozmadev/bigville && python3 -m pytest tests/ -q)
211 passed
```

## 2. Predictions

1. **`Times(Int,Int)` value-closure** — `PASS`. Zero non-integer cells found
   across every live caller's real `w`/contribution range, checked directly
   inside `integer_values_audit` (not inferred from the AST-name change
   alone).
2. **Byte-identity across every non-bigville consumer** — `PASS`. All 13
   consumer test files pass with zero test edits (one measurement-script
   fix — `source_audit`'s `fulfilment_reads_supergraph` check, sec3 — is not
   a consumer test and does not touch behavior).
3. **G1 plateau stays green, unedited** — `PASS`. `W_MAG_PROBE ⊂ [1,∞)` is
   entirely above the attenuation clamp; `test_emotion_phenotype_migrated.py`
   required zero edits.
4. **Genuine magnitude sensitivity** — `PASS`, exceeded: 7 distinct values
   registered, 7 measured, strictly monotone, both endpoints (`w=0`→`0`,
   `w=1`→`300` exact) byte-identical to the old sign gate.
5. **Real flagship scenario, both directions** — `PASS`. Sharing
   (open-in-place) publishes `+987` to the other 3 participants; hoarding
   (move-to-self-then-open) publishes `-3` — both real, measured, not
   asserted in advance to a specific number in the PREREG (the PREREG
   deliberately registered only the SIGN prediction, not the magnitude, to
   avoid backfitting).
6. **No hand-picked constants** — `PASS`. `grep` for a literal `10`/`1024`
   SCALE anywhere in the touched Python files: none — `B` is read live from
   `derive_scale_bits()` everywhere it's used.

## 3. A real, pre-existing test defect found and fixed en route

`scripts/core_emotions_measure.py::source_audit`'s `fulfilment_reads_supergraph`
check was a literal substring match on `em_fulfilment`'s `where` clause for
the string `"supergraph_contribution"` — it broke the moment that read moved
one hop out into the new `em_weighted_contribution` rule, even though the
supergraph frame is still reached, just through a named intermediate instead
of inline. Fixed to check the dependency one hop out (`em_fulfilment` reads
`weighted_contribution`, AND `em_weighted_contribution`'s own effects read
both `supergraph_contribution` and `w_supergraph_q`) — this is a genuine,
reportable finding (a test asserting *how* a value is computed rather than
*that* the right upstream signal is reached), not a tolerance loosened to
make a regression disappear.

## 4. Honesty notes

**Does establish**: `w_supergraph`'s magnitude now genuinely, monotonically
shapes `fulfilment_value` (and therefore `hit_fulfilment`/`hit_pride`'s
firing threshold and `arousal`'s intensity) for every consumer whose `w`
lands in `(0,1)` — today, that is bigville alone, and bigville's own
contribution signal was graded in the same change so the fix is
behaviorally real there, not merely reachable. Zero new Rust. Zero
hand-picked constants — `B` is derived live from real per-consumer data and
will change automatically if that data changes. Strengthened, not weakened,
the integer-native gate (`integer_values_audit` now covers real ranges it
previously didn't touch at all). Confirmed byte-identical for all 11
originally-identified consumers plus 2 more found during the sweep
(`abusive_r5/r6/r7/n4`), 15 consumer files total.

**Does NOT establish**: that `B`'s current value is calibrated to anything
external. Does NOT fix `ss_decision_value`'s own identical `w_spite` sign
gate (`seeds/spite_skill.json`) — named as a residual, not built here, because
every current consumer only ever draws `w_spite ∈ {0.0,1.0}`, but bigville's
own authored cast carries continuous `w_spite` values that will hit this
exact defect once spite reaches bigville. Does NOT run the full cast-100
`decide_speech` flip-sweep falsifier
(`LOG_WEIGHT_QUANTIZATION_RESULTS.md`'s harness, pass criterion inverted) —
the population-level `fulfilment_value` spread (93/100 distinct at the real
flagship contribution) is measured directly instead, which is upstream of
that harness and sufficient to confirm the mechanism is behaviorally live,
but the full speech-decision propagation was not independently re-verified
end-to-end in this pass; deferred, not silently skipped. Does NOT touch
`cred_on`'s naming collision (Phase B).

## 5. Files

**ocelot:**
- `docs/research/psychology_affect/SUPERGRAPH_WEIGHT_MAGNITUDE_{PREREG,RESULTS}.md` (new)
- `domains/core_emotions_weight.py` (new — shared quantizer)
- `scripts/build_core_emotions_seed.py` (edited: `em_weighted_contribution`
  rule; `em_fulfilment_value`/`em_fulfilment`/`em_pride`/`arousal_mux` reads)
- `seeds/core_emotions.json` (regenerated, 24 rules)
- `scripts/core_emotions_measure.py` (`integer_audit` denylist narrowed;
  `integer_values_audit` widened; `_hub` auto-derives `w_supergraph_q`/
  `w_scale_bits`; `source_audit`'s `fulfilment_reads_supergraph` fixed)
- `scripts/emotion_phenotype_measure.py` (`_hub` auto-derives)
- `domains/harvest_world.py`, `domains/harvest_spite_world.py`,
  `worlds/glassbox_r1_world.py`, `worlds/langsim_world.py`,
  `domains/marshmallow_world.py`, `domains/achieve_world.py`,
  `worlds/abusive_{r4,r5,r6,r7,n4,u0}_*.py` (each: one import, one
  `w_supergraph_q`/`w_scale_bits` derivation at the existing
  `HeldEmotionParams` construction site)
- `worlds/bigville_ocelot_adapter.py` (`_ensure_emotional_core` derives
  `w_supergraph_q`/`w_scale_bits`; `record_action_outcome` accepts optional
  graded `supergraph_contribution`/`collective_success`)
- `seeds/spite_skill.json`, `seeds/harvest_commons.json` (comment/description
  text updated to match the corrected formula; no functional change)
- `docs/research/vision/VISION_EMOTION_PHENOTYPE_RESULTS.md` (retracted in
  place — the "structural plateau" claim was formula-conditional)
- `docs/research/psychology_affect/EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md`
  (psychopathy note corrected — design doc was right, code was wrong)

**bigville:**
- `bigville/bigville/held_board_games.py` (`_room_tick` computes and
  publishes the real reach-delta as `supergraph_contribution`/
  `collective_success`)
