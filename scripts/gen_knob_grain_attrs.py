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
d["version"] = max(d["version"], "1.12.0", key=lambda v: tuple(map(int, v.split("."))))
if "v1.12.0 (2026-10-08" not in d["description"]:
    d["description"] += (" v1.12.0 (2026-10-08, tranche 10): opt-in knob_edit.step_mode=='grain' steps a knob to the next"
                         " distinct observed value of the signal its gating comparison reads (found structurally in the"
                         " active rules; values read from grain_signal_types), with a degenerate guard (the new gate must"
                         " still separate the observed values). Absent -> fixed knob_step.")
P.write_text(json.dumps(d, indent=1, ensure_ascii=False) + ("\n" if text.endswith("\n") else ""))
print("variation_ops", d["version"])
