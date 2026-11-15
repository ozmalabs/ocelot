"""Bounded DisCoPy/native-substrate composition and identity comparison.

This is an interoperability probe, not a claim that a general research graph
is a category. It maps three named objects to native graph nodes and two named
arrows to typed edges. A native rewrite rule materializes the one composable
path. DisCoPy independently constructs the corresponding monoidal diagram.
The comparison checks boundary/type labels and source-ID preservation only;
it does not establish a semantics-preserving functor or equality of arbitrary
arrows. Both optional dependencies are imported lazily.
"""
from __future__ import annotations

from importlib import metadata
from typing import Any


class OptionalDependencyUnavailable(RuntimeError):
    pass


SOURCE_IDS = {
    "object_x": "paper:object:X",
    "object_y": "paper:object:Y",
    "object_z": "paper:object:Z",
    "arrow_f": "paper:arrow:f",
    "arrow_g": "paper:arrow:g",
    "identity_x": "paper:identity:id_X",
}


def _versions() -> dict[str, str]:
    versions = {}
    for package in ("discopy", "substrate-rs"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "installed, version metadata unavailable"
    return versions


def run_experiment() -> dict[str, Any]:
    """Construct and compare one typed chain and one left identity law."""
    try:
        from discopy import monoidal as monoidal
        from substrate_rs import Substrate
    except ImportError as exc:
        raise OptionalDependencyUnavailable(
            "categorical interoperability requires optional `discopy` and `substrate_rs`"
        ) from exc

    # DisCoPy's monoidal diagrams encode typed boundaries and composition.
    X, Y, Z = (monoidal.Ty(name) for name in ("X", "Y", "Z"))
    f_box = monoidal.Box("f", X, Y)
    g_box = monoidal.Box("g", Y, Z)
    chain = f_box >> g_box
    identity_law = monoidal.Id(X) >> f_box

    # The substrate arm stores object/arrow source IDs on its native graph,
    # then fires an explicit path-composition rule to create g_after_f.
    sub = Substrate()
    objects = {
        "X": sub.add_node("CategoryObject", {"source_id": SOURCE_IDS["object_x"], "name": "X"}),
        "Y": sub.add_node("CategoryObject", {"source_id": SOURCE_IDS["object_y"], "name": "Y"}),
        "Z": sub.add_node("CategoryObject", {"source_id": SOURCE_IDS["object_z"], "name": "Z"}),
    }
    # Register only edge shapes used by this probe. This is a local grammar,
    # not a universal categorical schema.
    for edge_type in ("f", "g", "g_after_f", "id_X", "id_then_f"):
        for src_type in ("CategoryObject",):
            for tgt_type in ("CategoryObject",):
                sub._inner.add_production({
                    "src": {"type": src_type, "var": "src"},
                    "edge_type": edge_type,
                    "tgt": {"type": tgt_type, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "categorical_interop_probe_v1",
                })
    sub.add_edge(objects["X"], "f", objects["Y"], {"source_id": SOURCE_IDS["arrow_f"]})
    sub.add_edge(objects["Y"], "g", objects["Z"], {"source_id": SOURCE_IDS["arrow_g"]})
    sub.add_edge(objects["X"], "id_X", objects["X"], {"source_id": SOURCE_IDS["identity_x"]})
    sub._inner.add_rule({
        "name": "compose_f_then_g",
        "match": [["x", "f", "y"], ["y", "g", "z"]],
        "where": None,
        "effects": [["add_edge", "x", "g_after_f", "z",
                     {"source_id": "derived:paper:arrow:g_after_f"}]],
    })
    sub._inner.add_rule({
        "name": "left_identity_on_f",
        "match": [["x", "id_X", "x"], ["x", "f", "y"]],
        "where": None,
        "effects": [["add_edge", "x", "id_then_f", "y",
                     {"source_id": "derived:paper:identity_X_then_f"}]],
    })
    sub._inner.run_rules()
    native = sub.graph_to_dict()

    node_ids = {node["attrs"].get("source_id"): node["id"]
                for node in native["nodes"]}
    edges = [{"type": edge["type"], "src": edge["src"], "tgt": edge["tgt"],
              "source_id": edge["attrs"].get("source_id")}
             for edge in native["edges"]]
    retained_source_ids = set(node_ids) | {edge["source_id"] for edge in edges
                                          if edge["source_id"] is not None}
    composed = [edge for edge in edges if edge["type"] == "g_after_f"]
    identity_composed = [edge for edge in edges if edge["type"] == "id_then_f"]
    if len(composed) != 1 or len(identity_composed) != 1:
        raise RuntimeError("native rewrite did not materialize exactly one chain and identity witness")

    return {
        "status": "completed",
        "versions": _versions(),
        "scope": "one X→Y→Z chain and one left-identity case",
        "discopy": {
            "chain_dom": str(chain.dom), "chain_cod": str(chain.cod),
            "chain_boxes": [box.name for box in chain.boxes],
            "identity_law_equal_to_f": identity_law == f_box,
        },
        "substrate": {
            "object_node_ids_by_source_id": node_ids,
            "composed_path": composed,
            "identity_path_witness": identity_composed,
            "native_node_count": len(native["nodes"]),
            "native_edge_count": len(native["edges"]),
        },
        "source_ids": dict(SOURCE_IDS),
        "comparison": {
            "boundaries_agree": str(chain.dom) == "X" and str(chain.cod) == "Z",
            "preserved_source_ids": sorted(retained_source_ids & set(SOURCE_IDS.values())),
            "all_source_ids_preserved": set(SOURCE_IDS.values()).issubset(retained_source_ids),
            "equivalence_claimed": False,
            "limitations": [
                "The substrate composition is a graph rewrite over a selected edge path.",
                "The identity path is a witness edge; it does not quotient arrows by equality.",
                "DisCoPy diagrams and substrate edges have not been connected by a proven functor.",
                "No source paper semantics, associativity law, or right-identity law is checked.",
            ],
        },
    }


def main() -> int:
    import json
    try:
        result = run_experiment()
    except OptionalDependencyUnavailable as exc:
        result = {"status": "skipped_optional_dependencies", "reason": str(exc),
                  "scope": "one X→Y→Z chain and one left-identity case",
                  "source_ids": dict(SOURCE_IDS), "equivalence_claimed": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
