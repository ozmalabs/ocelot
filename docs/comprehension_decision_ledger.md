# Comprehension decision ledger — the Python blind-spot burn-down list

**Wave 3 (Deep-Reader cutover, 2026-07-10).** The shadow read (Wave 2:
`WorldAdapter._shadow_read_turn`, opt-in, `reading_drive.run_reading_flow`
under the `conversational` aperture) is now a REAL, if partial, INPUT to the
comprehension record — the divergence corpus
(`tests/fixtures/comprehension_divergence/divergence.json`, 162 utterances)
decided WHICH fields cut over and how far:

* **kind — NO cutover.** `sak_kind` (Wave 4, `seeds/speech_act_classify.json`)
  stays authoritative: 93.8% agreement (152/162) with the shadow read, and
  all 10 disagreements are `comp_kind` being deliberately PRAGMATIC (surface
  imperatives promoted to `question` for the satisfiable/meta/table dispatch —
  "Name one of your rules.", "List your rules.", "Tell me about the rule X.",
  "Show me your gaps.", politeness-prefixed forms, one THEN-marker case, one
  "There is a gap in your reasoning."). Instead, `_write_comprehension_to_graph`
  (`substrate/world_adapter.py`) now writes a mechanical DATUM,
  `speech_act_divergence=1.0`, whenever the final `comp_kind` disagrees with
  the Message's own `shadow_speech_act` (both values stay independently
  readable on the same Message — no new echo attrs needed). No routing rule
  consumes it; it exists for the agent's own future divergence-noticing
  machinery (a `gap_awareness`-style recurring-divergence rule was scoped and
  DELIBERATELY DEFERRED — pure scope discipline, not a difficulty finding: the
  10 disagreements are all_ already-understood, one-off pragmatic promotions,
  not a live noticeable pattern yet).
* **predicate/content for INSTRUCTIONS — STRICT ENRICHMENT cutover.**
  `_write_comprehension_to_graph` computes the OLD leading-verb parse
  (`d.get("predicate")` / `_instruction_content`) exactly as before; when (and
  ONLY when) the OLD predicate is absent for an instruction-kind turn, it
  reads `shadow_predicate` (recorded on the Message earlier in the SAME
  `converse()` turn, before `comprehend_text` runs) back as `comp_predicate`
  (tagged `comp_predicate_source=shadow_enrichment`), and likewise falls back
  to `shadow_focus` for `comp_content` when the old predicate — and therefore
  any old argument extraction — was absent. When the old predicate IS present,
  both fields are BYTE-IDENTICAL to pre-Wave-3 (the instruction rows of
  `tests/fixtures/speech_act_parity/speech_act.json` and the whole divergence
  corpus's 36 instruction rows all carry a non-null OLD predicate today, so
  this enrichment currently fires on ZERO rows in either fixture — an HONEST
  residual, not a defect: `_instruction_content`'s own final fallback is the
  raw text, which is "always present" in the sense the strict enrichment rule
  checks, so on-corpus value is mostly forward cover for a genuinely empty
  frame; see the honest coverage note in the Wave 3 build report). This keeps
  the "old value wins on disagreement" parity bar from the mission brief
  automatically, because the branch it would have disagreed on (both sides
  present) is exactly the branch this policy never touches.
* **topic/focus — ENRICHMENT ONLY, single-token-restricted.** The existing
  `_topic_facts`-driven NP-span extraction is untouched; a NEW final `elif`
  branch in `_write_comprehension_to_graph` fires only when NOTHING else
  claimed the turn (no `facts.get("topic")`, no anaphor, not a know-table
  question, not deferred to meta, not hypothetical, not attachment-routed) AND
  the turn's `comp_kind == "question"` (matching `route_question_to_topic`'s
  own kind guard — `topic_pending` on a non-question turn would be inert, so
  scoping to question keeps the write meaningful) — it reads `shadow_focus`
  and writes it as `comp_topic` + `topic_pending=1.0` ONLY when it is a
  SINGLE clean token (mission's own documented fallback: shadow_focus is a
  HEAD-only read — "problem" for "three body problem" — and this wave does
  not build multi-word NP-span recovery off the shadow SentenceParse, so a
  multi-word shadow_focus is left alone rather than routing on a truncated
  topic). Existing comp_topic-bearing rows are byte-unchanged (the branch is
  reached only when the old parse wrote nothing at all).
* **Latency lever — TWO real duplicate-rule-install bugs found and fixed, not
  a rule-scope filter.** Profiling the shadow read's tick loop via the
  engine's `rule_costs()` self-instrumentation (not guesswork) showed the
  reading-family (`la_*`) rules were NOT the dominant cost; the dominant cost
  was `rule_mention_resolves_to_concept` evaluated TWICE per pass, because
  the full-seed agent held DUPLICATE copies of whole rule families. Root
  cause, both sites the same shape: `substrate.boot_all.load_all_seeds` (a
  full boot) records installed seeds as `SeedSummary{seed_id}` nodes, but two
  on-demand seed loaders checked ONLY for `Seed{id}` marker nodes and so
  re-installed already-loaded seeds on a full-boot agent's first use:
  (1) `domains/reflective_faculty.py::_ensure_seed_chain` /
  `_ensure_shape_decode_loop` — called on every `run_reading_flow` /
  `induce_concern` — re-installed `literary_analysis_driving` +
  `shape_decode_loop` + `composer_dispatch` + deps (measured 18→36 `la_*`
  rules, +21 rules overall, on the first post-boot reading-flow call);
  (2) `substrate/boot_core.py::load_seeds_into` — called by
  `receive_utterance._ensure_intent_seeds` — re-installed the whole intent
  closure (+16 duplicate rules including the second
  `rule_mention_resolves_to_concept`) on the first conversation turn. Fixed
  by honouring BOTH provenance markers (`_installed_seed_ids()` helper in
  `reflective_faculty.py`; a `summary_installed` skip-set in
  `load_seeds_into`, used for the skip check only — `Seed`-node bookkeeping
  and depends_on wiring unchanged). Mechanical bookkeeping corrections, no
  new decisions. MEASURED (full-seed agent, 8-turn battery, shadow latency
  excl first turn): before ~292ms avg / climbing to 413ms; after ~214ms avg
  / climbing to 296ms (~27% cut; duplicate rules eliminated: post-turn rule
  count 480→458, only the 5 pre-existing cross-seed name collisions remain).
  The `≤100ms` target was NOT reached: the honest residual is (a)
  `rule_mention_resolves_to_concept`'s O(held concepts × accumulated
  mentions) join re-evaluated in every `run_rules` pass — it grows with
  conversation length and dominates every fixpoint, shadow or not; and (b)
  the engine offers NO rule-family scoping (`run_rules(max_steps)` has no
  filter; Shape-target pruning is a different axis) — Rust-side support
  needed: either a per-rule scope tag honoured by `run_rules`'s dirty-scan,
  or (better, fixes (a) too) an incremental index for the
  mention→concept-name equality join. Not hacked around in Python, per the
  architecture rule.

**Wave 4 (2026-07-10).** Governing principle: *self-repair ⟺ graph-native;
Python is the blind spot.* Every decision below is one the agent currently
CANNOT see, experiment on, or repair, because it executes in Python instead of
as graph rules. This ledger is the exhaustive inventory of every remaining
Python decision on the comprehension path (text in → comprehension record →
routed turn), each with its inputs, migration difficulty, and blockers. It is
the burn-down list for the next waves.

**Migrated this wave (Wave 4):** the speech-act KIND decision
(`comprehend_text._classify_kind` → `seeds/speech_act_classify.json`,
sak_kind_* rules; adapter writes only signals; parity-gated byte-for-byte over
133 utterances by `tests/test_speech_act_parity_migrated.py`; regression
pinned by `tests/test_comprehension_decision_audit_migrated.py`).

Difficulty scale:

* **S** — a boolean/enum over signals already (or trivially) graph-visible;
  one seed rule + at most a mechanical signal write. The sak pattern applies
  directly.
* **M** — needs several parse facts written as graph data, an ordered
  preference expressed as rule guards, or a modest new signal surface; no new
  Rust required.
* **L** — needs a prerequisite build: the parse frame as first-class graph
  data (per-token role/pos on Mentions), a lexicon-as-nodes + scoring Term, or
  a new Rust primitive.

**Cross-cutting blockers** (referenced as B1–B4 below):

* **B1 — the parse frame is not graph data.** `parse_with_gaps`'s elements
  (surface/role/pos, focus, gaps) live only in a Python dict. Mentions carry
  `text` + reading-order adjacency but not POS/role. Any frame-shape decision
  (topic NP spans, polar detection, relation composition reads) migrates
  cleanly only after the adapter mechanically writes the parsed
  role/pos/focus onto the Mention chain (a pure translation of data the POS
  layer already computed — sanctioned).
* **B2 — provisional-kind / half-ingested-turn exposure.** Downstream rules
  key on `comp_kind`. Until the still-Python intercepts (table fastpath,
  satisfiable, rule-name promotion) migrate, the rules must mint the ladder
  kind as `sak_kind`, not `comp_kind` — minting `comp_kind` in the
  pre-comprehension pass would expose a provisional kind (e.g. "Tell me about
  the moon." is ladder-instruction, final-question) to comp_kind-keyed rules
  mid-turn. Documented in the seed. **Measured corollary (Wave 4):** running a
  FULL `comprehend()` fixpoint between ingest and the comp_* writes is itself
  a behavior change — mention-keyed rules fire on the half-ingested turn
  (observed: `serve_next_detail_chunk` won the serve-vs-anaphor race that
  install order had settled the other way, flipping
  `test_more_without_detail_falls_through_to_summary`). Mid-ingest rule
  decisions must therefore run ISOLATED (export the held rule bodies, run
  them alone — `_graph_kind_for`'s pattern) until the whole turn ingest is
  itself rule-driven.
* **B3 — bag-of-words scoring in the DSL.** The meta-lexicon keyword-overlap
  scoring (`_best_meta_entry`) is an argmax over entries × fragment
  containment. Doable as lexicon-entries-as-nodes + an Argmax Term, but the
  entry set (`seeds/question_targets.json`) must first be installed as nodes
  rather than a JSON file Python loads.
* **B4 — intercept ORDER is itself a decision.** `comprehend_text` runs
  name-inquiry → self-identity → self-kind → self-process → coinage →
  satisfiable → no-world → table → general, and the question branch runs
  rule-name > self-process > keyword > polar-capability > honest-manner >
  wh-default. Migrating one intercept means expressing its position in this
  ladder as rule priorities/guards (the escalation_rungs precedent), not just
  its predicate.

---

## 1. `domains/comprehend_text.py`

| # | Decision | What it decides | Inputs | Diff | Blockers |
|---|---|---|---|---|---|
| 1.1 | `_classify_kind` | question / instruction / statement | ends-?, first element role/pos | **DONE** | — (Wave 4: `seeds/speech_act_classify.json`; body retained only as capture oracle + no-native fallback) |
| 1.2 | `_strip_politeness` | leading token is a discourse/politeness marker → strip | recognised words, `_POLITENESS_MARKERS` | M | markers as held Concepts + a Mention-marking rule; the strip itself stays mechanical normalisation |
| 1.3 | `_is_name_inquiry` (→ `sense_of_reference.is_name_inquiry`) | the turn asks about the agent's own NAME | text patterns, name references | L | lives in a separate module with its own pattern logic; B4 |
| 1.4 | `_detect_self_identity` / `_match_self_identity` | "what/who are you" identity intercept | recognised words per region; In/Eq/And Terms (verdict already Rust-evaluated) | M | shape SELECTION + region iteration + intercept position are Python; B4 |
| 1.5 | `_detect_self_kind` | copular polar self-classification ("are you an LLM?") | composed relation (subj∈self-cues, copula, object) + word-shape fallback | M | B1 (relation read), B4 |
| 1.6 | `_detect_self_process` | reflexive manner question the agent HOLDS a SelfProcess account for | "how"+self-cue prefilter, frame focus, `find_self_process` graph read | M | the graph read is already native; the gating/prefilter is Python; B1, B4 |
| 1.7 | coinage → wordplay routing (`_wp.find_coinage`) | an OOV token is a playful coinage → wordplay path | morphology/portmanteau analysis | L | the morphological analyser is its own Python faculty; B4 |
| 1.8 | `_detect_satisfiable` | enumerate-imperative over held data ("Name one of your rules") → target faculty | recognised words, `_ENUMERATE_VERBS`, possessive cue, `_SATISFIABLE_TARGET` | S | verbs/targets as Concepts (the instruction_route precedent) + one rule over the Mention chain; B4 for its ladder slot. **Next-smallest candidate** |
| 1.9 | `_is_perception_request` + `_conv_scene is None` (honest_no_world) | a perception report is requested with no world attached | leading account verb, perception cues, scene state | S | cue sets as Concepts; `_conv_scene` must become a graph datum (an edge, like current_attachment); B4 |
| 1.10 | table-fastpath precedence (`_cq.comprehend` grounded → wrap & stop) | the held construction table owns this turn | TargetSpec.grounded | M | depends on §3 (the table itself, L); B4 |
| 1.11 | empty-frame guard | no tokens → frontier dispatch | frame.elements empty | S | one rule once frame emptiness is a signal; B2 |
| 1.12 | reflexive determination | question is ABOUT the agent | grounded rule name (`_detect_reflexive_rule`) OR self-cue word | M | rule-summary lookup is a graph read; the OR + cue set are Python; B1 |
| 1.13 | spurious-rule-name suppression | a self_* faculty beats a rule name that is one of its own match fragments | meta-lexicon fragments vs rule name | M | B3 |
| 1.14 | question strategy ladder | rule_name > self_process > keyword > polar-capability > honest-manner > wh_default | all of the above | M | ordered rules with mutual-exclusion guards (escalation_rungs precedent); B3, B4 |
| 1.15 | `_best_meta_entry` / `_score_meta_entry` | which meta-lexicon entry best covers the words | `seeds/question_targets.json` entries, word bag | L | B3 |
| 1.16 | `_capture_meta_arg` | the argument span for a meta target (arg_after / arg_between) | entry anchors, token list | M | span extraction over the Mention chain |
| 1.17 | `_is_polar_capability_question` | polar "can you X" with no external object | composed relation | M | B1 |
| 1.18 | `_hypothetical_assumption` | counterfactual "if you had X" on a polar question | regex over raw text | M | regex → Mention-chain rule; duplicated in world_adapter (§2.12) |
| 1.19 | `_asks_self_structure` | manner question is about STRUCTURE (self_organisation) vs process | `_STRUCTURE_CUES` bag | S | cues as Concepts + refers_to rule (the deficiency-cue precedent) |
| 1.20 | `_self_process_verb` | phrasing datum for the honest self floor | frame adjacency | S | render-side only; not a routing decision |
| 1.21 | world-question topic + `resolve_focus` → know/frontier | topic nominal, pre-resolved answer, else frontier | composed relation, substrate | M | B1; overlaps `route_question_to_topic` (already a rule) — consolidation target |
| 1.22 | instruction promotion (grounded rule name → question) | "Tell me about the rule X" is an information request | gap tokens vs held RuleSummaries | M | B2 (it changes kind after the sak rules ran), B4 |
| 1.23 | instruction predicate/object extraction | which spans are predicate/object | first element, composed relation | S | mechanical-adjacent; write as parse data (extends the existing comp_predicate write) |
| 1.24 | statement branch | everything else is an assertion | — | S | falls out when 1.14 migrates |

## 2. `substrate/world_adapter.py` (comprehension path)

| # | Decision | What it decides | Inputs | Diff | Blockers |
|---|---|---|---|---|---|
| 2.1 | `classify_speech_act` | greeting/thanks/question/request/statement at the I/O boundary | `_GREETING_FORMS`/`_THANKS_FORMS`/`_QUESTION_LEADS`/`_IMPERATIVE_LEADS` head cues | S | sanctioned boundary classifier, but forms could be held Concepts + rules (the deficiency-cue precedent); interacts with `_SOCIAL_ACTS` (§2.13) |
| 2.2 | `_write_comprehension_to_graph`: defer-to-meta (`_defer_to_meta`) | a meta-classified turn whose topic head is a self-word writes no comp_topic | dispatch.path, topic head, `_SELF_WORDS` | M | reconciliation of two parse outputs; becomes a rule guard once topic facts are rule-visible (B1) |
| 2.3 | `_write_comprehension_to_graph`: `route_topic` gate | whether to write comp_topic + topic_pending (the topic-route trigger) | kind, hypo, attachment_routed, `_ATTACHMENT_REF_WORDS`, self_kind meta, reflexive, composition | M | the biggest residual conjunction; most conjuncts are already Message attrs — consolidate into `route_question_to_topic`'s guards |
| 2.4 | `_write_comprehension_to_graph`: elliptical follow-up gate | topic_followup for a verbless fragment | topic facts | M | B1 |
| 2.5 | `_write_comprehension_to_graph`: know-table topic write | a table know-question's concept becomes comp_topic | spec.know_concept, `_SELF_WORDS` | M | depends on §3 |
| 2.6 | `_attachment_question_refs` / `_text_decode_question_refs` | the turn refers to the held upload / asks to read its text | `_ATTACHMENT_PHRASES`, `_TEXT_DECODE_PHRASES`, topic facts | M | phrase lists as held Concepts/signs; B1 |
| 2.7 | `_topic_facts` | the turn's topic NP (multi-word span), anaphor, elliptical, made-of composition | frame elements, composed relation, `_ANAPHOR_*`, `_TOPIC_DETERMINERS` | L | B1 — needs per-token role/pos on the Mention chain + an NP-span walk (rules or a Rust term) |
| 2.8 | `_instruction_content` | which span a read-instruction reads (after ':', else object, else raw) | raw text, comp object | S | preference order as rule guards over parse data |
| 2.9 | `_record_self_account_gap` / `_record_instruction_outcome` / `_answer_topic_reply` outcome | (recorders — sanctioned data writes) with thin gating (`if topic:`, handled iff goal/marker) | graph state | S | mostly done; the residual gates are one-conjunct |
| 2.10 | `answer_question` dispatch sequencing | which backend answers (table-meta reflect / meta / honest_self / know) + regex "what is X" fallback | comp.dispatch | M | mirrors what converse's rules already decide; the regex fallback is S |
| 2.11 | `_reply_for_inbound` fallback ordering | which outbound Message is "the" reply | responds_to spine, id order | S | mechanical read with a preference; make the reply edge explicit |
| 2.12 | `_hypothetical_assumption` (duplicate of 1.18) | counterfactual clause | regex | M | fold into 1.18's migration |
| 2.13 | `converse`'s `_SOCIAL_ACTS` skip | social turns bypass comprehension | speech_act name | S | one rule guard once 2.1 migrates |

## 3. `domains/comprehend_question.py` (the held construction TABLE)

| # | Decision | What it decides | Inputs | Diff | Blockers |
|---|---|---|---|---|---|
| 3.1 | `comprehend` ordering | compound > compare > meta > know > world-frame | sub-comprehenders | M | B4; the order is a preference ladder |
| 3.2 | `comprehend_meta` (`_all_present` fragment match) | which meta entry an exact-fragment question hits | `seeds/question_targets.json` meta lexicon, `_SELF_CUES` | L | B3 (lexicon as nodes); the seed file is already data — the MATCHING runs in Python |
| 3.3 | `comprehend_know` | "what is X" → know(X) | know templates | M | template set is small; B3 |
| 3.4 | `comprehend_compound` | ≥2 grounded leaves joined by a connective → compound subgoals | connective split + recursive comprehend | L | recursion over rules; the clause segmentation precedent (reading_collapse 1e) applies |
| 3.5 | `comprehend_compare` | acquired comparison construction → compare subgoals | acquired construction store | L | acquisition loop is entangled with the metacognitive path |
| 3.6 | `_map_to_target` | relation-phrase + object-phrase → formal op + params | lexicon entries, `_extract_degree` | L | B3; op params extraction |
| 3.7 | `plainify` / `_split_sentences` | LaTeX → surface tokens; sentence split | markup | S | sanctioned mechanical translation — keep (I/O boundary), listed for completeness |
| 3.8 | `diagnose_comprehension_gap` / `acquire_*` | why comprehension failed; mint a new construction | templates | L | the acquisition seam; out of the live turn path |

## Counts

| Difficulty | Count | Items |
|---|---|---|
| DONE (this wave) | 1 | 1.1 |
| S | 12 | 1.8, 1.9, 1.11, 1.19, 1.20, 1.23, 1.24, 2.1, 2.8, 2.9, 2.11, 2.13 (+3.7 sanctioned-keep, not counted) |
| M | 17 | 1.2, 1.4, 1.5, 1.6, 1.10, 1.12, 1.13, 1.14, 1.16, 1.17, 1.18, 1.21, 1.22, 2.2, 2.3, 2.4, 2.5, 2.6*, 2.10, 2.12 → of these 2.12 folds into 1.18 and 2.6 counts once ⇒ 17 distinct |
| L | 8 | 1.3, 1.7, 1.15, 2.7, 3.2, 3.4, 3.5, 3.6 (+3.1/3.3 ride on B3; 3.8 out of turn path) |

**Recommended next moves (in order):** (1) 1.8 `_detect_satisfiable` — pure S,
fixtures already in the parity corpus ("Name one of your rules.", "List your
rules.", "Enumerate your faculties."); (2) 1.9 honest_no_world (S, needs
`_conv_scene` as an edge); (3) the B1 prerequisite build (write role/pos onto
the Mention chain — mechanical, unlocks 1.5/1.6/1.17/1.21/2.2/2.3/2.4/2.7);
(4) consolidate 2.3's route gate into `route_question_to_topic`'s guards.

**Honest note on `comp_kind`:** the sak rules mint the ladder's decision as
`sak_kind`, and `comp_kind` remains the FINAL record `_write_comprehension_
to_graph` writes (an echo of `sak_kind` on the general path; overridden by the
still-Python intercepts exactly as before). `comp_kind` becomes rule-minted
end-to-end only when B2 clears (the intercepts migrate) — until then the seed's
description documents why.

## 4. Dynamic-thresholds / reopen / reform wave (2026-07-11) — TABLED literals

The wave landed the reading-layer threshold family FULLY (ring/reopen/reform/
order — see `seeds/reading_aperture.json`'s `ApertureBudget.trace_capacity_*`/
`max_revisits`/`max_order_*`/`widen_*`/`reform_*`, the two held Program
derivations `reading_derive_trace_capacity`/`reading_derive_max_order`,
`domains/reading_norms.py`, and `tests/test_dynamic_thresholds_migrated.py`).
Per the task's own "prefer a working vertical slice" instruction, the
FOLLOWING pre-existing rule literals were surveyed but deliberately NOT
promoted this wave — they are a different family (narrative-shape detection,
speech-act-divergence health, and salience-cache promotion) whose rules live
in OTHER seed files, and promoting them was judged separable, lower-risk work
rather than essential to the ring/reopen/reform vertical slice:

| # | Literal | File : rule | What it gates | Diff | Note |
|---|---|---|---|---|---|
| 4.1 | `3.0` / `2.0` / `1.0` (sentences/animates/wants floors) | `seeds/reading_aperture.json` : `escalate_narrative_shape` | when a light-aperture read's spine LOOKS narrative-shaped enough to escalate to full depth | S | same file as this wave's own rules, same `ApertureBudget`-per-register pattern — the natural next promotion, held back only for time; would add `narrative_floor_sentences`/`narrative_floor_animates`/`narrative_floor_wants` fields exactly like this wave's fields |
| 4.2 | `3.0` (recurrence count) | `seeds/comprehension_health.json` : `note_recurring_speech_act_divergence` | how many same-pair divergent Messages before the recurrence is "a pattern, not noise" | S | a different HealthNorm-keyed metric (`speech_act_divergence_recurrence`), not register-keyed — needs its own `Argmax`-by-`metric` Let, mirroring `note_comprehension_latency_gap`'s existing `ceiling` lookup in the SAME file (copy-paste distance) |
| 4.3 | `10.0` (span) / `3.0` (mentions) | `seeds/salient_cache.json` : `scell_promote` | local→story salience promotion (order-N nesting: a threading protagonist vs a one-scene bystander) | S | `salient_cache.json` has no per-register or per-metric norm node yet — would need a NEW singleton norm node (or a `SalienceClock`-attached pair), a smaller lift than 4.1/4.2 but a genuinely separate seed |

None of these gates decisions in the ring/reopen/reform path this wave built;
promoting them is mechanically the SAME pattern (extend a held node with the
literal's field, swap the rule's `Lit` for an `Attr` read) already proven
three times over in `seeds/reading_aperture.json` this wave — low risk,
scoped out purely for time.

## 5. Blind-spot closure R6 + R7 (2026-07-11) — two front-end routing decisions moved to graph rules

Wave directive: *"have the jabberwock close the python blind spot residuals"* —
close a Python-blind residual by ELIMINATING the blind spot (migrate the
DECISION into rule territory, so the surface enters the agent's own repair
jurisdiction), never by patching the Python. Both landed WITHOUT editing
`domains/comprehend_text.py` (its ladder is unchanged; the misroutes it still
produces are now overridden by rules the agent holds, can see, and can ablate).

**R6 — bare first-person routing ("Who am I?", "What do I want?") — DONE
(`seeds/first_person_routing.json` v1.0.0).** The failure was located
precisely: `_has_self_cue` (item 1.12's cue set) contains only second-person
cues + "me", so "Who am I?" / "What do I want?" set `reflexive=False`, fell to
the non-reflexive "know" branch (item 1.21), and looked the pronoun "I" up as
a world concept → "I don't hold that." The meta lexicon (B3, item 3.2) can't
catch it either — its interlocutor_model entries all require the token "me".
Migration shape: NOT a Python pronoun check and NOT new lexicon fragments —
the rule `route_first_person_question_to_interlocutor` joins the "know"
dispatch's own echoed topic nominal (`comp_know_concept`, a new mechanical
echo in `_write_comprehension_to_graph`, same status as `comp_verb`) against
the intent seed's EXISTING first-person resolution
(`rule_first_person_resolves_to_speaker`: Mention{i,me,my,mine}
-refers_to-> Intent.speaker, graph-resolved every turn): when the "know"
concept's own Mention refers_to THIS turn's speaker, the question is about
the SPEAKER → `Goal{kind:answer_interlocutor_meta}`. The adapter fulfiller
`_answer_interlocutor_meta_reply` (converse read-off leg 2b) renders it via
`reflect("interlocutor_model")` — the same reader "what do you know about me"
already uses. `conversation_honest_floor` v1.2.0 gained the matching third
deferral guard (same shape as its answer_topic/answer_attachment guards).
What moved OUT of Python: the "first-person-subject question ⇒ about the
speaker" ROUTING decision (a slice of 1.12 + 1.21's misroute surface). What
remains Python: `_has_self_cue`'s cue set itself (1.12), the know-branch
topic-nominal extraction (1.21) — both still on the burn-down list; the new
rule reads their OUTPUT rather than replacing them.

**R7 — multi-word topic keys miss the HeldAnswer bridge — DONE
(`seeds/conversation_topic_span.json` v1.0.0 + `conversation_topic_route`
v1.2.0).** The Wave-3 residual documented above (topic/focus enrichment
"single-token-restricted"; `_topic_facts` = item 2.7, B1-blocked, head-grain)
made "What do you know about the Wright brothers?" route on the truncated
head "wright" and miss the document bridge's own key "wright_brothers".
Migration shape: no new NP-span heuristic — `_shadow_read_turn` records
`shadow_doc_topic` mechanically (does one of THIS turn's newly-minted
SmEntities carry a name equal to an EXISTING HeldAnswer topic — two
independent runs of the SAME deterministic entity-naming landing on the same
string; the SmEntity-pool set-difference idiom is the one shadow_referent
already uses), and the rule `route_shadow_topic_to_answer` DECIDES that name
is the turn's topic, minting the same `Goal{kind:answer_topic}` shape keyed
on it. `route_question_to_topic` gained one static deferral guard
(`shadow_doc_topic` must be null — same precedent as its v1.1.0 possessive
guard; the attr is written pre-tick, so no install-order race). What moved
OUT of Python: the head-vs-span topic-key CHOICE for document-held topics.
What remains: `_topic_facts` (2.7) itself is still the head-grain frame walk
— B1 unchanged; the bridge covers exactly the topics a held document (or any
HeldAnswer) actually contains, not arbitrary multi-word world topics.

Gates: `tests/test_first_person_routing_migrated.py` (9: closure ×3, honest
unknown-party floor, parity ×4 incl. "what do you know about me" staying on
the old meta route, ablation-reverts proof) +
`tests/test_topic_span_migrated.py` (7: Wright-brothers closure, single-token
parity, absent-topic honest path, deep_ingest-off byte-identical,
self-question precedence, ablation-reverts proof). The ablation tests double
as the agent-jurisdiction proof: each closure is a live, named, removable
rule — `remove_rule` flips the behaviour back, so the experiment/adopt spine
can vary it.

**Environment note (bench):** a stale `substrate_rs` in site-packages
(2026-07-03, predates `TransferDecode`) loses the import race to
`runners/dsl/python` only in single-file runs; in a broad mixed chunk the
stale copy can load first and fail ~45 unrelated tests
(deform_metric/dimension_inference/aperture_escalation/document_memory/...).
Verified NOT this wave's doing: the same 46-test set is green with
`PYTHONPATH=runners/dsl/python` pinned, leaving only the pre-existing
`exhausted_trail` failure. Fix is `pip install -U` of the fresh wheel or
always pinning PYTHONPATH in broad benches.

## 6. Blind-spot closure R8 + R9 (2026-07-12) — the reform's own components
reach the situation model; a modeled belief carries its full proposition

Wave directive (same as R6/R7): *"have the jabberwock close the python blind
spot residuals"* — this wave closes the FINAL two named residuals, R8 and R9,
by the SAME philosophy as Wave A (commit 7980f4e1f6): the DECISION lands in
graph data or a mechanical readback of the reader's own output; Python only
plumbs; jurisdiction is proven by ablation (`remove_rule` reverts behaviour).

**R8 — reform components now reach the SmEntity situation model (DONE,
`seeds/reading_reform_ingest.json` v1.0.0).** The dynamic-thresholds/reform
wave (401ea41a5d) deliberately deferred re-ingesting a reform's decomposed
`part_of`/marker component predications into the situation model — they only
ever landed on the `SentenceParse` node's own `reform_predications` JSON
attr. Migration shape: the SAME two-stage pending/done handoff
`reform_overcomplex_clause`/`_execute_pending_reforms` already use, one
stage further down the pipeline. The rule `ingest_reform_components` DECIDES
a completed reform's components (`reform_done=1`) belong in the model,
marking `reform_ingest_pending=1`; the mechanical executor
(`reading_drive._execute_pending_reform_ingests`, run both opportunistically
inline in `_shim_monitoring` and via the ALWAYS-ON `reform_ingest_reflex` —
the SAME "the rule can't fire before Python writes the precondition, so the
FIRST opportunistic call can never catch its own just-completed reform"
race `reform_reflex` already documents one stage up) mints REAL graph
structure: a `part_of` predication becomes a real `part_of` EDGE between two
`SmEntity` nodes via the EXISTING `inference_generation._mint_part_of`
mechanical idiom (reused verbatim — `part_of` is not a change-of-state verb
`situation_model_reader.ingest_predication` would otherwise act on), stamped
`from_reform=1` on the part entity for provenance; any other reform
predication goes through `situation_model_reader.ingest_predication`
directly. Guarded by `reform_ingested` (the `kin_monitored`/`reform_done`
exactly-once idiom applied one level up).

**A real regression was caught by the broad bench and fixed en route:** the
first cut routed non-part_of components through `coref_entities.
resolve_and_ingest` — which re-runs `_touch_entity`'s mention-count/recency
bookkeeping over a sentence whose order-1 predications the live spine had
ALREADY counted once, double-counting salience. Measured effect: 'The
Travelling Musicians' protagonist derivation flipped from 'dog' to 'robbers'
(`test_bridging_anaphora_migrated::test_tm_antagonist_decided_by_opposition`
red; attribution proven by an ablation arm — rule removed ⇒ dog/robbers/
opposition restored). The fix: non-part_of components ingest via
`situation_model_reader.ingest_predication` (structure only — property attrs
/ eventive mints — no coref bookkeeping); the re-ingest is about the
STRUCTURE the reform recovered, never a second count of the same mentions.
Suite green after the fix with the rule ACTIVE.

The feared "double-ingest against the once-per-sentence monitoring guard"
turned out to be a NON-ISSUE once the guard's actual shape was read
(the task's own instruction): `_shim_monitoring`'s `kin_monitored` loop
reads a SentenceParse's `resolved_predications` attr ONLY — `reform_
predications` is a completely separate attr the kinship scan never touches
— so re-ingesting a reform's components can structurally never re-trigger or
duplicate that scan. No new guard machinery was needed beyond `reform_
ingested` itself.

`substrate/world_adapter.py::_mint_document_held_answers` (mechanical host
I/O, sanctioned) was extended to ALSO read a flow's `from_reform=1` SmEntity
part_of EDGES (the real situation-model structure, not the parse's `reform_
predications` JSON) into its held-answer text, so "What do you know about
the device?" now names its parts.

Gates: `tests/test_reform_reingest_migrated.py` (7: real part_of edges mint
+ are provenance-stamped, exactly-once re-run, the kin_monitored guard
proven untouched — both the guard count AND `resolved_predications` byte-
unchanged, the device-sentence document-QA closure proof, ablation-reverts
proof, seed structure/canon round-trip, idempotent boot).

**R9 — a modeled Level-2 belief/goal carries the FULL proposition, not just
its head (DONE, `seeds/proposition_capture.json` v1.0.0).** `character_tom`'s
nested belief-world/goal grounding (reused verbatim by the interlocutor's own
Level-2 attitude ingest, `substrate/world_adapter.py`'s attitude-ingest
block) only ever kept the complement predication's HEAD argument as
`referent` ("I think the new scheduler is faster" → `referent=
'new_scheduler'`), even though the reader's own `read_clause` call already
produced the FULL triple (`['is_a', 'new_scheduler', 'faster']`) right there.
`reflective_faculty._run_interlocutor_model` rendered from that head alone —
"I model you as likely believing new_scheduler."

Migration shape: `_nested_entity`/`_ground_attitude_complement` mechanically
stamp the ALREADY-COMPUTED full predication (`proposition`, json) and the
complement's verbatim span (`proposition_span` — "the new scheduler is
faster", never DET-stripped/underscored like the head-grain `referent`) onto
the Level-2 node, unconditionally — the SAME mechanical-mint discipline
`situation_model_reader.ingest_predication` already uses for every other
node attr; nothing here is a Python DECISION, it is fuller plumbing of data
the reader's own (already rule-decided) clause parse produced. The DECISION
surface — whether a Level-2 node's fuller data is ELIGIBLE for rendering —
is a genuine graph rule, `mark_attitude_proposition_capture`
(`seeds/proposition_capture.json`), matched via a fresh `is_attitude_level2`
self-edge (the SAME single-node self-match idiom `situation_model_reader.
_entity`'s `is_entity` / `reading_drive`'s `is_sentence_parse` already use,
stamped on BOTH the belief/knowledge SmEntity and the desire SmEvent at
mint time — one rule covers both attitude flavors): it flags a node carrying
`proposition_span` with `proposition_capture=1`. `_run_interlocutor_model`
prefers `proposition_span` ONLY when `proposition_capture==1`, falling back
to the pre-closure head-grain `referent`/`idx_intentionality`/`goal` fields
otherwise — so ablating the rule reverts EVERY render to the old head-grain
text even though the richer data is still sitting on the node, proving the
decision genuinely lives in the rule.

The head-grain `referent`/`idx_intentionality`/`goal` fields are UNCHANGED
(every existing reader of them — `character_belief_world`, `character_goal`,
the desire-flavor render fallback — is byte-identical); the new attrs are
purely additive. The narrative `character_tom.py` reading path (`tests/
test_character_tom.py`, 18 legacy cases) keeps its existing head-grain
`character_belief_world`/`character_goal` semantics — it gains the SAME
richer attrs on its nested nodes (lower-risk: additive-only, chosen over
also rewriting its own render, which nothing in that suite currently needs)
but nothing in that suite reads or depends on them.

Gates: `tests/test_proposition_beliefs_migrated.py` (9: belief + desire
Level-2 nodes carry the full proposition, the render uses the full
proposition instead of the head, a live daemon-shaped transcript proof,
hedged-confidence-math parity, the narrative Sally-Anne reading spot-check
unaffected, ablation-reverts proof, seed structure/canon round-trip,
idempotent boot). `tests/test_interlocutor_modeling_migrated.py` (24) and
`tests/test_character_tom.py` (18) both green unmodified — no existing test
in either suite asserts exact `belief_world_state`/attr-set equality or the
OLD head-grain render text verbatim, so the enrichment is purely additive
from their point of view.

**Jurisdiction proof (both, the ablation-gate discipline Wave A established):**
each closure's decision is a live, named, `remove_rule`-able Rule — removing
`ingest_reform_components` (R8) leaves the reform itself untouched (a
DIFFERENT, unablated rule) but nothing is re-ingested into the situation
model; removing `mark_attitude_proposition_capture` (R9) leaves the fuller
mechanical mint untouched (the data is still on the node) but the render
reverts to head-grain. Both surfaces are ordinary seed-resident Rules inside
the Experiment→judge→adopt spine's reach — no `comprehend_text.py` edit,
no new Python decision, in either closure.

**This closes the burn-down list this wave opened:** R6 + R7 (Wave A) + R8 +
R9 (this wave) are the four Python blind-spot residuals named for this
initiative; all four are DONE.

## 7. R10 — the rung-4 join index (2026-07-12): the mention→concept equality
join is O(1) per mention; the matcher takes declarative index hints

Wave directive: *"have the jabberwock do the rung 4 join index."* R10 is the
Wave-3 latency residual named above (section: "Latency lever"): `rule_mention_
resolves_to_concept`'s match pattern — `(agent, knows_concept, c)` ×
`(m, has_mention, mention)` — shares NO variable between its two match-edges;
only the where-clause `Eq(Attr(mention,"text"), Attr(c,"name"))` connects
them, and the matcher (`rewrite.rs::extend_each`) evaluates the where-clause
only AFTER fully enumerating each edge's candidates, so the rule paid the full
held-Concepts × accumulated-Mentions cartesian product on every `run_rules`
pass, growing with conversation length.

**Measured before (full-seed shadow agent, 20-turn battery,
`scripts/rule_join_profile.py`):** the rule's per-pass cost grew 845µs
(7 mentions) → 15,430µs (159 mentions) — >20× the next-most-expensive rule —
with steady-state shadow latency ~55.4ms avg and climbing. **After:** 30µs →
106µs over the same battery (~146× cheaper at turn 19, and now O(mentions)
flat instead of O(concepts×mentions)); the rule dropped OUT of the top-8
rule_costs() entirely; steady-state shadow ~46.6ms avg and flat. The agent's
own `comprehension_health` HealthNorm (ceiling 50ms on
`shadow_latency_recent_avg`): before, the 20-turn rolling average never
returned under the ceiling (55–58ms steady, climbing); after, once the
cold-start turn rolls out of the window the rolling average sits at ~49.5ms —
under the agent's held ceiling by its own senses.

**The agent's attempt first (the honest boundary).** Its
`performance_self_improvement` Programs read the measured shape correctly:
`perf_diagnose` returned `per-item` (cost ∝ items, not one-time init — ratio
0.05, far under RATIO=50) and `perf_fix_pick` selected `optimize-op`. But
`optimize-op`'s enactment is an honest specified-boundary stub, and the
rung-4 authoring surface (`RustExtensionSpec` semantic-kind templates →
`ALLOWED_INSTALL_FILES` = term.rs/jsonio.rs/reflect.rs/py.rs/shape.rs) can
only add TERM primitives — and a Term cannot intercept this cost: the join
lives in the MATCH phase, before any Term evaluates. Nor can the rule be
re-expressed to move the join into where/effects Term territory:
`Effect::AddEdge`'s src/tgt are match-VARIABLE names only (`parse_effect_json`,
py.rs) — an effect cannot target a Term-computed node, so "match only the
mention; compute the concept with `NodesWhere`" has no legal effect to bind
it. The engine-side matcher change therefore exceeded rung-4's write surface
BY CONSTRUCTION and was done by human hands under the user's directive —
`ALLOWED_INSTALL_FILES` was NOT widened (pinned by
`tests/test_join_index_migrated.py::test_allowed_install_files_not_widened`).

**The fix (engine, `rewrite.rs` + `substrate.rs` + py.rs wire format):**
- `IndexJoinHint { for_var, via_var, via_key, node_type, this_key }` — a
  declarative per-rule hint (new optional `"index_hints"` key in the rule
  JSON dialect; absent → empty → byte-identical behaviour for every
  pre-existing rule). Round-trips through `rule_to_json`/`parse_rule_json`.
- `hinted_candidates` (rewrite.rs): in the both-unbound match-edge case, if
  a hint's `via_var` is bound and the `(node_type, this_key)` attr index is
  declared, candidates come from `graph.nodes_where(node_type, this_key,
  via.attrs[via_key])` — INDEX-THEN-VERIFY (every hit is confirmed against
  the real edge via `in_neighbours`/`neighbours`), so a stale/absent/wrong
  index can only WIDEN the search back to the original scan, never fabricate
  a match. No epoch machinery needed: `TypedGraph`'s attr indices are
  incrementally maintained on every insert/set_attr/delete (graph.rs), so
  the conservative invalidation the mission asked for is the existing
  always-fresh index.
- `reorder_match_edges_with_hints` (rewrite.rs) + `add_rule` (substrate.rs):
  hint-aware install-time reorder guarantees the `via_var`-binding edge is
  scheduled before the hinted edge, and `add_rule` auto-declares the hint's
  attr index (idempotent), so a hinted seed rule is self-contained.
- `seeds/intent.json`: `rule_mention_resolves_to_concept` carries the ONE
  hint (`for_var:"c", via_var:"mention", via_key:"text", node_type:"Concept",
  this_key:"name"`). Match/where/effects are UNCHANGED — resolution
  behaviour byte-identical (gated).

Gates: `tests/test_join_index_migrated.py` (5: mid-conversation Concept add
resolves immediately; removed Concept immediately ungroundable — live index
under mutation; hinted-vs-unhinted rule swap + revert via the same
export_rules/remove_rule/add_rule primitive `perform_adoptions` uses, with
byte-identical resolution on a mixed fixture; ~30× latency separation at
150×150 scale; ALLOWED_INSTALL_FILES unchanged). Rust unit tests
(rewrite.rs): hinted join parity with the unindexed matcher, fallback-when-
undeclared, no-false-positive, hint-aware reorder, add_rule auto-declare.
Conversation batteries green post-change (interlocutor 24, instruction_gap,
nl_steering, speech_act_parity, full_turn, qa, topic_route, topic_span,
shadow_read: 94 passed).

Honest residuals: (a) the hint is authored seed data, not yet something the
agent MINTS for other disjoint-join rules it might diagnose (the
`IndexJoinHint` wire format is rule JSON, so a future graph-authored variant
CAN carry one — the vocabulary is in its reach; the diagnosis-to-hint
composer is not built); (b) `run_rules` still has no per-rule family scoping
(the OTHER half of the Wave-3 residual) — the join index removed the
dominant cost, scoping remains unbuilt; (c) `rule_costs()` reports per rule
SLOT, so a name shared by a tombstoned and a live slot needs summing
(documented in the gate's `_rule_us`).
