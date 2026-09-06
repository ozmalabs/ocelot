# FEEL-THEN-REASON two-stage analogical matcher — pre-registration (block 299000)

**Status: PRE-REGISTRATION. Committed BEFORE the confirmatory build/measure/test.**
The two seams below, the measurable speed metric, and the falsifiers are fixed
here in advance. The measured frontier table + power demo live in
`FEEL_THEN_REASON_RESULTS.md`; any deviation from the predictions here is reported
straight, not retrofitted.

> **HONEST NOTE ON WHAT THIS IS (read first).** This is a SYSTEM-1/SYSTEM-2
> decomposition of the *existing* analogy search, not a new model. Human
> analogical retrieval is famously two-stage: a cheap, similarity-driven "feel"
> that throws up a shortlist (MAC — many-are-called), then an expensive
> structural alignment over only the shortlisted set (FAC — few-are-chosen;
> Forbus/Gentner/Law's MAC/FAC). The substrate's `find_analogies` already HAS
> both halves latent in it — it just runs the expensive half over the WHOLE
> target set. This rung separates them so the cheap "feel" can prune the
> expensive "reason", and so a felt correspondence can be *ranked* even when the
> surface structure is thin. **Both seams are opt-in and default OFF, so the
> default path is byte-identical to today.**

## 0. Seed claim (verbatim, run at prereg time)

```
$ python3 scripts/seed_claim.py 299000 299999
SEED CLAIM 299000-299999: CLEAN -- no collision DETECTED.
  Scope: 1014 files with seed sinks; 749 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## 1. The cost structure this exploits (confirmed by reading the seams)

`find_analogies(source, targets)` → `observe(...)` writes **N** source
`AnalogyProbe`s and **M** target `ConceptShape` parts. Each part / probe is one
`concept_signature(...)` call, and `concept_signature` EDGE-ENUMERATES via
`_outgoing_relations` (walks `out_edges` / `neighbours` over every relational
edge type) — that edge walk is the expensive part of building the signature.

The `ap_decode` rule (`seeds/analogy_search.json`) is
`Argmax(FixedCount(AntiUnify(probe.sig, part.sig)))` gated by
`In(part.name, obs.scope)`. So the number of `AntiUnify` firings is
**~ Σ_probes |probe.scope|** — and today every probe's scope is the FULL target
part set, i.e. ~**N·M** firings (computed twice in the fixpoint).

The felt sub-signature is cheaply separable: `_dynamical_relations(sub, concept,
schema, overlay=False)` reads ONE node-attr per `field:`-sourced axis and
quantises through `_round_to_vocab` over `schema['field_axes']` — **no edge
walk**, and `_qualia_schema` is cached. This asymmetry (feel is cheap, the full
signature is expensive because of the edge walk) is the entire speedup basis:

* **Stage 1 (speed)** — if the cheap felt sub-signature prunes each probe's
  `scope` to `k << M` NEAREST-felt targets, `AntiUnify` firings drop from ~N·M
  to ~N·k, AND we skip building the edge-enumerating FULL signature for the
  pruned targets (fewer edge-enumerations).
* **Stage 2 (power)** — the felt coordinates are currently weighted FLAT:
  `_discriminative_struct` discards the dimension tag, and `_order_from_transform`
  pins the felt (`dynamical:` / `phenomenal:`) axes to order 2 alongside surface
  role matches. `_dimensions_in_transform(tkey)` PRESERVES the dimension tags —
  that is the read that lets a felt-shared correspondence be surfaced in the
  ranking even when its structural (surface) count is low.

## 2. The two seams (implemented EXACTLY as below; both OPT-IN, default OFF)

### STAGE 1 — felt-shortlist pruning (`felt_shortlist_k`)
* New param `felt_shortlist_k=None` on `find_analogies`, threaded to `observe`.
* In `observe`, where `probe_scope` is computed: when `felt_shortlist_k` is set,
  compute the CHEAP felt sub-signature (`_dynamical_relations(sub, concept,
  schema, overlay=...)`, optionally including overlay axes; NEVER the full
  `concept_signature`) for the source concept and each target part, and set
  `probe_scope` = the **k** parts with the NEAREST felt sub-signature.
* **Felt-distance** = number of NON-shared felt coordinates =
  `len(felt_src ^ felt_part)` (size of the symmetric difference of the two felt
  frozensets). Ties broken deterministically by part name.
* `ap_decode`'s existing `In(part.name, obs.scope)` then prunes the `Argmax` —
  **NO seed / rule change.**
* `felt_shortlist_k=None` ⇒ `probe_scope` stays the FULL set ⇒ byte-identical.

### STAGE 2 — felt-biased ranking (`felt_bias`)
* New param `felt_bias=False` on `find_analogies`.
* In results assembly, compute `felt_shared` = count of shared dims in
  `_dimensions_in_transform(tkey)` whose name starts with `dynamical:` or
  `phenomenal:`.
* When `felt_bias=True`, sort with a felt-aware key that adds a `-felt_shared`
  tier AHEAD OF `feature_count` in `analogical_thinking.RANK_KEY` (a RANK_KEY
  variant `RANK_KEY_FELT` taking `felt_shared`).
* When `felt_bias=False`, use `at.RANK_KEY` EXACTLY as today.
* `_discriminative_struct`'s FLAT count (which gates `min_score`) is UNCHANGED —
  only the RANKING changes when `felt_bias` is on. The min_score floor is
  identical to today either way.

### INSTRUMENTATION — the speedup made countable
* An opt-in, module-level counter records, per `find_analogies` call:
  * `antiunify_firings` = Σ_probes `len(probe_scope)` (the `ap_decode` candidate
    count = the firing count), and
  * `edge_enumerations` = number of FULL `concept_signature` builds (target
    parts + probes actually signed).
* Reset per call, read via a module accessor. This makes N·M vs N·k a MEASURED
  number, not an asserted one.

## 3. Predictions (failable)

* **P1 (default == today).** With `felt_shortlist_k=None` and `felt_bias=False`,
  `find_analogies` returns the SAME analogies in the SAME order as a k=None
  baseline across the listed migrated tests, and the `_native.abi3.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`.
* **P2 (speed).** For a real target battery with M candidates, some `k < M`
  yields a strictly SMALLER `antiunify_firings` proxy than `k=None` WHILE the top
  structural analogy found at `k=None` is still returned (recall retained). We
  report the frontier: the smallest `k` at which quality is retained.
* **P3 (power).** There is a real cross-domain pair sharing a felt shape (matching
  `phenomenal:sharpness` or `dynamical:valence`/`commitment`) but different surface
  structure, that `felt_bias=False` ranks BELOW other matches / below `min_score`
  (a GENUINE miss — verified by running `felt_bias=False` first and showing it is
  not in the top results), and `felt_bias=True` surfaces it into the top.
* **P4 (anti-faking).** Perturbing a concept's `sharpness`/`valence` source attr
  CHANGES both the felt shortlist AND the felt rank — the felt prior is DERIVED
  from the real `_dynamical_relations` signature, not a hand-set score.

## 4. Falsifiers (any ⇒ the rung is broken / not a win; report straight)

* **(i)** Default (both off) is NOT byte-identical to today ⇒ the seam leaked ⇒
  BROKEN. Fix or retract.
* **(ii)** Felt-first is faster but WORSE — it prunes a TRUE structural match at
  some `k < M` that k=None found ⇒ this is a speed/quality TRADEOFF, not a Pareto
  win. Report the honest frontier (the k threshold above which quality is
  retained), do not claim a free lunch.
* **(iii)** The power gain is HAND-PICKED — the "surfaced" analogy was not
  actually a below-threshold / below-other-matches structural miss under
  `felt_bias=False` ⇒ FAKED. The demo must show the miss first.

## 5. Anti-faking commitments

* The felt prior is the REAL `_dynamical_relations` signature (the same
  `field:`-sourced quantised coordinates — bouba/kiki `phenomenal:sharpness`,
  CAN `dynamical:valence`/`commitment` — that `concept_signature` already emits),
  NOT a tuned similarity score invented for this rung.
* Felt-distance is a pure set operation (symmetric-difference size) over those
  coordinates — no weights, no learned parameters.
* No new Rust, no `.so` change (md5 fixed at `7efe75eba05b006cafd15dbb4b7da246`),
  no `graph_rewrite.run` / `_match` / `_apply` / `make_rule`, no CAN cognition
  internals (`runners/dsl/src/*.rs`), no toolbox solver, no frozen-seed edit, and
  **no rule change to `seeds/analogy_search.json`** (the `In(part.name, scope)`
  gate already does the pruning). Python-only edits to
  `domains/analogy_search.py` + a RANK_KEY variant in
  `domains/analogical_thinking.py`.

## 6. Verdict shape (to be filled in RESULTS)

The RESULTS doc reports the firing-vs-quality frontier table + the power demo and
states plainly whether feel-then-reason is a **PARETO WIN** (fewer firings,
same-or-better top quality, AND new felt analogies surfaced) or a
**SPEED/QUALITY TRADEOFF** (honest frontier: quality retained only for
`k ≥ threshold`), and whether the power analogy was a genuine structural-flat
below-threshold miss. Honest either way.
