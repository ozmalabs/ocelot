# Review of the Statement (`01s.spec` → `01s_graphic_equalisation_statement.tex`, from long r276) — proposal for fixes

Scope: the spec (169 lines, the only hand-written part), the generated
`.tex` (620 lines, 14 pp), `tools/build_statement.py`, and the long paper
at r276 for what is and is not pulled. Nothing applied. The generated file
is never edited directly; every fix below is to the spec, the generator, or
the long paper.

Compile: 0 undefined, 0 overfull. The generator's contract (pulled blocks
cannot drift; connecting prose can) holds. The findings are about *what*
is pulled, one generator bug, and one promise the section makes that the
reader cannot check.

---

## A. The statement does not state the theory's headline results

The box says "This is the theory". 01's own conclusion names six results
as the theory: the grammar is the loop; world forcing is not self-action;
residual is discrepancy not diagnosis; history matters only where it
survives as present structure; identity exists only under individuation;
and the single prohibition. The statement carries **none of the six as a
numbered result**, and also omits:

| result in 01 | label | status in 01s |
|---|---|---|
| The Law of Graphic Equalisation itself | `hyp:the-law` | paraphrased in spec prose ("The Law is that…") |
| Axiom −1 | `ax:no-view` | never pulled; referenced **5×** as "(Relativity of grounding, long form)" |
| No substrate time dimension | `ax:no-time` | paraphrased ("Time is not a substrate dimension") |
| No frame-free identity | `thm:no-frame-free` | absent; "identity" is in the long paper's subtitle |
| SELF / SUPERGRAPH identity | `def:self-identity`, `def:supergraph-identity` | absent |
| Residual is what a containing grammar does not admit | `prop:residual-inadmissible` | absent; `prop:two-gates` (pulled) points at it as long form |
| Growth is grammar extension | `cor:mint-is-grammar` | absent |
| Self-change is subset-change | `prop:no-direct-self-alter` | absent; its falsifier is also not pulled |
| Graph-law determinism | `prop:determinism` | absent; **its falsifier is pulled** |
| Antecedent-state principle | `prop:antecedent-state` | absent; **its falsifier is pulled** |
| Minimal / discrete sufficiency | `hyp:minimal-graph`, `hyp:discrete` | absent; **both falsifiers pulled** |
| History matters only as present structure | `cor:history` | absent |
| Partial order suffices | `prop:partial-order` | absent |
| Writeability is contingent | `rem:writeability` | absent; referenced 2× and load-bearing for the `[detail]` mark on "Cost is the write" |

Meanwhile the statement spends ~170 lines on five pulled *remarks*
(`rem:evaluation-writes`, `rem:handler-abuse`, `rem:vacated`,
`rem:supply-not-containment`, `rem:failure-instrument`) that are argument,
with Spectre, Chesterton and Paine in them — against the box's "It argues
for none of them" and "What is missing here is not detail but argument".

**Fix, spec side (no 01 change):** add
`@pull hyp:the-law` after the "The Law is that…" sentence (keep the
sentence as lead-in); `@pull ax:no-view` at the head of Frames;
`@pull ax:no-time` at the head of Time; `@pull thm:no-frame-free`,
`@pull def:self-identity`, `@pull def:supergraph-identity` in a short new
section "Identity"; `@pull prop:residual-inadmissible` and
`@pull cor:mint-is-grammar` after `def:residual`; `@pull prop:antecedent-state`,
`@pull prop:determinism`, `@pull hyp:minimal-graph`, `@pull hyp:discrete`
(all short) where their falsifiers need them; `@pull rem:writeability`
after `prop:economics`; `@pull cor:history` in Time. That is fourteen
pulls, all under ten lines each except `rem:writeability`, and it removes
eleven of the 32 fallbacks at once (five are Axiom −1 alone).

**Fix, 01 side (needed for the remarks):** the five argument-remarks each
carry a claim the falsifier list already names as a commitment. Extract
each claim into a numbered result in 01 and pull that instead:
- `prop:handler-relocates` — a handler coheres a failure to a value; the
  audit relocates rather than closes (from `rem:handler-abuse`).
- `prop:vacated-three-states` — absent / vacated-dangling / vacated-
  represented; dependents live in the referring frames (from `rem:vacated`).
- `prop:termination-supply` — termination propagates along supply, not
  containment; three kinds of dependent (from `rem:supply-not-containment`).
- `prop:boundary-by-crossing` — a frame that never fails discloses nothing;
  handlers reduce what failure teaches (from `rem:failure-instrument`).
- `prop:evaluation-writes` — a read returns structure, so evaluation is a
  write, free because information-preserving (from `rem:evaluation-writes`).
Same pattern the 01 review's C.2–C.4 applied to decoherence, capability and
hazard. The remarks stay in 01 as the argument; the statement pulls the
propositions.

**Fix, 01 side (the prohibition):** the spec's "Primitives, and the single
prohibition" section states the prohibition in *unsynchronised prose*
because 01 has no numbered result for it — `sec:prohibition` is all prose
plus a starred subsection. Add `\begin{proposition}[The single
prohibition]\label{prop:prohibition}` in 01 with the three clauses (not
self-transparent at the running level; throughput not measurable in
independent units; no view from nowhere) and the two named exclusions, and
pull it. The formal-analogue paragraph can then be one pulled remark or
stay as spec prose.

---

## B. Falsifiers are pulled for results the statement does not carry

The spec's own sentence: "Below are the commitments **attached to the
material this statement carries**." Nine of the twenty pulled commitments
are attached to material that is *not* carried, and each says so by
rendering its target as "(…, long form)": Minimal graph sufficiency,
Discrete sufficiency, Antecedent-state principle, Graph-law determinism,
Residual is inadmissibility, Realisation is single-valued, No-copy,
Provenance is never closed by inference, The relativity of grounding.

A.'s pulls fix seven of these. **Realisation is single-valued** and
**No-copy** are the ledger's two postulates; with `tab:ledger` now pulled
they are carried, and the No-copy entry's "(The frame interface and its
economics, long form)" is a section pointer, acceptable. **Provenance** is
carried once `prop:prohibition` exists.

Conversely, eleven of 01's commitments are not pulled: A hazard is a signed
capability change; Capability and accessibility are distinct; Description
length is constitutive; Externalising lengthens the interval; Frame-relative
identity; Globally-async/locally-sync; Minting is a rule; No free lunch; No
implicit historical state; Partial-order sufficiency; Self-change is
subset-change. After A., **Frame-relative identity**, **Minting is a rule**,
**Self-change is subset-change**, **Capability and accessibility**, **A
hazard is…** and **No implicit historical state** all attach to carried
material and should be pulled. That leaves five genuinely not carried, which
is the honest residual.

---

## C. The promise the reader cannot check

Spec l.129–132: "the generator reports the difference on every build so the
omission stays visible rather than becoming a claim." The generator reports
it to *the builder's terminal*. The reader of the PDF sees nothing.

**Fix (generator):** emit the omitted commitments' titles into the document
automatically — after the enumerate, `\noindent\emph{Not carried in this
statement:}` followed by the titles of every long-paper commitment the spec
did not `@falsifier`, generated so it cannot drift. Then the sentence is
true of the artefact and not only of the build log.

---

## D. Generator bug: natbib labels with a trailing author list render raw

`_label()` in `build_statement.py` matches `^(.*?)\((\d{4}[a-z]?)\)$`. 01's
bibitems carry the full natbib form `[Osvik et~al.(2006)Osvik, Shamir, and
Tromer]`, which does not end in `)`, so the regex fails and the whole label
is emitted verbatim. Result in the PDF (l.258, 282, 436):

```
(Osvik et~al.(2006)Osvik, Shamir, and Tromer; Kocher et~al.(2019)Kocher, Horn, Fogh, …, and Yarom)
(Basiri et~al.(2016)Basiri, Behnam, de~Rooij, Hochstein, Kosewski, Reynolds, and Rosenthal)
```

Chesterton/Paine/Capecchi render correctly because their labels have no
trailing list. **Fix:** drop the `$` anchor — `^(.*?)\((\d{4}[a-z]?)\)` —
and use groups 1 and 2. One character. Then regenerate; the 01a review's
`et~al.` normalisation made this worse, not better, by adding author lists
to nine more entries.

---

## E. Section-title fallbacks should carry the number

Three fallbacks point at *sections* ("Scope and epistemic status, long
form" ×3, and five others). A title is findable; a number is faster.
**Fix (generator):** the long paper's `.aux` has every section's number;
render section fallbacks as "(long paper §1, *Scope and epistemic status*)".
Same for theorem-like fallbacks: "(long paper Proposition 12.4, *Graph-law
determinism*)". Read the number from `\newlabel{…}{{N}{page}…}` in
`01_….aux`; if the aux is absent, fall back to the current form.

---

## F. Spec prose that has drifted or overstates

1. **Economics lead-in** (spec l.71–72): "Cost attaches to writes rather
   than to holding" — stated flat, while 01 r276 marks "Cost is the write"
   `[detail]` and `rem:writeability` calls the distribution a pattern.
   → "Cost characteristically attaches to writes…".
2. **Time lead-in** (l.108–109): "which is why a frame that runs no rules
   has none" — 01's `prop:cycle-unit` says the unit is a *cycle* and
   requires closure; a frame can run rules without closing a loop and
   still have no time. → "…from its own closure cycles, so a frame with no
   closed loop has none."
3. **Prohibition paragraph** (l.132–139): drifts already — it says "cannot
   measure its own throughput in units independent of it", which 01
   `sec:prohibition` states with the "number obtainable and its absolute
   scale not" qualifier the spec then adds by hand. Resolved by A.'s
   `prop:prohibition`.
4. **Carvings lead-in** (l.142–146): "the cuts that look like joints are
   the cheap ones rather than the real ones" — 01 says convergence is a
   tendency and does not say joints *are* cheap cuts. → "…and what looks
   like a joint is where the cheap cuts of frames doing shared work
   coincide."
5. **Box** (l.15–24): "Every definition and proposition below is pulled" —
   true; but after A. the box should also say the statement carries the
   long paper's numbered results *and its falsifiers for them*, and that
   the remaining commitments are listed by title (C.).
6. **Companion names.** Pulled text says "the companion paper on mind",
   "the physics companion", "the Narrativium measured for the frame",
   "*Is*". The statement names only the long paper. One sentence in the box
   naming the four, using 01's table names.
7. l.122 "the cosmology companion's result" — inherited from 01; being
   fixed in 01 (→ mind companion) by the running agent; regenerate after.

---

## G. Mechanical

- `\input{01.counts}` in the preamble is carried from 01's preamble and
  unused in the statement. Harmless; the generator could strip it.
- The `thebibliography` header note ("The works named above, listed from
  the long paper so the two cannot disagree") is an `\item[]` inside the
  environment — renders fine, but put it as a `\noindent\small` line before
  `\begin{thebibliography}` so it is not a bibliography entry.
- The spec's `\date` has `\textemdash`/`\textbullet` without
  `\texorpdfstring` (hyperref is loaded; no warning yet because the title
  has no math, but keep it uniform with the set).
- Regeneration comment at the spec foot says `python3
  ../../tools/build_statement.py 01s.spec` from `papers/formal/`; the
  generated file header says `tools/build_statement.py formal/01s.spec`.
  Neither matches the form used in this session
  (`python3 tools/build_statement.py papers/formal/01s.spec` from the repo
  root). Pick one and state it in both places.

---

## What is right and should not be touched

- The generate-don't-copy contract, the MISSING exit, and the
  unpulled-block report are the correct design and are why the
  cross-document numbering fixes propagated for free.
- The ledger as a pulled table with live `IS-` refs.
- The box's distinction between a statement and an abridgement.

---

## Suggested order

1. **D** — one-character generator fix; regenerate. (Visible in every
   citation.)
2. **A, spec side** — fourteen pulls; regenerate; count fallbacks again
   (expect ~32 → ~15).
3. **A, 01 side** — six extractions in 01 (five claim-propositions + the
   prohibition), bump 01, pull them, drop the five remark pulls.
4. **B** — add the six attachable falsifiers.
5. **C** and **E** — generator: omitted-commitments list; numbered
   fallbacks.
6. **F**, **G**.
