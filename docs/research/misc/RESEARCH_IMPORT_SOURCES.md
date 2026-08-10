# RESEARCH — mechanically importable canonical sources: impedance scoping

**Date:** 2026-08-01. Scope: measure which canonical advanced-math/algorithm
sources can be walked BY A SCRIPT (not authored one paper at a time), and
the IMPEDANCE between each source's representation and this substrate's.
**Measurement only — no engine/seed/adapter source touched, no Rust, no
cargo.** Files created: `scripts/arc6_import_impedance.py`,
`results/arc6_import_impedance.json`, this document. Companion to (but
does not modify) `PROGRAM_SYNTHESIS_ARC6_M0_AB.md` (Seam A kernel-import
list, Seam B `extract_function` reach) and `PROGRAM_SYNTHESIS_ARC6_M0_CD.md`
(Seam C math-shape null, Seam D theorem-property ceiling).

**The substrate's hard constraints, re-stated because every number below
is measured against them:**

- **In-frame is integer/rational/exact.** Non-integer structure is
  cross-frame — it lives in a MAP applied intensionally, never in a
  frame's own coordinates (CLAUDE.md's frame/continuum invariant,
  independently re-derived by `PROGRAM_SYNTHESIS_ARC5_EXACT_FIRST.md`/
  `..._RATIONAL.md`).
- **`ProgEval`'s oracle table forbids shelling out.** `prog_eval.rs`'s own
  doc comment: *"CallExtern. Evaluated ONLY against the declared `oracles`
  Dict... NO shelling out, ever — an extern's semantics is a knowledge gap
  that heals via the teacher chain, not a reason to run code."* This is a
  THIRD, independent filter beyond exactness and licence, and it changes
  the ranking below materially (§2.3).

---

## 0. The three import problems, kept separate

| # | problem | what "import" means | seam it feeds |
|---|---|---|---|
| A | **KERNELS** | a computational function registerable as a `ProgEval` oracle (or `reason.py::CAPABILITIES` entry) | Seam A |
| B | **PROPERTIES/THEOREMS** | a checkable assertion `comprehend_theorem`-shaped or property-atom-shaped | Seam D |
| C | **TASK→SOLUTION CONTENT** | a corpus of (task, reference solution) pairs | already OEIS; a candidate Rosetta Code bet |

Every source below is filed under exactly one of these; conflating them
(e.g. treating Lean mathlib4 as a "kernel source" because it CONTAINS
computable definitions) is the named error the brief warns against, and
none of the tables below do it.

---

## 1. PROBLEM A — kernels — measured

### 1.1 SymPy — live walk, 149 callables

`scripts/arc6_import_impedance.py::probe_sympy` walked
`sympy.ntheory.*` (7 submodules), `sympy.functions.combinatorial.numbers`,
`sympy.functions.combinatorial.factorials`, and
`sympy.combinatorics.partitions` via `inspect.getmembers`, invoked each
public callable on canonical small-int argsets (`(12,)`, `(2,3)`,
`(10,3)`, `(2,3,5)`, `(5,)`, `(7,2)`, 2s timeout per call), and classified
the RESULT type.

| | value |
|---|---|
| total public callables walked | **149** |
| successfully invoked on a canonical argset | **125 (84%)** |
| **exact** (int / `Integer` / `Rational` / `Fraction` / bool-predicate / a container whose elements are all exact) | **107 (85.6% of invoked)** |
| **inexact** (float / complex / `Float` / mpf / mpc) | **0** |
| invoked, result type unclassified (symbolic `Add`, `Matrix`, `dict`-of-mixed, ...) | 18 |
| not callable on any trial argset (needs bespoke shape: matrices, symbols, permutations) | 24 |

**Sample of exact kernels found:** `abundance`, `divisor_count`,
`divisor_sigma`, `divisors`, `factorint`, `is_carmichael`,
`is_mersenne_prime`, `is_palindromic`, `continued_fraction`,
`discrete_log`, `binomial_coefficients` — every one already
arbitrary-precision-exact in SymPy, zero float leakage across the whole
ntheory/combinatorics-numbers surface. **Licence: BSD-3-Clause.
Already installed (1.14.0) — zero import cost for the ones already
overlapping `reason.py::CAPABILITIES`** (which itself already wraps
`math.gcd`/`math.comb`/Miller-Rabin/etc. — SymPy would be additive for
the ~100 exact functions `reason.py` does NOT yet wrap: Carmichael/
amicable/abundant-number tests, continued fractions, discrete log,
Gaussian primes, digit-manipulation helpers).

**Mechanical walk cost:** the entire 149-function inventory + exactness
classification took **under 5 seconds of script time** — this is the
sharpest possible contrast with hand-authoring one kernel per paper. A
similar walk over SymPy's full public API (thousands of functions, most
needing bespoke non-integer args — polynomials, matrices, ODEs) would
need per-family argument templates, not a universal trial set; the
ntheory/combinatorics-numbers slice was chosen exactly because small
integers are a valid universal probe there.

### 1.2 mpmath — the architectural contrast, confirmed live

Same walk mechanism, 7 spot-checked functions (`sqrt`, `exp`,
`factorial`, `gamma`, `pi`, `log`, `sin`): **100% returned `mpf`**
(arbitrary-*precision* floating point). Concretely,
`mpmath.factorial(5)` — an operation whose true value is the EXACT
integer 120 — returns an `mpf`, not an int. mpmath is architecturally
inexact by design (its whole purpose is multi-precision floats); it is
admissible only as a cross-frame MAP/comparator (per the CLAUDE.md
invariant — a rendering or verdict metric), never as an in-frame oracle.
**This is a clean, load-bearing negative result, not a bug**: it
confirms the substrate's own invariant against a real library built the
opposite way.

### 1.3 The `ProgEval` "no shelling out" filter — the decisive cut over PARI/FLINT/GAP

The brief asks about PARI/GP, FLINT, GAP as kernel sources. All three are
GPL/LGPL (checked live, not assumed — see table). But licence is not the
binding constraint here; **architecture is**:

| candidate | in-process binding on PyPI? | mechanism | verdict |
|---|---|---|---|
| **FLINT** via `python-flint` | YES (`pip index versions python-flint` → 0.9.0, not installed here — installing into the shared env is outside this task's file-ownership scope) | Cython binding directly against `libflint` — an in-process C call | **ADMISSIBLE.** Exact by design (arbitrary-precision int/rational/poly/matrix). Licence LGPL-3.0 (confirmed live via GitHub API: `flintlib/flint`). |
| **PARI/GP** via `cypari2` | YES (2.2.4 on PyPI) | Cython embedding of the PARI C library, in-process | **ADMISSIBLE.** Exact for its core domain (integers/rationals/p-adics/algebraic numbers); GPL-2.0-or-later (PARI's own canonical host is a Bitbucket/Mercurial repo, not GitHub — corroborated the licence key via a public GitHub mirror). **GPL note, flagged not dismissed:** fine to call in-process from the Python world-adapter layer; STATICALLY linking into the compiled `substrate_rs` binary would extend GPL obligations to that binary. |
| **GAP** | **NO.** Checked `pygap` (doesn't exist), `gappy` (0.4.3 exists on PyPI but is an unrelated project — "Python framework for Gap Service API," a web-service client, not the GAP CAS), `gappy-system` (doesn't exist). GAP's real Python binding (`sage.libs.gap`) ships only inside the full SageMath distribution, which is not installed here (`sage` not found). | The standalone GAP interpreter is normally driven via subprocess/pty (pexpect-style) | **EXCLUDED**, not on capability or licence grounds — on the `ProgEval` doc comment's explicit "no shelling out, ever." A clean import would need a custom Rust/C FFI to `libgap`, comparable in scope to a new engine primitive — out of a scoping task. GPL-2.0 confirmed live (`gap-system/gap`). |

**This is the sharpest finding of the kernel half:** the ranking among
external CAS libraries is not "which is most powerful" (GAP's group
theory is the deepest of the three) but **"which has an in-process FFI
binding"** — a constraint invisible until `prog_eval.rs`'s own doc
comment was read directly.

### 1.4 Import cost & yield, kernels

Mechanical walk cost is uniform and cheap (minutes of script development
per library that already has small-arity, small-int-testable functions);
the cost that varies is **wiring** a walked function into `ProgEval`'s
oracle Dict or `reason.py::CAPABILITIES` — that is unaffected by this
measurement and already sized in `PROGRAM_SYNTHESIS_ARC6_M0_AB.md` §1.4
(ranks 1–3 unlock 7/222 unreached MBPP tasks at near-zero cost using
functions ALREADY in `reason.py`). **This measurement's yield claim is
narrower and honest about it:** SymPy adds breadth (more exact number-
theory functions) but was not tested against the specific 222-task
unreached population — that cross-check is future work, not claimed here.
FLINT/PARI add exactness headroom for LARGER integers/polynomials than
Python's stdlib comfortably reaches (still exact, just faster/more
general) — a capacity lever, not a new-task-class lever, against the
measured MBPP population.

---

## 2. PROBLEM B — properties/theorems — measured

### 2.1 Metamath `set.mm` — live download + sampled classification (LIVE DEMO #1)

Downloaded the real file live (`raw.githubusercontent.com/metamath/
set.mm`, **CC0-1.0**, confirmed via its own `LICENSE` file — public domain,
zero licence risk). **51,043,506 bytes, 47,625 real `$p` theorem
statements** (2 header-documentation lines that superficially match the
same regex were found and excluded — see §4). 2000 sampled (stride
sampling across the whole file), classified by class-symbol tokens
**confirmed live by grepping the file's OWN `$a class TOK $.`
declarations** (not guessed):

| class | n / 2000 | % | meaning |
|---|---|---|---|
| `real_analysis_crossframe` | 207 | **10.35%** | statement mentions `RR`/`CC`/`sin`/`cos`/`exp`/`sqrt`/`~~>`/`S.`(integral)/`_D`(derivative)/topology tokens |
| `integer_finite_inframe` | 255 | **12.75%** | mentions `NN`/`NN0`/`ZZ`/`Fin`/`Word`/`!`/... — no real/complex token |
| `domain_free_logic` | 1538 | **76.9%** | pure propositional/set-theoretic identity, no numeric-domain token at all (e.g. `⊢ (φ → (ψ → (χ → θ)))`) |

**Interpretation, held to the honest standard the arc-6 ceiling docs set:**
89.65% of theorems are NOT real/complex-analysis (in-frame or
domain-neutral) — a genuinely favourable split relative to Lean/Isabelle
below. But the useful Seam-D-relevant slice is NOT the 76.9% —
propositional tautologies (modus-ponens variants) are trivially in-frame
as symbol manipulation but carry no program-refuting content. **The
actionable slice is the 12.75% `integer_finite_inframe` bucket**
(divisibility, primality, factorial/Bell-number-style identities,
finite-set facts) — extrapolated to the full 47,625 theorems, order
**~6,000** candidate theorems, before any further filtering for
subject-matter overlap with MBPP/ARC-style program properties (not
measured here — a second-pass filter, named as future work, not
assumed).

### 2.2 Lean mathlib4 — structural + sampled (SUPPLEMENTARY LIVE PROBE)

**Apache-2.0** (confirmed via GitHub API). Live GitHub tree fetch: **8,302
`.lean` files** under `Mathlib/`. Directory-level split (a coarser, HONEST
proxy — file counts, not per-theorem content):

| bucket | files | % |
|---|---|---|
| cross-frame dirs (Analysis/Topology/MeasureTheory/Probability/Dynamics/AlgebraicGeometry/Geometry) | 2,241 | 27.0% |
| in-frame dirs (Data/NumberTheory/Combinatorics/Computability/Logic/SetTheory/Order/Control) | 1,576 | 19.0% |
| abstract/mixed (Algebra/CategoryTheory/RingTheory/LinearAlgebra/Tactic/FieldTheory/...) | 4,485 | **54.0%** |

A random 25-file sample's `theorem`/`lemma` signatures (fetched live,
tokens classified by ℝ/ℂ/`Real.`/... vs ℕ/ℤ/`Finset`/`Fintype`/...):

| class | n / 25 |
|---|---|
| `abstract_generic_undetermined` (theorems exist, but are type-class-polymorphic — generic over an arbitrary `CommRing`/`Module`/`Category`, no concrete numeric domain at all) | 9 |
| `integer_finite_inframe` | 11 |
| `real_analysis_crossframe` | 2 |
| `mixed` | 2 |
| no theorem/lemma in file | 1 |

**The finding that matters more than the real-vs-int split: a THIRD
impedance axis.** Over half of mathlib4's files sit in directories whose
content is dependent-type-theory abstraction (type classes over
arbitrary algebraic structures) — neither concretely real nor concretely
integer until instantiated. This is a structurally different
representation from this substrate's typed graph regardless of numeric
domain, and it is why mathlib4's real impedance is higher than either
Metamath's or a naive "how much of it is analysis" question would
suggest. **Caveat on the sampled classification's reliability, stated
plainly:** unlike Metamath's tokens (confirmed against the file's own
type-DECLARATIONS), the mathlib token check is heuristic — `Fin`/`Nat`/
`Finset` can appear as an INDEXING device inside an otherwise abstract
proof (e.g. `Mathlib/Algebra/Lie/Weights/Basic.lean`, about Lie-algebra
representation theory, was tagged `integer_finite_inframe` purely because
it indexes weight spaces with `Finset`). **This classification is
noisier than Metamath's and should be read as directional, not exact.**

### 2.3 Isabelle AFP — live topic taxonomy (SUPPLEMENTARY LIVE PROBE)

**Licence: BSD-style OR GNU LGPL, author's choice per entry** (confirmed
via `isa-afp.org/about` — both permissive, zero blocking risk). **1,012
entries, 604 authors, ~323,000 lemmas** (read via a full-render fetch;
the `/statistics/` page renders these via client-side JS so this
script's plain-curl path — used for everything else — got an empty body
there; the headline figures are reported as sourced, not re-verified by
the committed script). The **topic taxonomy itself parses live** with
plain curl (a bug was found and fixed mid-session — see §4) and is the
SOURCE'S OWN classification, not a heuristic:

| bucket | entries |
|---|---|
| Algorithms + Data structures + Automata/formal languages | **208** |
| Number theory + Combinatorics + Graph theory + Order | **157** |
| Analysis + Measure/integration + Topology + Probability theory | **130** |
| (of 1,012 total; leaf counts overlap since an entry can carry >1 topic) | |

**AFP is the most directly relevant PROPERTY source of the three** for a
program-synthesis use: 208 entries are literally **verified algorithms**
(the brief's own suggestion), a category neither Metamath nor mathlib4
labels as cleanly. Isabelle/HOL's underlying logic is classical HOL with
genuine real/complex analysis support, so the SAME cross-frame caveat
applies to individual entries, but the taxonomy lets a future importer
target the "Algorithms"/"Data structures" leaves directly rather than
filtering a monolithic corpus.

### 2.4 Ranked recommendation, properties

**Metamath first, AFP second, mathlib4 third**, for three compounding
reasons: (1) CC0 licence removes all legal friction outright, where AFP
needs an author-by-author licence read for anything beyond casual use
and mathlib4's Apache-2.0, while permissive, still requires attribution
bookkeeping at scale; (2) Metamath's format is a single flat, regular
grammar (`label $p statement $= proof $.`) that a 40-line script parses
completely, where Lean/Isabelle proofs are full dependently-typed
programs needing a real type-checker's elaboration state to interpret
correctly — the mechanical-walk cost gap is an order of magnitude, not a
polish difference; (3) Metamath's own proof FORM (a substitution chain
over syntax trees) is structurally closer to this substrate's own
`Unify`/`AntiUnify`/`Covers` primitives than either dependent type
theory (Lean) or HOL's typed lambda calculus (Isabelle) — a Metamath
proof step is literally "instantiate this axiom/theorem's metavariables
by substitution," which is Robinson unification by another name. This
last point is a structural/architectural fit claim, not independently
benchmarked here — named as the strongest a-priori reason to prototype
Metamath import first, not as a proven result.

---

## 3. PROBLEM C — content — flagged, not pursued

### 3.1 OEIS — already integrated, not a new bet

`domains/oeis_local.py` + `scripts/oeis_extract_verify.py` (both
pre-existing, read-only here). Local dump: **392,167 sequences,
105,319,702 bytes** (`data/oeis/data/train-00000-of-00001.parquet`).
`PROGRAM_SYNTHESIS_ARC6_M0_AB.md` §2.1 reproduced its extraction
mechanism live THIS SESSION: **8/8 target sequences extracted from prose
and verified against real ground-truth values**, 2 honest non-
extractions named (Fibonacci, primes). This is the model for what a
working content import looks like — already measured, already gated,
not re-litigated here.

### 3.2 Rosetta Code — live single-task demo (LIVE DEMO #2, light-touch per the CONTENT flag)

**Licence: GNU Free Documentation License 1.3** (confirmed live, page
footer) — copyleft/attribution, NOT license-free; a real cost line item
for anyone building an importer, unlike Metamath's CC0. Live fetch of
one task page (`Fibonacci_sequence`): **312 distinct per-language
sections** on a single task — a genuine, mechanically-countable
demonstration of "one task, many surfaces." The MediaWiki API probe
(`/mw/api.php?action=query&...`) **FAILED** with `"No such action"` —
the endpoint/action set has apparently moved or been restricted since
older documentation; a real importer would need to either find the
correct API surface or fall back to page-scraping (as this demo did),
which is a genuine, if modest, extra engineering cost. Approximate total
task count (~1,200–1,400) is the well-known published figure, **NOT**
independently re-confirmed here (the API path that would have confirmed
it is the one that failed).

**Flagged per the brief's own instruction:** Rosetta Code is a CONTENT
source. This project has nulled six content bets at their ceiling (most
recently this morning, per the project's own standing record). **Nothing
here recommends building a Rosetta Code importer** — the live demo shows
it is mechanically walkable and a real "many surfaces" structure exists,
which is the honest extent of a scoping-level claim. Any actual import
would need a preregistered hypothesis and a powered gate, exactly like
every other content bet in this project, and the GFDL attribution
requirement is a real cost that a preregistration should price in
up front.

---

## 4. What broke, live, and how it was found

Reporting failures honestly, per the discipline established by
`PROGRAM_SYNTHESIS_ARC6_M0_AB/CD.md`:

1. **Metamath token collision — "D" ≠ derivative.** A first pass used
   the bare token `D` as a real-analysis marker (intending the
   derivative operator). It collided catastrophically with the generic
   4th class-metavariable (`A, B, C, D, ...`), classifying ordinary
   substitution-variable statements like `⊢ (φ → C = D)` as
   "real analysis." Found by inspecting the classifier's own trigger
   tokens on its example hits (not trusting the aggregate count),
   confirmed the REAL derivative token is `_D` (via
   `grep 'cdv \$a class'`), and fixed. The bare `pi` token had the same
   flaw (real token is `_pi`) and was fixed the same way, before it ever
   produced a wrong count.
2. **Metamath regex missed indentation.** The first parse regex required
   the theorem label to immediately follow a newline (`\n(\S+)`); real
   `set.mm` labels are indented inside `${ ... $}` blocks, so it matched
   zero theorems. Fixed to `\n\s*(\S+)`.
3. **Metamath doc-comment false positive.** The file's own header
   documents its syntax with a literal line `<label> $p <symbollist> $=
   <proof> $.`, which matches the theorem regex but is not a theorem.
   Found because ONE sample row showed a literal `<label>` — excluded by
   requiring no `<`/`>` in a real label (Metamath labels never contain
   them).
4. **AFP topic regex silently returned all-zero sums.** The first regex
   for leaf topic counts (`>Name (N)</a>`, no internal whitespace
   tolerance) matched only the 4 top-level H2 headings (whose `(N)` is a
   SUBCATEGORY count, e.g. "Mathematics (4)" meaning 4 subgroups) because
   real leaf entries render as `<a href="...">↵  Name (N)↵</a>` — the
   label and the closing tag both sit on their own lines. The bug was
   silent (no exception; the sums were just 0), caught only by manually
   inspecting `topic_taxonomy_live_parsed`'s length (4, obviously wrong
   for a page claiming ~200 named topics) before trusting the output.
   Fixed with `\s*` on both sides of the `(N)` group.
5. **SymPy walk hung with no traceback.** The very first run of
   `probe_sympy` timed out at the harness's 60s ceiling with no
   exception printed — one ntheory function (never isolated by name,
   not worth the further cost once the fix was general) ran long enough
   under one of the trial argsets to exceed any reasonable per-call
   budget. Fixed generically with a `signal.alarm`-based 2-second
   per-call timeout, not by hunting the specific offending function.
6. **Rosetta Code's MediaWiki API returned "No such action."** Not a
   bug in the probe — the site's `/mw/api.php` endpoint rejected the
   standard `action=query` call live. Reported as a genuine external
   fact (§3.2), not patched around.
7. **`bool` and container results were mis-classified as "not exact."**
   The first `is_exact` pass excluded `bool` (since `bool` is a Python
   `int` subclass and the check order needed to be deliberate) and
   didn't look inside lists/dicts/generators at all, so predicate
   functions (`is_carmichael`, `isprime`-style) and container-returning
   functions (`factorint`, `divisors`) were dumped into "unclassified"
   (72/124 invoked results). Fixed by (a) treating a decidable boolean
   predicate as exact — it IS in-frame, unambiguously — and (b)
   recursing into list/tuple/set/dict/generator results (bounded depth
   2, generators materialised via `itertools.islice` to avoid hanging on
   an infinite one) and requiring EVERY element to be exact. This raised
   the exact count from 52/124 to 107/124 and is the honest, not
   flattering-by-omission, number reported above.

---

## 5. Ranked recommendation

| rank | source | class | why |
|---|---|---|---|
| 1 | **SymPy `ntheory`/`combinatorial.numbers`** | KERNEL | already installed, BSD, 0% inexact measured, ~106 additional exact functions beyond `reason.py`'s current set, minutes of wiring cost |
| 2 | **Metamath `set.mm`** | PROPERTY | CC0 (zero licence friction), single regular grammar (cheapest mechanical walk of the three formal libraries), proof form structurally closest to `Unify`/`AntiUnify`; ~6,000-theorem actionable slice (integer/finite, pre-subject-filter) out of 47,625 |
| 3 | **python-flint / cypari2** | KERNEL | in-process FFI (admissible under the "no shelling out" rule that excludes GAP), exact, LGPL/GPL — not installed here (scope), pip-installable |
| 4 | **Isabelle AFP** | PROPERTY | best-labelled source for "verified algorithms" specifically (208 entries pre-classified by the source itself); BSD/LGPL; heavier per-entry parse cost than Metamath (full HOL term language, not a flat grammar) |
| 5 | **Lean mathlib4** | PROPERTY | largest and most actively maintained, Apache-2.0, but highest measured impedance — 54% of files are type-class-abstract (a third impedance axis beyond real-vs-integer) on top of the usual real-analysis weight, and full elaboration-level parsing is the most expensive of the three formal libraries |
| — | **GAP** | KERNEL | EXCLUDED under the current architecture (no in-process binding) |
| — (flagged, not ranked) | **OEIS** | CONTENT | already integrated and measured (8/8 live today) — not a new decision |
| — (flagged, not ranked) | **Rosetta Code** | CONTENT | mechanically walkable (312 language sections on one task, confirmed live), GFDL 1.3 attribution cost, API path broken live — a preregistered bet if pursued, per the project's six-null standing rule, not a default import |

**Operator vs. content, stated once, plainly:** SymPy, mpmath, FLINT,
PARI, GAP are OPERATOR imports — import freely, gated only by the
architecture checks in §1 (exactness, in-process binding), not by the
content-bet null rule. Metamath, mathlib4, AFP are PROPERTY imports —
same freedom, since a theorem is a fact about a domain, not a task
outcome the eval was tuned against; the yield estimates above (§2) are
honest upper bounds pending a subject-matter overlap filter against the
actual MBPP/ARC unreached populations, named as the necessary next step,
not performed here. OEIS and Rosetta Code are CONTENT imports — subject
to the project's own six-null standing rule; OEIS already cleared that
bar live, Rosetta Code has not yet been tried and should be
preregistered, not assumed, if pursued.
