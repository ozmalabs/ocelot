# Real-paper extraction and Lean capability probe

**Result: statement ingestion worked for two selected papers, but no sampled
mathematical fragment went through the full automatic path as written.** This
is an exploratory capability probe, not an estimate of general accuracy.

| Local paper source | Formal statement records | Math fragments attempted | Translated | Lean accepted |
| --- | ---: | ---: | ---: | ---: |
| GE theory, `01_law_of_graphic_equalisation_theory_referenced.tex` | 67 | 12 | 0 | 0 |
| GE Born recovery, `01d_graphic_equalisation_born_recovery.tex` | 0 | 0 | 0 | 0 |
| arXiv:2606.13224, *Bott-Chern and Aeppli Homotopy* | 57 | 12 | 0 | 0 |

The source files and SHA-256 hashes, all attempted fragments, reasons and
locators are in [results.json](results.json). The GE reader reported 19
unresolved references for the theory paper. The numbers of records are what
the reader emitted, not validated precision or recall. The Born paper contains
mathematics but no supported recognized statement environments in the selected
file: zero records means this reader did not capture them, not that the paper
contains no claims. The arXiv source is under the local gitignored `data/`
corpus; its content hash is recorded, but the file is not archived here.

Selection was the first 12 delimited, operator-bearing math fragments in
recognized statement environments in each chosen file, in source order.
There were 16 eligible fragments in the GE theory and 126 in the arXiv source;
the rest were not attempted. The probe supplies those fragments to the helper:
the paper-ingestion API itself does **not** isolate formulas. The selection is
heuristic, nonrandom, and does not inspect graphics, external `\\input` files,
unrecognized prose statements, or every piece of mathematics. Without an
independent annotated inventory and semantic ground truth, these data do not
establish extraction recall or translation correctness.

The rejected fragments include graph tuples and custom GE macros, sets and
functions, and categorical operators and subscripts in the arXiv paper. The
reader records the source assertions and references, but the formula
translator does not yet represent these constructs. It is therefore premature
to claim general paper-to-model or paper-to-Lean capability.

## Hand-selected source controls

After the first-pass failures, three simple or diagnostic formulas were
manually located in two other local GE papers. These are **not part of the
sample above** and do not estimate coverage. The controls, source hashes and
locators are in [manual_controls.json](manual_controls.json).

- `N=2`, in the narrativium paper's finite worked example, translated to a
  native equality. The native result was true for `N=2` and false for `N=1`.
  The generated [Lean definition](lean/control_simple_integer.lean) compiled
  with Lean 4.33.1, and a [concrete `by decide` example](lean/control_simple_integer_example.lean)
  was accepted. That checks the chosen Boolean equality at one input; it does
  **not** prove that the paper's stated count follows from its construction.
- `g=0.13`, from a separate reporting passage, translated to a native
  floating-point equality. Lean export refused the floating literal, so no
  Lean file was built for it. This test does not validate the underlying
  empirical result.
- `E_0=mc^2` was accepted as `E_0 = (mc)^2`, treating `mc` as one variable.
  The paper intends a mass–energy relation, so this is **not** a faithful
  interpretation of implicit multiplication. The translator now emits an
  explicit ambiguity residual for adjacent-letter identifiers; the model still
  requires review. Lean export refused the power term.

In addition, a separate read-only agent tested the existing broader LaTeX
reader on the first two controls. It dropped the left side of `N=2` and read
`g=0.13` as a product of `0` and `13`; its `comprehends` flag is not evidence
of faithful parsing. This reinforces the need for a checked, lossless parser
and source-to-model review rather than interpreting syntax acceptance as
understanding.

## Reproduction

Run the following from the Ocelot checkout, with the sibling GE checkout, the
local arXiv file and project-local Lean 4.33.1 present:

```bash
python -m evaluation.research_assistant.real_paper_capability
python -m evaluation.research_assistant.real_paper_manual_controls
```

The scripts write results and generated Lean under this directory. Lean's
acceptance is a kernel check of generated declarations and the explicitly
added small example, not verification of the paper's scientific assertions.
The next defensible capability study needs a frozen multi-paper source manifest,
independent annotations of statement/formula spans and intended semantics,
and separate metrics for extraction, translation correctness, executable
agreement and Lean compilation. The local sample does not provide those labels.
