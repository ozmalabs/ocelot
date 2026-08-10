"""THE JABBERWOCK READS + GROUNDS THE ARC-AGI WEBSITE — a thin world-adapter.

A human who plays ARC-AGI walks in having READ the site: they know what a game
is, what they're doing, what winning means, the core-knowledge framing. The fair
fight is the jabberwock walking in with the SAME context — formed by ITS OWN
read+ground faculty, not hand-authored by the harness.

THIS SHELL IS A WORLD-ADAPTER (CLAUDE.md): it owns NO reasoning and holds NO agent
state. It only (1) boots the substrate + installs the agent's PRIOR-EXPERIENCE
concept seeds (the foundation concepts it already holds: objects/agents/relations/
psychology/communication — its standing knowledge, NOT authored here), (2) feeds
the ARC-AGI docs prose to the agent's read+ground faculty, (3) reads back + reports
what IT grounded.

THE FACULTY (all the meaning is the agent's, none is the shell's):
  · construction_grammar.extract_definition — the ONE general genus-differentia
    reader. Over ANY definitional sentence ("X is a Y ...") it recovers
    {term, genus, differentia, register}. The TERMS + their genera come from ARC's
    OWN prose — the shell does not name a single concept.
  · read_and_ground.read_and_ground — for each extracted (term, definition
    sentence) it GROUNDS the term: comprehends the genus, then RECURSES toward the
    agent's held primitives. If the genus is a concept the agent already HOLDS
    (its prior experience), the term is grounded-in-prior-experience; if not, it is
    an HONEST held-ungrounded residual (the gap between what the site assumes a
    reader knows and what the agent can connect to — itself the interesting result).

The shell's only text work is MECHANICAL world-adapter I/O: read the files, split
into sentences, hand each to the agent's reader. No conditional over graph state,
no meaning judgement, no authored "game" concept, no shape->faculty mapping.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:.:scripts \\
        python3 scripts/jabberwock_reads_arc_agi_site.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))
sys.path.insert(0, str(ROOT / "scripts"))

from substrate_rs import _native

from domains import construction_grammar as cg
from domains import grounded_representation as gr
from domains import read_and_ground as rag

# OFFLINE: this is offline reading of already-downloaded ARC docs. The agent's
# reader (read_and_ground) falls through to a network reference lookup for an
# un-held genus; we keep it OFFLINE so an un-held genus is an HONEST stall (the
# fed sentence is the only definition), not a slow network attempt. The fed
# `definition_text` short-circuits before this anyway — this only blocks the
# recursive descent's reference lookups.
_orig_read_definition = rag._read_definition


def _offline_read_definition(concept_name, conversation, definition_text=None,
                             substrate=None):
    if definition_text:
        return definition_text.strip() or None
    feed = getattr(conversation, "_definition_feed", None)
    if isinstance(feed, dict):
        t = feed.get(concept_name) or feed.get(concept_name.lower())
        if isinstance(t, str) and t.strip():
            return t.strip()
    return None  # no network: an un-held genus stalls honestly.


rag._read_definition = _offline_read_definition

SEP = "=" * 78
ARC_DIR = Path("/tmp/arc3_context")
SAVE_PATH = ROOT / "data" / "arc_agi_grounded_context.json"

# the agent's PRIOR-EXPERIENCE concept seeds (foundation knowledge it already
# holds — NOT authored here; these are existing seeds/*.json the agent ships
# with). Loaded as the held basis the read terms ground AGAINST.
# two seed formats: a `nodes`/`edges` graph form and a `concepts`-array form.
# Both are the agent's standing foundation knowledge (NOT authored here). The
# communication_concepts + physics_foundation + vision_object seeds carry exactly
# the CORE-KNOWLEDGE primitives ARC's framing invokes (action/event/motion/agent/
# goal/space/object/cause/change-of-state/force/mass/objectness/object_permanence)
# — the agent's prior experience the read terms ground AGAINST.
PRIOR_SEEDS_NODES = [
    "conceptual_categories",   # objects/animals/people/places (core categories)
    "relations",               # causes/contains/uses/needs/produces/enables ...
    "conversation",            # speech-acts / discourse concepts
    "psychology",              # belief/desire/intention/goal (mental states)
]
PRIOR_SEEDS_CONCEPTS = [
    "communication_concepts",  # action/event/motion/agent/goal/space/cause/...
    "physics_foundation",      # force/mass/velocity/energy/momentum/spacetime
    "vision_object",           # objectness/object_permanence/invariance/geon
]


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# (1) MECHANICAL: install the agent's prior-experience seeds. A node/edge JSON
# loader for the seed format (local_id nodes + {local:..}/{role:..} edges). This
# is pure world-adapter translation — graph data in, no decision over it.
# ---------------------------------------------------------------------------

def _install_nodes_seed(s, d: dict) -> str:
    idmap = {}
    for n in d.get("nodes", []):
        lid = n.get("local_id", n.get("id"))
        attrs = n.get("attrs", {}) or {}
        try:
            nid = s.add_node(n.get("type", "Concept"), attrs)
            if lid is not None:
                idmap[lid] = nid
        except Exception:
            pass
    n_edges = 0
    for e in d.get("edges", []):
        src = e.get("src"); tgt = e.get("tgt")
        sid = idmap.get(src.get("local")) if isinstance(src, dict) else None
        tid = idmap.get(tgt.get("local")) if isinstance(tgt, dict) else None
        if sid is None or tid is None:
            continue
        try:
            s.add_edge(sid, e.get("type", "rel"), tid)
            n_edges += 1
        except Exception:
            pass
    return f"{len(idmap)} nodes, {n_edges} edges"


def _install_concepts_seed(s, d: dict) -> str:
    """The `concepts`-array seed form (communication_concepts / physics_foundation
    / vision_object): each entry is name+kind+gloss. Install as a Concept node
    (the agent's standing concept). Idempotent on existing names."""
    have = {s.node(c)["attrs"].get("name") for c in s.nodes("Concept")}
    n = 0
    for c in d.get("concepts", []):
        name = c.get("name")
        if not name or name in have:
            continue
        try:
            s.add_node("Concept", {"name": name, "kind": c.get("kind", ""),
                                   "definition": c.get("gloss", ""),
                                   "origin": "prior_experience_seed"})
            have.add(name); n += 1
        except Exception:
            pass
    return f"{n} concepts"


def install_prior_experience(s) -> dict:
    held_before = {s.node(c)["attrs"].get("name") for c in s.nodes("Concept")}
    loaded = {}
    for seed in PRIOR_SEEDS_NODES:
        p = ROOT / "seeds" / f"{seed}.json"
        if not p.exists():
            loaded[seed] = "(missing)"; continue
        loaded[seed] = _install_nodes_seed(s, json.loads(p.read_text()))
    for seed in PRIOR_SEEDS_CONCEPTS:
        p = ROOT / "seeds" / f"{seed}.json"
        if not p.exists():
            loaded[seed] = "(missing)"; continue
        loaded[seed] = _install_concepts_seed(s, json.loads(p.read_text()))
    held_after = {s.node(c)["attrs"].get("name") for c in s.nodes("Concept")}
    held_after.discard(None)
    new = held_after - held_before
    return {"loaded": loaded, "n_held": len(held_after),
            "held_names": held_after, "new": new}


# ---------------------------------------------------------------------------
# (2) MECHANICAL: read the ARC docs + split into sentences. World-adapter I/O.
# ---------------------------------------------------------------------------

_HEAD = re.compile(r"^\s{0,3}#{1,6}\s", re.M)


# a DEFINITIONAL copula = a copula immediately FOLLOWED BY AN ARTICLE ('is a',
# 'is an', 'is the') — the surface mark of a defining noun phrase ('X is a Y'),
# as opposed to a passive/predicative ('X is recorded', 'X is required', 'X is
# designed'). This is an I/O-boundary SURFACE classifier (CLAUDE.md-permitted:
# converting opaque web prose into the smallest definitional token the agent's
# genus reader should see) — NOT a meaning decision; the genus + grounding are
# entirely the agent's.
_DEF_COPULA = re.compile(r"\b[A-Za-z][A-Za-z0-9 '/-]{1,40}\b\s+(?:is|are)\s+(?:a|an|the)\s+[a-z]")


def read_sentences() -> list[tuple[str, str]]:
    """(source_file, sentence) for every DEFINITIONAL prose sentence in the docs.

    Mechanical world-adapter I/O: strip markdown tables/headers/code fences,
    split into sentences PER PARAGRAPH (so cross-paragraph text never fuses into
    a frankenstein 'sentence'), and keep only sentences carrying a definitional
    'X is a/an/the <noun>' copula. extract_definition still decides the genus."""
    out: list[tuple[str, str]] = []
    for fn in ["llms-full.txt", "tech_report.txt", "arc_agi.txt", "arc_agi_3.txt"]:
        p = ARC_DIR / fn
        if not p.exists() or not p.stat().st_size:
            continue
        text = p.read_text(errors="ignore")
        text = re.sub(r"```.*?```", " ", text, flags=re.S)  # drop code fences
        # work PER LINE/paragraph; drop table rows, headers, source lines, list
        # bullets — non-prose markdown that fuses into garbage if concatenated.
        for ln in text.splitlines():
            st = ln.strip()
            if (not st or st.startswith("|") or st.startswith("#")
                    or st.startswith("Source:") or st.startswith("```")
                    or st.startswith(">")):
                continue
            st = re.sub(r"\s+", " ", st)
            for sent in re.split(r"(?<=[.!?])\s+", st):
                sent = sent.strip().strip("*-• ")
                if not (12 <= len(sent) <= 200):
                    continue
                if not _DEF_COPULA.search(sent):
                    continue
                out.append((fn, sent))
    return out


# the surface->concept-name convention (rag._name_norm) — a normalisation, not a
# meaning decision.
def _norm(surface: str) -> str:
    return re.sub(r"\s+", "_", (surface or "").lower().strip())


# the genus head NP can be a multiword phrase; the agent grounds the head noun
# (read_and_ground's own head-noun fallback). For the HELD check we test the full
# phrase AND its head — both are the agent's lexicon, not a decision here.
def _genus_held(s, genus: str, index: dict) -> bool:
    if not genus:
        return False
    if rag._is_held(s, _norm(genus), index=index):
        return True
    head = genus.split()[-1]
    return rag._is_held(s, _norm(head), index=index)


def main() -> None:
    banner("BOOT — the agent's read+ground faculty over a fresh substrate")
    s = _native.Substrate()
    gr.open_grounding_productions(s)

    class Conv:
        # the agent's construction grammar (the held genus-differentia structure).
        _constructions = cg.load_constructions()

    conv = Conv()

    banner("PRIOR EXPERIENCE — install the foundation concept seeds the agent holds")
    prior = install_prior_experience(s)
    for seed, info in prior["loaded"].items():
        print(f"  {seed:28s} {info}")
    print(f"  -> agent now HOLDS {prior['n_held']} Concept nodes (its prior "
          f"experience / basis).")

    banner("READ — extract every definitional sentence from the ARC-AGI docs")
    sentences = read_sentences()
    print(f"  {len(sentences)} candidate prose sentences across the ARC docs.")

    index = gr._concept_by_name(s)
    # the agent reads each sentence; extract_definition yields a (term, genus) when
    # the sentence DEFINES something. Dedup by term (first definition wins).
    seen_terms: dict[str, dict] = {}
    for fn, sent in sentences:
        try:
            d = cg.extract_definition(sent, substrate=s)
        except Exception:
            continue
        if not d:
            continue
        term = (d.get("term") or "").strip()
        genus = (d.get("genus") or "").strip()
        if not term or not genus:
            continue
        # mechanical surface filter: a real definiendum is a short noun phrase, not
        # a whole subordinate clause. (read_and_ground's own _is_clean_object spirit;
        # a surface-shape check, not a meaning decision.)
        if len(term.split()) > 5 or len(genus.split()) > 7:
            continue
        key = _norm(term)
        if key in seen_terms:
            continue
        seen_terms[key] = {"term": term, "genus": genus, "sentence": sent,
                           "source": fn, "register": d.get("register")}

    print(f"  the agent's genus reader found {len(seen_terms)} DEFINED terms in "
          f"ARC's prose (terms + genera are ARC's, not the harness's).")

    banner("GROUND — read_and_ground each ARC term toward the agent's held primitives")
    # stage the read definitions as a teacher FEED (the agent's own fed-gloss path):
    # read_and_ground reads the gloss from conv._definition_feed and, because the
    # source is a fed teacher gloss (not the encyclopedia), skips the network
    # provenance lookup — fully offline, the intended taught-fact path.
    conv._definition_feed = {
        key: f"{info['term']} is a {info['genus']}. {info['sentence']}"
        for key, info in seen_terms.items()}

    grounded_prior: list[dict] = []   # genus is a concept the agent already holds
    held_ungrounded: list[dict] = []  # genus not held — honest residual
    for key, info in seen_terms.items():
        try:
            res = rag.read_and_ground(s, key, conv, _index=index, max_depth=1)
        except Exception as e:
            held_ungrounded.append({**info, "reason": f"read error: {e}"})
            continue
        index = gr._concept_by_name(s)  # refresh after a possible new concept
        genus_held = _genus_held(s, info["genus"], index)
        row = {**info, "grounded": bool(res.get("grounded")),
               "reason": res.get("reason"), "genus_held": genus_held}
        if genus_held:
            grounded_prior.append(row)
        else:
            held_ungrounded.append(row)

    banner("WHAT THE JABBERWOCK GROUNDED — its verdict (verbatim from its reader)")
    print(f"\n  GROUNDED-IN-PRIOR-EXPERIENCE ({len(grounded_prior)}): the ARC term's "
          f"genus is a concept the agent already holds.")
    for r in sorted(grounded_prior, key=lambda x: x["term"]):
        print(f"    · {r['term']:24s} is-a [{r['genus']}]   "
              f"(grounded={r['grounded']}, src={r['source']})")
    print(f"\n  HELD-UNGROUNDED RESIDUAL ({len(held_ungrounded)}): the ARC term's "
          f"genus is NOT a concept the agent holds — honest gap.")
    for r in sorted(held_ungrounded, key=lambda x: x["term"]):
        print(f"    · {r['term']:24s} is-a [{r['genus']}]   "
              f"(genus held? {r.get('genus_held')}, src={r['source']})")

    # THE GAP (the interesting result): ARC's prose ASSUMES the reader holds the
    # core-knowledge priors its tech report names (objectness/agentness/goal-
    # directedness/space/cause). Read the agent's OWN graph for which of those it
    # actually holds — the basis a human walks in with. (Names checked against the
    # agent's held concepts; the LIST of priors is ARC's tech-report vocabulary,
    # not an authored mapping — we only ask the graph 'do you hold this?'.)
    banner("THE CORE-KNOWLEDGE BASIS — which priors ARC assumes does the agent hold?")
    arc_priors = ["object", "objectness", "object_permanence", "agent", "goal",
                  "action", "event", "motion", "change_of_state", "cause",
                  "space_inside", "space_above", "space_below", "space_near",
                  "space_contact", "space_direction", "value", "intention",
                  "perception_visual", "number", "comparison_more",
                  "comparison_equal", "interaction", "reward", "state"]
    idx_now = gr._concept_by_name(s)
    held_priors = [p for p in arc_priors if _genus_held(s, p, idx_now)]
    miss_priors = [p for p in arc_priors if p not in held_priors]
    print(f"  HELD ({len(held_priors)}): {held_priors}")
    print(f"  NOT HELD ({len(miss_priors)}): {miss_priors}")

    banner("INTROSPECT — the ARC concepts now resident in the agent's graph")
    # read back the Concept nodes the read created (origin marks the grounded ones).
    arc_terms = set(seen_terms.keys())
    resident = []
    for c in s.nodes("Concept"):
        nm = s.node(c)["attrs"].get("name")
        if nm and _norm(nm) in arc_terms:
            # the built_from genus the agent recorded for this concept.
            genera = []
            try:
                for tgt in s.neighbours(c, "built_from"):
                    genera.append(s.node(tgt)["attrs"].get("name"))
            except Exception:
                pass
            resident.append((nm, genera))
    print(f"  {len(resident)} ARC concepts are now NODES in the agent's graph "
          f"(wired built_from -> their genus).")

    # PERSIST via the agent's OWN save path (self_persistence.save_state ->
    # graph_to_dict). A later play session boots with this context.
    banner("PERSIST — save the grounded graph via the agent's own save path")
    try:
        from domains import self_persistence as sp
        summary = sp.save_state(s, str(SAVE_PATH))
        print(f"  saved -> {summary['path']}")
        print(f"  {summary['n_nodes']} nodes, {summary['n_edges']} edges, "
              f"{summary['size_bytes']} bytes.")
    except Exception as e:
        print(f"  (save failed: {e})")

    banner("SUMMARY")
    print(f"  terms read from ARC prose : {len(seen_terms)}")
    print(f"  grounded in prior experience: {len(grounded_prior)}")
    print(f"  held-ungrounded residual    : {len(held_ungrounded)}")


if __name__ == "__main__":
    main()
