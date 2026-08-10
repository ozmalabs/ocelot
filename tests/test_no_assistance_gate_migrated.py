"""Wave 6 EXIT GATE — THE GRADUATION GATE: the full improvement loop closes
with ZERO hosted-LLM assistance and ZERO human framing beyond the sanctioned
NL surface (converse turns + the UI flag button + the daemon's own tick
hooks). This wrapper runs `scripts/no_assistance_gate.py`'s importable
`run_gate` (small N: cycle A cue family + cycle B ablation family + the
adoption-safety negative control) and asserts its summary — the script is the
proof; this test keeps it standing.

Also asserted here, cheaply (no boot): the source-discipline audit is real
(it actually flags a forbidden call) and currently clean on the shipped gate.
"""
from __future__ import annotations

import ast
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import no_assistance_gate as nag                       # noqa: E402

_GUARDED_SEEDS = (
    os.path.join(ROOT, "seeds", "experiment_conclusions.json"),   # close_experiment_loop teach()
    os.path.join(ROOT, "seeds", "comprehend_instruction.json"),   # cue adoption teach()
)


@pytest.fixture(autouse=True)
def _guard_seed_files():
    """Snapshot/restore the seeds the adoption path writes (belt-and-braces on
    top of conftest's session-wide persist guard — the gate is also runnable
    outside pytest, where its own main() applies the same guard)."""
    before = {}
    for p in _GUARDED_SEEDS:
        before[p] = open(p).read() if os.path.exists(p) else None
    try:
        yield
    finally:
        for p, content in before.items():
            if content is not None:
                with open(p, "w") as f:
                    f.write(content)
            elif os.path.exists(p):
                os.unlink(p)


@pytest.fixture(autouse=True)
def _restore_no_llm_env():
    """run_gate sets OZMA_NO_LLM=1; don't leak it into the rest of the bench."""
    before = os.environ.get("OZMA_NO_LLM")
    try:
        yield
    finally:
        if before is None:
            os.environ.pop("OZMA_NO_LLM", None)
        else:
            os.environ["OZMA_NO_LLM"] = before


# --- the audit is real: it flags a forbidden call, and the shipped gate is clean ---

def test_source_discipline_audit_is_real_and_clean():
    assert nag.audit_source_discipline() == [], \
        "the shipped gate script must be clean of forbidden calls"
    # the audit genuinely detects: a synthetic module with a forbidden call
    probe = ast.parse("x.mint_experiment(1)\nteach(a, 'T', {})\nconverse('hi')")
    hits = []
    for node in ast.walk(probe):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            if name in nag._FORBIDDEN_CALLS:
                hits.append(name)
    assert sorted(hits) == ["mint_experiment", "teach"], \
        "the forbidden-call set must catch both attribute and plain calls (and not converse)"


# --- THE GRADUATION GATE ---------------------------------------------------------

def test_no_assistance_gate_closes_two_cycles_and_denies_the_regressor(tmp_path):
    audit = nag.run_gate(tmp_path / "gate", budget_s=420.0, keep_runs=True)
    summary = audit["summary"]

    failed = [c["label"] for c in summary["checks"] if not c["ok"]]
    assert summary["pass"], f"gate failed checks: {failed}"

    # N >= 2 full cycles closed unassisted, one per variation family
    assert summary["cycles_closed"] >= 2
    families = {c["family"] for c in audit["cycles"] if c.get("adoption_id") is not None}
    assert {"cue_set_edit", "reply_ablation"} <= families

    # every closed cycle's audit record is complete — the deliverable trail
    for c in audit["cycles"]:
        for key in ("concern_id", "promoted_by", "experiment_id", "variation_op",
                    "child_result", "judge_outcome", "adoption_id",
                    "before_reply", "after_reply"):
            assert c.get(key) not in (None, "", {}), (c["cycle"], key, c.get(key))
        assert c["judge_outcome"] == "supported"
        assert int(c["child_result"].get("regressions") or 0) == 0
        assert (c["before_reply"] or "").strip() != (c["after_reply"] or "").strip()

    # THE NEGATIVE CONTROL: supported-but-regressing judged supported, NOT adopted
    control = audit["negative_control"]
    assert control["judge_outcome"] == "supported"
    assert int(control["child_result"]["regressions"]) >= 1
    assert int(control["child_result"]["score"]) > 0
    assert control["adopt_denied"] is True and control.get("adoption_id") is None
    assert control["adopt_denied_reason"]
    assert "blocked from adoption" in (control.get("status_reply") or "")

    # the audit trail was written next to the runs
    audit_path = tmp_path / "gate" / "audit.json"
    assert audit_path.exists()
    on_disk = json.load(open(audit_path))
    assert on_disk["summary"]["pass"] is True
    assert on_disk["no_llm"] is True
