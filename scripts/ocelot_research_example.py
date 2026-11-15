"""Construct and export a sourced, bounded Boolean-extension investigation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scripts.ocelot_research_service import ResearchService


def make_example(workspace: Path, ge: Path) -> dict:
    svc = ResearchService(workspace)
    root = {"root_id": "ge", "path": str(ge.resolve()), "files": [
        "notes/GRAPHIC_EQUALISATION_FOR_LLMS.md",
        "notes/experiments/ge_oracle_elimination/PAPER_CLAIM_EVIDENCE.md"]}
    state = svc.call("init", {"question": "Does a total single-valued Boolean extension make an arbitrary residual easy to solve?", "mode": "deductive", "roots": [root]})
    sid = state["investigation_id"]
    def record(kind, **fields):
        return svc.call("record", {"session_id": sid, "kind": kind, "fields": fields})
    def link(src, relation, tgt):
        svc.call("link", {"session_id": sid, "src": src["id"], "relation": relation, "tgt": tgt["id"], "fields": {"provenance": "researcher interpretation of cited ledger"}})
    frame = record("Frame", boundary="finite Boolean extension and residual CNF", state="input and fresh output variables", rules="supplied defining relation", grammar="total single-valued extension over declared inputs", possibilities="projection and reconstruction; residual remains", realisation="a particular projected instance", residual="arbitrary residual is not solved by structure alone", cost="discovery and solving costs are not bounded by the bijection", grounding="Boolean formulae", test="inspect supplied hard-residual reduction and finite checks", empirical_exemption_reason="deductive comparison; finite checks are illustrative")
    claim = record("Claim", wording="A total single-valued extension makes an arbitrary residual easy to solve", scope="arbitrary residual CNF", claim_type="hypothesis", author="example researcher", status="contradicted", limitations="The cited construction challenges this broad claim; no universal hardness or complexity separation is established.")
    alternative = record("Alternative", wording="The extension preserves projection while a supplied residual can remain arbitrary.", scope="the stated construction; independent review remains open")
    pack = svc.call("context", {"session_id": sid, "query": "supplied XOR-chain arbitrary residual projection", "limit": 20})
    matches = [x for x in pack["results"] if x["citation"]["path"].endswith("PAPER_CLAIM_EVIDENCE.md")]
    if not matches:
        raise RuntimeError("selected GE claim-evidence ledger unavailable")
    source = record("Source", title="GE paper claim and evidence ledger", locator=matches[0]["citation"])
    evidence = record("Evidence", wording="The ledger describes a supplied XOR-chain construction coexisting with an arbitrary 3-CNF residual; finite witnesses are distinct from its reduction.", limitations="The entry does not claim that GE solves the residual, an unconditional lower bound, or novelty.")
    link(claim, "scoped_by", frame)
    link(alternative, "scoped_by", frame)
    link(evidence, "cites", source)
    link(evidence, "opposes", claim)
    link(evidence, "supports", alternative)
    record("Decision", wording="Review the cited primary construction and an independent specialist assessment before extending the claim.", status="open")
    return svc.call("export", {"session_id": sid})


def make_historical(workspace: Path, ocelot: Path) -> dict:
    """Import an old prereg/results pair without certifying the historical run."""
    folder = "docs/research/engine_substrate/"
    prereg = folder + "SUBSTRATE_NATURALPROOFS_RUNG_ENTRY_PANEL_V1_PREREG_20260927.md"
    results = folder + "SUBSTRATE_NATURALPROOFS_RUNG_ENTRY_PANEL_V1_RESULTS_20260927.md"
    svc = ResearchService(workspace)
    sid = svc.call("init", {"question": "Did the recorded NaturalProofs reading panel enter the reflective mint path after startup?", "mode": "exploratory", "roots": [{"root_id": "ocelot", "path": str(ocelot.resolve()), "files": [prereg, results]}]})["investigation_id"]
    def record(kind, **fields):
        return svc.call("record", {"session_id": sid, "kind": kind, "fields": fields})
    def link(src, rel, tgt):
        svc.call("link", {"session_id": sid, "src": src["id"], "relation": rel, "tgt": tgt["id"], "fields": {"provenance": "historical results report"}})
    pack = svc.call("context", {"session_id": sid, "query": "NaturalProofs reading panel workers receipt", "limit": 100})
    def locator(path):
        return next(r["citation"] for r in pack["results"] if r["citation"]["path"] == path)
    prior_locator = locator(prereg)
    prior_source = record("Source", title="Historical preregistration", locator=prior_locator)
    result_source = record("Source", title="Historical results", locator=locator(results))
    protocol = record("Protocol", title="Historical entry panel preregistration", revision=prior_locator.get("revision") or "unavailable", immutable=bool(prior_locator.get("revision")), prereg_git={"root_id": "ocelot", "path": prereg, "commit_oid": prior_locator.get("revision")}, limitations="The current commit can identify content; this helper did not observe historical registration or execution.")
    run = record("Run", receipt_status="manual", title="Historical two-worker panel", limitations="Receipt is a report of historical artifacts, not a captured run.")
    observation = record("Observation", wording="The results report 0/63 post-startup tasks with a new concern receipt in each worker.", limitations="The report says answer correctness and proof quality were not assessed; its inference is limited to the selected panel and route.")
    claim = record("Claim", wording="The audited reading route produced no post-startup concern receipt in the reported sample.", scope="two workers, 63 post-startup tasks each", claim_type="empirical_observation", author="historical results report", status="open", limitations="No independent replay or historical engine verification by this helper.")
    link(protocol, "tests", run)
    link(run, "produced", observation)
    link(observation, "cites", result_source)
    link(claim, "cites", prior_source)
    link(observation, "supports", claim)
    return svc.call("export", {"session_id": sid})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", required=True)
    p.add_argument("--ge-root")
    p.add_argument("--ocelot-root")
    p.add_argument("--historical", action="store_true")
    a = p.parse_args()
    if a.historical:
        if not a.ocelot_root: p.error("--historical requires --ocelot-root")
        result = make_historical(Path(a.workspace), Path(a.ocelot_root))
    else:
        if not a.ge_root: p.error("--ge-root is required")
        result = make_example(Path(a.workspace), Path(a.ge_root))
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
