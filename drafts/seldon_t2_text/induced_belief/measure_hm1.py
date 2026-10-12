"""measure_hm1 — H-M1: does the macro-surprise mechanism recover a forecast-
relevant DIRECTION on the macro_release prints H1 scored 0.0 on?

Runs macro_surprise.decode_macro_surprise over the FROZEN
induced_belief/macro_study_set.json labels (hand-labeled released-vs-prior
direction, committed BEFORE this measurement — see the file's _meta and the
macro_study_set.sha256 checksum), and reports macro-snippet directional accuracy
vs the ToM arm's 0.0 baseline on these prints.

CONFIRMED iff macro-snippet directional accuracy > 0.5 (MACRO_SURPRISE_PREREG
H-M1). The gold distribution is up=6/down=9/none=2 (NOT 50/50), so >0.5 is a
genuine bar, not a coin flip.

For the panel-trend snippets (prior=None in the text), the unit's own
macro_monthly panel is loaded (t2_adapter.load_panels) so the released-vs-trend
path can fire; for text-prior snippets the panel is unused. No fabricated
numbers: every prediction is a real decode.

Emits a JSON blob to stdout the results write-up quotes verbatim.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_T2 = os.path.dirname(_HERE)
_ROOT = os.path.dirname(os.path.dirname(_T2))
for p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python"), _T2):
    if p not in sys.path:
        sys.path.insert(0, p)

MACRO_STUDY = os.path.join(_HERE, "macro_study_set.json")
UNITS_DIR = os.path.join(_ROOT, ".bigtmp", "track2", "units")


def load_macro_study():
    with open(MACRO_STUDY) as f:
        return json.load(f)["snippets"]


def _asof_for_unit(unit_dir):
    import tomllib
    card = os.path.join(unit_dir, "card.toml")
    try:
        with open(card, "rb") as f:
            c = tomllib.load(f)
        return (c.get("provenance", {}).get("data_cutoff")
                or c.get("task", {}).get("asof")
                or c.get("targets", {}).get("asof"))
    except Exception:
        return None


def _load_panel_for(unit):
    """Load the unit's macro panel if it ships one (for the panel-trend path).
    Returns a panel DataFrame or None. Mechanical host I/O."""
    unit_dir = os.path.join(UNITS_DIR, unit)
    if not os.path.isdir(unit_dir):
        return None
    try:
        from t2_adapter import load_panels
    except Exception:
        return None
    asof = _asof_for_unit(unit_dir)
    try:
        return load_panels(unit_dir, asof)
    except Exception:
        return None


def run_macro(snips):
    from substrate.world_adapter import WorldAdapter
    from induced_belief import arm
    from induced_belief import macro_surprise as ms

    a = WorldAdapter()
    mk = arm.boot(a)
    ms.boot_macro(a)

    # cache panels per unit (some snippets share a unit).
    panel_cache = {}
    rows = []
    for s in snips:
        unit = s.get("unit")
        if unit not in panel_cache:
            panel_cache[unit] = _load_panel_for(unit)
        panel = panel_cache[unit]
        arm.reset_beliefs(a, mk)
        r = ms.decode_macro_surprise(a, s["text"], mk, panel=panel,
                                     series_hint=s.get("series"))
        rows.append({
            "id": s["id"], "gold": s["gold"], "pred": r["direction"],
            "unit": unit, "series": s.get("series"),
            "released": s.get("released"), "prior": s.get("prior"),
            "source": r["surprise"]["source"],
            "surprise_sign": r["surprise"]["surprise_sign"],
            "trend": r["surprise"].get("trend"),
            "marginal": r["marginal"], "grounding_weight": r["grounding_weight"],
            "reached": r["reached"], "hops": r["hops"],
            "grounding_gap": r["grounding_gap"], "shift": r["shift"],
        })
    return rows


def main():
    snips = load_macro_study()
    rows = run_macro(snips)

    correct = sum(1 for r in rows if r["pred"] == r["gold"])
    n = len(rows)
    acc = correct / n if n else None

    # split by path source
    by_source = defaultdict(lambda: [0, 0])
    for r in rows:
        by_source[r["source"] or "none"][1] += 1
        if r["pred"] == r["gold"]:
            by_source[r["source"] or "none"][0] += 1
    by_source_out = {k: {"correct": v[0], "n": v[1],
                         "acc": round(v[0] / v[1], 3) if v[1] else None}
                     for k, v in by_source.items()}

    # directional (exclude gold==none for the up/down recovery view)
    dir_rows = [r for r in rows if r["gold"] in ("up", "down")]
    dir_correct = sum(1 for r in dir_rows if r["pred"] == r["gold"])
    dir_n = len(dir_rows)

    out = {
        "arm": "macro_surprise",
        "n_snippets": n,
        "gold_distribution": dict(Counter(r["gold"] for r in rows)),
        "tom_baseline_acc": 0.0,   # the ToM arm's score on macro_release (H1)
        "macro_surprise_acc": round(acc, 3) if acc is not None else None,
        "correct": correct,
        "confirm_threshold": 0.5,
        "H_M1_confirmed": bool(acc is not None and acc > 0.5),
        "directional_only": {
            "correct": dir_correct, "n": dir_n,
            "acc": round(dir_correct / dir_n, 3) if dir_n else None,
        },
        "by_source": by_source_out,
        "per_snippet": rows,
    }
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
