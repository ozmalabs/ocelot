# Review of `09_adaptability.tex` (draft-2026-09-02.1, r91) — proposal for fixes

Scope: the whole file (1448 lines, 24 pp), its log, the companions it draws
on (00 r121, 01 r278, 01b r39, 02 r26, 04 r20, 06 r27, 09a r5, 10 r4), and
the repository record for every figure it reports. Line numbers are r91.
Nothing applied.

Compile: 0 warnings, 0 overfull, 33 citations, all cited. No
implementation identifiers. The by-name reference check passes. The first
five sections (`sec:not-intelligence` → `sec:counter`) plus `sec:priors`,
`sec:oracle`, `sec:prior` and the falsifier list are a tight theory paper
of about nine pages and are the best statement in the set of the ladder,
the Occam ordering, the regime split, and `prop:no-prior-free`. **The
findings are structural: the paper's own opening says the consequences
live in the applied companion, and then fourteen of its twenty-four pages
are those consequences; one remark was written for the geopolitical paper
and refers to material that is not in this one; "the companion" names five
different papers; and three record claims are misread or unlocated.**

Constraint on every fix below: **twenty labels in this file are cited by
10 r4 and 01c r7** (`AD-rem:nowhere` ×12, `rem:timing` ×8, `rem:exchange`
×8, `rem:chollet` ×7, `rem:schedule` ×6, `rem:race` ×4, `rem:phase`,
`rem:interval`, `rem:individual`, `prop:no-prior-free` ×3 each, `rem:unit`,
`rem:scarcity`, `rem:reconstruct`, `rem:building` ×2, `sec:priors`,
`sec:ladder`, `rem:plural`, `rem:expertise`, `rem:direction`,
`rem:contingent` ×1). Every one must survive, under the same name, and
00 → 01 → 01a → 09 → 10 compile order must be kept.

---

## A. The paper contradicts its own scope statement, by fourteen pages

l.43–46: "*An applied companion carries the consequences this paper does
not.* Those consequences run inside one frame — contemporary geopolitics
and the institutions of an industrial civilisation — at a length that
would dominate a paper about a capability. They are developed separately
… Nothing here depends on it."

Then l.326–1176 — `rem:schedule` through `rem:exchange`, fourteen remarks
in `sec:persons` alone, ~850 lines — carry: the copy result; persons;
institutions made contingent; intellectual property; the rule-from-nowhere
basin; a signed-error argument for a half-century window (l.680–685, "on
the present author's reading … within roughly the next half-century");
the percolation theorem; convergent pressure; the harness-migration
literature; the unit of measurement; "the phase change is not pending: it
began" (l.1016–1018); the fixed-vs-compounding race; "the binding
constraint is one person, and it is already exceeded"; and a seven-year
\$58 billion interceptor contract. That is the applied paper, inside the
theory paper, at a length that dominates it — the exact outcome the
opening says was avoided.

**Fix (recommended).** Keep every label where it is (constraint above),
and make the paper honest about what it contains:

1. Replace l.43–46 with a true scope sentence: the paper has two parts;
   Part I (`sec:not-intelligence` → `sec:oracle`, `sec:prior`,
   `sec:falsifiability`) is the theory; Part II derives consequences at
   the frame of substrates, persons and institutions **without leaving the
   account's own terms** — no geopolitical evidence is used here; the
   geopolitical paper applies Part II to one frame with evidence and is
   assessed separately.
2. Give Part II real sections instead of fourteen remarks under
   `sec:persons`: *Schedules of payment* (`rem:schedule`, and move
   `rem:oracle-cost` next to it), *Persons* (`rem:direction`,
   `rem:persons`, `rem:reconstruct`), *Institutions* (`rem:contingent`,
   `rem:scarcity`, `rem:nowhere`), *Projection* (`rem:phase`,
   `rem:percolation`, `rem:method`, `rem:convergent`, `rem:present`,
   `rem:unit`, `rem:building`, `rem:interval`, `rem:timing`), *Capacity*
   (`rem:race`, `rem:individual`, `rem:expertise`, `rem:exchange`). Section
   labels new; remark labels unchanged.
3. Move the falsifier list after Part II and extend it (E).

The alternative — moving Part II into 10 — would cost 10 all eight of its
`AD-rem:exchange` and twelve `AD-rem:nowhere` citations and 01c its two,
and would put the *derivations* (which use no evidence) into the paper
that is supposed to be assessed on evidence. Not recommended.

---

## B. `rem:exchange` was written for paper 10 and refers to things that are not in this paper

l.1145: "Calling the interceptor stocks *non-financeable* was crude" —
nothing in 09 calls anything non-financeable. l.1151: "the seven-year
contract … what \$58 billion buys" — no contract is introduced in 09; it
is 10 l.288–293. l.1156–1157: "Which corrects something running through
this whole section. Capacity has been treated as one pool" — no section of
09 treats capacity as one pool. l.1157: "The buffers named above" — no
buffers are named above. l.1159: "which the applied companion finds
degrading" — 10 is the applied companion, so this remark is 10 quoting
itself from inside 09.

Yet 10 cites `AD-rem:exchange` eight times, for the *general* claim: money
converts between frames at a rate; one rate (into individual capacity)
does not exist; a stipulated conversion is not a measurement. That general
claim is correct and belongs here.

**Fix.** Rewrite `rem:exchange` self-contained, in the account's terms:
(i) Narrativium's `NV-prop:no-sum`, `NV-def:conversion`,
`NV-rem:kappa-kinds` cited by number; (ii) the three capacities as three
frames — fiscal, materiel, and the capacity to revoke a frame — stated
generally; (iii) the non-existent rate, from `rem:expertise` and
`rem:individual`; (iv) the stipulated-versus-principled caution. Delete
the interceptor sentence, the \$58 billion, "was crude", "this whole
section", and "the buffers named above". If a worked instance is wanted,
one sentence: "the geopolitical paper reports a materiel case in which the
fiscal-to-materiel rate was measured at seven years" — with a `GP-`
cross-reference once 10 has a prefix, or without one.

---

## C. "The companion" names five papers, and Axiom −1 names none

Occurrences and what each actually refers to:

| line | phrase | paper |
|---|---|---|
| 27 (box) | "the companion reports what is built" | 09a |
| 141 | "the assessment companion" | 06 |
| 155 | "the companion programme" | the record (06/09a) |
| 225 | "the companion's first proposition" (a frame holding nothing is no frame) | 00 `IS-prop:is` |
| 231, 356, 480, 509, 578, 870, 640 | "Axiom −1" | 01 `GE-ax:no-view`, never said |
| 318 | "the companion programme is an instance" | 06 |
| 323, 339 | "the companion on assessment" | 06 |
| 347 | "the companion's Definition of a frame … $\mathcal{B}_{W:G}$" | 01 `GE-def:frame` |
| 400 | "the substrate paper states, unhedged, … functional identity" | 01 `sec:scope` l.168 |
| 451 | "the companion reports that the faculty … is not yet resident" | 09a `rem:selfrepair` |
| 564, 581, 971, 1146 | "the Narrativium companion" | 04 |
| 579, 739, 934, 1095 | "the theory companion" | 01 |
| 596 | "the companion's proposition … no veto over world-caused change" | 01 `GE-prop:self-governance` |
| 615 | "a Seldon manifold" | 02 |
| 620, 965 | "the companion on manifolds" / "carrying it says so in a section heading" | 02 `SM-sec:prediction` ("Reachability rather than point prediction" — verified) |
| 715, 1159 | "the applied companion" | 10 |
| 787 | "the companion on what can exist" | 00 `IS-prop:is`; the types clause is 01 `GE-rem:types-forced` |
| 1130 | "the psychological companion reports at length that within-frame quality does not transfer out of its frame" | 01b — **not located** (no "within-frame", "transfer" or "quality" passage in 01b r39 says this); verify or drop |
| 1170 | "the companion insists on" (principled vs stipulated conversion) | 04 `NV-rem:kappa-kinds` |

**Fix.** Naming sentence in the box (the adaptability implementation
paper; *Is*; Graphic Equalisation; the mind companion; *Seldon*;
*Narrativium*; the assessment paper; the geopolitical paper) with the
"inherits their definitions, epistemic boundary, and level-of-claims"
clause; `xr-hyper` with `IS-`, `GE-`, `MS-`, `SM-`, `NV-` (and an `AS-`
prefix for 06 if 06 has labels worth citing — its section labels exist:
`AS-sec:substrate-size` for the decoder seed, `AS-sec:estimate` for the
language-model half); every row above converted to a resolving number;
"Axiom −1" → "Graphic Equalisation's Axiom~\ref{GE-ax:no-view}" at first
use and "Axiom~\ref{GE-ax:no-view}" after.

One reference the paper *should* make and does not: `rem:schedule`'s copy
argument ("a graph copy copies a competence … name a property the original
has that the copy lacks") is 01's **Proposition
`GE-prop:copyable-generators`** (Copyable generators are a difference in
kind). Cite it; 09 is applying 01's result, not deriving a new one.

---

## D. Record claims: one misread, one unlocated, one to cite

1. **`rem:oracle-cost` l.318–320: "Roughly half its implementation was
   performed by a language model … enforced by a switch and a gate."**
   06 `sec:estimate` l.650–657 says something different: self-*direction*
   and self-*implementation* are two halves of self-modification; the
   first has been exercised extensively by the substrate; the second —
   *writing the resulting structure* — was performed by a language model
   and is deliberately not built. "That half" is a half of a
   distinction, not a proportion of the implementation. **Fix:** "the
   substrate directs its own acquisition and does not write it; the
   writing was performed by a language model (06 by number)". The "switch
   and a gate" enforcement is not in 06 and was not found in the record
   under that description — name what it refers to or drop it.
2. **`rem:chollet` l.253–256.** The failure-baseline clause is verified
   against the record (the baseline carries commit, engine hash and path,
   condition, measurement time, load average at start and end, worker
   count). "Its psychological runs name the machine and whether the box
   was shared" was **not found** in the psychology record; the only
   "shared box" sentence located is in an engine pre-registration. Drop
   the psychological half or replace with what is there.
3. **`sec:counter` l.158–169** (synthesis 54/257 both arms; composition
   +21 pp CI-separated) and **`rem:schedule` l.339–340** (decoder seed
   byte-identical by hash across seven consuming frames) are verified
   against the record and 06. They need 01's evidence-standard sentence
   once (`sec:counter` first use): a pre-registered implementation record
   not circulated with these papers.

---

## E. Falsifiers

1. No `[shape]`/`[detail]` definition. Add 01's sentence verbatim before
   the list.
2. The ten items cover Part I only. Part II has ~850 lines with no
   exposure. Add:
   - `[shape]` **A graph copy copies a competence** (`rem:schedule`):
     fails on a property of the original that the copy lacks which is not
     a property of the move (change of world).
   - `[detail]` **A rule without a declared frame has no free exit**
     (`rem:nowhere`): fails if a rule asserted absolutely is shown revoked
     at the container's cost (Δg = 0) rather than through the contained
     state.
   - `[shape]` **Compressors approach the ladder** (`rem:convergent`):
     fails on a general compressor whose moves against a residual are not
     among the four.
   - `[detail]` **Model figures understate arrangements** (`rem:unit`):
     fails if, on a fixed test, a model evaluated cold is not exceeded by
     the same model in a harness it was allowed to build.
   - `[detail]` **The fifth quantity is not negligible** (`rem:present`):
     fails if the share of a harness-heavy system's competence held
     outside its opaque part is measured and found immaterial.
3. After the list, one sentence: the half-century judgement
   (`rem:phase`) and "the phase change has begun" (`rem:timing`) are
   recorded judgements with named inputs, not falsifiers; a reader
   contests them by contesting an input.
4. Item 7 (`[detail]`, benchmark measures a relation) currently has its
   test recorded as "untested" at l.283–284 — good; say in the item that
   the LeGris dataset is where it would be run.

---

## F. Narrated drafting

The set's rule since 7309f2b9: a paper is what it says now. Sites:

| line | phrase |
|---|---|
| 183 | "this section exists because the first version of it made that error" |
| 241 | "less of it survives than the previous sentence of this paragraph once claimed" |
| 802 | "which the list did not say" |
| 1145 | "Calling the interceptor stocks *non-financeable* was crude" (B) |
| 1156 | "Which corrects something running through this whole section" (B) |

State each positively; keep the history here.

---

## G. Bibliography and mechanical

- `\begin{thebibliography}{9}` with 33 entries → `{99}`.
- Order is not alphabetical: `legris2025` after `miller1956`; `block1972`
  after `newell1973`; `percolation2026` (Diskin) after `onsager1931`;
  `prade2014` last. Sort.
- `spelke2006` → **2007**: *Developmental Science* 10(1):89–96 is the
  January 2007 issue.
- `legris2025`: verified — *Scientific Data* 12, article **1380**, 2025;
  add the article number (the entry currently has volume only).
- `percolation2026`: verified — the arXiv title is "Supercritical
  sharpness of percolation" (arXiv:2603.03257, March 2026), not "… for
  percolation on transitive graphs"; give the arXiv id and the exact
  title, keep the Quanta date (31 August 2026, correct). The remark's
  "completed in December 2025" should read "posted March 2026" or cite
  Quanta for the December date.
- `zhou2026`: verified (arXiv:2604.08224, April 2026, 21 authors). Three
  authors + `et~al.` in the entry rather than all twenty-one.
- `prade2014`: give the volume (*Computational Approaches to Analogical
  Reasoning*, Studies in Computational Intelligence 548) or cite the
  journal version.
- `\texorpdfstring` on the `\date` dashes.

---

## What is right and should not be touched

- `def:adapt` and its three words; `rem:one` ("the second is what the
  first looks like when the objects are rules rather than observations").
- `rem:occam`: a mint that survives the earlier rungs is a claim about the
  held set; the two failure directions.
- `sec:counter` and `rem:plural`: the regime split, and "the mechanism can
  be present and idle with nothing indicating so".
- `prop:no-prior-free` and its proof; `sec:prior`'s "the origin is not in
  the space" as the one thing added to generalizability theory.
- `rem:chollet`'s four-place arrangement and "those are not hygiene, they
  are the coordinates".
- `rem:nowhere`'s "absoluteness is the removal of a rule's exit", and the
  correction that world-forcing is untouched.
- `rem:percolation`'s "the theorem applies to no object in this
  programme" stated first.
- `rem:interval`: the interval is over futures, not years.
- `sec:prior`'s treatment of Levy–Goldberg / Linzen: the critique does not
  transfer because the operation is exact and refuses.

---

## Suggested order

1. **A** — scope sentence and Part II sectioning (labels untouched).
2. **B** — `rem:exchange` self-contained.
3. **C** — naming, `xr-hyper`, `GE-prop:copyable-generators`.
4. **D** — the language-model half; the psychology clause; evidence
   sentence.
5. **E**, **F**, **G**.
