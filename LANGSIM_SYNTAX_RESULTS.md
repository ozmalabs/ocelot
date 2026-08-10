# LANGSIM SYNTAX-CARRYING LANGUAGE (block 244000) — RESULTS

Block **244000**. Pre-registration: `LANGSIM_SYNTAX_PREREG.md` (committed
`68bea6032ac84fa0458735409cea21a4551055c2`, BEFORE any number). This is the
**BUILD-OUT** of the langsim language-limitation map's measured **#1 limitation**:
the substrate's graph-resident language carried LEXICAL content but **NOT
SYNTAX** — comprehension was ORDER-INSENSITIVE (a bag of grounded referents), so
the SCRAMBLED control could not fail. **This block makes comprehension
SYNTAX-CARRYING (word ORDER → a structured Intent), and the scrambled control
finally FAILS — the exact pre-shaped success.**

## STEP 0 — the mechanism already existed; it was BYPASSED (no LLM, no Rust)

`domains/language.py` already implements the **composition / Merge** stage its
cascade names: `comprehend()` drives the general, vocabulary-independent Merge
RULES (`_merge_rules()`) on the **Rust engine** (`apply_rule_once`), filling a
head sign's argument SLOTS (role + direction L/R + optional role-marker) with
adjacent saturated constituents — **order-sensitive by construction**. The
langsim coordination path bypassed it for a referent-bag read. This block WIRES
it in with a langsim lexicon (graph-resident sign data giving verbs argument
structure). Verbatim from the harness (own engine, no LLM, no template):

```
'I give wood'      -> give{agent:I,  patient:wood}                 (order assigns roles)
'wood I give'      -> give{agent:I,  patient:None}  + [wood]       (scramble: patient UNBOUND)
'wood give I'      -> give{agent:wood, patient:I}                  (role-swap by order)
'I give wood to you' -> give{agent:I, patient:wood, recipient:you} (3-place: recipient KEPT)
```

## THE HEADLINE — G-syntax-carries (n=40 seeds, T=30, value/agent-tick)

Same three arms, same seeding convention, same value economy as langsim (world
INHERITED verbatim; the ONLY causal change is the structured promise gate).

| arm | mean | 95% bootstrap CI | vs langsim |
|---|---|---|---|
| **language** | 3.3542 | [3.1166, 3.6042] | **identical** (3.3542) |
| **no-language** (control) | 1.3417 | [1.2466, 1.4417] | **identical** (1.3417) |
| **scrambled** (control) | **1.2983** | [1.2133, 1.3883] | **DROPPED from 3.2458 → 1.30** |

| gap | mean | 95% CI | verdict |
|---|---|---|---|
| language − no-language | 2.0125 | [1.8699, 2.1625] | CI > 0 → language coordinates (PASS) |
| **language − scrambled** | **2.0558** | **[1.8017, 2.3250]** | **CI > 0 → SCRAMBLED FAILS (HEADLINE)** |
| scrambled − no-language | −0.0433 | [−0.1817, 0.0833] | CI includes 0 → **scrambled sits AT the floor** |

**The pre-shaped success, measured.** Langsim DIM 4: `gap language−scrambled` =
0.1083 CI **[−0.2083, 0.4543]** (included 0 — scrambled did NOT fail). Here it is
**2.0558 CI [1.8017, 2.3250]**, strictly above 0, and `gap scrambled−none` now
includes 0 — **the scrambled control has dropped exactly to the no-language
floor.** Because comprehension now carries word ORDER into a structured Intent, a
word-order scramble no longer binds the offered resource to `give`, so the
structured gate refuses it. **The language−none arms reproduce langsim's numbers
byte-for-byte** — proof the economy is unchanged and the ONLY moving part is the
gate collapsing the scrambled arm. Langsim's DIM 4 went from **partial pass** (CI
above no-language only) to **FULL pass** (CI above BOTH controls).

## G-comprehension-order-sensitive — word order now assigns roles

| delivered | structured Intent | carries the offer (needs wood)? |
|---|---|---|
| `I give wood` (intact) | give{agent:I, patient:wood} | ✅ |
| `wood I give` (scrambled) | give{agent:I, **patient:None**} | ❌ — patient not bound to give |
| `wood give I` (role-swap) | give{**agent:wood, patient:I**} | ❌ — roles swapped by order |
| `I give stone` (wrong resource) | give{agent:I, patient:stone} | ❌ — content wrong |

`ORDER-SENSITIVE: True` (langsim: **False**). `CONTENT-SENSITIVE: True`
(retained). `ROLES-SWAPPED-BY-ORDER: True` — `wood give I` puts `wood` in the
agent slot and `I` in the patient slot, the mirror of `I give wood`. Word order
is now load-bearing; the scramble that langsim's bag comprehension shrugged off
now changes the structured meaning.

## G-generation-3-place — the ditransitive keeps the recipient (arity ceiling lifted)

Aptness (recipient present AND round-trips) = **100% (3/3)** vs langsim's
ditransitive, which DROPPED the recipient (`give X to Y` → `give X`):

| intent | rendered surface | round-trips? |
|---|---|---|
| give{I, wood, you} | `I give wood to you` | ✅ |
| give{you, stone, me} | `you give stone to me` | ✅ |
| give{I, grain, you} | `I give grain to you` | ✅ |

**Path taken: graph-side / Python, NO Rust.** The ditransitive is produced by
`language.produce` — the language faculty's documented inverse of the
compositional comprehender, over the SAME graph-resident signs (surface order
derived from each sign's arg dir/marker; correctness is the ROUND-TRIP, shown
above, not asserted). This is NOT the Rust `RenderRules` render path, which
carries the langsim arity-2 ceiling — stated plainly per the prereg. The
recipient slot is carried because the `give` sign is given three argument slots
(`agent` L, `patient` R bare, `recipient` R marker `to`); the SAME 3-slot sign
parses the 2-place `I give wood` (recipient simply unfilled) and the 3-place
`I give wood to you` (recipient bound).

## G-glass-box — the structured Intent is a live-graph node

The composed Intent is mirrored into the listener's live substrate as an
`Intent{predicate, agent, patient, recipient}` node (`has_intent` edge from the
Message), readable via `graph_to_dict`. Verbatim (roles absent from the parse
stored as `''`):

```
last_intent_node('I give wood') -> {'predicate':'give','agent':'I','patient':'wood','recipient':''}
graph_to_dict has an Intent node: True
```

Gated by `test_structured_intent_is_a_node_in_the_live_graph`.

## Python-vs-Rust path — NO RUST (preferred path taken)

Both sides were done **graph-side, with ZERO new Rust**:

- **Comprehension** = the existing `domains/language.py` composition/Merge RULES
  on the Rust engine, driven by a langsim lexicon (graph data). No new Term, no
  engine change.
- **Generation (3-place)** = the existing `language.produce` faculty inverse over
  the same signs. No engine change.

`runners/dsl` diff EMPTY; no `term.rs` / `runners/dsl` change. The Rust
`RenderRules` render engine was left untouched — its arity-2 ceiling remains
(langsim's OLD path still exhibits it, pinned by the regression). The build-out
is a **lexicon (graph data) + a mechanical adapter** (structured-Intent mirror +
structured gate).

## Discipline / provenance ledger

- **base SHA:** `98ab428ae9d90b5859ad2bfdad92c913a48316b0`.
- **prereg commit (clean, before any number):** `68bea6032ac84fa0458735409cea21a4551055c2`.
- **engine:** built in THIS worktree from committed source (`cargo build
  --release`), md5 **`10f65be659e0d9a9290aff39f7f5b92a`**, provenance **own**
  (`source_match=own`; byte-identical to block 243000's own-engine hash → same
  Rust source, ZERO Rust change). Loaded native is this worktree's own build.
- **canonical shared `.so`:** `fd82dc2978dbb055496dd82390ac2ebe` at START and END
  — **UNCHANGED** (never written through — my build targets THIS worktree's
  `runners/dsl/python/substrate_rs/_native.abi3.so`, not the canonical tree).
- **`runners/dsl` diff:** EMPTY — **ZERO Rust added.** No new Term.
- **source_match: own** — every new file is `langsim_syntax` / `LANGSIM_SYNTAX`
  under block 244000; **no existing tracked file edited** (langsim's world,
  harness, and tests are byte-UNCHANGED — the new path is a `LangSimWorld`
  subclass + new harness + new tests).
- **source-audit:** 0 forbidden Python rule-engine calls (`graph_rewrite` /
  `gr.run` / `_match` / `_apply` / `make_rule`) in executable code of the new
  files (`tests/test_langsim_syntax_migrated.py::test_no_forbidden_rule_engine_calls_in_new_files`).
- **Oracle `rung7_vision_bench.sh`:** **214 passed, 10 skipped** (AFTER; `data/`
  absent — the documented 214-without / 224-with figure, IDENTICAL to block
  243000). BEFORE == AFTER (my files are additive and excluded from the script's
  fixed vision-test file list; no Rust, so the engine behaviour is byte-identical
  to canonical source). `test_engine_provenance_migrated` PASSED inside it →
  provenance **own**. ZERO new reds.
- **Oracle `per_area_settlement_regression.sh`:** **23 failed, 278 passed, 5
  skipped** (AFTER). The fail-set node-id SET is IDENTICAL before == after by
  CONSTRUCTION: the script runs a FIXED named file list (block 186000); NONE of
  my files are in it, and NONE of the listed test files import
  `langsim_syntax` / `langsim_syntax_world` / the syntax harness; no Rust, so the
  engine is byte-identical. The 23 reds are the **pre-existing environment
  baseline** — all in conversation / topic-route / gap-awareness / elaboration /
  cortices-tick / composer-driver areas (FileNotFoundError from absent `data/`,
  frozen-baseline drift, daemon-reconcile assertions) — and **ZERO are in
  `langsim_syntax`**. My additive files cannot reach any of them. ZERO new reds.
  Enumerated AFTER fail node-ids (= the before-set by construction):
  `test_composer_driver_migrated::test_question_driver_parity`;
  `test_cortices_tick::{test_crow_report_byte_identical_via_tick,
  test_nested_lion_mouse_reciprocity_via_tick,
  test_ticked_reading_matches_run_reading_flow_report}`;
  `test_elaboration_migrated::{test_detail_request_minted_and_chain_ingested,
  test_expand_synonym_also_serves, test_more_without_detail_falls_through_to_summary,
  test_plain_anaphora_uses_summary_not_serve,
  test_progressive_disclosure_serves_next_chunk_each_time}`;
  `test_gap_awareness_migrated::{test_gaps_are_deduped_by_content,
  test_implicit_gap_is_filed_once, test_implicit_unresolved_topic_files_a_gap,
  test_resolved_topic_files_no_gap,
  test_unaccounted_self_faculty_files_a_clean_self_gap}`;
  `test_topic_route_selfheal_migrated::{test_external_topic_still_routes_with_possessive_guard,
  test_infer_3d_from_2d_image_graph_capability_reply,
  test_navigate_3d_spaces_graph_capability_reply,
  test_polar_capability_conditional_clause_not_topic_routed,
  test_polar_capability_question_honest_reply,
  test_polar_capability_with_object_still_routes_topic,
  test_reflexive_topic_question_routes_to_topic_not_self,
  test_self_heals_knowledge_gap_via_teacher,
  test_what_is_x_made_of_routes_to_topic_not_know_tail}`.
  **`test_failure_baseline_migrated` (in the list) PASSED** — it gates the live
  fail-set against the recorded `results/failure_baseline.json`, so its green is a
  POSITIVE check that my changes introduced ZERO new reds, not merely a structural
  argument.
- **langsim regression:** `tests/test_langsim_migrated.py` STILL GREEN — the OLD
  referent-bag path is untouched, so its pinned limitations (order-insensitive
  bag comprehension, arity-2 generation) remain true of the OLD path. The new
  syntax path is additive.

### Seed occupancy (HONEST — not clean, documented)

`python3 scripts/seed_claim.py 244000 244999` → **REFUSED** (verbatim):

```
SEED CLAIM 244000-244999: REFUSED.
  OCCUPIED: 2 seed integer(s) in this range are measurably drawn by 1 file(s).
    244000: scripts/snap_run.py
    244100: scripts/snap_run.py
```

The only occupant is `scripts/snap_run.py`, which is **block 242000**
(`SEED_BASE = 242000`) whose `anger_arm` seeds `SEED_BASE + 2000 = 244000` and
`SEED_BASE + 2100 = 244100` — an **over-cap overreach** of the 242000 block into
244xxx (CAVEAT-1 territory), pre-existing and NOT a real 244xxx reservation.
This block was ASSIGNED as 244000 by the supervisor. **This build-out's harness
draws only small integers (`range(n_seeds)` = 0..39, the langsim precedent), so
it never draws 244000/244100 — ZERO actual seed collision.** Reported straight,
not papered over.

## Honest separation: synthetic mechanism vs benchmark value

This is a **synthetic model** of syntax-as-coordination. The contribution is the
**glass-box gate inversion** — a measured, CI-separated demonstration that
wiring the existing composition/Merge stage into the coordination path makes
**syntax load-bearing**: the scrambled control drops from ≈language to the
no-language floor. It is NOT a benchmark number and NOT social science. The
language−none arms are near-forced by the reused langsim economy (they reproduce
langsim exactly, by design, as the fixed reference); the evidential weight is on
the **scrambled arm's collapse** and the **order-sensitivity / role-swap** the
composed Intent now carries.

## What was NOT done (honest residuals)

- **The RUST render engine's arity-2 ceiling is NOT fixed.** 3-place generation
  uses `language.produce` (the faculty inverse), not `RenderRules`. Lifting the
  ceiling IN the Rust render path is a separate, real Rust change, deliberately
  not taken (the prereg pre-declared the graph-side path).
- **The langsim OLD path is unchanged and still order-insensitive** — by design
  (additive build-out; the regression pins the OLD behaviour). Agents choosing
  the syntax path do so via `LangSimSyntaxWorld`; the referent-bag path remains
  for backward compatibility.
- **The structured gate is scoped to the langsim promise frame** (`give` +
  agent∈{I,me} + patient==need). It is the composition/Merge faculty applied to
  this content path, not a general re-plumbing of every comprehension path in the
  world adapter (which still uses the referent layer).
- **Anaphora precision** (langsim DIM 5) is NOT addressed here — out of scope for
  the #1 limitation.
