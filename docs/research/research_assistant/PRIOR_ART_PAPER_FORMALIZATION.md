# Prior art for paper-to-graph and formalization

Surveyed 2026-11-15. This assesses candidates against the current helper; it
does not claim they have been integrated or tested on our papers. The current
[fixed real-paper probe](../../../evaluation/research_assistant/real_papers_20261115_after/RESULTS.md)
translated 3 of 24 selected fragments and produced two Lean-accepted
definitions. That small sample is a regression set, not an accuracy estimate.

## Useful components

| Gap | Candidate | Potential use here | Boundary |
| --- | --- | --- | --- |
| TeX document and math structure | [LaTeXML](https://github.com/brucemiller/LaTeXML), [conversion documentation](https://math.nist.gov/~BMiller/LaTeXML/manual/usage/usage.conversion.html) | Parse whole documents into structured XML and MathML, including document context; retain our raw spans and links alongside the output. | Conversion needs compatible packages and bindings; XML or MathML structure does not determine a symbol's meaning. Verify whether source locations survive conversion on our actual papers. |
| Mathematical syntax and ambiguity | [SymPy LaTeX parsing](https://docs.sympy.org/latest/modules/parsing.html) with Lark backend | Generate structured expression candidates, using its ambiguity reporting and configurable grammar. Lower only explicitly supported, reviewed forms into native Terms. | Experimental and incomplete; its treatment of juxtaposition as multiplication may conflict with a paper's identifiers. The ANTLR backend can silently accept partial input. No parser's output should be treated as ground truth. |
| Paper-specific notation | LaTeXML bindings, source definitions and contextual symbol declarations | Associate definitions, scope, sorts, macros, assumptions and references with formula occurrences in the existing research graph. | A macro expansion or symbol occurrence does not by itself establish mathematical type or meaning. Conflicting interpretations must remain separate candidates. |
| Semantic interoperability | [OpenMath content dictionaries](https://openmath.org/standard/om20-2019-07-01/omstd20.html), [Math-in-the-Middle](https://arxiv.org/abs/1603.06424) | Evaluate crosswalks from typed graph symbols to shared mathematical vocabulary and explicit mappings to Lean or a computer algebra system. | Symbol dictionaries do not supply an execution engine or establish that a paper uses a symbol in the standard sense. Avoid adopting a new canonical representation before an actual cross-tool round trip is validated. |
| PDF structure | [GROBID](https://github.com/grobidOrg/grobid/blob/master/doc/Coordinates-in-PDF.md) TEI and PDF coordinates | Optional source adapter for sections, references and equation bounding boxes, preserving page coordinates. | [GROBID's FAQ](https://github.com/grobidOrg/grobid/blob/master/doc/Frequently-asked-questions.md) says superscript/subscript information is not serialized to TEI. It is not sufficient as a mathematical formula transcriber. |
| PDF mathematical transcription | [Nougat](https://facebookresearch.github.io/nougat/) | Evaluate as an optional PDF-to-markup transcription stage for papers without TeX source, with page-image provenance. | OCR output can corrupt notation; measure separately against source and treat it as proposed evidence. |
| Scientific claims and evidence | [SciFact](https://github.com/allenai/scifact) and [SciClaim](https://aclanthology.org/2021.emnlp-main.381/) | Borrow claim/evidence annotation and evaluation approaches; store sourced claim candidates and attributed support/refutation edges in the substrate. | SciFact evaluates evidence for supplied claims against abstracts; it is not a turnkey full-paper claim extractor. Automated labels are not established facts. |
| Categorical structure and execution | [DisCoPy](https://github.com/discopy/discopy); [Catlab.jl](https://github.com/AlgebraicJulia/Catlab.jl) | Compare typed objects, arrows, composition, identities and functor evaluation with the existing native graph/term execution. Prototype a narrow interoperability adapter and law checks. | A claim dependency graph is not automatically a category, and a categorical arrow is not automatically an executable native function. DisCoPy covers particular categorical structures; Catlab adds Julia integration cost. |
| Lean libraries and proof search | [Mathlib](https://leanprover-community.github.io/documentation.html), [LeanDojo](https://github.com/lean-dojo/LeanDojo), [Autoform Bot](https://github.com/facebookresearch/autoform-bot) | Resolve reviewed symbols to library declarations; investigate premise retrieval, project decomposition and compiler-guided proof attempts for claims with explicit obligations. | Pin Lean/Mathlib versions. Compilation checks a formal artifact, not source correspondence; proof-search tooling is a separate, potentially expensive integration. |
| Formalization evaluation | [ProofNet](https://github.com/zhangir-azerbayev/ProofNet), [ProofNet#/RLM25 and ProofNetVerif](https://arxiv.org/abs/2406.07222) | Evaluate statement fidelity separately from parsing and Lean acceptance, including research-level cases. | These are mathematical statement benchmarks, not a complete benchmark of raw PDF extraction, graph quality or native execution. |

## Recommended integration order

1. Add a document adapter interface retaining original source hash, spans,
   raw text, parser version, warnings and output provenance. Compare LaTeXML
   with the existing reader on the same TeX files; do not replace the existing
   path until source mapping and custom macros are evaluated.
2. Prototype an optional SymPy/Lark candidate parser. Preserve ambiguities and
   input consumption; only map a small verified expression subset into the
   substrate, recording domain and juxtaposition choices. Compare against the
   same 24 fragments and a manually annotated, broader held-out sample.
3. Extend the graph with scoped symbol/definition candidates, explicit types,
   equation references and source-backed assumption/dependency edges. Use the
   existing native graph as the authoritative execution/trace path. Compare
   categorical composition and identity behavior with DisCoPy on selected
   typed examples before deciding whether an adapter earns its dependency.
4. Add a separate Lean/Mathlib statement export and optional proof workflow,
   with versioned libraries, explicit hypotheses, provenance, and a check for
   placeholders and added axioms. Keep native execution equivalence and
   overflow conditions explicit. Distinguish a compiled definition, a
   typechecked proposition, and a kernel-checked proof.
5. Add PDF and prose claim extraction after the source-backed path has an
   evaluation set; reconcile extracted text/formulas with page locations.

For each stage report attempted/unsupported/error counts and manual fidelity
judgements, not just successful parses or Lean compilation. Test source
location, formula completeness, declared types, ambiguity, graph edge
precision, native outputs and Lean source correspondence separately. Include
counterexamples such as `mc` as one identifier versus `m*c`, differently
scoped identical symbols, and a syntactically valid but semantically wrong
formalization. Compare licensing, version requirements and resource costs
before adopting any component.

At survey time, `sympy`, `lark`, `pylatexenc`, `discopy`, and `lean_dojo` were
not importable in this checkout's `.venv`; `latexml` was not on PATH. These are
research candidates, not dependencies installed or verified in this change.
