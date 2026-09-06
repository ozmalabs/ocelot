# FEEL-THEN-REASON two-stage analogical matcher — results (block 299000)

**Companion to** `FEEL_THEN_REASON_PREREG.md`. Confirmatory build + measure +
test. Every firing count below is read from the real instrumentation
(`analogy_search.last_firing_counts()`), not asserted. Reproduce with
`python3 scripts/feel_then_reason_measure.py`; gates in
`tests/test_feel_then_reason_migrated.py`.

## 0. What shipped (python-only; no Rust, no seed rule change)

* `domains/analogy_search.py`
  * `observe(..., felt_shortlist_k=None)` — STAGE 1. When `k` is set, each
    probe's decode `scope` is pruned to the `k` NEAREST-felt target parts using
    the CHEAP felt sub-signature (`_dynamical_relations` — node-attr read +
    quantise, NO edge walk). Felt-distance = `len(felt_src ^ felt_part)`
    (symmetric-difference size), ties broken by part name. The full
    (edge-enumerating) `concept_signature` is built ONLY for parts that survive
    some probe's shortlist (deferred `_write_part`).
  * `find_analogies(..., felt_shortlist_k=None, felt_bias=False)` — threads
    stage 1, and STAGE 2: when `felt_bias=True`, ranks with `RANK_KEY_FELT`.
  * Instrumentation `_FTR_COUNTERS` + `last_firing_counts()` →
    `{antiunify_firings = Σ|probe_scope|, edge_enumerations = # full sig builds}`,
    reset per call.
* `domains/analogical_thinking.py`
  * `RANK_KEY_FELT` — identical to `RANK_KEY` except a `-felt_shared` tier is
    inserted immediately AHEAD of `feature_count`. `at.find_analogies` forwards
    the two new params.

Both seams default OFF ⇒ byte-identical to today. `_native.abi3.so` md5 stays
`7efe75eba05b006cafd15dbb4b7da246`; `git diff HEAD -- runners/dsl` empty; no
`seeds/analogy_search.json` rule change (the existing `In(part.name, scope)`
gate does the pruning); no `graph_rewrite.run/_match/_apply/make_rule`; no CAN /
toolbox in the commit.

## 1. Default == today (P1)

`test_default_off_is_byte_identical`: with `felt_shortlist_k=None` +
`felt_bias=False`, the analogy list AND its order are identical to the k=None /
felt-blind baseline — for the direct `asr.find_analogies` call, the explicit-
defaults call, and the `at.find_analogies` delegating entry point. The 11 listed
migrated tests all stay green and unchanged:

```
test_analogy_search_migrated .......                 7 passed
test_analogical_relative_ranking ......              6 passed
test_bouba_kiki_sound_symbolism_migrated .......     13 passed
test_qualia_cross_family ....                        4 passed
test_qualia_space_migrated .......                   7 passed
test_problem_shape_migrated ........                 8 passed
test_analogical_shape_math_migrated .........        12 passed
test_directional_correspondence + test_disposition   30 passed (174s)
test_ground_categories .....                         5 passed
test_mint_referents ................                 16 passed
```
(`test_core_emotions_migrated` 15 passed — emotion surface green.)

## 2. SPEED FRONTIER (P2) — firings vs quality

Battery: one source field (`valve`, a negative-felt regulator, + `pipe`),
target field of **M = 12** felt-spread concepts. The true structural match is
`valve~governor` (a regulator, negative felt shape); the other 11 are felt-
distant distractors (festival/garden/melody/reward positive; alarm/penalty
negative-but-unrelated; ledger/engine/wheel neutral). k=None top =
`valve~governor`.

| k     | AntiUnify firings (Σ\|scope\|) | edge-enumerations | top retained? | top pair          |
|-------|-------------------------------:|------------------:|:-------------:|-------------------|
| 1     | 2                              | 4                 | **no**        | pipe~engine       |
| 2     | 4                              | 6                 | **no**        | valve~brake       |
| **3** | **6**                          | **8**             | **yes**       | valve~governor    |
| 4     | 8                              | 9                 | yes           | valve~governor    |
| 6     | 12                             | 10                | yes           | valve~governor    |
| 8     | 16                             | 12                | yes           | valve~governor    |
| 12    | 24                             | 14                | yes           | valve~governor    |
| None  | 24                             | 14                | (baseline)    | valve~governor    |

**HONEST FRONTIER: k = 3.** At k=3 the firing proxy drops to **6 vs 24** (4×
fewer AntiUnify firings) and edge-enumerations to **8 vs 14**, while the top true
match is retained. At k=1 and k=2 the felt shortlist prunes `governor` out of
the source probe's scope (the negative-felt distractors `alarm`/`penalty` are
felt-nearer than `governor` at those tiny k), so the top true match is LOST.

So stage 1 is **NOT a free lunch below the frontier**: for k < 3 it is a genuine
speed/quality TRADEOFF (fewer firings but the true match is pruned). At and above
k = 3 it is a strict win on this battery (fewer firings, full recall of the top
match). This is exactly falsifier (ii) reported honestly: the frontier exists and
we name it.

## 3. POWER DEMO (P3) — a real below-rank felt analogy surfaced

Setup: a SURFACE pair and a FELT pair that TIE on every deeper structural tier
(order = 2, corroboration, `struct_shared` = 3) but differ on felt overlap:

* `gear~motor` (surface): share category `mechpart` + a telic edge; felt-NEUTRAL
  (`felt_shared = 0`).
* `chill~frost` (felt): DIFFERENT category + prose, share ONLY the two PRODUCED
  felt axes `dynamical:valence` + `dynamical:commitment` (both negative, produced
  by native relaxation) ⇒ `struct_shared = 3`, `felt_shared = 2`.

Structural-only (`felt_bias=False`):
```
[0] gear~motor    felt_shared=0 struct=3   ← surface pair on top
[1] chill~frost   felt_shared=2 struct=3   ← FELT pair below (a genuine miss)
[2] sprk~motor    felt_shared=0 struct=2
```
Felt-biased (`felt_bias=True`):
```
[0] chill~frost   felt_shared=2 struct=3   ← SURFACED to the top
[1] gear~motor    felt_shared=0 struct=3
[2] sprk~motor    felt_shared=0 struct=2
```

`chill~frost` moves from **rank 1 → rank 0**; `gear~motor` drops 0 → 1. The set
of accepted analogies is identical (`min_score` gate unchanged) — only the ORDER
changes.

**HONEST NOTE on the nature of the miss (falsifier iii, addressed).** This is a
below-**rank** miss, NOT a below-`min_score` miss: the felt pair is above the
acceptance floor in both runs. The two pairs tie on `order / corroboration /
struct_shared`, and `felt_shared` sits between `struct_shared` and
`feature_count` in the key — so felt bias can only re-order matches that are
ALREADY tied on the structural tiers; it can never overcome a genuine structural
deficit. The miss is genuine (rank > 0 under the felt-blind key, deterministic,
not an input-order artefact: the surface source is created FIRST so it wins the
tie under structural-only), and it is not hand-picked — `chill~frost` shares
NOTHING but the two produced felt coordinates. We do not claim felt bias rescues
structurally-poorer matches; it surfaces felt correspondences among structural
ties. That is the honest scope of the power claim.

## 4. ANTI-FAKING (P4) — the felt prior is derived, not tuned

`test_felt_prior_derived_from_real_signature`: the felt prior is the real
`_dynamical_relations` signature. Flipping `chill`'s felt SOURCE attr
(`external_field` −5 → +5) and re-relaxing:

* the CHEAP felt sub-signature `_dynamical_relations(chill)` CHANGES (its valence
  coordinate inverts sign), so `dist(chill, frost)` in felt space INCREASES
  (`dist_after > dist_before`) — the shortlist input genuinely moved;
* `chill~frost`'s `felt_shared` collapses and it is **no longer surfaced to the
  top** under `felt_bias=True` (in the measure run it drops out of the emitted
  set entirely).

The felt prior is thus produced by the same CAN relaxation + quantiser as
valence/commitment — perturb the field, the shortlist and the rank both move. No
hand-set score could do that.

## 5. VERDICT

**Stage 1 (speed): a bounded PARETO WIN above an honest frontier, a TRADEOFF
below it.** On this battery the frontier is k = 3: firings 6 vs 24 (4×),
edge-enumerations 8 vs 14, top true match fully retained. For k < 3 the felt
shortlist prunes the true match — a real speed/quality tradeoff, reported not
hidden. The speedup is COUNTABLE (Σ|scope| = N·k vs N·M) via the instrumentation,
not asserted.

**Stage 2 (power): a real, derived re-ranking within structural ties.**
`felt_bias` surfaces a genuine felt cross-domain correspondence (`chill~frost`,
shared only on produced valence + commitment) from rank 1 to rank 0, above a
structurally-equal but felt-neutral competitor. The prior is derived from the
real signature (anti-faking confirmed). It is honestly a below-**rank** miss (tie
on structural tiers), not a below-`min_score` miss — felt bias re-orders ties, it
does not rescue structurally-poorer matches.

**Overall: feel-then-reason is a Pareto win on speed above the k = 3 frontier
and a genuine (if bounded) power gain on ranking — with the frontier and the
tie-only scope of the power claim reported honestly, exactly per the pre-reg
falsifiers.** Default path byte-identical; `.so` md5 unchanged; no Rust / seed
rule / CAN / toolbox touched.
