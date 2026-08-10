"""THE CAMPAIGN — the jabberwock reads its 146 dark encyclopedias and grounds
their vocabulary to the WordNet bedrock (docs/encyclopedic_seeds_reading_plan.md).

A WORLD-ADAPTER driver (CLAUDE.md): it SEQUENCES the agent's own faculties — it
decides nothing about meaning. For each unregistered legacy prose-rule seed it
  1. READS the seed's prose rules (head/body facts + if/then/why principles) —
     mechanical file I/O;
  2. EXTRACTS the content words — a thin I/O-boundary tokenizer (opaque prose ->
     the smallest graph tokens), not a meaning decision;
  3. GROUNDS each distinct word ONCE (global dedup) via the agent's read_and_ground
     faculty fed by the WordNet dictionary reader (wordnet_genus.ChainReader) —
     the AGENT comprehends each genus and its recursion climbs built_from to the
     seeded lexical_ontology_roots bedrock (`entity`).

Shared substrate: every word grounds into ONE graph, so shared ancestors
(`stream`, `body_of_water`, `physical_entity`, …) ground once and are reused —
the encyclopedic vocabulary becomes one reachable grounding graph.

Honest coverage: WordNet noun-hypernym chains cover ~half the vocabulary; the
rest (jargon, adjectives/verbs, proper nouns, technical compounds with no clean
noun ladder) is the NAMED frontier, reported, not hidden.

Writes: var/encyclopedic_campaign_report.json (per-seed coverage + totals +
sample frontier) and var/encyclopedic_grounded_graph.json (the grounded graph).
Prints a progress line per seed so a Monitor can watch it.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import time

import domains.seed_registry  # noqa: F401 — populates REGISTRY
from substrate.seeds import REGISTRY
from substrate.boot_core import CORE_SEEDS, load_seeds_into
from substrate.world_adapter import WorldAdapter
from domains.read_and_ground import read_and_ground
from domains import wordnet_genus as wg
from domains import web_world

# The on-disk Wikipedia dump (20231101.en) is AUTHORITATIVE for the campaign:
# a title absent locally is a definitive miss, not a network round-trip. Without
# this a WordNet-miss word (or a mid-chain genus not in the dump) cost ~1-20s of
# HTTP retries — the whole slowness. Local-only makes a miss instant.
web_world.set_local_only(True)

# Connectives / function words — dropped at the I/O boundary (not content).
_STOP = set(
    "the a an of to in on for and or is are be been being am was were by with as "
    "at from that which who whom whose when where then thus it its this these "
    "those must should can may will would could into not no any all each every "
    "some more most less than so non sub via per about against over under above "
    "below between within without across through but if while during after before "
    "such also only just both either neither nor yet because since unless until "
    "they them their there here what how why does do did has have had having "
    # adverbs / discourse connectives — function words, not encyclopedic content
    "again always already almost ahead along away around often sometimes usually "
    "hence thereby therefore otherwise however moreover conversely namely indeed "
    "rather quite very much many few several first second third next last finally "
    "above below onto upon amongst whilst whereas whereby herein thereof therein "
    "allow allows allowed allowing make makes made get gets got let lets "
    # contraction FRAGMENTS (the tokeniser splits 'aren't' -> 'aren'): not content
    "ain aren arent isn isnt wasn wasnt weren werent don dont doesn doesnt didn "
    "didnt won wont wouldn wouldnt couldn couldnt shouldn shouldnt mustn mustnt "
    "needn neednt hasn hasnt haven havent hadn hadnt mightn shan oughtn daren cant "
    # indefinite pronouns / correlative adverbs — function words, not vocabulary
    "another anything anyone anybody anywhere someone somebody something somewhere "
    "everyone everybody everything everywhere nobody nothing nowhere none anyhow "
    "somehow apart aside instead perhaps otherwise meanwhile nonetheless besides "
    "nevertheless furthermore regardless henceforth elsewhere likewise".split()
)


_CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+")


def _split_token(tok: str) -> list[str]:
    """Split on the ORTHOGRAPHIC CUE: a compound joined by hyphens / underscores
    ('action-space') and a camelCase / code identifier ('addEdge' -> add, edge)
    become their parts. This is the high-confidence boundary signal (the same one
    the agent's authored MorphHead/MorphTail primitive reads); the agent's
    morpheme decomposition then handles the UN-marked compounds below."""
    out: list[str] = []
    for piece in re.split(r"[-_]+", tok):
        out.extend(_CAMEL.findall(piece))
    return out


# --- the agent's SHAPE-based morpheme decomposition, wired in --------------
# After the orthographic cue, each token is decomposed by the agent's own faculty
# (domains/morpheme_decomposition): it recognises known morphemes in the SHAPE,
# the reading chosen by its compression selector (graph-resident Argmin), so an
# UN-marked compound ('addedge', 'actionspace') still grounds as its parts. A form
# the agent has read as a unit stays whole. Decision is the agent's, not a regex.
_DECOMP = {"code": None, "held": None, "wa": None, "n": 0}
_DECOMP_CACHE: dict[str, list[str]] = {}


def _morphemes(word: str) -> list[str]:
    """The agent's morpheme reading of one token (cached per distinct word). On a
    scratch substrate refreshed periodically so the candidate pool stays small."""
    if word in _DECOMP_CACHE:
        return _DECOMP_CACHE[word]
    if _DECOMP["code"] is None:
        from domains import morpheme_decomposition as _md
        from substrate.world_adapter import WorldAdapter as _WA
        _DECOMP["md"] = _md
        _DECOMP["code"], _DECOMP["held"] = _md.corpus_morpheme_code()
        _DECOMP["wa"] = _WA()
        _DECOMP["wa_cls"] = _WA
    if _DECOMP["n"] >= 800:          # refresh scratch substrate to bound growth
        _DECOMP["wa"] = _DECOMP["wa_cls"]()
        _DECOMP["n"] = 0
    _DECOMP["n"] += 1
    parts = _DECOMP["md"].decompose(_DECOMP["wa"].s, word,
                                    _DECOMP["code"], _DECOMP["held"])["parts"]
    _DECOMP_CACHE[word] = parts
    return parts


def _content_words(text: str) -> set[str]:
    # Tokenise (original case for camelCase) -> ORTHOGRAPHIC split (cue) -> the
    # AGENT'S morpheme decomposition (shape) -> lowercase, drop connectives/short.
    words: set[str] = set()
    for raw in re.findall(r"[A-Za-z][A-Za-z_-]+", text or ""):
        for sub in _split_token(raw):
            w = sub.lower()
            if len(w) <= 2 or w in _STOP:
                continue
            for m in _morphemes(w):
                if len(m) > 2 and m not in _STOP:
                    words.add(m)
    return words


def _legacy_seed_prose() -> dict[str, list[str]]:
    """{seed_id: [prose strings]} for every UNREGISTERED legacy prose-rule seed
    (head/body facts + if/then/why principles)."""
    registered = set(REGISTRY.known())
    out: dict[str, list[str]] = {}
    for path in sorted(glob.glob("seeds/*.json")):
        sid = os.path.basename(path)[:-5]
        if sid in registered:
            continue
        try:
            d = json.load(open(path))
        except Exception:
            continue
        prose: list[str] = []
        for r in (d.get("rules") or []):
            if not isinstance(r, dict) or "match" in r:
                continue
            if "head" in r and "body" in r:
                prose.append(f"{r.get('head','')} {r.get('body','')}")
            elif "if" in r and "then" in r:
                prose.append(
                    " ".join(map(str, r.get("if") or []))
                    + " " + " ".join(map(str, r.get("then") or []))
                    + " " + str(r.get("why", "")))
        if prose:
            out[sid] = prose
    return out


def run():
    os.makedirs("var", exist_ok=True)
    wa = WorldAdapter(seeds=CORE_SEEDS)
    load_seeds_into(wa.s, wa.agent,
                    ["lexical_ontology_roots", "relations", "psychology"])

    seeds = _legacy_seed_prose()
    print(f"campaign: {len(seeds)} legacy encyclopedias", flush=True)

    # the agent reads its prose for EPONYMS — technical names ('Ackermann
    # function', "Amdahl's law") that denote the PERSON they're named after, in no
    # dictionary but attested by the prose. They ground AS a person (-> entity).
    from domains import eponym_grounding as _eg
    eponyms = _eg.detect_eponyms([p for ps in seeds.values() for p in ps])
    print(f"eponyms read from prose: {len(eponyms)}", flush=True)

    # the agent expands technical ACRONYMS by context — reading Wikipedia's
    # disambiguation senses and picking the one whose words match the acronym's
    # prose context ('AAC' -> 'Advanced Audio Coding' -> 'coding'). High-precision.
    from domains import acronym_context as _ac
    acronym_heads = _ac.build_acronym_heads([p for ps in seeds.values() for p in ps])
    print(f"acronyms expanded by context: {len(acronym_heads)}", flush=True)

    grounded: set[str] = set()       # words that grounded to a basis primitive
    attempted: set[str] = set()      # words tried (dedup)
    per_seed: dict[str, dict] = {}
    t_start = time.time()

    for i, (sid, prose) in enumerate(sorted(seeds.items()), 1):
        words = set()
        for p in prose:
            words |= _content_words(p)
        new = [w for w in sorted(words) if w not in attempted]
        for w in new:
            attempted.add(w)
            # Read each word through the HYBRID reader: the word's sense-consistent
            # WordNet ladder when present, the on-disk Wikipedia lead when WordNet
            # misses ('admin' -> 'administration', 'anycast' -> '… methodology'),
            # AND lazy WordNet for the SUB-GENERA those leads name so they chain to
            # the bedrock instead of dead-ending. The AGENT comprehends each genus.
            try:
                if w in acronym_heads:
                    reader = _ac.AcronymReader(w, acronym_heads[w])
                elif w in eponyms:
                    reader = _eg.EponymReader(w)
                else:
                    reader = wg.HybridChainReader(w)
                res = read_and_ground(wa.s, w, conversation=reader, max_depth=25)
                if res.get("grounded"):
                    grounded.add(w)
            except Exception:
                pass  # an un-readable word is the honest miss, not a crash
        cov = [w for w in words if w in grounded]
        per_seed[sid] = {"words": len(words), "grounded": len(cov),
                         "coverage": round(len(cov) / max(1, len(words)), 3)}
        dt = time.time() - t_start
        print(f"[{i:3d}/{len(seeds)}] {sid:34s} "
              f"words={len(words):4d} grounded={len(cov):4d} "
              f"({per_seed[sid]['coverage']:.0%})  "
              f"| total {len(grounded)}/{len(attempted)} | {dt:.0f}s",
              flush=True)

    total_words = len(attempted)
    total_grounded = len(grounded)
    frontier = sorted(attempted - grounded)
    report = {
        "seeds": len(seeds),
        "distinct_words": total_words,
        "grounded": total_grounded,
        "coverage": round(total_grounded / max(1, total_words), 3),
        "elapsed_s": round(time.time() - t_start, 1),
        "per_seed": per_seed,
        "frontier_sample": frontier[:200],
        "frontier_count": len(frontier),
    }
    with open("var/encyclopedic_campaign_report.json", "w") as fh:
        json.dump(report, fh, indent=1)
    with open("var/encyclopedic_grounded_graph.json", "w") as fh:
        json.dump(wa.s.graph_to_dict(), fh)

    print("=" * 60, flush=True)
    print(f"DONE: {total_grounded}/{total_words} distinct words grounded "
          f"({report['coverage']:.0%}) across {len(seeds)} encyclopedias "
          f"in {report['elapsed_s']:.0f}s", flush=True)
    print(f"frontier (ungrounded): {len(frontier)} — sample: {frontier[:15]}",
          flush=True)
    print("report -> var/encyclopedic_campaign_report.json", flush=True)


if __name__ == "__main__":
    run()
    sys.exit(0)
