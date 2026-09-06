# FELT-RESCUE strong arm of feel-then-reason — results (block 300000)

**Confirmatory.** Run AFTER the pre-registration
(`FELT_RESCUE_STRONG_ARM_PREREG.md`). The seam, the grounded predicate, the
precision-preservation test, and the falsifiers were fixed in advance; this
doc reports the measured numbers and the verdict, honest either way.

Reproduce: `python3 scripts/felt_rescue_measure.py`
Gates: `python3 -m pytest tests/test_felt_rescue_migrated.py`

## 1. What was built

An opt-in, default-OFF `felt_rescue` seam on `analogy_search.find_analogies`
(threaded through the delegating `analogical_thinking.find_analogies`). At the
below-`min_score` `continue` in the read-back loop, a candidate whose
DISCRIMINATIVE structural count sits below the floor is given a SECOND CHANCE:
ADMITTED (tagged `felt_rescued=True`) IFF its shared felt shape is
RARE-by-chance per `_felt_rescue_ok` — a shared non-valence felt coord (e.g. a
`phenomenal:sharpness` pole) OR `felt_shared >= 2`; a lone shared
`dynamical:valence` sign never rescues. `_discriminative_struct` (today's gate)
is untouched. `felt_rescue=False` (default) ⇒ the branch is never taken ⇒
byte-identical `continue`.

This CHANGES THE ACCEPTED SET (recovers below-`min_score` structural misses) —
strictly stronger than block 299000's stage 1 (shortlist) and stage 2 (re-rank),
neither of which changed which analogies passed the gate.

## 2. Default == today (P1)

`felt_rescue=False` (with `felt_shortlist_k=None`, `felt_bias=False`) ⇒
`find_analogies` returns the SAME accepted set in the SAME order as today, and
every result carries `felt_rescued=False`. Verified byte-identical (same
accepted set + order) across:

```
test_feel_then_reason_migrated        test_qualia_space_migrated
test_analogy_search_migrated          test_problem_shape_migrated
test_analogical_relative_ranking      test_mint_referents
test_bouba_kiki_sound_symbolism_migrated  test_ground_categories
test_qualia_cross_family              test_disposition
```

`93 passed` for the felt_rescue + feel_then_reason + the ten regression files
together. `_native.abi3.so` md5 = `7efe75eba05b006cafd15dbb4b7da246` (unchanged).

## 3. The labelled below-threshold battery

One battery, run 1-vs-1 per pair (the analogy decode emits exactly ONE analogy
per source concept — the single Argmax-best target; so a 1-vs-1 field pins
emission of exactly the labelled pair and makes its felt shape unambiguous):

* **TRUE** (6 pairs) — cross-domain pairs sharing a RARE felt shape: a shared
  `phenomenal:sharpness` pole (by-chance 0.012), thin/distinct surface, so their
  DISCRIMINATIVE count is 1 (`is_a` never counts) — BELOW `min_score = k = 2`.
* **SPURIOUS** (6 pairs) — pairs sharing ONLY a bare `dynamical:valence` sign
  (by-chance 0.488, a coin flip). `identity_field = 0` keeps
  `dynamical:commitment` DARK (the Task-1 finding), so the ONLY shared felt coord
  is valence. Also disc = 1, below `k`.

**Genuine-miss verification (run FIRST):** all 6 TRUE pairs were confirmed
ABSENT from the accepted set at the `min_score = 2` baseline — genuine
below-`min_score` misses, NOT constructed to sit "just under the line" and NOT
hand-set: the felt coords are the REAL `_dynamical_relations` signature (valence
from the committed `state` field, sharpness from the bouba/kiki `sharpness`
source attr).

## 4. The 3-run precision-at-recall table (P3 — the core test)

`k = 2`. THREE runs on the SAME battery:

| run                              | recall_TRUE | spurious_admitted | precision_on_junk |
|----------------------------------|:-----------:|:-----------------:|:-----------------:|
| (i)   baseline  `min_score=2`    |   **0/6**   |       0/6         |       1.00        |
| (ii)  blanket   `min_score=1`    |   **6/6**   |     **6/6**       |     **0.00**      |
| (iii) rescue    `min_score=2`+R  |   **6/6**   |     **0/6**       |     **1.00**      |

Glass-box (rescue run): every TRUE pair admitted with `felt_shared=1`, shared
felt axis `sharpness`, `felt_rescued=True`; every SPURIOUS pair NOT admitted
(shared felt axis `valence` alone — rejected by the predicate).

Reading the table:

* The **baseline** (i) misses everything below `k` — 0/6 TRUE, 0/6 SPURIOUS.
* The **blanket** loosen (ii) recovers the TRUE misses (6/6) but at the cost of
  admitting ALL the junk (6/6 SPURIOUS, precision 0.00) — it is indiscriminate.
* The **rescue** (iii) recovers the TRUE misses at the SAME recall as blanket
  (6/6) while admitting NONE of the junk (0/6 SPURIOUS, precision 1.00).

## 5. Verdict

> **STRONG ARM CONFIRMED.**
>
> `felt_rescue` recovers the TRUE felt misses at recall EQUAL to the blanket
> `min_score-1` drop (6/6 = 6/6) WHILE rejecting the spurious valence-coincidence
> pairs the blanket drop admits — precision **1.00 ≫ 0.00**. The rescue is
> SELECTIVE, not threshold-loosening: it does not admit junk at anything like the
> blanket rate (0/6 vs 6/6). This is a genuine accepted-set change that recovers
> below-`min_score` structural misses, strictly stronger than stages 1/2.

Against the falsifiers:

* **(i) default byte-identical** — HOLDS (§2); the seam did not leak.
* **(ii) rescue admits junk like a blanket drop** — REFUTED: rescue admits 0/6
  spurious vs blanket's 6/6. Selective.
* **(iii) hand-constructed / hand-set** — REFUTED: the TRUE pairs were verified
  ABSENT at the baseline (genuine misses), and the felt coords are the real
  `_dynamical_relations` signature (perturbing the felt SOURCE attr removes the
  rescue — gate (e)), not a hand-set constant.

## 6. Rarity keying + anti-faking (P4, P5 — from the test suite)

* **Rarity (P4):** a pair sharing ONLY a valence sign is NOT rescued; a pair
  sharing a `phenomenal:sharpness` pole IS; a pair sharing TWO felt axes
  (valence + sharpness, `felt_shared >= 2`) IS. The predicate keys on the
  MEASURED rarity, not on bare felt presence — a lone valence (the coin flip) is
  the only felt shape rejected.
* **Anti-faking (P5):** perturbing the rescued pair's felt SOURCE attr removes
  the rescue — flipping the sharpness pole makes the two poles disagree so no
  shared felt coord survives the frozenset intersection (no rescue); zeroing the
  second felt coord on a two-felt pair drops `felt_shared` to 1 (a lone valence)
  which the rarity predicate rejects (no rescue). The felt prior is DERIVED from
  the real signature.

## 7. Honesty notes

* The TRUE pairs were **genuine below-`min_score` misses**, verified absent at
  the `min_score = k` baseline before any rescue was applied — not constructed
  to sit just under the line.
* The felt coords are the **real produced signature** — valence from the
  committed `state` field the `dynamical:valence` axis reads, sharpness from the
  bouba/kiki `sharpness` source attr the `phenomenal:sharpness` axis reads — not
  hand-set transform coordinates. `dynamical:commitment` was left DARK
  (`identity_field = 0`), matching the Task-1 finding that commitment stays 0.0
  under real relaxation on the regard/hate-path corpus.
* The predicate keys on the **measured rarity** (valence 0.488 vs sharpness-pole
  0.012 vs felt≥2 0.009), expressed as a pure set predicate over the shared felt
  axes — no tuned threshold constant.

## 8. No-change confirmation

* `_native.abi3.so` md5 = `7efe75eba05b006cafd15dbb4b7da246` (unchanged).
* `git diff HEAD -- runners/dsl` empty (no CAN internals touched).
* No rule change to `seeds/analogy_search.json` (`ap_emit` already emits the
  below-`min_score` node; the rescue is a Python read-back branch).
* No `graph_rewrite.run` / `_match` / `_apply` / `make_rule`; no toolbox solver;
  no frozen-seed edit. Python-only edits to `domains/analogy_search.py` +
  threading through `domains/analogical_thinking.py`.
