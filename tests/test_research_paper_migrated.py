from __future__ import annotations

import hashlib

from scripts.ocelot_research import ResearchGraph
from scripts.ocelot_research_paper import ingest_paper, preview_paper


def _graph(tmp_path, relpath: str, content: str):
    source_root = tmp_path / "sources"
    source_root.mkdir(exist_ok=True)
    path = source_root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    graph = ResearchGraph.create(
        "Review a paper", root=tmp_path, investigation_id="paper-test",
        roots=[{"root_id": "papers", "path": str(source_root),
                "repository": "fixture", "files": {relpath: "selected"}}],
    )
    return graph


def test_markdown_preview_and_ingest_are_located_and_unverified(tmp_path):
    graph = _graph(tmp_path, "paper.md", "# Demo\n\n## Theorem T (A sample result)\n\nFor every x, P(x).\n")
    before = len(graph.state()["events"])
    preview = preview_paper(graph, root_id="papers", path="paper.md")
    assert len(graph.state()["events"]) == before
    assert preview["records"][0]["locator"]["start_line"] == 3
    assert preview["sha256"]
    result = ingest_paper(graph, root_id="papers", path="paper.md")
    claim = result["claims"][0]
    assert claim["parsed_assertion"] is True
    assert claim["semantics_verified"] is False
    assert claim["status"] == "unresolved"
    assert claim["source_locator"]["path"] == "paper.md"
    assert "model_candidate" not in claim
    assert ingest_paper(graph, root_id="papers", path="paper.md")["duplicate"] is True


def test_tex_proof_refs_and_unresolved_extraction_are_preserved(tmp_path):
    tex = (r"\begin{theorem}\label{thm:main} For every x, P(x).\end{theorem}" "\n"
           r"\begin{proof}Use \ref{lem:missing}.\end{proof}" "\n")
    graph = _graph(tmp_path, "sample.tex", tex)
    preview = preview_paper(graph, root_id="papers", path="sample.tex")
    record = preview["records"][0]
    assert record["label"] == "thm:main"
    assert record["proof_references"] == ["lem:missing"]
    assert record["proof_locator"]["start_line"] == 2
    assert preview["unresolved_references"][0]["reference"] == "lem:missing"
    result = ingest_paper(graph, root_id="papers", path="sample.tex")
    assert result["claims"][0]["proof_text"]
    assert result["claims"][0]["unresolved_references"]


def test_latexml_supplement_is_fixture_driven_and_keeps_tex_as_authority(tmp_path):
    import hashlib

    tex = r"\begin{theorem}\label{thm:main} For every x, P(x).\end{theorem}"
    source_root = tmp_path / "sources"
    source_root.mkdir()
    (source_root / "sample.tex").write_text(tex, encoding="utf-8")
    xml = ("<?xml version='1.0'?>\n"
           "<ltx:document xmlns:ltx='http://dlmf.nist.gov/LaTeXML'>"
           "<ltx:title>Fixture title</ltx:title>"
           "<ltx:theorem label='thm:main'><ltx:p>converted text</ltx:p></ltx:theorem>"
           "<ltx:equation label='eq:one'><ltx:Math><ltx:XMath>x = 2</ltx:XMath>"
           "</ltx:Math></ltx:equation></ltx:document>")
    (tmp_path / "sources" / "sample.xml").write_text(xml, encoding="utf-8")
    # Manifest selection is explicit for both the TeX source and converter output.
    graph = ResearchGraph.create(
        "Review a paper", root=tmp_path, investigation_id="latexml-test",
        roots=[{"root_id": "papers", "path": str(source_root),
                "repository": "fixture",
                "files": {"sample.tex": "source", "sample.xml": "converter output"}}],
    )
    report = preview_paper(graph, root_id="papers", path="sample.tex",
                           latexml_path="sample.xml")
    converted = report["latexml_document"]
    assert converted["title"] == "Fixture title"
    assert converted["structure_counts"] == {"theorem": 1, "equation": 1}
    assert converted["labels"] == ["thm:main", "eq:one"]
    equation = converted["equation_candidates"][0]
    assert equation["label"] == "eq:one"
    assert "XMath" in equation["serialized_xml"]
    assert equation["text"] == "x = 2"
    assert equation["interpretation_status"] == "unverified_converter_candidate"
    assert equation["artifact_provenance"]["document_sha256"] == converted["document_sha256"]
    assert equation["artifact_provenance"]["source_sha256"] == converted["source_sha256"]
    assert equation["artifact_provenance"]["source_correspondence_verified"] is False
    assert equation["artifact_provenance"]["source_locator"] is None
    assert converted["source_sha256"] == hashlib.sha256(tex.encode()).hexdigest()
    assert converted["source_locators_available"] is False
    assert converted["use_for_claim_ingestion"] is False
    assert report["records"][0]["raw_excerpt"] == tex
    assert report["records"][0]["locator"] == {
        "start_line": 1, "end_line": 1, "label_line": 1}


def test_latexml_equation_candidates_are_bounded():
    from scripts.ocelot_research_paper import _latexml_document_report

    equations = "".join(f"<equation label='eq:{i}'/>" for i in range(40))
    report = _latexml_document_report(
        f"<document>{equations}</document>".encode(),
        source_sha256="a" * 64, document_path="paper.xml")
    assert report["structure_counts"]["equation"] == 40
    assert len(report["equation_candidates"]) == 32
    assert report["equation_candidates_truncated"] is True
    assert report["equation_candidate_limit"] == 32


def test_latexml_fixture_rejects_entity_declarations():
    import pytest
    from scripts.ocelot_research import ResearchError
    from scripts.ocelot_research_paper import _latexml_document_report

    with pytest.raises(ResearchError, match="DTD/entity"):
        _latexml_document_report(
            b"<!DOCTYPE x [<!ENTITY e 'boom'>]><x>&e;</x>",
            source_sha256="a" * 64, document_path="paper.xml")


def test_unselected_and_escaping_files_are_rejected(tmp_path):
    graph = _graph(tmp_path, "paper.md", "# Empty\n")
    import pytest
    from scripts.ocelot_research import ResearchError
    with pytest.raises(ResearchError, match="not explicitly selected"):
        preview_paper(graph, root_id="papers", path="other.md")
    with pytest.raises(ResearchError):
        preview_paper(graph, root_id="papers", path="../outside.md")


def test_manually_recorded_matching_source_does_not_block_import(tmp_path):
    graph = _graph(tmp_path, "paper.md", "# Demo\n\n## Theorem T (A result)\n\nFor every x, P(x).\n")
    digest = hashlib.sha256((tmp_path / "sources" / "paper.md").read_bytes()).hexdigest()
    graph.record("Source", name="paper.md", locator={
        "root_id": "papers", "repository": "fixture", "path": "paper.md",
        "sha256": digest, "kind": "paper"})
    preview = preview_paper(graph, root_id="papers", path="paper.md")
    assert preview["duplicate"] is False
    assert preview["partial_import"] is False
    result = ingest_paper(graph, root_id="papers", path="paper.md")
    assert result["ingested"] is True


def test_displayed_formulas_are_sourced_evidence_not_claims(tmp_path):
    tex = ("Intro prose.\n"
           "\\[ N=2 \\]\n"
           "\\begin{remark}\nA local observation.\n"
           "\\begin{equation} E_0=mc^2 \\end{equation}\n"
           "\\end{remark}\n"
           "\\begin{theorem}T\n\\begin{equation}x=y\\end{equation}\n"
           "\\end{theorem}\n")
    graph = _graph(tmp_path, "formulas.tex", tex)
    preview = preview_paper(graph, root_id="papers", path="formulas.tex")
    candidates = preview["formula_candidates"]
    assert len(candidates) == 3
    assert candidates[0]["formula"] == "N=2"
    assert candidates[0]["locator"]["start_line"] == 2
    assert candidates[0]["locator"]["end_line"] == 2
    assert candidates[0]["locator"]["start_offset"] < candidates[0]["locator"]["end_offset"]
    assert candidates[1]["context_kind"] == "remark"
    assert candidates[1]["is_claim"] is False
    assert candidates[1]["ambiguity"]
    assert candidates[2]["containing_claim_indexes"] == [0]

    result = ingest_paper(graph, root_id="papers", path="formulas.tex")
    assert len(result["formula_evidence"]) == 3
    assert all(e["evidence_type"] == "sourced_formula_candidate" for e in result["formula_evidence"])
    assert len(result["claims"]) == 1
    containment_edges = [edge for edge in graph.state()["edges"]
                         if edge.get("provenance", {}).get("kind") == "source_span_containment"]
    assert len(containment_edges) == 1
    assert containment_edges[0]["src"] == result["formula_evidence"][2]["id"]
    assert containment_edges[0]["tgt"] == result["claims"][0]["id"]


def test_real_ge_paper_display_math_locator_when_sibling_is_available():
    from pathlib import Path
    import pytest
    source = (Path(__file__).resolve().parents[1].parent / "graphic-equalisation" /
              "papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex")
    if not source.is_file():
        pytest.skip("sibling GE paper checkout is unavailable")
    from scripts.ocelot_research_paper import _formula_candidates
    text = source.read_text(encoding="utf-8")
    candidates = _formula_candidates(text)
    assert candidates
    first = candidates[0]
    lines = text.splitlines()
    excerpt = "\n".join(lines[first["locator"]["start_line"] - 1:
                            first["locator"]["end_line"]])
    assert first["raw_excerpt"] in excerpt
    assert first["interpretation_status"] == "unparsed_candidate"


def test_inline_math_is_located_and_fenced_or_commented_math_is_skipped(tmp_path):
    from scripts.ocelot_research_paper import _formula_candidates_report
    tex = ("% $commented$\n"
           "Inline $N=2$ then \\(g=0.13\\).\n"
           "$$D=3$$\n")
    candidates, report = _formula_candidates_report(tex)
    assert [candidate["formula"].strip() for candidate in candidates] == ["N=2", "g=0.13", "D=3"]
    assert [candidate["presentation"] for candidate in candidates] == [
        "inline", "inline", "display"]
    assert all(candidate["raw_excerpt"] for candidate in candidates)
    assert report["truncated"] is False
    assert report["unmatched_delimiters"] == []

    markdown = ("Inline $x=1$.\n\n```tex\n$x=2$\n$$x=3$$\n```\n"
                "<!-- $x=4$ -->\n`$x=6$` and \\(x=5\\)\n")
    md_candidates, _ = _formula_candidates_report(markdown, markdown=True)
    assert [candidate["formula"].strip() for candidate in md_candidates] == ["x=1", "x=5"]

    escaped, escaped_report = _formula_candidates_report(
        r"\$literal \\$paired$ end")
    assert [candidate["formula"].strip() for candidate in escaped] == ["paired"]
    assert escaped_report["unmatched_delimiters"] == []


def test_inline_unmatched_delimiters_and_candidate_cap_are_explicit(tmp_path):
    from scripts.ocelot_research_paper import _formula_candidates_report
    candidates, report = _formula_candidates_report("$x$ $y$ $z", max_candidates=1)
    assert len(candidates) == 1
    assert report["truncated"] is True
    assert report["max_candidates"] == 1
    assert report["unmatched_delimiters"] == [{
        "delimiter": "$", "line": 1,
        "reason": "unpaired single-dollar delimiter"}]


def test_real_inline_narrativium_control_is_found_when_sibling_is_available():
    from pathlib import Path
    import pytest
    source = (Path(__file__).resolve().parents[1].parent / "graphic-equalisation" /
              "papers/formal/04_narrativium_theory_referenced.tex")
    if not source.is_file():
        pytest.skip("sibling GE paper checkout is unavailable")
    from scripts.ocelot_research_paper import _formula_candidates
    text = source.read_text(encoding="utf-8")
    candidates = _formula_candidates(text)
    match = next(candidate for candidate in candidates
                 if candidate["formula"].strip() == "N=2")
    assert match["presentation"] == "inline"
    assert match["locator"]["start_line"] == 150
    assert match["raw_excerpt"] == "$N=2$"


def test_tex_math_context_captures_explicit_macros_and_local_domains(tmp_path):
    tex = ("\\newcommand\\NN{\\mathbb{N}}\n"
           "% \\newcommand\\BAD{\u211d}\n"
           "\\begin{verbatim}\n\\newcommand\\FAKE{0}\n\\end{verbatim}\n"
           "Let $m,c$ be real numbers.\n"
           "For all $m,n\\in\\NN$, the construction applies.\n")
    graph = _graph(tmp_path, "context.tex", tex)
    preview = preview_paper(graph, root_id="papers", path="context.tex")
    records = preview["mathematical_context"]["records"]
    symbol = next(item for item in records if item["kind"] == "symbol")
    assert symbol["name"] == r"\NN"
    assert symbol["expansion"] == r"\mathbb{N}"
    assert symbol["locator"]["start_line"] == 1
    assert not any(item.get("name") in {r"\BAD", r"\FAKE"} for item in records)
    explicit = [item for item in records if item["declaration"] in {
        "explicit_prose_domain", "explicit_domain_membership"}]
    assert len(explicit) == 2
    assert explicit[0]["name"] == "m,c"
    assert explicit[0]["expansion"] == "real numbers"
    assert explicit[1]["name"] == "m,n"
    assert explicit[1]["expansion"] == r"m,n\in\NN"
    assert all(item["semantics_verified"] is False for item in records)

    result = ingest_paper(graph, root_id="papers", path="context.tex")
    assert result["frame_id"]
    assert result["mathematical_context"]
    nodes = {node["id"]: node for node in graph.state()["nodes"]}
    scoped = {edge["src"] for edge in graph.state()["edges"] if edge["type"] == "scoped_by"}
    assert all(node["id"] in scoped for node in result["mathematical_context"])
    assert {node["id"] for node in result["mathematical_context"]} <= scoped
    formulas = [node for node in graph.state()["nodes"]
                if node["type"] == "Evidence" and node.get("evidence_type") == "sourced_formula_candidate"]
    assert all(node["id"] in scoped for node in formulas)


def test_real_arxiv_tex_notation_context_is_source_located():
    from pathlib import Path
    from scripts.ocelot_research_paper import _math_context

    source = Path(__file__).resolve().parents[1] / "data/arxiv/2606.13224/main.tex"
    if not source.is_file():
        import pytest
        pytest.skip("selected arXiv TeX source is unavailable")
    records = _math_context(source.read_text(encoding="utf-8"),
                            root_id="arxiv", path="2606.13224/main.tex",
                            sha256="test-digest")["records"]
    macro = next(record for record in records if record.get("name") == r"\NN")
    membership = next(record for record in records
                      if record.get("expansion") == r"m,n\in\NN")
    assert (macro["locator"]["start_line"], macro["expansion"]) == (89, r"\mathbb{N}")
    assert membership["locator"]["start_line"] == 219
    assert membership["name"] == "m,n"


def test_local_domain_scope_covers_enclosing_statement_only_and_reuses_frame(tmp_path):
    tex = ("\\begin{theorem}\n"
           "Let $m$ be a real number. Choose $c$ as a real number.\n"
           "The expression $(m+c)^2$ is considered here.\n"
           "\\end{theorem}\n"
           "\\begin{remark}\n"
           "The expression $m+c$ is mentioned separately.\n"
           "\\end{remark}\n")
    graph = _graph(tmp_path, "local-scope.tex", tex)
    result = ingest_paper(graph, root_id="papers", path="local-scope.tex")
    state = graph.state()
    nodes = {node["id"]: node for node in state["nodes"]}
    edge_targets = {edge["src"]: edge["tgt"] for edge in state["edges"]
                    if edge["type"] == "scoped_by"}
    definitions = [node for node in state["nodes"]
                   if node["type"] == "MathematicalDefinition"
                   and node.get("declaration") == "explicit_prose_domain"]
    assert len(definitions) == 2
    m_scope, c_scope = (edge_targets[node["id"]] for node in definitions)
    assert m_scope == c_scope
    local_frames = [node for node in state["nodes"] if node["type"] == "Frame"
                    and node.get("scope_kind") == "local_source_context"]
    assert len(local_frames) == 1
    local_frame_id = local_frames[0]["id"]
    assert m_scope == local_frame_id
    assert any(edge["src"] == local_frame_id and edge["type"] == "scoped_by"
               and edge["tgt"] == result["frame_id"] for edge in state["edges"])

    formulas = [node for node in state["nodes"]
                if node["type"] == "Evidence" and node.get("evidence_type") == "sourced_formula_candidate"]
    theorem_formula = next(node for node in formulas if node.get("wording") == "(m+c)^2")
    remark_formula = next(node for node in formulas if node.get("wording") == "m+c")
    assert edge_targets[theorem_formula["id"]] == local_frame_id
    assert edge_targets[remark_formula["id"]] == result["frame_id"]
    assert nodes[local_frame_id]["source_locator"]["start_line"] == 1


def test_macro_declared_inside_statement_scopes_only_that_statement(tmp_path):
    tex = ("\\begin{theorem}\n"
           "\\newcommand\\LocalN{\\mathbb{N}}\n"
           "The notation $\\LocalN$ is used here.\n"
           "\\end{theorem}\n"
           "The notation $\\LocalN$ is also mentioned later.\n")
    graph = _graph(tmp_path, "local-macro.tex", tex)
    result = ingest_paper(graph, root_id="papers", path="local-macro.tex")
    state = graph.state()
    formula_nodes = [node for node in state["nodes"]
                     if node["type"] == "Evidence" and node.get("evidence_type") == "sourced_formula_candidate"]
    inside = next(node for node in formula_nodes if node.get("wording") == r"\LocalN")
    outside = [node for node in formula_nodes if node.get("wording") == r"\LocalN"]
    assert len(outside) == 2
    outside = max(outside, key=lambda node: node["locator"]["start_line"])
    targets = {edge["src"]: edge["tgt"] for edge in state["edges"]
               if edge["type"] == "scoped_by"}
    assert targets[inside["id"]] != result["frame_id"]
    assert targets[outside["id"]] == result["frame_id"]
    local_frames = [node for node in state["nodes"] if node["type"] == "Frame"
                    and node.get("scope_kind") == "local_source_context"]
    assert len(local_frames) == 1
    macro = next(node for node in state["nodes"] if node["type"] == "MathematicalSymbol"
                 and node.get("name") == r"\LocalN")
    assert targets[macro["id"]] == local_frames[0]["id"]


def test_formula_ingest_pages_resume_and_deduplicate_overlapping_ranges(tmp_path):
    tex = ("## Formula paper\n"
           "First $a=1$. Second \\(b=2\\). Third $$c=3$$.\n")
    graph = _graph(tmp_path, "paged.tex", tex)
    first = ingest_paper(graph, root_id="papers", path="paged.tex",
                         max_formula_candidates=0)
    assert first["ingested"] is True
    assert first["formula_has_more"] is True
    assert first["formula_evidence"] == []
    claim_count = len([n for n in graph.state()["nodes"] if n["type"] == "Claim"])

    widened = ingest_paper(graph, root_id="papers", path="paged.tex",
                           max_formula_candidates=2, formula_offset=0)
    assert widened["ingested"] is True
    assert len(widened["formula_evidence"]) == 2
    assert len([n for n in graph.state()["nodes"] if n["type"] == "Claim"]) == claim_count

    overlap = ingest_paper(graph, root_id="papers", path="paged.tex",
                           max_formula_candidates=2, formula_offset=1)
    assert len(overlap["formula_evidence"]) == 2
    all_evidence = [n for n in graph.state()["nodes"]
                    if n["type"] == "Evidence" and n.get("evidence_type") == "sourced_formula_candidate"]
    assert len(all_evidence) == 3
    assert len({n["candidate_id"] for n in all_evidence}) == 3

    before = len(graph.state()["events"])
    replay = ingest_paper(graph, root_id="papers", path="paged.tex",
                          max_formula_candidates=2, formula_offset=1)
    assert replay["duplicate"] is True
    assert len(graph.state()["events"]) == before
