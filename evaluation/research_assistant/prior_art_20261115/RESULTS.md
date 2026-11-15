# Prior-art integration probe

The [integration plan](../../../docs/research/research_assistant/PRIOR_ART_INTEGRATION_PLAN.md)
was exercised with SymPy 1.14.0, Lark 1.2.2 and DisCoPy 1.2.1 in the local
virtual environment. The optional dependencies are listed in
`requirements-research-optional.txt`.

The SymPy/Lark adapter received the exact 24 raw fragments from the existing
real-paper sample. It returned one ambiguous parse candidate and 23 unparsed
results: 1/12 ambiguous for GE theory and 0/12 parsed for arXiv 2606.13224. The third paper had no
fragments in this particular formal-environment sample. The one candidate was
`\delta^P=a`; its syntax is not a verified interpretation of the paper. The
input contains paper-specific macros, set notation, arrows and formatting that
the parser frequently cannot consume. Full results and the source hashes are
in [sympy_paper_probe.json](sympy_paper_probe.json). A parser candidate is not
an executable substrate Term and cannot be compared directly to the prior
3/24 executable translations as a gain in model coverage. This small,
nonrandom sample has no semantic gold labels.

The [categorical probe](categorical_interop.json) compared a single typed
`X → Y → Z` DisCoPy diagram and left identity with native graph rewrite rules.
The diagram's boundaries and the native composed edge agreed, all six source
IDs were retained, and DisCoPy simplified the selected identity. The substrate
produced an identity witness edge, not a quotient proving arrow equality.
There is no general functor, associativity check, right-identity check or
demonstration of paper-level meaning in this experiment.

The optional LaTeXML path summarizes a separately supplied XML file and emits
bounded equation candidates, with
both hashes and an explicit unverified source correspondence. It has fixture
tests but no real conversion result: LaTeXML itself was unavailable locally.
It does not create graph claims from XML. Scoped mathematical symbols and
definitions can now be authored in the research graph; automatic extraction,
name resolution and type checking remain future work.

Reproduce from the repository root, after installing the optional requirements:

```bash
.venv/bin/python -m evaluation.research_assistant.sympy_paper_probe
MPLCONFIGDIR=/tmp/ocelot-matplotlib .venv/bin/python -m evaluation.research_assistant.categorical_interop
```

Original baseline data remains unchanged. Inspect output candidate forms and
parser diagnostics rather than treating success counts as correctness.

## Source context and model execution

The subsequent [arXiv scope evaluation](contextual_resolution_arxiv.json)
ingests arXiv:2606.13224 and uses the native graph to follow the formula's
local Frame to the paper Frame. It finds the paper's `\NN` declaration at
line 89 and its use in `m,n\in\NN` at line 219. The translator uses that
source-linked macro expansion. The source declaration alone does not specify
whether zero is a natural number: without an explicit convention, model
creation reports unsupported. With minimum 0 and 1 supplied as separate
assumptions, both candidate models executed on positive and negative inputs,
their generated Lean definitions were accepted, and their traces include the
formula evidence, local Frame and macro node. Lean acceptance checks those
definitions, not their fidelity to the paper or the paper's broader theorem.
This is one hand-selected example, not a coverage estimate or a proof of the
paper's claim. Run it with
`.venv/bin/python -m scripts.eval_arxiv_scoped_formula_resolution --output /tmp/arxiv-context.json`.
