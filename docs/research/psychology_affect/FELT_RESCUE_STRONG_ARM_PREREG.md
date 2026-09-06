# FELT-RESCUE strong arm of feel-then-reason — pre-registration (block 300000)

**Status: PRE-REGISTRATION. Committed BEFORE the confirmatory build/measure/test.**
The seam, the grounded predicate, the precision-preservation test, and the
falsifiers are fixed here in advance. The measured 3-run precision-at-recall
table + the verdict live in `FELT_RESCUE_STRONG_ARM_RESULTS.md`; any deviation
from the predictions here is reported straight, not retrofitted.

> **HONEST NOTE ON WHAT THIS IS (read first).** Feel-then-reason (block 299000)
> shipped two *weak* arms: stage 1 (`felt_shortlist_k`) only SHORTLISTED the
> decode scope (a speed prune) and stage 2 (`felt_bias`) only RE-RANKED matches
> that were *already accepted* (a permutation). Neither changed WHICH analogies
> pass the `min_score` gate — the accepted SET was byte-identical either way.
> This rung builds the **STRONG arm**: a SELECTIVE felt-RESCUE that *changes the
> accepted set* by admitting a candidate whose structural match falls BELOW
> `min_score` — but IFF its shared felt shape is felt-COHERENT and RARE-by-chance.
> That is strictly stronger than stages 1/2: it recovers genuine structural
> MISSES, it does not merely reorder or prune. **The seam is opt-in and default
> OFF, so the default path is byte-identical to today.**

## 0. Seed claim (verbatim, run at prereg time)

```
$ python3 scripts/seed_claim.py 300000 300999
SEED CLAIM 300000-300999: CLEAN -- no collision DETECTED.
  Scope: 1014 files with seed sinks; 749 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## 1. The strong-arm claim

`find_analogies` gates an emitted analogy on DISCRIMINATIVE shared structure:
`disc = _discriminative_struct(tkey); if disc < eff_min_score: continue`
(domains/analogy_search.py, the read-back loop). A cross-domain pair whose felt
shapes agree on a RARE-by-chance axis but whose *surface* structural count sits
below `min_score` is DROPPED today — a genuine felt-coherent miss.

The strong arm gives such a candidate a SECOND CHANCE: under an opt-in
`felt_rescue` flag, a below-`min_score` candidate is ADMITTED (tagged
`felt_rescued=True`) IFF its shared felt shape passes the grounded rarity
predicate below; otherwise the `continue` fires exactly as today. This CHANGES
THE ACCEPTED SET — it recovers structural misses — which stages 1/2 never did.

## 2. The MEASURED rarity (Task 1 findings — grounded, not assumed)

Task 1 measured, on the real relaxed regard/hate-path corpus, the by-chance
rate at which two concepts SHARE a felt coordinate:

| shared felt coordinate           | by-chance rate | verdict                              |
|----------------------------------|---------------:|--------------------------------------|
| `dynamical:valence` SIGN         |          0.488 | coin flip — WEAK, floods junk        |
| `phenomenal:sharpness` POLE      |          0.012 | ~40× rarer — a real signal           |
| `felt_shared >= 2` (two+ axes)   |          0.009 | rare — coincidence of two is unlikely |

Two grounded facts drive this:

* **Valence is a coin flip.** A shared valence SIGN happens ~49% of the time by
  chance — barely better than a coin. A rescue that keys on valence would flood
  the accepted set with junk. **A lone shared valence sign NEVER rescues.**
* **Sharpness rarity is POPULATEDNESS × agreement.** Only crossmodal concepts
  carry a `phenomenal:sharpness` coordinate at all (the bouba/kiki axis; most
  concepts are dark on it), and then the two poles must AGREE. That product is
  ~0.012 — ~40× rarer than valence.
* **`commitment` is DARK in practice.** Under real relaxation, `identity_field`
  stays 0.0 on the regard/hate-path concepts, so `dynamical:commitment` gives
  `k=None` (no coordinate). We do NOT lean on commitment's nominal 9 levels — it
  is dark, so it simply does not contribute a shared coordinate in practice. The
  predicate treats it uniformly with any other non-valence felt axis (it would
  qualify as a "rare felt coord" *when populated*, but in practice it is not).

## 3. THE FELT-COHERENCE PREDICATE (grounded on the measured rarity)

Admit a below-`min_score` candidate IFF its shared felt shape is
**RARE-BY-CHANCE**:

> **(a shared `phenomenal:sharpness` pole) OR (`felt_shared >= 2`).**
> A lone shared `dynamical:valence` sign NEVER rescues.

Generalised cleanly (no hard-coded axis whitelist beyond the valence exclusion):
a **"rare felt coord"** = any shared felt coordinate on an axis OTHER than
`dynamical:valence`, OR `felt_shared >= 2`. So a shared sharpness pole, a shared
*populated* commitment/trait step, or two-or-more shared felt coords all
qualify; bare valence alone does not. Concretely:

```
felt_axes  = {dim of each shared 3-tuple in tkey whose dim starts
              "dynamical:" or "phenomenal:" and whose value is discriminative}
rare_felt  = {a in felt_axes if a != "dynamical:valence"}
felt_shared = len(felt_axes)
RESCUE  <=>  (len(rare_felt) >= 1) or (felt_shared >= 2)
        # equivalently: NOT (felt_axes == {"dynamical:valence"}) and felt_axes non-empty,
        # OR felt_shared >= 2 — a lone valence is the ONLY felt shape rejected.
```

This keys on MEASURED rarity (valence 0.488 vs sharpness-pole 0.012 vs
felt≥2 0.009), NOT a tuned constant. `felt_shared` and the shared felt axes are
read from `tkey` via `_dimensions_in_transform` — the SAME dimension tags the
existing `felt_shared` result field already uses. Because `AntiUnify` over two
signature frozensets is a WHOLE-TUPLE set intersection, a felt coordinate
survives into `tkey` only when both concepts carry the IDENTICAL
`(dim, "field", k)` tuple (same axis AND same pole k), so "shared sharpness
pole" is exactly "`phenomenal:sharpness` ∈ felt_axes" — no re-read needed. A
value-aware re-read of the two concept nodes (`_dynamical_relations`) is
available as a cross-check but is not required for the predicate.

## 4. The seam (default-OFF; byte-identical when off)

* New param `felt_rescue=False` on `analogy_search.find_analogies`, threaded
  through the delegating `analogical_thinking.find_analogies` entry.
* Emission (`ap_emit`) fires on aligned / `struct_shared > 0`, NOT on
  `min_score`, so below-`min_score` `Analogy` nodes ARE emitted and inspectable
  in the read-back loop — the rescue needs no seed/rule change.
* At the below-`min_score` `continue` (the `if disc < eff_min_score:` guard in
  the read-back loop): under `felt_rescue`, compute `felt_shared` + the shared
  felt AXES + whether any is non-valence from `tkey`, apply the predicate, and
  ADMIT the candidate (tagging `felt_rescued=True`) IFF the predicate holds;
  else `continue` exactly as today.
* `_discriminative_struct` (the flat count / today's gate) is UNCHANGED — the
  rescue is a SECOND-CHANCE branch added only under the flag.
* `felt_rescue=False` (default) ⇒ the branch is never taken ⇒ byte-identical
  `continue` ⇒ **default == today**. Non-rescued results carry
  `felt_rescued=False`.

## 5. Predictions (failable)

* **P1 (default == today).** With `felt_rescue=False` (and `felt_shortlist_k=None`,
  `felt_bias=False`), `find_analogies` returns the SAME analogies in the SAME
  order as today across the listed migrated tests, and `_native.abi3.so` md5
  stays `7efe75eba05b006cafd15dbb4b7da246`.
* **P2 (strong arm).** There is a real cross-domain pair sharing a RARE felt
  shape (a sharpness pole, or `felt_shared >= 2`) whose surface structural count
  sits below `min_score = k`, so it is ABSENT from the accepted set at the
  `min_score = k` baseline (a GENUINE miss — verified by running the baseline
  first and showing it is absent). With `felt_rescue=True` at `min_score = k` it
  is PRESENT and tagged `felt_rescued=True` (a real accepted-set change).
* **P3 (precision preservation — the CORE test).** On ONE labelled battery of
  below-threshold candidates (TRUE = pairs sharing a rare felt shape; SPURIOUS =
  pairs sharing ONLY a bare valence sign, or nothing felt), run THREE times:
  (i) `min_score = k` baseline, (ii) `min_score = k-1` blanket loosen, (iii)
  `min_score = k` + `felt_rescue`. The strong arm HOLDS IFF run (iii) recovers
  the TRUE felt pairs at recall ≈ run (ii) (recovers the felt misses) WHILE its
  precision ≫ run (ii) (it REJECTS the spurious valence-coincidence pairs that
  blanket-loosening admits). Selective, not threshold-loosening.
* **P4 (rarity keying).** A pair sharing ONLY a valence sign is NOT rescued; a
  pair sharing a sharpness pole OR `felt_shared >= 2` IS — proving the predicate
  keys on rarity, not on bare felt PRESENCE.
* **P5 (anti-faking).** Perturbing the rescued pair's felt SOURCE attr (flip
  `sharpness`, or zero the second felt coord) and re-relaxing REMOVES the rescue
  — the felt prior is DERIVED from the real `_dynamical_relations` signature, not
  hand-set.

## 6. Falsifiers (any ⇒ the strong arm is broken / not selective; report straight)

* **(i)** Default (`felt_rescue=False`) is NOT byte-identical to today ⇒ the seam
  leaked ⇒ BROKEN. Fix or retract.
* **(ii)** Rescue admits SPURIOUS junk at ~the SAME rate as the blanket
  `min_score-1` drop ⇒ it IS threshold-loosening, not selective ⇒ report a
  **FAILED strong arm** honestly (precision not preserved).
* **(iii)** The rescued analogy was HAND-CONSTRUCTED to sit just under the line,
  or the felt coord was HAND-SET rather than produced by relaxation ⇒ FAKED. The
  TRUE pairs must be genuine below-`min_score` misses, verified absent at the
  baseline; the felt coords must be produced by the real extractor/relaxation.

## 7. Anti-faking commitments

* The felt prior is the REAL `_dynamical_relations` signature (the same
  `field:`-sourced quantised coordinates — bouba/kiki `phenomenal:sharpness`,
  CAN `dynamical:valence`/`commitment` — that `concept_signature` already emits),
  NOT a tuned similarity score invented for this rung.
* The predicate keys on MEASURED rarity (valence 0.488 vs sharpness-pole 0.012
  vs felt≥2 0.009), expressed as a pure set predicate over the shared felt axes
  — no weights, no learned parameters, no tuned threshold constant.
* No new Rust, no `.so` change (md5 fixed at `7efe75eba05b006cafd15dbb4b7da246`),
  no `graph_rewrite.run` / `_match` / `_apply` / `make_rule`, no CAN cognition
  internals (`runners/dsl/src/*.rs`), no toolbox solver, no frozen-seed edit, and
  **no rule change to `seeds/analogy_search.json`** (`ap_emit` already emits the
  below-`min_score` node; the rescue is a Python read-back branch). Python-only
  edits to `domains/analogy_search.py` + threading through
  `domains/analogical_thinking.py`.

## 8. Verdict shape (to be filled in RESULTS)

The RESULTS doc reports the 3-run precision-at-recall table (recall on the TRUE
set + spurious-admitted count on the junk set, for baseline / blanket / rescue)
and states plainly whether the strong arm is **CONFIRMED** (rescue recovers the
TRUE felt misses at recall ≈ blanket AND precision ≫ blanket = selective) or
**FAILED** (rescue admits junk like a blanket drop = threshold-loosening).
Honest either way, and reports whether the TRUE pairs were genuine
below-`min_score` misses (verified absent at the baseline) rather than
constructed-to-fit.
