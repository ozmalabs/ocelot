# LANGSIM — the LANGUAGE-LIMITATION MAP (block 243000) — PRE-REGISTRATION

**Status: PRE-REGISTRATION. No measurements below. Written BEFORE any number.**
Block **243000** (`scripts/seed_claim.py 243000 243999` → CLEAN, recorded verbatim
in results). This is a **MEASURE-FIRST PROBE**. The deliverable is an honest
**language-limitation map** — *what breaks first, in what order* — for the
substrate's GRAPH-RESIDENT utterance faculty when N agents in a richer economy +
building world must coordinate through **real produced utterances**. The
deliverable is NOT "it works."

## 0. What this probes (and the corrected premise)

The utterance faculty is **fully graph-based — NO LLM**. Generation is
`WorldAdapter.utterance_for(meaning)` / the `_communicative_action` render path:
a relational communicative meaning is realised to a surface string by the
graph lexicon (`Sign` nodes, `learn_sign`) + the Rust Render engine
(`RenderRules`) read in reverse (`domains/language_production.py`). Comprehension
is `receive_utterance` + `comprehend()` — the seeded intent/referent Rules
(`domains/language.py`, `comprehend_text`) that tokenise an utterance into
`Mention` nodes and resolve `Mention -refers_to-> Concept`, building an `Intent`.

**Source-audit bar (sharp): the utterance content must originate from the
graph-resident language machinery — NOT an LLM AND NOT a Python string template.**
That is the exact thing this probe measures. Any transcript in the results whose
surface string is a Python f-string / `.format` / templated join is a FIRING
OFFENCE and voids the run.

The step-up over block 234000 (GLASS-BOX R1): R1's "language" was a
`stated_give=1` cheap-talk **flag** under `comms_on` — no utterance string ever
existed. Here the coordination signal is a **real graph-emitted utterance
string** that the receiver must **comprehend back into graph state** before any
rule can act on it. The probe measures where that real round-trip degrades.

## 1. The world (mechanical adapter — enrich glassbox_r1)

`worlds/langsim_world.py` — a WORLD ADAPTER (ingest/emit around `run_rules()`),
additive, `self_load_only`, default-OFF. Enriches `glassbox_r1_world`:

- **N heterogeneous agents** (honest `w_supergraph=1` vs psychopath `w=0` seeds,
  the harvest lineage), each carrying a **language faculty** (its own
  `WorldAdapter` host) + resource holdings as graph state.
- **Multiple resources** (`wood`, `stone`, `grain`) seeded as `Concept` nodes the
  agents `knows_concept`, so referents can resolve.
- **A BUILDING / PRODUCTION affordance**: an agent holding the required resource
  set can BUILD a structure of value `V_BUILD` (> any single holding), consuming
  the inputs. Building rewards trade (you need what you lack to build).
- **An economy**: per-agent holdings + accumulated value; collective welfare.

Every AGENT DECISION is a graph **rule**, never Python:
- **whether to give / trade** = the R1 value Argmax rule `gb_choose_give`
  (`total_value = happiness + fulfilment_value`), gated on `promise_in`;
- **whether to build** = a rule over held resources;
- **what to communicate about** = the content (which resource, which partner,
  which quantity) is READ from the agent's own graph state (holdings/needs) —
  mechanical I/O, exactly like R1 reads `chosen_give` — and REALISED to an
  utterance by the graph faculty. The renderer, not Python, produces the string.

The one causal change vs R1: `promise_in` for the receiver is set **iff the
receiver actually COMPREHENDED a real promise utterance that resolved to the
right resource + partner** — language is now genuinely in the loop.

## 2. Pre-registered measurement DIMENSIONS + metrics

For EACH dimension: a numeric metric + CAPTURED real transcript examples
(successes AND failures). All utterances printed verbatim from the graph faculty.

1. **Generation aptness** — for each communicative situation (inform-holding,
   request-resource, promise-trade, coordinate-build), does the graph faculty
   produce an APT utterance? Metric: **aptness rate** = fraction of situations
   whose rendered string is (a) non-empty, (b) not a bare act-name leak, (c)
   contains the intended content sign(s). Sub-probe: **novel-situation
   generation** — situations whose frame is NOT in the grounded render rules
   (multi-argument, quantified, conditional). Report where aptness degrades.
2. **Referent grounding** — does the produced utterance refer to the RIGHT world
   entities? Metric: **referent-correctness rate** = fraction of produced
   utterances whose content sign, when comprehended, resolves to the intended
   resource/partner Concept (right resource, right partner, right quantity).
3. **Comprehension** — does the RECEIVING agent parse the utterance into the
   correct graph state? Metric: **comprehension-correctness rate** = fraction of
   delivered utterances for which the receiver's resolved `Mention -refers_to->`
   set matches the sender's intended referents AND an `Intent` is built.
4. **Coordination-carrying (the R1 gate, now with REAL language)** — does the
   comprehended info change the receiver's behaviour CORRECTLY? Metric:
   **collective build/trade value per agent-tick**, REAL-language ON vs the two
   controls in §3, bootstrap-CI-separated.
5. **Multi-turn coherence** — over a multi-turn request→offer→promise→confirm
   exchange, does the dialogue stay coherent and converge to a completed trade?
   Metric: **convergence rate** = fraction of multi-turn negotiations reaching a
   completed, correctly-referented trade within a fixed turn budget; **coherence
   decay** = turn index at which referents first mis-resolve.

## 3. The FAILABLE coordination control (§4 falsification bar)

The coordination gate (dimension 4) is measured against controls that MUST be
able to fail it:

- **NO-LANGUAGE control** — same world, same seeds, utterances never delivered
  (`promise_in` can only come from a comprehended utterance, so it stays 0). If
  collective value is not CI-higher with language, **language is not the lever —
  reported straight** (R1's registered falsifier, carried forward).
- **SCRAMBLED-UTTERANCE control** — the faculty produces the real utterance, but
  its tokens are shuffled before delivery so comprehension mis-resolves. This
  isolates *comprehension of real content* from *the mere presence of a
  channel*. If scrambled coordinates as well as intact, the content is not being
  used — reported straight.

**PASS** = intact-language value CI-separated ABOVE **both** controls. Anything
less is reported as the honest result, not spun.

## 4. Honest-reporting protocol (binds the results)

- **The map is the deliverable.** Rank the limitations by *what breaks first*.
  If generation is fluent but grounding fails, say so; if comprehension is the
  bottleneck, say so. A dimension that PASSES cleanly is reported as passing; a
  dimension that BREAKS is reported with the captured failing transcript.
- **Real transcripts only.** Every reported utterance is printed verbatim by the
  graph faculty in the harness; failing utterances are captured, not hidden.
- **Novel-utterance generation at breadth is the PRE-FLAGGED open question**
  (SCOPING §3a/(a)). If the faculty's render frames are narrow, that is an
  expected finding, reported as such — not a failure of the probe.
- **Synthetic-mechanism vs benchmark value SEPARATED.** This is a synthetic
  model of language-as-coordination; the contribution is the glass-box
  attribution + the limitation map, NOT a benchmark number and NOT social
  science.
- **No number before this prereg is committed.** The CLEAN `seed_claim` output
  is pasted verbatim in the results.
- **Anthropomorphism refused.** Utterances, promises, trades are mechanical graph
  structures; report the mechanism.

## 5. Discipline (binds every step)

- **Architecture rule:** agents are graphs; the world is a mechanical adapter;
  every social/economic/build/communicate DECISION is a graph rule or a
  mechanical read of graph state. Zero `graph_rewrite.run` / `gr.run` / `_match`
  / `_apply` / `make_rule` in new code. Source-audit reported.
- **Ideally NO new Rust Term** — the language faculty already exists. If a new
  Term is genuinely needed, STOP and report rather than adding it. `runners/dsl`
  diff EMPTY; canonical `.so` md5 UNCHANGED (record start==end, real file); own
  engine build; `source_match=own`.
- **Oracle** `rung7_vision_bench.sh` BEFORE==AFTER; `per_area_settlement_
  regression.sh` fail-set node-id SET identical before==after; ZERO new reds.
- **Additive `langsim_` / `LANGSIM` files only**; explicit `git add <path>`,
  never `git add -A`; touch no existing tracked file. Any new seed
  `self_load_only`, default-OFF.
- **Do NOT merge to main, do NOT write the ledger row.** Commits stay on branch.

## 6. Expected honest outcomes (pre-stated, so the map can surprise us)

Pre-flagged expectations (stated so a null is legible, NOT a hypothesis to
defend): generation of the SEEDED speech-act frames will render; aptness will
**degrade for verb-argument and multi-argument frames** outside the grounded
"of"-relation render rule; referent grounding will resolve when the resource
`Concept` exists and fail silently when it does not; comprehension will resolve
content nouns but may drop verb/intent structure; the intact-vs-scrambled gate
will separate iff comprehension actually carries content. The RANKING of these
is the result — measured, not assumed.
