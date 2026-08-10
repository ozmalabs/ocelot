"""seeds/perception_concepts.json — the perception / visual-cortex concepts the JABBERWOCK LEARNED from its
local Wikipedia (visual cortex, object permanence, perception, predictive coding, iconic memory, saccade,
multiple object tracking): the knowledge it needs to DESIGN a retaining visual cortex. The definitions are
Wikipedia's, fetched through the agent's WikiTeacher; this captures them as Concept graph-data so a fresh boot
holds them. Re-run to refresh from Wikipedia. Not hand-authored — Wikipedia's text, grounded by the agent."""
import sys, json
sys.path.insert(0, "."); sys.path.insert(0, "runners/dsl/python")
from domains.wiki_library import WikipediaLibrary
from domains.wiki_teacher import WikiTeacher

SUBJECTS = ["visual cortex", "object permanence", "perception", "predictive coding",
            "iconic memory", "saccade", "multiple object tracking"]
lib = WikipediaLibrary(); wt = WikiTeacher(lib)
concepts = []
for s in SUBJECTS:
    p = wt(f"what is {s}")
    defn = (p or {}).get("answer") if isinstance(p, dict) else None
    if not defn:
        art = wt.lookup(s); defn = getattr(art, "abstract", None) if art else None
    if defn:
        concepts.append({"name": s.replace(" ", "_"), "definition": defn.strip()[:700],
                         "domain": "perception"})
        print(f"  {s} -> {len(defn)} chars")
    else:
        print(f"  {s} -> NO DEFINITION")
seed = {"id": "perception_concepts", "version": "1.0.0", "depends_on": [],
        "description": ("Perception / visual-cortex concepts the jabberwock learned from Wikipedia (the "
            "knowledge to design a retaining visual cortex): " + ", ".join(SUBJECTS) + "."),
        "nodes": [], "edges": [], "productions": [], "rules": [], "concepts": concepts}
json.dump(seed, open("seeds/perception_concepts.json", "w"), indent=1)
json.load(open("seeds/perception_concepts.json"))
print(f"wrote seeds/perception_concepts.json: {len(concepts)} concepts")
