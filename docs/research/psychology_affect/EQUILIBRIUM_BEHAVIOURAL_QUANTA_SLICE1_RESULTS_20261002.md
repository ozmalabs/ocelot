# EQUILIBRIUM BEHAVIOURAL QUANTA — SLICE 1 RESULTS (stream T3b)

**Date:** 2026-10-02. Worktree `.worktrees/t3b` (branch `t3b/behavioural-quanta`, base `2aefc943`) plus **uncommitted** files (§6). Design: [`EQUILIBRIUM_BEHAVIOURAL_QUANTA_DESIGN_20261002.md`](EQUILIBRIUM_BEHAVIOURAL_QUANTA_DESIGN_20261002.md). PREREG: [`EQUILIBRIUM_BEHAVIOURAL_QUANTA_PREREG_20261002.md`](EQUILIBRIUM_BEHAVIOURAL_QUANTA_PREREG_20261002.md).

The PREREG is still a **DRAFT and was not frozen** before this slice ran. The goldens here were written by the implementer alongside the rules, so nothing below is confirmatory. This is a systems slice on synthetic data only: pseudonyms throughout, no corpus, `OZMA_NO_LLM=1`, no Rust changes.

## 1. What was built

The seed pack is now **0.3.0 / `eq-tax-0.3.0`**: 11 `self_load_only` manifests, all produced by `scripts/build_equilibrium_seed_pack.py`, which imports `scripts/_equilibrium_quanta_rules.py`. Every codebook row is minted through `domains.teach`. In total there are 113 rules, and all of them are graph data.

| Manifest | Content |
|---|---|
| `equilibrium_window` (new) | Window ingest Γ productions. 5 `EqStratum` clock nodes. S0 rules `eq.win.responds_to.{reply,adjacent}` (meeting adjacency is gated on `EqWindow.eq_kind`). |
| `equilibrium_scope` (new) | 62 closed-class rows: `EqScopeOp` (27 neg, 18 hedge), `EqScopeBoundary` (9), `EqCohMarker` contrast (8). These are **lexical by design** (DESIGN §5.4). |
| `equilibrium_lexicon` | 136 `EqCue` rows (87 before) across 14 cue sets. Class slots: `<num>`, `<noun.person>`, `<noun.group>`. |
| `equilibrium_msg` | 74 rules. n-gram hits, scope-decided labels (affirmed / `_negated` / `_hedged`), `hedge`, `reply_contrast`, speech act, spans. |
| `equilibrium_traits` (new) | 25 `EqTrait` and 44 `EqTraitCue` rows. This is the open vocabulary. |
| `equilibrium_quanta` (new) | 24 rules. Generic evidence, hedged, counter and addressee rules. Floor, run, responsiveness, withdrawal, question_demand, compose. Match shapes. |
| `equilibrium_competence` (new) | 5 rules: corroborated, contested, claim_grounding (two `+` rules and one `−` rule). |
| `equilibrium_episode` (new) | 34 `EqEpisodeCue`/`EqFacetCue` rows. 8 rules: root, extend, facet, generative true/false, facet match. |
| `equilibrium_label_status` | 70 rows: msg labels, traits (7 `pattern.*` disabled), `episode.dispute`, and 5 facets. The `pat.*` rows are removed. |

**Adapter (`domains/equilibrium_classify.py`).** It ingests, ticks and reads out. `discourse(substrate, agent_root, window, turns)` runs `ingest_window`, then `run_strata`, then `read_discourse`.

**Server.** `POST /v1/discourse` follows the shared contract. Validation is closed. The turn limit is 500. The body cap is 16 MiB. Errors never echo the input. There is one fork per request, with the revision checked on every request and the strong digest checked every 1,000 requests and on `/healthz`. `/v1/info` now carries `trait_status`, `episode_kind_status`, `facet_codes` and `endpoints` (`ok`/`ok`). `/v1/classify` is unchanged on the wire; only the version suffixes changed.

## 2. Decisions and deviations from the design

1. **Stratified negation via a seeded clock (adapter judgement call).**
   - Rules that read *absence* (claim_grounding −, generative, match shapes, counter-attach, responsiveness) must not run before the facts they negate over are complete.
   - Each stratum rule carries the match edge `["agent","eq_stratum_k","st"]`. The adapter ticks to fixpoint, then opens S1…S5 **in seeded order**, adding one marker edge per stratum and ticking after each.
   - This is a fixed schedule declared in seed data, with no branch on graph state. A reviewer may prefer a Rust "stratified run" primitive. That would be the clean form, and it was not built.
2. **Scope by relation, not closure.** DESIGN §5.2 propagated `eq_in_scope` edges. Instead, a cue head `t` is in scope of an operator `o` when:
   - `o` is in the same clause (`eq_clause`, from tokeniser punctuation),
   - `o.eq_pos < t.eq_pos`, and
   - no `EqScopeBoundary` token lies between them.

   This needs no fixpoint and no ordering hazard.
3. **Hit → decide split.** Scoped n-gram rules write `eq_hit_<set>` (Message→Token) and the `eqcue:` provenance. Three scope rules then decide affirmed, negated or hedged. Message `rule_ids` contain both the n-gram rule and the label rule (e.g. `eq.msg.concession.cue_bigram` and `eq.msg.concession.affirmed`).
4. **Form vs lemma.**
   - Formula sets match `form`, per DESIGN §5.4 (idioms). Only `domain_technical` matches `lemma`.
   - The lemma is WordNet `morphy` (verb, then noun, else the form). The builder normalises cue words with the **same adapter function**.
   - With noun-first order, `was`→`wa` and `is`→`i`; verb-first avoids that.
   - The token chain no longer crosses clause punctuation. This stops "thank you, team" from matching `you <noun.group>`.
5. **`index_hints` (R10 join index) on n-gram cue rules.** This changes matcher traversal only. S0 time on long texts dropped from 2.44 s to 0.56 s (30 × 4,000 chars). Classify throughput rose from 1,166 msgs/s (0.2.0 SLICE figure) to 1,431 msgs/s.
6. **Meeting addressing.** In meetings, a turn without `reply_to` *responds to* the previous turn when another actor spoke it (`eq_responds_to` / `eq_addresses`).
7. **Wire details.**
   - The episode id is `ep:<root turn id>`, not the design's `ep:<window>:<root>`. The client caps ids at 255 characters, so turn ids are capped at 252 server-side.
   - Discourse errors use `bad_request`. Classify keeps `schema_violation`.
   - The `busy` error is not produced: requests serialise on the lock.
8. **Match shape.** I used PREREG §4.3: exact means E > |{pick E}| with no counter and no hedge; partial means E > C and not exact; weak covers everything else.
   - A single uncontested act is therefore `partial`. That matches the "single turn at most partial" decision.
   - It contradicts DESIGN §6.2's weak row ("a single-turn act") and the PREREG G2/G10 expectations of `weak`. That is an internal inconsistency in the drafts, flagged here and not resolved by me.
   - `claim_grounding −` is weak by construction.
9. **Fuel.** `DISCOURSE_FUEL = 10,000` steps per stratum tick, the same as classify. The maximum observed is 37 steps (S0, 500 turns).
10. **New trait added to the vocabulary:** `interaction.withdrawal` (disengagement formula; later turns by the same actor are counter-evidence), needed for the withdrawal golden. `competence.contested` was also added (a claim later met by another actor's contrast reply that carries grounding).

**Unverified machinery from DESIGN §12.3:**

| Item | Outcome |
|---|---|
| `add_node_if_absent` with term-valued keys | **Verified**: dedup on resolved values, including Node values (probe, plus every quantum test). |
| `Argmax` ties | **Worked around**: not used. Floor is strict max via `Not Exists(other with ≥ turns)`, and the tie test passes. |
| ShapeDecode multi-turn / unmarked coherence | **Not attempted**: only marked contrast ships. |
| `classify_argument` on Message | **Not used.** |
| 500-turn fixpoint cost | **Measured** (§4). |

## 3. Predictions vs measurements (PREREG numbering)

| P | Prediction | Result |
|---|---|---|
| P1 | 16 goldens G1–G16 pass exactly | **Partial / not as specified.** Built: a meeting golden (floor, uncorroborated claim contested by grounded evidence, concession, de-escalation bridge, withdrawal) and a thread golden (acknowledged plus corroborated claim, non-response, question demand), each asserting the exact set of `(actor, trait, polarity, target)` keys. Also covered: G3, G5 (limitation), G8 and its control, G9 including the tie, G10 including the absent-actor variant, G11, G12, G13, G14, G16. **G2 and G10 expect `weak`, but `partial` is produced** (see §2.8). **G15 (quoted hostility) fails: not built** (WI-3c). G4, G6 and G7 are not written as separate goldens. |
| P2 | ≥40 × 3 negation set, 100% single negation | **Smaller set:** 20 near-miss items plus quanta-level negated and hedged tests. All pass, including "not a good point" → `concession_negated` and no `concession`. Double negation behaves as documented (still negated). Negation across a comma is not seen, by design. |
| P3 | Compliance | (a) The adapter has no conditionals over graph state. Exceptions: the fuel check and the mechanical read-out sort/omit. (b) Every quantum and episode has rule ids, and the wire ids are `name:0.3.0`. (c) A test asserts **zero** numeric `Lit` in any pack rule. (d) A grep test finds no `anthropic`/`openai`/`teacher_via_claude`/`language_world`/`nltk.download` in the request-path files. The Equilibrium `check_no_llm.py` was not run here. |
| P4 | Determinism and invariance | (a) Identical output on re-run, in-process and over HTTP. (b) Relabelling **actors** gives the permuted output; turn-id relabelling was not tested. (c) Prepending a neutral turn to the thread golden leaves the quanta set unchanged, floor included. |
| P5 | New trait via teach manifest, diff touches only seeds | **Variant only.** On a fork, adding `EqTraitCue` and `EqTraitCompose` rows as graph data produces a new trait and a composite (match = weakest component). A disabled composite is not minted, and the base is untouched. The PREREG test trait `epistemic.source_request` (verb.communication + source noun) was **not built**: the class token covers noun lexnames only. |
| P6 | 500-turn p95 0.6–1.5 s; 200-turn ≤ 0.5 s; RSS ≤ 384 MB; quanta adds < 50% over classify `run_rules`; ≥2× fuel headroom | 500-turn p95 **658 ms**. 200-turn p95 **299 ms**. 50-turn p95 70 ms. VmHWM **242 MiB**. Fuel headroom about 270× (37 of 10,000). **Quanta overhead prediction FAILED:** for 500 turns, S0 (the classify-equivalent pass) takes 132 ms and S1–S5 take 225 ms, so quanta add about +170%. |
| P7 | Base unchanged after 20 × 500 + 100 × 100 turns | **Pass.** 20,000 turns in 120 windows. `source_revision` is `[1753,245,127]` before and after. The strong digest at boot equals the digest after replay. The tree diff is empty. strace live with zero writes outside tmp. |
| P8 | Fairness audit | **Not run.** There is no sealed red-team set. |
| P9 | Exploratory | **Not run.** |

## 4. Measurements (actual output, concurrency 1, loopback HTTP)

```
MEASURE discourse c=1 window=50 turns x20: p50 59 ms p95 70 ms max 93 ms, 839 turns/s
MEASURE discourse c=1 window=200 turns x10: p50 215 ms p95 299 ms max 301 ms, 876 turns/s
MEASURE discourse c=1 window=500 turns x10: p50 565 ms p95 658 ms max 697 ms, 873 turns/s
MEASURE boot-to-healthy 2.12s, peak RSS (VmHWM) boot 239.0 MiB -> after 241.7 MiB
MEASURE c=1 batch=100 n=10000: 1431 msgs/s (/v1/classify), batch p50 68.7 ms p95 85.5 ms
P7 discourse turns=20000 windows=120 source_revision=[1753, 245, 127] digest=d966a5535469492b strace=yes
```
These lines are from the final full-suite run (98 passed). An earlier run gave 500-turn p95 637 ms and 200-turn p95 263 ms.

**In-process breakdown, 500-turn synthetic window:**
- meeting: ingest 306 ms; ticks S0..S5 = 132 / 22 / 140 / 38 / 24 / 1 ms; read 12 ms; steps `[37, 7, 13, 5, 6, 0]`;
- thread: ingest 182 ms; S0 134 ms; S1–S5 about 225 ms.

**Nulls and problems:**
- **Worst case:** a 500 × 4,000-character window takes about **35 s**. About 80% of the ingest time is the existing `kind_signals` speech-act parse, which is not new code. Requests serialise, so one such window blocks the sidecar, and it exceeds the Equilibrium client's default 10 s timeout.
- **Memory:** WordNet raises boot RSS from about 44 MiB (0.2.0) to about 239 MiB. That is still under 384 MB.

## 5. Gaps and open questions

1. The stratum clock in the adapter should become a Rust primitive (a stratified `run_rules`) if reviewers object to item §2.1.
2. `Token.lemma` / `eq_class` are WordNet boundary lookups, a judgement call under CLAUDE.md:122-125. They have first-sense bias. "I'm an idiot" and "as a user" fire `msg.credential`, because `noun.person` is the first sense.
3. Remaining coverage limits:
   - quote spans (G15) are not built;
   - only **marked** contrast coherence exists (no ShapeDecode);
   - no typed modal frames;
   - double negation is not resolved;
   - negation does not cross a comma ("I don't think, honestly, that's fair" is missed).
4. Episodes:
   - overlapping roots are not merged (G11 shows `ep:g1` null plus an overlapping `ep:g3` false);
   - meeting adjacency growth may over-merge;
   - facet `match` is almost always `weak`, because C is the episode's non-facet turns, as the design specifies.
5. `competence.demonstrated` fires on any technical-vocabulary mention, including a question like "Could the cache be cold?". This is a precision and fairness concern for P8.
6. Composites: the generic compose rule takes a conjunction of two components. The shipped `pattern.*` rows are status-only. Their design definitions need absence and other-actor conditions that a conjunction cannot express.
7. `coherence_relations.json` cannot be loaded through `load_seed_manifest` ("seed node missing local_id"). Its DISC_CONTRAST forms are **copied** into `equilibrium_scope` with a citation, rather than declared as a dependency.
8. The drafts disagree on single-act `match` (§2.8). The disagreement must be resolved before the PREREG is frozen.

## 6. Files

Modified:
- `domains/equilibrium_classify.py`
- `services/equilibrium_classifier/server.py`
- `scripts/build_equilibrium_seed_pack.py`
- `seeds/equilibrium_{tokens,lexicon,msg,pattern,label_status}.json`
- `tests/test_equilibrium_classify.py`
- `tests/test_equilibrium_classifier_service.py`

New:
- `scripts/_equilibrium_quanta_rules.py`
- `seeds/equilibrium_{window,scope,traits,quanta,competence,episode}.json`
- `tests/test_equilibrium_discourse.py`
- `tests/test_equilibrium_discourse_service.py`
- this document
