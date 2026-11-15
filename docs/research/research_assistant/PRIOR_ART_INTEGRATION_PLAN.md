# Paper-to-graph prior-art integration plan

Objective: improve paper ingestion, scoped mathematical meaning, native graph
execution and Lean output using existing tools where they are demonstrated to
help. Preserve original paper evidence and distinguish proposed interpretations
from checked results.

1. **Structured source**: implement an optional LaTeXML adapter alongside the
   existing reader. Preserve source hash, output provenance and parser errors;
   only attach exact source locators when demonstrably available. Exercise both
   the adapter and the absence/failure paths.
2. **Formula candidates**: add an optional SymPy/Lark parser that retains the
   original formula, parser version, diagnostics and ambiguity. Its output is
   a proposal; do not silently substitute its interpretation for executable
   Terms. Test ambiguous juxtaposition and incomplete input explicitly.
3. **Scoped symbols**: represent mathematical symbols, scoped definitions,
   meanings and assumptions as sourced nodes and relations in the existing
   research ledger and native projection. Preserve competing interpretations.
4. **Category and Lean**: compare typed composition and identity to DisCoPy on
   a bounded executable chain, then assess an adapter against actual substrate
   behavior. Retain Lean compilation as a separate result from source fidelity
   and proof; investigate Mathlib and proof search only when a specific
   reproducible obligation warrants the additional dependencies.
5. **Evaluation**: run optional tools on the existing 24-fragment paper probe
   and representative document files when available. Report attempted, parsed,
   ambiguous and failed results separately, along with source hashes, versions,
   limitations and reproduction commands. Keep the original baselines intact.
   Add tests for dependency absence, parser errors, provenance and graph links.

PDF transcription, broad scientific-claim extraction, full Mathlib
autoformalization and semantic-interchange standards need their own measured
integration once source-level coverage and symbol resolution are established.
They are not implied by successfully parsing LaTeX or compiling a definition.

## Execution status

The optional SymPy/Lark candidate service and scoped graph vocabulary are
implemented. The LaTeXML adapter consumes a separately produced XML artifact;
its source correspondence is unverified and it does not invoke the converter.
A bounded DisCoPy comparison has been run. The first measured results and
remaining limitations are in the
[integration probe](../../../evaluation/research_assistant/prior_art_20261115/RESULTS.md).
Automatic scoped-symbol resolution, a general categorical functor or law
checker, and a Mathlib proof workflow remain unimplemented.
