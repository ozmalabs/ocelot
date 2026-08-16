# ToM system unification — RESULTS (Parts 2 & 3 landed; Part 1 deferred)

**Task**: user, "unify the tom system," following the hate→pity rung's
own investigation finding four disconnected ToM-adjacent systems
(`character_tom.py`, `psychology.py`, `interlocutor_model.py`,
`hate_attribution.py`'s `controllability_for`). Presented three concrete,
independently-scoped options; user selected: **register a shared
meta-shape, name/document bigville's ToM primitive, retire
`psychology.py`** — explicitly NOT the fourth option (structurally
merging `character_tom` and bigville's ToM), which the investigation
found would be destructive (different corpora, different
representations, no shared caller).

**Two of three landed. The third (shared meta-shape) turned out to need
a materially different, larger scope than first understood — reported
honestly below rather than forced through under a shallow reading.**

## 1. Retire `psychology.py` — LANDED

**Investigated before deleting, not assumed** (the first investigation's
claim — "nothing else imports it" — was INCOMPLETE and would have been
wrong to act on directly): `character_tom.py:147` loads a SEED FILE
(`seeds/psychology.json`, via `manifest_for("psychology")`) at runtime,
completely separate from the Python module. Confirmed precisely, before
touching anything:

- `domains/psychology.py`'s FUNCTIONS (`install_psychology`,
  `install_self_capabilities`, `_retarget_sign`, `has_theory_of_mind`,
  `mental_states`, `_ensure_concept`, `_ensure_edge`) all call
  CuriousAgent-era API (`agent.mind_graph`, `agent._concept_nodes`,
  `agent.mind_substrate.transform()`, `agent.install_microtheory`,
  `agent.operates_in`, `agent.learn_sign`, `agent.runtime_capabilities`)
  — none of which `WorldAdapter` (confirmed by reading
  `substrate/world_adapter.py`) exposes; `CuriousAgent` itself was
  deleted 2026-06-18.
- Their ONLY caller was `domains/arc3_full_seed.py`, confirmed
  independently dead: unreferenced by any live test, importable only
  from `scripts/arc_archive/*` (an explicitly-archived directory), and
  carrying 11 further CuriousAgent-only calls of its own.
- `tests/test_psychology_migrated.py`'s `has_theory_of_mind()`/
  `mental_states()` calls are methods on `WorldAdapter` ITSELF
  (`substrate/world_adapter.py:4569,4580`) — a completely separate,
  already-migrated implementation, confirmed by reading before assuming.
  It imports only the CONSTANT TUPLES from `psychology.py`
  (`_MENTAL_STATES`, `_MENTAL_STATE_PARENT`, `_MIND_CONCEPTS`,
  `_TOM_CONCEPTS`, `_PSYCHOLOGY_MT`) to assert against `seeds/
  psychology.json`, loaded via the modern `WorldAdapter(seeds=...)` path.

**Removed precisely**: the seven CuriousAgent-era functions and
`_MENTAL_VERB_SIGNS` (data only the removed `install_psychology` read).
**Kept precisely**: the five constant tuples the live migrated test
imports, and the seed file itself (`seeds/psychology.json`, untouched —
`character_tom.py`'s own dependency). `domains/arc3_full_seed.py`'s own
reference to `install_psychology` was left as-is — it was already broken
independently of this change, and fixing a fully-dead, archived-only
orchestration script is a separate, out-of-scope cleanup, not part of
this task.

Verified: `tests/test_psychology_migrated.py` 11/11,
`tests/test_character_tom.py` 18/18 (confirming `seeds/psychology.json`
is genuinely untouched and still loads).

## 2. Name/document bigville's ToM primitive — LANDED

New module `domains/bigville_theory_of_mind.py`:
`mint_resident_tom_belief(inner, mt, aspect, target)` — a thin, named
wrapper over `shared_arousal.mint_target_concept`, drawing the precise
distinction the investigation surfaced: NOT every target-scoped Concept
is a ToM belief. `regard_for`/`desire_for`/`removal_desire_for`/
`pity_for` are the RESIDENT's own affect toward the target (plain
`mint_target_concept`, no wrapper needed); `controllability_for` is
different in kind — it attributes a property of the TARGET's own agency
(Premack & Woodruff 1978's own definition of Theory of Mind: attributing
mental states to ANOTHER). `hate_attribution.py`'s own
`controllability_for` minting now routes through this named entry point
— same node, same behavior, now reachable by name for the next rung that
needs a genuine ToM-of-another-resident belief instead of re-deriving the
pattern from prose comments.

Verified: `tests/test_bigville_theory_of_mind.py` 4/4, confirming the
named entry point and `hate_attribution.py`'s own direct-mint path
resolve to the IDENTICAL node.

## 3. Register a shared meta-shape — DEFERRED, scope corrected

**What the first investigation didn't surface, found only by trying to
implement this**: there is no single "meta-shape system" to register
into. Reading the actual seed data (`seeds/shape_vocabulary.json`,
`seeds/meta_shape_growth.json`) surfaced THREE genuinely distinct "shape"
subsystems in this codebase, not one:

1. **Construction-grammar `ShapeSignature`s** (`character_tom.py`'s own
   `propositional_attitude`, `reading_collapse`'s codebook) — pattern-
   match constructions for TEXT PARSING, decoded via
   `reflective_faculty.compose_design_for_goal`'s `ShapeDecode` Term.
2. **The `MetaShape`/`ShapePrinciple` self-organizational taxonomy**
   (`shape_vocabulary.json`'s 41 static nodes — `FunctionalRole`,
   `ShapePrinciple` entries like `homeostasis`/`prediction`/
   `pattern_completion`/`structure_mapping` — feeding
   `analogical_thinking`'s `recognise_meta_shape`, per CLAUDE.md's own
   META_SHAPE_FIRST_CLASS_RESULTS.md work) — the taxonomy `teach()` files
   the agent's own knowledge under.
3. **The dynamic sd-loop `ShapeSignature` codebook**
   (`meta_shape_growth.json`, 0 STATIC nodes — everything here is MINTED
   AT RUNTIME by the recognize→transform→infer-dimension→mint rule
   ladder CLAUDE.md documents; there is no seed-time registration point
   at all for this layer).

Registering a "shared meta-shape" that lets the substrate recognize
character_tom's nested belief-world and bigville's target-scoped belief
as the SAME abstract pattern requires committing to WHICH of these three
systems is the right target, and — for options 1 and 3 — actually
running real recognize/decode passes over both concrete instances and
confirming convergence, not just adding a static graph node. That is
materially more work, and more risk to two independently-tested working
subsystems, than the shallow "add one linking node" the original
proposal implied.

**Not attempted without checking back first.** Rather than force a
shallow, cosmetic registration into whichever system looked easiest (a
`has_principle` edge into `shape_vocabulary.json`'s static taxonomy would
be low-risk but would NOT actually let `analogical_thinking` recognize
the shared shape at decode time — it would just be a label, not the
capability the user asked for), this is reported back honestly as needing
a scoping decision: which of the three systems, and at what depth
(static label vs. live recognize/decode convergence)?

## 4. Files

- `docs/research/engine_substrate/TOM_SYSTEM_UNIFICATION_RESULTS.md` (this file)
- `domains/psychology.py` (edited: 7 CuriousAgent-era functions + `_MENTAL_VERB_SIGNS` removed, constants kept)
- `domains/bigville_theory_of_mind.py` (new)
- `domains/hate_attribution.py` (edited: `controllability_for` now minted via `mint_resident_tom_belief`)
- `tests/test_bigville_theory_of_mind.py` (4/4, new)
