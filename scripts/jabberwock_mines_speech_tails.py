"""THE JABBERWOCK MINES THE TAILS — speech-understanding DISORDERS and EXCEPTIONAL
people. Per user: "mine further on speech understanding disorders and exceptional
people. the tails have more data."

WHY THE TAILS (the (G,Gamma) reading): a disorder is a NATURAL ABLATION EXPERIMENT —
it removes ONE structure and leaves the rest, DISSOCIATING the components of speech
understanding (capability = admissible structure; binary admissibility — the component
is there or not, [[ozma_recognition_is_a_conjunction]]). Pure word deafness =
word-recognition broken with hearing + language INTACT -> word-recognition is a
SEPARABLE structure. The exceptional tail (echolocators = biosonar, hyperpolyglots,
interpreters) shows what the structure does at its LIMIT. So the tails MAP speech
understanding to its components far better than the typical pipeline.

THE ENGINE (the agent's own faculty, extends scripts/jabberwock_studies_audio_
communication.py): read_and_ground -> web_world.wikipedia_summary (GET-only),
COMPREHEND -> genus. BUT the disorder's DATA is the DISSOCIATION (impaired vs
preserved), which lives in the DIFFERENTIA, not the head-noun genus (the known
extractor limit — talking-drum -> 'hourglass-shaped drum'). So the world-adapter ALSO
surfaces the DISSOCIATION CLAUSE: the sentence(s) carrying impaired/preserved markers
(mechanical I/O highlighting of the informative clause; the agent's comprehension is
the genus, the clause is the raw structural datum the tails uniquely provide). Each
concept is banked into a held Microtheory 'speech_understanding_tails'.

Donkey-clean: reads as STRUCTURE to map components, never "train a model"; GET-only; no
verbatim dump beyond the single dissociation clause that IS the datum. HONEST: genus
extraction is fragile on functional defs; the dissociation clause is the world-adapter
surfacing the informative sentence, not deep comprehension (that depth is the residual).

Run:  python -m scripts.jabberwock_mines_speech_tails
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import types                                                          # noqa: E402
from scripts.jabberwock_frontier_select import _build_mind            # noqa: E402
from domains import read_and_ground as rag                            # noqa: E402
from domains import grounded_representation as gr                     # noqa: E402
from domains import web_world as ww                                   # noqa: E402

# THE TAILS — each a natural ablation (disorder) or a limit case (exceptional).
TAILS: dict[str, list[str]] = {
    "disorders — aphasias (production/comprehension/repetition dissociate)": [
        "Aphasia", "Receptive aphasia", "Expressive aphasia", "Conduction aphasia",
        "Transcortical sensory aphasia"],
    "disorders — agnosias (recognition dissociates from hearing)": [
        "Pure word deafness", "Auditory agnosia", "Phonagnosia", "Amusia",
        "Auditory verbal agnosia"],
    "disorders — processing / developmental": [
        "Auditory processing disorder", "Specific language impairment", "Dyslexia",
        "Landau–Kleffner syndrome"],
    "disorders — degraded input / production": [
        "Cochlear implant", "Foreign accent syndrome", "Dysarthria"],
    "exceptional — the limit cases": [
        "Human echolocation", "Hyperpolyglot", "Simultaneous interpretation",
        "Absolute pitch", "Echoic memory"],
}

# markers of a DISSOCIATION (what is impaired vs what is PRESERVED) — the datum.
_DISSOC = re.compile(
    r"\b(intact|preserved|spared|despite|whereas|impair|inability|unable|cannot|"
    r"loss of|deficit|difficulty|while .*(?:normal|preserved)|normal hearing)\b",
    re.IGNORECASE)


def _dissociation(extract: str) -> str | None:
    """The world-adapter surfaces the INFORMATIVE clause — the sentence carrying the
    impaired-vs-preserved contrast that IS the dissociation datum. Mechanical I/O."""
    if not extract:
        return None
    sents = re.split(r"(?<=[.])\s+", extract)
    hits = [s.strip() for s in sents if _DISSOC.search(s)]
    if not hits:
        return None
    # the first 1-2 dissociation sentences (the structural contrast).
    return " ".join(hits[:2])[:300]


def main() -> int:
    print("=" * 78)
    print("THE JABBERWOCK MINES THE TAILS — speech-understanding disorders & exceptional")
    print("=" * 78)
    sub = _build_mind()
    conv = types.SimpleNamespace()
    mt = sub.add_node("Microtheory", {"name": "speech_understanding_tails",
                                      "origin": "agent_self_study"})

    dissocs: list[tuple[str, str, str]] = []   # (group, concept, dissociation clause)
    n_read = n_genus = n_dissoc = n_miss = 0

    for group, concepts in TAILS.items():
        print(f"\n{'-'*74}\n{group}")
        for name in concepts:
            summ = ww.wikipedia_summary(name) or (
                lambda t: ww.wikipedia_summary(t[0]) if t else None)(
                    ww.wikipedia_search(name, limit=1))
            extract = (summ or {}).get("extract", "") if summ else ""
            try:
                r = rag.read_and_ground(sub, name, conv, max_depth=2)
            except Exception:
                r = {"structure": None, "grounded": False}
            n_read += 1
            genus = (r.get("structure") or {}).get("genus")
            if genus:
                n_genus += 1
            # link into the tails Microtheory.
            cid = gr._concept_by_name(sub).get(name.lower()) or \
                gr._concept_by_name(sub).get(name)
            if cid is not None:
                try:
                    sub.add_edge(mt, "has_concept", cid)
                except Exception:
                    pass
            dissoc = _dissociation(extract)
            if dissoc:
                n_dissoc += 1
                dissocs.append((group, name, dissoc))
                print(f"  · {name}")
                print(f"      genus={genus!r}")
                print(f"      DISSOCIATION: {dissoc}")
            else:
                n_miss += 1
                print(f"  · {name:<28} genus={genus!r}  (no dissociation clause found)")

    print("\n" + "=" * 78)
    print(f"MINED: {n_read} tail concepts; {n_genus} genus-extracted; "
          f"{n_dissoc} with a DISSOCIATION clause; {n_miss} clause-miss.")
    print("\nTHE DISSOCIATION MAP — what each tail tells the agent SEPARATES (the data "
          "the tails uniquely provide; capability=admissible-structure, read off the "
          "natural ablations):")
    for group, name, dissoc in dissocs:
        print(f"  [{group.split('—')[0].strip()[:12]:<12}] {name:<26} :: {dissoc[:140]}")
    print("\nHONEST: the genus extractor is weak on functional defs (a disorder's value "
          "is its DISSOCIATION, not its genus); the dissociation clause is the world-"
          "adapter surfacing the informative sentence (the datum), the agent's deep "
          "comprehension of which component it separates is the residual. The domain is "
          "now a held Microtheory the agent can transfer FROM.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
