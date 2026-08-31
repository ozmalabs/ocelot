# Plan: remaining changes from the external review

Written 2026-08-31, against **Is r98** and **Theory r244**. Every number here is
measured, not estimated; where the review's own estimate does not survive
measurement, that is stated rather than quietly adjusted.

---

## 1. Measured baseline

| | Is | Theory |
|---|---|---|
| body words | 9,653 | 41,539 |
| pages | 16 | 69 |
| sections | 11 | 27 |

**Theory's mass is concentrated.** Six sections carry 58% of it:

| words | section |
|---|---|
| 5,440 | The frame interface and its economics |
| 4,013 | Decoherence |
| 4,001 | Axiom −1: relativity of grounding |
| 3,997 | The minimal graph |
| 3,367 | Falsifiability commitments |
| 3,351 | Scope and epistemic status |

**And its tail is vestigial.** Eight sections are ≤200 words — including
*The Law of Graphic Equalisation* at **60 words**, which is the paper's title
result holding its own top-level section.

**Is** is more evenly spread; top three (How the claim is reached 1,806 / Prior
positions 1,475 / Falsifiability 1,208) are 46%.

---

## 2. The review's page target does not survive arithmetic

The review proposes **69 → 35–40pp** and itemises the savings: §1 −8, revision
history −7, Remark 2.6 −2, §12 −3, §14 −3, §15 −2, §23 −1, §26 −2, duplicated
arguments −3. Total −31pp.

**The history line is the problem.** It is done, and it yielded **84 words —
about 0.2 pages, not 7.** The 16 sites were *clauses*, not passages: "an earlier
version of this remark claimed closure" is nine words, and removing it saves
nine words. The estimate assumed bulk that was not there, and it was the
largest single item in the list.

Correcting that line alone takes the achievable total to ~24pp, i.e. **69 → ~45**,
and only if every other estimate holds — none of which have been measured the way
this one now has. **Treat 45pp as the honest ceiling and re-measure after each
item rather than budgeting against the total.**

This does not weaken the review. Its *diagnosis* verified precisely (`which is`
142 exact, `exactly` 43 exact, 27 sections exact). Its *sizing* is where it is
weakest, which is the ordinary asymmetry: counting occurrences is reliable,
estimating what they weigh is not.

---

## 3. Work items, in execution order

Ordered by **risk of losing content**, cheapest and safest first. Each states
what verifies it.

### Tier A — mechanical, no claim touched — **DONE 2026-08-31**

| # | item | measured | verify |
|---|---|---|---|
| A1 | Sort both reference lists; add Yamey 1949 page numbers | 2 files | `bibitem` order; compile clean |
| A2 | Nāgārjuna glyph — source is `N\=ag\=arjuna`, correct LaTeX; the review saw a *font* failure | 3 sites | render at 300dpi, inspect |
| A3 | Enumerative openers that promise a count: `Two things` ×13, `Two things follow` ×6, `Two consequences` ×5, `Two further` ×4, `Three things` ×3, `Two cautions` ×2 = **33** | 33 sites | grep to zero where the count is not load-bearing; check each delivers the number promised |
| A4 | `worth stating/marking/having/noting` ~20 | 20 sites | grep |

### Tier B — additive, nothing removed (est. 1 session)

| # | item | notes |
|---|---|---|
| B1 | **Companion map**: half-page box in Theory §1 — title, short name, one-line scope, for all nine companions (80 mentions currently, no map) | pure addition; then enforce short names |
| B2 | **Ledger as a table** — entry / status / where argued / what it replaced, prose beneath | the ledger is ~1,700 words inside the 4,001-word Axiom −1 section |
| B3 | Group Theory's 27 sections into parts (Foundations / Dynamics / Economics / Failure / Time / Provenance / Carvings / Positioning) | no text moves; `\part` only |

### Tier C — relocation (est. 2 sessions, needs care)

| # | item | risk |
|---|---|---|
| C1 | Demote the 8 sections ≤200w into their neighbours as propositions — **except** *The Law of Graphic Equalisation* (60w), which is the title result and should get *more*, not less | low; breaks `\ref` targets — sweep all cross-paper refs |
| C2 | Capability/accessibility from Remark 12.5 → §15, where *capability* is defined | medium: §12 currently defines the distinction before the reader meets either term |
| C3 | Theory §1's "what kind of thing" + "what kind of document" → 07 | **flagged**: 07 is 15pp; adding 8pp makes it 23pp. This relocates the problem unless those sub-essays are cut *while* moving. Do C3 only with a cut target attached. |

### Tier D — rewriting, conclusions-first (est. 2–3 sessions)

Highest risk of losing content; each needs the result stated in the first
paragraph and the search compressed behind it.

- **§15** — state up front: *an information hazard is a capability change whose
  negative sign is admissible in the reference frame, above a frame-relative
  threshold.* Then support. (Currently: hazard → "the neutral class has no
  name" → literature search → the term.)
- **Remark 14.1** — currently a chapter (2+2=5, IEEE 754, Manhattan Project,
  Bochvar/Halldén/Ryle/da Costa, Milner/Scott–Strachey). Keep two examples;
  IEEE to two sentences; prior art to §25.
- **Remark 23.3** — keep appendix + genome-bloat; the dead-code paragraph
  restates `def:well-formed`'s fourth cost.
- **Remark 2.6, 12.6** — 12.6 states the "free simpliciter is set by the
  superframes" point twice in near-identical words.
- **Is §3** (461w) → one paragraph, or fold into §5's MDL discussion.
- **Is §6** (1,143w) → half. Keep Farolfi, Pacioli, Ellerman's group-of-
  differences, one sentence of Yamey/Sangster.
- **Is §10** → two pages; the Pacioli→Hamilton→De Morgan→Cayley dating is told
  twice (§6 and §10).

### Tier E — falsifier list, last (est. 1 session)

**Do this last, and check the dependency first.** `01s.spec` pulls **20
falsifiers by exact name**; Theory has **30 items**. Renaming or renumbering
breaks the generator — which now hard-fails rather than silently emitting past
`\end{document}`, so the failure will be loud, but the spec must be updated in
the same commit.

- Strip argument and history from entries; target *fails if X* in one or two
  sentences. Justification moves to the remark each entry cites.
- Nest the risk the paper itself says is "counted four times" (entries 19, 21,
  27 second clause, 30) under one entry with four places to look.
- Entries 8 and 11 are named as consequences rather than wagers — list them as
  derivations in the body, not as falsifiers.
- Result: **30 → ~20**, each readable at a glance.

---

## 4. Items I would not do as specified

- **"Align Is with Theory on falsifiability."** Already resolved differently and
  better: neither bare verdict is available, both import a frame in which the
  counterexample would be coherent, and the distinction sits below the aperture
  at which falsifiability is normally argued. The papers do not disagree; either
  sentence read alone looks as though they do. Both now say so.
- **Axiom −1 rename.** The review suggests the name invites the confusion the
  four passages fight. It does — but the number *records* something: not an
  axiom, and stated first anyway, because the import is free. Renaming discards
  the finding. Say it once (in 2.1) and cut the other three.
- **"Axiom −1 hyphen/minus inconsistency."** Measured: 17 minus, **0 hyphen**.
  Nothing to fix.
- **Blanket em-dash reduction** (496 in Theory, 106 in Is). Most are appositive
  definitions doing real work. Sweeping them on an audited text is how claims
  get lost. Only worth doing inside Tier D rewrites, paragraph by paragraph.

---

## 5. Standing risk

The defect this session found seven times is **a correction applied at its site
and not swept to what points at it** — and pass seven found it in text written
hours earlier, not years. Every item above is a correction at a site.

**Therefore: after each item, re-read the whole section, not the edit.** §1 of Is
went 951 → 745 → 1,269 words because five separately-correct fixes never re-read
the section. That is the failure mode this plan is most likely to reproduce.


---

## 6. Tier A execution record (2026-08-31)

**A1 — references.** Both lists sorted alphabetically by author then year (Is 16
entries, Theory 83), accent-stripped sort keys so `N\=ag\=arjuna` files under N.
Yamey 1949 given its page range (99–113). Arya pair relabelled (2000a)/(2000b) —
previously (2000)/(2000b), a suffix with nothing to suffix.

**A2 — the Nāgārjuna glyph: investigated, and there is nothing to fix.**
The review reported it rendering as "N¯ag¯arjuna". Checked in three places:
the source is `N\=ag\=arjuna`, which is correct LaTeX; **the rendered page is
correct** (inspected at 200dpi — properly composed macrons); and the extracted
text is `N` + `a` + U+0304, i.e. **NFD rather than NFC**, which Python reads as
`'Nāgārjuna'` and normalises to the precomposed form identically. So the output
is canonically-equivalent Unicode and the reviewer's tool displayed the
decomposed form badly.

Two candidate fixes were tried and **both reverted**: `cmap` and
`\input{glyphtounicode}\pdfgentounicode=1` each left the extraction byte-identical.
T1 composes the accent from two glyphs, so decomposed output is inherent to
pdflatex+T1; precomposed extraction needs LuaLaTeX or XeLaTeX with Unicode fonts,
which is an engine change across twelve documents and out of proportion to a
display artefact in one tool. **Adding packages that changed nothing would be
exactly the cost `def:well-formed` prices as idle**, so they came out again.

**A3 — count-promising openers: 33 → 8.** Kept: those delivering with
First/Second, and the two standalone signposts (*Four qualifications*, *Three
things about that statement*) that head genuine multi-paragraph lists. Stripped
the rest, keeping the content and dropping the numeral.

**One real miscount found**, confirming the review's secondary note: *"Two things
this account adds, and one it must obey"* promises three and delivers two.
Corrected to *"This account adds two things and must obey a third."*

**A4 — the announce-then-say tic.** Twelve of the clearest cut: *"This is worth
stating because the obvious gloss is wrong in a specific way"* → *"The obvious
gloss is wrong in a specific way."* Ten remain, where the phrase carries content
(*"is worth running"*, *"is worth answering"*, *"is worth its"*) rather than
announcing.

**Measured cost of Tier A: −120 words in Theory, −1 in Is.** Page counts
unchanged (69 / 16). This is consistent with §2's warning and worth recording as
a second data point: **the style items are real defects and are not where pages
come from.** Pages are in Tiers C and D.

---

## 7. The history sweep was itself unswept (2026-08-31)

The revision-history removal was executed against **Is and Theory only** — the
two papers the review named. Measured afterwards across all twelve: **34 more
sites in nine other papers**, including **eight in 07**, the assessment
companion, which is where the rule about not apologising was being written.

That is the week's defect class at its purest: a correction applied where it was
reported and not swept to what the same rule points at.

Now cleared. Remaining sites: **three, all inside Theory's ledger**, which keeps
its withdrawals under a stated contract ("a ledger whose entries cannot be
checked against what they replaced is not checkable"), plus the four the
statement paper inherits by pulling the ledger.

| paper | sites | words |
|---|---|---|
| 07 | 8 | −67 |
| 01b | 7 | −43 |
| 04 | 4 | −28 |
| 06 | 3 | −22 |
| 01a | 2 | −17 |
| 02 | 2 | −7 |
| 03 | 1 | −2 |
| **total** | **27** | **−186** |

**Third data point for §2.** −186 words, no page count changed anywhere. The
history removal across *all twelve papers* has now cost about 270 words in
total — against the review's estimate of 6–8 pages for Theory alone.

**And the rule it was serving is now stated** (07): an account of this kind
cannot apologise, because an apology instructs a reader how to read from a
standpoint outside the reading, and there is none; it is also idle structure by
`def:well-formed`. The admissible form of the same impulse is an **exposure** —
what would settle the matter against the account — which asks for nothing and
hands over something. Every apology has that translation.

---

## 8. Tier B execution record (2026-08-31)

**B1 — companion map.** Table in Theory §1: title, short name, one-line scope,
for all twelve documents. Measured beforehand: **80 companion mentions with no
consistent naming** — `companion on assessment`, `companion physics`, `companion
paper on mind`, `companion states with its prior art`, all ad hoc. The middle
column is now the only form the paper uses.

*Caught in my own new text*: the introductory sentence said "Eleven documents
make up this programme" while the table listed twelve. Twelve documents, eleven
companions — this paper is one of them. Fixed before commit; the column widths
were also hyphenating "the physics com-panion" and were rebalanced.

**B2 — ledger as a table.** Status / entry / where argued and what it replaced,
five rows, with the prose beneath as the argument for each placement. The header
paragraph shrank from a count-and-caveat to two sentences.

**B3 — seven parts.** Foundations · The substrate · Frames, economics, and
failure · Order and time · Provenance and its limit · Carvings and determinism ·
Positioning, falsifiers, and close. Section numbering runs continuous (1–27
unchanged), so no `\ref` target moved — confirmed by 0 reference warnings.

**Cost: +1 page (69 → 70).** Tier B is additive by design and was never going to
reduce anything; it is on the list because the review's second-most-important
change was navigational, not editorial.

**Running total against §2's warning.** Tiers A and B together: −306 words of
prose, +1 page of tables. **The page count has not moved down once.** Every item
that reduces pages is in Tier C or D, exactly as the corrected arithmetic
predicted.
