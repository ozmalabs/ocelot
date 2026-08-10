# BIGVILLE — SYNTACTICALLY COMPOSED POLITICAL DRAMA — RESULTS

Block **246000**. Pre-registration: `BIGVILLE_LANG_PREREG.md` (committed
`ec450714c23001d069d40173f84555f1646f7b99`, BEFORE any number). Base SHA
`b1b021f517acb327160af2cbdf55f3627b484d8d`.

## Headline

**THE DRAMA'S UTTERANCES ARE NOW COMPOSED, NOT LOOKED UP.** Block 245000 proved
the political drama emerges from the seeds + rules but flagged its own residual —
the utterance TEXT was a cosmetic canned-string map (`UTT_TEXT` in the 245 runner).
This block wires the drama's utterances through the block-244000 syntax faculty:
John's benevolent self-claim, his DARVO accusation of Mary, his held undermine
intent, and Mary's claim about John are each COMPOSED via `language.produce` from a
structured `Intent{predicate, agent, patient}` over a graph-resident drama lexicon,
and comprehended ORDER-SENSITIVELY via `language.comprehend`. The observation counts
that drive the UNCHANGED credibility rule are DERIVED by COMPREHENDING the composed
public face — so the language is load-bearing. The 245 emergence gates stay green,
now carried by composed language.

| gate | result |
|---|---|
| **G-composed-not-lookup** (HEADLINE) | **PASS** — composed surface round-trips; source-audit clean (no lookup dict) |
| **G-roles-carry** (order-sensitive who-accuses-whom) | **PASS** — role-swap changes the target; scramble drops the agent |
| **G-drama-still-emerges** (245 under composed language) | **PASS** — scheme 1.0/0.0, inference hostile-1/none-0, credibility 1/5 vs 5/5 |
| **G-discipline** | **PASS** — own engine, canonical `.so` unchanged, NO Rust, oracles before==after |

## G-composed-not-lookup — the load-bearing proof (composed, not looked up)

A composed utterance and its structured Intent, round-trip-verified on the own
engine (no LLM, no template, no lookup):

```
structured Intent : {"predicate": "accuse", "agent": "John", "patient": "Mary"}
COMPOSED surface  : "John accuse Mary"              (language.produce over drama signs)
comprehended back : {"predicate": "accuse", "agent": "John", "patient": "Mary"}
round_trips       : True
```

The live drama's composed episode (glass-box read off `ComposedUtterance` nodes;
`results/bigville_lang/episode_transcript.txt`):

```
t01  John (public, COMPOSED):  "John serve Bigville ; John accuse Mary"  <<< stated!=held DECEPTION
      parsed roles: {'predicate': 'serve', 'agent': 'John', 'patient': 'Bigville'}
      John (held intent, COMPOSED from graph): "John undermine Mary"  {'predicate':'undermine','agent':'John','patient':'Mary'}
      Mary (ToM decode -> minted belief): John is 'hostile'
      villagers backing Mary this tick: 0/5
```

The **`stated≠held` gap is now LINGUISTIC**: a composed public utterance (John
*serves* Bigville / *accuses* Mary) versus a composed private intent (John
*undermines* Mary). Both surfaces are produced by the faculty and comprehended back
to their structured roles — nothing is a canned string.

**Source-audit (gated).** `worlds/bigville_lang_world.py` and
`domains/drama_syntax.py`: NO forbidden Python rule-engine call (`graph_rewrite.run`
/ `gr.run` / `_match` / `_apply` / `make_rule`), NO shaping token, and NO canned
drama utterance string / lookup dict. The composition path is `language.produce` /
`language.comprehend` (the graph faculty), reached through `drama_syntax`. Gated by
`test_source_audit_no_utterance_lookup_dict_and_no_python_rule_engine`.

## G-roles-carry — who-accuses-whom is carried order-sensitively

| composed / delivered | comprehended structured Intent | target (patient) |
|---|---|---|
| `John accuse Mary` | {accuse, agent:John, patient:Mary} | **Mary** |
| `Mary accuse John` (role-swap) | {accuse, agent:Mary, patient:John} | **John** |
| `accuse John Mary` (word-order scramble) | {accuse, **agent:None**, patient:John} | agent UNBOUND |

"John accuses Mary" ≠ "Mary accuses John": the receiver comprehends WHO accuses
WHOM from word ORDER — a role-swap changes the target, and a scramble (verb-first)
fails to bind the agent (the agent slot is a LEFT slot; no left neighbour ⇒ no
accuser). This is the who-did-what-to-whom the drama's credibility asymmetry needs.
The composed public face DRIVES the credibility counts: under deception every
villager parses John's benevolent `serve` face (`seen_benevolent == 20`,
`seen_hostile == 0` for all 5) — verified by
`test_the_composed_face_drives_the_credibility_counts`.

## G-drama-still-emerges — the 245 dynamics under composed language

Re-run the three 245 headline dynamics + their FAILING controls, now driven by the
composed utterances (`results/bigville_lang/results.json`):

| gate | main arm | FAILING control | result |
|---|---|---|---|
| **G-scheme-emerges** | John undermines 20/20 (`scheme rate 1.0`) | non-psychopath → **0.0**; indifferent psychopath → **0.0** | PASS |
| **G-inference-emerges** | Mary mints **1** `InferredDisposition='hostile'` + goal + claim | no-ToM → **0**; benign John → decode `'benign'`, no goal | PASS |
| **G-credibility-asymmetry** | deception → **1/5** back Mary | deception collapsed → **5/5** | PASS |

Values are byte-identical to 245's categorical results because the composed
observation counts are preserved BY CONSTRUCTION (each derived count maps 1-to-1
onto 245's direct read: `seen_benevolent += 1` iff the comprehended public names
John as `serve` agent ≡ `+= stated`; `seen_hostile` iff `undermine` agent ≡
`+= (1-stated)`; `heard_claim` iff Mary's comprehended claim names John undermining
≡ `+= mary_claims`). The DECISIONS remain the unchanged 245 seed rules
(`ss_choose_burn`, `bd_john_public_face`, `bd_mary_infers`/`_forms_goal`/`_claims`,
`bd_villager_backs`); only the surfaces and the counts are now composed/comprehended.

## Which frames COMPOSE vs fall back (honest scope)

- **COMPOSE (all of the drama's key utterances):** `serve{John, Bigville}` (John's
  benevolent self-claim), `accuse{John, Mary}` (the DARVO blame), `undermine{John,
  Mary}` (John's held intent), `undermine{John, village}` (Mary's claim). Every one
  is produced by `language.produce` and comprehended back to its structured roles.
- **Falls back / not attempted:** the public deception face is TWO composed clauses
  (`serve … ; accuse …`), not ONE conjoined clause — `language.comprehend` returns
  the two top-level constituents; a genuine coordinated conjunction ("I serve
  Bigville AND the pastor stirs trouble" as one Merge tree) is not built (no
  conjunction sign in the lexicon). The predicates are SVO 2-place; the 244000
  3-place ditransitive (recipient via a role-marker) is not used by the drama.
- **Evidential weight — now genuinely linguistic for the credibility gate:** the
  villagers' `seen_benevolent`/`seen_hostile`/`heard_claim` counts are DERIVED by
  comprehending the composed utterances (a parsed `serve`-by-John vs `undermine`-by
  -John), so the credibility asymmetry is carried by who-does-what the receiver
  parses. Mary's INFERENCE, by contrast, decodes John's observed ACTION harm-rate
  (behaviour, not language) — unchanged from 245, correctly (ToM reads deeds, not
  words). So the drama's evidential spine is now part-linguistic (the public
  credibility channel) and part graph-state (the behavioural ToM channel), reported
  straight.

## Discipline / provenance ledger

- **base SHA:** `b1b021f517acb327160af2cbdf55f3627b484d8d`.
- **prereg commit (before any number):** `ec450714c23001d069d40173f84555f1646f7b99`.
- **engine:** built in THIS worktree from committed source (`cargo build
  --release`), md5 `10f65be659e0d9a9290aff39f7f5b92a`, provenance **own**
  (`source_match=own`; byte-identical Rust to blocks 243/244/245 — this rung adds
  ZERO Rust, same md5).
- **canonical shared `.so`:** `fd82dc2978dbb055496dd82390ac2ebe` at START AND END —
  **UNCHANGED** (never written through; my build targets THIS worktree's
  `_native.abi3.so`).
- **`runners/dsl` diff:** EMPTY — **ZERO Rust added.** No new Term. The drama
  lexicon is graph-resident Sign data; composition/comprehension is the existing
  `language.py` Merge faculty on the existing engine (the 244000 path).
- **source_match: own** — every new file is `bigville_lang` / `drama_syntax` /
  `BIGVILLE_LANG` under block 246000; **no existing tracked file edited** (blocks
  244 and 245 are reused BY IMPORT — `BigvilleLangWorld` subclasses the untouched
  `BigvilleDramaWorld`; `drama_syntax` imports the untouched `language`).
- **Oracle `rung7_vision_bench.sh`:** **214 passed, 10 skipped**, zero failures —
  matches the 244/245 documented baseline EXACTLY (this rung touches no vision path;
  my files are additive and not in the script's fixed file list). `test_engine_
  provenance_migrated` GREEN inside it → provenance **own**.
- **Oracle `per_area_settlement_regression.sh`:** **23 failed, 278 passed, 5
  skipped** — fail-set node-id SET IDENTICAL to the 244/245 documented baseline
  (3 `test_cortices_tick` + 1 `test_composer_driver_migrated::test_question_driver_
  parity` + 5 `test_gap_awareness_migrated` + 5 `test_elaboration_migrated` + 9
  `test_topic_route_selfheal_migrated` = 23). IDENTICAL before==after by construction
  (fixed file list; none of my files are in it, none import `bigville_lang`/
  `drama_syntax`; no Rust). ALL 23 are the pre-existing environment baseline
  (conversation/topic-route/gap-awareness/elaboration/cortices-tick/composer-driver
  — FileNotFoundError from absent `data/`, frozen-baseline drift, daemon-reconcile
  assertions); ZERO involve bigville. `test_failure_baseline_migrated` and
  `test_engine_provenance_migrated` both GREEN (not in the FAILED set). ZERO new reds.
- **Gate:** `tests/test_bigville_lang_migrated.py` — **11 passed**.

## Honest separation & residuals

- This is a synthetic MODEL. The 245 contribution (glass-box attribution of the
  scheme/inference/credibility dynamic to named knobs under failing controls) is
  unchanged; THIS block's contribution is that the SURFACE and the credibility
  observation counts are now genuinely composed/comprehended by the graph syntax
  faculty, not templated — the who-accuses-whom is carried by word order.
- The economy and every social DECISION are 245's unchanged graph rules; the
  composed counts are byte-identical to 245's by construction. The evidential
  weight moved from "cosmetic label" to "linguistic artefact" for the public
  credibility channel; the ToM channel remains behavioural (correctly).
- Two composed clauses, not one conjoined clause, for the deception face (no
  conjunction sign); reported. SVO 2-place predicates only.
