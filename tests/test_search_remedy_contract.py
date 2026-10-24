"""P23.04 evidence-linked remedy and fixed-budget checks."""
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "docs/research/engine_substrate/COGNITION_SEARCH_REMEDY_DECISION.md"
FEASIBILITY = ROOT / "evaluation/process_mastery/results/"
FUNNEL = FEASIBILITY / "p23_search_funnel_audit_20261024.json"


def test_each_remedy_names_a_measured_barrier():
    text = DECISION.read_text()
    rows = [line for line in text.splitlines() if line.startswith("| ")
            and "p22_training_panel_registered_root_" in line]
    assert len(rows) == 4
    assert all("Measurement" in row or "15,000/15,000" in row
               or "20,000 new attempts" in row or "19,998 of 20,000" in row
               or "three novel nonidentity effects" in row for row in rows)
    assert "P23 funnel artifact" in text
    assert "no larger search ceiling" in text


def test_no_identity_or_held_effect_promoted():
    text = DECISION.read_text()
    assert "Identity, active, adopted, and duplicate effects remain ineligible." in text
    feasibility = json.loads((FEASIBILITY / "p23_search_feasibility_audit_20261024.json").read_text())
    g2 = feasibility["d4"]["generation_two"]
    known = {tuple(effect) for effect in g2["active_effects"] + g2["adopted_effects"]}
    assert tuple(g2["identity_effect"]) not in g2["remaining_novel_nonidentity_effects"]
    assert all(tuple(effect) not in known
               for effect in g2["remaining_novel_nonidentity_effects"])
    funnel = json.loads(FUNNEL.read_text())
    branch = next(row for row in funnel["branch_records"]
        if row["artifact_path"].endswith(
            "p22_training_panel_registered_root_d4_g2_0992_0993_ticks120_depth3.json"))
    assert branch["funnel"]["new_legal_unique_effects"] == 0


def test_trial_headroom_within_total_ceiling():
    text = DECISION.read_text()
    rows = dict((label, int(per.replace(",", "")) * int(targets.replace(",", "")))
        for label, per, targets in re.findall(
            r"\| (Ordinary discovery search|Independent-goal transfer reserve) \| ([0-9,]+) \| ([0-9,]+) \| [0-9,]+ \|",
            text))
    assert rows["Ordinary discovery search"] == 40_000
    assert rows["Independent-goal transfer reserve"] == 20_000
    new_work = sum(rows.values())
    inherited = 20_000
    total_ceiling = 120_000
    assert inherited + new_work == 80_000 <= total_ceiling
    funnel = json.loads(FUNNEL.read_text())
    branch = next(row for row in funnel["branch_records"]
        if row["artifact_path"].endswith(
            "p22_training_panel_registered_root_loopover_g1_0980_0983_ticks120_depth3.json"))
    assert branch["inherited_graph_attempts"] == inherited
    assert branch["global_attempt_ceiling"] == total_ceiling
    assert branch["global_attempt_headroom"] > 0
    assert branch["request_attempt_headroom_total"] == 0
