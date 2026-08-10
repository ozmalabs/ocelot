"""Speech-and-sound concept bootstrap.

The substrate's audio pipeline mints PhonemeInstances, AcousticSigns,
SonorityValleys etc. — concrete instances tied to specific audio.
What was missing: the abstract CATEGORIES the agent should reason
about. "What is a phoneme?" "What is a word?" "What's a boundary?"

This module installs those categories as graph data — Concept nodes
+ their relations + is_a edges from existing instance-typed nodes
to the right abstract Concept. The graph then carries the
vocabulary an alignment Rule (step 2) reads from.

The hierarchy:

  Concept(sound)
    ├── voice                       — periodic acoustic energy
    └── noise                       — non-periodic
  Concept(boundary)                 — where one unit ends, another begins
    ├── silence_boundary            — gap between voiced segments
    └── sonority_valley_boundary    — deep envelope minimum
  Concept(unit)
    ├── phoneme                     — smallest perceptual sound unit
    ├── syllable                    — phoneme cluster around a sonority peak
    ├── word                        — meaningful sequence of phonemes/syllables
    └── utterance                   — sequence of words on one stream
  Concept(sequence)                 — ordered collection (anything composed_of others)

Instance-to-category edges already present after bootstrap:

  every Phoneme    is_a phoneme
  every base AcousticSign           is_a syllable     (size ~ 1 segment)
  every compositional AcousticSign  is_a word         (size ~ many segments)
  every Utterance                   is_a utterance
  every SonorityValley              is_a sonority_valley_boundary

Bootstrap is idempotent — call from a world adapter's startup hook.
"""
from __future__ import annotations


_SPEECH_PRODUCTIONS = [
    # Instance-typed substrate nodes can carry an is_a edge to their
    # abstract Concept. The Concept node type already exists (speech
    # seed); only the new edge types need declaring.
    ("Phoneme", "is_a", "Concept",
     "speech_concepts:phoneme_is_a"),
    ("AcousticSign", "is_a", "Concept",
     "speech_concepts:sign_is_a"),
    ("Utterance", "is_a", "Concept",
     "speech_concepts:utterance_is_a"),
    ("SonorityValley", "is_a", "Concept",
     "speech_concepts:valley_is_a"),
    # Concept-to-Concept hierarchy edges. `kind_of` is the abstract
    # taxonomy ('voice is a kind of sound'); separate from is_a so we
    # can keep the agent's concept tree introspectable without
    # tangling it with instance grounding.
    ("Concept", "kind_of", "Concept",
     "speech_concepts:concept_kind_of"),
    ("Concept", "composed_of", "Concept",
     "speech_concepts:concept_composed_of"),
    ("Concept", "bounded_by", "Concept",
     "speech_concepts:concept_bounded_by"),
]


# Speech vocabulary the bootstrap mints. Keyed by name; value is
# (description, optional kind_of, optional composed_of, optional
# bounded_by). The order matters only for readability — bootstrap
# resolves all references in two passes.
_SPEECH_CONCEPTS = [
    ("sound",     "any acoustic event in the audio stream", None, None, None),
    ("voice",     "periodic acoustic energy from a speaker",
        "sound", None, None),
    ("noise",     "non-periodic acoustic energy",
        "sound", None, None),
    ("silence",   "absence of voice; threshold-dependent",
        "sound", None, None),

    ("boundary",  "point where one unit ends, another begins",
        None, None, None),
    ("silence_boundary",        "gap of silence between voiced segments",
        "boundary", None, None),
    ("sonority_valley_boundary",
        "deep minimum of the smoothed total envelope — substrate's "
        "word-boundary detector signal",
        "boundary", None, None),

    ("unit",      "any acoustic / linguistic unit",
        None, None, None),
    ("phoneme",   "smallest perceptual sound unit",
        "unit", None, None),
    ("syllable",  "phoneme cluster around a sonority peak",
        "unit", "phoneme", "sonority_valley_boundary"),
    ("word",      "meaningful sequence of phonemes / syllables",
        "unit", "syllable", "sonority_valley_boundary"),
    ("utterance", "sequence of words bounded by silence",
        "unit", "word", "silence_boundary"),

    ("sequence",  "ordered collection of units of the same kind",
        None, None, None),
]


def _ensure_concept(substrate, name, description):
    """Find Concept{name}, else mint with the description. Idempotent."""
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") == name:
            return c
    return substrate.add_node("Concept", {
        "name": name,
        "description": description,
        "origin": "speech_bootstrap",
    })


def _has_edge_with_target(substrate, src, edge_type, tgt):
    """True if the (src, edge_type, tgt) edge already exists."""
    for n in substrate.neighbours(src, edge_type):
        if n == tgt:
            return True
    return False


def install_speech_bootstrap(substrate) -> None:
    """Productions only — concept minting + is_a tagging is done by
    `bootstrap_speech_concepts` from a world adapter at startup so
    it sees the already-loaded instance nodes."""
    for src_t, et, tgt_t, prov in _SPEECH_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass


def bootstrap_speech_concepts(substrate) -> dict:
    """Mint the speech-concept vocabulary as graph data + wire
    is_a edges from existing instance-typed nodes to their abstract
    category. Idempotent — re-running adds nothing new on a fully
    bootstrapped substrate."""
    # Phase 1 — mint every Concept by name.
    concept_by_name: dict[str, object] = {}
    for name, desc, _, _, _ in _SPEECH_CONCEPTS:
        concept_by_name[name] = _ensure_concept(substrate, name, desc)

    # Phase 2 — wire the concept-to-concept hierarchy.
    for name, _, kind_of, composed_of, bounded_by in _SPEECH_CONCEPTS:
        c = concept_by_name[name]
        if kind_of is not None:
            parent = concept_by_name[kind_of]
            if not _has_edge_with_target(substrate, c, "kind_of", parent):
                substrate.add_edge(c, "kind_of", parent)
        if composed_of is not None:
            part = concept_by_name[composed_of]
            if not _has_edge_with_target(substrate, c, "composed_of", part):
                substrate.add_edge(c, "composed_of", part)
        if bounded_by is not None:
            bd = concept_by_name[bounded_by]
            if not _has_edge_with_target(substrate, c, "bounded_by", bd):
                substrate.add_edge(c, "bounded_by", bd)

    # Phase 3 — tag instances with is_a. These edges let alignment
    # Rules ask "what kind of unit is this node?" without hardcoding
    # node-type strings.
    phoneme_c = concept_by_name["phoneme"]
    syllable_c = concept_by_name["syllable"]
    word_c = concept_by_name["word"]
    utterance_c = concept_by_name["utterance"]
    valley_c = concept_by_name["sonority_valley_boundary"]

    tagged = {"phoneme": 0, "syllable": 0, "word": 0,
                "utterance": 0, "valley": 0}

    for p in substrate.nodes("Phoneme"):
        if not _has_edge_with_target(substrate, p, "is_a", phoneme_c):
            substrate.add_edge(p, "is_a", phoneme_c)
            tagged["phoneme"] += 1

    # Base AcousticSigns (composed != True) are syllable-sized
    # (one trajectory ≈ one syllable). Compositional ones (the chunk
    # promotion produces these) are word-sized.
    for s in substrate.nodes("AcousticSign"):
        attrs = substrate.node(s)["attrs"]
        is_composed = bool(attrs.get("composed", False))
        target = word_c if is_composed else syllable_c
        if not _has_edge_with_target(substrate, s, "is_a", target):
            substrate.add_edge(s, "is_a", target)
            tagged["word" if is_composed else "syllable"] += 1

    for u in substrate.nodes("Utterance"):
        if not _has_edge_with_target(substrate, u, "is_a", utterance_c):
            substrate.add_edge(u, "is_a", utterance_c)
            tagged["utterance"] += 1

    for v in substrate.nodes("SonorityValley"):
        if not _has_edge_with_target(substrate, v, "is_a", valley_c):
            substrate.add_edge(v, "is_a", valley_c)
            tagged["valley"] += 1

    return {
        "concepts_present": len(concept_by_name),
        "tagged": tagged,
    }


__all__ = [
    "install_speech_bootstrap",
    "bootstrap_speech_concepts",
    "_SPEECH_PRODUCTIONS",
    "_SPEECH_CONCEPTS",
]
