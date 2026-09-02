# Review of `08_certified_answers_as_an_audit.tex` (draft-2026-09-02.1, r1) — proposal for fixes

Scope: the whole file (184 lines, 4 pp), its log, and the record it
abridges (`docs/research/HLE_KEY_AUDIT.md`, a running dossier). Line
numbers are r1. Nothing applied.

Compile: 0 warnings, 0 overfull, two citations. No implementation
identifiers. The paper is a faithful abridgement of the dossier, and its
stance (an auditor, not a competitor; zero false accusations is the whole
value; coverage 1.8% is the honest headline; the not-convicted section
matters more) is exactly right. **The four convictions that can be checked
from the page were checked and hold**: the Hurewicz kernel (χ(G) = −47/40,
index 80, rank 1 − χ(K) = 95; the key's ∏(nᵢ − 1) = 28 is the two-factor
formula; the [2,2,2] control gives 5 vs 1); the sudden expansion (⟨E⟩ is
unchanged under a sudden change of the well, so 0%); 6-31G toluene
(9 per C, 2 per H, 7·9 + 8·2 = 79); the Aztec diamond (2^{n(n+1)/2}, so
never 6). The boolean-expression count depends on the grammar and is not
checkable from the page; the paper says so implicitly by giving two
routes. Findings are about standing, one contradiction in the abstract,
and what a reader needs in order to check the fifth conviction and the
keys themselves.

---

## A. What system, and on what standing

The paper never says what "the system" is. A reader of 08 alone learns
that *a* system answers under certificate; not that it is this
programme's substrate, run with general faculties, nor where the record
of the run lives. 01's companion table calls this "the audit paper" and
expects it to be read with the set.

**Fix.** One sentence in `sec:audit` or a new opening paragraph: the
system is the substrate described in Graphic Equalisation, run with its
general faculties (no per-question code); the derivations, certificates
and the dossier are the programme's pre-registered record, not circulated
with these papers (01's standard sentence, adapted) — **with the
difference that here the five diagnoses are stated fully enough to be
re-derived from the page, so a reader can check the convictions without
the record.** That is a stronger position than any other paper in the set
holds and the paper should say so rather than leave it implicit at l.156
("stated with its diagnosis specifically so that this is attemptable").
Add the naming sentence (Graphic Equalisation; the adaptability paper if
the certification faculty is described there — check 09 for
"certificate"/"certified"; if not, name only 01).

---

## B. The reader cannot find the keys

An audit of a public benchmark's keys is checkable only if the reader can
locate the questions. The dossier carries each question's dataset id
(e.g. the Hurewicz item is `66f407a066abc59ffb9a82ae`); the paper omits
them. Those are the benchmark's own public identifiers, not
implementation identifiers, and the public split's keys are published.
**Fix:** give each conviction's dataset id in its paragraph heading, and
say which split (public) the 2,370 text-only questions are.

Also verify the count. HLE's released set is 2,500 questions with a
multimodal fraction; "2,370 text-only" should be checked against the
benchmark's own numbers for the version audited, and the version (date or
revision of the dataset) stated, since keys have been corrected over
time — a conviction against a since-corrected key is a different finding
from one against a standing key.

---

## C. The abstract contradicts itself in one clause

l.39–41: "with **no accusation withdrawn** and **one of its own earlier
flags retracted** after re-derivation found a sign error in the system".
A flag and an accusation are the same thing to a reader. The record's
distinction is pre-banking flag vs banked conviction. **Fix:** "no banked
conviction withdrawn, and one pre-banking flag retracted after
re-derivation located a sign error in the system rather than in the key".

---

## D. The fifth conviction needs its grammar on the page

`sec:convictions`, computer science (l.114–121): "filtering all 7⁵ strings
through a recursive-descent parser, and generating bottom-up from the
grammar — both yield 90 valid expressions of which 47 are true". Unlike
the other four, this cannot be checked without the grammar (the seven
symbols, the production rules, the precedence). The paragraph then argues
that "no consistent grammar excludes what [the key] excludes" and "no
precedence convention yields 44" — claims that depend on exactly the
grammar not shown. **Fix:** state the alphabet and the grammar in a
display (five lines), and the two-false/five-missing enumeration as a
short table, so the conviction meets the standard the other four meet.

---

## E. Falsifiability

1. **No `[shape]`/`[detail]` definition.** Add 01's sentence verbatim.
2. **Item 3 "The diagnoses locate the error" is `[shape]`** and describes
   its own failure as "a distinct and weaker failure" in which "the
   conviction survives and the explanation does not" — that is a mechanism
   failing while the result stands: `[detail]`.
3. **Item 5 "Coverage is not the claim"** is the scope-note shape the set
   has moved out of its lists (01b, 02a, 02b): "a reader who extracts one
   has found an error rather than a result." Move to a
   `\noindent\emph{Scope note (not a falsifier).}` after the list.
4. **Missing, and the paper's real exposure:** the arithmetic of
   `sec:why` predicts that *any* frontier benchmark contains wrong keys.
   `[detail]`: fails if the same certified-answering run on a second
   benchmark of comparable size and review standard convicts nothing.
   That is the claim that makes the paper about a *discipline* rather
   than about one benchmark, and it is the one test not yet run.
5. **Item 4 "Tier-B is not a holding pen"** is good and should stay; add
   the count (six items, named by kind in `sec:tierb`) so a later
   conviction can be matched to it.

---

## F. Bibliography and mechanical

- `phan2025`: "Long Phan et al. Humanity's Last Exam. 2025." — no venue,
  no identifier. It is arXiv:2501.14249 (Center for AI Safety and Scale
  AI, January 2025, ~1,000 authors); give the arXiv id, the first few
  authors with `et~al.`, and the dataset URL, and date the version
  audited (B).
- `elkies1992`: Part I is JAC 1(2):111–132; Part II is 1(3):219–234, and
  the tiling formula is proved across both. Cite both or say "Part I".
- `\texorpdfstring` on the `\date` dashes; `thebibliography{9}` fine for
  two entries, `{99}` if more are added.
- The draft box carries the paper's own scope sentence and the standard
  falsifiability sentence; add the naming clause (A).

---

## What is right and should not be touched

- `sec:why`: "the instrument built to test reasoning is bound by the same
  arithmetic of error rates as everything else, and a benchmark with no
  wrong keys would be the surprising object."
- `rem:zero`: the asymmetry on purpose, and "an auditor that has never
  withdrawn anything has not been audited."
- The Aztec-diamond paragraph: "refuting the key requires only the parity
  of a theorem and no recomputation of the question at all."
- `sec:tierb` entire, especially the K₁ case: "An audit willing to accuse
  here would be worth less everywhere."
- `sec:not`: a benchmark score and a certified audit are different
  measurements, and "certified coverage doubles as audit at no additional
  cost".

---

## Suggested order

1. **A** and **B** — standing and the ids (the reader's route to the
   keys).
2. **D** — the grammar on the page.
3. **C**, **E**, **F**.
