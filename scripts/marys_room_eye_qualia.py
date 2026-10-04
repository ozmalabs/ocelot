"""Run the bounded Mary’s Room analogue over the committed color identity rules.

The physical prediction is an explicit theory baseline calculated from known cone
responses. The eye arm computes its readout in the graph. This is a system
capability experiment, not a test for phenomenal consciousness.
"""
from __future__ import annotations

import json
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import colour_identity_world as ciw  # noqa: E402
from domains.analogy_search import concept_signature  # noqa: E402


RED = {"cL": 15, "cM": 5, "cS": 20}
NEUTRAL = {"cL": 10, "cM": 10, "cS": 20}


def boot():
    s, agent = boot_core()
    load_seeds_into(s, agent, ["vision_colour_identity"])
    # Qualia-space is a graph schema but is not a boot_core registry seed.
    # Install its manifest explicitly so the signature read uses the codebook.
    manifest = json.loads((Path(__file__).parents[1] / "seeds" / "qualia_space.json").read_text())
    s._inner.load_seed_manifest(manifest, agent)
    return s


def cells(spec):
    return [dict(spec, rrow=0, rcol=i) for i in range(12)]


def prediction_from_physics(spec):
    # Mary’s theory baseline: opponent coordinates from the known cone responses.
    return (spec["cL"] - spec["cM"], spec["cS"] - (spec["cL"] + spec["cM"]))


def run_exposure(spec, *, achromatopsia=0.0):
    s = boot()
    h = ciw.add_field(s, cells=cells(spec))
    ciw.set_flag(s, identity=1.0)
    for p in s.nodes("ColourIdentityParams"):
        s.set_attr(p, "achromatopsia", float(achromatopsia))
    ciw.tick(s)
    region_attrs = [s.node(n)["attrs"] for n in h["region_ids"]]
    categories = list(s.nodes("ColourCategory"))
    return {
        "opponent_values": sorted({(int(round(a.get("crg", 0))), int(round(a.get("cby", 0))))
                                    for a in region_attrs}),
        "opponent_computed_cells": sum(a.get("op_done", 0.0) > 0.5 for a in region_attrs),
        "categories": [s.node(n)["attrs"] for n in categories],
        "category_signatures": [sorted(concept_signature(s, n)) for n in categories],
    }


def main():
    predicted = prediction_from_physics(RED)
    # Before exposure, there is no sensory graph to read and no category present.
    before = {"region_count": 0, "category_count": 0,
              "theory_prediction": predicted}
    after = run_exposure(RED)
    after_value = after["opponent_values"][0] if after["opponent_values"] else None
    achromatic = run_exposure(NEUTRAL)
    achromatopsia = run_exposure(RED, achromatopsia=1.0)

    result = {
        "experiment": "marys_room_eye_qualia_bounded_analogue_v1",
        "provenance": provenance_line(),
        "before_release": before,
        "after_release": after,
        "achromatic_floor": achromatic,
        "achromatopsia_control": achromatopsia,
        "prediction_matches_eye": predicted == after_value,
        "pass": (
            before["region_count"] == 0 and before["category_count"] == 0
            and predicted == after_value
            and len(after["categories"]) == 1
            and after["categories"][0].get("crg") == predicted[0]
            and after["categories"][0].get("cby") == predicted[1]
            and bool(after["category_signatures"])
            and len(achromatic["categories"]) == 1
            and (achromatic["categories"][0].get("crg"), achromatic["categories"][0].get("cby")) == (0, 0)
            and achromatopsia["opponent_values"] == [predicted]
            and achromatopsia["categories"] == []
        ),
    }
    # The actual live-signal check is explicit and applied in both stimulus arms.
    result["pass"] = result["pass"] and after["opponent_computed_cells"] == 12 \
        and achromatopsia["opponent_computed_cells"] == 12
    out = Path(__file__).parents[1] / "results" / "marys_room_eye_qualia.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
