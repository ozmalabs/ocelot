from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs/research/engine_substrate"


def _read(name: str) -> str:
    return (DOCS / name).read_text()


def test_p5_docs_define_project_generated_inputs_not_external_production_inputs():
    requirements = _read("P5_ATTESTED_RESULT_REQUIREMENTS.md")
    handoff = _read("P5_PRODUCTION_INPUT_HANDOFF.md")
    plan = _read("P5_BLOCKER_COMPLETION_PLAN.md")

    assert "There are no externally supplied “production inputs.”" in requirements
    assert "Project-generated controlled-run input" in requirements
    assert "Fabricated evidence" in requirements
    assert "There are no externally supplied production inputs and no external task provider." in handoff
    assert "The absence of an external task provider is not a stop condition" in plan
    assert "not a human-supplied production-input checklist" in handoff
    for document in (requirements, handoff, plan):
        assert "external task provider is required" not in document
        assert "human-supplied production-input checklist" not in document.replace("not a human-supplied production-input checklist", "")


def test_p5_docs_disclose_all_time_seed_bindings_and_real_execution_gates():
    requirements = _read("P5_ATTESTED_RESULT_REQUIREMENTS.md")
    handoff = _read("P5_PRODUCTION_INPUT_HANDOFF.md")
    plan = _read("P5_BLOCKER_COMPLETION_PLAN.md")

    for document in (requirements, handoff, plan):
        assert "timing_record_digest" in document
        assert "input_seed_digest" in document
        assert "input_digest" in document

    for gate in (
        "signed Confidential Space",
        "KMS",
        "supervisor",
        "signed receipts",
        "result seal",
    ):
        assert gate.lower() in requirements.lower()
        assert gate.lower() in handoff.lower() or gate.lower() in plan.lower()

    assert "Generation is not execution evidence" in handoff
    assert "A failure of any item is a no-go" in requirements
