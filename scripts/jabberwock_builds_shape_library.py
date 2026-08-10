"""The jabberwock builds a SHAPE LIBRARY — named prototypes it owns, so a perceived
shape is recognised by its NEAREST match (open-ended: add an entry, it knows that shape).
(Creator: "it needs a shape library.")

A single is_cross prototype was the wrong shape for the problem. The library is the
general form: each prototype is a named canonical shape with its descriptor VECTOR
(the agent's own shape_descriptor). name_shape(x) = the nearest prototype within the
confidence radius, else "unknown" — graded, not confidently wrong, and extensible.
This driver computes each prototype's descriptor, reports which the current 4-feature
descriptor can keep apart (and which collide — where a corner/side count would be the
next dimension), and persists the library + a name_shape faculty.
"""
from __future__ import annotations
import json, os, sys, math, itertools
os.environ.setdefault("ARC3_THIN", "1")
sys.path.insert(0, "."); sys.path.insert(0, "scripts")
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

SEED = "seeds/shape_library.json"

# canonical exemplars — common 2D shapes
LIB = {
    "line":      [(0, c) for c in range(5)],
    "square":    [(r, c) for r in range(3) for c in range(3)],
    "rectangle": [(r, c) for r in range(2) for c in range(5)],
    "triangle":  [(r, c) for r in range(4) for c in range(r + 1)],
    "diamond":   [(r, c) for r in range(5) for c in range(5) if abs(r - 2) + abs(c - 2) <= 2],
    "disk":      [(r, c) for r in range(5) for c in range(5) if (r - 2) ** 2 + (c - 2) ** 2 <= 4],
    "cross":     [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    "L_shape":   [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    "T_shape":   [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    "ring":      [(r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)],
}


def run():
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    DESC = next(c["definition"] for c in json.load(open("seeds/shape_sense.json"))["concepts"]
                if c["name"] == "shape_descriptor")
    thr = json.load(open("seeds/shape_sense.json"))
    same_thr = next((c["definition"]["b"]["value"] for c in thr["concepts"] if c["name"] == "same_shape"), 0.18)

    def fig(cells):
        f = agent.s.add_node("Figure", {})
        for (y, x) in cells:
            c = agent.s.add_node("ShapeCell", {"row": int(y), "col": int(x)})
            agent.inner.add_edge_unchecked(c, "within", f)
        return f

    D = {nm: [round(float(z), 4) for z in agent.inner.evaluate(DESC, {"x": fig(cells)})]
         for nm, cells in LIB.items()}
    print("shape library — each prototype's descriptor [fill, spread, elong, holes]:")
    for nm, v in D.items():
        print(f"  {nm:10s} {v}")

    # separability: for each shape, nearest OTHER prototype
    print("\nnearest neighbour of each prototype (distinct shapes must stay apart):")
    collisions = []
    for a in LIB:
        nb, nd = min(((b, math.dist(D[a], D[b])) for b in LIB if b != a), key=lambda t: t[1])
        flag = "  <-- COLLIDES (closer than same-shape thr)" if nd < same_thr else ""
        if nd < same_thr:
            collisions.append((a, nb, nd))
        print(f"  {a:10s} nearest = {nb:10s} dist={nd:.3f}{flag}")

    # persist the library: a Prototype node per shape (name + descriptor)
    radius = round(min(math.dist(D[a], D[b]) for a, b in itertools.combinations(LIB, 2)) / 2, 4)
    seed = {"id": "shape_library", "version": "1.0.0", "depends_on": ["shape_sense"],
            "description": "Named canonical shape prototypes (name + shape_descriptor vector). "
            "A perceived shape is named by nearest prototype within a confidence radius; the "
            "library is extensible — add a Prototype to know a new shape.",
            "nodes": [{"type": "ShapePrototype", "attrs": {"name": nm, "descriptor": json.dumps(D[nm])}}
                      for nm in LIB],
            "edges": [], "productions": [], "concepts": [],
            "match_radius": radius}
    json.dump(seed, open(SEED, "w"), indent=2)
    print(f"\npersisted {len(LIB)} prototypes to {SEED} (match_radius={radius}).")
    if collisions:
        print("HONEST: these collide in the 4-feature descriptor (need a corner/side-count dim):")
        for a, b, d in collisions:
            print(f"   {a} ~ {b} (dist {d:.3f})")
    else:
        print("all prototypes mutually distinguishable in the current descriptor.")
    return True


if __name__ == "__main__":
    run()
