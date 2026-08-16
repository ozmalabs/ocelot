# PROGRAM SYNTHESIS META-SKILL ASSESSMENT — investigation only, no build

**Headline finding, corrected against the data (see §4 for the
re-derivation): the "51 of 52 ops have zero Γ productions" framing this
assessment started with is the WRONG GRAIN, and fixing the grain changes the
answer. The atomic unit of Γ-production authoring is not "one op," it is
"one evidence-gate site" — and `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §1.1`
has ALREADY, in the same document that diagnosed the 2/52 gap, fully
enumerated all 11 evidence flags and all 14 gate sites, by exact source line,
predicate, and admitted op(s), and §3.2 has already demonstrated the
transcription recipe (Rust `if` → Γ `where_` Term) twice, on the two
productions that shipped. Porting the other 12 gate sites is not 12 separate
research problems and not a meta-skill — it is a bulk transcription pass over
data that already exists verbatim in the diagnosing document, deliberately
deferred only for single-variable rung discipline (prove parity on 2 before
doing 14), a precondition this arc has already met (the 2-production slice
shipped, GO). This is cheaper than a meta-skill: it is the codebook-load
floor the standard demands, and the codebook is pre-written.**

**One genuine, build-ready meta-skill does exist, and it is smaller and more
targeted than any of the three candidates as originally posed: the offline
mint-sweep harness both `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §6` and
`DERIVED_OPERATOR_TIER_RESULTS.md §5` independently design (force a
not-yet-admitted op or derived-op template into a failing task, check
held-out-row agreement, novelty-guard, mint) — named explicitly by the
derived-operator doc as shareable as ONE harness across both populations
(§6 cross-synergy, quoted in full below). This is real new machinery, not
built in either lineage, but it is ONE mechanism that closes two named
residual clusters at once (Γ productions beyond the known 14 gates; the
derived-operator registry's total absence of a corpus-wide candidate search,
not "no candidates exist" — only one was ever checked, ad hoc, and it was
negative). It is correctly gated behind the codebook-load above (prove the
sweep rediscovers the SortBy/task-64 fact automatically before trusting it
with anything novel).

`SynthesisOperatorShape` (Rung 4) is the one candidate that is genuinely NOT
a codebook-load-in-disguise — checked directly against
`STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §4.3`, no MBPP task's own `why`
column has ever cited an operator-shape mismatch as its blocker, so unlike
the Γ table there is no known, already-enumerated backlog of shapes sitting
unauthored anywhere in this arc's documents. Its population is still
measurably 2 (per `git log`) not because a growth mechanism is missing, but
because nothing has yet produced the DATA a growth mechanism — or a bulk
authoring pass — would consume. This is the one place in the whole
assessment where "wait, don't build yet" is the correct call, and it is
correct for a different reason than the assessment's first pass gave it.

Of the ~70 residuals enumerated in Part 1, most of the rest are **category
(a) missing primitives** (the sanctioned, already-working hand-authored-Rust
pathway — not a meta-skill gap) or **category (c) something-else** (a
verification mechanism explicitly named as neither sd-loop-shaped nor
Γ-shaped; an information-theoretic floor with no fix at any layer; a
search/pruning-cost seam; and a plain bookkeeping gap — remaining
already-built `TermNode` variants absent from the `OP_TABLE` registry).

The live agent's own gap-finding machinery (Part 2) confirms, mechanically
and without prompting, that program synthesis has never been taught into its
conversational self-model: asked "how does your program synthesis faculty
work," it filed a real `SelfConcern{kind:'self_account'}` — the correct,
documented behavior for a faculty it holds no account of (CLAUDE.md's
`note_self_account_gap`) — rather than fabricating an answer. This is
informative about the boundary between the engineering subsystem and the
conversational graph, not about the engineering subsystem's own remaining
work, and is reported as such.

---

## 1. Method

Every doc in `docs/research/program_synthesis/` touched by the recent arc
(file mtimes 2026-08-14 through 2026-08-16, confirmed by `ls -la` and `git
log --oneline`, 19 files) was read in full and mined for every sentence under
"What this document does NOT establish," "named but not built," "explicitly
out of scope," "deferred, gated on X," or equivalent framing. Each item below
is tagged with its source doc and, where the doc states one, its unblock
condition in the doc's own words. Three older `docs/research/engine_substrate/`
documents CLAUDE.md already summarizes (`SHAPE_AUDIT.md`, `META_SHAPE_FIRST_CLASS_RESULTS.md`,
`RULE_SIGNATURE_SLICE_RESULTS.md`) were read directly for their ranked-findings
section rather than re-derived, per the task's own framing that they are older
and broader than the program-synthesis arc.

Part 2 ran the two live-agent mechanisms named in the task —
`domains/self_capability_collapse.py::perceive_capability_gaps` against the
existing `seeds/self_challenge_battery.json`, and a live `WorldAdapter.converse()`
session asking direct program-synthesis questions — against a freshly booted
agent, mirroring `scripts/jabberwock_finds_its_own_gaps.py`'s own boot
sequence exactly. All output reported below is literal, not inferred.

---

## 2. Part 1 — the enumerated residual list

### 2.1 Structural-ceiling-reassessment cluster (`STRUCTURAL_CEILING_REASSESSMENT_PREREG`,
`_RUNG1_RESULTS`, `_RUNG2_RUNG3_PREREG/RESULTS`, `RUNG3_SORT_PRICING_RESULTS`,
`RUNGS_1_2_4_RECONCILIATION_RESULTS`, `CEILING_REASSESSMENT_4_PREREG/RESULTS`)

| # | Source | Residual | Unblock condition (doc's own words) |
|---|---|---|---|
| 1 | REASSESSMENT_PREREG | Rung 4 (`SynthesisOperatorShape` recognize+grow) | "after Rung 1 has shipped a few more operator-shapes to season the classifier's real drift, not before" |
| 2 | REASSESSMENT_PREREG | `term:Recurse` | re-price only after Rungs 1–3 land and enumerator headroom is re-measured |
| 3 | REASSESSMENT_PREREG | `term:Format` | none stated (1-task reach, named only to avoid being cited as a reach number later) |
| 4 | REASSESSMENT_PREREG | sd-loop-style automatic primitive mint for OP_TABLE | **rejected as a design direction entirely** — "no shape to match … a mint has never once automated building a primitive" |
| 5 | REASSESSMENT_PREREG | Re-platform DSL Term grammar onto Γ edge machinery | rejected — "no present evidence it buys anything" |
| 6 | RUNG1_RESULTS | `parse_excluded_term` not extended for 10 new Terms | none stated; P7-B repair loop silently skips |
| 7 | RUNG1_RESULTS | 22 tests show drift from widened op-table, none re-pinned | none stated |
| 8 | RUNG1_RESULTS | No per-primitive attribution for +5 tasks (`Str`/`ParseInt` unconfirmed) | none stated |
| 9 | RUNG2_RUNG3_PREREG/RESULTS | Rung 3 (`Sort`) NO-GO as scoped (collapsed to 1 unwitnessed task) | "re-open only if `boundary:SetLit` and/or `term:DictItems` are separately taken first" — **later met, see #10** |
| 10 | RUNG3_SORT_PRICING_RESULTS | Confirms #9's precondition fired: `Sort` built via `cmp_value_lex` once `SetLit`/`DictItems` landed, +5 (tasks 71,141,232,428,473) | already resolved |
| 11 | RUNG3_SORT_PRICING_RESULTS | Fraction of the +5 attributable to `Sort` alone vs. companion ops not isolated | none stated |
| 12 | RUNGS_1_2_4_RECONCILIATION | Rung 4b (structural-match recognize, `Covers`/`AntiUnifyWitness`) | **confirmed completely unbuilt** |
| 13 | RUNGS_1_2_4_RECONCILIATION | Rung 4c (mint a new `SynthesisOperatorShape` from residual) | **confirmed completely unbuilt** — zero mint/grow rules anywhere in the seed |
| 14 | CEILING_REASSESSMENT_4 | `DictFromPairs` Dict-reconstruction half untestable without writing the Term | deliberately deferred to keep the rung single-variable (later built in DICTFROMPAIRS docs) |
| 15 | CEILING_REASSESSMENT_4 | Tasks 117 (per-element coercion), 299 (groupby-aggregate-argmax), 305 (Filter+Take, untested), 417 (group-by-first-element), 470 (sliding-window pair primitive) | each below the arc's own ≥2-witness bar for a standalone rung |
| 16 | CEILING_REASSESSMENT_4 | Task 412 — search-cost/pruning puzzle (both `FilterList` and modulo already offered, still not found within 140k+ candidates) | named, not diagnosed |
| 17 | CEILING_REASSESSMENT_4 | Retrieved-exemplar fallthrough (87 tasks, 93.3% false-accept) re-confirmed | NO-GO, not reopened |

**SynthesisOperatorShape / Rung 4 population, checked directly (not
estimated):** `git log --oneline -- seeds/program_synthesis_grounding.json`
shows exactly two commits in the file's history — the initial import (2
`SynthesisOperatorShape` nodes: `thresholded_greater_branch`,
`thresholded_lower_branch`) and one later commit (`9365017`) that only
deletes the Argmax tiebreak. **The population is still exactly 2**, measured
*after* this arc landed 10 new Terms, `Sort`, `DictItems`, `SortBy`,
`GroupCount`, `DictMerge`, `Call`/derived-operator-tier, and
`IntersectAll`/`UnionAll` — none of which needed a third
`SynthesisOperatorShape`, because every one of those gains came from
op-table/typed-default exposure, never from the shape-selector layer. Rung 4
item 1's *tiebreak-deletion* half shipped (commit `9365017`, citing this
PREREG by name); the *structural-match* half of item 1 and **all** of item 2
(grow/mint) remain unbuilt — a self-consistent, honestly-gated deferral, not
an oversight.

### 2.2 Survey / scoped-fix cluster (`DICTFROMPAIRS`, `MAX_SIZE_SEAM_PRICING`,
`HOLDOUT_FAIL_SURVEY`, `PROPERTY_REJECT_SURVEY`, `STRUCTURAL_REJECT_SURVEY`,
`BUDGET_EXHAUSTED_SURVEY`, `MODSQRT_SCOPED_FIX`)

Three of these (`MAX_SIZE_SEAM_PRICING`, `HOLDOUT_FAIL_SURVEY`,
`STRUCTURAL_REJECT_SURVEY`) ship as a single PREREG file with results folded
in — confirmed, no separate RESULTS doc exists for any of the three.

| # | Source | Residual | Unblock condition |
|---|---|---|---|
| 18 | DICTFROMPAIRS | Widen `filter_templates_by_size` with an `item[k] OP rhs` index-projection template shape | explicitly "a genuinely new, unpriced, primitive-layer addition… OUT OF SCOPE for this rung" |
| 19 | DICTFROMPAIRS | Raise `max_size`/widen `DICT_DEFAULT_OPS` jointly | named, unpriced (later individually priced — see #20) |
| 20 | MAX_SIZE_SEAM_PRICING | Global `max_size` raise (measured): NO-GO — zero conversions, +2.1% wall-clock | closed, not reopened |
| 21 | MAX_SIZE_SEAM_PRICING | `max_size` not threaded through the same Rust-side spec-shape branch that already picks typed-default op lists | named as the CLAUDE.md-compliant narrow fix; not built (moot given #20) |
| 22 | HOLDOUT_FAIL_SURVEY | **A new, purpose-built generalisation-verification mechanism**, transferring across 3 call sites (retrieval / top-level-enumerate / descent-hole-enumerate) | named by two documents, never sized; yield capped at self-honesty (`accepted_holdout_fail`→`gapped`), **zero MBPP score movement by design** |
| 23 | HOLDOUT_FAIL_SURVEY | `ps_construction` field stale/mislabeled on 20/27 non-retrieval tasks | needs a Rule-level fix in `seeds/program_synthesis.json`; scope of invalidation to prior docs' per-task citations not audited |
| 24 | PROPERTY_REJECT_SURVEY | Whether the PropertyAtom-gated-fallthrough signal transfers to `structural_verdict_reject`/`accepted_holdout_fail` | named as next candidate — **answered NO by #25/#26** |
| 25 | STRUCTURAL_REJECT_SURVEY | Same pattern ported, measured: **0/10 conversions** | root cause is shared but explicitly **not a primitive-layer bug** — "a property of the population's information content" (specs underdetermined by 1–3 rows); D1/D2/D3 shape heuristics and retrieval/enumerate independently converge on the same degenerate library |
| 26 | STRUCTURAL_REJECT_SURVEY | A narrower (D1-only) fallback would convert task 109 | **explicitly refused**, quoting CLAUDE.md's Purpose section directly: "optimising the number at the cost of the understanding behind it… Not built." |
| 27 | STRUCTURAL_REJECT_SURVEY | Raise `ps_enum_reserve_budget` above 1 | "no positive evidence to justify building it," not sized |
| 28 | BUDGET_EXHAUSTED_SURVEY | **Eleven already-shipped `TermNode` variants absent from `OP_TABLE` entirely**: `Mod`, `Pow`, `Sqrt`, `BitAnd`, `BitOr`, `BitXor`, `Shl`, `Lshr`, `Ashr` (working `evaluate()` arms, unreachable — corroborated by a pre-existing source comment in `synth_enumerate.rs:2737`) | none stated beyond call-site-scoped exposure (see #32) |
| 29 | BUDGET_EXHAUSTED_SURVEY | Bitwise family (228, 399, 429) needs `Shl+BitAnd+Not` composed AND "a zip-two-lists-elementwise primitive that does not exist AT ALL in this engine" | named, not built — separate, larger primitive |
| 30 | BUDGET_EXHAUSTED_SURVEY | String-index-parity (226, 437) needs `Mod` on index AND an indexed string filter/map primitive (`IndexedMap`'s pool excludes `Str`) | named — "genuinely different, larger, 2-part gap" |
| 31 | BUDGET_EXHAUSTED_SURVEY | `Range`/iteration gap (~10 tasks) — "a NEW way for a scalar to produce a dynamically-sized list, not merely exposing an existing Term" | explicitly excluded from this rung's scope |
| 32 | BUDGET_EXHAUSTED_SURVEY | **Cross-lane regression mechanism**: `prog_moves.py::_run_synth_enumerate` calls with no explicit `ops`, silently inheriting ANY typed-default widening — "a genuine, previously-unmeasured blast radius," named as a structural gap in how regression-pricing scope is drawn generally | narrower fix (explicit `ops` override at that call site) named — **this is exactly what #33 built** |
| 33 | MODSQRT_SCOPED_FIX | Call-site-scoped `Mod`/`Sqrt` exposure — **built, GO, +3/+3/0, clean** | resolved for 2 of the 11 ops in #28 |
| 34 | MODSQRT_SCOPED_FIX | Task 92 still doesn't convert; `official`-arm residual (14,164,455,464, search-cost inflation *within* the bare-scalar branch) | not investigated further; predicted un-fixable by call-site scoping since it's not cross-lane |
| 35 | MODSQRT_SCOPED_FIX | A third scoping variant (adaptive/smaller budget for the bare-scalar branch) | "a real, plausible, entirely unpriced idea for a future rung" |

**General-mechanism framing, quoted exactly** — the survey cluster is the
only place in the arc where a residual is explicitly tested against, and
found to sit **outside**, the sd-loop/Γ dichotomy:

> HOLDOUT_FAIL_SURVEY: "a genuinely new VERIFICATION mechanism, not a missing
> primitive and not a missing admissible move."

> STRUCTURAL_REJECT_SURVEY: the shared root cause is real and general but "not
> a primitive-layer bug" — an information-theoretic floor on what the
> population's spec rows can determine, with no fix at any layer.

### 2.3 Γ-admissibility-grammar and derived-operator-tier cluster

(`OPLIST_ADMISSIBILITY_GRAMMAR_PREREG/RESULTS/SLICE1_RESULTS`,
`DERIVED_OPERATOR_TIER_PREREG/RESULTS/SLICE1_PREREG/SLICE1_RESULTS`)

| # | Source | Residual | Unblock condition |
|---|---|---|---|
| 36 | OPLIST_RESULTS §9 | §6.2 sweep-size bound ("tens to low hundreds of enumerate calls") never measured | run the first-slice Step 5 sweep |
| 37 | OPLIST_RESULTS §9 | Evidence-flag duplication (Python-duplicate vs. new Rust PyO3 exposer) left open | orchestrator decision + a Rust change (out of scope this rung) |
| 38 | OPLIST_RESULTS §9 | Template-pool population (`map_templates_by_size` etc.) argued structurally identical to the op-list case, but **no production design written** | a follow-on design rung |
| 39 | OPLIST_SLICE1_RESULTS §7 | **The offline mint sweep is NOT this rung** — never run | see Q1 below |
| 40 | OPLIST_SLICE1_RESULTS §7 | Only `SortBy`'s 2 gates converted to Γ; ~48 other evidence-gate sites remain hand-written Rust `if`s | the mint sweep, #39 |
| 41 | OPLIST_SLICE1_RESULTS §7 | Γ verdict is a parallel fact — **recorded but never consulted** by production behavior, for SortBy too | not wired this rung |
| 42 | OPLIST_SLICE1_RESULTS §7 | `SynthSpecShape` nodes unbounded/undeduplicated (one minted per `run_enumerate` call) | unsized |
| 43 | DERIVED_TIER_RESULTS §10 | Build (B), the generic pool-typed combinator | design-time estimate only, gated on a second real candidate |
| 44 | DERIVED_TIER_RESULTS §10 | Mint bar (support≥2) sufficiency | no corpus-wide false-positive rate measured |
| 45 | DERIVED_TIER_RESULTS §10 | Only one retroactive candidate tested (`JoinListSep`) and it's **negative** (support=1) | no sweep run to find a positive case |
| 46 | DERIVED_TIER_RESULTS §10 | Whether a derived-op tier ever moves MBPP pass count | measured **NO** for the one case checked (§8.2) — value is reuse/hygiene, not capability, so far |
| 47 | DERIVED_TIER_SLICE1_RESULTS §5 | Confirms none of #43–46 attempted in slice 1 either; only `Call{name,args}` + build-A fallback + `Total2` parity built, merged GO | — |

**Q1 — Γ-production coverage, and is it the "recognizer-with-no-growth"
defect shape?** Op-table size, live-counted across the arc: 31 (stale
design-time) → 50 (corrected) → **52** (`OP_TABLE`, `synth_enumerate.rs:289-381`,
counted programmatically at slice 1) — flagged in the docs as already stale
three times, "the pattern that made the prior two citations stale is
structural… `OP_TABLE` grows every time a stdlib-port rung lands." Of those
52 ops, **exactly 2 Γ Productions exist, both for `SortBy`**
(`seeds/program_synthesis_opgrammar.json`) — **51 of 52 ops have zero Γ
productions.** Direct answer: yes, functionally the same class of defect as
`recognise_meta_shape`'s pre-fix state — a hand-enumerated population with a
few authored entries and no growth path for the rest — with one precision the
docs themselves insist on: a Γ production **admits** (a generative move-set
test), it does not "recognize" the way a codebook decode does, so what's
missing is not a decode-quality fix but a **mint mechanism for Productions**,
which the doc explicitly frames as the same primitive one level up:

> OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §6.1: "This is exactly the sd-loop's
> own recognize→residual→mint discipline, one level up."

> §6.4, on why the sweep wasn't run: "Not inside `run_rules()` (too expensive
> for a per-tick fixpoint pass). Correct home: an offline script in the same
> family as `scripts/ceiling3_diag_sweep.py`… run periodically or on-demand —
> mirroring how the sd loop's OWN growth is triggered by observation ticks but
> this population's growth is triggered by a deliberately batched search
> sweep. This is a genuinely different invocation model from the rest of the
> sd-loop family and should be named as such, not silently assimilated."

**Correction, checked directly against `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md
§1.1` and §3.2 (read in full, not summarized): the "1 op of 52" framing above
is the wrong grain, and this matters for Part 3.** §1.1 is not a diagnosis
that 51 ops each need their own bespoke investigation — it is a completed
table, already read out with exact source lines, of **11 evidence flags
feeding 14 distinct branch-selection sites**, each one a direct, mechanical
`if <boolean evidence test on the spec> { admit op(s) }` — several of which
admit a whole bucket at once (`DEFAULT_STR_OPS`, `SET_DEFAULT_OPS`,
`TUPLE_BUILD_OPS`, `LIST_EXTRA_OPS`), not one op per gate. §3.2 demonstrates,
twice, the exact lossless transcription of one such gate into a Γ
`Production` (`Eq(Attr(spec,"has_dict_value"),1) → admits SynthOp{name:
"SortBy"}`, and the second `has_list_of_lists` gate the same way) — this is
the SAME recipe for all 14 gates, not a new design per gate. §8 (the
buildable-first-slice section) confirms explicitly that porting the
remaining 12 gates was excluded from the first slice **only** for
single-variable scope discipline ("prove the mechanism reproduces a fact
this codebase has ALREADY measured and shipped by hand… before trusting it
with anything novel") — not because any of the 12 needs new design. That
precondition (prove parity on 2 first) is already met: `OPLIST_ADMISSIBILITY_
GRAMMAR_SLICE1_RESULTS.md` shipped exactly those 2 productions, GO. See §4.1
below for why this makes the remaining 12 a bulk codebook-transcription pass,
not a meta-skill-shaped gap at all.

**Q2 — the named cross-synergy.** Verbatim, DERIVED_OPERATOR_TIER_RESULTS.md
§6:

> "One efficiency worth naming, not yet built: the two documents' own offline
> mint sweeps (this one's §5.4, OPLIST's own §6.4) could share ONE harness —
> try a candidate (an existing op OR a derived-op template) against a failing
> task, check held-out agreement, and on a cross-task hit, mint BOTH the
> op/template (this document) and its admissibility Production (OPLIST)
> together. Named as a real, cheap synergy; not priced or built here."

Status: purely named, never referenced again in either SLICE1 doc. Both
harnesses it would share are themselves unbuilt — this is a deferral over two
deferrals, and has nothing to attach to yet.

**Q3 — op-table size and per-op cost.** 52 entries, live-counted (see Q1).
`Call`'s build cost, measured not estimated: **~155 actual lines vs. ~60–100
estimated** for the TermNode variant itself, plus a separately-priced 278
core lines for the build-A dispatch wiring (5 files: term.rs +132,
term_variants.rs +5, jsonio.rs +12, reflect.rs +11, synth_enumerate.rs +278
core +220 tests). Forward cost, per §4/§9: **"A derived op whose arity+pool-shape
matches ONE of the six existing shapes is zero further Rust from this point
on — register it as data, done."** A derived op needing a novel pool
combination still needs new Rust (build A); build B (unbuilt) would close
that generically but is explicitly declined as premature — no second
candidate exists in the corpus.

### 2.4 Older, broader residuals from `docs/research/engine_substrate/` (context, not re-derived — per CLAUDE.md's own summary, confirmed by reading `SHAPE_AUDIT.md` §8 directly)

- The meta-shape codebook's mint path — **already fixed** (`META_SHAPE_FIRST_CLASS_RESULTS.md`), no longer a residual.
- `CapabilityAxis` identity corruption (`SHAPE_AUDIT.md` §3.1, ranked finding #5) — unfixed, live.
- 159/634 rule-carrying seeds mint edges through zero Γ productions (§8 finding #4) — corpus-scale measurement, unfixed, and explicitly caveated by its own author: "I did **not** verify at the engine level that a rule-effect `add_edge` bypasses `check_edge`… treat the 159 as a measured population, not as 159 confirmed admissibility violations."
- `import_rules_no_mirror` (Rule-side analogue of the Γ checkpoint-reload fix) — named, not built.
- The chunk-mining/e-graph question — named, not resolved, an empirical-per-corpus question.

These are real and CLAUDE.md-documented, but none of them is program-synthesis-specific, and none of the program-synthesis residuals in §2.1–2.3 depend on them being fixed first.

---

## 3. Part 2 — the live agent's own gap-finding, literal output

**(a) `perceive_capability_gaps` against the existing `seeds/self_challenge_battery.json`, as-is.** 4/5 challenges passed; 1 (`explain_planning_failure`, the battery's own deliberately-stubbed item) produced a `bare_ack` surface (`'noted'`) and minted `CapabilityGap #24500`. The battery is confirmed 100% generic-conversational (self-organisation, world-rule lookup, instruction-following, greeting, planning-failure account) — nothing in it touches program synthesis or MBPP. This run is uninformative for program synthesis **by construction**, exactly as expected going in; reported honestly rather than omitted.

**(b) Live `converse()`, literal replies:**

- Q: *"What gaps do you have in program synthesis?"* → A: *"I currently hold 8 gaps I've flagged about myself (8 implicit): (1) 'core boot integrity is compromised; inspect the linked seed-load evidence' (boot_integrity); …"* — the "in program synthesis" qualifier is ignored entirely; the gap-lister has no topic filter and dumps every held `SelfConcern`, none of which are program-synthesis-related.
- Q: *"What can't you do?"* → A: *"I am Jabberwock."* — the bare identity-fallback floor; no gap-aware content triggered.
- Q: *"How does your program synthesis faculty work?"* → A: *"I can't say precisely how I program synthesis faculty."* — ungrammatical, but functionally the honest self-account floor.

**(c) `SelfConcern`/`SelfProcess` data, verbatim.** 9 `SelfConcern` nodes minted across the session (0 existed right after boot). **1 is the on-topic finding**: `#24436 {kind: 'self_account', source: 'implicit', content: 'program synthesis faculty', status: 'noted'}` — `note_self_account_gap` firing exactly as CLAUDE.md documents: the agent holds no `SelfProcess` account for "program synthesis" (confirmed independently: of 7 `SelfProcess` nodes in the graph, zero match synth/program/code in `process`/`aliases`) and filed a gap live when asked. The other 8 minted nodes are identical `kind: 'boot_integrity'` content, 7 auto-retired by the legacy-dedup mechanism (`retire_duplicate_gap`, firing live) — unrelated background noise from the conversation ticks, not from the program-synthesis questions, reported for completeness but out of scope for this assessment.

**Assessment, as instructed, kept brief:** informative on exactly one point — program synthesis has never been taught into the agent's conversational self-model, and the machinery correctly files a real gap about that fact rather than fabricating an answer — and uninformative everywhere else (topic mismatch, exactly as predicted). This is a fact about the boundary between the Python/Rust engineering subsystem and the graph-native conversational faculty, not a finding about the engineering subsystem's own remaining work; it does not change the Part 3 ranking below.

---

## 4. Part 3 — classification and the ranked weighing

### 4.1 Classification by CLAUDE.md's own SHAPES-NOT-NUMBERS test, re-cut

The orchestrator's sharpening is correct and changes this section: a
classification that terminates in "one at a time" for the Γ-production
residual was cutting the population at the wrong grain (per-op, when the
diagnosing document itself already cuts it at per-gate, a 4x-coarser and
FULLY POPULATED table). Re-cutting by grain, not by which document happened
to name the residual, produces four groups instead of three:

**(a) Missing primitive (sanctioned Rust pathway, genuinely one Term at a
time, not a meta-skill gap):** #2, #3, #15 (all five tasks), #16, #18, #29,
#30, #31 — zip-elementwise, indexed string filter/map,
dynamically-sized-list-from-scalar, index-projection templates, per-element
coercion, groupby-aggregate-argmax, sliding-window pair. Each is a genuinely
new Rust `TermNode` or template shape with no shared structure among them
beyond "someone writes the Term" — checked directly, these do NOT reduce to
entries in any existing table the way the Γ-gate residual does. This is the
already-working pathway CLAUDE.md sanctions; none of these close by building
a meta-skill or loading a codebook, because no codebook of them exists yet.

**(b1) A codebook that already exists, fully populated, in the diagnosing
document — a bulk transcription pass, not a meta-skill:** the Γ-admissibility
grammar's remaining 12 evidence-gate sites (of 14 total; 2 shipped). This is
the corrected reading of what looked, on first pass, like "51 ops need
productions built one at a time." It is not: `OPLIST_ADMISSIBILITY_GRAMMAR_
RESULTS.md §1.1` is itself the complete table — 11 evidence flags, 14
branch-selection sites, each with its exact source line, its boolean
predicate, and its admitted op(s) (several admitting whole buckets:
`DEFAULT_STR_OPS`, `SET_DEFAULT_OPS`, `TUPLE_BUILD_OPS`, `LIST_EXTRA_OPS`,
`Replace`/`Split`/`StrCount`/`Capitalize`/`Str`/`ParseInt` together under
`spec_has_string_value`, `DictItems`/`SortBy`/`Reverse` under
`spec_has_dict_value`, etc.), and §3.2 has already demonstrated the exact,
lossless transcription recipe (Rust `if` → Γ `where_` Term expression) twice.
Porting the other 12 requires zero new investigation — the fork-(a)-vs-(b)
evidence-flag-duplication decision (§7 of that doc) is already MADE (fork
(a), Python duplication, used for the 2 shipped productions) and simply
needs to be extended to the other ~9 predicates, which are themselves
already fully specified in the same table. This is the codebook-load floor
the standard demands, at its cheapest possible form: the data was never
missing, only untranscribed, and the reason it wasn't transcribed already is
stated explicitly in the doc's own §8 as scope discipline for a FIRST slice,
not difficulty.

**(b2) A codebook that does NOT yet exist and needs a real (but shared, and
correctly scoped) discovery mechanism to populate it:** the offline
mint-sweep harness, named independently and near-identically by
`OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §6` (Γ productions for evidence-gate
combinations not yet in the Rust ladder at all — i.e., facts about the
99-task `gapped:enumerate_failed` population nobody has looked for yet, as
opposed to (b1)'s facts that are already known and just sitting untranscribed)
and `DERIVED_OPERATOR_TIER_RESULTS.md §5` (derived-op registry candidates —
the registry has only ONE real entry, and per §10's own admission **no
corpus-wide sweep was ever run to look for a second one**; the sole
candidate checked, `JoinListSep`, was found ad hoc, not by search, and is
negative). Both docs independently converge on the identical mechanism
(force a candidate in, check `found:true` AND held-out-row agreement,
novelty-guard, mint), and §6 of the derived-operator doc names the two as
literally shareable as ONE harness (quoted below). This is the one place in
this whole assessment that is genuinely a meta-skill — new machinery, not
yet built in either lineage — and it is correctly gated behind (b1): prove
the harness rediscovers the known-safe SortBy/task-64 fact automatically
before trusting it on either population.

**(b3) A codebook/grammar with a real growth mechanism precondition that is
genuinely, measurably unmet — correctly not-yet-ready, for a checked reason:**
`SynthesisOperatorShape` (Rung 4). Unlike (b1), there is no equivalent of
`OPLIST §1.1`'s table for this population — checked directly against
`STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §4.3`: "no MBPP task currently
fails FOR THIS REASON — every one of the 42 named blockers is a primitive
gap, not a selection-layer miss," confirmed by the per-task `why` column
never citing an operator-shape mismatch. There is nothing sitting
already-known and untranscribed to pour into this codebook, unlike (b1). Its
population is still exactly 2 (confirmed by `git log
-- seeds/program_synthesis_grounding.json`, two commits total, the second
only deleting a tiebreak) not because authoring is deferred by scope
discipline, but because nothing in the corpus has yet produced a THIRD
shape's worth of evidence. This is the one candidate where "don't build yet"
survives the re-cut, and for a sharper reason than the first pass gave it:
not "meta-skill not built," but "no data exists anywhere, known or unknown,
to justify building or loading anything here."

**(c) Something else entirely (named precisely, per CLAUDE.md's own closing instruction), unchanged by the re-cut:**
- **A generalisation-verification mechanism** (#22) — HOLDOUT_FAIL_SURVEY tests
  this explicitly against the sd-loop/Γ dichotomy and finds it fits **neither**:
  it is not a decoded quantity and not an admissible move, it is a check that a
  program's fit to its examples predicts its fit to held-out behavior. Its
  yield is capped at self-honesty (`accepted_holdout_fail`→`gapped`), by design
  never a score movement.
- **An information-theoretic floor** (#25) — STRUCTURAL_REJECT_SURVEY's root
  cause is real, general, and shared across two independent code paths
  (retrieval and enumerate), and explicitly **not fixable at any layer**: a
  spec underdetermined by 1–3 example rows has no primitive, no grammar
  production, and no verification mechanism that recovers information that
  was never in the input. This is not a residual any codebook or meta-skill
  closes; it is a ceiling to report and stop pushing on, exactly as the doc
  itself concludes by quoting CLAUDE.md's own Purpose section against
  building a narrower fix for task 109.
- **A search/pruning-cost seam** (#16, #34, `MAX_SIZE_SEAM_PRICING`'s own
  NO-GO) — task 412 and the `official`-arm residual are not primitive-absence
  or admissibility problems; both `FilterList` and modulo are already
  reachable and still not found within 140k+ candidates. This is the same
  *shape* of lever CLAUDE.md's own Omniglot arc named for proposal
  recall/dwell scheduling ("bins propose, continuous decides") — worth noting
  as a plausible transfer target, but nothing in this arc has scoped it as
  such.
- **A plain registry/bookkeeping gap** (#28) — the remaining already-Rust-built
  `TermNode`s absent from `OP_TABLE` is not a shape-recognition failure at
  all; it is an enumeration that was never updated when the Terms shipped,
  corroborated by a pre-existing source comment the arc found sitting
  unaddressed in `synth_enumerate.rs`. Trivial to state, non-trivial to fix
  safely — see §4.3.
- **A test/regression-scoping discipline gap** (#32) — `prog_moves.py`'s
  unscoped `ops=None` call silently inheriting typed-default widening is a
  cross-lane blast-radius bug in how the arc measures its own regressions,
  not a synthesis-capability gap. MODSQRT_SCOPED_FIX (#33) shows the fix
  pattern (explicit per-call-site `ops` override) works — GO, +3/+3/0 — but
  the gap (an audit of every OTHER unscoped call site) remains open.

### 4.2 The shared mint-sweep harness, quoted precisely (b2's real design status)

`DERIVED_OPERATOR_TIER_RESULTS.md` §6, in full:

> "One efficiency worth naming, not yet built: the two documents' own offline
> mint sweeps (this one's §5.4, OPLIST's own §6.4) could share ONE harness —
> try a candidate (an existing op OR a derived-op template) against a failing
> task, check held-out agreement, and on a cross-task hit, mint BOTH the
> op/template (this document) and its admissibility Production (OPLIST)
> together. Named as a real, cheap synergy; not priced or built here."

Both individual sweep designs (OPLIST §6.1–6.4, DERIVED §5.1–5.4) are
substantially specified — search+held-out-row methodology cited from prior
art (`CEILING_REASSESSMENT_3`'s manual precedent), a novelty guard mirroring
`sd_mint_quantum`'s own `Not(Exists(...))` idiom, a stated (if unmeasured)
cost bound (tens-to-low-hundreds of enumerate calls, not thousands), and an
explicit offline-script home (`scripts/ceiling3_diag_sweep.py`'s own family).
What is missing is not design, it is: (i) the single shared harness itself
(currently two separate paragraphs in two separate documents describing the
same mechanism), and (ii) having ever been run. Both are real, bounded,
buildable work — a genuine next-rung meta-skill, correctly distinct from
(b1)'s pure transcription and from (b3)'s "nothing to build yet."

### 4.3 Weighing the four groups, with real numbers

| Group | What it actually is | Design status | Ready now? | Named MBPP payoff |
|---|---|---|---|---|
| (b1) Γ-gate bulk transcription | Copy 12 already-fully-specified table rows into Production JSON, extending an already-made fork-(a) decision | **Complete** — the data is written out in §1.1, the recipe demonstrated twice in §3.2 | **Yes, today** | Not itself a new admitted op (Γ doesn't gate anything the Rust ladder didn't already gate) — payoff is turning a parallel, unconsulted Γ verdict into the enforced, self-repairable path CLAUDE.md's "AGENT FIXES ITSELF WHERE IT IS GRAPH-NATIVE" section asks for, for the MAJORITY of `OP_TABLE` (many gates admit whole buckets) instead of 1/52 |
| (b2) shared mint-sweep harness | New offline discovery mechanism, one harness, two consumers | Substantially designed in both docs, never merged or run | **Yes, but correctly gated behind (b1)'s parity proof** | Unmeasured but NOT capped at zero the way a narrower reading suggested — it discovers genuinely new Γ facts (beyond the known 14 gates) AND new derived-op registry candidates (a population that has literally never been searched) in one pass |
| (b3) `SynthesisOperatorShape` mint | Recognize + grow, both unbuilt | Design exists (Rung 4) but has no data to consume | **No — checked, not assumed: zero MBPP tasks cite this as a blocker** | Unknown; correctly deferred until a real task-level need appears |

This directly contradicts the assessment's first-pass conclusion that "none
of the three candidates would close a single named residual if built today."
(b1) closes the Γ-admissibility gap for the large majority of `OP_TABLE`
this week, with zero research risk, because the codebook was never actually
missing — only untranscribed. (b2) is a real, previously-unbuilt meta-skill,
correctly sized as SMALLER than "complete the whole Γ mint sweep from
scratch" (most of Γ's coverage comes from (b1), not from (b2)) and CHEAPER
than building two separate harnesses, because both documents already
describe the same mechanism. Only (b3) survives the "don't build it yet"
verdict, and it survives for the right reason: absence of data, not absence
of a growth path nobody has fed.

### 4.4 The `OP_TABLE` registration gap, and where it now ranks

The remaining already-Rust-built, `OP_TABLE`-absent `TermNode`s (#28: `Pow`,
`BitAnd`, `BitOr`, `BitXor`, `Shl`, `Lshr`, `Ashr`) and the cross-lane
blast-radius audit (#32) remain real and remain category (c) — genuinely one
Term at a time, with a proven exposure recipe (MODSQRT_SCOPED_FIX, +3/+3/0)
but no shared codebook to bulk-load, since each Term's own call-site
regression profile has to be individually checked. They rank below (b1)/(b2)
now, not because they lost value, but because (b1)/(b2) turned out to be
cheaper and more general than they first appeared.


---

## 5. What this document does NOT establish

- It does not establish that porting the remaining 12 evidence-gate sites
  (b1) is EXACTLY as trivial as the 2 already shipped — only that the design
  doc's own words describe it as the same recipe applied to already-known
  data, and that the two shipped productions are the worked proof of the
  recipe. Doing the other 12 could still surface an unforeseen wrinkle (e.g.
  a predicate whose Python duplication is less clean than `has_dict_value`'s)
  — this assessment did not write or test the transcription for the other
  12, only verified that the data and the recipe both already exist on paper.
- It does not establish that the shared mint-sweep harness (b2), once built,
  would find ANY genuinely new admissible fact beyond the known 14 gates, or
  any derived-op candidate beyond the negative `JoinListSep` case — only that
  the search has never been run, so "nothing more is out there" is an
  unsupported claim, not a measured one, in either direction.
- It does not establish that `SynthesisOperatorShape`'s "past 2 shapes"
  precondition is the RIGHT precondition — only that it has not fired, and
  that (unlike (b1)) no already-known backlog of un-authored shapes exists
  anywhere in this arc's documents to make firing it worthwhile yet. It is
  plausible the precondition itself is miscalibrated (shapes may need a new
  KIND of task pattern to grow from, not more op-table exposure or a mint
  sweep over the existing primitive population) — this assessment did not
  design or test an alternative precondition.
- It does not establish a full accounting of every MBPP task's individual
  blocker — Part 1's residual list is what the arc's own documents named as
  undone, not an independent re-derivation of the full 257-task ledger.
- It does not establish whether the older, broader `SHAPE_AUDIT.md` residuals
  (§2.4) — `CapabilityAxis` corruption, 159/634 zero-production seeds,
  `import_rules_no_mirror` — interact with program synthesis at all; they were
  read for context per the task's instructions, not investigated for
  program-synthesis relevance.
- It does not establish that the live agent's self-account gap for "program
  synthesis" (§3c) is worth closing — teaching a `SelfProcess` account is
  cheap and orthogonal to everything else in this document, named but not
  costed, since Part 2 was explicitly bounded to ~20% of total effort.
- It does not build, price with code, or run anything — every "GO"/"NO-GO"
  and every quoted design cited above is quoted from a prior document's own
  measurement or design, not reproduced or re-verified by execution here.

---

## 6. Ranked recommendation

Two of the three named candidates resolve, not to a meta-skill and not to
"no single meta-skill dominates," but to a cheaper answer the orchestrator's
own standard names as the acceptable floor: **a codebook load.** The Γ
coverage gap that looked like "51 ops, one at a time" is actually "12 table
rows, already written down, already demonstrated twice" — closing it is
data entry against a diagnosing document, not research. A second, smaller,
genuine meta-skill (the shared mint-sweep harness) is real, build-ready, and
uniquely closes two independently-named residual clusters at once. Only the
third candidate, `SynthesisOperatorShape`, is correctly not-ready — and for
the sharpest possible reason: no data exists anywhere for it to consume, not
"the growth path hasn't been built yet."

1. **Bulk-transcribe the Γ-admissibility grammar's remaining 12
   evidence-gate sites** (`OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §1.1`'s
   own table, `§3.2`'s own recipe) into Production JSON in
   `seeds/program_synthesis_opgrammar.json`, extending the seed the 2
   shipped `SortBy` productions already live in. This is the highest-ranked
   item in this assessment precisely because it is NOT a meta-skill and not
   new architecture — it is the codebook-load floor, at its cheapest: the
   data was never missing, the recipe was already proven twice, and the only
   reason it stopped at 2 was single-variable scope discipline for a FIRST
   slice, a precondition already met. Buildable first slice: extend the
   fork-(a) Python evidence-flag duplication (already built for
   `has_dict_value`/`has_list_of_lists`) to the other ~9 predicates in
   §1.1's table, author the remaining 12 Productions verbatim from the
   table, and re-run the SAME exact-set-diff parity check
   `OPLIST_ADMISSIBILITY_GRAMMAR_SLICE1_RESULTS.md` already used (zero
   regressions, zero new passes expected — this is a plumbing/coverage move,
   not a capability move, and should be measured and reported as such, not
   oversold).
2. **Build the shared offline mint-sweep harness** — one mechanism serving
   both `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md §6` (genuinely NEW Γ facts,
   beyond the 14 known gates, from the 99-task `gapped:enumerate_failed`
   population) and `DERIVED_OPERATOR_TIER_RESULTS.md §5` (the
   derived-operator registry's first-ever corpus-wide candidate search,
   since only one ad hoc candidate has ever been checked). This is the one
   genuine meta-skill this assessment recommends building, correctly gated
   behind #1: prove it first by checking whether it automatically
   REDISCOVERS the SortBy/task-64 production that a human already
   hand-verified (`CEILING_REASSESSMENT_3`'s own manual precedent) before
   trusting it with anything the corpus hasn't already confirmed by hand. Do
   not build the derived-operator tier's generic pool-typed combinator
   (build B) speculatively alongside this — let the sweep surface a second
   real candidate first, exactly as `DERIVED_OPERATOR_TIER_RESULTS.md §9`
   itself specifies.
3. **`SynthesisOperatorShape` Rung 4 — do not build.** Checked directly, not
   assumed: zero of the 42 named MBPP blockers in this arc cite an
   operator-shape mismatch, and no other document holds an un-authored
   backlog for this population the way §1.1 held one for Γ. Revisit only if
   a future rung's own residual explicitly needs a THIRD operator-shape (not
   more op-table entries, not a Γ production) to fire — and if it does,
   check first whether that need is itself just an un-transcribed table
   entry somewhere, per this document's own corrected method, before
   concluding a new mint mechanism is required.
4. **Continue the `OP_TABLE` registration grind** (`Pow`, `BitAnd`, `BitOr`,
   `BitXor`, `Shl`, `Lshr`, `Ashr`) via the proven MODSQRT_SCOPED_FIX
   call-site-scoped recipe, one Term at a time — genuinely irreducible to a
   codebook load (each Term's regression profile has to be individually
   checked against the cross-lane blast-radius risk #32 found), but with a
   proven, repeatable, measured-positive recipe already in hand (+3/+3/0).
5. **The generalisation-verification mechanism (HOLDOUT_FAIL_SURVEY) and the
   cross-lane blast-radius audit** remain real, both named as general by
   their own documents, and both worth their own small scoped rungs
   independent of 1–4 — the first for self-honesty (explicitly not
   benchmark score), the second as a prerequisite for doing #4 at scale
   without repeated `prog_moves.py`-shaped surprises.
6. **Teach the agent a `SelfProcess` account for "program synthesis."**
   Near-zero cost, orthogonal to everything above, closes the one concrete
   thing Part 2 found — worth a line item, not a rung.
