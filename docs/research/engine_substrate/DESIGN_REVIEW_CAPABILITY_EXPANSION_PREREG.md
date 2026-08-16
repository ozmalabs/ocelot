# Design review — capability expansion proposals — PREREG (investigation only)

**Date:** 2026-08-16. **Status: INVESTIGATION-AND-PROPOSAL ONLY.** No code,
no seed JSON, no tests, no worktree — this document is the rung's only
artifact. Written against the working tree at `main` (recent history:
`fecd35e` "Merge progsyn-rung1-tier1", with the ceiling-reassessment-5/6/7
series landed since; the newest state read here is
`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_7_PREREG.md`, dated 2026-08-16, whose
own baseline is `main @ 03fa65d`, MBPP endgame 88/87/113). Every claim below
is grounded in a file read directly during this review; where a claim is
carried from another document's own measurement rather than re-derived, the
carrying document is named and the claim is not upgraded beyond what it
established.

---

## 0. Headline

**The sharpest place in this codebase where a number currently stands where a
shape belongs is the program-synthesis search's own cost function — and it is
a site that did not exist when `SHAPE_AUDIT.md` was written.** `SynthEnumerate`
orders candidates by uniform node count (*"size = 1 (the node) + sum of child
sizes; leaves are size 1"*, `runners/dsl/src/synth_enumerate.rs:82,962-963`),
and its constant-pool construction registers **every whole revealed-output
string as a size-1 `Lit` leaf** (`synth_enumerate.rs:2801-2808` — every whole
string value observed in the outputs, plus every character, pushed into
`const_set`; integer-valued outputs likewise at `:2767-2778`). Under that
metric, quoting the observation costs exactly as much as abstracting over it:
`Lit('PythonProgram')` prices identically to `Var(a)`. This single pricing
decision is, mechanically, the entire "Occam-ordering wall"
`CEILING_REASSESSMENT_7_PREREG.md §5` just measured — the size-7 two-branch
literal-lookup that memorizes both revealed rows Occam-outranks the genuine
size-11 composition, 5 out of 5 times on the string-shaped probe set, and the
60-task `accepted_holdout_fail` bucket plus `RETRIEVAL_FALLTHROUGH_RESULTS.md`'s
56/60 wrong-on-held-out probe are the same field measured from two other
directions. **The fix this document proposes (§2) is not a budget raise, a
threshold, or a filter — it is to make the search's Occam metric the
substrate's own compression principle: a literal's cost is its description
length given its witnesses, so a candidate that must quote the observation
pays for the observation.** Three further proposals follow: data-only growth
of the operator inventory via program-grain anti-unification over the
already-shipped `Call`/`DerivedOpRegistry` path (§3), making the built-but-
advisory-only synthesis Γ load-bearing (§1.4, folded into §2's second slice),
and giving the gap-awareness machinery eyes on the engineering subsystems it
currently cannot see (§4). A ranked recommendation with known-safe first
gates closes the document (§6).

---

## 1. Where the two generative primitives are NOT yet load-bearing — findings
     with fresh eyes, scoped to what `SHAPE_AUDIT.md` did not already name

`SHAPE_AUDIT.md` (read: §0 summary, section structure, §5 Pattern-D findings
and rejections) already inventories 40 confirmed sites; none are re-derived
here. The five findings below are either **new sites landed after that audit's
baseline** (`abae030`) or cross-document syntheses the audit's per-site method
could not see.

### 1.1 The Occam metric itself is a uniform count — a number where a shape
      belongs, in the search's own foundation (NEW SITE)

The enumerator is this codebase's third generative engine (alongside the sd
loop and Γ): it generates admissible Term-trees in cost order. Its cost model
is `size = 1 + Σ child sizes`, leaves 1 (`synth_enumerate.rs:82`; restated at
`:962-963` for the hidden-Var accounting). `DERIVED_OPERATOR_TIER_RESULTS.md
§1.1` even describes this as *"MDL/Occam-ordered by increasing size"* — but a
uniform node count is not MDL. MDL prices a symbol by its description length
under the model's own codebook; uniform counting asserts every leaf carries
equal information. That assertion is false in exactly the way that matters:
a 14-character string quoted verbatim from a revealed output row carries the
entire observation's information, and the current metric charges it one unit.

This is the SHAPES-NOT-NUMBERS failure mode — "a scalar knob is the unpaid
debt" — sitting inside the subsystem's most load-bearing loop, and it
post-dates the audit: the audit's Pattern-E sweep looked for rates and
thresholds, not for a cost model whose uniformity IS the scalar assumption.
The measured consequences, all from this week:

- `CEILING_REASSESSMENT_7_PREREG.md §5.1`: task 102's returned candidate is
  `(if (a == 'python_program') then 'PythonProgram' else 'PythonLanguage')` —
  size 7, memorizes both revealed rows, fails held-out; the hand-verified
  genuine composition is size 11 and is never reached. All 5 of 5 string-shaped
  tasks that converge at a 2,000,000 budget return this same degenerate shape,
  and all 5 fail held-out.
- `§5.3` names the generalization: with 2 revealed rows, the space of small
  literal-lookup wrong answers consumes any affordable budget before a correct
  larger composition is reached — and reassessment-6's `max_size` 9→20 raise
  made it strictly worse (the whole 9-task "saturated" population became
  budget-exhausted).
- `RETRIEVAL_FALLTHROUGH_RESULTS.md`: on the 60 `accepted_holdout_fail`-class
  tasks, the enumerator finds a syntactically complete candidate 60/60 times
  within budget — and 56/60 are wrong on held-out. The false-accept field is
  not a corner case; it is the dominant outcome of the current metric on
  under-constrained specs.

### 1.2 The constant pool prices memorization at parity with abstraction
      (the mechanism under 1.1, read directly)

`synth_enumerate.rs:2744-2809`: the pool is (a) requested consts or the
`0,1,2,-1` default, (b) **integer-valued outputs, auto-appended**, (c) every
whole input/output string and every character of each. The comment at
`:2780-2784` is explicit that string consts are *"SPEC-DERIVED ONLY"* and
*"bounded naturally by the spec's own content size"* — a sound anti-global-
alphabet discipline that nonetheless treats a whole per-row-varying output
string and a single delimiter character as the same kind of thing. They are
not: `"_"` (appears in the inputs, recurs across rows) is data the genuine
composition consumes; `'PythonProgram'` (one row's entire answer) is the
answer sheet. The pool has no witness structure — no record of whether a
literal recurs across rows, appears in inputs, or is unique to one output —
so the search cannot distinguish a reusable constant from a memorized one.
Note the same distinction the arc itself already enforces one level up: a
new primitive requires ≥2 independent witnesses
(`CEILING_REASSESSMENT_7_PREREG.md §0`'s "≥2-witness bar";
`DERIVED_OPERATOR_TIER_RESULTS.md §5`: *"single-task held-out-row agreement
is an unsafe mint bar"*, support ≥ 2 is the correct one). The literal pool
applies no such bar at the literal grain.

### 1.3 Scoped budget constants are accreting — the F-16 regress shape,
      reproducing in the newest subsystem (NEW SITES, post-audit)

`ZIP_MAX_CANDIDATES: u64 = 300_000` (`synth_enumerate.rs:255`) and
`DICT_FILTER_MAX_CANDIDATES: u64 = 300_000` (`:288`), each gated by op-name
membership in the resolved op list (`:2818-2836`), each with its own
carefully-written doc comment establishing its own measurement discipline.
Individually each is a well-run rung. Collectively they are the opening of
the F-16 regress CLAUDE.md documents verbatim — *"each rate needs a rate"* —
in budget form: each task family that hits the wall mints its own scoped
budget constant, and `CEILING_REASSESSMENT_7`'s own sweeps (2,000,000 and
5,000,000, "no principled stopping point," §5.2) are the third and fourth
knocks on that door, declined only by the rung's own restraint. A budget is a
number standing in for the shape "how much of this space is worth searching,"
and §2's proposal changes what the space costs rather than how much of it is
bought.

### 1.4 The synthesis Γ is built, verified, and load-bearing for NOTHING
      (post-audit; the cleanest open Γ gap in the tree)

`GAMMA_BULK_TRANSCRIPTION_RESULTS.md` (2026-08-16, read in full): the op-list
evidence-gate ladder is now fully transcribed as Γ productions —
`seeds/program_synthesis_opgrammar.json`, 57 `SynthOp` nodes matching live
`OP_TABLE` exactly, 13+2 productions, **420/420 real-spec parity with zero
unexplained mismatches**, and the parity check gated in CI. And §10.4 of that
document states the standing residual plainly: *"Does not wire Γ consultation
into `run_enumerate`'s real op-list construction — explicitly out of scope
per the task brief (residual #41)."* So the substrate now carries a complete,
corpus-verified admissibility grammar for op selection whose verdicts are
recorded facts that nothing consults — a Γ that generates no move set. This
is the inverse of the bigville finding (rules minting edges through zero
productions): here the productions exist and the subsystem routes around
them. The parity sweep was exactly the right way to earn trust; the earned
trust is now sitting unspent. (Folded into §2 slice 2 rather than proposed
separately — the flip is small and the parity harness is already the gate.)

### 1.5 The gap machinery cannot see the engineering self

`PROGRAM_SYNTHESIS_SELF_IMPROVEMENT_WIRING_INVESTIGATION.md` (read in full)
establishes, with cited code: synthesis failure does file
`SelfConcern{kind:'code_write'}` (`seeds/program_synthesis.json:5208-5359`,
`ps_gap_file`) and the full gap→promote→teach→resolve circle runs live in a
real-substrate test — but (a) `kind:'prog_read'` promotion falls through to a
structurally-mismatched `comprehend_first` default and is untested end-to-end
(§2 of that doc), and (b) the decomposition-tier-2/3/4 blockers and the
import-impedance survey — the named, measured ceilings of the engineering
subsystems — exist ONLY as `ArcGoal` structure and research prose, invisible
to `_run_self_gaps` and therefore to a human asking the agent "what gaps do
you have" (§5). The residual populations this review reads all day —
`enumerate_failed` 67, `accepted_holdout_fail` 60, the priced-but-unbuilt
tiers — are precisely the kind of self-knowledge CLAUDE.md's "THE AGENT FINDS
ITS OWN GAPS" section says the agent should hold, and none of it is graph.
The agent's self-model covers its conversational faculties and stops at the
door of its own engine room. §4 proposes the smallest honest fix.

### 1.6 Checked and NOT flagged (the rejections carry value too)

- **The derived-operator tier's mint discipline** (`DERIVED_OPERATOR_TIER_
  RESULTS.md §5`) is exemplary, not a defect — it derived the support-≥2 bar
  from a measured 6/6 spurious result and let that bar refuse its own
  motivating case (task 421). §3 builds on it rather than around it.
- **The A-series/`ArcGoal` split** from `SelfConcern` gap-awareness is a
  considered, correct separation (wiring investigation §5, including the
  "Seam C" warning against parsing free text into signatures) — §4
  deliberately does not propose bridging them.
- **The retrieval fallthrough NO-GO** (`RETRIEVAL_FALLTHROUGH_RESULTS.md`)
  is correct on its own terms; its 56/60 measurement is used here as
  evidence FOR §2, not re-litigated.
- **`OP_TABLE` hand-authorship** — settled by
  `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §1` (the
  primitive layer is CLAUDE.md's own sanctioned primitive-in-Rust pathway;
  no mint has ever produced interpreter code, and none should). Not
  re-opened; §3 proposes growing COMPOSITIONS as data, which that document's
  own boundary explicitly permits.

---

## 2. PROPOSAL 1 (headline) — Witness-priced literals: make the search's
     Occam metric the substrate's own compression principle

**Name:** `mdl-occam` — description-length candidate ordering with
witness-based literal pricing.

**The capability gap it closes.** Both live ≥2-witness clusters
(`102/411`, `137/442`) are hand-verified correct, zero-new-primitive, and
unreachable — not because the space is too big in absolute terms (Rust burns
5M candidates in ~8.6s, `CEILING_REASSESSMENT_7 §5.2`) but because the metric
walks the degenerate region first. Every future few-shot synthesis task —
MBPP or not — inherits the same wall, because the wall is a property of
"2 revealed rows + uniform leaf cost," not of any task. Fixing the metric is
the difference between a search that scales with budget and one that
saturates into memorization at any budget.

**Why this is shape-shaped, not another knob.** The sd loop's foundation is
dynamic quantization: recognition is compression against a held codebook, and
a residual that will not compress is what mints. A candidate program is a
CODE for the revealed rows; a candidate that must quote an output row
verbatim has compressed nothing — its "residual" is the entire observation.
Pricing a literal by its description length given its witnesses is therefore
not a new heuristic bolted onto the enumerator; it is the same principle the
substrate already runs everywhere else, applied to the enumerator's ordering.
CLAUDE.md sanctions MDL by name (the identifiability guard: *"never encode
precision the steps cannot support (MDL)"*), and the decision procedure holds
up: the cost lives in the map between candidate-space and observation-space
(a comparator), where real-valued/graded structure is legal.

**Mechanism, precisely.** In `const_set` construction
(`synth_enumerate.rs:2744-2809`), each pooled literal gets a witness census
that is already computable from data in scope (`envs`, `outputs` — no new
inputs needed):

- appears in ≥1 revealed INPUT → **data-derived** (delimiters, probe values);
- appears in ALL revealed outputs identically → **row-invariant** (a genuine
  constant of the task);
- appears in exactly ONE row's output and nowhere else → **single-witness
  output quote** — the memorization signature.

Registration cost: data-derived and row-invariant literals keep cost 1
(unchanged, byte-preserving for the arithmetic default pool `0,1,2,-1` and
all characters). A single-witness output quote registers at its description
length — for a string, its character count; for an auto-appended integer
output, its digit count. Everything downstream (`by_size`, the growth loop,
budgets, pruning) is untouched — the change is entirely "which size class a
leaf registers into," the same mechanism `list_unary_extra_cost` /
`extra_cost` on derived ops already uses to make richer constructs price
honestly (`synth_enumerate.rs:854-968,1156-1184`). The prediction is
concrete and falsifiable: task 102's degenerate lookup reprices from size 7
to ~7+2×(13-1) ≈ 31, past `max_size=20` — while the genuine size-11
composition, which quotes nothing, is unchanged and becomes the Occam-first
fit; all five of §5.1's measured spurious candidates flip the same way.

**Slice 1 (buildable, small):** the census + repricing above, strings only,
in Rust; ~40-80 lines in one file. Gates, in order: (1) **known-safe fact
first** — the full MBPP battery must re-find the current 88/87/113 with an
empty `lost_pass` list (the honest risk: a currently-passing task whose
accepted program legitimately quotes a single-witness output literal would
regress; if the battery finds one, that task is the measurement, reported,
not patched around); (2) the 5-task spurious probe set from
`CEILING_REASSESSMENT_7 §5.1` re-swept — prediction: zero of the five return
a literal-lookup shape; (3) tasks 102/411 re-swept at the DEFAULT budget —
if the genuine composition is found, that is +2 ids and the first
Occam-ordering conversion in the arc; if not found, the finding is still
decisive (the wall was not literal-pricing alone) and the rung reports it.

**Slice 2 (Γ, makes 1.4's earned trust load-bearing):** re-express the
pricing rule as the first CONSULTED production family in
`seeds/program_synthesis_opgrammar.json` — the literal-admissibility census
as `where`-clause evidence, weights as the cost — and flip one narrow part
of `run_enumerate`'s spec construction to read Γ verdicts, with the existing
420/420 parity harness as the regression gate (residual #41's own named
closure path). This turns the pool from a filtered set into a generated one,
which is the Γ doctrine's actual demand.

**Slice 3 (named, not designed here):** the negative-codebook variant the
task brief raises — grow an `AntiSignature` codebook from the 60-task
`accepted_holdout_fail` corpus (anti-unify the accepted-wrong programs;
`AntiUnifyWitness` is shipped, `term.rs:1036,3758`) and consult it as
ordering evidence. Considered honestly: for the literal-lookup family,
slice 1 subsumes it more cheaply and without a learned artifact to maintain;
its real value would be degenerate FAMILIES that are not literal-based, and
whether those exist in the 60 is an empirical question
(`HOLDOUT_FAIL_SURVEY`'s own finding was "idiosyncratic, no shared fix,"
which cuts against). Deferred until slice 1's residue is measured — building
it first would be a shape matcher built before there is a shape to match.

**Risk/size:** LOW-MEDIUM. No new architecture, no new Term, one file;
the single real risk (a legitimate single-witness-literal solution among the
current 88) is measurable in gate (1) before anything else depends on it.

---

## 3. PROPOSAL 2 — Program-grain anti-unification: mint derived operators
     from solved-program pairs ("solve one, get the cluster")

**Name:** `program-parallelogram` — data-only growth of the operator
inventory by anti-unifying witnessed solutions into `derived_ops` templates.

**The capability gap it closes.** Every task is currently searched from
scratch; nothing transfers between solved siblings. Yet the corpus is FULL
of siblings: 102/411 are the same program over different data (0.93 prompt
similarity), 137/442 differ by one predicate, and the near-duplicate scan in
`CEILING_REASSESSMENT_7 §3` found more. And this codebase has already proven
the exact mechanism at another grain: `RULE_REFERENCE_LAYER_SIZING_RESULTS.md`
(cited in CLAUDE.md) took three corpus rules, ran ONE `AntiUnifyWitness` call
plus `Substitute`, and produced a novel, correct rule absent from all 2,851
recognisers — 318 such parallelograms, 200/200 sampled transfers lossless.
Programs are Term-trees; the same algebra applies verbatim.

**Mechanism.** When two accepted (or human-taught — `teach_write_shape_from_
example` already exists and is tested end-to-end, wiring investigation §3)
Programs anti-unify with a small witness set, the shared template with typed
holes is minted as a **`derived_ops` entry** — the data path
`DERIVED_OPERATOR_TIER_SLICE1_RESULTS.md` already shipped:
`TermNode::Call{name,args}` dispatching through a per-search
`DerivedOpRegistry`, template JSON + params + `extra_cost`, proven
byte-identical to a native op at both evaluation and search level. This
stays exactly on the right side of the boundary
`STRUCTURAL_CEILING_REASSESSMENT_PREREG.md §1.3` drew: **no new interpreter
semantics are ever minted — a derived op is a composition of shipped
primitives, consumed by an already-generic evaluator** — which is precisely
the property that made `sd_mint_quantum` safe to automate. The mint bar is
the tier's own: cross-task support ≥ 2, independently verified (its
retroactive walkthrough showed this bar correctly REFUSING a single-witness
mint). Honest constraint carried forward: a template whose hole pools do not
match one of the six hand-coded pool shapes is refused with a named reason,
not force-fit (the tier's §4 residual; closing it generally is a separate,
priced, one-time Rust rung).

**What changes in KIND, not just in count.** Today the op inventory grows
only by human Rust PRs; with this, it also grows as graph data from the
agent's own solved/taught corpus — the first data-only growth path for the
operator layer, and the one that turns ONE human demonstration into a
cluster-wide capability (teach 137's shape once; 442 becomes a one-hole
search). It also composes multiplicatively with §2: a minted derived op with
honest `extra_cost` enters the SAME repriced ordering, so transfer proposals
and MDL ordering reinforce rather than fight.

**Risk/size:** MEDIUM. The pieces exist (`AntiUnifyWitness`/`Substitute`,
`Call`/registry, the mint bar, the teach path); the new work is the minting
rule + the Program-IR-to-template builder + persistence of minted entries as
seed data, plus the genuinely open design question of hole-typing against
the six pool shapes. First slice: OFFLINE — run the anti-unifier over the
existing accepted-Program corpus and count parallelograms with support ≥ 2
(the exact "prove it reproduces a known-safe fact" move: 102/411's template
should fall out if either is ever taught/solved); zero agent wiring until
that census says the population is real.

---

## 4. PROPOSAL 3 — Engineering-gap visibility: the agent's own measured
     residuals become graph it can surface

**Name:** `measured-residual-filing` — measurement scripts file structured
gap facts; rules decide; the surfacing reader reads.

**The capability gap it closes.** §1.5's finding: the agent can name its
conversational gaps and not its engineering ones, although the engineering
ones are the most precisely measured facts in the whole tree (blocker
histograms, priced tiers, ≥2-witness clusters, the Occam wall itself). Per
CLAUDE.md's own directive — *"if it can't fix it, at least find the gap"* —
a capability ceiling the agent cannot even REPORT is a gap in the
gap-finding machinery, and it is exactly the population a human would want
surfaced when deciding what to build next.

**Mechanism (each piece stays inside the sanctioned adapter/rule split).**
(a) The diagnostic scripts (`ceiling3_diag_sweep.py`, the battery) already
compute structured residual populations; at write-time they additionally
ingest each named population as a typed fact node (mechanical I/O — the
numbers are already in a dict in the script's hand; NO prose parsing, per
the "Seam C" warning the wiring investigation's §5 cites against exactly
that). (b) A small seed's rules — sibling to `ps_gap_file`, reusing
`gap_awareness.json`'s dedup/retire discipline — decide which populations
constitute a standing `SelfConcern{kind:'engineering_residual', ...}` and
when a re-measurement retires one (the count went to zero → the rule
retires it, the same shape as `retire_duplicate_gap`). (c) `_run_self_gaps`
surfaces them with zero new plumbing, because the node shape is the
confirmed-real one. Plus the wiring investigation's own smallest
recommendation, adopted here as-is: a test exercising `promote_self_concern`
on a `prog_read` concern (converting its §2 reasoned prediction into a
measurement), then the `_process_prog_read_standing` closure branch in the
`code_write` precedent's exact shape.

**Risk/size:** LOW. All spines exist and are tested; the new surface is one
ingest call per script, one small seed, one daemon branch. The design
question worth one paragraph of care: granularity (file per POPULATION with
a count and a task-id list attr, not per task-id — 169 concerns would flood
the reader; ~8 population-grain concerns inform it).

---

## 5. Why §2 outranks the task's own suggested negative-codebook framing

The brief's candidate — grow a codebook of known-degenerate signatures as a
negative prior — was investigated (§2 slice 3) and is genuinely sd-loop-
shaped. It is ranked behind witness-pricing for three grounded reasons:
(1) the measured degenerate field is, so far, ONE family (literal-lookup
`IfThenElse` over row constants — 5/5 in `CEILING_REASSESSMENT_7 §5.1`), and
pricing removes that family's advantage at generation time without any
learned artifact, maintenance, or false-positive surface; (2) a negative
codebook consulted as a veto is a FILTER, which the Γ doctrine explicitly
warns against ("a generated set, never a filtered one") — the pricing form
keeps the fix generative; (3) `HOLDOUT_FAIL_SURVEY`'s own NO-GO found the
accepted-wrong population idiosyncratic, which is evidence against a
mintable shared shape existing today. If slice 1's post-fix residue shows a
second coherent degenerate family, that measurement — not this document —
is the negative codebook's prereg.

---

## 6. Ranked recommendation

1. **Build §2 slice 1 (witness-priced literals) next.** It attacks the one
   problem every other lever is currently jammed against (reassessment-7's
   NO-GO names "the underlying Occam-ordering problem" as the blocker for
   BOTH live clusters), it is small, it has a falsifiable 5/5→0/5
   prediction, and its first gate is the house discipline verbatim:
   reproduce the known-safe 88/87/113 with `lost_pass=[]` before trusting it
   with anything novel. It also has the highest generalization-per-line of
   anything here: the fix is to the metric, so every future few-shot domain
   inherits it.
2. **§4 (measured-residual filing) in parallel or immediately after** — it
   is cheap, independent, touches no search machinery, and pays the
   competent-man dividend directly: the agent that can say "my enumerator
   memorizes under 2-row specs; here is the measured population" is
   exhibiting the self-knowledge the whole gap-awareness arc exists for.
3. **§3 (program-parallelogram) as the following arc**, gated on its
   offline census slice first. It is the largest capability expansion of
   the three — a new KIND of growth for the operator layer — but its value
   compounds with §2 (transfer proposals entering an honest ordering), so
   it should land second, and its census costs almost nothing to run now.
4. **§2 slice 2 (Γ flip, residual #41)** whenever the opgrammar surface is
   next touched — the parity harness makes it cheap, and leaving a 420/420-
   verified grammar advisory-only is carrying the cost of Γ without
   collecting its benefit.

## 7. What this document does NOT establish

1. No code, seed, or test was written; no battery was run. All MBPP
   numbers (88/87/113, the 5/5 spurious sweep, 56/60, 420/420) are the
   cited documents' own measurements, current as of their dates, not
   re-derived here.
2. §2's repricing prediction for task 102 is arithmetic over the published
   sizes, not a run — and whether 411/137/442 then converge at default
   budget is explicitly NOT predicted (reassessment-7 §6.1 leaves their
   reachability open; slice 1's gate treats "still not found" as a
   decisive, reportable outcome, not a failure of the rung).
3. Whether any currently-passing task legitimately depends on a
   single-witness output literal is unknown until gate (1) runs — this is
   §2's one real regression surface and is deliberately front-loaded.
4. §3's parallelogram census over the accepted-Program corpus has not been
   run; the 318-parallelogram figure is the RULE corpus's, cited as
   mechanism precedent only, not as a prediction for the Program corpus.
5. The §1 findings were checked against `SHAPE_AUDIT.md`'s section list and
   rejections, but this review did not re-read all 40 sites; a collision
   with an audit sub-finding not visible at section grain is possible.
6. Integer-output literal pricing (the auto-append at
   `synth_enumerate.rs:2767-2778`) is named in §2 but deliberately excluded
   from slice 1's scope; its regression surface (arithmetic tasks) is
   larger and unmeasured.
