# Seed-pick structural fallback — pre-registration

Companion to `RULE_SIGNATURE_SLICE_PREREG.md` / `RULE_SIGNATURE_SLICE_RESULTS.md`
and `RULE_SIGNATURE_PRODUCTION_WIRING_PREREG.md` / `..._RESULTS.md` (read first
— they built and wired the `where`-signature fallback for A1/A2, the two
Python-function `keywords_text` sites). This rung is the charter that RESULTS
doc names for A3 and explicitly does NOT build: *"define
`seed_signature(seed_manifest) -> frozenset[(rule_name, *rule_signature_row)]`,
mint it alongside `SeedSummary` the same additive-attr way
`where_signature_json` was minted onto `RuleSummary`, and build a
hand-constructed Class-A/B-style oracle over a SAMPLE of the 661-seed
population before trusting it in the live `_compose_experiment_rule` seed-skip
pick."* Per this folder's own house discipline and CLAUDE.md's "RUN 15
CORRECTION": power the gate before the endgame, registered here before the
production edit.

**Worktree:** `/home/matt/ocelot-seed-signature`, branch
`seed-pick-structural-fallback`, detached from `main` at `6314ebe` (verified:
`git log --oneline -1 main` → `6314ebe Merge gamma-production-adopt-handler:
judge/adopt split, GO`). Engine unchanged — this rung adds no Rust:
`runners/dsl/python/substrate_rs/_native.abi3.so` sha256
`23ba3f1dbe20459c340440978d379c09d83eba7109b489a56a754ebd9b92a7af`.

---

## 0. The site, restated precisely (SHAPE_AUDIT.md §2.1, A3)

`reflective_faculty.py:4331-4344` (`_compose_experiment_rule`'s `vary`
branch) — the agent decides which of its own loaded seeds to ablate in a live
self-experiment by an `Argmax` over `SeedSummary` nodes, scored by
`StringIndexOf`-`Sum` overlap between a `CapabilityAxis`'s
`residual_predicates` words and `SeedSummary.keywords_text` (id words + every
declared rule's NAME split on `_` + `RelationCue` keywords + concept names +
first ~40 description words — `substrate/boot_all.py::_seed_keywords_text`).
This is a bag of identifiers, not what the seed's rules structurally *do*.

**Two properties make this site structurally different from A1/A2, both
already named by the prior rung and confirmed again here, not assumed:**

1. `rule_signature`/`where_signature` flatten ONE rule's `where` clause. A
   `SeedSummary` has no `where` clause — a seed is a *manifest* declaring
   MANY rules (0–128 in the real corpus, see §1 below). There is no existing
   per-seed structural object to read; one must be DEFINED.
2. The pick is not a plain Python function evaluated once
   (`_pick_acting_rule`/`_pick_reply_rule`'s own shape) — it is a Term
   embedded via `{"__term__": ...}` into a `SeedDelta`'s `add_node` EFFECT,
   inside a "mint" rule the composer builds and installs LIVE with
   `add_rule`. The Term is evaluated by the engine's own `run_rules()`
   fixpoint whenever that installed rule's `where` matches — not once,
   synchronously, by the composing Python function.

---

## 1. Investigation findings — read before any bar was set

### 1.1 The candidate population, counted before the bar (not asserted)

`scripts/seed_signature_discover_probes.py` (read-only, this rung's own
discovery tool, precedent: `RULE_SIGNATURE_SLICE_PREREG.md` §0.2's structural
population count, `scratch_investigate/discover_probes2.py`'s discovery
method for A1/A2):

- **897 seed manifest files** on disk (`seeds/*.json`), of which 639 declare
  at least one rule.
- **4127 total rule declarations** across all seed manifests — the true
  candidate structural surface, NOT the ~2200-row subset that happens to have
  won a `RuleSummary` mirror (only rules writing `chosen_action`/`reply`/a
  where-literal are mirrored; the great majority of the corpus's rules write
  neither). Largest single seed: `humanoid_adaptation.json`, 128 rules.
- The live `_compose_experiment_rule` Argmax candidate pool itself (per the
  prior rung's own A3 investigation, `part2_site_investigation_results.json`):
  **690 total `SeedSummary` nodes, 661 skippable** (real Argmax candidates —
  non-frozen).

### 1.2 Rust vs Python for `seed_where_signature` — same answer as the rule
grain, for the same reason

Exactly `RULE_SIGNATURE_SLICE_PREREG.md` §0.1's argument, one level up: the
computation operates over already-parsed manifest JSON
(`substrate.seed_loader.manifest_for`, the identical read
`reflective_faculty._rule_seed_map` already performs for the identical
purpose) and reuses the EXISTING graph-resident `where_signature` program per
rule (no new Term, no new Rust) — the only new code is the aggregation loop
over a manifest's `rules` list and the tagging of each row with its owning
rule's name. Pure Python, additive, no Rust — confirmed by inspection, not
assumed: `domains/seed_signature.py` calls no PyO3 method that does not
already exist, adds no Term variant.

### 1.3 The design choice the task explicitly requires be made, not assumed:
Term-level join vs precomputed aggregate field

**Decision: precomputed aggregate field on `SeedSummary`, mirroring
`RuleSummary.where_signature_json` exactly. NOT a live Term-level join.**

A Term-level join was considered: inside the `vary` branch's `Argmax` over
`SeedSummary` candidates, nest a nested `Filter`/`Exists` over `RuleSummary`
joined by `from_seed == s.seed_id`, scoring by `Exists` of a `where_signature_
json` substring hit. This is EXPRESSIBLE in the existing algebra (the same
`Filter`/`Exists`/`NodesOfType` primitives A1/A2 already use, no new Term
type) — but rejected for two independent reasons, per §0's own structural
observations:

- **Coverage.** `RuleSummary` mirrors only `chosen_action`/`reply`/
  where-literal-writing rules — a small minority of the 4127-rule corpus
  (§1.1). Joining against it would score a seed by an arbitrary, effect-shape-
  filtered SUBSET of its rules, not what the charter asks for ("what the
  seed's rules structurally DO," unqualified).
- **Live cost, no caching.** Per §0 property 2, this Term is evaluated by the
  engine's own `run_rules()` fixpoint every time the installed mint rule's
  `where` matches — unlike A1/A2, which call `native.evaluate` ONCE from
  Python. A nested join re-walking (up to) 661 seeds × their rule sets, INSIDE
  a live installed rule, with no memoisation the engine provides for a Term
  evaluation, is real per-firing cost with no free caching — a materially
  different risk profile from A1/A2's one-shot Python-side evaluation.

The precomputed aggregate avoids both: `ensure_seed_signature` (called once,
idempotently, from `_compose_experiment_rule`'s Python — the SAME idempotent-
mint discipline `_pick_acting_rule` uses for `rule_signature.
ensure_where_signature`) walks EVERY rule the seed's manifest declares
(§1.1's full 4127, not the `RuleSummary`-mirrored subset) and stores the
union as ONE JSON-string attr, `SeedSummary.where_signature_json` — read back
by the installed rule's Term via the IDENTICAL `StringIndexOf` shape
`keywords_text` already uses. The installed rule's own Term complexity is
UNCHANGED (one more string-attr read per candidate, no nested join, no new
Term type) — this is the load-bearing property: it keeps the fix inside the
existing Term-tree convention (`_pick_acting_rule`'s own docstring: "Both
Argmaxes stay inside ONE evaluated Term — the fallback is a branch of the
SAME Term tree, not a second Python-side decision") while moving the
EXPENSIVE part (walking 4127 rule declarations) to a one-time Python
precompute, exactly where `ensure_where_signature` already puts the
equivalent cost for the rule grain.

### 1.4 `ensure_seed_signature` cost, measured before being trusted as
"one-time, acceptable"

*(filled in from `scripts/seed_signature_discover_probes.py`'s own timed run
— see §AR4 / the RESULTS doc for the actual number; registered here as a
gate: if the full-corpus first-call cost is so large it cannot complete
inside a normal daemon tick budget, that is itself a finding this doc commits
to reporting honestly, not silently absorbing.)*

---

## AR1 — the combination-wiring design (registered before the edit)

**Same reasoning A1/A2's own AR1 used, restated for this site, not
re-derived from different first principles**
(`RULE_SIGNATURE_PRODUCTION_WIRING_PREREG.md` AR1): a naive full replacement
of the `keywords_text` Argmax with a structural-only Argmax risks regressing
whichever seeds are genuinely named by their OWN identifiers (id/rule-name/
description words) rather than by what their rules structurally read/write —
symmetric to A1/A2's Class B. **Decision: LEXICOGRAPHIC FALLBACK, identical
shape to A1/A2.** Try `keywords_text` Argmax first, exactly unchanged
(`_compose_experiment_rule`'s `vary` branch's existing Term is NOT edited in
its primary path); only when it genuinely abstains (`best == None` OR its own
`overlap(best) <= 0` — the SAME abstain test the unmodified code already
performs) does the SAME `Sum`/`StringIndexOf`/`Argmax` shape run a second time
against `SeedSummary.where_signature_json` instead of `keywords_text`.
Expressed as ONE Term (matches `_compose_experiment_rule`'s own existing
convention: Python assembles the Term dict mechanically, the WHOLE
lexicographic decision is evaluated inside the engine in one call, embedded
into the SAME `{"__term__": ...}` `delta_attrs["skip_seeds"]`/
`delta_attrs["skip_seed_id"]` slots the unmodified code already writes).

**Not a pre-filter, not a weighted blend** — same reasoning as A1/A2's own
AR1 (§ of that doc): structural scores 0 on any seed whose identity is
genuinely name-native (a seed with generic rule names but a distinctive id/
description), so pre-filtering on it first would risk excluding the
name-native winner before `keywords_text` ever saw it; the two scores are not
commensurable (word-hits against a short id/blurb string vs word-hits against
a much larger aggregated structural JSON blob), so a blend needs a tuning
weight this rung has no principled way to set and no measured need to.

---

## AR2 — the powering bar

This site's real candidate population (661 skippable seeds) is smaller than
A1/A2's ~44-rule pool only in the sense that A1/A2 measured PER-RULE; here
the natural unit is PER-SEED, and 661 is comfortably larger than A1/A2's
whole pool. Per the task brief's own explicit framing ("no floor is
pre-set... uniform treatment is not required" —
`RULE_SIGNATURE_PRODUCTION_WIRING_PREREG.md` AR3's own precedent for a
per-site verdict, which is what this rung IS, made concrete for A3
specifically), this rung registers a SMALLER but still real, non-invented,
mechanically-discovered oracle rather than A1/A2's full 40-probe design:

- **Floor: at least 4 genuine, mechanically-discovered Class A probes**
  (a seed where a real `CapabilityAxis`-shaped residual-predicate word
  structurally names one of that seed's rules but is absent from the seed's
  own `keywords_text`) **and at least 2 genuine Class B probes** (a seed
  where `keywords_text` already carries a genuine, non-zero-overlap match) —
  discovered by `scripts/seed_signature_discover_probes.py`'s mechanical
  scan over the REAL 661-seed population, never hand-invented.
- **Directional bar:** on the discovered Class A probes, the primary
  `keywords_text` Argmax must abstain (score 0) and the structural fallback
  must correctly pick the seed the probe word was drawn from, on EVERY probe
  used as a live demonstration (small-N here, so no 5-margin win-count bar —
  this rung reports the raw pass/fail per probe, honestly, rather than
  dressing up a small N as powered).
- **No-regression bar:** on the discovered Class B probes, the WIRED function
  (primary + fallback) must return the IDENTICAL seed the unwired primary
  Argmax alone already returns — the fallback must never fire when the
  primary already found a genuine (score > 0) match, confirmed by construction
  of the Term (same `Ite` guard shape A1/A2 use) AND checked live on the
  Class B probes.
- If §1.1's real population cannot support 4 genuine Class A probes (the
  structural signature genuinely never diverges from `keywords_text` at the
  seed grain — a real possible outcome, not assumed away), this rung reports
  **underpowered / NO-GO**, with the raw counts given exactly as measured.

---

## AR3 — build `seed_signature` + the fallback wiring (scope)

- `domains/seed_signature.py::seed_where_signature(sub, seed_id, manifest) ->
  frozenset[(rule_name, *row)]` — union, over EVERY rule the seed's own
  manifest declares (re-read from disk via `manifest_for`, not the
  `RuleSummary`-mirrored subset), of `rule_signature.where_signature(sub,
  rule['where'])`, each row tagged with its owning rule's name. A rule whose
  program traps is skipped (mirrors `ensure_where_signature`'s own documented
  behaviour), not guessed.
- `ensure_seed_signature(sub) -> int` — idempotent, mints/upgrades ONE new
  attr `where_signature_json` on the EXISTING `SeedSummary` population
  `substrate/boot_all.py::_mint_seed_summary` already produces. No `add_node`
  anywhere in the new module (confirmed by inspection) — mirrors
  `rule_signature.ensure_where_signature`'s own "additive attr only" scope
  exactly.
- **`_compose_experiment_rule`'s `vary` branch (`reflective_faculty.py:4324-
  4344`)**: the ONLY production edit. Add a `_resolve_agent(agent)` call +
  `seed_signature.ensure_seed_signature(sub0)` before the Term is built
  (mirrors `_pick_acting_rule`'s own `_ensure_acting_rule_provenance` +
  `rule_signature.ensure_where_signature` precall exactly); extend
  `skip_id_expr`'s `Let`/`Ite` chain with the SAME lexicographic-fallback
  shape AR1 registers, reading `where_signature_json` instead of
  `keywords_text` on the `Not(...)`/abstain branch. `overlap`/`candidates`/
  `best` (the primary Argmax) are UNCHANGED.
- **Zero changes to `_pick_acting_rule`, `_pick_reply_rule`,
  `_ensure_acting_rule_provenance`, `_ensure_reply_rule_provenance`,
  `domains/rule_signature.py`, or any A4-A9 site** (A4's own in-flight branch,
  if any, touches `_EDIT_OPS`/`_compose_structural_variant` at a disjoint line
  range — not this rung's concern).

---

## AR4 — no regression

- **Paired failing-node-id lists, not counts**, for the self-experiment
  composer path this task touches: `tests/test_experiment_composer.py`,
  `tests/test_self_delta.py` (its own `test_skip_seeds_pick_is_
  discriminative` directly exercises this Argmax), `tests/test_composers_
  graph.py`, `tests/test_acting_variant.py`, `tests/test_agent_authors_new_
  rule_migrated.py`, `tests/test_gap_awareness_migrated.py`,
  `tests/test_self_concern_promote_migrated.py`.
- **Baseline captured on this worktree BEFORE the production edit**, on
  `6314ebe` — then re-run after the wiring edit lands, comparing lists, not
  counts.
- **New test file**: `tests/test_seed_signature_structural_fallback.py` —
  the Class A/Class B live demonstration as a pytest gate (not just a
  throwaway script), so the finding is a standing regression check, not a
  one-off measurement.

---

## Reproduce (this doc's own validation, before any production edit)

```bash
cd /home/matt/ocelot-seed-signature
git log --oneline -1                                        # 6314ebe (detached base)
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so   # 23ba3f1d...92af (unchanged)

# §1.1/§1.4 — population count + ensure_seed_signature cost, discovery of
# real Class A/B probe candidates
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scripts/seed_signature_discover_probes.py
```
