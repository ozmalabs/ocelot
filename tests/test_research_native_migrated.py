from __future__ import annotations

from scripts.ocelot_research import ResearchGraph
from scripts.ocelot_research_native import ENGINE, project_research_graph


def test_native_projection_preserves_nodes_edges_attrs_and_mapping(tmp_path):
    graph = ResearchGraph.create("Inspect native projection", root=tmp_path,
                                 investigation_id="native-test")
    source = graph.record("Source", name="paper.md",
                          locator={"path": "paper.md", "sha256": "a" * 64})
    claim = graph.record("Claim", wording="For all x, P(x).", claim_type="theorem",
                         status="unresolved", parsed_assertion=True,
                         interpretation_candidate={"status": "unverified_candidate",
                                                   "candidates": {"quantified_claim": {"kind": "forall"}}})
    graph.link(claim["id"], "cites", source["id"],
               provenance={"kind": "paper_import", "line": 8},
               rationale="Source locator only")

    projected = project_research_graph(graph)
    native = projected["graph"]
    assert len(native["nodes"]) == 3
    assert len(native["edges"]) == 1
    mapped_claim = native["nodes"][projected["node_id_map"][claim["id"]]]
    assert mapped_claim["type"] == "Claim"
    assert mapped_claim["attrs"]["wording"] == claim["wording"]
    assert mapped_claim["attrs"]["interpretation_candidate"] == claim["interpretation_candidate"]
    assert mapped_claim["attrs"]["projection_provenance"]["engine"] == ENGINE
    native_edge = native["edges"][0]
    assert native_edge["type"] == "cites"
    assert native_edge["attrs"]["provenance"]["line"] == 8
    assert native_edge["attrs"]["projection_provenance"]["research_edge_id"] == "edge-000001"


def test_native_query_is_optional_and_read_only(tmp_path):
    graph = ResearchGraph.create("Read-only query", root=tmp_path,
                                 investigation_id="native-query-test")
    before = graph.state()
    projected = project_research_graph(graph, query={"type": "Lit", "value": 17})
    assert projected["query_result"] == 17
    assert projected["engine_provenance"]["engine"] == ENGINE
    assert graph.state() == before


def test_nodes_of_type_query_returns_typed_serializable_native_ids(tmp_path):
    graph = ResearchGraph.create("Query projected claims", root=tmp_path,
                                 investigation_id="native-nodes-query-test")
    claim = graph.record("Claim", wording="A claim", claim_type="hypothesis",
                         status="open", nested={"source": ["paper", 1]})
    projected = project_research_graph(
        graph, query={"type": "NodesOfType", "node_type": "Claim"})
    found = projected["query_result"]
    assert found == [{"kind": "NodeID",
                      "value": projected["node_id_map"][claim["id"]],
                      "node_type": "Claim"}]
    # The output is suitable for service JSON and the stored nested fields
    # retain their original JSON structure.
    import json
    json.dumps(projected)
    # graph_to_dict uses the substrate's tagged wire encoding for list values.
    from substrate_rs import Substrate
    reloaded = Substrate()
    reloaded.graph_from_dict(projected["graph"])
    node = reloaded.node(reloaded.nodes("Claim")[0])
    assert node["attrs"]["nested"] == {"source": ["paper", 1]}
