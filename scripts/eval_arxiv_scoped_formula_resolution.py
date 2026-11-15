"""End-to-end scoped formula-resolution evaluation on arXiv:2606.13224.

This creates an isolated research session, ingests the locally stored arXiv
TeX source through the existing service, and resolves the paper's
``m,n\\in\\NN`` example against the imported paper frame. It reports source
evidence and explicitly checks that the natural-number lower bound remains
unresolved without a researcher-supplied convention.

Run from the repository root with:

    PYTHONPATH=runners/dsl/python:. python3 scripts/eval_arxiv_scoped_formula_resolution.py
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from scripts.ocelot_research import ResearchGraph, ResearchError
from scripts.ocelot_research_service import ResearchService


ROOT = Path(__file__).resolve().parents[1]
PAPER_ID = "2606.13224"
PAPER_RELATIVE_PATH = f"{PAPER_ID}/main.tex"
PAPER_ROOT = ROOT / "data" / "arxiv"
FORMULA = r"m,n\in\NN"


def _line_excerpt(source: str, line: int) -> dict[str, Any]:
    lines = source.splitlines()
    return {"line": line, "text": lines[line - 1] if 1 <= line <= len(lines) else None}


def evaluate() -> dict[str, Any]:
    source_path = PAPER_ROOT / PAPER_RELATIVE_PATH
    if not source_path.is_file():
        raise FileNotFoundError(f"arXiv source is not available: {source_path}")
    source_text = source_path.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="ocelot-arxiv-formula-eval-") as workspace:
        service = ResearchService(workspace)
        initial = service.call("init", {
            "question": f"Evaluate source-scoped notation in arXiv:{PAPER_ID}",
            "mode": "exploratory",
            "roots": [{
                "root_id": "arxiv",
                "path": str(PAPER_ROOT),
                "repository": f"arXiv:{PAPER_ID}",
                "files": {PAPER_RELATIVE_PATH: "selected TeX source"},
            }],
        })
        session_id = initial["investigation_id"]
        preview = service.call("paper_preview", {
            "session_id": session_id,
            "root_id": "arxiv",
            "path": PAPER_RELATIVE_PATH,
            "max_formula_candidates": 16,
        })

        matching_formula = next((item for item in preview["formula_candidates"]
                                 if item["formula"].replace(" ", "") == FORMULA), None)
        if matching_formula is None:
            raise RuntimeError(
                f"formula {FORMULA!r} was not extracted from the selected source")
        macro_record = next((item for item in preview["mathematical_context"]["records"]
                             if item.get("kind") == "symbol"
                             and item.get("name") == r"\NN"), None)
        if macro_record is None:
            raise RuntimeError(r"the source declaration for \NN was not extracted")

        ingested = service.call("paper_ingest", {
            "session_id": session_id,
            "root_id": "arxiv",
            "path": PAPER_RELATIVE_PATH,
            "max_formula_candidates": 16,
        })
        frame_id = ingested.get("frame_id")
        if not frame_id:
            raise RuntimeError("paper ingestion did not return its source scope frame")

        state = ResearchGraph.load(session_id, root=workspace).state()
        node_by_id = {node["id"]: node for node in state["nodes"]}
        formula_node = next((node for node in ingested["formula_evidence"]
                             if node.get("wording", "").replace(" ", "")
                             == FORMULA), None)
        if formula_node is None:
            raise RuntimeError("the extracted formula was not ingested as evidence")
        local_scopes = [edge["tgt"] for edge in state["edges"]
                        if edge.get("src") == formula_node["id"]
                        and edge.get("type") == "scoped_by"
                        and node_by_id.get(edge.get("tgt"), {}).get("scope_kind")
                        == "local_source_context"]
        if len(local_scopes) != 1:
            raise RuntimeError(
                f"expected one exact local formula scope, found {len(local_scopes)}")
        formula_scope_id = local_scopes[0]

        resolution = service.call("formula_resolve", {
            "session_id": session_id,
            "scope_id": formula_scope_id,
            "formula": matching_formula["formula"],
        })
        model_without_convention = service.call("formula_model", {
            "session_id": session_id,
            "claim_id": formula_node["id"],
            "formula": matching_formula["formula"],
            "context_scope_id": formula_scope_id,
            "reviewer": "evaluation-script",
            "review_note": "Expected refusal: no convention for the minimum natural number was supplied.",
        })
        macro_node = next((node for node in ingested["mathematical_context"]
                           if node.get("name") == r"\NN"), None)

        def graph_links(node_id: str | None) -> list[dict[str, Any]]:
            if not node_id:
                return []
            rows = []
            for edge in state["edges"]:
                if edge["src"] == node_id or edge["tgt"] == node_id:
                    other_id = edge["tgt"] if edge["src"] == node_id else edge["src"]
                    rows.append({"type": edge["type"], "direction":
                                 "out" if edge["src"] == node_id else "in",
                                 "node_id": other_id,
                                 "node_type": node_by_id.get(other_id, {}).get("type")})
            return rows

        def execution_summary(result: dict[str, Any]) -> dict[str, Any]:
            trace = result.get("trace") or {}
            return {"status": result.get("status"), "value": result.get("value"),
                    "target": result.get("target"), "trace_status": trace.get("status"),
                    "trace_paths": trace.get("paths", []),
                    "truth_assessed": result.get("truth_assessed")}

        candidate_runs = []
        if model_without_convention.get("status") == "unsupported":
            for natural_minimum, positive_env, negative_env in (
                    (0, {"m": 0, "n": 3}, {"m": -1, "n": 3}),
                    (1, {"m": 1, "n": 3}, {"m": 0, "n": 3})):
                candidate = service.call("formula_model", {
                    "session_id": session_id,
                    "claim_id": formula_node["id"],
                    "formula": matching_formula["formula"],
                    "context_scope_id": formula_scope_id,
                    "domain_assumptions": {"natural_minimum": natural_minimum},
                    "reviewer": "evaluation-script",
                    "review_note": (
                        f"Explore the explicit natural-number bound {natural_minimum}; "
                        "this convention is not inferred from the paper source."),
                })
                node_id = candidate["candidate"]["id"]
                try:
                    lean = service.call("check_lean", {"session_id": session_id, "node_id": node_id})
                except ResearchError as exc:
                    lean = {"status": "unavailable", "reason": str(exc)}
                candidate_runs.append({
                    "natural_minimum_assumption": natural_minimum,
                    "candidate_id": node_id,
                    "found_verbatim_in_source_evidence": candidate["found_verbatim_in_claim"],
                    "model_trace_paths": candidate["trace"].get("paths", []),
                    "lean": {"status": lean.get("status"), "version": lean.get("lean_version"),
                             "source_sha256": lean.get("source_sha256"), "reason": lean.get("reason")},
                    "positive_execution": execution_summary(service.call("execute", {
                        "session_id": session_id, "node_id": node_id,
                        "env": positive_env,
                    })),
                    "negative_execution": execution_summary(service.call("execute", {
                        "session_id": session_id, "node_id": node_id,
                        "env": negative_env,
                    })),
                })

        return {
            "evaluation": "real_arxiv_scoped_formula_resolution",
            "arxiv_id": PAPER_ID,
            "paper_title": "Bott-Chern and Aeppli Homotopy",
            "session_id": session_id,
            "source": {
                "path": str(source_path),
                "sha256": preview["sha256"],
                "macro_declaration": {
                    "node": macro_node,
                    "line_excerpt": _line_excerpt(source_text,
                                                   macro_record["locator"]["start_line"]),
                    "graph_links": graph_links(macro_node["id"] if macro_node else None),
                },
                "formula_evidence": {
                    "extracted_candidate": matching_formula,
                    "node": formula_node,
                    "line_excerpt": _line_excerpt(source_text,
                                                   matching_formula["locator"]["start_line"]),
                    "graph_links": graph_links(formula_node["id"] if formula_node else None),
                },
            },
            "paper_scope": node_by_id.get(frame_id),
            "formula_local_scope": node_by_id.get(formula_scope_id),
            "resolution": resolution,
            "natural_minimum_check": {
                "status_without_explicit_convention": model_without_convention["status"],
                "reason": model_without_convention.get("reason"),
                "natural_minimum_inferred": None,
                "interpretation": (
                    "The source declares \\NN as \\mathbb{N}, but does not state here "
                    "whether zero is included. Translation therefore requires an explicit "
                    "minimum of 0 or 1."
                ),
            },
            "explicit_convention_candidate_runs": candidate_runs,
            "truth_assessed": False,
            "limitations": [
                "Source declarations are recorded as evidence, not verified mathematical semantics.",
                "The native formula resolver reports notation context; it does not decide whether 0 belongs to the naturals.",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        help="write the JSON evaluation report to this path")
    args = parser.parse_args()
    report = evaluate()
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
