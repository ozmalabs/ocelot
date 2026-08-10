"""gap_driven_acquisition — GAP-DRIVEN KNOWLEDGE ACQUISITION (self-improvement #3).

The earn-not-borrow loop pointed at the agent's OWN KNOWLEDGE GAPS. A KNOWLEDGE
gap is a thin/empty DIMENSION the concept-graph edge-learner (`concept_graph`)
cannot ground — a domain with (almost) no `Microtheory -has_concept-> Concept`
edges, so its region is unresolved (best region-cosine ~0, source falls to the
labelled anchor). When the agent perceives such a gap it does what a person does
with a word it doesn't know: it READS a source, EXTRACTS the region's concepts,
TEACHES the microtheory (persisted, reboot-proof), and the concept-graph then
edge-learns the region (coverage rises) — the SAME shape the external developer
produced BY HAND (seeds/computer_architecture_microtheory.json et al.), but now
AGENT-DRIVEN off a perceived gap.

    GAP (thin/anchored dimension, read off concept_graph coverage)
      -> READ   (read_and_ground's reference reader / wiki_local slab / a fed doc)
      -> EXTRACT (the region's concepts, straight from the source enumerations)
      -> TEACH  (a Microtheory + has_concept edges; persisted to a seed manifest)
      -> RE-DECODE (concept_graph now edge-learns the region — coverage rises)

WORLD-ADAPTER DISCIPLINE (CLAUDE.md). This module owns NO agent decision. It
MARSHALS the read (mechanical reference I/O), EXTRACTS by a source-faithful
enumeration parse (each concept's surface is a substring of the source — never
invented), and INSTALLS the microtheory as admissible graph mutations
(`add_node` / `add_edge`, mirroring the seed loader) + a persisted manifest. The
GAP DECISION is read off `concept_graph`'s coverage (the learner, unchanged); the
grounding/teach is the reused `read_and_ground` + `teach` machinery; the re-decode
is `concept_graph` re-reading the new edges. No `if/else` decides what a concept
means, and there is NO LLM (donkey=0 — extraction is arithmetic over the source).

EARN, NOT FABRICATE (the honesty guard). Every taught concept traces to the read
source (`traces_to_source`): the extractor only emits terms the source names. A
gap with NO readable source yields an HONEST NULL ("can't acquire, no source") —
the agent never fabricates a microtheory. If the source is thin, the taught
microtheory is thin (honest), not padded.

HONEST SCOPE (stated plainly). The COVERAGE of the region rises graph-natively
(bag_size 0 -> N, region-cosine 0 -> positive, the descent co-descends into the
new home microtheory). A genuinely-novel domain's `source` stays 'anchor' rather
than flipping to 'edge', because flipping requires the domain to be REGISTERED as
a labelled region anchor (the hand path's `concept_graph._REGION_ANCHORS` edit) —
a separate LABELLING decision, not edge-learning, and out of this module's scope
(it does not touch the learner). And the enumeration extraction is noisier than
hand-curation (some list fragments leak) — reported, not hidden.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from domains import concept_graph as cg

_ROOT = Path(__file__).resolve().parent.parent
_SEEDS = _ROOT / "seeds"

# thin-dimension threshold: a domain whose has_concept bag is this small AND whose
# region the learner cannot ground is a KNOWLEDGE gap. Read off concept_graph, the
# same coverage the connectivity_report measures — not a bespoke constant.
_THIN_BAG = 2


# =========================================================================== #
#  GAP SIGNAL — read off concept_graph coverage (the learner, unchanged).
# =========================================================================== #

def coverage(agent, domain: str) -> dict:
    """The concept-graph COVERAGE of `domain` — a pure read of the learner's own
    measures: the has_concept bag size, the region confidence (best cosine /
    clarity / grounded), and the descent depth + region + source. This is the
    signal the gap decision is read off (no new measure)."""
    conf = cg.region_confidence(agent, domain)
    d = cg.descend(agent, domain)
    region, source = cg.world_dimension(agent, domain)
    return {"domain": domain, "bag": cg.bag_size(agent, domain),
            "best": conf["best"], "clarity": conf["clarity"],
            "grounded": conf["grounded"], "region": region, "source": source,
            "depth": d["depth"], "path": d["path"]}


def is_knowledge_gap(agent, domain: str, *, thin_bag: int = _THIN_BAG) -> bool:
    """True iff `domain` is a KNOWLEDGE gap: a thin dimension the edge-learner
    cannot ground — its has_concept bag is <= `thin_bag` AND `concept_graph` does
    not ground its region (best cosine below the floor, no edge). A read of the
    learner's coverage, not a hand list."""
    cov = coverage(agent, domain)
    return cov["bag"] <= thin_bag and not cov["grounded"]


def detect_knowledge_gaps(agent, candidates, *, thin_bag: int = _THIN_BAG) -> list:
    """The gap set, DERIVED from coverage (not hardcoded): the subset of
    `candidates` that are knowledge gaps (thin + ungrounded region). `candidates`
    is the pool to check — the microtheory/domain names in play (a caller passes
    the domains it is reasoning over; the DECISION of which are gaps is the
    coverage read here). Returns [{domain, ...coverage}] sorted thinnest-first."""
    gaps = [coverage(agent, d) for d in candidates if is_knowledge_gap(agent, d, thin_bag=thin_bag)]
    gaps.sort(key=lambda c: (c["bag"], c["best"]))
    return gaps


def gap_domain_of(agent, gap_node) -> Optional[str]:
    """Bridge a minted `CapabilityGap` (domains/self_capability_collapse.py) of the
    KNOWLEDGE kind to a domain name: read its `topic` / `domain` / `region` attr.
    A faculty-only gap (no knowledge topic) returns None. Mechanical graph read —
    the gap was DECIDED by the collapse residual, this only reads its subject."""
    sub = getattr(agent, "s", agent)
    at = gap_node if isinstance(gap_node, dict) else sub.node(gap_node)["attrs"]
    for k in ("topic", "domain", "region", "knowledge_domain"):
        v = at.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


# =========================================================================== #
#  READ — reuse the reference reader (read_and_ground's slab / a fed document).
# =========================================================================== #

def read_source(agent, domain: str, *, source_text: Optional[str] = None,
                source_title: Optional[str] = None,
                conversation=None) -> dict:
    """READ the gap domain's source. Reuses the SAME reading stack read_and_ground
    reads through:

      1. an injected `source_text` (a fed reference document — a teacher / a test),
      2. else the `wiki_local` reference slab (the local Wikipedia store the
         read_and_ground reader consults) at `source_title` or `domain`,
      3. else read_and_ground's `_read_def` lead (the reference reader) as a thin
         fallback.

    Returns {found, text, lead, title, source, provenance}. `found=False` (no
    injected text, no slab page, no lead) is the HONEST-NULL branch: the caller
    reports 'can't acquire, no source' and NEVER fabricates. Mechanical I/O."""
    if source_text and source_text.strip():
        return {"found": True, "text": source_text.strip(),
                "lead": _first_sentence(source_text), "title": source_title or domain,
                "source": "fed_document", "provenance": None}

    title = source_title or domain.replace("_", " ")
    # the wiki_local reference slab — the local store read_and_ground reads.
    try:
        from domains import wiki_local as _wl
        if _wl.present():
            summ = _wl.summary(title)
            if summ and (summ.get("text") or summ.get("extract")):
                return {"found": True, "text": summ.get("text") or summ.get("extract"),
                        "lead": _first_sentence(summ.get("extract") or ""),
                        "title": summ.get("title") or title,
                        "source": summ.get("source") or "wikipedia",
                        "provenance": summ.get("provenance")}
    except Exception:
        pass

    # read_and_ground's reference reader (a thin definitional lead) — the last
    # fallback; reused, not reimplemented.
    try:
        from domains import read_and_ground as _rag
        lead = _rag._read_def(domain, conversation, None, substrate=getattr(agent, "s", agent))
        if lead and lead.strip():
            return {"found": True, "text": lead.strip(), "lead": _first_sentence(lead),
                    "title": title, "source": "reference_reader", "provenance": None}
    except Exception:
        pass

    return {"found": False, "text": "", "lead": "", "title": title,
            "source": None, "provenance": None}


def _first_sentence(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    m = re.search(r"[.!?](?:\s|$)", t)
    return (t[: m.end()].strip() if m else t[:300].strip())


# =========================================================================== #
#  EXTRACT — the region's concepts, straight from the source (source-faithful).
# =========================================================================== #

# enumeration cues: a source names a domain's parts as a comma/'and'-list after
# one of these ("...phases: preprocessing, lexical analysis, parsing, ...").
_ENUM_CUE = re.compile(
    r"(?:called|such as|includ(?:e|es|ing|ed)|comprises|consists of|are:|phases:|"
    r"primitives are:|operations,[^:]*:|types of[^:]*:|components?:|elements?:|"
    r"concepts?:)\s*"
    r"([a-z][a-z0-9 ,\-]+?)[.;]", re.IGNORECASE)

# a list item that leads with one of these is a verb/connective fragment, not a
# concept noun-phrase — dropped (extraction quality guard, no meaning decision).
_ITEM_STOP_LEAD = frozenset("""
    or for and nor but so the a an some all of to by via using with without into
    e g i minimizing minimising maximizing reducing reduce predicting assigns
    converting including such related between within across over under this that
    these those which when where while than then also most more less very
""".split())

# a list item containing any of these ANYWHERE is a prose fragment, not a clean
# concept noun-phrase — dropped (adverbs / temporals / hedges / bare verbs that
# only ever appear inside sentence prose, never inside a real concept name).
_ITEM_MIDSTOP = frozenset("""
    however seriously intended various many several certain historical modern
    other another whether although because therefore usually often sometimes
    generally typically especially particularly namely e.g. i.e. etc mainly
    leaders diplomats people person someone thing things instance instances
""".split())


def extract_microtheory(domain: str, source: dict, *, max_concepts: int = 30,
                        nominal_filter: bool = False, collapse_agent: Any = None) -> dict:
    """EXTRACT the region's concept web from the read source — a source-FAITHFUL
    enumeration parse: the terms the source itself LISTS as the domain's parts. A
    list item is kept iff it is a 1-3-word noun phrase (or a single alpha word
    len>4) that does NOT lead with a verb/connective, and — the honesty guard —
    whose surface is a SUBSTRING of the source text. NOTHING is invented.

    When `nominal_filter=True` (the SELF-IMPROVEMENT-CYCLE fix — off by default so
    the legacy extraction is byte-identical), each candidate is additionally routed
    through the agent's POS faculty (consumption_quality.is_nominal): a clause /
    verb-phrase / PP fragment that the hand stop-lists leak
    (`producing_oxygen_gas`, `rather_than_water`, `catalyzed_by_rubisco`) is
    DROPPED, a genuine noun phrase (`calvin_cycle`, `carbon_fixation`) is KEPT. The
    dropped fragments are reported in `dropped_fragments` (before/after auditable).

    Returns {domain, definition, concepts:[{name, surface, definition}],
    source_title, source, thin, dropped_fragments}. `thin=True` when the source
    named no extractable concepts (the honest thin case — a bare stub, not padded)."""
    text = source.get("text", "") or ""
    low = text.lower()
    definition = source.get("lead") or _first_sentence(text)
    concepts: list = []
    seen: set = set()
    for m in _ENUM_CUE.finditer(text):
        span = m.group(1)
        # the sentence the enumeration sits in — a traceable per-concept context.
        ctx = _sentence_around(text, m.start())
        for raw in re.split(r",|\band\b", span):
            surface = raw.strip().strip(".").strip()
            surface = re.sub(r"^(the|a|an|some|all|of|machine specific)\s+", "",
                             surface, flags=re.IGNORECASE).strip()
            words = surface.split()
            if not words:
                continue
            if words[0].lower() in _ITEM_STOP_LEAD:
                continue
            if any(w.lower() in _ITEM_MIDSTOP for w in words):
                continue
            ok_phrase = (1 <= len(words) <= 3) and 3 <= len(surface) <= 34
            ok_word = len(words) == 1 and surface.isalpha() and len(surface) > 4
            if not (ok_phrase or ok_word):
                continue
            if surface.lower() not in low:            # honesty: must be in the source
                continue
            name = re.sub(r"\s+", "_", surface.lower())
            if not name or name in seen or name == domain:
                continue
            seen.add(name)
            concepts.append({"name": name, "surface": surface,
                             "definition": ctx or definition})
            if len(concepts) >= max_concepts:
                break
        if len(concepts) >= max_concepts:
            break
    # READING-BY-COLLAPSE path (beside the enum parser): when an agent is provided,
    # ALSO read the source's definitional / attributive / causal / ... prose by
    # ShapeDecode over the construction codebook (domains/reading_collapse.py) and
    # MERGE its concepts, deduped by name. This is the escape from the enum-only
    # trenchcoat: the enum cue yields 0 on definitional prose, the reader grounds
    # the subject+genus (is_a) and other predications the enum parse never sees. The
    # enum path is untouched (collapse_agent=None -> byte-identical legacy).
    collapse_concepts: list = []
    collapse_report: dict = {}
    if collapse_agent is not None:
        try:
            from domains import reading_collapse as _rc
            col = _rc.concepts_from_reading(collapse_agent, domain, source, definition=definition)
            collapse_report = {"constructions": col.get("constructions", {}),
                               "n_predications": col.get("n_predications", 0)}
            have = {c["name"] for c in concepts}
            for c in col.get("concepts", []):
                if c["name"] in have or c["name"] == domain:
                    continue
                if c["surface"].lower() not in low:      # honesty: keep the source-trace guard
                    continue
                have.add(c["name"])
                collapse_concepts.append(c)
                concepts.append(c)
                if len(concepts) >= max_concepts:
                    break
        except Exception:
            pass
    dropped_fragments: list = []
    if nominal_filter and concepts:
        # the cycle's NOMINAL fix: keep noun phrases, drop clause fragments (POS
        # faculty). Verify-gated in consumption_quality; applied here as the parse's
        # quality guard. Lazy import (consumption_quality reads the POS faculties).
        from domains import consumption_quality as cq
        kept, dropped = cq.nominal_filter(concepts)
        dropped_fragments = [c["name"] for c in dropped]
        concepts = kept
    return {"domain": domain, "definition": definition, "concepts": concepts,
            "source_title": source.get("title"), "source": source.get("source"),
            "thin": len(concepts) == 0, "dropped_fragments": dropped_fragments,
            "collapse_concepts": [c["name"] for c in collapse_concepts],
            "collapse_report": collapse_report}


def _sentence_around(text: str, pos: int) -> str:
    start = text.rfind(".", 0, pos) + 1
    m = re.search(r"[.!?]", text[pos:])
    end = pos + (m.end() if m else 200)
    return re.sub(r"\s+", " ", text[start:end]).strip()[:300]


def traces_to_source(extracted: dict, source: dict) -> bool:
    """The EARN-NOT-FABRICATE guard: every extracted concept's surface is a
    substring of the read source text. True iff the microtheory is fully sourced
    (no invented concept). A read, not a decision."""
    low = (source.get("text", "") or "").lower()
    return all(c["surface"].lower() in low for c in extracted.get("concepts", []))


# =========================================================================== #
#  TEACH — install the microtheory (live graph) + persist (reboot-proof).
# =========================================================================== #

def _manifest(extracted: dict) -> dict:
    """The seed manifest for the acquired microtheory — the exact
    {id, microtheory, concepts} format the seed loader (substrate.boot_all) and the
    edge-learner (concept_graph) read (see seeds/*_microtheory.json)."""
    domain = extracted["domain"]
    return {
        "id": f"{domain}_microtheory",
        "version": "1.0.0",
        "depends_on": [],
        "description": (f"ACQUIRED microtheory: the agent read '{extracted.get('source_title')}' "
                        f"({extracted.get('source')}), extracted the region's concepts, and taught "
                        f"itself — gap-driven knowledge acquisition."),
        "acquired": True,
        "source_title": extracted.get("source_title"),
        "source": extracted.get("source"),
        "microtheory": {"name": domain, "definition": extracted["definition"],
                        "category": domain},
        "concepts": [{"name": c["name"], "definition": c["definition"],
                      "category": domain} for c in extracted["concepts"]],
    }


def teach_microtheory(agent, extracted: dict, *, seeds_dir=_SEEDS,
                      record_provenance: bool = True) -> dict:
    """TEACH the extracted microtheory: install it LIVE (admissible graph mutations
    mirroring the seed loader) AND persist a seed manifest (reboot-proof), then
    clear the concept-graph cache so the re-decode reads the new edges.

    LIVE: reuse the domain's existing (stub) Microtheory node if present, else mint
    one; add each Concept + the `has_concept` edge (idempotent). PERSIST: write
    seeds_dir/<domain>_microtheory.json (the loader re-installs it on a fresh boot).
    RECORD: reuse `teach()` to file a persisted provenance note of the acquisition.

    Returns {mt, domain, n_concepts, seed_path, concepts}."""
    domain = extracted["domain"]
    sub = agent.s

    # LIVE — reuse an existing same-name Microtheory stub if one exists, else mint.
    mt = None
    for n in sub.nodes("Microtheory"):
        if sub.node(n)["attrs"].get("name") == domain and not sub.neighbours(n, "has_concept"):
            mt = n
            break
    if mt is None:
        mt = sub.add_node("Microtheory", {"name": domain,
                                          "definition": extracted["definition"],
                                          "category": domain, "origin": domain,
                                          "acquired": True})
    installed = []
    for c in extracted["concepts"]:
        cid = sub.add_node("Concept", {"name": c["name"], "definition": c["definition"],
                                       "domain": domain, "category": domain})
        if not sub.has_edge(mt, "has_concept", cid):
            sub.add_edge(mt, "has_concept", cid, None)
        installed.append(c["name"])

    # PERSIST — the reboot-proof seed manifest (the loader re-installs it).
    seeds_dir = Path(seeds_dir)
    seeds_dir.mkdir(parents=True, exist_ok=True)
    seed_path = seeds_dir / f"{domain}_microtheory.json"
    seed_path.write_text(json.dumps(_manifest(extracted), indent=1))

    # RECORD — reuse the teach() facility to file a persisted provenance note.
    if record_provenance:
        try:
            from domains.teach import teach
            teach(agent, "AcquiredMicrotheory",
                  {"domain": domain, "source": str(extracted.get("source")),
                   "source_title": str(extracted.get("source_title")),
                   "n_concepts": len(installed),
                   "topic": f"acquired_{domain}"},
                  category="acquired_knowledge", seeds_dir=seeds_dir)
        except Exception:
            pass

    cg._CACHE.clear()                       # re-arm the edge-learner over the new edges
    return {"mt": mt, "domain": domain, "n_concepts": len(installed),
            "seed_path": str(seed_path), "concepts": installed}


# =========================================================================== #
#  THE FULL LOOP — gap -> read -> extract -> teach -> re-decode.
# =========================================================================== #

def acquire_for_gap(agent, domain: str, *, source_text: Optional[str] = None,
                    source_title: Optional[str] = None, conversation=None,
                    seeds_dir=_SEEDS) -> dict:
    """The whole gap-driven acquisition, end to end, for one gap `domain`:

      1. snapshot the BEFORE coverage (concept_graph — the gap signal);
      2. READ the source (reference reader / slab / fed doc);
      3. if no source -> HONEST NULL ({acquired:False, reason:'no readable source'});
      4. EXTRACT the region's concepts (source-faithful; assert they trace);
      5. TEACH the microtheory (live install + persisted manifest);
      6. snapshot the AFTER coverage -> the re-decode (coverage rises).

    Returns {acquired, reason, domain, before, after, extracted, traced, seed_path,
    delta}. The gap DECISION is the coverage read; the read/teach reuse the
    existing machinery; NO fabrication (traced=True guaranteed on success)."""
    before = coverage(agent, domain)
    src = read_source(agent, domain, source_text=source_text,
                      source_title=source_title, conversation=conversation)
    if not src["found"]:
        return {"acquired": False, "reason": "no readable source — cannot acquire "
                "(honest null; no microtheory fabricated)", "domain": domain,
                "before": before, "after": before, "extracted": None,
                "traced": False, "seed_path": None, "delta": {}}

    extracted = extract_microtheory(domain, src)
    if extracted["thin"]:
        return {"acquired": False, "reason": "source named no extractable concepts "
                "(thin source — honest, not padded)", "domain": domain,
                "before": before, "after": before, "extracted": extracted,
                "traced": True, "seed_path": None, "delta": {}}

    traced = traces_to_source(extracted, src)
    if not traced:                          # defensive: never teach un-sourced content
        return {"acquired": False, "reason": "extracted concepts did not trace to the "
                "source — refusing to teach (earn-not-fabricate guard)", "domain": domain,
                "before": before, "after": before, "extracted": extracted,
                "traced": False, "seed_path": None, "delta": {}}

    taught = teach_microtheory(agent, extracted, seeds_dir=seeds_dir)
    after = coverage(agent, domain)
    delta = {"bag": after["bag"] - before["bag"],
             "best": round(after["best"] - before["best"], 4),
             "depth": after["depth"] - before["depth"]}
    return {"acquired": True, "reason": "grounded — read, extracted, taught; "
            "concept_graph now edge-learns the region (coverage rose)",
            "domain": domain, "before": before, "after": after,
            "extracted": extracted, "traced": True,
            "seed_path": taught["seed_path"], "delta": delta,
            "n_concepts": taught["n_concepts"]}


__all__ = [
    "coverage", "is_knowledge_gap", "detect_knowledge_gaps", "gap_domain_of",
    "read_source", "extract_microtheory", "traces_to_source",
    "teach_microtheory", "acquire_for_gap",
]
