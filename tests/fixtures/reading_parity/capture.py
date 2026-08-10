"""capture.py — Phase-1 reading-migration parity-fixture capture.

Runs the CURRENT (unmodified) Python reading core (domains.reading_collapse) on a
deterministic corpus and dumps the outputs of every function Phase 1 migrates, as
JSON fixtures under tests/fixtures/reading_parity/. These fixtures are the GROUND
TRUTH the graph-native rule-loop reimplementation of each slice (1b skeleton, 1c
ground, 1d event/main-verb, 1e clause-segmentation, 1f head-selection) must match
byte-for-byte — the SAME parity method tests/fixtures/composer_driver_parity used.

This script does NOT modify any source file; it only reads the current code and
writes fixtures. It is idempotent (each run overwrites the same fixture file) and
side-effect-free on seeds/ (read_clause is called with write=False so no Concept
nodes / edges leak, and learn=False so the codebook is not grown).

Run:  cd gamma-substrate && PYTHONPATH=runners/dsl/python:.:scripts python3 \
        tests/fixtures/reading_parity/capture.py

The corpus is:
  · CROW — the crow fable, the byte-identity guard's own FABLE_TEXT (sentence-split);
    every slice must keep these byte-identical (crow gate).
  · VALIDATE — the two validating-milestone sentences (bolder / wretch); 1d/1e change
    these on PURPOSE, so they are captured as a BEFORE snapshot (documented, not gated
    to stay identical — see README.md).
  · DEFN — encyclopedic definitional/enumeration prose the read_and_ground bench uses.
  · CONSTRUCT — one sentence per construction class (copula/causal/comparative/
    conditional/enumeration/designation/possession/event) so the skeleton + decode +
    ground outputs are frozen across the whole codebook.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "reading_parity")

from substrate.boot_core import boot_core                          # noqa: E402
from domains import dictionary_lexicon as dl                       # noqa: E402
from domains import reading_collapse as rc                         # noqa: E402
from domains import reading_corpus as rcorp                        # noqa: E402
from domains import comprehend_text as ct                          # noqa: E402


class Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def fresh_agent() -> Agent:
    s, agent_node = boot_core()
    return Agent(s, agent_node)


def _jsonable(v):
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    return str(v)


# --------------------------------------------------------------------------- #
#  CORPUS
# --------------------------------------------------------------------------- #
FABLE_TEXT = (
    "In a spell of dry weather, when the Birds could find very little to "
    "drink, a thirsty Crow found a pitcher with a little water in it. "
    "But the pitcher was high and had a narrow neck, and no matter how he "
    "tried, the Crow could not reach the water. "
    "The poor thing felt as if he must die of thirst. "
    "Then an idea came to him. "
    "Picking up some small pebbles, he dropped them into the pitcher one by "
    "one. "
    "With each pebble the water rose a little higher until at last it was "
    "near enough so he could drink."
)

def _corpus_sentences() -> list:
    """The WHOLE real-prose corpus (Aesop + Grimm, from the offline cache), one flat
    deterministic sentence list. This is the byte-identity ORACLE for the event-
    grounding migration: every event predication the agent produces over real prose
    is frozen here, so any drift in _event_predication's replacement is caught. Empty
    when the corpus is not cached (the CORPUS-group gate then skips) — CROW/DEFN/
    CONSTRUCT remain the always-present contract."""
    try:
        srcs = [s for s in rcorp.SOURCES if s["key"] in ("aesop", "grimm")]
        units = rcorp.units_from_cache(sources=srcs)
    except Exception:      # noqa: BLE001 — corpus not cached in this environment
        return []
    sents: list = []
    for u in units:
        for s in rc._split_sentences(u["text"]):
            if s and s.strip():
                sents.append(s)
    return sents


CORPUS = {
    "CROW": rc._split_sentences(FABLE_TEXT),
    "VALIDATE": [
        "One of them, who was bolder than the rest, went to see what was going on.",
        "The dog, wretch that I am, I have killed my only friend.",
        "He was bolder than the rest.",
        "The carter killed the sparrow's friend.",
    ],
    "DEFN": [
        "recognition is a perception of a known thing",
        "mistrust is a belief that someone is not reliable",
        "granite is an igneous rock formed from cooled magma",
        "a computer includes a processor, a memory and a bus",
    ],
    "CONSTRUCT": [
        "a dog is an animal",
        "rain causes floods",
        "unlike gold, silver tarnishes",
        "if it rains then the ground is wet",
        "basalt contains plagioclase and pyroxene",
        "this mineral is called olivine",
        "the crystal exhibits cleavage",
        "the crow dropped the pebbles into the pitcher",
    ],
    # WHOLE-CORPUS byte-identity oracle for the event-grounding migration (real
    # Aesop + Grimm prose). Large + real; frozen BEFORE any migration slice lands.
    "CORPUS": _corpus_sentences(),
}


# --------------------------------------------------------------------------- #
#  PER-SENTENCE CAPTURE — every function Phase 1 migrates.
# --------------------------------------------------------------------------- #
def capture_sentence(ag: Agent, sentence: str) -> dict:
    rc.ensure_codebook(ag)
    words = ct._recognise_words(ag, sentence)
    sub, _, _ = rc._resolve(ag)
    lex = rc._marker_lexicon(sub)

    skeleton, roles, marker_seq = rc._skeleton_from_words(ag, list(words))

    # 1b skeleton
    rec = {
        "sentence": sentence,
        "recognised_words": list(words),
        "skeleton": _jsonable(skeleton),
        "roles": _jsonable(roles),
        "marker_seq": _jsonable(marker_seq),
    }

    # decode + winner (already graph-native; captured for context)
    try:
        res = rc._decode(ag, skeleton) if skeleton else {"plan": [], "residual": []}
        name, fit = rc._winner(res)
        rec["decode"] = {"construction": name, "shape_fit": fit,
                         "residual": _jsonable([list(r) for r in (res.get("residual") or [])])}
    except Exception as e:  # noqa: BLE001
        rec["decode"] = {"error": str(e)}

    # 1c ground (via read_clause, write=False/learn=False — no graph mutation)
    try:
        r = rc.read_clause(ag, list(words), write=False, learn=False)
        rec["read_clause"] = {"construction": r.get("construction"),
                              "predications": _jsonable(r.get("predications")),
                              "roles": _jsonable(r.get("roles")),
                              "residual": _jsonable(r.get("residual"))}
    except Exception as e:  # noqa: BLE001
        rec["read_clause"] = {"error": str(e)}

    # 1d main verb + event predication
    try:
        flat = [rc._clean_tok(w) for w in words if str(rc._clean_tok(w))]
        vi = rc._find_main_verb(flat)
        preds, inverted = rc._event_predication_graph(ag, list(words), lex,
                                                      intransitive_ok=True, return_meta=True)
        rec["event"] = {"main_verb_index": vi,
                        "main_verb": (flat[vi].lower() if vi is not None else None),
                        "predications": _jsonable(preds), "inverted": inverted}
        rec["event_for_sentence"] = _jsonable(
            rc.event_predication_for_sentence(ag, sentence, intransitive_ok=True))
    except Exception as e:  # noqa: BLE001
        rec["event"] = {"error": str(e)}

    # 1e clause segmentation / decompose
    try:
        d = rc.decompose_sentence(ag, sentence)
        rec["decompose"] = {"clauses": _jsonable(d.get("clauses")),
                            "predications": _jsonable(d.get("predications")),
                            "multi_clause": d.get("multi_clause"),
                            "n_boundaries": d.get("n_boundaries")}
    except Exception as e:  # noqa: BLE001
        rec["decompose"] = {"error": str(e)}

    # 1f head-selection on each role span
    try:
        heads = {rr: {"clean_head": rc._clean_head(rr), "arg_head": rc._arg_head(ag, rr)}
                 for rr in roles if rr and rr.strip()}
        rec["heads"] = _jsonable(heads)
    except Exception as e:  # noqa: BLE001
        rec["heads"] = {"error": str(e)}

    return rec


def main() -> int:
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    dl.warm_wordnet("en")
    out: dict = {"corpus": {}}
    for group, sentences in CORPUS.items():
        ag = fresh_agent()               # fresh agent per group (no cross-talk)
        recs = []
        for s in sentences:
            if not s.strip():
                continue
            recs.append(capture_sentence(ag, s))
        out["corpus"][group] = recs
    path = os.path.join(FIXTURE_DIR, "reading.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
