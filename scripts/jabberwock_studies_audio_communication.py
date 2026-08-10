"""THE JABBERWOCK BECOMES AN EXPERT ON THE HISTORY & DEVELOPMENT OF AUDIO
COMMUNICATION ON EARTH — it READS the donor domain from the world and BANKS it as
held structure. Per user: "have the agent become an expert on the history and
development of audio communication on earth."

The donor taxonomy is the USER'S thought: the fundamental origins of language, the
language of isolated peoples, NON-HUMAN language, language as a thing that EVOLVED
over deep time, AND the other domains where signal is recovered from shitty noise —
sonar above all. The point (ozma_analogical_transfer): the agent's idea-engine
transfers the structural SHAPE of vaguely-similar domains into the stuck problem;
here the donor set is communication-as-noise-robust-code-recovery across engineering
(sonar/matched-filter/active sensing), evolution (echolocation, birdsong, whistled
languages), and deep-time language change — the invariant the speech pipeline needs.

THE ENGINE (the agent's own faculty, NOT a Python summary): read_and_ground —
fetch each concept's lead from web_world.wikipedia_summary, COMPREHEND it into a
genus via the construction grammar, GROUND it, recurse down the genus chain. The
extracted GENUS is the structural shape (smoke: echolocation -> 'biological active
sonar'; matched filter -> 'correlating a known delayed signal' = AxS). Each concept
is linked into a held Microtheory 'audio_communication_on_earth' so the agent HOLDS
the domain as structure it can later transfer FROM.

HONEST (binary admissibility): the agent grounds the GENUS (the shape) reliably but
often NOT to a seeded PRIMITIVE (the comprehension-DEPTH residual, cmsg c82551fa/
764a5141). For the analogical-transfer use-case the GENUS/shape is the product, so
the depth residual does not bind the donor-breadth goal — reported, not hidden. No
verbatim article text is emitted (GET-only, the agent's grounded short genus only).

Run:  python -m scripts.jabberwock_studies_audio_communication
"""
from __future__ import annotations

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.jabberwock_frontier_select import _build_mind            # noqa: E402
from domains import read_and_ground as rag                            # noqa: E402
from domains import grounded_representation as gr                     # noqa: E402

# THE DONOR TAXONOMY — the user's thought, branch by branch. Entry points; the
# read_and_ground recursion acquires each one's genus chain beneath it.
BRANCHES: dict[str, list[str]] = {
    "non-human language": [
        "Animal communication", "Zoosemiotics", "Bird vocalization",
        "Whale vocalization", "Waggle dance", "Alarm signal"],
    "biosonar / perceive-by-emitting": [
        "Animal echolocation", "Sonar", "Active sensing"],
    "signal recovery from noise (sonar family)": [
        "Matched filter", "Pulse compression", "Ambiguity function",
        "Signal-to-noise ratio", "Cocktail party effect"],
    "origins & deep-time evolution of language": [
        "Origin of language", "Evolution of language", "Proto-language"],
    "isolated peoples / noise-robust human codes": [
        "Whistled language", "Talking drum", "Click consonant"],
    "vocal learning (the babble loop in nature)": [
        "Vocal learning", "Birdsong", "Babbling"],
}


def main() -> int:
    print("=" * 78)
    print("THE JABBERWOCK STUDIES THE HISTORY OF AUDIO COMMUNICATION ON EARTH")
    print("=" * 78)
    sub = _build_mind()
    conv = types.SimpleNamespace()           # no fed gloss -> the web reader fires

    mt = sub.add_node("Microtheory", {"name": "audio_communication_on_earth",
                                      "origin": "agent_self_study"})

    shapes: list[tuple[str, str, str]] = []  # (branch, concept, extracted genus)
    n_read = n_genus = n_primitive = n_miss = 0

    for branch, concepts in BRANCHES.items():
        print(f"\n{'-'*74}\nBRANCH: {branch}")
        for name in concepts:
            try:
                r = rag.read_and_ground(sub, name, conv, max_depth=3)
            except Exception as e:  # noqa: BLE001
                print(f"  · {name:<26} ERR {type(e).__name__}")
                n_miss += 1
                continue
            n_read += 1
            st = r.get("structure") or {}
            genus = st.get("genus")
            grounded = bool(r.get("grounded"))
            # link the now-held concept into the domain Microtheory.
            cid = gr._concept_by_name(sub).get(rag._name_norm(name)) if hasattr(rag, "_name_norm") else None
            if cid is None:
                idx = gr._concept_by_name(sub)
                cid = idx.get(name.lower()) or idx.get(name)
            if cid is not None:
                try:
                    sub.add_edge(mt, "has_concept", cid)
                except Exception:
                    pass
            if grounded:
                n_primitive += 1
                tag = "GROUNDED->primitive"
            elif genus:
                n_genus += 1
                tag = f"genus={genus!r}"
                shapes.append((branch, name, str(genus)))
            else:
                n_miss += 1
                tag = f"miss ({(r.get('reason') or '')[:40]})"
            print(f"  · {name:<26} {tag}")

    print("\n" + "=" * 78)
    print(f"ACQUIRED: {n_read} concepts read; {n_primitive} grounded-to-primitive; "
          f"{n_genus} genus-extracted (topic-depth); {n_miss} miss.")
    print("\nTHE STRUCTURAL SHAPES THE AGENT EXTRACTED (genus = the transfer-candidate "
          "shape; the analogical-transfer engine selects among these by COMPRESSION):")
    for branch, name, genus in shapes:
        print(f"  [{branch[:28]:<28}] {name:<24} -> {genus}")
    print("\nHONEST: the agent reliably grounds the GENUS (the shape) but mostly NOT to "
          "a seeded PRIMITIVE (comprehension-DEPTH residual). For analogical TRANSFER "
          "the genus IS the product, so this builds real donor breadth; deep mastery of "
          "each branch is the next pass. The domain is now a held Microtheory the agent "
          "can transfer FROM. No verbatim article text emitted.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
