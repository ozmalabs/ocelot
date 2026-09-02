# Review of `06_assessing_an_account_of_this_kind.tex` (draft-2026-09-02.1, r26) — proposal for fixes

Scope: the whole file (1073 lines, 20 pp), its log, 01 r278 for what it
attributes, and — because this paper quotes the implementation record —
the repository itself, for whether the quoted figures match the record
today. Line numbers are r26. Nothing applied.

Compile: 0 warnings, 0 overfull, four citations, all resolve (Carnap,
Lakatos, Friston, Heinlein — the last correctly moved here from 01). The
argument of `sec:risk` → `sec:implementable` → `sec:question` (a vocabulary
cannot be falsified; a claim with content can; the discriminator is
whether attempting a counterexample has an outcome) is the set's best
statement of its own epistemic position and is not questioned. The
findings are: the construction paper cited for the implementability
claim; record figures that have drifted, one of which does not add up;
a stated policy of leaving corrections visible that the rest of the set
has since abandoned; and cross-reference hygiene.

---

## A. The construction paper carries the implementability claim

l.107–108: "This framework is *implementable, forwards*, and has been
implemented (**the constructive companion**)." l.385–386: "the
constructive companion is a normative specification containing none of
[the measurements]." A1 is outside the releasable set. The
implementability claim is the hinge of `sec:implementable` ("supplies the
surface on which it can fail") and it currently rests on a document the
reader cannot obtain.

**Fix.** Rest it on what the reader *can* weigh, in 01 r278's standard
form: "has been implemented, and the implementation is the programme's own
pre-registered record, not circulated with these papers — a claim a reader
may decline to credit on the terms Graphic Equalisation states". Drop both
references to the constructive companion; the sentence at l.385 becomes
"…and no circulated paper contains them."

---

## B. The record figures: what matches, what has drifted, what does not add up

The paper quotes the engineering record throughout `sec:implementation`,
`sec:substrate-size`, `sec:record-wrong` and `sec:estimate`, marks every
figure as an assertion, and says (l.531) the baseline "is now some weeks
old". Checked against the repository on 2 September 2026:

| claim | paper | repository today | status |
|---|---|---|---|
| Rust core files | 89 | 89 | matches |
| seed manifests | 805 | 805 | matches |
| term-language variants | 239 | ~234 (rough count of the enum) | close; verify |
| results tracked / on disk | 17 of 1,216 | 17 of 1,216 | matches exactly |
| failure baseline red node ids | 216 | 216 (`total`, `entries`) | matches; measured 2026-08-13 |
| files swept | 1,092 | `files_green` 912 + `files_red` 133 = 1,045 | **does not add up** — verify what 1,092 counts |
| pre-registration stems with no results | 84 | 93 | **drifted** |
| commits / documents | ~4,000 / ~1,900 over five months | this repository: 1,270 since import on 2026-08-10; 1,566 docs | the larger figure is the other repository; say so |
| composition +21, verdict +51.5 [67.0, 79.1] vs [22.6, 31.3] | as stated | matches the programme's own record | fine |

Two consequences.

1. **The paper is doing the thing its own `sec:record-wrong` warns
   against**: quoting counts ("the enumerated failure baseline — a list of
   node identifiers rather than a count, for reasons this programme had to
   learn — stands at 216") as if a count could be held. It cannot; one of
   the four checkable counts has moved in three weeks and one does not
   reconcile with its source. **Fix:** date every figure to the baseline's
   `measured_at` (2026-08-13) and the commit it was read at, or state them
   as "at the baseline's measurement date" once in `sec:implementation`
   and drop the repetition; fix 1,092 or explain it (skips + errors?);
   update 84 → the current count with its date, or replace with "some
   dozens".
2. **"Some weeks old" will keep being truer.** Either regenerate the
   figures at each revision from the record (the same fix 01 took for its
   own counts: a generated `06.counts.tex`), or state them once with a
   date and never update them, as a snapshot. The first is the set's
   established answer.

Also: l.638 "four thousand commits and nineteen hundred documents over five
months … the sweep covered the smaller of the two repositories" — this
repository's history begins at a squashed import on 2026-08-10. A reader
given only what is circulated cannot reconstruct either number. Say the
record spans two repositories and neither is circulated.

---

## C. "Corrections are left in the text rather than smoothed out of it" — a policy the set has abandoned

l.277–279: "the account is written to make [revisions] cheap — which is
why the falsifiability commitments are stated separately from the
constructions, and **why corrections are left in the text rather than
smoothed out of it**."

That was the set's practice until 7309f2b9 ("A paper is what it says now
— twelve sites where the set narrated its own drafting") and the passes
since, which removed narrated corrections from 00, 01, 01a–c, 02, 02a–b,
03, 04, 05. The sentence is now false of every other paper, and 06 is the
one paper still written to it. At least fourteen sites:

| line | phrase |
|---|---|
| 186–191 | "Six review passes over this corpus, each running some twenty-odd lenses, did not find…" |
| 220–222 | "This material was carried in the substrate paper's scope section … reproduced here unchanged in substance" |
| 444 | "The qualification given earlier was too generous and must be replaced by the measurement" |
| 564–566 | "the stronger phrasing available here … fails twice over" |
| 589–594 | "the paper having already ruled the assumption out. It read the upward weight as *functional* … That is not what happened here" |
| 618–630 | "a distinction this paper had been running together … That reading is more favourable than the one this paragraph first gave, and it should be corrected to it" |
| 636–643 | "though that statement needs its own correction first, because the audit producing it searched about a quarter of the available record" |
| 696–697 | "with a qualification the first version of this passage omitted" |
| 797 | "and corrects Section~\ref{sec:risk}'s opening in the process" |
| 948 | "The trajectory claim has since been quantified" |
| 986 | "was caught three times in this corpus within a day" |
| 1000–1005 | "got it wrong in one cluster … all in economics material written in a single day" |
| 1008–1010 | "this one carried no commitments at all while naming a claim as the one worth testing … so the list is owed here" |
| 1041–1047 | "The list of prohibitions above once carried *cost attaching to the write* as a fifth member and no longer does" |

Two of these are content rather than narration and should stay in
substance: the review-selects-for-true-imports argument (l.193–217) is a
real result about method — keep it, but state it as a property of review
("a procedure that examines what a text asserts cannot examine what it
lets a reader assume") without the "six passes, twenty lenses, did not
find" preamble; and the modal-clothing check (`sec:modal`) is a real
discipline — keep the check, drop "caught three times within a day" and
the single-day cluster.

**Fix.** Decide the policy explicitly, then apply it. The recommendation
is the set's: state each result positively, keep the revision record in
the review record. If instead 06 is to be the one paper that keeps its
corrections visible (defensible for an assessment paper), l.277–279 must
say "in this paper" rather than "the account", and the abstract should
say so.

The one place narration is load-bearing and should be kept in a different
form: `sec:contribution` l.291–301, the shape-correction *rate* ("roughly
one shape correction to three detail corrections, on that day … the
beginning of a series"). That is a measurement the paper promises to
continue. Either continue it (add the later days, from the commit log) or
say the series was not continued.

---

## D. Cross-references and naming

1. "the substrate paper" ×31, "the companion" ×6, "the physics companion"
   ×2, "the companion on mind" ×1, "the constructive companion" ×2, "Graphic
   Equalisation" ×1. Draft box generic. Add the naming sentence (Graphic
   Equalisation; the physics companion; the mind companion; *Narrativium*)
   with the "inherits…" clause; collapse "the substrate paper" and "the
   companion" to "Graphic Equalisation".
2. `xr-hyper` to 01 (`[GE-]`), 01b (`[MS-]`), 01a (`[PH-]`). Targets, all
   present: `GE-def:well-formed` (l.69, 81, 159, 552, 748),
   `GE-ax:no-view` (l.585, 904), `GE-prop:convergence-observed` +
   `GE-hyp:cheap-cut` (l.147, 890), `GE-prop:compression-convergence`
   (l.253, 336, 371), `GE-hyp:located-degradation` (l.269),
   `GE-prop:boundary-by-crossing` (l.123), `GE-rem:only-g` (l.333),
   `GE-rem:why-minus-one` (l.193), `GE-rem:types-forced` (l.202–204),
   `GE-rem:one-substance` (l.188–190, 208–209), `GE-prop:prohibition`
   (l.1042), `GE-rem:writeability` (l.877, 1047), 01's falsifiability
   section (l.250, 270, 283, 287, 364), `MS-rem:realisation` (l.838–853,
   the "am I the one in the wrong" case), `PH-` for the "impossible was the
   wrong word twice over" line (l.1002 → `PH-rem:oneway-rule` or the
   one-move remark; verify which carries that sentence now).
3. l.356: `\citeauthor{heinlein1973}` fine; the "competent man" standard is
   also the repository's stated purpose (CLAUDE.md) — no change needed,
   noted for the record.

---

## E. Structure

1. `sec:implementation` uses numbered `\subsection` (`sec:substrate-size`,
   `sec:record-wrong`) while `sec:contribution` uses `\subsection*`.
   Harmonise (numbered; they are referenced).
2. `sec:objection` runs from the triviality objection (l.860–919) into
   material that belongs to `sec:estimate` — "Per-choice quality is
   assessable; ordering optimality is not" (l.921), "Two further gaps"
   (l.927), "What survives unchanged is the argument above it, which never
   depended on the motivation" (l.933), the trajectory quantification
   (l.948–972) and "Three debts" (l.975). None of that is about the
   triviality objection. Move l.921–983 to the end of `sec:estimate`, where
   the motivation argument and the audit they refer to live.
3. `sec:own-commitments` item 1 is thirty lines inside an `\item`. Split:
   the commitment (three sentences), then the operationalisation debt and
   the confounds as a paragraph after the list.
4. The paper has no numbered results at all. Two claims the rest of the set
   leans on should be numbered so they can be cited: **the discriminator**
   (`sec:question` l.822–824: a framework is a theory rather than a
   vocabulary iff attempting a counterexample has an outcome) and
   **scope and kind of residual as the grading of a choice**
   (`sec:scale` l.714–718). `\begin{proposition}` for each.

---

## F. Mechanical

- `\texorpdfstring` on the `\date` dashes; `\S\ref{sec:question}` (l.182)
  → `Section~\ref`; unused macros `\Poss`, `\Coll`, `\Hist` and five unused
  theorem environments (only `enumerate` and prose are used).
- l.209 "there is one graph-data stuff in the obvious sense" — reads as a
  typo; "there is one *kind of* stuff, graph data, in the obvious sense".
- l.564 one 60-word sentence with two nested clauses; split at "fails
  twice over".
- l.974 `\medskip` before "Three debts" inside a section with no heading —
  after E.2 this lands in `sec:estimate`; give it a `\paragraph{Three
  debts.}`.

---

## What is right and should not be touched

- `sec:risk`'s narrowing of "unfalsifiable-by-construction" to the pure
  framework part, with well-formedness as what separates a framework
  from a vocabulary, and usefulness offered as a *record* never a
  threshold.
- `sec:implementable`: implementability as a warrant different in kind
  from coherence; "one discovers that a framework is underspecified only by
  attempting to build it".
- `sec:record-wrong` entire: "a reader given the first subsection and not
  the second would have been given a brochure."
- `sec:estimate`'s "the width is the finding", the no-apology rule with the
  exposure as its admissible form, and the upper bound as "a claim about
  other frames, not about this work".
- `sec:scale`: errors are residual; large partial residual localises,
  complete residual eliminates, no residual is the uninformative case; and
  the review-grading corollary.
- `sec:question` and `sec:objection`: the discriminator, the god paragraph,
  "Newton was not wrong", and the hazard that relaxing a prohibition moves
  the account toward the trivial reading.

---

## Suggested order

1. **A** — two sentences; removes the only non-releasable dependency.
2. **B** — date the figures and fix the one that does not reconcile;
   decide snapshot vs generated.
3. **C** — decide the policy; if the set's, apply it to fourteen sites.
4. **D** — names and `xr-hyper`.
5. **E**, **F**.
