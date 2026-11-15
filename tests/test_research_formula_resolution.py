from __future__ import annotations

from scripts.ocelot_research import ResearchGraph
from scripts.ocelot_formula_resolution import resolve_formula_ambiguity
from scripts.ocelot_research_formula import translate_formula


def _symbol(graph, scope, name, *, arity=0):
    symbol = graph.record("MathematicalSymbol", name=name, notation=name,
                          arity=arity, identity=f"{scope['id']}.{name}")
    graph.link(symbol["id"], "scoped_by", scope["id"])
    return symbol


def test_graph_selects_only_scoped_factorization_and_mapping_is_executable(tmp_path):
    graph = ResearchGraph.create("Resolve notation", root=tmp_path,
                                 investigation_id="formula-resolve-product")
    frame = graph.record("Frame", wording="Energy equation scope")
    _symbol(graph, frame, "E")
    m, c = _symbol(graph, frame, "m"), _symbol(graph, frame, "c")
    definition = graph.record("MathematicalDefinition", wording="m is mass and c is light speed",
                              status="proposed", provenance="reviewed source notation")
    graph.link(definition["id"], "defines", m["id"])
    graph.link(definition["id"], "defines", c["id"])

    result = resolve_formula_ambiguity(graph, "E=mc^2", scope_id=frame["id"])
    assert result["status"] == "selected"
    assert result["implicit_products"] == {"mc": ["m", "c"]}
    assert result["definitions"]
    assert result["provenance"]["native_query_engine"]["engine"]
    translated = translate_formula("E=mc^2", implicit_products=result["implicit_products"])
    assert translated.variables == ("E", "c", "m")


def test_unique_scoped_compact_symbol_is_selected_without_product_rewrite(tmp_path):
    graph = ResearchGraph.create("Select graph-declared compact symbol", root=tmp_path,
                                 investigation_id="formula-resolve-single-symbol")
    frame = graph.record("Frame", wording="Equation scope")
    symbol = _symbol(graph, frame, "mc")
    result = resolve_formula_ambiguity(graph, "E=mc^2", scope_id=frame["id"])
    assert result["status"] == "selected"
    assert result["implicit_products"] == {}
    assert result["selected_symbols"] == {
        "mc": {"symbol_id": symbol["id"], "scope_frame_id": frame["id"]}}
    assert result["selected_interpretation"]["kind"] == "scoped_symbol_readings"


def test_exact_symbol_and_factorization_remain_tied(tmp_path):
    graph = ResearchGraph.create("Retain genuine ambiguity", root=tmp_path,
                                 investigation_id="formula-resolve-tie")
    frame = graph.record("Frame", wording="Local scope")
    _symbol(graph, frame, "mc")
    _symbol(graph, frame, "m")
    _symbol(graph, frame, "c")
    result = resolve_formula_ambiguity(graph, "mc=1", scope_id=frame["id"])
    assert result["status"] == "tied"
    assert result["implicit_products"] == {}
    assert {c["kind"] for c in result["tied"][0]["candidates"]} == {
        "single_symbol", "implicit_product"}


def test_unscoped_symbols_do_not_resolve_and_function_evidence_is_reported(tmp_path):
    graph = ResearchGraph.create("Scope evidence", root=tmp_path,
                                 investigation_id="formula-resolve-scope")
    frame = graph.record("Frame", wording="Only this frame counts")
    other = graph.record("Frame", wording="Different scope")
    _symbol(graph, other, "m")
    _symbol(graph, other, "c")
    f = _symbol(graph, frame, "f", arity=1)
    result = resolve_formula_ambiguity(graph, "mc=f(x)", scope_id=frame["id"])
    assert result["status"] == "function_evidence_only"
    assert result["implicit_products"] == {}
    assert result["function_evidence"] == [{"notation": "f", "symbol_ids": [f["id"]],
                                             "arities": [1]}]


def test_other_unsupported_compact_names_keep_formula_partially_unresolved(tmp_path):
    graph = ResearchGraph.create("Do not fill unknown notation", root=tmp_path,
                                 investigation_id="formula-resolve-partial")
    frame = graph.record("Frame", wording="Local scope")
    _symbol(graph, frame, "m")
    _symbol(graph, frame, "c")
    result = resolve_formula_ambiguity(graph, "E=mc+uv", scope_id=frame["id"])
    assert result["status"] == "partially_resolved"
    assert result["implicit_products"] == {"mc": ["m", "c"]}
    assert "uv" in result["unresolved_notation"]


def test_scoped_tex_macro_is_returned_as_uninterpreted_evidence(tmp_path):
    graph = ResearchGraph.create("Keep macro expansion uninterpreted", root=tmp_path,
                                 investigation_id="formula-resolve-macro")
    frame = graph.record("Frame", wording="Paper notation scope")
    macro = graph.record("MathematicalSymbol", name=r"\NN", expansion=r"\mathbb{N}",
                         arity=0, interpretation_status="source_declared_uninterpreted",
                         semantics_verified=False,
                         locator={"path": "paper.tex", "start_line": 1})
    graph.link(macro["id"], "scoped_by", frame["id"])
    result = resolve_formula_ambiguity(graph, r"n\in\NN", scope_id=frame["id"])
    assert result["macro_evidence"] == [{
        "notation": r"\NN", "symbol_id": macro["id"],
        "scope_frame_id": frame["id"],
        "expansion": r"\mathbb{N}", "locator": {"path": "paper.tex", "start_line": 1},
        "interpretation_status": "source_declared_uninterpreted",
        "semantics_verified": False,
    }]


def test_child_scope_inherits_paper_macro_without_sibling_leakage(tmp_path):
    graph = ResearchGraph.create("Resolve through scoped parent", root=tmp_path,
                                 investigation_id="formula-resolve-ancestor")
    paper = graph.record("Frame", wording="Paper frame", scope_kind="paper")
    local = graph.record("Frame", wording="Local declaration", scope_kind="local_source_context")
    sibling = graph.record("Frame", wording="Unrelated local declaration", scope_kind="local_source_context")
    graph.link(local["id"], "scoped_by", paper["id"],
               provenance={"kind": "local_scope_parent"})
    graph.link(sibling["id"], "scoped_by", paper["id"],
               provenance={"kind": "local_scope_parent"})
    _symbol(graph, local, "m")
    _symbol(graph, local, "n")
    macro = graph.record("MathematicalSymbol", name=r"\NN", expansion=r"\mathbb{N}",
                         arity=0, interpretation_status="source_declared_uninterpreted",
                         semantics_verified=False, locator={"path": "paper.tex", "start_line": 1})
    graph.link(macro["id"], "scoped_by", paper["id"])
    sibling_symbol = _symbol(graph, sibling, "uv")

    result = resolve_formula_ambiguity(graph, r"mn\in\NN", scope_id=local["id"])
    assert result["status"] == "selected"
    assert result["implicit_products"] == {"mn": ["m", "n"]}
    assert result["macro_evidence"][0]["symbol_id"] == macro["id"]
    assert paper["id"] in result["provenance"]["context_frame_ids"]
    assert sibling["id"] not in result["provenance"]["context_frame_ids"]
    assert all(sibling_symbol["id"] not in item["symbol_ids"]
               for item in result["interpretations"])


def test_inherited_conflicting_symbol_readings_remain_tied(tmp_path):
    graph = ResearchGraph.create("Keep inherited notation conflicts", root=tmp_path,
                                 investigation_id="formula-resolve-inherited-tie")
    paper = graph.record("Frame", wording="Paper frame")
    local = graph.record("Frame", wording="Local frame")
    graph.link(local["id"], "scoped_by", paper["id"])
    paper_m = _symbol(graph, paper, "m")
    local_m = _symbol(graph, local, "m")
    _symbol(graph, local, "c")
    result = resolve_formula_ambiguity(graph, "mc=1", scope_id=local["id"])
    assert result["status"] == "tied"
    products = [candidate for candidate in result["tied"][0]["candidates"]
                if candidate["kind"] == "implicit_product"]
    assert {candidate["symbol_ids"][0] for candidate in products} == {
        paper_m["id"], local_m["id"]}
