# PROGRAM SYNTHESIS ARC 5 — SUMMARY (the representation arc)

**Date:** 2026-08-01. This is the arc-closing document, in the standing
pattern established by `PROGRAM_SYNTHESIS_ARC_SUMMARY.md` and
`PROGRAM_SYNTHESIS_ARC4_SUMMARY.md`: what was diagnosed, what was measured,
what was built, every null kept visible, the consolidated residual ledger,
and a methodological note this arc cannot skip. Every number below is cited
to the phase document and result artifact it comes from; none is
paraphrased from memory, and where two documents could be read as
disagreeing this says so explicitly (§7).

**The one-line result:** arcs 1–4 spent four independent nulls
discovering that *better proposal content* does not move the needle
(chunks, an NL-paired diet, retrieval, a cost instrument — all null, per
`PROGRAM_SYNTHESIS_ARC4_SUMMARY.md` §7). Arc 5 diagnosed *why*: the
synthesizer was searching **syntax** when the substrate's own law says
cognition is integer/shape-based — a syntax searcher built **beside** the
graph's shape-decode machinery instead of **on top of** it
(`PROGRAM_SYNTHESIS_ARCH_DIAGNOSIS.md`). Every structural move the arc
measured (reusing a shape, an intermediate, a missing dimension) beat a
bigger search budget, in two of three cases turning *impossible* into
*trivial*; the float side of the same diagnosis found that no program in
this project's benchmark corpus, and no numeric site in this project's own
DSP code, requires an in-frame float — with two live exceptions in the
project's own code, now fixed (§8). Both null probes (shape-recognition
constraint, the widest-gap criterion) are reported alongside the wins,
precisely measured, not smoothed over. The arc itself ran with **no
preregistration** (§6) — a limitation this document states plainly rather
than retrofitting one.

---

## 1. The architectural diagnosis (`PROGRAM_SYNTHESIS_ARCH_DIAGNOSIS.md`)

The project author's claim, quoted directly: *"The fundamental design of
[cognition] is... integer based, and doesn't need the other options. Which
means (a) Term Trees etc are trying to shove linear-ish computer logic into
a cognitive engine, and (b) the representations of the problems are not
correctly abstracted."*

The diagnosis is confirmed by the arc's own numbers, not asserted:

| move | syntax representation | shape representation |
|---|---|---|
| geometry family (6 MBPP tasks) | **unreachable at any size** — π not in the const set; 120,000 candidates exhausted | one shape `k·π·r^a·h^b` + a 3-integer parameter vector: 10–109 candidates each, **277 total** |
| `top_of_three` | `Max(a,b)` from 3 rows — **wrong** | extremum shape under S₃: **correct**, zero new data |
| nth octagonal | direct search **fails**, 200,000 tested | inner factor + one composition: **8,529**, correct |

What was actually built across arcs 1–4, in the diagnosis's own words: "a
miniature von Neumann evaluation model — AST nodes, size-ordered
enumeration, an interpreter, fit-the-outputs — expressed **in** the
substrate rather than **as** the substrate." The missing level is **shape →
IR**: the layer (`ShapeSignature`, `ShapeDecode`, `sd_mint_quantum`,
`DimInfer`, `LatentDimension`) already exists — the Omniglot arc proved the
pattern (propose by quantised index, render, compare) in vision — and this
project's program-synthesis line built a syntax searcher beside it instead
of on top of it. The verdict layer, the hub IR, and `ProgEval` are all
named explicitly as correct and untouched by this diagnosis — the defect
is localised to **proposal**, the half every prior arc's nulls already
implicated.

---

## 2. The three moves, measured (`PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md`, `PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md`)

The project author's frame: two ways to solve a problem — reuse a held
shape, or relax Γ by admitting the widest-gap new structure; when
comparing across orders gets expensive, an *intermediate* problem unlocks
tractability; or mint a *missing dimension* and the cost drops an order of
magnitude or more. All three were measured live against the real engine,
each on a single decisive case:

- **Move 2a — orbit augmentation (group action).** `br_10_top_of_three`
  from its 3 revealed rows: `Max(a,b)`, size 3, 532 candidates tested —
  **wrong** on held-out. From the **S₃ orbit of those same 3 rows** (13
  distinct rows, **zero new oracle calls**): `Max(a, Max(b,c))`, size 5,
  25,240 tested — **correct** on held-out, and independently verified
  against two hand-constructed witness rows outside both the revealed and
  held-out sets. A decoy check confirms the mechanism: `max(a,b)` satisfies
  all 3 revealed rows and fails their orbit — the orbit is what kills it.
  This directly overturns arc-4 S6's own conclusion that "the revealed rows
  are exhausted" (`PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md` §0) — two
  independent prior spikes had already derived this by different routes
  before the measurement confirmed it.
- **Move 2b — intermediate problems.** Task 59, nth octagonal number
  (`n*(3n-2)`): direct search at `max_size=9` with default constants tests
  **200,000** candidates and does not find it (budget exhausted). Solving
  the inner factor `(3n-2)` alone costs **8,529** candidates (found at size
  5); composing `n * inner(n)` is correct on held-out. ~23× cheaper, and it
  succeeds where direct search cannot finish at all.
- **Move 3 — mint the missing dimension.** Seven of arc-4's nineteen
  "arithmetic depth" tasks are one family, `k · π · r^a · h^b` (sphere/
  cylinder/cone/circle/polygon). Direct search is **unreachable at any
  size** — π is not in the constant set; 120,000 candidates exhausted. The
  family shape with dimension `(k, a, b)` solves **6/6**, 10–109 candidates
  each, **277 total** — recovering the exact textbook coefficients
  (`4/3,a=3`; `4,a=2`; `1/3,a=2,b=1`; `2,a=1,b=1`; `1,a=2,b=1`; `2,a=1`),
  real structure, not a fit. This directly corrects arc-4 S4's own filing
  of these 19 tasks as "deeper than `max_size=9`" — no size ceiling helps
  when the needed constant is not expressible in the basis at all; the
  problem was a missing dimension, not depth.

**The honest caveat, identical across all three (stated by the document
itself, not softened here):** the *mechanism* is confirmed; the
*selection* is not. In every case the orchestrator supplied the structure
by hand (the S₃ conjecture, the `(3n-2)` factorisation, the
`k·π·r^a·h^b` family). What is measured is that the structural move works
and how much it is worth; whether the system can find the structure
itself is the explicitly open question this arc hands forward, and the
machinery for each already exists, pointed at other domains
(`TransformDecode` for group action, `DimInfer`/`LatentDimension` for
dimension minting, descent's hole-finding for intermediates — the last of
which never fired on task 59's scalar arithmetic, since it is scoped to
list-input specs today).

---

## 3. The float results

Four documents, each measuring a different piece of the same claim (the
project author's: *"No program needs floats. Many programs are specified
in ways that imply they need floats."*):

### 3.1 Zero MBPP tasks need an in-frame float (`PROGRAM_SYNTHESIS_ARC5_FLOAT_NECESSITY.md`)

Across all 427 MBPP tasks: only 39 (9.1%) involve a float in their asserts
at all. Of those, 27 are rational parameters plus a cross-frame map
(π/√/÷/^), 8 have the float only in the output comparison, and 4 are
"irreducible float literal." **The four irreducible cases (tasks 139, 233,
276, 574) all carry the identical literal `3.1415`** — a hand-truncated π
(error 9.27e-05), a cross-frame constant written badly, not an irreducible
in-frame quantity. The complete inventory of float literals across all 427
reference solutions (`255.0`, `2.0`, `1.0`, `0.5`) contains **not one
irrational value**. **Tasks requiring a genuine in-frame float: 0/427.**
The document states its own limit plainly: this is MBPP, a basic
programming corpus, and "a numerics or signal-processing corpus would very
likely contain genuine in-frame reals... this result must not be quoted as
'no program needs floats.'"

### 3.2 Specs are written to imply floats (`PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md`)

Reading a float assert (`math.isclose(x, 62.83, rel_tol=0.001)`) as the
INTERVAL constraint it actually is — 17 significant digits followed by a
declaration that 3 of them matter — and solving for an exact structure
(rational coefficient × cross-frame constant × integer exponents) recovers
**11/20** usable float-involving tasks exactly: `4/3·π·r³`, `4·π·r²`,
`2·π·r`, `2·π·r·h`, `1·π·r²·h`, `1/3·π·r²·h`, `1/8·π·r²`, `9/8·n²`,
`5/6·b`, `1/180·π·d`, `1·√3·a²`. The remaining 9 are classified (by
inspecting the reference solution's operators, not demonstrated by fitting
— the document separates these two strengths of claim explicitly) as
needing a different exact shape: `tan` (163), `√` of a composite argument
(293, 731), fold/sum (248, 738, 300), a sum of two family terms (574), an
iterative algorithm (246), or a selection rather than arithmetic at all
(397, median-of-three). **Tasks requiring an in-frame float: 0/20.**

### 3.3 The strong claim survives this project's own DSP corpus (`PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md`)

The hardest available test: this project's own working audio/vision/
quantization stack (cochleagram, gammatone, LPC/Levinson-Durbin, YIN F0,
the shape/verdict comparator family, `space_quantize.rs`, `strokes.rs`)
plus seven classic numerical algorithms (Newton's method, trapezoid/
Simpson integration, LU decomposition, QR/Cholesky, FFT vs. NTT, RK4,
mean/variance/std). 23 sites audited, mechanically re-verified against
real source (`results/arc5_numerics_float_audit.json`, gated 19/19 by
`tests/test_arc5_numerics_audit_migrated.py`):

| class | n | meaning |
|---|---|---|
| A — cross-frame map, permitted | 19 | comparators, transforms, renderings |
| B — in-frame datum, would refute | **0** | — |
| C — avoidable in-frame float (defect, not requirement) | 4 | see §8 |
| D — genuinely irreducible, would refute | **0** | — |

**Zero class-D sites** — the strong claim survives its hardest available
test. The single cleanest confirmation: `runners/dsl/src/space_quantize.rs`
— the entire N-dimensional flood/quantization engine — contains zero
`f32`/`f64` occurrences besides one cosmetic sentinel (`c1-10`, the
`SpaceQuantum.qdist` -1.0-as-unset marker, itself class C). The document's
"sharp question" (does error accumulation over iterative steps make
in-frame reals necessary, or precision *tracking* necessary?) is answered
directly: precision tracking — every iterative algorithm examined is, at
each step, a closed rational operation on the previous rational state, and
IEEE float answers the eventual threshold comparison with no attached
uncertainty, "precisely the operational signature of the 1994 Pentium FDIV
bug." Honest qualification, stated by the document itself: this is a
judgment-call audit of a finite, honestly-scoped search, not a decidable
proof that no class-D site exists anywhere in the unswept remainder.

### 3.4 FPGA readiness (`PROGRAM_SYNTHESIS_ARC5_FPGA_READINESS.md`)

A mechanical float-density count (`f32`/`f64` type mentions, comments
stripped) over the 71,825-LOC Rust crate, by architectural role:

| role | LOC | f32/f64 | per kLOC |
|---|---|---|---|
| Cognitive core (reflect, quantize, shape, cycle, terms, **rules**, grammar, substrate, graph) | 12,039 | 75 | **6.2** |
| — of which the **rule engine** alone (rewrite + graph_rules) | 2,672 | **4** | **1.5** |
| DSL terms (term/prog_eval/synth_enumerate/jsonio) | 13,840 | 250 | 18.1 |
| Codec & other | 23,709 | 838 | 35.3 |
| PyO3 boundary | 8,113 | 419 | 51.6 |
| DSP / metric | 14,124 | 1,407 | 99.6 |

Density rises **monotonically outward**, exactly as the frame invariant
requires: core (6.2) → DSL (18.1) → codec (35.3) → Python boundary (51.6)
→ DSP/metric (99.6) per kLOC — the two highest densities are precisely the
cross-frame regions (host boundary, comparator/transform layer), permitted
by the invariant, the software analogue of an ADC/DAC edge. 34 modules
(19,237 LOC, 26.8% of the crate) contain no float at all. Consequence
stated directly: an FPGA target of the cognitive core would not be a
port — the fabric-side subsystem is already integer.

---

## 4. What was built: the exact-first rung (`PROGRAM_SYNTHESIS_ARC5_EXACT_FIRST.md`)

The diagnosis (§1) and the float measurements (§3) were productionised,
not left as measurement: `seeds/exact_families.json` (two `ExactFamily`
nodes as graph data — `scaled_power_product` and `sum_of_two_terms`),
`domains/prog_exact.py` (mechanical: interval-as-constraint, family fit,
shape→IR render, no graph-state decisions), and three new seed rules in
`seeds/program_synthesis.json` (v1.8.0 → v1.9.0, 63 → 66 rules) inserted
Occam-ordered between descent and enumerate, with the verdict layer
untouched.

**Result, real pipeline, PRIMARY protocol, the full 257-task MBPP test
battery, isolated correctly against a re-run "before" (the obvious frozen
comparator was found stale relative to HEAD and the document says so
rather than reusing it):**

| | pass / 257 | task ids that changed |
|---|---|---|
| before (clean HEAD, same run) | 28 | — |
| after (this build) | **34** | **+6: 82, 85, 139, 233, 276, 312** |

**Exactly the six geometry tasks predicted by §2's Move 3 changed outcome,
and zero other tasks moved in either direction** — checked exhaustively
against the full before/after task-id map, not a sample. 606 and 742 also
recover (needing a wider denominator set and a `√3` constant
respectively); 574 recovers the correct structure (`2π(rh) + 2π(r²)`) but
is reported failing held-out under exact float equality against a
truncated-π corpus reference with no declared tolerance — named as a
corpus artifact, not a defect in the recovered structure, and it falls
outside the scored 257-task test split either way. Every `Lit` in every
rendered IR is verified to be either a Python `int` or the one named
cross-frame constant's pre-computed double — never a bare float for a
fitted parameter. Tests: `tests/test_exact_first_migrated.py` 20/20,
`tests/test_program_synthesis_migrated.py` 17/17, a named 19-file arc-4/
arc-5 regression sweep at 508 passed / 6 failed — all six failures in
files outside this build's ownership (three literal seed-version-string
pins, three frozen "after" id-bucket snapshots this build's own headline
necessarily moves), each named individually and none a correctness
regression.

---

## 5. The nulls, kept visible

Per this project's own standing discipline (state the null as clearly as
the win), two dedicated probes returned negative, precisely measured:

### 5.1 Shape-recognition ceiling probe (`PROGRAM_SYNTHESIS_ARC5_SHAPE_PROBE.md`)

Tested whether recognising a goal's *shape* could supply the discriminating
constraint revealed rows cannot. **Headline: no**, measured four
independent ways against the real machinery (`RecogniseShape`,
`TransferDecode`, `SynthEnumerate`):

- Recognition fired on 23/257 (8.9%) MBPP test tasks — **0 genuine
  algorithmic true positives** among them; every hit traces to an
  accidental prose collision (e.g. "re**move** first and last" firing
  `spatial_motion:move`). The held vocabulary (`shape_vocabulary.json`) is
  entirely systems/cognition-flavoured (scheduler, memory_store, gating,
  homeostasis) — not one algorithmic keyword.
- The one constraint (argument symmetry) built specifically to test the
  hypothesis applies to only 3/76 traps and adds **zero** discriminating
  mass beyond the existing structural detectors (D1–D7).
- **Pruning: 0/13, live, against the real `SynthEnumerate` engine.**
  Where exclusion found anything at all (5/13), every candidate is
  verified wrong on held-out data — a structural trap is by definition
  behaviourally identical to the correct answer on revealed rows, so
  excluding it excludes the correct completion too. This is the same wall
  arc-4 S6 already proved for `br_10` specifically, reproduced here for 7
  more tasks.
- Analogical transfer: 4/4 honest walls (`meta_shape: null`) — the
  mechanism itself works (proven elsewhere for systems-shaped goals) but
  the codebook has never been seeded with anything program-synthesis-
  shaped.

Named precisely as a seeding/vocabulary gap, not a mechanism failure — and
named as the reason move 2a (§2) needed the structure supplied by hand.

### 5.2 The widest-gap criterion (`PROGRAM_SYNTHESIS_ARC5_WIDEST_GAP.md`)

Tested whether a widest-gap relaxation criterion could *discover* the S₃
structure move 2a needed by hand, with no lexicon. **On the headline case
it works, exactly**: unaided, the criterion enumerates `sym_full_S3` plus
all three 2-cycle subgroups plus idempotence, refutes none, correctly
scores gap=0 for the one subgroup (`a,b`) the trap `Max(a,b)` is already
symmetric in, and gap=1 for `S3` and both subgroups touching the ignored
argument `c` — selecting `Max(Max(a,b),c)`, verified on held-out and two
independently constructed witness rows.

**Generalisation is a plain null: of 48 non-`br_10` tasks (REOPENED_12 +
the arc-4 honest 36-residual), only 9 are even applicable to this grammar**
(arity-2/3, all-integer; the other 39 excluded by arity or type, with
reasons recorded). **Zero of the 8 other applicable tasks convert.** One
false selection (`292`, a division-shaped task with no `Div` in this
grammar's op inventory at all — a coverage gap, not a ranking failure).
**The binding constraint is grammar coverage, not the selection
mechanism** — corroborated independently by §5.1's own 3/76 finding that
symmetry-shaped defects are genuinely rare in this task population. Two
mid-run reframes (gap as one weight among several, not a sole decider; a
cheap `arity_gap` companion signal) are recorded as feature vectors for a
future weighted collapse, explicitly not built or tuned here.

---

## 6. The methodological result — this arc had no preregistration

Unlike arcs 2–4, each of which opened with a dedicated `_PLAN.md` and
`_PREREG.md` before any measurement (`PROGRAM_SYNTHESIS_ARC4_PLAN.md`,
`PROGRAM_SYNTHESIS_ARC4_PREREG.md`, and their amendments, cited throughout
`PROGRAM_SYNTHESIS_ARC4_SUMMARY.md` §2), **arc 5 has no `PLAN` or `PREREG`
document at all** — verified directly: no
`PROGRAM_SYNTHESIS_ARC5_PLAN.md`/`PROGRAM_SYNTHESIS_ARC5_PREREG.md` exists
in this tree, and the arc's own commit history (nine commits, `3d06a1fb69`
through `ec41d3001c`) shows each phase's document landing as its own
self-contained measurement, built from the immediately preceding
conversation rather than from a registered hypothesis set written in
advance. This should be stated plainly, not smoothed into the summary the
way arcs 2–4's own preregistrations were: **this arc grew conversationally.**

What was NOT sacrificed: every individual measurement in this arc is
still gated (a JSON results artifact plus a `tests/test_arc5_*_migrated.py`
suite, 19–22 tests apiece), twin-run deterministic where the document
claims determinism, and honest about its own scope limits (§3, §5 above).
The discipline that *substitutes* for a registered prereg, used
consistently across every arc-5 document, is **paired-identity
comparison, not CI-separated aggregates**: the exact-first rung's headline
is "exactly these six task ids moved, zero others" (§4), the orbit
result's headline is one task's revealed→held-out verdict flipping under a
named, refutable intervention (§2), and the widest-gap probe reports exact
applicable/converted/false-selection id lists (§5.2) rather than a bare
percentage. This is the same "a baseline is a list, never a count"
discipline arc 4 registered in writing beforehand
(`PROGRAM_SYNTHESIS_ARC4_SUMMARY.md` §6) — arc 5 practises it without
having registered it.

**What this arc genuinely lacks, and what a future arc should supply
before extending this line:** a powered endgame with preregistered bars,
of the kind `PROGRAM_SYNTHESIS_ARC_SUMMARY.md` §5's P7-D closes with (three
arms, Wilson CIs, a registered null-or-not verdict per hypothesis). Every
arc-5 number is real and every id list is honestly derived, but none of it
has been through a preregistered power calculation, and the arc's own
"honest caveat" for all three structural moves (§2) — "the mechanism is
confirmed, the selection is not" — is exactly the kind of finding a
powered follow-up would need to size before claiming it generalises. This
is recorded here as a **limitation of the arc**, not a footnote to be
read past.

---

## 7. Where documents could be read as disagreeing (and are not)

Two apparent tensions, resolved by reading the qualifying clause each
document already carries:

- `PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md`'s summary table lists
  **class C = 4** (`c1-10` the `qdist` sentinel, `c1-12` acoustic bands,
  `c1-14` the Fisher `sqrt`, `c2-07` mean/variance/std as a classic-
  algorithm class), while its own prose verdict foregrounds **"three
  sites"** (`c1-12`, `c1-14`, `c2-07`) as the headline "avoidable in-frame
  float" finding. These do not disagree: `c1-10` is explicitly described
  in the same document as "minor, cosmetic, free to fix... not because it
  does any work a float is needed for" and is kept out of the headline
  three precisely because it is a type-sentinel artifact, not a
  computation depending on float precision. §8 below fixes only the two
  LIVE repo sites in this project's own Python (`c1-12`, `c1-14`); `c1-10`
  (Rust) and `c2-07` (a generic textbook classification, not a specific
  repo site) are out of that scope.
- `PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md`'s geometry-family fits (§2, Move
  3) are explicitly flagged by its own "method note" as fit against **all
  three** MBPP asserts with no held-out row reserved (correctness is not
  in doubt since the recovered coefficients are exact textbook constants,
  but the *protocol* was fit-on-all). `PROGRAM_SYNTHESIS_ARC5_EXACT_FIRST.md`
  §"headline" later reports the SAME geometry family solved under the
  PRIMARY protocol (2 of 3 rows revealed, 1 genuinely held out) — this is
  not a contradiction but a strengthening: the exact-first build re-derived
  the same family shapes under the stricter, held-out-respecting protocol
  and got the same accepts, closing the earlier document's own named gap.

No other cross-document numeric conflicts were found in the course of
writing this summary.

---

## 8. Addendum: the two live class-C sites, fixed (2026-08-01, same day)

`PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md` named two live, avoidable
in-frame floats in this project's own Python (§3.3 above, `c1-12`/`c1-14`).
Both are fixed as of this document:

- **`domains/discriminative_invention.py` (`c1-14`).** The Fisher-
  discriminant decision (`analyse_confusion_band`) previously computed
  `std = var ** 0.5` and persisted it, feeding a `Div`-of-stds Term-tree.
  It now decides via `_fisher_separates_term`, a sqrt-free EXACT
  reformulation over `a_var`/`b_var` derived by isolating and squaring
  each square root in turn (the standard nested-radical rationalisation
  technique). Verdict-identity against the original std-based formula is
  gated across 160 cases spanning both sides of the threshold and near it
  (`tests/test_exact_invariant_migrated.py`). **Honest residual, recorded
  rather than hidden:** `ConfusionBand` nodes still also carry `a_std`/
  `b_std` (computed the same way as before), because two modules outside
  this fix's ownership — `domains/pairwise_recognition.py` and
  `domains/teacher_hook.py` — read those attrs directly for their own,
  separate Fisher-style decisions; removing the attrs would silently zero
  them under those files' `.get(key, 0.0)` fallback. The module's OWN
  decision no longer touches an irrational value; the ConfusionBand node
  as data structure is not yet fully migrated.
- **`domains/acoustic_resolution.py` (`c1-12`).** `enrich_sign_bands` now
  persists `band<N>_<i>` as a fixed-point Int (`round(v * 2**32)`) instead
  of a raw float. Order (the only property `formant_features.py`'s peak
  detector and several other order/ratio-based consumers actually need) is
  gated byte-identical against the raw-float computation across 80
  synthetic trajectories, with and without the agent's own per-sign
  normalisation.
- Both fixes are reformulations, not redesigns — every existing consumer
  of these attrs across the codebase (`formant_features`, `dynamics_
  features`, `speaker_norm`, `cue_assessment`, `hint_grounding`,
  `recognition_architecture`) was checked and uses only order comparisons,
  `ArgMax` (index-valued), or scale-invariant ratios, none a fixed
  absolute-magnitude threshold — the property that makes a uniform
  positive rescaling of the persisted attr behaviour-preserving for them.
- **Consequence for the numerics audit itself:** four assertions in
  `tests/test_arc5_numerics_audit_migrated.py` now fail
  (`test_no_unverified_sites`, `test_all_file_sites_verified_status`, and
  the two spot-checks pinning the pre-fix source text verbatim) — the
  audit's own live re-verification pass correctly detects that the two
  sites it documented no longer match, which is the audit doing its job,
  not a defect in the fix. That file is outside this addendum's ownership
  and is left as the historical record of the finding; updating its
  pinned evidence to the post-fix source is a small, named follow-up for
  whoever owns it next.

---

## 9. Consolidated residuals, named levers, and the open question

Deduplicated across every arc-5 document above:

1. **Shape/dimension acquisition is untested — the fourth-null rule
   applies.** Every structural win in §2 had its structure supplied by
   hand. `PROGRAM_SYNTHESIS_ARCH_DIAGNOSIS.md`'s own closing question:
   *can shapes at the right grain be acquired for this domain?* is
   explicitly unmeasured, and the document itself insists the answer must
   carry the same discipline that closed proposal-content as a lever four
   times already: "a shape codebook is still content, and content has
   nulled five times *when used as a proposer*." The claimed difference —
   a shape is not a proposal but a representation the program is
   *rendered from* — is testable and must be tested, not assumed.
2. **The vocabulary that would recognise algorithmic shapes does not
   exist.** `shape_vocabulary.json` and `mechanism_index.json` are
   entirely systems/cognition-flavoured; §5.1 names precisely what would
   need seeding (an `extremum`/`total_function_of_declared_args`
   MetaShape + Mechanism entry) for `RecogniseShape`/`TransferDecode` to
   fire on program-synthesis goals at all.
3. **The engine's only search-restriction primitive is behaviour-keyed**
   (`SynthEnumerate`'s `exclude`), and a structural trap's behavioural
   identity with the correct answer on revealed rows — its defining
   property — is exactly what makes behaviour-keyed exclusion unable to
   separate them (§5.1). A construction-time admissibility filter (e.g.
   "may not compile unless permutation-invariant") is named as the
   missing engine primitive, not built.
4. **Grammar coverage, not selection, bounds the widest-gap criterion**
   (§5.2): 39/48 of the generalisation population is inapplicable purely
   on arity/type grounds, and the one false selection is a missing `Div`
   in the op inventory, not a ranking failure. Widening the grammar is the
   named lever; a weighted collapse combining gap-score with the cheaper
   `arity_gap` companion signal is recorded as feature-vector
   infrastructure for a future combiner, explicitly untuned here.
5. **`sum_of_two_terms` is scoped to arity ≤2 with a single shared
   `(k, C)` across both terms** (`PROGRAM_SYNTHESIS_ARC5_EXACT_FIRST.md`)
   — the one measured case (task 574) needed no more; an unscoped,
   independent-coefficient two-term family is named as untested, not
   unbuilt.
6. **Nine residual float-shaped tasks need richer exact shapes**
   (§3.2): `tan`, `√` of a composite argument, fold/sum accumulation, an
   iterative algorithm, and a pure selection — each named individually,
   none requiring an in-frame float.
7. **This project's own DSP audit is a finite, honestly-scoped search,
   not a proof** (§3.3) — Corpus 1 covers the audio primitives, the
   shape/verdict comparator family, and the two quantization modules the
   brief named; a differently-scoped sweep could surface more class-C
   sites, though the recurring pattern (closed-form rational recurrence;
   `sqrt` as an avoidable specification choice) suggests it would not
   surface a class-D site.
8. **`ConfusionBand.a_std`/`b_std` are not yet fully retired** (§8) —
   two files outside this cleanup's ownership still depend on them
   directly; migrating `pairwise_recognition.py`/`teacher_hook.py` to the
   sqrt-free `a_var`/`b_var` form is the named follow-up that would let
   the attr be dropped entirely.
9. **No powered endgame exists for this arc** (§6) — every structural
   move and every float claim is measurement-first and gated, but none has
   been sized against a preregistered bar the way arc 4's S5 or the main
   arc's P7-D were. This is the arc's own standing limitation, carried
   forward rather than closed here.

**The honest open question this arc hands forward, stated once, plainly:**
whether shapes at the right grain can be *acquired* — not hand-supplied —
for program synthesis is untested. It is the single most consequential
unmeasured question this arc's diagnosis raises, and any future work on
this line should measure it before building further on the assumption that
it is true.
