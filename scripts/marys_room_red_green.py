"""Research-only red/green prediction vs photon-eye signal and graph compression."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from domains.photon_eye import GraphEye  # noqa: E402
from domains.analogy_search import concept_signature  # noqa: E402
from domains import colour_identity_world as ciw  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

CIE_LMS = {
    "red_610nm": (0.7057161, 0.2052721, 0.000008034895),
    "green_530nm": (0.7706373, 0.9356857, 0.01260114),
}
PHOTONS = 1000
REPEATS = 12
DIMS = 2


def unit(v):
    n = math.sqrt(sum(x*x for x in v))
    return None if n == 0.0 else tuple(x/n for x in v)


def opponent_from_lms(lms):
    L, M, S = lms
    return (L - M, S - 0.5 * (L + M))


def match(a, b):
    ua, ub = unit(a), unit(b)
    if ua is None or ub is None:
        return {"status": "zero_vector"}
    cosine = max(-1.0, min(1.0, sum(x*y for x, y in zip(ua, ub))))
    return {"cosine": cosine,
            "angle_degrees": math.degrees(math.acos(cosine)),
            "direction_score": 100.0 * (1.0 + cosine) / 2.0}


def photon_eye_pair():
    eye = GraphEye(n_az=2, context={"worker_capacity": 1}).build()
    try:
        eye.submit_photons([
            {"column": 0, "wavelength_nm": 610.0, "count": PHOTONS},
            {"column": 1, "wavelength_nm": 530.0, "count": PHOTONS},
        ])
        deadline = time.monotonic() + 5.0
        while eye.processed_count() < 1 and time.monotonic() < deadline:
            time.sleep(0.005)
        if eye.processed_count() != 1:
            raise RuntimeError(f"processed {eye.processed_count()} exposures, expected 1")
        percepts = eye.latest()["percepts"]
        if len(percepts) != 2:
            raise RuntimeError(f"received {len(percepts)} percepts, expected 2")
        return {
            "red_610nm": (float(percepts[0]["red_green"]), float(percepts[0]["blue_yellow"])),
            "green_530nm": (float(percepts[1]["red_green"]), float(percepts[1]["blue_yellow"])),
        }
    finally:
        eye.stop()


def _cone_encoding(rg, by):
    # Reversible adapter into colour_identity_world's (cL,cM,cS) input shape:
    # cM=1, cL-cM=rg, cS-(cL+cM)=by. Adds no class label or decision.
    cM = 1.0
    cL = cM + rg
    cS = by + cL + cM
    if min(cL, cM, cS) < 0.0:
        raise ValueError(f"opponent vector has no positive encoding under fixed cM=1: {(rg, by)}")
    return {"cL": cL, "cM": cM, "cS": cS}


def compress_field(vectors):
    s, agent = boot_core(seeds=())
    load_seeds_into(s, agent, ["vision_colour_identity"])
    qualia = json.loads((Path(__file__).parents[1] / "seeds" / "qualia_space.json").read_text())
    s._inner.load_seed_manifest(qualia, agent)
    cells = []
    for label in ("red_610nm", "green_530nm"):
        vals = _cone_encoding(*vectors[label])
        cells.extend([dict(vals, rrow=0, rcol=len(cells) + i) for i in range(REPEATS)])
    h = ciw.add_field(s, cells=cells)
    ciw.set_flag(s, identity=1.0)
    ciw.tick(s)
    categories = []
    for n in s.nodes("ColourCategory"):
        attrs = s.node(n)["attrs"]
        categories.append({"crg": float(attrs["crg"]), "cby": float(attrs["cby"]),
                           "members": int(attrs["members"]),
                           "signature": sorted(concept_signature(s, n))})
    categories.sort(key=lambda x: (x["crg"], x["cby"]))
    assignments = [ciw.region_attr(s, n, "sign_dist") for n in h["region_ids"]]
    N, k, d = len(cells), len(categories), DIMS
    raw = N * d
    coded = k * d + N
    return {"n_samples": N, "n_categories": k, "categories": categories,
            "all_assigned": all(x >= 0 for x in assignments),
            "raw_coordinate_cost": raw, "category_code_cost": coded,
            "compression_ratio": raw / coded if coded else None,
            "cost_reduction_fraction": (raw - coded) / raw if raw else None}


def main():
    research = {k: opponent_from_lms(v) for k, v in CIE_LMS.items()}
    eye = photon_eye_pair()
    per_color = {}
    for label, reference in research.items():
        observed = eye[label]
        theory_label = "red" if reference[0] > 0 else "green" if reference[0] < 0 else "unclassified"
        eye_label = "red" if observed[0] > 0 else "green" if observed[0] < 0 else "unclassified"
        per_color[label] = {
            "cie_lms": CIE_LMS[label], "research_opponent": reference,
            "research_prediction": theory_label, "eye_opponent": observed,
            "eye_prediction": eye_label, "label_agreement": theory_label == eye_label,
            "direction_match": match(reference, observed),
        }
    research_comp = compress_field(research)
    eye_comp = compress_field(eye)
    prototype_match = {}
    # The minted prototypes are the two exact source coordinates after the same
    # graph quantizer. Match by known RG sign, not by node order or labels in graph.
    for label in per_color:
        rcoord = research[label]
        ecoord = eye[label]
        prototype_match[label] = match(rcoord, ecoord)
    result = {
        "experiment": "marys_room_red_green_identification_compression_v1",
        "provenance": provenance_line(),
        "stimulus_photons": PHOTONS,
        "research_source": "CIE 2006 LMS cone fundamentals, 2-degree field, energy units, CIE 170-1:2006 table 6.7",
        "opponent_axes": {"red_green": "L-M", "blue_yellow": "S-0.5*(L+M)"},
        "research_only_classification_accuracy": sum(v["research_prediction"] == ("red" if k == "red_610nm" else "green") for k, v in per_color.items()) / 2.0,
        "eye_classification_accuracy": sum(v["eye_prediction"] == ("red" if k == "red_610nm" else "green") for k, v in per_color.items()) / 2.0,
        "red_green_label_agreement": all(v["label_agreement"] for v in per_color.values()),
        "per_color": per_color,
        "research_field_compression": research_comp,
        "experienced_eye_field_compression": eye_comp,
        "prototype_direction_matches": prototype_match,
        "mean_eye_research_direction_score": sum(v["direction_match"]["direction_score"] for v in per_color.values()) / 2.0,
    }
    out = Path(__file__).parents[1] / "results" / "marys_room_red_green.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
