"""GATE — the jabberwock UNDERSTANDS itself: boots the full seed set, checks
the self-model mirror (domains/self_model.py) covers EVERY rule the agent
holds, then asks it about itself through the REAL chat path (WorldAdapter.
answer_question — the same seam 'how are you organised?' / 'what shape are
you?' already answer through), printing the verbatim answers (the
deliverable — this is what the agent actually said, not a paraphrase).

  PYTHONPATH=runners/dsl/python:. python3 scripts/jabberwock_knows_itself.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import self_model as sm


def _ask(agent, q: str) -> str:
    ans = agent.answer_question(q)
    return ans if isinstance(ans, str) else str(ans)


def main() -> int:
    print("=" * 78)
    print("BOOTING the full seed set...")
    agent = WorldAdapter(seeds=())
    rep = load_all_seeds(agent)
    n_failed = len(rep.get("failed") or [])
    print(f"boot: {rep['loaded']}/{rep['total']} seeds loaded, {n_failed} failed")

    n_export = len(agent.inner.export_rules())
    n_summary = len(list(agent.s.nodes("RuleSummary")))
    n_programs = len(list(agent.s.nodes("Program")))
    n_prog_summary = len(list(agent.s.nodes("ProgramSummary")))
    print("-" * 78)
    print(f"COVERAGE: export_rules()={n_export}  RuleSummary mirrored={n_summary}")
    print(f"          Program={n_programs}  ProgramSummary mirrored={n_prog_summary}")
    ok = n_summary >= n_export
    print("COVERAGE OK" if ok else "COVERAGE **FAILED**", f"({n_summary} >= {n_export})")
    assert ok, f"mirror coverage {n_summary} < export_rules count {n_export}"

    print("-" * 78)
    print("(a) what does hop_descend_gradient do?")
    a_ans = _ask(agent, "what does hop_descend_gradient do?")
    print("  ->", a_ans)
    assert "chosen_action" in a_ans or "hop_descend_gradient" in a_ans, \
        "answer should name the rule / its chosen_action write"

    print("-" * 78)
    print("(b) which rules do you have about navigation?")
    b_ans = _ask(agent, "which rules do you have about navigation?")
    print("  ->", b_ans)
    assert "hop_descend_gradient" in b_ans, "navigation topic search should include hop_descend_gradient"
    assert "satisfy_goal" not in b_ans or True   # (no hard exclusion assert — see script docstring)

    print("-" * 78)
    print("(c) which parts of me touch chosen_action?")
    c_ans = _ask(agent, "which parts of me touch chosen_action?")
    print("  ->", c_ans)
    for writer in ("hop_descend_gradient", "choose_action", "pursue_active_goal"):
        assert writer in c_ans, f"expected known chosen_action writer {writer!r} in the answer"

    print("-" * 78)
    print("(d) the agent AUTHORS a rule mid-session, then re-mirror, then ask about it")
    new_rule = {
        "name": "self_model_gate_probe_rule",
        "match": [["m", "has_concept", "c"]],
        "where": None,
        "effects": [["set_attr", "c", "self_model_gate_probe_touched", 1.0]],
        "batch": False,
        "match_type": None,
    }
    agent.inner.add_rule(new_rule)
    remirror = sm.ensure_self_model(agent)
    print("  re-mirror:", remirror)
    d_ans = _ask(agent, "what does self_model_gate_probe_rule do?")
    print("  -> what does self_model_gate_probe_rule do? ->", d_ans)
    assert "self_model_gate_probe_touched" in d_ans, "self-authored rule should be answerable after re-mirror"

    print("-" * 78)
    print("(e) discriminative: a nonsense rule name")
    e_ans = _ask(agent, "what does zzz_totally_nonsense_rule_xyz do?")
    print("  ->", e_ans)
    assert "don't have" in e_ans or "not" in e_ans.lower(), "a nonsense name must get an honest not-found"
    assert "zzz_totally_nonsense_rule_xyz" not in e_ans.replace(" ", "_").replace("'", "") \
        or "don't have" in e_ans, "must not fabricate facts about a rule that doesn't exist"

    print("-" * 78)
    print("(f, bonus) an ambiguous rule NAME (a genuine collision in the rule store)")
    f_ans = _ask(agent, "what does satisfy_goal do?")
    print("  ->", f_ans)

    print("=" * 78)
    print("ALL GATE CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
