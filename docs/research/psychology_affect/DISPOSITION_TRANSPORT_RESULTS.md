# Disposition transport (affect-coupling Phase 1) — RESULTS

Registered design: `DISPOSITION_TRANSPORT_PREREG.md`. **All 6 predictions
confirmed.**

## 1. Live run (`scripts/disposition_transport_demo.py`)

```
=== Prediction 1: mood_bias diverges happiness via em_happiness ===
low mood_bias  happiness=0.2000 total_value=0.4000
high mood_bias happiness=1.8000 total_value=3.6000

=== Prediction 2: all 13 _PARAM_SPEC keys present ===
present on agent: 13/13 -> ['resolution_bins', 'arousal', 'prior_world_safe', 'prior_self_worth', 'charm_weight', 'hostile_weight', 'prior_others_trust', 'claim_weight', 'w_supergraph', 'w_spite', 'mood_bias', 'cred_on', 'valence']
coupler trait_* attrs: {'trait_hostile_weight': 0.42, 'trait_cred_on': 0.42, 'trait_valence': 0.42, 'trait_charm_weight': 0.42, 'trait_arousal': 0.42, 'trait_w_spite': 0.42}

=== Prediction 3: w_spite/cred_on/valence transport but are inert ===
baseline trait_valence=0.0000  varied trait_valence=0.9900
baseline happiness=1.0000  varied happiness=1.0000 (expect equal)

=== Prediction 4: generated ingroup_affinity reaches _speech_bond fallback ===
real warmth=0.0500  (old-default-would-have-been=0.1333)  match=True

=== Prediction 5: real social_disposition still wins over bucket familiarity ===
affect_affection=2.0000 (expect 2.0, the real disposition, not bucket-capped)

=== Prediction 6: generated backstory applies via the existing applier ===
TargetPattern count=6 targets=['Carl', 'class:unspecified', 'group:low', 'group:unspecified', 'role:unspecified', 'workplace_kind:unspecified']
```

## 2. Predictions

1. **`mood_bias` diverges happiness via the already-existing rule** —
   `PASS`. `happiness` moved `0.20 → 1.80` and `total_value` `0.40 → 3.60`
   between `mood_bias=-0.8` and `mood_bias=+0.8`, with ZERO new rule code
   — `em_happiness`/`em_fulfilment_value` were already reading it, they
   were just never fed a resident whose `mood_bias` differed from
   `_can_params`'s own 0.0 default before this phase transported real
   drawn values through.
2. **All 13 keys present** — `PASS`, enumerated by name (13/13 on the
   agent; the 6 non-additive/non-CAN traits also confirmed on the
   `AffectCoupler`, `mood_bias`/`valence` land as `mood_bias`/
   `trait_valence` per the design's additive-channel naming).
3. **`w_spite`/`cred_on`/`valence` transport but are inert** — `PASS`.
   `trait_valence` differs (`0.0` vs `0.99`, confirming transport), but
   `happiness` is IDENTICAL (`1.0000` both) — confirming no rule reads
   it yet, exactly the deliberate null this phase predicted.
4. **Generated `ingroup_affinity` reaches `_speech_bond`'s fallback** —
   `PASS`. Real warmth `0.0500` (from the generated `0.15`) vs. what the
   OLD hardcoded-`0.4`-default path would have produced (`0.1333`) —
   genuinely different, confirming the copy-through wiring works and
   isn't masked by `FAMILIARITY_CAP` at this magnitude.
5. **Real disposition still wins outright** — `PASS`. `affect_affection
   == 2.0000` exactly (the seeded `regard=2.0`/`admiration=2.0`), NOT
   diluted or averaged with the `shared_bucket_count=3` familiarity
   signal that was also present — the existing mutually-exclusive branch
   structure in `_speech_bond` held.
6. **Generated backstory applies via the reused applier** — `PASS`. 6
   `TargetPattern` nodes exactly as predicted (1 person — `Carl` — + 4
   own buckets + 1 out-group bucket). Honest incidental finding: with no
   `identity` dims supplied, 3 of the 4 own buckets defaulted to
   `"unspecified"` (the guard added in this phase) while `group` still
   resolved to a real value — because `_outgroup_bucket`'s own logic
   (`domains/bigville_disposition_apply.py`) treats an unrecognized tier
   via its deterministic name-hash fallback rather than passing through
   `"unspecified"` — a pre-existing, correct mechanical behavior, not a
   defect introduced here.

## 3. Honesty notes

**Does establish**: real transport of all 13 `_PARAM_SPEC` traits into a
`BigvilleOcelotResident`, with the one already-wired consumer
(`mood_bias`) immediately showing real behavioral divergence and the
other three previously-orphaned traits (`w_spite`, `cred_on`, `valence`)
landing without side effects — confirming this phase is genuinely
separable from Phase 2's consumption work, not accidentally coupling
early. Confirms `boot_core.CORE_SEEDS` includes `affective_state_core`
for every resident (the `AffectCoupler`'s `reads_affect` edge target
always exists). Closes the actual gap named in
`BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md`'s own out-of-scope list: a
generated backstory now reaches a live `BigvilleOcelotResident` through
one call, reusing `bigville_disposition_apply.py` rather than
duplicating its logic.

**Does NOT establish**: any new coupling behavior — `coupling_on` stays
`0.0`, `reactivity_gain`/`hostile_gain`/`warmth_gain` stay at their
neutral `1.0` forever in this phase (Phase 2). Does NOT touch
`decide_speech`'s existing arousal max-blend (Phase 3). Does NOT tag any
`SpeechOption`/target-scoped Concept with `affinity_*` attrs (Phase 2/4).
Does NOT run on a live `populate_town100` cast (Phase 5) — only
hand-constructed personality dicts were exercised here.

## 4. Files

- `docs/research/psychology_affect/DISPOSITION_TRANSPORT_PREREG.md`
- `docs/research/psychology_affect/DISPOSITION_TRANSPORT_RESULTS.md` (this file)
- `worlds/bigville_ocelot_adapter.py` (edited: `_can_params` +cred_on/valence,
  new `_disposition_traits`/`_ensure_affect_coupler`/`_apply_generated_dispositions`)
- `tests/test_disposition_transport.py` (new, 6/6)
- `scripts/disposition_transport_demo.py` (new)
