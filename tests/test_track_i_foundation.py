import json

from evaluation.process_mastery import generators as gen
from evaluation.process_mastery.scorecard import write_scorecard
from evaluation.process_mastery.harness import Agent


def test_pmb_generators_are_seeded_and_splits_disjoint():
    assert gen.split_seed("train", 0) == 0
    assert gen.split_seed("heldout", 0) == 1_000_000
    assert gen.loopover_scramble(3, 42) == gen.loopover_scramble(3, 42)
    assert gen.d4_task(42) == gen.d4_task(42)
    assert gen.blicket_task(42) == gen.blicket_task(42)
    assert set(gen.SPLITS["train"]).isdisjoint(gen.SPLITS["heldout"])


def test_pmb_scorecard_is_stable_and_keeps_raw_records(tmp_path):
    out = tmp_path / "scorecard.json"
    write_scorecard(out, metadata={"profile": "baseline"}, records=[
        {"family": "c", "seed": 3, "status": "NOT_RUN"},
        {"family": "a", "seed": 2, "status": "NOT_RUN"},
    ])
    data = json.loads(out.read_text())
    assert data["schema"] == "pmb-scorecard-v1"
    assert [r["family"] for r in data["records"]] == ["a", "c"]
    assert all(r["status"] == "NOT_RUN" for r in data["records"])


def test_loopover_3x3_schema_views_are_graph_minted_and_effect_distinct():
    agent = Agent(view_enabled=True)
    agent.add_loopover_domain(3)
    agent.run(max_ticks=20)
    schemas = agent.schemas("loopover_3")
    assert len(schemas) == 12
    assert all(agent.attrs(s).get("fingerprint_checked") == 1 for s in schemas)
    assert len({repr(agent.attrs(s).get("fingerprint")) for s in schemas}) == 12
