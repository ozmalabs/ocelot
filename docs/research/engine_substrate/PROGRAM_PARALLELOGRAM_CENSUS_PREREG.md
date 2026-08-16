# Program-parallelogram census — first slice of Proposal 2 — PREREG (investigation only)

**Date:** 2026-08-16. **Status: OFFLINE MEASUREMENT ONLY.** No agent wiring,
no seed change, no `derived_ops` entry minted into any live path, no engine
change. This is the exact, and only, deliverable
`DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md` §3 scoped for this rung:
*"First slice: OFFLINE — run the anti-unifier over the existing
accepted-Program corpus and count parallelograms with support >= 2 ... zero
agent wiring until that census says the population is real."* Script:
`scripts/program_parallelogram_census.py` (read in full before trusting any
number below — every count in this document is reproducible by running it).

**Worktree:** `/home/matt/ocelot-program-parallelogram-census`, branch
`program-parallelogram-census`, detached from `main` at `f4394fd` (verified
live: `git log --oneline -1 main` on the orchestrator's checkout showed
`f4394fd` at worktree creation time). `runners/dsl/src/term.rs:1036`
(`AntiUnifyWitness`) and `:3758` (`anti_unify_witness_values`, the doc
comment; the function itself starts at `:3768`) — the design doc's own
citations — are confirmed byte-line-identical in this worktree; no Rust was
touched or rebuilt.

---

## 0. Headline

**The corpus contains exactly ONE genuinely trustworthy, semantically
coherent, held-out-verified ≥2-witness parallelogram with a typed hole in
the primary (`full`, pass-only, 88-task) population — and the wider
population found by relaxing to "accepted" (pass + `accepted_holdout_fail`,
148 tasks) is DOMINATED by the same literal-lookup memorization defect
`DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md` §1.1/§2 already diagnosed at
the search-metric level — now independently confirmed, at the CORPUS-MINING
level, as a live hazard for Proposal 2 specifically.** Widening to the
`official` protocol arm (all parseable asserts revealed, 113 pass) finds two
more genuine parallelograms and zero additional degenerate ones — a result
that itself reproduces the design doc's own causal story (fewer revealed
rows → more room for a coincidental literal fit → more spurious template
recurrence). **The two live named clusters (task 102/411, 137/442) are
confirmed NOT in the corpus** (both still `gapped:enumerate_failed`, per
`CEILING_REASSESSMENT_7_PREREG.md`'s own NO-GO) — exactly as predicted. A
synthetic probe of their hand-verified term-trees additionally found that
**137 and 442 do not even share a Program-IR skeleton** (one wraps the
result in `Round`, the other does not) — so even if both entered the corpus
tomorrow, a naive anti-unify would NOT produce a clean parallelogram from
this pair without deeper design work, a fact the design doc's own
prompt-similarity framing did not anticipate.

**Verdict: the real population is currently too small and too
memorization-skewed to justify building the minting-rule/`derived_ops`
infrastructure this rung. This is not a null in the sense of "the mechanism
doesn't work" — the anti-unification algebra runs correctly, verified
lossless on every real family found — it is a null in the sense of
"solve one, get the cluster" not yet having enough of a corpus to solve
one from.** This mirrors this arc's own precedent for exactly this
situation (`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md`
§5.5, declining to size `SynthesisOperatorShape`'s classifier fix against a
2-entry population: *"sizing a fix from a 2-entry table would repeat
`SHAPE_AUDIT.md`'s own named mistake — a shape matcher built before there is
a shape to match"*). Full counts, the semantic breakdown, and the
admissibility check follow.

---

## 1. Method

### 1.1 Corpus source

`results/mbpp_endgame.json`, produced by `scripts/mbpp_endgame_battery.py`
(UNCHANGED, not re-run — this rung reads the artifact, it does not
re-measure the battery). Provenance, read directly from the artifact:
`head=3e7e93e804d8ec56a28d2b7c0ffdaa254650f19a`, `measured_at=
2026-08-16T18:40:37+1000`. `3e7e93e` is an ancestor of this worktree's
`f4394fd` (`git merge-base --is-ancestor` confirmed), and `git diff --stat
3e7e93e f4394fd -- runners/ domains/ substrate/ seeds/` touches only
`domains/bigville_theory_of_mind.py`, `domains/hate_attribution.py`,
`domains/psychology.py`, `domains/tom_meta_shape.py`,
`seeds/hate_attribution.json` — none in the program-synthesis path — so the
artifact is current for `main@f4394fd` and was NOT re-derived. The file is
gitignored (`.gitignore:25`) and was copied byte-identical into this
worktree (`sha256sum` matched) for the script to read; it is not committed.

Each row's `["ir"]` field is `domains.prog_synthesis.synthesize_from_
request`'s own captured accepted Program-IR
(`domains/prog_synthesis.py:2868`, `"ir": json.loads(_text(at.get
("ps_ir")))`), present for every row with `outcome in {"pass",
"accepted_holdout_fail"}` — i.e. every task whose search reached
`status=="accepted"`, confirmed by direct inspection: `full` arm, 148 rows
carry `ir`, of which 88 are `pass`.

### 1.2 What "accepted Program IR" actually looks like

Read directly from real rows before writing any grouping logic (not
assumed): the IR is a `ProgSeq{stmts:[...]}` tree. Two distinct shapes were
found live:

- **single-expression** — `ProgSeq{stmts:[ProgDefFnParam*, ProgReturn{value:
  <one Term-tree>}]}` — the classic `SynthEnumerate` DSL output
  (`Fold`/`MapList`/`FilterList`/... ) wrapped in a return statement. This is
  the grain `DERIVED_OPERATOR_TIER_RESULTS.md`'s `derived_ops`/`Call`
  design (§3) targets directly.
  `domains/prog_synthesis.py:796-802` is the construction site
  (`splice_binding`, the non-`code_write_stmts`/non-scalar-fold branch).
- **multi-statement** — `ProgSeq` with `ProgAssignVar`/`ProgForEach`/
  `ProgTupleUnpack`/nested `ProgReturn` — either a lowered scalar-fold
  (`_lower_scalar_fold_stmts`, `:756-774`) or a `code_write_stmts`-mode
  template assembled from named parts (`:786-795`, the `retrieved_exemplar`/
  `mck_*`/`ck_*`-tagged population — see §1.4).

This bears directly on the design doc's own named open question (§3
Risk/size: *"the genuinely open design question of hole-typing against the
six pool shapes"*): the `derived_ops` mechanism as designed operates on a
SINGLE Term-tree; a multi-statement program is a structurally different
grain the mechanism does not reach without further design (§4).

### 1.3 Skeleton grouping, then real `AntiUnifyWitness`/`Substitute`

Following `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §4.2's own precedent
("group by exact tree skeleton first," `scratch_rr/rr4_find_
parallelogram.py`), every accepted IR is grouped by a structural skeleton
(type tags + key sets + list lengths; leaf VALUES free) before any
`AntiUnifyWitness` call. This is not a convenience — it is a REQUIRED
precondition given a directly-observed engine property: `anti_unify_
witness_values`'s Dict arm (`term.rs:3780-3798`) generalises over **shared
keys only** and silently DROPS keys absent from either side — the exact
"Encoding C" pitfall `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §1.1 already
found and rejected at the rule grain. Unlike that document's skeleton
function, this census's `skeleton()` additionally forces **type-tag
equality** at every nested level (`scripts/program_parallelogram_
census.py:skeleton`) — a bare structural skeleton would let e.g.
`Plus{a,b}` and `Minus{a,b}` collapse into one family with the OP NAME
itself readable as a "hole," which is not executable (a `Call{name,args}`
dispatch needs a concrete op name, per `DERIVED_OPERATOR_TIER_RESULTS.md`
§3.2's own `Call` design).

For every family with support (distinct accepted tasks) >= 2, one real
`AntiUnifyWitness([ir_1, ..., ir_n])` call (N-ary — not pairwise, per
`term.rs:1027-1036`'s own doc comment: *"Evaluates `values` (a collection of
structured Values)"*) recovers the template + one witness (`sigma`) per
member, via `substrate_rs`'s generic `Substrate()._inner.evaluate()` — the
exact Python-callable pattern `scratch_rr/rr1_covers_witness_probe.py` and
`scratch_rr/rr4_transfer_at_scale.py` already established for the rule
grain, reused verbatim (confirmed live in this worktree: the Rust->Python
RETURN direction happily carries a tuple-keyed sigma dict; only the reverse,
fresh Python->Rust term-JSON INPUT, cannot, per `RULE_REFERENCE_LAYER_
SIZING_RESULTS.md` §7.2 — this rung's `verify_lossless` composes `Substitute`
INSIDE one native term-tree for exactly that reason).

### 1.4 A real engine quirk found and fixed during this rung, recorded
      rather than silently corrected

The first run of the census reported **every** real family as
`lossless=False`. Root cause, found by hand-diffing a reconstructed program
against its original: `anti_unify_witness_values`'s Tuple/List arm
(`term.rs:3801-3815`) always reconstructs `Value::Tuple(...)`
(`return Value::Tuple(Arc::new(out));`, unconditional) **regardless of
whether the original inputs were `Value::List` or `Value::Tuple`** — so a
`Substitute`d program whose IR used JSON arrays (Python `list` on the way
in) comes back as Python `tuple` at every position the algebra touched. This
is a genuine, newly-observed property of the anti-unify algebra's own
RECONSTRUCTION (it does not preserve List-vs-Tuple container identity
through a round trip) — confirmed to be a container-type relabelling only,
not information loss (the JSON-serialized content is byte-identical at every
position) — and is NOT the same defect class as the "Encoding C"
residual-loss finding above (that one drops content; this one only
relabels a container kind). The fix: `_values_equal` in the census script
compares `list`/`tuple` as equivalent (documented in the function's own
docstring) while still comparing keys/values/order/counts exactly
everywhere else. After the fix, **every real family's round trip verifies
lossless** (§2). Recorded per this arc's own house discipline (RULE_
REFERENCE's own §7 precedent: "record what nearly broke, don't silently
patch it").

A second, unrelated issue was found and fixed the same way (§4.1): the
naive synthetic-probe code initially ran `AntiUnifyWitness` across the
137/442 pair WITHOUT the skeleton precondition, hit the Dict-arm
shared-keys-only pitfall directly, and reported a bogus "1 hole" while
silently losing the non-shared sub-structure — caught, and replaced with an
explicit skeleton-match guard that refuses to run the algebra across a
mismatch and reports why instead.

---

## 2. The real census

Run: `PYTHONPATH=runners/dsl/python:. python3
scripts/program_parallelogram_census.py`. Full machine-readable output:
`results/program_parallelogram_census.json` (gitignored, regenerate by
re-running the script against `results/mbpp_endgame.json`).

### 2.1 `full` arm, pass-only (88 tasks) — THE primary, trustworthy population

| | |
|---|---|
| accepted (pass) programs | 88 |
| skeleton families | 84 |
| singleton families (no cross-task recurrence) | 81 |
| families with support >= 2 | **3** |
| — zero-hole duplicate families (byte-identical program, no template needed) | 2 |
| — real parallelograms (>0 holes) | **1** |

The one real parallelogram: **tasks 412 ("remove odd numbers from a given
list") / 426 ("filter odd numbers")**. Both `pass` (held-out-verified).
Template: `FilterList(a, __item, Eq(Mod(__item, 2), k))`, one scalar hole
`k` (`0` for 412, `1` for 426) at path `stmts.1.value.predicate.b.value`.
Round-trip verified lossless for both members. Semantically coherent — both
prompts describe the SAME operation (parity filter) with the opposite
parity constant, exactly the design doc's own "same program over different
data" framing (§3), realized for real, in the current corpus, for the first
time measured.

The two zero-hole duplicates: **{71, 141, 428}** (all "sort a list"/"sort
... by shell sort," all resolve to the bare `Sort` primitive, all `pass`)
and **{273, 282}** (both "subtract two tuples/lists element-wise," same
program, both `pass`) — genuine, correct reuse, but nothing to MINT (the
programs are already byte-identical; there is no hole to parametrize).

### 2.2 `full` arm, accepted (pass + `accepted_holdout_fail`, 148 tasks) —
     the wider population, and where the hazard shows up

| | |
|---|---|
| accepted programs (pass + accepted_holdout_fail) | 148 |
| skeleton families | 137 |
| singleton families | 130 |
| families with support >= 2 | **7** |
| — zero-hole duplicates | 2 (same two as §2.1) |
| — real parallelograms (>0 holes) | **5** |

The five, inspected individually (prompts + outcomes read directly, not
inferred from the template alone):

| tasks | outcome(s) | prompts (truncated) | verdict |
|---|---|---|---|
| 412/426 | pass, pass | remove odd numbers / filter odd numbers | **genuine** (same as §2.1) |
| 80/260/264/448 | all `accepted_holdout_fail` | nth tetrahedral number / nth NSW prime / dog's age in years / sum of perrin numbers | **DEGENERATE** — four semantically UNRELATED tasks share `IfThenElse(a%2==?, then=<LITERAL>, other=<LITERAL>)`, a pure 2-branch literal-lookup, support=4 |
| 267/271/287 | all `accepted_holdout_fail` | sum of squares of first n / sum of first n even naturals / sum of squares of first n even | **DEGENERATE** — same `IfThenElse` literal-lookup shape (different fixed condition), support=3, tasks are topically similar but the SHARED shape is memorization, not the shared arithmetic |
| 116/245 | both `accepted_holdout_fail` | tuple-to-integer conversion / max sum of a bitonic subsequence | **DEGENERATE** — two UNRELATED tasks share a `MinOver`-based literal-lookup template |
| 20/129 | pass, accepted_holdout_fail | woodball-number check / magic-square check | **MIXED-TRUST** — non-single-expression (multi-statement), one member passed its own held-out row, the other didn't; two unrelated prompts |

**Three of five (support 2, 3, and 4 respectively — i.e. higher recurrence
than the ≥2 floor) are the SAME literal-lookup memorization defect
`DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md` §1.1 diagnosed at the search
level, now caught recurring ACROSS semantically unrelated tasks in the
corpus itself.** This is new evidence, not a restatement: §1.1 measured that
the search FINDS this shape per-task; this census measures that the shape
also RECURS across tasks at exactly the cardinality (support >= 2) the
`derived_ops` mint bar would treat as evidence of a genuine reusable
primitive (`DERIVED_OPERATOR_TIER_RESULTS.md` §5.3's own bar). **A support-2
floor is necessary but was already flagged as not sufficient
(`DERIVED_OPERATOR_TIER_RESULTS.md` §5.3: "even support=2 is a floor, not a
guarantee... two tasks could share a coincidental structural similarity") —
this census is the first place that caveat is measured directly, not
theorized: 3 of 5 candidate mints in the `accepted` population would have
been memorization, if support>=2 alone were the mint trigger.**

### 2.3 `content_stripped` arm, pass-only (87 tasks) — cross-check

Identical shape to §2.1: 83 families, 80 singleton, 3 with support >= 2 (2
zero-hole duplicates, 1 real — the same 412/426 parity-filter parallelogram,
confirmed present even with the mined-chunk/bigram codebook stripped to the
8-shape starter set — i.e. this parallelogram is not an artifact of the
corpus diet).

### 2.4 `official` arm, pass-only (113 tasks) — the higher-signal cross-check

| | |
|---|---|
| accepted (pass) programs | 113 |
| skeleton families | 107 |
| singleton families | 102 |
| families with support >= 2 | **5** |
| — zero-hole duplicates | 2 |
| — real parallelograms | **3** |

All three real parallelograms are `pass`/`pass` and semantically coherent —
**zero degenerate ones found in this arm**:

- 412/426 — the same parity-filter parallelogram (§2.1).
- **16/434** (both `pass`) — "string contains sequences of lowercase
  letters joined..." / "matches a string with an a followed by one or more
  b's" — a shared regex/set-membership construction. Non-single-expression
  (multi-statement: a `ProgAssignVar` building a `set` before the return).
- **424/460** (both `pass`) — "extract only the rear index element of each
  string in the given tuple" / "get the first element of each sublist" —
  `MapList(a, __item, IndexAt(__item, k))`, one scalar hole `k` (`-1` vs
  `0`). Single-expression, lossless, semantically coherent.

**This is the sharpest single fact this census adds beyond the raw counts:
the OFFICIAL protocol (more revealed rows per task) has a strictly BETTER
genuine-parallelogram hit rate (3/3 real) than the PRIMARY protocol's wider
`accepted` population (2/5 real, once the `accepted_holdout_fail` population
is included) — which reproduces, from the corpus-mining side, the exact
causal mechanism `DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md` §1.1/§2
already named on the search-metric side: fewer revealed rows leave more room
for a small literal-lookup shape to coincidentally fit, and that risk
compounds when such shapes are then treated as candidate templates for
reuse.**

### 2.5 Deduplicated total, across every arm measured

Nine distinct (task-set) families were found across all four arms; three are
the identical 412/426 pair re-observed in three different arms (counted
once here):

- **Genuine, `pass`-verified, single-expression, admissible-today
  (§3): 412/426, 424/460 — 2 clusters.**
- **Genuine, `pass`-verified, but multi-statement (not admissible without
  further design, §3): 16/434 — 1 cluster.**
- **Mixed-trust (one member `pass`, one `accepted_holdout_fail`),
  multi-statement: 20/129 — 1 cluster.**
- **Degenerate literal-lookup memorization (all members
  `accepted_holdout_fail`), spanning semantically unrelated tasks:
  80/260/264/448, 116/245, 267/271/287 — 3 clusters.**
- **Trivial zero-hole duplicates (no template needed): 71/141/428, 273/282
  — 2 clusters.**

---

## 3. The hole-typing / admissibility check (task step 4)

**Caveat established first, directly, by the explore-agent's own reading of
`DERIVED_OPERATOR_TIER_RESULTS.md` (confirmed independently against the
current `synth_enumerate.rs`): the `derived_ops`/`Call{name,args}`
mechanism and its six-combinatorics-shape/two-pool (`general`/`list`)
admissibility taxonomy is a DESIGN PROPOSAL, not built code.** There is no
`DerivedOpRegistry`, no `Call` `TermNode` variant, and no pool-shape checker
in the tree to literally invoke — `DERIVED_OPERATOR_TIER_RESULTS.md` §9's
own verdict is "GO / NOT-YET-READY." So this section applies the taxonomy's
DOCUMENTED rules by hand to each found template, honestly labeled as a
by-hand check against a design, not a run of shipped admissibility code.

Two independent, well-defined axes, checked per family:

**(a) Structural grain** — does the template fit inside ONE Term-tree
(`is_single_expr_template`, `ProgSeq{ProgDefFnParam*, ProgReturn{value:
Term}}` only), the grain `derived_ops`/`Call` targets? Or is it a
multi-statement program (needs a larger, undesigned "program-level"
template mechanism)?

**(b) Pool fit, by hand, per `DERIVED_OPERATOR_TIER_RESULTS.md` §1.2/§3.1's
own documented rule** (`ValueTaker`-style: named args bound as Values, ONE
registered template evaluated, a param may be referenced via `Var(name)`
ANYWHERE inside the template body, not only as a direct child — confirmed
by that document's own §2.2 wording, *"possibly referencing the bound names
via `Var` anywhere inside it — including inside a `Fold`/`MapList` body"*):
every hole found in every REAL (non-degenerate) or DEGENERATE family in this
census is a bare **scalar** (an int, inside a `Lit`) — never a `list`- or
`dict`-kind hole (`all_holes_scalar_or_list: true` on every family with
`n_holes > 0`, machine-checked). A scalar hole is trivially `general`-pool
(`by_size` already carries bare literal leaves at size 1). So:

| family | single-expr | pool fit | admissible under the DOCUMENTED (not-yet-built) Build-A taxonomy |
|---|---|---|---|
| 412/426 | yes | 1 scalar hole, `general` | **YES** — `Unary`-shaped derived op (`a` fixed, `k` the one free general-pool param) |
| 424/460 | yes | 1 scalar hole, `general` | **YES** — same shape |
| 80/260/264/448 | yes | 2 scalar holes, `general` | **YES, structurally** — `Ternary`-shaped (`IfThenElse`'s `then`/`other`) — but semantically DEGENERATE (§2.2) |
| 267/271/287 | yes | 2 scalar holes, `general` | **YES, structurally** — same `Ternary` shape — DEGENERATE |
| 116/245 | yes | 2 scalar holes, `general` | **YES, structurally** — `Unary`-shaped (`MinOver`) — DEGENERATE |
| 16/434 | no | n/a | **NO** — multi-statement, outside the single-Term-tree design entirely |
| 20/129 | no | n/a | **NO** — multi-statement, same reason |

**The load-bearing finding of this section: pool-shape admissibility is
NOT the binding constraint on this corpus.** Every hole found, genuine or
degenerate, is a simple scalar that trivially fits the closed
`general`-pool taxonomy — the design doc's own named "genuinely open
question" (whether holes would match one of the six shapes) resolves, on
this corpus, mostly in the affirmative. **The actual binding constraint is
semantic soundness of the mint bar** (§2.2's finding): structural
admissibility and mint-worthiness are INDEPENDENT axes here, and on this
corpus's 5-family `accepted` population, 3 of 5 structurally-admissible
candidates are memorization. Any future minting rule built on this
mechanism needs a semantic/task-diversity check ORTHOGONAL to pool-typing,
not instead of it — pool-typing alone would pass the degenerate families
through cleanly.

---

## 4. The synthetic probe — the two named live clusters (task-step 3)

Per `CEILING_REASSESSMENT_7_PREREG.md`'s own confirmed NO-GO, live-verified
directly against `results/mbpp_endgame.json["arms"]["full"]` in this
worktree: **task 102, 411, 137, and 442 are all still
`gapped:enumerate_failed`** — none is in the accepted corpus, exactly as
that document reports and exactly as `DESIGN_REVIEW_CAPABILITY_EXPANSION_
PREREG.md` §7 item 4 anticipates ("the 318-parallelogram figure is the RULE
corpus's... not a prediction for the Program corpus"). So neither cluster
contributes to the real census in §2. This section runs a CLEARLY-LABELED
synthetic probe: the hand-verified term-trees `CEILING_REASSESSMENT_7_
PREREG.md` §4.1/§4.2 quotes (quoted from that document, NOT re-derived here)
are wrapped in the same `ProgSeq{ProgDefFnParam, ProgReturn{value:...}}`
shape real corpus rows use, and run through the identical
skeleton-then-anti-unify pipeline, to ask: IF either cluster entered the
corpus tomorrow, would this census's mechanism find it cleanly?

**Cluster 1 (102/411):** the document's own §4.1 states both tasks are
solved by the SAME term (`Fold(MapList(Split(a,"_"),item,Capitalize(item)),
item2,acc,init="",body=StringConcat(acc,item2))`) — i.e. this is not a
hole-bearing parallelogram at all; it is a stronger case, the SAME literal
program reused verbatim across two tasks (like the real `{71,141,428}`/
`{273,282}` zero-hole duplicates in §2.1/§2.2). Anti-unifying two copies of
the identical hand-built term confirms exactly this: **0 holes, round-trip
lossless.** If both tasks were solved by this term and entered the corpus,
they would land as one more zero-hole duplicate, not a template mint
candidate — consistent with, and not contradicting, the design doc's own
framing.

**Cluster 2 (137/442):** the hand-verified terms
(`Div(Count(FilterList(a,item,Eq(item,0))),Minus(Count(a),Count(FilterList
(...))))` for 137; `Round(Div(Count(FilterList(a,item,Gt(item,0))),
Count(a)),2)` for 442) **do NOT share a skeleton** — 137's core expression
is a 2-level `Div`/`Minus`/`Count` composition with no rounding; 442's
wraps a SIMPLER `Div` (denominator is bare `Count(a)`, not a `Minus`) inside
an outer `Round`. Their top-level `value` dicts share only the `"type"` key.
Per §1.3's own discipline, `AntiUnifyWitness` was deliberately NOT run
across this mismatch (it would silently drop the non-shared `a`/`b` vs
`value`/`ndigits` substructure and report a misleading single "type" hole —
verified directly during this rung before the guard was added, see
`scripts/program_parallelogram_census.py`'s `synthetic_probe()` comment).
**Finding: even if BOTH 137 and 442 were solved and entered the corpus
tomorrow, a clean parallelogram would NOT trivially fall out of this pair**
— despite the design doc's own 0.93-prompt-similarity framing (§3, cited
from `CEILING_REASSESSMENT_7 §3`'s near-duplicate scan) for the OTHER
cluster. Prompt-level similarity does not predict Program-IR skeleton
similarity for this pair; the design doc did not claim otherwise for this
specific cluster, but this is worth recording as a concrete instance where
the intuition would have been wrong.

---

## 5. Verdict: is the population real/large enough to justify the next rung?

**No, not yet, honestly reported per this arc's own house discipline
(equally valid an outcome as a GO, per this task's own instructions).**

Weighed directly:

- The mechanism WORKS — `AntiUnifyWitness`/`Substitute` run correctly on
  real Program-IR at N-ary arity, verified lossless on every real family
  (2.1-2.4), with one real engine quirk found, understood, and worked
  around (§1.4) rather than hidden.
- The population that would justify building the mint-rule/registry
  infrastructure is currently **2 admissible-today genuine clusters** in
  the trustworthy (pass-only) population, rising to **3** if the
  `official` protocol's higher-signal population is counted too — well
  below any reasonable population size to design a general minting RULE
  against (the same judgment `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_
  REASSESSMENT_PREREG.md` §5.5 already made for `SynthesisOperatorShape`'s
  2-entry table: *"a shape matcher built before there is a shape to
  match"*).
- Widening the corpus to increase the count (`accepted`, not just `pass`)
  does not help — it makes the population WORSE per-clean-signal (3 of 5
  additional candidates are memorization), and building a mint rule against
  it without a semantic-soundness gate would systematically harvest
  degenerate templates, an outcome strictly worse than building nothing.
- Neither of the design doc's own two named motivating examples (102/411,
  137/442) is in the corpus, and one of the two (137/442) would not even
  anti-unify cleanly if manually inserted — so the document's own strongest
  illustrative cases cannot yet ground a design decision either.

**What WOULD change this verdict, stated concretely for whoever revisits
this:** (a) the corpus growing substantially (more MBPP tasks converting via
Proposal 1's witness-priced-literal fix, which — per the design doc's own
§3 "composes multiplicatively with §2" — is exactly the mechanism expected
to grow this population, since it directly targets the SAME literal-lookup
degenerate shape found dominating §2.2's wider population); or (b) a
semantic-soundness/task-diversity check for the mint bar being designed
FIRST (the missing piece §3 of this document identifies, not merely support
>= 2); at that point re-running this exact script against a fresh
`results/mbpp_endgame.json` is a five-minute operation, not a redesign.

---

## 6. What this document does NOT establish

1. No agent wiring, seed change, or `derived_ops` entry was built or
   proposed as code — this is a census only, per the task's explicit scope.
2. The `official`-arm 3/3 clean-hit-rate finding (§2.4) is suggestive, not
   powered — n=3 real families is far too small to claim a general
   protocol-dependent rate; it is reported as a directional cross-check
   that reproduces an ALREADY-established causal story, not as a new
   independently-powered claim.
3. The `content_stripped` and `official` arms were analyzed at the same
   depth as `full`; cross-arm overlap beyond the 412/426 pair (e.g. whether
   any `official`-only or `content_stripped`-only family also recurs under
   a different arm's protocol at a task_id NOT examined here) was not
   exhaustively cross-referenced task-by-task beyond what §2.5 reports.
4. The admissibility check (§3) applies `DERIVED_OPERATOR_TIER_RESULTS.md`'s
   DOCUMENTED rules by hand; it does not run actual admissibility-checking
   Rust code, because none exists yet (confirmed directly, not assumed) —
   see §3's own caveat paragraph.
5. `teach_write_shape_from_example` (`domains/code_write_growth.py:234`) was
   confirmed real, tested, and NOT used to populate the corpus for this
   census — because it currently teaches ZERO live shapes: `seeds/
   code_write_constructions.json` holds exactly the 8 hand-authored
   starter shapes, `grep -c "taught_from"` over it is 0, and no test
   fixture holds a persisted taught shape either (all `teach_write_shape_
   from_example` call sites are inside individual tests/scripts and do not
   persist past one process). The design doc's "solved OR human-taught"
   framing (§3) is therefore, MEASURED here, currently "solved only" — the
   human-taught half of the corpus does not yet exist to census.
6. Whether the `MapList`/`FilterList` families found (412/426, 424/460)
   would still be found after Proposal 1's witness-priced-literal fix lands
   is not measured — that fix changes search ORDERING, not the accepted
   corpus's CONTENT for tasks that already converge under the current
   metric, so no regression is predicted, but this is not verified.
7. This document does not re-run or re-verify the 88/87/113 MBPP baseline —
   it is read directly from the already-measured, unmodified
   `results/mbpp_endgame.json` artifact, per this rung's own scope (no
   battery re-run).

---

## Reproduce

```bash
cd /home/matt/ocelot-program-parallelogram-census
git log --oneline -1                              # program-parallelogram-census, off f4394fd

# results/mbpp_endgame.json is gitignored; this worktree's copy is
# byte-identical to the one measured on main at 3e7e93e (an ancestor of
# f4394fd with no program-synthesis-path diff, verified in §1.1). To
# regenerate fresh instead of trusting the copy:
#   PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
#     python3 scripts/mbpp_endgame_battery.py

PYTHONPATH=runners/dsl/python:. python3 scripts/program_parallelogram_census.py
# writes results/program_parallelogram_census.json, prints the summary
# tables this document's §2 numbers are drawn from directly.
```
