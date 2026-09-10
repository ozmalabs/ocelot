"""Block 338000 — harvest the relations that PASSED calibration, at scale.

Reads seeds/generated/qwen3_relation_calibration.json (written by
scripts/llm_calibrate_relations.py). For each relation the calibration marked
`earned: true`, elicit it at scale over a larger inventory and write the reaped
edges tagged source=qwen3 + per-relation trust. Relations that did NOT earn the
band are SKIPPED and recorded as honest negatives — not reaped (that is the
point of the gate).

Per-relation scaled inventories are curated pools broad enough to be useful but
constrained enough for a clean read; capital-of/located-in draw on a country/
city list, part-of on a meronymy pool, same-as/opposite-of on an adjective pool.

ELICIT is oracle-only; no LLM at query. Run after calibration:
  HF_HOME=/applications/data/model_graph_work/hf_home \
  PYTHONPATH=runners/dsl/python:. \
  nohup /applications/data/model_graph_work/venv/bin/python -u \
    scripts/llm_harvest_relations.py > var/harvest_relations.log 2>&1 &
"""
from __future__ import annotations

import json
import os
import time

from domains import llm_hf_forward as hf
from domains import llm_knowledge_seed as ks

MODEL = "/applications/data/model_graph_work/Qwen3.8-4B-Distill"
CALIB = "seeds/generated/qwen3_relation_calibration.json"
OUT = "seeds/generated/qwen3_reaped_relations.json"
SOURCE = "qwen3"
TRUST = 0.5
BATCH = 32

# per-relation scaled elicitation config: (template, subjects, candidates)
# Kept compact + curated; the calibration already established whether the read
# is trustworthy — this widens coverage for the earned ones only.
_COUNTRIES = [
    "france", "germany", "spain", "italy", "japan", "china", "russia", "egypt",
    "canada", "brazil", "portugal", "greece", "poland", "austria", "norway",
    "sweden", "finland", "ireland", "cuba", "peru", "chile", "mexico", "india",
    "kenya", "morocco", "turkey", "thailand", "vietnam", "hungary", "denmark",
    "belgium", "switzerland", "netherlands", "argentina", "colombia",
]
_CAPITALS = [
    "paris", "berlin", "madrid", "rome", "tokyo", "beijing", "moscow", "cairo",
    "ottawa", "brasilia", "lisbon", "athens", "warsaw", "vienna", "oslo",
    "stockholm", "helsinki", "dublin", "havana", "lima", "santiago",
    "mexico_city", "delhi", "nairobi", "rabat", "ankara", "bangkok", "hanoi",
    "budapest", "copenhagen", "brussels", "bern", "amsterdam", "buenos_aires",
    "bogota",
]
_CITIES = _CAPITALS + ["lyon", "munich", "osaka", "mumbai", "lagos", "toronto",
                       "chicago", "sydney", "barcelona", "naples"]
_REGIONS = ["europe", "asia", "africa", "americas", "oceania", "france",
            "germany", "spain", "italy", "japan", "china", "usa", "canada"]
_PARTS = ["finger", "toe", "knuckle", "nail", "petal", "leaf", "root", "wheel",
          "engine", "door", "window", "roof", "page", "keyboard", "screen",
          "handle", "blade", "wing", "beak", "tail", "trunk", "branch"]
_WHOLES = ["hand", "foot", "arm", "leg", "body", "flower", "plant", "tree",
           "car", "vehicle", "room", "house", "building", "book", "computer",
           "office", "knife", "bird", "airplane", "elephant"]
_ADJ = ["big", "small", "fast", "slow", "happy", "sad", "hot", "cold", "up",
        "down", "light", "dark", "open", "closed", "full", "empty", "high",
        "low", "hard", "soft", "wet", "dry", "rich", "poor", "young", "old",
        "strong", "weak", "clean", "dirty", "quick", "large", "little"]

_CONFIG = {
    "part_of": ("A {} is part of a", _PARTS, sorted(set(_PARTS) | set(_WHOLES))),
    "located_in": ("{} is located in", _CITIES, sorted(set(_CITIES) | set(_REGIONS))),
    "capital_of": ("The capital of {} is", _COUNTRIES, sorted(set(_CAPITALS))),
    "same_as": ("A word that means the same as {} is", _ADJ, sorted(set(_ADJ))),
    "opposite_of": ("The opposite of {} is", _ADJ, sorted(set(_ADJ))),
}


def main() -> int:
    print("=" * 74)
    print("HARVEST RELATIONS — block 338000 (earned relations only)")
    print("=" * 74)
    if not os.path.isfile(CALIB):
        print("NO calibration file %s — run scripts/llm_calibrate_relations.py first"
              % CALIB)
        return 2
    calib = json.load(open(CALIB))["relations"]
    earned = [r for r, d in calib.items() if d.get("earned")]
    print("calibration says EARNED: %s" % (earned or "NONE"))
    if not earned:
        print("no relation earned the band — nothing to harvest (honest negative).")
        # still write an empty result recording the negative
        json.dump({"_doc": "No new relation earned the band (block 338).",
                   "source": SOURCE, "earned": [], "relations": {}},
                  open(OUT, "w"), indent=1)
        return 0

    t0 = time.time()
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    print("loaded HFForward in %.0fs" % (time.time() - t0))

    out = {"_doc": ("Reaped RELATIONS from qwen3 (block 338), EARNED tiers only "
                    "(per-relation calibration gate). Every edge source=qwen3 "
                    "trust=0.5. Relations that failed calibration are recorded "
                    "as honest negatives, not reaped."),
           "source": SOURCE, "trust": TRUST,
           "earned": earned, "skipped": [r for r in calib if r not in earned],
           "relations": {}}
    for rel in earned:
        tmpl, subs, cands = _CONFIG[rel]
        t1 = time.time()
        pairs = ks.elicit_relation_batch(m, tok, subs, template=tmpl,
                                         candidates=cands, batch_size=BATCH)
        edges = [{"subject": s, "relation": rel, "object": o,
                  "source": SOURCE, "trust": TRUST}
                 for s, o in pairs if s != o]
        out["relations"][rel] = {
            "template": tmpl, "n_edges": len(edges),
            "elicit_seconds": round(time.time() - t1, 1),
            "calibration": calib[rel], "edges": edges,
        }
        print("%-12s reaped %d edges in %.0fs"
              % (rel, len(edges), time.time() - t1))

    json.dump(out, open(OUT, "w"), indent=1)
    total = sum(len(v["edges"]) for v in out["relations"].values())
    print("\nwrote %s (%d edges across %d earned relations)"
          % (OUT, total, len(earned)))
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
