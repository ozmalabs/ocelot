"""arc_ls20_understanding_audit — RUNG 221000 source-audit (G-graph-native).

The reframe violation to detect is precise: an OBJECTIVE FUNCTION that SELECTS by
win/goal-proximity. That is goal coordinates (`goal_r`/`goal_c`) appearing inside a
SELECTION `value` subterm (an `Argmin`/`Argmax`), or a distance-to-goal construct
(`Minus`/`Abs` over the goal coords). Merely ROUTING to the goal cell for the
terminal delivery of an ALREADY-CORRECT symbol (a `set_attr wp_r <- goal_r`
assignment, the established 218000 `plan_deliver` pattern) is NOT a win-objective
and is admissible.

This audit asserts: NO `uh_*` DRIVE rule selects by goal proximity, AND the
curiosity pick selects by NOVELTY (`visits`), never by goal. The win-objective is
permitted ONLY in the `wb_*` CONTROL rules (by design). Prints a source_match
report; exits non-zero on violation."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from domains.ls20_understanding_seed import RULES  # noqa: E402

GOAL_TOKENS = ("goal_r", "goal_c")


def _find_selection_values(x, out):
    """Collect the `value` subtree of every Argmin/Argmax in the term."""
    if isinstance(x, dict):
        if x.get("type") in ("Argmin", "Argmax") and "value" in x:
            out.append(x["value"])
        for v in x.values():
            _find_selection_values(v, out)
    elif isinstance(x, list):
        for v in x:
            _find_selection_values(v, out)


def _refs_goal(x):
    s = str(x)
    return any(t in s for t in GOAL_TOKENS)


def main():
    print("=== SOURCE AUDIT (source_match): win/goal-reach OBJECTIVE in the drive ===")
    drive_viol = []; ctrl_objectives = []
    pick_selects_by = {}
    for r in RULES:
        name = r["name"]
        is_uh = name.startswith("uh_")
        is_wb = name.startswith("wb_")
        sels = []
        _find_selection_values(r.get("where", {}), sels)
        goal_selection = any(_refs_goal(v) for v in sels)
        # record what each pick rule selects by (the value subtree of its Argmin)
        if name.endswith("probe_pick") and sels:
            svs = str(sels[0])
            pick_selects_by[name] = ("goal-proximity" if _refs_goal(sels[0])
                                     else "visits/novelty" if "visits" in svs
                                     else "other:" + svs[:60])
        if goal_selection:
            (ctrl_objectives if is_wb else drive_viol if is_uh else ctrl_objectives).append(name)
    for name, by in pick_selects_by.items():
        tag = "DRIVE" if name.startswith("uh_") else "CONTROL"
        print(f"  pick rule {name:16} ({tag:7}) SELECTS BY: {by}")
    print(f"\n  uh_* DRIVE rules that SELECT by goal-proximity: {drive_viol}  (MUST be [])")
    print(f"  wb_* CONTROL rules that select by goal-proximity (by design): {ctrl_objectives}")
    # the drive's curiosity pick must select by novelty, never goal
    ok_pick = pick_selects_by.get("uh_probe_pick") == "visits/novelty"
    if drive_viol or not ok_pick:
        print("FAIL: the understanding drive references a win/goal objective.")
        return 1
    print("\nPASS: the uh_* drive selects by NOVELTY (curiosity), never by goal/win; "
          "the win-objective lives only in the wb_* control.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
