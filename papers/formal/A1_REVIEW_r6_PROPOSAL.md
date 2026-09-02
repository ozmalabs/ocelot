# Review of `A1_constructive_graphic_equalisation_implementation_referenced.tex` (draft-2026-09-02.1, r6) — proposal for fixes

Scope: the whole file (550 lines, 9 pp), its log/aux, `01_law_of_graphic_equalisation_theory_referenced.tex`
(r278, and its `.aux`) for every phrase A1 attributes to "the foundational paper" / "the theory," and
`runners/dsl/src/{rewrite,graph_rules,grammar,checker,substrate}.rs` plus `tests/` for the fifteen
conformance tests §19 says "a reference implementation should test." Line numbers are r6. Nothing
applied; nothing committed.

Compile: 0 warnings, 0 overfull/underfull boxes, 0 undefined citations, 9 pages — clean. No
`xr-hyper`/`\externaldocument` at all (01, 05 and 08 all carry it; A1 carries none). Numbering from the
`.aux`, since casual section names undercount: the ADD/REMOVE theorem is **Theorem 3.1** (§3, l.100);
the closure theorem is **Theorem 7.1**, not "5.1" (§7 "Least-fixed-point closure," l.182, because
§§4–6 intervene); the conformance list is **§19** "Conformance tests" (l.430–450), not "§17"; the
eleven lessons are **§20** (l.452–468). The findings below use the actual (r6) numbers throughout.

Headline: A1 attributes six phrases to "the theory" as if each named a specific result, and five of
the six resolve cleanly to a numbered proposition in 01 — but the sixth (the "relative-weighting
discipline" §13 rests on) does not exist in 01, which explicitly excludes "valuation algorithms" from
its own scope (01 l.57). Separately, of the fifteen conformance tests A1 says a reference
implementation "should test" (§19), at most two have a clear match anywhere in `runners/dsl/src`
under the vocabulary the paper itself uses, and the central claim of §6 (synchronous rounds, same-round
writes invisible) appears to be contradicted by how `run_rules` actually iterates rules today.

---

## A. Phrase → numbered result in 01 (six claimed, five resolve, one does not)

| A1 phrase (line) | 01 label | Match |
|---|---|---|
| "the Graph Law" (l.369, 384; also §7 title context) | `hyp:the-law` (§"The Law of Graphic Equalisation," l.934) | Exact |
| "the theory-level antecedent-state principle" (l.172) | `prop:antecedent-state` (l.941–943, subsection literally titled "The antecedent-state principle") | Exact |
| "the Graph Law's history principle" (l.372, `rem:base-is-present`) | `cor:history` ("History principle, strengthened," l.2114): "history matters only where it survives as present structure" | Exact — and note `prop:present-sufficiency` (l.2106) is the adjacent result the corollary depends on; citing both is more precise than citing the corollary alone |
| "self-admissibility as though the graph could veto the world" (l.426); lesson 2, l.458 | `prop:self-governance` ("Admissibility is self-governance, not armour," l.984); 01 itself uses the noun "self-admissibility" at l.2846 | Exact |
| "the composition's own falsifiability commitment is stated in the foundational paper" (l.51) | `sec:falsifiability` (l.2785 ff.), specifically the Composition paragraph before the enumerated list | Exact (a section reference, not a single label, but locatable) |
| "those weights must follow the theory's relative-weighting discipline" (l.310) | — | **No match.** 01 l.57: "It deliberately excludes executor design, rule scheduling, proposal records, retry protocols, **valuation algorithms**, and controller architecture." There is no numbered "relative-weighting discipline" in 01 for §13 to inherit. The nearest kin is `rem:axiom-in-bits`'s discipline (l.505: "no frame-free denominator, no absolute threshold, no evaluator standing outside every frame") and `prop:hazard-threshold`'s frame-relative ratio — both about *thresholds*, not about gauge-invariant relative *weights* between candidate deformations. §13's content (weight is only a gauge representative, offset-invariant, no absolute substrate weight) looks like original A1 content dressed as inheritance. |

**Fix.** If `xr-hyper` is adopted (worth doing — 01, 05 and 08 already do, and none of A1's five real
matches currently resolve), add `\usepackage{xr-hyper}` + `\externaldocument[GE-]{01_law_of_graphic_equalisation_theory_referenced}`
and point the five confirmed phrases at `GE-prop:antecedent-state`, `GE-cor:history` (+
`GE-prop:present-sufficiency`), `GE-prop:self-governance`, `GE-hyp:the-law`, `GE-sec:falsifiability`.
For the sixth, either (a) drop "the theory's" and own §13 as A1's own discipline (consistent with 01's
explicit valuation exclusion), or (b) if a numbered 01 result is intended, name which one — as written
it cites nothing that exists.

---

## B. The conformance-test audit (§19, l.430–450) — the fifteen items against the repository

A1 says "A reference implementation should test" fifteen properties. Checked against
`runners/dsl/src/{rewrite,graph_rules,grammar,checker,substrate,term,shape_decode,future_manifold}.rs`
(the files the task names, plus the neighbours a keyword search turned up) via `#[test]` function
names and bodies. `graph_rules.rs`, `checker.rs` and `grammar.rs` — three of the five files A1's own
formalism draws on most directly (proposal effects, admissibility, typed rules) — carry **zero**
inline unit tests.

| # | Conformance item (§19) | Found? | Where / note |
|---|---|---|---|
| 1 | enumeration-order invariance under Thm 7.1's assumptions | Partial | `rewrite.rs::parallel_batch_enumeration_is_order_identical_to_serial` — tests order-identity of one batch-apply path, not the full closure operator Thm 7.1 states conditions for |
| 2 | same-round non-readability | **Not found** | No test name or mechanism for a "round" with a frozen read-base and a fresh write-set; see §F below — the real `run_rules` loop does not appear to have this property at all |
| 3 | monotone frontier growth where monotonicity is claimed | **Not found** | `add_rule_bumps_gamma_epoch` / `add_production_bumps_gamma_epoch` (substrate.rs) test epoch bookkeeping, not frontier monotonicity of the proposal set |
| 4 | removal and freshness stratification | **Not found** | No hit for "stratif" or "freshness" anywhere in `runners/dsl/src` |
| 5 | deterministic compatible merge | **Not found** | No `merge_effects`/`compatible_merge`/`MergeResult` construct exists in `rewrite.rs` or `substrate.rs` at all — see §F |
| 6 | correct boundary identity publication | **Not found** | No `publish`/`Handle<..>`/η-style construct |
| 7 | absence of accidental cross-boundary atomicity | **Not found** | No boundary-atomicity test; `cognitive_cycle.rs::only_matching_checkin_can_cross_a_held_process_boundary` is a different (checkin-gated) boundary concept |
| 8 | stable exact-tie behaviour | Partial, different subsystems | `future_manifold.rs::equal_intervention_ties_are_kept_not_broken_arbitrarily`; `shape_decode.rs::a_genuine_tie_is_a_residual_not_the_alphabetically_first_shape`; `term.rs::attr_key_ranking_ties_break_ascending_by_key` — real tie-handling tests exist, none for A1's specific "tie scope = decision-coupling scope" (§14) construction |
| 9 | gauge invariance of relative weighting under common offsets | **Not found** | No hit for "gauge" outside H.264 codec weighted-prediction code (unrelated domain) |
| 10 | absence of a numeric weight for candidates outside the comparison domain | **Not found** | No "sentinel"/"absent dimension" test |
| 11 | provenance-preserving residual | Partial, different mechanism | `substrate.rs::gamma_residual_capture_distinguishes_different_triples` tests that Γ-admissibility *rejections* are attributed per (src,edge,tgt) triple — real provenance tracking, but for grammar-rejection residual, not A1's proposed-vs-realised `Δ^R⊖Δ^P` mismatch |
| 12 | full-proposal residual under complete non-realisation | **Not found** | `gamma_residual_capture_on_logs_one_node_per_rejection` is adjacent, not this |
| 13 | frame-local termination | **Not found** | No hit for "frame_local_terminat"/"frame.*terminat" |
| 14 | absence of hidden executor stochasticity | Not tested as such | `run_rules_opts`'s own doc comment argues its cycle-detection is exact-equality (no epsilon) "for a float relaxation," which is evidence of a deterministic *design*, but no test asserts "no RNG" |
| 15 | reproducibility of realised successors for identical antecedent configurations | Partial | `rewrite.rs::run_rules_reaches_fixed_point` — the closest real match: a deterministic fixpoint test |

**Net:** 2 of 15 have a reasonably direct match; 3 more have partial coverage in a different subsystem
under different vocabulary; 10 of 15 turned up nothing under the terms §19 itself uses, including two
(5, 6) for which the described *mechanism* — a merge function, a publication handle — does not appear
to exist in the engine at all, tested or not. This search is grep/name-based and not exhaustive (a
differently-named test could still cover the behaviour), but the paper's own §19 vocabulary is the
fair standard to search against, since that is the vocabulary a reader would use to look for it.

**Fix.** Either (a) build the missing tests against the actual engine — which first requires deciding
whether `run_rules` is meant to realise §6's synchronous-round semantics (see §F: right now it does
not), or (b) soften §19 from "should test" to "would need to test, given a conforming executor," and
say plainly, once, which of the fifteen exist today. As written, a reader has no way to tell that §19
is a wish list rather than a report.

---

## C. "WF" collides with 01's own, different, `def:well-formed`

§9 (l.215–229) defines seven typed predicates named `WF`, `WF_sym`, `WF_app`, `WF_rel`, `WF_seq`,
`WF^W_sym`, `WF_decision` — each a **binary gate**: `G⊕ΔG` (§2, l.73–79) is defined only when
`WF(G,ΔG)` holds, and `AtomicApply` (l.81–89) returns `FAIL` when it does not. A1 itself warns readers
not to conflate the seven ("These predicates validate different object types and cannot be substituted
merely because they share a name," l.228–229).

But 01 already has a `def:well-formed` (l.1317), and it is a **different kind of thing**: graded, not
binary; economic, not structural; and explicitly never gating — "Well-formedness is graded rather than
binary; it is relative to *what work* the graph is doing... and it is not enforced by the substrate.
**An ill-formed graph runs. It pays more to.**" (l.1330). A1's `WF` can produce `FAIL` and block an
operation from being applied at all; 01's well-formedness never blocks anything — it is a cost profile
a graph carries while running regardless. A1 never acknowledges the collision, despite flagging the
identical risk (same name, different referent) for its own seven predicates one paragraph later.

**Fix.** Rename A1's family (e.g. `Adm` for "admissible"/"applicable," reserving `WF` for 01's sense),
or add one sentence at l.215 disambiguating explicitly: "These are unrelated to the graded, non-gating
well-formedness of `GE-def:well-formed`; here `WF` denotes a binary applicability gate."

---

## D. Theorem 3.1 (l.100–108) — silent on WF at intermediate states

The theorem claims a finite ADD/REMOVE sequence transforms any finite `G` into any finite `H`; the
proof is "remove every fact in `G\H`, add every fact in `H\G`." §2 defines `G⊕ΔG` **only when**
`WF(G,ΔG)` holds, and `AtomicApply` `FAIL`s otherwise (l.81–89) — so whether this proof sequence is
even executable under the paper's own semantics depends on whether every intermediate state along
"remove everything in `G\H`, then add everything in `H\G`" is itself WF. The theorem does not order
the removals/additions, does not state whether WF must hold at every step or only that `G` and `H`
themselves are WF, and does not say which. (Example: if WF requires an edge's endpoints to be
present — a standard typed-graph constraint — then removing a node before removing an edge that
targets it, or adding an edge before its target node, could pass through a non-WF intermediate state,
and the "sequence" the proof asserts may not be realisable through `AtomicApply` at all without a
specific ordering.) The "intentionally weak" disclaimer immediately after (l.108: "not efficiency,
confluence, or semantic preservation") does not cover this — WF-validity of every step is a
correctness question, not a strength one, and the theorem is silent on it rather than answering it
either way.

**Fix.** Either (a) state and prove that an order exists under which every intermediate state is WF
(likely true for a reasonable WF definition, e.g. remove edges before their endpoint nodes, add nodes
before edges that use them — but this needs to be said, not assumed), or (b) restate the theorem over
`⊕` directly (not `AtomicApply`) and say explicitly that intermediate WF is not required because `⊕`
is a set-difference/union at the representation level, with `AtomicApply`'s per-step gating reserved
for the executor's actual behaviour.

---

## E. Theorem 7.1 (l.182–201) — which conditions are checkable

The theorem's **formal** hypothesis is monotonicity of `F` itself: `D_a⊆D_b ⇒ F(D_a)⊆F(D_b)`. The
**prose** then adds four more conditions in the same "if" clause: "positive derivation is monotone,
admissibility is base-stable or monotone proposal-sensitive, merge is deterministic on compatible
effects, and fresh-name invention is appropriately stratified." It is not stated whether these four are
(i) *sufficient conditions that jointly imply* the boxed monotonicity hypothesis (in which case the
boxed condition is redundant with them, and should be derived rather than co-asserted), or (ii)
*independent additional requirements* needed on top of monotone `F` (in which case they are doing
work Knaster–Tarski's classical theorem does not — order-independence of the lfp of a monotone
operator is automatic, so what precisely goes wrong without them, if `F` is already given as
monotone?).

Per-condition:
- **"positive derivation is monotone"** — restates the boxed condition in English; adds nothing
  checkable beyond it.
- **"merge is deterministic on compatible effects"** — precise enough to check in principle (does
  `⊔_D` compute a total function on compatible pairs?), though "compatible" is used but never defined
  (§6, l.170, only says "deterministic merge over compatible effects and explicit incompatibility
  otherwise" — no predicate for compatibility is given anywhere in the paper).
- **"admissibility is base-stable or monotone proposal-sensitive"** — neither disjunct is defined.
  "Base-stable" and "monotone proposal-sensitive" appear nowhere else in the document.
- **"fresh-name invention is appropriately stratified"** — "appropriately" carries the whole
  condition; no rank/stratum function is given (contrast the cited Datalog stratified-negation
  precedent, which has an explicit stratum ordering).

**Fix.** A precise statement needs: a definition of "compatible effects" (used at l.170 and here
without one); definitions of "base-stable admissibility" and "monotone proposal-sensitive
admissibility" as predicates over the admissibility function, with the disjunction's role stated
(why is *either* sufficient?); an explicit stratification function for fresh-name minting sites,
analogous to a Datalog stratum number; and a decision on whether the four prose conditions are meant
to *entail* the boxed hypothesis (then prove it and drop the redundancy) or *supplement* it (then say
what specifically the boxed condition alone fails to guarantee).

---

## F. Does `run_rules` actually have "same-round non-readability" (§6, l.164)?

§6 states the semantics being formalised: "Every rule in round `k` reads the same `g̃^(k)` and writes
to a fresh `E^(k)`. Same-round writes are not visible." §5 (l.122) explicitly identifies this
`ProposalClosure` with the code-level `run_rules`: "The formal implementation replaces the
code-oriented name `run_rules` with `ProposalClosure(...)`," implying they are the same function under
two names.

Reading `run_rules_opts` (`runners/dsl/src/rewrite.rs:2560` ff.), the actual loop is:

```rust
while steps < max_steps {
    for (rule_i, rule) in rules.iter().enumerate() {
        if rule.batch {
            if batch_apply_rule(rule, ..., graph, ...) { steps += 1; any_progress = true; }
            continue;
        }
        // cold path: enumerate bindings against `graph`, then apply one progressing binding
        ...
    }
}
```

Rules are applied **in sequence within one `while`-iteration**, mutating `graph` in place as each
rule fires; there is no separate frozen `g̃^(k)` read-base and no fresh `E^(k)` merged in afterward —
rule `i+1`'s `match_rule_each` call reads whatever `graph` looks like *after* rule `i`'s effects from
earlier in the same pass have already landed. That is the opposite of "same-round writes are not
visible." Whether this matters depends on whether any rule set in the codebase is actually sensitive
to within-pass ordering (many are not, if they're confluent), but §6 states a specific synchronous
semantics as *the* thing being formalised, and the function it names as the referent does not appear
to implement it.

**Fix.** Either (a) find the actual synchronous-round implementation if one exists elsewhere (the
task's file list — `graph_rules.rs`, `checker.rs`, `grammar.rs` — carries zero inline tests and was
not fully traced function-by-function here; it is worth checking whether one of those, rather than
`rewrite.rs::run_rules`, is the real referent), or (b) if `run_rules` is indeed the referent, correct
§6 to describe the sequential-within-pass semantics actually implemented, or (c) if synchronous rounds
are aspirational rather than descriptive, say so explicitly rather than presenting §5–§7 as "the formal
implementation replaces the code-oriented name `run_rules`."

---

## G. Bibliography

- **`ceri1989`** (l.506–509): the article title is wrapped in `\emph{...}` — "\emph{What You Always
  Wanted to Know About Datalog...}" — while the journal name, "IEEE Transactions on Knowledge and Data
  Engineering," is left plain. Every other journal entry in this bibliography does the opposite and
  correctly: Tarski (l.536–539) emphasises "\emph{Pacific Journal of Mathematics}," Lamport (l.531–534)
  emphasises "\emph{Communications of the ACM}," Cousot (l.516–519) emphasises the enclosing
  Proceedings title and leaves the article title plain. Ceri et al. is the one entry with the emphasis
  on the wrong element — exactly the "as if a book" mis-formatting the task flagged. Otherwise
  accurate: Ceri, Gottlob, Tanca, TKDE 1(1):146–166, 1989 is correct.
- **`winskel1987`** (l.541–546): content is accurate (Petri Nets: Applications and Relationships to
  Other Models of Concurrency, LNCS 255, pp. 325–392, Springer, 1987), but the entry carries three
  `\newblock`s after the author line where the parallel entry (`corradini1997`, an edited-volume
  chapter with the same shape: author(s), title, "In editors, \emph{Book}, pages, publisher, year")
  carries two. The extra `\newblock` sits mid-citation, right after "editors," and before the emphasised
  book title, producing uneven inter-block spacing between two structurally identical entries.
- **`corradini1997`, `ehrig2006`, `gray1993`, `lamport1978`, `tarski1955`, `cousot1977`**: all checked
  against the task's reference details and are accurate as formatted.
- All eight bibitems are cited in the text (checked via the citation keys against `\citep{}` uses at
  l.60, 91, 172, 203, 229, 247, 270, 473, 476, 479, 482).

**Fix.** Move the `\emph` in `ceri1989` from the article title to the journal name; drop the extra
`\newblock` in `winskel1987` to match `corradini1997`'s block structure.

---

## H. Set conventions

1. **The draft box promises what the paper doesn't have.** l.34–35: "Sections marked as falsifiability
   commitments are the intended points of attack" — this is the boilerplate sentence 01/05/08 all
   carry, but A1 has no `[shape]`/`[detail]`-tagged section at all; its only falsifiability content is
   one sentence deferring entirely to 01 (l.51: "The composition's own falsifiability commitment is
   stated in the foundational paper and is inherited here"). The box's promise is therefore false of
   this document specifically. **Fix:** either add A1's own falsifiability list for the claims that are
   A1-specific (e.g. Theorem 3.1's completeness claim, Theorem 7.1's four prose conditions, Proposition
   10.1's boundary-scoped atomicity — none of these are 01's to falsify, since 01 doesn't make them),
   or replace the box sentence with one that says plainly A1 carries no falsifiability list of its own
   and inherits 01's, dropping "Sections marked as..." since none are.
2. **`\texorpdfstring` missing on both `\date` dashes.** l.17: `\date{\textbf{Draft \textemdash\
   draft-2026-09-02.1}\\[2pt]2 September 2026 \textbullet\ document revision 6}` — plain `\textemdash`
   and `\textbullet`. 00/01/05/08 all wrap both as `\texorpdfstring{\textemdash}{---}` and
   `\texorpdfstring{\textbullet}{\textperiodcentered}` (confirmed in `01_...aux`/`.tex` l.24,
   `05_...tex` l.24, `08_...tex` l.17). A1 is the one paper in the set missing this. **Fix:** apply
   the same two wraps.
3. **Naming 01 is inconsistent, four ways.** "the companion theory of Graphic Equalisation" (l.41),
   "the foundational paper" (l.51, twice), "the theory" (bare, used at least eight times: l.53, 149,
   172, 274, 310, 428, 489), **"the theory papers" (plural, l.149)** — there is exactly one foundational
   theory paper: this plural is either a slip or silently includes the whole 00/01/0x set with no
   indication which. Bare "Graphic Equalisation" is also used at l.476, 485, 489, referring
   ambiguously to either the theory paper or the substrate/programme as a whole. This is the same
   inconsistency `05_REVIEW_r8_PROPOSAL.md` (§F.1) already flagged in a sibling paper. **Fix:** pick
   one name (01's own companion table, l.76, calls itself "The Law of Graphic Equalisation — Theory,"
   cited as "this paper" from inside 01, and would presumably be "the theory paper" from outside it),
   use it throughout, and fix l.149's plural.
4. **No implementation identifiers on the page, with one exception already flagged in the task brief:**
   l.122, `\texttt{run\_rules}`. Checked for others via `\texttt` — this is the only occurrence in the
   file, so no additional instances to fix beyond the one already known.
5. **No narration of drafting.** Checked for "was cut," "was moved," "earlier draft," "previous
   version," "retracted" — none found. A1 is clean on this point (contrast 05, which needed three such
   removals).

---

## I. The eleven lessons (§20, l.452–468) against 01

| # | Lesson (§20) | In 01 as a numbered result? |
|---|---|---|
| 1 | antecedent state is distinct from consequences of the current transition | Yes — `prop:antecedent-state` (l.941) |
| 2 | self-admissibility cannot function as armour against world-caused change | Yes — `prop:self-governance` (l.984) |
| 3 | outward action and inbound observation are different causal legs | Yes, closely — `prop:no-direct-self-alter` (l.990): "self-originated transformation ≠ outward influence ≠ inbound world forcing" is a three-way version of this two-way lesson |
| 4 | identity must be frame-typed | Yes — `thm:no-frame-free` ("No frame-free identity," l.1016) |
| 5 | failed interaction requires no persistent attempt object | **No.** 01 l.57 explicitly excludes "retry protocols" and "proposal records" from its own scope — this is A1-only, implementation-level content, consistent with rather than contradicting 01 |
| 6 | residual is mismatch and need not contain explanation | Yes, near-verbatim — 01 l.1418: "Residual is mismatch, not diagnosis. Complete non-realisation may therefore return the whole attempted deformation as residual," adjacent to `def:residual` (l.1413) and `prop:residual-inadmissible` (l.1425). **A1 reproduces this sentence almost word-for-word at l.416 without citing it.** |
| 7 | previous failure changes later dynamics only if consequences survive in state | Yes — `cor:history` (l.2114) / `prop:no-implicit-historical-state` (l.1420) |
| 8 | distinct boundaries cannot be silently treated as one primitive atomic transaction | **No** — this is A1's own `prop:boundary-atomicity` (A1 l.243), not a numbered 01 result; 01 has no boundary-atomicity proposition |
| 9 | higher-frame quantities may be first-class without being primitives of the lower graph | Yes — `prop:higher-frame` ("Higher-frame first-class structure," l.2040) |
| 10 | absent dimensions must not be represented by zero or an extreme numeric sentinel | **No**, though acknowledged generically — 01 l.134 refers forward to "the construction paper's closing list of eleven distinctions... about antecedence, identity typing, residual **and absent dimensions**," which names this lesson's topic but does not itself state a numbered result about zero/sentinel representation |
| 11 | apparent stochasticity belongs to incomplete observation, not the deterministic Graph Law | Yes — `prop:determinism` ("Graph-law determinism," l.2673) and `rem:qm-provenance` (l.2698) |

Eight of eleven are already numbered results in 01; three (5, 8, 10) are A1-only content, and 01 says
so about itself for two of them (5 via its scope exclusion, 10 via the forward-reference at l.134) —
these are not gaps in 01, they are correctly-scoped implementation content 01 declines to claim. Only
lesson 8 (boundary atomicity) is neither excluded by 01 nor pointed at by it; it is simply new.

**Fix.** Cite the eight matches (again, `xr-hyper` makes this mechanical); for lesson 6 specifically,
either cite 01's l.1418 sentence directly or drop the near-duplicate wording and instead say what A1
adds beyond it (the four-way `+`/`−` split of `Δ^R⊖Δ^P`, absent from 01's single `ϵ=δ^R⊖δ^P`). For 5,
8, 10, one sentence each noting they are implementation-only, not inherited, would pre-empt exactly
this review question.

---

## J. Not a fix for A1 — reported for 01

01 l.486: "The constructive companion is the evidence: its executor refuses that case as an explicit
incompatibility rather than residualising it" — a released paper (01) resting the evidence for one of
its own arguments (against treating incompatible collapse as union, in the discussion around
`rem:nothing-compulsory`) on A1, which is not circulated with the releasable set. The claim checks out
on A1's own text (§6, l.170: "deterministic merge over compatible effects and explicit incompatibility
otherwise"), so the dependency is real and specific, not vague — but it is 01's exposure, not A1's, and
belongs in 01's own review when 01 is next touched, not here.

---

## What is right and should not be touched

- The separation discipline itself (§1): theory is extensional, this is one executor, and the
  `AtomicApply`/`FAIL` split (§2) cleanly marks `FAIL` as implementation-only, never a theory-level
  state — stated and held consistently throughout (e.g. l.89, l.306).
- §11's causal-ordering account (publish-before-expose, l.259–266) citing Lamport/Winskel is
  well-matched: the "happened-before" partial order is exactly the right precedent for "realise ≺
  publish ≺ expose," and the citation is accurate.
- §16's `stochastic observation model ≠ stochastic substrate transition` box (l.377–382) is a clean,
  checkable distinction and correctly separates "a simulator may be convenient" from "the reference
  semantics is deterministic."
- §8's Proposition 10.1 (boundary-scoped atomicity) plus its Gray/Reuter grounding (l.247) is honestly
  scoped: it explicitly denies proving distributed atomicity impossible and instead locates it as
  additional represented structure — the right-sized claim.
- Theorem 3.1's self-description as "intentionally weak" (l.108) is the right instinct even though
  (per §D above) it doesn't cover the one gap that matters; the paper is not overclaiming what a
  representational-completeness result buys.
- §17/§21's Novelty paragraph (l.484–485) is honestly deflationary: "the individual implementation
  techniques are therefore largely established... the contribution... is their disciplined
  composition."

---

## Suggested order

1. **F** — settle whether `run_rules` is or is not the referent of §5–§7's synchronous-round
   semantics; this affects how §19's items 2 and 5 should even be tested, so it blocks B being acted on
   correctly.
2. **A** and **I** — the phrase/lesson → 01-result mapping, since it's mechanical once §F is settled and
   unblocks adopting `xr-hyper`.
3. **C** — the `WF`/well-formed disambiguation (one sentence, cheap, prevents real reader confusion).
4. **B** — decide per conformance item whether to build the test or soften the "should test" framing.
5. **D**, **E** — the two theorem precision gaps.
6. **G**, **H** — bibliography and mechanical set-convention fixes.
7. **J** — flag for 01's own review queue, not for this document.
