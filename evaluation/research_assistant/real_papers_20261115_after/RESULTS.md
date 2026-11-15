# Real-paper capability: same sample after expansion

The same 24 source fragments used in the [initial probe](../real_papers_20261115/RESULTS.md)
were rerun against the expanded reader and translator. Source hashes and the
selected fragment sequences match the initial run.

| Fixed sample | Before translated / Lean accepted | After translated / Lean accepted |
| --- | ---: | ---: |
| GE theory: 12 fragments | 0 / 0 | 2 / 1 |
| arXiv:2606.13224: 12 fragments | 0 / 0 | 1 / 1 |
| **Total: 24 fragments** | **0 / 0** | **3 / 2** |

The newly accepted arXiv expression is explicit finite membership of two
variables in `{0,1}`. It becomes a native Boolean term and a Lean definition;
the scalar mapping and finite-domain meaning are recorded as assumptions. The
GE Lean-accepted expression maps an indexed symbol to an integer scalar; that
mapping and its domain require review. The other translated GE expression
compares opaque text labels; Lean refuses those string-symbol terms. A compiled
definition is not a proof that a paper's statement is true or faithfully
formalized. [results.json](results.json) contains every sampled fragment,
translation status and Lean error, with generated files in `lean/`.

## Source-level extraction and execution

The reader now records inline and displayed formulas as source-located
Evidence nodes, including outside formal theorem environments. It pages results
with stable IDs; formulas are not automatically asserted as claims.
On the three probe files, its first page returned 229 candidate spans in the
GE theory, 36 in Born recovery, and 256 in the arXiv file with more available.
These counts include individual symbols and are not validated formula-recall
measurements; inline delimiters are currently paired within one line. Details
are in [formula_inventory.json](formula_inventory.json).

Four hand-selected demonstrations exercise the full path from an automatically
located paper span through a graph candidate, native execution and Lean check:

- `N=2` from the narrativium paper, evaluated at `N=2` and `N=1`.
- `E_0=mc^2` from the same paper, interpreted as `E_0=m*(c^2)` using an
  explicitly supplied `mc` product mapping. The checked integer model is a
  finite example, not a proof of the physical formula or its units.
- `m,n ∈ ℕ` from the arXiv paper, with the **explicit modelling choice** that
  naturals begin at zero and the native signed-i64 bound. The source's macro
  interpretation and chosen convention need review.
- `ε,μ ∈ {0,1}` from the arXiv paper, evaluated inside and outside that set.

The [machine-readable demonstrations](automatic_examples.json) include source
hashes, line numbers, model residuals and the checked Lean files. They were
selected after the original probe and are not a coverage sample. Lean checked
the generated definitions; it did not prove the paper's broader claims.

## Boundaries and reproduction

The sample is still small, nonrandom, and has no independent semantic gold
labels. Sets with symbolic elements, set builders, categorical arrows,
function-valued terms, custom macros, unbounded quantification and much of the
papers' notation remain unsupported. Input strings accepted as scalar names or
opaque symbols can still misrepresent the author's meaning; user review and
explicit domain assumptions remain necessary. The original source may use
macros or cross-file definitions the reader has not resolved. Lean export still
refuses constructs for which it cannot preserve the native semantics.

From the repository root with local Lean and the sibling source present:

```bash
python - <<'PY'
from pathlib import Path
import evaluation.research_assistant.real_paper_capability as probe
probe.OUT = Path('evaluation/research_assistant/real_papers_20261115_after').resolve()
probe.main()
PY
python -m evaluation.research_assistant.formula_inventory
python -m evaluation.research_assistant.automatic_formula_demo
```

The source paths and hashes are in the JSON records. The arXiv source lives in
gitignored `data/` and is not archived here. The original run remains separately
available for comparison; its result file was not overwritten.
