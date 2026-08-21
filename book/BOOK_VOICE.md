# BOOK_VOICE — register, tone, and the style contract

**Status: binding on every chapter.** Read this before drafting any prose.
Companions: `BOOK_PLAN.md` (structure), `BOOK_SOURCES.md` (evidence
locations), `BOOK_DOSSIERS.md` (per-chapter claims).

## The one-line register

**Warm, exact, and unimpressed with itself.** A working engineer explaining
what happened, what it cost, and what it does and does not establish — never a
pitch, never a press release, never a lone-genius narrative. When a claim is
large, the sentence carrying it gets *smaller*, not bigger.

## The three failure modes to steer away from, named

1. **The press register.** `~/ozmadev/internal/research/docs/article_popular.md`
   ("Everything Is Connected — And One Guy Figured Out How") is useful raw
   material and exactly the wrong voice: lone genius, sweeping claim, urgency.
   Mine it for facts, never for tone.
2. **The paper register.** Theorem-first, hedged, passive, method-before-motive.
   Correct for the preprints, fatal in a chapter.
3. **The mystery box.** Narrative-led does not mean claim-withheld. Every
   chapter states what it establishes in its opening paragraph; the story is
   *how the claim was earned*, never a suspense device.

## What "less formal" means, concretely

A style contract, so the loss of formality is a decision and not a drift:

1. **One chapter, one claim, stated in the opening paragraph in plain words.**
   The formal statement can come later; it never comes first.
2. **Theorems and axioms survive as named boxed statements.** Proofs move to an
   appendix or to the paper. A reader should be able to skip every box and
   still follow the argument.
3. **Numbers stay, intervals stay** — and each one gets a sentence saying what
   it does and does not establish. That rule already exists in this project
   (*synthetic-proven mechanism ≠ benchmark value, report both*); the book
   applies it in prose.
4. **Retractions stay in the body, never in an appendix.** They are the
   narrative engine. The drift that reproduced a published signature while
   driving nothing is a better paragraph than anything that worked first time.
5. **A notation budget.** `G=(g,r,Γ)`, residual, and Γ survive the whole book.
   Everything else is local to its chapter and re-introduced there. Γ gets one
   plain-language gloss on first use — *what the graph is allowed to do to
   itself* — and the symbol thereafter.
6. **No forward-referenced jargon.** If a chapter needs a later chapter's term,
   it uses ordinary words and cites forward in a footnote.
7. **Every chapter ends with what would falsify it.** The papers already carry
   falsifiability sections; keep them, de-formalised, as the closing beat.

## Chapter-grain inversion

The same flip applies inside each chapter, and it is what most of the rewriting
work actually is:

1. **Open on a scene** — a measurement, a failure, something that did not work.
   Not a definition, not a literature position.
2. **State the claim in that opening paragraph anyway.** Scene and claim
   together; the narrative earns it, it does not hide it.
3. **Withhold the *mechanism*, not the result.** The reader should want the
   apparatus before it appears.
4. **Numbers arrive as answers to questions the prose has raised.** A table is
   a resolution, never an inventory.
5. **Every chapter has its own antagonist** — the thing that fooled the author
   in that chapter. Ch. 09's is the decorative drift; ch. 10's is an easy eval
   subset; ch. 21's is a status line quoted without its condition.
6. **Close on the falsifier.** "What would kill this" is both the paper's
   rigour and the natural end of a story about trying to break your own work.

## The voice — four influences, already load-bearing

The older drafts carry editorial material the LaTeX papers stripped out, and
the most useful of it is an explicit **"Acknowledgements — to the
science-fiction lineage"** section (`graphs_paper_3_trajectory.md`), which
closes: *"They got there first. This paper is mostly the bookkeeping."* The
book should carry a version of that, and should stop treating the influences as
decoration — **they are already in the naming, doing structural work**:

- **Asimov** — *Seldon* manifolds. Psychohistory is the system-scope /
  individual-scope distinction, and the papers already formalise it: population
  trajectory has predictive force, individual outcomes stay underdetermined,
  and *the discriminating reader must hold both*. The Three Laws are the first
  popular statement of an admissibility grammar, and forty years of stories
  about their failure modes is a catalogue of underspecified Γ. Even Axiom 0's
  numbering is an Asimov joke (plus the zeroth law of thermodynamics) —
  a principle recognised late *because* it was presupposed.
- **Pratchett** — *narrativium*, taken directly and used seriously. Discworld
  is graph-native ontology with the seriousness disguised as comedy, and the
  paper's own acknowledgement names what the book should inherit: **rigorous
  thinking is more effective when it stays warm**, and anger at cruelty is not
  separate from doing the work properly. That last clause is the licence for
  ch. 12's register — clinical without being cold. *GNU Terry Pratchett.*
- **Carroll** — *Jabberwock*, the agent's own name. A logician writing
  nonsense is the exact posture of a book about admissibility: formal play at
  the edges of a grammar is how you find out what the grammar actually admits.
  Alice is frame-relativity fiction — the rules change between rooms and the
  child holds each room to its own consequences.
- **Sagan** — the register the book needs and the discipline it runs on, from
  one person: explain the hard thing without diluting it, and let wonder be
  *earned by rigour* rather than asserted. The baloney-detection ethic is ch.
  16 in a different vocabulary; the awe in Part I is Sagan's kind — awe at what
  the measurement actually says.

**One name the author left off his own list and the record puts back:
Heinlein.** `CLAUDE.md` opens on the competent-man passage and makes it the
project's stated measure of success, and the trilogy's acknowledgements credit
him for the cross-domain disposition — *learn what is needed when it is
needed*. Ch. 9's "one sensorimotor core, six bodies" is that criterion
measured. It belongs in the book's acknowledgements alongside the four.

**Two rules for using them.** Cite them where they did structural work
(Seldon, narrativium, Jabberwock, the competent man) and nowhere else — an
epigraph per chapter would cheapen all four. And keep the closing line's
posture: *they got there first; this is mostly the bookkeeping.* A book making
large claims is far better served by that sentence than by a defence.

## The author, stated once: a systems administrator

The introduction says the trade plainly — **systems administrator, not
researcher** — and then never returns to it. Not as modesty, and not as a
disclaimer against criticism, but because **the trade is the method's origin
and saying so is the strongest version of the fact.**

A sysadmin's core competence is exactly the question this book runs on: *what
are the unnamed assumptions here?* Debugging a production system is
assumption-elimination against a system that is lying to you — the monitoring
is green, the config is "obviously" right, the change was "unrelated." The
habits that produces are the ones the method chapter formalises: distrust the
reported state; **positive-control the instrument before believing the
reading**; a green dashboard is not evidence the service is up. The sixteen
inert instruments of ch. 1 were caught by that reflex, not by a test suite —
and the popular draft's own line is the right register for it, because it is
literal rather than self-deprecating: *"a digital plumber. That's not a
metaphor — it's his actual trade."*

On whether the title of researcher is now claimable: **let the record do it and
do not argue the point anywhere in the book.** Nineteen chapters of
pre-registered predictions, powered gates, kept retractions and reported nulls
either establish it or they don't, and a book that argues for its author's
standing invites the reader to weigh the standing instead of the evidence. One
sentence in the introduction, past tense, no hedging. Nothing after that.

## The papers do not disappear

Keep both tracks. The formal papers remain the citable artefacts — preprints,
with theorem environments, proofs and full protocol intact — and each chapter
carries a single pointer: *the formal statement is Paper N §M.* **Formality is
not lost, it is relocated**, which is what makes it safe to drop from the prose.
It also means a chapter can be drafted from an existing paper by subtraction
rather than rewritten from nothing.

## Register guards for the chapters that need them

These are not stylistic preferences — in these four places the wrong register
does real damage, and in every case the correct register **already exists in
the source documents** and should be carried across verbatim rather than
reinvented.

| chapter | guard | where the register is already set |
|---|---|---|
| **11 — When grounding fails** | mechanism and plausibility, **never** a validated clinical claim; the authored ingredient is named, not hidden; no claim that the live agent "went psychotic" | `PSYCHOSIS_DEMO_RESULTS.md` verdict section |
| **12 — Coercive control** | clinical, anti-sensational; **mechanism, not moral labels**; grounded in the author's own experience, stated once and not performed; the four-point ethics protocol quoted in full | `ABUSIVE_RELATIONSHIPS_LINE_SUMMARY.md` and the five scoping docs |
| **10 — Emotion** | the affect science is canonical and credited as such; the contribution is the mechanistic instantiation, not the discovery | `docs/features/psychology-affect.md`, `EMOTION_FRAMEWORK_LITERATURE.md` |
| **epilogue — the writer** | testimony, **not evidence**; n=1, uncontrolled, explicitly not offered as support for any preceding chapter; cost stated, never performed, never used as a credential | ch. 12's locked register, applied to the author |

## Non-negotiables

- **Retractions live in the body**, never an appendix. They are the narrative
  engine.
- **Every number gets a sentence** saying what it does *and does not*
  establish. A mechanism proven synthetically is not a benchmark result.
- **Every chapter closes on its falsifier** — what would kill this claim.
- **Nulls are reported as findings**, at the same weight as passes.
- **The author's standing is never argued.** Trade stated once in the
  introduction, past tense, no hedging; the record does the rest.
- **Length is never solved** by cutting retractions, intervals, or ch. 12's
  ethics protocol. Trim mechanism before evidence; trim inventory before
  argument.
