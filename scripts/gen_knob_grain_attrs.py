#!/usr/bin/env python3
"""Tranche 10: VariationOp{knob_edit}.grain_signal_types (inert data: the node
types the grain-quantised step reads the gated signal's observed values from)
in seeds/variation_ops.json v1.12.0. The step itself is opt-in via
`step_mode: "grain"` (absent -> the fixed knob_step, unchanged). Idempotent;
run after gen_variation_credit_seed.py / gen_cue_route_exclusion.py."""
import json
from pathlib import Path
P = Path(__file__).resolve().parents[1] / "seeds/variation_ops.json"
text = P.read_text(); d = json.loads(text)
n = next(n for n in d["nodes"] if n["type"] == "VariationOp" and n["attrs"].get("name") == "knob_edit")
n["attrs"]["grain_signal_types"] = ["SentenceParse"]
# v1.15.0 (tranche 12): promoted to default by the preregistered rule in
# SUBSTRATE_KNOB_GRAIN_PROMOTION_V3_PREREG_20261009.md (Q1-Q4 held).
n["attrs"]["step_mode"] = "grain"
n["attrs"]["grain_end"] = 1
# v1.16.0 (tranche 12): cue_set_edit.explore_unscored promoted to default by the
# preregistered rule in SUBSTRATE_EXPLORE_UNSCORED_PROMOTION_V1_PREREG_20261009.md (E1-E4 held).
c = next(x for x in d["nodes"] if x["type"] == "VariationOp" and x["attrs"].get("name") == "cue_set_edit")
c["attrs"]["explore_unscored"] = 1
d["version"] = max(d["version"], "1.16.0", key=lambda v: tuple(map(int, v.split("."))))
if "v1.12.0 (2026-10-08" not in d["description"]:
    d["description"] += (" v1.12.0 (2026-10-08, tranche 10): opt-in knob_edit.step_mode=='grain' steps a knob to the next"
                         " distinct observed value of the signal its gating comparison reads (found structurally in the"
                         " active rules; values read from grain_signal_types), with a degenerate guard (the new gate must"
                         " still separate the observed values). Absent -> fixed knob_step.")
P.write_text(json.dumps(d, indent=1, ensure_ascii=False) + ("\n" if text.endswith("\n") else ""))
if "v1.15.0 (2026-10-09" not in d["description"]:
    d["description"] += (" v1.15.0 (2026-10-09, tranche 12): knob_edit defaults to step_mode='grain' with grain_end=1"
                         " (a last-resort step one exact frame quantum past the observed frame), promoted by the"
                         " preregistered v3 gate.")
if "v1.16.0 (2026-10-09" not in d["description"]:
    d["description"] += (" v1.16.0 (2026-10-09, tranche 12): cue_set_edit.explore_unscored=1 by default (preregistered gate"
                         " E1-E4: zero-overlap verbs 6/6 vs 0/6, overlap verbs unchanged at 6/6 in 7 experiments).")
print("variation_ops", d["version"])
