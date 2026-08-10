"""Write this rung's PROVENANCE PIN and the measured-value PINS the gate asserts against.

§12.3: a provenance claim must be pinned to its DIFF, never to a mutable tree. BOTH ENDPOINTS
are fixed — `base_sha` (the `main` HEAD this rung was cut from) and `rung_commit_sha` (this
rung's OWN implementation commit). Never `HEAD`, never the working tree.

Run AFTER the implementation commit exists:
    PYTHONPATH=.:runners/dsl/python python scripts/ink_ventral_pin.py <rung_commit_sha>
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains import engine_provenance

# PROTOCOL §10 rule 3 / 1b -- PIN, do not merely REPORT. This script's whole
# job is to record the engine, which makes reporting-without-pinning the
# sharpest form of the defect: it described an engine it had not pinned.
engine_provenance.engine_preamble()

BASE_SHA = "328065b62a31cf1daeb601557f21a0d331a2aed2"
RES = os.path.join(ROOT, "results", "ink_ventral_measure.json")


def main() -> int:
    if len(sys.argv) != 2 or len(sys.argv[1]) != 40:
        print("usage: ink_ventral_pin.py <40-char rung commit sha>")
        return 2
    rung = sys.argv[1]
    line = engine_provenance.provenance_line()
    rep = engine_provenance.engine_provenance()
    pin = {"base_sha": BASE_SHA, "rung_commit_sha": rung,
           "provenance_line": line,
           "engine_verdict": rep["source_match"],
           "engine_sha256_short": rep["short"],
           "engine_tree": rep["engine_tree"],
           "this_tree": rep["this_tree"],
           "stale_rust": rep["stale_rust"]}
    with open(os.path.join(ROOT, "results", "ink_ventral_provenance.json"), "w") as f:
        json.dump(pin, f, indent=1)

    with open(RES) as f:
        r = json.load(f)
    pins = {
        "a3": r["arms"]["a3"]["acc"],
        "a4": r["arms"]["a4"]["acc"],
        "h1_prefix": r["h1_verdict"].split(" ")[0],
        "h3_prefix": r["h3_verdict"].split(" ")[0],
        "h2": r["h2_verdict"],
        "h2_acc": r["h2"]["acc"],
        "overall": r["overall"],
        "g0b_pass": r["g0bc"]["g0b_pass"],
        "g0c_refutes": r["g0bc"]["g0c_refutes_at_premise"],
        "g0b_obs": r["g0bc"]["modal_agreement"],
        "g0b_null": r["g0bc"]["null_modal_agreement"],
        "g0c_f0": r["g0bc"]["f0"],
    }
    with open(os.path.join(ROOT, "results", "ink_ventral_pins.json"), "w") as f:
        json.dump(pins, f, indent=1)
    print(json.dumps({"pin": pin, "pins": pins}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
