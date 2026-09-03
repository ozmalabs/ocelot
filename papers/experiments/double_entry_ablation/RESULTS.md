# Double-entry accounting ablation — paper 00

## Question

Does paper 00 require its double-entry-accounting material to make the argument
as written, rather than merely to decorate it?

## Design

This was a two-version, two-reviewer, source-level ablation.

- **Manuscript A** was a coherent ablation. It removes the double-entry worked
  case in `sec:track-record`, its later historical/mechanistic reprise in
  `sec:prior`, and the eight bibliography entries used only by those passages.
  The adjacent transition is minimally repaired so the remaining field list is
  explicitly illustration rather than evidence.
- **Manuscript B** is the full paper-00 baseline, copied without substantive
  change. Both copies change only their `xr-hyper` paths so they compile from
  this experiment directory.
- Each manuscript was compiled with three `pdflatex` passes. A is 17 pages and
  B is 19 pages. Final logs have no errors, undefined references/citations,
  warnings, or over/underfull boxes; extracted PDF text has no `??` markers.
- Two independent reviewers received only `manuscript_A.tex` and
  `manuscript_B.tex`, in opposite orders. They were told the names were
  arbitrary and were not told the ablation hypothesis, mapping, provenance, or
  source-paper location. They were prohibited from reading surrounding files,
  history, diffs, PDFs, or prior reviews. Each gave a standalone steelman,
  breakdown, evidence-architecture, compellingness, and release verdict before
  a short post-review comparison.

The reviewer reports are `blinded_reviewer_1.md` and `blinded_reviewer_2.md`.

## Unblinding

| Blinded identifier | Actual version |
|---|---|
| Manuscript A | No-double-entry ablation |
| Manuscript B | Full baseline, including the double-entry case |

The removed material is the worked claim that double-entry bookkeeping is a
compression, its history/formalisation lag, the group-of-differences and
directed-graph characterisations, and the later use of that case to explain how
something simple and widely used can remain unwritten across field boundaries.
This is a **content** ablation, not a sentence-level shortening exercise.

## Blinded results

### Shared steelman: what survives the ablation

Both reviewers found the same conceptual spine in A and B:

1. The paper isolates `distinction is relation` as its sole foundational
   commitment rather than disguising it as a proof.
2. Its removal method is run with a stated asymmetric limit: successful removal
   establishes only that the tried structure was not required; failed removal
   does not establish necessity.
3. The bare untyped graph result, the object-language/metatheory distinction,
   and the explicit epistemic-to-ontic boundary remain intact.
4. The first three commitments and their stated exposure are not supplied by,
   nor made dependent on, the accounting case.

Accordingly, removing the case does **not** break paper 00 as a scoped
conceptual argument for its relational floor. Both reviewers still rated the
central claim's clarity 9/10 in both versions. Both gave both versions a
release verdict of at least “publishable with stated scope limits” for that
narrow core.

### Divergent breakdown: the fourth commitment

The result is unanimous on the fourth commitment: the prediction that
formalisms under compression move toward graph form.

- In **A**, both reviewers noted that `sec:track-record` itself says its field
  list is “illustration rather than evidence” and that none has been checked for
  the relevant *movement*, rather than mere graph drawability. With the worked
  case removed, the paper names a discriminator but supplies no checked,
  datable instance satisfying it. Reviewer 1 calls the commitment “evidentially
  empty”; reviewer 2 says A lacks the concrete evidence its own section title
  and fourth commitment promise.
- In **B**, both reviewers judged the double-entry material to supply the one
  required kind of support: a concrete, dated, formally characterised, and
  candidly limited instance. The case does not establish the general prediction
  or operationalise compression pressure, but it makes the prediction a
  supported and attackable conjecture rather than a bare assertion.

The reviewers also independently identified B's residual weakness: the
explanation “unwritten because no field owned it” is strained by the paper's
own De Morgan/Cayley counterweight. This weakens the *explanation of the lag*;
it does not erase the case's evidential role for the fourth commitment.

### Compellingness

| Measure | A: ablated | B: baseline | Interpretation |
|---|---:|---:|---|
| Central-claim clarity | 9/10 (both reviewers) | 9/10 (both reviewers) | The accounting case is not needed to state or parse the core claim. |
| Argument credibility | 7/10 (both reviewers) | 7–8/10 | The conceptual core is unchanged; B gains credibility for the fourth commitment. |
| Motivation to accept / continue | 5–6/10 | 7/10 | The worked, dated case gives B a concrete payload and reason to credit the empirical exposure. |

## Decision

**The double-entry material is not required for the paper's core conceptual
argument (commitments 1–3), but it is required for paper 00 as currently
framed if the fourth commitment remains an evidential commitment and
`sec:track-record` retains its present role.**

The ablation does not say that double entry is uniquely required. It says the
paper needs **some** worked, datable case that meets its stated discriminator:
movement of a formalism under relevant pressure, not an endpoint that can merely
be drawn as a graph. The existing double-entry case is the only such support in
this manuscript.

There are therefore two coherent paths:

1. **Keep the case** (or replace it with equally concrete evidence), while
   tightening the “no field owned it” transition and retaining the present
   candid limits. This preserves the fourth commitment as a supported,
   falsifiable empirical exposure.
2. **Remove the case and demote the fourth commitment.** Rename/reframe the
   section so it no longer claims a track record, label convergence toward graph
   form an untested conjecture, and do not present the field list as evidence.
   This preserves the conceptual paper but gives up the current empirical
   payload.

The experiment supports path 1 for the current paper: B is more compelling and
better calibrated without making the case carry the central ontological claim.

## Limits

This is evidence about argumentative function, not historical truth of the
accounting case or philosophical truth of paper 00. There were two independent
LLM reviewers, not a representative human-reader sample. They were blinded to
mapping and hypothesis, but each necessarily saw both manuscript texts; this is
blinding to experimental intent, not blindness to textual difference. Neither
reviewer checked external historical sources. The conclusion is therefore a
strong local result — agreement across opposite reading orders and independent
reviews — not a universal readership measurement.

## Verification

- Original source remained `papers/formal/00_is.tex` (r125); it was not edited
  for this experiment.
- Only experiment-directory copies and reports were created.
- The no-double-entry condition was checked textually: A has no `double entry`
  text; B retains it.
- No experiment artifact was committed or pushed.
