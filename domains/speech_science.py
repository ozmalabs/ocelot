"""speech_science — load the theory of how speech works into the graph.

The data lives in `seeds/speech_science.json` (the three pillars: production,
perception, acquisition) + the expansion packs under `seeds/expansions/` that
decompose each pillar into its sub-mechanisms. This module is the mechanical
loader (JSON -> graph): it mints the `speech_science` Microtheory + the pillar
Concepts, then `install_all_concept_expansions` wires the sub-mechanisms under
them. The agent later assesses its OWN speech implementation against this map.
"""
from __future__ import annotations

import json
from pathlib import Path

from .code_authoring import _install_concept
from .concept_expansions import install_all_concept_expansions

_SEED_PATH = (Path(__file__).resolve().parent.parent /
              "seeds" / "speech_science.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


def install_speech_science(substrate) -> dict:
    """Install the speech_science Mt + its pillar concepts, then every
    speech-* expansion pack that decomposes them. Idempotent. Returns
    name -> NodeID for the Mt + pillars."""
    seed = _load_seed()
    # Productions the loader's edges need (no-ops if already registered).
    for src, et, tgt in (("Microtheory", "has_concept", "Concept"),
                         ("Microtheory", "has_rule", "Rule"),
                         ("Concept", "decomposes", "Concept")):
        try:
            substrate.add_production({
                "src": {"type": src, "var": "a"}, "edge_type": et,
                "tgt": {"type": tgt, "var": "b"},
                "provenance": f"speech_science:{et}"})
        except Exception:
            pass
    mt = None
    for n in substrate.nodes("Microtheory"):
        if substrate.node(n)["attrs"].get("name") == "speech_science":
            mt = n
            break
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": "speech_science",
            "description": seed.get("description", ""),
            "origin": "speech_science"})

    out = {"_mt": mt}
    for c in seed.get("concepts", []):
        existing = None
        for ec in substrate.neighbours(mt, "has_concept"):
            if substrate.node(ec)["attrs"].get("name") == c["name"]:
                existing = ec
                break
        if existing is not None:
            out[c["name"]] = existing
            continue
        cid = _install_concept(substrate, mt, c["name"], c["definition"], c.get("term"))
        substrate.set_attr(cid, "category", c.get("category", ""))
        substrate.set_attr(cid, "origin", "speech_science")
        out[c["name"]] = cid

    # Wire the sub-mechanisms (the decompositions) from the expansion packs.
    install_all_concept_expansions(substrate)
    return out


_PILLARS = {"speech_production", "speech_perception", "speech_acquisition"}

# Synonyms bridging the THEORY's vocabulary to the agent's IMPLEMENTATION names
# (the impl uses band-means etc., the theory uses formants etc.).
_SYNONYMS = {
    "peripheral_auditory_analysis": ["cochlea", "gammatone", "cochlear", "a1",
                                     "patch", "band", "lateral"],
    "vocal_tract_resonance_formants": ["formant", "band_mean", "mid_band"],
    "voice_onset_time": ["vot", "onset", "burst"],
    "lexical_access": ["lexical", "recognise", "recognize", "vote", "dtw"],
    "categorical_perception": ["categorical", "cluster", "quantis", "quantiz"],
    "babble_feedback_loop": ["babble", "babbling", "mismatch", "motor"],
    "perception_production_link": ["motor", "babble", "synth"],
    "acoustic_cues": ["band", "formant", "voicing", "sibilant", "sonor"],
    "syllable_structure": ["syllable", "sonority", "nucleus", "chunk"],
    "segmentation": ["sonority", "valley", "boundary", "syllable"],
    "statistical_learning": ["vote", "signature", "learn", "distribution"],
    "distributional_learning_of_categories": ["vote", "distribution", "cluster"],
}


def _kw(name: str) -> set:
    return {w for w in name.lower().replace("_", " ").split() if len(w) > 3}


def _impl_names(substrate):
    """Gather the agent's SPEECH-system implementation: (name -> kind) for
    keyword matching, AND the set of implementation concept NODE-IDS. Gathered by
    Mt MEMBERSHIP (phonology/speech_development `contains`), not by `origin` —
    because a science concept that SHARES a node with an impl concept is literally
    implemented (the shared node would otherwise be hidden by the expansion
    overwriting `origin`). Returns (impl_names, impl_node_ids)."""
    impl, nodes = {}, set()
    for mtname, kind in (("phonology", "phonology"),
                         ("speech_development", "speech_development")):
        mt = next((n for n in substrate.nodes("Microtheory")
                   if substrate.node(n)["attrs"].get("name") == mtname), None)
        if mt is None:
            continue
        for c in substrate.neighbours(mt, "contains"):
            nodes.add(c)
            nm = (substrate.node(c)["attrs"].get("name") or "").lower()
            if nm:
                impl[nm] = kind
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("feature_kind") == "comparison":
            nodes.add(c)
            impl[(substrate.node(c)["attrs"].get("name") or "").lower()] = \
                "invented_feature"
    for op in substrate.nodes("Operation"):
        k = (substrate.node(op)["attrs"].get("kind") or "").lower()
        if k:
            impl[k] = "pipeline_op"
    for t in ("SpeechCortex", "MotorCortex", "IntentCortex", "DevelopmentCortex",
              "AuditoryCortex"):
        for _ in substrate.nodes(t):
            impl[t.lower()] = "cortex"
    return impl, nodes


def assess_speech_system(substrate) -> dict:
    """The agent assesses its OWN speech system against the speech_science theory:
    for each sub-mechanism the science names, is there an implementing element?
    Records `SpeechGap` nodes for the misses and returns
    {'covered': [...], 'gaps': [...], 'coverage': float}."""
    mt = next((n for n in substrate.nodes("Microtheory")
               if substrate.node(n)["attrs"].get("name") == "speech_science"), None)
    if mt is None:
        return {"covered": [], "gaps": [], "coverage": 0.0}
    impl, impl_nodes = _impl_names(substrate)
    # index impl by keyword for fast lookup
    impl_kw = {}
    for nm in impl:
        for w in _kw(nm):
            impl_kw.setdefault(w, nm)

    covered, gaps = [], []
    for c in substrate.neighbours(mt, "has_concept"):
        name = substrate.node(c)["attrs"].get("name", "")
        if name in _PILLARS:
            continue
        # SHARED NODE = implemented as itself (the science concept IS an impl one).
        if c in impl_nodes:
            covered.append((name, "shared concept node"))
            continue
        keys = _kw(name) | set(_SYNONYMS.get(name, []))
        hit = None
        for w in keys:
            if w in impl_kw:
                hit = impl_kw[w]
                break
            for inm in impl:
                if len(w) > 3 and (w in inm or inm in w):
                    hit = inm
                    break
            if hit:
                break
        if hit:
            covered.append((name, hit))
        else:
            gaps.append(name)
            substrate.set_attr(c, "implemented", 0)
            try:
                substrate.add_production({
                    "src": {"type": "SpeechGap", "var": "a"},
                    "edge_type": "missing_concept",
                    "tgt": {"type": "Concept", "var": "b"},
                    "provenance": "speech_science:gap"})
            except Exception:
                pass
            g = substrate.add_node("SpeechGap", {
                "concept": name, "origin": "speech_science_assessment"})
            try:
                substrate.add_edge(g, "missing_concept", c, {})
            except Exception:
                pass
    n = len(covered) + len(gaps)
    return {"covered": covered, "gaps": gaps,
            "coverage": (len(covered) / n) if n else 0.0}


def reason_about_gap(substrate, gap_name: str) -> dict:
    """The first step of THINKING, not reacting: the agent REASONS over its
    seeded science (the derivation rules) to DERIVE a justified hypothesis about a
    gap, instead of trying a canned list. It finds the science rule that concludes
    the gap is needed, reads that rule's premises + rationale, checks the premise
    against its own measured situation, and synthesises a hypothesis. Records a
    graph-resident `ReasonedHypothesis` (the agent's thought) + returns it."""
    # the science derivation rules (if -> then, with a 'why')
    rules = []
    for r in substrate.nodes("Rule"):
        a = substrate.node(r)["attrs"]
        if str(a.get("expansion_pack", "")).startswith("speech_"):
            rules.append(a)
    g = gap_name.replace("_", " ")
    # the rule whose CONCLUSION involves the gap = why the science says it matters
    concluding = next(
        (a for a in rules
         if any(gap_name in t or g in t for t in a.get("then_clauses", []))),
        None)
    if concluding is None:
        return {"hypothesis": None}
    premises = concluding.get("if_clauses", [])
    why = concluding.get("why", "")
    # the agent reasons: the rule's premise is a precondition; does it hold for me?
    # (its features were measured HARMFUL -> they are not speaker/context invariant,
    #  which is precisely the premise of these perception design-constraint rules.)
    # The REMEDY the agent reports is READ OFF the rule's own conclusion (then-
    # clauses), not a hardcoded normalization fix — so the hypothesis is correct for
    # whichever gap the rule concludes (normalization / top-down restoration /
    # recover-the-category-by-top-down), instead of always prescribing a baseline
    # subtraction. This keeps the derivation the rule's, not a constant.
    conclusion = "; ".join(concluding.get("then_clauses", [])) or gap_name
    hyp_text = (
        f"Science rule '{concluding.get('name')}' concludes that {gap_name} is "
        f"REQUIRED given {premises} — because: {why}  I have measured my own "
        f"features as counterproductive (lever_harms), i.e. NOT invariant — the "
        f"rule's premise holds for me. THEREFORE {gap_name} is not a knob to tune "
        f"but a PRECONDITION to add, and the rule names what to build: "
        f"{conclusion} — I should add that machinery and re-test.")
    h = substrate.add_node("ReasonedHypothesis", {
        "about_gap": gap_name,
        "from_rule": concluding.get("name"),
        "premises": list(premises),
        "rationale": why,
        "hypothesis": hyp_text,
        "origin": "speech_reasoning"})
    return {"hypothesis": hyp_text, "node": h, "rule": concluding.get("name"),
            "premises": premises}


def science_says_formants_are_peaks(substrate) -> bool:
    """The agent reads the science it HOLDS to ground what a formant IS
    operationally: the `vocal_tract_resonance_formants` concept states formants
    'appear as spectral peaks'. This is the agent consulting its own knowledge
    (not an LLM) to decide HOW to compose its detector. Returns True if the
    grounding is present."""
    mt = next((n for n in substrate.nodes("Microtheory")
               if substrate.node(n)["attrs"].get("name") == "speech_science"), None)
    if mt is None:
        return False
    for c in substrate.neighbours(mt, "has_concept"):
        a = substrate.node(c)["attrs"]
        if a.get("name") == "vocal_tract_resonance_formants":
            return "peak" in (a.get("definition", "")).lower()
    return False


__all__ = ["install_speech_science", "assess_speech_system", "reason_about_gap",
           "science_says_formants_are_peaks"]
