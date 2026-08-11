# LANGSIM SYNTAX-CARRYING LANGUAGE (block 244000) — PRE-REGISTRATION

**Status: PRE-REGISTRATION. No measurements below. Written BEFORE any number.**
Block **244000**. This is a **BUILD-OUT** of the measured #1 limitation from the
langsim language-limitation map (block 243000): the substrate's graph-resident
language carries **LEXICAL** content but **NOT SYNTAX**. The deliverable is a
language faculty whose **comprehension is SYNTAX-CARRYING** — word ORDER →
structured roles — measured against the exact pre-shaped success metric langsim
already defined.

## 0. The measured target (from `LANGSIM_LANGUAGE_LIMITATION_RESULTS.md`)

Langsim proved, behind a failable control:

1. **Comprehension is ORDER-INSENSITIVE (the deepest break).** `I give wood`
   and the scrambled `wood I give` comprehend to the SAME thing — a *bag* of
   grounded referents, not a compositional parse of word order (DIM 3).
2. **The coordination channel therefore carries a word-SET, not syntax** — so in
   the coordination gate (DIM 4) the **SCRAMBLED control does NOT fail**
   (gap language−scrambled CI includes 0). Syntax carries zero information.
3. **Generation has an ARITY-2 ceiling** — a ditransitive `give X to Y` DROPS
   the recipient (DIM 1).

Langsim's own recommended top build-out (RESULTS §"RECOMMENDED TOP BUILD-OUT"):
*"Make comprehension SYNTAX-CARRYING: bind the promise utterance's roles into an
Intent's argument slots (who-gives-WHAT-to-WHOM), so the scrambled control
FAILS ... populate a structured `Intent{predicate, agent, patient, recipient}`
from the `Mention` order (the composition/Merge stage the `language.py` cascade
names but the referent layer currently bypasses), and gate `promise_in` on the
STRUCTURED role match, not mere token presence."* This block does exactly that.

## 1. The mechanism (graph-native; the composition/Merge stage already exists)

`domains/language.py` already implements a **composition / Merge** stage —
`comprehend()` runs the general, vocabulary-independent Merge rules
(`_merge_rules()`, driven on the Rust engine via `apply_rule_once`) that fill a
head sign's argument SLOTS (role + direction L/R + optional role-marker) with
adjacent saturated constituents, building a structured predicate-argument
meaning Term. It is **order-sensitive by construction** (a left-slot binds the
constituent to its LEFT; a right-slot binds to its RIGHT). The langsim
coordination path BYPASSED this — it used the referent-bag resolution
(`Mention -refers_to-> Concept`) instead.

The fix WIRES the existing composition stage into the coordination path, with a
**langsim lexicon** (graph-resident sign data) giving the verbs argument
structure:

- `give` — **3-place**: `agent` (dir L), `patient` (dir R, bare), `recipient`
  (dir R, role-marker `to`). Realises/parses `I give wood to you`.
- `have` / `need` / `want` — 2-place: `agent` (L), `patient` (R bare).
- resource/role nouns (`I`, `you`, `me`, `wood`, `stone`, …) as grounded leaves;
  `to` as a role-marker.

Comprehension = `language.comprehend(text, langsim_lexicon)` → a structured
meaning Term → mapped mechanically to `Intent{predicate, agent, patient,
recipient}`, **mirrored into the agent's live graph as an `Intent` node**
(glass-box; readable in `graph_to_dict`). Generation of the ditransitive =
`language.produce(meaning, langsim_lexicon)` — comprehension's documented inverse
over the SAME signs (surface order derived from each sign's arg dir/marker, i.e.
graph-resident lexicon data; correctness is ROUND-TRIP `comprehend(produce(m))==m`).

**Python/Rust path (pre-declared intent): NO new Rust.** The composition/Merge
faculty and the producer already exist in `domains/language.py` and run on the
existing Rust engine; the build-out is a **lexicon (graph data) + a mechanical
adapter that mirrors the parse into an Intent node and gates on structured
roles**. If a genuinely necessary Rust change surfaces during the build it will
be flagged prominently and done with full Rust-rung discipline; the pre-declared
expectation is that none is needed. `runners/dsl` diff EMPTY; canonical shared
`.so` md5 UNCHANGED (recorded start==end); own engine build; `source_match=own`.

## 2. The coordination gate (structured, replacing token-presence)

Reusing langsim's world + value economy verbatim (so the comparison is
apples-to-apples), the **only** change is the promise gate. In langsim,
`promise_in` for a receiver was set by a **bag** read (`"give" in names AND
needed-resource in names`) — order-insensitive. Here it is set by a **STRUCTURED
role match** on the comprehended Intent:

    offer_valid  ⟺  predicate == give  AND  agent ∈ {I, me}  AND  patient == receiver.needs

i.e. *the partner (agent) offers (predicate=give) the receiver exactly the
resource it needs (patient)*. A scramble that breaks word order fails to bind
`patient` to `give` (or binds the wrong role), so the structured match fails —
which is the whole point. The gate remains a mechanical read of graph state
feeding the unchanged `gb_choose_give` value rule; no new agent decision in
Python.

## 3. PRE-REGISTERED GATES (success is PRE-SHAPED by langsim)

Same three coordination arms as langsim (**language / no-language / scrambled**),
same seeding convention (`range(n_seeds)`, small integers — see §5), bootstrap
95% CIs (2000 resamples), n=40 seeds for the headline (n=20/T=25 in the pinned
test for speed, matching langsim's test).

- **G-syntax-carries (HEADLINE).** Re-run the coordination measurement with the
  structured gate. Pre-shaped success (langsim RESULTS): the **SCRAMBLED control
  now DROPS toward the no-language floor** — `gap language−scrambled` CI **> 0**
  (strictly above zero), while **intact language holds** (`gap language−none` CI
  **> 0**). Report all three arm means + CIs and both gap CIs. This is the exact
  inversion of langsim's DIM 4 partial-pass: scrambled≈language BECOMES
  scrambled≪language. **This is the load-bearing result.**

- **G-comprehension-order-sensitive.** `I give wood` and `wood I give` parse to
  DIFFERENT structured Intents (`order_sensitive` flips from langsim's `False` to
  `True`). Specifically: `I give wood` → `give{agent:I, patient:wood}`;
  `wood I give` → `patient` NOT bound to `give` (the offered resource is not the
  patient). A role-swap `wood give I` → `give{agent:wood, patient:I}` (agent and
  patient SWAPPED by order). Content-sensitivity is retained.

- **G-generation-3-place.** A ditransitive intent `give{agent, patient,
  recipient}` renders to a surface that KEEPS the recipient (`I give wood to
  you`), and round-trips (`comprehend(produce(m)) == m`). The arity-2 ceiling is
  lifted for this frame. Re-measure ditransitive aptness (recipient present)
  vs the langsim 62.5% generation baseline / the arity-ceiling finding.

- **G-glass-box.** The structured `Intent{predicate, agent, patient, recipient}`
  is a real node in the agent's live substrate, readable via `graph_to_dict`.

- **G-discipline.** Source-audit clean (ZERO `graph_rewrite` / `gr.run` /
  `_match` / `_apply` / `make_rule` in new executable code); own engine build;
  `source_match=own`; canonical shared `.so` md5 recorded start==end
  (UNCHANGED — no Rust); `runners/dsl` diff EMPTY. Oracle `rung7_vision_bench.sh`
  and `per_area_settlement_regression.sh` fail-set node-id SET identical
  before==after (my files are additive; no Rust). **Regression: the langsim
  gates (`tests/test_langsim_migrated.py`) must STILL PASS** — langsim's world +
  harness are UNTOUCHED, so its pinned limitations (order-insensitive bag
  comprehension, arity-2) remain true of the OLD path; the new path is additive.

## 4. Honest-reporting protocol (binds the results)

- **Real transcripts only.** Every reported parse/utterance is printed verbatim
  by the graph faculty in the harness; a scrambled failure is captured, not hidden.
- **The headline is the scrambled-control DROP.** If, when measured, the
  scrambled control does NOT drop (gap CI includes 0), that is reported straight
  as a failed build-out — not spun.
- **Generation path stated plainly.** The ditransitive is produced by
  `language.produce` (the language faculty's lexicon-driven inverse of the
  compositional comprehender), NOT the Rust `RenderRules` render path (which has
  the arity-2 ceiling). This is the graph-side path; it is reported as such, and
  demonstrated non-lossy by the ROUND-TRIP, not asserted.
- **Synthetic mechanism vs benchmark value SEPARATED.** This is a synthetic model
  of syntax-as-coordination; the contribution is the glass-box attribution +
  the measured gate inversion, NOT a benchmark number.
- **No number before this prereg is committed.** The `seed_claim` output is
  pasted verbatim in the results (see §5 for the honest occupancy note).

## 5. Discipline (binds every step)

- **Architecture rule:** agents are graphs; the world is a mechanical adapter;
  every decision is a graph rule or a mechanical read of graph state. The
  structured gate is a mechanical read; the composition is the existing Merge
  RULES on the Rust engine. Zero forbidden Python rule-engine calls in new code.
- **Additive `langsim_syntax` / `LANGSIM_SYNTAX` files only**; explicit
  `git add <path>`, never `git add -A`; **touch no existing tracked file**
  (langsim's world/harness/tests are UNMODIFIED — the new path is a subclass +
  new harness). A peer session shares main — its files are never touched.
- **Seed occupancy (honest, NOT clean).** `python3 scripts/seed_claim.py 244000
  244999` is **REFUSED**: it flags integers **244000** and **244100** as drawn by
  `scripts/snap_run.py` — which is **block 242000** whose `anger_arm` seeds
  `SEED_BASE+2000 = 244000` and `SEED_BASE+2100 = 244100` (an **over-cap
  overreach** of the 242000 block into 244xxx, CAVEAT-1 territory), the ONLY
  occupant reported. This block was ASSIGNED as 244000 by the supervisor; the
  overreach is pre-existing and is NOT a real 244xxx reservation. **This
  build-out's harness draws only small integers (`range(n_seeds)` = 0..39, the
  langsim precedent), so it never draws 244000/244100 — ZERO actual collision.**
  The verbatim REFUSED output is pasted in the results; the honest occupancy is
  reported, not papered over.
- **Do NOT merge to main, do NOT write the ledger row.** Commits stay on branch.

## 6. Expected honest outcomes (pre-stated, so a null is legible)

Pre-flagged (stated so a null is legible, not a hypothesis to defend): the
compositional comprehender is order-sensitive by construction, so the structured
gate SHOULD invert the scrambled control; the 3-place producer SHOULD keep the
recipient and round-trip; the langsim OLD-path gates SHOULD stay green (untouched).
The MEASURED gap-language−scrambled CI (does it clear 0, and by how much) is the
result — measured, not assumed. Residual risk pre-flagged: some random scrambles
of a 3-token utterance could, in principle, re-parse to a valid offer; the
structured gate (requiring agent∈{I,me} AND patient==need bound to give) is
designed to exclude them, and the measured scrambled arm mean is the check.
