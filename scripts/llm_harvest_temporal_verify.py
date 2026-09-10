"""Block 334000 — VERIFY the temporal-trust path for the reaped `qwen3` source.

Re-authoring domains/communication_concepts.py (the JSON->graph installer,
removed with the python-core purge) materializes the qwen3 concept's `timeline`
as SourceEvent graph nodes (has_event) grounded (built_from) in the concepts each
calibration event grounds in. The already-live reader source_provenance.context_
for / _compose_trust then DERIVES a time-sliced trust band from those events
instead of the flat held reliability.

This script installs the seed into a FRESH substrate world and checks, with NO
model and NO network (pure graph):
  1. the qwen3 concept gains has_event edges to SourceEvent nodes (the 3
     calibration events materialized);
  2. epistemic_status_for_source(s,'qwen3') is now DERIVED + time-sliced
     (why-string mentions the composed cone), not the flat band;
  3. the composed weight sits BELOW an attested reference (wikipedia);
  4. the net of the calibration events is HONEST: knowledge earned (+1) and
     process control-failed (-1) OFFSET -> the calibrated self-published band,
     time-sliced so an early cutoff (before the events) reads the bare baseline.
Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/llm_harvest_temporal_verify.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

from domains.communication_concepts import install_communication_concepts_seed
from domains import source_provenance as sp


def _find_concept(s, name):
    for cid in s.nodes("Concept"):
        if s.node(cid)["attrs"].get("name") == name:
            return cid
    return None


def main() -> int:
    s = _native.Substrate()
    mt = install_communication_concepts_seed(s)
    assert mt is not None, "install returned None"

    qid = _find_concept(s, "qwen3")
    assert qid is not None, "qwen3 concept not installed"

    # (1) SourceEvent nodes + has_event edges materialized
    evs = list(s.neighbours(qid, "has_event"))
    ev_names = sorted(s.node(e)["attrs"].get("event_id") for e in evs)
    print("has_event -> SourceEvent nodes:", ev_names)
    assert len(evs) == 3, f"expected 3 calibration events, got {len(evs)}"
    # each event grounded (built_from) in >=1 concept
    for e in evs:
        g = list(s.neighbours(e, "built_from"))
        assert g, f"event {s.node(e)['attrs'].get('event_id')} not grounded"

    # (2) epistemic status is now DERIVED + time-sliced (present cutoff = whole cone)
    st_now = sp.epistemic_status_for_source(s, "qwen3")
    print("\nepistemic_status_for_source('qwen3') [present]:")
    print(json.dumps(st_now, indent=1, default=str))
    assert st_now is not None
    why = (st_now.get("why") or "")
    assert "DERIVED" in why and "time-sliced" in why, \
        "expected a DERIVED time-sliced band, got the flat band"

    # (3) below the attested reference (wikipedia)
    st_wiki = sp.epistemic_status_for_source(s, "wikipedia")
    print("\nepistemic_status_for_source('wikipedia'):")
    print(json.dumps(st_wiki, indent=1, default=str))
    w_q = st_now.get("confidence")
    w_w = st_wiki.get("confidence")
    print(f"\nqwen3 weight={w_q}  wikipedia weight={w_w}")
    assert w_q is not None and w_w is not None
    assert w_q < w_w, "qwen3 must sit strictly below the attested reference"

    # (4) HONEST net: knowledge (+1) and process control-failed (-1) OFFSET.
    ctx = sp.context_for(s, "qwen3")
    tr = ctx["trust"]
    print("\ncomposed trust (present):", json.dumps(tr, default=str))
    assert tr["raising_events"] == ["qwen3_calibration_knowledge_isa"]
    assert tr["lowering_events"] == ["qwen3_calibration_process_negate"]
    # net zero -> baseline self_published band, weight at the 0.5 baseline
    assert tr["status"] == "self_published", tr["status"]
    assert abs(tr["weight"] - 0.5) < 1e-9, tr["weight"]

    # (4b) TIME-SLICE: a cutoff BEFORE the 2026-09-04 calibration -> empty cone,
    # bare baseline (no events have entered) — proving it is derived, not flat.
    ctx_early = sp.context_for(s, "qwen3", when="2020-01-01")
    print("composed trust (2020 cutoff):",
          json.dumps(ctx_early["trust"], default=str),
          "| in_cone:", [e["id"] for e in ctx_early["in_cone_events"]])
    assert ctx_early["in_cone_events"] == [], "no calibration events before 2020"

    print("\nALL TEMPORAL-TRUST CHECKS PASSED "
          "(qwen3 band is DERIVED + time-sliced, honest net, below attested).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
