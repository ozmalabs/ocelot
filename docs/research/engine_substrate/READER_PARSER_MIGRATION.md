# Reading-parser graph-native migration (plan)

The deep reading parser (`domains/reading_collapse.py` +
`domains/coref_entities.py`) is the largest remaining Python system whose
DECISIONS should be graph rules the agent holds and can repair. This plan moves
those decisions graph-native, one at a time, behind the frozen-corpus byte-parity
gate, and — wherever the mechanism allows — gets the Jabberwock to AUTHOR the
rules itself (its composer via `induce_concern`/`ground_concern`, its
classify-by-join authoring `procedural_reader → binding_resolver →
method_synthesis`, or by teaching construction/marker DATA it holds), the same
way it self-built the recount and describe faculties this session.

## The governing constraints (every phase)

1. **No new Python decision.** Each moved decision becomes a graph rule / held
   construction-or-marker DATA, or a Rust-evaluated Term. `_skeleton_from_words`
   / `_find_main_verb` / coref naming Python that DECIDES must shrink, not grow.
2. **The Jabberwock builds it where it can.** Prefer the agent authoring the
   rule from a held method/concern over a hand-written seed rule. Hand-written
   graph DATA (a construction/marker row, a MethodSpec) is acceptable
   bootstrapping; hand-written Python decisions are not.
3. **Byte-parity discipline.** `tests/test_reading_parity_migrated.py` is the
   frozen Aesop+Grimm oracle. A phase that changes the parser will fail it. That
   is expected — but the fixture may be regenerated ONLY after auditing EVERY
   diff leaf-by-leaf and confirming each is a strict improvement or neutral
   (never a regression). If the diff is too large or mixed to audit with
   confidence, STOP and report — do not regenerate blind, do not fake.
4. **donkey == 0.** No LLM anywhere.
5. **Off-limits files** (concurrent sessions / frozen): `interlocutor_model.py`,
   `reflective_faculty.py` (import only), `world_adapter.py`,
   `seeds/conversation_*.json`, `seeds/intent.json`, `ast_to_term.py`,
   `curious_agent.py`, and the `code_*` files. No `teach()`/`seed_*` in probe
   scripts (persists + pollutes; delete any untracked pollution seed).
6. Do NOT run git. One phase per agent; phases run SEQUENTIALLY (each may
   regenerate the shared fixture).

## The residuals to migrate (each a Python decision → a rule)

### PHASE 1 — main-verb selection (the "of" mis-parse)
`He promoted the burning of fossil fuels.` reads `of(he_promoted_burning,
fossil_fuels)` — the nested `of` wins as the skeleton marker and the finite verb
`promoted` is never selected as the main relation. `He promoted fossil fuels.`
reads correctly (`promoted(he, fossil_fuels)`). The Python decision: in
`_skeleton_from_words`, `of` fires as a skeleton marker and the verb-finding
fallback (`_find_main_verb`, run only when NO skeleton marker fired) is skipped.
DECISION to move graph-native: "which token heads the main predication when a
finite verb and a nested preposition compete" — the verb should win; the `of`
is a nested-PP relation inside the object NP. (Related pattern already graph-
native: the `QUANTIFIER` partitive glue + the `BUT` contrast coordinator, both
MarkerClass DATA the reader reads.) Corpus scan: 519 sentences carry `OF` in the
skeleton, 363 with a verb before the `of` — but MOST are NOT mis-parses (the
`of` is genuinely the head, or the interaction differs), so the ACTUAL parity
diff is expected to be far smaller. Measure it empirically; audit the real diff.

### PHASE 2 — embedded-clause decomposition
`Public Citizen said Big Oil captured the government.` mashes `Big Oil captured
the government` into ONE entity `big_oil_captured_government` instead of a nested
event under `say`. The decision: a post-`say`/report-verb complement is a nested
clause to decompose, not a flat NP. Move the decompose decision graph-native.

### PHASE 3 — coref entity naming (surname retention)
`Robert Levy` → entity `robert` (the surname is dropped). `coref_entities`
entity-head naming picks the first token. The decision: a multi-token proper
name keeps its full span as the entity. Move graph-native.

## Sequencing
Phase 1 → review → Phase 2 → review → Phase 3. Each agent: map the exact Python
decision, move it graph-native (agent-authored where possible), measure the real
parity diff, audit it, regenerate the fixture only if every diff is an
improvement/neutral, add a migrated test asserting the new correct read + that
the decision is a rule (ablation changes output). Report the map, the diff, the
audit, and anything left Python with brutal honesty.
