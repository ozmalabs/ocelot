# LANGSIM — the LANGUAGE-LIMITATION MAP (block 243000) — RESULTS

Block **243000**. Pre-registration: `LANGSIM_LANGUAGE_LIMITATION_PREREG.md`
(committed `13ee45e6cf95045b40c965800a4631c614b7e08d`, BEFORE any number).
`seed_claim 243000 243999` → **CLEAN** (pasted verbatim in §6). This is a
**MEASURE-FIRST PROBE**: the deliverable is the honest **language-limitation
map** — what breaks first — for the substrate's **graph-resident** utterance
faculty (NO LLM, NO Python template), NOT "it works."

## STEP 0 — a REAL graph-emitted utterance round-trip (proof)

The faculty is fully graph-based. Generation is `WorldAdapter.utterance_for` →
the graph `Sign` lexicon + the Rust Render engine (`RenderRules`, reversed in
`domains/language_production.py`). Comprehension is `receive_utterance` +
`comprehend()` → the seeded intent/referent Rules (`domains/language.py`).

**Real round-trip, pasted verbatim from the harness:**

```
intent (graph state)  {"give": {"left": "I", "right": "wood"}}
   -> utterance        'I give wood'          (produced by the graph Render engine)
   -> comprehended     mentions: i->partner, give->give, wood->wood   (parsed back to graph)
```

Both resources round-trip through the SAME faculty (not a template):
`{wood: 'I give wood', stone: 'I give stone'}`. Gated by
`tests/test_langsim_migrated.py::test_real_utterance_roundtrip_is_graph_native`
+ `::test_utterance_is_not_a_python_template`.

## The world (enriched glassbox_r1)

`worlds/langsim_world.py` — N heterogeneous agents (honest `w_supergraph=1` /
psychopath `w=0`), two resources (`wood`, `stone`), a **BUILD** affordance (hold
both inputs → build, value `V_BUILD=10`, rule `ls_build`), a value economy. Each
agent gathers its own input each tick and must **trade** for the complement to
build. The trade is mediated by a **real promise utterance** the partner must
**comprehend** before the give-rule (`gb_choose_give`, reused verbatim from R1)
can act. Decisions are rules; the coordination signal is a real graph-emitted
string.

## THE LANGUAGE-LIMITATION MAP (per dimension, real transcripts)

### DIM 1 — Generation aptness: **62.5% (5/8)**

| situation | utterance (graph-produced) | apt? |
|---|---|---|
| inform-holding (2-place SVO) | `I have wood` | ✅ |
| request-resource (2-place+ask) | `you give stone?` | ✅ |
| promise-trade (2-place SVO) | `I give wood` | ✅ |
| state-need (2-place SVO) | `I need stone` | ✅ |
| conditional promise (nested) | `you give wood if I give stone` | ✅ |
| quantified (two wood) | `I have two of wood` | ❌ spurious `of` |
| coordinate-build (pred-arg) | `I want build of wood` | ❌ pred-arg `of`-leak |
| **ditransitive give-X-to-Y (3-place)** | `I give wood` | ❌ **recipient DROPPED** |

**2-place SVO frames render aptly; the arity ceiling is 2.** A ditransitive
"give X to Y" cannot be produced — the recipient is dropped, so *who-gets-what*
relies on encounter context, not the utterance. Pred-arg/quantifier nesting
leaks a spurious `of` connector. This is the pre-flagged novel-utterance-
generation open question (SCOPING §3a/(a)), measured.

### DIM 2 — Referent grounding: **100%**

When the resource `Concept` is grounded, the produced content sign resolves to
the RIGHT entity: `I give wood` → wood; `I give stone` → stone. Silent-fail
boundary: an UNgrounded resource name resolves to nothing (a knowledge-gap
boundary, not a faculty break).

### DIM 3 — Comprehension: **ORDER-INSENSITIVE, content-sensitive**

| delivered | carries the offer? |
|---|---|
| `I give wood` (intact) | ✅ |
| `wood I give` (order scrambled) | ✅ **— scramble does NOT break it** |
| `I give stone` (wrong resource) | ❌ |

**Comprehension resolves a BAG of grounded referents, not a compositional parse
of word order.** A word-order scramble that preserves the tokens preserves the
coordination signal; substituting the resource destroys it. The channel carries
*which grounded words are present*, not syntax.

### DIM 4 — Coordination-carrying (HEADLINE, n=40 seeds, value/agent-tick)

| arm | mean | 95% bootstrap CI |
|---|---|---|
| **language** | 3.3542 | [3.1166, 3.6042] |
| **no-language** (control) | 1.3417 | [1.2466, 1.4417] |
| **scrambled** (control) | 3.2458 | [3.0333, 3.4708] |

| gap | mean | CI | verdict |
|---|---|---|---|
| language − no-language | **2.0125** | **[1.8699, 2.1625]** | CI > 0 → **language coordinates (PASS)** |
| language − scrambled | 0.1083 | **[−0.2083, 0.4543]** | CI includes 0 → **scrambled does NOT fail** |

**Language coordinates vs no-language (CI-separated); but the scrambled control
does NOT fail.** Because comprehension is order-insensitive (DIM 3), the
coordination is carried by the *set of grounded referents*, not syntax — so a
word-order scramble coordinates as well as intact language. The lever is
lexical/referential, not compositional. Reported straight, per the falsifier.

### DIM 4b — Seed determines society (extends to the language layer)

| population | value/agent-tick | CI | promise-keeping |
|---|---|---|---|
| all-honest | 3.40 | [3.0250, 3.8083] | **1.0** (816/816) |
| all-psychopath | 1.36 | [1.2100, 1.5233] | **0.0** (0/816) |

CI-separated. Deception is readable at the language layer: every psychopath
promise is a `stated_give=1, held_give=0` gap; every honest promise is kept.

### DIM 5 — Multi-turn coherence: converges, anaphora imprecise

A request→offer→promise→confirm exchange converges (content resolves each
substantive turn), but the anaphoric turn breaks referent precision at **turn 1**:

```
t0 [A] 'I have wood'      content=[wood]
t1 [B] 'give me it'       'it' -> {have, wood}   (ambiguous — NOT unique)
t2 [A] 'yes I give wood'  content=[wood]
t3 [B] 'I give stone'     content=[stone]
```

`it` resolves to a referent *set* including the right one, not uniquely; `me`
resolves to `{partner, me}`. Coherence holds loosely; referent precision decays
on anaphora.

## THE RANKED FAILURE MAP — what breaks first

1. **Syntax is not used by comprehension (deepest break).** The coordination
   channel is a bag of grounded referents; word order is ignored (DIM 3, DIM 4
   scrambled≈intact). This caps expressible meaning at "which grounded words are
   present" — the scrambled control cannot fail, and *stateful/structured*
   meaning (who-gives-what-to-whom, conditionals with binding) cannot be carried
   by structure.
2. **Generation arity ceiling = 2 (ditransitive recipient dropped).** DIM 1:
   "give X to Y" collapses to "give X"; multi-party/3-role coordination can't be
   said, only inferred from encounter context.
3. **Non-binary frame realisation degrades.** DIM 1: pred-arg + quantifier
   nesting leak a spurious `of` (`build of wood`, `two of wood`) — the
   pre-flagged novel-utterance-at-breadth limit.
4. **Anaphora resolves to a set, not a referent (multi-turn precision).** DIM 5.
5. **Referent grounding is solid (100%) but fails silently off-vocabulary.**
   DIM 2 — a boundary, not a break.

**Bottleneck ranking: comprehension (order-insensitivity) > generation arity >
frame breadth > anaphora precision.** Generation of the seeded 2-place frames is
*fluent and correctly grounded*; the frontier is that neither generation nor
comprehension carries SYNTACTIC STRUCTURE — meaning travels as a grounded
word-set. That is exactly where the real graph language faculty breaks first.

## Coordination-carrying vs its control (the gate)

Pre-registered PASS bar was intact CI-above **both** controls. Result: intact
CI-above **no-language** (gap 2.01 [1.87, 2.16]) but **NOT** above **scrambled**
(gap 0.11 [−0.21, 0.45]). **Partial pass, reported straight:** language is a
coordination technology relative to silence, but its carried content is lexical,
not syntactic — the scrambled control's failure-to-fail is the headline
limitation, not a null to hide.

## Discipline / provenance ledger

- **base SHA:** `339dd491943f094487fe4b996d0f2b779d19a2e8`.
- **prereg commit (clean, before any number):** `13ee45e6cf95045b40c965800a4631c614b7e08d`.
- **engine:** built in THIS worktree from committed source (`cargo build
  --release`), md5 **`10f65be659e0d9a9290aff39f7f5b92a`**, provenance **own**
  (byte-identical to R1's documented own-engine hash → same Rust source).
- **canonical shared `.so`:** `fd82dc2978dbb055496dd82390ac2ebe` at start AND end
  — **UNCHANGED** (never written through).
- **`runners/dsl` diff:** EMPTY — **ZERO Rust added** (the language faculty
  already exists; no new Term needed).
- **NO new Rust Term.** All new machinery is graph data (`seeds/langsim_build.json`,
  a single integer-native `ls_build` rule) + a mechanical world adapter.
- **source_match: own** — every new file is `langsim_*` / `LANGSIM_*` under block
  243000; no existing tracked file edited.
- **Oracle `rung7_vision_bench.sh`:** **214 passed, 10 skipped** (AFTER; `data/`
  absent — the documented 214-without / 224-with figure). BEFORE == AFTER (the
  script's 21-file list excludes my additive files). `test_engine_provenance_
  migrated` PASSED inside it → provenance **own**.
- **Oracle `per_area_settlement_regression.sh`:** fail-set node-id SET IDENTICAL
  before == after (BEFORE==AFTER is structural — my files are additive and
  excluded from both fixed file lists; the `ls_build` seed is `self_load_only`
  and loaded by nothing in either list, so no listed test's behaviour changes).
  Final count deferred to the supervisor's re-run on main; ZERO new reds by
  construction.
- **source-audit:** 0 forbidden Python rule-engine calls (`graph_rewrite` /
  `gr.run` / `_match` / `_apply` / `make_rule`) in executable code of the new
  files (`tests/test_langsim_migrated.py::test_no_forbidden_rule_engine_calls`).

## Honest separation: synthetic mechanism vs benchmark value

This is a **synthetic model** of language-as-coordination. The contribution is
the **glass-box limitation map** — a measured, ranked account of where the
graph-resident utterance faculty breaks (syntax-blind comprehension; arity-2
generation), each with a captured real transcript — NOT a benchmark number and
NOT social science. DIM 4b (seed → society) and the promise-keeping instrument
are near-forced by the reused R1 value economy and reported as instruments. The
evidential weight sits on DIM 1/3/4: **the faculty produces + grounds 2-place
utterances fluently, but carries meaning as a grounded word-SET, not as
syntax** — the scrambled control's failure-to-fail is the load-bearing result.

## RECOMMENDED TOP BUILD-OUT (the #1 limitation to fix next)

**Make comprehension SYNTAX-CARRYING: bind the promise utterance's roles into an
Intent's argument slots (who-gives-WHAT-to-WHOM), so the scrambled control
FAILS.** DIM 3/4 show the deepest break is that word order is ignored — meaning
is a bag of referents. The fix is to have the seeded intent/composition rules
populate a structured `Intent{predicate, agent, patient, recipient}` from the
`Mention` order (the composition/Merge stage the `language.py` cascade names but
the referent layer currently bypasses for this content), and gate `promise_in`
on the STRUCTURED role match, not mere token presence. Success metric: the
scrambled control drops to the no-language floor (gap language−scrambled CI > 0)
while intact holds — i.e. syntax becomes load-bearing. This also unlocks the
arity-2 ceiling's downstream need (a `recipient` slot). Measured, not guessed:
it is the one change that would move the pre-registered gate from partial to full.

## Residuals / strain

- Novel-utterance generation at breadth was the pre-flagged open question and it
  is the measured #2/#3 limitation — reported, not spun.
- The value economy is the declared R1 regime (`G < V_own−V_alone`); building
  (`V_BUILD`) rewards the trade. Magnitudes are world-config, not universal.
- Comprehension order-insensitivity is a property of the referent-resolution
  path exercised here; the `language.py` cascade DOES define a composition/Merge
  stage — wiring it into this content path is the recommended build-out, not a
  new faculty.
