# History and context

This document exists because of a specific, otherwise-irreversible loss: on
2026-08-10, this project was extracted from a private monorepo
(`ozmalabs/internal`) into its own standalone repository, and the extraction
squashed roughly 4,000 commits of granular development history into a
handful of commits (`git log --oneline main` currently shows 27). That
history is not recoverable from this repository's own `git log`. It still
exists in `ozmalabs/internal`, on the path `research/experiments/gamma-substrate`,
and this document was written by walking it directly — via the GitHub API,
not from memory or inference — so a reader of this standalone repo can get
the context the git history itself can no longer provide.

Everything below is sourced from one of: the internal repo's real commit
history (`gh api repos/ozmalabs/internal/commits?path=research/experiments/gamma-substrate`,
paginated across 4,002 unique commits, spanning 2026-05-29T13:55:29Z to
2026-08-10T11:58:56Z — both endpoints read directly off that API response,
not estimated); the two theory documents (`paper1.tex`, `infinity_paper.md`)
fetched fresh from `ozmalabs/internal/research/docs/`; and this repo's own
existing research record (`docs/research/theory_convergence/`,
`docs/research/engine_substrate/`). Where CLAUDE.md's own dated log is used
as a secondary source, its commit-hash citations were spot-checked against
the real internal-repo history (§3) before being trusted.

---

## 1. Origin

The theory came first. The creator's own framing, given directly for this
document: *"the history is in ozmalabs/internal ... this project is
supplied as proof to support it."* "The Law of Graphic Equalisation — Theory"
(Matthew Parslow) is an axiomatic paper about typed graphs, an admissibility
grammar (Γ) that governs what compositions on the graph are permitted, and
what happens when that grammar is made reflective — able to operate on
itself. Its central identity: *a grammar that admits self-modification IS a
compound loop*, not a mechanism that produces one or is improved by one. The
paper derives four expressibility theorems, three bound theorems (on
encoding cost, computational efficiency, and behavioural admissibility), a
four-level threshold hierarchy (τ0 operational → τ1 reflective → τ2
comparative → τ3 nomological), and states its falsifiers explicitly at every
scope it makes a claim.

This repository is the engineering-side proof of that theory, not an
independently-conceived agent architecture that happened to resemble it
afterward. The very first commit on the path, `ebb8b636`
(2026-05-29T13:55:29Z), is titled *"(G,Γ) substrate — curious agent,
graph-resident math tower, inverse inference, end-to-end language faculty"*
and its body states the rule this project has held ever since, on day one,
not as a later correction: *"Python only runs the graph and interfaces to
the world."* The `(G, Γ, C)` notation — typed graph, admissibility grammar,
consistency checker — that names this repo's whole architecture (see
`CLAUDE.md`'s second line) is the paper's own notation, used from the start.

A companion paper, "Approaching Infinity: Unbounded Reflective Depth"
(same author), formalises how the same reflective substrate grounds
unbounded structure: a *reflective tower* $R_0, R_1, R_2, \ldots$ where
$R_{n+1} = \psi(R_n)$ is the graph's representation of its own prior state.
Where $\psi$ is periodic, the tower stabilises at a fixed point (Tarski–Knaster,
Kleene's recursion theorem, Scott's $D_\infty$ are named as instances of this
case); where $\psi$ is aperiodic, the tower never stabilises and Theorem 1
proves it generates the natural numbers as an emergent, ℕ-indexed structure —
infinity as an absence of a base case, not a primitive quantity. This repo's
own verification of that claim against the running Rust code
(`docs/research/engine_substrate/SELF_REFERENCE_INFINITY_GROUNDING.md`,
§7 "CORRECTION") confirms the two papers' claims are precisely
complementary rather than redundant: self-reference (Axiom 3) is the
necessary precondition for a $\psi$ to iterate at all; aperiodicity is the
separate, sufficient condition that turns iteration into unboundedness
rather than a reflexive fixed point.

## 2. The shape of the development history

**Scale.** 4,002 commits on `research/experiments/gamma-substrate` across
74 calendar days (2026-05-29 to 2026-08-10), with commits recorded on 71 of
those 74 days. By month: 91 in the four days of late May, 1,953 in June,
1,812 in July, 146 in the first ten days of August. That is not a steady
trickle — the busiest single days on record are 2026-07-20 (162 commits),
2026-07-29 (153), 2026-06-05 (143), 2026-07-28 (138), and 2026-07-31 (126).
The first week alone (through 2026-06-04) already carries 313 commits: by
the end of day two (2026-05-30), the project had already run through six
numbered "Phase" migrations moving a renderer out of Python and into
graph-resident `RenderRules` — commit `546824a3`, *"Phase 6.5 — remove
static Python+Rust renderer dispatch"* — meaning the "no Python decision
logic" rule that `CLAUDE.md` now states as settled architecture was being
actively enforced, live, within 48 hours of the project's first commit, not
decided in the abstract and applied later.

**What kind of work, not just how much.** Skimming across the timeline
(rather than reading every commit) shows a consistent register: commit
subjects are not conventional one-liners but headline-length findings,
frequently in capitals, frequently naming a specific mechanism and its
failure or confirmation in the same breath. A few, verbatim, spread across
the timeline to show the register holds throughout, not just at the
showcase moments already documented in `CLAUDE.md`:

- `26203990` (2026-06-09) — *"ORDER-N COLLAPSE: the lever — solves 11/11,
  cracks the scaling wall (signal from noise)"*
- `f9787cc9` (2026-07-16) — *"RUNG 4 IS BUILT — AN ORIENTATION MAP FORMS
  FROM WAVES ALONE, WITH NO VISION: the lateral interaction is what makes
  it (interaction -6.91, p<0.0001, n=70)"*
- `4347e98b` (2026-08-06) — *"A DERIVED RELATION MUST NOT OUTLIVE ITS
  PREMISE: dominance retraction"*
- `d9c7628f` (2026-08-07) — *"CARRIAGE PASSES THROUGH A WELD: nine severed
  edges, five orphaned joint groups, and a reason that was wrong"*
- `65b8eb9d` (2026-08-09) — *"THE BALANCE TERM WAS SWITCHED OFF: one
  undeclared operator switch, and the lateral axis fixed"*

That register is a discipline, not a writing style. A pre-registration
culture is explicit in the subject lines themselves: "PREREG" appears in
220 commit subjects, the first at `1ec1801b` (2026-07-17, *"PREREG-2 — the
ORBIT LAW, prospective (PREREG-1's prediction is REFUTED)"*), and 200 of
those 220 land in July — the predict-before-measuring discipline that
`CLAUDE.md`'s own retracted-baseline paragraph describes was not a
constant background practice; it crystallised and then intensified in the
second half of the project, becoming the default mode by which new claims
were made admissible. "RETRACT"/"RETRACTION" appears 29 times, "DELETED" 14
times, "CORRECTION" 62 times, "RUNG" 197 times (the sd-loop growth-ladder
vocabulary that `CLAUDE.md`'s 2026-07-02 entries describe), "LANDED" 51
times. These are not incidental word choices — they are how this project's
own culture marks a load-bearing turn, and they hold steady across the
whole 2.5 months, not just at the entries `CLAUDE.md` chose to narrate.

**Domain breadth, dated against when it actually started** — not just
what `docs/research/`'s 15 topic folders (~1,125 markdown files total, per
`find docs/research -name '*.md' | wc -l` against the current tree) hold
today, but when each line of work actually began, read off the commit
history itself:

| Domain (`docs/research/` folder today) | First trace in commit history | Note |
|---|---|---|
| `psychology_affect/` | 2026-05-30 (`7a20f823`, "psychology Mt + theory of mind concepts") | Day 2. |
| `audio_speech/` | 2026-06-02 (`bcc6d016`, AudioWorld) | |
| `ls20/` (spatial/maze navigation, ARC-AGI-3 live play) | 2026-06-19 | |
| `program_synthesis/` (ARC-AGI grid puzzles) | 2026-06-15 (`b3b6fb3b`, "pivot to ARC — assess v3, start a grid DSL + generate-and-select solver on ARC-AGI-1") | Explicit pivot, not a gradual drift. |
| `vision/` | 2026-06-05 (`94804027`) — intensifies sharply from mid-July (the "THE EYE"/orientation-map/sd-loop-for-vision arc) | 376+ documents, by far the largest folder. |
| Omniglot / handwriting (mostly filed under `vision/` today) | 2026-06-23 (`bcd529dc`, "scale the motor-AbS writing recogniser to REAL handwriting") | The ten-run arc CLAUDE.md documents in detail runs 2026-07-02/03. |
| `doom/` | 2026-06-20 (`cef49c4f`, angular raycast projection) | |
| `bigville/` (social/economic simulation) | 2026-07-28 (`f7e8088b`, "bigville-drama (245000): PREREG") | 162 documents in under two weeks — the single most intense late-project burst. |
| `humanoid/` | 2026-07-29 | |
| `flight_control/` (F-16 / drone fault-tolerant control) | 2026-07-28 (in-flight propeller-failure adaptation) | Landed in the same 48-hour window as bigville and humanoid — a deliberate multi-domain generalisation push, not three unrelated efforts. |

The `bigville`, `humanoid`, and `flight_control` domains are worth reading
together: all three begin within the same 48-hour window at the very end
of July, all three are explicitly about a single graph-native agent
adapting across genuinely different embodiments and environments (a town
economy's social/legal rules, a humanoid body's effector authority, a
fixed-wing aircraft's damaged control surfaces), and — per the theory
convergence audit (§4) — all three independently produced closely related
findings about scoring/objective design (the "scoring a STATE as though it
were an OBJECTIVE" defect, found in the F-16 arc and reproduced within an
hour in the humanoid arc, `docs/research/humanoid/EFFECTOR_AUTHORITY_COLLAPSE_RESULTS.md:105-108`).
That is the project's late-stage character: not new isolated demos, but the
same substrate stress-tested across maximally different bodies and worlds
to find what generalises and what does not.

**A density note, not a citation error.** CLAUDE.md's dated log cites commit
`c0288920` (2026-07-02T08:57:35Z) as where handwriting-as-dynamic-quantization
"landed." Its actual subject line is *"OPERATOR CONSOLE + FOUR FRONTIERS —
the jabberwock is persistent, embodied, and self-experimenting"* — a
different-sounding headline. Checked directly against the internal repo:
that single commit's file list does include `strokes.rs`,
`stroke_codebook.py`, `stroke_library.py`, and `seeds/stroke_shapes.json`
alongside an always-on daemon, a webcam/browser/voice sensing bundle, and a
self-experimentation dispatch loop — four substantial, otherwise-unrelated
fronts landing in one commit. This is not a bad citation; it is a real
property of how this project's commits are shaped at its most intense
points: several days of parallel work land together, and the subject line
names the piece the author judged most significant, not everything the
diff touches. A reader treating any single commit hash in `CLAUDE.md` as a
complete description of that commit's contents should read the commit
itself.

## 3. Major turns, dated and cited

The following is not a re-listing of every `CLAUDE.md` heading — read
`CLAUDE.md` itself for the full, ongoing dated log. This is a synthesis of
what this document's own investigation of the raw commit history considers
genuinely load-bearing, cross-checked against `CLAUDE.md` where it overlaps.

**2026-05-29 — origin.** `ebb8b636`, the founding commit: the (G,Γ) typed
graph, a Term-tree DSL, a "curious agent" whose reasoning is graph-resident,
and — already — the rule that Python only runs the graph. 391 tests passing
at commit 1.

**2026-05-30 — the architecture rule is enacted, not decided.** Six
numbered "Phase" commits (`c19feb82` through `97dc331f`) move a working
Python+Rust renderer entirely into graph-resident `RenderRules` over the
course of one day, ending in `546824a3` deleting the static dispatch. This
is the first live instance of the pattern this repo's `CLAUDE.md` would
later formalise as a standing rule: found, fixed, migrated to the graph, in
hours, not planned as policy first.

**2026-06-15 — the pivot to ARC.** `b3b6fb3b`, *"pivot to ARC — assess v3,
start a grid DSL + generate-and-select solver on ARC-AGI-1 (13/400 train
solved, 92.9% precision, clean abstention)."* The `program_synthesis`
domain (99 documents today) and the live ARC-AGI-3 play (`b9b25456`, same
day: *"the curious agent plays LIVE ARC-AGI-3 — real protocol, real
client, genuine exploration; honest 0/7"*) both begin here.

**2026-06-18 — CuriousAgent deleted, migration complete.** `56529c6d`,
*"BURN THE HULL — delete CuriousAgent: the migration is complete."*
Verified directly against the internal repo (matches `CLAUDE.md`'s citation
exactly, including timestamp `2026-06-18T13:35:58Z`). The ~13K-line Python
`CuriousAgent` class — the entire pre-migration agent — is deleted outright;
the seed-booted `WorldAdapter` over the Rust substrate becomes the only
agent runtime. Two same-day follow-up commits (`9d4b3c6d`, `9977e2a0`)
record this in project documentation as complete, "not in-progress" —
notable because it means the migration-complete claim was itself treated
as a fact requiring a dedicated, separately-committed correction to the
project's own record, the same epistemic discipline later applied to
research claims.

**2026-07-02 — composer/driver migration and the dynamic-quantization
crystallization, in one of the densest 24-hour stretches in the whole
history.** Between `28454782` (03:48:35) and `d2cd7bed` the next morning
(02:05:02) the internal repo records **53 commits** — verified by counting
the raw timestamped list, not estimated. Inside that window, on at least
three visibly parallel tracks: the self-build composer and the order-N
growth loop move from Python beam search into a single Rust `ShapeDecode`
term and a `run_rules` fixpoint over seeded rules (`28454782`); quanta
navigation lands the same reframe applied to spatial belief (`b5c7bffb`,
05:44); transformation is reframed as "quantum change in a specific
dimension" (`518706ed`, 06:50) and dimension inference completes the growth
ladder (`65f94b70`, 07:32); handwriting/stroke recognition is folded into
the same machinery (bundled inside `c0288920`, 08:57, alongside the
console/sensing work noted below) and then run through a ten-run Omniglot
measurement arc (`26f74039` through `42855d5f`) in the same stretch; and,
concurrently, a wholly separate speech-acoustics track (APC context-
predictive front-end, real-accent transfer, a language→perception bridge
on real cochleagrams) and a separate experiment-composer graph-migration
track both land in the same window. This is not CLAUDE.md compressing a
week into one narrated paragraph — the internal repo's own timestamps show
it really did happen in under 24 hours, on multiple fronts at once.

**2026-07-03 — the powered-gate correction.** `f0fae1fe`, *"RUN 15 — THE
POWERED GATE CORRECTS THE ARC: honest ceiling 26.8% [22.6,31.3] on 10
alphabets (the 4-alphabet set was an easy subset); EVERY post-composition
delta was 1-3 episodes of noise."* A full day-15-run Omniglot arc,
apparently converging toward ~38%, is corrected downward by re-running under
proper statistical power — and the very next day, `7743c2de` (2026-07-03,
06:28), *"RUN 16 — RECONCILED: the old ~81% and the powered 26.8% were BOTH
real, and the difference was the VERDICT COMPARATOR all along... 73.5%
[67.0,79.1]"* resolves the apparent contradiction by identifying that
different verdict comparators, not different mechanisms, explained the two
numbers. This exact sequence — an honest downward correction under power,
followed the next day by a reconciliation that neither retracts the
correction nor the earlier number, but explains both — is as good a single
example as exists in the record of the project's stated discipline that "a
baseline must be a list, never a count," applied to its own results.

**2026-07-16/17 — the vision development arc's honest-null density.** In a
36-hour window, at least seven `PREREG`/`RETRACT`/`CONFIRMED` commits fire
in sequence on a developmental-vision (waves→orientation-map) arc: Stage 1's
"biology emerged" is retracted (`6c3a5a56`), rung-2 fails three times then
partially succeeds with an inverted finding (`cdbf005f`, `9c88d4ae`), rung 3
is built and separately found NOT built on a different sub-claim
(`f9787cc9` vs `fff6189b`, same day), and `f2c3bb65` distills the whole arc
into a written protocol: *"VISION_PROTOCOL.md — the rigor rules, distilled
from ten pre-registrations (nine failed) and three retracted results."*
Nine failures out of ten pre-registrations, reported as a headline in the
commit subject itself, is a strong data point for how seriously this
project's honest-null discipline was actually followed under real pressure,
not merely stated as a value.

**Late July into early August — the multi-domain generalisation push.**
Covered in §2 above: `bigville`, `humanoid`, and `flight_control` all begin
within roughly 48 hours of each other (2026-07-28/29), and by the time this
document's data was pulled the internal repo's most recent commit
(`32dd6020`, 2026-08-10T11:58:56Z, *"RUNG 5 NULL + the per-term
decomposition, WITH ITS PLACEMENT BUG NAMED"*) is still working the same
rung/PREREG discipline on presumably humanoid/effector work, unbroken, right
up to the day of extraction.

**2026-08-11 (this standalone repo, post-extraction) — "shapes not
numbers."** Not part of the 4,002-commit internal history — a commit made
directly in this new standalone repo (`89dd423`) — but worth recording
because it crystallises a lesson the internal history's own late-project
convergence produced: *"the sd loop and the admissibility grammar (Γ) are
the two generative primitives new work should compose with; scalar knobs
and rules that bypass `check_edge` are unpaid debt, per the F-16, humanoid
and bigville retrospectives measuring the same collapse independently three
times."* That is a direct, explicit reference to the same convergence this
document's §4 discusses formally.

## 4. The theoretical relationship, precisely stated

This repository's relationship to "The Law of Graphic Equalisation" is not
"inspired by." Per the creator directly, and confirmed by the commit
history (the paper's own `(G, Γ)` notation appears in the founding commit),
it is: **implementation of, and evidentiary support for.** The theory came
first; this codebase was built to be its proof.

That is a strong claim, and this project's own house discipline — state
falsifiers, report honest nulls as prominently as confirmations, never
round a list up into a bare count — requires it be qualified exactly as
precisely as the theory itself is. `docs/research/theory_convergence/THEORY_CONVERGENCE_AUDIT.md`
is a systematic, file-and-line-cited audit asking the sharper question:
does this repo's engineering, solving unrelated problems under its own
pressure, independently rediscover the theory's structure — not because
someone read the theorem and applied it top-down, but because the same wall
got hit twice? Its tally, exactly as reported there:

- **9 instances of genuine independent convergence**, across 6 mutually
  unrelated domains (F-16 flight control, social/governance simulation,
  ARC-AGI program synthesis, physics-as-cognition engineering, vision
  perception, speech acoustics). The single strongest finding is not a
  matched theorem but a matched *method*: the same generative move — reject
  what a stuck question presupposes rather than answer it as posed, exactly
  Axiom 0's own worked example — was independently articulated, unprompted,
  in writing, in at least three of those domains, one of them (the F-16
  arc) four separate times within one investigation.
- **3 explicit cross-references**, where one domain's write-up names having
  found "the same as" another domain already in this repo (most notably,
  the humanoid-domain arc explicitly quoting and reusing the F-16 arc's own
  diagnosis within the hour).
- A substantial **application layer** (the theory's own Γ/admissibility
  vocabulary used deliberately, top-down, as a design tool — e.g.
  `docs/research/bigville/BIGVILLE_ADMISSIBILITY_GRAMMAR.md`'s explicit
  citation of "Paper §1, Definition 2") — valuable as proof the framework is
  actually used, but explicitly excluded from the convergence count because
  it is not independent by construction.
- **5 of the paper's 9 checklisted sharpest signatures were searched for
  systematically and found nowhere independently** in this repo's ~1,100
  research documents: relative regression / island flightlessness, the
  τ-hierarchy's percolation-style capability discontinuity, the
  compression/translation/Γ-projection three-way split, the strict
  compound-loop identity claim stated verbatim, and Theorem XII's binary/
  continuous "hard edge" stated as its own explicit claim. The audit is
  explicit that this is a clean, reportable null, not a search failure —
  the paper's most exotic, most quantitatively-dressed content has, on this
  evidence, stayed theory.

Separately, `docs/research/engine_substrate/SELF_REFERENCE_INFINITY_GROUNDING.md`
verified the paper's Axiom 3 self-reference/infinity claim directly against
the running Rust code (not against paraphrase), including a `§7 CORRECTION`
added after the companion infinity paper was supplied, which resolved an
open question the first pass had left honestly unresolved rather than
silently patching over it. And `docs/research/engine_substrate/COGNITION_IS_PHYSICS_LITERATURE.md`
independently arrived at a "dissipation is inference" unification (one
integer relaxation dynamics read simultaneously as thermodynamic dissipation
and MAP inference, confirmed by a break-one-breaks-both falsifier) through
its own literature research — not by reading this theory paper, which is
not cited in that document — and only afterward found it consistent with
the wider active-inference/Friston literature the theory paper also touches.

The honest bottom line, in this project's own words (from the audit's own
verdict): *"this audit supports the cross-domain-independence claim as real
and non-trivial ... but it does not support the paper's full apparatus
uniformly ... A reader should walk away believing the identity claim and
the admissibility/integrity claims are doing real independent work in this
repo's engineering history, and treat the phase-transition/percolation
formalism and the relative-regression claim as still awaiting their own
evidence."*

## 5. Extraction to standalone

On 2026-08-10, this project was extracted from `research/experiments/gamma-substrate`
inside `ozmalabs/internal` and imported into its own repository,
`ozmalabs/ocelot` (this repository). The import is `26ca9ff`, *"Initial
import of ocelot project."* Everything since — the README rewrite, the code
map, the docs reorganisation (`3f9d7c3` moved 1,105 root/docs markdown files
into `docs/research/<topic>/`), the theory convergence audit, the
self-reference/infinity verification, and this document — was done in this
standalone repository afterward, starting 2026-08-11.

The extraction is why this document exists. Squashing ~4,000 commits into
an initial import is not a defect in how the extraction was done — a clean
history-free import is the normal, correct way to spin a project out of a
larger monorepo when the internal history is not meant to travel with it —
but it means every piece of context that git history normally carries for
free (when did this domain actually start, what did the author actually
try before landing on the current design, how many honest failures preceded
a confirmed result, what did the project's own commit-message register
sound like under real pressure) had to be independently reconstructed, once,
from the source of truth, before it became unrecoverable by anyone without
`ozmalabs/internal` access. This document is that reconstruction.

## 6. Where to go next

- **`CLAUDE.md`** — the authoritative, actively-maintained architecture
  rule and dated engineering log. Longer and more detailed than this
  document for anything after 2026-06-18; read it for the ongoing,
  present-tense record.
- **`README.md`** — what this repository is and how it is organised, as it
  stands today.
- **`docs/CODE_MAP.md`** — directory-by-directory map of the source tree.
- **`docs/research/INDEX.md`** — the full historical PREREG/RESULTS/plan
  corpus (~1,100 documents), grouped by subject; the detailed record behind
  every summary in `docs/features/`.
- **`docs/research/theory_convergence/THEORY_CONVERGENCE_AUDIT.md`** — the
  full, file-and-line-cited convergence tally summarised in §4 above.
- **`docs/research/engine_substrate/SELF_REFERENCE_INFINITY_GROUNDING.md`**
  — the Axiom 3 self-reference/infinity verification against the actual
  Rust code, including its §7 correction from the companion infinity paper.
- **`docs/research/engine_substrate/COGNITION_IS_PHYSICS_LITERATURE.md`** —
  the independently-arrived-at "dissipation is inference" unification.
