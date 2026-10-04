"""Compare a CIE standard-observer prediction for red with the photon eye output."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from domains.photon_eye import GraphEye  # noqa: E402

# CIE 2006 LMS cone fundamentals, 2° field, energy units, 610 nm.
CIE_LMS_610 = (0.7057161, 0.2052721, 0.000008034895)
PHOTON_COUNTS = (250, 500, 1000, 2000)


def unit(v):
    norm = math.sqrt(sum(x * x for x in v))
    if norm == 0.0:
        return None
    return tuple(x / norm for x in v)


def eye_red(count):
    eye = GraphEye(n_az=1, context={"worker_capacity": 1}).build()
    try:
        eye.submit_photons([{"column": 0, "wavelength_nm": 610.0, "count": count}])
        deadline = time.monotonic() + 5.0
        while eye.processed_count() < 1 and time.monotonic() < deadline:
            time.sleep(0.005)
        if eye.processed_count() != 1:
            raise RuntimeError(f"eye processed {eye.processed_count()} exposures; expected 1")
        snapshot = eye.latest()
        if not snapshot or len(snapshot.get("percepts", [])) != 1:
            raise RuntimeError("photon eye did not return exactly one percept")
        p = snapshot["percepts"][0]
        return (float(p["red_green"]), float(p["blue_yellow"]))
    finally:
        eye.stop()


def main():
    L, M, S = CIE_LMS_610
    research = (L - M, S - 0.5 * (L + M))
    research_unit = unit(research)
    rows = []
    for count in PHOTON_COUNTS:
        observed = eye_red(count)
        observed_unit = unit(observed)
        if observed_unit is None:
            rows.append({"photons": count, "observed": observed,
                         "status": "dead_zero_opponent_output"})
            continue
        cosine = max(-1.0, min(1.0, sum(a * b for a, b in zip(research_unit, observed_unit))))
        angle = math.degrees(math.acos(cosine))
        score = 100.0 * (1.0 + cosine) / 2.0
        rows.append({"photons": count, "observed": observed,
                     "observed_unit": observed_unit, "cosine": cosine,
                     "angular_mismatch_degrees": angle,
                     "direction_match_score": score, "status": "measured"})
    measured = [r for r in rows if r["status"] == "measured"]
    result = {
        "experiment": "marys_room_research_red_vs_photon_eye_v1",
        "provenance": provenance_line(),
        "research_source": "CIE 2006 LMS 2-degree cone fundamentals, energy units, 610 nm, CIE 170-1:2006 table 6.7",
        "cie_lms": {"L": L, "M": M, "S": S},
        "opponent_transform": {"RG": "L-M", "BY": "S-0.5*(L+M)"},
        "research_opponent": research,
        "research_opponent_unit": research_unit,
        "arms": rows,
        "summary": {
            "mean_direction_match_score": (sum(r["direction_match_score"] for r in measured) / len(measured)
                                             if measured else None),
            "worst_direction_match_score": (min(r["direction_match_score"] for r in measured)
                                              if measured else None),
            "all_arms_live": len(measured) == len(PHOTON_COUNTS),
        },
    }
    out = Path(__file__).parents[1] / "results" / "marys_room_red_match.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
