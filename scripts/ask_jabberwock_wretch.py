"""ASK THE JABBERWOCK what's wrong with the dog-and-sparrow reading and how it would
fix itself. A world-adapter shell: it STAGES the tale, then SEQUENCES the agent's
own faculties (reading_trace introspection + the situation-model read-off) and
prints what the agent reports. No decision here — the agent answers in its terms.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import comprehension_reader as cr                  # noqa: E402
from domains import coref_entities as ce                        # noqa: E402
from domains import reflective_faculty as rf                    # noqa: E402
import domains.reading_corpus as rc                             # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


SEP = "=" * 78


def banner(t):
    print("\n" + SEP + "\n" + t + "\n" + SEP)


def main():
    dl.warm_wordnet("en")
    grimm = [s for s in rc.SOURCES if s["key"] == "grimm"]
    units = {u["label"]: u for u in rc.load_units(sources=grimm)}
    tale = units["THE DOG AND THE SPARROW"]
    text = tale["text"]

    banner("THE TALE (the wretch/carter region)")
    for ln in text.splitlines():
        if any(w in ln.lower() for w in ("wretch", "carter", "sparrow", "driver", "kill")):
            print("  " + ln.strip())

    agent = _Agent(*boot_core())
    graph = cr.read_and_comprehend(agent, text, window=2, max_sentences=60)
    sm = graph["spine"]["situation_model"]

    banner("WHAT THE AGENT TRACKED (situation model — the entities it minted)")
    for nm in sorted(sm):
        st = sm[nm]
        cat = st.get("coref_category")
        m = st.get("coref_mentions")
        clean = ce._grounded_cleanliness(nm) if isinstance(nm, str) else None
        flag = "  <== EPITHET?" if isinstance(nm, str) and "wretch" in nm.lower() else ""
        print(f"  {nm!r:32} cat={cat!r:10} mentions={m} clean={clean}{flag}")

    sub = agent.s._inner if hasattr(agent.s, "_inner") else agent.s

    banner("ASK THE JABBERWOCK — reflect('referent_trace') — its OWN tracked-referent pool")
    ans = rf.reflect("referent_trace", None, sub)
    print(f"  n_referents: {ans.get('n_referents')}   n_suspect: {ans.get('n_suspect')}")
    print("  SUSPECT REFERENTS (tracked as a character but held-signal says junk):")
    for r in ans.get("suspect_referents", []):
        print(f"    {r['name']!r:34} cat={r['category']!r:9} mentions={r['mentions']} "
              f"clean={r['cleanliness']} agent={r['acts_as_agent']} theme={r['acts_as_theme']} "
              f"refers_to_in={r['refers_to_in']}  <- {r.get('why')}")

    for probe in ("wretch", "carter", "sparrow"):
        banner(f"ASK THE JABBERWOCK — reflect('referent_trace', {probe!r})")
        ans = rf.reflect("referent_trace", probe, sub)
        for r in ans.get("referents", []):
            if r.get("category") not in ("person", "animal"):
                continue
            print(f"    {r['name']!r:34} cat={r['category']!r:9} mentions={r['mentions']} "
                  f"clean={r['cleanliness']} agent={r['acts_as_agent']} theme={r['acts_as_theme']} "
                  f"refers_to_in={r['refers_to_in']}")


if __name__ == "__main__":
    main()
