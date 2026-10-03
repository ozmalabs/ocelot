# EQUILIBRIUM BEHAVIOURAL QUANTA — DESIGN (stream T3b: quanta, competence, episodes, cue recognition on the comprehension base)

**Date:** 2026-10-02. **Status: DESIGN DRAFT.** Worktree `/home/matt/ozmadev/ocelot/.worktrees/t3b`, branch `t3b/behavioural-quanta`, based on `t3/classifier-sidecar` @ `2aefc943` ("Equilibrium seed pack 0.2.0"). Companion PREREG: [`EQUILIBRIUM_BEHAVIOURAL_QUANTA_PREREG_20261002.md`](EQUILIBRIUM_BEHAVIOURAL_QUANTA_PREREG_20261002.md). Predecessors: [`EQUILIBRIUM_SEED_PACK_V0_DESIGN_20261002.md`](EQUILIBRIUM_SEED_PACK_V0_DESIGN_20261002.md), [`EQUILIBRIUM_SEED_PACK_V0_SLICE1_RESULTS_20261002.md`](EQUILIBRIUM_SEED_PACK_V0_SLICE1_RESULTS_20261002.md). Not merged and not pushed.

**This design supersedes v0 DESIGN §1.2 (fixed `pat.*` person labels) and §4.2 (the old `/v1/discourse` sketch).** The contract in §3 is the shared contract and is authoritative for both repos.

## 0. Purpose and the user decision

User decision (authoritative): *"Person labels should be normalised to behavioural quanta and should be arbitrary and dynamic and combinatory — a series of traits, not a fixed point. The classification and competence needs to move to a proper Ocelot base in a dedicated stream along with cue matching. This is the whole point of Ocelot."*

The stream does four things:

1. **Fixed person labels become behavioural quanta.** A quantum is an observed, evidence-backed statement of the form "within this window, actor X displayed trait T with polarity ±". It lists its evidence and counter-evidence turns. Quanta are:
   - **arbitrary/open**: traits are dotted lowercase codes from a versioned seed vocabulary that grows through `teach`, not an enum in code;
   - **dynamic**: quanta are scoped to a window and recomputed on every request. There is no persistent person state in Ocelot;
   - **combinatory**: a person is described by a *set* of quanta. Composite traits are defined in the codebook as conjunctions of component quanta, never as a single score.
2. **Competence moves into Ocelot** as relational quanta: claimed (status/credential/assertion-strength cues) versus demonstrated (grounding evidence) versus acknowledged (other actors concede to or cite the actor), plus corroboration inside the window. There is no single competence score.
3. **Dispute etiology moves into Ocelot.** Episodes are read out with facets (epistemic, status, procedural, affective, tribal) computed as graph patterns over the episode's turns, plus a `generative` flag.
4. **Cue recognition moves off flat n-gram `EqCue` matching** onto the comprehension base wherever machinery exists (§5). Lemma and WordNet class membership, negation/modality scope, speech-act kind, reply-pair coherence relations and claim/evidence structure replace exact token-form equality. What stays lexical is stated explicitly in §5.4.

Equilibrium consumes the output. It does **no** content classification, no categorisation of people, and no regexes or lexicons for labels. It only gates by label status, stores the evidence references, and presents the results.

## 1. Binding constraints

| Source | Constraint as applied here |
|---|---|
| CLAUDE.md:36-41, 106-120 | The Python adapter only INGESTs (a mechanical external→graph translation with no conditionals over graph state) and EMITs (a pure query). Every decision is a seed rule inside `run_rules`. |
| CLAUDE.md:122-125 | Only thin I/O-boundary token classifiers are allowed, and only where no Rust primitive exists (e.g. tokeniser span regexes, `endswith("?")`). §5.5 lists each one and justifies it. |
| CLAUDE.md:129-149 | Forbidden: `recognise_X`/`decide_Z` helpers, Python dicts of agent state, and Python if/else over graph state. Python cue sets were reverted as agent logic (684-698). |
| CLAUDE.md:152-165 | Missing expressiveness is a Rust Term plus a PyO3 one-liner ("primitive in Rust, composition in graph"). |
| CLAUDE.md:167-251, 328-346 | Seeds are versioned manifests minted via `teach(agent, type, attrs, category=...)`. `_compose_*`/builder scripts are legal **only** because they assemble Rule JSON. |
| CLAUDE.md:684 | A baseline or evidence set is a **list of node ids, never a count**. Quanta carry turn-id lists. |
| CLAUDE.md:944-1015 | SHAPES not numbers. There are no invented rates, floors, thresholds or weights, and no `1/n` learners. Every comparison is relational between two graph quantities (§6). |
| R11 / `OZMA_NO_LLM=1` | No LLM path may be reachable. `language_world.teacher_via_claude` (209) must not be imported on the request path. `teacher_stub` (340) is the only teacher, and only at build time. |
| Privacy | Synthetic data and pseudonyms only (`actor_a`, `expert_e`, `member_###`). Text never leaves the fork. Errors never echo input. |

## 2. Architecture (unchanged service shape)

The service shape is the same as `/v1/classify` (`services/equilibrium_classifier/server.py:217-299`):

```
boot once:   base = ec.boot()               # boot_core(PACK_IDS + new packs)
             snap = base.snapshot(); rev0 = snap.source_revision
per request: lock; assert snap.source_revision == rev0   # drift guard
             branch = snap.fork()
             ec.ingest_window(branch, req)            # mechanical (§4)
             steps = branch.run_rules(DISCOURSE_FUEL)  # the whole decision
             out = ec.read_discourse(branch, req)      # pure query (§7)
             del branch; unlock
             every STRONG_CHECK_EVERY: strong_digest(base) == digest0
```

- One request equals one window equals one fork. Nothing a window computes persists. Cross-window aggregation is the consumer's job over the returned id lists (§8.4).
- `DISCOURSE_FUEL` is a fuel cap (an engine resource bound, like `ShapeDecode.budget`), not a decision parameter. If `run_rules` returns with the fuel exhausted, the response is the error `{code:"budget_exhausted", retryable:false}`. A truncated fixpoint is never emitted as if it were complete. The value is set from the PREREG throughput measurement on synthetic 500-turn windows (PREREG P6), not tuned against labels.

## 3. HTTP contract — `POST /v1/discourse` (shared; must match Equilibrium exactly)

This is a POST on the loopback sidecar.

```
request  {"taxonomy_version"?: str, "window": {"window_id": str, "kind": "meeting"|"thread"}, "turns": [{"id": str, "actor_ref": str, "text": str, "reply_to"?: str|null, "ts_ms"?: int}]}  (<= 500 turns)
response {"ok": true, "taxonomy_version": str, "window_id": str,
  "messages": [<same per-message label objects as /v1/classify>],
  "quanta": [{"actor_ref": str, "trait": str (dotted lowercase code, open vocabulary), "polarity": "+"|"-", "match": "exact"|"partial"|"weak", "evidence": [turn ids], "counter_evidence": [turn ids], "target_ref"?: str, "rule_ids": [str]}],
  "episodes": [{"episode_id": str, "kind": str, "actor_refs": [str], "turns": [turn ids], "facets": [{"code": str, "match": "exact"|"partial"|"weak"}], "generative": bool|null, "rule_ids": [str]}]}
```

Rule ids use the client's format `name:<pack_version>` (no `@`). Errors are `{ok:false, error:{code, message, retryable}}` and never echo the input.

Server-side validation adds no semantics beyond the contract. All of it is mechanical schema checks before any fork:

- `taxonomy_version`, if present, must equal the pack's. Otherwise return 409 `taxonomy_mismatch` (same as `/v1/classify`).
- More than 500 turns, or an empty `turns`, returns 413 / 400 `bad_request`.
- Duplicate turn `id` returns 400 `bad_request`.
- A `reply_to` that names an id not in the window is **kept as a dangling reference**. It ingests as `Message{eq_reply_to_ref}` with no edge. The reply target is outside the window, and that is ordinary for threads, so it is not an error.
- `window.kind` outside the enum returns 400.
- Turns are taken **in array order as time order**. `ts_ms` is stored as an attribute and never used to re-sort. The client is responsible for ordering. This keeps ingest free of conditionals (§4).
- `messages[]` is byte-identical in shape to `/v1/classify` items for the same text. It reuses `to_wire` (server.py:134-153).
- `quanta[]` and `episodes[]` are ordered deterministically (§7.3). An empty list is a valid answer and is the expected one for windows with no cues.
- Error codes: `bad_request`, `taxonomy_mismatch`, `too_large`, `budget_exhausted`, `base_drift` (retryable:false; the service then refuses all requests), `busy` (retryable:true).

`GET /v1/info` changes `"/v1/discourse": "not_implemented"` (server.py:297) to `"ok"`. It adds `trait_status: {trait_code: status}`, `episode_kind_status` and `facet_codes`, all read from `LabelStatus` nodes (§9).

## 4. Window ingestion on the fork (mechanical)

`ec.ingest_window(branch, req)` extends `_ingest` (equilibrium_classify.py:84-107). Every line is an unconditional translation of request fields into nodes and edges. There is no branch on graph state.

| Graph item | From |
|---|---|
| `Window{window_id, eq_kind}` and `agent -eq_window-> Window` | `req.window` |
| `Actor{actor_ref}`, one per distinct `actor_ref`, plus `Window -eq_has_actor-> Actor` | turn `actor_ref` (dedup by string key is a mechanical id map, not a decision) |
| `Message{eq_ref=id, eq_turn_pos=i, ts_ms?, eq_reply_to_ref?}` with the existing `sak_*` signals, `CodeSpan`/`LinkSpan`, `Token` chain | turn *i*, exactly as `_ingest` does today |
| `Window -eq_has_turn-> Message` and `Message -eq_authored_by-> Actor` | turn |
| `Message -eq_reply_to-> Message` | `reply_to`, when the target id is in the window |
| `Message -eq_turn_next-> Message` | consecutive array positions (mirrors `eq_next` for tokens) |
| `Token{form, lemma, wn_lex?, eq_pos, eq_class}` | §5.5 boundary tokens (lemma and lexname are new attrs) |

Derived structure is **rule-minted**, not ingested:

- the "same actor's next turn" chain;
- `eq_addresses` (turn → actor addressed, via `reply_to`'s author);
- negation/modality scope edges;
- coherence relations;
- evidence edges.

This keeps the adapter thin and puts every derivation under rule ids that appear in the output.

`eq_turn_pos` is an integer *position*, not a measure. It exists so "later in the window" is a relational comparison `Gt(Attr(m2, eq_turn_pos), Attr(m1, eq_turn_pos))` between two graph values. This avoids minting the O(n²) transitive `eq_after` closure (125k edges at 500 turns).

## 5. Cue recognition on the comprehension base

### 5.1 What exists and is reused

| Machinery (from the brief) | Used for | How |
|---|---|---|
| `seeds/speech_act_classify.json` (`sak_kind_*`) over `kind_signals` ingest attrs | per-turn act (question/instruction/statement) | already in `/v1/classify`. Becomes the act layer for episodes and responsiveness. |
| WordNet lexname membership (`situation_model_reader._verb_lexname` 141, `cos_membership` 178, `eventive_membership` 159; `lexical_ontology_roots.json`) | class cues instead of word lists | `Token.wn_lex` at ingest (§5.5). Cue rules match `Attr(t, wn_lex) == <class>` from codebook nodes, e.g. `noun.person` for credential heads, `verb.communication` for citation verbs, `noun.group` for tribal collectives, `verb.cognition` for epistemic stance. |
| Lemma (`dictionary_lexicon._lemmatize` 403 / `_spacy_lemma` 433) | inflection-free matching | `Token.lemma`. Every `EqCue` word slot matches `lemma`, not `form`, unless the cue declares `match_on: form` (§5.4). |
| `seeds/coherence_relations.json` (8 `ShapeSignatureCoherence`, 5 `MarkerClass`) and `discourse_coherence` | reply-pair relations: contrast, concession, cause, elaboration, sequence | see §5.3: it is rule-driven on (parent, reply) pairs, not called from Python. |
| `seeds/discourse_argument.json` (`classify_rst`, `classify_argument`) | claim/evidence/warrant roles per turn | a claim/evidence role becomes the competence and epistemic-facet substrate (WI-7; verification needed that it fires on `Message` nodes). |
| `ShapeDecode` Term (term.rs:1638) and `seeds/shape_decode_loop.json` (`sd_decode`, `sd_recognize*`, `sd_mint_quantum`, `sd_dedup_existing`, `sd_redecode`) | episode skeleton decoding against an episode-kind codebook, with residual mint | §8.3 |
| `add_node_if_absent` effect (graph_rules.rs:260-276) | exactly one `EqQuantum` per (actor, trait, polarity[, target]) and one `EqEpisode` per root | §6 |

### 5.2 Negation and modality scope (new seeds; no Rust needed for v1)

The brief found **no negation-scope primitive** in the rule path. The design adds it graph-natively as closed-class codebook nodes plus scope propagation to fixpoint.

- **Codebook (taught, `category="equilibrium_scope"`):**
  - `EqScopeOp{op:"neg", lemma}` for negators (not, n't, never, no, nobody, nothing, neither, nor, without);
  - `EqScopeOp{op:"modal", lemma, force:"epistemic"|"deontic"}` for might, may, could, perhaps, probably, should, must, ought, …;
  - `EqScopeOp{op:"hedge", lemma}`;
  - `EqScopeBoundary{lemma|eq_class}` for clause boundaries: sentence punctuation, `but`, `although`, `however`, and the `DISC_CONTRAST` members of `MarkerClass`.
- **Rules:**
  - `eq.scope.open.<op>`: `[t lemma ∈ EqScopeOp][t eq_next u]` → `u -eq_in_scope-> t` with `{op}`.
  - `eq.scope.extend`: `[u eq_in_scope s][u eq_next v]`, `Not Exists(v matches EqScopeBoundary)` → `v -eq_in_scope-> s`.
  - The `run_rules` fixpoint is the closure. It is bounded by clause length, so there is no window-wide blow-up.
- **Use in cue rules:**
  - A cue match whose head token is in `neg` scope **does not fire the cue**. It fires `eqfire:<cue>.negated` instead. The trait codebook decides what that means: counter-evidence for the + pole, and evidence for the − pole only when the trait declares a `negated_pole` (§8.1). Example: "I'm not a doctor" is not `status.claim`. It is counter-evidence for it.
  - A head in `modal`/`hedge` scope fires `eqfire:<cue>.hedged`. Hedged evidence caps the quantum's `match` at `partial` (§6.2) and is evidence for `epistemic.hedging`.
  - Double negation (a negator inside the scope of another negator) is **not resolved** in v1. Such a cue emits `.negated` from the innermost operator only. This is a documented limitation, tested as a golden *expected-limitation* case (PREREG G5).
- Typed modal/permission frames from `comprehend_text` (713-740, `modality_evidence`) are a better source than the closed list. They are used where `kind_signals` already returns them. Adding them as `Token`/`Message` attrs is WI-3b and needs verification.

### 5.3 Reply-pair coherence as rules, not a Python pre-pass

`discourse_coherence` is Python-orchestrated and works per text (`_leading_marker` 170, `_decode` 248). Calling `coherence_between` from the adapter would be a Python decision. Instead:

- `eq.coh.marked.<rel>`: `[m eq_reply_to p][m first-token t][t lemma ∈ MarkerClass(rel)]` → `m -eq_coh-> p {rel}`. This uses the same `MarkerClass` nodes `coherence_relations.json` already seeds. It is a `depends_on`, not a copy.
- `eq.coh.unmarked`: a `ShapeDecode` Term in the rule's `where`/effect over `ShapeSignatureCoherence` with the (p, m) skeleton as goal. Whether ShapeDecode accepts a two-message skeleton built from `Token`/`Message` nodes is **unverified** (WI-4 spike). If not, v1 ships marked relations only and says so. No Python fallback is added.
- Rule-minted `eq_coh {rel: contrast|concession|cause|elaboration|sequence}` edges are the substrate for episodes (§8.3) and for `stance.concession` (the reply concedes to its parent).

### 5.4 What stays lexical, and why

Lexical matching (lemma or form equality against taught `EqCue` nodes) stays only where the meaning is carried by closed-class or non-compositional forms, so class membership would over-generate:

1. **Closed-class operators:** negators, modals, hedges, boosters ("clearly", "obviously"), discourse connectives, deictic and person pronouns (I/we/you/they for tribal and addressing cues). These are finite and language-specific by nature. WordNet does not cover function words.
2. **Non-compositional formulae and idioms:** "with all due respect", "fair point", "my bad", "no offence but", "do your own research", "just asking questions". Their pragmatic force is not a function of their parts. They match on `form` sequences (the current `cue_rules` n-gram shape, kept as one cue *kind* among several).
3. **Surface-format spans at the I/O boundary:** code blocks, inline code, URLs, DOIs, `[n]` citation brackets (the existing `_spans` tokenisers, equilibrium_classify.py:37-41). This is format, not meaning.
4. **Emoji senses** (v0 §1.4), until an emoji→sense membership seed exists.

Everything else becomes **lemma + class** or **structure**:

- credential heads (`noun.person` lexname in a first-person copular/possessive frame);
- citation verbs (`verb.communication` + `LinkSpan`/citation span in the same turn);
- epistemic verbs (`verb.cognition`);
- collectives (`noun.group`);
- concession and contrast (`eq_coh` relations rather than phrase lists).

All lexical items stay **seed data** (`EqCue`/`EqScopeOp` nodes via `teach`). None live in Python and none live in Equilibrium. The `LEXICON` list in `build_equilibrium_seed_pack.py` (113+) moves to a teach-manifest input file read by the builder (WI-2). The builder still only assembles Rule JSON and calls `teach`.

### 5.5 New I/O-boundary tokens (judgement calls, flagged)

| Token attr | Source | Why admissible (CLAUDE.md:122-125) | Risk |
|---|---|---|---|
| `Token.lemma` | `dictionary_lexicon._lemmatize` / `language_world._lemmatize` (no spaCy on the request path unless already loaded at boot) | It is opaque string normalisation to the smallest graph token, and no Rust lemmatiser exists. | It is a judgement call. A reviewer may require a Rust Term. Fallback: lemma = lowercased form, recorded in `/v1/info`. |
| `Token.wn_lex` | first-sense WordNet lexname (`situation_model_reader._verb_lexname` idiom, extended to nouns) | It is a lookup, not a decision. Sense choice is first-sense, not `pick_sense` (Lesk is a disambiguation decision and is excluded). | First-sense bias. This is a fairness risk for dialect and jargon (§10). |

No other new ingest attrs are added. Everything else is rule-derived.

## 6. Quanta: graph-native construction and SHAPES-not-numbers

### 6.1 Construction (one generic rule family, data-driven)

- **Trait codebook nodes (taught, `category="equilibrium_traits"`):**
  - `EqTrait{trait:"competence.claimed", poles:"+", negated_pole?, targetable:bool, status_ref}`;
  - `EqTraitCue{trait, pole:"+"|"-", fires:"<eqfire label>", role:"evidence"|"counter"|"hedged"}` (many per trait);
  - `EqTraitCompose{trait, requires:[trait:pole,...], same_target:bool}` for combinatory traits.
- **Evidence rule** `eq.quanta.evidence`, **one** rule for all traits. It matches `[m eq_authored_by a][m has eqfire:<f>][EqTraitCue c][Attr(c,fires)==f]` and runs `add_node_if_absent q EqQuantum{actor:a.actor_ref, trait:c.trait, pole:c.pole[, target]}`, `a -eq_has_quantum-> q`, `q -eq_evidence|eq_counter|eq_hedged-> m` (by `c.role`). New traits need **no rule change**, only codebook nodes.
- **Target** `target_ref`: for `targetable` traits the rule also binds `[m eq_reply_to p][p eq_authored_by b]`, and the dedup key includes `b`. Without a reply edge, the quantum is untargeted. Second-person address without `reply_to` does **not** infer a target in v1.
- **Counter-evidence for the + pole from the − pole and vice versa.** The rule `eq.quanta.cross_pole` links each `-` evidence edge as an `eq_counter` edge on the same actor's `+` quantum when that quantum exists. A − quantum is emitted only for traits whose `poles` include `-`.
- **Composites** `eq.quanta.compose`: when every `requires` component quantum exists for the same actor (and the same target if `same_target`), it mints the composite quantum. Its evidence is the union of the components' evidence edges. Composite `match` is the weakest component `match` (`MinOver` over an ordinal shape node, §6.2). This is how "a series of traits" composes into a pattern without a fixed label.
- **Rule ids:** each quantum collects `eq_by_rule` edges to the rule nodes that fired for it. The cue rule, the scope rules that altered it, the evidence rule and compose all appear. On the wire they become `wire_rule_id(name@0.3.0)` → `name:0.3.0` (server.py:128-131).

### 6.2 `match` as a shape (no thresholds)

`match` is decided by rules over the quantum's own evidence sets. Every comparison is relational between two graph-derived quantities, or is presence/absence. Let E = evidence turns, C = counter turns, H = hedged turns, and |·| = `Count(Neighbours(q, edge))` over *distinct* `Message` nodes.

| `match` | Shape (all conditions are graph-relational) | Rule |
|---|---|---|
| `exact` | `Exists(E)` ∧ `Not Exists(C)` ∧ `Not Exists(H)` ∧ E spans **more than one turn** (`Gt(Count(E), Count({first(E)}))`, i.e. a set strictly larger than its own singleton) | `eq.quanta.match.exact` |
| `partial` | `Exists(E)` ∧ `Gt(Count(E), Count(C))` and not exact (hedged evidence, or outweighed counter-evidence, or both) | `eq.quanta.match.partial` |
| `weak` | `Exists(E)` and neither of the above: a single-turn act, or `Count(E)` not greater than `Count(C)` | `eq.quanta.match.weak` |

- The singleton-versus-plural distinction is a **set-cardinality shape**, not a tuned floor. One act is an act. A repeated act within the window is a pattern. This follows `psy_personality.personality_predicts_aggregated_behaviour_not_individual_acts`. The PREREG seals it: it may not be moved to "≥3" after seeing data.
- `E` versus `C` is a comparison of two graph quantities. There is no ratio and no cutoff.
- A quantum where `Count(C) > Count(E)` is still emitted as `weak`, so the consumer sees the contested evidence. Suppression would be a hidden decision.
- The ordinal `exact > partial > weak` is itself a 3-node `EqMatchShape` chain in the seed (`eq_stronger_than` edges), so `MinOver` for composites reads graph order and not Python order.

### 6.3 Relational comparisons for interaction traits

| Trait | Shape |
|---|---|
| `interaction.floor` ("held the floor") | `Argmax` over the window's actors of `Count(InNeighbours(a, eq_authored_by))` (the `u0_choose` / `most_central` idiom). The quantum is minted only for the unique argmax. Evidence = that actor's turns. Counter = the next actor's turns. A tie yields no quantum. **Argmax tie semantics are unverified** (WI-5). If Argmax picks arbitrarily on ties, the rule adds `Not Exists(b ≠ a with Count equal)`. |
| `interaction.run` (consecutive turns) | rule-minted `eq_same_actor_next` where `eq_turn_next` joins turns by the same actor. Evidence = turns in a run whose own predecessor is the same actor. No length threshold: `match` follows §6.2. |
| `interaction.responsiveness` (−: selective non-response) | Question turn q (sak kind question) with `q eq_reply_to p`, `p eq_authored_by a`. Actor a authored a turn m with `Gt(m.eq_turn_pos, q.eq_turn_pos)`, and `Not Exists` a turn by a with `eq_reply_to q`. Evidence = q, counter = any later a-turn replying to q. **Absence is relational to the actor's own later activity**, so an actor who left the window is not marked. |
| `competence.corroborated` ("claim corroborated later in the window") | claim turn m1 ∈ E(`competence.claimed`) of a, and `Exists` m2 by b ≠ a with `Gt(m2.pos, m1.pos)` and (`m2 eq_coh m1 {concession}`, or m2 fires `epistemic.citation` replying to m1, or m2 fires `deference.to` targeting a). Evidence = {m1, m2}. |
| `epistemic.question_demand` (repeat) | question turns by a replying to b whose parent chain already contains a b-turn with a citation/link span. "After answered" is `Gt(pos)` plus `Exists`. |

## 7. Read-out (pure query)

### 7.1 Messages

`messages[]` is the existing `_read` per `Message` (equilibrium_classify.py:116-133), passed through `to_wire`.

### 7.2 Quanta and episodes

For each `EqQuantum` node the read-out emits `actor_ref`, `trait`, `polarity`, `match` (from its `eq_match` attr), `evidence`/`counter_evidence` as the sorted `eq_ref` of the linked `Message` nodes, `target_ref?`, and `rule_ids`. Hedged turns are reported inside `evidence`. `match` already encodes them, and the contract has no hedged field.

Status filtering is a lookup, not a decision. A quantum whose trait's `LabelStatus` is `disabled` has its evidence rule gated *in the graph*: `eq.quanta.evidence` requires `Not Exists(EqTrait -eq_has_label_status-> disabled)`, so a disabled quantum is never minted. The read-out emits everything that exists.

### 7.3 Determinism

- Lists are sorted by `(actor_ref, trait, polarity, target_ref)` for quanta and by first-turn position for episodes.
- Evidence lists are sorted by `eq_turn_pos`.
- `episode_id = "ep:" + window_id + ":" + <root turn id>`, so it is stable under re-run.
- The output is a function of the request only (PREREG P4).

## 8. Trait vocabulary, competence, episodes

### 8.1 Initial trait seed vocabulary (`equilibrium_traits` manifest v0.3.0, open)

Codes are `<family>.<trait>[.<sub>]`, dotted lowercase. **All ship `shadow`.** `pattern.*` composites ship `disabled`.

| Trait | Poles | Evidence (cue level, §5) | Notes |
|---|---|---|---|
| `competence.claimed` | + | credential frame (1st person + copula/possessive + `noun.person`/occupation class), experience claims, assertion boosters | negated → counter |
| `competence.demonstrated` | + | `CodeSpan`, `LinkSpan`/citation span, `domain_technical` cues, an `classify_argument` evidence role | subs `.code`, `.citation`, `.technical` |
| `competence.acknowledged` | + | another actor's concession/thanks/deference/citation **targeting** the actor | evidence turns are *other actors'* turns; `target_ref` = acknowledger |
| `competence.corroborated` | + | §6.3 | relational, within the window |
| `competence.claim_grounding` | +/− | + if claimed ∧ (demonstrated ∨ acknowledged ∨ corroborated). − if claimed ∧ none of them | − is capped at `weak` by its own rule: absence inside one bounded window is weak by construction |
| `epistemic.citation` | + | citation spans, citation verbs (`verb.communication`) with an attributed source | |
| `epistemic.hedging` | + | hedged-scope cues | not a deficit trait |
| `epistemic.assertion_strength` | + | boosters, unhedged categorical claims | |
| `epistemic.question_demand` | + | §6.3 | sealioning component |
| `stance.concession` | +/− | `eq_coh{concession}` to parent; concession formulae. − = negated concession ("I'm not wrong") | `negated_pole:"-"` |
| `stance.deescalation` | + | de-escalation formulae, apology, `eq_coh{concession}` after a contrast | |
| `stance.hostility` | + | cue-level hostility (v0), targetable | **cue displayed in window, not "a hostile person"** |
| `status.claim` | + | status/rank assertions (`competence.claimed` overlap, kept separate: status ≠ expertise) | |
| `status.dismissal` | + | dismissal of standing ("you wouldn't understand"), targetable | |
| `deference.to` | + | deference formulae, targetable | |
| `interaction.floor` / `.run` / `.responsiveness` | +/(−) | §6.3 | |
| `tribal.outgroup_reference` | + | 2nd/3rd person plural + `noun.group` collective in the same clause ("you people") | |
| `procedural.appeal` | + | deontic modal + `noun.act`/rule/process nouns, meta-talk about the discussion | |
| `pattern.sealioning` (composite, disabled) | + | `epistemic.question_demand`(→b) ∧ `stance.hostility` absent ∧ b has `epistemic.citation` | replaces v0 `pat.sealioning` |
| `pattern.selective_non_response` (composite, disabled) | + | `interaction.responsiveness:-` repeated (match ≥ partial via §6.2) | |

**Adding a trait requires no code change:**

1. Author a teach-manifest entry (`EqTrait`, ≥1 `EqTraitCue`, optional `EqTraitCompose`, and `LabelStatus{status:"shadow"}`), plus any new `EqCue` items.
2. Run the builder. It calls `teach(..., category="equilibrium_traits")`, which appends to `seeds/equilibrium_traits.json`.
3. Bump `PACK_VERSION`/`TAXONOMY_VERSION`.
4. The generic `eq.quanta.*` rules pick the trait up.

PREREG P5 tests this: the diff touches only seed and manifest files. A trait whose evidence needs a *new structural shape* (a new relation or a new comparison) needs a new rule in the builder. That is still Rule JSON and not Python decision logic, but it is a code-level change and is declared as such.

**Residual traits.** `sd_mint_quantum` can mint unnamed dimensions from residuals. v1 does **not** emit residual-minted traits on the wire. Unaudited, unnamed person traits are a fairness hazard. They are kept on the fork for the PREREG exploratory count only (P9) and discarded. Promoting a residual to a named trait is a human teach step.

### 8.2 Competence: relational, within and across windows

- Competence is the **set** of `competence.*` quanta, each with its own evidence. Ocelot never combines claimed, demonstrated, acknowledged and corroborated into one number. Equilibrium must not either (Equilibrium-side contract test).
- "Claimed vs demonstrated" is the pair of quanta plus `competence.claim_grounding`. The consumer sees, for example, `competence.claimed:+ exact` with `competence.demonstrated` absent and `competence.claim_grounding:- weak`. That says "asserted expertise repeatedly; showed no grounding in this window". It does not say "incompetent".
- Grounding evidence counts only from the actor's own turns (demonstrated) or from *other actors'* turns targeting them (acknowledged, corroborated). Self-citation of one's own earlier turn is not acknowledgement: the rule requires `b ≠ a` as `Not Eq(b, a)`.
- **Across windows:** Ocelot is stateless per request. Cross-window competence is a consumer-side **set union of evidence references** per (actor, trait), with no scoring and no re-classification. If cross-window *rules* are needed (e.g. "claim in window 1 corroborated in window 2"), the honest graph-native option is a larger window (≤500 turns) and not client-side logic. This is an open question (§12, Q1).

### 8.3 Episodes and etiology facets

- **Seeding** `eq.ep.root`: a turn m with `m eq_coh p {contrast}`, or a negated-agreement/concession-negative cue replying to p, and authors a ≠ b. This mints `add_node_if_absent EqEpisode{root:p}` with `kind:"dispute"`.
- **Growth** `eq.ep.extend`: to fixpoint, any turn replying to an episode turn (or `eq_turn_next` in a meeting with no reply edges) that carries a contrast/concession/hostility/question/citation cue joins via `eq_in_episode`. Reply chains in threads use `eq_reply_to`. Meetings use adjacency (`eq_turn_next`) because meeting turns usually lack reply edges. The rule selects on `Window.eq_kind`. That is graph data in a rule, not Python.
- **Merging:** two roots joined by a turn yield two episodes sharing a turn in v1. Union-find merging is WI-8b. It needs a minimum-root `MinOver` rule, which is not designed yet.
- **Kinds:** `dispute` (v1, shadow), `correction` (contrast + citation, no hostility; shadow), `question_answer` (question → reply with citation/elaboration; shadow), and `darvo` (ordered deny→attack→reverse; disabled; ShapeDecode skeleton, WI-9).
- **Facets** are each a codebook `EqFacet{code, cue_set}`. The facet's `match` uses the §6.2 shape over the episode's turns carrying facet cues, against those carrying none.
  - `epistemic`: citation spans, question_demand, `classify_argument` claim/evidence roles, `verb.cognition` stance.
  - `status`: `status.claim`, `status.dismissal`, credential frames.
  - `procedural`: `procedural.appeal`, deontic modality, rule/process nouns.
  - `affective`: hostility cues, affect lexemes from the `psychology.json` mental-state vocabulary, exclamation/intensifier tokens.
  - `tribal`: `tribal.outgroup_reference`, in/out-group pronoun contrast.
- **`generative`:**
  - `true` if `Exists` a concession/de-escalation/acknowledgement turn after the root (`Gt(pos)`) **and** `Not Exists` a later contrast/hostility turn after the last such concession.
  - `false` if `Exists` a later hostility/status-dismissal turn **and** `Not Exists` any concession/acknowledgement after the root.
  - `null` otherwise, including when the episode reaches the window end unresolved.
  - These are three mutually exclusive rule shapes, and `null` is the explicit default.
- Episode `rule_ids` are the root, extend, facet and generative rules that fired.

## 9. Label statuses

- Every trait, episode kind and facet has a `LabelStatus` node: `shadow`, `audited`, or `disabled`. This extends `seeds/equilibrium_label_status.json`, where v0's 7 `pat.*` entries are replaced by `pattern.*` composites.
- **All v0.3.0 items ship `shadow`.** Equilibrium's `label_gates` must keep `shadow` out of user-visible surfaces. Promotion to `audited` requires the PREREG audit (P8) and is a seed change with a version bump.
- `/v1/info` publishes the map. Status lives on the wire beside the output and not inside each quantum, because the contract has no per-quantum status field. That is deliberate: status is a property of the trait version, not of the observation.

## 10. Fairness and red-team risks per trait

| Trait / facet | Risk | Mitigation in design |
|---|---|---|
| `competence.claimed` / `status.claim` | Credential frames over-fire on people who state roles for context (e.g. "as a nurse, …"). | Kept separate from `claim_grounding`. All shadow. Golden G1/G2. The consumer must not show it as "boasting". |
| `competence.claim_grounding:-` | Absence of evidence in one window ≠ incompetence. Short windows bias against brief participants. | Capped `weak`. There is deliberately no minimum-turn gate, because that would be an invented threshold. Instead, the counter set is the actor's own turns with no grounding, so the consumer can see how thin the evidence is. Fairness audit P8 is stratified by turn count. |
| `competence.demonstrated` | Rewards code and links, which favours technical registers and native English jargon. WordNet first-sense bias. | `.code`/`.citation`/`.technical` subs stay separate so the consumer can down-weight per context. Red-team set with non-native phrasing (synthetic). |
| `stance.hostility` | Reclaimed slurs, banter, quoting someone else's hostility, AAVE/dialect false positives. | Cue-level only, targeted only via `reply_to`. Quoted spans (`>`-quote/blockquote format span) are excluded at the boundary. **Quote detection is a new boundary span (WI-3c).** Never surfaced as a person label. |
| `epistemic.hedging` | Could be read as low confidence or competence, a known gendered reading. | Not a competence input. The consumer contract states that hedging is neutral. |
| `epistemic.question_demand` / `pattern.sealioning` | Legitimate persistent questioning gets labelled as bad faith. | The composite is disabled. The component needs a *prior citation by the target*. Golden G8 is a negative control. |
| `interaction.floor` / `.run` | Chairs, presenters and the only expert hold the floor legitimately. Meetings differ from threads. | Descriptive, not evaluative. The status note says "context role unknown". |
| `interaction.responsiveness:-` | Time zones, the person not having seen the question, a reply outside the window. | Requires later activity by the same actor in the window. Dangling `reply_to` refs are not counted as non-response. |
| `tribal.outgroup_reference` | Legitimate group references ("you devs", "we nurses"); identity-group mentions. | Requires an address-plus-collective construction. **No identity-group lexicon, by design.** Red-team for protected-attribute nouns (must not fire on a group name alone). |
| `status.dismissal` | Sarcasm and irony are not detected. | shadow. Documented limitation. |
| All | Actor-name leakage into decisions. | Rules never read `actor_ref` strings. Relabelling invariance is a PREREG property (P4b). |
| All | Negation/modality errors flip meaning. | §5.2 scope rules. Goldens G3–G5. The double-negation limitation is documented. |

Red-team set (synthetic, hand-written, sealed until the PREREG freeze): banter, quotation, sarcasm, dialect variants, non-native phrasing, protected-group mentions, chair-led meetings, single-turn participants, and cross-window replies.

## 11. Work items (estimates are engineer-days, single person)

| WI | Item | Est. | Depends |
|---|---|---|---|
| 1 | Contract plumbing: `/v1/discourse` handler, validation, error model, `/v1/info` maps, `wire_rule_id` reuse; Equilibrium-side JSON-schema contract test (`EQDiscourse*V1`) kept byte-equal | 1.0 | — |
| 2 | Move `LEXICON` from the builder to a teach manifest; lemma matching in `cue_rules`; the `match_on: form` kind for idioms | 1.0 | — |
| 3 | Window ingest (`Window/Actor/eq_*` edges, `eq_turn_pos`); `Token.lemma`/`wn_lex` boundary attrs (3a); typed modal frames (3b); quote span (3c) | 1.5 | 2 |
| 4 | Negation/modality scope seeds and rules (§5.2); coherence marked rules; ShapeDecode-unmarked spike (§5.3) | 2.0 (+1.0 spike) | 3 |
| 5 | Generic quanta rules (evidence, cross-pole, compose, match shapes, `EqMatchShape` chain); Argmax tie verification | 2.0 | 3, 4 |
| 6 | Trait codebook v0.3.0 (§8.1) via teach; label statuses | 1.0 | 5 |
| 7 | Competence family incl. corroboration/acknowledgement; verify `classify_argument` fires on `Message` (or ship without it) | 1.5 | 5, 6 |
| 8 | Episodes: root/extend/facets/generative (8a); merge (8b) | 2.0 (+1.0) | 4, 5 |
| 9 | DARVO skeleton via ShapeDecode (disabled) | 1.5 | 8 |
| 10 | Goldens G1–G16, invariance tests, base-unchanged 10k-turn replay, throughput/RSS harness (PREREG) | 2.0 | 1–8 |
| 11 | Fairness/red-team synthetic set and audit script (stratified counts only) | 1.5 | 10 |
| **Total** | | **~17 d (+3 d optional)** | |

## 12. Open questions and gaps

1. **Cross-window rules.** Should the contract grow a `prior_quanta` input, or is window size (≤500) the boundary? The current answer is consumer-side set union only.
2. **Lemma/lexname as boundary tokens** (§5.5). Is this acceptable under CLAUDE.md:122-125, or does a reviewer require a Rust lemmatiser/WordNet Term?
3. **Unverified machinery:**
   - ShapeDecode on a multi-turn skeleton;
   - Argmax tie behaviour;
   - `add_node_if_absent` with term-valued (not literal) dedup attrs. The doc says "literal-or-term-dict" for `add_node` (py.rs:3808), and the if-absent dedup with term values is not confirmed;
   - `classify_argument` firing on `Message` nodes;
   - 500-turn fixpoint cost.
4. **Episode merging** semantics (shared-turn episodes) are deferred.
5. **Hedged evidence** is folded into `evidence` on the wire. If Equilibrium needs it separated, that is a contract change for both repos.
6. **Meeting windows** have no reply edges, so adjacency-based episode growth may over-merge. This needs synthetic meeting goldens.
7. **Debt carried, not fixed:** `discourse_coherence` fixed weights `_CAUSAL_WEIGHT`/`_NONCAUSAL_WEIGHT` and the `capability_graph` damping scalar are known non-compliant precedents. This design does not use either: centrality is not emitted, and competence does not propagate.
